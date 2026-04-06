import asyncio
import random
import re
from datetime import datetime, timedelta
from pprint import pformat

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import PauseCrawler, ReMakeRequest, SkipRequest, StopCrawler
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse, LoggedData
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
from turbocrawler.engine.data_types.info import ExecutionInfo, RunningInfo
from turbocrawler.engine.plugin import Plugin
from turbocrawler.engine.url_extractor import UrlExtractor
from turbocrawler.engine.worker_queues import WorkerQueueManager
from turbocrawler.logger import logger
from turbocrawler.utils import get_running_id


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], config: CrawlerRunnerConfig | None = None, cli_kwargs: dict | None = None):
        self._running_id = get_running_id()
        self._start_process_time = datetime.now()
        self._last_info_log_time = datetime.now()

        self._crawler_type = crawler
        self.crawler: Crawler
        self.config = config
        self.cli_kwargs = cli_kwargs or {}
        self.crawler_queue: CrawlerQueueABC
        self.plugins: list[Plugin] = []

        self._requests_info = {"Made": 0, "ReMakeRequest": 0, "SkipRequest": 0}
        self.parse_queue_manager: WorkerQueueManager

    async def _initialize_runner_dependencies(self):
        logger.create_file_handler(dir=self._crawler_type.crawler_name, filename=self._running_id)

        logger.info(f"crawler cli_kwargs: {self.cli_kwargs}")

        if self.config is None:
            self.config = CrawlerRunnerConfig()

        if self.config.crawler_queue_params is None:
            self.config.crawler_queue_params = dict()
        if self.config.crawled_queue_params is None:
            self.config.crawled_queue_params = dict()

        if 'crawler_name' not in self.config.crawler_queue_params.keys():
            self.config.crawler_queue_params['crawler_name'] = self._crawler_type.crawler_name
        if 'crawler_name' not in self.config.crawled_queue_params.keys():
            self.config.crawled_queue_params['crawler_name'] = self._crawler_type.crawler_name

        crawled_queue = self.config.crawled_queue(**self.config.crawled_queue_params)
        self.config.crawler_queue_params['crawled_queue'] = crawled_queue
        self.crawler_queue = self.config.crawler_queue(**self.config.crawler_queue_params)

        if self.config.plugins:
            self.plugins = self._initialize_plugins(self._crawler_type, self.config.plugins)
            logger.create_plugins_handlers(plugins=self.plugins, crawler=self._crawler_type,
                                           running_id=self._running_id)

        self.crawler = self._crawler_type(crawler_queue=self.crawler_queue, plugins=self.plugins, logger=logger, cli_kwargs=self.cli_kwargs)
        self._compile_regex()

        self.parse_queue_manager = WorkerQueueManager(queue_name='parse_queue',
                                  class_object=self.crawler,
                                  target=self.crawler.parse,
                                  qtd_workers=self.config.qtd_parse)

    async def run(self):
        await self._initialize_runner_dependencies()

        self.parse_queue_manager.start_workers()

        try:
            await self._call_all_start_crawler()

            await self._remove_crawled()

            await self._login()

            await self._call_crawler_first_request()

            await self._start_crawler_queue_loop()

            await self._save_all()

            return await self._call_all_stop_crawler()
        except StopCrawler as stop_crawler:
            return await self._call_all_stop_crawler(stop_crawler)
        except Exception as e:
            return await self._call_all_stop_crawler(exception=e)

    async def _stop_workers(self):
        if not self.parse_queue_manager.stopped:
            self.parse_queue_manager.stop_workers()

    async def _call_all_start_crawler(self):
        logger.info(f'Calling {self.crawler.crawler_name}.start_crawler')

        start_crawler_objs: list[Plugin | Crawler | CrawledQueueABC] = [*self.plugins, self.crawler, self.crawler_queue.crawled_queue]
        for obj in start_crawler_objs:
            await obj.start_crawler()

    async def _call_all_stop_crawler(self, stop_crawler: StopCrawler = None, exception: Exception = None) -> ExecutionInfo:
        forced_stop = False
        error = False
        reason = ""

        await self._stop_workers()

        if exception:
            forced_stop = True
            error = True
            reason = str(exception)
            logger.error(f'An exception happened in the execution, stopping the crawler.\nException:\n{exception}')

        if stop_crawler:
            forced_stop = True
            error = stop_crawler.error
            reason = stop_crawler.reason
            logger.info(f'StopCrawler raised reason {reason}')
        logger.info(f'Calling {self.crawler.crawler_name}.stop_crawler')

        execution_info = ExecutionInfo(**await self._get_running_info(),
                                       exception=exception,
                                       error=error,
                                       forced_stop=forced_stop,
                                       reason=reason)

        stop_crawler_objs: list[Plugin | Crawler | CrawledQueueABC] = [*self.plugins, self.crawler, self.crawler_queue, self.crawler_queue.crawled_queue]
        for obj in stop_crawler_objs:
            await obj.stop_crawler(execution_info=execution_info)

        formatted_info = pformat(execution_info, sort_dicts=False)
        logger.info(f'Execution info\n{formatted_info}', extra={'json': execution_info})
        return execution_info

    async def _call_crawler_first_request(self):
        logger.info(f'Calling {self.crawler.crawler_name}.crawler_first_request')
        for plugin in self.plugins:
            await plugin.crawler_first_request()
        crawler_response = await self.crawler.crawler_first_request()
        if crawler_response is not None:
            await self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.url)
            await self.crawler.parse(crawler_request=CrawlerRequest(url="crawler_first_request"),
                               crawler_response=crawler_response)
            await self._add_urls_to_queue(crawler_response=crawler_response)

    async def _start_crawler_queue_loop(self):
        logger.info('Processing crawler queue')
        while True:
            await self._log_info()
            next_crawler_request = await self.crawler_queue.get()
            if next_crawler_request:
                await self._make_request(crawler_request=next_crawler_request)
            else:
                logger.info('Crawler queue is empty, all crawler_requests made')
                await self._stop_workers()
                return True

    async def _make_request(self, crawler_request: CrawlerRequest):
        logger.debug(f'[process_request] URL: {crawler_request.url}')
        request_retries = 0
        while True:
            try:
                wait_time = random.uniform(*self.crawler.time_between_requests)
                await asyncio.sleep(wait_time)
                crawler_response: CrawlerResponse = None

                # call all process_request
                process_request_objs: list[Plugin | Crawler] = [*self.plugins, self.crawler]
                for plugin in process_request_objs:
                    func_return = await plugin.process_request(crawler_request=crawler_request)
                    if isinstance(func_return, CrawlerResponse):
                        crawler_response = func_return
                        break
                else:
                    raise StopCrawler(
                        f'Inside Crawler or Plugin process_request function must return a CrawlerResponse')

                # call all process_response
                process_response_objs: list[Plugin | Crawler] = [*self.plugins, self.crawler]
                for obj in process_response_objs:
                    await obj.process_response(crawler_request, crawler_response)

                if crawler_response.settings.parse_response:
                    await self.crawler.parse(crawler_request=crawler_request, crawler_response=crawler_response)
                if crawler_response.settings.automatic_schedule:
                    await self._add_urls_to_queue(crawler_response=crawler_response)

                self._requests_info['Made'] += 1
                break
            except ReMakeRequest as error:
                self._requests_info['ReMakeRequest'] += 1
                request_retries += 1
                max_retries = error.retries
                if request_retries >= max_retries:
                    logger.warning(f'Exceed retry tentatives for url {crawler_request.url}')
                    break
            except SkipRequest as error:
                self._requests_info['SkipRequest'] += 1
                logger.info(f'Skipping request for url {crawler_request.url} reason: {error.reason}')
                break
            except PauseCrawler as pause_crawler:
                logger.info(f'Pausing crawler for {pause_crawler.time} seconds as requested.')
                await asyncio.sleep(pause_crawler.time)
                break

    async def _add_urls_to_queue(self, crawler_response: CrawlerResponse) -> None:
        if not self.crawler.regex_extract_rules:
            return None

        if self.crawler.regex_extract_rules[0] == '*':
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.url,
                html_body=crawler_response.body,
                allowed_domains=self.crawler.allowed_domains)
        else:
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.url,
                html_body=crawler_response.body,
                extract_rules=self.crawler.regex_extract_rules,
                allowed_domains=self.crawler.allowed_domains)

        for url in urls_to_extract:
            crawler_request = CrawlerRequest(url=url,
                                             headers=crawler_response.headers,
                                             cookies=crawler_response.cookies,
                                             kwargs=crawler_response.kwargs)
            await self.crawler_queue.add(crawler_request=crawler_request)

    def _compile_regex(self):
        for i, extract_rule in enumerate(self.crawler.regex_extract_rules):
            raw_regex = extract_rule.regex
            if not isinstance(raw_regex, re.Pattern):
                self.crawler.regex_extract_rules[i].regex = re.compile(raw_regex)

    @staticmethod
    def _initialize_plugins(crawler: type[Crawler], plugins: list[type[Plugin]] = ()) -> list[Plugin]:
        initialized = []
        for plugin in plugins:
            initialized.append(plugin(crawler=crawler))
        return initialized

    async def _login(self) -> LoggedData:
        logger.info(f'Calling {self.crawler.crawler_name}.login')
        self.crawler.logged_data = await self.crawler.login()

    async def _save_all(self):
        logger.info(f'Calling {self.crawler.crawler_name}.save_all')
        await self.crawler.save_all()

    async def _remove_crawled(self):
        extract_rules_remove_crawled = [extract_rule for extract_rule in self.crawler.regex_extract_rules
                                        if extract_rule.remove_crawled]
        await self.crawler_queue.crawled_queue.remove_urls_with_remove_crawled(
            extract_rules_remove_crawled=extract_rules_remove_crawled)

    async def _get_running_info(self) -> RunningInfo:
        running_time = datetime.now() - self._start_process_time
        return RunningInfo(
            crawler_queue=await self.crawler_queue.get_info(),
            crawled_queue=await self.crawler_queue.crawled_queue.get_info(),
            requests_made=self._requests_info["Made"],
            requests_remade=self._requests_info["ReMakeRequest"],
            requests_skipped=self._requests_info["SkipRequest"],
            parse_queue=self.parse_queue_manager.get_info(),
            running_time=str(running_time),
            running_id=self._running_id
        )

    async def _log_info(self):
        have_passed_time = self._last_info_log_time + timedelta(minutes=1) < datetime.now()
        if have_passed_time:
            self._last_info_log_time = datetime.now()
            running_info = await self._get_running_info()
            formatted_info = pformat(running_info, sort_dicts=False)
            logger.info(f'\n{formatted_info}')

import re
import time
from datetime import datetime, timedelta
from pprint import pformat

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import ReMakeRequest, SkipRequest, StopCrawler
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
from turbocrawler.engine.data_types.info import ExecutionInfo, RunningInfo
from turbocrawler.engine.plugin import Plugin
from turbocrawler.engine.url_extractor import UrlExtractor
from turbocrawler.engine.worker_queues import WorkerQueueManager
from turbocrawler.logger import logger
from turbocrawler.utils import get_running_id


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], config: CrawlerRunnerConfig | None = None):
        self._running_id = get_running_id()
        self._start_process_time = datetime.now()
        self._last_info_log_time = datetime.now()

        self._crawler_type = crawler
        self.crawler: Crawler
        self.config = config
        self.crawler_queue: CrawlerQueueABC
        self.plugins: list[Plugin] = []

        self._requests_info = {"Made": 0, "ReMakeRequest": 0, "SkipRequest": 0}
        self.parse_queue_manager: WorkerQueueManager

    def _initialize_runner_dependencies(self):
        logger.create_file_handler(dir=self._crawler_type.crawler_name, filename=self._running_id)

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

        self.crawler = self._crawler_type(crawler_queue=self.crawler_queue, plugins=self.plugins, logger=logger)
        self._compile_regex()

        self.parse_queue_manager = WorkerQueueManager(queue_name='parse_queue',
                                                      class_object=self.crawler,
                                                      target=self.crawler.parse,
                                                      qtd_workers=self.config.qtd_parse)

    def run(self):
        self._initialize_runner_dependencies()

        self.parse_queue_manager.start_workers()

        try:
            self._call_all_start_crawler()

            self._remove_crawled()

            self._call_crawler_first_request()

            self._start_crawler_queue_loop()

            return self._call_all_stop_crawler()
        except StopCrawler as stop_crawler:
            return self._call_all_stop_crawler(stop_crawler)
        except Exception as e:
            return self._call_all_stop_crawler(exception=e)

    def _call_all_start_crawler(self):
        logger.info(f'Calling {self.crawler.crawler_name}.start_crawler')

        start_crawler_objs = [*self.plugins, self.crawler, self.crawler_queue.crawled_queue]
        for obj in start_crawler_objs:
            obj.start_crawler()

    def _call_all_stop_crawler(self, stop_crawler: StopCrawler = None, exception: Exception = None) -> ExecutionInfo:
        forced_stop = False
        error = False
        reason = ""

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

        execution_info = ExecutionInfo(**self._get_running_info(),
                                       exception=exception,
                                       error=error,
                                       forced_stop=forced_stop,
                                       reason=reason)

        stop_crawler_objs = [*self.plugins, self.crawler, self.crawler_queue, self.crawler_queue.crawled_queue]
        for obj in stop_crawler_objs:
            obj.stop_crawler(execution_info=execution_info)

        formatted_info = pformat(execution_info, sort_dicts=False)
        logger.info(f'Execution info\n{formatted_info}', extra={'json': execution_info})
        return execution_info

    def _call_crawler_first_request(self):
        logger.info(f'Calling {self.crawler.crawler_name}.crawler_first_request')
        for plugin in self.plugins:
            plugin.crawler_first_request()
        crawler_response = self.crawler.crawler_first_request()
        if crawler_response is not None:
            self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.url)
            self.crawler.parse(crawler_request=CrawlerRequest(url="crawler_first_request"),
                               crawler_response=crawler_response)
            self._add_urls_to_queue(crawler_response=crawler_response)

    def _start_crawler_queue_loop(self):
        logger.info('Processing crawler queue')
        while True:
            self._log_info()
            next_crawler_request = self.crawler_queue.get()
            if next_crawler_request:
                self._make_request(crawler_request=next_crawler_request)
            else:
                logger.info('Crawler queue is empty, all crawler_requests made')
                self.parse_queue_manager.stop_workers()
                return True

    def _make_request(self, crawler_request: CrawlerRequest):
        logger.debug(f'[process_request] URL: {crawler_request.url}')
        request_retries = 0
        while True:
            try:
                time.sleep(self.crawler.time_between_requests)
                crawler_response = None

                # call all process_request
                process_request_objs = [*self.plugins, self.crawler]
                for plugin in process_request_objs:
                    func_return = plugin.process_request(crawler_request=crawler_request)
                    if isinstance(func_return, CrawlerResponse):
                        crawler_response = func_return
                        break
                else:
                    raise StopCrawler(
                        f'Inside Crawler or Plugin process_request function must return a CrawlerResponse')

                # call all process_response
                process_response_objs = [*self.plugins, self.crawler]
                for obj in process_response_objs:
                    obj.process_response(crawler_request, crawler_response)

                if crawler_response.settings.parse_response:
                    self.crawler.parse(crawler_request=crawler_request, crawler_response=crawler_response)
                if crawler_response.settings.automatic_schedule:
                    self._add_urls_to_queue(crawler_response=crawler_response)

                self._requests_info['Made'] += 1
                break
            except ReMakeRequest as error:
                self._requests_info['ReMakeRequest'] += 1
                request_retries += 1
                max_retries = error.retries
                if request_retries >= max_retries:
                    logger.warn(f'Exceed retry tentatives for url {crawler_request.url}')
                    break
            except SkipRequest as error:
                self._requests_info['SkipRequest'] += 1
                logger.info(f'Skipping request for url {crawler_request.url} reason: {error.reason}')
                break

    def _add_urls_to_queue(self, crawler_response: CrawlerResponse) -> None:
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
            self.crawler_queue.add(crawler_request=crawler_request)

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

    def _remove_crawled(self):
        extract_rules_remove_crawled = [extract_rule for extract_rule in self.crawler.regex_extract_rules
                                        if extract_rule.remove_crawled]
        self.crawler_queue.crawled_queue.remove_urls_with_remove_crawled(
            extract_rules_remove_crawled=extract_rules_remove_crawled)

    def _get_running_info(self) -> RunningInfo:
        running_time = datetime.now() - self._start_process_time
        return RunningInfo(
            crawler_queue=self.crawler_queue.get_info(),
            crawled_queue=self.crawler_queue.crawled_queue.get_info(),
            requests_made=self._requests_info["Made"],
            requests_remade=self._requests_info["ReMakeRequest"],
            requests_skipped=self._requests_info["SkipRequest"],
            parse_queue=self.parse_queue_manager.get_info(),
            running_time=str(running_time),
            running_id=self._running_id
        )

    def _log_info(self):
        have_passed_time = self._last_info_log_time + timedelta(minutes=1) < datetime.now()
        if have_passed_time:
            self._last_info_log_time = datetime.now()
            running_info = self._get_running_info()
            formatted_info = pformat(running_info, sort_dicts=False)
            logger.info(f'\n{formatted_info}')

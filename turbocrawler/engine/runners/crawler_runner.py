import asyncio
import logging
import random
import re
from datetime import datetime, timedelta
from pprint import pformat

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import PauseCrawler, RetryRequest, SkipRequest, StopCrawler
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse, LoggedData
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
from turbocrawler.engine.data_types.info import ExecutionInfo, RunningInfo
from turbocrawler.engine.job import JobBase
from turbocrawler.engine.url_extractor import UrlExtractor

logger = logging.getLogger(__name__)


class CrawlerRunner(JobBase):
    name: str = "CrawlerRunner"

    def __init__(
        self, crawler: type[Crawler], config: CrawlerRunnerConfig | None = None, cli_kwargs: dict | None = None
    ):
        self._crawler_type = crawler
        self.log_dir_name = crawler.crawler_name
        super().__init__()

        self._last_info_log_time = datetime.now()

        self.crawler: Crawler
        self.config = config
        self.cli_kwargs = cli_kwargs or {}
        self.crawler_queue: CrawlerQueueABC

        self._requests_info = {"Made": 0, "RetryRequest": 0, "SkipRequest": 0}

    async def _initialize_runner_dependencies(self) -> None:
        logger.info(f"[Runner] crawler cli_kwargs: {self.cli_kwargs}")

        if self.config is None:
            self.config = CrawlerRunnerConfig()

        if self.config.crawler_queue_params is None:
            self.config.crawler_queue_params = dict()
        if self.config.crawled_queue_params is None:
            self.config.crawled_queue_params = dict()

        if "crawler_name" not in self.config.crawler_queue_params.keys():
            self.config.crawler_queue_params["crawler_name"] = self._crawler_type.crawler_name
        if "crawler_name" not in self.config.crawled_queue_params.keys():
            self.config.crawled_queue_params["crawler_name"] = self._crawler_type.crawler_name

        crawled_queue = self.config.crawled_queue(**self.config.crawled_queue_params)
        self.config.crawler_queue_params["crawled_queue"] = crawled_queue
        self.crawler_queue = self.config.crawler_queue(**self.config.crawler_queue_params)

        self.crawler = self._crawler_type(
            run_id=self._run_id,
            run_dir=self._run_dir,
            log_path=self._log_path,
            crawler_queue=self.crawler_queue,
            logger=logger,
            cli_kwargs=self.cli_kwargs,
        )
        self._compile_regex()

    async def run(self) -> ExecutionInfo:
        await self._initialize_runner_dependencies()

        try:
            await self._call_all_start_crawler()

            await self._remove_crawled()

            await self._login()

            await self._call_schedule_requests()

            await self._start_crawler_queue_loop()

            await self._save_all()

            return await self._call_all_stop_crawler()
        except StopCrawler as stop_crawler:
            return await self._call_all_stop_crawler(stop_crawler)
        except Exception as e:
            return await self._call_all_stop_crawler(exception=e)

    async def _call_all_start_crawler(self) -> None:
        logger.info(f"[Runner] Calling {self.crawler.crawler_name}.start_crawler")

        start_crawler_objs: list[Crawler | CrawledQueueABC] = [
            self.crawler,
            self.crawler_queue,
            self.crawler_queue.crawled_queue,
        ]
        for obj in start_crawler_objs:
            await obj.start_crawler()

    async def _call_all_stop_crawler(
        self, stop_crawler: StopCrawler = None, exception: Exception = None
    ) -> ExecutionInfo:
        forced_stop = False
        error = False
        reason = ""

        if exception:
            forced_stop = True
            error = True
            reason = str(exception)
            logger.error("[Runner] An exception happened in the execution, stopping the crawler.")
            logger.exception("[Runner] Exception traceback:")

        if stop_crawler:
            forced_stop = True
            error = stop_crawler.error
            reason = stop_crawler.reason
            logger.info(f"[Runner] StopCrawler raised reason {reason}")
        logger.info(f"[Runner] Calling {self.crawler.crawler_name}.stop_crawler")

        execution_info = ExecutionInfo(
            **vars(await self._get_running_info()),
            exception=exception,
            error=error,
            forced_stop=forced_stop,
            reason=reason,
            end_time=datetime.now(),
        )

        stop_crawler_objs: list[Crawler | CrawledQueueABC] = [
            self.crawler,
            self.crawler_queue,
            self.crawler_queue.crawled_queue,
        ]
        for obj in stop_crawler_objs:
            await obj.stop_crawler(execution_info=execution_info)

        formatted_info = pformat(execution_info, sort_dicts=False)
        logger.info(f"[Runner] Execution info\n{formatted_info}", extra={"json": execution_info})
        return execution_info

    async def _call_schedule_requests(self) -> None:
        logger.info(f"[Runner] Calling {self.crawler.crawler_name}.schedule_requests")
        await self.crawler.schedule_requests()

    async def _start_crawler_queue_loop(self) -> bool:
        logger.info("[Runner] Processing crawler queue")
        while True:
            await self._log_info()
            next_crawler_request = await self.crawler_queue.get()
            if next_crawler_request:
                await self._make_request(crawler_request=next_crawler_request)
            else:
                logger.info("[Runner] Crawler queue is empty, all crawler_requests made")
                break
        return True

    async def _make_request(self, crawler_request: CrawlerRequest) -> None:
        logger.debug(f"[Runner] [process_request] URL: {crawler_request.url}")
        request_retries = 0
        while True:
            try:
                # Wait for a random time between requests to avoid overloading the server
                wait_time = random.uniform(*self.crawler.time_between_requests)
                await asyncio.sleep(wait_time)

                # Call process_request
                process_request_function = getattr(self.crawler, crawler_request.process_request_function)
                crawler_response = await process_request_function(crawler_request=crawler_request)
                if not isinstance(crawler_response, CrawlerResponse):
                    raise StopCrawler(
                        reason="Inside Crawler process_request function must return a CrawlerResponse",
                        error=True,
                    )

                # Call process_request
                process_response_function = getattr(self.crawler, crawler_request.process_response_function)
                await process_response_function(crawler_request=crawler_request, crawler_response=crawler_response)

                # Call parse function
                if crawler_response.settings.parse_response:
                    parse_function = getattr(self.crawler, crawler_request.parse_function)
                    await parse_function(crawler_request=crawler_request, crawler_response=crawler_response)
                if crawler_response.settings.automatic_schedule:
                    await self._add_urls_to_queue(crawler_response=crawler_response)

                self._requests_info["Made"] += 1
                break
            except RetryRequest as error:
                self._requests_info["RetryRequest"] += 1
                request_retries += 1
                max_retries = error.retries
                if request_retries >= max_retries:
                    msg = f"Exceed retries for url {crawler_request.url}|Reason: {error.reason}"
                    logger.error(f"[Runner] {msg}")
                    if error.stop_crawler:
                        raise StopCrawler(reason=msg, error=True)
                    break
            except SkipRequest as error:
                self._requests_info["SkipRequest"] += 1
                logger.info(f"[Runner] Skipping request for url {crawler_request.url}|Reason: {error.reason}")
                break
            except PauseCrawler as pause_crawler:
                logger.info(f"[Runner] Pausing crawler for {pause_crawler.time} seconds|Reason: {pause_crawler.reason}")
                await asyncio.sleep(pause_crawler.time)
                break

    async def _add_urls_to_queue(self, crawler_response: CrawlerResponse) -> None:
        if not self.crawler.regex_extract_rules:
            return None

        if self.crawler.regex_extract_rules[0] == "*":
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.url,
                html_text=crawler_response.text,
                allowed_domains=self.crawler.allowed_domains,
            )
        else:
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.url,
                html_text=crawler_response.text,
                extract_rules=self.crawler.regex_extract_rules,
                allowed_domains=self.crawler.allowed_domains,
            )

        for url in urls_to_extract:
            crawler_request = CrawlerRequest(
                url=url,
                headers=crawler_response.headers,
                cookies=crawler_response.cookies,
                kwargs=crawler_response.kwargs,
            )
            await self.crawler_queue.add(crawler_request=crawler_request)

    def _compile_regex(self) -> None:
        for i, extract_rule in enumerate(self.crawler.regex_extract_rules):
            raw_regex = extract_rule.regex
            if not isinstance(raw_regex, re.Pattern):
                self.crawler.regex_extract_rules[i].regex = re.compile(raw_regex)

    async def _login(self) -> LoggedData:
        logger.info(f"[Runner] Calling {self.crawler.crawler_name}.login")
        self.crawler.logged_data = await self.crawler.login()
        return self.crawler.logged_data

    async def _save_all(self) -> None:
        logger.info(f"[Runner] Calling {self.crawler.crawler_name}.save_all")
        await self.crawler.save_all()

    async def _remove_crawled(self) -> None:
        extract_rules_remove_crawled = [
            extract_rule for extract_rule in self.crawler.regex_extract_rules if extract_rule.remove_crawled
        ]
        await self.crawler_queue.crawled_queue.remove_urls_with_remove_crawled(
            extract_rules_remove_crawled=extract_rules_remove_crawled
        )

    async def _get_running_info(self) -> RunningInfo:
        return RunningInfo(
            crawler_name=self.crawler.crawler_name,
            crawler_queue=await self.crawler_queue.get_info(),
            crawled_queue=await self.crawler_queue.crawled_queue.get_info(),
            requests_made=self._requests_info["Made"],
            requests_retried=self._requests_info["RetryRequest"],
            requests_skipped=self._requests_info["SkipRequest"],
            running_time=self.running_time(),
            start_time=self._start_process_time,
            run_id=self._run_id,
            run_dir=self._run_dir,
            log_path=self._log_path,
        )

    async def _log_info(self) -> None:
        have_passed_time = self._last_info_log_time + timedelta(minutes=1) < datetime.now()
        if have_passed_time:
            self._last_info_log_time = datetime.now()
            running_info = await self._get_running_info()
            formatted_info = pformat(running_info, sort_dicts=False)
            logger.info(f"[Runner]\n{formatted_info}")

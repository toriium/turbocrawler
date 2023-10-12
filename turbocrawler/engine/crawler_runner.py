import re
import time
from datetime import datetime, timedelta
from multiprocessing import cpu_count
from pprint import pformat

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import ReMakeRequest, SkipRequest, StopCrawler
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.models import CrawlerRequest, CrawlerResponse, RunningInfo
from turbocrawler.engine.url_extractor import UrlExtractor
from turbocrawler.engine.worker_queues import WorkerQueueManager
from turbocrawler.logger import logger
from turbocrawler.queues.crawler_queues import FIFOMemoryQueue


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], crawler_queue: CrawlerQueueABC = None):
        self.__start_process_time = datetime.now()
        self.__last_info_log_time = datetime.now()
        self.crawler = crawler
        if not crawler_queue:
            crawler_queue = FIFOMemoryQueue(crawler_name=crawler.crawler_name)
        self.crawler_queue = crawler_queue
        self.parse_queue_manager: WorkerQueueManager = WorkerQueueManager(queue_name='parse_queue',
                                                                          class_object=self.crawler,
                                                                          target=self.crawler.parse_crawler_response,
                                                                          qtd_workers=cpu_count())
        self.parse_queue_manager.start_workers()
        self.__compile_regex()
        self.__requests_info = {
            "Made": 0,
            "ReMakeRequest": 0,
            "SkipRequest": 0,
        }

    def run(self):
        self.crawler = self.crawler()
        self.crawler.crawler_queue = self.crawler_queue

        try:
            self.__call_all_start_crawler()
            self.__remove_crawled()

            self.__call_crawler_first_request()

            self.__process_crawler_queue()

            self.__call_all_stop_crawler()
        except StopCrawler as error:
            self.__call_all_stop_crawler(error)

    def __call_all_start_crawler(self):
        logger.info(f'Calling  {self.crawler.crawler_name}.start_crawler')
        self.crawler.start_crawler()
        self.crawler_queue.crawled_queue.start_crawler()

    def __call_all_stop_crawler(self, stop: StopCrawler = None):
        forced_stop = False
        reason = ""
        if stop:
            forced_stop = True
            reason = stop.reason
            logger.info(f'StopCrawler raised reason {reason}')
        logger.info(f'Calling  {self.crawler.crawler_name}.stop_crawler')

        running_time = datetime.now() - self.__start_process_time
        execution_info = {
            **self.__get_running_info(),
            "forced_stop": forced_stop,
            "reason": reason,
            "running_time": running_time,
        }

        self.crawler_queue.crawled_queue.stop_crawler()
        self.crawler.stop_crawler(execution_info=execution_info)

        logger.info(f'Execution info\n{pformat(execution_info)}')

    def __call_crawler_first_request(self):
        logger.info(f'Calling  {self.crawler.crawler_name}.crawler_first_request')
        crawler_response = self.crawler.crawler_first_request()
        if crawler_response is not None:
            self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.site_url)
            self.crawler.parse_crawler_response(crawler_response=crawler_response)
            self.__add_urls_to_queue(crawler_response=crawler_response)

    def __process_crawler_queue(self):
        logger.info('Processing crawler queue')

        # get requests from crawler queue
        while True:
            self.__log_info()
            next_crawler_request = self.crawler_queue.get_request_from_queue()
            if not next_crawler_request:
                logger.info('Crawler queue is empty, all crawler_requests made')

                # Wait until parse_queue is empty
                self.parse_queue_manager.stop_workers()
                logger.info('Parse queue is empty, all parse_crawler_response made')
                return True

            self.__make_request(crawler_request=next_crawler_request)

    def __make_request(self, crawler_request: CrawlerRequest):
        request_retries = 0
        while True:
            try:
                time.sleep(self.crawler.time_between_requests)
                logger.debug(f'[process_request] URL: {crawler_request.site_url}')
                crawler_response = self.crawler.process_request(crawler_request=crawler_request)
                self.__add_urls_to_queue(crawler_response=crawler_response)

                self.parse_queue_manager.queue.put({"crawler_response": crawler_response})
                self.__requests_info['Made'] = self.__requests_info['Made'] + 1
                break
            except ReMakeRequest as error:
                self.__requests_info['ReMakeRequest'] = self.__requests_info['ReMakeRequest'] + 1
                request_retries += 1
                error_retries = error.retries
                if request_retries >= error_retries:
                    logger.warn(f'Exceed retry tentatives for url {crawler_request.site_url}')
                    break
            except SkipRequest as error:
                self.__requests_info['SkipRequest'] = self.__requests_info['SkipRequest'] + 1
                logger.info(f'Skipping request for url {crawler_request.site_url} reason: {error.reason}')
                break

    def __add_urls_to_queue(self, crawler_response: CrawlerResponse) -> None:
        if not self.crawler.regex_extract_rules:
            return None

        if self.crawler.regex_extract_rules[0] == '*':
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.site_url,
                html_body=crawler_response.site_body,
                allowed_domains=self.crawler.allowed_domains)
        else:
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.site_url,
                html_body=crawler_response.site_body,
                extract_rules=self.crawler.regex_extract_rules,
                allowed_domains=self.crawler.allowed_domains)

        for url in urls_to_extract:
            crawler_request = CrawlerRequest(site_url=url,
                                             headers=crawler_response.headers,
                                             cookies=crawler_response.cookies,
                                             proxy=None)
            self.crawler_queue.add_request_to_queue(crawler_request=crawler_request)

    def __compile_regex(self):
        for i, extract_rule in enumerate(self.crawler.regex_extract_rules):
            raw_regex = extract_rule.regex
            if not isinstance(raw_regex, re.Pattern):
                self.crawler.regex_extract_rules[i].regex = re.compile(raw_regex)

    def __remove_crawled(self):
        extract_rules_remove_crawled = [extract_rule for extract_rule in self.crawler.regex_extract_rules
                                        if extract_rule.remove_crawled]
        self.crawler_queue.crawled_queue.remove_urls_with_remove_crawled(
            extract_rules_remove_crawled=extract_rules_remove_crawled)

    def __get_running_info(self) -> RunningInfo:
        return {
            "crawler_queue": len(self.crawler_queue),
            "crawled_queue": len(self.crawler_queue.crawled_queue),
            "scheduled_requests": self.crawler_queue.scheduled_requests,
            "requests_made": self.__requests_info["Made"],
            "requests_remade": self.__requests_info["ReMakeRequest"],
            "requests_skipped": self.__requests_info["SkipRequest"]
        }

    def __log_info(self):
        have_passed_time = self.__last_info_log_time + timedelta(minutes=1) < datetime.now()
        if have_passed_time:
            crawler_info = self.__get_running_info()
            msg = '\n'
            for key, value in crawler_info.items():
                msg += f'{key}: {value}\n'
            logger.info(msg)

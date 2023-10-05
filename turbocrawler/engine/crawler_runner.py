import re
import time
from multiprocessing import cpu_count

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import ReMakeRequest, SkipRequest, StopCrawler
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.models import CrawlerRequest, CrawlerResponse
from turbocrawler.engine.url_extractor import UrlExtractor
from turbocrawler.engine.worker_queues import WorkerQueueManager
from turbocrawler.logger import logger
from turbocrawler.queues.crawler_queues import FIFOMemoryQueue


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], crawler_queue: CrawlerQueueABC = None):
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

    def run(self):
        self.crawler = self.crawler()
        self.crawler.crawler_queue = self.crawler_queue

        try:
            self.__call_all_start_crawler()
            self.__remove_crawled()

            self.__call_crawler_first_request()

            self.__process_crawler_queue()

            self.__call_all_stop_crawler()
        except StopCrawler:
            self.__call_all_stop_crawler()

    def __call_all_start_crawler(self):
        logger.info('Calling  start_crawler')
        self.crawler.start_crawler()
        self.crawler_queue.crawled_queue.start_crawler()

    def __call_all_stop_crawler(self):
        logger.info('Calling  stop_crawler')
        self.crawler.stop_crawler()
        self.crawler_queue.crawled_queue.stop_crawler()

    def __call_crawler_first_request(self):
        logger.info('Calling  crawler_first_request')
        crawler_response = self.crawler.crawler_first_request()
        if crawler_response is not None:
            self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.site_url)
            self.crawler.parse_crawler_response(crawler_response=crawler_response)
            self.__add_urls_to_queue(crawler_response=crawler_response)

    def __process_crawler_queue(self):
        logger.info('Processing crawler queue')

        # get requests from crawler queue
        while True:
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
                break
            except ReMakeRequest as error:
                request_retries += 1
                error_retries = error.retries
                if request_retries >= error_retries:
                    logger.warn(f'Exceed retry tentatives for url {crawler_request.site_url}')
                    break
            except SkipRequest:
                logger.info(f'Skipping request for url {crawler_request.site_url}')
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

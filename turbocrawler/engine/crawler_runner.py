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
            crawler_queue = FIFOMemoryQueue()
        self.crawler_queue = crawler_queue
        self.parse_queue_manager: WorkerQueueManager = WorkerQueueManager(queue_name='parse_queue',
                                                                          class_object=self.crawler,
                                                                          target=self.crawler.parse_crawler_response,
                                                                          qtd_workers=cpu_count())
        self.parse_queue_manager.start_workers()

    def run(self):
        self.crawler = self.crawler()
        self.crawler.crawler_queue = self.crawler_queue

        try:
            logger.info('Calling  start_crawler')
            self.crawler.start_crawler()

            logger.info('Calling  crawler_first_request')
            crawler_response = self.crawler.crawler_first_request()
            if crawler_response is not None:
                self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.site_url)
                self.crawler.parse_crawler_response(crawler_response=crawler_response)
                self.__add_urls_to_queue(crawler_response=crawler_response)

            logger.info('Processing crawler queue')
            self.__process_crawler_queue()

            logger.info('Calling  stop_crawler')
            self.crawler.stop_crawler()
        except StopCrawler:
            logger.exception('Calling  stop_crawler')
            self.crawler.stop_crawler()

    def __process_crawler_queue(self):
        # get_request_from_queue
        while True:
            next_crawler_request = self.crawler_queue.get_request_from_queue()
            if not next_crawler_request:
                logger.info('Crawler queue is empty, all crawler_requests made')
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
        if not self.crawler.regex_rules:
            return None

        if self.crawler.regex_rules[0] == '*':
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.site_url,
                html_body=crawler_response.site_body,
                allowed_domains=self.crawler.allowed_domains)
        else:
            urls_to_extract = UrlExtractor.get_urls(
                site_current_url=crawler_response.site_url,
                html_body=crawler_response.site_body,
                regex_rules=self.crawler.regex_rules,
                allowed_domains=self.crawler.allowed_domains)

        for url in urls_to_extract:
            crawler_request = CrawlerRequest(site_url=url,
                                             headers=crawler_response.headers,
                                             cookies=crawler_response.cookies,
                                             proxy=None)
            self.crawler_queue.add_request_to_queue(crawler_request=crawler_request)

import time

from crawler_manager.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from crawler_manager.engine.control import ReMakeRequest, SkipRequest, StopCrawler
from crawler_manager.engine.crawler import Crawler
from crawler_manager.engine.models import CrawlerRequest, CrawlerResponse
from crawler_manager.engine.url_extractor import UrlExtractor
from crawler_manager.logger import logger
from crawler_manager.queues.crawler_queues import FIFOMemoryQueue


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], crawler_queue: CrawlerQueueABC = None):
        self.crawler = crawler
        if not crawler_queue:
            crawler_queue = FIFOMemoryQueue()
        self.crawler_queue = crawler_queue

    def run(self):
        self.crawler = self.crawler()
        self.crawler.crawler_queue = self.crawler_queue

        try:
            self.crawler.start_crawler()

            crawler_response = self.crawler.crawler_first_request()
            self.crawler_queue.crawled_queue.add_url_to_crawled_queue(crawler_response.site_url)
            self.crawler.parse_crawler_response(crawler_response=crawler_response)
            self.__add_urls_to_queue(crawler_response=crawler_response)

            self.__process_crawler_queue()

            self.crawler.stop_crawler()
        except StopCrawler:
            self.crawler.stop_crawler()

    def __process_crawler_queue(self):
        # get_request_from_queue
        while True:
            next_crawler_request = self.crawler_queue.get_request_from_queue()
            if not next_crawler_request:
                logger.info('All requests were made')
                return True

            self.__make_request(crawler_request=next_crawler_request)

    def __make_request(self, crawler_request: CrawlerRequest):
        request_retries = 0
        while True:
            try:
                time.sleep(self.crawler.time_between_requests)
                crawler_response = self.crawler.process_request(crawler_request=crawler_request)
                self.__add_urls_to_queue(crawler_response=crawler_response)
                self.crawler.parse_crawler_response(crawler_response=crawler_response)
                break
            except ReMakeRequest as error:
                request_retries += 1
                error_retries = error.retries
                if request_retries >= error_retries:
                    logger.warn(f'Exceed retry tentatives for url {crawler_request.site_url}')
                    break
            except SkipRequest:
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

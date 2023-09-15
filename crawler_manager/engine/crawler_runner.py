import time

from crawler_manager.engine.control import ReMakeRequest, SkipRequest, StopCrawler
from crawler_manager.engine.crawler import Crawler
from crawler_manager.engine.crawler_queue import CrawlerQueue
from crawler_manager.engine.models import CrawlerRequest, CrawlerResponse
from crawler_manager.engine.url_extractor import UrlExtractor


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler], crawler_queue: CrawlerQueue):
        self.crawler = crawler
        self.crawler_queue = crawler_queue

    def run(self):
        self.crawler = self.crawler()
        if 'crawler_queue' in self.crawler.__annotations__:
            self.crawler.crawler_queue = self.crawler_queue

        try:
            self.crawler.start_crawler()

            crawler_response = self.crawler.crawler_first_request()
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
                print('All requests were made')
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
                    print('Exceed retry tentatives')
                    break
            except SkipRequest:
                break

    def __add_urls_to_queue(self, crawler_response: CrawlerResponse):
        urls_to_extract = UrlExtractor.get_urls(
            site_current_url=crawler_response.site_url,
            html_body=crawler_response.site_body,
            regex_rules=self.crawler.regex_rules,
            allowed_domains=self.crawler.allowed_domains)
        for url in urls_to_extract:
            crawler_request = CrawlerRequest(site_url=url)
            self.crawler_queue.add_request_to_queue(crawler_request=crawler_request)

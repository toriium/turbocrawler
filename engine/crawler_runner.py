from engine.crawler import Crawler
from engine.crawler_queue import CrawlerQueue
from engine.crawler_request import CrawlerRequest
from engine.crawler_response import CrawlerResponse
from engine.url_extractor import UrlExtractor


class CrawlerRunner:
    def __init__(self, crawler: type[Crawler]):
        self.crawler = crawler
        self.crawler_queue = CrawlerQueue(crawler_name=self.crawler.crawler_name)

    def run(self):
        self.crawler = self.crawler()
        self.crawler.start_crawler()

        crawler_response = self.crawler.crawler_first_request()
        self.__add_urls_to_queue(crawler_response=crawler_response)
        self.__process_crawler_queue()

        self.crawler.stop_crawler()

    def __process_crawler_queue(self):
        while True:
            next_request_url = self.crawler_queue.get_request_from_queue()
            if not next_request_url:
                print('All requests were made')
                return True
            next_request = CrawlerRequest(site_url=next_request_url)
            crawler_response = self.crawler.process_request(crawler_request=next_request)

            self.__add_urls_to_queue(crawler_response=crawler_response)
            self.crawler.parse_crawler_response(crawler_response=crawler_response)

    def __add_urls_to_queue(self, crawler_response: CrawlerResponse):
        urls_to_extract = UrlExtractor.get_urls(
            site_current_url=crawler_response.site_url,
            html_body=crawler_response.site_body,
            regex_rules=self.crawler.regex_rules,
            allowed_domains=self.crawler.allowed_domains)
        for url in urls_to_extract:
            self.crawler_queue.add_request_to_queue(url=url)

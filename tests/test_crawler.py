from pprint import pprint

import requests
from parsel import Selector

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo, ExtractRule
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue
from turbocrawler.queues.crawler_queues import FIFOMemoryQueue


class QuotesToScrapeCrawler(Crawler):
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = 1
    session: requests.Session

    def start_crawler(self) -> None:
        self.session = requests.session()

    def crawler_first_request(self) -> CrawlerResponse | None:
        url = "https://quotes.toscrape.com/page/1/"
        response = self.session.get(url=url)
        return CrawlerResponse(site_url=response.url,
                               site_body=response.text,
                               status_code=response.status_code)

    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        response = self.session.get(crawler_request.site_url)
        return CrawlerResponse(site_url=response.url,
                               site_body=response.text,
                               status_code=response.status_code)

    def parse_crawler_response(self, crawler_response: CrawlerResponse) -> None:
        selector = Selector(crawler_response.site_body)
        quote_list = selector.css('div[class="quote"]')
        for quote in quote_list:
            data = {"quote": quote.css('span:nth-child(1)::text').get()[1:-1],
                    "author": quote.css('span:nth-child(2)>small::text').get(),
                    "tags_list": quote.css('div[class="tags"]>a::text').getall()}
            pprint(data)

    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        self.session.close()


crawled_queue = MemoryCrawledQueue(crawler_name=QuotesToScrapeCrawler.crawler_name, save_crawled_queue=True,
                                   load_crawled_queue=False)
crawler_queue = FIFOMemoryQueue(crawler_name=QuotesToScrapeCrawler.crawler_name, crawled_queue=crawled_queue)
CrawlerRunner(crawler=QuotesToScrapeCrawler, crawler_queue=crawler_queue).run()
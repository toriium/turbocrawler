import requests
from parsel import Selector

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo, ExtractRule
from turbocrawler.engine.plugin import Plugin
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue
from turbocrawler.queues.crawler_queues import FIFOMemoryCrawlerQueue


class TestPlugin(Plugin):

    def start_crawler(self) -> None:
        print("[Plugin] start_crawler")

    def crawler_first_request(self) -> None:
        print("[Plugin] crawler_first_request")

    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | CrawlerRequest | None:
        print("[Plugin] process_request")
        return None

    def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> CrawlerResponse:
        print("[Plugin] process_response")
        return crawler_response

    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        print("[Plugin] process_request")


class QuotesToScrapeCrawler(Crawler):
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = 1
    session: requests.Session

    @classmethod
    def start_crawler(cls) -> None:
        cls.session = requests.session()

    @classmethod
    def crawler_first_request(cls) -> CrawlerResponse | None:
        response = cls.session.get(url="https://quotes.toscrape.com/page/1/")
        return CrawlerResponse(url=response.url,
                               body=response.text,
                               status_code=response.status_code)

    @classmethod
    def process_request(cls, crawler_request: CrawlerRequest) -> CrawlerResponse:
        response = cls.session.get(crawler_request.url)
        return CrawlerResponse(url=response.url,
                               body=response.text,
                               status_code=response.status_code)

    @classmethod
    def parse_crawler_response(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = Selector(crawler_response.body)
        quote_list = selector.css('div[class="quote"]')
        for quote in quote_list:
            data = {"quote": quote.css('span:nth-child(1)::text').get()[1:-1],
                    "author": quote.css('span:nth-child(2)>small::text').get(),
                    "tags_list": quote.css('div[class="tags"]>a::text').getall()}

    @classmethod
    def stop_crawler(cls, execution_info: ExecutionInfo) -> None:
        cls.session.close()


crawled_queue = MemoryCrawledQueue(crawler_name=QuotesToScrapeCrawler.crawler_name,
                                   save_crawled_queue=True,
                                   load_crawled_queue=False)
crawler_queue = FIFOMemoryCrawlerQueue(crawler_name=QuotesToScrapeCrawler.crawler_name, crawled_queue=crawled_queue)
CrawlerRunner(crawler=QuotesToScrapeCrawler, plugins=[TestPlugin], crawler_queue=crawler_queue).run()

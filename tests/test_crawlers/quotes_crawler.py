from pprint import pprint

import requests
from selectolax.lexbor import LexborHTMLParser

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule


class QuotesToScrapeCrawler(Crawler):
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape.com']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = 1
    session: requests.Session

    @classmethod
    def start_crawler(cls) -> None:
        cls.session = requests.session()

    @classmethod
    def crawler_first_request(cls) -> CrawlerResponse | None:
        plugin = cls.get_plugin("TestPlugin")
        cls.crawler_queue.add(CrawlerRequest(url="https://quotes.toscrape.com/page/9/"))
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
    def process_response(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        crawler_response.kwargs['success'] = True

    @classmethod
    def parse(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = LexborHTMLParser(crawler_response.body)
        quote_list = selector.css('div[class="quote"]')
        for quote in quote_list:
            data = {"quote": quote.css_first('span:nth-child(1)').text()[1:-1],
                    "author": quote.css_first('span:nth-child(2)>small').text(),
                    "tag_list": [tag.text() for tag in quote.css('div[class="tags"]>a') if tag]}
            pprint(data)

    @classmethod
    def stop_crawler(cls, execution_info: ExecutionInfo) -> None:
        cls.session.close()

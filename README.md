# TurboCrawler

# What it is?
It is a Micro-Framework that you can use to build your crawlers easily, focused in being fast, extremely
customizable and easy to use, giving you the power to control the crawler behavior. Provide ways to schedule requests,
parse your data asynchronously, extract redirect links from an HTML page.

## Code Example
```python
from pprint import pprint
import requests
from parsel import Selector
from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo, ExtractRule


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
    def parse(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = Selector(crawler_response.body)
        for quote in selector.css('div[class="quote"]'):
            data = {"quote": quote.css('span:nth-child(1)::text').get()[1:-1],
                    "author": quote.css('span:nth-child(2)>small::text').get(),
                    "tags_list": quote.css('div[class="tags"]>a::text').getall()}
            pprint(data)

    @classmethod
    def stop_crawler(cls, execution_info: ExecutionInfo) -> None:
        cls.session.close()


CrawlerRunner(crawler=QuotesToScrapeCrawler).run()
```

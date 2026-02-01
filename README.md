# TurboCrawler


# What is it?
TurboCrawler is a micro-framework that makes it easy to build your own crawlers. It is designed to be fast, highly customizable, extensible, and easy to use, giving you full control over crawler behavior.
It provides tools to schedule requests, parse your data asynchronously, and extract redirect links from HTML pages.


# Installation

```sh
pip install turbocrawler
```


# Code Example

```python
import asyncio
from pprint import pprint
import requests
from selectolax.lexbor import LexborHTMLParser
from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule
from turbocrawler.engine.control import ReMakeRequest
from turbocrawler.engine.runners.crawler_runner import CrawlerRunner


class QuotesToScrapeCrawler(Crawler):
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape.com']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = (0.5, 1)
    session: requests.Session

    async def start_crawler(self) -> None:
        self.session = requests.session()

    async def crawler_first_request(self) -> CrawlerResponse | None:
        await self.crawler_queue.add(CrawlerRequest(url="https://quotes.toscrape.com/page/9/"))
        response = self.session.get(url="https://quotes.toscrape.com/page/1/")
        return CrawlerResponse(url=response.url,
                               body=response.text,
                               status_code=response.status_code)

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        response = self.session.get(crawler_request.url)
        return CrawlerResponse(url=response.url,
                               body=response.text,
                               status_code=response.status_code)

    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = LexborHTMLParser(crawler_response.body)
        quote_list = selector.css('div[class="quote"]')
        if not quote_list:
            raise ReMakeRequest(retries=2)
        crawler_response.kwargs['success'] = True

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = LexborHTMLParser(crawler_response.body)
        quote_list = selector.css('div[class="quote"]')
        for quote in quote_list:
            data = {"quote": quote.css_first('span:nth-child(1)').text()[1:-1],
                    "author": quote.css_first('span:nth-child(2)>small').text(),
                    "tag_list": [tag.text() for tag in quote.css('div[class="tags"]>a') if tag]}
            pprint(data)

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        self.session.close()

if __name__ == '__main__':
    asyncio.run(CrawlerRunner(crawler=QuotesToScrapeCrawler).run())
```

# Understanding TurboCrawler

## Crawler
### Attributes
- `crawler_name`: The name of your crawler. This info will be used by `CrawledQueue`.
- `allowed_domains`: List containing all domains that the crawler may add to `CrawlerQueue`.
- `regex_extract_rules`: List containing `ExtractRule` objects. The regex passed here will be used to extract all redirect links from an HTML page (e.g., 'href="/users"') that you return in `CrawlerResponse.body`. If you leave this list empty, it will not enable the automatic population of `CrawlerQueue` for every `CrawlerResponse.body`.
- `time_between_requests`: Time range that each request will have to wait before being executed.


### Methods
#### `start_crawler`
Use this to start a session, webdriver, etc.

#### `crawler_first_request`
Use this to make the first request to a site (normally the login). It can also be used to schedule the first pages to crawl.
Possible returns:
- `CrawlerResponse`: The response will be sent to the `parse` method and follow the rule in **OBS-1**.
- `None`: The response will not be sent to the `parse` method.

#### `process_request`
This method receives all scheduled requests in the `CrawlerQueue.add`, either added manually or by automatic scheduling with `regex_extract_rules`.
Here you must implement all your request logic: cookies, headers, proxy, retries, etc.
The method receives a `CrawlerRequest` and must return a `CrawlerResponse`.
See **OBS-1**.

#### `process_response`
This method receives all requests made by `process_request`.
Here you can implement any logic, such as scheduling requests, validating responses, retrying logic, etc.
This method is optional.

#### `parse`
This method receives all `CrawlerResponse` objects from `crawler_first_request`, `process_request`, or `process_response`.
Here you can parse your response, extract the target fields from HTML, and dump the data (e.g., to a database).

#### `stop_crawler`
Use this to close a session, webdriver, etc.

OBS:
1. If `regex_extract_rules` is filled, the redirects specified in the rules will be scheduled in the `CrawlerQueue`. If not, no requests will be scheduled automatically.

### Order of calls
1. `start_crawler`
2. `crawler_first_request`
3. Start a loop executing the methods sequentially: `process_request` -> `process_response` -> `parse` (repeat until the `CrawlerQueue` is empty).
4. `stop_crawler`

---


## CrawlerRunner
Responsible for running the Crawler, calling the methods in order, automatically scheduling your requests, and handling the queues.
By default, it uses:
- `FIFOMemoryCrawlerQueue` for `CrawlerQueue`
- `MemoryCrawledQueue` for `CrawledQueue`

But you can change these using the built-in queues in `turbocrawler.queues` or by creating your own queues.

---


## CrawlerQueue
The CrawlerQueue stores your `CrawlerRequest` objects, which are then removed and processed by `process_request`.

---


## CrawledQueue
The CrawledQueue stores all URLs from processed `CrawlerRequest` objects. It prevents dispatching a request to an already crawled URL, but this behavior can be changed.

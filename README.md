# TurboCrawler

# What it is?
It is a Micro-Framework that you can use to build your crawlers easily, focused in being fast, extremely
customizable, extensible and easy to use, giving you the power to control the crawler behavior. 
Provide ways to schedule requests, parse your data asynchronously, extract redirect links from an HTML page.

# Install

```sh
pip install turbocrawler
```

# Code Example

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
# Understanding the turbocrawler:

## Crawler
### Attributes
- `crawler_name` the name of your crawler, this info will be used by `CrawledQueue`
- `allowed_domains` list containing all domains that the crawler may add to `CrawlerQueue`
- `regex_extract_rules` list containing `ExtractRule` objects, the regex passed here will be  
  used to extract all redirect links from an HTML page, EX: 'href="/users"', that you return in `CrawlerResponse.body`  
  If you let this list empty will not enable the automatic population of `CrawlerQueue` for every `CrawlerResponse.body`
- `time_between_requests` Time that each request will have to wait before being executed

### Methods
#### `start_crawler`
Should be used to start a session, webdriver, etc...

#### `crawler_first_request`
Should be used to make the first request in a site normally the login,
Here could also be used to schedule the first pages to crawl.  
2 possible Returns:
- return `CrawlerResponse` the response will be sent to `parse` method and apply follow rule **OBS-1  
- return `None` the response will not be sent to `parse` method

#### `process_request`
This method receives all scheduled requests in the `CrawlerQueue.add`
being added through manual `CrawlerQueue.add` or by automatic schedule with regex_extract_rules.  
Here you must implement all your request logic, cookies, headers, proxy, retries, etc...  
The method receives a `CrawlerRequest` and must return a `CrawlerResponse`.  
Apply follow rule **OBS-1.

#### `process_respose`
This method receives all requests made by `process_request`  
Here you can implement any logic, like, scheduling requests,
validating response, remake the requests, etc...
Isn't mandatory to implement this method

#### `parse`
This method receives all `CrawlerResponse` from
`crawler_first_request`, `process_request` or `process_respose`  
Here you can parse your response,
getting the targets fields from HTML and dump the data, in a database for example.

#### `stop_crawler`
Should be used to close a session, webdriver, etc...

OBS:
1. If filled `regex_extract_rules` the redicts specified in the rules will schedule
   in the `CrawlerQueue`, if not filled `regex_extract_rules` will not schedule any request.

### Order of calls
1. `start_crawler`
2. `crawler_first_request`
3. Start loop executing the methods sequentially `process_request` -> `process_response` -> `parse` -> loop forever.  
   The loop only stops when `CrawlerQueue` is empty.
4. `stop_crawler`

---

## CrawlerRunner
Is the responsible to run the Crawler, calling the methods in order,
responsible to automatic schedule your requests, and handle the queues.  
It uses by default:
- `FIFOMemoryCrawlerQueue` for `CrawlerQueue`  
- `MemoryCrawledQueue` for `CrawledQueue`

But you can change it using the built-ins queues
in `turbocrawler.queues` or creating your own queues

---

## CrawlerQueue
CrawlerQueue is where yours `CrawlerRequest` are stored
and then will be removed to be processed at `process_request`

---

## CrawledQueue
CrawledQueue is where all urls from the processed `CrawlerRequest` are stored
It prevents to remake a request to the same url, but this behavior can be changed.

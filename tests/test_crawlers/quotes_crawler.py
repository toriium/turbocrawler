import asyncio
import json

import httpx
from pydantic import BaseModel
from selectolax.lexbor import LexborHTMLParser

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo, ExtractRule, LoggedData
from turbocrawler.engine.control import RetryRequest


class Quote(BaseModel):
    author: str
    quote: str

class QuotesToScrapeCrawler(Crawler):
    # Lib Attributes
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape.com']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = (0.5, 1)

    # Personal Attributes
    client: httpx.Client
    quote_list: list[Quote] = []


    async def start_crawler(self) -> None:
        self.client = httpx.Client()

    async def login(self) -> LoggedData:
        username = self.cli_kwargs["username"]
        password = self.cli_kwargs["password"]
        login_url = "https://quotes.toscrape.com/login"
        response = self.client.post(login_url, data={"username": username, "password": password}, follow_redirects=True)
        if response.status_code != 200:
            raise Exception("Login Failed")

        return LoggedData(cookies=dict(self.client.cookies),
                          headers=self.client.headers,
                          local_storage={})

    async def schedule_requests(self) -> None:
        await self.crawler_queue.add(CrawlerRequest(url="https://quotes.toscrape.com/page/1/"))


    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        response = self.client.get(crawler_request.url)
        return CrawlerResponse(
            url=str(response.url),
            text=response.text,
            status_code=response.status_code
        )

    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector = LexborHTMLParser(crawler_response.text)
        quote_list = selector.css('div[class="quote"]')
        if not quote_list:
            raise RetryRequest(reason="No quotes found", retries=2)
        crawler_response.kwargs['selector'] = selector

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        selector: LexborHTMLParser = crawler_response.kwargs['selector']
        quote_list = selector.css('div[class="quote"]')
        for quote in quote_list:
            data = {"quote": quote.css_first('span:nth-child(1)').text()[1:-1],
                    "author": quote.css_first('span:nth-child(2)>small').text(),
                    "tag_list": [tag.text() for tag in quote.css('div[class="tags"]>a') if tag]}
            self.quote_list.append(Quote(**data))

    async def save_all(self) -> None:
        self.logger.info("All data parsed, saving to quotes.json")
        with open("quotes.json", "w") as f:
            json.dump([quote.model_dump() for quote in self.quote_list], f, indent=4)

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        self.client.close()

if __name__ == '__main__':
    cli_kwargs = {"username": "admin", "password": "123"}
    asyncio.run(CrawlerRunner(crawler=QuotesToScrapeCrawler, cli_kwargs=cli_kwargs).start())
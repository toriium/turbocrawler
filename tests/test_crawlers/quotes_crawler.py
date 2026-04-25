import asyncio
import json

import requests
from pydantic import BaseModel
from selectolax.lexbor import LexborHTMLParser

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule
from turbocrawler.engine.control import ReMakeRequest
from turbocrawler.engine.data_types.crawler import LoggedData
from turbocrawler.engine.runners.crawler_runner import CrawlerRunner


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
    session: requests.Session
    quote_list: list[Quote] = []


    async def start_crawler(self) -> None:
        self.session = requests.session()

    async def login(self) -> LoggedData:
        username = self.cli_kwargs["username"]
        password = self.cli_kwargs["password"]
        login_url = "https://quotes.toscrape.com/login"
        response = self.session.post(login_url, data={"username": username, "password": password}, allow_redirects=True)
        if response.status_code != 200:
            raise Exception("Login Failed")

        return LoggedData(cookies=self.session.cookies.get_dict(),
                          headers=self.session.headers,
                          local_storage={})

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
            self.quote_list.append(Quote(**data))

    async def save_all(self) -> None:
        self.logger.info("All data parsed, saving to quotes.json")
        with open("quotes.json", "w") as f:
            json.dump([quote.model_dump() for quote in self.quote_list], f, indent=4)

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        self.session.close()

if __name__ == '__main__':
    cli_kwargs = {"username": "admin", "password": "123"}
    asyncio.run(CrawlerRunner(crawler=QuotesToScrapeCrawler, cli_kwargs=cli_kwargs).start())
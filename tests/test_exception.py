import asyncio

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo


class CrawlerWithException(Crawler):
    crawler_name = "CrawlerWithException"

    async def start_crawler(self) -> None:
        self.fake_method()  # Will raise an exception

    async def schedule_requests(self) -> None:
        return None

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse: ...

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None: ...


if __name__ == "__main__":
    asyncio.run(CrawlerRunner(crawler=CrawlerWithException, cli_kwargs={}).start())

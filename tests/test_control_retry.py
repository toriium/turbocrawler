import asyncio

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo
from turbocrawler.engine.control import RetryRequest


class RetryCrawler(Crawler):
    crawler_name = "RetryCrawler"

    async def start_crawler(self) -> None: ...

    async def schedule_requests(self) -> None:
        await self.crawler_queue.add(CrawlerRequest(url="https://test.com"))

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        force_stop = self.cli_kwargs["force_stop"]
        raise RetryRequest(reason="Test Retry", retries=2, stop_crawler=force_stop)

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None: ...


async def test_retry_force_stop():
    # Setup
    cli_kwargs = {"force_stop": True}
    execution_info: ExecutionInfo = await CrawlerRunner(crawler=RetryCrawler, cli_kwargs=cli_kwargs).start()

    # Assert
    assert execution_info["error"] is True
    assert "Test Retry" in execution_info["reason"]
    assert execution_info["requests_retried"] == 2


async def test_retry_no_force_stop():
    # Setup
    cli_kwargs = {"force_stop": False}
    execution_info: ExecutionInfo = await CrawlerRunner(crawler=RetryCrawler, cli_kwargs=cli_kwargs).start()

    # Assert
    assert execution_info["error"] is False
    assert execution_info["reason"] == ""
    assert execution_info["requests_retried"] == 2


if __name__ == "__main__":
    asyncio.run(CrawlerRunner(crawler=RetryCrawler, cli_kwargs={}).start())

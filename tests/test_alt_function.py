import asyncio

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo


class DefaultFunctionsCrawler(Crawler):
    crawler_name = "DefaultFunctionsCrawler"

    async def start_crawler(self) -> None: ...

    async def schedule_requests(self) -> None:
        crawler_request = CrawlerRequest(url="https://test.com")
        await self.crawler_queue.add(crawler_request)

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        return CrawlerResponse(
            url=crawler_request.url,
            text="",
            status_code=200,
        )

    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None: ...


class AlternativeFunctionsCrawler(DefaultFunctionsCrawler):
    crawler_name = "AlternativeFunctionsCrawler"

    async def schedule_requests(self) -> None:
        crawler_request = CrawlerRequest(
            url="https://test.com",
            process_request_function="process_request_alt",
            process_response_function="process_response_alt",
            parse_function="parse_alt",
        )
        await self.crawler_queue.add(crawler_request)

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        raise Exception("Wrong Function called")

    async def process_request_alt(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        return CrawlerResponse(
            url=crawler_request.url,
            text="",
            status_code=200,
        )

    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        raise Exception("Wrong Function called")

    async def process_response_alt(
        self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse
    ) -> None: ...

    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        raise Exception("Wrong Function called")

    async def parse_alt(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...


class FailAltFunctionsCrawler(AlternativeFunctionsCrawler):
    crawler_name = "FailAltFunctionsCrawler"

    async def schedule_requests(self) -> None:
        crawler_request = CrawlerRequest(url="https://test.com")
        await self.crawler_queue.add(crawler_request)


async def test_default_functions_success():
    # Action
    execution_info: ExecutionInfo = await CrawlerRunner(crawler=DefaultFunctionsCrawler).start()

    # Assert
    assert execution_info["error"] is False
    assert execution_info["reason"] == ""


async def test_alternative_functions_success():
    # Action
    execution_info: ExecutionInfo = await CrawlerRunner(crawler=AlternativeFunctionsCrawler).start()

    # Assert
    assert execution_info["error"] is False
    assert execution_info["reason"] == ""


async def test_alternative_functions_exception():
    # Action
    execution_info: ExecutionInfo = await CrawlerRunner(crawler=FailAltFunctionsCrawler).start()

    # Assert
    assert execution_info["error"] is True
    assert execution_info["reason"] == "Wrong Function called"


if __name__ == "__main__":
    asyncio.run(CrawlerRunner(crawler=AlternativeFunctionsCrawler, cli_kwargs={}).start())

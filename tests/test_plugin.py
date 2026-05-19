from tests.test_crawlers.quotes_crawler import QuotesToScrapeCrawler
from turbocrawler import CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
from turbocrawler.engine.plugin import Plugin
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue
from turbocrawler.queues.crawler_queues import FIFOMemoryCrawlerQueue


class FakePlugin(Plugin):
    async def start_crawler(self) -> None:
        print("[Plugin] start_crawler")

    async def schedule_requests(self) -> None:
        print("[Plugin] schedule_requests")

    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | None:
        print("[Plugin] process_request")
        crawler_request.kwargs = {"test": 5}

    async def process_response(
        self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse
    ) -> CrawlerResponse:
        print("[Plugin] process_response")
        return crawler_response

    async def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        print("[Plugin] stop_crawler")


if __name__ == "__main__":
    config = CrawlerRunnerConfig(
        crawler_queue=FIFOMemoryCrawlerQueue,
        crawler_queue_params=None,
        crawled_queue=MemoryCrawledQueue,
        crawled_queue_params=dict(save_crawled_queue=True, load_crawled_queue=False),
        plugins=[TestPlugin],
        qtd_parse=2,
    )
    CrawlerRunner(crawler=QuotesToScrapeCrawler, config=config).run()

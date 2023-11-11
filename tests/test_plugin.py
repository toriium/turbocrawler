from tests.test_crawlers.quotes_crawler import QuotesToScrapeCrawler
from turbocrawler import CrawlerRequest, CrawlerResponse, CrawlerRunner, ExecutionInfo
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
from turbocrawler.engine.plugin import Plugin
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue
from turbocrawler.queues.crawler_queues import FIFOMemoryCrawlerQueue


class TestPlugin(Plugin):

    def start_crawler(self) -> None:
        print("[Plugin] start_crawler")

    def crawler_first_request(self) -> None:
        print("[Plugin] crawler_first_request")

    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | CrawlerRequest | None:
        print("[Plugin] process_request")
        return None

    def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> CrawlerResponse:
        print("[Plugin] process_response")
        return crawler_response

    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        print("[Plugin] process_request")


if __name__ == '__main__':
    config = CrawlerRunnerConfig(crawler_queue=FIFOMemoryCrawlerQueue,
                                 crawler_queue_params=None,
                                 crawled_queue=MemoryCrawledQueue,
                                 crawled_queue_params=dict(save_crawled_queue=True, load_crawled_queue=False),
                                 plugins=[TestPlugin], qtd_parse=2)
    CrawlerRunner(crawler=QuotesToScrapeCrawler, config=config).run()

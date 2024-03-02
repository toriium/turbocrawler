from dataclasses import dataclass

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.plugin import Plugin
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue
from turbocrawler.queues.crawler_queues import FIFOMemoryCrawlerQueue


@dataclass
class CrawlerRunnerConfig:
    crawler_queue: type[CrawlerQueueABC] = FIFOMemoryCrawlerQueue
    crawler_queue_params: dict | None = None
    crawled_queue: type[CrawledQueueABC] = MemoryCrawledQueue
    crawled_queue_params: dict | None = None

    plugins: list[type[Plugin]] | None = ()
    qtd_parse: int | None = 2

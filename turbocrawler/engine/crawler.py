from abc import ABC, abstractmethod
from typing import Any

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse, ExtractRule
from turbocrawler.engine.data_types.info import ExecutionInfo
from turbocrawler.engine.plugin import Plugin
from turbocrawler.logger import LOG


class Crawler(ABC):
    crawler_name: str
    allowed_domains: list[str]
    regex_extract_rules: list[ExtractRule] = []
    time_between_requests: int | float = 0

    crawler_queue: CrawlerQueueABC
    plugins: list[Plugin]
    logger: LOG

    def __init__(self, crawler_queue: CrawlerQueueABC, plugins: list[Plugin], logger: LOG):
        self.crawler_queue = crawler_queue
        self.plugins = plugins
        self.logger = logger

    @abstractmethod
    def start_crawler(self) -> None:
        ...

    @abstractmethod
    def crawler_first_request(self) -> CrawlerResponse | None:
        ...

    @abstractmethod
    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | None:
        ...

    def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        return None

    @abstractmethod
    def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> Any:
        ...

    @abstractmethod
    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        ...

    def get_plugin(self, plugin_name) -> Plugin | None:
        target_plugin = [plugin for plugin in self.plugins if plugin.__class__.__name__ == plugin_name]
        if not target_plugin:
            return None

        return target_plugin[0]

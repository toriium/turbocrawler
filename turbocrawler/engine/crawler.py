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

    @classmethod
    @abstractmethod
    def start_crawler(cls) -> None:
        ...

    @classmethod
    @abstractmethod
    def crawler_first_request(cls) -> CrawlerResponse | None:
        ...

    @classmethod
    @abstractmethod
    def process_request(cls, crawler_request: CrawlerRequest) -> CrawlerResponse | None:
        ...

    @classmethod
    def process_response(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        return None

    @classmethod
    @abstractmethod
    def parse(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> Any:
        ...

    @classmethod
    @abstractmethod
    def stop_crawler(cls, execution_info: ExecutionInfo) -> None:
        ...

    @classmethod
    def get_plugin(cls, plugin_name) -> Plugin | None:
        target_plugin = [plugin for plugin in cls.plugins if plugin.__class__.__name__ == plugin_name]
        if not target_plugin:
            return None

        return target_plugin[0]

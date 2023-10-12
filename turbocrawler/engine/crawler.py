from abc import ABC, abstractmethod
from typing import Any

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.models import CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule


class Crawler(ABC):
    crawler_name: str
    allowed_domains: list[str]
    regex_extract_rules: list[ExtractRule] = []
    time_between_requests: int | float = 0

    crawler_queue: CrawlerQueueABC

    def __init__(self) -> None:
        ...

    @abstractmethod
    def start_crawler(self) -> None:
        ...

    @abstractmethod
    def crawler_first_request(self) -> CrawlerResponse:
        ...

    @abstractmethod
    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        ...

    @abstractmethod
    def parse_crawler_response(self, crawler_response: CrawlerResponse) -> Any:
        ...

    @abstractmethod
    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        ...

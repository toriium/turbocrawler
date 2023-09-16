from abc import ABC, abstractmethod
from typing import Any

from crawler_manager.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from crawler_manager.engine.models import CrawlerRequest, CrawlerResponse


class Crawler(ABC):
    crawler_name: str
    allowed_domains: list[str]
    regex_rules: list[str]
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

    # @abstractmethod
    # def before_request(self):
    #     ...

    @abstractmethod
    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        ...

    # @abstractmethod
    # def after_request(self):
    #     ...

    @abstractmethod
    def parse_crawler_response(self, crawler_response: CrawlerResponse) -> Any:
        ...

    @abstractmethod
    def stop_crawler(self) -> None:
        ...

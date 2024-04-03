from abc import ABC, abstractmethod
from logging import Handler

from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse
from turbocrawler.engine.data_types.info import ExecutionInfo


class Plugin(ABC):
    def __init__(self, crawler):
        self.crawler = crawler

    @abstractmethod
    def start_crawler(self) -> None:
        ...

    @abstractmethod
    def crawler_first_request(self) -> None:
        ...

    @abstractmethod
    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | None:
        ...

    @abstractmethod
    def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        return None

    @abstractmethod
    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        ...

    def log_handler(self, crawler, running_id: str) -> Handler | None:
        return None

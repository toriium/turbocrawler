from abc import ABC, abstractmethod

from turbocrawler import Crawler
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse
from turbocrawler.engine.data_types.info import ExecutionInfo


class Plugin(ABC):
    def __init__(self, crawler: type[Crawler]):
        self.crawler = crawler

    @abstractmethod
    def start_crawler(self) -> None:
        ...

    @abstractmethod
    def crawler_first_request(self) -> None:
        ...

    @abstractmethod
    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | CrawlerRequest | None:
        ...

    @abstractmethod
    def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> CrawlerResponse:
        return crawler_response

    @abstractmethod
    def stop_crawler(self, execution_info: ExecutionInfo) -> None:
        ...

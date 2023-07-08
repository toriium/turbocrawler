from abc import ABC, abstractmethod
from typing import Any
from engine.crawler_response import CrawlerResponse

from engine.crawler_request import CrawlerRequest


class Crawler(ABC):
    crawler_name: str
    allowed_domains: list[str]
    regex_rules: list[str]

    @abstractmethod
    def start_crawler(self) -> CrawlerResponse:
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

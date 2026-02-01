from abc import ABC, abstractmethod
from logging import Handler

from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse
from turbocrawler.engine.data_types.info import ExecutionInfo


class Plugin(ABC):
    def __init__(self, crawler):
        self.crawler = crawler

    @abstractmethod
    async def start_crawler(self) -> None: ...

    @abstractmethod
    async def crawler_first_request(self) -> None: ...

    @abstractmethod
    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | None: ...

    @abstractmethod
    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        return None

    @abstractmethod
    async def stop_crawler(self, execution_info: ExecutionInfo) -> None: ...

    def log_handler(self, crawler, running_id: str) -> Handler | None:
        return None

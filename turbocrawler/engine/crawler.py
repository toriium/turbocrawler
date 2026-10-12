import logging
from abc import ABC, abstractmethod
from numbers import Number
from typing import Any

from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.data_types.crawler import CrawlerRequest, CrawlerResponse, ExtractRule, LoggedData
from turbocrawler.engine.data_types.info import ExecutionInfo


class Crawler(ABC):
    crawler_name: str
    allowed_domains: list[str]
    regex_extract_rules: list[ExtractRule] = []
    time_between_requests: Number | tuple[Number] = 0

    run_id: str
    crawler_queue: CrawlerQueueABC
    logger: logging.Logger
    cli_kwargs: dict[str, Any]

    logged_data: LoggedData

    def __init__(
        self,
        run_id: str,
        crawler_queue: CrawlerQueueABC,
        logger: logging.Logger,
        cli_kwargs: dict[str, Any],
    ):
        self.run_id = run_id
        self.crawler_queue = crawler_queue
        self.logger = logger
        self.cli_kwargs = cli_kwargs
        if isinstance(self.time_between_requests, tuple):
            assert len(self.time_between_requests) == 2, "time_between_requests tuple must have exactly two elements"
            self.time_between_requests = (self.time_between_requests[0], self.time_between_requests[1])
        else:
            self.time_between_requests = (self.time_between_requests, self.time_between_requests)

    @abstractmethod
    async def start_crawler(self) -> None: ...

    async def login(self) -> LoggedData:
        return LoggedData()

    @abstractmethod
    async def schedule_requests(self) -> None: ...

    @abstractmethod
    async def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse | None: ...

    async def process_response(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        return None

    @abstractmethod
    async def parse(self, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> Any: ...

    async def save_all(self) -> None:
        """
        Triggers: after crawler_queue_loop finishes and before stop_crawler()
        Here you can implemented a logic to save all collected data at once
        for example, saving all collected data in a database in one transaction.
        """
        return None

    @abstractmethod
    async def stop_crawler(self, execution_info: ExecutionInfo) -> None: ...

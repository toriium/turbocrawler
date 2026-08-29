from abc import ABC, abstractmethod

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.data_types.crawler import CrawlerRequest
from turbocrawler.engine.data_types.info import CrawlerQueueInfo, ExecutionInfo
from turbocrawler.logger import logger
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue


class CrawlerQueueABC(ABC):
    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        self.crawler_name = crawler_name
        if crawled_queue is None:
            crawled_queue = MemoryCrawledQueue(crawler_name=self.crawler_name)
        self.crawled_queue = crawled_queue
        self.__urls_scheduled: list[str] = []  # Prevents scheduling the same URL again before it's crawled
        self.__info = CrawlerQueueInfo(add=0, get=0, length=0)

    @abstractmethod
    def __len__(self):
        pass

    async def get_info(self) -> CrawlerQueueInfo:
        """Returns the current state of the queue"""
        return CrawlerQueueInfo(add=self.__info["add"], get=self.__info["get"], length=len(self))

    async def get(self) -> CrawlerRequest | None:
        """
        Retrieves a crawler request from the queue.
        Removes the URL from the scheduled list and adds it to the crawled queue.

        Returns:
            CrawlerRequest | None: The crawler request or None if the queue is empty.
        """
        if await self._is_queue_empty():
            return None

        crawler_request = await self._get_and_remove_request_from_queue()
        if crawler_request is None:
            return None
        self.__urls_scheduled.remove(crawler_request.url)

        await self.__add_url_to_crawled_queue(url=crawler_request.url)
        self.__info["get"] += 1
        return crawler_request

    async def add(self, crawler_request: CrawlerRequest, verify_crawled: bool = True) -> None:
        """
        Add a crawler request to the queue.
        Validates if it was crawled or is already scheduled before adding to the queue.
        Updates queue info.

        Parameters:
            crawler_request (CrawlerRequest): The crawler request to add.
            verify_crawled (bool): Bypass the crawled and scheduled checks.

        Returns:
            None
        """
        url = crawler_request.url

        if not verify_crawled:
            self.__info["add"] += 1
            await self._insert_queue(crawler_request)
            self.__urls_scheduled.append(url)
            return

        if await self._is_url_in_queue(url=url):
            logger.debug(f"[{self.__class__.__name__}] {url} is on the __crawler_queue")
            return

        if not await self.__page_already_crawled(url=url):
            self.__info["add"] += 1
            await self._insert_queue(crawler_request)
            self.__urls_scheduled.append(url)
        else:
            logger.debug(f"[{self.__class__.__name__}] {url} already_crawled")

    def urls_scheduled(self) -> list[str]:
        return self.__urls_scheduled

    @abstractmethod
    async def _insert_queue(self, crawler_request: CrawlerRequest) -> None:
        pass

    @abstractmethod
    async def _get_and_remove_request_from_queue(self) -> CrawlerRequest | None:
        """Pop a CrawlerRequest from the queue. Returns None if the queue is empty."""
        pass

    async def _is_url_in_queue(self, url) -> bool:
        """Checks if the URL is already in the queue to be crawled"""
        return url in self.__urls_scheduled

    @abstractmethod
    async def _is_queue_empty(self) -> bool:
        """Checks if the queue is empty"""
        pass

    async def __page_already_crawled(self, url: str) -> bool:
        """Checks if the URL is already crawled in the crawled queue"""
        return await self.crawled_queue.is_url_in_crawled_queue(url=url)

    async def __add_url_to_crawled_queue(self, url: str) -> None:
        """Adds the URL to the crawled queue"""
        await self.crawled_queue.add(url=url)

    async def stop_crawler(self, execution_info: ExecutionInfo):
        """
        Triggers when the stop crawler process is executed

        Parameters:
            execution_info (ExecutionInfo): The execution info of the crawler
        Returns:
            None
        """
        pass

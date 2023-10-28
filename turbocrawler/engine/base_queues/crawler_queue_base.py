from abc import ABC, abstractmethod

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.data_types.crawler import CrawlerRequest
from turbocrawler.engine.data_types.info import CrawlerQueueInfo
from turbocrawler.logger import logger
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue


class CrawlerQueueABC(ABC):

    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        self.crawler_name = crawler_name
        if crawled_queue is None:
            crawled_queue = MemoryCrawledQueue(crawler_name=self.crawler_name)
        self.crawled_queue = crawled_queue
        self.__urls_scheduled = set()
        self.__info = CrawlerQueueInfo(add=0, get=0, length=0)

    @abstractmethod
    def __len__(self):
        pass

    def get_info(self) -> CrawlerQueueInfo:
        return CrawlerQueueInfo(add=self.__info['add'], get=self.__info['get'], length=len(self))

    def get(self) -> CrawlerRequest | None:
        if self._is_queue_empty():
            return None

        crawler_request = self._get_and_remove_request_from_queue()
        if crawler_request is None:
            return None
        self.__urls_scheduled.remove(crawler_request.url)

        self.__add_url_to_crawled_queue(url=crawler_request.url)
        self.__info['get'] += 1
        return crawler_request

    def add(self, crawler_request: CrawlerRequest, verify_crawled: bool = True) -> None:
        if not verify_crawled:
            self.__info['add'] += 1
            self._insert_queue(crawler_request)
            return

        url = crawler_request.url
        if self._is_url_in_queue(url=url):
            logger.debug(f'[{self.__class__.__name__}] {url} is on the __crawler_queue')
            return

        if not self.__page_already_crawled(url=url):
            self.__info['add'] += 1
            self._insert_queue(crawler_request)
            self.__urls_scheduled.add(url)
        else:
            logger.debug(f'[{self.__class__.__name__}] {url} already_crawled')

    @abstractmethod
    def _insert_queue(self, crawler_request: CrawlerRequest) -> None:
        pass

    @abstractmethod
    def _get_and_remove_request_from_queue(self) -> CrawlerRequest | None:
        pass

    def _is_url_in_queue(self, url) -> bool:
        return url in self.__urls_scheduled

    @abstractmethod
    def _is_queue_empty(self) -> bool:
        pass

    def __page_already_crawled(self, url: str) -> bool:
        return self.crawled_queue.is_url_in_crawled_queue(url=url)

    def __add_url_to_crawled_queue(self, url: str) -> None:
        self.crawled_queue.add(url=url)

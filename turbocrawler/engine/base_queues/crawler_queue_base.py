from abc import ABC, abstractmethod

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.models import CrawlerRequest
from turbocrawler.logger import logger
from turbocrawler.queues.crawled_queue import MemoryCrawledQueue


class CrawlerQueueABC(ABC):

    def __init__(self, crawled_queue: CrawledQueueABC = None, save_crawled_queue: bool = False):
        self.save_crawled_queue = save_crawled_queue
        if not crawled_queue:
            crawled_queue = MemoryCrawledQueue()
        self.crawled_queue = crawled_queue
        self.__crawled_queue_control = set()

    def get_request_from_queue(self) -> CrawlerRequest | None:
        if self._is_queue_empty():
            if not self.save_crawled_queue:
                self.crawled_queue.delete_crawled_queue()
            return None

        crawler_request = self._get_and_remove_request_from_queue()
        self.__crawled_queue_control.remove(crawler_request.site_url)

        self.__add_url_to_crawled_queue(url=crawler_request.site_url)
        return crawler_request

    def add_request_to_queue(self, crawler_request: CrawlerRequest, verify_crawled: bool = True) -> None:
        if not verify_crawled:
            self._insert_queue(crawler_request)

        url = crawler_request.site_url
        if self._is_url_in_queue(url=url):
            logger.debug(f'URL: {url} is on the __crawler_queue')
            return

        if not self.__page_already_crawled(url=url):
            self._insert_queue(crawler_request)
            self.__crawled_queue_control.add(url)
        else:
            logger.debug(f'URL: {url} already_crawled')

    @abstractmethod
    def _insert_queue(self, crawler_request: CrawlerRequest):
        pass

    @abstractmethod
    def _get_and_remove_request_from_queue(self) -> CrawlerRequest:
        pass

    def _is_url_in_queue(self, url) -> bool:
        return url in self.__crawled_queue_control

    @abstractmethod
    def _is_queue_empty(self) -> bool:
        pass

    def __page_already_crawled(self, url: str) -> bool:
        return self.crawled_queue.is_on_crawled_queue(url=url)

    def __add_url_to_crawled_queue(self, url: str) -> None:
        self.crawled_queue.add_url_to_crawled_queue(url=url)

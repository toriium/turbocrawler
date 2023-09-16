from crawler_manager.engine.models import CrawlerRequest
from abc import ABC, abstractmethod


class CrawledQueueABC(ABC):
    @abstractmethod
    def add_to_crawled_queue(self, url: str) -> None:
        pass

    @abstractmethod
    def is_on_crawled_queue(self, url: str) -> bool:
        pass

    @abstractmethod
    def delete_crawled_queue(self) -> None:
        pass


class CrawlerQueueABC(ABC):

    def __init__(self, crawled_queue: CrawledQueueABC, save_crawled_queue: bool = False):
        self.save_crawled_queue = save_crawled_queue
        self.crawled_queue = crawled_queue

    def get_request_from_queue(self) -> CrawlerRequest | None:
        if self._is_queue_empty():
            if not self.save_crawled_queue:
                self.crawled_queue.delete_crawled_queue()
            return None
        else:
            crawler_request = self._get_and_remove_request_from_queue()

        self.__add_to_crawled_queue(url=crawler_request.site_url)
        return crawler_request

    def add_request_to_queue(self, crawler_request: CrawlerRequest) -> None:
        url = crawler_request.site_url
        if self._is_url_in_queue(url=url):
            print(f'URL: {url} is on the __crawler_queue')
            return

        if not self.__page_already_crawled(url=url):
            self._insert_queue(crawler_request)
        else:
            print(f'URL: {url} already_crawled')

    @abstractmethod
    def _insert_queue(self, crawler_request: CrawlerRequest):
        pass

    @abstractmethod
    def _get_and_remove_request_from_queue(self) -> CrawlerRequest:
        pass

    @abstractmethod
    def _is_url_in_queue(self, url) -> bool:
        pass

    @abstractmethod
    def _is_queue_empty(self) -> bool:
        pass

    def __page_already_crawled(self, url: str) -> bool:
        return self.crawled_queue.is_on_crawled_queue(url=url)

    def __add_to_crawled_queue(self, url: str) -> None:
        self.crawled_queue.add_to_crawled_queue(url=url)

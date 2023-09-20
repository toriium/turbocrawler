from abc import ABC, abstractmethod


class CrawledQueueABC(ABC):
    @abstractmethod
    def add_url_to_crawled_queue(self, url: str) -> None:
        pass

    @abstractmethod
    def is_on_crawled_queue(self, url: str) -> bool:
        pass

    @abstractmethod
    def delete_crawled_queue(self) -> None:
        pass

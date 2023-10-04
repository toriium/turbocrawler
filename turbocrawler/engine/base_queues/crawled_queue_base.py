from abc import ABC, abstractmethod
from turbocrawler.logger import logger


class CrawledQueueABC(ABC):

    def __init__(
            self,
            crawler_name: str,
            must_save_crawled_queue: bool = False,
            must_load_crawled_queue: bool = False):
        self.crawler_name = crawler_name
        self.must_save_crawled_queue = must_save_crawled_queue
        self.must_load_crawled_queue = must_load_crawled_queue

    def start_crawler(self):
        if self.must_load_crawled_queue:
            logger.info('Calling load_crawled_queue')
            self.load_crawled_queue()

    @abstractmethod
    def add_url_to_crawled_queue(self, url: str) -> None:
        pass

    @abstractmethod
    def is_on_crawled_queue(self, url: str) -> bool:
        pass

    @abstractmethod
    def load_crawled_queue(self) -> None:
        pass

    @abstractmethod
    def delete_crawled_queue(self) -> None:
        pass

    @abstractmethod
    def save_crawled_queue(self) -> None:
        pass

    def stop_crawler(self):
        if self.must_save_crawled_queue:
            logger.info('Calling save_crawled_queue')
            self.save_crawled_queue()
        else:
            logger.info('Calling delete_crawled_queue')
            self.delete_crawled_queue()

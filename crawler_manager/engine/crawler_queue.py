import os

from crawler_manager.engine.models import CrawlerRequest
from abc import ABC, abstractmethod


class CrawledQueue:
    def __init__(self, crawler_name: str):
        self.crawler_name = crawler_name

        self.__file_name = f"{self.crawler_name}_crawled_queue.txt"
        self.__queue_dir_name = 'crawlers_queue'
        self.__queue_dir_path = f'{os.getcwd()}/{self.__queue_dir_name}'
        self.__crawler_queue_file_path = f'{self.__queue_dir_path}/{self.__file_name}'

        self.__create_file_path()

    def __create_file_path(self):
        os.makedirs(self.__queue_dir_path, exist_ok=True)
        if not os.path.exists(self.__crawler_queue_file_path):
            with open(self.__crawler_queue_file_path, 'w'):
                ...

    def add_to_crawled_queue(self, url: str) -> None:
        self.__append_queue(url=url)

    def is_on_crawled_queue(self, url: str) -> bool:
        with open(self.__crawler_queue_file_path, 'r') as file:
            for _line, line_value in enumerate(file):
                if url == line_value.strip():
                    return True
            else:
                return False

    def delete_crawled_queue(self):
        if os.path.exists(self.__crawler_queue_file_path):
            os.remove(self.__crawler_queue_file_path)

    def __append_queue(self, url):
        with open(self.__crawler_queue_file_path, 'a') as file:
            file.write(f"\n{url}")


class CrawlerQueueABC(ABC):

    def __init__(self, crawled_queue: CrawledQueue, save_crawled_queue: bool = False):
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

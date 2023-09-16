import os
from collections import deque

from crawler_manager.engine.crawler import Crawler
from crawler_manager.engine.crawler_queue import CrawlerQueueABC, CrawledQueueABC
from crawler_manager.engine.models import CrawlerRequest


class TextCrawledQueue(CrawledQueueABC):
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
        with open(self.__crawler_queue_file_path, 'a') as file:
            file.write(f"\n{url}")

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


class FIFOMemoryQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawler: type[Crawler], crawled_queue: CrawledQueueABC, save_crawled_queue: bool = False):
        super().__init__(crawled_queue=crawled_queue, save_crawled_queue=save_crawled_queue)
        self.__crawler_queue = deque()

    def _insert_queue(self, crawler_request: CrawlerRequest):
        self.__crawler_queue.append(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest:
        return self.__crawler_queue.popleft()

    def _is_url_in_queue(self, url) -> bool:
        request = CrawlerRequest(site_url=url)
        return request in self.__crawler_queue

    def _is_queue_empty(self) -> bool:
        return False if bool(self.__crawler_queue) else True

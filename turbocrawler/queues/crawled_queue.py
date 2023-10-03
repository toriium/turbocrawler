import os

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.utils import create_file_path


class TextCrawledQueue(CrawledQueueABC):

    def __init__(
            self,
            crawler_name: str,
            save_crawled_queue: bool = False,
            load_crawled_queue: bool = False):
        super().__init__(crawler_name=crawler_name,
                         save_crawled_queue=save_crawled_queue,
                         load_crawled_queue=load_crawled_queue)

        self.__file_name = f"{self.crawler_name}_crawled_queue.txt"
        self.__queue_dir_name = 'crawlers_queue'
        self.__queue_dir_path = f'{os.getcwd()}/{self.__queue_dir_name}'
        self.__crawler_queue_file_path = f'{self.__queue_dir_path}/{self.__file_name}'

        create_file_path(self.__crawler_queue_file_path)

    def add_url_to_crawled_queue(self, url: str) -> None:
        with open(self.__crawler_queue_file_path, 'a') as file:
            file.write(f"\n{url}")

    def is_on_crawled_queue(self, url: str) -> bool:
        with open(self.__crawler_queue_file_path, 'r') as file:
            for _line, line_value in enumerate(file):
                if url == line_value.strip():
                    return True

        return False

    def load_crawled_queue(self) -> None:
        pass

    def delete_crawled_queue(self):
        if os.path.exists(self.__crawler_queue_file_path):
            os.remove(self.__crawler_queue_file_path)

    def save_crawled_queue(self) -> None:
        pass


class MemoryCrawledQueue(CrawledQueueABC):
    def __init__(
            self,
            crawler_name: str,
            save_crawled_queue: bool = False,
            load_crawled_queue: bool = False):
        super().__init__(crawler_name=crawler_name,
                         save_crawled_queue=save_crawled_queue,
                         load_crawled_queue=load_crawled_queue)

        self.crawled_queue = set()

        self.__file_name = f"{self.crawler_name}_crawled_queue.txt"
        self.__queue_dir_name = 'crawlers_queue'
        self.__queue_dir_path = f'{os.getcwd()}/{self.__queue_dir_name}'
        self.__crawler_queue_file_path = f'{self.__queue_dir_path}/{self.__file_name}'

    def add_url_to_crawled_queue(self, url: str) -> None:
        self.crawled_queue.add(url)

    def is_on_crawled_queue(self, url: str) -> bool:
        return url in self.crawled_queue

    def load_crawled_queue(self) -> None:
        with open(self.__crawler_queue_file_path, 'w') as file:
            for line in file:
                self.crawled_queue.add(line)

    def delete_crawled_queue(self) -> None:
        del self.crawled_queue

    def save_crawled_queue(self) -> None:
        create_file_path(self.__crawler_queue_file_path)
        with open(self.__crawler_queue_file_path, 'w') as file:
            [file.writelines(f'{url}\n') for url in self.crawled_queue]

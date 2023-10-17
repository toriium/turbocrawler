import os

from turbocrawler.engine.base_queues.crawled_queue_base import CrawledQueueABC
from turbocrawler.engine.data_types.crawler import ExtractRule
from turbocrawler.utils import create_file_path


class TextCrawledQueue(CrawledQueueABC):

    def __init__(
            self,
            crawler_name: str,
            save_crawled_queue: bool = False,
            load_crawled_queue: bool = False):
        super().__init__(crawler_name=crawler_name,
                         must_save_crawled_queue=save_crawled_queue,
                         must_load_crawled_queue=load_crawled_queue)

        self.__file_name = f"{self.crawler_name}_crawled_queue.txt"
        self.__queue_dir_name = 'crawlers_queue'
        self.__queue_dir_path = f'{os.getcwd()}/{self.__queue_dir_name}'
        self.__crawler_queue_file_path = f'{self.__queue_dir_path}/{self.__file_name}'

        create_file_path(self.__crawler_queue_file_path)

    def __len__(self):
        with open(self.__crawler_queue_file_path, 'r') as file:
            for line_number, _ in enumerate(file, 1):
                pass
        return line_number

    def add_url_to_crawled_queue(self, url: str) -> None:
        with open(self.__crawler_queue_file_path, 'a') as file:
            file.write(f"{url}\n")

    def is_url_in_crawled_queue(self, url: str) -> bool:
        with open(self.__crawler_queue_file_path, 'r') as file:
            for line_value in file:
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

    def remove_urls_with_remove_crawled(self, extract_rules_remove_crawled: list[ExtractRule]) -> None:
        temp_file_path = f"{self.__crawler_queue_file_path}_temp_file"
        with open(self.__crawler_queue_file_path, 'r') as original_file:
            with open(temp_file_path, 'w') as temp_file:
                for line_value in original_file:
                    url = line_value.strip()
                    if not self._match_with_regex(url=url, extract_rules=extract_rules_remove_crawled):
                        temp_file.write(f"{url}\n")

        os.remove(self.__crawler_queue_file_path)
        os.rename(temp_file_path, self.__crawler_queue_file_path)


class MemoryCrawledQueue(CrawledQueueABC):
    def __init__(
            self,
            crawler_name: str,
            save_crawled_queue: bool = False,
            load_crawled_queue: bool = False):
        super().__init__(crawler_name=crawler_name,
                         must_save_crawled_queue=save_crawled_queue,
                         must_load_crawled_queue=load_crawled_queue)

        self.crawled_queue = set()

        self.__file_name = f"{self.crawler_name}_crawled_queue.txt"
        self.__queue_dir_name = 'crawlers_queue'
        self.__queue_dir_path = f'{os.getcwd()}/{self.__queue_dir_name}'
        self.__crawler_queue_file_path = f'{self.__queue_dir_path}/{self.__file_name}'

    def __len__(self):
        return len(self.crawled_queue)

    def add_url_to_crawled_queue(self, url: str) -> None:
        self.crawled_queue.add(url)

    def is_url_in_crawled_queue(self, url: str) -> bool:
        return url in self.crawled_queue

    def load_crawled_queue(self) -> None:
        if not os.path.exists(self.__crawler_queue_file_path):
            raise FileNotFoundError(f'Unable to find path {self.__crawler_queue_file_path}'
                                    f' to execute load_crawled_queue')
        with open(self.__crawler_queue_file_path, 'r') as file:
            for url in file:
                self.crawled_queue.add(url.strip())

    def delete_crawled_queue(self) -> None:
        del self.crawled_queue

    def save_crawled_queue(self) -> None:
        create_file_path(self.__crawler_queue_file_path)
        with open(self.__crawler_queue_file_path, 'w') as file:
            [file.writelines(f'{url}\n') for url in self.crawled_queue]

    def remove_urls_with_remove_crawled(self, extract_rules_remove_crawled: list[ExtractRule]) -> None:
        urls_to_remove = []
        for url in self.crawled_queue:
            if self._match_with_regex(url=url, extract_rules=extract_rules_remove_crawled):
                urls_to_remove.append(url)

        for url in urls_to_remove:
            self.crawled_queue.remove(url)

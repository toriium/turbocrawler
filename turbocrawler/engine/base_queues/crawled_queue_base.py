from abc import ABC, abstractmethod

from turbocrawler.engine.data_types.crawler import ExtractRule
from turbocrawler.engine.data_types.info import CrawledQueueInfo, ExecutionInfo
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
        self.__info = CrawledQueueInfo(add=0, length=0)

    async def get_info(self) -> CrawledQueueInfo:
        return CrawledQueueInfo(add=self.__info['add'], length=len(self))

    async def start_crawler(self):
        if self.must_load_crawled_queue:
            logger.info(f'Calling {self.__class__.__name__}.load_crawled_queue')
            await self.load_crawled_queue()

    @staticmethod
    def _match_with_regex(url: str, extract_rules: list[ExtractRule]):
        for extract_rule in extract_rules:
            regex = extract_rule.regex
            if regex.findall(url):
                return True
        return False

    @abstractmethod
    def __len__(self):
        pass

    async def add(self, url: str) -> None:
        self.__info['add'] += 1
        await self.add_url_to_crawled_queue(url)

    @abstractmethod
    async def add_url_to_crawled_queue(self, url: str) -> None:
        pass

    @abstractmethod
    async def is_url_in_crawled_queue(self, url: str) -> bool:
        pass

    @abstractmethod
    async def load_crawled_queue(self) -> None:
        pass

    @abstractmethod
    async def delete_crawled_queue(self) -> None:
        pass

    @abstractmethod
    async def save_crawled_queue(self) -> None:
        pass

    @abstractmethod
    async def remove_urls_with_remove_crawled(self, extract_rules_remove_crawled: list[ExtractRule]) -> None:
        pass

    async def stop_crawler(self, execution_info: ExecutionInfo):
        if self.must_save_crawled_queue:
            logger.info(f'Calling {self.__class__.__name__}.save_crawled_queue')
            await self.save_crawled_queue()
        else:
            logger.info(f'Calling {self.__class__.__name__}.delete_crawled_queue')
            await self.delete_crawled_queue()
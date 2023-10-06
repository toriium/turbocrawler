from collections import deque

from turbocrawler.engine import CrawledQueueABC, CrawlerQueueABC
from turbocrawler.engine.models import CrawlerRequest


class FIFOMemoryQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        super().__init__(crawler_name=crawler_name, crawled_queue=crawled_queue)
        self.__crawler_queue = deque()

    def __len__(self):
        return len(self.__crawler_queue)

    def _insert_queue(self, crawler_request: CrawlerRequest):
        self.__crawler_queue.append(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest:
        return self.__crawler_queue.popleft()

    def _is_queue_empty(self) -> bool:
        return not bool(self.__crawler_queue)

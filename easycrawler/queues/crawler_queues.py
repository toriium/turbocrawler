from collections import deque

from easycrawler.engine import CrawledQueueABC, CrawlerQueueABC
from easycrawler.engine.models import CrawlerRequest


class FIFOMemoryQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawled_queue: CrawledQueueABC = None, save_crawled_queue: bool = False):
        super().__init__(crawled_queue=crawled_queue, save_crawled_queue=save_crawled_queue)
        self.__crawler_queue = deque()

    def _insert_queue(self, crawler_request: CrawlerRequest):
        self.__crawler_queue.append(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest:
        return self.__crawler_queue.popleft()

    def _is_queue_empty(self) -> bool:
        return not bool(self.__crawler_queue)

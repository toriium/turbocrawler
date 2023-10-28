from collections import deque
from queue import Empty, Queue

from turbocrawler.engine import CrawledQueueABC, CrawlerQueueABC
from turbocrawler.engine.data_types.crawler import CrawlerRequest


class FIFOMemoryCrawlerQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        super().__init__(crawler_name=crawler_name, crawled_queue=crawled_queue)
        self.__crawler_queue = deque()

    def __len__(self):
        return len(self.__crawler_queue)

    def _insert_queue(self, crawler_request: CrawlerRequest) -> None:
        self.__crawler_queue.append(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest | None:
        return self.__crawler_queue.popleft()

    def _is_queue_empty(self) -> bool:
        return not bool(self.__crawler_queue)


class LIFOMemoryCrawlerQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        super().__init__(crawler_name=crawler_name, crawled_queue=crawled_queue)
        self.__crawler_queue = deque()

    def __len__(self):
        return len(self.__crawler_queue)

    def _insert_queue(self, crawler_request: CrawlerRequest) -> None:
        self.__crawler_queue.append(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest | None:
        return self.__crawler_queue.pop()

    def _is_queue_empty(self) -> bool:
        return not bool(self.__crawler_queue)


class ThreadQueue(CrawlerQueueABC):
    """The queue is a FIFO"""

    def __init__(self, crawler_name: str, crawled_queue: CrawledQueueABC = None):
        super().__init__(crawler_name=crawler_name, crawled_queue=crawled_queue)
        self.__crawler_queue = Queue()

    def __len__(self):
        return self.__crawler_queue.qsize()

    def _insert_queue(self, crawler_request: CrawlerRequest) -> None:
        self.__crawler_queue.put(crawler_request)

    def _get_and_remove_request_from_queue(self) -> CrawlerRequest | None:
        try:
            return self.__crawler_queue.get(block=False)
        except Empty:
            return None

    def _is_queue_empty(self) -> bool:
        return not bool(self.__crawler_queue)

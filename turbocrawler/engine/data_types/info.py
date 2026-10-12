from typing import TypedDict


class CrawlerQueueInfo(TypedDict):
    add: int
    get: int
    length: int


class CrawledQueueInfo(TypedDict):
    add: int
    length: int


class RunningInfo(TypedDict):
    crawler_name: str
    crawler_queue: CrawlerQueueInfo
    crawled_queue: CrawledQueueInfo
    requests_made: int
    requests_retried: int
    requests_skipped: int
    running_time: str
    run_id: str


class ExecutionInfo(RunningInfo):
    exception: Exception | None
    forced_stop: bool
    error: bool
    reason: str

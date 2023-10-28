from typing import TypedDict


class WorkerQueueInfo(TypedDict):
    add: int
    get: int
    length: int


class WorkersStateInfo(TypedDict):
    WAITING: int
    EXECUTING: int
    STOPPED: int


class WorkerQueueManagerInfo(TypedDict):
    queue_name: str
    queue_info: WorkerQueueInfo
    workers_state: WorkersStateInfo


class CrawlerQueueInfo(TypedDict):
    add: int
    get: int
    length: int


class CrawledQueueInfo(TypedDict):
    add: int
    length: int


class RunningInfo(TypedDict):
    crawler_queue: CrawlerQueueInfo
    crawled_queue: CrawledQueueInfo
    requests_made: int
    requests_remade: int
    requests_skipped: int
    parse_queue: WorkerQueueManagerInfo | None
    running_time: str
    running_id: str


class ExecutionInfo(RunningInfo):
    forced_stop: bool
    reason: str

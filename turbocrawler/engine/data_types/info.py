from datetime import timedelta
from typing import TypedDict


class WorkerQueueInfo(TypedDict):
    put: int
    get: int
    len: int


class WorkerQueueManagerInfo(TypedDict):
    queue_name: str
    queue_info: WorkerQueueInfo
    workers_state: dict


class RunningInfo(TypedDict):
    crawler_queue: int
    crawled_queue: int
    scheduled_requests: int
    requests_made: int
    requests_remade: int
    requests_skipped: int
    parse_queue: WorkerQueueManagerInfo | None
    running_time: timedelta
    running_id: str


class ExecutionInfo(RunningInfo):
    forced_stop: bool
    reason: str

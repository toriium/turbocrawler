from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CrawlerQueueInfo:
    add: int
    get: int
    length: int


@dataclass
class CrawledQueueInfo:
    add: int
    length: int


@dataclass
class RunningInfo:
    crawler_name: str
    crawler_queue: CrawlerQueueInfo
    crawled_queue: CrawledQueueInfo
    requests_made: int
    requests_retried: int
    requests_skipped: int
    running_time: timedelta
    start_time: datetime
    run_id: str


@dataclass
class ExecutionInfo(RunningInfo):
    exception: Exception | None
    forced_stop: bool
    error: bool
    reason: str
    end_time: datetime

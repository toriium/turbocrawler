from dataclasses import dataclass

from turbocrawler.engine.job import JobExecutionResult, JobInfo


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
    job_info: JobInfo
    crawler_name: str
    crawler_queue: CrawlerQueueInfo
    crawled_queue: CrawledQueueInfo
    requests_made: int
    requests_retried: int
    requests_skipped: int


@dataclass(kw_only=True)
class ExecutionInfo(JobExecutionResult):
    crawler_name: str
    crawler_queue: CrawlerQueueInfo
    crawled_queue: CrawledQueueInfo
    requests_made: int
    requests_retried: int
    requests_skipped: int
    forced_stop: bool

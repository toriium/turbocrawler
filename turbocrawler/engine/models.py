import re
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


@dataclass(slots=True)
class CrawlerRequest:
    site_url: str
    headers: dict = None
    cookies: list[dict] = None
    proxy: str | None = None


@dataclass(slots=True)
class CrawlerResponse:
    site_url: str
    site_body: str
    status_code: int = 200
    headers: dict = None
    cookies: list[dict] = None
    kwargs: dict = None


@dataclass(slots=True)
class ExtractRule:
    regex: str | re.Pattern
    remove_crawled: bool = False


class RunningInfo(TypedDict):
    crawler_queue: int
    crawled_queue: int
    scheduled_requests: int
    requests_made: int
    requests_remade: int
    requests_skipped: int


class ExecutionInfo(RunningInfo):
    forced_stop: bool
    reason: str
    running_time: datetime

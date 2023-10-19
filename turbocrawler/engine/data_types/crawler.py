import re
from dataclasses import dataclass


@dataclass(slots=True)
class CrawlerRequest:
    url: str
    headers: dict = None
    cookies: dict = None
    kwargs: dict = None


@dataclass(slots=True)
class CrawlerResponse:
    url: str
    body: str
    status_code: int = 200
    headers: dict = None
    cookies: dict = None
    kwargs: dict = None


@dataclass(slots=True)
class ExtractRule:
    regex: str | re.Pattern
    remove_crawled: bool = False

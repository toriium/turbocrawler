import re
from dataclasses import dataclass, field


@dataclass
class Settings:
    automatic_schedule: bool = True
    parse_response: bool = True


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
    settings: Settings = field(default_factory=Settings)


@dataclass(slots=True)
class ExtractRule:
    regex: str | re.Pattern
    remove_crawled: bool = False

import re
from dataclasses import dataclass, field


@dataclass
class Settings:
    automatic_schedule: bool = True
    parse_response: bool = True


@dataclass(slots=True)
class CrawlerRequest:
    url: str
    headers: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)
    kwargs: dict = field(default_factory=dict)


@dataclass(slots=True)
class CrawlerResponse:
    url: str
    body: str
    status_code: int = 200
    headers: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)
    kwargs: dict = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)


@dataclass(slots=True)
class ExtractRule:
    regex: str | re.Pattern
    remove_crawled: bool = False

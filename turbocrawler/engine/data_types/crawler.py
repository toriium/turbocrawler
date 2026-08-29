import json
import re
from dataclasses import dataclass, field


@dataclass
class LoggedData:
    cookies: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    local_storage: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)


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
    process_request_function: str = "process_request"
    process_response_function: str = "process_response"
    parse_function: str = "parse"


@dataclass(slots=True)
class CrawlerResponse:
    url: str
    text: str
    status_code: int = 200
    headers: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)
    kwargs: dict = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)

    def json(self, **kwargs) -> dict | list | None:
        try:
            return json.loads(self.text, **kwargs)
        except json.decoder.JSONDecodeError:
            return None


@dataclass(slots=True)
class ExtractRule:
    regex: str | re.Pattern
    remove_crawled: bool = False

from dataclasses import dataclass


@dataclass
class CrawlerRequest:
    site_url: str

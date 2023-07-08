from dataclasses import dataclass

from selenium.webdriver.chromium.webdriver import ChromiumDriver


@dataclass
class CrawlerResponse:
    site_url: str
    site_body: str
    kwargs: None | dict

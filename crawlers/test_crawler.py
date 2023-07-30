from selenium.webdriver.chromium.webdriver import ChromiumDriver

from engine.crawler import Crawler
from engine.models import CrawlerRequest, CrawlerResponse

from parsers.json_file_maker import JsonFileMaker
from selenium_module.get_driver import get_undetected_chromedriver
from selenium_toolkit import SeleniumToolKit


class WebscraperIOCrawler(Crawler):
    crawler_name = "WebscraperIO"
    allowed_domains = ['webscraper.io']
    regex_rules = [
        '/product',
        '/computers',
        '/computers/tablets',
    ]
    time_between_requests = 1

    def __init__(self):
        self.sk: SeleniumToolKit = None
        self.driver: ChromiumDriver = None

    def start_crawler(self) -> None:
        self.driver = get_undetected_chromedriver()
        self.sk = SeleniumToolKit(driver=self.driver)

    def crawler_first_request(self) -> CrawlerResponse:
        url = 'https://check.torproject.org/'
        self.sk.goto(url=url)
        url = "https://webscraper.io/test-sites/e-commerce/static"
        self.sk.goto(url=url)

        site_url = self.driver.current_url
        site_body = self.driver.page_source
        kwargs = {"agua": 'agua'}
        return CrawlerResponse(site_url=site_url,
                               site_body=site_body,
                               status_code=200,
                               headers={},
                               cookies=self.driver.get_cookies(),
                               kwargs=kwargs)

    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        self.sk.goto(crawler_request.site_url)
        site_url = self.driver.current_url
        site_body = self.driver.page_source
        kwargs = {"agua2": 'agua2'}
        return CrawlerResponse(site_url=site_url,
                               site_body=site_body,
                               kwargs=kwargs)

    def parse_crawler_response(self, crawler_response: CrawlerResponse):
        json_data = {"site_url": crawler_response.site_url, "site_html": crawler_response.site_body}
        JsonFileMaker(crawler_name=self.crawler_name).create(json_data=json_data)

    def stop_crawler(self) -> None:
        if self.sk.webdriver_is_open():
            self.driver.quit()

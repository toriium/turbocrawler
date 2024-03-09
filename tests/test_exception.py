from turbocrawler import CrawlerRunner

import requests

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule


class CrawlerWithException(Crawler):
    crawler_name = "CrawlerWithException"
    allowed_domains = ['quotes.toscrape.com']
    regex_extract_rules = [ExtractRule(r'https://quotes.toscrape.com/page/[0-9]')]
    time_between_requests = 1
    session: requests.Session

    @classmethod
    def start_crawler(cls) -> None:
        raise ValueError("Mock error")

    @classmethod
    def crawler_first_request(cls) -> CrawlerResponse | None:
        return None

    @classmethod
    def process_request(cls, crawler_request: CrawlerRequest) -> CrawlerResponse:
        ...

    @classmethod
    def parse(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None:
        ...

    @classmethod
    def stop_crawler(cls, execution_info: ExecutionInfo) -> None:
        ...


if __name__ == '__main__':
    result = CrawlerRunner(crawler=CrawlerWithException).run()
    print(result)

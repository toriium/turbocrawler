from turbocrawler import CrawlerRunner

import requests

from turbocrawler import Crawler, CrawlerRequest, CrawlerResponse, ExecutionInfo, ExtractRule


class CrawlerWithException(Crawler):
    crawler_name = "CrawlerWithException"
    allowed_domains = ["quotes.toscrape.com"]
    regex_extract_rules = [ExtractRule(r"https://quotes.toscrape.com/page/[0-9]")]
    time_between_requests = 1
    session: requests.Session

    @classmethod
    async def start_crawler(cls) -> None:
        raise ValueError("Mock error")

    @classmethod
    async def schedule_requests(cls) -> None:
        return None

    @classmethod
    async def process_request(cls, crawler_request: CrawlerRequest) -> CrawlerResponse: ...

    @classmethod
    async def parse(cls, crawler_request: CrawlerRequest, crawler_response: CrawlerResponse) -> None: ...

    @classmethod
    async def stop_crawler(cls, execution_info: ExecutionInfo) -> None: ...


if __name__ == "__main__":
    result = CrawlerRunner(crawler=CrawlerWithException).run()
    print(result)

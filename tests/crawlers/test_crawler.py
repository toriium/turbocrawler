import requests

from crawler_manager import Crawler, CrawlerRequest, CrawlerResponse


class QuotesToScrapeCrawler(Crawler):
    crawler_name = "QuotesToScrape"
    allowed_domains = ['quotes.toscrape']
    regex_rules = [
        r'https://quotes.toscrape.com/page/[0-9]',
    ]
    time_between_requests = 1
    session = requests.Session

    def start_crawler(self) -> None:
        self.session = requests.session()

    def crawler_first_request(self) -> CrawlerResponse:
        url = "https://quotes.toscrape.com/page/1/"
        response = self.session.get(url=url)

        site_url = response.url
        status_code = response.status_code
        site_body = response.text

        kwargs = {"agua": 'agua'}
        return CrawlerResponse(site_url=site_url,
                               site_body=site_body,
                               status_code=status_code,
                               headers={},
                               cookies=[],
                               kwargs=kwargs)

    def process_request(self, crawler_request: CrawlerRequest) -> CrawlerResponse:
        response = self.session.get(crawler_request.site_url)
        site_url = response.url
        site_body = response.text
        kwargs = {"agua2": 'agua2'}
        return CrawlerResponse(site_url=site_url,
                               site_body=site_body,
                               kwargs=kwargs)

    def parse_crawler_response(self, crawler_response: CrawlerResponse):
        ...
        # json_data = {"site_url": crawler_response.site_url, "site_html": crawler_response.site_body}
        # JsonFileMaker(crawler_name=self.crawler_name).create(json_data=json_data)

    def stop_crawler(self) -> None:
        self.session.close()

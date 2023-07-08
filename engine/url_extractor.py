import re
from parsel import Selector


class UrlExtractor:
    @classmethod
    def get_urls(cls, html_body: str, regex_rules: list[str], site_domain: str, internet_protocol: str = None):
        urls_from_html = cls.extract_urls_from_html(html_body=html_body, regex_rules=regex_rules)
        return cls.transform_urls(urls=urls_from_html, site_domain=site_domain, internet_protocol=internet_protocol)

    @staticmethod
    def validate_url_domain():
        ...

    @staticmethod
    def transform_urls(urls: list[str], site_domain: str, internet_protocol: str = 'https') -> list[str]:
        transformed_urls = []
        for url in urls:
            if site_domain in url:
                transformed_urls.append(url)
            if url.startswith('/'):
                transformed_url = f'{internet_protocol}://{site_domain}{url}'
                transformed_urls.append(transformed_url)
        return transformed_urls

    @staticmethod
    def extract_urls_from_html(html_body: str, regex_rules: list[str]) -> list[str] | None:
        matched_urls = []
        selector = Selector(html_body)
        hrefs_in_html = selector.css(query='a[href]::attr(href)').getall()
        if not hrefs_in_html:
            return None

        for regex in regex_rules:
            re_rule = re.compile(regex)
            for href in hrefs_in_html:
                href_match = re_rule.findall(href)
                if href_match:
                    matched_urls.append(href)

        return matched_urls

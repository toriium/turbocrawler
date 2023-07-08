import re
from parsel import Selector


class UrlExtractor:
    @classmethod
    def get_urls(cls, site_current_url: str, html_body: str, regex_rules: list[str], allowed_domains: list[str]):
        hrefs_in_html = cls.extract_hrefs_from_html(html_body=html_body)
        urls = cls.transform_hrefs(site_current_url=site_current_url, hrefs=hrefs_in_html)
        urls = cls.validate_urls_with_allowed_domains(urls=urls, allowed_domains=allowed_domains)
        urls = cls.validate_urls_with_regex(urls=urls, regex_rules=regex_rules)
        return urls

    @staticmethod
    def validate_urls_with_regex(urls: list[str], regex_rules: list[str]):
        matched_urls = []
        for regex in regex_rules:
            re_rule = re.compile(regex)
            for url in urls:
                href_match = re_rule.findall(url)
                if href_match:
                    matched_urls.append(url)
        return matched_urls

    @staticmethod
    def validate_urls_with_allowed_domains(urls: list[str], allowed_domains: list[str]):
        valid_urls = []
        for url in urls:
            for domain in allowed_domains:
                if domain in url:
                    valid_urls.append(url)
        return valid_urls

    @staticmethod
    def transform_hrefs(site_current_url: str, hrefs: list[str]) -> list[str]:
        transformed_urls = []
        for href in hrefs:
            if href.startswith(("https://", "http://")):
                transformed_urls.append(href)
            if href.startswith('/'):
                transformed_url = f'{site_current_url}{href}'
                transformed_urls.append(transformed_url)
        return transformed_urls

    @staticmethod
    def extract_hrefs_from_html(html_body: str) -> list[str] | None:
        selector = Selector(html_body)
        hrefs_in_html = selector.css(query='a[href]::attr(href)').getall()
        return hrefs_in_html

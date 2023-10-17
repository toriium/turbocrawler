from urllib.parse import urljoin, urlparse

from parsel import Selector

from turbocrawler.engine.data_types.crawler import ExtractRule


class UrlExtractor:
    @classmethod
    def get_urls(cls, site_current_url: str, html_body: str, allowed_domains: list[str],
                 extract_rules: list[ExtractRule] = None):
        site_current_domain = cls.get_url_domain(site_current_url)

        hrefs_in_html = cls.extract_hrefs_from_html(html_body=html_body)
        urls = cls.transform_hrefs(site_current_domain=site_current_domain, hrefs=hrefs_in_html)
        urls = cls.validate_urls_with_allowed_domains(urls=urls, allowed_domains=allowed_domains)

        if extract_rules:
            urls = cls.validate_urls_with_regex(urls=urls, extract_rules=extract_rules)

        return urls

    @staticmethod
    def validate_urls_with_regex(urls: list[str], extract_rules: list[ExtractRule]):
        matched_urls = []
        for extract_rule in extract_rules:
            re_rule = extract_rule.regex
            for url in urls:
                href_match = re_rule.findall(url)
                if href_match:
                    matched_urls.append(url)
        return matched_urls

    @staticmethod
    def validate_urls_with_allowed_domains(urls: set[str], allowed_domains: list[str]):
        valid_urls = []
        for url in urls:
            for domain in allowed_domains:
                if domain in url:
                    valid_urls.append(url)
        return valid_urls

    @staticmethod
    def transform_hrefs(site_current_domain: str, hrefs: list[str]) -> set[str]:
        transformed_urls = set()
        for href in hrefs:
            if href.startswith(("https://", "http://")):
                transformed_urls.add(href)
            if href.startswith('/'):
                transformed_url = urljoin(site_current_domain, href)
                transformed_urls.add(transformed_url)
        return transformed_urls

    @staticmethod
    def extract_hrefs_from_html(html_body: str) -> list[str] | None:
        selector = Selector(html_body)
        hrefs_in_html = selector.css(query='a[href]::attr(href)').getall()
        return hrefs_in_html

    @staticmethod
    def get_url_domain(url: str) -> str:
        parser = urlparse(url)
        domain = parser.netloc
        scheme = parser.scheme
        return f"{scheme}://{domain}"

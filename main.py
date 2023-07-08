from crawlers.test_crawler import WebscraperIOCrawler
from engine.crawler_runner import CrawlerRunner

crawler = WebscraperIOCrawler()
response = CrawlerRunner(crawler=crawler).run()
print(response)

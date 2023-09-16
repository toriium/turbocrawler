from crawler_manager.engine.crawler_runner import CrawlerRunner
from tests.crawlers.test_crawler import QuotesToScrapeCrawler

crawler = QuotesToScrapeCrawler
response = CrawlerRunner(crawler=crawler).run()
print(response)

from easycrawl.engine.crawler_runner import CrawlerRunner
from tests.crawlers.test_crawler import QuotesToScrapeCrawler

response = CrawlerRunner(crawler=QuotesToScrapeCrawler).run()
print('Success')

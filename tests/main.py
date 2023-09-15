from tests.crawlers.test_crawler import WebscraperIOCrawler
from crawler_manager.engine.crawler_queue import CrawlerQueue
from crawler_manager.engine.crawler_runner import CrawlerRunner

crawler = WebscraperIOCrawler
crawler_queue = CrawlerQueue(crawler=crawler, save_crawled_queue=True)
response = CrawlerRunner(crawler=crawler, crawler_queue=crawler_queue).run()
print(response)

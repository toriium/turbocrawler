
from crawler_manager.engine.crawler_runner import CrawlerRunner
from crawler_manager.queues.default_queue import FIFOMemoryQueue
from tests.crawlers.test_crawler import QuotesToScrapeCrawler

crawler = QuotesToScrapeCrawler
crawler_queue = FIFOMemoryQueue(crawler=crawler, save_crawled_queue=True)
response = CrawlerRunner(crawler=crawler, crawler_queue=crawler_queue).run()
print(response)

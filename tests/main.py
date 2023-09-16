from crawler_manager.engine.crawler_runner import CrawlerRunner
from crawler_manager.queues.default_queue import FIFOMemoryQueue, MemoryCrawledQueue
from tests.crawlers.test_crawler import QuotesToScrapeCrawler

crawler = QuotesToScrapeCrawler
crawled_queue = MemoryCrawledQueue()
crawler_queue = FIFOMemoryQueue(crawler=crawler, crawled_queue=crawled_queue, save_crawled_queue=True)
response = CrawlerRunner(crawler=crawler, crawler_queue=crawler_queue).run()
print(response)

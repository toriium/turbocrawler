from crawler_manager.engine.crawler_runner import CrawlerRunner
from crawler_manager.queues.crawler_queues import FIFOMemoryQueue
from tests.crawlers.test_crawler import QuotesToScrapeCrawler

crawler = QuotesToScrapeCrawler
crawler_queue = FIFOMemoryQueue(save_crawled_queue=True)
response = CrawlerRunner(crawler=crawler, crawler_queue=crawler_queue).run()
print(response)

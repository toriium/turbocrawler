import pytest

from turbocrawler import CrawlerRequest
from turbocrawler.queues.crawler_queues import FIFOMemoryCrawlerQueue


@pytest.fixture
def crawler_queue() -> FIFOMemoryCrawlerQueue:
    return FIFOMemoryCrawlerQueue(crawler_name="TestCrawler")

async def test_queue_add_different_urls(crawler_queue):
    urls = [f"http://example.com/{i}" for i in range(2)]

    for url in urls:
        await crawler_queue.add(CrawlerRequest(url=url))

    assert len(crawler_queue) == len(urls)
    assert crawler_queue.urls_scheduled() == set(urls)

async def test_queue_add_same_url(crawler_queue):
    url = "http://example.com"

    for _ in range(5):
        await crawler_queue.add(CrawlerRequest(url=url))

    assert len(crawler_queue) == 1
    assert crawler_queue.urls_scheduled() == set([url])

async def test_queue_add_different_urls_verify_crawled_false(crawler_queue):
    urls = [f"http://example.com/{i}" for i in range(2)]

    for url in urls:
        await crawler_queue.add(CrawlerRequest(url=url), verify_crawled=False)

    assert len(crawler_queue) == len(urls)
    assert crawler_queue.urls_scheduled() == set(urls)

async def test_queue_add_same_url_verify_crawled_false(crawler_queue):
    url = "http://example.com"

    for _ in range(5):
        await crawler_queue.add(CrawlerRequest(url=url), verify_crawled=False)

    assert len(crawler_queue) == 5
    assert crawler_queue.urls_scheduled() == set([url])

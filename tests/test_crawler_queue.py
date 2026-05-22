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

    # Assert queue state
    assert len(crawler_queue) == len(urls)
    assert crawler_queue.urls_scheduled() == urls


async def test_queue_add_same_url(crawler_queue):
    url = "http://example.com"

    for _ in range(5):
        await crawler_queue.add(CrawlerRequest(url=url))

    # Assert queue state
    assert len(crawler_queue) == 1
    assert crawler_queue.urls_scheduled() == [url]


async def test_queue_add_different_urls_verify_crawled_false(crawler_queue):
    urls = [f"http://example.com/{i}" for i in range(2)]

    for url in urls:
        await crawler_queue.add(CrawlerRequest(url=url), verify_crawled=False)

    # Assert queue state
    assert len(crawler_queue) == len(urls)
    assert crawler_queue.urls_scheduled() == urls


async def test_queue_add_same_url_verify_crawled_false(crawler_queue):
    url = "http://example.com"

    for _ in range(5):
        await crawler_queue.add(CrawlerRequest(url=url), verify_crawled=False)

    # Assert queue state
    assert len(crawler_queue) == 5
    assert crawler_queue.urls_scheduled() == [url] * 5


async def test_queue_get_empty(crawler_queue):
    result = await crawler_queue.get()
    assert result is None


async def test_queue_get(crawler_queue):
    url = "http://example.com"
    await crawler_queue.add(CrawlerRequest(url=url))

    result = await crawler_queue.get()
    assert result.url == url

    # Assert queue state
    assert len(crawler_queue) == 0
    assert crawler_queue.urls_scheduled() == []


async def test_queue_get_different_urls(crawler_queue):
    urls = [f"http://example.com/{i}" for i in range(3)]

    for url in urls:
        await crawler_queue.add(CrawlerRequest(url=url))

    for url in urls:
        result = await crawler_queue.get()
        assert result.url == url

    # Assert queue state
    assert len(crawler_queue) == 0
    assert crawler_queue.urls_scheduled() == []


async def test_queue_get_same_url(crawler_queue):
    url = "http://example.com"
    for _ in range(3):
        await crawler_queue.add(CrawlerRequest(url=url))

    # 1 call
    result = await crawler_queue.get()
    assert result.url == url

    # 2 call
    result = await crawler_queue.get()
    assert result is None

    # Assert queue state
    assert len(crawler_queue) == 0
    assert crawler_queue.urls_scheduled() == []


async def test_queue_get_same_url_verify_crawled_false(crawler_queue):
    url = "http://example.com"
    for _ in range(2):
        await crawler_queue.add(CrawlerRequest(url=url), verify_crawled=False)

    # 1 call
    result = await crawler_queue.get()
    assert result.url == url

    # 2 call
    result = await crawler_queue.get()
    assert result.url == url

    # Assert queue state
    assert len(crawler_queue) == 0
    assert crawler_queue.urls_scheduled() == []

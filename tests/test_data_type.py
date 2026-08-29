from turbocrawler.engine.data_types.crawler import CrawlerResponse


def test_crawler_response_valid_json_dict():
    text = '{"key": "value"}'
    response = CrawlerResponse(url="http://example.com", text=text, status_code=200)
    assert response.json() == {"key": "value"}


def test_crawler_response_valid_json_list():
    text = '["value1", "value2"]'
    response = CrawlerResponse(url="http://example.com", text=text, status_code=200)
    assert response.json() == ["value1", "value2"]


def test_crawler_response_invalid_json():
    text = "invalid json"
    response = CrawlerResponse(url="http://example.com", text=text, status_code=200)
    assert response.json() is None

class ReMakeRequest(Exception):
    def __init__(self, retries):
        self.retries = retries


class SkipRequest(Exception):
    def __init__(self, reason: str = None):
        self.reason = reason


class StopCrawler(Exception):
    def __init__(self, reason: str = None, error: bool = True):
        self.error = error
        self.reason = reason


class PauseCrawler(Exception):
    """
    Raises to stop the crawler process for some time
    """

    def __init__(self, time: int):
        self.time = time

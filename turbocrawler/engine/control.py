class ReMakeRequest(Exception):
    def __init__(self, retries):
        self.retries = retries


class SkipRequest(Exception):
    def __init__(self, reason: str = None):
        self.reason = reason


class StopCrawler(Exception):
    def __init__(self, reason: str = None):
        self.reason = reason

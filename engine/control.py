class ReMakeRequest(Exception):
    def __init__(self, retries):
        self.retries = retries


class SkipRequest(Exception):
    ...


class StopCrawler(Exception):
    ...

class BaseControl(Exception):
    def __init__(self, reason):
        self.reason = reason

class RetryRequest(BaseControl):
    """
    Raises to remake the current request
    """
    def __init__(self, reason: str, retries: int = 0, stop_crawler: bool = True):
        super().__init__(reason)
        self.retries = retries
        self.stop_crawler = stop_crawler



class SkipRequest(BaseControl):
    """
    Raises to skip the current request and move on to the next one
    """
    ...


class StopCrawler(BaseControl):
    """
    Raises to stop the crawler process immediately
    """
    def __init__(self, reason: str, error: bool = True):
        super().__init__(reason)
        self.error = error


class PauseCrawler(BaseControl):
    """
    Raises to stop the crawler process for some time
    """

    def __init__(self, reason: str, time: int):
        super().__init__(reason)
        self.time = time

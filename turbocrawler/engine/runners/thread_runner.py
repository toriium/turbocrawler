import time
from datetime import datetime

from turbocrawler import CrawlerRunner
from turbocrawler.engine.base_queues.crawler_queue_base import CrawlerQueueABC
from turbocrawler.engine.control import ReMakeRequest, SkipRequest
from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.data_types.crawler import CrawlerRequest
from turbocrawler.engine.data_types.info import RunningInfo
from turbocrawler.engine.worker_queues import WorkerQueueManager
from turbocrawler.logger import logger


class ThreadCrawlerRunner(CrawlerRunner):
    def __init__(self,
                 crawler: type[Crawler],
                 crawler_queue: CrawlerQueueABC = None,
                 qtd_request: int = 2):
        super().__init__(crawler=crawler, crawler_queue=crawler_queue)

        self.request_queue_manager: WorkerQueueManager = WorkerQueueManager(queue_name='request_queue',
                                                                            class_object=self.crawler,
                                                                            target=self._make_request,
                                                                            qtd_workers=qtd_request)

    def _process_crawler_queue(self):
        self.request_queue_manager.start_workers()
        logger.info('Processing crawler queue')

        # get requests from crawler queue
        while True:
            self._log_info()
            next_crawler_request = self.crawler_queue.get()
            if next_crawler_request:
                # self._make_request(crawler_request=next_crawler_request)
                self.request_queue_manager.queue.put({"crawler_request": next_crawler_request})
            else:
                time.sleep(1)
                if self.request_queue_manager.workers_executing():
                    time.sleep(1)
                    continue
                if not self.request_queue_manager.queue.is_empty():
                    time.sleep(1)
                    continue
                if self.crawler_queue:
                    continue

                logger.info('Crawler queue is empty, all crawler_requests made')
                # Wait until parse_queue is empty
                self.parse_queue_manager.stop_workers()
                self.request_queue_manager.stop_workers()
                logger.info('Parse queue is empty, all parse_crawler_response made')
                return True

    def _make_request(self, crawler_request: CrawlerRequest):
        request_retries = 0
        while True:
            try:
                time.sleep(self.crawler.time_between_requests)
                logger.debug(f'[process_request] URL: {crawler_request.url}')
                crawler_response = self.crawler.process_request(crawler_request=crawler_request)
                self._add_urls_to_queue(crawler_response=crawler_response)

                self.parse_queue_manager.queue.put({"crawler_request": crawler_request,
                                                    "crawler_response": crawler_response})
                self._requests_info['Made'] += 1
                break
            except ReMakeRequest as error:
                self._requests_info['ReMakeRequest'] += 1
                request_retries += 1
                error_retries = error.retries
                if request_retries >= error_retries:
                    logger.warn(f'Exceed retry tentatives for url {crawler_request.url}')
                    break
            except SkipRequest as error:
                self._requests_info['SkipRequest'] += 1
                logger.info(f'Skipping request for url {crawler_request.url} reason: {error.reason}')
                break

    def _get_running_info(self) -> RunningInfo:
        running_time = datetime.now() - self._start_process_time
        return RunningInfo(
            crawler_queue=self.crawler_queue.get_info(),
            crawled_queue=self.crawler_queue.crawled_queue.get_info(),
            requests_made=self._requests_info["Made"],
            requests_remade=self._requests_info["ReMakeRequest"],
            requests_skipped=self._requests_info["SkipRequest"],
            parse_queue=None,
            running_time=str(running_time),
            running_id=self._running_id
        )

import time
from queue import Empty, Queue
from threading import Thread
from typing import Callable

from turbocrawler.logger import logger


class WorkerQueue:
    __queue = Queue()

    @classmethod
    def put(cls, data):
        cls.__queue.put(data)

    @classmethod
    def get(cls):
        try:
            return cls.__queue.get(block=False)
        except Empty:
            return None

    @classmethod
    def is_empty(cls):
        return cls.__queue.empty()


class WorkerQueueManager:
    def __init__(self, queue_name: str, class_object: object, target: Callable, qtd_workers: int):
        self.queue_name = queue_name
        self.class_object = class_object
        self.target = target
        self.qtd_workers = qtd_workers
        self.workers = None
        self.queue = WorkerQueue()
        self.must_stop_workers = False

    def start_workers(self):
        self.workers = [
            ConsumerQueueWorker(worker_name=f'Worker[{c}]', worker_queue_manager=self)
            for c in range(self.qtd_workers)]
        [w.start() for w in self.workers]

    def stop_workers(self):
        self.must_stop_workers = True
        [w.join() for w in self.workers]


class ConsumerQueueWorker(Thread):
    def __init__(self, worker_name: str, worker_queue_manager: WorkerQueueManager):
        Thread.__init__(self)
        self.worker_name = worker_name
        self.queue_name = worker_queue_manager.queue_name
        self.worker_queue_manager = worker_queue_manager
        self.queue = worker_queue_manager.queue
        self.target = worker_queue_manager.target
        logger.debug(f'{self.queue_name}|{self.worker_name}| CREATED')

    def run(self):
        while True:
            if self.queue.is_empty():
                if self.worker_queue_manager.must_stop_workers:
                    logger.debug(f'{self.queue_name}|{self.worker_name}| STOPPING')
                    break
                logger.debug(f'{self.queue_name}|{self.worker_name}| WAITING')
                time.sleep(1)
                continue

            next_call = self.queue.get()
            if not next_call:
                continue

            try:
                logger.debug(f'[{self.target.__name__}] URL: {next_call.get("crawler_response").site_url}')
                self.target(self.worker_queue_manager.class_object, **next_call)
            except Exception as error:
                logger.error(error)

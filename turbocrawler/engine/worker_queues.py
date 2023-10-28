import time
from collections.abc import Callable
from enum import Enum
from queue import Empty, Queue
from threading import Thread

from turbocrawler.engine.data_types.info import WorkerQueueInfo, WorkerQueueManagerInfo, WorkersStateInfo
from turbocrawler.logger import logger


class WorkerState(Enum):
    WAITING = "WAITING"
    EXECUTING = "EXECUTING"
    STOPPED = "STOPPED"


class WorkerQueue:
    def __init__(self):
        self.__queue = Queue()
        self.info = WorkerQueueInfo(add=0, get=0, length=0)

    def get_info(self) -> WorkerQueueInfo:
        return WorkerQueueInfo(add=self.info["add"], get=self.info["get"], length=self.__queue.qsize())

    def put(self, data):
        self.info["add"] += 1
        self.__queue.put(data)

    def get(self):
        try:
            value = self.__queue.get(block=False)
            self.info["get"] += 1

        except Empty:
            return None
        return value

    def is_empty(self):
        return self.__queue.empty()

    def __len__(self):
        return self.__queue.qsize()


class WorkerQueueManager:
    def __init__(self, queue_name: str, class_object: object, target: Callable, qtd_workers: int):
        self.queue_name = queue_name
        self.class_object = class_object
        self.target = target
        self.qtd_workers = qtd_workers
        self.workers: list[ConsumerQueueWorker] = []
        self.queue = WorkerQueue()
        self.must_stop_workers = False

    def __get_workers_state(self) -> WorkersStateInfo:
        workers_state = WorkersStateInfo(WAITING=0, EXECUTING=0, STOPPED=0)
        for worker in self.workers:
            state = worker.worker_state.value
            workers_state[state] += 1

        return workers_state

    def workers_executing(self) -> bool:
        states = self.__get_workers_state()
        executing = states.get(WorkerState.EXECUTING.value)
        if executing:
            return True
        return False

    def get_info(self) -> WorkerQueueManagerInfo:
        workers_state = self.__get_workers_state()
        return WorkerQueueManagerInfo(queue_name=self.queue_name,
                                      queue_info=self.queue.get_info(),
                                      workers_state=workers_state)

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
        self.worker_state = WorkerState.WAITING
        logger.debug(f'{self.queue_name}|{self.worker_name}| CREATED')

    def run(self):
        while True:
            if self.queue.is_empty():
                if self.worker_queue_manager.must_stop_workers:
                    logger.debug(f'{self.queue_name}|{self.worker_name}| STOPPING')
                    self.worker_state = WorkerState.STOPPED
                    break
                time.sleep(1)
                self.worker_state = WorkerState.WAITING
                continue

            next_call = self.queue.get()
            if not next_call:
                continue

            self.worker_state = WorkerState.EXECUTING
            try:
                logger.debug(f'[{self.target.__name__}] URL: {self.__get_url(next_call)}')
                # self.target(self.worker_queue_manager.class_object, **next_call)
                self.target(**next_call)
            except Exception as error:
                logger.exception(f'{self.queue_name}|{self.worker_name}\n{error}')

    @staticmethod
    def __get_url(next_call):
        data = next_call.get("crawler_response")
        if data:
            return data.url
        return next_call.get("crawler_request").url

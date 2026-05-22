import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from turbocrawler.logger import logger


def get_running_id() -> str:
    now = datetime.now()
    f_date = now.strftime("%Y%m%d_%H%M%S")
    return f"{f_date}_{uuid4().hex[-5:]}"


class JobBase(ABC):
    name: str

    def __init__(self):
        self._running_id = get_running_id()

    async def start(self):
        self._start_process_time = datetime.now()

        logger.info(f"{self.name} --- Start ---")
        try:
            logger.info(f"Calling {self.name}.run")
            response = await self.run()
            self.job_success()
        except Exception as e:
            self.job_error(exception=e)
            response = None

        logger.info(f"{self.name} --- END took:{self.running_time()} ---")
        return response

    def job_success(self):
        logger.info(f"{self.name} --- Success ---")

    def job_error(self, exception: Exception):
        logger.error(f"{self.name} --- Error ---")
        exception_reason = traceback.format_exception_only(exception)[-1].strip()
        logger.error(f"REASON: {exception_reason}")
        logger.exception("Error tracestack")

    def running_time(self) -> datetime:
        now = datetime.now()
        return now - self._start_process_time

    @abstractmethod
    async def run(self):
        pass

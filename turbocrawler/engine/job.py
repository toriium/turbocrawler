import os
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from turbocrawler.logger import logger


def get_run_id() -> str:
    now = datetime.now()
    now_str = now.strftime("%Y%m%dT%H%M%S")
    return f"{now_str}_{uuid4().hex[:6]}"


class JobBase(ABC):
    name: str
    log_dir_name: str | None = None
    logger = logger

    def __init__(self):
        self._run_id = get_run_id()
        self._log_handlers = []

    async def start(self):
        self._start_process_time = datetime.now()
        log_path = f"{os.getcwd()}/turbocrawler_logs/{self.log_dir_name or self.name}/{self._run_id}/execution.log"
        self._log_handlers.append(logger.create_file_handler(log_path))

        logger.info(f"{self.name} --- Start ---")
        response = None
        try:
            logger.info(f"Calling {self.name}.run")
            response = await self.run()
            self.job_success()
        except Exception as e:
            self.job_error(exception=e)
        finally:
            logger.info(f"{self.name} --- END took:{self.running_time()} ---")
            for handler in self._log_handlers:
                logger.remove_handler(handler)
            self._log_handlers = []

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

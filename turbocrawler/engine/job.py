import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from turbocrawler.logger import RunIdFilter, formatter, run_id_var
from turbocrawler.utils import create_file_path

logger = logging.getLogger(__name__)


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
        run_id_token = run_id_var.set(self._run_id)
        self._log_handlers.append(self._create_file_handler())

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
                logging.getLogger("turbocrawler").removeHandler(handler)
                handler.close()
            self._log_handlers = []
            run_id_var.reset(run_id_token)

        return response

    def _create_file_handler(self) -> logging.FileHandler:
        self._run_dir = Path.cwd() / "turbocrawler_logs" / (self.log_dir_name or self.name) / self._run_id
        self._log_path = self._run_dir / "execution.log"
        create_file_path(self._log_path)
        file_handler = logging.FileHandler(self._log_path, mode="w")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RunIdFilter(self._run_id))
        logging.getLogger("turbocrawler").addHandler(file_handler)
        return file_handler

    def job_success(self):
        logger.info(f"{self.name} --- Success ---")

    def job_error(self, exception: Exception):
        logger.error(f"{self.name} --- Error ---")
        exception_reason = traceback.format_exception_only(exception)[-1].strip()
        logger.error(f"REASON: {exception_reason}")
        logger.exception("Error tracestack")

    def running_time(self) -> timedelta:
        now = datetime.now()
        return now - self._start_process_time

    @abstractmethod
    async def run(self):
        pass

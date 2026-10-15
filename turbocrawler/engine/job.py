from dataclasses import dataclass, field
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from turbocrawler.logger import RunIdFilter, formatter, run_id_var
from turbocrawler.utils import create_file_path

logger = logging.getLogger("turbocrawler")


def get_run_id() -> str:
    now = datetime.now()
    now_str = now.strftime("%Y%m%dT%H%M%S")
    return f"{now_str}_{uuid4().hex[:6]}"

@dataclass(kw_only=True)
class JobInfo:
    name: str
    run_id: str
    run_dir: Path
    log_path: Path
    log_dir_name: str | None = None
    job_start_time: datetime

@dataclass(kw_only=True)
class JobExecutionResult(JobInfo):
    job_end_time: datetime
    job_running_time: timedelta
    success: bool
    reason: str | None
    exception: Exception | None

class JobBase(ABC):
    name: str 
    log_dir_name: str | None = None # Directory name for storing log files, defaults to job name if not set
    logger: logging.Logger
    job_info: JobInfo

    _run_id: str # Unique identifier for the current job run
    _run_dir: Path # Directory for any runtime files related to the job
    _log_path: Path # Path to the log file for the job
    _job_start_time: datetime # When the current job run started

    def __init__(self):
        assert hasattr(self, "name"), "Job must have a name"
        
        self._run_id = get_run_id()
        self._log_handlers = []
        self.logger = logger

    async def start(self, log_level: int = logging.INFO):
        self._job_start_time = datetime.now()

        # Define logging for this job run
        logging.getLogger("turbocrawler").setLevel(log_level)
        run_id_token = run_id_var.set(self._run_id)
        self._log_handlers.append(self._create_file_handler())

        self.job_info = JobInfo(
            name=self.name,
            log_dir_name=self.log_dir_name,
            run_id=self._run_id,
            run_dir=self._run_dir,
            log_path=self._log_path,
            job_start_time=self._job_start_time,
        )

        logger.info(f"[Job] {self.name} --- Start ---")

        
        job_execution_result: JobExecutionResult = None
        try:
            await self.notify_job_start(self.job_info)
            logger.info(f"[Job] Calling {self.name}.run")
            job_execution_result = await self.run()

            assert isinstance(job_execution_result, JobExecutionResult), "Job did not return a valid JobExecutionResult"

            self.job_log_success()
        except Exception as e:
            self.job_log_error(exception=e)
            job_execution_result = JobExecutionResult(
                **self.job_info.__dict__,
                job_end_time=datetime.now(),
                job_running_time=self.running_time(),
                success=False,
                reason=str(e),
                exception=e,
            )
        finally:
            # notify_job_end never raises an exception to the caller
            try:
                await self.notify_job_end(job_execution_result)
            except Exception as e:
                logger.error(f"[Job] Error during notify_job_end: {e}")

            logger.info(f"[Job] {self.name} --- END took:{self.running_time()} ---")
            
            # Clean up log handlers for this job run
            for handler in self._log_handlers:
                logging.getLogger("turbocrawler").removeHandler(handler)
                handler.close()
            self._log_handlers = []
            run_id_var.reset(run_id_token)

        return job_execution_result

    def _create_file_handler(self) -> logging.FileHandler:
        self._run_dir = Path.cwd() / "turbocrawler_logs" / (self.log_dir_name or self.name) / self._run_id
        self._log_path = self._run_dir / "execution.log"
        create_file_path(self._log_path)
        file_handler = logging.FileHandler(self._log_path, mode="w")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RunIdFilter(self._run_id))
        logging.getLogger("turbocrawler").addHandler(file_handler)
        return file_handler

    async def notify_job_start(self, job_info: JobInfo):
        logger.debug(f"[Job] {self.name} --- Notify Start ---")

    async def notify_job_end(self, job_execution_result: JobExecutionResult):
        logger.debug(f"[Job] {self.name} --- Notify End ---")

    def job_log_success(self):
        logger.info(f"[Job] {self.name} --- Success ---")

    def job_log_error(self, exception: Exception):
        logger.error(f"[Job] {self.name} --- Error ---")
        exception_reason = traceback.format_exception_only(exception)[-1].strip()
        logger.error(f"REASON: {exception_reason}")
        logger.exception("[Job] Error tracestack")

    def running_time(self) -> timedelta:
        now = datetime.now()
        return now - self._job_start_time

    @abstractmethod
    async def run(self) -> JobExecutionResult:
        pass

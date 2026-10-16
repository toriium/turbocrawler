import asyncio
import logging
import re
from datetime import datetime

from turbocrawler.engine.job import JobBase, JobExecutionResult, get_run_id

logger = logging.getLogger("turbocrawler")


def test_get_run_id_format():
    assert re.fullmatch(r"\d{8}T\d{6}_[0-9a-f]{6}", get_run_id())


def test_get_run_id_unique():
    assert get_run_id() != get_run_id()


class SuccessJob(JobBase):
    name = "SuccessJob"

    async def run(self):
        self.logger.info(f"Running {self.name}")
        await asyncio.sleep(2)
        self.logger.info(f"Finished running {self.name}")
        return JobExecutionResult(
            **self.job_info.__dict__,
            job_end_time=datetime.now(),
            job_running_time=self.running_time(),
            success=True,
            reason=None,
            exception=None,
        )


class ErrorJob(JobBase):
    name = "ErrorJob"

    async def run(self):
        self.logger.info(f"Running {self.name}")
        await asyncio.sleep(2)
        self.logger.info(f"Finished running {self.name}")
        raise Exception("Intentional error for testing")


async def test_success_job_run():
    success_job = SuccessJob()
    await success_job.start()


async def test_error_job_run():
    error_job = ErrorJob()
    try:
        await error_job.start()
    except Exception as e:
        assert str(e) == "Intentional error for testing"


async def test_each_run_has_own_log_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handlers_before = list(logger.handlers)

    success_result = await SuccessJob().start()
    assert logger.handlers == handlers_before

    error_result = await ErrorJob().start()
    assert logger.handlers == handlers_before

    success_log = success_result.log_path.read_text()
    error_log = error_result.log_path.read_text()

    assert "SuccessJob --- Start ---" in success_log
    assert "SuccessJob --- END" in success_log
    assert "ErrorJob" not in success_log

    assert "ErrorJob --- Error ---" in error_log
    assert "SuccessJob" not in error_log


async def test_log_dir_name_overrides_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    job = SuccessJob()
    job.log_dir_name = "custom_dir"
    result = await job.start()

    assert result.log_path.exists()
    assert result.log_path.parent.parent.name == "custom_dir"


async def test_parallel_runs_have_isolated_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handlers_before = list(logger.handlers)

    success_result, error_result = await asyncio.gather(SuccessJob().start(), ErrorJob().start())
    assert logger.handlers == handlers_before

    success_log = success_result.log_path.read_text()
    error_log = error_result.log_path.read_text()

    assert "Finished running SuccessJob" in success_log
    assert "ErrorJob" not in success_log

    assert "Finished running ErrorJob" in error_log
    assert "SuccessJob" not in error_log


async def test_job_triggers_notify_success(tmp_path, monkeypatch):
    job = SuccessJob()
    result: JobExecutionResult = await job.start(log_level=logging.DEBUG)

    assert result.success is True
    log = result.log_path.read_text()
    assert "SuccessJob --- Notify Start ---" in log
    assert "SuccessJob --- Notify End ---" in log


async def test_job_triggers_notify_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    job = ErrorJob()
    result: JobExecutionResult = await job.start(log_level=logging.DEBUG)

    assert result.success is False
    log = result.log_path.read_text()
    assert "ErrorJob --- Notify Start ---" in log
    assert "ErrorJob --- Notify End ---" in log

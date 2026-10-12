import re
import asyncio
from turbocrawler.engine.job import get_run_id, JobBase
from turbocrawler.logger import logger


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


class ErrorJob(JobBase):
    name = "ErrorJob"

    async def run(self):
        self.logger.info(f"Running {self.name}")
        await asyncio.sleep(2)
        self.logger.info(f"Finished running {self.name}")
        raise Exception("Intentional error for testing")

def test_success_job_run():
    success_job = SuccessJob()
    asyncio.run(success_job.start())

def test_error_job_run():
    error_job = ErrorJob()
    try:
        asyncio.run(error_job.start())
    except Exception as e:
        assert str(e) == "Intentional error for testing"

def test_each_run_has_own_log_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handlers_before = list(logger.handlers)

    success_job = SuccessJob()
    asyncio.run(success_job.start())
    assert logger.handlers == handlers_before

    error_job = ErrorJob()
    asyncio.run(error_job.start())
    assert logger.handlers == handlers_before

    success_log = (tmp_path / "turbocrawler_logs" / "SuccessJob" / success_job._run_id / "execution.log").read_text()
    error_log = (tmp_path / "turbocrawler_logs" / "ErrorJob" / error_job._run_id / "execution.log").read_text()

    assert "SuccessJob --- Start ---" in success_log
    assert "SuccessJob --- END" in success_log
    assert "ErrorJob" not in success_log

    assert "ErrorJob --- Error ---" in error_log
    assert "SuccessJob" not in error_log


def test_log_dir_name_overrides_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    job = SuccessJob()
    job.log_dir_name = "custom_dir"
    asyncio.run(job.start())

    assert (tmp_path / "turbocrawler_logs" / "custom_dir" / job._run_id / "execution.log").exists()

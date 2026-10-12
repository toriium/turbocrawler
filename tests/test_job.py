import re
import asyncio
from turbocrawler.engine.job import get_run_id, JobBase


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
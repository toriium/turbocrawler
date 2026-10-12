import logging
from contextvars import ContextVar


"""
This module provides a logging setup for the Turbocrawler project.
It includes a custom logging filter to associate log records with a specific run ID.

Each logger must be different for each run
Each logger should be accessed in any part of the code through the getLogger("turbocrawler") code.
When Changing the "turbocrawler" logger level, it only changes the level for this logger not impacting other loggers.
If running Jobs in parallel, each job should have its own run ID to ensure log records are correctly associated with the respective job.

Log level will be defined in the start() method of each job.
---
HOW TO USE:

logger = logging.getLogger("turbocrawler")
logger.info("This is an example log message.")
"""

formatter = logging.Formatter("%(asctime)s|%(levelname)s| %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

run_id_var: ContextVar[str | None] = ContextVar("run_id", default=None)


class RunIdFilter(logging.Filter):
    """Only lets through records logged inside the run with this run_id"""

    def __init__(self, run_id: str):
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        return run_id_var.get() == self.run_id


_console_handler = logging.StreamHandler()
_console_handler.setFormatter(formatter)

logging.getLogger("turbocrawler").addHandler(_console_handler)

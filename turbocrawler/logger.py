import logging
from contextvars import ContextVar

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

_base_logger = logging.getLogger("turbocrawler")
_base_logger.setLevel(logging.INFO)
_base_logger.addHandler(_console_handler)

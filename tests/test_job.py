import re

from turbocrawler.engine.job import get_run_id


def test_get_run_id_format():
    assert re.fullmatch(r"\d{8}T\d{6}_[0-9a-f]{6}", get_run_id())


def test_get_run_id_unique():
    assert get_run_id() != get_run_id()

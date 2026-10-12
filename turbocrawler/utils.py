from pathlib import Path


def create_file_path(file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch(exist_ok=True)

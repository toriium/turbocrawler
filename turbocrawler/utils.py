import os
from datetime import datetime
from uuid import uuid4


def create_file_path(file_path: str):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            ...


def get_running_id() -> str:
    now = datetime.now()
    f_date = now.strftime("%Y%m%d_%H%M%S")
    return f"{f_date}_{uuid4().hex[-5:]}"

import os


def create_file_path(file_path: str):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            ...


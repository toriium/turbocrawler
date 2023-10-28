import logging
import os

from turbocrawler.utils import create_file_path

formatter = logging.Formatter('%(asctime)s|%(levelname)s| %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class LOG(logging.Logger):
    def create_console_handler(self):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

    def create_file_handler(self, dir: str, filename: str):
        path = f'{os.getcwd()}/crawler_logs/{dir}/{filename}.txt'
        create_file_path(path)
        file_handler = logging.FileHandler(path, mode='w')
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)


logger = LOG('turbocrawler')
logger.setLevel(logging.INFO)
logger.create_console_handler()

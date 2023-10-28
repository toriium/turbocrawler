import logging
import os

formatter = logging.Formatter('%(asctime)s|%(levelname)s| %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

logger = logging.getLogger('turbocrawler')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(f'{os.getcwd()}/log.txt')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

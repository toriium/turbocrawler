import logging

logger = logging.getLogger('easycrawler')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('-log',
                    '--loglevel',
                    default='info',
                    help='Provide logging level. Example --loglevel debug, default=info')
args = parser.parse_args()

logger = logging.getLogger()
logger.setLevel(args.loglevel.upper())

ch = logging.StreamHandler()
ch.setLevel(args.loglevel.upper())

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

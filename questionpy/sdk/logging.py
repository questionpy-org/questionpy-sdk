import logging
import sys


def init_logging():
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

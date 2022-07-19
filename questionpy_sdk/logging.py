import logging
import sys


def init_logging() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

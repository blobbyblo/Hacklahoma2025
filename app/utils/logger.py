"""
Logging setup.
"""
import logging


def get_logger(name=__name__):
  logger = logging.getLogger(name)
  if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
  return logger

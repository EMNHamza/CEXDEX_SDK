# log_config.py

import logging
from logging.handlers import TimedRotatingFileHandler
import time


def setup_logging():
    log_filename = time.strftime("_logs/LogsCexDex.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Désactiver les gestionnaires existants (notamment ceux de la console)
    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = TimedRotatingFileHandler(
        log_filename,
        when="midnight",
        interval=1,
        backupCount=10
    )
    handler.suffix = "%Y%m%d.log"

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)



def test_setup_logging():
    log_filename = time.strftime("_logs/TESTLogsCexDex.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Désactiver les gestionnaires existants (notamment ceux de la console)
    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = TimedRotatingFileHandler(
        log_filename,
        when="midnight",
        interval=1,
        backupCount=10
    )
    handler.suffix = "%Y%m%d.log"

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

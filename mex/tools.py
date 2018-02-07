# -*- coding: utf-8 -*-
import logging


log = logging.getLogger(__name__)


def init_logging(disable_libs=True):
    """Activate simple console debug logging"""

    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    if disable_libs:
        loggers = logging.Logger.manager.loggerDict.keys()
        for logger in loggers:
            if not logger.startswith('mex'):
                logging.getLogger(logger).disabled = True


def batchwise(rng: range, batch_size):
    """Batchwise api iteration.

    batchwise(range(1501, 1750), 100)
    ['1501-1600', '1601-1700', '1701-1750']
    """
    for i in range(0, len(rng) + 1, batch_size):
        batch = rng[i:i + batch_size - 1]
        yield '{}-{}'.format(batch.start, batch.stop)

"""```python
from .logger import IS_DEBUG, LOG_LEVEL, getLogger
```"""
import os
import logging
from tqdm import tqdm
_LOG_KEYS = ['LOG', 'LOGLEVEL', 'LOG_LEVEL']
_LOGLEVEL = [os.environ.get(k) for k in _LOG_KEYS]
_LOGLEVEL = [x for x in _LOGLEVEL if x is not None]
_LOGLEVEL = _LOGLEVEL[0].lower() if _LOGLEVEL else 'info'
_LOGLVLS = ['debug', 'info', 'warn', 'error', 'critical', 'fatal']
_LOGLVLS = {x[0]: x for x in _LOGLVLS}
LOG_LEVEL = _LOGLVLS.get(_LOGLEVEL[0], 'info')
LOG_LEVEL_INT = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
IS_DEBUG = LOG_LEVEL == 'debug'
_DATEFMT = '%H:%M:%S'
_LEVEL_PREFIX = {
    logging.DEBUG: '🔍DEBUG',
    logging.INFO: '💬 INFO',
    logging.WARNING: '⚠️  WARN',
    logging.ERROR: '❌ERROR',
    logging.CRITICAL: '⛔⛔CRITICAL',
    logging.FATAL: '☠️FATAL',
}


class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = _LEVEL_PREFIX.get(record.levelno, record.levelname)
        return super().format(record)


class TqdmStream(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)
        self.flush()


_HANDLER = TqdmStream()
_HANDLER.setFormatter(CustomFormatter('%(levelname)s %(asctime)s %(filename)s:%(lineno)d\t%(message)s', datefmt=_DATEFMT))


def getLogger(name=__name__):
    Log = logging.getLogger(name)
    Log.setLevel(LOG_LEVEL.upper())
    Log.addHandler(_HANDLER)
    Log.propagate = False
    return Log


Log = getLogger(__name__)

if __name__ == '__main__':
    from time import sleep
    Log.debug('Hello, world!')
    TOTAL = 10
    with tqdm(total=TOTAL, desc='Progress') as pbar:
        for i in range(TOTAL):
            Log.log(LOG_LEVEL_INT, f'Progress: {i + 1}/10')
            sleep(0.1)
            pbar.update(1)

"""```python
from mocap_wrapper.logger import PG_DL, IS_DEBUG, LOGLEVEL
```"""
import atexit
import logging
from os import environ, path
IS_DEBUG = False
_LOGLEVEL = environ.get('LOG')
if _LOGLEVEL and _LOGLEVEL.upper().startswith('D'):
    IS_DEBUG = True
_LOGLEVEL = (_LOGLEVEL or 'INFO').upper()[0]
_DATEFMT = '%H:%M:%S'
_LEVEL_PREFIX = {
    logging.DEBUG: '🔍DEBUG',
    logging.INFO: '💬 INFO',
    logging.WARNING: '⚠️  WARN',
    logging.ERROR: '❌ERROR',
    logging.CRITICAL: '⛔⛔CRITICAL',
    logging.FATAL: '☠️FATAL',
}
LEVEL_STR_INT = {
    'D': logging.DEBUG,
    'I': logging.INFO,
    'W': logging.WARNING,
    'E': logging.ERROR,
    'C': logging.CRITICAL,
    'F': logging.FATAL,
}
LOGLVL = LEVEL_STR_INT.get(_LOGLEVEL, logging.INFO)


class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = _LEVEL_PREFIX.get(record.levelno, record.levelname)
        return super().format(record)


from logging import StreamHandler
HANDLER = StreamHandler()
HANDLER.setFormatter(CustomFormatter('%(levelname)s %(asctime)s %(filename)s:%(lineno)d\t%(message)s', datefmt=_DATEFMT))


def getLogger(name=__name__):
    Log = logging.getLogger(name)
    Log.setLevel(LOGLVL)
    Log.addHandler(HANDLER)
    Log.propagate = False
    return Log


Log = getLogger(__name__)

if __name__ == '__main__':
    Log.debug('Hello, world!')
    # task = PROGRESS_DL.add_task('test', total=10)
    from time import sleep
    for i in range(10):
        # PROGRESS_DL.update(task, advance=1)
        Log.info(f'Progress: {i + 1}/10')
        sleep(0.1)
    # cleanup()

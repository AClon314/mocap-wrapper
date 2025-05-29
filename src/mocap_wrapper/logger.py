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


try:
    from rich.text import Text
    # from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, TextColumn
    HANDLER = RichHandler(rich_tracebacks=True)
    HANDLER.setFormatter(CustomFormatter(datefmt=_DATEFMT))

    class SpeedColumn(TextColumn):
        def __init__(self, unit='steps/s', *args, **kwargs) -> None:
            """
            Use `"{task.fields['status']}"` first, then use `'{task.speed:.3f} {unit}'`

            Args:
                args: see `TextColumn`
                kwargs: see `TextColumn`

            Usage:
            ```python
            pg = Progress(SpeedColumn(unit='frame/s'))
            pg.update(task, ...)    # use self-contained speed
            pg.update(task, status='Start') # use status
            ```
            """
            super().__init__(*args, text_format=kwargs.pop('text_format', ''), **kwargs)
            self.unit = unit

        def render(self, task):
            text = ''
            if 'status' in task.fields.keys():
                text = task.fields['status']
            elif task.speed:
                text = f"{task.speed:.3f} {self.unit}"
            return Text(text=text)

    def cleanup():
        """
        start then **STOP** progress bar

        ps: I don't like rich.Console, on linux it makes the scroll bar unuseable, could cause flickering progress.
        Every time you `stop()` brings side effect: breaking 2 new blank lines.
        """
        if 'PROGRESS_DL' in globals():
            PROGRESS_DL.start()
            PROGRESS_DL.stop()
        # if 'CONSOLE' in globals():
        #     CONSOLE.end_capture()
    atexit.register(cleanup)

    PROGRESS_DL = Progress(*Progress.get_default_columns(), SpeedColumn())
    PROGRESS_DL.start()

    # CONSOLE = Console()
except ImportError:
    print(f'{path.basename(__file__)}\t⚠️ rich not installed，fallback to logging.StreamHandler')
    from logging import StreamHandler
    HANDLER = StreamHandler()
    HANDLER.setFormatter(CustomFormatter('%(filename)s:%(lineno)d\t%(funcName)s: %(message)s', datefmt=_DATEFMT))


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

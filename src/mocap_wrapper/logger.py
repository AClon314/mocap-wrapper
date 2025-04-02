"""```python
from mocap_wrapper.logger import PG_DL, IS_DEBUG, LOGLEVEL
```"""
import atexit
import logging
from logging import getLogger
from typing import Any
from os import environ, path
IS_DEBUG = False
LOGLEVEL = environ.get('LOGLVL')
if LOGLEVEL and LOGLEVEL.upper() == 'DEBUG':
    IS_DEBUG = True
LOGLEVEL = (LOGLEVEL or 'INFO').upper()
fmt = ''
config: dict[str, Any] = {
    'level': LOGLEVEL,
    'datefmt': '%H:%M:%S',
}

try:
    from rich.text import Text
    # from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, TextColumn
    config['handlers'] = [RichHandler(rich_tracebacks=True)]

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
        """start then **STOP** progress bar"""
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
    config['handlers'] = [StreamHandler()]
    fmt = ' %(filename)s:%(lineno)d\t'
logging.basicConfig(
    **config,
    format=fmt + '%(funcName)s: %(message)s',
)

if __name__ == '__main__':
    Log = getLogger(__name__)
    Log.debug('Hello, world!')
    task = PROGRESS_DL.add_task('test', total=10)
    from time import sleep
    for i in range(10):
        PROGRESS_DL.update(task, advance=1)
        sleep(0.1)
    cleanup()

"""```python
from mocap_wrapper.logger import getLogger, PG_DL, IS_DEBUG, LOGLEVEL
```"""
import atexit
import logging
from logging import getLogger
from os import environ, path
IS_DEBUG = False
LOGLEVEL = environ.get('LOGLVL')
if LOGLEVEL:
    IS_DEBUG = True
LOGLEVEL = (LOGLEVEL or 'INFO').upper()
fmt = ''
config = {
    'level': LOGLEVEL,
    'datefmt': '%H:%M:%S',
}

# ignore urllib3.connectionpool
connectionpool_logger = getLogger("urllib3.connectionpool")
connectionpool_logger.setLevel(logging.CRITICAL)

try:
    from rich import print
    from rich.text import Text
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, TextColumn
    config['handlers'] = [RichHandler(rich_tracebacks=True)]

    class SpeedColumn(TextColumn):
        def render(self, task):
            text = ''
            if 'status' in task.fields.keys():
                text = task.fields['status']
            elif task.speed:
                text = f"{task.speed:.3f} steps/s"
            return Text(text=text)

    def cleanup():
        if 'PROGRESS_DL' in globals():
            PROGRESS_DL.stop()
        # if 'CONSOLE' in globals():
        #     CONSOLE.end_capture()
    atexit.register(cleanup)

    PROGRESS_DL = Progress(*Progress.get_default_columns(), SpeedColumn(''))
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

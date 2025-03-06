"""```python
from mocap_wrapper.logger import getLogger, dl_pg
```"""
import atexit
import logging
from logging import getLogger
from os import environ, path
LOGLEVEL = environ.get('LOGLVL', 'INFO').upper()
LOGFILE = environ.get('LOG')
fmt = ''
config = {
    'level': LOGLEVEL,
    'datefmt': '%H:%M:%S',
}
if LOGFILE:
    config['filename'] = LOGFILE

# ignore urllib3.connectionpool
connectionpool_logger = getLogger("urllib3.connectionpool")
connectionpool_logger.setLevel(logging.CRITICAL)

try:
    from rich import print
    from rich.text import Text
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

    PG_DL = Progress(*Progress.get_default_columns(), SpeedColumn(''))
    PG_DL.start()
except ImportError:
    print(f'{path.basename(__file__)}\t⚠️ rich not installed，fallback to logging.StreamHandler')
    from logging import StreamHandler
    config['handlers'] = [StreamHandler()]
    fmt = ' %(filename)s:%(lineno)d\t'
logging.basicConfig(
    **config,
    format=fmt + '%(funcName)s: %(message)s',
)


def cleanup():
    if 'PG_DL' in globals():
        PG_DL.stop()


atexit.register(cleanup)

if __name__ == '__main__':
    Log = getLogger(__name__)
    Log.debug('Hello, world!')

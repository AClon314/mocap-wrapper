from os import environ, path
from logging import basicConfig, getLogger


def getLog(name=__name__):
    LOGLEVEL = environ.get('LOGLEVEL', 'INFO').upper()
    config = {
        'level': LOGLEVEL,
        'datefmt': '%H:%M:%S',
        # 'filename': f'{__file__}.log',
    }
    fmt = ''
    try:
        from rich.logging import RichHandler
        config['handlers'] = [RichHandler()]
    except ImportError:
        print(f'{path.basename(__file__)}\t⚠️ rich not installed，fallback to logging.StreamHandler')
        from logging import StreamHandler
        config['handlers'] = [StreamHandler()]
        fmt = '%(filename)s:%(lineno)d\t'
    basicConfig(
        **config,
        format=fmt + '%(funcName)s: %(message)s',
    )
    return getLogger(name)

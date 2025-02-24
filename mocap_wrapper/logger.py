from os import environ
from rich.logging import RichHandler
from logging import basicConfig, getLogger


def getLog(name=__name__):
    LOGLEVEL = environ.get('LOGLEVEL', 'INFO').upper()
    basicConfig(
        level=LOGLEVEL,
        format='%(funcName)s: %(message)s',
        datefmt='%H:%M:%S',
        # filename=f'{__file__}.log',
        handlers=[RichHandler()]
    )
    return getLogger(name)

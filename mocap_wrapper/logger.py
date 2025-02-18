from os import environ
import logging

LOGLEVEL = environ.get('LOGLEVEL', 'DEBUG').upper()
logging.basicConfig(
    level=LOGLEVEL,
    format='%(levelname)s %(asctime)s\t%(filename)s:%(lineno)d\t%(funcName)s:\t%(message)s',
    datefmt='%H:%M:%S',
    # filename=f'{__file__}.log'
)

Log = logging.getLogger(__name__)

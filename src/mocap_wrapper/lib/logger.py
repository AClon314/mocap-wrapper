"""
Use env var `IS_JSON=1`/`LOG=d` to enable features.  
Log to stderr, Progress to stdout
"""
import os
import sys
import json
import logging
from numpy import isin
from tqdm import tqdm
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar, cast
_LOG_KEYS = ['LOG', 'LOGLEVEL', 'LOG_LEVEL']
_LOGLEVEL = [os.environ.get(k) for k in _LOG_KEYS]
_LOGLEVEL = [x for x in _LOGLEVEL if x is not None]
_LOGLEVEL = _LOGLEVEL[0].lower() if _LOGLEVEL else 'info'
_LOGLVLS = ['debug', 'info', 'warn', 'error', 'critical', 'fatal']
_LOGLVLS = {x[0]: x for x in _LOGLVLS}
LOG_LEVEL = _LOGLVLS.get(_LOGLEVEL[0], 'info')
LOG_LEVEL_INT = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
IS_DEBUG = LOG_LEVEL == 'debug'
IS_JSON = os.environ.get('IS_JSON', None)
_FMT = "{'log':'%(levelname)s','time':'%(asctime)s','msg':%(message)s}" if IS_JSON else '%(levelname)s %(asctime)s %(name)s:%(lineno)d\t%(message)s'
_DATEFMT = '%H:%M:%S'
_LEVEL_PREFIX = {
    logging.DEBUG: '🔍DEBUG',
    logging.INFO: '💬 INFO',
    logging.WARNING: '⚠️  WARN',
    logging.ERROR: '❌ERROR',
    logging.CRITICAL: '⛔⛔CRITICAL',
    logging.FATAL: '☠️FATAL',
}
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")


def copy_args(
    func: Callable[_PS, Any]
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """Decorator does nothing but returning the casted original function"""
    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)
    return return_func


async def run_1by1(coros: list[Coroutine], raise_if_none=True, raise_if_return0=True):
    results: list[Any] = []
    exception = None
    for coro in coros:
        Log.debug(f'{coro=}')
        try:
            if isinstance(coro, Coroutine):
                ret = await coro
            elif callable(coro):
                ret = coro()
            else:
                ret = coro

            if raise_if_none and ret is None:
                raise ValueError(f'{coro} returned None')
            if hasattr(ret, 'get_status') and callable(ret.get_status):
                returncode = ret.get_status()
                Log.debug(f'{returncode=}')
                if raise_if_return0 and returncode != 0:
                    raise RuntimeError(ret)
            results.append(ret)
        except Exception as e:
            exception = e
            Log.exception('', exc_info=e) if IS_DEBUG else None
            break
    return results, exception


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if IS_JSON:
            record.msg = repr(record.getMessage())
        else:
            record.levelname = _LEVEL_PREFIX.get(record.levelno, record.levelname)
        return super().format(record)


class TqdmJson(tqdm):
    def display(self, *args, **kwargs): print(self.get_json(), file=sys.stderr) if IS_JSON else super().display(*args, **kwargs)

    @copy_args(tqdm.__init__)
    def __init__(self, *args, **kwargs):
        if IS_JSON:
            kwargs.setdefault('mininterval', 1.0)
        self.id = id(self)
        super().__init__(*args, **kwargs)

    def get_json(self):
        fmt = self.format_dict if hasattr(self, 'format_dict') else {}
        rate: float = fmt.get('rate')   # type:ignore
        eta = int((self.total - self.n) / float(rate)) if rate else None
        fmt = {'time': float(f"{fmt.get('elapsed'):.1f}"), 'eta': eta, 'rate': rate, 'unit': fmt['unit']}
        obj = {
            'progress': self.id,
            'n': self.n,
            'total': self.total,
            **fmt,
            'msg': repr(self.desc)[1:-1],
        }
        obj = {k: v for k, v in obj.items() if v is not None and v != ''}
        return json.dumps(obj, ensure_ascii=False)


tqdm = TqdmJson


class TqdmStream(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg, file=sys.stdout)
        self.flush()


_HANDLER = TqdmStream()
_HANDLER.setFormatter(CustomFormatter(_FMT, datefmt=_DATEFMT))


def getLogger(name=__name__):
    if '❯' not in name:
        name = name.replace('.', '/') + '.py'
    Log = logging.getLogger(name)
    Log.setLevel(LOG_LEVEL.upper())
    Log.addHandler(_HANDLER)
    Log.propagate = False
    return Log


Log = getLogger(__name__)

if __name__ == '__main__':
    from time import sleep
    Log.debug('Hello, world!')
    TOTAL = 20
    for i in tqdm(range(2), desc="Outer Loop"):
        for j in tqdm(range(5), desc=f"Inner Loop {i}"):
            Log.info(f"Processing {i}-{j} \" ' ")
            sleep(0.2)

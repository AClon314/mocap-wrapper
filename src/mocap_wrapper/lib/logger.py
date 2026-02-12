"""
Use env var `IS_JSON=1`/`LOG=d` to enable features.
Log to stderr, Progress to stdout
"""

import os
import sys
import json
import logging
from tqdm import tqdm
from typing import Any, Callable, ParamSpec, TypeVar, cast

LOG = os.environ.get("LOG", "INFO").upper()
IS_DEBUG = os.environ.get("TERM_PROGRAM", None) or LOG == "DEBUG"
IS_JSON = os.environ.get("IS_JSON", None)
_FMT = (
    "{'log':'%(levelname)s','time':'%(asctime)s','msg':%(message)s}"
    if IS_JSON
    else "%(levelname)s %(asctime)s %(name)s:%(lineno)d\t%(message)s"
)
_DATEFMT = "%H:%M:%S"
_LEVEL_PREFIX = {
    logging.DEBUG: "🔍DEBUG",
    logging.INFO: "💬 INFO",
    logging.WARNING: "⚠️  WARN",
    logging.ERROR: "❌ERROR",
    logging.CRITICAL: "⛔⛔CRITICAL",
    logging.FATAL: "☠️FATAL",
}
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")


def is_debug(Log: logging.Logger):
    return Log.isEnabledFor(logging.DEBUG)


def copy_args(
    func: Callable[_PS, Any],
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """Decorator does nothing but returning the casted original function"""

    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)

    return return_func


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if IS_JSON:
            record.msg = repr(record.getMessage())
        else:
            record.levelname = _LEVEL_PREFIX.get(record.levelno, record.levelname)
        return super().format(record)


class TqdmJson(tqdm):
    def display(self, *args, **kwargs):
        (
            print(self.get_json(), file=sys.stderr)
            if IS_JSON
            else super().display(*args, **kwargs)
        )

    @copy_args(tqdm.__init__)
    def __init__(self, *args, **kwargs):
        if IS_JSON:
            kwargs.setdefault("mininterval", 1.0)
        self.id = id(self)
        super().__init__(*args, **kwargs)

    def get_json(self):
        fmt = self.format_dict if hasattr(self, "format_dict") else {}
        rate: float = fmt.get("rate")  # type:ignore
        eta = int((self.total - self.n) / float(rate)) if rate else None
        fmt = {
            "time": float(f"{fmt.get('elapsed'):.1f}"),
            "eta": eta,
            "rate": rate,
            "unit": fmt["unit"],
        }
        obj = {
            "progress": self.id,
            "n": self.n,
            "total": self.total,
            **fmt,
            "msg": repr(self.desc)[1:-1],
        }
        obj = {k: v for k, v in obj.items() if v is not None and v != ""}
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
    if "❯" not in name:
        name = name.replace(".", "/") + ".py"
    Log = logging.getLogger(name)
    Log.setLevel(logging.DEBUG if IS_DEBUG else LOG)
    Log.addHandler(_HANDLER)
    Log.propagate = False
    Log.log(Log.level, Log.level)
    return Log


Log = getLogger(__name__)

if __name__ == "__main__":
    from time import sleep

    Log.debug("Hello, world!")
    TOTAL = 20
    for i in tqdm(range(2), desc="Outer Loop"):
        for j in tqdm(range(5), desc=f"Inner Loop {i}"):
            Log.info(f"Processing {i}-{j} \" ' ")
            sleep(0.2)

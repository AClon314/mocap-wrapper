import os
from sys import platform
from pathlib import Path
from datetime import timedelta
from importlib.metadata import version as _version
from importlib.resources import path as _res_path
from typing import Literal, ParamSpec, TypeVar, Callable, Any, cast, get_args
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")
TYPE_RUNS = Literal['wilor', 'gvhmr']
RUNS = get_args(TYPE_RUNS)
DIR_SELF = os.path.dirname(os.path.abspath(__file__))
PACKAGE = __package__.split('.')[0] if __package__ else os.path.basename(DIR_SELF)
__version__ = _version(PACKAGE)
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'
TIMEOUT_SECONDS = 15      # seconds for next http request, to prevent being 403 blocked
TIMEOUT_MINUTE = timedelta(minutes=2).seconds
TIMEOUT_QUATER = timedelta(minutes=15).seconds
QRCODE = """
█▀▀▀▀▀█  ▀▀█▄ █ ▄ █▀▀▀▀▀█
█ ███ █ ▄▀██▄▄█▄█ █ ███ █
█ ▀▀▀ █ ▀▄█ ▀█▄ █ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄▀▄▀ █▄▀ ▀▀▀▀▀▀▀
▀█ ▄▄▀▀█▄▀█▄▄▀ █   ▄█▀▄
▀█▄██▀▀█▄▀▄ ▀ ▀█▄▄▄▄▄▄ ▀█
▄▀▄█▀▄▀█▄▀██▄ █▄▀ ▀█ ▀ █▀
█ ▀▀ ▀▀▄ ▀ ▄ ▀▀▀█ ▀▀ ▄██▀
▀   ▀ ▀▀█▄▀▄▄▀▄ █▀▀▀██▀▄▀
█▀▀▀▀▀█ █▄ ▀▄  ▄█ ▀ █ ▀ █
█ ███ █  █▀█▄▀ ▀███▀▀█▀█▄
█ ▀▀▀ █ ▄▀▄▄    █  ▀▄█▀ █
▀▀▀▀▀▀▀ ▀ ▀▀  ▀ ▀ ▀▀▀▀  ▀"""[1:]


def copy_args(
    func: Callable[_PS, Any]
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """Decorator does nothing but returning the casted original function"""
    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)
    return return_func


def res_path(pkg=__package__, module='pixi', file='pixi.toml'):
    if pkg is None:
        return Path(DIR_SELF, '..', module, file).resolve().absolute()
    else:
        pkg = pkg.split('.')[0]
        with _res_path(f'{pkg}.{module}', file) as P:
            return P.absolute()


def get_cmds(doc: str | None):
    cmds = doc.strip().splitlines() if doc else []
    cmds = [cmd.strip() for cmd in cmds]
    cmds = [cmd for cmd in cmds if cmd]
    return cmds


from .aria import *
from .config import *
from .data_viewer import *
from .FFmpeg import *
from .logger import *
from .pkg_mgr import *
from .process import *

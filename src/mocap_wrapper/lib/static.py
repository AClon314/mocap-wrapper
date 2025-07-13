'''
To prevent recursive import, this file can NOT import self modules!
'''
import os
from sys import platform
from pathlib import Path
from datetime import timedelta
from functools import cache, cached_property
from importlib.metadata import version as _version
from importlib.resources import path as _res_path
from types import ModuleType
from typing import ParamSpec, TypeVar, Callable, Literal, Any, get_args, cast
from huggingface_hub import HfApi
try:
    from mirror_cn import is_need_mirror
except ImportError:
    def is_need_mirror() -> bool: return bool(os.environ.get('IS_MIRROR', ''))
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")
TYPE_RUNS = Literal['wilor', 'gvhmr', 'dynhamr']
RUNS: tuple[TYPE_RUNS] = get_args(TYPE_RUNS)
RUNS_REPO: dict[TYPE_RUNS, str] = {
    'wilor': 'WiLoR-mini',
    'gvhmr': 'GVHMR',
    'dynhamr': 'Dyn-HaMR',
}
CONCURRENT = int(os.environ.get('CONCURRENT', 3))
DIR_SELF = os.path.dirname(os.path.abspath(__file__))
PACKAGE = __package__.split('.')[0] if __package__ else os.path.basename(DIR_SELF)
VERSION = _version(PACKAGE)
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


def remove_if_p(path: str | Path):
    """remove file if progress is successful"""
    os.remove(path) if os.path.exists(path) else None


def copy_args(
    func: Callable[_PS, Any]
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """Decorator does nothing but returning the casted original function"""
    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)
    return return_func


def res_path(pkg=__package__, module='pixi', file='pixi.toml'):
    if pkg is None:
        return Path(DIR_SELF, '..', module, file).resolve()
    else:
        pkg = pkg.split('.')[0]
        with _res_path(f'{pkg}.{module}', file) as P:
            return P.absolute()


def get_cmds(doc: str | None):
    cmds = doc.strip().splitlines() if doc else []
    cmds = [cmd.strip() for cmd in cmds]
    cmds = [cmd for cmd in cmds if cmd]
    return cmds


class _Env:
    '''Global variables and properties for the package.'''
    # HUGFACE = 'https://{domain}/{owner_repo}/resolve/main/'
    @cached_property
    def is_mirror(cls): return is_need_mirror()
    @cached_property
    def HF(cls): return HfApi(endpoint=cls.domain_hf)

    @cached_property
    def domain_hf(cls):
        DOMAIN_HF = 'hf-mirror.com' if cls.is_mirror else 'huggingface.co'
        DOMAIN_HF = 'https://' + DOMAIN_HF
        return DOMAIN_HF

    @cache
    def mod(cls, Dir: Literal['install', 'lib', 'runs']):
        '''lru_cache! Example: `Env.mod('install')['gvhmr']()`'''
        import importlib
        files = os.listdir(Path(__file__, '..', '..', Dir).resolve())
        pys = [f[:-3] for f in files if f.endswith('.py')]
        mods: dict[str, Callable[..., ModuleType]] = {}
        for p in pys:
            def _mod(): return importlib.import_module(f'.{Dir}.{p}', package=__package__)
            mods[p] = _mod
        return mods


Env = _Env()

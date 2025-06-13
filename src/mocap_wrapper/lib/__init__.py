import os
import toml
from pathlib import Path
from mocap_wrapper.lib.process import DIR
from platformdirs import user_config_path
from importlib.metadata import version as _version
from importlib.resources import path as _res_path
from typing import Literal, ParamSpec, TypeVar, Callable, Any, TypedDict, Union, Unpack, cast, get_args
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")
TYPE_RUNS = Literal['wilor', 'gvhmr']
RUNS = get_args(TYPE_RUNS)
DIR_SELF = os.path.dirname(os.path.abspath(__file__))
PACKAGE = __package__ if __package__ else os.path.basename(DIR_SELF)
__version__ = _version(PACKAGE)
TYPE_KEYS_CONFIG = Union[Literal['search_dir'], str]  # I think python type system is not mature enough to handle this
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


def copy_kwargs(
    kwargs_call: Callable[_PS, Any]
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """Decorator does nothing but returning the casted original function"""
    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)
    return return_func


def path_expand(path: str | Path, absolute=True):
    path = os.path.expandvars(os.path.expanduser(path))
    if absolute:
        path = os.path.abspath(path)
    return path


def res_path(pkg=__package__, module='requirements', file='requirements.txt'):
    if __package__ is None:
        return os.path.join(DIR_SELF, module, file)
    else:
        with _res_path(f'{pkg}.{module}', file) as P:
            return P.absolute()


class TYPE_CONFIG(TypedDict, total=False):
    search_dir: str
    gvhmr: bool
    wilor: bool


class Config(dict):
    default: TYPE_CONFIG = {
        'search_dir': path_expand(DIR),
        'gvhmr': False,
        'wilor': False,
    }

    def __init__(self, /, *args: TYPE_CONFIG, file: Path | str = "config.toml", **kwargs: Unpack[TYPE_CONFIG]) -> None:
        """

        This will sync to config file:
        ```python
        CONFIG['search_dir'] = '.'
        ```
        """
        self.update(self.default)
        super().__init__(*args, **kwargs)
        self.path = user_config_path(appname=PACKAGE, ensure_exists=True).joinpath(file)
        if os.path.exists(self.path):
            config = toml.load(self.path)
            self.update(config)
            # except toml.TomlDecodeError as e:
            #     # TODO: auto recover from this exception
            #     Log.warning(f"Load failed {self.path}: {e}")
        self.dump()

    def dump(self, file: Path | str = '') -> None:
        """将self dict保存到TOML文件"""
        if not file:
            file = self.path
        with open(file, "w") as f:
            toml.dump(dict(self), f)    # dict() for not recursive

    def __getitem__(self, key: TYPE_KEYS_CONFIG) -> Any:
        return super().__getitem__(key)

    def __setitem__(self, key: TYPE_KEYS_CONFIG, value: Any) -> None:
        super().__setitem__(key, value)
        if key in self.default.keys():
            self.dump()


CONFIG = Config()

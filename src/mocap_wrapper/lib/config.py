import toml
from pathlib import Path
from platformdirs import user_config_path
from mirror_cn import is_need_mirror
from . import PACKAGE
from typing import Any, Literal, TypedDict, Union, Unpack
TYPE_KEYS_CONFIG = Union[Literal['search_dir'], str]  # I think python type system is not mature enough to handle this


class TYPE_CONFIG(TypedDict, total=False):
    is_mirror: bool
    search_dir: str
    gvhmr: bool
    wilor: bool


class Config(dict):
    default: TYPE_CONFIG = {
        'is_mirror': is_need_mirror(),
        'search_dir': '.',
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
        if Path(self.path).exists():
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

    def __getitem__(self, key: TYPE_KEYS_CONFIG):
        return super().__getitem__(key)

    def __setitem__(self, key: TYPE_KEYS_CONFIG, value: Any) -> None:
        super().__setitem__(key, value)
        if key in self.default.keys():
            self.dump()


CONFIG = Config()
DIR = CONFIG['search_dir']
IS_MIRROR = CONFIG['is_mirror']

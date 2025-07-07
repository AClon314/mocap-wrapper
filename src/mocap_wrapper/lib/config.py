import toml
from pathlib import Path
from collections import UserDict
from functools import cached_property
from platformdirs import user_config_path
from . import PACKAGE, RUNS_REMAP, TYPE_RUNS
try:
    from mirror_cn import is_need_mirror
except ImportError:
    def is_need_mirror(): return False
from typing import Any, Literal, Union
TYPE_CONFIG_KEYS = Union[Literal['search_dir'], TYPE_RUNS, str]  # I think python type system is not mature enough to handle this


class Config(UserDict):
    @cached_property
    def is_mirror(self): return is_need_mirror()

    @property
    def default(self):
        SEARCH_DIR = self.data.get('search_dir', str(Path('.').absolute()))
        return {
            'search_dir': SEARCH_DIR,
            'gvhmr': str(Path(SEARCH_DIR, RUNS_REMAP['gvhmr'])),
            'wilor': str(Path(SEARCH_DIR, RUNS_REMAP['wilor'])),
        }

    def __init__(self, dic: dict = {}, file: Path | str = "config.toml"):
        """
        This will sync to config file:
        ```python
        CONFIG['search_dir'] = '.'
        ```
        """
        self.path = user_config_path(appname=PACKAGE, ensure_exists=True).joinpath(file)
        if Path(self.path).exists():
            config = toml.load(self.path)
            dic.update(config)
            # except toml.TomlDecodeError as e:
            #     # TODO: auto recover from this exception
            #     Log.warning(f"Load failed {self.path}: {e}")
        super().__init__(**dic)
        super().__init__(**{**self.default, **dic})

    def dump(self, file: Path | str = '') -> None:
        """将self dict保存到TOML文件"""
        if not file:
            file = self.path
        with open(file, "w") as f:
            toml.dump(self.data, f)

    def __getitem__(self, key: TYPE_CONFIG_KEYS):
        return super().__getitem__(key)

    def __setitem__(self, key: TYPE_CONFIG_KEYS, value: Any) -> None:
        super().__setitem__(key, value)
        if key in self.default.keys():
            self.dump()

    def __delitem__(self, key: Any):
        super().__delitem__(key)
        self.data[key] = self.default[key]


CONFIG = Config()

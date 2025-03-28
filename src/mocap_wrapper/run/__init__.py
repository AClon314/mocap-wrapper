import os
import sys
import toml
from platformdirs import user_config_path
from typing import Literal
MAPPING = {
    'gvhmr': 'GVHMR',
}


def chdir_gitRepo(mod: Literal['gvhmr']):
    config_path = user_config_path(appname='mocap_wrapper', ensure_exists=True).joinpath('config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        dst = os.path.join(config['search_dir'], MAPPING[mod])
        sys.path.append(dst)
        os.chdir(dst)
    else:
        raise FileNotFoundError(f'config.toml not found in {config_path}')

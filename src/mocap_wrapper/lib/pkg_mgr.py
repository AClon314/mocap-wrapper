"""
- system package manager(apt/dnf/brew/winget)
- python package manager(pixi)
"""
import os
import json
import asyncio
# from sys import path as PATH
from shutil import which, copy as cp
from . import *
from . import TIMEOUT_MINUTE, TIMEOUT_QUATER, DIR
from typing import Literal, Dict, Tuple, Union, get_args
Log = getLogger(__name__)
ENV = 'mocap'
BIN_PKG = {
    'aria2c': {
        None: 'aria2',
        'winget': 'aria2.aria2',
    },
    '7z': {
        None: '7zip',
        'winget': '7z',
        'dnf': '7z',
        'brew': 'p7zip',
        'apt': 'p7zip-full p7zip-rar',
    },
    'git': {
        None: 'git',
        'winget': 'Git.Git',
    },
    'ffmpeg': {None: 'ffmpeg'},  # TODO delayable
}
BINS = [_bin for _bin in BIN_PKG.keys()]
TYPE_SHELLS = Literal['zsh', 'bash', 'ps']
SHELLS: Tuple[TYPE_SHELLS] = get_args(TYPE_SHELLS)
TYPE_PY_MGRS = Literal['mamba', 'conda', 'pip']
PY_MGRS: Tuple[TYPE_PY_MGRS] = get_args(TYPE_PY_MGRS)
SU = '' if is_win or os.geteuid() == 0 else 'sudo '
TYPE_PKG_ACT = Union[None, Literal['install', 'remove', 'update']]
PKG_MGRS: Dict[str, Dict[TYPE_PKG_ACT, str]] = {
    'winget': {
        # windows # https://github.com/microsoft/winget-pkgs , `t` search file in `manifest`
        'update': 'upgrade --all --silent',
        'install': 'install --accept-package-agreements',
        'remove': 'uninstall'
    },
    'apt': {
        # debian, ubuntu # https://packages.debian.org/search?keywords=
        'update': 'update -y',
        'install': 'install -y --ignore-missing',
        'remove': 'remove'
    },
    'pacman': {
        # arch # https://archlinux.org/packages/?repo=Extra&q=
        'update': '-Sy',
        'install': '-S --noconfirm',
        'remove': '-R'
    },
    'dnf': {
        # fedora # https://pkgs.org/search/?q=
        'update': 'check-update -y',
        'install': 'install -y --skip-unavailable',
        'remove': 'remove'
    },
    'zypper': {
        # suse # https://packagehub.suse.com/search/?q=
        'update': 'refresh',
        'install': 'install -n --ignore-unknown',
        'remove': 'remove'
    },
    'emerge': {
        # gentoo # https://packages.gentoo.org/packages/search?q=
        'update': '--sync',
        'install': '--ask=n --keep-going',
        'remove': '--unmerge'
    },
    'brew': {
        # macos, linux # https://formulae.brew.sh/formula/
        'update': 'update -y',
        'install': 'install -y',
        'remove': 'remove'
    },
}
PKG_MGRS['yum'] = PKG_MGRS['dnf']   # rhel
_pkg_mgrs_keys = set(PKG_MGRS.keys())
for _b, _p in BIN_PKG.items():
    default = _p[None]
    lack = _pkg_mgrs_keys - set(_p.keys())
    for _mgr in lack:
        BIN_PKG[_b][_mgr] = default


def remove_if_p(path: str | Path):
    """remove file if progress is successful"""
    os.remove(path) if os.path.exists(path) else None


def get_shell():
    for s in SHELLS:
        if which(s):
            return s


def get_pkg_mgr():
    for mgr in PKG_MGRS.keys():
        if which(mgr):
            return mgr
    raise FileNotFoundError(f"Not found any of {PKG_MGRS.keys()}")


async def pkg(action: TYPE_PKG_ACT, package: list[str] = [], **kwargs):
    p = f"{SU}{PKG_MGR} {PKG_MGRS[PKG_MGR][action]} {' '.join(package)}"
    return run_tail(p, **kwargs)


async def i_pkgs(**kwargs):
    # dnf/yum will update before each install
    if PKG_MGR not in ['dnf', 'yum']:
        await pkg('update', **kwargs)
    pkgs = [p[PKG_MGR] for p in BIN_PKG.values()]
    await pkg('install', pkgs, **kwargs)
    return True


async def get_envs(manager: Literal['mamba', 'conda'] = 'mamba', **kwargs):
    """
    Args:
        manager (str): 'mamba', 'conda'
        kwargs (dict): `subprocess.Popen()` args

    Returns: 
        env (dict): eg: {'base': '~/miniforge3'}
        now (str): currently env name like 'base'
    """
    tasks = [
        echo(f'{manager} env list --json', **kwargs),
        echo(f'{manager} info --json', **kwargs)
    ]
    p_env, p_info = await asyncio.gather(*tasks)
    _envs: list = json.loads(p_env[1])['envs']
    env = {os.path.split(v)[-1]: v for v in _envs}
    _info = json.loads(p_info[1])
    _prefix = ''
    if manager.endswith('mamba'):
        _prefix = 'miniforge3'
        now = _info['environment']
    elif manager.endswith('conda'):
        _prefix = 'miniconda3'
        now = _info['active_prefix_name']
    else:
        raise ValueError(f"Unsupported manager: {manager}. Use 'mamba' or 'conda'.")
    env['base'] = env[_prefix]
    env.pop(_prefix)
    Log.debug(f'{env=}')
    return env, now


def git_pull(**kwargs):
    """```sh
    git fetch --all
    git pull
    git submodule update --init --recursive
    ```"""
    kwargs.setdefault('timeout', TIMEOUT_QUATER)
    p = run_tail('git fetch --all', **kwargs)
    p = run_tail('git pull', **kwargs)
    p = run_tail('git submodule update --init --recursive', **kwargs)
    return p


def clean(**kwargs):
    kwargs.setdefault('timeout', TIMEOUT_MINUTE)
    cmds = [
        'pixi cache clean',
        'uv cache clean',
    ]
    for cmd in cmds:
        run_tail(cmd, **kwargs)


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()

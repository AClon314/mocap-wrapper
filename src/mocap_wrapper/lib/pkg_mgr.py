"""
- system package manager(apt/dnf/brew/winget)
- python package manager(pixi)
"""
import os
import shutil
from pathlib import Path
# from sys import path as PATH
from . import TIMEOUT_MINUTE, TIMEOUT_QUATER, is_win, is_linux, is_mac, get_cmds
from .logger import getLogger
from .process import run_tail
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
        'apt': 'p7zip-full',    # TODO: p7zip-rar
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
SU = '' if is_win or os.geteuid() == 0 else 'sudo'
TYPE_PKG_ACT = Union[None, Literal['install', 'remove', 'update']]
PKG_MGRS: Dict[str, Dict[TYPE_PKG_ACT, str | list]] = {
    'winget': {
        # windows # https://github.com/microsoft/winget-pkgs , `t` search file in `manifest`
        'update': 'upgrade --all --silent'.split(),
        'install': 'install --accept-package-agreements'.split(),
        'remove': 'uninstall'
    },
    'apt': {
        # debian, ubuntu # https://packages.debian.org/search?keywords=
        'update': 'update -y'.split(),
        'install': 'install -y --ignore-missing'.split(),
        'remove': 'remove'
    },
    'pacman': {
        # arch # https://archlinux.org/packages/?repo=Extra&q=
        'update': '-Sy',
        'install': '-S --noconfirm'.split(),
        'remove': '-R'
    },
    'dnf': {
        # fedora # https://pkgs.org/search/?q=
        'update': 'check-update -y'.split(),
        'install': 'install -y --skip-unavailable'.split(),
        'remove': 'remove'
    },
    'zypper': {
        # suse # https://packagehub.suse.com/search/?q=
        'update': 'refresh',
        'install': 'install -n --ignore-unknown'.split(),
        'remove': 'remove'
    },
    'emerge': {
        # gentoo # https://packages.gentoo.org/packages/search?q=
        'update': '--sync',
        'install': '--ask=n --keep-going'.split(),
        'remove': '--unmerge'
    },
    'brew': {
        # macos, linux # https://formulae.brew.sh/formula/
        'update': 'update -y'.split(),
        'install': 'install -y'.split(),
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
        if shutil.which(s):
            return s


def get_pkg_mgr():
    for mgr in PKG_MGRS.keys():
        if shutil.which(mgr):
            return mgr
    raise FileNotFoundError(f"Not found any of {PKG_MGRS.keys()}")


async def pkg(action: TYPE_PKG_ACT, package: list[str] = [], **kwargs):
    act = PKG_MGRS[PKG_MGR][action]
    act = [act] if isinstance(act, str) else act
    p = ([SU] if SU else []) + [PKG_MGR] + act + package
    return run_tail(p, **kwargs)


async def i_pkgs(**kwargs):
    # dnf/yum will update before each install
    if PKG_MGR not in ['dnf', 'yum']:
        await pkg('update', **kwargs)
    pkgs = [p[PKG_MGR] for p in BIN_PKG.values()]
    await pkg('install', pkgs, **kwargs)
    return True


async def git_pull(**kwargs):
    """
git fetch --all  
git pull  
git submodule update --init --recursive
    """
    timeout = kwargs.pop('timeout', TIMEOUT_QUATER)
    cmds = get_cmds(git_pull.__doc__)
    for cmd in cmds:
        await run_tail(cmd, timeout=timeout, **kwargs).Await(timeout=timeout)


def clean(**kwargs):
    '''
pixi cache clean  
uv cache clean
    '''
    kwargs.setdefault('timeout', TIMEOUT_MINUTE)
    cmds = get_cmds(clean.__doc__)
    for cmd in cmds:
        run_tail(cmd, **kwargs)


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()

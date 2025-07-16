"""
use pixi as user space package manager
"""
import shutil
from .static import TIMEOUT_MINUTE, TIMEOUT_QUATER, Env, get_cmds, is_win
from .logger import getLogger
from .process import run_tail
from typing import Literal, get_args
Log = getLogger(__name__)
TYPE_BINS = Literal['aria2c', '7z', 'git', 'ffmpeg']
BINS = get_args(TYPE_BINS)
BIN_PKG = {v: v for v in get_args(TYPE_BINS)}
BIN_PKG: dict[TYPE_BINS, str] = {
    **BIN_PKG,
    'aria2c': 'aria2',  # use winget to install aria2.aria2
    '7z': '7zip' if is_win else 'p7zip',
}


async def i_pkgs(*bin: TYPE_BINS | str, bin_pkg: dict[str, str] = {}):
    '''pixi global install bin'''
    bins: list[str] = list(bin if bin and bin[0] else []) + list(bin_pkg.keys()) or list(BINS)  # when bin[0]==''
    bin_path = {p: shutil.which(p) for p in bins}
    missing_bins = [p for p, v in bin_path.items() if not v]
    pkgs = [BIN_PKG[b] for b in missing_bins if b in BINS] + [bin_pkg[b] for b in missing_bins if b in bin_pkg.keys()]  # type: ignore
    Log.debug(f'{locals()=}')
    if not missing_bins:
        return
    if is_win and 'aria2' in pkgs:
        pkgs.pop(0)
        cmd_install = 'winget install --accept-package-agreements aria2.aria2'
        if Env.is_mirror:
            cmds = [
                'winget source remove winget',
                'winget source add winget https://mirrors.ustc.edu.cn/winget-source --trust-level trusted',
                cmd_install,
                'winget source reset winget'
            ]
            for cmd in cmds:
                _p = await run_tail(cmd).Await(TIMEOUT_MINUTE)
                if _p.get_status() != 0:
                    Log.error(cmd)
                    break
        else:
            _p = await run_tail(cmd_install).Await(TIMEOUT_MINUTE)
    cmd = 'pixi global install'.split() + pkgs
    p = await run_tail(cmd).Await(TIMEOUT_QUATER)
    return p


def clean(**kwargs):
    '''
pixi cache clean  
uv cache clean
    '''
    kwargs.setdefault('timeout', TIMEOUT_MINUTE)
    cmds = get_cmds(clean.__doc__)
    for cmd in cmds:
        run_tail(cmd, **kwargs)

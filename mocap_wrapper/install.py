import aria2p
import subprocess as sp
import asyncio as aio
import os
from sys import platform
from shutil import which
from time import time
from datetime import timedelta
from mocap_wrapper.logger import Log
from types import SimpleNamespace
from typing import Dict, Literal, Union
# editable variables:
PACKAGES = [('aria2', 'aria2c'), 'git', 'unzip']
ARIA_PORTS = [6800, 16800]
ARIA_OPTIONS = {
    "dir": "~",
    "max-connection-per-server": "5",
    "split": "5",
    "min-split-size": "1M",
    "continue": "true",
}
PKG_MGR = None

BINS = [p[1] if isinstance(p, tuple) else p for p in PACKAGES]
PACKAGES = [p[0] if isinstance(p, tuple) else p for p in PACKAGES]
aria: aria2p.API = None
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'
su = '' if is_win or os.geteuid() == 0 else 'sudo '
Type_pkg_act = Union[None, Literal['install', 'remove', 'update']]
pkg_mgrs: Dict[str, Dict[Type_pkg_act, str]] = {
    'winget': {
        # windows
        'update': 'upgrade --all',
        'install': 'install',
        'remove': 'uninstall'
    },
    'apt': {
        # debian
        'update': 'update',
        'install': 'install',
        'remove': 'remove'
    },
    'pacman': {
        # arch
        'update': '-Sy',
        'install': '-S',
        'remove': '-R'
    },
    'dnf': {
        # fedora
        'update': 'check-update',
        'install': 'install',
        'remove': 'remove'
    },
    'zypper': {
        # suse
        'update': 'refresh',
        'install': 'install',
        'remove': 'remove'
    },
    'emerge': {
        # gentoo
        'update': '--sync',
        'install': '',
        'remove': '--unmerge'
    },
}
pkg_mgrs['brew'] = pkg_mgrs['apt']  # macos
pkg_mgrs['yum'] = pkg_mgrs['dnf']   # rhel


def Popen(cmd='aria2c --enable-rpc --rpc-listen-port=6800',
          wait=True, Raise=True, dry_run=False, **kwargs):
    """default: run cmd in background"""
    Log.info(cmd)
    if dry_run:
        return
    p = sp.Popen(cmd, shell=True, **kwargs)
    if wait:
        p.wait()
    if p.returncode != 0:
        if Raise:
            raise Exception(f"Failed: {cmd}")
        else:
            Log.error(f"Failed: {cmd}")
    return p


def Exec(cmd, timeout=10.0, Print=True, dry_run=False, **kwargs) -> Union[str, bytes, None]:
    Log.info(cmd)
    if dry_run:
        return
    s = sp.check_output(cmd, shell=True, timeout=timeout, **kwargs).decode().strip()
    if Print:
        print(s)
    return s


def version(cmd: str):
    """use `cmd --version` to check if a program is installed"""
    cmd += ' --version'
    p = Popen(cmd)
    return p.returncode == 0


def get_pkg_mgr():
    global PKG_MGR
    for mgr in pkg_mgrs.keys():
        if version(mgr):
            PKG_MGR = mgr
            break
    return PKG_MGR


def pkg(action: Type_pkg_act, package: list[str], **kwargs):
    if not PKG_MGR:
        get_pkg_mgr()
    p = cmd = f"{su}{PKG_MGR} {pkg_mgrs[action]} {' '.join(package)}"
    p = Popen(cmd, wait=True, **kwargs)
    return p


def try_aria_port():
    for port in ARIA_PORTS:
        try:
            aria2 = aria2p.API(
                aria2p.Client(
                    host="http://localhost",
                    port=port,
                    secret=""
                )
            )
            aria2.get_stats()
            return aria2
        except Exception as e:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
    return None


def i_pkgs(**kwargs):
    """aria2"""
    if is_linux:
        cmd = [
            su + "apt-get update",
            su + f"apt-get install {' '.join(PACKAGES)} -y"
        ]
        for c in cmd:
            Popen(c, **kwargs)
    elif is_win:
        ...
    elif is_mac:
        ...
    return True


async def download(url: str, options=ARIA_OPTIONS,
                   duration=1, max_eta=timedelta(minutes=30).total_seconds(),
                   dry_run=False):
    """check if download is complete every `duration` seconds"""
    # start = time()
    d = SimpleNamespace()
    d.dir = '~'
    Log.info(f"{url} -> {d.dir}")
    if dry_run:
        return d
    d = aria.add_uris([url], options=options)
    if d.eta >= timedelta.max:
        Log.warning(f"No ETA for {url}")
    while True:
        await aio.sleep(duration)
        if d.is_complete():
            break
    return d


async def i_mamba(**kwargs):
    url = "https://github.com/conda-forge/miniforge/releases/latest/download/"
    setup = ''
    if is_linux or is_mac:
        setup = "echo Miniforge3-$(uname)-$(uname -m).sh"
        setup = Exec(setup, **kwargs)
    elif is_win:
        setup = "Miniforge3-Windows-x86_64.exe"
    else:
        raise Exception("Unsupported platform")
    url += setup
    d = await download(url, **kwargs)
    setup = d.dir + '/' + setup
    p = None
    if is_win:
        p = Popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
    else:
        p = Popen(f'bash "{setup}" -b', **kwargs)
    return p


def env_list(mgr='mamba', **kwargs):
    """return a list of conda envs, with current env at the first"""
    s = Exec(f'{mgr} env list', **kwargs)
    s = [l.split()[0] for l in s.split('\n') if l and not l.startswith('#')]
    now = os.getenv('CONDA_DEFAULT_ENV')
    if now in s:
        s.remove(now)
        s.insert(0, now)
    return s


def requirements_to_list(requirements_txt='requirements.txt'):
    with open(requirements_txt) as f:
        return f.read().splitlines()


def mamba(*pkgs: str, env: str = None, python: str = None,
          requirements_txt='requirements.txt', **kwargs):
    """By default do 3 things:
    - create if no exist
    - activate env  
    - install from `...` and `requirements.txt`

    `**kwargs` for `subprocess.Popen(...)`
    """
    mgr = 'mamba'
    envs = env_list(mgr, **kwargs)
    p = None
    if env in envs:
        p = Popen(f"{mgr} activate {env}", **kwargs)
    else:
        p = Popen(f"{mgr} create -y -n {env} python={python}", **kwargs)

    if requirements_txt:
        pkgs += requirements_to_list(requirements_txt)
    return p


def i_gvhmr(dir='~', **kwargs):
    os.chdir(os.path.expanduser(dir))
    p = Popen('git clone https://github.com/zju3dv/GVHMR --recursive', **kwargs)
    os.chdir('GVHMR')
    cmd = """conda create -y -n gvhmr python=3.10
conda activate gvhmr
pip install -r requirements.txt
pip install -e .
# to install gvhmr in other repo as editable, try adding "python.analysis.extraPaths": ["path/to/your/package"] to settings.json

# DPVO
cd third-party/DPVO
wget https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
unzip eigen-3.4.0.zip -d thirdparty && rm -rf eigen-3.4.0.zip
pip install torch-scatter -f "https://data.pyg.org/whl/torch-2.3.0+cu121.html"
pip install numba pypose
export CUDA_HOME=/usr/local/cuda-12.1/
export PATH=$PATH:/usr/local/cuda-12.1/bin/
pip install -e ."""
    p = mamba(env='gvhmr', python='3.10', **kwargs)


def check_install(**kwargs):
    pkgs = [which(p) for p in BINS]
    Log.debug(pkgs)
    if any(p is None for p in pkgs):
        i_pkgs()

    aria = try_aria_port()
    if aria is None:
        # try to start aria2c
        Popen(**kwargs)
        aria = try_aria_port()
        if aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(aria)

    p = which('mamba')
    Log.debug(p)
    if not p:
        aio.run(i_mamba(**kwargs))

    i_gvhmr(**kwargs)


if __name__ == '__main__':
    p = mamba(env='gvhmr', python='3.10')

    # check_install(dry_run=True)

import aria2p
import subprocess as sp
import asyncio as aio
import os
from rich import print
from rich.progress import Progress
from sys import platform
from shutil import which
from time import sleep, time
from datetime import timedelta
from regex import sub
from mocap_wrapper.logger import getLog
from types import SimpleNamespace
from typing import Dict, Literal, Union, get_args, overload
Log = getLog(__name__)

ARIA_PORTS = [6800, 16800]
OPT = {
    'dir': os.path.expanduser('~'),
    # 'out': 'filename',
    'continue': True,
    'split': 5,
    'max_connection_per_server': 5,
    'min_split_size': 20  # don't split if file size < 40M
}
PACKAGES = [('aria2', 'aria2c'), 'git', 'unzip']
BINS = [p[1] if isinstance(p, tuple) else p for p in PACKAGES]
PACKAGES = [p[0] if isinstance(p, tuple) else p for p in PACKAGES]
TYPE_SHELLS = Literal['zsh', 'bash', 'ps', 'cmd']
SHELLS = get_args(TYPE_SHELLS)
PY_MGR = 'mamba'
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'
SU = '' if is_win or os.geteuid() == 0 else 'sudo '
TYPE_PKG_ACT = Union[None, Literal['install', 'remove', 'update']]
PKG_MGRS: Dict[str, Dict[TYPE_PKG_ACT, str]] = {
    'winget': {
        # windows
        'update': 'upgrade --all --silent',
        'install': 'install --silent',
        'remove': 'uninstall'
    },
    'apt': {
        # debian
        'update': 'update -y',
        'install': 'install -y',
        'remove': 'remove'
    },
    'pacman': {
        # arch
        'update': '-Sy',
        'install': '-S --noconfirm',
        'remove': '-R'
    },
    'dnf': {
        # fedora
        'update': 'check-update -y',
        'install': 'install -y',
        'remove': 'remove'
    },
    'zypper': {
        # suse
        'update': 'refresh',
        'install': 'install -n',
        'remove': 'remove'
    },
    'emerge': {
        # gentoo
        'update': '--sync',
        'install': '--ask=n',
        'remove': '--unmerge'
    },
}
PKG_MGRS['brew'] = PKG_MGRS['apt']  # macos
PKG_MGRS['yum'] = PKG_MGRS['dnf']   # rhel


def Popen(cmd='aria2c --enable-rpc --rpc-listen-port=6800',
          timeout=300., Raise=True, dry_run=False, **kwargs):
    """Used on long running commands
    set `timeout` to -1 to run in background
    """
    Log.info(cmd)
    if dry_run:
        return
    p = sp.Popen(cmd, shell=True, **kwargs)
    if timeout is None or timeout >= 0:
        p.wait(timeout=timeout)
        if p.returncode != 0:
            if Raise:
                raise Exception(f"Failed: {cmd}")
            else:
                Log.error(f"Failed: {cmd}")
    return p


def Exec(cmd, timeout=10.0, Print=True, **kwargs) -> Union[str, bytes, None]:
    """Only used on instantly returning commands"""
    Log.info(cmd)
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
    MGR = None
    for mgr in PKG_MGRS.keys():
        if which(mgr):
            MGR = mgr
            break
    return MGR


def pkg(action: TYPE_PKG_ACT, package: list[str], **kwargs):
    p = f"{SU}{PKG_MGR} {PKG_MGRS[action]} {' '.join(package)}"
    p = Popen(p, timeout=True, **kwargs)
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
    pkg('update', **kwargs)
    pkg('install', PACKAGES, **kwargs)
    return True


def rich_finish(task: int):
    P.update(task, completed=100)
    P.start_task(task)


async def download(url: str, duration=0.5, dry_run=False, **kwargs: aria2p.Options):
    """check if download is complete every `duration` seconds

    `**kwargs` for `aria2p.API.add_uris(...)`:
    - `dir`: download directory
    - `out`: output filename
    - `max-connection-per-server`: `-x`
    - `split`: `-s`
    """
    # start = time()
    options = {**OPT, **kwargs}
    max_speed = 0

    if dry_run:
        d = SimpleNamespace()
        d.dir = options['dir']
        return d

    d = aria.add_uris([url], options=options)
    await aio.sleep(1.0)
    d = aria.get_download(d.gid)
    url = d.files[0].uris[0]['uri']
    filename = os.path.basename(url)
    d.path = path = os.path.join(d.dir, filename)
    if d.is_complete:
        Log.info(f"{d.path} already downloaded")
        return d

    has_eta = d.eta < timedelta.max
    Log.warning(f"No ETA for {url}") if not has_eta else None

    task = P.add_task(f"⬇️ Download {filename}", total=d.total_length, start=True)
    Log.debug(f"{d.__dict__}")
    while not d.is_complete:
        await aio.sleep(duration)
        d = aria.get_download(d.gid)
        P.update(task, completed=d.completed_length)
    d.path = path
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
    d = await download(url)
    setup = d.dir + '/' + setup
    p = None
    if is_win:
        p = Popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
    else:
        p = Popen(f'bash "{setup}" -b', **kwargs)
    return p


def get_envs(manager='mamba', **kwargs):
    """return a list of conda envs, with current env at the first"""
    s = Exec(f'{manager} env list', **kwargs)
    s = [l.split()[0] for l in s.split('\n') if l and not l.startswith('#')]
    now = os.getenv('CONDA_DEFAULT_ENV')
    if now in s:
        s.remove(now)
        s.insert(0, now)
    return s


def get_shell():
    SHELL = None
    for s in SHELLS:
        if which(s):
            SHELL = s
            break
    return SHELL


def mamba(cmd: str = None, env: str = None, python: str = None,
          txt='requirements.txt', *pkgs: str, **kwargs):
    """By default do 2 things:
    1. create env if no exist
    2. install from `pkgs` and `requirements.txt`
    - if `cmd` then, run `cmd` in the env

    `**kwargs` for `subprocess.Popen(...)`
    """
    failed = []
    envs = get_envs(PY_MGR)
    pkgs = list(pkgs)
    python = f'python={python}' if python else ''
    if env and env not in envs:
        p = Popen(f"{PY_MGR} create -y -n {env} {python}", **kwargs)
        failed.append(p) if p.returncode != 0 else None

    if txt and os.path.exists(txt):
        txt = '--file ' + txt
    else:
        Log.warning(f"{txt} not found requirements.txt")
        txt = ''
    if pkgs or txt:
        p = Popen(f"{PY_MGR} install -y -n {env} {txt} {' '.join(pkgs)}", **kwargs)
        failed.append(p) if p.returncode != 0 else None

    if cmd:
        cmd = sub(r"'(['\"])", r"\\\1", cmd)
        if is_win:
            _c = '/c'
        else:
            _c = '-c'
        cmd = f"{PY_MGR} run -n {env} {SHELL} {_c} '{cmd}'"
        p = Popen(cmd, **kwargs)
        failed.append(p) if p.returncode != 0 else None

    return failed


class ExistsPathList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().insert(0, os.getcwd())

    def append(self, object):
        if os.path.exists(object):
            super().append(object)
        else:
            Log.warning(f"{object} not exists")

    @overload
    def chdir(self, path: str) -> None: ...

    @overload
    def chdir(self, index: int) -> None: ...

    def chdir(self, arg):
        if isinstance(arg, int):
            os.chdir(self[arg])
        else:
            self.append(arg)
            os.chdir(arg)

    def pushd(self, path: str):
        self.chdir(path)

    def popd(self) -> str:
        p = self.pop()
        os.chdir(p)
        return p


async def i_gvhmr(dir='~', **kwargs):
    env = 'gvhmr'
    d = ExistsPathList()
    d.chdir(os.path.expanduser(dir))
    p = Popen('git clone https://github.com/zju3dv/GVHMR --recursive', **kwargs)
    d.chdir('GVHMR')
    p = mamba(env=env, python='3.10', **kwargs)
    p = mamba('pip install -e .', env=env, **kwargs)
    d.pushd('third-party/DPVO')
    f = await download('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip')
    p = Popen(f'unzip {f.path}', **kwargs)


def check_install(**kwargs):
    global aria
    failed = []
    pkgs = [which(p) for p in BINS]
    Log.debug(pkgs)
    pkgs = [p is None for p in pkgs]
    if any(pkgs):
        task = P.add_task("Install packages", start=False)
        i_pkgs()
        rich_finish(task)

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
        task = P.add_task("Install Mamba", start=False)
        aio.run(i_mamba(**kwargs))
        rich_finish(task)

    task = P.add_task("Install GVHMR", start=False)
    aio.run(i_gvhmr(**kwargs))
    rich_finish(task)


SHELL: str = get_shell()
PKG_MGR: str = get_pkg_mgr()
aria: aria2p.API = try_aria_port()
with Progress() as P:
    if __name__ == '__main__':
        check_install(dry_run=True)

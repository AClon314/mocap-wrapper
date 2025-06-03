"""shared install logic: 
- shell package manager(apt/dnf/brew/winget)
- python package manager(pip/mamba/conda)
"""
# from sys import path as PATH
from shutil import which, copy as cp
from mocap_wrapper.lib import *
from typing import Dict, Literal, Union, get_args
from mocap_wrapper.logger import getLogger

Log = getLogger(__name__)
ENV = 'mocap'
PACKAGES = [('aria2', 'aria2c'), 'git', '7z', ('p7zip-full p7zip-rar', '7z'), 'ffmpeg']  # TODO 7z: p7zip-full p7zip-rar
BINS = [p[1] if isinstance(p, tuple) else p for p in PACKAGES]
PACKAGES = [p[0] if isinstance(p, tuple) else p for p in PACKAGES]
TYPE_SHELLS = Literal['zsh', 'bash', 'ps']
SHELLS: Tuple[TYPE_SHELLS] = get_args(TYPE_SHELLS)
TYPE_PY_MGRS = Literal['mamba', 'conda', 'pip']
PY_MGRS: Tuple[TYPE_PY_MGRS] = get_args(TYPE_PY_MGRS)
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


def remove_if_p(path: str | Path):
    """remove file if progress is successful"""
    os.remove(path) if os.path.exists(path) else None


def get_py_mgr() -> TYPE_PY_MGRS:
    for mgr in PY_MGRS:
        if which(mgr):
            if mgr == 'conda':
                Log.warning(f"Use `mamba` for faster install")
            return mgr
    raise Exception(f"Not found any of {PY_MGRS}")


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
    p = await popen(p, **kwargs)
    return p


async def i_pkgs(**kwargs):
    # dnf/yum will update before each install
    if PKG_MGR not in ['dnf', 'yum']:
        await pkg('update', **kwargs)
    await pkg('install', PACKAGES, **kwargs)
    return True


async def get_envs(manager: TYPE_PY_MGRS = 'mamba', **kwargs):
    """
    Args:
        manager (str): 'mamba', 'conda', 'pip'
        kwargs (dict): `subprocess.Popen()` args

    Returns: 
        env (dict): eg: {'base': '~/miniforge3'}
        now (str): currently env name like 'base'
    """
    p, env = await echo(f'{manager} env list --json', **kwargs)
    env = env.strip().splitlines()[2:]
    env = [l.split() for l in env if l]   # type: ignore
    env = {l[0]: l[1 if len(l) == 2 else 2] for l in env}
    now = str(os.getenv('CONDA_DEFAULT_ENV'))
    return env, now


async def mamba(
    cmd: str = '',
    py_mgr: TYPE_PY_MGRS = 'mamba',
    env=ENV,
    python: str = '',
    txt: Literal['requirements.txt'] | Path | str = '',
    pkgs=[],
    **kwargs
):
    """By default do 2 things:
    1. create env if no exist
    2. install from `pkgs` and `txt`
    3. if `cmd` then, run `cmd` in the env

    Args:
        py_mgr (str): use `mamba` to install.
        kwargs (dict): `subprocess.Popen` args

    Returns:
        TODO: return failed list
    """
    envs = {}
    python = f'python={python}' if python else ''
    if py_mgr is None:
        py_mgr = PY_MGR
    if py_mgr == 'pip':
        envs, _ = await get_envs(PY_MGR)
        Log.info(f"skipped creating env for unsupported {py_mgr}")
    else:
        envs, _ = await get_envs(py_mgr)
        if env and env not in envs:
            p = await popen(f"{py_mgr} create -y -n {env} {python}", **kwargs)

    _txt = ''
    if txt:
        if os.path.exists(path_expand(txt)):
            if py_mgr == 'pip':
                _txt = '-r ' + str(txt)
            else:
                _txt = '--file ' + str(txt)
        else:
            Log.warning(f"{_txt} not found as requirements.txt")
    else:
        txt = ''

    py_bin = os.path.join(envs[env], 'bin')
    PY = ['pip', 'python']  # TODO: cache re.compile
    PY = {p: os.path.join(py_bin, p) for p in PY}
    if pkgs or txt:
        if py_mgr == 'pip':
            p = await popen(f"{PY['pip']} install {_txt} {' '.join(pkgs)}", **kwargs)
        else:
            p = await popen(f"{py_mgr} install -y -n {env} {_txt} {' '.join(pkgs)}", **kwargs)

    if cmd:
        cmd = re.sub(r"'(['])", r"\\\1", cmd)
        if is_win:
            _c = '/c'
        else:
            _c = '-c'

        is_sub = False
        for k, v in PY.items():
            pattern = re.compile(rf'^{k}(?= )')
            if pattern.match(cmd):
                cmd = re.sub(pattern, v, cmd)
                is_sub = True
                break
        if not is_sub:
            cmd = ' '.join(filter(None, (py_mgr, 'run -n', env, SHELL, _c, f"'{cmd}'")))
        p = await popen(cmd, **kwargs)
    return True  # TODO: return failed list


def txt_pip_retry(txt: str | Path, tmp_dir=DIR, env=ENV):
    """
    1. remove installed lines
    2. install package that start with `# ` (not like `##...`or`# #...`)
    """
    filename = os.path.basename(txt)
    txt = path_expand(txt)
    tmp = os.path.join(path_expand(tmp_dir), filename)
    if not os.path.exists(txt):
        raise FileNotFoundError(f"{txt} not found")
    cp(txt, tmp)
    with open(tmp, 'r', encoding='UTF-8') as f:
        raw = f.read()
    raw = re.sub(r'^(?!#).*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^# ', '', raw, flags=re.MULTILINE)
    with open(tmp, 'w', encoding='UTF-8') as f:
        f.write(raw)
    p = mamba(py_mgr='pip', txt=tmp, env=env)
    # remove_if_p(tmp, p)
    return p


async def git_pull(**kwargs):
    """```sh
    git fetch --all
    git pull
    git submodule update --init --recursive
    ```"""
    kwargs.setdefault('Raise', False)
    p = await popen('git fetch --all', **kwargs)
    p = await popen('git pull', **kwargs)
    p = await popen('git submodule update --init --recursive', **kwargs)
    return p


async def install(runs: Sequence[TYPE_RUNS], **kwargs):
    global Aria
    tasks = []

    pkgs = {p: which(p) for p in BINS}
    Log.debug(f'installed: {pkgs}')
    pkgs = [p for p, v in pkgs.items() if not v]
    if any(pkgs):
        await i_pkgs()

    if Aria is None:
        # try to start aria2c
        p = await popen('aria2c --enable-rpc --rpc-listen-port=6800', timeout=False, **kwargs)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    if PY_MGR == 'pip':
        from mocap_wrapper.script.mamba import i_mamba
        i_mamba()

    if 'gvhmr' in runs:
        from mocap_wrapper.install.gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in runs:
        from mocap_wrapper.install.wilor_mini import i_wilor_mini
        tasks.append(i_wilor_mini(**kwargs))

    ret = await aio.gather(*tasks)
    return ret


async def clean():
    p = await popen('pip cache purge')
    p = await popen('conda clean --all')


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()
PY_MGR = get_py_mgr()
try:
    if __name__ == '__main__':
        aio.run(install(runs=['gvhmr', ]))
except ImportError:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment.")
    raise

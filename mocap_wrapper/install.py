import subprocess as sp
import asyncio as aio
import os
from sys import platform, path as PATH
from shutil import which, copy as cp, move as mv
from time import sleep, time
from datetime import timedelta
from mocap_wrapper.logger import getLog
from types import SimpleNamespace
from typing import Dict, List, Literal, Union, get_args, overload
Log = getLog(__name__)

MODS = ['wilor', 'gvhmr']
ENV = 'mocap'
ARIA_PORTS = [6800, 16800]
OPT = {
    'dir': '~',
    # 'out': 'filename',
    'continue': True,
    'split': 5,
    'max_connection_per_server': 5,
    'min_split_size': 20  # don't split if file size < 40M
}
PACKAGES = [('aria2', 'aria2c'), 'git', 'unzip']
BINS = [p[1] if isinstance(p, tuple) else p for p in PACKAGES]
PACKAGES = [p[0] if isinstance(p, tuple) else p for p in PACKAGES]
TYPE_SHELLS = Literal['zsh', 'bash', 'ps']
SHELLS: TYPE_SHELLS = get_args(TYPE_SHELLS)
TYPE_PY_MGRS = Literal['mamba', 'conda', 'pip']
PY_MGRS: TYPE_PY_MGRS = get_args(TYPE_PY_MGRS)
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


# def if_fail(fails: list, progress: Union[sp.Popen, List[sp.Popen]]):
#     if isinstance(progress, list):
#         fails += progress
#     else:
#         fails.append(progress) if progress.returncode != 0 else None


def unzip(zip_path: str, to: str, **kwargs):
    if is_win:
        p = Popen(f'Expand-Archive -Path "{zip_path}" -DestinationPath "{to}"')
    else:
        p = Popen(f'unzip {zip_path} -d {to}', **kwargs)


def Popen(cmd='aria2c --enable-rpc --rpc-listen-port=6800',
          timeout=300., Raise=True, dry_run=False, **kwargs):
    """Used on long running commands
    set `timeout` to -1 to run in background
    """
    Log.info(cmd)
    if dry_run:
        return
    p = sp.Popen(cmd, shell=True, env=os.environ, **kwargs)
    if timeout is None or timeout >= 0:
        p.wait(timeout=timeout)
        if p.returncode != 0:
            if Raise:
                raise Exception(f"{cmd}")
            else:
                Log.error(f"{cmd}")
    return p


def Exec(cmd, timeout=60.0, Print=True, **kwargs) -> Union[str, bytes, None]:
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


def get_py_mgr() -> Union[TYPE_PY_MGRS, None]:
    for mgr in PY_MGRS:
        if which(mgr):
            if mgr == 'pip':
                break
            elif mgr == 'conda':
                Log.warning(f"Use `mamba` for faster install")
            return mgr
    aio.run(i_mamba())


def get_pkg_mgr() -> Union[str, None]:
    for mgr in PKG_MGRS.keys():
        if which(mgr):
            return mgr


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
        except ImportError:
            Log.warning(f"Failed to import aria2p")
            return None
        except Exception as e:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
            return None


def i_pkgs(**kwargs):
    # dnf/yum will update before each install
    if PKG_MGR not in ['dnf', 'yum']:
        pkg('update', **kwargs)
    pkg('install', PACKAGES, **kwargs)
    return True


def rich_finish(task: int):
    P.update(task, completed=100)
    P.start_task(task)


def path_expand(path: str):
    return os.path.expandvars(os.path.expanduser(path))


def opt_expand(url: str, **kwargs):
    options = {**OPT, **kwargs}
    options['dir'] = path_expand(options['dir'])
    if 'out' in options.keys():
        options['out'] = path_expand(options['out'])
    else:
        options['out'] = os.path.basename(url)
    return options


def curl(url: str, dry_run=False, **kwargs):
    options = opt_expand(url, **kwargs)
    out = os.path.join(options['dir'], options['out'])
    if is_win:
        p = Popen(f'bitsadmin /transfer MocapWrapperJob /download /priority normal {url} {out}', **kwargs)
    else:
        p = Popen(f'curl -L -C - -o {out} {url}', **kwargs)
    p.dir = options['dir']
    return p


async def aria(url: str, duration=0.5, dry_run=False, **kwargs: 'aria2p.Options'):
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

    Log.debug(options)
    d = Aria.add_uris([url], options=options)
    await aio.sleep(1.0)
    d = Aria.get_download(d.gid)
    url = d.files[0].uris[0]['uri']
    filename = os.path.basename(url)
    d.path = path = os.path.join(d.dir, filename)
    if d.is_complete:
        Log.info(f"{d.path} already downloaded")
        return d

    has_eta = d.eta < timedelta.max
    Log.warning(f"No ETA for {url}") if not has_eta else None
    if d.total_length == 0:
        raise Exception(f'length=0 for GID={d.gid}, detail: {d.__dict__}')

    task = P.add_task(f"⬇️ Download {filename}", total=d.total_length, start=has_eta)
    Log.debug(f"{d.__dict__}")
    while not d.is_complete:
        await aio.sleep(duration)
        d = Aria.get_download(d.gid)
        P.update(task, completed=d.completed_length, download_status=f'{d.completed_length_string()}/{d.total_length_string()} @ {d.download_speed_string()}')
    d.path = path
    return d


async def i_mamba(require_restart=True, **kwargs):
    Log.info("📦 Install Mamba")
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
    if Aria:
        d = await aria(url)
    else:
        d = curl(url)
    setup = d.dir + '/' + setup
    p = None
    if is_win:
        p = Popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
    else:
        p = Popen(f'bash "{setup}" -b', **kwargs)
    if p.returncode == 0:
        os.remove(setup)

    if require_restart:
        Log.info(f"✔ re-open new terminal and run me again to refresh shell env!")
        exit(0)

    return p


def get_envs(manager='mamba', **kwargs):
    """return {'base': '~/miniforge3'}"""
    env = Exec(f'{manager} env list', **kwargs)
    env = [l.split() for l in env.split('\n') if l and not l.startswith('#')]
    env = {l[0]: l[1 if len(l) == 2 else 2] for l in env}
    now = os.getenv('CONDA_DEFAULT_ENV')
    return env, now


def get_shell() -> Union[TYPE_SHELLS, None]:
    for s in SHELLS:
        if which(s):
            return s


def mamba(cmd: str = None,
          py_mgr: TYPE_PY_MGRS = None,
          env=ENV,
          python: str = None,
          txt: Literal['requirements.txt'] = None,
          pkgs=[], **kwargs):
    """By default do 2 things:
    1. create env if no exist
    2. install from `pkgs`
    - if `cmd` then, run `cmd` in the env

    `**kwargs` for `subprocess.Popen(...)`
    """
    envs = {}
    python = f'python={python}' if python else ''
    if py_mgr is None:
        py_mgr = PY_MGR
    if py_mgr == 'pip':
        envs, _ = get_envs(PY_MGR)
        Log.info(f"skipped creating env for unsupported {py_mgr}")
    else:
        envs, _ = get_envs(py_mgr)
        if env and env not in envs:
            p = Popen(f"{py_mgr} create -y -n {env} {python}", **kwargs)

    if txt:
        if os.path.exists(os.path.abspath(txt)):
            if py_mgr == 'pip':
                txt = '-r ' + txt
            else:
                txt = '--file ' + txt
        else:
            Log.warning(f"{txt} not found as requirements.txt")
    else:
        txt = ''
    if pkgs or txt:
        if py_mgr == 'pip':
            py_bin = os.path.join(envs[env], 'bin')
            pip = os.path.join(py_bin, 'pip')
            python = os.path.join(py_bin, 'python')
            p = Popen(f"{pip} install {txt} {' '.join(pkgs)}", **kwargs)
        else:
            p = Popen(f"{py_mgr} install -y -n {env} {txt} {' '.join(pkgs)}", **kwargs)

    if cmd:
        cmd = sub(r"'(['])", r"\\\1", cmd)
        # when need sheel env: {SHELL} {_c}
        # if is_win:
        #     _c = '/c'
        # else:
        #     _c = '-c'
        if py_mgr == 'pip':
            cmd = sub(r'^pip ', pip, cmd)
            cmd = sub(r'^python ', python, cmd)
            for word in ['pip', 'python']:
                if word in cmd:
                    Log.warning(f"Detected suspicious untranslated executable: {word}. If you encounter errors, you may want to modify the source code :)")
        else:
            cmd = f"{py_mgr} run -n {env} '{cmd}'"
        p = Popen(cmd, **kwargs)

    return p


class ExistsPathList(list):
    def __init__(self, chdir: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append(os.getcwd())
        if chdir:
            self.chdir(chdir)

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


def txt_from_self(filename='requirements.txt'):
    path = os.path.join(os.path.dirname(__file__), 'requirements', filename)
    return path


def txt_pip_retry(txt: str, tmp_dir='~', env=ENV):
    """
    1. remove installed
    2. install package that start with `# ` (not like `##...`or`# #...`)
    """
    filename = os.path.basename(txt)
    txt = path_expand(txt)
    tmp_dir = os.path.join(path_expand(tmp_dir), filename)
    if not os.path.exists(txt):
        raise FileNotFoundError(f"{txt} not found")
    cp(txt, tmp_dir)
    with open(tmp_dir, 'r', encoding='UTF-8') as f:
        raw = f.read()
    raw = sub(r'^(?!#).*', '', raw, flags=MULTILINE)
    raw = sub(r'^# ', '', raw, flags=MULTILINE)
    with open(tmp_dir, 'w', encoding='UTF-8') as f:
        f.write(raw)
    p = mamba(py_mgr='pip', txt=tmp_dir, env=env)
    os.remove(tmp_dir)
    return p


async def i_smplx(dir='~', env=ENV, **kwargs):
    Log.info("📦 Install SMPL && SMPLX")
    dir = path_expand(dir)
    d = ExistsPathList(dir)
    f = await aria('https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip')

    f = await aria('https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip')


async def i_dpvo(dir='~', env=ENV, **kwargs):
    Log.info("📦 Install DPVO")
    dir = path_expand(dir)
    unzip_to = os.path.join(dir, 'thirdparty')
    f = await aria('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip')
    p = None
    p = unzip(f.path, to=unzip_to, **kwargs)

    os.remove(f.path) if p.returncode == 0 and os.path.exists(f.path) else None

    if is_win:
        Log.warning("`export` not supported windows yet")
    else:
        CUDA = os.path.join('/usr/local/cuda-12.1/'.split('/'))
        PATH.append(os.path.join(CUDA, 'bin'))
        os.environ['CUDA_HOME'] = CUDA
    p = mamba(f'pip install -e {dir}', env=env, **kwargs)

    Log.info("✔ Installed DPVO")
    return p


async def i_gvhmr(dir='~', env=ENV, **kwargs):
    Log.info("📦 Install GVHMR")
    dir = path_expand(dir)
    d = ExistsPathList(dir)

    async def i_dpvo_before():
        p = Popen('git clone https://github.com/zju3dv/GVHMR --recursive', Raise=False, **kwargs)
        d.chdir('GVHMR')
        p = mamba(env=env, python='3.10', txt=txt_from_self('gvhmr.txt'), **kwargs)
        p = mamba(f'pip install -e {os.getcwd()}', env=env, **kwargs)
        return p

    tasks = [i_dpvo_before(), i_dpvo(dir=dir, env=env, **kwargs)]
    tasks = [aio.create_task(t) for t in tasks]
    tasks = await aio.gather(*tasks)

    d.pushd('third-party/DPVO')
    mv()
    d.popd()

    Log.info("✔ Installed GVHMR")


async def i_wilor_mini(env=ENV, **kwargs):
    Log.info("📦 Install WiLoR-mini")
    txt = txt_from_self('wilor-mini.txt')
    p = mamba(txt=txt, env=env, python='3.10', **kwargs)
    p = txt_pip_retry(txt, env=env)
    p = mamba(py_mgr='pip', pkgs=['git+https://github.com/warmshao/WiLoR-mini'], env=env, **kwargs)
    Log.info("✔ Installed WiLoR-mini")
    return p


async def install(mods, **kwargs):
    global Aria
    tasks = []

    pkgs = [which(p) for p in BINS]
    Log.debug(pkgs)
    pkgs = [p is None for p in pkgs]
    if any(pkgs):
        i_pkgs()

    if Aria is None:
        # try to start aria2c
        Popen(**kwargs)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    if 'mamba' in mods:
        aio.run(i_mamba(**kwargs))

    # if len(mods) > 1:
    #     kwargs.update({'env': 'mocap'})
    if 'gvhmr' in mods:
        tasks.append(aio.create_task(i_gvhmr(**kwargs)))
    if 'wilor' in mods:
        tasks.append(aio.create_task(i_wilor_mini(**kwargs)))

    Log.debug(f"task={tasks}")
    tasks = await aio.gather(*tasks)
    return tasks


def clean():
    p = Popen('pip cache purge')
    p = Popen('conda clean --all')


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()
PY_MGR = get_py_mgr()
try:
    import aria2p
    from rich import print
    from rich.text import Text
    from rich.progress import Progress, TextColumn
    from regex import sub, MULTILINE

    Aria: 'aria2p.API' = try_aria_port()

    class SpeedColumn(TextColumn):
        def render(self, task):
            if 'download_status' in task.fields.keys():
                return Text(task.fields['download_status'])
            elif task.speed:
                return Text(f"{task.speed:.3f} steps/s")
            else:
                return Text("")
    with Progress(*Progress.get_default_columns(), SpeedColumn('')) as P:
        if __name__ == '__main__':
            aio.run(install(mods=['gvhmr', ]))
except ImportError as e:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment")

import os
import asyncio as aio
import subprocess as sp
from sys import path as PATH
from shutil import which, copy as cp
from mocap_wrapper.logger import getLog
from mocap_wrapper.lib import *
from typing import Dict, List, Literal, Union, get_args
Log = getLog(__name__)

MODS = ['wilor', 'gvhmr']
ENV = 'mocap'
PACKAGES = [('aria2', 'aria2c'), 'git', '7z']
BINS = [p[1] if isinstance(p, tuple) else p for p in PACKAGES]
PACKAGES = [p[0] if isinstance(p, tuple) else p for p in PACKAGES]
TYPE_SHELLS = Literal['zsh', 'bash', 'ps']
SHELLS: TYPE_SHELLS = get_args(TYPE_SHELLS)
TYPE_PY_MGRS = Literal['mamba', 'conda', 'pip']
PY_MGRS: TYPE_PY_MGRS = get_args(TYPE_PY_MGRS)
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


def remove_if_p(path: str, progress: sp.Popen):
    os.remove(path) if progress.returncode == 0 and os.path.exists(path) else None


def get_py_mgr() -> Union[TYPE_PY_MGRS, None]:
    mgr = ''
    for mgr in PY_MGRS:
        if which(mgr):
            if mgr == 'pip':
                mgr = 'mamba'
                aio.run(i_mamba())  # TODO
                break
            elif mgr == 'conda':
                Log.warning(f"Use `mamba` for faster install")
    return mgr


def get_pkg_mgr() -> Union[str, None]:
    for mgr in PKG_MGRS.keys():
        if which(mgr):
            return mgr


def pkg(action: TYPE_PKG_ACT, package: list[str] = [], **kwargs):
    p = f"{SU}{PKG_MGR} {PKG_MGRS[PKG_MGR][action]} {' '.join(package)}"
    p = Popen(p, **kwargs)
    return p


def i_pkgs(**kwargs):
    # dnf/yum will update before each install
    if PKG_MGR not in ['dnf', 'yum']:
        pkg('update', **kwargs)
    pkg('install', PACKAGES, **kwargs)
    return True


def rich_finish(task: int):
    P.update(task, completed=100)
    P.start_task(task)


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


def google_drive(ID: str):
    # TODO
    """
    - ID: shared file url. Example: `https://drive.google.com/file/d/1DE5G***********************K0nr0/view?...`, then `1DE5G***********************K0nr0` is the ID
    """
    uuid = 'da72c1d0-7076-45c9-9b2f-312c8edae741'
    # return 'https://drive.google.com/uc?export=download&id=' + ID
    return f'https://drive.usercontent.google.com/download?id={ID}&export=download&authuser=0&confirm=t&uuid={uuid}&at=AEz70l5ReyqrF6PqljBUTBLj5yqr:1740753223630'


def i_mamba(require_restart=True, **kwargs):
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
        d = aria(url)   # TODO
    else:
        d = curl(url)

    def i_mamba_post():
        setup = d.dir + '/' + setup
        p = None
        if is_win:
            p = Popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
        else:
            p = Popen(f'bash "{setup}" -b', **kwargs)
        remove_if_p(setup, p)

        p = mamba(env='nogil', txt=txt_from_self(), pkgs=['python-freethreading'], **kwargs)
        p = Popen("conda config --set env_prompt '({default_env})'", **kwargs)

        if require_restart:
            Log.info(f"✔ re-open new terminal and run me again to refresh shell env!")
            exit(0)  # TODO: find a way not to exit
        return p

    return  # p


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
        if is_win:
            _c = '/c'
        else:
            _c = '-c'
        if py_mgr == 'pip':
            cmd = sub(r'^pip ', pip, cmd)
            cmd = sub(r'^python ', python, cmd)
            for word in ['pip', 'python']:
                if word in cmd:
                    Log.warning(f"Detected suspicious untranslated executable: {word}. If you encounter errors, you may want to modify the source code :)")
        else:
            cmd = f"{py_mgr} run -n {env} {SHELL} {_c} '{cmd}'"
        p = Popen(cmd, **kwargs)

    return p


def txt_from_self(filename='requirements.txt'):
    path = os.path.join(os.path.dirname(__file__), 'requirements', filename)
    return path


def txt_pip_retry(txt: str, tmp_dir='~', env=ENV):
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
    raw = sub(r'^(?!#).*', '', raw, flags=MULTILINE)
    raw = sub(r'^# ', '', raw, flags=MULTILINE)
    with open(tmp, 'w', encoding='UTF-8') as f:
        f.write(raw)
    p = mamba(py_mgr='pip', txt=tmp, env=env)
    remove_if_p(tmp, p)
    return p


def smpl_task(dir='~',
              download='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
              referer='https://smpl.is.tue.mpg.de/',
              PHPSESSID='26-digits_123456789_123456',
              user_agent='Transmission/2.77',
              **kwargs):
    """
    - dir: download to which temp dir
    - download: file url
    - referer: main domain
    - PHPSESSID: from your logged-in cookie🍪, **expires after next login**
    - user_agent: from your browser🌐
    """
    dir = path_expand(dir)

    cookie = os.path.join(dir, 'cookies.txt')
    cookies = [{
        'domain': '.' + referer.split('/')[2],  # MAYBE BUGGY
        'name': 'PHPSESSID',
        'value': PHPSESSID,
    }]
    save_cookies_to_file(cookies, cookie)
    options = {
        'load-cookies': cookie,
        'user-agent': user_agent,
        'referer': referer,
    }
    options = {**options, **kwargs}
    return aria(download, **options)


def i_smpl(dir='~',
           PHPSESSIDs: dict = {'smpl': '', 'smplx': ''},
           user_agent='Transmission/2.77',
           **kwargs) -> List['aria2p.Download']:
    """
    - PHPSESSIDs: {'smpl': '26-digits_123456789_123456', 'smplx': '26-digits_123456789_123456'}
    """
    Log.info("⬇️ Download SMPL && SMPLX (📝 By downloading, you agree to SMPL/SMPL-X corresponding licences)")

    for k, v in PHPSESSIDs.items():
        if not (v and isinstance(v, str)):
            Log.warning(f"🍪 cookies: PHPSESSID for {k}={v} could cause download failure")

    tasks = [
        smpl_task(dir=dir, PHPSESSID=PHPSESSIDs['smpl'], user_agent=user_agent, **kwargs),
        smpl_task(download='https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip',
                  referer='https://smpl-x.is.tue.mpg.de/',
                  dir=dir, PHPSESSID=PHPSESSIDs['smplx'], user_agent=user_agent, **kwargs)
    ]
    tasks = aio.gather(*tasks)  # TODO

    for t in tasks:
        if t.is_complete:
            unzip(t.path, to=dir, **kwargs)

    if any([not t.is_complete for t in tasks]):
        Log.error("❌ please check your cookies:PHPSESSID if it's expired, or change your IP address by VPN")
    else:
        Log.info("✔ Downloaded SMPL && SMPLX")
    return tasks


def i_dpvo(dir='~', env=ENV, **kwargs):
    Log.info("📦 Install DPVO")
    dir = path_expand(dir)
    f = aria('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip')   # TODO
    p = unzip(f.path, to=dir, **kwargs)
    remove_if_p(f.path, p)

    if is_win:
        Log.warning("`export` not supported windows yet")
    else:
        CUDA = os.path.join('/usr/local/cuda-12.1/'.split('/'))
        PATH.append(os.path.join(CUDA, 'bin'))
        os.environ['CUDA_HOME'] = CUDA
    p = mamba(f'pip install -e {dir}', env=env, **kwargs)

    Log.info("✔ Installed DPVO")
    return p


def i_gvhmr_models(dir='~', **kwargs):
    Log.info("📦 Download GVHMR pretrained models (📝 By downloading, you agree to the GVHMR's corresponding licences)")
    dir = path_expand(dir)
    os.chdir(dir)
    G_drive = {
        'dpvo/dpvo.pth': '1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0',
        'gvhmr/gvhmr_siga24_release.ckpt': '1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP',
        'hmr2/epoch=10-step=25000.ckpt': '1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc',
        'vitpose/vitpose-h-multi-coco.pth': '1sR8xZD9wrZczdDVo6zKscNLwvarIRhP5',
        'yolo/yolov8x.pt': '1_HGm-lqIH83-M1ML4bAXaqhm_eT2FKo5',
    }

    G_drive = {os.path.join(dir, k): google_drive(v) for k, v in G_drive.items()}
    Log.debug(G_drive)
    tasks = [aria(url=url, out=out) for out, url in G_drive.items()]
    tasks = [aio.create_task(t) for t in tasks]
    tasks = aio.gather(*tasks)  # TODO
    Log.info("✔ Download GVHMR pretrained models")
    return tasks


def i_gvhmr(dir='~', env=ENV, **kwargs):
    Log.info("📦 Install GVHMR")
    dir = path_expand(dir)
    d = ExistsPathList(chdir=dir)
    dir = os.path.join(dir, 'GVHMR')
    if not os.path.exists(dir):
        p = Popen('git clone https://github.com/zju3dv/GVHMR', Raise=False, **kwargs)
    d.chdir('GVHMR')
    os.makedirs('inputs/checkpoints', exist_ok=True)
    dir_checkpoints = os.path.join(dir, 'inputs/checkpoints')

    def i_gvhmr_post():
        p = Popen('git submodule update --init --recursive', **kwargs)
        p = mamba(env=env, python='3.10', txt=txt_from_self('gvhmr.txt'), **kwargs)
        p = mamba(f'pip install -e {os.getcwd()}', env=env, **kwargs)
        return p

    tasks = [
        i_gvhmr_post(),
        i_dpvo(dir=os.path.join(dir, 'third-party/DPVO'), env=env, **kwargs),
        i_smpl(dir=dir_checkpoints, **kwargs),
        i_gvhmr_models(dir=dir_checkpoints, **kwargs)
    ]
    tasks = [aio.create_task(t) for t in tasks]
    tasks = aio.gather(*tasks)  # TODO

    Log.info("✔ Installed GVHMR")


def i_wilor_mini(env=ENV, **kwargs):
    Log.info("📦 Install WiLoR-mini")
    txt = txt_from_self('wilor-mini.txt')
    p = mamba(txt=txt, env=env, python='3.10', **kwargs)
    p = txt_pip_retry(txt, env=env)
    p = mamba(py_mgr='pip', pkgs=['git+https://github.com/warmshao/WiLoR-mini'], env=env, **kwargs)
    Log.info("✔ Installed WiLoR-mini")
    return p


def install(mods, **kwargs):
    global Aria
    tasks = []

    pkgs = [which(p) for p in BINS]
    Log.debug(pkgs)
    pkgs = [p is None for p in pkgs]
    if any(pkgs):
        i_pkgs()

    if Aria is None:
        # try to start aria2c
        Popen(timeout=False, **kwargs)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    if 'mamba' in mods:
        aio.run(i_mamba(**kwargs))

    if 'gvhmr' in mods:
        tasks.append(aio.create_task(i_gvhmr(**kwargs)))
    if 'wilor' in mods:
        tasks.append(aio.create_task(i_wilor_mini(**kwargs)))

    Log.debug(f"task={tasks}")
    tasks = aio.gather(*tasks)  # TODO
    return tasks


def clean():
    p = Popen('pip cache purge')
    p = Popen('conda clean --all')


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()
PY_MGR = get_py_mgr()
try:
    from regex import sub, MULTILINE
    from netscape_cookies import save_cookies_to_file
    if __name__ == '__main__':
        with Progress(*Progress.get_default_columns(), SpeedColumn('')) as P:
            run(install(mods=['gvhmr', ]))
except ImportError as e:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment. {e}")

import os
from sys import path as PATH
from shutil import which, copy as cp
from mocap_wrapper.logger import getLogger
from mocap_wrapper.lib import *
from typing import Dict, List, Literal, Union, get_args
Log = getLogger(__name__)

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
    """remove file if progress is successful"""
    os.remove(path) if progress.returncode == 0 and os.path.exists(path) else None


def get_py_mgr() -> Union[TYPE_PY_MGRS, None]:
    for mgr in PY_MGRS:
        if which(mgr):
            if mgr == 'conda':
                Log.warning(f"Use `mamba` for faster install")
            return mgr
    raise Exception(f"Not found any of {PY_MGRS}")


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
        d = run_async(download(url, **kwargs))
    else:
        raise Exception("Aria2c not found")

    setup = d.dir + '/' + setup
    p = None
    if is_win:
        p = Popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
    else:
        p = Popen(f'bash "{setup}" -b', **kwargs)
    remove_if_p(setup, p)

    p = mamba(env='nogil', txt=txt_from_self(), pkgs=['python-freethreading'], **kwargs)
    p = Popen("conda config --set env_prompt '({default_env})'", **kwargs)  # TODO: need test

    if require_restart:
        Log.info(f"✔ re-open new terminal and run me again to refresh shell env!")
        exit(0)  # TODO: find a way not to exit


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


async def mamba(
    cmd: str = None,
    py_mgr: TYPE_PY_MGRS = None,
    env=ENV,
    python: str = None,
    txt: Literal['requirements.txt'] = None,
    pkgs=[], **kwargs
):
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
        if os.path.exists(path_expand(txt)):
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


def txt_pip_retry(txt: str, tmp_dir=DIR, env=ENV):
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


def tmd_coro(Dir=DIR,
             url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
             referer='https://smpl.is.tue.mpg.de/',
             PHPSESSID='26-digits_123456789_123456',
             user_agent='Transmission/2.77',
             **kwargs):
    """
    - Dir: download to which temp dir
    - url: file url
    - referer: main domain
    - PHPSESSID: from your logged-in cookie🍪, **expires after next login**
    - user_agent: from your browser🌐
    """
    Dir = path_expand(Dir)
    path = path_expand(os.path.join(Dir, 'cookies.txt'))
    cookies = [{
        'domain': DIR + referer.split('/')[2],  # MAYBE BUGGY
        'name': 'PHPSESSID',
        'value': PHPSESSID,
    }]
    save_cookies_to_file(cookies, path)
    options = {
        'load-cookies': path,
        'user-agent': user_agent,
        'referer': referer,
    }
    options = {**options, **kwargs}
    return download(url, dir=Dir, **options)


@async_worker
async def i_smpl(
    Dir=DIR,
    PHPSESSIDs: dict = {'smpl': '', 'smplx': ''},
    user_agent='Transmission/2.77',
    duration=RELAX,
    **kwargs
) -> List['aria2p.Download']:
    """
    - PHPSESSIDs: {'smpl': '26-digits_123456789_123456', 'smplx': '26-digits_123456789_123456'}
    """
    Log.info("⬇️ Download SMPL && SMPLX (📝 By downloading, you agree to SMPL/SMPL-X corresponding licences)")

    for k, v in PHPSESSIDs.items():
        if not (v and isinstance(v, str)):
            Log.warning(f"🍪 cookies: PHPSESSID for {k}={v} could cause download failure")

    Dir = path_expand(Dir)
    zips = {
        'SMPL_python_v.1.1.0.zip': {
            'from': 'SMPL_python_v.1.1.0/smpl/models/*',
            'to': 'smpl',
            'coro': tmd_coro(Dir=Dir, PHPSESSID=PHPSESSIDs['smpl'], user_agent=user_agent, **kwargs),
        },
        'models_smplx_v1_1.zip': {
            'from': 'models/smplx/*',
            'to': 'smplx',
            'coro': tmd_coro(
                url='https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip',
                referer='https://smpl-x.is.tue.mpg.de/',
                Dir=Dir, PHPSESSID=PHPSESSIDs['smplx'], user_agent=user_agent, **kwargs
            ),
        }
    }

    dls = []
    for zip, d in zips.items():
        zip_file = os.path.join(Dir, zip)
        zips[zip]['to'] = os.path.join(Dir, d['to'])
        if os.path.exists(zip_file):
            unzip(zip_file, From=d['from'], to=d['to'], **kwargs)
        else:
            dls.append(d['coro'])

    def unzip_after_dl(task: aio.Task[aria2p.Download]):
        if task.cancelled():
            msg = "Download cancelled"
            Log.error(msg)
        t = task.result()
        if t.is_complete:
            d = zips[os.path.basename(t.path)]  # TODO: check if t.path is correct
            unzip(t.path, From=d['from'], to=d['to'], **kwargs)

    dls = await aio.gather(*await run_1by1(dls, unzip_after_dl))

    if any([not dl.is_complete for dl in dls]):
        Log.error("❌ please check your cookies:PHPSESSID if it's expired, or change your IP address by VPN")
    else:
        Log.info("✔ Downloaded SMPL && SMPLX")
    return dls


@async_worker
async def i_dpvo(Dir=DIR, env=ENV, **kwargs):
    Log.info("📦 Install DPVO")
    Dir = path_expand(Dir)
    f = await download(
        'https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',
        md5='994092410ba29875184f7725e0371596',
        dir=Dir
    )
    if f.is_complete and os.path.exists(f.path):
        p = unzip(f.path, to=os.path.join(Dir, 'thirdparty'), **kwargs)
        # remove_if_p(f.path, p)
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")

    if is_win:
        Log.warning("`export` not supported windows yet")
    else:
        CUDA = '/usr/local/cuda-12.1/'.split('/')
        CUDA = os.path.join(*CUDA)
        if os.path.exists(CUDA):
            PATH.append(os.path.join(CUDA, 'bin'))
            os.environ['CUDA_HOME'] = CUDA
        else:
            Log.warning(f"❌ CUDA not found in {CUDA}")
    p = mamba(f'pip install -e {Dir}', env=env, **kwargs)

    Log.info("✔ Installed DPVO")
    return p


@async_worker
async def i_gvhmr_models(Dir=DIR, duration=RELAX):
    Log.info("📦 Download GVHMR pretrained models (📝 By downloading, you agree to the GVHMR's corresponding licences)")
    Dir = path_expand(Dir)
    G_drive = {
        ('dpvo', 'dpvo.pth'): '1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0',
        ('gvhmr', 'gvhmr_siga24_release.ckpt'): '1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP',
        ('hmr2', 'epoch=10-step=25000.ckpt'): '1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc',
        ('vitpose', 'vitpose-h-multi-coco.pth'): '1sR8xZD9wrZczdDVo6zKscNLwvarIRhP5',
        ('yolo', 'yolov8x.pt'): '1_HGm-lqIH83-M1ML4bAXaqhm_eT2FKo5',
    }
    coros = []
    for out, ID in G_drive.items():
        url = google_drive(id=ID)
        t = download(url, out=os.path.join(Dir, *out))
        coros.append(t)

    results = await run_1by1(coros)

    Log.info("✔ Download GVHMR pretrained models")


@async_worker
async def i_gvhmr(Dir=DIR, env=ENV, **kwargs):
    Log.info("📦 Install GVHMR")
    Dir = path_expand(Dir)
    d = ExistsPathList(chdir=Dir)
    Dir = os.path.join(Dir, 'GVHMR')
    if not os.path.exists(Dir):
        p = Popen('git clone https://github.com/zju3dv/GVHMR', Raise=False, **kwargs)
    d.chdir('GVHMR')
    dir_checkpoints = path_expand(os.path.join('inputs', 'checkpoints'))
    dir_smpl = os.path.join(dir_checkpoints, 'body_models')
    os.makedirs(dir_smpl, exist_ok=True)

    @worker
    def i_gvhmr_post():
        p = Popen('git fetch --all', Raise=False, **kwargs)
        p = Popen('git pull', Raise=False, **kwargs)
        p = Popen('git submodule update --init --recursive', Raise=False, **kwargs)
        p = mamba(env=env, python='3.10', txt=txt_from_self('gvhmr.txt'), **kwargs)
        p = mamba(f'pip install -e {os.getcwd()}', env=env, **kwargs)
        return p
    i_gvhmr_post()  # should non blocking in new thread

    tasks = [
        i_dpvo(Dir=os.path.join(Dir, 'third-party/DPVO'), env=env, **kwargs),
        i_smpl(Dir=dir_smpl, **kwargs),
        i_gvhmr_models(Dir=dir_checkpoints, **kwargs)
    ]
    tasks = [await t for t in tasks]    # should non bloking in new threads
    ThreadWorkerManager.await_workers(*tasks)   # should block
    Log.info("✔ Installed GVHMR")


def i_wilor_mini(env=ENV, **kwargs):
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

    pkgs = {p: which(p) for p in BINS}
    Log.debug(pkgs)
    pkgs = [p for p, v in pkgs.items() if not v]
    if any(pkgs):
        i_pkgs()

    if Aria is None:
        # try to start aria2c
        Popen(timeout=False, **kwargs)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    if PY_MGR == 'pip':
        run_async(i_mamba())

    if 'gvhmr' in mods:
        tasks.append(i_gvhmr(Dir='..', **kwargs))
    if 'wilor' in mods:
        tasks.append(i_wilor_mini(**kwargs))

    Log.debug(f"task={tasks}")
    tasks = [await t for t in tasks]
    ThreadWorkerManager.await_workers(*tasks)
    return tasks


def clean():
    p = Popen('pip cache purge')
    p = Popen('conda clean --all')


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()
PY_MGR = get_py_mgr()
try:
    from mocap_wrapper.Gdown import google_drive
    from regex import sub, MULTILINE
    from netscape_cookies import save_cookies_to_file
    if __name__ == '__main__':
        aio.run(install(mods=['gvhmr', ]))
except ImportError:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment.")
    raise

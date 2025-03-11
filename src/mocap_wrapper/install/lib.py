"""shared install logic."""
from hashlib import md5
import os
from sys import path as PATH
from shutil import which, copy as cp
from mocap_wrapper.lib import *
from typing import Dict, List, Literal, TypedDict, Union, Unpack, get_args
from mocap_wrapper.logger import getLogger

Log = getLogger(__name__)

ENV = 'mocap'
PACKAGES = [('aria2', 'aria2c'), 'git', '7z']
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


def remove_if_p(path: Union[str, Path]):
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


async def i_mamba(require_restart=True, **kwargs):
    Log.info("📦 Install Mamba")
    url = "https://github.com/conda-forge/miniforge/releases/latest/download/"
    setup = ''
    if is_linux or is_mac:
        setup = "echo Miniforge3-$(uname)-$(uname -m).sh"
        p, setup = await echo(setup, **kwargs)
        setup = setup.strip()
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
        p = await popen(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3', **kwargs)
    else:
        p = await popen(f'bash "{setup}" -b', **kwargs)
    remove_if_p(setup)

    p = mamba(env='nogil', txt=txt_from_self(), pkgs=['python-freethreading'], **kwargs)
    p = await popen("conda config --set env_prompt '({default_env})'", **kwargs)  # TODO: need test

    if require_restart:
        Log.info(f"✔ re-open new terminal and run me again to refresh shell env!")
        exit(0)  # TODO: find a way not to exit


async def get_envs(manager: TYPE_PY_MGRS = 'mamba', **kwargs):
    """
    Args:
        manager (str): 'mamba', 'conda', 'pip'
        kwargs (dict): `subprocess.Popen()` args

    Returns: 
        env (dict): eg: {'base': '~/miniforge3'}
        now (str): currently env name like 'base'
    """
    p, env = await echo(f'{manager} env list', **kwargs)
    env = env.strip()
    env = [l.split() for l in env.split('\n') if l and not l.startswith('#')]   # type: ignore
    env = {l[0]: l[1 if len(l) == 2 else 2] for l in env}
    now = str(os.getenv('CONDA_DEFAULT_ENV'))
    return env, now


async def mamba(
    cmd: str = '',
    py_mgr: TYPE_PY_MGRS = 'mamba',
    env=ENV,
    python: str = '',
    txt: Union[Literal['requirements.txt'], str] = '',
    pkgs=[],
    **kwargs
):
    """By default do 2 things:
    1. create env if no exist
    2. install from `pkgs` and `txt`
    3. if `cmd` then, run `cmd` in the env

    Args:
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
            p = await popen(f"{pip} install {txt} {' '.join(pkgs)}", **kwargs)
        else:
            p = await popen(f"{py_mgr} install -y -n {env} {txt} {' '.join(pkgs)}", **kwargs)

    if cmd:
        cmd = re_sub(r"'(['])", r"\\\1", cmd)
        if is_win:
            _c = '/c'
        else:
            _c = '-c'
        if py_mgr == 'pip':
            cmd = re_sub(r'^pip ', pip, cmd)
            cmd = re_sub(r'^python ', python, cmd)
            for word in ['pip', 'python']:
                if word in cmd:
                    Log.warning(f"Detected suspicious untranslated executable: {word}. If you encounter errors, you may want to modify the source code :)")
        else:
            cmd = ' '.join(filter(None, (py_mgr, 'run -n', env, SHELL, _c, f"'{cmd}'")))
        p = await popen(cmd, **kwargs)
    return True  # TODO: return failed list


def txt_from_self(filename='requirements.txt'):
    from importlib.resources import path as res_path
    with res_path('mocap_wrapper.requirements', filename) as path:
        return str(path.absolute())


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
    raw = re_sub(r'^(?!#).*', '', raw, flags=MULTILINE)
    raw = re_sub(r'^# ', '', raw, flags=MULTILINE)
    with open(tmp, 'w', encoding='UTF-8') as f:
        f.write(raw)
    p = mamba(py_mgr='pip', txt=tmp, env=env)
    # remove_if_p(tmp, p)
    return p


class Kw_itmd_coro(TypedDict, total=False):
    md5: str
    duration: float
    dry_run: bool


class Kw_itmd(Kw_itmd_coro, total=False):
    Dir: str
    url: str
    referer: str
    PHPSESSID: str
    user_agent: str


class Kw_i_smpl(Kw_itmd):
    From: str
    to: str


def tue_mpg_download(
    Dir=DIR,
    url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
    referer='https://smpl.is.tue.mpg.de/',
    PHPSESSID='26-digits_123456789_123456',
    user_agent='Transmission/2.77',
    **kwargs: Unpack[Kw_itmd_coro]
):
    """
    Returns:
        Coroutine: async download()

    Args:
        Dir (str): downlaod directory
        url (str): download file url
        referer (str): prevent error 403
        PHPSESSID (str, optional): not necessary. PHPSESSID retrieved from logged in cookie, **expires after next login**  
                        从已登录的 cookie 中获取的 PHPSESSID，**在下次登录后过期**
        user_agent (str, optional): not necessary. User-Agent to prevent error 403
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


async def tue_mpg(
    From='SMPL_python_v.1.1.0/smpl/models/*',
    to='smpl',
    map: Dict[str, str] = {},
    **kwargs: Unpack[Kw_itmd]
):
    """
    1.Download 2.unzip 3.synlink files

    Args:
        Dir (str): work directory
        url (str): download file url
        referer (str): prevent error 403

        From (str): which files to unzip
        to (str): where to unzip
        map (dict): symlink after unzip  
            eg: {'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'}
    """
    f = await tue_mpg_download(**kwargs)
    p = await unzip(f.path, From=From, to=to, **kwargs)
    for From, to in map.items():
        os.symlink(From, to)
    return f


async def i_smpl(
    PHPSESSIDs: dict = {'smpl': '', 'smplx': ''},
    **kwargs: Unpack[Kw_i_smpl]
) -> List['aria2p.Download']:
    """
    Args:
        PHPSESSIDs (dict): {'smpl': '26-digits_123456789_123456', 'smplx': '26-digits_123456789_123456'}
    """
    Log.info("⬇️ Download SMPL && SMPLX (📝 By downloading, you agree to SMPL/SMPL-X corresponding licences)")

    # for k, v in PHPSESSIDs.items():
    #     if not (v and isinstance(v, str)):
    #         Log.warning(f"🍪 cookies: PHPSESSID for {k}={v} could cause download failure")

    Dir = path_expand(kwargs.setdefault('Dir', DIR))
    tasks = [
        tue_mpg(
            **filter_kwargs([i_smpl], kwargs),  # type: ignore
            url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
            referer='https://smpl.is.tue.mpg.de/',
            md5='21f382969eed3ee3f597b049f228f84d',
            From='SMPL_python_v.1.1.0/smpl/models/*',
            to='smpl',
            map={'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'},
            Dir=Dir,
            PHPSESSID=PHPSESSIDs['smpl'],
        ),
        tue_mpg(
            **filter_kwargs([i_smpl], kwargs),  # type: ignore
            url='https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip',
            referer='https://smpl-x.is.tue.mpg.de/',
            md5='763a8d2d6525263ed09aeeac3e67b134',
            From='models/smplx/*',
            to='smplx',
            Dir=Dir,
            PHPSESSID=PHPSESSIDs['smplx'],
        ),
    ]
    dls = await aio.gather(*await run_1by1(tasks))

    if any([not dl.is_complete for dl in dls]):
        Log.error("❌ please check your cookies:PHPSESSID if it's expired, or change your IP address by VPN")
    else:
        Log.info("✔ Installed SMPL && SMPLX")
    return dls


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
        # remove_if_p(f.path)    # TODO: remove_if_p
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")

    txt = txt_from_self('dpvo.txt')
    p = mamba(env=env, txt=txt, **kwargs)
    p = txt_pip_retry(txt, env=env)

    if is_win:
        Log.warning("`export` not supported windows yet")
    else:
        # TODO these seems unnecessary
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


async def install(mods, **kwargs):
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
        run_async(i_mamba())

    if 'gvhmr' in mods:
        from mocap_wrapper.install.gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in mods:
        from mocap_wrapper.install.wilor_mini import i_wilor_mini
        tasks.append(i_wilor_mini(**kwargs))

    tasks = await aio.gather(*tasks)
    return tasks


async def clean():
    p = await popen('pip cache purge')
    p = await popen('conda clean --all')


SHELL = get_shell()
PKG_MGR = get_pkg_mgr()
PY_MGR = get_py_mgr()
try:
    from mocap_wrapper.Gdown import google_drive
    from netscape_cookies import save_cookies_to_file   # type: ignore
    if __name__ == '__main__':
        aio.run(install(mods=['gvhmr', ]))
except ImportError:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment.")
    raise

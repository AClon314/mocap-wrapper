#!/bin/env python
from operator import is_
import os
import re
import sys
import json
import socket
import shutil
import logging
import subprocess
from time import time
from random import shuffle
from urllib.request import urlretrieve, urlopen
IS_DEBUG = os.getenv('GITHUB_ACTIONS', None)
__package__ = 'mocap_wrapper'
_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO
_SLASH_R = '\r\033[K' if IS_DEBUG else ''
_SLASH_N = '\n' if IS_DEBUG else ''
logging.basicConfig(level=_LEVEL)
Log = logging.getLogger(__name__)
is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')
is_linux = sys.platform.startswith('linux')
ENV = 'base' if IS_DEBUG else 'gil'  # TODO: nogil when compatible
FOLDER = 'mocap'
MAMBA = 'mamba'
CONDA = 'conda'
LAST_SPEED = 0.0
LAST_TIME = BEGIN_TIME = START_SLOW_TIME = time()
LAST_TIME = LAST_TIME - 1
TIMEOUT = 15
_RE = {
    'mamba_prefix': 'PREFIX=(.*)\n',
    'python': r'Python (\d+).(\d+)',
}
RE = {k: re.compile(v) for k, v in _RE.items()}
MIRROR_DL = [
    ['https://gh.h233.eu.org/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [@X.I.U/XIU2] 提供'],
    ['https://ghproxy.1888866.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [WJQSERVER-STUDIO/ghproxy] 提供'],
    ['https://gh.ddlc.top/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [@mtr-static-official] 提供'],
    ['https://slink.ltd/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [知了小站] 提供'],
    ['https://gh-proxy.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh-proxy.com] 提供'],
    ['https://cors.isteed.cc/github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [@Lufs\'s] 提供'],
    ['https://hub.gitmirror.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [GitMirror] 提供'],
    ['https://down.sciproxy.com/github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [sciproxy.com] 提供'],
    ['https://ghproxy.cfd/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [@yionchilau] 提供'],
    ['https://github.boki.moe/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [blog.boki.moe] 提供'],
    ['https://github.moeyy.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [moeyy.cn] 提供'],
    ['https://gh-proxy.net/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh-proxy.net] 提供'],
    ['https://github.yongyong.online/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [github.yongyong.online] 提供'],
    ['https://ghdd.862510.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghdd.862510.xyz] 提供'],
    ['https://gh.jasonzeng.dev/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.jasonzeng.dev] 提供'],
    ['https://gh.monlor.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.monlor.com] 提供'],
    ['https://fastgit.cc/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [fastgit.cc] 提供'],
    ['https://github.tbedu.top/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [github.tbedu.top] 提供'],
    ['https://gh-proxy.linioi.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh-proxy.linioi.com] 提供'],
    ['https://firewall.lxstd.org/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [firewall.lxstd.org] 提供'],
    ['https://mirrors.chenby.cn/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [mirrors.chenby.cn] 提供'],
    ['https://github.ednovas.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [github.ednovas.xyz] 提供'],
    ['https://ghfile.geekertao.top/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghfile.geekertao.top] 提供'],
    ['https://ghp.keleyaa.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghp.keleyaa.com] 提供'],
    ['https://github.wuzhij.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [github.wuzhij.com] 提供'],
    ['https://gh.cache.cloudns.org/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.cache.cloudns.org] 提供'],
    ['https://gh.chjina.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.chjina.com] 提供'],
    ['https://ghpxy.hwinzniej.top/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghpxy.hwinzniej.top] 提供'],
    ['https://cdn.crashmc.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [cdn.crashmc.com] 提供'],
    ['https://git.yylx.win/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [git.yylx.win] 提供'],
    ['https://gitproxy.mrhjx.cn/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gitproxy.mrhjx.cn] 提供'],
    ['https://ghproxy.cxkpro.top/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghproxy.cxkpro.top] 提供'],
    ['https://gh.xxooo.cf/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.xxooo.cf] 提供'],
    ['https://ghproxy.xiaopa.cc/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [ghproxy.xiaopa.cc] 提供'],
    ['https://gh.944446.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.944446.xyz] 提供'],
    ['https://github.limoruirui.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [github.limoruirui.com] 提供'],
    ['https://api-gh.muran.eu.org/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [api-gh.muran.eu.org] 提供'],
    ['https://gh.idayer.com/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.idayer.com] 提供'],
    ['https://gh.zwnes.xyz/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.zwnes.xyz] 提供'],
    ['https://gh.llkk.cc/https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [gh.llkk.cc] 提供'],
    ['https://down.npee.cn/?https://github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [npee社区] 提供'],
    ['https://raw.ihtw.moe/github.com', '美国', '[美国 Cloudflare CDN] - 该公益加速源由 [raw.ihtw.moe] 提供'],
    ['https://dgithub.xyz', '美国', '[美国 西雅图] - 该公益加速源由 [dgithub.xyz] 提供'],
    ['https://gh-proxy.ygxz.in/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [@一个小站 www.ygxz.in] 提供'],
    ['https://gh.nxnow.top/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [gh.nxnow.top] 提供'],
    ['https://gh-proxy.ygxz.in/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [gh-proxy.ygxz.in] 提供'],
    ['https://gh.zwy.one/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [gh.zwy.one] 提供'],
    ['https://ghproxy.monkeyray.net/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [ghproxy.monkeyray.net] 提供'],
    ['https://gh.xx9527.cn/https://github.com', '美国', '[美国 洛杉矶] - 该公益加速源由 [gh.xx9527.cn] 提供'],
    # 为了缓解非美国公益节点压力（考虑到很多人无视前面随机的美国节点），干脆也将其加入随机
    ['https://ghproxy.net/https://github.com', '英国', '[英国伦敦] - 该公益加速源由 [ghproxy.net] 提供提示：希望大家尽量多使用美国节点（每次随机 负载均衡），避免流量都集中到亚洲公益节点，减少成本压力，公益才能更持久~'],
    ['https://ghfast.top/https://github.com', '其他', '[日本、韩国、新加坡、美国、德国等]（CDN 不固定） - 该公益加速源由 [ghproxy.link] 提供提示：希望大家尽量多使用美国节点（每次随机 负载均衡），避免流量都集中到亚洲公益节点，减少成本压力，公益才能更持久~'],
    ['https://wget.la/https://github.com', '其他', '[中国香港、中国台湾、日本、美国等]（CDN 不固定） - 该公益加速源由 [ucdn.me] 提供提示：希望大家尽量多使用美国节点（每次随机 负载均衡），避免流量都集中到亚洲公益节点，减少成本压力，公益才能更持久~'],
    ['https://kkgithub.com', '其他', '[中国香港、日本、韩国、新加坡等] - 该公益加速源由 [help.kkgithub.com] 提供提示：希望大家尽量多使用美国节点（每次随机 负载均衡），避免流量都集中到亚洲公益节点，减少成本压力，公益才能更持久~'],
]
shuffle(MIRROR_DL)
MIRROR_CLONE = [
    ['https://gitclone.com', '国内', '[中国 国内] - 该公益加速源由 [GitClone] 提供 - 缓存：有 - 首次比较慢，缓存后较快'],
    ['https://kkgithub.com', '香港', '[中国香港、日本、新加坡等] - 该公益加速源由 [help.kkgithub.com] 提供'],
    ['https://ghfast.top/https://github.com', '韩国', '[日本、韩国、新加坡、美国、德国等]（CDN 不固定） - 该公益加速源由 [ghproxy] 提供'],
    ['https://githubfast.com', '韩国', '[韩国] - 该公益加速源由 [Github Fast] 提供'],
    ['https://ghproxy.net/https://github.com', '日本', '[日本 大阪] - 该公益加速源由 [ghproxy.net] 提供'],
]
shuffle(MIRROR_CLONE)
MIRROR_PYPI = [
    'https://pypi.tuna.tsinghua.edu.cn/simple',  # 清华
    'https://mirrors.aliyun.com/pypi/simple',  # 阿里云
    'http://pypi.hustunique.com/simple',  # 华中科技大学
    'http://mirrors.cloud.tencent.com/pypi/simple/',  # 腾讯云
    'https://pypi.mirrors.ustc.edu.cn/simple/',  # 中国科学技术大学
]
MIRROR_CONDA = [
    {
        'main': [
            'https://mirrors.ustc.edu.cn/anaconda/pkgs/main',
            'https://mirrors.ustc.edu.cn/anaconda/pkgs/r',
            'https://mirrors.ustc.edu.cn/anaconda/pkgs/msys2'
        ],
        # 'conda-forge': ['https://mirrors.ustc.edu.cn/anaconda/cloud'],
        # 'bioconda': ['https://mirrors.ustc.edu.cn/anaconda/cloud'],
    }
]


def run(cmd, timeout=15 * 60, log=True):
    Log.info(f'run❯ {cmd}') if log else None
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    p.stdout = p.stdout.strip()
    p.stderr = p.stderr.strip()
    if log:
        Log.info(p.stdout) if p.stdout else None
        Log.error(p.stderr) if p.stderr else None
        Log.debug(p.returncode) if p.returncode != 0 else None
    return p


def call(cmd):
    Log.info(f'call❯ {cmd}')
    return os.system(cmd)


def mirror_clone(url: str | None = None):
    if url is None:
        url = MIRROR_CLONE.pop(0)[0]
    call(f'git config --system  url."{url}/".insteadOf "https://github.com"')
    call(f'git config --system  url."{url}/".insteadOf "git@github.com:"')


def mirror_pypi(url: str | None = None):
    if url is None:
        url = MIRROR_PYPI.pop(0)
    call(f'pip config set global.index-url {url}')
    call(f'pip config set global.trusted-host {url.split("://")[1].split("/")[0]}')


def mirror_conda(urls: dict | None = None):
    call(f'{MAMBA} clean -i')
    if urls is None:
        urls = MIRROR_CONDA[0]
    main: list[str] = urls.pop('main', [])
    custom: dict[str, list[str]] = urls
    for url in main:
        call(f'{MAMBA} config prepend channels {url}')
    for channel, _urls in custom.items():
        for url in _urls:
            call(f'{MAMBA} config prepend channels {url}')


def mirror():
    Log.info("🔍 Checking mirrors...")
    try:
        with urlopen('https://www.google.com', timeout=3) as response:
            if response.status != 200:
                raise Exception("Google is not reachable")
            else:
                MIRROR_DL.insert(0, ['https://github.com', '美国', '[官方Github]'])
    except:
        global IS_MIRROR
        IS_MIRROR = True
        mirror_clone()
        mirror_pypi()
        # mirror_conda()


def dl_progress(count, block_size, total_bytes):
    global LAST_SPEED, LAST_TIME, BEGIN_TIME, START_SLOW_TIME
    N = 1024**2  # 1 MB
    block_size_mb = block_size / N
    total_mb = total_bytes / N if total_bytes > 0 else -1
    done = count * block_size_mb

    cur_time = time()
    elapsed = cur_time - BEGIN_TIME
    current_speed = done / elapsed if elapsed > 0 else -1

    # 指数加权平均平滑速度
    alpha = 0.8
    if current_speed > 0:
        LAST_SPEED = alpha * LAST_SPEED + (1 - alpha) * current_speed
    else:
        LAST_SPEED *= alpha  # 无数据时衰减历史速度

    # 计算剩余时间（基于平滑速度）
    remain_mb = total_mb - done
    remain_sec = remain_mb / LAST_SPEED if LAST_SPEED > 1e-6 else float('inf')

    # 每1秒更新一次日志
    if cur_time - LAST_TIME > 1:
        LAST_TIME = cur_time
        if total_bytes > 0:
            percent = done * 100 / total_mb if total_mb > 0 else 0
            if percent >= 100:
                msg = f"✔ Downloaded {total_mb:.2f} MB"
            else:
                msg = f"⬇ Downloading: {percent:.1f}% @ {LAST_SPEED:.2f}MB/s\t🕒 {remain_sec / 60:.2f}min\t({done:.1f}/{total_mb:.1f} MB)"
        else:
            msg = f"⬇ Downloading: {done:.2f} MB"
        print(f'{_SLASH_R}{msg}', end=_SLASH_N)
        sys.stdout.flush()

    # 限速判断
    SLOW_SPEED = 0.5  # 可调整的低速阈值（MB/s）
    if elapsed > TIMEOUT:  # 连接稳定后开始判断
        if LAST_SPEED < SLOW_SPEED:
            # 记录首次进入低速的时间
            if START_SLOW_TIME is None:
                START_SLOW_TIME = cur_time
            # 持续低速超过阈值时间则触发重试
            elif cur_time - START_SLOW_TIME > TIMEOUT:
                START_SLOW_TIME = None
                raise Exception(f"🐌 Too slow, speed={LAST_SPEED:.2f}MB/s < {SLOW_SPEED}MB/s for {TIMEOUT}s.")
        else:
            START_SLOW_TIME = None


def download(from_url: str, to_path: str | None = None, log=True):
    global BEGIN_TIME
    Log.info(f"🔍 Download from {from_url}") if log else None
    BEGIN_TIME = time()
    filename, http_headers = urlretrieve(from_url, filename=to_path, reporthook=dl_progress)
    return filename, http_headers


def get_envs(manager='mamba'):
    """
    Args:
        manager (str): 'mamba', 'conda', 'pip'
        kwargs (dict): `subprocess.Popen()` args

    Returns:
        env (dict): eg: {'base': '~/miniforge3'}
        now (str): currently env name like 'base'
    """
    p = run(f'{manager} env list', log=not IS_DEBUG)
    _env = p.stdout.splitlines()[2:]
    _env = [l.split() for l in _env if l]   # type: ignore
    env = {l[0]: l[1 if len(l) == 2 else 2] for l in _env}
    now = str(os.getenv('CONDA_DEFAULT_ENV'))
    return env, now


def get_latest_release_tag(owner='conda-forge', repo='miniforge') -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['tag_name']
    except Exception as e:
        return '25.3.0-3'   # 2025-6-2


def i_mamba():
    if shutil.which('mamba'):
        Log.info("✅ Mamba is already installed.")
        return
    Log.info("📦 Install Mamba")
    if is_win:
        setup = "Miniforge3-Windows-x86_64.exe"
    else:
        p = run("echo Miniforge3-$(uname)-$(uname -m).sh")
        setup = p.stdout
    if os.path.exists(setup):
        mamba_exe(setup)
        if not os.path.exists(MAMBA):
            os.remove(setup)  # remove broken setup
    if not os.path.exists(MAMBA):
        tag = get_latest_release_tag()
        url = f"/conda-forge/miniforge/releases/download/{tag}/"
        url += setup
        for m in MIRROR_DL:
            _url = m[0] + url
            Log.info(f"🔍 From {_url} ({m[-1]})")
            try:
                setup, _ = download(_url, setup, log=False)
                break
            except Exception as e:
                Log.warning(f"Skip: {e}")
        if not os.path.exists(setup):
            raise FileNotFoundError(f"Download failed: {setup}")
        mamba_exe(setup)


def mamba_exe(setup, cleanup=not IS_DEBUG):
    if is_win:
        p = run(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3')
    else:
        p = run(f'bash "{setup}" -b')
    _prefix = RE['mamba_prefix'].search(p.stdout)
    if _prefix:
        prefix: str = _prefix.group(1).strip()
        global MAMBA, CONDA
        MAMBA = os.path.join(prefix, 'condabin', 'mamba')
        CONDA = os.path.join(prefix, 'condabin', 'conda')
    if cleanup:
        os.remove(setup)
    return p.returncode


def i_micromamba():
    Log.info("📦 Install Micro-mamba")
    if is_win:
        run('Invoke-Expression ((Invoke-WebRequest -Uri https://micro.mamba.pm/install.ps1 -UseBasicParsing).Content)')
    else:
        run(r'"${SHELL}" <(curl -L micro.mamba.pm/install.sh)')
    symlink(MAMBA, '/bin/mamba') if not is_win else None  # TODO: mac?
    os.link('micromamba', 'mamba')


def symlink(src: str, dst: str, is_src_dir=False, overwrite=True,
            *args, dir_fd: int | None = None):
    Log.debug(f'🔗 {src} → {dst}')
    try:
        if overwrite and os.path.exists(dst):
            os.remove(dst)
        os.symlink(src=src, dst=dst, target_is_directory=is_src_dir, *args, dir_fd=dir_fd)
        return dst
    except:
        return None


def i_mocap():
    if shutil.which('mocap'):
        Log.info("✅ Mocap is already installed.")
        return
    try:
        if (envs_now := get_envs(MAMBA)):
            envs, now = envs_now
            if ENV not in envs.keys():
                raise FileNotFoundError(f"Environment '{ENV}' not found.")
    except:
        if ENV != 'base':
            p = run(f'python --version')
            version = RE['python'].search(p.stdout)
            if not version:
                version = '3.13'    # TODO: 2025-6-2
            else:
                version = version.groups()
                version = '.'.join(version)
            p = run(f"{MAMBA} create -n {ENV} python={version} -y")    # python-freethreading # don't install in `base`

    envs, _ = get_envs(MAMBA)
    py_bin = os.path.join(envs[ENV], 'bin')
    PY = ['pip', 'python']
    PY = {p: os.path.join(py_bin, p) for p in PY}
    if IS_MIRROR:
        github = 'gitee'
    else:
        github = 'github'
    if IS_DEBUG:
        tag = '[dev]'
    else:
        tag = ''
    for i in range(5):
        p = run(f'{PY["pip"]} install "{__package__}{tag} @ git+https://{github}.com/AClon314/mocap-wrapper.git"')
        error = p.stderr.lower()
        if p.returncode == 0:
            break
        elif any([kw in error for kw in ('network', 'git clone')]):
            mirror_clone() if 'git clone' in error else None
            mirror_pypi() if 'network' in error else None
            continue
        else:
            raise Exception(f"Failed to install python package.")
    mocap = os.path.join(os.path.dirname(PY['pip']), 'mocap')
    symlink(mocap, '/bin/mocap') if not is_win else None
    Log.debug(f'{p.__dict__=}')
    # os.makedirs('mocap', exist_ok=True)
    # os.chdir('mocap')
    mocap = shutil.which('mocap')
    if mocap is None:
        raise FileNotFoundError("mocap executable not found.")


def get_shell():
    p = run('ps -p $$', log=False)
    shell = p.stdout.splitlines()[1].split()[-1]
    return shell


if __name__ == "__main__":
    if not any([is_win, is_mac, is_linux]):
        Log.warning(f"❓ Unsupported OS={sys.platform}")
    socket.setdefaulttimeout(TIMEOUT)
    if not all([shutil.which(exe) for exe in ('mamba', 'mocap')]):
        mirror()
    i_mamba()
    i_mocap()
    os.execvp('mocap', ["--version"])  # -I

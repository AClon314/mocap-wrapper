#!/bin/env python
'''
# this script will set git/pip mirrors, install mamba, mocap-wrapper.
curl https://raw.githubusercontent.com/AClon314/mocap-wrapper/refs/heads/master/src/mocap_wrapper/script/mamba.py | python
'''
import os
import re
import sys
import json
import socket
import shutil
import logging
import argparse
import subprocess
from time import time
from typing import Literal
from urllib.request import urlretrieve, urlopen
from site import getuserbase
from mirror_cn.mirror import GITHUB_RELEASE, is_need_mirror, global_git, global_pip, Shuffle
IS_DEBUG = os.getenv('GITHUB_ACTIONS', None) or os.getenv('LOG', None)
__package__ = 'mocap_wrapper'
_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO
_SLASH_R = r'\r\033[K' if IS_DEBUG else ''
_SLASH_N = '\n' if IS_DEBUG else ''
logging.basicConfig(level=_LEVEL, format='[%(asctime)s %(levelname)s] %(filename)s:%(lineno)s\t%(message)s', datefmt='%d-%H:%M:%S')
Log = logging.getLogger(__name__)
is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')
is_linux = sys.platform.startswith('linux')
if is_win:
    BIN = r'C:\\Windows\\System32'  # TODO: dirty but working
else:
    BIN = os.path.join(getuserbase(), 'bin') if os.getuid() != 0 else '/usr/local/bin'
ENV = 'base' if IS_DEBUG else 'nogil'
FOLDER = 'mocap'
MAMBA = '/root/miniforge3/bin/mamba'
CONDA = '/root/miniforge3/bin/conda'
TIMEOUT = 12
SLOW_SPEED = 0.5  # MB/s
_RE = {
    'mamba_prefix': 'PREFIX=(.*)\n',
    'python': r'Python (\d+).(\d+)',
}
RE = {k: re.compile(v) for k, v in _RE.items()}


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


def dl_progress(begin_time: float, filename: str = '', log: bool = True):
    """创建一个带有局部状态的下载进度回调函数"""
    last_speed = 0.0
    last_time = begin_time - 1
    start_slow_time = None

    def progress(count, block_size, total_bytes):
        nonlocal last_speed, last_time, start_slow_time

        N = 1024**2  # 1 MB
        block_size_mb = block_size / N
        total_mb = total_bytes / N if total_bytes > 0 else -1
        done = count * block_size_mb

        cur_time = time()
        elapsed = cur_time - begin_time
        current_speed = done / elapsed if elapsed > 0 else -1

        # 指数加权平均平滑速度
        alpha = 0.8
        if current_speed > 0:
            last_speed = alpha * last_speed + (1 - alpha) * current_speed
        else:
            last_speed *= alpha  # 无数据时衰减历史速度

        # 计算剩余时间（基于平滑速度）
        remain_mb = total_mb - done
        remain_sec = remain_mb / last_speed if last_speed > 1e-6 else float('inf')

        # 每1秒更新一次日志
        if log and cur_time - last_time > 1:
            last_time = cur_time
            if total_bytes > 0:
                percent = done * 100 / total_mb if total_mb > 0 else 0
                if percent >= 100:
                    msg = f"✔ Downloaded {total_mb:.2f} MB"
                else:
                    msg = f"⬇ Downloading: {percent:.1f}% @ {last_speed:.2f}MB/s\t🕒 {remain_sec / 60:.2f}min\t({done:.1f}/{total_mb:.1f} MB)"
            else:
                msg = f"⬇ Downloading: {done:.2f} MB"

            if filename:
                msg = f"{msg}\t{filename}"
            print(f'{_SLASH_R}{msg}', end=_SLASH_N, flush=True)

        # 限速判断
        if elapsed > TIMEOUT:  # 连接稳定后开始判断
            if last_speed < SLOW_SPEED:
                # 记录首次进入低速的时间
                if start_slow_time is None:
                    start_slow_time = cur_time
                # 持续低速超过阈值时间则触发重试
                elif cur_time - start_slow_time > TIMEOUT:
                    start_slow_time = None
                    raise Exception(f"🐌 Too slow, speed={last_speed:.2f}MB/s < {SLOW_SPEED}MB/s for {TIMEOUT}s.")
            else:
                start_slow_time = None

    return progress


def download(from_url: str, to_path: str | None = None, log=True):
    Log.info(f"🔍 Download from {from_url}") if log else None
    filename = os.path.basename(to_path if to_path else from_url)
    filename, http_headers = urlretrieve(
        from_url, filename=to_path,
        reporthook=dl_progress(begin_time=time(), filename=filename, log=log))
    return filename, http_headers


def get_envs(manager: Literal['mamba', 'conda'] = 'mamba'):
    """
    Args:
        manager (str): 'mamba', 'conda'
        kwargs (dict): `subprocess.Popen()` args

    Returns:
        env (dict): eg: {'base': '~/miniforge3'}
        now (str): currently env name like 'base'
    """
    p = run(f'{manager} env list --json', log=False)
    _envs: list = json.loads(p.stdout)['envs']
    env = {os.path.split(v)[-1]: v for v in _envs}
    p = run(f'{manager} info --json', log=False)
    _info = json.loads(p.stdout)
    _prefix = ''
    if manager.endswith('mamba'):
        _prefix = 'miniforge3'
        now = _info['environment']
    elif manager.endswith('conda'):
        _prefix = 'miniconda3'
        now = _info['active_prefix_name']
    else:
        raise ValueError(f"Unsupported manager: {manager}. Use 'mamba' or 'conda'.")
    env['base'] = env[_prefix]
    env.pop(_prefix)
    return env, now


def get_latest_release_tag(owner='conda-forge', repo='miniforge') -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['tag_name']
    except Exception as e:
        tag = '25.3.0-3'   # 2025-6-2
        Log.warning(f"Failed to fetch latest release tag, fallback to {tag}: {e}")
        return tag


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
        p = mamba_exe(setup)
        if 'md5sum mismatch' in p.stderr:
            os.remove(setup)  # remove broken setup
        else:
            return
    tag = get_latest_release_tag()
    url = f"/conda-forge/miniforge/releases/download/{tag}/"
    url += setup
    for m in GITHUB_RELEASE:
        _url = m[0] + url
        Log.info(f"🔍 From {_url} ({m[-1]})")
        try:
            setup, _ = download(_url, setup, log=False)
            break
        except Exception as e:
            Log.warning(f"Skip: {e}")
    if not os.path.exists(setup):
        raise FileNotFoundError(f"Download: {setup}")
    mamba_exe(setup)


def mamba_exe(setup, cleanup=not IS_DEBUG):
    if is_win:
        p = run(f'start /wait "" {setup} /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\\Miniforge3')
    else:
        p = run(f'bash "{setup}" -b')
    global_mamba_path(p.stdout)
    if cleanup:
        os.remove(setup)
    symlink(MAMBA, os.path.join(BIN, 'mamba')) if not is_win else None  # TODO: mac?
    return p


def global_mamba_path(output: str):
    _prefix = RE['mamba_prefix'].search(output)
    if _prefix:
        prefix: str = _prefix.group(1).strip()
        global MAMBA, CONDA
        MAMBA = os.path.join(prefix, 'bin', 'mamba')
        CONDA = os.path.join(prefix, 'bin', 'conda')
    else:
        raise ValueError(f"Failed to parse mamba prefix from output: {output}")


def i_micromamba():
    Log.info("📦 Install Micro-mamba")
    if is_win:
        p = run('Invoke-Expression ((Invoke-WebRequest -Uri https://micro.mamba.pm/install.ps1 -UseBasicParsing).Content)')
    else:
        p = run(r'"${SHELL}" <(curl -L micro.mamba.pm/install.sh)')
    global_mamba_path(p.stdout)
    symlink(MAMBA, os.path.join(BIN, 'mamba')) if not is_win else None


def symlink(src: str, dst: str, is_src_dir=False, overwrite=True,
            *args, dir_fd: int | None = None):
    Log.debug(f'🔗 symlink {src} → {dst}')
    if not os.path.exists(src):
        Log.error(f"{src=} does NOT exist.")
        return None
    dst_dir = dst if os.path.isdir(dst) else os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    try:
        if overwrite and os.path.exists(dst):
            os.remove(dst)
        os.symlink(src=src, dst=dst, target_is_directory=is_src_dir, *args, dir_fd=dir_fd)
        return dst
    except Exception as e:
        Log.error(f"symlink: {e}")
        return None


def i_mocap():
    if shutil.which('mocap'):
        Log.info("⚠️ Reinstall mocap")
    try:
        if (envs_now := get_envs(MAMBA)):
            envs, now = envs_now
            if ENV not in envs.keys():
                raise FileNotFoundError(f"Environment '{ENV}' not found.")
    except:
        if ENV != 'base':
            p = run(f"{MAMBA} create -n {ENV} python-freethreading -y")  # don't install in `base`

    envs, _ = get_envs(MAMBA)
    py_bin = os.path.join(envs[ENV], 'bin')
    PY = ['pip', 'python']
    PY = {p: os.path.join(py_bin, p) for p in PY}
    tag = '[dev]' if IS_DEBUG else ''
    if IS_DEBUG:
        pkg = f'-e ".[dev]"'
    else:
        github = 'gitee' if IS_MIRROR else 'github'
        url = f'git+https://{github}.com/AClon314/mocap-wrapper.git'
        pkg = f'"{__package__}{tag} @ {url}"'
    for i in range(5):
        p = run(f'{PY["pip"]} install {pkg}')
        error = p.stderr.lower()
        if p.returncode == 0:
            break
        elif any([kw in error for kw in ('network', 'git clone')]):
            global_git() if 'git clone' in error else None
            global_pip() if 'network' in error else None
            continue
        else:
            raise Exception(f"Failed to install python package.")
    mocap = os.path.join(os.path.dirname(PY['pip']), 'mocap')
    symlink(mocap, os.path.join(BIN, 'mocap')) if not is_win else None
    # Log.debug(f'{p.__dict__=}')
    # os.makedirs('mocap', exist_ok=True)
    # os.chdir('mocap')
    mocap = shutil.which('mocap')
    if mocap is None:
        raise FileNotFoundError("mocap executable not found.")


def get_shell():
    p = run('ps -p $$', log=False)
    shell = p.stdout.splitlines()[1].split()[-1]
    return shell


def set_timeout(timeout: int = TIMEOUT):
    global TIMEOUT
    TIMEOUT = timeout
    socket.setdefaulttimeout(TIMEOUT)


def argParse():
    parser = argparse.ArgumentParser(description='Install mamba & mocap-wrapper script. mamba和mocap-wrapper的预安装脚本。')
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompts. 无人值守，跳过确认提示。')
    args = parser.parse_args()
    if not args.yes:
        confirm = input("Install mamba as python env manager, and mocap-wrapper? (y/N): ").strip().lower()
        if confirm != 'y':
            Log.info("Installation cancelled.")
            sys.exit(0)


def main():
    msg = f'Run `mamba activate {ENV}` and `mocap --install -b wilor,gvhmr` to continue!'
    Log.debug(f'{os.environ=}')
    if not any([is_win, is_mac, is_linux]):
        Log.warning(f"❓ Unsupported OS={sys.platform}")
    # get_args()
    Shuffle()
    socket.setdefaulttimeout(TIMEOUT)
    is_need_mirror()
    i_mamba()
    i_mocap()
    Log.info(f"✅ {msg}`")
    # os.execvp('mocap', ['mocap', '--install'])


if __name__ == "__main__":
    i_mamba()
    main()

#!/bin/env python
'''
# this script will set git/pip mirrors, install mamba, mocap-wrapper.
curl https://raw.githubusercontent.com/AClon314/mocap-wrapper/refs/heads/master/src/mocap_wrapper/install/mamba.py | python
'''
import os
import re
import sys
import json
import socket
import shlex
import shutil
import logging
import argparse
import subprocess
from time import time
from site import getuserbase
from urllib.request import urlretrieve, urlopen
from typing import Iterable, Literal, Sequence

from mirror_cn.mirror_cn import try_script
IS_DEBUG = os.getenv('GITHUB_ACTIONS', None) or os.getenv('LOG', None)
__package__ = 'mocap_wrapper'
_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO
_SLASH_R = r'\r\033[K' if IS_DEBUG else ''
_SLASH_N = '\n' if IS_DEBUG else ''
_SELF = os.path.abspath(__file__)
_SELF_DIR = os.path.dirname(_SELF)
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
TIMEOUT = 12
SLOW_SPEED = 0.5  # MB/s
_RE = {
    'python': r'Python (\d+).(\d+)',
}
RE = {k: re.compile(v) for k, v in _RE.items()}
_ID = 0
def _shlex_quote(args: Iterable[str]): return ' '.join(shlex.quote(str(arg)) for arg in args)
def _get_cmd(cmds: Iterable[str] | str): return cmds if isinstance(cmds, str) else _shlex_quote(cmds)
def _strip(s: str): return s.strip() if s else ''


def call(cmd: Sequence[str] | str, Print=True):
    '''⚠️ Strongly recommended use list[str] instead of str to pass commands, 
    to avoid shell injection risks for online service.'''
    global _ID
    _ID += 1
    prefix = f'{cmd[0]}_{_ID}'
    cmd = _get_cmd(cmd)
    Log.info(f'{prefix}🐣❯ {cmd}') if Print else None
    try:
        process = subprocess.run(cmd, shell=True, text=True, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        process = e
    if Print:
        stdout = _strip(process.stdout)
        stderr = _strip(process.stderr)
        Log.info(f'{prefix}❯ {stdout}') if stdout else None
        Log.error(f'{prefix}❯ {stderr}') if stderr else None
    return process


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


def download(
    from_url: str, to_path: str | None = None,
    if_exist: Literal['override', 'skip'] = 'skip', log=True
):
    filename = os.path.basename(to_path if to_path else from_url)
    if if_exist == 'skip' and to_path and os.path.exists(to_path):
        Log.info(f"🔍❗ Already exists at {to_path}: {from_url}") if log else None
        return filename, {}
    Log.info(f"🔍 Download from {from_url}") if log else None
    filename, http_headers = urlretrieve(
        from_url, filename=to_path,
        reporthook=dl_progress(begin_time=time(), filename=filename, log=log))
    return filename, http_headers


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


def get_argv():
    """fallback to sys.argv if fails"""
    import shlex
    try:
        import shlex
        if is_win:
            result = subprocess.run(
                ['wmic', 'process', 'where', f'processid={os.getpid()}', 'get', 'commandline', '/value'],
                capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if line.startswith('CommandLine='):
                    cmdline = line[12:].strip()
                    if cmdline:
                        return shlex.split(cmdline)
        else:
            result = subprocess.run(
                ['ps', '-p', str(os.getpid()), '-o', 'args='],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                cmdline = result.stdout.strip()
                if cmdline:
                    # 使用shlex正确处理引号和转义
                    return shlex.split(cmdline)
    except Exception as e:
        print(f"{e}")
    # 回退到标准方式
    return sys.argv


_ARGV = get_argv()
if 'python' in _ARGV[0]:
    _PYTHON = _ARGV[0]
else:
    _PYTHON = 'python'
    _ARGV.insert(0, _PYTHON)
try:
    from mirror_cn import is_need_mirror, global_pixi, global_git, Shuffle, try_script
except ImportError:
    _py_path = os.path.join(_SELF_DIR, 'mirror_cn.py')
    if os.path.exists(_py_path):
        raise
    Log.debug('❗ mirror_cn module not found, fixing...')
    download('https://gitee.com/aclon314/mirror-cn/raw/main/src/mirror_cn/mirror_cn.py', _py_path)
    os.execvp(_PYTHON, _ARGV)


def i_pixi():
    if shutil.which('pixi') and not IS_MIRROR:
        return call(['pixi', 'self-update'])
    _ext = 'ps1' if is_win else 'sh'
    _file = f'install.{_ext}'
    url = f'https://pixi.sh/{_file}'
    file, _ = download(url, to_path=_file)
    Log.info(f'{file=}')
    tag = get_latest_release_tag()
    os.environ['PIXI_VERSION'] = tag
    for p in try_script(os.path.join('.', file)):
        if p.returncode == 0:
            break
    path = re.search(r"is installed into '(/.*?)'", p.stdout)
    path = path.group(1) if path else None
    if not path:
        assert False, "Failed to extract path from stdout"
    Log.info(f'{path=}')
    # warn: Could not detect shell type.
    # Please permanently add '/root/.pixi/bin' to your $PATH to enable the 'pixi' command.
    if p and 'PATH' in p.stderr:
        _export = f'export PATH=$PATH:{path}'
        _bashrc = os.path.expanduser('~/.bashrc')
        if os.path.exists(_bashrc):
            with open(_bashrc, 'r') as f:
                content = f.read()
            if _export not in content:
                Log.info(f'Adding to {_bashrc}: {_export}')
        with open(_bashrc, 'a') as f:
            f.write(f'\n{_export}\n')
    if not os.path.exists(path):
        assert False, "Failed to install pixi"
    Log.info(f"✅ pixi installed: {file}")
    return p


def i_uv():
    if not shutil.which('pixi'):
        raise Exception("pixi is not installed")
    p = call(['pixi', 'global', 'install', 'uv'])  # install uv
    if (uv := shutil.which('uv')) or p.returncode == 0:
        Log.info(f"✅ uv installed: {uv=}\t{p.returncode=}")


def i_mocap():
    if not shutil.which('uv'):
        raise Exception("uv is not installed")
    if shutil.which('mocap'):
        Log.info("⚠️ Reinstall mocap")
    git = 'https://gitee.com/AClon314/mocap-wrapper' if IS_MIRROR else 'https://github.com/AClon314/mocap-wrapper'
    p = call(['uv', 'pip', 'install', f'git+{git}'])
    if (mocap := shutil.which('mocap')) or p.returncode == 0:
        Log.info(f"✅ mocap installed: {mocap=}\t{p.returncode=}")


def set_timeout(timeout: int = TIMEOUT):
    global TIMEOUT
    TIMEOUT = timeout
    socket.setdefaulttimeout(TIMEOUT)


def is_post_install():
    parser = argparse.ArgumentParser(description=f'Pre-install script for {__package__}. {__package__}的预安装脚本。')
    parser.add_argument('-y', action='store_true', help='⭐ Unattended, only pre-install. 无人值守，仅预安装。')
    parser.add_argument('--yes', action='store_true', help='Unattended, will run `mocap --install` after pre-install. 无人值守，预安装后将运行 `mocap --install`。')
    args = parser.parse_args()
    if not (args.y or args.yes):
        confirm = input("Install pixi & uv as python env manager, and mocap-wrapper? (y/N): ").strip().lower()
        if confirm != 'y':
            sys.exit(0)
    elif args.yes:
        return True
    return False


def main():
    global IS_MIRROR
    msg = f'Run `mocap --install -b wilor,gvhmr` to continue!'
    Log.debug(f'{os.environ=}')
    IS_POST_INSTALL = is_post_install()
    Shuffle()
    set_timeout()
    IS_MIRROR = is_need_mirror()
    if IS_MIRROR:
        global_git()
    i_pixi()
    i_uv()
    i_mocap()
    if IS_POST_INSTALL:
        os.execvp('mocap', ['mocap', '--install'])
    else:
        Log.info(f"✅ {msg}`")


if __name__ == "__main__":
    main()

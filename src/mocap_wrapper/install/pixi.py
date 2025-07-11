#!/bin/env python
'''
# this script will set git/pip mirrors, install mamba, mocap-wrapper.
curl https://raw.githubusercontent.com/AClon314/mocap-wrapper/refs/heads/master/src/mocap_wrapper/install/mamba.py | python
# TODO: because `pixi global install` does NOT support install as **editable** pypi package, so we have to use `uv pip install -e .`
'''
if __name__ != '__main__':
    raise ImportError("This installation script must be run directly, not imported as a module.")
import os
import re
import sys
import socket
import shutil
import logging
import argparse
import subprocess
from time import time
from locale import getdefaultlocale
from urllib.request import urlretrieve
from typing import Literal
IS_DEBUG = os.getenv('GITHUB_ACTIONS', None) or os.getenv('LOG', None)
IS_MIRROR = None
SEARCH_DIR = 'mocap'
TIMEOUT = 12
SLOW_SPEED = 0.5  # MB/s
_pkg_ = __package__ or 'mocap_wrapper'
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
MIRROR_CN_PY = 'https://gitee.com/aclon314/mirror-cn/raw/main/src/mirror_cn/mirror_cn.py' if getdefaultlocale()[0] == 'zh_CN' else 'https://raw.githubusercontent.com/AClon314/mirror-cn/main/src/mirror_cn/mirror_cn.py'
_HOME = os.path.expanduser('~')
PIXI_BIN = os.getenv('PIXI_BIN', None) or os.path.join(_HOME, '.pixi', 'bin')
VENV = os.path.join(_HOME, '.venv')
os.environ['PATH'] = os.pathsep.join([os.getenv('PATH', ''), PIXI_BIN, os.path.join(VENV, 'bin')])
_BIN_PYTHON = os.sep.join(sys.executable.split(os.sep)[-2:])
_RE = {
    'python': r'Python (\d+).(\d+)',
}
RE = {k: re.compile(v) for k, v in _RE.items()}


def system(args: list):
    cmd = ' '.join(args)
    Log.info(f'{cmd=}')
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


def download(
    from_url: str, to_path: str | None = None,
    if_exist: Literal['override', 'skip'] = 'skip', log=True
):
    filename = os.path.basename(to_path if to_path else from_url)
    if if_exist == 'skip' and to_path and os.path.exists(to_path):
        Log.info(f"🔍❗ Already exists at {to_path}: {from_url}") if log else None
        return filename, {}
    Log.info(f"🔍 Download: {from_url}") if log else None
    filename, http_headers = urlretrieve(
        from_url, filename=to_path,
        reporthook=dl_progress(begin_time=time(), filename=filename, log=log))
    return filename, http_headers


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
    from mirror_cn import is_need_mirror, global_git, global_pixi, global_uv, get_latest_release_tag, try_script, run
except (ImportError, SyntaxError) as e:
    if 'mirror_cn' not in str(e):
        raise
    _py_path = os.path.join(_SELF_DIR, 'mirror_cn.py')
    if os.path.exists(_py_path):
        os.remove(_py_path)
    download(MIRROR_CN_PY, _py_path)
    os.execvp(_PYTHON, _ARGV)


def i_pixi():
    global PIXI_BIN
    if shutil.which('pixi'):
        if IS_MIRROR:
            Log.warning('Skip pixi self-update')
            return 0
        return system(['pixi', 'self-update'])
    Log.debug(f'{shutil.which("pixi")=}\t{locals()=}')
    _ext = 'ps1' if is_win else 'sh'
    _file = f'install.{_ext}'
    url = f'https://pixi.sh/{_file}'
    file, _ = download(url, to_path=_file)
    Log.info(f'{file=}')
    if os.environ.get('PIXI_VERSION', None) is None:
        try:
            tag = get_latest_release_tag('prefix-dev/pixi')
        except Exception as e:
            tag = 'v0.49.0'  # https://github.com/prefix-dev/pixi/releases: 2025/07/02
            Log.warning(f'Fallback to {tag=}, {e}')
        os.environ['PIXI_VERSION'] = tag
    for p in try_script(os.path.join('.', file)):
        if p.returncode == 0:
            break
    pixi_bin = re.search(r"is installed into '(.*?)'", p.stdout)
    pixi_bin = pixi_bin.group(1) if pixi_bin else None
    PIXI_BIN = pixi_bin or PIXI_BIN  # pixi_bin if pixi_bin else PIXI_BIN
    os.environ['PATH'] = os.pathsep.join([PIXI_BIN, os.getenv('PATH', '')])
    if not os.path.exists(PIXI_BIN):
        raise Exception(f"Post check failed, {PIXI_BIN=} does not exist.")
    system('pixi config set --global run-post-link-scripts insecure'.split())
    Log.info(f"✅ pixi installed in: {PIXI_BIN=}")
    return p


def i_uv():
    if not shutil.which(os.path.join(PIXI_BIN, 'pixi')):
        raise Exception("pixi is not installed")
    global_pixi() if IS_MIRROR else None
    if not shutil.which('uv'):
        returncode = system(['pixi', 'global', 'install', 'uv'])  # install uv
        if (UV := shutil.which('uv')) or returncode == 0:
            Log.info(f"✅ uv installed: {UV=}\t{returncode=}")

    global_uv() if IS_MIRROR else None
    while (ret := system(['uv', 'python', 'install', '-v'])) and ret != 0:
        if IS_MIRROR:
            global_uv()
    ret = system(['uv', 'venv', VENV])
    PYTHON = os.path.join(VENV, _BIN_PYTHON)
    if os.path.exists(PYTHON):
        Log.info(f"✅ uv global .venv installed: {PYTHON=}")


def i_mocap():
    if not shutil.which('uv'):
        raise Exception("uv is not installed")
    if shutil.which('mocap'):
        Log.info("⚠️ Reinstall mocap")

    os.environ['UV_PYTHON'] = os.path.join(VENV, _BIN_PYTHON)
    git = 'https://gitee.com/AClon314/mocap-wrapper' if IS_MIRROR else 'https://github.com/AClon314/mocap-wrapper'
    install = ['-e', '.[dev]'] if os.getcwd().endswith(_pkg_.replace('_', '-')) else [f'git+{git}']
    # _v = ['-v'] if IS_DEBUG else []
    ret = system(['uv', 'pip', 'install', *install])
    if (mocap := shutil.which('mocap')) and ret == 0:
        Log.info(f"✅ mocap installed: {mocap=}\t{ret=}")


def set_shell_init_venv_PATH():
    '''. ~/.venv/bin/activate && export PATH=... > ~/.profile ; source ~/.profile > ~/.bashrc, ~/.zshrc, ~/.xonshrc'''
    Log.info('Setup activate venv/PATH in shell profile...')
    if is_win:
        _activate = r'~\.venv\Scripts\activate'  # .venv\Scripts\activate
        p = run(['powershell', '-Command', '$PROFILE.AllUsersCurrentHost'])
        profile = p.stdout.strip()
        os.makedirs(os.path.dirname(profile), exist_ok=True)
        script = rf'''if (Test-Path "{_activate}") {{
    & "{_activate}"
}}
'''
        write(script, profile)
        return _activate
    _activate = '. ~/.venv/bin/activate'
    _export = f'export PATH="$PATH:{PIXI_BIN}:$HOME/.venv/bin"'
    profile = os.path.expanduser(f'~/.profile')
    _source = f'. {profile}'   # because re-source ~/.bashrc would break some ENV, and usually ~/.profile is simple.
    write('\n'.join([_activate, _export]), profile)

    shells = [_sh for _sh in ['bash', 'zsh', 'xonsh'] if shutil.which(_sh)]
    for sh in shells:
        _shrc = os.path.expanduser(f'~/.{sh}rc')
        write(_source, _shrc)
    if not shells:
        Log.warning(f'⚠️⚠️⚠️ venv/PATH update at {profile}, add to your .*shrc: {_source} ⚠️⚠️⚠️')
    return _activate


def write(text: str, file: str):
    '''Write text to file if the first line is not already present.'''
    if os.path.exists(file):
        with open(file, 'r') as f:
            content = f.read()
    else:
        content = ''
    if text.strip().split('\n')[0].strip() not in content:
        with open(file, 'a') as f:
            f.write(f'\n{text}\n')
        Log.info(f'✅ {file} ← {text}')
        return True
    return False


def set_timeout(timeout: int = TIMEOUT):
    global TIMEOUT
    TIMEOUT = timeout
    socket.setdefaulttimeout(TIMEOUT)


def is_unattended():
    parser = argparse.ArgumentParser(description=f'Pre-install script for {_pkg_}. {_pkg_}的预安装脚本。')
    parser.add_argument('-y', '--yes', action='store_true', help='Unattended, only pre-install. 无人值守，仅预安装。')
    args = parser.parse_args()
    if not args.yes:
        confirm = input("Install pixi & uv as python env manager, and mocap-wrapper? (y/N): ").strip().lower()
        if confirm != 'y':
            sys.exit(0)
        return False
    return True


def main():
    global IS_MIRROR
    msg = f'Run `mocap --install -b wilor,gvhmr` to continue!'
    Log.debug(f'{os.environ=}')
    IS_AUTO = is_unattended()
    set_timeout()
    IS_MIRROR = is_need_mirror()
    if IS_MIRROR:
        global_git()
    i_pixi()
    i_uv()
    i_mocap()
    set_shell_init_venv_PATH()
    Log.info(f"✅ {msg}`")
    os.remove(MIRROR_CN_PY) if os.path.exists(MIRROR_CN_PY) else None
    SHELL = 'powershell' if is_win else os.getenv('SHELL', 'zsh' if is_mac else 'bash')
    os.execvp(SHELL, [SHELL]) if not IS_AUTO else None


if __name__ == "__main__":
    main()

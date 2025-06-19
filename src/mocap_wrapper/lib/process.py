"""shared functions:

- run_fg: return (exit status, mixture of stdout & stderr), timeout will auto-kill
- run_bg: interact with stdin, need kill() before get_status()
- run_tail: no stdin, long running in bg, need kill() before get_status()
- Spawn: manually controll details of the process
"""
import os
import sys
import shlex
import aexpect
import asyncio
from pathlib import Path
from sys import platform
from shutil import get_terminal_size
from typing import Coroutine, Literal, Sequence
from .logger import Log, getLogger
from . import copy_kwargs, _TIMEOUT_MINUTE, DIR
from typing_extensions import deprecated
Log = getLogger(__name__)
_RUN_ID = 0
def run_async(func: Coroutine, timeout=_TIMEOUT_MINUTE, loop=asyncio.get_event_loop()): return asyncio.run_coroutine_threadsafe(func, loop).result(timeout)
def shlex_quote(args: Sequence[str]): return ' '.join(shlex.quote(str(arg)) for arg in args)


def is_main_thread():
    import threading
    return threading.current_thread() == threading.main_thread()


def get_coro_sig(coro) -> tuple[str, dict]:
    func_name = coro.__qualname__
    args = coro.cr_frame.f_locals
    return func_name, args


def mkdir(dir):
    os.makedirs(dir, exist_ok=True)
    Log.info(f'📁 Created: {dir}')


def relink(src, dst, dst_is_dir=False):
    """remove dst link and create a symlink"""
    if os.path.islink(dst):
        os.remove(dst)
    os.symlink(src, dst, target_is_directory=dst_is_dir)
    Log.info(f'🔗 symlink: {dst} → {src}')


def _aexpect(prefix: str, func):
    def wrapper(commands: str | Sequence[str], *args, **kwargs):
        global _RUN_ID
        cmd = commands if isinstance(commands, str) else shlex_quote(commands)
        cmd0 = commands[0] if isinstance(commands, Sequence) else commands.split()[0]

        if prefix in ['fg', 'bg', 'tail']:
            kwargs.setdefault('output_func', Log.info)
            kwargs.setdefault('output_prefix', f'{prefix}_{_RUN_ID}❯{cmd0}:\t')

        Log.info(f'{prefix}_{_RUN_ID}:\t{cmd}')
        ret = func(command=cmd, *args, **kwargs)
        _RUN_ID += 1
        return ret
    return wrapper


@copy_kwargs(aexpect.run_fg)
def run_fg(commands: Sequence[str], *args, **kwargs) -> tuple[int | None, str | None]: return _aexpect('fg', aexpect.run_fg)(commands, *args, **kwargs)
@copy_kwargs(aexpect.run_bg)
def run_bg(commands: str | Sequence[str], *args, **kwargs) -> 'aexpect.Expect': return _aexpect('bg', aexpect.run_bg)(commands, *args, **kwargs)
@copy_kwargs(aexpect.run_tail)
def run_tail(commands: str | Sequence[str], *args, **kwargs) -> 'aexpect.Expect': return _aexpect('tail', aexpect.run_tail)(commands, *args, **kwargs)
@copy_kwargs(aexpect.Spawn)
def spawn(commands: str | Sequence[str], *args, **kwargs) -> 'aexpect.Spawn': return _aexpect('spawn', aexpect.Spawn)(commands, *args, **kwargs)


def unzip(
    zip_path: str | Path, From='', to: str = DIR, pwd='',
    overwrite_rule: Literal['always', 'skip', 'rename_new', 'rename_old'] = 'skip',
    **kwargs
):
    """
    use 7z to unzip files

    Args:
        From (str): eg: `subdir/*`
        pwd (str): password
    """
    if isinstance(zip_path, Path):
        zip_path = str(zip_path.resolve())
    mode = 'x'
    if From:
        mode = 'e'
    if to:
        to = '-o' + to
    if pwd:
        pwd = f'-p{pwd}'

    conflict = ''
    if overwrite_rule == 'skip':
        conflict = '-aos'
    elif overwrite_rule == 'always':
        conflict = '-aoa'
    elif overwrite_rule == 'rename_new':
        conflict = '-aou'
    elif overwrite_rule == 'rename_old':
        conflict = '-aot'
    else:
        Log.warning(f"Unknown replace_if_existing: {overwrite_rule}")
    cmd = filter(None, ('7z', mode, conflict, pwd, zip_path, From, to))
    p = run_bg(cmd, **kwargs)
    return p


@deprecated('use `run_bg` instead')
async def popen(
    cmd: str,
    mode: Literal['realtime', 'wait', 'no-wait'] = 'realtime',
    Raise=False,
    timeout: float | int | None = _TIMEOUT_MINUTE,
    **kwargs
):
    """Used on long running commands

    Args:
        mode (str):
            - realtime: **foreground**, print in real-time
            - wait: await until finished
            - wait-print: after finished, print the output
            - no-wait: **background**, immediately return, suitable for **forever-looping**, use:
            p = await popen('cmd', mode='bg')
            await p.expect(pexpect.EOF, async_=True)
            print(p.before.decode().strip())
        kwargs: `pexpect.spawn()` args

    Returns:
        process (pexpect.spawn):
    """
    import pexpect
    Log.info(f"{mode}: {cmd=}") if mode != 'wait' else None
    dim = get_terminal_size()
    dim = dim.lines, dim.columns
    p = pexpect.spawn(cmd, timeout=timeout, dimensions=dim, **kwargs)
    FD = sys.stdout.fileno()
    def os_write(): return os.write(FD, p.read_nonblocking(4096))
    if mode == 'realtime':
        while p.isalive():
            try:
                os_write()
            except pexpect.EOF:
                break
            except pexpect.TIMEOUT:
                Log.warning(f"Timeout kill: {cmd}")
                break
            except Exception:
                raise
            await asyncio.sleep(0.1)
        try:
            os_write()
        except pexpect.EOF:
            ...
    elif mode == 'wait':
        while p.isalive():
            try:
                await p.expect(pexpect.EOF, async_=True)
            except pexpect.TIMEOUT:
                Log.warning(f"Timeout kill: {cmd}")
                break
            except Exception:
                raise
    elif mode == 'no-wait':
        return p
    else:
        raise ValueError(f"Invalid mode: {mode}")
    p.before = p.before.decode().strip() if p.before else ''
    if p.exitstatus != 0:
        if Raise:
            raise ChildProcessError(f"{cmd}")
        else:
            Log.warning(f'{p.exitstatus} from "{cmd}" → {p.before}')
    return p


@deprecated('use `cmd` instead')
@copy_kwargs(popen)
async def echo(*args, **kwargs):
    p = await popen(*args, mode='wait', **kwargs)
    return p, str(p.before)

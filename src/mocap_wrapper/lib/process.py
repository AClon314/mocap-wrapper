"""shared functions:

- run_fg: return (exit status, mixture of stdout & stderr), timeout will auto-kill
- run_tail: interact with stdin, need kill() before get_status()
- run_tail: no stdin, long running in bg, need kill() before get_status()
- Spawn: manually controll details of the process
"""
import os
import shlex
import aexpect
import asyncio
from math import inf
from pathlib import Path
from typing import Coroutine, Literal, Sequence
from .logger import Log, getLogger
from . import copy_args, TIMEOUT_MINUTE, DIR
Log = getLogger(__name__)
_RUN_ID = 0
_INTERVAL = 0.1
def run_async(func: Coroutine, timeout=TIMEOUT_MINUTE, loop=asyncio.get_event_loop()): return asyncio.run_coroutine_threadsafe(func, loop).result(timeout)
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


def symlink(src: str, dst: str, overwrite=True, is_src_dir=False, dir_fd: int | None = None):
    Log.info(f'🔗 symlink {src} → {dst}')
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source path does not exist: {src}")
    dst_dir = dst if os.path.isdir(dst) else os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    if overwrite and os.path.exists(dst):
        os.remove(dst)
    os.symlink(src=src, dst=dst, target_is_directory=is_src_dir, dir_fd=dir_fd)
    return dst


async def Await(self: 'aexpect.Spawn', timeout: int | float | None = None, interval=_INTERVAL):
    ''' wrap `aexpect.Spawn` as async func 

    Args:
        timeout: when ≥ 0, kill process after `timeout` seconds;  
            when < 0, **DON'T** kill after `timeout` and return `self`;  
            when==None, don't kill after `timeout` and await **infinitely**.
        interval: `await asyncio.sleep(interval_seconds)`
    '''
    timer = 0
    if timeout is None:
        is_inf = True
        timeout = inf
    else:
        is_inf = False
    no_kill = timeout < 0
    timeout = abs(timeout)
    while self.is_alive() and (is_inf or no_kill or timer < timeout):
        await asyncio.sleep(interval)
        timer += interval
    if self.is_alive():
        if not no_kill:
            self.kill()
        else:
            Log.warning(f'Still running after {timeout=}: {self}')
    else:
        Log.debug(f'{timer=}')
    return self
aexpect.Spawn.Await = Await  # type: ignore[method-assign]


class Spawn(aexpect.Spawn):
    @copy_args(Await)
    async def Await(self, *args, **kwargs): return await Await(self, *args, **kwargs)


class Tail(aexpect.Tail, Spawn):
    ...


class Expect(aexpect.Expect, Spawn):
    ...


def _aexpect(prefix: str, func):
    def wrapper(commands: str | Sequence[str], *args, **kwargs):
        global _RUN_ID
        cmd = commands if isinstance(commands, str) else shlex_quote(commands)
        cmd0 = commands.split()[0] if isinstance(commands, str) else commands[0]

        kwargs.setdefault('output_func', Log.info)
        kwargs.setdefault('output_prefix', f'{prefix}_{_RUN_ID}❯{cmd0}:\t')
        kwargs.setdefault('timeout', _INTERVAL)

        Log.info(f'{prefix}🐣_{_RUN_ID}:\t{cmd}')
        ret = func(command=cmd, *args, **kwargs)
        _RUN_ID += 1
        return ret
    return wrapper


@copy_args(aexpect.run_fg)
def run_fg(cmds: Sequence[str], *args, **kwargs) -> tuple[int | None, str | None]: return _aexpect('fg', aexpect.run_fg)(cmds, *args, **kwargs)
@copy_args(aexpect.run_bg)
def run_bg(cmds: str | Sequence[str], *args, **kwargs) -> Expect: return _aexpect('bg', aexpect.run_bg)(cmds, *args, **kwargs)
@copy_args(aexpect.run_tail)
def run_tail(cmds: str | Sequence[str], *args, **kwargs) -> Tail: return _aexpect('tail', aexpect.run_tail)(cmds, *args, **kwargs)


async def unzip(
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
    p = await run_tail(cmd).Await()
    return p

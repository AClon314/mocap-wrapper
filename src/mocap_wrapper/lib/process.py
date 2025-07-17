"""shared functions:

- run_fg: return (exit status, mixture of stdout & stderr), timeout will auto-kill
- run_tail: interact with stdin, need kill() before get_status()
- run_tail: no stdin, long running in bg, need kill() before get_status()
- Spawn: manually controll details of the process
"""
import os
import re
import shlex
import aexpect
import asyncio
from math import inf
from pathlib import Path
from typing import Coroutine, Literal, Sequence
from .logger import Log, getLogger, is_debug
from .static import TYPE_RUNS, copy_args, TIMEOUT_MINUTE, res_path
from .config import CONFIG
Log = getLogger(__name__)
IS_DEBUG = is_debug(Log)
_RUN_ID = 0
_INTERVAL = 0.1
_RE_CTRL_ASCII = re.compile(r'\x1b\[[0-9;]*m')
def run_async(func: Coroutine, timeout=TIMEOUT_MINUTE, loop: asyncio.AbstractEventLoop | None = None): return asyncio.run_coroutine_threadsafe(func, loop=loop if loop else asyncio.get_event_loop()).result(timeout)
def shlex_quote(args: Sequence[str]): return ' '.join(shlex.quote(str(arg)) for arg in args)


def is_main_thread():
    import threading
    return threading.current_thread() == threading.main_thread()


def get_coro_sig(coro) -> tuple[str, dict]:
    func_name = coro.__qualname__
    args = coro.cr_frame.f_locals
    return func_name, args


def set_status(self: 'aexpect.Spawn', status: int, timeout: float = 1):
    from aexpect.shared import wait_for_lock
    b = wait_for_lock(self.lock_server_running_filename, timeout=timeout)   # type: ignore
    if not b:
        Log.error(f'wait_for_lock exceed {timeout=}: {locals()=}')
        return
    try:
        with open(self.status_filename, "w", encoding="utf-8") as status_file:
            status_file.write(str(status))
    except IOError as e:
        Log.exception('', exc_info=e) if IS_DEBUG else None


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
        # Log.debug(f'{locals()=}\n\n\n\n\n')
        timer += interval
    if self.is_alive():
        if not no_kill:
            self.kill()
            set_status(self, 128 + 15)    # SIGTERM, fix aexpect always return 0 even if killed
        else:
            Log.warning(f'Still running after {timeout=}: {self}')
    else:
        Log.debug(f'{locals()=}')
        if self.get_status() == 128 + 9:    # SIGKILL
            Log.error('The process is forced to be terminated by the system (-9), which may be caused by insufficient memory (OOM). Please check the system memory or issue to developer. 进程被系统强制终止（-9），可能是内存不足（OOM）导致，请检查系统内存或联系开发者。')
    return self
aexpect.Spawn.Await = Await  # type: ignore[method-assign]


class Spawn(aexpect.Spawn):
    @copy_args(Await)
    async def Await(self, *args, **kwargs): return await Await(self, *args, **kwargs)
    @property
    def status(self): return self.get_status()
    @status.setter
    @copy_args(set_status)
    def status(self, status: int): return set_status(self, status)


class Tail(aexpect.Tail, Spawn):
    ...


class Expect(aexpect.Expect, Spawn):
    ...


def _aexpect(prefix: str, func):
    def wrapper(commands: str | Sequence[str], *args, **kwargs):
        global _RUN_ID
        cmd = commands if isinstance(commands, str) else shlex_quote(commands)
        cmd0 = commands.split()[0] if isinstance(commands, str) else commands[0]

        kwargs.setdefault('timeout', _INTERVAL)
        Log.info(f'{prefix}{_RUN_ID}🐣❯ {cmd}')
        if kwargs.get('output_func', None) is None:
            _Log = getLogger(f'{prefix}{_RUN_ID}❯{cmd0}')
            def _Log_info(msg: str, *args, **kwargs): _Log.info(msg, *args, **kwargs) if _RE_CTRL_ASCII.sub('', msg).strip() else None
            kwargs.setdefault('output_func', _Log_info)
        ret = func(command=cmd, *args, **kwargs)
        _RUN_ID += 1
        return ret
    return wrapper


@copy_args(aexpect.run_fg)
def run_fg(cmds: Sequence[str], *args, **kwargs) -> tuple[int | None, str | None]: return _aexpect('fg', aexpect.run_fg)(cmds, *args, **kwargs)
@copy_args(aexpect.run_bg)
def run_bg(cmds: str | Sequence[str], *args, **kwargs) -> Expect: return _aexpect('bg', aexpect.run_bg)(cmds, *args, **kwargs)
@copy_args(aexpect.run_tail)
def run_tail(cmds: str | Sequence[str], *args, **kwargs) -> Tail: return _aexpect('', aexpect.run_tail)(cmds, *args, **kwargs)


async def unzip(
    zip_path: str | Path, From='', to: str = CONFIG['search_dir'], pwd='',
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


async def Python(arg0: str | Path = '', *args: str, run: TYPE_RUNS | Path, env='default'):
    '''pixi run -e=env -- python args...

    if `arg0` is Path: pixi run -e=env -- python arg0 args...  
    else if `arg0` is str and run==gvhmr: pixi run -e=env -- python ...run/gvhmr.py args...
    '''
    # TODO: run at same time if vram > 6gb, or 1 by 1 based if vram < 4gb
    _arg0 = [str(arg0)] if arg0 else []
    py = _arg0 if isinstance(arg0, Path) else [str(res_path(module='run', file=f'{run}.py')), *_arg0]
    RUN = str(run) if isinstance(run, Path) else CONFIG[run]
    _env = [] if not env or env == 'default' else [f'-e={env}']
    _args = [*py, *args]
    cmd = ['pixi', 'run', '-q', *_env, '--manifest-path', RUN, '--', 'python', *_args]
    if '--help' in _args or '-h' in _args:
        return os.system(' '.join(cmd))
    return await run_tail(cmd, output_prefix='', output_func=print).Await()

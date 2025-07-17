import os
import shutil
import asyncio
import itertools
from pathlib import Path
from signal import SIGTERM
from ..lib import getLogger, run_tail, res_path, get_cmds, wait_all_dl, i_pkgs, Aria_process, is_debug, TIMEOUT_QUATER, TIMEOUT_MINUTE, TYPE_RUNS, Env
from typing import Coroutine, Generator, Sequence, Any
Log = getLogger(__name__)
IS_DEBUG = is_debug(Log)
try:
    from mirror_cn import replace_github_with_mirror
except ImportError:
    def replace_github_with_mirror(file: str) -> Generator[tuple[str, str], Any, None]: yield ((file, 'github.com'))


async def install(runs: Sequence[TYPE_RUNS], **kwargs):
    tasks = []
    tasks.append(i_pkgs())

    if 'dynhamr' in runs:
        from .dynhamr import i_dynhamr
        tasks.append(i_dynhamr(**kwargs))
    if 'gvhmr' in runs:
        from .gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in runs:
        from .wilor import i_wilor
        tasks.append(i_wilor(**kwargs))

    done, pending = await asyncio.wait(
        [asyncio.gather(*tasks, return_exceptions=True), asyncio.create_task(wait_all_dl())],
        return_when=asyncio.FIRST_COMPLETED
    )
    ret = done.pop().result()
    for task in pending:
        task.cancel()
    Aria_process.kill(SIGTERM) if Aria_process else None
    return ret


async def i_python_env(Dir: str | Path, pixi_toml='gvhmr.toml', env=['default'], use_mirror: bool | None = None):
    '''when `use_mirror` is None, use `Env.is_mirror`'''
    _toml = str(res_path(file=pixi_toml))
    pixi_toml = Path(Dir, 'pixi.toml')
    use_mirror = Env.is_mirror if use_mirror is None else use_mirror
    timeout = 4 if Env.is_mirror and use_mirror else TIMEOUT_QUATER  # fail quickly if CN use github.com
    Log.debug(f'{locals()=}')
    iter_github = [(_toml, 'github.com')]
    iters = itertools.chain(iter_github, replace_github_with_mirror(file=str(_toml))) if use_mirror else iter_github
    for file, github_mirror in iters:
        Log.debug(f'{github_mirror=}, {timeout=}, {file=}')
        if pixi_toml.exists():
            os.remove(pixi_toml)
        shutil.copy(file, pixi_toml)
        _env = [f'-e={_}' for _ in env]
        cmd = ['pixi', 'install', '-q', *_env, '--manifest-path', str(pixi_toml)]
        Log.info(f'🐍 {" ".join(cmd)}')
        p = await run_tail(cmd).Await(timeout)
        if p.get_status() == 0:
            return p
        elif p.get_status() == 128 + 9:  # OOM
            return
        timeout = TIMEOUT_QUATER


async def Git(cmd: Sequence[str], timeout: float | None = TIMEOUT_MINUTE, retry=True, Raise=True):
    '''with mirror_cn'''
    Log.debug(f'Git {cmd=}')
    if Env.is_mirror:
        from mirror_cn import git
        p = await asyncio.to_thread(git, *cmd, retry=retry, timeout=timeout)
        if Raise and p is None:
            raise RuntimeError(f"Git failed: {' '.join(cmd)}")
    else:
        p = await run_tail(['git', *cmd]).Await(timeout)
        if Raise and p.get_status() not in [0, 128]:
            raise RuntimeError(f"Git failed: {' '.join(cmd)}", p)
    return p


async def git_pull(Dir: str | Path = '', **kwargs):
    """
git fetch --all  
git pull  
git submodule update --init --recursive
    """
    _dir = os.getcwd()
    os.chdir(Dir) if Dir else None
    cmds = get_cmds(git_pull.__doc__)
    for cmd in cmds:
        await Git(cmd.lstrip('git ').split(), **kwargs)
    os.chdir(_dir) if Dir else None


async def gather(coros: Sequence[Coroutine], success_msg=''):
    '''gather, notify by `Log.info/Log.exception`'''
    Log.debug(f'{coros=}')
    if not coros:   # fix: gather(*coros) will stuck when coros=[]
        return [], [], []
    _results = await asyncio.gather(*coros, return_exceptions=True)
    exceptions = [r for r in _results if isinstance(r, Exception)]
    results = [r for r in _results if not isinstance(r, BaseException)]
    if exceptions:
        [Log.exception('', exc_info=e) for e in exceptions]
    else:
        Log.info(f"✔ {success_msg}") if success_msg else None
    return _results, results, exceptions


async def run_1by1(coros: list[Coroutine], raise_if_none=True, raise_if_return0=True):
    results: list[Any] = []
    exception = None
    for coro in coros:
        Log.debug(f'{coro=}')
        try:
            if isinstance(coro, Coroutine):
                ret = await coro
            elif callable(coro):
                ret = coro()
            else:
                ret = coro

            if raise_if_none and ret is None:
                raise ValueError(f'{coro} returned None')
            if hasattr(ret, 'get_status') and callable(ret.get_status):
                returncode = ret.get_status()
                Log.debug(f'{returncode=}')
                if raise_if_return0 and returncode != 0:
                    raise RuntimeError(ret)
            results.append(ret)
        except Exception as e:
            exception = e
            Log.exception('', exc_info=e) if IS_DEBUG else None
            break
    return results, exception

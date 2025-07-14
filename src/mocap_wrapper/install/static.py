import os
import shutil
import asyncio
import itertools
from pathlib import Path
from signal import SIGTERM
from ..lib import getLogger, run_tail, res_path, get_cmds, wait_all_dl, i_pkgs, Aria_process, TIMEOUT_QUATER, TIMEOUT_MINUTE, TYPE_RUNS, Env
from typing import Coroutine, Generator, Sequence, Any
Log = getLogger(__name__)
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
        [asyncio.gather(*tasks), asyncio.create_task(wait_all_dl())],
        return_when=asyncio.FIRST_COMPLETED
    )
    ret = done.pop().result()
    for task in pending:
        task.cancel()
    Aria_process.kill(SIGTERM) if Aria_process else None
    return ret


async def i_python_env(Dir: str | Path, pixi_toml='gvhmr.toml', use_mirror: bool | None = None):
    '''when `use_mirror` is None, use `Env.is_mirror`'''
    _toml = str(res_path(file=pixi_toml))
    pixi_toml = Path(Dir, 'pixi.toml')
    # if (txt := Path(Dir, 'requirements.txt')).exists():
    #     shutil.move(txt, Path(Dir, 'requirements.txt.bak'))
    use_mirror = Env.is_mirror if use_mirror is None else use_mirror
    timeout = 4 if Env.is_mirror and use_mirror else TIMEOUT_QUATER  # fail quickly if CN use github.com
    iter_github = [(_toml, 'github.com')]
    iters = itertools.chain(iter_github, replace_github_with_mirror(file=str(_toml))) if use_mirror else iter_github
    for file, _ in iters:
        if pixi_toml.exists():
            os.remove(pixi_toml)
        shutil.copy(file, pixi_toml)
        cmd = ['pixi', 'install', '-q', '--manifest-path', str(pixi_toml)]
        Log.info(f'🐍 {" ".join(cmd)}')
        p = await run_tail(cmd).Await(timeout)
        if p.get_status() == 0:
            return p
        timeout = TIMEOUT_QUATER


async def Git(cmd: Sequence[str]):
    '''with mirror_cn, return None when failed.'''
    p = await run_tail(['git', *cmd]).Await(TIMEOUT_MINUTE)
    if p.get_status() not in [128, 0] and Env.is_mirror:    # 128 means existed
        from mirror_cn import git
        p = await asyncio.to_thread(git, *cmd)
    return p


async def git_pull(Dir: str | Path = '', **kwargs):
    """
git fetch --all  
git pull  
git submodule update --init --recursive
    """
    _dir = os.getcwd()
    os.chdir(Dir) if Dir else None
    timeout = kwargs.pop('timeout', TIMEOUT_QUATER)
    cmds = get_cmds(git_pull.__doc__)
    for cmd in cmds:
        await run_tail(cmd, **kwargs).Await(timeout=timeout)
    os.chdir(_dir) if Dir else None


async def gather_notify(coros: Sequence[Coroutine], success_msg=''):
    _results = await asyncio.gather(*coros, return_exceptions=True)
    exceptions = [r for r in _results if isinstance(r, Exception)]
    results = [r for r in _results if not isinstance(r, BaseException)]
    if exceptions:
        [Log.exception('', exc_info=e) for e in exceptions]
    else:
        Log.info(f"✔ {success_msg}") if success_msg else None
    return results, exceptions

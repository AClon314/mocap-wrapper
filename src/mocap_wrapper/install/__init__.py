import os
import shutil
import asyncio
import itertools
from pathlib import Path
from signal import SIGKILL
from mirror_cn import replace_github_with_mirror
from ..lib import TIMEOUT_QUATER, TYPE_RUNS, BINS, CONFIG, Aria_process, getLogger, i_pkgs, res_path, run_tail, wait_all_dl
from typing import Sequence
Log = getLogger(__name__)


async def i_python_env(Dir: str | Path, pixi_toml='gvhmr.toml', use_mirror=True):
    _toml = str(res_path(file=pixi_toml))
    pixi_toml = Path(Dir, 'pixi.toml')
    # if (txt := Path(Dir, 'requirements.txt')).exists():
    #     shutil.move(txt, Path(Dir, 'requirements.txt.bak'))
    timeout = 4 if CONFIG.is_mirror and use_mirror else TIMEOUT_QUATER  # fail quickly if CN use github.com
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


async def install(runs: Sequence[TYPE_RUNS], **kwargs):
    tasks = []

    pkgs = {p: shutil.which(p) for p in BINS}
    Log.debug(f'installed: {pkgs}')
    pkgs = [p for p, v in pkgs.items() if not v]
    if any(pkgs):
        await i_pkgs()

    if 'gvhmr' in runs:
        from .gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in runs:
        from .wilor import i_wilor_mini
        tasks.append(i_wilor_mini(**kwargs))

    done, pending = await asyncio.wait(
        [asyncio.gather(*tasks), asyncio.create_task(wait_all_dl())],
        return_when=asyncio.FIRST_COMPLETED
    )
    ret = done.pop().result()
    for task in pending:
        task.cancel()
    Aria_process.kill(SIGKILL) if Aria_process else None
    return ret

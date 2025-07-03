import shutil
import signal
import asyncio
from ..lib import getLogger, TYPE_RUNS, BINS, i_pkgs, run_tail, try_aria_port, Aria
from typing import Sequence
Log = getLogger(__name__)
TORCH_REPO = 'MiroPsota/torch_packages_builder'
def _Log_info(msg: str, *args, **kwargs): Log.info(msg.strip(), *args, **kwargs)


async def install(runs: Sequence[TYPE_RUNS], **kwargs):
    global Aria
    tasks = []

    pkgs = {p: shutil.which(p) for p in BINS}
    Log.debug(f'installed: {pkgs}')
    pkgs = [p for p, v in pkgs.items() if not v]
    if any(pkgs):
        await i_pkgs()

    p_aria = None
    if Aria is None:
        # try to start aria2c
        p_aria = await run_tail(
            'aria2c --enable-rpc --rpc-listen-port=6800',
            output_func=_Log_info).Await()
        await asyncio.sleep(1.5)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    # Log.debug(f'{runs=}')
    if 'gvhmr' in runs:
        from .gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in runs:
        from .wilor_mini import i_wilor_mini
        tasks.append(i_wilor_mini(**kwargs))

    ret = await asyncio.gather(*tasks)
    p_aria.kill(signal.SIGKILL) if p_aria else None
    return ret

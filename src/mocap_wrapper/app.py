#!/bin/python
import os
import logging
from warnings import filterwarnings
SELF_DIR = os.path.dirname(os.path.abspath(__file__))
filterwarnings("ignore", category=RuntimeWarning)
filterwarnings("ignore", category=DeprecationWarning)

# ignore urllib3.connectionpool
connectionpool_logger = logging.getLogger("urllib3.connectionpool")
connectionpool_logger.setLevel(logging.CRITICAL)
import sys
import copy
import asyncio
import argparse
from typing import Sequence
from .lib import getLogger, ffmpeg_or_link, Python, CONFIG, PACKAGE, QRCODE, RUNS, TYPE_RUNS, VERSION
from .install.static import install
DEFAULT: Sequence[TYPE_RUNS] = ('wilor', 'gvhmr')
OUTPUT_DIR = os.path.join(CONFIG['search_dir'], 'output')
def version(): return f'{PACKAGE} {VERSION} 👻\tconfig: {CONFIG.path}\tcode: https://github.com/AClon314/mocap-wrapper'
async def gather(*args, **kwargs): return await asyncio.gather(*args, **kwargs)
_VERSION_ = version()
Log = getLogger(__name__)


async def run(runs: Sequence[TYPE_RUNS], input: str, outdir: str, Range='', args: Sequence[str] = []):
    video = await ffmpeg_or_link(input, outdir, Range=Range)
    for m in runs:
        p = await Python('--input', video, '-o', outdir, *args, run=m)


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        print(QRCODE)
        print(f'example: mocap -I -@ .. -i input.mp4')
        super().print_help(file)
        tasks = [Python('--help', run=m)for m in DEFAULT]
        asyncio.run(gather(*tasks))


def argParse():
    print(_VERSION_)
    arg = ArgParser(description=f'sincerelly thanks to gvhmr/wilor/wilor-mini devs and others that help each other♥️ , please consider donate♥️ if helps you a lot :)')
    arg.add_argument('-v', '--version', action='store_true')
    arg.add_argument('-I', '--install', action='store_true', help='force to re-install runs')
    arg.add_argument('-b', '--by', nargs='*', default=False, metavar=','.join(RUNS), help=f'install with/run by, default all installed, eg: `--by={",".join(DEFAULT)}`')
    arg.add_argument('-@', '--at', metavar=CONFIG['search_dir'], help='search_dir of git repos, eg: `--at=".."` if GVHMR is current work dir')
    arg.add_argument('-i', '--input', nargs='*', metavar='in.mp4')
    arg.add_argument('-o', '--outdir', metavar=OUTPUT_DIR, default=OUTPUT_DIR)
    arg.add_argument('-r', '--range', metavar='[a,b]or[a,duration]', default='', help='video time range, eg: `--range=0:0:1,0:2` is 1s~2s, `--range=10` is 0s~10s')
    # arg.add_argument('--euler', action='store_true', help='use euler_XYZ for bones rotations for export data')
    ns, args = arg.parse_known_args()
    return ns, args


async def mocap(
    inputs: list[str] = [], outdir=OUTPUT_DIR,
    Range='', at=CONFIG['search_dir'], by: Sequence[TYPE_RUNS] = RUNS,
    args: list[str] = []
):
    if at:
        CONFIG['search_dir'] = at
    os.makedirs(CONFIG['search_dir'], exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    _by = list(copy.deepcopy(by))
    for i in by:
        if i and getattr(CONFIG, i, True) and os.path.exists(os.path.join(CONFIG[i], 'pixi.toml')):
            _by.remove(i)
    await install(runs=_by)
    if inputs:
        for i in inputs:
            # TODO: auto parallelize if vram > 6gb
            await run(by, i, outdir, Range=Range, args=args)
    else:
        for b in by:
            p = await Python(args.pop(0) if args else '', *args, run=b)


def script_entry():
    args, _args = argParse()
    if len(sys.argv) <= 1:
        from .server.mcp import main as mcp_main
        mcp_main()
        return
    if args.by:
        by = []
        for r in args.by:
            by += r.split(',')
    else:
        by = DEFAULT

    if args.install and by and by[0]:  # fix mocap -I -b ''
        for r in by:
            del CONFIG[r]   # TODO
            setattr(CONFIG, r, None)

    asyncio.run(mocap(
        inputs=args.input,
        outdir=args.outdir,
        Range=args.range,
        at=args.at,
        by=by,
        args=_args,
    ))


if __name__ == "__main__":
    script_entry()

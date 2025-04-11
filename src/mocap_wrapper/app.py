#!/bin/python
import os
import atexit
import argparse
import asyncio as aio
from typing import Any, Coroutine, Sequence
from mocap_wrapper.logger import IS_DEBUG, cleanup
from mocap_wrapper.lib import DIR, RUNS, CONFIG, PACKAGE, TYPE_RUNS, QRCODE, ffmpeg_or_link, gather, getLogger, mkdir, path_expand, res_path, __version__
from mocap_wrapper.install.lib import ENV, install, async_queue, mamba
DEFAULT: Sequence[TYPE_RUNS] = ('wilor', 'gvhmr')
OUTPUT_DIR = os.path.join(DIR, 'output')
Log = getLogger(__name__)
def version(): return f'{PACKAGE} {__version__} 👻\tconfig: {CONFIG.path}\tcode: https://github.com/AClon314/mocap-wrapper'
# TODO： 兼容notebook环境pip，避免循环导入，解耦模块


async def Python(run: TYPE_RUNS, *args: str):
    # TODO: run at same time if vram > 6gb, or 1 by 1 based if vram < 4gb
    _arg = ' '.join(args)
    if run == 'wilor':
        run = 'wilorMini'   # type: ignore
    py = res_path(module='run', file=f'{run}.py')
    cmd = f'python {py} {_arg}'
    return await mamba(cmd, env=ENV)


async def run(runs: Sequence[TYPE_RUNS], input: str, outdir: str, Range='', args: Sequence[str] = []):
    video = await ffmpeg_or_link(input, outdir, Range=Range)
    for m in runs:
        IS = await Python(m, '--input', video, '-o', outdir, *args)


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        print(QRCODE)
        print(f'example: mocap -I -@ .. -i input.mp4')
        super().print_help(file)
        tasks = [Python(m, '--help')for m in DEFAULT]
        aio.run(gather(*tasks))


def argParser():
    print(version())
    arg = ArgParser(description=f'sincerelly thanks to gvhmr/wilor/wilor-mini devs and others that help each other♥️ , please consider donate♥️ if helps you a lot :)')
    arg.add_argument('-v', '--version', action='store_true')
    arg.add_argument('-I', '--install', action='store_true', help='force to re-install runs')
    arg.add_argument('-b', '--by', nargs='*', default=False, metavar=RUNS, help=f'install with/run by, default all installed, eg: `--by={",".join(DEFAULT)}`')
    arg.add_argument('-@', '--at', metavar=DIR, help='search_dir of git repos, eg: `--at=".."` if GVHMR is current work dir')
    arg.add_argument('-i', '--input', nargs='*', metavar='in.mp4')
    arg.add_argument('-o', '--outdir', metavar=OUTPUT_DIR, default=OUTPUT_DIR)
    arg.add_argument('-r', '--range', metavar='[a,b]or[a,duration]', default='', help='video time range, eg: `--range=0:0:1,0:2` is 1s~2s, `--range=10` is 0s~10s')
    # arg.add_argument('--euler', action='store_true', help='use euler_XYZ for bones rotations for export data')
    arg.add_argument('--convert', action='store_true', help='convert all input .npy/.npz/.pt/.pkl into .npz for blender addon')

    # arg.add_argument('--smpl', help='cookies:PHPSESSID to download smpl files. eg: `--smpl=26-digits_123456789_123456`')
    # arg.add_argument('--smplx', help='cookies:PHPSESSID to download smplx files. eg: `--smplx=26-digits_123456789_123456`')
    # arg.add_argument('--user-agent', help='From your logged in browser. eg: `--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"`')
    args, _args = arg.parse_known_args()
    return args, _args


def mocap(
    inputs: list[str], outdir: str,
    Range: str, at: str, by: Sequence[TYPE_RUNS],
    is_npt, _args: list[str]
):
    atexit.register(cleanup)
    global DIR
    if at:
        DIR = CONFIG['search_dir'] = path_expand(at)
    mkdir(DIR)
    mkdir(outdir)

    tasks: list[Coroutine[Any, Any, Any]] = [async_queue()]
    for i in by:
        if CONFIG[i] != True or not os.path.exists(CONFIG[i]):
            tasks.append(install(runs=by))
            aio.run(gather(*tasks), debug=IS_DEBUG)
    if inputs:
        cleanup()
        for i in inputs:
            # TODO: auto parallelize if vram > 6gb
            aio.run(
                run(by, i, outdir, Range=Range, args=_args),
                debug=IS_DEBUG)
    if is_npt:
        from mocap_wrapper.script.data_viewer import convert_npt
        convert_npt(inputs, outdir, save=True, Print=True)


def script_entry():
    args, _args = argParser()
    if args.by:
        by = []
        for r in args.by:
            by += r.split(',')
    else:
        by = DEFAULT

    if args.install:
        for r in by:
            CONFIG[r] = False

    mocap(
        inputs=args.input,
        outdir=args.outdir,
        Range=args.range,
        at=args.at,
        by=by,
        is_npt=args.convert,
        _args=_args
    )


if __name__ == "__main__":
    script_entry()

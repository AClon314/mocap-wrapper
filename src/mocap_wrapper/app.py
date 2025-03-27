#!/bin/python
import os
import argparse
import asyncio as aio
from typing import Coroutine, Sequence
from mocap_wrapper.logger import IS_DEBUG
from mocap_wrapper.lib import DIR, MODS, CONFIG, PACKAGE, TYPE_MODS, QRCODE, copy_kwargs, getLogger, path_expand, res_path, __version__
from mocap_wrapper.install.lib import ENV, install, async_queue, mamba
DEFAULT: Sequence[TYPE_MODS] = ('wilor', 'gvhmr')
Log = getLogger(__name__)


@copy_kwargs(aio.gather)
async def gather(*args, **kwargs): return await aio.gather(*args, **kwargs)
def version(): return f'{PACKAGE} {__version__} 👻, config: {CONFIG.path}'


async def Python(mod: TYPE_MODS, *args: str):
    # TODO: run at same time if vram > 6gb, or 1 by 1 based if vram < 4gb
    _arg = ' '.join(args)
    if mod == 'wilor':
        mod = 'wilorMini'   # type: ignore
    py = res_path(module='run', file=f'{mod}.py')
    return await mamba(f'python {py} {_arg}', env=ENV, py_mgr='pip')


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        print(QRCODE)
        print(f'example: mocap -I -@ .. -i input.mp4')
        super().print_help(file)
        tasks = [Python(m, '--help')for m in DEFAULT]
        aio.run(gather(*tasks))


def main():
    global DIR
    arg = ArgParser(description=f'https://github.com/AClon314/mocap-wrapper, sincerelly thanks to gvhmr/wilor/wilor-mini devs and other developers that help each other ♥️, please consider donate♥️ if helps you a lot :)')
    arg.add_argument('-v', '--version', action='store_true')
    arg.add_argument('-I', '--install', action='store_true')
    arg.add_argument('-b', '--by', nargs='*', default=False, metavar=MODS, help=f'install with/run by, default all installed, eg: `--by={",".join(DEFAULT)}`')
    arg.add_argument('-@', '--at', metavar=DIR, help='search_dir of git repos, eg: `--at=".."` if GVHMR is current work dir')
    arg.add_argument('-i', '--input', metavar='in.mp4')

    # arg.add_argument('--smpl', help='cookies:PHPSESSID to download smpl files. eg: `--smpl=26-digits_123456789_123456`')
    # arg.add_argument('--smplx', help='cookies:PHPSESSID to download smplx files. eg: `--smplx=26-digits_123456789_123456`')
    # arg.add_argument('--user-agent', help='From your logged in browser. eg: `--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"`')

    print(version())
    args, _args = arg.parse_known_args()

    if args.at:
        DIR = CONFIG['search_dir'] = path_expand(args.at)
    if not os.path.exists(DIR):
        os.makedirs(DIR, exist_ok=True)
        Log.info(f'📁 Created: {DIR}')

    if args.by:
        mods = []
        for m in args.by:
            mods += m.split(',')
    else:
        mods = DEFAULT

    if args.install != False or args.install == []:
        tasks: list[Coroutine] = [async_queue()]
        tasks.append(install(mods=mods))
        aio.run(gather(*tasks), debug=IS_DEBUG)
    if args.input:
        for m in mods:
            aio.run(Python(m, '-i', args.input))
    if not any(vars(args).values()):
        arg.print_help()


if __name__ == "__main__":
    main()

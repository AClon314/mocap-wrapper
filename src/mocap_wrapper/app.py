#!/bin/python
import os
import argparse
import asyncio as aio
from typing import Sequence
from mocap_wrapper.lib import DIR, MODS, CONFIG, PACKAGE, TYPE_MODS, QRCODE, path_expand, __version__
from mocap_wrapper.logger import IS_DEBUG
from mocap_wrapper.install.lib import install, async_queue, mamba
DEFAULT: Sequence[TYPE_MODS] = ('gvhmr', 'wilor')


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        print(QRCODE)
        super().print_help(file)


def version(): return f'{PACKAGE} {__version__} 👻'


def main():
    arg = ArgParser(description=f'{version()}, config: {CONFIG.path}, Source: https://github.com/AClon314/mocap-wrapper, please consider donate♥️ developers if this helps you a lot :)')
    arg.add_argument('-I', '--install', nargs='*', default=False, metavar=MODS, help=f'eg: `--install={",".join(DEFAULT)}`')
    arg.add_argument('-@', '--at', default=DIR, metavar=DIR, help='search_dir of git repos, eg: `--at=".."` if GVHMR is current work dir')
    arg.add_argument('-i', '--input', help='eg: `-i input.mp4`')
    arg.add_argument('-v', '--version', action='version', version=version())

    # arg.add_argument('--smpl', help='cookies:PHPSESSID to download smpl files. eg: `--smpl=26-digits_123456789_123456`')
    # arg.add_argument('--smplx', help='cookies:PHPSESSID to download smplx files. eg: `--smplx=26-digits_123456789_123456`')
    # arg.add_argument('--user-agent', help='From your logged in browser. eg: `--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"`')

    tasks = [async_queue()]  # type: list
    arg = arg.parse_args()

    dir = path_expand(arg.at)
    if os.path.exists(CONFIG['search_dir']):
        dir = CONFIG['search_dir']
    elif not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

    if arg.install != False or arg.install == []:
        if arg.install:
            mods = []
            for m in arg.install:
                mods += m.split(',')
        else:
            mods = DEFAULT
        tasks.append(install(mods=mods, Dir=dir))
        aio.run(tasks[1], debug=IS_DEBUG)
    if arg.input:
        print(f'Input file: {arg.input}')
        # mamba()


if __name__ == "__main__":
    main()

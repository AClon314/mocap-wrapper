#!/bin/python
import os
import argparse
import asyncio as aio
from mocap_wrapper.lib import DIR, MODS
from mocap_wrapper.logger import IS_DEBUG
from mocap_wrapper.install.lib import install, async_queue
DEFAULT = ['gvhmr', 'wilor']


async def one_by_one(tasks):
    ret = []
    for t in tasks:
        ret.append(await t)
    return ret


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('-I', '--install', nargs='*', default=False, metavar=MODS, help=f'eg: `--install={",".join(DEFAULT)}`')
    arg.add_argument('-I@', '--install-at', default=DIR, metavar=DIR, help='eg: `--install-at=".."` (if your cwd(current work dir)=GVHMR, use `..` and `-I gvhmr` to install)')
    arg.add_argument('-i', '--input', help='eg: `-i input.mp4`')

    # arg.add_argument('--smpl', help='cookies:PHPSESSID to download smpl files. eg: `--smpl=26-digits_123456789_123456`')
    # arg.add_argument('--smplx', help='cookies:PHPSESSID to download smplx files. eg: `--smplx=26-digits_123456789_123456`')
    # arg.add_argument('--user-agent', help='From your logged in browser. eg: `--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"`')

    tasks = [async_queue()]  # type: list
    arg = arg.parse_args()
    if os.path.exists(arg.install_at) == False:
        os.makedirs(arg.install_at, exist_ok=True)
    if arg.install != False or arg.install == []:
        if arg.install:
            mods = []
            for m in arg.install:
                mods += m.split(',')
        else:
            mods = DEFAULT
        tasks.append(install(mods=mods, Dir=arg.install_at))
    if arg.input:
        print(f'Input file: {arg.input}')
    aio.run(one_by_one(tasks), debug=IS_DEBUG)


if __name__ == "__main__":
    main()

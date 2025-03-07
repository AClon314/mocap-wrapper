#!/bin/python
import argparse
import asyncio as aio
DEFAULT = ['gvhmr', 'wilor']


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('-I', '--install', nargs='*', default=False, help=f'eg: `--install={",".join(DEFAULT)}`')
    arg.add_argument('-i', '--input', help='eg: `-i input.mp4`')

    arg.add_argument('--smpl', help='cookies:PHPSESSID to download smpl files. eg: `--smpl=26-digits_123456789_123456`')
    arg.add_argument('--smplx', help='cookies:PHPSESSID to download smplx files. eg: `--smplx=26-digits_123456789_123456`')
    arg.add_argument('--user-agent', help='From your logged in browser. eg: `--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"`')

    arg.add_argument('--tmp-dir', default='~', help='to store downloaded files. Better be the **SAME** as the destination path, which can instantly move tmp files.')

    arg = arg.parse_args()
    if arg.install != False or arg.install == []:
        if arg.install:
            mods = []
            for m in arg.install:
                mods += m.split(',')
        else:
            mods = DEFAULT
        from mocap_wrapper.install import install
        tasks = aio.run(install(mods=mods))
    if arg.input:
        print(f'Input file: {arg.input}')


if __name__ == "__main__":
    main()

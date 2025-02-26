#!/bin/python
import argparse
import asyncio as aio
DEFAULT = ['gvhmr', 'wilor']


async def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('-I', '--install', nargs='*', default=False, help=f'eg: `--install={",".join(DEFAULT)}`')
    arg.add_argument('-i', '--input', help='eg: `-i input.mp4`')
    arg = arg.parse_args()
    if arg.install != False or arg.install == []:
        if arg.install:
            mods = []
            for m in arg.install:
                mods += m.split(',')
        else:
            mods = DEFAULT
        from mocap_wrapper.install import install
        tasks = await install(mods=mods)
    if arg.input:
        print(f'Input file: {arg.input}')


if __name__ == "__main__":
    aio.run(main())

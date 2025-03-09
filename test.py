import asyncio as aio
from mocap_wrapper.lib import Popen


async def main():
    p = [
        Popen('while :; do echo 1; done'),
        Popen('while :; do echo 2; done'),
    ]
    rets = aio.gather(*p)
    print(rets)

aio.run(main())

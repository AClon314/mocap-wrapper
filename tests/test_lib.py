#!/bin/env python
import pytest
import shutil
import logging
import numpy as np
from os import getcwd
from sys import path as PATH
from time import sleep
from mocap_wrapper.run.lib import euler, quat_rotAxis
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.lib import *
DRY_RUN = False
ENV = 'test'
URLS = [
    # 'https://dldir1.qq.com/qqfile/qq/PCQQ9.7.17/QQ9.7.17.29225.exe',  # CN: 200MB
    # 'http://speedtest.zju.edu.cn/100M',
    # 'https://speed.cloudflare.com/__down?during=download&bytes=104857600',   # GLOBAL: 100MB
    'https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',  # 3MB
]
Log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    'cmds, func',
    [
        (['sleep 0.5', 'sleep 4', 'sleep 0.5'], run_tail),
        (['aria2c --enable-rpc --rpc-listen-port=16800'] * 2, run_tail),
        (['curl -I https://www.bing.com'] * 2, run_tail),
    ]
)
def test_aexpect_sync(cmds: list[str], func):
    aexpects: list['aexpect.Expect'] = [func(cmd, timeout=2) for cmd in cmds]
    failed = []
    while aexpects:
        p = aexpects.pop()
        if isinstance(p, (aexpect.Expect, aexpect.Spawn)):
            p.kill()
            failed.append(p.command) if p.get_status() != 0 else None
        elif p[0] != 0 and p[1]:
            # run_tail
            failed.append(p[1])
        else:
            aexpects.append(p)  # re-append if not finished
        # Log.info(f'{p.command} {p.get_status()}')


@pytest.mark.parametrize(
    'cmds, func',
    [
        (['sleep 0.5', 'sleep 4', 'sleep 0.5'], run_tail),
    ]
)
async def test_aexpect(cmds: list[str], func: Callable[[str], Spawn]):
    tasks = [func(cmd).Await() for cmd in cmds]
    Log.info(f'{len(tasks)=}')
    results = await asyncio.gather(*tasks)
    Log.info(results)


@pytest.mark.parametrize(
    "urls, kwargs",
    [(URLS, {'dir': os.path.join(CWD, 'output')}),]
)
async def test_download(urls, kwargs):
    dls = download(urls, **kwargs)
    await wait_slowest()
    # os.remove(d.path)


@pytest.mark.parametrize(
    "Zip, From, To",
    [
        ('example.zip', None, '.example'),
    ]
)
async def test_unzip(Zip, From, To):
    p = await unzip(Zip, From, To)
    shutil.rmtree(To)
    assert p.get_status() == 0, p


@pytest.mark.parametrize(
    "urls",
    [(URLS),]
)
async def test_resume(urls):
    coros = [asyncio.create_task(is_resumable_file(url)) for url in urls]
    for c in asyncio.as_completed(coros):
        try:
            is_resume, filename = await c
        except aiohttp.ServerConnectionError as e:
            Log.error(e)
            continue


@pytest.skip('requires aria2c')
@pytest.mark.parametrize(
    "video",
    [
        'https://github.com/warmshao/WiLoR-mini/raw/refs/heads/main/assets/video.mp4',
    ]
)
async def test_ffmpeg(video, dry_run=False):
    print(video)
    if dry_run:
        p = ffprobe(video)
    else:
        p = await ffmpeg_or_link(from_file=video, to_dir='../output')
    Log.info(p)


@pytest.mark.parametrize(
    "text",
    [
        '0:0:0.0,0:0:5.0',
        '0:0:0.0+0.5',
        '62,120',
        '62+0:1',
        '10'
    ]
)
def test_range_time(text):
    Range = range_time(text)


@pytest.mark.parametrize(
    "rot",
    [
        [1, 1, 1],
    ]
)
def test_rod(rot):
    if not hasattr(rot, 'shape'):
        rot = np.array(rot)
    Quat = quat_rotAxis(rot)
    Euler = euler(Quat)
    Log.info(Quat)
    Log.info(Euler)


@pytest.fixture(scope="function", autouse=True)
def setup_progress():
    ...
    yield
    # clean()


if __name__ == '__main__':
    ...
    asyncio.run(
        test_download(URLS, {'dir': CWD})
        # test_worker()
    )

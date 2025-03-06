import pytest
from os import getcwd
from sys import path as PATH
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.install import *
from mocap_wrapper.Gdown import google_drive
DRY_RUN = False
ENV = 'test'


URLS = [
    # 'https://dldir1.qq.com/qqfile/qq/PCQQ9.7.17/QQ9.7.17.29225.exe',  # CN: 200MB
    # 'http://speedtest.zju.edu.cn/100M',
    # 'https://speed.cloudflare.com/__down?during=download&bytes=104857600',   # GLOBAL: 100MB
    'https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',  # 3MB
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "urls, kwargs",
    [(URLS, {'dir': os.path.join(CWD, 'output')}),]
)
async def test_download(urls, kwargs):
    tasks = [download(url, dry_run=DRY_RUN, **kwargs) for url in urls]
    dls = await aio.gather(*tasks)
    for d in dls:
        assert d.completed_length > 1, d
        # os.remove(d.path)


@pytest.mark.skip(reason="need to pre-install in CI")
@pytest.mark.parametrize(
    "From, to",
    [('output/SMPL_python_v.1.1.0.zip',
      'output'),]
)
def test_unzip(From, to):
    p = unzip(From, to, dry_run=DRY_RUN)
    assert p.returncode == 0, p
    # os.rmdir(to)


@pytest.mark.parametrize(
    "func, kwargs",
    [
        (sp.Popen, {'bad': 'arg', 'stdin': sp.PIPE}),
        (sp.check_output, {'bad': 'arg', 'stdin': sp.PIPE}),
    ]
)
def test_kwargs(func, kwargs):
    kwargs = Kwargs([func], kwargs)
    p = func(f"echo '{func}' {kwargs}", shell=True, **kwargs)
    assert p, p


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "urls",
    [(URLS),]
)
async def test_resume(urls):
    coros = [aio.create_task(is_resumable_file(url)) for url in urls]
    for c in aio.as_completed(coros):
        try:
            is_resume, filename = await c
        except aiohttp.ServerConnectionError as e:
            Log.error(e)
            continue


@pytest.fixture(scope="function", autouse=True)
def setup_progress():
    ...
    yield
    # clean()


if __name__ == '__main__':
    ...
    aio.run(
        test_download(URLS, {'dir': CWD})
        # test_worker()
    )

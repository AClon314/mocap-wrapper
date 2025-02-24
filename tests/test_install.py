import pytest
from os import getcwd
from sys import path as PATH
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.install import *
DRY_RUN = False
ENV = 'test'


@pytest.mark.skip(reason='ok')
@pytest.mark.parametrize(
    "mgr",
    [('mamba'), ('conda'),]
)
def test_env_list(mgr: int):
    envs = get_envs(mgr)
    assert 'base' in envs, envs


@pytest.mark.parametrize(
    "pkgs, env, cmd",
    [(('numpy', 'pandas'), ENV, "echo $CONDA_DEFAULT_ENV"),]
)
def test_mamba(pkgs, env, cmd):
    fail = mamba(*pkgs, env=env, txt=None, cmd=cmd, dry_run=DRY_RUN)
    assert not fail, fail


URLS = [
    'https://dldir1.qq.com/qqfile/qq/PCQQ9.7.17/QQ9.7.17.29225.exe',  # CN: 200MB
    'https://speed.cloudflare.com/__down?during=download&bytes=104857600'   # GLOBAL: 100MB
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, kwargs",
    [(URLS[0], {'dir': CWD})]
)
async def test_download(url, kwargs):
    d = await download(url, dry_run=DRY_RUN, kwargs=kwargs)
    assert d.is_complete, d
    os.remove(d.path)


@pytest.hookimpl(tryfirst=True)
def pytest_end(session, exitstatus):
    cleanup = Popen(f"mamba env remove -y -n {ENV}")

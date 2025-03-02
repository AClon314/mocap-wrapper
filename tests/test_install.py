import pytest
from os import getcwd
from sys import path as PATH
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.install import *
DRY_RUN = False
ENV = 'test'


@pytest.mark.parametrize(
    "mgr",
    [('mamba'), ('conda'),]
)
def test_env_list(mgr: str):
    envs, now = get_envs(mgr)
    Log.debug(f'{now}, {envs}')
    assert 'base' in envs.keys(), envs


@pytest.mark.parametrize(
    "pkgs, env, cmd",
    [(('numpy', 'pandas'), ENV, "echo $CONDA_DEFAULT_ENV"),]
)
def test_mamba(pkgs, env, cmd):
    fail = mamba(*pkgs, env=env, txt=None, cmd=cmd, dry_run=DRY_RUN)
    cleanup = Popen(f"{PY_MGR} env remove -y -n {ENV}")
    assert not fail, fail


URLS = [
    'https://dldir1.qq.com/qqfile/qq/PCQQ9.7.17/QQ9.7.17.29225.exe',  # CN: 200MB
    'https://speed.cloudflare.com/__down?during=download&bytes=104857600',   # GLOBAL: 100MB
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, kwargs",
    [(URLS[0], {'dir': CWD})]
)
async def test_download(url, kwargs):
    d = await aria(url, dry_run=DRY_RUN, kwargs=kwargs)
    assert d.completed_length > 1, d
    os.remove(d.path)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "smpl, smplx",
    [('smpl=18j30naqt388odc21r4kkmvpa0',
      'smplx=8flff24q1cuirp28c1v959r00n')]
)
async def test_smpl(smpl, smplx):
    dls = await i_smpl(PHPSESSIDs={'smpl': smpl, 'smplx': smplx}, dry_run=DRY_RUN)
    for d in dls:
        assert d.completed_length > 1, d
        os.remove(d.path)


@pytest.mark.parametrize(
    "From, to",
    [('output/SMPL_python_v.1.1.0.zip',
      'output'),]
)
def test_unzip(From, to):
    p = unzip(From, to, dry_run=DRY_RUN)
    assert p.returncode == 0, p
    # os.rmdir(to)

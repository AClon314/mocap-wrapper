import pytest
from os import getcwd
from sys import path as PATH
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.install.lib import *
from mocap_wrapper.install.Gdown import google_drive
DRY_RUN = True
ENV = 'test'


# @pytest.mark.skip(reason="need to pre-install in CI")
@pytest.mark.parametrize(
    "mgr",
    [('mamba'), ('conda'),]
)
async def test_env_list(mgr: str):
    envs, now = await get_envs(mgr)
    Log.debug(f'{now}, {envs}')
    assert 'base' in envs.keys(), envs


@pytest.mark.skip(reason="need to pre-install in CI")
@pytest.mark.parametrize(
    "pkgs, env, cmd",
    [(('numpy', 'pandas'), ENV, "echo $CONDA_DEFAULT_ENV"),]
)
async def test_mamba(pkgs, env, cmd):
    fail = await mamba(*pkgs, env=env, txt=None, cmd=cmd, dry_run=DRY_RUN)
    cleanup = await popen(f"mamba env remove -y -n {ENV}")
    assert not fail, fail


@pytest.mark.skip(reason="403 Forbidden")
@pytest.mark.parametrize(
    "smpl, smplx",
    [('smpl=18j30naqt388odc21r4kkmvpa0',
      'smplx=8flff24q1cuirp28c1v959r00n')]
)
async def test_smpl(smpl, smplx):
    from mocap_wrapper.install.smpl import i_smpl
    dls = await i_smpl()
    for d in dls:
        assert d.completed_length > 1, d
        os.remove(d.path)


@pytest.mark.parametrize(
    "ID",
    [
        ('1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0'),
        ('1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP'),
        ('1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc'),
    ]
)
async def test_Gdrive(ID):
    url = google_drive(id=ID)
    Log.info(url)
    assert url, url


if __name__ == '__main__':
    ...
    # asyncio.run(test_Gdrive('1DE5GVftRCfZOTMp8YWF0xkGudD'))

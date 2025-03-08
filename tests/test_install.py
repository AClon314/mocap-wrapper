import pytest
from os import getcwd
from sys import path as PATH
CWD = getcwd()
PATH.append(CWD)
from mocap_wrapper.install.lib import *
from mocap_wrapper.Gdown import google_drive
DRY_RUN = True
ENV = 'test'


@pytest.mark.skip(reason="need to pre-install in CI")
@pytest.mark.parametrize(
    "mgr",
    [('mamba'), ('conda'),]
)
def test_env_list(mgr: str):
    envs, now = get_envs(mgr)
    Log.debug(f'{now}, {envs}')
    assert 'base' in envs.keys(), envs


@pytest.mark.skip(reason="need to pre-install in CI")
@pytest.mark.parametrize(
    "pkgs, env, cmd",
    [(('numpy', 'pandas'), ENV, "echo $CONDA_DEFAULT_ENV"),]
)
def test_mamba(pkgs, env, cmd):
    fail = mamba(*pkgs, env=env, txt=None, cmd=cmd, dry_run=DRY_RUN)
    cleanup = Popen(f"{PY_MGR} env remove -y -n {ENV}")
    assert not fail, fail


@pytest.mark.skip(reason="403 Forbidden")
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ID",
    [
        ('1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0'),
        ('1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP'),
        ('1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc'),
        ('1sR8xZD9wrZczdDVo6zKscNLwvarIRhP5'),
        ('1_HGm-lqIH83-M1ML4bAXaqhm_eT2FKo5')
    ]
)
async def test_Gdrive(ID):
    url = google_drive(id=ID)
    Log.info(url)
    assert url, url


@pytest.fixture(scope="function", autouse=True)
def setup_progress():
    ...
    yield
    # clean()


if __name__ == '__main__':
    ...
    # aio.run(test_Gdrive('1DE5GVftRCfZOTMp8YWF0xkGudD'))

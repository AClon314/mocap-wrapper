import pytest
from mocap_wrapper.install import env_list


@pytest.mark.parametrize(
    "mgr",
    [
        ('mamba'),
        ('conda'),
    ]
)
def test_env_list(mgr: int):
    envs = env_list(mgr)
    assert 'base' in envs, envs

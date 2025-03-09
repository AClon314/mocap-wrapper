from mocap_wrapper.lib import *
from mocap_wrapper.install.lib import *
from mocap_wrapper.logger import getLogger
Log = getLogger(__name__)


@worker  # type: ignore
def i_wilor_mini(env=ENV, **kwargs):
    Log.info("📦 Install WiLoR-mini")
    kwargs.pop('Dir', None)
    txt = txt_from_self('wilor-mini.txt')
    p = mamba(txt=txt, env=env, python='3.10', **kwargs)
    p = txt_pip_retry(txt, env=env)
    p = mamba(py_mgr='pip', pkgs=['git+https://github.com/warmshao/WiLoR-mini'], env=env, **kwargs)
    Log.info("✔ Installed WiLoR-mini")
    return p

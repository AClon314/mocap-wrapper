from mocap_wrapper.install.lib import *
Log = getLogger(__name__)


async def i_wilor_mini(env=ENV, **kwargs):
    Log.info("📦 Install WiLoR-mini")
    kwargs.pop('Dir', None)
    txt = txt_from_self('wilor_mini.txt')
    p = await mamba(txt=txt, env=env, python='3.10', **kwargs)
    p = await txt_pip_retry(txt, env=env)
    p = await mamba(py_mgr='pip', pkgs=['git+https://github.com/warmshao/WiLoR-mini'], env=env, **kwargs)
    Log.info("✔ Installed WiLoR-mini")
    return p

from . import i_python_env
from ..lib import *
Log = getLogger(__name__)


async def i_wilor_mini(Dir: str | Path = CONFIG['wilor'], **kwargs):
    Log.info("📦 Install WiLoR-mini")
    os.makedirs(Dir, exist_ok=True)
    p = await i_python_env(Dir=Dir, pixi_toml='wilor.toml', use_mirror=False)
    if p and p.get_status() == 0:
        Log.info("✔ Installed WiLoR-mini")
    return p

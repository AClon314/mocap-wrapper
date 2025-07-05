from . import i_python_env
from ..lib import *
Log = getLogger(__name__)
DIR_WILOR = Path(CONFIG['search_dir'], 'WiLoR-mini')


async def i_wilor_mini(Dir: str | Path = DIR_WILOR, **kwargs):
    Log.info("📦 Install WiLoR-mini")
    p = await i_python_env(Dir=Dir, pixi_toml='wilor.toml', use_mirror=False)
    Log.info("✔ Installed WiLoR-mini")
    CONFIG['wilor'] = True
    return p

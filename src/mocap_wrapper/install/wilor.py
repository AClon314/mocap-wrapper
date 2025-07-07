from . import i_python_env
from ..lib import *
Log = getLogger(__name__)
name = RUNS_REMAP['wilor']


async def i_wilor_mini(Dir: str | Path = CONFIG['wilor'], **kwargs):
    Log.info(f"📦 Install {name}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/warmshao/WiLoR-mini {Dir}', **kwargs).Await(TIMEOUT_MINUTE)
    p = await i_python_env(Dir=Dir, pixi_toml='wilor.toml', use_mirror=False)
    if p and p.get_status() == 0:
        Log.info(f"✔ Installed {name}")
    return p

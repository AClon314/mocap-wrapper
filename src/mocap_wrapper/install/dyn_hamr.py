from . import i_python_env
from ..lib import *
Log = getLogger(__name__)
name = RUNS_REMAP['dynhamr']


async def i_dyn_hamr(Dir: str | Path = CONFIG['dynhamr'], **kwargs):
    Log.info(f"📦 Install {name}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/ZhengdiYu/Dyn-HaMR {Dir}', **kwargs).Await(TIMEOUT_MINUTE)
    # p = await git_pull(Dir=Dir)

    # TODO: mano symlink
    p = await i_python_env(Dir=Dir, pixi_toml='dynhamr.toml')
    if p and p.get_status() == 0:
        Log.info(f"✔ Installed {name}")
    return p

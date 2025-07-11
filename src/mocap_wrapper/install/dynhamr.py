from .static import i_python_env, git_pull
from ..lib import *
Log = getLogger(__name__)
_name_ = RUNS_REPO['dynhamr']


async def i_dyn_hamr(Dir: str | Path = CONFIG['dynhamr'], **kwargs):
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/ZhengdiYu/Dyn-HaMR {Dir}', **kwargs).Await(TIMEOUT_MINUTE)
    tasks = [
        git_pull(Dir=Dir),
        i_python_env(Dir=Dir, pixi_toml='dynhamr.toml')
    ]

    # TODO: mano symlink
    if p and p.get_status() == 0:
        Log.info(f"✔ Installed {_name_}")
    return p

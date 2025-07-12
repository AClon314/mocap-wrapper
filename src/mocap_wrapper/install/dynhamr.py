from .static import gather_notify, i_python_env, git_pull
from .huggingface import i_hugging_face
from ..lib import *
Log = getLogger(__name__)
_STEM = 'dynhamr'
_name_ = RUNS_REPO[_STEM]


async def i_dyn_hamr(Dir: str | Path = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/ZhengdiYu/Dyn-HaMR {Dir}').Await(TIMEOUT_MINUTE)
    tasks = [
        git_pull(Dir=Dir),
        i_python_env(Dir=Dir, pixi_toml=f'{_STEM}.toml'),
        i_hugging_face(_STEM),
    ]
    return await gather_notify(tasks, success_msg=f'Installed {_name_}')

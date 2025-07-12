from .static import gather_notify, i_python_env
from .huggingface import i_hugging_face
from ..lib import *
Log = getLogger(__name__)
_STEM = 'wilor'
_name_ = RUNS_REPO[_STEM]


async def i_wilor_mini(Dir: str | Path = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/warmshao/WiLoR-mini {Dir}').Await(TIMEOUT_MINUTE)
    tasks = [
        i_python_env(Dir=Dir, pixi_toml=f'{_STEM}.toml', use_mirror=False),
        i_hugging_face(_STEM),
    ]
    return await gather_notify(tasks, success_msg=f'Installed {_name_}')

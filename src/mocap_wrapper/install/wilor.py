from .static import gather, i_python_env, Git
from .huggingface import i_hugging_face
from ..lib import *
Log = getLogger(__name__)
_STEM = 'wilor'
_name_ = RUNS_REPO[_STEM]


async def i_wilor(Dir: str | Path = CONFIG[_STEM]):
    '''install wilor-mini'''
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    if not Path(Dir).exists():
        await Git(['clone', 'https://github.com/warmshao/WiLoR-mini', str(Dir)])
    tasks = [
        i_python_env(Dir=Dir, pixi_toml=f'{_STEM}.toml', use_mirror=False),
        i_hugging_face(_STEM),
    ]
    return await gather(tasks, success_msg=f'Installed {_name_}')

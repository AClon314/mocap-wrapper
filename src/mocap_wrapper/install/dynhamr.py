from .static import gather_notify, i_python_env, git_pull
from .huggingface import i_hugging_face
from ..lib import *
Log = getLogger(__name__)
_STEM = 'dynhamr'
_name_ = RUNS_REPO[_STEM]


async def i_dynhamr(Dir: Path | str = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/ZhengdiYu/Dyn-HaMR {Dir}').Await(TIMEOUT_MINUTE)
    tasks = [
        i_thirdparty(Dir=Dir),
        i_hugging_face(_STEM),
    ]
    return await gather_notify(tasks, success_msg=f'Installed {_name_}')


async def i_thirdparty(Dir: Path | str = CONFIG[_STEM]):
    p = await git_pull(Dir=Dir)
    p = await i_python_env(Dir=Dir, pixi_toml=f'{_STEM}.toml', use_mirror=False)
    if not p:
        return ([], [Exception('pixi install failed')])
    tasks = [
        i_dpvo(),
    ]
    return await gather_notify(tasks)


async def i_dpvo(setup_py=Path(CONFIG[_STEM], 'third-party', 'DROID-SLAM', 'setup.py')):
    '''install DROID-SLAM with CUDA compiling job'''
    return await Python(_STEM, str(setup_py), 'install')

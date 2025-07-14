from warnings import deprecated
from .static import gather_notify, i_python_env, git_pull, Git
from .huggingface import i_hugging_face
from ..lib import *
Log = getLogger(__name__)
_STEM = 'dynhamr'
_name_ = RUNS_REPO[_STEM]


async def i_dynhamr(Dir: Path | str = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_}")
    os.makedirs(Dir, exist_ok=True)
    p = await Git(['clone', 'https://github.com/ZhengdiYu/Dyn-HaMR', str(Dir)])
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


# @deprecated('You can download *.npy from ...')
async def i_bmc(Dir=Path(CONFIG[_STEM], 'Hand-BMC-pytorch')):
    '''if *.npy is not ready-made, we build from BMC'''
    if Path(CONFIG[_STEM], 'BMC').exists():
        Log.info('skip BMC pre-calculation, `BMC/` already exists')
        return ([], [])
    p = await Git(['clone', 'https://github.com/MengHao666/Hand-BMC-pytorch', str(Dir)])
    if not p:
        return ([], [Exception('BMC git clone failed')])
    p = await i_python_env(Dir=Dir, pixi_toml='BMC.toml', use_mirror=False)
    # joints_zip = Path(Dir, 'joints.zip')  # from google drive or baidu pan
    # p = await unzip(joints_zip, Dir)
    p = await Python(Dir, str(Dir.joinpath('calculate_bmc.py')))  # type: ignore

if __name__ == '__main__':
    import asyncio
    asyncio.run(i_bmc())

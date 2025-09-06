from .static import gather, i_python_env, git_pull, Git, run_1by1
from .huggingface import i_hugging_face
from ..lib import *

Log = getLogger(__name__)
_STEM = "dynhamr"
_name_ = RUNS_REPO[_STEM]


async def i_dynhamr(Dir: Path | str = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_}")
    if not Path(Dir, ".git").exists():
        await Git(["clone", "https://github.com/ZhengdiYu/Dyn-HaMR", str(Dir)])
    tasks = [
        i_thirdparty(Dir=Dir),
        i_hugging_face(_STEM),
    ]
    return await gather(tasks, success_msg=f"Installed {_name_}")


def i_thirdparty(Dir: Path | str = CONFIG[_STEM]):
    queue = [
        i_python_env(Dir=Dir, pixi_toml=f"{_STEM}.toml", use_mirror=False),
        ENV_cuda_toolkit(),
        i_dpvo(),
    ]
    if not Path(Dir, "third-party", "DROID-SLAM", "setup.py").exists():
        queue.insert(0, git_pull())
    return run_1by1(queue)


async def ENV_cuda_toolkit(Dir: Path | str = CONFIG[_STEM]):
    CUDA_HOME = Path(Dir, ".pixi", "envs", "default")
    if CUDA_HOME and CUDA_HOME.exists():
        os.environ["CUDA_HOME"] = str(CUDA_HOME)
        Log.info(f"{CUDA_HOME=}")
    else:
        Log.error("CUDA_HOME not set, please check your pixi installation")


def i_dpvo(setup_py=Path(CONFIG[_STEM], "third-party", "DROID-SLAM", "setup.py")):
    return Python(
        setup_py, "install", run=_STEM
    )  # '''install DROID-SLAM with CUDA compiling job'''


# @deprecated('You can download *.npy from ...')
def i_bmc(Dir=Path(CONFIG[_STEM], "Hand-BMC-pytorch")):
    """if *.npy is not ready-made, we build from BMC"""
    if_missing_then_calc = {
        Path(CONFIG[_STEM], "_DATA", "BMC", "bone_len_max.npy"): Python(
            Dir / "calculate_bmc.py", run="dynhamr", env="bmc"
        ),
        Path(CONFIG[_STEM], "_DATA", "BMC", "CONVEX_HULLS.npy"): Python(
            Dir / "calculate_convex_hull.py", run="dynhamr", env="bmc"
        ),
    }
    queue = []
    _gather = []
    if not Path(Dir).exists():
        _gather.append(
            Git(["clone", "https://github.com/ZhengdiYu/Dyn-HaMR", str(Dir)])
        )
    _gather.append(
        i_python_env(Dir=Dir, pixi_toml=f"{_STEM}.toml", env="bmc", use_mirror=False)
    )
    queue.append(gather(_gather))
    # joints_zip = Path(Dir, 'joints.zip')  # from google drive or baidu pan
    # p = await unzip(joints_zip, Dir)
    is_missing = False
    for filepath, coro in if_missing_then_calc.items():
        if not filepath.exists():
            queue.append(coro)
            is_missing = True
    if not is_missing:
        queue = []
    os.chdir(Dir)  # fix: relative open files under BMC/*.npy
    if is_linux:
        os.environ["QT_QPA_PLATFORM"] = (
            "xcb"  # fix: This application failed to start because it could not find or load the Qt platform plugin "wayland" in "". Available platform plugins are: eglfs, minimal, minimalegl, offscreen, vnc, xcb.
        )
    return run_1by1(queue)


# def i_human_body_prior(Dir=Path(CONFIG[_STEM], 'dyn-hamr', 'human_body_prior')):
#     '''install human_body_prior'''
#     if Path(Dir).exists():
#         Log.info('skip human_body_prior, `human_body_prior/` already exists')
#     queue = [
#         Git(['clone', 'https://github.com/nghorbani/human_body_prior', str(Dir)]),
#         Python('setup.py', 'develop', run=_STEM),
#     ]
#     return run_1by1(queue)


if __name__ == "__main__":
    import asyncio

    asyncio.run(i_bmc())

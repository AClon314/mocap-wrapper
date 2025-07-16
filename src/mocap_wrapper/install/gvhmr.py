import os
from pathlib import Path
from .static import gather, i_python_env, Git
from .huggingface import i_hugging_face
from ..lib import TIMEOUT_MINUTE, TIMEOUT_QUATER, RUNS_REPO, CONFIG, IS_DEBUG, getLogger, get_uncomplete, run_tail, res_path, File, download, unzip
Log = getLogger(__name__)
_STEM = 'gvhmr'
_name_ = RUNS_REPO[_STEM]


async def i_gvhmr(Dir: str | Path = CONFIG[_STEM]):
    Log.info(f"📦 Install {_name_} at {CONFIG[_STEM]}")
    os.makedirs(Dir, exist_ok=True)
    p = await Git(['clone', 'https://github.com/zju3dv/GVHMR', str(Dir)])
    link_config(Dir)
    # dir_checkpoints = str(Path(Dir, 'inputs', 'checkpoints'))
    # os.makedirs(Path(dir_checkpoints, 'body_models'), exist_ok=True)

    tasks = [
        i_python_env(Dir=Dir, pixi_toml='gvhmr.toml'),
        i_dl_models(),
        # git_pull(Dir=Dir),
        # i_dpvo(Dir=Path(Dir, 'third-party/DPVO')),
    ]
    return await gather(tasks, f'Installed {_name_}')


def link_config(Dir: Path | str = CONFIG[_STEM], file='gvhmr.yaml'):
    src = res_path(module='install', file=file)
    dst = Path(Dir, 'hmr4d', 'configs', file)
    if dst.exists() and dst.readlink() == src:
        return
    try:
        os.link(src, dst)
    except Exception as e:
        Log.exception('', exc_info=e) if IS_DEBUG else None
        Log.warning(f"🔗 Skip link, you can delete {dst.name}: {e}")


async def i_dl_models():
    p = await i_hugging_face(_STEM)
    if not p:
        Log.error(f"Please download GVHMR models at https://huggingface.co or https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link")
    return p


async def i_dpvo(Dir: Path | str = CONFIG['search_dir']):
    Log.info("📦 Install DPVO")
    f = File('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',
             path=Path(Dir, 'eigen-3.4.0.zip'), md5='994092410ba29875184f7725e0371596')
    dl = download(f)
    if not get_uncomplete(dl) and f.exists():
        p = await unzip(f.path, to=os.path.join(Dir, 'thirdparty'))
        # remove_if_p(f.path)    # TODO: remove_if_p
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")
    p = await run_tail(['pixi', 'add', '--pypi', '.']).Await(TIMEOUT_QUATER)  # TODO
    Log.info("✔ Add DPVO")
    return p

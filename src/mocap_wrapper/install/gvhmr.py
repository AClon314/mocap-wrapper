import os
import asyncio
from pathlib import Path
from .static import i_python_env
from .huggingface import i_hugging_face
from ..lib import TIMEOUT_MINUTE, TIMEOUT_QUATER, RUNS_REPO, CONFIG, getLogger, get_uncomplete, run_tail, symlink, res_path, File, download, unzip
Log = getLogger(__name__)
_name_ = RUNS_REPO['gvhmr']


def i_config(Dir: str | Path = CONFIG['gvhmr'], file='gvhmr.yaml'):
    src = res_path(module='install', file=file)
    dst = os.path.join(Dir, 'hmr4d', 'configs', file)
    symlink(str(src), dst)


async def i_models(Dir: str | Path = CONFIG['gvhmr']):
    p = await i_hugging_face('gvhmr')
    if not p:
        Log.error(f"Please download GVHMR models at https://huggingface.co or https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link")
    return p


async def i_gvhmr(Dir: str | Path = CONFIG['gvhmr'], **kwargs):
    Log.info(f"📦 Install {_name_} at {CONFIG['gvhmr']}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/zju3dv/{_name_} {Dir}', **kwargs).Await(TIMEOUT_MINUTE)
    dir_checkpoints = str(Path(Dir, 'inputs', 'checkpoints'))
    os.makedirs(Path(dir_checkpoints, 'body_models'), exist_ok=True)
    i_config(Dir)

    tasks = [
        i_python_env(Dir=Dir, pixi_toml='gvhmr.toml'),
        i_models(Dir=dir_checkpoints),
        # git_pull(Dir=Dir),
        # i_dpvo(Dir=Path(Dir, 'third-party/DPVO')),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    exceptions = [r for r in results if isinstance(r, Exception)]
    if exceptions:
        [Log.exception(e, exc_info=e) for e in exceptions]
    else:
        Log.info(f"✔ Installed {_name_}")
    return results


async def i_dpvo(Dir: str | Path = CONFIG['search_dir'], **kwargs):
    Log.info("📦 Install DPVO")
    f = File('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',
             path=Path(Dir, 'eigen-3.4.0.zip'), md5='994092410ba29875184f7725e0371596')
    dl = download(f)
    if not get_uncomplete(dl) and f.exists():
        p = await unzip(f.path, to=os.path.join(Dir, 'thirdparty'), **kwargs)
        # remove_if_p(f.path)    # TODO: remove_if_p
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")
    p = await run_tail(['pixi', 'add', '--pypi', '.']).Await(TIMEOUT_QUATER)  # TODO
    Log.info("✔ Add DPVO")
    return p


if __name__ == '__main__':
    ...

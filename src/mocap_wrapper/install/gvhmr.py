import os
import asyncio
from pathlib import Path
from . import i_python_env
from .smpl import i_smplx
from .Gdown import google_drive
from ..lib import TIMEOUT_MINUTE, TIMEOUT_QUATER, CONFIG, getLogger, run_tail, symlink, res_path, File, download, is_complete, wait_slowest_dl, unzip
DIR_GVHMR = Path(CONFIG['search_dir'], 'GVHMR')
Log = getLogger(__name__)


def i_config(Dir: str | Path = DIR_GVHMR, file='gvhmr.yaml'):
    src = res_path(module='install', file=file)
    dst = os.path.join(Dir, 'hmr4d', 'configs', file)
    symlink(str(src), dst)


async def i_models(Dir: str | Path = DIR_GVHMR):
    Log.info("📦 Download GVHMR pretrained models (📝 By downloading, you agree to the GVHMR's corresponding licences)")
    DOMAIN = 'hf-mirror.com' if CONFIG.is_mirror else 'huggingface.co'
    HUG_GVHMR = f'https://{DOMAIN}/camenduru/GVHMR/resolve/main/'
    LFS = {
        ('dpvo', 'dpvo.pth'): {
            'GD_ID': '1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0',   # Google Drive ID
            'md5': 'a0f9fe5b98171bd4e63bba2d98077642',
        },
        ('gvhmr', 'gvhmr_siga24_release.ckpt'): {
            'GD_ID': '1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP',
            'md5': '5203aeed445c5270eea9daa042887422',
        },
        ('hmr2', 'epoch=10-step=25000.ckpt'): {
            'GD_ID': '1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc',
            'md5': '83fe68195d3e75c42d9acc143dfe4f32',
        },
        ('vitpose', 'vitpose-h-multi-coco.pth'): {
            'GD_ID': '1sR8xZD9wrZczdDVo6zKscNLwvarIRhP5',
            'md5': 'f4f688596b67696967c700b497a44804',
        },
        ('yolo', 'yolov8x.pt'): {
            'GD_ID': '1_HGm-lqIH83-M1ML4bAXaqhm_eT2FKo5',
            'md5': '1b82eaab0786b77a43e2394856604f08',
        },
    }
    files: list[File] = []
    for out, dic in LFS.items():
        urls = [HUG_GVHMR + '/'.join(out)]
        if not CONFIG.is_mirror:
            try:
                urls.append(google_drive(id=dic['GD_ID']))
            except Exception as e:
                Log.info(f'Skip Google drive for {out} from {dic["GD_ID"]}: {e}')
        files.append(File(*urls, path=Path(Dir, *out), md5=dic['md5']))
    dls = download(*files)
    await wait_slowest_dl(dls)
    if is_complete(dls):
        Log.info("✔ Download GVHMR models")
    else:
        Log.error(f"Please download GVHMR models at {HUG_GVHMR} or https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link")
    return dls


async def i_gvhmr(Dir: str | Path = DIR_GVHMR, **kwargs):
    Log.info(f"📦 Install GVHMR at {DIR_GVHMR}")
    os.makedirs(Dir, exist_ok=True)
    p = await run_tail(f'git clone https://github.com/zju3dv/GVHMR {Dir}', **kwargs).Await(TIMEOUT_MINUTE)
    dir_checkpoints = str(Path(Dir, 'inputs', 'checkpoints'))
    os.makedirs(Path(dir_checkpoints, 'body_models'), exist_ok=True)
    i_config(Dir)

    tasks = [
        i_python_env(Dir=Dir, pixi_toml='gvhmr.toml'),
        i_smplx(Dir=dir_checkpoints, **kwargs),
        i_models(Dir=dir_checkpoints),
        # git_pull(),
        # i_dpvo(Dir=Path(Dir, 'third-party/DPVO')),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    exceptions = [r for r in results if isinstance(r, Exception)]
    if exceptions:
        [Log.exception(e, exc_info=e) for e in exceptions]
    else:
        Log.info("✔ Installed GVHMR")
        CONFIG['gvhmr'] = True
    return results


async def i_dpvo(Dir: str | Path = CONFIG['search_dir'], **kwargs):
    Log.info("📦 Install DPVO")
    f = File('https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',
             path=Path(Dir, 'eigen-3.4.0.zip'), md5='994092410ba29875184f7725e0371596')
    dl = download(f)
    if is_complete(dl) and f.exists():
        p = await unzip(f.path, to=os.path.join(Dir, 'thirdparty'), **kwargs)
        # remove_if_p(f.path)    # TODO: remove_if_p
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")
    p = await run_tail(['pixi', 'add', '--pypi', '.']).Await(TIMEOUT_QUATER)  # TODO
    Log.info("✔ Add DPVO")
    return p


if __name__ == '__main__':
    ...

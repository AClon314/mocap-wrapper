from functools import partial
import os
from mocap_wrapper.Gdown import google_drive
from mocap_wrapper.logger import getLogger
from mocap_wrapper.lib import *
from mocap_wrapper.install.lib import *
Log = getLogger(__name__)


async def i_gvhmr_models(Dir=DIR, **kwargs):
    Log.info("📦 Download GVHMR pretrained models (📝 By downloading, you agree to the GVHMR's corresponding licences)")
    Dir = path_expand(Dir)
    URL_HUGGINGFACE = 'https://huggingface.co/camenduru/GVHMR/resolve/main/'
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
    LFS_SMPL = {
        ('body_models', 'smpl', 'SMPL_NEUTRAL.pkl'): {
            'md5': 'b78276e5938b5e57864b75d6c96233f7'
        },
        ('body_models', 'smplx', 'SMPLX_NEUTRAL.npz'): {
            'md5': '6eed2e6dfee62a3f4fb98dcd41f94e06'
        }
    }
    coros = []
    try:
        for out, dic in LFS.items():
            url = URL_HUGGINGFACE + '/'.join(out)
            t = download(url, md5=dic['md5'], out=os.path.join(Dir, *out))
            coros.append(t)
        for out, dic in LFS_SMPL.items():
            url = URL_HUGGINGFACE + out[-1]
            t = download(url, md5=dic['md5'], out=os.path.join(Dir, *out))
            coros.append(t)
        results = await aio.gather(*coros)

        coros = []
        PATH_MODEL = [os.path.join(Dir, *out) for out in LFS.keys()]
        IS_MODEL = all([os.path.exists(p) for p in PATH_MODEL])
        if not IS_MODEL:
            for out, dic in LFS.items():
                url = google_drive(id=dic['GD_ID'])
                t = download(url, md5=dic['md5'], out=os.path.join(Dir, *out))
                coros.append(t)
        PATH_SMPL = [os.path.join(Dir, *out) for out in LFS_SMPL.keys()]
        IS_SMPL = all([os.path.exists(p) for p in PATH_SMPL])
        if not IS_SMPL:
            coros.append(i_smpl(Dir=os.path.join(Dir, 'body_models'), **kwargs))
        results = await aio.gather(*coros)

        Log.info("✔ Download GVHMR pretrained models")
    except Exception as e:
        Log.error(f"❌ please download GVHMR pretrained models manually from: 'https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link', error: {e}")


async def i_gvhmr(Dir=DIR, env=ENV, **kwargs):
    Log.info("📦 Install GVHMR")
    p = mamba(env=env, python='3.10', **kwargs)
    Dir = path_expand(Dir)
    d = ExistsPathList(chdir=Dir)
    Dir = os.path.join(Dir, 'GVHMR')
    if not os.path.exists(Dir):
        p = await popen('git clone https://github.com/zju3dv/GVHMR', Raise=False, **kwargs)
    d.chdir('GVHMR')
    dir_checkpoints = path_expand(os.path.join('inputs', 'checkpoints'))
    os.makedirs(os.path.join(dir_checkpoints, 'body_models'), exist_ok=True)

    async def i_gvhmr_post():
        txt = txt_from_self('gvhmr.txt')
        p = await mamba(env=env, txt=txt, **kwargs)
        p = await txt_pip_retry(txt, env=env)
        return p

    async def git_mamba():
        p = await git_pull()
        p = await mamba(f'pip install -e {os.getcwd()}', env=env, **kwargs)
        return p

    tasks = [
        git_mamba(),
        i_gvhmr_post(),
        i_dpvo(Dir=os.path.join(Dir, 'third-party/DPVO'), env=env, **kwargs),
        i_gvhmr_models(Dir=dir_checkpoints, **kwargs)
    ]
    tasks = await aio.gather(*tasks)
    Log.info("✔ Installed GVHMR")

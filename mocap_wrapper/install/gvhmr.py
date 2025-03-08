import os
from mocap_wrapper.Gdown import google_drive
from mocap_wrapper.logger import getLogger
from mocap_wrapper.lib import *
from mocap_wrapper.install.lib import *
Log = getLogger(__name__)


@async_worker
async def i_gvhmr_models(Dir=DIR, duration=RELAX):
    Log.info("📦 Download GVHMR pretrained models (📝 By downloading, you agree to the GVHMR's corresponding licences)")
    Dir = path_expand(Dir)
    G_drive = {
        ('dpvo', 'dpvo.pth'): {
            'ID': '1DE5GVftRCfZOTMp8YWF0xkGudDxK0nr0',
            'md5': 'a0f9fe5b98171bd4e63bba2d98077642',
        },
        ('gvhmr', 'gvhmr_siga24_release.ckpt'): {
            'ID': '1c9iCeKFN4Kr6cMPJ9Ss6Jdc3SZFnO5NP',
            'md5': '5203aeed445c5270eea9daa042887422',
        },
        ('hmr2', 'epoch=10-step=25000.ckpt'): {
            'ID': '1X5hvVqvqI9tvjUCb2oAlZxtgIKD9kvsc',
            'md5': '83fe68195d3e75c42d9acc143dfe4f32',
        },
        ('vitpose', 'vitpose-h-multi-coco.pth'): {
            'ID': '1sR8xZD9wrZczdDVo6zKscNLwvarIRhP5',
            'md5': 'f4f688596b67696967c700b497a44804',
        },
        ('yolo', 'yolov8x.pt'): {
            'ID': '1_HGm-lqIH83-M1ML4bAXaqhm_eT2FKo5',
            'md5': '1b82eaab0786b77a43e2394856604f08',
        },
    }
    coros = []
    try:
        for out, dic in G_drive.items():
            url = google_drive(id=dic['ID'])
            t = download(url, md5=dic['md5'], out=os.path.join(Dir, *out))
            coros.append(t)
        results = await aio.gather(*await run_1by1(coros))
        Log.info("✔ Download GVHMR pretrained models")
    except Exception as e:
        Log.error(f"❌ please download GVHMR pretrained models manually from: 'https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link', error: {e}")


@async_worker
async def i_gvhmr(Dir=DIR, env=ENV, **kwargs):
    Log.info("📦 Install GVHMR")
    p = mamba(env=env, python='3.10', **kwargs)
    Dir = path_expand(Dir)
    d = ExistsPathList(chdir=Dir)
    Dir = os.path.join(Dir, 'GVHMR')
    if not os.path.exists(Dir):
        p = Popen('git clone https://github.com/zju3dv/GVHMR', Raise=False, **kwargs)
    d.chdir('GVHMR')
    dir_checkpoints = path_expand(os.path.join('inputs', 'checkpoints'))
    dir_smpl = os.path.join(dir_checkpoints, 'body_models')
    os.makedirs(dir_smpl, exist_ok=True)

    @worker
    def i_gvhmr_post():
        p = Popen('git fetch --all', Raise=False, **kwargs)
        p = Popen('git pull', Raise=False, **kwargs)
        p = Popen('git submodule update --init --recursive', Raise=False, **kwargs)
        txt = txt_from_self('gvhmr.txt')
        p = mamba(env=env, txt=txt, **kwargs)
        p = mamba(f'pip install -e {os.getcwd()}', env=env, **kwargs)
        p = txt_pip_retry(txt, env=env)
        return p
    i_gvhmr_post()  # should non blocking in new thread

    tasks = [
        i_dpvo(Dir=os.path.join(Dir, 'third-party/DPVO'), env=env, **kwargs),
        i_smpl(Dir=dir_smpl, **kwargs),
        i_gvhmr_models(Dir=dir_checkpoints, **kwargs)
    ]
    tasks = [await t for t in tasks]    # should non bloking in new threads
    ThreadWorkerManager.await_workers(*tasks)   # should block
    Log.info("✔ Installed GVHMR")

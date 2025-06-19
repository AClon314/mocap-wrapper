from mocap_wrapper.lib import *


async def i_dpvo(Dir=DIR, env=ENV, **kwargs):
    Log.info("📦 Install DPVO")
    f = await download(
        'https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip',
        md5='994092410ba29875184f7725e0371596',
        dir=Dir
    )
    if f.is_complete and os.path.exists(f.path):
        p = unzip(f.path, to=os.path.join(Dir, 'thirdparty'), **kwargs)
        # remove_if_p(f.path)    # TODO: remove_if_p
    else:
        Log.error("❌ Can't unzip Eigen to third-party/DPVO/thirdparty")

    txt = res_path(file='dpvo.txt')
    p = mamba(env=env, txt=txt, **kwargs)
    p = txt_pip_retry(txt, env=env)

    if is_win:
        Log.warning("`export` not supported windows yet")
    else:
        # TODO these seems unnecessary
        CUDA = '/usr/local/cuda-12.1/'.split('/')
        CUDA = os.path.join(*CUDA)
        if os.path.exists(CUDA):
            PATH.append(os.path.join(CUDA, 'bin'))
            os.environ['CUDA_HOME'] = CUDA
        else:
            Log.warning(f"❌ CUDA not found in {CUDA}")
    p = mamba(f'pip install -e {Dir}', env=env, **kwargs)

    Log.info("✔ Installed DPVO")
    return p

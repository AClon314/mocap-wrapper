import os
import re
import asyncio
from pathlib import Path
from huggingface_hub import HfApi
from typing import Literal, Sequence
from .static import TYPE_RUNS, gather_notify
from ..lib import Global, CONFIG, RUNS, IS_DEBUG, copy_args, getLogger
Log = getLogger(__name__)
TYPE_HUGFACE = TYPE_RUNS | Literal['smplx']
TYPE_REMOTE_LOCAL = dict[Path, list[Path]]
TYPE_FILE_RUN_DIR = dict[str, dict[TYPE_HUGFACE, str]]
RUN_TO_REPOS: dict[TYPE_RUNS, list[TYPE_HUGFACE]] = {
    'gvhmr': ['smplx'],
    'dynhamr': ['wilor'],
}
OWNER_REPO: dict[TYPE_HUGFACE, str] = {
    'smplx': 'camenduru/SMPLer-X',
    'gvhmr': 'camenduru/gvhmr',
    'wilor': 'warmshao/WiLoR-mini',
    'dynhamr': 'Zhengdi/Dyn-HaMR',
    'hamer': 'ZhengdiYu/HameR',
}
FILTERS: dict[TYPE_HUGFACE, str | TYPE_FILE_RUN_DIR] = {
    'smplx': {
        'SMPL_NEUTRAL.pkl': {
            'gvhmr': 'body_models/smpl',
        },
        'SMPLX_NEUTRAL.npz': {
            'gvhmr': 'body_models/smplx',
        },
    },
    'wilor': {
        'MANO_RIGHT.pkl': {
            'dynhamr': 'data/mano',
            'wilor': '',
        },
        'mano_mean_params.npz': {
            'dynhamr': 'data',
            'wilor': '',
        },
        'wilor_final.ckpt': {'wilor': ''},
        'detector.pt': {'wilor': ''},
    },
    'gvhmr': r'^(?!preproc_data|\.).*',
}
REPO_TO_LOCAL_PATH_PREFIX: dict[TYPE_RUNS, str] = {
    'gvhmr': 'inputs/checkpoints',
    'wilor': 'wilor_mini/pretrained_models',
    'dynhamr': '_DATA',
}


async def i_hugging_face(*run: TYPE_RUNS, concurrent=2):
    '''Download models from Hugging Face. `Dir` depends on `CONFIG`'''
    Log.info(f"📦 Download {run} models (📝 By downloading, you agree to the corresponding licences)")
    repos: list[TYPE_HUGFACE] = list(run)
    for k in run:
        repos.extend(RUN_TO_REPOS.get(k, []))
    repos = list(set(repos))  # 去重
    repo_to_rl: dict[TYPE_HUGFACE, TYPE_REMOTE_LOCAL] = {}
    for repo in repos:
        repo_id: str = OWNER_REPO[repo]
        remote_paths = await asyncio.to_thread(Global.HF.list_repo_files, repo_id=repo_id)  # request 1 by 1
        remote_paths = [f for f in remote_paths if not (f.startswith('.') or f.startswith('README'))]  # 排除隐藏文件
        Filters = FILTERS.get(repo, '.*')
        rl_paths: TYPE_REMOTE_LOCAL = {}
        for str_path in remote_paths:
            Rpath = Path(str_path)

            if isinstance(Filters, str):
                if repo not in run:
                    break
                if not re.match(Filters, str_path):
                    continue
                rl_paths[Rpath] = [Path(
                    CONFIG.get(repo, ''),
                    REPO_TO_LOCAL_PATH_PREFIX.get(repo, ''),
                    Rpath.parent
                )]
            else:
                is_pick = False
                for filename, run_dir in Filters.items():
                    if Rpath.name == filename:
                        is_pick = True
                        break
                if is_pick == False:
                    continue
                rl_paths[Rpath] = [Path(
                    CONFIG.get(_run, ''),
                    REPO_TO_LOCAL_PATH_PREFIX.get(_run, ''),   # type: ignore
                    dir
                ) for _run, dir in run_dir.items() if _run in RUNS]
        repo_to_rl[repo] = rl_paths
    Log.debug(f'{repo_to_rl=}')
    semaphore = asyncio.Semaphore(concurrent)  # 最多2个并发

    @copy_args(HfApi.hf_hub_download)
    async def dl(self=Global.HF, *args, dsts: list[Path], **kwargs):
        if IS_DEBUG:
            print('⬇️', kwargs, f'{dsts=}')
            return
        async with semaphore:
            kwargs.setdefault('local_dir', dsts[0].parent)
            p = await asyncio.to_thread(self.hf_hub_download, *args, **kwargs)
            os_link(p, dsts[1:])
            return p

    tasks = []
    for repo, rl_paths in repo_to_rl.items():
        repo_id = OWNER_REPO[repo]
        for remote, locals in rl_paths.items():
            srcs = [Path(local, remote.name) for local in locals]
            srcs, dsts = _get_exists_andNot(srcs)
            if srcs:
                # TODO: check srcs[0] sha256
                os_link(srcs[0], dsts)
            else:
                tasks.append(dl(
                    Global.HF, repo_id=repo_id, filename=remote.name,
                    subfolder='/'.join(remote.parent.parts), dsts=dsts))    # type: ignore
    files, exceptions = await gather_notify(tasks, f'Download models {run}')
    if exceptions:
        [Log.error(f"You can download from https://huggingface.co/{OWNER_REPO[k]}/tree/main") for k in run]
    return files, exceptions


def os_link(src: Path | str, dsts: Sequence[Path | str]):
    '''1 src to N dsts, use Log instead of raise'''
    success: Sequence[Path | str] = []
    fail: Sequence[Path | str] = []
    for dst in dsts:
        try:
            os.link(src, dst)
            success.append(dst)
        except Exception as e:
            Log.exception(e, exc_info=e)
            fail.append(dst)
    Log.debug(f"✔ {src} →{success}, ❌ {fail}") if dsts else None
    return success, fail


def _get_exists_andNot(paths: Sequence[Path]):
    exists: list[Path] = []
    not_exists: list[Path] = []
    for p in paths:
        if p.exists():
            exists.append(p)
        else:
            not_exists.append(p)
    return exists, not_exists


# async def i_hugging_face_aria2(key: TYPE_HUGFACE):
#     Log.info(f"📦 Download {key} models (📝 By downloading, you agree to the corresponding licences)")
#     HUG_FACE = HUGFACE.format(domain=DOMAIN_HF, owner_repo=OWNER_REPO[key])
#     files: list[File] = []
#     for hf in LFS[key]:
#         url = HUG_FACE + hf.From
#         files.append(File(url, path=Path(CONFIG[key], *os.path.split(hf.to)), sha256=hf.sha256))
#     dls = download(*files)
#     await wait_slowest_dl(dls)
#     fail = get_uncomplete(dls)
#     if not get_uncomplete(dls):
#         Log.info(f"✔ Download {key} models")

if __name__ == '__main__':
    asyncio.run(i_hugging_face('dynhamr'))

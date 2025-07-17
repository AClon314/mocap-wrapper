import os
import re
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from huggingface_hub import HfApi
from typing import Literal, Sequence
from .static import TYPE_RUNS, gather
from ..lib import Env, CONFIG, is_debug, copy_args, getLogger
Log = getLogger(__name__)
IS_DEBUG = is_debug(Log)
HF_MAIN = 'https://huggingface.co/{}/tree/main'
TYPE_HUGFACE = TYPE_RUNS | Literal['smplx', 'hamer', 'hawor']   # TODO: remove hamer/hawor if supported in run
TYPE_FILE_RUN_DIR = dict[str, dict[TYPE_HUGFACE, str]]
RUN_TO_REPOS: dict[TYPE_HUGFACE, list[TYPE_HUGFACE]] = {
    'gvhmr': ['smplx'],
    'dynhamr': ['hamer', 'hawor'],
}
OWNER_REPO: dict[TYPE_HUGFACE, str] = {
    'smplx': 'camenduru/SMPLer-X',
    'gvhmr': 'camenduru/gvhmr',
    'wilor': 'warmshao/WiLoR-mini',
    'dynhamr': 'Zhengdi/Dyn-HaMR',
    'hamer': 'spaces/geopavlakos/HaMeR',
    'hawor': 'ThunderVVV/HaWoR',
}
REGEX: dict[TYPE_HUGFACE, str] = {
    'smplx': r'SMPL_NEUTRAL\.pkl|SMPLX_NEUTRAL\.npz',
    'gvhmr': r'^(?!preproc_data|\.).*',
    'wilor': r'^(?!.*wilor_vit\.onnx).*',
    'hamer': r'_DATA',
    'hawor': r'.*\.yaml',  # TODO: for test only
}
LOCAL_REMAP: TYPE_FILE_RUN_DIR = {
    'SMPL_NEUTRAL.pkl': {
        'gvhmr': 'body_models/smpl',
    },
    'SMPLX_NEUTRAL.npz': {
        'gvhmr': 'body_models/smplx',
    },
    'MANO_RIGHT.pkl': {
        'dynhamr': 'data/mano',
    },
    'mano_mean_params.npz': {
        'dynhamr': 'data',
    },
    'dataset_config.yaml': {'dynhamr': 'hamer_ckpts'},
    'model_config.yaml': {'dynhamr': 'hamer_ckpts'},
    'hamer.ckpt': {'dynhamr': 'hamer_ckpts/checkpoints'},
    'wholebody.pth': {'dynhamr': 'vitpose_ckpts/vitpose+_huge'},
    'droid.pth': {'dynhamr': ''},
    # TODO: hmp_model/...

}
REPO_TO_LOCAL_PREFIX: dict[TYPE_HUGFACE, str] = {
    'gvhmr': 'inputs/checkpoints',
    'wilor': 'wilor_mini',
    'dynhamr': '_DATA',
}


@dataclass
class _File:
    # name: str
    remotes: dict[TYPE_HUGFACE, list[Path]] = field(default_factory=dict)
    locals: list[Path] = field(default_factory=list)


async def i_hugging_face(*run: TYPE_HUGFACE, concurrent=2):
    '''Download models from Hugging Face. `Dir` depends on `CONFIG`'''
    Log.info(f"📦 Download {run} models (📝 By downloading, you agree to the corresponding licences)")
    repos: list[TYPE_HUGFACE] = list(run)
    for k in run:
        repos.extend(RUN_TO_REPOS.get(k, []))
    repos = list(set(repos))  # 去重
    _files: dict[str, _File] = {}
    for repo in repos:
        repo_id: str = OWNER_REPO[repo]
        repo_type = repo_id.split('/')[0].rstrip('s')
        if repo_type in ['space', 'dataset']:
            repo_id = '/'.join(repo_id.split('/')[1:])  # get owner/repo_name
        else:
            repo_type = None
        remote_paths = await asyncio.to_thread(Env.HF.list_repo_files, repo_id=repo_id, repo_type=repo_type)  # request 1 by 1
        remote_paths = [f for f in remote_paths if not (f.startswith('.') or f.startswith('README'))]  # 排除隐藏文件
        regex = re.compile(REGEX.get(repo, '.*'))
        for str_path in remote_paths:
            Match = regex.match(str_path)
            if not Match:
                continue
            Rpath = Path(str_path)
            run_dir = LOCAL_REMAP.get(Rpath.name, {})
            _locals: list[Path] = []
            if (repo_in_run := repo in run):
                # 当 gvhmr 仅需要 gvhmr 仓库时
                _locals += [Path(
                    CONFIG.get(repo, ''),
                    REPO_TO_LOCAL_PREFIX.get(repo, ''),
                    Rpath
                )]
            if (is_run_dir := set(run).intersection(set(run_dir.keys()))):
                # 当 gvhmr 需要 smplx 仓库时
                _locals += [Path(
                    CONFIG.get(_run, ''),
                    REPO_TO_LOCAL_PREFIX.get(_run, ''),  # type: ignore
                    dir, Rpath.name
                ) for _run, dir in run_dir.items()]
            if not (is_run_dir or repo_in_run):
                continue
            Log.debug(f'{repo=} {repo_in_run=},{is_run_dir=}\t{_locals=}')
            _file = _files.setdefault(Rpath.name, _File())
            _file.remotes.setdefault(repo, []).append(Rpath)
            _file.locals.extend(_locals)

    for fname, _file in _files.items():
        _file.locals = list(set(_file.locals))  # 去重

    if IS_DEBUG:
        import pprint
        Log.debug(f'_files={len(_files.keys())}\n' + pprint.pformat(_files, indent=2))
    semaphore = asyncio.Semaphore(concurrent)  # 最多n个并发

    @copy_args(HfApi.hf_hub_download)
    async def dl(self=Env.HF, *args, dsts: list[Path], **kwargs):
        _dst = dsts[0]
        filename = str(kwargs.get('filename', args[1] if len(args) > 1 else ''))
        _dir = _dst.resolve().parent if Path(filename).parent == _dst.parent.name else _dst   # TODO: hf_hub_download replicate file structure! like dpvo/dpvo/dpvo.ckpt
        _dir = _dir if _dir.is_dir() else _dir.parent
        if IS_DEBUG:
            print('⬇', kwargs, f'{dsts=} {locals()=}')
            return
        if not dsts:
            Log.error(f"No destination paths provided for {kwargs=}{args=}")
            return
        kwargs.setdefault('local_dir', str(_dir))
        async with semaphore:
            src = await asyncio.to_thread(self.hf_hub_download, *args, **kwargs)
            if Path(src) != _dst:
                import shutil
                shutil.move(src, _dst)
            os_link(_dst, dsts[1:])
            return src

    tasks = []
    exceptions = []
    for fname, _file in _files.items():
        repo = list(_file.remotes.keys())[0]
        rpath = _file.remotes[repo][0]
        repo_id = OWNER_REPO[repo]
        srcs, dsts = _get_exists_andNot(_file.locals)
        if srcs:
            try:
                os_link(srcs[0], dsts)
            except Exception as e:
                Log.exception('', exc_info=e)
                exceptions.append(e)
        else:
            tasks.append(dl(
                Env.HF, repo_id=repo_id, filename=str(rpath), dsts=dsts))    # type: ignore
    _, files, _e = await gather(tasks, f'Download models {run}')
    exceptions.extend(_e)
    if exceptions:
        Log.error(f"Try download from {[HF_MAIN.format(OWNER_REPO[k]) for k in repos]}")
    return files, exceptions


def os_link(src: Path | str, dsts: Sequence[Path | str]):
    '''1 src to N dsts, can raise'''
    for dst in dsts:
        dst = Path(dst)
        if not (dst.exists() and dst.readlink() == src):
            os.link(src, dst)


def _get_exists_andNot(paths: Sequence[Path]):
    exists: list[Path] = []
    not_exists: list[Path] = []
    for p in paths:
        if p.exists():
            exists.append(p)
        else:
            not_exists.append(p)
    return exists, not_exists

# HUGFACE = 'https://{domain}/{owner_repo}/resolve/main/'
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
    # asyncio.run(i_hugging_face('dynhamr', 'gvhmr', 'wilor'))
    asyncio.run(i_hugging_face('hawor'))

import aria2p
import asyncio
from pathlib import Path
from netscape_cookies import save_cookies_to_file
from mocap_wrapper.lib import CONFIG, DIR, File, getLogger, symlink, unzip, download, is_complete, wait_slowest
from typing import Dict, TypedDict, Unpack
Log = getLogger(__name__)
HUG_SMPLX = 'https://{}/camenduru/SMPLer-X/resolve/main/'


class Kw_itmd_coro(TypedDict, total=False):
    md5: str
    duration: float
    dry_run: bool


class Kw_itmd(Kw_itmd_coro, total=False):
    Dir: str
    url: str
    referer: str
    PHPSESSID: str
    user_agent: str


class Kw_i_smpl(Kw_itmd):
    From: str
    to: str


def download_tue_mpg(
    url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
    path=Path(DIR, 'SMPL_python_v.1.1.0.zip'),
    referer='https://smpl.is.tue.mpg.de/',
    PHPSESSID='26-digits_123456789_123456',
    user_agent='Transmission/2.77',
    **kwargs: Unpack[Kw_itmd_coro]
):
    """
    Args:
        url (str): download file url
        path (str): download file path
        referer (str): prevent error 403
        PHPSESSID (str, optional): not necessary. PHPSESSID retrieved from logged in cookie, **expires after next login**  
                        从已登录的 cookie 中获取的 PHPSESSID，**在下次登录后过期**
        user_agent (str, optional): not necessary. User-Agent to prevent error 403
    """
    cookies_txt = Path(path, 'cookies.txt')
    cookies = [{
        'domain': DIR + referer.split('/')[2],  # MAYBE BUGGY
        'name': 'PHPSESSID',
        'value': PHPSESSID,
    }]
    save_cookies_to_file(cookies, cookies_txt)
    options = {
        'load-cookies': cookies_txt,
        'user-agent': user_agent,
        'referer': referer,
    }
    options = {**options, **kwargs}
    return download(File(url, path=Path(path,)), **options)


async def dl_unzip_ln(
    From='SMPL_python_v.1.1.0/smpl/models/*',
    to='smpl',
    map: Dict[str, str] = {},
    **kwargs: Unpack[Kw_itmd]
):
    """
    1.Download 2.unzip 3.symlink files

    Args:
        url (str): download file url
        path (str): download file path
        referer (str): prevent error 403

        From (str): which files to unzip
        to (str): where to unzip
        map (dict): symlink after unzip  
            eg: {'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'}
    """
    dls = download_tue_mpg(**kwargs)
    if dls is None:
        return
    p = await unzip(dls[0].files[0].path, From=From, to=to, **kwargs)
    for From, to in map.items():
        symlink(From, dst=to)
    return dls


def i_smplx_hugging_face(Dir: str):
    global HUG_SMPLX
    Log.info("📦 Download SMPL/X pretrained models (📝 By downloading, you agree to the SMPL & SMPL-X's corresponding licences)")
    DOMAIN = 'hf-mirror.com' if CONFIG.is_mirror else 'huggingface.co'
    HUG_SMPLX = HUG_SMPLX.format(DOMAIN)
    LFS_SMPL = {
        ('body_models', 'smpl', 'SMPL_NEUTRAL.pkl'): {
            'md5': 'b78276e5938b5e57864b75d6c96233f7'
        },
        ('body_models', 'smplx', 'SMPLX_NEUTRAL.npz'): {
            'md5': '6eed2e6dfee62a3f4fb98dcd41f94e06'
        }
    }
    files: list[File] = []
    for out, dic in LFS_SMPL.items():
        url = HUG_SMPLX + out[-1]
        files.append(File(url, path=Path(Dir, *out), md5=dic['md5']))
    dls = download(*files)
    return dls


async def i_smplx_tue_mde(
    PHPSESSIDs: dict = {'smpl': '', 'smplx': ''},
    **kwargs: Unpack[Kw_i_smpl]
):
    """
    Args:
        PHPSESSIDs (dict): {'smpl': '26-digits_123456789_123456', 'smplx': '26-digits_123456789_123456'}
    """
    Log.info("⬇️ Download SMPL && SMPLX (📝 By downloading, you agree to SMPL/SMPL-X corresponding licences)")

    # for k, v in PHPSESSIDs.items():
    #     if not (v and isinstance(v, str)):
    #         Log.warning(f"🍪 cookies: PHPSESSID for {k}={v} could cause download failure")

    Dir = kwargs.setdefault('Dir', DIR)
    tasks = [
        dl_unzip_ln(
            **kwargs,   # type: ignore
            **dict(
                url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
                path=Path(Dir, 'SMPL_python_v.1.1.0.zip'),
                referer='https://smpl.is.tue.mpg.de/',
                md5='21f382969eed3ee3f597b049f228f84d',
                From='SMPL_python_v.1.1.0/smpl/models/*',
                to='smpl',
                map={'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'},
                PHPSESSID=PHPSESSIDs['smpl']),
        ),
        dl_unzip_ln(
            **kwargs,   # type: ignore
            **dict(
                url='https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip',
                path=Path(Dir, 'models_smplx_v1_1.zip'),
                referer='https://smpl-x.is.tue.mpg.de/',
                md5='763a8d2d6525263ed09aeeac3e67b134',
                From='models/smplx/*',
                to='smplx',
                PHPSESSID=PHPSESSIDs['smplx'],)
        ),
    ]
    # TODO: download 1by1 when in same domain
    dls = await asyncio.gather(*tasks)
    dls = [dl[0] for dl in dls if dl is not None]

    if not is_complete(dls):
        Log.error("Please check your cookies:PHPSESSID if it's expired, or change your IP address by VPN")
    return dls


async def i_smplx(Dir: str, **kwargs) -> list['aria2p.Download']:
    dls = i_smplx_hugging_face(Dir, **kwargs)
    await wait_slowest(*dls)
    if not is_complete(dls):
        dls = await i_smplx_tue_mde(Dir=str(Path(Dir, 'body_models')), **kwargs)
    if not is_complete(dls):
        Log.error(f"Please download SMPLX models at {HUG_SMPLX} or https://smpl.is.tue.mpg.de/")
    else:
        Log.info("✔ Download SMPLX models")
    return dls


async def i_smplx_blender():
    Log.info("⬇️ Download Blender SMPL-X Plugin")
    url = "https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=smplx_blender_addon_lh_20241129.zip"
    # TODO: check md5
    ...

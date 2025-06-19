from mocap_wrapper.lib import *
from typing import Dict, TypedDict


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


def tue_mpg_download(
    Dir=DIR,
    url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
    referer='https://smpl.is.tue.mpg.de/',
    PHPSESSID='26-digits_123456789_123456',
    user_agent='Transmission/2.77',
    **kwargs: Unpack[Kw_itmd_coro]
):
    """
    Returns:
        Coroutine: async download()

    Args:
        Dir (str): downlaod directory
        url (str): download file url
        referer (str): prevent error 403
        PHPSESSID (str, optional): not necessary. PHPSESSID retrieved from logged in cookie, **expires after next login**  
                        从已登录的 cookie 中获取的 PHPSESSID，**在下次登录后过期**
        user_agent (str, optional): not necessary. User-Agent to prevent error 403
    """
    path = os.path.join(Dir, 'cookies.txt')
    cookies = [{
        'domain': DIR + referer.split('/')[2],  # MAYBE BUGGY
        'name': 'PHPSESSID',
        'value': PHPSESSID,
    }]
    save_cookies_to_file(cookies, path)
    options = {
        'load-cookies': path,
        'user-agent': user_agent,
        'referer': referer,
    }
    options = {**options, **kwargs}
    return download(url, dir=Dir, **options)


async def tue_mpg(
    From='SMPL_python_v.1.1.0/smpl/models/*',
    to='smpl',
    map: Dict[str, str] = {},
    **kwargs: Unpack[Kw_itmd]
):
    """
    1.Download 2.unzip 3.synlink files

    Args:
        Dir (str): work directory
        url (str): download file url
        referer (str): prevent error 403

        From (str): which files to unzip
        to (str): where to unzip
        map (dict): symlink after unzip  
            eg: {'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'}
    """
    f = await tue_mpg_download(**kwargs)
    p = unzip(f.path, From=From, to=to, **kwargs)
    for From, to in map.items():
        os.symlink(From, to)
    return f


async def i_smpl(
    PHPSESSIDs: dict = {'smpl': '', 'smplx': ''},
    **kwargs: Unpack[Kw_i_smpl]
) -> List['aria2p.Download']:
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
        tue_mpg(
            **kwargs,   # type: ignore
            **dict(
                url='https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip',
                referer='https://smpl.is.tue.mpg.de/',
                md5='21f382969eed3ee3f597b049f228f84d',
                From='SMPL_python_v.1.1.0/smpl/models/*',
                to='smpl',
                map={'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl': 'SMPL_NEUTRAL.pkl'},
                Dir=Dir,
                PHPSESSID=PHPSESSIDs['smpl']),
        ),
        tue_mpg(
            **kwargs,   # type: ignore
            **dict(
                url='https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=models_smplx_v1_1.zip',
                referer='https://smpl-x.is.tue.mpg.de/',
                md5='763a8d2d6525263ed09aeeac3e67b134',
                From='models/smplx/*',
                to='smplx',
                Dir=Dir,
                PHPSESSID=PHPSESSIDs['smplx'],)
        ),
    ]
    dls = await aio.gather(*await run_1by1(tasks))  # TODO: download 1by1 when in same domain!!!

    if any([not dl.is_complete for dl in dls]):
        Log.error("❌ please check your cookies:PHPSESSID if it's expired, or change your IP address by VPN")
    else:
        Log.info("✔ Installed SMPL && SMPLX as pickle")
    return dls


async def i_smpl_blender():
    Log.info("⬇️ Download Blender SMPL-X Plugin")
    url = "https://download.is.tue.mpg.de/download.php?domain=smplx&sfile=smplx_blender_addon_lh_20241129.zip"
    # TODO: check md5
    ...

try:
    from netscape_cookies import save_cookies_to_file   # type: ignore
except ImportError:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment.")
    raise

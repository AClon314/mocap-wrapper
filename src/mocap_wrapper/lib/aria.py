#!/bin/env python
import os
import asyncio
import hashlib
from typing import TypedDict, Unpack
from worker import worker    # type: ignore
from .logger import getLogger
from . import TIMEOUT_MINUTE
Log = getLogger(__name__)
_ARIA_PORTS = [6800, 16800]
_TIMEOUT_SEC = 15      # seconds for next http request, to prevent being 403 blocked
_OPT = {
    'dir': '',  # you can edit dir here
    # 'out': 'filename',
    'continue': 'true',
    'split': 5,
    'max-connection-per-server': 5,
    'max-concurrent-downloads': 2,
    'min-split-size': '20M',  # don't split if file size < 40M
    'retry-wait': _TIMEOUT_SEC,
    'max-tries': 3,
}
_OPT = {k: str(v) for k, v in _OPT.items()}


async def worker_ret(worker, check_interval=0.01):
    """
    Wait the worker to finish, and return the result
    """
    if worker.is_alive:
        while not worker.finished:
            await asyncio.sleep(check_interval)
        return worker.ret
    else:
        raise Exception(f"Worker not started")


async def calc_md5(file_path):
    @worker  # type: ignore
    def wrap():
        with open(file_path, 'rb') as f:
            Log.info(f"🖩 Calc MD5 for {file_path}")
            return hashlib.md5(f.read()).hexdigest()
    task = wrap()
    return await worker_ret(task)


def try_aria_port() -> 'aria2p.API':
    for port in _ARIA_PORTS:
        try:
            aria2 = aria2p.API(
                aria2p.Client(
                    host="http://localhost",
                    port=port,
                    secret=""
                )
            )
            aria2.get_stats()
            return aria2
        except Exception as e:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
    raise ConnectionError(f"Failed to connect to aria2 on ports {_ARIA_PORTS}")


async def aria(
    url: str,
    duration=0.5,
    resumable=False,
    options: dict = {**_OPT},  # type: ignore
):
    """
    used to be wrapped in `download`, this is without retry logic

    Args:
        url (str): download url
        duration (float): check if download is complete every `duration` seconds
        resumable (bool): if the file is resumable
        dry_run (bool): if True, only download 5MB
        options (dict): aria2p.Options
    """
    P = PROGRESS_DL
    url = url() if callable(url) else url
    dl = Aria.add_uris([url], options=options)  # type: ignore
    task = P.add_task(f"⬇️ {url}", start=False)
    # def Url(): return dl.files[0].uris[0]['uri']     # get redirected url
    def Filename(): return os.path.basename(dl.path)
    Log.debug(f"options after: {dl.options.get_struct()}")
    max_speed = 10
    count = 0   # to calc time lapse

    def keep_loop():
        """priority:
        1. status=done→False
        1. dry_run→False
        1. not resumable→True
        1. speed too slow→False"""
        if dl.is_complete or dl.status == 'error':
            return False
        completed = dl.completed_length
        if dry_run and completed > 1024 ** 2 * 5:  # 5MB
            return False
        if not resumable:
            return True

        # if now_speed is lower than 1/4 of max, and last to long, cancel
        debt = completed - (max_speed // 4) * count * duration
        Log.debug(f'debt={debt}\t{completed} max={max_speed} {count}x{duration}\t{dl.url}')
        debt = debt < -int(options.get('retry-wait', _TIMEOUT_SEC))
        if debt:
            return False

        return True

    while keep_loop():
        await asyncio.sleep(duration)
        dl: Download_patch = Aria.get_download(dl.gid)  # type: ignore
        count += 1
        # Log.debug(f"current: {dl.__dict__}")
        # Log.debug(f"♻️ is_loop: {keep_loop()}\t{Url()}")

        now_speed = dl.download_speed
        if now_speed > max_speed:
            max_speed = now_speed

        status = f'{dl.completed_length_string() if dl.completed_length else ""}/{dl.total_length_string() if dl.total_length else ""} @ {dl.download_speed_string() if dl.download_speed else ""}'
        if P:
            if dl.total_length > 0:
                P.start_task(task)
            P.update(task, description=f"⬇️ {Filename()}",
                     total=dl.total_length,
                     completed=dl.completed_length,
                     status=status)
        else:
            Log.info(status)

    dl.path = dl.files[0].path
    # dl.url = Url()
    if dl.is_complete:
        Log.info(f"✅ {dl.path} from '{dl.url}'")
    elif Aria:
        Aria.remove([dl])   # warning: can't get_download(dl.gid) after dl.gid removed
    P.remove_task(task)
    return dl


class Kw_download(TypedDict, total=False):
    dir: str
    out: str
    max_connection_per_server: str
    split: str
    user_agent: str
    referer: str
    max_tries: str
    header: str


async def download(
    url: str,
    md5: str = '',
    duration=0.5,
    **kwargs: Unpack[Kw_download]
):
    """check if download is complete every `duration` seconds

    `**kwargs` for `aria2p.API.add_uris(...)`, key/value **use str, not int**:
    - `dir`: download directory
    - `out`: output filename
    - `max-connection-per-server`: `-x`
    - `split`: `-s`  
    - `user-agent`: mozilla/5.0
    - `referer`: domain url
    - `max-tries`: default `-m 5`
    - ~~`header`~~: not implemented due to aria2p only accept `str` for 1 header

    [⚙️for more options](https://aria2.github.io/manual/en/html/aria2c.html#input-file)
    """
    # TODO: 重构！ queue design for run_1by1, 同域名的下载，等待上一个下载完成后再开始下一个
    options = {**_OPT, **kwargs}
    Log.debug(f"options before: {options}")

    resumable, filename = await is_resumable_file(url)
    Path = os.path.join(str(options['dir']), filename)   # if out is just filenmae
    out = str(options.get('out'))
    if out:
        if os.path.exists(out):  # if out is path/filename
            Path = out

    if md5 and os.path.exists(Path):
        _md5 = await calc_md5(Path)
        if _md5 == md5:
            Log.info(f"✅ {filename} already exists (MD5={md5})")
            dl = SimpleNamespace(path=Path, url=url, is_complete=True)
            return dl

    Try = Try_init = int(options.get('max-tries', 5))  # type: ignore
    Wait = int(options.get('retry-wait', _TIMEOUT_SEC))    # type: ignore
    def Task(): return aria(url, duration, resumable, options)

    # TODO 重试人为移除造成的异常 aria2p.client.ClientException: GID a000f9abff9597e7 is not found
    dl = await Task()
    Complted = dl.completed_length
    Log.debug(f'resume={resumable}\twait={Wait} from {url}')
    while not dl.is_complete and Try > 0:
        # if succeeded in downloading 1KB, reset Try
        if dl.completed_length - Complted > 1024:
            Complted = dl.completed_length
            Try = Try_init

        task = PROGRESS_DL.add_task(f"🕒 {os.path.basename(dl.path)}", total=Wait, completed=Wait)
        Log.error(f"{Try} retry left after {options.get('retry-wait')} sec for {dl.path}:💬 '{dl.error_message}' from '{dl.url}'")
        Try -= 1

        for i in range(int(Wait // duration)):
            await asyncio.sleep(duration)
            PROGRESS_DL.advance(task, -duration)
        PROGRESS_DL.remove_task(task)
        dl = await Task()

    if not dl.is_complete:
        Log.error(f"😭 Download failed: {url}")
    elif md5:
        _md5 = await calc_md5(dl.path)
        if _md5 != md5:
            Log.warning(f"MD5 checksum: yours {_md5} != {md5} expected")

    return dl


Aria = None
import aria2p
import aiohttp
Aria = try_aria_port()


async def is_resumable_file(url: str, timeout=TIMEOUT_MINUTE):
    """```python
    return resumable(True/False), filename(str/None)
    ```"""
    filename = os.path.basename(url)
    Timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=Timeout) as session:
        try:
            # async with session.head(url, headers={'Range': 'bytes=0-0'}) as resp:
            #     status = resp.status == 206
            async with session.head(url) as resp:
                header = resp.headers.get('Accept-Ranges') == 'bytes'
                content_disposition = resp.headers.get('Content-Disposition')
                if content_disposition:
                    filename = content_disposition.split('filename=')[-1].strip('"')
                Log.debug(f"Resumable: {filename} {header}:\t{url}\t{resp.status}\t{resp.headers}")
                return header, filename
        except Exception as e:
            Log.error(f"{url}: {e}")
            return False, filename

if __name__ == '__main__':
    ...
    # run_tail('python -c "from tqdm import tqdm; import time; import sys; [time.sleep(0.02) for _ in tqdm(range(100),file=sys.stdout)]"')

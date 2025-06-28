#!/bin/env python
'''
download files with aria2p, a python wrapper for aria2
'''
import aria2p
import asyncio
import hashlib
from pathlib import Path
from datetime import timedelta
from typing import Callable, Literal, TypedDict, get_args
from .logger import getLogger
Log = getLogger(__name__)
_ARIA_PORTS = [6800, 16800]
_INTERVAL = 0.5
TIMEOUT_SECONDS = 15      # seconds for next http request, to prevent being 403 blocked
TYPE_HASH = Literal['md5', 'sha1', 'sha256', 'sha512', 'shake_128', 'shake_256']
HASH = get_args(TYPE_HASH)
_OPT = {
    # 'dir': '',  # you can edit dir here
    # 'out': 'filename',
    'continue': 'true',
    'split': 5,
    'max-connection-per-server': 5,
    'max-concurrent-downloads': 2,
    'min-split-size': '20M',  # don't split if file size < 40M
    'retry-wait': TIMEOUT_SECONDS,
    'max-tries': 3,
}
_OPT = {k: str(v) for k, v in _OPT.items()}
DOWNLOADS = []


class Kw_download(TypedDict, total=False):
    dir: str
    out: str | Callable[..., str]
    max_connection_per_server: str
    split: str
    user_agent: str
    referer: str
    max_tries: str
    header: str


def calc_hash(file_path: str | Path, algorithm: TYPE_HASH | str = 'md5'):
    # TODO: multi process/thread
    Log.info(f"🖩 Calc {algorithm}: {file_path}")
    with open(file_path, 'rb') as f:
        return getattr(hashlib, algorithm)(f.read()).hexdigest()


class File(Path):
    def __init__(
            self, *args, url: str,
            md5: str | None = None, sha256: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.expect_md5 = md5
        self.expect_sha256 = sha256

    @property
    def md5(self) -> str:
        return calc_hash(self, 'md5')

    @md5.setter
    def md5(self, value: str):
        self.expect_md5 = value

    def exists(self, *, check_hash=False, follow_symlinks: bool = True) -> bool:
        is_exist = super().exists(follow_symlinks=follow_symlinks)
        is_hash = self.checksum()
        if check_hash:
            if is_hash is None:
                raise ValueError(f"Checksum not provided for {self}")
            return is_exist and is_hash
        else:
            return is_exist

    def checksum(self, hash: str | None = None, algorithm: TYPE_HASH = 'md5') -> bool | None:
        _hash = calc_hash(self, algorithm)
        if not hash:
            hash = next((h for h in (self.expect_md5, self.expect_sha256) if h), None)
        is_hash = (_hash == hash) if hash else None
        Log.warning(f"{self}: {hash}(expected) ≠ {_hash}(current)") if is_hash == False else None
        Log.debug(f"{self}: {hash}(expected)") if is_hash == True else None
        return is_hash


def try_aria_port() -> 'aria2p.API':
    for port in _ARIA_PORTS:
        try:
            aria2 = aria2p.API(aria2p.Client(
                host="http://localhost",
                port=port,
                secret=""
            ))
            aria2.get_stats()
            return aria2
        except Exception as e:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
    raise ConnectionError(f"Failed to connect to aria2 on ports {_ARIA_PORTS}")


def download(
    files: list[File],
    options: dict | Kw_download = {**_OPT}  # type: ignore
):
    """download files with aria2p

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
    # TODO: support metalink .meta4
    files = [d for d in files if not d.exists()]
    urls = [f.url for f in files]
    Log.info(f'⬇ {files=}')
    options = {**_OPT, **options}
    if not urls:
        return
    dls = Aria.add_uris(urls, options=options)
    DOWNLOADS.append(dls)
    return dls


def get_slowest(*dl: 'aria2p.Download') -> 'aria2p.Download | None':
    """return the slowest download"""
    dls = dl if dl else DOWNLOADS
    longest_eta = timedelta()
    _slowest = None
    for _dl in dls:
        if longest_eta < _dl.eta:
            longest_eta = _dl.eta
            _slowest = _dl
    return _slowest


async def wait_slowest(*dl: 'aria2p.Download'):
    dls = dl if dl else DOWNLOADS
    while (slowest := get_slowest(*dls)):
        Log.info(f"⏳ Waiting for {slowest.name} to complete, ETA: {slowest.eta}") if not dl else None
        await asyncio.sleep(_INTERVAL)


Aria = try_aria_port()


if __name__ == '__main__':
    ...
    # run_tail('python -c "from tqdm import tqdm; import time; import sys; [time.sleep(0.02) for _ in tqdm(range(100),file=sys.stdout)]"')

#!/bin/env python
'''
download files with aria2p, a python wrapper for aria2
'''
import aria2p
import asyncio
import hashlib
from pathlib import Path
from datetime import timedelta
from typing import Callable, Literal, Sequence, TypedDict, Unpack, get_args
from .logger import getLogger
Log = getLogger(__name__)
_ARIA_PORTS = [6800, 16800]
_INTERVAL = 0.5
TIMEOUT_SECONDS = 15      # seconds for next http request, to prevent being 403 blocked
TYPE_HASH = Literal['md5', 'sha1', 'sha256', 'sha512', 'shake_128', 'shake_256']
HASH = get_args(TYPE_HASH)
_OPT = {
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


def calc_hash(file_path: str | Path, algorithm: TYPE_HASH | str = 'md5') -> str:
    # TODO: multi process/thread
    Log.info(f"🖩 Calc {algorithm}: {file_path}")
    with open(file_path, 'rb') as f:
        return getattr(hashlib, algorithm)(f.read()).hexdigest()


class File(Path):
    '''use with `download()`

    Args:
        options: for `aria2p.API.add_uris(...)`, key/value **use str, not int**

    `max-connection-per-server`: `-x`  
    `split`: `-s`  
    `user-agent`: mozilla/5.0  
    `referer`: domain url  
    `max-tries`: default `-m 3`, see `_OPT`  
    ~~`header`~~: not implemented due to aria2p only accept `str` for 1 header
    '''

    def __init__(
            self, *urls: str, path: Sequence[str] | str | Path | None = None,
            md5: str | None = None, sha256: str | None = None, **options):
        if path is None:
            path = urls[0].split('/')[-1]
        super().__init__(path) if isinstance(path, (str, Path)) else super().__init__(*path)
        self = self.resolve().absolute()
        self.urls = list(urls)
        self.expect_md5 = md5
        self.expect_sha256 = sha256
        for k, v in options.items():
            setattr(self, k, v)

    @property
    def md5(self): return calc_hash(self, 'md5')
    @md5.setter
    def md5(self, value: str): self.expect_md5 = value

    def exists(self, *, check_hash=True, follow_symlinks: bool = True):
        '''return is_exist and checksum'''
        is_exist = super().exists(follow_symlinks=follow_symlinks)
        is_hash = self.checksum()
        return (is_exist and is_hash) if check_hash else is_exist

    def checksum(self, hash: str | None = None, algorithm: TYPE_HASH = 'md5') -> bool:
        '''raise ValueError if no hash is set, return True if hash matches'''
        _hash = calc_hash(self, algorithm)
        if not hash:
            hash = next((h for h in (self.expect_md5, self.expect_sha256) if h), None)
        if not hash:
            raise ValueError(f"unset `md5` or `sha256`: {self}")
        is_hash = _hash == hash
        Log.warning(f"{self}: {hash}(expected) ≠ {_hash}(current)") if is_hash == False else None
        Log.debug(f"{self}: {hash}(expected)") if is_hash == True else None
        return is_hash


def download(
    *file: File,
    **options: Unpack[Kw_download]
) -> list['aria2p.Download']:
    """check exists and checksum, or download files with aria2p

    Args:
        options: default `_OPT`, for `aria2p.API.add_uris(...)`, key/value **use str, not int**

    `max-connection-per-server`: `-x`  
    `split`: `-s`  
    `user-agent`: mozilla/5.0  
    `referer`: domain url  
    `max-tries`: default `-m 3`, see `_OPT`  
    ~~`header`~~: not implemented due to aria2p only accept `str` for 1 header  
    ~~`out`: output filename~~, has set in `file`  
    ~~`dir`: download directory~~, has set in `file`  

    [⚙️for more options](https://aria2.github.io/manual/en/html/aria2c.html#input-file)
    """
    files = [d for d in file if not d.exists()]
    Log.info(f'⬇ {files=}')
    if not files:
        return []
    dls = []
    for f in files:
        _options = {**_OPT, **options, 'dir': f.parent, 'out': f.name}
        dls.append(Aria.add_uris(f.urls, options=_options))  # type: ignore
    DOWNLOADS.extend(dls)
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


def is_complete(dls: Sequence['aria2p.Download|None']): return not dls or all([dl.is_complete for dl in dls if dl])


def try_aria_port() -> aria2p.API:
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
            Log.debug(f"Failed to connect to aria2 on port {port}: {e}")
    raise ConnectionError(f"Failed to connect to aria2 on ports {_ARIA_PORTS}")


try:
    Aria = try_aria_port()
except Exception:
    Aria = None


if __name__ == '__main__':
    ...
    # run_tail('python -c "from tqdm import tqdm; import time; import sys; [time.sleep(0.02) for _ in tqdm(range(100),file=sys.stdout)]"')

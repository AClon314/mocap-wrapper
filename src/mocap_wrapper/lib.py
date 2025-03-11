"""shared functions here"""
import os
import sys
import hashlib
from pathlib import Path
import subprocess as sp
import asyncio as aio
from sys import platform
from datetime import timedelta
from types import SimpleNamespace

from worker import worker    # type: ignore
from mocap_wrapper.logger import getLogger, PROGRESS_DL
from typing import Any, Callable, Coroutine, List, Literal, ParamSpec, Sequence, Tuple, TypeVar, TypedDict, Union, Unpack, cast, overload
from typing_extensions import deprecated
Log = getLogger(__name__)
MODS = ['wilor', 'gvhmr']
TIME_OUT = timedelta(minutes=10).seconds
RELAX = 15      # seconds for next http request, to prevent being 403 blocked
DIR = '.'       # fallback directory, don't edit
CHECK_KWARGS = True
ARIA_PORTS = [6800, 16800]
OPT = {
    'dir': '.',  # you can edit dir here
    # 'out': 'filename',
    'continue': 'true',
    'split': 5,
    'max-connection-per-server': 5,
    'max-concurrent-downloads': 2,
    'min-split-size': '20M',  # don't split if file size < 40M
    'retry-wait': RELAX,
    'max-tries': 3,
}
OPT = {k: str(v) for k, v in OPT.items()}
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'


def path_expand(path: Union[str, Path], absolute=True):
    path = os.path.expandvars(os.path.expanduser(path))
    if absolute:
        path = os.path.abspath(path)
    return path


def run_async(func: Coroutine, timeout=TIME_OUT, loop=aio.get_event_loop()):
    return aio.run_coroutine_threadsafe(func, loop).result(timeout)


def is_main_thread():
    import threading
    return threading.current_thread() == threading.main_thread()


def get_coro_sig(coro) -> tuple[str, dict]:
    func_name = coro.__qualname__
    args = coro.cr_frame.f_locals
    return func_name, args


async def async_queue(duration=0.02):
    _len = 9
    states = {
        'PENDING': '🕒',
        'RUNNING': '🏃',
    }
    q_last = ''
    while _len > 2:
        tasks = aio.all_tasks()
        _len = len(tasks)
        tasks = [
            f'{states.get(t._state, t._state)}{t.get_name()}' for t in tasks if 'async_queue' not in t.get_name()
        ]
        q_now = '\n'.join(tasks)
        if q_now != q_last:
            q_last = q_now
            Log.info(f'{_len} in async queue: {q_now}')
        await aio.sleep(duration)

# def rich_finish(task: 'rich.progress.TaskID'):
#     P = PG_DL
#     P.update(task, completed=100)
#     P.start_task(task)


def then(coro: Coroutine, *serials_1by1: Tuple[Callable], parallel_1toN: List[Callable] = []):
    """run callbacks after coro"""
    async def _then():
        result = await coro
        for func in parallel_1toN:
            func(result)
        return result
    return _then()


async def run_1by1(
    coros: Sequence[Union[Coroutine, aio.Task]],
    callback: Union[Callable, aio.Task, None] = None,
    duration=RELAX
):
    """
    Run tasks one by one with a duration of `duration` seconds

    ```python
    # urgent way
    for result in aio.as_completed(await run_1by1([coro1, coro2], callback)):
        print(result)

    # wait until all complted
    results = await aio.gather(*await run_1by1([coro1, coro2], callback))
    ```

    - callback: accept `Task` object as argument only
    ```python
    def callback(task: asyncio.Task[TYPE_OF_RETURN]):
        if task.cancelled():
            msg = "Download cancelled"
            raise Exception(msg)
        t = task.result()
        return t
    ```
    """
    tasks: List[aio.Task] = []
    for i in range(len(coros)):
        c = coros[i]
        if isinstance(c, Coroutine):
            t = aio.create_task(c)
            if callback and callable(callback):
                t.add_done_callback(callback)
            tasks.append(t)
        elif isinstance(c, aio.Task):
            tasks.append(c)
        else:
            raise TypeError(f"Invalid type: {type(c)}")
        if i < len(coros) - 1:
            await aio.sleep(duration)
    return tasks

PS = ParamSpec("PS")
TV = TypeVar("TV")


def copy_kwargs(
    kwargs_call: Callable[PS, Any]
) -> Callable[[Callable[..., TV]], Callable[PS, TV]]:
    """Decorator does nothing but returning the casted original function"""
    def return_func(func: Callable[..., TV]) -> Callable[PS, TV]:
        return cast(Callable[PS, TV], func)
    return return_func


def filter_kwargs(funcs: List[Union[Callable, object]], kwargs, check=CHECK_KWARGS):
    """Filter out invalid kwargs to prevent Exception

    Don't use this if the funcs 
    actually parse args by `**kwargs` 
    while using `.pyi` to hint args,
    which will filter out your needed kwargs.

    ```python
    def Popen(cmd, Raise, **kwargs):
        kwargs = Kwargs([sp.Popen, Popen], kwargs)
        p = sp.Popen(cmd, **kwargs)
        return p
    ```
    """
    if not check:
        return kwargs
    from inspect import signature, isclass
    d = {}
    for f in funcs:
        if isclass(f):
            params = signature(f.__init__).parameters
        elif callable(f):
            params = signature(f).parameters
        else:
            raise TypeError(f"Invalid type: {type(f)}")
        # Log.debug(f"{funcs[0]} {params}")
        for k, v in kwargs.items():
            if k in params:
                d[k] = v
            else:
                Log.warning(f"Invalid kwarg: {k}={v}, please report to developer")
    return d


async def unzip(
    zip_path: Union[str, Path], From='', to=DIR, pwd='',
    overwrite_rule: Literal['always', 'skip', 'rename_new', 'rename_old'] = 'skip',
    **kwargs
):
    """
    use 7z to unzip files

    Args:
        From (str): eg: `subdir/*`
        pwd (str): password
    """
    mode = 'x'
    if From:
        mode = 'e'
    if to:
        to = '-o' + to
    if pwd:
        pwd = f'-p{pwd}'

    conflict = ''
    if overwrite_rule == 'skip':
        conflict = '-aos'
    elif overwrite_rule == 'always':
        conflict = '-aoa'
    elif overwrite_rule == 'rename_new':
        conflict = '-aou'
    elif overwrite_rule == 'rename_old':
        conflict = '-aot'
    else:
        Log.warning(f"Unknown replace_if_existing: {overwrite_rule}")
    cmd = ' '.join(filter(None, ('7z', mode, conflict, pwd, f'"{zip_path}"', From, to)))
    p = await popen(cmd, **kwargs)
    return p


async def popen(
    cmd: str,
    mode: Literal['realtime', 'wait', 'no-wait'] = 'realtime',
    Raise=True,
    timeout=TIME_OUT,
    **kwargs
):
    """Used on long running commands

    Args:
        mode (str):
            - realtime: **foreground**, print in real-time
            - wait: await until finished
            - no-wait: **background**, immediately return, suitable for **forever-looping**, use:
            p = await popen('cmd', mode='bg')
            await p.expect(pexpect.EOF, async_=True)
            print(p.before.decode())
        kwargs: `pexpect.spawn()` args

    Returns:
        process (pexpect.spawn): 
    """
    Log.info(f'start {cmd}')
    p = pexpect.spawn(cmd, timeout=timeout, **kwargs)
    if mode == 'realtime':
        while True:
            try:
                await p.expect(['\r\n', '\r', '\n'], async_=True)
                if p.before and p.after and isinstance(p.before, bytes) and isinstance(p.after, bytes):
                    sys.stdout.buffer.write(p.before + p.after)
                    # sys.stdout.flush()
            except pexpect.EOF:
                break
            except pexpect.TIMEOUT:
                Log.warning(f"Timeout: {cmd}")
            except Exception:
                if Raise:
                    raise
                else:
                    Log.warning(f"{cmd} → {p.before}")
    elif mode == 'wait':
        try:
            await p.expect(pexpect.EOF, async_=True)
        except pexpect.TIMEOUT:
            Log.warning(f"Timeout: {cmd}")
        except Exception:
            if Raise:
                Log.error(f'{cmd} → {p.before}')
                raise
            else:
                Log.warning(f"{cmd} → {p.before}")
    elif mode == 'no-wait':
        ...
    else:
        raise ValueError(f"Invalid mode: {mode}")
    return p


@copy_kwargs(popen)
async def echo(*args, **kwargs):
    p = await popen(*args, mode='wait', **kwargs)
    text = ''
    if p.before and isinstance(p.before, bytes):
        text = p.before.decode()
    else:
        raise Exception(f"{args}, {kwargs}")
    return p, text


@deprecated('Use `popen` instead, this sync would block the main thread')
def Popen_(
    cmd: str,
    timeout=TIME_OUT, Raise=True, dry_run=False, **kwargs
):
    """Used on long running commands  
    set `timeout` to -1 to run in background (non-blocking)

    - Raise: if False, log warning instead of raising Exception
    - dry_run: if True, only print the command without executing
    """
    Log.info(cmd)
    if dry_run:
        return
    p = sp.Popen(
        cmd,
        shell=True, env=os.environ, encoding='utf-8',
        **filter_kwargs([sp.Popen], kwargs)
    )
    if timeout is None or timeout >= 0:
        p.wait(timeout=timeout)
        if p.returncode != 0:
            if Raise:
                raise ChildProcessError(f"{cmd}")
            else:
                Log.warning(f"{cmd}")
    return p


@copy_kwargs(sp.check_output)
@deprecated('Use `popen` instead, this sync would block the main thread')
def Exec_(args, Print=True, **kwargs) -> str:
    """Only used on instantly returning commands

    - Print: print the output
    - kwargs: default `shell=True`, `timeout=TIMEOUT`
    """
    Log.info(args)
    kwargs.setdefault('shell', True)
    kwargs.setdefault('timeout', TIME_OUT)
    s: str = sp.check_output(args, **kwargs).decode().strip()
    if Print:
        print(s)
    return s


async def version(cmd: str):
    """
    use `cmd --version` to check if a program is installed

    if not found,  
    raise `pexpect.exceptions.ExceptionPexpect: The command was not found or was not executable`
    """
    cmd += ' --version'
    p, out = await echo(cmd)
    Log.info(f"{cmd} → {out}")
    return True


async def worker_ret(worker, check_interval=0.01):
    """
    Wait the worker to finish, and return the result
    """
    if worker.is_alive:
        while not worker.finished:
            await aio.sleep(check_interval)
        return worker.ret
    else:
        raise Exception(f"Worker not started")


async def calc_md5(file_path):
    @worker  # type: ignore
    def wrap():
        with open(file_path, 'rb') as f:
            Log.info(f"Calculating MD5 for {file_path}")
            return hashlib.md5(f.read()).hexdigest()
    task = wrap()
    return await worker_ret(task)


def try_aria_port() -> 'aria2p.API':
    for port in ARIA_PORTS:
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
        except Exception:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
    raise ConnectionError(f"Failed to connect to aria2 on ports {ARIA_PORTS}")


async def aria(
    url: str,
    duration=0.5,
    resumable=False,
    dry_run=False,
    options: dict = {**OPT},  # type: ignore
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
        debt = debt < -int(options.get('retry-wait', RELAX))
        if debt:
            return False

        return True

    while keep_loop():
        await aio.sleep(duration)
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

    dl.path = path_expand(dl.files[0].path)
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
    dry_run=False,
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
    # TODO: queue design for run_1by1
    options = {**OPT, **kwargs}
    Log.debug(f"options before: {options}")

    resumable, filename = await is_resumable_file(url)
    Path = os.path.join(str(options['dir']), filename)   # if out is just filenmae
    out = str(options.get('out'))
    if out:
        out = path_expand(out)
        if os.path.exists(out):  # if out is path/filename
            Path = out
    Path = path_expand(Path)

    if md5 and os.path.exists(Path):
        _md5 = await calc_md5(Path)
        if _md5 == md5:
            Log.info(f"✅ {filename} already exists (MD5={md5})")
            dl = SimpleNamespace(path=Path, url=url, is_complete=True)
            return dl

    Try = Try_init = int(options.get('max-tries', 5))  # type: ignore
    Wait = int(options.get('retry-wait', RELAX))    # type: ignore
    def Task(): return aria(url, duration, resumable, dry_run, options)

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
            await aio.sleep(duration)
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


class ExistsPathList(list):
    def __init__(self, chdir: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append(os.getcwd())
        if chdir:
            self.chdir(chdir)

    def append(self, object):
        if os.path.exists(object):
            super().append(object)
        else:
            Log.warning(f"{object} not exists")

    @overload
    def chdir(self, path: str) -> None: ...

    @overload
    def chdir(self, index: int) -> None: ...

    def chdir(self, path):  # type: ignore
        if isinstance(path, int):
            os.chdir(self[path])
        else:
            self.append(path)
            os.chdir(path)

    def pushd(self, path: str):
        self.chdir(path)

    def popd(self) -> str:
        p = self.pop()
        os.chdir(p)
        return p


class Single():
    """
    ```python
    class PROGRESS(Single):
        @classmethod
        def get(cls, value=rich_init) -> Progress:
            return super().get(value)
    ```
    """
    instance = None

    @classmethod
    def get(cls, value: Union[Callable, Any] = None):
        if Single.instance is None:
            if callable(value):
                Single.instance = value()
            else:
                Single.instance = value
        return Single.instance


Aria = None
try:
    import aria2p
    import aiohttp
    import pexpect
    from regex import sub as re_sub, compile as re_compile, MULTILINE

    Aria = try_aria_port()

    async def is_resumable_file(url: str, timeout=TIME_OUT):
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

    class Download_patch(aria2p.Download):
        @property
        def path(self):
            return self.files[0].path

        @path.setter
        def path(self, value):
            self.path = value

        @property
        def url(self):
            return self.files[0].uris[0]['uri']

        @url.setter
        def url(self, value):
            self.url = value

    aria2p.Download = Download_patch

    if __name__ == '__main__':
        Log.debug('⛄')
        # aio.run()

except ImportError as e:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment. {e}")

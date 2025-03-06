"""shared functions here"""
import os
import subprocess as sp
import asyncio as aio
from sys import platform
from datetime import timedelta
from mocap_wrapper.logger import getLogger, PG_DL
from typing import Any, Callable, Coroutine, List, Literal, Union, overload
Log = getLogger(__name__)
TIMEOUT = timedelta(minutes=15).seconds
RELAX = 15    # seconds for next http request, to prevent being 403 blocked
CHECK_KWARGS = True
ARIA_PORTS = [6800, 16800]
OPT = {
    'dir': '.',
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


def path_expand(path: str):
    return os.path.expandvars(os.path.expanduser(path))


def run_async(func: Coroutine, timeout=TIMEOUT, loop=aio.get_event_loop()):
    return aio.run_coroutine_threadsafe(func, loop).result(timeout)


def rich_finish(task: int):
    P = PG_DL
    P.update(task, completed=100)
    P.start_task(task)


async def run_1by1(
    coros: List[Coroutine],
    callback: Callable[[aio.Task], object] = None,
    duration=RELAX
):
    """
    Run tasks one by one with a duration of `duration` seconds

    ```python
    # urgent way
    for result in aio.as_completed(run_1by1([coro1, coro2, coro3], callback)):
        print(result)

    # wait until all complted
    results = await aio.gather(run_1by1([coro1, coro2, coro3], callback))
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
        t = aio.create_task(c)
        if callback and callable(callback):
            t.add_done_callback(callback)
        tasks.append(t)
        if i < len(coros) - 1:
            await aio.sleep(duration)
    return tasks
    # result = await t
    # yield result
    # results = await aio.gather(*tasks)
    # return results


def Kwargs(funcs: List[Union[Callable, object]], kwargs, check=CHECK_KWARGS):
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


def unzip(zip_path: str, to: str, pwd='',
          overwrite_policy: Literal['always', 'skip', 'rename_new', 'rename_old'] = 'skip',
          **kwargs):
    """use 7z to unzip files"""
    if pwd:
        pwd = f'-p{pwd}'

    conflict = ''
    if overwrite_policy == 'skip':
        conflict = '-aos'
    elif overwrite_policy == 'always':
        conflict = '-aoa'
    elif overwrite_policy == 'rename_new':
        conflict = '-aou'
    elif overwrite_policy == 'rename_old':
        conflict = '-aot'
    else:
        Log.warning(f"Unknown replace_if_existing: {overwrite_policy}")

    cmd = f'7z x {conflict} {pwd} "{zip_path}" -o"{to}"'    # default: -mmt=on
    p = Popen(cmd, **Kwargs([sp.Popen, Popen], kwargs))
    return p


async def Popen_(cmd='aria2c --enable-rpc --rpc-listen-port=6800',
                 timeout=TIMEOUT, Raise=True, dry_run=False, **kwargs):
    """Used on long running commands
    set `timeout` to -1 to run in background (non-blocking)
    """
    Log.info(cmd)
    if dry_run:
        return
    p = await aio.create_subprocess_shell(
        cmd, **Kwargs([aio.create_subprocess_shell, Popen], kwargs)
    )
    if timeout is None or timeout >= 0:
        await p.wait()
        if p.returncode != 0:
            if Raise:
                raise Exception(f"{cmd}")
            else:
                Log.error(f"{cmd}")
    return p


def Popen(cmd='aria2c --enable-rpc --rpc-listen-port=6800',
          timeout: Union[float, None] = None, Raise=True, dry_run=False, **kwargs):
    """Used on long running commands
    set `timeout` to -1 to run in background (non-blocking)
    """
    Log.info(cmd)
    if dry_run:
        return
    p = sp.Popen(cmd, shell=True, env=os.environ, **Kwargs([sp.Popen], kwargs))
    if timeout is None or timeout >= 0:
        p.wait(timeout=timeout)
        if p.returncode != 0:
            if Raise:
                raise Exception(f"{cmd}")
            else:
                Log.error(f"{cmd}")
    return p


def Exec(cmd, timeout=TIMEOUT, Print=True, **kwargs) -> Union[str, bytes, None]:
    """Only used on instantly returning commands"""
    Log.info(cmd)
    s = sp.check_output(cmd, shell=True, timeout=timeout, **Kwargs([Exec], kwargs)).decode().strip()
    if Print:
        print(s)
    return s


def version(cmd: str):
    """use `cmd --version` to check if a program is installed"""
    cmd += ' --version'
    p = Popen(cmd)
    return p.returncode == 0


def try_aria_port():
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
        except ImportError:
            Log.error(f"Failed to import aria2p")
            return None
        except Exception as e:
            Log.error(f"Failed to connect to aria2 on port {port}: {e}")
            return None


async def aria(url: str, duration=0.5, resumable=False, dry_run=False, options: 'aria2p.Options' = {**OPT}):
    """used to be wrapped in `download`, no retry logic"""
    P = PG_DL
    url = url() if callable(url) else url
    dl = Aria.add_uris([url], options=options)
    task = P.add_task(f"⬇️ Download {url}", start=False) if P else None
    def Url(): return dl.files[0].uris[0]['uri']     # get redirected url
    def Path(): return dl.files[0].path
    def Filename(): return os.path.basename(Path())
    if dl.is_complete:
        Log.info(f"{Path()} already downloaded")
        return dl
    Log.debug(f"options after: {dl.options.get_struct()}")
    max_speed = 2
    count = 0   # to calc time lapse

    def keep_loop():
        """priority:
        1. status=done→False
        1. dry_run→False
        1. not resumable→True
        1. speed too slow→False"""
        if dl.is_complete or dl.status == 'error':
            return False
        complted = dl.completed_length
        if dry_run and complted > 1024 ** 2 * 5:  # 5MB
            return False
        if not resumable:
            return True

        # if now_speed is lower than 1/4 of max, and last to long, cancel
        debt = complted - (max_speed // 4) * count * duration
        Log.debug(f'debt={debt}\t{complted} {max_speed} {count} {duration}\t{Url()}')
        debt = debt < -int(options.get('retry-wait', RELAX))
        if debt:
            return False

        return True

    while keep_loop():
        await aio.sleep(duration)
        dl = Aria.get_download(dl.gid)
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

    dl.path = os.path.abspath(Path())
    dl.url = Url()
    if dl.is_complete:
        Log.info(f"✅ {dl.path} from '{dl.url}'")
    else:
        Aria.remove([dl])   # warning: can't get_download(dl.gid) after dl.gid removed
    P.remove_task(task)
    return dl


async def download(url: Union[str, Callable], duration=0.5, dry_run=False, **kwargs: 'aria2p.Options'):
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
    options = {**OPT, **kwargs}
    Log.debug(f"options before: {options}")
    # if options.get('out'):
    #     options['dir'] = ''

    resumable = await is_resumable(url)
    Try = Try_init = int(options.get('max-tries', 5))  # default 5
    Wait = int(options.get('retry-wait', RELAX))
    def Task(): return aria(url, duration, resumable, dry_run, options)
    dl = await Task()
    Complted = dl.completed_length
    while not dl.is_complete and Try > 0:
        # if succeeded in downloading 1KB, reset Try
        if dl.completed_length - Complted > 1024:
            Complted = dl.completed_length
            Try = Try_init

        task = PG_DL.add_task(f"🕒 {os.path.basename(dl.path)}", total=Wait, completed=Wait)
        Log.error(f"{Try} retry left after {options.get('retry-wait')} sec for {dl.path}:💬 '{dl.error_message}' from '{dl.url}'")
        Try -= 1

        for i in range(int(Wait // duration)):
            await aio.sleep(duration)
            PG_DL.advance(task, -duration)
        PG_DL.remove_task(task)

        dl = await Task()

    if dl.completed_length < 1:
        Log.error(f"Download failed: {url}")

    return dl


class ExistsPathList(list):
    def __init__(self, chdir: str = None, *args, **kwargs):
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

    def chdir(self, arg):
        if isinstance(arg, int):
            os.chdir(self[arg])
        else:
            self.append(arg)
            os.chdir(arg)

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
    from worker import worker, async_worker, ThreadWorkerManager
    Aria: aria2p.API = try_aria_port()

    async def is_resumable(url: str, timeout=TIMEOUT):
        Timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=Timeout) as session:
            try:
                async with session.head(url, headers={'Range': 'bytes=0-0'}) as resp:
                    status = resp.status == 206
                    # header = resp.headers.get('Accept-Ranges') == 'bytes'
                    Log.debug(f"Resumable: {status}:\t{url}\t{resp.status}\t{resp.headers}")
                    return status
            except Exception:
                Log.error(f"Failed to connect to {url}")
                return False

    if __name__ == '__main__':
        Log.debug('⛄')
        # aio.run()

except ImportError as e:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment. {e}")

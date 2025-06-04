"""shared functions:
- download/aria, calc_md5, is_resumable_file, try_aria_port
- popen/echo, unzip/version
- run_1by1, async_queue
- copy_kwargs, filter_kwargs, get_coro_sig, is_main_thread
- path_expand, ExistsPathList, Single
"""
import os
import sys
import json
import toml
import hashlib
import subprocess as sp
import asyncio as aio
from pathlib import Path
from sys import platform
from fractions import Fraction
from datetime import timedelta, datetime
from shutil import get_terminal_size
from platformdirs import user_config_path
from importlib.resources import path as _res_path
from importlib.metadata import version as _version
from worker import worker    # type: ignore
from mocap_wrapper.logger import IS_DEBUG, PROGRESS_DL, Log
from types import SimpleNamespace
from typing import Any, Callable, Coroutine, Dict, List, Literal, Optional, ParamSpec, Sequence, Tuple, TypeVar, TypedDict, Union, Unpack, cast, get_args, overload
from typing_extensions import deprecated
# config
_TIMEOUT = timedelta(minutes=20).seconds
_RELAX = 15      # seconds for next http request, to prevent being 403 blocked
_ARIA_PORTS = [6800, 16800]
_OPT = {
    'dir': '.',  # you can edit dir here
    # 'out': 'filename',
    'continue': 'true',
    'split': 5,
    'max-connection-per-server': 5,
    'max-concurrent-downloads': 2,
    'min-split-size': '20M',  # don't split if file size < 40M
    'retry-wait': _RELAX,
    'max-tries': 3,
}
_OPT = {k: str(v) for k, v in _OPT.items()}
_CHECK_KWARGS = True

# export
DIR = '.'   # fallback to current dir
TYPE_RUNS = Literal['wilor', 'gvhmr']
RUNS = get_args(TYPE_RUNS)
DIR_SELF = os.path.dirname(os.path.abspath(__file__))
PACKAGE = __package__ if __package__ else os.path.basename(DIR_SELF)
__version__ = _version(PACKAGE)
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'
QRCODE = """
█▀▀▀▀▀█  ▀▀█▄ █ ▄ █▀▀▀▀▀█
█ ███ █ ▄▀██▄▄█▄█ █ ███ █
█ ▀▀▀ █ ▀▄█ ▀█▄ █ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄▀▄▀ █▄▀ ▀▀▀▀▀▀▀
▀█ ▄▄▀▀█▄▀█▄▄▀ █   ▄█▀▄
▀█▄██▀▀█▄▀▄ ▀ ▀█▄▄▄▄▄▄ ▀█
▄▀▄█▀▄▀█▄▀██▄ █▄▀ ▀█ ▀ █▀
█ ▀▀ ▀▀▄ ▀ ▄ ▀▀▀█ ▀▀ ▄██▀
▀   ▀ ▀▀█▄▀▄▄▀▄ █▀▀▀██▀▄▀
█▀▀▀▀▀█ █▄ ▀▄  ▄█ ▀ █ ▀ █
█ ███ █  █▀█▄▀ ▀███▀▀█▀█▄
█ ▀▀▀ █ ▄▀▄▄    █  ▀▄█▀ █
▀▀▀▀▀▀▀ ▀ ▀▀  ▀ ▀ ▀▀▀▀  ▀"""[1:]


def path_expand(path: str | Path, absolute=True):
    path = os.path.expandvars(os.path.expanduser(path))
    if absolute:
        path = os.path.abspath(path)
    return path


def res_path(pkg=__package__, module='requirements', file='requirements.txt'):
    if __package__ is None:
        return os.path.join(DIR_SELF, module, file)
    else:
        with _res_path(f'{pkg}.{module}', file) as P:
            return P.absolute()


# I think python type system is not mature enough to handle this
TYPE_KEYS_CONFIG = Union[Literal['search_dir'], str]


class TYPE_CONFIG(TypedDict, total=False):
    search_dir: str
    gvhmr: bool
    wilor: bool


class Config(dict):
    default: TYPE_CONFIG = {
        'search_dir': path_expand(DIR),
        'gvhmr': False,
        'wilor': False,
    }

    def __init__(self, /, *args: TYPE_CONFIG, file: Path | str = "config.toml", **kwargs: Unpack[TYPE_CONFIG]) -> None:
        """

        This will sync to config file:
        ```python
        CONFIG['search_dir'] = '.'
        ```
        """
        self.update(self.default)
        super().__init__(*args, **kwargs)
        self.path = user_config_path(appname=PACKAGE, ensure_exists=True).joinpath(file)
        if os.path.exists(self.path):
            config = toml.load(self.path)
            self.update(config)
            # except toml.TomlDecodeError as e:
            #     # TODO: auto recover from this exception
            #     Log.warning(f"Load failed {self.path}: {e}")
        self.dump()

    def dump(self, file: Path | str = '') -> None:
        """将self dict保存到TOML文件"""
        if not file:
            file = self.path
        with open(file, "w") as f:
            toml.dump(dict(self), f)    # dict() for not recursive

    def __getitem__(self, key: TYPE_KEYS_CONFIG) -> Any:
        return super().__getitem__(key)

    def __setitem__(self, key: TYPE_KEYS_CONFIG, value: Any) -> None:
        super().__setitem__(key, value)
        if key in self.default.keys():
            self.dump()


CONFIG = Config()
DIR = CONFIG['search_dir']


def run_async(func: Coroutine, timeout=_TIMEOUT, loop=aio.get_event_loop()):
    return aio.run_coroutine_threadsafe(func, loop).result(timeout)


def is_main_thread():
    import threading
    return threading.current_thread() == threading.main_thread()


def get_coro_sig(coro) -> tuple[str, dict]:
    func_name = coro.__qualname__
    args = coro.cr_frame.f_locals
    return func_name, args


def mkdir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        Log.info(f'📁 Created: {dir}')


def relink(src, dst, dst_is_dir=False):
    """remove dst link and create a symlink"""
    if os.path.islink(dst):
        os.remove(dst)
    os.symlink(src, dst, target_is_directory=dst_is_dir)
    Log.info(f'🔗 symlink: {dst} → {src}')


async def async_queue(duration=5.0):
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
        q_now = '\t'.join(tasks)
        if q_now != q_last:
            q_last = q_now
            Log.info(f'{_len} in async queue: {q_now}')
        await aio.sleep(duration)

# def rich_finish(task: 'rich.progress.TaskID'):
#     P = PG_DL
#     P.update(task, completed=100)
#     P.start_task(task)


async def run_1by1(
    coros: Sequence[Coroutine | aio.Task],
    callback: Callable | aio.Task | None = None,
    duration=_RELAX
):
    """
    Run tasks one by one with a duration of `duration` seconds

    ```python
    # urgent way
    for result in aio.as_completed(await run_1by1([coro1(), coro2()], sync_func)):
        print(result)

    # wait until all complted
    results = await aio.gather(*await run_1by1([coro1(), coro2()], async_func()))
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


def filter_kwargs(funcs: List[Callable | object], kwargs, check=_CHECK_KWARGS):
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


@copy_kwargs(aio.gather)
async def gather(*args, **kwargs): return await aio.gather(*args, **kwargs)


async def unzip(
    zip_path: str | Path, From='', to=DIR, pwd='',
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
    Raise=False,
    timeout: float | int | None = _TIMEOUT,
    **kwargs
):
    """Used on long running commands

    Args:
        mode (str):
            - realtime: **foreground**, print in real-time
            - wait: await until finished
            - wait-print: after finished, print the output
            - no-wait: **background**, immediately return, suitable for **forever-looping**, use:
            p = await popen('cmd', mode='bg')
            await p.expect(pexpect.EOF, async_=True)
            print(p.before.decode().strip())
        kwargs: `pexpect.spawn()` args

    Returns:
        process (pexpect.spawn):
    """
    Log.info(f"{mode}: {cmd=}") if mode != 'wait' else None
    dim = get_terminal_size()
    dim = dim.lines, dim.columns
    p = pexpect.spawn(cmd, timeout=timeout, dimensions=dim, **kwargs)
    FD = sys.stdout.fileno()
    def os_write(): return os.write(FD, p.read_nonblocking(4096))
    if mode == 'realtime':
        while p.isalive():
            try:
                os_write()
            except pexpect.EOF:
                break
            except pexpect.TIMEOUT:
                Log.warning(f"Timeout kill: {cmd}")
                break
            except Exception:
                raise
            await aio.sleep(0.1)
        try:
            os_write()
        except pexpect.EOF:
            ...
    elif mode == 'wait':
        while p.isalive():
            try:
                await p.expect(pexpect.EOF, async_=True)
            except pexpect.TIMEOUT:
                Log.warning(f"Timeout kill: {cmd}")
                break
            except Exception:
                raise
    elif mode == 'no-wait':
        return p
    else:
        raise ValueError(f"Invalid mode: {mode}")
    p.before = p.before.decode().strip() if p.before else ''
    if p.exitstatus != 0:
        if Raise:
            raise ChildProcessError(f"{cmd}")
        else:
            Log.warning(f'{p.exitstatus} from "{cmd}" → {p.before}')
    return p


@copy_kwargs(popen)
async def echo(*args, **kwargs):
    p = await popen(*args, mode='wait', **kwargs)
    return p, str(p.before)


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
    dry_run=False,
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
        debt = debt < -int(options.get('retry-wait', _RELAX))
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
    # TODO: queue design for run_1by1, 同域名的下载，等待上一个下载完成后再开始下一个
    options = {**_OPT, **kwargs}
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
    Wait = int(options.get('retry-wait', _RELAX))    # type: ignore
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
    def get(cls, value: Callable | Any = None):
        if Single.instance is None:
            if callable(value):
                Single.instance = value()
            else:
                Single.instance = value
        return Single.instance


@deprecated('Use `ffmpeg` instead')
async def ffmpeg_(
    input: str,
    out: str,
    fps: int | None = None,
    crf: int | None = 20,    # 17 lossless,23,28
    start: str = '00:00:00',
    duration: str | None = None,
    encode: Literal['copy', 'h264', 'av1'] = 'copy',
    overwrite=True,
    **kwargs
):
    # TODO: use nvidia hardware acceleration

    args = ''
    if overwrite:
        args += '-y '
    if crf:
        args += f'-crf {crf} '
    if duration:
        args += f'-ss {start} -t {duration} '
    if encode != 'copy' and fps is None:
        from fractions import Fraction
        meta = ffprobe(input, timeout=_RELAX)
        frac = Fraction(meta['streams'][0]['avg_frame_rate'])
        fps = round(frac.numerator / frac.denominator)
        args += f'-r {fps} '
    if encode == 'copy':
        args += '-c copy '
    elif encode == 'h264':
        args += '-c:v libx264 -c:a aac '

    cmd = filter(None, ['ffmpeg', '-hide_banner', '-i', f"{input}", args, f"{out}"])
    cmd = ' '.join(cmd)
    return await popen(cmd, **kwargs)


class Kw_ff_streams(TypedDict):
    index: int
    codec_name: Literal['h264', 'h265', 'aac'] | str
    codec_type: Literal['video', 'audio', 'subtitle']
    width: int
    height: int
    r_frame_rate: str
    avg_frame_rate: str


class Kw_ffprobe(TypedDict):
    streams: List[Kw_ff_streams]
    format: dict


@deprecated('Use `ffprobe` instead')
async def ffprobe_(input: str):
    """
    get metadata of a video

    usage:
    ```python
    d = await ffprobe('x.mp4')
    print(d['streams'][0]['r_frame_rate'])
    ```
    """
    cmd = f'ffprobe -v quiet -print_format json -show_streams -show_format "{input}"'
    p = await popen(cmd, mode='wait')
    if isinstance(p.before, bytes):
        text = p.before.decode().strip()
        js = json.loads(text)
        if IS_DEBUG:
            json.dump(js, sys.stdout, ensure_ascii=False, indent=2)
        return js
    else:
        raise RuntimeError(f"{cmd} → {p.before}")


def is_vbr(metadata: dict[str, Any], codec_type: Literal['video', 'audio'] = 'video'):
    """is bitrate variable, fallback is True"""
    for s in metadata['streams']:
        if s['codec_type'] == codec_type:
            IS = s['r_frame_rate'] != s['avg_frame_rate']
            Log.debug(f"{'VBR' if IS else 'CBR'} from {metadata}")
            return IS
    return True


def range_time(Str: str):
    """convert str to timedelta

    Args:
        Str (str): <start>+<duration> or <start>,<end>
        e.g.:
        - 00:00:00+00:00:05
        - 0:0:0+0:5
        - 61+0.5    # 61s ~ 61.5s
        - 10       # 0s ~ 10s
    """
    TIME_FORMAT = '%H:%M:%S.%f'
    _range = re.split(r'[+,]', Str)
    if len(_range) == 1:
        start = timedelta(seconds=0)
        _range.insert(0, start)
    if len(_range) != 2:
        Log.warning(f"Invalid time range: {Str}, please use <start>+<duration> or <start>,<end>")
    for i, str_time in enumerate(_range):
        if not isinstance(str_time, str):
            continue
        Try = str_time.split(':')
        _len = min(len(Try), 3)
        a = 9 - 3 * _len
        b = len(TIME_FORMAT) if '.' in str_time else -3
        if len(Try) == 1:
            sec = float(Try[0])
            t = timedelta(seconds=sec)
        else:
            _t = datetime.strptime(str_time, TIME_FORMAT[a:b])
            t = timedelta(hours=_t.hour, minutes=_t.minute, seconds=_t.second, milliseconds=_t.microsecond)
        if i == 0:
            start = t
        elif i == 1:
            if ',' in Str:
                end = t
                duration = end - start
            else:
                duration = t
                # end = start + duration
    Log.info(f"{start}+{duration} from {Str}")
    return start, duration


async def ffmpeg_or_link(from_file: str, to_dir: str, Range='', fps_times=5):
    """if file is vbr, ffmpeg to re-encode  
    else create soft symlink

    Args:
        from_file (str): input video file
        to_dir (str): output directory, e.g.: `output/AAA/...`
        Range (str): see `range_time()`
        fps_times (int): round to times of fps_times, by default leads to 5,10,15,20 fps...

    Returns:
        to_file (str): path of final video file
    """
    kw, is_ffmpeg_from = need_ffmpeg(from_file, Range, fps_times)
    filename = os.path.splitext(os.path.basename(from_file))[0]
    to_dir = os.path.join(to_dir, filename)   # output/xxx
    to_file = os.path.join(to_dir, filename + '.mp4')
    mkdir(to_dir)

    is_ffmpeg_to = os.path.exists(to_file)
    if is_ffmpeg_to:
        _, is_ffmpeg_to = need_ffmpeg(to_file, fps_times=fps_times)
    else:
        is_ffmpeg_to = True

    if is_ffmpeg_to:
        if is_ffmpeg_from:
            p = (
                ffmpeg.input(from_file)
                .output(filename=to_file, vcodec='libx264', acodec='aac', **kw)
                .global_args(hide_banner=not IS_DEBUG)
                .run_async())
            poll = None
            while poll is None:
                poll = p.poll()
                await aio.sleep(0.2)
        else:
            relink(from_file, to_file)
    return to_file


def need_ffmpeg(from_file, Range='', fps_times=5):
    kw: dict[str, Any] = {}
    metadata = ffprobe(from_file)
    from_fps = Fraction(metadata['streams'][0]['r_frame_rate'])
    to_fps = round(from_fps.numerator / from_fps.denominator / fps_times) * fps_times
    from_fps = from_fps.numerator / from_fps.denominator
    if Range:
        is_ffmpeg = True
        r = [r.total_seconds() for r in range_time(Range)]
        kw.update({'ss': r[0], 't': r[1]})
    if is_diff_fps := from_fps != to_fps:
        is_ffmpeg = True
        kw.update({'r': to_fps})
    if not Range and not is_diff_fps:
        is_ffmpeg = is_vbr(metadata)
    return kw, is_ffmpeg


Aria = None
try:
    import regex as re
    import aria2p
    import aiohttp
    import pexpect
    import ffmpeg
    from ffmpeg import probe as ffprobe
    Aria = try_aria_port()

    async def is_resumable_file(url: str, timeout=_TIMEOUT):
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
        PROGRESS_DL.stop()
        aio.run(popen('python -c "from tqdm import tqdm; import time; import sys; [time.sleep(0.02) for _ in tqdm(range(100),file=sys.stdout)]"', mode='realtime'))
except Exception as e:
    Log.error(e)

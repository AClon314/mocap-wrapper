import os
import subprocess as sp
import asyncio as aio
from sys import platform
from datetime import timedelta
from mocap_wrapper.logger import getLog
from typing import Callable, Coroutine, List, Literal, Union, overload
Log = getLog(__name__)
TIMEOUT = timedelta(minutes=15).seconds
CHECK_KWARGS = True
ARIA_PORTS = [6800, 16800]
OPT = {
    'dir': '.',
    # 'out': 'filename',
    'continue': True,
    'split': 5,
    'max_connection_per_server': 5,
    'max-concurrent-downloads': 2,
    'min_split_size': 20,  # don't split if file size < 40M
    'retry-wait': 5,
    'max-tries': 5,
}
is_linux = platform == 'linux'
is_win = platform == 'win32'
is_mac = platform == 'darwin'


def path_expand(path: str):
    return os.path.expandvars(os.path.expanduser(path))


def run_async(func: Coroutine, timeout=TIMEOUT, loop=aio.get_event_loop()):
    return aio.run_coroutine_threadsafe(func, loop).result(timeout)


def rich_finish(task: int):
    PG.update(task, completed=100)
    PG.start_task(task)


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
            Log.warning(f"Failed to import aria2p")
            return None
        except Exception as e:
            Log.warning(f"Failed to connect to aria2 on port {port}: {e}")
            return None


async def aria(url: Union[str, Callable], duration=0.5, dry_run=False, P: 'Progress' = None, **kwargs: 'aria2p.Options'):
    """check if download is complete every `duration` seconds

    `**kwargs` for `aria2p.API.add_uris(...)`:
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
    if not P:
        P = PG
    options = {**OPT, **kwargs}
    Log.debug(f"options before: {options}")
    # if options.get('out'):
    #     options['dir'] = ''

    async def add_download():
        nonlocal url
        url = url() if callable(url) else url
        dl = Aria.add_uris([url], options=options)
        dl = Aria.get_download(dl.gid)
        def Url(): return dl.files[0].uris[0]['uri']     # get redirected url
        def Path(): return dl.files[0].path
        def Filename(): return os.path.basename(Path())
        if dl.is_complete:
            Log.info(f"{Path()} already downloaded")
            return dl
        Log.debug(f"options after: {dl.options.get_struct()}")

        task = P.add_task(f"⬇️ Download {Filename()}", start=False) if P else None
        while not dl.is_complete:
            Log.debug(f"current: {dl.__dict__}")
            if dry_run and dl.completed_length > 1024 ** 2 * 5:
                break

            await aio.sleep(duration)
            dl = Aria.get_download(dl.gid)

            status = f'{dl.completed_length_string()}/{dl.total_length_string()} @ {dl.download_speed_string()}'
            if P:
                if dl.total_length > 0:
                    P.start_task(task)
                P.update(task, description=f"⬇️ {Filename()}",
                         total=dl.total_length,
                         completed=dl.completed_length,
                         status=status)
            else:
                Log.info(status)

        P.remove_task(task) if P else None
        Aria.remove([dl])
        dl.path = Path()
        dl.url = Url()
        return dl

    Try = options['max-tries']
    dl = await add_download()
    while dl.status == 'error' and Try > 0:
        Try -= 1
        Log.error(f"{Try} retry {dl.path} after {options['retry-wait']} sec, ❌ {dl.error_message} from '{dl.url}'")
        await aio.sleep(int(options['retry-wait']))
        dl = await add_download()

    if dl.completed_length < 1:
        Log.warning(f"Download failed: {url}")

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


Aria = None
try:
    import aria2p
    from worker import worker, async_worker, ThreadWorkerManager
    from rich import print
    from rich.text import Text
    from rich.progress import Progress, TextColumn

    class SpeedColumn(TextColumn):
        def render(self, task):
            if 'status' in task.fields.keys():
                return Text(task.fields['status'])
            elif task.speed:
                return Text(f"{task.speed:.3f} steps/s")
            else:
                return Text("")
    Aria: 'aria2p.API' = try_aria_port()
    PG = Progress(*Progress.get_default_columns(), SpeedColumn(''))
    PG.start()
    if __name__ == '__main__':
        ...
        # aio.run()

except ImportError as e:
    Log.error(f"⚠️ detect missing packages, please check your current conda environment. {e}")

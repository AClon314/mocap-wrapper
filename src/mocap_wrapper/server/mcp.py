import asyncio
from functools import partial
from fastapi import FastAPI
from fastmcp import FastMCP, Context
from mocap_wrapper import OUTPUT_DIR, SELF_DIR, mocap
from mocap_wrapper.lib import RUNS, CONFIG, LOG_LEVEL, PACKAGE, TYPE_RUNS, __version__
from typing import Callable, Sequence
TITLE = f'{PACKAGE} {{}} backend server'
HOST = '0.0.0.0'
PORT = 23333
MCP = FastMCP(TITLE.format('MCP'), version=__version__)
APP_MCP = MCP.http_app(path='/mcp')
APP = FastAPI(lifespan=APP_MCP.lifespan, title=TITLE.format('fastapi'), version=__version__)


def tool_post(func: Callable | None = None, **kwargs):
    """
    equal to `@MCP.tool` & `@APP.post`

    Args:
        name (str): tool name
        description (str): ...
        tags (list[str]): ...
    """
    if func is None:
        return partial(tool_post, **kwargs)
    name = func.__name__
    doc = func.__doc__ or None
    kwargs.setdefault('name', name)
    kwargs.setdefault('description', doc)
    mcp_tool = MCP.tool(**kwargs)
    fastapi_post = APP.post(**{'path': f'/{name}', 'operation_id': name, **kwargs})
    return mcp_tool(fastapi_post(func))


@APP.get('/')
async def root():
    return {
        'message': RUNS,
        'version': __version__}


@tool_post
async def install(by: Sequence[TYPE_RUNS], at=CONFIG['search_dir'], ctx: Context | None = None):
    '''Install default runs with gvhmr, or specified runs if `by` is provided.'''
    if ctx:
        await ctx.info(f'Install {by} {at=}...')
        # progress = 0
        # while progress < 1.0:
        #     progress += 10
        #     await ctx.report_progress(progress, 100, f'Installing at {progress}...')
        #     await asyncio.sleep(2)
    await mocap(by=by, at=at)
    return at


@tool_post
async def run(inputs: list[str], outdir=OUTPUT_DIR, Range='', by: Sequence[TYPE_RUNS] = RUNS, ctx: Context | None = None):
    '''Run the mocap model and get results.'''
    if ctx:
        await ctx.info(f'Run {by}...')
        # progress = 0
        # while progress < 1.0:
        #     progress += 10
        #     await ctx.report_progress(progress, 100, f'Running at {progress}...')
        #     await asyncio.sleep(2)
    await mocap(inputs=inputs, outdir=outdir, Range=Range, by=by)
    return outdir

APP.mount("/", APP_MCP)


def main():
    import uvicorn
    uvicorn.run(
        "mocap_wrapper.server.mcp:APP",
        host=HOST, port=PORT, log_level=LOG_LEVEL,
        reload=True,  # 启用热重载
        reload_dirs=[SELF_DIR],
        timeout_graceful_shutdown=1,  # 优雅关闭超时时间（秒）
        timeout_keep_alive=1,  # 保持连接超时时间
        reload_delay=1
    )


if __name__ == "__main__":
    main()

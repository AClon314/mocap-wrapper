import re
import shutil
import signal
import aiohttp
import asyncio
import platform
from ..lib import getLogger, TYPE_RUNS, BINS, i_pkgs, run_tail, try_aria_port, Aria, is_win, is_mac, is_linux
from typing import Sequence
Log = getLogger(__name__)


async def install(runs: Sequence[TYPE_RUNS], **kwargs):
    global Aria
    tasks = []

    pkgs = {p: shutil.which(p) for p in BINS}
    Log.debug(f'installed: {pkgs}')
    pkgs = [p for p, v in pkgs.items() if not v]
    if any(pkgs):
        await i_pkgs()

    p_aria = None
    if Aria is None:
        # try to start aria2c
        p_aria = await run_tail('aria2c --enable-rpc --rpc-listen-port=6800').Await()
        await asyncio.sleep(1.5)
        Aria = try_aria_port()
        if Aria is None:
            raise Exception("Failed to connect rpc to aria2, is aria2c/Motrix running?")
    Log.debug(Aria)

    # Log.debug(f'{runs=}')
    if 'gvhmr' in runs:
        from .gvhmr import i_gvhmr
        tasks.append(i_gvhmr(**kwargs))
    if 'wilor' in runs:
        from .wilor_mini import i_wilor_mini
        tasks.append(i_wilor_mini(**kwargs))

    ret = await asyncio.gather(*tasks)
    p_aria.kill(signal.SIGKILL) if p_aria else None
    return ret


async def dl_pytorch3d(To: str):
    github = 'https://github.com/MiroPsota/torch_packages_builder/releases/download'
    tag = 'pytorch3d'
    if is_win:
        ...


async def find_releases_by_tag(repo: str, tag_pattern: str):
    """
    根据tag模式在GitHub仓库中查找所有匹配的release tags

    Args:
        repo: GitHub仓库路径，如 "MiroPsota/torch_packages_builder"
        tag_pattern: 要查找的tag模式，如 "pytorch3d"

    Returns:
        匹配的tag列表，如 ['pytorch3d-0.7.8', 'pytorch3d-0.6.0']
    """
    url = f"https://api.github.com/repos/{repo}/releases"
    matching_tags = []

    try:
        async with aiohttp.ClientSession() as session:
            page = 1
            while True:
                params = {'page': page, 'per_page': 100}
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        Log.error(f"GitHub API请求失败: {response.status}")
                        break

                    releases = await response.json()
                    if not releases:  # 没有更多页面
                        break

                    for release in releases:
                        tag_name = release.get('tag_name', '')
                        if tag_pattern in tag_name:
                            matching_tags.append(tag_name)

                    page += 1

    except Exception as e:
        Log.error(f"查找releases时出错: {e}")

    # 按版本号降序排序
    matching_tags.sort(key=lambda x: _extract_version(x), reverse=True)
    Log.debug(f"找到匹配的tags: {matching_tags}")
    return matching_tags


async def find_best_wheel(
    repo: str,
    tag: str,
    pytorch_version: str = "2.3.0",
    cuda_version: str = "12.1",
    python_version: str = "3.10"
):
    """
    寻找最符合当前环境的wheel文件URL

    Args:
        repo: GitHub仓库路径
        tag: release tag
        pytorch_version: PyTorch版本，如 "2.3.0"
        cuda_version: CUDA版本，如 "12.1" 或 "cpu"
        python_version: Python版本，如 "3.10"

    Returns:
        最匹配的wheel文件下载URL，如果未找到则返回None
    """
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"

    # 获取系统信息
    os_info = _get_os_info()
    arch_info = _get_arch_info()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    Log.error(f"无法获取release信息: {response.status}")
                    return None

                release_data = await response.json()
                assets = release_data.get('assets', [])

                # 过滤wheel文件
                wheel_assets = [asset for asset in assets
                                if asset.get('name', '').endswith('.whl')]

                if not wheel_assets:
                    Log.warning(f"在tag {tag} 中未找到wheel文件")
                    return None

                # 构建匹配条件
                pytorch_short = pytorch_version.replace('.', '')[:3]  # "2.3.0" -> "230"
                cuda_short = cuda_version.replace('.', '') if cuda_version != "cpu" else "cpu"  # "12.1" -> "121"
                python_short = python_version.replace('.', '')  # "3.10" -> "310"

                # 评分函数来找最佳匹配
                best_score = -1
                best_url = None

                for asset in wheel_assets:
                    filename = asset.get('name', '')
                    score = _score_wheel_compatibility(
                        filename, pytorch_short, cuda_short, python_short, os_info, arch_info
                    )

                    if score > best_score:
                        best_score = score
                        best_url = asset.get('browser_download_url')

                if best_url:
                    Log.info(f"找到最佳匹配的wheel: {best_url}")
                else:
                    Log.warning("未找到兼容的wheel文件")

                return best_url

    except Exception as e:
        Log.error(f"查找wheel文件时出错: {e}")
        return None


def _extract_version(tag: str) -> tuple:
    """从tag中提取版本号用于排序"""
    version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', tag)
    if version_match:
        return tuple(map(int, version_match.groups()))
    return (0, 0, 0)


def _get_os_info() -> str:
    """获取操作系统信息"""
    if is_win:
        return "win"
    elif is_mac:
        return "macosx"
    elif is_linux:
        return "linux"
    else:
        return "unknown"


def _get_arch_info() -> str:
    """获取处理器架构信息"""
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        return "x86_64"
    elif machine in ['aarch64', 'arm64']:
        return "arm64"
    elif machine.startswith('arm'):
        return "arm64"
    else:
        return machine


def _score_wheel_compatibility(
    filename: str,
    pytorch_version: str,
    cuda_version: str,
    python_version: str,
    os_info: str,
    arch_info: str
) -> int:
    """
    为wheel文件兼容性打分
    分数越高表示越匹配当前环境
    """
    score = 0
    filename_lower = filename.lower()

    # PyTorch版本匹配 (最重要)
    if f"pt{pytorch_version}" in filename_lower:
        score += 100
    elif pytorch_version[:2] in filename_lower:  # 主版本匹配
        score += 50

    # CUDA版本匹配
    if cuda_version == "cpu":
        if "cpu" in filename_lower:
            score += 80
    else:
        if f"cu{cuda_version}" in filename_lower:
            score += 80
        elif "cu12" in filename_lower and cuda_version.startswith("12"):
            score += 60

    # Python版本匹配
    if f"cp{python_version}" in filename_lower:
        score += 60
    elif python_version[:2] in filename_lower:
        score += 30

    # 操作系统匹配
    if os_info == "win" and "win" in filename_lower:
        score += 40
    elif os_info == "linux" and "linux" in filename_lower:
        score += 40
    elif os_info == "macosx" and "macosx" in filename_lower:
        score += 40

    # 架构匹配
    if arch_info == "x86_64" and "x86_64" in filename_lower:
        score += 30
    elif arch_info == "arm64" and ("arm64" in filename_lower or "universal2" in filename_lower):
        score += 30
    elif "amd64" in filename_lower and arch_info == "x86_64":
        score += 25

    return score


# 示例使用函数
async def example_usage():
    """使用示例"""
    # 1. 查找pytorch3d的所有release tags
    tags = await find_releases_by_tag("MiroPsota/torch_packages_builder", "pytorch3d")
    print(f"找到的tags: {tags}")

    # 2. 查找最匹配的wheel文件
    if tags:
        wheel_url = await find_best_wheel(
            "MiroPsota/torch_packages_builder",
            tags[0],  # 使用最新版本
            pytorch_version="2.3.0",
            cuda_version="12.1",
            python_version="3.10"
        )
        print(f"最佳匹配的wheel: {wheel_url}")

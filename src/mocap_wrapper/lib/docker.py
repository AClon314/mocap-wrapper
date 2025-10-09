"""
use podman/udocker as package manager for AI MCP models.

Usage:
```
docker images
docker pull <image>
docker save <image> -o <image>.tar
docker run -it --rm <image> bash
```
"""

import os
from .static import is_linux
from .logger import getLogger
from .process import run_tail

Log = getLogger(__name__)


def inContainer():
    """am I docker in docker? return True if `cat /proc/1/cgroup` == `0::/`"""
    if not is_linux:
        return False
    with open("/proc/1/cgroup", "rt") as f:
        LINES = f.read().strip().splitlines()
    last = LINES[-1]
    if len(LINES) > 1:
        Log.warning(f"cgroup v1 detected, report issue if any. {locals()=}")
    if last == "0::/":
        return True
    elif "scope" in last:
        return False
    else:
        return True


def _nameOfImage(image: str) -> str:
    """get a valid container name from image name"""
    return image.split("/")[-1].replace(":", "-").replace(".", "-")


def podman(
    image="ghcr.io/containerd/busybox:latest",
    cmd: list[str] = [],
    args: list[str] = [],
    name: str | None = None,
):
    """
    Args:
        name: name & hostname, if None, use image name, else if "", use random name
    """
    if name is None:
        name = _nameOfImage(image)
    arg_name = (
        [
            f"--name={name}",
            f"--hostname={name}",
        ]
        if name
        else []
    )
    arg_linux = (
        [
            "--env=DISPLAY",
            "--volume=/tmp/.X11-unix:/tmp/.X11-unix",
            "--volume=/etc/localtime:/etc/localtime:ro",
        ]
        if is_linux
        else []
    )
    return run_tail(
        [
            "podman",
            "run",
            "--replace",
            # "--detach",  # run in background, instead of `--it`
            '--label="io.containers.autoupdate=registry"',
            *arg_name,
            # '--log-driver=journald',
            # '--device="nvidia.com/gpu=all"',  # TODO: AMD gpu?
            "--security-opt=label=disable",
            *arg_linux,
            *args,
            image,
            *cmd,
        ]
    )


def udocker(
    image="ghcr.io/containerd/busybox:latest",
    cmd: list[str] = [],
    args: list[str] = [],
    name: str | None = None,
):
    if name is None:
        name = _nameOfImage(image)
    allow_root = (
        [
            "--allow-root",
        ]
        if os.geteuid() == 0
        else []
    )
    return run_tail(
        [
            "udocker",
            *allow_root,
            "run",
            *args,
            image,
            *cmd,
        ]
    )


# /root/.pixi/bin/udocker --allow-root install
# /root/.pixi/bin/udocker --allow-root --help

if __name__ == "__main__":
    podman(cmd=["sh", "-c", "cat /proc/1/cgroup"])
    # udocker(cmd=["sh", "-c", "cat /proc/1/cgroup"])

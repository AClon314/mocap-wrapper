#!/bin/env python
"""
Post process for buf generate
"""
import re
import shutil
import subprocess
from pathlib import Path

SELF = Path(__file__)
DIR_API = SELF.resolve().parent
ROOT = DIR_API.parent  # 项目根（与 package.json 同级）
DIR_MOCAP_API = ROOT / "src" / "mocap_wrapper" / "api"


def run(cmd, err_hint: str = ""):
    print(">", cmd)
    try:
        return subprocess.run(cmd, shell=True, check=True, cwd=DIR_API)
    except subprocess.CalledProcessError as e:
        if err_hint:
            print(f"💡 {err_hint=}")
        raise


run("buf dep update")
run("buf lint")
run("buf generate", "maybe you can try `npm/pnpm/bun run api:gen` ?")

RE_IMPORT = re.compile(r"\nimport.*?\.(?=\w*_pb2 as )")
RE_FROM_IMPORT = re.compile(r"(?<=\nfrom )(?=buf\.validate import validate_pb2)")
PB2_PY = list(DIR_MOCAP_API.glob("**/*.py")) + list(DIR_MOCAP_API.glob("**/*.pyi"))
for py in PB2_PY:
    if py.name == "validate_pb2.py":
        continue
    # print(f"read {py=}")
    with py.open() as f:
        text = f.read()
    Import = RE_IMPORT.search(text)
    from_import = RE_FROM_IMPORT.search(text)
    if not (Import or from_import):
        continue
    print(f"patch {py=}")
    text = RE_IMPORT.sub("\nfrom . import ", text)
    text = RE_FROM_IMPORT.sub("..", text)
    with py.open("w") as f:
        f.write(text)

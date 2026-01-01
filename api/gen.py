#!/env/python
"""
Post process for buf generate
"""
import re, shutil
from pathlib import Path

SELF = Path(__file__)
CWD = SELF.resolve().parents[1]  # 项目根（与 package.json 同级）
DIR_SRC = CWD / "src"
DIR_MOCAP = DIR_SRC / "mocap_wrapper"
DIR_MOCAP_API = DIR_MOCAP / "api"
DIR_BUF_FROM = DIR_SRC / "buf"
DIR_BUF_TO = DIR_MOCAP_API / "buf"
if not DIR_BUF_FROM.exists():
    raise FileNotFoundError(f"{DIR_BUF_FROM=}")
if DIR_BUF_TO.exists():
    print(f"remove {DIR_BUF_TO=}")
    shutil.rmtree(DIR_BUF_TO)
shutil.move(DIR_BUF_FROM, DIR_MOCAP_API)

RE_IMPORT = re.compile(r"(?<=from )(?=buf\.validate import validate_pb2)")
PB2_PY = [p for p in DIR_MOCAP_API.glob("**/*_pb2.py*") if p.name != "validate_pb2.py"]
for py in PB2_PY:
    print(f"patch {py=}")
    with py.open() as f:
        text = f.read()
    text = RE_IMPORT.sub("..", text)
    with py.open("w") as f:
        f.write(text)

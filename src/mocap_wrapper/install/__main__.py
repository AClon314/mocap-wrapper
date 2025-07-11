import sys
import asyncio
from . import install
asyncio.run(install(sys.argv))  # type: ignore

"""global inject & which need to be expose"""

from .lib.logger import getLogger

Log = getLogger(__name__)

try:
    from .app import mocap, script_entry
except ImportError as e:
    Log.exception(f"{__name__=}:", exc_info=e)

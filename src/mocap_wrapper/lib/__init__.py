'''
if module=`run/`, you can only use `lib.static`, `lib.logger`, and `lib.config`

else, enjoy full access to all lib modules
'''
from .static import *
from .logger import *
from .config import *
try:
    from .process import *
    from .aria import *
    from .pkg_mgr import *
    from .FFmpeg import *
    from .data_viewer import *
except ImportError as e:
    Log.exception(f'\n{__name__=}:', exc_info=e) if IS_DEBUG else None

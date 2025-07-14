import os
IS_DEBUG = os.environ.get('LOG', 'i').lower()
IS_DEBUG = IS_DEBUG[0] == 'd' if IS_DEBUG else False
try:
    from .app import mocap, script_entry
except ImportError as e:
    from logging import getLogger
    Log = getLogger(__name__)
    Log.exception(f'\n{__name__=}:', exc_info=e) if IS_DEBUG else None

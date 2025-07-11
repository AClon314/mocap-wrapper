import os
IS_DEBUG = os.environ.get('LOG', 'i').lower()
IS_DEBUG = IS_DEBUG[0] == 'd' if IS_DEBUG else False
try:
    from .app import mocap, script_entry
except ImportError as e:
    print(f'Skip root import') if IS_DEBUG else None

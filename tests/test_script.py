#!/bin/env python
import os
import pytest
import logging
from concurrent.futures import ThreadPoolExecutor
from mocap_wrapper.script.mamba import MIRROR_DL, download
Log = logging.getLogger(__name__)
IS_DEBUG = os.getenv('GITHUB_ACTIONS', None)


def _download(url):
    try:
        download(url, log=False)
        Log.info(f'✅ {url}')
        return True
    except Exception as e:
        Log.error(f'{e} from {url}')
        return False


@pytest.mark.skipif(bool(IS_DEBUG), reason='test manually, CI would increase pressure on welfare mirror servers')
@pytest.mark.parametrize("suffix", [
    "/godotengine/godot/releases/download/4.4.1-stable/godot-4.4.1-stable.tar.xz",
])
def test_mirror(suffix: str):
    urls: dict[str, None | bool] = {u[0]: None for u in MIRROR_DL}
    Log.info(f'Checking {len(urls)} URLs with suffix: {suffix}')
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_download, [u + suffix for u in urls.keys()]))
    for url, result in zip(urls.keys(), results):
        urls[url] = result
    ture = [u for u, b in urls.items() if b is True]
    false = [u for u, b in urls.items() if b is False]
    none = [u for u, b in urls.items() if b is None]
    Log.info(f'✅ {len(ture)} succeeded: {ture}')
    Log.warning(f'❓ {len(none)} in buggy: {none}') if len(none) > 0 else None
    Log.error(f'❌ {len(false)} failed: {false}')

#! /bin/env python
"""data viewer for NPT, Numpy Pickle pyTorch"""
try:
    import re
    import os
    import json
    import argparse
    import pickle
    import numpy as np
    import torch
    from typing import Any, Optional
except ImportError as e:
    ...
_FILE = [
    '/home/n/document/code/mocap/output/0_input_video/0_input_video.mp4_hand00.pt',
    '/home/n/document/code/mocap/output/hands_easy✋/hands_easy✋.pt',
    '/home/n/document/code/mocap/output/背越式跳高（慢动作）/mocap_背越式跳高（慢动作）.npz'
]
_MAX_DEPTH = 4
_MAX_KEYS = 100
_OUTPUT = './data_viewer'
_FLAT = {}
_SHAPE = {}
def Type(v): return str(type(v))[8:-2]
def prefix(file) -> str: return os.path.splitext(os.path.basename(file))[0]
def is_dict(v): return hasattr(v, 'keys')
def is_list(v): return hasattr(v, '__iter__') and not is_dict(v) and not isinstance(v, str)
def load_np(file): return np.load(file, allow_pickle=True)
def load_pt(file): return torch.load(file)


def load_pkl(file):
    with open(file, 'rb') as f:
        data = pickle.load(f)
    return data


def load(file):
    if file.endswith('.pt'):
        data = load_pt(file)
    elif file.endswith('.pkl'):
        data = load_pkl(file)
    elif file.endswith('.npy') or file.endswith('.npz'):
        data = load_np(file)
    else:
        raise ValueError(f'Unsupported file type: {file}')
    print(f'load as {Type(data)} from {file}')
    return data, file


def tree_node(v):
    """
    Args:
        shape_old(tuple): for compare
    ```python
    shape = getattr(v, 'shape', None)
    ```"""
    shape = getattr(v, 'shape', '')
    dtype = getattr(v, 'dtype', None)
    dtype = Type(dtype) if dtype else None
    if shape or dtype:
        ret = {
            'shape': shape,
            'type': Type(v),
            'dtype': dtype,
        }
        shape_old = _SHAPE.get(id(v), None)
        if shape_old and shape_old != shape:
            ret['shape_old'] = shape_old
        return ret
    return v


def expand_dict(data, prefix='', depth=0) -> dict[str, Any]:
    if depth > _MAX_DEPTH:
        print(f'too deep, depth: {depth}')
        return {}
    depth += 1

    if is_list(data):
        for i, x in enumerate(data):
            expand_dict(x, f'{prefix}列{i}一', depth)
    elif is_dict(data):
        for k, v in data.items():
            # 如果k有非下划线符号，全部替换成_
            k = re.sub(r'[^a-zA-Z0-9_]', '_', k)

            shape_old = getattr(v, 'shape', None)
            if is_dict(v):
                expand_dict(v, f'{prefix}{k}一', depth)
            else:
                if isinstance(v, torch.Tensor):
                    for i, x in enumerate(v.shape):
                        if x == 1:
                            v = v.squeeze(0)
                elif isinstance(v, np.ndarray):
                    for i, x in enumerate(v.shape):
                        if x == 1:
                            v = np.squeeze(v, 0)
                if len(_FLAT.keys()) >= _MAX_KEYS:
                    print(f'too many keys, keys.len: {len(_FLAT.keys())}')
                    return {}
                _FLAT[f'{prefix}{k}'] = v
                if shape_old:
                    _SHAPE[id(v)] = shape_old
    return _FLAT


def json_dumps(data, **kwargs):
    """Safely serialize data to JSON, skipping non-serializable values."""
    def default_handler(obj):
        try:
            return tree_node(obj)
        except Exception:
            print(f'Error serializing {obj} of type {type(obj)}')
            return None  # skip
    return json.dumps(
        data, default=default_handler, ensure_ascii=False, **kwargs)


def get_global(files, Print=True):
    for f in files:
        try:
            _prefix = prefix(f) if len(_FILE) > 0 else ''
            expand_dict(load(f), prefix=_prefix + '一')
            globals().update(_FLAT)
        except Exception as e:
            print(f'Error {f}: {e}')


def main():
    global _FILE
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', nargs='+', type=str, help='input file')
    arg.add_argument('-o', '--output', type=str, metavar=_OUTPUT, default=_OUTPUT, help='.npz filename')
    args = arg.parse_args()
    if args.input:
        _FILE += args.input
    get_global(_FILE, Print=False)
    print(json_dumps(_FLAT, indent=4))
    np.savez_compressed(_OUTPUT, **_FLAT)


if __name__ == '__main__':
    main()

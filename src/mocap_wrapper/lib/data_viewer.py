#! /bin/env python
"""data viewer for NPT, Numpy Pickle pyTorch
```python
from data_viewer import convert_npt
```
"""
import os
import re
import json
import argparse
from typing import Any
try:
    import pickle
    import numpy as np
    import torch
except ImportError as e:
    ...
_FILE = []
_MAX_DEPTH = 4
_MAX_KEYS = 100
_PY_VAR = True
_OUTNAME = './data_viewer'
_FLAT = {}
_SHAPE = {}
_SEP = '一' if _PY_VAR else '→'
def Type(v): return str(type(v))[8:-2]
def sub(str): return re.sub(r'[^a-zA-Z0-9_]', '_', str)
def prefix(file) -> str: return os.path.splitext(os.path.basename(file))[0]
def is_dict(v): return hasattr(v, 'keys')
def is_list(v): return hasattr(v, '__getitem__') and hasattr(v, '__len__') and getattr(v, 'ndim', 0) != 0 and not is_dict(v) and not isinstance(v, str)
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
    return data


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
            'type': Type(v),
            'dtype': dtype,
            'shape': shape,
        }
        shape_old = _SHAPE.get(id(v), None)
        if shape_old and shape_old != shape:
            ret['shape_old'] = shape_old
        return ret
    return v


def expand_dict(data, prefix='', depth=0) -> dict[str, Any]:
    global _FLAT, _SHAPE, _PY_VAR, _SEP
    if depth > _MAX_DEPTH:
        print(f'too deep, depth: {depth}')
        return {}
    depth += 1

    if is_list(data):
        print(f'list: {prefix} len: {len(data)}')
        if len(data) > 0 and is_dict(data[0]):
            for i, x in enumerate(data):
                expand_dict(x, f'{prefix}列{i}{_SEP}', depth)
        else:
            _FLAT[prefix] = data
    elif is_dict(data):
        for k, v in data.items():
            if _PY_VAR:
                k = sub(k)

            shape_old = getattr(v, 'shape', None)
            if is_dict(v):
                expand_dict(v, f'{prefix}{k}{_SEP}', depth)
            else:
                if isinstance(v, (torch.Tensor, np.ndarray)):
                    while v.shape and v.shape[0] == 1:
                        v = v.squeeze(0)
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


def flatten_data(files):
    global _FLAT
    for f in files:
        is_len = len(files) > 1
        _prefix = prefix(f) if is_len else ''
        if is_len:
            if _PY_VAR:
                _prefix = _SEP + sub(_prefix)
            _prefix += _SEP
        expand_dict(load(f), prefix=_prefix)
        # globals().update(_FLAT)
    return _FLAT


def convert_npt(files: list, outname=_OUTNAME, save=False, Print=False):
    """```python
    _GLOBAL = convert_npt(files=[])
    globals().update(_GLOBAL)
    ```"""
    global _FLAT
    flatten_data(files)
    metadata = json_dumps(_FLAT, indent=2)
    if Print:
        print(metadata)
    if save:
        np.savez_compressed(outname, **_FLAT)
        if outname:
            with open(outname + '.json', 'w') as f:
                f.write(metadata)
    return _FLAT


def argParse():
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', nargs='+', type=str, help='input file')
    arg.add_argument('-o', '--output', type=str, metavar=_OUTNAME, default=_OUTNAME, help='.npz filename')
    args = arg.parse_args()
    global _FILE
    if args.input:
        _FILE += args.input
    convert_npt(_FILE, outname=args.output)
    return args


if __name__ == '__main__':
    argParse()

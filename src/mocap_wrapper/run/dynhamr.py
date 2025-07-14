import os
try:
    from .lib import *
except ImportError:
    from lib import run, Rodrigues, RotMat_to_quat, savez, chdir_gitRepo, continuous, euler, free_ram as _free_ram  # type: ignore
chdir_gitRepo('dynhamr')

_kw = {
    'data': 'video',
    'run_opt': 'True',
    'data.seq': 'hands_wave',
}
kw = [f'{k}={v}' for k, v in _kw.items()]


def run_1():
    p = run(['pixi', 'run', '-q', '--', 'python', os.path.join('dyn-hamr', 'run_opt.py'), *kw])
    return p


if __name__ == '__main__':
    run_1()

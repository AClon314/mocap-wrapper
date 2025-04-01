import os
import sys
import toml
import argparse
from platformdirs import user_config_path
from typing import Literal, Sequence
MAPPING = {
    'gvhmr': 'GVHMR',
}


def chdir_gitRepo(mod: Literal['gvhmr']):
    config_path = user_config_path(appname='mocap_wrapper', ensure_exists=True).joinpath('config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        dst = os.path.join(config['search_dir'], MAPPING[mod])
        sys.path.append(dst)
        os.chdir(dst)
    else:
        raise FileNotFoundError(f'config.toml not found in {config_path}')


TYPE_RANGE = tuple[int, int]


def continuous(List: Sequence[int]) -> list[tuple[int, int]]:
    """
    Detect continuous parts in a sorted list.

    Args:
        List: A sorted list of integers, e.g., [0, 1, 2, 10, 11]

    Returns:
        list(tuple): Each tuple represents a continuous interval, e.g., [(0, 2), (10, 11)]
    """
    if not List:
        return []
    result = []
    start = List[0]
    end = start
    for num in List[1:]:
        if num == end + 1:
            end = num
        else:
            result.append((start, end))
            start = num
            end = num
    result.append((start, end))
    return result


def invert_ranges(ranges: Sequence[tuple], total_range: tuple) -> list[tuple]:
    """
    Invert the given ranges within the total_range.

    Args:
        ranges: A sequence of ranges to be inverted.
        total_range: The total range within which the inversion is performed.

    Returns:
        list(tuple): The inverted ranges.
    """
    total_start, total_end = total_range
    valid_ranges = []
    # Truncate ranges to fit within total_range and collect valid ones
    for r in ranges:
        start = max(r[0], total_start)
        end = min(r[1], total_end)
        if start < end:
            valid_ranges.append((start, end))

    # Merge overlapping or adjacent ranges
    if not valid_ranges:
        return [(total_start, total_end)] if total_start < total_end else []

    sorted_ranges = sorted(valid_ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]
    for current in sorted_ranges[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    # Generate inverted ranges
    inverted = []
    prev_end = total_start
    for interval in merged:
        current_start = interval[0]
        if prev_end < current_start:
            inverted.append((prev_end, current_start))
        prev_end = max(prev_end, interval[1])
    if prev_end < total_end:
        inverted.append((prev_end, total_end))

    return inverted


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        super().print_help(file)
        exit(1)

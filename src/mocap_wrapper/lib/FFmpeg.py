import os
import re
import ffmpeg
import asyncio
from ffmpeg import probe as ffprobe
from fractions import Fraction
from datetime import datetime, timedelta
from .process import mkdir, symlink
from .logger import IS_DEBUG, getLogger
from typing import Any, Literal
Log = getLogger(__name__)


def is_vbr(metadata: dict[str, Any], codec_type: Literal['video', 'audio'] = 'video'):
    """is bitrate variable, fallback is True"""
    for s in metadata['streams']:
        if s['codec_type'] == codec_type:
            IS = s['r_frame_rate'] != s['avg_frame_rate']
            Log.debug(f"{'VBR' if IS else 'CBR'} from {metadata}")
            return IS
    return True


def range_time(Str: str):
    """convert str to timedelta

    Args:
        Str (str): <start>+<duration> or <start>,<end>
        e.g.:
        - 00:00:00+00:00:05
        - 0:0:0+0:5
        - 61+0.5    # 61s ~ 61.5s
        - 10       # 0s ~ 10s
    """
    TIME_FORMAT = '%H:%M:%S.%f'
    _range = re.split(r'[+,]', Str)
    if len(_range) == 1:
        start = timedelta(seconds=0)
        _range.insert(0, start)
    if len(_range) != 2:
        Log.warning(f"Invalid time range: {Str}, please use <start>+<duration> or <start>,<end>")
    for i, str_time in enumerate(_range):
        if not isinstance(str_time, str):
            continue
        Try = str_time.split(':')
        _len = min(len(Try), 3)
        a = 9 - 3 * _len
        b = len(TIME_FORMAT) if '.' in str_time else -3
        if len(Try) == 1:
            sec = float(Try[0])
            t = timedelta(seconds=sec)
        else:
            _t = datetime.strptime(str_time, TIME_FORMAT[a:b])
            t = timedelta(hours=_t.hour, minutes=_t.minute, seconds=_t.second, milliseconds=_t.microsecond)
        if i == 0:
            start = t
        elif i == 1:
            if ',' in Str:
                end = t
                duration = end - start
            else:
                duration = t
                # end = start + duration
    Log.info(f"{start}+{duration} from {Str}")
    return start, duration


async def ffmpeg_or_link(from_file: str, to_dir: str, Range='', fps_times=5):
    """if file is vbr, ffmpeg to re-encode  
    else create soft symlink

    Args:
        from_file (str): input video file
        to_dir (str): output directory, e.g.: `output/AAA/...`
        Range (str): see `range_time()`
        fps_times (int): round to times of fps_times, by default leads to 5,10,15,20 fps...

    Returns:
        to_file (str): path of final video file
    """
    kw, is_ffmpeg_from = is_need_ffmpeg(from_file, Range, fps_times)
    filename = os.path.splitext(os.path.basename(from_file))[0]
    to_dir = os.path.join(to_dir, filename)   # output/xxx
    to_file = os.path.join(to_dir, filename + '.mp4')
    mkdir(to_dir)

    is_ffmpeg_to = os.path.exists(to_file)
    if is_ffmpeg_to:
        _, is_ffmpeg_to = is_need_ffmpeg(to_file, fps_times=fps_times)
    else:
        is_ffmpeg_to = True

    if is_ffmpeg_to:
        if is_ffmpeg_from:
            p = (
                ffmpeg.input(from_file)
                .output(filename=to_file, vcodec='libx264', acodec='aac', **kw)
                .global_args(hide_banner=not IS_DEBUG)
                .run_async())
            poll = None
            while poll is None:
                poll = p.poll()
                await asyncio.sleep(0.2)
        else:
            symlink(from_file, to_file)
    return to_file


def is_need_ffmpeg(from_file, Range='', fps_times=5):
    kw: dict[str, Any] = {}
    metadata = ffprobe(from_file)
    from_fps = Fraction(metadata['streams'][0]['r_frame_rate'])
    to_fps = round(from_fps.numerator / from_fps.denominator / fps_times) * fps_times
    from_fps = from_fps.numerator / from_fps.denominator
    if Range:
        is_ffmpeg = True
        r = [r.total_seconds() for r in range_time(Range)]
        kw.update({'ss': r[0], 't': r[1]})
    if is_diff_fps := from_fps != to_fps:
        is_ffmpeg = True
        kw.update({'r': to_fps})
    if not Range and not is_diff_fps:
        is_ffmpeg = is_vbr(metadata)
    return kw, is_ffmpeg

# background_workers.pyi — Typing and Interface Stub for background_workers
from __future__ import annotations
from __future__ import annotations
import hashlib
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
from math import gcd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal
from core_utils import get_app_data_dir, safe_replace, ffmpeg_path, ffprobe_path
from bootstrap import setup_windows_dll_directories
from process_lifecycle import register_process, unregister_process
from timeline_widgets import WaveformEnvelope, build_waveform_pyramid

class StoryAutoDetectWorker(QObject):
    finished = ...
    progress = ...
    error = ...
    MUSIC_TOKEN_RE = ...

    def __init__(self, audio_file, silence_threshold=..., lead_in_padding=..., audio_duration=..., transcript_segments=..., whisper_model=..., detection_mode=..., **kwargs):
        ...

    def cancel(self):
        ...

    def _emit_progress(self, message: str, percent: int=...):
        ...

    def _is_real_speech(self, text: str) -> bool:
        ...

    def run(self):
        ...

def get_waveform_peak_cache_path(audio_file, project_file=...):
    ...
from timeline_widgets import WaveformEnvelope, build_waveform_pyramid

def read_waveform_peak_cache(audio_file, points_per_second=..., project_file=...):
    ...

def write_waveform_peak_cache(audio_file, peaks, points_per_second=..., project_file=..., levels=...):
    ...

def invalidate_waveform_peak_cache(audio_file, project_file=...):
    ...

class WaveformWorker(QObject):
    finished = ...

    def __init__(self, audio_file, points_per_second=..., project_file=...):
        ...

    def cancel(self):
        ...

    def run(self):
        ...

def get_video_thumbnail_cache_dir(media_file: str | Path | None, project_file: str | Path | None=...) -> Path | None:
    ...

def read_video_thumbnail_cache(media_file: str | Path | None, duration: float, project_file: str | Path | None=...) -> list | None:
    ...

def invalidate_video_thumbnail_cache(media_file: str | Path | None, project_file: str | Path | None=...) -> bool:
    ...

class VideoThumbnailWorker(QObject):
    finished = ...
    error = ...

    def __init__(self, media_path, duration, output_dir, count=...):
        ...

    def cancel(self):
        ...

    def run(self):
        ...
from timeline_widgets import TimelineCanvas, TimelineResizeHandle, TimelineOverviewBar, TimelineWidget

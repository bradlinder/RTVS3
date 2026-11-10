# core_utils.pyi — Typing and Interface Stub for core_utils
from __future__ import annotations
from __future__ import annotations
from typing import Any, NamedTuple, Optional
import hashlib
import math
import os
import re
import shutil
import sys
import time
from pathlib import Path
import os, sys
from qt_compat import _ensure_pyside6_fallback

def safe_process_events():
    ...

def get_active_theme_mode(default: str=...) -> str:
    ...

def _apply_dwm_titlebar_hwnd(hwnd: int, theme_mode: str) -> None:
    ...

def apply_window_titlebar_theme(widget, theme_mode: Optional[str]=...) -> None:
    ...

def _deferred_titlebar_theme(widget, theme_mode: str) -> None:
    ...

def make_dialog_maximizable(dialog) -> None:
    ...

def extract_dropped_file_paths(mime_data) -> List[str]:
    ...

def _ensure_runtime_bin_on_path():
    ...

def compute_file_sha256(file_path: str | Path, chunk_size: int=...) -> str:
    ...

def verify_file_sha256(file_path: str | Path, expected_sha256: str) -> bool:
    ...

def safe_extract_zip(zip_source, dest_dir) -> None:
    ...

def safe_extract_tar(tar_source, dest_dir) -> None:
    ...

def safe_replace(src: str | Path, dest: str | Path) -> None:
    ...

def get_github_repo() -> str:
    ...

def get_update_channel() -> str:
    ...

def get_app_data_dir() -> Path:
    ...

def get_models_storage_dir() -> Path:
    ...

def set_models_storage_dir(new_path=...) -> Path:
    ...

def get_bundled_runtime_dir() -> Path:
    ...

def find_bundled_executable(name: str) -> str | None:
    ...

def ffmpeg_path() -> str | None:
    ...

def ffprobe_path() -> str | None:
    ...

def format_byte_size(num_bytes: int | float) -> str:
    ...

def format_time(seconds, include_millis=...):
    ...

def format_clock_duration(seconds: float, include_millis: bool=...) -> str:
    ...

def parse_time(value):
    ...

def safe_filename(text):
    ...

def is_sentence_end(text):
    ...

def calculate_fade_curve_factor(u: float, fcurve: str=...) -> float:
    ...

def calculate_fade_out_factor(u: float, fcurve: str=...) -> float:
    ...

class StoryVocabulary(NamedTuple):
    mode: str
    singular: str
    plural: str
    singular_lower: str
    plural_lower: str
    add_label: str
    set_start: str
    set_end: str
    metadata_btn: str
    settings_btn: str
    detect_action: str
    panel_title: str
    is_es: bool

def get_story_vocabulary(win_or_settings: Any=..., language: Optional[str]=...) -> StoryVocabulary:
    ...

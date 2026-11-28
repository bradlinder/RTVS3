# cache_manager.pyi — Typing and Interface Stub for cache_manager
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from core_utils import get_app_data_dir, format_byte_size
_ACTIVE_THUMBNAIL_DIRS: set[str] = ...

def register_active_thumbnail_dir(path: Path | str | None) -> None:
    ...

def unregister_active_thumbnail_dir(path: Path | str | None) -> None:
    ...

def get_active_thumbnail_dirs() -> set[str]:
    ...

def cleanup_old_thumbnail_cache(max_age_hours: int=..., active_dir: Path | str | None=..., exclude_dirs: list | set | None=..., blocking: bool=..., base_dir: Path | str | None=...) -> threading.Thread | None:
    ...

def collect_settings_project_dirs() -> list:
    ...

def get_cache_disk_usage(project_dirs=..., include_global_caches: bool=..., include_settings_dirs: bool=..., cancel_check=...) -> dict:
    ...

def purge_caches(clear_thumbnails=..., clear_waveforms=..., clear_audio_extracts=..., project_dirs=..., include_global_caches: bool=..., cancel_check=...) -> tuple[int, int]:
    ...

class ClearCacheDialog(QDialog):

    def __init__(self, parent=..., language=..., project_dirs=..., auto_refresh=..., include_global_caches: bool=..., include_settings_dirs: bool=...):
        ...

    def _init_ui(self):
        ...

    def _build_scan_dirs(self) -> list:
        ...

    def _set_busy_state(self, busy: bool, status_text: str | None=..., is_error: bool=...):
        ...

    def _apply_stats(self, stats: dict):
        ...

    def _start_worker(self, worker):
        ...

    def refresh_stats(self):
        ...

    def _on_scan_finished(self, stats: dict, gen: int):
        ...

    def _on_purge_finished(self, files_deleted: int, bytes_freed: int, stats: dict, gen: int):
        ...

    def _on_worker_error(self, error_msg: str, gen: int):
        ...

    def _cleanup_workers(self):
        ...

    def accept(self):
        ...

    def reject(self):
        ...

    def closeEvent(self, event):
        ...

    def _on_clear_all(self):
        ...

    def _on_clear_selected(self):
        ...

    def _do_purge(self, clear_thumbs: bool, clear_waves: bool, clear_audio: bool):
        ...

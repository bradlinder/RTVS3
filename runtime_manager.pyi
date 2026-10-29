# runtime_manager.pyi — Typing and Interface Stub for runtime_manager
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import sys
import os
import json
import shutil
import logging
import subprocess
import time
import re
import queue
import threading
from pathlib import Path

def register_process(proc: subprocess.Popen):
    ...

def unregister_process(proc: subprocess.Popen):
    ...

def kill_all_subprocesses():
    ...

def _robust_urlretrieve(url: str, destination: Path, timeout: float=...) -> None:
    ...

def _emit_progress(progress_cb, percent: float, message: str):
    ...

def _run_pip_with_progress(cmd: list[str], feature_name: str, packages: list[str], progress_cb=..., env=..., creationflags=..., start_pct: float=..., end_pct: float=..., cancel_event: threading.Event=...) -> tuple[bool, str]:
    ...

def detect_nvidia_gpu() -> bool:
    ...

def _remove_macos_quarantine(target_path: Path | str) -> None:
    ...

class RuntimeManager:

    def __init__(self, base_dir: Path=...):
        ...

    def get_last_error(self) -> str:
        ...

    def get_env_dir(self, feature_name: str) -> Path:
        ...

    def get_manifest_path(self, feature_name: str) -> Path:
        ...

    def _get_raw_executable(self, feature_name: str) -> Path:
        ...

    def get_executable(self, feature_name: str) -> str:
        ...

    def resolve_target_python(self, target_version: str=...) -> str:
        ...

    def bundled_uv_path(self) -> Path | None:
        ...

    def ensure_uv(self, progress_cb=...) -> Path | None:
        ...

    def _get_uv_env(self) -> dict:
        ...

    def _find_extracted_python(self, target_version: str=...) -> str:
        ...

    def _download_standalone_python(self, target_version: str=..., progress_cb=...) -> str:
        ...

    def ensure_managed_python(self, target_version: str=..., progress_cb=...) -> str:
        ...

    def kill_all_subprocesses(self):
        ...

    def remove_environment(self, feature_name: str) -> bool:
        ...

    @staticmethod
    def prune_cuda_artifacts(env_dir: Path) -> int:
        ...

    def get_runtime_executable(self, feature_name: str, progress_cb=...) -> str:
        ...

    def get_plugin_requirements(self, feature_name: str, plugin_dir: Path=...) -> list:
        ...

    def is_env_up_to_date(self, feature_name: str) -> bool:
        ...

    def write_manifest(self, feature_name: str, python_used: str, packages: list=...):
        ...

    def ensure_environment(self, feature_name: str, force_rebuild: bool=..., progress_cb=..., plugin_dir: Path=..., cancel_event: threading.Event=...) -> bool:
        ...

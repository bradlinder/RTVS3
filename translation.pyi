# translation.pyi — Typing and Interface Stub for translation
from __future__ import annotations
from __future__ import annotations
import sys
import copy
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from prs_shared import format_time, register_process, unregister_process

def _translation_worker_class():
    ...
from PySide6.QtCore import QObject, Qt, QThread, QTimer, QProcess, QProcessEnvironment, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

class TranslationEnvSetupWorker(QObject):
    progress = ...
    finished = ...

    def __init__(self, plugin_dir: Path | None=..., runtime_mgr=...):
        ...

    def cancel(self):
        ...

    def run(self):
        ...

def _translation_runtime_entry_path(app=...) -> Path:
    ...

def _translation_runtime_manager(app=...):
    ...

class TranslationMixin:

    def source_language_code(self) -> str:
        ...

    def target_language_code(self) -> str:
        ...

    def translation_key(self, from_code: str=..., to_code: str=...) -> str:
        ...

    def get_translation_item(self, from_code: str, to_code: str) -> dict | None:
        ...

    def translation_export_spec(self, options: dict | None=...):
        ...

    def translation_is_current(self, key: str | None=...) -> bool:
        ...

    def has_spanish_translation(self) -> bool:
        ...

    def get_spanish_translation_item(self) -> dict | None:
        ...

    def mark_stale_translations(self):
        ...

    def update_translation_language_selector(self):
        ...

    def change_translation_display(self, mode: str | int | None=...):
        ...

    def render_translation_view(self):
        ...

    def check_translation_models_async(self):
        ...

    def _cleanup_translation_env_thread(self):
        ...

    def _on_translation_env_progress(self, percent_or_msg, message: str=...):
        ...

    def stop_translation_worker(self, timeout_ms: int=...) -> bool:
        ...

    def _start_translation_runtime_request(self, request: dict, on_finished=...) -> bool:
        ...

    def _on_translation_env_setup_finished(self, error):
        ...

    def _launch_translation_process(self, request: dict, on_finished, python_exe: str, entry: Path) -> bool:
        ...

    def start_translation(self, from_code: str=..., to_code: str=..., install_if_missing: bool=...):
        ...

    def _on_translation_progress(self, percent: float, message: str):
        ...

    def _on_translation_finished(self, translated_transcript: Any, translation_key: str):
        ...

    def _on_translation_cancelled(self, results: Any, translation_key: str):
        ...

    def _on_translation_error(self, error_message: str):
        ...

    def _on_translation_thread_finished(self):
        ...

    def _translation_thread_finished(self):
        ...

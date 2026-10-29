# model_management.pyi — Typing and Interface Stub for model_management
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget
from prs_shared import *
from bootstrap import NullWriter, init_null_streams_and_hf_env

class _DummyTranslationWorker:

    @classmethod
    def model_root(cls, variant=...):
        ...

    @classmethod
    def model_dir(cls, from_code, to_code, variant=...):
        ...

    @classmethod
    def model_is_installed(cls, from_code, to_code, variant=...):
        ...

def _translation_worker_class():
    ...

def _translation_plugin_installed(self) -> bool:
    ...
from model_install_workers import WhisperModelInstallWorker, DiarizationModelInstallWorker, get_diarization_model_dir, is_diarization_model_available

class ModelManagementMixin:

    def model_cache_candidates(self, model_name):
        ...

    def model_cache_path(self, model_name):
        ...

    def is_whisper_model_available(self, model_name):
        ...

    def refresh_whisper_model_chooser(self):
        ...

    def current_whisper_model(self):
        ...

    def update_whisper_model_tooltip(self):
        ...

    def set_whisper_model_from_ui(self, index):
        ...

    def translation_model_display_name(self, variant=...):
        ...

    def translation_model_root(self, variant=...):
        ...

    def refresh_translation_model_chooser(self):
        ...

    def set_translation_model_from_ui(self, index):
        ...

    def prompt_translation_model(self):
        ...

    def open_model_cleanup_dialog(self):
        ...

    def purge_all_data_action(self, parent_widget=..., on_complete=...):
        ...

    def open_translation_model_manager(self):
        ...

    def install_whisper_model_for_manager(self, model_name, dialog):
        ...

    def cancel_model_installation(self):
        ...

    def _on_model_install_progress(self, percent: int, message: str):
        ...

    def _install_whisper_model_background(self, model_name):
        ...

    def _model_install_finished(self, error):
        ...

    def _model_install_thread_finished(self):
        ...

    def _poll_model_install(self, dialog):
        ...

    def install_diarization_model_for_manager(self, dialog):
        ...

    def install_translation_models_for_manager(self, from_code, to_code, variant, dialog):
        ...

    def _translation_manager_install_finished(self, from_code, to_code, variant, dialog):
        ...

    def _translation_manager_install_error(self, message, dialog):
        ...

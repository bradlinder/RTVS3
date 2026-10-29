# project_lifecycle.pyi — Typing and Interface Stub for project_lifecycle
from __future__ import annotations
from __future__ import annotations
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import QDir, QTime, QUrl, Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout
from prs_shared import PROJECT_VERSION, cleanup_old_thumbnail_cache, read_rtvs_project_file, safe_filename, write_rtvs_project_file, write_waveform_peak_cache, make_dialog_maximizable, ProjectMetadataDict
from transcript_story import Story

class ProjectLifecycleMixin:

    def close_project(self, prompt=...):
        ...

    def new_project(self):
        ...

    def project_audio_reference(self):
        ...

    def project_data(self) -> Dict[str, Any]:
        ...

    def _write_project_file(self, file_path: str):
        ...

    def prepare_export_directories(self, target_base_dir=..., default_name=..., prompt_user=...):
        ...

    def get_default_save_directory(self) -> str:
        ...

    def validate_project_data(self, data: Dict[str, Any]) -> List[str]:
        ...

    def save_project_as(self) -> bool:
        ...

    def save_project(self, force=...):
        ...

    def open_backup_restore_dialog(self):
        ...

    def load_project_file(self, filename, prompt=..., preserve_media=...):
        ...

    def load_project(self, filename=...):
        ...

    def open_purge_project_data_dialog(self):
        ...

    def purge_project_data(self, purge_transcript: bool=..., purge_translations: bool=..., purge_speakers: bool=..., purge_stories: bool=..., purge_media: bool=...) -> bool:
        ...

class ProjectDataPurgeDialog(QDialog):

    def __init__(self, parent=..., is_es=...):
        ...

    def _init_ui(self):
        ...

    def _set_all_checked(self, checked: bool):
        ...

    def _update_purge_button_state(self):
        ...

    def get_purge_options(self) -> dict[str, bool]:
        ...

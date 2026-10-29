# playback_preferences.pyi — Typing and Interface Stub for playback_preferences
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
import warnings
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTime, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QInputDialog, QMessageBox, QPushButton, QVBoxLayout, QWidget, QComboBox, QDoubleSpinBox
from prs_shared import INTERNAL_APP_ID, PROJECT_VERSION, APP_DISPLAY_NAME, get_app_data_dir, get_app_icon, get_github_repo, get_license_file_path, safe_replace
from theme_preferences import ThemePreferencesMixin
from playback_controller import PlaybackControllerMixin
from preferences_reset import RestoreSelectedSettingsDialog, PreferencesResetMixin
from preferences_dialog import PreferencesDialogMixin
from project_state_mixin import ProjectStateMixin

class PlaybackPreferencesMixin(ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, ProjectStateMixin):

    def _install_diagnostic_logging(self):
        ...

    def export_activity_log(self):
        ...

    def log_activity(self, action_text, mark_dirty=...):
        ...

    def handle_activity_click(self, item):
        ...

    def restore_snapshot(self, index):
        ...

    def clear_activity_log(self):
        ...

    def trigger_find_next(self):
        ...

    def trigger_find_prev(self):
        ...

    def open_diagnostic_log_folder(self):
        ...

    def show_about_dialog(self):
        ...

    def check_for_updates(self, interactive: bool=...):
        ...

    def trigger_silent_update_check(self):
        ...

    def apply_audio_output_device(self, device_name=..., volume=...):
        ...

    def show_licenses_dialog(self):
        ...

    def on_expected_speakers_changed(self, value):
        ...

    def on_diarization_sensitivity_changed(self, value):
        ...

    def update_auto_save_timer(self):
        ...

    def prompt_set_whisper_model(self):
        ...

    def prompt_set_skip_seconds(self):
        ...

    def prompt_set_auto_detect_thresholds(self):
        ...

    def prompt_set_auto_save(self):
        ...

    def trigger_auto_save(self):
        ...

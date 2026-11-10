# preferences_dialog.pyi — Typing and Interface Stub for preferences_dialog
from __future__ import annotations
import logging
from typing import Optional
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QPushButton, QDialogButtonBox, QMessageBox, QLabel, QLineEdit, QWidget, QComboBox, QTableWidget
from prs_shared import APP_DISPLAY_NAME, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, set_models_storage_dir
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from preferences_reset import RestoreSelectedSettingsDialog, PreferencesResetMixin
from preferences_tabs_core import build_general_tab, build_shortcuts_tab, build_audio_hardware_tab, build_updates_tab, build_ai_models_tab, build_gpu_tab
from preferences_tabs_media import build_playback_timeline_tab, build_detection_tab, build_batch_tab, build_cleanup_tab, build_youtube_tab
from preferences_tab_daw import build_external_editors_tab

class PreferencesDialogMixin(PreferencesResetMixin):

    def open_preferences_dialog(self, initial_category=..., modal=...):
        ...

# preferences_tabs_media.pyi — Typing and Interface Stub for preferences_tabs_media
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import logging
from pathlib import Path
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton, QFileDialog, QMessageBox
from prs_shared import INTERNAL_APP_ID, FadeCurveVisualSelector
from preferences_reset import RestoreSelectedSettingsDialog

def build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    ...

def build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    ...

def build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    ...

def build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    ...

def build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    ...

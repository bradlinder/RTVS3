# plugin.pyi — Typing and Interface Stub for plugin
from __future__ import annotations
from __future__ import annotations
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QGroupBox, QFormLayout, QComboBox, QScrollArea, QTextEdit, QFileDialog, QRadioButton, QButtonGroup, QCheckBox, QProgressBar, QWidget, QSlider, QFrame
from prs_shared import INTERNAL_APP_ID, PROJECT_VERSION, QSettings, CollapsibleSection, ffmpeg_path, format_time, safe_filename
from plugins.base import BasePlugin, PluginManifest
from plugins.wordpress.client import WordPressClient, _get_wp_password, _set_wp_password, generate_wp_excerpt, WordPressSettingsDialog, execute_wordpress_upload

def capture_video_frame(video_path: str, timestamp: float, output_path: str, timeout: float=...) -> bool:
    ...

class WordPressPublishDialog(QDialog):

    def __init__(self, plugin: Plugin, parent: Any=..., story: Any=...):
        ...

    def setup_ui(self):
        ...

    def load_custom_text_settings(self):
        ...

    def save_custom_text_defaults(self):
        ...

    def load_metadata(self):
        ...

    def do_capture_frame(self):
        ...

    def on_image_mode_changed(self):
        ...

    def on_browse_image(self):
        ...

    def on_configure_credentials(self):
        ...

    def on_publish(self):
        ...

    def on_publish_finished(self, success: bool, msg: str, post_data: Any):
        ...

    def closeEvent(self, event):
        ...

class WordPressPublishWorker(QThread):
    finished_signal = ...

    def __init__(self, client: WordPressClient, title: str, content: str, excerpt: str, status: str, image_path: Optional[str]):
        ...

    def run(self):
        ...

class WordPressStoryMetadataWidget(QGroupBox):

    def __init__(self, plugin: Any, parent: Any=...):
        ...

    def setup_ui(self):
        ...

    def refresh_targets_dropdown(self):
        ...

    def _on_target_changed(self, index: int):
        ...

    def set_story(self, story: Any):
        ...

    def _get_active_wp_metadata(self) -> dict:
        ...

    def _load_current_target_metadata(self):
        ...

    def _open_post_settings_dialog(self):
        ...

    def _on_refresh_taxonomy(self):
        ...

class Plugin(BasePlugin):

    def __init__(self, manifest: PluginManifest, app: Any=...):
        ...

    def on_load(self) -> bool:
        ...

    def get_export_destinations(self) -> List[Any]:
        ...

    def get_export_actions(self) -> List[tuple[str, Callable]]:
        ...

    def get_story_actions(self, story: Any=...) -> List[tuple[str, Callable]]:
        ...

    def create_story_metadata_widget(self, parent: Any=...) -> Any:
        ...

    def on_story_selected(self, story: Any=...) -> None:
        ...

    def get_preferences_widget(self, parent: Any=...) -> Any:
        ...

    def open_publish_dialog(self, parent: Any=..., story: Any=...):
        ...

    def open_post_metadata_dialog(self, parent: Any=..., story: Any=...):
        ...

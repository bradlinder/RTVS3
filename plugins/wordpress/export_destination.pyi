# export_destination.pyi — Typing and Interface Stub for export_destination
from __future__ import annotations
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialog, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget
from prs_shared import INTERNAL_APP_ID, safe_filename, safe_process_events
from plugins.base import ExportDestination
from plugins.wordpress.client import WordPressClient, WordPressSettingsDialog, execute_wordpress_upload, _get_wp_password, build_episode_stories_toc, format_parent_episode_notice, is_wp_auth_error
from plugins.wordpress.authors import expand_legacy_author_term_ids
from plugins.wordpress.wp_post_builder import capture_video_frame, build_wp_post_items
from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget

class WordPressExportDestination(ExportDestination):

    def __init__(self, plugin: Any=...):
        ...

    @property
    def button_label(self) -> str:
        ...

    @button_label.setter
    def button_label(self, val: Any) -> None:
        ...

    def get_export_button_label(self) -> str:
        ...

    @property
    def widget(self) -> Any:
        ...

    @widget.setter
    def widget(self, val: Any) -> None:
        ...

    def create_widget(self, parent: Any, main_window: Any) -> Any:
        ...

    def _ensure_tab_widget(self) -> Optional[WordPressExportTabWidget]:
        ...

    def on_scope_changed(self, scope: str, stories: list) -> None:
        ...

    def validate(self) -> Tuple[bool, str]:
        ...

    def get_export_data(self) -> Dict[str, Any]:
        ...

    def execute_export(self, main_window: Any, export_data: Dict[str, Any], progress_dialog: Any=...) -> bool:
        ...

class WordPressPostMetadataDialog(QDialog):

    def __init__(self, parent: Optional[QWidget], main_window: Any, target_story_index: Optional[int]=...):
        ...

    def _on_save_clicked(self):
        ...

    def _on_close_clicked(self):
        ...

    def _on_save_and_close(self):
        ...

    def done(self, r: int):
        ...
from plugins.wordpress.castos import SS_PODCAST_AUDIO_FILE, SS_PODCAST_AUDIO_FILE_ID, SS_PODCAST_DURATION, SS_PODCAST_FILESIZE, SS_PODCAST_FEED, SS_PODCAST_EPISODE_TYPE, CASTOS_SHORTCODE, CASTOS_PLAYER_BLOCK, build_castos_post_meta, format_castos_duration, fetch_castos_feeds

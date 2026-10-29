# wordpress_dialog.pyi — Typing and Interface Stub for wordpress_dialog
from __future__ import annotations
from __future__ import annotations
import html
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt, QTimer, QSettings, QRectF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QRadioButton, QScrollArea, QSlider, QVBoxLayout, QWidget
from prs_shared import INTERNAL_APP_ID, CollapsibleSection, ResizableTextEdit, ffmpeg_path, format_time, safe_filename
from plugins.wordpress.client import WordPressClient, generate_wp_excerpt as _client_generate_wp_excerpt, format_rich_text_to_html, format_parent_episode_notice, build_episode_stories_toc, WordPressSettingsDialog, execute_wordpress_upload, _get_wp_password

def generate_wp_excerpt(transcript_words, start_t, end_t):
    ...

def capture_video_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    ...

class WordPressExportTabWidget(QWidget):

    def __init__(self, parent: QWidget, main_window: Any, metadata_editor_mode: bool=...):
        ...

    def _setup_ui(self):
        ...

    def update_wp_pres_visibility(self):
        ...

    def _update_wp_conn_status(self):
        ...

    def _open_wp_settings(self):
        ...

    def _filter_authors_list(self, text: str):
        ...

    def _filter_categories_list(self, text: str):
        ...

    def _on_title_edited(self, text: str):
        ...

    def _on_excerpt_edited(self):
        ...

    def _auto_generate_current_excerpt(self):
        ...

    def _autofill_all_excerpts(self):
        ...

    def _on_author_item_changed(self, item):
        ...

    def _on_category_item_changed(self, item):
        ...

    def _clear_current_authors(self):
        ...

    def _clear_current_categories(self):
        ...

    def _get_selected_story_indices(self) -> List[int]:
        ...

    def _apply_authors_to_selected_stories(self):
        ...

    def _apply_categories_to_selected_stories(self):
        ...

    def _apply_thumbnails_to_selected_stories(self):
        ...

    def _apply_authors_to_all_posts(self):
        ...

    def _apply_categories_to_all_posts(self):
        ...

    def _apply_thumbnails_to_all_posts(self):
        ...

    def _sync_post_to_project(self, idx: int):
        ...

    def save_all_posts_to_project(self):
        ...

    def _update_post_list_item_label(self, idx: int):
        ...

    def _on_wp_post_selection_changed(self, row: int):
        ...

    def _get_editor_checked_authors(self) -> Tuple[List[int], List[int]]:
        ...

    def _set_editor_checked_authors(self, author_ids: List[int], author_term_ids: List[int]):
        ...

    def _get_editor_checked_categories(self) -> List[int]:
        ...

    def _set_editor_checked_categories(self, cat_ids: List[int]):
        ...

    def _get_wp_post_bounds(self, post_index=...) -> Tuple[float, float]:
        ...

    def _sync_wp_slider_to_pos(self, pos: float):
        ...

    def _on_wp_slider_value_changed(self, val: int):
        ...

    def _on_wp_scrub_timer_timeout(self):
        ...

    def _on_wp_step(self, delta_secs: float):
        ...

    def _on_wp_sync_playhead(self):
        ...

    def _load_post_editor_state(self, index: int):
        ...

    def _on_wp_thumb_mode_changed(self):
        ...

    def _capture_wp_frame(self, pos=...):
        ...

    def _on_wp_browse_thumb(self):
        ...

    def rebuild_post_items(self, scope: Optional[str]=...):
        ...

    def _populate_wp_export_metadata(self, force_refresh: bool=...):
        ...

    def _refresh_wp_metadata(self):
        ...

class WordPressPostMetadataDialog(QDialog):

    def __init__(self, parent: Optional[QWidget], main_window: Any, target_story_index: Optional[int]=...):
        ...

    def _on_save_and_close(self):
        ...

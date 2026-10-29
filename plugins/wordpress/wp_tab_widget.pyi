# wp_tab_widget.pyi — Typing and Interface Stub for wp_tab_widget
from __future__ import annotations
from __future__ import annotations
import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QCheckBox, QFileDialog, QListWidgetItem, QMessageBox, QWidget
from prs_shared import INTERNAL_APP_ID, format_time, safe_filename
from plugins.wordpress.client import WordPressClient, WordPressSettingsDialog, generate_wp_excerpt, _get_wp_password, is_wp_auth_error
from plugins.wordpress.wp_post_builder import capture_video_frame, build_wp_post_items
from plugins.wordpress.wp_ui_builder import setup_wp_tab_ui

class WordPressExportTabWidget(QWidget):

    def __init__(self, parent: QWidget, main_window: Any, metadata_editor_mode: bool=...):
        ...

    def _setup_ui(self):
        ...

    def _on_wp_include_audio_toggled(self, checked: bool):
        ...

    def _update_wp_conn_status(self):
        ...

    def _open_wp_settings(self):
        ...

    def _filter_authors_list(self, text: str):
        ...

    def _filter_categories_list(self, text: str):
        ...

    def _sync_to_proj(self, idx: int):
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

    def _apply_podcast_to_selected_stories(self):
        ...

    def _apply_podcast_to_all_posts(self):
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

    def _cleanup_temp_files(self) -> None:
        ...

    def closeEvent(self, event: Any) -> None:
        ...

    def rebuild_post_items(self, scope: Optional[str]=...):
        ...

    def _populate_wp_export_metadata(self, force_refresh: bool=...):
        ...

    def _refresh_castos_feeds(self):
        ...

    def _refresh_wp_metadata(self):
        ...

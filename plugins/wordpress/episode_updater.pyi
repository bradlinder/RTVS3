# episode_updater.pyi — Typing and Interface Stub for episode_updater
from __future__ import annotations
from __future__ import annotations
import html
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QRadioButton, QVBoxLayout, QWidget
from prs_shared import INTERNAL_APP_ID, get_app_data_dir, safe_filename

def extract_slug_or_id_from_url(url_or_id: str) -> Tuple[Optional[int], str]:
    ...

def clean_html_to_plain_excerpt(raw_html: str) -> str:
    ...

def build_story_slug(title: str) -> str:
    ...

def normalize_wp_iso_date(date_str: Optional[str]) -> Optional[str]:
    ...

def format_wp_date_for_input(iso_date: Optional[str]) -> str:
    ...

def _extract_audio_url_from_post_payload(post: Dict[str, Any], html_fallback: str=...) -> str:
    ...

def _parse_wp_post_json(post: Dict[str, Any], client: Any=..., fallback_url: str=...) -> Dict[str, Any]:
    ...

def resolve_wp_post_from_url(client: Any, url_or_id: str) -> Dict[str, Any]:
    ...

def _resolve_download_dir(main_window: Any=..., target_dir: Optional[Path]=...) -> Path:
    ...

def download_wp_episode_audio(post_info: Dict[str, Any], main_window: Any=..., target_dir: Optional[Path]=...) -> Path:
    ...

def _refresh_dialog_export_button(tab_widget: Any) -> None:
    ...

def _is_update_mode(tab_widget: Any) -> bool:
    ...

def _get_current_tab_post(tab_widget: Any) -> Optional[Dict[str, Any]]:
    ...

def sync_wp_audio_checkbox_label(tab_widget: Any) -> None:
    ...

def _sync_mode_visibility(tab_widget: Any) -> None:
    ...

def load_episode_updater_from_post(tab_widget: Any, post: Dict[str, Any]) -> None:
    ...

def _update_existing_status_label(tab_widget: Any, post: Optional[Dict[str, Any]]) -> None:
    ...

def _copy_fetched_post_fields(target: Dict[str, Any], post_info: Dict[str, Any]) -> None:
    ...

def apply_fetched_post_to_tab(tab_widget: Any, post_info: Dict[str, Any], target_idx: Optional[int]=...) -> None:
    ...

def _populate_project_from_fetched_post(main_window: Any, post_info: Dict[str, Any]) -> None:
    ...

def _get_configured_client(parent_widget: QWidget) -> Any:
    ...

def setup_wp_mode_and_date_ui(tab_widget: Any, parent_section: Any) -> None:
    ...

class LoadWordPressEpisodeDialog(QDialog):

    def __init__(self, main_window: Any, parent: Optional[QWidget]=...):
        ...

    def _sync_local_row_enabled(self):
        ...

    def _on_browse_local(self):
        ...

    def _resolve_target(self, url: str) -> Dict[str, Any]:
        ...

    def _on_fetch_clicked(self):
        ...

    def _on_load_clicked(self):
        ...

def prompt_load_existing_wp_episode_dialog(main_window: Any, parent: Optional[QWidget]=...) -> bool:
    ...

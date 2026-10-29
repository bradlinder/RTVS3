# client.pyi — Typing and Interface Stub for client
from __future__ import annotations
from __future__ import annotations
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from prs_shared import INTERNAL_APP_ID, PROJECT_VERSION, QSettings, ffmpeg_path, format_time, safe_filename
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QRadioButton, QTextEdit, QVBoxLayout, QWidget

def _get_keyring():
    ...

def _get_wp_fallback_cipher():
    ...

def _get_wp_password(username: str) -> str:
    ...

def _set_wp_password(username: str, password: str) -> bool:
    ...

def format_rich_text_to_html(text: str | list, auto_link_urls: bool=..., main_window: Any=...) -> str:
    ...

def format_parent_episode_notice(episode_title: str, episode_url: str, template: str=...) -> str:
    ...

def build_episode_stories_toc(stories: list[dict]) -> str:
    ...

def generate_wp_excerpt(text: str, max_words: int=...) -> str:
    ...

def is_wp_auth_error(err: Any) -> bool:
    ...

class WordPressClient:

    def __init__(self, site_url: str, username: str, password: str):
        ...

    def is_configured(self) -> bool:
        ...

    def _get_auth(self):
        ...

    def _discover_canonical_base(self) -> None:
        ...

    def _is_safe_redirect(self, current_url: str, next_url: str) -> bool:
        ...

    def _get_request(self, url: str, params: dict | None=..., headers: dict | None=..., timeout: int=...) -> Any:
        ...

    def _post_request(self, url: str, json_data: dict | None=..., headers: dict | None=..., timeout: int=...) -> Any:
        ...

    def _post_multipart(self, url: str, path: Path, upload_filename: str, mime_type: str, timeout: int=...) -> Any:
        ...

    def test_connection(self) -> tuple[bool, str]:
        ...

    def get_categories(self) -> list[dict]:
        ...

    def get_authors(self) -> list[dict]:
        ...

    def upload_media(self, file_path: str, filename: str | None=...) -> dict:
        ...

    def get_podcast_feeds(self) -> list[dict]:
        ...

    def create_post(self, title: str, content: str, excerpt: str=..., status: str=..., category_ids: list[int] | None=..., author_ids: list[int] | None=..., author_term_ids: list[int] | None=..., featured_media_id: int | None=..., meta: dict[str, Any] | None=..., podcast_series: list[int] | None=...) -> dict:
        ...

    def update_post(self, post_id: int, content: str | None=..., title: str | None=..., excerpt: str | None=..., status: str | None=..., category_ids: list[int] | None=..., featured_media_id: int | None=..., meta: dict[str, Any] | None=..., podcast_series: list[int] | None=...) -> dict:
        ...

class WordPressSettingsDialog(QDialog):

    def __init__(self, parent=...):
        ...

    def _test_connection(self):
        ...

    def _save_settings(self):
        ...

def get_wp_client() -> WordPressClient | None:
    ...

class WordPressPreferencesPage(QWidget):

    def __init__(self, parent: Any=..., app: Any=...):
        ...

    def setup_ui(self):
        ...

    def _test_connection(self):
        ...

    def save_preferences(self, dialog=...):
        ...

def _group_segments_into_paragraphs(segments: list, min_words: int=...) -> list:
    ...

def _build_audio_fade_filter(duration: float, fade_in: float=..., fade_out: float=..., fade_curve: str=...) -> list[str]:
    ...

def execute_wordpress_upload(main_window: Any, client: WordPressClient, post_title: str=..., post_excerpt: str=..., start: float | None=..., end: float | None=..., task_label: str=..., include_english: bool=..., include_spanish: bool=..., spanish_presentation: str=..., primary_language: str=..., author_ids: list[int] | None=..., author_term_ids: list[int] | None=..., category_ids: list[int] | None=..., show_completion_dialog: bool=..., media_filename: str | None=..., progress_callback=..., featured_image_path: str | None=..., parent_episode_info: dict | None=..., link_parent_episode: bool=..., parent_episode_template: str=..., parent_episode_pos: str=..., include_audio: bool=..., fade_in: float=..., fade_out: float=..., fade_curve: str=..., apply_fades: bool=..., accordion_pos: str=..., is_podcast: bool=..., podcast_feed: str=..., podcast_feed_id: int | None=..., podcast_feed_ids: list[int] | None=..., podcast_feeds: list[str] | None=..., podcast_episode_type: str=..., podcast_season: str | int | None=..., podcast_episode_number: str | int | None=...) -> dict:
    ...

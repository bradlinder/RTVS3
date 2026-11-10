# user_guide_dialog.pyi — Typing and Interface Stub for user_guide_dialog
from __future__ import annotations
from __future__ import annotations
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QImageReader, QKeySequence, QTextCursor
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSplitter, QTextBrowser, QTextEdit, QVBoxLayout, QWidget
from embedded_guides import get_embedded_guide
from core_utils import apply_window_titlebar_theme, get_active_theme_mode, make_dialog_maximizable

class ResponsiveTextBrowser(QTextBrowser):

    def __init__(self, parent: Optional[QWidget]=...):
        ...

    def resizeEvent(self, event):
        ...

    def scale_images_to_viewport(self):
        ...

class UserGuideDialog(QDialog):
    GUIDE_CATALOG: List[Dict[str, str]] = ...

    @staticmethod
    def _find_docs_dir() -> Path:
        ...

    def __init__(self, parent: Optional[QWidget]=..., initial_guide_id: str=...):
        ...

    def _setup_ui(self):
        ...

    def _apply_browser_stylesheet(self):
        ...

    def _resolve_image_urls(self, markdown_text: str) -> str:
        ...

    def _load_guide_by_id(self, guide_id: str):
        ...

    def _on_topic_selected(self, row: int):
        ...

    def _focus_search(self):
        ...

    def _get_guide_raw_text(self, guide_id: str) -> str:
        ...

    def _update_cross_topic_badges(self, query: str) -> int:
        ...

    def _on_search_query_changed(self, text: str):
        ...

    def _execute_in_doc_search(self, query: str, other_matches_count: int=...):
        ...

    def _update_match_label(self):
        ...

    def _highlight_matches(self, scroll: bool=...):
        ...

    def _find_next_match(self):
        ...

    def _find_prev_match(self):
        ...

    def keyPressEvent(self, event):
        ...

    def _zoom_in(self):
        ...

    def _zoom_out(self):
        ...

    def _reset_zoom(self):
        ...

    def _open_in_external_browser(self):
        ...

    def _build_dynamic_shortcuts_guide(self) -> str:
        ...

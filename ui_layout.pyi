# ui_layout.pyi — Typing and Interface Stub for ui_layout
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QTimer, QSize
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QTextCursor, QShortcut
from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMenu, QMenuBar, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSplitter, QStatusBar, QTextEdit, QToolButton, QVBoxLayout, QWidget
from prs_shared import CommentsPanel, FindReplaceDialog, InteractiveTranscriptEdit, StoryListWidget, TimelineWidget, ffmpeg_path, ffprobe_path, format_time, platform_seq, safe_filename
from ui_menus import PersistentMenu, UiMenusMixin
from ui_dialog_launchers import UiDialogLaunchersMixin

class UiLayoutMixin(UiMenusMixin, UiDialogLaunchersMixin):

    def build_ui(self):
        ...

    def filter_transcript_search(self, target: str):
        ...

    def toggle_transcript_editing_mode(self, *args, **kwargs):
        ...

    def _on_transcript_editing_mode_changed(self, is_editing: bool):
        ...

    def _sync_format_toolbar_buttons(self):
        ...

    def _on_toolbar_split_speaker(self):
        ...

    def _apply_transcript_font_scale(self, scale, persist=...):
        ...

    def _on_font_size_combo_changed(self, index: int):
        ...

    def adjust_transcript_font_size(self, direction):
        ...

    def reset_transcript_font_size(self):
        ...

    def update_story_list_height(self):
        ...

    def auto_generate_selected_story_excerpt(self):
        ...

    def _on_story_excerpt_text_changed(self):
        ...

    def toggle_maximize_stories_panel(self):
        ...

    def setup_plugin_story_extensions(self):
        ...

    def notify_story_selection_to_plugins(self, selected_story=...):
        ...

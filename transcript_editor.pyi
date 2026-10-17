# transcript_editor.pyi — Typing and Interface Stub for Interactive Transcript Editor
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from PySide6.QtWidgets import QTextEdit, QWidget, QDialog
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent
from PySide6.QtCore import QMimeData

from transcript_editor_dialogs import FindReplaceDialog, TranscriptSelectionBubble
from transcript_styles import transcript_text_view_stylesheet, clean_dark_mode_clipboard_html
from transcript_context_menu_mixin import TranscriptContextMenuMixin
from transcript_formatting_mixin import TranscriptFormattingMixin
from transcript_timeline_sync_mixin import TranscriptTimelineSyncMixin

__all__ = [
    "FindReplaceDialog",
    "TranscriptSelectionBubble",
    "transcript_text_view_stylesheet",
    "clean_dark_mode_clipboard_html",
    "InteractiveTranscriptEdit",
]

class InteractiveTranscriptEdit(TranscriptContextMenuMixin, TranscriptFormattingMixin, TranscriptTimelineSyncMixin, QTextEdit):
    def __init__(self, parent: Optional[QWidget] = ...) -> None: ...
    def lock_scroll_position(self, v_val: Optional[int] = ..., h_val: Optional[int] = ..., duration_ms: int = ...) -> None: ...
    def apply_theme_style(self, mode: Optional[str] = ...) -> None: ...
    def set_font_scale(self, scale: float) -> None: ...
    def set_editing_mode(self, enabled: bool) -> None: ...
    def createMimeDataFromSelection(self) -> QMimeData: ...

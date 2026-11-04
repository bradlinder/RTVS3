# playback_controller.pyi — Typing and Interface Stub for playback_controller
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox, QWidget
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from prs_shared import format_time, calculate_fade_curve_factor, calculate_fade_out_factor, InteractiveTranscriptEdit
from core_utils import apply_window_titlebar_theme, make_dialog_maximizable

class PlaybackControllerMixin:

    def is_video_file(self, path):
        ...

    def _ensure_video_preview_dialog(self):
        ...

    def update_video_preview_state(self):
        ...

    def toggle_video_preview(self, checked=...):
        ...

    def handle_scrub_position(self, seconds):
        ...

    def execute_scrub_seek(self):
        ...

    def eventFilter(self, watched, event):
        ...

    def _is_text_entry_focused(self) -> bool:
        ...

    def _matches_shortcut(self, event, action_id: str, default_seq: str) -> bool:
        ...

    def _toggle_follow_playhead(self):
        ...

    def mark_story_start_point(self):
        ...

    def mark_story_end_point(self):
        ...

    def get_segment_index_at_time(self, target_time: float):
        ...

    def split_current_segment_at_playhead(self):
        ...

    def merge_current_segment_with_next(self):
        ...

    def set_skip_seconds_from_ui(self, value):
        ...

    def set_playback_rate(self, rate: float):
        ...

    def toggle_play(self):
        ...

    def stop_audio(self):
        ...

    def seek_to(self, seconds):
        ...

    def seek_relative(self, delta_seconds):
        ...

    def audio_position_changed(self, position):
        ...

    def get_fade_volume_factor_at_time(self, t: float) -> float:
        ...

    def update_realtime_fade_volume(self):
        ...

    def _on_fade_timer_tick(self):
        ...

    def audio_duration_changed(self, duration):
        ...

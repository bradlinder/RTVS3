# speaker_dialogs.pyi — Typing and Interface Stub for speaker_dialogs
from __future__ import annotations
from __future__ import annotations
import html
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple
from PySide6.QtCore import Qt, QTimer, QSettings, QUrl, QEvent
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox, QFrame, QLineEdit, QInputDialog, QApplication, QStyledItemDelegate, QAbstractItemDelegate
from prs_shared import format_time, parse_time, INTERNAL_APP_ID
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from speaker_name_matcher import is_generic_speaker_label

class ChangeSpeakerDialog(QDialog):

    def __init__(self, current_name: str, target_name: str, seg_idx: int=..., parent=..., show_save_voice_profile: bool=..., already_saved_voice_profile: bool=...):
        ...

    def _on_all(self):
        ...

    def _on_subsequent(self):
        ...

    def _on_single(self):
        ...

    @property
    def save_to_station_voices(self) -> bool:
        ...

def _is_gui_thread() -> bool:
    ...

def _should_init_audio_preview() -> bool:
    ...

class SpeakerNameDelegate(QStyledItemDelegate):

    def __init__(self, dialog: SpeakerManagerDialog):
        ...

    def createEditor(self, parent, option, index):
        ...

    def eventFilter(self, editor, event):
        ...

class SpeakerManagerDialog(QDialog):

    def __init__(self, parent=...):
        ...

    def _is_gui_thread(self) -> bool:
        ...

    def _get_audio_source_url(self) -> Optional[QUrl]:
        ...

    def _get_sample_duration(self) -> float:
        ...

    def _find_speaker_sample_range(self, speaker_name: str) -> Optional[Tuple[float, float]]:
        ...

    def _play_speaker_sample(self, speaker_name: str):
        ...

    def _stop_sample_playback(self):
        ...

    def _on_preview_playback_state_changed(self, state):
        ...

    def _on_preview_media_status_changed(self, status):
        ...

    def _init_ui(self):
        ...

    def _schedule_debounced_save(self):
        ...

    def _flush_debounced_save(self):
        ...

    def _populate(self):
        ...

    def _start_inline_edit_on_row(self, row: int):
        ...

    def _on_table_item_changed(self, item: QTableWidgetItem):
        ...

    def _rename_speaker(self, current_name, raw_id):
        ...

    def _apply_speaker_rename(self, current_name: str, target: str, raw_id: Any):
        ...

    def _merge_speaker_into(self, source_name):
        ...

    def _on_quick_merge(self):
        ...

    def _on_toggle_station_voice(self, speaker_name: str, checked: bool, checkbox: QCheckBox):
        ...

    def _on_fix_speaker_names(self):
        ...

    def _on_open_voice_profiles(self):
        ...

    def reject(self):
        ...

    def accept(self):
        ...

    def closeEvent(self, event):
        ...

    def toggle_float_mode(self, pinned: Optional[bool]=...):
        ...

    def changeEvent(self, event):
        ...

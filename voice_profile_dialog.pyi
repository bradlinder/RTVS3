# voice_profile_dialog.pyi — Typing and Interface Stub for voice_profile_dialog
from __future__ import annotations
from __future__ import annotations
import html
import re
from typing import List, Optional, Tuple
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup, QSlider, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox, QFrame, QLineEdit, QInputDialog, QListWidgetItem, QDoubleSpinBox, QFormLayout, QProgressDialog, QApplication
from prs_shared import format_time, parse_time, INTERNAL_APP_ID
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from speaker_identity import cosine_similarity, robust_reference_profile, compare_against_profiles, is_confident_match

class VoiceProfileMatchDialog(QDialog):

    def __init__(self, ref_seg_idx: int, current_speaker: str, target_speaker: str=..., prompt_new_speaker: bool=..., ref_seg_indices: Optional[List[int]]=..., parent=...):
        ...

    def _on_playback_state_changed(self, state):
        ...

    def _toggle_hints(self):
        ...

    def _on_slider_changed(self, val):
        ...

    def get_active_ref_indices(self) -> List[int]:
        ...

    def _on_controls_changed(self):
        ...

    def _update_matches(self):
        ...

    def _select_all_matches(self):
        ...

    def _deselect_all_matches(self):
        ...

    def _toggle_master_checkbox(self, checked: bool):
        ...

    def _on_table_item_changed(self, item):
        ...

    def _get_selected_segment_indices(self) -> List[int]:
        ...

    def _update_action_summary(self):
        ...

    def _on_apply(self):
        ...

    def reject(self):
        ...

    def _seek_to_time(self, seconds: float):
        ...

    def _is_playing(self) -> bool:
        ...

    def _stop_playback(self):
        ...

    def _toggle_playback(self):
        ...

    def _toggle_audition_button(self):
        ...

    def _on_table_selection_changed(self):
        ...

    def _on_table_cell_double_clicked(self, row, col):
        ...

    def eventFilter(self, watched, event):
        ...

    def keyPressEvent(self, event):
        ...

# transcript_story.pyi — Typing and Interface Stub for transcript_story
from __future__ import annotations
from typing import List, Optional, Tuple
import html
import re
from prs_shared import *
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup, QSlider, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox, QFrame, QLineEdit, QInputDialog, QListWidgetItem, QDoubleSpinBox, QFormLayout, QProgressDialog, QApplication
from PySide6.QtCore import Qt, QTimer, QSettings, QObject
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor
from speaker_identity import cosine_similarity, robust_reference_profile, compare_against_profiles, is_confident_match, centroid
from speaker_palette import SpeakerColorAssigner
from voice_profile_dialog import VoiceProfileMatchDialog
from speaker_dialogs import ChangeSpeakerDialog, SpeakerManagerDialog
from story_fades_dialog import StoryFadesDialog
from story_model import Story, SetStoriesCommand, SelectStoriesCommand, StoryBoundaryChangeCommand, FADE_CURVE_TABLES, get_fade_curve_factors
from story_crud_mixin import StoryCrudMixin
from speaker_editing_mixin import SpeakerEditingMixin
from voice_profile_ops_mixin import VoiceProfileOpsMixin

class TranscriptStoryMixin(StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin):

    def render_transcript(self):
        ...

    def on_transcript_selection_changed(self):
        ...

    def on_transcript_text_changed(self):
        ...

    def transcript_clicked(self, url):
        ...

    def edit_segment_comment_dialog(self, seg_idx: int, sel_text: str=..., start_char: Optional[int]=..., end_char: Optional[int]=..., t_range: Optional[tuple[float, float]]=..., covered_indices: Optional[List[int]]=...):
        ...
    edit_segment_note_dialog = ...

    def add_comment_from_selection(self):
        ...

    def delete_segment_comment(self, seg_idx):
        ...

    def toggle_comments_panel(self):
        ...

    def toggle_show_comments(self, checked):
        ...
    toggle_show_notes = ...

    def toggle_comment_highlights(self, checked):
        ...

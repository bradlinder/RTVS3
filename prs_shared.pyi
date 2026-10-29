# prs_shared.pyi — Typing and Interface Stub for prs_shared
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import logging
import html
from bisect import bisect_left, bisect_right
import copy
import gzip
import io
import hashlib
import json
import math
import re
import struct
import subprocess
import shutil
import sys
import threading
import time
from datetime import datetime
import os
import warnings
import traceback
import tempfile
from pathlib import Path
from theme_tokens import ThemeTokens
from bootstrap import setup_windows_dll_directories

class ProjectMetadataDict(dict):

    def __getattr__(self, name: str):
        ...

    def __setattr__(self, name: str, value):
        ...

    def __delattr__(self, name: str):
        ...

def _ensure_runtime_bin_on_path():
    ...
from core_utils import INTERNAL_APP_ID, APP_DISPLAY_NAME, DEFAULT_GITHUB_REPO, make_dialog_maximizable, apply_window_titlebar_theme, safe_process_events, get_active_theme_mode, extract_dropped_file_paths, compute_file_sha256, verify_file_sha256, safe_extract_zip, safe_extract_tar, safe_replace, get_github_repo, get_update_channel, get_app_data_dir, get_models_storage_dir, set_models_storage_dir, get_bundled_runtime_dir, find_bundled_executable, ffmpeg_path, ffprobe_path, format_time, parse_time, safe_filename, is_sentence_end, format_byte_size
from transcript_cleaner import HALLUCINATION_PHRASES, HALLUCINATION_PATTERNS, REPEATED_BRACKET_PATTERN, REPEATED_PAREN_PATTERN, REPEATED_MUSIC_NOTE_PATTERN, REPEATED_PUNCTUATION_PATTERN, collapse_repeating_ngrams, strip_hallucination_phrases, trim_trailing_degenerate_tail, scrub_transcript_segments, scrub_transcript
from project_serialization import MAX_DECOMPRESSED_PROJECT_BYTES, sanitize_project_data_for_storage, serialize_rtvs_project, deserialize_rtvs_project, _decompress_gzip_bounded, read_rtvs_project_file, write_rtvs_project_file
from process_lifecycle import _REGISTERED_PROCESSES, _WINDOWS_JOB_HANDLE, init_child_process_job_isolation, bind_subprocess_to_job, register_process, unregister_process, terminate_all_registered_processes
from model_install_workers import WhisperModelInstallWorker, DiarizationModelInstallWorker, get_diarization_model_dir, is_diarization_model_available
from audio_normalization import DEFAULT_TARGET_LUFS, DEFAULT_TARGET_DBFS, DEFAULT_QUIET_THRESHOLD_LUFS, DEFAULT_QUIET_THRESHOLD_DBFS, LoudnessReport, parse_ebur128_summary, probe_media_duration_seconds, probe_media_loudness, AudioLoudnessProbeWorker, normalize_audio_sidecar, get_effective_audio_for_processing
from html.parser import HTMLParser
import os, sys
from qt_compat import _ensure_pyside6_fallback

class ResizableTextEdit(QWidget):

    def __init__(self, text: str=..., parent=...):
        ...

    def _grip_press(self, event):
        ...

    def _grip_move(self, event):
        ...

    def _grip_release(self, event):
        ...

    def sizeHint(self) -> QSize:
        ...

    def minimumSizeHint(self) -> QSize:
        ...

    def toPlainText(self) -> str:
        ...

    def setPlainText(self, text: str):
        ...

    def setText(self, text: str):
        ...

    def text(self) -> str:
        ...

    def clear(self):
        ...

    def setPlaceholderText(self, text: str):
        ...

    def placeholderText(self) -> str:
        ...

    def setToolTip(self, tip: str):
        ...

    def setAcceptRichText(self, accept: bool):
        ...

    def setTabChangesFocus(self, tab: bool):
        ...

    def setEnabled(self, enabled: bool):
        ...

    def setReadOnly(self, ro: bool):
        ...

    def isReadOnly(self) -> bool:
        ...

    def setFocus(self, *args, **kwargs):
        ...

    def hasFocus(self) -> bool:
        ...

    def document(self):
        ...

    def textCursor(self):
        ...

    def setTextCursor(self, cursor):
        ...

    def __getattr__(self, name: str):
        ...

    @property
    def textChanged(self):
        ...

class CollapsibleSection(QWidget):
    toggled = ...

    def __init__(self, title: str=..., parent=..., is_expanded: bool=..., subtitle: str=...):
        ...

    def _update_ui(self):
        ...

    def refresh_theme(self):
        ...

    def _on_btn_clicked(self):
        ...

    def set_expanded(self, expanded: bool):
        ...

    def is_expanded(self) -> bool:
        ...

    def set_title(self, title: str):
        ...

    def set_subtitle(self, subtitle: str):
        ...

    def add_widget(self, widget: QWidget):
        ...

    def add_layout(self, layout: QLayout):
        ...

def platform_seq(key_str: str) -> QKeySequence:
    ...

def get_app_icon() -> QIcon:
    ...

def get_license_file_path(filename: str=...) -> Path | None:
    ...
from transcript_editor import FindReplaceDialog

class ExportDialog(QDialog):

    def __init__(self, parent=..., has_media=..., default_name=...):
        ...

    def init_ui(self):
        ...

    def get_settings(self):
        ...
from core_utils import calculate_fade_curve_factor, calculate_fade_out_factor

def create_fade_curve_pixmap(curve_type: str, width: int=..., height: int=..., is_selected: bool=..., accent_color: QColor=..., bg_color: QColor=...) -> QPixmap:
    ...

def create_fade_curve_icon(curve_type: str, width: int=..., height: int=...) -> QIcon:
    ...

class Story:

    def __init__(self, start=..., end=..., title=..., suggestion=..., metadata=..., fade_in=..., fade_out=..., fade_curve=...):
        ...

    def to_dict(self):
        ...

    @classmethod
    def from_dict(cls, data):
        ...

class ProjectStateCommand(QUndoCommand):

    def __init__(self, main_window, before_state, after_state, description=...):
        ...

    def undo(self):
        ...

    def redo(self):
        ...
from transcript_editor import transcript_text_view_stylesheet
from comment_widgets import CommentEditorDialog, NoteEditorDialog, CommentCardWidget, CommentsPanel
from transcript_editor import TranscriptSelectionBubble, InteractiveTranscriptEdit

def read_document_text(path: Path) -> str:
    ...
from batch_dialog import BatchFileListWidget, BatchProcessingDialog
from transcript_editor import InteractiveTranscriptEdit, TranscriptSelectionBubble, FindReplaceDialog, transcript_text_view_stylesheet
from comment_widgets import CommentEditorDialog, NoteEditorDialog, CommentCardWidget, CommentsPanel
from cache_manager import ClearCacheDialog, cleanup_old_thumbnail_cache, format_byte_size, get_cache_disk_usage, purge_caches, register_active_thumbnail_dir, unregister_active_thumbnail_dir, get_active_thumbnail_dirs

def __getattr__(name: str):
    ...

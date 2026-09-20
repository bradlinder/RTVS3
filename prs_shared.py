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

setup_windows_dll_directories()

def _ensure_runtime_bin_on_path():
    """Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    candidates = [
        exe_dir / "runtime" / "bin",
        exe_dir.parent / "runtime" / "bin",
        exe_dir / "bin",
        exe_dir.parent / "bin",
    ]
    for c in candidates:
        if c.is_dir():
            str_path = str(c.resolve())
            current_path = os.environ.get("PATH", "")
            if str_path not in current_path:
                os.environ["PATH"] = str_path + os.pathsep + current_path
            break

_ensure_runtime_bin_on_path()

# Re-exports from Phase 1 modularization (core_utils, transcript_cleaner, project_serialization, process_lifecycle)
from core_utils import (
    compute_file_sha256,
    verify_file_sha256,
    safe_extract_zip,
    safe_extract_tar,
    safe_replace,
    get_github_repo,
    get_update_channel,
    get_app_data_dir,
    get_models_storage_dir,
    set_models_storage_dir,
    get_bundled_runtime_dir,
    find_bundled_executable,
    ffmpeg_path,
    ffprobe_path,
    format_time,
    parse_time,
    safe_filename,
    is_sentence_end,
)
from transcript_cleaner import (
    HALLUCINATION_PHRASES,
    HALLUCINATION_PATTERNS,
    REPEATED_BRACKET_PATTERN,
    REPEATED_PAREN_PATTERN,
    REPEATED_MUSIC_NOTE_PATTERN,
    REPEATED_PUNCTUATION_PATTERN,
    collapse_repeating_ngrams,
    strip_hallucination_phrases,
    trim_trailing_degenerate_tail,
    scrub_transcript_segments,
    scrub_transcript,
)
from project_serialization import (
    MAX_DECOMPRESSED_PROJECT_BYTES,
    sanitize_project_data_for_storage,
    serialize_rtvs_project,
    deserialize_rtvs_project,
    _decompress_gzip_bounded,
    read_rtvs_project_file,
    write_rtvs_project_file,
)
from process_lifecycle import (
    _REGISTERED_PROCESSES,
    _WINDOWS_JOB_HANDLE,
    init_child_process_job_isolation,
    bind_subprocess_to_job,
    register_process,
    unregister_process,
    terminate_all_registered_processes,
)

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    DOCX_AVAILABLE = True
except ImportError:
    Document = None
    Pt = None
    RGBColor = None
    DOCX_AVAILABLE = False

from html.parser import HTMLParser

from PySide6.QtCore import (
    Qt,
    QUrl,
    Signal,
    QObject,
    QThread,
    QRect,
    QRectF,
    QLineF,
    QPointF,
    QEvent,
    QTimer,
    QTime,
    QProcess,
    QProcessEnvironment,
    QSettings,
    QSize,
    QCoreApplication,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QFont,
    QAction,
    QActionGroup,
    QUndoStack,
    QUndoCommand,
    QKeySequence,
    QPalette,
    QTextCursor,
    QTextCharFormat,
    QTextDocument,
    QShortcut,
    QPixmap,
    QIcon,
    QCursor,
    QDesktopServices,
)

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QAbstractSpinBox,
    QTextEdit,
    QPlainTextEdit,
    QTextBrowser,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QInputDialog,
    QSpinBox,
    QSlider,
    QComboBox,
    QCompleter,
    QToolTip,
    QMenu,
    QDialog,
    QCheckBox,
    QDoubleSpinBox,
    QScrollBar,
    QFrame,
    QStackedWidget,
    QProgressDialog,
    QScrollArea,
    QSizePolicy,
    QStyledItemDelegate,
    QStyle,
    QToolButton,
    QLayout,
)

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class ResizableTextEdit(QWidget):
    """Multi-line text editor defaulted to ~2 lines of height with a drag handle for vertical expansion."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Compute ~2 lines height based on font metrics
        fm = self.text_edit.fontMetrics()
        line_height = fm.lineSpacing()
        self._min_h = max(44, line_height * 2 + 12)
        self.text_edit.setFixedHeight(self._min_h)
        self.setFixedHeight(self._min_h + 10)

        # Visual resize grip bar at bottom
        self.grip = QFrame()
        self.grip.setObjectName("resizable_text_grip")
        self.grip.setFixedHeight(8)
        self.grip.setCursor(Qt.CursorShape.SizeVerCursor)
        self.grip.setToolTip("Drag down/up to resize excerpt box")
        self.grip.mousePressEvent = self._grip_press
        self.grip.mouseMoveEvent = self._grip_move
        self.grip.mouseReleaseEvent = self._grip_release

        layout.addWidget(self.text_edit)
        layout.addWidget(self.grip)

        self._resizing = False
        self._start_y = 0
        self._start_h = self._min_h
        self._start_win_h = 0

    def _grip_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._resizing = True
            self._start_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            self._start_h = self.text_edit.height()
            win = self.window()
            if win:
                self._start_win_h = win.height()
            event.accept()

    def _grip_move(self, event):
        if self._resizing:
            global_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            dy = global_y - self._start_y
            new_h = max(self._min_h, min(450, int(self._start_h + dy)))
            old_h = self.text_edit.height()
            if new_h != old_h:
                self.text_edit.setFixedHeight(new_h)
                self.setFixedHeight(new_h + 10)
                self.updateGeometry()
                win = self.window()
                if win and hasattr(self, "_start_win_h") and self._start_win_h > 0:
                    win_delta = new_h - self._start_h
                    target_win_h = max(win.minimumHeight(), int(self._start_win_h + win_delta))
                    win.resize(win.width(), target_win_h)
                    if win.layout():
                        win.layout().activate()
                    win.updateGeometry()
            event.accept()

    def _grip_release(self, event):
        self._resizing = False
        event.accept()

    def sizeHint(self) -> QSize:
        return QSize(self.text_edit.sizeHint().width(), self.text_edit.height() + 10)

    def minimumSizeHint(self) -> QSize:
        return QSize(self.text_edit.minimumSizeHint().width(), self._min_h + 10)

    def toPlainText(self) -> str:
        return self.text_edit.toPlainText()

    def setPlainText(self, text: str):
        self.text_edit.setPlainText(text)

    def setText(self, text: str):
        self.text_edit.setPlainText(text)

    def text(self) -> str:
        return self.text_edit.toPlainText()

    def clear(self):
        self.text_edit.clear()

    def setPlaceholderText(self, text: str):
        self.text_edit.setPlaceholderText(text)

    def placeholderText(self) -> str:
        return self.text_edit.placeholderText()

    def setToolTip(self, tip: str):
        self.text_edit.setToolTip(tip)

    def setAcceptRichText(self, accept: bool):
        self.text_edit.setAcceptRichText(accept)

    def setTabChangesFocus(self, tab: bool):
        self.text_edit.setTabChangesFocus(tab)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.text_edit.setEnabled(enabled)
        self.grip.setEnabled(enabled)

    def setReadOnly(self, ro: bool):
        self.text_edit.setReadOnly(ro)

    def isReadOnly(self) -> bool:
        return self.text_edit.isReadOnly()

    def setFocus(self, *args, **kwargs):
        self.text_edit.setFocus(*args, **kwargs)

    def hasFocus(self) -> bool:
        return self.text_edit.hasFocus()

    def document(self):
        return self.text_edit.document()

    def textCursor(self):
        return self.text_edit.textCursor()

    def setTextCursor(self, cursor):
        self.text_edit.setTextCursor(cursor)

    def __getattr__(self, name: str):
        if "text_edit" in self.__dict__ and hasattr(self.text_edit, name):
            return getattr(self.text_edit, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def textChanged(self):
        return self.text_edit.textChanged


class CollapsibleSection(QWidget):
    """A clean, collapsible and expandable section widget with a styled toggle button,
    expand/collapse indicator arrow (▾ / ▸), section title, optional subtitle/summary badge,
    and a content container."""

    toggled = Signal(bool)

    def __init__(self, title: str = "", parent=None, is_expanded: bool = True, subtitle: str = ""):
        super().__init__(parent)
        self._is_expanded = bool(is_expanded)
        self._title = title
        self._subtitle = subtitle

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 4)
        self._main_layout.setSpacing(0)

        # Header button
        self.toggle_btn = QToolButton(self)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self._is_expanded)
        self.toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._on_btn_clicked)

        # Content container
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("CollapsibleContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 8, 10, 10)
        self.content_layout.setSpacing(8)

        self._main_layout.addWidget(self.toggle_btn)
        self._main_layout.addWidget(self.content_widget)

        self._update_ui()
        self.content_widget.setVisible(self._is_expanded)

    def _update_ui(self):
        arrow = "▾" if self._is_expanded else "▸"
        sub = f"  ({self._subtitle})" if self._subtitle else ""
        self.toggle_btn.setText(f" {arrow}  {self._title}{sub}")

        radius = "6px 6px 0px 0px" if self._is_expanded else "6px"
        border_bottom = "none" if self._is_expanded else "1px solid #334155"

        self.toggle_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: #1e293b;
                color: #f1f5f9;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #334155;
                border-bottom: {border_bottom};
                border-radius: {radius};
                padding: 7px 12px;
                text-align: left;
            }}
            QToolButton:hover {{
                background-color: #283548;
                border-color: #475569;
            }}
            QToolButton:pressed {{
                background-color: #0f172a;
            }}
        """)

        self.content_widget.setStyleSheet("""
            QWidget#CollapsibleContent {
                background-color: rgba(15, 23, 42, 0.35);
                border: 1px solid #334155;
                border-top: none;
                border-radius: 0px 0px 6px 6px;
            }
        """)

    def _on_btn_clicked(self):
        self.set_expanded(self.toggle_btn.isChecked())

    def set_expanded(self, expanded: bool):
        self._is_expanded = bool(expanded)
        self.toggle_btn.setChecked(self._is_expanded)
        self.content_widget.setVisible(self._is_expanded)
        self._update_ui()
        self.toggled.emit(self._is_expanded)

    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_title(self, title: str):
        self._title = title
        self._update_ui()

    def set_subtitle(self, subtitle: str):
        self._subtitle = subtitle
        self._update_ui()

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QLayout):
        self.content_layout.addLayout(layout)


# ============================================================
# Application constants
# ============================================================

# Display branding shown to the user (title bar, About box, installers).
APP_DISPLAY_NAME = "Radio & TV Segmenter"
PROJECT_VERSION = "3.5.0-beta-3"
DEFAULT_GITHUB_REPO = "bradlinder/RTVS3"


# Internal identifiers are intentionally left as "RadioTVStorySegmenter" (the
# original project name) rather than renamed to match APP_DISPLAY_NAME: this
# is the QSettings org/app name and the per-user app-data folder name, and
# changing it would orphan existing beta users' saved preferences and
# downloaded Whisper model cache on upgrade. Only user-facing text changes.
INTERNAL_APP_ID = "RadioTVStorySegmenter"

HELPER_PROTOCOL_VERSION = "1.0"
WAVEFORM_ANALYSIS_RATE = 8000
WAVEFORM_POINTS_PER_SECOND = 200
MIN_WORDS_PER_PARAGRAPH = 100
MAX_ACTIVITY_SNAPSHOTS = 50


def platform_seq(key_str: str) -> QKeySequence:
    """Return a QKeySequence adapted for macOS vs Windows/Linux.

    - Replaces 'Ctrl+' with 'Meta+' (Command ⌘) on macOS.
    - Leaves standard Ctrl/Shift/Alt unmodified on Windows/Linux.
    """
    if sys.platform == "darwin":
        # Meta in Qt key strings corresponds to Command (⌘) on macOS
        key_str = key_str.replace("Ctrl+", "Meta+")
    return QKeySequence(key_str)
    
def get_app_icon() -> QIcon:
    """Return the application QIcon loaded from bundled resources or fallback to empty."""
    icon_paths = []

    # 1. PyInstaller temporary extraction directory (_MEIPASS)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = Path(meipass)
        icon_paths.extend([
            p / "resources" / "icon.ico",
            p / "resources" / "icon.png",
            p / "resources" / "icon.svg",
            p / "icon.ico",
            p / "icon.png",
        ])

    # 2. Frozen binary folder, alongside the exe, and inside _internal/
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
        icon_paths.extend([
            app_dir / "resources" / "icon.ico",
            app_dir / "resources" / "icon.png",
            app_dir / "resources" / "icon.svg",
            app_dir / "_internal" / "resources" / "icon.ico",
            app_dir / "_internal" / "resources" / "icon.png",
            app_dir / "_internal" / "resources" / "icon.svg",
            app_dir / "icon.ico",
            app_dir / "icon.png",
        ])

    # 3. Source directory
    src_dir = Path(__file__).resolve().parent
    icon_paths.extend([
        src_dir / "resources" / "icon.ico",
        src_dir / "resources" / "icon.png",
        src_dir / "resources" / "icon.svg",
        src_dir / "icon.ico",
        src_dir / "icon.png",
    ])

    for path in icon_paths:
        if path.is_file():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon

    return QIcon()

def get_license_file_path(filename: str = "NOTICES.txt") -> Path | None:
    """Return the path to a licensing or notice file, checking bundle and source paths."""
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / filename)
        candidates.append(Path(meipass) / "resources" / filename)
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
        candidates.append(app_dir / filename)
        candidates.append(app_dir / "resources" / filename)
        candidates.append(app_dir.parent / "Resources" / filename)
    src_dir = Path(__file__).resolve().parent
    candidates.append(src_dir / filename)
    candidates.append(src_dir / "resources" / filename)
    for p in candidates:
        if p.is_file():
            return p
    return None


# ============================================================
# Find & Replace Dialog
# ============================================================

class FindReplaceDialog(QDialog):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.find_input = QLineEdit()
        self.replace_input = QLineEdit()
        self.case_checkbox = QCheckBox("Match Case")

        form.addRow("Find:", self.find_input)
        form.addRow("Replace with:", self.replace_input)
        layout.addLayout(form)
        layout.addWidget(self.case_checkbox)

        btn_layout = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")

        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

        self.find_next_btn.clicked.connect(self.find_next)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)

        self.shortcut_find_next = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_find_next.activated.connect(self.find_next)

    def get_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        target = self.find_input.text()
        if not target:
            return False

        found = self.text_edit.find(target, self.get_flags())
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, self.get_flags())

        return found

    def replace(self):
        target = self.find_input.text()
        if not target:
            return

        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        target = self.find_input.text()
        replacement = self.replace_input.text()
        if not target:
            return

        # Perform cursor-based forward pass to prevent infinite matching loops
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        self.text_edit.setTextCursor(cursor)

        count = 0
        flags = self.get_flags()
        while self.text_edit.find(target, flags):
            match_cursor = self.text_edit.textCursor()
            match_cursor.insertText(replacement)
            count += 1

        cursor.endEditBlock()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")
        
class ExportDialog(QDialog):
    def __init__(self, parent=None, has_media=True, default_name="export"):
        super().__init__(parent)
        self.has_media = has_media
        self.default_name = default_name
        self.setWindowTitle("Export Options")
        self.setMinimumWidth(380)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Export Scope Selection
        self.scope_section = CollapsibleSection("Export Scope", self, is_expanded=True)
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Full Episode", "full")
        self.scope_combo.addItem("All Stories", "all_stories")
        self.scope_combo.addItem("Selected Stories Only", "selected_stories")
        self.scope_combo.addItem("Full Episode & All Stories", "full_and_all_stories")
        self.scope_section.add_widget(self.scope_combo)
        layout.addWidget(self.scope_section)

        # Export Format Options
        self.format_section = CollapsibleSection("Export Formats", self, is_expanded=True)

        self.txt_checkbox = QCheckBox("Text (.txt)")
        self.txt_checkbox.setChecked(True)

        self.docx_checkbox = QCheckBox("Word Document (.docx)")
        self.docx_checkbox.setChecked(True)

        self.pdf_checkbox = QCheckBox("PDF Document (.pdf)")
        self.pdf_checkbox.setChecked(True)

        self.media_checkbox = QCheckBox("Export Audio / Video Clips")
        if not self.has_media:
            self.media_checkbox.setChecked(False)
            self.media_checkbox.setEnabled(False)
            self.media_checkbox.setToolTip("No media file is associated with this document.")
        else:
            self.media_checkbox.setChecked(True)
            self.media_checkbox.setToolTip("Export corresponding media clips for each story segment.")

        self.notes_checkbox = QCheckBox("Include Segment & Project Notes")
        self.notes_checkbox.setChecked(True)

        self.highlights_checkbox = QCheckBox("Include Comment Highlights")
        self.highlights_checkbox.setToolTip("Apply visual highlights to commented sections in exported DOCX & PDF documents.")
        self.highlights_checkbox.setChecked(True)

        self.format_section.add_widget(self.txt_checkbox)
        self.format_section.add_widget(self.docx_checkbox)
        self.format_section.add_widget(self.pdf_checkbox)
        self.format_section.add_widget(self.notes_checkbox)
        self.format_section.add_widget(self.highlights_checkbox)
        self.format_section.add_widget(self.media_checkbox)
        layout.addWidget(self.format_section)

        # Base Filename Input
        form_layout = QFormLayout()
        self.filename_input = QLineEdit(self.default_name)
        form_layout.addRow("Base Filename:", self.filename_input)
        layout.addLayout(form_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.export_btn = QPushButton("Export")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Connections
        self.export_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_settings(self):
        return {
            "scope": self.scope_combo.currentData(),
            "txt": self.txt_checkbox.isChecked(),
            "docx": self.docx_checkbox.isChecked(),
            "pdf": self.pdf_checkbox.isChecked(),
            "include_notes": self.notes_checkbox.isChecked(),
            "include_highlights": self.highlights_checkbox.isChecked(),
            "media": self.media_checkbox.isChecked(),
            "filename": self.filename_input.text().strip() or self.default_name,
        }

# ============================================================
# Data model
# ============================================================

def calculate_fade_curve_factor(u: float, fcurve: str = "linear") -> float:
    """Calculate normalized fade-in multiplier (0.0 to 1.0) given progress `u` in [0, 1]."""
    u = max(0.0, min(1.0, float(u)))
    fcurve = str(fcurve).lower()
    if fcurve == "s_curve":
        return float(0.5 * (1.0 - math.cos(math.pi * u)))
    elif fcurve == "logarithmic":
        return float(math.log10(1.0 + 9.0 * u))
    elif fcurve == "exponential":
        return float((math.pow(10.0, u) - 1.0) / 9.0)
    else:  # "linear"
        return u


def calculate_fade_out_factor(u: float, fcurve: str = "linear") -> float:
    """Calculate normalized fade-out multiplier (1.0 to 0.0) given progress `u` from 0.0 (fade start) to 1.0 (silence).

    Accurately maps the visual preview cues to the applied fade-out:
    - Logarithmic (⌒): Gentle initial volume roll-off, steepening near the end (convex / domed).
    - Exponential (◞): Rapid initial volume attenuation, followed by a gentle tail to silence (concave / scooped).
    - S-Curve (∿): Smooth cosine ease-in and ease-out transition.
    - Linear (╱): Constant-rate linear attenuation (1.0 - u).
    """
    u = max(0.0, min(1.0, float(u)))
    fcurve = str(fcurve).lower()
    if fcurve == "s_curve":
        return float(0.5 * (1.0 + math.cos(math.pi * u)))
    elif fcurve == "logarithmic":
        # Matches Logarithmic preview (⌒): stays high initially before dropping at end
        return float(max(0.0, min(1.0, 1.0 - (math.pow(10.0, u) - 1.0) / 9.0)))
    elif fcurve == "exponential":
        # Matches Exponential preview (◞): drops fast initially then gently glides to silence
        return float(max(0.0, min(1.0, 1.0 - math.log10(1.0 + 9.0 * u))))
    else:
        return float(1.0 - u)


FADE_CURVE_PROFILES = [
    {
        "id": "linear",
        "symbol": "╱",
        "title": "Linear",
        "full_name": "Linear Ramp",
        "desc": "Straight line constant-rate volume attenuation (╱)",
    },
    {
        "id": "s_curve",
        "symbol": "∿",
        "title": "S-Curve",
        "full_name": "Cosine S-Curve",
        "desc": "Smooth cosine ease-in and ease-out transition (∿)",
    },
    {
        "id": "logarithmic",
        "symbol": "⌒",
        "title": "Logarithmic",
        "full_name": "Logarithmic",
        "desc": "Rapid initial volume rise with gentle plateau (⌒)",
    },
    {
        "id": "exponential",
        "symbol": "◞",
        "title": "Exponential",
        "full_name": "Exponential",
        "desc": "Gentle initial volume roll with steep acceleration (◞)",
    },
]

_FADE_CURVE_PIXMAP_CACHE = {}
_FADE_CURVE_ICON_CACHE = {}


def create_fade_curve_pixmap(
    curve_type: str,
    width: int = 56,
    height: int = 30,
    is_selected: bool = False,
    accent_color: QColor = None,
    bg_color: QColor = None,
) -> QPixmap:
    """Render a high-DPI visual curve representation showing the volume attenuation shape."""
    cache_key = (str(curve_type), int(width), int(height), bool(is_selected))
    if accent_color is None and bg_color is None and cache_key in _FADE_CURVE_PIXMAP_CACHE:
        return _FADE_CURVE_PIXMAP_CACHE[cache_key]

    pix = QPixmap(width, height)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    bg = bg_color if bg_color is not None else (QColor(15, 23, 42, 235) if not is_selected else QColor(30, 41, 59, 255))
    border_color = QColor(56, 189, 248, 220) if is_selected else QColor(51, 65, 85, 180)
    painter.setPen(QPen(border_color, 1.2 if is_selected else 1.0))
    painter.setBrush(QBrush(bg))
    card_rect = QRectF(1.0, 1.0, width - 2.0, height - 2.0)
    painter.drawRoundedRect(card_rect, 4.0, 4.0)

    pad_x = 7.0
    pad_top = 5.0
    pad_bottom = 5.0
    plot_w = width - 2.0 * pad_x
    plot_h = height - pad_top - pad_bottom

    # Subtle ceiling and baseline reference lines
    grid_pen = QPen(QColor(148, 163, 184, 45), 0.8, Qt.PenStyle.DashLine)
    painter.setPen(grid_pen)
    painter.drawLine(QPointF(pad_x, pad_top), QPointF(width - pad_x, pad_top))
    painter.drawLine(QPointF(pad_x, height - pad_bottom), QPointF(width - pad_x, height - pad_bottom))

    if accent_color is None:
        palette = {
            "linear": QColor("#38bdf8"),
            "s_curve": QColor("#818cf8"),
            "logarithmic": QColor("#34d399"),
            "exponential": QColor("#fb923c"),
        }
        color = palette.get(str(curve_type).lower(), QColor("#38bdf8"))
    else:
        color = accent_color

    steps = 24
    points = []
    for step_i in range(steps + 1):
        u = step_i / float(steps)
        val = calculate_fade_curve_factor(u, curve_type)
        px = pad_x + u * plot_w
        py = (height - pad_bottom) - val * plot_h
        points.append(QPointF(px, py))

    curve_path = QPainterPath()
    if points:
        curve_path.moveTo(points[0])
        for pt in points[1:]:
            curve_path.lineTo(pt)

    # Shaded polygon area beneath the curve
    fill_path = QPainterPath(curve_path)
    fill_path.lineTo(QPointF(width - pad_x, height - pad_bottom))
    fill_path.lineTo(QPointF(pad_x, height - pad_bottom))
    fill_path.closeSubpath()

    fill_color = QColor(color.red(), color.green(), color.blue(), 55 if is_selected else 35)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(fill_color))
    painter.drawPath(fill_path)

    # Curve stroke
    pen_width = 2.0 if is_selected else 1.6
    painter.setPen(QPen(color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(curve_path)

    # Tactile terminal nodes
    painter.setPen(QPen(QColor(15, 23, 42), 1.0))
    painter.setBrush(QBrush(color))
    if points:
        painter.drawEllipse(points[0], 2.2, 2.2)
        painter.drawEllipse(points[-1], 2.2, 2.2)

    painter.end()

    if accent_color is None and bg_color is None:
        _FADE_CURVE_PIXMAP_CACHE[cache_key] = pix
    return pix


def create_fade_curve_icon(curve_type: str, width: int = 56, height: int = 30) -> QIcon:
    """Return a QIcon containing visual render of the specified audio fade curve."""
    cache_key = (str(curve_type), int(width), int(height))
    if cache_key in _FADE_CURVE_ICON_CACHE:
        return _FADE_CURVE_ICON_CACHE[cache_key]

    normal_pix = create_fade_curve_pixmap(curve_type, width=width, height=height, is_selected=False)
    selected_pix = create_fade_curve_pixmap(curve_type, width=width, height=height, is_selected=True)
    icon = QIcon()
    icon.addPixmap(normal_pix, QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(selected_pix, QIcon.Mode.Normal, QIcon.State.On)
    icon.addPixmap(selected_pix, QIcon.Mode.Active, QIcon.State.Off)
    icon.addPixmap(selected_pix, QIcon.Mode.Active, QIcon.State.On)

    _FADE_CURVE_ICON_CACHE[cache_key] = icon
    return icon


class FadeCurveVisualSelector(QWidget):
    """Visual selector widget providing interactive card buttons for audio fade curves."""
    currentDataChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None, button_width=92, button_height=60):
        super().__init__(parent)
        self._current_data = "linear"
        self._buttons = []
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        for idx, profile in enumerate(FADE_CURVE_PROFILES):
            cid = profile["id"]
            btn = QToolButton(self)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(56, 28))
            btn.setIcon(create_fade_curve_icon(cid, width=56, height=28))
            btn.setText(f"{profile['symbol']} {profile['title']}")
            btn.setToolTip(f"{profile['full_name']}\n{profile['desc']}")
            btn.setFixedSize(button_width, button_height)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn.setStyleSheet("""
                QToolButton {
                    background-color: rgba(30, 41, 59, 0.7);
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #cbd5e1;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 2px;
                }
                QToolButton:hover {
                    background-color: rgba(51, 65, 85, 0.85);
                    border: 1px solid #94a3b8;
                    color: #f8fafc;
                }
                QToolButton:checked {
                    background-color: rgba(14, 116, 144, 0.35);
                    border: 2px solid #38bdf8;
                    color: #38bdf8;
                    font-weight: bold;
                }
            """)

            self._button_group.addButton(btn, idx)
            btn.toggled.connect(self._on_button_toggled)
            layout.addWidget(btn)
            self._buttons.append((cid, btn))

        layout.addStretch()
        self.setCurrentData("linear")

    def _on_button_toggled(self, checked):
        if not checked:
            return
        for idx, (cid, btn) in enumerate(self._buttons):
            if btn.isChecked():
                if self._current_data != cid:
                    self._current_data = cid
                    self.currentDataChanged.emit(cid)
                    self.currentIndexChanged.emit(idx)
                break

    def currentData(self) -> str:
        return self._current_data

    def setCurrentData(self, curve_type: str):
        target = str(curve_type or "linear").lower().strip()
        found = False
        for idx, (cid, btn) in enumerate(self._buttons):
            if cid == target:
                btn.setChecked(True)
                self._current_data = cid
                found = True
                break
        if not found and self._buttons:
            self._buttons[0][1].setChecked(True)
            self._current_data = self._buttons[0][0]

    def findData(self, curve_type: str) -> int:
        target = str(curve_type or "linear").lower().strip()
        for idx, (cid, _) in enumerate(self._buttons):
            if cid == target:
                return idx
        return -1

    def currentIndex(self) -> int:
        for idx, (cid, _) in enumerate(self._buttons):
            if cid == self._current_data:
                return idx
        return 0

    def setCurrentIndex(self, idx: int):
        if 0 <= idx < len(self._buttons):
            self.setCurrentData(self._buttons[idx][0])



class Story:
    def __init__(
        self,
        start=0,
        end=0,
        title="Untitled Story",
        suggestion=False,
        metadata=None,
        fade_in=None,
        fade_out=None,
        fade_curve=None,
    ):
        self.start = float(start)
        self.end = float(end)
        self.title = title
        self.suggestion = suggestion
        self.metadata = dict(metadata) if isinstance(metadata, dict) else {}

        if fade_in is not None:
            self.fade_in = max(0.0, float(fade_in))
        else:
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_in = max(0.0, float(settings.value("default_fade_in_duration", 0.0)))
            except Exception:
                self.fade_in = 0.0

        if fade_out is not None:
            self.fade_out = max(0.0, float(fade_out))
        else:
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_out = max(0.0, float(settings.value("default_fade_out_duration", 1.0)))
            except Exception:
                self.fade_out = 1.0

        if fade_curve is not None:
            self.fade_curve = str(fade_curve)
        else:
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_curve = str(settings.value("default_fade_curve", "linear") or "linear")
            except Exception:
                self.fade_curve = "linear"

    def to_dict(self):
        d = {
            "start": self.start,
            "end": self.end,
            "title": self.title,
            "suggestion": self.suggestion,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "fade_curve": getattr(self, "fade_curve", "linear"),
        }
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d

    @classmethod
    def from_dict(cls, data):
        known = {"start", "end", "title", "suggestion", "metadata", "fade_in", "fade_out", "fade_curve"}
        meta = dict(data.get("metadata", {})) if isinstance(data.get("metadata"), dict) else {}
        for k, v in data.items():
            if k not in known:
                meta[k] = v
        return cls(
            start=data.get("start", 0),
            end=data.get("end", 0),
            title=data.get("title", "Untitled Story"),
            suggestion=data.get("suggestion", False),
            metadata=meta,
            fade_in=data.get("fade_in"),
            fade_out=data.get("fade_out"),
            fade_curve=data.get("fade_curve"),
        )


# ============================================================
# Undo / Redo Commands
# ============================================================

class StoryFadesChangeCommand(QUndoCommand):
    """Discrete undo/redo command for story audio fade-in, fade-out, and curve adjustments."""

    def __init__(self, main_window, story_index, old_in, old_out, new_in, new_out, old_curve="linear", new_curve="linear", description="Adjust Audio Fades"):
        super().__init__(description)
        self.main_window = main_window
        self.story_index = story_index
        self.old_in = round(float(old_in), 3)
        self.old_out = round(float(old_out), 3)
        self.new_in = round(float(new_in), 3)
        self.new_out = round(float(new_out), 3)
        self.old_curve = str(old_curve)
        self.new_curve = str(new_curve)

    def undo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].fade_in = self.old_in
            self.main_window.stories[self.story_index].fade_out = self.old_out
            self.main_window.stories[self.story_index].fade_curve = self.old_curve
            self._sync_ui()

    def redo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].fade_in = self.new_in
            self.main_window.stories[self.story_index].fade_out = self.new_out
            self.main_window.stories[self.story_index].fade_curve = self.new_curve
            self._sync_ui()

    def _sync_ui(self):
        if hasattr(self.main_window, "refresh_story_list"):
            self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if hasattr(self.main_window, "save_project"):
            self.main_window.save_project()


class SetStoriesCommand(QUndoCommand):
    def __init__(self, main_window, old_stories, new_stories, description="Modify Stories"):
        super().__init__(description)
        self.main_window = main_window
        self.old_stories = [Story.from_dict(s.to_dict()) for s in old_stories]
        self.new_stories = [Story.from_dict(s.to_dict()) for s in new_stories]

    def undo(self):
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.old_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        self.main_window.save_project()

    def redo(self):
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.new_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        self.main_window.save_project()


class StoryBoundaryChangeCommand(QUndoCommand):
    """Discrete undo/redo command for story boundary adjustments (start/end times)."""

    def __init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description="Adjust Story Boundary"):
        super().__init__(description)
        self.main_window = main_window
        self.story_index = story_index
        self.old_start = round(float(old_start), 3)
        self.old_end = round(float(old_end), 3)
        self.new_start = round(float(new_start), 3)
        self.new_end = round(float(new_end), 3)

    def undo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.old_start
            self.main_window.stories[self.story_index].end = self.old_end
            self._sync_ui(self.old_start, self.old_end)

    def redo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.new_start
            self.main_window.stories[self.story_index].end = self.new_end
            self._sync_ui(self.new_start, self.new_end)

    def _sync_ui(self, start, end):
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if getattr(self.main_window, "current_selected_story_indices", []) == [self.story_index]:
            if hasattr(self.main_window, "start_input"):
                self.main_window.start_input.setText(format_time(start))
            if hasattr(self.main_window, "end_input"):
                self.main_window.end_input.setText(format_time(end))
        self.main_window.mark_project_dirty(self.text())
        self.main_window.save_project()


class SelectStoriesCommand(QUndoCommand):
    def __init__(self, main_window, old_selection, new_selection, description="Change Story Selection"):
        super().__init__(description)
        self.main_window = main_window
        self.old_selection = list(old_selection)
        self.new_selection = list(new_selection)

    def undo(self):
        self.main_window.apply_story_selection_indices(self.old_selection)

    def redo(self):
        self.main_window.apply_story_selection_indices(self.new_selection)


class ProjectStateCommand(QUndoCommand):
    """Undo/redo a complete editable project state.

    This is intentionally broader than story-only undo. Transcript text,
    speaker labels/overrides, translations, diarization and story data all
    travel together so Ctrl+Z / Ctrl+Shift+Z can restore a coherent project.
    """
    def __init__(self, main_window, before_state, after_state, description="Modify Project"):
        super().__init__(description)
        self.main_window = main_window
        # before_state and after_state are already isolated snapshot dicts produced
        # by _capture_project_state(). Storing shallow dict copies avoids expensive
        # recursive deepcopy duplication and prevents GC hitches on long files (>60 min).
        self.before_state = copy.deepcopy(before_state) if isinstance(before_state, dict) else before_state
        self.after_state = copy.deepcopy(after_state) if isinstance(after_state, dict) else after_state
        self._first_redo = True

    def undo(self):
        self.main_window._restore_project_state_for_undo(self.before_state)

    def redo(self):
        if self._first_redo:
            self._first_redo = False
            return
        self.main_window._restore_project_state_for_undo(self.after_state)


# ============================================================
# ============================================================
# Custom Story Card Delegate (Milestones 3.10 & 3.14)
# ============================================================

class StoryCardDelegate(QStyledItemDelegate):
    """Renders story items as clean cards with color-coded accent bars, pill badges, and time metadata."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        w = option.rect.width() if (option and option.rect and option.rect.width() > 0) else 240
        return QSize(max(120, w), 46)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        try:
            rect = option.rect
            list_widget = option.widget
            win = list_widget.window() if list_widget else None
            tokens = getattr(win, "tokens", ThemeTokens())
            palette = getattr(tokens, "story_palette", ("#2563eb", "#d97706", "#059669", "#7c3aed", "#e11d48", "#0d9488", "#4f46e5", "#db2777"))

            row = index.row()
            item_color = QColor(palette[row % len(palette)])

            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

            card_rect = QRectF(rect.x() + 3, rect.y() + 2, rect.width() - 6, rect.height() - 4)

            # Card Background & Outline
            if is_selected:
                bg = tokens.color(getattr(tokens, "selection_fill", "#38bdf8"))
                bg.setAlpha(90)
                border_pen = QPen(tokens.color(getattr(tokens, "selection_border", "#38bdf8")), 1.5)
            elif is_hovered:
                hover_hex = getattr(tokens, "bg_surface", getattr(tokens, "btn_hover_bg", "#181b20"))
                bg = tokens.color(hover_hex)
                border_pen = QPen(tokens.color(getattr(tokens, "border_subtle", "#282c35")), 1.0)
            else:
                card_hex = getattr(tokens, "bg_card", getattr(tokens, "card_bg", "#1e222a"))
                bg = tokens.color(card_hex)
                border_pen = QPen(tokens.color(getattr(tokens, "border_subtle", "#282c35")), 1.0)

            painter.fillRect(card_rect, bg)
            painter.setPen(border_pen)
            painter.drawRoundedRect(card_rect, 4.0, 4.0)

            # 4px Left Accent Bar in assigned story color
            bar_rect = QRectF(card_rect.x(), card_rect.y(), 4, card_rect.height())
            painter.fillRect(bar_rect, item_color)

            # Story Data
            story_data = index.data(Qt.ItemDataRole.UserRole)
            is_music = getattr(win, "story_detection_mode", "voice") == "music"
            is_es = getattr(win, "language", "en") == "es"
            badge_prefix = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

            if isinstance(story_data, dict):
                title = story_data.get("title", f"{badge_prefix} {row + 1}")
                start = float(story_data.get("start", 0.0))
                end = float(story_data.get("end", 0.0))
                dur = max(0.0, end - start)
                time_str = f"{format_time(start, include_millis=False)} – {format_time(end, include_millis=False)}  ({format_time(dur, include_millis=False)})"
            else:
                raw_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
                # Parse legacy string format "1. 00:00:00 – 00:02:15  Title"
                parts = raw_text.split("  ", 1)
                if len(parts) == 2:
                    time_str = parts[0].split(". ", 1)[-1] if ". " in parts[0] else parts[0]
                    title = parts[1]
                else:
                    time_str = ""
                    title = raw_text

            # Numbered Pill Badge (Story 1, Story 2...)
            badge_text = f"{badge_prefix} {row + 1}"
            badge_font = QFont(option.font)
            badge_font.setPointSize(8)
            badge_font.setBold(True)
            painter.setFont(badge_font)

            badge_w = max(48, painter.fontMetrics().horizontalAdvance(badge_text) + 12)
            badge_rect = QRectF(card_rect.x() + 9, card_rect.y() + 5, badge_w, 17)
            pill_bg = QColor(item_color)
            pill_bg.setAlpha(220)
            painter.fillRect(badge_rect, pill_bg)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

            # Story Headline / Title
            title_font = QFont(option.font)
            title_font.setPointSize(9)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(tokens.color(getattr(tokens, "text_primary", "#f0f3f6")))

            title_rect = QRectF(card_rect.x() + 15 + badge_w, card_rect.y() + 5, card_rect.width() - (22 + badge_w), 17)
            elided_title = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, int(title_rect.width()))
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_title)

            # Time range metadata
            if time_str:
                win = self.parent().window() if self.parent() else None
                fades_enabled = getattr(win, "enable_audio_fades", False)
                if fades_enabled:
                    fade_in = getattr(story, "fade_in", 0.0) if story else 0.0
                    fade_out = getattr(story, "fade_out", 0.0) if story else 0.0
                    if fade_in > 0 or fade_out > 0:
                        time_str += f"  •  Fades: {fade_in:.1f}s / {fade_out:.1f}s"
                time_font = QFont(option.font)
                time_font.setPointSize(8)
                painter.setFont(time_font)
                painter.setPen(tokens.color(getattr(tokens, "text_secondary", "#8b949e")))
                time_rect = QRectF(card_rect.x() + 9, card_rect.y() + 24, card_rect.width() - 18, 14)
                painter.drawText(time_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, time_str)
        except Exception:
            # Fallback safe card painting
            painter.fillRect(option.rect, QColor("#1e222a"))
            painter.setPen(QColor("#ffffff"))
            raw_text = index.data(Qt.ItemDataRole.DisplayRole) or f"Story {index.row() + 1}"
            painter.drawText(option.rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, str(raw_text))
        finally:
            painter.restore()


# ============================================================
# Interactive Transcript Edit Widget
# ============================================================

def transcript_text_view_stylesheet(mode, font_size=16):
    """Shared visual treatment for transcript-style views.

    ``font_size`` is deliberately supplied at runtime so the user's transcript
    zoom preference changes only transcript text, not the surrounding UI.
    """
    font_size = max(11, min(25, float(font_size)))
    if mode == "light":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #c5c5cb;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
            }}
        """
    elif mode == "high_contrast":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffff00;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
            }}
        """
    return f"""
        QTextEdit, QTextBrowser {{
            background-color: #121417;
            color: #f0f3f6;
            border: 1px solid #282c35;
            border-radius: 8px;
            padding: 12px;
            font-size: {font_size:.1f}px;
            line-height: 1.6;
            selection-background-color: #38bdf8;
            selection-color: #ffffff;
        }}
    """


class CommentEditorDialog(QDialog):
    """Multi-line document-style comment editor supporting spaces, line breaks, and paragraph breaks."""
    def __init__(self, parent=None, comment_text="", title="Add Comment", prompt="Enter comment details:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        label = QLabel(prompt, self)
        label.setWordWrap(True)
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(label)

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(comment_text)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setPlaceholderText("Type your comment here... (Spaces, tabs, Enter line breaks, and Ctrl+Enter to save supported)")
        self.text_edit.setStyleSheet("font-size: 13px; line-height: 1.5; padding: 6px;")
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ Delete Comment", self)
        self.delete_btn.setStyleSheet("color: #dc2626; font-weight: bold;")
        self.delete_btn.setVisible(bool(comment_text and comment_text.strip()))

        self.save_btn = QPushButton("Save Comment", self)
        self.save_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel", self)

        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.delete_btn.clicked.connect(self._on_delete)
        self._is_deleted = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.accept()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_delete(self):
        self._is_deleted = True
        self.accept()

    def get_comment_text(self):
        if self._is_deleted:
            return ""
        return self.text_edit.toPlainText()

    def get_note_text(self):
        return self.get_comment_text()

    def is_deleted(self):
        return self._is_deleted


# Alias for backward compatibility
NoteEditorDialog = CommentEditorDialog


class CommentCardWidget(QFrame):
    """Card representing a single range-anchored comment in the Comments side panel."""
    editRequested = Signal(int)
    deleteRequested = Signal(int)
    seekRequested = Signal(float, int)

    def __init__(self, seg_idx, start_time, end_time, comment_text, quote_text="", parent=None):
        super().__init__(parent)
        self.seg_idx = seg_idx
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.setObjectName("comment_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        time_str = f"[{format_time(self.start_time)} - {format_time(self.end_time)}]"
        self.time_lbl = QLabel(f"<b>{time_str}</b>", self)
        self.time_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
        header_layout.addWidget(self.time_lbl)
        header_layout.addStretch()

        self.edit_btn = QToolButton(self)
        self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("Edit comment")
        self.edit_btn.setStyleSheet("border: none; padding: 2px;")
        self.edit_btn.clicked.connect(lambda: self.editRequested.emit(self.seg_idx))
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QToolButton(self)
        self.delete_btn.setText("🗑️")
        self.delete_btn.setToolTip("Delete comment")
        self.delete_btn.setStyleSheet("border: none; padding: 2px; color: #ef4444;")
        self.delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.seg_idx))
        header_layout.addWidget(self.delete_btn)
        layout.addLayout(header_layout)

        if quote_text and quote_text.strip():
            esc_q = quote_text.strip()
            if len(esc_q) > 90:
                esc_q = esc_q[:87] + "..."
            self.quote_lbl = QLabel(f'<i>"{esc_q}"</i>', self)
            self.quote_lbl.setWordWrap(True)
            self.quote_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; margin-bottom: 2px;")
            layout.addWidget(self.quote_lbl)

        self.comment_lbl = QLabel(comment_text, self)
        self.comment_lbl.setWordWrap(True)
        self.comment_lbl.setStyleSheet("font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.comment_lbl)

        self.set_selected(False)

    def set_selected(self, is_selected=True, theme="dark"):
        """Apply distinct active/selected visual indication to card."""
        self._is_selected = is_selected
        if is_selected:
            if theme == "light":
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: #fef08a;
                        border: 2px solid #ca8a04;
                        border-left: 6px solid #a16207;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: rgba(250, 204, 21, 0.35);
                        border: 2px solid #f59e0b;
                        border-left: 6px solid #d97706;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                """)
        else:
            if theme == "light":
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: #fef9c3;
                        border: 1px solid #fde047;
                        border-left: 4px solid #eab308;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                    QFrame#comment_card:hover {
                        background-color: #fef08a;
                        border-color: #ca8a04;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: rgba(254, 240, 138, 0.08);
                        border: 1px solid rgba(234, 179, 8, 0.35);
                        border-left: 4px solid #eab308;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                    QFrame#comment_card:hover {
                        background-color: rgba(254, 240, 138, 0.16);
                        border-color: #eab308;
                    }
                """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.seekRequested.emit(self.start_time, self.seg_idx)
            event.accept()
            return
        super().mousePressEvent(event)


class CommentsPanel(QWidget):
    """Collapsible docked Comments Sidebar / Pane sitting beside the transcript view."""
    commentSeekRequested = Signal(float, int)
    commentEditRequested = Signal(int)
    commentDeleteRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("comments_panel")
        self.setMinimumWidth(220)
        self.setMaximumWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 4)
        self.title_lbl = QLabel("<b>💬 Comments (0)</b>", self)
        self.title_lbl.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        self.add_btn = QToolButton(self)
        self.add_btn.setText("+ Add")
        self.add_btn.setToolTip("Add comment to current transcript selection (Ctrl+M)")
        self.add_btn.setStyleSheet("padding: 2px 6px; font-weight: bold;")
        self.add_btn.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self.add_btn)

        self.close_btn = QToolButton(self)
        self.close_btn.setText("✕")
        self.close_btn.setToolTip("Close Comments Sidebar (Ctrl+Alt+C)")
        self.close_btn.setStyleSheet("border: none; padding: 2px 4px; color: #94a3b8;")
        self.close_btn.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # Scroll area for cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_widget)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # Empty state label
        self.empty_lbl = QLabel(
            "No comments yet.\n\nHighlight text in the transcript and select '💬 Add Comment' to annotate.",
            self
        )
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 24px 12px;")
        main_layout.addWidget(self.empty_lbl)

    def _on_add_clicked(self):
        win = self.window()
        if hasattr(win, "add_comment_from_selection"):
            win.add_comment_from_selection()
        elif hasattr(win, "transcript_view"):
            cursor = win.transcript_view.textCursor()
            seg_idx = win.transcript_view.get_segment_index_at_cursor(cursor)
            if seg_idx is not None and hasattr(win, "edit_segment_comment_dialog"):
                win.edit_segment_comment_dialog(seg_idx)

    def _on_close_clicked(self):
        win = self.window()
        if hasattr(win, "toggle_show_comments"):
            win.toggle_show_comments(False)
        else:
            self.hide()

    def set_comments(self, segments):
        """Populate the comment cards from transcript segments."""
        # Clear existing card widgets
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        comment_count = 0
        if segments:
            for idx, seg in enumerate(segments):
                c_text = seg.get("comments") or seg.get("notes", "")
                if c_text and c_text.strip():
                    comment_count += 1
                    quote = seg.get("comment_selected_text") or seg.get("text", "")
                    card = CommentCardWidget(
                        seg_idx=idx,
                        start_time=seg.get("start", 0.0),
                        end_time=seg.get("end", 0.0),
                        comment_text=c_text.strip(),
                        quote_text=quote,
                        parent=self.scroll_widget
                    )
                    card.seekRequested.connect(self.commentSeekRequested.emit)
                    card.editRequested.connect(self.commentEditRequested.emit)
                    card.deleteRequested.connect(self.commentDeleteRequested.emit)
                    self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self.title_lbl.setText(f"<b>💬 Comments ({comment_count})</b>")
        if comment_count > 0:
            self.empty_lbl.hide()
            self.scroll_area.show()
        else:
            self.empty_lbl.show()
            self.scroll_area.hide()

    def highlight_segment(self, target_seg_idx):
        """Visually flash/highlight a specific comment card."""
        main_win = self.window()
        theme = getattr(main_win, "current_theme", "dark")
        for i in range(self.cards_layout.count() - 1):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), CommentCardWidget):
                card = item.widget()
                is_sel = (target_seg_idx is not None and card.seg_idx == target_seg_idx)
                card.set_selected(is_sel, theme)
                if is_sel:
                    self.scroll_area.ensureWidgetVisible(card)


class TranscriptSelectionBubble(QFrame):
    """Floating quick-action toolbar on transcript selection (Milestone 3.12)."""
    playRequested = Signal()
    storyRequested = Signal()
    cutRequested = Signal()
    exportRequested = Signal()
    commentRequested = Signal()
    noteRequested = Signal()  # alias for backward compatibility

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("transcript_selection_bubble")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self.play_btn = QToolButton(self)
        self.play_btn.setText("▶ Play")
        self.play_btn.setToolTip("Preview audio for this selection (Space)")
        self.play_btn.clicked.connect(self.playRequested.emit)
        layout.addWidget(self.play_btn)

        self.story_btn = QToolButton(self)
        self.story_btn.setText("+ Story")
        self.story_btn.setToolTip("Create a new story cut from highlighted text (Enter)")
        self.story_btn.clicked.connect(self.storyRequested.emit)
        layout.addWidget(self.story_btn)

        self.comment_btn = QToolButton(self)
        self.comment_btn.setText("💬 Comment")
        self.comment_btn.setToolTip("Add comment to highlighted section (Ctrl+M)")
        self.comment_btn.clicked.connect(self._emit_comment)
        layout.addWidget(self.comment_btn)

        self.note_btn = self.comment_btn  # alias

        self.cut_btn = QToolButton(self)
        self.cut_btn.setText("✂ Exclude")
        self.cut_btn.setToolTip("Exclude or cut this range")
        self.cut_btn.clicked.connect(self.cutRequested.emit)
        layout.addWidget(self.cut_btn)

        self.export_btn = QToolButton(self)
        self.export_btn.setText("⚡ Export")
        self.export_btn.setToolTip("Quick export selection as audio soundbite")
        self.export_btn.clicked.connect(self.exportRequested.emit)
        layout.addWidget(self.export_btn)

        self.setStyleSheet("""
            QFrame#transcript_selection_bubble {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
            }
            QToolButton {
                background-color: transparent;
                color: #f1f5f9;
                border: none;
                border-radius: 4px;
                padding: 4px 9px;
                font-size: 11px;
                font-weight: bold;
                min-width: 52px;
            }
            QToolButton:hover {
                background-color: #334155;
                color: #38bdf8;
            }
            QToolButton:pressed {
                background-color: #0f172a;
            }
        """)
        self.hide()

    def _emit_comment(self):
        self.commentRequested.emit()
        self.noteRequested.emit()
        self.hide()


class InteractiveTranscriptEdit(QTextEdit):
    linkClicked = Signal(QUrl)
    editingModeChanged = Signal(bool)
    formatChanged = Signal()
    requestInsertSpeaker = Signal(int, float, str)
    requestSplitAtCursor = Signal(int, float)
    requestRemoveSpeakerAtBlock = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.is_editing_mode = False
        self.setReadOnly(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAcceptDrops(True)

        self.current_theme = "dark"
        self.font_scale = 1.0
        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        self.anchor_ranges = {}
        self.time_anchor_index = []
        self.time_anchor_starts = []

        self.char_timestamp_map = []
        self._context_menu_cursor_position = None

        # Text selection state and preferences
        self.selection_mode = "replace"  # "replace" or "keep"
        self.saved_selections = []  # List of dicts for multi-selection mode
        self._is_left_down = False
        self._is_left_dragging = False
        self._left_press_pos = None
        self._pending_click_href = None
        self._is_right_down = False
        self._is_right_dragging = False
        self._right_press_pos = None
        self._right_press_cursor_pos = None
        self._suppress_next_context_menu = False

        # Floating Quick-Action Bubble (Milestone 3.12)
        self.selection_bubble = TranscriptSelectionBubble(self.viewport())
        self.selection_bubble.playRequested.connect(self._on_bubble_play)
        self.selection_bubble.storyRequested.connect(self._on_bubble_story)
        self.selection_bubble.noteRequested.connect(self._on_bubble_note)
        self.selection_bubble.cutRequested.connect(self._on_bubble_cut)
        self.selection_bubble.exportRequested.connect(self._on_bubble_export)
        self.selection_bubble.hide()

        self.apply_theme_style("dark")
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # Scroll stability & lock tracking
        self._is_scroll_locked = False
        self._scroll_lock_target_v = None
        self._scroll_lock_target_h = None
        self._scroll_lock_timer = None
        self._user_scrolled_recently = False

        if self.verticalScrollBar():
            self.verticalScrollBar().rangeChanged.connect(self._on_v_range_changed)
            self.verticalScrollBar().sliderPressed.connect(self._release_scroll_lock)

    def lock_scroll_position(self, v_val: int, h_val: int = 0, duration_ms: int = 400):
        """Pin vertical and horizontal scrollbars to exact pixel values during layout reflows.
        Automatically detaches when the layout stabilizes or when the user manually scrolls."""
        self._scroll_lock_target_v = max(0, int(v_val))
        self._scroll_lock_target_h = max(0, int(h_val))
        self._is_scroll_locked = True

        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()

        if v_bar:
            v_bar.setValue(self._scroll_lock_target_v)
        if h_bar:
            h_bar.setValue(self._scroll_lock_target_h)

        if not hasattr(self, "_scroll_lock_timer") or self._scroll_lock_timer is None:
            self._scroll_lock_timer = QTimer(self)
            self._scroll_lock_timer.setSingleShot(True)
            self._scroll_lock_timer.timeout.connect(self._release_scroll_lock)

        self._scroll_lock_timer.stop()
        self._scroll_lock_timer.start(max(50, int(duration_ms)))

    def _release_scroll_lock(self):
        self._is_scroll_locked = False
        self._scroll_lock_target_v = None
        self._scroll_lock_target_h = None

    def _on_v_range_changed(self, min_val, max_val):
        if getattr(self, "_is_scroll_locked", False) and self._scroll_lock_target_v is not None:
            v_bar = self.verticalScrollBar()
            if v_bar and v_bar.value() != self._scroll_lock_target_v:
                v_bar.setValue(self._scroll_lock_target_v)

    def focusInEvent(self, event):
        # Override QTextEdit's default focusInEvent which invokes ensureCursorVisible()
        # and causes unwanted viewport jumps when dialogs close.
        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()
        v_val = v_bar.value() if v_bar else 0
        h_val = h_bar.value() if h_bar else 0

        super().focusInEvent(event)

        if v_bar and v_bar.value() != v_val:
            v_bar.setValue(v_val)
        if h_bar and h_bar.value() != h_val:
            h_bar.setValue(h_val)

        # Defend against delayed Qt event-loop cursor visibility enforcement
        QTimer.singleShot(0, lambda: self._enforce_scroll_after_focus(v_val, h_val))

    def _enforce_scroll_after_focus(self, target_v: int, target_h: int):
        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()
        if v_bar and v_bar.value() != target_v and not getattr(self, "_user_scrolled_recently", False):
            v_bar.setValue(target_v)
        if h_bar and h_bar.value() != target_h and not getattr(self, "_user_scrolled_recently", False):
            h_bar.setValue(target_h)

    def wheelEvent(self, event):
        # Manual user scroll cancels any active scroll lock
        self._release_scroll_lock()
        self._user_scrolled_recently = True
        QTimer.singleShot(500, lambda: setattr(self, "_user_scrolled_recently", False))
        super().wheelEvent(event)

    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            main_win = self.window()
            show_highlights = str(getattr(main_win, "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
            if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
                cursor = self.cursorForPosition(e.pos())
                cpos = cursor.position()
                matching_span = None
                for span in self.comment_spans:
                    if span["start"] <= cpos <= span["end"]:
                        matching_span = span
                        break
                if matching_span:
                    st = matching_span.get("start_time", 0.0)
                    m, s = divmod(int(st), 60)
                    h, m = divmod(m, 60)
                    time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

                    quote_txt = matching_span.get("selected_text", "").strip()
                    if quote_txt:
                        trunc = quote_txt[:90] + ("..." if len(quote_txt) > 90 else "")
                        quote_html = (
                            f"<div style='font-size: 11px; color: #94a3b8; font-style: italic; margin-bottom: 5px; "
                            f"border-left: 2px solid #f59e0b; padding-left: 6px;'>&ldquo;{html.escape(trunc)}&rdquo;</div>"
                        )
                    else:
                        quote_html = ""

                    c_body = html.escape(matching_span.get("comment", ""))
                    is_light = getattr(self, "current_theme", "dark") == "light"
                    bg_col = "#ffffff" if is_light else "#0f172a"
                    text_col = "#0f172a" if is_light else "#f8fafc"
                    border_col = "#d97706" if is_light else "#f59e0b"

                    tooltip_html = (
                        f"<div style='background-color: {bg_col}; color: {text_col}; border: 1.5px solid {border_col}; "
                        f"border-radius: 6px; padding: 7px 11px; font-family: sans-serif; max-width: 360px;'>"
                        f"<div style='font-weight: bold; color: {border_col}; margin-bottom: 4px; font-size: 12px;'>"
                        f"💬 Comment &bull; {time_str}</div>"
                        f"{quote_html}"
                        f"<div style='white-space: pre-wrap; line-height: 1.4; font-size: 12px; margin-bottom: 6px;'>{c_body}</div>"
                        f"<div style='font-size: 10px; color: #64748b; border-top: 1px solid rgba(245, 158, 11, 0.3); padding-top: 3px;'>"
                        f"Click highlight to open comment window &bull; Spacebar to play</div>"
                        f"</div>"
                    )
                    pos = e.globalPos() if hasattr(e, "globalPos") else (e.globalPosition().toPoint() if hasattr(e, "globalPosition") else self.mapToGlobal(e.pos()))
                    QToolTip.showText(pos, tooltip_html, self.viewport())
                    return True
            QToolTip.hideText()
        return super().event(e)

    def _on_bubble_play(self):
        win = self.window()
        if hasattr(win, "play_active_transcript_selection"):
            win.play_active_transcript_selection()
        elif hasattr(win, "play_selection"):
            win.play_selection()

    def _on_bubble_story(self):
        win = self.window()
        if hasattr(win, "add_story_from_active_selection"):
            win.add_story_from_active_selection()
        self.selection_bubble.hide()

    def _on_bubble_note(self):
        win = self.window()
        if hasattr(win, "add_comment_from_selection"):
            win.add_comment_from_selection()
        elif hasattr(win, "edit_segment_comment_dialog"):
            cursor = self.textCursor()
            seg_idx = self.get_segment_index_at_cursor(cursor)
            if seg_idx is None:
                seg_idx = cursor.blockNumber()
            win.edit_segment_comment_dialog(seg_idx)
        elif hasattr(win, "add_note_dialog"):
            win.add_note_dialog()
        self.selection_bubble.hide()

    def _on_bubble_cut(self):
        win = self.window()
        if hasattr(win, "exclude_selection"):
            win.exclude_selection()
        self.selection_bubble.hide()

    def _on_bubble_export(self):
        win = self.window()
        if hasattr(win, "quick_export_selection"):
            win.quick_export_selection()
        self.selection_bubble.hide()

    def paintEvent(self, event):
        super().paintEvent(event)
        win = self.window()
        has_media = bool(getattr(win, "audio_file", None) or getattr(self, "audio_file", None))
        if has_media:
            return
        if self.document().isEmpty() or not self.toPlainText().strip():
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self.viewport().rect()

            card_w = min(460, rect.width() - 40)
            card_h = min(220, rect.height() - 40)
            if card_w > 120 and card_h > 80:
                card_x = rect.x() + (rect.width() - card_w) // 2
                card_y = rect.y() + (rect.height() - card_h) // 2
                card_rect = QRectF(card_x, card_y, card_w, card_h)

                is_dark = self.current_theme == "dark"
                pen = QPen(QColor("#3b82f6" if is_dark else "#2563eb"), 1.5, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                fill_color = QColor(30, 41, 59, 120) if is_dark else QColor(241, 245, 249, 180)
                painter.setBrush(fill_color)
                painter.drawRoundedRect(card_rect, 10.0, 10.0)

                title_font = QFont(self.font())
                title_font.setPointSize(12)
                title_font.setBold(True)
                painter.setFont(title_font)
                painter.setPen(QColor("#f8fafc" if is_dark else "#0f172a"))
                t_rect = QRectF(card_x + 16, card_y + 24, card_w - 32, 28)
                painter.drawText(t_rect, Qt.AlignmentFlag.AlignCenter, "Drop an Audio or Video File Here to Begin")

                sub_font = QFont(self.font())
                sub_font.setPointSize(9)
                painter.setFont(sub_font)
                painter.setPen(QColor("#94a3b8" if is_dark else "#64748b"))
                s_rect = QRectF(card_x + 16, card_y + 58, card_w - 32, 42)
                painter.drawText(s_rect, Qt.AlignmentFlag.AlignCenter, "Supports WAV, MP3, MP4, M4A, MKV, FLAC, and OGG\nAuto-generates synchronized word-level transcription")

                btn_font = QFont(self.font())
                btn_font.setPointSize(9)
                btn_font.setBold(True)
                painter.setFont(btn_font)
                btn_rect = QRectF(card_x + (card_w - 200) // 2, card_y + 115, 200, 32)
                painter.fillRect(btn_rect, QColor("#2563eb"))
                painter.setPen(QColor("#ffffff"))
                painter.drawRoundedRect(btn_rect, 5.0, 5.0)
                painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Open Media File... (Ctrl+O)")

                hint_font = QFont(self.font())
                hint_font.setPointSize(8)
                painter.setFont(hint_font)
                painter.setPen(QColor("#64748b"))
                h_rect = QRectF(card_x + 16, card_y + 155, card_w - 32, 24)
                painter.drawText(h_rect, Qt.AlignmentFlag.AlignCenter, "Or click File > Open Media in the menu bar")
            painter.end()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                if u.isLocalFile():
                    path = u.toLocalFile()
                    win = self.window()
                    if hasattr(win, "load_media_file"):
                        win.load_media_file(path)
                        event.acceptProposedAction()
                        return
        super().dropEvent(event)

    def set_selection_mode(self, mode):
        self.selection_mode = mode if mode in ("replace", "keep") else "replace"
        if self.selection_mode == "replace" and self.saved_selections:
            self.saved_selections = []
            self.update_extra_selections()

    def set_char_timestamp_map(self, mapping):
        self.char_timestamp_map = mapping

    def has_active_selection(self):
        cursor = self.textCursor()
        if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
            return True
        if getattr(self, "saved_selections", None) and len(self.saved_selections) > 0:
            return True
        return False

    def clear_all_selections(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.clearSelection()
            self.setTextCursor(cursor)
        self.saved_selections = []
        self.setExtraSelections([])
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()
        main_win = self.window()
        if hasattr(main_win, "timeline"):
            main_win.timeline.set_transcript_selection_range(None, None)
        if hasattr(main_win, "statusBar"):
            main_win.statusBar().showMessage("Cleared transcript selection.")

    def get_time_range_for_char_span(self, start_pos, end_pos):
        if not self.char_timestamp_map:
            return None
        s_pos = min(start_pos, end_pos)
        e_pos = max(start_pos, end_pos)
        overlaps = []
        for item in self.char_timestamp_map:
            if len(item) >= 4:
                a, b, ts_start, ts_end = item[0], item[1], item[2], item[3]
            else:
                a, b, ts_start = item
                ts_end = ts_start
            if b > s_pos and a < e_pos:
                overlaps.append((float(ts_start), float(ts_end)))
        if not overlaps:
            return None
        return min(x[0] for x in overlaps), max(x[1] for x in overlaps)

    def get_selected_time_range(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            s_pos = min(cursor.selectionStart(), cursor.selectionEnd())
            e_pos = max(cursor.selectionStart(), cursor.selectionEnd())
            res = self.get_time_range_for_char_span(s_pos, e_pos)
            if res is not None:
                return res
        if getattr(self, "saved_selections", None):
            return (
                min(s["start_time"] for s in self.saved_selections),
                max(s["end_time"] for s in self.saved_selections),
            )
        return None

    def get_all_selected_story_ranges(self):
        """Returns a list of dicts: [{'start_time': float, 'end_time': float, 'text': str, ...}, ...]"""
        if self.selection_mode == "keep" and self.saved_selections:
            return sorted(self.saved_selections, key=lambda x: x.get("start_time", 0.0))

        cursor = self.textCursor()
        if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
            s_pos = min(cursor.selectionStart(), cursor.selectionEnd())
            e_pos = max(cursor.selectionStart(), cursor.selectionEnd())
            t_range = self.get_time_range_for_char_span(s_pos, e_pos)
            if not t_range:
                main_win = self.window()
                st = getattr(main_win, "current_position", 0.0)
                t_range = (st, st + 5.0)
            return [{
                "start_char": s_pos,
                "end_char": e_pos,
                "start_time": t_range[0],
                "end_time": t_range[1],
                "text": cursor.selectedText().strip(),
            }]
        return []

    def select_comment_range(self, seg_idx):
        """Navigate and select the exact comment text range in the transcript view."""
        main_win = self.window()
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript
        if not t_data or not isinstance(t_data, dict) or "segments" not in t_data:
            return
        segments = t_data.get("segments", [])
        if not (0 <= seg_idx < len(segments)):
            return
        seg = segments[seg_idx]
        c_selected = (seg.get("comment_selected_text") or "").strip()
        c_start = seg.get("comment_char_start")
        c_end = seg.get("comment_char_end")

        doc = self.document()
        doc_text = doc.toPlainText()
        positions = None
        if c_selected:
            pos_in_doc = doc_text.find(c_selected)
            if pos_in_doc >= 0:
                positions = (pos_in_doc, pos_in_doc + len(c_selected))
            else:
                block = doc.findBlockByNumber(seg_idx)
                if block.isValid():
                    block_text = block.text()
                    pos_in_block = block_text.find(c_selected)
                    if pos_in_block >= 0:
                        start_p = block.position() + pos_in_block
                        positions = (start_p, start_p + len(c_selected))
        if not positions and c_start is not None and c_end is not None and c_end > c_start and c_end <= doc.characterCount():
            positions = (c_start, c_end)

        if not positions:
            block = doc.findBlockByNumber(seg_idx)
            if block.isValid():
                positions = (block.position(), block.position() + max(1, block.length() - 1))

        if positions:
            cursor = QTextCursor(doc)
            cursor.setPosition(positions[0])
            cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self.setFocus()

    def update_extra_selections(self):
        extras = []
        main_win = self.window()
        self.comment_spans = []
        show_highlights = str(getattr(main_win, "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}

        # Amber / Yellow Comment Highlights (Word & Google Docs Style)
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript
        if t_data and isinstance(t_data, dict) and "segments" in t_data:
            segments = t_data.get("segments", [])
            doc = self.document()
            doc_text = doc.toPlainText()
            seen_spans = set()
            for idx, seg in enumerate(segments):
                comment_text = seg.get("comments") or seg.get("notes", "")
                if comment_text and comment_text.strip():
                    c_start = seg.get("comment_char_start")
                    c_end = seg.get("comment_char_end")
                    c_selected = (seg.get("comment_selected_text") or "").strip()

                    span_key = (comment_text.strip(), c_selected, c_start, c_end)
                    if span_key in seen_spans:
                        continue
                    seen_spans.add(span_key)

                    positions = None
                    if c_selected:
                        pos_in_doc = doc_text.find(c_selected)
                        if pos_in_doc >= 0:
                            positions = (pos_in_doc, pos_in_doc + len(c_selected))
                        else:
                            block = doc.findBlockByNumber(idx)
                            if block.isValid():
                                block_text = block.text()
                                pos_in_block = block_text.find(c_selected)
                                if pos_in_block >= 0:
                                    start_p = block.position() + pos_in_block
                                    positions = (start_p, start_p + len(c_selected))

                    if not positions and c_start is not None and c_end is not None and c_end > c_start and c_end <= doc.characterCount():
                        positions = (c_start, c_end)

                    if not positions:
                        target_anchor = f"seg_{idx}"
                        positions = self.anchor_ranges.get(target_anchor)
                        if not positions:
                            block = doc.findBlockByNumber(idx)
                            if block.isValid():
                                positions = (block.position(), block.position() + max(1, block.length() - 1))

                    if positions:
                        # Always register span for hover tooltips and click navigation
                        self.comment_spans.append({
                            "start": positions[0],
                            "end": positions[1],
                            "seg_idx": idx,
                            "comment": comment_text.strip(),
                            "selected_text": c_selected,
                            "start_time": float(seg.get("start", 0.0)),
                            "end_time": float(seg.get("end", 0.0)),
                        })

                        # Amber highlight extra selection (toggled by Show/Hide Highlights)
                        if show_highlights:
                            comment_fmt = QTextCharFormat()
                            if getattr(self, "current_theme", "dark") == "light":
                                comment_fmt.setBackground(QColor(254, 240, 138, 220))  # Warm amber highlight
                                comment_fmt.setForeground(QColor(133, 77, 14))
                            else:
                                comment_fmt.setBackground(QColor(133, 77, 14, 200))  # Dark warm amber highlight
                                comment_fmt.setForeground(QColor(254, 240, 138))
                            comment_cursor = QTextCursor(doc)
                            comment_cursor.setPosition(positions[0])
                            comment_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
                            extra = QTextEdit.ExtraSelection()
                            extra.format = comment_fmt
                            extra.cursor = comment_cursor
                            extras.append(extra)

        if hasattr(self, "saved_selections") and self.saved_selections:
            fmt = QTextCharFormat()
            if getattr(self, "current_theme", "dark") == "light":
                fmt.setBackground(QColor(186, 215, 255, 170))
                fmt.setForeground(QColor(15, 23, 42))
            else:
                fmt.setBackground(QColor(40, 105, 215, 170))
                fmt.setForeground(QColor(255, 255, 255))

            for sel in self.saved_selections:
                extra = QTextEdit.ExtraSelection()
                extra.format = fmt
                cursor = QTextCursor(self.document())
                cursor.setPosition(sel["start_char"])
                cursor.setPosition(sel["end_char"], QTextCursor.MoveMode.KeepAnchor)
                extra.cursor = cursor
                extras.append(extra)

        if getattr(self, "_playback_highlight_selection", None) is not None:
            extras.append(self._playback_highlight_selection)

        self.setExtraSelections(extras)

    def _on_selection_completed(self, cursor):
        if not cursor.hasSelection():
            return
        start_char = min(cursor.selectionStart(), cursor.selectionEnd())
        end_char = max(cursor.selectionStart(), cursor.selectionEnd())
        if end_char <= start_char:
            return

        t_range = self.get_time_range_for_char_span(start_char, end_char)
        if not t_range:
            main_win = self.window()
            start_t = getattr(main_win, "current_position", 0.0)
            end_t = start_t + 5.0
            t_range = (start_t, end_t)

        selected_text = cursor.selectedText().strip()

        if self.selection_mode == "keep":
            # Multi-selection mode: accumulate selections without clearing previous ones
            merged = False
            for s in self.saved_selections:
                if not (end_char < s["start_char"] or start_char > s["end_char"]):
                    s["start_char"] = min(s["start_char"], start_char)
                    s["end_char"] = max(s["end_char"], end_char)
                    merged_tr = self.get_time_range_for_char_span(s["start_char"], s["end_char"])
                    if merged_tr:
                        s["start_time"], s["end_time"] = merged_tr
                    c = QTextCursor(self.document())
                    c.setPosition(s["start_char"])
                    c.setPosition(s["end_char"], QTextCursor.MoveMode.KeepAnchor)
                    s["text"] = c.selectedText().strip()
                    merged = True
                    break
            if not merged:
                self.saved_selections.append({
                    "start_char": start_char,
                    "end_char": end_char,
                    "start_time": t_range[0],
                    "end_time": t_range[1],
                    "text": selected_text
                })

            # Clear active cursor selection so extraSelections render clearly
            temp_cursor = QTextCursor(cursor)
            temp_cursor.clearSelection()
            self.setTextCursor(temp_cursor)
            self.update_extra_selections()

            main_win = self.window()
            if hasattr(main_win, "statusBar"):
                count = len(self.saved_selections)
                main_win.statusBar().showMessage(f"Selected {count} sections. Right-click or click 'Add Story' to save.")
        else:
            # Single selection mode: replace previous selection
            self.saved_selections = []
            self.setExtraSelections([])
            main_win = self.window()
            if hasattr(main_win, "timeline") and t_range:
                main_win.timeline.set_transcript_selection_range(t_range[0], t_range[1])
            if hasattr(main_win, "statusBar") and t_range:
                main_win.statusBar().showMessage(f"Transcript selection: {format_time(t_range[0])} – {format_time(t_range[1])}")

        main_win = self.window()
        show_floating = str(getattr(main_win, "show_floating_selection_toolbar", getattr(self, "show_floating_selection_toolbar", True))).lower() in {"1", "true", "yes"}
        if hasattr(self, "selection_bubble") and not self.is_editing_mode and show_floating:
            c_rect = self.cursorRect(cursor)
            bubble_hint = self.selection_bubble.sizeHint()
            b_w = max(336, bubble_hint.width() + 16)
            b_h = max(34, bubble_hint.height())
            bx = max(8, min(self.viewport().width() - b_w - 8, c_rect.center().x() - b_w // 2))
            by = max(4, c_rect.top() - b_h - 6)
            self.selection_bubble.setFixedSize(b_w, b_h)
            self.selection_bubble.setGeometry(bx, by, b_w, b_h)
            self.selection_bubble.show()
            self.selection_bubble.raise_()
        elif hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

    def apply_theme_style(self, mode):
        self.current_theme = mode
        self.setStyleSheet(transcript_text_view_stylesheet(mode, 14 * self.font_scale))
        self.update_extra_selections()

    def set_font_scale(self, scale):
        """Set transcript font scale without affecting the rest of the UI."""
        self.font_scale = max(0.80, min(1.80, float(scale)))
        # Update the widget font as well as its stylesheet so QTextDocument's
        # inherited HTML text follows the scale consistently.
        font = QFont(self.font())
        font.setPointSizeF(16.0 * self.font_scale * 72.0 / 96.0)
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.setStyleSheet(transcript_text_view_stylesheet(self.current_theme, 14 * self.font_scale))
        self.update_extra_selections()

    def set_editing_mode(self, enabled):
        if self.is_editing_mode == enabled:
            return
        self.is_editing_mode = enabled
        self.setReadOnly(not enabled)
        if enabled:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.clear_highlight()
            self.setFocus()
        else:
            self.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
        self.editingModeChanged.emit(enabled)

    def toggle_bold(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        curr_weight = self.fontWeight()
        new_weight = QFont.Weight.Normal if curr_weight > QFont.Weight.Medium else QFont.Weight.Bold
        fmt.setFontWeight(new_weight)
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_italic(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.fontItalic())
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_underline(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.fontUnderline())
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_strikethrough(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        is_strike = self.currentCharFormat().fontStrikeOut()
        fmt.setFontStrikeOut(not is_strike)
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_highlight(self, color_name="#fef08a", force_apply=False):
        """Toggle or change color of rich highlighting on active text selection or contiguous highlighted region."""
        cursor = self.textCursor()
        main_win = self.window()
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        cur_fmt = self.currentCharFormat()
        curr_bg = cur_fmt.background().color()
        has_active_highlight = (
            cur_fmt.background().style() != Qt.BrushStyle.NoBrush
            and curr_bg.isValid()
            and curr_bg.alpha() > 0
            and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
        )

        target_color = QColor(color_name)
        target_hex = target_color.name().lower()

        # If already highlighted with exact same color and force_apply is False, toggle it off
        if has_active_highlight and not force_apply and curr_bg.name().lower() == target_hex:
            self.remove_highlight()
            return

        # 1. Update underlying transcript data model (for both View and Edit modes)
        segs = main_win.transcript.get("segments", []) if (hasattr(main_win, "transcript") and main_win.transcript) else []

        target_segs = set()
        if cursor.hasSelection():
            sel_start = min(cursor.selectionStart(), cursor.selectionEnd())
            sel_end = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self, "get_time_range_for_char_span"):
                t_range = self.get_time_range_for_char_span(sel_start, sel_end)
                if t_range and t_range[0] is not None and t_range[1] is not None:
                    st, et = t_range
                    for i, s in enumerate(segs):
                        s_st = s.get("start", 0.0)
                        s_et = s.get("end", 0.0)
                        if s_st <= et and s_et >= st:
                            target_segs.add(i)

        if not target_segs:
            c_seg = self.get_segment_index_at_cursor(cursor)
            if c_seg is not None and 0 <= c_seg < len(segs):
                target_segs.add(c_seg)
            else:
                blk = cursor.blockNumber()
                if 0 <= blk < len(segs):
                    target_segs.add(blk)

        # Build flattened word list to identify contiguous highlighted regions
        flat_words = []
        for s_idx, seg in enumerate(segs):
            if not isinstance(seg, dict):
                continue
            seg_hl = seg.get("highlight")
            words = seg.get("words", [])
            if isinstance(words, list) and words:
                for w_idx, w in enumerate(words):
                    if isinstance(w, dict):
                        w_hl = w.get("highlight") or seg_hl
                        is_hl = bool(w_hl and w_hl not in (False, "false", "False", 0, None))
                        flat_words.append({
                            "seg_idx": s_idx,
                            "word_idx": w_idx,
                            "word_dict": w,
                            "seg_dict": seg,
                            "is_hl": is_hl
                        })
            else:
                text = seg.get("text", "")
                for w_idx, word_str in enumerate(text.split()):
                    is_hl = bool(seg_hl and seg_hl not in (False, "false", "False", 0, None))
                    flat_words.append({
                        "seg_idx": s_idx,
                        "word_idx": w_idx,
                        "word_dict": None,
                        "seg_dict": seg,
                        "is_hl": is_hl
                    })

        total_words = len(flat_words)
        targeted_flat_indices = set()
        for idx, fw in enumerate(flat_words):
            if fw["seg_idx"] in target_segs:
                targeted_flat_indices.add(idx)

        # Expand backwards and forwards across contiguous highlighted word blocks to recolor full region
        indices_to_recolor = set()
        for t_idx in targeted_flat_indices:
            if 0 <= t_idx < total_words:
                if flat_words[t_idx]["is_hl"]:
                    start_i = t_idx
                    while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                        start_i -= 1
                    end_i = t_idx
                    while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                        end_i += 1
                    for k in range(start_i, end_i + 1):
                        indices_to_recolor.add(k)
                elif cursor.hasSelection():
                    indices_to_recolor.add(t_idx)

        # If user clicked near a highlighted region (e.g. adjacent word boundary)
        if not indices_to_recolor and targeted_flat_indices:
            for t_idx in targeted_flat_indices:
                for offset in (-1, 1, -2, 2):
                    adj = t_idx + offset
                    if 0 <= adj < total_words and flat_words[adj]["is_hl"]:
                        start_i = adj
                        while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                            start_i -= 1
                        end_i = adj
                        while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                            end_i += 1
                        for k in range(start_i, end_i + 1):
                            indices_to_recolor.add(k)

        # Apply new highlight color to targeted data words & segments
        affected_segs = set()
        if indices_to_recolor:
            for k in indices_to_recolor:
                fw = flat_words[k]
                if fw["word_dict"]:
                    fw["word_dict"]["highlight"] = target_hex
                affected_segs.add(fw["seg_idx"])
            for s_idx in affected_segs:
                seg = segs[s_idx]
                seg["highlight"] = target_hex
        else:
            for s_idx in target_segs:
                if 0 <= s_idx < len(segs):
                    seg = segs[s_idx]
                    seg["highlight"] = target_hex
                    if "words" in seg and isinstance(seg["words"], list):
                        for w in seg["words"]:
                            if isinstance(w, dict):
                                w["highlight"] = target_hex

        # 2. Update QTextCharFormat on editor / view
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(target_color))
        fmt.setForeground(QBrush(QColor("#0f172a")))

        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)

        if hasattr(main_win, "mark_project_dirty"):
            main_win.mark_project_dirty()

        # Re-render transcript view so HTML reflects updated colors in both View and Edit modes
        if hasattr(main_win, "render_transcript"):
            main_win.render_transcript()

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Change Highlight Color")

        self.setFocus()
        self.formatChanged.emit()
        self.update_extra_selections()

    def remove_highlight(self):
        """Removes background highlighting for the entire contiguous highlighted section(s) intersecting active selection or cursor."""
        cursor = self.textCursor()
        main_win = self.window()

        # Capture baseline for universal undo / redo history
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None
        segs = main_win.transcript.get("segments", []) if (hasattr(main_win, "transcript") and main_win.transcript) else []

        # 1. Determine target segment index/indices from selection or cursor position
        target_segs = set()
        if cursor.hasSelection():
            sel_start = min(cursor.selectionStart(), cursor.selectionEnd())
            sel_end = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self, "get_time_range_for_char_span"):
                t_range = self.get_time_range_for_char_span(sel_start, sel_end)
                if t_range and t_range[0] is not None and t_range[1] is not None:
                    st, et = t_range
                    for i, s in enumerate(segs):
                        s_st = s.get("start", 0.0)
                        s_et = s.get("end", 0.0)
                        if s_st <= et and s_et >= st:
                            target_segs.add(i)

        if not target_segs:
            c_seg = self.get_segment_index_at_cursor(cursor)
            if c_seg is not None and 0 <= c_seg < len(segs):
                target_segs.add(c_seg)
            else:
                blk = cursor.blockNumber()
                if 0 <= blk < len(segs):
                    target_segs.add(blk)

        # 2. Build flattened word list to identify contiguous highlighted regions
        flat_words = []
        for s_idx, seg in enumerate(segs):
            if not isinstance(seg, dict):
                continue
            seg_hl = seg.get("highlight")
            words = seg.get("words", [])
            if isinstance(words, list) and words:
                for w_idx, w in enumerate(words):
                    if isinstance(w, dict):
                        w_hl = w.get("highlight") or seg_hl
                        is_hl = bool(w_hl and w_hl not in (False, "false", "False", 0, None))
                        flat_words.append({
                            "seg_idx": s_idx,
                            "word_idx": w_idx,
                            "word_dict": w,
                            "seg_dict": seg,
                            "is_hl": is_hl
                        })
            else:
                text = seg.get("text", "")
                for w_idx, word_str in enumerate(text.split()):
                    is_hl = bool(seg_hl and seg_hl not in (False, "false", "False", 0, None))
                    flat_words.append({
                        "seg_idx": s_idx,
                        "word_idx": w_idx,
                        "word_dict": None,
                        "seg_dict": seg,
                        "is_hl": is_hl
                    })

        total_words = len(flat_words)
        targeted_flat_indices = set()
        for idx, fw in enumerate(flat_words):
            if fw["seg_idx"] in target_segs:
                targeted_flat_indices.add(idx)

        # 3. Expand backwards and forwards across contiguous highlighted word blocks
        indices_to_clear = set()
        for t_idx in targeted_flat_indices:
            if 0 <= t_idx < total_words and flat_words[t_idx]["is_hl"]:
                start_i = t_idx
                while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                    start_i -= 1
                end_i = t_idx
                while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                    end_i += 1
                for k in range(start_i, end_i + 1):
                    indices_to_clear.add(k)

        # If user clicked near a highlighted region (e.g. adjacent space or word boundary)
        if not indices_to_clear and targeted_flat_indices:
            for t_idx in targeted_flat_indices:
                for offset in (-1, 1, -2, 2):
                    adj = t_idx + offset
                    if 0 <= adj < total_words and flat_words[adj]["is_hl"]:
                        start_i = adj
                        while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                            start_i -= 1
                        end_i = adj
                        while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                            end_i += 1
                        for k in range(start_i, end_i + 1):
                            indices_to_clear.add(k)

        # 4. Clear highlight on all contiguous words and clean up segment metadata
        if not indices_to_clear:
            for s_idx in target_segs:
                if 0 <= s_idx < len(segs):
                    seg = segs[s_idx]
                    seg.pop("highlight", None)
                    if "words" in seg and isinstance(seg["words"], list):
                        for w in seg["words"]:
                            if isinstance(w, dict):
                                w.pop("highlight", None)
        else:
            affected_segs = set()
            for k in indices_to_clear:
                fw = flat_words[k]
                if fw["word_dict"]:
                    fw["word_dict"].pop("highlight", None)
                affected_segs.add(fw["seg_idx"])

            for s_idx in affected_segs:
                seg = segs[s_idx]
                words = seg.get("words", [])
                if isinstance(words, list):
                    has_remaining_hl = any(
                        isinstance(w, dict) and bool(w.get("highlight"))
                        for w in words
                    )
                    if not has_remaining_hl:
                        seg.pop("highlight", None)
                else:
                    seg.pop("highlight", None)

        # Clear character format background brush on cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.setCurrentCharFormat(fmt)

        if hasattr(main_win, "mark_project_dirty"):
            main_win.mark_project_dirty()

        # Re-render transcript to reflect exact updated state
        if hasattr(main_win, "render_transcript"):
            main_win.render_transcript()

        # Commit project state change for undo stack
        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Remove Highlight")

        self.formatChanged.emit()
        self.update_extra_selections()

    def clear_formatting(self):
        cursor = self.textCursor()
        main_win = self.window()
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        fmt.setForeground(QBrush(Qt.BrushStyle.NoBrush))
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.setCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.setCurrentCharFormat(fmt)

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Clear Formatting")

        self.setFocus()
        self.formatChanged.emit()

    def get_current_formatting(self):
        fmt = self.currentCharFormat()
        bg = fmt.background().color()
        has_highlight = bg.isValid() and bg.alpha() > 0 and fmt.background().style() != Qt.BrushStyle.NoBrush
        return {
            "bold": fmt.fontWeight() > QFont.Weight.Medium,
            "italic": fmt.fontItalic(),
            "underline": fmt.fontUnderline(),
            "strike": fmt.fontStrikeOut(),
            "highlight": has_highlight,
        }

    def mousePressEvent(self, event):
        if self.is_editing_mode:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            self._left_press_pos = pos
            self._is_left_down = True
            self._is_left_dragging = False
            self._pending_click_href = None

            # Check if clicked on a timestamp/word link
            hit_cursor = self.cursorForPosition(pos)
            href = hit_cursor.charFormat().anchorHref()
            if not href and hit_cursor.position() > 0:
                probe = QTextCursor(hit_cursor)
                probe.setPosition(max(0, hit_cursor.position() - 1))
                href = probe.charFormat().anchorHref()

            if href and (href.startswith("word:") or href.startswith("time:") or href.startswith("speaker:")):
                self._pending_click_href = href

            if self.selection_mode == "replace" and self.saved_selections:
                self.saved_selections = []
                self.update_extra_selections()

            super().mousePressEvent(event)
            return

        elif event.button() == Qt.MouseButton.RightButton:
            self._right_press_pos = pos
            self._is_right_down = True
            self._is_right_dragging = False
            self._right_press_cursor_pos = self.cursorForPosition(pos).position()
            self._suppress_next_context_menu = False
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_editing_mode:
            super().mouseMoveEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        drag_dist = QApplication.startDragDistance() if hasattr(QApplication, "startDragDistance") else 4
        if drag_dist < 4:
            drag_dist = 4

        if getattr(self, "_is_left_down", False):
            press_pos = getattr(self, "_left_press_pos", pos)
            if (pos - press_pos).manhattanLength() >= drag_dist:
                self._is_left_dragging = True
            super().mouseMoveEvent(event)
            return

        if getattr(self, "_is_right_down", False):
            press_pos = getattr(self, "_right_press_pos", pos)
            if (pos - press_pos).manhattanLength() >= drag_dist:
                self._is_right_dragging = True
                curr_pos = self.cursorForPosition(pos).position()
                start_pos = getattr(self, "_right_drag_start_cursor_pos", curr_pos)

                cursor = QTextCursor(self.document())
                cursor.setPosition(start_pos)
                cursor.setPosition(curr_pos, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                event.accept()
                return

        # Passive Hover: cursor shape indicator over comment highlights
        hit_cursor = self.cursorForPosition(pos)
        hit_pos = hit_cursor.position()
        over_comment = False
        show_highlights = str(getattr(self.window(), "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
        if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
            for span in self.comment_spans:
                if span["start"] <= hit_pos <= span["end"]:
                    over_comment = True
                    break
        if over_comment:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            href = hit_cursor.charFormat().anchorHref()
            if not href:
                self.viewport().unsetCursor()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        if not getattr(self, "is_editing_mode", False):
            self.viewport().unsetCursor()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_editing_mode:
            super().mouseReleaseEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = getattr(self, "_is_left_dragging", False)
            self._is_left_down = False
            self._is_left_dragging = False
            pending_href = getattr(self, "_pending_click_href", None)
            self._pending_click_href = None

            super().mouseReleaseEvent(event)

            cursor = self.textCursor()
            has_sel = cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0)

            if not was_dragging and not has_sel:
                # Single Left-Click without dragging -> check for comment highlight or seek/navigation
                if self.selection_mode == "replace":
                    self.clear_all_selections()

                hit_cursor = self.cursorForPosition(pos)
                hit_pos = hit_cursor.position()
                clicked_span = None
                show_highlights = str(getattr(self.window(), "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
                if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
                    for span in self.comment_spans:
                        if span["start"] <= hit_pos <= span["end"]:
                            clicked_span = span
                            break

                if clicked_span:
                    main_win = self.window()
                    # 1. Open the comments window/pane if closed
                    if hasattr(main_win, "toggle_show_comments"):
                        main_win.toggle_show_comments(True)
                    # 2. Highlight and scroll to this comment card in comments panel
                    if hasattr(main_win, "comments_panel") and hasattr(main_win.comments_panel, "highlight_segment"):
                        main_win.comments_panel.highlight_segment(clicked_span["seg_idx"])
                    # 3. Seek to time position WITHOUT starting playback
                    seek_time = clicked_span["start_time"]
                    if hasattr(main_win, "seek_to"):
                        main_win.seek_to(seek_time)
                    if hasattr(main_win, "timeline") and hasattr(main_win.timeline, "ensure_position_visible"):
                        main_win.timeline.ensure_position_visible(seek_time)
                    event.accept()
                    return

                if pending_href and (pending_href.startswith("word:") or pending_href.startswith("time:") or pending_href.startswith("speaker:")):
                    self.linkClicked.emit(QUrl(pending_href))
                    event.accept()
                    return
                else:
                    href = hit_cursor.charFormat().anchorHref()
                    if href and (href.startswith("word:") or href.startswith("time:") or href.startswith("speaker:")):
                        self.linkClicked.emit(QUrl(href))
                        event.accept()
                        return
            else:
                # Left-drag selection completed
                if has_sel:
                    self._on_selection_completed(cursor)
                event.accept()
                return

        elif event.button() == Qt.MouseButton.RightButton:
            was_right_dragging = getattr(self, "_is_right_dragging", False)
            self._is_right_down = False
            self._is_right_dragging = False

            if was_right_dragging:
                self._suppress_next_context_menu = True
                cursor = self.textCursor()
                if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
                    self._on_selection_completed(cursor)
                event.accept()
                return
            else:
                self._suppress_next_context_menu = False
                self.show_context_menu(pos)
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def _nearest_word_anchor(self, cursor):
        """Return the word anchor nearest the actual QTextDocument cursor."""
        pos = cursor.position()
        best = None
        best_distance = None
        for href, (start_pos, end_pos) in self.anchor_ranges.items():
            if not href.startswith("word:"):
                continue
            if start_pos <= pos <= end_pos:
                distance = 0
            elif pos < start_pos:
                distance = start_pos - pos
            else:
                distance = pos - end_pos
            if best_distance is None or distance < best_distance:
                parts = href.split(":")
                if len(parts) >= 3 and parts[2].isdigit():
                    try:
                        best = (float(parts[1]), int(parts[2]), href)
                        best_distance = distance
                    except ValueError:
                        pass

        # Fallback to char_timestamp_map if anchor_ranges has no match
        if best is None and getattr(self, "char_timestamp_map", None):
            for entry in self.char_timestamp_map:
                c_start, c_end = entry[0], entry[1]
                ts = entry[2]
                s_idx = entry[4] if len(entry) >= 5 else None
                if c_start <= pos <= c_end and s_idx is not None:
                    return (float(ts), int(s_idx), f"word:{ts}:{s_idx}")

        return best

    def get_timestamp_at_cursor(self, cursor):
        nearest = self._nearest_word_anchor(cursor)
        if nearest is not None:
            return nearest[0]
        # Search the current block in the document for any anchor
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            pass
            it += 1
        main_win = self.window()
        return getattr(main_win, "current_position", 0.0)

    def get_block_start_timestamp(self, cursor):
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            pass
            it += 1
        return self.get_timestamp_at_cursor(cursor)

    def get_block_end_timestamp(self, cursor):
        block = cursor.block()
        last_ts = None
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            last_ts = float(parts[1])
                        except ValueError:
                            pass
            it += 1
        if last_ts is not None:
            return last_ts
        return self.get_timestamp_at_cursor(cursor)

    def get_segment_index_at_cursor(self, cursor):
        nearest = self._nearest_word_anchor(cursor)
        if nearest is not None:
            return nearest[1]
        # Search current block for segment index
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 3 and parts[2].isdigit():
                        return int(parts[2])
                elif href and href.startswith("speaker:"):
                    parts = href.split(":")
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
            it += 1
        return None

    def move_cursor_to_segment_start(self, seg_idx):
        """Best-effort: places the caret at the first word of seg_idx after
        a render_transcript() refresh, so editing can continue in place."""
        target_href = None
        for _start, _end, href in self.time_anchor_index:
            if href.endswith(f":{seg_idx}"):
                target_href = href
                break
        if not target_href:
            return
        positions = self.anchor_ranges.get(target_href)
        if not positions:
            return
        cursor = QTextCursor(self.document())
        cursor.setPosition(positions[0])
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def keyPressEvent(self, event):
        # The application owns undo/redo for project edits.  Do this before
        # QTextEdit's native undo stack so Ctrl+Z / Ctrl+Shift+Z is consistent
        # with speaker-label, story and other project-state operations.
        if event.matches(QKeySequence.StandardKey.Undo):
            main_win = self.window()
            if hasattr(main_win, "flush_pending_transcript_undo"):
                main_win.flush_pending_transcript_undo()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.undo()
                event.accept()
                return
        if event.matches(QKeySequence.StandardKey.Redo):
            main_win = self.window()
            if hasattr(main_win, "flush_pending_transcript_undo"):
                main_win.flush_pending_transcript_undo()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.redo()
                event.accept()
                return

        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))
        is_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        key = event.key()

        # Add / Edit Comment shortcut (Ctrl+M, Ctrl+Alt+M)
        if (is_ctrl and key == Qt.Key.Key_M and not is_shift and not is_alt) or \
           (is_ctrl and is_alt and key == Qt.Key.Key_M):
            main_win = self.window()
            if hasattr(main_win, "add_comment_from_selection"):
                main_win.add_comment_from_selection()
                event.accept()
                return
            elif hasattr(main_win, "edit_segment_comment_dialog"):
                cursor = self.textCursor()
                seg_idx = self.get_segment_index_at_cursor(cursor)
                if seg_idx is None:
                    seg_idx = cursor.blockNumber()
                main_win.edit_segment_comment_dialog(seg_idx)
                event.accept()
                return

        # Toggle Comments Sidebar shortcut (Ctrl+Alt+C or Alt+5)
        if (is_ctrl and is_alt and key == Qt.Key.Key_C and not is_shift) or \
           (is_alt and key == Qt.Key.Key_5 and not is_ctrl and not is_shift):
            main_win = self.window()
            if hasattr(main_win, "toggle_comments_panel"):
                main_win.toggle_comments_panel()
                event.accept()
                return

        if self.is_editing_mode:
            if is_ctrl and not is_shift and not is_alt:
                if key == Qt.Key.Key_B:
                    self.toggle_bold()
                    event.accept()
                    return
                elif key == Qt.Key.Key_I:
                    self.toggle_italic()
                    event.accept()
                    return
                elif key == Qt.Key.Key_U:
                    self.toggle_underline()
                    event.accept()
                    return
                elif key == Qt.Key.Key_K:
                    self.toggle_strikethrough()
                    event.accept()
                    return
                elif key in (Qt.Key.Key_Backslash, Qt.Key.Key_Space):
                    self.clear_formatting()
                    event.accept()
                    return
            elif is_ctrl and is_shift and not is_alt:
                if key in (Qt.Key.Key_X, Qt.Key.Key_S):
                    self.toggle_strikethrough()
                    event.accept()
                    return

        if self.is_editing_mode and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()

            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter: add a speaker label break (split the segment here).
                seg_idx = self.get_segment_index_at_cursor(cursor)
                if seg_idx is None:
                    seg_idx = cursor.blockNumber()
                split_time = self.get_timestamp_at_cursor(cursor)
                self.requestSplitAtCursor.emit(seg_idx, split_time)
                event.accept()
                return

            ts = self.get_timestamp_at_cursor(cursor)
            time_str = format_time(ts)

            cursor.insertBlock()

            ts_html = (
                f'<a href="time:{ts}" style="color:#8b949e !important; text-decoration:none;">'
                f'<b>{time_str}</b></a>&nbsp;'
            )
            cursor.insertHtml(ts_html)
            event.accept()
            return

        if self.is_editing_mode and event.key() == Qt.Key.Key_Backspace and self.textCursor().atBlockStart():
            cursor = self.textCursor()
            seg_idx = self.get_segment_index_at_cursor(cursor)
            if seg_idx is not None and seg_idx > 0:
                self.requestRemoveSpeakerAtBlock.emit(seg_idx)
                event.accept()
                return

        if event.key() == Qt.Key.Key_Escape:
            if self.has_active_selection():
                self.clear_all_selections()
                event.accept()
                return
            if self.is_editing_mode:
                self.set_editing_mode(False)
                event.accept()
                return

        if event.matches(QKeySequence.StandardKey.Find):
            main_win = self.window()
            if hasattr(main_win, "open_find_replace"):
                main_win.open_find_replace()
                event.accept()
                return

        if not self.is_editing_mode and event.key() in (
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown
        ):
            main_win = self.window()
            skip_sec = float(getattr(main_win, "skip_seconds", 5.0) or 5.0)
            cursor = self.textCursor()
            key = event.key()

            if key == Qt.Key.Key_Home:
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                t = self.get_block_start_timestamp(cursor)
                if t is not None and hasattr(main_win, "seek_to"):
                    main_win.seek_to(t)
                event.accept()
                return
            elif key == Qt.Key.Key_End:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                t = self.get_block_end_timestamp(cursor)
                if t is not None and hasattr(main_win, "seek_to"):
                    main_win.seek_to(t)
                event.accept()
                return
            elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
                if hasattr(main_win, "seek_relative"):
                    main_win.last_position_source = "transcript"
                    main_win.seek_relative(-skip_sec)
                    if hasattr(main_win, "transcript") and hasattr(self, "move_cursor_to_time"):
                        self.move_cursor_to_time(getattr(main_win, "current_position", 0.0), main_win.transcript)
                event.accept()
                return
            elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
                if hasattr(main_win, "seek_relative"):
                    main_win.last_position_source = "transcript"
                    main_win.seek_relative(skip_sec)
                    if hasattr(main_win, "transcript") and hasattr(self, "move_cursor_to_time"):
                        self.move_cursor_to_time(getattr(main_win, "current_position", 0.0), main_win.transcript)
                event.accept()
                return

        super().keyPressEvent(event)

    def show_context_menu(self, position):
        """Context menu for both viewing and editing modes.  Speaker labels
        are interactive targets, while right-clicking anywhere else offers a
        speaker insertion at the nearest transcript timestamp.
        """
        if getattr(self, "_suppress_next_context_menu", False):
            self._suppress_next_context_menu = False
            return

        hit_cursor = self.cursorForPosition(position)
        href = hit_cursor.charFormat().anchorHref()
        if not href and hit_cursor.position() > 0:
            probe = QTextCursor(hit_cursor)
            probe.setPosition(max(0, hit_cursor.position() - 1))
            href = probe.charFormat().anchorHref()

        speaker_target = None
        if href and href.startswith("speaker:"):
            parts = href.split(":", 2)
            if len(parts) >= 3 and parts[1].isdigit():
                speaker_target = (int(parts[1]), parts[2])

        # Preserve active text selection when right-clicking so the user can easily
        # add the selection to a story, play it, or clear it from the context menu.
        if not self.has_active_selection():
            self.setTextCursor(hit_cursor)

        # Store the exact document position that opened the menu.  QAction
        # execution can otherwise move the QTextCursor, which used to make a
        # speaker insertion land at an unrelated earlier timestamp.
        self._context_menu_cursor_position = hit_cursor.position()

        menu = self.createStandardContextMenu() if self.is_editing_mode else QMenu(self)
        main_win = self.window()

        if self.has_active_selection():
            ranges = self.get_all_selected_story_ranges()
            count = len(ranges)
            title = f"Add Selected Sections to New Stories ({count})" if count > 1 else "Add Selected Text to New Story"
            add_selection = QAction(title, self)
            add_selection.triggered.connect(lambda: main_win.add_selection_to_story())
            menu.addAction(add_selection)

            play_selection = QAction("Play Selected Text", self)
            play_selection.triggered.connect(lambda: main_win.play_transcript_selection())
            menu.addAction(play_selection)

            clear_selection = QAction("Clear Selection", self)
            clear_selection.setShortcut(QKeySequence("Esc"))
            clear_selection.triggered.connect(self.clear_all_selections)
            menu.addAction(clear_selection)

            menu.addSeparator()

        # Speaker controls are deliberately available in BOTH modes.
        if speaker_target:
            seg_idx, raw_speaker = speaker_target
            
            change_menu = menu.addMenu("Change Speaker To")
            known_speakers = []
            if hasattr(main_win, "get_all_known_speakers"):
                known_speakers = main_win.get_all_known_speakers()
            for spk in known_speakers:
                action = change_menu.addAction(spk)
                action.triggered.connect(
                    lambda _, i=seg_idx, s=raw_speaker, name=spk: main_win.execute_speaker_rename(i, s, name)
                )
            change_menu.addSeparator()
            new_change_action = change_menu.addAction("Add New Speaker...")
            new_change_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.execute_speaker_rename(i, s, "__NEW__")
            )

            remove_action = QAction("Remove Speaker Label", self)
            remove_action.setEnabled(seg_idx > 0)
            remove_action.triggered.connect(
                lambda _, i=seg_idx: main_win.remove_speaker_label_at_segment(i)
            )
            menu.addAction(remove_action)
            menu.addSeparator()

        insert_menu = menu.addMenu("Add Speaker Label Here")
        target_cursor = hit_cursor
        target_seg_idx = self.get_segment_index_at_cursor(target_cursor)
        if target_seg_idx is None:
            target_seg_idx = target_cursor.blockNumber()
        target_time = self.get_timestamp_at_cursor(target_cursor)

        known_speakers = []
        if hasattr(main_win, "get_all_known_speakers"):
            known_speakers = main_win.get_all_known_speakers()
        for spk in known_speakers:
            action = insert_menu.addAction(spk)
            action.triggered.connect(
                lambda _, s=target_seg_idx, t=target_time, name=spk: self.requestInsertSpeaker.emit(s, t, name)
            )
        insert_menu.addSeparator()
        new_spk_action = insert_menu.addAction("Add New Speaker...")
        new_spk_action.triggered.connect(
            lambda _, s=target_seg_idx, t=target_time: self.requestInsertSpeaker.emit(s, t, "__NEW__")
        )

        if hasattr(main_win, "open_speaker_manager_dialog"):
            manage_spk_act = QAction("Manage Speakers & Detection Clusters...", self)
            manage_spk_act.triggered.connect(main_win.open_speaker_manager_dialog)
            menu.addAction(manage_spk_act)
            menu.addSeparator()

        target_seg = self.get_segment_index_at_cursor(hit_cursor)
        if target_seg is None:
            target_seg = hit_cursor.blockNumber()
        has_comment = False
        if hasattr(main_win, "transcript") and main_win.transcript:
            segs = main_win.transcript.get("segments", [])
            if 0 <= target_seg < len(segs):
                has_comment = bool(segs[target_seg].get("comments") or segs[target_seg].get("notes"))
        comment_title = "💬 Edit Comment..." if has_comment else "💬 Add Comment..."

        if not self.is_editing_mode:
            add_vocab = QAction("Add Selected Text to Glossary", menu)
            add_vocab.setEnabled(self.has_active_selection())
            def _add_vocab_from_selection():
                ranges = self.get_all_selected_story_ranges()
                txt = ranges[0]["text"] if ranges else self.textCursor().selectedText()
                main_win.add_to_glossary(txt)
            add_vocab.triggered.connect(_add_vocab_from_selection)
            menu.addAction(add_vocab)

            edit_comment_act = QAction(f"{comment_title}\tCtrl+M", menu)
            edit_comment_act.triggered.connect(
                lambda _, s=target_seg: getattr(
                    main_win, "add_comment_from_selection",
                    lambda: getattr(main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None))(s)
                )() if self.has_active_selection() else getattr(
                    main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None)
                )(s)
            )
            menu.addAction(edit_comment_act)

            if has_comment:
                del_comment_act = QAction("🗑️ Delete Comment", menu)
                del_comment_act.triggered.connect(
                    lambda _, s=target_seg: getattr(main_win, "delete_segment_comment", lambda x: None)(s)
                )
                menu.addAction(del_comment_act)

            cur_fmt = hit_cursor.charFormat() if hit_cursor else self.currentCharFormat()
            curr_bg = cur_fmt.background().color()
            active_hl_hex = None
            if (
                cur_fmt.background().style() != Qt.BrushStyle.NoBrush
                and curr_bg.isValid()
                and curr_bg.alpha() > 0
                and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
            ):
                active_hl_hex = curr_bg.name().lower()

            if not active_hl_hex and hasattr(main_win, "transcript") and main_win.transcript:
                segs = main_win.transcript.get("segments", [])
                target_seg_i = self.get_segment_index_at_cursor(hit_cursor)
                if target_seg_i is not None and 0 <= target_seg_i < len(segs):
                    seg = segs[target_seg_i]
                    s_hl = seg.get("highlight")
                    if s_hl and s_hl not in (False, "false", "False", 0, None):
                        active_hl_hex = "#fef08a" if isinstance(s_hl, bool) else str(s_hl).lower()

            hl_title = "🎨 Change Highlight Color" if active_hl_hex else "🖊️ Highlight Text"

            hl_colors = [
                ("🟡 Yellow", "#fef08a"),
                ("🟢 Green", "#bbf7d0"),
                ("🔵 Blue / Cyan", "#bae6fd"),
                ("🌸 Pink", "#fbcfe8"),
                ("🟠 Orange", "#fed7aa"),
                ("🟣 Purple", "#e9d5ff"),
            ]

            hl_menu = menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            hl_menu.addSeparator()
            act_rem_hl = hl_menu.addAction("⚪ Remove Highlight")
            act_rem_hl.triggered.connect(self.remove_highlight)

            toggle_comments_act = QAction("💬 Toggle Comments Sidebar\tCtrl+Alt+C", menu)
            toggle_comments_act.triggered.connect(lambda: getattr(main_win, "toggle_comments_panel", lambda: None)())
            menu.addAction(toggle_comments_act)

            menu.addSeparator()
            edit_action = QAction("Edit Transcript\tF2", menu)
            edit_action.triggered.connect(lambda: self.set_editing_mode(True))
            menu.addAction(edit_action)
        else:
            fmt_menu = menu.addMenu("Format Text")
            act_bold = fmt_menu.addAction("Bold\tCtrl+B")
            act_bold.triggered.connect(self.toggle_bold)

            act_italic = fmt_menu.addAction("Italic\tCtrl+I")
            act_italic.triggered.connect(self.toggle_italic)

            act_underline = fmt_menu.addAction("Underline\tCtrl+U")
            act_underline.triggered.connect(self.toggle_underline)

            act_strike = fmt_menu.addAction("Strikethrough\tCtrl+K")
            act_strike.triggered.connect(self.toggle_strikethrough)

            fmt_menu.addSeparator()

            cur_fmt = hit_cursor.charFormat() if hit_cursor else self.currentCharFormat()
            curr_bg = cur_fmt.background().color()
            active_hl_hex = None
            if (
                cur_fmt.background().style() != Qt.BrushStyle.NoBrush
                and curr_bg.isValid()
                and curr_bg.alpha() > 0
                and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
            ):
                active_hl_hex = curr_bg.name().lower()

            if not active_hl_hex and hasattr(main_win, "transcript") and main_win.transcript:
                segs = main_win.transcript.get("segments", [])
                target_seg_i = self.get_segment_index_at_cursor(hit_cursor)
                if target_seg_i is not None and 0 <= target_seg_i < len(segs):
                    seg = segs[target_seg_i]
                    s_hl = seg.get("highlight")
                    if s_hl and s_hl not in (False, "false", "False", 0, None):
                        active_hl_hex = "#fef08a" if isinstance(s_hl, bool) else str(s_hl).lower()

            hl_title = "🎨 Change Highlight Color" if active_hl_hex else "🖊️ Highlight Text"

            hl_menu = fmt_menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            hl_menu.addSeparator()
            act_rem_hl = hl_menu.addAction("⚪ Remove Highlight")
            act_rem_hl.triggered.connect(self.remove_highlight)

            act_clear = fmt_menu.addAction("Clear Formatting\tCtrl+\\")
            act_clear.triggered.connect(self.clear_formatting)

            menu.addSeparator()
            edit_comment_act = QAction(f"{comment_title}\tCtrl+M", menu)
            edit_comment_act.triggered.connect(
                lambda _, s=target_seg: getattr(
                    main_win, "add_comment_from_selection",
                    lambda: getattr(main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None))(s)
                )() if self.textCursor().hasSelection() else getattr(
                    main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None)
                )(s)
            )
            menu.addAction(edit_comment_act)

            if has_comment:
                del_comment_act = QAction("🗑️ Delete Comment", menu)
                del_comment_act.triggered.connect(
                    lambda _, s=target_seg: getattr(main_win, "delete_segment_comment", lambda x: None)(s)
                )
                menu.addAction(del_comment_act)

            rem_hl_act = QAction("🎨 Remove Highlight", menu)
            rem_hl_act.triggered.connect(self.remove_highlight)
            menu.addAction(rem_hl_act)

            toggle_comments_act = QAction("💬 Toggle Comments Sidebar\tCtrl+Alt+C", menu)
            toggle_comments_act.triggered.connect(lambda: getattr(main_win, "toggle_comments_panel", lambda: None)())
            menu.addAction(toggle_comments_act)

            menu.addSeparator()
            find_action = QAction("Find and Replace...\tCtrl+F", menu)
            find_action.triggered.connect(lambda: main_win.open_find_replace())
            menu.addAction(find_action)

            menu.addSeparator()
            exit_action = QAction("View Transcript\tF2", menu)
            exit_action.triggered.connect(lambda: self.set_editing_mode(False))
            menu.addAction(exit_action)

        menu.exec(self.mapToGlobal(position))

    def rebuild_anchor_index(self):
        """Index transcript anchors once so playback highlighting is O(1) lookup."""
        self.anchor_ranges = {}
        doc = self.document()
        block = doc.begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    href = fragment.charFormat().anchorHref()
                    if href:
                        self.anchor_ranges[href] = (
                            fragment.position(),
                            fragment.position() + fragment.length(),
                        )
                it += 1
            block = block.next()

    def set_time_anchor_index(self, entries):
        self.time_anchor_index = sorted(entries, key=lambda item: item[0])
        self.time_anchor_starts = [item[0] for item in self.time_anchor_index]

    def clear_highlight(self):
        if not self.active_highlight_anchor and getattr(self, "_playback_highlight_selection", None) is None:
            return

        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        self.update_extra_selections()

    def highlight_word_at_time(self, seconds, transcript_data, auto_scroll: bool = False):
        if self.is_editing_mode or not transcript_data:
            return

        target_anchor = None
        if self.time_anchor_index:
            idx = bisect_right(self.time_anchor_starts, seconds) - 1
            if idx >= 0:
                start_time, end_time, anchor = self.time_anchor_index[idx]
                # Allow a small tolerance window or match if within the timestamp block
                if start_time <= seconds <= end_time or (seconds - end_time) < 0.3:
                    target_anchor = anchor
            elif self.time_anchor_starts and seconds < self.time_anchor_starts[0]:
                target_anchor = self.time_anchor_index[0][2]

        if not target_anchor or target_anchor == self.active_highlight_anchor:
            return

        doc = self.document()
        positions = self.anchor_ranges.get(target_anchor)
        if not positions:
            self.rebuild_anchor_index()
            positions = self.anchor_ranges.get(target_anchor)

        if not positions:
            self.clear_highlight()
            return

        target_cursor = QTextCursor(doc)
        target_cursor.setPosition(positions[0])
        target_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)

        # Overlay Word Highlighting using QTextEdit.ExtraSelection
        # Prevents document mutations and expensive text reflows during playback
        highlight_fmt = QTextCharFormat()
        if self.current_theme == "light":
            highlight_fmt.setForeground(QColor("#0056b3"))
            highlight_fmt.setBackground(QColor(186, 215, 255, 120))
        elif self.current_theme == "high_contrast":
            highlight_fmt.setForeground(QColor("#ffff00"))
            highlight_fmt.setBackground(QColor(255, 255, 0, 80))
        else:
            highlight_fmt.setForeground(QColor("#58a6ff"))
            highlight_fmt.setBackground(QColor(88, 166, 255, 75))
        highlight_fmt.setFontWeight(QFont.Weight.Bold)

        extra = QTextEdit.ExtraSelection()
        extra.format = highlight_fmt
        extra.cursor = target_cursor

        self.active_highlight_anchor = target_anchor
        self._playback_highlight_selection = extra
        self.update_extra_selections()

# ============================================================
# Document Reading Utilities
# ============================================================

def read_document_text(path: Path) -> str:
    ext = path.suffix.lower()

    if ext == ".docx":
        if not DOCX_AVAILABLE or Document is None:
            raise ImportError("python-docx is required to read .docx files")
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    elif ext == ".pdf":
        text_pages = []
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_pages.append(extracted)
            return "\n".join(text_pages)
        except ImportError:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(str(path))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_pages.append(extracted)
                return "\n".join(text_pages)
            except ImportError:
                try:
                    import pdfplumber
                    with pdfplumber.open(str(path)) as pdf:
                        for page in pdf.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text_pages.append(extracted)
                    return "\n".join(text_pages)
                except ImportError:
                    raise RuntimeError(
                        "PDF support requires 'pypdf'. Install it with:\npip install pypdf"
                    )

    elif ext in (".html", ".htm"):
        try:
            raw_html = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_html = path.read_text(encoding="utf-8-sig", errors="ignore")

        class HTMLTextParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.pieces = []
            def handle_data(self, data):
                self.pieces.append(data)

        parser = HTMLTextParser()
        parser.feed(raw_html)
        return "".join(parser.pieces)

    else:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                return path.read_text(encoding="latin-1", errors="replace")


# ============================================================
# Story Auto-Detection VAD Worker
# ============================================================

class StoryAutoDetectWorker(QObject):
    finished = Signal(list)
    progress = Signal((str, int), (str,))
    error = Signal(str)

    # Filter out Whisper music notes and non-speech sound tags
    MUSIC_TOKEN_RE = re.compile(
        r"^([♪♫♬\s]+|\[(?:music|applause|laughter|cheering|sound|singing|theme)\]|\((?:music|applause|laughter|singing)\))$",
        re.IGNORECASE
    )

    def __init__(
        self,
        audio_file,
        silence_threshold=3.0,
        lead_in_padding=0.5,
        audio_duration=0,
        transcript_segments=None,
        whisper_model="parakeet-onnx",
        detection_mode="voice",
        **kwargs,
    ):
        super().__init__()
        self.audio_file = str(audio_file)
        self.silence_threshold = float(silence_threshold or 3.0)
        self.lead_in_padding = float(lead_in_padding or 0.5)
        self.audio_duration = float(audio_duration or 0.0)
        self.transcript_segments = transcript_segments or []
        self.whisper_model = whisper_model or "parakeet-onnx"
        self.detection_mode = str(detection_mode or "voice").strip().lower()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _emit_progress(self, message: str, percent: int = 0):
        if self._is_cancelled:
            return
        pct = max(0, min(100, int(percent)))
        try:
            self.progress.emit(str(message), pct)
        except Exception:
            try:
                self.progress.emit(str(message))
            except Exception:
                pass
        try:
            self.progress[str].emit(str(message))
        except Exception:
            pass

    def _is_real_speech(self, text: str) -> bool:
        txt = str(text).strip()
        if not txt or self.MUSIC_TOKEN_RE.match(txt):
            return False
        if all(ch in "♪♫♬ \t\r\n" for ch in txt):
            return False
        return True

    def run(self):
        try:
            if self._is_cancelled:
                self.error.emit("Process canceled by user.")
                return

            detected_stories = []

            if not self.audio_file or not os.path.isfile(self.audio_file):
                raise FileNotFoundError(f"Audio file not found: {self.audio_file}")

            self._emit_progress("[Step 1/2] Detecting speech activity...", 25)

            speech_timestamps = None
            total_dur = self.audio_duration

            # Step 1: Read and normalize audio to 16kHz mono float32
            audio_data = None
            sample_rate = 16000

            try:
                setup_windows_dll_directories()
                import soundfile as sf
                audio_data, file_sr = sf.read(str(self.audio_file), dtype="float32")
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=-1)
                sample_rate = file_sr
            except Exception:
                # Fallback to FFmpeg decode if soundfile cannot read container/codec
                try:
                    import subprocess
                    import numpy as np
                    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
                    cmd = [
                        ffmpeg_bin, "-y", "-v", "error",
                        "-i", str(self.audio_file),
                        "-vn", "-sn", "-dn",
                        "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"
                    ]
                    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                    if p.returncode == 0 and len(p.stdout) > 0:
                        audio_data = np.frombuffer(p.stdout, dtype=np.float32)
                        sample_rate = 16000
                except Exception:
                    pass

            if audio_data is not None and len(audio_data) > 0:
                if sample_rate != 16000:
                    try:
                        from scipy.signal import resample_poly
                        from math import gcd
                        g = gcd(sample_rate, 16000)
                        audio_data = resample_poly(audio_data, 16000 // g, sample_rate // g).astype("float32")
                        sample_rate = 16000
                    except Exception:
                        pass

                total_dur = max(float(len(audio_data)) / 16000.0, self.audio_duration)

                # Try Neural Silero VAD (ONNX or Torch)
                try:
                    import torch
                    import numpy as np
                    from silero_vad import load_silero_vad, get_speech_timestamps
                    try:
                        if isinstance(audio_data, np.ndarray):
                            if not audio_data.flags.writeable or not audio_data.flags.c_contiguous:
                                audio_data = np.ascontiguousarray(audio_data, dtype=np.float32).copy()
                        wav = torch.from_numpy(audio_data)
                    except (RuntimeError, UserWarning, AttributeError, Exception):
                        try:
                            wav = torch.as_tensor(audio_data, dtype=torch.float32)
                        except (RuntimeError, UserWarning, AttributeError, Exception):
                            wav = torch.tensor(audio_data.tolist(), dtype=torch.float32)
                    try:
                        vad_model = load_silero_vad(onnx=True)
                    except Exception:
                        vad_model = load_silero_vad()

                    speech_timestamps = get_speech_timestamps(
                        wav,
                        vad_model,
                        sampling_rate=16000,
                        min_speech_duration_ms=250,
                        min_silence_duration_ms=400,
                        return_seconds=True,
                    )
                except Exception as vad_err:
                    self._emit_progress(
                        f"[Step 1/2] Neural voice detection unavailable ({type(vad_err).__name__}: {vad_err}); "
                        "falling back to a lower-accuracy volume-based detector for this file. "
                        "Background music or noise may prevent story breaks from being detected correctly.",
                        30,
                    )
                    # Pure NumPy / SciPy acoustic energy envelope fallback (no neural deps needed)
                    try:
                        import numpy as np
                        chunk_size = int(16000 * 0.1)  # 100ms frames
                        num_chunks = len(audio_data) // chunk_size
                        if num_chunks > 0:
                            chunks = audio_data[:num_chunks * chunk_size].reshape(num_chunks, chunk_size)
                            rms = np.sqrt(np.mean(chunks ** 2, axis=1) + 1e-12)
                            db = 20 * np.log10(rms + 1e-12)
                            silence_thresh_db = np.percentile(db, 20) + 6.0
                            is_speech = db > silence_thresh_db

                            raw_intervals = []
                            in_speech = False
                            start_f = 0
                            for f_idx, val in enumerate(is_speech):
                                if val and not in_speech:
                                    in_speech = True
                                    start_f = f_idx
                                elif not val and in_speech:
                                    in_speech = False
                                    raw_intervals.append({
                                        "start": round(start_f * 0.1, 2),
                                        "end": round(f_idx * 0.1, 2)
                                    })
                            if in_speech:
                                raw_intervals.append({
                                    "start": round(start_f * 0.1, 2),
                                    "end": round(num_chunks * 0.1, 2)
                                })
                            speech_timestamps = raw_intervals
                    except Exception:
                        pass

            if not speech_timestamps and self.transcript_segments:
                speech_timestamps = []
                for seg in self.transcript_segments:
                    text = seg.get("text", "")
                    if self._is_real_speech(text):
                        speech_timestamps.append({
                            "start": float(seg.get("start", 0.0)),
                            "end": float(seg.get("end", 0.0)),
                        })

            if self.detection_mode == "music":
                self._emit_progress("[Step 2/2] Detecting songs and track boundaries...", 80)
                # Music Mode: Detect song segments separated by non-musical transitions
                # (silence, dialog-only speech, or non-musical sounds lasting >= silence_threshold).
                music_hint_intervals = []
                if self.transcript_segments:
                    for seg in self.transcript_segments:
                        txt = seg.get("text", "")
                        st = float(seg.get("start", 0.0))
                        et = float(seg.get("end", 0.0))
                        if not self._is_real_speech(txt):
                            music_hint_intervals.append((st, et))

                frame_dur = 0.5
                num_frames = int(max(1, math.ceil(total_dur / frame_dur))) if total_dur > 0 else 0
                frame_is_music = [False] * num_frames

                if audio_data is not None and len(audio_data) > 0 and sample_rate > 0:
                    samples_per_frame = int(sample_rate * frame_dur)
                    rms_list = []
                    try:
                        import numpy as np
                        has_np = isinstance(audio_data, np.ndarray)
                    except Exception:
                        has_np = False

                    for f in range(num_frames):
                        s_idx = f * samples_per_frame
                        e_idx = min(len(audio_data), (f + 1) * samples_per_frame)
                        chunk = audio_data[s_idx:e_idx]
                        if len(chunk) > 0:
                            if has_np:
                                rms_val = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
                            else:
                                rms_val = math.sqrt(sum(float(x) ** 2 for x in chunk) / len(chunk) + 1e-12)
                            rms_list.append(rms_val)
                        else:
                            rms_list.append(0.0)

                    sorted_rms = sorted(rms_list)
                    silence_rms = sorted_rms[int(len(sorted_rms) * 0.12)] if sorted_rms else 0.001
                    silence_rms = max(silence_rms, 0.002)

                    window_radius = 2  # +/- 2 frames = 2.0s rolling window
                    for f in range(num_frames):
                        f_start = f * frame_dur
                        f_end = (f + 1) * frame_dur
                        f_rms = rms_list[f] if f < len(rms_list) else 0.0

                        if f_rms < silence_rms:
                            frame_is_music[f] = False
                            continue

                        in_speech = False
                        if speech_timestamps:
                            in_speech = any(
                                not (f_end <= sp["start"] or f_start >= sp["end"])
                                for sp in speech_timestamps
                            )

                        w_start = max(0, f - window_radius)
                        w_end = min(num_frames, f + window_radius + 1)
                        w_vals = rms_list[w_start:w_end]
                        min_w = min(w_vals) if w_vals else 0.0
                        max_w = max(w_vals) if w_vals else 1.0
                        valley_ratio = min_w / (max_w + 1e-6)

                        has_music_hint = any(
                            not (f_end <= mh[0] or f_start >= mh[1])
                            for mh in music_hint_intervals
                        )

                        if has_music_hint:
                            frame_is_music[f] = True
                        elif not in_speech:
                            # Sustained non-speech acoustic energy -> music instrumental/song
                            frame_is_music[f] = True
                        else:
                            # Speech active: check if accompanied by continuous musical rhythm
                            frame_is_music[f] = bool(valley_ratio >= 0.22)

                elif music_hint_intervals:
                    for f in range(num_frames):
                        f_start = f * frame_dur
                        f_end = (f + 1) * frame_dur
                        frame_is_music[f] = any(
                            not (f_end <= mh[0] or f_start >= mh[1])
                            for mh in music_hint_intervals
                        )

                min_break_frames = max(2, int(round(float(self.silence_threshold) / frame_dur)))
                music_intervals = []
                in_music = False
                seg_start_f = 0
                non_music_gap_count = 0

                for f_idx, is_mus in enumerate(frame_is_music):
                    if is_mus:
                        if not in_music:
                            in_music = True
                            seg_start_f = f_idx
                        non_music_gap_count = 0
                    else:
                        if in_music:
                            non_music_gap_count += 1
                            if non_music_gap_count >= min_break_frames:
                                seg_end_f = f_idx - non_music_gap_count + 1
                                music_intervals.append((
                                    round(seg_start_f * frame_dur, 2),
                                    round(seg_end_f * frame_dur, 2)
                                ))
                                in_music = False
                                non_music_gap_count = 0

                if in_music:
                    music_intervals.append((
                        round(seg_start_f * frame_dur, 2),
                        round(len(frame_is_music) * frame_dur, 2)
                    ))

                for idx, (mst, met) in enumerate(music_intervals):
                    st = max(0.0, mst - self.lead_in_padding)
                    et = min(total_dur, met + min(0.3, self.lead_in_padding))
                    if et - st >= 5.0:
                        detected_stories.append(Story(
                            start=round(st, 2),
                            end=round(et, 2),
                            title=f"Song {len(detected_stories) + 1}"
                        ))

            # Voice Mode or fallback if no music intervals detected
            if not detected_stories and speech_timestamps:
                self._emit_progress("[Step 2/2] Assembling stories from vocal intervals...", 85)
                story_starts = [max(0.0, speech_timestamps[0]["start"] - self.lead_in_padding)]
                story_ends = []
                target_gap = max(1.0, float(self.silence_threshold))

                for i in range(len(speech_timestamps) - 1):
                    if self._is_cancelled:
                        self.error.emit("Process canceled by user.")
                        return

                    curr_speech_end = speech_timestamps[i]["end"]
                    next_speech_start = speech_timestamps[i + 1]["start"]
                    gap = next_speech_start - curr_speech_end

                    if gap >= target_gap:
                        story_ends.append(curr_speech_end + min(0.3, self.lead_in_padding))
                        story_starts.append(max(0.0, next_speech_start - self.lead_in_padding))

                story_ends.append(max(float(speech_timestamps[-1]["end"]), total_dur))

                for idx, (st, et) in enumerate(zip(story_starts, story_ends)):
                    if et - st >= 3.0:  # Minimum story duration filter
                        detected_stories.append(Story(
                            start=round(st, 2),
                            end=round(et, 2),
                            title=f"Story {len(detected_stories) + 1}"
                        ))

            if not detected_stories and total_dur > 0:
                detected_stories = [Story(start=0.0, end=round(total_dur, 2), title="Story 1")]

            self._emit_progress("Story detection complete.", 100)
            self.finished.emit(detected_stories)

        except Exception as exc:
            if not self._is_cancelled:
                self.error.emit(str(exc))

# ============================================================
# Transcription worker
# ============================================================

# Transcription is executed by the same isolated local helper process used
# for Speaker Detection. This keeps ML model loading out of the Qt GUI process.



# ============================================================
# Speaker diarization worker
# ============================================================



# ============================================================
# Waveform Extraction Worker & Binary Peak Cache (.peaks)
# ============================================================

PEAKS_MAGIC = b"RTVSPEAK"
PEAKS_VERSION = 1

def get_waveform_peak_cache_path(audio_file, project_file=None):
    """
    Return local project or appdata path for waveform peak binary cache file.
    Prefers project-local hidden cache <Project>/.cache/peaks/<media_stem>.peaks,
    falling back to user appdata cache. Never creates .cache inside standalone media folders.
    """
    if not audio_file:
        return None
    try:
        audio_p = Path(audio_file).resolve()
        
        # 1. If explicit project_file provided, store in project folder's .cache/peaks/
        if project_file:
            proj_p = Path(project_file).resolve()
            proj_dir = proj_p.parent if (proj_p.is_file() or proj_p.suffix.lower() in ('.rtvs', '.json')) else proj_p
            if proj_dir.exists() and os.access(str(proj_dir), os.W_OK):
                cache_peaks_dir = proj_dir / ".cache" / "peaks"
                cache_peaks_dir.mkdir(parents=True, exist_ok=True)
                if sys.platform == "win32":
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(str(proj_dir / ".cache"), 0x02)
                    except Exception:
                        pass
                return cache_peaks_dir / f"{audio_p.stem}.peaks"

        # 2. Check if audio_file is located inside an existing project folder bundle
        candidate_proj = None
        if audio_p.parent.name.lower() in ("media", "audio"):
            if list(audio_p.parent.parent.glob("*.rtvs")) or (audio_p.parent.parent / ".cache").exists():
                candidate_proj = audio_p.parent.parent
        elif list(audio_p.parent.glob("*.rtvs")) or (audio_p.parent / ".cache").exists():
            candidate_proj = audio_p.parent

        if candidate_proj and candidate_proj.exists() and os.access(str(candidate_proj), os.W_OK):
            cache_peaks_dir = candidate_proj / ".cache" / "peaks"
            cache_peaks_dir.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(str(candidate_proj / ".cache"), 0x02)
                except Exception:
                    pass
            return cache_peaks_dir / f"{audio_p.stem}.peaks"
    except Exception:
        pass

    # 3. Safe fallback: global AppData cache (never write into arbitrary media folders)
    try:
        cache_dir = get_app_data_dir() / "cache" / "peaks"
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(str(audio_file).encode("utf-8")).hexdigest()[:16]
        return cache_dir / f"{key}_{Path(audio_file).stem}.peaks"
    except Exception:
        return None

class WaveformEnvelope(list):
    """Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels."""
    def __init__(self, iterable=None, levels=None):
        super().__init__(iterable or [])
        self.waveform_levels = levels or []


def build_waveform_pyramid(peaks):
    """Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.
    
    Each level downsamples the previous level by 4x, allowing instantaneous O(1) viewport-scaled
    waveform rendering on long audio files (>60 min) without UI thread lag.
    """
    if not peaks:
        return []
    if HAVE_NUMPY and np is not None:
        try:
            arr = np.asarray(peaks, dtype=np.float32)
            levels = [arr]
            curr = arr
            while len(curr) > 4:
                pad = (4 - (len(curr) % 4)) % 4
                if pad:
                    curr_padded = np.pad(curr, (0, pad), mode="edge")
                else:
                    curr_padded = curr
                curr = np.max(curr_padded.reshape(-1, 4), axis=1)
                levels.append(curr)
            return levels
        except Exception:
            pass

    # Pure Python fallback
    levels = [list(peaks)]
    curr = levels[0]
    while len(curr) > 4:
        next_level = [max(curr[i:i + 4]) for i in range(0, len(curr), 4)]
        levels.append(next_level)
        curr = next_level
    return levels


def read_waveform_peak_cache(audio_file, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
    """
    Read cached waveform peak envelope from binary cache.
    Returns list of float peaks or None if cache is missing or stale.
    Supports transparent migration from legacy adjacent .peaks files.
    """
    cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
    audio_p = Path(audio_file) if audio_file else None
    
    # Check if primary cache path exists, otherwise look for legacy adjacent file or appdata fallback
    candidate_paths = []
    if cache_path:
        candidate_paths.append((cache_path, False))
    if audio_p:
        # Fallback to appdata cache
        try:
            appdata_p = get_app_data_dir() / "cache" / "peaks" / f"{hashlib.sha256(str(audio_file).encode('utf-8')).hexdigest()[:16]}_{audio_p.stem}.peaks"
            if appdata_p != cache_path:
                candidate_paths.append((appdata_p, False))
        except Exception:
            pass
        legacy_path = audio_p.with_name(audio_p.name + ".peaks")
        if legacy_path != cache_path:
            candidate_paths.append((legacy_path, True))

    for p, is_legacy in candidate_paths:
        if not p.exists():
            continue
        try:
            if audio_p and audio_p.exists() and audio_p.stat().st_mtime > p.stat().st_mtime:
                continue
            with open(p, "rb") as f:
                magic = f.read(8)
                if magic != PEAKS_MAGIC:
                    continue
                header_bytes = f.read(10)
                if len(header_bytes) < 10:
                    continue
                version, pps, count = struct.unpack("<HfI", header_bytes)
                if version != PEAKS_VERSION or count == 0:
                    continue
                raw_data = f.read(count * 4)
                if len(raw_data) != count * 4:
                    continue
                peaks = list(struct.unpack(f"<{count}f", raw_data))
                levels = build_waveform_pyramid(peaks)
                envelope = WaveformEnvelope(peaks, levels=levels)
                # If read from legacy path, migrate to project .cache/peaks/ atomically
                if is_legacy and cache_path and not cache_path.exists():
                    write_waveform_peak_cache(audio_file, peaks, points_per_second=pps, project_file=project_file)
                return envelope
        except Exception:
            continue
    return None

def write_waveform_peak_cache(audio_file, peaks, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
    """
    Write waveform peak envelope to binary cache with atomic rename.
    """
    if not audio_file or not peaks:
        return
    try:
        cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
        if not cache_path:
            return
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = cache_path.with_name(cache_path.name + ".tmp")
        count = len(peaks)
        with open(tmp_path, "wb") as f:
            f.write(PEAKS_MAGIC)
            f.write(struct.pack("<HfI", PEAKS_VERSION, float(points_per_second), count))
            f.write(struct.pack(f"<{count}f", *peaks))
            f.flush()
            os.fsync(f.fileno())
        safe_replace(tmp_path, cache_path)
    except Exception:
        pass


def invalidate_waveform_peak_cache(audio_file, project_file=None):
    """Delete any cached waveform peak binary file for audio_file, including legacy paths."""
    deleted = False
    try:
        cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
        if cache_path and cache_path.exists():
            cache_path.unlink(missing_ok=True)
            deleted = True
        if audio_file:
            audio_p = Path(audio_file)
            legacy_p = audio_p.with_name(audio_p.name + ".peaks")
            if legacy_p.exists():
                legacy_p.unlink(missing_ok=True)
                deleted = True
            appdata_p = get_app_data_dir() / "cache" / "peaks" / f"{hashlib.sha256(str(audio_file).encode('utf-8')).hexdigest()[:16]}_{audio_p.stem}.peaks"
            if appdata_p.exists():
                appdata_p.unlink(missing_ok=True)
                deleted = True
    except Exception:
        pass
    return deleted


class WaveformWorker(QObject):
    finished = Signal(list, bool)

    def __init__(self, audio_file, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
        super().__init__()
        self.audio_file = str(audio_file)
        self.points_per_second = points_per_second
        self.project_file = project_file
        self._cancel_event = threading.Event()
        self._process = None

    def cancel(self):
        """Thread-safe cancellation request; also stops the FFmpeg child process."""
        self._cancel_event.set()
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def run(self):
        """Build a compact peak envelope without loading the whole recording into RAM."""
        process = None
        try:
            # Keep the waveform envelope bounded for multi-hour recordings.
            # We still stream decoded PCM through FFmpeg; only the compact peak
            # envelope is retained in memory.
            effective_pps = int(self.points_per_second)
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                probe = subprocess.run(
                    [ffprobe_path() or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", self.audio_file],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10, check=True,
                    creationflags=creationflags,
                )
                duration = float(probe.stdout.strip() or 0)
                max_points = 800_000
                if duration > 0 and duration * effective_pps > max_points:
                    effective_pps = max(20, int(max_points / duration))
            except Exception:
                pass
            samples_per_peak = max(1, WAVEFORM_ANALYSIS_RATE // max(1, effective_pps))
            cmd = [
                ffmpeg_path() or "ffmpeg", "-vn", "-i", self.audio_file,
                "-f", "s16le", "-ac", "1",
                "-ar", str(WAVEFORM_ANALYSIS_RATE),
                "-v", "quiet", "pipe:1",
            ]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1024 * 1024,
                creationflags=creationflags,
            )
            self._process = process
            register_process(process)

            peaks = []
            max_possible_val = 32768.0
            samples_in_peak = 0
            peak_value = 0
            leftover_samples = np.empty(0, dtype=np.int16) if (HAVE_NUMPY and np is not None) else None

            while True:
                if self._cancel_event.is_set():
                    try:
                        process.kill()
                    except Exception:
                        pass
                    process.wait()
                    self.finished.emit([], True)
                    return

                raw = process.stdout.read(128 * 1024)
                if not raw:
                    break

                if self._cancel_event.is_set():
                    try:
                        process.kill()
                    except Exception:
                        pass
                    process.wait()
                    self.finished.emit([], True)
                    return

                if HAVE_NUMPY and np is not None:
                    chunk = np.frombuffer(raw, dtype=np.int16)
                    if chunk.size > 0:
                        if leftover_samples.size > 0:
                            chunk = np.concatenate((leftover_samples, chunk))
                        n_peaks = chunk.size // samples_per_peak
                        if n_peaks > 0:
                            usable = chunk[:n_peaks * samples_per_peak]
                            reshaped = np.abs(usable).reshape(n_peaks, samples_per_peak)
                            chunk_peaks = (np.max(reshaped, axis=1) / max_possible_val).astype(np.float32)
                            peaks.extend(chunk_peaks.tolist())
                            leftover_samples = chunk[n_peaks * samples_per_peak:]
                        else:
                            leftover_samples = chunk
                else:
                    sample_count = len(raw) // 2
                    if sample_count:
                        samples = struct.unpack(f"<{sample_count}h", raw[:sample_count * 2])
                        for sample in samples:
                            peak_value = max(peak_value, abs(sample))
                            samples_in_peak += 1
                            if samples_in_peak == samples_per_peak:
                                peaks.append(peak_value / max_possible_val)
                                samples_in_peak = 0
                                peak_value = 0

            return_code = process.wait()
            if self._cancel_event.is_set():
                self.finished.emit([], True)
                return
            if return_code != 0:
                self.finished.emit([], False)
                return

            if HAVE_NUMPY and np is not None and leftover_samples is not None and leftover_samples.size > 0:
                peaks.append(float(np.max(np.abs(leftover_samples)) / max_possible_val))
            elif samples_in_peak:
                peaks.append(peak_value / max_possible_val)

            if peaks:
                try:
                    write_waveform_peak_cache(self.audio_file, peaks, effective_pps, project_file=self.project_file)
                except Exception:
                    pass

            levels = build_waveform_pyramid(peaks)
            envelope = WaveformEnvelope(peaks, levels=levels)
            self.finished.emit(envelope, False)
        except Exception:
            if process is not None:
                try:
                    process.kill()
                    process.wait()
                except Exception:
                    pass
            self.finished.emit([], self._cancel_event.is_set())
        finally:
            if process is not None:
                unregister_process(process)
            self._process = None


# ============================================================
# Video Thumbnail Caching & Background Extraction
# ============================================================

def get_video_thumbnail_cache_dir(media_file: str | Path | None, project_file: str | Path | None = None) -> Path | None:
    """Return the deterministic thumbnail cache directory for a media file, associating with project if available."""
    if not media_file:
        return None
    try:
        p = Path(media_file).resolve()
        stat = p.stat()
        key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}"
        h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]
        
        # 1. Project-level thumbnail directory
        if project_file:
            proj_p = Path(project_file).resolve()
            proj_dir = proj_p.parent if (proj_p.is_file() or proj_p.suffix.lower() in ('.rtvs', '.json')) else proj_p
            if proj_dir.exists() and os.access(str(proj_dir), os.W_OK):
                base = proj_dir / ".cache" / "thumbnails"
                return base / h

        # 2. Check if media resides in project bundle
        candidate_proj = None
        if p.parent.name.lower() in ("media", "audio"):
            if list(p.parent.parent.glob("*.rtvs")) or (p.parent.parent / ".cache").exists():
                candidate_proj = p.parent.parent
        elif list(p.parent.glob("*.rtvs")) or (p.parent / ".cache").exists():
            candidate_proj = p.parent

        if candidate_proj and candidate_proj.exists() and os.access(str(candidate_proj), os.W_OK):
            base = candidate_proj / ".cache" / "thumbnails"
            return base / h

        # 3. Global AppData / Temp directory fallback
        base = get_app_data_dir() / "cache" / "thumbnails"
        return base / h
    except Exception:
        try:
            h = hashlib.sha256(str(Path(media_file)).encode("utf-8")).hexdigest()[:24]
            base = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
            return base / h
        except Exception:
            return None


def read_video_thumbnail_cache(media_file: str | Path | None, duration: float, project_file: str | Path | None = None) -> list | None:
    """Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.
    
    Returns list of items if the cache exists, contains valid thumbnail images, and is
    not older than the media file; otherwise returns None.
    """
    if not media_file or duration <= 0:
        return None
    try:
        cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file)
        if not cache_dir or not cache_dir.exists() or not cache_dir.is_dir():
            # Try global fallback
            alt_dir = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails" / hashlib.sha256(str(Path(media_file)).encode("utf-8")).hexdigest()[:24]
            if alt_dir.exists() and alt_dir.is_dir():
                cache_dir = alt_dir
            else:
                return None

        media_p = Path(media_file)
        if media_p.exists():
            if media_p.stat().st_mtime > cache_dir.stat().st_mtime:
                return None

        thumbs = sorted(cache_dir.glob("thumb_*.jpg"))
        if not thumbs or len(thumbs) < 2:
            return None

        valid_thumbs = []
        for t in thumbs:
            if t.exists() and t.stat().st_size > 0:
                valid_thumbs.append(t)

        if not valid_thumbs or len(valid_thumbs) != len(thumbs):
            return None

        items = []
        num = len(valid_thumbs)
        for i, p in enumerate(valid_thumbs):
            ts = (i / max(1, num - 1)) * duration if num > 1 else 0.0
            items.append((ts, str(p)))
        return items
    except Exception:
        return None


def invalidate_video_thumbnail_cache(media_file: str | Path | None, project_file: str | Path | None = None) -> bool:
    """Delete the thumbnail cache directory for a given media file."""
    deleted = False
    try:
        cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file)
        if cache_dir and cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            deleted = True
        # Also clean up tempdir thumbnail cache
        if media_file:
            try:
                p = Path(media_file).resolve()
                stat = p.stat()
                key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}"
                h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]
                t_dir = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails" / h
                if t_dir.exists():
                    shutil.rmtree(t_dir, ignore_errors=True)
                    deleted = True
            except Exception:
                pass
    except Exception:
        pass
    return deleted


class VideoThumbnailWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, media_path, duration, output_dir, count=36):
        super().__init__()
        self.media_path = Path(media_path)
        self.duration = max(0.1, float(duration or 0))
        self.output_dir = Path(output_dir)
        self.count = max(8, min(80, int(count)))
        self._cancelled = False
        self._process = None

    def cancel(self):
        self._cancelled = True
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def run(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            fps = self.count / self.duration
            vf = f"fps={fps:.8f},scale=320:-2:force_original_aspect_ratio=decrease"
            pattern = str(self.output_dir / "thumb_%03d.jpg")
            cmd = [ffmpeg_path() or "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(self.media_path), "-map", "0:v:0", "-vf", vf, "-q:v", "4", pattern]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
            register_process(self._process)
            _stdout, stderr = self._process.communicate()
            returncode = self._process.returncode
            if self._cancelled:
                self.finished.emit([])
                return
            if returncode != 0:
                raise RuntimeError(stderr.strip() or "FFmpeg could not create video thumbnails.")
            files = sorted(self.output_dir.glob("thumb_*.jpg"))
            if not files:
                raise RuntimeError("No video thumbnails were generated.")
            actual_count = len(files)
            items = []
            for i, path in enumerate(files):
                if self._cancelled:
                    break
                timestamp = (i / max(1, actual_count - 1)) * self.duration if actual_count > 1 else 0.0
                items.append((timestamp, str(path)))
            self.finished.emit(items)
        except Exception as exc:
            if not self._cancelled:
                self.error.emit(str(exc))
            else:
                self.finished.emit([])
        finally:
            if self._process is not None:
                unregister_process(self._process)
            self._process = None


class TimelineCanvas(QWidget):
    positionClicked = Signal(float)
    scrubPositionChanged = Signal(float)
    storyRegionUpdated = Signal(int, float, float)
    newRegionStarted = Signal(float, float)
    newRegionUpdated = Signal(float, float)
    multiSelectionChanged = Signal(list)
    dragOperationFinished = Signal()
    scrollOffsetChanged = Signal(float)
    zoomChanged = Signal()
    mediaDropped = Signal(str)
    selectionRangeChanged = Signal(object, object)
    storyCreatedFromSelection = Signal(float, float)
    storyClicked = Signal(int)

    RULER_HEIGHT = 24
    EDGE_HANDLE_THRESHOLD = 8
    CURSOR_GRAB_THRESHOLD = 12
    DRAG_PIXEL_THRESHOLD = 5

    def __init__(self, parent=None, tokens=None):
        super().__init__(parent)
        self.tokens = tokens if tokens is not None else ThemeTokens()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.duration = 1
        self.position = 0
        self.skip_seconds = 5
        self.is_playing = False
        self.audio_file_name = None

        self.selection_start = None
        self.selection_end = None
        self.is_right_dragging = False
        self.active_selection_handle = None
        self.active_fade_target = None  # Tuple: (story_index, 'fade_in' | 'fade_out')
        self._fade_drag_start_val = 0.0
        self.show_audio_fades = False
        self.enable_magnetic_snapping = False
        self._last_tooltip_text = ""

        self.stories = []
        self.waveform_peaks = []
        self.waveform_levels = []
        self.video_thumbnails = []
        self.is_video = False
        self.show_waveform = True
        self.show_thumbnails = True
        self.thumbnail_position = "below"
        self.selected_story_indices = []
        self.transcript_selection_range = None

        self.zoom_level = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 80.0
        self.scroll_offset = 0.0

        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_offset = 0.0

        self.is_left_down = False
        self.is_scrubbing = False
        self.left_down_x = 0
        self.has_dragged = False
        self.selection_start_time = 0.0

        self.is_box_selecting = False
        self.box_start_time = 0.0

        self.active_edge_target = None

        self.waveform_pixmap = None
        self.pixmap_dirty = True
        self.buffered_total_width = 0
        self._last_rendered_width = 0
        self._last_rendered_height = 0
        self._last_rendered_scroll = None
        self._last_rendered_zoom = None

        # Background generation activity indicators
        self.active_background_tasks = set()
        self.background_status_text = ""
        self.show_background_banner = False
        self._background_delay_timer = QTimer(self)
        self._background_delay_timer.setSingleShot(True)
        self._background_delay_timer.setInterval(100)
        self._background_delay_timer.timeout.connect(self._activate_background_banner)

        self.setMinimumHeight(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

    def set_is_video(self, is_video: bool):
        self.is_video = bool(is_video)
        self.pixmap_dirty = True
        self.update()

    def set_background_generation_active(self, task_name: str, active: bool):
        """Set generation state for 'waveform' or 'thumbnails'."""
        if active:
            self.active_background_tasks.add(task_name)
            self.show_background_banner = True
            if self._background_delay_timer.isActive():
                self._background_delay_timer.stop()
        else:
            self.active_background_tasks.discard(task_name)
            if not self.active_background_tasks:
                self._background_delay_timer.stop()
                self.show_background_banner = False
                self.background_status_text = ""
                self.pixmap_dirty = True
                self.update()
                return

        self._update_background_status_text()
        self.pixmap_dirty = True
        self.update()

    def _activate_background_banner(self):
        if self.active_background_tasks:
            self.show_background_banner = True
            self._update_background_status_text()
            self.pixmap_dirty = True
            self.update()

    def _update_background_status_text(self):
        win = self.window()
        is_es = getattr(win, "language", "en") == "es"
        labels = []
        if "waveform" in self.active_background_tasks:
            labels.append("forma de onda" if is_es else "audio waveform")
        if "thumbnails" in self.active_background_tasks:
            labels.append("miniaturas de video" if is_es else "video thumbnails")
        if labels:
            prefix = "Generando " if is_es else "Generating "
            sep = " y " if is_es else " and "
            self.background_status_text = f"{prefix}{sep.join(labels)}..."
        else:
            self.background_status_text = ""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            local_files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if local_files:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.mediaDropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def set_audio_filename(self, filename):
        self.audio_file_name = filename
        self.pixmap_dirty = True
        self.update()

    def set_duration(self, duration):
        self.duration = max(1, duration)
        self.clamp_scroll_offset()
        self.zoomChanged.emit()
        self.pixmap_dirty = True
        self.update()

    def set_position(self, position):
        self.position = position
        self.ensure_position_visible(self.position)
        self.update()

    def set_playing_state(self, is_playing):
        self.is_playing = is_playing

    def ensure_position_visible(self, target_time):
        if self.zoom_level <= 1.0:
            return

        vis_dur = self.visible_duration()
        old_offset = self.scroll_offset

        if self.is_playing:
            self.scroll_offset = target_time - (vis_dur / 2.0)
            self.clamp_scroll_offset()
        else:
            view_start = self.scroll_offset
            view_end = self.scroll_offset + vis_dur
            margin = vis_dur * 0.05
            if target_time < (view_start + margin) or target_time > (view_end - margin):
                self.scroll_offset = target_time - (vis_dur / 2.0)
                self.clamp_scroll_offset()

        if self.scroll_offset != old_offset:
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True

    def set_transcript_selection_range(self, start, end):
        if start is None or end is None:
            self.transcript_selection_range = None
        else:
            self.transcript_selection_range = (max(0.0, float(start)), min(self.duration, float(end)))
        self.update()

    def set_stories(self, stories, selected_indices=None):
        self.stories = stories
        self.selected_story_indices = selected_indices if selected_indices is not None else []
        self.update()

    def set_waveform_peaks(self, peaks, levels=None):
        self.waveform_peaks = peaks or []
        if levels is not None:
            self.waveform_levels = levels
        elif hasattr(peaks, "waveform_levels") and peaks.waveform_levels:
            self.waveform_levels = peaks.waveform_levels
        elif self.waveform_peaks:
            self.waveform_levels = build_waveform_pyramid(self.waveform_peaks)
        else:
            self.waveform_levels = []
        self.pixmap_dirty = True
        self.update()

    def set_timeline_views(self, show_waveform=True, show_thumbnails=True):
        self.show_waveform = bool(show_waveform)
        self.show_thumbnails = bool(show_thumbnails)
        self.pixmap_dirty = True
        self.update()

    def set_video_thumbnails(self, thumbnails):
        self.video_thumbnails = []
        for timestamp, filename in thumbnails or []:
            pix = QPixmap(str(filename))
            if not pix.isNull():
                self.video_thumbnails.append((float(timestamp), pix))
        self.pixmap_dirty = True
        self.update()

    def set_skip_seconds(self, seconds):
        self.skip_seconds = max(1, int(seconds))

    def visible_duration(self):
        return self.duration / self.zoom_level

    def clamp_scroll_offset(self):
        max_offset = max(0.0, self.duration - self.visible_duration())
        self.scroll_offset = max(0.0, min(max_offset, self.scroll_offset))
        self.scrollOffsetChanged.emit(self.scroll_offset)

    def time_to_x(self, time_val, width):
        if self.visible_duration() <= 0:
            return 0
        return ((time_val - self.scroll_offset) / self.visible_duration()) * width

    def x_to_time(self, x_val, width):
        ratio = x_val / max(1, width)
        return self.scroll_offset + (ratio * self.visible_duration())

    def snap_time(self, raw_time: float, exclude_story_idx: int = None, width: int = None, pixel_threshold: int = 10) -> float:
        """Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels."""
        if not getattr(self, "enable_magnetic_snapping", True):
            return raw_time

        width = width or max(1, self.width())
        vis_dur = max(0.001, self.visible_duration())
        threshold_dt = (pixel_threshold / max(1, width)) * vis_dur

        snap_points = []

        # 1. Playhead position
        if hasattr(self, "position") and self.position is not None:
            snap_points.append(float(self.position))

        # 2. Selection region anchors
        if getattr(self, "selection_start", None) is not None:
            snap_points.append(float(self.selection_start))
        if getattr(self, "selection_end", None) is not None:
            snap_points.append(float(self.selection_end))

        # 3. Story boundaries
        for idx, story in enumerate(getattr(self, "stories", [])):
            if exclude_story_idx is not None and idx == exclude_story_idx:
                continue
            snap_points.append(float(story.start))
            snap_points.append(float(story.end))

        best_snap = raw_time
        min_diff = threshold_dt + 0.00001

        for pt in snap_points:
            diff = abs(raw_time - pt)
            if diff <= threshold_dt and diff < min_diff:
                min_diff = diff
                best_snap = pt

        return best_snap

    def find_edge_at_pos(self, pos_x, width):
        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)

            if abs(pos_x - start_x) <= self.EDGE_HANDLE_THRESHOLD:
                return (index, 'start')
            elif abs(pos_x - end_x) <= self.EDGE_HANDLE_THRESHOLD:
                return (index, 'end')
        return None

    FADE_HANDLE_THRESHOLD = 12

    def find_fade_handle_at_pos(self, pos_x, pos_y, width):
        """Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks."""
        if not getattr(self, "show_audio_fades", False):
            return None

        top_y = self.RULER_HEIGHT
        if pos_y < (top_y - 8) or pos_y > (top_y + 26):
            return None

        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)
            if end_x < -16 or start_x > width + 16:
                continue

            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)

            # Fade-in handle apex sits at (start + fade_in) along top edge
            fin_x = self.time_to_x(story.start + fin, width)
            if abs(pos_x - fin_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_in")

            # Fade-out handle apex sits at (end - fade_out) along top edge
            fout_x = self.time_to_x(story.end - fout, width)
            if abs(pos_x - fout_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_out")
        return None

    def find_story_at_time(self, time):
        """Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping."""
        candidates = []
        for index, story in enumerate(self.stories):
            if story.start <= time <= story.end:
                candidates.append((story.end - story.start, index))
        if candidates:
            candidates.sort()
            return candidates[0][1]
        return None

    def is_near_playhead(self, pos_x, width):
        cursor_x = self.time_to_x(self.position, width)
        return abs(pos_x - cursor_x) <= self.CURSOR_GRAB_THRESHOLD

    def set_zoom(self, new_zoom, center_x=None, focus_time=None):
        width = max(1, self.width())
        if focus_time is None:
            # Anchor zoom around the active cursor position (self.position)
            focus_time = getattr(self, "position", 0.0)
            if focus_time is None:
                focus_time = 0.0

        if center_x is None:
            # Keep the active cursor at its current screen x position, or center if off-screen
            cur_x = self.time_to_x(focus_time, width)
            if 0 <= cur_x <= width:
                center_x = cur_x
            else:
                center_x = width / 2.0

        self.zoom_level = max(self.min_zoom, min(self.max_zoom, new_zoom))

        new_visible = self.visible_duration()
        ratio = center_x / max(1, width)
        self.scroll_offset = focus_time - (ratio * new_visible)

        self.clamp_scroll_offset()
        self.zoomChanged.emit()
        self.scrollOffsetChanged.emit(self.scroll_offset)
        self.pixmap_dirty = True
        self.update()

    def resizeEvent(self, event):
        self.pixmap_dirty = True
        super().resizeEvent(event)

    def wheelEvent(self, event):
        # 1. Check for horizontal scrolling (trackpad 2-finger horizontal gesture, horizontal tilt/side wheel, or Shift+vertical wheel)
        h_delta_px = event.pixelDelta().x() if hasattr(event, "pixelDelta") else 0
        h_delta_angle = event.angleDelta().x() if hasattr(event, "angleDelta") else 0
        v_delta_angle = event.angleDelta().y() if hasattr(event, "angleDelta") else 0
        v_delta_px = event.pixelDelta().y() if hasattr(event, "pixelDelta") else 0
        modifiers = event.modifiers()

        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        # Explicit horizontal input (horizontal scroll wheel or trackpad 2-finger horizontal pan)
        if h_delta_px != 0 or h_delta_angle != 0:
            if h_delta_px != 0:
                pan_dt = (h_delta_px / max(1, self.width())) * self.visible_duration()
                self.scroll_offset -= pan_dt
            else:
                pan_dt = (h_delta_angle / 120.0) * (self.visible_duration() * 0.1)
                self.scroll_offset -= pan_dt
            self.clamp_scroll_offset()
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True
            self.update()
            event.accept()
            return

        # Shift + vertical wheel -> horizontal scrolling
        if is_shift:
            if v_delta_px != 0:
                pan_dt = (v_delta_px / max(1, self.width())) * self.visible_duration()
                self.scroll_offset -= pan_dt
            else:
                pan_dt = (v_delta_angle / 120.0) * (self.visible_duration() * 0.1)
                self.scroll_offset -= pan_dt
            self.clamp_scroll_offset()
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True
            self.update()
            event.accept()
            return

        # Vertical scroll wheel / standard wheel -> Zoom centered on active cursor
        if v_delta_angle != 0:
            factor = 1.15 ** (abs(v_delta_angle) / 120.0)
            if v_delta_angle > 0:
                self.set_zoom(self.zoom_level * factor)
            else:
                self.set_zoom(self.zoom_level / factor)
            event.accept()
            return

        super().wheelEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        pos_x = event.position().x()
        width = self.width()

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.pan_start_x = pos_x
            self.pan_start_offset = self.scroll_offset
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # --- FADE ENVELOPE HANDLE INTERACTION ---
        fade_hit = self.find_fade_handle_at_pos(pos_x, event.position().y(), width)
        if fade_hit:
            self.active_fade_target = fade_hit
            idx, f_type = fade_hit
            self._fade_drag_start_val = getattr(self.stories[idx], f_type, 0.0)
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()
            return

        # --- RIGHT-CLICK: Drag Selection, Handle Adjustments, or Context Menu ---
        if event.button() == Qt.MouseButton.RightButton:
            curr_t = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))

            # Check if clicking a handle on an existing right-click selection
            if self.selection_start is not None and self.selection_end is not None:
                x_start = self.time_to_x(self.selection_start, width)
                x_end = self.time_to_x(self.selection_end, width)
                x_min = min(x_start, x_end)
                x_max = max(x_start, x_end)

                if abs(pos_x - x_min) <= self.EDGE_HANDLE_THRESHOLD:
                    self.active_selection_handle = "start" if x_start <= x_end else "end"
                    self.is_right_dragging = True
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                    event.accept()
                    return
                elif abs(pos_x - x_max) <= self.EDGE_HANDLE_THRESHOLD:
                    self.active_selection_handle = "end" if x_start <= x_end else "start"
                    self.is_right_dragging = True
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                    event.accept()
                    return
                elif x_min < pos_x < x_max:
                    self._show_selection_context_menu(event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos())
                    event.accept()
                    return

            # Check if grabbing an existing story edge
            edge_hit = self.find_edge_at_pos(pos_x, width)
            if edge_hit:
                self.active_edge_target = edge_hit
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return

            # Otherwise, begin drawing a new selection region
            self.selection_start = curr_t
            self.selection_end = curr_t
            self.active_selection_handle = "end"
            self.is_right_dragging = True
            self.selectionRangeChanged.emit(self.selection_start, self.selection_end)
            self.update()
            event.accept()
            return

        # --- LEFT-CLICK: Continuous Audio Scrubbing & Playhead Navigation ---
        # Story boundaries cannot be moved by left-clicking/dragging handles.
        # Use right-click + drag on handles or the Set Story Start/End buttons.
        if event.button() == Qt.MouseButton.LeftButton:
            time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            self.position = time
            self.is_left_down = True
            self.is_scrubbing = True
            self.positionClicked.emit(time)
            self.scrubPositionChanged.emit(time)
            story_idx = self.find_story_at_time(time)
            if story_idx is not None:
                self.storyClicked.emit(story_idx)
            self.update()
            event.accept()
            return

    def mouseMoveEvent(self, event):
        pos_x = event.position().x()
        width = self.width()

        if self.is_panning:
            dx = pos_x - self.pan_start_x
            dt = (dx / max(1, width)) * self.visible_duration()
            self.scroll_offset = self.pan_start_offset - dt
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        # --- RIGHT-CLICK DRAG: Update Selection Region and Handles ---
        if self.is_right_dragging:
            raw_time = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))
            curr_time = self.snap_time(raw_time, width=width)
            if self.active_selection_handle == "start":
                self.selection_start = curr_time
            elif self.active_selection_handle == "end":
                self.selection_end = curr_time

            s = min(self.selection_start, self.selection_end)
            e = max(self.selection_start, self.selection_end)
            self.selectionRangeChanged.emit(s, e)
            self.update()
            event.accept()
            return

        # --- LEFT-CLICK DRAG: Continuous Audio Scrubbing ---
        if self.is_left_down and self.is_scrubbing:
            raw_time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            curr_time = self.snap_time(raw_time, width=width)
            self.scrubPositionChanged.emit(curr_time)
            event.accept()
            return

        # --- FADE HANDLE DRAG ---
        if self.active_fade_target:
            idx, f_type = self.active_fade_target
            if 0 <= idx < len(self.stories):
                story = self.stories[idx]
                story_dur = max(0.01, story.end - story.start)
                raw_time = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))
                curr_time = self.snap_time(raw_time, width=width)
                if f_type == "fade_in":
                    max_in = max(0.0, story_dur - getattr(story, "fade_out", 0.0))
                    story.fade_in = round(max(0.0, min(max_in, curr_time - story.start)), 2)
                elif f_type == "fade_out":
                    max_out = max(0.0, story_dur - getattr(story, "fade_in", 0.0))
                    story.fade_out = round(max(0.0, min(max_out, story.end - curr_time)), 2)
                self.update()
            event.accept()
            return

        if self.active_edge_target:
            idx, edge_type = self.active_edge_target
            if 0 <= idx < len(self.stories):
                raw_time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
                curr_time = self.snap_time(raw_time, exclude_story_idx=idx, width=width)
                story = self.stories[idx]

                if edge_type == 'start':
                    new_start = min(curr_time, story.end - 0.1)
                    self.storyRegionUpdated.emit(idx, new_start, story.end)
                elif edge_type == 'end':
                    new_end = max(curr_time, story.start + 0.1)
                    self.storyRegionUpdated.emit(idx, story.start, new_end)

            event.accept()
            return

        pos_y = event.position().y()
        edge_hit = self.find_edge_at_pos(pos_x, width)
        fade_hit = self.find_fade_handle_at_pos(pos_x, pos_y, width)

        if self.is_near_playhead(pos_x, width) or edge_hit or fade_hit:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.unsetCursor()

        if not (self.is_panning or self.is_left_down or self.is_right_dragging or self.active_edge_target or self.active_fade_target):
            tooltip_text = ""
            if fade_hit:
                idx, f_type = fade_hit
                if 0 <= idx < len(self.stories):
                    f_dur = getattr(self.stories[idx], f_type, 0.0)
                    f_name = "Fade-In" if f_type == "fade_in" else "Fade-Out"
                    tooltip_text = f"{self.stories[idx].title} ({f_name}: {f_dur:.2f}s)\nDrag handle horizontally to adjust audio fade"
            elif edge_hit:
                idx, edge_type = edge_hit
                title = self.stories[idx].title if 0 <= idx < len(self.stories) else f"Story #{idx+1}"
                tooltip_text = f"{title} ({edge_type.capitalize()} Boundary)\nRight-click and drag to adjust"

            if tooltip_text:
                if tooltip_text != getattr(self, "_last_tooltip_text", ""):
                    self._last_tooltip_text = tooltip_text
                    QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
            else:
                if getattr(self, "_last_tooltip_text", ""):
                    self._last_tooltip_text = ""
                    QToolTip.hideText()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active_fade_target:
            idx, f_type = self.active_fade_target
            self.active_fade_target = None
            self.unsetCursor()
            if 0 <= idx < len(self.stories):
                win = self.window()
                curr_val = getattr(self.stories[idx], f_type, 0.0)
                if abs(curr_val - self._fade_drag_start_val) >= 0.01:
                    if f_type == "fade_in":
                        old_in, new_in = self._fade_drag_start_val, curr_val
                        old_out, new_out = self.stories[idx].fade_out, self.stories[idx].fade_out
                    else:
                        old_in, new_in = self.stories[idx].fade_in, self.stories[idx].fade_in
                        old_out, new_out = self._fade_drag_start_val, curr_val
                    if hasattr(win, "undo_stack"):
                        win.undo_stack.push(StoryFadesChangeCommand(win, idx, old_in, old_out, new_in, new_out))
                    elif hasattr(win, "save_project"):
                        win.save_project()
                if hasattr(win, "refresh_story_list"):
                    win.refresh_story_list()
            self.update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.unsetCursor()
            event.accept()
            return

        # --- RIGHT-CLICK RELEASE: Finalize Selection Boundaries ---
        if event.button() == Qt.MouseButton.RightButton:
            if self.is_right_dragging:
                self.is_right_dragging = False
                self.active_selection_handle = None
                self.unsetCursor()
                if self.selection_start is not None and self.selection_end is not None:
                    if abs(self.selection_start - self.selection_end) < 0.05:
                        self.selection_start = None
                        self.selection_end = None
                        self.selectionRangeChanged.emit(None, None)
                        self.update()
                        gpos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
                        self._show_timeline_context_menu(gpos, event.position().x())
                        event.accept()
                        return
                    else:
                        s = min(self.selection_start, self.selection_end)
                        e = max(self.selection_start, self.selection_end)
                        self.selection_start, self.selection_end = s, e
                        self.selectionRangeChanged.emit(s, e)
                self.update()
                event.accept()
                return

            if self.active_edge_target:
                self.active_edge_target = None
                self.unsetCursor()
                self.dragOperationFinished.emit()
                event.accept()
                return

        # --- LEFT-CLICK RELEASE: Finalize Audio Scrubbing ---
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_left_down:
                self.is_left_down = False
                self.is_scrubbing = False
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def _show_timeline_context_menu(self, global_pos, pos_x):
        win = self.window()
        menu = QMenu(self)
        width = self.width()
        time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
        story_idx = self.find_story_at_time(time)

        is_music = getattr(win, "story_detection_mode", "voice") == "music"
        is_es = getattr(win, "language", "en") == "es"
        term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

        select_action = None
        fades_action = None
        delete_action = None
        if story_idx is not None and 0 <= story_idx < len(self.stories):
            select_action = menu.addAction(f"{('Seleccionar' if is_es else 'Select')} {term} #{story_idx + 1}")
            if hasattr(win, "open_story_fades_dialog"):
                fades_action = menu.addAction("Ajustar fundidos de audio..." if is_es else "Set Audio Fades...")
            delete_action = menu.addAction(f"{('Eliminar' if is_es else 'Delete')} {term} #{story_idx + 1}")
            menu.addSeparator()

        has_audio = bool(getattr(win, "audio_file", None))
        has_video = bool(getattr(win, "current_media_is_video", False))

        regen_wf_act = None
        regen_th_act = None
        if hasattr(win, "regenerate_waveform"):
            label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
            regen_wf_act = menu.addAction(label)
            regen_wf_act.setEnabled(has_audio)

        if hasattr(win, "regenerate_video_thumbnails"):
            label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
            regen_th_act = menu.addAction(label)
            regen_th_act.setEnabled(has_audio and has_video)

        if not menu.actions():
            return

        selected = menu.exec(global_pos)
        if story_idx is not None and 0 <= story_idx < len(self.stories):
            if select_action and selected == select_action:
                self.storyClicked.emit(story_idx)
            elif fades_action and selected == fades_action:
                if hasattr(win, "open_story_fades_dialog"):
                    win.open_story_fades_dialog(story_index=story_idx)
            elif delete_action and selected == delete_action:
                if hasattr(win, "apply_story_selection_indices") and hasattr(win, "delete_selected_story"):
                    win.apply_story_selection_indices([story_idx], seek=False)
                    win.delete_selected_story()
        if regen_wf_act and selected == regen_wf_act:
            win.regenerate_waveform()
        elif regen_th_act and selected == regen_th_act:
            win.regenerate_video_thumbnails()

    def _show_selection_context_menu(self, global_pos):
        if self.selection_start is None or self.selection_end is None:
            return
        s = min(self.selection_start, self.selection_end)
        e = max(self.selection_start, self.selection_end)
        win = self.window()
        is_music = getattr(win, "story_detection_mode", "voice") == "music"
        is_es = getattr(win, "language", "en") == "es"
        term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")
        menu = QMenu(self)
        add_action = menu.addAction(f"{('Agregar' if is_es else 'Add')} {term} {('desde la selección' if is_es else 'from Selection')}")
        clear_action = menu.addAction("Borrar selección" if is_es else "Clear Selection")

        menu.addSeparator()
        has_audio = bool(getattr(win, "audio_file", None))
        has_video = bool(getattr(win, "current_media_is_video", False))

        regen_wf_act = None
        regen_th_act = None
        if hasattr(win, "regenerate_waveform"):
            label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
            regen_wf_act = menu.addAction(label)
            regen_wf_act.setEnabled(has_audio)

        if hasattr(win, "regenerate_video_thumbnails"):
            label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
            regen_th_act = menu.addAction(label)
            regen_th_act.setEnabled(has_audio and has_video)

        selected = menu.exec(global_pos)
        if selected == add_action:
            self.storyCreatedFromSelection.emit(s, e)
        elif selected == clear_action:
            self.selection_start = None
            self.selection_end = None
            self.selectionRangeChanged.emit(None, None)
            self.update()
        elif regen_wf_act and selected == regen_wf_act:
            win.regenerate_waveform()
        elif regen_th_act and selected == regen_th_act:
            win.regenerate_video_thumbnails()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Undo):
            main_win = self.window()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.undo()
                event.accept()
                return

        if event.matches(QKeySequence.StandardKey.Redo):
            main_win = self.window()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.redo()
                event.accept()
                return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            main_win = self.window()
            # If there is a selected/highlighted story, delete it directly from the timeline
            if hasattr(main_win, "delete_selected_story") and getattr(main_win, "current_selected_story_indices", None):
                main_win.delete_selected_story()
                event.accept()
                return
            elif self.selected_story_indices and hasattr(main_win, "delete_selected_story"):
                if hasattr(main_win, "apply_story_selection_indices"):
                    main_win.apply_story_selection_indices(self.selected_story_indices, seek=False)
                main_win.delete_selected_story()
                event.accept()
                return
            # If there is an active timeline drag selection range without a selected story, clear it
            elif self.selection_start is not None or self.selection_end is not None:
                self.selection_start = None
                self.selection_end = None
                self.selectionRangeChanged.emit(None, None)
                self.update()
                event.accept()
                return

        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.set_zoom(self.zoom_level * 1.2)
            event.accept()
            return

        if event.key() == Qt.Key.Key_Minus:
            self.set_zoom(self.zoom_level / 1.2)
            event.accept()
            return

        if event.key() == Qt.Key.Key_A or (event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.scroll_offset -= self.visible_duration() * 0.1
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        if event.key() == Qt.Key.Key_D or (event.key() == Qt.Key.Key_Right and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.scroll_offset += self.visible_duration() * 0.1
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Left:
            self.positionClicked.emit(max(0, self.position - self.skip_seconds))
            event.accept()
            return

        if event.key() == Qt.Key.Key_Right:
            self.positionClicked.emit(min(self.duration, self.position + self.skip_seconds))
            event.accept()
            return

        if event.key() == Qt.Key.Key_Home:
            self.positionClicked.emit(0)
            event.accept()
            return

        if event.key() == Qt.Key.Key_End:
            self.positionClicked.emit(self.duration)
            event.accept()
            return

        super().keyPressEvent(event)

    def set_thumbnail_position(self, position):
        if position in ("above", "below") and self.thumbnail_position != position:
            self.thumbnail_position = position
            self.pixmap_dirty = True
            self.update()

    def render_waveform_buffer(self, width, height):
        dpi_scale = self.devicePixelRatioF()
        phys_width = max(1, int(width * dpi_scale))
        phys_height = max(1, int(height * dpi_scale))

        pixmap = QPixmap(phys_width, phys_height)
        pixmap.setDevicePixelRatio(dpi_scale)
        pixmap.fill(self.tokens.color(self.tokens.bg_surface))

        painter = QPainter(pixmap)
        if not painter.isActive():
            return pixmap
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        available = max(20, height - self.RULER_HEIGHT)
        is_video_mode = getattr(self, "is_video", False) or bool(self.video_thumbnails) or ("thumbnails" in self.active_background_tasks)
        has_thumbs = bool(self.show_thumbnails and (self.video_thumbnails or is_video_mode))

        if has_thumbs and self.show_waveform:
            thumbnail_height = int(available * 0.46)
            waveform_height = available - thumbnail_height
        elif has_thumbs:
            thumbnail_height = available
            waveform_height = 0
        elif self.show_waveform:
            thumbnail_height = 0
            waveform_height = available
        else:
            thumbnail_height = 0
            waveform_height = 0

        if self.thumbnail_position == "below" and self.show_waveform and has_thumbs:
            waveform_y = self.RULER_HEIGHT
            thumbnail_y = self.RULER_HEIGHT + waveform_height
        else:
            thumbnail_y = self.RULER_HEIGHT
            waveform_y = self.RULER_HEIGHT + thumbnail_height

        middle_y = waveform_y + (waveform_height / 2.0)

        # Draw subtle divider line between waveform and thumbnail tracks when both are visible
        if has_thumbs and self.show_waveform and thumbnail_height > 0 and waveform_height > 0:
            divider_y = thumbnail_y if self.thumbnail_position == "below" else waveform_y
            painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
            painter.drawLine(QPointF(0, divider_y), QPointF(width, divider_y))

        if has_thumbs and thumbnail_height > 0:
            if self.video_thumbnails:
                target_h = max(14, int((thumbnail_height - 6) * 0.88))
                vis_dur = max(0.001, self.visible_duration())

                # Resizing logic: scale thumbnail width dynamically with track height
                sample_pix = self.video_thumbnails[0][1] if self.video_thumbnails else None
                aspect = (sample_pix.width() / max(1, sample_pix.height())) if (sample_pix and not sample_pix.isNull() and sample_pix.height() > 0) else (16.0 / 9.0)
                target_w = max(24, int(target_h * aspect))

                # Buffer based on scaled thumbnail width to avoid pop-in at borders
                dt_buffer = (target_w / max(1, width)) * vis_dur * 1.5
                t_min = max(0.0, self.scroll_offset - dt_buffer)
                t_max = min(self.duration, self.scroll_offset + vis_dur + dt_buffer)

                ts_list = [item[0] for item in self.video_thumbnails]
                start_idx = max(0, bisect_left(ts_list, t_min) - 1)
                end_idx = min(len(self.video_thumbnails), bisect_right(ts_list, t_max) + 1)

                # Prevent thumbnails from overlapping or cropping when zoomed out.
                # Prioritize full-size, uncropped display of frames over crowding.
                last_drawn_right = -100000.0
                min_gap_px = 2.0

                for i in range(start_idx, end_idx):
                    timestamp, pix = self.video_thumbnails[i]
                    x = self.time_to_x(timestamp, width)
                    if x + target_w < 0 or x - target_w > width:
                        continue
                    scaled = pix.scaled(
                        target_w,
                        target_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    draw_x = int(x - scaled.width() // 2)
                    # If drawing this thumbnail would overlap/clip the previous full-size thumbnail, skip it
                    if draw_x < (last_drawn_right + min_gap_px):
                        continue

                    draw_y = thumbnail_y + (thumbnail_height - scaled.height()) // 2
                    painter.drawPixmap(draw_x, int(draw_y), scaled)
                    painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
                    painter.drawRect(draw_x, int(draw_y), scaled.width(), scaled.height())
                    last_drawn_right = draw_x + scaled.width()
            elif "thumbnails" in self.active_background_tasks or is_video_mode:
                # Placeholder preview track while generating video thumbnails
                win = self.window()
                is_es = getattr(win, "language", "en") == "es"
                gen_text = "Generando miniaturas de video..." if is_es else "Generating video thumbnails..."
                
                # Draw subtle filmstrip frame placeholder boxes along the track
                target_h = max(14, int((thumbnail_height - 6) * 0.88))
                aspect = 16.0 / 9.0
                target_w = max(24, int(target_h * aspect))
                draw_y = thumbnail_y + (thumbnail_height - target_h) // 2
                
                painter.save()
                box_pen = self.tokens.pen(self.tokens.border_subtle, 1.0)
                box_pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(box_pen)
                
                step_px = target_w + 8
                x_pos = 12
                while x_pos + target_w < width - 12:
                    painter.drawRoundedRect(QRectF(x_pos, draw_y, target_w, target_h), 2.0, 2.0)
                    x_pos += step_px
                
                # Draw centered preview badge with text
                painter.setFont(self.font())
                fm = painter.fontMetrics()
                text_w = fm.horizontalAdvance(gen_text)
                text_badge_w = text_w + 24
                text_badge_h = min(26, max(18, thumbnail_height - 6))
                text_badge_x = (width - text_badge_w) / 2.0
                text_badge_y = thumbnail_y + (thumbnail_height - text_badge_h) / 2.0
                text_badge_rect = QRectF(text_badge_x, text_badge_y, text_badge_w, text_badge_h)
                
                painter.setPen(self.tokens.pen(self.tokens.status_banner_border, 1.0))
                painter.setBrush(self.tokens.brush(self.tokens.status_banner_bg, 235))
                painter.drawRoundedRect(text_badge_rect, 4.0, 4.0)
                painter.setPen(self.tokens.color(self.tokens.status_banner_text))
                painter.drawText(text_badge_rect, Qt.AlignmentFlag.AlignCenter, gen_text)
                painter.restore()

        if self.show_waveform and self.waveform_peaks and waveform_height > 0:
            painter.setPen(self.tokens.pen(self.tokens.waveform_stroke, 1.0))
            levels = self.waveform_levels or [self.waveform_peaks]
            total_pixel_width = max(width, int(width * self.zoom_level))
            level_index = 0
            while level_index + 1 < len(levels) and (len(levels[level_index]) / max(1, total_pixel_width)) > 2.0:
                level_index += 1
            peaks = levels[level_index]
            total_peaks = len(peaks)
            dur = max(0.001, self.duration)
            waveform_lines = []
            for x in range(width):
                t0 = self.x_to_time(x, width)
                t1 = self.x_to_time(x + 1, width)
                start_idx = int((t0 / dur) * total_peaks)
                end_idx = int((t1 / dur) * total_peaks)
                end_idx = max(start_idx + 1, end_idx)
                start_idx = max(0, min(total_peaks, start_idx))
                end_idx = max(0, min(total_peaks, end_idx))
                if start_idx >= total_peaks or end_idx <= start_idx:
                    continue

                peak_slice = peaks[start_idx:end_idx]
                if hasattr(peak_slice, "__len__") and len(peak_slice) > 0:
                    try:
                        max_val = float(np.max(peak_slice)) if (HAVE_NUMPY and np is not None and isinstance(peak_slice, np.ndarray)) else float(max(peak_slice))
                    except Exception:
                        max_val = float(max(peak_slice))
                    amplitude = max_val * (waveform_height * 0.88)
                    if amplitude > 0.5:
                        waveform_lines.append(
                            QLineF(x + 0.5, middle_y - amplitude / 2.0, x + 0.5, middle_y + amplitude / 2.0)
                        )
            if waveform_lines:
                painter.drawLines(waveform_lines)
        elif self.show_waveform and waveform_height > 0:
            painter.setPen(self.tokens.pen(self.tokens.waveform_baseline, 1))
            painter.drawLine(QPointF(0, middle_y), QPointF(width, middle_y))

        painter.end()
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        waveform_height = height - self.RULER_HEIGHT

        if (self.pixmap_dirty or self.waveform_pixmap is None or 
            self._last_rendered_width != width or 
            self._last_rendered_height != height or
            self._last_rendered_scroll != self.scroll_offset or
            self._last_rendered_zoom != self.zoom_level):
            
            self.waveform_pixmap = self.render_waveform_buffer(width, height)
            self._last_rendered_width = width
            self._last_rendered_height = height
            self._last_rendered_scroll = self.scroll_offset
            self._last_rendered_zoom = self.zoom_level
            self.buffered_total_width = width
            self.pixmap_dirty = False

        if self.waveform_pixmap is not None:
            painter.drawPixmap(0, 0, self.waveform_pixmap)

        ruler_rect = QRectF(0, 0, width, self.RULER_HEIGHT)
        painter.fillRect(ruler_rect, self.tokens.ruler_background_color())
        painter.setPen(self.tokens.ruler_divider_pen())
        painter.drawLine(QPointF(0, self.RULER_HEIGHT), QPointF(width, self.RULER_HEIGHT))

        visible_dur = self.visible_duration()
        target_ticks = max(2, width // 100)
        base_interval = visible_dur / target_ticks

        nice_intervals = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
        chosen_interval = nice_intervals[-1]
        for step in nice_intervals:
            if base_interval <= step:
                chosen_interval = step
                break

        painter.setFont(self.font())
        painter.setPen(self.tokens.ruler_tick_pen())

        start_tick = (self.scroll_offset // chosen_interval) * chosen_interval
        t = start_tick

        while t <= self.scroll_offset + visible_dur:
            x = self.time_to_x(t, width)
            if 0 <= x <= width:
                painter.drawLine(QPointF(x, self.RULER_HEIGHT - 6), QPointF(x, self.RULER_HEIGHT))

                mins = int(t // 60)
                secs = int(t % 60)
                hrs = int(mins // 60)
                mins = mins % 60

                label = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"
                text_rect = QRectF(x + 3, 2, 60, self.RULER_HEIGHT - 4)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

            t += chosen_interval

        audio_name = getattr(self, "audio_file_name", None)
        if audio_name:
            painter.setPen(self.tokens.pen(self.tokens.audio_label_text, 1.0))
            filename_rect = QRectF(8, self.RULER_HEIGHT + 4, 300, 18)
            painter.drawText(filename_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Audio: {audio_name}")

        if self.transcript_selection_range:
            sel_start, sel_end = self.transcript_selection_range
            sx = self.time_to_x(sel_start, width)
            ex = self.time_to_x(sel_end, width)
            left = max(0, min(width, sx))
            right = max(0, min(width, ex))
            if right > left:
                painter.fillRect(QRectF(left, self.RULER_HEIGHT, right-left, waveform_height), self.tokens.selection_rect_brush(is_transcript=True))
                painter.setPen(self.tokens.selection_rect_pen())
                painter.drawLine(QPointF(left, self.RULER_HEIGHT), QPointF(left, height))
                painter.drawLine(QPointF(right, self.RULER_HEIGHT), QPointF(right, height))

        # Draw active right-click drag selection with adjustable edge handles
        if self.selection_start is not None and self.selection_end is not None:
            sx = self.time_to_x(self.selection_start, width)
            ex = self.time_to_x(self.selection_end, width)
            left = max(0.0, min(float(width), min(sx, ex)))
            right = max(0.0, min(float(width), max(sx, ex)))
            if right > left:
                painter.fillRect(QRectF(left, self.RULER_HEIGHT, right - left, waveform_height), self.tokens.selection_rect_brush(is_transcript=False))
                painter.setPen(self.tokens.selection_rect_pen())
                painter.drawRect(QRectF(left, self.RULER_HEIGHT, right - left, waveform_height))
                painter.fillRect(QRectF(left - 3, self.RULER_HEIGHT, 6, waveform_height), self.tokens.selection_handle_brush())
                painter.fillRect(QRectF(right - 3, self.RULER_HEIGHT, 6, waveform_height), self.tokens.selection_handle_brush())

        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)

            if end_x < 0 or start_x > width:
                continue

            is_selected = index in self.selected_story_indices
            rect_start = max(0, start_x)
            rect_end = min(width, end_x)

            painter.fillRect(
                QRectF(rect_start, self.RULER_HEIGHT, max(1, rect_end - rect_start), waveform_height),
                self.tokens.story_segment_brush(index, is_selected=is_selected),
            )

            # --- Audio Fade Ramps & Envelope Visualization ---
            if getattr(self, "show_audio_fades", False):
                fin = getattr(story, "fade_in", 0.0)
                fout = getattr(story, "fade_out", 0.0)
                fcurve = getattr(story, "fade_curve", "linear") or "linear"
                story_dur = max(0.001, story.end - story.start)
                fin = max(0.0, min(fin, story_dur))
                fout = max(0.0, min(fout, max(0.0, story_dur - fin)))

                top_y = float(self.RULER_HEIGHT)
                bottom_y = float(height)

                fin_apex_x = self.time_to_x(story.start + fin, width)
                if fin > 0:
                    if fin_apex_x >= 0 and start_x <= width:
                        in_path = QPainterPath()
                        in_path.moveTo(start_x, bottom_y)
                        steps = 16
                        for step_i in range(1, steps + 1):
                            u = step_i / float(steps)
                            px = start_x + u * (fin_apex_x - start_x)
                            val = calculate_fade_curve_factor(u, fcurve)
                            py = bottom_y - val * (bottom_y - top_y)
                            in_path.lineTo(px, py)

                        # Fill shaded polygon area under curve
                        fill_path = QPainterPath(in_path)
                        fill_path.lineTo(start_x, top_y)
                        fill_path.lineTo(start_x, bottom_y)
                        fill_path.closeSubpath()

                        painter.setBrush(QColor(0, 0, 0, 85 if is_selected else 55))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawPath(fill_path)

                        # Smooth ramp stroke
                        ramp_pen = QPen(QColor("#38bdf8" if is_selected else "#7dd3fc"), 1.2)
                        painter.setPen(ramp_pen)
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawPath(in_path)

                # Tactile Grab Handle for Fade-In at apex along top edge
                if 0 <= fin_apex_x <= width:
                    handle_color = QColor("#38bdf8" if is_selected else "#60a5fa")
                    painter.setPen(QPen(handle_color.darker(130), 1))
                    painter.setBrush(handle_color)
                    painter.drawRoundedRect(QRectF(fin_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

                fout_apex_x = self.time_to_x(story.end - fout, width)
                if fout > 0:
                    if end_x >= 0 and fout_apex_x <= width:
                        out_path = QPainterPath()
                        out_path.moveTo(fout_apex_x, top_y)
                        steps = 16
                        for step_i in range(1, steps + 1):
                            u = step_i / float(steps)
                            px = fout_apex_x + u * (end_x - fout_apex_x)
                            # fade out volume factor goes from 1.0 down to 0.0 matching preview cues
                            val = calculate_fade_out_factor(u, fcurve)
                            py = bottom_y - val * (bottom_y - top_y)
                            out_path.lineTo(px, py)

                        fill_path = QPainterPath(out_path)
                        fill_path.lineTo(end_x, top_y)
                        fill_path.lineTo(fout_apex_x, top_y)
                        fill_path.closeSubpath()

                        painter.setBrush(QColor(0, 0, 0, 85 if is_selected else 55))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawPath(fill_path)

                        # Smooth ramp stroke
                        ramp_pen = QPen(QColor("#f43f5e" if is_selected else "#fb7185"), 1.2)
                        painter.setPen(ramp_pen)
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawPath(out_path)

                # Tactile Grab Handle for Fade-Out at apex along top edge
                if 0 <= fout_apex_x <= width:
                    handle_color = QColor("#f43f5e" if is_selected else "#f87171")
                    painter.setPen(QPen(handle_color.darker(130), 1))
                    painter.setBrush(handle_color)
                    painter.drawRoundedRect(QRectF(fout_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

            painter.setPen(self.tokens.story_segment_pen(index, is_selected=is_selected))
            if 0 <= start_x <= width:
                painter.drawLine(QPointF(start_x, self.RULER_HEIGHT), QPointF(start_x, height))
            if 0 <= end_x <= width:
                painter.drawLine(QPointF(end_x, self.RULER_HEIGHT), QPointF(end_x, height))

        # Draw Playhead Line
        cursor_x = self.time_to_x(self.position, width)
        if 0 <= cursor_x <= width:
            painter.setPen(self.tokens.playhead_pen(2.0))
            painter.drawLine(QPointF(cursor_x, 0), QPointF(cursor_x, height))

        # Draw Background Task Status Banner (Waveform / Thumbnail Generation)
        if self.show_background_banner and self.background_status_text:
            painter.save()
            font = self.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(self.background_status_text)
            badge_w = text_w + 24
            badge_h = 24
            badge_x = (width - badge_w) / 2.0
            badge_y = self.RULER_HEIGHT + 8

            badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
            painter.setPen(self.tokens.pen(self.tokens.status_banner_border, 1.5))
            painter.setBrush(self.tokens.brush(self.tokens.status_banner_bg, 230))
            painter.drawRoundedRect(badge_rect, 4.0, 4.0)

            painter.setPen(self.tokens.color(self.tokens.status_banner_text))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.background_status_text)
            painter.restore()


class TimelineResizeHandle(QWidget):
    """Visual drag-handle at the bottom of the timeline allowing vertical resizing."""
    def __init__(self, target_widget, parent=None):
        super().__init__(parent or target_widget)
        self.target_widget = target_widget
        self.setFixedHeight(7)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setToolTip("Drag down/up to resize timeline height")
        self._dragging = False
        self._start_y = 0
        self._start_h = 140

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Background bar
        is_dark = self.palette().window().color().value() < 128
        bg_color = QColor("#161b22") if is_dark else QColor("#e1e4e8")
        painter.fillRect(self.rect(), bg_color)

        # Center grip pill
        grip_color = QColor("#484f58") if is_dark else QColor("#8c959f")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grip_color)
        cx = self.width() // 2
        cy = self.height() // 2
        painter.drawRoundedRect(QRectF(cx - 24, cy - 1.5, 48, 3), 1.5, 1.5)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            self._start_h = self.target_widget.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            cur_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            delta = int(cur_y - self._start_y)
            new_h = max(90, min(500, self._start_h + delta))
            if new_h != self.target_widget.height():
                self.target_widget.setFixedHeight(new_h)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                settings.setValue("timeline_height", self.target_widget.height())
                settings.sync()
            except Exception:
                pass
            event.accept()
            return
        super().mouseReleaseEvent(event)


class TimelineOverviewBar(QWidget):
    """Interactive navigation overview pill below the timeline with drag-to-zoom edge handles."""
    valueChanged = Signal(int)

    HANDLE_WIDTH = 7
    BAR_HEIGHT = 16

    def __init__(self, canvas, parent=None, tokens=None):
        super().__init__(parent)
        self.canvas = canvas
        self.tokens = tokens if tokens is not None else ThemeTokens()
        self.setFixedHeight(self.BAR_HEIGHT)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._dragging = None  # None, 'pan', 'left_handle', 'right_handle'
        self._drag_start_x = 0
        self._drag_start_offset = 0.0
        self._drag_fixed_left = 0.0
        self._drag_fixed_right = 0.0
        self._hover_handle = None

        if hasattr(self.canvas, "scrollOffsetChanged"):
            self.canvas.scrollOffsetChanged.connect(lambda _: self.update())
        if hasattr(self.canvas, "zoomChanged"):
            self.canvas.zoomChanged.connect(self.update)

    def get_pill_rect(self):
        w = max(1, self.width())
        dur = max(0.001, getattr(self.canvas, "duration", 1.0))
        vis = min(dur, max(0.001, self.canvas.visible_duration()))
        offset = max(0.0, min(dur - vis, getattr(self.canvas, "scroll_offset", 0.0)))

        pill_x = (offset / dur) * w
        pill_w = max(16.0, (vis / dur) * w)
        if pill_x + pill_w > w:
            pill_x = max(0.0, w - pill_w)

        return QRectF(pill_x, 2.0, pill_w, max(4.0, self.height() - 4.0))

    def _hit_test(self, pos_x):
        pill = self.get_pill_rect()
        if not pill.contains(QPointF(pos_x, self.height() / 2.0)):
            return 'track'

        # Left edge handle hit (resizable)
        if abs(pos_x - pill.left()) <= self.HANDLE_WIDTH:
            return 'left'
        # Right edge handle hit (resizable)
        if abs(pos_x - pill.right()) <= self.HANDLE_WIDTH:
            return 'right'

        return 'pill'

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            w = max(1, self.width())
            h = max(1, self.height())
            dur = max(0.001, getattr(self.canvas, "duration", 1.0))

            is_dark = self.palette().window().color().value() < 128

            # 1. Track background
            track_bg = QColor("#161b22") if is_dark else QColor("#e8ecf1")
            track_border = QColor("#21262d") if is_dark else QColor("#d0d7de")
            painter.setPen(QPen(track_border, 1.0))
            painter.setBrush(track_bg)
            painter.drawRoundedRect(QRectF(0.5, 1.0, w - 1.0, h - 2.0), 3.0, 3.0)

            # 2. Mini story segments in overview
            stories = getattr(self.canvas, "stories", [])
            if stories and dur > 0:
                for s_idx, story in enumerate(stories):
                    s_start = max(0.0, min(dur, getattr(story, "start", 0.0)))
                    s_end = max(s_start, min(dur, getattr(story, "end", 0.0)))
                    if s_end > s_start:
                        sx = (s_start / dur) * w
                        sw = max(2.0, ((s_end - s_start) / dur) * w)
                        s_color = self.tokens.story_segment_color(s_idx, alpha=110 if is_dark else 130)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(s_color)
                        painter.drawRect(QRectF(sx, 3.0, sw, h - 6.0))

            # 3. Viewport Pill
            pill = self.get_pill_rect()

            # Pill base style
            if self._dragging == 'pan' or self._hover_handle == 'pill':
                pill_bg = QColor("#3f4c60") if is_dark else QColor("#9aa8ba")
                pill_border = QColor("#58a6ff") if is_dark else QColor("#0969da")
            else:
                pill_bg = QColor("#303846") if is_dark else QColor("#afbccb")
                pill_border = QColor("#485569") if is_dark else QColor("#8c99a8")

            painter.setPen(QPen(pill_border, 1.0))
            painter.setBrush(pill_bg)
            painter.drawRoundedRect(pill, 4.0, 4.0)

            # 4. Resizable Left & Right edge grab handles
            left_h_active = (self._hover_handle == 'left' or self._dragging == 'left_handle')
            right_h_active = (self._hover_handle == 'right' or self._dragging == 'right_handle')

            # Left handle styling
            if left_h_active:
                painter.setBrush(QColor("#38bdf8" if is_dark else "#0284c7"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(pill.left(), pill.top(), 5.0, pill.height()), 2.0, 2.0)
            else:
                painter.setPen(QPen(QColor("#8b949e" if is_dark else "#ffffff"), 1.2))
                mid_y = pill.top() + pill.height() / 2.0
                painter.drawLine(QPointF(pill.left() + 3.0, mid_y - 3.0), QPointF(pill.left() + 3.0, mid_y + 3.0))

            # Right handle styling
            if right_h_active:
                painter.setBrush(QColor("#38bdf8" if is_dark else "#0284c7"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(pill.right() - 5.0, pill.top(), 5.0, pill.height()), 2.0, 2.0)
            else:
                painter.setPen(QPen(QColor("#8b949e" if is_dark else "#ffffff"), 1.2))
                mid_y = pill.top() + pill.height() / 2.0
                painter.drawLine(QPointF(pill.right() - 3.0, mid_y - 3.0), QPointF(pill.right() - 3.0, mid_y + 3.0))

            # 5. Playhead indicator tick
            pos = getattr(self.canvas, "position", 0.0)
            if 0 <= pos <= dur:
                cur_x = (pos / dur) * w
                painter.setPen(QPen(QColor("#ef4444" if is_dark else "#dc2626"), 1.5))
                painter.drawLine(QPointF(cur_x, 1.0), QPointF(cur_x, h - 1.0))
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos_x = event.position().x()
            w = max(1, self.width())
            dur = max(0.001, getattr(self.canvas, "duration", 1.0))
            hit = self._hit_test(pos_x)

            if hit == 'left':
                self._dragging = 'left_handle'
                self._drag_start_x = pos_x
                self._drag_fixed_right = self.canvas.scroll_offset + self.canvas.visible_duration()
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.update()
                event.accept()
                return

            elif hit == 'right':
                self._dragging = 'right_handle'
                self._drag_start_x = pos_x
                self._drag_fixed_left = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.update()
                event.accept()
                return

            elif hit == 'pill':
                self._dragging = 'pan'
                self._drag_start_x = pos_x
                self._drag_start_offset = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                event.accept()
                return

            elif hit == 'track':
                # Center viewport around clicked position
                clicked_time = (pos_x / w) * dur
                vis = self.canvas.visible_duration()
                self.canvas.scroll_offset = clicked_time - (vis / 2.0)
                self.canvas.clamp_scroll_offset()
                self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
                self.canvas.pixmap_dirty = True
                self.canvas.update()

                self._dragging = 'pan'
                self._drag_start_x = pos_x
                self._drag_start_offset = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos_x = event.position().x()
        w = max(1, self.width())
        dur = max(0.001, getattr(self.canvas, "duration", 1.0))

        if self._dragging == 'pan':
            dx = pos_x - self._drag_start_x
            dt = (dx / w) * dur
            self.canvas.scroll_offset = self._drag_start_offset + dt
            self.canvas.clamp_scroll_offset()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        elif self._dragging == 'left_handle':
            new_left_time = max(0.0, min(self._drag_fixed_right - 0.1, (pos_x / w) * dur))
            new_vis_dur = max(0.05, self._drag_fixed_right - new_left_time)
            min_vis = dur / self.canvas.max_zoom
            max_vis = dur / self.canvas.min_zoom
            new_vis_dur = max(min_vis, min(max_vis, new_vis_dur))
            new_left_time = max(0.0, self._drag_fixed_right - new_vis_dur)

            self.canvas.zoom_level = max(self.canvas.min_zoom, min(self.canvas.max_zoom, dur / new_vis_dur))
            self.canvas.scroll_offset = new_left_time
            self.canvas.clamp_scroll_offset()
            self.canvas.zoomChanged.emit()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        elif self._dragging == 'right_handle':
            new_right_time = min(dur, max(self._drag_fixed_left + 0.1, (pos_x / w) * dur))
            new_vis_dur = max(0.05, new_right_time - self._drag_fixed_left)
            min_vis = dur / self.canvas.max_zoom
            max_vis = dur / self.canvas.min_zoom
            new_vis_dur = max(min_vis, min(max_vis, new_vis_dur))

            self.canvas.zoom_level = max(self.canvas.min_zoom, min(self.canvas.max_zoom, dur / new_vis_dur))
            self.canvas.scroll_offset = self._drag_fixed_left
            self.canvas.clamp_scroll_offset()
            self.canvas.zoomChanged.emit()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        hit = self._hit_test(pos_x)
        self._hover_handle = hit
        if hit in ('left', 'right'):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.setToolTip("Drag edge to zoom in or out")
        elif hit == 'pill':
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setToolTip("Drag pill to scroll timeline")
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip("Click to jump to point in timeline")
        self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging is not None:
            self._dragging = None
            pos_x = event.position().x()
            hit = self._hit_test(pos_x)
            if hit in ('left', 'right'):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif hit == 'pill':
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self._hover_handle = None
        self.update()
        super().leaveEvent(event)

    def setRange(self, min_val, max_val):
        self.update()

    def setPageStep(self, step):
        self.update()

    def setSingleStep(self, step):
        self.update()

    def setValue(self, val):
        self.update()


class TimelineWidget(QWidget):
    mediaDropped = Signal(str)

    def __init__(self, parent=None, tokens=None):
        super().__init__(parent)
        self.tokens = tokens if tokens is not None else getattr(parent, "tokens", ThemeTokens())
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas = TimelineCanvas(self, tokens=self.tokens)
        self.overview_bar = TimelineOverviewBar(self.canvas, parent=self, tokens=self.tokens)
        self.scrollbar = self.overview_bar
        self.resize_handle = TimelineResizeHandle(self)

        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.overview_bar)
        layout.addWidget(self.resize_handle)

        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        saved_h = settings.value("timeline_height", 140)
        try:
            saved_h = int(saved_h)
        except (ValueError, TypeError):
            saved_h = 140
        saved_h = max(90, min(500, saved_h))
        self.setFixedHeight(saved_h)

        self.canvas.scrollOffsetChanged.connect(self.update_scrollbar_from_canvas)
        self.canvas.mediaDropped.connect(self.mediaDropped.emit)
        self.canvas.zoomChanged.connect(self.update_scrollbar_range)
        self.scrollbar.valueChanged.connect(self.update_canvas_from_scrollbar)

        self.selectionRangeChanged = self.canvas.selectionRangeChanged
        self.storyCreatedFromSelection = self.canvas.storyCreatedFromSelection
        self.storyClicked = self.canvas.storyClicked

        self.is_internal_scrollbar_update = False
        self.update_scrollbar_range()

    def set_is_video(self, is_video: bool):
        if hasattr(self, "canvas") and hasattr(self.canvas, "set_is_video"):
            self.canvas.set_is_video(is_video)

    def set_background_generation_active(self, task_name: str, active: bool):
        if hasattr(self, "canvas") and hasattr(self.canvas, "set_background_generation_active"):
            self.canvas.set_background_generation_active(task_name, active)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.mediaDropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def update_scrollbar_range(self):
        self.is_internal_scrollbar_update = True
        total = int(self.canvas.duration * 1000)
        visible = int(self.canvas.visible_duration() * 1000)

        self.scrollbar.setRange(0, max(0, total - visible))
        self.scrollbar.setPageStep(visible)
        self.scrollbar.setSingleStep(max(100, visible // 10))
        self.is_internal_scrollbar_update = False
        self.update_scrollbar_from_canvas(self.canvas.scroll_offset)

    def update_scrollbar_from_canvas(self, offset):
        if self.is_internal_scrollbar_update:
            return

        self.is_internal_scrollbar_update = True
        try:
            self.scrollbar.setValue(int(offset * 1000))
        finally:
            self.is_internal_scrollbar_update = False

    def update_canvas_from_scrollbar(self, val):
        if self.is_internal_scrollbar_update:
            return

        self.is_internal_scrollbar_update = True
        try:
            self.canvas.scroll_offset = val / 1000.0
            self.canvas.clamp_scroll_offset()
            self.canvas.update()
        finally:
            self.is_internal_scrollbar_update = False

    def __getattr__(self, name):
        return getattr(self.canvas, name)


# ============================================================
# Main Window
# ============================================================




class StoryListWidget(QListWidget):
    """QListWidget subclass for story segmentation list with right-click context menu and drag-drop support."""
    deleteRequested = Signal()
    exportRequested = Signal()
    exportStoryWordPressRequested = Signal()
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.filesDropped.emit(paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _show_context_menu(self, pos):
        parent = self.parent()
        while parent and not hasattr(parent, "open_story_fades_dialog"):
            parent = parent.parent()
        if not parent:
            return

        if not self.selectedItems():
            return

        menu = QMenu(self)

        audition_act = QAction("Audition Story Playback", self)
        audition_act.triggered.connect(lambda: parent.audition_story(self.currentRow()))
        menu.addAction(audition_act)

        menu.addSeparator()

        fade_menu = menu.addMenu("Audio Fades")

        adjust_fades_act = QAction("Adjust Fades for Selected Story...", self)
        adjust_fades_act.triggered.connect(lambda: parent.open_story_fades_dialog())
        fade_menu.addAction(adjust_fades_act)

        apply_default_fades_act = QAction("Apply Default Fades to Selected Stories", self)
        apply_default_fades_act.triggered.connect(lambda: parent.apply_fades_to_selected_stories())
        fade_menu.addAction(apply_default_fades_act)

        remove_fades_act = QAction("Remove Fades from Selected Stories", self)
        remove_fades_act.triggered.connect(lambda: parent.remove_fades_from_selected_stories())
        fade_menu.addAction(remove_fades_act)

        fade_menu.addSeparator()
        curve_menu = fade_menu.addMenu("Set Fade Curve Profile")

        # Determine current curve from selected story if available
        curr_curve = "linear"
        if hasattr(parent, "stories") and parent.stories:
            curr_row = self.currentRow()
            if 0 <= curr_row < len(parent.stories):
                curr_curve = getattr(parent.stories[curr_row], "fade_curve", "linear") or "linear"

        for profile in FADE_CURVE_PROFILES:
            cid = profile["id"]
            icon = create_fade_curve_icon(cid, width=44, height=22)
            act = QAction(icon, f"{profile['symbol']}  {profile['full_name']}", self)
            act.setIconVisibleInMenu(True)
            act.setCheckable(True)
            act.setChecked(cid == curr_curve)
            act.setToolTip(profile["desc"])
            act.triggered.connect(lambda checked=False, ck=cid: parent.set_fade_curve_for_selected_stories(ck))
            curve_menu.addAction(act)

        menu.addSeparator()

        export_act = QAction("Export Selected Stories...", self)
        export_act.triggered.connect(lambda: self.exportRequested.emit())
        menu.addAction(export_act)

        wp_act = QAction("Export to WordPress / CMS...", self)
        wp_act.triggered.connect(lambda: self.exportStoryWordPressRequested.emit())
        menu.addAction(wp_act)

        menu.addSeparator()

        del_act = QAction("Delete Selected Story", self)
        del_act.triggered.connect(lambda: self.deleteRequested.emit())
        menu.addAction(del_act)

        menu.exec(self.mapToGlobal(pos))


class BatchFileListWidget(QListWidget):
    filesDropped = Signal(list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

class BatchProcessingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.resize(700, 670)
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Add media files or documents. Drag and drop files or folders directly into the list below."))

        # File List View
        self.files = BatchFileListWidget()
        self.files.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.files, 1)

        row = QHBoxLayout()
        add = QPushButton("Add Files…")
        rem = QPushButton("Remove Selected")
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch()
        layout.addLayout(row)

        # Output / Project Directory Selector
        dir_group = QGroupBox("Target Save Location")
        dir_layout = QHBoxLayout(dir_group)
        self.output = QLineEdit()
        self.output.setPlaceholderText("Default (project folder or media file directory if empty)")
        browse = QPushButton("Browse Folder…")
        dir_layout.addWidget(self.output, 1)
        dir_layout.addWidget(browse)
        layout.addWidget(dir_group)

        # --- Section 1: Pipeline & Process Selection ---
        proc_group = QGroupBox("1. Processing Pipeline Selection")
        proc_layout = QVBoxLayout(proc_group)

        self.pipeline_full_radio = QRadioButton("Run Full Processing Pipeline (Transcribe + Diarize + Detect Stories)")
        self.pipeline_full_radio.setChecked(True)
        self.pipeline_custom_radio = QRadioButton("Select Specific Processes to Run:")
        
        proc_layout.addWidget(self.pipeline_full_radio)
        proc_layout.addWidget(self.pipeline_custom_radio)

        # Custom process checkboxes
        self.custom_proc_widget = QWidget()
        custom_proc_layout = QVBoxLayout(self.custom_proc_widget)
        custom_proc_layout.setContentsMargins(20, 0, 0, 0)

        self.proc_transcribe = QCheckBox("Transcription")
        self.proc_transcribe.setChecked(True)
        custom_proc_layout.addWidget(self.proc_transcribe)

        # -- Speaker Detection (formerly "Diarize Speakers") --
        speaker_row = QHBoxLayout()
        self.proc_diarize = QCheckBox("Speaker Detection")
        self.proc_diarize.setChecked(True)
        speaker_row.addWidget(self.proc_diarize)
        speaker_row.addWidget(QLabel("Expected Speakers:"))
        self.batch_expected_speakers_combo = QComboBox()
        self.batch_expected_speakers_combo.addItem("Auto-Detect", "auto")
        self.batch_expected_speakers_combo.addItem("1 Speaker (Solo Fast-Path)", "1")
        self.batch_expected_speakers_combo.addItem("2 Speakers (Interview)", "2")
        self.batch_expected_speakers_combo.addItem("3+ Speakers (Panel / Group)", "3+")
        default_expected = str(getattr(parent, "expected_speakers", "auto") or "auto")
        default_idx = self.batch_expected_speakers_combo.findData(default_expected)
        self.batch_expected_speakers_combo.setCurrentIndex(default_idx if default_idx >= 0 else 0)
        speaker_row.addWidget(self.batch_expected_speakers_combo, 1)
        custom_proc_layout.addLayout(speaker_row)
        self.proc_diarize.toggled.connect(self.batch_expected_speakers_combo.setEnabled)
        self.batch_expected_speakers_combo.setEnabled(self.proc_diarize.isChecked())

        # -- Story Detection --
        stories_row = QHBoxLayout()
        self.proc_stories = QCheckBox("Story Detection")
        self.proc_stories.setChecked(True)
        stories_row.addWidget(self.proc_stories)
        stories_row.addWidget(QLabel("Silence Gap:"))
        self.batch_gap_spin = QDoubleSpinBox()
        self.batch_gap_spin.setRange(0.5, 30.0)
        self.batch_gap_spin.setSingleStep(0.5)
        self.batch_gap_spin.setSuffix(" sec")
        self.batch_gap_spin.setValue(3.0)
        stories_row.addWidget(self.batch_gap_spin)
        stories_row.addWidget(QLabel("Lead-in:"))
        self.batch_pad_spin = QDoubleSpinBox()
        self.batch_pad_spin.setRange(0.0, 5.0)
        self.batch_pad_spin.setSingleStep(0.1)
        self.batch_pad_spin.setSuffix(" sec")
        self.batch_pad_spin.setValue(0.2)
        stories_row.addWidget(self.batch_pad_spin)
        custom_proc_layout.addLayout(stories_row)
        self.proc_stories.toggled.connect(self.batch_gap_spin.setEnabled)
        self.proc_stories.toggled.connect(self.batch_pad_spin.setEnabled)
        self.batch_gap_spin.setEnabled(self.proc_stories.isChecked())
        self.batch_pad_spin.setEnabled(self.proc_stories.isChecked())

        # -- Translation (formerly "Spanish Translation") --
        translate_row = QHBoxLayout()
        self.proc_translate = QCheckBox("Translation")
        self.proc_translate.setChecked(False)
        translate_row.addWidget(self.proc_translate)
        translate_row.addWidget(QLabel("Direction:"))
        self.batch_translate_direction_combo = QComboBox()
        self.batch_translate_direction_combo.addItem("Auto-Detect (Flip EN \u2194 ES)", "auto")
        self.batch_translate_direction_combo.addItem("English to Spanish", "en-es")
        self.batch_translate_direction_combo.addItem("Spanish to English", "es-en")
        translate_row.addWidget(self.batch_translate_direction_combo, 1)
        custom_proc_layout.addLayout(translate_row)
        self.proc_translate.toggled.connect(self.batch_translate_direction_combo.setEnabled)
        self.batch_translate_direction_combo.setEnabled(self.proc_translate.isChecked())
        proc_layout.addWidget(self.custom_proc_widget)
        self.custom_proc_widget.setEnabled(False)

        self.pipeline_custom_radio.toggled.connect(self.custom_proc_widget.setEnabled)
        layout.addWidget(proc_group)

        # --- Section 2: Project & Save Options ---
        opts_group = QGroupBox("2. Project & Save Options")
        opts_layout = QVBoxLayout(opts_group)

        self.save_project_check = QCheckBox("Auto-save updated project (.rtvs) files to specified directory (or default)")
        self.save_project_check.setChecked(True)
        opts_layout.addWidget(self.save_project_check)

        self.skip_existing_check = QCheckBox("Skip re-processing if requested output files already exist")
        self.skip_existing_check.setChecked(True)
        opts_layout.addWidget(self.skip_existing_check)

        layout.addWidget(opts_group)

        # --- Section 3: Output Formats & Scope (for standard exports) ---
        self.export_group = QGroupBox("3. Output Formats & Scope")
        export_layout = QVBoxLayout(self.export_group)

        self.save_project_only_check = QCheckBox("Save projects only (do not export text or media files)")
        self.save_project_only_check.setChecked(False)
        self.save_project_only_check.setToolTip("Run the selected processing and save the resulting project files without creating transcript, subtitle, document, or media exports.")
        export_layout.addWidget(self.save_project_only_check)

        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel("Export Scope:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Full Transcripts Only", "full")
        self.scope_combo.addItem("Individual Stories Only", "stories")
        self.scope_combo.addItem("Full Transcripts + Individual Stories", "both")
        scope_row.addWidget(self.scope_combo, 1)
        export_layout.addLayout(scope_row)

        fmt_row = QHBoxLayout()
        self.fmt_txt = QCheckBox("TXT (.txt)")
        self.fmt_docx = QCheckBox("DOCX (.docx)")
        self.fmt_srt = QCheckBox("SRT (.srt)")
        self.fmt_vtt = QCheckBox("VTT (.vtt)")
        self.fmt_txt.setChecked(True)
        self.fmt_docx.setChecked(True)
        fmt_row.addWidget(self.fmt_txt)
        fmt_row.addWidget(self.fmt_docx)
        fmt_row.addWidget(self.fmt_srt)
        fmt_row.addWidget(self.fmt_vtt)
        export_layout.addLayout(fmt_row)

        details_row = QHBoxLayout()
        self.include_speakers = QCheckBox("Include speaker labels")
        self.include_speakers.setChecked(True)
        self.include_times = QCheckBox("Include timestamps")
        self.include_times.setChecked(False)
        self.translate_check = QCheckBox("Translate")
        details_row.addWidget(self.include_speakers)
        details_row.addWidget(self.include_times)
        details_row.addWidget(self.translate_check)
        export_layout.addLayout(details_row)

        self.batch_export_translate_direction_combo = QComboBox()
        self.batch_export_translate_direction_combo.addItem("Auto-Detect", "auto")
        self.batch_export_translate_direction_combo.addItem("English → Spanish", "en-es")
        self.batch_export_translate_direction_combo.addItem("Spanish → English", "es-en")
        export_translate_row = QHBoxLayout()
        export_translate_row.addWidget(QLabel("Translation Direction:"))
        export_translate_row.addWidget(self.batch_export_translate_direction_combo, 1)
        export_layout.addLayout(export_translate_row)

        layout.addWidget(self.export_group)

        def _on_save_project_only_toggled(checked):
            # Keep the group accessible but disable the file format & scope pickers
            self.scope_combo.setEnabled(not checked)
            self.fmt_txt.setEnabled(not checked)
            self.fmt_docx.setEnabled(not checked)
            self.fmt_srt.setEnabled(not checked)
            self.fmt_vtt.setEnabled(not checked)
            self.include_speakers.setEnabled(not checked)
            self.include_times.setEnabled(not checked)
            self.translate_check.setEnabled(not checked)
            self.batch_export_translate_direction_combo.setEnabled((not checked) and self.translate_check.isChecked())

        self.save_project_only_check.toggled.connect(_on_save_project_only_toggled)
        self.translate_check.toggled.connect(self.batch_export_translate_direction_combo.setEnabled)
        self.batch_export_translate_direction_combo.setEnabled(self.translate_check.isChecked())
        self.batch_translate_direction_combo.currentIndexChanged.connect(
            lambda idx: self.batch_export_translate_direction_combo.setCurrentIndex(idx)
            if 0 <= idx < self.batch_export_translate_direction_combo.count() else None
        )
        self.batch_export_translate_direction_combo.currentIndexChanged.connect(
            lambda idx: self.batch_translate_direction_combo.setCurrentIndex(idx)
            if 0 <= idx < self.batch_translate_direction_combo.count() else None
        )

        # Dialog Action Buttons and Default Management
        btns = QHBoxLayout()
        self.save_defaults_btn = QPushButton("Save Options as Default")
        self.reset_defaults_btn = QPushButton("Reset to Defaults")
        self.start = QPushButton("Start Batch")
        self.start.setDefault(True)
        cancel = QPushButton("Cancel")
        btns.addWidget(self.save_defaults_btn)
        btns.addWidget(self.reset_defaults_btn)
        btns.addStretch()
        btns.addWidget(self.start)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        # Load remembered preferences or defaults
        self._load_saved_options()

        # Signal Connections
        add.clicked.connect(self.add_files)
        rem.clicked.connect(lambda: [self.files.takeItem(self.files.row(i)) for i in self.files.selectedItems()])
        browse.clicked.connect(self.choose_output)
        self.save_defaults_btn.clicked.connect(lambda: self.save_options_to_settings(as_default=True))
        self.reset_defaults_btn.clicked.connect(self.reset_options_to_defaults)
        cancel.clicked.connect(self.reject)
        self.start.clicked.connect(self._on_start_clicked)
        
        self.files.filesDropped.connect(self.add_paths)
        self.files.model().rowsInserted.connect(self.auto_detect_options)
        self.files.model().rowsRemoved.connect(self.auto_detect_options)

    def _load_saved_options(self):
        parent = self.parent()
        settings = getattr(parent, "settings_store", None)
        if not settings:
            return
        pipe_mode = str(settings.value("batch_opt_pipeline_mode", "full"))
        if pipe_mode == "custom":
            self.pipeline_custom_radio.setChecked(True)
        else:
            self.pipeline_full_radio.setChecked(True)

        def _to_bool(val, default):
            if val is None:
                return default
            return str(val).lower() in ("true", "1", "yes")

        self.proc_transcribe.setChecked(_to_bool(settings.value("batch_opt_proc_transcribe"), True))
        self.proc_diarize.setChecked(_to_bool(settings.value("batch_opt_proc_diarize"), True))
        self.proc_stories.setChecked(_to_bool(settings.value("batch_opt_proc_stories"), True))
        self.proc_translate.setChecked(_to_bool(settings.value("batch_opt_proc_translate"), False))

        expected = str(settings.value("batch_opt_expected_speakers", getattr(parent, "expected_speakers", "auto") or "auto"))
        idx_exp = self.batch_expected_speakers_combo.findData(expected)
        if idx_exp >= 0:
            self.batch_expected_speakers_combo.setCurrentIndex(idx_exp)
        try:
            self.batch_gap_spin.setValue(float(settings.value("batch_opt_story_gap", 3.0) or 3.0))
            self.batch_pad_spin.setValue(float(settings.value("batch_opt_story_pad", 0.2) or 0.2))
        except (TypeError, ValueError):
            pass
        translate_dir = str(settings.value("batch_opt_translate_direction", "auto"))
        idx_dir = self.batch_translate_direction_combo.findData(translate_dir)
        if idx_dir >= 0:
            self.batch_translate_direction_combo.setCurrentIndex(idx_dir)
            self.batch_export_translate_direction_combo.setCurrentIndex(idx_dir)

        self.save_project_check.setChecked(_to_bool(settings.value("batch_opt_save_project"), True))
        self.skip_existing_check.setChecked(_to_bool(settings.value("batch_opt_skip_existing"), True))
        self.save_project_only_check.setChecked(_to_bool(settings.value("batch_opt_save_project_only"), False))

        scope = str(settings.value("batch_opt_scope", "full"))
        idx = self.scope_combo.findData(scope)
        if idx >= 0:
            self.scope_combo.setCurrentIndex(idx)

        self.fmt_txt.setChecked(_to_bool(settings.value("batch_opt_fmt_txt"), True))
        self.fmt_docx.setChecked(_to_bool(settings.value("batch_opt_fmt_docx"), True))
        self.fmt_srt.setChecked(_to_bool(settings.value("batch_opt_fmt_srt"), False))
        self.fmt_vtt.setChecked(_to_bool(settings.value("batch_opt_fmt_vtt"), False))

        self.include_speakers.setChecked(_to_bool(settings.value("batch_opt_include_speakers"), True))
        self.include_times.setChecked(_to_bool(settings.value("batch_opt_include_times"), False))
        self.translate_check.setChecked(_to_bool(settings.value("batch_opt_translate_check"), False))

    def save_options_to_settings(self, as_default=False):
        parent = self.parent()
        settings = getattr(parent, "settings_store", None)
        if not settings:
            return
        pipe_mode = "custom" if self.pipeline_custom_radio.isChecked() else "full"
        settings.setValue("batch_opt_pipeline_mode", pipe_mode)
        settings.setValue("batch_opt_proc_transcribe", self.proc_transcribe.isChecked())
        settings.setValue("batch_opt_proc_diarize", self.proc_diarize.isChecked())
        settings.setValue("batch_opt_proc_stories", self.proc_stories.isChecked())
        settings.setValue("batch_opt_proc_translate", self.proc_translate.isChecked())
        settings.setValue("batch_opt_expected_speakers", self.batch_expected_speakers_combo.currentData())
        settings.setValue("batch_opt_story_gap", self.batch_gap_spin.value())
        settings.setValue("batch_opt_story_pad", self.batch_pad_spin.value())
        settings.setValue("batch_opt_translate_direction", self.batch_export_translate_direction_combo.currentData())

        settings.setValue("batch_opt_save_project", self.save_project_check.isChecked())
        settings.setValue("batch_opt_skip_existing", self.skip_existing_check.isChecked())
        settings.setValue("batch_opt_save_project_only", self.save_project_only_check.isChecked())

        settings.setValue("batch_opt_scope", self.scope_combo.currentData())
        settings.setValue("batch_opt_fmt_txt", self.fmt_txt.isChecked())
        settings.setValue("batch_opt_fmt_docx", self.fmt_docx.isChecked())
        settings.setValue("batch_opt_fmt_srt", self.fmt_srt.isChecked())
        settings.setValue("batch_opt_fmt_vtt", self.fmt_vtt.isChecked())

        settings.setValue("batch_opt_include_speakers", self.include_speakers.isChecked())
        settings.setValue("batch_opt_include_times", self.include_times.isChecked())
        settings.setValue("batch_opt_translate_check", self.translate_check.isChecked())
        if as_default:
            QMessageBox.information(self, "Batch Options", "Current batch export options saved as defaults.")

    def reset_options_to_defaults(self):
        self.pipeline_full_radio.setChecked(True)
        self.proc_transcribe.setChecked(True)
        self.proc_diarize.setChecked(True)
        self.proc_stories.setChecked(True)
        self.proc_translate.setChecked(False)
        idx_exp = self.batch_expected_speakers_combo.findData("auto")
        if idx_exp >= 0:
            self.batch_expected_speakers_combo.setCurrentIndex(idx_exp)
        self.batch_gap_spin.setValue(3.0)
        self.batch_pad_spin.setValue(0.2)
        idx_dir = self.batch_translate_direction_combo.findData("auto")
        if idx_dir >= 0:
            self.batch_translate_direction_combo.setCurrentIndex(idx_dir)
            self.batch_export_translate_direction_combo.setCurrentIndex(idx_dir)

        self.save_project_check.setChecked(True)
        self.skip_existing_check.setChecked(True)
        self.save_project_only_check.setChecked(False)

        idx = self.scope_combo.findData("full")
        if idx >= 0:
            self.scope_combo.setCurrentIndex(idx)

        self.fmt_txt.setChecked(True)
        self.fmt_docx.setChecked(True)
        self.fmt_srt.setChecked(False)
        self.fmt_vtt.setChecked(False)

        self.include_speakers.setChecked(True)
        self.include_times.setChecked(False)
        self.translate_check.setChecked(False)
       
        self.save_options_to_settings()
        QMessageBox.information(self, "Batch Options", "Batch export options reset to factory defaults.")

    def _on_start_clicked(self):
        self.save_options_to_settings(as_default=False)
        self.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.add_paths(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_paths(self, paths):
        for f in paths:
            p = Path(f)
            if p.is_file() and not any(self.files.item(i).text() == str(p) for i in range(self.files.count())):
                self.files.addItem(str(p))
            elif p.is_dir():
                for sub in sorted(p.rglob("*")):
                    if sub.is_file() and not any(self.files.item(i).text() == str(sub) for i in range(self.files.count())):
                        self.files.addItem(str(sub))
        self.auto_detect_options()

    def add_files(self):
        filters = "All Supported Files (*.*)"
        parent = self.parent()
        settings = getattr(parent, "settings_store", None)
        default_dir = ""
        if settings is not None:
            default_dir = str(settings.value("batch_add_files_directory", "") or "")
        if not default_dir:
            default_dir = getattr(parent, "_dialog_directory", lambda: "")()
        files, _ = QFileDialog.getOpenFileNames(self, "Add Files", default_dir, filters)
        if files and settings is not None:
            settings.setValue("batch_add_files_directory", str(Path(files[0]).resolve().parent))
        self.add_paths(files)

    def choose_output(self):
        d = QFileDialog.getExistingDirectory(
            self, "Choose Output Folder", getattr(self.parent(), "_dialog_directory", lambda: "")()
        )
        if d:
            self.output.setText(d)

    def auto_detect_options(self):
        """Auto-detect available options based on imported file extensions."""
        file_paths = [self.files.item(i).text() for i in range(self.files.count())]
        
        has_media = any(
            Path(p).suffix.lower() in {
                ".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mov", ".mkv", ".avi", ".webm"
            } for p in file_paths
        )
        has_docs = any(
            Path(p).suffix.lower() in {
                ".txt", ".docx", ".pdf", ".html", ".htm", ".md"
            } for p in file_paths
        )

        # Adjust option controls depending on file types found in queue
        self.include_speakers.setEnabled(has_media)
        self.include_times.setEnabled(has_media)
        self.fmt_srt.setEnabled(has_media)
        self.fmt_vtt.setEnabled(has_media)
        self.scope_combo.setEnabled(has_media)


# ============================================================
# Cache Inspection, Purging, & ClearCacheDialog (Extracted to cache_manager.py)
# ============================================================
from cache_manager import (
    format_byte_size,
    cleanup_old_thumbnail_cache,
    get_cache_disk_usage,
    purge_caches,
    ClearCacheDialog,
)



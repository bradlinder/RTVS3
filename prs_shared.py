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

INTERNAL_APP_ID = "RadioTVStorySegmenter"
APP_DISPLAY_NAME = "Radio & TV Segmenter"
PROJECT_VERSION = "3.7.5-beta"
DEFAULT_GITHUB_REPO = "bradlinder/RTVS3"


def make_dialog_maximizable(dialog) -> None:
    """Enforce standard OS window maximize and restore title bar controls for resizable dialogs."""
    try:
        from PySide6.QtCore import Qt
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
    except Exception:
        pass

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
get_app_storage_dir = get_app_data_dir
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
# APP_DISPLAY_NAME, PROJECT_VERSION, and DEFAULT_GITHUB_REPO are defined at the top of prs_shared.py.


# Internal identifiers are intentionally left as "RadioTVStorySegmenter" (the
# original project name) rather than renamed to match APP_DISPLAY_NAME: this
# is the QSettings org/app name and the per-user app-data folder name, and
# changing it would orphan existing beta users' saved preferences and
# downloaded Whisper model cache on upgrade. Only user-facing text changes.
INTERNAL_APP_ID = "RadioTVStorySegmenter"

HELPER_PROTOCOL_VERSION = "1.0"
WAVEFORM_ANALYSIS_RATE = 8000
WAVEFORM_POINTS_PER_SECOND = 200
MIN_WORDS_PER_PARAGRAPH = 35
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
# Find & Replace Dialog (Extracted to transcript_editor.py)
# ============================================================
from transcript_editor import FindReplaceDialog

class ExportDialog(QDialog):
    def __init__(self, parent=None, has_media=True, default_name="export"):
        super().__init__(parent)
        self.has_media = has_media
        self.default_name = default_name
        self.setWindowTitle("Export Options")
        self.setMinimumWidth(380)
        make_dialog_maximizable(self)

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

from core_utils import calculate_fade_curve_factor, calculate_fade_out_factor


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


# FadeCurveVisualSelector (Extracted to story_widgets.py)
from story_widgets import FadeCurveVisualSelector



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

# Story Undo / Redo Commands (Extracted to story_widgets.py)
from story_widgets import (
    StoryFadesChangeCommand,
    SetStoriesCommand,
    StoryBoundaryChangeCommand,
    SelectStoriesCommand,
)


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

# Custom Story Card Delegate (Extracted to story_widgets.py)
from story_widgets import StoryCardDelegate


# ============================================================
# Interactive Transcript View Stylesheet (Extracted to transcript_editor.py)
# ============================================================
from transcript_editor import transcript_text_view_stylesheet

# ============================================================
# Comments Panel & Comment Editor (Extracted to comment_widgets.py)
# ============================================================
from comment_widgets import (
    CommentEditorDialog,
    NoteEditorDialog,
    CommentCardWidget,
    CommentsPanel,
)

# ============================================================
# Interactive Transcript Editor & Selection Bubble (Extracted to transcript_editor.py)
# ============================================================
from transcript_editor import (
    TranscriptSelectionBubble,
    InteractiveTranscriptEdit,
)

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
# Background Workers & Waveform Peak Cache (Extracted to background_workers.py)
# ============================================================
from background_workers import (
    StoryAutoDetectWorker,
    get_waveform_peak_cache_path,
    read_waveform_peak_cache,
    write_waveform_peak_cache,
    invalidate_waveform_peak_cache,
    WaveformWorker,
    VideoThumbnailWorker,
    get_video_thumbnail_cache_dir,
    read_video_thumbnail_cache,
    invalidate_video_thumbnail_cache,
    PEAKS_MAGIC,
    PEAKS_VERSION,
    WAVEFORM_ANALYSIS_RATE,
    WAVEFORM_POINTS_PER_SECOND,
)

# ============================================================
# Batch Processing Dialog (Extracted to batch_dialog.py)
# ============================================================
from batch_dialog import (
    BatchFileListWidget,
    BatchProcessingDialog,
)

# ============================================================
# Story Widgets (Extracted to story_widgets.py)
# ============================================================
from story_widgets import (
    StoryListWidget,
)

# ============================================================
# Timeline & Waveform Widgets (Extracted to timeline_widgets.py)
# ============================================================
from timeline_widgets import (
    TimelineCanvas,
    TimelineOverviewBar,
    TimelineResizeHandle,
    TimelineWidget,
    WaveformEnvelope,
    build_waveform_pyramid,
    StoryFadesChangeCommand,
)

# ============================================================
# Transcript Editor & Selection (Extracted to transcript_editor.py)
# ============================================================
from transcript_editor import (
    InteractiveTranscriptEdit,
    TranscriptSelectionBubble,
    FindReplaceDialog,
    transcript_text_view_stylesheet,
)

# ============================================================
# Comments & Notes Panel (Extracted to comment_widgets.py)
# ============================================================
from comment_widgets import (
    CommentEditorDialog,
    NoteEditorDialog,
    CommentCardWidget,
    CommentsPanel,
)

# ============================================================
# Cache Manager (Extracted to cache_manager.py)
# ============================================================
from cache_manager import (
    ClearCacheDialog,
    cleanup_old_thumbnail_cache,
    format_byte_size,
    get_cache_disk_usage,
    purge_caches,
)


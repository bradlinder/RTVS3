"""YouTube Video Publisher Plugin for Radio & TV Segmenter.

Provides Zero-API Assisted Publishing to YouTube Studio with:
- Automated chapter timestamps formatted directly from story boundaries
- Subtitles / Closed Captions (.srt) generation for YouTube
- Thumbnail extraction / custom image selection
- Metadata clipboard integration & automatic YouTube Studio browser launching
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QWidget,
    QFileDialog,
    QRadioButton,
    QButtonGroup,
)

from prs_shared import (
    INTERNAL_APP_ID,
    PROJECT_VERSION,
    ffmpeg_path,
    format_time,
)
from plugins.base import BasePlugin, PluginManifest


def capture_video_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    ff = ffmpeg_path() or "ffmpeg"
    cmd = [
        ff, "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{max(0.0, timestamp):.3f}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=30, creationflags=flags)
        return res.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0
    except (subprocess.TimeoutExpired, Exception):
        return False


class YouTubeSettingsDialog(QDialog):
    """Preferences dialog for YouTube Publishing (Direct API & Assisted Upload defaults)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.setWindowTitle("YouTube Publishing Preferences")
        self.setMinimumSize(580, 480)
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Info
        header_group = QGroupBox("Publishing Workflow")
        h_layout = QVBoxLayout(header_group)
        title_lbl = QLabel("<b>YouTube Video Publisher (Dual-Mode)</b>")
        info_lbl = QLabel(
            "Radio & TV Segmenter supports both <b>Direct 1-Click API Upload</b> via YouTube Data API v3 "
            "(streams video, custom thumbnail, and captions directly to your channel in the background) and "
            "<b>Zero-API Assisted Upload</b> (packages local assets, copies chapter descriptions, and launches YouTube Studio in your browser)."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        h_layout.addWidget(title_lbl)
        h_layout.addWidget(info_lbl)
        layout.addWidget(header_group)

        # Default Metadata Settings
        meta_group = QGroupBox("Default Video Settings")
        form = QFormLayout(meta_group)
        form.setSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Direct 1-Click API Upload", "api")
        self.mode_combo.addItem("Zero-API Assisted Upload (Browser)", "assisted")
        saved_mode = str(self.settings.value("export_yt_mode", "api"))
        midx = self.mode_combo.findData(saved_mode)
        if midx >= 0:
            self.mode_combo.setCurrentIndex(midx)
        form.addRow("Default Publishing Mode:", self.mode_combo)

        self.category_combo = QComboBox()
        yt_categories = [
            ("News & Politics", "25"),
            ("Entertainment", "24"),
            ("Education", "27"),
            ("People & Blogs", "22"),
            ("Music", "10"),
            ("Film & Animation", "1"),
            ("Science & Technology", "28"),
            ("Howto & Style", "26"),
            ("Travel & Events", "19"),
            ("Sports", "17"),
        ]
        for name, cid in yt_categories:
            self.category_combo.addItem(name, cid)
        saved_cat = str(self.settings.value("export_yt_category", "25"))
        idx = self.category_combo.findData(saved_cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        form.addRow("Default Category:", self.category_combo)

        self.privacy_combo = QComboBox()
        self.privacy_combo.addItem("Unlisted (Recommended)", "unlisted")
        self.privacy_combo.addItem("Public", "public")
        self.privacy_combo.addItem("Private", "private")
        saved_priv = str(self.settings.value("export_yt_privacy", "unlisted"))
        pidx = self.privacy_combo.findData(saved_priv)
        if pidx >= 0:
            self.privacy_combo.setCurrentIndex(pidx)
        form.addRow("Default Privacy:", self.privacy_combo)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("news, broadcast, interview, segment")
        saved_tags = str(self.settings.value("export_yt_tags", "news, broadcast, segment"))
        self.tags_edit.setText(saved_tags)
        form.addRow("Default Tags:", self.tags_edit)

        layout.addWidget(meta_group)

        # Workflow Automation Options
        opts_group = QGroupBox("Workflow Automation Defaults")
        opts_layout = QVBoxLayout(opts_group)
        opts_layout.setSpacing(6)

        self.cb_copy = QCheckBox("Automatically copy Title, Description & Chapters to clipboard")
        self.cb_copy.setChecked(self.settings.value("export_yt_copy_clipboard", True, type=bool))
        opts_layout.addWidget(self.cb_copy)

        self.cb_browser = QCheckBox("Automatically launch YouTube Studio upload page in browser (Assisted mode)")
        self.cb_browser.setChecked(self.settings.value("export_yt_open_browser", True, type=bool))
        opts_layout.addWidget(self.cb_browser)

        self.cb_subtitles = QCheckBox("Automatically generate Closed Captions (.srt) for YouTube")
        self.cb_subtitles.setChecked(self.settings.value("export_yt_subtitles", True, type=bool))
        opts_layout.addWidget(self.cb_subtitles)

        self.cb_folder = QCheckBox("Open export directory in file explorer after packaging (Assisted mode)")
        self.cb_folder.setChecked(self.settings.value("export_yt_open_folder", True, type=bool))
        opts_layout.addWidget(self.cb_folder)

        layout.addWidget(opts_group)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Preferences")
        save_btn.setStyleSheet("font-weight: bold;")
        save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def on_save(self):
        self.settings.setValue("export_yt_mode", self.mode_combo.currentData())
        self.settings.setValue("export_yt_category", self.category_combo.currentData())
        self.settings.setValue("export_yt_privacy", self.privacy_combo.currentData())
        self.settings.setValue("export_yt_tags", self.tags_edit.text().strip())
        self.settings.setValue("export_yt_copy_clipboard", self.cb_copy.isChecked())
        self.settings.setValue("export_yt_open_browser", self.cb_browser.isChecked())
        self.settings.setValue("export_yt_subtitles", self.cb_subtitles.isChecked())
        self.settings.setValue("export_yt_open_folder", self.cb_folder.isChecked())
        self.settings.sync()
        self.accept()


class Plugin(BasePlugin):
    """YouTube Video Publisher plugin hooking into RTVS."""

    def on_load(self) -> bool:
        return True

    def get_export_destinations(self) -> List[Any]:
        from plugins.youtube.export_destination import YouTubeExportDestination
        return [YouTubeExportDestination(self)]

    def get_export_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("Publish to YouTube...", self.open_publish_dialog),
        ]

    def get_preferences_widget(self, parent=None) -> Any:
        box = QGroupBox("YouTube Video Publishing", parent)
        layout = QVBoxLayout(box)
        lbl = QLabel(
            "<b>YouTube Video Publisher (Dual-Mode)</b><br>"
            "Publish broadcast videos with interactive chapter markers, custom video thumbnails, "
            "and closed caption (.srt) tracks directly via <b>YouTube Data API v3</b> or through "
            "the <b>Zero-API Assisted Upload</b> workflow."
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl)

        btn = QPushButton("Configure YouTube Defaults & Credentials...")
        btn.clicked.connect(lambda: YouTubeSettingsDialog(parent or self.app).exec())
        layout.addWidget(btn)
        return box

    def open_publish_dialog(self):
        if hasattr(self.app, "open_unified_export_dialog"):
            self.app.open_unified_export_dialog(initial_dest="youtube")

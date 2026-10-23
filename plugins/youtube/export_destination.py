"""YouTube Export Destination for UnifiedExportDialog with Zero-Auth Manual Publishing.

Supports:
- Local video packaging (or rendering audio broadcasts to MP4)
- Companion thumbnail extraction or custom image packaging
- Subtitles (.srt) generation
- Formatted sidecar metadata (.txt) and clipboard payload (Title, Description with clickable chapters, Speaker credits, Tags)
- One-click YouTube Studio browser launch
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("rtvs.youtube.export")

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    CollapsibleSection,
    ffmpeg_path,
    format_time,
    safe_filename,
    get_active_theme_mode,
)
from plugins.base import ExportDestination
from plugins.youtube.guide_dialog import YouTubeAssistedUploadGuideDialog
from export.subtitles import generate_youtube_chapters, write_subtitles_file

YOUTUBE_CATEGORIES = [
    ("25", "News & Politics"),
    ("24", "Entertainment"),
    ("22", "People & Blogs"),
    ("27", "Education"),
    ("28", "Science & Technology"),
    ("10", "Music"),
    ("17", "Sports"),
    ("23", "Comedy"),
    ("1", "Film & Animation"),
    ("26", "Howto & Style"),
]


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
        res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=30, creationflags=flags)
        return res.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0
    except (subprocess.TimeoutExpired, Exception):
        return False


class YouTubeExportTabWidget(QWidget):
    """Configuration and preview panel for YouTube Zero-Auth Manual Publishing."""

    def __init__(self, parent: QWidget, main_window: Any):
        super().__init__(parent)
        self.main_window = main_window
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._is_video_project = bool(getattr(self.main_window, "current_media_is_video", False))
        self._yt_frame_pos = float(getattr(self.main_window, "current_position", 0.0) or 0.0)
        self._temp_preview_files = set()

        self._yt_scrub_timer = QTimer(self)
        self._yt_scrub_timer.setSingleShot(True)
        self._yt_scrub_timer.setInterval(120)
        self._yt_scrub_timer.timeout.connect(self._on_yt_scrub_timer_timeout)

        self._setup_ui()

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        yt_layout = QVBoxLayout(scroll_content)
        yt_layout.setSpacing(12)

        # Overview banner with Open YouTube Studio button
        yt_theme_mode = get_active_theme_mode("dark")

        yt_banner = QWidget()
        yt_b_layout = QVBoxLayout(yt_banner)
        yt_b_layout.setContentsMargins(12, 10, 12, 10)
        if yt_theme_mode == "light":
            yt_banner.setStyleSheet("background-color: #eaedf0; border-radius: 6px; border: 1px solid #b6bcc4;")
        elif yt_theme_mode == "high_contrast":
            yt_banner.setStyleSheet("background-color: #000000; border-radius: 6px; border: 1px solid #ffffff;")
        else:
            yt_banner.setStyleSheet("background-color: #1e293b; border-radius: 6px; border: 1px solid #334155;")

        mode_header_layout = QHBoxLayout()
        yt_banner_title = QLabel("<b>YouTube Video Publisher (Zero-Auth Manual Package)</b>")
        if yt_theme_mode == "light":
            yt_banner_title.setStyleSheet("color: #b91c1c; font-size: 13px;")
        elif yt_theme_mode == "high_contrast":
            yt_banner_title.setStyleSheet("color: #ff0000; font-size: 13px;")
        else:
            yt_banner_title.setStyleSheet("color: #f87171; font-size: 13px;")
        mode_header_layout.addWidget(yt_banner_title)
        mode_header_layout.addStretch()

        self.open_studio_btn = QPushButton("Open YouTube Studio")
        self.open_studio_btn.setToolTip("Open YouTube Studio upload page in your default web browser.")
        self.open_studio_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; font-size: 11px; padding: 4px 10px; border-radius: 4px;")
        self.open_studio_btn.clicked.connect(lambda: webbrowser.open("https://studio.youtube.com/channel/UC/videos/upload?d=ud"))
        mode_header_layout.addWidget(self.open_studio_btn)

        yt_b_layout.addLayout(mode_header_layout)

        self.yt_banner_info = QLabel(
            "Exports your rendered video (MP4), companion thumbnail image, .srt captions, and sidecar metadata (.txt), "
            "copies Title/Description/Chapters to your clipboard, and opens YouTube Studio in your browser—no login required."
        )
        self.yt_banner_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.yt_banner_info.setWordWrap(True)
        yt_b_layout.addWidget(self.yt_banner_info)

        yt_layout.addWidget(yt_banner)

        # Video Metadata Section
        self.yt_meta_section = CollapsibleSection("Video Details", self, is_expanded=True, subtitle="Title, Category, Privacy, Tags")
        yt_meta_layout = QGridLayout()
        yt_meta_layout.setSpacing(8)

        yt_meta_layout.addWidget(QLabel("Title:"), 0, 0)
        self.yt_title_edit = QLineEdit()
        self.yt_title_edit.setPlaceholderText("Enter YouTube video title...")
        yt_meta_layout.addWidget(self.yt_title_edit, 0, 1, 1, 3)

        yt_meta_layout.addWidget(QLabel("Category:"), 1, 0)
        self.yt_category_combo = QComboBox()
        for cid, cname in YOUTUBE_CATEGORIES:
            self.yt_category_combo.addItem(cname, cid)
        saved_cat = str(self.settings.value("export_yt_category", "25"))
        c_idx = self.yt_category_combo.findData(saved_cat)
        if c_idx >= 0:
            self.yt_category_combo.setCurrentIndex(c_idx)
        yt_meta_layout.addWidget(self.yt_category_combo, 1, 1)

        yt_meta_layout.addWidget(QLabel("Privacy:"), 1, 2)
        self.yt_privacy_combo = QComboBox()
        self.yt_privacy_combo.addItem("Unlisted (Recommended)", "unlisted")
        self.yt_privacy_combo.addItem("Public", "public")
        self.yt_privacy_combo.addItem("Private", "private")
        saved_priv = str(self.settings.value("export_yt_privacy", "unlisted"))
        p_idx = self.yt_privacy_combo.findData(saved_priv)
        if p_idx >= 0:
            self.yt_privacy_combo.setCurrentIndex(p_idx)
        yt_meta_layout.addWidget(self.yt_privacy_combo, 1, 3)

        yt_meta_layout.addWidget(QLabel("Tags:"), 2, 0)
        self.yt_tags_edit = QLineEdit()
        self.yt_tags_edit.setPlaceholderText("Comma-separated tags, e.g. news, broadcast, interview")
        self.yt_tags_edit.setText(str(self.settings.value("export_yt_tags", "news, broadcast, segment")))
        yt_meta_layout.addWidget(self.yt_tags_edit, 2, 1, 1, 3)

        self.yt_meta_section.add_layout(yt_meta_layout)
        yt_layout.addWidget(self.yt_meta_section)

        # Description & Chapter Markers Section
        self.yt_desc_section = CollapsibleSection("Description & Chapters", self, is_expanded=True)
        yt_desc_layout = QVBoxLayout()
        yt_desc_layout.setSpacing(6)

        desc_header_layout = QHBoxLayout()
        desc_tip = QLabel("Chapter timestamps (00:00) will automatically become chapters on YouTube:")
        desc_tip.setStyleSheet("color: #64748b; font-size: 11px;")
        desc_header_layout.addWidget(desc_tip)
        desc_header_layout.addStretch()
        self.yt_regen_chapters_btn = QPushButton("Reset Chapters from Stories")
        self.yt_regen_chapters_btn.setToolTip("Regenerate default description and chapter timestamps from current stories.")
        self.yt_regen_chapters_btn.clicked.connect(self.populate_metadata)
        desc_header_layout.addWidget(self.yt_regen_chapters_btn)
        yt_desc_layout.addLayout(desc_header_layout)

        self.yt_desc_edit = QPlainTextEdit()
        self.yt_desc_edit.setMinimumHeight(130)
        self.yt_desc_edit.setPlaceholderText("Enter video description and chapter timestamps...")
        yt_desc_layout.addWidget(self.yt_desc_edit)

        self.yt_desc_section.add_layout(yt_desc_layout)
        yt_layout.addWidget(self.yt_desc_section)

        # Thumbnail & Extras Section
        self.yt_extras_section = CollapsibleSection("Thumbnail & Extras", self, is_expanded=True, subtitle="Thumbnail, Subtitles (.srt)")
        yt_extras_layout = QVBoxLayout()
        yt_extras_layout.setSpacing(8)

        thumb_subgroup = QWidget()
        thumb_sub_layout = QHBoxLayout(thumb_subgroup)
        thumb_sub_layout.setContentsMargins(0, 0, 0, 0)

        thumb_radio_box = QVBoxLayout()
        self.yt_rad_auto_thumb = QRadioButton("Automatic (YouTube selects frame)")
        self.yt_rad_frame_grab = QRadioButton("Grab frame from video")
        self.yt_rad_file_thumb = QRadioButton("Select custom image file...")

        if not self._is_video_project:
            self.yt_rad_frame_grab.setEnabled(False)
            self.yt_rad_frame_grab.setToolTip("Frame capture requires a loaded video file.")
            self.yt_rad_auto_thumb.setChecked(True)
        else:
            self.yt_rad_frame_grab.setChecked(True)

        self.yt_rad_auto_thumb.toggled.connect(self._on_yt_thumb_mode_changed)
        self.yt_rad_frame_grab.toggled.connect(self._on_yt_thumb_mode_changed)
        self.yt_rad_file_thumb.toggled.connect(self._on_yt_thumb_mode_changed)

        thumb_radio_box.addWidget(self.yt_rad_auto_thumb)
        thumb_radio_box.addWidget(self.yt_rad_frame_grab)
        thumb_radio_box.addWidget(self.yt_rad_file_thumb)
        thumb_sub_layout.addLayout(thumb_radio_box, 1)

        # Thumbnail preview label
        self.yt_thumb_preview_label = QLabel("No Preview")
        self.yt_thumb_preview_label.setFixedSize(160, 90)
        self.yt_thumb_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if yt_theme_mode == "light":
            self.yt_thumb_preview_label.setStyleSheet("background-color: #eaedf0; border: 1px solid #b6bcc4; border-radius: 4px; color: #78808d; font-size: 10px;")
        elif yt_theme_mode == "high_contrast":
            self.yt_thumb_preview_label.setStyleSheet("background-color: #000000; border: 1px solid #ffffff; border-radius: 4px; color: #ffffff; font-size: 10px;")
        else:
            self.yt_thumb_preview_label.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 4px; color: #64748b; font-size: 10px;")
        thumb_sub_layout.addWidget(self.yt_thumb_preview_label)

        yt_extras_layout.addWidget(thumb_subgroup)

        # Frame Scrub Controls
        self.yt_scrub_widget = QWidget()
        scrub_layout = QVBoxLayout(self.yt_scrub_widget)
        scrub_layout.setContentsMargins(0, 0, 0, 0)
        scrub_layout.setSpacing(4)

        slider_row = QHBoxLayout()
        self.yt_scrub_slider = QSlider(Qt.Orientation.Horizontal)
        self.yt_scrub_slider.setRange(0, 10000)
        self.yt_scrub_slider.valueChanged.connect(self._on_yt_slider_value_changed)
        slider_row.addWidget(self.yt_scrub_slider, 1)

        self.yt_scrub_time_label = QLabel(format_time(self._yt_frame_pos, True))
        self.yt_scrub_time_label.setFixedWidth(75)
        self.yt_scrub_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self.yt_scrub_time_label)
        scrub_layout.addLayout(slider_row)

        step_btn_row = QHBoxLayout()
        btn_minus1 = QPushButton("-1s")
        btn_minus1.clicked.connect(lambda: self._on_yt_step(-1.0))
        step_btn_row.addWidget(btn_minus1)

        btn_minus_frame = QPushButton("-1f")
        btn_minus_frame.clicked.connect(lambda: self._on_yt_step(-1.0 / 30.0))
        step_btn_row.addWidget(btn_minus_frame)

        btn_plus_frame = QPushButton("+1f")
        btn_plus_frame.clicked.connect(lambda: self._on_yt_step(1.0 / 30.0))
        step_btn_row.addWidget(btn_plus_frame)

        btn_plus1 = QPushButton("+1s")
        btn_plus1.clicked.connect(lambda: self._on_yt_step(1.0))
        step_btn_row.addWidget(btn_plus1)

        step_btn_row.addStretch()

        btn_sync_ph = QPushButton("Sync to Playhead")
        btn_sync_ph.clicked.connect(self._on_yt_sync_playhead)
        step_btn_row.addWidget(btn_sync_ph)

        scrub_layout.addLayout(step_btn_row)
        yt_extras_layout.addWidget(self.yt_scrub_widget)

        # File browse row
        self.yt_browse_widget = QWidget()
        browse_layout = QHBoxLayout(self.yt_browse_widget)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        self.yt_thumb_path_label = QLabel("No file selected")
        self.yt_thumb_path_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        browse_layout.addWidget(self.yt_thumb_path_label, 1)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_yt_browse_thumb)
        browse_layout.addWidget(btn_browse)
        yt_extras_layout.addWidget(self.yt_browse_widget)

        self._on_yt_thumb_mode_changed()

        # Checkbox extras
        self.yt_cb_subtitles = QCheckBox("Generate Closed Captions (.srt)")
        self.yt_cb_subtitles.setChecked(self.settings.value("export_yt_subtitles", True, type=bool))
        yt_extras_layout.addWidget(self.yt_cb_subtitles)

        self.yt_cb_copy_clipboard = QCheckBox("Copy description & chapters to clipboard")
        self.yt_cb_copy_clipboard.setChecked(self.settings.value("export_yt_copy_clipboard", True, type=bool))
        yt_extras_layout.addWidget(self.yt_cb_copy_clipboard)

        self.yt_cb_open_browser = QCheckBox("Open YouTube Studio in browser after export")
        self.yt_cb_open_browser.setChecked(self.settings.value("export_yt_open_browser", True, type=bool))
        yt_extras_layout.addWidget(self.yt_cb_open_browser)

        self.yt_cb_open_folder = QCheckBox("Open export folder after packaging")
        self.yt_cb_open_folder.setChecked(self.settings.value("export_yt_open_folder", True, type=bool))
        yt_extras_layout.addWidget(self.yt_cb_open_folder)

        self.yt_extras_section.add_layout(yt_extras_layout)
        yt_layout.addWidget(self.yt_extras_section)

        # Bottom stretch
        yt_layout.addStretch()

        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)

        # Initialize content
        self.populate_metadata()

    def _get_yt_bounds(self) -> Tuple[float, float]:
        scope = "full"
        dlg = self.window()
        if hasattr(dlg, "scope_combo"):
            scope = dlg.scope_combo.currentData()
        elif hasattr(self.parent(), "scope_combo"):
            scope = self.parent().scope_combo.currentData()
        stories = getattr(self.main_window, "stories", [])
        if scope == "selected_stories":
            sel_indices = getattr(self.main_window, "current_selected_story_indices", [])
            if sel_indices:
                sel_stories = [stories[i] for i in sel_indices if 0 <= i < len(stories)]
                if sel_stories:
                    return float(min(getattr(s, "start", 0.0) for s in sel_stories)), float(max(getattr(s, "end", 0.0) for s in sel_stories))
        elif scope == "all_stories" and stories:
            return float(min(getattr(s, "start", 0.0) for s in stories)), float(max(getattr(s, "end", 0.0) for s in stories))

        dur = float(getattr(self.main_window, "total_duration", 0.0) or 0.0)
        return 0.0, dur

    def _on_yt_thumb_mode_changed(self):
        is_grab = self.yt_rad_frame_grab.isChecked()
        is_file = self.yt_rad_file_thumb.isChecked()
        self.yt_scrub_widget.setVisible(is_grab)
        self.yt_browse_widget.setVisible(is_file)
        if is_grab:
            self._update_yt_scrub_slider_range()
            self._schedule_yt_frame_preview()
        elif is_file:
            path = self.yt_thumb_path_label.text()
            if path and Path(path).exists():
                pix = QPixmap(path)
                if not pix.isNull():
                    self.yt_thumb_preview_label.setPixmap(pix.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.yt_thumb_preview_label.setText("No Image")
        else:
            self.yt_thumb_preview_label.setText("Auto Thumbnail")

    def _update_yt_scrub_slider_range(self):
        s_min, s_max = self._get_yt_bounds()
        span = max(0.001, s_max - s_min)
        pos = max(s_min, min(s_max, self._yt_frame_pos))
        frac = (pos - s_min) / span
        val = int(round(frac * 10000))
        self.yt_scrub_slider.blockSignals(True)
        self.yt_scrub_slider.setValue(val)
        self.yt_scrub_slider.blockSignals(False)
        self.yt_scrub_time_label.setText(format_time(pos, True))

    def _on_yt_slider_value_changed(self, value):
        s_min, s_max = self._get_yt_bounds()
        span = s_max - s_min
        pos = s_min + (value / 10000.0) * span
        self._yt_frame_pos = pos
        self.yt_scrub_time_label.setText(format_time(pos, True))
        self._schedule_yt_frame_preview()

    def _on_yt_step(self, delta_sec):
        s_min, s_max = self._get_yt_bounds()
        new_pos = max(s_min, min(s_max, self._yt_frame_pos + delta_sec))
        self._yt_frame_pos = new_pos
        self._update_yt_scrub_slider_range()
        self._schedule_yt_frame_preview()

    def _on_yt_sync_playhead(self):
        ph = float(getattr(self.main_window, "current_position", 0.0) or 0.0)
        s_min, s_max = self._get_yt_bounds()
        self._yt_frame_pos = max(s_min, min(s_max, ph))
        self._update_yt_scrub_slider_range()
        self._schedule_yt_frame_preview()

    def _schedule_yt_frame_preview(self):
        if not self._is_video_project or not self.yt_rad_frame_grab.isChecked():
            return
        self._yt_scrub_timer.start()

    def _on_yt_scrub_timer_timeout(self):
        if not self._is_video_project or not self.yt_rad_frame_grab.isChecked():
            return
        video_path = getattr(self.main_window, "current_media_path", None)
        if not video_path or not Path(video_path).exists():
            return
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        self._temp_preview_files.add(tmp.name)
        ok = capture_video_frame(str(video_path), self._yt_frame_pos, tmp.name)
        if ok and Path(tmp.name).exists():
            pix = QPixmap(tmp.name)
            if not pix.isNull():
                self.yt_thumb_preview_label.setPixmap(pix.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _on_yt_browse_thumb(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Thumbnail Image",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            self.yt_thumb_path_label.setText(path)
            pix = QPixmap(path)
            if not pix.isNull():
                self.yt_thumb_preview_label.setPixmap(pix.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _cleanup_temp_files(self) -> None:
        """Purge temporary thumbnail frame grabs."""
        if hasattr(self, "_temp_preview_files") and self._temp_preview_files:
            for temp_f in list(self._temp_preview_files):
                try:
                    if temp_f and Path(temp_f).exists():
                        Path(temp_f).unlink(missing_ok=True)
                except Exception as exc:
                    logger.debug(f"Failed to remove temp file {temp_f}: {exc}")
            self._temp_preview_files.clear()

    def closeEvent(self, event: Any) -> None:
        """Clean up temporary thumbnail files on closure."""
        self._cleanup_temp_files()
        super().closeEvent(event)

    def reject(self) -> None:
        """Ensure temp preview files are purged on dialog rejection."""
        self._cleanup_temp_files()
        super().reject()

    def done(self, r: int) -> None:
        """Ensure temp preview files are purged on dialog completion."""
        self._cleanup_temp_files()
        super().done(r)

    def populate_metadata(self):
        """Builds default title, description, chapter timestamps, and speaker credits from current stories."""
        proj_title = ""
        if getattr(self.main_window, "project_file", None):
            proj_title = Path(self.main_window.project_file).stem
        elif getattr(self.main_window, "audio_file", None):
            proj_title = Path(self.main_window.audio_file).stem
        else:
            proj_title = "Broadcast Segment"

        if not self.yt_title_edit.text().strip():
            self.yt_title_edit.setText(proj_title)

        stories = getattr(self.main_window, "stories", [])
        desc_lines = [
            f"{proj_title}",
            "",
            "Chapters:",
        ]
        chapters = generate_youtube_chapters(stories, ensure_zero_start=True)
        if chapters.strip():
            desc_lines.append(chapters.strip())
        else:
            desc_lines.append("00:00 - Full Broadcast")

        # Extract unique speaker credits from transcript segments if available
        speakers: List[str] = []
        transcript = getattr(self.main_window, "transcript", None)
        segments = transcript.get("segments", []) if isinstance(transcript, dict) else getattr(self.main_window, "transcript_segments", [])
        if segments:
            seen_spk = set()
            for seg in segments:
                spk = (seg.get("speaker") if isinstance(seg, dict) else getattr(seg, "speaker", "")) or ""
                spk = str(spk).strip()
                if spk and spk.lower() not in ("unknown", "none") and spk not in seen_spk:
                    seen_spk.add(spk)
                    speakers.append(spk)
        if speakers:
            desc_lines.append("")
            desc_lines.append(f"Speakers: {', '.join(speakers)}")

        self.yt_desc_edit.setPlainText("\n".join(desc_lines))
        if self.yt_rad_frame_grab.isChecked() and self._is_video_project:
            self._update_yt_scrub_slider_range()
            self._schedule_yt_frame_preview()


class YouTubeExportDestination(ExportDestination):
    """Export destination handler for YouTube Zero-Auth Manual Publishing."""

    def __init__(self, plugin: Any = None):
        super().__init__(
            id="youtube",
            title="YouTube Video Publisher",
            description="Zero-auth manual publishing package for YouTube Studio with MP4 video, thumbnail, chapters, and .srt subtitles.",
            icon="youtube",
        )
        self.plugin = plugin
        self.tab_widget: Optional[YouTubeExportTabWidget] = None

    def create_widget(self, parent: Any, main_window: Any) -> Any:
        self.tab_widget = YouTubeExportTabWidget(parent, main_window)
        return self.tab_widget

    def on_scope_changed(self, scope: str, stories: list) -> None:
        if self.tab_widget:
            self.tab_widget.populate_metadata()

    def validate(self) -> Tuple[bool, str]:
        if not self.tab_widget:
            return False, "YouTube tab not initialized."
        title = self.tab_widget.yt_title_edit.text().strip()
        if not title:
            return False, "Please enter a YouTube video title."
        return True, ""

    def get_export_data(self) -> Dict[str, Any]:
        if not self.tab_widget:
            return {}
        w = self.tab_widget
        thumb_mode = "none"
        thumb_file = None
        if w.yt_rad_frame_grab.isChecked():
            thumb_mode = "frame"
        elif w.yt_rad_file_thumb.isChecked():
            thumb_mode = "file"
            thumb_file = w.yt_thumb_path_label.text().strip()

        return {
            "mode": "assisted",
            "title": w.yt_title_edit.text().strip(),
            "category": w.yt_category_combo.currentData(),
            "privacy": w.yt_privacy_combo.currentData(),
            "tags": w.yt_tags_edit.text().strip(),
            "description": w.yt_desc_edit.toPlainText().strip(),
            "thumb_mode": thumb_mode,
            "thumb_file": thumb_file,
            "thumb_frame_pos": w._yt_frame_pos,
            "copy_clipboard": w.yt_cb_copy_clipboard.isChecked(),
            "open_browser": w.yt_cb_open_browser.isChecked(),
            "open_folder": w.yt_cb_open_folder.isChecked(),
            "subtitles": w.yt_cb_subtitles.isChecked(),
            "include_subtitles": w.yt_cb_subtitles.isChecked(),
        }

    def execute_export(self, main_window: Any, export_data: Dict[str, Any], progress_dialog: Any = None) -> bool:
        if hasattr(main_window, "_handle_youtube_export_result"):
            main_window._handle_youtube_export_result(export_data)
            return True
        return False

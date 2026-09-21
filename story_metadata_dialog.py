"""Radio & TV Story Segmenter — Universal Story & Post Metadata Architecture.

Provides a unified, multi-pane modal dialog (StoryMetadataDialog) and tabbed editor
for configuring episode and story metadata (titles, authors, categories/tags,
excerpts, video frame thumbnails, publishing status, and editorial notes).

Features:
- Offline-first: works 100% natively without any external plugins or networks.
- Plugin Enrichment: seamlessly detects WordPress (and CMS plugins) to load
  live author rosters (including Co-Authors Plus guest authors) and hierarchical
  categories.
- Rich Video Frame Grabber: interactive position scrubber, step controls, and live
  thumbnail preview powered by FFmpeg.
- Instant Two-Way Synchronization: writes directly to Story.title, Story.metadata,
  and project_metadata, immediately updating the main window sidebar inputs and
  StoryListWidget while auto-saving to the .rtvs project.
"""

from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core_utils import ffmpeg_path, format_time, parse_time, INTERNAL_APP_ID


def generate_story_excerpt(text: str, max_words: int = 55) -> str:
    """Generate a clean, readable excerpt of up to max_words from transcript text."""
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return " ".join(words)
    trimmed = " ".join(words[:max_words])
    # Avoid trailing punctuation before ellipsis
    while trimmed and trimmed[-1] in ",;:-\"'":
        trimmed = trimmed[:-1]
    return trimmed + "…"


class StoryMetadataDialog(QDialog):
    """Universal modal dialog for inspecting and editing post and story metadata across the project."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        main_window: Any = None,
        target_story_index: Optional[int] = None,
    ):
        super().__init__(parent)
        self.main_window = main_window or parent
        self.target_story_index = target_story_index
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

        self.setWindowTitle("Story & Post Metadata Editor")
        self.resize(960, 720)
        self.setMinimumSize(780, 560)
        self.setObjectName("story_metadata_dialog")

        # Media & state flags
        self._is_video_project = bool(getattr(self.main_window, "current_media_is_video", False))
        self._temp_preview_files: Set[str] = set()
        self._syncing_editor = False
        self._current_target_index = 0
        self.target_items: List[Dict[str, Any]] = []

        # Cached taxonomy
        self._cached_authors: List[Dict[str, Any]] = []
        self._cached_categories: List[Dict[str, Any]] = []

        # Scrub timer for video frame grabs
        self._scrub_timer = QTimer(self)
        self._scrub_timer.setSingleShot(True)
        self._scrub_timer.timeout.connect(self._on_scrub_timer_timeout)

        self._init_ui()
        self._load_taxonomies()
        self.rebuild_target_items()

        # Focus initial story if provided
        if self.target_story_index is not None:
            # 0 is Full Episode, 1..N are stories
            item_row = self.target_story_index + 1
            if 0 <= item_row < self.targets_list.count():
                self.targets_list.setCurrentRow(item_row)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Dialog header description
        header_widget = QWidget(self)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        info_label = QLabel(
            "<b>Story & Post Metadata</b> — Configure titles, authors, categories/tags, "
            "excerpts, and featured images for full episodes and individual stories.",
            self
        )
        info_label.setWordWrap(True)
        header_layout.addWidget(info_label, 1)

        # Taxonomy Refresh Button (if WP or CMS available)
        self.refresh_tax_btn = QPushButton("🔄 Refresh WP Taxonomies", self)
        self.refresh_tax_btn.setToolTip("Fetch latest Authors and Categories from WordPress REST API")
        self.refresh_tax_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.refresh_tax_btn.clicked.connect(self._on_refresh_taxonomy_clicked)
        header_layout.addWidget(self.refresh_tax_btn)

        main_layout.addWidget(header_widget)

        # Splitter: Left is Target Stories list, Right is Editor Pane
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(6)

        # Left: Targets List
        left_panel = QWidget(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        left_hdr = QLabel("<b>Episodes & Stories</b>", left_panel)
        left_layout.addWidget(left_hdr)

        self.targets_list = QListWidget(left_panel)
        self.targets_list.setObjectName("story_metadata_targets_list")
        self.targets_list.setMinimumWidth(220)
        self.targets_list.setMaximumWidth(320)
        self.targets_list.currentRowChanged.connect(self._on_target_selection_changed)
        left_layout.addWidget(self.targets_list, 1)

        splitter.addWidget(left_panel)

        # Right: Target Editor
        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(10)

        # Target Header
        self.target_header_label = QLabel("<b>Editing: Full Episode</b>", right_panel)
        self.target_header_label.setStyleSheet("font-size: 14px; color: #38bdf8; padding-bottom: 2px;")
        right_layout.addWidget(self.target_header_label)

        # Scroll Area for Form
        scroll_area = QScrollArea(right_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(0, 0, 8, 0)
        form_layout.setSpacing(12)

        # 1. Title Row
        title_group = QGroupBox("Story / Post Title", scroll_content)
        title_box_layout = QVBoxLayout(title_group)
        title_box_layout.setContentsMargins(10, 8, 10, 8)
        self.title_input = QLineEdit(title_group)
        self.title_input.setPlaceholderText("Enter display title...")
        self.title_input.textChanged.connect(self._on_title_text_changed)
        title_box_layout.addWidget(self.title_input)
        form_layout.addWidget(title_group)

        # 2. Multi-Pane: Authors & Categories
        tax_row = QHBoxLayout()
        tax_row.setSpacing(10)

        # Authors Column
        authors_group = QGroupBox("Authors & Contributors", scroll_content)
        authors_layout = QVBoxLayout(authors_group)
        authors_layout.setContentsMargins(10, 8, 10, 8)
        authors_layout.setSpacing(6)

        # Filter
        self.authors_filter = QLineEdit(authors_group)
        self.authors_filter.setPlaceholderText("🔍 Filter authors...")
        self.authors_filter.textChanged.connect(self._filter_authors)
        authors_layout.addWidget(self.authors_filter)

        # Authors Checklist
        self.authors_list = QListWidget(authors_group)
        self.authors_list.setMinimumHeight(130)
        self.authors_list.setMaximumHeight(180)
        self.authors_list.itemChanged.connect(self._on_author_item_changed)
        authors_layout.addWidget(self.authors_list)

        # Freeform Author Name
        manual_auth_layout = QHBoxLayout()
        manual_auth_lbl = QLabel("Manual:", authors_group)
        self.manual_author_input = QLineEdit(authors_group)
        self.manual_author_input.setPlaceholderText("Author name (if not in list)")
        self.manual_author_input.textChanged.connect(self._on_manual_author_changed)
        manual_auth_layout.addWidget(manual_auth_lbl)
        manual_auth_layout.addWidget(self.manual_author_input)
        authors_layout.addLayout(manual_auth_layout)

        tax_row.addWidget(authors_group, 1)

        # Categories & Tags Column
        cats_group = QGroupBox("Categories & Tags", scroll_content)
        cats_layout = QVBoxLayout(cats_group)
        cats_layout.setContentsMargins(10, 8, 10, 8)
        cats_layout.setSpacing(6)

        # Filter
        self.cats_filter = QLineEdit(cats_group)
        self.cats_filter.setPlaceholderText("🔍 Filter categories...")
        self.cats_filter.textChanged.connect(self._filter_categories)
        cats_layout.addWidget(self.cats_filter)

        # Categories Checklist
        self.cats_list = QListWidget(cats_group)
        self.cats_list.setMinimumHeight(130)
        self.cats_list.setMaximumHeight(180)
        self.cats_list.itemChanged.connect(self._on_category_item_changed)
        cats_layout.addWidget(self.cats_list)

        # Tags / Keywords Input
        tags_layout = QHBoxLayout()
        tags_lbl = QLabel("Tags:", cats_group)
        self.tags_input = QLineEdit(cats_group)
        self.tags_input.setPlaceholderText("Comma-separated tags (e.g. news, interview)")
        self.tags_input.textChanged.connect(self._on_tags_changed)
        tags_layout.addWidget(tags_lbl)
        tags_layout.addWidget(self.tags_input)
        cats_layout.addLayout(tags_layout)

        tax_row.addWidget(cats_group, 1)
        form_layout.addLayout(tax_row)

        # 3. Excerpt Section
        excerpt_group = QGroupBox("Excerpt & Summary", scroll_content)
        excerpt_layout = QVBoxLayout(excerpt_group)
        excerpt_layout.setContentsMargins(10, 8, 10, 8)
        excerpt_layout.setSpacing(6)

        exc_btn_row = QHBoxLayout()
        exc_btn_row.addWidget(QLabel("Short summary for web/feeds:", excerpt_group))
        exc_btn_row.addStretch()

        self.auto_excerpt_btn = QPushButton("✨ Auto-Generate Excerpt (55 Words)", excerpt_group)
        self.auto_excerpt_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.auto_excerpt_btn.clicked.connect(self._on_auto_generate_excerpt)
        exc_btn_row.addWidget(self.auto_excerpt_btn)
        excerpt_layout.addLayout(exc_btn_row)

        self.excerpt_edit = QTextEdit(excerpt_group)
        self.excerpt_edit.setPlaceholderText("Story excerpt / summary for publishing...")
        self.excerpt_edit.setMaximumHeight(80)
        self.excerpt_edit.textChanged.connect(self._on_excerpt_text_changed)
        excerpt_layout.addWidget(self.excerpt_edit)
        form_layout.addWidget(excerpt_group)

        # 4. Featured Image / Video Thumbnail
        thumb_group = QGroupBox("Featured Image & Thumbnail", scroll_content)
        thumb_layout = QVBoxLayout(thumb_group)
        thumb_layout.setContentsMargins(10, 8, 10, 8)
        thumb_layout.setSpacing(8)

        radio_row = QHBoxLayout()
        self.thumb_button_group = QButtonGroup(self)

        self.rad_thumb_none = QRadioButton("No Image", thumb_group)
        self.rad_thumb_grab = QRadioButton("Grab Frame from Video", thumb_group)
        self.rad_thumb_file = QRadioButton("Select Custom Image File", thumb_group)

        self.thumb_button_group.addButton(self.rad_thumb_none)
        self.thumb_button_group.addButton(self.rad_thumb_grab)
        self.thumb_button_group.addButton(self.rad_thumb_file)

        self.rad_thumb_grab.setEnabled(self._is_video_project)
        if not self._is_video_project:
            self.rad_thumb_grab.setToolTip("Video frame grabbing requires a loaded video file.")

        self.rad_thumb_none.toggled.connect(self._on_thumb_mode_changed)
        self.rad_thumb_grab.toggled.connect(self._on_thumb_mode_changed)
        self.rad_thumb_file.toggled.connect(self._on_thumb_mode_changed)

        radio_row.addWidget(self.rad_thumb_none)
        radio_row.addWidget(self.rad_thumb_grab)
        radio_row.addWidget(self.rad_thumb_file)
        radio_row.addStretch()
        thumb_layout.addLayout(radio_row)

        # Interactive Scrubber / Preview area
        thumb_content_row = QHBoxLayout()
        thumb_content_row.setSpacing(12)

        # Preview Thumbnail Box
        self.thumb_preview_label = QLabel(thumb_group)
        self.thumb_preview_label.setFixedSize(160, 90)
        self.thumb_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_preview_label.setStyleSheet("""
            QLabel {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                color: #64748b;
                font-size: 11px;
            }
        """)
        self.thumb_preview_label.setText("No Thumbnail")
        thumb_content_row.addWidget(self.thumb_preview_label)

        # Controls Container
        self.thumb_controls_stack = QWidget(thumb_group)
        controls_layout = QVBoxLayout(self.thumb_controls_stack)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        # Video Frame Scrub Controls
        self.video_scrub_widget = QWidget(self.thumb_controls_stack)
        scrub_layout = QVBoxLayout(self.video_scrub_widget)
        scrub_layout.setContentsMargins(0, 0, 0, 0)
        scrub_layout.setSpacing(4)

        slider_row = QHBoxLayout()
        self.frame_slider = QSlider(Qt.Orientation.Horizontal, self.video_scrub_widget)
        self.frame_slider.setRange(0, 10000)
        self.frame_slider.valueChanged.connect(self._on_slider_value_changed)
        slider_row.addWidget(self.frame_slider, 1)

        self.frame_time_label = QLabel("00:00:00.000", self.video_scrub_widget)
        self.frame_time_label.setStyleSheet("font-family: monospace; font-size: 11px; font-weight: bold;")
        slider_row.addWidget(self.frame_time_label)
        scrub_layout.addLayout(slider_row)

        stepper_row = QHBoxLayout()
        stepper_row.setSpacing(4)

        btn_m1s = QPushButton("-1.0s", self.video_scrub_widget)
        btn_m1s.clicked.connect(lambda: self._on_step_frame(-1.0))
        stepper_row.addWidget(btn_m1s)

        btn_m100 = QPushButton("-0.1s", self.video_scrub_widget)
        btn_m100.clicked.connect(lambda: self._on_step_frame(-0.1))
        stepper_row.addWidget(btn_m100)

        btn_p100 = QPushButton("+0.1s", self.video_scrub_widget)
        btn_p100.clicked.connect(lambda: self._on_step_frame(0.1))
        stepper_row.addWidget(btn_p100)

        btn_p1s = QPushButton("+1.0s", self.video_scrub_widget)
        btn_p1s.clicked.connect(lambda: self._on_step_frame(1.0))
        stepper_row.addWidget(btn_p1s)

        btn_sync = QPushButton("📍 Sync to Playhead", self.video_scrub_widget)
        btn_sync.setToolTip("Set frame capture time to current main window player position")
        btn_sync.clicked.connect(self._on_sync_playhead_clicked)
        stepper_row.addWidget(btn_sync)
        stepper_row.addStretch()

        scrub_layout.addLayout(stepper_row)
        controls_layout.addWidget(self.video_scrub_widget)

        # File Browse Controls
        self.file_browse_widget = QWidget(self.thumb_controls_stack)
        file_layout = QHBoxLayout(self.file_browse_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)

        self.image_path_label = QLabel("No image selected", self.file_browse_widget)
        self.image_path_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        file_layout.addWidget(self.image_path_label, 1)

        self.browse_image_btn = QPushButton("Browse Image...", self.file_browse_widget)
        self.browse_image_btn.clicked.connect(self._on_browse_image)
        file_layout.addWidget(self.browse_image_btn)

        controls_layout.addWidget(self.file_browse_widget)
        thumb_content_row.addWidget(self.thumb_controls_stack, 1)

        thumb_layout.addLayout(thumb_content_row)
        form_layout.addWidget(thumb_group)

        # 5. Editorial & Publishing Details
        pub_group = QGroupBox("Editorial & Publishing Options", scroll_content)
        pub_form = QFormLayout(pub_group)
        pub_form.setContentsMargins(10, 8, 10, 8)
        pub_form.setSpacing(6)

        self.status_combo = QComboBox(pub_group)
        self.status_combo.addItem("Draft", "draft")
        self.status_combo.addItem("Published", "publish")
        self.status_combo.addItem("Pending Review", "pending")
        self.status_combo.addItem("Private", "private")
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)
        pub_form.addRow("Status:", self.status_combo)

        self.slug_input = QLineEdit(pub_group)
        self.slug_input.setPlaceholderText("custom-url-slug")
        self.slug_input.textChanged.connect(self._on_slug_changed)
        pub_form.addRow("Slug:", self.slug_input)

        self.notes_edit = QLineEdit(pub_group)
        self.notes_edit.setPlaceholderText("Internal editorial notes or comments...")
        self.notes_edit.textChanged.connect(self._on_notes_changed)
        pub_form.addRow("Notes:", self.notes_edit)

        form_layout.addWidget(pub_group)

        scroll_area.setWidget(scroll_content)
        right_layout.addWidget(scroll_area, 1)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter, 1)

        # Bottom Button Bar
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.apply_btn = QPushButton("Apply", self)
        self.apply_btn.setToolTip("Save all metadata changes to project without closing")
        self.apply_btn.clicked.connect(self.save_all_to_project)
        btn_box.addWidget(self.apply_btn)

        btn_box.addStretch()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.cancel_btn)

        self.save_close_btn = QPushButton("Save & Close", self)
        self.save_close_btn.setDefault(True)
        self.save_close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.save_close_btn.clicked.connect(self._on_save_and_close)
        btn_box.addWidget(self.save_close_btn)

        main_layout.addLayout(btn_box)

    def _load_taxonomies(self, force_remote: bool = False):
        """Load cached WordPress taxonomies or attempt remote fetch if active."""
        authors = []
        categories = []

        if not force_remote:
            raw_auth = self.settings.value("wp_cached_authors", "")
            raw_cat = self.settings.value("wp_cached_categories", "")
            if raw_auth:
                try:
                    authors = json.loads(raw_auth)
                except Exception:
                    pass
            if raw_cat:
                try:
                    categories = json.loads(raw_cat)
                except Exception:
                    pass

        if force_remote or (not authors and not categories):
            try:
                from plugins.wordpress.client import get_wp_client
                client = get_wp_client()
                if client and client.is_configured():
                    authors = client.get_authors() if hasattr(client, "get_authors") else []
                    categories = client.get_categories() if hasattr(client, "get_categories") else []
                    self.settings.setValue("wp_cached_authors", json.dumps(authors))
                    self.settings.setValue("wp_cached_categories", json.dumps(categories))
            except Exception as exc:
                if force_remote:
                    QMessageBox.warning(self, "Taxonomy Fetch Error", f"Could not fetch WordPress taxonomies: {exc}")

        self._cached_authors = authors or []
        self._cached_categories = categories or []

        self._populate_authors_list()
        self._populate_categories_list()

    def _populate_authors_list(self):
        self.authors_list.blockSignals(True)
        self.authors_list.clear()

        filter_text = self.authors_filter.text().strip().lower()
        for author in self._cached_authors:
            if not isinstance(author, dict):
                continue
            name = author.get("name", "Unknown Author")
            slug = author.get("slug", "")
            slug_str = f" (@{slug})" if slug else ""
            auth_type = author.get("type", "Guest" if author.get("is_guest") else "WP User")
            display_text = f"{name}{slug_str} [{auth_type}]"

            if filter_text and filter_text not in display_text.lower():
                continue

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, author)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.authors_list.addItem(item)

        self.authors_list.blockSignals(False)

    def _populate_categories_list(self):
        self.cats_list.blockSignals(True)
        self.cats_list.clear()

        filter_text = self.cats_filter.text().strip().lower()
        for cat in self._cached_categories:
            if not isinstance(cat, dict):
                continue
            name = cat.get("name", "Unnamed Category")
            if filter_text and filter_text not in name.lower():
                continue
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, cat.get("id"))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.cats_list.addItem(item)

        self.cats_list.blockSignals(False)

    def _filter_authors(self, _):
        checked_auth_ids, checked_term_ids = self._get_checked_authors_from_ui()
        self._populate_authors_list()
        self._set_checked_authors_in_ui(checked_auth_ids, checked_term_ids)

    def _filter_categories(self, _):
        checked_cat_ids = self._get_checked_categories_from_ui()
        self._populate_categories_list()
        self._set_checked_categories_in_ui(checked_cat_ids)

    def _on_refresh_taxonomy_clicked(self):
        self._load_taxonomies(force_remote=True)
        if 0 <= self._current_target_index < len(self.target_items):
            self._load_target_into_ui(self._current_target_index)
        QMessageBox.information(
            self,
            "Taxonomies Refreshed",
            f"Loaded {len(self._cached_authors)} authors and {len(self._cached_categories)} categories."
        )

    def rebuild_target_items(self):
        """Construct the list of editable targets: Full Episode (0) followed by each Story."""
        items: List[Dict[str, Any]] = []

        audio_file = getattr(self.main_window, "audio_file", None)
        base_name = Path(audio_file).stem if audio_file else "Full Episode"
        stories = getattr(self.main_window, "stories", []) or []

        # 1. Full Episode Target
        proj_meta = getattr(self.main_window, "project_metadata", {}) or {}
        if not isinstance(proj_meta, dict):
            proj_meta = {}
            self.main_window.project_metadata = proj_meta
        wp_proj = proj_meta.get("wordpress", {}) if isinstance(proj_meta.get("wordpress"), dict) else {}

        raw_full_text = self.main_window._get_transcript_text_slice(0.0, None) if hasattr(self.main_window, "_get_transcript_text_slice") else ""
        default_full_excerpt = generate_story_excerpt(raw_full_text, 55)

        full_item = {
            "type": "full",
            "index": -1,
            "task_label": "🎬 Full Episode",
            "title": proj_meta.get("title") or wp_proj.get("title") or base_name,
            "author": proj_meta.get("author", "") or wp_proj.get("manual_author", ""),
            "author_ids": list(wp_proj.get("author_ids") or []),
            "author_term_ids": list(wp_proj.get("author_term_ids") or []),
            "category_ids": list(wp_proj.get("category_ids") or []),
            "tags": list(proj_meta.get("tags") or wp_proj.get("tags") or []),
            "excerpt": proj_meta.get("excerpt") or wp_proj.get("excerpt") or default_full_excerpt,
            "featured_image": proj_meta.get("featured_image") or wp_proj.get("featured_image"),
            "featured_image_mode": proj_meta.get("featured_image_mode") or wp_proj.get("featured_image_mode", "none"),
            "frame_pos": float(wp_proj.get("frame_pos") if wp_proj.get("frame_pos") is not None else (getattr(self.main_window, "current_position", 0.0) or 0.0)),
            "status": wp_proj.get("status", "draft"),
            "slug": wp_proj.get("slug", ""),
            "notes": proj_meta.get("notes", ""),
            "start": None,
            "end": None,
        }
        items.append(full_item)

        # 2. Individual Story Targets
        for idx, story in enumerate(stories):
            meta = getattr(story, "metadata", {}) or {}
            if not isinstance(meta, dict):
                meta = {}
                story.metadata = meta
            wp_meta = meta.get("wordpress", {}) if isinstance(meta.get("wordpress"), dict) else {}

            raw_st_text = self.main_window._get_transcript_text_slice(story.start, story.end) if hasattr(self.main_window, "_get_transcript_text_slice") else ""
            default_st_excerpt = generate_story_excerpt(raw_st_text, 55)

            st_item = {
                "type": "story",
                "index": idx,
                "story_ref": story,
                "task_label": f"📖 Story #{idx + 1}",
                "title": story.title or wp_meta.get("title") or f"Story #{idx + 1}",
                "author": meta.get("author", "") or wp_meta.get("manual_author", ""),
                "author_ids": list(wp_meta.get("author_ids") or []),
                "author_term_ids": list(wp_meta.get("author_term_ids") or []),
                "category_ids": list(wp_meta.get("category_ids") or []),
                "tags": list(meta.get("tags") or wp_meta.get("tags") or []),
                "excerpt": meta.get("excerpt") or wp_meta.get("excerpt") or default_st_excerpt,
                "featured_image": meta.get("featured_image") or wp_meta.get("featured_image"),
                "featured_image_mode": meta.get("featured_image_mode") or wp_meta.get("featured_image_mode", "none"),
                "frame_pos": float(wp_meta.get("frame_pos") if wp_meta.get("frame_pos") is not None else story.start),
                "status": wp_meta.get("status", "draft"),
                "slug": wp_meta.get("slug", ""),
                "notes": meta.get("notes", ""),
                "start": story.start,
                "end": story.end,
            }
            items.append(st_item)

        self.target_items = items
        self._current_target_index = 0

        self.targets_list.blockSignals(True)
        self.targets_list.clear()
        for idx, target in enumerate(self.target_items):
            self.targets_list.addItem("")
            self._update_target_list_item_display(idx)
        self.targets_list.blockSignals(False)

        if self.targets_list.count() > 0:
            self.targets_list.setCurrentRow(0)
            self._load_target_into_ui(0)

    def _update_target_list_item_display(self, idx: int):
        if not (0 <= idx < len(self.target_items)) or idx >= self.targets_list.count():
            return
        target = self.target_items[idx]
        title = target.get("title") or target.get("task_label", f"Target {idx + 1}")
        sub = []
        if target.get("author"):
            sub.append(target["author"])
        elif target.get("author_ids") or target.get("author_term_ids"):
            n_auth = len(target.get("author_ids", [])) + len(target.get("author_term_ids", []))
            sub.append(f"{n_auth} author(s)")
        if target.get("category_ids"):
            sub.append(f"{len(target['category_ids'])} cat(s)")
        sub_str = f" [{', '.join(sub)}]" if sub else ""

        self.targets_list.item(idx).setText(f"{target.get('task_label', '')}: {title}{sub_str}")

    def _on_target_selection_changed(self, row: int):
        if row < 0 or row >= len(self.target_items):
            return
        self._load_target_into_ui(row)

    def _load_target_into_ui(self, index: int):
        if not (0 <= index < len(self.target_items)):
            return
        self._current_target_index = index
        target = self.target_items[index]

        self._syncing_editor = True

        # Header Text
        if target.get("type") == "full":
            dur = max(0.0, float(getattr(self.main_window, "duration", 0.0) or 0.0))
            self.target_header_label.setText(
                f"<b>Full Episode Metadata</b>  <span style='color: #8b949e; font-size: 11px;'>({format_time(dur, include_millis=False)})</span>"
            )
        else:
            s_idx = target.get("index", 0)
            st = target.get("start", 0.0) or 0.0
            et = target.get("end", 0.0) or 0.0
            dur = max(0.0, et - st)
            self.target_header_label.setText(
                f"<b>Story #{s_idx + 1} Metadata</b>  <span style='color: #8b949e; font-size: 11px;'>({format_time(st, include_millis=False)} – {format_time(et, include_millis=False)} • {dur:.1f}s)</span>"
            )

        # Title
        self.title_input.setText(target.get("title", ""))

        # Excerpt
        self.excerpt_edit.setPlainText(target.get("excerpt", ""))

        # Manual Author & Tags
        self.manual_author_input.setText(target.get("author", ""))
        self.tags_input.setText(", ".join(target.get("tags", [])))

        # Status & Slug & Notes
        status = target.get("status", "draft")
        s_idx = self.status_combo.findData(status)
        if s_idx >= 0:
            self.status_combo.setCurrentIndex(s_idx)
        self.slug_input.setText(target.get("slug", ""))
        self.notes_edit.setText(target.get("notes", ""))

        # Featured Image & Scrubber
        mode = target.get("featured_image_mode", "none")
        img = target.get("featured_image")
        frame_pos = target.get("frame_pos")
        if frame_pos is None:
            t_min, _ = self._get_target_bounds(index)
            frame_pos = t_min
            target["frame_pos"] = frame_pos

        if mode == "grab" and self._is_video_project:
            self.rad_thumb_grab.setChecked(True)
            self.video_scrub_widget.setVisible(True)
            self.file_browse_widget.setVisible(False)
            self._sync_slider_to_pos(frame_pos)
            if img and Path(img).exists():
                pix = QPixmap(str(img)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.thumb_preview_label.setPixmap(pix)
            else:
                self.thumb_preview_label.clear()
                self.thumb_preview_label.setText("Video Frame")
        elif mode == "file" and img:
            self.rad_thumb_file.setChecked(True)
            self.video_scrub_widget.setVisible(False)
            self.file_browse_widget.setVisible(True)
            self.image_path_label.setText(Path(img).name)
            if Path(img).exists():
                pix = QPixmap(str(img)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.thumb_preview_label.setPixmap(pix)
            else:
                self.thumb_preview_label.clear()
                self.thumb_preview_label.setText("Image not found")
        else:
            self.rad_thumb_none.setChecked(True)
            self.video_scrub_widget.setVisible(False)
            self.file_browse_widget.setVisible(False)
            self.image_path_label.setText("No image selected")
            self.thumb_preview_label.clear()
            self.thumb_preview_label.setText("No Thumbnail")

        self._syncing_editor = False

        # Set Checklist selections
        self._set_checked_authors_in_ui(target.get("author_ids", []), target.get("author_term_ids", []))
        self._set_checked_categories_in_ui(target.get("category_ids", []))

    def _get_target_bounds(self, target_index: Optional[int] = None) -> Tuple[float, float]:
        idx = self._current_target_index if target_index is None else target_index
        if 0 <= idx < len(self.target_items):
            p = self.target_items[idx]
            if p.get("start") is not None and p.get("end") is not None:
                t_start = float(p["start"])
                t_end = float(p["end"])
                return t_start, max(t_start + 0.1, t_end)
        dur = max(0.1, float(getattr(self.main_window, "duration", 0.0) or 0.0))
        return 0.0, dur

    def _sync_slider_to_pos(self, pos: float):
        t_min, t_max = self._get_target_bounds()
        clamped = max(t_min, min(t_max, float(pos)))
        if 0 <= self._current_target_index < len(self.target_items):
            self.target_items[self._current_target_index]["frame_pos"] = clamped
        span = max(0.001, t_max - t_min)
        val = int(round(((clamped - t_min) / span) * 10000))
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(max(0, min(10000, val)))
        self.frame_slider.blockSignals(False)
        self.frame_time_label.setText(format_time(clamped, include_millis=True))

    def _on_slider_value_changed(self, val: int):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        t_min, t_max = self._get_target_bounds()
        pos = t_min + (val / 10000.0) * (t_max - t_min)
        self.target_items[self._current_target_index]["frame_pos"] = pos
        self.frame_time_label.setText(format_time(pos, include_millis=True))
        self._scrub_timer.start(120)

    def _on_scrub_timer_timeout(self):
        if 0 <= self._current_target_index < len(self.target_items):
            pos = self.target_items[self._current_target_index].get("frame_pos")
            self._capture_frame(pos=pos)

    def _on_step_frame(self, delta_secs: float):
        if not (0 <= self._current_target_index < len(self.target_items)):
            return
        t_min, t_max = self._get_target_bounds()
        cur_pos = self.target_items[self._current_target_index].get("frame_pos", t_min)
        new_pos = max(t_min, min(t_max, cur_pos + delta_secs))
        self._sync_slider_to_pos(new_pos)
        self._capture_frame(pos=new_pos)

    def _on_sync_playhead_clicked(self):
        if not (0 <= self._current_target_index < len(self.target_items)):
            return
        t_min, t_max = self._get_target_bounds()
        playhead_pos = float(getattr(self.main_window, "current_position", 0.0) or 0.0)
        new_pos = max(t_min, min(t_max, playhead_pos))
        self._sync_slider_to_pos(new_pos)
        self._capture_frame(pos=new_pos)

    def _capture_frame(self, pos: Optional[float] = None) -> Optional[str]:
        if not (0 <= self._current_target_index < len(self.target_items)):
            return None
        if not self._is_video_project:
            self.thumb_preview_label.setText("Audio-only media")
            return None
        media_file = getattr(self.main_window, "audio_file", None)
        if not media_file or not Path(media_file).exists():
            self.thumb_preview_label.setText("No media loaded")
            return None

        target = self.target_items[self._current_target_index]
        if pos is None:
            pos = float(target.get("frame_pos") or target.get("start") or 0.0)

        target["frame_pos"] = float(pos)
        out_dir = Path(tempfile.gettempdir())
        out_path = out_dir / f"rtvs_meta_frame_{self._current_target_index}_{os.getpid()}.jpg"
        ff = ffmpeg_path() or "ffmpeg"
        cmd = [
            ff, "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{max(0.0, float(pos)):.3f}",
            "-i", str(media_file),
            "-frames:v", "1",
            "-q:v", "2",
            str(out_path),
        ]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=5, creationflags=flags)
            if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
                target["featured_image"] = str(out_path)
                target["featured_image_mode"] = "grab"
                self._temp_preview_files.add(str(out_path))
                pix = QPixmap(str(out_path)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.thumb_preview_label.setPixmap(pix)
                return str(out_path)
        except Exception as exc:
            print(f"[STORY METADATA] Frame capture error: {exc}")
        self.thumb_preview_label.setText("Frame capture failed")
        return None

    def _on_thumb_mode_changed(self):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        target = self.target_items[self._current_target_index]
        if self.rad_thumb_none.isChecked():
            self.video_scrub_widget.setVisible(False)
            self.file_browse_widget.setVisible(False)
            self.image_path_label.setText("No image selected")
            self.thumb_preview_label.clear()
            self.thumb_preview_label.setText("No Thumbnail")
            target["featured_image"] = None
            target["featured_image_mode"] = "none"
        elif self.rad_thumb_grab.isChecked():
            self.file_browse_widget.setVisible(False)
            self.video_scrub_widget.setVisible(True)
            if target.get("frame_pos") is None:
                t_min, _ = self._get_target_bounds()
                target["frame_pos"] = t_min
            self._sync_slider_to_pos(target["frame_pos"])
            self._capture_frame(pos=target.get("frame_pos"))
        elif self.rad_thumb_file.isChecked():
            self.video_scrub_widget.setVisible(False)
            self.file_browse_widget.setVisible(True)
            custom_path = target.get("featured_image")
            if custom_path and Path(custom_path).exists() and target.get("featured_image_mode") == "file":
                self.image_path_label.setText(Path(custom_path).name)
                pix = QPixmap(str(custom_path)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.thumb_preview_label.setPixmap(pix)
            else:
                self.image_path_label.setText("Click Browse to select image file")
                self.thumb_preview_label.clear()
                self.thumb_preview_label.setText("No Image\nSelected")

    def _on_browse_image(self):
        if not (0 <= self._current_target_index < len(self.target_items)):
            return
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select Featured Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*.*)",
        )
        if fn:
            target = self.target_items[self._current_target_index]
            target["featured_image"] = fn
            target["featured_image_mode"] = "file"
            self.rad_thumb_file.setChecked(True)
            self.image_path_label.setText(Path(fn).name)
            pix = QPixmap(fn).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumb_preview_label.setPixmap(pix)

    def _on_title_text_changed(self, text: str):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["title"] = text
        self._update_target_list_item_display(self._current_target_index)

    def _on_excerpt_text_changed(self):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["excerpt"] = self.excerpt_edit.toPlainText().strip()

    def _on_auto_generate_excerpt(self):
        if not (0 <= self._current_target_index < len(self.target_items)):
            return
        target = self.target_items[self._current_target_index]
        st = target.get("start")
        et = target.get("end")
        raw_text = self.main_window._get_transcript_text_slice(st, et) if hasattr(self.main_window, "_get_transcript_text_slice") else ""
        exc = generate_story_excerpt(raw_text, 55)
        self.excerpt_edit.setPlainText(exc)
        target["excerpt"] = exc

    def _on_manual_author_changed(self, text: str):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["author"] = text.strip()
        self._update_target_list_item_display(self._current_target_index)

    def _on_tags_changed(self, text: str):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        tags = [t.strip() for t in text.split(",") if t.strip()]
        self.target_items[self._current_target_index]["tags"] = tags

    def _on_status_changed(self, _):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["status"] = self.status_combo.currentData()

    def _on_slug_changed(self, text: str):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["slug"] = text.strip()

    def _on_notes_changed(self, text: str):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        self.target_items[self._current_target_index]["notes"] = text.strip()

    def _on_author_item_changed(self, _):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        auth_ids, term_ids = self._get_checked_authors_from_ui()
        target = self.target_items[self._current_target_index]
        target["author_ids"] = auth_ids
        target["author_term_ids"] = term_ids

        # If manual author is empty and we have checked authors, fill manual author display name
        if not target.get("author"):
            names = []
            for i in range(self.authors_list.count()):
                item = self.authors_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(data, dict) and data.get("name"):
                        names.append(data["name"])
            if names:
                self.manual_author_input.setText(", ".join(names))
                target["author"] = ", ".join(names)

        self._update_target_list_item_display(self._current_target_index)

    def _on_category_item_changed(self, _):
        if self._syncing_editor or not (0 <= self._current_target_index < len(self.target_items)):
            return
        cat_ids = self._get_checked_categories_from_ui()
        self.target_items[self._current_target_index]["category_ids"] = cat_ids
        self._update_target_list_item_display(self._current_target_index)

    def _get_checked_authors_from_ui(self) -> Tuple[List[int], List[int]]:
        author_ids: List[int] = []
        author_term_ids: List[int] = []
        for i in range(self.authors_list.count()):
            item = self.authors_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    if data.get("is_guest"):
                        tid = data.get("term_id") or data.get("id")
                        if tid:
                            author_term_ids.append(int(tid))
                    else:
                        uid = data.get("user_id") or data.get("id")
                        if uid:
                            author_ids.append(int(uid))
        return author_ids, author_term_ids

    def _set_checked_authors_in_ui(self, author_ids: List[int], author_term_ids: List[int]):
        self._syncing_editor = True
        auth_set = set(int(x) for x in (author_ids or []))
        term_set = set(int(x) for x in (author_term_ids or []))
        for i in range(self.authors_list.count()):
            item = self.authors_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            checked = False
            if isinstance(data, dict):
                if data.get("is_guest"):
                    tid = data.get("term_id") or data.get("id")
                    if tid and int(tid) in term_set:
                        checked = True
                else:
                    uid = data.get("user_id") or data.get("id")
                    if uid and int(uid) in auth_set:
                        checked = True
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_editor = False

    def _get_checked_categories_from_ui(self) -> List[int]:
        cat_ids: List[int] = []
        for i in range(self.cats_list.count()):
            item = self.cats_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                cid = item.data(Qt.ItemDataRole.UserRole)
                if cid is not None:
                    cat_ids.append(int(cid))
        return cat_ids

    def _set_checked_categories_in_ui(self, cat_ids: List[int]):
        self._syncing_editor = True
        cid_set = set(int(x) for x in (cat_ids or []))
        for i in range(self.cats_list.count()):
            item = self.cats_list.item(i)
            cid = item.data(Qt.ItemDataRole.UserRole)
            checked = (cid is not None and int(cid) in cid_set)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_editor = False

    def save_all_to_project(self):
        """Commit all configured metadata into Project/Story data structures and sync UI."""
        stories = getattr(self.main_window, "stories", []) or []
        proj_meta = getattr(self.main_window, "project_metadata", None)
        if not isinstance(proj_meta, dict):
            proj_meta = {}
            self.main_window.project_metadata = proj_meta

        for target in self.target_items:
            t_type = target.get("type")
            if t_type == "full":
                proj_meta["title"] = target.get("title", "")
                proj_meta["author"] = target.get("author", "")
                proj_meta["excerpt"] = target.get("excerpt", "")
                proj_meta["tags"] = list(target.get("tags") or [])
                proj_meta["featured_image"] = target.get("featured_image")
                proj_meta["featured_image_mode"] = target.get("featured_image_mode", "none")
                proj_meta["notes"] = target.get("notes", "")

                wp_proj = proj_meta.setdefault("wordpress", {})
                wp_proj["title"] = target.get("title", "")
                wp_proj["excerpt"] = target.get("excerpt", "")
                wp_proj["manual_author"] = target.get("author", "")
                wp_proj["author_ids"] = list(target.get("author_ids") or [])
                wp_proj["author_term_ids"] = list(target.get("author_term_ids") or [])
                wp_proj["category_ids"] = list(target.get("category_ids") or [])
                wp_proj["tags"] = list(target.get("tags") or [])
                wp_proj["status"] = target.get("status", "draft")
                wp_proj["slug"] = target.get("slug", "")
                wp_proj["featured_image"] = target.get("featured_image")
                wp_proj["featured_image_mode"] = target.get("featured_image_mode", "none")
                wp_proj["frame_pos"] = target.get("frame_pos")

            elif t_type == "story":
                s_idx = target.get("index", -1)
                st_ref = target.get("story_ref")
                if not st_ref and 0 <= s_idx < len(stories):
                    st_ref = stories[s_idx]

                if st_ref:
                    # Update Title
                    new_title = target.get("title") or f"Story #{s_idx + 1}"
                    st_ref.title = new_title

                    # Update Metadata
                    if not hasattr(st_ref, "metadata") or st_ref.metadata is None:
                        st_ref.metadata = {}
                    st_ref.metadata["author"] = target.get("author", "")
                    st_ref.metadata["excerpt"] = target.get("excerpt", "")
                    st_ref.metadata["tags"] = list(target.get("tags") or [])
                    st_ref.metadata["featured_image"] = target.get("featured_image")
                    st_ref.metadata["featured_image_mode"] = target.get("featured_image_mode", "none")
                    st_ref.metadata["notes"] = target.get("notes", "")

                    wp_meta = st_ref.metadata.setdefault("wordpress", {})
                    wp_meta["title"] = new_title
                    wp_meta["excerpt"] = target.get("excerpt", "")
                    wp_meta["manual_author"] = target.get("author", "")
                    wp_meta["author_ids"] = list(target.get("author_ids") or [])
                    wp_meta["author_term_ids"] = list(target.get("author_term_ids") or [])
                    wp_meta["category_ids"] = list(target.get("category_ids") or [])
                    wp_meta["tags"] = list(target.get("tags") or [])
                    wp_meta["status"] = target.get("status", "draft")
                    wp_meta["slug"] = target.get("slug", "")
                    wp_meta["featured_image"] = target.get("featured_image")
                    wp_meta["featured_image_mode"] = target.get("featured_image_mode", "none")
                    wp_meta["frame_pos"] = target.get("frame_pos")

        # Instant Two-Way Synchronization with Main Window UI
        if hasattr(self.main_window, "refresh_story_list"):
            self.main_window.refresh_story_list()

        # Update currently selected story inputs if open in sidebar
        selected_indices = getattr(self.main_window, "current_selected_story_indices", []) or []
        if len(selected_indices) == 1:
            cur_idx = selected_indices[0]
            if 0 <= cur_idx < len(stories):
                cur_st = stories[cur_idx]
                if hasattr(self.main_window, "title_input") and self.main_window.title_input:
                    self.main_window.title_input.setText(cur_st.title or "")
                if hasattr(self.main_window, "author_input") and self.main_window.author_input:
                    self.main_window.author_input.setText(cur_st.metadata.get("author", "") if cur_st.metadata else "")
                if hasattr(self.main_window, "excerpt_edit") and self.main_window.excerpt_edit:
                    self.main_window.excerpt_edit.setText(cur_st.metadata.get("excerpt", "") if cur_st.metadata else "")

        # Mark project dirty and auto-save
        if hasattr(self.main_window, "mark_project_dirty"):
            self.main_window.mark_project_dirty("Update Story Metadata")
        elif hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)

        if hasattr(self.main_window, "save_project"):
            try:
                self.main_window.save_project()
            except Exception as e:
                print(f"[STORY METADATA] Error auto-saving project: {e}")

    def _on_save_and_close(self):
        self.save_all_to_project()
        self.accept()

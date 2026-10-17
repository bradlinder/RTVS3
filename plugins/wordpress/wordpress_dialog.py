"""WordPress Export Tab Widget and Post Metadata Dialog."""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QSettings, QRectF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
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
    ResizableTextEdit,
    ffmpeg_path,
    format_time,
    safe_filename,
)
from plugins.wordpress.client import (
    WordPressClient,
    generate_wp_excerpt as _client_generate_wp_excerpt,
    format_rich_text_to_html,
    format_parent_episode_notice,
    build_episode_stories_toc,
    WordPressSettingsDialog,
    execute_wordpress_upload,
    _get_wp_password,
)


def generate_wp_excerpt(transcript_words, start_t, end_t):
    slice_text = " ".join([w.get("text", "") for w in transcript_words if start_t <= float(w.get("start", 0)) <= end_t])
    return _client_generate_wp_excerpt(slice_text)


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
    res = subprocess.run(cmd, capture_output=True, creationflags=flags)
    return res.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0


class WordPressExportTabWidget(QWidget):
    """Configuration and preview panel for WordPress Draft Posts."""

    def __init__(self, parent: QWidget, main_window: Any, metadata_editor_mode: bool = False):
        super().__init__(parent)
        self.main_window = main_window
        self.metadata_editor_mode = metadata_editor_mode
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._is_video_project = bool(getattr(self.main_window, "current_media_is_video", False))
        self._temp_preview_files = set()

        self._wp_scrub_timer = QTimer(self)
        self._wp_scrub_timer.setSingleShot(True)
        self._wp_scrub_timer.setInterval(120)
        self._wp_scrub_timer.timeout.connect(self._on_wp_scrub_timer_timeout)

        self.wp_cached_authors_data: List[Dict[str, Any]] = []
        self.wp_cached_categories_data: List[Dict[str, Any]] = []
        self.wp_post_items: List[Dict[str, Any]] = []
        self._current_post_index = 0
        self._syncing_post_editor = False

        self._setup_ui()

    def _setup_ui(self):
        wp_page_layout = QVBoxLayout(self)
        wp_page_layout.setContentsMargins(0, 0, 0, 0)
        wp_page_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>WordPress Gutenberg Post Publisher</b>"))
        top_bar.addStretch()

        self.wp_settings_btn = QPushButton("WordPress Account & API Settings...", self)
        self.wp_settings_btn.clicked.connect(self._open_wp_settings)
        top_bar.addWidget(self.wp_settings_btn)

        self.wp_refresh_meta_btn = QPushButton("Refresh WP Categories & Authors", self)
        self.wp_refresh_meta_btn.clicked.connect(self._refresh_wp_metadata)
        top_bar.addWidget(self.wp_refresh_meta_btn)
        wp_page_layout.addLayout(top_bar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("<b>Stories & Draft Posts Queue</b>"))
        self.wp_posts_list_widget = QListWidget(self)
        self.wp_posts_list_widget.currentRowChanged.connect(self._on_wp_post_selection_changed)
        left_col.addWidget(self.wp_posts_list_widget)

        batch_apply_group = QGroupBox("Bulk Apply to All Posts", self)
        batch_layout = QVBoxLayout(batch_apply_group)
        batch_btn_row1 = QHBoxLayout()
        self.batch_authors_btn = QPushButton("Apply Authors...", self)
        self.batch_authors_btn.clicked.connect(self._apply_authors_to_all_posts)
        batch_btn_row1.addWidget(self.batch_authors_btn)

        self.batch_cats_btn = QPushButton("Apply Categories...", self)
        self.batch_cats_btn.clicked.connect(self._apply_categories_to_all_posts)
        batch_btn_row1.addWidget(self.batch_cats_btn)
        batch_layout.addLayout(batch_btn_row1)

        self.batch_thumbs_btn = QPushButton("Regenerate Featured Images for All...", self)
        self.batch_thumbs_btn.clicked.connect(self._apply_thumbnails_to_all_posts)
        batch_layout.addWidget(self.batch_thumbs_btn)
        left_col.addWidget(batch_apply_group)
        content_layout.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("<b>Selected Post Metadata & Gutenberg Preview</b>"))

        form_scroll = QScrollArea(self)
        form_scroll.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)

        self.wp_title_edit = QLineEdit(self)
        self.wp_title_edit.textChanged.connect(self._on_title_edited)
        self.form_layout.addRow("Post Title:", self.wp_title_edit)

        slug_row = QHBoxLayout()
        self.wp_slug_edit = QLineEdit(self)
        slug_row.addWidget(self.wp_slug_edit, 1)
        self.wp_status_combo = QComboBox(self)
        self.wp_status_combo.addItems(["Draft", "Publish", "Pending Review", "Private"])
        slug_row.addWidget(QLabel("Status:"))
        slug_row.addWidget(self.wp_status_combo)
        self.form_layout.addRow("URL Slug & Status:", slug_row)

        self.wp_excerpt_edit = ResizableTextEdit(self)
        self.wp_excerpt_edit.setMaximumHeight(70)
        self.wp_excerpt_edit.textChanged.connect(self._on_excerpt_edited)
        
        excerpt_top = QHBoxLayout()
        excerpt_top.addWidget(QLabel("Excerpt / Subtitle:"))
        excerpt_top.addStretch()
        self.wp_auto_excerpt_btn = QPushButton("Auto-Generate from Transcript", self)
        self.wp_auto_excerpt_btn.clicked.connect(self._auto_generate_current_excerpt)
        excerpt_top.addWidget(self.wp_auto_excerpt_btn)
        
        excerpt_box = QWidget()
        ex_layout = QVBoxLayout(excerpt_box)
        ex_layout.setContentsMargins(0, 0, 0, 0)
        ex_layout.addLayout(excerpt_top)
        ex_layout.addWidget(self.wp_excerpt_edit)
        self.form_layout.addRow(excerpt_box)

        tax_row = QHBoxLayout()
        
        auth_box = QVBoxLayout()
        auth_top = QHBoxLayout()
        auth_top.addWidget(QLabel("WordPress Authors:"))
        auth_top.addStretch()
        self.wp_clear_auth_btn = QPushButton("Clear", self)
        self.wp_clear_auth_btn.setMaximumWidth(50)
        self.wp_clear_auth_btn.clicked.connect(self._clear_current_authors)
        auth_top.addWidget(self.wp_clear_auth_btn)
        auth_box.addLayout(auth_top)

        self.wp_authors_list = QListWidget(self)
        self.wp_authors_list.setMaximumHeight(110)
        self.wp_authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.wp_authors_list.itemChanged.connect(self._on_author_item_changed)
        auth_box.addWidget(self.wp_authors_list)
        
        self.wp_apply_auth_sel_btn = QPushButton("Apply to Selected Stories...", self)
        self.wp_apply_auth_sel_btn.clicked.connect(self._apply_authors_to_selected_stories)
        auth_box.addWidget(self.wp_apply_auth_sel_btn)
        tax_row.addLayout(auth_box, 1)

        cats_box = QVBoxLayout()
        cats_top = QHBoxLayout()
        cats_top.addWidget(QLabel("Categories:"))
        cats_top.addStretch()
        self.wp_clear_cats_btn = QPushButton("Clear", self)
        self.wp_clear_cats_btn.setMaximumWidth(50)
        self.wp_clear_cats_btn.clicked.connect(self._clear_current_categories)
        cats_top.addWidget(self.wp_clear_cats_btn)
        cats_box.addLayout(cats_top)

        self.wp_categories_list = QListWidget(self)
        self.wp_categories_list.setMaximumHeight(110)
        self.wp_categories_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.wp_categories_list.itemChanged.connect(self._on_category_item_changed)
        cats_box.addWidget(self.wp_categories_list)

        self.wp_apply_cats_sel_btn = QPushButton("Apply to Selected Stories...", self)
        self.wp_apply_cats_sel_btn.clicked.connect(self._apply_categories_to_selected_stories)
        cats_box.addWidget(self.wp_apply_cats_sel_btn)
        tax_row.addLayout(cats_box, 1)

        self.form_layout.addRow(tax_row)

        thumb_box = QVBoxLayout()
        thumb_top = QHBoxLayout()
        thumb_top.addWidget(QLabel("Featured Image (Thumbnail):"))
        thumb_top.addStretch()
        self.wp_apply_thumb_sel_btn = QPushButton("Apply to Selected Stories...", self)
        self.wp_apply_thumb_sel_btn.clicked.connect(self._apply_thumbnails_to_selected_stories)
        thumb_top.addWidget(self.wp_apply_thumb_sel_btn)
        thumb_box.addLayout(thumb_top)

        thumb_mid = QHBoxLayout()
        self.wp_thumb_preview_lbl = QLabel(self)
        self.wp_thumb_preview_lbl.setFixedSize(160, 90)
        self.wp_thumb_preview_lbl.setStyleSheet("background: #111; border: 1px solid #444; border-radius: 4px;")
        self.wp_thumb_preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wp_thumb_preview_lbl.setText("No Image")
        thumb_mid.addWidget(self.wp_thumb_preview_lbl)

        thumb_controls = QVBoxLayout()
        self.wp_thumb_mode_combo = QComboBox(self)
        self.wp_thumb_mode_combo.addItems([
            "Auto-capture frame at story start",
            "Auto-capture frame at story midpoint",
            "Custom image file...",
            "None / Do not upload"
        ])
        self.wp_thumb_mode_combo.currentIndexChanged.connect(self._on_wp_thumb_mode_changed)
        thumb_controls.addWidget(self.wp_thumb_mode_combo)

        thumb_sub_row = QHBoxLayout()
        self.wp_thumb_time_lbl = QLabel("Time: 0.00s")
        thumb_sub_row.addWidget(self.wp_thumb_time_lbl)
        thumb_sub_row.addStretch()
        self.wp_thumb_browse_btn = QPushButton("Browse...", self)
        self.wp_thumb_browse_btn.clicked.connect(self._on_wp_browse_thumb)
        thumb_sub_row.addWidget(self.wp_thumb_browse_btn)
        thumb_controls.addLayout(thumb_sub_row)
        thumb_mid.addLayout(thumb_controls, 1)
        thumb_box.addLayout(thumb_mid)

        if not self._is_video_project:
            self.wp_thumb_mode_combo.setEnabled(False)
            self.wp_thumb_browse_btn.setEnabled(False)
            self.wp_thumb_preview_lbl.setText("Audio-only Project\n(No Video Frames)")

        self.form_layout.addRow(thumb_box)

        if self._is_video_project:
            scrub_box = QVBoxLayout()
            scrub_top = QHBoxLayout()
            scrub_top.addWidget(QLabel("Thumbnail Frame Timecode Scrub:"))
            scrub_top.addStretch()
            self.wp_sync_playhead_btn = QPushButton("Sync from Main Playhead", self)
            self.wp_sync_playhead_btn.clicked.connect(self._on_wp_sync_playhead)
            scrub_top.addWidget(self.wp_sync_playhead_btn)
            scrub_box.addLayout(scrub_top)

            slider_row = QHBoxLayout()
            self.wp_time_slider = QSlider(Qt.Orientation.Horizontal, self)
            self.wp_time_slider.setRange(0, 1000)
            self.wp_time_slider.valueChanged.connect(self._on_wp_slider_value_changed)
            slider_row.addWidget(self.wp_time_slider, 1)
            
            self.wp_step_back_btn = QPushButton("◀ 1s", self)
            self.wp_step_back_btn.setMaximumWidth(55)
            self.wp_step_back_btn.clicked.connect(lambda: self._on_wp_step(-1.0))
            slider_row.addWidget(self.wp_step_back_btn)

            self.wp_step_fwd_btn = QPushButton("1s ▶", self)
            self.wp_step_fwd_btn.setMaximumWidth(55)
            self.wp_step_fwd_btn.clicked.connect(lambda: self._on_wp_step(1.0))
            slider_row.addWidget(self.wp_step_fwd_btn)
            scrub_box.addLayout(slider_row)
            self.form_layout.addRow(scrub_box)

        self.wp_content_preview_edit = ResizableTextEdit(self)
        self.wp_content_preview_edit.setMinimumHeight(160)
        self.form_layout.addRow("Gutenberg HTML Content Preview:", self.wp_content_preview_edit)

        form_container.setLayout(self.form_layout)
        form_scroll.setWidget(form_container)
        right_col.addWidget(form_scroll)
        content_layout.addLayout(right_col, 2)

        wp_page_layout.addLayout(content_layout)
        self._populate_wp_export_metadata()

    def update_wp_pres_visibility(self):
        pass

    def _update_wp_conn_status(self):
        pass

    def _open_wp_settings(self):
        dlg = WordPressSettingsDialog(self, self.main_window)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_wp_metadata()

    def _filter_authors_list(self, text: str):
        pass

    def _filter_categories_list(self, text: str):
        pass

    def _on_title_edited(self, text: str):
        if self._syncing_post_editor:
            return
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["title"] = text
            self._update_post_list_item_label(self._current_post_index)

    def _on_excerpt_edited(self):
        if self._syncing_post_editor:
            return
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["excerpt"] = self.wp_excerpt_edit.toPlainText()

    def _auto_generate_current_excerpt(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[self._current_post_index]
        transcript_words = getattr(self.main_window, "transcript_words", [])
        start_t = post.get("start", 0.0)
        end_t = post.get("end", 0.0)
        excerpt = generate_wp_excerpt(transcript_words, start_t, end_t)
        self.wp_excerpt_edit.setPlainText(excerpt)
        post["excerpt"] = excerpt

    def _autofill_all_excerpts(self):
        transcript_words = getattr(self.main_window, "transcript_words", [])
        for post in self.wp_post_items:
            start_t = post.get("start", 0.0)
            end_t = post.get("end", 0.0)
            post["excerpt"] = generate_wp_excerpt(transcript_words, start_t, end_t)
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self._load_post_editor_state(self._current_post_index)

    def _on_author_item_changed(self, item):
        if self._syncing_post_editor:
            return
        auth_ids, auth_term_ids = self._get_editor_checked_authors()
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["author_ids"] = auth_ids
            self.wp_post_items[self._current_post_index]["author_term_ids"] = auth_term_ids

    def _on_category_item_changed(self, item):
        if self._syncing_post_editor:
            return
        cat_ids = self._get_editor_checked_categories()
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["category_ids"] = cat_ids

    def _clear_current_authors(self):
        self._syncing_post_editor = True
        for i in range(self.wp_authors_list.count()):
            item = self.wp_authors_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self._syncing_post_editor = False
        self._on_author_item_changed(None)

    def _clear_current_categories(self):
        self._syncing_post_editor = True
        for i in range(self.wp_categories_list.count()):
            item = self.wp_categories_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self._syncing_post_editor = False
        self._on_category_item_changed(None)

    def _get_selected_story_indices(self) -> List[int]:
        if hasattr(self.main_window, "current_selected_story_indices") and self.main_window.current_selected_story_indices:
            return [i for i in self.main_window.current_selected_story_indices if 0 <= i < len(self.wp_post_items)]
        if 0 <= self._current_post_index < len(self.wp_post_items):
            return [self._current_post_index]
        return []

    def _apply_authors_to_selected_stories(self):
        indices = self._get_selected_story_indices()
        if not indices:
            return
        auth_ids, auth_term_ids = self._get_editor_checked_authors()
        for idx in indices:
            self.wp_post_items[idx]["author_ids"] = list(auth_ids)
            self.wp_post_items[idx]["author_term_ids"] = list(auth_term_ids)
        QMessageBox.information(self, "Applied", f"Applied authors to {len(indices)} selected post(s).")

    def _apply_categories_to_selected_stories(self):
        indices = self._get_selected_story_indices()
        if not indices:
            return
        cat_ids = self._get_editor_checked_categories()
        for idx in indices:
            self.wp_post_items[idx]["category_ids"] = list(cat_ids)
        QMessageBox.information(self, "Applied", f"Applied categories to {len(indices)} selected post(s).")

    def _apply_thumbnails_to_selected_stories(self):
        indices = self._get_selected_story_indices()
        if not indices or not self._is_video_project:
            return
        video_path = getattr(self.main_window, "audio_file", None)
        if not video_path:
            return
        count = 0
        for idx in indices:
            post = self.wp_post_items[idx]
            mode = post.get("thumb_mode", 0)
            if mode == 3:  # None
                continue
            start_t = post.get("start", 0.0)
            end_t = post.get("end", 0.0)
            t_pt = start_t if mode == 0 else (start_t + end_t) / 2.0
            tmp_img = tempfile.mktemp(suffix=".jpg", prefix="rtvs_wp_thumb_")
            if capture_video_frame(video_path, t_pt, tmp_img):
                post["custom_thumb_path"] = tmp_img
                self._temp_preview_files.add(tmp_img)
                count += 1
        QMessageBox.information(self, "Thumbnails Regenerated", f"Regenerated featured image thumbnails for {count} selected post(s).")

    def _apply_authors_to_all_posts(self):
        auth_ids, auth_term_ids = self._get_editor_checked_authors()
        for post in self.wp_post_items:
            post["author_ids"] = list(auth_ids)
            post["author_term_ids"] = list(auth_term_ids)
        QMessageBox.information(self, "Applied", f"Applied authors to all {len(self.wp_post_items)} posts.")

    def _apply_categories_to_all_posts(self):
        cat_ids = self._get_editor_checked_categories()
        for post in self.wp_post_items:
            post["category_ids"] = list(cat_ids)
        QMessageBox.information(self, "Applied", f"Applied categories to all {len(self.wp_post_items)} posts.")

    def _apply_thumbnails_to_all_posts(self):
        if not self._is_video_project:
            return
        video_path = getattr(self.main_window, "audio_file", None)
        if not video_path:
            return
        count = 0
        for post in self.wp_post_items:
            mode = post.get("thumb_mode", 0)
            if mode == 3:
                continue
            start_t = post.get("start", 0.0)
            end_t = post.get("end", 0.0)
            t_pt = start_t if mode == 0 else (start_t + end_t) / 2.0
            tmp_img = tempfile.mktemp(suffix=".jpg", prefix="rtvs_wp_thumb_")
            if capture_video_frame(video_path, t_pt, tmp_img):
                post["custom_thumb_path"] = tmp_img
                self._temp_preview_files.add(tmp_img)
                count += 1
        QMessageBox.information(self, "Thumbnails Regenerated", f"Regenerated featured image thumbnails for all {count} posts.")

    def _sync_post_to_project(self, idx: int):
        pass

    def save_all_posts_to_project(self):
        pass

    def _update_post_list_item_label(self, idx: int):
        if 0 <= idx < self.wp_posts_list_widget.count():
            post = self.wp_post_items[idx]
            t_str = f"[{format_time(post.get('start', 0))} - {format_time(post.get('end', 0))}]"
            self.wp_posts_list_widget.item(idx).setText(f"{idx+1}. {post.get('title', '')} {t_str}")

    def _on_wp_post_selection_changed(self, row: int):
        if row < 0 or row >= len(self.wp_post_items):
            return
        self._current_post_index = row
        self._load_post_editor_state(row)

    def _get_editor_checked_authors(self) -> Tuple[List[int], List[int]]:
        auth_ids = []
        auth_term_ids = []
        for i in range(self.wp_authors_list.count()):
            item = self.wp_authors_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    if "id" in data:
                        auth_ids.append(int(data["id"]))
                    if "term_id" in data:
                        auth_term_ids.append(int(data["term_id"]))
        return auth_ids, auth_term_ids

    def _set_editor_checked_authors(self, author_ids: List[int], author_term_ids: List[int]):
        self._syncing_post_editor = True
        for i in range(self.wp_authors_list.count()):
            item = self.wp_authors_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            checked = False
            if isinstance(data, dict):
                if data.get("id") in author_ids or data.get("term_id") in author_term_ids:
                    checked = True
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_post_editor = False

    def _get_editor_checked_categories(self) -> List[int]:
        cat_ids = []
        for i in range(self.wp_categories_list.count()):
            item = self.wp_categories_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict) and "id" in data:
                    cat_ids.append(int(data["id"]))
        return cat_ids

    def _set_editor_checked_categories(self, cat_ids: List[int]):
        self._syncing_post_editor = True
        for i in range(self.wp_categories_list.count()):
            item = self.wp_categories_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            checked = False
            if isinstance(data, dict) and data.get("id") in cat_ids:
                checked = True
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_post_editor = False

    def _get_wp_post_bounds(self, post_index=None) -> Tuple[float, float]:
        idx = self._current_post_index if post_index is None else post_index
        if 0 <= idx < len(self.wp_post_items):
            post = self.wp_post_items[idx]
            return float(post.get("start", 0.0)), float(post.get("end", 0.0))
        return 0.0, 1.0

    def _sync_wp_slider_to_pos(self, pos: float):
        start_t, end_t = self._get_wp_post_bounds()
        dur = max(0.001, end_t - start_t)
        clamped = max(start_t, min(end_t, pos))
        ratio = (clamped - start_t) / dur
        self.wp_time_slider.blockSignals(True)
        self.wp_time_slider.setValue(int(ratio * 1000))
        self.wp_time_slider.blockSignals(False)
        self.wp_thumb_time_lbl.setText(f"Time: {clamped:.2f}s")

    def _on_wp_slider_value_changed(self, val: int):
        if not self._is_video_project:
            return
        start_t, end_t = self._get_wp_post_bounds()
        dur = end_t - start_t
        t_pt = start_t + (val / 1000.0) * dur
        self.wp_thumb_time_lbl.setText(f"Time: {t_pt:.2f}s")
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["thumb_time"] = t_pt
        self._wp_scrub_timer.start()

    def _on_wp_scrub_timer_timeout(self):
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self._capture_wp_frame()

    def _on_wp_step(self, delta_secs: float):
        if not self._is_video_project:
            return
        start_t, end_t = self._get_wp_post_bounds()
        if 0 <= self._current_post_index < len(self.wp_post_items):
            cur_t = self.wp_post_items[self._current_post_index].get("thumb_time", start_t)
            new_t = max(start_t, min(end_t, cur_t + delta_secs))
            self.wp_post_items[self._current_post_index]["thumb_time"] = new_t
            self._sync_wp_slider_to_pos(new_t)
            self._capture_wp_frame(new_t)

    def _on_wp_sync_playhead(self):
        if not self._is_video_project:
            return
        cur_pos = float(getattr(self.main_window, "position", 0.0))
        start_t, end_t = self._get_wp_post_bounds()
        if start_t <= cur_pos <= end_t:
            if 0 <= self._current_post_index < len(self.wp_post_items):
                self.wp_post_items[self._current_post_index]["thumb_time"] = cur_pos
                self._sync_wp_slider_to_pos(cur_pos)
                self._capture_wp_frame(cur_pos)

    def _load_post_editor_state(self, index: int):
        if not (0 <= index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[index]
        self._syncing_post_editor = True
        self.wp_title_edit.setText(post.get("title", ""))
        self.wp_slug_edit.setText(post.get("slug", ""))
        self.wp_excerpt_edit.setPlainText(post.get("excerpt", ""))
        self.wp_status_combo.setCurrentText(post.get("status", "Draft"))

        self._set_editor_checked_authors(post.get("author_ids", []), post.get("author_term_ids", []))
        self._set_editor_checked_categories(post.get("category_ids", []))

        mode = post.get("thumb_mode", 0)
        self.wp_thumb_mode_combo.setCurrentIndex(mode)

        if self._is_video_project:
            t_pt = post.get("thumb_time", post.get("start", 0.0))
            self._sync_wp_slider_to_pos(t_pt)
            custom_path = post.get("custom_thumb_path", "")
            if custom_path and Path(custom_path).exists():
                pix = QPixmap(custom_path)
                if not pix.isNull():
                    self.wp_thumb_preview_lbl.setPixmap(pix.scaled(self.wp_thumb_preview_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    self.wp_thumb_preview_lbl.setText("Invalid Image")
            else:
                self.wp_thumb_preview_lbl.setText("No Image Captured")

        html_preview = post.get("html_content", "")
        self.wp_content_preview_edit.setPlainText(html_preview)
        self._syncing_post_editor = False

    def _on_wp_thumb_mode_changed(self):
        if self._syncing_post_editor:
            return
        mode = self.wp_thumb_mode_combo.currentIndex()
        if 0 <= self._current_post_index < len(self.wp_post_items):
            post = self.wp_post_items[self._current_post_index]
            post["thumb_mode"] = mode
            if mode == 3:
                self.wp_thumb_preview_lbl.setText("Disabled")
                post["custom_thumb_path"] = ""
            elif mode in (0, 1):
                start_t, end_t = self._get_wp_post_bounds()
                t_pt = start_t if mode == 0 else (start_t + end_t) / 2.0
                post["thumb_time"] = t_pt
                self._sync_wp_slider_to_pos(t_pt)
                self._capture_wp_frame(t_pt)

    def _capture_wp_frame(self, pos=None):
        if not self._is_video_project:
            return
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[self._current_post_index]
        if post.get("thumb_mode", 0) == 3:
            return
        video_path = getattr(self.main_window, "audio_file", None)
        if not video_path or not Path(video_path).exists():
            return
        t_pt = pos if pos is not None else post.get("thumb_time", post.get("start", 0.0))
        tmp_img = tempfile.mktemp(suffix=".jpg", prefix="rtvs_wp_thumb_")
        if capture_video_frame(video_path, t_pt, tmp_img):
            post["custom_thumb_path"] = tmp_img
            self._temp_preview_files.add(tmp_img)
            pix = QPixmap(tmp_img)
            if not pix.isNull():
                self.wp_thumb_preview_lbl.setPixmap(pix.scaled(self.wp_thumb_preview_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _on_wp_browse_thumb(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Featured Image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not filepath:
            return
        if 0 <= self._current_post_index < len(self.wp_post_items):
            post = self.wp_post_items[self._current_post_index]
            post["custom_thumb_path"] = filepath
            post["thumb_mode"] = 2
            self._syncing_post_editor = True
            self.wp_thumb_mode_combo.setCurrentIndex(2)
            self._syncing_post_editor = False
            pix = QPixmap(filepath)
            if not pix.isNull():
                self.wp_thumb_preview_lbl.setPixmap(pix.scaled(self.wp_thumb_preview_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def rebuild_post_items(self, scope: Optional[str] = None):
        stories = getattr(self.main_window, "stories", [])
        transcript_words = getattr(self.main_window, "transcript_words", [])
        audio_name = Path(getattr(self.main_window, "audio_file", "Podcast Episode")).stem

        scope = scope or self.settings.value("wordpress/export_scope", "individual_stories")

        posts_list = getattr(self, "wp_posts_list_widget", None) or getattr(self, "wp_posts_list", None)
        if posts_list and hasattr(posts_list, "blockSignals"):
            posts_list.blockSignals(True)
        if posts_list and hasattr(posts_list, "clear"):
            posts_list.clear()
        self.wp_post_items.clear()

        def _safe_get(obj, attr, default=0.0):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        def build_story_item(idx: int, st: Any) -> dict:
            title = _safe_get(st, "title", f"Story #{idx+1}")
            start_t = float(_safe_get(st, "start", 0.0))
            end_t = float(_safe_get(st, "end", 1.0))
            excerpt = generate_wp_excerpt(transcript_words, start_t, end_t)
            
            story_words = [w for w in transcript_words if start_t <= float(_safe_get(w, "start", 0)) <= end_t]
            html_content = format_rich_text_to_html(story_words, True, st)

            return {
                "story_index": idx,
                "title": title,
                "slug": safe_filename(title).lower(),
                "status": "Draft",
                "excerpt": excerpt,
                "start": start_t,
                "end": end_t,
                "thumb_mode": 0,
                "thumb_time": start_t,
                "custom_thumb_path": "",
                "author_ids": [],
                "author_term_ids": [],
                "category_ids": [],
                "html_content": html_content,
            }

        if scope in ("full_episode", "full"):
            full_title = f"{audio_name} - Full Episode & Rundown" if scope == "full_episode" else f"{audio_name} - Full Episode"
            start_t = float(_safe_get(stories[0], "start", 0.0)) if stories else 0.0
            end_t = float(_safe_get(stories[-1], "end", 60.0)) if stories else float(getattr(self.main_window, "audio_duration", 60.0))
            excerpt = generate_wp_excerpt(transcript_words, start_t, end_t)
            toc_html = build_episode_stories_toc(stories)
            full_html = toc_html + format_rich_text_to_html(transcript_words, None)

            self.wp_post_items.append({
                "story_index": -1,
                "title": full_title,
                "task_label": "Full Episode",
                "slug": safe_filename(full_title).lower(),
                "status": "Draft",
                "excerpt": excerpt,
                "start": start_t,
                "end": end_t,
                "thumb_mode": 0,
                "thumb_time": start_t,
                "custom_thumb_path": "",
                "author_ids": [],
                "author_term_ids": [],
                "category_ids": [],
                "html_content": full_html,
            })
        elif scope in ("individual_stories", "all_stories"):
            for idx, st in enumerate(stories):
                self.wp_post_items.append(build_story_item(idx, st))
        elif scope in ("selected_stories", "selected"):
            selected_indices = getattr(self.main_window, "current_selected_story_indices", [])
            for idx in selected_indices:
                if 0 <= idx < len(stories):
                    self.wp_post_items.append(build_story_item(idx, stories[idx]))
        elif scope in ("both", "full_and_all_stories"):
            full_title = f"{audio_name} - Full Episode"
            start_t = float(_safe_get(stories[0], "start", 0.0)) if stories else 0.0
            end_t = float(_safe_get(stories[-1], "end", 60.0)) if stories else float(getattr(self.main_window, "audio_duration", 60.0))
            excerpt = generate_wp_excerpt(transcript_words, start_t, end_t)
            toc_html = build_episode_stories_toc(stories)
            full_html = toc_html + format_rich_text_to_html(transcript_words, None)
            
            self.wp_post_items.append({
                "story_index": -1,
                "title": full_title,
                "task_label": "Full Episode",
                "slug": safe_filename(full_title).lower(),
                "status": "Draft",
                "excerpt": excerpt,
                "start": start_t,
                "end": end_t,
                "thumb_mode": 0,
                "thumb_time": start_t,
                "custom_thumb_path": "",
                "author_ids": [],
                "author_term_ids": [],
                "category_ids": [],
                "html_content": full_html,
            })
            for idx, st in enumerate(stories):
                self.wp_post_items.append(build_story_item(idx, st))

        for idx, post in enumerate(self.wp_post_items):
            t_str = f"[{format_time(post.get('start', 0))} - {format_time(post.get('end', 0))}]"
            item = QListWidgetItem(f"{idx+1}. {post.get('title', '')} {t_str}") if 'QListWidgetItem' in globals() else f"{idx+1}. {post.get('title', '')} {t_str}"
            if posts_list and hasattr(posts_list, "addItem"):
                posts_list.addItem(item)

        if posts_list and hasattr(posts_list, "blockSignals"):
            posts_list.blockSignals(False)
        if self.wp_post_items and posts_list and hasattr(posts_list, "setCurrentRow"):
            posts_list.setCurrentRow(0)

    def _populate_wp_export_metadata(self, force_refresh: bool = False):
        client = WordPressClient.from_settings()
        if not client.is_configured():
            self.wp_authors_list.clear()
            self.wp_categories_list.clear()
            self.rebuild_post_items()
            return

        authors, cats = client.fetch_site_metadata(force_refresh=force_refresh)
        self.wp_cached_authors_data = authors
        self.wp_cached_categories_data = cats

        self.wp_authors_list.blockSignals(True)
        self.wp_authors_list.clear()
        for auth in authors:
            name = auth.get("name", "Author")
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, auth)
            self.wp_authors_list.addItem(item)
        self.wp_authors_list.blockSignals(False)

        self.wp_categories_list.blockSignals(True)
        self.wp_categories_list.clear()
        for cat in cats:
            name = cat.get("name", "Category")
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, cat)
            self.wp_categories_list.addItem(item)
        self.wp_categories_list.blockSignals(False)

        self.rebuild_post_items()

    def _refresh_wp_metadata(self):
        self._populate_wp_export_metadata(force_refresh=True)
        QMessageBox.information(self, "Refreshed", "Successfully refreshed WordPress authors and categories from REST API.")


class WordPressPostMetadataDialog(QDialog):
    """Dialog for editing WordPress post metadata for an individual story."""

    def __init__(self, parent: Optional[QWidget], main_window: Any, target_story_index: Optional[int] = None):
        super().__init__(parent)
        self.main_window = main_window
        self.target_story_index = target_story_index
        self.setWindowTitle("WordPress Story Post Metadata")
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit(self)
        form.addRow("Post Title:", self.title_edit)

        self.slug_edit = QLineEdit(self)
        form.addRow("URL Slug:", self.slug_edit)

        self.status_combo = QComboBox(self)
        self.status_combo.addItems(["Draft", "Publish", "Pending Review", "Private"])
        form.addRow("Post Status:", self.status_combo)

        self.excerpt_edit = ResizableTextEdit(self)
        form.addRow("Excerpt / Subtitle:", self.excerpt_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save & Close", self)
        save_btn.clicked.connect(self._on_save_and_close)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_save_and_close(self):
        self.accept()

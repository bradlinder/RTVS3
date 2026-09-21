"""WordPress Publisher Plugin for Radio & TV Segmenter.

Allows direct publishing of audio/video stories to WordPress with
custom excerpt, author assignment, categories, and custom featured image
(local file or video frame grab at playhead/story timestamp).
"""
from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QFileDialog,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QProgressBar,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    PROJECT_VERSION,
    QSettings,
    ffmpeg_path,
    format_time,
    safe_filename,
)
from plugins.base import BasePlugin, PluginManifest
from plugins.wordpress.client import (
    WordPressClient,
    _get_wp_password,
    _set_wp_password,
    generate_wp_excerpt,
    WordPressSettingsDialog,
    execute_wordpress_upload,
)


def capture_video_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    """Extract a high quality single frame from a video using fast seeking FFmpeg."""
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


class WordPressPublishDialog(QDialog):
    """Publish a story or project to WordPress with featured image selection."""

    def __init__(self, plugin: Plugin, parent: Any = None, story: Any = None):
        super().__init__(parent)
        self.plugin = plugin
        self.app = plugin.app
        self.story = story
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.temp_dir = tempfile.mkdtemp(prefix="rtvs_wp_")
        self.captured_frame_path: Optional[str] = None
        self.custom_image_path: Optional[str] = None

        self.setWindowTitle("Publish Story to WordPress")
        self.setMinimumSize(660, 680)
        self.setup_ui()
        self.load_metadata()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Connection info header
        site_url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
        username = str(self.settings.value("wp_username", "") or "")
        header_text = f"<b>WordPress Site:</b> {site_url or '<i>Not configured</i>'} ({username or 'No user'})"
        self.conn_label = QLabel(header_text)
        layout.addWidget(self.conn_label)

        # Post fields
        post_group = QGroupBox("Post Details")
        form = QFormLayout(post_group)

        self.title_edit = QLineEdit()
        form.addRow("Title:", self.title_edit)

        self.excerpt_edit = QTextEdit()
        self.excerpt_edit.setMaximumHeight(65)
        form.addRow("Excerpt:", self.excerpt_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Draft", "draft")
        self.status_combo.addItem("Pending Review", "pending")
        self.status_combo.addItem("Publish Immediately", "publish")
        form.addRow("Status:", self.status_combo)

        layout.addWidget(post_group)

        # Custom Text / Notice Group
        custom_group = QGroupBox("Custom Header / Footer Text (Optional)")
        custom_layout = QVBoxLayout(custom_group)

        self.custom_text_edit = QTextEdit()
        self.custom_text_edit.setPlaceholderText(
            "e.g. Note: The following transcript was machine-generated and may contain some spelling errors or other inaccuracies."
        )
        self.custom_text_edit.setMaximumHeight(65)
        custom_layout.addWidget(self.custom_text_edit)

        pos_row = QHBoxLayout()
        self.pos_button_group = QButtonGroup(self)
        self.rad_pos_top = QRadioButton("Place at top of post")
        self.rad_pos_bottom = QRadioButton("Place at bottom of post")
        self.pos_button_group.addButton(self.rad_pos_top)
        self.pos_button_group.addButton(self.rad_pos_bottom)
        pos_row.addWidget(self.rad_pos_top)
        pos_row.addWidget(self.rad_pos_bottom)
        pos_row.addStretch()
        custom_layout.addLayout(pos_row)

        opt_layout = QVBoxLayout()
        self.chk_no_snippet = QCheckBox("Hide from Google & search engine snippets (data-nosnippet)")
        self.chk_no_snippet.setToolTip(
            "Wraps custom text in data-nosnippet and Google search engine directives so search engines index the story but exclude this notice from search result summaries."
        )
        self.chk_no_excerpt = QCheckBox("Exclude this text from WordPress post excerpts")
        self.chk_no_excerpt.setToolTip(
            "Prevents this notice from appearing in automated WordPress theme excerpts or post list teasers."
        )
        opt_layout.addWidget(self.chk_no_snippet)
        opt_layout.addWidget(self.chk_no_excerpt)
        custom_layout.addLayout(opt_layout)

        save_def_row = QHBoxLayout()
        self.save_defaults_btn = QPushButton("Save Text & Options as Default")
        self.save_defaults_btn.setToolTip(
            "Save this custom text, placement, and exclusion options as the default for all future WordPress posts."
        )
        self.save_defaults_btn.clicked.connect(self.save_custom_text_defaults)
        self.saved_defaults_status = QLabel("")
        self.saved_defaults_status.setStyleSheet("color: #2ea44f; font-size: 11px;")
        save_def_row.addWidget(self.save_defaults_btn)
        save_def_row.addWidget(self.saved_defaults_status)
        save_def_row.addStretch()
        custom_layout.addLayout(save_def_row)

        layout.addWidget(custom_group)
        self.load_custom_text_settings()

        # Featured Image Group
        img_group = QGroupBox("Featured Image (Thumbnail)")
        img_layout = QVBoxLayout(img_group)

        self.img_button_group = QButtonGroup(self)
        self.rad_no_img = QRadioButton("No featured image")
        self.rad_frame_grab = QRadioButton("Grab frame from video at current position")
        self.rad_file_img = QRadioButton("Choose image file from computer...")

        self.img_button_group.addButton(self.rad_no_img)
        self.img_button_group.addButton(self.rad_frame_grab)
        self.img_button_group.addButton(self.rad_file_img)

        img_layout.addWidget(self.rad_no_img)
        img_layout.addWidget(self.rad_frame_grab)
        img_layout.addWidget(self.rad_file_img)

        # Preview preview & picker row
        picker_row = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.on_browse_image)
        self.browse_btn.setEnabled(False)
        picker_row.addWidget(self.browse_btn)
        picker_row.addWidget(self.file_path_label, stretch=1)
        img_layout.addLayout(picker_row)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedHeight(120)
        self.preview_label.setStyleSheet("background: #1e293b; border-radius: 6px; border: 1px solid #334155;")
        self.preview_label.setText("No Image Preview")
        img_layout.addWidget(self.preview_label)

        # Logic for radio toggles
        has_video = bool(getattr(self.app, "current_media_is_video", False) and getattr(self.app, "audio_file", None))
        self.rad_frame_grab.setEnabled(has_video)
        if has_video:
            self.rad_frame_grab.setChecked(True)
        else:
            self.rad_no_img.setChecked(True)

        self.rad_no_img.toggled.connect(self.on_image_mode_changed)
        self.rad_frame_grab.toggled.connect(self.on_image_mode_changed)
        self.rad_file_img.toggled.connect(self.on_image_mode_changed)

        layout.addWidget(img_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        btn_layout = QHBoxLayout()
        self.config_btn = QPushButton("Configure Credentials...")
        self.config_btn.clicked.connect(self.on_configure_credentials)
        btn_layout.addWidget(self.config_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.publish_btn = QPushButton("Publish Post")
        self.publish_btn.setStyleSheet("font-weight: bold; background-color: #2563eb; color: white; padding: 6px 16px;")
        self.publish_btn.clicked.connect(self.on_publish)
        btn_layout.addWidget(self.publish_btn)

        layout.addLayout(btn_layout)

    def load_custom_text_settings(self):
        """Load persistent custom text defaults from application settings."""
        saved_text = str(self.settings.value("wp_custom_text", "") or "")
        saved_pos = str(self.settings.value("wp_custom_text_pos", "top") or "top").lower()
        saved_no_snippet = str(self.settings.value("wp_custom_text_no_snippet", "true")).lower() in ("true", "1", "yes")
        saved_no_excerpt = str(self.settings.value("wp_custom_text_no_excerpt", "true")).lower() in ("true", "1", "yes")

        self.custom_text_edit.setPlainText(saved_text)
        if saved_pos == "bottom":
            self.rad_pos_bottom.setChecked(True)
        else:
            self.rad_pos_top.setChecked(True)
        self.chk_no_snippet.setChecked(saved_no_snippet)
        self.chk_no_excerpt.setChecked(saved_no_excerpt)

    def save_custom_text_defaults(self):
        """Save active custom text, placement, and exclusion settings as persistent defaults."""
        self.settings.setValue("wp_custom_text", self.custom_text_edit.toPlainText())
        self.settings.setValue("wp_custom_text_pos", "bottom" if self.rad_pos_bottom.isChecked() else "top")
        self.settings.setValue("wp_custom_text_no_snippet", self.chk_no_snippet.isChecked())
        self.settings.setValue("wp_custom_text_no_excerpt", self.chk_no_excerpt.isChecked())
        self.saved_defaults_status.setText("✓ Saved as default")

    def load_metadata(self):
        title = ""
        content = ""
        timestamp = 0.0

        if self.story:
            title = getattr(self.story, "title", "Untitled Story")
            start = getattr(self.story, "start", 0.0)
            end = getattr(self.story, "end", 0.0)
            timestamp = start
            if hasattr(self.app, "get_story_transcript"):
                content = self.app.get_story_transcript(self.story)
            elif hasattr(self.app, "transcript"):
                content = str(self.app.transcript)
        elif hasattr(self.app, "stories") and self.app.stories:
            sel_indices = getattr(self.app, "current_selected_story_indices", [])
            idx = sel_indices[0] if sel_indices else 0
            if 0 <= idx < len(self.app.stories):
                st = self.app.stories[idx]
                title = st.title
                timestamp = st.start
                if hasattr(self.app, "get_story_transcript"):
                    content = self.app.get_story_transcript(st)

        if not title and hasattr(self.app, "audio_file") and self.app.audio_file:
            title = Path(self.app.audio_file).stem

        self.title_edit.setText(title)
        # Explicit excerpt is generated cleanly from story content alone
        self.excerpt_edit.setText(generate_wp_excerpt(content))
        self.target_timestamp = timestamp

        if self.rad_frame_grab.isChecked():
            self.do_capture_frame()

    def do_capture_frame(self):
        media_file = getattr(self.app, "audio_file", None)
        if not media_file or not Path(media_file).exists():
            return
        out = os.path.join(self.temp_dir, "frame_grab.jpg")
        pos = getattr(self.app, "current_position", self.target_timestamp)
        if capture_video_frame(str(media_file), pos, out):
            self.captured_frame_path = out
            pix = QPixmap(out).scaled(200, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(pix)
            self.rad_frame_grab.setText(f"Grab frame from video (at {format_time(pos)})")

    def on_image_mode_changed(self):
        if self.rad_no_img.isChecked():
            self.browse_btn.setEnabled(False)
            self.preview_label.clear()
            self.preview_label.setText("No Featured Image")
        elif self.rad_frame_grab.isChecked():
            self.browse_btn.setEnabled(False)
            self.do_capture_frame()
        elif self.rad_file_img.isChecked():
            self.browse_btn.setEnabled(True)
            if self.custom_image_path and Path(self.custom_image_path).exists():
                pix = QPixmap(self.custom_image_path).scaled(200, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.preview_label.setPixmap(pix)
            else:
                self.preview_label.clear()
                self.preview_label.setText("Click Browse to select image file")

    def on_browse_image(self):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select Featured Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*.*)",
        )
        if fn:
            self.custom_image_path = fn
            self.file_path_label.setText(Path(fn).name)
            pix = QPixmap(fn).scaled(200, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(pix)

    def on_configure_credentials(self):
        from plugins.wordpress.client import WordPressSettingsDialog
        dlg = WordPressSettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            site_url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
            username = str(self.settings.value("wp_username", "") or "")
            self.conn_label.setText(f"<b>WordPress Site:</b> {site_url} ({username})")

    def on_publish(self):
        site_url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
        username = str(self.settings.value("wp_username", "") or "")
        password = _get_wp_password(username)

        if not site_url or not username or not password:
            QMessageBox.warning(
                self,
                "WordPress Not Configured",
                "Please configure your WordPress Site URL, Username, and Application Password first.",
            )
            self.on_configure_credentials()
            return

        client = WordPressClient(site_url, username, password)

        # Image to upload
        img_to_upload: Optional[str] = None
        if self.rad_frame_grab.isChecked() and self.captured_frame_path:
            img_to_upload = self.captured_frame_path
        elif self.rad_file_img.isChecked() and self.custom_image_path:
            img_to_upload = self.custom_image_path

        self.publish_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate

        title = self.title_edit.text().strip() or "Untitled Story"
        excerpt = self.excerpt_edit.toPlainText().strip()
        status = self.status_combo.currentData() or "draft"

        # Content
        content = ""
        if self.story and hasattr(self.app, "get_story_transcript"):
            content = self.app.get_story_transcript(self.story)
        elif hasattr(self.app, "transcript_view") and hasattr(self.app.transcript_view, "toPlainText"):
            content = self.app.transcript_view.toPlainText()

        # Format content with paragraphs
        if content:
            paras = [f"<p>{p.strip()}</p>" for p in content.split("\n\n") if p.strip()]
            formatted_content = "\n".join(paras) if paras else f"<p>{content}</p>"
        else:
            formatted_content = "<p></p>"

        # Build custom notice HTML (Header / Footer)
        custom_text = self.custom_text_edit.toPlainText().strip()
        custom_pos = "bottom" if self.rad_pos_bottom.isChecked() else "top"
        no_snippet = self.chk_no_snippet.isChecked()
        no_excerpt = self.chk_no_excerpt.isChecked()

        if custom_text:
            text_escaped = html.escape(custom_text).replace("\n\n", "</p><p>").replace("\n", "<br/>")
            inner_html = f"<p>{text_escaped}</p>"
            if no_snippet:
                custom_html = (
                    f'<!-- wp:paragraph -->\n'
                    f'<div data-nosnippet="true" class="rtvs-custom-notice" style="font-style: italic; opacity: 0.85; margin: 16px 0;">\n'
                    f'<!--googleoff: all-->\n'
                    f'{inner_html}\n'
                    f'<!--googleon: all-->\n'
                    f'</div>\n'
                    f'<!-- /wp:paragraph -->'
                )
            else:
                custom_html = (
                    f'<!-- wp:paragraph -->\n'
                    f'<div class="rtvs-custom-notice" style="font-style: italic; opacity: 0.85; margin: 16px 0;">\n'
                    f'{inner_html}\n'
                    f'</div>\n'
                    f'<!-- /wp:paragraph -->'
                )

            if custom_pos == "top":
                formatted_content = f"{custom_html}\n\n{formatted_content}"
            else:
                formatted_content = f"{formatted_content}\n\n{custom_html}"

        # If excerpt is empty, ensure it's generated from pure transcript if no_excerpt is checked
        if not excerpt:
            if no_excerpt:
                excerpt = generate_wp_excerpt(content)

        # Run background publish
        worker = WordPressPublishWorker(client, title, formatted_content, excerpt, status, img_to_upload)
        worker.finished_signal.connect(self.on_publish_finished)
        self._worker_thread = worker
        worker.start()

    def on_publish_finished(self, success: bool, msg: str, post_data: Any):
        self.publish_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if success:
            post_id = post_data.get("id") if isinstance(post_data, dict) else None
            post_link = post_data.get("link") if isinstance(post_data, dict) else ""
            
            # Save post ID in story metadata for backward & forward compatibility
            if self.story and post_id:
                if not hasattr(self.story, "metadata") or not isinstance(self.story.metadata, dict):
                    self.story.metadata = {}
                self.story.metadata["wp_post_id"] = post_id
                self.story.metadata["wp_post_link"] = post_link
                if hasattr(self.app, "save_project"):
                    self.app.save_project(force=False)

            info = f"Story successfully published to WordPress!\n\nPost ID: {post_id}\nStatus: {post_data.get('status', 'draft')}"
            if post_link:
                info += f"\nURL: {post_link}"
            QMessageBox.information(self, "Published Successfully", info)
            self.accept()
        else:
            QMessageBox.critical(self, "Publishing Error", f"Failed to publish to WordPress:\n\n{msg}")

    def closeEvent(self, event):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
        super().closeEvent(event)


class WordPressPublishWorker(QThread):
    finished_signal = Signal(bool, str, object)

    def __init__(self, client: WordPressClient, title: str, content: str, excerpt: str, status: str, image_path: Optional[str]):
        super().__init__()
        self.client = client
        self.title = title
        self.content = content
        self.excerpt = excerpt
        self.status = status
        self.image_path = image_path

    def run(self):
        try:
            featured_media_id = None
            if self.image_path and Path(self.image_path).exists():
                upload_res = self.client.upload_media(self.image_path)
                featured_media_id = upload_res.get("id")

            # Create post
            post_res = self.client.create_post(
                title=self.title,
                content=self.content,
                excerpt=self.excerpt,
                status=self.status,
            )

            # If featured media was uploaded, attach it
            if featured_media_id and post_res.get("id"):
                import requests
                post_id = post_res["id"]
                url = f"{self.client.api_base}/posts/{post_id}"
                requests.post(url, auth=self.client._get_auth(), json={"featured_media": featured_media_id}, timeout=20)
                post_res["featured_media"] = featured_media_id

            self.finished_signal.emit(True, "Success", post_res)
        except Exception as exc:
            self.finished_signal.emit(False, str(exc), None)


class WordPressStoryMetadataWidget(QGroupBox):
    """Inline metadata editor for WordPress publishing options directly in the main Story Editor."""

    def __init__(self, plugin: Plugin, parent: Any = None):
        super().__init__("WordPress Publishing Options", parent)
        self.plugin = plugin
        self.app = plugin.app
        self.current_story = None
        self._updating_ui = False
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # No story placeholder
        self.placeholder_lbl = QLabel("<i>Select a single story to configure WordPress metadata.</i>")
        self.placeholder_lbl.setStyleSheet("color: #64748b;")
        layout.addWidget(self.placeholder_lbl)

        # Content container
        self.form_container = QWidget()
        form_layout = QFormLayout(self.form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(6)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Draft", "draft")
        self.status_combo.addItem("Pending Review", "pending")
        self.status_combo.addItem("Publish Immediately", "publish")
        self.status_combo.addItem("Scheduled / Future", "future")
        self.status_combo.currentIndexChanged.connect(self._on_metadata_changed)
        form_layout.addRow("Status:", self.status_combo)

        # Excerpt with auto-generate button
        excerpt_box = QVBoxLayout()
        self.excerpt_edit = QTextEdit()
        self.excerpt_edit.setPlaceholderText("Custom post excerpt (optional)...")
        self.excerpt_edit.setMaximumHeight(60)
        self.excerpt_edit.textChanged.connect(self._on_metadata_changed)
        excerpt_box.addWidget(self.excerpt_edit)

        exc_btn_row = QHBoxLayout()
        self.gen_excerpt_btn = QPushButton("✨ Auto-Generate Excerpt")
        self.gen_excerpt_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.gen_excerpt_btn.clicked.connect(self._generate_excerpt)
        exc_btn_row.addWidget(self.gen_excerpt_btn)
        exc_btn_row.addStretch()
        excerpt_box.addLayout(exc_btn_row)
        form_layout.addRow("Excerpt:", excerpt_box)

        # Categories
        self.cats_edit = QLineEdit()
        self.cats_edit.setPlaceholderText("Category IDs (comma-separated, e.g. 1, 5)")
        self.cats_edit.textChanged.connect(self._on_metadata_changed)
        form_layout.addRow("Categories:", self.cats_edit)

        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags (comma-separated, e.g. news, radio)")
        self.tags_edit.textChanged.connect(self._on_metadata_changed)
        form_layout.addRow("Tags:", self.tags_edit)

        # Featured Image row
        img_row = QHBoxLayout()
        self.img_label = QLabel("None")
        self.img_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.browse_img_btn = QPushButton("Browse...")
        self.browse_img_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.browse_img_btn.clicked.connect(self._browse_image)
        self.grab_frame_btn = QPushButton("Grab Frame")
        self.grab_frame_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.grab_frame_btn.clicked.connect(self._grab_video_frame)
        self.clear_img_btn = QPushButton("Clear")
        self.clear_img_btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        self.clear_img_btn.clicked.connect(self._clear_image)

        img_row.addWidget(self.img_label)
        img_row.addStretch()
        img_row.addWidget(self.browse_img_btn)
        img_row.addWidget(self.grab_frame_btn)
        img_row.addWidget(self.clear_img_btn)
        form_layout.addRow("Featured Image:", img_row)

        layout.addWidget(self.form_container)
        self.form_container.setVisible(False)

    def set_story(self, story: Any):
        self.current_story = story
        if not story:
            self.placeholder_lbl.setVisible(True)
            self.form_container.setVisible(False)
            return

        self.placeholder_lbl.setVisible(False)
        self.form_container.setVisible(True)

        self._updating_ui = True
        try:
            wp_meta = getattr(story, "metadata", {}).get("wordpress", {}) if getattr(story, "metadata", None) else {}

            status = wp_meta.get("status", "draft")
            idx = self.status_combo.findData(status)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            else:
                self.status_combo.setCurrentIndex(0)

            self.excerpt_edit.setPlainText(wp_meta.get("excerpt", ""))

            cats = wp_meta.get("category_ids", [])
            self.cats_edit.setText(", ".join(str(c) for c in cats))

            tags = wp_meta.get("tags", [])
            self.tags_edit.setText(", ".join(str(t) for t in tags))

            feat_img = wp_meta.get("featured_image")
            if feat_img and Path(feat_img).exists():
                self.img_label.setText(Path(feat_img).name)
            else:
                self.img_label.setText("None")
        finally:
            self._updating_ui = False

    def _on_metadata_changed(self):
        if self._updating_ui or not self.current_story:
            return

        if not hasattr(self.current_story, "metadata") or self.current_story.metadata is None:
            self.current_story.metadata = {}

        wp_meta = self.current_story.metadata.setdefault("wordpress", {})
        wp_meta["status"] = self.status_combo.currentData()
        wp_meta["excerpt"] = self.excerpt_edit.toPlainText().strip()

        cat_ids = []
        for part in self.cats_edit.text().split(","):
            part = part.strip()
            if part.isdigit():
                cat_ids.append(int(part))
        wp_meta["category_ids"] = cat_ids
        wp_meta["tags"] = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]

        if hasattr(self.app, "set_unsaved_changes"):
            self.app.set_unsaved_changes(True)

    def _generate_excerpt(self):
        if not self.current_story:
            return
        st = self.current_story
        raw_text = ""
        if hasattr(self.app, "_get_transcript_text_slice"):
            raw_text = self.app._get_transcript_text_slice(st.start, st.end)
        elif hasattr(self.app, "transcript"):
            full_t = getattr(self.app, "transcript", []) or []
            words = []
            for seg in full_t:
                s_start = seg.get("start", 0.0)
                s_end = seg.get("end", 0.0)
                if (st.start is None or s_end >= st.start) and (st.end is None or s_start <= st.end):
                    words.append(seg.get("text", ""))
            raw_text = " ".join(words)

        exc = generate_wp_excerpt(raw_text, max_words=55)
        if exc:
            self.excerpt_edit.setPlainText(exc)

    def _browse_image(self):
        if not self.current_story:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Featured Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*.*)"
        )
        if path:
            wp_meta = self.current_story.metadata.setdefault("wordpress", {})
            wp_meta["featured_image"] = path
            wp_meta["featured_image_mode"] = "custom"
            self.img_label.setText(Path(path).name)
            if hasattr(self.app, "set_unsaved_changes"):
                self.app.set_unsaved_changes(True)

    def _grab_video_frame(self):
        if not self.current_story:
            return
        video_path = getattr(self.app, "audio_file", None)
        if not video_path or not getattr(self.app, "current_media_is_video", False):
            QMessageBox.information(self, "No Video", "Active media file is not a video.")
            return

        ts = float(self.current_story.start or 0.0)
        temp_dir = tempfile.mkdtemp(prefix="rtvs_wp_frame_")
        frame_path = os.path.join(temp_dir, f"frame_{int(ts)}.jpg")
        if capture_video_frame(str(video_path), ts, frame_path):
            wp_meta = self.current_story.metadata.setdefault("wordpress", {})
            wp_meta["featured_image"] = frame_path
            wp_meta["featured_image_mode"] = "video_frame"
            self.img_label.setText(Path(frame_path).name)
            if hasattr(self.app, "set_unsaved_changes"):
                self.app.set_unsaved_changes(True)
        else:
            QMessageBox.warning(self, "Capture Failed", "Failed to extract video frame using FFmpeg.")

    def _clear_image(self):
        if not self.current_story:
            return
        wp_meta = self.current_story.metadata.setdefault("wordpress", {})
        wp_meta["featured_image"] = None
        wp_meta["featured_image_mode"] = "none"
        self.img_label.setText("None")
        if hasattr(self.app, "set_unsaved_changes"):
            self.app.set_unsaved_changes(True)


class Plugin(BasePlugin):
    """WordPress Plugin implementation hooking into RTVS."""

    def __init__(self, manifest: PluginManifest, app: Any = None):
        super().__init__(manifest, app)
        self._story_widget: Optional[WordPressStoryMetadataWidget] = None

    def on_load(self) -> bool:
        return True

    def get_export_destinations(self) -> List[Any]:
        from plugins.wordpress.export_destination import WordPressExportDestination
        return [WordPressExportDestination(self)]

    def get_export_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("Publish to WordPress...", lambda: self.open_publish_dialog(parent=self.app)),
        ]

    def get_story_actions(self, story: Any = None) -> List[tuple[str, Callable]]:
        return [
            ("Export Story to WordPress / CMS...", lambda: self.open_publish_dialog(parent=self.app, story=story)),
        ]

    def create_story_metadata_widget(self, parent: Any = None) -> Any:
        self._story_widget = WordPressStoryMetadataWidget(self, parent=parent)
        return self._story_widget

    def on_story_selected(self, story: Any = None) -> None:
        if self._story_widget:
            self._story_widget.set_story(story)

    def get_preferences_widget(self, parent: Any = None) -> Any:
        from plugins.wordpress.client import WordPressPreferencesPage
        return WordPressPreferencesPage(parent=parent, app=self.app)

    def open_publish_dialog(self, parent: Any = None, story: Any = None):
        dlg = WordPressPublishDialog(self, parent=parent or self.app, story=story)
        dlg.exec()

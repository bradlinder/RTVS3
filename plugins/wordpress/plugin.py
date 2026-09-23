"""WordPress Publisher Plugin for Radio & TV Segmenter.

Allows direct publishing of audio/video stories to WordPress with
custom excerpt, author assignment, categories, and custom featured image
(local file or video frame grab at playhead/story timestamp).
"""
from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QScrollArea,
    QTextEdit,
    QFileDialog,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QProgressBar,
    QWidget,
    QSlider,
    QFrame,
)

from prs_shared import (
    INTERNAL_APP_ID,
    PROJECT_VERSION,
    QSettings,
    CollapsibleSection,
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
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
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
    """Clean, compact WordPress metadata launcher & inspector embedded in the Stories sidebar."""

    def __init__(self, plugin: Any, parent: Any = None):
        super().__init__("WordPress Post Configuration", parent)
        self.plugin = plugin
        self.app = plugin.app
        self.current_story = None
        self.current_target_mode = "full"  # "full" or "story"
        self._current_story_idx = -1
        self._updating_ui = False
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

        self.setup_ui()
        self.refresh_targets_dropdown()
        self._load_current_target_metadata()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Primary Action Button: "WordPress Post Settings..."
        self.open_dialog_btn = QPushButton("🗗 WordPress Post Settings...")
        self.open_dialog_btn.setObjectName("wp_open_post_settings_btn")
        self.open_dialog_btn.setToolTip("Open the multi-pane WordPress post editor to configure titles, excerpts, authors, categories, and featured images for all stories and the full episode.")
        self.open_dialog_btn.setStyleSheet("""
            QPushButton#wp_open_post_settings_btn {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #0369a1;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#wp_open_post_settings_btn:hover {
                background-color: #0ea5e9;
                border-color: #38bdf8;
            }
            QPushButton#wp_open_post_settings_btn:pressed {
                background-color: #0369a1;
            }
        """)
        self.open_dialog_btn.clicked.connect(self._open_post_settings_dialog)
        layout.addWidget(self.open_dialog_btn)

        # Target Selector row
        target_row = QHBoxLayout()
        target_row.setSpacing(6)
        target_lbl = QLabel("Target:")
        target_lbl.setStyleSheet("font-weight: 500; font-size: 11px;")
        target_row.addWidget(target_lbl)

        self.target_combo = QComboBox()
        self.target_combo.setToolTip("Inspect configured metadata for the Full Episode or a specific Story")
        self.target_combo.currentIndexChanged.connect(self._on_target_changed)
        target_row.addWidget(self.target_combo, 1)
        layout.addLayout(target_row)

        # Summary Info Card
        self.summary_box = QFrame()
        self.summary_box.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QLabel {
                font-size: 11px;
            }
        """)
        summary_layout = QVBoxLayout(self.summary_box)
        summary_layout.setContentsMargins(4, 4, 4, 4)
        summary_layout.setSpacing(3)

        self.title_lbl = QLabel("<b>Title:</b> Full Episode")
        self.title_lbl.setWordWrap(True)
        summary_layout.addWidget(self.title_lbl)

        self.authors_lbl = QLabel("<b>Authors:</b> Default / None")
        summary_layout.addWidget(self.authors_lbl)

        self.cats_lbl = QLabel("<b>Categories:</b> Default / None")
        summary_layout.addWidget(self.cats_lbl)

        self.thumb_lbl = QLabel("<b>Featured Image:</b> None")
        summary_layout.addWidget(self.thumb_lbl)

        self.status_lbl = QLabel("<b>Status:</b> Draft")
        summary_layout.addWidget(self.status_lbl)

        layout.addWidget(self.summary_box)

        # Secondary Quick Actions
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        self.auto_excerpt_btn = QPushButton("✨ Auto-Excerpt")
        self.auto_excerpt_btn.setToolTip("Auto-generate a 55-word excerpt from this story's transcript directly")
        self.auto_excerpt_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.auto_excerpt_btn.clicked.connect(self._on_quick_auto_excerpt)
        actions_row.addWidget(self.auto_excerpt_btn)

        self.refresh_btn = QPushButton("⟳ Refresh Taxonomy")
        self.refresh_btn.setToolTip("Fetch fresh authors and categories from the connected WordPress site")
        self.refresh_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.refresh_btn.clicked.connect(self._on_refresh_taxonomy)
        actions_row.addWidget(self.refresh_btn)

        layout.addLayout(actions_row)

    def refresh_targets_dropdown(self):
        """Populate target_combo with Full Episode and all current project stories."""
        self.target_combo.blockSignals(True)
        prev_data = self.target_combo.currentData()
        self.target_combo.clear()

        self.target_combo.addItem("🎬 Full Episode", "full")
        stories = getattr(self.app, "stories", []) or []
        for idx, st in enumerate(stories):
            title = st.title if getattr(st, "title", None) else f"Story {idx + 1}"
            self.target_combo.addItem(f"📖 Story {idx + 1}: {title}", f"story_{idx}")

        # Restore selection if possible
        found_idx = -1
        if prev_data:
            for i in range(self.target_combo.count()):
                if self.target_combo.itemData(i) == prev_data:
                    found_idx = i
                    break
        if found_idx >= 0:
            self.target_combo.setCurrentIndex(found_idx)
        else:
            self.target_combo.setCurrentIndex(0)
        self.target_combo.blockSignals(False)

    def _on_target_changed(self, index: int):
        data = self.target_combo.itemData(index)
        if data == "full":
            self.current_target_mode = "full"
            self.current_story = None
            self._current_story_idx = -1
        elif isinstance(data, str) and data.startswith("story_"):
            try:
                s_idx = int(data.split("_")[1])
                stories = getattr(self.app, "stories", []) or []
                if 0 <= s_idx < len(stories):
                    self.current_target_mode = "story"
                    self.current_story = stories[s_idx]
                    self._current_story_idx = s_idx
            except Exception:
                self.current_target_mode = "full"
                self.current_story = None
                self._current_story_idx = -1
        self._load_current_target_metadata()

    def set_story(self, story: Any):
        """Called when user selects a story in the story list or timeline."""
        self.refresh_targets_dropdown()
        if story:
            stories = getattr(self.app, "stories", []) or []
            if story in stories:
                idx = stories.index(story)
                target_key = f"story_{idx}"
                for i in range(self.target_combo.count()):
                    if self.target_combo.itemData(i) == target_key:
                        self.target_combo.setCurrentIndex(i)
                        return
        self._load_current_target_metadata()

    def _get_active_wp_metadata(self) -> dict:
        if self.current_target_mode == "story" and self.current_story:
            if not hasattr(self.current_story, "metadata") or self.current_story.metadata is None:
                self.current_story.metadata = {}
            return self.current_story.metadata.setdefault("wordpress", {})
        else:
            proj_meta = getattr(self.app, "project_metadata", None)
            if not isinstance(proj_meta, dict):
                proj_meta = {}
                self.app.project_metadata = proj_meta
            return proj_meta.setdefault("wordpress", {})

    def _load_current_target_metadata(self):
        wp_meta = self._get_active_wp_metadata()

        # Title
        if self.current_target_mode == "story" and self.current_story:
            title = wp_meta.get("title") or getattr(self.current_story, "title", "") or f"Story {self._current_story_idx + 1}"
        else:
            audio_file = getattr(self.app, "audio_file", None)
            default_title = Path(audio_file).stem if audio_file else "Full Episode"
            title = wp_meta.get("title") or default_title
        self.title_lbl.setText(f"<b>Title:</b> {html.escape(title)}")

        # Authors
        raw_auth = self.settings.value("wp_cached_authors", "")
        auth_data = json.loads(raw_auth) if raw_auth else []
        auth_ids = set(wp_meta.get("author_ids") or [])
        term_ids = set(wp_meta.get("author_term_ids") or [])
        matched_authors = []
        for a in auth_data:
            if isinstance(a, dict):
                if not a.get("is_guest") and (a.get("user_id") in auth_ids or a.get("id") in auth_ids):
                    matched_authors.append(a.get("name", "User"))
                elif a.get("is_guest") and (a.get("term_id") in term_ids or a.get("id") in term_ids):
                    matched_authors.append(a.get("name", "Guest"))
        if not matched_authors and self.current_target_mode == "story" and self.current_story:
            st_auth = self.current_story.metadata.get("author")
            if st_auth:
                matched_authors.append(st_auth)
        auth_text = ", ".join(matched_authors) if matched_authors else "Default / None"
        self.authors_lbl.setText(f"<b>Authors:</b> {html.escape(auth_text)}")

        # Categories
        raw_cat = self.settings.value("wp_cached_categories", "")
        cat_data = json.loads(raw_cat) if raw_cat else []
        cat_ids = set(wp_meta.get("category_ids") or [])
        matched_cats = [c.get("name") for c in cat_data if isinstance(c, dict) and c.get("id") in cat_ids]
        cat_text = ", ".join(matched_cats) if matched_cats else "Default / None"
        self.cats_lbl.setText(f"<b>Categories:</b> {html.escape(cat_text)}")

        # Featured Image
        mode = wp_meta.get("featured_image_mode", "none")
        img = wp_meta.get("featured_image")
        pos = wp_meta.get("frame_pos")
        if mode == "video_frame":
            time_str = format_time(pos, include_millis=True) if pos is not None else ""
            self.thumb_lbl.setText(f"<b>Featured Image:</b> Video Frame @ {time_str}")
        elif mode == "file" and img:
            self.thumb_lbl.setText(f"<b>Featured Image:</b> File ({Path(img).name})")
        else:
            self.thumb_lbl.setText("<b>Featured Image:</b> None")

        # Status
        status = wp_meta.get("status", "draft").capitalize()
        self.status_lbl.setText(f"<b>Status:</b> {status}")

    def _open_post_settings_dialog(self):
        from plugins.wordpress.export_destination import WordPressPostMetadataDialog
        target_idx = self._current_story_idx if self.current_target_mode == "story" else None
        dlg = WordPressPostMetadataDialog(self, self.app, target_story_index=target_idx)
        if dlg.exec():
            self.refresh_targets_dropdown()
            self._load_current_target_metadata()

    def _on_quick_auto_excerpt(self):
        if self.current_target_mode == "story" and self.current_story:
            raw_text = self.app._get_transcript_text_slice(self.current_story.start, self.current_story.end) if hasattr(self.app, "_get_transcript_text_slice") else ""
            exc = generate_wp_excerpt(raw_text, 55)
            if not hasattr(self.current_story, "metadata") or self.current_story.metadata is None:
                self.current_story.metadata = {}
            self.current_story.metadata["excerpt"] = exc
            wp_meta = self.current_story.metadata.setdefault("wordpress", {})
            wp_meta["excerpt"] = exc
            if hasattr(self.app, "excerpt_edit") and self.app.excerpt_edit:
                if hasattr(self.app.excerpt_edit, "setText"):
                    self.app.excerpt_edit.setText(exc)
                elif hasattr(self.app.excerpt_edit, "setPlainText"):
                    self.app.excerpt_edit.setPlainText(exc)
            if hasattr(self.app, "mark_project_dirty"):
                self.app.mark_project_dirty("Generate Auto-Excerpt")
            elif hasattr(self.app, "set_unsaved_changes"):
                self.app.set_unsaved_changes(True)
            QMessageBox.information(self, "Auto-Excerpt", "Generated 55-word excerpt for current story from transcript.")
        else:
            raw_text = self.app._get_transcript_text_slice(None, None) if hasattr(self.app, "_get_transcript_text_slice") else ""
            exc = generate_wp_excerpt(raw_text, 55)
            wp_meta = self._get_active_wp_metadata()
            wp_meta["excerpt"] = exc
            if hasattr(self.app, "set_unsaved_changes"):
                self.app.set_unsaved_changes(True)
            QMessageBox.information(self, "Auto-Excerpt", "Generated 55-word excerpt for full episode from transcript.")

    def _on_refresh_taxonomy(self):
        try:
            from plugins.wordpress.client import get_wp_client
            client = get_wp_client()
            if not client.is_configured():
                QMessageBox.information(self, "WordPress Not Configured", "Please configure WordPress settings first under Settings > Manage Plugins.")
                return
            authors = client.get_authors()
            cats = client.get_categories()
            self.settings.setValue("wp_cached_authors", json.dumps(authors))
            self.settings.setValue("wp_cached_categories", json.dumps(cats))
            self._load_current_target_metadata()
            QMessageBox.information(self, "Refreshed", f"Successfully loaded {len(authors)} authors and {len(cats)} categories from WordPress.")
        except Exception as exc:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh from WordPress: {exc}")


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
            ("WordPress Post & Story Settings...", lambda: self.open_post_metadata_dialog(parent=self.app, story=story)),
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

    def open_post_metadata_dialog(self, parent: Any = None, story: Any = None):
        from plugins.wordpress.export_destination import WordPressPostMetadataDialog
        target_idx = None
        if story and hasattr(self.app, "stories"):
            try:
                target_idx = self.app.stories.index(story)
            except Exception:
                target_idx = None
        dlg = WordPressPostMetadataDialog(parent=parent or self.app, main_window=self.app, target_story_index=target_idx)
        dlg.exec()
        if self._story_widget:
            self._story_widget.refresh_targets_dropdown()
            self._story_widget._load_current_target_metadata()


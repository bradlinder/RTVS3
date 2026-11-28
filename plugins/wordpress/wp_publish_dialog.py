"""WordPress single-story publish dialog with featured image and notice options."""
from __future__ import annotations

import html
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from prs_shared import INTERNAL_APP_ID, QSettings, format_time
from plugins.wordpress.client import (
    WordPressClient,
    WordPressSettingsDialog,
    _get_wp_password,
    generate_wp_excerpt,
    is_wp_auth_error,
)
from plugins.wordpress.wp_post_builder import capture_video_frame
from plugins.wordpress.wp_workers import WordPressPublishWorker


class WordPressPublishDialog(QDialog):
    """Publish a story or project to WordPress with featured image selection."""

    def __init__(self, plugin: Any, parent: Any = None, story: Any = None):
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
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setup_ui()
        self.load_metadata()

    def _resolve_spellcheck_context(self):
        dlg_dict = getattr(self, "__dict__", {})
        main_win = dlg_dict.get("main_window") or dlg_dict.get("app") or self.parent()
        return main_win

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
        self.status_combo.setEnabled(False)
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

        try:
            from spellcheck_helper import OfflineSpellChecker
            from spellcheck_widgets import attach_spellcheck

            mw = self._resolve_spellcheck_context()
            sp = OfflineSpellChecker(main_window=mw)
            self._spellchecker = sp
            for field in (self.title_edit, self.excerpt_edit, self.custom_text_edit):
                attach_spellcheck(field, main_window=mw, spellchecker=sp)
        except Exception:
            logging.getLogger(__name__).warning("Failed to attach WordPress publish spellcheckers", exc_info=True)

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

        # Preview & picker row
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

        src_meta = getattr(self.story, "metadata", None) if self.story else getattr(self.app, "project_metadata", None)
        wp_img_meta = src_meta.get("wordpress", {}) if isinstance(src_meta, dict) and isinstance(src_meta.get("wordpress"), dict) else {}

        self.img_meta_widget = QWidget()
        img_meta_form = QFormLayout(self.img_meta_widget)
        img_meta_form.setContentsMargins(0, 4, 0, 0)
        img_meta_form.setSpacing(6)
        self.img_caption_edit = QLineEdit()
        self.img_caption_edit.setPlaceholderText("Optional WordPress Media Library caption (e.g. photo credit)")
        self.img_caption_edit.setText(str(wp_img_meta.get("featured_image_caption") or ""))
        img_meta_form.addRow("Caption:", self.img_caption_edit)
        self.img_alt_edit = QLineEdit()
        self.img_alt_edit.setPlaceholderText("Optional accessibility alt text describing the image")
        self.img_alt_edit.setText(str(wp_img_meta.get("featured_image_alt_text") or ""))
        img_meta_form.addRow("Alt Text:", self.img_alt_edit)
        img_layout.addWidget(self.img_meta_widget)

        try:
            from spellcheck_helper import OfflineSpellChecker
            from spellcheck_widgets import attach_spellcheck

            mw = self._resolve_spellcheck_context()
            sp = getattr(self, "_spellchecker", None) or OfflineSpellChecker(main_window=mw)
            for img_field in (self.img_caption_edit, self.img_alt_edit):
                attach_spellcheck(img_field, main_window=mw, spellchecker=sp)
        except Exception:
            logging.getLogger(__name__).warning("Failed to attach WordPress image metadata spellcheckers", exc_info=True)

        # Logic for radio toggles
        has_video = bool(getattr(self.app, "current_media_is_video", False) and getattr(self.app, "audio_file", None))
        self.rad_frame_grab.setEnabled(has_video)
        if has_video:
            self.rad_frame_grab.setChecked(True)
        else:
            self.rad_no_img.setChecked(True)
        self.img_meta_widget.setVisible(not self.rad_no_img.isChecked())

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
        self.saved_defaults_status.setText("Saved as default")

    def load_metadata(self):
        title = ""
        content = ""
        timestamp = 0.0

        if self.story:
            title = getattr(self.story, "title", "Untitled Story")
            start = getattr(self.story, "start", 0.0)
            end = getattr(self.story, "end", 0.0)
            timestamp = start
            if hasattr(self.app, "_get_transcript_text_slice"):
                content = self.app._get_transcript_text_slice(start, end)
            elif hasattr(self.app, "get_story_transcript"):
                content = self.app.get_story_transcript(self.story)
            elif hasattr(self.app, "transcript"):
                raw_t = self.app.transcript
                if isinstance(raw_t, dict):
                    content = raw_t.get("text", "")
                elif isinstance(raw_t, str):
                    content = raw_t
        elif hasattr(self.app, "stories") and self.app.stories:
            sel_indices = getattr(self.app, "current_selected_story_indices", [])
            idx = sel_indices[0] if sel_indices else 0
            if 0 <= idx < len(self.app.stories):
                st = self.app.stories[idx]
                title = st.title
                timestamp = st.start
                if hasattr(self.app, "_get_transcript_text_slice"):
                    content = self.app._get_transcript_text_slice(st.start, st.end)
                elif hasattr(self.app, "get_story_transcript"):
                    content = self.app.get_story_transcript(st)

        if not title and hasattr(self.app, "audio_file") and self.app.audio_file:
            title = Path(self.app.audio_file).stem

        self.title_edit.setText(title)
        # Explicit excerpt is generated cleanly from story content alone
        self.excerpt_edit.setText(generate_wp_excerpt(content))
        self.target_timestamp = timestamp

        if self.rad_frame_grab.isChecked():
            self.do_capture_frame()

    def _set_preview_image(self, image_path: str):
        pix = QPixmap(str(image_path))
        if pix.isNull():
            self.preview_label.clear()
            self.preview_label.setText("Preview unavailable")
        else:
            self.preview_label.setPixmap(
                pix.scaled(200, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )

    def do_capture_frame(self):
        media_file = getattr(self.app, "audio_file", None)
        if not media_file or not Path(media_file).exists():
            return
        out = os.path.join(self.temp_dir, "frame_grab.jpg")
        pos = getattr(self.app, "current_position", self.target_timestamp)
        if capture_video_frame(str(media_file), pos, out):
            self.captured_frame_path = out
            self._set_preview_image(out)
            self.rad_frame_grab.setText(f"Grab frame from video (at {format_time(pos)})")

    def on_image_mode_changed(self):
        if hasattr(self, "img_meta_widget"):
            self.img_meta_widget.setVisible(not self.rad_no_img.isChecked())
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
                self._set_preview_image(self.custom_image_path)
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
            self._set_preview_image(fn)

    def on_configure_credentials(self):
        dlg = WordPressSettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            site_url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
            username = str(self.settings.value("wp_username", "") or "")
            self.conn_label.setText(f"<b>WordPress Site:</b> {site_url} ({username})")

    def on_publish(self):
        site_url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
        username = str(self.settings.value("wp_username", "") or "")
        password = _get_wp_password(username)

        if not site_url or not username or not password or site_url in ("https://example.com", "http://example.com", "example.com"):
            reply = QMessageBox.question(
                self,
                "WordPress Credentials Required",
                "WordPress site connection settings are missing or incomplete.\n\nWould you like to enter your website URL and login details now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
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
        if self.story:
            if hasattr(self.app, "_get_transcript_text_slice"):
                content = self.app._get_transcript_text_slice(getattr(self.story, "start", None), getattr(self.story, "end", None))
            elif hasattr(self.app, "get_story_transcript"):
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
        if not excerpt and no_excerpt:
            excerpt = generate_wp_excerpt(content)

        # Run background publish
        img_caption = self.img_caption_edit.text().strip() if hasattr(self, "img_caption_edit") else ""
        img_alt = self.img_alt_edit.text().strip() if hasattr(self, "img_alt_edit") else ""
        worker = WordPressPublishWorker(
            client, title, formatted_content, excerpt, status, img_to_upload,
            image_caption=img_caption, image_alt_text=img_alt,
        )
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
            if is_wp_auth_error(msg):
                reply = QMessageBox.question(
                    self,
                    "WordPress Credentials Required",
                    f"Failed to publish to WordPress due to invalid or expired credentials:\n\n{msg}\n\nWould you like to enter or correct your website URL and login details now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.on_configure_credentials()
            else:
                QMessageBox.critical(self, "Publishing Error", f"Failed to publish to WordPress:\n\n{msg}")

    def _cleanup_workers(self):
        worker = getattr(self, "_worker_thread", None)
        temp_dir = getattr(self, "temp_dir", None)
        self._worker_thread = None
        if worker is not None:
            sig = getattr(worker, "finished_signal", None)
            if sig is not None:
                try:
                    sig.disconnect(self.on_publish_finished)
                except Exception:
                    pass
            try:
                is_running_fn = getattr(worker, "isRunning", None)
                if callable(is_running_fn) and is_running_fn():
                    if hasattr(worker, "requestInterruption"):
                        worker.requestInterruption()
                    worker.setParent(None)
                    _DETACHED_WP_PUBLISH_WORKERS.add(worker)
                    worker.finished.connect(lambda *_, w=worker: _DETACHED_WP_PUBLISH_WORKERS.discard(w))
                    if temp_dir:
                        worker.finished.connect(lambda *_, td=temp_dir: shutil.rmtree(td, ignore_errors=True))
                    worker.finished.connect(worker.deleteLater)
                    return
            except RuntimeError:
                pass
        if temp_dir:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def reject(self):
        self._cleanup_workers()
        super().reject()

    def closeEvent(self, event):
        self._cleanup_workers()
        super().closeEvent(event)


_DETACHED_WP_PUBLISH_WORKERS: set = set()


__all__ = ["WordPressPublishDialog"]

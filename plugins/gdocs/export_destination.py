"""Google Docs Export Destination for UnifiedExportDialog."""
from __future__ import annotations

import threading
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    # Minimal fallback for headless or test environments
    class QWidget: pass  # type: ignore
    class QDialog: pass  # type: ignore

try:
    from prs_shared import INTERNAL_APP_ID, safe_filename
except Exception:
    INTERNAL_APP_ID = "com.bradlinder.radiotvsegmenter"
    def safe_filename(name: str) -> str:
        import re
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()
from plugins.base import ExportDestination
from plugins.gdocs.formatter import (
    GoogleDocsSerializer,
    create_google_doc,
    batch_update_google_doc,
)
from plugins.gdocs.comments import attach_editorial_notes_as_comments


class GoogleDocsExportDestination(ExportDestination):
    """ExportDestination implementation for Google Docs & Drive."""

    def __init__(self, plugin: Any):
        super().__init__(
            id="gdocs",
            title="Google Docs & Drive",
            description="Exports formatted transcripts, story chapters, speaker turns, and margin notes to Google Docs.",
            button_label="Export to Google Docs...",
        )
        self.plugin = plugin
        self.auth_manager = plugin.auth_manager
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.widget: Optional[QWidget] = None
        self.main_window: Any = None

    def create_widget(self, parent: Any, main_window: Any) -> Any:
        self.main_window = main_window
        self.widget = QWidget(parent)
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 1. Google Account Connection Card
        auth_group = QGroupBox("Google Account Connection")
        a_layout = QVBoxLayout(auth_group)

        self.account_status_lbl = QLabel()
        self._update_auth_status_label()
        a_layout.addWidget(self.account_status_lbl)

        btn_row = QHBoxLayout()
        self.auth_btn = QPushButton("Sign in with Google...")
        self.auth_btn.clicked.connect(self._on_auth_button_clicked)
        btn_row.addWidget(self.auth_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        btn_row.addWidget(self.disconnect_btn)
        btn_row.addStretch()
        a_layout.addLayout(btn_row)
        layout.addWidget(auth_group)

        # 2. Document & Drive Destination Options
        doc_group = QGroupBox("Document & Drive Settings")
        form = QFormLayout(doc_group)
        form.setSpacing(10)

        self.title_input = QLineEdit()
        default_title = "Broadcast Transcript"
        if hasattr(main_window, "media_path") and main_window.media_path:
            import os
            base = os.path.splitext(os.path.basename(main_window.media_path))[0]
            default_title = f"{base} — Transcript"
        self.title_input.setText(default_title)
        form.addRow("Document Title:", self.title_input)

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Optional (Root 'My Drive' if blank)")
        self.folder_input.setText(str(self.settings.value("gdocs_last_folder_id", "") or ""))
        form.addRow("Drive Folder ID:", self.folder_input)

        layout.addWidget(doc_group)

        # 3. Formatting & Content Options
        fmt_group = QGroupBox("Formatting & Content Options")
        f_layout = QVBoxLayout(fmt_group)

        self.cb_speakers = QCheckBox("Include Speaker Labels (ALICE, BOB)")
        self.cb_speakers.setChecked(self.settings.value("gdocs_opt_speakers", True, type=bool))
        f_layout.addWidget(self.cb_speakers)

        self.cb_timestamps = QCheckBox("Include Section & Speaker Timestamps (00:01:23)")
        self.cb_timestamps.setChecked(self.settings.value("gdocs_opt_timestamps", True, type=bool))
        f_layout.addWidget(self.cb_timestamps)

        self.cb_word_timestamps = QCheckBox("Include Inline Word Timestamps (word [00:12.3])")
        self.cb_word_timestamps.setChecked(self.settings.value("gdocs_opt_word_timestamps", False, type=bool))
        f_layout.addWidget(self.cb_word_timestamps)

        self.cb_comments = QCheckBox("Anchor Editorial Story Notes as Drive Margin Comments")
        self.cb_comments.setChecked(self.settings.value("gdocs_opt_comments", True, type=bool))
        f_layout.addWidget(self.cb_comments)

        self.cb_browser = QCheckBox("Open Google Doc in Web Browser Upon Completion")
        self.cb_browser.setChecked(self.settings.value("gdocs_opt_browser", True, type=bool))
        f_layout.addWidget(self.cb_browser)

        layout.addWidget(fmt_group)
        layout.addStretch()

        self._update_auth_ui_state()
        return self.widget

    def _update_auth_status_label(self):
        if not hasattr(self, "account_status_lbl") or not self.account_status_lbl:
            return
        if self.auth_manager.is_authenticated():
            email = self.auth_manager.get_user_email() or "Google Account"
            self.account_status_lbl.setText(f"✓ <b>Connected:</b> {email}")
            self.account_status_lbl.setStyleSheet("color: #16a34a; font-size: 12px;")
        else:
            self.account_status_lbl.setText("⚠ <b>Not connected</b> — Sign in to export documents to Google Drive.")
            self.account_status_lbl.setStyleSheet("color: #dc2626; font-size: 12px;")

    def _update_auth_ui_state(self):
        self._update_auth_status_label()
        is_auth = self.auth_manager.is_authenticated()
        if hasattr(self, "auth_btn"):
            self.auth_btn.setVisible(not is_auth)
        if hasattr(self, "disconnect_btn"):
            self.disconnect_btn.setVisible(is_auth)

    def _on_auth_button_clicked(self):
        ok, msg = self.auth_manager.start_loopback_auth()
        if ok:
            QMessageBox.information(self.widget, "Connected", f"Successfully linked account: {msg}")
        else:
            QMessageBox.critical(self.widget, "Authentication Failed", f"Could not link Google account:\n{msg}")
        self._update_auth_ui_state()

    def _on_disconnect_clicked(self):
        self.auth_manager.logout()
        QMessageBox.information(self.widget, "Disconnected", "Google Account credentials cleared.")
        self._update_auth_ui_state()

    def validate(self) -> Tuple[bool, str]:
        if not self.auth_manager.is_authenticated():
            return False, "Please sign in with your Google Account before exporting to Google Docs."
        if hasattr(self, "title_input") and not self.title_input.text().strip():
            return False, "Please specify a document title."
        return True, ""

    def get_export_data(self) -> Dict[str, Any]:
        title = self.title_input.text().strip() if hasattr(self, "title_input") else "Transcript"
        folder_id = self.folder_input.text().strip() if hasattr(self, "folder_input") else ""

        # Persist preferences
        self.settings.setValue("gdocs_last_folder_id", folder_id)
        if hasattr(self, "cb_speakers"):
            self.settings.setValue("gdocs_opt_speakers", self.cb_speakers.isChecked())
            self.settings.setValue("gdocs_opt_timestamps", self.cb_timestamps.isChecked())
            self.settings.setValue("gdocs_opt_word_timestamps", self.cb_word_timestamps.isChecked())
            self.settings.setValue("gdocs_opt_comments", self.cb_comments.isChecked())
            self.settings.setValue("gdocs_opt_browser", self.cb_browser.isChecked())
        self.settings.sync()

        return {
            "title": title,
            "folder_id": folder_id,
            "include_speakers": self.cb_speakers.isChecked() if hasattr(self, "cb_speakers") else True,
            "include_timestamps": self.cb_timestamps.isChecked() if hasattr(self, "cb_timestamps") else True,
            "include_word_timestamps": self.cb_word_timestamps.isChecked() if hasattr(self, "cb_word_timestamps") else False,
            "anchor_comments": self.cb_comments.isChecked() if hasattr(self, "cb_comments") else True,
            "open_browser": self.cb_browser.isChecked() if hasattr(self, "cb_browser") else True,
        }

    def execute_export(self, main_window: Any, export_data: Dict[str, Any], progress_dialog: Any = None) -> bool:
        token = self.auth_manager.get_valid_access_token()
        if not token:
            if progress_dialog:
                progress_dialog.close()
            QMessageBox.critical(main_window, "Authentication Error", "Unable to obtain a valid Google access token.")
            return False

        title = export_data.get("title", "Broadcast Transcript")
        folder_id = export_data.get("folder_id", "")
        include_speakers = export_data.get("include_speakers", True)
        include_timestamps = export_data.get("include_timestamps", True)
        include_word_timestamps = export_data.get("include_word_timestamps", False)
        anchor_comments = export_data.get("anchor_comments", True)
        open_browser = export_data.get("open_browser", True)

        # Retrieve stories and transcript
        stories = getattr(main_window, "stories", [])
        transcript_data = getattr(main_window, "transcript", {}) or {}
        segments = transcript_data.get("segments", [])

        meta = {
            "media_filename": getattr(main_window, "media_path", ""),
            "duration": getattr(main_window, "duration", 0.0),
            "language": transcript_data.get("language", ""),
        }

        # 1. Serialize Document Payload
        serializer = GoogleDocsSerializer()
        _, batch_requests, comment_anchors = serializer.serialize_document(
            document_title=title,
            stories=stories,
            transcript_segments=segments,
            project_metadata=meta,
            include_speakers=include_speakers,
            include_timestamps=include_timestamps,
            include_word_timestamps=include_word_timestamps,
        )

        # 2. Create Document via Docs API
        ok, doc_id, _ = create_google_doc(token, title, folder_id=folder_id)
        if not ok:
            if progress_dialog:
                progress_dialog.close()
            QMessageBox.critical(main_window, "Export Failed", f"Failed to create Google Doc:\n{doc_id}")
            return False

        # 3. Apply Batch Update Styling
        ok_batch, batch_err = batch_update_google_doc(token, doc_id, batch_requests)
        if not ok_batch:
            print(f"[GDOCS EXPORT] Warning on batch update: {batch_err}")

        # 4. Attach Margin Comments if requested
        if anchor_comments and comment_anchors:
            attach_editorial_notes_as_comments(token, doc_id, comment_anchors)

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        if progress_dialog:
            progress_dialog.close()

        if open_browser:
            webbrowser.open(doc_url)

        QMessageBox.information(
            main_window,
            "Export Completed",
            f"Successfully exported transcript to Google Docs!\n\nDocument ID: {doc_id}\n\nOpened in your web browser.",
        )
        return True

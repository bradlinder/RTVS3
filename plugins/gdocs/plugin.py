"""Google Docs & Drive Exporter Plugin implementation for Radio & TV Segmenter."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QGroupBox,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QFormLayout,
        QMessageBox,
        QFileDialog,
        QDialog,
        QWidget,
    )
except ImportError:
    class QWidget: pass  # type: ignore
    class QGroupBox: pass  # type: ignore
    class QDialog: pass  # type: ignore

from plugins.base import BasePlugin, PluginManifest
from plugins.gdocs.auth import GoogleDocsAuthManager, parse_google_credentials_json, DEFAULT_CLIENT_ID
from plugins.gdocs.export_destination import GoogleDocsExportDestination
from plugins.gdocs.review import GoogleDocsReviewDialog


class Plugin(BasePlugin):
    """Google Docs & Drive Exporter plugin connecting RTVS to Google Docs REST API."""

    def __init__(self, manifest: PluginManifest, app: Any = None):
        super().__init__(manifest, app)
        self.auth_manager = GoogleDocsAuthManager()

    def on_load(self) -> bool:
        return True

    def get_export_destinations(self) -> List[Any]:
        return [GoogleDocsExportDestination(self)]

    def get_export_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("Export to Google Docs...", self.open_export_dialog),
        ]

    def get_tools_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("Google Docs: Review & Pull Corrections...", self.open_review_dialog),
        ]

    def open_export_dialog(self):
        if hasattr(self.app, "open_unified_export_dialog"):
            self.app.open_unified_export_dialog(initial_dest="gdocs")

    def open_review_dialog(self):
        dialog = GoogleDocsReviewDialog(auth_manager=self.auth_manager, main_window=self.app)
        dialog.exec()

    def get_preferences_widget(self, parent: Any = None) -> Any:
        box = QGroupBox("Google Docs & Drive Integration", parent)
        layout = QVBoxLayout(box)
        layout.setSpacing(12)

        desc = QLabel(
            "<b>Google Docs & Drive Integration</b><br>"
            "Connect your Google account to create, format, and publish broadcast news transcripts, "
            "speaker turns, story chapters, and editorial margin notes directly into Google Docs."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(desc)

        # 1. Clean Account Status Card
        status_box = QGroupBox("Account Status")
        s_layout = QVBoxLayout(status_box)
        s_layout.setSpacing(8)

        self.pref_status_lbl = QLabel()
        self.pref_status_lbl.setStyleSheet("font-size: 12px; padding: 4px 0;")
        s_layout.addWidget(self.pref_status_lbl)

        btn_row = QHBoxLayout()
        self.pref_login_btn = QPushButton("Connect Google Account")
        self.pref_login_btn.setStyleSheet("font-weight: 600; padding: 6px 14px;")
        self.pref_login_btn.clicked.connect(self._on_pref_login)
        btn_row.addWidget(self.pref_login_btn)

        self.pref_logout_btn = QPushButton("Disconnect Google Account")
        self.pref_logout_btn.clicked.connect(self._on_pref_logout)
        btn_row.addWidget(self.pref_logout_btn)
        btn_row.addStretch()
        s_layout.addLayout(btn_row)
        layout.addWidget(status_box)

        # 2. Advanced Developer Settings (Hidden by default / Collapsible)
        self.adv_box = QGroupBox("Advanced Developer Settings (Optional)")
        self.adv_box.setCheckable(True)
        self.adv_box.setChecked(self.auth_manager.is_using_custom_client())
        a_layout = QVBoxLayout(self.adv_box)
        a_layout.setSpacing(8)

        adv_desc = QLabel(
            "Radio & TV Segmenter uses the official public desktop OAuth client. "
            "If you are developing or testing your own Google Cloud Console project, "
            "you may supply custom credentials below."
        )
        adv_desc.setWordWrap(True)
        adv_desc.setStyleSheet("color: #64748b; font-size: 10.5px;")
        a_layout.addWidget(adv_desc)

        c_form = QFormLayout()
        cid, csec = self.auth_manager.get_client_credentials()
        # If currently using default, show empty in edit boxes
        custom_cid = cid if self.auth_manager.is_using_custom_client() else ""

        self.client_id_edit = QLineEdit()
        self.client_id_edit.setText(custom_cid)
        self.client_id_edit.setPlaceholderText("Leave empty to use official production client")
        c_form.addRow("Custom Client ID:", self.client_id_edit)

        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.Password)
        self.client_secret_edit.setText(csec if self.auth_manager.is_using_custom_client() else "")
        self.client_secret_edit.setPlaceholderText("Optional for desktop public clients")
        c_form.addRow("Custom Client Secret:", self.client_secret_edit)
        a_layout.addLayout(c_form)

        adv_btn_row = QHBoxLayout()
        self.import_json_btn = QPushButton("Import credentials.json…")
        self.import_json_btn.clicked.connect(self._on_import_credentials_json)
        adv_btn_row.addWidget(self.import_json_btn)

        self.reset_default_btn = QPushButton("Reset to Default Client")
        self.reset_default_btn.clicked.connect(self._on_reset_default_client)
        adv_btn_row.addWidget(self.reset_default_btn)
        adv_btn_row.addStretch()
        a_layout.addLayout(adv_btn_row)

        layout.addWidget(self.adv_box)
        layout.addStretch()

        self._update_pref_status()
        return box

    def _update_pref_status(self):
        if not hasattr(self, "pref_status_lbl") or not self.pref_status_lbl:
            return

        if self.auth_manager.is_authenticated():
            email = self.auth_manager.get_user_email() or "Google Account"
            self.pref_status_lbl.setText(f"<span style='color: #16a34a; font-weight: bold;'>✓ Connected</span> — <b>{email}</b>")
            if hasattr(self, "pref_login_btn"): self.pref_login_btn.setVisible(False)
            if hasattr(self, "pref_logout_btn"): self.pref_logout_btn.setVisible(True)
        else:
            self.pref_status_lbl.setText("<span style='color: #64748b;'>Not connected</span><br><span style='color: #94a3b8; font-size: 11px;'>Connect your Google account to create and work with Google Docs from RTVS.</span>")
            if hasattr(self, "pref_login_btn"): self.pref_login_btn.setVisible(True)
            if hasattr(self, "pref_logout_btn"): self.pref_logout_btn.setVisible(False)

    def _on_pref_login(self):
        ok, msg = self.auth_manager.start_loopback_auth(parent_widget=self.app)
        if ok:
            QMessageBox.information(self.app, "Google Account Connected", f"Successfully linked Google account:\n{msg}")
        else:
            QMessageBox.critical(self.app, "Connection Failed", f"Could not connect Google account:\n\n{msg}")
        self._update_pref_status()

    def _on_pref_logout(self):
        reply = QMessageBox.question(
            self.app,
            "Disconnect Google Account",
            "Are you sure you want to disconnect your Google account from Radio & TV Segmenter?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.auth_manager.logout(revoke_remote=True)
            QMessageBox.information(self.app, "Disconnected", "Your Google account has been disconnected.")
            self._update_pref_status()

    def _on_import_credentials_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.app,
            "Select Google OAuth credentials.json",
            "",
            "JSON Files (*.json);;All Files (*.*)",
        )
        if not file_path:
            return
        cid, csec, _ = parse_google_credentials_json(file_path)
        if not cid:
            QMessageBox.warning(
                self.app,
                "Invalid Credentials File",
                "Could not find a valid OAuth 'client_id' in the selected JSON file.\n"
                "Please make sure it was downloaded from Google Cloud Console as a 'Desktop app' client.",
            )
            return
        self.client_id_edit.setText(cid)
        self.client_secret_edit.setText(csec or "")
        self.auth_manager.save_client_credentials(cid, csec or "")
        QMessageBox.information(
            self.app,
            "Custom Credentials Saved",
            "Custom Google Cloud OAuth client credentials loaded successfully.",
        )

    def _on_reset_default_client(self):
        self.auth_manager.reset_to_default_credentials()
        self.client_id_edit.setText("")
        self.client_secret_edit.setText("")
        if hasattr(self, "adv_box"):
            self.adv_box.setChecked(False)
        QMessageBox.information(
            self.app,
            "Default Client Restored",
            "Radio & TV Segmenter will use the official built-in client ID.",
        )

    def save_preferences(self, widget: Any) -> None:
        if hasattr(self, "adv_box") and self.adv_box.isChecked():
            cid = self.client_id_edit.text().strip()
            csec = self.client_secret_edit.text().strip()
            if cid:
                self.auth_manager.save_client_credentials(cid, csec)
        elif hasattr(self, "adv_box") and not self.adv_box.isChecked():
            if self.auth_manager.is_using_custom_client():
                self.auth_manager.reset_to_default_credentials()

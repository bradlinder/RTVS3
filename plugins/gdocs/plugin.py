"""Google Docs & Drive Exporter Plugin implementation for Radio & TV Segmenter."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QGroupBox,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QFormLayout,
        QMessageBox,
        QWidget,
    )
except ImportError:
    # Fallback for headless environments
    class QWidget: pass  # type: ignore
    class QGroupBox: pass  # type: ignore

from plugins.base import BasePlugin, PluginManifest
from plugins.gdocs.auth import GoogleDocsAuthManager
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
        layout.setSpacing(10)

        desc = QLabel(
            "<b>Google Docs & Drive Publishing</b><br>"
            "Export rich broadcast transcripts with speaker turns, story sections, and editorial margin comments. "
            "Connect using OAuth 2.0 loopback authorization or configure custom Google Cloud credentials."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(desc)

        # Account status
        status_box = QGroupBox("Connected Google Account")
        s_layout = QVBoxLayout(status_box)
        self.pref_status_lbl = QLabel()
        self._update_pref_status()
        s_layout.addWidget(self.pref_status_lbl)

        btn_row = QHBoxLayout()
        self.pref_login_btn = QPushButton("Sign in with Google...")
        self.pref_login_btn.clicked.connect(self._on_pref_login)
        btn_row.addWidget(self.pref_login_btn)

        self.pref_logout_btn = QPushButton("Disconnect Account")
        self.pref_logout_btn.clicked.connect(self._on_pref_logout)
        btn_row.addWidget(self.pref_logout_btn)
        btn_row.addStretch()
        s_layout.addLayout(btn_row)
        layout.addWidget(status_box)

        # Custom OAuth Credentials
        custom_box = QGroupBox("Custom Google Cloud Credentials (Optional)")
        c_form = QFormLayout(custom_box)
        cid, csec = self.auth_manager.get_client_credentials()

        self.client_id_edit = QLineEdit()
        self.client_id_edit.setText(cid)
        c_form.addRow("OAuth Client ID:", self.client_id_edit)

        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.Password)
        self.client_secret_edit.setText(csec)
        self.client_secret_edit.setPlaceholderText("Leave empty to use default desktop credentials")
        c_form.addRow("OAuth Client Secret:", self.client_secret_edit)

        layout.addWidget(custom_box)
        return box

    def _update_pref_status(self):
        if hasattr(self, "pref_status_lbl") and self.pref_status_lbl:
            if self.auth_manager.is_authenticated():
                email = self.auth_manager.get_user_email() or "Google Account"
                self.pref_status_lbl.setText(f"✓ Connected: <b>{email}</b>")
                self.pref_status_lbl.setStyleSheet("color: #16a34a;")
                if hasattr(self, "pref_login_btn"): self.pref_login_btn.setVisible(False)
                if hasattr(self, "pref_logout_btn"): self.pref_logout_btn.setVisible(True)
            else:
                self.pref_status_lbl.setText("⚠ Not connected to any Google account.")
                self.pref_status_lbl.setStyleSheet("color: #dc2626;")
                if hasattr(self, "pref_login_btn"): self.pref_login_btn.setVisible(True)
                if hasattr(self, "pref_logout_btn"): self.pref_logout_btn.setVisible(False)

    def _on_pref_login(self):
        ok, msg = self.auth_manager.start_loopback_auth()
        if ok:
            QMessageBox.information(self.app, "Connected", f"Successfully linked Google account: {msg}")
        else:
            QMessageBox.critical(self.app, "Error", f"Failed to authenticate: {msg}")
        self._update_pref_status()

    def _on_pref_logout(self):
        self.auth_manager.logout()
        QMessageBox.information(self.app, "Disconnected", "Google credentials have been removed.")
        self._update_pref_status()

    def save_preferences(self, widget: Any) -> None:
        if hasattr(self, "client_id_edit") and hasattr(self, "client_secret_edit"):
            cid = self.client_id_edit.text().strip()
            csec = self.client_secret_edit.text().strip()
            self.auth_manager.save_client_credentials(cid, csec)

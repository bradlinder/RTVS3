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
        QTextBrowser,
        QWidget,
    )
except ImportError:
    # Fallback for headless environments
    class QWidget: pass  # type: ignore
    class QGroupBox: pass  # type: ignore
    class QDialog: pass  # type: ignore

from plugins.base import BasePlugin, PluginManifest
from plugins.gdocs.auth import GoogleDocsAuthManager, parse_google_credentials_json
from plugins.gdocs.export_destination import GoogleDocsExportDestination
from plugins.gdocs.review import GoogleDocsReviewDialog


class GoogleOAuthSetupGuideDialog(QDialog):
    """Detailed visual guide with clickable hyperlinks for Google Cloud Console setup."""

    def __init__(self, parent: Any = None, on_import_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.on_import_callback = on_import_callback
        self.setWindowTitle("Google Docs — OAuth Setup Guide (No Hosting Required)")
        self.resize(740, 600)
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)
        html_content = """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b;">
            <h2 style="color: #0284c7; margin-top: 0; margin-bottom: 8px;">Connecting Radio & TV Segmenter to Google Docs</h2>
            <p style="color: #475569; font-size: 13px; margin-bottom: 14px;">
                Because Radio & TV Segmenter is a <b>local desktop application</b>, all exports run directly from your machine. 
                <b>No web hosting, external servers, or domain names are required.</b> Follow these steps once to authorize your Google account:
            </p>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 14px;">
                <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px; font-weight: bold; width: 32px; color: #0284c7; vertical-align: top;">1</td>
                    <td style="padding: 10px;">
                        <b>Create a Google Cloud Project</b><br>
                        Open the <a href="https://console.cloud.google.com/" style="color: #0284c7; font-weight: bold;">Google Cloud Console (console.cloud.google.com)</a>.<br>
                        Click the project dropdown at the top &gt; <b>New Project</b> (e.g. <i>Radio TV Segmenter</i>) &gt; <b>Create</b>.
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px; font-weight: bold; color: #0284c7; vertical-align: top;">2</td>
                    <td style="padding: 10px;">
                        <b>Enable Google Docs &amp; Drive APIs</b><br>
                        Visit the <a href="https://console.cloud.google.com/apis/library" style="color: #0284c7; font-weight: bold;">Google Cloud API Library</a>.<br>
                        • Search for <a href="https://console.cloud.google.com/apis/library/docs.googleapis.com" style="color: #0284c7;"><b>Google Docs API</b></a> and click <b>Enable</b>.<br>
                        • Search for <a href="https://console.cloud.google.com/apis/library/drive.googleapis.com" style="color: #0284c7;"><b>Google Drive API</b></a> and click <b>Enable</b>.
                    </td>
                </tr>
                <tr style="background: #fffbeb; border: 1px solid #fef3c7; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px; font-weight: bold; color: #b45309; vertical-align: top;">3</td>
                    <td style="padding: 10px;">
                        <b style="color: #9a3412;">Configure OAuth Consent Screen (EASIEST METHOD)</b><br>
                        Go to <a href="https://console.cloud.google.com/apis/credentials/consent" style="color: #0284c7; font-weight: bold;">APIs &amp; Services &gt; OAuth consent screen</a>.<br>
                        • User Type: Select <b>External</b> &gt; Click <b>Create</b>.<br>
                        • App name: <code>Radio &amp; TV Segmenter</code>.<br>
                        • User support &amp; Developer email: Select your email from the dropdown.<br>
                        • Click <b>Save and Continue</b> through Scopes and Test Users to the Summary.<br><br>
                        • <b style="color: #047857;">RECOMMENDED (Skip Test Users &amp; Avoid Error 403):</b><br>
                        &nbsp;&nbsp;On the <b>OAuth consent screen</b> page, click the <b style="color: #047857;">PUBLISH APP</b> button under <i>Publishing status</i>.<br>
                        &nbsp;&nbsp;<i>(Publishing lets you sign in immediately with any of your Google accounts without needing to manage test user lists. Google will show an "unverified app" screen where you simply click <b>Advanced &gt; Go to Radio &amp; TV Segmenter</b> to authorize.)</i>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px; font-weight: bold; color: #0284c7; vertical-align: top;">4</td>
                    <td style="padding: 10px;">
                        <b>Create Desktop OAuth Client ID</b><br>
                        Go to <a href="https://console.cloud.google.com/apis/credentials" style="color: #0284c7; font-weight: bold;">APIs &amp; Services &gt; Credentials</a>.<br>
                        • Click <b>+ Create Credentials</b> &gt; <b>OAuth client ID</b>.<br>
                        • Application type: Select <b>Desktop app</b>.<br>
                        • Name: <code>Radio &amp; TV Segmenter Desktop</code> &gt; Click <b>Create</b>.<br>
                        • In the popup, click <b>Download JSON</b> (saves <code>credentials.json</code> to your computer).
                    </td>
                </tr>
                <tr style="background: #f8fafc;">
                    <td style="padding: 10px; font-weight: bold; color: #0284c7; vertical-align: top;">5</td>
                    <td style="padding: 10px;">
                        <b>Import into Radio &amp; TV Segmenter</b><br>
                        Click the <b>Import credentials.json...</b> button below to load your file. Then click <b>Sign in with Google...</b> to connect!
                    </td>
                </tr>
            </table>
        </div>
        """
        browser.setHtml(html_content)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        if self.on_import_callback:
            import_btn = QPushButton("Import credentials.json Now...")
            import_btn.setStyleSheet("font-weight: bold; padding: 6px 12px;")
            def _do_import():
                self.accept()
                self.on_import_callback()
            import_btn.clicked.connect(_do_import)
            btn_row.addWidget(import_btn)

        open_consent_btn = QPushButton("Open Consent Screen (Add Test User) ↗")
        def _open_consent():
            try:
                QDesktopServices.openUrl(QUrl("https://console.cloud.google.com/apis/credentials/consent"))
            except Exception:
                import webbrowser
                webbrowser.open("https://console.cloud.google.com/apis/credentials/consent")
        open_consent_btn.clicked.connect(_open_consent)
        btn_row.addWidget(open_consent_btn)

        open_console_btn = QPushButton("Google Cloud Console ↗")
        def _open_console():
            try:
                QDesktopServices.openUrl(QUrl("https://console.cloud.google.com/"))
            except Exception:
                import webbrowser
                webbrowser.open("https://console.cloud.google.com/")
        open_console_btn.clicked.connect(_open_console)
        btn_row.addWidget(open_console_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)


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
        custom_box = QGroupBox("Google Cloud OAuth Credentials")
        c_layout = QVBoxLayout(custom_box)

        c_info = QLabel(
            "Google requires an OAuth Client ID to authorize desktop access to Google Docs and Drive. "
            "No web hosting or servers are needed."
        )
        c_info.setWordWrap(True)
        c_info.setStyleSheet("color: #64748b; font-size: 11px;")
        c_layout.addWidget(c_info)

        c_form = QFormLayout()
        cid, csec = self.auth_manager.get_client_credentials()

        self.client_id_edit = QLineEdit()
        self.client_id_edit.setText(cid)
        self.client_id_edit.setPlaceholderText("e.g. 1234567890-xxx.apps.googleusercontent.com")
        c_form.addRow("OAuth Client ID:", self.client_id_edit)

        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.Password)
        self.client_secret_edit.setText(csec)
        self.client_secret_edit.setPlaceholderText("Client secret from Google Cloud Console (if applicable)")
        c_form.addRow("OAuth Client Secret:", self.client_secret_edit)
        c_layout.addLayout(c_form)

        cred_btn_row = QHBoxLayout()
        self.import_json_btn = QPushButton("Import credentials.json...")
        self.import_json_btn.clicked.connect(self._on_import_credentials_json)
        cred_btn_row.addWidget(self.import_json_btn)

        self.setup_guide_btn = QPushButton("Setup Instructions (1 Min)")
        self.setup_guide_btn.clicked.connect(self._on_show_setup_guide)
        cred_btn_row.addWidget(self.setup_guide_btn)
        cred_btn_row.addStretch()
        c_layout.addLayout(cred_btn_row)

        layout.addWidget(custom_box)
        return box

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
            "Credentials Loaded",
            f"Successfully loaded Google OAuth Client ID!\n\nYou can now click 'Sign in with Google...' to connect.",
        )

    def _on_show_setup_guide(self):
        guide = GoogleOAuthSetupGuideDialog(self.app, on_import_callback=self._on_import_credentials_json)
        guide.exec()

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
        cid, _ = self.auth_manager.get_client_credentials()
        if not cid or not cid.strip() or "rtvs-desktop-oauth" in cid:
            msg_box = QMessageBox(self.app)
            msg_box.setWindowTitle("Google OAuth Setup Required")
            msg_box.setText(
                "A free Google Cloud OAuth Client ID is required to connect to Google Docs & Drive.\n\n"
                "• No web hosting or servers are needed (runs 100% locally on your computer).\n"
                "• Takes about 1–2 minutes to set up once."
            )
            guide_btn = msg_box.addButton("Open Setup Guide (Clickable Links)...", QMessageBox.ButtonRole.ActionRole)
            import_btn = msg_box.addButton("Import credentials.json...", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.exec()

            clicked = msg_box.clickedButton()
            if clicked == guide_btn:
                self._on_show_setup_guide()
                return
            elif clicked == import_btn:
                self._on_import_credentials_json()
                return
            else:
                return

        ok, msg = self.auth_manager.start_loopback_auth(parent_widget=self.app)
        if ok:
            QMessageBox.information(self.app, "Connected", f"Successfully linked Google account: {msg}")
        else:
            QMessageBox.critical(self.app, "Authentication Failed", f"Could not link Google account:\n\n{msg}")
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

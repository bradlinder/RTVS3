"""Google Docs Export Destination for UnifiedExportDialog.

Provides configuration UI, Drive folder management, scope selection,
and execution engine for exporting formatted broadcast transcripts,
speaker turns, story segmentations, and margin notes to Google Docs.
"""
from __future__ import annotations

import os
import threading
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
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
from plugins.gdocs.drive_folders import (
    create_drive_folder,
    get_or_create_project_subfolder,
    DriveFolderPickerDialog,
)


class GoogleDocsExportDestination(ExportDestination):
    """ExportDestination implementation for Google Docs."""

    def __init__(self, plugin: Any):
        super().__init__(
            id="gdocs",
            title="Google Docs",
            description="Exports formatted transcripts, story chapters, speaker turns, and margin notes to Google Docs.",
            button_label="Export to Google Docs...",
        )
        self.plugin = plugin
        self.auth_manager = plugin.auth_manager
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.widget: Optional[QWidget] = None
        self.main_window: Any = None
        self.current_scope: str = "full"
        self._stories_cache: List[Any] = []
        self._selected_story_indices: List[int] = []

    def create_widget(self, parent: Any, main_window: Any) -> Any:
        self.main_window = main_window
        self._stories_cache = getattr(main_window, "stories", []) or []

        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        # 1. Google Account Connection Card
        auth_group = QGroupBox("Google Account Connection")
        a_layout = QVBoxLayout(auth_group)
        a_layout.setContentsMargins(10, 10, 10, 10)
        a_layout.setSpacing(8)

        self.account_status_lbl = QLabel()
        self._update_auth_status_label()
        a_layout.addWidget(self.account_status_lbl)

        btn_row = QHBoxLayout()
        self.auth_btn = QPushButton("Sign in with Google…")
        self.auth_btn.clicked.connect(self._on_auth_button_clicked)
        btn_row.addWidget(self.auth_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        btn_row.addWidget(self.disconnect_btn)
        btn_row.addStretch()
        a_layout.addLayout(btn_row)
        layout.addWidget(auth_group)

        # 2. Document & Title Settings
        doc_group = QGroupBox("Document Settings")
        doc_layout = QVBoxLayout(doc_group)
        doc_layout.setContentsMargins(10, 10, 10, 10)
        doc_layout.setSpacing(8)

        title_lbl = QLabel("Document Title:")
        title_lbl.setStyleSheet("font-weight: 500; font-size: 11px; color: #94a3b8;")
        self.title_input = QLineEdit()
        default_title = "Broadcast Transcript"
        # Prioritize project file name, then media/audio file name
        p_path = getattr(main_window, "project_file", None) or getattr(main_window, "current_project_path", None)
        if p_path:
            try:
                base = os.path.splitext(os.path.basename(str(p_path)))[0]
                if base:
                    default_title = base
            except Exception:
                pass
        if default_title == "Broadcast Transcript":
            m_path = (
                getattr(main_window, "media_path", None)
                or getattr(main_window, "audio_file", None)
                or getattr(main_window, "current_media_path", None)
            )
            if m_path:
                try:
                    base = os.path.splitext(os.path.basename(str(m_path)))[0]
                    if base:
                        default_title = base
                except Exception:
                    pass
        self.title_input.setText(default_title)
        doc_layout.addWidget(title_lbl)
        doc_layout.addWidget(self.title_input)
        layout.addWidget(doc_group)

        # 3. Language Options
        lang_group = QGroupBox("Language Options")
        lang_layout = QVBoxLayout(lang_group)
        lang_layout.setContentsMargins(10, 10, 10, 10)
        lang_layout.setSpacing(8)

        src_code = "en"
        if hasattr(main_window, "source_language_code"):
            try:
                src_code = str(main_window.source_language_code() or "en").lower()
            except Exception:
                src_code = "en"

        has_translation = False
        if hasattr(main_window, "get_spanish_translation_item"):
            try:
                t_item = main_window.get_spanish_translation_item()
                if t_item and isinstance(t_item, dict):
                    has_translation = bool(t_item.get("segments"))
            except Exception:
                has_translation = False

        lang_checks_row = QHBoxLayout()
        lang_checks_row.setSpacing(12)

        saved_en = self.settings.value("gdocs_opt_en", True, type=bool)
        saved_es = self.settings.value("gdocs_opt_es", False, type=bool)
        if not saved_en and not saved_es:
            if src_code == "es":
                saved_es = True
            else:
                saved_en = True

        if src_code == "es":
            self.cb_es = QCheckBox("Spanish (Original)")
            self.cb_es.setChecked(saved_es)
            self.cb_es.setEnabled(True)

            self.cb_en = QCheckBox("English (Translated)")
            self.cb_en.setEnabled(has_translation)
            self.cb_en.setChecked(has_translation and saved_en)
            if not has_translation:
                self.cb_en.setToolTip("English translation is not available for this project. Generate a translation first to enable.")
        else:
            self.cb_en = QCheckBox("English (Original)")
            self.cb_en.setChecked(saved_en)
            self.cb_en.setEnabled(True)

            self.cb_es = QCheckBox("Spanish (Translated)")
            self.cb_es.setEnabled(has_translation)
            self.cb_es.setChecked(has_translation and saved_es)
            if not has_translation:
                self.cb_es.setToolTip("Spanish translation is not available for this project. Generate a translation first to enable.")

        lang_checks_row.addWidget(self.cb_en)
        lang_checks_row.addWidget(self.cb_es)
        lang_checks_row.addStretch()
        lang_layout.addLayout(lang_checks_row)

        # Dual language mode container
        self.dual_lang_container = QWidget()
        d_layout = QHBoxLayout(self.dual_lang_container)
        d_layout.setContentsMargins(0, 4, 0, 0)
        d_layout.setSpacing(8)

        d_label = QLabel("Dual Language Mode:")
        d_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.dual_lang_combo = QComboBox()
        self.dual_lang_combo.addItem("Separate Google Docs for each language", "separate")
        self.dual_lang_combo.addItem("Single combined Google Doc (English first, Spanish below)", "en_first")
        self.dual_lang_combo.addItem("Single combined Google Doc (Spanish first, English below)", "es_first")
        saved_dual = str(self.settings.value("gdocs_dual_lang_mode", "separate") or "separate")
        dual_idx = self.dual_lang_combo.findData(saved_dual)
        if dual_idx >= 0:
            self.dual_lang_combo.setCurrentIndex(dual_idx)

        d_layout.addWidget(d_label)
        d_layout.addWidget(self.dual_lang_combo)
        d_layout.addStretch()
        lang_layout.addWidget(self.dual_lang_container)

        def _update_dual_visibility():
            both = self.cb_en.isChecked() and self.cb_es.isChecked()
            self.dual_lang_container.setVisible(both)

        self.cb_en.toggled.connect(_update_dual_visibility)
        self.cb_es.toggled.connect(_update_dual_visibility)
        _update_dual_visibility()

        layout.addWidget(lang_group)

        # 4. Google Drive Destination Folder
        folder_group = QGroupBox("Google Drive Destination Folder")
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setContentsMargins(10, 10, 10, 10)
        folder_layout.setSpacing(8)

        # Read persisted folder info
        self.folder_id = str(self.settings.value("gdocs_last_folder_id", "") or "")
        self.folder_name = str(self.settings.value("gdocs_last_folder_name", "") or "")
        if not self.folder_id:
            self.folder_name = "Root (My Drive)"

        self.folder_display_lbl = QLabel()
        self.folder_display_lbl.setStyleSheet("""
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 11.5px;
            color: #f8fafc;
        """)
        self._update_folder_display()
        folder_layout.addWidget(self.folder_display_lbl)

        f_btn_row = QHBoxLayout()
        f_btn_row.setSpacing(6)

        self.select_folder_btn = QPushButton("Select Folder…")
        self.select_folder_btn.setToolTip("Browse and choose an existing Google Drive folder.")
        self.select_folder_btn.clicked.connect(self._on_select_folder_clicked)
        f_btn_row.addWidget(self.select_folder_btn)

        self.new_folder_btn = QPushButton("+ Create New Folder…")
        self.new_folder_btn.setToolTip("Create a new folder directly in Google Drive.")
        self.new_folder_btn.clicked.connect(self._on_create_folder_clicked)
        f_btn_row.addWidget(self.new_folder_btn)

        self.root_folder_btn = QPushButton("Use Root")
        self.root_folder_btn.setToolTip("Export directly to the root of your Google Drive.")
        self.root_folder_btn.clicked.connect(self._on_use_root_clicked)
        f_btn_row.addWidget(self.root_folder_btn)

        f_btn_row.addStretch()
        folder_layout.addLayout(f_btn_row)

        # Subfolder Option Checkbox
        self.cb_subfolder = QCheckBox("Create a new subfolder for each project")
        self.cb_subfolder.setToolTip(
            "When checked, creates a folder named after the project/media file inside the chosen Drive folder and saves exports there."
        )
        self.cb_subfolder.setChecked(self.settings.value("gdocs_create_project_subfolders", True, type=bool))
        folder_layout.addWidget(self.cb_subfolder)

        layout.addWidget(folder_group)

        # 4. Story Selection Panel (Visible when scope is "selected_stories")
        self.story_select_group = QGroupBox("Select Stories to Export")
        s_layout = QVBoxLayout(self.story_select_group)
        s_layout.setContentsMargins(10, 10, 10, 10)
        s_layout.setSpacing(6)

        self.story_select_info = QLabel("Choose the individual stories to include in this Google Docs export:")
        self.story_select_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        s_layout.addWidget(self.story_select_info)

        self.stories_list = QListWidget()
        self.stories_list.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px;
                color: #f8fafc;
                min-height: 90px;
                max-height: 140px;
            }
            QListWidget::item {
                padding: 4px 6px;
            }
        """)
        s_layout.addWidget(self.stories_list)

        s_btns = QHBoxLayout()
        self.select_all_stories_btn = QPushButton("Select All")
        self.select_all_stories_btn.clicked.connect(self._select_all_stories)
        self.deselect_all_stories_btn = QPushButton("Deselect All")
        self.deselect_all_stories_btn.clicked.connect(self._deselect_all_stories)
        s_btns.addWidget(self.select_all_stories_btn)
        s_btns.addWidget(self.deselect_all_stories_btn)
        s_btns.addStretch()
        s_layout.addLayout(s_btns)

        layout.addWidget(self.story_select_group)
        self._populate_stories_list()
        self.story_select_group.setVisible(self.current_scope == "selected_stories")

        # 5. Formatting & Content Options
        fmt_group = QGroupBox("Formatting & Content Options")
        f_layout = QVBoxLayout(fmt_group)
        f_layout.setContentsMargins(10, 10, 10, 10)
        f_layout.setSpacing(6)

        self.cb_speakers = QCheckBox("Include Bold Speaker Labels (e.g. Speaker Name: )")
        self.cb_speakers.setToolTip("Include bold inline speaker names at the start of dialogue turns (speaker labels are bold by default).")
        self.cb_speakers.setChecked(self.settings.value("gdocs_opt_speakers", True, type=bool))
        f_layout.addWidget(self.cb_speakers)

        self.cb_chapters = QCheckBox("Include Story Chapters as Headers (Table of Contents)")
        self.cb_chapters.setToolTip("Insert Heading 2 (H2) section headers for each story chapter so you can jump between stories using the Google Docs outline / Table of Contents (default: unchecked).")
        self.cb_chapters.setChecked(self.settings.value("gdocs_opt_chapters", False, type=bool))
        f_layout.addWidget(self.cb_chapters)

        self.cb_timestamps = QCheckBox("Include Paragraph & Story Timestamps [00:01:23]")
        self.cb_timestamps.setToolTip("Muted bracketed timecodes at the start of paragraphs and in story chapter headings.")
        self.cb_timestamps.setChecked(self.settings.value("gdocs_opt_timestamps", True, type=bool))
        f_layout.addWidget(self.cb_timestamps)

        self.cb_comments = QCheckBox("Anchor Editorial Story Notes as Google Docs Margin Comments")
        self.cb_comments.setToolTip("Inserts story editorial notes and segment annotations as interactive discussion comments in the Google Docs margin.")
        self.cb_comments.setChecked(self.settings.value("gdocs_opt_comments", True, type=bool))
        f_layout.addWidget(self.cb_comments)

        self.cb_browser = QCheckBox("Open Google Doc in Web Browser Upon Completion")
        self.cb_browser.setChecked(self.settings.value("gdocs_opt_browser", True, type=bool))
        f_layout.addWidget(self.cb_browser)

        layout.addWidget(fmt_group)
        layout.addStretch()

        scroll.setWidget(content_widget)
        self.widget = scroll

        self._update_auth_ui_state()
        return self.widget

    def _update_folder_display(self):
        if not hasattr(self, "folder_display_lbl") or not self.folder_display_lbl:
            return
        if not self.folder_id:
            self.folder_display_lbl.setText("📁 <b>Folder:</b> Root (My Drive)")
        else:
            name = self.folder_name or "Custom Folder"
            self.folder_display_lbl.setText(f"📁 <b>Folder:</b> {name} <span style='color: #64748b;'>(ID: {self.folder_id})</span>")

    def _populate_stories_list(self):
        if not hasattr(self, "stories_list") or not self.stories_list:
            return
        self.stories_list.clear()

        # Check which stories are currently selected in main window
        active_indices = set()
        if hasattr(self.main_window, "current_selected_story_indices"):
            active_indices = set(self.main_window.current_selected_story_indices or [])

        for idx, story in enumerate(self._stories_cache):
            title = getattr(story, "title", None) or (story.get("title") if isinstance(story, dict) else f"Story {idx + 1}")
            item = QListWidgetItem(f"Story {idx + 1}: {title}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # Default check state: checked if selected in main window, or if active_indices empty check all
            is_checked = (idx in active_indices) if active_indices else True
            item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.stories_list.addItem(item)

    def _select_all_stories(self):
        for i in range(self.stories_list.count()):
            self.stories_list.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all_stories(self):
        for i in range(self.stories_list.count()):
            self.stories_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected_story_indices(self) -> List[int]:
        if not hasattr(self, "stories_list") or not self.stories_list:
            return list(range(len(self._stories_cache)))
        selected = []
        for i in range(self.stories_list.count()):
            item = self.stories_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected

    def on_scope_changed(self, scope: str, stories: list) -> None:
        """Called when export scope changes in the UnifiedExportDialog."""
        self.current_scope = scope
        self._stories_cache = stories or []
        if hasattr(self, "story_select_group") and self.story_select_group:
            self.story_select_group.setVisible(scope == "selected_stories")
            self._populate_stories_list()

    def _on_select_folder_clicked(self):
        token = self.auth_manager.get_valid_access_token()
        if not token:
            QMessageBox.warning(self.widget, "Sign In Required", "Please sign in with Google first to browse your Drive folders.")
            return

        dlg = DriveFolderPickerDialog(
            self.widget,
            access_token=token,
            current_folder_id=self.folder_id,
            current_folder_name=self.folder_name,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.folder_id = dlg.selected_folder_id
            self.folder_name = dlg.selected_folder_name
            self.settings.setValue("gdocs_last_folder_id", self.folder_id)
            self.settings.setValue("gdocs_last_folder_name", self.folder_name)
            self.settings.sync()
            self._update_folder_display()

    def _on_create_folder_clicked(self):
        token = self.auth_manager.get_valid_access_token()
        if not token:
            QMessageBox.warning(self.widget, "Sign In Required", "Please sign in with Google first to create folders in Google Drive.")
            return

        name, ok = QInputDialog.getText(
            self.widget,
            "Create Google Drive Folder",
            "Enter name for the new folder:",
            text="Radio & TV Segmenter Exports",
        )
        if not ok or not name.strip():
            return

        parent_id = self.folder_id if self.folder_id else None
        success, new_id, err = create_drive_folder(token, name.strip(), parent_id=parent_id)
        if not success:
            QMessageBox.critical(self.widget, "Folder Creation Failed", f"Could not create folder in Google Drive:\n{err}")
            return

        self.folder_id = new_id
        self.folder_name = name.strip()
        self.settings.setValue("gdocs_last_folder_id", self.folder_id)
        self.settings.setValue("gdocs_last_folder_name", self.folder_name)
        self.settings.sync()
        self._update_folder_display()
        QMessageBox.information(self.widget, "Folder Created", f"Created folder '{name.strip()}' in Google Drive and set it as the export destination!")

    def _on_use_root_clicked(self):
        self.folder_id = ""
        self.folder_name = "Root (My Drive)"
        self.settings.setValue("gdocs_last_folder_id", "")
        self.settings.setValue("gdocs_last_folder_name", "Root (My Drive)")
        self.settings.sync()
        self._update_folder_display()

    def _update_auth_status_label(self):
        if not hasattr(self, "account_status_lbl") or not self.account_status_lbl:
            return
        if self.auth_manager.is_authenticated():
            email = self.auth_manager.get_user_email() or "Google Account"
            self.account_status_lbl.setText(f"✓ <b>Connected:</b> {email}")
            self.account_status_lbl.setStyleSheet("color: #16a34a; font-size: 12px;")
        else:
            self.account_status_lbl.setText("⚠ <b>Not connected</b> — Sign in to export documents to Google Docs.")
            self.account_status_lbl.setStyleSheet("color: #dc2626; font-size: 12px;")

    def _update_auth_ui_state(self):
        self._update_auth_status_label()
        is_auth = self.auth_manager.is_authenticated()
        if hasattr(self, "auth_btn"):
            self.auth_btn.setVisible(not is_auth)
        if hasattr(self, "disconnect_btn"):
            self.disconnect_btn.setVisible(is_auth)

    def _on_auth_button_clicked(self):
        cid, _ = self.auth_manager.get_client_credentials()
        if not cid or not cid.strip() or "rtvs-desktop-oauth" in cid:
            from plugins.gdocs.plugin import GoogleOAuthSetupGuideDialog
            def _import_cb():
                from PySide6.QtWidgets import QFileDialog
                from plugins.gdocs.auth import parse_google_credentials_json
                fp, _ = QFileDialog.getOpenFileName(
                    self.widget,
                    "Select Google OAuth credentials.json",
                    "",
                    "JSON Files (*.json);;All Files (*.*)",
                )
                if fp:
                    c_id, c_sec, _ = parse_google_credentials_json(fp)
                    if c_id:
                        self.auth_manager.save_client_credentials(c_id, c_sec or "")
                        QMessageBox.information(self.widget, "Credentials Loaded", "Google OAuth credentials loaded successfully! You can now sign in.")
            guide = GoogleOAuthSetupGuideDialog(self.widget, on_import_callback=_import_cb)
            guide.exec()
            return

        ok, msg = self.auth_manager.start_loopback_auth(parent_widget=self.widget)
        if ok:
            QMessageBox.information(self.widget, "Connected", f"Successfully linked account: {msg}")
        else:
            QMessageBox.critical(self.widget, "Authentication Failed", f"Could not link Google account:\n\n{msg}")
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
        if hasattr(self, "cb_en") and hasattr(self, "cb_es"):
            if not self.cb_en.isChecked() and not self.cb_es.isChecked():
                return False, "Please select at least one language for Google Docs export (English or Spanish)."
        if self.current_scope == "selected_stories":
            selected = self.get_selected_story_indices()
            if not selected:
                return False, "Please select at least one story to export."
        return True, ""

    def get_export_data(self) -> Dict[str, Any]:
        title = self.title_input.text().strip() if hasattr(self, "title_input") else "Transcript"
        create_subfolder = self.cb_subfolder.isChecked() if hasattr(self, "cb_subfolder") else True
        include_en = self.cb_en.isChecked() if hasattr(self, "cb_en") else True
        include_es = self.cb_es.isChecked() if hasattr(self, "cb_es") else False
        dual_lang_mode = self.dual_lang_combo.currentData() if hasattr(self, "dual_lang_combo") else "separate"
        include_speakers = self.cb_speakers.isChecked() if hasattr(self, "cb_speakers") else True
        include_chapters = self.cb_chapters.isChecked() if hasattr(self, "cb_chapters") else False
        bold_speakers = True  # Always bold by default per user requirement

        # Persist preferences
        self.settings.setValue("gdocs_last_folder_id", self.folder_id)
        self.settings.setValue("gdocs_last_folder_name", self.folder_name)
        self.settings.setValue("gdocs_create_project_subfolders", create_subfolder)
        self.settings.setValue("gdocs_opt_en", include_en)
        self.settings.setValue("gdocs_opt_es", include_es)
        self.settings.setValue("gdocs_dual_lang_mode", dual_lang_mode)
        self.settings.setValue("gdocs_opt_speakers", include_speakers)
        self.settings.setValue("gdocs_opt_chapters", include_chapters)
        if hasattr(self, "cb_timestamps"):
            self.settings.setValue("gdocs_opt_timestamps", self.cb_timestamps.isChecked())
        if hasattr(self, "cb_comments"):
            self.settings.setValue("gdocs_opt_comments", self.cb_comments.isChecked())
        if hasattr(self, "cb_browser"):
            self.settings.setValue("gdocs_opt_browser", self.cb_browser.isChecked())
        self.settings.sync()

        return {
            "title": title,
            "folder_id": self.folder_id,
            "folder_name": self.folder_name,
            "create_subfolder": create_subfolder,
            "scope": self.current_scope,
            "selected_stories": self.get_selected_story_indices(),
            "include_english": include_en,
            "include_spanish": include_es,
            "dual_language_mode": dual_lang_mode,
            "include_speakers": include_speakers,
            "bold_speakers": True,
            "include_story_chapters": include_chapters,
            "include_timestamps": self.cb_timestamps.isChecked() if hasattr(self, "cb_timestamps") else True,
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

        base_title = export_data.get("title", "Broadcast Transcript")
        folder_id = export_data.get("folder_id", "")
        create_subfolder = export_data.get("create_subfolder", True)
        scope = export_data.get("scope", getattr(self, "current_scope", "full"))
        selected_stories = export_data.get("selected_stories", [])
        include_en = export_data.get("include_english", True)
        include_es = export_data.get("include_spanish", False)
        dual_lang_mode = export_data.get("dual_language_mode", "separate")
        include_speakers = export_data.get("include_speakers", True)
        bold_speakers = True
        include_story_chapters = export_data.get("include_story_chapters", export_data.get("include_chapters", False))
        include_timestamps = export_data.get("include_timestamps", True)
        anchor_comments = export_data.get("anchor_comments", True)
        open_browser = export_data.get("open_browser", True)

        # Retrieve stories and transcript from main_window
        stories = getattr(main_window, "stories", []) or []
        transcript_data = getattr(main_window, "transcript", {}) or {}
        segments = transcript_data.get("segments", [])

        # Retrieve source language & translation segments
        src_code = "en"
        if hasattr(main_window, "source_language_code"):
            try:
                src_code = str(main_window.source_language_code() or "en").lower()
            except Exception:
                src_code = "en"

        orig_segments = segments
        trans_segments = []
        if hasattr(main_window, "get_spanish_translation_item"):
            try:
                t_item = main_window.get_spanish_translation_item()
                if t_item and isinstance(t_item, dict):
                    trans_segments = t_item.get("segments", []) or []
            except Exception as e:
                print(f"[GDOCS EXPORT] Translation fetch warning: {e}")

        if src_code == "es":
            spanish_segments = orig_segments
            english_segments = trans_segments
        else:
            english_segments = orig_segments
            spanish_segments = trans_segments

        # If subfolder requested, find or create project subfolder in Google Drive
        target_folder_id = folder_id
        if create_subfolder:
            media_path = getattr(main_window, "media_path", "")
            project_base_name = ""
            if media_path:
                project_base_name = os.path.splitext(os.path.basename(media_path))[0]
            if not project_base_name:
                project_base_name = base_title.replace(" — Transcript", "")
            
            ok_sub, sub_id, _ = get_or_create_project_subfolder(
                access_token=token,
                parent_folder_id=folder_id if folder_id else None,
                project_name=project_base_name,
            )
            if ok_sub and sub_id:
                target_folder_id = sub_id

        serializer = GoogleDocsSerializer()
        created_docs = []

        def _export_single_doc(doc_title: str, segs: list, lang_lbl: str, sec_segs: Optional[list] = None, sec_title: Optional[str] = None, sec_lang: Optional[str] = None) -> Tuple[bool, str, str]:
            meta = {
                "media_filename": getattr(main_window, "media_path", ""),
                "duration": getattr(main_window, "duration", 0.0),
                "language": lang_lbl,
            }
            _, batch_requests, comment_anchors = serializer.serialize_document(
                document_title=doc_title,
                stories=stories,
                transcript_segments=segs,
                project_metadata=meta,
                scope=scope,
                selected_story_indices=selected_stories,
                main_window=main_window,
                include_speakers=include_speakers,
                bold_speakers=True,
                include_story_chapters=include_story_chapters,
                include_timestamps=include_timestamps,
                include_comments=anchor_comments,
                include_highlights=True,
                lang_code=lang_lbl.lower(),
                secondary_segments=sec_segs,
                secondary_title=sec_title,
                secondary_lang_code=sec_lang,
            )
            ok, doc_id, _ = create_google_doc(token, doc_title, folder_id=target_folder_id)
            if not ok:
                return False, doc_id, ""
            ok_batch, batch_err = batch_update_google_doc(token, doc_id, batch_requests)
            if not ok_batch:
                print(f"[GDOCS EXPORT] Warning on batch update for '{doc_title}': {batch_err}")
            if anchor_comments and comment_anchors:
                attach_editorial_notes_as_comments(token, doc_id, comment_anchors)
            return True, doc_id, f"https://docs.google.com/document/d/{doc_id}/edit"

        # Case 1: Dual Language export
        if include_en and include_es:
            if dual_lang_mode == "separate":
                # Export English doc
                t_en = f"{base_title} (English)" if "(English)" not in base_title else base_title
                ok_en, id_en, url_en = _export_single_doc(t_en, english_segments, "EN")
                if not ok_en:
                    if progress_dialog: progress_dialog.close()
                    QMessageBox.critical(main_window, "Export Failed", f"Failed to create English Google Doc:\n{id_en}")
                    return False
                created_docs.append((t_en, url_en))

                # Export Spanish doc
                t_es = f"{base_title} (Spanish)" if "(Spanish)" not in base_title else base_title
                ok_es, id_es, url_es = _export_single_doc(t_es, spanish_segments, "ES")
                if not ok_es:
                    if progress_dialog: progress_dialog.close()
                    QMessageBox.critical(main_window, "Export Failed", f"Failed to create Spanish Google Doc:\n{id_es}")
                    return False
                created_docs.append((t_es, url_es))

            elif dual_lang_mode == "en_first":
                t_bi = f"{base_title} (Bilingual - EN/ES)"
                ok_bi, id_bi, url_bi = _export_single_doc(
                    t_bi, english_segments, "EN / ES",
                    sec_segs=spanish_segments, sec_title="Spanish Translation", sec_lang="es"
                )
                if not ok_bi:
                    if progress_dialog: progress_dialog.close()
                    QMessageBox.critical(main_window, "Export Failed", f"Failed to create Bilingual Google Doc:\n{id_bi}")
                    return False
                created_docs.append((t_bi, url_bi))

            elif dual_lang_mode == "es_first":
                t_bi = f"{base_title} (Bilingual - ES/EN)"
                ok_bi, id_bi, url_bi = _export_single_doc(
                    t_bi, spanish_segments, "ES / EN",
                    sec_segs=english_segments, sec_title="English Translation", sec_lang="en"
                )
                if not ok_bi:
                    if progress_dialog: progress_dialog.close()
                    QMessageBox.critical(main_window, "Export Failed", f"Failed to create Bilingual Google Doc:\n{id_bi}")
                    return False
                created_docs.append((t_bi, url_bi))

        elif include_es and not include_en:
            t_es = base_title if src_code == "es" else f"{base_title} (Spanish)"
            ok_es, id_es, url_es = _export_single_doc(t_es, spanish_segments, "ES")
            if not ok_es:
                if progress_dialog: progress_dialog.close()
                QMessageBox.critical(main_window, "Export Failed", f"Failed to create Spanish Google Doc:\n{id_es}")
                return False
            created_docs.append((t_es, url_es))

        else:
            # English only
            t_en = base_title if src_code != "es" else f"{base_title} (English)"
            ok_en, id_en, url_en = _export_single_doc(t_en, english_segments, "EN")
            if not ok_en:
                if progress_dialog: progress_dialog.close()
                QMessageBox.critical(main_window, "Export Failed", f"Failed to create Google Doc:\n{id_en}")
                return False
            created_docs.append((t_en, url_en))

        if progress_dialog:
            progress_dialog.close()

        if open_browser:
            for _, doc_url in created_docs:
                webbrowser.open(doc_url)

        folder_info_msg = ""
        if target_folder_id:
            folder_info_msg = "\nSaved in Google Drive destination folder."

        docs_summary = "\n".join([f"• {t}" for t, _ in created_docs])
        QMessageBox.information(
            main_window,
            "Export Completed",
            f"Successfully exported transcript to Google Docs!\n\nDocuments:\n{docs_summary}{folder_info_msg}\n\nOpened in your web browser.",
        )
        return True

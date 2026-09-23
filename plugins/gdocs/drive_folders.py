"""Google Drive Folder Management Engine and Folder Selector Dialog.

Provides Google Drive API v3 interactions for:
- Querying and browsing folders in Google Drive
- Creating new folders directly in Google Drive
- Managing project-specific subfolders
- Interactive Qt folder picker dialog
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    class QDialog: pass  # type: ignore
    class QWidget: pass  # type: ignore


def extract_folder_id_from_input(text: str) -> str:
    """Extract Drive folder ID whether provided as raw ID or full Google Drive URL.
    
    Examples:
    - 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptnyt
    - https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptnyt
    - https://drive.google.com/drive/u/0/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptnyt?usp=sharing
    """
    if not text:
        return ""
    text = text.strip()
    # Match URL pattern
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", text)
    if match:
        return match.group(1)
    # Check if string looks like a standard Google ID (alphanumeric, dashes, underscores)
    if re.match(r"^[a-zA-Z0-9_-]{10,}$", text):
        return text
    return text


def list_drive_folders(
    access_token: str,
    parent_id: Optional[str] = None,
    page_size: int = 100,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """Retrieve folders from Google Drive via Drive API v3.
    
    Returns:
        (success, list_of_folders, error_message)
    """
    if not access_token:
        return False, [], "Missing access token"

    query_parts = ["mimeType = 'application/vnd.google-apps.folder'", "trashed = false"]
    if parent_id and parent_id.strip():
        pid = parent_id.strip()
        query_parts.append(f"'{pid}' in parents")

    q_str = " and ".join(query_parts)
    params = urllib.parse.urlencode({
        "q": q_str,
        "fields": "files(id, name, parents, modifiedTime)",
        "orderBy": "name",
        "pageSize": str(page_size),
    })
    url = f"https://www.googleapis.com/drive/v3/files?{params}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            folders = data.get("files", [])
            return True, folders, ""
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, [], f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, [], f"Drive API error: {e}"


def get_drive_folder_info(
    access_token: str,
    folder_id: str,
) -> Tuple[bool, Dict[str, Any], str]:
    """Get metadata for a specific folder ID."""
    if not access_token or not folder_id:
        return False, {}, "Missing token or folder ID"

    params = urllib.parse.urlencode({"fields": "id, name, mimeType, trashed"})
    url = f"https://www.googleapis.com/drive/v3/files/{urllib.parse.quote(folder_id)}?{params}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data, ""
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, {}, f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, {}, f"Drive API error: {e}"


def create_drive_folder(
    access_token: str,
    folder_name: str,
    parent_id: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """Create a new folder in Google Drive.
    
    Returns:
        (success, new_folder_id, error_message)
    """
    if not access_token:
        return False, "", "Missing access token"
    if not folder_name or not folder_name.strip():
        return False, "", "Folder name cannot be empty"

    clean_name = folder_name.strip()
    url = "https://www.googleapis.com/drive/v3/files?fields=id,name"
    payload: Dict[str, Any] = {
        "name": clean_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id and parent_id.strip():
        payload["parents"] = [parent_id.strip()]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            f_id = res_json.get("id", "")
            return True, f_id, ""
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, "", f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, "", f"Drive API error: {e}"


def get_or_create_project_subfolder(
    access_token: str,
    parent_folder_id: Optional[str],
    project_name: str,
) -> Tuple[bool, str, str]:
    """Find or create a dedicated project subfolder inside the target parent folder.
    
    Returns:
        (success, folder_id, error_message)
    """
    if not access_token:
        return False, "", "Missing access token"
    
    clean_name = re.sub(r'[\\/*?:"<>|]', "", project_name).strip() or "Broadcast Project"

    # Search if subfolder already exists
    escaped_name = clean_name.replace("'", "\\'")
    query_parts = [
        f"name = '{escaped_name}'",
        "mimeType = 'application/vnd.google-apps.folder'",
        "trashed = false",
    ]
    if parent_folder_id and parent_folder_id.strip():
        query_parts.append(f"'{parent_folder_id.strip()}' in parents")

    q_str = " and ".join(query_parts)
    params = urllib.parse.urlencode({
        "q": q_str,
        "fields": "files(id, name)",
        "pageSize": "5",
    })
    url = f"https://www.googleapis.com/drive/v3/files?{params}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            files = data.get("files", [])
            if files:
                return True, files[0]["id"], ""
    except Exception:
        pass

    # If not found, create new subfolder
    return create_drive_folder(access_token, clean_name, parent_id=parent_folder_id)


if PYSIDE_AVAILABLE:
    class DriveFolderPickerDialog(QDialog):
        """Dialog allowing users to browse, search, and pick or create Google Drive folders."""

        def __init__(
            self,
            parent: Optional[QWidget],
            access_token: str,
            current_folder_id: str = "",
            current_folder_name: str = "",
        ):
            super().__init__(parent)
            self.access_token = access_token
            self.selected_folder_id = current_folder_id
            self.selected_folder_name = current_folder_name or ("Root (My Drive)" if not current_folder_id else "Selected Folder")
            self._folders: List[Dict[str, Any]] = []

            self.setWindowTitle("Select Google Drive Folder")
            self.resize(520, 480)
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            self._setup_ui()
            self._load_folders()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(10)

            # Instruction / Search Bar
            info_lbl = QLabel("Choose a Google Drive folder for transcript exports, or create a new one:")
            info_lbl.setWordWrap(True)
            info_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(info_lbl)

            search_row = QHBoxLayout()
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("Filter folders by name…")
            self.search_edit.textChanged.connect(self._filter_list)
            search_row.addWidget(self.search_edit)

            self.refresh_btn = QPushButton("↻ Refresh")
            self.refresh_btn.clicked.connect(self._load_folders)
            search_row.addWidget(self.refresh_btn)
            layout.addLayout(search_row)

            # Folder list
            self.list_widget = QListWidget()
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 4px;
                    color: #f8fafc;
                }
                QListWidget::item {
                    padding: 8px 10px;
                    border-radius: 4px;
                }
                QListWidget::item:hover {
                    background-color: #1e293b;
                }
                QListWidget::item:selected {
                    background-color: #0284c7;
                    color: #ffffff;
                }
            """)
            self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
            self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
            layout.addWidget(self.list_widget, 1)

            # Manual ID / URL paste row
            paste_row = QHBoxLayout()
            paste_row.setSpacing(6)
            paste_lbl = QLabel("Or paste Folder URL / ID:")
            paste_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            self.paste_edit = QLineEdit()
            self.paste_edit.setPlaceholderText("https://drive.google.com/drive/folders/… or Folder ID")
            self.paste_edit.setText(self.selected_folder_id)
            self.paste_edit.textChanged.connect(self._on_paste_changed)
            paste_row.addWidget(paste_lbl)
            paste_row.addWidget(self.paste_edit, 1)
            layout.addLayout(paste_row)

            # Status label
            self.status_lbl = QLabel()
            self.status_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
            self._update_status_display()
            layout.addWidget(self.status_lbl)

            # Action Buttons Row
            btn_row = QHBoxLayout()
            self.new_folder_btn = QPushButton("+ Create New Folder…")
            self.new_folder_btn.clicked.connect(self._on_create_folder_clicked)
            btn_row.addWidget(self.new_folder_btn)

            self.root_btn = QPushButton("Use Root (My Drive)")
            self.root_btn.clicked.connect(self._select_root)
            btn_row.addWidget(self.root_btn)

            btn_row.addStretch()

            self.ok_btn = QPushButton("Select Folder")
            self.ok_btn.setDefault(True)
            self.ok_btn.clicked.connect(self._accept_selection)
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self.reject)

            btn_row.addWidget(self.ok_btn)
            btn_row.addWidget(self.cancel_btn)
            layout.addLayout(btn_row)

        def _update_status_display(self):
            if not self.selected_folder_id:
                self.status_lbl.setText("<b>Active Selection:</b> Root (My Drive)")
            else:
                self.status_lbl.setText(f"<b>Active Selection:</b> 📁 {self.selected_folder_name} (ID: {self.selected_folder_id})")

        def _load_folders(self):
            self.list_widget.clear()
            # Root entry at top
            root_item = QListWidgetItem("📁 Root (My Drive)")
            root_item.setData(Qt.ItemDataRole.UserRole, "")
            root_item.setData(Qt.ItemDataRole.UserRole + 1, "Root (My Drive)")
            self.list_widget.addItem(root_item)

            ok, folders, err = list_drive_folders(self.access_token)
            if not ok:
                err_item = QListWidgetItem(f"⚠ Could not list folders: {err}")
                err_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_widget.addItem(err_item)
                return

            self._folders = folders
            self._filter_list()

            # Restore selection if exists
            if self.selected_folder_id:
                for i in range(self.list_widget.count()):
                    item = self.list_widget.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.selected_folder_id:
                        self.list_widget.setCurrentItem(item)
                        break

        def _filter_list(self):
            filter_text = self.search_edit.text().strip().lower()
            self.list_widget.clear()

            # Always add Root
            root_item = QListWidgetItem("📁 Root (My Drive)")
            root_item.setData(Qt.ItemDataRole.UserRole, "")
            root_item.setData(Qt.ItemDataRole.UserRole + 1, "Root (My Drive)")
            self.list_widget.addItem(root_item)

            for f in self._folders:
                fname = f.get("name", "Untitled Folder")
                fid = f.get("id", "")
                if filter_text and filter_text not in fname.lower():
                    continue
                item = QListWidgetItem(f"📁 {fname}")
                item.setData(Qt.ItemDataRole.UserRole, fid)
                item.setData(Qt.ItemDataRole.UserRole + 1, fname)
                self.list_widget.addItem(item)

        def _on_selection_changed(self):
            items = self.list_widget.selectedItems()
            if items:
                fid = items[0].data(Qt.ItemDataRole.UserRole)
                fname = items[0].data(Qt.ItemDataRole.UserRole + 1)
                self.selected_folder_id = fid or ""
                self.selected_folder_name = fname or "Root (My Drive)"
                self.paste_edit.blockSignals(True)
                self.paste_edit.setText(self.selected_folder_id)
                self.paste_edit.blockSignals(False)
                self._update_status_display()

        def _on_item_double_clicked(self, item: QListWidgetItem):
            self._on_selection_changed()
            self._accept_selection()

        def _on_paste_changed(self, text: str):
            clean_id = extract_folder_id_from_input(text)
            self.selected_folder_id = clean_id
            if not clean_id:
                self.selected_folder_name = "Root (My Drive)"
            else:
                self.selected_folder_name = f"Custom Folder ({clean_id})"
            self._update_status_display()

        def _select_root(self):
            self.selected_folder_id = ""
            self.selected_folder_name = "Root (My Drive)"
            self.paste_edit.clear()
            self._update_status_display()
            self.accept()

        def _on_create_folder_clicked(self):
            name, ok = QInputDialog.getText(
                self,
                "New Google Drive Folder",
                "Enter folder name:",
                text="Radio & TV Segmenter Exports",
            )
            if not ok or not name.strip():
                return

            parent_id = self.selected_folder_id if self.selected_folder_id else None
            success, new_id, err = create_drive_folder(self.access_token, name.strip(), parent_id=parent_id)
            if not success:
                QMessageBox.critical(self, "Folder Creation Failed", f"Could not create folder:\n{err}")
                return

            QMessageBox.information(self, "Folder Created", f"Created folder '{name.strip()}' in Google Drive!")
            self.selected_folder_id = new_id
            self.selected_folder_name = name.strip()
            self._load_folders()
            self._update_status_display()

        def _accept_selection(self):
            clean_id = extract_folder_id_from_input(self.paste_edit.text())
            if clean_id:
                self.selected_folder_id = clean_id
            self.accept()
else:
    class DriveFolderPickerDialog:  # type: ignore
        """Headless fallback for DriveFolderPickerDialog when PySide6 is not present."""
        def __init__(self, *args, **kwargs):
            pass

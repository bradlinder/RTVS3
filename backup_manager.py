"""Unified State Serialization, Local, and Google Drive Cloud Backup & Restore Engine.

Provides cryptographically verified backup archiving (SHA-256), local archive export/import,
and 1-click Google Drive cloud backup and restoration for Radio & TV Story Segmenter.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core_utils import INTERNAL_APP_ID, make_dialog_maximizable

try:
    from prs_shared import PROJECT_VERSION
except Exception:
    PROJECT_VERSION = "3.8.0-stable"

logger = logging.getLogger(__name__)

BACKUP_FORMAT_IDENTIFIER = "RadioTVStorySegmenter-Backup"
BACKUP_SCHEMA_VERSION = "3.8.0"


def compute_data_checksum(data: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 checksum over normalized JSON serialization of data."""
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def serialize_preferences(settings_store=None) -> Dict[str, Any]:
    """Extracts all persistent preferences from QSettings while safely coercing values."""
    if settings_store is None:
        try:
            from PySide6.QtCore import QSettings
            settings_store = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        except Exception:
            return {}

    prefs: Dict[str, Any] = {}
    try:
        keys = settings_store.allKeys() if hasattr(settings_store, "allKeys") else []
        for k in keys:
            if k.startswith("keyboard_shortcuts/"):
                continue
            val = settings_store.value(k)
            if isinstance(val, (str, int, float, bool, list, dict)) or val is None:
                prefs[k] = val
            else:
                try:
                    prefs[k] = str(val)
                except Exception:
                    pass
    except Exception as exc:
        logger.warning(f"Error enumerating preferences: {exc}")
    return prefs


def serialize_keyboard_shortcuts(settings_store=None, shortcuts_mgr=None) -> Dict[str, str]:
    """Extracts custom keyboard shortcut keybindings from ShortcutsManager or QSettings."""
    shortcuts: Dict[str, str] = {}
    if shortcuts_mgr is not None and hasattr(shortcuts_mgr, "custom_shortcuts"):
        shortcuts = dict(shortcuts_mgr.custom_shortcuts)
    elif settings_store is not None:
        try:
            settings_store.beginGroup("keyboard_shortcuts")
            for k in settings_store.allKeys():
                shortcuts[k] = str(settings_store.value(k, ""))
            settings_store.endGroup()
        except Exception:
            pass
    else:
        try:
            from PySide6.QtCore import QSettings
            store = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            store.beginGroup("keyboard_shortcuts")
            for k in store.allKeys():
                shortcuts[k] = str(store.value(k, ""))
            store.endGroup()
        except Exception:
            pass
    return shortcuts


def serialize_glossary(settings_store=None) -> List[Dict[str, Any]]:
    """Extracts shared terminology glossary entries."""
    try:
        from terminology import load_glossary
        return load_glossary(settings_store=settings_store)
    except Exception:
        return []


def serialize_models_inventory() -> List[Dict[str, Any]]:
    """Extracts installed local model metadata."""
    models: List[Dict[str, Any]] = []
    try:
        from prs_shared import models_dir
        md = models_dir()
        if os.path.exists(md):
            for entry in sorted(os.listdir(md)):
                entry_path = os.path.join(md, entry)
                if os.path.isdir(entry_path):
                    size_mb = 0.0
                    try:
                        size_mb = round(
                            sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(entry_path) for f in fs)
                            / (1024 * 1024),
                            2,
                        )
                    except Exception:
                        pass
                    models.append({
                        "name": entry,
                        "type": "directory",
                        "size_mb": size_mb,
                    })
    except Exception:
        pass
    return models


def serialize_plugin_states(settings_store=None) -> Dict[str, Any]:
    """Extracts enabled states for installed plugins."""
    plugins_state: Dict[str, Any] = {}
    known_plugins = ["youtube", "wordpress", "gdocs", "translation"]
    if settings_store is None:
        try:
            from PySide6.QtCore import QSettings
            settings_store = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        except Exception:
            pass

    for pid in known_plugins:
        enabled = True
        if settings_store is not None:
            val = settings_store.value(f"plugin_{pid}_enabled", True)
            enabled = str(val).lower() in {"1", "true", "yes"} if isinstance(val, str) else bool(val)
        plugins_state[pid] = {"enabled": enabled}
    return plugins_state


def create_backup_payload(
    settings_store=None,
    shortcuts_mgr=None,
    main_window=None,
) -> Dict[str, Any]:
    """Creates a unified, cryptographically verified state backup payload dictionary."""
    data = {
        "preferences": serialize_preferences(settings_store),
        "keyboard_shortcuts": serialize_keyboard_shortcuts(settings_store, shortcuts_mgr),
        "glossary": serialize_glossary(settings_store),
        "models_inventory": serialize_models_inventory(),
        "plugins": serialize_plugin_states(settings_store),
    }

    checksum = compute_data_checksum(data)
    payload = {
        "format": BACKUP_FORMAT_IDENTIFIER,
        "schema_version": BACKUP_SCHEMA_VERSION,
        "app_version": PROJECT_VERSION,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": sys.platform,
        "archive_checksum": checksum,
        "data": data,
    }
    return payload


def verify_backup_payload(payload_raw: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Validates structure, format identifier, and SHA-256 cryptographic checksum."""
    if isinstance(payload_raw, (bytes, bytearray)):
        try:
            payload_raw = payload_raw.decode("utf-8")
        except Exception as exc:
            return False, f"Failed to decode payload bytes: {exc}", None

    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw)
        except Exception as exc:
            return False, f"Invalid JSON payload: {exc}", None
    elif isinstance(payload_raw, dict):
        payload = payload_raw
    else:
        return False, "Unsupported payload container", None

    if not isinstance(payload, dict):
        return False, "Backup payload root must be a JSON object", None

    fmt = payload.get("format")
    if fmt != BACKUP_FORMAT_IDENTIFIER:
        return False, f"Unrecognized backup format: '{fmt}' (expected '{BACKUP_FORMAT_IDENTIFIER}')", None

    expected_checksum = payload.get("archive_checksum")
    data = payload.get("data")
    if not isinstance(data, dict):
        return False, "Backup payload missing 'data' container", None

    computed_checksum = compute_data_checksum(data)
    if expected_checksum != computed_checksum:
        return (
            False,
            f"Cryptographic integrity failure: SHA-256 digest mismatch (computed {computed_checksum[:12]}..., expected {str(expected_checksum)[:12]}...)",
            None,
        )

    return True, "Integrity verified (SHA-256 match)", payload


def apply_backup_payload(
    payload: Dict[str, Any],
    main_window=None,
    settings_store=None,
    shortcuts_mgr=None,
) -> Tuple[bool, List[str]]:
    """Applies a verified backup payload to system settings, shortcuts, and glossary."""
    valid, msg, validated_payload = verify_backup_payload(payload)
    if not valid or not validated_payload:
        return False, [f"Validation error: {msg}"]

    data = validated_payload.get("data", {})
    restored_items: List[str] = []

    if settings_store is None:
        try:
            from PySide6.QtCore import QSettings
            settings_store = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        except Exception:
            pass

    # 1. Preferences
    prefs = data.get("preferences", {})
    if prefs and settings_store is not None:
        for k, v in prefs.items():
            try:
                settings_store.setValue(k, v)
            except Exception:
                pass
        if hasattr(settings_store, "sync"):
            settings_store.sync()
        restored_items.append(f"Preferences ({len(prefs)} keys restored)")

    # 2. Keyboard Shortcuts
    shortcuts = data.get("keyboard_shortcuts", {})
    if shortcuts is not None:
        if settings_store is not None:
            try:
                settings_store.beginGroup("keyboard_shortcuts")
                for k in settings_store.allKeys():
                    settings_store.remove(k)
                for k, v in shortcuts.items():
                    settings_store.setValue(k, v)
                settings_store.endGroup()
                if hasattr(settings_store, "sync"):
                    settings_store.sync()
            except Exception:
                pass
        if shortcuts_mgr is not None and hasattr(shortcuts_mgr, "reload_shortcuts"):
            try:
                shortcuts_mgr.reload_shortcuts()
                if hasattr(shortcuts_mgr, "shortcutsChanged"):
                    shortcuts_mgr.shortcutsChanged.emit()
            except Exception:
                pass
        restored_items.append(f"Keyboard Shortcuts ({len(shortcuts)} custom overrides restored)")

    # 3. Glossary
    glossary = data.get("glossary", [])
    if glossary is not None and settings_store is not None:
        try:
            settings_store.setValue("glossary", json.dumps(glossary))
            if hasattr(settings_store, "sync"):
                settings_store.sync()
        except Exception:
            pass
        if main_window is not None and hasattr(main_window, "refresh_glossary"):
            try:
                main_window.refresh_glossary()
            except Exception:
                pass
        restored_items.append(f"Glossary ({len(glossary)} entries restored)")

    # 4. Plugins
    plugins_data = data.get("plugins", {})
    if plugins_data and settings_store is not None:
        for pid, pconf in plugins_data.items():
            if isinstance(pconf, dict) and "enabled" in pconf:
                settings_store.setValue(f"plugin_{pid}_enabled", pconf["enabled"])
        if hasattr(settings_store, "sync"):
            settings_store.sync()
        restored_items.append(f"Plugin States ({len(plugins_data)} plugins configured)")

    # 5. Live UI Refresh
    if main_window is not None:
        if hasattr(main_window, "show_timestamps") and settings_store is not None:
            main_window.show_timestamps = str(settings_store.value("show_timestamps", "true")).lower() in {"1", "true", "yes"}
            if hasattr(main_window, "show_timestamps_action"):
                main_window.show_timestamps_action.setChecked(main_window.show_timestamps)
        if hasattr(main_window, "show_milliseconds") and settings_store is not None:
            main_window.show_milliseconds = str(settings_store.value("show_milliseconds", "false")).lower() in {"1", "true", "yes"}
            if hasattr(main_window, "show_milliseconds_action"):
                main_window.show_milliseconds_action.setChecked(main_window.show_milliseconds)
        if hasattr(main_window, "silence_threshold") and settings_store is not None:
            main_window.silence_threshold = float(settings_store.value("silence_threshold", 3.0) or 3.0)
        if hasattr(main_window, "lead_in_padding") and settings_store is not None:
            main_window.lead_in_padding = float(settings_store.value("lead_in_padding", 0.5) or 0.5)
        if hasattr(main_window, "story_detection_mode") and settings_store is not None:
            main_window.story_detection_mode = str(settings_store.value("story_detection_mode", "voice") or "voice")
            if hasattr(main_window, "update_story_segment_terminology"):
                try:
                    main_window.update_story_segment_terminology()
                except Exception:
                    pass
        if hasattr(main_window, "enable_audio_fades") and settings_store is not None:
            main_window.enable_audio_fades = str(settings_store.value("enable_audio_fades", "false")).lower() in {"1", "true", "yes"}
            if hasattr(main_window, "timeline") and hasattr(main_window.timeline, "canvas"):
                main_window.timeline.canvas.show_audio_fades = main_window.enable_audio_fades
                main_window.timeline.canvas.update()
        if hasattr(main_window, "preview_audio_fades") and settings_store is not None:
            main_window.preview_audio_fades = str(settings_store.value("preview_audio_fades", "false")).lower() in {"1", "true", "yes"}
        if hasattr(main_window, "skip_seconds") and settings_store is not None:
            try:
                main_window.skip_seconds = int(settings_store.value("skip_seconds", 5) or 5)
                if hasattr(main_window, "timeline"):
                    main_window.timeline.set_skip_seconds(main_window.skip_seconds)
            except Exception:
                pass
        if hasattr(main_window, "render_transcript"):
            try:
                main_window.render_transcript()
            except Exception:
                pass
        if hasattr(main_window, "log_activity"):
            main_window.log_activity(f"[SYSTEM] Restored backup archive ({', '.join(restored_items)})", mark_dirty=False)

    return True, restored_items


def export_local_backup(
    target_path: str | Path,
    settings_store=None,
    shortcuts_mgr=None,
    main_window=None,
) -> Tuple[bool, str]:
    """Writes a verified state backup archive to a local file."""
    try:
        payload = create_backup_payload(settings_store, shortcuts_mgr, main_window)
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(payload, indent=2, ensure_ascii=False)
        p.write_text(content, encoding="utf-8")
        return True, str(p)
    except Exception as exc:
        return False, str(exc)


def restore_local_backup(
    source_path: str | Path,
    main_window=None,
    settings_store=None,
    shortcuts_mgr=None,
) -> Tuple[bool, str, List[str]]:
    """Restores settings and configurations from a local backup file."""
    try:
        p = Path(source_path)
        if not p.is_file():
            return False, f"File does not exist: {p}", []
        raw_text = p.read_text(encoding="utf-8")
        valid, msg, payload = verify_backup_payload(raw_text)
        if not valid or not payload:
            return False, msg, []
        success, items = apply_backup_payload(
            payload,
            main_window=main_window,
            settings_store=settings_store,
            shortcuts_mgr=shortcuts_mgr,
        )
        if not success:
            return False, f"Failed to restore items: {', '.join(items)}", []
        return True, "Backup successfully restored", items
    except Exception as exc:
        return False, str(exc), []


# --- Google Drive Cloud Backup & Restore Integration ---

def _get_gdocs_auth_manager():
    """Dynamically resolves GoogleDocsAuthManager for Google Drive API operations."""
    try:
        from plugins.gdocs.auth import GoogleDocsAuthManager
        return GoogleDocsAuthManager()
    except Exception:
        return None


def list_cloud_backups(auth_manager=None) -> Tuple[bool, List[Dict[str, Any]], str]:
    """Queries Google Drive API v3 for RTVS backup archives."""
    if auth_manager is None:
        auth_manager = _get_gdocs_auth_manager()
    if not auth_manager or not auth_manager.is_authenticated():
        return False, [], "Google account not authenticated. Please sign in via the Google Docs plugin."

    token = auth_manager.get_valid_access_token()
    if not token:
        return False, [], "Failed to acquire valid Google Drive access token."

    query = "(name contains 'rtvs_settings_' or name contains 'rtvs_backup_') and trashed = false"
    params = urllib.parse.urlencode({
        "q": query,
        "fields": "files(id, name, size, createdTime, modifiedTime, description)",
        "orderBy": "createdTime desc",
        "pageSize": "50",
    })
    url = f"https://www.googleapis.com/drive/v3/files?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            files = data.get("files", [])
            return True, files, ""
    except Exception as exc:
        return False, [], f"Google Drive API query failed: {exc}"


def upload_cloud_backup(
    payload: Dict[str, Any],
    auth_manager=None,
    custom_name: str = "",
) -> Tuple[bool, str, str]:
    """Uploads a settings payload directly to Google Drive via multipart API."""
    if auth_manager is None:
        auth_manager = _get_gdocs_auth_manager()
    if not auth_manager or not auth_manager.is_authenticated():
        return False, "", "Google account not authenticated."

    token = auth_manager.get_valid_access_token()
    if not token:
        return False, "", "Failed to obtain valid Google Drive access token."

    checksum = payload.get("archive_checksum", "")
    app_ver = payload.get("app_version", PROJECT_VERSION)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = custom_name.strip() or f"rtvs_settings_{ts}.rtvs-settings"
    if not any(filename.endswith(ext) for ext in (".rtvs-settings", ".rtvs-preferences", ".rtvs-backup")):
        filename += ".rtvs-settings"

    description = f"RTVS System Settings v{app_ver} | SHA-256: {checksum}"
    metadata = {
        "name": filename,
        "mimeType": "application/json",
        "description": description,
    }

    payload_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    boundary = f"=====RTVS_BACKUP_BOUNDARY_{int(time.time())}====="
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: application/json\r\n\r\n"
    ).encode("utf-8") + payload_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", f"multipart/related; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            file_id = res_data.get("id", "")
            return True, file_id, ""
    except Exception as exc:
        return False, "", f"Drive upload failed: {exc}"


def download_cloud_backup(file_id: str, auth_manager=None) -> Tuple[bool, Dict[str, Any], str]:
    """Downloads and verifies an RTVS backup from Google Drive."""
    if auth_manager is None:
        auth_manager = _get_gdocs_auth_manager()
    if not auth_manager or not auth_manager.is_authenticated():
        return False, {}, "Google account not authenticated."

    token = auth_manager.get_valid_access_token()
    if not token:
        return False, {}, "Missing valid access token."

    url = f"https://www.googleapis.com/drive/v3/files/{urllib.parse.quote(file_id)}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_bytes = resp.read()
            valid, msg, payload = verify_backup_payload(content_bytes)
            if not valid or not payload:
                return False, {}, f"Cloud backup integrity check failed: {msg}"
            return True, payload, ""
    except Exception as exc:
        return False, {}, f"Drive download failed: {exc}"


def restore_cloud_backup(
    file_id: str,
    auth_manager=None,
    main_window=None,
    settings_store=None,
) -> Tuple[bool, str, List[str]]:
    """Restores system configuration directly from a Google Drive cloud backup."""
    ok, payload, err = download_cloud_backup(file_id, auth_manager=auth_manager)
    if not ok:
        return False, err, []
    success, restored_items = apply_backup_payload(
        payload,
        main_window=main_window,
        settings_store=settings_store,
    )
    if not success:
        return False, f"Failed applying restored state: {', '.join(restored_items)}", []
    return True, f"Successfully restored {len(restored_items)} configuration groups from cloud backup", restored_items


# --- PySide6 Backup & Restore Center Dialog ---

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTabWidget,
        QWidget,
        QFileDialog,
        QMessageBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QGroupBox,
        QTextEdit,
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False


if HAS_QT:
    class BackupRestoreDialog(QDialog):
        """Unified Modal Dialog for Local and Google Drive Cloud Backup & Restore."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.main_window = parent
            self.auth_manager = _get_gdocs_auth_manager()
            self.setWindowTitle("Backup & Restore Center")
            self.setMinimumSize(720, 520)
            self.resize(780, 580)
            make_dialog_maximizable(self)
            self._setup_ui()
            self._refresh_local_summary()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Header
            header_lbl = QLabel("<h2>Backup & Restore Center</h2>")
            header_lbl.setStyleSheet("color: #38bdf8; margin-bottom: 2px;")
            layout.addWidget(header_lbl)

            desc_lbl = QLabel(
                "Export, preserve, and restore all application configurations, custom keyboard shortcuts, "
                "glossary dictionaries, and plugin states locally or seamlessly through Google Drive cloud backups."
            )
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
            layout.addWidget(desc_lbl)

            # Tabs
            self.tabs = QTabWidget(self)
            self.local_tab = QWidget()
            self.cloud_tab = QWidget()
            self.tabs.addTab(self.local_tab, "Local Archive")
            self.tabs.addTab(self.cloud_tab, "Google Drive")
            layout.addWidget(self.tabs)

            self._build_local_tab()
            self._build_cloud_tab()

            # Close button
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            btn_row.addWidget(close_btn)
            layout.addLayout(btn_row)

        def _build_local_tab(self):
            layout = QVBoxLayout(self.local_tab)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(12)

            # Current state summary card
            self.summary_box = QGroupBox("Active System State Summary")
            box_layout = QVBoxLayout(self.summary_box)
            self.summary_label = QLabel("Analyzing current state...")
            self.summary_label.setStyleSheet("color: #cbd5e1; font-size: 13px;")
            box_layout.addWidget(self.summary_label)
            layout.addWidget(self.summary_box)

            # Actions Box
            actions_box = QGroupBox("Local Archive Actions")
            act_layout = QHBoxLayout(actions_box)
            act_layout.setSpacing(12)

            self.btn_export_local = QPushButton("Create Local Settings File (.rtvs-settings)...")
            self.btn_export_local.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px;")
            self.btn_export_local.clicked.connect(self._on_export_local)
            act_layout.addWidget(self.btn_export_local)

            self.btn_restore_local = QPushButton("Restore from Settings File...")
            self.btn_restore_local.setStyleSheet("background-color: #334155; color: white; font-weight: bold; padding: 8px 14px;")
            self.btn_restore_local.clicked.connect(self._on_restore_local)
            act_layout.addWidget(self.btn_restore_local)

            self.btn_restore_defaults = QPushButton("Restore System Defaults…")
            self.btn_restore_defaults.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 8px 14px;")
            self.btn_restore_defaults.setToolTip("Reset system preferences, shortcuts, and configurations back to factory defaults.")
            def _on_restore_defaults_clicked():
                if self.main_window and hasattr(self.main_window, "open_restore_system_defaults_dialog"):
                    self.main_window.open_restore_system_defaults_dialog()
                    self._refresh_local_summary()
            self.btn_restore_defaults.clicked.connect(_on_restore_defaults_clicked)
            act_layout.addWidget(self.btn_restore_defaults)

            layout.addWidget(actions_box)

            # Status log
            layout.addWidget(QLabel("<b>Operation Log & Verification:</b>"))
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setStyleSheet("background-color: #0f172a; color: #cbd5e1; font-family: monospace; font-size: 11px;")
            layout.addWidget(self.log_text)

        def _build_cloud_tab(self):
            layout = QVBoxLayout(self.cloud_tab)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(12)

            # Auth Status Card
            auth_box = QGroupBox("Google Account Connection")
            auth_layout = QHBoxLayout(auth_box)
            self.cloud_auth_label = QLabel("Checking Google authentication...")
            self.cloud_auth_label.setStyleSheet("color: #cbd5e1; font-size: 13px;")
            auth_layout.addWidget(self.cloud_auth_label)

            self.btn_cloud_refresh = QPushButton("Refresh Cloud List")
            self.btn_cloud_refresh.clicked.connect(self._refresh_cloud_list)
            auth_layout.addWidget(self.btn_cloud_refresh)
            layout.addWidget(auth_box)

            # Cloud Actions Row
            act_row = QHBoxLayout()
            self.btn_upload_cloud = QPushButton("Backup to Google Drive...")
            self.btn_upload_cloud.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 14px;")
            self.btn_upload_cloud.clicked.connect(self._on_upload_cloud)
            act_row.addWidget(self.btn_upload_cloud)

            self.btn_restore_cloud = QPushButton("Restore Selected Cloud Backup")
            self.btn_restore_cloud.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 8px 14px;")
            self.btn_restore_cloud.clicked.connect(self._on_restore_cloud)
            act_row.addWidget(self.btn_restore_cloud)
            act_row.addStretch()
            layout.addLayout(act_row)

            # Cloud Backups Table
            self.cloud_table = QTableWidget(0, 4)
            self.cloud_table.setHorizontalHeaderLabels(["Backup Filename", "Created Date", "Size", "SHA-256 Digest"])
            self.cloud_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.cloud_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.cloud_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.cloud_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.cloud_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.cloud_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            layout.addWidget(self.cloud_table)

        def _refresh_local_summary(self):
            prefs = serialize_preferences()
            shortcuts = serialize_keyboard_shortcuts()
            glossary = serialize_glossary()
            models = serialize_models_inventory()
            plugins = serialize_plugin_states()

            summary = (
                f"• Preferences: <b>{len(prefs)}</b> persistent keys\n"
                f"• Custom Keyboard Shortcuts: <b>{len(shortcuts)}</b> overrides\n"
                f"• Glossary Rules: <b>{len(glossary)}</b> custom terms\n"
                f"• Downloaded Models: <b>{len(models)}</b> model packages\n"
                f"• Active Plugins: <b>{len(plugins)}</b> extensions"
            )
            self.summary_label.setText(summary)
            self._update_cloud_auth_status()

        def _update_cloud_auth_status(self):
            if self.auth_manager and self.auth_manager.is_authenticated():
                email = self.auth_manager.get_authenticated_email() or "Connected Account"
                self.cloud_auth_label.setText(f"Connected to Google Drive: <b>{email}</b>")
                self.btn_upload_cloud.setEnabled(True)
                self.btn_cloud_refresh.setEnabled(True)
            else:
                self.cloud_auth_label.setText("Not signed into Google. Connect via Google Docs / Drive plugin.")
                self.btn_upload_cloud.setEnabled(False)
                self.btn_restore_cloud.setEnabled(False)

        def _on_export_local(self):
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            default_name = f"RTVS_Settings_{now_str}.rtvs-settings"
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Local Settings File",
                default_name,
                "RTVS Settings (*.rtvs-settings *.rtvs-preferences *.rtvs-backup);;JSON Files (*.json);;All Files (*)",
            )
            if not save_path:
                return

            ok, err = export_local_backup(save_path, main_window=self.main_window)
            if ok:
                payload = create_backup_payload(main_window=self.main_window)
                cs = payload.get("archive_checksum", "")
                self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Exported settings file: {save_path}")
                self.log_text.append(f"       SHA-256 Digest: {cs}")
                QMessageBox.information(
                    self,
                    "Settings Export Complete",
                    f"Successfully created verified settings archive:\n\n{save_path}\n\nSHA-256 Digest: {cs[:16]}...",
                )
            else:
                self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Export failed: {err}")
                QMessageBox.critical(self, "Export Failed", f"Failed to export settings:\n{err}")

        def _on_restore_local(self):
            open_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select RTVS Settings File",
                "",
                "RTVS Settings (*.rtvs-settings *.rtvs-preferences *.rtvs-backup);;JSON Files (*.json);;All Files (*)",
            )
            if not open_path:
                return

            try:
                raw_text = Path(open_path).read_text(encoding="utf-8")
                valid, msg, payload = verify_backup_payload(raw_text)
                if not valid or not payload:
                    QMessageBox.critical(self, "Integrity Verification Failed", f"Invalid settings file:\n{msg}")
                    return

                data = payload.get("data", {})
                p_count = len(data.get("preferences", {}))
                s_count = len(data.get("keyboard_shortcuts", {}))
                g_count = len(data.get("glossary", []))
                cs = payload.get("archive_checksum", "")[:16]

                confirm = QMessageBox.question(
                    self,
                    "Confirm State Restore",
                    f"Verified settings from v{payload.get('app_version', 'unknown')} ({payload.get('created_at', '')[:10]}):\n\n"
                    f"• {p_count} Preferences\n"
                    f"• {s_count} Custom Keyboard Shortcuts\n"
                    f"• {g_count} Glossary Entries\n"
                    f"• Cryptographic SHA-256: {cs}...\n\n"
                    "Would you like to restore this configuration into the application?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return

                ok, items = apply_backup_payload(payload, main_window=self.main_window)
                if ok:
                    self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Restored settings from {open_path}")
                    for it in items:
                        self.log_text.append(f"       + {it}")
                    self._refresh_local_summary()
                    QMessageBox.information(
                        self,
                        "Restore Successful",
                        f"State successfully restored:\n\n• " + "\n• ".join(items),
                    )
                else:
                    err_msg = ", ".join(items) if items else "Unknown restore error"
                    self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Restore failed: {err_msg}")
                    QMessageBox.critical(self, "Restore Failed", f"Restore error:\n{err_msg}")
            except Exception as exc:
                QMessageBox.critical(self, "Restore Error", f"Unexpected error reading backup:\n{exc}")

        def _refresh_cloud_list(self):
            self._update_cloud_auth_status()
            if not self.auth_manager or not self.auth_manager.is_authenticated():
                return

            self.cloud_table.setRowCount(0)
            ok, files, err = list_cloud_backups(self.auth_manager)
            if not ok:
                QMessageBox.warning(self, "Cloud Query Failed", f"Could not list Google Drive backups:\n{err}")
                return

            self.cloud_table.setRowCount(len(files))
            for row, f in enumerate(files):
                fid = f.get("id", "")
                name = f.get("name", "")
                created = f.get("createdTime", "")[:19].replace("T", " ")
                size_str = f"{int(f.get('size', 0)) / 1024:.1f} KB" if f.get("size") else "N/A"
                desc = f.get("description", "")
                cs = desc.split("SHA-256:")[-1].strip()[:16] if "SHA-256:" in desc else "Verified"

                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.ItemDataRole.UserRole, fid)
                self.cloud_table.setItem(row, 0, name_item)
                self.cloud_table.setItem(row, 1, QTableWidgetItem(created))
                self.cloud_table.setItem(row, 2, QTableWidgetItem(size_str))
                self.cloud_table.setItem(row, 3, QTableWidgetItem(cs))

            self.btn_restore_cloud.setEnabled(len(files) > 0)

        def _on_upload_cloud(self):
            if not self.auth_manager or not self.auth_manager.is_authenticated():
                QMessageBox.warning(self, "Authentication Required", "Please connect to Google first.")
                return

            payload = create_backup_payload(main_window=self.main_window)
            ok, fid, err = upload_cloud_backup(payload, auth_manager=self.auth_manager)
            if ok:
                cs = payload.get("archive_checksum", "")[:16]
                QMessageBox.information(
                    self,
                    "Cloud Backup Uploaded",
                    f"Successfully uploaded verified backup to Google Drive!\n\nFile ID: {fid}\nSHA-256: {cs}...",
                )
                self._refresh_cloud_list()
            else:
                QMessageBox.critical(self, "Cloud Upload Failed", f"Failed uploading backup to Google Drive:\n{err}")

        def _on_restore_cloud(self):
            row = self.cloud_table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Selection Required", "Please select a cloud backup from the table.")
                return

            name_item = self.cloud_table.item(row, 0)
            if not name_item:
                return
            file_id = name_item.data(Qt.ItemDataRole.UserRole)
            backup_name = name_item.text()

            confirm = QMessageBox.question(
                self,
                "Restore Cloud Backup",
                f"Are you sure you want to download and restore configuration from Google Drive backup:\n\n{backup_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            ok, status_msg, items = restore_cloud_backup(
                file_id,
                auth_manager=self.auth_manager,
                main_window=self.main_window,
            )
            if ok:
                self._refresh_local_summary()
                QMessageBox.information(
                    self,
                    "Cloud Restore Successful",
                    f"Cloud configuration restored successfully:\n\n• " + "\n• ".join(items),
                )
            else:
                QMessageBox.critical(self, "Cloud Restore Failed", f"Restore error:\n{status_msg}")

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

try:
    from core_utils import INTERNAL_APP_ID, make_dialog_maximizable, PROJECT_VERSION
except ImportError:
    try:
        from prs_shared import INTERNAL_APP_ID, make_dialog_maximizable, PROJECT_VERSION
    except Exception:
        INTERNAL_APP_ID = "RadioTVStorySegmenter"
        PROJECT_VERSION = "3.9.51-beta"
        def make_dialog_maximizable(dlg): pass

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
        md = None
        try:
            from core_utils import get_models_storage_dir
            md = str(get_models_storage_dir())
        except (ImportError, AttributeError):
            pass

        if not md:
            try:
                from prs_shared import models_dir
                md = str(models_dir())
            except Exception:
                pass

        if md and os.path.exists(md):
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
    known_plugins = ["youtube", "wordpress", "translation"]
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
        QGroupBox,
        QTextEdit,
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False


if HAS_QT:
    class BackupRestoreDialog(QDialog):
        """Modal Dialog for Local System Settings Backup & Restore."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.main_window = parent
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
                "glossary dictionaries, and plugin states using cryptographically verified local archive files."
            )
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
            layout.addWidget(desc_lbl)

            # Tabs
            self.tabs = QTabWidget(self)
            self.local_tab = QWidget()
            self.tabs.addTab(self.local_tab, "Local Archive")
            layout.addWidget(self.tabs)

            self._build_local_tab()

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

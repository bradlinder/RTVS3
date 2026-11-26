"""Qt Dialog for inspecting and managing the Managed Remote Media Cache (YouTube & WordPress)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from prs_shared import INTERNAL_APP_ID
from remote_media_cache import (
    CACHE_CAP_SETTING_KEY,
    DEFAULT_CACHE_CAP_GB,
    RemoteMediaCacheManager,
    format_bytes_human,
)

CACHE_CAP_OPTIONS: List[Tuple[str, float]] = [
    ("2 GB", 2.0),
    ("5 GB", 5.0),
    ("10 GB (Default)", 10.0),
    ("25 GB", 25.0),
    ("50 GB", 50.0),
    ("100 GB", 100.0),
    ("Unlimited", 0.0),
]


def get_configured_cache_cap_gb(settings_store: Optional[QSettings] = None) -> float:
    """Read the user's configured Remote Media Cache limit in GB (0.0 = Unlimited)."""
    store = settings_store or QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    raw = store.value(CACHE_CAP_SETTING_KEY, DEFAULT_CACHE_CAP_GB)
    try:
        val = float(raw)
        return val if val >= 0.0 else DEFAULT_CACHE_CAP_GB
    except (TypeError, ValueError):
        return DEFAULT_CACHE_CAP_GB


class ManageCachedMediaDialog(QDialog):
    """Inspect, cap, and manually prune cached YouTube and WordPress remote downloads."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        main_window: Any = None,
        cache_manager: Optional[RemoteMediaCacheManager] = None,
    ):
        super().__init__(parent)
        self.main_window = main_window or parent
        self.cache_manager = cache_manager or RemoteMediaCacheManager()
        self.settings = getattr(self.main_window, "settings_store", None) or QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

        self.setWindowTitle("Manage Cached Remote Media")
        self.setMinimumSize(720, 460)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self._entries: List[dict] = []
        self._build_ui()
        self.refresh_table()

    def _active_protected_paths(self) -> List[str]:
        out: List[str] = []
        audio_f = getattr(self.main_window, "audio_file", None)
        if audio_f:
            try:
                out.append(str(Path(audio_f).resolve()))
            except Exception:
                out.append(str(audio_f))
        return out

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        intro = QLabel(
            "<b>Managed Remote Media Cache</b><br>"
            "<span style='color: #64748b; font-size: 11px;'>"
            "Stores video and audio downloaded from YouTube and WordPress. User-owned local recordings "
            "are never touched, and cleared remote files can be re-downloaded when reopening a saved .rtvs project.</span>"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Summary + Cap row
        top_row = QHBoxLayout()
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        top_row.addWidget(self.summary_label, 1)

        cap_lbl = QLabel("Cache Size Limit:")
        self.cap_combo = QComboBox()
        for label, val in CACHE_CAP_OPTIONS:
            self.cap_combo.addItem(label, val)
        curr_cap = get_configured_cache_cap_gb(self.settings)
        matched_idx = -1
        for i in range(self.cap_combo.count()):
            if abs(float(self.cap_combo.itemData(i)) - curr_cap) < 0.01:
                matched_idx = i
                break
        if matched_idx >= 0:
            self.cap_combo.setCurrentIndex(matched_idx)
        else:
            self.cap_combo.addItem(f"{curr_cap:g} GB (Custom)", curr_cap)
            self.cap_combo.setCurrentIndex(self.cap_combo.count() - 1)
        self.cap_combo.currentIndexChanged.connect(self._on_cap_changed)

        top_row.addWidget(cap_lbl)
        top_row.addWidget(self.cap_combo)
        layout.addLayout(top_row)

        # Entries table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Title", "Source", "Quality", "Size", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for col in (1, 2, 3, 4):
                hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        # Plugin-provided maintenance actions (e.g. Check / Update yt-dlp) — decoupled from plugins/
        plugin_actions = self._collect_plugin_maintenance_actions()
        if plugin_actions:
            tools_row = QHBoxLayout()
            tools_lbl = QLabel("Downloader Tools:")
            tools_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            tools_row.addWidget(tools_lbl)
            for lbl, cb in plugin_actions:
                btn = QPushButton(lbl)
                btn.clicked.connect(lambda _checked=False, fn=cb: fn(self))
                tools_row.addWidget(btn)
            tools_row.addStretch()
            layout.addLayout(tools_row)

        # Action buttons
        btn_row = QHBoxLayout()
        self.delete_sel_btn = QPushButton("Delete Selected")
        self.delete_sel_btn.clicked.connect(self._on_delete_selected)
        btn_row.addWidget(self.delete_sel_btn)

        self.clear_exported_btn = QPushButton("Clear Exported Media")
        self.clear_exported_btn.setToolTip("Delete cached files that have already been exported, keeping unexported and currently open files.")
        self.clear_exported_btn.clicked.connect(self._on_clear_exported)
        btn_row.addWidget(self.clear_exported_btn)

        self.clear_all_btn = QPushButton("Clear All Unused Cache")
        self.clear_all_btn.setToolTip("Delete all cached remote downloads except the file currently open in the editor.")
        self.clear_all_btn.clicked.connect(self._on_clear_all)
        btn_row.addWidget(self.clear_all_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _collect_plugin_maintenance_actions(self) -> List[Tuple[str, Callable]]:
        actions: List[Tuple[str, Callable]] = []
        pm = getattr(self.main_window, "plugin_manager", None)
        if not pm or not hasattr(pm, "plugins"):
            return actions
        for plugin in pm.plugins.values():
            try:
                if not pm.is_plugin_enabled(plugin.id):
                    continue
                getter = getattr(plugin, "get_cache_maintenance_actions", None)
                if callable(getter):
                    for item in getter() or []:
                        if isinstance(item, tuple) and len(item) == 2 and callable(item[1]):
                            actions.append(item)
            except Exception:
                continue
        return actions

    def refresh_table(self) -> None:
        cap_gb = float(self.cap_combo.currentData() or 0.0)
        stats = self.cache_manager.get_stats(cap_gb=cap_gb)
        self._entries = self.cache_manager.list_entries()

        protected = set()
        for p in self._active_protected_paths():
            try:
                protected.add(str(Path(p).resolve()).lower())
            except Exception:
                protected.add(str(p).lower())

        cap_str = f"{cap_gb:g} GB" if cap_gb > 0 else "Unlimited"
        by_p = stats.get("by_provider", {})
        yt_b = by_p.get("youtube", {}).get("bytes", 0)
        wp_b = by_p.get("wordpress", {}).get("bytes", 0)
        self.summary_label.setText(
            f"<b>{stats['count']} cached file(s)</b> — "
            f"{format_bytes_human(stats['total_bytes'])} used of {cap_str} "
            f"(YouTube: {format_bytes_human(yt_b)}, WordPress: {format_bytes_human(wp_b)})"
        )

        self.table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            fp_low = str(entry.get("file_path") or "").lower()
            is_active = fp_low in protected
            is_exported = bool(entry.get("last_exported_at"))
            if is_active:
                status_str = "In Use (Protected)"
            elif is_exported:
                status_str = "Exported"
            else:
                status_str = "Cached"

            prov_raw = str(entry.get("provider") or "remote")
            prov_disp = {"youtube": "YouTube", "wordpress": "WordPress"}.get(prov_raw, prov_raw.title())
            qual_disp = str(entry.get("quality_preset") or "Default")

            title_item = QTableWidgetItem(str(entry.get("title") or entry.get("filename") or ""))
            title_item.setData(Qt.ItemDataRole.UserRole, entry.get("cache_key", ""))
            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, QTableWidgetItem(prov_disp))
            self.table.setItem(row, 2, QTableWidgetItem(qual_disp))
            self.table.setItem(row, 3, QTableWidgetItem(format_bytes_human(entry.get("size_bytes", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(status_str))

        has_entries = len(self._entries) > 0
        has_exported = any(bool(e.get("last_exported_at")) for e in self._entries)
        self.delete_sel_btn.setEnabled(has_entries)
        self.clear_exported_btn.setEnabled(has_exported)
        self.clear_all_btn.setEnabled(has_entries)

    def _on_cap_changed(self) -> None:
        cap_gb = float(self.cap_combo.currentData() or 0.0)
        self.settings.setValue(CACHE_CAP_SETTING_KEY, cap_gb)
        self.settings.sync()
        if cap_gb > 0:
            res = self.cache_manager.enforce_size_cap(cap_gb, protected_paths=self._active_protected_paths())
            if res.get("deleted_count", 0) > 0:
                QMessageBox.information(
                    self,
                    "Cache Limit Applied",
                    f"Removed {res['deleted_count']} older cached file(s) ({format_bytes_human(res['freed_bytes'])} freed) "
                    f"to fit within the {cap_gb:g} GB cache limit.",
                )
        self.refresh_table()

    def _on_delete_selected(self) -> None:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not rows:
            QMessageBox.information(self, "No Selection", "Select one or more cached files to delete.")
            return
        keys = []
        for r in rows:
            item = self.table.item(r, 0)
            if item is not None:
                k = item.data(Qt.ItemDataRole.UserRole)
                if k:
                    keys.append(str(k))
        if not keys:
            return
        ans = QMessageBox.question(
            self,
            "Delete Selected Cached Media",
            f"Delete {len(keys)} selected cached media file(s) from disk?\n\n"
            "Your .rtvs project transcripts, stories, and metadata will remain intact, and the media can be re-downloaded later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        protected = self._active_protected_paths()
        deleted = 0
        freed = 0
        skipped: List[str] = []
        for key in keys:
            ok, sz, err = self.cache_manager.delete_entry(key, protected_paths=protected)
            if ok:
                deleted += 1
                freed += sz
            elif err:
                skipped.append(err)

        self.refresh_table()
        msg = f"Deleted {deleted} file(s) ({format_bytes_human(freed)} freed)."
        if skipped:
            msg += "\n\nSkipped:\n" + "\n".join(f"- {s}" for s in skipped[:5])
        QMessageBox.information(self, "Cache Updated", msg)

    def _on_clear_exported(self) -> None:
        ans = QMessageBox.question(
            self,
            "Clear Exported Cached Media",
            "Delete all cached remote downloads that have already been exported (excluding any file currently open)?\n\n"
            "You can still re-download any episode later when reopening its .rtvs project.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        res = self.cache_manager.clear_cache(exported_only=True, protected_paths=self._active_protected_paths())
        self.refresh_table()
        QMessageBox.information(
            self,
            "Exported Media Cleared",
            f"Cleared {res['deleted_count']} exported cached file(s) ({format_bytes_human(res['freed_bytes'])} freed).",
        )

    def _on_clear_all(self) -> None:
        ans = QMessageBox.question(
            self,
            "Clear All Unused Cached Media",
            "Delete all cached YouTube and WordPress media files except the currently open project's file?\n\n"
            "Your saved .rtvs projects keep their transcripts, stories, and re-download source links.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        res = self.cache_manager.clear_cache(exported_only=False, protected_paths=self._active_protected_paths())
        self.refresh_table()
        QMessageBox.information(
            self,
            "Remote Media Cache Cleared",
            f"Cleared {res['deleted_count']} cached file(s) ({format_bytes_human(res['freed_bytes'])} freed).",
        )


def find_redownload_provider(main_window: Any, source_meta: dict) -> Any:
    """Locate an enabled plugin capable of re-downloading ``source_meta`` (decoupled from plugins/)."""
    if not isinstance(source_meta, dict) or not source_meta.get("provider"):
        return None
    pm = getattr(main_window, "plugin_manager", None)
    if not pm or not hasattr(pm, "plugins"):
        return None
    for plugin in pm.plugins.values():
        try:
            if not pm.is_plugin_enabled(plugin.id):
                continue
            can_fn = getattr(plugin, "can_redownload_remote_source", None)
            if callable(can_fn) and can_fn(source_meta):
                return plugin
        except Exception:
            continue
    return None


def reattach_downloaded_media_to_project(main_window: Any, media_path: Path | str) -> bool:
    """Bind a newly re-downloaded remote media file onto an already-loaded .rtvs project."""
    if not main_window or not media_path:
        return False
    p = Path(media_path).expanduser().resolve()
    if not p.exists():
        return False

    from PySide6.QtCore import QUrl
    main_window.audio_file = p
    main_window.current_media_is_video = p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi"}
    if hasattr(main_window, "player") and hasattr(main_window.player, "setSource"):
        main_window.player.setSource(QUrl.fromLocalFile(str(p)))
    if hasattr(main_window, "timeline") and hasattr(main_window.timeline, "set_audio_filename"):
        main_window.timeline.set_audio_filename(p.name)
    if hasattr(main_window, "update_video_preview_state"):
        main_window.update_video_preview_state()
    if hasattr(main_window, "load_waveform_async"):
        main_window.load_waveform_async()
    if getattr(main_window, "current_media_is_video", False) and hasattr(main_window, "start_video_thumbnail_generation"):
        main_window.start_video_thumbnail_generation()
    if hasattr(main_window, "update_processing_menu_status"):
        main_window.update_processing_menu_status()
    if hasattr(main_window, "statusBar"):
        main_window.statusBar().showMessage(f"Source media restored: {p.name}")
    return True


def prompt_redownload_missing_remote_media(
    main_window: Any,
    source_meta: dict,
    parent: Optional[QWidget] = None,
) -> bool:
    """Offer 1-click re-download when an opened .rtvs project's cached remote media is missing."""
    if not isinstance(source_meta, dict) or not source_meta.get("provider"):
        return False
    provider_label = {"youtube": "YouTube", "wordpress": "WordPress"}.get(
        str(source_meta.get("provider") or "").lower(),
        str(source_meta.get("provider") or "Remote Source").title(),
    )
    title = str(source_meta.get("title") or source_meta.get("source_url") or "this episode")
    quality = str(source_meta.get("quality_preset") or "default")
    provider_plugin = find_redownload_provider(main_window, source_meta)

    box = QMessageBox(parent or main_window)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle("Cached Source Media Cleared")
    box.setText(
        f"This project loaded cleanly with all transcripts, stories, and metadata intact, "
        f"but its cached {provider_label} media file is no longer on disk."
    )
    if provider_plugin is not None:
        box.setInformativeText(
            f"Source: {title}\nQuality preset: {quality}\n\n"
            f"You can keep editing text and embeds without media, or re-download the source file from {provider_label} now."
        )
        redl_btn = box.addButton(f"Re-download from {provider_label}", QMessageBox.ButtonRole.AcceptRole)
        keep_btn = box.addButton("Continue Without Media", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(redl_btn)
        box.exec()
        if box.clickedButton() == redl_btn:
            restored = provider_plugin.redownload_remote_source(source_meta, parent=parent or main_window)
            if restored:
                return reattach_downloaded_media_to_project(main_window, restored)
        return False
    else:
        box.setInformativeText(
            f"Enable the {provider_label} plugin under Tools > Manage Plugins & Add-ons to re-download this episode automatically."
        )
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        return False


__all__ = [
    "CACHE_CAP_OPTIONS",
    "get_configured_cache_cap_gb",
    "ManageCachedMediaDialog",
    "find_redownload_provider",
    "reattach_downloaded_media_to_project",
    "prompt_redownload_missing_remote_media",
]

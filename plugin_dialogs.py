"""GitHub plugins dialogs, batch download workers, and PluginManagerDialog."""
from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from prs_shared import INTERNAL_APP_ID, PROJECT_VERSION, get_github_repo, safe_extract_zip, verify_file_sha256
from plugins.base import BasePlugin, PluginManifest

logger = logging.getLogger(__name__)


class GitHubPluginsWorker(QThread):
    """Fetches list of available plugins from GitHub release assets and official catalog."""
    finished = Signal(bool, list, str)

    def __init__(self, repo: str, parent=None):
        super().__init__(parent)
        self.repo = repo

    def run(self):
        plugins_catalog = [
            {
                "id": "youtube",
                "name": "YouTube Video Publisher",
                "category": "export",
                "version": PROJECT_VERSION,
                "description": "Publishes broadcast video stories to YouTube with chapter timestamps, frame grabs/custom thumbnails, tags, and assisted YouTube Studio upload.",
                "author": "Radio & TV Segmenter Team",
                "asset_name": f"rtvs-plugin-youtube-v{PROJECT_VERSION}.rtvs-addon",
                "download_url": f"https://github.com/{self.repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-youtube-v{PROJECT_VERSION}.rtvs-addon",
                "fallback_url": f"https://raw.githubusercontent.com/{self.repo}/main/plugins/youtube.rtvs-addon",
            },
            {
                "id": "wordpress",
                "name": "WordPress Publisher",
                "category": "export",
                "version": PROJECT_VERSION,
                "description": "Publishes segmented audio/video stories, transcripts, excerpts, and custom featured images directly to WordPress posts via the WP REST API.",
                "author": "Radio & TV Segmenter Team",
                "asset_name": f"rtvs-plugin-wordpress-v{PROJECT_VERSION}.rtvs-addon",
                "download_url": f"https://github.com/{self.repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-wordpress-v{PROJECT_VERSION}.rtvs-addon",
                "fallback_url": f"https://raw.githubusercontent.com/{self.repo}/main/plugins/wordpress.rtvs-addon",
            },
            {
                "id": "gdocs",
                "name": "Google Docs & Sheets Exporter",
                "category": "export",
                "version": PROJECT_VERSION,
                "description": "Exports rich segmented transcripts directly to Google Docs with H2 chapter headings, and generates professional radio/TV rundown spreadsheets in Google Sheets.",
                "author": "Radio & TV Segmenter Team",
                "asset_name": f"rtvs-plugin-gdocs-v{PROJECT_VERSION}.rtvs-addon",
                "download_url": f"https://github.com/{self.repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-gdocs-v{PROJECT_VERSION}.rtvs-addon",
                "fallback_url": f"https://raw.githubusercontent.com/{self.repo}/main/plugins/gdocs.rtvs-addon",
            }
        ]
        try:
            api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            req = urllib.request.Request(api_url, headers={"User-Agent": "RadioTVStorySegmenter-PluginManager"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                assets = data.get("assets", [])
                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(".rtvs-addon"):
                        for cat in plugins_catalog:
                            if cat["asset_name"] == name:
                                cat["download_url"] = asset.get("browser_download_url", cat["download_url"])
                                cat["version"] = data.get("tag_name", cat["version"])
            self.finished.emit(True, plugins_catalog, "")
        except Exception as e:
            logger.info("GitHub API fetch fallback to static catalog: %s", e)
            self.finished.emit(True, plugins_catalog, "")


class GitHubDownloadWorker(QThread):
    """Downloads and installs a `.rtvs-addon` plugin package from GitHub releases."""
    finished = Signal(bool, str, str)

    def __init__(self, plugin_meta: dict, plugins_dir: Path, repo: str, parent=None):
        super().__init__(parent)
        self.plugin_meta = plugin_meta
        self.plugins_dir = plugins_dir
        self.repo = repo

    def run(self):
        plugin_id = self.plugin_meta.get("id")
        download_url = self.plugin_meta.get("download_url")
        fallback_url = self.plugin_meta.get("fallback_url")

        if not plugin_id:
            self.finished.emit(False, "", "Invalid plugin metadata.")
            return

        urls_to_try = [u for u in [download_url, fallback_url] if u]
        if not urls_to_try:
            self.finished.emit(False, plugin_id, "No valid download URL provided.")
            return

        success = False
        last_err = ""
        tmp_dir = Path(tempfile.mkdtemp(prefix="rtvs_plugin_dl_"))

        try:
            addon_path = tmp_dir / f"{plugin_id}.rtvs-addon"
            for url in urls_to_try:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "RadioTVStorySegmenter-PluginDownloader"})
                    with urllib.request.urlopen(req, timeout=30) as resp, open(addon_path, "wb") as f:
                        shutil.copyfileobj(resp, f)
                    if addon_path.exists() and addon_path.stat().st_size > 100:
                        success = True
                        break
                except Exception as ex:
                    last_err = str(ex)
                    continue

            if not success:
                self.finished.emit(False, plugin_id, f"Failed to download plugin package: {last_err}")
                return

            target_plugin_dir = self.plugins_dir / plugin_id
            if target_plugin_dir.exists():
                shutil.rmtree(target_plugin_dir, ignore_errors=True)
            target_plugin_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(addon_path, "r") as zf:
                zf.extractall(target_plugin_dir)

            self.finished.emit(True, plugin_id, f"Successfully installed '{plugin_id}'.")
        except Exception as e:
            self.finished.emit(False, plugin_id, f"Error installing plugin: {e}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class GitHubBatchDownloadWorker(QThread):
    """Batch installs all missing or outdated official plugins."""
    progress = Signal(str, int, int)
    finished = Signal(bool, str)

    def __init__(self, plugins_to_install: List[dict], plugins_dir: Path, repo: str, parent=None):
        super().__init__(parent)
        self.plugins_to_install = plugins_to_install
        self.plugins_dir = plugins_dir
        self.repo = repo

    def run(self):
        total = len(self.plugins_to_install)
        for idx, meta in enumerate(self.plugins_to_install, 1):
            pid = meta.get("id")
            self.progress.emit(f"Installing {pid}...", idx, total)
            
            download_url = meta.get("download_url")
            fallback_url = meta.get("fallback_url")
            urls = [u for u in [download_url, fallback_url] if u]
            
            success = False
            tmp_dir = Path(tempfile.mkdtemp(prefix="rtvs_batch_dl_"))
            try:
                addon_path = tmp_dir / f"{pid}.rtvs-addon"
                for u in urls:
                    try:
                        req = urllib.request.Request(u, headers={"User-Agent": "RadioTVStorySegmenter-BatchDownloader"})
                        with urllib.request.urlopen(req, timeout=30) as resp, open(addon_path, "wb") as f:
                            shutil.copyfileobj(resp, f)
                        if addon_path.exists() and addon_path.stat().st_size > 100:
                            success = True
                            break
                    except Exception:
                        continue

                if success:
                    target_dir = self.plugins_dir / pid
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(addon_path, "r") as zf:
                        zf.extractall(target_dir)
            except Exception:
                pass
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        self.finished.emit(True, "Batch installation completed.")


class GitHubPluginsDialog(QDialog):
    """Browse and install official and community plugins from GitHub releases."""

    def __init__(self, plugin_manager: Any, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setWindowTitle("Browse GitHub Plugins Catalog")
        self.resize(750, 500)

        layout = QVBoxLayout(self)

        info_lbl = QLabel("Browse official and community extensions published on GitHub. Click 'Install' to add or update any extension instantly.")
        layout.addWidget(info_lbl)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Plugin ID", "Name", "Version", "Author", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Catalog", self)
        self.refresh_btn.clicked.connect(self.fetch_catalog)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.catalog_data: List[dict] = []
        self.fetch_catalog()

    def fetch_catalog(self):
        self.refresh_btn.setEnabled(False)
        repo = get_github_repo()
        self.worker = GitHubPluginsWorker(repo, self)
        self.worker.finished.connect(self.on_catalog_fetched)
        self.worker.start()

    def on_catalog_fetched(self, success: bool, catalog: list, err: str):
        self.refresh_btn.setEnabled(True)
        if not success:
            QMessageBox.warning(self, "Catalog Fetch Failed", f"Could not fetch plugin catalog from GitHub:\n{err}")
            return
        self.catalog_data = catalog
        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(len(self.catalog_data))
        for row, meta in enumerate(self.catalog_data):
            pid = meta.get("id", "")
            name = meta.get("name", "")
            ver = meta.get("version", "")
            author = meta.get("author", "")

            self.table.setItem(row, 0, QTableWidgetItem(pid))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(ver))
            self.table.setItem(row, 3, QTableWidgetItem(author))

            install_btn = QPushButton("Install / Update", self)
            install_btn.clicked.connect(lambda checked=False, m=meta: self.install_plugin(m))
            self.table.setCellWidget(row, 4, install_btn)

    def install_plugin(self, meta: dict):
        pid = meta.get("id")
        repo = get_github_repo()
        self.dl_worker = GitHubDownloadWorker(meta, self.plugin_manager.plugins_dir, repo, self)
        self.dl_worker.finished.connect(lambda success, pid, msg: self.on_installed(success, pid, msg))
        
        self.progress_dlg = QProgressDialog(f"Downloading and installing {pid}...", "Cancel", 0, 0, self)
        self.progress_dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dlg.show()
        
        self.dl_worker.start()

    def on_installed(self, success: bool, pid: str, msg: str):
        if hasattr(self, "progress_dlg"):
            self.progress_dlg.close()
        if success:
            QMessageBox.information(self, "Installation Successful", msg)
            self.plugin_manager.discover_plugins()
            self.accept()
        else:
            QMessageBox.critical(self, "Installation Failed", msg)


class PluginManagerDialog(QDialog):
    """Main management dialog for discovering, enabling, disabling, installing, and removing plugins."""

    def __init__(self, plugin_manager: Any, parent=None):
        super().__init__(parent)
        self.manager = plugin_manager
        self.setWindowTitle("Extensions & Plugins Manager")
        self.resize(800, 520)

        layout = QHBoxLayout(self)

        # Left list of plugins
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Installed Extensions"))
        self.plugin_table = QTableWidget(self)
        self.plugin_table.setColumnCount(3)
        self.plugin_table.setHorizontalHeaderLabels(["ID", "Name", "Status"])
        self.plugin_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.plugin_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.plugin_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.plugin_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.plugin_table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.plugin_table)
        layout.addLayout(left_layout, 1)

        # Right details and actions
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Extension Details"))

        self.details_edit = QTextEdit(self)
        self.details_edit.setReadOnly(True)
        right_layout.addWidget(self.details_edit)

        self.enable_chk = QCheckBox("Enable Extension on Startup", self)
        self.enable_chk.toggled.connect(self.on_enable_toggled)
        right_layout.addWidget(self.enable_chk)

        action_layout = QHBoxLayout()
        self.install_local_btn = QPushButton("Install from .rtvs-addon...", self)
        self.install_local_btn.clicked.connect(self.install_local_addon)
        action_layout.addWidget(self.install_local_btn)

        self.browse_gh_btn = QPushButton("Browse GitHub...", self)
        self.browse_gh_btn.clicked.connect(self.browse_github_catalog)
        action_layout.addWidget(self.browse_gh_btn)
        right_layout.addLayout(action_layout)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        right_layout.addWidget(close_btn)

        layout.addLayout(right_layout, 1)

        self.refresh_list()

    def refresh_list(self):
        self.manager.discover_plugins()
        manifests = self.manager.manifests
        self.plugin_table.setRowCount(len(manifests))

        row = 0
        for pid, manifest in manifests.items():
            self.plugin_table.setItem(row, 0, QTableWidgetItem(pid))
            self.plugin_table.setItem(row, 1, QTableWidgetItem(manifest.name))
            status = "Enabled" if self.manager.is_plugin_enabled(pid) else "Disabled"
            self.plugin_table.setItem(row, 2, QTableWidgetItem(status))
            row += 1

        if manifests:
            self.plugin_table.selectRow(0)

    def on_selection_changed(self):
        selected_rows = self.plugin_table.selectionModel().selectedRows()
        if not selected_rows:
            self.details_edit.clear()
            self.enable_chk.setEnabled(False)
            return

        row = selected_rows[0].row()
        item = self.plugin_table.item(row, 0)
        if not item:
            return
        pid = item.text()
        plugin = self.manager.get_plugin(pid)
        manifest = self.manager.manifests.get(pid)

        if not manifest:
            return

        details = f"<b>ID:</b> {manifest.id}<br>"
        details += f"<b>Name:</b> {manifest.name}<br>"
        details += f"<b>Version:</b> {manifest.version}<br>"
        details += f"<b>Author:</b> {manifest.author}<br>"
        details += f"<b>Category:</b> {manifest.category}<br><br>"
        details += f"<b>Description:</b><br>{manifest.description}"
        self.details_edit.setHtml(details)

        self.enable_chk.blockSignals(True)
        self.enable_chk.setChecked(self.manager.is_plugin_enabled(pid))
        self.enable_chk.setEnabled(True)
        self.enable_chk.blockSignals(False)

    def on_enable_toggled(self, enabled: bool):
        selected_rows = self.plugin_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item = self.plugin_table.item(row, 0)
        if not item:
            return
        pid = item.text()
        self.manager.set_plugin_enabled(pid, enabled)
        self.refresh_list()

    def install_local_addon(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Install Plugin Addon", "", "Radio/TV Segmenter Addon (*.rtvs-addon *.zip)")
        if not filepath:
            return
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                manifest_data = None
                for name in zf.namelist():
                    if name.endswith("manifest.json"):
                        with zf.open(name) as mf:
                            manifest_data = json.loads(mf.read().decode("utf-8"))
                        break
                if not manifest_data:
                    QMessageBox.warning(self, "Invalid Addon", "The selected archive does not contain a valid `manifest.json`.")
                    return

                pid = manifest_data.get("id")
                if not pid:
                    QMessageBox.warning(self, "Invalid Addon", "Manifest missing required `id` field.")
                    return

                target_dir = self.manager.plugins_dir / pid
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
                target_dir.mkdir(parents=True, exist_ok=True)
                zf.extractall(target_dir)

            QMessageBox.information(self, "Installation Successful", f"Successfully installed plugin '{pid}'.")
            self.refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Installation Failed", f"Failed to install addon:\n{e}")

    def browse_github_catalog(self):
        dlg = GitHubPluginsDialog(self.manager, self)
        dlg.exec()
        self.refresh_list()

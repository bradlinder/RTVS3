"""GitHub plugins browser and installer dialog with multi-selection."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from prs_shared import PROJECT_VERSION, get_github_repo
from plugins.installer_workers import (
    GitHubPluginsWorker,
    GitHubDownloadWorker,
    GitHubBatchDownloadWorker,
    get_official_plugins_catalog,
)
from plugins.version_utils import is_newer_plugin_version

if TYPE_CHECKING:
    from plugins.manager import PluginManager

class GitHubPluginsDialog(QDialog):
    """Browses, downloads, installs, and manages add-ons directly from GitHub releases with multi-selection."""

    def __init__(self, manager: PluginManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.repo = get_github_repo()
        self.catalog: List[Dict[str, Any]] = get_official_plugins_catalog(self.repo)
        self.download_worker: Optional[GitHubDownloadWorker] = None
        self.batch_worker: Optional[GitHubBatchDownloadWorker] = None
        self.fetch_worker: Optional[GitHubPluginsWorker] = None
        self.row_checkboxes: List[QCheckBox] = []

        self.setWindowTitle("Download Plugins & Extensions from GitHub")
        self.setMinimumSize(860, 600)
        self.resize(900, 640)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setup_ui()
        self.render_table()
        self.fetch_plugins()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(
            "<b>Download Plugins & Extensions from GitHub</b><br>"
            f"<span style='color: #64748b;'>Browse official extensions published on the GitHub repository releases ({self.repo}). "
            "Select individual or multiple plugins to download, install, enable, disable, or remove in batch.</span>"
        )
        layout.addWidget(header)

        self.repo_label = QLabel(f"Connecting to GitHub releases for <b>{self.repo}</b>...")
        layout.addWidget(self.repo_label)

        # Batch Selection Toolbar
        batch_bar = QHBoxLayout()
        batch_bar.setSpacing(8)

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_plugins)
        batch_bar.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_plugins)
        batch_bar.addWidget(deselect_all_btn)

        batch_bar.addSpacing(10)

        self.batch_download_btn = QPushButton("Download & Install Selected")
        self.batch_download_btn.setStyleSheet("font-weight: bold;")
        self.batch_download_btn.clicked.connect(self.download_selected_plugins)
        batch_bar.addWidget(self.batch_download_btn)

        self.batch_update_btn = QPushButton("Update All Available")
        self.batch_update_btn.setStyleSheet("font-weight: bold; color: #0284c7;")
        self.batch_update_btn.clicked.connect(self.update_all_available_plugins)
        self.batch_update_btn.setVisible(False)
        batch_bar.addWidget(self.batch_update_btn)

        self.batch_enable_btn = QPushButton("Enable Selected")
        self.batch_enable_btn.clicked.connect(self.enable_selected_plugins)
        batch_bar.addWidget(self.batch_enable_btn)

        self.batch_disable_btn = QPushButton("Disable Selected")
        self.batch_disable_btn.clicked.connect(self.disable_selected_plugins)
        batch_bar.addWidget(self.batch_disable_btn)

        self.batch_uninstall_btn = QPushButton("Uninstall Selected...")
        self.batch_uninstall_btn.clicked.connect(self.uninstall_selected_plugins)
        batch_bar.addWidget(self.batch_uninstall_btn)

        batch_bar.addStretch()
        layout.addLayout(batch_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "Plugin", "Version", "Category", "Status", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().setMinimumSectionSize(44)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.cellClicked.connect(lambda row, col: self.on_selection_changed())
        layout.addWidget(self.table)

        desc_box = QGroupBox("Plugin Description")
        desc_layout = QVBoxLayout(desc_box)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(90)
        self.desc_text.setMaximumHeight(120)
        desc_layout.addWidget(self.desc_text)
        layout.addWidget(desc_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh from GitHub")
        self.refresh_btn.clicked.connect(self.fetch_plugins)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def fetch_plugins(self):
        self.repo_label.setText(f"Checking GitHub releases for <b>{self.repo}</b>...")
        self.refresh_btn.setEnabled(False)

        self.fetch_worker = GitHubPluginsWorker(self.repo, self)
        self.fetch_worker.finished.connect(self.on_plugins_fetched)
        self.fetch_worker.start()

    def on_plugins_fetched(self, success: bool, catalog: list, note: str):
        self.refresh_btn.setEnabled(True)
        self.catalog = catalog
        if note:
            self.repo_label.setText(f"Repository: <b>{self.repo}</b> ({note})")
        else:
            self.repo_label.setText(f"Repository: <b>{self.repo}</b> (Latest Releases)")
        self.render_table()

    def render_table(self):
        self.manager.discover_plugins()
        self.table.setRowCount(0)
        self.row_checkboxes.clear()

        has_any_update = False

        for row, item in enumerate(self.catalog):
            self.table.insertRow(row)
            self.table.setRowHeight(row, 48)
            plugin_id = item["id"]
            is_installed = self.manager.is_plugin_installed(plugin_id)
            is_enabled = self.manager.is_plugin_enabled(plugin_id)
            installed_manifest = self.manager.manifests.get(plugin_id)
            installed_version = installed_manifest.version if installed_manifest else None
            remote_version = str(item.get("version", PROJECT_VERSION))
            has_update = is_installed and installed_version and is_newer_plugin_version(remote_version, installed_version)
            if has_update:
                has_any_update = True

            # Column 0: Selection Checkbox
            chk = QCheckBox()
            chk.setChecked(False)
            self.row_checkboxes.append(chk)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(4, 2, 4, 2)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            # Column 1: Name Item
            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 1, name_item)

            # Column 2: Version
            if has_update:
                ver_item = QTableWidgetItem(f"v{remote_version} (Installed: v{installed_version})")
                ver_item.setForeground(QColor("#0284c7"))
            elif is_installed:
                ver_item = QTableWidgetItem(f"v{installed_version}")
            else:
                ver_item = QTableWidgetItem(f"v{remote_version}")
            self.table.setItem(row, 2, ver_item)

            # Column 3: Category
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("category", "General")).capitalize()))

            # Column 4: Status
            if has_update:
                status_text = f"Update Available (v{remote_version})"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor("#0284c7"))
                status_item.setFont(QFont(self.font().family(), self.font().pointSize(), QFont.Weight.Bold))
            elif is_installed:
                status_text = "Installed (Enabled)" if is_enabled else "Installed (Disabled)"
                status_item = QTableWidgetItem(status_text)
            else:
                status_text = "Available"
                status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 4, status_item)

            # Column 5: Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 4, 6, 4)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            btn_style = "QPushButton { min-height: 28px; padding: 4px 12px; }"
            if not is_installed:
                download_btn = QPushButton("Download & Install")
                download_btn.setStyleSheet("QPushButton { font-weight: bold; min-height: 28px; padding: 4px 12px; }")
                download_btn.clicked.connect(lambda _, it=item: self.download_and_install_plugin(it))
                action_layout.addWidget(download_btn)
            else:
                if has_update:
                    update_btn = QPushButton(f"Update to v{remote_version}")
                    update_btn.setStyleSheet("QPushButton { font-weight: bold; min-height: 28px; padding: 4px 12px; background-color: #0284c7; color: white; border-radius: 4px; }")
                    update_btn.clicked.connect(lambda _, it=item: self.download_and_install_plugin(it))
                    action_layout.addWidget(update_btn)

                toggle_btn = QPushButton("Disable" if is_enabled else "Enable")
                toggle_btn.setStyleSheet(btn_style)
                toggle_btn.clicked.connect(lambda _, pid=plugin_id, cur=is_enabled: self.toggle_plugin(pid, not cur))
                action_layout.addWidget(toggle_btn)

                uninstall_btn = QPushButton("Uninstall")
                uninstall_btn.setStyleSheet(btn_style)
                uninstall_btn.clicked.connect(lambda _, pid=plugin_id, nm=item["name"]: self.uninstall_plugin(pid, nm))
                action_layout.addWidget(uninstall_btn)

            self.table.setCellWidget(row, 5, action_widget)

        self.batch_update_btn.setVisible(has_any_update)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def update_all_available_plugins(self):
        """Finds all installed plugins with available updates and updates them in batch."""
        updates_to_run = []
        for item in self.catalog:
            pid = item["id"]
            if self.manager.is_plugin_installed(pid):
                m = self.manager.manifests.get(pid)
                if m and is_newer_plugin_version(str(item.get("version", "")), m.version):
                    updates_to_run.append(item)

        if not updates_to_run:
            QMessageBox.information(self, "Plugin Updates", "All installed plugins are up to date.")
            return

        names = "\n• ".join([f"{it['name']} (v{it.get('version', '')})" for it in updates_to_run])
        res = QMessageBox.question(
            self,
            "Update Plugins",
            f"Download and install updates for the following {len(updates_to_run)} plugin(s)?\n\n• {names}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"Updating {len(updates_to_run)} plugin(s)...")
        self.progress_label.setVisible(True)

        self.batch_worker = GitHubBatchDownloadWorker(updates_to_run, self.manager, enable_after=True, parent=self)
        self.batch_worker.progress.connect(self.on_download_progress)
        self.batch_worker.finished.connect(self.on_batch_download_finished)
        self.batch_worker.start()

    def select_all_plugins(self):
        for chk in self.row_checkboxes:
            chk.setChecked(True)
        self.table.selectAll()

    def deselect_all_plugins(self):
        for chk in self.row_checkboxes:
            chk.setChecked(False)
        self.table.clearSelection()

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Returns list of plugin items that are either checked or part of extended row selection."""
        selected_set = set()
        # Checked rows
        for row, chk in enumerate(self.row_checkboxes):
            if chk.isChecked():
                selected_set.add(row)
        # Highlighted / multi-selected rows
        for item in self.table.selectedItems():
            selected_set.add(item.row())

        result = []
        for row in sorted(selected_set):
            name_cell = self.table.item(row, 1)
            if name_cell:
                data = name_cell.data(Qt.ItemDataRole.UserRole)
                if data:
                    result.append(data)
        return result

    def on_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            selected_rows = self.table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
            elif self.table.selectedItems():
                row = self.table.selectedItems()[0].row()

        if row < 0 or row >= self.table.rowCount():
            self.desc_text.clear()
            return

        item_cell = self.table.item(row, 1)
        if not item_cell:
            return
        data = item_cell.data(Qt.ItemDataRole.UserRole)
        if data:
            desc = (
                f"<b>{data['name']}</b> (ID: <code>{data['id']}</code>)<br>"
                f"{data.get('description', '')}<br><br>"
                f"<b>Author:</b> {data.get('author', 'Official')} &nbsp;•&nbsp; "
                f"<b>Download Package:</b> <code>{data.get('asset_name', '')}</code>"
            )
            self.desc_text.setHtml(desc)

    def download_and_install_plugin(self, item: Dict[str, Any]):
        plugin_id = item["id"]
        plugin_name = item["name"]
        asset_name = item.get("asset_name", f"{plugin_id}.rtvs-addon")
        download_url = item.get("download_url") or item.get("fallback_url")

        bundled_addons = self.manager.get_bundled_addons()
        fallback_addon = bundled_addons.get(plugin_id)

        dest_file = Path(tempfile.gettempdir()) / f"rtvs_download_{plugin_id}_{asset_name}"

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"Starting download of {plugin_name}...")
        self.progress_label.setVisible(True)

        self.download_worker = GitHubDownloadWorker(download_url, dest_file, fallback_addon, self)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(lambda ok, path, err, nm=plugin_name, pid=plugin_id: self.on_download_finished(ok, path, err, nm, pid))
        self.download_worker.start()

    def download_selected_plugins(self):
        items = self.get_selected_items()
        uninstalled = [it for it in items if not self.manager.is_plugin_installed(it["id"])]
        if not uninstalled:
            QMessageBox.information(
                self,
                "Download Plugins",
                "Please select one or more uninstalled plugins from the list to download and install."
            )
            return

        res = QMessageBox.question(
            self,
            "Download Selected Plugins",
            f"Download and install the following {len(uninstalled)} selected plugin(s)?\n\n• " +
            "\n• ".join([it["name"] for it in uninstalled]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"Downloading {len(uninstalled)} plugins...")
        self.progress_label.setVisible(True)

        self.batch_worker = GitHubBatchDownloadWorker(uninstalled, self.manager, enable_after=True, parent=self)
        self.batch_worker.progress.connect(self.on_download_progress)
        self.batch_worker.finished.connect(self.on_batch_download_finished)
        self.batch_worker.start()

    def on_batch_download_finished(self, succeeded: int, failed: int, errors: list):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Discover newly extracted plugins and load enabled ones safely on the main GUI thread
        self.manager.discover_plugins()
        for pid, manifest in list(self.manager.manifests.items()):
            if self.manager.is_plugin_enabled(pid):
                self.manager.load_plugin(pid)

        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()

        self.render_table()

        if failed == 0:
            QMessageBox.information(
                self,
                "Batch Installation Complete",
                f"Successfully downloaded and installed {succeeded} plugin(s)!"
            )
        else:
            err_msg = "\n".join(errors)
            QMessageBox.warning(
                self,
                "Batch Installation Results",
                f"Installed {succeeded} plugin(s).\n{failed} plugin(s) encountered issues:\n\n{err_msg}"
            )

    def enable_selected_plugins(self):
        items = self.get_selected_items()
        installed = [it for it in items if self.manager.is_plugin_installed(it["id"])]
        if not installed:
            QMessageBox.information(self, "Enable Plugins", "Please select one or more installed plugins to enable.")
            return

        count = 0
        for it in installed:
            pid = it["id"]
            self.manager.set_plugin_enabled(pid, True)
            self.manager.load_plugin(pid)
            count += 1

        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()
        self.render_table()
        QMessageBox.information(self, "Plugins Enabled", f"Enabled {count} selected plugin(s).")

    def disable_selected_plugins(self):
        items = self.get_selected_items()
        installed = [it for it in items if self.manager.is_plugin_installed(it["id"])]
        if not installed:
            QMessageBox.information(self, "Disable Plugins", "Please select one or more installed plugins to disable.")
            return

        count = 0
        for it in installed:
            pid = it["id"]
            self.manager.set_plugin_enabled(pid, False)
            self.manager.unload_plugin(pid)
            count += 1

        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()
        self.render_table()
        QMessageBox.information(self, "Plugins Disabled", f"Disabled {count} selected plugin(s).")

    def uninstall_selected_plugins(self):
        items = self.get_selected_items()
        installed = [it for it in items if self.manager.is_plugin_installed(it["id"])]
        if not installed:
            QMessageBox.information(self, "Uninstall Plugins", "Please select one or more installed plugins to uninstall.")
            return

        names = "\n• ".join([it["name"] for it in installed])
        res = QMessageBox.question(
            self,
            "Uninstall Selected Plugins",
            f"Are you sure you want to uninstall and remove {len(installed)} selected plugin(s)?\n\n• {names}\n\n"
            "This will remove the plugin files and disable all related features.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            for it in installed:
                self.manager.uninstall_plugin(it["id"])
            self.render_table()
            QMessageBox.information(self, "Plugins Removed", f"Successfully uninstalled {len(installed)} plugin(s).")

    def on_download_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.progress_label.setText(msg)

    def on_download_finished(self, success: bool, file_path: str, error_msg: str, plugin_name: str, plugin_id: str):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        if not success:
            QMessageBox.critical(self, "Download Failed", f"Could not download {plugin_name}:\n{error_msg}")
            return

        try:
            ok = self.manager.install_addon(file_path, enable=False)
            if ok:
                res = QMessageBox.question(
                    self,
                    "Plugin Installed",
                    f"<b>{plugin_name}</b> has been downloaded and installed successfully!\n\n"
                    "Would you like to enable this plugin now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if res == QMessageBox.StandardButton.Yes:
                    self.manager.set_plugin_enabled(plugin_id, True)
                    self.manager.load_plugin(plugin_id)
                    if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
                        self.manager.app.refresh_plugin_menus()

                self.render_table()
            else:
                QMessageBox.warning(self, "Installation Failed", f"Downloaded package for {plugin_name} was invalid or missing manifest.")
        except Exception as exc:
            QMessageBox.critical(self, "Installation Error", f"Failed to install {plugin_name}:\n{exc}")
        finally:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass

    def toggle_plugin(self, plugin_id: str, enable: bool):
        self.manager.set_plugin_enabled(plugin_id, enable)
        if enable:
            self.manager.load_plugin(plugin_id)
        else:
            self.manager.unload_plugin(plugin_id)
        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()
        self.render_table()

    def uninstall_plugin(self, plugin_id: str, plugin_name: str):
        res = QMessageBox.question(
            self,
            "Uninstall Plugin",
            f"Are you sure you want to uninstall and remove '{plugin_name}'?\n\n"
            "This will remove the plugin files and disable its features.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            self.manager.uninstall_plugin(plugin_id)
            QMessageBox.information(self, "Plugin Removed", f"'{plugin_name}' has been successfully uninstalled.")
            self.render_table()


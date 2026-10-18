"""Plugin and Add-On Manager Dialog for inspecting, enabling, and installing add-ons."""
from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QColor
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
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from prs_shared import PROJECT_VERSION, get_github_repo, safe_extract_zip, verify_file_sha256
from plugins.installer_workers import GitHubBatchDownloadWorker
from plugins.github_dialog import GitHubPluginsDialog
from plugins.version_utils import is_newer_plugin_version

if TYPE_CHECKING:
    from plugins.manager import PluginManager

class PluginManagerDialog(QDialog):
    """GUI Dialog for viewing, managing, enabling, installing, and removing plugins with multi-selection."""

    def __init__(self, manager: PluginManager, parent: Any = None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Manage Plugins & Add-ons")
        self.setMinimumSize(880, 580)
        self.resize(920, 620)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(
            "<b>Installed Plugins & Extensions</b><br>"
            "<span style='color: #64748b;'>Enable, disable, configure, or install optional publishing destinations and workflow extensions in batch.</span>"
        )
        layout.addWidget(header)

        # Batch Selection Toolbar
        batch_bar = QHBoxLayout()
        batch_bar.setSpacing(6)

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_plugins)
        batch_bar.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_plugins)
        batch_bar.addWidget(deselect_all_btn)

        batch_bar.addSpacing(6)

        self.batch_enable_btn = QPushButton("Enable Selected")
        self.batch_enable_btn.clicked.connect(self.enable_selected_plugins)
        batch_bar.addWidget(self.batch_enable_btn)

        self.batch_disable_btn = QPushButton("Disable Selected")
        self.batch_disable_btn.clicked.connect(self.disable_selected_plugins)
        batch_bar.addWidget(self.batch_disable_btn)

        self.batch_uninstall_btn = QPushButton("Uninstall Selected")
        self.batch_uninstall_btn.clicked.connect(self.uninstall_selected_plugins)
        batch_bar.addWidget(self.batch_uninstall_btn)

        self.batch_configure_btn = QPushButton("Configure...")
        self.batch_configure_btn.setToolTip("Open preferences for the selected plugin.")
        self.batch_configure_btn.clicked.connect(self.configure_selected_plugin)
        batch_bar.addWidget(self.batch_configure_btn)

        batch_bar.addSpacing(6)

        self.batch_check_updates_btn = QPushButton("Check for Updates")
        self.batch_check_updates_btn.setToolTip("Check GitHub for newer versions of installed plugins without updating the core app.")
        self.batch_check_updates_btn.clicked.connect(self.check_for_plugin_updates)
        batch_bar.addWidget(self.batch_check_updates_btn)

        batch_bar.addStretch()
        layout.addLayout(batch_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Enabled", "Name", "Version", "Category", "Author"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.verticalHeader().setMinimumSectionSize(38)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.cellClicked.connect(lambda row, col: self.on_selection_changed())
        layout.addWidget(self.table)

        self.empty_label = QLabel(
            "<i>No plugins are currently installed. Use <b>Download from GitHub...</b> to explore and install official add-ons, or click <b>Install Addons...</b> to select local files.</i>"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #64748b; padding: 12px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

        # Description box
        desc_box = QGroupBox("Plugin Details")
        desc_layout = QVBoxLayout(desc_box)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(90)
        self.desc_text.setMaximumHeight(120)
        desc_layout.addWidget(self.desc_text)
        layout.addWidget(desc_box)

        # Action bar
        btn_layout = QHBoxLayout()

        download_github_btn = QPushButton("Download from GitHub...")
        download_github_btn.setStyleSheet("font-weight: bold;")
        download_github_btn.clicked.connect(self.on_download_github)
        btn_layout.addWidget(download_github_btn)

        install_btn = QPushButton("Install Addon(s) (.rtvs-addon)...")
        install_btn.setToolTip("Select one or multiple add-on packages to install simultaneously.")
        install_btn.clicked.connect(self.on_install_addon)
        btn_layout.addWidget(install_btn)

        open_folder_btn = QPushButton("Open Plugins Folder")
        open_folder_btn.clicked.connect(self.on_open_folder)
        btn_layout.addWidget(open_folder_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def on_download_github(self):
        try:
            dlg = GitHubPluginsDialog(self.manager, self)
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
            dlg.exec()
            self.refresh_list()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "GitHub Plugins", f"Could not open GitHub plugins browser:\n{exc}")

    def select_all_plugins(self):
        self.table.selectAll()

    def deselect_all_plugins(self):
        self.table.clearSelection()

    def get_selected_plugin_ids(self) -> List[str]:
        """Returns the list of plugin_ids selected via multi-row selection."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        result = []
        for row in sorted(selected_rows):
            name_cell = self.table.item(row, 1)
            if name_cell:
                pid = name_cell.data(Qt.ItemDataRole.UserRole)
                if pid:
                    result.append(pid)
        return result

    def refresh_list(self):
        self.manager.discover_plugins()
        self.table.setRowCount(0)
        row = 0
        for plugin_id, manifest in sorted(self.manager.manifests.items(), key=lambda x: x[1].name):
            self.table.insertRow(row)
            self.table.setRowHeight(row, 42)

            # Checkbox
            chk = QCheckBox()
            is_enabled = self.manager.is_plugin_enabled(plugin_id)
            chk.setChecked(is_enabled)
            chk.stateChanged.connect(lambda state, pid=plugin_id: self.on_toggle_plugin(pid, state))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(4, 2, 4, 2)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            # Name item
            name_item = QTableWidgetItem(manifest.name)
            name_item.setData(Qt.ItemDataRole.UserRole, plugin_id)
            self.table.setItem(row, 1, name_item)

            # Version item
            self.table.setItem(row, 2, QTableWidgetItem(f"v{manifest.version}"))

            # Category item
            self.table.setItem(row, 3, QTableWidgetItem(manifest.category.capitalize()))

            # Author item
            self.table.setItem(row, 4, QTableWidgetItem(manifest.author or "Official"))

            row += 1

        is_empty = self.table.rowCount() == 0
        self.empty_label.setVisible(is_empty)
        self.batch_enable_btn.setEnabled(not is_empty)
        self.batch_disable_btn.setEnabled(not is_empty)
        self.batch_uninstall_btn.setEnabled(not is_empty)

        if not is_empty:
            self.table.selectRow(0)
        else:
            self.desc_text.clear()

    def on_toggle_plugin(self, plugin_id: str, state: int):
        enabled = state == Qt.CheckState.Checked.value or state == 2
        self.manager.set_plugin_enabled(plugin_id, enabled)
        if enabled:
            self.manager.load_plugin(plugin_id)
        else:
            self.manager.unload_plugin(plugin_id)
        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()

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

        item = self.table.item(row, 1)
        if not item:
            return
        plugin_id = item.data(Qt.ItemDataRole.UserRole)
        manifest = self.manager.manifests.get(plugin_id)
        if manifest:
            folder = self.manager.plugin_paths.get(plugin_id, "Unknown")
            desc = (
                f"<b>{manifest.name}</b> (ID: <code>{manifest.id}</code>)<br>"
                f"{manifest.description}<br><br>"
                f"<b>Author:</b> {manifest.author or 'Official'} &nbsp;•&nbsp; "
                f"<b>Location:</b> <span style='font-size: 11px;'>{folder}</span>"
            )
            self.desc_text.setHtml(desc)

    def configure_selected_plugin(self):
        selected_ids = self.get_selected_plugin_ids()
        if not selected_ids:
            QMessageBox.information(self, "Configure Plugin", "Please select a plugin from the list to configure.")
            return
        pid = selected_ids[0]
        # Make sure plugin is enabled
        if not self.manager.is_plugin_enabled(pid):
            self.manager.set_plugin_enabled(pid, True)
            self.manager.load_plugin(pid)
            if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
                self.manager.app.refresh_plugin_menus()
            self.refresh_list()

        cat_map = {
            "gdocs": "Google Docs",
            "wordpress": "WordPress",
            "youtube": "YouTube",
        }
        target_cat = cat_map.get(pid, pid)
        if self.manager.app and hasattr(self.manager.app, "open_preferences_dialog"):
            self.accept()
            self.manager.app.open_preferences_dialog(initial_category=target_cat)

    def enable_selected_plugins(self):
        selected_ids = self.get_selected_plugin_ids()
        if not selected_ids:
            QMessageBox.information(self, "Enable Plugins", "Please select one or more plugins from the list.")
            return

        for pid in selected_ids:
            self.manager.set_plugin_enabled(pid, True)
            self.manager.load_plugin(pid)

        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()
        self.refresh_list()
        QMessageBox.information(self, "Plugins Enabled", f"Enabled {len(selected_ids)} selected plugin(s).")

    def disable_selected_plugins(self):
        selected_ids = self.get_selected_plugin_ids()
        if not selected_ids:
            QMessageBox.information(self, "Disable Plugins", "Please select one or more plugins from the list.")
            return

        for pid in selected_ids:
            self.manager.set_plugin_enabled(pid, False)
            self.manager.unload_plugin(pid)

        if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
            self.manager.app.refresh_plugin_menus()
        self.refresh_list()
        QMessageBox.information(self, "Plugins Disabled", f"Disabled {len(selected_ids)} selected plugin(s).")

    def uninstall_selected_plugins(self):
        selected_ids = self.get_selected_plugin_ids()
        if not selected_ids:
            QMessageBox.information(self, "Uninstall Plugins", "Please select one or more plugins from the list to uninstall.")
            return

        names = []
        for pid in selected_ids:
            m = self.manager.manifests.get(pid)
            names.append(m.name if m else pid)

        res = QMessageBox.question(
            self,
            "Uninstall Plugins",
            f"Are you sure you want to uninstall and remove {len(selected_ids)} plugin(s)?\n\n• " +
            "\n• ".join(names) +
            "\n\nThis will remove the plugin files and disable all related features.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            for pid in selected_ids:
                self.manager.uninstall_plugin(pid)
            self.refresh_list()
            QMessageBox.information(self, "Plugins Removed", f"Successfully uninstalled {len(selected_ids)} plugin(s).")

    def on_install_addon(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Install Plugin Add-on Package(s)",
            "",
            "RTVS Add-on Packages (*.rtvs-addon *.zip);;All Files (*.*)",
        )
        if not files:
            return

        installed_count = 0
        for fn in files:
            try:
                ok = self.manager.install_addon(fn, enable=False)
                if ok:
                    installed_count += 1
            except Exception as exc:
                print(f"[PLUGINS] Failed to install {fn}: {exc}")

        if installed_count > 0:
            res = QMessageBox.question(
                self,
                "Addons Installed",
                f"Successfully installed {installed_count} plugin package(s)!\n\nWould you like to enable them now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if res == QMessageBox.StandardButton.Yes:
                manifests = self.manager.discover_plugins()
                for pid in manifests:
                    if not self.manager.is_plugin_enabled(pid):
                        self.manager.set_plugin_enabled(pid, True)
                        self.manager.load_plugin(pid)
                if self.manager.app and hasattr(self.manager.app, "refresh_plugin_menus"):
                    self.manager.app.refresh_plugin_menus()
            self.refresh_list()
        else:
            QMessageBox.warning(self, "Installation Failed", "Could not install plugin packages. Make sure each package contains a valid manifest.json.")

    def check_for_plugin_updates(self):
        """Checks GitHub for newer versions of installed plugins without updating the core app."""
        self.manager.discover_plugins()
        installed_manifests = dict(self.manager.manifests)
        if not installed_manifests:
            res = QMessageBox.question(
                self,
                "Check for Plugin Updates",
                "No plugins are currently installed.\n\nWould you like to open the GitHub catalog to browse and install available add-ons?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if res == QMessageBox.StandardButton.Yes:
                self.on_download_github()
            return

        # Show non-modal loading dialog / worker
        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Checking GitHub releases for plugin updates...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Checking for Updates")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        repo = get_github_repo()
        worker = GitHubPluginsWorker(repo, self)

        def on_check_finished(success: bool, catalog: list, note: str):
            progress.close()
            if not success and not catalog:
                QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    "Could not connect to GitHub to check for plugin updates. Please check your internet connection."
                )
                return

            catalog_map = {it["id"]: it for it in catalog}
            updates_available = []

            for pid, manifest in self.manager.manifests.items():
                if pid in catalog_map:
                    remote_item = catalog_map[pid]
                    remote_ver = str(remote_item.get("version", ""))
                    if remote_ver and is_newer_plugin_version(remote_ver, manifest.version):
                        updates_available.append((manifest, remote_item))

            if not updates_available:
                QMessageBox.information(
                    self,
                    "Plugins Up to Date",
                    f"All {len(self.manager.manifests)} installed plugin(s) are up to date!\n\n(Checked against latest GitHub releases for {repo})"
                )
                return

            # Format update list
            update_lines = []
            for m, r_item in updates_available:
                update_lines.append(f"• <b>{m.name}</b>: v{m.version} &rarr; <span style='color: #0284c7; font-weight: bold;'>v{r_item.get('version', '')}</span>")

            update_msg = (
                f"<b>{len(updates_available)} plugin update(s) available:</b><br><br>"
                + "<br>".join(update_lines)
                + "<br><br>Would you like to download and install these update(s) now without modifying the core app?"
            )

            res = QMessageBox.question(
                self,
                "Plugin Updates Available",
                update_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if res == QMessageBox.StandardButton.Yes:
                self.run_batch_plugin_updates([item for _, item in updates_available])

        worker.finished.connect(on_check_finished)
        worker.start()

    def run_batch_plugin_updates(self, update_items: List[Dict[str, Any]]):
        """Downloads and installs a batch of plugin updates."""
        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Updating plugins from GitHub...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Updating Plugins")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        batch_worker = GitHubBatchDownloadWorker(update_items, self.manager, enable_after=True, parent=self)

        def on_progress(pct, msg):
            progress.setValue(pct)
            progress.setLabelText(msg)

        def on_batch_finished(succeeded, failed, errors):
            progress.close()
            self.refresh_list()
            if failed == 0:
                QMessageBox.information(
                    self,
                    "Updates Completed",
                    f"Successfully updated {succeeded} plugin(s) to the latest version!\n\nAll updated features are now active."
                )
            else:
                err_str = "\n• ".join(errors)
                QMessageBox.warning(
                    self,
                    "Updates Completed with Issues",
                    f"Updated {succeeded} plugin(s), but {failed} failed:\n\n• {err_str}"
                )

        batch_worker.progress.connect(on_progress)
        batch_worker.finished.connect(on_batch_finished)
        batch_worker.start()

    def on_open_folder(self):
        self.manager.ensure_packaged_addons()
        user_dir = self.manager.get_user_plugins_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        import subprocess
        if sys.platform == "win32":
            os.startfile(str(user_dir))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(user_dir)])
        else:
            subprocess.Popen(["xdg-open", str(user_dir)])

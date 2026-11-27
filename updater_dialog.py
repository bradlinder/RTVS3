"""Qt UI dialog and main-window mixin for checking, downloading, and installing updates.

Strict Single Responsibility: UI presentation & user interaction only.
Background QThread workers live in `updater_workers.py`; headless update helpers
live in `updater_core.py`.
"""
from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path

try:
    from prs_shared import get_app_icon
except Exception:
    def get_app_icon():
        return None

try:
    from PySide6.QtCore import Qt, QUrl, QSettings
    from PySide6.QtGui import QCursor, QDesktopServices
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )
except Exception:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, QUrl, QSettings
    from PySide6.QtGui import QCursor, QDesktopServices
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )

from updater_core import (
    APP_DISPLAY_NAME,
    DEFAULT_GITHUB_REPO,
    INTERNAL_APP_ID,
    PROJECT_VERSION,
    _is_trusted_download_url,
    cleanup_old_installers,
    format_byte_size,
    get_app_data_dir,
    get_github_repo,
    get_update_channel,
    is_version_newer,
    is_version_older,
    launch_and_install,
    parse_version_tuple,
    select_best_asset_for_platform,
)
from updater_workers import CheckUpdateWorker, DownloadUpdateWorker


class CheckUpdateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, auto_start: bool = True):
        super().__init__(parent)
        self.setWindowTitle(f"Check for Updates — {APP_DISPLAY_NAME}")
        self.setMinimumWidth(580)
        self.setMinimumHeight(480)
        self.resize(600, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        # Proactively prune older installer downloads to prevent storage bloat while retaining recent packages
        cleanup_old_installers(max_to_keep=2)

        self.repo = get_github_repo()
        if self.repo.lower() in ("bradlinder/rtvs", "bradlinder/radiotvstorysegmenter", "radiotvstorysegmenter"):
            self.repo = DEFAULT_GITHUB_REPO
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                settings.setValue("github_repo", DEFAULT_GITHUB_REPO)
            except Exception:
                pass
        self.releases: list[dict] = []
        self.selected_release_idx: int = 0
        self.release_info: dict = {}
        self.asset_info: dict = {}
        self.downloaded_path: str | None = None
        self.check_worker: CheckUpdateWorker | None = None
        self.download_worker: DownloadUpdateWorker | None = None

        self._build_ui()

        if auto_start:
            self.start_check()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon = get_app_icon()
        self.icon_label = QLabel()
        if icon is not None and not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(48, 48))
        self.icon_label.setFixedSize(48, 48)
        header_layout.addWidget(self.icon_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.title_label = QLabel(APP_DISPLAY_NAME)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_vbox.addWidget(self.title_label)

        self.version_label = QLabel(f"Current version: v{PROJECT_VERSION}  •  Repository: {self.repo}")
        self.version_label.setStyleSheet("font-size: 12px; color: #777;")
        title_vbox.addWidget(self.version_label)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        self.status_label = QLabel("Connecting to GitHub...")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(18)
        main_layout.addWidget(self.progress_bar)

        # Update Channel selector row
        self.channel_layout = QHBoxLayout()
        self.channel_layout.setSpacing(8)

        self.channel_label = QLabel("Release Channel:")
        self.channel_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.channel_layout.addWidget(self.channel_label)

        self.channel_combo = QComboBox()
        self.channel_combo.setStyleSheet("font-size: 12px; padding: 3px 8px;")
        self.channel_combo.addItem("Stable Releases Only (Recommended)", "stable")
        self.channel_combo.addItem("Stable & Beta Releases", "beta")
        curr_chan = get_update_channel()
        self.channel_combo.setCurrentIndex(1 if curr_chan == "beta" else 0)
        self.channel_combo.currentIndexChanged.connect(self._on_channel_changed)
        self.channel_layout.addWidget(self.channel_combo)
        self.channel_layout.addStretch()
        main_layout.addLayout(self.channel_layout)

        # Version selection dropdown row (Historical Release Selector)
        self.version_select_layout = QHBoxLayout()
        self.version_select_layout.setSpacing(8)

        self.version_select_label = QLabel("Select Version:")
        self.version_select_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.version_select_layout.addWidget(self.version_select_label)

        self.version_combo = QComboBox()
        self.version_combo.setStyleSheet("font-size: 12px; padding: 3px 8px; min-width: 220px;")
        self.version_combo.currentIndexChanged.connect(self._on_version_selected)
        self.version_select_layout.addWidget(self.version_combo, 1)

        self.version_select_container = QWidget()
        self.version_select_container.setLayout(self.version_select_layout)
        self.version_select_container.hide()
        main_layout.addWidget(self.version_select_container)

        notes_header_layout = QHBoxLayout()
        notes_header_layout.setContentsMargins(0, 0, 0, 0)

        self.notes_label = QLabel("Release Notes:")
        self.notes_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 4px;")
        self.notes_label.hide()
        notes_header_layout.addWidget(self.notes_label)

        notes_header_layout.addStretch()

        self.full_changelog_label = QLabel()
        self.full_changelog_label.setOpenExternalLinks(True)
        self.full_changelog_label.setStyleSheet("font-size: 12px; margin-top: 4px;")
        self.full_changelog_label.hide()
        notes_header_layout.addWidget(self.full_changelog_label)

        main_layout.addLayout(notes_header_layout)

        self.notes_browser = QTextBrowser()
        self.notes_browser.setOpenExternalLinks(True)
        self.notes_browser.setStyleSheet(
            "QTextBrowser { border: 1px solid #ccc; border-radius: 4px; padding: 8px; font-size: 12px; }"
        )
        self.notes_browser.hide()
        main_layout.addWidget(self.notes_browser, 1)

        self.asset_info_label = QLabel("")
        self.asset_info_label.setStyleSheet("font-size: 12px; color: #555;")
        self.asset_info_label.hide()
        main_layout.addWidget(self.asset_info_label)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)

        self.github_link_btn = QPushButton("View on GitHub")
        self.github_link_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.github_link_btn.clicked.connect(self._open_github_release)
        self.github_link_btn.hide()
        self.btn_layout.addWidget(self.github_link_btn)

        self.btn_layout.addStretch()

        self.action_btn = QPushButton("Check Again")
        self.action_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 6px 16px; }"
        )
        self.action_btn.clicked.connect(self._handle_primary_action)
        self.btn_layout.addWidget(self.action_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self._handle_close)
        self.btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(self.btn_layout)

    def _on_channel_changed(self, index: int):
        new_chan = self.channel_combo.currentData() or "stable"
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            settings.setValue("update_channel", new_chan)
        except Exception:
            pass
        self.start_check()

    def start_check(self):
        chan = get_update_channel()
        if hasattr(self, "channel_combo") and self.channel_combo:
            chan = self.channel_combo.currentData() or chan
        chan_desc = "Beta & Stable" if chan == "beta" else "Stable"
        self.status_label.setText(f"Checking for {chan_desc} updates from {self.repo}...")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.version_select_container.hide()
        self.notes_label.hide()
        self.notes_browser.hide()
        self.asset_info_label.hide()
        self.github_link_btn.hide()
        self.action_btn.setEnabled(False)

        self.check_worker = CheckUpdateWorker(self.repo, parent=self, channel=chan)
        self.check_worker.releases_loaded.connect(self._on_releases_loaded)
        self.check_worker.update_available.connect(self._on_update_available)
        self.check_worker.up_to_date.connect(self._on_up_to_date)
        self.check_worker.error.connect(self._on_check_error)
        self.check_worker.start()

    def _on_releases_loaded(self, releases: list):
        self.releases = releases
        self.version_combo.blockSignals(True)
        self.version_combo.clear()

        clean_cur = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", PROJECT_VERSION.strip(), flags=re.IGNORECASE).lower()

        for idx, r in enumerate(releases):
            tag = r.get("tag_name", "")
            name = r.get("name") or tag
            clean_tag = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", tag.strip(), flags=re.IGNORECASE).lower()

            is_cur = (clean_tag == clean_cur)
            is_new = is_version_newer(tag, PROJECT_VERSION)
            is_old = is_version_older(tag, PROJECT_VERSION)

            label_parts = [name if name != tag else tag]
            if name != tag:
                label_parts.append(f"({tag})")

            if idx == 0 and is_new:
                label_parts.append("★ Latest Update")
            elif idx == 0:
                label_parts.append("★ Latest")

            if is_cur:
                label_parts.append("[Installed]")
            elif is_old:
                label_parts.append("(Older)")

            display_text = " ".join(label_parts)
            self.version_combo.addItem(display_text, idx)

        self.version_combo.setCurrentIndex(0)
        self.version_combo.blockSignals(False)
        self.version_select_container.show()

    def _on_version_selected(self, index: int):
        if index < 0 or index >= len(self.releases):
            return
        selected_release = self.releases[index]
        self._display_release(selected_release)

    def _display_release(self, release_info: dict):
        self.release_info = release_info
        tag = release_info.get("tag_name", "Unknown")
        name = release_info.get("name", tag)
        body = release_info.get("body", "No release notes provided.")

        assets = release_info.get("assets", [])
        self.asset_info = select_best_asset_for_platform(assets, target_version=tag, repo=self.repo) or {}

        self.progress_bar.hide()
        self.notes_label.show()

        changelog_url = f"https://github.com/{self.repo}/blob/main/CHANGELOG.md"
        self.full_changelog_label.setText(
            f'<a href="{changelog_url}" style="color: #1976d2; font-weight: 500; text-decoration: underline;">View Full Changelog in Browser ↗</a>'
        )
        self.full_changelog_label.show()
        self.notes_browser.show()

        formatted_body = body.replace("\r\n", "\n").replace("\n", "<br>")
        self.notes_browser.setHtml(
            f"<div style='font-family: sans-serif; line-height: 1.4;'>"
            f"<b>Release:</b> {name} ({tag})<br>"
            f"<hr style='border: 0; border-top: 1px solid #ddd;'>"
            f"{formatted_body}"
            f"</div>"
        )

        clean_cur = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", PROJECT_VERSION.strip(), flags=re.IGNORECASE).lower()
        clean_tag = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", tag.strip(), flags=re.IGNORECASE).lower()
        is_newer = is_version_newer(tag, PROJECT_VERSION)
        is_older = is_version_older(tag, PROJECT_VERSION)
        is_current = (clean_cur == clean_tag)

        top_release = self.releases[0] if getattr(self, "releases", None) else None
        is_top_release = False
        if top_release:
            top_tag = top_release.get("tag_name", "")
            clean_top = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", top_tag.strip(), flags=re.IGNORECASE).lower()
            is_top_release = (clean_tag == clean_top)

        if is_newer:
            self.status_label.setText(f"★ A newer version is available: {name} ({tag})")
            self.status_label.setStyleSheet("font-size: 14px; color: #1976d2; font-weight: bold;")
            primary_verb = "Update to"
        elif is_older:
            self.status_label.setText(f"⚠️ Selected release ({tag}) is older than installed version (v{PROJECT_VERSION})")
            self.status_label.setStyleSheet("font-size: 13px; color: #e65100; font-weight: bold;")
            primary_verb = "Rollback to"
        elif is_current:
            if is_top_release:
                self.status_label.setText(f"✓ Radio & TV Segmenter is up to date (v{PROJECT_VERSION})")
            else:
                self.status_label.setText(f"✓ You are currently running this version (v{PROJECT_VERSION})")
            self.status_label.setStyleSheet("font-size: 13px; color: #2e7d32; font-weight: bold;")
            primary_verb = "Reinstall"
        else:
            self.status_label.setText(f"Selected release: {name} ({tag})")
            self.status_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            primary_verb = "Install"

        if self.asset_info and self.asset_info.get("browser_download_url"):
            asset_name = self.asset_info.get("name", "installer package")
            asset_size = format_byte_size(self.asset_info.get("size", 0))

            normalized_asset_name = re.sub(r"\.+", ".", asset_name)
            asset_ver_match = re.search(r"(\d+(?:\.\d+)+)", normalized_asset_name)
            asset_ver = asset_ver_match.group(1) if asset_ver_match else ""

            notice_html = ""
            if asset_ver and clean_tag:
                # Compare semantic versions rather than raw strings to avoid false alarms from formatting differences
                if parse_version_tuple(asset_ver)[0] != parse_version_tuple(clean_tag)[0]:
                    notice_html = f"<br><span style='color: #e65100; font-size: 11px;'>⚠️ Notice: Attached asset is labeled v{asset_ver}, which differs from release tag {tag}.</span>"

            self.asset_info_label.setText(f"Platform package: <b>{asset_name}</b> ({asset_size}){notice_html}")
            self.asset_info_label.show()

            # Check if this exact installer file is already cached on disk and complete
            updates_dir = get_app_data_dir() / "updates"
            existing_file = (updates_dir / Path(asset_name).name).resolve() if asset_name else None
            expected_size = int(self.asset_info.get("size", 0))
            is_cached = bool(existing_file and existing_file.is_file() and (expected_size <= 0 or existing_file.stat().st_size >= expected_size * 0.95))

            if is_current:
                self.downloaded_path = str(existing_file) if is_cached else None
                if is_top_release:
                    self.action_btn.setText("Check Again")
                else:
                    self.action_btn.setText(f"Reinstall {tag}")
            elif is_cached:
                self.downloaded_path = str(existing_file)
                self.action_btn.setText("Restart && Install")
                self.status_label.setText(f"✓ Update package for {tag} is already downloaded and ready to install.")
                self.status_label.setStyleSheet("font-size: 13px; color: #2e7d32; font-weight: bold;")
            else:
                self.downloaded_path = None
                self.action_btn.setText(f"{primary_verb} {tag}")
        else:
            self.asset_info_label.setText("No automated binary package detected for your OS. Visit GitHub to download.")
            self.asset_info_label.show()
            if is_current and is_top_release:
                self.action_btn.setText("Check Again")
            else:
                self.action_btn.setText("Open Download Page")

        self.action_btn.setEnabled(True)
        self.github_link_btn.show()

    def _on_up_to_date(self, current_ver: str, remote_tag: str):
        if self.releases:
            self._display_release(self.releases[0])
        else:
            self.progress_bar.hide()
            self.status_label.setText(
                f"✓ Radio & TV Segmenter is up to date!\n\n"
                f"You are running version {current_ver}, which is the latest available release ({remote_tag})."
            )
            self.status_label.setStyleSheet("font-size: 13px; color: #2e7d32; font-weight: bold;")
            self.action_btn.setText("Check Again")
            self.action_btn.setEnabled(True)
            self.github_link_btn.show()

    def _on_update_available(self, release_info: dict, asset_info: dict, is_newer: bool):
        self._display_release(release_info)

    def _on_check_error(self, message: str):
        self.progress_bar.hide()
        self.status_label.setText(f"Update Check Error:\n{message}")
        self.status_label.setStyleSheet("font-size: 13px; color: #d32f2f;")
        self.action_btn.setText("Retry Check")
        self.action_btn.setEnabled(True)
        self.github_link_btn.show()

    def _handle_primary_action(self):
        btn_text = self.action_btn.text().replace("&&", "&").strip()
        if btn_text in ("Check Again", "Retry Check"):
            self.start_check()
        elif btn_text == "Open Download Page":
            self._open_github_release()
        elif btn_text in ("Restart & Install", "Restart Install", "Install & Restart", "Install Restart"):
            self._install_and_restart()
        else:
            tag = self.release_info.get("tag_name", "")
            if is_version_older(tag, PROJECT_VERSION):
                proceed = self._confirm_downgrade(tag)
                if not proceed:
                    return
            self.start_download()

    def _confirm_downgrade(self, target_version: str) -> bool:
        """Modal Warning Dialog when selecting a version lower than installed PROJECT_VERSION."""
        warn_box = QMessageBox(self)
        warn_box.setIcon(QMessageBox.Icon.Warning)
        warn_box.setWindowTitle("Confirm Version Rollback")
        warn_box.setText(
            f"<b>Warning: Potential Version Incompatibility</b><br><br>"
            f"You are about to roll back from <b>v{PROJECT_VERSION}</b> to older release <b>{target_version}</b>.<br><br>"
            f"Installing an older version may cause configuration or project file "
            f"incompatibilities with newer data formats.<br><br>"
            f"It is strongly recommended to back up your project data before proceeding.<br><br>"
            f"Would you like to proceed with the rollback?"
        )
        warn_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        warn_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        return warn_box.exec() == QMessageBox.StandardButton.Yes

    def start_download(self):
        download_url = self.asset_info.get("browser_download_url")
        tag = self.release_info.get("tag_name", "update")
        file_name = self.asset_info.get("name", f"RadioTVSegmenter-Update-{tag}.exe")

        if not download_url:
            self._open_github_release()
            return

        if not _is_trusted_download_url(download_url):
            QMessageBox.critical(
                self, "Update Blocked",
                "The update download URL did not point to an official GitHub domain, "
                "so it was blocked for your safety.",
            )
            self._open_github_release()
            return

        self.status_label.setText(f"Downloading {tag}: {file_name}...")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.action_btn.setEnabled(False)
        self.close_btn.setText("Cancel")

        self.download_worker = DownloadUpdateWorker(download_url, file_name, self, release_info=self.release_info)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_progress(self, percent: int, downloaded: int, total: int, speed_str: str):
        self.progress_bar.setValue(percent)
        down_str = format_byte_size(downloaded)
        tot_str = format_byte_size(total) if total > 0 else "unknown"
        self.status_label.setText(f"Downloading update... {down_str} of {tot_str} ({percent}%) • {speed_str}")

    def _on_download_finished(self, file_path: str):
        self.downloaded_path = file_path
        self.progress_bar.setValue(100)
        self.status_label.setText("✓ Download complete! Ready to install.")
        self.status_label.setStyleSheet("font-size: 14px; color: #2e7d32; font-weight: bold;")
        self.action_btn.setText("Restart && Install")
        self.action_btn.setEnabled(True)
        self.close_btn.setText("Later")

    def _on_download_error(self, message: str):
        self.progress_bar.hide()
        self.status_label.setText(
            f"Download Error:\n{message}\n\n"
            "The direct installer binary for this release is not yet attached on GitHub.\n"
            "Opening the GitHub Releases page in your web browser..."
        )
        self.status_label.setStyleSheet("font-size: 13px; color: #d32f2f;")
        self.action_btn.setText("Open Download Page")
        self.action_btn.setEnabled(True)
        self.close_btn.setText("Close")

        QMessageBox.warning(
            self,
            "Installer Binary Not Found",
            f"Could not download installer directly:\n{message}\n\n"
            "The release tag exists on GitHub, but the Windows Setup .exe has not yet been uploaded as a release asset.\n\n"
            "Opening https://github.com/bradlinder/RTVS3/releases in your browser now.",
        )
        self._open_github_release()

    def _install_and_restart(self):
        if not self.downloaded_path:
            return

        is_verified = getattr(self.download_worker, "checksum_verified", True)
        if not is_verified:
            warn = QMessageBox.warning(
                self,
                "Unverified Update Package",
                f"Notice: The release on GitHub did not include a published SHA-256 checksum file to verify the downloaded package.\n\n"
                f"Package: {Path(self.downloaded_path).name}\n\n"
                f"Do you want to proceed with installing this unverified package?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if warn != QMessageBox.StandardButton.Yes:
                return

        # Guard unsaved user work before initiating shutdown
        app = QApplication.instance()
        dirty_win = None
        if app:
            for widget in app.topLevelWidgets():
                if getattr(widget, "project_dirty", False):
                    dirty_win = widget
                    break
        if dirty_win:
            save_reply = QMessageBox.question(
                self,
                "Save Changes Before Restart?",
                "You have unsaved changes in your current project.\n\n"
                "Would you like to save your project before closing the application to install the update?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if save_reply == QMessageBox.StandardButton.Cancel:
                return
            if save_reply == QMessageBox.StandardButton.Save:
                if hasattr(dirty_win, "save_project"):
                    saved = dirty_win.save_project()
                    if not saved:
                        return

        tag = self.release_info.get("tag_name", "update")
        confirm = QMessageBox.question(
            self,
            "Restart & Install Update",
            f"Radio & TV Segmenter will now close the application and launch the installer for {tag} to complete the update.\n\n"
            f"Proceed with restart and installation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        success = launch_and_install(self.downloaded_path, parent=self)
        if success:
            self.accept()
            app = QApplication.instance()
            if app:
                # Instantly hide all top-level windows so the app visual interface disappears immediately
                try:
                    for widget in app.topLevelWidgets():
                        if hasattr(widget, "hide"):
                            widget.hide()
                        if hasattr(widget, "close"):
                            widget.close()
                except Exception:
                    pass

                # Flush application settings if available on main window or QSettings
                try:
                    QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID).sync()
                except Exception:
                    pass

                # Force immediate exit watcher after 3.0s if Qt event loop delays shutdown
                def _force_exit_watcher():
                    time.sleep(3.0)
                    os._exit(0)

                threading.Thread(target=_force_exit_watcher, daemon=True).start()
                app.quit()
            else:
                os._exit(0)

    def _open_github_release(self):
        url = self.release_info.get("html_url") or f"https://github.com/{self.repo}/releases"
        QDesktopServices.openUrl(QUrl(url))

    def _cleanup_workers(self):
        worker = getattr(self, "check_worker", None)
        if worker is not None:
            try:
                worker.releases_loaded.disconnect(self._on_releases_loaded)
            except Exception:
                pass
            try:
                worker.update_available.disconnect(self._on_update_available)
            except Exception:
                pass
            try:
                worker.up_to_date.disconnect(self._on_up_to_date)
            except Exception:
                pass
            try:
                worker.error.disconnect(self._on_check_error)
            except Exception:
                pass
            try:
                if worker.isRunning():
                    worker.requestInterruption()
                    # Detach from dialog so Qt never aborts with "QThread: Destroyed while thread is still running"
                    worker.setParent(None)
                    _DETACHED_UPDATE_WORKERS.add(worker)
                    worker.finished.connect(lambda w=worker: _DETACHED_UPDATE_WORKERS.discard(w))
                    worker.finished.connect(worker.deleteLater)
            except RuntimeError:
                pass
            self.check_worker = None

        dl_worker = getattr(self, "download_worker", None)
        if dl_worker is not None:
            try:
                if dl_worker.isRunning():
                    dl_worker.cancel()
                    if not dl_worker.wait(2000):
                        dl_worker.setParent(None)
                        _DETACHED_UPDATE_WORKERS.add(dl_worker)
                        dl_worker.finished.connect(lambda w=dl_worker: _DETACHED_UPDATE_WORKERS.discard(w))
                        dl_worker.finished.connect(dl_worker.deleteLater)
            except RuntimeError:
                pass
            self.download_worker = None

    def _handle_close(self):
        self._cleanup_workers()
        self.reject()

    def reject(self):
        self._cleanup_workers()
        super().reject()

    def closeEvent(self, event):
        self._cleanup_workers()
        super().closeEvent(event)


_DETACHED_UPDATE_WORKERS: set = set()


class UpdaterMixin:
    def check_for_updates(self, interactive: bool = True):
        cleanup_old_installers(max_to_keep=2)
        dialog = CheckUpdateDialog(self, auto_start=True)
        if interactive:
            dialog.exec()
        else:
            dialog.show()

    def trigger_silent_update_check(self):
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            auto_check = str(settings.value("auto_check_updates", "true")).lower() in {"1", "true", "yes"}
            if not auto_check:
                return
        except Exception:
            pass

        repo = get_github_repo()
        channel = get_update_channel()
        worker = CheckUpdateWorker(repo, parent=self, channel=channel)
        if hasattr(self, "_track_worker_thread"):
            self._track_worker_thread(worker)

        def on_update(release_info, asset_info, is_newer):
            if is_newer:
                tag = release_info.get("tag_name", "")
                self.log_activity(f"[UPDATE] New version {tag} available from GitHub.", mark_dirty=False)
                if hasattr(self, "statusBar"):
                    self.statusBar().showMessage(f"★ Update Available: {tag} — Use Help > Check for Updates to install.", 15000)

        worker.update_available.connect(on_update)
        worker.start()
        self._silent_update_worker = worker


__all__ = [
    "get_app_icon",
    "CheckUpdateDialog",
    "UpdaterMixin",
]

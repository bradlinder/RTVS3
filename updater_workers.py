"""Background QThread workers for GitHub release checking and installer downloads.

Strict Single Responsibility: QThread worker lifecycle, progress/status signals,
and cancellation only. Zero PySide6 QtWidgets imports.
"""
from __future__ import annotations

import hashlib
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from PySide6.QtCore import QObject, QThread, Signal
except Exception:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import QObject, QThread, Signal

from updater_core import (
    PROJECT_VERSION,
    _find_release_checksum,
    _is_trusted_download_url,
    cleanup_old_installers,
    fetch_releases,
    format_byte_size,
    get_app_data_dir,
    get_github_repo,
    get_update_channel,
    is_version_newer,
    select_best_asset_for_platform,
)


class CheckUpdateWorker(QThread):
    releases_loaded = Signal(list)
    update_available = Signal(dict, dict, bool)
    up_to_date = Signal(str, str)
    error = Signal(str)

    def __init__(self, repo: str | None = None, parent: QObject | None = None, channel: str | None = None):
        if isinstance(parent, str) and channel is None:
            channel = parent
            parent = None
        super().__init__(parent)
        self.repo = repo or get_github_repo()
        self.channel = channel if channel is not None else get_update_channel()

    def run(self):
        try:
            releases = fetch_releases(self.repo, channel=self.channel)
            if not releases:
                chan_str = "stable" if self.channel == "stable" else "beta or stable"
                self.error.emit(f"No published {chan_str} releases found for repository '{self.repo}'.")
                return

            self.releases_loaded.emit(releases)

            release_data = releases[0]
            tag_name = release_data.get("tag_name", "")
            if not tag_name:
                self.error.emit("GitHub release does not have a valid tag name.")
                return

            assets = release_data.get("assets", [])
            best_asset = select_best_asset_for_platform(assets, target_version=tag_name, repo=self.repo) or {}
            is_newer = is_version_newer(tag_name, PROJECT_VERSION)

            if is_newer:
                self.update_available.emit(release_data, best_asset, True)
            else:
                self.up_to_date.emit(PROJECT_VERSION, tag_name)

        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                self.error.emit(
                    f"No published releases found for repository '{self.repo}'.\n"
                    "Make sure releases have been published on GitHub."
                )
            elif http_err.code == 403:
                self.error.emit(
                    "GitHub API rate limit exceeded or access forbidden.\n"
                    "Please try again later or visit the GitHub repository in your browser."
                )
            else:
                self.error.emit(f"GitHub API error (HTTP {http_err.code}): {http_err.reason}")
        except urllib.error.URLError as url_err:
            self.error.emit(
                f"Network connection failed: {url_err.reason}.\n"
                "Please verify your internet connection and try again."
            )
        except Exception as exc:
            self.error.emit(f"Failed to check for updates: {exc}")


class DownloadUpdateWorker(QThread):
    progress = Signal(int, int, int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, download_url: str, file_name: str, parent: QObject | None = None, release_info: dict | None = None):
        super().__init__(parent)
        self.download_url = download_url
        self.file_name = Path(file_name).name or "update.download"
        self.release_info = release_info or {}
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if not _is_trusted_download_url(self.download_url):
                self.error.emit("Refusing to download: the update URL is not an official GitHub download link.")
                return

            updates_dir = get_app_data_dir() / "updates"
            updates_dir.mkdir(parents=True, exist_ok=True)
            destination = (updates_dir / self.file_name).resolve()
            if updates_dir.resolve() not in destination.parents:
                self.error.emit("Refusing to write the update outside the updates directory.")
                return
            temp_dest = destination.with_suffix(destination.suffix + ".download")

            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"RadioTVSegmenter/{PROJECT_VERSION}"},
            )

            start_time = time.time()
            hasher = hashlib.sha256()
            with urllib.request.urlopen(req, timeout=30) as response:
                total_bytes = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                with open(temp_dest, "wb") as f_out:
                    while True:
                        if self._is_cancelled:
                            f_out.close()
                            if temp_dest.exists():
                                temp_dest.unlink(missing_ok=True)
                            self.error.emit("Download cancelled by user.")
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)

                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        speed_str = f"{format_byte_size(int(speed))}/s"

                        percent = int((downloaded / total_bytes) * 100) if total_bytes > 0 else 0
                        self.progress.emit(percent, downloaded, total_bytes, speed_str)

            if not temp_dest.exists():
                self.error.emit("Downloaded file could not be finalized.")
                return

            expected_sha256 = _find_release_checksum(self.release_info, self.file_name)
            if expected_sha256:
                actual = hasher.hexdigest().lower()
                if actual != expected_sha256.lower():
                    temp_dest.unlink(missing_ok=True)
                    self.error.emit("Downloaded file failed SHA-256 verification and was discarded.")
                    return
                self.checksum_verified = True
            else:
                self.checksum_verified = False

            shutil.move(str(temp_dest), str(destination))
            # Automatically purge older installer packages, retaining recent installers
            cleanup_old_installers(max_to_keep=2)
            self.finished.emit(str(destination))

        except Exception as exc:
            self.error.emit(f"Download failed: {exc}")


__all__ = [
    "CheckUpdateWorker",
    "DownloadUpdateWorker",
]

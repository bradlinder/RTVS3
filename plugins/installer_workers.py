"""Background QThread workers for querying, downloading, and batch installing official plugins."""
from __future__ import annotations

import json
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from prs_shared import PROJECT_VERSION

if TYPE_CHECKING:
    from plugins.manager import PluginManager


def get_official_plugins_catalog(repo: str) -> List[Dict[str, Any]]:
    """Returns the base catalog of official plugins for the repository."""
    return [
        {
            "id": "youtube",
            "name": "YouTube Video Publisher",
            "category": "export",
            "version": PROJECT_VERSION,
            "description": "Publishes broadcast video stories to YouTube with chapter timestamps, frame grabs/custom thumbnails, tags, and assisted YouTube Studio upload.",
            "author": "Radio & TV Segmenter Team",
            "asset_name": f"rtvs-plugin-youtube-v{PROJECT_VERSION}.rtvs-addon",
            "download_url": f"https://github.com/{repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-youtube-v{PROJECT_VERSION}.rtvs-addon",
            "fallback_url": f"https://raw.githubusercontent.com/{repo}/main/plugins/youtube.rtvs-addon",
        },
        {
            "id": "wordpress",
            "name": "WordPress Publisher",
            "category": "export",
            "version": PROJECT_VERSION,
            "description": "Publishes segmented audio/video stories, transcripts, excerpts, and custom featured images directly to WordPress posts via the WP REST API.",
            "author": "Radio & TV Segmenter Team",
            "asset_name": f"rtvs-plugin-wordpress-v{PROJECT_VERSION}.rtvs-addon",
            "download_url": f"https://github.com/{repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-wordpress-v{PROJECT_VERSION}.rtvs-addon",
            "fallback_url": f"https://raw.githubusercontent.com/{repo}/main/plugins/wordpress.rtvs-addon",
        },
        {
            "id": "translation",
            "name": "Language Translation",
            "category": "ai",
            "version": PROJECT_VERSION,
            "description": "Provides local multi-language neural machine translation (MarianMT and NLLB models) with synchronized bilingual split-view editing and translated exports.",
            "author": "Radio & TV Segmenter Team",
            "asset_name": f"rtvs-plugin-translation-v{PROJECT_VERSION}.rtvs-addon",
            "download_url": f"https://github.com/{repo}/releases/download/v{PROJECT_VERSION}/rtvs-plugin-translation-v{PROJECT_VERSION}.rtvs-addon",
            "fallback_url": f"https://raw.githubusercontent.com/{repo}/main/plugins/translation.rtvs-addon",
        },
    ]


class GitHubPluginsWorker(QThread):
    """Fetches list of available plugins from GitHub release assets and official catalog."""
    finished = Signal(bool, list, str)

    def __init__(self, repo: str, parent=None):
        super().__init__(parent)
        self.repo = repo

    def run(self):
        plugins_catalog = get_official_plugins_catalog(self.repo)

        # Try querying GitHub Releases API
        api_url = f"https://api.github.com/repos/{self.repo}/releases?per_page=10"
        headers = {"User-Agent": f"RadioTVSegmenter/{PROJECT_VERSION}"}
        req = urllib.request.Request(api_url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    releases = json.loads(response.read().decode("utf-8"))
                    best_assets: Dict[str, Dict[str, Any]] = {}
                    catalog_by_id = {item["id"]: item for item in plugins_catalog}

                    for rel in releases:
                        tag_ver = rel.get("tag_name", "").lstrip("v")
                        for asset in rel.get("assets", []):
                            aname = asset.get("name", "")
                            if not (aname.endswith(".rtvs-addon") or aname.endswith(".zip")):
                                continue

                            detected_id = None
                            detected_ver = tag_ver or PROJECT_VERSION

                            for pid in catalog_by_id:
                                if f"plugin-{pid}" in aname or f"{pid}.rtvs-addon" in aname:
                                    detected_id = pid
                                    break

                            if detected_id:
                                durl = asset.get("browser_download_url", "")
                                asize = asset.get("size", 0)
                                if detected_id not in best_assets or (tag_ver and tag_ver == PROJECT_VERSION):
                                    best_assets[detected_id] = {
                                        "url": durl,
                                        "size": asize,
                                        "version": detected_ver,
                                        "asset_name": aname,
                                    }

                    for pid, adata in best_assets.items():
                        if pid in catalog_by_id:
                            catalog_by_id[pid]["download_url"] = adata["url"]
                            catalog_by_id[pid]["version"] = adata["version"]
                            catalog_by_id[pid]["asset_name"] = adata["asset_name"]
                            catalog_by_id[pid]["size_bytes"] = adata["size"]

                    self.finished.emit(True, list(catalog_by_id.values()), "Live releases catalog synchronized successfully.")
                    return
        except Exception as exc:
            print(f"[PLUGINS] GitHub releases check failed ({exc}), using standard release catalog.")

        self.finished.emit(True, plugins_catalog, "Connected via official catalog cache.")


class GitHubDownloadWorker(QThread):
    """Downloads an add-on package in background with progress updates."""
    progress = Signal(int, str)
    finished = Signal(bool, str, str)

    def __init__(self, download_url: str, local_dest: Path, fallback_local_addon: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.local_dest = local_dest
        self.fallback_local_addon = fallback_local_addon
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        headers = {"User-Agent": f"RadioTVSegmenter/{PROJECT_VERSION}"}
        req = urllib.request.Request(self.download_url, headers=headers)
        success = False
        last_error = ""

        try:
            self.progress.emit(10, "Connecting to GitHub server...")
            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.headers.get("content-length", 0))
                bytes_so_far = 0
                chunk_size = 32 * 1024
                self.local_dest.parent.mkdir(parents=True, exist_ok=True)

                with open(self.local_dest, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            self.finished.emit(False, "", "Download cancelled by user.")
                            return
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_so_far += len(chunk)
                        if total_size > 0:
                            pct = int((bytes_so_far / total_size) * 85) + 10
                            self.progress.emit(min(pct, 95), f"Downloading ({bytes_so_far // 1024} KB / {total_size // 1024} KB)...")
                        else:
                            self.progress.emit(50, f"Downloading ({bytes_so_far // 1024} KB)...")
                success = True
        except Exception as exc:
            last_error = str(exc)
            print(f"[PLUGINS] Download from {self.download_url} failed: {exc}")

        if not success and self.fallback_local_addon and self.fallback_local_addon.exists():
            try:
                self.progress.emit(60, "Copying from local package cache...")
                self.local_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.fallback_local_addon, self.local_dest)
                success = True
            except Exception as copy_exc:
                last_error = str(copy_exc)

        if success and self.local_dest.exists() and self.local_dest.stat().st_size > 0:
            self.progress.emit(100, "Download complete!")
            self.finished.emit(True, str(self.local_dest), "")
        else:
            self.finished.emit(False, "", f"Failed to download plugin: {last_error or 'Network error'}")


class GitHubBatchDownloadWorker(QThread):
    """Downloads and installs a batch of add-on packages in sequence with progress updates."""
    progress = Signal(int, str)
    finished = Signal(int, int, list)  # (succeeded_count, failed_count, error_messages)

    def __init__(self, items: List[Dict[str, Any]], manager: Any, enable_after: bool = False, parent=None):
        super().__init__(parent)
        self.items = items
        self.manager = manager
        self.enable_after = enable_after
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.items)
        if total == 0:
            self.finished.emit(0, 0, [])
            return

        succeeded = 0
        failed = 0
        errors = []

        headers = {"User-Agent": f"RadioTVSegmenter/{PROJECT_VERSION}"}
        bundled_addons = self.manager.get_bundled_addons()

        for idx, item in enumerate(self.items):
            if self._is_cancelled:
                errors.append("Batch download cancelled by user.")
                break

            plugin_id = item["id"]
            plugin_name = item["name"]
            asset_name = item.get("asset_name", f"{plugin_id}.rtvs-addon")
            download_url = item.get("download_url") or item.get("fallback_url")
            fallback_addon = bundled_addons.get(plugin_id)

            dest_file = Path(tempfile.gettempdir()) / f"rtvs_download_{plugin_id}_{asset_name}"
            success = False
            last_error = ""

            base_pct = int((idx / total) * 100)
            next_pct = int(((idx + 1) / total) * 100)
            self.progress.emit(base_pct, f"Downloading ({idx + 1}/{total}): {plugin_name}...")

            if download_url:
                try:
                    req = urllib.request.Request(download_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=15) as response:
                        total_size = int(response.headers.get("content-length", 0))
                        bytes_so_far = 0
                        chunk_size = 32 * 1024
                        dest_file.parent.mkdir(parents=True, exist_ok=True)

                        with open(dest_file, "wb") as f:
                            while True:
                                if self._is_cancelled:
                                    break
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                bytes_so_far += len(chunk)
                                if total_size > 0:
                                    item_pct = min(int((bytes_so_far / total_size) * (next_pct - base_pct)), next_pct - base_pct)
                                    self.progress.emit(base_pct + item_pct, f"Downloading ({idx + 1}/{total}): {plugin_name} ({bytes_so_far // 1024} KB / {total_size // 1024} KB)...")
                    if not self._is_cancelled and dest_file.exists() and dest_file.stat().st_size > 0:
                        success = True
                except Exception as exc:
                    last_error = str(exc)
                    print(f"[PLUGINS] Batch download of {plugin_name} failed: {exc}")

            if not success and fallback_addon and fallback_addon.exists():
                try:
                    self.progress.emit(base_pct + 10, f"Copying ({idx + 1}/{total}): {plugin_name} from local cache...")
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(fallback_addon, dest_file)
                    success = True
                except Exception as copy_exc:
                    last_error = str(copy_exc)

            if success and dest_file.exists() and dest_file.stat().st_size > 0:
                self.progress.emit(next_pct, f"Installing ({idx + 1}/{total}): {plugin_name}...")
                try:
                    ok = self.manager.install_addon(dest_file, enable=self.enable_after, load_ui=False)
                    if ok:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{plugin_name}: Failed to extract valid manifest from package.")
                except Exception as inst_exc:
                    failed += 1
                    errors.append(f"{plugin_name}: {inst_exc}")
                finally:
                    try:
                        dest_file.unlink(missing_ok=True)
                    except Exception:
                        pass
            else:
                failed += 1
                errors.append(f"{plugin_name}: {last_error or 'Network download error'}")

        self.progress.emit(100, "Batch operation complete.")
        self.finished.emit(succeeded, failed, errors)

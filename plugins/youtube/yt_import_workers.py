"""Background QThread workers for yt-dlp provisioning, YouTube metadata probing, and video downloads.

Strict Single Responsibility: worker lifecycle, cancellation, and signal emission only.
Zero Qt widget/dialog instantiation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from remote_media_cache import (
    DEFAULT_CACHE_CAP_GB,
    RemoteMediaCacheManager,
    make_cache_key,
)
from plugins.youtube.yt_dlp_runner import (
    DEFAULT_YOUTUBE_QUALITY,
    build_youtube_project_stem,
    download_youtube_video,
    find_yt_dlp_binary,
    install_or_update_yt_dlp,
    normalize_quality_preset,
    probe_youtube_video,
)


class YtDlpInstallWorker(QThread):
    """Background worker that installs or updates the managed yt-dlp binary."""

    progress = Signal(int, str)
    finished = Signal(str, str)  # binary_path, version_str
    failed = Signal(str)

    def __init__(self, parent=None, base_dir: Optional[Path] = None):
        super().__init__(parent)
        self._base_dir = base_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            bin_path, version = install_or_update_yt_dlp(
                base_dir=self._base_dir,
                progress_callback=lambda pct, msg: self.progress.emit(int(pct), str(msg)),
                cancel_check=lambda: self._cancelled,
            )
            self.finished.emit(str(bin_path), str(version))
        except InterruptedError:
            self.failed.emit("yt-dlp update cancelled.")
        except Exception as exc:
            self.failed.emit(str(exc))


class YouTubeProbeWorker(QThread):
    """Background worker that ensures yt-dlp is installed and probes YouTube video metadata."""

    progress = Signal(int, str)
    finished = Signal(dict)
    failed = Signal(str, dict)  # message, error_meta

    def __init__(
        self,
        url_or_id: str,
        cookies_browser: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.url_or_id = url_or_id
        self.cookies_browser = cookies_browser
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            yt_bin = find_yt_dlp_binary()
            if yt_bin is None:
                self.progress.emit(5, "yt-dlp not found. Installing automatically...")
                yt_bin, _ver = install_or_update_yt_dlp(
                    progress_callback=lambda pct, msg: self.progress.emit(min(70, int(pct * 0.7)), msg),
                    cancel_check=lambda: self._cancelled,
                )
            if self._cancelled:
                self.failed.emit("Metadata lookup cancelled.", {"category": "cancelled"})
                return
            self.progress.emit(75, "Fetching video details from YouTube...")
            meta = probe_youtube_video(
                self.url_or_id,
                yt_dlp_bin=yt_bin,
                cookies_browser=self.cookies_browser,
            )
            if self._cancelled:
                self.failed.emit("Metadata lookup cancelled.", {"category": "cancelled"})
                return
            self.progress.emit(100, "Video details loaded.")
            self.finished.emit(meta)
        except InterruptedError:
            self.failed.emit("Operation cancelled.", {"category": "cancelled"})
        except Exception as exc:
            err_meta = getattr(exc, "yt_dlp_error", None)
            if not isinstance(err_meta, dict):
                err_meta = {"category": "generic", "needs_update": False, "needs_cookies": False}
            self.failed.emit(str(exc), err_meta)


class YouTubeDownloadWorker(QThread):
    """Background worker that downloads a YouTube video into the Managed Remote Media Cache."""

    progress = Signal(int, str)
    finished = Signal(dict)
    failed = Signal(str, dict)  # message, error_meta

    def __init__(
        self,
        url_or_id: str,
        video_meta: Optional[Dict[str, Any]] = None,
        quality_preset: str = DEFAULT_YOUTUBE_QUALITY,
        cookies_browser: str = "",
        force_redownload: bool = False,
        cache_cap_gb: float = DEFAULT_CACHE_CAP_GB,
        protected_paths: Optional[List[str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.url_or_id = url_or_id
        self.video_meta = dict(video_meta or {})
        self.quality_preset = normalize_quality_preset(quality_preset)
        self.cookies_browser = cookies_browser
        self.force_redownload = bool(force_redownload)
        self.cache_cap_gb = float(cache_cap_gb if cache_cap_gb is not None else DEFAULT_CACHE_CAP_GB)
        self.protected_paths = list(protected_paths or [])
        self._cancelled = False
        self._active_proc: Optional[subprocess.Popen] = None

    def cancel(self) -> None:
        self._cancelled = True
        proc = self._active_proc
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass

    def _set_active_proc(self, proc: Optional[subprocess.Popen]) -> None:
        self._active_proc = proc

    def run(self) -> None:
        try:
            yt_bin = find_yt_dlp_binary()
            if yt_bin is None:
                self.progress.emit(3, "Installing yt-dlp automatically...")
                yt_bin, _ver = install_or_update_yt_dlp(
                    progress_callback=lambda pct, msg: self.progress.emit(min(15, int(pct * 0.15)), msg),
                    cancel_check=lambda: self._cancelled,
                )

            meta = dict(self.video_meta)
            if not meta.get("video_id"):
                self.progress.emit(16, "Fetching video details from YouTube...")
                meta = probe_youtube_video(
                    self.url_or_id,
                    yt_dlp_bin=yt_bin,
                    cookies_browser=self.cookies_browser,
                )

            if self._cancelled:
                self.failed.emit("Download cancelled.", {"category": "cancelled"})
                return

            vid = str(meta.get("video_id") or "")
            canonical_url = str(meta.get("canonical_url") or self.url_or_id)
            title = str(meta.get("title") or f"YouTube_{vid}")
            upload_date = str(meta.get("upload_date") or "")

            cache_mgr = RemoteMediaCacheManager()
            cache_key = make_cache_key("youtube", vid, self.quality_preset)

            cached_hit = None if self.force_redownload else cache_mgr.get_existing_cached_file(cache_key, touch=True)
            if cached_hit is not None:
                self.progress.emit(100, "Loaded from local cache.")
                self.finished.emit({
                    "file_path": str(cached_hit),
                    "cache_key": cache_key,
                    "from_cache": True,
                    "quality_preset": self.quality_preset,
                    "video_meta": meta,
                })
                return

            out_dir = cache_mgr.get_provider_dir("youtube")
            stem = f"{build_youtube_project_stem(title, upload_date, vid)}_{vid}_{self.quality_preset}"

            self.progress.emit(18, f"Starting YouTube download ({self.quality_preset})...")
            downloaded_path = download_youtube_video(
                canonical_url,
                output_dir=out_dir,
                filename_stem=stem,
                quality_preset=self.quality_preset,
                yt_dlp_bin=yt_bin,
                cookies_browser=self.cookies_browser,
                progress_callback=lambda pct, msg: self.progress.emit(max(18, min(98, int(pct))), str(msg)),
                cancel_check=lambda: self._cancelled,
                process_callback=self._set_active_proc,
            )

            entry = cache_mgr.register_download(
                cache_key=cache_key,
                file_path=downloaded_path,
                provider="youtube",
                source_url=canonical_url,
                source_id=vid,
                quality_preset=self.quality_preset,
                title=title,
                upload_date=upload_date,
            )

            # Enforce configured LRU cap while protecting the newly downloaded file and active media
            protected = list(self.protected_paths) + [str(downloaded_path)]
            eviction = cache_mgr.enforce_size_cap(self.cache_cap_gb, protected_paths=protected)

            self.progress.emit(100, "Download complete.")
            self.finished.emit({
                "file_path": str(downloaded_path),
                "cache_key": cache_key,
                "cache_entry": entry,
                "from_cache": False,
                "quality_preset": self.quality_preset,
                "video_meta": meta,
                "eviction": eviction,
            })
        except InterruptedError:
            self.failed.emit("YouTube download cancelled.", {"category": "cancelled"})
        except Exception as exc:
            err_meta = getattr(exc, "yt_dlp_error", None)
            if not isinstance(err_meta, dict):
                err_meta = {"category": "generic", "needs_update": False, "needs_cookies": False}
            self.failed.emit(str(exc), err_meta)


__all__ = [
    "YtDlpInstallWorker",
    "YouTubeProbeWorker",
    "YouTubeDownloadWorker",
]

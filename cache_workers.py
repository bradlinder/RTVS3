"""Radio & TV Segmenter — Background QThread workers for ClearCacheDialog.

Keeps disk scanning and cache purging off the Qt main GUI thread while
maintaining clean single-responsibility domain separation from cache_manager.py.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal


_DETACHED_CACHE_WORKERS: set[QThread] = set()


def detach_cache_worker(worker: QThread | None, wait_ms: int = 150) -> None:
    """Safely interrupt, disconnect, and wait/detach an active cache worker thread."""
    if worker is None:
        return
    try:
        worker.requestInterruption()
    except Exception:
        pass
    for sig_name in ("finished_scan", "failed_scan", "finished_purge", "failed_purge"):
        sig = getattr(worker, sig_name, None)
        if sig is not None:
            try:
                sig.disconnect()
            except Exception:
                pass
    try:
        running = bool(worker.isRunning())
    except Exception:
        running = False
    if running:
        try:
            finished = bool(worker.wait(wait_ms))
        except Exception:
            finished = False
        if not finished:
            try:
                worker.setParent(None)
            except Exception:
                pass
            _DETACHED_CACHE_WORKERS.add(worker)
            try:
                worker.finished.connect(
                    lambda w=worker: (
                        _DETACHED_CACHE_WORKERS.discard(w),
                        w.deleteLater(),
                    )
                )
            except Exception:
                pass
            return
    try:
        worker.deleteLater()
    except Exception:
        pass


class CacheScanWorker(QThread):
    """Background worker that scans temporary cache disk usage."""

    finished_scan = Signal(dict)
    failed_scan = Signal(str)

    def __init__(
        self,
        project_dirs=None,
        include_global_caches: bool = True,
        include_settings_dirs: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._project_dirs = list(project_dirs) if project_dirs else []
        self._include_global_caches = bool(include_global_caches)
        self._include_settings_dirs = bool(include_settings_dirs)

    def run(self):
        from cache_manager import get_cache_disk_usage

        try:
            stats = get_cache_disk_usage(
                project_dirs=self._project_dirs,
                include_global_caches=self._include_global_caches,
                include_settings_dirs=self._include_settings_dirs,
                cancel_check=self.isInterruptionRequested,
            )
            if not self.isInterruptionRequested():
                self.finished_scan.emit(stats)
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.failed_scan.emit(str(exc))


class CachePurgeWorker(QThread):
    """Background worker that purges selected caches and rescans remaining disk usage."""

    finished_purge = Signal(int, int, dict)
    failed_purge = Signal(str)

    def __init__(
        self,
        clear_thumbnails: bool = True,
        clear_waveforms: bool = True,
        clear_audio_extracts: bool = True,
        purge_project_dirs=None,
        scan_project_dirs=None,
        include_global_caches: bool = True,
        include_settings_dirs: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._clear_thumbnails = bool(clear_thumbnails)
        self._clear_waveforms = bool(clear_waveforms)
        self._clear_audio_extracts = bool(clear_audio_extracts)
        self._purge_project_dirs = list(purge_project_dirs) if purge_project_dirs else []
        self._scan_project_dirs = list(scan_project_dirs) if scan_project_dirs else []
        self._include_global_caches = bool(include_global_caches)
        self._include_settings_dirs = bool(include_settings_dirs)

    def run(self):
        from cache_manager import get_cache_disk_usage, purge_caches

        try:
            files_deleted, bytes_freed = purge_caches(
                clear_thumbnails=self._clear_thumbnails,
                clear_waveforms=self._clear_waveforms,
                clear_audio_extracts=self._clear_audio_extracts,
                project_dirs=self._purge_project_dirs,
                include_global_caches=self._include_global_caches,
                cancel_check=self.isInterruptionRequested,
            )
            if self.isInterruptionRequested():
                return
            stats = get_cache_disk_usage(
                project_dirs=self._scan_project_dirs,
                include_global_caches=self._include_global_caches,
                include_settings_dirs=self._include_settings_dirs,
                cancel_check=self.isInterruptionRequested,
            )
            if not self.isInterruptionRequested():
                self.finished_purge.emit(files_deleted, bytes_freed, stats)
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.failed_purge.emit(str(exc))

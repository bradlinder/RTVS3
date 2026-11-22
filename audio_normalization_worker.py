"""Background QThread worker for non-blocking EBU R128 loudness probing."""

from __future__ import annotations

from pathlib import Path

from audio_normalization import (
    DEFAULT_QUIET_THRESHOLD_DBFS,
    DEFAULT_QUIET_THRESHOLD_LUFS,
    DEFAULT_TARGET_LUFS,
    probe_media_loudness,
)

try:
    from PySide6.QtCore import QObject, QThread, Signal
except ImportError:
    class QObject:  # type: ignore
        def __init__(self, parent=None):
            pass

    class QThread:  # type: ignore
        def __init__(self, parent=None):
            pass

        def start(self):
            self.run()

        def isRunning(self):
            return False

    def Signal(*args, **kwargs):  # type: ignore
        class _Sig:
            def connect(self, slot):
                pass

            def disconnect(self, slot=None):
                pass

            def emit(self, *a, **k):
                pass
        return _Sig()


class AudioLoudnessProbeWorker(QThread):
    """Background worker thread to probe audio loudness without freezing Qt GUI."""

    probed = Signal(object)  # LoudnessReport
    error = Signal(str)

    def __init__(
        self,
        media_path: str | Path,
        target_lufs: float = DEFAULT_TARGET_LUFS,
        quiet_threshold_lufs: float = DEFAULT_QUIET_THRESHOLD_LUFS,
        quiet_threshold_dbfs: float = DEFAULT_QUIET_THRESHOLD_DBFS,
        timeout: float = 15.0,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.media_path = str(media_path)
        self.target_lufs = float(target_lufs)
        self.quiet_threshold_lufs = float(quiet_threshold_lufs)
        self.quiet_threshold_dbfs = float(quiet_threshold_dbfs)
        self.timeout = float(timeout)
        self._canceled = False

    def cancel(self):
        """Request worker cancellation."""
        self._canceled = True

    def run(self):
        """Execute non-blocking probe in background."""
        if self._canceled:
            return
        report = probe_media_loudness(
            self.media_path,
            target_lufs=self.target_lufs,
            quiet_threshold_lufs=self.quiet_threshold_lufs,
            quiet_threshold_dbfs=self.quiet_threshold_dbfs,
            timeout=self.timeout,
        )
        if self._canceled:
            return
        if report.error:
            self.error.emit(report.error)
        self.probed.emit(report)


__all__ = ["AudioLoudnessProbeWorker"]

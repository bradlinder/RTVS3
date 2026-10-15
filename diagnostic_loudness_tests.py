"""Radio & TV Story Segmenter — Diagnostic Loudness Normalization & Auto-Boost Test Suite."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from diagnostic_helpers import DiagnosticItem


class DiagnosticLoudnessTestsMixin:
    """Diagnostic tests for Smart Hybrid Audio Loudness Probing & Normalization."""

    def _test_smart_hybrid_audio_loudness_probing(self, item: DiagnosticItem):
        """Validates fast multi-window EBU R128 loudness & peak probing across synthetic test media."""
        from audio_normalization import (
            DEFAULT_TARGET_LUFS,
            DEFAULT_TARGET_DBFS,
            DEFAULT_QUIET_THRESHOLD_LUFS,
            DEFAULT_QUIET_THRESHOLD_DBFS,
            LoudnessReport,
            parse_ebur128_summary,
            probe_media_loudness,
            AudioLoudnessProbeWorker,
        )

        # 1. Verify parser on simulated ebur128 output
        sample_stderr = """
[Parsed_ebur128_0 @ 0x55651befde40] Summary:

  Integrated loudness:
    I:         -28.5 LUFS
    Threshold: -38.5 LUFS

  Loudness range:
    LRA:         6.4 LU
    Threshold: -48.5 LUFS
    LRA low:   -32.0 LUFS
    LRA high:  -25.6 LUFS

  True peak:
    Peak:      -14.2 dBFS
"""
        i, lra, peak = parse_ebur128_summary(sample_stderr)
        assert abs(i - (-28.5)) < 0.01, f"Expected -28.5 LUFS, got {i}"
        assert abs(lra - 6.4) < 0.01, f"Expected 6.4 LU, got {lra}"
        assert abs(peak - (-14.2)) < 0.01, f"Expected -14.2 dBFS, got {peak}"

        # 2. Verify synthetic quiet audio probing
        temp_dir = tempfile.mkdtemp(prefix="rtvs_test_loudness_")
        try:
            quiet_wav = Path(temp_dir) / "quiet_test.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=1000:duration=4",
                    "-af", "volume=-32dB",
                    str(quiet_wav),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            report = probe_media_loudness(quiet_wav)
            assert report.error is None, f"Probing encountered error: {report.error}"
            assert report.is_quiet is True, "Synthetic -32dB audio should be flagged as quiet"
            assert report.integrated_lufs < -24.0, f"Expected integrated LUFS < -24.0, got {report.integrated_lufs}"
            assert report.true_peak_dbtp < -20.0, f"Expected peak < -20.0, got {report.true_peak_dbtp}"
            assert report.sampled is False, "Short audio (4s) should not use multi-window sampling"

            # 3. Verify AudioLoudnessProbeWorker initialization and cancel
            worker = AudioLoudnessProbeWorker(quiet_wav)
            assert worker.target_lufs == DEFAULT_TARGET_LUFS
            assert worker.quiet_threshold_lufs == DEFAULT_QUIET_THRESHOLD_LUFS
            worker.cancel()
            assert worker._canceled is True

            item.status = "PASS"
            item.message = f"EBU R128 loudness probe verified (I={report.integrated_lufs:.1f} LUFS, Peak={report.true_peak_dbtp:.1f} dBFS, is_quiet={report.is_quiet})"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

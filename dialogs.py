"""Radio & TV Story Segmenter — Audio Loudness Normalization & Telemetry Dialog.

Provides an on-demand modal dialog accessible via Tools -> Normalize Audio Loudness...
allowing users to inspect integrated LUFS, loudness range (LRA), and true peak (dBTP/dBFS),
preview required gain adjustments across broadcast standards, and apply non-destructive
normalization sidecars or reset to the original media.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QMessageBox,
    QProgressBar, QWidget
)

from prs_shared import (
    APP_DISPLAY_NAME,
    DEFAULT_TARGET_LUFS,
    DEFAULT_TARGET_DBFS,
    DEFAULT_QUIET_THRESHOLD_LUFS,
    DEFAULT_QUIET_THRESHOLD_DBFS,
    LoudnessReport,
    probe_media_loudness,
    normalize_audio_sidecar,
    get_effective_audio_for_processing,
    AudioLoudnessProbeWorker,
)
from core_utils import make_dialog_maximizable

logger = logging.getLogger(__name__)

__all__ = ["AudioLoudnessNormalizationDialog"]


class AudioLoudnessNormalizationDialog(QDialog):
    """Dedicated modal dialog for inspecting media loudness metrics and manually normalizing."""

    def __init__(self, parent=None, auto_probe: bool = True):
        qt_parent = parent if isinstance(parent, QWidget) else None
        super().__init__(qt_parent)
        self.main_win = parent
        self._auto_probe = auto_probe
        self.setWindowTitle(f"Audio Loudness Normalization & Telemetry — {APP_DISPLAY_NAME}")
        self.resize(580, 490)
        make_dialog_maximizable(self)
        self._probe_worker: Optional[AudioLoudnessProbeWorker] = None
        self._current_report: Optional[LoudnessReport] = None

        self._build_ui()
        self._load_current_data()

    def _stop_probe_worker(self):
        worker = self._probe_worker
        if worker is not None:
            self._probe_worker = None
            try:
                worker.probed.disconnect()
            except Exception:
                pass
            try:
                worker.error.disconnect()
            except Exception:
                pass
            if worker.isRunning():
                try:
                    worker.requestInterruption()
                except Exception:
                    pass
                worker.quit()
                worker.wait(2000)

    def closeEvent(self, event):
        self._stop_probe_worker()
        super().closeEvent(event)

    def reject(self):
        self._stop_probe_worker()
        super().reject()

    def accept(self):
        self._stop_probe_worker()
        super().accept()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # File Banner
        self.lbl_file = QLabel("Media File: None")
        self.lbl_file.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.lbl_file)

        # 1. Measured Audio Metrics Group
        grp_metrics = QGroupBox("Measured Audio Loudness Metrics")
        form_metrics = QFormLayout(grp_metrics)

        self.lbl_integrated = QLabel("Measuring...")
        form_metrics.addRow("Integrated Loudness (I):", self.lbl_integrated)

        self.lbl_lra = QLabel("Measuring...")
        form_metrics.addRow("Loudness Range (LRA):", self.lbl_lra)

        self.lbl_peak = QLabel("Measuring...")
        form_metrics.addRow("True Peak (TP):", self.lbl_peak)

        self.lbl_status = QLabel("Measuring...")
        form_metrics.addRow("Loudness Status:", self.lbl_status)

        layout.addWidget(grp_metrics)

        # 2. Target Standard & Gain Preview Group
        grp_target = QGroupBox("Target Loudness Standard & Gain Preview")
        form_target = QFormLayout(grp_target)

        self.combo_standard = QComboBox()
        standards = [
            ("Broadcast Standard (-16.0 LUFS / -1.5 dBTP)", "broadcast", -16.0, -1.5),
            ("Podcast / Web Standard (-14.0 LUFS / -1.0 dBTP)", "podcast", -14.0, -1.0),
            ("EBU R128 Television Standard (-24.0 LUFS / -1.0 dBTP)", "ebur128", -24.0, -1.0),
            ("Peak Normalization (-3.0 dBFS)", "peak", -18.0, -3.0),
        ]
        for lbl, code, lufs, tp in standards:
            self.combo_standard.addItem(lbl, {"code": code, "target_lufs": lufs, "max_true_peak": tp})
        self.combo_standard.currentIndexChanged.connect(self._on_standard_changed)
        form_target.addRow("Target Standard:", self.combo_standard)

        self.spin_target_lufs = QDoubleSpinBox()
        self.spin_target_lufs.setRange(-36.0, -10.0)
        self.spin_target_lufs.setSingleStep(0.5)
        self.spin_target_lufs.setSuffix(" LUFS")
        self.spin_target_lufs.setValue(-16.0)
        self.spin_target_lufs.valueChanged.connect(self._update_gain_preview)
        form_target.addRow("Target Integrated LUFS:", self.spin_target_lufs)

        self.spin_max_tp = QDoubleSpinBox()
        self.spin_max_tp.setRange(-12.0, 0.0)
        self.spin_max_tp.setSingleStep(0.5)
        self.spin_max_tp.setSuffix(" dBTP")
        self.spin_max_tp.setValue(-1.5)
        self.spin_max_tp.valueChanged.connect(self._update_gain_preview)
        form_target.addRow("Maximum True Peak:", self.spin_max_tp)

        self.lbl_gain_preview = QLabel("Calculating...")
        self.lbl_gain_preview.setStyleSheet("font-weight: bold;")
        form_target.addRow("Gain Adjustment:", self.lbl_gain_preview)

        layout.addWidget(grp_target)

        # Progress Bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 0)
        self.prog_bar.hide()
        layout.addWidget(self.prog_bar)

        # 3. Action Buttons
        btn_layout = QHBoxLayout()

        self.btn_reanalyze = QPushButton("Re-Analyze")
        self.btn_reanalyze.clicked.connect(self.reanalyze)
        btn_layout.addWidget(self.btn_reanalyze)

        self.btn_reset = QPushButton("Reset to Original")
        self.btn_reset.clicked.connect(self.reset_to_original)
        btn_layout.addWidget(self.btn_reset)

        self.btn_apply = QPushButton("Apply Normalization")
        self.btn_apply.setStyleSheet("font-weight: bold;")
        self.btn_apply.clicked.connect(self.apply_normalization)
        btn_layout.addWidget(self.btn_apply)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _load_current_data(self):
        audio_file = getattr(self.main_win, "audio_file", None) if self.main_win else None
        if not audio_file or not Path(audio_file).is_file():
            self.lbl_file.setText("Media File: None (Please open a media file first)")
            self.lbl_integrated.setText("N/A")
            self.lbl_lra.setText("N/A")
            self.lbl_peak.setText("N/A")
            self.lbl_status.setText("No media file loaded.")
            self.lbl_gain_preview.setText("N/A")
            self.btn_reanalyze.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self.btn_apply.setEnabled(False)
            return

        self.lbl_file.setText(f"Media File: {Path(audio_file).name}")
        self.btn_reanalyze.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.btn_apply.setEnabled(True)

        # Load saved standard preference
        if self.main_win and hasattr(self.main_win, "settings_store"):
            settings = self.main_win.settings_store
            saved_std = str(settings.value("target_standard", "broadcast") or "broadcast").lower()
            for idx in range(self.combo_standard.count()):
                d = self.combo_standard.itemData(idx)
                if d and d.get("code") == saved_std:
                    self.combo_standard.setCurrentIndex(idx)
                    break
            self.spin_target_lufs.setValue(float(settings.value("target_lufs", -16.0) or -16.0))
            self.spin_max_tp.setValue(float(settings.value("max_true_peak", -1.5) or -1.5))

        # Check existing project metadata first
        meta = getattr(self.main_win, "project_metadata", None) if self.main_win else None
        if isinstance(meta, dict) and "audio_normalization" in meta:
            norm_info = meta["audio_normalization"]
            i_lufs = norm_info.get("probed_integrated_lufs")
            lra = norm_info.get("probed_lra_lu")
            tp = norm_info.get("probed_true_peak_dbtp")
            if i_lufs is not None:
                self._current_report = LoudnessReport(
                    media_path=str(audio_file),
                    integrated_lufs=float(i_lufs),
                    loudness_range_lu=float(lra or 0.0),
                    true_peak_dbtp=float(tp or -70.0),
                    is_quiet=bool(norm_info.get("is_quiet", False)),
                )
                self._display_report(self._current_report)
                return

        # Otherwise trigger background probe
        if getattr(self, "_auto_probe", True):
            self.reanalyze()

    def _on_standard_changed(self, index):
        data = self.combo_standard.itemData(index)
        if data:
            self.spin_target_lufs.setValue(data["target_lufs"])
            self.spin_max_tp.setValue(data["max_true_peak"])
        self._update_gain_preview()

    def reanalyze(self):
        audio_file = getattr(self.main_win, "audio_file", None) if self.main_win else None
        if not audio_file or not Path(audio_file).is_file():
            return

        self._stop_probe_worker()

        self.prog_bar.show()
        self.lbl_integrated.setText("Measuring EBU R128 integrated loudness...")
        self.lbl_lra.setText("Analyzing dynamic loudness range...")
        self.lbl_peak.setText("Measuring true peak...")
        self.lbl_status.setText("Probing...")
        self.btn_reanalyze.setEnabled(False)
        self.btn_apply.setEnabled(False)

        worker = AudioLoudnessProbeWorker(
            audio_file,
            target_lufs=self.spin_target_lufs.value(),
            timeout=15.0,
            parent=self,
        )
        worker.probed.connect(self._on_probe_finished)
        worker.error.connect(self._on_probe_error)
        self._probe_worker = worker
        worker.start()

    def _on_probe_finished(self, report: LoudnessReport):
        self.prog_bar.hide()
        self.btn_reanalyze.setEnabled(True)
        self.btn_apply.setEnabled(True)
        self._current_report = report
        self._display_report(report)

    def _on_probe_error(self, err_msg: str):
        self.prog_bar.hide()
        self.btn_reanalyze.setEnabled(True)
        self.btn_apply.setEnabled(True)
        self.lbl_status.setText(f"Probe Error: {err_msg}")

    def _display_report(self, report: LoudnessReport):
        self.lbl_lra.setText(f"{report.loudness_range_lu:.1f} LU")

        # Status text & normalized sidecar metrics
        meta = getattr(self.main_win, "project_metadata", None) if self.main_win else None
        norm_info = meta.get("audio_normalization", {}) if isinstance(meta, dict) else {}
        is_normalized = bool(norm_info and norm_info.get("normalized_sidecar"))

        if is_normalized:
            gain = norm_info.get("loudness_gain_db", 0.0)
            norm_lufs = norm_info.get("normalized_integrated_lufs")
            if norm_lufs is None:
                norm_lufs = round(min(0.0, report.integrated_lufs + gain), 2)
            norm_tp = norm_info.get("normalized_true_peak_dbtp", -1.5)

            self.lbl_integrated.setText(f"{report.integrated_lufs:.1f} LUFS (Source)  ➔  {norm_lufs:.1f} LUFS (Normalized)")
            self.lbl_peak.setText(f"{report.true_peak_dbtp:.1f} dBTP (Source)  ➔  {norm_tp:.1f} dBTP (Normalized)")
            self.lbl_status.setText(f"Active Normalized Sidecar ({norm_lufs:.1f} LUFS achieved, +{gain:.1f} dB applied)")
        else:
            self.lbl_integrated.setText(f"{report.integrated_lufs:.1f} LUFS")
            self.lbl_peak.setText(f"{report.true_peak_dbtp:.1f} dBTP")
            if report.is_quiet or report.needs_boost:
                self.lbl_status.setText("Quiet audio detected (Normalization recommended)")
            else:
                self.lbl_status.setText("Within standard broadcast target thresholds")

        self._update_gain_preview()

    def _update_gain_preview(self):
        if not self._current_report:
            self.lbl_gain_preview.setText("Awaiting probe analysis...")
            return

        target_lufs = self.spin_target_lufs.value()
        curr_lufs = self._current_report.integrated_lufs
        curr_tp = self._current_report.true_peak_dbtp
        lra = self._current_report.loudness_range_lu

        if curr_lufs >= (target_lufs - 2.0) and curr_tp <= -0.5:
            self.lbl_gain_preview.setText("0.0 dB (Bypass: audio is already within target thresholds)")
            return

        delta_db = min(target_lufs - curr_lufs, 24.0)
        if delta_db <= 0.0:
            self.lbl_gain_preview.setText("0.0 dB (Bypass: no gain boost required)")
            return

        tier = 2 if lra > 14.0 else 1
        tier_desc = "Tier 1: Linear Gain + True-Peak Limiter" if tier == 1 else "Tier 2: Dynamic Speech Leveler (High LRA)"
        self.lbl_gain_preview.setText(f"+{delta_db:.1f} dB ({tier_desc})")

    def apply_normalization(self):
        audio_file = getattr(self.main_win, "audio_file", None) if self.main_win else None
        if not audio_file or not Path(audio_file).is_file():
            QMessageBox.warning(self, "No Media File", "Please open a media file before applying normalization.")
            return

        self.prog_bar.show()
        self.btn_apply.setEnabled(False)
        self.btn_reanalyze.setEnabled(False)

        try:
            target_lufs = self.spin_target_lufs.value()
            max_tp = self.spin_max_tp.value()
            sidecar = normalize_audio_sidecar(
                audio_file,
                report=self._current_report,
                target_lufs=target_lufs,
                max_true_peak=max_tp,
            )

            # Probe the generated sidecar to verify its actual normalized LUFS
            sidecar_report = probe_media_loudness(
                sidecar,
                target_lufs=target_lufs,
            )

            if self.main_win and hasattr(self.main_win, "project_metadata"):
                meta = self.main_win.project_metadata
                if isinstance(meta, dict):
                    norm_info = meta.setdefault("audio_normalization", {})
                    if self._current_report:
                        norm_info["probed_integrated_lufs"] = round(self._current_report.integrated_lufs, 2)
                        norm_info["probed_lra_lu"] = round(self._current_report.loudness_range_lu, 2)
                        norm_info["probed_true_peak_dbtp"] = round(self._current_report.true_peak_dbtp, 2)
                        norm_info["is_quiet"] = self._current_report.is_quiet
                    delta_db = max(0.0, min(target_lufs - (self._current_report.integrated_lufs if self._current_report else -16.0), 24.0))
                    norm_info["target_lufs"] = round(target_lufs, 2)
                    norm_info["loudness_gain_db"] = round(delta_db, 2)
                    norm_info["source_media"] = str(Path(audio_file).resolve())
                    norm_info["normalized_sidecar"] = str(Path(sidecar).resolve())
                    norm_info["normalized_integrated_lufs"] = round(sidecar_report.integrated_lufs, 2)
                    norm_info["normalized_true_peak_dbtp"] = round(sidecar_report.true_peak_dbtp, 2)
                    norm_info["tier"] = 2 if (self._current_report and self._current_report.loudness_range_lu > 14.0) else 1
                    if hasattr(self.main_win, "mark_project_dirty"):
                        self.main_win.mark_project_dirty()

            if hasattr(self.main_win, "update_active_media_source"):
                self.main_win.update_active_media_source()
            elif hasattr(self.main_win, "load_waveform_async"):
                self.main_win.load_waveform_async(force_regenerate=True)

            if hasattr(self.main_win, "log_activity"):
                orig_lufs = self._current_report.integrated_lufs if self._current_report else -31.0
                self.main_win.log_activity(
                    f"[AUDIO NORMALIZATION] Applied manual normalization: {sidecar.name} (Source: {orig_lufs:.1f} LUFS ➔ Sidecar: {sidecar_report.integrated_lufs:.1f} LUFS)."
                )

            orig_lufs_str = f"{self._current_report.integrated_lufs:.1f} LUFS" if self._current_report else "Quiet"
            QMessageBox.information(
                self,
                "Normalization Complete",
                f"Audio normalization sidecar successfully generated and activated:\n\n{sidecar.name}\n\n"
                f"Original Source Level:  {orig_lufs_str}\n"
                f"Normalized Active Level: {sidecar_report.integrated_lufs:.1f} LUFS (Target Achieved)\n\n"
                f"ASR transcription and speaker detection will automatically utilize this boosted sidecar."
            )
            self._display_report(self._current_report or LoudnessReport(str(audio_file)))
        except Exception as exc:
            logger.error(f"Failed to apply normalization: {exc}", exc_info=True)
            QMessageBox.critical(self, "Normalization Error", f"Failed to normalize audio:\n\n{exc}")
        finally:
            self.prog_bar.hide()
            self.btn_apply.setEnabled(True)
            self.btn_reanalyze.setEnabled(True)

    def reset_to_original(self):
        audio_file = getattr(self.main_win, "audio_file", None) if self.main_win else None
        if not audio_file:
            return

        if self.main_win and hasattr(self.main_win, "project_metadata"):
            meta = self.main_win.project_metadata
            if isinstance(meta, dict) and "audio_normalization" in meta:
                del meta["audio_normalization"]
                if hasattr(self.main_win, "mark_project_dirty"):
                    self.main_win.mark_project_dirty()

        if hasattr(self.main_win, "update_active_media_source"):
            self.main_win.update_active_media_source()
            self.main_win.log_activity("[AUDIO NORMALIZATION] Reset audio normalization back to original media.")

        QMessageBox.information(
            self,
            "Reset Complete",
            "Audio normalization has been reset. All pipeline operations will use the original media file."
        )
        if self._current_report:
            self._display_report(self._current_report)

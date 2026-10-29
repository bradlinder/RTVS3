"""benchmark_dialog.py - PySide6 Graphical Benchmark Dialog & Workers.

Provides:
- create_benchmark_dialog: Factory function returning native PySide6 Benchmark Dialog
- BenchmarkWorker: Dedicated QThread running benchmark suite without GUI blocking
- SampleDownloadWorker: Background QThread downloading real 30-min sample broadcast audio
- Visual hardware rating tiers, score cards, and real-time processing estimate cards
- Zero-pill typography discipline and persistent window geometry restoration
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from benchmark_engine import BenchmarkEngine
from benchmark_models import (
    BenchmarkMetric,
    delete_sample_audio_files,
    download_sample_audio,
    find_available_sample_audio,
    format_duration_estimate,
)
from qt_compat import _ensure_pyside6_fallback

_ensure_pyside6_fallback()


def create_benchmark_dialog(parent=None):
    """Factory creating the native PySide6 Benchmark Dialog."""
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )

    class BenchmarkWorker(QThread):
        item_updated = Signal(object)
        finished = Signal()

        def __init__(self, engine: BenchmarkEngine):
            super().__init__()
            self.engine = engine
            self._is_stopped = False

        def stop(self):
            self._is_stopped = True

        def run(self):
            self.engine.on_update = lambda m: self.item_updated.emit(m)
            self.engine.run_all(stop_requested_fn=lambda: self._is_stopped)
            self.finished.emit()

    class SampleDownloadWorker(QThread):
        progress = Signal(int, str)
        finished = Signal(bool, str)

        def __init__(self):
            super().__init__()
            self._is_cancelled = False

        def cancel(self):
            self._is_cancelled = True

        def run(self):
            try:
                dest = download_sample_audio(
                    progress_callback=lambda pct, msg: self.progress.emit(pct, msg),
                    cancel_check=lambda: self._is_cancelled,
                )
                self.finished.emit(True, f"Sample saved: {dest.name}")
            except Exception as exc:
                self.finished.emit(False, str(exc))

    class BenchmarkDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("System Performance & Speed Benchmark")
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            self.setMinimumSize(640, 420)
            default_w, default_h = 780, 540
            screen = None
            try:
                from PySide6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen()
                if screen:
                    avail = screen.availableGeometry()
                    target_w = min(default_w, max(640, int(avail.width() * 0.75)))
                    target_h = min(default_h, max(420, int(avail.height() * 0.75)))
                    self.resize(target_w, target_h)
                else:
                    self.resize(default_w, default_h)
            except Exception:
                self.resize(default_w, default_h)

            try:
                from PySide6.QtCore import QSettings
                settings = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
                saved_w = settings.value("benchmark_dialog_width", type=int)
                saved_h = settings.value("benchmark_dialog_height", type=int)
                if saved_w and saved_h and saved_w >= 600 and saved_h >= 400:
                    if screen:
                        avail = screen.availableGeometry()
                        saved_w = min(saved_w, avail.width())
                        saved_h = min(saved_h, avail.height())
                    self.resize(saved_w, saved_h)
            except Exception:
                pass

            self.active_parent_media = None
            if parent:
                for attr in ("current_media_path", "audio_file", "media_path", "current_file"):
                    val = getattr(parent, attr, None)
                    if val and os.path.isfile(str(val)):
                        self.active_parent_media = str(val)
                        break

            self.custom_selected_path = self.active_parent_media
            self.engine = BenchmarkEngine(quick=False)
            self.worker_thread: Optional[BenchmarkWorker] = None
            self.download_worker: Optional[SampleDownloadWorker] = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(10)

            # Header & System Specs
            header_layout = QVBoxLayout()
            title_lbl = QLabel("System Performance & Speed Benchmark")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_lbl.setFont(title_font)
            header_layout.addWidget(title_lbl)

            hw = self.engine.hardware_profile
            gpu_str = (
                f"GPU: {hw['gpu_devices'][0]['name']}"
                if hw.get("gpu_devices")
                else "Hardware: CPU Execution Mode"
            )
            ram_str = f" | {hw['total_ram_gb']} GB RAM" if "total_ram_gb" in hw else ""
            subtitle_lbl = QLabel(
                f"Profiles throughput, Real-Time Factor (RTF), memory footprints, and pipeline speeds.\n"
                f"System: {hw['processor']} ({hw['cpu_count_logical']} logical cores{ram_str}) | {gpu_str}"
            )
            subtitle_lbl.setWordWrap(True)
            subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            header_layout.addWidget(subtitle_lbl)
            layout.addLayout(header_layout)

            # Top Banners Container
            banners_layout = QHBoxLayout()
            banners_layout.setSpacing(10)

            # Score Card Banner
            self.score_card = QFrame()
            self.score_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(30, 41, 59, 0.7);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            score_layout = QVBoxLayout(self.score_card)
            score_layout.setContentsMargins(10, 8, 10, 8)
            score_layout.setSpacing(4)

            self.score_lbl = QLabel("RTVS Hardware Score: Ready")
            self.score_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
            score_layout.addWidget(self.score_lbl)

            self.tier_lbl = QLabel("Run benchmark to evaluate hardware rating")
            self.tier_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: 500;")
            score_layout.addWidget(self.tier_lbl)

            banners_layout.addWidget(self.score_card, stretch=2)

            # Estimated Processing Times Banner
            self.est_card = QFrame()
            self.est_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.7);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            est_layout = QVBoxLayout(self.est_card)
            est_layout.setContentsMargins(10, 8, 10, 8)
            est_layout.setSpacing(4)

            est_header_row = QHBoxLayout()
            self.est_title_lbl = QLabel("Estimated 30-Min Audio Process Time:")
            self.est_title_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #f8fafc;")
            est_header_row.addWidget(self.est_title_lbl)
            est_header_row.addStretch()

            asr_lbl = QLabel("Engine:")
            asr_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
            est_header_row.addWidget(asr_lbl)

            self.asr_combo = QComboBox()
            self.asr_combo.addItems([
                "Parakeet TDT (FastConformer ONNX)",
                "Whisper INT8 (Encoder-Decoder)",
            ])
            self.asr_combo.setToolTip("Switch ASR engine model to recalculate projected turnaround times")
            self.asr_combo.currentIndexChanged.connect(self._update_estimates_display)
            est_header_row.addWidget(self.asr_combo)
            est_layout.addLayout(est_header_row)

            self.est_summary_lbl = QLabel("Transcription: -- | Diarization: -- | Story: -- | Total: --")
            self.est_summary_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            est_layout.addWidget(self.est_summary_lbl)

            banners_layout.addWidget(self.est_card, stretch=3)
            layout.addLayout(banners_layout)

            # Audio Source Selection & Management Card
            self.source_card = QFrame()
            self.source_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.5);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            source_card_layout = QVBoxLayout(self.source_card)
            source_card_layout.setContentsMargins(10, 8, 10, 8)
            source_card_layout.setSpacing(6)

            src_row1 = QHBoxLayout()
            src_lbl = QLabel("Audio Source:")
            src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #f8fafc;")
            src_row1.addWidget(src_lbl)

            self.source_combo = QComboBox()
            self.source_combo.addItems([
                "Synthetic RAM Stream (Zero Disk Footprint, Instant)",
                "Standard 30-Min Broadcast Sample (MP3 ~6.9 MB)",
                "Custom Audio File / Active Timeline Media...",
            ])
            self.source_combo.currentIndexChanged.connect(self._on_source_changed)
            src_row1.addWidget(self.source_combo, stretch=1)

            # Sample Action Buttons
            self.sample_action_btn = QPushButton("Download Sample (~6.9 MB)")
            self.sample_action_btn.clicked.connect(self._on_sample_action_clicked)
            src_row1.addWidget(self.sample_action_btn)

            self.delete_sample_btn = QPushButton("Delete Sample")
            self.delete_sample_btn.setToolTip("Delete local sample MP3 file to free up ~6.9 MB of disk space")
            self.delete_sample_btn.setStyleSheet("color: #f87171;")
            self.delete_sample_btn.clicked.connect(self._on_delete_sample_clicked)
            src_row1.addWidget(self.delete_sample_btn)

            self.browse_custom_btn = QPushButton("Browse...")
            self.browse_custom_btn.clicked.connect(self._on_browse_custom_clicked)
            src_row1.addWidget(self.browse_custom_btn)

            source_card_layout.addLayout(src_row1)

            # Source Details / Download Progress Row
            src_row2 = QHBoxLayout()
            self.source_status_lbl = QLabel("Ready")
            self.source_status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            src_row2.addWidget(self.source_status_lbl, stretch=1)

            self.download_progress_bar = QProgressBar()
            self.download_progress_bar.setRange(0, 100)
            self.download_progress_bar.setValue(0)
            self.download_progress_bar.setFixedWidth(180)
            self.download_progress_bar.setVisible(False)
            src_row2.addWidget(self.download_progress_bar)

            source_card_layout.addLayout(src_row2)
            layout.addWidget(self.source_card)

            # Progress Bar & Duration / Rigor Selector
            top_controls = QVBoxLayout()
            top_controls.setSpacing(4)

            dur_row = QHBoxLayout()
            dur_lbl = QLabel("Benchmark Rigor / Duration:")
            dur_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #f8fafc;")
            dur_row.addWidget(dur_lbl)

            self.duration_combo = QComboBox()
            self.duration_combo.addItems([
                "Quick Mode (1 Min Audio | ~3–5s Evaluation)",
                "Standard Benchmark (5 Min Audio | ~15–25s Run) [Recommended]",
                "Sustained Stress (10 Min Audio | ~45–90s Run)",
                "Full 30-Min Endurance (30 Min Audio | ~2–5m Run)",
            ])
            self.duration_combo.setCurrentIndex(1)
            self.duration_combo.setToolTip("Select workload scale and audio duration to balance speed vs thermal/boost clock evaluation")
            self.duration_combo.currentIndexChanged.connect(self._on_duration_changed)
            dur_row.addWidget(self.duration_combo, stretch=1)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.engine.metrics))
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%v / %m Tests Completed")
            self.progress_bar.setFixedWidth(240)
            dur_row.addWidget(self.progress_bar)

            top_controls.addLayout(dur_row)

            self.duration_desc_lbl = QLabel("")
            self.duration_desc_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; padding-left: 2px;")
            top_controls.addWidget(self.duration_desc_lbl)
            layout.addLayout(top_controls)

            # Metrics Tree
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Subsystem / Benchmark", "Status", "Duration", "Score", "Throughput / Details"])
            self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.tree.setAlternatingRowColors(True)
            layout.addWidget(self.tree)

            self._populate_tree()

            # Footer Controls
            btn_layout = QHBoxLayout()
            self.run_btn = QPushButton("Run Benchmark (5-Min Audio)")
            self.run_btn.setStyleSheet("font-weight: bold; padding: 6px 16px;")
            self.run_btn.clicked.connect(self._on_run_clicked)

            self.stop_btn = QPushButton("Cancel")
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self._on_stop_clicked)

            self.copy_btn = QPushButton("Copy Report to Clipboard")
            self.copy_btn.clicked.connect(self._on_copy_clicked)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.accept)

            btn_layout.addWidget(self.run_btn)
            btn_layout.addWidget(self.stop_btn)
            btn_layout.addWidget(self.copy_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(self.close_btn)
            layout.addLayout(btn_layout)

            sample_present = find_available_sample_audio() is not None
            if sample_present:
                self.source_combo.setCurrentIndex(1)
            else:
                self.source_combo.setCurrentIndex(0)
            self._update_source_ui()
            self._update_duration_desc()

        def _save_window_size(self):
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
                settings.setValue("benchmark_dialog_width", self.width())
                settings.setValue("benchmark_dialog_height", self.height())
            except Exception:
                pass

        def closeEvent(self, event):
            self._save_window_size()
            super().closeEvent(event)

        def accept(self):
            self._save_window_size()
            super().accept()

        def reject(self):
            self._save_window_size()
            super().reject()

        def _get_selected_duration_mode(self) -> str:
            if not hasattr(self, "duration_combo"):
                return "standard"
            idx = self.duration_combo.currentIndex()
            mode_keys = ["quick", "standard", "sustained", "full"]
            if 0 <= idx < len(mode_keys):
                return mode_keys[idx]
            return "standard"

        def _update_duration_desc(self):
            mode = self._get_selected_duration_mode()
            info = BenchmarkEngine.DURATION_MODES.get(mode, BenchmarkEngine.DURATION_MODES["standard"])
            if hasattr(self, "duration_desc_lbl"):
                self.duration_desc_lbl.setText(f"{info['name']}: {info['description']} (Est. duration: {info['estimate_runtime']})")
            dur_label = f"{int(info['audio_seconds'] // 60)}-Min Audio" if info['audio_seconds'] >= 60 else f"{int(info['audio_seconds'])}s Audio"
            if hasattr(self, "run_btn"):
                self.run_btn.setText(f"Run Benchmark ({dur_label})")

        def _on_duration_changed(self):
            self._update_duration_desc()

        def _update_source_ui(self):
            idx = self.source_combo.currentIndex()
            sample_path = find_available_sample_audio()

            if idx == 0:  # Synthetic
                self.sample_action_btn.setVisible(False)
                self.delete_sample_btn.setVisible(False)
                self.browse_custom_btn.setVisible(False)
                self.source_status_lbl.setText("Zero-disk synthetic speech fixture (instant RAM allocation).")
            elif idx == 1:  # Sample Audio
                self.browse_custom_btn.setVisible(False)
                if sample_path:
                    mb = sample_path.stat().st_size / (1024 * 1024)
                    self.sample_action_btn.setVisible(False)
                    self.delete_sample_btn.setVisible(True)
                    self.source_status_lbl.setText(f"Broadcast sample ready ({sample_path.name}, {mb:.1f} MB, ~30m). Tests FFmpeg decoding & real speech.")
                else:
                    self.sample_action_btn.setVisible(True)
                    self.sample_action_btn.setText("Download Sample (~6.9 MB)")
                    self.delete_sample_btn.setVisible(False)
                    self.source_status_lbl.setText("Sample not downloaded. Click 'Download Sample' to fetch from GitHub.")
            elif idx == 2:  # Custom Audio
                self.sample_action_btn.setVisible(False)
                self.delete_sample_btn.setVisible(False)
                self.browse_custom_btn.setVisible(True)
                if self.custom_selected_path and os.path.isfile(self.custom_selected_path):
                    p = Path(self.custom_selected_path)
                    mb = p.stat().st_size / (1024 * 1024)
                    self.source_status_lbl.setText(f"Selected Media: {p.name} ({mb:.1f} MB)")
                else:
                    self.source_status_lbl.setText("No custom file selected. Click 'Browse...' to select an audio or video file.")

        def _on_source_changed(self):
            self._update_source_ui()

        def _on_browse_custom_clicked(self):
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Audio or Video File for Benchmark",
                "",
                "All Supported Media Files (*.*);;Common Audio & Video (*.mp3 *.wav *.mp4 *.m4a *.aac *.flac *.ogg *.mkv *.avi *.mov *.webm *.aiff *.opus *.wmv *.ts);;All Files (*)",
            )
            if file_path:
                self.custom_selected_path = file_path
                self._update_source_ui()

        def _on_sample_action_clicked(self):
            if self.download_worker and self.download_worker.isRunning():
                return
            self.download_progress_bar.setVisible(True)
            self.download_progress_bar.setValue(0)
            self.sample_action_btn.setEnabled(False)
            self.source_status_lbl.setText("Initiating sample download from GitHub...")

            self.download_worker = SampleDownloadWorker()
            self.download_worker.progress.connect(self._on_download_progress)
            self.download_worker.finished.connect(self._on_download_finished)
            self.download_worker.start()

        def _on_download_progress(self, pct: int, msg: str):
            self.download_progress_bar.setValue(pct)
            self.source_status_lbl.setText(msg)

        def _on_download_finished(self, ok: bool, msg: str):
            self.download_progress_bar.setVisible(False)
            self.sample_action_btn.setEnabled(True)
            if ok:
                self._update_source_ui()
                QMessageBox.information(self, "Download Complete", "The benchmark broadcast sample audio file has been downloaded successfully.")
            else:
                self.source_status_lbl.setText(f"Download failed: {msg}")
                QMessageBox.warning(self, "Download Error", f"Could not download sample audio file:\n\n{msg}")

        def _on_delete_sample_clicked(self):
            res = QMessageBox.question(
                self,
                "Delete Sample Audio?",
                "Are you sure you want to delete the local broadcast sample audio file to free up ~6.9 MB of disk space?\n\nYou can re-download it anytime from the benchmark dialog.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res == QMessageBox.StandardButton.Yes:
                ok, freed, msg = delete_sample_audio_files()
                self._update_source_ui()
                if ok:
                    QMessageBox.information(self, "Sample Deleted", msg)
                else:
                    QMessageBox.warning(self, "Delete Result", msg)

        def _populate_tree(self):
            self.tree.clear()
            self.tree_items = {}
            for m in self.engine.metrics:
                item = QTreeWidgetItem([m.name, m.status, "", "", m.notes])
                self.tree.addTopLevelItem(item)
                self.tree_items[m.name] = item

        def _on_run_clicked(self):
            idx = self.source_combo.currentIndex()
            mode = "synthetic" if idx == 0 else ("sample" if idx == 1 else "custom")
            duration_mode = self._get_selected_duration_mode()

            self.engine = BenchmarkEngine(
                duration_mode=duration_mode,
                audio_source_mode=mode,
                custom_audio_path=self.custom_selected_path,
            )
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.duration_combo.setEnabled(False)
            self.source_combo.setEnabled(False)
            self.sample_action_btn.setEnabled(False)
            self.delete_sample_btn.setEnabled(False)
            self.browse_custom_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.score_lbl.setText("Running benchmark suite...")
            self.tier_lbl.setText("Evaluating subsystem throughput...")
            self.est_summary_lbl.setText("Calculating processing throughput...")
            self._populate_tree()

            self.worker_thread = BenchmarkWorker(self.engine)
            self.worker_thread.item_updated.connect(self._on_item_updated)
            self.worker_thread.finished.connect(self._on_benchmarks_finished)
            self.worker_thread.start()

        def _on_stop_clicked(self):
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop()
                self.stop_btn.setEnabled(False)

        def _on_item_updated(self, metric: BenchmarkMetric):
            item = self.tree_items.get(metric.name)
            if not item:
                return
            item.setText(1, metric.status)
            if metric.duration_seconds > 0:
                item.setText(2, f"{metric.duration_seconds:.2f}s")
            if metric.score_points > 0:
                item.setText(3, f"{metric.score_points:,} pts")
            item.setText(4, metric.notes)

            if metric.status == "COMPLETED":
                item.setForeground(1, QColor("#16a34a"))
            elif metric.status == "FAILED":
                item.setForeground(1, QColor("#dc2626"))
            elif metric.status == "RUNNING":
                item.setForeground(1, QColor("#2563eb"))
            elif metric.status == "SKIPPED":
                item.setForeground(1, QColor("#ca8a04"))

            completed_count = sum(1 for m in self.engine.metrics if m.status in ("COMPLETED", "FAILED", "SKIPPED"))
            self.progress_bar.setValue(completed_count)

        def _update_estimates_display(self):
            if not self.engine.processing_estimates:
                return
            est = self.engine.processing_estimates
            is_parakeet = (self.asr_combo.currentIndex() == 0)

            if is_parakeet:
                trans_sec = est.transcription_parakeet_seconds
                trans_rtf = est.transcription_parakeet_rtf
                total_sec = est.total_with_parakeet_seconds
                total_rtf = est.total_with_parakeet_rtf
                model_name = "Parakeet"
            else:
                trans_sec = est.transcription_whisper_seconds
                trans_rtf = est.transcription_whisper_rtf
                total_sec = est.total_with_whisper_seconds
                total_rtf = est.total_with_whisper_rtf
                model_name = "Whisper"

            trans_str = f"{format_duration_estimate(trans_sec)} ({trans_rtf:.1f}x)"
            diar_str = format_duration_estimate(est.diarization_seconds)
            story_str = format_duration_estimate(est.story_detection_seconds)
            total_str = format_duration_estimate(total_sec)
            trans_label = (
                f"Translate: {format_duration_estimate(est.translation_seconds)}"
                if est.translation_installed
                else "Translate: Off"
            )
            self.est_title_lbl.setText(
                f"Est. 30-Min Audio ({model_name}): {total_str} ({total_rtf:.1f}x RTF)"
            )
            self.est_summary_lbl.setText(
                f"{model_name}: {trans_str} | Diarize: {diar_str} | Stories: {story_str} | {trans_label}"
            )

        def _on_benchmarks_finished(self):
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.duration_combo.setEnabled(True)
            self.source_combo.setEnabled(True)
            self.sample_action_btn.setEnabled(True)
            self.delete_sample_btn.setEnabled(True)
            self.browse_custom_btn.setEnabled(True)

            completed = sum(1 for m in self.engine.metrics if m.status == "COMPLETED")
            total = len(self.engine.metrics)
            score = self.engine.composite_score
            tier = self.engine.hardware_tier
            self.score_lbl.setText(f"Features: {completed}/{total} Functional | Score: {score:,} pts")
            self.tier_lbl.setText(f"Rating Tier: {tier} ({completed}/{total} user-facing feature subsystems verified)")

            self._update_estimates_display()

        def _on_copy_clicked(self):
            completed = sum(1 for m in self.engine.metrics if m.status == "COMPLETED")
            total = len(self.engine.metrics)
            pct = (completed / total) * 100 if total else 0
            lines = [
                "Radio & TV Story Segmenter — System Feature & Performance Benchmark Report",
                "=" * 65,
                f"Features : {completed}/{total} Functional ({pct:.0f}% Verified)",
                f"Platform : {self.engine.hardware_profile['platform']}",
                f"CPU      : {self.engine.hardware_profile['processor']} ({self.engine.hardware_profile['cpu_count_logical']} cores)",
            ]
            if "total_ram_gb" in self.engine.hardware_profile:
                lines.append(f"RAM      : {self.engine.hardware_profile['total_ram_gb']} GB")
            dur_info = self.engine.DURATION_MODES.get(self.engine.duration_mode, self.engine.DURATION_MODES["standard"])
            lines.append(f"Rigor    : {dur_info['name']} ({dur_info['audio_seconds']}s audio window)")
            lines.append(f"Audio    : {self.engine.audio_source_description or 'Synthetic RAM Stream'}")
            lines.append("-" * 65)
            for m in self.engine.metrics:
                score_str = f" [{m.score_points:,} pts]" if m.score_points > 0 else ""
                lines.append(f"[{m.status}] {m.name} ({m.duration_seconds:.2f}s){score_str}: {m.notes}")
            lines.append("=" * 65)
            lines.append(f"RTVS HARDWARE SCORE: {self.engine.composite_score:,} pts  ({self.engine.hardware_tier})")
            if self.engine.score_breakdown:
                lines.append("-" * 65)
                lines.append("Subsystem Breakdown:")
                for cat, pts in self.engine.score_breakdown.items():
                    lines.append(f"  • {cat.ljust(22)} : {pts:,} pts")

            if self.engine.processing_estimates:
                est = self.engine.processing_estimates
                lines.append("-" * 65)
                lines.append("Estimated Processing Times (30-Minute Broadcast Audio):")
                lines.append(f"  • Story & Boundary Detection   : {est.details.get('story_detection', '')}")
                lines.append(f"  • AI Transcription (Parakeet)  : {est.details.get('transcription_parakeet', '')}")
                lines.append(f"  • AI Transcription (Whisper)   : {est.details.get('transcription_whisper', '')}")
                lines.append(f"  • Speaker Diarization          : {est.details.get('diarization', '')}")
                lines.append(f"  • Neural Translation           : {est.details.get('translation', '')}")
                lines.append("  " + "-" * 59)
                lines.append(f"  • Complete Pipeline (Parakeet) : {est.details.get('total_with_parakeet', '')}")
                lines.append(f"  • Complete Pipeline (Whisper)  : {est.details.get('total_with_whisper', '')}")

            lines.append("=" * 65)

            report_text = "\n".join(lines)
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(report_text)
                self.copy_btn.setText("Copied!")
                QApplication.processEvents()

    return BenchmarkDialog(parent=parent)

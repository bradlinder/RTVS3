"""Radio & TV Story Segmenter — Playback Preferences & Application Facade.

Aggregates theme preferences, playback transport controls, preferences dialog,
project state undo/redo, activity logging, and diagnostic lifecycle handlers.
Provides 100% backward-compatible facade re-exports for all components.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
import warnings
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QTime, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QInputDialog, QMessageBox,
    QPushButton, QVBoxLayout, QWidget, QComboBox, QDoubleSpinBox
)

from prs_shared import (
    INTERNAL_APP_ID, PROJECT_VERSION, APP_DISPLAY_NAME,
    get_app_data_dir, get_app_icon, get_github_repo,
    get_license_file_path, safe_replace
)
from theme_preferences import ThemePreferencesMixin
from playback_controller import PlaybackControllerMixin
from preferences_reset import RestoreSelectedSettingsDialog, PreferencesResetMixin
from preferences_dialog import PreferencesDialogMixin
from project_state_mixin import ProjectStateMixin

logger = logging.getLogger(__name__)

__all__ = [
    "PlaybackPreferencesMixin",
    "RestoreSelectedSettingsDialog",
    "ThemePreferencesMixin",
    "PlaybackControllerMixin",
    "PreferencesDialogMixin",
    "PreferencesResetMixin",
    "ProjectStateMixin",
]


class PlaybackPreferencesMixin(ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, ProjectStateMixin):
    """Aggregates all playback, preferences, styling, and application lifecycle mixins."""

    def _install_diagnostic_logging(self):
        """Install startup-safe diagnostics that never depend on the GUI widgets."""
        self._original_showwarning = warnings.showwarning
        self._original_excepthook = sys.excepthook
        self.log_dir = get_app_data_dir() / "logs"
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.log_dir = Path.cwd() / "logs"
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        self.crash_log_file = self.log_dir / f"prs_{datetime.now().strftime('%Y-%m-%d')}.log"

        def write_diag(kind, message):
            try:
                operation = getattr(self, "current_operation", None) or "idle"
                with self.crash_log_file.open("a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{kind}] {INTERNAL_APP_ID}_v{PROJECT_VERSION} operation={operation}\n")
                    f.write(str(message))
                    f.write("\n\n")
            except Exception:
                pass

        self._write_diag = write_diag
        try:
            self._faulthandler_file = self.crash_log_file.open("a", encoding="utf-8")
            import faulthandler
            faulthandler.enable(file=self._faulthandler_file, all_threads=True)
            self._faulthandler_enabled = True
        except Exception as exc:
            self._faulthandler_file = None
            self._faulthandler_enabled = False
            write_diag("WARNING", f"Could not enable faulthandler: {exc}")
        write_diag("SYSTEM", "Diagnostic logging initialized.")
        try:
            write_diag("SYSTEM", f"Python={sys.version.split()[0]} | executable={sys.executable}")
            try:
                from plugins.translation.worker import TranslationWorker
                write_diag("SYSTEM", f"Model root={TranslationWorker.model_root()}")
                for _f, _t in (("en", "es"), ("es", "en")):
                    write_diag("SYSTEM", f"Model {_f}->{_t} installed={TranslationWorker.model_is_installed(_f, _t)} path={TranslationWorker.model_dir(_f, _t)}")
            except Exception as _tw_err:
                write_diag("SYSTEM", f"TranslationWorker diagnostics unavailable: {_tw_err}")
        except Exception as exc:
            write_diag("WARNING", f"Startup model diagnostic failed: {exc}")

        def showwarning(message, category, filename, lineno, file=None, line=None):
            text = f"{category.__name__}: {message} ({Path(filename).name}:{lineno})"
            write_diag("WARNING", text)
            if getattr(self, "activity_list", None) is not None:
                try:
                    self.log_activity(f"[WARNING] {text}", mark_dirty=False)
                except Exception:
                    pass
            try:
                return self._original_showwarning(message, category, filename, lineno, file, line)
            except Exception:
                return None

        def excepthook(exc_type, exc_value, exc_tb):
            text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            write_diag("CRASH/EXCEPTION", text)
            try:
                crash_file = self.log_dir / f"crash_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with crash_file.open("w", encoding="utf-8") as cf:
                    cf.write(f"{APP_DISPLAY_NAME} v{PROJECT_VERSION} Crash Report\n")
                    cf.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    cf.write(f"Python: {sys.version}\n")
                    cf.write(f"Platform: {sys.platform}\n\n")
                    cf.write(text)
            except Exception:
                pass

            try:
                if hasattr(self, "project_data") and (getattr(self, "project_dirty", False) or getattr(self, "audio_file", None)):
                    data = self.project_data()
                    target_file = None
                    proj_file = getattr(self, "project_file", None)
                    if proj_file:
                        target_file = Path(proj_file).with_suffix(".crash_recovery.rtvs")
                    elif getattr(self, "audio_file", None):
                        audio_path = Path(self.audio_file)
                        target_file = audio_path.with_name(f"{audio_path.stem}.crash_recovery.rtvs")
                    else:
                        target_file = self.log_dir / f"emergency_crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.crash_recovery.rtvs"

                    if target_file:
                        from prs_shared import write_rtvs_project_file
                        write_rtvs_project_file(target_file, data)
                        write_diag("CRASH-RECOVERY", f"Emergency project snapshot preserved to {target_file}")
            except Exception as crash_save_exc:
                try:
                    write_diag("CRASH-RECOVERY-FAIL", str(crash_save_exc))
                except Exception:
                    pass

            if getattr(self, "activity_list", None) is not None:
                try:
                    self.log_activity(f"[ERROR] {exc_type.__name__}: {exc_value}", mark_dirty=False)
                except Exception:
                    pass
            try:
                self._original_excepthook(exc_type, exc_value, exc_tb)
            except Exception:
                pass

        def thread_excepthook(args):
            try:
                thread_name = getattr(args.thread, "name", "unknown")
                text = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
                write_diag("THREAD-CRASH", f"thread={thread_name}\n{text}")
                try:
                    crash_file = self.log_dir / f"crash_report_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    with crash_file.open("w", encoding="utf-8") as cf:
                        cf.write(f"{APP_DISPLAY_NAME} v{PROJECT_VERSION} Thread Crash Report\n")
                        cf.write(f"Thread: {thread_name}\n")
                        cf.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        cf.write(text)
                except Exception:
                    pass
            except Exception:
                pass

        warnings.showwarning = showwarning
        sys.excepthook = excepthook
        threading.excepthook = thread_excepthook

    def export_activity_log(self):
        """Export session activity log entries to a timestamped plain-text file."""
        if not hasattr(self, "activity_list") or self.activity_list.count() == 0:
            QMessageBox.information(self, "Activity Log", "No activity log entries to export.")
            return

        from PySide6.QtWidgets import QFileDialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"rtvs_activity_{timestamp}.txt"
        proj_dir = str(self.project_file.parent) if self.project_file else str(Path.home())
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Log",
            str(Path(proj_dir) / default_name),
            "Text Files (*.txt);;All Files (*.*)"
        )
        if not filename:
            return

        try:
            lines = []
            lines.append(f"{APP_DISPLAY_NAME} — Activity Log Export")
            lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Project: {self.project_file if self.project_file else 'Unsaved'}")
            lines.append(f"Media: {self.audio_file if self.audio_file else 'None'}")
            lines.append("-" * 60)
            for i in range(self.activity_list.count()):
                lines.append(self.activity_list.item(i).text())
            Path(filename).write_text("\n".join(lines), encoding="utf-8")
            self.log_activity(f"[EXPORT] Exported activity log to {Path(filename).name}")
            self.statusBar().showMessage(f"Activity log exported: {Path(filename).name}")
        except Exception as exc:
            self.log_activity(f"[ERROR] Activity log export failed: {exc}")
            QMessageBox.critical(self, "Activity Log Export Error", str(exc))

    def log_activity(self, action_text, mark_dirty=True):
        if not hasattr(self, "activity_list"):
            return
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtGui import QColor
        timestamp = datetime.now().strftime("%H:%M:%S")
        item_text = f"[{timestamp}] {action_text}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, len(getattr(self, "project_snapshots", [])))

        is_dark = str(self.settings_store.value("theme_mode", "dark")).lower() != "light"
        if "[ERROR]" in action_text or "CRITICAL" in action_text:
            item.setForeground(QColor("#ff6b6b" if is_dark else "#d32f2f"))
        elif "[WARNING]" in action_text:
            item.setForeground(QColor("#ffd166" if is_dark else "#f57c00"))
        elif "[PROJECT]" in action_text or "[IMPORT]" in action_text:
            item.setForeground(QColor("#06d6a0" if is_dark else "#2e7d32"))
        elif "[PROCESSING]" in action_text or "[AI]" in action_text:
            item.setForeground(QColor("#118ab2" if is_dark else "#0288d1"))
        elif "[SNAPSHOT]" in action_text:
            item.setForeground(QColor("#b5838d" if is_dark else "#7b1fa2"))
        elif "[SETTINGS]" in action_text:
            item.setForeground(QColor("#4cc9f0" if is_dark else "#0097a7"))
        elif "[SECURITY]" in action_text:
            item.setForeground(QColor("#ff9f1c" if is_dark else "#e65100"))
        elif "[EXPORT]" in action_text:
            item.setForeground(QColor("#a8dadc" if is_dark else "#00796b"))

        self.activity_list.addItem(item)
        if self.activity_list.count() > 300:
            self.activity_list.takeItem(0)
        self.activity_list.scrollToBottom()

        if hasattr(self, "_write_diag"):
            self._write_diag("ACTIVITY", action_text)

        if mark_dirty:
            self.mark_project_dirty()

    def handle_activity_click(self, item):
        snapshot_index = item.data(Qt.ItemDataRole.UserRole)
        if snapshot_index is not None and snapshot_index >= 0:
            self.restore_snapshot(snapshot_index)

    def restore_snapshot(self, index):
        if not hasattr(self, "project_snapshots") or index >= len(self.project_snapshots):
            return
        snapshot_data = self.project_snapshots[index]
        self.is_restoring_snapshot = True
        try:
            self.stories = [Story.from_dict(item) for item in snapshot_data.get("stories", [])]
            self.transcript = self._clone_transcript_state(snapshot_data.get("transcript"))
            self.diarization = copy.deepcopy(snapshot_data.get("diarization")) if snapshot_data.get("diarization") is not None else None
            self.speaker_names = dict(snapshot_data.get("speaker_names", {}))
            self.segment_speaker_overrides = dict(snapshot_data.get("segment_speaker_overrides", {}))
            self.translations = copy.deepcopy(snapshot_data.get("translations", {}))
            self.translation_display_mode = snapshot_data.get("translation_display_mode", "en")
            self.current_selected_story_indices = list(snapshot_data.get("selected_indices", []))

            if hasattr(self, "update_translation_language_selector"):
                self.update_translation_language_selector()
            if hasattr(self, "transcript_language_selector"):
                idx = self.transcript_language_selector.findData(self.translation_display_mode)
                if idx >= 0:
                    self.transcript_language_selector.blockSignals(True)
                    self.transcript_language_selector.setCurrentIndex(idx)
                    self.transcript_language_selector.blockSignals(False)

            if self.transcript:
                self.render_transcript()
                if hasattr(self, "comments_panel") and self.comments_panel:
                    self.comments_panel.set_comments(self.transcript.get("segments", []))
            else:
                self.transcript_view.clear()
                self.transcript_view.set_char_timestamp_map([])
                if hasattr(self, "comments_panel") and self.comments_panel:
                    self.comments_panel.set_comments([])
            self.refresh_story_list()
            self.apply_story_selection_indices(self.current_selected_story_indices, seek=False)
            self.project_dirty = True
            self.update_window_title()
            self.log_activity(f"[SNAPSHOT] Restored project snapshot #{index + 1}", mark_dirty=False)
        finally:
            self.is_restoring_snapshot = False

    def clear_activity_log(self):
        if hasattr(self, "activity_list"):
            self.activity_list.clear()
            self.log_activity("[ACTIVITY] Log cleared.", mark_dirty=False)

    def trigger_find_next(self):
        """Find Next shortcut (F3) handler: advances to next search match."""
        find_panel = getattr(self, "find_replace_panel", None)
        if find_panel and find_panel.isVisible():
            find_panel._find_next()
        elif hasattr(self, "open_find_replace"):
            self.open_find_replace()

    def open_diagnostic_log_folder(self):
        folder = getattr(self, "log_dir", get_app_data_dir() / "logs")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform.startswith("win"):
                try:
                    os.startfile(str(folder))
                except Exception:
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    subprocess.Popen(['explorer', str(folder)], creationflags=creationflags)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            QMessageBox.critical(self, "Diagnostics", f"Could not open the diagnostic log folder.\n\n{exc}")

    def show_about_dialog(self):
        about_text = (
            f"<h2>{APP_DISPLAY_NAME}</h2>"
            f"<p><b>Version {PROJECT_VERSION}</b></p>"
            f"<p>An automated broadcast audio segmentation, transcription, "
            f"and speaker detection platform built for radio production.</p>"
            f"<p style='font-size:12px; color:#555;'>Developed with the aid of AI tools, including Gemini, Claude, and ChatGPT.</p>"
            f"<hr>"
            f"<p><b>Open-Source Licensing &amp; Attribution:</b></p>"
            f"<p style='font-size:12px; color:#444; line-height:1.4;'>"
            f"  <b>Application Icon:</b> <i>'Electronic Media'</i> by Fatam Organa from "
            f"<a href='https://thenounproject.com/icon/electronic-media-5929933/'>Noun Project</a> "
            f"(licensed under CC BY 3.0).<br>"
            f"  <b>PySide6 / Qt 6:</b> The Qt Company (LGPLv3). Dynamically linked.<br>"
            f"  <b>FFmpeg:</b> FFmpeg developers (LGPLv2.1+ / GPLv2+). Invoked as separate binary.<br>"
            f"  <b>AI &amp; Speech:</b> OpenAI Whisper (MIT), faster-whisper &amp; CTranslate2 (MIT), "
            f"WeSpeaker &amp; ONNX Runtime (Apache 2.0 / MIT), PyTorch (BSD-3), Hugging Face Transformers &amp; Hub (Apache 2.0).<br>"
            f"</p>"
            f"<p style='font-size:11px; color:#666;'>"
            f"Click 'View Licenses' to review full license texts, compliance disclosures, and copyright notices."
            f"</p>"
        )
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"About {APP_DISPLAY_NAME}")
        msg_box.setText(about_text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        icon = get_app_icon()
        if not icon.isNull():
            msg_box.setIconPixmap(icon.pixmap(64, 64))

        check_updates_btn = msg_box.addButton("Check for Updates…", QMessageBox.ButtonRole.ActionRole)
        view_licenses_btn = msg_box.addButton("View Licenses", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        msg_box.exec()

        if msg_box.clickedButton() == check_updates_btn:
            self.check_for_updates(interactive=True)
        elif msg_box.clickedButton() == view_licenses_btn:
            self.show_licenses_dialog()

    def check_for_updates(self, interactive: bool = True):
        """Open the Check for Updates dialog to query GitHub releases and install updates."""
        try:
            from updater import CheckUpdateDialog
            dialog = CheckUpdateDialog(self, auto_start=True)
            if interactive:
                dialog.exec()
            else:
                dialog.show()
        except Exception as exc:
            if interactive:
                QMessageBox.warning(self, "Update Error", f"Unable to launch update checker:\n{exc}")

    def trigger_silent_update_check(self):
        """Perform a background update check without showing UI unless an update is found."""
        try:
            from updater import CheckUpdateWorker
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            auto_check = str(settings.value("auto_check_updates", "true")).lower() in {"1", "true", "yes"}
            if not auto_check:
                return

            repo = get_github_repo()
            worker = CheckUpdateWorker(repo, self)
            if hasattr(self, "_track_worker_thread"):
                self._track_worker_thread(worker)

            def on_update(release_info, asset_info, is_newer):
                if is_newer:
                    tag = release_info.get("tag_name", "")
                    self.log_activity(f"[UPDATE] New version {tag} available on GitHub.", mark_dirty=False)
                    if hasattr(self, "statusBar"):
                        self.statusBar().showMessage(f"★ Update Available: {tag} — Check About dialog to install.", 15000)

            worker.update_available.connect(on_update)
            worker.start()
            self._background_update_worker = worker
        except Exception:
            pass

    def apply_audio_output_device(self, device_name=None, volume=None):
        """Apply selected audio output device and volume to the active player."""
        if not hasattr(self, "audio_output") or not self.audio_output:
            return
        if device_name is None:
            device_name = str(self.settings_store.value("audio_output_device", "System Default") or "System Default")
        if volume is None:
            try:
                volume = float(self.settings_store.value("audio_output_volume", 100) or 100) / 100.0
            except Exception:
                volume = 1.0

        try:
            from PySide6.QtMultimedia import QMediaDevices
            if not device_name or device_name in ("System Default", "default"):
                default_dev = QMediaDevices.defaultAudioOutput()
                self.audio_output.setDevice(default_dev)
            else:
                for dev in QMediaDevices.audioOutputs():
                    if dev.description() == device_name:
                        self.audio_output.setDevice(dev)
                        break
            self.audio_output.setVolume(max(0.0, min(1.0, float(volume))))
        except Exception as e:
            logger.warning(f"Could not set audio output device '{device_name}': {e}")

    def show_licenses_dialog(self):
        from PySide6.QtWidgets import QTextEdit, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{APP_DISPLAY_NAME} — Open-Source Licenses & Attributions")
        dialog.resize(750, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)
        text_edit.setFontFamily("monospace")

        notices_path = get_license_file_path("NOTICES.txt")
        content = ""
        if notices_path and notices_path.is_file():
            try:
                content = notices_path.read_text(encoding="utf-8")
            except Exception as e:
                content = f"Error reading NOTICES.txt: {e}"
        else:
            content = "NOTICES.txt not found."

        text_edit.setPlainText(content)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(dialog)
        open_file_btn = button_box.addButton("Open File", QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        def _open_file():
            if notices_path and notices_path.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(notices_path)))

        open_file_btn.clicked.connect(_open_file)
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(button_box)
        dialog.exec()

    def on_expected_speakers_changed(self, value):
        """Kept as a public hook in case a future toolbar control adjusts the expected-speakers hint directly."""
        new_value = str(value or "auto")
        changed = new_value != getattr(self, "expected_speakers", "auto")
        self.expected_speakers = new_value
        if changed and getattr(self, "diarization", None) is not None:
            self.processing_status["diarization"] = False
            self.log_activity("[PROCESSING] Expected speakers changed; existing speaker detection is marked for reprocessing.", mark_dirty=False)
        self.mark_project_dirty()
        self.log_activity(f"[SETTINGS] Expected speakers set to '{new_value}'.")
        self.statusBar().showMessage(f"Expected speakers: {new_value}.")

    def on_diarization_sensitivity_changed(self, value):
        """Public hook for adjusting speaker separation sensitivity."""
        new_value = str(value or "normal")
        changed = new_value != getattr(self, "diarization_sensitivity", "normal")
        self.diarization_sensitivity = new_value
        if changed and getattr(self, "diarization", None) is not None:
            self.processing_status["diarization"] = False
            self.log_activity("[PROCESSING] Speaker separation sensitivity changed; existing speaker detection is marked for reprocessing.", mark_dirty=False)
        self.mark_project_dirty()
        self.log_activity(f"[SETTINGS] Speaker separation sensitivity set to '{new_value}'.")
        self.statusBar().showMessage(f"Speaker separation sensitivity: {new_value}.")

    def update_auto_save_timer(self):
        if getattr(self, "auto_save_minutes", 0) > 0:
            self.auto_save_timer.start(self.auto_save_minutes * 60 * 1000)
        else:
            self.auto_save_timer.stop()

    def prompt_set_whisper_model(self):
        if hasattr(self, "model_input"):
            self.model_input.setFocus()
            self.model_input.showPopup()

    def prompt_set_skip_seconds(self):
        val, accepted = QInputDialog.getInt(
            self,
            "Set Arrow Key Skip Length",
            "Enter skip duration in seconds for Left/Right arrow keys:",
            getattr(self, "skip_seconds", 5),
            1,
            300,
            1,
        )
        if accepted:
            self.skip_seconds = val
            self.timeline.set_skip_seconds(val)
            self.log_activity(f"[SETTINGS] Skip length set to {val}s.")
            self.statusBar().showMessage(f"Arrow key skip length set to {val} second(s).")

    def prompt_set_auto_detect_thresholds(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Story Detection Settings")
        dialog.setFixedWidth(380)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        mode_box = QComboBox()
        mode_box.addItem("Voice / Speech (Dialog Pauses)", "voice")
        mode_box.addItem("Music / Songs (Music Programs)", "music")
        curr_det_mode = str(getattr(self, "story_detection_mode", "voice") or "voice")
        idx = mode_box.findData(curr_det_mode)
        mode_box.setCurrentIndex(idx if idx >= 0 else 0)

        thresh_box = QDoubleSpinBox()
        thresh_box.setRange(0.5, 30.0)
        thresh_box.setSingleStep(0.5)
        thresh_box.setValue(getattr(self, "silence_threshold", 3.0))
        thresh_box.setSuffix(" sec")

        pad_box = QDoubleSpinBox()
        pad_box.setRange(0.0, 5.0)
        pad_box.setSingleStep(0.1)
        pad_box.setValue(getattr(self, "lead_in_padding", 0.5))
        pad_box.setSuffix(" sec")

        form.addRow("Detection Basis:", mode_box)
        form.addRow("Silence Gap Threshold:", thresh_box)
        form.addRow("Lead-In Padding:", pad_box)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        reset_defaults_btn = QPushButton("Restore Defaults")
        reset_defaults_btn.setToolTip("Reset speech detection thresholds to system defaults (Voice mode, 3.0s gap, 0.5s padding)")
        def _on_restore_detect_defaults():
            thresh_box.setValue(3.0)
            pad_box.setValue(0.5)
            idx_v = mode_box.findData("voice")
            if idx_v >= 0:
                mode_box.setCurrentIndex(idx_v)
        reset_defaults_btn.clicked.connect(_on_restore_detect_defaults)
        btn_box.addWidget(reset_defaults_btn)
        btn_box.addStretch()

        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.story_detection_mode = str(mode_box.currentData() or "voice")
            self.silence_threshold = thresh_box.value()
            self.lead_in_padding = pad_box.value()
            if hasattr(self, "settings_store") and self.settings_store is not None:
                self.settings_store.setValue("story_detection_mode", self.story_detection_mode)
                self.settings_store.setValue("silence_threshold", self.silence_threshold)
                self.settings_store.setValue("lead_in_padding", self.lead_in_padding)
            if hasattr(self, "update_story_segment_terminology"):
                self.update_story_segment_terminology()
            self.log_activity(f"[SETTINGS] Thresholds set: Mode={self.story_detection_mode.capitalize()}, Gap={self.silence_threshold}s, Padding={self.lead_in_padding}s.")
            self.statusBar().showMessage(f"Detection updated: Mode={self.story_detection_mode.capitalize()}, Gap={self.silence_threshold}s, Padding={self.lead_in_padding}s.")

    def prompt_set_auto_save(self):
        val, accepted = QInputDialog.getInt(
            self,
            "Auto-Save Interval",
            "Enter auto-save frequency in minutes (0 to disable):",
            getattr(self, "auto_save_minutes", 5),
            0,
            120,
            1,
        )
        if accepted:
            self.auto_save_minutes = val
            self.update_auto_save_timer()
            if val > 0:
                self.log_activity(f"[SETTINGS] Auto-save set to {val} min.")
                self.statusBar().showMessage(f"Auto-save configured for every {val} minute(s).")
            else:
                self.log_activity("[SETTINGS] Auto-save disabled.")
                self.statusBar().showMessage("Auto-save disabled.")

    def trigger_auto_save(self):
        if not (getattr(self, "audio_file", None) and getattr(self, "project_file", None) and getattr(self, "project_dirty", False)):
            return
        try:
            autosave = self.project_file.with_suffix(self.project_file.suffix + ".autosave")
            data = self.project_data()
            data["waveform_peaks"] = []
            data["_autosave"] = {"created_at": datetime.now().isoformat(timespec="seconds"), "source_project": str(self.project_file)}
            tmp = autosave.with_name(autosave.name + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            safe_replace(tmp, autosave)
            current_time = QTime.currentTime().toString("hh:mm A")
            self.log_activity(f"[AUTOSAVE] Recovery snapshot written ({current_time}).", mark_dirty=False)
            self.statusBar().showMessage(f"Recovery snapshot saved at {current_time}")
            if hasattr(self, "save_state_label"):
                self.save_state_label.setText(f"✓ Recovery snapshot {current_time}")
        except Exception as exc:
            self.log_activity(f"[AUTOSAVE] Recovery snapshot failed: {exc}", mark_dirty=False)

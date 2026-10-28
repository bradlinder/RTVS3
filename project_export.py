"""Radio & TV Story Segmenter — Unified Project & Media Export Facade.

Aggregates:
- Dialog UI and export format selection (export_dialogs.py)
- Media clipping and audio track rendering (export_media_clipper.py)
- Document, subtitles, and DAW interchange formatting (export_documents.py)
- Story & full episode batch export pipeline (export_story_pipeline.py)
- Project lifecycle and session archiving (project_lifecycle.py)

Provides 100% backward compatibility for all callers and plugins.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
import warnings
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
)

from core_utils import (
    safe_filename,
    safe_process_events,
    format_time,
    is_sentence_end,
    ffmpeg_path,
)
from project_serialization import read_rtvs_project_file
from prs_shared import *
from project_lifecycle import ProjectLifecycleMixin

# Re-exports from decomposed export submodules
from export_dialogs import (
    show_export_completion_dialog,
    ExportDialogsMixin,
    UnifiedExportDialog,
)
from export_media_clipper import (
    ExportMediaClipperMixin,
    render_audio_track,
    extract_audio_clip,
)
from export_documents import (
    ExportDocumentsMixin,
    TranscriptPdfWriter,
    create_story_docx,
    seconds_to_cue_time,
    generate_cue_sheet,
    generate_youtube_chapters,
    generate_srt_content,
    generate_vtt_content,
    generate_cue_content,
    generate_reaper_project,
    generate_samplitude_edl,
    generate_fcp7_xml,
    generate_fcpxml,
    generate_aaf_interchange,
    generate_hindenburg_session,
    generate_audacity_labels,
    generate_audition_xml,
    generate_daw_marker_csv,
    MIN_WORDS_PER_PARAGRAPH,
)
from export_story_pipeline import ExportStoryPipelineMixin


class ProjectExportMixin(
    ExportDialogsMixin,
    ExportMediaClipperMixin,
    ExportDocumentsMixin,
    ExportStoryPipelineMixin,
    ProjectLifecycleMixin,
):
    """Unified application export mixin composed of focused export sub-mixins."""

    # Extensions resolve_project_media() will accept as a project's media file.
    _VALID_MEDIA_EXTENSIONS = {
        ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".oga", ".opus", ".wma",
        ".aiff", ".aif", ".caf", ".amr", ".ac3", ".dts", ".ra", ".rm",
        ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".mpg", ".mpeg",
        ".3gp", ".3g2", ".ts", ".mts", ".m2ts", ".asf", ".flv",
    }

    def export_project_archive(self, destination_zip: Optional[str] = None) -> bool:
        """Export current project state, transcripts, and media into a self-contained portable .zip archive."""
        if not getattr(self, "audio_file", None) and not getattr(self, "transcript", None) and not getattr(self, "stories", None):
            QMessageBox.information(
                self,
                "Export Project Archive",
                "No project data or media is currently loaded to export."
            )
            return False

        audio_file = getattr(self, "audio_file", None)
        base_name = safe_filename(
            Path(audio_file).stem if audio_file else "project"
        )
        target_base_dir = Path(self.get_default_save_directory())

        if not destination_zip:
            default_path = str(target_base_dir / f"{base_name}_archive.zip")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Project Archive (.zip)",
                default_path,
                "Zip Archives (*.zip);;All Files (*.*)"
            )
            if not file_path:
                return False
            dest_zip = Path(file_path)
        else:
            dest_zip = Path(destination_zip)

        dest_zip.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = self.project_data()
            if audio_file and Path(audio_file).exists():
                media_path = Path(audio_file).resolve()
                data["audio_reference"] = f"Media/{media_path.name}"
                data["audio_file_name"] = media_path.name
                data["audio_duration"] = float(getattr(self, "audio_duration", 0.0) or 0.0)

            with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # 1. Project file inside zip
                proj_json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
                zf.writestr(f"{base_name}.rtvs", proj_json_bytes)

                # 2. Source Media file
                if audio_file and Path(audio_file).exists():
                    media_path = Path(audio_file).resolve()
                    zf.write(media_path, arcname=f"Media/{media_path.name}")

                # 3. Waveform Peak Cache if available
                timeline = getattr(self, "timeline", None)
                if audio_file and getattr(timeline, "waveform_peaks", None):
                    peaks = timeline.waveform_peaks
                    peak_bytes = json.dumps({"peaks": [float(p) for p in peaks]}).encode("utf-8")
                    zf.writestr(".cache/peaks.json", peak_bytes)

            if hasattr(self, "log_activity"):
                self.log_activity(f"[PROJECT] Exported self-contained project archive to {dest_zip}")
            show_export_completion_dialog(
                self,
                title="Project Archive Exported",
                message=f"Successfully exported self-contained project archive:\n\n{dest_zip.name}",
                export_path=str(dest_zip)
            )
            return True
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] Failed to export project archive: {exc}")
            QMessageBox.critical(
                self,
                "Archive Export Failed",
                f"Could not export project archive:\n{exc}"
            )
            return False

    def ensure_project_for_processing_pipeline(self) -> bool:
        """Ensures a project file is established on disk before running multi-stage
        automated pipelines so progress can be safely saved between stages.
        """
        if getattr(self, "project_file", None):
            return True

        if getattr(self, "batch_active", False):
            return bool(self.save_project_as())

        if getattr(self, "audio_file", None) or getattr(self, "transcript", None):
            reply = QMessageBox.question(
                self,
                "Save Project",
                "Multi-stage automated processing saves progress to your project file after each stage.\n\n"
                "Would you like to save this project now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                return bool(self.save_project_as())
            return False

        return False

    def find_adjacent_project(self, media_path: Path) -> Optional[Path]:
        """Looks for adjacent .rtvs or legacy .json project files referencing media_path."""
        candidates = [
            media_path.parent / f"{media_path.stem}.rtvs",
            media_path.parent / f"{media_path.stem}.json",
            media_path.parent / media_path.stem / f"{media_path.stem}.rtvs",
            media_path.parent / media_path.stem / f"{media_path.stem}.json",
        ]
        for candidate in candidates:
            if not candidate.exists() or not candidate.is_file():
                continue
            try:
                data = read_rtvs_project_file(candidate)
                ref = data.get("audio_file")
                if not ref:
                    continue
                ref_path = Path(ref)
                if not ref_path.is_absolute():
                    ref_path = candidate.parent / ref_path
                if ref_path.resolve() == media_path.resolve():
                    return candidate.resolve()
            except Exception:
                continue
        return None

    def resolve_project_media(
        self,
        project_file: Path,
        audio_reference: Optional[str],
        audio_file_abs: Optional[str] = None,
    ) -> Optional[Path]:
        """Resolves portable or absolute project media reference with security extension validation."""
        def _is_valid_media_candidate(candidate: Path) -> bool:
            return candidate.exists() and candidate.is_file() and candidate.suffix.lower() in self._VALID_MEDIA_EXTENSIONS

        # 1. Check remembered absolute path if available and exists on disk
        if audio_file_abs:
            abs_candidate = Path(audio_file_abs).expanduser().resolve()
            if _is_valid_media_candidate(abs_candidate):
                return abs_candidate

        if not audio_reference:
            return None

        ref_path = Path(audio_reference)

        # 2. Check audio_reference if already absolute and exists
        if ref_path.is_absolute():
            cand = ref_path.resolve()
            if _is_valid_media_candidate(cand):
                return cand

        proj_dir = project_file.parent

        # 3. Check relative to project_file.parent
        rel_candidate = (proj_dir / ref_path).resolve()
        if _is_valid_media_candidate(rel_candidate):
            return rel_candidate

        # 4. Check inside Media/ subfolder in project dir
        media_candidate = (proj_dir / "Media" / ref_path.name).resolve()
        if _is_valid_media_candidate(media_candidate):
            return media_candidate

        # 5. Check direct basename in project directory
        basename_candidate = (proj_dir / ref_path.name).resolve()
        if _is_valid_media_candidate(basename_candidate):
            return basename_candidate

        # 6. Check in default projects directory
        default_dir = getattr(self, "default_project_directory", "")
        if default_dir:
            cand = (Path(default_dir) / ref_path.name).resolve()
            if _is_valid_media_candidate(cand):
                return cand

        # 7. Check in last media directory
        last_media = getattr(self, "last_media_directory", "")
        if last_media:
            cand = (Path(last_media) / ref_path.name).resolve()
            if _is_valid_media_candidate(cand):
                return cand

        return None

    def closeEvent(self, event):
        """MainWindow close event handling shutdown, worker cancellation, and QSettings sync."""
        self._is_closing = True
        if hasattr(self, "log_activity"):
            self.log_activity("[SYSTEM] Application shutdown requested.")
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage("Shutting down...")

        model_thread = getattr(self, "_model_install_thread", None)
        if model_thread is not None and model_thread.isRunning():
            if hasattr(self, "log_activity"):
                self.log_activity("[WARNING] A model installation is still running; close was canceled to prevent an interrupted download.", mark_dirty=False)
            QMessageBox.warning(
                self,
                "Model Installation Still Running",
                "A model or AI component is still being installed. Please wait for the installation to finish before closing the application."
            )
            event.ignore()
            return

        for attr in ("_active_export_dialog", "_active_metadata_dialog", "_active_speaker_manager_dialog", "_active_preferences_dialog"):
            dlg = getattr(self, attr, None)
            if dlg is not None and dlg.isVisible():
                try:
                    if hasattr(dlg, "_persist_plugin_draft_states"):
                        dlg._persist_plugin_draft_states()
                    if hasattr(dlg, "save_all_to_project"):
                        dlg.save_all_to_project()
                    if hasattr(dlg, "save_preferences"):
                        dlg.save_preferences()
                except Exception:
                    pass

        if getattr(self, "project_dirty", False) and not getattr(self, "batch_active", False):
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes in the current project. Would you like to save before exiting?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.StandardButton.Save:
                if not self.save_project():
                    event.ignore()
                    return

        try:
            if hasattr(self, "cleanup_transcription_process"):
                self.cleanup_transcription_process()
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Transcription cleanup failed: {exc}")

        try:
            if hasattr(self, "stop_all_processing") and not self.stop_all_processing(timeout_ms=10000):
                if hasattr(self, "log_activity"):
                    self.log_activity("[WARNING] One or more processing workers are still shutting down. Close was canceled to avoid destroying a running QThread.", mark_dirty=False)
                QMessageBox.warning(
                    self,
                    "Processing Still Running",
                    "A local processing task is still shutting down. The application was not closed to prevent data loss or a thread crash.\n\nPlease wait a few seconds and try closing again."
                )
                event.ignore()
                return
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Processing cleanup failed: {exc}", mark_dirty=False)
            event.ignore()
            return

        try:
            player = getattr(self, "player", None)
            if player:
                player.stop()
                player.setSource(QUrl())
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Media player cleanup failed: {exc}")

        # Waveform worker thread shutdown
        try:
            if hasattr(self, "stop_waveform_worker") and not self.stop_waveform_worker(timeout_ms=10000):
                if hasattr(self, "log_activity"):
                    self.log_activity("[WARNING] Waveform worker is still shutting down. Close was canceled to avoid destroying a running QThread.", mark_dirty=False)
                QMessageBox.warning(
                    self,
                    "Waveform Still Running",
                    "The waveform worker is still shutting down. The application was not closed to prevent a thread crash.\n\nPlease wait a few seconds and try closing again."
                )
                event.ignore()
                return
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Waveform cleanup encountered an issue: {exc}", mark_dirty=False)

        if hasattr(self, "_close_floating_dialogs"):
            self._close_floating_dialogs(persist_drafts=False)

        try:
            for thread in list(getattr(self, "translation_status_threads", [])):
                if thread.isRunning():
                    thread.quit()
                    thread.wait(5000)
            if hasattr(self, "translation_status_threads"):
                self.translation_status_threads.clear()
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Translation status cleanup failed: {exc}", mark_dirty=False)

        try:
            if hasattr(self, "stop_video_thumbnail_worker") and not self.stop_video_thumbnail_worker():
                if hasattr(self, "log_activity"):
                    self.log_activity("[WARNING] Video thumbnail worker is still stopping. Close was canceled to avoid a QThread lifetime crash.", mark_dirty=False)
                try:
                    QMessageBox.warning(
                        self,
                        "Video Thumbnails Generating",
                        "Video thumbnail generation is still finishing in the background.\n\n"
                        "Please wait a few seconds and try closing again to ensure clean thread termination."
                    )
                except Exception:
                    pass
                event.ignore()
                return
        except Exception:
            pass

        try:
            if hasattr(self, "auto_save_timer"):
                self.auto_save_timer.stop()
            if hasattr(self, "scrub_timer"):
                self.scrub_timer.stop()
        except Exception:
            pass

        checkpoint_thread = getattr(self, "translation_checkpoint_thread", None)
        if checkpoint_thread is not None and checkpoint_thread.is_alive():
            checkpoint_thread.join(timeout=5.0)

        for save_thread in list(getattr(self, "translation_save_threads", [])):
            if save_thread.is_alive():
                save_thread.join(timeout=5.0)

        try:
            if hasattr(self, "_original_showwarning"):
                warnings.showwarning = self._original_showwarning
            if hasattr(self, "_original_excepthook"):
                sys.excepthook = self._original_excepthook
        except Exception:
            pass

        try:
            terminate_all_registered_processes()
        except Exception:
            pass

        try:
            cleanup_old_thumbnail_cache(24)
        except Exception:
            pass

        try:
            settings_store = getattr(self, "settings_store", None)
            if settings_store is not None:
                settings_store.sync()
        except Exception as exc:
            if hasattr(self, "log_activity"):
                self.log_activity(f"[WARNING] Settings sync failed: {exc}", mark_dirty=False)

        if hasattr(self, "ipc_server") and self.ipc_server:
            try:
                self.ipc_server.close()
                QLocalServer.removeServer("RadioTVStorySegmenter_IPC_Server")
            except Exception:
                pass

        if hasattr(self, "log_activity"):
            self.log_activity("[SYSTEM] Application shutdown cleanup complete.")
        event.accept()

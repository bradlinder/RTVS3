"""Radio & TV Story Segmenter — Project Lifecycle & Persistence Management.

Encapsulates project file serialization, session state restoration, bundling,
autosave, and project closing/loading logic.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QDir, QTime, QUrl, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from prs_shared import (
    PROJECT_VERSION,
    cleanup_old_thumbnail_cache,
    read_rtvs_project_file,
    safe_filename,
    write_rtvs_project_file,
    write_waveform_peak_cache,
)
from transcript_story import Story


class ProjectLifecycleMixin:
    """Provides project lifecycle and persistence methods for MainWindow."""

    def close_project(self, prompt=True):
        if prompt and getattr(self, "project_dirty", False):
            answer = QMessageBox.question(
                self,
                "Close Project",
                "Close current project? Unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False

        try:
            if hasattr(self, "stop_video_thumbnail_worker") and not self.stop_video_thumbnail_worker():
                QMessageBox.warning(
                    self,
                    "Thumbnail Worker Still Running",
                    "Video thumbnails are still being generated. Please wait a few seconds and close again.",
                )
                return False
        except Exception:
            pass

        if hasattr(self, "stop_all_processing") and not self.stop_all_processing(timeout_ms=5000):
            QMessageBox.warning(
                self,
                "Close Project",
                "A processing worker could not be stopped safely. The project was not closed.",
            )
            return False

        self.media_generation = getattr(self, "media_generation", 0) + 1
        self.story_job_token = getattr(self, "story_job_token", 0) + 1

        if getattr(self, "player", None):
            self.player.stop()
            self.player.setSource(QUrl())

        self.audio_file = None
        self.project_file = None
        self.transcript = None
        self.diarization = None
        self.speaker_names = {}
        self.segment_speaker_overrides = {}
        self.stories = []
        self.current_selected_story_indices = []
        self.duration = 0
        self.current_position = 0

        if hasattr(self, "undo_stack") and self.undo_stack:
            self.undo_stack.clear()
        if hasattr(self, "activity_snapshots") and self.activity_snapshots:
            self.activity_snapshots.clear()

        if hasattr(self, "set_tools_actions_enabled"):
            self.set_tools_actions_enabled(False)
        if hasattr(self, "save_action"):
            self.save_action.setEnabled(False)
        if hasattr(self, "save_as_action"):
            self.save_as_action.setEnabled(False)

        if hasattr(self, "play_button"):
            self.play_button.setText("▶ Play")
        if hasattr(self, "time_label"):
            self.time_label.setText("00:00.000 / 00:00.000")
        if hasattr(self, "speaker_status"):
            self.speaker_status.setText("Speaker detection has not been run.")

        if hasattr(self, "transcript_view"):
            self.transcript_view.clear()
            self.transcript_view.set_char_timestamp_map([])
        if hasattr(self, "story_list"):
            self.story_list.clear()
        if hasattr(self, "activity_list"):
            self.activity_list.clear()

        if hasattr(self, "start_input"):
            self.start_input.clear()
        if hasattr(self, "end_input"):
            self.end_input.clear()
        if hasattr(self, "title_input"):
            self.title_input.clear()
        if hasattr(self, "story_boundary_container"):
            self.story_boundary_container.setVisible(False)

        if hasattr(self, "timeline") and self.timeline:
            self.timeline.set_duration(1)
            self.timeline.set_position(0)
            self.timeline.set_stories([])
            self.timeline.set_waveform_peaks([])
            self.timeline.set_zoom(1.0)
            self.timeline.scroll_offset = 0.0
            self.timeline.set_audio_filename(None)
            if hasattr(self.timeline, "set_video_thumbnails"):
                self.timeline.set_video_thumbnails([])
        self.video_thumbnail_dir = None

        if hasattr(self, "update_window_title"):
            self.update_window_title()
        try:
            cleanup_old_thumbnail_cache(24)
        except Exception:
            pass
        if hasattr(self, "log_activity"):
            self.log_activity("[FILE] Project closed.", mark_dirty=False)
        self.statusBar().showMessage("Project closed.")
        return True

    def new_project(self):
        if self.close_project(prompt=True):
            self.open_audio()

    def project_audio_reference(self):
        if not self.audio_file:
            return None
        try:
            if self.project_file:
                return os.path.relpath(self.audio_file, self.project_file.parent)
        except ValueError:
            pass
        return str(self.audio_file)

    def project_data(self) -> Dict[str, Any]:
        return {
            "format": "Radio & TV Story Segmenter Project",
            "version": PROJECT_VERSION,
            "audio_file": self.project_audio_reference(),
            "audio_file_abs": str(Path(self.audio_file).resolve()) if self.audio_file else None,
            "duration": self.duration,
            "transcript": self.transcript,
            "transcript_notes": getattr(self, "transcript_notes", ""),
            "diarization": self.diarization,
            "speaker_names": self.speaker_names,
            "segment_speaker_overrides": self.segment_speaker_overrides,
            "translations": getattr(self, "translations", {}),
            "translation_display_mode": getattr(self, "translation_display_mode", "off"),
            "stories": [story.to_dict() for story in getattr(self, "stories", [])],
            "plugins_data": getattr(self, "plugins_project_data", {}),
            "settings": {
                "auto_save_minutes": getattr(self, "auto_save_minutes", 5),
                "skip_seconds": getattr(self, "skip_seconds", 5),
                "whisper_model": getattr(self, "whisper_model", "small"),
                "translation_model_variant": getattr(self, "translation_model_variant", "tiny"),
                "silence_threshold": getattr(self, "silence_threshold", 3.0),
                "lead_in_padding": getattr(self, "lead_in_padding", 0.5),
                "expected_speakers": getattr(self, "expected_speakers", "auto"),
                "show_speaker_labels": getattr(self, "show_speaker_labels", True),
                "show_timestamps": getattr(self, "show_timestamps", True),
                "language": getattr(self, "language", "en"),
            },
            "processing_status": dict(getattr(self, "processing_status", {})),
            "session": {
                "position": getattr(self, "current_position", 0),
                "timeline_zoom": getattr(self.timeline, "zoom_level", 1.0) if hasattr(self, "timeline") else 1.0,
                "timeline_scroll_offset": getattr(self.timeline, "scroll_offset", 0.0) if hasattr(self, "timeline") else 0.0,
                "selected_story_indices": list(getattr(self, "current_selected_story_indices", [])),
                "video_preview_visible": bool(
                    getattr(self, "video_preview_dialog", None) and self.video_preview_dialog.isVisible()
                ),
            },
        }

    def _write_project_file(self, file_path: str):
        """Writes project state dictionary directly to disk."""
        destination = Path(file_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.project_file = destination

        media_mode = str(self.settings_store.value("media_ingest_mode", "reference")).strip().lower()
        copy_media = (
            str(self.settings_store.value("copy_media_to_project_folder", "false")).lower() in {"1", "true", "yes"}
            or media_mode == "copy"
        )

        if media_mode == "ask" and self.audio_file and Path(self.audio_file).exists():
            src_media = Path(self.audio_file).resolve()
            if src_media.parent != destination.parent and src_media.parent != (destination.parent / "Media"):
                res = QMessageBox.question(
                    self,
                    "Copy Media to Project Folder?",
                    f"Would you like to copy the media file ('{src_media.name}') into the project bundle folder for portability?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes,
                )
                if res == QMessageBox.StandardButton.Cancel:
                    return False
                copy_media = (res == QMessageBox.StandardButton.Yes)

        if copy_media and self.audio_file and Path(self.audio_file).exists():
            src_media = Path(self.audio_file).resolve()
            media_subfolder = destination.parent / "Media"
            if media_subfolder.is_dir() or str(self.settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}:
                media_subfolder.mkdir(parents=True, exist_ok=True)
                target_media = media_subfolder / src_media.name
            else:
                target_media = destination.parent / src_media.name

            if target_media.resolve() != src_media:
                try:
                    shutil.copy2(src_media, target_media)
                    self.audio_file = target_media
                    if hasattr(self, "log_activity"):
                        self.log_activity(f"[PROJECT] Copied media file to project folder: {target_media.name}", mark_dirty=False)
                except Exception as exc:
                    if hasattr(self, "log_activity"):
                        self.log_activity(f"[WARNING] Could not copy media to project folder: {exc}", mark_dirty=False)

        if self.audio_file and getattr(self, "timeline", None) and getattr(self.timeline, "waveform_peaks", None):
            try:
                write_waveform_peak_cache(self.audio_file, self.timeline.waveform_peaks, project_file=destination)
            except Exception:
                pass

        data = self.project_data()
        errors = self.validate_project_data(data)
        if errors:
            raise ValueError("Validation failed: " + "; ".join(errors))

        write_rtvs_project_file(destination, data)
        self.project_dirty = False
        self._remember_saved_project(str(destination))
        if hasattr(self, "update_window_title"):
            self.update_window_title()

    def prepare_export_directories(self, target_base_dir=None, default_name=None, prompt_user=True):
        """Resolves project export subfolders (Transcripts, Media)."""
        create_bundle = str(self.settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}

        if target_base_dir is None and self.project_file:
            active_parent = self.project_file.parent
            has_transcripts = (active_parent / "Transcripts").is_dir()
            has_media = (active_parent / "Media").is_dir()

            if has_transcripts or has_media or active_parent.name == self.project_file.stem:
                transcripts_dir = active_parent / "Transcripts"
                media_dir = active_parent / "Media"
                transcripts_dir.mkdir(parents=True, exist_ok=True)
                media_dir.mkdir(parents=True, exist_ok=True)
                return active_parent, transcripts_dir, media_dir, self.project_file.stem

        if target_base_dir is None:
            target_base_dir = self.get_default_save_directory()

        fallback_name = safe_filename(
            default_name 
            or (self.project_file.stem if self.project_file else None)
            or (self.audio_file.stem if self.audio_file else "export")
        )

        folder_name = fallback_name
        base_path = Path(target_base_dir)

        if (base_path / "Transcripts").is_dir() or (base_path / "Media").is_dir() or base_path.name == fallback_name:
            project_dir = base_path
            transcripts_dir = project_dir / "Transcripts"
            media_dir = project_dir / "Media"
            transcripts_dir.mkdir(parents=True, exist_ok=True)
            media_dir.mkdir(parents=True, exist_ok=True)
            return project_dir, transcripts_dir, media_dir, base_path.name

        if prompt_user and create_bundle:
            dialog_name, ok = QInputDialog.getText(
                self,
                "Project Folder Name",
                "Enter folder name for project and export subfolders:",
                QLineEdit.EchoMode.Normal,
                fallback_name,
            )
            if not ok:
                return None, None, None, None
            folder_name = safe_filename(dialog_name.strip()) or fallback_name

        if create_bundle:
            project_dir = base_path / folder_name
            transcripts_dir = project_dir / "Transcripts"
            media_dir = project_dir / "Media"
        else:
            project_dir = base_path
            transcripts_dir = base_path
            media_dir = base_path

        project_dir.mkdir(parents=True, exist_ok=True)
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        media_dir.mkdir(parents=True, exist_ok=True)

        return project_dir, transcripts_dir, media_dir, folder_name

    def get_default_save_directory(self) -> str:
        """Returns target base directory based on preferences and loaded media."""
        save_with_media = (
            str(self.settings_store.value("save_project_with_media", "false")).lower() in {"1", "true", "yes"}
        )
        if save_with_media and self.audio_file:
            media_path = Path(self.audio_file)
            if media_path.exists():
                return str(media_path.parent)

        if getattr(self, "default_project_directory", ""):
            return str(self.default_project_directory)

        return str(Path.home())

    def validate_project_data(self, data: Dict[str, Any]) -> List[str]:
        """Return a list of structural project-data problems before saving."""
        errors = []
        if data.get("format") != "Radio & TV Story Segmenter Project":
            errors.append("Invalid project format.")
        duration = data.get("duration", 0)
        try:
            if float(duration) < 0:
                errors.append("Media duration cannot be negative.")
        except (TypeError, ValueError):
            errors.append("Media duration is not numeric.")

        transcript = data.get("transcript")
        if transcript is not None:
            if isinstance(transcript, list):
                transcript = {"segments": transcript}
                data["transcript"] = transcript
                if hasattr(self, "transcript"):
                    self.transcript = transcript
            elif not isinstance(transcript, dict):
                transcript = {"segments": []}
                data["transcript"] = transcript
                if hasattr(self, "transcript"):
                    self.transcript = transcript

            segments = transcript.get("segments")
            if not isinstance(segments, list):
                transcript["segments"] = []
                data["transcript"] = transcript
                if hasattr(self, "transcript"):
                    self.transcript = transcript
                segments = []

            if not isinstance(segments, list):
                errors.append("Transcript segments are missing or invalid.")
            else:
                for i, seg in enumerate(segments):
                    if not isinstance(seg, dict):
                        errors.append(f"Transcript segment {i + 1} is invalid.")
                        continue
                    try:
                        if float(seg.get("start", 0)) > float(seg.get("end", 0)):
                            errors.append(f"Transcript segment {i + 1} has an invalid time range.")
                    except (TypeError, ValueError):
                        errors.append(f"Transcript segment {i + 1} has invalid timestamps.")

        stories = data.get("stories", [])
        if not isinstance(stories, list):
            errors.append("Stories data is not a list.")
        else:
            for i, story in enumerate(stories):
                try:
                    start = float(story.get("start", 0))
                    end = float(story.get("end", 0))
                    if start < 0 or end < start:
                        errors.append(f"Story {i + 1} has an invalid time range.")
                except (AttributeError, TypeError, ValueError):
                    errors.append(f"Story {i + 1} is invalid.")
        return errors

    def save_project_as(self) -> bool:
        if not self.audio_file and not self.transcript:
            return False

        base_name = safe_filename(
            Path(self.audio_file).stem if self.audio_file else "project"
        )
        chosen_folder, transcripts_dir, media_dir, folder_name = self.prepare_export_directories(default_name=base_name, prompt_user=True)
        if not chosen_folder:
            return False

        filename = str(chosen_folder / f"{folder_name}.rtvs")

        self.project_file = Path(filename).expanduser().resolve()
        self.project_file.parent.mkdir(parents=True, exist_ok=True)
        self.save_project(force=True)
        return True

    def save_project(self, force=True):
        if not self.audio_file:
            return False
        if not self.project_file:
            return self.save_project_as()
        if not force and not getattr(self, "project_dirty", False):
            return True
        if getattr(self, "save_in_progress", False):
            return False

        self.save_in_progress = True
        temp_file = self.project_file.with_name(self.project_file.name + ".tmp")
        backup_file = self.project_file.with_name(self.project_file.name + ".backup")
        try:
            self.project_file.parent.mkdir(parents=True, exist_ok=True)

            copy_media = str(self.settings_store.value("copy_media_to_project_folder", "false")).lower() in {"1", "true", "yes"}
            if copy_media and self.audio_file and Path(self.audio_file).exists():
                src_media = Path(self.audio_file).resolve()
                media_subfolder = self.project_file.parent / "Media"
                if media_subfolder.is_dir() or str(self.settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}:
                    media_subfolder.mkdir(parents=True, exist_ok=True)
                    target_media = media_subfolder / src_media.name
                else:
                    target_media = self.project_file.parent / src_media.name

                if target_media.resolve() != src_media:
                    try:
                        shutil.copy2(src_media, target_media)
                        self.audio_file = target_media
                        if hasattr(self, "log_activity"):
                            self.log_activity(f"[PROJECT] Copied media file to project folder: {target_media.name}", mark_dirty=False)
                    except Exception as exc:
                        if hasattr(self, "log_activity"):
                            self.log_activity(f"[WARNING] Could not copy media to project folder: {exc}", mark_dirty=False)

            if self.audio_file and getattr(self, "timeline", None) and getattr(self.timeline, "waveform_peaks", None):
                try:
                    write_waveform_peak_cache(self.audio_file, self.timeline.waveform_peaks)
                except Exception:
                    pass

            data = self.project_data()
            errors = self.validate_project_data(data)
            if errors:
                message = "Project validation failed:\n\n" + "\n".join(f"• {item}" for item in errors)
                if hasattr(self, "log_activity"):
                    self.log_activity(f"[ERROR] Project validation failed: {'; '.join(errors)}", mark_dirty=False)
                QMessageBox.critical(self, "Project Validation Error", message)
                return False

            if self.project_file.exists():
                shutil.copy2(self.project_file, backup_file)
                if hasattr(self, "log_activity"):
                    self.log_activity(f"[PROJECT] Previous project saved as recovery backup: {backup_file.name}", mark_dirty=False)

            write_rtvs_project_file(self.project_file, data)
            try:
                self.project_file.with_suffix(self.project_file.suffix + ".autosave").unlink(missing_ok=True)
            except Exception:
                pass
            self.project_dirty = False
            self._remember_saved_project(str(self.project_file))
            if hasattr(self, "update_window_title"):
                self.update_window_title()
            saved_time = QTime.currentTime().toString("hh:mm:ss A")
            if hasattr(self, "save_state_label"):
                self.save_state_label.setText(f"✓ Saved {saved_time}")
            self.statusBar().showMessage(f"Project saved: {self.project_file.name}")
            return True
        except Exception as exc:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] Project save failed: {exc}", mark_dirty=False)
            QMessageBox.critical(self, "Save Error", str(exc))
            return False
        finally:
            self.save_in_progress = False

    def load_project_file(self, filename, prompt=True, preserve_media=False):
        project_path = Path(filename).expanduser().resolve()
        if not project_path.exists():
            QMessageBox.critical(self, "Error", f"Project file not found: {filename}")
            return False

        if not preserve_media and prompt and getattr(self, "project_dirty", False):
            answer = QMessageBox.question(
                self,
                "Open Project",
                "Open project? Unsaved changes in the current project will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False

        try:
            data = read_rtvs_project_file(project_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not read project file: {exc}")
            return False

        errors = self.validate_project_data(data)
        if errors:
            message = "Project file validation failed:\n\n" + "\n".join(f"• {item}" for item in errors)
            QMessageBox.critical(self, "Invalid Project", message)
            return False

        ref = data.get("audio_file")
        resolved_audio = None
        if ref:
            direct_candidate = (project_path.parent / ref).resolve()
            if direct_candidate.exists():
                resolved_audio = direct_candidate
            else:
                abs_candidate = Path(ref).resolve()
                if abs_candidate.exists():
                    resolved_audio = abs_candidate

        if not preserve_media:
            if not self.close_project(prompt=False):
                return False
            if resolved_audio and resolved_audio.exists():
                self.audio_file = resolved_audio
                self.current_media_is_video = str(resolved_audio.suffix).lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi"}
                self.player.setSource(QUrl.fromLocalFile(str(self.audio_file)))
                self.timeline.set_audio_filename(self.audio_file.name)
                self.update_media_dependent_ui()

        self.project_file = project_path
        self.duration = float(data.get("duration", 0.0) or 0.0)
        self.transcript = data.get("transcript")
        self.transcript_notes = data.get("transcript_notes", "")
        self.diarization = data.get("diarization")
        self.speaker_names = {k: str(v) for k, v in data.get("speaker_names", {}).items()}
        self.segment_speaker_overrides = {
            int(k): str(v) for k, v in data.get("segment_speaker_overrides", {}).items()
        }
        self.translations = data.get("translations", {})
        self.translation_display_mode = data.get("translation_display_mode", "off")

        self.stories = []
        for s in data.get("stories", []):
            try:
                self.stories.append(Story.from_dict(s))
            except Exception:
                pass

        self.plugins_project_data = data.get("plugins_data", {})

        self.timeline.set_duration(self.duration)
        self.timeline.set_stories(self.stories)
        self.refresh_story_list()
        self.refresh_transcript_view()

        session = data.get("session", {})
        pos = float(session.get("position", 0.0) or 0.0)
        self.current_position = max(0.0, min(self.duration, pos))
        self.timeline.set_position(self.current_position)

        self.project_dirty = False
        if hasattr(self, "update_window_title"):
            self.update_window_title()
        self._remember_saved_project(str(project_path))
        self.statusBar().showMessage(f"Project loaded: {project_path.name}")
        return True

    def load_project(self, filename=None):
        if not filename:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Load Project", self._dialog_directory(),
                "RadioTV Story Segmenter Projects (*.rtvs);;Legacy Projects (*.json);;All Files (*.*)",
            )
        if filename:
            try:
                directory = str(Path(filename).resolve().parent)
                self.settings_store.setValue("last_open_directory", directory)
                self.settings_store.sync()
            except Exception:
                pass
            return self.load_project_file(filename, prompt=True, preserve_media=False)
        return False

    def open_purge_project_data_dialog(self):
        """Open the modal dialog allowing users to selectively wipe project data."""
        is_es = (getattr(self, "language", "en") == "es")
        dialog = ProjectDataPurgeDialog(self, is_es=is_es)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_purge_options()
            self.purge_project_data(
                purge_transcript=options.get("transcript", False),
                purge_translations=options.get("translations", False),
                purge_speakers=options.get("speakers", False),
                purge_stories=options.get("stories", False),
                purge_media=options.get("media", False),
            )

    def purge_project_data(
        self,
        purge_transcript: bool = False,
        purge_translations: bool = False,
        purge_speakers: bool = False,
        purge_stories: bool = False,
        purge_media: bool = False,
    ) -> bool:
        """Selectively wipe project components while preserving user undo history."""
        if not any([purge_transcript, purge_translations, purge_speakers, purge_stories, purge_media]):
            return False

        is_es = (getattr(self, "language", "en") == "es")

        # 1. Capture snapshot for Undo (Ctrl+Z)
        before_state = None
        if hasattr(self, "_capture_project_state"):
            before_state = self._capture_project_state()

        purged_items = []

        if purge_transcript:
            self.transcript = None
            self.transcript_notes = ""
            if hasattr(self, "transcription_result_received"):
                self.transcription_result_received = False
            if hasattr(self, "processing_status") and isinstance(self.processing_status, dict):
                self.processing_status["transcription"] = False
            if hasattr(self, "transcript_view") and self.transcript_view:
                self.transcript_view.clear()
                self.transcript_view.set_char_timestamp_map([])
            if hasattr(self, "comments_panel") and self.comments_panel:
                self.comments_panel.set_comments([])
            self.pipeline_active = False
            self.pipeline_queue = []
            self.pipeline_rerun_confirmed = False
            purged_items.append("Transcripción y palabras" if is_es else "Transcript & Words")

        if purge_translations:
            self.translations = {}
            self.translation_display_mode = "en"
            if hasattr(self, "processing_status") and isinstance(self.processing_status, dict):
                self.processing_status["translation"] = False
            if hasattr(self, "update_translation_language_selector"):
                self.update_translation_language_selector()
            purged_items.append("Traducciones" if is_es else "Translations")

        if purge_speakers:
            self.diarization = None
            self.diarization_result = None
            self.speaker_names = {}
            self.segment_speaker_overrides = {}
            self._diar_index_key = None
            self._diar_sorted_segments = None
            self._diar_speaker_labels = set()
            self.pending_diarization = False
            self.pipeline_speaker_detection_requested = False
            if hasattr(self, "processing_status") and isinstance(self.processing_status, dict):
                self.processing_status["diarization"] = False
            if hasattr(self, "speaker_status") and self.speaker_status:
                self.speaker_status.setText("Speaker detection has not been run." if not is_es else "No se ha ejecutado la detección de hablantes.")
            # If transcript is kept, strip speaker annotations from segments
            if self.transcript and isinstance(self.transcript, dict):
                for seg in self.transcript.get("segments", []) or []:
                    if isinstance(seg, dict):
                        seg.pop("speaker", None)
            purged_items.append("Diarización de hablantes" if is_es else "Speaker Diarization")

        if purge_stories:
            self.stories = []
            self.current_selected_story_indices = []
            if hasattr(self, "processing_status") and isinstance(self.processing_status, dict):
                self.processing_status["stories"] = False
            if hasattr(self, "timeline") and self.timeline:
                self.timeline.set_stories([])
            if hasattr(self, "refresh_story_list"):
                self.refresh_story_list()
            if hasattr(self, "start_input"):
                self.start_input.clear()
            if hasattr(self, "end_input"):
                self.end_input.clear()
            if hasattr(self, "title_input"):
                self.title_input.clear()
            if hasattr(self, "story_boundary_container"):
                self.story_boundary_container.setVisible(False)
            purged_items.append("Historias y metadatos" if is_es else "Stories & Metadata")

        if purge_media:
            if getattr(self, "player", None):
                self.player.stop()
                self.player.setSource(QUrl())
            self.audio_file = None
            self.duration = 0.0
            self.current_position = 0.0
            if hasattr(self, "play_button"):
                self.play_button.setText("▶ Play")
            if hasattr(self, "time_label"):
                self.time_label.setText("00:00.000 / 00:00.000")
            if hasattr(self, "timeline") and self.timeline:
                self.timeline.set_duration(0.0)
                self.timeline.set_position(0.0)
            if hasattr(self, "waveform_view") and self.waveform_view:
                self.waveform_view.set_audio(None)
            purged_items.append("Vínculo de medios" if is_es else "Media Link")

        # Refresh UI
        if hasattr(self, "refresh_transcript_view"):
            self.refresh_transcript_view()
        elif hasattr(self, "render_transcript") and self.transcript:
            self.render_transcript()

        if hasattr(self, "refresh_story_list"):
            self.refresh_story_list()

        self.project_dirty = True
        if hasattr(self, "update_window_title"):
            self.update_window_title()

        # Commit undo state
        if before_state and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, "Purge Project Data")

        summary = ", ".join(purged_items)
        if hasattr(self, "log_activity"):
            self.log_activity(f"[PROJECT] Purged components: {summary}")
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(
                f"Purged: {summary}. Press Ctrl+Z to undo." if not is_es
                else f"Purgado: {summary}. Presione Ctrl+Z para deshacer.",
                6000
            )
        return True


class ProjectDataPurgeDialog(QDialog):
    """Modal dialog allowing users to selectively clear/purge project components."""

    def __init__(self, parent=None, is_es=False):
        super().__init__(parent)
        self.is_es = is_es
        self.setWindowTitle("Limpiar / Purgar datos del proyecto" if is_es else "Clear / Purge Project Data")
        self.resize(540, 440)
        make_dialog_maximizable(self)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header description
        desc_text = (
            "Seleccione los componentes del proyecto que desea purgar o restablecer. "
            "Esta acción se puede deshacer inmediatamente con Edición > Deshacer (Ctrl+Z)."
            if self.is_es else
            "Select the project components you wish to purge or reset. "
            "This action can be undone immediately with Edit > Undo (Ctrl+Z)."
        )
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Warning banner
        warning_box = QLabel(
            "⚠️ Los datos seleccionados se eliminarán de la memoria de la sesión actual."
            if self.is_es else
            "⚠️ Selected data components will be cleared from the active session memory."
        )
        warning_box.setWordWrap(True)
        warning_box.setStyleSheet(
            "background-color: rgba(220, 53, 69, 0.12); color: #dc3545; "
            "border: 1px solid rgba(220, 53, 69, 0.3); border-radius: 6px; padding: 8px 12px; font-weight: bold;"
        )
        layout.addWidget(warning_box)

        # Group box of options
        group_title = "Componentes a purgar" if self.is_es else "Components to Purge"
        group = QGroupBox(group_title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        # Checkboxes
        self.chk_transcript = QCheckBox(
            "Transcripción y palabras temporizadas" if self.is_es else "Transcript & Timed Words"
        )
        self.chk_transcript.setToolTip(
            "Eliminar segmentos de transcripción, marcas de tiempo por palabra y mapas de caracteres."
            if self.is_es else
            "Wipe transcription segments, word-level timestamps, and character maps."
        )

        self.chk_translations = QCheckBox(
            "Traducciones guardadas" if self.is_es else "Saved Translations"
        )
        self.chk_translations.setToolTip(
            "Eliminar traducciones de español/inglés y alineaciones bilingües."
            if self.is_es else
            "Delete saved Spanish/English translation segments and bilingual alignments."
        )

        self.chk_speakers = QCheckBox(
            "Diarización de hablantes" if self.is_es else "Speaker Diarization"
        )
        self.chk_speakers.setToolTip(
            "Restablecer etiquetas de hablantes y nombres personalizados al estado inicial."
            if self.is_es else
            "Reset speaker labels and custom speaker names to unassigned state."
        )

        self.chk_stories = QCheckBox(
            "Historias y metadatos segmentados" if self.is_es else "Stories & Segmented Metadata"
        )
        self.chk_stories.setToolTip(
            "Eliminar todas las historias, límites de tiempo, títulos y resúmenes."
            if self.is_es else
            "Remove all segmented story boundaries, custom titles, and excerpts."
        )

        self.chk_media = QCheckBox(
            "Vínculo de archivo de audio/video" if self.is_es else "Audio / Video Media Link"
        )
        self.chk_media.setToolTip(
            "Desvincular el archivo de medios activo y restablecer la posición de reproducción."
            if self.is_es else
            "Unlink active media file and reset playback position / duration."
        )

        for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media):
            group_layout.addWidget(chk)
            chk.toggled.connect(self._update_purge_button_state)

        layout.addWidget(group)

        # Selection helpers
        sel_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar todo" if self.is_es else "Select All")
        deselect_all_btn = QPushButton("Deseleccionar todo" if self.is_es else "Deselect All")
        select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        deselect_all_btn.clicked.connect(lambda: self._set_all_checked(False))
        sel_layout.addWidget(select_all_btn)
        sel_layout.addWidget(deselect_all_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        layout.addSpacing(6)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar" if self.is_es else "Cancel")
        cancel_btn.clicked.connect(self.reject)

        self.purge_btn = QPushButton("Purgar datos seleccionados" if self.is_es else "Purge Selected Data")
        self.purge_btn.setStyleSheet(
            "QPushButton { background-color: #d9534f; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #c9302c; }"
            "QPushButton:disabled { background-color: #e0e0e0; color: #888888; }"
        )
        self.purge_btn.clicked.connect(self.accept)
        self.purge_btn.setEnabled(False)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.purge_btn)
        layout.addLayout(btn_layout)

    def _set_all_checked(self, checked: bool):
        for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media):
            chk.setChecked(checked)

    def _update_purge_button_state(self):
        any_checked = any(
            chk.isChecked() for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media)
        )
        self.purge_btn.setEnabled(any_checked)

    def get_purge_options(self) -> dict[str, bool]:
        return {
            "transcript": self.chk_transcript.isChecked(),
            "translations": self.chk_translations.isChecked(),
            "speakers": self.chk_speakers.isChecked(),
            "stories": self.chk_stories.isChecked(),
            "media": self.chk_media.isChecked(),
        }


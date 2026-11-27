"""Story boundary detection processing mixin for Radio & TV Story Segmenter."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QDialog, QMessageBox

from prs_shared import (
    Story,
    SetStoriesCommand,
    StoryAutoDetectWorker,
    format_time,
    get_story_vocabulary,
)

logger = logging.getLogger(__name__)


class StoryDetectionProcessingMixin:
    def start_auto_detect_stories(self, overrides: Optional[Dict[str, Any]] = None):
        if not isinstance(overrides, dict):
            overrides = None
        if not self.audio_file:
            return

        default_mode = str(getattr(self, "story_detection_mode", "voice") or "voice")
        default_silence = float(getattr(self, "silence_threshold", 3.0) or 3.0)
        default_padding = float(getattr(self, "lead_in_padding", 0.5) if getattr(self, "lead_in_padding", None) is not None else 0.5)
        raw_min_story = getattr(self, "min_story_duration", 3.0)
        try:
            default_min_story = max(0.0, float(raw_min_story if raw_min_story is not None else 3.0))
        except (TypeError, ValueError):
            default_min_story = 3.0

        eff_mode = default_mode
        eff_silence = default_silence
        eff_padding = default_padding
        eff_min_story = default_min_story
        is_one_time_override = False

        is_standalone = (not getattr(self, "pipeline_active", False)) and (not getattr(self, "batch_active", False))
        if isinstance(overrides, dict):
            eff_mode = str(overrides.get("story_detection_mode", default_mode) or default_mode)
            eff_silence = float(overrides.get("silence_threshold", default_silence))
            eff_padding = float(overrides.get("lead_in_padding", default_padding))
            eff_min_story = max(0.0, float(overrides.get("min_story_duration", default_min_story)))
            save_as_defaults = bool(overrides.get("save_as_defaults", False))
            if save_as_defaults:
                self._persist_story_detect_defaults(eff_mode, eff_silence, eff_padding, eff_min_story)
            else:
                is_one_time_override = (
                    eff_mode != default_mode
                    or abs(eff_silence - default_silence) > 1e-6
                    or abs(eff_padding - default_padding) > 1e-6
                    or abs(eff_min_story - default_min_story) > 1e-6
                )
        elif is_standalone and not os.environ.get("RTVS_HEADLESS_SKIP_DETECT_DIALOG"):
            vocab = get_story_vocabulary(self)
            from story_detect_dialog import StandaloneDetectStoriesDialog

            dlg = StandaloneDetectStoriesDialog(
                parent=self,
                existing_count=len(getattr(self, "stories", []) or []),
                silence_threshold=default_silence,
                min_story_duration=default_min_story,
                detection_mode=default_mode,
                lead_in_padding=default_padding,
                is_es=vocab.is_es,
                term=vocab.singular,
                term_plural=vocab.plural,
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            vals = dlg.get_values()
            eff_mode = vals["story_detection_mode"]
            eff_silence = vals["silence_threshold"]
            eff_padding = vals["lead_in_padding"]
            eff_min_story = max(0.0, vals["min_story_duration"])
            if vals["save_as_defaults"]:
                self._persist_story_detect_defaults(eff_mode, eff_silence, eff_padding, eff_min_story)
            else:
                is_one_time_override = (
                    eff_mode != default_mode
                    or abs(eff_silence - default_silence) > 1e-6
                    or abs(eff_padding - default_padding) > 1e-6
                    or abs(eff_min_story - default_min_story) > 1e-6
                )

        is_music = (eff_mode == "music")
        term = "Song" if is_music else "Story"
        self._active_story_detect_mode = eff_mode

        self.set_tools_actions_enabled(False)
        self.set_processing_stage(f"{term} Detection")
        if not self.pipeline_active:
            self.processing_status["stories"] = False
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_button.show()
        mode_str = eff_mode.capitalize()
        override_note = ", one-time override" if is_one_time_override else ""
        self.log_activity(
            f"[{'SONG' if is_music else 'STORY'} DETECT] Started {term.lower()} detection "
            f"(Mode: {mode_str}, Threshold: {eff_silence:.1f}s, Padding: {eff_padding:.1f}s, "
            f"Min Segment Length: {eff_min_story:.1f}s{override_note})"
        )

        self.story_job_token += 1
        job_token = self.story_job_token
        self.thread = QThread(self)
        self._track_worker_thread(self.thread)

        transcript_segments = []
        if isinstance(self.transcript, dict):
            transcript_segments = self.transcript.get("segments", [])
        elif isinstance(self.transcript, list):
            transcript_segments = self.transcript

        self.worker = StoryAutoDetectWorker(
            self.audio_file,
            silence_threshold=eff_silence,
            lead_in_padding=eff_padding,
            audio_duration=getattr(self, "duration", 0),
            transcript_segments=transcript_segments,
            whisper_model=getattr(self, "whisper_model", "parakeet-onnx"),
            detection_mode=eff_mode,
            min_story_duration=eff_min_story,
        )
        self.worker.moveToThread(self.thread)
        self.worker._job_token = job_token
        self.thread.setProperty("job_token", job_token)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.auto_detect_progress)
        self.worker.finished.connect(self.auto_detect_finished)
        self.worker.error.connect(self.auto_detect_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.worker_thread_finished)

        self.thread.start()

    def _persist_story_detect_defaults(
        self,
        detection_mode: str,
        silence_threshold: float,
        lead_in_padding: float,
        min_story_duration: float,
    ) -> None:
        self.story_detection_mode = str(detection_mode or "voice")
        self.silence_threshold = float(silence_threshold)
        self.lead_in_padding = float(lead_in_padding)
        self.min_story_duration = max(0.0, float(min_story_duration))
        store = getattr(self, "settings_store", None)
        if store is not None:
            store.setValue("story_detection_mode", self.story_detection_mode)
            store.setValue("silence_threshold", self.silence_threshold)
            store.setValue("lead_in_padding", self.lead_in_padding)
            store.setValue("min_story_duration", self.min_story_duration)
        if hasattr(self, "update_story_segment_terminology"):
            self.update_story_segment_terminology()

    def auto_detect_progress(self, message, percent):
        self.update_processing_progress(percent, message)

    def auto_detect_finished(self, new_stories):
        try:
            # Stale Worker State Overwrite Guard (Item 1.1 / P1-03)
            current_media = str(Path(self.audio_file).resolve()) if getattr(self, "audio_file", None) else None
            target_media = getattr(getattr(self, "worker", None), "audio_file", None)
            target_media_resolved = str(Path(target_media).resolve()) if target_media else None
            if target_media_resolved and current_media != target_media_resolved:
                self.log_activity(
                    f"[STORY DETECT] Ignored stale completion payload: active media changed from {target_media_resolved} to {current_media}.",
                    mark_dirty=False
                )
                return

            worker_token = getattr(getattr(self, "worker", None), "_job_token", None)
            if worker_token is not None and worker_token != getattr(self, "story_job_token", None):
                self.log_activity(
                    f"[STORY DETECT] Ignored obsolete job token #{worker_token} (active job is #{getattr(self, 'story_job_token', None)}).",
                    mark_dirty=False
                )
                return

            # 1. Complete progress and stop the 1-second ETA timer unconditionally
            self.progress.setValue(100)
            self.progress.hide()
            self.cancel_button.hide()
            if hasattr(self, "skip_stage_button"):
                self.skip_stage_button.hide()
            self.set_processing_stage(None)
            self.set_tools_actions_enabled(True)

            # 2. Commit stories to project state and update UI lists
            active_mode = getattr(self, "_active_story_detect_mode", None) or getattr(self, "story_detection_mode", "voice")
            is_music = (active_mode == "music")
            self._active_story_detect_mode = None
            term = "Song" if is_music else "Story"
            term_plural = "Songs" if is_music else "Stories"
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            self.commit_story_change(old_stories, new_stories, f"Detect {term_plural}")

            count = len(new_stories)
            self.processing_status["stories"] = True
            self.update_processing_stage_summary()
            msg = f"{term} detection complete: Created {count} {term.lower()} region(s)."
            self.log_activity(f"[{'SONG' if is_music else 'STORY'} DETECT] Complete: Auto-created {count} {term.lower()} region(s).")
            self.statusBar().showMessage(msg)
            self.save_project()

            # 3. Advance automated multi-stage pipelines if active
            if self.pipeline_active and self.pipeline_queue:
                QTimer.singleShot(0, self._run_next_selected_processing)
            elif self.batch_active and self.pipeline_active:
                self.pipeline_active = False
                self._batch_export_current()
                QTimer.singleShot(0, self._batch_next_media)
            elif self.pipeline_active:
                self.pipeline_active = False
                self.log_activity("[AUTOMATION] Selected processing complete.")
        except Exception as exc:
            logger.exception("Error in auto_detect_finished")
            self.log_activity(f"[STORY DETECT ERROR] Error processing story detection results: {exc}")
            self.progress.hide()
            self.cancel_button.hide()
            if hasattr(self, "skip_stage_button"):
                self.skip_stage_button.hide()
            self.set_processing_stage(None)
            self.set_tools_actions_enabled(True)
            if getattr(self, "pipeline_active", False) and getattr(self, "pipeline_queue", []):
                self.log_activity(
                    f"[PIPELINE RECOVERY] Advancing to next queued stage '{self.pipeline_queue[0]}' following story detection error."
                )
                QTimer.singleShot(100, self._run_next_selected_processing)
            else:
                self.pipeline_active = False
                self.pipeline_queue = []

    def auto_detect_error(self, message):
        self.progress.hide()
        self.cancel_button.hide()
        if hasattr(self, "skip_stage_button"):
            self.skip_stage_button.hide()
        self.set_tools_actions_enabled(True)
        self.set_processing_stage(None)

        if getattr(self, "batch_active", False):
            self.log_activity(f"[BATCH ERROR] Story detection error: {message}")
            if hasattr(self, "_batch_media_error"):
                self._batch_media_error(message)
            return

        if message == "Process canceled by user.":
            self.statusBar().showMessage("Story detection canceled by user.")
            if getattr(self, "pipeline_active", False):
                self.pipeline_active = False
                self.pipeline_queue = []
                self.pipeline_rerun_confirmed = False
        else:
            self.log_activity(f"[STORY DETECT] Error: {message}")
            if getattr(self, "pipeline_active", False) and getattr(self, "pipeline_queue", []):
                next_stage = self.pipeline_queue[0]
                reply = QMessageBox.question(
                    self,
                    "Story Detection Failed",
                    f"Story Detection failed: {message}\n\nWould you like to skip this stage and continue with '{next_stage}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.log_activity(f"[PIPELINE RECOVERY] User skipped failed story detection; continuing with '{next_stage}'.")
                    QTimer.singleShot(0, self._run_next_selected_processing)
                    return
                else:
                    self.pipeline_active = False
                    self.pipeline_queue = []
                    self.pipeline_rerun_confirmed = False
            else:
                if getattr(self, "pipeline_active", False):
                    self.pipeline_active = False
                    self.pipeline_queue = []
                    self.pipeline_rerun_confirmed = False
                QMessageBox.critical(self, "Story Detection Error", message)


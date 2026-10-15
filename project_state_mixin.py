"""Radio & TV Story Segmenter — Project State, Undo/Redo & Processing Progress Mixin.

Manages project state snapshots, undo/redo stack push/restore operations,
dirty tracking, window title formatting, and multi-stage processing ETA/progress calculations.
"""

import copy
import logging
import sys
import time
from pathlib import Path

from prs_shared import APP_DISPLAY_NAME, PROJECT_VERSION, Story, ProjectStateCommand

logger = logging.getLogger(__name__)


class ProjectStateMixin:
    """Provides project state snapshotting, undo/redo state restoration, and progress tracking."""

    def _format_elapsed_time(self, seconds: float) -> str:
        seconds = max(0, int(seconds))
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m}m {s:02d}s"

    def _format_time_remaining(self, seconds: float) -> str:
        seconds = max(0, int(seconds))
        if seconds <= 0:
            return "0s"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"~{h}h {m:02d}m"
        if m > 0:
            return f"~{m}m {s:02d}s" if m < 5 else f"~{m}m"
        return f"~{s}s"

    def _get_stage_estimated_duration(self, stage_key: str) -> float:
        dur = float(getattr(self, "duration", 0.0) or 0.0)
        if dur <= 0:
            return 30.0
        ratios = {
            "transcription": 0.20,
            "diarization": 0.08,
            "stories": 0.02,
            "translation": 0.05,
        }
        base_ratio = ratios.get(stage_key, 0.05)
        return max(5.0, dur * base_ratio)

    def calculate_processing_eta(self, percent: float) -> tuple[float, float, str]:
        now = time.monotonic()
        stage_start = getattr(self, "stage_start_monotonic", None) or now
        elapsed = max(0.001, now - stage_start)

        if percent > 2.0:
            stage_total_est = (elapsed / (percent / 100.0))
            stage_remaining = max(0.0, stage_total_est - elapsed)
        else:
            stage_key = getattr(self, "current_processing_stage_key", "")
            stage_remaining = self._get_stage_estimated_duration(stage_key)

        queue = getattr(self, "pipeline_queue", [])
        queued_stages_est = sum(self._get_stage_estimated_duration(sk) for sk in queue)

        total_remaining = stage_remaining + queued_stages_est
        eta_str = self._format_time_remaining(total_remaining)
        return stage_remaining, total_remaining, eta_str

    def set_processing_stage(self, stage, detail=""):
        if stage:
            stage_key = stage.lower()
            names = {
                "transcription": "Transcribing",
                "diarization": "Detecting Speakers",
                "stories": "Detecting Stories",
                "translation": "Translating",
            }
            stage_name = names.get(stage_key, stage.capitalize())
            self.current_processing_stage_key = stage_key
            self.current_processing_stage_name = stage_name
            self.current_processing_stage_detail = detail
            self.stage_start_monotonic = time.monotonic()
            self.last_reported_stage_percent = 0
            self.last_reported_stage_message = ""

            if not getattr(self, "pipeline_active", False):
                self.pipeline_total_stages = 1
                self.pipeline_current_stage_idx = 1
                self.pipeline_all_stages = [stage_key]
                self.pipeline_start_monotonic = self.stage_start_monotonic
            else:
                total = getattr(self, "pipeline_total_stages", 1)
                queue_len = len(getattr(self, "pipeline_queue", []))
                calc_idx = max(1, total - queue_len)
                curr_idx = getattr(self, "pipeline_current_stage_idx", 1)
                self.pipeline_current_stage_idx = max(curr_idx, calc_idx)
                if not getattr(self, "pipeline_start_monotonic", None):
                    self.pipeline_start_monotonic = self.stage_start_monotonic

            if not hasattr(self, "_progress_tick_timer"):
                from PySide6.QtCore import QTimer
                self._progress_tick_timer = QTimer(self)
                self._progress_tick_timer.setInterval(1000)
                self._progress_tick_timer.timeout.connect(self._on_progress_timer_tick)

            if not self._progress_tick_timer.isActive():
                self._progress_tick_timer.start()

            self.update_processing_progress(0, "")
        else:
            self.current_processing_stage_key = None
            self.current_processing_stage_name = ""
            self.current_processing_stage_detail = ""
            self.stage_start_monotonic = None
            self.last_reported_stage_percent = 0
            if not getattr(self, "pipeline_active", False):
                self.pipeline_start_monotonic = None
            if hasattr(self, "_progress_tick_timer") and self._progress_tick_timer.isActive():
                self._progress_tick_timer.stop()
            self.processing_stage_label.clear()
            self.processing_stage_label.hide()
            if hasattr(self, "progress"):
                self.progress.hide()
                self.progress.setFormat("%p%")

    def _on_progress_timer_tick(self):
        if getattr(self, "current_processing_stage_name", ""):
            pct = getattr(self, "last_reported_stage_percent", 0)
            self.update_processing_progress(pct)

    def update_processing_progress(self, percent: float, message: str = ""):
        percent = max(0, min(100, int(percent)))
        self.last_reported_stage_percent = percent
        
        stage_rem, total_rem, eta_str = self.calculate_processing_eta(percent)
        
        is_batch = getattr(self, "batch_active", False) and getattr(self, "batch_total_files", 0) > 1
        is_pipeline = getattr(self, "pipeline_active", False) and getattr(self, "pipeline_total_stages", 0) > 1
        stage_name = getattr(self, "current_processing_stage_name", "Processing")
        stage_detail = getattr(self, "current_processing_stage_detail", "")
        
        stage_desc = f"{stage_name}"
        if stage_detail:
            stage_desc += f" ({stage_detail})"

        if message:
            self.last_reported_stage_message = message
        else:
            message = getattr(self, "last_reported_stage_message", "")

        if is_batch:
            batch_file_start = getattr(self, "batch_file_start_time", None) or getattr(self, "stage_start_monotonic", None) or time.monotonic()
            file_elapsed = max(0.0, time.monotonic() - batch_file_start)
            elapsed_str = self._format_elapsed_time(file_elapsed)

            batch_curr = max(1, getattr(self, "batch_current_file_idx", 1))
            batch_total = max(1, getattr(self, "batch_total_files", 1))
            
            file_remaining = total_rem
            file_eta_str = self._format_time_remaining(file_remaining)
            
            current_file_total_est = file_elapsed + file_remaining
            
            completed_durations = getattr(self, "batch_completed_durations", [])
            if completed_durations:
                avg_dur = sum(completed_durations) / len(completed_durations)
            else:
                avg_dur = current_file_total_est
                
            remaining_files_after_this = max(0, batch_total - batch_curr)
            overall_remaining = file_remaining + (remaining_files_after_this * avg_dur)
            overall_eta_str = self._format_time_remaining(overall_remaining)
            
            label_text = f"File {batch_curr} of {batch_total} ({stage_desc}) — Elapsed: {elapsed_str} | File ETA: {file_eta_str} | Overall ETA: {overall_eta_str}"
            prog_format = f"File {batch_curr}/{batch_total} (%p%) — Elapsed: {elapsed_str} | File: {file_eta_str} | Job: {overall_eta_str}"
        elif is_pipeline:
            pipe_start = getattr(self, "pipeline_start_monotonic", None) or getattr(self, "stage_start_monotonic", None) or time.monotonic()
            pipe_elapsed = max(0.0, time.monotonic() - pipe_start)
            elapsed_str = self._format_elapsed_time(pipe_elapsed)

            current_idx = getattr(self, "pipeline_current_stage_idx", 1)
            total_stages = getattr(self, "pipeline_total_stages", 1)
            label_text = f"Stage {current_idx} of {total_stages}: {stage_desc} — Elapsed: {elapsed_str} | Remaining: {eta_str}"
            prog_format = f"Stage {current_idx}/{total_stages} (%p%) — Elapsed: {elapsed_str} | Remaining: {eta_str}"
        else:
            stage_start = getattr(self, "stage_start_monotonic", None) or getattr(self, "pipeline_start_monotonic", None) or time.monotonic()
            stage_elapsed = max(0.0, time.monotonic() - stage_start)
            elapsed_str = self._format_elapsed_time(stage_elapsed)

            if message:
                label_text = f"{stage_desc}: {message} — Elapsed: {elapsed_str} | Remaining: {eta_str}"
                prog_format = f"{message} (%p%)"
            else:
                label_text = f"{stage_desc} — Elapsed: {elapsed_str} | Remaining: {eta_str}"
                prog_format = f"%p% — Elapsed: {elapsed_str} | Remaining: {eta_str}"
            
        if hasattr(self, "processing_stage_label"):
            self.processing_stage_label.setText(label_text)
            self.processing_stage_label.show()
        if hasattr(self, "progress"):
            self.progress.setValue(percent)
            self.progress.setFormat(prog_format)
            self.progress.show()
        if message and hasattr(self, "statusBar"):
            self.statusBar().showMessage(message)

    def update_processing_stage_summary(self):
        if not hasattr(self, "processing_stage_label"):
            return
        done = []
        if self.processing_status.get("transcription"):
            done.append("Transcription")
        if self.processing_status.get("diarization"):
            done.append("Speaker Detection")
        if self.processing_status.get("stories"):
            done.append("Story Detection")
        if done:
            self.processing_stage_label.setToolTip("Completed: " + ", ".join(done))
        else:
            self.processing_stage_label.setToolTip("")

    @staticmethod
    def _clone_transcript_state(transcript):
        if transcript is None:
            return None
        return copy.deepcopy(transcript)

    def _capture_project_state(self):
        """Capture all editable project data for the application undo stack."""
        return {
            "stories": [s.to_dict() for s in self.stories],
            "transcript": self._clone_transcript_state(self.transcript),
            "diarization": copy.deepcopy(self.diarization) if self.diarization is not None else None,
            "speaker_names": dict(self.speaker_names),
            "segment_speaker_overrides": {str(k): v for k, v in self.segment_speaker_overrides.items()},
            "translations": copy.deepcopy(self.translations),
            "translation_display_mode": getattr(self, "translation_display_mode", "en"),
            "selected_indices": list(getattr(self, "current_selected_story_indices", [])),
        }

    def get_project_state(self):
        """Public alias for _capture_project_state for undo history capture."""
        return self._capture_project_state()

    def _restore_project_state_for_undo(self, state):
        """Restore a complete editable project state without creating another undo entry."""
        if getattr(self, "is_restoring_undo", False):
            return
        self.is_restoring_undo = True
        try:
            self.stories = [Story.from_dict(item) for item in state.get("stories", [])]
            self.transcript = self._clone_transcript_state(state.get("transcript"))
            self.diarization = copy.deepcopy(state.get("diarization")) if state.get("diarization") is not None else None
            self.speaker_names = {str(k): str(v) for k, v in state.get("speaker_names", {}).items()}
            self.segment_speaker_overrides = {int(k): str(v) for k, v in state.get("segment_speaker_overrides", {}).items()}
            self.translations = copy.deepcopy(state.get("translations", {}))
            self.translation_display_mode = state.get("translation_display_mode", "en")
            self.current_selected_story_indices = list(state.get("selected_indices", []))

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
            self.save_project()
        finally:
            self.is_restoring_undo = False

    def _commit_project_state_change(self, before_state, description="Modify Project"):
        """Push a complete project-state undo command after a mutation."""
        if getattr(self, "is_restoring_undo", False) or not before_state:
            return
        after_state = self._capture_project_state()
        if before_state == after_state:
            return
        self.undo_stack.push(ProjectStateCommand(self, before_state, after_state, description))

    def flush_pending_transcript_undo(self):
        """Commit a pending grouped text edit before another project action or Ctrl+Z."""
        timer = getattr(self, "_transcript_undo_timer", None)
        if timer is not None and timer.isActive():
            timer.stop()
        if getattr(self, "_pending_transcript_edit_before", None) is not None:
            before = self._pending_transcript_edit_before
            self._pending_transcript_edit_before = None
            self._commit_project_state_change(before, "Edit Transcript")

    def mark_project_dirty(self, reason=None):
        """Mark the current project as needing a save and refresh the UI state."""
        if getattr(self, "is_restoring_snapshot", False):
            return
        self.project_dirty = True
        self.update_window_title()
        if reason:
            self.log_activity(f"[PROJECT] {reason}", mark_dirty=False)

    def update_window_title(self):
        proj_name = self.project_file.name if getattr(self, "project_file", None) else "Unsaved"
        dirty_marker = " *" if getattr(self, "project_dirty", False) else ""
        self.setWindowTitle(f"{APP_DISPLAY_NAME} v{PROJECT_VERSION} — Project: {proj_name}{dirty_marker}")
        if hasattr(self, "save_state_label"):
            if getattr(self, "project_dirty", False):
                self.save_state_label.setText("● Unsaved changes")
            elif getattr(self, "project_file", None):
                self.save_state_label.setText("✓ Saved")
            else:
                self.save_state_label.setText("Not saved")

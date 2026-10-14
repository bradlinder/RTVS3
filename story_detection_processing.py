"""Story boundary detection processing mixin for Radio & TV Story Segmenter."""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QMessageBox

from prs_shared import (
    Story,
    SetStoriesCommand,
    StoryAutoDetectWorker,
    format_time,
)

logger = logging.getLogger(__name__)


class StoryDetectionProcessingMixin:
    def start_auto_detect_stories(self):
        if not self.audio_file:
            return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        if self.stories and not self.pipeline_active and not getattr(self, "pipeline_rerun_confirmed", False):
            answer = QMessageBox.question(
                self,
                f"Detect {term_plural}",
                f"Detecting {term.lower()} boundaries will replace your current {term_plural} list.\n\nDo you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.set_tools_actions_enabled(False)
        self.set_processing_stage(f"{term} Detection")
        if not self.pipeline_active:
            self.processing_status["stories"] = False
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_button.show()
        mode_str = str(getattr(self, "story_detection_mode", "voice") or "voice").capitalize()
        self.log_activity(
            f"[{'SONG' if is_music else 'STORY'} DETECT] Started {term.lower()} detection (Mode: {mode_str}, Threshold: {self.silence_threshold}s)"
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
            silence_threshold=self.silence_threshold,
            lead_in_padding=self.lead_in_padding,
            audio_duration=getattr(self, "duration", 0),
            transcript_segments=transcript_segments,
            whisper_model=getattr(self, "whisper_model", "parakeet-onnx"),
            detection_mode=getattr(self, "story_detection_mode", "voice"),
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

    def auto_detect_progress(self, message, percent):
        self.update_processing_progress(percent, message)

    def auto_detect_finished(self, new_stories):
        # 1. Complete progress and stop the 1-second ETA timer unconditionally
        self.progress.setValue(100)
        self.progress.hide()
        self.cancel_button.hide()
        self.set_processing_stage(None)
        self.set_tools_actions_enabled(True)

        # 2. Commit stories to project state and update UI lists
        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
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

    def auto_detect_error(self, message):
        self.progress.hide()
        self.cancel_button.hide()
        self.set_tools_actions_enabled(True)
        self.set_processing_stage(None)
        if getattr(self, "pipeline_active", False):
            self.pipeline_active = False
            self.pipeline_queue = []
            self.pipeline_rerun_confirmed = False
        if getattr(self, "batch_active", False):
            self.batch_active = False

        if message == "Process canceled by user.":
            self.statusBar().showMessage("Story detection canceled by user.")
        else:
            self.log_activity(f"[STORY DETECT] Error: {message}")
            self.log_activity(
                "[AUTOMATION] Story Detection failed. Run All Processing can resume from completed stages after the error is addressed."
            )
            QMessageBox.critical(self, "Story Detection Error", message)


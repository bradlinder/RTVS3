# processing.pyi — Typing and Interface Stub for processing
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import sys
import os
import json
import html
import logging
import threading
from pathlib import Path
from PySide6.QtCore import QProcess, QProcessEnvironment, QThread, Qt, QTimer, QEventLoop, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QDialog, QProgressDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox, QInputDialog
from prs_shared import HELPER_PROTOCOL_VERSION, Story, SetStoriesCommand, SelectStoriesCommand, StoryAutoDetectWorker, format_time, get_models_storage_dir, register_process, unregister_process
from prs_shared import compute_file_sha256, verify_file_sha256, collapse_repeating_ngrams, strip_hallucination_phrases, trim_trailing_degenerate_tail, scrub_transcript_segments, scrub_transcript
from model_management import WhisperModelInstallWorker

class RuntimeSetupWorker(QThread):
    progress = ...
    finished_ok = ...

    def __init__(self, runtime_mgr, feature, parent=..., ensure_kwargs=...):
        ...

    def cancel(self):
        ...

    def run(self):
        ...
from transcription_processing import TranscriptionProcessingMixin
from diarization_processing import DiarizationProcessingMixin
from story_detection_processing import StoryDetectionProcessingMixin

class ProcessingMixin(TranscriptionProcessingMixin, DiarizationProcessingMixin, StoryDetectionProcessingMixin):
    _CORE_BUNDLED_FEATURES = ...

    def _ensure_runtime_environment_responsive(self, feature, **ensure_kwargs) -> bool:
        ...

    def cancel_current_process(self):
        ...

    def update_skip_stage_button_visibility(self):
        ...

    def skip_current_pipeline_stage(self):
        ...

    def commit_story_change(self, old_stories, new_stories, description=...):
        ...

    def apply_story_selection_indices(self, selected_rows, seek=...):
        ...

    def on_timeline_story_clicked(self, index):
        ...

    def story_selection_changed(self):
        ...

    def handle_timeline_multi_selection(self, selected_indices):
        ...

    def set_tools_actions_enabled(self, enabled):
        ...

    def stop_story_detection_worker(self, timeout_ms=...):
        ...

    def stop_all_processing(self, timeout_ms=...):
        ...

    def confirm_stop_processing_for_media_change(self):
        ...

    def worker_thread_finished(self):
        ...

    def start_full_auto_pipeline(self):
        ...

    def _confirm_pipeline_rerun_if_needed(self, stages, parent=...):
        ...

    def _run_next_selected_processing(self):
        ...

    def start_transcribe_and_diarize(self):
        ...

    def _processing_choice(self, kind):
        ...

    def _worker_command(self, args):
        ...

    def _resolve_worker_command(self, args):
        ...

    def _apply_worker_env_overrides(self, process, env_overrides):
        ...

    def _download_model_and_continue_transcription(self, model_name: str, label: str):
        ...

    def _on_transcription_dl_progress(self, pct: int, msg: str):
        ...

    def _on_transcription_dl_cancel(self):
        ...

    def _on_transcription_dl_finished(self, err):
        ...

    def _on_transcription_dl_thread_cleanup(self):
        ...

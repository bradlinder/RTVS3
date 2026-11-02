# project_state_mixin.pyi — Typing and Interface Stub for project_state_mixin
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import copy
import logging
import sys
import time
from pathlib import Path
from prs_shared import APP_DISPLAY_NAME, PROJECT_VERSION, Story, ProjectStateCommand

class ProjectStateMixin:

    def _format_elapsed_time(self, seconds: float) -> str:
        ...

    def _format_time_remaining(self, seconds: float) -> str:
        ...

    def _get_stage_estimated_duration(self, stage_key: str) -> float:
        ...

    def calculate_processing_eta(self, percent: float) -> tuple[float, float, str]:
        ...

    def set_processing_stage(self, stage, detail=...):
        ...

    def _on_progress_timer_tick(self):
        ...

    def update_processing_progress(self, percent: float, message: str=...):
        ...

    def update_processing_stage_summary(self):
        ...

    @staticmethod
    def _clone_transcript_state(transcript):
        ...

    def _capture_project_state(self):
        ...

    def get_project_state(self):
        ...

    def _restore_project_state_for_undo(self, state):
        ...

    def _commit_project_state_change(self, before_state, description=...):
        ...

    def flush_pending_transcript_undo(self):
        ...

    def mark_project_dirty(self, reason=...):
        ...

    def update_window_title(self):
        ...

    def is_project_empty(self) -> bool:
        ...

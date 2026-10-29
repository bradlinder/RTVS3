# story_crud_mixin.pyi — Typing and Interface Stub for story_crud_mixin
from __future__ import annotations
from __future__ import annotations
from typing import Any, List, Optional
from core_utils import INTERNAL_APP_ID, format_time, parse_time
from story_model import Story, SetStoriesCommand, StoryBoundaryChangeCommand
from story_fades_dialog import StoryFadesDialog

class StoryCrudMixin:

    def refresh_story_list(self):
        ...

    def handle_new_story_started(self, start_time: float, end_time: float):
        ...

    def handle_new_story_updated(self, start_time: float, end_time: float):
        ...

    def handle_drag_story_region(self, index: int, start_time: float, end_time: float):
        ...

    def audition_story(self, index: int):
        ...

    def handle_drag_finished(self):
        ...

    def update_selected_story(self):
        ...

    def delete_selected_story(self):
        ...

    def get_current_interaction_time(self, for_boundary=...):
        ...

    def set_selected_story_start(self):
        ...

    def set_selected_story_end(self):
        ...

    def add_selection_to_story(self):
        ...

    def play_transcript_selection(self):
        ...

    def select_all_stories(self):
        ...

    def handle_timeline_selection_range_changed(self, start_time: Optional[float], end_time: Optional[float]):
        ...

    def add_story_from_range(self, start_time: float, end_time: float):
        ...

    def add_story_from_active_selection(self):
        ...

    def open_story_fades_dialog(self, story_index: Optional[int]=...):
        ...

    def apply_fades_to_selected_stories(self, fade_in: Optional[float]=..., fade_out: Optional[float]=..., fade_curve: Optional[str]=...):
        ...

    def remove_fades_from_selected_stories(self):
        ...

    def set_fade_curve_for_selected_stories(self, curve_type: str):
        ...

    def open_story_metadata_dialog(self, target_story_index: Optional[int]=..., modal: bool=...):
        ...

    def _notify_floating_dialogs(self):
        ...

    def _close_floating_dialogs(self, persist_drafts: bool=...):
        ...

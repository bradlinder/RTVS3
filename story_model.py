"""Radio & TV Story Segmenter — Story Model, Boundaries & Undo Commands.

Provides:
- Story: Core data model representing a segmented audio/video story cut.
- Boundary & overlap validation functions.
- Undo/redo commands: SetStoriesCommand, SelectStoriesCommand, StoryBoundaryChangeCommand.
- Fade curve tables and mathematical factor helpers.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

import os, sys
from qt_compat import _ensure_pyside6_fallback

if os.environ.get("RTVS_WORKER_MODE") == "1" or (getattr(sys, "frozen", False) and not hasattr(sys, "_MEIPASS_GUI")):
    _ensure_pyside6_fallback()
    QSettings = getattr(sys.modules["PySide6.QtCore"], "QSettings")
    QUndoCommand = getattr(sys.modules["PySide6.QtGui"], "QUndoCommand")
else:
    try:
        from PySide6.QtCore import QSettings
        from PySide6.QtGui import QUndoCommand
    except (ImportError, Exception, BaseException):
        _ensure_pyside6_fallback()
        QSettings = getattr(sys.modules["PySide6.QtCore"], "QSettings")
        QUndoCommand = getattr(sys.modules["PySide6.QtGui"], "QUndoCommand")

from core_utils import INTERNAL_APP_ID, format_time


FADE_CURVE_TABLES: Dict[str, Dict[str, Any]] = {
    "linear": {
        "label": "Linear",
        "description": "Standard linear volume ramp (constant slope).",
    },
    "s_curve": {
        "label": "S-Curve",
        "description": "Smooth sinusoidal ease-in and ease-out.",
    },
    "logarithmic": {
        "label": "Logarithmic",
        "description": "Rapid initial gain rise tapering smoothly (perceptual loudness).",
    },
    "exponential": {
        "label": "Exponential",
        "description": "Gradual initial rise accelerating towards boundary.",
    },
}


def get_fade_curve_factors(progress: float, curve: str = "linear") -> float:
    """Calculate gain factor (0.0 to 1.0) given normalized fade progress (0.0 to 1.0)."""
    p = max(0.0, min(1.0, float(progress)))
    c = str(curve or "linear").lower()
    if c == "s_curve":
        return 0.5 * (1.0 - math.cos(p * math.pi))
    elif c == "logarithmic":
        return math.log10(1.0 + 9.0 * p)
    elif c == "exponential":
        return (math.exp(2.0 * p) - 1.0) / (math.exp(2.0) - 1.0)
    return p


class Story:
    """Represents a segmented radio or TV news/broadcast story with boundaries and fade metadata."""

    def __init__(
        self,
        start: float = 0.0,
        end: float = 0.0,
        title: str = "Untitled Story",
        suggestion: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        fade_in: Optional[float] = None,
        fade_out: Optional[float] = None,
        fade_curve: Optional[str] = None,
    ):
        self.start = float(start)
        self.end = float(end)
        self.title = str(title or "Untitled Story")
        self.suggestion = bool(suggestion)
        self.metadata = dict(metadata) if isinstance(metadata, dict) else {}

        if fade_in is not None:
            self.fade_in = max(0.0, float(fade_in))
        else:
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_in = max(0.0, float(settings.value("default_fade_in_duration", 0.0)))
            except Exception:
                self.fade_in = 0.0

        if fade_out is not None:
            self.fade_out = max(0.0, float(fade_out))
        else:
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_out = max(0.0, float(settings.value("default_fade_out_duration", 1.0)))
            except Exception:
                self.fade_out = 1.0

        if fade_curve is not None:
            self.fade_curve = str(fade_curve)
        else:
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                self.fade_curve = str(settings.value("default_fade_curve", "linear") or "linear")
            except Exception:
                self.fade_curve = "linear"

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "start": self.start,
            "end": self.end,
            "title": self.title,
            "suggestion": self.suggestion,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "fade_curve": getattr(self, "fade_curve", "linear"),
        }
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Story":
        known = {"start", "end", "title", "suggestion", "metadata", "fade_in", "fade_out", "fade_curve"}
        meta = dict(data.get("metadata", {})) if isinstance(data.get("metadata"), dict) else {}
        for k, v in data.items():
            if k not in known:
                meta[k] = v
        return cls(
            start=float(data.get("start", 0.0)),
            end=float(data.get("end", 0.0)),
            title=str(data.get("title", "Untitled Story")),
            suggestion=bool(data.get("suggestion", False)),
            metadata=meta,
            fade_in=data.get("fade_in"),
            fade_out=data.get("fade_out"),
            fade_curve=data.get("fade_curve"),
        )

    def __repr__(self) -> str:
        return f"<Story '{self.title}' [{self.start:.2f}s - {self.end:.2f}s] dur={self.duration:.2f}s>"


def validate_story_boundaries(start: float, end: float, media_duration: Optional[float] = None) -> Tuple[float, float]:
    """Clamp and ensure start < end within [0.0, media_duration]."""
    s = max(0.0, float(start))
    e = max(s + 0.05, float(end))
    if media_duration is not None and media_duration > 0.0:
        s = min(s, media_duration)
        e = min(e, media_duration)
        if s >= e:
            s = max(0.0, e - 0.05)
    return s, e


def check_story_overlap(stories: List[Story]) -> List[Tuple[int, int]]:
    """Return pairs of story indices that temporally overlap."""
    overlaps: List[Tuple[int, int]] = []
    n = len(stories)
    for i in range(n):
        s1 = stories[i]
        for j in range(i + 1, n):
            s2 = stories[j]
            if max(s1.start, s2.start) < min(s1.end, s2.end):
                overlaps.append((i, j))
    return overlaps


class SetStoriesCommand(QUndoCommand):
    """Undo/redo command for wholesale updates to the project's story list."""

    def __init__(self, main_window: Any, old_stories: List[Story], new_stories: List[Story], description: str = "Modify Stories"):
        super().__init__(description)
        self.main_window = main_window
        self.old_stories = [Story.from_dict(s.to_dict()) for s in old_stories]
        self.new_stories = [Story.from_dict(s.to_dict()) for s in new_stories]

    def undo(self):
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.old_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if hasattr(self.main_window, "save_project"):
            self.main_window.save_project()

    def redo(self):
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.new_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if hasattr(self.main_window, "save_project"):
            self.main_window.save_project()


class StoryBoundaryChangeCommand(QUndoCommand):
    """Discrete undo/redo command for story boundary adjustments (start/end times)."""

    def __init__(self, main_window: Any, story_index: int, old_start: float, old_end: float, new_start: float, new_end: float, description: str = "Adjust Story Boundary"):
        super().__init__(description)
        self.main_window = main_window
        self.story_index = story_index
        self.old_start = round(float(old_start), 3)
        self.old_end = round(float(old_end), 3)
        self.new_start = round(float(new_start), 3)
        self.new_end = round(float(new_end), 3)

    def undo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.old_start
            self.main_window.stories[self.story_index].end = self.old_end
            self._sync_ui(self.old_start, self.old_end)

    def redo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.new_start
            self.main_window.stories[self.story_index].end = self.new_end
            self._sync_ui(self.new_start, self.new_end)

    def _sync_ui(self, start: float, end: float):
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if getattr(self.main_window, "current_selected_story_indices", []) == [self.story_index]:
            if hasattr(self.main_window, "start_input"):
                self.main_window.start_input.setText(format_time(start))
            if hasattr(self.main_window, "end_input"):
                self.main_window.end_input.setText(format_time(end))
        if hasattr(self.main_window, "mark_project_dirty"):
            self.main_window.mark_project_dirty(self.text())
        if hasattr(self.main_window, "save_project"):
            self.main_window.save_project()


class SelectStoriesCommand(QUndoCommand):
    """Undo/redo command for active story selection index changes."""

    def __init__(self, main_window: Any, old_selection: List[int], new_selection: List[int], description: str = "Change Story Selection"):
        super().__init__(description)
        self.main_window = main_window
        self.old_selection = list(old_selection)
        self.new_selection = list(new_selection)

    def undo(self):
        if hasattr(self.main_window, "apply_story_selection_indices"):
            self.main_window.apply_story_selection_indices(self.old_selection)

    def redo(self):
        if hasattr(self.main_window, "apply_story_selection_indices"):
            self.main_window.apply_story_selection_indices(self.new_selection)

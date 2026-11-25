"""Diagnostic editor and find-replace test bench facade."""
from __future__ import annotations

from diagnostics.editor_guides_and_daw_tests import DiagnosticEditorGuidesAndDawTestsMixin
from diagnostics.editor_story_ui_tests import DiagnosticEditorStoryUiTestsMixin


class DiagnosticEditorTestsMixin(
    DiagnosticEditorGuidesAndDawTestsMixin,
    DiagnosticEditorStoryUiTestsMixin,
):
    """Backward-compatible facade for editor, guides, and REAPER DAW diagnostic tests."""


__all__ = [
    "DiagnosticEditorTestsMixin",
    "DiagnosticEditorGuidesAndDawTestsMixin",
    "DiagnosticEditorStoryUiTestsMixin",
]

"""shortcuts package — Modular Keyboard Shortcuts Management Subsystem."""
from __future__ import annotations

from shortcuts.schema import (
    ShortcutDef,
    SHORTCUT_DEFINITIONS,
    get_platform_default,
    format_sequence_display,
    normalize_sequence_string,
    _get_shortcuts_theme_mode,
)
from shortcuts.manager import ShortcutsManager
from shortcuts.widgets import KeySequenceRecorderEdit
from shortcuts.dialogs import KeyboardShortcutsPage

__all__ = [
    "ShortcutDef",
    "SHORTCUT_DEFINITIONS",
    "get_platform_default",
    "format_sequence_display",
    "normalize_sequence_string",
    "_get_shortcuts_theme_mode",
    "ShortcutsManager",
    "KeySequenceRecorderEdit",
    "KeyboardShortcutsPage",
]

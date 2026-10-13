"""shortcuts/definitions.py — Shortcut definitions and schema re-exports for keyboard shortcut management."""
from __future__ import annotations

from shortcuts.schema import (
    ShortcutDef,
    SHORTCUT_DEFINITIONS,
    ACTION_ALIASES,
    get_platform_default,
    format_sequence_display,
    normalize_sequence_string,
    _get_shortcuts_theme_mode,
)

__all__ = [
    "ShortcutDef",
    "SHORTCUT_DEFINITIONS",
    "ACTION_ALIASES",
    "get_platform_default",
    "format_sequence_display",
    "normalize_sequence_string",
    "_get_shortcuts_theme_mode",
]

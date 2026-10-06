"""shortcuts/manager.py — Core ShortcutsManager coordinator and QSettings integration."""
from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QKeySequence

from shortcuts.schema import (
    SHORTCUT_DEFINITIONS,
    ShortcutDef,
    format_sequence_display,
    get_platform_default,
    normalize_sequence_string,
)


class ShortcutsManager(QObject):
    """Central repository and coordinator for all configurable application shortcuts."""

    shortcutsChanged = Signal()

    def __init__(self, settings_store: Optional[QSettings] = None):
        super().__init__()
        if settings_store is None:
            settings_store = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
        self.settings_store = settings_store
        self._overrides: Dict[str, str] = {}
        self.load()

    def load(self):
        """Read customized shortcut overrides from QSettings."""
        self._overrides.clear()
        try:
            self.settings_store.beginGroup("keyboard_shortcuts")
            for defn in SHORTCUT_DEFINITIONS:
                val = self.settings_store.value(defn.action_id, None)
                if val is not None and str(val).strip() != "":
                    self._overrides[defn.action_id] = str(val).strip()
            self.settings_store.endGroup()
        except Exception as exc:
            print(f"[SHORTCUTS] Error loading shortcut settings: {exc}")

    def get_definitions(self) -> List[ShortcutDef]:
        return SHORTCUT_DEFINITIONS

    def get_definition(self, action_id: str) -> Optional[ShortcutDef]:
        for defn in SHORTCUT_DEFINITIONS:
            if defn.action_id == action_id:
                return defn
        return None

    def get_default_shortcut(self, action_id: str) -> str:
        defn = self.get_definition(action_id)
        if defn:
            return get_platform_default(defn)
        return ""

    def get_current_shortcut(self, action_id: str) -> str:
        if action_id in self._overrides:
            return self._overrides[action_id]
        return self.get_default_shortcut(action_id)

    def is_customized(self, action_id: str) -> bool:
        if action_id not in self._overrides:
            return False
        default_seq = normalize_sequence_string(self.get_default_shortcut(action_id))
        cur_seq = normalize_sequence_string(self._overrides[action_id])
        return cur_seq != default_seq

    def set_shortcut(self, action_id: str, new_seq: str):
        """Set a shortcut override for action_id. Passing empty string or None sets to None."""
        if not new_seq or new_seq.strip() in ("", "None", "<none>"):
            self._overrides[action_id] = "None"
            return

        normalized = normalize_sequence_string(new_seq)
        default_seq = normalize_sequence_string(self.get_default_shortcut(action_id))
        if normalized == default_seq:
            if action_id in self._overrides:
                del self._overrides[action_id]
        else:
            self._overrides[action_id] = normalized

    def reset_shortcut(self, action_id: str):
        """Reset a single shortcut back to its platform default."""
        if action_id in self._overrides:
            del self._overrides[action_id]

    def reset_all(self):
        """Reset all shortcuts back to application defaults."""
        self._overrides.clear()

    def save(self):
        """Persist all overrides to QSettings and emit notification signal."""
        try:
            self.settings_store.beginGroup("keyboard_shortcuts")
            self.settings_store.remove("")  # remove existing keys in group
            for act_id, seq_str in self._overrides.items():
                self.settings_store.setValue(act_id, seq_str)
            self.settings_store.endGroup()
            self.settings_store.sync()
        except Exception as exc:
            print(f"[SHORTCUTS] Error saving shortcut settings: {exc}")
        self.shortcutsChanged.emit()

    def find_conflict(self, candidate_seq: str, excluding_action_id: str = "") -> Optional[ShortcutDef]:
        """Check if candidate_seq is already bound to another action."""
        if not candidate_seq or candidate_seq.strip() in ("", "None", "<none>"):
            return None
        norm_candidate = normalize_sequence_string(candidate_seq).lower()
        if not norm_candidate:
            return None

        for defn in SHORTCUT_DEFINITIONS:
            if defn.action_id == excluding_action_id:
                continue
            cur = self.get_current_shortcut(defn.action_id)
            if not cur or cur in ("None", "<none>"):
                continue
            if normalize_sequence_string(cur).lower() == norm_candidate:
                return defn
        return None

    def apply_to_window(self, window):
        """Update shortcuts on all QAction and QShortcut objects on MainWindow,
        configuring ApplicationShortcut context so in-focus app shortcuts reliably override other apps."""
        from prs_shared import platform_seq

        for defn in SHORTCUT_DEFINITIONS:
            cur_seq = self.get_current_shortcut(defn.action_id)
            if not cur_seq or cur_seq == "None":
                qt_seq = QKeySequence()
            else:
                # platform_seq handles Mac Ctrl->Meta translation if not already done
                qt_seq = platform_seq(cur_seq)

            if defn.attr_name and hasattr(window, defn.attr_name):
                target = getattr(window, defn.attr_name)
                if target is not None:
                    try:
                        if defn.is_qshortcut:
                            target.setKey(qt_seq)
                            if hasattr(target, "setContext"):
                                target.setContext(Qt.ShortcutContext.ApplicationShortcut)
                        else:
                            target.setShortcut(qt_seq)
                            if hasattr(target, "setShortcutContext"):
                                target.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
                            if hasattr(window, "addAction") and target not in window.actions():
                                window.addAction(target)
                    except Exception as exc:
                        print(f"[SHORTCUTS] Failed to apply shortcut {cur_seq} to {defn.attr_name}: {exc}")

        # Update toolbar buttons and controls to dynamically display current shortcuts in tooltips
        button_tooltips = {
            "toggle_comments": ("comments_toggle_btn", "Toggle Comments Sidebar & Annotations"),
            "toggle_edit_mode": ("transcript_mode_toggle_btn", "Switch to Text Editing Mode"),
            "transcript_font_up": ("transcript_font_up_btn", "Increase Transcript Font Size"),
            "transcript_font_down": ("transcript_font_down_btn", "Decrease Transcript Font Size"),
            "transcript_font_reset": ("transcript_font_reset_btn", "Reset Transcript Font Size"),
            "fmt_bold": ("fmt_bold_btn", "Bold"),
            "fmt_italic": ("fmt_italic_btn", "Italic"),
            "fmt_underline": ("fmt_underline_btn", "Underline"),
            "fmt_strikethrough": ("fmt_strike_btn", "Strikethrough"),
            "fmt_highlight": ("transcript_highlight_btn", "Highlight Selected Text"),
            "fmt_clear": ("fmt_clear_btn", "Clear Formatting"),
            "split_speaker": ("fmt_split_btn", "Split Speaker Segment at Cursor"),
            "play_pause": ("play_pause_btn", "Play / Pause playback"),
            "set_story_start": ("set_story_start_btn", "Set start time of selected story"),
            "set_story_end": ("set_story_end_btn", "Set end time of selected story"),
            "add_story": ("add_story_btn", "Add story from active selection"),
            "export_stories": ("export_stories_btn", "Unified Export"),
        }

        for action_id, (attr_name, base_text) in button_tooltips.items():
            if hasattr(window, attr_name):
                btn = getattr(window, attr_name)
                if btn is not None:
                    seq_str = self.get_current_shortcut(action_id)
                    if seq_str and seq_str not in ("None", "<none>"):
                        disp_str = format_sequence_display(seq_str)
                        btn.setToolTip(f"{base_text} ({disp_str})")
                    else:
                        btn.setToolTip(base_text)

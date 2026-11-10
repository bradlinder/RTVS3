# transcript_context_menu_mixin.pyi — Typing and Interface Stub for transcript_context_menu_mixin
from __future__ import annotations
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from reaper_bridge import build_reaper_cue_payload, attach_reaper_cue_to_mimedata, write_reaper_sidecar_cue
from transcript_styles import clean_dark_mode_clipboard_html

class TranscriptContextMenuMixin:

    def _on_bubble_play(self):
        ...

    def _on_bubble_story(self):
        ...

    def _on_bubble_note(self):
        ...

    def _on_bubble_cut(self):
        ...

    def _on_bubble_export(self):
        ...

    def show_context_menu(self, position):
        ...

    def copy_highlighted_selection(self) -> bool:
        ...

    def copy_selection_for_reaper(self) -> bool:
        ...

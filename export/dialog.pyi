# dialog.pyi — Typing and Interface Stub for dialog
from __future__ import annotations
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from prs_shared import INTERNAL_APP_ID, CollapsibleSection, format_time, safe_filename, make_dialog_maximizable
from core_utils import apply_window_titlebar_theme, get_active_theme_mode
from plugin_base import ExportDestination
from export.reorder_dialog import DEFAULT_EXPORT_DESTINATIONS_ORDER, _get_export_theme_mode, get_export_destinations_order, save_export_destinations_order, ReorderExportDestinationsDialog

class UnifiedExportDialog(QDialog):

    def __init__(self, main_window: Any, initial_scope: str=..., initial_dest: Optional[str]=..., parent: Optional[QWidget]=...):
        ...

    def showEvent(self, event):
        ...

    def _build_destinations_layout(self):
        ...

    def _on_reorder_destinations(self):
        ...

    def _create_local_page(self) -> QWidget:
        ...

    def _on_location_radio_toggled(self):
        ...

    def _browse_custom_export_location(self):
        ...

    def _create_timeline_page(self) -> QWidget:
        ...

    def _on_timeline_location_radio_toggled(self):
        ...

    def _browse_custom_timeline_location(self):
        ...

    def _toggle_all_sections(self):
        ...

    def _update_export_button_label(self):
        ...

    def _on_dest_changed(self):
        ...

    def _on_scope_changed(self):
        ...

    def _open_id3_editor(self):
        ...

    def _copy_youtube_chapters(self):
        ...

    def _load_saved_options(self):
        ...

    def save_options_to_settings(self, as_default: bool=...):
        ...

    def _handle_accept(self):
        ...

    def get_result(self) -> Dict[str, Any]:
        ...

    def _persist_plugin_draft_states(self):
        ...

    def done(self, r: int):
        ...

    def toggle_float_mode(self, pinned: Optional[bool]=...):
        ...

    def set_scope_and_destination(self, scope: Optional[str]=..., dest_id: Optional[str]=...):
        ...

    def refresh_from_main_window(self):
        ...

    def _toggle_maximize(self):
        ...

    def changeEvent(self, event):
        ...

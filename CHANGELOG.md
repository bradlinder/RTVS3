# Changelog

## v3.9.76-beta
- **Timeline & Story Context Menu Transient Parent Top-Level Normalization (`timeline_context_menus.py`, `timeline_widgets.py`, `story_widgets.py`)**:
  - **Top-Level Window Parenting for Menus & Tooltips**: Updated `show_timeline_context_menu`, `show_selection_context_menu`, and story list context menus to use `canvas.window()` / `self.window()` as their parent `QWidget` instead of the child timeline canvas or list widget.
  - **Eliminated QWidgetWindow Transient Parent Warning**: Resolved Qt platform warning (`QWidgetWindow(..., name="timeline_widgetWindow") must be a top level window.`) which occurred on Windows when OLE drag-and-drop created a native `HWND` for the child timeline widget, causing Qt's `QWindow::setTransientParent` to warn when context menus or tooltips referenced the child widget instead of the top-level `QMainWindow`.

## v3.9.75-beta
- **Interactive Transcript Offset Sanitization & Out-of-Range Cursor Prevention (`transcript_editor.py`, `story_crud_mixin.py`, `transcript_timeline_sync_mixin.py`, `transcript_selection_mixin.py`, `transcript_playback_highlight_mixin.py`, `transcript_navigation_mixin.py`)**:
  - **Comprehensive Editor State Reset (`transcript_editor.py`)**: Overrode `InteractiveTranscriptEdit.clear()` to completely purge `char_timestamp_map`, `anchor_ranges`, `time_anchor_index`, `time_anchor_starts`, `timeline_selection_span`, and cached extra selections when clearing documents or loading new media, ensuring stale word character positions from prior projects are eliminated.
  - **Timeline Scrubbing & Selection Bounds Clamping (`story_crud_mixin.py`)**: Added early-exit guards in `handle_timeline_selection_range_changed` when no active transcript exists or when the document character count is <= 1 (empty document). Enforced document length boundary checks (`doc.characterCount()`) to clamp `first_char` and `last_char` within valid ranges, eliminating Qt's `QTextCursor::setPosition: Position out of range` console warnings.
  - **ExtraSelection Cursor Positioning Bounds Guards (`transcript_timeline_sync_mixin.py`, `transcript_selection_mixin.py`, `transcript_playback_highlight_mixin.py`, `transcript_navigation_mixin.py`)**: Wrapped cursor positioning for timeline selection spans, saved selections, and playback word highlights with strict `0 <= pos < doc_len` boundary validation.

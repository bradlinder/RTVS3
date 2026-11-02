# Changelog

## v3.9.57-beta
- **Simultaneous Search Auto-Highlighting & Live Match Counter (`playback_preferences.py`, `transcript_timeline_sync_mixin.py`, `transcript_selection_mixin.py`, `ui_layout.py`, `transcript_editor_dialogs.py`, `theme_qss.py`)**:
  - **Simultaneous Document-Wide Highlighting**: Typing in the transcript search bar (or Find & Replace dialog) immediately highlights every occurrence of the search phrase across the entire transcript using non-destructive `QTextEdit.ExtraSelection` (theme-aware warm amber highlight for inactive matches and vibrant cyan/sky highlight for the active match), providing instant visual density awareness.
  - **Live Match Counter Badge (`X / Y`)**: Added a compact, high-visibility match counter badge (`1 / 14` or `0 / 0`) directly beside the transcript search bar and inside the Find & Replace dialog that dynamically updates as you type or cycle through matches.
  - **Bidirectional 'Find Prev' and 'Find Next' Controls**: Added paired 'Find Prev' and 'Find Next' buttons directly in the transcript search bar and Find & Replace dialog for rapid one-click mouse navigation alongside `Enter` / `Shift+Enter` and `Ctrl+G` / `Ctrl+Shift+G`.
  - **Seamless Real-Time Synchronization**: Search highlights and match counters automatically synchronize bidirectionally between the transcript search bar, transcript editor, and Find & Replace dialog.

## v3.9.56-beta
- **Find & Replace Dialog In-Focus Shortcut Interception (	ranscript_editor_dialogs.py, playback_preferences.py)**:
  - Fixed Ctrl+G and Ctrl+Shift+G not triggering while focus is inside the Find & Replace dialog (including ind_input, 
eplace_input, and child controls). Replaced problematic modeless QShortcut instances with direct keyPressEvent interception across ind_input, 
eplace_input, and FindReplaceDialog, circumventing Qt's ambiguous shortcut suppression with the main window's application action.
  - Added full keyboard navigation within the Find dialog: Enter executes Find Next, Shift+Enter executes Find Previous, and Ctrl+F refocuses and selects the search query.
  - Resolved backward search active selection loop: in both FindReplaceDialog.find_prev and 	rigger_find_prev, repositioned cursor to the start of the current selection before querying backward, preventing the search from repeatedly re-matching the active word.
  - Added guaranteed ensureCursorVisible() and status bar feedback on every dialog search pass.

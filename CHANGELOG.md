# Changelog

## v3.9.56-beta
- **Find & Replace Dialog In-Focus Shortcut Interception (	ranscript_editor_dialogs.py, playback_preferences.py)**:
  - Fixed Ctrl+G and Ctrl+Shift+G not triggering while focus is inside the Find & Replace dialog (including ind_input, 
eplace_input, and child controls). Replaced problematic modeless QShortcut instances with direct keyPressEvent interception across ind_input, 
eplace_input, and FindReplaceDialog, circumventing Qt's ambiguous shortcut suppression with the main window's application action.
  - Added full keyboard navigation within the Find dialog: Enter executes Find Next, Shift+Enter executes Find Previous, and Ctrl+F refocuses and selects the search query.
  - Resolved backward search active selection loop: in both FindReplaceDialog.find_prev and 	rigger_find_prev, repositioned cursor to the start of the current selection before querying backward, preventing the search from repeatedly re-matching the active word.
  - Added guaranteed ensureCursorVisible() and status bar feedback on every dialog search pass.

## v3.9.55-beta
- **Inline Transcript Search & Find/Replace Synchronization (playback_preferences.py, ui_layout.py, ui_dialog_launchers.py, 	ranscript_editor_dialogs.py, ui_menus.py, shortcuts/schema.py, shortcuts/manager.py, RadioTVSegmenter.py)**:
  - **Inline Search Navigation**: Pressing Enter or clicking Find Next in the transcript search box now executes an inline search cycling through matches directly in the transcript view with automatic wrap-around and status bar feedback, without popping open the modal dialog.
  - **Backward Search Support**: Pressing Shift+Enter in the transcript search box executes an inline Find Previous search backward through the transcript.
  - **Modern Standard Keyboard Shortcuts (Ctrl+G / Ctrl+Shift+G)**: Standardized Find Next to Ctrl+G (Cmd+G on macOS) and Find Previous to Ctrl+Shift+G (Cmd+Shift+G on macOS) across both the main window and the Find & Replace dialog, eliminating non-functional legacy F3/Shift+F3 key conflicts caused by ambiguous QShortcut/QAction overloads.
  - **Conflict-Free Shortcut Migration**: Reassigned Glossary & Custom Vocabulary to Ctrl+Alt+V (Cmd+Alt+V on macOS), resolving the shortcut collision with Find Previous. Added automatic legacy shortcut migration in ShortcutsManager to seamlessly transition existing preferences.
  - **Two-Way Search Term Synchronization**: Ctrl+F (or Edit > Find and Replace...) now automatically pre-populates the Find & Replace dialog with whatever term is entered in the transcript search box (or active transcript text selection) and selects the text for immediate editing. Finding next/previous in the dialog updates the transcript search box in real time.

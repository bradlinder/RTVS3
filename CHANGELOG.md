# Changelog

## v3.9.55-beta
- **Inline Transcript Search & Find/Replace Synchronization (playback_preferences.py, ui_layout.py, ui_dialog_launchers.py, 	ranscript_editor_dialogs.py, ui_menus.py, shortcuts/schema.py, shortcuts/manager.py, RadioTVSegmenter.py)**:
  - **Inline Search Navigation**: Pressing Enter or clicking Find Next in the transcript search box now executes an inline search cycling through matches directly in the transcript view with automatic wrap-around and status bar feedback, without popping open the modal dialog.
  - **Backward Search Support**: Pressing Shift+Enter in the transcript search box executes an inline Find Previous search backward through the transcript.
  - **Modern Standard Keyboard Shortcuts (Ctrl+G / Ctrl+Shift+G)**: Standardized Find Next to Ctrl+G (Cmd+G on macOS) and Find Previous to Ctrl+Shift+G (Cmd+Shift+G on macOS) across both the main window and the Find & Replace dialog, eliminating non-functional legacy F3/Shift+F3 key conflicts caused by ambiguous QShortcut/QAction overloads.
  - **Conflict-Free Shortcut Migration**: Reassigned Glossary & Custom Vocabulary to Ctrl+Alt+V (Cmd+Alt+V on macOS), resolving the shortcut collision with Find Previous. Added automatic legacy shortcut migration in ShortcutsManager to seamlessly transition existing preferences.
  - **Two-Way Search Term Synchronization**: Ctrl+F (or Edit > Find and Replace...) now automatically pre-populates the Find & Replace dialog with whatever term is entered in the transcript search box (or active transcript text selection) and selects the text for immediate editing. Finding next/previous in the dialog updates the transcript search box in real time.

## v3.9.54-beta
- **Interactive Transcript Threshold Auto-Scroll & Dual Settings Toggles (	ranscript_timeline_sync_mixin.py, 	ranscript_editor.py, playback_controller.py, ui_menus.py, preferences_tabs_media.py, preferences_dialog.py, RadioTVSegmenter.py)**:
  - Implemented intelligent threshold-based auto-scrolling in InteractiveTranscriptEdit: when playback approaches the bottom ~18% of the visible viewport or moves off-screen, the view smoothly scrolls to position the active spoken line at the upper third (~25%) of the screen, providing ample forward reading space without continuous word-by-word micro-jitter.
  - Added user interaction safety guards: auto-scroll is safely suppressed during text editing mode (Ctrl+E), active text selection drags, and manual scrolling (mouse wheel or scrollbar drag temporarily disengages auto-scroll until seeking, toggling playback, or clicking a transcript link).
  - Added user-configurable toggle in **View > Transcript > Auto-Scroll During Playback** and in **Preferences > Playback & Timeline > Transcript Playback Scroll** (default: enabled), persisted in QSettings.

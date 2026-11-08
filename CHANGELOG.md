# Changelog

## v3.9.88-beta
- **Searchable/Sortable Glossary Dialog, Contextual Terminology Engine & Alternate Spelling Mapping (glossary_dialog.py, media_batch.py, 	erminology.py, 	ranscript_context_menu_mixin.py)**:
  - **Modular Glossary Dialog (glossary_dialog.py)**: Extracted custom vocabulary/glossary interface into a dedicated UI module with real-time text filtering (setRowHidden), 6-way sorting (A-Z, Z-A, protected terms first, case-sensitive first), and 4-column data model (Match case).
  - **Alternate Spelling Workflows (	erminology.py, 	ranscript_context_menu_mixin.py)**: Multi-variant source terms accept comma-separated spellings (e.g., Kimberlei Davis, Kimberley Davis, Kimberly Davis -> Kimberlei Davis). Right-clicking a word in the transcript offers *Add Selected Text as Alternate Spelling For...* with live normalization and full Undo/Redo tracking.
  - **Two-Pass Contextual & Phonetic Co-Reference Resolution (	erminology.py)**: Multi-word proper names correctly resolve across timed tokens and project-scoped single-word co-references (e.g. standalone Kimberley -> Kimberlei), guarded against false-positive rewrites when another surname (such as Kimberley Johnson) is present.
- **Story Selection Transcript Highlighting & Smart Copy (	ranscript_editor.py, 	imeline_context_menus.py, 	ranscript_context_menu_mixin.py)**:
  - **Synchronized Transcript Overlays**: Selecting stories on the timeline, sidebar, or via audition highlights the story character span in the transcript view.
  - **Smart Copy & Universal Esc Deselection**: Pressing Ctrl+C with a story selection active copies the clean story transcript to clipboard. Pressing Esc clears active selections across all widgets.
  - **Timeline Context Menu Parity**: Right-clicking a story on the timeline auto-selects it and provides *Audition Story Playback*, *Story & Post Metadata...*, and *Export Selected Stories...*.
- **Diagnostic Test Bench Thread Safety, Windows Clipboard & Teardown Hardening (diagnostic_dialog.py, diagnostic_editor_tests.py, 	ranscript_editor.py)**:
  - **Main-Thread Dispatch for UI Widget Diagnostics**: Routed all GUI dialog and widget tests to the Qt main thread via BlockingQueuedConnection, completely eliminating secondary-thread QBasicTimer::stop crashes, widget deadlocks, and post-run garbage collection faults.
  - **Windows OLE Clipboard Guard**: Guarded OS clipboard writes with QThread.currentThread() == app.thread() to eliminate OleSetClipboard: COM error 0x800401f0 on background threads.
  - **Test Bench Title Polish**: Replaced design-era artifact titles with clean domain-accurate names (UI Theme Palettes and Clipboard Rich Text Formatting, Story Highlighting, Smart Copy & Glossary Engine) and implemented backward-compatible dispatch aliasing.

## v3.9.87-beta

- **Seriously Simple Podcasting (Castos) Rich Player Auto-Injection (plugins/wordpress/client.py, plugins/wordpress/castos.py, diagnostic_export_tests.py, plugins/wordpress/manifest.json)**:

  - **Castos V2 Rich Player Auto-Injection (plugins/wordpress/client.py)**: Resolved an issue where exporting a post designated as a Castos Podcast Episode resulted in a simple browser audio bar (\wp-audio-shortcode\ + plain meta links) instead of the rich Castos V2 player widget (with series cover artwork, episode title, dark mode skin, and playback controls).

  - **Legacy \[ss_player]\ Shortcode Elimination**: Removed the hardcoded \[ss_player]\ shortcode block from post content generation for podcast posts. In Seriously Simple Podcasting, \[ss_player]\ explicitly renders the legacy compact audio bar and suppresses SSP's automatic dynamic rich player injection. Omitting manual player shortcodes/blocks when \is_podcast=True\ allows Seriously Simple Podcasting to dynamically inject the rich, branded Castos V2 player at the site's configured player location (*Above content*), matching the October 21 episode layout.

  - **Regression Test Bench Alignment (\diagnostic_export_tests.py\)**: Updated the WordPress export diagnostic test to verify that podcast posts omit both standard \<!-- wp:audio -->\ blocks and legacy \[ss_player]\ shortcodes, guaranteeing uninterrupted rich Castos player rendering.

  - **Plugin Version Synchronization (\plugins/wordpress/manifest.json\)**: Synchronized the WordPress plugin manifest version to .9.87-beta\ in compliance with lazy catch-up policy.

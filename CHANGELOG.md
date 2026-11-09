# Changelog

## v3.9.89-beta (In Progress)
- **Story Duration Visibility & Selection Indicators — Phase 1 (core_utils.py, prs_shared.py, story_crud_mixin.py, processing.py, media_batch.py, ui_layout.py, diagnostic_editor_tests.py)**:
  - **Sidebar Story Duration Subtitle (1.1)**: Display story length in clock format (e.g. `[02:30.5]` or `00:02:30`) on a dedicated second subtitle line below the time range in the Stories sidebar list (`story_crud_mixin.py`, `ui_layout.py`). Expanded list item row height and container min/max bounds to prevent vertical clipping on compact viewports.
  - **Multi-Selection Total Duration Header Counter (1.4)**: Real-time aggregate duration readout in the Stories sidebar header (`stories_header`) reflecting current single- or multi-story selection (`Stories (1) — [02:30.5]`, `Stories (3) — [07:14.2]`). Supports music terminology (`Songs`) and Spanish localization (`Historias`, `Canciones`).
  - **Duration Formatting & Regression Suite (1.5 Phase 1)**: Added `format_clock_duration(seconds, include_millis)` to `core_utils.py` and automated diagnostic test `Story Duration Visibility & Header Aggregation` in `diagnostic_editor_tests.py`.

## v3.9.88-beta
- **Searchable/Sortable Glossary Dialog, Contextual Terminology Engine & Alternate Spelling Mapping (glossary_dialog.py, media_batch.py, terminology.py, transcript_context_menu_mixin.py)**:
  - **Modular Glossary Dialog (glossary_dialog.py)**: Extracted custom vocabulary/glossary interface into a dedicated UI module with real-time text filtering (setRowHidden), 6-way sorting (A-Z, Z-A, protected terms first, case-sensitive first), and 4-column data model (Match case).
  - **Alternate Spelling Workflows (terminology.py, transcript_context_menu_mixin.py)**: Multi-variant source terms accept comma-separated spellings (e.g., Kimberlei Davis, Kimberley Davis, Kimberly Davis -> Kimberlei Davis). Right-clicking a word in the transcript offers *Add Selected Text as Alternate Spelling For...* with live normalization and full Undo/Redo tracking.
  - **Two-Pass Contextual & Phonetic Co-Reference Resolution (terminology.py)**: Multi-word proper names correctly resolve across timed tokens and project-scoped single-word co-references (e.g. standalone Kimberley -> Kimberlei), guarded against false-positive rewrites when another surname (such as Kimberley Johnson) is present.
- **Story Selection Transcript Highlighting & Smart Copy (transcript_editor.py, timeline_context_menus.py, transcript_context_menu_mixin.py)**:
  - **Synchronized Transcript Overlays**: Selecting stories on the timeline, sidebar, or via audition highlights the story character span in the transcript view.
  - **Smart Copy & Universal Esc Deselection**: Pressing Ctrl+C with a story selection active copies the clean story transcript to clipboard. Pressing Esc clears active selections across all widgets.
  - **Timeline Context Menu Parity**: Right-clicking a story on the timeline auto-selects it and provides *Audition Story Playback*, *Story & Post Metadata...*, and *Export Selected Stories...*.
- **Diagnostic Test Bench Thread Safety, Windows Clipboard & Teardown Hardening (diagnostic_dialog.py, diagnostic_editor_tests.py, transcript_editor.py)**:
  - **Main-Thread Dispatch for UI Widget Diagnostics**: Routed all GUI dialog and widget tests to the Qt main thread via BlockingQueuedConnection, completely eliminating secondary-thread QBasicTimer::stop crashes, widget deadlocks, and post-run garbage collection faults.
  - **Windows OLE Clipboard Guard**: Guarded OS clipboard writes with QThread.currentThread() == app.thread() to eliminate OleSetClipboard: COM error 0x800401f0 on background threads.
  - **Test Bench Title Polish**: Replaced design-era artifact titles with clean domain-accurate names and implemented backward-compatible dispatch aliasing.

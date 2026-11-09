# Changelog

## v3.9.89-beta
- **Story Duration Visibility, Edit Form Placement & Timeline Selection Indicators (core_utils.py, prs_shared.py, story_crud_mixin.py, timeline_widgets.py, timeline_snap.py, ui_layout.py, diagnostic_editor_tests.py)**:
  - **Story Edit Form Duration Field (1.1)**: Added a dedicated read-only `Duration:` field (`self.duration_input`) placed directly below `Range:` in the story edit form. Dynamically displays story duration in clock format (`02:30.5`) on single selection, aggregate duration on multi-selection, and clears when unselected (`ui_layout.py`, `story_crud_mixin.py`, `processing.py`).
  - **Single-Line Story List & Audio Fade Badge Polish (1.1)**: Maintained clean single-line story list items without vertical clutter, and updated fade badge language from cryptic abbreviations (`[Out:1.0s]`) to explicit wording (`[Fade In: 0.5s | Fade Out: 1.0s]`).
  - **Timeline Story Body Hover Readout (1.2)**: Hovering over the main body of a story block on the waveform canvas displays a clean tooltip and status bar readout showing Story Title, time range, and clock duration (`timeline_widgets.py`, `timeline_snap.py`).
  - **Live Selection Drag & Hover Duration Indicator (1.3)**: Real-time duration clock readout in tooltip and status bar while drawing or resizing selection regions, or dragging story boundary handles on the timeline.
  - **Multi-Selection Total Duration Header Counter (1.4)**: Real-time aggregate duration readout in the Stories sidebar header (`stories_header`) reflecting current single- or multi-story selection (`Stories (1) — [02:30.5]`, `Stories (3) — [07:14.2]`). Supports music terminology (`Songs`) and Spanish localization (`Historias`, `Canciones`).
  - **Diagnostic Regression Suite (1.5)**: Automated unit and headless assertions for duration string formatting, edit form field updates, single-line list rendering, timeline hover tooltips, and live drag indicators in `diagnostic_editor_tests.py`.

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

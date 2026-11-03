# Changelog

## v3.9.71-beta
- **Find & Replace Data-Model Synchronization & Speaker Re-render Immunity (`transcript_editor_dialogs.py`, `ui_dialog_launchers.py`, `diagnostic_editor_tests.py`)**:
  - **Eliminated Find & Replace Speaker Reversion**: Resolved an architectural defect where Find & Replace previously performed direct in-place modifications only in the `QTextEdit` presentation buffer without mutating the underlying project data model (`transcript["segments"]`, `words`, and `speaker_names`). Because the data model was left unchanged, any subsequent speaker label modification or speaker manager action called `render_transcript()`, instantly re-rendering the view from the unedited data model and reverting all corrected names back to the previous misspellings.
  - **Data-Model Backed Replacements**: Find & Replace now directly mutates `transcript["segments"]`, synchronizes word-level alignment and timestamps via `sync_segment_words()`, updates full transcript text, and synchronizes active translations.
  - **Speaker Alias & Glossary Synchronization**: Added an "Include Speakers" option (enabled by default) that updates matching display aliases in `speaker_names` and `custom_speakers_glossary`, ensuring speaker headers and spoken dialogue stay synchronized.
  - **Project State Undo/Redo & Persistence**: Every Find & Replace operation now captures before/after project states, records clean undo commands on `undo_stack`, marks the project dirty, triggers `render_transcript()` with scroll position preservation, and persists changes.
  - **Shortcut & Context Menu Unification**: Added `open_find_replace` alias in `UiDialogLaunchersMixin` to seamlessly handle both `open_find_replace()` and `open_find_dialog()` invocations from editor shortcuts and context menus.
  - **Automated Diagnostic Suite (`diagnostic_editor_tests.py`)**: Added end-to-end automated test `Find and Replace Project Synchronization and Undo` verifying data-model mutations, word alignment synchronization, speaker change survival, and undo/redo integrity.

## v3.9.70-beta
- **Version Source-of-Truth Harmonization & Updater Dialog Desync Resolution (`core_utils.py`, `updater.py`, `prs_shared.py`, `RadioTVSegmenter.py`)**:
  - **Resolution of Core Version Desync**: Harmonized `PROJECT_VERSION` across `core_utils.py`, `prs_shared.py`, `RadioTVSegmenter.py`, and `backup_manager.py` to `3.9.70-beta`, eliminating the desync where `updater.py` read an outdated version from `core_utils.py` while the main window title read from `prs_shared.py`.
  - **Updater Dual-Check Version Binding (`updater.py`)**: Bound `updater.py`'s `PROJECT_VERSION` to synchronize with `prs_shared.PROJECT_VERSION` at module import time, preventing future version drift across decoupled packages.
  - **Checklist & Verification Alignment (`AGENTS.md`, `bump_version.py`)**: Updated project release checklists and automated tooling to verify synchronization across all 13 canonical version entrypoints.

# Changelog

## v3.10.8-beta
- **Main Menu Bar Deduplication, Qt Ampersand Escaping & Polish (`ui_menus.py`, `theme_preferences.py`, `shortcuts/schema.py`, `diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
  - **Menu Deduplication & Cleaner Ownership (`ui_menus.py`)**:
    - Kept `Backup && Restore Settings...` exclusively under **Settings** (removing the misleading `Backup & Restore...` duplicate from **File**, while keeping `self.backup_restore_action` aliased).
    - Kept `Batch Processing...` and `Clear Temporary Cache...` exclusively under **Tools** (removing duplicates from **File** and **Settings**).
    - Kept `Manage AI Models...` exclusively under **Settings** (removing the duplicate from **Tools**).
    - Kept `Comments Sidebar Panel` exclusively in top-level **View** and `Show Comment Highlights` exclusively in **View → Transcript** (with compatibility aliases preserved).
    - Moved `Check for Updates...` from **Settings** to **Help** directly above `About Radio & TV Segmenter`.
  - **Qt Ampersand Escaping & State Polish (`ui_menus.py`, `theme_preferences.py`, `shortcuts/schema.py`)**:
    - Fixed all 6 single-ampersand menu labels (`Publishing && Plugins`, `Glossary && Custom Vocabulary...`, `Backup && Restore Settings...`, `User Guides && Documentation...`, `About Radio && TV Segmenter`, and `Run Feature && Performance Benchmark...`) so `&` characters render cleanly.
    - Made **View → Theme** (*Dark* / *Light* / *High Contrast*) exclusive checkable radio actions synchronized with active settings and `ThemePreferencesMixin.set_theme()`.
    - Aligned initial menu labels (`&Segments Panel`, `&Detect Segments...`) with `get_story_vocabulary()` and updated `shortcuts/schema.py` metadata for `backup_restore`.
  - **Regression Coverage (`diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
    - Added `Menu Bar Deduplication and Escaping Integrity` validating zero duplicate `QAction` instances, zero unescaped ` & ` labels, single-menu ownership, checkable theme actions, alias preservation, and shortcut schema sync.

## v3.10.7-beta
- **Milestone 3.1 & 3.3 Modularization: Retire Orphaned `plugin_dialogs.py` & Extract `AudioLoudnessProbeWorker` (`audio_normalization.py`, `audio_normalization_worker.py`, `prs_shared.py`, `scripts/modular_audit.py`, `diagnostic_loudness_tests.py`)**:
  - **Retire Dead Legacy Module (`plugin_dialogs.py`, `scripts/modular_audit.py`)**:
    - Deleted obsolete `plugin_dialogs.py` (`447` lines), which had zero callers and was superseded by `plugins/installer_workers.py`, `plugins/github_dialog.py`, and `plugins/manager_dialog.py`.
  - **100% Qt-Free Loudness Engine & Worker Extraction (`audio_normalization.py`, `audio_normalization_worker.py`, `prs_shared.py`, `scripts/modular_audit.py`)**:
    - Extracted `AudioLoudnessProbeWorker` and its `PySide6.QtCore` import block verbatim into dedicated `audio_normalization_worker.py`.
    - Updated `prs_shared.py` to import `AudioLoudnessProbeWorker` directly from `audio_normalization_worker` for static PyInstaller tracing, added a lazy `__getattr__` backward-compatibility shim in `audio_normalization.py` (now 100% Qt-free), and removed both `plugin_dialogs.py` and `audio_normalization.py` from `GRANDFATHERED_LEGACY_MODULES` (`7 -> 5` legacy exemptions).
  - **Regression Coverage (`diagnostic_loudness_tests.py`)**:
    - Extended `_test_smart_hybrid_audio_loudness_probing` with AST zero-`PySide6` verification on `audio_normalization.py` and identity checks for `AudioLoudnessProbeWorker` via both `audio_normalization` and `prs_shared`.

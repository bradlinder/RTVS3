# Changelog

## v3.10.9-beta
- **Keyboard Shortcuts Collision/Wiring Fixes, Dynamic Help Guide & Full Documentation Sync (`ui_layout.py`, `shortcuts/schema.py`, `shortcuts/manager.py`, `playback_controller.py`, `transcript_editor.py`, `transcript_context_menu_mixin.py`, `user_guide_dialog.py`, `ui_dialog_launchers.py`, `translation.py`, `backup_manager.py`, `docs/guides/*.md`, `embedded_guides.py`, `docs/README.md`, `README.md`, `ARCHITECTURE.md`, `BUILD_INSTRUCTIONS.txt`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **Keyboard Shortcut Collision & Wiring Fixes (`ui_layout.py`, `shortcuts/schema.py`, `shortcuts/manager.py`, `playback_controller.py`, `transcript_editor.py`, `transcript_context_menu_mixin.py`)**:
    - Resolved `Ctrl+K` collision between **Strikethrough Text** and **Split Block at Playhead** by reassigning `fmt_strike_action` to `Alt+Shift+5`.
    - Fixed `playback_controller.py` to query `delete_selected_story` (and added `"delete_story"` alias), wired `transcript_editor.py` and `transcript_context_menu_mixin.py` to honor user-customized `copy_selection_as_audio_clip` bindings, and added `customize_shortcuts` (`F8`), `copy_text` (`Ctrl+C`), `fmt_strikethrough` (`Alt+Shift+5`), `fmt_highlight` (`Ctrl+Shift+H`), and `user_guides` (`Shift+F2`) to `SHORTCUT_DEFINITIONS` while updating stale `Stories` schema descriptions.
  - **Dynamic Shortcuts Tab & Stale Prompt Fixes (`user_guide_dialog.py`, `ui_dialog_launchers.py`, `translation.py`, `backup_manager.py`)**:
    - Replaced the hardcoded 26-row fallback in `UserGuideDialog._build_dynamic_shortcuts_guide()` with a live generator reading `SHORTCUT_DEFINITIONS` and active user shortcuts.
    - Updated plugin-disabled prompts in `ui_dialog_launchers.py` and `translation.py` to point to `Tools > Manage Plugins & Add-ons...`, and cleaned up the `backup_manager.py` docstring.
  - **User Guides, Embedded Fallbacks & Repo Docs Sync (`docs/guides/*.md`, `embedded_guides.py`, `docs/README.md`, `README.md`, `ARCHITECTURE.md`, `BUILD_INSTRUCTIONS.txt`)**:
    - Fixed wrong shortcuts (`Ctrl+E` → `F2`, `Ctrl+,` → `Ctrl+P`, `Ctrl+Alt+S` Speaker Manager) and moved menu paths across all 6 guides and `embedded_guides.py`, replaced removed Google Drive / OAuth YouTube / nonexistent Markdown & CMX 3600 claims with current Zero-Auth YouTube, PublishPress Authors, Offline Spellcheck, Voice Profile Tools, and Loudness Normalization workflows, and rebuilt `README.md` shortcuts directly from `shortcuts/schema.py`.
  - **Regression Coverage (`diagnostic_speaker_cleanup_tests.py`)**:
    - Extended `_test_menu_bar_deduplication_and_escaping_integrity` to enforce zero shortcut collisions, complete `SHORTCUT_DEFINITIONS` menu coverage, dynamic shortcuts guide output, and 1:1 `embedded_guides.py` ↔ `docs/guides/*.md` synchronization.

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

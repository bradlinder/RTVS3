# Changelog

## v3.10.10-beta
- **Diagnostic Parity Fixes: Embedded Guide Key, Action Button Polish & Story Fade Test Isolation (`embedded_guides.py`, `speaker_profiles_dialog.py`, `diagnostic_editor_tests.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **Fix `video_shows` Embedded Guide Lookup (`embedded_guides.py`, `diagnostic_speaker_cleanup_tests.py`)**:
    - Renamed `EMBEDDED_GUIDES["video_youtube"]` back to `"video_shows"` so frozen builds resolve *Video Shows & YouTube Publishing* properly and synced the key in `diagnostic_speaker_cleanup_tests.py`.
  - **Live-Theme QSS Polish Timing (`speaker_profiles_dialog.py`)**:
    - Attached `action_w` to column `4` via `setCellWidget()` and called `ensurePolished()` on each action button and wrapper before reading `sizeHint()` / enforcing `setMinimumWidth()`, eliminating the 2px live-stylesheet measurement drift (`63 < 65`).
  - **Test Isolation (`diagnostic_editor_tests.py`)**:
    - Patched `QSettings` around the disabled-fades `Story(...)` check in `_test_story_duration_visibility_and_header_aggregation` so real user Preferences never trigger a false failure.

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

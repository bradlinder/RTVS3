# Changelog

## v3.9.99-beta
- **UX Responsiveness, Timeline Right-Click Dead Zones & Floating Toolbar Fixes (`transcript_timeline_sync_mixin.py`, `timeline_widgets.py`, `background_workers.py`, `project_lifecycle.py`, `plugins/wordpress/wp_tab_widget.py`, `translation.py`, `diagnostic_editor_tests.py`, `diagnostic_export_tests.py`)**:
  - **Floating Selection Toolbar Guard & Positioning (`transcript_timeline_sync_mixin.py`)**:
    - Enforced the `show_floating_selection_toolbar` preference and `not is_editing_mode` guard inside `TranscriptTimelineSyncMixin._on_selection_completed()` (previously only enforced in an unimported legacy mixin), and positioned `selection_bubble` using viewport-local coordinates instead of global screen coordinates.
  - **Timeline Right-Click Dead Zones & Drag Hysteresis (`timeline_widgets.py`)**:
    - Guarded fade handle hit-testing to left mouse clicks so right-clicking near fade handles opens the timeline context menu immediately (including **Adjust Story Fades...**).
    - Added a 5px horizontal right-drag threshold (`_check_right_drag`) before starting range selection or edge drags on right-button press, opening the context menu cleanly on right-button release when clicking near segment edges or with minor cursor jitter.
    - Extracted shared `_handle_media_drag_event()` helper and removed dead left-drag fields.
  - **UI-Thread Save & Keystroke Lag Elimination (`background_workers.py`, `project_lifecycle.py`, `plugins/wordpress/wp_tab_widget.py`, `translation.py`)**:
    - Added a NumPy `tobytes()` fast path (`_pack_f32()`) and `skip_if_exists=True` valid cache check in `write_waveform_peak_cache()` so `save_project()` and `_write_project_file()` no longer rebuild and `os.fsync()` 360k-peak `.peaks` files synchronously on every auto-save.
    - Gated `refresh_story_list()` inside `WordPressExportTabWidget._sync_post_to_project()` strictly on actual story `title` or `author` changes, and added `log_reason: bool = False` to eliminate per-keystroke story list rebuilds and `[PROJECT] Update WordPress Metadata` log storms.
    - Removed per-lookup `[DEBUG] source_language_code` log spam from `translation.py`.
  - **Regression Verification (`diagnostic_editor_tests.py`, `diagnostic_export_tests.py`)**:
    - Added automated checks covering floating toolbar enable/disable + viewport geometry (`6d`), timeline right-click menus over fade handles, edges, and 2px jitter (`6e`), `skip_if_exists` peak cache preservation (`6f`), and zero `refresh_story_list` / `log_reason` triggers during WordPress caption/alt typing (plus updated `6c` `TimelineCanvas(None)` parentage for real PySide6 compatibility).

## v3.9.98-beta
- **CI Tag-Release Plugin Bundling Fix & Plugin Manager Update Check Hardening (`.github/workflows/build.yml`, `plugins/manager_dialog.py`, `diagnostic_cloud_and_system_tests.py`)**:
  - **GitHub Actions Tag-Push Plugin Bundling (`.github/workflows/build.yml`)**:
    - Fixed all four build jobs (`build-plugins`, `build-windows`, `build-macos`, `build-linux`) where `BUILD_PLUGIN_*` environment variables used `${{ inputs.plugin_* != false }}` — which evaluated to `false` on `push: tags` releases because `inputs.*` is `null` and GitHub Actions coerces `null != false` to `false`, causing plugins (including WordPress, YouTube, and Translation) to be omitted from tag-triggered installers.
    - Updated `BUILD_PLUGIN_WORDPRESS`, `BUILD_PLUGIN_YOUTUBE`, `BUILD_PLUGIN_TRANSLATION`, and `BUILD_PLUGIN_GDOCS` across all 4 jobs to `${{ github.event_name == 'push' || inputs.plugin_* }}` so tag releases always bundle all plugins while preserving manual `workflow_dispatch` toggles.
  - **Plugin Manager Update & Open Folder Fix (`plugins/manager_dialog.py`)**:
    - Added missing `import sys` (required by `on_open_folder()` platform checks) and missing `GitHubPluginsWorker` import from `plugins.installer_workers` (resolving `NameError: name 'GitHubPluginsWorker' is not defined` in `check_for_plugin_updates()`).
    - Retained strong references to active background worker instances (`_update_check_worker`, `_batch_update_worker`).
  - **Regression Verification (`diagnostic_cloud_and_system_tests.py`)**:
    - Added assertions in `_test_plugin_interface_sandbox_testing` verifying that `.github/workflows/build.yml` never regresses to `inputs.plugin_* != false` and validating `PluginManagerDialog.check_for_plugin_updates()` and `on_open_folder()` without `NameError`.

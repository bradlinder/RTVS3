# Changelog

## v3.10.19-beta
- **Milestone 3.1a: `updater.py` Modular Decomposition & SRP Separation (`updater.py`, `updater_core.py`, `updater_workers.py`, `updater_dialog.py`, `installer/build_tools/config.py`, `scripts/modular_audit.py`, `scripts/dev_check.py`, `diagnostic_dialog.py`, `diagnostics/system_runtime_tests.py`)**:
  - **Headless Core & Worker Separation (`updater_core.py`, `updater_workers.py`)**:
    - Extracted GitHub release querying (`fetch_releases()`, `fetch_latest_release()`), semantic version comparison (`parse_version_tuple()`, `is_version_newer()`, `is_version_older()`), SHA-256 checksum lookup, platform asset selection, detached Windows/macOS/Linux installer launch (`launch_and_install()`), and installer cache cleanup (`cleanup_old_installers()`) into 100% headless `updater_core.py` (758 lines, zero top-level `PySide6.QtWidgets` imports).
    - Extracted `CheckUpdateWorker(QThread)` and `DownloadUpdateWorker(QThread)` into dedicated worker module `updater_workers.py` (189 lines, zero `QtWidgets` imports).
  - **Pure Qt UI Module, Facade & Audit Cleanup (`updater_dialog.py`, `updater.py`, `installer/build_tools/config.py`, `scripts/modular_audit.py`, `scripts/dev_check.py`)**:
    - Moved `CheckUpdateDialog(QDialog)` and `UpdaterMixin` into `updater_dialog.py` (702 lines) with a null-safe app icon guard, converted `updater.py` (1,549 → 80 lines) into a full backward-compatible facade preserving the `PROJECT_VERSION` fallback for `bump_version.py`, and deleted obsolete `updater.pyi`.
    - Registered `updater_core`, `updater_workers`, and `updater_dialog` in PyInstaller `HIDDEN_IMPORTS` and removed `updater.py` from grandfathered monolith lists (dropping grandfathered SRP collisions from `4` to `3` and `>1,000`-line legacy modules from `10` to `9` with zero new collisions).
  - **Regression & Frozen-GUI Dispatch Coverage (`diagnostic_dialog.py`, `diagnostics/system_runtime_tests.py`)**:
    - Added facade identity, `CheckUpdateDialog(auto_start=False)` instantiation, headless isolation, `HIDDEN_IMPORTS`, and budget-guard assertions to `diagnostics/system_runtime_tests.py`, and registered `_test_windows_detached_update_helper_architecture` in `_MAIN_THREAD_TEST_HANDLERS`.

## v3.10.18-beta
- **Fix YouTube Import Media Loading & Archived Media Tool Re-Activation (`plugins/youtube/yt_import_dialog.py`, `plugins/youtube/manifest.json`, `remote_media_cache_dialog.py`, `diagnostics/youtube_import_cache_tests.py`)**:
  - **Fix Downloaded YouTube Video Not Opening After Download (`plugins/youtube/yt_import_dialog.py`, `plugins/youtube/manifest.json`)**:
    - Replaced the broken `close_project()` + nonexistent `main_window.load_audio()` sequence in `prompt_load_youtube_episode_dialog()` with `main_window.load_media_file(str(file_path), source="YouTube video URL")`, ensuring downloaded videos immediately open in the media player/timeline with waveform, video thumbnails, and transcription/diarization tools enabled while honoring unsaved-project Save/Discard/Cancel prompts without closing the active project on cancel.
    - Enabled `redownload_remote_media_action` inside `populate_project_from_youtube_import()` and repackaged `plugins/youtube.rtvs-addon` (`3.10.18-beta`).
  - **Archived Remote Media Re-Attach Tool Enablement & Regression Tests (`remote_media_cache_dialog.py`, `diagnostics/youtube_import_cache_tests.py`)**:
    - Updated `reattach_downloaded_media_to_project()` to call `set_tools_actions_enabled(True)`, sync `timeline.set_is_video()`, and enable `regen_thumbnails_action` when restoring cleared remote media onto an existing `.rtvs` project.
    - Added end-to-end `MainWindow.load_media_file` handoff, cancel-abort safety, and `reattach_downloaded_media_to_project` tool-enablement regression checks to `diagnostics/youtube_import_cache_tests.py`.

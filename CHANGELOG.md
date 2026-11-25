# Changelog

## v3.10.14-beta
- **Milestone 3.9 & 3.10: WordPress Publishing UI Consolidation, Worker Extraction & Dead-Code Pruning (`plugins/wordpress/wp_workers.py`, `plugins/wordpress/wp_publish_dialog.py`, `plugins/wordpress/plugin.py`, `plugins/wordpress/wordpress_dialog.py`, `plugins/wordpress/manifest.json`, `scripts/modular_audit.py`, `diagnostics/export_wordpress_media.py`, `diagnostics/system_runtime_tests.py`)**:
  - **Worker & Dialog Separation (`plugins/wordpress/wp_workers.py`, `plugins/wordpress/wp_publish_dialog.py`)**:
    - Extracted `WordPressPublishWorker(QThread)` into dedicated headless-worker module `plugins/wordpress/wp_workers.py` (78 lines) and `WordPressPublishDialog(QDialog)` into `plugins/wordpress/wp_publish_dialog.py` (524 lines), preserving all featured image preview, custom notice, credential prompt, and offline spellcheck (`title_edit`, `excerpt_edit`, `custom_text_edit`, `img_caption_edit`, `img_alt_edit`) wiring.
  - **Opportunistic Dead-Code Pruning & Facades (`plugins/wordpress/plugin.py`, `plugins/wordpress/wordpress_dialog.py`)**:
    - Pruned confirmed dead `WordPressStoryMetadataWidget` (~274 lines) and duplicated `capture_video_frame()` helper from `plugins/wordpress/plugin.py` (980 → 89 lines), keeping `Plugin.create_story_metadata_widget() -> None` and backward-compatible re-exports intact.
    - Replaced superseded 903-line `plugins/wordpress/wordpress_dialog.py` duplicate UI with a 28-line compatibility facade re-exporting canonical `WordPressExportTabWidget` (`wp_tab_widget.py`), `WordPressPostMetadataDialog` (`export_destination.py`), `capture_video_frame` (`wp_post_builder.py`), and `generate_wp_excerpt`.
  - **Audit Cleanup, Plugin Catch-Up & Regression Tests (`scripts/modular_audit.py`, `plugins/wordpress/manifest.json`, `diagnostics/export_wordpress_media.py`, `diagnostics/system_runtime_tests.py`)**:
    - Removed `plugins/wordpress/plugin.py` and `plugins/wordpress/wordpress_dialog.py` from `GRANDFATHERED_LEGACY_MODULES` (dropping grandfathered SRP collisions from `5` to `4` with zero new violations) and deleted obsolete `plugin.pyi` and `wordpress_dialog.pyi`.
    - Bumped `plugins/wordpress/manifest.json` to `3.10.14-beta` (leaving untouched plugins unchanged), repackaged `wordpress.rtvs-addon`, and added modular identity, dead-widget exclusion, facade, and budget-guard checks.
  - **Spellcheck Deleted-Widget Lifecycle Fix (`spellcheck_widgets.py`, `diagnostic_speaker_cleanup_tests.py`)**:
    - Added `shiboken6.isValid()` guards (`_is_qt_object_alive()`, `SpellCheckController.is_alive()` / `dispose()`), weakref `destroyed` cleanup hooks, and `RuntimeError` guards across `SpellCheckController`, `_LineEditSpellOverlay.paintEvent()`, `attach_spellcheck()`, and `refresh_all_spellcheckers()`, eliminating stale `Internal C++ object (QLineEdit) already deleted` tracebacks when refreshing after closing dialogs, with deleted-widget regression assertions.

## v3.10.13-beta
- **Milestone 3.1: `model_management.py` Modularization & `ModelCleanupDialog` Extraction (`model_management.py`, `model_cleanup_dialog.py`, `installer/build_tools/config.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/system_runtime_tests.py`)**:
  - **Pure Qt UI Extraction (`model_cleanup_dialog.py`)**:
    - Extracted `ModelCleanupDialog`, `WHISPER_MODEL_CATALOG`, `format_directory_size()`, and shared `_stop_and_remove_runtime_env()` helper out of `model_management.py`, preserving all Manage Models controls, progress callbacks, selected-model removal, translation runtime cleanup prompts, and full purge hooks.
  - **Controller Cleanup & Duplication Pruning (`model_management.py`, `installer/build_tools/config.py`)**:
    - Reduced `model_management.py` from 989 lines to ~610 lines (well below the 800-line target), pruned unused Qt widget imports, reused `WHISPER_MODEL_CATALOG` and `_stop_and_remove_runtime_env()` in `refresh_whisper_model_chooser()` and `purge_all_data_action()`, kept all `ModelManagementMixin` & `WhisperModelInstallWorker` re-exports intact, removed obsolete `model_management.pyi`, and added `model_cleanup_dialog` to PyInstaller `HIDDEN_IMPORTS`.
  - **Regression Coverage (`diagnostics/editor_story_ui_tests.py`, `diagnostics/system_runtime_tests.py`)**:
    - Added `ModelCleanupDialog` instantiation, row/progress/refresh checks and `model_management` re-export assertions, and registered `model_management.py` + `model_cleanup_dialog.py` in modularity budget verification.

# Changelog

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

## v3.9.97-beta
- **WordPress Featured Image Caption & Alt Text Support (`plugins/wordpress/client.py`, `plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/plugin.py`, `plugins/wordpress/youtube_embed.py`, `diagnostic_export_tests.py`)**:
  - **REST API Attachment Metadata Updates (`client.py`)**:
    - Added `WordPressClient.update_media_metadata(media_id, caption=..., alt_text=...)` posting to `/wp/v2/media/{id}` (with `?rest_route=/wp/v2/media/{id}` fallback) and extended `upload_media()` with optional `caption` and `alt_text` kwargs.
    - Extended `execute_wordpress_upload()` with `featured_image_caption` and `featured_image_alt_text` kwargs; updates the uploaded WordPress Media Library attachment metadata immediately after image upload while keeping metadata failures non-fatal (`[WORDPRESS WARNING]`).
  - **Export Dialog UI, Bulk Apply & Project Persistence (`wp_ui_builder.py`, `wp_tab_widget.py`, `wp_post_builder.py`, `youtube_embed.py`)**:
    - Added separate **Caption** and **Alt Text** fields under Featured Image (Thumbnail) (`wp_img_meta_widget`), shown whenever any image mode other than `None` is active (both custom image files and video frame grabs).
    - Persisted `featured_image_caption` and `featured_image_alt_text` via `sync_featured_image_meta()` across story/episode switches, project saves, rebuilds, bulk apply-to-selected/all actions, and hover tooltips.
  - **Single-Post Quick Publish Dialog & Automated Tests (`plugin.py`, `export_destination.py`, `diagnostic_export_tests.py`)**:
    - Added matching Caption and Alt Text inputs and worker metadata publishing in `WordPressPublishDialog` / `WordPressPublishWorker`, plus caption indicators in `WordPressStoryMetadataWidget`.
    - Added automated unit and headless Qt UI integration tests in `_test_wordpress_featured_image_caption_and_alt_text`.

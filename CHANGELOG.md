# Changelog

## v3.10.29-beta
- **System-Wide Qt Zero-Flash Fix Across Export, Open Remote Episode & Classic Export Dialogs + Permanent AST & Multi-Dialog Guards (`plugins/youtube/export_destination.py`, `plugins/youtube/yt_import_dialog.py`, `plugins/youtube/manifest.json`, `export_dialogs.py`, `scripts/dev_check.py`, `AGENTS.md`, `diagnostics/editor_story_ui_tests.py`)**:
  - **Fix Remaining Orphan-Window Flashes (`plugins/youtube/export_destination.py`, `plugins/youtube/yt_import_dialog.py`, `export_dialogs.py`)**:
    - Fixed `YouTubeExportTabWidget._setup_ui()` (parented `yt_scrub_widget` / `yt_browse_widget` and moved initial `_on_yt_thumb_mode_changed()` after `yt_extras_section.add_layout(yt_extras_layout)`), eliminating the fleeting window flash when opening `UnifiedExportDialog` on video projects.
    - Fixed `LoadYouTubeEpisodeDialog._build_ui()` (`File > Open Remote Episode`) by parenting `fetch_btn` and `wp_link_edit` to `self` and applying initial `.setVisible()` after layout attachment, and fixed `export_dialogs.py:_choose_export_formats()` where `media.setVisible(media_available)` ran on an unparented `QCheckBox` before `layout.addWidget(media)`.
    - Repackaged `youtube.rtvs-addon` (`3.10.29-beta`).
  - **Permanent System-Wide Guards (`scripts/dev_check.py`, `diagnostics/editor_story_ui_tests.py`, `AGENTS.md`)**:
    - Added Pillar 5 (`check_qt_orphan_widget_flashes()`) to `scripts/dev_check.py` (statically auditing 180+ modules via AST for pre-attach non-`False` `.setVisible()` / `.setRowVisible()` calls, and removed now-modularized `background_workers.py` from `GRANDFATHERED`).
    - Upgraded the Qt `QEvent.Show` orphan-window spy in `diagnostics/editor_story_ui_tests.py` to sweep `UnifiedExportDialog` (with WordPress & YouTube plugins), `LoadYouTubeEpisodeDialog`, Preferences tabs, and core dialogs alongside the static AST check, and documented the zero-flash parenting rule in `AGENTS.md`.

## v3.10.28-beta
- **WordPress Custom Selection "Not Included in Export" Empty State & Fix Preferences Orphan-Widget Flash on `Ctrl+P` (`export/story_selector.py`, `plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/manifest.json`, `preferences_tabs_media.py`, `preferences_tabs_core.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/export_wordpress_media.py`)**:
  - **WordPress "Not Included in Export" Placeholder under `Custom Selection` (`export/story_selector.py`, `plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/manifest.json`)**:
    - Replaced stale post metadata with a clean, theme-adaptive **"Not included in this export"** placeholder panel whenever clicking an unchecked story/Full Episode row (or clearing all selections) in `ExportStorySelectorSidebar`, preventing accidental edits to a previously focused story.
    - Included a one-click **`Include in Export`** button right inside the placeholder that checks the focused sidebar item and immediately reveals its WordPress metadata editor, and repackaged `wordpress.rtvs-addon` (`3.10.28-beta`).
  - **Fix Flashing Orphan Windows When Opening Preferences (`Ctrl+P`) (`preferences_tabs_media.py`, `preferences_tabs_core.py`)**:
    - Attached `play_form` to `play_layout` before calling `_update_fades_options_visibility()` in `build_playback_timeline_tab()` and attached `mod_form` to `mod_layout` before calling `_update_beam_visibility()` in `build_ai_models_tab()`, eliminating brief top-level OS window flashes caused by calling `setVisible(True)` / `setRowVisible(..., True)` on unparented widgets before layout attachment, backed by a live Qt `QEvent.Show` orphan-window regression test.

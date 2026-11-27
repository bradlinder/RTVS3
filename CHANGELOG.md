# Changelog

## v3.10.24-beta
- **Two-Step Standalone Detect Segments Dialog & Concise `Custom Selection` Export Scope Label (`story_detect_dialog.py`, `export/dialog.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/export_wordpress_core.py`)**:
  - **Streamlined Two-Step Standalone Detect Segments Flow (`story_detect_dialog.py`)**:
    - Simplified `StandaloneDetectStoriesDialog` into a clean confirmation prompt showing a single-line summary of the active thresholds plus an **Adjust Settings...** button that opens a dedicated `DetectStoriesSettingsDialog` for editing silence gap, minimum segment length, detection basis, lead-in padding, and the opt-in **Save these values as my new defaults** checkbox.
    - Clicking **Apply** in `DetectStoriesSettingsDialog` returns the user to the confirmation dialog with the updated summary line (marking one-time overrides vs. saved defaults) before running detection.
  - **Concise Export Scope Label (`export/dialog.py`)**:
    - Shortened the `"selected_stories"` scope dropdown label in `UnifiedExportDialog` from `Selected Segments / Custom Selection` to **`Custom Selection`** and updated diagnostic assertions.

## v3.10.23-beta
- **Standalone Detect Stories One-Time Threshold Override Dialog & Bounded Timeline Thumbnail Density Presets (`story_detect_dialog.py`, `story_detection_processing.py`, `background_workers.py`, `media_batch.py`, `RadioTVSegmenter.py`, `preferences_tabs_media.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`, `timeline_context_menus.py`, `installer/build_tools/config.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/system_runtime_tests.py`)**:
  - **Standalone Detect Stories One-Time Override Dialog (`story_detect_dialog.py`, `story_detection_processing.py`, `installer/build_tools/config.py`)**:
    - Added compact `StandaloneDetectStoriesDialog` (registered in PyInstaller `HIDDEN_IMPORTS`) shown whenever running standalone **Detect Stories / Segments** (while keeping multi-stage **Run Processing** and Batch mode non-interactive).
    - Presents **Silence Gap Threshold** and **Minimum Segment Length** up front, tucks **Detection Basis** and **Lead-In Padding** inside a collapsed **More Options** section, merges the existing overwrite warning inline when stories already exist, and defaults to a one-time run-only override unless **Save these values as my new defaults** is checked.
  - **Bounded Timeline Thumbnail Density Presets (`background_workers.py`, `media_batch.py`, `RadioTVSegmenter.py`, `preferences_tabs_media.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`, `timeline_context_menus.py`)**:
    - Added three memory-bounded timeline thumbnail density presets — **Standard (36 frames)**, **Detailed (90 frames)**, and **High (180 frames)** (capped safely at 200 frames in `VideoThumbnailWorker`) — selectable in **Preferences → Media / Timeline** and via a checkable **Regenerate Video Thumbnails** submenu on the timeline right-click menu.
    - Isolated cache directories per density preset while preserving backward-compatible cache reuse for Standard (36), added automatic background regeneration when changing density in Preferences, guarded `QAction.triggered(bool)` slot dispatch, and added regression tests.

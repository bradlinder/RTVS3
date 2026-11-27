# Changelog

## v3.10.25-beta
- **Fix Overlapping & Clipped Controls in Preferences Audio Fades (`preferences_tabs_media.py`, `story_widgets.py`, `diagnostics/editor_story_ui_tests.py`)**:
  - **Eliminate Double-Indented Audio Fades Form Layout (`preferences_tabs_media.py`)**:
    - Removed the nested `play_form.addRow("", fades_sub_widget)` sub-form that pushed Audio Fades sub-controls into the narrow right column, placing **Fade Audio Preview**, **Default Story Fade-In**, **Default Story Fade-Out**, and **Default Fade Curve** directly into `play_form` with `setRowVisible()` toggling and wrapping the **Playback & Timeline** tab in a borderless `QScrollArea`.
  - **2×2 Responsive Grid Mode for `FadeCurveVisualSelector` (`story_widgets.py`)**:
    - Added an optional `columns` parameter to `FadeCurveVisualSelector` (using a `2×2` `QGridLayout` at `118×58px` per card in Preferences while keeping the horizontal `1×4` strip intact in `StoryFadesDialog`), fixing overlapping `Linear` / `S-Curve` / `Logarithmic` / `Exponential` curve cards and right-edge text clipping on `Preview audio fades in real-time during playback`, backed by a live Qt geometry-overlap regression test.

## v3.10.24-beta
- **Two-Step Standalone Detect Segments Dialog & Concise `Custom Selection` Export Scope Label (`story_detect_dialog.py`, `export/dialog.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/export_wordpress_core.py`)**:
  - **Streamlined Two-Step Standalone Detect Segments Flow (`story_detect_dialog.py`)**:
    - Simplified `StandaloneDetectStoriesDialog` into a clean confirmation prompt showing a single-line summary of the active thresholds plus an **Adjust Settings...** button that opens a dedicated `DetectStoriesSettingsDialog` for editing silence gap, minimum segment length, detection basis, lead-in padding, and the opt-in **Save these values as my new defaults** checkbox.
    - Clicking **Apply** in `DetectStoriesSettingsDialog` returns the user to the confirmation dialog with the updated summary line (marking one-time overrides vs. saved defaults) before running detection.
  - **Concise Export Scope Label (`export/dialog.py`)**:
    - Shortened the `"selected_stories"` scope dropdown label in `UnifiedExportDialog` from `Selected Segments / Custom Selection` to **`Custom Selection`** and updated diagnostic assertions.

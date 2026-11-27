# Changelog

## v3.10.26-beta
- **Duration-Scaled Per-Minute Thumbnail Density Presets, Anywhere-on-Timeline Regenerate Menu & Synchronized Shortcuts/User Guides (`background_workers.py`, `media_batch.py`, `preferences_tabs_media.py`, `timeline_context_menus.py`, `shortcuts/schema.py`, `user_guide_dialog.py`, `docs/guides/*.md`, `embedded_guides.py`, `README.md`, `diagnostics/editor_story_ui_tests.py`)**:
  - **4-Tier Duration-Scaled Per-Minute Thumbnail Density (`background_workers.py`, `media_batch.py`, `preferences_tabs_media.py`)**:
    - Replaced fixed thumbnail frame counts with four duration-scaled presets labeled by rate per minute: **Standard (2 per min, 16–180)**, **Detailed (4 per min, 24–300)**, **High (8 per min, 36–480)**, and **Extra High (16 per min, 48–960)**.
    - Updated `VideoThumbnailWorker` to extract `240px`-wide frames (`~50%` lower RAM footprint while staying sharp on HiDPI timelines) using 4-digit filenames (`thumb_%04d.jpg`) and distinct per-count cache directories.
  - **Right-Click Anywhere on Timeline for Regeneration (`timeline_context_menus.py`)**:
    - Exposed **Regenerate Waveform** and the 4-tier checkable **Regenerate Video Thumbnails** submenu when right-clicking anywhere on the timeline—including inside already-assigned segments/stories—not only on empty space.
  - **Synchronized Keyboard Shortcuts, Built-In Guides & README (`shortcuts/schema.py`, `user_guide_dialog.py`, `docs/guides/*.md`, `embedded_guides.py`, `README.md`)**:
    - Updated `detect_stories` and `regen_thumbnails` descriptions in `shortcuts/schema.py` and `README.md`, added the **Right-Click Timeline** control note to `user_guide_dialog.py`, updated all five relevant user guides (`getting_started_and_workflow.md`, `wordpress_exporting.md`, `export_formats.md`, `youtube_features.md`, `video_shows_and_youtube_publishing.md`) for `Custom Selection`, YouTube-source WordPress defaults/embed inheritance, two-step Detect Segments overrides, Audio Fades 2×2 curve layout, and per-minute thumbnail density, and mirrored them verbatim into `embedded_guides.py`.

## v3.10.25-beta
- **Fix Overlapping & Clipped Controls in Preferences Audio Fades (`preferences_tabs_media.py`, `story_widgets.py`, `diagnostics/editor_story_ui_tests.py`)**:
  - **Eliminate Double-Indented Audio Fades Form Layout (`preferences_tabs_media.py`)**:
    - Removed the nested `play_form.addRow("", fades_sub_widget)` sub-form that pushed Audio Fades sub-controls into the narrow right column, placing **Fade Audio Preview**, **Default Story Fade-In**, **Default Story Fade-Out**, and **Default Fade Curve** directly into `play_form` with `setRowVisible()` toggling and wrapping the **Playback & Timeline** tab in a borderless `QScrollArea`.
  - **2×2 Responsive Grid Mode for `FadeCurveVisualSelector` (`story_widgets.py`)**:
    - Added an optional `columns` parameter to `FadeCurveVisualSelector` (using a `2×2` `QGridLayout` at `118×58px` per card in Preferences while keeping the horizontal `1×4` strip intact in `StoryFadesDialog`), fixing overlapping `Linear` / `S-Curve` / `Logarithmic` / `Exponential` curve cards and right-edge text clipping on `Preview audio fades in real-time during playback`, backed by a live Qt geometry-overlap regression test.

# Changelog

## v3.9.79-beta
- **WordPress YouTube Embed Dynamic Auto-Dimming & Control State Synchronization (`plugins/wordpress/youtube_embed.py`, `diagnostic_export_tests.py`)**:
  - **Context-Aware Auto-Dimming**: Automatically disables (grays out) the YouTube Video Placement radio buttons ("Place at top" / "Place at bottom") and story start/stop timestamp checkboxes whenever the YouTube URL field is empty or contains an invalid URL/ID.
  - **Dynamic State Synchronization**: Entering or pasting a valid YouTube link instantly activates and illuminates all placement and story timecode options, providing real-time visual feedback and eliminating ambiguity regarding empty URL handling.
  - **Status Label Guidance & Tooltips**: Updated dynamic status label below the URL box to clearly guide users (`No YouTube video attached. (Enter a YouTube URL above to configure embed options)`), accompanied by descriptive disabled-state tooltips on all placement controls.
  - **Automated Regression Suite**: Expanded diagnostic test `WordPress YouTube Video Embed` in `diagnostic_export_tests.py` with end-to-end assertions verifying dynamic enable/disable transitions across blank, valid, and cleared URL states.

## v3.9.78-beta
- **Native In-App Documentation Viewer & Comprehensive User Guides (`user_guide_dialog.py`, `playback_preferences.py`, `docs/guides/`, `build_installer.py`)**:
  - **Native In-App Documentation Reader (`user_guide_dialog.py`)**: Created an interactive desktop reader dialog (`UserGuideDialog`) featuring topic navigation, zoom controls (`Ctrl++` / `Ctrl+-`), dark/light theme synchronization, and an optional "Open in Web Browser" export.
  - **Inline Screenshot Rendering**: Integrated PySide6 `QTextBrowser` with automatic relative image resolution (`file:///...`), displaying pixel-accurate PNG screenshots inline directly within the application window without needing external editors or web browsers.
  - **Comprehensive Multi-Guide Library**:
    - **Getting Started & Workflow (`docs/guides/getting_started_and_workflow.md`)**: User-friendly walkthrough covering media loading, playback controls, speech transcription, speaker renaming, story segmentation, and the Batch Processing Center.
    - **WordPress Exporting & Setup (`docs/guides/wordpress_exporting.md`)**: Step-by-step instructions on generating WordPress Application Passwords, connecting RTVS3, configuring post draft scopes, setting authors/categories, and handling podcast enclosures.
    - **YouTube Features & Chapter Generation (`docs/guides/youtube_features.md`)**: Generating and copying timestamped chapter lists for YouTube video descriptions, and embedding timestamped clips into articles.
    - **Export Formats & DAW Integration (`docs/guides/export_formats.md`)**: Split audio cuts with fades, Word/PDF documents, REAPER DAW projects, and video EDL/XML timelines.
  - **Installer Packaging Directive (`build_installer.py`)**: Packaged the `docs/` hierarchy into PyInstaller distribution bundles so guides and screenshots are available offline in frozen application builds.

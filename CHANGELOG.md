# Changelog

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

## v3.9.77-beta
- **User Documentation, Automated Zero-Hallucination Screenshots & Help Menu Integration (`docs/guides/video_shows_and_youtube_publishing.md`, `scripts/capture_guide_screenshots.py`, `ui_menus.py`, `playback_preferences.py`, `AGENTS.md`)**:
  - **Comprehensive Video Shows & YouTube Publishing Guide (`docs/guides/video_shows_and_youtube_publishing.md`)**: Authored an end-to-end user guide explaining the hybrid local media / YouTube hosting workflow, step-by-step export walkthrough, YouTube URL format compatibility reference, and 16:9 mobile-responsive Gutenberg iframe block architectures.
  - **Programmatic Zero-Hallucination Screenshot Engine (`scripts/capture_guide_screenshots.py`)**: Built an automated off-screen Qt rendering script that captures pixel-accurate PNG screenshots (`wordpress_export_media_tab.png`, `wordpress_export_content_tab.png`, `wordpress_posts_list_badges.png`, `wordpress_preferences_credentials.png`, `unified_export_dialog.png`) directly from native widgets, guaranteeing zero AI visual hallucination in technical documentation.
  - **In-App Help Menu Integration (`ui_menus.py`, `playback_preferences.py`)**: Added "User Guides & Documentation..." (`Shift+F2`) to the **Help** menu, launching the user's native system viewer or default browser to local guides and repository docs via `QDesktopServices.openUrl()`.
  - **Standardized Documentation Policy (`AGENTS.md`)**: Formalized Section 16 defining the Three-Tier Documentation Cadence (Tier 1 Changelog/Roadmap sync, Tier 2 Feature Guide creation, Tier 3 Master Manual audits) and the Zero-Hallucination Visual Asset Invariant.

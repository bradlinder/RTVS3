# Changelog

## v3.9.77-beta
- **User Documentation, Automated Zero-Hallucination Screenshots & Help Menu Integration (`docs/guides/video_shows_and_youtube_publishing.md`, `scripts/capture_guide_screenshots.py`, `ui_menus.py`, `playback_preferences.py`, `AGENTS.md`)**:
  - **Comprehensive Video Shows & YouTube Publishing Guide (`docs/guides/video_shows_and_youtube_publishing.md`)**: Authored an end-to-end user guide explaining the hybrid local media / YouTube hosting workflow, step-by-step export walkthrough, YouTube URL format compatibility reference, and 16:9 mobile-responsive Gutenberg iframe block architectures.
  - **Programmatic Zero-Hallucination Screenshot Engine (`scripts/capture_guide_screenshots.py`)**: Built an automated off-screen Qt rendering script that captures pixel-accurate PNG screenshots (`wordpress_export_media_tab.png`, `wordpress_export_content_tab.png`, `wordpress_posts_list_badges.png`) directly from native widgets, guaranteeing zero AI visual hallucination in technical documentation.
  - **In-App Help Menu Integration (`ui_menus.py`, `playback_preferences.py`)**: Added "User Guides & Documentation..." (`Shift+F2`) to the **Help** menu, launching the user's native system viewer or default browser to local guides and repository docs via `QDesktopServices.openUrl()`.
  - **Standardized Documentation Policy (`AGENTS.md`)**: Formalized Section 16 defining the Three-Tier Documentation Cadence (Tier 1 Changelog/Roadmap sync, Tier 2 Feature Guide creation, Tier 3 Master Manual audits) and the Zero-Hallucination Visual Asset Invariant.

## v3.9.76-beta
- **Timeline & Story Context Menu Transient Parent Top-Level Normalization (`timeline_context_menus.py`, `timeline_widgets.py`, `story_widgets.py`)**:
  - **Top-Level Window Parenting for Menus & Tooltips**: Updated `show_timeline_context_menu`, `show_selection_context_menu`, and story list context menus to use `canvas.window()` / `self.window()` as their parent `QWidget` instead of the child timeline canvas or list widget.
  - **Eliminated QWidgetWindow Transient Parent Warning**: Resolved Qt platform warning (`QWidgetWindow(..., name="timeline_widgetWindow") must be a top level window.`) which occurred on Windows when OLE drag-and-drop created a native `HWND` for the child timeline widget, causing Qt's `QWindow::setTransientParent` to warn when context menus or tooltips referenced the child widget instead of the top-level `QMainWindow`.

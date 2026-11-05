# Changelog

## v3.9.80-beta
- **In-App User Guides Program Directory Packaging & Hardcoded Embedded Fallbacks (`user_guide_dialog.py`, `embedded_guides.py`, `build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `diagnostic_editor_tests.py`)**:
  - **Application Program Directory Installation (`build_installer.py`, `RadioTVStorySegmenter.iss`)**: Explicitly bundled the entire `docs/` hierarchy (user guides and screenshot images) into `dist/RadioTVSegmenter/docs/` during stage 2 packaging. When installed via the Windows Setup wizard, documentation is placed directly into `{app}\docs\` (`C:\Program Files\Radio & TV Segmenter\docs\`).
  - **PyInstaller Internal Pruning Protection (`build_installer.py`)**: Protected `_internal/docs` during post-build file pruning by refining directory cleanup rules to only prune third-party documentation inside `site-packages`, preserving application user guides and offline resources.
  - **Robust Multi-Candidate Path Resolution (`user_guide_dialog.py`)**: Replaced single-path assumptions with `_find_docs_dir()` scanning candidate locations across installed program roots (`sys.executable.parent / "docs"`), PyInstaller internal runtime (`_MEIPASS / "docs"`), macOS bundle resources (`Contents/Resources/docs`), and development source repositories.
  - **Hardcoded Compile-Time Embedded Fallbacks (`embedded_guides.py`)**: Embedded full markdown copies of all 5 core user guides as compiled Python string fallbacks. In the event disk files are removed or inaccessible, `UserGuideDialog` seamlessly renders the built-in guide text, ensuring end users never encounter "Guide Not Found" errors.
  - **Automated Regression Suite (`diagnostic_editor_tests.py`, `test_runner.py`)**: Added diagnostic item `In-App User Guides and Documentation Viewer` validating guide catalog completeness, live disk loading, simulated zero-disk embedded fallbacks, and installer packaging invariants.

## v3.9.79-beta
- **WordPress YouTube Embed Dynamic Auto-Dimming & Control State Synchronization (`plugins/wordpress/youtube_embed.py`, `diagnostic_export_tests.py`)**:
  - **Context-Aware Auto-Dimming**: Automatically disables (grays out) the YouTube Video Placement radio buttons ("Place at top" / "Place at bottom") and story start/stop timestamp checkboxes whenever the YouTube URL field is empty or contains an invalid URL/ID.
  - **Dynamic State Synchronization**: Entering or pasting a valid YouTube link instantly activates and illuminates all placement and story timecode options, providing real-time visual feedback and eliminating ambiguity regarding empty URL handling.
  - **Status Label Guidance & Tooltips**: Updated dynamic status label below the URL box to clearly guide users (`No YouTube video attached. (Enter a YouTube URL above to configure embed options)`), accompanied by descriptive disabled-state tooltips on all placement controls.
  - **Automated Regression Suite**: Expanded diagnostic test `WordPress YouTube Video Embed` in `diagnostic_export_tests.py` with end-to-end assertions verifying dynamic enable/disable transitions across blank, valid, and cleared URL states.

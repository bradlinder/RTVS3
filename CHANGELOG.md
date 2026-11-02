# Changelog

## v3.9.59-beta
- **Preferences Real-Time Category & Setting Search Filter (`preferences_dialog.py`, `diagnostic_loudness_tests.py`)**:
  - **Inline Search Box Above Navigation Tabs**: Added a dedicated settings search box directly above the category navigation sidebar on the left of the Preferences dialog, providing natural, desktop-standard discoverability.
  - **Instant Multi-Page Setting Text Indexing**: As the user types (e.g. *whisper*, *loudness*, *theme*, *gpu*, *shortcuts*), the dialog inspects labels, checkboxes, groupbox titles, combobox entries, table items, and tooltips across all stacked pages in real time (~2ms).
  - **Dynamic Category Filtering & Match Badging**: Automatically hides non-matching category tabs and appends live match count badges to matching categories (e.g. `AI Models (7)`, `Audio Settings (4)`). If the active tab no longer matches, focus auto-switches to the first matching category.
  - **Fluid Keyboard Navigation**: Added `Escape` key handling to instantly clear the search filter and restore full category visibility without closing the dialog, and `Down` arrow handling to transition focus seamlessly from the search field into the category list. Clearing the search box restores all original category names and visibility immediately.

## v3.9.58-beta
- **Windows Drag-and-Drop Ingestion Overhaul (`core_utils.py`, `playback_controller.py`, `ui_layout.py`, `transcript_editor.py`, `installer/Windows/RadioTVStorySegmenter.iss`)**:
  - **Inno Setup Non-Elevated Launch (`runasoriginaluser`)**: Added `runasoriginaluser` to the `[Run]` directive in `RadioTVStorySegmenter.iss`. Previously, when users installed or updated the application and checked "Launch Radio & TV Segmenter", the process was launched with inherited Administrator elevation. Windows User Interface Privilege Isolation (UIPI) silently blocks all drag-and-drop messages (WM_DROPFILES and OLE) from non-elevated Windows Explorer to elevated processes. The `runasoriginaluser` flag ensures the app launches with standard user credentials so Explorer drag-and-drop works out of the box.
  - **Windows URI Leading Slash Regex Stripper (`core_utils.py`)**: Corrected `_clean_path_candidate` in `core_utils.py` using a robust regex (`^/+(?=[a-zA-Z]:[\\/])`) to cleanly strip leading slashes from Windows drive letter URIs (e.g. `file:///C:/path`, `/C:/path`, `///C:/path`), resolving an index offset bug that prevented `Path.resolve().exists()` from verifying dropped media paths.
  - **Window-Wide & Central Widget Drop Acceptance (`ui_layout.py`, `playback_controller.py`, `transcript_editor.py`)**:
    - Enabled `setAcceptDrops(True)` on the main window's `central_widget`.
    - Expanded `eventFilter` in `playback_controller.py` so any drag of supported media (`.wav`, `.mp3`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.wma`, `.aiff`, `.mp4`, `.mov`, `.mkv`, `.webm`, etc.) or project archives (`.rtvs`, `.rtvs3`) over the timeline, central widget, story list, transcript, or window background displays the green Copy cursor and dispatches cleanly to `load_media_file` or `load_project_file`.
    - Fixed undefined `open_media_file` callback in `story_list.filesDropped` by connecting to unified `_handle_dropped_media_or_project`.

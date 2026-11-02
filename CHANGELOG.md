# Changelog

## v3.9.58-beta
- **Windows Drag-and-Drop Ingestion Overhaul (`core_utils.py`, `playback_controller.py`, `ui_layout.py`, `transcript_editor.py`, `installer/Windows/RadioTVStorySegmenter.iss`)**:
  - **Inno Setup Non-Elevated Launch (`runasoriginaluser`)**: Added `runasoriginaluser` to the `[Run]` directive in `RadioTVStorySegmenter.iss`. Previously, when users installed or updated the application and checked "Launch Radio & TV Segmenter", the process was launched with inherited Administrator elevation. Windows User Interface Privilege Isolation (UIPI) silently blocks all drag-and-drop messages (WM_DROPFILES and OLE) from non-elevated Windows Explorer to elevated processes. The `runasoriginaluser` flag ensures the app launches with standard user credentials so Explorer drag-and-drop works out of the box.
  - **Windows URI Leading Slash Regex Stripper (`core_utils.py`)**: Corrected `_clean_path_candidate` in `core_utils.py` using a robust regex (`^/+(?=[a-zA-Z]:[\/])`) to cleanly strip leading slashes from Windows drive letter URIs (e.g. `file:///C:/path`, `/C:/path`, `///C:/path`), resolving an index offset bug that prevented `Path.resolve().exists()` from verifying dropped media paths.
  - **Window-Wide & Central Widget Drop Acceptance (`ui_layout.py`, `playback_controller.py`, `transcript_editor.py`)**:
    - Enabled `setAcceptDrops(True)` on the main window's `central_widget`.
    - Expanded `eventFilter` in `playback_controller.py` so any drag of supported media (`.wav`, `.mp3`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.wma`, `.aiff`, `.mp4`, `.mov`, `.mkv`, `.webm`, etc.) or project archives (`.rtvs`, `.rtvs3`) over the timeline, central widget, story list, transcript, or window background displays the green Copy cursor and dispatches cleanly to `load_media_file` or `load_project_file`.
    - Fixed undefined `open_media_file` callback in `story_list.filesDropped` by connecting to unified `_handle_dropped_media_or_project`.

## v3.9.57-beta
- **Simultaneous Search Auto-Highlighting & Live Match Counter (`playback_preferences.py`, `transcript_timeline_sync_mixin.py`, `transcript_selection_mixin.py`, `ui_layout.py`, `transcript_editor_dialogs.py`, `theme_qss.py`)**:
  - **Simultaneous Document-Wide Highlighting**: Typing in the transcript search bar (or Find & Replace dialog) immediately highlights every occurrence of the search phrase across the entire transcript using non-destructive `QTextEdit.ExtraSelection` (theme-aware warm amber highlight for inactive matches and vibrant cyan/sky highlight for the active match), providing instant visual density awareness.
  - **Live Match Counter Badge (`X / Y`)**: Added a compact, high-visibility match counter badge (`1 / 14` or `0 / 0`) directly beside the transcript search bar and inside the Find & Replace dialog that dynamically updates as you type or cycle through matches.
  - **Bidirectional 'Find Prev' and 'Find Next' Controls**: Added paired 'Find Prev' and 'Find Next' buttons directly in the transcript search bar and Find & Replace dialog for rapid one-click mouse navigation alongside `Enter` / `Shift+Enter` and `Ctrl+G` / `Ctrl+Shift+G`.
  - **Seamless Real-Time Synchronization**: Search highlights and match counters automatically synchronize bidirectionally between the transcript search bar, transcript editor, and Find & Replace dialog.

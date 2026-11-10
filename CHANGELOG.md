# Changelog

## v3.9.95-beta
- **Windows Post-Update Elevation De-escalation & Context Menu Hardening (`installer/Windows/RadioTVStorySegmenter.iss`, `timeline_context_menus.py`, `background_workers.py`, `media_batch.py`, `diagnostic_editor_tests.py`)**:
  - **Inno Setup Standard-User Post-Install Execution (`installer/Windows/RadioTVStorySegmenter.iss`)**:
    - Replaced `{win}\explorer.exe` invocation with Inno Setup's native `runasoriginaluser` directive on the postinstall `[Run]` command (`Flags: nowait postinstall skipifsilent runasoriginaluser`).
    - Eliminates Windows UAC split-token elevation lockout on post-update launches: newly updated applications consistently run within the interactive user session, preserving immediate access to mapped network drives, SMB shares (`\\Server\Share`), network credentials, and Windows Explorer drag-and-drop without requiring an application restart.
  - **Timeline Context Menu Localization Fix (`timeline_context_menus.py`)**:
    - Resolved `NameError: name 'is_es' is not defined` in `show_timeline_context_menu` by properly assigning `is_es = vocab.is_es`.
    - Restored right-click context menu functionality on empty timeline canvas areas and story blocks across English and Spanish locales.
    - Added optional `exec_menu: bool = True` parameter to both `show_timeline_context_menu()` and `show_selection_context_menu()` allowing headless verification and automated testing without opening blocking modal loops.
  - **Waveform Worker Network & File Error Reporting (`background_workers.py`, `media_batch.py`)**:
    - Configured FFmpeg subprocess stderr capture in `WaveformWorker` (`-v error`, `stderr=subprocess.PIPE`).
    - Propagated exact FFmpeg failure causes (`error_message`) to `MediaBatchMixin._waveform_finished()` so network access denials, unreachable shares, or corrupt audio streams log explicit actionable error messages rather than silently failing with "produced no audio data".
  - **Diagnostic Test Bench Menu Traversal Guard (`diagnostic_editor_tests.py`)**:
    - Added automated context-menu building verification across English and Spanish in `_test_story_highlighting_smart_copy_and_glossary_engine`, guaranteeing all action labels, dynamic vocabulary interpolations, and locale variables are exercised in CI.
  - **Progressive Streaming Waveform Rendering (`background_workers.py`, `media_batch.py`, `timeline_widgets.py`, `timeline_painter.py`, `diagnostic_editor_tests.py`)**:
    - Added real-time rate-limited waveform peak streaming via `WaveformWorker.progress` signal (`Signal(list, float, int)`), emitting partial peak arrays every ~250ms during extraction.
    - Updated `timeline_painter.py` to index progressive peaks by absolute time math (`eff_pps = progressive_pps / (4 ** level_index)`), rendering peaks left-to-right along the center baseline at their exact timeline ruler coordinates as frames decode over SMB network shares.
    - Added live percentage completion badge to the timeline background status banner (`Generating audio waveform ({pct}%)...`).
    - Added comprehensive regression unit test in `diagnostic_editor_tests.py` verifying partial peak rendering, percentage badge updates, and clean state restoration upon completion.

## v3.9.94-beta
- **Universal "Segment" Terminology & Display Title Standardization (`core_utils.py`, `preferences_tabs_core.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`, `preferences_tabs_media.py`, `RadioTVSegmenter.py`, `transcript_context_menu_mixin.py`, `transcript_editor_dialogs.py`, `story_widgets.py`, `ui_layout.py`, `media_batch.py`, `timeline_snap.py`, `ui_menus.py`, `story_metadata_dialog.py`, `shortcuts/schema.py`, `diagnostic_editor_tests.py`)**:
  - **Universal "Segment" Terminology Standardization (`core_utils.py`)**:
    - Streamlined `get_story_vocabulary()` to permanently and universally resolve timeline entries to **Segment / Segments** (`Segmento / Segmentos` in Spanish), eliminating multi-mode switching and reducing `core_utils.py` by 34 lines (down to 773 lines, safely within the 800-line modularity threshold).
    - Preserved `StoryVocabulary` structure and underlying object schemas for 100% backward compatibility with existing `.rtvs` project files and undo/redo history.
  - **Preferences Vocabulary Simplification (`preferences_tabs_core.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`)**:
    - Removed the redundant `UI Vocabulary / Terminology` dropdown from Preferences General tab and decoupled vocabulary logic from preference saving and factory resets.
  - **Acoustic Detection Mode Retention (`preferences_tabs_media.py`)**:
    - Retained the Voice vs. Music acoustic boundary detection algorithm in Preferences while updating labels to **Music / Track Breaks (Music Programs)** and tooltips to consistently reference segment boundaries rather than switching terminology to "Songs".
  - **Interactive Transcript & Floating Bubble Alignment (`transcript_context_menu_mixin.py`, `transcript_editor_dialogs.py`)**:
    - Right-click transcript context menu updated to dynamically reflect `Add Selected Text to New Segment` (or `Add Selected Sections to New Segments ({count})`), `Audition Segment Playback`, `Copy Segment Transcript`, `Copy Segment as Audio Clip`, and `Segment & Post Metadata...`.
    - Floating selection bubble button updated from `+ Story` to `+ Segment` with matching tooltip.
  - **Sidebar, Timeline & Dialog Terminology Polish (`story_widgets.py`, `timeline_snap.py`, `ui_layout.py`, `media_batch.py`, `story_metadata_dialog.py`, `ui_menus.py`)**:
    - Story card delegates and fallback text now badge items as `Segment 1`, `Segment 2` (or `Segmento 1`, `Segmento 2`).
    - Sidebar right-click menu actions updated to `Audition Segment Playback`, `Copy Segment Transcript (Ctrl+C)`, `Export Selected Segments...`, `Segment & Post Metadata...`, and `Delete Selected Segment`.
    - Waveform hover tooltips updated from `Story #N:` to `Segment #N:`.
    - Form placeholders updated to `Segment title / headline` and `Segment author / reporter / contributor`.
    - Floating metadata dialog updated to `Segment Settings & Metadata`.
    - Tools menu simplified to `Detect Segments (Complete)` / `&Detect Segments...` (or `&Detectar segmentos`), removing dynamic song switching.
  - **Display Title Update (`ui_menus.py`, `core_utils.py`)**:
    - Help menu updated to `&About Radio & TV Segmenter` to match `APP_DISPLAY_NAME = "Radio & TV Segmenter"`, while keeping `INTERNAL_APP_ID = "RadioTVStorySegmenter"` intact for QSettings stability.
  - **Keyboard Shortcut Registry Alignment (`shortcuts/schema.py`, `RadioTVSegmenter.py`)**:
    - Shortcut action labels updated to `Play Current Segment Only`, `Mark Segment In-Point ([)`, `Mark Segment Out-Point (])`, and `Delete Selected Segment` while keeping underlying `action_id` keys identical.

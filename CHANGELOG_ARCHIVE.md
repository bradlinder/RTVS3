# Changelog Archive (Historical Releases: v1.1 – v3.8.9-beta.19)

## v3.9.72-beta
- **Export Destination Reordering Synchronization & Plugin Tab Binding Hardening (`export/dialog.py`, `plugins/wordpress/export_destination.py`, `plugins/youtube/export_destination.py`, `diagnostic_export_tests.py`)**:
  - **Eliminated 'WordPress Tab Not Initialized' Reordering Defect**: Fixed an architectural desynchronization bug in `UnifiedExportDialog._build_destinations_layout()` where reordering export destinations via the "⇅ Reorder…" dialog queried the plugin manager for new destination instances while reusing cached QWidget pages, but failed to re-bind the new destination objects to the existing pages. Clicking "Export" subsequently failed with `"WordPress tab not initialized."` or `"YouTube tab not initialized."`.
  - **Cached Destination & Page Reconnection Guarantee (`export/dialog.py`)**: `_build_destinations_layout()` now preserves the existing initialized `dest_obj` from `_dest_entries` and explicitly rebinds `tab_widget` and `widget` attributes to the cached page for both existing and newly instantiated destination instances.
  - **Defensive Unlinked Widget Resolvers (`plugins/wordpress/export_destination.py`, `plugins/youtube/export_destination.py`)**: Added `_ensure_tab_widget()` defensive fallbacks in `WordPressExportDestination` and `YouTubeExportDestination`. If `tab_widget` is ever unlinked when `validate()`, `button_label`, or `get_export_data()` is called, the destination automatically checks its `.widget` property and falls back to resolving its registered page from the active dialog's `_dest_entries` rather than crashing or rejecting export.
  - **Early Constructor Initialization**: Initialized `self.plugin = plugin` and `self.tab_widget = None` prior to `super().__init__()` in export destination classes to safely support dynamic property evaluation (`self.button_label`) during base class instantiation.
  - **Automated Contract & Reconnection Verification (`diagnostic_export_tests.py`)**: Updated `Export Destination Interface Contract Verification` test to validate dynamic unlinked widget reconnection and defensive resolver binding across WordPress and YouTube destinations.

## v3.9.71-beta
- **Find & Replace Data-Model Synchronization & Speaker Re-render Immunity (`transcript_editor_dialogs.py`, `ui_dialog_launchers.py`, `diagnostic_editor_tests.py`)**:
  - **Eliminated Find & Replace Speaker Reversion**: Resolved an architectural defect where Find & Replace previously performed direct in-place modifications only in the `QTextEdit` presentation buffer without mutating the underlying project data model (`transcript["segments"]`, `words`, and `speaker_names`). Because the data model was left unchanged, any subsequent speaker label modification or speaker manager action called `render_transcript()`, instantly re-rendering the view from the unedited data model and reverting all corrected names back to the previous misspellings.
  - **Data-Model Backed Replacements**: Find & Replace now directly mutates `transcript["segments"]`, synchronizes word-level alignment and timestamps via `sync_segment_words()`, updates full transcript text, and synchronizes active translations.
  - **Speaker Alias & Glossary Synchronization**: Added an "Include Speakers" option (enabled by default) that updates matching display aliases in `speaker_names` and `custom_speakers_glossary`, ensuring speaker headers and spoken dialogue stay synchronized.
  - **Project State Undo/Redo & Persistence**: Every Find & Replace operation now captures before/after project states, records clean undo commands on `undo_stack`, marks the project dirty, triggers `render_transcript()` with scroll position preservation, and persists changes.
  - **Shortcut & Context Menu Unification**: Added `open_find_replace` alias in `UiDialogLaunchersMixin` to seamlessly handle both `open_find_replace()` and `open_find_dialog()` invocations from editor shortcuts and context menus.
  - **Automated Diagnostic Suite (`diagnostic_editor_tests.py`)**: Added end-to-end automated test `Find and Replace Project Synchronization and Undo` verifying data-model mutations, word alignment synchronization, speaker change survival, and undo/redo integrity.

## v3.9.70-beta
- **Version Source-of-Truth Harmonization & Updater Dialog Desync Resolution (`core_utils.py`, `updater.py`, `prs_shared.py`, `RadioTVSegmenter.py`)**:
  - **Resolution of Core Version Desync**: Harmonized `PROJECT_VERSION` across `core_utils.py`, `prs_shared.py`, `RadioTVSegmenter.py`, and `backup_manager.py` to `3.9.70-beta`, eliminating the desync where `updater.py` read an outdated version from `core_utils.py` while the main window title read from `prs_shared.py`.
  - **Updater Dual-Check Version Binding (`updater.py`)**: Bound `updater.py`'s `PROJECT_VERSION` to synchronize with `prs_shared.PROJECT_VERSION` at module import time, preventing future version drift across decoupled packages.
  - **Checklist & Verification Alignment (`AGENTS.md`, `bump_version.py`)**: Updated project release checklists and automated tooling to verify synchronization across all 13 canonical version entrypoints.

## v3.9.61-beta
- **Installed Windows Drag-and-Drop Diagnostic & Setup Hardening (`RadioTVSegmenter.py`, `ui_layout.py`, `installer/Windows/RadioTVStorySegmenter.iss`)**:
  - **Child Widget Event Propagation (`ui_layout.py`)**: Removed `central_widget.setAcceptDrops(True)` on the layout container to prevent default `QWidget::dragEnterEvent` from rejecting drag events before reaching child targets.
  - **Shortcut Working Directory Specification (`RadioTVStorySegmenter.iss`)**: Configured explicit `WorkingDir: "{app}"` for both desktop and start menu shortcuts generated by Inno Setup.


This archive preserves historical release notes and point releases prior to v3.9.0-beta.1.
For current and active releases, see [CHANGELOG.md](CHANGELOG.md).

---

## v3.9.68-beta
- **Windows Auto-Updater Syntax & Detached Handoff Hardening (`updater.py`)**:
  - **Python Helper Syntax & Indentation Resolution**: Fixed critical 4-space unexpected indent bug in `updater.py`'s dynamically generated Python helper template (`rtvs_update_helper.py`), which caused Python to crash on launch with `IndentationError` when updating between releases.
  - **Synchronous In-Memory Validation Guard**: Added `compile(python_helper_code, "rtvs_update_helper.py", "exec")` validation check before writing the helper script to disk. If template generation ever raises a syntax or indentation exception, execution safely aborts to the PowerShell supervisor instead of spawning an inoperable child process.
  - **Preserved UAC Elevation & Post-Install De-Elevation Architecture**: Maintained explicit elevated installer handoff (`runas`) for `C:\Program Files` authorization while guaranteeing standard user token execution on first run via `RadioTVStorySegmenter.iss`'s `{win}\explorer.exe` post-install hook, ensuring drag-and-drop and clipboard functionality work out of the box.

## v3.9.67-beta
- **False Unsaved Changes Prompt Elimination on Application Exit (`project_export.py`, `playback_preferences.py`, `media_batch.py`)**:
  - **Inversion of Activity Logger Default Parameter (`playback_preferences.py`)**: Changed `log_activity(self, action_text, mark_dirty=False)` default from `mark_dirty=True` to `mark_dirty=False`. Ephemeral activity telemetry and diagnostic console messages no longer mark the user's project file as dirty unless explicit project data mutations are committed.
  - **Shutdown Telemetry Self-Dirty Bug Resolution (`project_export.py`)**: In `closeEvent()`, `self.log_activity("[SYSTEM] Application shutdown requested.")` previously invoked `mark_project_dirty()` on every close attempt, converting a clean, saved project (`✓ Saved`) into a dirty project right before the exit prompt check. Explicitly passed `mark_dirty=False` and safeguarded shutdown telemetry.
  - **Graceful Cancel / Discard State Restoration (`project_export.py`)**: Reset `self._is_closing = False` when the user cancels the exit confirmation dialog or if project save fails, and cleared `self.project_dirty = False` upon user discard.
  - **Background Waveform & Story Selection False-Dirty Elimination (`media_batch.py`, `processing.py`, `export_documents.py`)**: Background waveform generation completion, timeline story selection, document/audio exports, and preference updates no longer inadvertently trigger dirty state.
  - **Window Title & State Label Synchronization (`media_batch.py`)**: Ensured `update_window_title()` is called immediately following crash recovery or autosave restore so `save_state_label` always accurately reflects project dirty status.

## v3.9.66-beta
- **Windows Detached Installer Handoff & Window Visibility Fix (`updater.py`, `project_data_purge_dialog.py`, `ui_layout.py`)**:
  - **Explicit `-WindowStyle Normal` Execution (`updater.py`)**: Added `-WindowStyle Normal` parameters to `Start-Process` calls in the PowerShell supervisor script (`rtvs_update_supervisor.ps1`). Previously, spawning `powershell.exe` with `CREATE_NO_WINDOW` caused child `Start-Process` invocations to inherit `Hidden` window style, causing Inno Setup (`RadioTVSegmenter-*-Setup.exe`) to execute invisibly in the background.
  - **Fail-Safe CMD Batch Supervisor Fallback (`updater.py`)**: Added a secondary `.cmd` batch supervisor (`rtvs_update_supervisor.cmd`) utilizing `start "" "%INSTALLER_PATH%"`. The Windows `start` command forces Windows Shell `ShellExecute` with `SW_SHOWNORMAL` (1) and native UAC elevation, guaranteeing the installer GUI wizard opens visibly on screen even if PowerShell is restricted or fails to spawn.
  - **Subprocess Cmd Launch Fallback (`updater.py`)**: Updated Python helper script fallback to `cmd.exe /c start "" "%INSTALLER_PATH%"`, ensuring shell window visibility across all launch paths.
  - **Startup Import Error Hotfix (`project_data_purge_dialog.py`, `ui_layout.py`)**: Fixed `ImportError: cannot import name 'make_dialog_maximizable'` by importing from `core_utils` and adding a backward-compatible re-export in `ui_layout.py`.

## v3.9.65-beta
- **Unsaved Changes Prompt Harmonization & False-Dirty Elimination (`playback_controller.py`, `project_lifecycle.py`, `media_batch.py`, `project_data_purge_dialog.py`)**:
  - **False-Dirty Elimination on UI Playback Controls (`playback_controller.py`)**: Removed erroneous `self.project_dirty = True` flag when updating skip duration (`set_skip_seconds_from_ui`), persisting user preferences directly to `QSettings` without dirtying clean projects.
  - **Standardized Save / Discard / Cancel Prompt Matrix (`project_lifecycle.py`, `media_batch.py`)**: Standardized all project close/open prompts to explicit `Save | Discard | Cancel` choices, aligning `close_project()` and `load_project_file()` with `closeEvent()` and clearing `self.project_dirty = False` immediately upon user discard or successful save.
  - **Eliminated Double-Prompts on New Project Workflow (`project_lifecycle.py`, `media_batch.py`)**: Guaranteed that closing or resetting a project immediately sets `project_dirty = False`, ensuring subsequent media loading dialogs do not re-prompt when opening new media.
  - **Modular Architecture & File Size Compliance (`project_data_purge_dialog.py`, `project_lifecycle.py`)**: Extracted `ProjectDataPurgeDialog` into a dedicated UI dialog submodule, reducing `project_lifecycle.py` from 999 to 864 lines while maintaining 100% backward compatibility via facade re-exports.

## v3.9.64-beta
- **Windows Update Elevation (UIPI) Fix & Pre-Regression Drag-and-Drop Rollback (`updater.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `RadioTVSegmenter.py`, `ui_layout.py`, `playback_controller.py`, `timeline_widgets.py`, `timeline_overview_widget.py`, `transcript_editor.py`)**:
  - **Root-Cause Resolution for Post-Update Drag-and-Drop Lockout (`updater.py`, `RadioTVStorySegmenter.iss`)**: Resolved the Windows User Interface Privilege Isolation (UIPI) elevation loop where installing an update via **Help -> Check for Updates** explicitly invoked `ShellExecuteW(..., 'runas', ...)` on the outer Inno Setup `SetupLdr.e32` bootstrapper (`asInvoker`), causing `[Run] ... runasoriginaluser` to inherit an elevated Administrator token (`TokenElevation = True`) and causing Windows Kernel UIPI to block all OLE drag-and-drop from Medium Integrity `explorer.exe`.
  - **Explorer Shell De-Elevated Post-Install Launch (`RadioTVStorySegmenter.iss`)**: Updated the Inno Setup `[Run]` postinstall entry to launch `{app}\{#MyAppExeName}` via `{win}\explorer.exe`, guaranteeing that even when the installer is launched from an already-elevated session, the new application process spawns under the interactive desktop shell's non-elevated user token.
  - **Standard Invoker Update Hand-Off (`updater.py`)**: Updated the detached update helper to launch the Inno Setup installer via standard `'open'` first (falling back to `'runas'` only if needed) so Inno Setup's outer bootstrapper retains the non-elevated user token while its internal worker handles elevation.
  - **Rollback of Unnecessary Drag-and-Drop Experimental Changes**: Reverted `RadioTVSegmenter.py`, `ui_layout.py`, `playback_controller.py`, `timeline_widgets.py`, `timeline_overview_widget.py`, and `transcript_editor.py` to their clean `v3.9.57-beta` baseline (retaining only the `load_media_file` signal connection fix in `ui_layout.py` and preserving all non-drag-and-drop features from `v3.9.59-beta` and `v3.9.60-beta`).

## v3.9.63-beta
- **Complete Drag-and-Drop Restoration Across All Native Targets (`timeline_widgets.py`, `timeline_overview_widget.py`, `transcript_editor.py`, `RadioTVSegmenter.py`)**:
  - **Comprehensive Widget-Level Event Coverage**: Implemented missing `dragMoveEvent` alongside `dragEnterEvent` and `dropEvent` across `TimelineCanvas`, `TimelineWidget`, and `TimelineOverviewBar`, ensuring continuous mouse movement over the timeline canvas does not cause Windows OLE to drop to `DROPEFFECT_NONE` (?? cursor).
  - **Direct-to-Canvas Audio Ingestion (`timeline_widgets.py`)**: Restored `self.setAcceptDrops(True)` and direct `extract_dropped_file_paths(event.mimeData())` handling on `TimelineCanvas`, emitting `mediaDropped` directly into `_handle_dropped_media_or_project`.
  - **Transcript Window File Dropping (`transcript_editor.py`)**: Wired `InteractiveTranscriptEdit`'s `dragEnterEvent`, `dragMoveEvent`, and `dropEvent` with `extract_dropped_file_paths` so dropping audio/video files directly into the transcript area reliably opens them.
  - **Top-Level Fallback Acceptance (`RadioTVSegmenter.py`)**: Enabled `self.setAcceptDrops(True)` and clean drag events on `MainWindow` as a universal drop target for window borders and background areas.

## v3.9.62-beta
- **Dual-Target Native Drag-and-Drop Restoration for Timeline & Transcript (`playback_controller.py`, `RadioTVSegmenter.py`, `timeline_widgets.py`, `timeline_overview_widget.py`, `transcript_editor.py`, `build_installer.py`)**:
  - **De-overengineered Architecture & Global Interceptor Pruning (`playback_controller.py`, `RadioTVSegmenter.py`)**: Completely removed the application-wide `eventFilter` drag interception in `playback_controller.py` that was consuming events at the `QApplication` level, as well as `MainWindow` drop handlers and `win32_dnd.py` message filter collisions.
  - **Direct-to-Widget Timeline Ingestion (`timeline_widgets.py`, `timeline_overview_widget.py`)**: Restored the clean, native Qt widget-level drop handling on `TimelineCanvas` and `TimelineWidget` using standard `event.mimeData().hasUrls()` and `event.acceptProposedAction()`, dispatching dropped file paths directly to `mediaDropped` and `load_media_file`.
  - **Direct-to-Widget Transcript Ingestion (`transcript_editor.py`)**: Standardized `TranscriptEditor`'s `dragEnterEvent` and `dropEvent` to accept dropped audio/video media files and project archives natively, matching the visual empty-state invitation card (*"Drop an Audio or Video File Here to Begin"*).
  - **Native OLE Integrity**: Preserved unhindered OLE communication between Windows Explorer and Qt's Windows platform plugin (`qwindows.dll`), eliminating drop cursor rejections across installed desktop environments.

## v3.9.60-beta
- **Empty Project Close & Save Prompt Bypass (`project_state_mixin.py`, `media_batch.py`, `project_lifecycle.py`, `project_export.py`, `diagnostic_cloud_and_system_tests.py`)**:
  - **Workspace State Inspection (`is_project_empty()`)**: Added `is_project_empty()` to `ProjectStateMixin` to verify whether the workspace contains loaded audio (`audio_file`), an associated project file (`project_file`), transcript text/segments (`transcript`), or defined stories (`stories`).
  - **Silent Media Ingestion on Blank Canvas**: Updated `prepare_for_new_media()` in `media_batch.py` so opening or dragging an audio file into an empty workspace proceeds immediately without prompting *"The current project has unsaved changes. Would you like to save it before closing?"*.
  - **Silent Project Reset & Clean State Guarantee**: Updated `close_project()` and `load_project_file()` in `project_lifecycle.py` and `closeEvent()` in `project_export.py` to bypass confirmation dialogs when the workspace is empty, and ensured `self.project_dirty = False` is explicitly reset on project close so subsequent file operations always start with a clean state.

## v3.9.59-beta
- **Preferences Real-Time Category & Setting Search Filter (`preferences_dialog.py`, `diagnostic_loudness_tests.py`)**:
  - **Inline Search Box Above Navigation Tabs**: Added a dedicated settings search box directly above the category navigation sidebar on the left of the Preferences dialog, providing natural, desktop-standard discoverability.
  - **Instant Multi-Page Setting Text Indexing**: As the user types (e.g. *whisper*, *loudness*, *theme*, *gpu*, *shortcuts*), the dialog inspects labels, checkboxes, groupbox titles, combobox entries, table items, and tooltips across all stacked pages in real time (~2ms).
  - **Dynamic Category Filtering & Match Badging**: Automatically hides non-matching category tabs and appends live match count badges to matching categories (e.g. `AI Models (7)`, `Audio Settings (4)`). If the active tab no longer matches, focus auto-switches to the first matching category.
  - **Fluid Keyboard Navigation**: Added `Escape` key handling to instantly clear the search filter and restore full category visibility without closing the dialog, and `Down` arrow handling to transition focus seamlessly from the search field into the category list. Clearing the search box restores all original category names and visibility immediately.

## v3.9.58-beta
- **Windows Drag-and-Drop Ingestion Overhaul (`core_utils.py`, `playback_controller.py`, `ui_layout.py`, `transcript_editor.py`, `installer/Windows/RadioTVStorySegmenter.iss`)**:
  - **Inno Setup Non-Elevated Launch (`runasoriginaluser`)**: Added `runasoriginaluser` to the `[Run]` directive in `RadioTVStorySegmenter.iss`. Previously, when users installed or updated the application and checked "Launch Radio & TV Segmenter", the process was launched with inherited Administrator elevation. Windows User Interface Privilege Isolation (UIPI) silently blocks all drag-and-drop messages (WM_DROPFILES and OLE) from non-elevated Windows Explorer to elevated processes. The `runasoriginaluser` flag ensures the app launches with standard user credentials so Explorer drag-and-drop works out of the box.
  - **Windows URI Leading Slash Regex Stripper (`core_utils.py`)**: Corrected `_clean_path_candidate` in `core_utils.py` using a robust regex (`^/+(?=[a-zA-Z]:[\/])`) to cleanly strip leading slashes from Windows drive letter URIs (e.g. `file:///C:/path`, `/C:/path`, `///C:/path`), resolving an index offset bug that prevented `Path.resolve().exists()` from verifying dropped media paths.
  - **Window-Wide & Central Widget Drop Acceptance (`ui_layout.py`, `playback_controller.py`, `transcript_editor.py`)**:
    - Enabled `setAcceptDrops(True)` on the main window's `central_widget`.
    - Expanded `eventFilter` in `playback_controller.py` so any drag of supported media (`.wav`, `.mp3`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.wma`, `.aiff`, `.mp4`, `.mov`, `.mkv`, `.webm`, etc.) or project archives (`.rtvs`, `.rtvs3`) over the timeline, central widget, story list, transcript, or window background displays the green Copy cursor and dispatches cleanly to `load_media_file` or `load_project_file`.
    - Fixed undefined `open_media_file` callback in `story_list.filesDropped` by connecting to unified `_handle_dropped_media_or_project`.
- **Simultaneous Search Auto-Highlighting & Live Match Counter (`playback_preferences.py`, `transcript_timeline_sync_mixin.py`, `transcript_selection_mixin.py`, `ui_layout.py`, `transcript_editor_dialogs.py`, `theme_qss.py`)**:
  - **Simultaneous Document-Wide Highlighting**: Typing in the transcript search bar (or Find & Replace dialog) immediately highlights every occurrence of the search phrase across the entire transcript using non-destructive `QTextEdit.ExtraSelection` (theme-aware warm amber highlight for inactive matches and vibrant cyan/sky highlight for the active match), providing instant visual density awareness.
  - **Live Match Counter Badge (`X / Y`)**: Added a compact, high-visibility match counter badge (`1 / 14` or `0 / 0`) directly beside the transcript search bar and inside the Find & Replace dialog that dynamically updates as you type or cycle through matches.
  - **Bidirectional 'Find Prev' and 'Find Next' Controls**: Added paired 'Find Prev' and 'Find Next' buttons directly in the transcript search bar and Find & Replace dialog for rapid one-click mouse navigation alongside `Enter` / `Shift+Enter` and `Ctrl+G` / `Ctrl+Shift+G`.
  - **Seamless Real-Time Synchronization**: Search highlights and match counters automatically synchronize bidirectionally between the transcript search bar, transcript editor, and Find & Replace dialog.

## v3.9.56-beta
- **Find & Replace Dialog In-Focus Shortcut Interception (`transcript_editor_dialogs.py`, `playback_preferences.py`)**:
  - Fixed Ctrl+G and Ctrl+Shift+G not triggering while focus is inside the Find & Replace dialog (including `find_input`, `replace_input`, and child controls). Replaced problematic modeless QShortcut instances with direct keyPressEvent interception across `find_input`, `replace_input`, and FindReplaceDialog, circumventing Qt's ambiguous shortcut suppression with the main window's application action.
  - Added full keyboard navigation within the Find dialog: Enter executes Find Next, Shift+Enter executes Find Previous, and Ctrl+F refocuses and selects the search query.
  - Resolved backward search active selection loop: in both FindReplaceDialog.find_prev and trigger_find_prev, repositioned cursor to the start of the current selection before querying backward, preventing the search from repeatedly re-matching the active word.
  - Added guaranteed ensureCursorVisible() and status bar feedback on every dialog search pass.

## v3.9.55-beta
- **Inline Transcript Search & Find/Replace Synchronization (playback_preferences.py, ui_layout.py, ui_dialog_launchers.py, 	ranscript_editor_dialogs.py, ui_menus.py, shortcuts/schema.py, shortcuts/manager.py, RadioTVSegmenter.py)**:
  - **Inline Search Navigation**: Pressing Enter or clicking Find Next in the transcript search box now executes an inline search cycling through matches directly in the transcript view with automatic wrap-around and status bar feedback, without popping open the modal dialog.
  - **Backward Search Support**: Pressing Shift+Enter in the transcript search box executes an inline Find Previous search backward through the transcript.
  - **Modern Standard Keyboard Shortcuts (Ctrl+G / Ctrl+Shift+G)**: Standardized Find Next to Ctrl+G (Cmd+G on macOS) and Find Previous to Ctrl+Shift+G (Cmd+Shift+G on macOS) across both the main window and the Find & Replace dialog, eliminating non-functional legacy F3/Shift+F3 key conflicts caused by ambiguous QShortcut/QAction overloads.
  - **Conflict-Free Shortcut Migration**: Reassigned Glossary & Custom Vocabulary to Ctrl+Alt+V (Cmd+Alt+V on macOS), resolving the shortcut collision with Find Previous. Added automatic legacy shortcut migration in ShortcutsManager to seamlessly transition existing preferences.
  - **Two-Way Search Term Synchronization**: Ctrl+F (or Edit > Find and Replace...) now automatically pre-populates the Find & Replace dialog with whatever term is entered in the transcript search box (or active transcript text selection) and selects the text for immediate editing. Finding next/previous in the dialog updates the transcript search box in real time.

## v3.9.54-beta
- **Interactive Transcript Threshold Auto-Scroll & Dual Settings Toggles (	ranscript_timeline_sync_mixin.py, 	ranscript_editor.py, playback_controller.py, ui_menus.py, preferences_tabs_media.py, preferences_dialog.py, RadioTVSegmenter.py)**:
  - Implemented intelligent threshold-based auto-scrolling in InteractiveTranscriptEdit: when playback approaches the bottom ~18% of the visible viewport or moves off-screen, the view smoothly scrolls to position the active spoken line at the upper third (~25%) of the screen, providing ample forward reading space without continuous word-by-word micro-jitter.
  - Added user interaction safety guards: auto-scroll is safely suppressed during text editing mode (Ctrl+E), active text selection drags, and manual scrolling (mouse wheel or scrollbar drag temporarily disengages auto-scroll until seeking, toggling playback, or clicking a transcript link).
  - Added user-configurable toggle in **View > Transcript > Auto-Scroll During Playback** and in **Preferences > Playback & Timeline > Transcript Playback Scroll** (default: enabled), persisted in QSettings.

## v3.9.53-beta
- **Updater Check & Cached Installer State Disambiguation (`updater.py`)**:
  - Resolved an issue in `CheckUpdateDialog` where having a previously downloaded installer package in `%APPDATA%/RTVS3/updates/` falsely caused the dialog to display `✓ Update package for <version> is already downloaded and ready to install.` and show a `Restart & Install` button even when the user was already running that version.
  - Added strict `is_current` and `is_top_release` verification before evaluating cached installer packages, ensuring the dialog accurately confirms `✓ Radio & TV Segmenter is up to date (v{PROJECT_VERSION})` and presents a `Check Again` action when running the latest release.

## v3.9.52-beta
- **AMD Ryzen AI Strix Point Hardware Probe & UMA Telemetry (`scripts/setup_local_ai.py`) [Milestone 2.1]**:
  - Implemented zero-dependency hardware detection for AMD Ryzen AI 9 HX 370 (12 cores / 24 threads), Radeon 890M (`gfx1150`, RDNA 3.5), AMD XDNA 2 NPU (`DEV_17F0`), and unified memory architecture (64GB LPDDR5x with 32GB dedicated UMA VRAM).
  - Calculated optimal runtime parameters for Ollama local inference (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_KEEP_ALIVE=60m`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_IGPU_ENABLE=1`).
- **Tiered Local AI Model Suite & D: Drive Consolidation (`scripts/setup_local_ai.py`) [Milestone 2.2]**:
  - Migrated Ollama model storage to `D:\OllamaModels`, freeing C: drive SSD capacity and activating ROCm 7.1 + Vulkan GPU acceleration on Radeon 890M.
  - Provisioned, SHA256-verified, and GPU-benchmarked the complete four-tier quantized coding model suite: `qwen2.5-coder:1.5b` (50.7 tok/s), `7b` (17.4 tok/s), `14b` (8.3 tok/s), `32b` (4.2 tok/s), plus `nomic-embed-text` (semantic vector indexing), `minicpm-v` (29.9 tok/s Qwen2 vision model), and `deepseek-r1:14b` (9.6 tok/s chain-of-thought reasoning engine).
- **Local Server Health Check & 0-Latency Prompt Cache Pinning (`scripts/setup_local_ai.py`) [Milestone 2.3]**:
  - Integrated repository symbol map from `.codemaps/symbol_index.json` (~3,710 tokens across all 155 modules) into Ollama's KV prompt cache, achieving 58.6x faster prompt retrieval (39.3 ms vs 2,305 ms cold compilation).
  - Registered tuned model variants (`qwen2.5-coder:*-rtvs`) enforcing 32k/16k working context window limits with 8-bit quantized KV cache (`q8_0`).
- **Token-Thrift IDE Configuration & Rule Provisioner (`scripts/ide_config.py`, `scripts/setup_local_ai.py`, `.vscode/settings.json`, `.continue/config.json`, `.clinerules`, `.cursorrules`) [Milestone 2.4]**:
  - Automated zero-token setup via `python scripts/setup_local_ai.py --setup-ide`, creating fully wired configurations for Continue, Cline, Cursor, and VS Code.
  - Wired tiered model routing: `qwen2.5-coder:1.5b-rtvs` for real-time tab autocomplete, `14b-rtvs` for fast chat/edits, `32b-rtvs` for architecture, `deepseek-r1:14b` for concurrency proofs, `minicpm-v` for UI inspection, and `nomic-embed-text` for semantic indexing.
  - Enforced project architectural invariants in `.clinerules` and `.cursorrules`: symbol-first targeted range reads, 800-line budget ceilings, minimal contiguous diff replacements, and clean typography.

- **Token-Budget Task-to-Model Router & CI Invariant Verifier (`scripts/task_router.py`, `scripts/setup_local_ai.py`) [Milestone 2.5]**:
  - Implemented automated task routing (`python scripts/setup_local_ai.py --route "<task>"`) mapping work to model tiers based on file length (<300 lines -> 7B/14B; refactoring -> 32B; concurrency -> R1 14B; UI -> MiniCPM-V).
  - Added CI invariant verifier (`python scripts/setup_local_ai.py --verify-ci`) ensuring strict core module decoupling from dev scripts, full Python syntax integrity across all 157 modules, and version synchronization.
- **Multi-Tier AI Safety, Reverse-Caller Impact Analysis & Pre-Flight Gate (`docs/VERSION_CONTROL_GUIDE.md`, `scripts/task_router.py`, `scripts/bundle_context.py`, `scripts/dev_check.py`) [Milestone 2.6]**:
  - Authored comprehensive `docs/VERSION_CONTROL_GUIDE.md` detailing the 3-tier branching model (`stable`, `beta`, `dev`), disposable AI task branches (`ai/*`), snapshot rollbacks, and recovery cheat sheets.
  - Implemented AST reverse-caller and blast-radius analyzer (`python scripts/task_router.py --impact <symbol>`) providing sub-second call site mapping before method signature edits.
  - Built one-shot context bundler CLI (`python scripts/bundle_context.py <symbol>`) packaging targeted symbol slices, `.pyi` typing stubs, caller patterns, and test commands into a token-bounded (~1,200 token) markdown bundle for local AI models.
  - Created fast pre-flight developer gate (`python scripts/dev_check.py`) verifying syntax integrity, `.pyi` stub sync, preview sync, line budget, and change-aware Tier 2 tests in <10 seconds.
- **Single Responsibility & Desktop Domain Separation Invariant (`scripts/modular_audit.py`, `scripts/dev_check.py`, `AGENTS.md`, `ARCHITECTURE.md`, `roadmap.txt`) [Milestone 2.7]**:
  - Formalized strict single-purpose domain separation as an unbreakable architectural invariant across the 4 core domains: UI presentation, worker concurrency, headless processing engines, and data models/serialization.
  - Implemented automated AST domain collision analyzer (`python scripts/modular_audit.py --check-srp [file]`) detecting and preventing incompatible domain mixtures (e.g. UI widgets co-located with audio DSP engines or background QThreads).
  - Integrated SRP collision checks directly into the pre-flight developer gate (`scripts/dev_check.py`) to guarantee zero architectural drift on future development.
  - Refocused roadmap monolithic file modularization milestones on purpose and responsibility decoupling in addition to line budgets.

## v3.9.51-beta

- **Debounced Speaker Table Disk Writes (`speaker_dialogs.py`) [P4-04]**:
  - Implemented 500ms debounced project saving (`_save_debounce_timer`) in `SpeakerManagerDialog` during inline speaker name editing and cell navigation, eliminating rapid synchronous full-project gzip disk writes and UI stutter.
  - Added guaranteed `_flush_debounced_save()` across dialog `accept()`, `reject()`, and `closeEvent()`, ensuring zero data loss when exiting the dialog.
- **Story Excerpt Undo/Redo Snapshots (`ui_layout.py`) [P6-08]**:
  - Integrated `auto_generate_selected_story_excerpt()` with project-level undo history via `commit_story_change(old_stories, new_stories, "Auto-generate Excerpt")`.
  - Captures full pre-mutation story state snapshots so generated excerpts can be immediately reverted or restored via Ctrl+Z / Ctrl+Shift+Z without corrupting custom excerpts.
- **Core Module Plugin Decoupling & Architectural Invariant Enforcement (`plugin_base.py`, `plugins/base.py`, `export/dialog.py`, `plugin_dialogs.py`, `model_management.py`) [P5-03]**:
  - Extracted core plugin interface contracts (`PluginManifest`, `BasePlugin`, `ExportDestination`) into `plugin_base.py`, establishing a clean interface boundary at the application root.
  - Preserved 100% backward compatibility for all plugins and test harnesses through facade re-exports in `plugins/base.py`.
  - Decoupled `export/dialog.py` and `plugin_dialogs.py` from `plugins.base` by importing directly from `plugin_base`.
  - Replaced hard import of `plugins.translation.worker` in `model_management.py` with dynamic import and fallback `_DummyTranslationWorker`, eliminating crashes when the translation plugin is absent or disabled.
- **UI Typography Cleanliness & Decorative Emoji Removal (`comment_widgets.py`, `shortcuts/dialogs.py`, `voice_profile_dialog.py`, `id3_editor.py`, `benchmark_dialog.py`, `plugins/wordpress/plugin.py`, `plugins/youtube/guide_dialog.py`) [P6-06]**:
  - Removed decorative emojis and unrequested glyphs across action buttons, dialog titles, and status labels:
    - `comment_widgets.py`: Cleaned action buttons to "Delete Comment", "Edit", and panel header to "Comments (0)".
    - `shortcuts/dialogs.py`: Replaced "📍 Select in Table" with clean typography "Select in Table"; stripped decorative `✅`, `ℹ️`, `⚠️` symbols from candidate lookup results.
    - `voice_profile_dialog.py`: Cleaned hints toggle button and groupbox to "Usage Hints" and "Acoustic Voice Profile Matcher — Quick Usage Guide".
    - `id3_editor.py`: Cleaned "⚡ Auto-Fill from Project" to "Auto-Fill from Project" and removed status label lightning bolts.
    - `benchmark_dialog.py`: Cleaned workload preset combobox and action button text ("Quick Mode", "Standard Benchmark", "Sustained Stress", "Full 30-Min Endurance", "Download Sample").
    - `plugins/wordpress/plugin.py`: Cleaned "🗗 WordPress Post Settings..." to "WordPress Post Settings...".
    - `plugins/youtube/guide_dialog.py`: Removed decorative clipboard emoji from notice banner.
    - Retained transcript highlight color circle emojis (`🟡`, `🟢`, etc.) and main window comments toggle (`💬 Comments`) per user specification.
- **Export Dialog Vestigial Cleanup & Reorder List Parity (`export/dialog.py`, `export/reorder_dialog.py`) [P6-09, P6-10]**:
  - Cleaned unpopulated `self._temp_preview_files` set and dead loop in `UnifiedExportDialog.done()` [P6-09].
  - Restored `"timeline"` (`Timeline & DAW Project Files`) to the default fallback available destinations list in `ReorderExportDestinationsDialog` [P6-10].
- **Project Save/Load Pipeline Reliability & Waveform Peak Restitution (`project_lifecycle.py`, `project_state_mixin.py`, `media_batch.py`, `project_export.py`)**:
  - Fixed disabled File > Save Project / Save Project As menu actions on project load and when project modifications occur.
  - Added instant async loading of cached waveform peaks (`.cache/peaks/`) and background video thumbnail generation upon opening saved projects, resolving blank timeline views.
  - Restored timeline zoom and scroll offsets from project session metadata.
  - Hardened media path resolution with fallback to relative/absolute file searches and passed `project_file` context when writing peak caches.
  - Removed ambiguous automatic adjacent project restoration and eliminated orphaned candidate search routines (`find_adjacent_project`), establishing strict separation between File > Open Media (clean media slate) and File > Open Project (session restoration).
- **PDF Proportional Font Word-Wrap Accuracy & Idempotency (`export/pdf.py`) [P6-07]**:
  - Replaced monospace character width approximation with standard Adobe Helvetica AFM proportional glyph width tables, preventing word-wrap overflow and margin clipping on uppercase text and acronyms.
  - Added typographic Unicode character normalization for smart quotes (`“`, `”`, `‘`, `’`), prime quotes, em/en-dashes, and special whitespace before CP1252 encoding, eliminating unwanted `?` corruption.
  - Added idempotent `_finished` flag and cached PDF byte storage in `finish()` / `get_pdf_bytes()` preventing accidental empty trailing page generation on repeated calls.
- **Changelog Historical Archive Roll (`CHANGELOG.md`, `CHANGELOG_ARCHIVE.md`) [P7-06]**:
  - Pruned historical releases prior to `v3.9.0-beta.1` (`v3.8.0-stable` through `v3.8.9-beta.19`) into `CHANGELOG_ARCHIVE.md`, reducing `CHANGELOG.md` footprint by ~62 KB.

## v3.9.50-beta
- **Pipeline Fault Recovery & Skip Stage (`processing.py`, `ui_layout.py`, `project_state_mixin.py`, `story_detection_processing.py`, `diarization_processing.py`, `transcription_processing.py`, `translation.py`, `theme_qss.py`)**:
  - **Dynamic Skip Stage Button (`ui_layout.py`, `processing.py`, `project_state_mixin.py`)**: Added a dedicated "Skip Stage" button alongside Cancel that dynamically appears whenever a multi-stage pipeline is running with queued downstream stages. Cleanly terminates the active worker and immediately advances the pipeline queue without losing remaining stages.
  - **Stage Completion & Error Fault Recovery (`story_detection_processing.py`, `diarization_processing.py`, `transcription_processing.py`, `translation.py`)**: Wrapped stage completion callbacks in robust exception handlers that prevent the UI and progress bar from locking up if result processing fails, and added user prompts on worker errors offering to skip the failed stage and continue with the rest of the pipeline.
- **Keyboard Usability & Transport Customization (`shortcuts/schema.py`, `shortcuts/manager.py`, `playback_controller.py`, `RadioTVSegmenter.py`, `ui_menus.py`, `story_crud_mixin.py`, `transcript_editor_dialogs.py`, `playback_preferences.py`)**:
  - **Complete Shortcut Customization Coverage (`shortcuts/schema.py`, `RadioTVSegmenter.py`, `ui_menus.py`)**: Wired all 24 shortcut schema definitions previously lacking `attr_name` (now 79/79 actions fully customizable), registering corresponding QActions and QShortcuts on MainWindow and adding Find Next / Find Previous and Configure Audio Fades to the Edit menu [P4-01].
  - **Customizable Transport & Text Focus Mitigations (`playback_controller.py`, `shortcuts/manager.py`, `story_crud_mixin.py`, `timeline_widgets.py`)**: Bound Spacebar play/pause and all transport/navigation shortcuts to user preferences with `_is_text_entry_focused()` focus guards, preventing key-stealing in QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox, and editable transcript modes [P4-02].
- **Concurrency, Batch Reliability & Export Interchange Fidelity (`transcription_processing.py`, `diarization_processing.py`, `story_detection_processing.py`, `media_batch.py`, `export/timeline.py`, `export_story_pipeline.py`, `export/dialog.py`, `processing.py`, `project_export.py`, `diagnostic_dialog.py`)**:
  - **Stale Background Worker State Overwrite Guard (`transcription_processing.py`, `diarization_processing.py`, `story_detection_processing.py`)**: Bound transcription and diarization completion callbacks to the active media path (`_transcription_source_media`, `_diarization_source_media`), discarding background results if the user switched media before the worker finished [P1-03].
  - **Non-Modal Batch Error Handling (`media_batch.py`, `transcription_processing.py`, `diarization_processing.py`, `story_detection_processing.py`)**: Replaced blocking modal `QMessageBox` error popups during batch processing with non-modal activity log warnings and automatic advance to `_batch_next_media`, ensuring unattended multi-file batch runs are never halted by a single failing file [P1-04].
  - **Worker Lifecycle & Re-entrancy Guards (`media_batch.py`, `project_export.py`, `processing.py`, `diagnostic_dialog.py`)**:
    - Added lingering video thumbnail worker thread tracking to prevent Qt thread teardown crashes [P3-02].
    - Added user notification on export thumbnail generation timeout in `project_export.py` [P3-03].
    - Bound `translate_button.setEnabled(has_transcript)` in `processing.py` to prevent invalid translation triggers [P3-04].
    - Added `try ... finally: self.finished.emit()` in `diagnostic_dialog.py:TestRunnerWorker.run` to guarantee background diagnostic worker threads cleanly signal completion even on uncaught errors.
  - **Samplitude EDL Destination Timecode Contiguity (`export/timeline.py`)**: Fixed destination timecode tracking in `generate_samplitude_edl` when `unselected_audio_mode == "exclude"`, using a contiguous `dst_cursor` placement so destination timecode starts at 00:00:00:00 and advances contiguously across selected regions without dead air gaps [P6-05].
  - **DAW Export Format Matrix Unification & Line Budget Hygiene (`export_story_pipeline.py`, `export/dialog.py`)**:
    - Harmonized DAW project parameters (sample rates, track names, and scopes) across story and full-episode export pipelines [P6-04].
    - Consolidated duplicate DAW timeline writing routines in `export_story_pipeline.py` into a shared `_export_daw_interchange_files` helper, maintaining the strict 1,000-line budget invariant (964 lines).
  - **Permanent Audit Documentation (`docs/audit/`)**: Migrated all 8 comprehensive audit phase reports and roadmap specifications into versioned repository documents for permanent developer reference.

## v3.9.49-beta
- **Thread-Affinity & Cross-Thread Qt Warning Elimination (`diagnostic_core_tests.py`, `diagnostic_export_tests.py`, `speaker_dialogs.py`)**:
  - Eliminated `QObject: Cannot create children for a parent that is in a different thread` and `QBasicTimer::stop: Failed. Possibly trying to stop from a different thread` warnings in the console when running diagnostic suites from within the GUI application (`DiagnosticDialog` worker `QThread`).
  - Refactored `diagnostic_core_tests.py` mock host window from `QWidget` to pure-Python `SpeakerDialogRefinementMixin`, preventing secondary worker threads from attempting top-level native window registration.
  - Implemented `is_main_gui_thread` thread-affinity branching in `diagnostic_core_tests.py` and `diagnostic_export_tests.py` (matching the pattern in `diagnostic_loudness_tests.py`), executing full interactive UI widget lifecycles when run on the main thread and verifying business logic and class invariants when executed inside secondary worker threads.
  - Added inline cell editor cleanup prior to dialog teardown, eliminating orphaned `QLineEdit` cursor blink timers (`QBasicTimer`).

## v3.9.48-beta
- **Speaker Sample Player Thread-Affinity Guard & Diagnostic Console Hygiene (`speaker_dialogs.py`, `diagnostic_core_tests.py`)**:
  - Resolved `QObject: Cannot create children for a parent that is in a different thread` cross-thread parenting warnings and unwanted FFmpeg hardware probe messages in the application console.
  - Added thread-affinity verification (`_is_gui_thread()`) to `SpeakerManagerDialog` across `_populate()`, `_play_speaker_sample()`, and `_stop_sample_playback()`.
  - Prevented background worker threads (such as `DiagnosticDialog` worker threads) from invoking hardware soundcard media loading on secondary threads while preserving 100% normal audio playback when accessed from the main GUI window.
  - Guarded `_preview_player` media engine triggers during automated unit test suite execution in `diagnostic_core_tests.py`.

## v3.9.47-beta
- **Active Danger Zone: Critical Data Loss, Security & Instant Crash Resolution (`media_batch.py`, `updater.py`, `story_metadata_dialog.py`, `plugins/wordpress/client.py`, `ui_layout.py`, `export/audio.py`, `project_state_mixin.py`)**:
  - **Batch Queue Zero-Byte Overwrite Protection (`media_batch.py`)**: Fixed critical bug where enabling "Skip already-transcribed files" (`skip_existing`) invoked `_batch_export_current()` with `transcript=None`, clobbering existing valid transcript files on disk with 0-byte blanks. Guarded export routines against None transcripts.
  - **Updater SHA-256 Checksum Verification & Unverified Warning (`updater.py`)**: Enforced SHA-256 package verification in `DownloadUpdateWorker`, recording checksum status. Added an explicit confirmation warning dialog in `_install_and_restart()` if an update lacks a verified SHA-256 checksum on GitHub, preventing unverified installer execution.
  - **Unsaved Work Guard Prior to Update Restart (`updater.py`)**: Added a top-level project dirty inspection prior to updater restart. If unsaved project edits exist, users are prompted with Save / Discard / Cancel dialog to prevent data loss. Extended the shutdown watcher wait interval from 0.8s to 3.0s.
  - **WordPress Dialog Import Resilience & Decoupling (`story_metadata_dialog.py`)**: Replaced direct hard import of `plugins.wordpress.wp_tab_widget.WordPressExportTabWidget` with safe dynamic import and fallback notice widget, eliminating crashes when the WordPress plugin is absent, disabled, or uninstalled, and adhering to core-plugin architectural boundaries.
  - **HTTP Redirect Credential Protection (`plugins/wordpress/client.py`)**: Added `_is_safe_redirect()` validation to strip WordPress credentials and basic auth headers whenever a server redirect crosses domains or downgrades from HTTPS to plain HTTP, preventing credential leakage to untrusted third parties.
  - **Story Excerpt Type Safety Crash Fix (`ui_layout.py`)**: Fixed dictionary key iteration crash in `auto_generate_selected_story_excerpt()`. Safely extracted segment arrays from `self.transcript` dictionary objects (`{"segments": [...]}`) and guarded segment element types.
  - **FFmpeg OS Pipe Buffer Deadlock Elimination (`export/audio.py`)**: Replaced blocking `proc.poll()` / `time.sleep()` loop with non-blocking `proc.communicate(timeout=0.05)` pipe draining inside `_run_ffmpeg_export()`. Completely eliminates process deadlocks when FFmpeg emits >64KB to stdout/stderr. Added `-nostats` and `-loglevel error` to reduce pipe saturation and processing overhead.
  - **Undo/Redo File Dialog Suppression on Unsaved Projects (`project_state_mixin.py`)**: Suppressed modal "Save Project As" file chooser dialogs when pressing Ctrl+Z (undo) or Ctrl+Shift+Z (redo) on new, unsaved projects by checking `getattr(self, "project_file", None)` prior to invoking `self.save_project()`.

## v3.9.46-beta
- **Codebase De-Bloat & Orphaned Code Eradication (`timeline_canvas.py`, `preferences_tabs.py`, `voice_profile_matcher_mixin.py`, `timeline_envelope.py`, `build_installer.py`)**:
  - Permanently eliminated **3,085 lines of orphaned dead duplicate code** identified during the comprehensive architectural audit:
    - Deleted `timeline_canvas.py` (1,344 lines) and `timeline_envelope.py` (51 lines), which were fully superseded by `timeline_widgets.py` and `waveform_envelope.py` with zero active imports.
    - Deleted `preferences_tabs.py` (1,142 lines), which was fully superseded by `preferences_tabs_core.py` and `preferences_tabs_media.py`.
    - Deleted `voice_profile_matcher_mixin.py` (548 lines), an unimported byte-for-byte duplicate of `voice_profile_ops_mixin.py`.
  - Reduced the repository's modules exceeding the 1,000-line ceiling from 16 down to 14, and total project files from 157 down to 153.
  - Cleaned up obsolete build and scaffold artifacts in the repository root: removed stale Inno Setup script `RadioTVStorySegmenter.iss` (dated Oct 23, superseded by `installer/Windows/RadioTVStorySegmenter.iss`) and dead Vite/React scaffold configuration files (`vite.config.ts`, `eslint.config.js`, `tailwind.config.js`, `postcss.config.js`, `tsconfig.json`).
  - Added missing PyInstaller hidden-imports in `build_installer.py` for new export engine submodules: `--hidden-import export.audio` and `--hidden-import export.timeline`, preventing dynamic import failures in frozen standalone distributions.
  - Re-synchronized `roadmap.txt` to strict $N-1$ sliding-window compliance, pruning historical milestones older than $N-1$ to reduce prompt context tokens.


## v3.9.45-beta
- **Diagnostic Test Bench Background Worker Thread-Safety & UI Hang Resolution (`core_utils.py`, `diagnostic_export_tests.py`, `preview_manager.py`)**:
  - Resolved an application-wide freeze and "(Not Responding)" lockup occurring during the System Diagnostic Test Bench when executing the `WordPress Export Scope Post Builder` diagnostic check.
  - Added thread-affinity guards to `apply_window_titlebar_theme` and its deferred callback `_deferred_titlebar_theme` in `core_utils.py`: verified `QThread.currentThread() == app.thread()` prior to querying native OS window handles (`widget.winId()`).
  - Prevented Win32/Qt cross-thread window creation deadlock where worker threads instantiating modeless export dialogs (`UnifiedExportDialog`, `StoryMetadataDialog`) synchronously requested native OS platform window handles (`HWND`) while the main GUI thread event loop was blocked waiting on worker task progression.
  - Added transient widget cleanup (`deleteLater()`) across test scopes in `diagnostic_export_tests.py` to prevent orphaned QWidget references during headless and graphical test bench runs.
  - Fixed escaped template literals in `preview_manager.py` to resolve Python `SyntaxWarning` notifications during runtime inspection.

## v3.9.44-beta
- **Application-Wide Keyboard Shortcut Alignment & 79-Action Schema Harmonization (`shortcuts/schema.py`, `ui_dialog_launchers.py`, `shortcuts/manager.py`, `README.md`)**:
  - Restored true application keybindings across the central shortcut schema, aligning Preferences to `Ctrl+P` (macOS: `Cmd+P`), Glossary / Terminology to `Ctrl+Shift+G`, Add Comment to `Ctrl+M`, Manage AI Models to `Ctrl+Alt+M`, Multi-Stage Pipeline to `Ctrl+R`, ID3 Tag Editor to `Ctrl+Shift+I`, and Timeline Zoom to `+` / `-`.
  - Added 28 missing canonical actions to `shortcuts/schema.py` and the F1 Reference table, including the full AI Processing Pipeline (Transcribe `Ctrl+T`, Detect Speakers `Ctrl+D`, Detect Stories `Ctrl+Shift+A`, Translate `Ctrl+Shift+L`, Regenerate Waveform `Ctrl+Shift+W`, Regenerate Thumbnails `Ctrl+Shift+T`, Normalize Loudness `Ctrl+Alt+N`), all Panel & View Toggles (Timeline `Alt+1`, Transcript `Alt+2`, Stories `Alt+3`, Activity `Alt+4`, Comments Sidebar `Ctrl+Alt+C`, Comment Highlights `Ctrl+Alt+H`, Waveform `Ctrl+Alt+W`, Thumbnails `Ctrl+Alt+T`, Video Preview `Ctrl+Shift+V`, Speaker Labels `Ctrl+Alt+S`, Timestamps `Ctrl+Alt+I`), Core Editing (Undo `Ctrl+Z`, Redo `Ctrl+Shift+Z`), and Diagnostic Utilities.
  - Linked 100% of action attribute names directly to `MainWindow` and `ui_menus.py` (e.g. `pref_action`, `save_action`, `save_as_action`, `export_action`), ensuring user customizations in Preferences -> Keyboard Shortcuts immediately and reliably bind to application menus and toolbars.
  - Resolved transport seek duplicates by mapping aliases (`seek_backward`, `seek_forward`, `seek_start`, `seek_end`) cleanly in `ACTION_ALIASES`, eliminating redundant rows in the F1 reference dialog.
  - Completely synchronized the Markdown reference table in `README.md` to document all 79 active shortcuts across 8 canonical categories.

## v3.9.43-beta
- **Configurable Speaker Sample Preview Duration in Preferences (`preferences_tabs_media.py`, `preferences_dialog.py`, `preferences_reset.py`, `speaker_dialogs.py`)**:
  - Added a dedicated "Speaker Sample Preview Length" control (`QDoubleSpinBox`, 1.0s to 15.0s, default 3.0s) to the **Story Detection & Diarization** preferences tab.
  - Wired settings persistence to `QSettings` (`speaker_sample_duration`), enabling users to customize the audition length for representative speaker voice clips across the application.
  - Updated `SpeakerManagerDialog` (`speaker_dialogs.py`) to dynamically read `_get_sample_duration()`, selecting candidate utterances and auditioning audio according to user preferences, with dynamic tooltip feedback showing the configured sample length.
  - Integrated full factory defaults restoration and category reset support in `preferences_reset.py` and `preferences_reset_dialog.py`.
- **Open-Source AI & Speech Attribution Synchronization (`playback_preferences.py`)**:
  - Updated the **Help -> About Radio & TV Story Segmenter** dialog to explicitly credit **WeSpeaker** and **ONNX Runtime** (`Apache 2.0 / MIT`), aligning the dialog with `NOTICES.txt` and `ARCHITECTURE.md` as the primary on-device neural speaker diarization engines.

## v3.9.42-beta
- **Dynamic Single-Source-of-Truth F1 Keyboard Shortcuts Reference & Live Search (`ui_dialog_launchers.py`, `README.md`)**:
  - Dynamically generated the F1 Keyboard Shortcuts Reference dialog in `ui_dialog_launchers.py` (`show_shortcuts_dialog`) directly from `ShortcutsManager` and active keybinding overrides, eliminating outdated static HTML tables and ensuring 100% synchronization forever.
  - Added real-time instant search and filtering toolbar (`QLineEdit`) at the top of the dialog, allowing users to quickly search shortcuts by action name, key sequence, category, or description.
  - Grouped all 51 canonical application shortcuts into clean, structured tables matching canonical categories: *File & Project*, *Playback & Transport*, *Story & Segment Editing*, *Search & Transcript Tools*, *Timeline & Navigation*, and *Help & Diagnostics*.
  - Added theme-adaptive styling supporting dark, light, and high-contrast modes, rendering keyboard badges with `<kbd>` tags and displaying descriptive tooltips/subtitles for all actions.
  - Retained the "Customize Shortcuts..." button connecting directly to the Keyboard Shortcuts tab in Preferences for rapid customization.
  - Synchronized `README.md` keyboard shortcuts documentation to reflect all 51 active shortcuts, canonical categories, accurate platform defaults (Windows/Linux and macOS), and detailed descriptions.

## v3.9.41-beta
- **Direct Inline Speaker Renaming & Tab Progression (`speaker_dialogs.py`, `diagnostic_core_tests.py`)**:
  - Implemented direct inline double-click editing on the "Speaker Name / Alias" cell in the speaker management table with seamless Tab key progression (Milestone 11.3).
  - Built `SpeakerNameDelegate` (`QStyledItemDelegate`) with theme-adaptive active styling (dark, light, high-contrast) and automatic pre-selection of speaker names upon editor focus.
  - Added intelligent Tab / Shift+Tab keyboard progression: pressing Tab automatically commits the current speaker rename, flushes transcript undo state, persists to project JSON, and advances the inline editor directly to the next speaker row in editing state, enabling rapid sequential renaming of all detected clusters.
  - Implemented smart navigation guards: pressing Tab without modifying a name or with whitespace immediately advances to the next speaker without triggering redundant project saves or undo history mutations.
  - Locked columns 1–3 ("Cluster / Raw ID", "Turns", "Total Duration") to non-editable flags (`~Qt.ItemFlag.ItemIsEditable`), ensuring clean, single-column inline renaming without accidental cell clicks.
  - Added comprehensive automated diagnostic test assertions in `diagnostic_core_tests.py` validating column edit triggers, delegate binding, inline rename propagation, and Tab progression state transitions.

## v3.9.40-beta
- **Batch Processing Silent Auto-Save & Unified Project File Generation (`media_batch.py`, `project_lifecycle.py`, `transcription_processing.py`)**:
  - Resolved an issue where running a multi-file batch job saved only a single `.rtvs` project file for the first item and failed to generate individual `.rtvs` project files for subsequent media items.
  - Implemented `_get_batch_project_target_path(base_name)` in `media_batch.py` to ensure consistent, reliable project file resolution across both pre-binding and export cycles for standard and unified transcripts mode.
  - Pre-bound `self.project_file` in `_batch_next_media()` immediately after loading each audio file, enabling intermediate pipeline stages (e.g. `save_project()` at line 489 in `transcription_processing.py`) to auto-save silently without falling back to interactive modal prompts (`save_project_as()`).
  - Added an active batch fallback in `project_lifecycle.py` (`save_project`): if `self.project_file` is unassigned during batch execution, it routes directly to `self._batch_save_project_file()` instead of invoking `QFileDialog.getSaveFileName()`. Suppressed interactive `QMessageBox` alerts and media copy prompts when `batch_active` is True.
  - Verified multi-file batch execution through simulation and automated tests, ensuring each audio file in a batch creates and preserves its own individual `.rtvs` project file.
- **Diagnostic Test Bench Three-Tier Verification Hierarchy & Performance Optimization (`test_runner.py`, `diagnostic_dialog.py`, `diagnostic_selector.py`, `diagnostic_loudness_tests.py`, `AGENTS.md`, `GEMINI.md`)**:
  - Implemented smart change-aware diagnostic test runner defaulting: executing `python test_runner.py` (or `--quiet`) automatically defaults to Tier 2 (running only tests matching modified git files in ~0.5–2s) whenever uncommitted changes exist, preventing slow, token-heavy 68-test runs during turn-by-turn development.
  - Added explicit `--all` flag to `test_runner.py` for comprehensive release audits (Tier 3), while preserving targeted `--filter <keyword>` execution (Tier 1) for sub-second verification.
  - Codified the Three-Tier Diagnostic Verification Hierarchy in `AGENTS.md` and `GEMINI.md` under Section 3 (Pre-Completion Verification) and Section 11 (Diagnostic & Log Output Discipline).
  - Decomposed monolithic `test_runner.py` (993 lines) by extracting `create_diagnostic_dialog` into dedicated submodule `diagnostic_dialog.py` (284 lines), reducing `test_runner.py` to 740 lines in full compliance with the <800-line modularity invariant (Rule 10).
  - Fixed PySide6 Qt parentage type mismatches in `MockPreferencesApp` and imported missing `QPushButton` in `diagnostic_loudness_tests.py`, achieving a 100% pass rate (68/69 passed, 1 modularity advisory warning) across the entire diagnostic suite in under 20 seconds.
  - Shortened synthetic test audio fixture durations from 15.0s/10.0s to 5.0s, reducing full-suite execution time by ~67%.

## v3.9.39-beta
- **Strict Effective Speaker Scoping for Unknown Cluster Merges (`speaker_dialog_refinement_mixin.py`, `speaker_dialogs.py`)**:
  - Fixed an over-broad segment matching bug where raw segments that lacked manual speaker overrides (`segment_speaker_overrides` = None) were erroneously matched as "Unknown Speaker" even when their effective diarization name was already a valid speaker (such as "Speaker 2").
  - Tightened `is_unknown_source` guards in `merge_speakers()` and `_rename_speaker()` to strictly check that `get_effective_speaker_name()` is empty or unassigned before matching, ensuring known speaker clusters are completely untouched when merging unassigned turns.
  - Prevented global alias contamination by popping "Unknown Speaker" from `speaker_names` rather than aliasing it globally, preserving distinct unassigned states for future media.
  - Added unit test assertion in `diagnostic_core_tests.py` ensuring known speaker turns (`SPEAKER_01`) remain intact when an unassigned turn is merged.

## v3.9.38-beta
- **"Unknown Speaker" Cluster Merge & Rename Fix (`speaker_dialog_refinement_mixin.py`, `speaker_dialogs.py`, `export_documents.py`)**:
  - Fixed an issue where segments without diarization overlap (displayed in the speaker management table as "Unknown Speaker") failed to reassign when clicking "Merge Into..." or "Rename / Alias".
  - Updated `merge_speakers()` in `speaker_dialog_refinement_mixin.py` to recognize unknown/unassigned speaker clusters (`is_unknown_source`), matching empty or unassigned effective names and reassigning turn overrides (`SEG_{idx}_SPEAKER`), `seg["speaker"]`, and diarization segments properly.
  - Updated `SpeakerManagerDialog` (`speaker_dialogs.py`) to pool candidates across visible table items and known speakers for both "Merge Into..." and "Merge Two Speakers...", and updated `_rename_speaker` to handle renaming "Unknown Speaker" clusters.
  - Enhanced `export_documents.py` (`speaker_for_segment`) to fall back gracefully to `segment.get("speaker")` when `speaker_at_time` returns no diarization match.
  - Added unit test assertions in `diagnostic_core_tests.py` verifying full round-trip merge of "Unknown Speaker" turns into named clusters with live table row reduction.

## v3.9.37-beta
- **Speaker Management Quick Sample Audio Preview (`speaker_dialogs.py`, `diagnostic_core_tests.py`, `test_runner.py`)**:
  - Implemented instant "Play Sample" / "Stop" voice audition buttons alongside each detected speaker in `SpeakerManagerDialog` (`speaker_dialogs.py`).
  - Added intelligent representative utterance resolution (`_find_speaker_sample_range`): scans transcript segments for the active speaker cluster and selects the longest continuous speech segment >= 3.0 seconds (or the first utterance if shorter) to ensure clean, identifiable voice preview.
  - Built non-blocking 3-second preview playout using an isolated `QMediaPlayer` and `QAudioOutput` channel with dedicated volume and audio device binding, guaranteeing that auditioning speaker samples never alters main project scrub position, playback markers, or transport state.
  - Added robust playout lifecycle and teardown safety: preview playback automatically terminates on timeout, on clicking "Stop", when switching to audition another speaker, on window close/rejection/acceptance, or before entering rename/merge workflows.
  - Added automated diagnostic test coverage in `diagnostic_core_tests.py` and `test_runner.py` verifying sample range resolution, playout toggling, button state synchronization, and clean dialog teardown.

## v3.9.36-beta
- **Stories Pop-Out Dialog Parity with WordPress Draft Export View (`story_metadata_dialog.py`, `plugins/wordpress/export_destination.py`, `ui_layout.py`)**:
  - Replaced the monolithic 1,313-line vertical form in `story_metadata_dialog.py` with an exact clone of the 4-tab WordPress draft export view (`WordPressExportTabWidget`), bringing full feature parity (`Post Content`, `Authors & Taxonomy`, `Podcast & Media`, and `Publishing & Formatting`) to the pop-out editor.
  - Implemented dedicated "Save" and "Close" action buttons in the bottom right of the Stories pop-out dialog and `WordPressPostMetadataDialog`, replacing modal "Cancel" and "Export" buttons. The "Save" button instantly commits all post metadata to the active project state with visual confirmation ("Saved ✓") without closing the window, while "Close" auto-commits and dismisses the floating dialog.
  - Renamed the header pop-out button from "Pop Out" to "Story Settings" with an expanded, descriptive tooltip explaining that it opens comprehensive story and post settings.
- **Strict Prohibition on Non-Draft Export Statuses (`plugins/wordpress/wordpress_dialog.py`, `plugins/wordpress/plugin.py`, `story_metadata_dialog.py`)**:
  - Locked all post status selectors strictly to "Draft" only, permanently removing options for "Published", "Publish Immediately", "Pending Review", and "Private" to ensure posts can never be accidentally published or altered from draft status during export or metadata staging.
- **Icon and Emoji Elimination from Search & Filter Bars (`story_metadata_dialog.py`, `plugins/wordpress/wp_ui_builder.py`, `shortcuts/dialogs.py`)**:
  - Audited search and filter interfaces across the application and removed decorative magnifying glass glyphs (`🔍`) from author/category filter inputs and group boxes, enforcing clean, distraction-free desktop typography in strict adherence to UI design discipline.
- **Live Co-Editing & Sync Transcript Architecture**:
  - Synchronized "Sync Transcript" button integration across both `UnifiedExportDialog` and `StoryMetadataDialog`: when co-editing transcripts in the main window while keeping metadata floating side-by-side, clicking "Sync Transcript" flushes in-memory keystroke buffers, recalculates word counts/story boundaries, and updates post models in real time without requiring a window restart.

## v3.9.35-beta
- **4-Tab WordPress Export Architecture & Configurable Layout Switcher (`plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/client.py`)**:
  - Replaced the cramped vertical accordion stack in `WordPressExportTabWidget` with a spacious 4-tab layout (`Post Content`, `Authors & Taxonomy`, `Podcast & Media`, and `Publishing & Formatting`) featuring high-contrast card/pill tab styling across Dark, Light, and High-Contrast themes.
  - Replaced the fixed-height gripped `ResizableTextEdit` excerpt input with a full-height auto-expanding `QTextEdit` (`QSizePolicy.Policy.Expanding`) that scales dynamically with dialog resizing, paired with a docked Custom Header/Footer Notice inside a vertical `QSplitter`.
  - Expanded Author and Category checklists to fill full vertical tab height, removed the 8 redundant "Bulk Apply" buttons, preserved active tab selection when stepping through stories in the left-hand queue, and automatically omitted the `Publishing & Formatting` tab when running in Story Metadata mode.
  - Added a user-configurable `Export Configuration View Layout` dropdown (`Tabs (Recommended)`, `Split Two-Column`, `Classic Vertical Accordion`) in `WordPressSettingsDialog` and `WordPressPreferencesPage` persisted via `QSettings("wordpress_layout_style")` (including `QComboBox` import resolution in `plugins/wordpress/client.py`).
- **Non-Modal Floating Export & Story Metadata Windows with Live Transcript Co-Editing (`export/dialog.py`, `export_dialogs.py`, `story_metadata_dialog.py`, `story_crud_mixin.py`, `project_state_mixin.py`, `project_lifecycle.py`, `project_export.py`, `ui_layout.py`)**:
  - Transitioned `UnifiedExportDialog` and `StoryMetadataDialog` to independent non-modal floating windows (`Qt.WindowType.Window`, `Qt.WindowModality.NonModal`, `WA_QuitOnClose=False`), enabling publishers to freely click back into the main transcript window to edit words, fix spelling, scrub audio, or relabel speakers without modal lockout or z-order window obstruction.
  - Added a checkable `Pin on Top` header button (`toggle_float_mode`), a `Sync Transcript` header button (`refresh_from_main_window`), and a `Pop Out` button (`popout_stories_btn`) in the main window's Stories sidebar header that automatically un-maximizes the Stories panel if needed and launches the floating metadata editor.
  - Implemented singleton window focus management (`_active_export_dialog`, `_active_metadata_dialog`), live state synchronization on `_commit_project_state_change` and `QEvent.Type.WindowActivate`, pre-export pending transcript undo flushing, and clean draft persistence/window teardown on `close_project` and `closeEvent`.
- **Diagnostic Verification Suite (`diagnostic_export_tests.py`)**:
  - Added automated assertions verifying shared story/project WordPress metadata round-tripping, 4-tab and 3-tab (`metadata_editor_mode`) layout construction, `WordPressPreferencesPage` / `WordPressSettingsDialog` layout combo initialization, and non-modal floating dialog controls.

## v3.9.34-beta
- **Shared Story & Project WordPress Metadata Persistence (`story_metadata_dialog.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/castos.py`, `export/dialog.py`, `export_dialogs.py`)**:
  - Established `story.metadata["wordpress"]` and `project_metadata["wordpress"]` as the canonical source of truth for all WordPress publishing metadata (`title`, `excerpt`, `author_ids`, `author_term_ids`, `category_ids`, `featured_image`, `featured_image_mode`, `frame_pos`, `status`, `slug`, `tags`, `is_podcast`, `podcast_feed_ids`, `season`, `episode_number`).
  - Implemented live two-way synchronization in `WordPressExportTabWidget` and `castos.py` so all field edits, excerpt auto-generation, thumbnail captures, and Castos podcast toggles immediately update the active project state.
  - Ensured closing or canceling `UnifiedExportDialog` preserves all typed data, author selections, category assignments, and custom notices, auto-saving them to the `.rtvs` project container so users can switch back to the main window to edit transcript text or label speakers without losing work.
  - Added export session memory (`last_export_scope` and `last_export_dest`) so reopening the Export dialog returns directly to the user's active workflow.
  - Added plugin-aware taxonomy visibility to `StoryMetadataDialog`: dynamically displays WordPress taxonomy lists and refresh tools only when the WordPress plugin is active, while cleanly managing offline metadata natively.
- **Orphaned Plugin Deprecation Pruning (`plugins/manager.py`)**:
  - Added automatic deprecation pruning in `PluginManager.sync_bundled_updates()` to remove obsolete user-directory plugin remnants (such as retired `gdocs`) on launch, preventing `No module named 'plugins.gdocs'` startup warnings.

## v3.9.33-beta
- **Google Drive/Docs & Sheets Cloud Integration Removal (`plugins/gdocs/`, `plugins/google_sheets.py`, `backup_manager.py`, `plugins/installer_workers.py`, `plugins/manager_dialog.py`, `plugin_dialogs.py`, `export/reorder_dialog.py`, `preferences_dialog.py`, `build_installer.py`)**:
  - Retired the Google Docs/Drive export plugin (`plugins/gdocs/`, `plugins/gdocs.rtvs-addon`), dormant Google Sheets plugin (`plugins/google_sheets.py`), OAuth 2.0 PKCE local loopback listeners, token caches, and setup guides (`GOOGLE_OAUTH_SETUP.md`, `GOOGLE_DOCS_USER_GUIDE.md`).
  - Removed the Google Drive Cloud Backup tab and cloud upload/download helpers from `backup_manager.py`, consolidating backup management around verified local `.rtvs-backup` archives.
  - Unregistered `gdocs` from plugin installer catalogs, manager dialogs, export tab reordering defaults, preferences reset handlers, and PyInstaller build flags while preserving all local offline document exports (`export_documents.py`: DOCX, PDF, TXT, HTML, CSV, JSON, SRT/VTT).
- **YouTube Zero-Auth Manual Export Streamlining (`plugins/youtube/plugin.py`, `plugins/youtube/export_destination.py`, `export_media_clipper.py`, `export_story_pipeline.py`)**:
  - Removed `plugins/youtube/api.py`, Google OAuth 2.0 account linking, and direct YouTube Data API v3 upload dependencies from the YouTube Video Publisher plugin (`v3.9.33-beta`).
  - Streamlined the YouTube export destination around a zero-auth local upload package workflow with a direct "Open YouTube Studio" browser launcher.
  - Added automatic audio-to-video MP4 conversion (`ffmpeg -loop 1 ... -c:v libx264 -tune stillimage -pix_fmt yuv420p`) for audio-only broadcasts (`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.aac`, `.wma`) using either a user-selected thumbnail or an auto-generated 1280x720 dark broadcast slate PNG (`_generate_broadcast_slate_thumbnail`).
  - Enhanced the exported `{base_name}_youtube_metadata.txt` sidecar and clipboard payload to include Video Title, Description with clickable chapter timestamps (`00:00`), automatic Speaker credits, and comma-separated tags alongside the `.mp4` video, companion thumbnail image, and `.srt` closed captions.
- **Diagnostic Test Suite Synchronization & Lazy Facade Wildcard Export Fix (`prs_shared.py`, `diagnostic_core_tests.py`, `diagnostic_selector.py`, `test_runner.py`, `diagnostic_batch_tests.py`, `diagnostic_export_tests.py`, `diagnostic_cloud_and_system_tests.py`)**:
  - Added explicit `__all__` export list in `prs_shared.py` covering `_STORY_WIDGET_EXPORTS`, `_TIMELINE_WIDGET_EXPORTS`, and `_BACKGROUND_WORKER_EXPORTS` so modules using `from prs_shared import *` (`media_batch.py`, `RadioTVSegmenter.py`, `transcript_story.py`, etc.) bind `read_waveform_peak_cache`, `WaveformWorker`, and `VideoThumbnailWorker` via `__getattr__`, resolving `NameError: name 'read_waveform_peak_cache' is not defined` when loading media files.
  - Replaced retired Google Docs/Sheets OAuth tests with offline document and YouTube zero-auth package verification tests across all 68 diagnostic checks, and added `--changed` / `--filter` smart test selection via `diagnostic_selector.py`.

## v3.9.32-beta
- **Circular Import Elimination & Core Facade Decoupling (`prs_shared.py`, `story_widgets.py`, `background_workers.py`)**:
  - Replaced tight top-level UI and background worker imports in `prs_shared.py` (`FadeCurveVisualSelector`, `StoryFadesChangeCommand`, `TimelineCanvas`, `StoryAutoDetectWorker`, etc.) with Python 3.7+ module-level `__getattr__` and `globals()` caching.
  - Resolved circular import deadlock between core utilities and worker modules, allowing `background_workers.py` to be cleanly imported and executed in isolation without circular dependency errors.
- **Video Thumbnail Worker Zero-Division Guard (`background_workers.py`)**:
  - Protected frame rate calculation (`fps = max(0.001, float(self.count or 1)) / max(0.001, float(self.duration or 0.0))`) against zero-duration or corrupt video streams, preventing `ZeroDivisionError` crashes during background thumbnail generation.
- **WordPress Media Binary Streaming & Canonical Endpoint Resolution (`plugins/wordpress/client.py`)**:
  - Fixed inoperable raw binary upload fallback in `upload_media()`: replaced invalid JSON payload call with direct streaming binary upload (`requests.post(url, data=f, headers=headers)`) using file handle references.
  - Prioritized canonical non-trailing `/media` endpoint before trailing slash fallback `/media/` to eliminate HTTP 301 Moved Permanently redirects across standard WordPress REST configurations.
- **Podcast Scope Default Isolation & UI Decoupling (`plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/castos.py`, `plugins/wordpress/export_destination.py`)**:
  - Updated default podcast designation across export scopes: `Full Episode` posts now default to `is_podcast = True`, while child story posts default to `is_podcast = False`.
  - When exporting `full` or `full_and_all_stories`, only the Full Episode is designated as a podcast episode by default.
  - When exporting `all_stories` or `selected_stories`, child story items remain standard WordPress posts with podcast toggles unchecked by default.
  - Removed aggressive 2-post synchronization coupling in `setup_castos_ui` (`castos.py`) so checking or unchecking a podcast box for one queue item never forces or overrides the state of any other queue item.
  - Eliminated podcast metadata leakage in `export_destination.py` that previously forced podcast taxonomy onto child story scopes.
- **Roadmap Invariant Tracking & Monolithic Module Cataloging (`roadmap.txt`)**:
  - Added Section 9 to roadmap detailing Wave 6 Monolithic File Decomposition for all 17 remaining source files exceeding 1,000 lines under the single-responsibility invariant.

## v3.9.31-beta
- **Seriously Simple Podcasting Duplicate Post Elimination & String Metadata Serialization (`plugins/wordpress/client.py`, `plugins/wordpress/castos.py`)**:
  - Identified and resolved the root cause of duplicate draft posts in WordPress: Seriously Simple Podcasting (SSP) registers `filesize` as `type: string` in its REST schema. When sent as an integer, WordPress returns `HTTP 400 Bad Request` (`rest_invalid_type: meta.filesize`).
  - Discovered that WordPress core inserts the post into the MySQL database *before* validating meta parameters. When the request failed with 400, the post was already created in the database, and RTVS's fallback retry generated a second post (resulting in two identical draft posts).
  - Updated `build_castos_post_meta` and sanitized metadata in `client.py:create_post` to ensure `filesize`, `duration`, `season`, and `episode_number` are strictly formatted as strings, allowing the initial REST API request to succeed immediately with `201 Created` on the first attempt with zero retries.
  - Implemented defensive post commitment detection in `client.py:create_post`: if WordPress ever returns 400 after partially committing a post to the database, RTVS queries and detects the committed draft, updating its taxonomy and media attachments rather than posting a duplicate draft.
- **Export Scope Title Preservation & De-Consolidation (`plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/export_destination.py`)**:
  - Removed artificial single-story consolidation code that previously overwrote the user's Full Episode title (e.g. "LYB Narration") with story snippet titles (e.g. "00:02 Little Yenta Books is a...").
  - Fixed `build_full_item()` in `wp_post_builder.py` so that selecting or switching export scopes never copies child story titles into the Full Episode post definition.
  - Maintained clean scope boundaries in `export_destination.py`: `full` exports the Full Episode, `all_stories` exports child stories, and `full_and_all_stories` exports both without destroying individual post identities.
- **Test Bench User Settings Isolation (`diagnostic_export_tests.py`)**:
  - Wrapped test execution in a `finally` block in `diagnostic_export_tests.py` to preserve and restore the user's active `wp_site_url` and `wp_username` settings, preventing test placeholder credentials from altering live configuration.

## v3.9.30-beta
- **Complete WordPress Duplicate Draft Post Elimination & Export Scope Synchronization (`export/dialog.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/castos.py`)**:
  - Resolved an issue where exporting to WordPress draft posts produced two duplicate posts (one with podcast settings applied, and one without) when exporting projects with a single story or full episode across all scopes (`full`, `all_stories`, `selected_stories`, and `full_and_all_stories`).
  - In `export/dialog.py`, triggered `self._on_scope_changed()` synchronously upon dialog initialization so that all registered destination panels (including WordPress) immediately sync their queue definitions with the active scope dropdown.
  - In `plugins/wordpress/wp_post_builder.py`, unified single-story projects under `full_and_all_stories` scope to produce exactly one consolidated post item rather than queuing redundant Full Episode and Story 1 drafts.
  - In `plugins/wordpress/export_destination.py`, enforced strict single-post resolution under `full` and single-story scopes with bi-directional podcast metadata inheritance, ensuring podcast feeds, episode numbers, and series taxonomy IDs are never lost.
  - Added strict title-level deduplication in `execute_export`: posts sharing matching normalized titles are automatically consolidated into a single draft submission with merged podcast taxonomy properties.
  - In `plugins/wordpress/castos.py`, synchronized podcast toggle state across full episode and story items when projects contain a single story to eliminate non-podcast shadow posts.
- **Unified Export Dialog Menu Action Routing (`plugins/wordpress/plugin.py`)**:
  - Updated "Publish to WordPress..." in the Publishing & Plugins menu to route directly to `self.app.open_unified_export_dialog(initial_dest="wordpress")`, aligning with the YouTube and Google Docs plugin integrations and opening the modern WordPress export panel.
- **Synchronous Release Alignment**:
  - Synchronized `PROJECT_VERSION` across all 10 project locations to `v3.9.30-beta`.

## v3.9.29-beta
- **Seriously Simple Podcasting Multi-Feed Selection (`plugins/wordpress/castos.py`, `plugins/wordpress/client.py`, `plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/wp_tab_widget.py`)**:
  - Implemented multi-selection for podcast feeds/series in the WordPress export panel via checkable `wp_podcast_feeds_list`, enabling publishers on multi-feed websites to assign an episode to multiple podcast feeds simultaneously (e.g. both "Block by Block" and "Around the Block").
  - Extended the data model to record `podcast_feed_ids: list[int]` and `podcast_feeds: list[str]`, preserving selections seamlessly across story queue switches and project sessions.
  - Updated `create_post` and `execute_wordpress_upload` in `client.py` to transmit the complete list of series term IDs (`payload["series"] = [id1, id2, ...]`) to the WordPress REST API.
  - Retained `wp_podcast_feed_combo` as an automatic backward-compatible proxy to prevent regressions in external integrations.
- **Duplicate WordPress Draft Elimination & Strict Scope Enforcement (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`)**:
  - Eliminated redundant draft post creation across all export scopes (`full`, `all_stories`, `selected_stories`, `full_and_all_stories`).
  - Removed trailing-slash endpoint `f"{self.api_base}/posts/"` in `client.py:create_post`, preventing web server canonical 301/302 redirects from triggering duplicate POST submissions.
  - Enforced strict scope filtering in `export_destination.py:execute_export`: `scope == "full"` strictly restricts the upload queue to the single Full Episode post, while `scope in ("all_stories", "selected_stories")` strictly isolates child story posts.
  - Added an automated boundary-and-title deduplication safety net in `ordered_wp_posts` guaranteeing exactly one clean draft post per intended story or full episode.
  - Extracted `copy_podcast_meta` into `castos.py`, reducing `wp_tab_widget.py` from 998 lines to 969 lines to maintain strict compliance with the 1,000-line modularity ceiling.
- **System Diagnostic Test Bench Completion Fix (`diagnostic_export_tests.py`)**:
  - Resolved an issue where Test #33 (`WordPress Audio Inclusion Toggle & Error Resilience`) remained in `RUNNING` status and never reported completion in the diagnostic test dialog.
  - Linked `self._test_wordpress_castos_podcast_integration(item)` directly within `_test_wordpress_audio_inclusion_toggle_and_error_resilience` and explicitly set `item.status = "PASS"` with verification messaging, ensuring all 71 tests complete cleanly across GUI and CLI runners (70 passed, 1 warning, 0 failed).
- **Seriously Simple Podcasting (Castos) Episode File & Meta Association Fix (`plugins/wordpress/castos.py`, `plugins/wordpress/client.py`)**:
  - Corrected post meta mapping in `build_castos_post_meta` to supply native Seriously Simple Podcasting meta fields (`audio_file`, `duration`, `filesize`, `episode_type`, `season`, `episode_number`) alongside legacy compatibility aliases.
  - Strictly eliminated leading-underscore keys (`_...`) from REST metadata payloads to avoid WordPress REST API `HTTP 400 Bad Request` (`rest_invalid_param: meta`) errors.
  - Updated `create_post` and `update_post` in `client.py` to automatically associate uploaded audio media attachments with the created draft post via `/media/{att_id}`.
- **Podcast Series / Feed Auto-Discovery, Author Exclusion & Taxonomy Assignment Fix (`plugins/wordpress/castos.py`, `plugins/wordpress/client.py`, `plugins/wordpress/wp_tab_widget.py`)**:
  - Updated WordPress series assignment to target the native Seriously Simple Podcasting taxonomy (`series`) with backward-compatible fallback (`podcast_series`), ensuring the selected feed is properly checked in the WordPress sidebar.
  - Implemented dynamic REST API taxonomy auto-discovery in `fetch_castos_feeds` querying `/wp-json/wp/v2/taxonomies` to detect custom or plugin-specific rest bases, as well as probing canonical routes (`/wp-json/wp/v2/series`, `/wp-json/ssp/v1/feeds`), ensuring all registered podcast feeds/series appear in the dropdown.
  - Added strict exclusion of non-podcast taxonomies (`author`, `ppma_author`, `category`, `post_tag`, `nav_menu`) and author slugs, preventing author usernames (such as `brad linder`) from ever being misidentified as podcast feeds.
  - Added `sanitize_castos_feeds` cache sanitization on initialization to ensure any legacy cached author terms are immediately purged from local preferences.
  - Added user guidance prompt in `_refresh_castos_feeds` when WordPress credentials are not yet configured.
- **Audio Inclusion Auto-Enabling & Pre-Export Validation (`plugins/wordpress/castos.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/export_destination.py`)**:
  - Automatically enabled the "Include audio files in WordPress export" checkbox whenever a post is designated as a Podcast Episode.
  - Added real-time informational prompt if a user unchecks audio inclusion while podcast episodes are active, and an automated pre-export confirmation dialog offering to re-enable audio inclusion before publishing.
- **WordPress Podcast Single-Draft Export & Scope Inheritance Fix (`plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/castos.py`)**:
  - Resolved an issue where exporting to WordPress with Seriously Simple Podcasting enabled resulted in duplicate draft posts or dropped podcast metadata when set to "Full Episode" or "Full Episode & All Stories".
  - In `wp_post_builder.py`, added cross-scope metadata preservation: when a user configures podcast settings and switches scope to "Full Episode", the podcast feed, episode parameters, authors, and categories are seamlessly inherited by the Full Episode post rather than reset.
  - Added full-span single-story detection under `full_and_all_stories` scope to avoid queuing redundant duplicate items when a story encompasses the entire audio file.
  - In `export_destination.py`, added automated podcast deduplication to `execute_export`: if an export queue contains a designated podcast post alongside an un-designated duplicate covering the same audio bounds, the redundant non-podcast post is automatically omitted from publishing.
  - In `castos.py`, synchronized toggle state so podcast designation and feeds cleanly apply without orphaned shadow draft posts.
- **Diagnostic Bench Mock Hardening (`diagnostic_export_tests.py`)**:
  - Resolved `TypeError` in `MockFeedDiscoveryClient` where instance method lambda binding passed `self` to 0-arg lambdas in Test #33.
- **Synchronous Release Alignment**:
  - Synchronized `PROJECT_VERSION` across all 10 project locations to `v3.9.29-beta`.

## v3.9.28-beta
- **Audio Loudness Normalization Dialog Robustness & Defensive Parentage (`dialogs.py`)**:
  - Added duck-typing parent validation (`qt_parent = parent if isinstance(parent, QWidget) else None; super().__init__(qt_parent)`) in `AudioLoudnessNormalizationDialog`, preventing PySide6 `TypeError` when instantiated with headless mock windows or custom presenter wrappers.
- **Synchronous Release Alignment**:
  - Synchronized `PROJECT_VERSION` across all 10 project locations to `v3.9.28-beta`.

## v3.9.27-beta
- **Audio Loudness Normalization & Active Media Source Refresh Fix (`audio_normalization.py`, `dialogs.py`, `media_batch.py`)**:
  - Fixed an issue where applying manual audio loudness normalization (`Ctrl+Alt+N` / `Tools -> Normalize Audio Loudness...`) with auto-boost disabled in Preferences resulted in unrefreshed waveforms and stale audio playback streams.
  - Updated `get_effective_audio_for_processing` in `audio_normalization.py` to resolve absolute file paths and verify `source_media` path ownership so normalized sidecars from previously opened files are never mistakenly applied to newly opened media files.
  - Updated `dialogs.py` (`apply_normalization`) to store resolved absolute paths for `source_media` and `normalized_sidecar` in `project_metadata`.
  - Fixed `load_media_file` in `media_batch.py` to reset `self.project_metadata` to a clean `ProjectMetadataDict()` on new media imports, preventing stale loudness metadata from lingering.
  - Updated `update_active_media_source` and `load_waveform_async` in `media_batch.py` to pass `project_file` parameter to `read_waveform_peak_cache`, `write_waveform_peak_cache`, and `invalidate_waveform_peak_cache`, ensuring peak cache files are correctly invalidated and recalculated from the boosted sidecar WAV file upon manual normalization.
  - Resolved player source swapping in `update_active_media_source` by ensuring `self.player.stop()` is called prior to `self.player.setSource(QUrl.fromLocalFile(str(eff_path)))` with absolute resolved file paths.

## v3.9.26-beta
- **Seriously Simple Podcasting (Castos) Submodule Integration (`plugins/wordpress/castos.py`)**:
  - Implemented dedicated `castos.py` module containing Castos post meta field definitions (`ss_podcast_audio_file`, `ss_podcast_duration`, `ss_podcast_filesize`, `ss_podcast_feed`, `ss_podcast_episode_type`, `ss_podcast_season`, `ss_podcast_episode_number`).
  - Added REST API series/feed discovery helper `fetch_castos_feeds` querying `/wp-json/wp/v2/podcast_series` and `/wp-json/ssp/v1/feeds` with safe default feed fallback (`"default"` / `"Main Podcast Feed"`).
  - Implemented `build_castos_post_meta` and shortcode/block player generator (`[podcast_episode]` / `<!-- wp:castos-player/player -->`).
- **WordPress REST Client & Media Attachment ID Binding (`plugins/wordpress/client.py`)**:
  - Enhanced `create_post` and `update_post` to accept custom `meta` dictionaries and `podcast_series` taxonomy IDs.
  - Added `get_podcast_feeds()` client method for fetching available podcast feeds from the WordPress site.
  - Updated `execute_wordpress_upload` to support podcast episode parameters (`is_podcast`, `podcast_feed`, `podcast_feed_id`, `podcast_episode_type`, `podcast_season`, `podcast_episode_number`).
  - Automated media library upload to capture media attachment ID and filesize (`ss_podcast_audio_file` meta and `ss_podcast_filesize`).
  - Implemented conditional player embedding: embeds Castos web player for designated podcast episodes (omitting standard `<!-- wp:audio -->` blocks to prevent duplicate audio players), while preserving default `<!-- wp:audio -->` blocks for non-podcast exports.
- **WordPress Post Item Builders & Export Execution (`plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/export_destination.py`)**:
  - Updated `build_story_item` and `build_full_item` in `wp_post_builder.py` to populate and preserve podcast fields.
  - Passed podcast metadata through `execute_wordpress_upload` in `export_destination.py` and saved podcast export info into `project_metadata["wordpress"]`.
- **Dynamic Podcast Options UI & Bulk Actions (`plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/wp_tab_widget.py`)**:
  - Built `setup_castos_ui` collapsible section with "Designate as Podcast Episode" checkbox, dynamic podcast feed dropdown with "Refresh Feeds" REST API fetch button, episode type selector (Full / Trailer / Bonus), and Season / Episode number spinboxes.
  - Added dynamic visibility connections showing/hiding Castos options when the podcast checkbox is toggled.
  - Added bulk action handlers ("Apply Podcast Settings to Selected / All") for multi-story queue management.
- **Synchronous Version Bump**: Synchronized all project locations and web preview scaffolding to `v3.9.26-beta`.

## v3.9.25-beta
- **Audio Loudness Normalization & Auto-Boost Preferences Integration (`preferences_dialog.py`, `preferences_tabs_core.py`, `preferences_reset.py`, `playback_preferences.py`)**:
  - Implemented the "Audio Loudness Normalization & Auto-Boost" preference controls in the Audio Hardware preferences tab.
  - Added user-configurable toggle for automatic loudness normalization on import (default: enabled) to ensure quiet broadcast files are automatically brought to optimal levels for ASR transcription and speaker detection without altering source media.
  - Added Target Standard selector with dynamic presets: Broadcast Standard (-16.0 LUFS / -1.5 dBTP, default), Podcast / Web Standard (-14.0 LUFS / -1.0 dBTP), EBU R128 Television Standard (-24.0 LUFS / -1.0 dBTP), and Peak Normalization (-3.0 dBFS), automatically updating target LUFS, maximum true-peak, and quiet trigger threshold spinboxes.
  - Added minimum trigger thresholds: Quiet LUFS Threshold (-24.0 LUFS default, range -36.0 to -14.0 LUFS) and Quiet Peak/dBFS Threshold (-6.0 dBFS default, range -18.0 to -1.0 dBFS).
  - Added "Apply loudness boost to in-app playback and exported audio clips" toggle (default: disabled) preserving original mix unless explicitly opted-in by user.
  - Integrated full defaults restoration support into `preferences_reset.py` and category defaults reset handler.
- **Tools Menu Manual Normalization Action & Telemetry Dialog (`dialogs.py`, `ui_menus.py`, `ui_dialog_launchers.py`, `processing.py`, `RadioTVSegmenter.py`)**:
  - Added `Tools -> Normalize Audio Loudness...` action with `Ctrl+Alt+N` shortcut in `ui_menus.py`, dynamically enabled when an audio/video media file is loaded.
  - Implemented dedicated `AudioLoudnessNormalizationDialog` modal in `dialogs.py`:
    * Displays measured audio metrics: Integrated Loudness (I) in LUFS, Loudness Range (LRA) in LU, True Peak (TP) in dBTP/dBFS, and loudness status.
    * Provides Target Standard dropdown and live Gain Adjustment preview with intelligent detection of bypass (already within spec), Tier 1 linear gain + true-peak limiter, or Tier 2 dynamic speech leveler (high LRA > 14 LU).
    * Includes "Apply Normalization", "Re-Analyze", and "Reset to Original" action buttons with background non-blocking execution via `AudioLoudnessProbeWorker`.
    * Clean native desktop typography adhering strictly to the zero-unrequested-emoji design policy.
- **Headless Qt / PySide6 Compatibility Engine Hardening (`qt_compat.py`)**:
  - Resolved circular import between `prs_shared.py` and `dialogs.py`.
  - Enhanced `qt_compat.py` with standalone mock implementations for `DummyQComboBox`, `DummyQDoubleSpinBox`, `DummyQSpinBox`, and `DummySignal`.
  - Added numeric `__int__`, `__index__`, and `__float__` protocol methods to `DynamicMock`, eliminating `TypeError: 'QComboBox' object cannot be interpreted as an integer` during headless CI and test runner sweeps.
- **Automated Diagnostic Suite & Milestone 4 Verification (`diagnostic_loudness_tests.py`, `test_runner.py`)**:
  - Registered `Audio Loudness Preferences and Manual Normalization Dialog` diagnostic test in `test_runner.py` and `diagnostic_loudness_tests.py`.
  - Verified end-to-end normalization against synthetic quiet audio, standard selection spinbox dispatch, telemetry inspection, manual sidecar application, and reset-to-original workflows.
  - All 64 diagnostic tests passing cleanly with 0 failures.
- **Milestones 7 and 8 Swap & Roadmap N-1 Window Synchronization (`roadmap.txt`)**:
  - Swapped Milestones 7 and 8 in `roadmap.txt`, prioritizing the Interactive Text-Based Media Assembly & Multi-Asset Ripple Editing Engine as Milestone 7 and positioning the Android Transcriber Companion App as Milestone 8.
  - Synchronized N-1 sliding window: Active release $N=$ `v3.9.25-beta`, predecessor release $N-1=$ `v3.9.24-beta`.
- **Synchronous Version Bump**: Synchronized all project locations and web preview scaffolding to `v3.9.25-beta`.

## v3.9.24-beta
- **Project Close & Last Project Restore `ProjectMetadataDict` NameError Resolution (`project_lifecycle.py`)**:
  - Resolved `NameError: name 'ProjectMetadataDict' is not defined` triggered in `close_project()` and `load_project_file()` / `restore_last_project()`.
  - Added explicit `ProjectMetadataDict` import from `prs_shared` in `project_lifecycle.py`, ensuring project state resets cleanly without unhandled runtime exceptions.
- **Timeline & Main Window Media Drag-and-Drop Restoration (`timeline_widgets.py`, `timeline_overview_widget.py`, `timeline_canvas.py`, `RadioTVSegmenter.py`, `playback_controller.py`)**:
  - Restored external media file drag-and-drop ingestion directly into the timeline canvas, overview navigation bar, and main application window.
  - Implemented missing `dragMoveEvent` and `dragLeaveEvent` handlers across `TimelineCanvas`, `TimelineOverviewBar`, and `TimelineWidget`; in Qt, omitting `dragMoveEvent` causes `QWidget::dragMoveEvent` to default to `event.ignore()` during cursor motion, preventing `dropEvent` from executing.
  - Standardized MIME data extraction on `extract_dropped_file_paths(event.mimeData())`, seamlessly supporting local files, `file://` URLs, Windows drive paths, URI lists, and raw text drops.
  - Fixed PySide6 `TypeError: 'isAncestorOf' called with wrong argument types: PySide6.QtWidgets.QWidget.isAncestorOf(QWindow)` in `playback_controller.py` by adding explicit `isinstance(watched, QWidget)` type verification and exception safety guards.
- **WordPress Publisher Automated Full-Episode Footer Links & TOC Synchronization (`plugins/wordpress/export_destination.py`, `plugins/wordpress/wp_ui_builder.py`)**:
  - Resolved `NameError: name 'build_episode_stories_toc' is not defined` and `NameError: name 'is_wp_auth_error' is not defined` in `plugins/wordpress/export_destination.py` by importing missing helper functions from `plugins.wordpress.client`.
  - Prioritized publishing Full Episode items before individual story posts during multi-post WordPress uploads so that the newly generated Full Episode URL/ID is immediately captured and available for story cross-linking.
  - Added support for retrieving existing Full Episode metadata from project metadata or export data when publishing individual stories.
  - Ensured automated correspondence notices (`rtvs-parent-episode-notice`) linking back to the parent episode are cleanly appended to the footer/bottom of each story page, and persisted Full Episode metadata into `project_metadata`.
  - Defaulted `wp_parent_episode_pos` in `wp_ui_builder.py` and `export_destination.py` to `bottom` so correspondence links naturally position as footer notices.
  - Added comprehensive automated diagnostic test in `diagnostic_export_tests.py` covering multi-post cross-linking footer correspondence notices, TOC appending, and project metadata persistence.
- **ASR Language Probing & Parakeet ONNX Fallback Refinement (`worker_asr_engines.py`)**:
  - Resolved false non-English language detections on English audio files that caused automatic fallback from user-preferred Parakeet ONNX to Whisper Small.
  - Updated `probe_audio_language()` to sample 30 seconds starting 10 seconds into the media file (`-ss 10 -t 30`), skipping intro music, station jingles, and initial silence that previously distorted mel spectrographic feature extraction.
  - Raised the confidence threshold for overriding user-selected Parakeet ONNX to $\ge 65\%$ and added fallback override logic when English language probability remains significant ($>25\%$).
- **Sherpa-ONNX Runtime Environment Package Inclusion (`runtime_manager.py`, `bootstrap.py`)**:
  - Resolved `sherpa-onnx` runtime missing error in isolated worker environments (`transcribe_env` / `gpu_transcribe_env`) by explicitly adding `sherpa-onnx>=1.13,<2` to `ENV_CONFIGS["transcribe"]` and `ENV_CONFIGS["gpu_transcribe"]` package manifests in `runtime_manager.py`.
  - Bumped environment manifest versions (`1.1.0` / `1.2.0`), triggering automated runtime updates on next launch to automatically provision `sherpa-onnx`.
  - Guarded `bootstrap.py` `ensure_sherpa_onnx_runtime()` against executing invalid `--user` pip flags when running inside virtual environments (`sys.prefix != sys.base_prefix`), preventing pip command failures on Windows.
- **Speaker Detection `QInputDialog` NameError & Repository-Wide AST Import Verification (`diarization_processing.py`, `media_batch.py`)**:
  - Resolved `NameError: name 'QInputDialog' is not defined` when launching Speaker Detection by adding `QInputDialog` to `from PySide6.QtWidgets import ...` in `diarization_processing.py`.
  - Executed a repository-wide AST scanner across all Python modules to audit PySide6 widget references, fixing missing layout/table imports in `media_batch.py` (`QVBoxLayout`, `QHBoxLayout`, `QTableWidget`, `QAction`).
- **Two-Tier Hybrid Audio Loudness Normalization & Auto-Boost Integration (`audio_normalization.py`, `transcription_processing.py`, `diarization_processing.py`, `test_runner.py`, `diagnostic_loudness_tests.py`)**:
  - Implemented the non-destructive conditional two-tier hybrid audio normalization pipeline in `audio_normalization.py`:
    * **Conditional Bypass**: Media files already meeting standard broadcast loudness targets (`integrated_lufs >= target_lufs - 2.0` and `true_peak_dbtp <= -0.5 dBFS`) cleanly bypass processing (`needs_boost = False`), avoiding redundant disk I/O and latency.
    * **Tier 1 (Linear Gain + True-Peak Limiter)**: Automatically boosts uniform quiet audio (`LRA <= 14.0 LU`) using exact linear gain (`delta_db = min(target_lufs - report.integrated_lufs, 24.0)`) and transparent brickwall limiting (`alimiter=limit=-1.5dB:level=false`) without single-pass compressor pumping artifacts.
    * **Tier 2 (Dynamic Speech Leveler)**: Automatically engages speech-tuned dynamic normalization (`highpass=f=80,dynaudnorm=f=250:g=15:p=0.89:m=10.0,alimiter=limit=-1.5dB:level=false`) when extreme speaker disparity is detected (`LRA > 14.0 LU`, e.g., loud studio host + quiet telephone guest).
  - Wired `get_effective_audio_for_processing()` into `transcription_processing.py` and `diarization_processing.py`:
    * Automatically feeds cached, normalized 16 kHz mono WAV sidecars into Whisper, Parakeet, and WeSpeaker without modifying the user's original source media.
    * Populates measured integrated LUFS, LRA, true peak, and boost telemetry into `project_metadata["audio_normalization"]`.
  - Added comprehensive automated diagnostic test (`Two-Tier Hybrid Audio Loudness Normalization`) in `diagnostic_loudness_tests.py` and `test_runner.py` verifying conditional bypass, Tier 1 boost accuracy, Tier 2 leveler dispatch, and settings preference toggling.
- **Synchronous Version Bump**: Synchronized all project locations and web preview scaffolding to `v3.9.24-beta`.

## v3.9.23-beta
- **Frozen GUI Application PySide6 Submodule Resolution (`qt_compat.py`, `prs_shared.py`, `core_utils.py`, `story_model.py`)**:
  - Resolved `KeyError: 'PySide6.QtNetwork'` and startup failures when launching the frozen desktop GUI application (`RadioTVSegmenter.exe` / `.app`).
  - Corrected worker mode detection: replaced erroneous `not hasattr(sys, "_MEIPASS_GUI")` check in `prs_shared.py`, `core_utils.py`, and `story_model.py` with explicit worker identification (`RTVS_WORKER_MODE=1` or `"worker" in Path(sys.executable).stem.lower()`), ensuring the main GUI application natively imports bundled PySide6 submodules.
  - Enhanced `_ensure_pyside6_fallback()` in `qt_compat.py`: imports all 6 application submodules (`QtCore`, `QtNetwork`, `QtGui`, `QtWidgets`, `QtMultimedia`, `QtMultimediaWidgets`) and guarantees any missing submodule is populated with a `MockModule` in `sys.modules`, completely preventing `KeyError` exceptions across both GUI and headless environments.
- **Synchronous Version Bump**: Synchronized all project locations and web preview scaffolding to `v3.9.23-beta`.

## v3.9.22-beta
- **Headless AI Worker Shiboken C-Extension Bypass (`qt_compat.py`)**:
  - Resolved fatal Python error (`Fatal Python error: libshiboken/signature: could not initialize part 2`, `TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'`) during Stage 5/5 frozen AI worker self-test execution (`prs_worker`) across macOS and Linux CI builds.
  - Inverted fallback evaluation in `_ensure_pyside6_fallback()`: when running in worker mode (`RTVS_WORKER_MODE=1`) or forced (`force=True`), immediately injects the zero-dependency mock shims directly into `sys.modules` without ever attempting `import PySide6.QtCore`.
  - Completely avoids dynamic library initialization of Shiboken C-extensions (`QtCore.abi3.so` / `QtCore.dylib`) in frozen bundles where PySide6 is excluded from the worker specification, preventing `signature_bootstrap.py` crashes.
  - Added `QUndoCommand` dummy type to the mock `PySide6.QtGui` module to cleanly support command subclassing in headless environments.
- **Synchronous Version Bump**: Synchronized all project locations and web preview scaffolding to `v3.9.22-beta`.

## v3.9.21-beta
- **UV Package Index Strategy Resolution (`.github/workflows/build.yml`)**:
  - Resolved `uv pip install` dependency conflict error (`error: No solution found when resolving dependencies: Because only certifi==2022.12.7 is available and you require certifi==2024.2.2...`) during Windows and Linux CI workflow execution.
  - Added `--index-strategy unsafe-best-match` to `uv pip install` invocations in `build.yml` so `uv` correctly considers packages across both the CPU PyTorch wheel index and PyPI.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.21-beta`.

## v3.9.20-beta
- **Worker Process Environment Bypass & PyInstaller Exclusion Alignment (`build_installer.py`, `radio_tv_story_segmenter_worker.py`, `story_model.py`, `core_utils.py`, `prs_shared.py`)**:
  - Resolved persistent macOS and Linux Stage 3/5 PyInstaller worker build failures where `PySide6.QtCore` was collected into Extension Modules without its backing `libQt6Core` dynamic libraries.
  - Added explicit `--exclude-module` flags in `build_installer.py` for all PySide6 submodules (`PySide6.QtCore`, `PySide6.QtGui`, `PySide6.QtWidgets`, `PySide6.QtNetwork`, `PySide6.QtMultimedia`, `PySide6.QtMultimediaWidgets`).
  - Added early worker mode environment detection (`RTVS_WORKER_MODE=1` set at worker entry point) in `story_model.py`, `core_utils.py`, and `prs_shared.py`: directly activates `_ensure_pyside6_fallback()` and retrieves symbols from `sys.modules`, completely avoiding any `from PySide6... import` statements.
  - Guarantees zero C-extension `dlopen` calls occur in the background AI worker binary across macOS, Linux, and Windows.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.20-beta`.

## v3.9.19-beta
- **PyInstaller Excluded Submodule Retrieval via `sys.modules` (`prs_shared.py`, `story_model.py`, `core_utils.py`)**:
  - Resolved macOS and Linux PyInstaller frozen build worker self-test failures during Stage 3/5 compilation (`prs_worker`).
  - When `--exclude-module PySide6` is passed to PyInstaller, PyInstaller's C import hook (`pyimod02_importers.py`) intercepts any nested `from PySide6.QtCore import ...` statement and raises `ModuleNotFoundError` or `BaseException` regardless of `sys.modules` state.
  - Refactored `prs_shared.py`, `story_model.py`, and `core_utils.py` fallback handlers: calls `_ensure_pyside6_fallback()` and retrieves symbols directly from `sys.modules["PySide6.*"]` using `getattr()`.
  - Bypasses PyInstaller's bytecode importer check entirely, guaranteeing that `prs_worker` (`radio_tv_story_segmenter_worker`) initializes its JSON IPC protocol and passes `--self-test` across macOS, Linux, and Windows.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.19-beta`.

## v3.9.18-beta
- **MockModule Metadata Conformance for PyTorch Custom Ops & Inspect (`qt_compat.py`)**:
  - Resolved Linux and macOS CI build failures (`AttributeError: type object '__file__' has no attribute 'endswith'`) during `torch` custom operator factory registration.
  - Fixed `MockModule.__getattr__` in `qt_compat.py`: explicit string values are returned for `__file__` (`"<mock_module_name>"`) and `None` / `[]` for `__cached__`, `__spec__`, `__loader__`, and `__path__`.
  - Prevents Python's `inspect.getsourcefile()` from receiving dynamic mock classes instead of filename strings when inspecting dynamic modules.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.18-beta`.

## v3.9.17-beta
- **PyInstaller Frozen Worker Qt Fallback Engine (`qt_compat.py`, `prs_shared.py`, `story_model.py`, `core_utils.py`)**:
  - Resolved GitHub Actions CI build failures (`ImportError: DLL load failed while importing QtCore: The specified module could not be found`) across Windows, macOS, and Linux when freezing the standalone background AI worker executable (`radio_tv_story_segmenter_worker`).
  - Enhanced `_ensure_pyside6_fallback()` in `qt_compat.py` to test submodules (`PySide6.QtCore`, `PySide6.QtWidgets`, `PySide6.QtGui`) instead of top-level `import PySide6`.
  - Wrapped `PySide6` imports in `prs_shared.py`, `story_model.py`, and `core_utils.py` in `try...except Exception:` blocks with automatic `_ensure_pyside6_fallback()` mock module injection.
  - Guarantees the frozen AI worker executable initializes its JSON IPC protocol and executes its `--self-test` cleanly without requiring PySide6 C-extensions to be bundled in the background worker package.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.17-beta`.

## v3.9.16-beta
- **Background Thread Affinity & Qt GUI Object Isolation (`plugins/manager.py`, `plugins/installer_workers.py`, `plugins/github_dialog.py`)**:
  - Fixed `QObject: Cannot create children for a parent that is in a different thread` console warnings during batch plugin downloads and updates.
  - Added `load_ui: bool = True` parameter to `PluginManager.install_addon()`: background thread `GitHubBatchDownloadWorker` extracts plugin files to disk and updates settings without instantiating GUI widgets or `QMenu` actions across thread boundaries.
  - Defer plugin instantiation and menu reconstruction to `on_batch_download_finished()` on the main GUI thread after worker thread completion.
  - Fixed missing signal connection for batch updates in `GitHubPluginsDialog`.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.16-beta`.

## v3.9.15-beta
- **Manage Plugins Toolbar Optimization & Space Recovery (`plugins/manager_dialog.py`)**:
  - Removed redundant "Export Selected..." button, reclaiming horizontal toolbar width and preventing button text clipping.
  - Eliminated label truncation on Windows and High-DPI screens ("Enable Selectec", "Disable Selectec", "ninstall Selectec", "eck for Update").
  - Streamlined button labels ("Uninstall Selected", "Check for Updates") and adjusted toolbar spacing from 8px to 6px.
  - Expanded dialog default geometry to 920x620 (minimum 880x580) to provide comfortable breathing room across all desktop font scaling environments.
- **True Plugin Uninstallation & Multi-Tier Purge Engine (`plugins/manager.py`)**:
  - Resolved issue where uninstalling a plugin only disabled it instead of removing it from disk.
  - Implemented multi-tier filesystem purge in `PluginManager.uninstall_plugin`: completely deletes plugin directories and packaged `.rtvs-addon` archives across both user application data directories and application bundled plugin paths.
  - Added persistent `uninstalled` state tracking via `QSettings` (`_is_uninstalled`): safely handles read-only installations (e.g. frozen in Program Files) so uninstalled add-ons are strictly excluded during discovery and immediately disappear from the installed list.
  - Installing or downloading an add-on automatically clears the uninstalled setting and re-enables full discovery.
- **GitHub Plugins Downloader Reliability & Immediate Catalog Rendering (`plugins/github_dialog.py`, `plugins/installer_workers.py`)**:
  - Eliminated dialog launch delay: pre-populates `GitHubPluginsDialog` with the official plugin catalog immediately on initialization so the catalog table renders instantly with zero network wait time.
  - Added missing Google Docs & Drive Exporter (`gdocs`) entry to `get_official_plugins_catalog`.
  - Fixed Windows modal dialog parenting and focus activation by switching to `setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)` and issuing `show()`, `raise_()`, and `activateWindow()`.
  - Added robust exception handling with user-facing error dialogs in `on_download_github`.
- **Diagnostic Benchmark Suite Resilience (`diagnostic_cloud_and_system_tests.py`)**:
  - Resolved `TimeoutError` in `AI Worker Subprocess Execution and IPC Handshake` benchmark test by extending subprocess execution timeout from 15s to 45s.
  - Prevents false-negative benchmark timeouts during cold starts on Windows with Python 3.14 when loading heavy dynamic C-extensions (PyTorch, WeSpeaker ONNX, CTranslate2, SciPy, Scikit-learn).
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.15-beta`.

## v3.9.14-beta
- **Codebase Modularization & Monolithic File Decomposition (Wave 5 — Milestone 3.7 Completed)**:
  - **Timeline Widgets Decomposition (`timeline_widgets.py`)**:
    - Decomposed 1,898-line `timeline_widgets.py` into dedicated submodules: `waveform_envelope.py` (55 lines), `timeline_overview_widget.py` (339 lines), `timeline_painter.py` (419 lines), `timeline_context_menus.py` (108 lines), and `timeline_snap.py` (119 lines).
    - Reduced `timeline_widgets.py` from 1,898 lines down to 934 lines while preserving 100% backward-compatible zero-breakage facade re-exports for `WaveformEnvelope`, `TimelineResizeHandle`, `TimelineOverviewBar`, `TimelineCanvas`, and `TimelineWidget`.
  - **Plugin Management & GitHub Catalog Decomposition (`plugins/manager.py`)**:
    - Decomposed 1,942-line `plugins/manager.py` into focused submodules: `plugins/installer_workers.py` (260 lines) for background QThreads, `plugins/github_dialog.py` (566 lines) for browsing and batch downloading add-ons from GitHub releases, `plugins/manager_dialog.py` (579 lines) for the main plugin manager dialog, and `plugins/version_utils.py` (32 lines) for semantic version comparison.
    - Reduced `plugins/manager.py` from 1,942 lines down to 586 lines (a 70% reduction) while preserving full re-exports of all dialogs and worker classes.
  - **WordPress Export Destination Decomposition (`plugins/wordpress/export_destination.py`)**:
    - Decomposed 2,080-line `plugins/wordpress/export_destination.py` into focused submodules: `plugins/wordpress/wp_post_builder.py` (199 lines) for post assembly, transcript slicing, and video frame extraction, `plugins/wordpress/wp_ui_builder.py` (610 lines) for UI tab layout construction, and `plugins/wordpress/wp_tab_widget.py` (861 lines) for post editing and preview scrubbing.
    - Reduced `plugins/wordpress/export_destination.py` from 2,080 lines down to 474 lines (a 77% reduction) while maintaining `WordPressExportDestination` and `WordPressPostMetadataDialog` with 100% backward compatibility.
    - Updated `plugins/wordpress/manifest.json` to version `3.9.14-beta` under the lazy catch-up policy.
  - **Milestone 3 Item 3.7 Completion (`roadmap.txt`)**:
    - Finalized Item 3.7 in `roadmap.txt`.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.14-beta`.

## v3.9.13-beta
- **Codebase Modularization & Monolithic File Decomposition (Wave 4)**:
  - **AI Background Worker Decomposition (`radio_tv_story_segmenter_worker.py`)**:
    - Decomposed 2,264-line AI background worker into focused domain submodules: `worker_ipc.py` (216 lines), `worker_asr_engines.py` (816 lines), `worker_diarization_engine.py` (902 lines), `worker_clustering.py` (448 lines), and `worker_story_engine.py` (388 lines).
    - Reduced `radio_tv_story_segmenter_worker.py` from 2,264 lines down to 219 lines (a 90% reduction) while preserving 100% backward-compatible zero-breakage facade re-exports and CLI/IPC protocol handlers.
  - **Performance Benchmark Suite Decomposition (`benchmark.py`)**:
    - Decomposed 2,198-line performance benchmark suite into focused domain submodules: `benchmark_models.py` (457 lines), `benchmark_engine.py` (903 lines), and `benchmark_dialog.py` (674 lines).
    - Reduced `benchmark.py` from 2,198 lines down to 216 lines (a 90% reduction) while preserving 100% backward-compatible zero-breakage facade re-exports and CLI runners.
  - **Milestone 3 Item 3.6 Completion (`roadmap.txt`)**:
    - Finalized Item 3.6 in `roadmap.txt`.
- **Consultative "What's Next" Roadmap Review Directive (`roadmap.txt`)**:
  - Replaced the automatic single-step execution rule with a consultative review directive: queries asking "what's next" now present a comprehensive summary of proposed roadmap options, scopes, and target files for user evaluation before initiating code modifications.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.13-beta`.

## v3.9.12-beta
- **Automated AST Symbol Indexer & Repository Map (`scripts/generate_symbol_index.py`, `.codemaps/`)**:
  - Implemented `scripts/generate_symbol_index.py` scanning 100% of Python modules in the repository (<1.0s runtime) using standard `ast` parsing.
  - Generates machine-dense `.codemaps/symbol_index.json` and human/LLM-readable `.codemaps/INDEX.md` providing instant global visibility of class hierarchies, method signatures, exports, and line numbers.
  - Added CLI flags `--outline <file>` for sub-40 line structural views and `--search <query>` for instant symbol location across all modules.
- **High-ROI Zero-Token Facade Typing Interface Stubs (`.pyi`)**:
  - Created typing stubs for core re-export facades: `prs_shared.pyi`, `processing.pyi`, `playback_preferences.pyi`, `transcript_editor.pyi`, and `project_export.pyi`.
  - Delivers a 95–97% token reduction when verifying public APIs, class signatures, and typing contracts without loading full source files.
- **Token-Thrifty Development & Surgical Range-Editing Rule (`AGENTS.md`, `GEMINI.md`)**:
  - Enforced Section 11 (*Token-Thrifty Development & Surgical Range-Editing Directive*) requiring agents to read files via targeted line-slice ranges, consult `.codemaps/INDEX.md` or `--outline`, perform contiguous edits, use `.pyi` stubs, and execute diagnostics in `--quiet` mode.
- **Milestone 3 Item 3.9 Completion (`roadmap.txt`)**:
  - Finalized Item 3.9 ("Token-Reduction Architecture & Tiered Symbol Indexing for Local LLM Efficiency") in `roadmap.txt`.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.12-beta`.

## v3.9.11-beta
- **"Save Project As..." Native File Dialog Restoration (`project_lifecycle.py`)**:
  - Restored standard `QFileDialog.getSaveFileName` modal dialog prompt when triggering "Save Project As..." (`Ctrl+Shift+S`) or saving a new untitled project.
  - Resolves issue where saving a project with "Save Project As..." bypassed user confirmation and automatically saved to an existing or default location without prompting for a destination path or project name.
  - Automatically initializes the file dialog in the active project directory or media folder and ensures dedicated `Transcripts/` and `Media/` subfolders are created when project bundles are enabled.
- **WordPress REST API Export Scoping Fix (`plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`)**:
  - Resolved `AttributeError: 'WordPressClient' object has no attribute '_discover_canonical_base'` by placing `is_wp_auth_error` at module scope rather than splitting the `WordPressClient` class definition.
  - Restored full client functionality (`_discover_canonical_base`, `_post_request`, `_post_multipart`, `test_connection`, `get_categories`, `get_authors`, `create_post`, `update_post`, `upload_media`).
  - Synchronized WordPress plugin manifest version to `3.9.11-beta`.
- **Roadmap Architecture Refinements: AST Decomposition Suggester & Token-Reduction Architecture (`roadmap.txt`)**:
  - **Milestone 3 Expansion (Items 3.8 & 3.9)**:
    * Expanded Item 3.8 from a passive test guard into an active AST-based structural analyzer (`scripts/modular_audit.py`) that profiles class/method cohesion and automatically suggests turnkey file split blueprints, submodule naming, and `__all__` re-exports for any file approaching the line budget, eliminating guesswork and token waste.
    * Added Item 3.9 ("Token-Reduction Architecture & Tiered Symbol Indexing for Local LLM Efficiency"): Introduces a high-ROI tiered strategy with an automated repository-wide AST symbol indexer across 100% of files (`scripts/generate_symbol_index.py`), targeted `.pyi` interface stubs for large/facade monoliths (>500 lines) delivering ~97% token savings without leaf maintenance drag, and universal surgical range-editing rules.
  - **Milestone 5 Token-Efficiency Bridge (Items 5.1–5.5)**:
    * Integrated Milestone 3's symbol indices and AST suggester directly into Milestone 5's AMD Ryzen AI / local model platform (`scripts/setup_local_ai.py`).
    * Configured prefix-cache pinning for `.codemaps/symbol_index.json` to give local models instant global API visibility at 0 repeated prompt tokens.
    * Added context-window budgeting (`OLLAMA_KV_CACHE_TYPE=q8_0`, 16k working context) reducing KV-cache VRAM by >60% to safeguard system memory for concurrent Whisper/WeSpeaker transcription runs.
- **Token-Reduction & Developer Workflow Tooling (Recommendations 1, 3, 4)**:
  - **Diagnostic Suite Quiet Mode (`test_runner.py`)**: Added `--quiet` / `-q` CLI mode collapsing 68 passing test printouts into a single token-dense line (`[PASS] 62/68 diagnostic tests passed in 1.84s`), saving ~1,400 tokens per test run while preserving full failure details on regressions.
  - **Changelog Sliding Window & Historical Archival (`CHANGELOG.md`, `CHANGELOG_ARCHIVE.md`)**: Preserved the active 25 point releases (all of v3.9 and v3.8) in `CHANGELOG.md` (reducing file size from 2,653 down to 506 lines, saving ~80,000 tokens) while archiving legacy releases (v1.1 through v3.7.22) into `CHANGELOG_ARCHIVE.md`.
  - **Compact Error & Exception Extraction Engine (`scripts/log_summary.py`)**: Implemented standalone CLI and importable parser isolating root exceptions, failing files/lines, and application call stacks from verbose Qt/C++ console noise into clean <15-line reports.
- **Synchronous Version Bump**: Synchronized all 13 core project files and web preview scaffolding to `v3.9.11-beta`.

## v3.9.10-beta
- **Codebase Modularization & Monolithic File Decomposition (Wave 3)**:
  - **Interactive Transcript Editor Decomposition (`transcript_editor.py`)**: Decomposed 2,566-line `transcript_editor.py` into focused submodules: `transcript_editor_dialogs.py` (215 lines), `transcript_styles.py` (105 lines), `transcript_context_menu_mixin.py` (416 lines), `transcript_formatting_mixin.py` (351 lines), and `transcript_timeline_sync_mixin.py` (567 lines), reducing `transcript_editor.py` down to 862 lines (under the <1,000-line invariant) while preserving 100% backward-compatible zero-breakage facade re-exports.
  - **Transcript Story Decomposition (`transcript_story.py`)**: Decomposed 3,055-line `transcript_story.py` into focused submodules: `story_model.py` (228 lines), `story_crud_mixin.py` (724 lines), and `story_detection_processing.py` (143 lines), reducing `transcript_story.py` down to 836 lines.
  - **Synchronous Version Bump**: Synchronized all 12 core project files and web preview scaffolding to `v3.9.10-beta`.

## v3.9.9-beta
- **Roadmap Update: Android Transcriber & Speaker Diarization Mobile Companion (`roadmap.txt`)**:
  - Added optional lower-priority future milestone (`v4.3.0`) for an offline mobile companion app.
  - Features **dual ASR engine options** (Whisper `base.en` `q8_0` via `whisper.cpp` vs. Zipformer via `sherpa-onnx`) allowing users to choose between maximum accuracy/punctuation (Whisper) or blazing-fast speed/low memory (Zipformer).
  - Includes an **on-demand model download and removal manager** enabling users to download, inspect storage, test both engines, and delete models on demand.
  - Added standalone AI Studio starter prompt specification (Option A launcher in Section 7.6) so the companion app can be spun off into a dedicated Android workspace with turnkey dual Whisper/Zipformer runtimes whenever ready.
- **Codebase Modularization & Monolithic File Decomposition (Wave 2A, Wave 2B & Wave 3)**:
  - **Wave 3: Transcript Story & Interactive Editor Decomposition (`transcript_story.py` & `transcript_editor.py`)**:
    - Decomposed 3,055-line `transcript_story.py` into focused submodules: `story_model.py` (228 lines), `story_crud_mixin.py` (724 lines), and `story_detection_processing.py` (143 lines), reducing `transcript_story.py` to 836 lines.
    - Decomposed 2,566-line `transcript_editor.py` into focused submodules: `transcript_editor_dialogs.py` (215 lines), `transcript_styles.py` (105 lines), `transcript_context_menu_mixin.py` (416 lines), `transcript_formatting_mixin.py` (351 lines), and `transcript_timeline_sync_mixin.py` (567 lines), reducing `transcript_editor.py` to 862 lines while preserving 100% backward-compatible zero-breakage facade re-exports.
  - **Wave 2A: Playback & Preferences Decomposition (`playback_preferences.py`)**: Decomposed 4,042-line monolith into focused modules: `theme_preferences.py` (596 lines), `playback_controller.py` (330 lines), `preferences_reset.py` (613 lines), `preferences_tabs_core.py` (509 lines), `preferences_tabs_media.py` (641 lines), `preferences_dialog.py` (588 lines), and `project_state_mixin.py` (328 lines), retaining `playback_preferences.py` (640 lines) as a 100% backward-compatible facade.
  - **Wave 2B: Unified Project & Media Export Decomposition (`project_export.py`)**: Decomposed 3,144-line monolith into focused modules: `export_dialogs.py` (372 lines), `export_media_clipper.py` (211 lines), `export_documents.py` (774 lines), and `export_story_pipeline.py` (979 lines), retaining `project_export.py` (447 lines) as a 100% backward-compatible facade.
- **Fast Non-Blocking Multi-Window Audio Loudness Probing (`audio_normalization.py`, `prs_shared.py`, `test_runner.py`)**:
  - **Fast EBU R128 Loudness Probing Engine (`audio_normalization.py`)**: Implemented `probe_media_loudness()` and `AudioLoudnessProbeWorker(QThread)` leveraging FFmpeg `ebur128=peak=true` filter. Measures Integrated Loudness (`I` in LUFS), Loudness Range (`LRA` in LU), and True Peak (`TP` in dBTP/dBFS) without blocking the Qt GUI thread.
  - **Multi-Window High-Speed Sampling for Long Media**: Automatically samples three 20-second audio windows at 15%, 50%, and 85% of total duration for media exceeding 180 seconds via video-disabled stream seeking (`-vn -ss -t`), enabling 3-hour broadcast recordings to probe in under 1.5 seconds at >200x real-time speed.
  - **Clean Subprocess Lifecycle Tracking**: Wrapped all probing operations in `process_lifecycle.register_process()` and `unregister_process()` with strict timeout enforcement and graceful termination.
  - **Automated Diagnostic Suite (`diagnostic_loudness_tests.py`, `test_runner.py`)**: Created focused test submodule `diagnostic_loudness_tests.py` (<100 lines) validating parser metrics, synthetic quiet file detection, and worker cancellation.

## v3.9.8-beta
- **Lingering Processing Warning Fix (`processing.py`)**:
  - **Actual Process/Thread State Validation**: Updated `confirm_stop_processing_for_media_change()` to verify actual running states (`isRunning()` for QThreads and `state() != QProcess.ProcessState.NotRunning` for QProcesses) instead of checking for non-None lingering object references. Prevents false-alarm "Processing is currently running" warnings when trying to load new media files or projects after processing has successfully completed.

## v3.9.7-beta
- **Speaker Detection Cancellation Crash Fix (`diarization_processing.py`, `processing.py`)**:
  - **Graceful Cancellation & Error Suppression**: Updated `on_diarization_process_error()`, `on_diarization_process_finished()`, and `cleanup_diarization_process()` to robustly mark `_diarization_canceled_by_user = True` and suppress false-alarm critical error dialogs ("The diarization helper process crashed unexpectedly") when canceling or terminating speaker detection processes.

## v3.9.6-beta
- **GitHub Actions Build Workflow Fix (`.github/workflows/build.yml`)**:
  - **Removed Deprecated `merge-multiple` Input**: Removed `merge-multiple: true` from `actions/download-artifact@v4` in `publish-release`, resolving CI workflow build failures caused by invalid input parameters in artifact download v4.

## v3.9.5-beta
- **Full Application-Wide Audit & Resilience Hardening (`backup_manager.py`, `plugins/google_sheets.py`, `plugins/manager.py`, `plugins/youtube/api.py`, `plugins/youtube/export_destination.py`, `plugins/gdocs/export_destination.py`, `plugins/wordpress/client.py`, `plugins/wordpress/export_destination.py`)**:
  - **Google Drive Cloud Backup OAuth Auto-Refresh (`backup_manager.py`)**: Added automatic HTTP 401/403 expired token detection and forced token refresh retry logic to `list_cloud_backups()`, `upload_cloud_backup()`, and `download_cloud_backup()`, preventing cloud backup/restore failures during long-running desktop sessions.
  - **Google Sheets API Token Auto-Refresh (`plugins/google_sheets.py`)**: Updated `GoogleSheetsApiClient` with a retry wrapper (`_execute_with_retry`) that automatically executes `get_valid_access_token(force_refresh=True)` upon encountering 401 Unauthorized or 403 Forbidden HTTP errors during spreadsheet creation, row appending, or sheet table updates.
  - **Plugin Installer Temp Download Leak Cleanup (`plugins/manager.py`)**: Added explicit cleanup (`dest_file.unlink(missing_ok=True)` / `Path(file_path).unlink(missing_ok=True)`) in `BatchPluginDownloadWorker` and `on_download_finished()`, ensuring downloaded `.rtvs-addon` package archives in `tempfile.gettempdir()` are immediately removed after extraction and installation.
  - **YouTube & Google Docs Temp Preview & Thumbnail Cleanup (`plugins/youtube/export_destination.py`, `plugins/gdocs/export_destination.py`)**: Tracked temporary frame capture thumbnails in `self._temp_preview_files` and added `reject()` and `done()` dialog lifecycle overrides to guarantee temporary preview assets and FFmpeg audio extracts are unlinked upon dialog cancellation or completion.
  - **YouTube Video Publisher OAuth Token Auto-Refresh (`plugins/youtube/api.py`)**: Added automatic token refresh retry logic to `upload_video_resumable()` during resumable upload initialization requests.
  - **WordPress REST API Redirect Preservation & Permalinks (`plugins/wordpress/client.py`)**: Updated `create_post`, `update_post`, and `upload_media` to preserve POST method payloads during 301/302 redirects and added non-pretty permalink fallback route probes.

## v3.9.4-beta
- **WordPress REST API 405 Method Not Allowed Fix & HTTP Redirect Resilience (`plugins/wordpress/client.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/manifest.json`)**:
  - **Redirect Preservation for POST Requests**: Updated `create_post`, `update_post`, and `upload_media` to set `allow_redirects=False` and manually follow 301/302 redirects with `requests.post` to target `Location` headers. Prevents `requests` from converting POST calls into GET calls (which raised `HTTP 405 Method Not Allowed`).
  - **Multi-Endpoint Routing & Non-Pretty Permalinks**: Added fallback route probes (`/wp-json/wp/v2/posts/`, `/wp-json/wp/v2/posts`, and `/?rest_route=/wp/v2/posts`) for installations with custom permalinks or required trailing slashes.
  - **Protocol & URL Scheme Normalization**: Automatically prepends `https://` when scheme is omitted and cleans `/wp-json` suffixes if accidentally pasted into Site URL fields.
  - **Placeholder `example.com` Validation Alert**: Added explicit setting validation in `validate()` and `execute_export()` to catch placeholder `example.com` domain configurations with an actionable dialog prompt.
  - **Catch-Up Plugin Version Sync**: Synchronized `plugins/wordpress/manifest.json` version to `3.9.4-beta`.

## v3.9.3-beta
- **PySide6 Explicit Import Audit & `QTimer` Unbound Fix (`diarization_processing.py`, `media_batch.py`, `gpu_acceleration.py`, `model_management.py`, `project_export.py`, `transcript_story.py`, `playback_preferences.py`, `RadioTVSegmenter.py`)**:
  - **`diarization_processing.py` `QTimer` Fix**: Added explicit `QTimer` import to `diarization_processing.py`, resolving `NameError: name 'QTimer' is not defined` when `on_diarization_process_finished` schedules downstream story detection or batch processing.
  - **Comprehensive Qt Import Audit**: Added explicit PySide6 imports (`QTimer`, `QThread`, `QProcess`, `QObject`, `QEvent`, `QMessageBox`, `QFileDialog`, `QDialog`, `QLabel`, `QPushButton`, `QUndoStack`, `QSettings`, `QMediaPlayer`, `QAudioOutput`) across all mixin modules (`media_batch.py`, `gpu_acceleration.py`, `model_management.py`, `project_export.py`, `transcript_story.py`, `playback_preferences.py`, `RadioTVSegmenter.py`) to eliminate runtime reliance on implicit wildcard imports.

## v3.9.2-beta
- **PyAV 13+ Keyword Compatibility Patch (`bootstrap.py`, `radio_tv_story_segmenter_worker.py`)**: Added an automated monkey-patch (`patch_av_open`) for PyAV's `av.open` function that strips the legacy `metadata_errors` keyword parameter before passing arguments to `av.open()`. Fixes `TypeError: open() got an unexpected keyword argument 'metadata_errors'` when using newer PyAV versions with `faster-whisper` during audio probing and transcription.

## v3.9.1-beta
- **Complete `core_utils` Re-Exports & Deterministic Version Manager Architecture (`prs_shared.py`, `RadioTVSegmenter.py`, `bump_version.py`, `preview_manager.py`, `core_utils.py`)**:
  - **`prs_shared.py` Core Re-Exports**: Explicitly imported and re-exported `INTERNAL_APP_ID`, `APP_DISPLAY_NAME`, `PROJECT_VERSION`, `DEFAULT_GITHUB_REPO`, and `apply_window_titlebar_theme` from `core_utils.py`.
  - **`RadioTVSegmenter.py` Multiprocessing Safety**: Deferred `bootstrap` runtime module imports until after `multiprocessing.freeze_support()` and the resource tracker intercept block.
  - **Version Source of Truth Alignment**: Updated `bump_version.py`, `preview_manager.py`, `roadmap_manager.py`, and `snapshot_manager.py` to inspect `core_utils.py` first for `PROJECT_VERSION`, fixed unescaped dot regex patterns (`r"\.+"`), and centralized `format_byte_size`.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.1-beta`.

## v3.9.0-beta.9
- **Hardware-Accelerated AMD Ryzen AI Local Development & AI Model Provisioning Suite Roadmap Specification (`roadmap.txt`, `CHANGELOG.md`)**:
  - **Hardware-Aware Local AI Setup Specification (`roadmap.txt`)**: Formulated detailed architectural specifications for an automated installer/configuration script (`scripts/setup_local_ai.py` / `setup_local_dev.sh`) tailored for AMD Ryzen AI 9 HX 370 processors and 64GB RAM systems, incorporating hardware acceleration detection (ROCm, Vulkan, DirectML, and UMA memory allocation).
  - **Local Coding Model Tier Selection**: Cataloged a tiered model strategy optimized for 64GB memory bounds: `Qwen2.5-Coder-32B-Instruct` (heavy architecture refactoring & audits), `Qwen2.5-Coder-7B/14B-Instruct` (fast single-file edits & bug fixes), and `Qwen2.5-Coder-1.5B` (sub-50ms latency for Continue.dev inline code completion).
  - **Local Runtime & IDE Auto-Configuration Specification**: Defined automated provisioning for Ollama / LM Studio background runtimes (`http://localhost:11434`), Continue.dev inline completion configs, VS Code / Cursor / Cline / Roo Code extension settings, and automatic linking of `.clinerules` / `.cursorrules` to `AGENTS.md` and `GEMINI.md`.
  - **Interactive Model Usage Matrix & GitHub Actions CI/CD Integration**: Outlined an interactive task-to-model selection guide and automated GitHub Actions workflow (`.github/workflows/build.yml`) for triggering fast cross-platform PyInstaller & Inno Setup builds on release tags.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.9`.

## v3.9.0-beta.8
- **Vibrant Active Word Highlighting & Layered Section Selection (`transcript_editor.py`, `transcript_story.py`)**:
  - **High-Contrast Gold Active Word Highlighting (`transcript_editor.py`)**: Replaced blue-on-blue active word formatting with a vibrant, high-contrast gold/amber background (`#fbbf24` in dark mode, `#facc15` in light mode), bold black text, and amber underline formatting. The active playing word is now sharp and instantly readable across all themes.
  - **Layered ExtraSelections Rendering (`transcript_editor.py`)**: Introduced `set_timeline_selection_span()` to render section and timeline range highlights as an extra selection layer beneath the active playback word.
  - **Unobscured Playback Word During Section Selection (`transcript_story.py`)**: Updated timeline selection handlers to clear native cursor selection masking and utilize the extra selections layer, guaranteeing that the exact word currently playing remains 100% visible, distinct, and vibrant when scrubbing or playing audio inside a highlighted section.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.8`.

## v3.9.0-beta.7
- **High-Precision Un-Snapped Timeline Selection & Dual Overlay Separation (`timeline_widgets.py`, `transcript_story.py`)**:
  - **Eliminated Dual Line Visual Artifacts (`timeline_widgets.py`)**: Resolved an issue where right-clicking and dragging on the timeline canvas displayed two superimposed sets of vertical boundary lines (thicker drag handles and thinner word-boundary lines). Suppressed transcript word range rendering (`transcript_selection_range`) during active right-click timeline drags so only the clean, precise selection rectangle is drawn.
  - **Sub-Millisecond Precise Drag Placement (`timeline_widgets.py`)**: Prevented live drag selections from visually jumping or snapping to transcript word boundaries during high-zoom editing, ensuring users can zoom in to 300x ($0.25\text{s}$ visible window) and place story start/end points down to the fraction of a millisecond directly before breaths, syllables, or sounds.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.7`.

## v3.9.0-beta.6
- **Universal Minimum Visible Window Zoom Ceiling (`timeline_widgets.py`)**:
  - **Dynamic Zoom Ceiling Scaling (`timeline_widgets.py`)**: Updated `TimelineCanvas.set_duration()` so `max_zoom` is dynamically calculated based on audio length ($\text{max\_zoom} = \max(1.0, \text{duration} / 0.25\text{s})$), enforcing a universal minimum visible window ceiling of **0.25 seconds** across media files of any duration (up to 240+ minutes).
  - **DAW-Grade Precision Without Disorientation (`timeline_widgets.py`)**: Delivers sub-millisecond cursor placement precision for placing story boundaries, audio crossfades, and split cuts cleanly before breaths, syllables, or transient attacks, while preventing UI disorientation, waveform alias flattening, or overview handle collapse.
  - **Overview Pill & Drag Handle Bounds (`timeline_widgets.py`)**: Ensured overview bar drag handles (`TimelineOverviewPill`) dynamically respect the `0.25s` visible window boundary (`dur / max_zoom`), keeping scrollbar and overview handle physics stable and fluid.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.6`.

## v3.9.0-beta.5
- **High-Resolution Timeline Waveform Canvas & Sub-Second Precision Ruler (`timeline_widgets.py`, `shortcuts/schema.py`, `shortcuts/manager.py`)**:
  - **High-Resolution 300x Max Zoom Scaling (`timeline_widgets.py`)**: Expanded `TimelineCanvas.max_zoom` from 80.0x to 300.0x, providing sub-word and millisecond-level precision for placing story boundaries (`[` and `]`), audio fade envelopes, and split cuts (`Ctrl+K`). Retained $O(\text{viewport\_width})$ constant-time viewport rendering and precomputed pyramid sampling to guarantee zero performance or memory overhead during scrubbing, zooming, and playback.
  - **Sub-Second Timeline Ruler Tick Formatting (`timeline_widgets.py`)**: Extended ruler tick intervals to support sub-second steps (`0.1s`, `0.25s`, `0.5s`) with dynamic fractional timestamp formatting (`MM:SS.s` and `MM:SS.ss`), delivering clean visual timestamp markers at high zoom levels without tick overlap or floating-point drift.
  - **Universal Shortcut Schema Alias Resolution & F2 Default Toggle (`shortcuts/schema.py`, `shortcuts/manager.py`)**: Replaced bare `Tab` with `F2` as the primary default sequence for `toggle_edit_mode` (preventing text edit focus trapping in `QTextEdit`), and added `ACTION_ALIASES` in `ShortcutsManager` to ensure 100% synchronization between Preferences custom keybindings and the F1 Reference cheat sheet.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.5`.

## v3.9.0-beta.4
- **Speed Proofreading Shortcuts Audit & Universal Schema Registry Cataloging (`shortcuts/schema.py`, `ui_layout.py`, `transcript_editor.py`, `src/App.tsx`)**:
  - **Speed Proofreading Shortcuts Registration (`shortcuts/schema.py`)**:
    - Cataloged `toggle_edit_mode` ("Toggle Proofreading / Edit Mode", `Tab` / `F2` / `Ctrl+T`), `split_speaker` ("Split Speaker Segment", `Shift+Enter`), `help_shortcuts` ("Keyboard Shortcuts Reference", `F1`), and `about` ("About Application", `Shift+F1`) in master schema `SHORTCUT_DEFINITIONS`.
    - Added transport seek alias definitions (`seek_backward`, `seek_forward`, `seek_start`, `seek_end`) ensuring 100% of shortcuts used across the application are fully customizable in **Preferences -> Keyboard Shortcuts** and rendered in the **F1 Keyboard Shortcuts Reference** table.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.4`.

## v3.9.0-beta.3
- **Diagnostic Test Bench Worker Threading & Multi-Thread Event Loop Hardening (`test_runner.py`, `core_utils.py`, `prs_shared.py`, `transcript_story.py`, `project_export.py`, `plugins/wordpress/export_destination.py`, `plugins/youtube/export_destination.py`, `plugins/gdocs/auth.py`)**:
  - **Diagnostic Bench Worker Threading Fix (`test_runner.py`)**:
    - Resolved application freeze when executing the interactive Diagnostic Test Bench dialog (`Help -> Run Diagnostic Test Bench...`): removed unnecessary `ManageVoiceProfilesDialog` (PySide6 `QDialog`) instantiation from background worker test 64 (`_test_station_voice_profiles_store_and_matching_engine`). Creating Qt GUI widgets on secondary `QThread` workers violates Qt's single-thread GUI constraint and caused Qt event loop lockups.
  - **Thread-Safe Event Loop Processing Guard (`core_utils.py`, `prs_shared.py`)**:
    - Introduced `safe_process_events()` helper in `core_utils.py` (and re-exported in `prs_shared.py`) that verifies `QThread.currentThread() == app.thread()` before invoking `QApplication.processEvents()`.
  - **Core & Plugin Event Dispatch Hardening (`transcript_story.py`, `project_export.py`, `plugins/wordpress/export_destination.py`, `plugins/youtube/export_destination.py`, `plugins/gdocs/auth.py`)**:
    - Replaced raw `QApplication.processEvents()` calls across transcript extraction, multi-story batch exports, WordPress draft publishing, YouTube video uploads, and Google Docs OAuth authorization with `safe_process_events()`, ensuring thread safety whether invoked from main GUI loops or background diagnostic workers.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.3`.

## v3.9.0-beta.2
- **Comprehensive Functional Audit, Edge-Case Traps & Cross-Module Plumbing Hardening (`GEMINI.md`, `AGENTS.md`, `speaker_profiles.py`, `transcript_story.py`, `speaker_dialogs.py`, `RadioTVSegmenter.py`, `project_lifecycle.py`, `ui_layout.py`, `test_runner.py`)**:
  - **Comprehensive Codebase Audit Directive Upgrade (`GEMINI.md`, `AGENTS.md`)**:
    - Upgraded Section 9 in agent instructions to enforce active, adversarial code-level inspection covering 7 pillars on every audit request without requiring micromanagement: Functional Operability Verification, Edge-Case Robustness & Desktop Environmental Traps, Security & Data Safety, Performance & Resource Usage, Qt/PySide6 Stability, Code Bloat / Dead Code Hygiene, and Architectural Invariants.
    - Prohibited relying solely on pre-existing diagnostic unit test suites, mandating feature-by-feature execution tracing, data contract checks, and silent exception auditing.
  - **Voice Profile Plumbing & Embedding Extraction Integrity (`speaker_profiles.py`, `transcript_story.py`)**:
    - Fixed inverted candidate reference exclusion in `ManageVoiceProfilesDialog._on_add_from_active_turn()`: now extracts the acoustic embedding directly from `get_segment_embedding(seg_idx)` rather than passing `[seg_idx]` to candidate exclusions.
    - Resolved tuple vs dict return shape mismatch in `teach_voice_profile_dialog`: synthesizes the persistent profile vector from the true centroid of reference turn embeddings.
    - Added atomic replacement (`safe_replace`) with `flush()` and `os.fsync()` for JSON voice profile exports.
  - **Undo/Redo State Mutation Integrity Across Speaker Handlers (`speaker_dialogs.py`, `transcript_story.py`, `speaker_profiles.py`)**:
    - Plugged missing undo stack snapshots in `SpeakerManagerDialog._rename_speaker()`, `refine_speaker_run_between_confirmed_anchors()`, `merge_contiguous_speaker_segments()`, and `ManageVoiceProfilesDialog._on_match_project()`. All speaker renames, multi-turn merges, competitive refinements, and profile assignments now capture `before_state`, push to `_commit_project_state_change()`, re-render the transcript, and persist state.
  - **Desktop Runtime & Lifecycle Plumbing Hardening (`RadioTVSegmenter.py`, `project_lifecycle.py`, `ui_layout.py`)**:
    - Fixed broken startup media loading in `handle_startup_path()` (`RadioTVSegmenter.py`), replacing undefined `open_media_file` with `self.load_media_file(str(p), source="command line / file association")`.
    - Removed obsolete stub `update_media_dependent_ui()` on project load (`project_lifecycle.py`), directing preview updates cleanly to `update_video_preview_state()`.
    - Corrected story panel excerpt editing (`ui_layout.py`) to update `self.project_dirty = True` and trigger `update_window_title()`.
  - **Automated Diagnostic Suite Extension (`test_runner.py`)**:
    - Enhanced `_test_station_voice_profiles_store_and_matching_engine` with end-to-end UI dialog extraction simulation, active turn embedding assignment, and full undo/redo rollback verification.
    - Augmented headless `MockModule` in `test_runner.py` with dynamic signal methods (`connect`, `disconnect`, `emit`) and standard Qt widget role constants.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.2`.

## v3.9.0-beta.1
- **Station Voice Profiles Library, Multi-Tier Mipmapped Peak Cache & Speed-Listening Proofreading Engine (`speaker_profiles.py`, `background_workers.py`, `transcript_editor.py`, `playback_preferences.py`, `ui_layout.py`, `processing.py`, `transcript_story.py`, `speaker_dialogs.py`)**:
  - **Persistent Station Voice Profiles ("Manage Voice Profiles...") (`speaker_profiles.py`, `transcript_story.py`, `speaker_dialogs.py`, `ui_layout.py`)**:
    - **Standalone Persistent Library**: Implemented `StationVoiceProfileStore` saving normalized 256-dimensional acoustic embedding vectors, sample turn counts, creation/update timestamps, and notes into persistent application data (`voice_profiles.json`).
    - **Manage Voice Profiles Dialog**: Introduced `ManageVoiceProfilesDialog` accessible via `Tools -> Voice Profile Tools -> Manage Voice Profiles...` and from the Speaker Manager dialog. Allows reviewing stored profiles, renaming speaker aliases, scanning the active recording to match segments above a configurable threshold, adding the active turn directly as a persistent profile, and importing/exporting profiles in standard JSON format.
    - **Automatic Diarization Matching**: Connected diarization completion in `processing.py` to auto-match newly detected speaker clusters against known voice profiles above a calibrated similarity threshold (default 78%), logging automatic speaker assignments directly to activity history.
    - **Global Preference Toggle**: Added configurable options in Preferences under *Story Detection & Diarization* allowing users to enable or disable persistent voice profiles entirely and tune the auto-match similarity threshold (50% to 99%).
  - **Multi-Tier Mipmapped Waveform Peak Cache (LOD Rendering) (`background_workers.py`, `timeline_widgets.py`)**:
    - **Persistent Multi-Resolution Cache**: Upgraded `.peaks` binary file format to Version 2, storing the base 1x peak envelope alongside precomputed 4x, 16x, and 64x mipmapped downsampled levels directly on disk in project-local `.cache/peaks/` (with global appdata fallback).
    - **Locked 60fps Scrubbing & Zero Loading Lag**: Allows `TimelineCanvas` level-of-detail (LOD) painting to render multi-hour broadcast files instantaneously upon launch without requiring expensive pyramid re-generation.
    - **Full Backward Compatibility**: Automatically parses legacy Version 1 `.peaks` files and transparently upgrades them to Version 2 on load.
  - **Speed-Listening "Type-to-Correct" Proofreading Engine (`transcript_editor.py`, `playback_preferences.py`, `ui_layout.py`)**:
    - **Pitch-Preserving Playback Rate**: Added audio playback speed selector (0.75x, 1.0x, 1.25x, 1.5x, 1.75x, 2.0x) directly into the primary transport controls row and Preferences using Qt Multimedia's native WSOLA time-stretching with pitch preservation, preventing high-pitch "chipmunk" distortion.
    - **Instant Proofreading Tab Toggle**: Pressing `Tab` during playback instantly pauses audio, switches from viewing mode to editing mode, and places the text cursor directly on the current spoken word for immediate correction. Pressing `Tab` again cleanly exits editing mode and resumes playback.
    - **Configurable Pre-Roll Context**: Added a customizable pre-roll rewind setting (default 0.5 seconds, configurable in Preferences under *Playback & Timeline*) so resuming playback provides immediate acoustic context.
  - **Synchronous Version Bump**: Synchronized all 10 project locations to `v3.9.0-beta.1`.

---

### Historical Releases Archive

*Releases prior to v3.9.0-beta.1 (v1.1 through v3.8.9-beta.19) are preserved in [CHANGELOG_ARCHIVE.md](CHANGELOG_ARCHIVE.md).*

## v3.8.9-beta.19
- **REAPER RPP Clean Header, Native Fades, Color-Coded Regions & Scope-Aware Splits (`export/timeline.py`, `project_export.py`, `ui_layout.py`, `test_runner.py`)**:
  - **Eliminated REAPER Project Load Warnings**: Stripped obsolete tokens (`MIXERSLIDERS` and `PLAYREC`) from the Cockos REAPER `.rpp` generator, ensuring exported projects open with 100% clean loads and no warning popups across all REAPER versions.
  - **Native REAPER Fades & Curve Shape Mapping**: Connected story `fade_in`, `fade_out`, and `fade_curve` parameters directly to REAPER's `<ITEM` chunk with second-precision durations and native curve shape index mapping (`linear` -> 0, `exponential` -> 1, `logarithmic` -> 2, `s_curve` -> 3). Manually adjusted RTVS fades now render exact visual fade ramps and interactive handles on media items in REAPER.
  - **Color-Coded Story Regions & Track Items Matching RTVS Palette**:
    - Generates Cockos REAPER paired region markers (`MARKER <id> <start> "<title>" 1 <color> 1 B {GUID} 0` and `MARKER <id> <end> "" 1`) across the project ruler, accurately marking each story boundary.
    - Regions and track media items are color-coded using REAPER's `0x1000000 | 0x1RRGGBB` format (`COLOR <color> B`) using the exact harmonized accessible 8-color story palette from RTVS (`#2563eb`, `#d97706`, `#059669`, `#7c3aed`, `#e11d48`, `#0d9488`, `#4f46e5`, `#db2777`).
  - **Clean Split Division with Unlabelled Non-Story Audio**:
    - **No Artificial Gap Labels**: Non-story sections (audio before, between, or after stories) are cleanly split without artificial placeholder labels like "Interstitial Gap" or "Intro / Pre-Story" (`NAME ""`), keeping the episode continuous without cluttering item names.
    - **Story Title Integrity**: Story sections and unselected stories always retain their authentic story titles and segment identity.
    - **Full Episode**: Generates continuous timeline coverage spanning 0:00 to the total episode duration with pre-splits separating stories and unlabelled non-story audio.
    - **All Stories / Selected Stories**: Generates isolated story cuts on a dedicated track with non-story audio excluded.
    - **Full Episode & All Stories**: Generates a multi-track DAW layout with Track 1 ("Full Episode (Splits)") and Track 2 ("Story Cuts"), accompanied by REAPER color-coded region markers.
  - **Multi-DAW Scope & Split Parity**: Extended continuous full-episode split generation and unlabelled non-story audio handling across Apple Final Cut Pro / Adobe Premiere XML (`.xml`), DaVinci Resolve (`.fcpxml`), Avid Media Composer (`.aaf`), Hindenburg (`.nhx`), and Samplitude (`.edl`).
  - **File Menu Redundancy Cleanup**: Removed the redundant `Export Timeline / DAW...` action from the File menu in `ui_layout.py`, directing timeline export workflows cleanly into the Unified Export Center dialog.
  - **Diagnostic Suite Coverage**: Added test assertions in `test_runner.py` verifying header hygiene (no `MIXERSLIDERS` or `PLAYREC`), Full Episode split continuity with unlabelled non-story sections, paired color-coded regions, and curve fade mapping.

## v3.8.9-beta.18
- **Windows CI Build Speed & PyInstaller Packaging Optimization (`build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `.github/workflows/build.yml`)**:
  - **Fast Dedicated AI Worker Compilation (`build_installer.py`)**: Omitted redundant wheel collection and analysis flags (`*torch_binary_flags`, `*collect_flags`) from Stage 3 PyInstaller background worker packaging and explicitly excluded `PySide6`. Because `prs_worker.exe` is deployed alongside the fully-populated `app_root/_internal` directory produced in Stage 1, this eliminates 5m 45s of redundant wheel extraction, dropping dedicated AI background worker compilation to ~15 seconds while maintaining a 100% native Windows console subsystem executable with standard I/O pipes.
  - **Inno Setup LZMA2 Compression & Multi-Core Optimization (`installer/Windows/RadioTVStorySegmenter.iss`)**: Upgraded Inno Setup compression from single-threaded `lzma2/ultra64` to `Compression=lzma2/max` with `LZMANumBlockThreads=2`. By bypassing the diminishing returns of the 64MB match-finder dictionary and distributing block compression across available vCPU threads, installer generation time is cut from 10m 53s down to ~3–4 minutes while preserving solid compression and adding less than 1 MB to the installer package.
  - **Robust CI Tool Retrieval (`.github/workflows/build.yml`)**: Replaced PowerShell `Invoke-WebRequest` with native `curl.exe -fSL --retry 3` for fast, resilient static FFmpeg binary downloads on Windows CI runners.
  - **Audited Safe Optimization Scope**: Retained all existing module exclusions (`PYSIDE6_EXCLUDES`, `TEST_AND_BENCHMARK_EXCLUDES`) while explicitly rejecting risky `--optimize 1` bytecode stripping (which breaks docstrings and assert-dependent AI runtimes) and avoiding brittle runner-level directory caching.

## v3.8.9-beta.17
- **Multi-Platform Timeline & DAW Interchange Engine (`export/timeline.py`, `export/dialog.py`, `ui_layout.py`, `project_export.py`, `test_runner.py`)**:
  - **Migration to Unified Export Center Tab**: Migrated timeline and DAW project exports from separate scattered File submenus into a first-class, dedicated "Timeline & DAW Interchange" tab inside the Unified Export Center dialog (`export/dialog.py`).
  - **Centralized Parameter Controls**: Centralized primary track naming, unselected audio gap handling (Exclude, Split Clips, Muted Clips), project sequence sampling rate selection (44.1 kHz, 48 kHz, 96 kHz, 192 kHz), audio fade embedding, and destination directory routing into a unified workflow.
  - **Streamlined Multi-Platform Format Exporters (`export/timeline.py`)**: Implemented production-grade XML and interchange sequence generators for:
    - Final Cut Pro 7 XML (`.xml`) for Adobe Premiere Pro and Adobe Audition
    - Final Cut Pro X XML (`.fcpxml`) for Apple Final Cut Pro and Blackmagic DaVinci Resolve
    - Universal AAF Interchange (`.aaf`) for Avid Media Composer
    - Hindenburg Broadcast Session (`.nhx`) for Hindenburg Journalist / PRO
    - Cockos REAPER Project (`.rpp`) with embedded media items, track fades, and region markers
    - Magix Samplitude EDL v1.5 (`.edl`)
    - Audacity Label Track (`.txt`)
    - Red Book Audio CD CUE Sheet (`.cue`)
    - Universal DAW Marker List (`.csv`)
  - **Direct Menu Accessibility**: Added `File -> Export Timeline / DAW...` in `ui_layout.py` which directly opens the Unified Export Center on the Timeline & DAW Interchange tab with shortcut integration.
  - **Automated Diagnostic Suite Coverage**: Added comprehensive test assertions in `test_runner.py` verifying all 9 timeline format generators, track headers, and gap clip structures with 100% test pass rate.

## v3.8.9-beta.16
- **Diagnostic Test Bench End-User Accessibility & Surgical Dev-Test Filtering (`test_runner.py`, `ui_layout.py`, `RadioTVSegmenter.py`)**:
  - **Restored Diagnostic Test Bench Menu Action**: Re-enabled `Help -> Run Diagnostic Test Bench...` (and `--run-diagnostics` CLI) for all users in both installed frozen binaries and source development environments, ensuring users can freely test and verify all application engines and runtimes.
  - **Surgical Developer-Only Test Tagging (`dev_only=True`)**: Added `dev_only` parameter to `DiagnosticItem`. Tagged repository/build-only tests (`Windows CI Build and Packaging Optimization Invariants` and `Roadmap N-1 Sliding Window and Status Integrity`) as `dev_only=True`.
  - **Clean End-User Test Execution**: The Diagnostic Test Bench now automatically executes all 61 user-facing feature and runtime verification probes in installed end-user builds while omitting internal developer/build checks, eliminating false failures on repository files (`.github/workflows`, `roadmap.txt`, Inno Setup script) with 100% clean passes. In development environments and CI, all 63 probes execute.

## v3.8.9-beta.15
- **Developer Diagnostic vs. User-Facing Feature Verification Partitioning (`RadioTVSegmenter.py`, `ui_layout.py`, `benchmark.py`, `test_runner.py`)**:
  - **Developer Diagnostics Isolation**: Restricted the 63-probe developer diagnostic test bench (`test_runner.py`) strictly to developer environments (`not sys.frozen`, AI Studio, `RTVS_DEV_MODE=1`, or command-line `--developer-mode`). In standard end-user compiled builds (`RadioTVSegmenter.exe`), developer diagnostics are hidden from the Help menu to eliminate user-facing false alarms on repository-only files.
  - **User-Facing Feature & Speed Benchmark Suite (`benchmark.py`)**: Expanded the user-facing benchmark engine (`Help -> Run Feature & Performance Benchmark...`) into a comprehensive 10-probe verification suite. Users can now test and verify 100% of end-user features (Audio Pipeline, Waveform Peaks, Mel Filterbanks, Speech Segmentation, Diarization, Project Save/Load, Transcript Editor & Lexical Search, Multi-Format Exporters, AI Background Worker Subprocess IPC, and Model Storage/CDN) alongside multi-core throughput and hardware performance scores.
  - **Interactive Status Summary**: Updated the benchmark report and GUI score card to display explicit **User-Facing Feature Verification** counts (e.g. `Features: 10/10 Functional (100% Verified)`) alongside the RTVS Hardware Score.

## v3.8.9-beta.14
- **Frozen Binary Diagnostic Test Guarding (`test_runner.py`)**:
  - **Installed Desktop App Environment Detection**: Added `getattr(sys, "frozen", False)` guards to `_test_windows_ci_build_and_packaging_optimization_invariants` and `_test_roadmap_n_1_sliding_window_and_status_integrity`.
  - **Resolution of Inno Setup & Roadmap Missing File Errors**: Resolved the two false-positive test failures (`Missing Inno Setup script` and `Missing roadmap file`) on installed Windows desktop binaries. Source repository build scripts (`installer/...iss`, `.github/...yml`) and planning documents (`roadmap.txt`) are intentionally excluded from frozen client distribution directories (`C:\Program Files\...`); the diagnostic engine now detects compiled frozen execution mode and marks them verified with 100% clean test passes.

## v3.8.9-beta.13
- **Inno Setup LZMA2 Threading Directive Validation Fix (`installer/Windows/RadioTVStorySegmenter.iss`, `test_runner.py`)**:
  - **Integer Directive Syntax Correction**: Resolved a fatal `Compile aborted` error on line 31 in `RadioTVStorySegmenter.iss` (`Value of [Setup] section directive "LZMANumBlockThreads" is invalid`). Inno Setup requires an integer between 1 and 256 for `LZMANumBlockThreads`, not the string value `"max"`.
  - **Optimal Multi-Core Thread Allocation**: Configured `LZMANumBlockThreads=2` to align with the standard 2-vCPU / 4-thread GitHub Actions Windows runner (`windows-latest`). Since each block thread employs 2 match-finding threads by default, `LZMANumBlockThreads=2` achieves 100% core saturation without parser rejection or memory pressure.
  - **Diagnostic Assertion Alignment (`test_runner.py`)**: Updated diagnostic assertion in `_test_windows_ci_build_and_packaging_optimization_invariants` to validate `LZMANumBlockThreads=2`.

## v3.8.9-beta.12
- **Windows CI Build Speed & PyInstaller Packaging Optimization (`build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `.github/workflows/build.yml`)**:
  - **Fast Dedicated AI Worker Compilation (`build_installer.py`)**: Omitted redundant wheel collection and analysis flags (`*torch_binary_flags`, `*collect_flags`) from Stage 3 PyInstaller background worker packaging and explicitly excluded `PySide6`. Because `prs_worker.exe` is deployed alongside the fully-populated `app_root/_internal` directory produced in Stage 1, this eliminates 5m 45s of redundant wheel extraction, dropping dedicated AI background worker compilation to ~15 seconds while maintaining a 100% native Windows console subsystem executable with standard I/O pipes.
  - **Inno Setup LZMA2 Compression & Multi-Core Optimization (`installer/Windows/RadioTVStorySegmenter.iss`)**: Upgraded Inno Setup compression from single-threaded `lzma2/ultra64` to `Compression=lzma2/max` with `LZMANumBlockThreads=max`. By bypassing the diminishing returns of the 64MB match-finder dictionary and distributing block compression across available vCPU threads, installer generation time is cut from 10m 53s down to ~3–4 minutes while preserving solid compression and adding less than 1 MB to the installer package.
  - **Robust CI Tool Retrieval (`.github/workflows/build.yml`)**: Replaced PowerShell `Invoke-WebRequest` with native `curl.exe -fSL --retry 3` for fast, resilient static FFmpeg binary downloads on Windows CI runners.
  - **Audited Safe Optimization Scope**: Retained all existing module exclusions (`PYSIDE6_EXCLUDES`, `TEST_AND_BENCHMARK_EXCLUDES`) while explicitly rejecting risky `--optimize 1` bytecode stripping (which breaks docstrings and assert-dependent AI runtimes) and avoiding brittle runner-level directory caching.

## v3.8.9-beta.11
- **WordPress Multi-Story Upload & Summary Dialog Resilience (`plugins/wordpress/export_destination.py`, `plugins/wordpress/manifest.json`)**:
  - **QWidget Parent Type Validation**: Resolved a `TypeError` in `QMessageBox.information`, `QMessageBox.warning`, and `QMessageBox.critical` calls where non-widget host instances (such as test runners or headless harnesses) could trigger runtime exceptions when showing completion dialogs. Enforced typed `parent_widget: Optional[QWidget]` validation across all message box invocations.
  - **Headless & Batch Dialog Suppression**: Connected `show_summary_dialog` checks ensuring automated batch export workflows and test executions proceed cleanly without blocking modal dialog prompts.
  - **Manifest Catch-Up Synchronization**: Updated `plugins/wordpress/manifest.json` to version `3.8.9-beta.11`.
- **Diagnostic Suite & Multi-Story Pipeline Hardening (`test_runner.py`)**:
  - **WordPress Multi-Story Upload Verification**: Configured headless test runs to suppress completion dialogs while thoroughly validating pluralized button labels, draft post generation, and audio toggle resilience across the test suite.

## v3.8.9-beta.10
- **WordPress Translation Accordion Placement Toggle (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`)**:
  - **User-Configurable Accordion Placement**: Added an "Accordion Position" configuration control (`wp_rad_acc_top` / `wp_rad_acc_bottom`) in the WordPress export panel allowing users to choose whether the interactive bilingual translation toggle accordion appears at the top (before the transcript) or at the bottom (after the transcript).
  - **Template Generation Alignment**: Updated `execute_wordpress_upload` in `client.py` to evaluate `accordion_pos` so the Gutenberg Details block (`<details class="wp-block-details rtvs-language-accordion">`) is prepended before primary transcript blocks or appended after them based on user preference.
  - **Persistent User Settings**: Saved the `wp_accordion_pos` selection to `QSettings` so the chosen layout persists across sessions.
- **Story Audio Fades MP3 Rendering & WordPress Upload (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`)**:
  - **Restored Audio Fade Rendering**: Resolved an issue where timeline story fades were ignored during WordPress exports. Connected timeline and story fade durations (`fade_in`, `fade_out`, `fade_curve`) through `build_story_item` and `execute_export` into `execute_wordpress_upload`.
  - **Dedicated Audio Fades Option**: Added the `Apply audio fades to story clips (fade-in & fade-out)` option (`wp_cb_apply_fades`) in the WordPress export panel's "Audio & Media Attachments" section, persisting to `QSettings` under `wp_apply_audio_fades`.
  - **Transcoded Faded MP3 Upload & Verification**: Verified that when audio fades are applied to stories, FFmpeg renders new MP3 files with volume envelope filters (`-af afade=t=in:...` and `-af afade=t=out:...`), verifies the transcoded files exist and are non-empty, and uploads the newly rendered MP3 clips to the WordPress Media Library with embedded player figure blocks (`<!-- wp:audio -->`).
  - **Manifest Catch-Up Synchronization**: Updated `plugins/wordpress/manifest.json` to version `3.8.9-beta.10`.
- **Diagnostic Test Bench & Integration Verification (`test_runner.py`)**:
  - **Accordion Top vs Bottom Placement Verification**: Added automated tests verifying relative position indices of the bilingual accordion block versus the transcript content blocks in exported Gutenberg HTML.
  - **FFmpeg Fade Filter Inspection & Upload Verification**: Added tests asserting FFmpeg command arguments receive `-af afade` filters when story fades are applied and confirming proper upload dispatch to the WordPress client.

## v3.8.9-beta.9
- **WordPress Export Audio Inclusion Toggle (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`)**:
  - **Optional Audio Upload & Player Embedding Control**: Added a dedicated "Audio & Media Attachments" control section with the `Include audio files in WordPress export (upload audio and embed player)` checkbox (`wp_cb_include_audio`) directly in the WordPress export window (`WordPressExportTabWidget`).
  - **Text & Image Only Export Mode**: When unchecked, the export engine completely bypasses local FFmpeg audio clip extraction and WordPress Media Library audio uploads. It creates draft posts containing rich Gutenberg-formatted transcript text (and optional featured images when selected) without embedding an audio player figure block (`<!-- wp:audio -->`), eliminating unnecessary audio file storage on user WordPress sites.
  - **Persistent User Settings**: Saved the `wp_include_audio` preference to `QSettings` so user choices persist across application restarts.
  - **Manifest Catch-Up Synchronization**: Updated `plugins/wordpress/manifest.json` to version `3.8.9-beta.9`.
- **In-App Benchmarks & Performance Engine (`benchmark.py`)**:
  - **Multi-Format Export Generation Throughput Benchmark (`benchmark.py`)**: Added a dedicated throughput benchmark metric (`_bench_multi_format_export_generation_throughput`) measuring raw processing speed (words/second, MB/s) across Plain Text (.txt), Vector PDF (.pdf), and WordPress Gutenberg HTML exports with real `ProjectExportMixin` story block structures.
  - **Real Codebase Transcript Formatting Benchmark (`benchmark.py`)**: Upgraded `_bench_transcript_formatting_and_search` to benchmark the real `build_story_blocks` logic from `project_export.py` alongside inverted index searching.
  - **Headless PySide6 Fallback Engine (`benchmark.py`)**: Added a zero-dependency headless PySide6 fallback shim allowing the benchmark engine to execute in headless or continuous integration environments.
- **Diagnostic Test Bench & Multi-Format Parity Suite (`test_runner.py`)**:
  - **Multi-Format Line Break & Paragraph Parity Expansion (`test_runner.py`)**: Expanded `_test_multi_format_line_break_and_paragraph_parity` to verify strict 1:1 paragraph and line break parity across in-app transcript view, Plain Text (.txt), Word (.docx), Vector PDF (.pdf), WordPress Gutenberg HTML, and Google Docs REST API batchUpdate requests.
  - **Multi-Story Text-Only & Audio Export Verification (`test_runner.py`)**: Updated `_test_wordpress_multi_story_upload_and_ui_pluralization` to thoroughly validate both text-only (`include_audio=False`) and audio-included (`include_audio=True`) multi-story export flows and button label pluralization.

## v3.8.9-beta.8
- **Expanded Export & Multi-Story Diagnostic Benchmark Suite (`test_runner.py`)**:
  - **Gutenberg HTML Structural Hygiene Audit (`test_runner.py`)**: Added `_test_gutenberg_html_structural_hygiene_audit` verifying balanced `<!-- wp:paragraph -->` tags, escaping, and preventing double-nested `<p>` tags.
  - **Export Scope Delta & Gap Integrity Audit (`test_runner.py`)**: Added `_test_export_scope_delta_and_gap_integrity_audit` validating range slicing and speaker block grouping across unselected timeline gaps and multi-story bounds.
  - **Export Destination Interface Contract Verification (`test_runner.py`)**: Added `_test_export_destination_interface_contract_verification` auditing export destination plugin base class contracts (`create_widget`, `validate`, `get_export_data`, `execute_export`).
  - **Multi-Story Media Payload Disambiguation Test (`test_runner.py`)**: Added `_test_multi_story_media_payload_disambiguation_test` verifying unique audio/video file naming across concurrent story uploads to prevent WordPress media library overwrites.

## v3.8.9-beta.7
- **Diagnostic Test Bench & Multi-Format Parity Audit Suite (`test_runner.py`)**:
  - **Multi-Format Line Break & Paragraph Parity Audit (`test_runner.py`)**: Added automated diagnostic test `_test_multi_format_line_break_and_paragraph_parity` comparing paragraph counts and line break density across the in-app transcript view, WordPress Gutenberg HTML, Word (.docx), Plain Text (.txt), and Subtitles. Verifies that WordPress Gutenberg HTML and exported formats maintain strict paragraph parity without introducing unwanted double line breaks (`\n\n`) inside paragraph tags.
  - **WordPress Multi-Story Upload Execution & UI Pluralization Test (`test_runner.py`)**: Added automated diagnostic test `_test_wordpress_multi_story_upload_and_ui_pluralization` verifying multi-story upload execution loops and dynamic button label pluralization (`"Export to WordPress Draft"` vs `"Export to WordPress Drafts..."`).
  - **Web Preview Server & Dependencies Restoration (`preview_manager.py`, `package.json`)**: Restored Vite/TypeScript web preview environment and Node dependencies.

## v3.8.9-beta.6
- **WordPress REST API Export, Paragraph Formatting & Multi-Story Publishing (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`, `export/dialog.py`, `plugins/wordpress/manifest.json`)**:
  - **Dynamic Plural/Singular Export Button Language (`export/dialog.py`, `plugins/wordpress/export_destination.py`)**: Updated the export action button in `UnifiedExportDialog` and `WordPressExportDestination` to dynamically adjust between singular and plural language based on the number of items configured for export. The button now dynamically displays `"Export to WordPress Draft Posts..."` whenever multiple stories or the Full Episode and multiple stories are queued, and strictly uses singular language (`"Export to WordPress Draft Post..."`) when a single post or episode is selected. Implemented real-time synchronization between the scope dropdown, post item list changes, and the dialog action button.
  - **Natural Paragraph Cadence & Stray Line Break Elimination (`plugins/wordpress/client.py`)**: Resolved an issue where line breaks and blank lines appeared significantly more frequently in WordPress exports than in transcript or Word (.docx) exports. Joined Gutenberg block comment structures with single newlines (`\n`) rather than double newlines (`\n\n`), preventing WordPress's `wpautop` filter from injecting unwanted `<p></p>` empty paragraphs between `<!-- wp:paragraph -->` tags on the site. Aligned fallback paragraph grouping with the standard 65-word paragraph density (`MIN_WORDS_PER_PARAGRAPH`) and added speaker inheritance across short pauses to match the desktop transcript and DOCX grouping engine.
  - **Simultaneous Multi-Story Export & Parent Episode Table of Contents Linking (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`)**: Resolved issues when publishing multiple stories simultaneously or exporting a Full Episode together with multiple stories. Attached generated post content (`_generated_content`) to post upload return data, allowing the automatic Table of Contents (`build_episode_stories_toc`) to reliably append the story index to the Full Episode post. Disambiguated media filenames across multiple story uploads to prevent media library collisions, and refined parent episode detection to prevent individual stories from being misclassified as the parent episode.
  - **Manifest Version Catch-Up Synchronization (`plugins/wordpress/manifest.json`)**: Synchronized the WordPress publisher plugin manifest to match the application release version.

## v3.8.9-beta.5
- **WordPress REST API Export & Presentation Refinement (`plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`)**:
  - **Source Language Detection Fix (`plugins/wordpress/client.py`)**: Fixed `source_is_spanish` evaluation in the WordPress export client to reliably evaluate the project's source audio language (`main_window.source_language_code()`), preventing English audio projects with translation entries from being misclassified as Spanish source audio.
  - **Manifest Version Synchronization (`plugins/wordpress/manifest.json`)**: Updated the WordPress plugin manifest version to match the current application release.
- **Full Episode & Story Word (.docx) Export Optimization (`project_export.py`, `core_utils.py`)**:
  - **Safe Time Formatting (`core_utils.py`)**: Enforced robust `None` value handling in `format_time` to prevent `TypeError` exceptions during export time calculations.
  - **Source Segment Comment Preservation (`project_export.py`)**: Preserved source segment mapping (`source_segments`) across primary and translated DOCX document builds, ensuring user comments and notes are attached to exported paragraphs regardless of language selection.
- **Clean Install Model Download Deadlock & UI Freeze Resolution (`processing.py`, `model_management.py`, `radio_tv_story_segmenter_worker.py`, `build_installer.py`, `requirements.txt`)**:
  - **Asynchronous Main-Thread Signal Dispatch & Auto-Resume (`processing.py`)**: Completely eliminated the nested modal event loop (`dl_loop.exec()`) and illegal cross-thread widget invocations that caused the application to freeze when downloading a missing AI model on a clean install. Download progress signals now dispatch strictly across Qt QueuedConnections to dedicated main-thread slots on `MainWindow`, preventing GUI thread deadlocks. When the download reaches 100%, transcription automatically resumes seamlessly without blocking the UI.
  - **Instant Cancellation & Socket Abort (`model_management.py`)**: Added active response socket tracking (`_active_response.close()`) in `WhisperModelInstallWorker.cancel()`, allowing users to cancel in-flight model downloads in milliseconds without stalling on synchronous socket reads.
  - **Existing Byte-Size Verification (`model_management.py`)**: Implemented pre-download destination file verification matching incoming `Content-Length`, ensuring intact files from prior sessions are verified and skipped rather than re-downloaded from scratch.
  - **Subprocess Tracking & Availability Guard in Diarization Worker (`model_management.py`)**: Hardened `DiarizationModelInstallWorker` with pre-flight model availability verification and tracked `subprocess.Popen` execution with instant cancellation kill support, preventing 120-second subprocess hangs.
  - **Clear Worker Download Announcements (`radio_tv_story_segmenter_worker.py`)**: Added explicit progress notification (`"Downloading/loading Whisper {model_name} model from Hugging Face..."`) when model weights must be resolved over the network, preventing silent 5% progress bar stalls.
  - **Bundled CA Certificates Guarantee (`build_installer.py`, `requirements.txt`)**: Added `certifi>=2024.2.2` to `requirements.txt` and `collect_all_packages` in `build_installer.py`, guaranteeing that frozen Windows bundles include valid root CA certificate stores for Hugging Face and CDN downloads.

## v3.8.9-beta.4
- **AI Model Download Reliability & UI Responsiveness Hardening (`model_management.py`, `processing.py`, `radio_tv_story_segmenter_worker.py`, `bootstrap.py`, `runtime_manager.py`)**:
  - **Offline Language Probing (`radio_tv_story_segmenter_worker.py`)**: Resolved an issue where starting transcription on a clean install froze at 2% (*"Inspecting audio language compatibility..."*) because `probe_audio_language` was instantiating `WhisperModel("tiny")` without checking if it existed locally, triggering an unprompted, synchronous background download of Whisper Tiny. Added `local_files_only=True` and fallback logic so language detection only probes models already present on disk and immediately defaults to English if uninstalled without blocking execution.
  - **In-Dialog Model Download Progress & Cancellation (`model_management.py`)**: Resolved an issue where clicking "Download / Install" in the Manage Models dialog disabled all buttons without displaying an in-dialog progress bar (making the application appear frozen while the background thread downloaded weights). Added a dedicated progress panel with real-time transfer size/percentage counters and an active "Cancel Download" button directly inside the dialog.
  - **SSL Certificate Verification & Socket Timeout Hardening (`model_management.py`, `bootstrap.py`, `plugins/translation/support.py`)**: Configured `certifi.where()` CA certificate bundles across `_download_http_file`, `bootstrap.py`, and `plugins/translation/support.py` on Windows and Linux to resolve silent SSL certificate verification failures during downloads from Hugging Face and CDN endpoints. Enforced 30-second socket timeouts and 3x retry loops with exponential backoff, preventing infinite socket hangs if a CDN connection drops mid-transfer.
  - **Progress Event Throttling (`model_management.py`)**: Throttled download progress signals to a maximum rate of 10 Hz (every 100–150 ms) during chunked streaming, eliminating Qt cross-thread event queue saturation that previously caused UI micro-freezes during high-speed downloads.
  - **404 Fast-Path Bypass for Optional Vocabulary Files (`model_management.py`)**: When optional files (like `vocabulary.json`) return HTTP 404, the downloader immediately skips to `vocabulary.txt` instead of stalling inside `huggingface_hub` API fallbacks.
  - **Clean Install Download Loop Protection (`processing.py`)**: Configured `progress_box.setAutoReset(False)` and `progress_box.setAutoClose(False)` in `start_transcription` to prevent Qt's progress dialog from spuriously firing cancellation events upon reaching 100% completion.
  - **Frozen Worker Subprocess Invocation (`model_management.py`)**: Fixed `DiarizationModelInstallWorker` to invoke `prs_worker.exe` rather than `sys.executable` (the GUI binary) when packaged under PyInstaller.
  - **Safe URL Retrieval (`runtime_manager.py`)**: Replaced un-timed `urllib.request.urlretrieve` calls in `ensure_uv` and `_download_standalone_python` with `_robust_urlretrieve` enforcing atomic chunked writes, timeout boundaries, and CA verification.

## v3.8.9-beta.3
- **Installed Footprint & Installer Size Optimization (`build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`)**:
  - **Pruned Software OpenGL Rasterizer (`opengl32sw.dll`)**: Stripped Mesa llvmpipe software OpenGL binary (~30 MB) from packaged bundles; standard `QtWidgets` native GDI/DirectWrite rendering and `QtMultimediaWidgets` Direct3D 11 video presentation run natively with zero reliance on software OpenGL.
  - **On-Demand Runtime Tool Provisioning (`uv.exe`)**: Omitted pre-bundled `uv.exe` from the default installer payload (saving ~50 MB on installed disk footprint), relying on `runtime_manager.py`'s existing on-demand download mechanism when users explicitly choose to install optional GPU acceleration or Translation plugin runtimes. Added `--bundle-uv` CLI flag to `build_installer.py` for optional manual pre-bundling.
  - **Inno Setup Ultra Solid Compression**: Upgraded Windows setup installer script from `Compression=lzma2/fast` to `Compression=lzma2/ultra64` with `SolidCompression=yes`, significantly shrinking the downloaded setup executable size.

## v3.8.9-beta.2
- **Supported Media Format Clarifications & UI Tooltip Refinements (`transcript_editor.py`, `benchmark.py`, `ui_layout.py`, `batch_dialog.py`)**:
  - **Drop Card Dynamic Bounding Box & Multi-Line Word Wrap**: Resolved horizontal text clipping on the empty-state media ingestion card by adding `Qt.TextFlag.TextWordWrap` to `QPainter.drawText` overlay routines, expanding maximum card width (from 460px to 520px), and dynamically spacing subtitle and action button bounds. Applied responsive word-wrapping across `batch_dialog.py` empty queues as well.
  - **Comprehensive Format Support Messaging**: Updated the empty-state drag-and-drop card in `transcript_editor.py` to state *"Supports all standard audio & video formats (WAV, MP3, MP4, MOV, MKV, FLAC, etc.)"*, accurately communicating full FFmpeg compatibility without implying an artificial restriction to only 7 containers.
  - **Benchmark Tool Media Picker Normalization**: Expanded the custom file picker filter in `benchmark.py` to `"All Supported Media Files (*.*)"`, ensuring `.mov`, `.webm`, `.aiff`, `.opus`, and other supported media containers are not masked in the operating system browser.
  - **Descriptive Text Document Tooltips**: Added explicit tooltips and status-bar hints to `File > Open Document...` (`open_doc_act`) and `File > Open Media...` (`open_media_act`) in `ui_layout.py`, clarifying that Open Document imports external text documents (`.txt`, `.docx`, `.pdf`, `.html`, `.md`) directly into the transcript workspace.

## v3.8.8-stable
- **Configurable Paragraph Word Count & Natural Sentence Boundary Grouping (`playback_preferences.py`, `transcript_story.py`, `RadioTVSegmenter.py`)**:
  - **User-Configurable Paragraph Length**: Added a dedicated "Paragraph Length" spinbox under Settings > Preferences > General (ranging from 20 to 250 words, default 65 words). Allows users to tailor paragraph density to their broadcast formatting needs, instantly updating open transcripts upon saving preferences.
  - **Sentence Boundary Grouping & Orphan Elimination**: Clarified grouping behavior where speech pauses or target word counts trigger breaks only at sentence terminators (`.`, `?`, `!`), avoiding mid-sentence cuts. Implemented lookahead protection preventing trailing sentence fragments (< 25 words) from being orphaned as single-sentence paragraphs before speaker changes.
  - **Persistent Settings & Defaults Integration**: Integrated the paragraph length setting into the settings store, startup loading routine, and the Category Defaults Reset dialog.
- **Word-Level Highlighting Precision & Timing Invariant Preservation (`transcript_editor.py`, `transcript_story.py`, `test_runner.py`)**:
  - **Live QTextDocument Fragment Highlighting**: Eliminated preceding-word bleed where highlighting a selection unintentionally highlighted preceding words. Directly resolves selection bounding spans against underlying document fragments and canonical `(seg_idx, word_idx)` token coordinates.
  - **Full Millisecond Timestamp Invariant Preservation**: Retained high-precision floating-point timestamps across internal structures, tokens, anchor hrefs, and export formats even when millisecond display is toggled off in the UI.
  - **Targeted Removal Fallback**: Ensured remove-highlight strictly removes highlights from the selected word range rather than stripping document-wide highlights when target resolution encounters edge cases.
- **Transcript Word-Level Highlighting & Natural Sentence Paragraph Grouping Fixes (`transcript_story.py`, `transcript_editor.py`, `transcript_cleaner.py`, `test_runner.py`)**:
  - **Natural Sentence Boundary Grouping**: Fixed an issue where artificial time markers and paragraph breaks were inserted mid-sentence (such as at 0:27 and 0:53) due to speech pauses triggering `time_gap >= 5.0` without checking for sentence endings. Enforced that paragraph breaks within the same speaker turn only occur at natural sentence boundaries (`prev_word_ended_sentence`), preventing dangling sentence fragments from being split into separate paragraphs. Also ensured unassigned or missing speaker tags inherit the active speaker to prevent false speaker-change splits.
  - **Precise Word-Level Highlighting & Preceding Word Bleed Elimination**: Resolved a bug where selecting a specific sentence fragment to highlight mistakenly applied yellow highlighting to several words that came before that section (and following lines). Replaced cumulative string-length character offset estimates with live `QTextDocument` fragment queries and canonical `(seg_idx, word_idx)` token mapping. Now queries actual document fragment coordinates directly, isolating selection bounds so preceding words and trailing words are never highlighted. Also eliminated the blanket fallback in remove-highlighting that previously removed all document highlights if target resolution failed.
  - **Eliminated Transcript Corruption & White Text Artifacts**: Resolved an issue where highlighting text in View mode triggered `on_transcript_text_changed`, which failed to strip timestamps like `0:27` from block text and baked timestamps and speaker labels directly into the segment text as bold white words. Protected highlighting operations with `is_updating_transcript_view`, guarded `on_transcript_text_changed` strictly to active edit mode, updated timestamp stripping regexes to handle single-digit minute formats (`0:27`), and added self-healing sanitization in `scrub_transcript_segments`.
- **Audio Fades Dialog & Context Menu Streamlining (`story_fades_dialog.py`, `story_widgets.py`, `timeline_widgets.py`, `plugins/wordpress/plugin.py`)**:
  - **Direct Enable/Disable Toggle on Audio Fades Screen**: Added a prominent, permanent `Enable audio fades (timeline envelope handles and playback auditioning)` check-box directly onto the Audio Fades dialog window. Toggling it updates timeline envelope handles and playback auditioning in real time, and persists directly to application preferences.
  - **Clean Single-Action Right-Click Context Menus**: Streamlined the right-click menus on both the timeline canvas (`Set Audio Fades...`) and the sidebar story list (`Audio Fades...`) to a single, direct action that opens the Audio Fades configuration dialog, completely eliminating redundant submenus and duplicate preference toggles.
  - **Removed Auto-Excerpt Button from Stories Widget**: Removed the redundant auto-excerpt button from the stories sidebar widget (and cleaned up decorative emoji glyphs), keeping excerpt generation and editing focused within the dedicated Story Metadata editor dialog.
- **System Diagnostic Test Bench Thread-Safety Fix (`test_runner.py`)**:
  - **Eliminated UI Freeze in Diagnostic Test Bench**: Resolved an issue where running the diagnostic test bench inside the desktop application (`Help -> Run Diagnostic Test Bench...`) would freeze the UI. Fixed cross-thread GUI widget instantiations (`BatchProcessingDialog`) executing on secondary worker threads (`QThread`), replacing them with 100% thread-safe interface and logic validations.
  - **Subprocess Spawn & IPC Handshake Hardening**: Added `stdin=subprocess.DEVNULL`, `CREATE_NO_WINDOW` flags on Windows, and strict timeout exception handlers to worker diagnostic subprocess probes, preventing child process hangs.
  - **Clean Worker Thread Lifecycle**: Guarded `start_diagnostics` against concurrent invocation, connected `deleteLater` handlers on worker and thread completion, and ensured clean teardown.
- **Core Architecture Modularization (`transcript_story.py`, `shortcuts_manager.py`, `export/dialog.py`)**:
  - **`shortcuts/` Modular Subsystem**: Decomposed the monolithic 1,795-line `shortcuts_manager.py` into a structured package (`shortcuts/schema.py`, `shortcuts/manager.py`, `shortcuts/widgets.py`, `shortcuts/dialogs.py`). Replaced `shortcuts_manager.py` with a lightweight, 100% backward-compatible re-export facade.
  - **Export Center Dialog Decoupling (`export/reorder_dialog.py`, `export/dialog.py`)**: Extracted `ReorderExportDestinationsDialog` and export destination ordering logic out of `export/dialog.py` into a dedicated `export/reorder_dialog.py` module.
  - **Transcript Story Dialog Extraction (`voice_profile_dialog.py`, `speaker_dialogs.py`, `story_fades_dialog.py`, `transcript_story.py`)**: Extracted ~1,380 lines of modal dialog implementations (`VoiceProfileMatchDialog`, `SpeakerManagerDialog`, `ChangeSpeakerDialog`, and `StoryFadesDialog`) into dedicated standalone files with complete `__all__` re-exports in `transcript_story.py`, reducing `transcript_story.py` from 4,284 lines to 2,915 lines.
  - **Installer Packaging Bundles (`build_installer.py`)**: Added hidden import declarations for all newly extracted submodules and packages to guarantee frozen executable stability on Windows, macOS, and Linux.
  - **Zero Regressions & Invariant Preservation**: All existing interfaces, method signatures, test paths, and plugin bindings continue operating without modification.

## v3.8.7-stable
- **Automated Version-Bumping Engine (`bump_version.py`)**:
  - **Single-Command Synchronization Engine**: Implemented `bump_version.py` automating the synchronous 10-location release checklist across core Python modules (`prs_shared.py`, `updater.py`, `build_installer.py`), Inno Setup installer script (`RadioTVStorySegmenter.iss`), `transcript_story.py`, plugin manifests (`plugins/*/manifest.json`), and web preview scaffolding (`package.json`, `metadata.json`, `index.html`, `src/App.tsx`).
  - **Comprehensive CLI Capabilities**: Added support for explicit target versions, semantic increments (`--patch`, `--minor`, `--major`), status verification (`--check`), simulation (`--dry-run`), and selective plugin bumping (`--plugins`).
  - **Token & Context Optimization**: Drastically cuts development token usage by eliminating repetitive multi-file manual reads and diffs during point releases.
- **Ephemeral Scripts Cleanup & Archival Architecture (`AGENTS.md`, `GEMINI.md`, `.gitignore`, `.archive/`)**:
  - **Ephemeral Artifact Cleanup**: Safely purged 7 obsolete throwaway debug scripts (`test_output.py`, `update_changelog.py`, `update_roadmap.py`) and visual mockup generators (`build_bars_comparison.py`, `build_titlebar_mockups.py`, `generate_user_screenshot_mockup.py`, `generate_corrected_visual_mockup.py`), along with 22 temporary mockup images (~1.5 MB) in `resources/`. Permanent application assets (`icon.ico`, `icon.png`, `icon.svg`) remain completely intact.
  - **Project Rule Directive (Section 8)**: Codified the Ephemeral Scripts & Artifact Lifecycle Directive in `AGENTS.md` and `GEMINI.md`, requiring agents to ask users upon task completion whether to delete or archive one-off tools.
  - **Git-Ignored Archive Repository (`.archive/`)**: Configured `.archive/` in `.gitignore` to store archived tools for agent and engineer reference without polluting git status, active search results, or frozen installers.
- **Development Roadmap Realignment (`roadmap.txt`)**:
  - **Top Priority Modularization**: Elevated Clean Modularization of Core Monoliths (`RadioTVSegmenter.py`, `transcript_story.py`, `processing.py`, `export/dialog.py`) with 100% backward-compatible `__all__` re-exports to the top upcoming development milestone (Section 3) in `roadmap.txt`.

## v3.8.6-stable
- **Universal Window & Dialog Title Bar Synchronization with Option 4 Steel Slate (`core_utils.py`, `playback_preferences.py`)**:
  - **Identical Title Bar Palette Across All Windows**: Enforced Option 4 Medium Steel Slate (`#3c4450`) with crisp white text (`#f8fafc`) and subtle frame border (`#4e5765`) across BOTH the main application window AND all pop-up/modal windows (Export Center, Preferences, Story Metadata Editor, Voice Profile Matcher, Keyboard Shortcuts, Batch Processing, ID3 Editor, Model Management).
  - **Global Window Activation & Show Interception (`playback_preferences.py`, `core_utils.py`)**: Enhanced global `eventFilter` to intercept `QEvent.Type.Show`, `ShowToParent`, `WindowActivate`, and `Polish` events across all `topLevelWidgets()`, executing both immediate and deferred Windows DWM attribute application (`_apply_dwm_titlebar_hwnd`) so newly spawned dialogs never revert to white/unstyled caption chrome.
- **Complete Light Mode Visual Consistency across Dialogs & Export Center (`prs_shared.py`, `export/dialog.py`, `story_metadata_dialog.py`, `shortcuts_manager.py`, `transcript_story.py`, `plugins/wordpress/export_destination.py`, `plugins/youtube/export_destination.py`)**:
  - **Light Theme Normalization for `CollapsibleSection` (`prs_shared.py`)**: Refactored `CollapsibleSection` to dynamically query active theme mode. In Light Mode (Option C), section header strips render in clean silver fog (`#e3e6ea`, hover `#d0d4d9`, border `#b6bcc4`) with dark ink text (`#22262c`), and section body containers use soft light-fog surfaces (`#eaedf0`) instead of hardcoded dark navy (`#1e293b` / `rgba(15, 23, 42, 0.35)`).
  - **Export Center Light Mode Alignment (`export/dialog.py`)**: Synchronized header labels, "Collapse All" button, maximize button, format checkboxes, destination radio buttons, unselected audio combo box, ID3 tag button, and reorder destination list items to use light mode token palettes matching Preferences, Batch Processing, and Multi-Stage Processing.
  - **Story Metadata & Post Editor (`story_metadata_dialog.py`)**: Replaced hardcoded dark background and border styles with theme-aware styling for taxonomy refresh, auto-excerpt generation, and video thumbnail preview cards.
  - **Keyboard Shortcuts & Voice Profile Matcher (`shortcuts_manager.py`, `transcript_story.py`)**: Normalized shortcut recording inputs, lookup result cards, table rows, and acoustic re-clustering dialogs to respect the active Light Mode palette.
- **Visual Inspection Mockups (`generate_corrected_visual_mockup.py`, `resources/light_mode_consistency_comparison.png`)**:
  - Generated high-resolution side-by-side comparison board verifying exact visual harmony between the Main Window and the Export Dialog in Light Mode Option 4.

## v3.8.5-stable
- **Darker Title Bar Option 4 (Medium Steel Slate) for Light Mode (`core_utils.py`, `RadioTVSegmenter.py`, `playback_preferences.py`, `theme_tokens.py`, `test_runner.py`)**:
  - **Option 4 Medium Steel Slate Title Bars (`#3c4450`)**: Configured native Windows DWM window title bars and modal dialog title bars to render in a refined, medium-dark steel slate tone (`#3c4450`) with crisp white title text (`#f8fafc`) and subtle frame border (`#4e5765`) when running in Light Mode (Option C).
  - **Eliminated Glaring Bright Window Frames**: Solved the default stark-white OS caption bar glare in Light Mode across both the main application window and modal dialogs (such as Preferences, Story Metadata, Export Center, Manage Models, Batch Processing, and Audio Fades).
  - **Dynamic DWM Window Chrome Synchronization (`core_utils.py`, `playback_preferences.py`)**:
    - Implemented `apply_window_titlebar_theme(widget, theme_mode)` in `core_utils.py` leveraging Windows DWM APIs (`DWMWA_USE_IMMERSIVE_DARK_MODE`, `DWMWA_CAPTION_COLOR`, `DWMWA_TEXT_COLOR`, and `DWMWA_BORDER_COLOR`).
    - Integrated with `make_dialog_maximizable(dialog)` so newly opened dialogs automatically inherit dark title bar attributes.
    - Updated `set_theme` in `playback_preferences.py` to synchronously refresh title bar caption attributes across all open `QApplication.topLevelWidgets()` immediately upon theme switching without requiring application restart.
  - **Theme Drawing Token Integration (`theme_tokens.py`)**: Added `titlebar_bg` (`#3c4450`), `titlebar_text` (`#f8fafc`), and `titlebar_border` (`#4e5765`) to `ThemeTokens` and `_LIGHT_TOKEN_OVERRIDES`.
  - **Automated Diagnostic Test Suite (`test_runner.py`)**: Updated `_test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting` validating Option 4 title bar color tokens and theme synchronization.

## v3.8.4-stable
- **Light Mode Option C: Muted Low-Contrast Silver & Fog Palette (`playback_preferences.py`, `theme_tokens.py`, `transcript_editor.py`, `transcript_story.py`)**:
  - **Eliminated Eye-Straining Stark Whites**: Replaced blinding bright surfaces with a balanced, modern low-contrast silver/fog theme designed specifically to eliminate glare during prolonged editing sessions.
  - **Balanced Cool Surfaces**: Implemented smooth light-fog window backgrounds (`#dcdfe3`), soft slate-fog container surfaces (`#e3e6ea`), card panels (`#d6dae0`), and muted silver-slate borders (`#b6bcc4`).
  - **Matte Transcript & Editor Viewport**: Configured transcript text edits, tables, lists, and dialog inputs to use a matte light-fog background (`#eaedf0`) with deep graphite ink typography (`#22262c`) providing optimal readability without harsh contrast spikes.
  - **Subdued Accents & Speaker Identity**: Employed refined broadcast cornflower/slate blue (`#2e74b5`) for interactive controls, focus rings, sliders, and progress bars; deep slate blue (`#205493`) for speaker labels; muted slate gray (`#545b66`) for timestamps and rulers; and soft cornflower highlight (`#b8d1ea` with `#132c44` text) for selections.
  - **Theme Drawing Token Synchronization**: Updated `_LIGHT_TOKEN_OVERRIDES` in `theme_tokens.py` to synchronize waveform fills (`#4178a8`), waveform stroke (`#6b7e94`), playhead (`#b91c1c`), speaker tags (`#d0d4d9`), status banners (`#e3e6ea`), and story track overlays.
- **Dark-Mode Clipboard Plain Text Color Normalization with Rich Formatting Preservation (`transcript_editor.py`, `test_runner.py`)**:
  - **Plain Text Color Conversion (`clean_dark_mode_clipboard_html`)**: When copying transcript selections in dark mode (or high contrast), plain text words (rendered on screen in white `#ffffff` or `#f0f3f6`) are normalized to `#000000` (black) in the HTML clipboard payload.
  - **External Document Fidelity**: Pasting into Word, Google Docs, Apple Notes, or email renders clean, readable black text without invisible white-on-white text against white pages.
  - **Strict Rich Formatting Preservation**: Plain text color normalization strictly targets unformatted/plain word spans while preserving all other rich formatting:
    - Speaker labels remain in distinct blue (`#58a6ff` in dark mode, `#205493` in light mode).
    - Comment and search highlights strictly retain their background colors (`#fef08a`) and dark text styling (`#0f172a`).
    - Timestamps remain in distinct muted gray (`#8b949e`).
    - Bold (`font-weight:700`), italic (`font-style:italic`), underline, and strikethrough styling are completely preserved.
  - **Regex Lookbehind Safety**: Utilized negative lookbehind `(?<![-a-zA-Z])color\s*:` to ensure `background-color:` attributes are never modified.
- **Automated Diagnostic Suite Integration (`test_runner.py`)**:
  - Added `_test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting` validating Option C light tokens, transcript stylesheet generation, plain-text white-to-black normalization, and rich formatting preservation across speaker labels, highlights, and timestamps.

## v3.8.3-stable
- **Light Mode Option B: Warm Newsprint & Reading Tone Palette (`playback_preferences.py`, `theme_tokens.py`, `transcript_editor.py`, `transcript_story.py`)**:
  - **Eliminated Harsh Glare & Blinding White Surfaces**: Replaced stark white backgrounds (`#faf8f5`, `#fcfbfa`) across transcripts, text editors, list widgets, tables, inputs, and buttons with a soothing, low-glare warm paper tone (`#f2eee5`).
  - **Gentle Surface Harmonies**: Replaced glaring window surfaces (`#f4f1ea`) with gentle warm linen/parchment (`#ede8df`), card containers with `#ded7ca`, and subtle borders with `#c8c0ae`.
  - **Subdued Accent & Typography**: Replaced harsh electric blue (`#2563eb`) with refined broadcast slate-blue (`#316498`), deep sapphire blue (`#245892`) for speaker labels, and warm deep charcoal ink (`#2b2723`) for primary text.
  - **Comfortable Reading Selection**: Replaced high-glare cyan selections with soft reading pastel blue (`#c8ddf5` with `#1b3b5e` text).
  - **Synchronized Drawing Tokens**: Updated `_LIGHT_TOKEN_OVERRIDES` in `theme_tokens.py` to keep waveform envelopes (`#3b75af`), playhead (`#c53030`), rulers, and overlays in lockstep with Qt stylesheet rendering.
- **Dark-Mode Clipboard Plain Text Color Normalization (`transcript_editor.py`, `test_runner.py`)**:
  - **Intelligent Rich Text Clipboard Export (`clean_dark_mode_clipboard_html`)**: When copying transcript selections in dark mode (or high contrast), plain text words (rendered on screen in white `#ffffff` or `#f0f3f6`) are normalized to `#000000` (black) in the HTML clipboard payload.
  - **External Document Fidelity**: Pasting copied transcripts into Microsoft Word, Google Docs, Apple Notes, LibreOffice, or email clients now renders clean, readable black text instead of invisible white-on-white text against light document pages.
  - **Strict Rich Formatting Preservation**: Plain text color conversion strictly targets unformatted/plain word spans while preserving all rich formatting:
    - Speaker labels remain in distinct blue (`#58a6ff` in dark mode, `#245892` in light mode).
    - Comment and search highlights strictly retain their background colors (`#fef08a`) and dark text styling (`#0f172a`).
    - Timestamps remain in distinct muted gray (`#8b949e`).
    - Bold (`font-weight:700`), italic (`font-style:italic`), underline, and strikethrough styling are completely preserved.
  - **Regex Lookbehind Safety**: Utilized negative lookbehind `(?<![-a-zA-Z])color\s*:` to ensure `background-color:` attributes are never modified.
- **Automated Diagnostic Test (`test_runner.py`)**:
  - Added `_test_option_b_warm_paper_light_theme_and_dark_mode_clipboard_formatting` validating Option B light tokens, transcript stylesheet generation, white-to-black normalization, and rich formatting preservation across speaker labels, highlights, and timestamps.

## v3.8.1-stable
- **Backup & Restore Center Bug Fix (`backup_manager.py`)**:
  - Fixed a blocking `ValueError: not enough values to unpack (expected 3, got 2)` during local settings restoration. `apply_backup_payload` returns a 2-tuple `(success, items)` while the caller unpacked 3 variables, throwing an error message modal on every restore attempt.
  - Enhanced `apply_backup_payload` live state update to refresh all runtime attributes (`silence_threshold`, `lead_in_padding`, `story_detection_mode`, `enable_audio_fades`, `preview_audio_fades`, `skip_seconds`) and canvas visual indicators immediately in-memory without requiring application restart.
  - Added direct **"Restore System Defaults…"** button inside the Backup & Restore Center dialog (Local Archive tab) allowing instant factory reset from the backup center.
- **Universal System Defaults Restoration & Persistent In-Memory Synchronization (`RadioTVSegmenter.py`, `playback_preferences.py`, `transcript_story.py`, `ui_layout.py`)**:
  - **Comprehensive 15-Category Reset Engine (`playback_preferences.py`)**:
    - Re-engineered `apply_settings_reset` to ensure 100% comprehensive defaults restoration across all 15 categories (General Appearance, Project Dirs & Bundling, Autosave, Keyboard Shortcuts, Audio Hardware, Updates & GitHub, AI Models, GPU Acceleration, Playback & Timeline, Audio Fades, Story Detection & Diarization, Batch Processing, Export Options, Export Custom Location, and WordPress Settings).
    - Included all previously omitted settings: `single_instance_mode`, `show_floating_selection_toolbar`, `open_comments_on_launch`, `show_comment_highlights`, `show_timestamps`, `show_milliseconds`, `auto_detect_fallback_whisper`, `gpu_acceleration_enabled`, and individual GPU workflow switches.
    - Updated all live form widgets (`single_instance_combo`, `floating_toolbar_chk`, `open_comments_chk`, `show_highlights_chk`, `show_timestamps_chk`, `show_millis_chk`, `pref_auto_lang_chk`, `global_gpu_chk`, `gpu_trans_chk`, `gpu_translate_chk`, `gpu_diarize_chk`, `theme_combo`, `startup_combo`, `proj_dir_edit`, `autosave_spin`, `audio_dev_combo`, `vol_slider`, `auto_update_chk`, `repo_edit`, `pref_whisper_combo`, `pref_beam_combo`, `pref_trans_combo`, `skip_spin`, `wave_chk`, `thumb_chk`, `thumb_pos_combo`, `sel_mode_combo`, `enable_fades_chk`, `preview_fades_chk`, `fade_in_spin`, `fade_out_spin`, `fade_curve_combo`, `det_mode_combo`, `gap_spin`, `pad_spin`, `expected_speakers_combo`, `sensitivity_combo`, `ask_speakers_chk`, and all batch widgets) synchronously.
  - **Startup & Post-Reset Attribute Lifecycle (`RadioTVSegmenter.py`)**:
    - Implemented `load_persistent_settings()` on `MainWindow` to load all persistent preferences from `QSettings` into memory at startup, and re-read them after any settings reset or restore operation.
  - **"Clear All User Preferences" Deep Factory Reset (`playback_preferences.py`)**:
    - Fixed the "Clear All User Preferences (Reset Settings to Defaults)…" action in the Cleanup Data preferences page so it properly resets all in-memory attributes on `MainWindow` and all live form widgets before flushing disk storage.
  - **Top-Level Settings Menu Integration (`ui_layout.py`)**:
    - Added **"Restore System Defaults..."** directly to the top-level **Settings** menu bar, opening the category selection dialog with 1 click.
  - **Per-Page "Restore Category Defaults" Across All Preferences Tabs**:
    - Added inline "Restore Category Defaults" buttons to all Preferences pages (General, Audio Hardware, Updates & GitHub, AI Models, GPU Acceleration, Playback & Timeline, Detection, and Batch Processing).
  - **Dedicated Dialog Resets**:
    - Added "Restore Defaults" button in "Story Detection Settings" dialog (`prompt_set_auto_detect_thresholds`) and updated Story Fades dialog (`transcript_story.py`) `_restore_defaults` to restore initial factory system defaults (0.0s in, 1.0s out, linear curve).
- **Settings Menu Cleanliness (`ui_layout.py`)**:
  - Removed "Show Timestamps" and "Show Milliseconds in Timestamps" from the top-level **Settings** menu bar, strictly retaining their canonical locations in **View > Transcript**, **Preferences > General**, and **Export > Content Options**.

## v3.8.0-stable
- **Comprehensive Cloud & Local Backup & Restore System (`backup_manager.py`, `project_lifecycle.py`, `ui_layout.py`)**:
  - **Milestone 3.1: Unified State Serialization & Cryptographic Verification**:
    - Centralized serialization engine packaging application preferences (`QSettings`), custom keyboard shortcut reassignments (`shortcuts_manager.py`), glossary / terminology entries (`terminology.py`), installed AI model metadata (`runtime_manager.py`), and plugin toggle states into a portable settings archive (`.rtvs-settings` and `.rtvs-preferences` JSON format).
    - Cryptographic verification via deterministic SHA-256 checksums calculated over canonical serialized state to guarantee zero tampering or bit-rot.
  - **Milestone 3.2: Manual Local Backup & Restore Center**:
    - Dedicated modal dialog with `make_dialog_maximizable` support accessible via **File > Backup & Restore...** (`Ctrl+Shift+U`) and **Settings > Backup & Restore Settings...**.
    - Local Archive Tab featuring live state summaries, "Create Local Settings File (.rtvs-settings)..." file export, and "Restore from Settings File..." with pre-flight inspection and confirmation prompts.
    - Live reload of preferences, keyboard shortcuts, terminology dictionaries, and transcript views upon restoration without requiring an application restart.
    - Clean native desktop UI discipline: eliminated all unrequested emoji icons (e.g. folder, cloud, checkmarks) in favor of standard, professional desktop styling.
  - **Milestone 3.3: 1-Click Google Drive Cloud Backup & Restore**:
    - Integrated with existing Google Drive OAuth (`drive.file` scope) from `plugins/gdocs`.
    - Direct cloud backup uploads via Google Drive API multipart protocol (`rtvs_settings_*.rtvs-settings`), cloud backup enumeration, and 1-click cloud restoration with SHA-256 verification.
- **Persistent View Menu (`ui_layout.py`)**:
  - Implemented `PersistentMenu` (`QMenu` subclass): toggling any checkable options in the **View** menu (e.g. Timeline Panel, Transcript Panel, Stories Panel, Activity History, Comments Sidebar, Comment Highlights) or submenus (Timeline, Transcript) no longer abruptly closes the menu.
  - The menu stays open allowing users to quickly toggle multiple options in a single pass until clicking elsewhere on the screen or pressing `Esc`. Actions execute immediately upon each click.
- **Tri-Location Clean Transcript Milliseconds Display Toggle**:
  - Configurable toggle controlling whether timestamps display sub-second millisecond precision (`MM:SS.mmm`) or clean human-readable formatting (`MM:SS` / `HH:MM:SS`), accessible across all three primary workflow locations:
    1. **View Menu**: Under **View > Transcript > Show Milliseconds in Timestamps**.
    2. **Export Window**: Under **Export > Content & Language Options > Show Milliseconds in Timestamps** (TXT, DOCX, and PDF text exports honor this preference).
    3. **Preferences Dialog**: Inside **Settings > Preferences > General > Timecode Precision**.
  - All three locations remain bidirectionally synchronized in real time.
  - Subtitle exports (SRT, VTT) and DAW sessions (REAPER, EDL) strictly preserve millisecond and frame precision regardless of this setting.
- **UI Design Discipline Enforced (`AGENTS.md`, `GEMINI.md`)**:
  - Enforced strict prohibition on adding unrequested icons or emoji symbols (folders, clouds, disks, checkmarks, warning signs) to tabs, buttons, dialog titles, menus, or cards.
- **Automated Diagnostic Test (`test_runner.py`)**:
  - Added `_test_comprehensive_local_and_cloud_backup_and_restore_engine` to the test suite, validating state serialization, SHA-256 cryptographic verification, tamper detection, `.rtvs-settings` local archive roundtrip, and cloud payload integrity.
  - Added `backup_manager.py` to `_test_modal_dialog_maximizable_import_integrity` verification audit.
- **Plugin Catch-Up Synchronization**:
  - Synchronized versions across `plugins/gdocs`, `plugins/wordpress`, and `plugins/youtube` to `v3.8.0-stable`.

---


## v3.7.22-stable
- **Diagnostic Test Bench Frozen PyInstaller Binary Hardening (`test_runner.py`)**:
  - **Resolved `AssertionError: batch_dialog.py file not found`**: Fixed test harness in `_test_batch_unified_transcripts_directory_export`. When running from compiled PyInstaller frozen executables (`RadioTVSegmenter.exe`), python source `.py` files are bundled into bytecode archives rather than loose files on disk. The test now conditionally runs AST verification when `batch_dialog.py` is present on disk, and seamlessly falls back to module reflection and runtime widget validation in compiled frozen binary environments.
  - **Resolved `AssertionError: export/dialog.py missing`**: Updated `_test_unified_export_destinations_and_youtube_auth_integrity` to make `export/dialog.py` and `plugins/wordpress/plugin.py` file checks frozen-aware, using live module reflection when executed from packaged PyInstaller binaries.
  - **Clean Status Messaging**: Refined `_test_modal_dialog_maximizable_import_integrity` to report `"(compiled frozen binary mode)"` when executed in frozen environments rather than reporting zero modules.
- **Plugin Catch-Up Synchronization**:
  - Synchronized `manifest.json` versions for modified plugins: `plugins/youtube` (`v3.7.22-stable`), `plugins/wordpress` (`v3.7.22-stable`), and `plugins/gdocs` (`v3.7.22-stable`).

## v3.7.21-stable
- **Diagnostic Test Bench Hardening & Attribute Lifecycle Resolution (`test_runner.py`, `plugins/base.py`)**:
  - **Resolved `AttributeError: 'DummyMainWindow' object has no attribute 'transcript_for_range'`**: Fixed an attribute deletion error in `_test_wordpress_export_content_and_transcript_formatter`. In Python, attempting `del win.transcript_for_range` on an instance when the method is defined on the class raises an `AttributeError`. Replaced direct instance deletion with safe class-level `delattr` and fallback assignment (`win.transcript_for_range = None`), ensuring test execution proceeds smoothly on all environments with PySide6 installed.
  - **Resolved `TypeError: PluginManifest.__init__() got an unexpected keyword argument 'enabled'`**: Added canonical `enabled: bool = False` dataclass field and parsing support to `PluginManifest` in `plugins/base.py`. Updated the WordPress plugin test manifest instantiation in `_test_unified_export_destinations_and_youtube_auth_integrity` (`test_runner.py`) to supply both `enabled_by_default` and `enabled` keyword arguments aligned with `PROJECT_VERSION`.
- **Media Extension & Title Path Resolution Hardening (`export/dialog.py`, `plugins/youtube/export_destination.py`)**:
  - **Safe String & Path Type Coercion**: Wrapped `audio_file` and `project_file` references in `Path(...)` within `UnifiedExportDialog` (`export/dialog.py`) and `YouTubeExportWidget` (`plugins/youtube/export_destination.py`), preventing unexpected `AttributeError: 'str' object has no attribute 'suffix'` / `'stem'` when media paths are supplied as strings.
  - **Destination Page Initialization Guard**: Enforced `page is not None` checks during export destination discovery before attaching destination pages to the dialog stacked widget.
- **Plugin Catch-Up Synchronization**:
  - Synchronized `manifest.json` versions for modified plugins: `plugins/youtube` (`v3.7.21-stable`), `plugins/wordpress` (`v3.7.21-stable`), and `plugins/gdocs` (`v3.7.21-stable`).

## v3.7.20-stable
- **Diagnostic Test Bench Hardening & Resilient Test Harness (`test_runner.py`, `plugins/wordpress/client.py`)**:
  - **Resolved `AssertionError: Unauthenticated email should return empty string`**: Fixed test assumption in `_test_unified_export_destinations_and_youtube_auth_integrity` where creating `YouTubeAuthManager` and `GoogleDocsAuthManager` on user machines with pre-existing authenticated credentials (such as linked Google / YouTube accounts) returned the user's actual email address instead of empty strings. The test now deterministically validates both unauthenticated and authenticated branches using isolated test instances, while safely checking consistency (`get_authenticated_email() == get_user_email()`) on existing manager instances without clearing user credentials.
  - **Resolved `RuntimeError: FFmpeg audio preparation failed` in WordPress Formatter Test**: Fixed `_test_wordpress_export_content_and_transcript_formatter` where `dummy_audio_path` previously wrote non-audio dummy bytes (`b"ID3" + b"\x00" * 200`). When executed on machines with FFmpeg installed (such as Windows with FFmpeg 7.1), FFmpeg failed to parse the invalid audio during the story slice conversion step. Updated the test harness to generate a valid 16kHz 16-bit PCM WAV audio file using Python's standard `wave` module, and added a safe fallback wrapper around `subprocess.run` to guarantee bulletproof execution across all developer machines and CI environments.
  - **Compact FFmpeg Error Diagnostics (`plugins/wordpress/client.py`)**: Improved error reporting in `execute_wordpress_upload` so that if FFmpeg encounters corrupt media during audio preparation, the exception message reports the trailing error lines rather than the long FFmpeg compilation banner.

## v3.7.19-stable
- **Unified Export Center & Destination Integrity Fix (`plugins/youtube/api.py`, `plugins/youtube/export_destination.py`, `plugins/gdocs/auth.py`, `export/dialog.py`, `test_runner.py`)**:
  - **Resolved `AttributeError: 'YouTubeAuthManager' object has no attribute 'get_authenticated_email'`**: Fixed a blocking runtime exception that prevented opening the Unified Export Dialog (`File > Export...` or clicking `Export...` from the stories sidebar). `YouTubeExportWidget` invoked `self.auth_manager.get_authenticated_email()`, while `GoogleDocsAuthManager` originally defined `get_user_email()`.
  - **Cross-Plugin Authentication Aliasing & Resilient Status Queries**: Added canonical `get_authenticated_email()` and `get_user_email()` methods across both `YouTubeAuthManager` and `GoogleDocsAuthManager`. Hardened `_update_auth_status_ui` with fallback resolution and safe exception handling.
  - **Isolated Export Destination Exception Guards**: Wrapped individual export destination widget creation in `export/dialog.py` (`UnifiedExportDialog._build_destinations_layout`) with comprehensive `try...except` blocks. If any third-party destination encounters an unexpected error during widget creation, it is gracefully logged while ensuring Local Files, YouTube, Google Docs, and WordPress options remain fully accessible.
- **Stories Panel Clean Separation & WordPress Post Configuration Isolation (`plugins/wordpress/plugin.py`, `ui_layout.py`)**:
  - **Removed WordPress Post Configuration from Stories Sidebar**: Streamlined the right-hand stories panel by eliminating the embedded `WordPress Post Configuration` group box and button. Per workflow requirements, WordPress post settings and metadata are now strictly accessed from:
    1. **Unified Export Center** (`File > Export...` > WordPress destination tab)
    2. **Preferences** (`Settings > Preferences > WordPress`)
    3. **Dedicated Post Dialog** (`Tools > WordPress Post & Story Settings...` or right-click story menu)
  - **Dynamic Sidebar Container Visibility**: Updated `ui_layout.py` to keep `plugin_story_extensions_container` hidden by default and dynamically toggle visibility only when active plugin story extensions are explicitly provided, restoring a clean, uncluttered layout for story creation and editing.
- **Plugin Catch-Up Synchronization**:
  - Synchronized `manifest.json` versions for modified plugins: `plugins/youtube` (`v3.7.19-stable`), `plugins/wordpress` (`v3.7.19-stable`), and `plugins/gdocs` (`v3.7.19-stable`).
- **PDF Export Bold Speaker Labels & Adaptive Flow (`export/pdf.py`, `test_runner.py`)**:
  - **Resolved Non-Bold Speaker Labels in PDF Exports**: Previously, `TranscriptPdfWriter.add_paragraph` formatted the entire line (timestamp, speaker label, and body text) as a single monolithic string using the standard `/F1` font (`Helvetica` regular) with a single `BT /F1 ... Tj ET` PDF text operator.
  - **Inline Font Switching to Helvetica-Bold (`/F2`)**: Enhanced the vector PDF engine to render speaker labels in Helvetica-Bold (`/F2 10.0 Tf`) and timestamps in subtle gray (`/F1 9.5 Tf 0.45 0.5 0.55 rg`), cleanly followed by regular paragraph body text (`/F1 10.0 Tf`).
  - **Adaptive Multiline Word Wrapping**: Implemented `_wrap_paragraph_text` which calculates line-0 prefix width occupied by timestamps and bold speaker labels, wrapping remaining words on line 0 while allowing subsequent lines to occupy the full printable page width.
- **Automated Diagnostic Tests (`test_runner.py`)**:
  - `_test_unified_export_destinations_and_youtube_auth_integrity`: Validates YouTube and Google Docs auth email methods, WordPress story panel exclusion, and export dialog exception guards.
  - `_test_pdf_transcript_export_and_bold_speaker_labels`: Validates lightweight vector PDF transcript generator, bold speaker labels (`/F2`), timestamps, comments, highlights, and multiline wrapping.
- **Batch Processing Drag-and-Drop Ingestion & Dialog-Wide Event Filtering (`batch_dialog.py`, `core_utils.py`, `test_runner.py`)**:
  - **Full Drag-and-Drop Ingestion in Batch Processing Dialog**: Added comprehensive drag-and-drop support to the Batch Processing Center (`BatchProcessingDialog` / `Ctrl+Shift+B`), allowing users to drag and drop single files, multiple media files, documents, or entire directory trees directly into the batch tool.
  - **Dynamic Visual Drop Indicators & Empty-State Guide**: Implemented rich visual feedback with antialiased dashed accent boundaries and clear text prompts in `BatchFileListWidget` that adaptively highlight drop zones when dragging files over either empty or already-populated queue lists.
  - **Recursive Directory Ingestion & Automatic Deduplication**: Enabled seamless folder dropping that recursively traverses nested directories (`p.rglob("*")`) to extract all contained media and document assets while preventing duplicate file entries in the processing queue.
  - **Dialog-Wide Drag Event Delegation**: Installed recursive drag-and-drop event filters across all child widgets, group boxes, labels, and action rows in `BatchProcessingDialog`, ensuring file drops anywhere across the window interface are reliably captured and appended to the queue.
  - **Cross-Platform MIME & URI Normalization**: Enhanced `extract_dropped_file_paths` in `core_utils.py` to robustly decode `QUrl` local files, `file://` and `localhost` URIs, percent-encoded path spaces, Windows drive letter prefixes (`/C:/`), and quoted text line drops.
  - **Automated Diagnostic Test (`test_runner.py`)**: Added `_test_batch_drag_and_drop_ingestion_and_event_handling` to the diagnostic test bench, verifying multi-schema MIME data extraction, recursive folder ingestion, deduplication, and dialog event filter dispatch.
- **Batch Processing Unified Transcripts Directory Option (`batch_dialog.py`, `media_batch.py`, `project_export.py`, `test_runner.py`)**:
  - **Single Transcripts Directory Mode**: Added a dedicated `[x] Save all transcripts to a single directory` option in the Batch Processing Center (`BatchProcessingDialog`). When enabled, transcripts, documents, and subtitle files (`.txt`, `.docx`, `.srt`, `.vtt`) for all processed files are exported directly into a single consolidated folder (defaulting to `<Target Location>/Transcripts/` or any user-selected custom directory) rather than isolated per-file subdirectories.
  - **Preserved Project Session Organization**: Kept non-destructive `.rtvs` project sessions organized in `<Target Location>/Projects/<base_name>.rtvs`, allowing users to quickly collect all output documents while preserving session markers, speaker diarization, waveforms, and timestamped editing data.
  - **Dedicated Transcripts Directory Picker**: Added a companion folder input and "Browse Transcripts Folder…" selector, allowing users to direct batch transcripts to cloud storage, shared network locations, or custom local folders with automatic fallback to `<Target Location>/Transcripts`.
  - **Enhanced Skip-Existing Verification**: Upgraded batch skip-existing check to detect whether outputs exist directly in the unified transcripts folder, preventing redundant AI pipeline runs when documents are already present.
  - **Custom Location Propagation in Story Exports**: Updated `perform_stories_export` in `project_export.py` to accept and forward `is_custom_location=True`, ensuring story exports write cleanly to the target transcripts folder without creating redundant nested subfolders.
  - **Automated Diagnostic Test (`test_runner.py`)**: Added `_test_batch_unified_transcripts_directory_export` verifying AST configuration, Qt widget states, settings persistence, project session isolation, transcript routing, and skip-existing checks.

## v3.7.15-stable
- **Modal Dialog Maximizable Import Fix (`batch_dialog.py`, `export/dialog.py`, `id3_editor.py`, `story_metadata_dialog.py`, `project_lifecycle.py`, `playback_preferences.py`, `transcript_story.py`, `test_runner.py`)**:
  - **Resolved `NameError: name 'make_dialog_maximizable' is not defined`**: Fixed a runtime exception when opening the Batch Processing Center dialog (`open_batch_processing_dialog` / `Ctrl+Shift+B`), where `BatchProcessingDialog.__init__` invoked `make_dialog_maximizable(self)` without importing the helper from `core_utils`.
  - **Comprehensive Dialog Audit & Import Normalization**: Audited all modal and tool dialogs (`BatchProcessingDialog`, `UnifiedExportDialog`, `ID3TagEditorDialog`, `StoryMetadataDialog`, `ProjectDataPurgeDialog`, `RestoreSelectedSettingsDialog`, and transcript story dialogs) to ensure `make_dialog_maximizable` is explicitly imported and bound.
  - **Automated AST Diagnostic Integrity Test (`test_runner.py`)**: Added `_test_modal_dialog_maximizable_import_integrity` to the diagnostic test bench, performing static AST syntax tree verification across all dialog modules to guarantee no dialog invokes `make_dialog_maximizable` without a matching import.

## v3.7.14-stable
- **WordPress Direct REST API Export Fix (`plugins/wordpress/client.py`, `plugins/wordpress/plugin.py`, `plugins/wordpress/manifest.json`, `test_runner.py`)**:
  - **Resolved `'str' object has no attribute 'get'` WordPress Export Failure**: Fixed a critical bug where exporting a post to WordPress failed with `Errors: Filename: 'str' object has no attribute 'get'`. In RTVS, the application transcript is structured as a dictionary containing metadata and the `segments` list (`{"text": ..., "segments": [...]}`). In `execute_wordpress_upload`, iterating directly over `main_window.transcript` yielded dictionary keys as strings (`'text'`, `'segments'`), causing segment attribute lookups (`seg.get("start")`) to fail with an `AttributeError`.
  - **Resilient Multi-Format Transcript Slicing**: Updated transcript parsing to cleanly support dictionary structures (`raw_transcript.get("segments")`), raw segment lists, and plain text fallbacks (`_get_transcript_text_slice`), utilizing `main_window.transcript_for_range` for accurate story clipping.
  - **Robust Media GUID & URL Resolution**: Guarded WordPress media upload responses so that media `guid` values returned as either raw string URLs or nested objects (`{"rendered": "..."}`) are safely unwrapped without raising attribute errors.
  - **Integrated Spanish Translation Mapping**: Properly mapped project-level translation segments (`get_spanish_translation_item()` / `translations["en-es"]`) to source segments via `_source_index`, ensuring bilingual accordion and dual-language post presentations format accurately.
  - **Acoustic Speaker Name Propagation**: Integrated `get_effective_speaker_name` and `speaker_for_segment` into WordPress paragraph generation so user-customized speaker names and merged diarization clusters display in published post transcripts.
  - **WordPress Export Content & Formatting Diagnostic Test**: Added a dedicated verification test (`_test_wordpress_export_content_and_transcript_formatter`) in `test_runner.py` asserting dictionary transcript slicing, range extraction, bilingual formatting, and media GUID resolution.
  - **Plugin Catch-Up Synchronization**: Synchronized WordPress plugin version to `3.7.14-stable` in `plugins/wordpress/manifest.json`.

## v3.7.13-stable
- **macOS Multiprocessing & PyInstaller Resource Tracker Intercept (`RadioTVSegmenter.py`, `radio_tv_story_segmenter_worker.py`, `test_runner.py`)**:
  - **Resolved "Unknown Processing Mode: from multiprocessing.resource_tracker import main;main(9)" Crash**: Fixed a critical crash on macOS when running multi-stage processing (transcription with parakeet-onnx or whisper, speaker detection, and story segmentation). In packaged PyInstaller builds on macOS/POSIX, `sys.executable` points to the compiled frozen binary (`RadioTVStorySegmenter` or `prs_worker`). When ML runtimes (WeSpeaker, sherpa-onnx, PyTorch, faster-whisper) spawn resource-tracking or child processes via `multiprocessing.spawn`, Python executes `sys.executable -c "from multiprocessing.resource_tracker import main;main(fd)"`.
  - **PyInstaller `freeze_support()` Initialization**: Added top-level `multiprocessing.freeze_support()` calls at the very entry points of both `RadioTVSegmenter.py` and `radio_tv_story_segmenter_worker.py`, ensuring all multiprocessing spawn protocols (`--multiprocessing-fork`) are caught before GUI or ML pipeline initialization.
  - **Direct `-c` Spawn Interception**: Implemented early command-line interception in both executables to directly execute `-c` code strings inside the frozen environment, allowing `resource_tracker` and spawn workers to initialize and exit gracefully instead of being rejected as unknown CLI flags.
  - **Comprehensive Diagnostic Test Bench Expansion (`test_runner.py`)**:
    * **Out-of-Process Worker Subprocess & IPC Diagnostic**: Added real child process execution (`_test_ai_worker_subprocess_execution_and_ipc_handshake`) testing worker binary launching, permissions, IPC `hello` handshake, and self-test execution.
    * **Frozen Subprocess Multiprocessing Spawn Protocol Test**: Added explicit child process test (`_test_frozen_subprocess_multiprocessing_spawn_protocol`) executing `-c` code to guarantee that subprocess spawn commands never fail or produce unknown mode errors.
    * **Full System & Troubleshooting Report Generator**: Added `generate_diagnostic_report` producing structured diagnostic reports with host OS specifications, architecture, frozen state, resolved worker paths, test results, and actionable remediation steps.
    * **Diagnostic Dialog Save & Copy Enhancements**: Updated GUI test bench dialog with a dedicated "Save Report to File..." button and rich clipboard copying for streamlined troubleshooting.

## v3.7.12-stable
- **Temporary Cache Manager & Preview Fix (`cache_manager.py`, `core_utils.py`, `prs_shared.py`, `media_batch.py`, `playback_preferences.py`)**:
  - **Resolved Unresponsive "Clear Temporary Cache" Action**: Fixed a missing `make_dialog_maximizable` import in `cache_manager.py` that caused `ClearCacheDialog` to raise a runtime exception and fail silently when invoked from **Settings > Clear Temporary Cache...**.
  - **Unified Interactive Cache Preview in Preferences**: Updated the **Preferences > Cleanup Data** page to open the interactive `ClearCacheDialog` instead of a blind confirmation prompt, allowing users to preview exact file counts and byte sizes across Video Thumbnails, Waveform Peaks, and Temporary Audio Extracts before purging.
  - **Multi-Directory Cache Scanning**: Enhanced `get_cache_disk_usage` and `purge_caches` to accurately scan and clean project-specific `.cache/` directories alongside system application data and temp folders without cross-directory directory collisions.
- **UI & Context Menu Icon Harmonization (`ui_layout.py`, `transcript_editor.py`, `story_metadata_dialog.py`)**:
  - **Menu & Action Bar De-Cluttering**: Removed decorative icons from the top menu bar (`Voice Profile Tools`) and right-click context menus (`Voice Profile Tools`, `Highlight Text`, `Change Highlight Color`, `Remove Highlight`), presenting a clean, consistent typography-first menu hierarchy while preserving functional color swatches for text highlighting.
  - **Stories Panel & Metadata Button Cleanups**: Removed emoji icons from `Story Metadata...` and `Auto-Generate Excerpt` buttons in the stories widget sidebar, aligning button styling with native desktop conventions.
  - **Transcript Toolbar & Formatting Refinements**: Removed leading symbols from `Split Speaker`, `Highlight ▾`, and the `Editing Mode` helper label in the transcript formatting toolbar.
  - **Story & Post Metadata Dialog Polish**: Streamlined actions in the metadata editor by removing icons from `Refresh WP Taxonomies`, `Sync to Playhead`, `Full Episode`, and individual `Story #N` task tabs while retaining core transport and status badges across the application.
  - **Dialog Ergonomics & Maximize Button Policy**: Audited `make_dialog_maximizable` across compact dialogs (Cache, Comment, Speaker Rename, Find/Replace, Update) to remove redundant maximize buttons and prevent awkward empty spacing, while preserving full maximize capabilities for data-intensive views.
- **Direct YouTube API Video Upload & Dual-Mode Publishing (`plugins/youtube/api.py`, `plugins/youtube/export_destination.py`, `plugins/youtube/plugin.py`, `plugins/youtube/manifest.json`)**:
  - **YouTube Data API v3 Client Engine**: Built full OAuth 2.0 PKCE client supporting scopes `youtube.upload` and `youtube`, featuring resumable video uploads with streaming 2MB chunks, real-time byte counters, throughput speed calculation, and remaining ETA.
  - **Automated Thumbnail & Caption Track Publishing**: Integrated automated custom video thumbnail uploading via `thumbnails.set` and closed caption (.srt) track insertion via `captions.insert`.
  - **Dual-Mode Publishing Workflow Selector**: Added a mode selector to easily toggle between **Direct 1-Click API Upload** (background API upload with direct link generation) and **Zero-API Assisted Upload** (browser launch and clipboard copying).
- **Google Sheets Tabular Export & Analytics Backend (`plugins/google_sheets.py`, `test_runner.py`)**:
  - **Production-Ready Google Sheets API v4 Client**: Created backend client supporting spreadsheet creation, A1 range appending, and data batch updates under scope `https://www.googleapis.com/auth/spreadsheets`.
  - **Rundown & Speaker Analytics Formatters**: Included domain transformers `format_story_rundown_table` and `format_speaker_analytics_table` for converting broadcast segment metadata and speaker talk-time airtime balance into spreadsheet rows.
  - **Dormant UI Architecture**: The backend engine is fully tested and ready in the codebase, with user-facing export UI deferred until scheduled in future rundown workflow milestones.

## v3.7.11-beta
- **Unified Voice Profile Tools Submenu & Multi-Entrypoint Integration (`transcript_editor.py`, `ui_layout.py`, `transcript_story.py`, `processing.py`)**:
  - **Single Cohesive Context Submenu**: Grouped all acoustic voice profiling, reference assignment, A/B dialog classification, and cluster inspection actions into a dedicated `🎙️ Voice Profile Tools` submenu within the transcript editor context menu, eliminating menu sprawl and elevating feature discoverability.
  - **Clear, Action-Oriented Tool Labeling**: Standardized submenu action titles with crystal-clear descriptors and tooltips:
    * `Teach / Match This Voice Across Project...` (uses reference voice profile to find and reassign matching turns)
    * `Set as Reference Profile for New Speaker...` (prompts for a new speaker name and immediately matches similar turns)
    * `Refine Rapid Dialog Turns (A/B Classifier)...` (competitively classifies turns in a conversational range between two confirmed speakers)
    * `Manage Speakers & Detection Clusters...` (inspects durations, renames/aliases, and merges duplicate clusters)
  - **Top Menu Bar Integration (`Tools -> Voice Profile Tools`)**: Added the full `🎙️ Voice Profile Tools` suite under the top-level **Tools** menu in `ui_layout.py`, enabling complete keyboard and menu bar access to voice profiling and clustering without requiring a prior right-click on the transcript canvas.
  - **Context-Aware Turn Inference Fallback**: Updated `teach_voice_profile_dialog` in `transcript_story.py` to smartly infer active turns from the transcript editor text cursor or current audio player position when launched without explicit segment coordinates, ensuring robust 1-click execution from the top menu bar.
  - **Pipeline State & Action Synchronization**: Integrated `voice_tools_menu` and all child actions into `set_tools_actions_enabled` within `processing.py`, ensuring actions are enabled/disabled gracefully with project transcript availability.

## v3.7.10-beta
- **Refine Rapid Dialog Turn Context & Timestamp Redesign (`prompt_refine_speaker_run` in `transcript_story.py`)**:
  - **Rich Dropdown Turn Selectors**: Replaced raw numeric segment index spinboxes with rich dropdown selectors displaying formatted timestamps, speaker labels, and spoken text snippets for both Start and End turns (e.g. `[00:14.200] Turn #4 (Leticia): “Hello, how are you today…”`), making turn boundaries immediately recognizable.
  - **Live Range & Context Preview Card**: Added a dedicated live preview container displaying the total turns selected, time span, and duration (e.g. `Range: Turns #4 to #14 (11 turns) • Time: 00:14.200 – 00:48.500 (34.30s)`), accompanied by styled text previews of the starting and ending speaker turns.
  - **Resilient Range Handling**: Seamlessly handles out-of-order turn selections, automatically normalizing bounds (`min(s_i, e_i), max(s_i, e_i)`).
- **Speakers & Detection Clusters Table Ergonomics & Legibility Fix (`SpeakerManagerDialog` in `transcript_story.py`)**:
  - **Row Height & Header Geometry Normalization**: Resolved severe vertical clipping of action buttons in the "Actions" column by standardizing table row heights (`setRowHeight(row, 46)`), setting vertical header default section size to 46px, and allocating a fixed 240px width to column 4.
  - **High-Contrast Action Button Styling**: Restyled "Rename / Alias" and "Merge Into..." buttons with crisp typography, high-contrast dark slate backgrounds, rounded borders, generous click targets (26px min-height), and pointing hand cursors for effortless legibility and interaction.
- **Acoustic Voice Profile Matcher Performance & Fluidity Upgrades (`VoiceProfileMatchDialog` & `find_matching_voice_turns` in `transcript_story.py`)**:
  - **Debounced Slider Scrubbing (60+ FPS)**: Separated instant threshold label updates from matching engine calculations using a 60ms single-shot debounce timer (`_slider_timer`), delivering fluid 60+ FPS slider responsiveness during rapid scrubbing without UI freezing.
  - **Precomputed Competitor Speaker Centroids**: Optimized `find_matching_voice_turns` by precomputing base centroids and top-turn sets for competitor clusters once outside the candidate loop, eliminating hundreds of redundant 256-dimensional vector calculations per threshold adjustment.
  - **Flicker-Free Batch Table Population**: Wrapped table updates in `setUpdatesEnabled(False)` and pre-allocated row counts (`setRowCount(len(self.matched_turns))`) instead of incremental `insertRow()`, completely removing layout thrashing.
  - **Player Seek Guarding**: Guarded `_on_table_selection_changed` during table updates to suppress spurious audio playback seeks while scrubbing the similarity threshold.
  - **User Selection State Retention**: Retained explicit turn deselects across threshold adjustments via `_user_deselected_ids`, ensuring user-unchecked candidates stay unselected.

## v3.7.9-beta
- **Test Bench Frozen-Path & Acoustic Voice Mock Signature Fixes (`test_runner.py`)**:
  - **Environment-Resilient Subtitle & DAW Module Resolution (`_resolve_export_subtitles_module`, `_resolve_export_daw_module`)**: Fixed `FileNotFoundError` during the `Audio / Subtitle Sync Drift Test` when running tests inside installed production directories (such as `C:\Program Files\Radio & TV Segmenter\`), frozen packages, or non-root working directories. Tests now resolve modules seamlessly via standard python package imports before falling back to multi-candidate filesystem paths (`_MEIPASS`, `_internal`, relative).
  - **Acoustic Voice Profile Mock Signature Compatibility**: Updated `MockTranscriptWindow.log_activity(self, msg, *args, **kwargs)` in `_test_acoustic_voice_profile_matcher` to gracefully accept keyword arguments such as `mark_dirty=False` emitted by `TranscriptStoryMixin.register_confirmed_speaker_turn()`, resolving `TypeError` when running against the live Qt mixin stack.
  - **Verified Full Diagnostic Suite (39 Tests)**: Re-verified all 39 diagnostic tests across clean-slate and arbitrary working directory environments, confirming 0ms drift in subtitle/chapter timing and flawless acoustic profiling.

## v3.7.8-beta
- **Zero-Config Google Docs & Drive Integration Redesign (`plugins/gdocs/auth.py`, `plugins/gdocs/plugin.py`, `plugins/gdocs/export_destination.py`, `GOOGLE_OAUTH_SETUP.md`, `GOOGLE_DOCS_USER_GUIDE.md`)**:
  - **Zero-Config User Authentication Flow**: Users no longer need to create a Google Cloud project, enable APIs, configure consent screens, or download/import `credentials.json` files. Integration operates out-of-the-box via a single **"Connect Google Account"** button.
  - **RFC 7636 PKCE & Cryptographic State Security**: Upgraded the local loopback OAuth engine to full Proof Key for Code Exchange (`code_verifier`, SHA-256 `code_challenge`, `S256`) and cryptographically random, single-use 32-byte `state` tokens, completely safeguarding local desktop callbacks against authorization code interception and CSRF attacks.
  - **Least-Privilege Scopes**: Enforced minimal required scopes (`documents`, `drive.file`, and `userinfo.email`). `drive.file` grants access exclusively to documents created or opened by RTVS, avoiding broad unrestricted Google Drive access and exempting the application from complex CASA Tier 2/3 security assessments.
  - **Modernized Loopback Server & Graceful Browser Handoff**: Binds dynamically on `127.0.0.1` (ports 8085-8095 or ephemeral), serves sleek styled status cards to the web browser on completion, and safely suppresses sensitive tokens from logs.
  - **Remote Token Revocation on Disconnect**: When disconnecting, the application securely removes tokens from OS keyring / machine-cipher storage and executes an explicit grant revocation request to Google's authorization servers.
  - **Advanced Developer Settings Accordion**: Advanced self-hosted or testing setups can still supply custom client IDs and client secrets through a collapsible developer accordion in Preferences, completely hidden from normal users.
  - **Developer Production Guide & User Documentation**: Created `GOOGLE_OAUTH_SETUP.md` detailing Google Cloud Console production configuration, consent screen verification, branding, and CASA exemptions, alongside `GOOGLE_DOCS_USER_GUIDE.md` for end-users.

## v3.7.7-beta
- **Acoustic Voice Profile Candidate Extraction Progress & Cancellation Guard (`transcript_story.py`, `test_runner.py`)**:
  - **Cooperative Candidate Extraction Progress Dialog (`_build_voice_profile_candidates`)**: Added a modal `QProgressDialog` that activates when opening `VoiceProfileMatchDialog` on un-diarized transcripts requiring significant on-the-fly acoustic vector extraction (> 12 uncached segments).
  - **Immediate Cancellation Escape Hatch**: Provides a responsive **Cancel** button with cooperative loop termination (`progress_dlg.wasCanceled()`) and `QApplication.processEvents()` pumping, preventing GUI freezes while preserving all partially computed vectors directly in segment cache (`seg["embedding"]`).
  - **Diagnostic Test Bench Coverage Extension (`test_runner.py`)**: Enhanced `_test_acoustic_voice_profile_reclustering` to validate candidate pre-caching progress extraction and cancellation state handling.

## v3.7.6-beta
- **Windows Installer Handoff & Detached Update Helper Architecture Overhaul — Milestone 4 (`updater.py`, `build_installer.py`)**:
  - **Standalone Detached Update Helper (`launch_and_install` in `updater.py`)**: Replaced temporary fragile PowerShell/CMD script file generation with a dedicated detached helper execution flow spawned with `CREATE_BREAKAWAY_FROM_JOB` and `DETACHED_PROCESS` flags.
  - **Clean Parent & Sibling Process Exit Polling**: Update helper directly polls caller process PID via native Win32 `OpenProcess` / `SYNCHRONIZE` handles and process discovery before initiating installation, completely preventing UAC credential dialog prompts over running windows or installer premature exits.
  - **Elevated UAC Execution Fallback (`ShellExecuteW` with `runas`)**: Launches the downloaded Inno Setup executable with administrative elevation (`runas`), falling back cleanly to standard process launch if elevation is declined or bypassed.
  - **Structured Update Logging (`%LOCALAPPDATA%\RadioTVStorySegmenter\update.log`)**: Implemented persistent timestamped update diagnostics logging across all update lifecycle phases: handoff initiation, PID polling, elevation attempts, installer launch status, and cleanup.
  - **Diagnostic Test Bench Coverage Extension (`test_runner.py`)**: Added unit test `Windows Detached Update Helper Architecture` validating script generation, parameter guards, non-existent target rejection, and update logging integrity.
 
## v3.7.5-beta
- **Acoustic Voice Profiling & Speaker Correction Engine Refinements (`speaker_identity.py`, `transcript_story.py`, `transcript_editor.py`)**:
  - **Candidate Vector Pre-Caching (`VoiceProfileMatchDialog` & `find_matching_voice_turns`)**: Implemented upfront candidate vector pre-caching (`_ensure_candidate_cache`), completely eliminating redundant WeSpeaker ONNX feature extractions and audio slice decodes during threshold slider scrubbing for instantaneous, stutter-free threshold adjustments.
  - **Robust Profile Synthesis & Competitor Target Separation**: Target speaker profiles are synthesized via robust multi-sample centroid aggregation (`robust_reference_profile`), and candidate turns assigned to the target speaker name are automatically excluded from competing acoustic profile sets.
  - **Detailed Acoustic Margin Tooltips**: Match table rows now display informative tooltips detailing target acoustic similarity, closest competitor similarity, and separation margin (e.g. `Similarity: 88.4% | Nearest competitor: 72.1% (separation: +16.3%)`).
  - **In-Place Rapid Keyboard Shortcuts for Candidate Toggling**: Added `Return`, `Enter`, and `X` shortcuts to immediately toggle candidate inclusion checkboxes directly while navigating the candidate table with keyboard arrow keys.
  - **Rapid Dialog Turns Competitive Classifier (`transcript_story.py`, `transcript_editor.py`)**: Added interactive `prompt_refine_speaker_run` dialog and transcript editor context menu action ("Refine Rapid Dialog Turns (Competitive Classifier)...") allowing users to competitively classify rapid, alternating dialogue turns between two confirmed anchor speakers using relative cosine distance, with automatic sample enrollment.
  - **Session-Wide Voice Profile Auto-Enrollment (`match_acoustic_voice_profile`)**: Automatically enrolls verified speaker turn embeddings into the active session voice profile cache (`_session_speaker_profiles`) upon applying acoustic voice identification.
- **Diagnostic Test Bench Subtitle/Speaker Alignment Synchronizations (`test_runner.py`)**:
  - Synchronized `DiagnosticEngine` unit tests (`_test_audio_subtitle_sync`, `_test_transcription_subtitle_export_parity`) with updated speaker detection logic, strict timestamp bounds, and modern formatting standards.
  - All 27 diagnostic test suites pass cleanly with 100% test suite fidelity.
- **Universal Window Maximize & Restore Flag Enforcement - Milestone 4.1 (`prs_shared.py`, all dialog modules)**:
  - Enforced `Qt.WindowMaximizeButtonHint` and maximized capability via standardized `make_dialog_maximizable` helper across all resizable modal and non-modal dialogs:
    - Core: `VoiceProfileMatchDialog`, `ChangeSpeakerDialog`, `StoryFadesDialog`, `SpeakerManagerDialog`, `StoryMetadataDialog`, `CommentEditorDialog`, `ClearCacheDialog`, `ProjectDataPurgeDialog`, `DiagnosticDialog`, `BenchmarkDialog`, `CheckUpdateDialog`, `UnifiedExportDialog`, `ReorderExportDestinationsDialog`, `RestoreSelectedSettingsDialog`, `BatchProcessingDialog`, and `PreferencesDialog`.
    - Plugins: `DriveFolderPickerDialog`, `GoogleDocsReviewDialog`, `GoogleOAuthSetupGuideDialog`, `PluginManagerDialog`, `GitHubPluginsDialog`, `WordPressSettingsDialog`, `WordPressPostMetadataDialog`, `WordPressPublishDialog`, `YouTubeSettingsDialog`, and `YouTubeAssistedUploadGuideDialog`.

## v3.7.4-beta
- **Acoustic Voice Profile & Speaker Identity Engine Architecture Upgrade (`speaker_identity.py`, `processing.py`, `transcript_editor.py`, `transcript_story.py`)**:
  - **Isolated Voice Profile Math & Identity Module (`speaker_identity.py`)**: Extracted core vector mathematical operations, similarity scoring, robust profile synthesis, centroid calculation, and confidence thresholding into a clean standalone module.
  - **Tight Overlap Embedding Filtering (`processing.py`)**: Prevented long macro-blocks (> 8s or > 2.5x segment duration) from stamping pooled acoustic vectors onto shorter transcript turns. Enforced minimum overlap thresholds (`best_overlap >= 0.5 * duration` or `>= 0.8s`) for accurate embedding attachment during diarization mapping.
  - **Enhanced Transcript Selection & Copy Support (`transcript_editor.py`)**: Enabled standard `Ctrl+C` / `Cmd+C` shortcuts across both viewing and editing modes, and added explicit context menu "Copy" actions for highlighted transcript selections.
  - **Refined Acoustic Profile Matcher & Re-Clustering (`transcript_story.py`)**: Upgraded `VoiceProfileMatchDialog` and acoustic voice turn matching logic with robust profile synthesis, multi-mode baseline comparisons, and high-confidence automatic re-clustering across timeline speaker turns.
## v3.7.3-beta
- **Interactive Audio Auditioning & Direct Playback Navigation in Acoustic Voice Profile Matcher (`transcript_story.py`)**:
  - **Click-to-Seek Candidate Navigation (`VoiceProfileMatchDialog` in `transcript_story.py`)**: Connected table selection changes (`itemSelectionChanged`) to `parent_window.seek_to(start_t)`, allowing instant timeline playhead and transcript view jump to any candidate speaker turn's exact timestamp upon selection.
  - **Spacebar Audition Play/Pause (`keyPressEvent` in `VoiceProfileMatchDialog`)**: Implemented keyboard event handling so pressing Spacebar while browsing candidate turns immediately plays or pauses audio from that turn's start time (smartly bypassing text inputs like editable speaker combo box).
  - **Auto-Audition Header Action & Double-Click Playback**: Added a dedicated **"▶ Audition Turn"** button in the candidate header bar alongside `cellDoubleClicked` event handlers to instantly trigger playback for candidate verification before reassigning speaker labels.

## v3.7.2-beta
- **Multi-Sample Acoustic Voice Profile Centroids & Composite Baseline Matching (`transcript_story.py`)**:
  - **Multi-Sample Vector Centroid Synthesis (`get_composite_embedding` in `transcript_story.py`)**: Implemented L2-normalized element-wise averaging across multiple segment embedding vectors. Allows building composite voice profile baselines that average out single-turn noise, microphone variations, or background interference for significantly improved speaker matching accuracy.
  - **Reference Baseline Selection Modes (`VoiceProfileMatchDialog` in `transcript_story.py`)**: Added interactive reference vector baseline mode controls directly in the Reference Speaker Turn Card:
    - *Single Reference Turn*: Matches candidate speech turns strictly against the single selected segment's 256-dimensional acoustic vector.
    - *Composite Speaker Profile*: Dynamically calculates an L2-normalized acoustic centroid averaged across all existing turns currently assigned to that speaker cluster in the project.
    - *Multi-Selection Profile*: Averages acoustic vectors across a custom multi-segment selection.
  - **Exclusion & Reassignment Precision (`find_matching_voice_turns` and `match_acoustic_voice_profile`)**: Updated candidate match search and re-clustering logic to exclude all reference profile turns from candidate list while automatically reassigning both candidate matches and reference profile turns synchronously when applying re-clustering.

## v3.7.1-beta
- **Acoustic Voice Profile Matcher Interactive Guidance & Initialization Stability (`transcript_story.py`, `radio_tv_story_segmenter_worker.py`)**:
  - **Collapsible Usage Hints & Feature Guide (`VoiceProfileMatchDialog` in `transcript_story.py`)**: Added an interactive, toggleable quick-start usage guide directly within the Acoustic Voice Profile Matcher window. Outlines reference turn selection, target speaker assignment, global vs. cluster search scope strategies, sensitivity threshold tuning, and candidate verification. Features a one-click `[Minimize / Hide Hints]` button and remembers visibility preferences in QSettings.
  - **Initialization Signal Race Condition Fix (`VoiceProfileMatchDialog` in `transcript_story.py`)**: Resolved an `AttributeError: 'VoiceProfileMatchDialog' object has no attribute 'thresh_slider'` caused by radio button `setChecked` signals firing during `__init__` before slider allocation. Deferred radio signal connections until after all controls are constructed and added defensive attribute guards to `_update_matches()`.
  - **Pydantic Model Freeze Exception Resolution (`radio_tv_story_segmenter_worker.py`)**: Resolved a `pydantic.ValidationError` when attaching acoustic vector embeddings to frozen diarization segment objects by calculating and serializing embeddings directly into dictionary representations without in-place mutation.

## v3.7.0-beta
- **Acoustic Voice Profile Matcher & On-Demand Re-Clustering (`transcript_story.py`, `radio_tv_story_segmenter_worker.py`)**:
  - **Voice Embedding Vector Persistence (`radio_tv_story_segmenter_worker.py`, `processing.py`)**: Preserved segment-level 256-dimensional WeSpeaker ONNX embedding vectors across diarization runs, worker results, project serialization dictionaries, and transcript segment metadata.
  - **"Teach This Voice" Interactive Match Dialog (`VoiceProfileMatchDialog` in `transcript_story.py`)**:
    - Added an intuitive dialog accessible directly from transcript speaker context actions.
    - Allows users to select a reference speech turn to "teach" an unseparated speaker's vocal characteristics.
    - Interactive Cosine Similarity threshold slider (0.50 – 0.95, default 0.70) with dynamic live candidate count and match highlighting.
    - Scope toggle to search either within the current speaker cluster only or across all timeline speaker turns.
    - Candidate match table displaying timestamps, similarity percentages (e.g., `94.2% match`), current speaker labels, and searchable text snippets with context.
    - Target speaker label selector supporting existing speaker names or instant creation of new speaker identities.
  - **On-Demand Cosine Similarity Re-Clustering Engine (`transcript_story.py`)**:
    - High-speed pure Python vector similarity engine evaluating unit-normalized acoustic embeddings without requiring full timeline re-diarization or heavy ML runtime re-execution.
    - Robust fallback for non-embedding runs and zero external runtime dependencies.
    - Seamless project state snapshot and full undo stack (`Ctrl+Z`) integration.
  - **Diagnostic Test Bench Coverage Extension (`test_runner.py`)**:
    - Added comprehensive automated diagnostic test 37 (`_test_acoustic_voice_profile_matcher`) validating 256-dimensional embedding retrieval, cosine similarity threshold filtering, timeline re-clustering, and state rollback fidelity.
 
## v3.6.5-beta
- **Google Drive & Docs Formatting Parity, Folder Management & Scopes (`plugins/gdocs/`)**:
  - **Project & Media File Name as Default Document Title**: Updated the default document title to automatically inherit the current project file name or media file name, replacing generic placeholder titles.
  - **Always-Bold Speaker Labels (`formatter.py`, `export_destination.py`)**: Speaker labels at the start of dialogue turns are now always bolded by default in Google Docs output with clean, dedicated textStyle styling, removing the need for a separate checkbox while guaranteeing consistent bold styling.
  - **Optional Story Chapters as H2 Headers for Table of Contents**: Added an optional checkbox ("Include Story Chapters as Headers (Table of Contents)") unchecked by default. When checked, story chapter boundaries are inserted as Heading 2 (`HEADING_2`) styled headers, enabling users to jump between stories using the Google Docs outline and Table of Contents.
  - **Language Selection & Dual Language Modes (`export_destination.py`, `formatter.py`)**: Added options to export transcripts in English, Spanish, or both. When both languages are selected, users can choose between generating separate Google Docs for each language or combining them into a single bilingual document with custom ordering (English first or Spanish first).
  - **Local Docx & WordPress Layout Parity (`formatter.py`)**: Rewrote the document generation engine to use `build_coherent_blocks`, grouping words and segments into natural paragraph blocks with bracketed muted timestamps and clean paragraph breaks matching the local Word document and WordPress exporters.
  - **Configurable Export Scopes**: Added scope selection controls supporting export of the full episode transcript, individual or selected stories, or full episode combined with selected/all stories.
  - **Interactive Google Drive Folder Management (`drive_folders.py`)**: Integrated `DriveFolderPickerDialog` enabling users to browse Google Drive hierarchy, select a default target folder for exports, and create new folders directly from the dialog via Google Drive API v3.
  - **Editorial Margin Comments Support**: Added optional toggle to anchor story editorial notes directly as native Google Docs margin comments.
- **WordPress Export Scope Post Builder Test Resilience (`test_runner.py`, `plugins/wordpress/export_destination.py`)**:
  - Added defensive `getattr(self, "metadata_editor_mode", False)` checks in `WordPressExportTabWidget` and ensured `MockWpWidget` provides `metadata_editor_mode`, resolving diagnostic test failures in headless runner environments.
- **Selective Purge & Stage Pipeline Rerun Safeguards (`project_lifecycle.py`, `processing.py`)**:
  - **Deep Purge State Cleanup**: Enhanced `purge_project_data` to reset all residual pipeline states (`transcription_result_received`, diarization caches, active queues, rerun confirmations, and speaker label sets) when clearing transcripts or diarization.
  - **Diarization Existence Validation**: Updated `_confirm_pipeline_rerun_if_needed` and `_processing_choice` to require that valid transcript segments actually exist before considering speaker diarization complete, eliminating spurious "Speaker Detection has already been completed" prompts after clearing or purging transcripts.
- **Customizable Export Destination Ordering (`export/dialog.py`, `playback_preferences.py`)**:
  - Implemented customizable destination display ordering in the Unified Export Center.
  - **Interactive Drag-and-Drop & Move Ordering (`ReorderExportDestinationsDialog`)**: Added interactive destination reordering dialog featuring smooth drag-and-drop list reordering and Move Up / Move Down buttons.
  - **Quick Reorder Access**: Added a dedicated "⇅ Reorder…" button directly inside the Export window's Destination section as well as a "Customize Export Destinations Order…" button in `Preferences > Batch & Export`.
  - **Default Destination Ordering**: Established clean default ordering prioritizing `Local Files (Media & Transcripts)`, `WordPress Draft Post`, `Google Docs`, and `YouTube Studio (Assisted Upload)`.
- **Google OAuth Loopback UX, Non-Blocking Progress & Error Handling (`plugins/gdocs/`)**:
  - **Non-Blocking Auth Progress Indicator**: Replaced blocking UI freezes with an asynchronous, parented progress dialog with a responsive Cancel button while awaiting browser authorization loopback callback.
  - **Targeted Google Error 403 / Access Denied Guidance**: Added actionable detection and guidance for Google Cloud 403 `access_denied` errors, providing direct deep links to Google Cloud Console Audience & Test User registration.
  - **Responsive Formatting Layout in Export Dialog**: Wrapped Google Docs export configuration in a dedicated scroll area and expanded default window dimensions (`860x700`) to guarantee all typography, paragraph styling, and comment anchoring controls fit comfortably without truncation.
  - **Simplified Destination Title**: Renamed export tab label to "Google Docs" across the exporter interface.

## v3.6.4-beta
- **Google Docs & Drive Export Plugin Architecture (`plugins/gdocs/`)**:
  - Implemented the complete Google Docs & Drive publishing plugin with modular zero-external-dependency REST architecture:
    - **OAuth 2.0 Loopback Authentication Engine (`plugins/gdocs/auth.py`)**: Built local loopback HTTP callback listener (`127.0.0.1:8085/callback`) for secure browser authorization, token exchange (`https://oauth2.googleapis.com/token`), OS keyring credential storage with encrypted machine-bound fallback, and automatic background access token refreshing.
    - **Google Docs REST API Serializer & Formatter (`plugins/gdocs/formatter.py`)**: Generates structured Google Docs documents featuring Title typography, metadata summary headers, story chapter sections (`HEADING_2`), uppercase speaker turn headers, paragraph styling, and optional inline word timestamps, computed with exact UTF-16 code unit offset ranges for Google Docs `batchUpdate`.
    - **Native Margin Comments & Drive Anchoring (`plugins/gdocs/comments.py`)**: Integrates with Google Drive Comments API (`drive.comments.create` and `drive.comments.list`) to attach story editorial notes, transcription corrections, and review tags directly into native margin comments anchored to document text snippets.
    - **Unified Export Center & Menu Integration (`plugins/gdocs/export_destination.py`, `plugins/gdocs/plugin.py`, `plugins/gdocs/manifest.json`)**: Seamlessly exposes "Google Docs & Drive" destination inside `UnifiedExportDialog` and `File > Export` menu with non-blocking execution, document title/folder configuration, and direct browser launching.
    - **One-Time Review & Comment Pull Integration (`plugins/gdocs/review.py`)**: Added `GoogleDocsReviewDialog` (via `Tools > Google Docs: Review & Pull Corrections...`) allowing editorial staff to inspect remote revisions in a Google Doc, view Drive margin comments, and pull verified transcript updates back into active project segments.
    - **Diagnostic Regression Verification (`test_runner.py`)**: Extended test 34 to validate live `gdocs` manifest schema, UTF-16 character code unit counting, document serialization, and segment revision diff calculations.

## v3.6.3
- **Diagnostic Test Bench Coverage Extension (`test_runner.py`)**:
  - Implemented 9 new zero-dependency and high-coverage automated diagnostic routines (tests 27 through 35) across the core system architecture:
    - **Translation Routing & Key Priority Unit Test**: Verifies `source_language_code()` and `target_language_code()` resolution under explicit (`es-en`, `en-es`) and auto-detection modes, ensuring proper directional precedence for bilingual projects.
    - **Symmetrical Translation Editing State Test**: Validates translation dictionary segment edits, state propagation, and automatic marking of stale translation states (`mark_stale_translations`) upon transcript mutation.
    - **Interactive Change Speaker Dialogue Flow Test**: Programmatically validates speaker change dialogue flows (All Instances, Contiguous Single Turn, Subsequent Occurrences, Cancel) to guarantee precision in downstream speaker reassignment.
    - **Story Boundary Validation & Overlap Test**: Enforces boundary normalization, monotonic bounds adjustment, fade curve serialization (`to_dict` / `from_dict`), and interval overlap detection.
    - **Audio / Subtitle Sync Drift Test**: Ensures 0ms timestamp alignment across SubRip (`.srt`), WebVTT (`.vtt`), YouTube chapter tracklists, and Red Book 75 fps CUE sheets.
    - **Interactive Transcript Editing & Split/Join Unit Tests**: Exercises segment splitting at arbitrary word timestamps, segment joining, word list concatenation, and index shift adjustments for speaker override maps.
    - **Exporter Structure Invariant Tests**: Validates structural syntax invariants for Cockos REAPER (`.rpp` S-expression tag balance), Magix Samplitude EDL (`.edl` v1.5 header & sample rate declarations), and Adobe Audition / FCP7 XML (`xmeml` sequence/media trees).
    - **Plugin Interface Sandbox Testing**: Tests `PluginManifest` schema validation, `BasePlugin` lifecycle hooks (`on_load`, `on_enable`, `on_disable`), and Google Docs comment anchoring intervals.
    - **Project File Integrity & Portable Path Resolution**: Tests structural validation error catching on corrupted/malformed project dictionaries and portable media file path resolution.

## v3.6.2
- **Selective Project Data Purge & Wipe Utility (`project_lifecycle.py`, `ui_layout.py`)**:
  - Implemented `ProjectDataPurgeDialog` accessible via `Edit > Clear / Purge Project Data...` with selective checkboxes for:
    - **Transcript & Timed Words**: Wipes transcribed segments, word-level timestamps, and character maps.
    - **Saved Translations**: Clears translation dictionaries, bilingual alignments, and resets translation display mode.
    - **Speaker Diarization**: Resets speaker clusters and custom names to an unassigned state.
    - **Stories & Metadata**: Removes segmented story boundaries, custom titles, excerpts, and tags while leaving transcripts intact.
    - **Audio/Video Media Link**: Unlinks active media file references and resets player/timeline state.
  - **Undo Stack Integration & Safety Guards**: Captures a full project state snapshot prior to purging, enabling instant recovery via `Edit > Undo` (`Ctrl+Z`).
  - Added visual warning indicators, checkbox tooltips, and "Select All" / "Deselect All" convenience toggles.
- **Glossary Import & Export Utility (`media_batch.py`, `terminology.py`)**:
  - Added dedicated **"Import..."** and **"Export..."** buttons to the Custom Vocabulary / Glossary dialog.
  - Supports importing and exporting terminology in standard JSON, CSV, and TSV formats with automatic schema deduplication.

## v3.6.1
- **Ultra Diarization Sensitivity Option & Unified Clustering Thresholds (`playback_preferences.py`, `radio_tv_story_segmenter_worker.py`)**:
  - Added a high-precision **Ultra (Studio — Extreme strictness for near-identical voices)** preset mapping to an acoustic cosine distance threshold of `0.38` (requiring $\ge 0.62$ cosine similarity).
  - Designed specifically for studio environments, podcasts, and co-anchor broadcasts where speakers of similar vocal timbres and acoustics risk being collapsed into a single speaker cluster.
  - Standardized the distance threshold calculation across all execution paths—including unconstrained auto-clustering and constrained Expected Speakers (`2` / `3+`) workflows—ensuring that sensitivity settings take effect reliably across the entire pipeline.
  - Updated the Preferences UI dropdown and descriptive tooltip under **Story Detection & Diarization**.

## v3.6.0-stable (Verified Stable Release)
- **Comprehensive Glossary & Protected Terminology Architecture (`terminology.py`, `plugins/translation/worker.py`, `media_batch.py`, `processing.py`, `translation.py`)**:
  - Implemented robust pre-translation protection for glossary terms and proper nouns, ensuring protected terms (such as `atrévete -> Atrévete` or protected brands/names) are never sent to the translation model destructively.
  - Isolated subprocess translation requests now explicitly carry structured glossary rules across process boundaries, resolving QSettings registry view disparities in child worker processes.
  - Added authoritative post-ASR glossary normalization (`normalize_transcript`) across all transcription backends.
  - Upgraded the Custom Vocabulary dialog with a structured bilingual table, dedicated "Don't translate" checkboxes, and robust schema parsing.
- **Milestone Confirmation & Verification**:
  - Confirmed that translation model detection and variant routing are fully operational across all NMT and ASR pipelines, making separate future detection roadmap tasks redundant.

## v3.5.34
- **Bidirectional MT Glossary Override Resolution (`plugins/translation/worker.py`)**:
  - Fixed an issue where explicit translation rules of the form `source -> translation` (such as `atrévete -> Atrévete`) were not recognized when translating Spanish to English (or vice versa), because the system searched the translated target text for the Spanish word `atrévete` instead of its translated counterpart.
  - Solved this elegantly by pre-translating the source word/phrase (e.g., `atrévete`) using the loaded model and tokenizer inside the translation worker thread to discover the machine translation output (e.g., `dare`).
  - Dynamically searches for both the original source word (to cover literal verbatim pass-throughs) and its translated counterpart (to cover translated outputs like `dare`) in the translated sentence, and replaces them with the designated target word (`Atrévete`) securely with full word boundaries (`\b`).
  - Retained fallback support for target-text direct matching rules (such as `dare -> Atrévete`).

## v3.5.33
- **Custom Translation Glossary Rules & Capitalization Protection (`plugins/translation/worker.py`, `media_batch.py`)**:
  - Implemented custom bidirectional translation glossary overrides and automatic proper noun protection.
  - Allowed users to specify explicit translation mapping rules using standard syntax like `source -> translation` (e.g., `dare -> Atrévete` or `brave -> Atrévete`) to force exact terminology mappings during neural machine translation.
  - Added automatic proper noun protection: if a word in the Glossary begins with a capital letter, the translator automatically detects its presence in the original source text and ensures its capitalization and spelling are preserved in the translated text.
  - Dynamically filtered translation mapping expressions (containing `->`) out of the Whisper initial prompt in `apply_glossary_to_whisper_context()` to avoid polluting transcription cues.
- **Dynamic Localization of Custom Vocabulary Dialog (`media_batch.py`)**:
  - Fully localized the Glossary dialog into Spanish and English depending on the active interface language preferences.
  - Added descriptive guides explaining the use of custom translation rules and automated proper noun casing.
- **Robust Glossary Loading on Startup (`media_batch.py`)**:
  - Fixed a startup issue where `_load_user_preferences()` was missing the loader routine for `self.glossary`, causing the custom vocabulary to remain empty until modified. Correctly loads and deserializes JSON glossary settings on boot.

## v3.5.32
- **Dynamic Language Routing for Multilingual ONNX Models (`radio_tv_story_segmenter_worker.py`)**:
  - Resolved a core pipeline bug where transcripts produced with the Multilingual FastConformer ONNX model were unconditionally labeled as language `"es"`, regardless of the spoken language in the audio.
  - Instead of discarding the real language-detection probe computed earlier (`probe_audio_language()`), wired the detected language (`detected_lang`) directly to the ONNX transcription generator to ensure proper translation directions and correct billing/export tracking downstream.
  - Retained the Spanish-only fallback mapping specifically for the Spanish FastConformer model, which is Spanish-only by construction.
- **Robust Project Metadata Null-Guard Check (`processing.py`)**:
  - Refactored the broad, always-true check `isinstance(self.project_metadata, object)` to a strict and safe null-guard check `self.project_metadata is not None` before syncing the detected spoken language to prevent state issues with uninitialized project objects.

## v3.5.31
- **Fixed Symmetrical Language Swapping & Fallbacks in Document Exports (`project_export.py`)**:
  - Resolved a bug where Spanish-source files with both English and Spanish checked produced swapped `.txt` and `.pdf` files. This occurred because `source_code` fallback logic hardcoded `"en"` when batch translation options were absent, mistakenly mapping translated blocks onto original filename suffixes.
  - Dynamically resolved the correct `source_code` fallback as `src_code` (which identifies `"es"` for Spanish-source projects and `"en"` for English-source projects).
  - Fixed a formatting bug in `.docx` exports where both English and Spanish Word files came out in Spanish. This occurred because the DOCX exporter dynamically retrieved word-level details from original Spanish segments (`source_segments`) even when formatting translated English text blocks, ignoring the translated strings.
  - Dynamically disabled original word-level segment fallbacks for non-matching languages (`lang_code != src_code`), ensuring the correct translated text is printed for translated tracks.

## v3.5.30
- **Dynamic Language Selection & Custom Labeling in Export Options (`export/dialog.py`, `project_export.py`, `plugins/wordpress/export_destination.py`)**:
  - Dynamically resolved and configured export options depending on whether the project's primary source language is English or Spanish.
  - Re-labeled "Spanish (Translated)" to "English (Translated)" in Spanish-source projects, and vice versa in English-source projects.
  - Correctly pre-checked the primary language checkbox ("Spanish" or "English") and only enabled the translation track checkbox if translation segments are generated.
  - Pre-selected the primary language in the WordPress export panel according to the project's source language dynamically.
  - Solved an issue where the export dialog failed to recognize translations, cleanly reading segment availability from the active project's translation dictionary structure instead of the non-existent `spanish_transcript` attribute.

## v3.5.29
- **Fixed Word-Level Display Bug in Translation-Only View (`transcript_story.py`)**:
  - Solved a deep-seated bug where selecting "English (Translation)" in Spanish-source projects incorrectly displayed the original Spanish words.
  - While whole translated segments contain the correct translated English string inside `segment["text"]`, deep-copied metadata from the original transcript segments included a legacy `"words"` array containing Spanish word timestamps.
  - Introduced an `is_rendering_translation` flag to dynamically skip mapping original word arrays when displaying translated text. The view now cleanly splits the translated string by space (using `seg_text.split()`) while correctly preserving parent segment timestamps for interactive seeks.

## v3.5.28
- **Dynamic Translation Key Prioritization (`translation.py`)**:
  - Refactored `get_spanish_translation_item` to dynamically prioritize translation key lookup based on `source_language_code()` (checking `es-en` first for Spanish-source projects, and `en-es` first for English-source projects).
  - This ensures that if a project has legacy or stale translation keys (e.g. from the previous Spanish-to-Spanish translation bug), they do not override or mask the correct, newly generated translations.
- **Automated Legacy Translation Key Purging (`translation.py`)**:
  - Programmed the `_on_translation_finished` callback to automatically purge obsolete/conflicting translation directions (e.g., popping out `en-es` when an `es-en` translation finishes, and vice-versa) to prevent project state pollution on re-translation.

## v3.5.27
- **Fixed Translation Display in English View (`transcript_story.py`)**:
  - Resolved a bug where Spanish-source projects rendered the original Spanish text when the "English (Translation)" view was selected in the transcript language dropdown.
  - Symmetrically updated `render_transcript` to load the translated English segments (`es_segments`) instead of defaulting to the Spanish original (`segments`) when the project source language is Spanish.
- **Symmetrical Translation Editing & State Management (`transcript_story.py`)**:
  - Standardized edit synchronizations in `on_transcript_text_changed` so that edits to the English translation text properly update the translation dictionary segments, keeping the translation "ready" and marking other translation directions "stale" correctly.
- **Dynamic Action Tooltips (`transcript_story.py`)**:
  - Dynamically customized the Edit/View transcript toggle button's tooltips to represent either English or Spanish translation editing depending on the active project's source language.

## v3.5.26
- **Restored Change Speaker Dialog Ergonomics (`transcript_story.py`)**:
  - Restored the streamlined three-button dialog layout for Change Speaker interactions: **All Instances**, **This Instance Only**, and **Cancel**.
  - Renamed the previous "This Turn Only" option to **This Instance Only** for improved clarity and consistency.
  - Eliminated the transitional "This & Subsequent" option from the layout to reduce clutter and align with user preferences.

## v3.5.25
- **Fixed Spanish-to-Spanish Translation Issue & Enhanced Language Detection (`translation.py`)**:
  - Implemented high-frequency Spanish stopword heuristics in `source_language_code()` as a fail-safe language detection mechanism.
  - When loading older project files or transcribing with engines that omit language metadata, the translation system now automatically detects Spanish transcripts from their text content.
  - This guarantees that translating a Spanish transcript correctly routes to `es-en` (Spanish to English) translation instead of incorrectly defaulting to `en-es` (English to Spanish), which previously caused the engine to output original Spanish text verbatim.
- **Dynamic Translation Labels in Split/Bilingual View (`transcript_story.py`)**:
  - Upgraded the transcript viewer's rendering logic to dynamically inspect `source_language_code()`.
  - The second line of translation in the split/bilingual view is now dynamically labeled as **`EN: `** for Spanish-to-English translations, and **`ES: `** for English-to-Spanish translations.

## v3.5.24
- **On-the-Fly Self-Healing & Robust Project Validation (`project_lifecycle.py`, `project_export.py`)**:
  - Fixed a critical validation error (`Project validation failed: Transcript segments are missing or invalid`) that would occasionally block users from saving their projects upon editing transcripts, exiting, or translating.
  - Implemented automatic real-time self-healing and structural normalization inside `validate_project_data()` across both the `project_lifecycle` and `project_export` modules.
  - When the transcription data model is temporarily represented as a raw list or an empty dictionary, the validation engine now instantly heals and normalizes the structure into a standard dictionary container (`{"segments": ...}`), preventing blocking save validation alerts and guaranteeing zero data loss.

## v3.5.23
- **Eliminated PySide6/Qt Dependency in Background Worker (`radio_tv_story_segmenter_worker.py`)**:
  - The background worker subprocess runs inside a lightweight python environment/virtual environment which purposefully does not have `PySide6` installed. 
  - Previously, `radio_tv_story_segmenter_worker.py` made imports from `prs_shared` which imported `PySide6` at the module level. This caused hidden `ImportError: No module named 'PySide6'` failures during model searches and transcript cleaning, silently breaking the auto-fallback availability checks and causing Whisper local loading to skip cached/installed paths.
  - Resolved this by creating zero-dependency, pure Python implementations of `get_app_data_dir_pure()` and `get_models_storage_dir_pure()` directly inside the worker.
  - Redirected transcript cleaning imports to the pure Python `transcript_cleaner` module rather than `prs_shared`.
- **Restored Fully Functional Model Availability Checks**:
  - Because `is_onnx_model_available()` is now 100% free of Qt/PySide6 dependency, model existence and status checks succeed perfectly on every run, preventing unwanted Whisper Small downloads/fallbacks when Spanish FastConformer or Multilingual FastConformer are installed.

## v3.5.22
- **Preserved User-Selected Spanish FastConformer & Multilingual Models (`radio_tv_story_segmenter_worker.py`)**:
  - Fixed model selection logic in `transcribe()` so that when `Spanish FastConformer ONNX` or `Multilingual FastConformer ONNX` is chosen as the default model in Preferences or the main UI, language probing preserves the selected ONNX model rather than overriding it or falling back to Whisper Small on Spanish audio.
  - Multilingual FastConformer is now properly recognized as a multi-language ONNX model and remains active across all supported non-English speech detections.
- **Enhanced Direct Model Search Paths (`radio_tv_story_segmenter_worker.py`)**:
  - Expanded `search_dirs` in `is_onnx_model_available()` and `transcribe_parakeet_onnx()` to resolve direct model paths when `PRS_MODELS_DIR` points directly to the model folder.

## v3.5.21
- **Eliminated False Positive ONNX Model Detection (`radio_tv_story_segmenter_worker.py`)**:
  - Removed parent directory search fallbacks from `is_onnx_model_available()`. Previously, searching bare parent directories like `PRS_MODELS_DIR` allowed `rglob("*")` to match files inside sibling model folders (such as `parakeet_onnx`), producing false positive availability reports for `fastconformer-es-onnx`.
  - Directory searches now strictly target model-specific destination folders (`fastconformer_es_onnx`, `fastconformer_multilingual_onnx`, `parakeet_onnx`).
- **sherpa-onnx Runtime Dependency Verification (`radio_tv_story_segmenter_worker.py`)**:
  - Added explicit runtime import validation (`import sherpa_onnx`) to `is_onnx_model_available()`. If the ONNX runtime module is missing or cannot be initialized, `is_onnx_model_available()` immediately returns `False`, preventing invalid model switches and runtime worker crashes.
- **Improved Auto-Switching Status Notifications (`radio_tv_story_segmenter_worker.py`)**:
  - When Spanish speech is probed, status messages now cleanly report whether Spanish FastConformer is being used or if the app is continuing with Whisper when FastConformer model files or the sherpa-onnx runtime are unavailable.

## v3.5.20
- **Universal Spanish FastConformer Auto-Switching (`radio_tv_story_segmenter_worker.py`)**:
  - Removed model-type restrictions on auto-language fallback probing in the background worker. Language inspection now runs whenever auto-fallback is enabled, regardless of whether `Whisper Small`, `Parakeet ONNX`, or another default model is selected.
  - When Spanish speech is detected, the worker automatically switches to `Spanish FastConformer ONNX` (or `Multilingual FastConformer ONNX`) if installed, enabling up to 10x faster Spanish transcriptions for all default model choices.
- **Recursive Multi-Subdirectory Model & Token Resolution (`radio_tv_story_segmenter_worker.py`)**:
  - Upgraded ONNX model file resolution (`tokens.txt`, `model.int8.onnx`, `encoder.int8.onnx`, etc.) in `is_onnx_model_available` and `transcribe_parakeet_onnx` to use recursive pattern matching (`rglob("*")`).
  - Ensures models downloaded into Hugging Face Hub subfolders or custom directory structures are detected and loaded flawlessly without falling back to Whisper.
- **Progress Stage Detail Banner Parsing (`processing.py`)**:
  - Fixed status message parsing in `processing.py` so that progress status updates containing fallback warning text accurately update `current_processing_stage_detail` to `Whisper Small` (or the active engine) instead of erroneously displaying `Spanish FastConformer ONNX`.

## v3.5.19
- **ONNX Model Availability Multi-Directory Search (`radio_tv_story_segmenter_worker.py`)**:
  - Upgraded `is_onnx_model_available` in the background worker to scan all candidate model storage locations (`PRS_MODELS_DIR` environment variable, custom storage path, and default appdata `models` folder).
  - Guarantees that when Spanish audio is probed, the worker reliably detects installed Spanish FastConformer ONNX models and auto-switches from Parakeet ONNX to Spanish FastConformer instead of falling back to Whisper.
- **Paragraph Grouping & Flow Restoration (`transcript_story.py`)**:
  - Removed an overly sensitive `time_gap >= 1.25` condition from the paragraph rendering logic that forced a paragraph break on short conversational breath pauses.
  - Same-speaker speech turns now naturally flow together into cohesive 35-50 word paragraph blocks (or until a speaker change or major silence pause $\ge 2.5$s occurs) as established in the formatting guidelines.
- **Speaker Separation Sensitivity Control (`playback_preferences.py`, `processing.py`, `radio_tv_story_segmenter_worker.py`)**:
  - Added a 4-tier **Speaker Separation Sensitivity** setting (`Low (Loose)`, `Normal (Balanced)`, `High (Strict)`, `Very High (Aggressive)`) in **Preferences > Story & Speaker Detection**.
  - Dynamically adjusts the Agglomerative Hierarchical Clustering (AHC) cosine distance threshold (from `0.78` down to `0.48`) in the `WeSpeaker ONNX` speaker diarization worker.
  - Setting sensitivity to **High** or **Very High** prevents the acoustic engine from over-merging distinct speakers with similar vocal pitches into a single label.
- **Spanish Download Prompt Fix (`processing.py`)**:
  - Fixed an issue where the "Download Spanish Model" prompt dialog was incorrectly shown after Spanish transcription even when a Spanish FastConformer model was already installed and used.
- **Language Probing & Dynamic Model Banner Fix (`radio_tv_story_segmenter_worker.py`, `processing.py`)**:
  - **Fixed Language Probe Parameter**: Resolved `TypeError` in `probe_audio_language()` by removing invalid `duration` keyword argument from `faster_whisper.transcribe()`, restoring fast language detection on audio files.
  - **Dynamic Model Stage Label**: Replaced hardcoded `Parakeet ONNX` string in worker chunk progress messages and updated `current_processing_stage_detail` in `processing.py` when auto-switching models. The activity bar now accurately displays `Spanish FastConformer ONNX` (or `Multilingual FastConformer ONNX`) when auto-switched.
- **Preferences Dialog NameError Resolution (`playback_preferences.py`)**:
  - Removed stale widget keys (`mod_expected_speakers_combo`, `mod_ask_speakers_chk`) from the preferences map, restoring normal launcher functionality for the Preferences dialog.

## v3.5.17
- **Smart "This & Subsequent" Speaker Reassignment (`transcript_story.py`)**:
  - Added a new **"This & Subsequent"** option to `ChangeSpeakerDialog` when renaming or reassigning a speaker label in the transcript view.
  - When two speakers are merged into a single cluster by speaker detection, clicking a speaker label and choosing **"This & Subsequent"** automatically updates that segment and all future occurrences of that speaker to the new name, eliminating the need to manually change each instance line by line.
- **Preferences Visibility & Accessibility (`playback_preferences.py`)**:
  - Added the **"Default Expected Speakers"** selector (`Auto-Detect`, `1 Speaker`, `2 Speakers`, `3+ Speakers`) and **"Speaker Estimate Prompt"** checkbox directly to the **Preferences > AI Models** tab.
  - Bidirectionally synced preferences across both the **AI Models** and **Story & Speaker Detection** tabs so settings remain accessible wherever users look for speaker detection options.

## v3.5.16
- **Live Progress Stage Branding & Real-Time Spanish Language UI Updates (`processing.py`, `translation.py`, `model_management.py`, `radio_tv_story_segmenter_worker.py`)**:
  - **Dynamic Stage Progress Branding**:
    - Resolved issue where the top activity bar mislabeled ONNX engines (e.g. `Transcription (Whisper fastconformer-multilingual-onnx)`).
    - Progress indicator now displays clean, accurate model branding based on the active engine (e.g. `Parakeet ONNX`, `Spanish FastConformer`, `Multilingual FastConformer`, or `Whisper {model}`).
  - **Real-Time Live Transcript Language Dropdown Synchronization**:
    - Resolved issue where the transcript view language selector defaulted to `English (Original)` during live transcription and only changed to `Español (Original)` upon job completion.
    - Updated `source_language_code()` and initial transcription setup to inspect `ProjectMetadata.source_language` and `translation_display_mode` dynamically, immediately updating the transcript language dropdown to `Español (Original)` as soon as Spanish audio is probed or a Spanish model is initialized.
  - **Strict Model Cache & Folder Validation**:
    - Fixed model candidate lookup in `model_management.py` and `radio_tv_story_segmenter_worker.py` to prevent ONNX models from matching against files in parent storage directories or misreporting disk usage.

## v3.5.15
- **Next-Gen ONNX AI Model Suite & Smart Spanish FastConformer Integration (`model_management.py`, `radio_tv_story_segmenter_worker.py`, `processing.py`, `playback_preferences.py`, `transcript_story.py`, `prs_shared.py`)**:
  - **New AI Model Options & Downloads**:
    - Added download & install options for **Parakeet ONNX Fast TDT (English)**, **Spanish FastConformer (Spanish)**, and **Multilingual FastConformer (English & Spanish)** in the AI Model Manager and Preferences.
    - Removed legacy `distil-medium.en` and `distil-large-v3` options from model choices and download lists.
  - **Smart Spanish Model Preference & Download Prompting**:
    - When non-English speech (`es`) is detected during pre-transcription probing, the app automatically checks for installed Spanish-compatible FastConformer models (`fastconformer-es-onnx` or `fastconformer-multilingual-onnx`).
    - If a Spanish FastConformer model is installed, transcription seamlessly uses that ultra-fast ONNX model (~250MB, CTC architecture) instead of falling back to Whisper.
    - If no Spanish-compatible FastConformer model is installed, the app falls back to Whisper Small and displays a prompt offering to open Manage AI Models to download one for up to 10x faster Spanish transcriptions.
  - **Transcript Paragraph Break Calculation Fix**:
    - Resolved issue where transcripts rendered as one giant block of text without paragraph breaks when using CTC models or continuous speech.
    - Updated `MIN_WORDS_PER_PARAGRAPH` threshold (from 100 to 35) and added multi-factor break conditions based on speaker changes, pause/silence gaps (>= 1.25s), segment boundaries, and sentence boundaries.
  - **Activity Meter ETA & Timer Cleanup**:
    - Resolved issue where the activity meter continued showing time elapsed after transcription was completed by explicitly stopping the ETA progress timer (`set_processing_stage(None)`) upon transcription completion.

## v3.5.14
- **Smart Language Detection, Automatic Whisper Model Switching & Dynamic Translation Alignment (`radio_tv_story_segmenter_worker.py`, `processing.py`, `playback_preferences.py`, `translation.py`)**:
  - **Pre-Transcription Language Prober & Auto-Fallback**:
    - Implemented a lightweight 15-second pre-transcription speech prober (`probe_audio_language`) using `faster-whisper`.
    - When `parakeet-onnx` (English-only) is selected and auto-language fallback is active, automatically detects non-English speech (such as Spanish) with confidence probability scoring.
    - Seamlessly reroutes the transcription pass to `Whisper Small` (or configured multilingual model) with clear live activity log notifications, avoiding Parakeet ONNX character garbage or failure on non-English speech.
  - **Dynamic Primary Language Assignment & Metadata Persistence**:
    - Automatically updates `ProjectMetadata.source_language` and session state upon transcription completion to reflect the actual spoken language (e.g. `es`).
  - **Dynamic Transcript Language Selector & Inverted Translation Alignment**:
    - Updated the search bar transcript language dropdown to dynamically display the native original language (e.g., `"Español (Original)"` when Spanish is detected, instead of hardcoding `"English (Original)"`).
    - Configured the OPUS-MT neural machine translation engine to translate from the detected non-English source language back to English (e.g., `es -> en`), offering `"Español (Original)"`, `"English (Translation)"`, and `"Bilingual (Split)"` display modes.
  - **User Preferences Control**:
    - Added `[x] Auto-detect non-English speech & fall back to Whisper Small for non-English audio` option in Preferences > AI Models, backed by `auto_detect_fallback_whisper` settings storage and `PRS_AUTO_LANGUAGE_FALLBACK` environment propagation.

## v3.5.13
- **Resolved Video Thumbnail Cache NameError (`prs_shared.py`, `media_batch.py`)**:
  - Fixed `NameError: name 'read_video_thumbnail_cache' is not defined` when opening media files containing video tracks.
  - Re-exported `get_video_thumbnail_cache_dir`, `read_video_thumbnail_cache`, and `invalidate_video_thumbnail_cache` from `background_workers.py` in `prs_shared.py`, and added explicit module imports in `media_batch.py`.
  - Prevented media loading routines from crashing on video files, ensuring audio waveform and video thumbnail generation overlays resolve and clear properly.

## v3.5.12 (including WordPress Plugin v3.5.12)
- **Unified Story & Post Metadata Architecture (`story_metadata_dialog.py`, `story_widgets.py`, `ui_layout.py`, `transcript_story.py`, `plugins/wordpress/export_destination.py`)**:
  - **Universal Core Story & Post Metadata Dialog**:
    - Created `StoryMetadataDialog` as a dedicated, universal multi-pane metadata workspace accessible via the "🗗 Story Metadata..." button in the Stories sidebar and the story list right-click context menu.
    - Features tabbed target switching between the Full Episode (🎬) and individual stories (📖 1, 📖 2...), with synchronized editing for Title, Authors, Categories/Tags, Excerpts, Editorial Notes, and Featured Video Frame captures.
    - Integrated FFmpeg video frame grabber with stepper adjustments (`-1s`, `-1f`, `+1f`, `+1s`, `⟳ Playhead`) and live 160x90 image thumbnail previews.
    - Integrated one-click transcript synopsis generator (~55-word auto-excerpt) directly into the dialog.
  - **Dynamic WordPress Taxonomy Enrichment & Offline Flexibility**:
    - When the WordPress plugin is active, automatically enriches the dialog with live author profiles (including Co-Authors Plus guest authors) and hierarchical categories with instant real-time search filtering.
    - When WordPress is inactive or offline, provides clean local author and category/tag entry with autocompletion and manual input fields.
  - **Instant Two-Way UI & Story List Synchronization**:
    - Synchronizes all metadata edits directly to `ProjectMetadata` and `Story.metadata`, automatically updating the main story details panel (Title, Author, Excerpt).
    - Immediately triggers `StoryListWidget.refresh_story_list()` so customized story titles update in real-time in the story list.
    - Persists all configured metadata directly to `.rtvs` project files upon saving.
  - **Streamlined Stories Sidebar Layout**:
    - Replaced redundant plugin-specific group boxes with a clean "🗗 Story Metadata..." launcher alongside the Export button, maximizing vertical screen real estate for story list items and timeline editing.
  - **Version Synchronization**:
    - Synchronized application core and WordPress plugin to `v3.5.12` across `prs_shared.py`, `core_utils.py`, `updater.py`, `build_installer.py`, Inno Setup installer, plugin manifest, and documentation.

## v3.5.11 (including WordPress Plugin v3.5.11)
- **Dedicated WordPress Post Settings Dialog & Stories Launcher (`plugins/wordpress/export_destination.py`, `plugins/wordpress/plugin.py`, `plugins/wordpress/manifest.json`)**:
  - **Multi-Pane & Tabbed WordPress Post Settings Modal**:
    - Converted post metadata editing into a dedicated modal dialog (`WordPressPostMetadataDialog`) that mirrors the WordPress Export Center interface.
    - Integrated side-by-side multi-pane layouts for Authors (with Co-Authors Plus guest author support and filtering) and Categories (hierarchical with filter search), alongside tabbed per-post navigation for Full Episode and all segmented stories.
    - Added instant two-way synchronization between post metadata configurations and the project's active story UI fields (updating title, excerpt, and author in real-time) and persisting progress to the `.rtvs` project file whether users complete all tasks at once or incrementally.
  - **Streamlined Stories Panel Integration**:
    - Replaced the embedded form with a compact summary card and a prominent "🗗 WordPress Post Settings..." launcher in the Stories sidebar, displaying configured titles, authors, categories, featured image status, and post status at a glance with quick auto-excerpt and taxonomy refresh triggers.
  - **Bug Fixes & Hardening**:
    - Resolved `TypeError: format_time() got an unexpected keyword argument 'include_hours'` by aligning timestamp formatting with `prs_shared.format_time(include_millis=True)`.
    - Resolved `AttributeError` for custom notice section in `WordPressExportTabWidget` by updating references to `wp_custom_section`.
  - **Plugin Version Synchronization**:
    - Synchronized WordPress plugin version to `v3.5.11` in `plugins/wordpress/manifest.json`.

## v3.5.10 (including WordPress Plugin v3.5.10)
- **Full-Window Stories Panel Maximization (`ui_layout.py`, `story_widgets.py`, `processing.py`, `transcript_story.py`)**:
  - **Comprehensive Multi-Widget Minimization**:
    - Enhanced the Stories Panel maximize toggle (`toggle_maximize_stories_panel`) to hide the timeline and transcript panels (`timeline.hide()`, `transcript_panel.hide()`, `activity_panel.hide()`) and set splitter ratios to `[0, 1000]` and `[1000, 0]`, enabling the Stories widget to expand across 100% of the main application window for focused metadata editing and story management.
    - Full bidirectional restoration: toggling restore immediately un-hides the timeline, transcript panel, and activity log, returning splitters to their exact pre-maximized dimensions.
  - **Dynamic Story List Height Adaptation**:
    - Implemented `StoryListWidget.adjust_height_to_contents()` and `update_story_list_height()` in `ui_layout.py` and `transcript_story.py`.
    - Automatically constrains the story list widget to only occupy the exact vertical space needed for its current items (capped at 220px when maximized), reserving all remaining vertical room for metadata editors, author checklists, excerpt boxes, and plugin extension panels.
- **Persistent Story Authors, Excerpts & WordPress Publishing Metadata (`plugins/wordpress/plugin.py`, `ui_layout.py`, `transcript_story.py`, `processing.py`, `project_export.py`)**:
  - **Core Story Author & Excerpt Editing**:
    - Integrated native Author (`QLineEdit`) and Excerpt (`QTextEdit`) controls into the main story details panel, including an instant "Auto-Generate Excerpt" button that generates a clean ~55-word synopsis from the story's transcript range.
    - Synchronized author and excerpt inputs with `Story.metadata["author"]` and `Story.metadata["excerpt"]`, ensuring full persistence in `.rtvs` project files for later export sessions.
  - **WordPress Author & Taxonomy Checklist Extension & Full Post Settings Parity**:
    - Upgraded `WordPressStoryMetadataWidget` in `plugins/wordpress/plugin.py` to achieve complete feature parity with the WordPress Export Dialog directly within the Stories editing workspace.
    - Integrated Target Switcher dropdown supporting seamless switching between Full Episode post configuration and individual segmented stories.
    - Added dedicated Post Title editor, Status selector, rich Excerpt editor with "Auto-Generate Excerpt", multi-author search with checkable list (supporting standard WP users and Co-Authors Plus guest authors), category search and checklists, manual overrides, and tag editors.
    - Implemented interactive Video Scrubber and Featured Image frame grabber directly inside the Stories panel with stepper controls (`-1s`, `-1f`, `+1f`, `+1s`, `⟳ Playhead`) and instant live 160x90 thumbnail preview.
    - Implemented Bulk Application tools across Authors, Categories, and Featured Image Thumbnails: "Apply to Selected Stories" (targeting multi-selected stories) and "Apply to All Stories" (applying settings globally across all stories and full episode).
    - Added "⛶ Maximize Panel" and "🗗 Pop-out..." buttons in the Stories header, launching the full-screen `WordPressPostMetadataDialog` modal for comfortable batch management.
    - Added instant two-way synchronization between the WordPress metadata widget, core story inputs, and the underlying `.rtvs` project file model.
  - **Export Engine Inclusion**:
    - Updated `project_export.py` text transcript story exports to format story-level Author and Excerpt metadata in the export headers.
  - **Unified Export Center Window Maximization**:
    - Verified `UnifiedExportDialog` window maximize/restore button in the dialog header, enabling full-screen expansion for comfortable batch configuration.
  - **Plugin Version Catch-Up**:
    - Synchronized WordPress plugin version to `v3.5.10` in `plugins/wordpress/manifest.json` per the lazy catch-up policy.

## v3.5.9 (including WordPress Plugin v3.5.9.1)
- **WordPress Export Cross-Linking & Rich Text Hyperlink Formatting (`plugins/wordpress/client.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/manifest.json`)**:
  - **Full Episode & Story Cross-Linking**:
    - When exporting a full episode alongside individual stories, the publisher automatically captures the parent episode's post URL and injects an attribution link (e.g. *"This story was broadcast as part of Full Episode"*) into each published story post.
    - Configurable notice positioning (top of post after player vs. bottom of post) and customizable template strings (supporting `{episode_title}` and `{episode_link}` placeholders).
    - Added automated back-linking: once all individual stories are published, the plugin optionally updates the parent Full Episode post with a Gutenberg-compatible Table of Contents indexing all broadcast stories with clickable links.
  - **Rich Text & Hyperlink Formatting**:
    - Integrated comprehensive rich text and hyperlink parsing in `format_rich_text_to_html()` for transcript paragraphs and custom notice blocks.
    - Automatically converts standard Markdown hyperlinks (`[text](url)`), auto-links raw URLs (`https://...`), and passes through safe HTML tags (`<a>`, `<strong>`, `<em>`, `<code>`) while sanitizing all other content.
  - **Plugin Version Bump**:
    - Incremented WordPress plugin release to `v3.5.9.1` in `manifest.json` following the selective plugin catch-up policy with zero impact on the core application footprint.
- **WordPress Plugin Decoupling & Modular Architecture Migration (`plugins/wordpress/`, `RadioTVSegmenter.py`, `project_export.py`, `playback_preferences.py`)**:
  - **Complete Core Decoupling**:
    - Fully removed `wordpress_export.py` and decoupled `WordPressExportMixin` from `MainWindow`, guaranteeing core application modules never import from `plugins/` per architectural invariants.
    - Updated export destination handling in `project_export.py` to route purely through dynamic plugin discovery via `plugin_manager.get_export_destinations()`.
  - **Isolated Client & Preferences (`plugins/wordpress/client.py`, `plugins/wordpress/preferences_page.py`)**:
    - Centralized all WordPress REST API interactions, secure keyring and DPAPI encrypted credential management, connection testing, and preferences page directly into `plugins/wordpress/`.
    - Integrated dynamic plugin preference discovery in `playback_preferences.py`, ensuring WordPress settings only appear when the plugin is enabled.
  - **Story Editor WordPress Metadata Widget (`plugins/wordpress/story_metadata_widget.py`, `ui_layout.py`, `story_widgets.py`)**:
    - Implemented `WordPressStoryMetadataWidget` dynamically loaded into the main Story Editor sidebar. Allows authors to assign Author, Post Status, Categories, Tags, Excerpt, and Featured Image directly while editing stories.
    - Persisted WordPress metadata cleanly within `.rtvs` project file schemas under `story.custom_metadata["wordpress"]` and pre-populated into the Export Center dialog.
    - Guaranteed zero UI contamination: when the plugin is disabled or uninstalled, the story editor remains free of WordPress controls.
  - **Self-Contained Export Destination (`plugins/wordpress/export_destination.py`)**:
    - Migrated media file uploading and draft/published post creation workflows into `WordPressExportDestination.execute_export()`.
- **Project Lifecycle & Broadcast Audio Export Modularization (`project_lifecycle.py`, `export/audio.py`, `project_export.py`)**:
  - **Project Lifecycle Separation**:
    - Extracted project file persistence (`close_project`, `save_project`, `save_project_as`, `open_project`, `_save_project_file`) from `project_export.py` into dedicated `ProjectLifecycleMixin` in `project_lifecycle.py`.
  - **Broadcast Audio & Stem Rendering Separation**:
    - Extracted broadcast audio rendering, fade curve processing, channel stem mixing, and normalization into `export/audio.py`.
- **Workspace & Export Fullscreen Expansion Controls (`ui_layout.py`, `export/dialog.py`)**:
  - **Story Workspace Maximization**:
    - Added maximize and restore toggle buttons to the Stories Panel allowing users to expand the story list and metadata editor across the entire application workspace for focused editorial work, with seamless restoration to the standard split-view layout.
  - **Export Center Dialog Maximization**:
    - Added maximize and fullscreen controls to `UnifiedExportDialog` for comfortable batch story export review and configuration.

## v3.5.8
- **Audio Fades "Apply" Action & Live Auditioning (`transcript_story.py`)**:
  - **Live Auditioning Without Closing Dialog**:
    - Added an "Apply" button to `StoryFadesDialog` alongside "Save Fades" and "Cancel", allowing real-time timeline visualization and auditioning of fade envelopes without dismissing the dialog.
    - Added snapshot tracking of pre-dialog fade states across all stories (`_initial_fades`), ensuring that clicking "Cancel" after applying changes seamlessly rolls back both the data model and timeline visualization.
    - Synchronized `MainWindow.edit_story_fades` undo/redo stack commands (`StoryFadesChangeCommand` / `SetStoriesCommand`) with the pre-dialog baseline values, preserving clean undo history even when multiple live applications are performed.
- **Timeline Navigation & Story Selection Performance Optimization (`timeline_widgets.py`, `transcript_story.py`)**:
  - **High-Frequency Drag Event Throttling**:
    - Implemented a 60 FPS (~16ms) rate limiter in `TimelineCanvas.mouseMoveEvent` during continuous drag operations (boundary edge dragging, fade handle adjustment, region selection, and scrub navigation) to eliminate UI thread event flooding.
  - **Deferred Sidebar List Relayout**:
    - Removed synchronous `QListWidgetItem` string reformatting and serialization from `handle_drag_story_region` in `transcript_story.py`, updating only start/end time inputs during the drag. Full list item widget updates and project saves are deferred to `handle_drag_finished`.
  - **Precomputed Fade Curve Geometry & Vector Caching**:
    - Precomputed 16-step lookup tables (`_FADE_IN_CURVE_TABLES`, `_FADE_OUT_CURVE_TABLES`) for all curve profiles (`linear`, `s_curve`, `logarithmic`, `exponential`), replacing dynamic mathematical evaluations on every frame.
    - Pre-cached pens and brushes in `TimelineCanvas` for fade fills, ramp strokes, and tactile grab handles, avoiding repetitive color allocations during rapid canvas repaints.
    - Cached story boundary snapping points in `set_stories` and during active drags to eliminate redundant boundary iteration overhead in `snap_time`.

## v3.5.7
- **Detached Process Supervisor & UAC Elevation Synchronization (`updater.py`)**:
  - **Process Lifecycle Synchronization**:
    - Replaced synchronous installer elevation with a fully detached, multi-stage supervisor script (`.ps1` with `.cmd` fallback).
    - The supervisor script monitors both the current process PID (`curr_pid`) and any process matching `RadioTVSegmenter.exe` / `RadioTVStorySegmenter.exe` until termination before triggering `Start-Process -Verb RunAs`.
    - Integrated a mandatory 2-second kernel release delay after process exit to guarantee all DLLs and executable file handles are released before setup launches.
  - **Instant UI Teardown**:
    - Refactored `_install_and_restart()` to immediately hide all top-level application windows (`widget.hide()`) and flush `QSettings` before scheduling a 0.8s hard exit watcher.
    - Prevents UAC elevation dialogs from popping up over active application windows and resolves installer premature auto-close collisions caused by file lock contention.

## v3.5.6
- **WordPress Export Scope Filtering Fix (`plugins/wordpress/export_destination.py`)**:
  - **Resolved Export Scope Regression**:
    - Fixed scope resolution in `rebuild_post_items()` so the export destination correctly queries `self.window()` (the top-level `UnifiedExportDialog`) for `scope_combo.currentData()`.
    - Resolved parent widget hierarchy traversal failure where `self.parent()` pointed to `QStackedWidget` rather than the export dialog, preventing scope checks from falling back to `"full"`.
  - **Synchronized Scope Signal Handling**:
    - Updated `WordPressExportDestination.on_scope_changed()` to explicitly forward the updated `scope` string parameter to `rebuild_post_items(scope=scope)`.
    - Ensures switching dropdown options between "Selected Stories", "All Stories", "Full Episode", and "Full Episode & All Stories" immediately updates the post navigation sidebar and configures draft uploads for the requested scope.
- **Diagnostic Test Bench Expansion (`test_runner.py`)**:
  - Added automated unit test (`WordPress Export Scope Post Builder`) verifying post items rebuilding and excerpt generation across all four export scope modes.

## v3.5.5
- **Multi-Format DAW Timeline Interchange Expansion (`export/daw.py`, `export/dialog.py`, `project_export.py`)**:
  - **Expanded DAW & NLE Interchange Formats**:
    - Added native support for Audacity Label Tracks (`.txt`), Adobe Audition / Final Cut Pro / Premiere XML (`.xml`), and Universal DAW Marker Lists (`.csv`) alongside Cockos REAPER (`.rpp`) and Magix Samplitude EDL (`v1.5`).
    - Added individual format toggle options in the Unified Export Center dialog with persistent state saved via `QSettings`.
  - **Unselected Audio Timeline Handling**:
    - Resolved issue where timeline exports excluded unselected audio gaps between story boundaries.
    - Added configurable "Unselected Audio Mode" setting in the Export Center with three modes:
      - **Exclude**: Export only selected story boundaries (legacy behavior).
      - **Split into Separate Clips**: Generate timeline clips for unselected audio gaps between stories.
      - **Include as Muted Clips**: Include unselected timeline gaps as explicitly muted audio clips in supporting DAWs (e.g. REAPER, Audition XML).
  - **Standalone DAW Format Exporters (`project_export.py`)**:
    - Exposed standalone export menu options and helper methods (`export_audacity_labels`, `export_audition_xml`, `export_daw_marker_csv`).
- **Diagnostic Test Bench Expansion (`test_runner.py`)**:
  - Added automated unit test (`DAW Timeline Interchange and Gap Handling`) verifying timeline clip construction, gap splitting, muting flags, and output format syntax across all DAW generators.

## v3.5.4
- **Contiguous Speaker Turn Reassignment (`transcript_story.py`)**:
  - **Single-Click Contiguous Turn Reassignment**:
    - Resolved speaker label reassignment regression where changing a speaker label only affected a single segment, requiring users to repeatedly change every segment in a paragraph.
    - Updated speaker label reassignment (`execute_speaker_rename`, `insert_speaker_label_at_time`, `split_segment_at_time`) to identify the full contiguous turn of segments sharing the selected speaker label.
    - Reassigns all words between the selected point and the next occurrence of a different speaker label in a single click.
  - **Diagnostic Test Bench Expansion (`test_runner.py`)**:
    - Added automated unit test (`Speaker Reassignment Contiguous Turn Logic`) verifying contiguous segment identification and boundary protection against subsequent speaker turns.

## v3.5.3
- **Windows Updater Race Condition Fix (`updater.py`)**:
  - **Detached PowerShell Supervisor**:
    - Resolved execution race condition on Windows where UAC prompts appeared before `RadioTVSegmenter.exe` closed, causing the installer to flash and exit prematurely due to file locks.
    - Implemented a background PowerShell PID supervisor that polls `os.getpid()` until `RadioTVSegmenter.exe` fully terminates and releases all process handles before launching the elevated installer wizard (`Start-Process -Verb RunAs`).
- **MP3 ID3 Tag Editor Module & Dialog (`id3_editor.py`)**:
  - **Comprehensive ID3 Metadata Editing**:
    - Added dedicated PySide6 ID3 Tag Editor dialog supporting standard ID3v2 metadata fields: Title (TIT2), Artist / Speaker (TPE1), Album / Show (TALB), Year (TYER/TDRC), Track Number (TRCK), Genre (TCON), Publisher / Call Sign (TPUB), Composer / Editor (TCOM), and Comments (COMM).
    - Integrated album cover art management (APIC frame) with interactive image picker and thumbnail preview.
  - **Dual ID3 Engine (Mutagen + Pure-Python Fallback)**:
    - Utilizes `mutagen` library when present in environment, backed by a robust pure-Python ID3v2.3 binary reader and writer fallback.
  - **One-Click Project Auto-Fill & Menu Integration**:
    - Added "⚡ Auto-Fill from Project" button in ID3 dialog to populate metadata from active project name, story titles, and speaker labels.
    - Added "🏷️ Edit ID3 Tags (MP3)..." action to the Tools menu (`Ctrl+Shift+I`) and Unified Export Center.
  - **Automated Story Clip Tag Embedding (`project_export.py`)**:
    - Automatically embeds ID3v2 tags into exported MP3 story clips during single or batch export passes.

## v3.5.2
- **GitHub Actions CI/CD Pipeline Hardening & Artifact Staging**:
  - **Isolated Artifact Package Staging (`dist/release_packages/`)**:
    - Created dedicated release packaging directories across Linux, Windows, macOS, and plugin build jobs.
    - Isolated final distributables (`.deb`, `.tar.gz`, `.exe`, `.dmg`, `.zip`) from heavy unbundled PyInstaller build trees (`dist/RadioTVSegmenter/`), eliminating manifest payload timeouts during `actions/upload-artifact@v4`.
  - **CI Workflow Resilience**:
    - Added `continue-on-error: true` and direct GitHub Release asset publishing (`softprops/action-gh-release@v2`) across all runner platforms.
    - Hardened `publish-release` job to download artifacts flexibly and generate SHA-256 checksum manifests (`SHA256SUMS`).

## v3.5.1
- **Stable Release — DAW Timeline Interchange & YouTube Chapter Marker Export (`export/daw.py`)**:
  - **Cockos REAPER Project Export (`.rpp`)**:
    - Generates multi-track REAPER project files with full XML-like S-expression syntax (`<REAPER_PROJECT`, `<TRACK`, `<ITEM`, `<SOURCE WAV>`).
    - Translates story segments into precision-aligned timeline items with source sample offsets (`SOFFS`), story titles (`NAME`), non-destructive fade-in/fade-out curves (`FADEIN`, `FADEOUT`), and color-coded project region markers (`MARKER`).
  - **Magix Samplitude EDL (v1.5) Export (`.edl`)**:
    - Generates standard broadcast Edit Decision Lists (v1.5) compatible with Magix Samplitude and Sequoia.
    - Implements millisecond-precision `HH:MM:SS:mmm` timecode formatting (`format_edl_timestamp`) mapping timeline start/end boundaries to project and source tracks.
  - **One-Click YouTube Chapter Marker Clipboard Copy**:
    - Added instant `Ctrl+Shift+Y` shortcut and "Copy Chapters" button to copy zero-based (`00:00 - Introduction`) YouTube chapter markers directly to the system clipboard.
  - **Unified Export Center & Menu Integration**:
    - Integrated DAW export checkboxes in `UnifiedExportDialog` with persistent `QSettings` state.
    - Added dedicated "Export Timeline / DAW" submenu and YouTube chapter actions to the File menu and batch export pipeline.
  - **Diagnostic Test Bench Expansion (`test_runner.py`)**:
    - Added automated unit and fuzz diagnostics for REAPER S-expression generation, Samplitude EDL header/timecode parsing, and chapter marker zero-start enforcement.

## v3.5.0
- **Stable Release — Phase 2 Architecture Modularization & Performance Milestone**:
  - **Comprehensive Monolith Decomposition (`prs_shared.py`)**:
    - Modularized the historic 6,719-line monolith into dedicated, self-contained domain modules, shrinking `prs_shared.py` down to **1,082 lines** (an **84% reduction**).
    - **Background Concurrency Workers (`background_workers.py`)**: Extracted `StoryAutoDetectWorker`, `WaveformWorker`, `VideoThumbnailWorker`, and binary waveform peak cache persistence into `background_workers.py` (~984 lines).
    - **Batch Processing Center (`batch_dialog.py`)**: Extracted `BatchProcessingDialog` and `BatchFileListWidget` drag-and-drop orchestrator into `batch_dialog.py` (~507 lines).
    - **Comments Panel & Editor (`comment_widgets.py`)**: Extracted `CommentEditorDialog`, `NoteEditorDialog`, `CommentCardWidget`, and `CommentsPanel` (~320 lines).
    - **Transcript Editor (`transcript_editor.py`)**: Extracted `InteractiveTranscriptEdit`, `TranscriptSelectionBubble`, `FindReplaceDialog`, and stylesheet definitions (~2,160 lines).
    - **Timeline Widgets (`timeline_widgets.py`)**: Extracted `TimelineCanvas`, `TimelineOverviewBar`, `TimelineWidget`, and `WaveformEnvelope` (~1,831 lines).
    - **Story Manager Widgets (`story_widgets.py`)**: Extracted `StoryListWidget` (~610 lines).
    - **Cache & Storage Layer (`cache_manager.py`)**: Extracted persistent model and thumbnail cache managers (~536 lines).
  - **100% Backward-Compatible Zero-Regression Shims**:
    - Maintained transparent re-exports in `prs_shared.py` ensuring seamless backward compatibility for all internal callers and plugins (`StoryListWidget`, `TimelineWidget`, `InteractiveTranscriptEdit`, `CommentsPanel`, etc.) with zero code breaks.
    - Updated `build_installer.py` with explicit hidden imports for all modularized source modules (`story_widgets`, `timeline_widgets`, `transcript_editor`, `comment_widgets`, `background_workers`, `batch_dialog`, `cache_manager`, etc.) to guarantee zero import failures in frozen PyInstaller Windows releases.
  - **Benchmark Suite Responsive Geometry (`benchmark.py`)**:
    - Screen-aware default dialog sizing (`780x540`, min `640x420`) with persistent `QSettings` dimensions.

## v3.5.0-beta-10
- **Phase 2 prs_shared.py Modularization — Comments Panel & Editor Extraction (`comment_widgets.py`)**:
  - **Extracted Range-Anchored Comment Components**:
    - Extracted `CommentEditorDialog`, `NoteEditorDialog`, `CommentCardWidget`, and `CommentsPanel` (~320 lines) from `prs_shared.py` into a dedicated, self-contained module `comment_widgets.py`.
    - Preserved all rich commenting features: multi-line rich editing with line breaks (`Enter`), quick-save (`Ctrl+Enter`), timestamp range displays, excerpt quoting, seek synchronization, and active visual selection styles.
  - **Zero-Regression Re-Export Shims**:
    - Installed transparent re-export shims in `prs_shared.py`, guaranteeing that `ui_layout.py`, `transcript_story.py`, and all dependent plugins continue accessing comment widgets without changes.
  - **Continued Monolith Footprint Reduction**:
    - Reduced `prs_shared.py` from 2,751 lines down to 2,443 lines (a cumulative ~64% reduction from its original 6,719 lines).

## v3.5.0-beta-9
- **Phase 2 prs_shared.py Modularization — Transcript Editor Extraction (`transcript_editor.py`)**:
  - **Extracted Interactive Transcript Components**:
    - Extracted `InteractiveTranscriptEdit`, `TranscriptSelectionBubble`, `FindReplaceDialog`, and `transcript_text_view_stylesheet` (~2,160 lines) from `prs_shared.py` into a dedicated, self-contained module `transcript_editor.py`.
    - Fully preserved all rich interactive capabilities: word-level audio playback highlighting, speaker attribution context menus, floating quick-action selection bubble toolbar, find-and-replace document operations, and undo/redo stacks.
  - **Zero-Regression Re-Export Shims**:
    - Installed complete re-export shims in `prs_shared.py` ensuring that existing callers (`ui_layout.py`, `playback_preferences.py`, `transcript_story.py`, and plugins) continue accessing all transcript symbols seamlessly.
  - **Substantial Footprint Reduction**:
    - Reduced monolithic `prs_shared.py` from 4,907 lines down to 2,751 lines (a 2,156-line / ~44% reduction this release, and a cumulative ~59% reduction from its original 6,719 lines).
- **Benchmark Suite: Responsive Initial Window Sizing & Size Persistence (`benchmark.py`)**:
  - **Screen-Aware Default Window Size**:
    - Replaced the oversized static `1000x760` window size with a screen-aware default (`780x540`) and a minimum size of `640x420`, ensuring the dialog opens at a well-proportioned size on standard laptops, DPI-scaled displays, and external monitors on first launch without requiring manual resizing.
  - **Persistent Custom Window Geometry**:
    - Added window size persistence via `QSettings` (`benchmark_dialog_width` and `benchmark_dialog_height`) in `closeEvent`, `accept`, and `reject`, automatically remembering any user-adjusted dimensions for future runs.

## v3.5.0-beta-8
- **Phase 2 prs_shared.py Modularization — Timeline Widgets Extraction (`timeline_widgets.py`)**:
  - **Extracted Timeline Components**:
    - Extracted `TimelineCanvas`, `TimelineResizeHandle`, `TimelineOverviewBar`, `TimelineWidget`, `WaveformEnvelope`, and `build_waveform_pyramid` (~1,831 lines) from `prs_shared.py` into a dedicated, self-contained module `timeline_widgets.py`.
    - Moved normalized fade calculation utilities `calculate_fade_curve_factor` and `calculate_fade_out_factor` into `core_utils.py`.
  - **100% Backward-Compatible Re-Export Architecture**:
    - Installed complete re-export shims in `prs_shared.py` so existing modules (`RadioTVSegmenter.py`, `transcript_story.py`, `ui_layout.py`, plugins) continue to access all timeline symbols without modification.
  - **Substantial Footprint Reduction**:
    - Reduced monolithic `prs_shared.py` from 6,719 lines down to 4,907 lines (an 1,812-line / ~27% reduction).

## v3.5.0-beta-7
- **Benchmark Suite: Flexible Rigor & Duration Profiles (`benchmark.py`)**:
  - **4-Tier Workload & Audio Duration Selector**:
    - Replaced the binary quick checkbox with a configurable duration selector matching desired benchmark intensity:
      - *⚡ Quick Spot-Check (1-Min Audio | ~3–5s Evaluation)*: Rapid sanity check with scaled-down workloads.
      - *🎯 Standard Benchmark (5-Min Audio | ~15–25s Run) [Default / Recommended]*: Balanced multi-core evaluation and steady-state hardware rating.
      - *🔥 Sustained Thermal Stress (10-Min Audio | ~45–90s Run)*: Measures multi-core memory bandwidth, sustained boost clocks, and thermal dissipation under continuous stress.
      - *🏔️ Full 30-Minute Broadcast Pass (30-Min Audio | ~2–5m Run)*: Complete end-to-end stress test across the full 30-minute broadcast duration.
  - **Dynamic UI Guidance & Responsive Action Labels**:
    - Added live duration description banner and adaptive button labels that dynamically update based on the selected workload scale.
  - **CLI & Automation Flags**:
    - Added `--quick`, `--standard`, `--sustained`, `--full`, and `--duration=<mode>` command-line arguments with full JSON reporting support.
- **Benchmark Dialog Initialization Fix**:
  - Fixed an initialization sequence bug where `_update_duration_desc()` was invoked before `run_btn` was instantiated, causing `'BenchmarkDialog' object has no attribute 'run_btn'`.
  - Added attribute safety guards (`hasattr`) for `run_btn`, `duration_desc_lbl`, and `duration_combo` to ensure crash-free dialog initialization across all PySide6 environments.

## v3.5.0-beta-6
- **Benchmark Engine: Real 30-Min Audio Source Toggle & Sample Asset Manager (`benchmark.py`)**:
  - **Audio Source Selection & Multi-Source Benchmark Support**:
    - Added user-selectable audio source modes in the Benchmark Dialog and CLI (`--sample`, `--file <path>`):
      - *In-Memory Synthetic RAM Stream*: Zero disk footprint, instant memory-only acoustic speech fixture.
      - *Standard 30-Min Broadcast Sample*: Real-world 32kbps MP3 audio file (~6.9 MB, 29m 58s) testing true FFmpeg decoding throughput and acoustic vocal characteristics.
      - *Custom Media File / Active Timeline Media*: Ability to benchmark directly against any user-selected local audio/video file or active project media.
  - **On-Demand Sample Download & Disk Cleanup Manager**:
    - Added non-blocking asynchronous download thread (`SampleDownloadWorker`) with live percentage progress bar to fetch the 30-minute test audio file from GitHub releases/mirrors.
    - Added instant one-click `Delete Sample` button and CLI `--delete-sample` command to delete the MP3 file and free up ~6.9 MB of disk space whenever desired.
  - **Dual ASR Model Turnaround & Interactive Engine Toggle**:
    - *Parakeet TDT 0.6B (Sherpa-ONNX FastConformer)*: Non-autoregressive acoustic transducer model providing high-throughput speech recognition (~30–45s on 24-core CPUs, ~40x to 70x RTF).
    - *Whisper INT8 / Distil-Whisper (Encoder-Decoder)*: Standard autoregressive sequence-to-sequence transformer model (~2m 15s–2m 30s on 24-core CPUs, ~12x to 15x RTF).
    - Interactive `ASR Engine:` selector dropdown in the Benchmark Dialog and side-by-side reporting across CLI, JSON, and clipboard export.
  - **Installer & Packaging Integration (`build_installer.py`)**:
    - Automatically bundles the `samples/` directory and test audio into application distribution builds if present.

## v3.5.0-beta-5
- **Benchmark Engine: 30-Minute Broadcast Processing Time Estimates (`benchmark.py`)**:
  - **Hardware-Calibrated Time-to-Process (TTP) Engine**: Integrated execution time estimation logic predicting turnaround times for standard 30-minute broadcast audio files based on live subsystem benchmark results:
    - *Story & Boundary Detection*: Estimates peak envelope extraction and multi-core pause analysis duration (~3–6s on modern CPUs).
    - *AI Transcription (Speech-to-Text)*: Estimates INT8 Whisper / Sherpa-ONNX inference turnaround and Real-Time Factor (e.g. ~2m 26s at 12.3x RTF on high-core CPUs).
    - *Speaker Diarization*: Estimates WeSpeaker 256-dimensional voice embedding extraction, pairwise distance matrix calculation, and agglomerative clustering turnaround (~20–80s).
    - *Neural Translation*: Estimates MarianMT / NLLB-200 INT8 sentence translation speed (~15–75s for typical 4,200-word broadcasts) and detects if the translation plugin runtime is installed and active.
    - *Complete Pipeline Turnaround*: Calculates combined end-to-end turnaround time and overall pipeline Real-Time Factor.
  - **PySide6 Graphical Benchmark Dialog & CLI Enhancements**:
    - Added dedicated top status banner card displaying formatted 30-minute processing breakdown and whole-pipeline RTF.
    - Added 30-minute turnaround estimates section to the CLI terminal output, JSON output schema (`--json`), and one-click clipboard summary export.

## v3.5.0-beta-4
- **Phase 2 prs_shared.py Modularization — Step 2: Story Widgets, Cards, & Delegates (`story_widgets.py`)**:
  - **Extracted Story UI & Undo Architecture**: Extracted `StoryCardDelegate`, `StoryListWidget`, `FadeCurveVisualSelector`, `StoryFadesChangeCommand`, `StoryBoundaryChangeCommand`, `SetStoriesCommand`, and `SelectStoriesCommand` from `prs_shared.py` into `/story_widgets.py`.
  - **Zero-Regression Re-Export Shims**: Configured complete symbol re-exports in `prs_shared.py`, maintaining 100% backward compatibility across all dependent modules (`RadioTVSegmenter.py`, `transcript_story.py`, and plugins).
  - **Decoupled Qt Styling & Delegation**: Story list rendering, fade curve selection overlays, selection signals, and undo/redo stacks now operate as a self-contained component.
- **Rigorous Performance & Speed Benchmark Suite (`benchmark.py`)**:
  - **High-Demand Multi-Subsystem Workloads**: Upgraded the benchmark engine to provide rigorous, standardized compute stress tests for cross-hardware performance comparison:
    - *Multi-Tier Waveform Peak & RMS Envelope Extraction*: 6,000 peak bins + RMS power calculation measuring Real-Time Factor (RTF), processing MB/s, and sample bins/second (>110x RTF).
    - *Audio STFT & 80-bin Mel Filterbank Feature Extraction*: 512-point FFT windowing and Mel scale filterbank projection measuring frames/second and acoustic modeling pre-processing speed.
    - *Multi-Core Speech Segmentation (Scaling Test)*: Distributes parallel vocal chunk boundary detections across all logical CPU cores using `ThreadPoolExecutor`, measuring multi-core scaling efficiency and audio minutes processed per second.
    - *Speaker Diarization Vector Clustering*: 256-dimensional embedding vectors with pairwise cosine distance matrix and agglomerative hierarchical centroid clustering (>19,000 comparisons/second).
    - *Deep Project Serialization & Timeline Interval Indexing*: 1,000 story segments with 30,000 word timestamp objects evaluating JSON throughput (MB/s) and binary interval search tree seeking latency.
    - *Transcript Formatting, Token Reflow & Lexical Search*: 35,000 words formatted into speaker-attributed HTML spans with an inverted search index (>300,000 words/second).
    - *Neural Transformer Self-Attention Kernel*: Multi-Head Attention ($Q \times K^T / \sqrt{d_k} \times V$) across 4 heads and 64 dimensions, measuring floating-point GFLOPS.
  - **Composite Hardware Performance Score ("RTVS Hardware Score")**:
    - Introduced a normalized composite benchmark score with subsystem breakdowns (Audio Pipeline, Multi-Core Compute, AI & Diarization, Memory & I/O, UI & Text Engine).
    - Established hardware classification tiers: *Entry / Portable*, *Mid-Range / Mainstream*, *High Performance / Pro*, and *Studio Workstation / Extreme*.
  - **Zero-Disk-Footprint Synthetic Acoustic Fixtures**:
    - Fast RAM-only speech acoustic seed generation with multi-frequency modulation and instant tiling, requiring zero external media files or disk I/O.
  - **PySide6 Graphical Benchmark Dialog Enhancement**:
    - Added Score Card banner with live score and hardware tier, Quick Mode toggle (~3s check vs 10s full suite), real-time progress indicators, and comprehensive clipboard summary export.

## v3.5.0-beta-3
- **Performance & Speed Benchmark Engine (`benchmark.py`)**:
  - **High-Precision Benchmark Harness (`benchmark.py`)**: Built an automated performance profiling suite using `time.perf_counter()` nanosecond resolution and `tracemalloc` memory tracing. Measures pipeline throughput and compute speeds without external media files:
    - *Waveform Peak Extraction*: Synthetic 16kHz PCM audio stream throughput benchmark measuring Real-Time Factor (RTF), processing MB/s, and sample bins/second (>160x RTF).
    - *Project Serialization Fidelity*: High-volume JSON serialization and deserialization throughput testing across hundreds of segmented stories (>25,000 segments/second).
    - *Vocal Energy & Boundary Segmentation*: Acoustic pause detection and boundary partitioning throughput across simulated energy curves (>3,000,000 windows/second).
    - *Transcript Formatting & Token Reflow*: Word-level document rendering, span formatting, and HTML tag generation speed (>1,900,000 words/second).
    - *Neural VAD Chunk Evaluation*: Silero VAD neural chunk evaluation latency with automated fallback to algorithmic energy detection (>2,900 chunks/second).
    - *Speaker Diarization Vector Search*: 256-dimensional embedding clustering and pairwise cosine similarity distance search throughput (>12,000 comparisons/second).
  - **PySide6 Graphical Benchmark Dialog (`create_benchmark_dialog`)**: Designed an interactive desktop dialog featuring real-time status badges, async `QThread` execution, progress indicator, system hardware profile summary, and a one-click clipboard report generator.
  - **Dual CLI & Subprocess Modes**: Supported headless benchmark profiling via `python benchmark.py [--quick] [--json]` and application executable flags (`RadioTVSegmenter.exe --benchmark`, `--bench`).
  - **Help Menu & Keyboard Shortcut Integration**: Added "Run Performance Benchmark..." to the Help menu (`ui_layout.py`) and shortcuts manager (`shortcuts_manager.py`) with default keyboard shortcut `Ctrl+Shift+B` (`Meta+Shift+B` on macOS).
- **In-App Updater & Diagnostic Test Bench Fixes**:
  - **Win32 ShellExecuteW Direct Elevation Launch**: Reworked `launch_and_install` in `updater.py` to use direct Win32 `ShellExecuteW` with `runas` UAC elevation and detached `CREATE_BREAKAWAY_FROM_JOB` subprocess fallback, completely eliminating intermediate `.bat` batch scripts and `cmd.exe` argument quote-mangling that produced Windows `\\` search errors.
  - **Diagnostic Test Bench Module Resolution in Packaged Builds**: Updated subtitle and timeline exporter probes in `test_runner.py` to resolve functions through standard package imports (`from export.subtitles import ...`) with dynamic fallbacks, fixing `FileNotFoundError` path resolution failures on frozen/installed Windows distributions.
- **Phase 2 prs_shared.py Modularization — Step 1 (`cache_manager.py`)**:
  - **Extracted Cache Management Logic**: Extracted disk usage calculation (`get_cache_disk_usage`), cache purging (`purge_caches`), background thumbnail purging (`cleanup_old_thumbnail_cache`), and the interactive `ClearCacheDialog` from `prs_shared.py` into `/cache_manager.py`.
  - **Backward-Compatible Re-Export Shims**: Installed clean re-export shims in `prs_shared.py`, preserving 100% symbol compatibility for all existing callers across `media_batch.py`, `playback_preferences.py`, and `project_export.py`.

## v3.5.0-beta-2
- **System Diagnostic Test Bench & Hardware Health Architecture**:
  - **Comprehensive Multi-Tiered Diagnostic Engine (`test_runner.py`)**: Built an automated zero-dependency diagnostic harness with 20 distinct verification probes covering:
    - *Core Logic & File I/O*: Boundary-case fuzz testing for time parsing and formatting, project serialization round-trip fidelity (.rtvs JSON), binary waveform peak cache (.peaks), and child process lifecycle isolation (`_SUBPROCESS_LOCK`).
    - *Subtitles & Export Formats*: Format verification for SubRip (.srt), WebVTT (.vtt), Red Book CUE sheets (75 fps frame calculation), and YouTube chapter markers (00:00 alignment).
    - *AI Runtimes & Inference Stack*: Health and loadability checks for PyTorch with native C-extensions (`torch._C`), CTranslate2 engine compute types, Sherpa-ONNX / ONNX Runtime execution providers, and DirectML / NVIDIA CUDA hardware acceleration device enumeration.
    - *Model Download & Provisioning*: Remote endpoint latency and reachability verification for Hugging Face Hub and GitHub CDN, model cache storage read/write/delete permissions, and zip/tar archive path-traversal (Zip Slip) security sandboxing.
    - *Story & Boundary Detection*: Vocal energy segmentation boundary calculation and `MUSIC_TOKEN_RE` non-speech token filtering.
    - *Audio Diarization & VAD*: Silero neural VAD initialization checks, WeSpeaker ONNX runtime presence, and translation plugin architecture isolation invariants.
  - **PySide6 Graphical Test Bench (`DiagnosticDialog`)**: Designed a native Qt desktop dialog providing real-time multi-threaded test execution, colored status badges (`PASS`, `FAIL`, `WARNING`, `SKIP`), category trees, progress bars, cancellation support, and a single-click "Copy Report" clipboard tool.
  - **Dual CLI & Subprocess Integration**: Implemented a headless CLI entry point callable via `python test_runner.py`, `--run-diagnostics`, `--test-bench`, or `--test-runner` on the main application executable, enabling automated CI and command-line health checks.
  - **Help Menu & Keyboard Shortcut Integration**: Integrated "Run Diagnostic Test Bench..." into the main application Help menu (`ui_layout.py`) and shortcuts manager (`shortcuts_manager.py`) with default shortcut `Ctrl+Shift+T` (`Meta+Shift+T` on macOS).

## v3.5.0-beta-1
- **Beta Release Channel & Prerelease Updater Architecture**:
  - **Configurable Release Channel (Stable vs. Beta)**: Added update channel configuration support across `core_utils.py`, `prs_shared.py`, `playback_preferences.py`, and `updater.py`. Users can select between "Stable Releases Only (Recommended)" and "Stable & Beta Releases".
  - **Prerelease Filtering in Updater Engine**: Updated `fetch_releases` in `updater.py` to filter out prereleases and tags containing `beta`, `alpha`, `rc`, `dev`, or `preview` when the stable channel is selected. When the beta channel is selected, all published releases (including prereleases) are presented.
  - **Interactive In-Dialog Channel Switching**: Added a dedicated "Release Channel" dropdown selector to `CheckUpdateDialog`, allowing users to immediately switch channels and re-query GitHub releases without needing to reopen application preferences.
  - **Preferences & System Defaults Integration**: Integrated the Update Channel selector into the "Updates & GitHub" preferences page (`playback_preferences.py`), complete with persistence in `QSettings` (`update_channel`), `live_widgets` integration, and restoration support in "Restore System Defaults".
  - **Semantic Versioning for Prereleases**: Enhanced `parse_version_tuple`, `is_version_newer`, and `is_version_older` in `updater.py` to support semantic prerelease comparisons (`(type_rank, build_num)` where stable releases outrank prereleases of the same base version).
  - **CI/CD Prerelease Automation**: Updated `.github/workflows/build.yml` to automatically detect prerelease tags (`-beta`, `-rc`, `-alpha`, `-preview`) and configure `prerelease: true` and `make_latest: false` on GitHub Releases, preventing early beta builds from overwriting the latest stable release pointer.

## v3.4.17
- **Windows Job Object Breakaway & Installer Lifecycle Fix**:
  - **Enabled `JOB_OBJECT_LIMIT_BREAKAWAY_OK`**: In `process_lifecycle.py`, added `JOB_OBJECT_LIMIT_BREAKAWAY_OK` (`0x00000800`) to `info.BasicLimitInformation.LimitFlags` alongside `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. Previously, because the Job Object lacked `JOB_OBJECT_LIMIT_BREAKAWAY_OK`, any child process created with `CREATE_BREAKAWAY_FROM_JOB` failed with `ERROR_ACCESS_DENIED` (WinError 5). This forced the update installer to remain assigned to the parent application's Job Object, which was immediately terminated by Windows (`KILL_ON_JOB_CLOSE`) when the main application exited, causing the installer window to flash and disappear.
  - **Clean Detached Breakaway Launch**: In `updater.py`, configured the update installer launcher to execute via a dedicated temporary launcher script (`.bat`) with `CREATE_BREAKAWAY_FROM_JOB` (`0x01000000`) and `STARTUPINFO.wShowWindow = SW_HIDE`. This avoids Windows `cmd.exe /c` quote-escaping mangling (which previously caused Windows Shell to misparse nested quotes and attempt to execute `\\`), prevents console window flashing, and cleanly breaks away from the Job Object so the Inno Setup installer runs uninterrupted.
  - **Coordinated Exit & Settings Flush**: Replaced the unconditional 0.5s `os._exit(0)` timer with an `aboutToQuit`-coordinated event watcher and explicit `QSettings.sync()` flush. This guarantees that window `closeEvent` handlers, project autosaves, and configuration writes complete before process termination without racing an abrupt hard exit.
- **False-Positive Antivirus Trigger Remediation (Clean Win32 API Launch)**:
  - **Eliminated Mark-of-the-Web (MotW) Stripping**: Completely removed `_unblock_windows_file` (which deleted the NTFS `:Zone.Identifier` Alternate Data Stream and executed PowerShell `Unblock-File`). In modern heuristic and ML-based antivirus engines (including Windows Defender / SmartScreen), modifying `:Zone.Identifier` or unblocking downloaded executables is categorized as security defense evasion (MITRE ATT&CK T1564.004), which caused browsers like Google Chrome and Windows Defender to falsely flag repository download archives (`RTVS3-*.zip`) as infected.
  - **Eliminated PowerShell Scripting**: Removed `powershell.exe -ExecutionPolicy Bypass` commands from the update flow, relying on native `cmd start`, Win32 `ShellExecuteW`, and `os.startfile`.
  - **Graceful Fallback Chain**: Preserved clean fallbacks to `ShellExecuteW` (`"runas"` and `"open"` verbs) and Python's built-in `os.startfile` when elevated execution is cancelled or restricted by local system policy.

## v3.4.16
- **Windows Update Supervisor & Window Visibility Hardening**:
  - **Eliminated Hidden Window Inheritance (`SW_HIDE`)**: Cleared inherited `STARTUPINFO.wShowWindow = SW_HIDE` from Python's detached supervisor launcher (`launch_and_install` in `updater.py`). Passing `wShowWindow = SW_HIDE` to the supervisor caused child processes to inherit the hidden flag, which forced Inno Setup's GUI wizard to momentarily flash and then disappear.
  - **Explicit WindowStyle Normalization**: Configured PowerShell's `Start-Process` with `-WindowStyle Normal`, explicitly instructing Windows to render the installer wizard dialog visibly (`SW_SHOWNORMAL`).
  - **Explicit Working Directory Configuration**: Added `-WorkingDirectory '{escaped_dir}'` to `Start-Process` and `/D "{str(path.parent)}"` to CMD trampoline fallbacks, ensuring the installer executes within its containing folder rather than defaulting to `C:\Windows\System32`.
  - **Persistent Supervisor Execution**: Added `-Wait` to `Start-Process`, ensuring the PowerShell supervisor remains active until the installation finishes rather than exiting prematurely while UAC or Inno Setup is initializing.
  - **Inno Setup Diagnostic Logging**: Enabled `SetupLogging=yes` in `installer/Windows/RadioTVStorySegmenter.iss` to automatically record setup actions to `%TEMP%`.

## v3.4.15
- **Self-Test Diagnostic Resilience & Non-Elevated Output**:
  - **Permission-Safe Diagnostic Output**: Updated `--self-test` in `RadioTVSegmenter.py` to gracefully handle non-writable install directories (`C:\Program Files\Radio & TV Segmenter\`). Diagnostic logs are now printed directly to standard output/console and persisted to writable user locations (`%LOCALAPPDATA%\RadioTVStorySegmenter\ai_self_test.txt` or system temp) instead of throwing an unhandled `PermissionError: [Errno 13]`.
- **Diarization Cancellation Cleanup**:
  - **Graceful Speaker Detection Cancellation**: Added `_diarization_canceled_by_user` state tracking in `cancel_current_process()` (`processing.py`). When a user cancels an active speaker detection run, the process termination signals are caught cleanly, suppressing false-alarm "helper process crashed" and "exited unexpectedly" critical error popups.
- **Windows Installer Launch & UAC Supervisor Hardening**:
  - **Bounded Supervisor Polling with Automatic Fallback**: Enhanced the detached PowerShell installer supervisor in `launch_and_install` (`updater.py`) with a bounded 15-second PID polling ceiling and an automatic elevation fallback (`try { Start-Process -Verb RunAs } catch { Start-Process }`). Ensures that the update installer is reliably launched even if the parent PID drops from process table tracking or Windows UAC encounters permission delays.

## v3.4.14
- **Windows Path Escaping in PowerShell Unblock-File**:
  - **Literal Path Single-Quote Escaping**: Escaped single quotes (`str(path).replace("'", "''")`) when invoking PowerShell's `Unblock-File -LiteralPath` in `_unblock_windows_file` (`updater.py`), ensuring reliable unblocking on systems where user accounts, directory structures, or downloads contain apostrophes.
- **Asynchronous Non-Blocking Single-Instance IPC**:
  - **Non-Blocking Connection Lifecycle**: Migrated IPC connection handling (`_handle_ipc_connection` in `RadioTVSegmenter.py`) from synchronous blocking `waitForReadyRead(1000)` to event-driven `readyRead` and `disconnected` signal listeners.
  - **Socket Retention & Resource Reclamation**: Retained incoming `QLocalSocket` references in `window._pending_ipc_sockets` to protect against premature Python garbage collection during async reading, and attached `deleteLater` upon disconnection to guarantee proper memory cleanup.
- **Timeline Canvas & Scrollbar Synchronization Safeguards**:
  - **Re-entrant Scroll Lock Protection**: Wrapped `self.is_internal_scrollbar_update` modifications in `try...finally` blocks in `TimelineWidget.update_scrollbar_from_canvas` and `update_canvas_from_scrollbar`, preventing scroll update lock freezes during unexpected layout reflows or asynchronous event loops.
- **Thread-Safe Subprocess Teardown & Process Lifecycle**:
  - **Concurrent Subprocess Tracking**: Added a dedicated `threading.Lock()` (`_SUBPROCESS_LOCK`) guarding `_ACTIVE_SUBPROCESSES` mutations and iteration in `runtime_manager.py` (`register_process`, `unregister_process`, and `kill_all_subprocesses`), preventing `RuntimeError: Set changed size during iteration` during multi-threaded cancellations and application shutdown.
- **Codebase Polish & Metadata Cleanup**:
  - **Eliminated Duplicate Initializers**: Cleaned redundant duplicate attribute assignments in `WaveformWorker.__init__` (`prs_shared.py`).
  - **Pruned Dead Code**: Removed obsolete, unreferenced `setup_visual_fade_curve_combo()` helper function in `prs_shared.py`.
  - **Synchronized Header Metadata**: Refreshed legacy application header docstrings in `RadioTVSegmenter.py` and `transcript_story.py` to match the current release version.
- **CI/CD Workflow Hardening**:
  - **Deterministic Static FFmpeg Setup for Windows & macOS**: Replaced the error-prone `FedericoCarboni/setup-ffmpeg@v3` action (which broke with `AssertionError: Cannot get latest release` and `Requested version is not available`) with a reliable, direct PowerShell static binary download from `Tyrrrz/FFmpegBin` (`7.0.2`), matching the proven static binary setup used on macOS and guaranteeing 100% deterministic builds without third-party action lookups.
  - **Resolved Node.js Environment Warnings**: Removed conflicting legacy `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` and `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` environment variables, standardizing runners on Node 24 without configuration warnings.

## v3.4.13
- **Windows Update Supervisor & Application Shutdown Synchronization**:
  - **Hardened PowerShell Supervisor Exit Check**: Upgraded the detached PowerShell PID supervisor loop in `launch_and_install` (`updater.py`) to an explicit `try { Get-Process -Id $pidToWait -ErrorAction Stop } catch { break }` exception handler. Guarantees that the supervisor accurately blocks until the main application process (`RadioTVSegmenter.exe`) has completely terminated before triggering UAC elevation (`Start-Process -Verb RunAs`).
  - **Post-Exit File Lock Settlement Buffer**: Added a 2-second safety sleep (`Start-Sleep -Seconds 2`) after process exit confirmation, ensuring Windows kernel handle cleanup, DLL unloading, and executable file lock releases are 100% complete before launching the update setup binary.
  - **Inno Setup Process Termination Rules**: Configured `CloseApplications=yes` and `CloseApplicationsFilter=*.exe` in the Windows Inno Setup installer specification (`RadioTVStorySegmenter.iss`), ensuring installer runs cleanly signal and wait for active application instances.
- **Installer Cache Retention Policy**:
  - **Multi-Package Retention Window**: Relaxed installer auto-cleanup threshold to `max_to_keep=2` across update checks and post-download tasks, preserving recent downloaded installer packages in `AppData/Local/RadioTVSegmenter/updates` rather than aggressively purging older binaries on every check.

## v3.4.12
- **Zero-Jump Transcript Viewport Stability & Focus Isolation**:
  - **Eliminated Undo-Push Playhead Seek Jump**: Resolved the issue where renaming a speaker or modifying transcript data while a story was selected caused the audio playhead to jump to the start of the selected story (e.g. `09:25.299`). Fixed `ProjectStateCommand.redo()` to bypass redundant re-execution on initial `QUndoStack.push()` and enforced `seek=False` in `_restore_project_state_for_undo()`.
  - **Focus Event Isolation & Cursor Suppression**: Overrode `focusInEvent` in `InteractiveTranscriptEdit` to suppress Qt's default `ensureCursorVisible()` behavior when speaker rename or prompt dialogs close, guaranteeing that focus changes never shift the viewport.
  - **Dynamic Scroll Lock & Range-Changed Pinning**: Introduced `lock_scroll_position()` in `InteractiveTranscriptEdit` which listens to `verticalScrollBar().rangeChanged` and anchors scrollbars to exact pre-action positions while layout reflows settle, automatically releasing upon manual user scroll interaction (mouse wheel, trackpad, or scrollbar dragging).
  - **Dialog Lifecycle Scroll Preservation**: Captured scroll offsets prior to opening `ChangeSpeakerDialog` or `QInputDialog` and preserved them across dialog acceptance, cancellation, and re-rendering lifecycles.

## v3.4.11
- **Strict Transcript Viewport Stability & Auto-Scroll Elimination**:
  - **Complete Elimination of Unsolicited Auto-Scrolling**: Removed automatic viewport scroll mutations from `highlight_word_at_time()` so that transcript word highlighting during playback, audio seek, or transcript refresh never alters the user's scroll position. The transcript viewport now moves strictly upon direct user scroll interaction.
  - **Speaker Label Interaction Decoupling**: Updated speaker label click routing in `transcript_clicked()` to trigger the speaker renaming flow directly without seeking audio or displacing the transcript viewport.
  - **Multi-Pass Scroll Restoration**: Hardened scrollbar position restoration across consecutive Qt document layout cycles (`QTimer.singleShot` stagger) during `render_transcript()` to guarantee zero viewport drift across any number of successive speaker modifications.

## v3.4.10
- **Eliminated Viewport Jumps on Speaker Name Updates**:
  - **Auto-Scroll Decoupling on Transcript Refresh**: Added explicit `auto_scroll=False` parameter to `highlight_word_at_time()` when called during transcript re-rendering (`render_transcript()`), preventing the viewport from auto-scrolling toward distant audio playhead positions when modifying speaker labels.
  - **Zero Viewport Drift**: Guaranteed exact vertical and horizontal scroll position retention across single and all-instance speaker renames, speaker additions, and speaker label deletions while retaining the active word highlight styling.

## v3.4.9
- **Streamlined Change Speaker Dialog Horizontal Layout & Concise Labels**:
  - **Horizontal Button Row Architecture**: Returned to a side-by-side horizontal button layout (`QHBoxLayout`) with generous 480px minimum dialog width and clean equal button stretch factors.
  - **Concise & Direct Action Labels**: Replaced verbose button strings with clean, succinct action labels (`All Instances`, `This Instance Only`, and `Cancel`) that fit comfortably side-by-side without horizontal text clipping or truncation.
  - **Clear Prompt Context**: Centered and formatted the prompt text (`Change 'Current Speaker' to 'New Speaker' for:`) to provide full context without repeating long speaker names inside button labels.

## v3.4.8
- **Preserved Transcript Scroll Position & Playhead Focus on Speaker Changes**:
  - **Viewport Scroll Offset Preservation**: Captured vertical and horizontal scrollbar positions before transcript re-rendering and restored them immediately after HTML rebuilding, preventing the view from jumping back to 0:00 when renaming or reassigning speakers.
  - **Active Playhead Word Re-Highlighting**: Re-triggered `highlight_word_at_time()` with active playback position following speaker updates, ensuring the active word remains highlighted and in focus without resetting scroll position.
  - **Single Instance Rename Correction**: Corrected dialog choice evaluation in `execute_speaker_rename()` for "This Instance Only" renames, avoiding unhandled variable references.

## v3.4.7
- **Resolved Change Speaker Popup Button Text Truncation**:
  - **Dedicated `ChangeSpeakerDialog` Class**: Replaced standard `QMessageBox` with a custom `ChangeSpeakerDialog` to eliminate horizontal button text clipping when renaming or reassigning transcript speakers.
  - **Vertical Action Button Architecture**: Arranged action choices (`All Instances of 'Speaker Name'` and `This Instance Only`) in a vertical stack layout, ensuring buttons have full horizontal dialog width without truncation or horizontal squeeze regardless of speaker name length.
  - **Spacious Dialog Minimum Dimensions**: Enforced a minimum width of 500px with dynamic size adjustment, HTML escaping for special character safety, and explicit segment number display for single-instance renames (`This Instance Only (Segment #X)`).

## v3.4.6
- **WordPress Preferences Options Parity with Export Settings**:
  - **Custom Header / Footer Disclaimer Options in Preferences**: Updated Settings > Preferences > WordPress Connection page to include all optional custom text, disclaimer, placement, and search/excerpt exclusion controls previously available only in the Export window.
  - **Custom Notice & Disclaimer Text Field**: Added a dedicated multiline text edit field in Preferences for defining default custom header/footer disclaimers (e.g., machine-generated transcript notices).
  - **Position & Exclusion Controls**: Added "Place at top of post" vs "Place at bottom of post" placement options, as well as `data-nosnippet` (Google snippet exclusion) and WordPress post excerpt exclusion checkboxes.
  - **Synchronized App Defaults & Cleanup Integration**: Settings saved in WordPress Preferences automatically persist to global application defaults across all direct publishing and export windows, and are fully cleared when running Settings Reset/Cleanup.

## v3.4.5
- **Dynamic Highlight Recoloring & Context-Aware Highlight Menu**:
  - **Highlight Color Changing**: Added support for changing the color of an existing highlight (e.g., changing a yellow highlight to blue, green, pink, orange, or purple) across both Viewing and Editing modes.
  - **Contiguous Region Recoloring**: Selecting a new color for an existing highlight automatically recolors the entire contiguous highlighted section across both the transcript data model and visual display.
  - **Context-Aware Context Menu (`🎨 Change Highlight Color`)**: Right-clicking on an existing highlight dynamically adjusts the right-click menu title to "🎨 Change Highlight Color" and displays a `(Current)` tag next to the active color in the submenu.
  - **Full Undo/Redo Integration**: Highlight color changes are tracked in the project undo history (`Ctrl+Z` / `Ctrl+Y`), allowing instant rollback and re-application.

## v3.4.4
- **Spanish-Only Transcript Editing & Single-Language Editing Workflows**:
  - **Spanish Translation Text Editing**: Full inline text editing and formatting is now supported when viewing in `Español (Translation)` mode, enabling editing and corrections of translated transcripts directly with real-time segment synchronization and undo/redo history tracking.
  - **Bilingual (Split View) Editing Guard & Clear Tooltip**: The `Edit Transcript` button and menu actions are gracefully disabled with grayed-out styling when in `Bilingual (Split View)` mode, presenting an explanatory tooltip: *"Editing is only available in single-language views (English or Español)."*
- **Transcript Header Toolbar De-Cluttering & Consolidation**:
  - **Single Consolidated Font Size Dropdown**: Replaced the separate three-button font scaling group (`A−`, `A`, `A+`) with a streamlined `QComboBox` font size selector (80%–180%) that stays synchronized with global keyboard shortcuts (`Ctrl++`, `Ctrl+-`, `Ctrl+0`).
  - **Eliminated Redundant Toolbar Translate Button**: Removed the standalone `Translate...` button from the transcript header bar since full translation commands and workflows are accessible via the top-level `Tools` menu and shortcuts.
  - **Consolidated Single Transcript Highlighter**: Removed the duplicate highlighter tool button from the editing formatting toolbar so that the persistent 6-color `Highlight ▾` button in the header toolbar acts as the unified highlighting control across both View and Edit modes.

## v3.4.3
- **Transcript Edit Mode Auto-Switch & Language Selection Unblocking**:
  - **Auto-Switch to English on Edit Mode Trigger**: Clicking `Edit Transcript`, pressing `F2`, or toggling `Edit Transcript Mode` from the View menu while viewing Spanish or Bilingual (Split) translations now automatically switches the display to `English (Original)` and activates text editing mode seamlessly, with an informative status bar notification.
  - **Always-Enabled Edit Mode Button**: The `Edit Transcript` toolbar button is no longer grayed out or locked when translations are displayed, allowing instant one-click transition into editing.
  - **Persistent Language Selector for Translated Projects**: The `transcript_language_selector` dropdown remains visible and interactive whenever a project contains translation data or active translation display modes, even if the translation generation plugin is currently disabled.
  - **View > Transcript > Language Display Menu**: Added a dedicated `Language Display` submenu to `View -> Transcript` allowing users to switch between `English (Original)`, `Español (Translation)`, and `Bilingual (Split View)` directly from the application menu bar.
  - **Application-Level F2 Shortcut Context**: Set `ApplicationShortcut` context on `transcript_edit_mode_action` ensuring `F2` reliably toggles edit mode from anywhere in the window.

## v3.4.2
- **Persistent 6-Color Transcript Highlighter & Independent Viewing Mode Access**:
  - **Header Toolbar 6-Color Highlighter**: Added a dedicated, persistent 6-color `Highlight ▾` popup menu tool button (`Yellow`, `Green`, `Blue/Cyan`, `Pink`, `Orange`, `Purple`, and `Remove Highlight`) to the transcript search header bar, making highlighting directly accessible during viewing and playback without needing to toggle edit mode.
  - **Context Menu Integration**: Added the 6-color highlight submenu and "Remove Highlight" action to the right-click context menu in both Viewing Mode and Editing Mode.
  - **Keyboard Shortcut (`Ctrl+Shift+H`)**: Streamlined `Ctrl+Shift+H` to apply the active highlight color to selected text in both Viewing and Editing modes without interfering with playback controls.
  - **Audio Playback Safety**: Preserved strict separation between text selection/highlighting and timeline playback controls. Spacebar continues to control playback in Viewing mode while allowing normal text input in Editing mode.
- **Transcript Edit Mode Responsiveness & Interaction Flags Fix**:
  - **Interaction Flags Synchronization**: Restored full text editor interaction flags (`TextEditorInteraction`) and proper widget focus in `InteractiveTranscriptEdit.set_editing_mode(True)`, allowing immediate cursor placement and text editing upon entering edit mode.
  - **Signal Argument Robustness**: Updated `toggle_transcript_editing_mode()` to safely accept arbitrary signal arguments from UI buttons and actions.
  - **Translation Guard Feedback**: Ensured clean status bar notifications informing users that text editing is exclusive to the English (Original) view if toggled while translation view is active.

## v3.4.1
- **Transcript Comment Highlights, Floating Hover Previews & Non-Playing Navigation**:
  - **Persistent Highlight Spans**: Sections of the transcript with attached comments now retain their visible background highlights even when the comment sidebar is collapsed or closed.
  - **Interactive Floating Hover Tooltip (`QToolTip`)**: Hovering over any highlighted transcript section displays an instant, styled floating tooltip showing the author and comment text, automatically disappearing when the mouse leaves the highlighted span.
  - **Click-to-Seek Without Auto-Play**: Clicking on a highlighted section in the transcript navigates playback position and centers the timeline without automatically starting audio playback, keeping the audio paused until the user hits Play or Spacebar.
  - **Seamless Panel Activation**: Clicking on a highlighted comment span automatically opens and focuses the comment panel/sidebar if it was closed.
  - **Global "Show Comment Highlights" Toggle**: Added toggle controls to both the View menu and Transcript menu (`Ctrl+Shift+H` / `F9`), allowing users to toggle visual comment highlights across the entire transcript while preserving underlying comment metadata.
  - **Configurable Startup & Highlight Defaults**: Added new General preferences under Settings > Preferences:
    - *Open Comments sidebar on startup*: Defaulted to `False` (closed on launch unless explicitly saved by user preference).
    - *Show Comment highlights in transcript*: Defaulted to `True` (active highlights rendered in transcript).
  - **Document Export Controls (DOCX & PDF Highlights Toggle)**: Added dedicated "Include Comment Highlights" checkboxes to both `ExportDialog` (`export/dialog.py`) and `TranscriptStoryExportDialog` (`prs_shared.py`), empowering users to include or omit visual highlight backgrounds in exported Word (.docx) documents and PDF files alongside native comments and margin annotations.
- **Visual Audio Fade Curve Profiles & Attenuation Inversion Bugfix**:
  - **Fixed Fade-Out Curve Inversion**: Corrected a bug where choosing the Logarithmic fade curve applied an Exponential attenuation curve on fade-out and vice versa. Implemented `calculate_fade_out_factor(u, fcurve)` in `prs_shared.py` to ensure auditory attenuation precisely matches the visual envelope preview for all curve types.
  - **High-DPI Graphical Curve Previews**: Replaced purely text descriptions of fade curve profiles with dynamic antialiased graphical curve previews across the application:
    - Dynamic curve rendering engine in `prs_shared.py` (`create_fade_curve_pixmap()` and `create_fade_curve_icon()`).
    - Interactive `FadeCurveVisualSelector` card buttons in Settings > Preferences > Playback & Timeline.
    - Upgraded "Audio Fades" -> "Set Fade Curve Profile" context sub-menu with crisp curve icons and profile checkmarks.
    - Integrated `FadeCurveVisualSelector` into the per-story `StoryFadesDialog`.
- **Phase 1 Modularization of `prs_shared.py` Monolith**:
  - Successfully extracted pure-Python, non-UI functionality into 4 dedicated modules (`core_utils.py`, `transcript_cleaner.py`, `project_serialization.py`, `process_lifecycle.py`), reducing `prs_shared.py` by over 700 lines with full backward-compatibility re-exports.

## v3.3.29
- **Cleaned Up Duplicate `StoryListWidget` Class in `prs_shared.py`**:
  - Removed obsolete ~70-line legacy `StoryListWidget` implementation sitting earlier in `prs_shared.py` (line 1546).
  - Eliminated shadow class pollution, leaving the canonical, feature-complete implementation with `filesDropped` signal and drag-drop support as the sole `StoryListWidget` definition.

## v3.3.28
- **Hardened YouTube Video Frame Capture Against Subprocess Hangs**:
  - Added a strict 30-second execution timeout (`timeout=30`) and `subprocess.TimeoutExpired` exception handling to `capture_video_frame()` in both `plugins/youtube/export_destination.py` and `plugins/youtube/plugin.py`.
  - Prevents FFmpeg from hanging or blocking the application indefinitely when encountering corrupt or pathological video inputs during YouTube thumbnail frame extraction.
  - Bumped `plugins/youtube/manifest.json` version to `3.3.28` under the plugin catch-up synchronization policy.

## v3.3.27
- **Resolved Bilingual Transcript Display Crash (`NameError: seg_indices`)**:
  - Fixed a UI rendering crash where the translation payload would successfully complete, but the text renderer would fail to display the Spanish or bilingual text due to a missing mapping reference (`seg_indices`).
  - The UI now successfully maps the translated segments back into the transcript viewer paragraph blocks, restoring bilingual mode functionality.

## v3.3.26
- **Fixed Silent Subprocess Payload Drop via Unicode Encode Failure (The True 100% Hang Fix)**:
  - Discovered that on Windows, \`sys.stdout.write\` defaults to the active OEM code page (typically \`cp1252\`) instead of UTF-8.
  - When the final JSON payload containing the translated text or speaker boundaries included unencodable characters (e.g. Spanish accents, emojis, or Unicode formatting), \`sys.stdout.write\` threw a hidden \`UnicodeEncodeError\`.
  - The internal signal emitter silently caught and swallowed the error, allowing the subprocess to cleanly exit with code 0 without ever delivering the final result to the UI.
  - Completely rewrote all subprocess IPC emit pipelines to aggressively write raw UTF-8 bytes to \`sys.stdout.buffer\`, definitively unblocking the "100% Complete" stall on Windows without data loss.

## v3.3.25
- **Fixed QProcess Stdout Pipe Truncation on Subprocess Exit**:
  - Fixed a critical bug in `translation.py` and `processing.py` where the final JSON payload emitted by background helpers could be permanently lost if the string was not followed by a final trailing newline when read from the pipe after the process exited.
  - Enforced a strict buffer flush (`force_flush=True`) during process cleanup that artificially guarantees any leftover JSON strings in the buffer are correctly flushed, parsed, and routed to the UI before cleanup.
  - This definitively resolves the "Translation complete. (100%)" hang and similar unresponsiveness during Diarization crashes/completions.

## v3.3.24
- **Resolved Translation Process Sticking at 100%**:
  - Identified and fixed a QProcess race condition in `translation.py`. When the translation subprocess completes and exits, the final `"finished"` JSON message containing the translated transcript payload was sometimes left unread in the stdout buffer because the finished callback did not drain remaining standard output.
  - Added an explicit `read_output()` call at the start of the `finished` slot in `translation.py`. This ensures all remaining standard output buffer data is fully read and parsed before the process object is unregistered and cleaned up, allowing translation to complete instantly and gracefully.
- **Enhanced Speaker Detection Progress Transparency & Detail**:
  - Swapped the hardcoded static progress status text ("Speaker Detection") with the dynamic subprocess message in `processing.py`.
  - The progress bar and status labels now display detailed status (e.g. "Clustering speaker signatures (AHC O(N^2) - 00m 46s elapsed)...") rather than a generic placeholder, letting the user know exactly what active background work is being performed.

## v3.3.23
- **Fixed Translation Environment Dependency Missing PyTorch (`torch`)**:
  - Discovered that the translation plugin's isolated virtual environment setup reads from `plugins/translation/requirements-runtime.txt` instead of falling back to core configuration, meaning PyTorch was completely omitted from pip installations.
  - Added `torch>=2.4.1` to the translation plugin's `requirements-runtime.txt` file, ensuring the CPU PyTorch wheel is properly installed during virtual environment creation.
  - Bumped the core translation configuration version to `2.14` to force a complete self-healing reconstruction of the environment for all users.
  - Resolves `OPUS-MT translation requires the CTranslate2 translation engine. Details: name 'torch' is not defined` when loading translation engines on CPU/Ryzen systems.
- **Prevented Main UI Thread Freeze during Speaker Detection on Long Files**:
  - Implemented an elegant rate-limiter for activity logging of diarization progress updates in `processing.py`.
  - Previously, logging every minor speaker detection progress update (thousands of ticks on long audio files) forced deep-cloning of all stories and undo/redo history state snapshots, locking up the Qt UI thread.
  - Progress ticks are now logged at most once every 3.0 seconds, preserving normal responsive UI feedback and preventing "Not Responding" application freezes on long recordings.

## v3.3.22
- **Fully Bypassed Redundant CPU PyTorch Environment Pruning**:
  - Configured `prune_cuda_artifacts` in `runtime_manager.py` to be a safe NO-OP for CPU configurations, preventing any recursive file deletions or folder pruning from corrupting PyTorch on Windows.
  - While pruning CUDA was originally helpful to clean up giant GPU wheel downloads, both the translation (`translate`) and diarization (`diarize`) environments are already configured with official, lightweight CPU PyTorch wheels (`https://download.pytorch.org/whl/cpu`) that contain no CUDA binaries and are extremely compact (~200MB) by default.
  - Eliminates `ImportError: cannot import name 'nn' from partially initialized module 'torch'` and related import crashes across AMD Ryzen and standard CPU systems.
  - Bumped virtual environment versions for both `diarize` (`1.2.5`) and `translate` (`2.13`) to trigger a fresh, self-healing reconstruction of both environments on users' systems, fully restoring functional, official PyTorch CPU environments.

## v3.3.21
- **Restored Crucial Windows PyTorch DLL Binaries folder (`torch/bin`)**:
  - Preserved `"torch/bin"` in the `prune_cuda_artifacts` footprint optimization exclusion list in `runtime_manager.py`.
  - Fixed `ImportError: cannot import name 'nn' from partially initialized module 'torch'` during diarization and translation engine loading on Windows machines.
  - Windows compiled `.dll` shared libraries are located inside `"torch/bin"`, so deleting this folder broke the entire PyTorch library's compiled C++ backends.
  - Bumped virtual environment spec versions for `diarize` (v1.2.4) and `translate` (v2.12) to force complete self-healing clean rebuilds of both environments on users' systems, fully restoring functional DLL binaries.

## v3.3.20
- **Diarization & Translation PyTorch Distributed Dependency Preservation**:
  - Excluded `torch/distributed` from the `prune_cuda_artifacts` pruning list in `runtime_manager.py`.
  - Fixes `ModuleNotFoundError: No module named 'torch.distributed'` which aborted speaker diarization and translation engine loading on Windows, especially on AMD Ryzen and standard CPU systems.
  - Bumped virtual environment versions for both `diarize` (v1.2.3) and `translate` (v2.11), triggering automated virtual environment rebuilding to safely restore missing files on user systems.
  - Removed speculative `intel-openmp` package requirements to keep CPU runtimes lean and cross-compatible with AMD Ryzen and Intel platforms alike.
- **Robust Subprocess Translation Error Handling**:
  - Added an explicit `error` type message handler to `translation.py` standard output stream parser.
  - Ensures local translation exceptions are captured and propagated as standard `QMessageBox` critical error dialogs rather than leaving the UI progress bar stuck indefinitely at 7%.

## v3.3.19
- **Runtime DLL Dependency & OpenMP Alignment**:
  - Investigated dependencies for the isolated `diarize` and `translate` CPU environments.
  - Aligned project version to v3.3.19 across core modules.

## v3.3.18
- **Runtime Resiliency & ABI Compatibility**:
  - Upgraded PyTorch CPU constraint to `torch>=2.4.1` in `runtime_manager.py` to support Python 3.12 ABI compatibility.
  - Patched `translation.py` `QProcess` cancellation logic to guarantee progress bar clearing and error exposure on silent or empty-stderr crashes.

## v3.3.15
- **RuntimeManager Class Definition Structural Fix**:
  - Un-indented the `_remove_macos_quarantine` helper function in `runtime_manager.py` that had incorrectly split the `RuntimeManager` class block.
  - Resolved `AttributeError: 'RuntimeManager' object has no attribute 'ensure_environment'` during environment provisioning, restoring fully automated AI worker setup.

## v3.3.14
- **RuntimeSetupWorker Threading Module Import Fix**:
  - Imported missing `threading` module in `processing.py`, resolving `NameError: name 'threading' is not defined` when initializing `RuntimeSetupWorker`.
  - Fixes stuck modal setup dialogs during transcription and speaker diarization worker initialization.

## v3.3.13
- **QCoreApplication Symbol Import & Clean Exit Fix**:
  - Imported `QCoreApplication` from `PySide6.QtCore` in `prs_shared.py`, resolving the `NameError: name 'QCoreApplication' is not defined` traceback when closing the application (`MainWindow.closeEvent`).
  - Confirmed that Windows Media Foundation codec messages (`[h264_mf]`, `[hevc_mf]`) are normal operating system notifications emitted during hardware video encoder teardown.

## v3.3.12
- **QPainterPath Symbol Fix & Canvas Error Resolution**:
  - Imported `QPainterPath` from `PySide6.QtGui` in `prs_shared.py`, resolving the `NameError: name 'QPainterPath' is not defined` exception that flooded the console and aborted `TimelineCanvas.paintEvent`.
  - Restored full visual rendering of audio fade ramps (blue fade-in slope & rose fade-out slope) and tactile grab handles on the timeline canvas.

## v3.3.11
- **Magnetic Snapping Disabling & Audio Fade Handle Visibility Restoration**:
  - Disabled default magnetic snapping in `TimelineCanvas` (`prs_shared.py`), restoring fluid, unconstrained 60 FPS story border dragging and edge adjustment.
  - Made tactile fade-in (blue) and fade-out (rose) drag handles ALWAYS visible along the top edge of every story block when audio fades are enabled, even when `fade_in` or `fade_out` is currently `0.0s`.
  - Expanded hit-testing threshold (`FADE_HANDLE_THRESHOLD = 12`) and vertical bounds for fade handles, allowing seamless grab-and-drag for both left and right mouse buttons to create audio fades directly on the timeline canvas.
  - Ensured right-clicking story blocks reliably opens the timeline context menu with "Set Audio Fades..." and story management actions.

## v3.3.10
- **ThemeTokens `story_segment_color` Restoration & Exception-Safe QPainter Painting**:
  - Added missing `story_segment_color(index, is_selected, alpha)` method to `ThemeTokens` (`theme_tokens.py`), fixing `AttributeError` during timeline overview rendering.
  - Wrapped `TimelineOverviewWidget.paintEvent` in exception-safe `try...finally: painter.end()` blocks to prevent unclosed `QPainter` instances from corrupting `QBackingStore` and crashing the application on window resize, minimize, or restore.

## v3.3.9
- **Native DWM Window Subclassing Elimination & Minimize/Resize Stability**:
  - Replaced `pywinstyles` HWND subclassing with native Windows 10/11 DWM title bar attribute (`DwmSetWindowAttribute`), preventing client area coordinate offsets and backing store crashes during minimize, restore, and resize actions.
  - Added `not self.isMinimized()` state guard in `MainWindow.changeEvent` to prevent paint engine calls while minimized.

## v3.3.8
- **Window Maximization & Window State Change Stability Fix**:
  - Replaced native Windows `pywinstyles.apply_style("mica")` DWM hook with safe dark theme styling to prevent crashes on window maximize.
  - Added `changeEvent` handler on `MainWindow` to gracefully respond to `WindowStateChange` events (maximize, restore, minimize).
  - Added `painter.isActive()` guard assertions to `TimelineCanvas` rendering routines to prevent native QPainter crashes on window resizing.

## v3.3.7
- **Story List Native File Drag-and-Drop Restoration**:
  - Added `filesDropped = Signal(list)` signal definition and drag event overrides (`dragEnterEvent`, `dragMoveEvent`, `dropEvent`) to `StoryListWidget`.
  - Connected `self.story_list.filesDropped` in `ui_layout.py` to seamlessly handle dropping audio or video media files directly onto the stories panel.

## v3.3.6
- **Story List Signal Architecture Restoration & Keyboard Shortcut Support**:
  - Restored missing `deleteRequested`, `exportRequested`, and `exportStoryWordPressRequested` PySignal attributes on `StoryListWidget`.
  - Added native key press handling (`keyPressEvent`) for `Delete` and `Backspace` keys on `StoryListWidget` items to emit `deleteRequested` signal for story deletion.
  - Resolved `AttributeError: 'StoryListWidget' object has no attribute 'deleteRequested'` crash on Windows application startup.

## v3.3.5
- **Asynchronous PowerShell Process Supervisor for Windows Updates**:
  - Fixed an issue where the Windows Check for Updates feature triggered the UAC elevation prompt before the application closed, causing Windows UAC to drop the installer launch token when the parent process exited prematurely.
  - Implemented a detached PowerShell supervisor process in `launch_and_install` that monitors the main application process ID (`Get-Process -Id $pidToWait`) to ensure the application completely closes and releases all file locks BEFORE triggering the UAC dialog.
  - Kept the supervisor process active during user interaction with UAC (`Start-Process -Verb RunAs`), guaranteeing seamless elevation and execution of the installer.

## v3.3.4
- **Non-Linear Audio Fade Envelope Curves & Custom Gain Profiles**:
  - Implemented selectable audio fade curve profiles: **Linear Ramp**, **Cosine S-Curve** ($0.5 \cdot (1 - \cos(\pi \cdot u))$), **Logarithmic** ($\log_{10}(1 + 9u)$), and **Exponential** ($(10^u - 1)/9$).
  - Fully supported across real-time playback gain modulation (`get_fade_volume_factor_at_time`), interactive 16-step vector curve drawing on `TimelineCanvas`, global default setting in Preferences -> *"Playback & Timeline"*, and story JSON project serialization (`fade_curve` field).
- **Magnetic Timeline Snapping Engine**:
  - Added magnetic snapping on `TimelineCanvas` (`snap_time()`) that magnetically snaps cursor drags during selection range adjustments, playhead scrubbing, story edge trimming, and audio fade handle dragging.
  - Snaps to nearby story start/end boundaries, playhead location, and selection region anchors within a 10-pixel threshold (`enable_magnetic_snapping`).
- **Story List Right-Click Context Menu & Batch Audio Fade Controls**:
  - Created `StoryListWidget` custom right-click context menu with dedicated **Audio Fades** sub-menu enabling one-click auditioning, batch fade application (`apply_fades_to_selected_stories`), batch fade removal (`remove_fades_from_selected_stories`), and quick fade curve profile selection across selected stories.
  - Expanded `StoryFadesDialog` to configure fade curve profile per story or project-wide, and added rich status tooltips and badges (`[In:0.5s Out:1.0s]`) to story list items.

## v3.3.3
- **Timeline Fades Optional by Default on New Installs**:
  - Configured `enable_audio_fades` and `preview_audio_fades` to default to `False` across all application initialization paths, QSettings fallbacks, and the "Restore Defaults" preferences routine.
  - New installations will keep timeline fades cleanly disabled until explicitly enabled by the user in Preferences -> *"Playback & Timeline"*, preserving maximum interface responsiveness and visual simplicity.
  - Existing user configurations that have already enabled or disabled the feature are respected and preserved across sessions.
- **Audio Output Volume Throttling & Playback Performance Optimization**:
  - Eliminated high-frequency redundant `setVolume()` calls into the system audio daemon during playback by tracking `_last_applied_fade_vol` and only applying gain changes when volume shifts by `>= 0.005`.
  - Adjusted real-time fade preview timer interval to 35ms (~28 FPS), significantly reducing CPU overhead while maintaining smooth, artifact-free audio crossfades.
  - Automatically suspends fade timers and restores full master volume when playback pauses or reaches the end of an auditioned story segment.
- **Timeline Canvas Tooltip Storm & Mouse Lag Elimination**:
  - Fixed an issue where millisecond-precision timestamp recalculations caused `QToolTip.showText()` to fire continuously (up to 100 times per second) during any cursor movement across the timeline.
  - Isolated timeline tooltips strictly to interactive hover targets (story edge boundaries and tactile fade envelope grab handles), automatically hiding tooltips during free scrubbing and panning for seamless 60+ FPS cursor response.
  - Cached boundary and fade hit-test lookups within `mouseMoveEvent` to prevent redundant coordinate recalculations.
- **Optimized Fade Overlay & Ramp Vector Painting**:
  - Replaced computationally intensive antialiased dashed line calculations (`DashLine`) in `paintEvent` with crisp, high-performance solid 1.2px vector ramp strokes.
  - Clamped polygon vertex arrays strictly to viewport bounds to minimize rasterization overhead.

## v3.3.2
- **Playback & Timeline Preferences Reorganization & Dynamic Visibility**:
  - Moved *"Default Story Fade-In"* and *"Default Story Fade-Out"* numeric controls from the Detection settings pane to Preferences -> *"Playback & Timeline"* directly below the Audio Fades section.
  - Implemented dynamic visibility grouping: *"Fade Audio Preview"* and the default fade duration controls are now conditionally displayed only when *"Enable story audio fades and timeline envelope handles"* is checked.
- **Active Cursor-Anchored Timeline Zooming**:
  - Updated `TimelineCanvas.set_zoom()` and all zoom triggers (`+`, `-`, `=`, and vertical mouse wheel) to anchor zoom transformations strictly at the active cursor/playhead position (`position`).
  - Clicking anywhere on the timeline immediately locks the active focus point so zooming in and out remains centered on that exact timestamp.
- **Multi-Axis Horizontal Scrolling & Trackpad Navigation**:
  - Added native horizontal scroll support in `TimelineCanvas.wheelEvent()` for dedicated horizontal scroll wheels, tilted scroll wheels, two-finger horizontal trackpad swipe gestures, and `Shift`+vertical wheel panning.
- **Interactive Overview Navigation Pill & Edge Drag-to-Zoom**:
  - Replaced the standard horizontal scrollbar with `TimelineOverviewBar`, a taller (16px) interactive overview strip featuring full-duration mini story segments and an active viewport pill.
  - Implemented tactile left and right edge grab handles allowing users to zoom in and out by clicking and dragging either edge of the navigation pill.
  - Supports click-to-jump navigation and smooth dragging across the media file with real-time cursor feedback and tooltips.

## v3.3.1
- **Real-Time Audio Fade Playback Preview & Auditioning System**:
  - Implemented real-time volume gain modulation during audio playback (`get_fade_volume_factor_at_time(t)` and `update_realtime_fade_volume()`) that tracks story fade-in and fade-out envelope curves in 25ms timer intervals (`fade_preview_timer`), modulating `QAudioOutput` gain dynamically.
  - Automatically restores master playback volume (`master_volume`) seamlessly upon pause, stop, or leaving fade envelope boundaries.
  - Added *"Audition Story (With Fades ▶)"* (`audition_story`) to the story list right-click context menu, enabling one-click auditioning of story clips from start to finish with fade envelope gain curves applied and automatic stop at story completion.
- **Windows In-App Updater & Installer Launch Hardening**:
  - Implemented automatic Mark-of-the-Web removal (`_unblock_windows_file`) stripping the NTFS `Zone.Identifier` alternate data stream and executing PowerShell `Unblock-File` so Windows Defender SmartScreen does not silently block downloaded update packages.
  - Upgraded Windows installer execution to an asynchronous decoupled shell trampoline (`cmd.exe /c timeout /t 1 /nobreak >nul & start "" "installer.exe"` with `DETACHED_PROCESS` and `CREATE_BREAKAWAY_FROM_JOB`), giving Python 1 second to cleanly exit and release binary locks before setup launches.
  - Added primary and secondary fallback execution paths via Windows `ShellExecuteW` with explicit `"runas"` administrative verb (attaching parent window handle `hwnd` for native UAC elevation dialogs) and `os.startfile`.
  - Updated in-app updater action button to *"Restart & Install"* with clear confirmation messaging explaining that the application will close and hand off to the setup wizard.
- **Playback & Timeline Preferences for Audio Fades**:
  - Added user toggles in Preferences -> *"Playback & Timeline"*:
    - *"Enable story audio fades and timeline envelope handles"* (`enable_audio_fades`, persisted across sessions in `QSettings`).
    - *"Preview audio fades in real-time during playback"* (`preview_audio_fades`, persisted across sessions in `QSettings`).
  - Seamlessly toggles timeline envelope grab handles, dark gain masks, and diagonal dashed ramp overlays on the canvas.
  - Honors `enable_audio_fades` across timeline rendering, hit-testing, story delegate metadata display (`Fades: X.Xs / Y.Ys`), and the export pipeline in `project_export.py`.
- **Timeline Canvas Performance & Tooltip Optimization**:
  - Enhanced canvas hit-testing and envelope painting with horizontal bounding box culling (`end_x < -16 or start_x > width + 16`) to skip offscreen stories during zoom and pan.
  - Debounced mouseMove hover tooltips on the timeline canvas to eliminate redundant OS tooltip redraw events during playback and scrubbing.

## v3.3.0
- **Story Audio Fade-In & Fade-Out Envelope Architecture**:
  - Extended the core `Story` data model with native `fade_in` and `fade_out` duration attributes, fully serialized into JSON project files and `.rtvs` archives with backwards-compatible migration.
  - Newly detected or manually created stories automatically inherit default fade settings from application preferences (default: 0.0s fade-in, 1.0s fade-out).
  - Added `StoryDelegate` rendering support displaying active fade durations (`Fades: X.Xs / Y.Ys`) directly in the story list sidebar.
- **Interactive Timeline Fade Ramps & Tactile Envelope Handles**:
  - Rendered audio gain envelopes directly on the timeline waveform canvas with semi-transparent gain masks and high-contrast diagonal ramp indicators (cyan for fade-in, rose for fade-out).
  - Added tactile envelope grab handles along the top edge of story blocks allowing direct horizontal drag-and-drop adjustment of fade durations with real-time cursor feedback and precision tooltips.
  - Integrated with `QUndoStack` through `StoryFadesChangeCommand` for discrete, non-destructive undo/redo of fade adjustments.
- **Story Fades Dialog & Context Menu Integration**:
  - Added *"Set Audio Fades..."* to both the timeline right-click context menu and the story list context menu.
  - Implemented `StoryFadesDialog` with precision decimal spinboxes, story duration clamps, quick presets (*"No Fades (0s)"* and *"Restore Defaults"*), and an option to apply settings project-wide.
- **Global Preferences & Detection Settings**:
  - Added *"Default Story Fade-In"* and *"Default Story Fade-Out"* numeric controls to the Detection settings pane in `playback_preferences.py`, persisted across sessions in `QSettings`.
- **Export Pipeline & FFmpeg Audio Filter Processing**:
  - Integrated FFmpeg audio filter chains (`afade=t=in:ss=0:d=...` and `afade=t=out:st=...:d=...`) into `extract_media()` in `project_export.py`.
  - Added an *"Apply audio fade-in & fade-out"* toggle option to the Unified Export Dialog (`export/dialog.py`), remembering user preferences.
  - Implemented intelligent video stream-copying (`-c:v copy`) when exporting video stories, re-encoding only the audio stream with fade filters to preserve visual quality and export speed.

## v3.2.20
- **macOS System CLI Tool & Homebrew PATH Environment Integration**:
  - Implemented `setup_macos_path_environment()` in `bootstrap.py` and `radio_tv_story_segmenter_worker.py` to ensure standard macOS tool directories (`/opt/homebrew/bin`, `/opt/homebrew/sbin`, `/usr/local/bin`, `/usr/local/sbin`, `~/.local/bin`, `~/.cargo/bin`) are present in `os.environ["PATH"]`.
  - Applications launched from macOS Finder / Dock / Spotlight run under `launchd` with a stripped-down `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`), which previously made Homebrew-installed `ffmpeg`, `ffprobe`, `python3`, and `uv` invisible.
  - Enhanced `find_bundled_executable()` in `prs_shared.py` to directly search Homebrew and standard macOS bin directories if not found on `PATH`.
- **Robust SSL Context Factory (Keyword Argument Handling)**:
  - Fixed a critical `TypeError: <lambda>() got an unexpected keyword argument 'purpose'` bug in `bootstrap.py` and `plugins/translation/support.py` where `ssl._create_default_https_context` was previously assigned a 0-argument lambda. Replaced with a flexible context factory accepting all keyword arguments (`purpose`, `cafile`, `capath`, `cadata`), ensuring downstream libraries (`requests`, `urllib3`, `pip`, `huggingface_hub`) never crash during SSL handshakes.
- **Worker Subprocess Environment Hardening & OpenMP Safety**:
  - Enhanced `_apply_worker_env_overrides()` in `processing.py` and `_launch_translation_process()` in `translation.py` to automatically propagate `KMP_DUPLICATE_LIB_OK`, `TOKENIZERS_PARALLELISM`, `HF_HUB_DISABLE_SYMLINKS_WARNING`, SSL certificate bundles, and Homebrew `PATH` into `QProcessEnvironment` across all worker subprocesses.
- **WeSpeaker Dependency & Gatekeeper Quarantine Clearance**:
  - Added `"wespeakerruntime>=1.0.0,<2.0.0"` to `ENV_CONFIGS["diarize"]["packages"]` in `runtime_manager.py` to ensure fresh diarization environments automatically install the required ONNX voice embedding engine.
  - Added recursive Gatekeeper quarantine removal (`_remove_macos_quarantine(env_dir)`) upon isolated virtual environment creation in `runtime_manager.py` to prevent macOS from terminating child processes or dylibs with `SIGKILL` (Killed: 9).

## v3.2.19
- **Resilient Translation Runtime Manager Resolution & macOS Execution Fixes**:
  - Implemented multi-layered `RuntimeManager` resolution in `translation.py`, `model_management.py`, and `plugins/manager.py` to prevent `AttributeError: 'RuntimeManager' object has no attribute 'ensure_environment'` or `kill_all_subprocesses` errors on macOS when launching translation background setup workers or managing model caches.
  - Explicitly passed `runtime_mgr` instance into `TranslationEnvSetupWorker` and fallback module importers to guarantee that `ensure_environment`, `kill_all_subprocesses`, and `remove_environment` are accessible across worker threads.
- **Preview & Version Inspector Synchronization**:
  - Synchronized version `v3.2.19` across `prs_shared.py`, `updater.py`, `build_installer.py`, Windows installer definitions, plugin manifests, `package.json`, `metadata.json`, and `index.html`.

## v3.2.18
- **macOS SSL Certificate Verification & Model Download Fixes**:
  - Automatically configures CA certificate bundles (`certifi.where()`) across `bootstrap.py`, `radio_tv_story_segmenter_worker.py`, `model_management.py`, and `plugins/translation/support.py`. Resolves `URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]>` on macOS during WeSpeaker, MarianMT, and NLLB model downloads.
- **Worker Interpreter Argument Filtering**:
  - Filtered out interpreter flags (`-B`, `-u`, `--prs-worker`) in `radio_tv_story_segmenter_worker.py`'s `main(argv)` entry point, eliminating `Error: Unknown processing mode: -B` when launching worker helpers.
- **Clean Application Shutdown & Single-Instance Reopen Fix**:
  - Implemented `closeEvent(event)` in `MainWindow` (`RadioTVSegmenter.py`) to properly stop background workers and close `QLocalServer` (`ipc_server`) upon window exit.
  - Added `_is_closing` state guards to prevent IPC connections from re-raising or re-opening the application window after the user closes the app.

## v3.2.17
- **Non-Blocking macOS & Linux Translation Process Cancellation**:
  - **Eliminated GUI Hangs on Cancel**: Replaced long 5000ms blocking wait calls in `stop_translation_worker()` (`translation.py`) with a fast 150ms graceful termination probe followed by immediate `SIGKILL` process termination on Unix/macOS. This prevents CTranslate2 C++ inference loops from freezing the Qt main thread and triggering macOS AppKit "Not Responding" hangs or window server crashes when the user clicks Cancel.
  - **Asynchronous Environment Setup Cancellation**: Connected `cancel_event` directly to `TranslationEnvSetupWorker` and `manager.ensure_environment()` in `translation.py`, allowing background translation runtime provisioning and package downloads to stop cleanly upon cancellation.
  - **Signal Disconnection Safety**: Safely disconnects background thread progress and completion signals during worker teardown to prevent delayed asynchronous callbacks from updating the UI or spawning error dialogs after cancellation.

## v3.2.16
- **macOS Speaker Diarization & Translation Stability Fixes**:
  - **OpenMP & Hugging Face Runtime Environment Flags**: Automatically sets `KMP_DUPLICATE_LIB_OK="TRUE"`, `TOKENIZERS_PARALLELISM="false"`, `HF_HUB_DISABLE_SYMLINKS_WARNING="1"`, `HF_HUB_DISABLE_PROGRESS_BARS="1"`, and `TQDM_DISABLE="1"` globally across worker processes and translation execution runtimes on macOS, Linux, and Windows.
  - **macOS Dynamic Library Resolution (`DYLD_LIBRARY_PATH`)**: Automatically injects `DYLD_LIBRARY_PATH` into `QProcessEnvironment` when launching translation worker subprocesses on macOS, ensuring CTranslate2 and SentencePiece shared libraries load seamlessly.
  - **macOS Gatekeeper Quarantine Removal (`com.apple.quarantine`)**: Added automatic quarantine attribute stripping (`xattr -dr com.apple.quarantine`) in `runtime_manager.py` when downloading or unpacking `uv`, standalone Python runtimes, or isolated virtual environments on macOS to prevent Gatekeeper permission blocks (`Permission denied` / `Killed: 9`).

## v3.2.15
- **Comprehensive Translation Job Cancellation**:
  - Enhanced `cancel_current_process` and media change guards in `processing.py` to reliably detect and terminate active translation tasks across `translation_process`, `translation_thread`, `_translation_env_thread`, and `_translation_env_worker`.
  - Upgraded `stop_translation_worker` in `translation.py` to terminate subprocess workers, disconnect pending signals, cleanly remove temporary request JSON files, and immediately restore the UI to an idle state.
  - Added `is_exporting` state tracker in `project_export.py` to prevent erroneous `[EXPORT] Cancel requested by user` log messages when cancelling processing tasks.
- **Accurate Speaker Diarization Model Management**:
  - Replaced the placeholder diarization informational message with interactive model management for the Speaker Diarization Model (WeSpeaker ResNet34 ONNX Voice Embedding).
  - Accurately checks WeSpeaker cache directories (`~/.wespeaker` and `models/wespeaker`) to display genuine installation status and disk footprint.
  - Provided interactive **Download / Install** (via background worker) and individual **Remove** controls in the *Manage Models & AI Data* dialog, and integrated WeSpeaker cache purging into the *Purge All Models & Cache Data* workflow.

## v3.2.14
- **Fixed Windows Update Installer Launch & Clean Process Exit**:
  - Enhanced `launch_and_install` in `updater.py` with multi-tier process execution on Windows, utilizing `subprocess.Popen` with `DETACHED_PROCESS` and `CREATE_NEW_PROCESS_GROUP` flags alongside 64-bit typed `ctypes.windll.shell32.ShellExecuteW` (`"open"` and `"runas"` UAC elevation fallback) and `os.startfile`.
  - Added clean window teardown and guaranteed background exit (`os._exit(0)`) in `_install_and_restart` so the running application releases all file locks immediately upon launching the installer, allowing Inno Setup to overwrite binaries seamlessly without blocking.
  - Automatically detects previously cached and verified installer packages in AppData/updates to present an immediate **"Install & Restart"** action.
- **Corrected Action Button Ampersand Formatting**:
  - Properly escaped accelerator ampersands as `"Install && Restart"` in Qt button declarations to ensure the label renders cleanly as **"Install & Restart"** in the updater interface.
  - Updated primary action handler to normalize and match both escaped and unescaped button strings.

## v3.2.13
- **Integrated Speaker Diarization Models & Runtime into Manage Models**:
  - Added full visibility, disk size metrics, and removal options for the Speaker Diarization Runtime & Models (`diarize_env` / WeSpeaker / ONNX / PyTorch) inside the *Manage Models & AI Data* tool.
  - Included `diarize_env` in the *Purge All Models & Cache* workflow to ensure complete cleanup of speaker identification models and environment dependencies.

## v3.2.12
- **Refined Translation Model Visibility in Manage Models & Preferences**:
  - Updated `_translation_plugin_installed` in `model_management.py` and `translation_installed` in `playback_preferences.py` to check both plugin installation AND enablement status (`is_plugin_installed("translation") and is_plugin_enabled("translation")`).
  - Bundled plugin manifests previously caused translation models to be displayed even when the translation plugin was not enabled or installed.
  - Manage Models now hides translation models when the translation plugin is inactive, unless orphaned translation model files already exist on disk (shown under "Translation models (Plugin Not Active)" with a "Remove" button to clean up disk space).

## v3.2.11
- **Fixed Updater `logger` NameError Bug**:
  - Imported `logging` and initialized `logger = logging.getLogger(__name__)` in `updater.py`.
  - Resolved `NameError: name 'logger' is not defined` during updater download cache cleanup (`cleanup_old_installers`), enabling seamless non-blocking update downloads.

## v3.2.10
- **Robust Windows UAC Elevation & Installer Launch Fix**:
  - Replaced basic shell execution in `launch_and_install` (`updater.py`) with explicit `ctypes.windll.shell32.ShellExecuteW` invocation using the `"runas"` verb on Windows.
  - Correctly triggers the Windows UAC permission prompt and ensures installer execution parameters and working directories are properly passed so the Inno Setup installer launches reliably upon user confirmation.

## v3.2.9
- **Aggressive Diarization & PyTorch Runtime Pruning (~70% Footprint Reduction)**:
  - Upgraded `prune_cuda_artifacts` in `runtime_manager.py` to strip heavy non-runtime development assets, C++ build headers (`torch/include`), CMake target metadata (`torch/share`), distributed multi-GPU training modules (`torch/distributed`), test suites (`torch/testing`, `torch/test`, `scipy/tests`, `numpy/tests`, `torchaudio/tests`), and GPU compiler packages (`triton`, `nvidia`) from CPU feature runtimes.
  - Reduces the `diarize_env` disk footprint from **~2.0 GB down to ~500–650 MB** without affecting speaker detection performance, accuracy, or inference speed.

## v3.2.8
- **Consolidated Single Updater Changelog Link**:
  - Removed duplicate inline changelog link from the update notes HTML body, maintaining a single, clean **"View Full Changelog in Browser ↗"** link in the release header.
- **"Clear Everything" Master Cleanup Control**:
  - Added a prominent **Clear Everything** button at the bottom of the "Cleanup Data" Preferences page (`Settings > Preferences > Cleanup Data`).
  - Completely purges all downloaded AI models, clears all temporary audio/video caches, resets user preferences to factory defaults, and clears app logs and updater installer packages in a single operation with confirmation.
- **Updated "All" & "Select" Button Labels**:
  - Standardized button wording across the Cleanup Data controls for visual clarity:
    - **Clear All Downloaded AI Models…**
    - **Clear Select AI Models…** (renamed from Open Model Manager)
    - **Clear All Temporary Caches (Waveforms, Audio Extracts, & Thumbnails)…**
    - **Clear All User Preferences (Reset Settings to Defaults)…**
    - **Clear All other App Data, Activity Logs & Update Packages…**

## v3.2.7
- **Centralized "Cleanup Data" Tab in Preferences**:
  - Added a dedicated "Cleanup Data" tab in the Preferences dialog (`Settings > Preferences > Cleanup Data`), consolidating all storage and application data management options in a clean, unified location.
  - Controls include:
    - **Clear Downloaded AI Models**: Purge all locally downloaded Whisper ASR, Parakeet, and translation models.
    - **Open Model Manager**: Open the detailed Model Management window for granular model inspection and deletion.
    - **Clear Temporary Caches**: Wipe generated waveform peak files, temporary audio extracts, and video thumbnails to reclaim storage.
    - **Clear User Preferences**: Reset application options and QSettings back to factory defaults with confirmation.
    - **Clear App Data & Activity Logs**: Purge log files, crash reports, and downloaded update installer packages from AppData.
  - Removed redundant "Purge All Models" item from the top-level Tools menu, keeping it centralized in the Model Manager and Cleanup Data tab.
- **Clickable Full Changelog URL Link**:
  - Upgraded the Check for Updates window (`Help > Check for Updates…`) to feature a prominent, clickable "View Full Changelog in Browser ↗" link above the release notes and inside the release summary.
  - Clicking opens `https://github.com/bradlinder/RTVS3/blob/main/CHANGELOG.md` directly in the default web browser.
- **Windows Installer Launch & UAC Elevation Fix**:
  - Updated `launch_and_install` in `updater.py` to launch downloaded installers on Windows via `os.startfile()`.
  - Fixes Windows Shell API execution, ensuring UAC administrator elevation permission prompts display cleanly and launch the installer window seamlessly after authorization.
  - Adjusted `cleanup_old_installers()` default retention (`max_to_keep=2`) to preserve recent downloaded installer packages in AppData.

## v3.2.6
- **Preferences GPU Acceleration Panel & Granular CUDA Tool Toggles**:
  - Relocated GPU acceleration configuration to a dedicated "GPU Acceleration" page inside the main Preferences dialog (`Settings > Preferences > GPU Acceleration`).
  - Added dedicated, granular acceleration checkboxes for all CUDA-capable tools:
    - **Transcription ASR**: Accelerated Faster-Whisper inference via CUDA FP16.
    - **Machine Translation**: Accelerated MarianMT / OPUS-MT translation via CTranslate2 CUDA FP16.
    - **Speaker Detection / Diarization**: Accelerated WeSpeaker ResNet34-LM voice embedding extraction via ONNX Runtime GPU (`CUDAExecutionProvider`).
  - Added real-time hardware status indicators reflecting whether an NVIDIA GPU is physically present (`detect_nvidia_gpu`) and whether the optional GPU runtime is currently installed.
- **100% Optional Architecture with Zero Disk Footprint When Disabled**:
  - The base distribution installer remains 100% CPU-first, lightweight, and completely free of CUDA/cuDNN packages.
  - Optional CUDA acceleration packages (`torch` cu121, `ctranslate2`, `onnxruntime-gpu`, `wespeakerruntime`) are isolated inside the on-demand `gpu_transcribe` virtual environment (`runtime_manager.py`).
  - When disabled or not installed, GPU acceleration consumes exactly **0 MB** of disk space.
  - Added one-click "Uninstall GPU Runtime (Reclaim Disk Space)" button in Preferences allowing users to remove the optional environment at any time to instantly reclaim ~1.5 GB.
- **Direct Accessibility for "Purge All Data & Cache"**:
  - Exposed the full data purge action directly in the main window menu under `Tools > Purge All Downloaded Models & Cache Data…`.
  - Added a matching "Purge All Downloaded Models & Cache Data…" button directly in `Preferences > AI Models` alongside the Model Manager.
  - Allows immediate one-click deletion of all downloaded Whisper ASR models, translation models, updater cache, log files, and optional virtual environments.

## v3.2.4
- **CPU-First Diarization & Translation Runtime Footprint Optimization**:
  - Stripped heavy CUDA/cuDNN dependencies from both the isolated translation (`runtimes/translate`) and diarization (`runtimes/diarize`) runtimes, configuring them with PyTorch CPU wheels (`https://download.pytorch.org/whl/cpu`) and reducing disk footprints by over 1.4 GB per runtime.
  - Implemented automatic CUDA artifact pruning (`prune_cuda_artifacts`) across `RuntimeManager` and `model_management.py` to systematically strip bundled NVIDIA packages (`nvidia-cublas*`, `nvidia-cudnn*`, `nvidia-nvrtc*`, `torch_cuda*`) upon environment setup and during Model Manager inspection.
  - Enforced pure CPU execution across `plugins/translation/worker.py` and `radio_tv_story_segmenter_worker.py`.
  - Updated Model Manager table labels to `"Translation Runtime & Dependencies (CTranslate2, CPU-only)"` for clear visibility of environment requirements.
- **AppData Installer Cache Management & Automatic Cleanup**:
  - Implemented `cleanup_old_installers()` in `updater.py` to automatically scan `AppData/updates` (and macOS/Linux app data equivalents) and delete older downloaded installer files (`.exe`, `.dmg`, `.pkg`, `.deb`, `.rpm`, `.AppImage`, etc.), retaining at most 1 recent package and removing all orphaned `.download` files.
  - Hooked automated installer cleanup into app startup, background update checks, download completion, and the Check for Updates dialog.
  - Added "Downloaded Update Installers" inspection and deletion to the AI Models & Cache Manager (`model_management.py`), as well as full cache purge support in `purge_all_data()`.
- **Documentation & Build Specification Accuracy**:
  - Synchronized `README.md`, `BUILD_INSTRUCTIONS.txt`, `STABILITY_NOTES.md`, and `ARCHITECTURE.md` to reflect the CPU-first architecture for translation and diarization and clarify optional Whisper GPU acceleration.

## v3.2.3
- **Interactive Windows Uninstaller Data Cleanup Prompt**:
  - Implemented custom Inno Setup `[Code]` uninstall hook in `installer/Windows/RadioTVStorySegmenter.iss` prompting users during uninstallation to optionally purge saved preferences, log files, and downloaded AI models from `%LOCALAPPDATA%\RadioTVStorySegmenter`.
- **Cross-Platform In-App Storage & Model Purge Manager**:
  - Added a "Purge All Models & Cache Data…" option in `model_management.py` and the AI Models Preferences pane, enabling macOS, Linux, and Windows users to safely delete downloaded Whisper ASR models, translation models, and log files to reclaim multi-gigabyte disk space at any time.

## v3.2.2-beta
- **Automatic GitHub Update Repository Migration (`bradlinder/RTVS3`)**:
  - Implemented automatic migration in `get_github_repo()` across `prs_shared.py`, `updater.py`, and `utils/constants.py` to detect legacy stored repository values (`bradlinder/RTVS`, `bradlinder/RadioTVStorySegmenter`) in user `QSettings` and seamlessly upgrade them to `bradlinder/RTVS3`.
  - Fixed hardcoded `"bradlinder/RTVS"` defaults in `playback_preferences.py` ("Restore Defaults" for Software Updates) to target `DEFAULT_GITHUB_REPO`.
  - Added repository string normalization on settings save and upon opening the Check for Updates dialog to prevent stale checks against older release repositories.
- **Dead Code & Orphaned Dialog Module Pruning**:
  - Purged obsolete `models.py` containing 185 lines of unused dataclasses replaced by native dictionary schemas in `prs_shared.py`.
  - Removed redundant dialog duplicates in `ui/dialogs/` (`find_replace.py` and `comment_editor.py`), eliminating the orphaned `ui/` folder tree.
  - Pruned committed 12 KB binary archive artifact `plugins/translation/translation.rtvs-addon` from the source repository.
- **Architectural Decoupling & Import Consolidation**:
  - Replaced hard top-level import of `YouTubeAssistedUploadGuideDialog` in `project_export.py` with lazy, guarded import inside `export_youtube_bundle`, preserving the architectural invariant that core modules must not import from `plugins/` on startup.
  - Consolidated `format_time` in `export/docx.py` to import directly from `prs_shared`, eliminating the last external dependency on `utils.time_format`.
  - Cleaned vestigial `torch_mod` parameter signatures and returns from `plugins/translation/worker.py` following the pure CTranslate2 engine transition.

## v3.2.1-dev (In Development / Roadmap)
- **GitHub Update Repository & Release Target Migration (`bradlinder/RTVS3`)**:
  - Migrated update check endpoints, release asset downloads, issue links, and manifest metadata from `bradlinder/RTVS` to `bradlinder/RTVS3` across `prs_shared.py`, `updater.py`, `utils/constants.py`, installer scripts, and plugin manifests.
- **Unified Core Asynchronous Runtime Provisioner & Responsive Dialog**:
  - Re-architected virtual environment creation and pip installation in `runtime_manager.py` with non-blocking subprocess polling and `threading.Event` cancellation.
  - Replaced blocking modal execution in `processing.py` with responsive threaded workers (`RuntimeSetupWorker` and `WhisperModelInstallWorker`), enabling seamless user cancellation without UI freezes or leaked background processes.
- **Whisper Hallucination & Degenerate Loop Scrubber**:
  - Implemented comprehensive transcript cleaning suite in `prs_shared.py` featuring n-gram repetition collapsing (`collapse_repeating_ngrams`), regex-based hallucination phrase pruning (`strip_hallucination_phrases`), and degenerate tail trimming (`trim_trailing_degenerate_tail`).
  - Integrated scrubber into transcription pipeline across `processing.py` and `radio_tv_story_segmenter_worker.py`.

## v3.2.0-dev
- **Subprocess & Worker Lifecycle Hardening (Windows Job Objects & POSIX Groups)**:
  - Bound the application and all child worker processes (`python.exe`, `ffmpeg.exe`, translation processes) to an OS Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) on Windows and isolated process groups on POSIX. Prevents lingering orphan processes if the parent process crashes or is killed externally.
- **Translation Plugin Self-Containment & Pure CTranslate2 Engine**:
  - Removed legacy PyTorch and Transformers fallbacks from `plugins/translation/worker.py` and pruned `torch` from translation runtime dependencies. Model inference runs strictly through quantized `ctranslate2` and `sentencepiece`, dramatically shrinking memory footprint and installation overhead.
- **Emergency Project State Serialization & Crash Recovery**:
  - Enhanced global exception hooks in `playback_preferences.py` to atomically snapshot dirty projects to `.crash_recovery.rtvs` upon unhandled exceptions.
  - Added startup detection in `media_batch.py` (`restore_last_opened`) to prompt users to recover emergency crash snapshots if an unexpected termination occurs.
- **Download Integrity & Plugin Verification**:
  - Implemented cryptographic SHA-256 validation helpers in `prs_shared.py` and wired optional `expected_sha256` integrity checking into `plugins/manager.py`'s `install_addon`.
  - Hardened translation model downloads in `plugins/translation/worker.py` with HTTP status validation and support for pinned revisions.

## v3.1.6
- **Resolved Comment Shortcut (Ctrl+M) Conflict**:
  - Connected the global `add_comment_action` (`Ctrl+M`) to the MainWindow `add_comment_from_selection()` method instead of a non-existent transcript view method. This ensures that pressing `Ctrl+M` works globally across the application, whether the transcript view is focused or not, and eliminates silent shortcut collisions.
- **Prevented Duplicate Comment Creation**:
  - Restricted selection-based comments to exactly one primary segment target index in the comment editor dialog instead of copy-creating multiple independent comments when a selection boundary slightly overlaps adjacent segments. This ensures that clicking the comment button or using the shortcut adds exactly one comment per selection range.

## v3.1.5
- **Spacebar Play/Pause Restoration in Transcript Viewing Mode**:
  - Refined the global event filter inside `playback_preferences.py` to allow the Spacebar key to toggle play/pause when the transcript text editor is focused in read-only viewing mode, instead of acting as a "Page Down" key.
- **UNC Network Share Safe File/Autosave Replacement Fallback**:
  - Implemented `safe_replace` across all persistent save pathways (`prs_shared.py`, `playback_preferences.py`, and `model_management.py`) utilizing exponential retry backoff loops and write-stream file copy fallbacks. This completely resolves `WinError 5 Access is denied` permission blocks during auto-saves and manual project saves on Windows SMB/UNC network storage shares.
- **Plugin Archive Path Traversal & Zip Slip Security Hardening**:
  - Implemented safe path validation (`safe_extract_zip` & `safe_extract_tar`) across `plugins/manager.py` and `runtime_manager.py` to strictly sanitize archive target paths and prevent path traversal vulnerabilities.
  - Added cryptographic SHA-256 checksum verification for downloaded plugin archives and standalone runtime binaries prior to extraction.
- **Transactional Staged Plugin Installations**:
  - Re-architected plugin installation and update workflows to extract into temporary staging directories, perform manifest/file validation, and execute atomic folder swaps with automated rollback on failure.
- **Translation Runtime Decoupling & Pure Plugin Architecture**:
  - Isolated translation dependencies, fallbacks, and runtime models strictly inside `plugins/translation/`, stripping direct ML model fallbacks from core code paths.
- **Deterministic Provisioning State Machine**:
  - Converted runtime environment provisioning in `runtime_manager.py` to a formal state machine (`NOT_INSTALLED` -> `CREATING` -> `INSTALLING` -> `VALIDATING` -> `READY` / `BROKEN`) with standardized recovery paths.

## v3.1.4
- **Diarization & Missing Type Definition Corrections**:
  - Resolved `NameError: name 'Optional' is not defined` crash on program launch after clean installation by explicitly importing type definitions inside `transcript_story.py`.

## v3.1.3
- **Floating Selection Popup Initialization & Preference Enforcement**:
  - Ensured `TranscriptSelectionBubble` starts hidden upon widget initialization so the floating toolbar is never displayed at startup.
  - Enforced `show_floating_selection_toolbar` preference checks across `prs_shared.py`, `ui_layout.py`, and `playback_preferences.py` so that if disabled in Preferences, the floating toolbar is never displayed at startup or on text selection.
- **Deep-State Isolation for Universal Undo & Redo**:
  - Resolved `_clone_transcript_state` object reference sharing in `playback_preferences.py` and `prs_shared.py` using complete deep copies.
  - Pressing `Ctrl+Z` (Undo) or `Ctrl+Shift+Z` (Redo) now reliably restores removed highlights and deleted comments, auto-refreshing both transcript views and the sidebar comments panel.
- **Enhanced Contiguous Highlight Removal**:
  - Re-engineered `remove_highlight` to clear character background brushes and word/segment metadata across contiguous highlighted sections spanning multiple sentences or paragraphs.

## v3.1.2
- **Expanded Keyboard Shortcut Customization Suite**:
  - Registered all application functions across File, Edit, View, Tools, Settings, and Help menus, right-click context menus, and transcript editor views into the shortcut customization manager.
  - Added default keyboard shortcut bindings for **Export Project Archive (.zip)** (`Ctrl+Shift+E` / `Cmd+Shift+E`), **Redo** (`Ctrl+Shift+Z` / `Cmd+Shift+Z`), **Delete Comment** (`Ctrl+Alt+D`), **Remove Highlight** (`Ctrl+Alt+H`), **Add Selected Text to New Story** (`Ctrl+Alt+N`), **Play Selected Text** (`Ctrl+Space`), and **Clear Text Selection** (`Esc`).
- **Alphabetical & Category Shortcut Sorting**:
  - Enhanced the Keyboard Shortcut Customizer dialog (`F8` / Preferences) with instant sorting controls ("Action (Alphabetical)" vs. "Category").
  - Shortcuts are arranged in clean alphabetical order by action name by default, with one-click toggles and interactive column header sorting.

## v3.1.1-beta-4
- **Contiguous Section Highlight Removal**:
  - Re-engineered `remove_highlight` in `prs_shared.py` to trace linear word sequences across single and multi-paragraph highlighted text blocks.
  - Selecting text or right-clicking anywhere within a highlighted region and choosing "Remove Highlight" now clears background highlighting across the entire contiguous highlighted section spanning multiple sentences or paragraphs.
- **Universal Undo & Redo Integration for Comments and Highlights**:
  - Captured project state baselines before comment deletion, comment creation, comment editing, highlight removal, and highlight toggling.
  - Pushed explicit `ProjectStateCommand` instances to `MainWindow.undo_stack` for every comment and highlight operation.
  - Pressing `Ctrl+Z` (Undo) and `Ctrl+Shift+Z` / `Ctrl+Y` (Redo) now reliably restores or reverts deleted comments and removed highlights.

## v3.1.1-beta-3
- **Bi-Directional Comment & Transcript Selection Synchronization**:
  - Implemented active visual styling for selected comment cards in `CommentsPanel` with high-contrast active borders and background fill.
  - Clicking a comment card in the sidebar highlights the card as active, seeks playback, and selects the corresponding text in the transcript.
  - Clicking or selecting commented text in the transcript view now automatically brings the corresponding comment card into active focus and scrolls it into view.
- **Rich Text Formatting in DOCX Export**:
  - Enhanced DOCX export engine (`create_story_docx` in `export/docx.py`) to reflect word-level and block-level rich text formatting options (**bold**, *italics*, <u>underline</u>, ~strikethrough~, and ==highlighted text==) in exported `.docx` documents.
- **Enhanced Right-Click Context Menu Options**:
  - Added **"Remove Highlight"** option to right-click context menus in both viewing and editing modes to clear highlighting from selected text or targeted segments.
  - Added **"Delete Comment"** option to right-click context menus in both viewing and editing modes to remove the comment and clear any associated highlights.

## v3.1.1-beta-2
- **Range-Based Comment Anchoring & Complete DOCX Export Capture**:
  - Upgraded comment creation (`add_comment_from_selection`) to anchor comments to the full selected text span (e.g. "Back when..." to "...about how") across single or multi-segment selections instead of single words or cursor blocks.
  - Sidebar comment cards and transcript highlights now display and highlight the exact quoted text selection span.
  - Clicking a comment card in the sidebar now seeks to the exact start time and selects the exact highlighted text range in the transcript view.
  - Enhanced DOCX export (`create_story_docx` & `inject_native_comments_to_docx`) to split paragraph runs and anchor OpenXML `w:commentRangeStart` and `w:commentRangeEnd` directly around selected text quotes.
  - Guaranteed 100% complete capture of all comments in transcript exports without omission.
- **Toggle Floating Selection Quick-Action Toolbar Preference**:
  - Added preference setting in Preferences dialog (General -> Selection Popup: "Show floating quick-action toolbar on text selection in transcript") to toggle floating selection tooltips (Play, Story, Comment, Exclude, Export).

## v3.1.1-beta-1
- **Streamlined Click-to-Record Keyboard Shortcut Tools**:
  - Eliminated redundant "Record Key" and "Record Shortcut" buttons from both the Shortcut Lookup Tool and the Shortcut Customizer Editor.
  - Users can now simply click or focus on the shortcut input text box to automatically engage recording mode, significantly streamlining the customizer UX.
- **Unified Export Window & Dialog Initialization Fix**:
  - Restored missing `QStackedWidget` import in `export/dialog.py` to ensure the unified export dialog opens properly without runtime initialization exceptions.
- **Resolved Ambiguous Shortcut Overloads & In-Focus Comment Toggle**:
  - Eliminated duplicate `QAction` shortcut bindings for `Ctrl+Alt+C` across window menus and context menus that previously caused Qt ambiguous shortcut warnings.
  - Replaced duplicate action instances with unified action references and ensured `TranscriptView` key press event routing triggers `toggle_comments_panel()` directly.
  - Re-architected Word `.docx` export pipeline (`create_story_docx` / `export/docx.py`) to package native OOXML annotations (`word/comments.xml`, `w:commentRangeStart`, `w:commentRangeEnd`, and `w:commentReference`) matching Microsoft Word and LibreOffice Writer specification standards.
  - Resolved LibreOffice document corruption warnings by ensuring fully-formed XML namespaces, sequence IDs, and schema references.
  - Exported comments and notes now render as native sidebar comment annotations in both Microsoft Word and LibreOffice Writer (as well as Google Docs).
  - Preserved full author metadata, timestamps, highlighted text ranges, and multi-note threading.
- **Interactive Keyboard Shortcut Lookup Tool & Conflict Inspector**:
  - Added dedicated Shortcut Lookup Tool directly inside the Keyboard Shortcut Customizer (`F8` / Preferences): enter or record any key combination to instantly see which function is currently mapped to it.
  - Displays rich metadata (action name, category, description, custom vs default status, and availability state).
  - Included interactive "📍 Select in Table" one-click jump to highlight and focus the matching action in the customizer table.
- **Transcript Text Selection Preservation**:
  - Fixed selection loss during text formatting: invoking Bold (`Ctrl+B`), Italic (`Ctrl+I`), Underline (`Ctrl+U`), Strikethrough (`Ctrl+K`), Highlighter, or Clear Formatting (`Ctrl+\`) now preserves the active text selection range until the user clicks elsewhere in the transcript.
- **Multi-Color Highlighter Palette & HTML Rendering**:
  - Restored highlighter functionality with support for 6 vibrant, standard highlighting colors: Yellow (`#fef08a`), Green (`#bbf7d0`), Cyan/Blue (`#bae6fd`), Pink (`#fbcfe8`), Orange (`#fed7aa`), and Purple (`#e9d5ff`).
  - Added color dropdown menu to the Highlight toolbar button and right-click context menu, with full token persistence and dynamic HTML styling.
- **Harmonized Keyboard Shortcut Engine & In-Focus Window Overrides**:
  - Enforced `Qt.ShortcutContext.ApplicationShortcut` across actions so in-focus application events execute reliably without OS collisions.
  - Set default keyboard shortcut for toggling the Comments Sidebar & Annotations to `Ctrl+Alt+C` (macOS: `Cmd+Option+C`).
  - Added full shortcut bindings and customization support for Rich Text Formatting (**Highlight**: `Ctrl+Shift+H`, **Bold**: `Ctrl+B`, **Italic**: `Ctrl+I`, **Underline**: `Ctrl+U`, **Strikethrough**: `Ctrl+K`, **Clear Formatting**: `Ctrl+\`) and **Split Speaker Segment** (`Shift+Enter`).
  - Enhanced Shortcut Customizer with automatic recording lifecycle and conflict resolution dialog.
- **Dynamic Toolbar Tooltips with Live Keyboard Shortcuts**:
  - All toolbar buttons (Comments toggle, Transcript Edit Mode toggle, Font size increase/decrease/reset, Bold, Italic, Underline, Strikethrough, Highlight, Clear Formatting, Split Speaker, Play/Pause, and Story controls) dynamically reflect their current assigned keyboard shortcuts directly in hover tooltips.

## v3.1.0-dev-2
- **Universal .docx Comments Compatibility (Microsoft Word, LibreOffice, Google Docs)**:
  - Re-engineered the Word (.docx) document export engine to generate both native OpenXML comments (`word/comments.xml`, `w:commentRangeStart`, `w:commentRangeEnd`, and `w:commentReference`) and styled visual annotation callouts.
  - Exported comments now appear in Microsoft Word's comment review pane, LibreOffice Writer's comment margin cards, and when uploaded to Google Docs.
  - Includes user preference integration (`export_include_comments`) with full timestamp spans, speaker attribution, and author metadata.
- **Keyboard Shortcut Customizer & Conflict Resolution System**:
  - Integrated interactive conflict detection in the Keyboard Shortcut Customizer (`F8` / Preferences): when assigning a key combination already in use by another action, a warning dialog prompts the user to either apply the shortcut to the new action (reassigning it) or keep the original binding.
  - If keeping the original binding, the customizer automatically re-engages recording mode so the user can immediately enter an alternative shortcut combination.
  - Added new actions to the shortcut registry: **Add / Edit Comment** (`Ctrl+M`), **Toggle Comments Sidebar** (`Alt+5`), **Toggle Transcript Edit Mode** (`F2`), **Bold** (`Ctrl+B`), **Italic** (`Ctrl+I`), **Underline** (`Ctrl+U`), **Strikethrough** (`Ctrl+K`), and **Clear Formatting** (`Ctrl+\`).
  - Resolved shortcut collisions across the application (e.g., separating Batch Processing to `Ctrl+Shift+B` so `Ctrl+B` is dedicated to Bold text formatting).
  - Enforced window-scoped shortcut context (`Qt.ShortcutContext.WindowShortcut`) across all actions so in-focus application events execute reliably.
- **Plugin Export Destination Architecture & WordPress Publishing Fix**:
  - Resolved plugin interface contracts in `export/dialog.py` and `plugins/wordpress/export_destination.py`, ensuring all plugin destinations supply appropriate button labels, icons, and configuration panels.
- **Codebase Modularization & Decoupled Architecture**:
  - Decoupled domain-specific export engines out of monolithic scripts into a dedicated `export/` package (`export/pdf.py`, `export/docx.py`, `export/subtitles.py`, `export/dialog.py`).
  - Implemented true dynamic plugin export destination architecture via `plugins.base.ExportDestination` and `PluginManager`.
  - Created structured data model layer (`models.py`) with type-annotated dataclasses (`StoryItem`, `ActivitySnapshot`, `ExportOptions`) and TypedDict definitions.
  - Extracted core utilities and dialog components into `utils/` (`constants.py`, `time_format.py`) and `ui/dialogs/` (`find_replace.py`, `comment_editor.py`).

## v3.0.2
- **Native PDF Document Export**:
  - Implemented standalone `TranscriptPdfWriter` generating native, dependency-free PDF 1.4 vector documents for individual story transcripts and full episode transcripts.
  - Added PDF format checkbox (`PDF document (.pdf)`) to Local Export formats alongside Text (.txt) and Word DOCX (.docx).
  - High-precision typography layout with Helvetica, Helvetica-Bold, and Helvetica-Oblique font resources, headers, metadata ribbons, line dividers, word-wrapped body paragraphs, timestamps, and speaker labels.
  - Professional comment callouts in PDF exports with yellow/amber side borders, distinctive backgrounds, and indented typography.
  - Automatic multi-page pagination with running page headers, dividers, and document footers ("Page X" and "Radio & TV Story Segmenter").
  - Export settings persistence (`export_format_pdf`) via `QSettings` and multi-format batch validation.
- **Collapsible Export Center Sections**:
  - Re-architected `UnifiedExportDialog` with reusable `CollapsibleSection` container widgets featuring animated disclosure chevrons, count badges, and clean rounded panels.
  - Organized Local Files, WordPress, and YouTube Studio export panels into clean, individually expandable and collapsible sections to optimize window height and visibility.
  - Added global "Collapse All / Expand All" toggle button to the main export header for one-click workflow navigation.

## v3.0.1-beta-1
- **Transcript Rich Text Formatting Toolbar & Styling Engine**:
  - Added dedicated formatting toolbar above the transcript view that automatically appears when Editing Mode is toggled on (`Edit Transcript`).
  - Added quick-access formatting buttons: **Bold** (`Ctrl+B`), **Italic** (`Ctrl+I`), **Underline** (`Ctrl+U`), **Strikethrough** (`Ctrl+K`), **Highlight** (Yellow text background), **Clear Formatting** (`Ctrl+\` / `Ctrl+Space`), and **Split Speaker Segment** (`Shift+Enter`).
  - Implemented real-time bidirectional format detection: toolbar buttons automatically toggle their active/pressed state matching the styling of text at the current cursor position or selection (`formatChanged` signal & cursor tracking).
  - Added right-click context menu "Format Text" submenu in editing mode providing full access to all styling actions and hotkeys.
  - Non-destructive token synchronization: word-level styling (`bold`, `italic`, `underline`, `strike`, `highlight`) is preserved across token splicing, re-rendering, and translation views.
- **Multi-Location Comments Sidebar Toggles**:
  - Added checkable "Show Comments Sidebar" option (`Ctrl+Alt+M`) to the **View > Transcript** submenu.
  - Retained "Show Comments Sidebar & Highlights" in top-level **View** menu and the "💬 Comments" toggle button in the transcript search header bar.
  - Connected the sidebar's close (`✕`) button directly to synchronized toggle state so closing the panel updates the toolbar button and all menu checkboxes synchronously.
  - Maintained user preference persistence for sidebar visibility across application sessions.

## v3.0.0-beta.5
- **Word / Google Docs / LibreOffice Style Comments Architecture**:
  - Re-architected notes into a professional, non-destructive **Comments** system inspired by Microsoft Word, Google Docs, and LibreOffice Writer.
  - Removed raw inline note blocks from the transcript body, keeping the reading flow completely uncluttered.
  - Implemented collapsible, docked **Comments Sidebar** (`CommentsPanel`) with comment cards displaying timestamp spans, quote excerpt anchors, multi-line comment text, and quick ✏️ Edit and 🗑️ Delete/Resolve actions.
  - Two-way interactive synchronization: clicking a comment card scrolls the transcript to the passage and seeks audio playback; hovering or clicking commented transcript passages highlights and scrolls to the card in the sidebar.
  - Non-destructive amber/yellow highlight ranges (`#fef08a` / `#854d0e`) rendered over commented transcript text via `QTextEdit.ExtraSelection` with hover tooltips.
  - Added dedicated View menu action "Show Comments Sidebar & Highlights" (`Ctrl+Alt+M`) and search bar toggle button.
- **Spacebar & Dialog Focus Isolation**:
  - Isolated keyboard shortcut dispatching (`eventFilter`) so global Play/Pause hotkeys are strictly suppressed whenever a text input, dialog, or comment editor is active.
  - Multi-line `CommentEditorDialog` with full native support for spaces, tabs, line breaks (`Enter`), and quick save (`Ctrl+Enter`).
- **Transcript Paragraph-Constrained Navigation**:
  - Fixed `Home` and `End` keys in `InteractiveTranscriptEdit` to seek and navigate strictly within the current paragraph block rather than jumping across the entire document.
  - Arrow key navigation in viewing mode jumps playback according to user skip settings and synchronizes timeline cursor and transcript word highlighting.
- **Decommissioned Project & Episode Notes (Scope Simplification)**:
  - Completely removed legacy project and episode notes dialogs and menus, focusing exclusively on segment-anchored document comments.
- **Word Document (DOCX) Comments Export**:
  - Added an "Include Comments" option to the export settings dialog with preference persistence.
  - Exports segment-anchored comments into Microsoft Word documents as beautifully styled, indented callouts (`💬 Comment: ...`) with accurate timing and speaker context.

## v3.0.0-beta.4
- **Transcript Navigation & Selection Jumping**:
  - Implemented timestamp and speaker label cursor navigation: clicking any timestamp link `[00:00]` or speaker header in `InteractiveTranscriptEdit` seeks playback to that exact second and positions text cursor precisely at the clicked location.
  - Paragraph-scoped `Home` and `End` key navigation moving the text cursor strictly to the start or end of the current paragraph block rather than jumping across the full transcript document.
  - Arrow key skipping in transcript edit view synchronized with user playback skip preferences (`playback_skip_interval`).
- **Interactive Notes & Highlighting System**:
  - Multi-line text note input supporting spaces, tabs, and paragraph breaks via custom `NoteInputDialog`.
  - Rich document-style section highlighting: text selections assigned notes are highlighted in distinct amber/yellow background styling (`#fef08a` / `#854d0e`), separate from active selection highlights.
  - Hover tooltip badges and right-click context menu options to view, edit, or delete notes attached to transcript segments.
  - "Add Note" trigger integrated into floating selection bubble and context menu.
- **DOCX Export with Notes**:
  - Updated `UnifiedExportDialog` and `project_export.py` with an "Include Segment & Project Notes" toggle (`export_opt_include_notes`).
  - Native Word document export renders formatted note paragraphs with custom indented callouts and distinct styling.

## v3.0.0-beta.3
- **Single-Instance Application Enforcement & Preference**:
  - Added preference setting in `playback_preferences.py` ("Instance Handling Mode") allowing users to choose between single-instance mode and multi-instance mode.
  - Implemented cross-instance IPC via `QLocalServer` and `QLocalSocket` in `RadioTVSegmenter.py`. When double-clicking an `.rtvs` file while the app is already running in single-instance mode, the file path is forwarded to the existing process.
  - If another project is open with unsaved changes, the app prompts the user to save before loading the requested project or dismiss the request.
- **Media Ingest Prompt Mode**:
  - Fixed prompt behavior when Media Ingest Mode is set to `"Prompt every time when saving project"` (`media_ingest_mode: ask`).
  - Triggers an interactive `QMessageBox` during `save_project` asking if the source media file should be copied into the project bundle `Media/` subfolder.
- **Project-Local Peak Cache Storage**:
  - Pre-calculated waveform `.peaks` cache files are now stored inside the project folder's hidden `.cache/peaks/` subfolder (or alongside the `.rtvs` file) rather than polluting the source media directory.
- **Transcript Keyboard Navigation**:
  - Enabled Home, End, PageUp, PageDown, and Arrow key navigation in `InteractiveTranscriptEdit` during viewing mode to move through transcript text smoothly.
- **Clickable Speaker & Timestamp Links**:
  - Enabled clicking on speaker labels (`speaker:`) and timestamps in the transcript to instantly seek timeline, audio, and video preview to that exact moment.
- **Transcript Notes & Segment Notes System**:
  - Added context menu actions ("Edit Segment Note..." and "Transcript & Project Notes...") to `InteractiveTranscriptEdit`.
  - In-line segment notes are rendered with yellow callout badges in the transcript viewer and saved directly in `.rtvs` project files.
  - Full project/episode notes and segment notes are automatically styled and included in DOCX exports.
- **Cache Usage & Purge Discovery**:
  - Fixed cache scanner in `get_cache_disk_usage` and `purge_caches` by automatically discovering project paths via `QSettings` (`default_project_directory`, `last_saved_project_path`, `recent_projects`), accurately calculating total `.peaks` files and bytes.
- **UI Contrast & Layout Fixes**:
  - Enhanced contrast for story list items in dark mode.
  - Consolidated Quick Actions bubble layout preventing label truncation.

## v3.0.0-beta
- **Debian / Ubuntu (.deb) Control Version Compliance**:
  - Fixed an issue where Debian control files generated with `V3.0.0-beta` or uppercase/prefixed version strings failed `dpkg-deb` validation (`'Version' field value: version number does not start with digit`).
  - Added Debian-compliant version string sanitization (`DEB_VERSION`) in `installer/Linux/build_deb.sh`, ensuring version strings strictly begin with digits, convert uppercase tags to lowercase, and map hyphens to tildes (`~`).
  - Sanitized version extraction across all GitHub Actions workflow jobs in `.github/workflows/build.yml`.
- **Self-Contained Project Bundles & Ingest Preferences**:
  - Added project media ingest behavior preferences (Reference in place vs. Copy into project bundle vs. Ask when saving) in `playback_preferences.py` and `project_export.py`.
  - Added automated disk space preflight verification before media ingestion using `shutil.disk_usage`, prompting confirmation when source media is large (>1 GB) or low disk headroom (<10%) is detected.
- **Clean Dedicated Directory Hierarchy**:
  - Upgraded project bundle structure to dedicated subfolders: `<Project>/media/` (original recordings), `<Project>/exports/audio/` (cut audio files), `<Project>/exports/transcripts/` (transcripts and documents), and `<Project>/.cache/` (hidden peak and transient caches).
  - Maintained complete backward compatibility for legacy projects with multi-tier fallback resolution in `resolve_project_media()`.
- **Project Maintenance & Mobility Tools**:
  - Added **File > Consolidate Media into Project...** to easily copy external files into the project directory for portability.
  - Added **File > Clean Cache / Reclaim Space...** to inspect and prune `.cache/peaks/` and scratch buffers.
  - Added **File > Export Project Archive (.zip)...** with customizable inclusion of source media, transcripts, and exports while excluding temporary caches.
  - Added interactive **Locate Missing Media** dialog with auto-discovery and one-click re-linking.
- **Workflow & UI Polish**:
  - Added interactive drag-and-drop zero-state onboarding cards to `InteractiveTranscriptEdit` and `StoryListWidget`.
  - Added "Open Folder" action button on export completion dialogs (`show_export_completion_dialog`) across story exports, full episodes, CUE sheets, and tracklists.
  - Added floating quick-action selection bubble toolbar (`TranscriptSelectionBubble`) over transcript selections with instant Play, + Story, Exclude, and Quick Export buttons.
  - Added dual-layer timeline navigation (`TimelineWidget`) with interactive macro overview strip, story segment blocks, and draggable viewfinder rectangle.
  - Added harmonized color-coded story accents across story cards (`StoryCardDelegate`), timeline spans, and transcript markers.
- **Full Project Version Alignment**:
  - Synchronized `v3.0.0-beta` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, `metadata.json`, `index.html`, `transcript_story.py`, and plugin manifests (`wordpress`, `youtube`, `translation`).

## v2.9.6
- **Windows & Cross-Platform Artifact Naming Normalization**:
  - Resolved an issue in the packaging pipeline where double dots (e.g. `2.9..6`) could be introduced into Windows installer executable names (`RadioTVSegmenter-2.9.6-Windows-Setup.exe`) and Linux tarball archives.
  - Hardened version extraction in `build_installer.py`, `build_windows.bat`, `build_deb.sh`, `build_app.sh`, and `.github/workflows/build.yml` with strict dot-collapsing and semantic versioning sanitization (`re.sub(r"\.+", ".", v)` / `tr -s '.'`).
- **Updater Engine Resilient Asset Matching & Semantic Verification**:
  - Enhanced `updater.py` with normalized string and semantic comparison logic across `parse_version_tuple`, `_find_release_checksum`, `select_best_asset_for_platform`, and `_display_release`.
  - Checksum discovery and asset matching now seamlessly handle normalized filenames (collapsing any legacy double-dot naming), ensuring download and verification never fail due to minor formatting discrepancies.
  - Asset label mismatch notices now evaluate numerical semantic version tuples rather than raw string comparisons to eliminate false-alarm warning banners.
- **Full Project Version Alignment**:
  - Synchronized `v2.9.6` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, `metadata.json`, `index.html`, `transcript_story.py`, and plugin manifests (`wordpress`, `youtube`, `translation`).
- **AI Studio Web Preview Git Hygiene & Zero-Token Scaffolding Restoration**:
  - Consolidated and restructured `.gitignore` to strictly isolate all Node/Vite web preview files (`package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`, `eslint.config.js`, `metadata.json`, `index.html`, `src/`, `public/`, `node_modules/`, `bun.lock`), keeping the GitHub repository focused exclusively on the Python desktop application.
  - Removed stale untracked `gitignore` file (without leading dot) to restore canonical gitignore parsing.
  - Implemented `preview_manager.py` to enable instant zero-token restoration and version synchronization across all web preview files (`python preview_manager.py --restore` / `--sync`).
  - Decoupled `src/App.tsx` from manual markdown copy-pasting by importing `CHANGELOG.md?raw` directly, ensuring real-time changelog preview updates without code maintenance overhead.

## v2.9.5
- **WordPress Export Media Notice Placement**:
  - Refined custom notice placement in `wordpress_export.py` so that top-positioned header notices appear directly beneath embedded audio (`<!-- wp:audio -->`) or video (`<!-- wp:video -->`) players, ensuring media player controls stay prominently at the top of the post.
- **Updater Engine Semantic Comparison Fix**:
  - Resolved an issue in `updater.py` where `is_version_older` was not defined when `_on_releases_loaded` was triggered by background release queries.
  - Implemented `is_version_older(remote_version_str, current_version_str)` for accurate semantic version tuple evaluation.
  - Restored full interactive visibility of the historical release selector dropdown (`QComboBox`) in the "Check for Updates" dialog.
- **Full Project Version Alignment**:
  - Synchronized `v2.9.5` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, `metadata.json`, `index.html`, `transcript_story.py`, and plugin manifests (`wordpress`, `youtube`, `translation`).
  - Added the incremental point release policy to project instructions (`AGENTS.md` and `GEMINI.md`).

## v2.9.4
- **Version Rollback & Historical Release Selector (Updater Engine)**:
  - Upgraded the "Check for Updates" dialog (`updater.py`) with an interactive historical release selector dropdown (`QComboBox`).
  - Fetches and displays all available GitHub releases with real-time release notes rendering in `QTextBrowser` upon selecting any past or current version.
  - Dynamically updates action button context and labels: "Update to v...", "Reinstall v...", or "Rollback to v...".
  - Implemented a safety warning modal confirmation dialog (`_confirm_downgrade`) when selecting an older version than currently installed to protect against configuration and project data incompatibilities.
- **Full Project Version Alignment**:
  - Synchronized `v2.9.4` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, `metadata.json`, `index.html`, `transcript_story.py`, and plugin manifests (`wordpress`, `youtube`, `translation`).

## v2.9.3
- **CI/CD Version Tag Synchronization**:
  - Fixed workflow release packaging to dynamically extract the release version from git tags (`GITHUB_REF_NAME`) or manual workflow inputs rather than falling back to stale local files.
  - Injected `BUILD_VERSION` into all platform build jobs (`build-plugins`, `build-windows`, `build-macos`, `build-linux`) in `.github/workflows/build.yml`.
- **Dynamic Build System Overrides**:
  - Enhanced `build_installer.py` with `--version <version>` CLI parameter and `BUILD_VERSION` environment variable support.
  - Automatically updates Inno Setup compilation flags, Debian packaging names, and distributable artifact filenames to match the active build tag.
- **In-App Updater Release Asset Verification**:
  - Added real-time asset filename inspection to `updater.py` in `_on_update_available`.
  - Displays a warning notice if a remote GitHub release tag contains binary assets labeled with an mismatched version, guiding users before downloading.
- **Full Project Version Alignment**:
  - Synchronized `v2.9.3` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, `metadata.json`, `index.html`, `transcript_story.py`, and plugin manifests (`wordpress`, `youtube`, `translation`).

## v2.9.2
- **Documentation Alignment & Post-Plugin Architecture Audit**:
  - Reconciled `STABILITY_NOTES.md` and `BUILD_INSTRUCTIONS.txt` to remove stale references claiming Hugging Face `Transformers` is tested in the core frozen binary, documenting that it lives strictly within the isolated `plugins/translation/` virtual environment.
  - Aligned core application runtime documentation with the modular post-plugin architecture.
- **WeSpeaker ONNX Embedding Engine Clarification**:
  - Confirmed and documented `wespeakerruntime` in `requirements.txt` and `radio_tv_story_segmenter_worker.py` as the dedicated, high-performance ONNX speaker voice embedding engine (`wespeaker_rt.Speaker(lang="en")`) for speaker diarization.
- **Repository Hygiene & Release Governance**:
  - Maintained `.gitignore` patterns preventing temporary build artifacts and virtual environments from being tracked.
  - Enforced release archive distribution governance via GitHub Releases.
- **Version Alignment**:
  - Bumped application version to `v2.9.2` across `prs_shared.py`, `updater.py`, `build_installer.py`, `RadioTVStorySegmenter.iss`, `package.json`, plugin manifests (`wordpress`, `youtube`, `translation`), metadata, and documentation.
- **Version-Tagged Plugin Packaging & Asset Standardization**:
  - Standardized plugin release assets to exclusively publish version-tagged `.rtvs-addon` packages (`rtvs-plugin-{id}-v{version}.rtvs-addon`) along with matching `.zip` archives.
  - Updated `build_installer.py` and `plugins/manager.py` to eliminate redundant unversioned asset duplication on GitHub Releases while ensuring robust local fallback behavior.

## v2.9.1

- **Seamless App Upgrade Plugin Synchronization**:
  - Automatically checks and upgrades installed plugins in the user directory when a newer bundled version is shipped with an application update.
  - Ensures existing users who upgrade the desktop application automatically receive all updated core plugin features without requiring manual reinstallation.
- **Independent Plugin Update Checker ("Check for Updates...")**:
  - Added a dedicated **Check for Updates...** action to the Plugin Manager (`Tools > Manage Plugins & Add-ons`), enabling users to check GitHub releases for newer versions of installed plugins and update them in-place without needing to rebuild or reinstall the core application.
  - Automatically compares installed plugin versions against the latest release assets published on GitHub (`.rtvs-addon` and `.zip` packages).
  - Displays a detailed update summary showing current vs. remote versions (e.g. `WordPress Publisher: v2.8.0 -> v2.9.1`) with one-click batch updating.
- **Enhanced In-App Plugin Browser & Update Actions**:
  - Updated the GitHub Plugins Browser dialog to detect when an installed plugin has a newer version available on GitHub, showing highlighted `Update Available (v...)` badges.
  - Added dedicated **Update to v...** action buttons for each outdated plugin, along with an **Update All Available** batch button on the toolbar.
  - Automatically reloads updated plugins dynamically and refreshes export menus immediately upon installation without requiring an app restart.
- **WordPress Publisher Plugin Custom Header / Footer Notices**:
  - Added custom header/footer text areas with placement selection (top or bottom of post).
  - Added search engine directive suppression (`data-nosnippet="true"` and `<!--googleoff: all-->...<!--googleon: all-->`) to prevent disclaimer text from overriding search engine result snippets while keeping the article fully indexable.
  - Added WordPress excerpt exclusion to keep post summaries clean in theme archives.
  - Added **Save Text & Options as Default** to persist custom notice text across all future posts.
- **Export UI Stability & Widget Proxy Fix**:
  - Fixed `AttributeError: 'ResizableTextEdit' object has no attribute 'setPlaceholderText'` by implementing complete `QTextEdit` method forwarding (`setPlaceholderText`, `placeholderText`, `clear`, `text`, `document`, and dynamic `__getattr__` delegation) on `ResizableTextEdit`.
- **Independent Modular Plugin Build & Packaging Tooling**:
  - Added `--plugin <name>` CLI option to `build_installer.py` (e.g., `python build_installer.py --plugin wordpress`) to package `.rtvs-addon` packages independently of the full installer.
  - Updated CI/CD workflow (`.github/workflows/build.yml`) to support standalone plugin builds.

## v2.8.7
- **Speaker Detection & Diarization Native Runtime Resolution**:
  - Resolved `ImportError: numpy._core.multiarray failed to import` during Speaker Detection / Diarization execution in frozen and installed Windows environments.
  - Dynamically registers all bundled C-extension dependency locations and native `.libs` directories (`numpy.libs`, `scipy.libs`, `sklearn.libs`, `wespeakerruntime`) in `_setup_windows_dll_directories()` and the PyInstaller Windows runtime hook (`torch_dll_hook.py`) via `os.add_dll_directory` and `PATH`.
  - Added explicit packaging collection flags (`--collect-all`, `--copy-metadata`, and `--hidden-import`) for `numpy`, `scipy`, `sklearn`, `wespeakerruntime`, `diarize`, and `torchaudio` across both primary GUI and standalone worker (`prs_worker`) PyInstaller builds.
  - Expanded worker `--self-test` diagnostic validation during CI/CD build staging to fully import the entire Diarization pipeline (`diarize.embeddings`, `diarize.clustering`, `diarize.vad`, `diarize.utils`, `wespeakerruntime`, and `sklearn.cluster`) before installer generation.
- **Dependency & Build Alignment**:
  - Pinned runtime and build dependencies for `scikit-learn>=1.4.0,<1.6.0`, `scipy>=1.11.0,<1.15.0`, `numpy>=1.26.0,<2.0.0`, and `wespeakerruntime>=1.0.0,<2.0.0` to guarantee binary ABI compatibility across ML modules.
- **Version Alignment**:
  - Bumped application version to `v2.8.7` across application constants (`prs_shared.py`), installer scripts (`RadioTVStorySegmenter.iss`), plugin manifests (`youtube`, `wordpress`, `translation`), metadata, and changelog viewers.

## v2.8.6
- **Real-Time Streaming OPUS-MT Model Downloads**:
  - Replaced blocking snapshot downloads with a direct chunked streaming downloader using standard Python libraries, eliminating frozen progress states and prerequisite dependencies.
  - Added live download percentage and transfer size counters (`Downloading model.safetensors (34 / 120 MB)`).
  - Integrated dynamic sibling file discovery via the Hugging Face API to ensure all required configuration, tokenizer, and weight files are acquired cleanly.
- **Persistent Progress & Stage Visualization**:
  - Decoupled the top execution panel, progress bar, and cancel button from the timeline canvas in `ui_layout.py` so processing, downloads, and translation stages stay visible when the timeline is hidden.
- **Pipeline Translation Staging & Prompting**:
  - Automatically checks for model availability when translation is included in processing workflows and prompts users for one-click download.
  - Enhanced error recovery and stage resetting on cancellation or missing prerequisites.
- **Translation Runtime & Dependency Cleanup**:
  - Added the `translate` isolated environment into the **Manage Models** dialog for disk usage tracking, manual removal, and reinstallation.
  - Prompts to remove unused translation runtime dependencies when all translation models are uninstalled.
  - Automatically purges isolated virtual environments and model caches when uninstalling the Translation plugin in the Plugin Manager.
- **Version Alignment**:
  - Bumped application version to `v2.8.6` across application constants, installer scripts, plugin manifests, and update handlers.

## v2.8.5
- **Customizable Keyboard Shortcuts**:
  - Integrated a dedicated **Keyboard Shortcuts** customization page into the Preferences dialog (`Settings > Preferences > Keyboard Shortcuts`).
  - Added a direct **Settings > Customize Keyboard Shortcuts...** menu item (`Ctrl+K` / `Cmd+K`) to jump straight to the shortcut editor.
  - Added an interactive **Key Sequence Recorder** widget allowing users to press any key or combination (with Ctrl, Alt, Shift, Meta/Cmd) or clear assignments.
  - Added real-time shortcut conflict / collision detection warning when a key sequence is already assigned to another action, with single-click reassignment.
  - Added search filtering and category dropdown filtering across File & Project, Edit, Panels & Views, AI Pipeline & Tools, Settings & Diagnostics, Help, and Playback & Navigation.
  - Added "Reset Selected" and "Reset All to Defaults" buttons, and integrated "Keyboard Shortcuts" into the "Restore System Defaults..." dialog.
  - Linked the "Customize Shortcuts..." button directly into the Quick Shortcuts Reference dialog (`F1` / `Cmd+?`).
  - Implemented dynamic live rebinding across `MainWindow` actions, `QShortcut` instances, and playback event filters without requiring application restart.
- **Documentation & Version Alignment**:
  - Updated application version to `v2.8.5` across `prs_shared.py`, `package.json`, `updater.py`, `build_installer.py`, Windows Inno Setup script (`RadioTVStorySegmenter.iss`), and `README.md`.
- **Conditional Whisper Speed / Quality Setting**:
  - Dynamically hides the **Transcription Speed / Quality** setting (`whisper_beam_size`) in Preferences whenever non-autoregressive models (such as Parakeet ONNX) are selected, displaying it exclusively for Whisper models.
- **Multi-Select & Batch Operations in Plugin Manager**:
  - Added multi-selection support with item checkboxes and batch actions in both the GitHub Plugins Browser and Local Plugin Manager.
  - Added batch toolbar actions: **Select All**, **Deselect All**, **Download & Install Selected**, **Enable Selected**, **Disable Selected**, and **Uninstall Selected**.
  - Added multi-package add-on import and batch export capabilities.
- **Translation Model Staging & Verification Resilience**:
  - Fixed snapshot download verification in `TranslationWorker` to check required file presence before checking `.complete` marker, ensuring successful Hugging Face transfers complete without unnecessary fallback retries.

## v2.8.3
- **Non-Blocking Translation Runtime Setup**:
  - Moved initial isolated translation runtime environment provisioning (`manager.ensure_environment`) off the main Qt GUI thread to a background `QThread` (`TranslationEnvSetupWorker`).
  - Added fast-path verification so up-to-date environments start immediately without setup overhead.
  - Connected real-time status and activity logging with cancellation and graceful thread cleanup support in `stop_translation_worker()`.
- **Documentation & Legal Compliance**:
  - Reconciled `README.md`, `NOTICES.txt`, and `BUILD_INSTRUCTIONS.txt` to reflect the active `diarize` (Silero VAD + WeSpeaker ONNX) diarization engine and on-demand Windows NVIDIA CUDA acceleration.
  - Added formal third-party license notices for `diarize`, `sherpa-onnx`, `WeSpeaker`, `onnxruntime`, `scipy`, `scikit-learn`, `cryptography`, and `keyring`.
- **Repository Hygiene**:
  - Added archive patterns (`*.zip`, `*.tar.gz`, `*.7z`) to `.gitignore` to prevent snapshot zips from polluting repository history.
- **Version Alignment**:
  - Updated application version, installer scripts, plugin manifests, and documentation to v2.8.3.

## v2.8.2
- **Isolated Runtime Mount Point & Link Mode Resilience**:
  - Resolved `[TRANSLATION ERROR] Failed to create Python minor version link directory (os error 448: The path cannot be traversed because it contains an untrusted mount point)` during translation runtime and OPUS-MT model installation on Windows.
  - Enforced `UV_LINK_MODE="copy"`, `UV_CACHE_DIR`, and `UV_DATA_DIR` across all `uv` environment creation (`uv venv --link-mode copy`) and package installation (`uv pip install --link-mode copy`) steps, preventing junction and symlink traversal failures on redirected or OneDrive-synced user directories.
  - Added self-healing runtime discovery (`_find_extracted_python`) in `RuntimeManager` that detects and verifies extracted Python interpreters even if post-install junction links report mount-point errors.
  - Added direct standalone CPython 3.12 download and pure archive extraction fallback (`python-build-standalone`) when junction-based package management is blocked by OS security policies.
  - Upgraded standalone `uv` toolchain version to `0.12.12`.
- **Version Alignment**:
  - Updated application version, installer scripts, and plugin manifests to v2.8.2.

## v2.8.1
- **Default Transcription Model**:
  - Set `Parakeet ONNX Fast TDT` as the out-of-the-box default transcription model across settings stores, preference dialogs, batch jobs, and project initializations.
  - Reordered model selectors across the application to prioritize Parakeet ONNX for ultra-fast, local English transcription.
- **Worker DLL Resolution in Frozen Builds**:
  - Resolved `[PYI-17568:ERROR] Failed to load Python DLL python312.dll` on Windows during transcription and diarization by prioritizing the top-level `prs_worker.exe` located directly alongside the `_internal/` dependency tree.
  - Prevented PyInstaller onedir binary placement inside `workers/` without an adjacent `_internal/` directory, and added automatic cleanup of legacy worker binaries in Windows installer upgrades.
- **Model Downloader Reliability**:
  - Implemented real-time chunked streaming downloads for Whisper and Parakeet models in `WhisperModelInstallWorker`, replacing stalled opaque downloads with live byte/MB counters and percentage tracking.
  - Resolved frozen-process `NoneType.write` crashes on clean Windows installs by introducing `NullWriter` stream guards and disabling terminal progress bars (`tqdm`, `huggingface_hub`) in GUI environments.
  - Removed deprecated `resume_download` and `local_dir_use_symlinks` parameters to eliminate modern `huggingface_hub` UserWarnings.
  - Hardened file finalization with atomic `os.replace` operations across temporary `.download` artifacts to prevent Windows file-sharing errors.
  - Added non-zero integrity checks (`stat().st_size > 1024`) in model availability verification to prevent interrupted 0-byte files from being identified as valid installations.
- **Translation Staging & Add-on Delivery**:
  - Added multi-file HTTP streaming fallback for all standard OPUS-MT assets (`config.json`, tokenizers, `source.spm`, `model.safetensors`, and `pytorch_model.bin`).
- **Tools Menu Accessibility**:
  - Added direct **Tools > Manage AI Models...** menu entry alongside existing Preferences navigation.
- **Version Alignment**:
  - Updated application, installer scripts, and plugin manifests to v2.8.1.

## v2.8.0
- Updated application and plugin versions to v2.8 across core, installers, and manifests.
- **Decoupled Translation Worker from PySide6**: Isolated translation runtime no longer requires or installs PySide6. Implemented a pure-Python `Signal` descriptor and `QObject` fallback in `worker.py` and guarded `QCoreApplication` in `runtime_entry.py`.
- **Dynamic Plugin Runtime Requirements**: `RuntimeManager` now dynamically reads `requirements-runtime.txt` from plugin directories rather than relying strictly on static configuration.
- **CPU PyTorch Wheel Configuration**: Isolated translation environment utilizes `--extra-index-url https://download.pytorch.org/whl/cpu` to avoid multi-gigabyte CUDA wheel downloads on CPU-only machines.
- **Cross-Platform `uv` Provisioning**: Added standalone `uv` binaries for Windows (x86_64, arm64), macOS (x86_64, arm64), and Linux (x86_64, aarch64) in `build_installer.py`, enabling automated managed Python provisioning across all platforms.
- **Enhanced Diagnostic Reporting**: Added detailed subprocess error capture in `RuntimeManager` and surfaced detailed error diagnostics in the translation UI.
- **Synchronized Plugin Add-on Archives**: Updated and re-packaged `.rtvs-addon` packages (`translation`, `wordpress`, `youtube`) and enhanced `PluginManager.ensure_packaged_addons()` to auto-refresh outdated archives when plugin source manifests change.

## v2.76c
- Reworked the plugin architecture around explicit core/shared versus isolated runtimes.
- Moved the OPUS-MT translation worker implementation out of the core application.
- Translation now runs through the plugin-owned isolated Python runtime.
- Removed translation-only `transformers`, `sentencepiece`, and `sacremoses` dependencies from the core Python requirements and core PyInstaller collection.
- Added `plugins/translation/requirements-runtime.txt` and isolated runtime metadata.
- Translation models are owned by the translation plugin's model registry and are hidden from Manage Models when the plugin is uninstalled.
- Uninstalling the translation plugin removes its isolated runtime but deliberately preserves downloaded translation models.
- Fixed Preferences category navigation so aliases such as `Models`, `AI Models`, `Detection`, and `Batch` select the correct page.
- WordPress and YouTube remain lightweight core-runtime plugins and use the same manifest architecture.
- Updated release version references to 2.76c.


## v2.7.1

### Disk Cache Management & "Clear Temporary Cache" Dialog
- **Temporary Cache Manager Dialog (`ClearCacheDialog`)**: Added a user-facing temporary cache inspection and cleanup dialog accessible via **Tools > Clear Temporary Cache...** and **Settings > Clear Temporary Cache...**.
- **Per-Store Disk Usage Breakdown**: Computes real-time file counts and storage size across:
  - **Video Thumbnails & Filmstrips**: Cached timeline thumbnail images in `%TEMP%/radio_tv_story_segmenter_thumbnails/`.
  - **Audio Waveform Peaks**: Precomputed waveform envelopes (`.peaks`) in `%APPDATA%/RadioTVStorySegmenter/cache/peaks/`.
  - **Temporary Audio Workfiles**: Temporary extracted audio tracks and work buffers (`prs_tmp_*.wav`, `rtvs_tmp_*.wav`).
- **Selective & Full Purging**: Users can selectively clear specific stores or click the primary **Clear All Caches** button to immediately reclaim all temporary disk space.
- **Bilingual Localization Support**: Full English and Spanish translation support for all cache dialog labels, feedback prompts, and menu actions.

### Build Pipeline Transparency & Real-Time Logging
- **Live Output Streaming**: Refactored `build_installer.py` subprocess runner to use unbuffered line-by-line live streaming via `subprocess.Popen(stdout=subprocess.PIPE, bufsize=1)`, eliminating log buffering delays in GitHub Actions CI runners.
- **Unbuffered Python Environment**: Configured `PYTHONUNBUFFERED: "1"` in `.github/workflows/build.yml` to ensure continuous stdout flushing across Windows, Linux, and macOS runners.
- **Stage Progress Banners**: Added explicit progress headers (`[1/5]` through `[5/5]`) and `--log-level INFO` verbosity to PyInstaller build steps, ensuring clear visibility into binary compilation stages.

### Ecosystem Version Alignment
- **Global v2.7.1 Synchronization**: Synchronized application, installer, and plugin versions across `prs_shared.py`, `package.json`, `RadioTVSegmenter.py`, `transcript_story.py`, `updater.py`, `build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `build_windows.bat`, `build_linux.sh`, `installer/Linux/build_deb.sh`, `installer/macOS/build_app.sh`, `.github/workflows/build.yml`, and all plugin manifests (`plugins/wordpress/manifest.json`, `plugins/youtube/manifest.json`, `plugins/translation/manifest.json`).

## v2.7.0

### Video Thumbnail Caching & Instant Project Reloading
- **Persistent Disk Thumbnail Caching**: Added deterministic, media-hash-keyed thumbnail disk caching (`get_video_thumbnail_cache_dir`, `read_video_thumbnail_cache`, `invalidate_video_thumbnail_cache`) in `prs_shared.py`.
- **Instant Project Restoration**: Opening a video file or reloading an existing `.rtvs` project now instantly reads cached filmstrip thumbnails directly from disk without re-extracting frames via FFmpeg.
- **Immediate Generation Preview & Track Placeholder**: Restored immediate visual feedback during thumbnail extraction, rendering a filmstrip track placeholder along with centered "Generating video thumbnails..." preview text and status banner.
- **Cache Invalidation & Manual Refresh**: Thumbnail cache automatically validates file modification timestamps (`st_mtime`) against the source video, ensuring stale frames are evicted if media is modified. Manual regeneration (**Media > Regenerate Video Thumbnails**) clears cache and re-extracts cleanly.
- **Extended Cache Retention**: Extended default background cache retention (`cleanup_old_thumbnail_cache`) from 24 hours to 7 days (168 hours) to ensure work-in-progress desktop video projects retain cached filmstrips across sessions.

### GitHub Actions Workflow Optimizations
- **All-Build Defaults**: Updated the GitHub Actions release workflow (`.github/workflows/build.yml`) `workflow_dispatch` configuration so all build checkboxes (`build_windows`, `build_macos`, `build_linux`, `plugin_wordpress`, `plugin_youtube`, `plugin_translation`, `create_release`) default to `true` (`checked`), allowing release managers to deselect targets rather than checking each one manually.

### Ecosystem Version Alignment
- **Global v2.7.0 Synchronization**: Bumped project and plugin versions to `2.7.0` across `prs_shared.py`, `package.json`, `RadioTVSegmenter.py`, `transcript_story.py`, `updater.py`, `build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `build_windows.bat`, `build_linux.sh`, `installer/Linux/build_deb.sh`, `installer/macOS/build_app.sh`, `.github/workflows/build.yml`, and all plugin manifests (`plugins/wordpress/manifest.json`, `plugins/youtube/manifest.json`, `plugins/translation/manifest.json`).

## v2.6.5

### In-Dialog Video Frame Scrubber & Thumbnail Controls
- **Interactive In-Dialog Timeline Scrubber**: Added an interactive horizontal slider, precision step buttons (`◀ -1s`, `◀ -1f`, `+1f ▶`, `+1s ▶`), live timestamp readout (`hh:mm:ss.zzz`), and a `⟳ Playhead` synchronization button directly inside both WordPress and YouTube export panels in `UnifiedExportDialog`.
- **Debounced Frame Previews**: Enabled responsive thumbnail capture with a 120ms debounce timer for smooth in-dialog scrubbing without freezing the UI.
- **Audio-Only Project Protection**: Automatically detects audio-only projects and disables "Grab frame from video" with helpful guidance tooltips, defaulting gracefully to "None", "Automatic", or custom image browse modes.

### Process Hardening & Temporary Asset Cleanup
- **FFmpeg Subprocess Timeouts**: Added 5-second timeouts and `TimeoutExpired` exception handling to all FFmpeg thumbnail extraction calls in `project_export.py`, preventing freezes on corrupted or unresponsive media.
- **Temporary Preview File Lifecycle**: Added automated tracking and purging of temporary preview files (`rtvs_wp_frame_*.jpg`, `rtvs_yt_frame_*.jpg`) on dialog cancellation or closure.

### Timeline Thumbnail Density Optimization
- **Increased Frame Extraction Density**: Increased `VideoThumbnailWorker` extraction count ceiling from 48 to 80 frames for richer visual coverage across long media files.
- **Aspect-Ratio-Preserving Density Tuning**: Optimized timeline thumbnail rendering dimensions with reduced horizontal scaling minimums and a 2.0px minimum gap, displaying more visual frames simultaneously without cropping images.

### Version Synchronization
- **Ecosystem Version Alignment**: Bumped project and plugin versions to `2.6.5` across `prs_shared.py`, `package.json`, `RadioTVSegmenter.py`, `transcript_story.py`, `updater.py`, `build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `plugins/wordpress/manifest.json`, `plugins/youtube/manifest.json`, and `plugins/translation/manifest.json`.

## v2.6.0

### Modular Plugin System
- **Plugin Management Engine**: Introduced modular plugin architecture (`plugins/manager.py`) with `BasePlugin`, `PluginManifest`, and `PluginManager` supporting auto-discovery, lifecycle controls, and dynamic loading from both bundled and user-level plugin directories.
- **WordPress Publisher Plugin**: Migrated WordPress publishing capabilities into a modular add-on (`plugins/wordpress/`) with category/tag syncing, excerpt formatting, featured image uploads, and background worker threads.
- **YouTube Video Publisher Plugin**: Implemented dedicated YouTube publisher plugin (`plugins/youtube/`) featuring OAuth 2.0 PKCE authentication with local callback server, chunked resumable video uploads, metadata/tag management, video frame thumbnail capture, and privacy settings.
- **Language Translation Plugin**: Encapsulated local neural machine translation into a modular add-on (`plugins/translation/`) with MarianMT and NLLB models and bilingual split-view editing.
- **Dynamic UI Menus**: Added dynamic action populator for `File -> Publishing & Plugins` and dynamic tool entries under `Tools`, plus the `Tools -> Manage Plugins & Add-ons...` management dialog.

### Project Storage & Backward Compatibility
- **Forward & Backward Compatibility**: Enhanced `.rtvs` project serialization and `Story` models with extensible `metadata` and top-level `plugins_data` dictionaries. Projects created in v2.6.0 open seamlessly in v2.5.2 without parsing errors, and legacy projects open in v2.6.0 without data loss.

### CI/CD Workflow & Selective Build Matrix
- **Selective Plugin Packaging & Building**: Extended `build_installer.py` and GitHub Actions (`.github/workflows/build.yml`) with build target options (`Core App + Selected Plugins`, `Core App Only`, and `Plugins Only`) and individual plugin checkboxes (`plugin_wordpress`, `plugin_youtube`, `plugin_translation`).
- **Standalone Release Artifacts**: Generated standalone `.zip` packages for each plugin (`rtvs-plugin-<id>-v2.6.0.zip`) ready for direct release distribution or in-app installation.
- **Version Bump**: Bumped version to `2.6.0` across `prs_shared.py`, `RadioTVSegmenter.py`, `media_batch.py`, `playback_preferences.py`, `updater.py`, `build_installer.py`, `build_windows.bat`, `build_linux.sh`, `installer/Windows/RadioTVStorySegmenter.iss`, `installer/Linux/build_deb.sh`, `installer/macOS/build_app.sh`, `.github/workflows/build.yml`, `package.json`, and all plugin manifests.

## v2.5.2

### Timeline Video Thumbnails Layout & Vertical Resizing
- **Thumbnails Positioned Below Waveform**: Relocated the video thumbnail track in `TimelineCanvas` so that thumbnails render cleanly beneath the audio waveform rather than above or overlaying it.
- **Dynamic Vertical Resizing**: Replaced the static thumbnail scaling constraints with dynamic aspect-ratio-aware dimensions that automatically expand and contract proportionally as the user resizes the timeline widget vertically.
- **Track Separation**: Added a subtle boundary divider between the audio waveform and video thumbnail strips for clear visual segmentation.
- **Higher Resolution Thumbnails**: Increased thumbnail extraction scale to 320px width (`scale=320:-2`) to keep video frames sharp and clear on high-DPI displays and enlarged timeline heights.
- **Preferences Configuration**: Added a "Thumbnail Placement" option under Preferences (Playback & Timeline) allowing users to choose between "Below audio waveform" (default) or "Above audio waveform".

### Automated Windows Installer & Version Synchronization
- **Strict Version Synchronization**: Updated `build_installer.py` with `sync_installer_scripts()` to automatically rewrite and verify the `#define MyAppVersion` directive in `installer/Windows/RadioTVStorySegmenter.iss` from the project's single source of truth (`PROJECT_VERSION` in `prs_shared.py`).
- **Direct Inno Setup Compilation Support**: Integrated automated detection and invocation of `ISCC.exe` into `build_installer.py`, compiling the Windows installer executable with `/DMyAppVersion="{PROJECT_VERSION}"` without relying on manual command-line flags.
- **Resilient Batch Extraction**: Hardened `build_windows.bat` to detect and use the active `!PYTHON_EXE!` runtime with regex extraction directly from `prs_shared.py`, preventing fallback issues when executing the Inno Setup compiler.
- **Version Bump**: Bumped version to `2.5.2` across `prs_shared.py`, `RadioTVSegmenter.py`, `media_batch.py`, `playback_preferences.py`, `updater.py`, `build_installer.py`, `build_windows.bat`, `build_linux.sh`, `installer/Windows/RadioTVStorySegmenter.iss`, `installer/Linux/build_deb.sh`, `installer/macOS/build_app.sh`, and `.github/workflows/build.yml`.

## v2.5.1

### Version Bump & Maintenance
- **Version Alignment**: Bumped project version to `2.5.1` across core modules, packaging scripts, and CI workflows.

## v2.4.2

### Timeline Interaction & Boundary Protection
- **Protected Timeline Boundary Handles**: Disabled accidental boundary modifications caused by left-clicking and dragging story edge handles in the timeline. Left-clicks across the timeline now exclusively handle playback seeking and audio scrubbing.
- **Explicit Right-Click & Button Boundary Adjustments**: Timeline boundary adjustments now require deliberate user actions:
  - Right-clicking and dragging a story's boundary handle directly resizes that boundary with undo/redo snapshotting.
  - Right-clicking and dragging across any timeline segment creates a selection region that can be quickly assigned with "Set Story Start" or "Set Story End".
  - Hovering over a story boundary handle displays an informative tooltip (`Right-click and drag to adjust`).
- **Version Synchronization**: Bumped version to `2.4.2` across `prs_shared.py`, `RadioTVSegmenter.py`, `build_installer.py`, `updater.py`, `package.json`, Windows Inno Setup, Linux Debian packaging, macOS bundling, and GitHub Actions CI workflows.

## v2.4.1

### Features & Story Boundary Controls
- **Set Story Start & End Buttons**: Restored dedicated "Set Story Start" and "Set Story End" action buttons in the Stories & Segments widget.
- **Contextual Timestamp Snapping**: Pressing either button sets the story's start or end boundary to match the current interaction position across the transcript and timeline:
  - Active timeline drag selections and highlighted transcript text ranges are prioritized.
  - Active transcript cursor positions and playback/waveform playhead locations are seamlessly detected and converted into precise story boundaries.
- **Dynamic Resizing & Contextual Visibility**: The boundary buttons appear cleanly above the Add, Select All, Delete, and Export buttons exclusively when a single story is selected. When multiple stories or no stories are selected, the buttons and their container are collapsed entirely with zero dead vertical space.
- **Full Undo/Redo & State Integration**: Boundary adjustments are committed into the unified project undo/redo stack (`Ctrl+Z` / `Ctrl+Shift+Z`), immediately refreshing the story list, time range inputs, timeline story regions, and autosave state.
- **Version Synchronization**: Bumped version to `2.4.1` across `prs_shared.py`, `RadioTVSegmenter.py`, `build_installer.py`, `updater.py`, `package.json`, build scripts, and CI workflows.

## v2.4

### Bug Fixes & Stability
- **Startup Crash Fix**: Fixed `NameError: name 'ffprobe_path' is not defined` in `ui_layout.py` by properly importing `ffprobe_path` from `prs_shared.py`, preventing an application crash during external dependency initialization.
- **Dependency Manifest Alignment**: Added `torchaudio>=2.0,<2.4` and `soundfile>=0.12.1` to `requirements.txt` to ensure standalone/manual Python environment installations include all packages directly imported by the application.

### CI/CD & Build Pipeline Security
- **GitHub Actions Script Injection Fix**: Eliminated the script injection vulnerability in `.github/workflows/build.yml` by routing the workflow's `${{ inputs.release_tag }}` input safely through environment variables (`env:`) rather than inline shell script string interpolation.
- **Release Integrity Guard**: Updated the `publish-release` job condition to require `!contains(needs.*.result, 'failure')`, ensuring GitHub Releases are never published if any platform build (Windows, macOS, Linux) fails.
- **Windows Build Timeout Margin**: Increased the Windows CI build job timeout to 75 minutes to provide a reliable buffer against runner timeouts.
- **Balanced Inno Setup Compression**: Optimized Windows installer packaging in `RadioTVStorySegmenter.iss` using `lzma2/max` with a 16MB dictionary size, delivering 50–70% faster Windows compression times on CI runners while retaining a compact installer binary.
- **Version Synchronization**: Unified version `2.4` across all core application modules, installer configurations, build scripts, and package descriptors.

## v2.3

### Installer Size & Package Optimization
- **Shared Runtime Architecture**: Eliminated the duplicate `_internal` distribution previously bundled inside `workers/`, deduplicating hundreds of megabytes of identical PyTorch, Transformers, CTranslate2, and ONNX Runtime runtimes into a unified application core shared seamlessly by both the GUI application and the AI worker (`prs_worker`).
- **Enhanced Pruning Pipeline**:
  - Removed unneeded C/C++ development headers, build artifacts, and package metadata (`torch/include`, `torchaudio/include`, `scipy/include`, `PySide6/include`, `onnxruntime/include`, etc.).
  - Stripped unused PySide6 runtime plugins (e.g., `sqldrivers`, `sensorgestures`, `qmltooling`, `geometryloaders`, `position`, `scenegraph`) and translation tables.
  - Purged `.pdb`, `.pyi`, `.c`, `.cpp`, `.h`, `.hpp`, `.pyx`, `.pxd` source and debug files, along with internal test and benchmark suites across all bundled packages.
  - Enabled binary symbol stripping on Linux (`strip --strip-unneeded`) and macOS (`strip -x`).
- **Maximum Installer Compression**:
  - **Windows**: Upgraded Inno Setup packaging to `lzma2/ultra64` compression with separate 64-bit multi-threaded compression process and maximum dictionary size (64MB).
  - **Linux**: Upgraded Debian packaging (`build_deb.sh`) to `dpkg-deb -z9` (maximum XZ compression) and distributable tarball packaging to `GZIP=-9`.
  - **macOS**: Upgraded DMG image generation (`build_app.sh`) with `hdiutil` maximum compression (`-imagekey zlib-level=9`).

### Codebase Cleanup & Conflict Prevention
- **Eliminated Duplicate Methods**: Removed the redundant `_check_external_dependencies` implementation in `RadioTVSegmenter.py` and unified dependency validation in `ui_layout.py`.
- **Dynamic Application Metadata**: Refactored the "About" dialog to use dynamic version and application name constants (`APP_DISPLAY_NAME`, `PROJECT_VERSION`) from `prs_shared.py` instead of hardcoded strings.
- **Dependency Manifest Cleanup**: Removed duplicate `keyring` package declaration from `requirements.txt`.
- **Version Synchronization**: Unified v2.3 versioning across `prs_shared.py`, `RadioTVSegmenter.py`, `transcript_story.py`, `updater.py`, `build_installer.py`, `build_windows.bat`, `build_linux.sh`, `installer/Windows/RadioTVStorySegmenter.iss`, `installer/Linux/build_deb.sh`, `installer/macOS/build_app.sh`, and `.github/workflows/build.yml`.

## v2.2

### Enhancements
- Updated application and installer versioning to v2.2 across Python core modules, build scripts, Windows Inno Setup scripts, and GitHub Actions workflows.

## v2.1.6

### Windows packaging/runtime reliability
- Build a dedicated `prs_worker` PyInstaller executable instead of falling back to the GUI executable for local AI processing.
- Add a PyInstaller Windows runtime hook for PyTorch, CTranslate2, ONNX Runtime, and related native DLL search paths.
- Add frozen-build AI self-tests for PyTorch, its `_C` native extension, CTranslate2, Transformers, and Silero VAD.
- Make the build fail before creating an installer when the frozen AI runtime cannot initialize.
- Preserve the complete worker `_internal` runtime instead of pruning native ML libraries from it.

## v2.1-stable

- **Timeline now themes with Light and High Contrast modes** (previously covered in the earlier changelog entry).
- **Fixed**: opening a new media file skipped an intended immediate duration probe (`probed_duration` was always `None`, dead code left over from an earlier refactor) -- the timeline could briefly show a stale or zero duration until the media player's own async duration signal arrived a moment later. Restored the probe and reduced its worst-case timeout from 15s to 5s.
- **Fixed**: `safe_filename()` (used for exported story/project folder and file names) didn't guard against an input that sanitizes down to nothing but dots -- a folder-name prompt or a project file's own story title of ".." could resolve one directory level *above* the intended export location instead of into a new subfolder. Dot-only results now fall back to a safe default name.

## v2.1.0-beta

- **Visual Theme Refresh**: Refined the dark visual system with layered charcoal/slate surfaces, restrained cyan interaction accents, cleaner borders, rounded controls, minimalist scrollbars, modern menus, and cohesive focus/selection states.
- **Waveform Presentation**: Refined waveform/ruler styling and moved the audio filename into a subtle metadata badge in the ruler margin.
- **Transcript Typography**: Added persistent transcript font-size controls with increase, decrease, and reset actions. Supports `Ctrl/Cmd + +`, `Ctrl/Cmd + -`, and `Ctrl/Cmd + 0`.
- **Transcript Readability**: Improved typography, active-selection treatment, speaker/timestamp presentation, and transcript visual hierarchy without changing the existing transcript layout.

# Changelog

## v1.9.9

- **Adjustable Custom Defaults**: Added "Save as Custom Defaults" buttons to each sub-menu in the preferences dialog, allowing users to save custom defaults that override original system defaults. Updated the reset preference option to "Restore System Defaults" to restore original factory defaults.
- **Updated Story Detection Default**: Changed the default story detection silence threshold to 3.0s.
- **Silero VAD Debug Cleanup**: Removed [STORY DEBUG] print statements from codebase.
- **Unified Application Version 1.9.9**: Synchronized version 1.9.9 across application constants, local PyInstaller/Inno Setup/Debian/macOS builders, GitHub Actions release workflows, documentation, and update verification manifests.

## v1.9.8

- **Resilient Multi-Stage Speaker Detection Progress**: Replaced brittle percentage-drop heuristics with keyword-based stage mapping across VAD, embedding extraction, and speaker clustering stages. Added monotonic percentage scaling with an upper safety ceiling (99%) to eliminate progress jumps and stalling during diarization.
- **Unified VAD Story Detection Pipeline**: Standardized story auto-detection on the Silero VAD audio pipeline with adaptive silence thresholding, 80% silence scaling margin, minimum story duration filters (5s), and music/sound token sanitization (`MUSIC_TOKEN_RE`).
- **Sequential Story Indexing**: Fixed story title generation to use contiguous sequential numbering (`Story 1`, `Story 2`, ...) even when transient sub-5-second audio blips are filtered out.
- **Unified Application Version 1.9.8**: Synchronized version 1.9.8 across the application constants, local PyInstaller/Inno Setup/Debian/macOS builders, GitHub Actions release workflows, documentation, and update verification manifests.

## v1.9.6

- **Moved WordPress settings into Preferences**: Site URL, Username, App Password, and Test Connection now live under Preferences > WordPress. The standalone "WordPress Export Settings..." menu item has been removed; the contextual "WordPress Settings..." button inside the Export dialog is unchanged and uses the same underlying settings.
- **Manage Models**: labeled the two Whisper models and the Parakeet model that are English-only ("Distil-Whisper Large v3 (English)", "Parakeet ONNX Fast TDT (English)") -- verified against each model's documentation rather than assumed.
- **Security**: sanitized update-download filenames and validated destination paths against directory traversal; restricted update downloads to official GitHub domains over HTTPS; added SHA-256 verification when a release publishes one; WordPress application passwords now use machine-derived encryption for the local-storage fallback (instead of plaintext) when no system keyring is available, with an on-screen notice when that fallback is used; project files now validate media file extensions before resolving/copying referenced media, closing a path where a malicious project file could reference and copy an arbitrary file; project file decompression is now streamed with a 200MB ceiling instead of unbounded.
- **Performance**: activity-log snapshots no longer re-serialize the full transcript/diarization/translations on every log entry -- only when a real edit occurs; first-run or upgrade installs of the local transcription/diarization environment now show a progress dialog instead of freezing the window.
- **Reliability**: the local transcription/diarization worker's stdout (JSON protocol) and stderr (diagnostic output) are no longer merged, preventing third-party library warnings from occasionally corrupting an in-flight result; WordPress export temp files now use a unique per-job directory instead of a shared fixed one; a worker-protocol-mismatch error dialog no longer shows a hardcoded, incorrect expected version number.

## v1.9.4

- **Global Multi-Stage Elapsed Time**: The progress indicator now tracks and displays elapsed time across all operations and multi-stage pipelines (including combined transcription + speaker diarization) from start to finish, rather than only during diarization.
- **Comprehensive "Restore All Settings to Defaults"**: The Restore All Defaults button in Preferences now resets all custom preferences across all areas of the application, including custom project directories, project bundling, export formats and content settings, custom export location overrides, audio output hardware and volume, AI model options, timeline preferences, detection parameters, and batch tool options.
- **New "Restore Selected Settings" Feature**: Added a dedicated "Restore Selected Settings…" dialog accessible in Preferences. Users can review customizable setting categories with checkboxes (with Select All and Deselect All convenience controls) and selectively reset only specific areas to factory defaults after a safety confirmation prompt.
- **Export Location Routing Refinement**: When using a custom export location, selected file types are saved directly to the chosen directory without creating unnecessary "Transcripts" or "Media" subfolders, keeping output clean while leaving the main project folder intact.

## v1.9.1

- Renamed user-facing Speaker Diarization references to **Detect Speakers**.
- Added an optional speaker-estimate prompt before non-batch speaker detection jobs, with a Preferences > Detection setting to ask every time or automatically use Auto-Detect.
- Open Media, Open Document, and Open Project dialogs now remember the last folder used.
- Renamed the Batch Processing translation option to **Translate** and made the selected English→Spanish, Spanish→English, or Auto-Detect direction control the actual translation output.

## v1.9.0

- Diarization engine overhaul: replaced the "Speaker Detection Sensitivity" slider (which `diarize` 0.1.2's embedding/clustering never actually read) with a "Default Expected Speakers" setting (Auto-Detect / 1 / 2 / 3+), also selectable per batch job.
- Added a solo fast-path: with 1 expected speaker, Speaker Detection now runs Silero VAD only (no WeSpeaker embedding or clustering) and, when a transcript already exists, can skip the local worker process entirely and label everything "Speaker 1" in-memory (~0.01s instead of a full detection pass).
- Speaker labels are now normalized to "Speaker 1", "Speaker 2", etc. in order of first appearance, instead of the diarize package's raw internal ids.
- Clamped OMP/ONNX Runtime thread pools (capped at 8, based on physical cores) before onnxruntime/torch/diarize are imported, to stop CPU oversubscription slowing down detection on high-thread-count machines.
- FFmpeg audio normalization for diarization now explicitly discards video/subtitle/data streams (`-vn -sn -dn -map 0:a:0?`) before decoding.
- Batch Processing dialog: "Diarize Speakers" renamed to "Speaker Detection" with an inline Expected Speakers selector; Story Detection gained inline Silence Gap / Lead-in Padding fields; "Spanish Translation" renamed to "Translation" with an explicit direction selector (Auto-Detect flips between English and Spanish based on the transcript's detected language, or force English→Spanish / Spanish→English).
- Existing projects saved by older builds that still have a `speaker_sensitivity` value load fine; the setting just falls back to "Auto-Detect" since it no longer maps to anything.

## v1.8.6
- Added a startup check for the sherpa-onnx Parakeet runtime; source/portable Python builds automatically install `sherpa-onnx>=1.13,<2` when it is missing.
- Updated the Windows/PyInstaller build to bundle the sherpa-onnx runtime.
- Fixed Parakeet token parsing so leading-space tokens are split into real words, preserving per-word timestamps and creating multiple transcript segments for speaker diarization.
- Improved Parakeet segment timing with sentence, word-count, and speech-gap boundaries so its transcript follows the same general timestamp/segment behavior as Whisper.
- Cleared the Speaker Detection progress-stage label when diarization finishes.

## 1.8.5

- Fixed persistent Transcription Model preferences so the selection survives application restart and is not overwritten by project files. Restore Defaults explicitly resets it to Small.
- Reworked Parakeet ONNX transcription to use the sherpa-onnx TDT runtime with the required encoder/decoder/joiner model bundle and automatic 80/128-feature detection.
- Activity Log exports now append the current date to the filename (`activity_log_YYYY-MM-DD.txt`).

## 1.8

- High-Speed Transcription Upgrade: Implemented dynamic CPU thread scaling for faster-whisper/CTranslate2, aligning thread pools with physical core counts to prevent hyperthread contention and SMT performance stalls.
- Configurable Greedy Decoding (`beam_size=1`): Added Transcription Speed / Quality mode selector in AI Models preferences for ultra-fast, greedy-decoding transcription passes alongside standard quality beam-search decoding (`beam_size=5`).
- Native Distil-Whisper Support: Integrated `distil-whisper/distil-medium.en` and `distil-whisper/distil-large-v3`, providing 4x to 6x faster inference on CPU with minimal accuracy trade-off.
- Parakeet / FastConformer ONNX Support: Integrated non-autoregressive NVIDIA FastConformer / Parakeet ONNX models for high-throughput speech-to-text.
- Enhanced Batch Progress Status & Dual ETAs: The batch processing progress indicator at the top of the window now displays relative progress (e.g. "File 1 of 3" or "1/3") accompanied by real-time estimated completion times for both the active file and the entire batch job.
- Batch Processing Drag and Drop: Users can now drag and drop one or more audio/video files or folders directly into the batch dialog list or input area.
- Persistent Batch Export Defaults: The app remembers last-used batch export options across sessions, with quick "Save Options as Default" and "Reset to Factory Defaults" controls in the batch dialog and Preferences.
- Native `.rtvs` Project File Association: Registered `.rtvs` project file associations across Windows (Registry progid), macOS (Info.plist), and Linux (shared-mime-info). Opening or double-clicking an `.rtvs` file directly launches and opens the project in Radio & TV Segmenter.
- Resolved Waveform Cleanup & Project Load Crash: Fixed an `AttributeError: 'TimelineCanvas' object has no attribute 'set_background_generation_active'` during project opening, media reloads, and application shutdown.
- Unified application version to 1.8 across all installers, package builders, update manifests, metadata, and documentation.

## 1.7

- Enhanced Transcript Selection Ergonomics: Distinguish between single click (move playback cursor / seek) and click-and-drag (select text range), preventing accidental word snapping or unwanted selections.
- Added Right-Click Drag Selection: Support selecting text by clicking and dragging with the right mouse button in addition to the left mouse button.
- Added "Clear Selection" Context Menu Action: Users can now un-select active transcript highlights directly from the right-click context menu or by pressing `Esc`.
- Configurable Multi-Selection Workflow: Added "New Text Selection Behavior" preference under Settings > Preferences > Playback & Timeline to choose between replacing previous selections (Single Selection) or preserving multiple concurrent selections (creating separate stories for each selected section).
- Translation Language Selector Fix: Resolved an issue where the transcript drop-down only displayed "English (Original)" after completing a translation. Fixed premature stale-status invalidation, enabled seamless switching between English, Español (Translation), and Bilingual (Split) views, and preserved translation state across project loads and undo actions.
- Unified application version to 1.7 across all platform installers, update manifests, metadata, and documentation.

## 1.63

- Streamlined Linux packaging: Added dedicated Debian/Ubuntu package builder (`RadioTVSegmenter-1.63-Linux-amd64.deb`) with complete FreeDesktop desktop launcher, system MIME-type handlers, application icons, and maintainer scripts.
- Solved Linux release asset size constraints (<2GB GitHub release limit): Enforced explicit CPU-only PyTorch wheel resolution to eliminate accidental multi-gigabyte CUDA runtime inclusions during Linux CI builds.
- Added aggressive non-runtime asset pruning (C++ headers, unit tests, debug symbols, type stubs) and Linux ELF binary stripping (`strip --strip-unneeded`) to reduce package footprint.
- Enhanced in-app updater to prioritize `.deb` package downloads on Debian/Ubuntu systems with native system package manager integration (`xdg-open`).
- Unified application version to 1.63 across all platform installers, update manifests, metadata, and documentation.

## 1.6.1

- Fixed: a custom AI model storage directory set in Preferences was not honored on the next app launch — startup always reset the Hugging Face cache location (`HF_HOME`) back to the default app-data folder, so new model downloads (and the Manage Models listing) could silently disagree with the configured directory.
- Fixed: closing the "Check for Updates" dialog while the initial GitHub check was still in flight could cause its background worker to emit into an already-closed dialog.
- Fixed: launching the downloaded installer on Windows no longer goes through `cmd.exe` (`shell=True`), avoiding a class of path-quoting risk.
- Fixed: removing a speaker label now only reassigns diarization data that actually belonged to the removed speaker in that time window, instead of any diarization segment that merely overlapped it (which could mislabel a different speaker's audio during cross-talk).

## 1.5

- Added integrated "Check for Updates" feature querying GitHub releases with automatic OS binary matching (.exe for Windows, .dmg for macOS, .tar.gz for Linux).
- Non-blocking download and automatic installer execution with safe application shutdown.
- Configurable model download and storage directory in Preferences, with direct link from Manage Models dialog.
- Redesigned Preferences dialog with a clean category tree on the left and settings panels on the right (inspired by Reaper Preferences layout).
- Relocated Language selection to the top-level Settings menu for easier discovery.
- Enhanced speaker label removal logic: removing a speaker label reassigns all audio and segments in that speaker's turn/section to the previous speaker without creating extra speaker labels.
- Streamlined "Change Speaker Label" dialog to only show "Rename All Instances", "Rename This Instance Only", and "Cancel".
- Added dynamic visual mode indicator to Edit/View Transcript button (highlighted active styling and text toggle).
- Optimized GitHub Actions CI/CD workflow: default to Windows builds and automatic release publishing, and fixed macOS arm64 FFmpeg runner compatibility.

## 1.4

- Windows taskbar icon integration and application icon resolution improvements.
- Build system synchronization and documentation updates.

- Established CPU-only as the default/base distribution target.
- Kept NVIDIA CUDA acceleration optional and installable after the base application is installed.
- Added a bundled Windows `uv` runtime manager so optional GPU environments do not require a system Python installation.
- Disabled the NVIDIA CUDA menu item on macOS, where CUDA is not supported.
- Renamed the GPU settings label to make the NVIDIA/CUDA limitation explicit.
- Restricted PySide6 packaging to QtCore, QtGui, QtWidgets, QtMultimedia and QtMultimediaWidgets.
- Added explicit exclusions for unused Qt modules to reduce PyInstaller output size.
- Added the missing Windows Inno Setup installer definition.
- Added the missing macOS `.app`/DMG packaging, signing and optional notarization script.
- Preserved per-user application data during application uninstall/update.
- Bumped the application version in `prs_shared.py` to 1.1.1.

## 1.1

- Install-oriented beta stabilization build.
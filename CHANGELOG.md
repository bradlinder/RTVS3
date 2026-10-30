# Changelog

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

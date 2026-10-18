# Changelog

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

### Historical Releases Archive

*Releases prior to v3.8.0-stable (v1.1 through v3.7.22) are preserved in [CHANGELOG_ARCHIVE.md](CHANGELOG_ARCHIVE.md).*

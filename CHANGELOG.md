# Changelog

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

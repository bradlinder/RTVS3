# Repository Symbol Index & API Map

> Generated: 2026-10-17 16:44:32 | Total Files: 147
> Use `python scripts/generate_symbol_index.py --outline <file>` for exact line numbers.

## Modules Overview

| Module | Lines | Summary | Primary Classes / Functions |
| :--- | :---: | :--- | :--- |
| `RadioTVSegmenter.py` | 558 | Radio & TV Segmenter — v3.9.11-beta | `MainWindow`, `main()` |
| `audio_normalization.py` | 331 | Radio & TV Story Segmenter — Audio Loudness Probing & Nor... | `LoudnessReport`, `AudioLoudnessProbeWorker`, `parse_ebur128_summary()`, `probe_media_duration_seconds()` *(+1 more)* |
| `background_workers.py` | 1014 | Radio & TV Story Segmenter — Background Worker Threads & ... | `StoryAutoDetectWorker`, `WaveformWorker`, `VideoThumbnailWorker`, `get_waveform_peak_cache_path()` *(+6 more)* |
| `backup_manager.py` | 953 | Unified State Serialization, Local, and Google Drive Clou... | `compute_data_checksum()`, `serialize_preferences()`, `serialize_keyboard_shortcuts()`, `serialize_glossary()` *(+11 more)* |
| `batch_dialog.py` | 690 | Radio & TV Story Segmenter — Batch Processing Dialog & Dr... | `BatchFileListWidget`, `BatchProcessingDialog` |
| `benchmark.py` | 2198 | Radio & TV Story Segmenter — Performance & Speed Benchmar... | `BenchmarkMetric`, `ProcessingEstimates`, `BenchmarkEngine`, `get_app_data_dir()` *(+12 more)* |
| `benchmark_dialog.py` | 674 | benchmark_dialog.py - PySide6 Graphical Benchmark Dialog ... | `create_benchmark_dialog()` |
| `benchmark_engine.py` | 903 | benchmark_engine.py - Core High-Precision Performance Ben... | `BenchmarkEngine` |
| `benchmark_models.py` | 457 | benchmark_models.py - Benchmark Data Models, Audio Genera... | `BenchmarkMetric`, `ProcessingEstimates`, `get_app_data_dir()`, `get_candidate_sample_audio_paths()` *(+9 more)* |
| `bootstrap.py` | 359 | Install-safe startup environment configuration for Radio ... | `NullWriter`, `init_null_streams_and_hf_env()`, `patch_av_open()`, `app_data_dir()` *(+7 more)* |
| `build_installer.py` | 1090 | Build the installable Radio & TV Segmenter application wi... | `exe_name()`, `find_tool()`, `check_cpu_only_torch()`, `torch_windows_binary_flags()` *(+8 more)* |
| `bump_version.py` | 451 | bump_version.py — Automated Version Synchronization Engine | `normalize_version()`, `get_current_version()`, `compute_bump()`, `check_all_versions()` *(+2 more)* |
| `cache_manager.py` | 685 | Radio & TV Segmenter — Cache management, disk usage scann... | `ClearCacheDialog`, `register_active_thumbnail_dir()`, `unregister_active_thumbnail_dir()`, `get_active_thumbnail_dirs()` *(+3 more)* |
| `comment_widgets.py` | 350 | comment_widgets.py - Range-Anchored Comments Panel & Comm... | `CommentEditorDialog`, `CommentCardWidget`, `CommentsPanel` |
| `core_utils.py` | 643 | Radio & TV Segmenter — Core filesystem, path, timing, and... | `safe_process_events()`, `get_active_theme_mode()`, `apply_window_titlebar_theme()`, `make_dialog_maximizable()` *(+22 more)* |
| `diagnostic_batch_tests.py` | 1078 | Diagnostic test bench suite component. | `DiagnosticBatchTestsMixin` |
| `diagnostic_cloud_and_system_tests.py` | 1413 | Diagnostic test bench suite component. | `DiagnosticCloudAndSystemTestsMixin` |
| `diagnostic_core_tests.py` | 609 | Diagnostic test bench suite component. | `DiagnosticCoreTestsMixin` |
| `diagnostic_export_tests.py` | 1309 | Diagnostic test bench suite component. | `DiagnosticExportTestsMixin` |
| `diagnostic_helpers.py` | 151 | Helper fixtures, module resolvers, and DiagnosticItem for... | `DiagnosticItem`, `generate_synthetic_wav()` |
| `diagnostic_loudness_tests.py` | 87 | Radio & TV Story Segmenter — Diagnostic Loudness Normaliz... | `DiagnosticLoudnessTestsMixin` |
| `diarization_processing.py` | 691 | Speaker diarization process management for Radio & TV Sto... | `DiarizationProcessingMixin` |
| `export/__init__.py` | 58 | Export package for Radio & TV Story Segmenter. | - |
| `export/audio.py` | 287 | Radio & TV Story Segmenter — Broadcast Audio Rendering & ... | `build_audio_fade_filter()`, `export_audio_track()`, `extract_audio_clip()` |
| `export/daw.py` | 37 | DAW and NLE timeline interchange formatters for Radio & T... | - |
| `export/dialog.py` | 1408 | Unified Export Dialog for Radio & TV Story Segmenter. | `UnifiedExportDialog` |
| `export/docx.py` | 534 | Word (.docx) export formatter for Radio & TV Story Segmen... | `inject_native_comments_to_docx()`, `create_story_docx()` |
| `export/pdf.py` | 285 | PDF export formatter for Radio & TV Story Segmenter. | `TranscriptPdfWriter` |
| `export/reorder_dialog.py` | 255 | export/reorder_dialog.py — Dialog for customizing the dis... | `ReorderExportDestinationsDialog`, `get_export_destinations_order()`, `save_export_destinations_order()` |
| `export/subtitles.py` | 222 | Subtitle and timeline formatters for Radio & TV Story Seg... | `format_subtitle_timestamp()`, `format_srt_timestamp()`, `format_vtt_timestamp()`, `format_cue_timestamp()` *(+9 more)* |
| `export/timeline.py` | 793 | Multi-Platform Timeline and DAW Interchange Engine for Ra... | `reaper_color_from_hex()`, `format_edl_timestamp()`, `build_timeline_clips()`, `generate_reaper_project()` *(+8 more)* |
| `export_dialogs.py` | 372 | Radio & TV Story Segmenter — Export Dialogs & Scope Selec... | `ExportDialogsMixin`, `show_export_completion_dialog()` |
| `export_documents.py` | 774 | Radio & TV Story Segmenter — Document, Transcript & Timel... | `ExportDocumentsMixin` |
| `export_media_clipper.py` | 211 | Radio & TV Story Segmenter — Media Clipper & Audio Track ... | `ExportMediaClipperMixin` |
| `export_story_pipeline.py` | 979 | Radio & TV Story Segmenter — Story & Full Episode Export ... | `ExportStoryPipelineMixin` |
| `gpu_acceleration.py` | 276 | Radio & TV Segmenter v1.1.1 — optional GPU acceleration r... | `GpuAccelerationInstallWorker`, `GpuAccelerationMixin` |
| `id3_editor.py` | 704 | ID3 Tag Editor module for Radio & TV Segmenter. | `ID3TagEditorDialog`, `read_id3_tags()`, `write_id3_tags()` |
| `installer/pyinstaller/torch_dll_hook.py` | 70 | PyInstaller runtime hook for Windows ML/native DLL resolu... | - |
| `media_batch.py` | 1699 | Radio & TV Segmenter v1.1.1 — media batch responsibilities. | `MediaBatchMixin` |
| `model_install_workers.py` | 189 | Radio & TV Segmenter — Model Download and Installation Ba... | `WhisperModelInstallWorker`, `DiarizationModelInstallWorker`, `get_diarization_model_dir()`, `is_diarization_model_available()` |
| `model_management.py` | 966 | Radio & TV Segmenter v1.1.1 — model management responsibi... | `ModelManagementMixin` |
| `playback_controller.py` | 330 | Radio & TV Story Segmenter — Media Player Transport & Pla... | `PlaybackControllerMixin` |
| `playback_preferences.py` | 640 | Radio & TV Story Segmenter — Playback Preferences & Appli... | `PlaybackPreferencesMixin` |
| `plugin_dialogs.py` | 458 | GitHub plugins dialogs, batch download workers, and Plugi... | `GitHubPluginsWorker`, `GitHubDownloadWorker`, `GitHubBatchDownloadWorker`, `GitHubPluginsDialog` *(+1 more)* |
| `plugins/__init__.py` | 6 | Radio & TV Segmenter — Plugin Architecture Package. | - |
| `plugins/base.py` | 207 | Radio & TV Segmenter — Plugin Base Interfaces and Manifest. | `PluginManifest`, `BasePlugin`, `ExportDestination` |
| `plugins/gdocs/__init__.py` | 6 | Google Docs & Drive Exporter Plugin for Radio & TV Segmen... | - |
| `plugins/gdocs/auth.py` | 631 | Google Docs & Drive Exporter — OAuth 2.0 Authentication E... | `_OAuthCallbackHandler`, `GoogleDocsAuthManager`, `generate_pkce_pair()`, `generate_oauth_state()` *(+1 more)* |
| `plugins/gdocs/comments.py` | 115 | Google Docs & Drive Native Margin Comments and Anchoring ... | `create_drive_comment()`, `list_drive_comments()`, `attach_editorial_notes_as_comments()` |
| `plugins/gdocs/drive_folders.py` | 445 | Google Drive Folder Management Engine and Folder Selector... | `extract_folder_id_from_input()`, `list_drive_folders()`, `get_drive_folder_info()`, `create_drive_folder()` *(+1 more)* |
| `plugins/gdocs/export_destination.py` | 813 | Google Docs Export Destination for UnifiedExportDialog. | `GoogleDocsExportDestination` |
| `plugins/gdocs/formatter.py` | 874 | Google Docs Document Serializer and Formatting Engine. | `GoogleDocsSerializer`, `format_time()`, `utf16_len()`, `is_sentence_end()` *(+4 more)* |
| `plugins/gdocs/plugin.py` | 232 | Google Docs & Drive Exporter Plugin implementation for Ra... | `Plugin` |
| `plugins/gdocs/review.py` | 329 | Google Docs Review and Comment Pull Integration. | `GoogleDocsReviewDialog`, `extract_doc_id_from_url()`, `fetch_google_doc_content()`, `compute_segment_diffs()` |
| `plugins/google_sheets.py` | 206 | Google Sheets Integration Engine for Radio & TV Segmenter. | `GoogleSheetsApiClient`, `format_story_rundown_table()`, `format_speaker_analytics_table()` |
| `plugins/manager.py` | 1942 | Radio & TV Segmenter — Plugin Manager and Discovery Engine. | `PluginManager`, `GitHubPluginsWorker`, `GitHubDownloadWorker`, `GitHubBatchDownloadWorker` *(+4 more)* |
| `plugins/translation/__init__.py` | 9 | Language Translation Plugin for Radio & TV Segmenter. | - |
| `plugins/translation/plugin.py` | 58 | Language Translation Plugin for Radio & TV Segmenter. | `Plugin` |
| `plugins/translation/runtime_entry.py` | 49 | CLI entry point for the isolated translation runtime. | `emit()`, `main()` |
| `plugins/translation/support.py` | 176 | Small dependency-light helpers shared by the translation ... | `configure_ssl_certificates()`, `get_app_data_dir()`, `get_legacy_models_storage_dirs()`, `get_models_storage_dir()` *(+2 more)* |
| `plugins/translation/worker.py` | 678 | Translation plugin worker. | `TranslationWorker` |
| `plugins/wordpress/__init__.py` | 6 | WordPress Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/wordpress/client.py` | 1562 | WordPress Plugin — Client, Credential Storage, and Upload... | `WordPressClient`, `WordPressSettingsDialog`, `WordPressPreferencesPage`, `format_rich_text_to_html()` *(+6 more)* |
| `plugins/wordpress/export_destination.py` | 2080 | WordPress Export Destination for UnifiedExportDialog. | `WordPressExportTabWidget`, `WordPressExportDestination`, `WordPressPostMetadataDialog`, `capture_video_frame()` |
| `plugins/wordpress/plugin.py` | 893 | WordPress Publisher Plugin for Radio & TV Segmenter. | `WordPressPublishDialog`, `WordPressPublishWorker`, `WordPressStoryMetadataWidget`, `Plugin` *(+1 more)* |
| `plugins/wordpress/wordpress_dialog.py` | 884 | WordPress Export Tab Widget and Post Metadata Dialog. | `WordPressExportTabWidget`, `WordPressPostMetadataDialog`, `generate_wp_excerpt()`, `capture_video_frame()` |
| `plugins/youtube/__init__.py` | 9 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/youtube/api.py` | 368 | YouTube Data API v3 Client & Direct Video Upload Engine. | `YouTubeAuthManager`, `YouTubeApiClient` |
| `plugins/youtube/export_destination.py` | 834 | YouTube Export Destination for UnifiedExportDialog with D... | `YouTubeExportTabWidget`, `YouTubeExportDestination`, `capture_video_frame()` |
| `plugins/youtube/guide_dialog.py` | 147 | Interactive Assisted Upload Guide Dialog for YouTube Studio. | `YouTubeAssistedUploadGuideDialog` |
| `plugins/youtube/plugin.py` | 234 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | `YouTubeSettingsDialog`, `Plugin`, `capture_video_frame()` |
| `preferences_dialog.py` | 588 | Radio & TV Story Segmenter — Preferences Modal Dialog. | `PreferencesDialogMixin` |
| `preferences_reset.py` | 613 | Radio & TV Story Segmenter — Preferences Reset & Factory ... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_reset_dialog.py` | 617 | Radio & TV Segmenter — Preferences reset and factory defa... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_tabs.py` | 1133 | Radio & TV Story Segmenter — Preferences Modal Tab Builders. | `build_general_tab()`, `build_shortcuts_tab()`, `build_audio_hardware_tab()`, `build_updates_tab()` *(+7 more)* |
| `preferences_tabs_core.py` | 509 | Radio & TV Story Segmenter — Preferences Modal Core Tab B... | `build_general_tab()`, `build_shortcuts_tab()`, `build_audio_hardware_tab()`, `build_updates_tab()` *(+2 more)* |
| `preferences_tabs_media.py` | 641 | Radio & TV Story Segmenter — Preferences Modal Media & Wo... | `build_playback_timeline_tab()`, `build_detection_tab()`, `build_batch_tab()`, `build_cleanup_tab()` *(+1 more)* |
| `preview_manager.py` | 659 | AI Studio Web Preview Manager for Radio & TV Story Segmen... | `get_project_version()`, `restore_preview()`, `sync_version()`, `verify_preview()` *(+1 more)* |
| `process_lifecycle.py` | 191 | Radio & TV Segmenter — Subprocess tracking and OS-level j... | `init_child_process_job_isolation()`, `bind_subprocess_to_job()`, `register_process()`, `unregister_process()` *(+2 more)* |
| `processing.py` | 1148 | Radio & TV Segmenter v3.3.29 — processing responsibilities. | `RuntimeSetupWorker`, `ProcessingMixin` |
| `project_export.py` | 447 | Radio & TV Story Segmenter — Unified Project & Media Expo... | `ProjectExportMixin` |
| `project_lifecycle.py` | 956 | Radio & TV Story Segmenter — Project Lifecycle & Persiste... | `ProjectLifecycleMixin`, `ProjectDataPurgeDialog` |
| `project_serialization.py` | 126 | Radio & TV Segmenter — Project file serialization and saf... | `sanitize_project_data_for_storage()`, `serialize_rtvs_project()`, `deserialize_rtvs_project()`, `read_rtvs_project_file()` *(+1 more)* |
| `project_state_mixin.py` | 328 | Radio & TV Story Segmenter — Project State, Undo/Redo & P... | `ProjectStateMixin` |
| `prs_shared.py` | 1257 |  | `ProjectMetadataDict`, `ResizableTextEdit`, `CollapsibleSection`, `ExportDialog` *(+8 more)* |
| `qt_compat.py` | 173 | Radio & TV Segmenter — Headless Qt / PySide6 Compatibilit... | `MockModule`, `DummyQt`, `DummyQSettings`, `DummyQMessageBox` *(+4 more)* |
| `radio_tv_story_segmenter_worker.py` | 2264 |  | `emit()`, `emit_hello()`, `get_optimal_transcription_threads()`, `get_app_data_dir_pure()` *(+15 more)* |
| `roadmap_manager.py` | 262 | roadmap_manager.py — Automated Roadmap & N-1 Sliding-Wind... | `RoadmapManager`, `get_current_app_version()`, `main()` |
| `runtime_manager.py` | 1035 |  | `RuntimeManager`, `register_process()`, `unregister_process()`, `kill_all_subprocesses()` *(+1 more)* |
| `scripts/generate_symbol_index.py` | 380 | generate_symbol_index.py — Fast AST Symbol Indexer & Repo... | `parse_function_signature()`, `analyze_file()`, `scan_repository()`, `generate_index_markdown()` *(+4 more)* |
| `scripts/log_summary.py` | 150 | log_summary.py — Compact Error & Exception Extraction Engine | `is_project_frame()`, `extract_log_summary()`, `main()` |
| `shortcuts/__init__.py` | 26 | shortcuts package — Modular Keyboard Shortcuts Management... | - |
| `shortcuts/definitions.py` | 22 | shortcuts/definitions.py — Shortcut definitions and schem... | - |
| `shortcuts/dialogs.py` | 623 | shortcuts/dialogs.py — Preferences page for keyboard shor... | `KeyboardShortcutsPage` |
| `shortcuts/manager.py` | 198 | shortcuts/manager.py — Core ShortcutsManager coordinator ... | `ShortcutsManager` |
| `shortcuts/schema.py` | 558 | shortcuts/schema.py — Shortcut definitions, dataclass mod... | `ShortcutDef`, `get_platform_default()`, `format_sequence_display()`, `normalize_sequence_string()` |
| `shortcuts/widgets.py` | 151 | shortcuts/widgets.py — Interactive Key Sequence Recorder ... | `KeySequenceRecorderEdit` |
| `shortcuts_manager.py` | 30 | Shortcuts Manager for Radio & TV Story Segmenter (Compati... | - |
| `snapshot_manager.py` | 276 | Snapshot Manager for Radio & TV Story Segmenter | `load_manifest()`, `save_manifest()`, `get_current_project_version()`, `ensure_git_repo()` *(+4 more)* |
| `speaker_dialog_refinement_mixin.py` | 508 | Radio & TV Story Segmenter — Speaker Dialog Refinement & ... | `SpeakerDialogRefinementMixin` |
| `speaker_dialogs.py` | 302 | speaker_dialogs.py — Dialogs for speaker renaming, turn a... | `ChangeSpeakerDialog`, `SpeakerManagerDialog` |
| `speaker_editing_mixin.py` | 580 | Radio & TV Story Segmenter — Speaker Label, Renaming & Se... | `SpeakerEditingMixin` |
| `speaker_identity.py` | 260 | Radio & TV Segmenter | `VoiceMatch`, `cosine_similarity()`, `normalize_vector()`, `centroid()` *(+3 more)* |
| `speaker_profiles.py` | 630 | speaker_profiles.py — Persistent Station Voice Profile Ma... | `StationVoiceProfile`, `StationVoiceProfileStore`, `ManageVoiceProfilesDialog` |
| `story_crud_mixin.py` | 735 | Radio & TV Story Segmenter — Story CRUD & Timeline Select... | `StoryCrudMixin` |
| `story_detection_processing.py` | 141 | Story boundary detection processing mixin for Radio & TV ... | `StoryDetectionProcessingMixin` |
| `story_fades_dialog.py` | 213 | story_fades_dialog.py — Dialog for fine-grained audio fad... | `StoryFadesDialog` |
| `story_metadata_dialog.py` | 1291 | Radio & TV Story Segmenter — Universal Story & Post Metad... | `StoryMetadataDialog`, `generate_story_excerpt()` |
| `story_model.py` | 254 | Radio & TV Story Segmenter — Story Model, Boundaries & Un... | `Story`, `SetStoriesCommand`, `StoryBoundaryChangeCommand`, `SelectStoriesCommand` *(+3 more)* |
| `story_widgets.py` | 531 | Radio & TV Story Segmenter — Story Sidebar Widgets, Item ... | `FadeCurveVisualSelector`, `StoryFadesChangeCommand`, `SetStoriesCommand`, `StoryBoundaryChangeCommand` *(+3 more)* |
| `terminology.py` | 275 | Model-independent terminology and glossary support. | `parse_glossary()`, `load_glossary()`, `normalize_text()`, `normalize_transcript()` *(+6 more)* |
| `theme_preferences.py` | 596 | Radio & TV Story Segmenter — Theme Preferences & Styling ... | `ThemePreferencesMixin` |
| `theme_qss.py` | 325 | Targeted QSS for the Radio & TV Segmenter visual design s... | - |
| `theme_tokens.py` | 307 | Theme Tokens for Radio & TV Story Segmenter. | `ThemeTokens`, `theme_tokens_for_mode()` |
| `timeline_canvas.py` | 1329 | TimelineCanvas: Interactive timeline widget rendering tim... | `TimelineCanvas` |
| `timeline_envelope.py` | 51 | Waveform envelope data structure and multi-resolution pyr... | `WaveformEnvelope`, `build_waveform_pyramid()` |
| `timeline_overview.py` | 351 | Timeline Resize Handle and Overview Navigation Bar widgets. | `TimelineResizeHandle`, `TimelineOverviewBar` |
| `timeline_widgets.py` | 1898 | Radio & TV Story Segmenter — Timeline Ruler, Track Views,... | `WaveformEnvelope`, `TimelineCanvas`, `TimelineResizeHandle`, `TimelineOverviewBar` *(+2 more)* |
| `transcript_cleaner.py` | 216 | Radio & TV Segmenter — Transcript cleaning, loop collapsi... | `collapse_repeating_ngrams()`, `strip_hallucination_phrases()`, `trim_trailing_degenerate_tail()`, `scrub_transcript_segments()` *(+1 more)* |
| `transcript_context_menu_mixin.py` | 415 | Radio & TV Story Segmenter — Interactive Transcript Conte... | `TranscriptContextMenuMixin` |
| `transcript_editor.py` | 862 | transcript_editor.py - Interactive Transcript Editor & Vi... | `InteractiveTranscriptEdit` |
| `transcript_editor_dialogs.py` | 214 | transcript_editor_dialogs.py - Dialog and floating toolba... | `FindReplaceDialog`, `TranscriptSelectionBubble` |
| `transcript_formatting_mixin.py` | 340 | Radio & TV Story Segmenter — Interactive Transcript Forma... | `TranscriptFormattingMixin` |
| `transcript_navigation_mixin.py` | 299 | transcript_navigation_mixin.py - Timestamp discovery, car... | `TranscriptNavigationMixin` |
| `transcript_playback_highlight_mixin.py` | 276 | Radio & TV Story Segmenter — Interactive Transcript Playb... | `TranscriptPlaybackHighlightMixin` |
| `transcript_selection_mixin.py` | 420 | transcript_selection_mixin.py - Multi-selection, timeline... | `TranscriptSelectionMixin` |
| `transcript_story.py` | 836 | Radio & TV Segmenter v3.9.11-beta — transcript story resp... | `TranscriptStoryMixin` |
| `transcript_styles.py` | 104 | transcript_styles.py - Transcript view stylesheets and da... | `transcript_text_view_stylesheet()`, `clean_dark_mode_clipboard_html()` |
| `transcript_timeline_sync_mixin.py` | 566 | Radio & TV Story Segmenter — Transcript Timeline & Playba... | `TranscriptTimelineSyncMixin` |
| `transcription_processing.py` | 524 | Transcription background process management for Radio & T... | `TranscriptionProcessingMixin` |
| `translation.py` | 896 | Radio & TV Segmenter — Local Translation Mixin. | `TranslationEnvSetupWorker`, `TranslationMixin` |
| `ui_dialog_launchers.py` | 304 | Dialog launchers and external modal helpers for Radio & T... | `UiDialogLaunchersMixin` |
| `ui_layout.py` | 1027 | Radio & TV Segmenter — UI Layout & Menu Construction Mixin. | `UiLayoutMixin` |
| `ui_menus.py` | 775 | Main application menu bar and action assembly for Radio &... | `PersistentMenu`, `UiMenusMixin` |
| `updater.py` | 1418 | Update manager and GitHub release installer for Radio & T... | `CheckUpdateWorker`, `DownloadUpdateWorker`, `CheckUpdateDialog`, `UpdaterMixin` *(+9 more)* |
| `utils/__init__.py` | 36 | Utility modules for Radio & TV Story Segmenter. | - |
| `utils/constants.py` | 41 | Application constants and environment configuration. | - |
| `utils/time_format.py` | 19 | Time formatting and parsing utilities. | - |
| `voice_profile_dialog.py` | 1006 | voice_profile_dialog.py — Dialog for finding and reassign... | `VoiceProfileMatchDialog` |
| `voice_profile_matcher_mixin.py` | 577 | Radio & TV Story Segmenter — Acoustic Voice Profile Match... | `VoiceProfileMatcherMixin` |
| `voice_profile_ops_mixin.py` | 585 | Radio & TV Story Segmenter — Voice Profile Matching & Emb... | `VoiceProfileOpsMixin` |
| `worker_asr_engines.py` | 816 | worker_asr_engines.py - Faster-Whisper, CTranslate2 & She... | `set_emit_callback()`, `get_optimal_transcription_threads()`, `get_app_data_dir_pure()`, `get_models_storage_dir_pure()` *(+4 more)* |
| `worker_clustering.py` | 448 | worker_clustering.py - Acoustic clustering, VAD pause bri... | `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `fast_cluster_ahc()`, `apply_clustering_patches()` *(+2 more)* |
| `worker_diarization_clustering.py` | 297 | worker_diarization_clustering.py - Speaker Clustering, Ce... | `fast_cluster_ahc()`, `apply_clustering_patches()`, `assign_short_segments_to_centroids()` |
| `worker_diarization_engine.py` | 902 | worker_diarization_engine.py - Speaker Diarization, Neura... | `set_emit_callback()`, `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `extract_embeddings_batched()` *(+3 more)* |
| `worker_ipc.py` | 216 | worker_ipc.py - Subprocess IPC protocol, environment setu... | `emit()`, `emit_hello()` |
| `worker_story_engine.py` | 388 | worker_story_engine.py - Acoustic & Lexical Story Boundar... | `is_real_speech()`, `detect_story_boundaries()` |

## Detailed Symbol Catalog

### `RadioTVSegmenter.py` (558 lines)
*Radio & TV Segmenter — v3.9.11-beta*
- **class `MainWindow(ModelManagementMixin, MediaBatchMixin, PlaybackPreferencesMixin, UiLayoutMixin, ProcessingMixin, TranslationMixin, TranscriptStoryMixin, ProjectExportMixin, GpuAccelerationMixin, QMainWindow)`** (lines 160–455):
  *Main application window for Radio & TV Segmenter.*
  - `__init__(self)` [L178-L351]
  - `handle_external_open_request(self, file_path)` [L353-L378] — *Called when another instance attempts to open a project file in single-instance mode.*
  - `load_persistent_settings(self)` [L380-L446] — *Loads all persistent user preferences from QSettings into MainWindow attributes.*
  - `changeEvent(self, event)` [L448-L455] — *Handle window state changes (e.g. maximize, restore, minimize) safely.*
- **Functions**:
  - `main()` [L458-L554]

### `audio_normalization.py` (331 lines)
*Radio & TV Story Segmenter — Audio Loudness Probing & Normalization Engine.*
- **class `LoudnessReport`** (lines 59–71):
  *Telemetry report representing measured loudness and peak metrics for an audio file.*
  - `to_dict(self)` [L70-L71]
- **class `AudioLoudnessProbeWorker(QThread)`** (lines 289–331):
  *Background worker thread to probe audio loudness without freezing Qt GUI.*
  - `__init__(self, media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout, parent)` [L295-L310]
  - `cancel(self)` [L312-L314] — *Request worker cancellation.*
  - `run(self)` [L316-L331] — *Execute non-blocking probe in background.*
- **Functions**:
  - `_safe_float(val_str, default)` [L74-L89] — *Parse string to float with safe handling for -inf, inf, nan.*
  - `parse_ebur128_summary(stderr_text)` [L92-L122] — *Parse FFmpeg ebur128 filter output to extract I (LUFS), LRA (LU), and Peak (dBTP/dBFS).*
  - `probe_media_duration_seconds(media_path, timeout)` [L125-L154] — *Fast probe of total media duration in seconds via ffprobe.*
  - `probe_media_loudness(media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout)` [L157-L286] — *Measure loudness (LUFS), dynamic range (LRA), and peak (dBTP) of an audio/video file.*

### `background_workers.py` (1014 lines)
*Radio & TV Story Segmenter — Background Worker Threads & Waveform Cache Helpers.*
- **class `StoryAutoDetectWorker(QObject)`** (lines 92–459):
  - `__init__(self, audio_file, silence_threshold, lead_in_padding, audio_duration, transcript_segments, whisper_model, detection_mode, **kwargs)` [L103-L122]
  - `cancel(self)` [L124-L125]
  - `_emit_progress(self, message, percent)` [L127-L141]
  - `_is_real_speech(self, text)` [L143-L149]
  - `run(self)` [L151-L459]
- **class `WaveformWorker(QObject)`** (lines 677–825):
  - `__init__(self, audio_file, points_per_second, project_file)` [L680-L686]
  - `cancel(self)` [L688-L696] — *Thread-safe cancellation request; also stops the FFmpeg child process.*
  - `run(self)` [L698-L825] — *Build a compact peak envelope without loading the whole recording into RAM.*
- **class `VideoThumbnailWorker(QObject)`** (lines 945–1003):
  - `__init__(self, media_path, duration, output_dir, count)` [L949-L956]
  - `cancel(self)` [L958-L965]
  - `run(self)` [L967-L1003]
- **Functions**:
  - `get_waveform_peak_cache_path(audio_file, project_file)` [L483-L537] — *Return local project or appdata path for waveform peak binary cache file.*
  - `read_waveform_peak_cache(audio_file, points_per_second, project_file)` [L542-L611] — *Read cached waveform peak envelope from binary cache.*
  - `write_waveform_peak_cache(audio_file, peaks, points_per_second, project_file, levels)` [L613-L651] — *Write waveform peak envelope and multi-resolution mipmapped levels to binary cache with atomic rename.*
  - `invalidate_waveform_peak_cache(audio_file, project_file)` [L654-L674] — *Delete any cached waveform peak binary file for audio_file, including legacy paths.*
  - `get_video_thumbnail_cache_dir(media_file, project_file)` [L832-L871] — *Return the deterministic thumbnail cache directory for a media file, associating with project if available.*
  - `read_video_thumbnail_cache(media_file, duration, project_file)` [L874-L916] — *Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.*
  - `invalidate_video_thumbnail_cache(media_file, project_file)` [L919-L942] — *Delete the thumbnail cache directory for a given media file.*

### `backup_manager.py` (953 lines)
*Unified State Serialization, Local, and Google Drive Cloud Backup & Restore Engine.*
- **Functions**:
  - `compute_data_checksum(data)` [L36-L39] — *Computes a deterministic SHA-256 checksum over normalized JSON serialization of data.*
  - `serialize_preferences(settings_store)` [L42-L67] — *Extracts all persistent preferences from QSettings while safely coercing values.*
  - `serialize_keyboard_shortcuts(settings_store, shortcuts_mgr)` [L70-L93] — *Extracts custom keyboard shortcut keybindings from ShortcutsManager or QSettings.*
  - `serialize_glossary(settings_store)` [L96-L102] — *Extracts shared terminology glossary entries.*
  - `serialize_models_inventory()` [L105-L143] — *Extracts installed local model metadata.*
  - `serialize_plugin_states(settings_store)` [L146-L163] — *Extracts enabled states for installed plugins.*
  - `create_backup_payload(settings_store, shortcuts_mgr, main_window)` [L166-L190] — *Creates a unified, cryptographically verified state backup payload dictionary.*
  - `verify_backup_payload(payload_raw)` [L193-L231] — *Validates structure, format identifier, and SHA-256 cryptographic checksum.*
  - `apply_backup_payload(payload, main_window, settings_store, shortcuts_mgr)` [L234-L360] — *Applies a verified backup payload to system settings, shortcuts, and glossary.*
  - `export_local_backup(target_path, settings_store, shortcuts_mgr, main_window)` [L363-L378] — *Writes a verified state backup archive to a local file.*
  - `restore_local_backup(source_path, main_window, settings_store, shortcuts_mgr)` [L381-L406] — *Restores settings and configurations from a local backup file.*
  - `_get_gdocs_auth_manager()` [L411-L417] — *Dynamically resolves GoogleDocsAuthManager for Google Drive API operations.*
  - `list_cloud_backups(auth_manager)` [L420-L459] — *Queries Google Drive API v3 for RTVS backup archives.*
  - `upload_cloud_backup(payload, auth_manager, custom_name)` [L462-L530] — *Uploads a settings payload directly to Google Drive via multipart API.*
  - `download_cloud_backup(file_id, auth_manager)` [L533-L573] — *Downloads and verifies an RTVS backup from Google Drive.*
  - `restore_cloud_backup(file_id, auth_manager, main_window, settings_store)` [L576-L593] — *Restores system configuration directly from a Google Drive cloud backup.*

### `batch_dialog.py` (690 lines)
*Radio & TV Story Segmenter — Batch Processing Dialog & Droppable File List.*
- **class `BatchFileListWidget(QListWidget)`** (lines 43–149):
  - `__init__(self, parent)` [L46-L53]
  - `dragEnterEvent(self, event)` [L55-L64]
  - `dragMoveEvent(self, event)` [L66-L74]
  - `dragLeaveEvent(self, event)` [L76-L79]
  - `dropEvent(self, event)` [L81-L91]
  - `paintEvent(self, event)` [L93-L149]
- **class `BatchProcessingDialog(QDialog)`** (lines 151–678):
  - `__init__(self, parent)` [L152-L422]
  - `eventFilter(self, watched, event)` [L424-L440]
  - `_load_saved_options(self)` [L442-L500]
  - `save_options_to_settings(self, as_default)` [L502-L535]
  - `reset_options_to_defaults(self)` [L537-L575]
  - `_on_start_clicked(self)` [L577-L579]
  - `dragEnterEvent(self, event)` [L581-L588]
  - `dragMoveEvent(self, event)` [L590-L597]
  - `dropEvent(self, event)` [L599-L607]
  - `add_paths(self, paths)` [L609-L623]
  - `add_files(self)` [L625-L637]
  - `choose_output(self)` [L639-L644]
  - `choose_transcripts_output(self)` [L646-L656]
  - `auto_detect_options(self)` [L658-L678] — *Auto-detect available options based on imported file extensions.*

### `benchmark.py` (2198 lines)
*Radio & TV Story Segmenter — Performance & Speed Benchmark Engine.*
- **class `BenchmarkMetric`** (lines 415–427):
- **class `ProcessingEstimates`** (lines 431–453):
  *Estimated processing times for a standard 30-minute broadcast file.*
- **class `BenchmarkEngine`** (lines 505–1397):
  *Executes high-precision performance throughput benchmarks.*
  - `__init__(self, quick, duration_mode, audio_source_mode, custom_audio_path)` [L551-L639]
  - `_get_target_audio_seconds(self)` [L641-L644] — *Returns the target audio window in seconds based on active duration mode.*
  - `_prepare_audio_source(self)` [L646-L686] — *Loads and prepares the configured audio stream (synthetic or real file).*
  - `run_all(self, stop_requested_fn)` [L688-L731]
  - `_compute_composite_score(self)` [L733-L769] — *Computes aggregate RTVS Hardware Performance Score normalized to baseline reference.*
  - `compute_processing_estimates(self, audio_duration_minutes)` [L771-L864] — *Computes realistic estimated execution times for a standard broadcast file.*
  - `_bench_waveform_peak_extraction(self, metric)` [L867-L914]
  - `_bench_audio_stft_and_mel_filterbank(self, metric)` [L917-L968]
  - `_bench_multi_core_speech_segmentation(self, metric)` [L971-L1017]
  - `_bench_speaker_diarization_vector_search(self, metric)` [L1020-L1065]
  - `_bench_project_serialization_and_indexing(self, metric)` [L1068-L1128]
  - `_bench_transcript_formatting_and_search(self, metric)` [L1131-L1192]
  - `_bench_multi_format_export_generation_throughput(self, metric)` [L1195-L1269]
  - `_bench_transformer_self_attention_kernel(self, metric)` [L1272-L1327]
  - `_bench_ai_background_worker_and_ipc_handshake(self, metric)` [L1330-L1368]
  - `_bench_model_cache_storage_and_cdn_connectivity(self, metric)` [L1371-L1397]
- **Functions**:
  - `get_app_data_dir()` [L70-L82] — *Returns application data directory consistent across platforms.*
  - `get_candidate_sample_audio_paths()` [L85-L108] — *Returns ordered list of file paths where sample audio may reside.*
  - `find_available_sample_audio()` [L111-L119] — *Finds the first existing valid sample audio file on disk.*
  - `get_sample_audio_target_path()` [L122-L135] — *Returns the primary target path for downloading the sample audio file.*
  - `delete_sample_audio_files()` [L138-L161] — *Deletes all sample audio files across candidate locations to free disk space.*
  - `download_sample_audio(progress_callback, cancel_check)` [L164-L223] — *Downloads the benchmark sample audio file with progress notifications.*
  - `decode_audio_file_pcm(file_path, max_duration_seconds)` [L230-L281] — *Decodes media file to 16kHz mono 16-bit PCM using FFmpeg.*
  - `_get_seed_speech_pcm(sample_rate)` [L291-L313] — *Generates a 5-second realistic speech-modulated PCM audio seed in memory.*
  - `generate_benchmark_audio(duration_seconds, sample_rate)` [L316-L338] — *Generates mono 16-bit 16kHz speech-like PCM WAV audio in memory via seed tiling.*
  - `get_system_hardware_profile()` [L345-L407] — *Inspects CPU, RAM, OS, and GPU environment.*
  - `is_translation_plugin_installed()` [L456-L486] — *Checks if the local neural translation plugin/runtime is installed and available.*
  - `format_duration_estimate(seconds)` [L489-L498] — *Formats seconds into a clear human-readable duration.*
  - `run_cli_benchmark(quick, duration_mode, as_json, use_sample, custom_file)` [L1404-L1490] — *Run performance benchmarks and print formatted terminal report.*
  - `create_benchmark_dialog(parent)` [L1497-L2145] — *Factory creating the native PySide6 Benchmark Dialog.*

### `benchmark_dialog.py` (674 lines)
*benchmark_dialog.py - PySide6 Graphical Benchmark Dialog & Workers.*
- **Functions**:
  - `create_benchmark_dialog(parent)` [L30-L674] — *Factory creating the native PySide6 Benchmark Dialog.*

### `benchmark_engine.py` (903 lines)
*benchmark_engine.py - Core High-Precision Performance Benchmark Runner.*
- **class `BenchmarkEngine`** (lines 39–903):
  *Executes high-precision performance throughput benchmarks.*
  - `__init__(self, quick, duration_mode, audio_source_mode, custom_audio_path)` [L85-L173]
  - `_get_target_audio_seconds(self)` [L175-L178] — *Returns the target audio window in seconds based on active duration mode.*
  - `_prepare_audio_source(self)` [L180-L220] — *Loads and prepares the configured audio stream (synthetic or real file).*
  - `run_all(self, stop_requested_fn)` [L222-L265]
  - `_compute_composite_score(self)` [L267-L301] — *Computes aggregate RTVS Hardware Performance Score normalized to baseline reference.*
  - `compute_processing_estimates(self, audio_duration_minutes)` [L303-L390] — *Computes realistic estimated execution times for a standard broadcast file.*
  - `_bench_waveform_peak_extraction(self, metric)` [L393-L438]
  - `_bench_audio_stft_and_mel_filterbank(self, metric)` [L441-L488]
  - `_bench_multi_core_speech_segmentation(self, metric)` [L491-L536]
  - `_bench_speaker_diarization_vector_search(self, metric)` [L539-L581]
  - `_bench_project_serialization_and_indexing(self, metric)` [L584-L642]
  - `_bench_transcript_formatting_and_search(self, metric)` [L645-L706]
  - `_bench_multi_format_export_generation_throughput(self, metric)` [L709-L784]
  - `_bench_transformer_self_attention_kernel(self, metric)` [L787-L836]
  - `_bench_ai_background_worker_and_ipc_handshake(self, metric)` [L839-L874]
  - `_bench_model_cache_storage_and_cdn_connectivity(self, metric)` [L877-L903]

### `benchmark_models.py` (457 lines)
*benchmark_models.py - Benchmark Data Models, Audio Generators & Hardware Profiler.*
- **class `BenchmarkMetric`** (lines 378–390):
- **class `ProcessingEstimates`** (lines 394–412):
  *Estimated processing times for a standard 30-minute broadcast file.*
- **Functions**:
  - `get_app_data_dir()` [L46-L58] — *Returns application data directory consistent across platforms.*
  - `get_candidate_sample_audio_paths()` [L61-L80] — *Returns ordered list of file paths where sample audio may reside.*
  - `find_available_sample_audio()` [L83-L91] — *Finds the first existing valid sample audio file on disk.*
  - `get_sample_audio_target_path()` [L94-L106] — *Returns the primary target path for downloading the sample audio file.*
  - `delete_sample_audio_files()` [L109-L132] — *Deletes all sample audio files across candidate locations to free disk space.*
  - `download_sample_audio(progress_callback, cancel_check)` [L135-L194] — *Downloads the benchmark sample audio file with progress notifications.*
  - `decode_audio_file_pcm(file_path, max_duration_seconds)` [L201-L248] — *Decodes media file to 16kHz mono 16-bit PCM using FFmpeg.*
  - `_get_seed_speech_pcm(sample_rate)` [L258-L280] — *Generates a 5-second realistic speech-modulated PCM audio seed in memory.*
  - `generate_benchmark_audio(duration_seconds, sample_rate)` [L283-L302] — *Generates mono 16-bit 16kHz speech-like PCM WAV audio in memory via seed tiling.*
  - `get_system_hardware_profile()` [L309-L370] — *Inspects CPU, RAM, OS, and GPU environment.*
  - `is_translation_plugin_installed()` [L415-L445] — *Checks if the local neural translation plugin/runtime is installed and available.*
  - `format_duration_estimate(seconds)` [L448-L457] — *Formats seconds into a clear human-readable duration.*

### `bootstrap.py` (359 lines)
*Install-safe startup environment configuration for Radio & TV Segmenter.*
- **class `NullWriter`** (lines 18–25):
  *Safe no-op stream object for windowed GUI executables where stdout/stderr are None.*
  - `write(self, *args, **kwargs)` [L20-L21]
  - `flush(self, *args, **kwargs)` [L22-L23]
  - `isatty(self)` [L24-L25]
- **Functions**:
  - `init_null_streams_and_hf_env()` [L28-L39] — *Ensure sys.stdout/sys.stderr are not None and suppress HF/tqdm console noise.*
  - `patch_av_open()` [L42-L58] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `app_data_dir()` [L66-L76]
  - `setup_windows_dll_directories()` [L82-L194] — *Register native DLL directories (PyTorch, CTranslate2, ONNX Runtime, etc.)*
  - `setup_macos_path_environment()` [L197-L229] — *Ensure standard CLI tool paths (Homebrew, MacPorts, ~/.local/bin) are*
  - `configure_ssl_certificates()` [L232-L264] — *Ensure HTTPS certificate verification works seamlessly across macOS, Linux, and Windows.*
  - `configure_runtime_environment()` [L267-L290] — *Prepare writable user data and model-cache locations before imports.*
  - `ensure_sherpa_onnx_runtime()` [L293-L323] — *Make sure the Parakeet runtime is importable before the GUI starts.*
  - `ensure_keyring_runtime()` [L325-L351] — *Ensure keyring (and pywin32-ctypes on Windows) is installed for secure credential storage.*
  - `check_and_install_core()` [L353-L356] — *Backward-compatible startup dependency check.*

### `build_installer.py` (1090 lines)
*Build the installable Radio & TV Segmenter application with PyInstaller.*
- **Functions**:
  - `exe_name(base)` [L105-L106]
  - `find_tool(name)` [L109-L172]
  - `check_cpu_only_torch()` [L175-L215]
  - `torch_windows_binary_flags()` [L218-L246]
  - `run(cmd)` [L249-L274]
  - `provision_optional_runtime_tools(app_root)` [L277-L357]
  - `prune_unneeded_bundled_files(app_root)` [L360-L489]
  - `sync_installer_scripts(project_version)` [L492-L505] — *Ensure Inno Setup and other installer packaging scripts match PROJECT_VERSION.*
  - `compile_windows_installer(project_version)` [L508-L543] — *Compile the Windows Inno Setup installer executable if ISCC is installed.*
  - `parse_build_args()` [L546-L636]
  - `package_plugins(app_root, include_wp, include_yt, include_tr, include_gd)` [L639-L709] — *Package plugins into standalone .zip release artifacts in dist/plugins/*
  - `main()` [L712-L1086]

### `bump_version.py` (451 lines)
*bump_version.py — Automated Version Synchronization Engine*
- **Functions**:
  - `normalize_version(ver)` [L26-L30] — *Normalize version string: strip leading 'v', collapse double dots, trim.*
  - `get_current_version()` [L32-L46] — *Extract active version from core_utils.py or prs_shared.py.*
  - `compute_bump(current_version, bump_type)` [L48-L73] — *Calculate next semantic version (patch, minor, major) preserving suffix.*
  - `check_all_versions()` [L75-L178] — *Inspect and report the version strings currently set across all files.*
  - `bump_all(new_version, dry_run, plugins)` [L180-L402] — *Execute synchronous version updates across all checklist targets.*
  - `main()` [L404-L448]

### `cache_manager.py` (685 lines)
*Radio & TV Segmenter — Cache management, disk usage scanning, and purging utilities.*
- **class `ClearCacheDialog(QDialog)`** (lines 519–685):
  *Dialog for inspecting disk cache sizes and clearing temporary data.*
  - `__init__(self, parent, language, project_dirs)` [L522-L532]
  - `_init_ui(self)` [L534-L624]
  - `refresh_stats(self)` [L626-L650]
  - `_on_clear_all(self)` [L652-L656]
  - `_on_clear_selected(self)` [L658-L669]
  - `_do_purge(self, clear_thumbs, clear_waves, clear_audio)` [L671-L685]
- **Functions**:
  - `register_active_thumbnail_dir(path)` [L45-L54] — *Register an active thumbnail directory so cache cleanup routines will never touch it.*
  - `unregister_active_thumbnail_dir(path)` [L57-L66] — *Unregister an active thumbnail directory when the project or session closes.*
  - `get_active_thumbnail_dirs()` [L69-L72] — *Return a copy of currently registered active thumbnail directories.*
  - `cleanup_old_thumbnail_cache(max_age_hours, active_dir, exclude_dirs, blocking)` [L76-L203] — *Purge temporary thumbnail directories older than max_age_hours in a background thread.*
  - `get_cache_disk_usage(project_dirs)` [L206-L391] — *Scan and compute disk usage for all temporary cache stores across appdata, temp dirs, and project folders.*
  - `purge_caches(clear_thumbnails, clear_waveforms, clear_audio_extracts, project_dirs)` [L394-L516] — *Purge requested cache stores safely from disk.*

### `comment_widgets.py` (350 lines)
*comment_widgets.py - Range-Anchored Comments Panel & Comment Editor Widgets*
- **class `CommentEditorDialog(QDialog)`** (lines 35–97):
  *Multi-line document-style comment editor supporting spaces, line breaks, and paragraph breaks.*
  - `__init__(self, parent, comment_text, title, prompt)` [L37-L75]
  - `keyPressEvent(self, event)` [L77-L82]
  - `_on_delete(self)` [L84-L86]
  - `get_comment_text(self)` [L88-L91]
  - `get_note_text(self)` [L93-L94]
  - `is_deleted(self)` [L96-L97]
- **class `CommentCardWidget(QFrame)`** (lines 104–221):
  *Card representing a single range-anchored comment in the Comments side panel.*
  - `__init__(self, seg_idx, start_time, end_time, comment_text, quote_text, parent)` [L110-L159]
  - `set_selected(self, is_selected, theme)` [L161-L213] — *Apply distinct active/selected visual indication to card.*
  - `mousePressEvent(self, event)` [L215-L221]
- **class `CommentsPanel(QWidget)`** (lines 224–350):
  *Collapsible docked Comments Sidebar / Pane sitting beside the transcript view.*
  - `__init__(self, parent)` [L230-L283]
  - `_on_add_clicked(self)` [L285-L293]
  - `_on_close_clicked(self)` [L295-L300]
  - `set_comments(self, segments)` [L302-L337] — *Populate the comment cards from transcript segments.*
  - `highlight_segment(self, target_seg_idx)` [L339-L350] — *Visually flash/highlight a specific comment card.*

### `core_utils.py` (643 lines)
*Radio & TV Segmenter — Core filesystem, path, timing, and hash utilities.*
- **Functions**:
  - `safe_process_events()` [L29-L38] — *Safely process pending Qt GUI events only when called from the main GUI thread.*
  - `get_active_theme_mode(default)` [L41-L75] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast') with universal multi-scope resolution.*
  - `_apply_dwm_titlebar_hwnd(hwnd, theme_mode)` [L78-L131] — *Low-level Windows DWM call applying caption and text colors to a window HWND.*
  - `apply_window_titlebar_theme(widget, theme_mode)` [L134-L165] — *Configures Windows DWM title bar caption colors matching active theme mode.*
  - `_deferred_titlebar_theme(widget, theme_mode)` [L168-L176] — *Deferred callback ensuring DWM attributes persist after Qt window frame initialization.*
  - `make_dialog_maximizable(dialog)` [L179-L186] — *Enforce standard OS window maximize and restore title bar controls for resizable dialogs.*
  - `extract_dropped_file_paths(mime_data)` [L189-L240] — *Robustly extracts local filesystem paths from QMimeData supporting URLs, URIs, and raw text.*
  - `_ensure_runtime_bin_on_path()` [L243-L262] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `compute_file_sha256(file_path, chunk_size)` [L268-L274] — *Compute the SHA-256 hexadecimal digest of a file.*
  - `verify_file_sha256(file_path, expected_sha256)` [L277-L285] — *Verify that a file matches the expected SHA-256 checksum (case-insensitive).*
  - `safe_extract_zip(zip_source, dest_dir)` [L288-L306] — *Safely extracts a ZIP archive to a destination directory, guarding against path traversal (Zip Slip).*
  - `safe_extract_tar(tar_source, dest_dir)` [L309-L327] — *Safely extracts a TAR archive to a destination directory, guarding against path traversal.*
  - `safe_replace(src, dest)` [L330-L368] — *Safely and atomically replace dest with src, handling file locks, permissions,*
  - `get_github_repo()` [L371-L388] — *Return the configured GitHub repository owner/repo string.*
  - `get_update_channel()` [L391-L406] — *Return the configured software update release channel: 'stable' or 'beta'.*
  - `get_app_data_dir()` [L409-L424] — *Return the per-user writable application-data directory.*
  - `get_models_storage_dir()` [L427-L445] — *Return the directory configured for storing downloaded models.*
  - `set_models_storage_dir(new_path)` [L448-L469] — *Set and persist a custom models storage directory.*
  - `get_bundled_runtime_dir()` [L472-L484] — *Locate the installed/bundled runtime resource directory.*
  - `find_bundled_executable(name)` [L487-L509] — *Find a bundled executable first, then fall back to PATH and common macOS locations.*
  - `ffmpeg_path()` [L512-L513]
  - `ffprobe_path()` [L516-L517]
  - `format_byte_size(num_bytes)` [L520-L543] — *Format byte quantities into human-readable strings.*
  - `format_time(seconds, include_millis)` [L546-L563]
  - `parse_time(value)` [L566-L582]
  - `safe_filename(text)` [L585-L601]
  - `is_sentence_end(text)` [L604-L605]
  - `calculate_fade_curve_factor(u, fcurve)` [L608-L619] — *Calculate normalized fade-in multiplier (0.0 to 1.0) given progress `u` in [0, 1].*
  - `calculate_fade_out_factor(u, fcurve)` [L622-L642] — *Calculate normalized fade-out multiplier (1.0 to 0.0) given progress `u` from 0.0 (fade start) to 1.0 (silence).*

### `diagnostic_batch_tests.py` (1078 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticBatchTestsMixin`** (lines 26–1077):
  - `_test_batch_unified_transcripts_directory_export(self, item)` [L27-L200]
  - `_test_batch_drag_and_drop_ingestion_and_event_handling(self, item)` [L202-L294]
  - `_test_unified_export_destinations_and_youtube_auth_integrity(self, item)` [L296-L398]
  - `_test_pdf_transcript_export_and_bold_speaker_labels(self, item)` [L400-L455]
  - `_test_fade_curve_tables_and_auditioning_state(self, item)` [L457-L538]
  - `_test_translation_routing_and_key_priority_unit_test(self, item)` [L540-L651]
  - `_test_symmetrical_translation_editing_state_test(self, item)` [L653-L732]
  - `_test_interactive_change_speaker_dialogue_flow_test(self, item)` [L734-L799]
  - `_test_story_boundary_validation_and_overlap_test(self, item)` [L801-L878]
  - `_test_audio_subtitle_sync_drift_test(self, item)` [L880-L924]
  - `_test_interactive_transcript_editing_and_split_join_unit_tests(self, item)` [L926-L1033]
  - `_test_exporter_structure_invariant_tests(self, item)` [L1035-L1077]

### `diagnostic_cloud_and_system_tests.py` (1413 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticCloudAndSystemTestsMixin`** (lines 26–1411):
  - `_test_plugin_interface_sandbox_testing(self, item)` [L27-L129]
  - `_test_project_file_integrity_and_portable_path_resolution(self, item)` [L131-L201]
  - `_test_google_docs_export_integrity(self, item)` [L203-L323]
  - `_test_acoustic_voice_profile_matcher(self, item)` [L325-L587]
  - `_test_windows_detached_update_helper_architecture(self, item)` [L589-L619] — *Validates update helper architecture: helper script generation, exit polling, and logging.*
  - `_test_google_docs_oauth_and_pkce_security(self, item)` [L621-L705] — *Validates OAuth 2.0 PKCE, CSRF state protection, and zero-config public client architecture.*
  - `_test_temporary_cache_management_and_storage_inspection(self, item)` [L707-L806] — *Validates cache usage stats calculation, preview categorization, and cache purging.*
  - `_test_youtube_data_api_and_direct_video_upload_engine(self, item)` [L808-L835] — *Validates YouTube API client, categories, headers, and export destination validation.*
  - `_test_google_sheets_tabular_export_and_formatting_engine(self, item)` [L837-L878] — *Validates Google Sheets tabular rundown formatter, speaker analytics, and client structure.*
  - `_test_multiprocessing_freeze_support_and_spawn_intercept(self, item)` [L880-L894] — *Validates that frozen process spawn intercepts -c invocations from resource_tracker and multiprocessing.*
  - `_resolve_worker_cmd(self)` [L896-L910] — *Resolves the executable and arguments to launch the AI background worker.*
  - `_test_ai_worker_subprocess_execution_and_ipc_handshake(self, item)` [L912-L978] — *Spawns the AI worker binary in an isolated subprocess, verifying IPC hello handshake and self-test.*
  - `_test_frozen_subprocess_multiprocessing_spawn_protocol(self, item)` [L980-L1018] — *Spawns the AI worker executable with Python -c to verify multiprocessing resource tracker interception.*
  - `_test_comprehensive_local_and_cloud_backup_and_restore_engine(self, item)` [L1020-L1132] — *Validates state serialization, SHA-256 verification, local backup roundtrip, and cloud payload integrity.*
  - `_test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting(self, item)` [L1134-L1187] — *Validates Option C muted low-contrast silver/fog palette and dark-mode clipboard rich styling.*
  - `_test_windows_ci_build_and_packaging_optimization_invariants(self, item)` [L1189-L1221] — *Validates Inno Setup compression parameters, Stage 3 PyInstaller optimizations, and CI settings.*
  - `_test_roadmap_n_1_sliding_window_and_status_integrity(self, item)` [L1223-L1242] — *Validates roadmap.txt N-1 sliding window retention, status indicator syntax, and version sync.*
  - `_test_station_voice_profiles_store_and_matching_engine(self, item)` [L1244-L1359] — *Validates StationVoiceProfileStore persistence, vector normalization, profile addition, matching logic, and JSON export/import.*
  - `_test_multi_tier_mipmapped_waveform_peak_cache_serialization(self, item)` [L1361-L1398] — *Validates Version 2 .peaks binary cache read/write with 4x/16x/64x LOD pyramid levels and transparent Version 1 upgrade.*
  - `_test_speed_listening_proofreading_rate_and_context_controls(self, item)` [L1400-L1411] — *Validates playback speed rates (0.75x to 2.0x), WSOLA pitch preservation parameters, and proofreading pre-roll configuration.*

### `diagnostic_core_tests.py` (609 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticCoreTestsMixin`** (lines 26–608):
  - `_test_time_parsing_and_formatting(self, item)` [L27-L65]
  - `_test_project_serialization_round_trip(self, item)` [L67-L95]
  - `_test_waveform_peak_cache_generator(self, item)` [L97-L117]
  - `_test_process_lifecycle_and_subprocess_lock(self, item)` [L119-L125]
  - `_test_subrip_srt_timestamp_formatting(self, item)` [L127-L137]
  - `_test_webvtt_vtt_formatting(self, item)` [L139-L147]
  - `_test_red_book_cue_sheet_generation(self, item)` [L149-L165]
  - `_test_youtube_chapter_markers(self, item)` [L167-L183]
  - `_test_cockos_reaper_project_rpp_generator(self, item)` [L185-L213]
  - `_test_magix_samplitude_edl_v1_5_export(self, item)` [L215-L244]
  - `_test_pytorch_and_torch_native_extensions(self, item)` [L246-L255]
  - `_test_ctranslate2_acceleration_engine(self, item)` [L257-L266]
  - `_test_sherpa_onnx_and_onnx_runtime_engine(self, item)` [L268-L277]
  - `_test_directml_and_gpu_device_enumeration(self, item)` [L279-L303]
  - `_test_hugging_face_and_cdn_connectivity(self, item)` [L305-L322]
  - `_test_model_directory_storage_and_permissions(self, item)` [L324-L334]
  - `_test_safe_archive_extraction_sandbox(self, item)` [L336-L356]
  - `_test_story_boundary_detection_pipeline(self, item)` [L358-L389]
  - `_test_music_vs_voice_mode_filtering(self, item)` [L391-L403]
  - `_test_silero_neural_vad_initialization(self, item)` [L405-L413]
  - `_test_wespeaker_diarization_architecture(self, item)` [L415-L422]
  - `_test_translation_plugin_architecture_invariants(self, item)` [L424-L436]
  - `_test_speaker_reassignment_contiguous_turn_logic(self, item)` [L438-L490]
  - `_test_daw_timeline_interchange_and_gap_handling(self, item)` [L492-L608]

### `diagnostic_export_tests.py` (1309 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticExportTestsMixin`** (lines 26–1308):
  - `_test_wordpress_export_scope_post_builder(self, item)` [L27-L112]
  - `_test_wordpress_export_content_and_transcript_formatter(self, item)` [L114-L325]
  - `_test_multi_format_line_break_and_paragraph_parity(self, item)` [L327-L448]
  - `_test_wordpress_multi_story_upload_and_ui_pluralization(self, item)` [L450-L602]
  - `_test_gutenberg_html_structural_hygiene_audit(self, item)` [L604-L640]
  - `_test_export_scope_delta_and_gap_integrity_audit(self, item)` [L642-L693]
  - `_test_export_destination_interface_contract_verification(self, item)` [L695-L714]
  - `_test_multi_story_media_payload_disambiguation_test(self, item)` [L716-L744]
  - `_test_wordpress_audio_inclusion_toggle_and_error_resilience(self, item)` [L746-L1069]
  - `_test_multi_scope_story_and_full_episode_export_pipeline(self, item)` [L1071-L1152]
  - `_test_audio_export_non_blocking_and_cancellation_pipeline(self, item)` [L1154-L1264]
  - `_test_modal_dialog_maximizable_import_integrity(self, item)` [L1266-L1308]

### `diagnostic_helpers.py` (151 lines)
*Helper fixtures, module resolvers, and DiagnosticItem for test runner.*
- **Public Exports (`__all__`)**: generate_synthetic_wav, DiagnosticItem, _resolve_export_subtitles_module, _resolve_export_daw_module
- **class `DiagnosticItem`** (lines 67–90):
  *Represents the execution outcome of an individual test or diagnostic probe.*
  - `__init__(self, name, category, description, dev_only)` [L70-L78]
  - `to_dict(self)` [L80-L90]
- **Functions**:
  - `generate_synthetic_wav(duration_seconds, sample_rate, frequencies, output_path)` [L18-L63] — *Generates a multi-frequency synthetic 16kHz mono WAV file in memory or on disk.*
  - `_resolve_export_subtitles_module()` [L95-L117] — *Resolves export.subtitles whether running from source, package, or frozen binary.*
  - `_resolve_export_daw_module()` [L120-L142] — *Resolves export.daw whether running from source, package, or frozen binary.*

### `diagnostic_loudness_tests.py` (87 lines)
*Radio & TV Story Segmenter — Diagnostic Loudness Normalization & Auto-Boost Test Suite.*
- **class `DiagnosticLoudnessTestsMixin`** (lines 16–87):
  *Diagnostic tests for Smart Hybrid Audio Loudness Probing & Normalization.*
  - `_test_smart_hybrid_audio_loudness_probing(self, item)` [L19-L87] — *Validates fast multi-window EBU R128 loudness & peak probing across synthetic test media.*

### `diarization_processing.py` (691 lines)
*Speaker diarization process management for Radio & TV Story Segmenter.*
- **class `DiarizationProcessingMixin`** (lines 23–691):
  - `on_diarization_process_error(self, error)` [L24-L78] — *Handles QProcess execution errors for the diarization process.*
  - `start_diarization(self)` [L80-L259]
  - `on_diarization_output(self, force_flush)` [L261-L364]
  - `on_diarization_stderr(self)` [L366-L385] — *Route the worker's stderr straight to the log, separate from the*
  - `on_diarization_process_finished(self, exit_code, exit_status)` [L387-L420]
  - `cleanup_diarization_process(self)` [L422-L456]
  - `diarization_progress(self, message, percent)` [L458-L459]
  - `diarization_finished(self, result)` [L461-L587]
  - `diarization_error(self, message)` [L589-L611]
  - `_diar_segments_cache_key(self)` [L614-L618]
  - `_ensure_diar_speaker_index(self)` [L620-L650]
  - `speaker_at_time(self, start, end)` [L652-L685]
  - `get_effective_speaker_name(self, seg_idx, segment)` [L687-L691]

### `export/__init__.py` (58 lines)
*Export package for Radio & TV Story Segmenter.*
- **Public Exports (`__all__`)**: UnifiedExportDialog, TranscriptPdfWriter, format_srt_timestamp, format_vtt_timestamp, format_cue_timestamp, format_youtube_timestamp, format_edl_timestamp, generate_srt_content, generate_vtt_content, generate_cue_content, generate_youtube_chapters, build_timeline_clips, generate_reaper_project, generate_samplitude_edl, generate_fcp7_xml, generate_audition_xml, generate_fcpxml, generate_aaf_interchange, generate_hindenburg_session, generate_audacity_labels, generate_cue_sheet, generate_daw_marker_csv, create_story_docx

### `export/audio.py` (287 lines)
*Radio & TV Story Segmenter — Broadcast Audio Rendering & Stem Processing.*
- **Functions**:
  - `build_audio_fade_filter(duration, fade_in, fade_out, fade_curve)` [L19-L45] — *Build FFmpeg audio filter strings for fade in and fade out.*
  - `_run_ffmpeg_export(command, timeout_sec, cancel_check, output_file)` [L48-L154] — *Run an FFmpeg command non-blockingly with cancellation checks and event processing.*
  - `export_audio_track(source_media, output_file, start, end, fade_in, fade_out, fade_curve, fades_enabled, is_video, timeout_sec, cancel_check, **kwargs)` [L157-L264] — *Render a segmented audio or video track with optional audio fades.*
  - `extract_audio_clip(source_media, start, end, output_file, timeout_sec, cancel_check)` [L267-L287] — *Extract an audio clip without filtering (fast helper).*

### `export/daw.py` (37 lines)
*DAW and NLE timeline interchange formatters for Radio & TV Story Segmenter.*
- **Public Exports (`__all__`)**: format_edl_timestamp, build_timeline_clips, generate_reaper_project, generate_samplitude_edl, generate_fcp7_xml, generate_audition_xml, generate_fcpxml, generate_aaf_interchange, generate_hindenburg_session, generate_audacity_labels, generate_cue_sheet, generate_daw_marker_csv

### `export/dialog.py` (1408 lines)
*Unified Export Dialog for Radio & TV Story Segmenter.*
- **class `UnifiedExportDialog(QDialog)`** (lines 61–1408):
  *Unified Export Center supporting Local Files and dynamic plugin destinations.*
  - `__init__(self, main_window, initial_scope, initial_dest, parent)` [L64-L286]
  - `showEvent(self, event)` [L288-L290]
  - `_build_destinations_layout(self)` [L292-L437] — *Construct destination radio buttons in customized user order.*
  - `_on_reorder_destinations(self)` [L439-L458] — *Open reorder dialog and rebuild layout on change.*
  - `_create_local_page(self)` [L460-L812]
  - `_on_location_radio_toggled(self)` [L814-L817]
  - `_browse_custom_export_location(self)` [L819-L824]
  - `_create_timeline_page(self)` [L826-L988]
  - `_on_timeline_location_radio_toggled(self)` [L990-L993]
  - `_browse_custom_timeline_location(self)` [L995-L1000]
  - `_toggle_all_sections(self)` [L1002-L1016]
  - `_update_export_button_label(self)` [L1018-L1031]
  - `_on_dest_changed(self)` [L1033-L1038]
  - `_on_scope_changed(self)` [L1040-L1048]
  - `_open_id3_editor(self)` [L1050-L1060] — *Open the ID3 Tag Editor for MP3 files.*
  - `_copy_youtube_chapters(self)` [L1062-L1078]
  - `_load_saved_options(self)` [L1080-L1158]
  - `save_options_to_settings(self, as_default)` [L1160-L1210]
  - `_handle_accept(self)` [L1212-L1275]
  - `get_result(self)` [L1277-L1377]
  - `done(self, r)` [L1379-L1387]
  - `_toggle_maximize(self)` [L1389-L1397]
  - `changeEvent(self, event)` [L1399-L1408]

### `export/docx.py` (534 lines)
*Word (.docx) export formatter for Radio & TV Story Segmenter.*
- **Functions**:
  - `_add_formatted_text_to_paragraph(p, text, words, block_fmt, include_highlights)` [L44-L125] — *Applies word-level or block-level rich text formatting (bold, italic, underline, strike, highlight) to DOCX runs.*
  - `inject_native_comments_to_docx(docx_bytes, comments_map, author, initials)` [L128-L374] — *Injects native OpenXML comment structures into a .docx ZIP archive.*
  - `create_story_docx(title, blocks, output_path, media_name, start_time, end_time, include_speakers, include_timestamps, include_milliseconds, include_comments, include_highlights, lang_code, source_segments)` [L377-L533] — *Creates a formatted Word (.docx) document with native OpenXML comments from story blocks and metadata.*

### `export/pdf.py` (285 lines)
*PDF export formatter for Radio & TV Story Segmenter.*
- **class `TranscriptPdfWriter`** (lines 12–285):
  *Lightweight, self-contained PDF 1.4 vector generator for transcript documents.*
  - `__init__(self, doc_title, page_width, page_height, margin)` [L17-L31]
  - `_escape_pdf(self, s)` [L33-L47]
  - `_flush_page(self)` [L49-L62]
  - `check_space(self, needed_pt)` [L64-L66]
  - `add_header(self, title, subtitle)` [L68-L83]
  - `_approx_char_width(self, font_name, size)` [L85-L86]
  - `_wrap_text(self, text, max_width, font_name, size)` [L88-L107]
  - `_wrap_paragraph_text(self, text, first_line_width, rest_line_width, font_name, size, has_prefix)` [L109-L149]
  - `add_paragraph(self, text, speaker, timestamp, comment, highlight)` [L151-L237]
  - `finish(self)` [L239-L282]
  - `get_pdf_bytes(self)` [L284-L285]

### `export/reorder_dialog.py` (255 lines)
*export/reorder_dialog.py — Dialog for customizing the display order of export destinations.*
- **class `ReorderExportDestinationsDialog(QDialog)`** (lines 52–255):
  *Dialog allowing the user to reorder export destinations via drag-and-drop or Move Up/Down.*
  - `__init__(self, parent, available_dests)` [L55-L218]
  - `_move_up(self)` [L220-L225]
  - `_move_down(self)` [L227-L232]
  - `_reset_default(self)` [L234-L246]
  - `_save_and_accept(self)` [L248-L255]
- **Functions**:
  - `_get_export_theme_mode()` [L25-L27] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast').*
  - `get_export_destinations_order()` [L30-L41] — *Retrieve user-configured export destination ordering.*
  - `save_export_destinations_order(order)` [L44-L49] — *Persist user-configured export destination ordering.*

### `export/subtitles.py` (222 lines)
*Subtitle and timeline formatters for Radio & TV Story Segmenter.*
- **Functions**:
  - `format_subtitle_timestamp(seconds, vtt)` [L15-L27] — *Format seconds into SRT (HH:MM:SS,mmm) or VTT (HH:MM:SS.mmm) timestamp.*
  - `format_srt_timestamp(seconds)` [L30-L32] — *Format seconds into SRT (HH:MM:SS,mmm) timestamp.*
  - `format_vtt_timestamp(seconds)` [L35-L37] — *Format seconds into WebVTT (HH:MM:SS.mmm) timestamp.*
  - `format_cue_timestamp(seconds)` [L40-L42] — *Format seconds into standard CUE sheet MM:SS:FF (75 frames per second).*
  - `format_youtube_timestamp(seconds)` [L45-L53] — *Format seconds into YouTube chapter timestamp (e.g. 03:45 or 01:23:45).*
  - `seconds_to_cue_time(seconds)` [L56-L68] — *Format seconds into standard CUE sheet MM:SS:FF (75 frames per second).*
  - `generate_cue_sheet(stories, media_filename, album_title, project_title, total_duration)` [L71-L109] — *Generate a standard red-book compatible .cue sheet from story segments.*
  - `generate_cue_content(stories, media_filename, album_title, project_title, total_duration)` [L112-L126] — *Generate CUE sheet content from story segments (alias for generate_cue_sheet).*
  - `generate_youtube_chapters(stories, ensure_zero_start)` [L129-L149] — *Generate YouTube chapter markers / tracklist (e.g. 00:00 - Intro, 03:45 - Track 1).*
  - `format_subtitles(blocks, fmt, include_speakers, clean_text_fn)` [L152-L191] — *Format a list of story/transcript blocks into an SRT or WebVTT formatted string.*
  - `write_subtitles_file(blocks, path, fmt, include_speakers, clean_text_fn)` [L194-L203] — *Writes formatted subtitles (SRT or VTT) to a destination path.*
  - `generate_srt_content(blocks, include_speakers, clean_text_fn)` [L206-L212] — *Generate SubRip (.srt) subtitle content from blocks.*
  - `generate_vtt_content(blocks, include_speakers, clean_text_fn)` [L215-L221] — *Generate WebVTT (.vtt) subtitle content from blocks.*

### `export/timeline.py` (793 lines)
*Multi-Platform Timeline and DAW Interchange Engine for Radio & TV Story Segmenter.*
- **Functions**:
  - `_xml_escape(text)` [L24-L35] — *Escape special XML characters for well-formed interchange output.*
  - `reaper_color_from_hex(hex_str)` [L51-L62] — *Convert #RRGGBB hex color to Cockos REAPER custom color integer (0x1000000 | 0x1RRGGBB).*
  - `_reaper_fade_curve_index(curve_name)` [L65-L74] — *Map RTVS fade curve name to Cockos REAPER native curve shape index.*
  - `format_edl_timestamp(seconds)` [L77-L93] — *Format seconds into standard Samplitude EDL timecode (HH:MM:SS:mmm).*
  - `_get_story_start(s)` [L96-L101]
  - `_get_story_end(s, start_val)` [L104-L109]
  - `build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades, scope, all_stories)` [L112-L239] — *Build an ordered list of timeline clips, supporting Full Episode continuous splits and story cuts.*
  - `_build_reaper_track_block(track_name, clips, source_type, media_name_only)` [L242-L301] — *Generate a clean Cockos REAPER <TRACK block with media items, fades, colors, and source offsets.*
  - `generate_reaper_project(stories, media_filename, project_title, apply_fades, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L304-L387] — *Generate a clean, warning-free Cockos REAPER project file (.rpp) with scope-aware tracks, fades, and regions.*
  - `generate_samplitude_edl(stories, media_filename, project_title, sample_rate, apply_fades, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L390-L433] — *Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `generate_fcp7_xml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L436-L523] — *Generate Final Cut Pro 7 XML (xmeml v5) interchange format for Premiere Pro and Audition.*
  - `generate_fcpxml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L530-L586] — *Generate Apple Final Cut Pro X XML (.fcpxml) format for FCPX, DaVinci Resolve, and Logic Pro.*
  - `generate_aaf_interchange(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L589-L659] — *Generate Universal AAF XML Interchange format (.aaf) for Avid Media Composer and Pro Tools.*
  - `generate_hindenburg_session(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, apply_fades, scope, all_stories)` [L662-L739] — *Generate a Hindenburg Broadcast Session (.nhx) for Hindenburg Journalist and Broadcaster.*
  - `generate_audacity_labels(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L742-L754] — *Generate an Audacity Label Track (.txt) import file.*
  - `generate_cue_sheet(stories, media_filename, project_title, total_duration)` [L757-L768] — *Generate a standard Red Book Audio CD CUE sheet (.cue).*
  - `generate_daw_marker_csv(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L771-L793] — *Generate a Universal DAW & NLE Marker List (.csv) format.*

### `export_dialogs.py` (372 lines)
*Radio & TV Story Segmenter — Export Dialogs & Scope Selection Interface.*
- **class `ExportDialogsMixin`** (lines 53–372):
  *Provides dialog launchers, format selectors, and destination routing for MainWindow.*
  - `trigger_export(self)` [L56-L58] — *Standard trigger for Export (File menu Ctrl+E / toolbar).*
  - `export_full_transcript(self)` [L60-L62] — *Triggered from the Export Transcript button above the transcript view.*
  - `open_export_scope_dialog(self)` [L64-L66] — *Standard trigger for the main toolbar Export button.*
  - `open_unified_export_dialog(self, initial_scope, initial_dest)` [L68-L219] — *Unified Export Dialog entry point for local file exports, WordPress publishing,*
  - `_choose_export_formats(self, title, allow_media)` [L221-L372] — *Modal dialog to choose formats and transcript options for classic export flows.*
- **Functions**:
  - `show_export_completion_dialog(parent, title, message, export_path)` [L34-L50] — *Displays export completion with an actionable 'Open Folder' button (Milestone 3.11).*

### `export_documents.py` (774 lines)
*Radio & TV Story Segmenter — Document, Transcript & Timeline Interchange Exporter.*
- **class `ExportDocumentsMixin`** (lines 49–774):
  *Provides document formatting, subtitle generation, and DAW interchange exports.*
  - `_subtitle_timestamp(self, seconds, vtt)` [L52-L62]
  - `write_subtitles(self, blocks, path, fmt, include_speakers)` [L64-L80]
  - `transcript_for_range(self, start, end)` [L82-L100]
  - `speaker_for_segment(self, segment)` [L102-L109]
  - `clean_export_text(self, text, current_speaker)` [L111-L144]
  - `build_story_blocks(self, segments)` [L146-L267]
  - `story_text(self, segments)` [L269-L285]
  - `add_story_to_docx(self, document, segments)` [L287-L301]
  - `_get_transcript_text_slice(self, start, end)` [L303-L310]
  - `export_cue_sheet(self, destination_path)` [L312-L344] — *Export story/song segments to a standard .cue sheet.*
  - `export_tracklist(self, destination_path)` [L346-L376] — *Export story/song segments as YouTube chapters / tracklist formatted text.*
  - `_get_unselected_audio_mode_pref(self)` [L378-L383]
  - `export_reaper_project(self, destination_path, unselected_audio_mode)` [L385-L418] — *Export story segments as a Cockos REAPER project file (.rpp).*
  - `export_samplitude_edl(self, destination_path, unselected_audio_mode)` [L420-L453] — *Export story segments as a Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `export_audacity_labels(self, destination_path, unselected_audio_mode)` [L455-L487] — *Export story segments as an Audacity Label Track (.txt).*
  - `export_audition_xml(self, destination_path, unselected_audio_mode)` [L489-L522] — *Export story segments as Adobe Audition / Final Cut Pro XML (.xml).*
  - `export_daw_marker_csv(self, destination_path, unselected_audio_mode)` [L524-L556] — *Export story segments as a Universal DAW Marker List (.csv).*
  - `copy_youtube_chapters_to_clipboard(self)` [L558-L575] — *Format story segments as YouTube chapters and copy them directly to the system clipboard.*
  - `export_timeline_interchange(self, formats, base, options, directory, scope, is_custom_location)` [L577-L774] — *Export multi-platform timeline and DAW interchange project files.*

### `export_media_clipper.py` (211 lines)
*Radio & TV Story Segmenter — Media Clipper & Audio Track Renderer.*
- **class `ExportMediaClipperMixin`** (lines 26–211):
  *Provides audio/video track rendering, story clip extraction, and YouTube media handling.*
  - `cancel_export(self)` [L29-L34] — *Flag the running export operation to halt at the next iteration.*
  - `extract_media(self, start, end, output_file, fade_in, fade_out, cancel_check)` [L36-L63] — *Export a media range using the same container/format as the imported file,*
  - `extract_audio(self, start, end, output_file)` [L65-L71] — *Backward-compatible helper for older project/export code.*
  - `_handle_youtube_export_result(self, result)` [L73-L211]

### `export_story_pipeline.py` (979 lines)
*Radio & TV Story Segmenter — Story & Full Episode Export Pipeline.*
- **class `ExportStoryPipelineMixin`** (lines 35–979):
  *Provides story batch export and full episode export orchestration.*
  - `_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L38-L68]
  - `_do_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L70-L391]
  - `export_selected_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L393-L458]
  - `export_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L460-L521]
  - `export_full_and_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L523-L607]
  - `export_full_episode(self, custom_formats, custom_base, custom_options, directory, show_completion, progress_dialog, progress_value, is_custom_location)` [L609-L955]
  - `perform_stories_export(self, target_stories, custom_formats, custom_base, custom_options, directory, show_completion, is_custom_location)` [L957-L979]

### `gpu_acceleration.py` (276 lines)
*Radio & TV Segmenter v1.1.1 — optional GPU acceleration responsibilities.*
- **class `GpuAccelerationInstallWorker(QObject)`** (lines 19–47):
  - `__init__(self, force_rebuild)` [L23-L25]
  - `run(self)` [L27-L47]
- **class `GpuAccelerationMixin`** (lines 50–276):
  - `gpu_acceleration_settings_key(self)` [L51-L52]
  - `is_gpu_acceleration_enabled(self)` [L54-L58]
  - `is_gpu_transcription_enabled(self)` [L60-L64]
  - `is_gpu_translation_enabled(self)` [L66-L70]
  - `is_gpu_diarization_enabled(self)` [L72-L76]
  - `is_gpu_acceleration_installed(self)` [L78-L82]
  - `gpu_worker_launch_info(self)` [L84-L127] — *If GPU acceleration is installed and enabled, returns*
  - `is_diarization_gpu_enabled(self)` [L129-L130]
  - `open_gpu_acceleration_settings(self)` [L132-L215]
  - `_start_gpu_acceleration_install(self, parent_dialog)` [L217-L240]
  - `_on_gpu_install_progress(self, percent_or_msg, message)` [L242-L251]
  - `_on_gpu_install_finished(self, error)` [L253-L254]
  - `_gpu_install_thread_cleanup(self)` [L256-L276]

### `id3_editor.py` (704 lines)
*ID3 Tag Editor module for Radio & TV Segmenter.*
- **class `ID3TagEditorDialog(QDialog)`** (lines 336–704):
  *PySide6 GUI Dialog for viewing, editing, auto-filling, and saving ID3 tags on MP3 files.*
  - `__init__(self, parent, mp3_path)` [L339-L362]
  - `_build_ui(self)` [L364-L517]
  - `_browse_mp3(self)` [L519-L529]
  - `_load_active_audio(self)` [L531-L544]
  - `load_tags_from_file(self)` [L546-L574]
  - `_update_art_preview(self)` [L576-L589]
  - `_browse_cover_art(self)` [L591-L614]
  - `_clear_cover_art(self)` [L616-L619]
  - `_autofill_from_project(self)` [L621-L671]
  - `save_tags(self)` [L673-L704]
- **Functions**:
  - `_encode_synchsafe(size)` [L61-L67] — *Encode an integer as a 4-byte ID3v2 synchsafe integer (7 bits per byte).*
  - `_decode_synchsafe(data)` [L70-L74] — *Decode a 4-byte synchsafe integer.*
  - `read_id3_tags(file_path)` [L77-L222] — *Reads ID3 tag metadata from an MP3 file.*
  - `write_id3_tags(file_path, tags)` [L225-L333] — *Writes or updates ID3v2 tags in an MP3 file.*

### `installer/pyinstaller/torch_dll_hook.py` (70 lines)
*PyInstaller runtime hook for Windows ML/native DLL resolution.*

### `media_batch.py` (1699 lines)
*Radio & TV Segmenter v1.1.1 — media batch responsibilities.*
- **class `MediaBatchMixin`** (lines 19–1699):
  - `probe_media_duration(self, path)` [L20-L34] — *Probe duration locally so video timelines can be populated immediately.*
  - `_track_worker_thread(self, thread)` [L36-L48] — *Keep a strong reference to active worker threads so Python GC never destroys them while executing.*
  - `stop_waveform_worker(self, timeout_ms)` [L50-L81] — *Stop the current waveform worker completely before replacing it or closing.*
  - `start_video_thumbnail_generation(self, force_regenerate)` [L83-L139]
  - `_video_thumbnail_thread_finished(self)` [L141-L148]
  - `_video_thumbnails_finished(self, items)` [L150-L156]
  - `stop_video_thumbnail_worker(self, timeout_ms)` [L158-L186]
  - `regenerate_waveform(self)` [L188-L198] — *Force recalculation of waveform peaks by clearing disk cache and restarting generation.*
  - `regenerate_video_thumbnails(self)` [L200-L213] — *Force regeneration of video filmstrip thumbnails.*
  - `load_waveform_async(self, force_regenerate)` [L215-L253]
  - `_waveform_finished(self, peaks, cancelled)` [L255-L268]
  - `_waveform_thread_finished(self)` [L270-L274]
  - `open_batch_processing_dialog(self)` [L276-L380]
  - `_batch_next_media(self)` [L382-L491]
  - `_batch_next_document(self)` [L493-L521]
  - `_batch_document_error(self, msg)` [L523-L532] — *Handles document batch translation errors safely.*
  - `_load_user_preferences(self)` [L534-L617]
  - `set_thumbnail_position(self, position)` [L619-L623]
  - `_remember_saved_project(self, path)` [L625-L656] — *Remember only projects that have actually been saved.*
  - `_dialog_directory(self, fallback)` [L658-L670]
  - `_remember_open_directory(self, path)` [L672-L679]
  - `_sync_startup_project_actions(self)` [L681-L687] — *Synchronize the Project Settings startup radio/check actions.*
  - `set_startup_project_mode(self, mode)` [L689-L695] — *Set the startup project policy.*
  - `restore_last_opened(self)` [L697-L833] — *Apply startup policy and offer recovery from a newer autosave snapshot.*
  - `toggle_speaker_labels(self, checked)` [L835-L838]
  - `toggle_timestamps(self, checked)` [L840-L847]
  - `toggle_milliseconds(self, checked)` [L849-L856]
  - `toggle_waveform_view(self, checked)` [L858-L862]
  - `toggle_thumbnail_view(self, checked)` [L864-L868]
  - `choose_default_project_directory(self)` [L870-L885]
  - `open_document_path(self, path)` [L887-L919]
  - `open_clear_cache_dialog(self)` [L921-L934]
  - `open_glossary_dialog(self)` [L936-L1174] — *Edit persistent terminology used by every ASR and translation backend.*
  - `_save_glossary(self)` [L1176-L1177]
  - `add_to_glossary(self, text)` [L1179-L1190]
  - `apply_glossary_to_whisper_context(self)` [L1192-L1203]
  - `add_custom_speaker_to_glossary(self, name)` [L1205-L1207]
  - `set_language(self, language, persist)` [L1209-L1230]
  - `_apply_localization(self)` [L1232-L1269]
  - `update_story_segment_terminology(self)` [L1271-L1375] — *Update all user-facing labels and tooltips to use 'Song' in Music mode and 'Story' in Voice mode.*
  - `open_document(self)` [L1377-L1429]
  - `export_text_file(self)` [L1431-L1439]
  - `open_media(self)` [L1441-L1450]
  - `prepare_for_new_media(self)` [L1452-L1475] — *Checks for unsaved changes before loading new media.*
  - `_batch_media_error(self, message)` [L1477-L1484]
  - `_batch_save_project_file(self)` [L1486-L1510] — *Saves project .json to dedicated directory structure during batch processing.*
  - `_batch_export_current(self)` [L1512-L1594] — *Handles automatic export or project saving during batch processing.*
  - `load_media_file(self, filename, source, restore_adjacent_project)` [L1596-L1693]
  - `open_audio(self)` [L1695-L1696]
  - `handle_media_drop(self, filename)` [L1698-L1699]

### `model_install_workers.py` (189 lines)
*Radio & TV Segmenter — Model Download and Installation Background Workers.*
- **class `WhisperModelInstallWorker(QObject)`** (lines 57–140):
  *Background worker for downloading Whisper, Parakeet, and FastConformer models.*
  - `__init__(self, model_name, parent)` [L63-L66]
  - `cancel(self)` [L68-L70] — *Request cancellation of active download.*
  - `run(self)` [L72-L140] — *Execute download in background thread.*
- **class `DiarizationModelInstallWorker(QObject)`** (lines 143–189):
  *Background worker for downloading WeSpeaker ResNet34/CAM++ ONNX diarization models.*
  - `__init__(self, parent)` [L149-L151]
  - `cancel(self)` [L153-L155] — *Request cancellation of active download.*
  - `run(self)` [L157-L189] — *Execute download in background thread.*
- **Functions**:
  - `get_diarization_model_dir()` [L35-L37] — *Return canonical directory for WeSpeaker ONNX diarization models.*
  - `is_diarization_model_available()` [L40-L54] — *Check if a valid WeSpeaker ONNX model is present in candidate directories.*

### `model_management.py` (966 lines)
*Radio & TV Segmenter v1.1.1 — model management responsibilities.*
- **class `ModelManagementMixin`** (lines 52–966):
  - `model_cache_candidates(self, model_name)` [L53-L140] — *Return all potential candidate directories where model weights might be stored.*
  - `model_cache_path(self, model_name)` [L142-L154]
  - `is_whisper_model_available(self, model_name)` [L156-L185]
  - `refresh_whisper_model_chooser(self)` [L187-L211]
  - `current_whisper_model(self)` [L213-L218]
  - `update_whisper_model_tooltip(self)` [L220-L226]
  - `set_whisper_model_from_ui(self, index)` [L228-L242]
  - `translation_model_display_name(self, variant)` [L244-L246]
  - `translation_model_root(self, variant)` [L248-L249]
  - `refresh_translation_model_chooser(self)` [L251-L261]
  - `set_translation_model_from_ui(self, index)` [L263-L272]
  - `prompt_translation_model(self)` [L274-L282]
  - `open_model_cleanup_dialog(self)` [L284-L640] — *Unified local model manager for Whisper and OPUS-MT models.*
  - `purge_all_data_action(self, parent_widget, on_complete)` [L642-L714] — *Purge all downloaded AI models, log files, updater cache, and translation runtimes.*
  - `open_translation_model_manager(self)` [L716-L718]
  - `install_whisper_model_for_manager(self, model_name, dialog)` [L720-L748]
  - `cancel_model_installation(self)` [L750-L755]
  - `_on_model_install_progress(self, percent, message)` [L757-L767]
  - `_install_whisper_model_background(self, model_name)` [L769-L807]
  - `_model_install_finished(self, error)` [L809-L810]
  - `_model_install_thread_finished(self)` [L812-L866]
  - `_poll_model_install(self, dialog)` [L868-L870]
  - `install_diarization_model_for_manager(self, dialog)` [L872-L900] — *Install or repair the WeSpeaker ResNet34 ONNX diarization voice embedding model.*
  - `install_translation_models_for_manager(self, from_code, to_code, variant, dialog)` [L902-L940] — *Install an OPUS-MT model through the translation plugin's isolated runtime.*
  - `_translation_manager_install_finished(self, from_code, to_code, variant, dialog)` [L943-L956]
  - `_translation_manager_install_error(self, message, dialog)` [L958-L966]
- **Functions**:
  - `_translation_worker_class()` [L30-L33] — *Load translation implementation only when the translation plugin is installed.*
  - `_translation_plugin_installed(self)` [L35-L41]

### `playback_controller.py` (330 lines)
*Radio & TV Story Segmenter — Media Player Transport & Playback Controller.*
- **class `PlaybackControllerMixin`** (lines 25–330):
  *Provides audio/video media player transport, scrubbing, and fade controls.*
  - `is_video_file(self, path)` [L28-L33]
  - `update_video_preview_state(self)` [L35-L39]
  - `toggle_video_preview(self, checked)` [L41-L62]
  - `handle_scrub_position(self, seconds)` [L64-L67]
  - `execute_scrub_seek(self)` [L69-L76]
  - `eventFilter(self, watched, event)` [L78-L161]
  - `set_skip_seconds_from_ui(self, value)` [L163-L170]
  - `set_playback_rate(self, rate)` [L172-L184]
  - `toggle_play(self)` [L186-L208]
  - `stop_audio(self)` [L210-L220]
  - `seek_to(self, seconds)` [L222-L235]
  - `seek_relative(self, delta_seconds)` [L237-L243]
  - `audio_position_changed(self, position)` [L245-L252]
  - `get_fade_volume_factor_at_time(self, t)` [L254-L297] — *Calculate the real-time audio volume fade factor [0.0, 1.0] for position `t`.*
  - `update_realtime_fade_volume(self)` [L299-L320] — *Modulate QAudioOutput volume in real-time according to story fade envelopes.*
  - `_on_fade_timer_tick(self)` [L322-L324]
  - `audio_duration_changed(self, duration)` [L326-L330]

### `playback_preferences.py` (640 lines)
*Radio & TV Story Segmenter — Playback Preferences & Application Facade.*
- **Public Exports (`__all__`)**: PlaybackPreferencesMixin, RestoreSelectedSettingsDialog, ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, PreferencesResetMixin, ProjectStateMixin
- **class `PlaybackPreferencesMixin(ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, ProjectStateMixin)`** (lines 51–640):
  *Aggregates all playback, preferences, styling, and application lifecycle mixins.*
  - `_install_diagnostic_logging(self)` [L54-L181] — *Install startup-safe diagnostics that never depend on the GUI widgets.*
  - `export_activity_log(self)` [L183-L216] — *Export session activity log entries to a timestamped plain-text file.*
  - `log_activity(self, action_text, mark_dirty)` [L218-L255]
  - `handle_activity_click(self, item)` [L257-L260]
  - `restore_snapshot(self, index)` [L262-L301]
  - `clear_activity_log(self)` [L303-L306]
  - `trigger_find_next(self)` [L308-L314] — *Find Next shortcut (F3) handler: advances to next search match.*
  - `open_diagnostic_log_folder(self)` [L316-L331]
  - `show_about_dialog(self)` [L333-L372]
  - `check_for_updates(self, interactive)` [L374-L385] — *Open the Check for Updates dialog to query GitHub releases and install updates.*
  - `trigger_silent_update_check(self)` [L387-L412] — *Perform a background update check without showing UI unless an update is found.*
  - `apply_audio_output_device(self, device_name, volume)` [L414-L438] — *Apply selected audio output device and volume to the active player.*
  - `show_licenses_dialog(self)` [L440-L479]
  - `on_expected_speakers_changed(self, value)` [L481-L491] — *Kept as a public hook in case a future toolbar control adjusts the expected-speakers hint directly.*
  - `on_diarization_sensitivity_changed(self, value)` [L493-L503] — *Public hook for adjusting speaker separation sensitivity.*
  - `update_auto_save_timer(self)` [L505-L509]
  - `prompt_set_whisper_model(self)` [L511-L514]
  - `prompt_set_skip_seconds(self)` [L516-L530]
  - `prompt_set_auto_detect_thresholds(self)` [L532-L598]
  - `prompt_set_auto_save(self)` [L600-L618]
  - `trigger_auto_save(self)` [L620-L640]

### `plugin_dialogs.py` (458 lines)
*GitHub plugins dialogs, batch download workers, and PluginManagerDialog.*
- **class `GitHubPluginsWorker(QThread)`** (lines 42–102):
  *Fetches list of available plugins from GitHub release assets and official catalog.*
  - `__init__(self, repo, parent)` [L46-L48]
  - `run(self)` [L50-L102]
- **class `GitHubDownloadWorker(QThread)`** (lines 105–163):
  *Downloads and installs a `.rtvs-addon` plugin package from GitHub releases.*
  - `__init__(self, plugin_meta, plugins_dir, repo, parent)` [L109-L113]
  - `run(self)` [L115-L163]
- **class `GitHubBatchDownloadWorker(QThread)`** (lines 166–214):
  *Batch installs all missing or outdated official plugins.*
  - `__init__(self, plugins_to_install, plugins_dir, repo, parent)` [L171-L175]
  - `run(self)` [L177-L214]
- **class `GitHubPluginsDialog(QDialog)`** (lines 217–306):
  *Browse and install official and community plugins from GitHub releases.*
  - `__init__(self, plugin_manager, parent)` [L220-L252]
  - `fetch_catalog(self)` [L254-L259]
  - `on_catalog_fetched(self, success, catalog, err)` [L261-L267]
  - `populate_table(self)` [L269-L284]
  - `install_plugin(self, meta)` [L286-L296]
  - `on_installed(self, success, pid, msg)` [L298-L306]
- **class `PluginManagerDialog(QDialog)`** (lines 309–458):
  *Main management dialog for discovering, enabling, disabling, installing, and removing plugins.*
  - `__init__(self, plugin_manager, parent)` [L312-L362]
  - `refresh_list(self)` [L364-L378]
  - `on_selection_changed(self)` [L380-L409]
  - `on_enable_toggled(self, enabled)` [L411-L421]
  - `install_local_addon(self)` [L423-L453]
  - `browse_github_catalog(self)` [L455-L458]

### `plugins/__init__.py` (6 lines)
*Radio & TV Segmenter — Plugin Architecture Package.*
- **Public Exports (`__all__`)**: BasePlugin, PluginManifest

### `plugins/base.py` (207 lines)
*Radio & TV Segmenter — Plugin Base Interfaces and Manifest.*
- **class `PluginManifest`** (lines 11–64):
  *Metadata describing a plugin, parsed from manifest.json.*
  - `from_dict(cls, data)` [L33-L54]
  - `from_file(cls, path)` [L57-L64]
- **class `BasePlugin`** (lines 67–167):
  *Base class for all Radio & TV Segmenter plugins.*
  - `__init__(self, manifest, app)` [L78-L81]
  - `id(self)` [L84-L85]
  - `name(self)` [L88-L89]
  - `version(self)` [L92-L93]
  - `is_enabled(self)` [L96-L97]
  - `get_enabled(self)` [L99-L100]
  - `set_enabled(self, enabled)` [L102-L109]
  - `on_load(self)` [L111-L115] — *Called immediately after the plugin module is loaded.*
  - `on_unload(self)` [L117-L119] — *Called when plugin is about to be unloaded or application closes.*
  - `on_enable(self)` [L121-L123] — *Called when the user enables the plugin.*
  - `on_disable(self)` [L125-L127] — *Called when the user disables the plugin.*
  - `get_export_actions(self)` [L129-L131] — *Return list of (Action Label, callback_function) for Export menu.*
  - `get_export_destinations(self)` [L133-L135] — *Return list of ExportDestination providers to embed into UnifiedExportDialog.*
  - `get_tools_actions(self)` [L137-L139] — *Return list of (Action Label, callback_function) for Tools menu.*
  - `get_story_actions(self, story)` [L141-L143] — *Return list of (Action Label, callback_function) for story context menu.*
  - `create_story_metadata_widget(self, parent)` [L145-L147] — *Return a QWidget to be embedded into the Stories panel for metadata editing, or None.*
  - `on_story_selected(self, story)` [L149-L151] — *Called when active story selection changes in the main editor.*
  - `get_preferences_widget(self, parent)` [L153-L155] — *Return a QWidget to be embedded into the Preferences dialog, or None.*
  - `save_preferences(self, widget)` [L157-L159] — *Called when the user saves the Preferences dialog.*
  - `on_project_loaded(self, project_data)` [L161-L163] — *Called when an .rtvs project is loaded. Allows reading plugin metadata.*
  - `on_project_saving(self, project_data)` [L165-L167] — *Called before an .rtvs project is saved. Allows injecting plugin metadata.*
- **class `ExportDestination`** (lines 170–206):
  *Base class for plugin-provided export destinations in UnifiedExportDialog.*
  - `__init__(self, id, title, description, icon, button_label)` [L173-L186]
  - `create_widget(self, parent, main_window)` [L188-L190] — *Create the configuration and preview widget embedded into the destination tab.*
  - `on_scope_changed(self, scope, stories)` [L192-L194] — *Called when export scope changes in the dialog (full, selected, all).*
  - `validate(self)` [L196-L198] — *Validate destination settings before export begins. Returns (ok, error_msg).*
  - `get_export_data(self)` [L200-L202] — *Collect export parameters to include in the final dialog result.*
  - `execute_export(self, main_window, export_data, progress_dialog)` [L204-L206] — *Execute the export action for this destination.*

### `plugins/gdocs/__init__.py` (6 lines)
*Google Docs & Drive Exporter Plugin for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: Plugin

### `plugins/gdocs/auth.py` (631 lines)
*Google Docs & Drive Exporter — OAuth 2.0 Authentication Engine.*
- **class `_OAuthCallbackHandler(BaseHTTPRequestHandler)`** (lines 157–245):
  *Local loopback HTTP request handler capturing and validating the authorization code.*
  - `do_GET(self)` [L161-L214]
  - `_render_html_response(self, success, title, message)` [L216-L241]
  - `log_message(self, format, *args)` [L243-L245]
- **class `GoogleDocsAuthManager`** (lines 248–631):
  *Manages Google OAuth 2.0 authorization, PKCE verification, token storage, and refresh.*
  - `__init__(self)` [L251-L254]
  - `get_client_credentials(self)` [L256-L282] — *Return (client_id, client_secret).*
  - `save_client_credentials(self, client_id, client_secret)` [L284-L299] — *Save custom client credentials (advanced / self-hosted setup).*
  - `reset_to_default_credentials(self)` [L301-L313] — *Reset to the built-in production client ID.*
  - `is_using_custom_client(self)` [L315-L318] — *Return True if the user has configured custom OAuth credentials.*
  - `_load_tokens(self)` [L320-L338] — *Load tokens securely from system keyring or machine-ciphered storage.*
  - `_save_tokens(self, tokens)` [L340-L354] — *Save token dictionary to OS keyring with machine-cipher fallback.*
  - `logout(self, revoke_remote)` [L356-L379] — *Clear all stored tokens, credentials, and optionally revoke grant with Google.*
  - `is_authenticated(self)` [L381-L385] — *Return True if we have a refresh token or an unexpired access token.*
  - `get_user_email(self)` [L387-L391] — *Return the authenticated user's email address if available.*
  - `get_authenticated_email(self)` [L393-L395] — *Alias for get_user_email() ensuring compatibility across export destinations.*
  - `get_valid_access_token(self, force_refresh)` [L397-L414] — *Return a valid access token, automatically refreshing if expired or forced.*
  - `refresh_access_token(self)` [L416-L460] — *Use the refresh token to obtain a fresh access token.*
  - `start_loopback_auth(self, parent_widget, port, timeout)` [L462-L631] — *Start local loopback server, launch system browser with PKCE, and exchange auth code.*
- **Functions**:
  - `generate_pkce_pair()` [L77-L89] — *Generate high-entropy PKCE code_verifier and S256 code_challenge per RFC 7636.*
  - `generate_oauth_state()` [L92-L94] — *Generate cryptographically secure 32-byte state token for CSRF protection.*
  - `parse_google_credentials_json(data_or_path)` [L97-L111] — *Extract (client_id, client_secret, project_id) from Google credentials.json content or path.*
  - `_get_keyring()` [L114-L120] — *Safely return keyring module if available.*
  - `_get_machine_cipher()` [L123-L133] — *Machine-bound obfuscation cipher for fallback storage when keyring is unavailable.*
  - `_encrypt_str(text)` [L136-L142]
  - `_decrypt_str(enc)` [L145-L154]

### `plugins/gdocs/comments.py` (115 lines)
*Google Docs & Drive Native Margin Comments and Anchoring Engine.*
- **Functions**:
  - `create_drive_comment(access_token, file_id, content, quoted_text, anchor_info)` [L16-L63] — *Create a native margin comment attached to a document file via Google Drive API.*
  - `list_drive_comments(access_token, file_id, include_deleted)` [L66-L85] — *Retrieve all margin comments and discussion threads from a document.*
  - `attach_editorial_notes_as_comments(access_token, file_id, comment_anchors)` [L88-L115] — *Iterate through comment anchors and attach margin comments for editorial notes.*

### `plugins/gdocs/drive_folders.py` (445 lines)
*Google Drive Folder Management Engine and Folder Selector Dialog.*
- **Functions**:
  - `extract_folder_id_from_input(text)` [L40-L58] — *Extract Drive folder ID whether provided as raw ID or full Google Drive URL.*
  - `list_drive_folders(access_token, parent_id, page_size)` [L61-L100] — *Retrieve folders from Google Drive via Drive API v3.*
  - `get_drive_folder_info(access_token, folder_id)` [L103-L125] — *Get metadata for a specific folder ID.*
  - `create_drive_folder(access_token, folder_name, parent_id)` [L128-L166] — *Create a new folder in Google Drive.*
  - `get_or_create_project_subfolder(access_token, parent_folder_id, project_name)` [L169-L215] — *Find or create a dedicated project subfolder inside the target parent folder.*

### `plugins/gdocs/export_destination.py` (813 lines)
*Google Docs Export Destination for UnifiedExportDialog.*
- **class `GoogleDocsExportDestination(ExportDestination)`** (lines 64–813):
  *ExportDestination implementation for Google Docs.*
  - `__init__(self, plugin)` [L67-L81]
  - `create_widget(self, parent, main_window)` [L83-L382]
  - `_update_folder_display(self)` [L384-L391]
  - `_populate_stories_list(self)` [L393-L411]
  - `_select_all_stories(self)` [L413-L415]
  - `_deselect_all_stories(self)` [L417-L419]
  - `get_selected_story_indices(self)` [L421-L429]
  - `on_scope_changed(self, scope, stories)` [L431-L437] — *Called when export scope changes in the UnifiedExportDialog.*
  - `_on_select_folder_clicked(self)` [L439-L457]
  - `_on_create_folder_clicked(self)` [L459-L486]
  - `_on_use_root_clicked(self)` [L488-L494]
  - `_update_auth_status_label(self)` [L496-L505]
  - `_update_auth_ui_state(self)` [L507-L513]
  - `_on_auth_button_clicked(self)` [L515-L521]
  - `_on_disconnect_clicked(self)` [L523-L534]
  - `validate(self)` [L536-L548]
  - `get_export_data(self)` [L550-L593]
  - `_cleanup_temp_files(self)` [L595-L604] — *Clean up any temporary preview or export files if present.*
  - `closeEvent(self, event)` [L606-L609] — *Clean up temporary resources on dialog closure.*
  - `reject(self)` [L611-L614] — *Purge temp resources on dialog rejection.*
  - `done(self, r)` [L616-L619] — *Purge temp resources on dialog completion.*
  - `execute_export(self, main_window, export_data, progress_dialog)` [L621-L813]

### `plugins/gdocs/formatter.py` (874 lines)
*Google Docs Document Serializer and Formatting Engine.*
- **class `GoogleDocsSerializer`** (lines 232–804):
  *Serializes broadcast news transcript projects into Google Docs batchUpdate payloads.*
  - `__init__(self)` [L235-L236]
  - `serialize_document(self, document_title, stories, transcript_segments, project_metadata, scope, selected_story_indices, main_window, include_speakers, bold_speakers, include_story_chapters, include_timestamps, include_word_timestamps, include_comments, include_highlights, lang_code, secondary_segments, secondary_title, secondary_lang_code)` [L238-L804] — *Generate plain document text, Google Docs batchUpdate requests, and comment anchor points.*
- **Functions**:
  - `format_time(seconds)` [L25-L38] — *Format seconds into MM:SS or HH:MM:SS string.*
  - `utf16_len(s)` [L41-L45] — *Return the length of a string in UTF-16 code units.*
  - `is_sentence_end(word)` [L48-L51] — *Check if word ends with terminal punctuation.*
  - `clean_transcript_text(text, current_speaker, all_speakers)` [L54-L82] — *Strip redundant baked-in speaker labels from the start of segment text.*
  - `build_coherent_blocks(segments, main_window)` [L85-L229] — *Group whisper/asr segments into coherent speaker-turn paragraphs matching DOCX export layout.*
  - `create_google_doc(access_token, title, folder_id)` [L807-L847] — *Create a new Google Doc via Google Docs REST API and optionally place in folder.*
  - `batch_update_google_doc(access_token, doc_id, requests)` [L850-L874] — *Execute batchUpdate styling and text insertion requests on a Google Doc.*

### `plugins/gdocs/plugin.py` (232 lines)
*Google Docs & Drive Exporter Plugin implementation for Radio & TV Segmenter.*
- **class `Plugin(BasePlugin)`** (lines 33–232):
  *Google Docs & Drive Exporter plugin connecting RTVS to Google Docs REST API.*
  - `__init__(self, manifest, app)` [L36-L38]
  - `on_load(self)` [L40-L41]
  - `get_export_destinations(self)` [L43-L44]
  - `get_export_actions(self)` [L46-L49]
  - `get_tools_actions(self)` [L51-L54]
  - `open_export_dialog(self)` [L56-L58]
  - `open_review_dialog(self)` [L60-L62]
  - `get_preferences_widget(self, parent)` [L64-L148]
  - `_update_pref_status(self)` [L150-L162]
  - `_on_pref_login(self)` [L164-L170]
  - `_on_pref_logout(self)` [L172-L183]
  - `_on_import_credentials_json(self)` [L185-L210]
  - `_on_reset_default_client(self)` [L212-L222]
  - `save_preferences(self, widget)` [L224-L232]

### `plugins/gdocs/review.py` (329 lines)
*Google Docs Review and Comment Pull Integration.*
- **class `GoogleDocsReviewDialog(QDialog)`** (lines 143–329):
  *Dialog for inspecting Google Doc edits, margin comments, and applying transcript updates.*
  - `__init__(self, auth_manager, main_window, parent)` [L146-L155]
  - `setup_ui(self)` [L157-L226]
  - `on_fetch_clicked(self)` [L228-L273]
  - `populate_table(self)` [L275-L298]
  - `on_apply_clicked(self)` [L300-L329]
- **Functions**:
  - `extract_doc_id_from_url(url_or_id)` [L45-L54] — *Extract document ID from a full Google Docs URL or return raw ID.*
  - `fetch_google_doc_content(access_token, doc_id)` [L57-L82] — *Retrieve Google Doc JSON structure and extract plain text.*
  - `compute_segment_diffs(local_segments, remote_text)` [L85-L140] — *Compare local transcript segments with paragraphs from the remote Google Doc.*

### `plugins/google_sheets.py` (206 lines)
*Google Sheets Integration Engine for Radio & TV Segmenter.*
- **class `GoogleSheetsApiClient`** (lines 43–133):
  *Client for Google Sheets API v4 operations.*
  - `__init__(self, auth_manager)` [L46-L52]
  - `_get_headers(self, content_type, force_refresh)` [L54-L64]
  - `_execute_with_retry(self, req_builder, max_retries)` [L66-L78] — *Executes HTTP request, attempting automatic token refresh on 401/403.*
  - `create_spreadsheet(self, title, sheet_names)` [L80-L99] — *Create a new Google Spreadsheet with optional initial sheet tab names.*
  - `append_rows(self, spreadsheet_id, range_name, rows)` [L101-L117] — *Append one or more rows of tabular data to the specified sheet range.*
  - `write_table(self, spreadsheet_id, range_name, rows)` [L119-L129] — *Overwrite/write tabular data to the specified sheet range using PUT.*
  - `get_spreadsheet_url(self, spreadsheet_id)` [L131-L133] — *Return canonical Google Sheets browser URL.*
- **Functions**:
  - `format_story_rundown_table(stories, format_time_fn)` [L140-L166] — *Convert story segment metadata into standard broadcast rundown rows.*
  - `format_speaker_analytics_table(transcript_segments, format_time_fn)` [L169-L206] — *Calculate and format per-speaker talk-time metrics and percentages into tabular rows.*

### `plugins/manager.py` (1942 lines)
*Radio & TV Segmenter — Plugin Manager and Discovery Engine.*
- **class `PluginManager`** (lines 68–567):
  *Manages discovery, lifecycle, settings, and GUI injection of plugins.*
  - `__init__(self, app)` [L71-L76]
  - `get_user_plugins_dir(cls)` [L79-L89] — *Returns the user-writable plugins folder.*
  - `get_bundled_plugins_dir(cls)` [L92-L103] — *Returns the application installation plugins folder.*
  - `discover_plugins(self)` [L105-L173] — *Scans plugin directories (bundled/repository and user folder) and loads manifests of available plugins.*
  - `sync_bundled_updates(self)` [L175-L238] — *Automatically updates installed plugins in the user directory if a newer version is bundled with an app update.*
  - `ensure_packaged_addons(self)` [L240-L270] — *Ensures that all bundled directory-based plugins have up-to-date .rtvs-addon files created.*
  - `get_bundled_addons(cls)` [L273-L289] — *Returns a map of plugin_id -> Path of bundled .rtvs-addon packages.*
  - `is_plugin_installed(self, plugin_id)` [L291-L293] — *Checks whether the plugin is installed in the system.*
  - `is_plugin_enabled(self, plugin_id)` [L295-L303]
  - `plugin_runtime(self, plugin_id)` [L305-L309]
  - `set_plugin_enabled(self, plugin_id, enabled)` [L311-L323]
  - `load_all_plugins(self)` [L325-L330] — *Discovers and instantiates all enabled plugins.*
  - `load_plugin(self, plugin_id)` [L332-L384]
  - `unload_plugin(self, plugin_id)` [L386-L393]
  - `get_export_destinations(self)` [L395-L405] — *Returns all ExportDestination objects contributed by currently enabled plugins.*
  - `uninstall_plugin(self, plugin_id)` [L408-L489] — *Uninstalls and removes a plugin completely from the system.*
  - `install_addon(self, package_path, enable, expected_sha256)` [L491-L543] — *Installs a .rtvs-addon or .zip package into the user plugins directory.*
  - `package_addon(cls, plugin_folder, output_zip)` [L546-L567] — *Zips a plugin directory into an .rtvs-addon file.*
- **class `GitHubPluginsWorker(QThread)`** (lines 570–693):
  *Fetches list of available plugins from GitHub release assets and official catalog.*
  - `__init__(self, repo, parent)` [L574-L576]
  - `run(self)` [L578-L693]
- **class `GitHubDownloadWorker(QThread)`** (lines 696–758):
  *Downloads an add-on package in background with progress updates.*
  - `__init__(self, download_url, local_dest, fallback_local_addon, parent)` [L701-L706]
  - `cancel(self)` [L708-L709]
  - `run(self)` [L711-L758]
- **class `GitHubBatchDownloadWorker(QThread)`** (lines 761–866):
  *Downloads and installs a batch of add-on packages in sequence with progress updates.*
  - `__init__(self, items, manager, enable_after, parent)` [L766-L771]
  - `cancel(self)` [L773-L774]
  - `run(self)` [L776-L866]
- **class `GitHubPluginsDialog(QDialog)`** (lines 869–1400):
  *Browses, downloads, installs, and manages add-ons directly from GitHub releases with multi-selection.*
  - `__init__(self, manager, parent)` [L872-L887]
  - `setup_ui(self)` [L889-L992]
  - `fetch_plugins(self)` [L994-L1001]
  - `on_plugins_fetched(self, success, catalog, note)` [L1003-L1010]
  - `render_table(self)` [L1012-L1110]
  - `update_all_available_plugins(self)` [L1112-L1145] — *Finds all installed plugins with available updates and updates them in batch.*
  - `select_all_plugins(self)` [L1147-L1150]
  - `deselect_all_plugins(self)` [L1152-L1155]
  - `get_selected_items(self)` [L1157-L1175] — *Returns list of plugin items that are either checked or part of extended row selection.*
  - `on_selection_changed(self)` [L1177-L1201]
  - `download_and_install_plugin(self, item)` [L1203-L1222]
  - `download_selected_plugins(self)` [L1224-L1254]
  - `on_batch_download_finished(self, succeeded, failed, errors)` [L1256-L1276]
  - `enable_selected_plugins(self)` [L1278-L1295]
  - `disable_selected_plugins(self)` [L1297-L1314]
  - `uninstall_selected_plugins(self)` [L1316-L1336]
  - `on_download_progress(self, percent, msg)` [L1338-L1340]
  - `on_download_finished(self, success, file_path, error_msg, plugin_name, plugin_id)` [L1342-L1376]
  - `toggle_plugin(self, plugin_id, enable)` [L1378-L1386]
  - `uninstall_plugin(self, plugin_id, plugin_name)` [L1388-L1400]
- **class `PluginManagerDialog(QDialog)`** (lines 1403–1942):
  *GUI Dialog for viewing, managing, enabling, installing, and removing plugins with multi-selection.*
  - `__init__(self, manager, parent)` [L1406-L1414]
  - `setup_ui(self)` [L1416-L1530]
  - `on_download_github(self)` [L1532-L1535]
  - `select_all_plugins(self)` [L1537-L1538]
  - `deselect_all_plugins(self)` [L1540-L1541]
  - `get_selected_plugin_ids(self)` [L1543-L1556] — *Returns the list of plugin_ids selected via multi-row selection.*
  - `refresh_list(self)` [L1558-L1604]
  - `on_toggle_plugin(self, plugin_id, state)` [L1606-L1614]
  - `on_selection_changed(self)` [L1616-L1642]
  - `configure_selected_plugin(self)` [L1644-L1666]
  - `enable_selected_plugins(self)` [L1668-L1681]
  - `disable_selected_plugins(self)` [L1683-L1696]
  - `uninstall_selected_plugins(self)` [L1698-L1722]
  - `export_selected_plugins(self)` [L1724-L1774]
  - `on_install_addon(self)` [L1776-L1813]
  - `check_for_plugin_updates(self)` [L1815-L1894] — *Checks GitHub for newer versions of installed plugins without updating the core app.*
  - `run_batch_plugin_updates(self, update_items)` [L1896-L1930] — *Downloads and installs a batch of plugin updates.*
  - `on_open_folder(self)` [L1932-L1942]
- **Functions**:
  - `parse_plugin_version_tuple(version_str)` [L22-L37] — *Parse plugin version string into comparable numerical components and a stability weight.*
  - `is_newer_plugin_version(new_version, current_version)` [L40-L44] — *Returns True if new_version is strictly newer than current_version.*

### `plugins/translation/__init__.py` (9 lines)
*Language Translation Plugin for Radio & TV Segmenter.*

### `plugins/translation/plugin.py` (58 lines)
*Language Translation Plugin for Radio & TV Segmenter.*
- **class `Plugin(BasePlugin)`** (lines 14–58):
  *Translation plugin providing local language translation capabilities.*
  - `on_load(self)` [L17-L18]
  - `on_enable(self)` [L20-L30]
  - `on_disable(self)` [L32-L42]
  - `get_tools_actions(self)` [L44-L47]
  - `get_preferences_widget(self, parent)` [L49-L58]

### `plugins/translation/runtime_entry.py` (49 lines)
*CLI entry point for the isolated translation runtime.*
- **Functions**:
  - `emit(obj)` [L16-L18]
  - `main()` [L20-L46]

### `plugins/translation/support.py` (176 lines)
*Small dependency-light helpers shared by the translation plugin runtime.*
- **Functions**:
  - `configure_ssl_certificates()` [L7-L38] — *Ensure HTTPS certificate verification works seamlessly across macOS, Linux, and Windows.*
  - `get_app_data_dir()` [L46-L56]
  - `get_legacy_models_storage_dirs()` [L58-L75] — *Return historical fallback model storage directories to recognize previously downloaded models.*
  - `get_models_storage_dir()` [L77-L107]
  - `_has_required_model_files(model_dir)` [L109-L114]
  - `model_is_installed(from_code, to_code, variant)` [L116-L142] — *Check if an OPUS-MT translation model is installed on disk without loading ML libraries.*
  - `setup_runtime_environment()` [L144-L174]

### `plugins/translation/worker.py` (678 lines)
*Translation plugin worker.*
- **class `TranslationWorker(QObject)`** (lines 62–678):
  *Local OPUS-MT translation/model-management worker.*
  - `__init__(self, segments, from_code, to_code, install_if_missing, installation_only, resume_results, model_variant, status_only, parent, transcript, variant, device, glossary, **kwargs)` [L90-L143]
  - `model_root(cls, variant)` [L146-L147]
  - `model_dir(cls, from_code, to_code, variant)` [L150-L162]
  - `_has_required_model_files(cls, directory)` [L165-L173]
  - `_model_is_installed_in_dir(cls, directory)` [L176-L188]
  - `model_is_installed(cls, from_code, to_code, variant)` [L191-L192]
  - `model_repo(cls, from_code, to_code, variant)` [L195-L196]
  - `cancel(self)` [L198-L199]
  - `_download_file(self, repo, filename, destination, progress_start, progress_end, label, revision)` [L201-L270]
  - `_ensure_model_installed(self)` [L272-L367] — *Download a complete Hugging Face snapshot into a staging directory and publish atomically.*
  - `_get_optimal_cpu_threads(self)` [L369-L377] — *Compute optimal thread count for translation on CPU (capped to 4-8).*
  - `_ensure_ctranslate2_model(self, model_dir)` [L379-L416] — *Ensure an INT8-quantized CTranslate2 model exists in model_dir / 'ct2_int8'.*
  - `_load_local_translation(self)` [L418-L461]
  - `_translate_batches(self, engine_type, tokenizer, model_or_translator)` [L463-L637]
  - `run(self)` [L639-L678]

### `plugins/wordpress/__init__.py` (6 lines)
*WordPress Publisher Plugin for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: Plugin

### `plugins/wordpress/client.py` (1562 lines)
*WordPress Plugin — Client, Credential Storage, and Upload Engine.*
- **class `WordPressClient`** (lines 341–711):
  *Client for WordPress REST API using Application Passwords.*
  - `__init__(self, site_url, username, password)` [L344-L356]
  - `is_configured(self)` [L358-L365] — *Return True if site_url, username, and password are all non-empty and non-placeholder.*
  - `_get_auth(self)` [L367-L368]
  - `_discover_canonical_base(self)` [L370-L381] — *Pre-detect canonical site URL and REST base to prevent redirect failures.*
  - `_post_request(self, url, json_data, headers, timeout)` [L383-L407] — *Issue an HTTP POST with manual redirect protection to keep POST method & Auth header.*
  - `_post_multipart(self, url, path, upload_filename, mime_type, timeout)` [L409-L432] — *Issue a multipart file POST with manual redirect protection.*
  - `test_connection(self)` [L434-L457] — *Test credentials against /wp/v2/users/me or /wp/v2/posts.*
  - `get_categories(self)` [L459-L475] — *Fetch post categories from WordPress.*
  - `get_authors(self)` [L477-L574] — *Fetch PublishPress Authors profiles, including guest authors without users.*
  - `upload_media(self, file_path, filename)` [L576-L622] — *Upload media using WordPress's standard multipart API, with raw fallback.*
  - `create_post(self, title, content, excerpt, status, category_ids, author_ids, author_term_ids, featured_media_id)` [L624-L667] — *Create a post in WordPress.*
  - `update_post(self, post_id, content, title, excerpt, status, category_ids, featured_media_id)` [L669-L711] — *Update an existing post in WordPress.*
- **class `WordPressSettingsDialog(QDialog)`** (lines 714–866):
  *Dialog for entering and testing WordPress site credentials.*
  - `__init__(self, parent)` [L717-L818]
  - `_test_connection(self)` [L820-L841]
  - `_save_settings(self)` [L843-L866]
- **class `WordPressPreferencesPage(QWidget)`** (lines 880–1021):
  *Preferences page widget for WordPress integration inside the application Preferences dialog.*
  - `__init__(self, parent, app)` [L883-L887]
  - `setup_ui(self)` [L889-L973]
  - `_test_connection(self)` [L975-L994]
  - `save_preferences(self, dialog)` [L996-L1021]
- **Functions**:
  - `_get_keyring()` [L48-L54] — *Safely return keyring module if available.*
  - `_get_wp_fallback_cipher()` [L57-L71] — *Best-effort symmetric cipher bound to this machine, used only for*
  - `_get_wp_password(username)` [L74-L99] — *Retrieve the stored WordPress application password.*
  - `_set_wp_password(username, password)` [L102-L136] — *Store the WordPress application password securely.*
  - `format_rich_text_to_html(text, auto_link_urls, main_window)` [L139-L239] — *Format rich text, Markdown hyperlinks, and URLs into safe HTML for WordPress posts.*
  - `format_parent_episode_notice(episode_title, episode_url, template)` [L242-L275] — *Format the parent episode notice block to inject into a story post.*
  - `build_episode_stories_toc(stories)` [L278-L313] — *Build a Gutenberg Table of Contents block listing all stories in the episode.*
  - `generate_wp_excerpt(text, max_words)` [L316-L326] — *Generate a clean WordPress-style post excerpt from text (standard 55 words).*
  - `is_wp_auth_error(err)` [L329-L338] — *Check if an error string or exception indicates an authentication or credential failure.*
  - `get_wp_client()` [L869-L877] — *Instantiate WordPressClient from stored settings if configured.*
  - `_group_segments_into_paragraphs(segments, min_words)` [L1024-L1072] — *Group consecutive segments with same speaker into natural paragraph blocks.*
  - `_build_audio_fade_filter(duration, fade_in, fade_out, fade_curve)` [L1075-L1103] — *Construct FFmpeg afade audio filter chain for story clips.*
  - `execute_wordpress_upload(main_window, client, post_title, post_excerpt, start, end, task_label, include_english, include_spanish, spanish_presentation, primary_language, author_ids, author_term_ids, category_ids, show_completion_dialog, media_filename, progress_callback, featured_image_path, parent_episode_info, link_parent_episode, parent_episode_template, parent_episode_pos, include_audio, fade_in, fade_out, fade_curve, apply_fades, accordion_pos)` [L1106-L1562] — *Extract media clip, upload to WordPress media library, and create draft post.*

### `plugins/wordpress/export_destination.py` (2080 lines)
*WordPress Export Destination for UnifiedExportDialog.*
- **class `WordPressExportTabWidget(QWidget)`** (lines 88–1645):
  *Configuration and preview panel for WordPress Draft Posts.*
  - `__init__(self, parent, main_window, metadata_editor_mode)` [L91-L110]
  - `_setup_ui(self)` [L112-L688]
  - `_on_wp_include_audio_toggled(self, checked)` [L690-L691]
  - `_update_wp_conn_status(self)` [L693-L701]
  - `_open_wp_settings(self)` [L703-L707]
  - `_filter_authors_list(self, text)` [L709-L713]
  - `_filter_categories_list(self, text)` [L715-L719]
  - `_on_title_edited(self, text)` [L721-L725]
  - `_on_excerpt_edited(self)` [L727-L730]
  - `_auto_generate_current_excerpt(self)` [L732-L739]
  - `_autofill_all_excerpts(self)` [L741-L747]
  - `_on_author_item_changed(self, item)` [L749-L756]
  - `_on_category_item_changed(self, item)` [L758-L764]
  - `_clear_current_authors(self)` [L766-L771]
  - `_clear_current_categories(self)` [L773-L777]
  - `_get_selected_story_indices(self)` [L779-L783]
  - `_apply_authors_to_selected_stories(self)` [L785-L818]
  - `_apply_categories_to_selected_stories(self)` [L820-L850]
  - `_apply_thumbnails_to_selected_stories(self)` [L852-L885]
  - `_apply_authors_to_all_posts(self)` [L887-L906]
  - `_apply_categories_to_all_posts(self)` [L908-L924]
  - `_apply_thumbnails_to_all_posts(self)` [L926-L946]
  - `_sync_post_to_project(self, idx)` [L948-L1039]
  - `save_all_posts_to_project(self)` [L1041-L1049] — *Persist all post metadata back into stories and project_metadata.*
  - `_update_post_list_item_label(self, idx)` [L1051-L1064]
  - `_on_wp_post_selection_changed(self, row)` [L1066-L1069]
  - `_get_editor_checked_authors(self)` [L1071-L1087]
  - `_set_editor_checked_authors(self, author_ids, author_term_ids)` [L1089-L1107]
  - `_get_editor_checked_categories(self)` [L1109-L1117]
  - `_set_editor_checked_categories(self, cat_ids)` [L1119-L1127]
  - `_get_wp_post_bounds(self, post_index)` [L1129-L1138]
  - `_sync_wp_slider_to_pos(self, pos)` [L1140-L1150]
  - `_on_wp_slider_value_changed(self, val)` [L1152-L1160]
  - `_on_wp_scrub_timer_timeout(self)` [L1162-L1166]
  - `_on_wp_step(self, delta_secs)` [L1168-L1176]
  - `_on_wp_sync_playhead(self)` [L1178-L1185]
  - `_load_post_editor_state(self, index)` [L1187-L1241]
  - `_on_wp_thumb_mode_changed(self)` [L1243-L1274]
  - `_capture_wp_frame(self, pos)` [L1276-L1326]
  - `_on_wp_browse_thumb(self)` [L1328-L1344]
  - `_cleanup_temp_files(self)` [L1346-L1355] — *Purge temporary frame grabs and preview images.*
  - `closeEvent(self, event)` [L1357-L1360] — *Clean up temp files on widget/dialog closure.*
  - `rebuild_post_items(self, scope)` [L1362-L1556]
  - `_populate_wp_export_metadata(self, force_refresh)` [L1558-L1611]
  - `_refresh_wp_metadata(self)` [L1613-L1645]
- **class `WordPressExportDestination(ExportDestination)`** (lines 1648–2028):
  *Export destination handler for WordPress REST API Draft Posts.*
  - `__init__(self, plugin)` [L1651-L1659]
  - `button_label(self)` [L1662-L1667]
  - `button_label(self, val)` [L1670-L1671]
  - `get_export_button_label(self)` [L1673-L1674]
  - `widget(self)` [L1677-L1678]
  - `widget(self, val)` [L1681-L1682]
  - `create_widget(self, parent, main_window)` [L1684-L1686]
  - `on_scope_changed(self, scope, stories)` [L1688-L1690]
  - `validate(self)` [L1692-L1708]
  - `get_export_data(self)` [L1710-L1729]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L1731-L2028]
- **class `WordPressPostMetadataDialog(QDialog)`** (lines 2031–2079):
  *Full-featured WordPress post & story metadata editor dialog.*
  - `__init__(self, parent, main_window, target_story_index)` [L2034-L2075]
  - `_on_save_and_close(self)` [L2077-L2079]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path, timeout)` [L64-L85]

### `plugins/wordpress/plugin.py` (893 lines)
*WordPress Publisher Plugin for Radio & TV Segmenter.*
- **class `WordPressPublishDialog(QDialog)`** (lines 91–518):
  *Publish a story or project to WordPress with featured image selection.*
  - `__init__(self, plugin, parent, story)` [L94-L109]
  - `setup_ui(self)` [L111-L264]
  - `load_custom_text_settings(self)` [L266-L279] — *Load persistent custom text defaults from application settings.*
  - `save_custom_text_defaults(self)` [L281-L287] — *Save active custom text, placement, and exclusion settings as persistent defaults.*
  - `load_metadata(self)` [L289-L330]
  - `do_capture_frame(self)` [L332-L342]
  - `on_image_mode_changed(self)` [L344-L359]
  - `on_browse_image(self)` [L361-L372]
  - `on_configure_credentials(self)` [L374-L380]
  - `on_publish(self)` [L382-L475]
  - `on_publish_finished(self, success, msg, post_data)` [L477-L511]
  - `closeEvent(self, event)` [L513-L518]
- **class `WordPressPublishWorker(QThread)`** (lines 521–558):
  - `__init__(self, client, title, content, excerpt, status, image_path)` [L524-L531]
  - `run(self)` [L533-L558]
- **class `WordPressStoryMetadataWidget(QGroupBox)`** (lines 561–837):
  *Clean, compact WordPress metadata launcher & inspector embedded in the Stories sidebar.*
  - `__init__(self, plugin, parent)` [L564-L576]
  - `setup_ui(self)` [L578-L666]
  - `refresh_targets_dropdown(self)` [L668-L691] — *Populate target_combo with Full Episode and all current project stories.*
  - `_on_target_changed(self, index)` [L693-L711]
  - `set_story(self, story)` [L713-L725] — *Called when user selects a story in the story list or timeline.*
  - `_get_active_wp_metadata(self)` [L727-L737]
  - `_load_current_target_metadata(self)` [L739-L792]
  - `_open_post_settings_dialog(self)` [L794-L800]
  - `_on_refresh_taxonomy(self)` [L802-L837]
- **class `Plugin(BasePlugin)`** (lines 840–892):
  *WordPress Plugin implementation hooking into RTVS.*
  - `__init__(self, manifest, app)` [L843-L845]
  - `on_load(self)` [L847-L848]
  - `get_export_destinations(self)` [L850-L852]
  - `get_export_actions(self)` [L854-L857]
  - `get_story_actions(self, story)` [L859-L863]
  - `create_story_metadata_widget(self, parent)` [L865-L867]
  - `on_story_selected(self, story)` [L869-L870]
  - `get_preferences_widget(self, parent)` [L872-L874]
  - `open_publish_dialog(self, parent, story)` [L876-L878]
  - `open_post_metadata_dialog(self, parent, story)` [L880-L892]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path, timeout)` [L66-L88] — *Extract a high quality single frame from a video using fast seeking FFmpeg.*

### `plugins/wordpress/wordpress_dialog.py` (884 lines)
*WordPress Export Tab Widget and Post Metadata Dialog.*
- **class `WordPressExportTabWidget(QWidget)`** (lines 79–842):
  *Configuration and preview panel for WordPress Draft Posts.*
  - `__init__(self, parent, main_window, metadata_editor_mode)` [L82-L101]
  - `_setup_ui(self)` [L103-L317]
  - `update_wp_pres_visibility(self)` [L319-L320]
  - `_update_wp_conn_status(self)` [L322-L323]
  - `_open_wp_settings(self)` [L325-L328]
  - `_filter_authors_list(self, text)` [L330-L331]
  - `_filter_categories_list(self, text)` [L333-L334]
  - `_on_title_edited(self, text)` [L336-L341]
  - `_on_excerpt_edited(self)` [L343-L347]
  - `_auto_generate_current_excerpt(self)` [L349-L358]
  - `_autofill_all_excerpts(self)` [L360-L367]
  - `_on_author_item_changed(self, item)` [L369-L375]
  - `_on_category_item_changed(self, item)` [L377-L382]
  - `_clear_current_authors(self)` [L384-L390]
  - `_clear_current_categories(self)` [L392-L398]
  - `_get_selected_story_indices(self)` [L400-L405]
  - `_apply_authors_to_selected_stories(self)` [L407-L415]
  - `_apply_categories_to_selected_stories(self)` [L417-L424]
  - `_apply_thumbnails_to_selected_stories(self)` [L426-L447]
  - `_apply_authors_to_all_posts(self)` [L449-L454]
  - `_apply_categories_to_all_posts(self)` [L456-L460]
  - `_apply_thumbnails_to_all_posts(self)` [L462-L481]
  - `_sync_post_to_project(self, idx)` [L483-L484]
  - `save_all_posts_to_project(self)` [L486-L487]
  - `_update_post_list_item_label(self, idx)` [L489-L493]
  - `_on_wp_post_selection_changed(self, row)` [L495-L499]
  - `_get_editor_checked_authors(self)` [L501-L513]
  - `_set_editor_checked_authors(self, author_ids, author_term_ids)` [L515-L525]
  - `_get_editor_checked_categories(self)` [L527-L535]
  - `_set_editor_checked_categories(self, cat_ids)` [L537-L546]
  - `_get_wp_post_bounds(self, post_index)` [L548-L553]
  - `_sync_wp_slider_to_pos(self, pos)` [L555-L563]
  - `_on_wp_slider_value_changed(self, val)` [L565-L574]
  - `_on_wp_scrub_timer_timeout(self)` [L576-L578]
  - `_on_wp_step(self, delta_secs)` [L580-L589]
  - `_on_wp_sync_playhead(self)` [L591-L600]
  - `_load_post_editor_state(self, index)` [L602-L633]
  - `_on_wp_thumb_mode_changed(self)` [L635-L650]
  - `_capture_wp_frame(self, pos)` [L652-L670]
  - `_on_wp_browse_thumb(self)` [L672-L685]
  - `rebuild_post_items(self, scope)` [L687-L802]
  - `_populate_wp_export_metadata(self, force_refresh)` [L804-L838]
  - `_refresh_wp_metadata(self)` [L840-L842]
- **class `WordPressPostMetadataDialog(QDialog)`** (lines 845–884):
  *Dialog for editing WordPress post metadata for an individual story.*
  - `__init__(self, parent, main_window, target_story_index)` [L848-L881]
  - `_on_save_and_close(self)` [L883-L884]
- **Functions**:
  - `generate_wp_excerpt(transcript_words, start_t, end_t)` [L59-L61]
  - `capture_video_frame(video_path, timestamp, output_path)` [L64-L76]

### `plugins/youtube/__init__.py` (9 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*

### `plugins/youtube/api.py` (368 lines)
*YouTube Data API v3 Client & Direct Video Upload Engine.*
- **class `YouTubeAuthManager`** (lines 61–123):
  *Specialized OAuth 2.0 PKCE manager for YouTube Data API v3 permissions.*
  - `__init__(self)` [L64-L70]
  - `is_authenticated(self)` [L72-L78] — *Return True if an access or refresh token is stored.*
  - `get_user_email(self)` [L80-L86] — *Return the authenticated user's email address if available.*
  - `get_authenticated_email(self)` [L88-L90] — *Return the authenticated user's email address if available.*
  - `get_valid_access_token(self, force_refresh)` [L92-L106] — *Return a valid access token, automatically refreshing if expired or forced.*
  - `get_authorization_url(self, port, state, code_challenge)` [L108-L123]
- **class `YouTubeApiClient`** (lines 126–368):
  *Production client for YouTube Data API v3.*
  - `__init__(self, auth_manager)` [L129-L130]
  - `_get_headers(self, content_type, force_refresh)` [L132-L140]
  - `get_channel_info(self)` [L142-L156] — *Fetch the authenticated user's YouTube channel snippet and statistics.*
  - `upload_video_resumable(self, video_path, title, description, tags, category_id, privacy_status, progress_callback, cancel_event, chunk_size)` [L158-L300] — *Upload video file using YouTube's Resumable Upload protocol.*
  - `set_thumbnail(self, video_id, image_path)` [L302-L323] — *Upload custom thumbnail for a video.*
  - `upload_caption_track(self, video_id, srt_content_or_path, language, name, is_draft)` [L325-L368] — *Upload Closed Captions (.srt track) directly to the uploaded YouTube video.*

### `plugins/youtube/export_destination.py` (834 lines)
*YouTube Export Destination for UnifiedExportDialog with Dual-Mode Publishing.*
- **class `YouTubeExportTabWidget(QWidget)`** (lines 85–604):
  *Configuration and preview panel for YouTube Publishing.*
  - `__init__(self, parent, main_window)` [L88-L103]
  - `_setup_ui(self)` [L105-L378]
  - `_on_mode_changed(self)` [L380-L394]
  - `_update_auth_status_ui(self)` [L396-L415]
  - `_on_toggle_auth(self)` [L417-L442]
  - `_get_yt_bounds(self)` [L444-L462]
  - `_on_yt_thumb_mode_changed(self)` [L464-L481]
  - `_update_yt_scrub_slider_range(self)` [L483-L492]
  - `_on_yt_slider_value_changed(self, value)` [L494-L500]
  - `_on_yt_step(self, delta_sec)` [L502-L507]
  - `_on_yt_sync_playhead(self)` [L509-L514]
  - `_schedule_yt_frame_preview(self)` [L516-L519]
  - `_on_yt_scrub_timer_timeout(self)` [L521-L535]
  - `_on_yt_browse_thumb(self)` [L537-L548]
  - `_cleanup_temp_files(self)` [L550-L559] — *Purge temporary thumbnail frame grabs.*
  - `closeEvent(self, event)` [L561-L564] — *Clean up temporary thumbnail files on closure.*
  - `reject(self)` [L566-L569] — *Ensure temp preview files are purged on dialog rejection.*
  - `done(self, r)` [L571-L574] — *Ensure temp preview files are purged on dialog completion.*
  - `populate_metadata(self)` [L576-L604] — *Builds default title, description, and chapter timestamps from current stories.*
- **class `YouTubeExportDestination(ExportDestination)`** (lines 607–834):
  *Export destination handler for YouTube Video Publishing.*
  - `__init__(self, plugin)` [L610-L618]
  - `create_widget(self, parent, main_window)` [L620-L622]
  - `on_scope_changed(self, scope, stories)` [L624-L626]
  - `validate(self)` [L628-L638]
  - `get_export_data(self)` [L640-L665]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L667-L677]
  - `_execute_direct_api_upload(self, main_window, export_data)` [L679-L834]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path)` [L67-L82]

### `plugins/youtube/guide_dialog.py` (147 lines)
*Interactive Assisted Upload Guide Dialog for YouTube Studio.*
- **class `YouTubeAssistedUploadGuideDialog(QDialog)`** (lines 24–147):
  *Post-export interactive guide dialog for YouTube Studio Assisted Publishing.*
  - `__init__(self, parent, files_dict, metadata)` [L27-L123]
  - `_copy_description(self)` [L125-L127]
  - `_copy_title(self)` [L129-L131]
  - `_copy_tags(self)` [L133-L135]
  - `_open_youtube_studio(self)` [L137-L138]
  - `_open_folder(self)` [L140-L147]

### `plugins/youtube/plugin.py` (234 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*
- **class `YouTubeSettingsDialog(QDialog)`** (lines 63–196):
  *Preferences dialog for YouTube Publishing (Direct API & Assisted Upload defaults).*
  - `__init__(self, parent)` [L66-L73]
  - `setup_ui(self)` [L75-L184]
  - `on_save(self)` [L186-L196]
- **class `Plugin(BasePlugin)`** (lines 199–234):
  *YouTube Video Publisher plugin hooking into RTVS.*
  - `on_load(self)` [L202-L203]
  - `get_export_destinations(self)` [L205-L207]
  - `get_export_actions(self)` [L209-L212]
  - `get_preferences_widget(self, parent)` [L214-L230]
  - `open_publish_dialog(self)` [L232-L234]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path)` [L45-L60]

### `preferences_dialog.py` (588 lines)
*Radio & TV Story Segmenter — Preferences Modal Dialog.*
- **class `PreferencesDialogMixin(PreferencesResetMixin)`** (lines 29–588):
  *Provides the main open_preferences_dialog method and settings persistence.*
  - `open_preferences_dialog(self, initial_category)` [L32-L588] — *Open the multi-category Preferences dialog.*

### `preferences_reset.py` (613 lines)
*Radio & TV Story Segmenter — Preferences Reset & Factory Defaults Engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 21–164):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L42-L125]
  - `_select_all(self)` [L127-L129]
  - `_deselect_all(self)` [L131-L133]
  - `_handle_reset(self)` [L135-L164]
- **class `PreferencesResetMixin`** (lines 167–613):
  *Provides methods for resetting settings to defaults across all app categories.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L170-L602] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L604-L613] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_reset_dialog.py` (617 lines)
*Radio & TV Segmenter — Preferences reset and factory default restore engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 20–163):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L41-L124]
  - `_select_all(self)` [L126-L128]
  - `_deselect_all(self)` [L130-L132]
  - `_handle_reset(self)` [L134-L163]
- **class `PreferencesResetMixin`** (lines 166–616):
  *Mixin providing settings reset and restore dialog actions.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L169-L605] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L607-L616] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_tabs.py` (1133 lines)
*Radio & TV Story Segmenter — Preferences Modal Tab Builders.*
- **Functions**:
  - `build_general_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L28-L166]
  - `build_shortcuts_tab(win, dialog, live_widgets)` [L169-L177]
  - `build_audio_hardware_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L180-L232]
  - `build_updates_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L235-L274]
  - `build_ai_models_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L277-L400]
  - `build_gpu_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L403-L511]
  - `build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L514-L628]
  - `build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L631-L721]
  - `build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L724-L847]
  - `build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L850-L1048]
  - `build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L1051-L1133]

### `preferences_tabs_core.py` (509 lines)
*Radio & TV Story Segmenter — Preferences Modal Core Tab Builders.*
- **Functions**:
  - `build_general_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L26-L164]
  - `build_shortcuts_tab(win, dialog, live_widgets)` [L167-L175]
  - `build_audio_hardware_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L178-L230]
  - `build_updates_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L233-L272]
  - `build_ai_models_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L275-L398]
  - `build_gpu_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L401-L509]

### `preferences_tabs_media.py` (641 lines)
*Radio & TV Story Segmenter — Preferences Modal Media & Workflow Tab Builders.*
- **Functions**:
  - `build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L22-L136]
  - `build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L139-L229]
  - `build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L232-L355]
  - `build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L358-L556]
  - `build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L559-L641]

### `preview_manager.py` (659 lines)
*AI Studio Web Preview Manager for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_project_version()` [L512-L521] — *Read PROJECT_VERSION from core_utils.py or prs_shared.py.*
  - `restore_preview(force)` [L524-L559] — *Ensure all preview scaffolding files exist with up-to-date version strings.*
  - `sync_version(version)` [L562-L606] — *Synchronize the application version into package.json, metadata.json, and index.html.*
  - `verify_preview()` [L609-L630] — *Verify that all preview files exist and are valid.*
  - `main()` [L633-L655]

### `process_lifecycle.py` (191 lines)
*Radio & TV Segmenter — Subprocess tracking and OS-level job object lifecycle isolation.*
- **Functions**:
  - `init_child_process_job_isolation()` [L20-L102] — *Initialize OS-level guarantees that child processes terminate when parent exits.*
  - `bind_subprocess_to_job(proc)` [L105-L137] — *Assign an individual process (by HANDLE or PID) to the Windows Job Object if needed.*
  - `register_process(proc)` [L140-L144] — *Register a QProcess or subprocess.Popen instance to track its lifecycle.*
  - `unregister_process(proc)` [L147-L149] — *Unregister a process when it exits naturally or is cleaned up.*
  - `get_registered_processes()` [L152-L154] — *Return a snapshot list of currently registered processes.*
  - `terminate_all_registered_processes()` [L160-L184] — *Terminate and wait on all active child processes upon application close.*

### `processing.py` (1148 lines)
*Radio & TV Segmenter v3.3.29 — processing responsibilities.*
- **class `RuntimeSetupWorker(QThread)`** (lines 56–85):
  *Runs runtime_manager.ensure_environment() off the GUI thread, so that*
  - `__init__(self, runtime_mgr, feature, parent, ensure_kwargs)` [L64-L69]
  - `cancel(self)` [L71-L72]
  - `run(self)` [L74-L85]
- **class `ProcessingMixin(TranscriptionProcessingMixin, DiarizationProcessingMixin, StoryDetectionProcessingMixin)`** (lines 92–1147):
  - `_ensure_runtime_environment_responsive(self, feature, **ensure_kwargs)` [L103-L193] — *Make sure the isolated venv for `feature` is ready before*
  - `cancel_current_process(self)` [L195-L327]
  - `commit_story_change(self, old_stories, new_stories, description)` [L329-L344]
  - `apply_story_selection_indices(self, selected_rows, seek)` [L346-L413]
  - `on_timeline_story_clicked(self, index)` [L415-L425] — *Handle user clicking a story region directly on the timeline canvas.*
  - `story_selection_changed(self)` [L427-L444]
  - `handle_timeline_multi_selection(self, selected_indices)` [L446-L457]
  - `set_tools_actions_enabled(self, enabled)` [L459-L493]
  - `stop_story_detection_worker(self, timeout_ms)` [L495-L518] — *Cancel Story Detection and wait for its QThread to finish.*
  - `stop_all_processing(self, timeout_ms)` [L520-L535] — *Stop every local processing job before changing media/projects or exiting.*
  - `confirm_stop_processing_for_media_change(self)` [L537-L565]
  - `worker_thread_finished(self)` [L567-L569]
  - `start_full_auto_pipeline(self)` [L571-L720] — *Open a chooser for the processing stages to run, then run them in order.*
  - `_confirm_pipeline_rerun_if_needed(self, stages, parent)` [L722-L791] — *Look ahead at stages about to run in a pipeline. If any have already*
  - `_run_next_selected_processing(self)` [L793-L871]
  - `start_transcribe_and_diarize(self)` [L873-L892]
  - `_processing_choice(self, kind)` [L894-L933] — *Return: run, continue, start_over, or cancel based on current state.*
  - `_worker_command(self, args)` [L935-L954] — *Return (executable, args, env_overrides) for the local AI worker,*
  - `_resolve_worker_command(self, args)` [L956-L1003] — *Return (executable, args, env_overrides) for the local AI worker.*
  - `_apply_worker_env_overrides(self, process, env_overrides)` [L1006-L1042] — *Applies extra environment variables (e.g. GPU device selection, SSL certs,*
  - `_download_model_and_continue_transcription(self, model_name, label)` [L1044-L1077] — *Asynchronously download a missing model with responsive in-dialog progress and auto-resume.*
  - `_on_transcription_dl_progress(self, pct, msg)` [L1079-L1089]
  - `_on_transcription_dl_cancel(self)` [L1091-L1098]
  - `_on_transcription_dl_finished(self, err)` [L1100-L1133]
  - `_on_transcription_dl_thread_cleanup(self)` [L1135-L1147]

### `project_export.py` (447 lines)
*Radio & TV Story Segmenter — Unified Project & Media Export Facade.*
- **class `ProjectExportMixin(ExportDialogsMixin, ExportMediaClipperMixin, ExportDocumentsMixin, ExportStoryPipelineMixin, ProjectLifecycleMixin)`** (lines 88–447):
  *Unified application export mixin composed of focused export sub-mixins.*
  - `export_project_archive(self, destination_zip)` [L105-L179] — *Export current project state, transcripts, and media into a self-contained portable .zip archive.*
  - `ensure_project_for_processing_pipeline(self)` [L181-L204] — *Ensures a project file is established on disk before running multi-stage*
  - `find_adjacent_project(self, media_path)` [L206-L229] — *Looks for adjacent .rtvs or legacy .json project files referencing media_path.*
  - `resolve_project_media(self, project_file, audio_reference, audio_file_abs)` [L231-L289] — *Resolves portable or absolute project media reference with security extension validation.*
  - `closeEvent(self, event)` [L291-L447] — *MainWindow close event handling shutdown, worker cancellation, and QSettings sync.*

### `project_lifecycle.py` (956 lines)
*Radio & TV Story Segmenter — Project Lifecycle & Persistence Management.*
- **class `ProjectLifecycleMixin`** (lines 42–804):
  *Provides project lifecycle and persistence methods for MainWindow.*
  - `close_project(self, prompt)` [L45-L157]
  - `new_project(self)` [L159-L161]
  - `project_audio_reference(self)` [L163-L171]
  - `project_data(self)` [L173-L213]
  - `_write_project_file(self, file_path)` [L215-L275] — *Writes project state dictionary directly to disk.*
  - `prepare_export_directories(self, target_base_dir, default_name, prompt_user)` [L277-L338] — *Resolves project export subfolders (Transcripts, Media).*
  - `get_default_save_directory(self)` [L340-L353] — *Returns target base directory based on preferences and loaded media.*
  - `validate_project_data(self, data)` [L355-L413] — *Return a list of structural project-data problems before saving.*
  - `save_project_as(self)` [L415-L459]
  - `save_project(self, force)` [L461-L542]
  - `open_backup_restore_dialog(self)` [L544-L551] — *Opens the unified Backup & Restore Center dialog.*
  - `load_project_file(self, filename, prompt, preserve_media)` [L553-L641]
  - `load_project(self, filename)` [L643-L657]
  - `open_purge_project_data_dialog(self)` [L659-L671] — *Open the modal dialog allowing users to selectively wipe project data.*
  - `purge_project_data(self, purge_transcript, purge_translations, purge_speakers, purge_stories, purge_media)` [L673-L804] — *Selectively wipe project components while preserving user undo history.*
- **class `ProjectDataPurgeDialog(QDialog)`** (lines 807–955):
  *Modal dialog allowing users to selectively clear/purge project components.*
  - `__init__(self, parent, is_es)` [L810-L817]
  - `_init_ui(self)` [L819-L936]
  - `_set_all_checked(self, checked)` [L938-L940]
  - `_update_purge_button_state(self)` [L942-L946]
  - `get_purge_options(self)` [L948-L955]

### `project_serialization.py` (126 lines)
*Radio & TV Segmenter — Project file serialization and safe decompression.*
- **Functions**:
  - `sanitize_project_data_for_storage(data, parent_key)` [L21-L51] — *Recursively optimize project data before serialization:*
  - `serialize_rtvs_project(data)` [L54-L58] — *Serialize project dictionary into a transparently gzip-compressed payload.*
  - `_decompress_gzip_bounded(raw_bytes, max_bytes)` [L61-L79] — *Decompress a gzip payload in chunks, stopping with a clear error the*
  - `deserialize_rtvs_project(raw_bytes)` [L82-L98] — *Deserialize project payload, transparently handling both gzip-compressed (.rtvs)*
  - `read_rtvs_project_file(file_path)` [L101-L113] — *Transparently read an .rtvs or .json project file from disk (compressed or uncompressed).*
  - `write_rtvs_project_file(file_path, data)` [L116-L126] — *Safely and atomically write a gzip-compressed .rtvs project file.*

### `project_state_mixin.py` (328 lines)
*Radio & TV Story Segmenter — Project State, Undo/Redo & Processing Progress Mixin.*
- **class `ProjectStateMixin`** (lines 18–328):
  *Provides project state snapshotting, undo/redo state restoration, and progress tracking.*
  - `_format_elapsed_time(self, seconds)` [L21-L27]
  - `_format_time_remaining(self, seconds)` [L29-L39]
  - `_get_stage_estimated_duration(self, stage_key)` [L41-L52]
  - `calculate_processing_eta(self, percent)` [L54-L71]
  - `set_processing_stage(self, stage, detail)` [L73-L128]
  - `_on_progress_timer_tick(self)` [L130-L133]
  - `update_processing_progress(self, percent, message)` [L135-L209]
  - `update_processing_stage_summary(self)` [L211-L224]
  - `_clone_transcript_state(transcript)` [L227-L230]
  - `_capture_project_state(self)` [L232-L243] — *Capture all editable project data for the application undo stack.*
  - `get_project_state(self)` [L245-L247] — *Public alias for _capture_project_state for undo history capture.*
  - `_restore_project_state_for_undo(self, state)` [L249-L288] — *Restore a complete editable project state without creating another undo entry.*
  - `_commit_project_state_change(self, before_state, description)` [L290-L297] — *Push a complete project-state undo command after a mutation.*
  - `flush_pending_transcript_undo(self)` [L299-L307] — *Commit a pending grouped text edit before another project action or Ctrl+Z.*
  - `mark_project_dirty(self, reason)` [L309-L316] — *Mark the current project as needing a save and refresh the UI state.*
  - `update_window_title(self)` [L318-L328]

### `prs_shared.py` (1257 lines)
- **class `ProjectMetadataDict(dict)`** (lines 30–45):
  *Dictionary subclass supporting both dict key access and attribute access for project metadata.*
  - `__getattr__(self, name)` [L32-L36]
  - `__setattr__(self, name, value)` [L38-L39]
  - `__delattr__(self, name)` [L41-L45]
- **class `ResizableTextEdit(QWidget)`** (lines 272–419):
  *Multi-line text editor defaulted to ~2 lines of height with a drag handle for vertical expansion.*
  - `__init__(self, text, parent)` [L275-L314]
  - `_grip_press(self, event)` [L316-L324]
  - `_grip_move(self, event)` [L326-L344]
  - `_grip_release(self, event)` [L346-L348]
  - `sizeHint(self)` [L350-L351]
  - `minimumSizeHint(self)` [L353-L354]
  - `toPlainText(self)` [L356-L357]
  - `setPlainText(self, text)` [L359-L360]
  - `setText(self, text)` [L362-L363]
  - `text(self)` [L365-L366]
  - `clear(self)` [L368-L369]
  - `setPlaceholderText(self, text)` [L371-L372]
  - `placeholderText(self)` [L374-L375]
  - `setToolTip(self, tip)` [L377-L378]
  - `setAcceptRichText(self, accept)` [L380-L381]
  - `setTabChangesFocus(self, tab)` [L383-L384]
  - `setEnabled(self, enabled)` [L386-L389]
  - `setReadOnly(self, ro)` [L391-L392]
  - `isReadOnly(self)` [L394-L395]
  - `setFocus(self, *args, **kwargs)` [L397-L398]
  - `hasFocus(self)` [L400-L401]
  - `document(self)` [L403-L404]
  - `textCursor(self)` [L406-L407]
  - `setTextCursor(self, cursor)` [L409-L410]
  - `__getattr__(self, name)` [L412-L415]
  - `textChanged(self)` [L418-L419]
- **class `CollapsibleSection(QWidget)`** (lines 422–589):
  *A clean, collapsible and expandable section widget with a styled toggle button,*
  - `__init__(self, title, parent, is_expanded, subtitle)` [L429-L458]
  - `_update_ui(self)` [L460-L558]
  - `refresh_theme(self)` [L560-L562] — *Re-render header and container styling when application theme changes.*
  - `_on_btn_clicked(self)` [L564-L565]
  - `set_expanded(self, expanded)` [L567-L572]
  - `is_expanded(self)` [L574-L575]
  - `set_title(self, title)` [L577-L579]
  - `set_subtitle(self, subtitle)` [L581-L583]
  - `add_widget(self, widget)` [L585-L586]
  - `add_layout(self, layout)` [L588-L589]
- **class `ExportDialog(QDialog)`** (lines 699–788):
  - `__init__(self, parent, has_media, default_name)` [L700-L708]
  - `init_ui(self)` [L710-L776]
  - `get_settings(self)` [L778-L788]
- **class `Story`** (lines 950–1028):
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L951-L996]
  - `to_dict(self)` [L998-L1010]
  - `from_dict(cls, data)` [L1013-L1028]
- **class `ProjectStateCommand(QUndoCommand)`** (lines 1044–1068):
  *Undo/redo a complete editable project state.*
  - `__init__(self, main_window, before_state, after_state, description)` [L1051-L1059]
  - `undo(self)` [L1061-L1062]
  - `redo(self)` [L1064-L1068]
- **Functions**:
  - `_ensure_runtime_bin_on_path()` [L49-L68] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `platform_seq(key_str)` [L614-L623] — *Return a QKeySequence adapted for macOS vs Windows/Linux.*
  - `get_app_icon()` [L625-L671] — *Return the application QIcon loaded from bundled resources or fallback to empty.*
  - `get_license_file_path(filename)` [L673-L691] — *Return the path to a licensing or notice file, checking bundle and source paths.*
  - `create_fade_curve_pixmap(curve_type, width, height, is_selected, accent_color, bg_color)` [L832-L924] — *Render a high-DPI visual curve representation showing the volume attenuation shape.*
  - `create_fade_curve_icon(curve_type, width, height)` [L927-L942] — *Return a QIcon containing visual render of the specified audio fade curve.*
  - `read_document_text(path)` [L1107-L1173]

### `qt_compat.py` (173 lines)
*Radio & TV Segmenter — Headless Qt / PySide6 Compatibility Engine.*
- **Public Exports (`__all__`)**: MockModule, DummyQt, DummyQSettings, DummyQMessageBox, DummyQApplication, DummyQHeaderView, DummyQAbstractItemView, DummyQLineEdit, _ensure_pyside6_fallback
- **class `MockModule(ModuleType)`** (lines 15–44):
  *Dynamic mock module that automatically manufactures nested mock classes and attributes.*
  - `__init__(self, name)` [L18-L20]
  - `__getattr__(self, name)` [L22-L44]
- **class `DummyQt`** (lines 47–56):
  *Mock Qt namespace constants.*
- **class `DummyQSettings`** (lines 59–82):
  *In-memory dictionary-backed QSettings fallback.*
  - `__init__(self, *a, **k)` [L63-L64]
  - `value(self, k, d)` [L66-L67]
  - `setValue(self, k, v)` [L69-L70]
  - `remove(self, k)` [L72-L73]
  - `sync(self)` [L75-L76]
  - `beginGroup(self, *a)` [L78-L79]
  - `endGroup(self)` [L81-L82]
- **class `DummyQMessageBox`** (lines 85–103):
  *Non-blocking headless QMessageBox stub.*
  - `information(*args, **kwargs)` [L90-L91]
  - `warning(*args, **kwargs)` [L94-L95]
  - `critical(*args, **kwargs)` [L98-L99]
  - `question(*args, **kwargs)` [L102-L103]
- **class `DummyQApplication`** (lines 106–119):
  *Headless QApplication stub.*
  - `processEvents()` [L110-L111]
  - `instance()` [L114-L115]
  - `topLevelWidgets()` [L118-L119]
- **class `DummyQHeaderView`** (lines 122–123):
- **class `DummyQAbstractItemView`** (lines 126–128):
- **class `DummyQLineEdit`** (lines 131–132):
- **Functions**:
  - `_ensure_pyside6_fallback()` [L135-L160] — *Ensures PySide6 modules are importable, installing the zero-dependency mock shim if unavailable.*

### `radio_tv_story_segmenter_worker.py` (2264 lines)
- **Functions**:
  - `_patch_av_open()` [L64-L80] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `_clamp_diarization_thread_env()` [L86-L115] — *Cap OMP/ONNX Runtime/BLAS thread pools before onnxruntime, torch, or the*
  - `_setup_windows_dll_directories()` [L122-L232] — *Register native DLL directories (PyTorch, CTranslate2, ONNX Runtime, etc.)*
  - `_safe_tensor_from_numpy(arr)` [L239-L257] — *Safely convert a numpy float32 array into a PyTorch tensor.*
  - `emit(message_type, **payload)` [L264-L267]
  - `emit_hello()` [L270-L271]
  - `get_optimal_transcription_threads()` [L274-L293] — *Calculate optimal CPU threads for faster-whisper / CTranslate2 / ONNX.*
  - `get_app_data_dir_pure()` [L296-L314] — *Return platform-specific app data directory in pure Python without PySide6.*
  - `get_models_storage_dir_pure()` [L317-L327] — *Return models storage directory in pure Python without PySide6.*
  - `is_onnx_model_available(model_name)` [L330-L388]
  - `transcribe_parakeet_onnx(audio_file, model_name, detected_lang, detected_confidence, initial_prompt, beam_size)` [L391-L728] — *Run installed ONNX models (Parakeet TDT, Spanish FastConformer, Multilingual FastConformer) through sherpa-onnx.*
  - `probe_audio_language(audio_file, sample_duration, preferred_model)` [L731-L814] — *Run a fast language detection probe using faster-whisper's mel feature extractor.*
  - `transcribe(audio_file, model_name, initial_prompt, beam_size)` [L817-L1042]
  - `normalize_audio_for_diarization(source_path)` [L1045-L1105] — *Extract a normalized 16 kHz mono WAV using the local FFmpeg binary.*
  - `configure_optimal_pytorch_threads()` [L1108-L1123] — *Clamp torch's intra-op/inter-op thread pools to match the*
  - `_normalize_expected_speakers(value)` [L1126-L1135] — *Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'.*
  - `_normalize_speaker_labels(segments)` [L1138-L1151] — *Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',*
  - `_diarize_solo_fast_path(audio_file, transcript_file)` [L1154-L1228] — *Solo fast-path: a single expected speaker means there is nothing to*
  - `_sensitivity_distance_threshold()` [L1234-L1242] — *Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.*
  - `fast_cluster_ahc(embeddings, k, distance_threshold)` [L1245-L1302] — *Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).*
  - `apply_clustering_patches()` [L1308-L1341] — *Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC.*
  - `_get_wespeaker_model()` [L1347-L1355] — *Retrieve or initialize the cached WeSpeaker ONNX model instance.*
  - `extract_embeddings_batched(audio_path, speech_segments, batch_size, min_segment_duration, embedding_window, embedding_step, progress_callback)` [L1358-L1481] — *Extract 256-dim speaker embeddings using WeSpeaker ResNet34-LM (ONNX)*
  - `run_vad_two_pass(audio_path, threshold, min_speech_duration_ms, min_silence_duration_ms, speech_pad_ms, bridge_pause_threshold_sec)` [L1484-L1557] — *Silero VAD with Pass 1 Pause Bridging (< 100ms).*
  - `assign_short_segments_to_centroids(short_segments, audio_path, centroids, label_values, raw_segments, min_confidence)` [L1560-L1663] — *Extract acoustic embeddings for short segments (< 0.8s, e.g. quick interjections*
  - `_calculate_embedding_for_interval(start, end, subsegments, embeddings)` [L1666-L1691] — *Compute unit-normalized 256-dimensional embedding vector for an interval [start, end].*
  - `run_transcript_guided_diarization(normalized_wav, transcript_file, expected_speakers, sensitivity, progress_callback)` [L1694-L1836] — *Execute transcript-guided speaker diarization:*
  - `diarize(audio_file, expected_speakers, transcript_file, sensitivity)` [L1839-L2152]
  - `main(argv)` [L2155-L2260]

### `roadmap_manager.py` (262 lines)
*roadmap_manager.py — Automated Roadmap & N-1 Sliding-Window Management Engine*
- **class `RoadmapManager`** (lines 45–208):
  - `__init__(self, roadmap_path)` [L46-L49]
  - `load(self)` [L51-L54]
  - `save(self)` [L56-L57]
  - `get_sections_info(self)` [L59-L102] — *Parse TOC and identify release sections.*
  - `audit(self)` [L104-L151] — *Audit roadmap.txt against N-1 sliding window and status tracking invariants.*
  - `set_item_status(self, item_num, status)` [L153-L176] — *Synchronously update the status checkbox for an item (e.g. '2.1', '3.2') to [x], [-], or [ ].*
  - `sync_current_version(self, target_version)` [L178-L200] — *Synchronize the current release version in roadmap.txt to target_version or prs_shared.py.*
  - `count_item_statuses(self)` [L202-L208] — *Count completed, in-progress, and planned items in the roadmap.*
- **Functions**:
  - `get_current_app_version()` [L23-L43] — *Extract PROJECT_VERSION from core_utils.py or prs_shared.py.*
  - `main()` [L210-L259]

### `runtime_manager.py` (1035 lines)
- **class `RuntimeManager`** (lines 361–1035):
  *Manages isolated Python virtual environments for ML features with auto-upgrade support.*
  - `__init__(self, base_dir)` [L364-L375]
  - `get_last_error(self)` [L377-L379] — *Returns the most recent detailed error message from environment setup or execution.*
  - `get_env_dir(self, feature_name)` [L381-L382]
  - `get_manifest_path(self, feature_name)` [L384-L385]
  - `_get_raw_executable(self, feature_name)` [L387-L391]
  - `get_executable(self, feature_name)` [L393-L399] — *Returns the path to the python executable inside the target feature environment if valid.*
  - `resolve_target_python(self, target_version)` [L401-L433] — *Finds a matching Python binary on the host system for building the environment.*
  - `bundled_uv_path(self)` [L436-L464] — *Return the uv binary shipped with the application across Windows, macOS, and Linux, or None if unavailable.*
  - `ensure_uv(self, progress_cb)` [L466-L536] — *Locates bundled or system uv, or automatically downloads standalone uv for the active OS/arch.*
  - `_get_uv_env(self)` [L538-L552] — *Constructs environment dictionary with managed Python directory for uv.*
  - `_find_extracted_python(self, target_version)` [L554-L583] — *Scan managed python directory for a working extracted python binary.*
  - `_download_standalone_python(self, target_version, progress_cb)` [L585-L622] — *Directly download and extract standalone CPython distribution without symlinks.*
  - `ensure_managed_python(self, target_version, progress_cb)` [L624-L680] — *Provision a private Python runtime with uv when the host has no matching Python.*
  - `kill_all_subprocesses(self)` [L682-L684] — *Force terminate any lingering isolated worker subprocesses.*
  - `remove_environment(self, feature_name)` [L686-L726] — *Remove an isolated feature environment without touching its models.*
  - `prune_cuda_artifacts(env_dir)` [L729-L785] — *Strip unused CUDA/cuDNN packages, heavy C++ dev headers, test suites,*
  - `get_runtime_executable(self, feature_name, progress_cb)` [L787-L791] — *Ensure and return the executable for an isolated feature runtime.*
  - `get_plugin_requirements(self, feature_name, plugin_dir)` [L793-L822] — *Read requirements-runtime.txt from plugin directory if available, fallback to ENV_CONFIGS.*
  - `is_env_up_to_date(self, feature_name)` [L824-L847] — *Verifies if environment exists and matches current config version and specs.*
  - `write_manifest(self, feature_name, python_used, packages)` [L849-L860] — *Writes configuration metadata upon successful environment creation.*
  - `ensure_environment(self, feature_name, force_rebuild, progress_cb, plugin_dir, cancel_event)` [L862-L1035] — *Creates or upgrades an isolated feature environment.*
- **Functions**:
  - `register_process(proc)` [L41-L49] — *Register an active Popen process for teardown monitoring.*
  - `unregister_process(proc)` [L52-L60] — *Remove completed process from tracking.*
  - `kill_all_subprocesses()` [L63-L78] — *Force terminate any lingering isolated worker subprocesses.*
  - `_robust_urlretrieve(url, destination, timeout)` [L81-L123] — *Download url to destination with explicit timeout, SSL certificate verification, and atomic write.*
  - `_emit_progress(progress_cb, percent, message)` [L126-L139] — *Safely emit progress supporting both 1-argument (message) and 2-argument (percent, message) callbacks.*
  - `_run_pip_with_progress(cmd, feature_name, packages, progress_cb, env, creationflags, start_pct, end_pct, cancel_event)` [L142-L257] — *Execute pip or uv pip with real-time output monitoring and progress reporting.*
  - `detect_nvidia_gpu()` [L327-L341] — *Best-effort check for a usable NVIDIA GPU on this machine, so the*
  - `_remove_macos_quarantine(target_path)` [L344-L358] — *Strip Gatekeeper com.apple.quarantine attribute on macOS for standalone executables.*

### `scripts/generate_symbol_index.py` (380 lines)
*generate_symbol_index.py — Fast AST Symbol Indexer & Repository Map Engine.*
- **Functions**:
  - `parse_function_signature(node)` [L48-L77] — *Format function name and parameter names into a compact signature string.*
  - `analyze_file(filepath)` [L80-L157] — *Parse a single Python file with AST and extract structural outline and symbols.*
  - `scan_repository()` [L160-L184] — *Scan all Python modules across the repository and build index data.*
  - `generate_index_markdown(index_data)` [L187-L258] — *Generate a clean, token-dense markdown catalog of all files and their symbols.*
  - `print_file_outline(filepath, index_data)` [L261-L293] — *Print a compact, high-density outline of a single file with line numbers.*
  - `search_symbols(query, index_data)` [L296-L319] — *Search for symbols across all indexed files.*
  - `build_and_save_index()` [L322-L342] — *Build the symbol index and save both JSON and Markdown into .codemaps/.*
  - `main()` [L345-L376]

### `scripts/log_summary.py` (150 lines)
*log_summary.py — Compact Error & Exception Extraction Engine*
- **Functions**:
  - `is_project_frame(filepath)` [L35-L40] — *Determine if a file path belongs to the application rather than external/standard libraries.*
  - `extract_log_summary(raw_log)` [L42-L128] — *Extract a high-density summary from a raw log or traceback string.*
  - `main()` [L130-L147]

### `shortcuts/__init__.py` (26 lines)
*shortcuts package — Modular Keyboard Shortcuts Management Subsystem.*
- **Public Exports (`__all__`)**: ShortcutDef, SHORTCUT_DEFINITIONS, get_platform_default, format_sequence_display, normalize_sequence_string, _get_shortcuts_theme_mode, ShortcutsManager, KeySequenceRecorderEdit, KeyboardShortcutsPage

### `shortcuts/definitions.py` (22 lines)
*shortcuts/definitions.py — Shortcut definitions and schema re-exports for keyboard shortcut management.*
- **Public Exports (`__all__`)**: ShortcutDef, SHORTCUT_DEFINITIONS, ACTION_ALIASES, get_platform_default, format_sequence_display, normalize_sequence_string, _get_shortcuts_theme_mode

### `shortcuts/dialogs.py` (623 lines)
*shortcuts/dialogs.py — Preferences page for keyboard shortcuts configuration.*
- **class `KeyboardShortcutsPage(QWidget)`** (lines 34–623):
  *Preferences page that provides a searchable table of all customizable shortcuts,*
  - `__init__(self, shortcuts_manager, parent_window, parent)` [L38-L53]
  - `_init_ui(self)` [L55-L281]
  - `_sort_by_action_name(self)` [L283-L289] — *Arrange table alphabetically by Action Name (Column 0).*
  - `_sort_by_category(self)` [L291-L297] — *Arrange table grouped by Category (Column 1).*
  - `_on_header_section_clicked(self, logical_index)` [L299-L316] — *Handle header column click to sort and update arrange toggle buttons.*
  - `_sort_table(self)` [L318-L321] — *Sort table rows by active sort column and order.*
  - `_on_lookup_sequence_changed(self, candidate_seq)` [L323-L378] — *Lookup action bound to candidate key sequence and update UI card.*
  - `_clear_lookup(self)` [L380-L385] — *Reset lookup tool state.*
  - `_on_lookup_jump_clicked(self)` [L387-L402] — *Scroll to and select the matched action in the table.*
  - `_populate_table(self)` [L404-L442]
  - `_update_status_item(self, item, action_id)` [L444-L472]
  - `_filter_table(self)` [L474-L493]
  - `_on_row_selected(self)` [L495-L528]
  - `_on_new_sequence_recorded(self, new_seq)` [L530-L533]
  - `_reset_selected_to_default(self)` [L535-L539]
  - `_apply_pending_change(self, action_id, new_seq)` [L541-L556]
  - `_check_conflict(self, candidate_seq, excluding_action_id)` [L558-L584]
  - `_reassign_conflict(self)` [L586-L591] — *Remove shortcut from conflicting action and assign to current selected action.*
  - `_confirm_reset_all(self)` [L593-L606]
  - `_on_save_clicked(self)` [L608-L615]
  - `save_shortcuts(self)` [L617-L623] — *Commit all pending shortcut changes to QSettings and apply to the MainWindow.*

### `shortcuts/manager.py` (198 lines)
*shortcuts/manager.py — Core ShortcutsManager coordinator and QSettings integration.*
- **class `ShortcutsManager(QObject)`** (lines 19–198):
  *Central repository and coordinator for all configurable application shortcuts.*
  - `__init__(self, settings_store)` [L24-L30]
  - `load(self)` [L32-L43] — *Read customized shortcut overrides from QSettings.*
  - `get_definitions(self)` [L45-L46]
  - `get_definition(self, action_id)` [L48-L53]
  - `get_default_shortcut(self, action_id)` [L55-L60]
  - `get_current_shortcut(self, action_id)` [L62-L68]
  - `is_customized(self, action_id)` [L70-L76]
  - `set_shortcut(self, action_id, new_seq)` [L78-L93] — *Set a shortcut override for action_id. Passing empty string or None sets to None.*
  - `reset_shortcut(self, action_id)` [L95-L101] — *Reset a single shortcut back to its platform default.*
  - `reset_all(self)` [L103-L105] — *Reset all shortcuts back to application defaults.*
  - `save(self)` [L107-L118] — *Persist all overrides to QSettings and emit notification signal.*
  - `find_conflict(self, candidate_seq, excluding_action_id)` [L120-L136] — *Check if candidate_seq is already bound to another action.*
  - `apply_to_window(self, window)` [L138-L198] — *Update shortcuts on all QAction and QShortcut objects on MainWindow,*

### `shortcuts/schema.py` (558 lines)
*shortcuts/schema.py — Shortcut definitions, dataclass models, and string helpers.*
- **class `ShortcutDef`** (lines 13–22):
- **Functions**:
  - `_get_shortcuts_theme_mode()` [L25-L27] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast').*
  - `get_platform_default(defn)` [L30-L37] — *Return the platform-adapted default shortcut string for a definition.*
  - `format_sequence_display(seq_str)` [L40-L49] — *Format key sequence into clean user-readable text for current OS.*
  - `normalize_sequence_string(seq_str)` [L52-L59] — *Return portable normalized representation of a shortcut string.*

### `shortcuts/widgets.py` (151 lines)
*shortcuts/widgets.py — Interactive Key Sequence Recorder and Input widgets.*
- **class `KeySequenceRecorderEdit(QLineEdit)`** (lines 11–151):
  *Interactive input widget that captures key presses and formats them into a shortcut sequence.*
  - `__init__(self, parent)` [L16-L24]
  - `set_sequence(self, seq_str)` [L26-L28]
  - `get_sequence(self)` [L30-L31]
  - `start_recording(self)` [L33-L52]
  - `stop_recording(self)` [L54-L69]
  - `mousePressEvent(self, event)` [L71-L74]
  - `focusInEvent(self, event)` [L76-L79]
  - `focusOutEvent(self, event)` [L81-L84]
  - `keyPressEvent(self, event)` [L86-L151]

### `shortcuts_manager.py` (30 lines)
*Shortcuts Manager for Radio & TV Story Segmenter (Compatibility Façade).*
- **Public Exports (`__all__`)**: ShortcutDef, SHORTCUT_DEFINITIONS, get_platform_default, format_sequence_display, normalize_sequence_string, _get_shortcuts_theme_mode, ShortcutsManager, KeySequenceRecorderEdit, KeyboardShortcutsPage

### `snapshot_manager.py` (276 lines)
*Snapshot Manager for Radio & TV Story Segmenter*
- **Functions**:
  - `load_manifest()` [L50-L57]
  - `save_manifest(data)` [L60-L63]
  - `get_current_project_version()` [L66-L85]
  - `ensure_git_repo()` [L88-L94] — *Ensure git repo is initialized with standard identity.*
  - `create_snapshot(name, is_stable, is_verified_stable)` [L97-L165]
  - `list_snapshots()` [L168-L190]
  - `restore_snapshot(name)` [L193-L247]
  - `main()` [L250-L272]

### `speaker_dialog_refinement_mixin.py` (508 lines)
*Radio & TV Story Segmenter — Speaker Dialog Refinement & Turn Merging Mixin.*
- **class `SpeakerDialogRefinementMixin`** (lines 45–508):
  *Mixin for competitive speaker run refinement, word synchronization, and turn merging.*
  - `refine_speaker_run_between_confirmed_anchors(self, start_idx, end_idx, spk_a, spk_b)` [L48-L128]
  - `prompt_refine_speaker_run(self, start_idx, end_idx)` [L130-L302]
  - `sync_segment_words(self, segment, new_text, word_formats)` [L304-L396]
  - `merge_speakers(self, source_speaker, target_speaker)` [L398-L451]
  - `open_speaker_manager_dialog(self)` [L453-L455]
  - `merge_contiguous_speaker_segments(self)` [L457-L508]

### `speaker_dialogs.py` (302 lines)
*speaker_dialogs.py — Dialogs for speaker renaming, turn assignment, and cluster management.*
- **Public Exports (`__all__`)**: ChangeSpeakerDialog, SpeakerManagerDialog
- **class `ChangeSpeakerDialog(QDialog)`** (lines 21–80):
  *Dialog prompting whether to apply a speaker name change to all instances or a single turn.*
  - `__init__(self, current_name, target_name, seg_idx, parent)` [L24-L68]
  - `_on_all(self)` [L70-L72]
  - `_on_subsequent(self)` [L74-L76]
  - `_on_single(self)` [L78-L80]
- **class `SpeakerManagerDialog(QDialog)`** (lines 85–302):
  *Manager dialog for inspecting, aliasing, and merging detected speaker clusters.*
  - `__init__(self, parent)` [L88-L96]
  - `_init_ui(self)` [L98-L139]
  - `_populate(self)` [L141-L218]
  - `_rename_speaker(self, current_name, raw_id)` [L220-L252]
  - `_merge_speaker_into(self, source_name)` [L254-L275]
  - `_on_quick_merge(self)` [L277-L297]
  - `_on_open_voice_profiles(self)` [L299-L302]

### `speaker_editing_mixin.py` (580 lines)
*Radio & TV Story Segmenter — Speaker Label, Renaming & Segment Editing Mixin.*
- **class `SpeakerEditingMixin(SpeakerDialogRefinementMixin)`** (lines 53–580):
  *Mixin for speaker labeling, splitting, renaming, and dialog turn refinement.*
  - `handle_insert_speaker_request(self, seg_idx, split_time, speaker_name)` [L56-L60]
  - `add_speaker_label_at(self, seg_idx, split_time, name)` [L62-L170]
  - `split_segment_at_time(self, seg_idx, split_time, new_speaker_name)` [L172-L274]
  - `prompt_rename_custom_speaker(self, old_name)` [L276-L294]
  - `display_speaker(self, speaker)` [L296-L310]
  - `get_all_known_speakers(self)` [L312-L342]
  - `execute_speaker_rename(self, seg_idx, raw_speaker, target_name)` [L344-L462]
  - `prompt_rename_speaker(self, seg_idx, speaker)` [L464-L465]
  - `remove_speaker_label_at_segment(self, seg_idx)` [L467-L547]
  - `register_confirmed_speaker_turn(self, seg_idx, speaker_name)` [L549-L577]
  - `register_confirmed_speaker_sample(self, seg_idx, speaker_name)` [L579-L580]

### `speaker_identity.py` (260 lines)
*Radio & TV Segmenter*
- **class `VoiceMatch`** (lines 44–48):
- **Functions**:
  - `_as_vector(value)` [L51-L67]
  - `cosine_similarity(a, b)` [L70-L88] — *Cosine similarity for already-normalized or arbitrary vectors.*
  - `normalize_vector(vector)` [L91-L92]
  - `centroid(vectors)` [L95-L117] — *Calculate a normalized centroid from valid embeddings.*
  - `robust_reference_profile(seed_vectors, candidate_vectors, *, max_samples, min_samples, seed_similarity)` [L120-L210] — *Build a speaker profile without blindly averaging an existing cluster.*
  - `compare_against_profiles(vector, target_profile, competitor_profiles)` [L213-L239] — *Compare a candidate against the target speaker and all competing profiles.*
  - `is_confident_match(result, *, threshold, margin, has_competitors)` [L242-L260] — *Require both:*

### `speaker_profiles.py` (630 lines)
*speaker_profiles.py — Persistent Station Voice Profile Manager & Storage Engine.*
- **class `StationVoiceProfile`** (lines 67–96):
  - `to_dict(self)` [L77-L78]
  - `from_dict(cls, data)` [L81-L96]
- **class `StationVoiceProfileStore`** (lines 99–274):
  *Persistent storage manager for recurring station voice acoustic profiles.*
  - `__init__(self, storage_dir)` [L102-L109]
  - `get_profiles_file_path(self)` [L111-L112]
  - `load(self)` [L114-L132]
  - `save(self)` [L134-L150]
  - `list_profiles(self)` [L152-L153]
  - `get_profile(self, profile_id)` [L155-L156]
  - `find_profile_by_name(self, name)` [L158-L163]
  - `add_or_update_profile(self, name, vector, sample_count, notes, source_media, profile_id)` [L165-L224]
  - `remove_profile(self, profile_id)` [L226-L231]
  - `clear(self)` [L233-L235]
  - `match_vector(self, vector, threshold, min_margin)` [L237-L274] — *Compare an unknown candidate vector against all saved voice profiles.*
- **class `ManageVoiceProfilesDialog(QDialog)`** (lines 277–630):
  *Management dialog for inspecting, auditing, adding, or deleting persistent station voice profiles.*
  - `__init__(self, parent, store, main_win)` [L280-L291]
  - `_init_ui(self)` [L293-L350]
  - `_populate_table(self)` [L352-L417]
  - `_on_rename(self, profile_id, old_name)` [L419-L432]
  - `_on_delete(self, profile_id, name)` [L434-L444]
  - `_on_match_project(self, prof)` [L446-L503]
  - `_on_add_from_active_turn(self)` [L505-L570]
  - `_on_export(self)` [L572-L600]
  - `_on_import(self)` [L602-L630]

### `story_crud_mixin.py` (735 lines)
*Radio & TV Story Segmenter — Story CRUD & Timeline Selection Mixin.*
- **class `StoryCrudMixin`** (lines 34–735):
  *Mixin providing story list UI management, CRUD operations, and fade handling.*
  - `refresh_story_list(self)` [L37-L80]
  - `handle_new_story_started(self, start_time, end_time)` [L82-L92]
  - `handle_new_story_updated(self, start_time, end_time)` [L94-L106]
  - `handle_drag_story_region(self, index, start_time, end_time)` [L108-L120]
  - `audition_story(self, index)` [L122-L145]
  - `handle_drag_finished(self)` [L147-L176]
  - `update_selected_story(self)` [L178-L236]
  - `delete_selected_story(self)` [L238-L263]
  - `get_current_interaction_time(self, for_boundary)` [L265-L283]
  - `set_selected_story_start(self)` [L285-L330]
  - `set_selected_story_end(self)` [L332-L377]
  - `add_selection_to_story(self)` [L379-L490]
  - `play_transcript_selection(self)` [L492-L511]
  - `select_all_stories(self)` [L513-L520]
  - `handle_timeline_selection_range_changed(self, start_time, end_time)` [L522-L565]
  - `add_story_from_range(self, start_time, end_time)` [L567-L601]
  - `add_story_from_active_selection(self)` [L603-L620]
  - `open_story_fades_dialog(self, story_index)` [L622-L664]
  - `apply_fades_to_selected_stories(self, fade_in, fade_out, fade_curve)` [L666-L699]
  - `remove_fades_from_selected_stories(self)` [L701-L702]
  - `set_fade_curve_for_selected_stories(self, curve_type)` [L704-L727]
  - `open_story_metadata_dialog(self, target_story_index)` [L729-L735]

### `story_detection_processing.py` (141 lines)
*Story boundary detection processing mixin for Radio & TV Story Segmenter.*
- **class `StoryDetectionProcessingMixin`** (lines 18–140):
  - `start_auto_detect_stories(self)` [L19-L82]
  - `auto_detect_progress(self, message, percent)` [L84-L85]
  - `auto_detect_finished(self, new_stories)` [L87-L119]
  - `auto_detect_error(self, message)` [L121-L140]

### `story_fades_dialog.py` (213 lines)
*story_fades_dialog.py — Dialog for fine-grained audio fade-in, fade-out, and curve adjustment.*
- **Public Exports (`__all__`)**: StoryFadesDialog
- **class `StoryFadesDialog(QDialog)`** (lines 18–211):
  *Dialog for fine-grained numerical adjustment of audio fade-in and fade-out durations.*
  - `__init__(self, parent, story, story_index)` [L21-L38]
  - `_init_ui(self)` [L40-L127]
  - `_on_enable_fades_toggled(self, checked)` [L129-L138]
  - `_sync_fades_preference(self)` [L140-L150]
  - `apply_current(self)` [L152-L175]
  - `accept(self)` [L177-L179]
  - `reject(self)` [L181-L203]
  - `_restore_defaults(self)` [L205-L208]
  - `get_fades(self)` [L210-L211]

### `story_metadata_dialog.py` (1291 lines)
*Radio & TV Story Segmenter — Universal Story & Post Metadata Architecture.*
- **class `StoryMetadataDialog(QDialog)`** (lines 85–1291):
  *Universal modal dialog for inspecting and editing post and story metadata across the project.*
  - `__init__(self, parent, main_window, target_story_index)` [L88-L131]
  - `_init_ui(self)` [L133-L607]
  - `_load_taxonomies(self, force_remote)` [L609-L645] — *Load cached WordPress taxonomies or attempt remote fetch if active.*
  - `_populate_authors_list(self)` [L647-L670]
  - `_populate_categories_list(self)` [L672-L689]
  - `_filter_authors(self, _)` [L691-L694]
  - `_filter_categories(self, _)` [L696-L699]
  - `_on_refresh_taxonomy_clicked(self)` [L701-L709]
  - `rebuild_target_items(self)` [L711-L797] — *Construct the list of editable targets: Full Episode (0) followed by each Story.*
  - `_update_target_list_item_display(self, idx)` [L799-L814]
  - `_on_target_selection_changed(self, row)` [L816-L819]
  - `_load_target_into_ui(self, index)` [L821-L905]
  - `_get_target_bounds(self, target_index)` [L907-L916]
  - `_sync_slider_to_pos(self, pos)` [L918-L928]
  - `_on_slider_value_changed(self, val)` [L930-L937]
  - `_on_scrub_timer_timeout(self)` [L939-L942]
  - `_on_step_frame(self, delta_secs)` [L944-L951]
  - `_on_sync_playhead_clicked(self)` [L953-L960]
  - `_capture_frame(self, pos)` [L962-L1002]
  - `_on_thumb_mode_changed(self)` [L1004-L1035]
  - `_on_browse_image(self)` [L1037-L1053]
  - `_on_title_text_changed(self, text)` [L1055-L1059]
  - `_on_excerpt_text_changed(self)` [L1061-L1064]
  - `_on_auto_generate_excerpt(self)` [L1066-L1075]
  - `_on_manual_author_changed(self, text)` [L1077-L1081]
  - `_on_tags_changed(self, text)` [L1083-L1087]
  - `_on_status_changed(self, _)` [L1089-L1092]
  - `_on_slug_changed(self, text)` [L1094-L1097]
  - `_on_notes_changed(self, text)` [L1099-L1102]
  - `_on_author_item_changed(self, _)` [L1104-L1125]
  - `_on_category_item_changed(self, _)` [L1127-L1132]
  - `_get_checked_authors_from_ui(self)` [L1134-L1150]
  - `_set_checked_authors_in_ui(self, author_ids, author_term_ids)` [L1152-L1170]
  - `_get_checked_categories_from_ui(self)` [L1172-L1180]
  - `_set_checked_categories_in_ui(self, cat_ids)` [L1182-L1190]
  - `save_all_to_project(self)` [L1192-L1287] — *Commit all configured metadata into Project/Story data structures and sync UI.*
  - `_on_save_and_close(self)` [L1289-L1291]
- **Functions**:
  - `_get_metadata_theme_mode()` [L66-L68] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast').*
  - `generate_story_excerpt(text, max_words)` [L71-L82] — *Generate a clean, readable excerpt of up to max_words from transcript text.*

### `story_model.py` (254 lines)
*Radio & TV Story Segmenter — Story Model, Boundaries & Undo Commands.*
- **class `Story`** (lines 59–143):
  *Represents a segmented radio or TV news/broadcast story with boundaries and fade metadata.*
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L62-L104]
  - `duration(self)` [L107-L108]
  - `to_dict(self)` [L110-L122]
  - `from_dict(cls, data)` [L125-L140]
  - `__repr__(self)` [L142-L143]
- **class `SetStoriesCommand(QUndoCommand)`** (lines 171–196):
  *Undo/redo command for wholesale updates to the project's story list.*
  - `__init__(self, main_window, old_stories, new_stories, description)` [L174-L178]
  - `undo(self)` [L180-L187]
  - `redo(self)` [L189-L196]
- **class `StoryBoundaryChangeCommand(QUndoCommand)`** (lines 199–236):
  *Discrete undo/redo command for story boundary adjustments (start/end times).*
  - `__init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description)` [L202-L209]
  - `undo(self)` [L211-L215]
  - `redo(self)` [L217-L221]
  - `_sync_ui(self, start, end)` [L223-L236]
- **class `SelectStoriesCommand(QUndoCommand)`** (lines 239–254):
  *Undo/redo command for active story selection index changes.*
  - `__init__(self, main_window, old_selection, new_selection, description)` [L242-L246]
  - `undo(self)` [L248-L250]
  - `redo(self)` [L252-L254]
- **Functions**:
  - `get_fade_curve_factors(progress, curve)` [L46-L56] — *Calculate gain factor (0.0 to 1.0) given normalized fade progress (0.0 to 1.0).*
  - `validate_story_boundaries(start, end, media_duration)` [L146-L155] — *Clamp and ensure start < end within [0.0, media_duration].*
  - `check_story_overlap(stories)` [L158-L168] — *Return pairs of story indices that temporally overlap.*

### `story_widgets.py` (531 lines)
*Radio & TV Story Segmenter — Story Sidebar Widgets, Item Delegates, and Undo Commands.*
- **class `FadeCurveVisualSelector(QWidget)`** (lines 59–161):
  *Visual selector widget providing interactive card buttons for audio fade curves.*
  - `__init__(self, parent, button_width, button_height)` [L64-L117]
  - `_on_button_toggled(self, checked)` [L119-L128]
  - `currentData(self)` [L130-L131]
  - `setCurrentData(self, curve_type)` [L133-L144]
  - `findData(self, curve_type)` [L146-L151]
  - `currentIndex(self)` [L153-L157]
  - `setCurrentIndex(self, idx)` [L159-L161]
- **class `StoryFadesChangeCommand(QUndoCommand)`** (lines 168–203):
  *Discrete undo/redo command for story audio fade-in, fade-out, and curve adjustments.*
  - `__init__(self, main_window, story_index, old_in, old_out, new_in, new_out, old_curve, new_curve, description)` [L171-L180]
  - `undo(self)` [L182-L187]
  - `redo(self)` [L189-L194]
  - `_sync_ui(self)` [L196-L203]
- **class `SetStoriesCommand(QUndoCommand)`** (lines 206–230):
  - `__init__(self, main_window, old_stories, new_stories, description)` [L207-L212]
  - `undo(self)` [L214-L221]
  - `redo(self)` [L223-L230]
- **class `StoryBoundaryChangeCommand(QUndoCommand)`** (lines 233–268):
  *Discrete undo/redo command for story boundary adjustments (start/end times).*
  - `__init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description)` [L236-L243]
  - `undo(self)` [L245-L249]
  - `redo(self)` [L251-L255]
  - `_sync_ui(self, start, end)` [L257-L268]
- **class `SelectStoriesCommand(QUndoCommand)`** (lines 271–282):
  - `__init__(self, main_window, old_selection, new_selection, description)` [L272-L276]
  - `undo(self)` [L278-L279]
  - `redo(self)` [L281-L282]
- **class `StoryCardDelegate(QStyledItemDelegate)`** (lines 289–417):
  *Renders story items as clean cards with color-coded accent bars, pill badges, and time metadata.*
  - `__init__(self, parent)` [L291-L292]
  - `sizeHint(self, option, index)` [L294-L296]
  - `paint(self, painter, option, index)` [L298-L417]
- **class `StoryListWidget(QListWidget)`** (lines 424–531):
  *QListWidget subclass for story segmentation list with right-click context menu and drag-drop support.*
  - `__init__(self, parent)` [L431-L435]
  - `dragEnterEvent(self, event)` [L437-L441]
  - `dragMoveEvent(self, event)` [L443-L447]
  - `dropEvent(self, event)` [L449-L456]
  - `keyPressEvent(self, event)` [L458-L463]
  - `_show_context_menu(self, pos)` [L465-L520]
  - `adjust_height_to_contents(self, min_h, max_h)` [L522-L531] — *Dynamically size the list widget to only fit the number of stories.*
- **Functions**:
  - `_get_fade_curve_profiles()` [L45-L47]
  - `_get_fade_curve_icon(cid, width, height)` [L50-L52]

### `terminology.py` (275 lines)
*Model-independent terminology and glossary support.*
- **Functions**:
  - `parse_glossary(raw)` [L19-L67] — *Return normalized glossary entries while accepting legacy list strings.*
  - `load_glossary(settings_store)` [L70-L78] — *Load the shared glossary from the application's QSettings object.*
  - `_replace_term(text, source, preferred)` [L81-L89]
  - `normalize_text(text, glossary)` [L92-L99] — *Canonicalize glossary terms without changing surrounding punctuation.*
  - `normalize_transcript(transcript, glossary)` [L102-L144] — *Normalize transcript text and word labels for every ASR backend.*
  - `translation_rules(glossary)` [L147-L150] — *Return only entries explicitly marked as protected for translation.*
  - `replace_term(text, source, preferred)` [L153-L155] — *Public replacement helper for translation workers.*
  - `split_protected_text(text, glossary)` [L158-L192] — *Split text into translatable and protected pieces.*
  - `export_glossary_to_json(glossary)` [L195-L198] — *Serialize glossary entries to formatted JSON string.*
  - `export_glossary_to_csv(glossary)` [L201-L216] — *Serialize glossary entries to standard CSV string.*
  - `import_glossary_from_text(raw_text)` [L219-L274] — *Parse glossary entries from JSON, CSV, TSV, or plain text lines.*

### `theme_preferences.py` (596 lines)
*Radio & TV Story Segmenter — Theme Preferences & Styling Engine.*
- **class `ThemePreferencesMixin`** (lines 19–596):
  *Provides application theme switching and styling methods.*
  - `set_theme(self, mode)` [L22-L596]

### `theme_qss.py` (325 lines)
*Targeted QSS for the Radio & TV Segmenter visual design system.*

### `theme_tokens.py` (307 lines)
*Theme Tokens for Radio & TV Story Segmenter.*
- **class `ThemeTokens`** (lines 27–195):
  *Centralized color and style tokens for custom QPainter drawing & QSS.*
  - `card_bg(self)` [L91-L93] — *Alias for bg_card for backwards compatibility.*
  - `btn_hover_bg(self)` [L96-L98] — *Alias for bg_surface / hover background.*
  - `color(self, hex_or_name, alpha)` [L100-L105] — *Return a QColor instance with an optional alpha channel (0-255).*
  - `pen(self, hex_or_name, width, style, alpha)` [L107-L121] — *Return a configured QPen with color, width, style, and alpha.*
  - `brush(self, hex_or_name, alpha, style)` [L123-L135] — *Return a configured QBrush with color, style, and alpha.*
  - `waveform_brush(self, opacity)` [L141-L144] — *Return QBrush for the waveform envelope with specified opacity (0.0 - 1.0).*
  - `playhead_pen(self, width)` [L146-L148] — *Return QPen for the active timeline playhead line.*
  - `ruler_background_color(self)` [L150-L152] — *Return QColor for the timeline ruler background strip.*
  - `ruler_tick_pen(self)` [L154-L156] — *Return QPen for ruler division tick marks and text labels.*
  - `ruler_divider_pen(self)` [L158-L160] — *Return QPen for the border line between ruler and waveform canvas.*
  - `selection_rect_brush(self, is_transcript)` [L162-L166] — *Return QBrush for timeline/transcript selection overlays.*
  - `selection_rect_pen(self)` [L168-L170] — *Return QPen for selection range bounding border.*
  - `selection_handle_brush(self)` [L172-L174] — *Return QBrush for dragging edge handles.*
  - `story_segment_brush(self, index, is_selected)` [L176-L180] — *Return QBrush for story region with index-based palette and selection alpha.*
  - `story_segment_color(self, index, is_selected, alpha)` [L182-L187] — *Return QColor for story region with index-based palette and selection alpha.*
  - `story_segment_pen(self, index, is_selected)` [L189-L195] — *Return QPen for story region boundary line.*
- **Functions**:
  - `theme_tokens_for_mode(mode)` [L297-L307] — *Return the ThemeTokens preset matching a Preferences theme_mode value*

### `timeline_canvas.py` (1329 lines)
*TimelineCanvas: Interactive timeline widget rendering time rulers, waveforms, video thumbnails, and story segments.*
- **class `TimelineCanvas(QWidget)`** (lines 37–1329):
  - `__init__(self, parent, tokens)` [L57-L145]
  - `set_is_video(self, is_video)` [L147-L150]
  - `set_background_generation_active(self, task_name, active)` [L152-L170]
  - `_activate_background_banner(self)` [L172-L177]
  - `_update_background_status_text(self)` [L179-L192]
  - `dragEnterEvent(self, event)` [L194-L200]
  - `dropEvent(self, event)` [L202-L208]
  - `set_audio_filename(self, filename)` [L210-L213]
  - `set_duration(self, duration)` [L215-L222]
  - `set_position(self, position)` [L224-L227]
  - `set_playing_state(self, is_playing)` [L229-L230]
  - `ensure_position_visible(self, target_time)` [L232-L252]
  - `set_transcript_selection_range(self, start, end)` [L254-L259]
  - `set_stories(self, stories, selected_indices)` [L261-L265]
  - `set_waveform_peaks(self, peaks, levels)` [L267-L278]
  - `set_timeline_views(self, show_waveform, show_thumbnails)` [L280-L284]
  - `set_video_thumbnails(self, thumbnails)` [L286-L293]
  - `set_skip_seconds(self, seconds)` [L295-L296]
  - `visible_duration(self)` [L298-L299]
  - `clamp_scroll_offset(self)` [L301-L304]
  - `time_to_x(self, time_val, width)` [L306-L309]
  - `x_to_time(self, x_val, width)` [L311-L313]
  - `snap_time(self, raw_time, exclude_story_idx, width, pixel_threshold)` [L315-L354]
  - `find_edge_at_pos(self, pos_x, width)` [L356-L365]
  - `find_fade_handle_at_pos(self, pos_x, pos_y, width)` [L369-L393]
  - `find_story_at_time(self, time)` [L395-L403]
  - `is_near_playhead(self, pos_x, width)` [L405-L407]
  - `set_zoom(self, new_zoom, center_x, focus_time)` [L409-L433]
  - `resizeEvent(self, event)` [L435-L437]
  - `wheelEvent(self, event)` [L439-L484]
  - `mousePressEvent(self, event)` [L486-L562]
  - `mouseMoveEvent(self, event)` [L564-L685]
  - `mouseReleaseEvent(self, event)` [L687-L755]
  - `_show_timeline_context_menu(self, global_pos, pos_x)` [L757-L810]
  - `_show_selection_context_menu(self, global_pos)` [L812-L852]
  - `keyPressEvent(self, event)` [L854-L933]
  - `set_thumbnail_position(self, position)` [L935-L939]
  - `render_waveform_buffer(self, width, height)` [L941-L1103]
  - `paintEvent(self, event)` [L1105-L1329]

### `timeline_envelope.py` (51 lines)
*Waveform envelope data structure and multi-resolution pyramid downsampling.*
- **class `WaveformEnvelope(list)`** (lines 12–16):
  *Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels.*
  - `__init__(self, iterable, levels)` [L14-L16]
- **Functions**:
  - `build_waveform_pyramid(peaks)` [L19-L51] — *Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.*

### `timeline_overview.py` (351 lines)
*Timeline Resize Handle and Overview Navigation Bar widgets.*
- **class `TimelineResizeHandle(QWidget)`** (lines 12–71):
  *Visual drag-handle at the bottom of the timeline allowing vertical resizing.*
  - `__init__(self, target_widget, parent)` [L14-L22]
  - `paintEvent(self, event)` [L24-L38]
  - `mousePressEvent(self, event)` [L40-L47]
  - `mouseMoveEvent(self, event)` [L49-L58]
  - `mouseReleaseEvent(self, event)` [L60-L71]
- **class `TimelineOverviewBar(QWidget)`** (lines 74–351):
  *Interactive navigation overview pill below the timeline with drag-to-zoom edge handles.*
  - `__init__(self, canvas, parent, tokens)` [L81-L99]
  - `get_pill_rect(self)` [L101-L112]
  - `_hit_test(self, pos_x)` [L114-L124]
  - `paintEvent(self, event)` [L126-L197]
  - `mousePressEvent(self, event)` [L199-L250]
  - `mouseMoveEvent(self, event)` [L252-L318]
  - `mouseReleaseEvent(self, event)` [L320-L334]
  - `leaveEvent(self, event)` [L336-L339]
  - `setRange(self, min_val, max_val)` [L341-L342]
  - `setPageStep(self, step)` [L344-L345]
  - `setSingleStep(self, step)` [L347-L348]
  - `setValue(self, val)` [L350-L351]

### `timeline_widgets.py` (1898 lines)
*Radio & TV Story Segmenter — Timeline Ruler, Track Views, Playhead, Overview & Canvas Widgets.*
- **class `WaveformEnvelope(list)`** (lines 49–53):
  *Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels.*
  - `__init__(self, iterable, levels)` [L51-L53]
- **class `TimelineCanvas(QWidget)`** (lines 92–1440):
  - `__init__(self, parent, tokens)` [L112-L202]
  - `set_is_video(self, is_video)` [L204-L207]
  - `set_background_generation_active(self, task_name, active)` [L209-L228] — *Set generation state for 'waveform' or 'thumbnails'.*
  - `_activate_background_banner(self)` [L230-L235]
  - `_update_background_status_text(self)` [L237-L250]
  - `dragEnterEvent(self, event)` [L252-L258]
  - `dropEvent(self, event)` [L260-L266]
  - `set_audio_filename(self, filename)` [L268-L271]
  - `set_duration(self, duration)` [L273-L281]
  - `set_position(self, position)` [L283-L286]
  - `set_playing_state(self, is_playing)` [L288-L289]
  - `ensure_position_visible(self, target_time)` [L291-L311]
  - `set_transcript_selection_range(self, start, end)` [L313-L318]
  - `set_stories(self, stories, selected_indices)` [L320-L324]
  - `set_waveform_peaks(self, peaks, levels)` [L326-L337]
  - `set_timeline_views(self, show_waveform, show_thumbnails)` [L339-L343]
  - `set_video_thumbnails(self, thumbnails)` [L345-L352]
  - `set_skip_seconds(self, seconds)` [L354-L355]
  - `visible_duration(self)` [L357-L358]
  - `clamp_scroll_offset(self)` [L360-L363]
  - `time_to_x(self, time_val, width)` [L365-L368]
  - `x_to_time(self, x_val, width)` [L370-L372]
  - `snap_time(self, raw_time, exclude_story_idx, width, pixel_threshold)` [L374-L419] — *Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels.*
  - `find_edge_at_pos(self, pos_x, width)` [L421-L430]
  - `find_fade_handle_at_pos(self, pos_x, pos_y, width)` [L434-L461] — *Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks.*
  - `find_story_at_time(self, time)` [L463-L472] — *Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping.*
  - `is_near_playhead(self, pos_x, width)` [L474-L476]
  - `set_zoom(self, new_zoom, center_x, focus_time)` [L478-L504]
  - `resizeEvent(self, event)` [L506-L508]
  - `wheelEvent(self, event)` [L510-L560]
  - `mousePressEvent(self, event)` [L562-L646]
  - `mouseMoveEvent(self, event)` [L648-L774]
  - `mouseReleaseEvent(self, event)` [L776-L846]
  - `_show_timeline_context_menu(self, global_pos, pos_x)` [L848-L901]
  - `_show_selection_context_menu(self, global_pos)` [L903-L943]
  - `keyPressEvent(self, event)` [L945-L1026]
  - `set_thumbnail_position(self, position)` [L1028-L1032]
  - `render_waveform_buffer(self, width, height)` [L1034-L1205]
  - `paintEvent(self, event)` [L1207-L1440]
- **class `TimelineResizeHandle(QWidget)`** (lines 1443–1504):
  *Visual drag-handle at the bottom of the timeline allowing vertical resizing.*
  - `__init__(self, target_widget, parent)` [L1445-L1453]
  - `paintEvent(self, event)` [L1455-L1471]
  - `mousePressEvent(self, event)` [L1473-L1480]
  - `mouseMoveEvent(self, event)` [L1482-L1491]
  - `mouseReleaseEvent(self, event)` [L1493-L1504]
- **class `TimelineOverviewBar(QWidget)`** (lines 1507–1795):
  *Interactive navigation overview pill below the timeline with drag-to-zoom edge handles.*
  - `__init__(self, canvas, parent, tokens)` [L1514-L1532]
  - `get_pill_rect(self)` [L1534-L1545]
  - `_hit_test(self, pos_x)` [L1547-L1559]
  - `paintEvent(self, event)` [L1561-L1640]
  - `mousePressEvent(self, event)` [L1642-L1694]
  - `mouseMoveEvent(self, event)` [L1696-L1762]
  - `mouseReleaseEvent(self, event)` [L1764-L1778]
  - `leaveEvent(self, event)` [L1780-L1783]
  - `setRange(self, min_val, max_val)` [L1785-L1786]
  - `setPageStep(self, step)` [L1788-L1789]
  - `setSingleStep(self, step)` [L1791-L1792]
  - `setValue(self, val)` [L1794-L1795]
- **class `TimelineWidget(QWidget)`** (lines 1798–1896):
  - `__init__(self, parent, tokens)` [L1801-L1838]
  - `set_is_video(self, is_video)` [L1840-L1842]
  - `set_background_generation_active(self, task_name, active)` [L1844-L1846]
  - `dragEnterEvent(self, event)` [L1848-L1852]
  - `dropEvent(self, event)` [L1854-L1860]
  - `update_scrollbar_range(self)` [L1862-L1871]
  - `update_scrollbar_from_canvas(self, offset)` [L1873-L1881]
  - `update_canvas_from_scrollbar(self, val)` [L1883-L1893]
  - `__getattr__(self, name)` [L1895-L1896]
- **Functions**:
  - `build_waveform_pyramid(peaks)` [L56-L88] — *Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.*

### `transcript_cleaner.py` (216 lines)
*Radio & TV Segmenter — Transcript cleaning, loop collapsing, and hallucination scrubbing.*
- **Functions**:
  - `collapse_repeating_ngrams(text, max_n, min_repeats)` [L36-L87] — *Detect and collapse degenerate repeating word/token loops in transcription text.*
  - `strip_hallucination_phrases(text)` [L90-L106] — *Filter out standard Whisper hallucination phrases and repetitive acoustic tags.*
  - `trim_trailing_degenerate_tail(segments, min_tail_repeats)` [L109-L121] — *Inspect the trailing segments of a transcript and truncate degenerate infinite loops at the end.*
  - `scrub_transcript_segments(segments, collapse_loops)` [L124-L202] — *Comprehensive scrubber for transcript segment lists:*
  - `scrub_transcript(transcript)` [L205-L216] — *Clean and sanitize a complete transcript payload dictionary.*

### `transcript_context_menu_mixin.py` (415 lines)
*Radio & TV Story Segmenter — Interactive Transcript Context Menu & Bubble Actions Mixin.*
- **class `TranscriptContextMenuMixin`** (lines 36–415):
  *Mixin for context menu construction and selection bubble quick-actions.*
  - `_on_bubble_play(self)` [L39-L44]
  - `_on_bubble_story(self)` [L46-L51]
  - `_on_bubble_note(self)` [L53-L66]
  - `_on_bubble_cut(self)` [L68-L73]
  - `_on_bubble_export(self)` [L75-L80]
  - `show_context_menu(self, position)` [L82-L415]

### `transcript_editor.py` (862 lines)
*transcript_editor.py - Interactive Transcript Editor & Viewer Components*
- **Public Exports (`__all__`)**: FindReplaceDialog, TranscriptSelectionBubble, transcript_text_view_stylesheet, clean_dark_mode_clipboard_html, InteractiveTranscriptEdit
- **class `InteractiveTranscriptEdit(TranscriptContextMenuMixin, TranscriptFormattingMixin, TranscriptTimelineSyncMixin, QTextEdit)`** (lines 116–862):
  - `__init__(self, parent)` [L129-L188]
  - `lock_scroll_position(self, v_val, h_val, duration_ms)` [L190-L211] — *Pin vertical and horizontal scrollbars to exact pixel values during layout reflows.*
  - `_release_scroll_lock(self)` [L213-L216]
  - `_on_v_range_changed(self, min_val, max_val)` [L218-L222]
  - `focusInEvent(self, event)` [L224-L240]
  - `_enforce_scroll_after_focus(self, target_v, target_h)` [L242-L248]
  - `createMimeDataFromSelection(self)` [L250-L264] — *Clean dark-mode white/light plain text colors to black (#000000) when copying.*
  - `wheelEvent(self, event)` [L266-L271]
  - `event(self, e)` [L273-L322]
  - `paintEvent(self, event)` [L324-L387]
  - `dragEnterEvent(self, event)` [L389-L393]
  - `dragMoveEvent(self, event)` [L395-L399]
  - `dropEvent(self, event)` [L401-L411]
  - `apply_theme_style(self, mode)` [L413-L416]
  - `set_font_scale(self, scale)` [L418-L428] — *Set transcript font scale without affecting the rest of the UI.*
  - `set_editing_mode(self, enabled)` [L430-L446]
  - `mousePressEvent(self, event)` [L448-L488]
  - `mouseMoveEvent(self, event)` [L490-L538]
  - `leaveEvent(self, event)` [L540-L544]
  - `mouseReleaseEvent(self, event)` [L546-L632]
  - `keyPressEvent(self, event)` [L634-L862]

### `transcript_editor_dialogs.py` (214 lines)
*transcript_editor_dialogs.py - Dialog and floating toolbar components for transcript editing.*
- **class `FindReplaceDialog(QDialog)`** (lines 42–130):
  *Modeless find-and-replace dialog for QTextEdit / InteractiveTranscriptEdit.*
  - `__init__(self, text_edit, parent)` [L45-L78]
  - `get_flags(self)` [L80-L84]
  - `find_next(self)` [L86-L98]
  - `replace(self)` [L100-L108]
  - `replace_all(self)` [L110-L130]
- **class `TranscriptSelectionBubble(QFrame)`** (lines 133–214):
  *Floating quick-action toolbar on transcript selection (Milestone 3.12).*
  - `__init__(self, parent)` [L142-L209]
  - `_emit_comment(self)` [L211-L214]

### `transcript_formatting_mixin.py` (340 lines)
*Radio & TV Story Segmenter — Interactive Transcript Formatting Mixin.*
- **class `TranscriptFormattingMixin`** (lines 33–340):
  *Mixin for text formatting actions (bold, italic, underline, highlight, clear).*
  - `toggle_bold(self)` [L36-L53]
  - `toggle_italic(self)` [L55-L70]
  - `toggle_underline(self)` [L72-L87]
  - `toggle_strikethrough(self)` [L89-L105]
  - `_get_target_word_indices_for_selection_or_cursor(self, flat_words)` [L107-L177]
  - `toggle_highlight(self, color_name, force_apply)` [L179-L245]
  - `remove_highlight(self)` [L247-L299]
  - `clear_formatting(self)` [L301-L328]
  - `get_current_formatting(self)` [L330-L340]

### `transcript_navigation_mixin.py` (299 lines)
*transcript_navigation_mixin.py - Timestamp discovery, caret positioning, anchor indexing, and playback highlighting.*
- **class `TranscriptNavigationMixin`** (lines 34–299):
  *Mixin managing time anchor indexing, cursor timestamp discovery, and live playback highlighting.*
  - `_nearest_word_anchor(self, cursor)` [L37-L70] — *Return the word anchor nearest the actual QTextDocument cursor.*
  - `get_timestamp_at_cursor(self, cursor)` [L72-L92]
  - `get_block_start_timestamp(self, cursor)` [L94-L109]
  - `get_block_end_timestamp(self, cursor)` [L111-L129]
  - `get_segment_index_at_cursor(self, cursor)` [L131-L151]
  - `move_cursor_to_segment_start(self, seg_idx)` [L153-L171] — *Best-effort: places the caret at the first word of seg_idx after*
  - `rebuild_anchor_index(self)` [L173-L220] — *Index transcript anchors once so playback highlighting is O(1) lookup,*
  - `set_time_anchor_index(self, entries)` [L222-L224]
  - `clear_highlight(self)` [L226-L233]
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L235-L299]

### `transcript_playback_highlight_mixin.py` (276 lines)
*Radio & TV Story Segmenter — Interactive Transcript Playback Highlighting Mixin.*
- **class `TranscriptPlaybackHighlightMixin`** (lines 24–276):
  *Mixin managing real-time audio playback word synchronization and time anchors.*
  - `_nearest_word_anchor(self, cursor)` [L27-L59] — *Return the word anchor nearest the actual QTextDocument cursor.*
  - `get_timestamp_at_cursor(self, cursor)` [L61-L80]
  - `get_block_start_timestamp(self, cursor)` [L82-L97]
  - `get_block_end_timestamp(self, cursor)` [L99-L117]
  - `get_segment_index_at_cursor(self, cursor)` [L119-L138]
  - `move_cursor_to_segment_start(self, seg_idx)` [L140-L156] — *Best-effort: places the caret at the first word of seg_idx after*
  - `rebuild_anchor_index(self)` [L158-L205] — *Index transcript anchors once so playback highlighting is O(1) lookup,*
  - `set_time_anchor_index(self, entries)` [L207-L209]
  - `clear_highlight(self)` [L211-L217]
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L219-L276]

### `transcript_selection_mixin.py` (420 lines)
*transcript_selection_mixin.py - Multi-selection, timeline spans, comment ranges, and bubble actions.*
- **class `TranscriptSelectionMixin`** (lines 31–420):
  *Mixin managing selection state, multi-select accumulation, comment highlights,*
  - `set_selection_mode(self, mode)` [L35-L39]
  - `set_char_timestamp_map(self, mapping)` [L41-L42]
  - `has_active_selection(self)` [L44-L50]
  - `clear_all_selections(self)` [L52-L65]
  - `get_time_range_for_char_span(self, start_pos, end_pos)` [L67-L83]
  - `get_selected_time_range(self)` [L85-L98]
  - `get_all_selected_story_ranges(self)` [L100-L121] — *Returns a list of dicts: [{'start_time': float, 'end_time': float, 'text': str, ...}, ...]*
  - `select_comment_range(self, seg_idx)` [L123-L168] — *Navigate and select the exact comment text range in the transcript view.*
  - `update_extra_selections(self)` [L170-L292]
  - `set_timeline_selection_span(self, start_char, end_char)` [L294-L299]
  - `_on_selection_completed(self, cursor)` [L301-L377]
  - `_on_bubble_play(self)` [L379-L384]
  - `_on_bubble_story(self)` [L386-L391]
  - `_on_bubble_note(self)` [L393-L406]
  - `_on_bubble_cut(self)` [L408-L413]
  - `_on_bubble_export(self)` [L415-L420]

### `transcript_story.py` (836 lines)
*Radio & TV Segmenter v3.9.11-beta — transcript story responsibilities.*
- **Public Exports (`__all__`)**: TranscriptStoryMixin, Story, SetStoriesCommand, SelectStoriesCommand, StoryBoundaryChangeCommand, StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin, ChangeSpeakerDialog, VoiceProfileMatchDialog, StoryFadesDialog, SpeakerManagerDialog, FADE_CURVE_TABLES, get_fade_curve_factors
- **class `TranscriptStoryMixin(StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin)`** (lines 62–835):
  - `render_transcript(self)` [L63-L452]
  - `on_transcript_selection_changed(self)` [L454-L486]
  - `on_transcript_text_changed(self)` [L488-L644]
  - `transcript_clicked(self, url)` [L646-L662]
  - `edit_segment_comment_dialog(self, seg_idx, sel_text, start_char, end_char, t_range, covered_indices)` [L664-L745]
  - `add_comment_from_selection(self)` [L749-L792]
  - `delete_segment_comment(self, seg_idx)` [L794-L814]
  - `toggle_comments_panel(self)` [L816-L819]
  - `toggle_show_comments(self, checked)` [L821-L827]
  - `toggle_comment_highlights(self, checked)` [L831-L835]

### `transcript_styles.py` (104 lines)
*transcript_styles.py - Transcript view stylesheets and dark-mode clipboard styling normalizers.*
- **Functions**:
  - `transcript_text_view_stylesheet(mode, font_size)` [L19-L62] — *Shared visual treatment for transcript-style views.*
  - `clean_dark_mode_clipboard_html(raw_html)` [L65-L104] — *Normalize plain text font colors to black (#000000) for external pasting.*

### `transcript_timeline_sync_mixin.py` (566 lines)
*Radio & TV Story Segmenter — Transcript Timeline & Playback Synchronization Mixin.*
- **class `TranscriptTimelineSyncMixin`** (lines 34–566):
  *Mixin for audio timecode synchronization, anchor indexing, and playback highlighting.*
  - `set_selection_mode(self, mode)` [L37-L41]
  - `set_char_timestamp_map(self, mapping)` [L43-L44]
  - `has_active_selection(self)` [L46-L52]
  - `clear_all_selections(self)` [L54-L67]
  - `get_time_range_for_char_span(self, start_pos, end_pos)` [L69-L85]
  - `get_selected_time_range(self)` [L87-L100]
  - `get_all_selected_story_ranges(self)` [L102-L122]
  - `select_comment_range(self, seg_idx)` [L124-L168]
  - `update_extra_selections(self)` [L170-L287]
  - `set_timeline_selection_span(self, start_char, end_char)` [L289-L294]
  - `_on_selection_completed(self, cursor)` [L296-L316]
  - `_nearest_word_anchor(self, cursor)` [L318-L349]
  - `get_timestamp_at_cursor(self, cursor)` [L351-L370]
  - `get_block_start_timestamp(self, cursor)` [L372-L387]
  - `get_block_end_timestamp(self, cursor)` [L389-L407]
  - `get_segment_index_at_cursor(self, cursor)` [L409-L428]
  - `move_cursor_to_segment_start(self, seg_idx)` [L430-L445]
  - `rebuild_anchor_index(self)` [L447-L492]
  - `set_time_anchor_index(self, entries)` [L494-L496]
  - `clear_highlight(self)` [L498-L504]
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L506-L566]

### `transcription_processing.py` (524 lines)
*Transcription background process management for Radio & TV Story Segmenter.*
- **class `TranscriptionProcessingMixin`** (lines 31–523):
  - `start_transcription(self)` [L32-L192]
  - `on_transcription_output(self, force_flush)` [L194-L278]
  - `on_transcription_stderr(self)` [L280-L303] — *Route the worker's stderr (third-party library warnings, C-level*
  - `_handle_live_streaming_segment(self, segment)` [L305-L344] — *Append an incoming live transcript chunk directly to the view without rebuilding the map.*
  - `on_transcription_process_finished(self, exit_code, exit_status)` [L346-L369]
  - `on_transcription_process_error(self, error)` [L371-L378]
  - `cleanup_transcription_process(self)` [L380-L397]
  - `transcription_progress(self, message, percent)` [L399-L400]
  - `transcription_finished(self, transcript)` [L402-L503]
  - `transcription_error(self, message)` [L505-L523]

### `translation.py` (896 lines)
*Radio & TV Segmenter — Local Translation Mixin.*
- **class `TranslationEnvSetupWorker(QObject)`** (lines 35–92):
  *Background worker that sets up the isolated translation runtime environment.*
  - `__init__(self, plugin_dir, runtime_mgr)` [L40-L45]
  - `cancel(self)` [L47-L49]
  - `run(self)` [L51-L92]
- **class `TranslationMixin`** (lines 132–896):
  *Mixin class managing transcript translation, language toggling, and worker lifecycle.*
  - `source_language_code(self)` [L135-L169] — *Return the source language code for translation.*
  - `target_language_code(self)` [L171-L179] — *Return the target language code for translation (see source_language_code).*
  - `translation_key(self, from_code, to_code)` [L181-L183] — *Generate standardized dictionary key for language translation pair.*
  - `get_translation_item(self, from_code, to_code)` [L185-L194] — *Return a current translation for an explicit language pair.*
  - `translation_export_spec(self, options)` [L196-L209] — *Return (source, target, suffix) for batch translation exports.*
  - `translation_is_current(self, key)` [L211-L225] — *Check if translation for the given key exists, has content, and is not stale.*
  - `has_spanish_translation(self)` [L227-L233] — *Check if an English-to-Spanish translation is available.*
  - `get_spanish_translation_item(self)` [L235-L255] — *Return the translation dictionary for en-es or es-en if present.*
  - `mark_stale_translations(self)` [L257-L264] — *Mark all existing translations as stale when transcript text changes.*
  - `update_translation_language_selector(self)` [L266-L327] — *Update translation UI selector states (tabs / combobox / actions).*
  - `change_translation_display(self, mode)` [L329-L347] — *Change the active translation display mode ('en', 'es', or 'split').*
  - `render_translation_view(self)` [L349-L351] — *Re-render transcript or translation view based on current display settings.*
  - `check_translation_models_async(self)` [L353-L368] — *Asynchronously verify if required translation models are installed.*
  - `_cleanup_translation_env_thread(self)` [L370-L390]
  - `_on_translation_env_progress(self, percent_or_msg, message)` [L392-L405]
  - `stop_translation_worker(self, timeout_ms)` [L407-L460]
  - `_start_translation_runtime_request(self, request, on_finished)` [L462-L548] — *Run translation code in the plugin-owned isolated Python environment.*
  - `_on_translation_env_setup_finished(self, error)` [L550-L593]
  - `_launch_translation_process(self, request, on_finished, python_exe, entry)` [L595-L722]
  - `start_translation(self, from_code, to_code, install_if_missing)` [L724-L798] — *Start local translation in the translation plugin's isolated runtime.*
  - `_on_translation_progress(self, percent, message)` [L800-L810] — *Handle progress updates from _translation_worker_class().*
  - `_on_translation_finished(self, translated_transcript, translation_key)` [L812-L862] — *Handle successful translation results.*
  - `_on_translation_cancelled(self, results, translation_key)` [L864-L874] — *Handle translation worker cancellation.*
  - `_on_translation_error(self, error_message)` [L876-L887] — *Handle translation worker failures.*
  - `_on_translation_thread_finished(self)` [L889-L892] — *Clean up thread reference.*
  - `_translation_thread_finished(self)` [L894-L896] — *Alias for _on_translation_thread_finished.*
- **Functions**:
  - `_translation_worker_class()` [L22-L25] — *Load the translation worker only when the translation plugin is installed.*
  - `_translation_runtime_entry_path(app)` [L95-L121]
  - `_translation_runtime_manager(app)` [L123-L130]

### `ui_dialog_launchers.py` (304 lines)
*Dialog launchers and external modal helpers for Radio & TV Story Segmenter.*
- **class `UiDialogLaunchersMixin`** (lines 25–303):
  *Mixin providing dialog launcher methods for shortcuts, benchmarks, diagnostics, and plugins.*
  - `open_project_dialog(self)` [L27-L42] — *Prompt user to open a project file (*.rtvs).*
  - `open_find_dialog(self)` [L44-L50] — *Display the Find and Replace dialog window.*
  - `show_shortcuts_dialog(self)` [L53-L208] — *Display a searchable or structured reference table of all active shortcuts.*
  - `show_diagnostic_test_bench(self)` [L210-L222] — *Open the interactive System Diagnostic Test Bench dialog.*
  - `show_performance_benchmark(self)` [L224-L236] — *Open the interactive System Performance & Speed Benchmark dialog.*
  - `open_plugins_manager(self)` [L238-L245] — *Open the Plugin Manager dialog to enable, disable, or inspect plugins.*
  - `open_id3_tag_editor(self, mp3_path)` [L247-L259] — *Open the ID3 Tag Editor dialog to view and edit MP3 audio metadata.*
  - `open_youtube_publish_dialog(self, story)` [L262-L285] — *Open the YouTube video publishing dialog or export view from the YouTube plugin.*
  - `open_wordpress_publish_dialog(self, story)` [L287-L303] — *Open the WordPress direct publish dialog from the WordPress plugin.*

### `ui_layout.py` (1027 lines)
*Radio & TV Segmenter — UI Layout & Menu Construction Mixin.*
- **class `UiLayoutMixin(UiMenusMixin, UiDialogLaunchersMixin)`** (lines 57–1023):
  *Mixin class providing UI construction, menu assembly, and UI event binding.*
  - `build_ui(self)` [L59-L717] — *Build and assemble all central widgets, layouts, and panels.*
  - `filter_transcript_search(self, target)` [L719-L736] — *Highlight and focus next occurrence of search term in transcript text view.*
  - `toggle_transcript_editing_mode(self, *args, **kwargs)` [L738-L760] — *Toggle between Viewing Mode (navigation/click-to-seek) and Editing Mode (text editing).*
  - `_on_transcript_editing_mode_changed(self, is_editing)` [L762-L797] — *Respond to changes in transcript edit vs view mode.*
  - `_sync_format_toolbar_buttons(self)` [L799-L819]
  - `_on_toolbar_split_speaker(self)` [L821-L828]
  - `_apply_transcript_font_scale(self, scale, persist)` [L830-L854] — *Apply a transcript-only font scale and optionally persist it.*
  - `_on_font_size_combo_changed(self, index)` [L856-L860]
  - `adjust_transcript_font_size(self, direction)` [L862-L864] — *Increase or decrease transcript font size by one 5% step.*
  - `reset_transcript_font_size(self)` [L866-L868] — *Restore the default transcript font size.*
  - `update_story_list_height(self)` [L870-L885] — *Size the story list to fit the current number of stories, leaving space for metadata and export fields.*
  - `auto_generate_selected_story_excerpt(self)` [L887-L915] — *Auto-generate an excerpt from the story transcript text for the currently selected story.*
  - `_on_story_excerpt_text_changed(self)` [L917-L934] — *Synchronize excerpt edits from the inline editor into story metadata.*
  - `toggle_maximize_stories_panel(self)` [L936-L989] — *Toggle maximize/restore of the stories panel across the full application window.*
  - `setup_plugin_story_extensions(self)` [L991-L1013] — *Populate plugin-provided widgets in the story panel.*
  - `notify_story_selection_to_plugins(self, selected_story)` [L1015-L1023] — *Notify all enabled plugins when the active story selection changes.*

### `ui_menus.py` (775 lines)
*Main application menu bar and action assembly for Radio & TV Story Segmenter.*
- **class `PersistentMenu(QMenu)`** (lines 50–73):
  *A QMenu subclass that stays open when checkable toggle options are activated,*
  - `addMenu(self, *args, **kwargs)` [L54-L59]
  - `mouseReleaseEvent(self, event)` [L61-L73]
- **class `UiMenusMixin`** (lines 78–774):
  *Mixin providing menu construction, action shortcut wiring, and menu synchronization.*
  - `build_menus(self)` [L80-L618] — *Construct the main application menu bar and associated keyboard shortcuts.*
  - `apply_user_shortcuts(self)` [L620-L625] — *Rebind all menu actions and application shortcuts according to user preferences.*
  - `_refresh_recent_projects_menu(self)` [L627-L655] — *Update recent projects submenu items based on user settings store.*
  - `_check_external_dependencies(self)` [L657-L671] — *Check bundled media tools and record actionable diagnostics.*
  - `_sync_undo_redo_actions(self)` [L673-L682] — *Synchronize undo/redo action states with QUndoStack.*
  - `_remember_directory(self, path)` [L684-L694] — *Persist directory of chosen file to improve user file dialog experience.*
  - `update_processing_menu_status(self)` [L697-L720] — *Update label annotations on Tools actions reflecting pipeline stage completion.*
  - `refresh_plugin_menus(self)` [L723-L774] — *Dynamically populate plugin export actions, tools menu actions, and core UI controls.*

### `updater.py` (1418 lines)
*Update manager and GitHub release installer for Radio & TV Segmenter.*
- **class `CheckUpdateWorker(QThread)`** (lines 649–707):
  - `__init__(self, repo, parent, channel)` [L655-L661]
  - `run(self)` [L663-L707]
- **class `DownloadUpdateWorker(QThread)`** (lines 772–854):
  - `__init__(self, download_url, file_name, parent, release_info)` [L777-L782]
  - `cancel(self)` [L784-L785]
  - `run(self)` [L787-L854]
- **class `CheckUpdateDialog(QDialog)`** (lines 857–1382):
  - `__init__(self, parent, auto_start)` [L858-L889]
  - `_build_ui(self)` [L891-L1026]
  - `_on_channel_changed(self, index)` [L1028-L1035]
  - `start_check(self)` [L1037-L1057]
  - `_on_releases_loaded(self, releases)` [L1059-L1094]
  - `_on_version_selected(self, index)` [L1096-L1100]
  - `_display_release(self, release_info)` [L1102-L1188]
  - `_on_up_to_date(self, current_ver, remote_tag)` [L1190-L1202]
  - `_on_update_available(self, release_info, asset_info, is_newer)` [L1204-L1205]
  - `_on_check_error(self, message)` [L1207-L1213]
  - `_handle_primary_action(self)` [L1215-L1229]
  - `_confirm_downgrade(self, target_version)` [L1231-L1246] — *Modal Warning Dialog when selecting a version lower than installed PROJECT_VERSION.*
  - `start_download(self)` [L1248-L1278]
  - `_on_download_progress(self, percent, downloaded, total, speed_str)` [L1280-L1284]
  - `_on_download_finished(self, file_path)` [L1286-L1293]
  - `_on_download_error(self, message)` [L1295-L1314]
  - `_install_and_restart(self)` [L1316-L1364]
  - `_open_github_release(self)` [L1366-L1368]
  - `_handle_close(self)` [L1370-L1382]
- **class `UpdaterMixin`** (lines 1385–1418):
  - `check_for_updates(self, interactive)` [L1386-L1392]
  - `trigger_silent_update_check(self)` [L1394-L1418]
- **Functions**:
  - `parse_version_tuple(version_str)` [L117-L150] — *Parse version string into comparable numerical components and a pre-release weight tuple.*
  - `is_version_newer(remote_version_str, current_version_str)` [L153-L160] — *Return True if remote_version_str is strictly newer than current_version_str.*
  - `is_version_older(remote_version_str, current_version_str)` [L163-L170] — *Return True if remote_version_str is strictly older than current_version_str.*
  - `format_byte_size(num_bytes)` [L173-L180]
  - `_is_trusted_download_url(url)` [L183-L192]
  - `_find_release_checksum(release_info, asset_name)` [L195-L234]
  - `select_best_asset_for_platform(assets, target_version, repo)` [L237-L307] — *Select the most suitable release asset dictionary for the current operating system,*
  - `fetch_releases(repo, max_releases, channel)` [L310-L373] — *Query GitHub API for published releases, sorted semantically by version number.*
  - `fetch_latest_release(repo)` [L376-L381] — *Query GitHub API for the most recent release (backward-compatibility wrapper).*
  - `_write_update_log(msg)` [L384-L394] — *Append timestamped message to the update helper log in LocalAppData.*
  - `launch_and_install(file_path, parent)` [L397-L646]
  - `cleanup_old_installers(max_to_keep, force_all)` [L710-L769] — *Clean up old downloaded application update installers from AppData/updates directory.*

### `utils/__init__.py` (36 lines)
*Utility modules for Radio & TV Story Segmenter.*
- **Public Exports (`__all__`)**: APP_DISPLAY_NAME, PROJECT_VERSION, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, HELPER_PROTOCOL_VERSION, WAVEFORM_ANALYSIS_RATE, WAVEFORM_POINTS_PER_SECOND, MIN_WORDS_PER_PARAGRAPH, MAX_ACTIVITY_SNAPSHOTS, get_github_repo, format_time, parse_time, safe_filename, is_sentence_end

### `utils/constants.py` (41 lines)
*Application constants and environment configuration.*
- **Public Exports (`__all__`)**: APP_DISPLAY_NAME, PROJECT_VERSION, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, HELPER_PROTOCOL_VERSION, WAVEFORM_ANALYSIS_RATE, WAVEFORM_POINTS_PER_SECOND, MIN_WORDS_PER_PARAGRAPH, MAX_ACTIVITY_SNAPSHOTS, get_github_repo

### `utils/time_format.py` (19 lines)
*Time formatting and parsing utilities.*
- **Public Exports (`__all__`)**: format_time, parse_time, safe_filename, is_sentence_end

### `voice_profile_dialog.py` (1006 lines)
*voice_profile_dialog.py — Dialog for finding and reassigning matching speaker turns using acoustic voice profiles.*
- **Public Exports (`__all__`)**: VoiceProfileMatchDialog
- **class `VoiceProfileMatchDialog(QDialog)`** (lines 29–1004):
  *Dialog for finding and reassigning matching speaker turns using a 256-dimensional acoustic voice profile.*
  - `__init__(self, ref_seg_idx, current_speaker, target_speaker, prompt_new_speaker, ref_seg_indices, parent)` [L32-L666]
  - `_on_playback_state_changed(self, state)` [L668-L673]
  - `_toggle_hints(self)` [L675-L683]
  - `_on_slider_changed(self, val)` [L685-L694]
  - `get_active_ref_indices(self)` [L696-L701]
  - `_on_controls_changed(self)` [L703-L706]
  - `_update_matches(self)` [L708-L779]
  - `_select_all_matches(self)` [L781-L793]
  - `_deselect_all_matches(self)` [L795-L807]
  - `_toggle_master_checkbox(self, checked)` [L809-L826] — *Batch toggle every row checkbox to match the master checkbox state.*
  - `_on_table_item_changed(self, item)` [L828-L836]
  - `_get_selected_segment_indices(self)` [L838-L846]
  - `_update_action_summary(self)` [L848-L878]
  - `_on_apply(self)` [L880-L894]
  - `reject(self)` [L896-L898]
  - `_seek_to_time(self, seconds)` [L900-L905]
  - `_is_playing(self)` [L907-L914]
  - `_stop_playback(self)` [L916-L925]
  - `_toggle_playback(self)` [L927-L940]
  - `_toggle_audition_button(self)` [L942-L951]
  - `_on_table_selection_changed(self)` [L953-L960]
  - `_on_table_cell_double_clicked(self, row, col)` [L962-L968]
  - `eventFilter(self, watched, event)` [L970-L988] — *Intercept Spacebar on the table widget for playback and Return/Enter/X for checkbox toggling.*
  - `keyPressEvent(self, event)` [L990-L1004]

### `voice_profile_matcher_mixin.py` (577 lines)
*Radio & TV Story Segmenter — Acoustic Voice Profile Matching Mixin.*
- **class `VoiceProfileMatcherMixin`** (lines 45–577):
  *Mixin handling WeSpeaker 256-d embeddings and acoustic voice matching.*
  - `get_segment_embedding(self, seg_idx)` [L48-L163] — *Retrieve a genuine 256-dimensional acoustic embedding for this segment.*
  - `get_composite_embedding(self, seg_indices)` [L165-L175]
  - `_build_voice_profile_candidates(self, ref_indices, parent_widget)` [L177-L249] — *Precompute candidate acoustic vectors across transcript segments.*
  - `find_matching_voice_turns(self, ref_seg_idx, threshold, scope_cluster_only, ref_seg_indices, target_name, cached_candidates)` [L251-L401] — *Find transcript turns acoustically matching a verified voice.*
  - `match_acoustic_voice_profile(self, ref_seg_idx, target_speaker, threshold, scope_cluster_only, selected_indices, ref_seg_indices)` [L403-L495]
  - `teach_voice_profile_dialog(self, seg_idx, raw_speaker, prompt_new_speaker)` [L497-L577]

### `voice_profile_ops_mixin.py` (585 lines)
*Radio & TV Story Segmenter — Voice Profile Matching & Embedding Extraction Mixin.*
- **class `VoiceProfileOpsMixin`** (lines 45–585):
  *Mixin for acoustic voice profile matching, WeSpeaker embeddings, and voice training.*
  - `get_segment_embedding(self, seg_idx)` [L48-L163] — *Retrieve a genuine 256-dimensional acoustic embedding for this segment.*
  - `get_composite_embedding(self, seg_indices)` [L165-L175]
  - `_build_voice_profile_candidates(self, ref_indices, parent_widget)` [L177-L249] — *Precompute candidate acoustic vectors across transcript segments.*
  - `find_matching_voice_turns(self, ref_seg_idx, threshold, scope_cluster_only, ref_seg_indices, target_name, cached_candidates)` [L251-L401] — *Find transcript turns acoustically matching a verified voice.*
  - `match_acoustic_voice_profile(self, ref_seg_idx, target_speaker, threshold, scope_cluster_only, selected_indices, ref_seg_indices)` [L403-L494]
  - `teach_voice_profile_dialog(self, seg_idx, raw_speaker, prompt_new_speaker)` [L496-L576]
  - `open_manage_voice_profiles_dialog(self)` [L578-L585]

### `worker_asr_engines.py` (816 lines)
*worker_asr_engines.py - Faster-Whisper, CTranslate2 & Sherpa-ONNX ASR Engines.*
- **Functions**:
  - `set_emit_callback(fn)` [L30-L33] — *Set custom IPC emitter function.*
  - `_emit(message_type, **payload)` [L36-L42]
  - `_patch_av_open()` [L45-L59] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `get_optimal_transcription_threads()` [L62-L81] — *Calculate optimal CPU threads for faster-whisper / CTranslate2 / ONNX.*
  - `get_app_data_dir_pure()` [L84-L102] — *Return platform-specific app data directory in pure Python without PySide6.*
  - `get_models_storage_dir_pure()` [L105-L115] — *Return models storage directory in pure Python without PySide6.*
  - `is_onnx_model_available(model_name)` [L118-L175] — *Check if sherpa-onnx runtime and target model files exist on disk.*
  - `transcribe_parakeet_onnx(audio_file, model_name, detected_lang, detected_confidence, initial_prompt, beam_size)` [L178-L506] — *Run installed ONNX models (Parakeet TDT, Spanish FastConformer, Multilingual FastConformer) through sherpa-onnx.*
  - `probe_audio_language(audio_file, sample_duration, preferred_model)` [L509-L588] — *Run a fast language detection probe using faster-whisper's mel feature extractor.*
  - `transcribe(audio_file, model_name, initial_prompt, beam_size)` [L591-L816] — *Transcribe media file using either Sherpa-ONNX or Faster-Whisper.*

### `worker_clustering.py` (448 lines)
*worker_clustering.py - Acoustic clustering, VAD pause bridging, and centroid assignments.*
- **Functions**:
  - `normalize_audio_for_diarization(source_path)` [L29-L89] — *Extract a normalized 16 kHz mono WAV using the local FFmpeg binary.*
  - `configure_optimal_pytorch_threads()` [L92-L106] — *Clamp torch's intra-op/inter-op thread pools to match the*
  - `_normalize_expected_speakers(value)` [L109-L118] — *Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'.*
  - `_normalize_speaker_labels(segments)` [L121-L134] — *Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',*
  - `_sensitivity_distance_threshold()` [L137-L143] — *Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.*
  - `fast_cluster_ahc(embeddings, k, distance_threshold)` [L146-L202] — *Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).*
  - `apply_clustering_patches()` [L205-L238] — *Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC.*
  - `run_vad_two_pass(audio_path, threshold, min_speech_duration_ms, min_silence_duration_ms, speech_pad_ms, bridge_pause_threshold_sec)` [L241-L314] — *Silero VAD with Pass 1 Pause Bridging (< 100ms).*
  - `assign_short_segments_to_centroids(short_segments, audio_path, centroids, label_values, raw_segments, min_confidence, model)` [L317-L420] — *Extract acoustic embeddings for short segments (< 0.8s) with symmetric audio context padding,*
  - `_calculate_embedding_for_interval(start, end, subsegments, embeddings)` [L423-L448] — *Compute unit-normalized 256-dimensional embedding vector for an interval [start, end].*

### `worker_diarization_clustering.py` (297 lines)
*worker_diarization_clustering.py - Speaker Clustering, Centroid Matching & Math Helpers.*
- **Functions**:
  - `_normalize_expected_speakers(value)` [L20-L29] — *Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'.*
  - `_normalize_speaker_labels(segments)` [L32-L45] — *Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',*
  - `_sensitivity_distance_threshold()` [L48-L55] — *Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.*
  - `fast_cluster_ahc(embeddings, k, distance_threshold)` [L58-L114] — *Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).*
  - `apply_clustering_patches()` [L117-L150] — *Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC.*
  - `assign_short_segments_to_centroids(short_segments, audio_path, centroids, label_values, raw_segments, min_confidence, get_wespeaker_model_fn, safe_tensor_fn)` [L153-L269] — *Extract acoustic embeddings for short segments (< 0.8s) with symmetric context padding,*
  - `_calculate_embedding_for_interval(start, end, subsegments, embeddings)` [L272-L297] — *Compute unit-normalized 256-dimensional embedding vector for an interval [start, end].*

### `worker_diarization_engine.py` (902 lines)
*worker_diarization_engine.py - Speaker Diarization, Neural VAD & Embedding Pipeline.*
- **Functions**:
  - `set_emit_callback(fn)` [L50-L53] — *Set custom IPC emitter function.*
  - `_emit(message_type, **payload)` [L56-L62]
  - `_safe_tensor_from_numpy(arr)` [L65-L80] — *Safely convert a numpy float32 array into a PyTorch tensor.*
  - `normalize_audio_for_diarization(source_path)` [L83-L143] — *Extract a normalized 16 kHz mono WAV using the local FFmpeg binary.*
  - `configure_optimal_pytorch_threads()` [L146-L159] — *Clamp torch's intra-op/inter-op thread pools to match the*
  - `_diarize_solo_fast_path(audio_file, transcript_file)` [L162-L236] — *Solo fast-path: a single expected speaker means there is nothing to*
  - `_get_wespeaker_model()` [L244-L252] — *Retrieve or initialize the cached WeSpeaker ONNX model instance.*
  - `extract_embeddings_batched(audio_path, speech_segments, batch_size, min_segment_duration, embedding_window, embedding_step, progress_callback)` [L255-L374] — *Extract 256-dim speaker embeddings using WeSpeaker ResNet34-LM (ONNX)*
  - `run_vad_two_pass(audio_path, threshold, min_speech_duration_ms, min_silence_duration_ms, speech_pad_ms, bridge_pause_threshold_sec)` [L377-L447] — *Silero VAD with Pass 1 Pause Bridging (< 100ms).*
  - `run_transcript_guided_diarization(normalized_wav, transcript_file, expected_speakers, sensitivity, progress_callback)` [L450-L581] — *Execute transcript-guided speaker diarization directly from sentence boundaries.*
  - `diarize(audio_file, expected_speakers, transcript_file, sensitivity)` [L584-L902] — *Execute complete speaker diarization pipeline on an audio media file.*

### `worker_ipc.py` (216 lines)
*worker_ipc.py - Subprocess IPC protocol, environment setup, and DLL initialization.*
- **Functions**:
  - `emit(message_type, **payload)` [L24-L28] — *Serialize and send structured JSON message to parent process over stdout.*
  - `emit_hello()` [L31-L33] — *Emit startup handshake message identifying protocol version and worker capabilities.*
  - `_patch_av_open()` [L36-L54] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `_clamp_diarization_thread_env()` [L57-L82] — *Cap OMP/ONNX Runtime/BLAS thread pools before onnxruntime, torch, or the*
  - `_setup_windows_dll_directories()` [L85-L195] — *Register native DLL directories (PyTorch, CTranslate2, ONNX Runtime, etc.)*
  - `_safe_tensor_from_numpy(arr)` [L198-L216] — *Safely convert a numpy float32 array into a PyTorch tensor.*

### `worker_story_engine.py` (388 lines)
*worker_story_engine.py - Acoustic & Lexical Story Boundary Detection Engine.*
- **Functions**:
  - `is_real_speech(text)` [L41-L48] — *Return True if text represents actual spoken words rather than music/sound tokens.*
  - `detect_story_boundaries(audio_file, silence_threshold, lead_in_padding, audio_duration, transcript_segments, whisper_model, detection_mode, is_cancelled_fn, progress_callback)` [L51-L388] — *Execute acoustic and lexical story boundary detection on an audio file.*


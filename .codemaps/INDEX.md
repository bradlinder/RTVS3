# Repository Symbol Index & API Map

> Generated: 2026-10-29 15:04:30 | Total Files: 154
> Use `python scripts/generate_symbol_index.py --outline <file>` for exact line numbers.

## Modules Overview

| Module | Lines | Summary | Primary Classes / Functions |
| :--- | :---: | :--- | :--- |
| `RadioTVSegmenter.py` | 646 | Radio & TV Segmenter — v3.9.52-beta | `MainWindow`, `main()` |
| `audio_normalization.py` | 541 | Radio & TV Story Segmenter — Audio Loudness Probing & Nor... | `LoudnessReport`, `AudioLoudnessProbeWorker`, `parse_ebur128_summary()`, `probe_media_duration_seconds()` *(+3 more)* |
| `background_workers.py` | 1015 | Radio & TV Story Segmenter — Background Worker Threads & ... | `StoryAutoDetectWorker`, `WaveformWorker`, `VideoThumbnailWorker`, `get_waveform_peak_cache_path()` *(+6 more)* |
| `backup_manager.py` | 622 | Unified State Serialization, Local, and Google Drive Clou... | `compute_data_checksum()`, `serialize_preferences()`, `serialize_keyboard_shortcuts()`, `serialize_glossary()` *(+7 more)* |
| `batch_dialog.py` | 702 | Radio & TV Story Segmenter — Batch Processing Dialog & Dr... | `BatchFileListWidget`, `BatchProcessingDialog` |
| `benchmark.py` | 216 | Radio & TV Story Segmenter — Performance & Speed Benchmar... | `run_cli_benchmark()`, `main()` |
| `benchmark_dialog.py` | 674 | benchmark_dialog.py - PySide6 Graphical Benchmark Dialog ... | `create_benchmark_dialog()` |
| `benchmark_engine.py` | 903 | benchmark_engine.py - Core High-Precision Performance Ben... | `BenchmarkEngine` |
| `benchmark_models.py` | 457 | benchmark_models.py - Benchmark Data Models, Audio Genera... | `BenchmarkMetric`, `ProcessingEstimates`, `get_app_data_dir()`, `get_candidate_sample_audio_paths()` *(+9 more)* |
| `bootstrap.py` | 385 | Install-safe startup environment configuration for Radio ... | `NullWriter`, `init_null_streams_and_hf_env()`, `patch_av_open()`, `app_data_dir()` *(+7 more)* |
| `build_installer.py` | 1079 | Build the installable Radio & TV Segmenter application wi... | `exe_name()`, `find_tool()`, `check_cpu_only_torch()`, `torch_windows_binary_flags()` *(+8 more)* |
| `bump_version.py` | 504 | bump_version.py — Automated Version Synchronization Engine | `normalize_version()`, `get_current_version()`, `compute_bump()`, `detect_modified_plugins()` *(+3 more)* |
| `cache_manager.py` | 685 | Radio & TV Segmenter — Cache management, disk usage scann... | `ClearCacheDialog`, `register_active_thumbnail_dir()`, `unregister_active_thumbnail_dir()`, `get_active_thumbnail_dirs()` *(+3 more)* |
| `comment_widgets.py` | 350 | comment_widgets.py - Range-Anchored Comments Panel & Comm... | `CommentEditorDialog`, `CommentCardWidget`, `CommentsPanel` |
| `core_utils.py` | 666 | Radio & TV Segmenter — Core filesystem, path, timing, and... | `safe_process_events()`, `get_active_theme_mode()`, `apply_window_titlebar_theme()`, `make_dialog_maximizable()` *(+22 more)* |
| `diagnostic_batch_tests.py` | 1067 | Diagnostic test bench suite component. | `DiagnosticBatchTestsMixin` |
| `diagnostic_cloud_and_system_tests.py` | 1267 | Diagnostic test bench suite component. | `DiagnosticCloudAndSystemTestsMixin` |
| `diagnostic_core_tests.py` | 826 | Diagnostic test bench suite component. | `DiagnosticCoreTestsMixin` |
| `diagnostic_dialog.py` | 288 | PySide6 Graphical Test Bench Dialog for Radio & TV Story ... | `create_diagnostic_dialog()` |
| `diagnostic_export_tests.py` | 1699 | Diagnostic test bench suite component. | `DiagnosticExportTestsMixin` |
| `diagnostic_helpers.py` | 151 | Helper fixtures, module resolvers, and DiagnosticItem for... | `DiagnosticItem`, `generate_synthetic_wav()` |
| `diagnostic_loudness_tests.py` | 382 | Radio & TV Story Segmenter — Diagnostic Loudness Normaliz... | `DiagnosticLoudnessTestsMixin` |
| `diagnostic_selector.py` | 191 | Smart Diagnostic Test Selector for Radio & TV Story Segme... | `get_modified_files()`, `has_git_changes()`, `detect_changed_tokens()`, `select_diagnostic_items()` |
| `dialogs.py` | 433 | Radio & TV Story Segmenter — Audio Loudness Normalization... | `AudioLoudnessNormalizationDialog` |
| `diarization_processing.py` | 769 | Speaker diarization process management for Radio & TV Sto... | `DiarizationProcessingMixin` |
| `export/__init__.py` | 67 | Export package for Radio & TV Story Segmenter. | - |
| `export/audio.py` | 287 | Radio & TV Story Segmenter — Broadcast Audio Rendering & ... | `build_audio_fade_filter()`, `export_audio_track()`, `extract_audio_clip()` |
| `export/daw.py` | 37 | DAW and NLE timeline interchange formatters for Radio & T... | - |
| `export/dialog.py` | 1441 | Unified Export Dialog for Radio & TV Story Segmenter. | `UnifiedExportDialog` |
| `export/docx.py` | 541 | Word (.docx) export formatter for Radio & TV Story Segmen... | `inject_native_comments_to_docx()`, `create_story_docx()` |
| `export/pdf.py` | 369 | PDF export formatter for Radio & TV Story Segmenter. | `TranscriptPdfWriter` |
| `export/reorder_dialog.py` | 255 | export/reorder_dialog.py — Dialog for customizing the dis... | `ReorderExportDestinationsDialog`, `get_export_destinations_order()`, `save_export_destinations_order()` |
| `export/subtitles.py` | 222 | Subtitle and timeline formatters for Radio & TV Story Seg... | `format_subtitle_timestamp()`, `format_srt_timestamp()`, `format_vtt_timestamp()`, `format_cue_timestamp()` *(+9 more)* |
| `export/timeline.py` | 801 | Multi-Platform Timeline and DAW Interchange Engine for Ra... | `reaper_color_from_hex()`, `format_edl_timestamp()`, `build_timeline_clips()`, `generate_reaper_project()` *(+8 more)* |
| `export_dialogs.py` | 415 | Radio & TV Story Segmenter — Export Dialogs & Scope Selec... | `ExportDialogsMixin`, `show_export_completion_dialog()` |
| `export_documents.py` | 776 | Radio & TV Story Segmenter — Document, Transcript & Timel... | `ExportDocumentsMixin` |
| `export_media_clipper.py` | 337 | Radio & TV Story Segmenter — Media Clipper & Audio Track ... | `ExportMediaClipperMixin` |
| `export_story_pipeline.py` | 964 | Radio & TV Story Segmenter — Story & Full Episode Export ... | `ExportStoryPipelineMixin` |
| `gpu_acceleration.py` | 276 | Radio & TV Segmenter v1.1.1 — optional GPU acceleration r... | `GpuAccelerationInstallWorker`, `GpuAccelerationMixin` |
| `id3_editor.py` | 704 | ID3 Tag Editor module for Radio & TV Segmenter. | `ID3TagEditorDialog`, `read_id3_tags()`, `write_id3_tags()` |
| `installer/pyinstaller/torch_dll_hook.py` | 70 | PyInstaller runtime hook for Windows ML/native DLL resolu... | - |
| `media_batch.py` | 1848 | Radio & TV Segmenter v1.1.1 — media batch responsibilities. | `MediaBatchMixin` |
| `model_install_workers.py` | 189 | Radio & TV Segmenter — Model Download and Installation Ba... | `WhisperModelInstallWorker`, `DiarizationModelInstallWorker`, `get_diarization_model_dir()`, `is_diarization_model_available()` |
| `model_management.py` | 989 | Radio & TV Segmenter v1.1.1 — model management responsibi... | `_DummyTranslationWorker`, `ModelManagementMixin` |
| `playback_controller.py` | 581 | Radio & TV Story Segmenter — Media Player Transport & Pla... | `PlaybackControllerMixin` |
| `playback_preferences.py` | 650 | Radio & TV Story Segmenter — Playback Preferences & Appli... | `PlaybackPreferencesMixin` |
| `plugin_base.py` | 205 | Radio & TV Segmenter — Plugin Base Interfaces and Manifest. | `PluginManifest`, `BasePlugin`, `ExportDestination` |
| `plugin_dialogs.py` | 447 | GitHub plugins dialogs, batch download workers, and Plugi... | `GitHubPluginsWorker`, `GitHubDownloadWorker`, `GitHubBatchDownloadWorker`, `GitHubPluginsDialog` *(+1 more)* |
| `plugins/__init__.py` | 6 | Radio & TV Segmenter — Plugin Architecture Package. | - |
| `plugins/base.py` | 6 | Radio & TV Segmenter — Plugin Base Interfaces and Manifes... | - |
| `plugins/github_dialog.py` | 580 | GitHub plugins browser and installer dialog with multi-se... | `GitHubPluginsDialog` |
| `plugins/installer_workers.py` | 293 | Background QThread workers for querying, downloading, and... | `GitHubPluginsWorker`, `GitHubDownloadWorker`, `GitHubBatchDownloadWorker`, `get_official_plugins_catalog()` |
| `plugins/manager.py` | 657 | Radio & TV Segmenter — Plugin Manager and Discovery Engine. | `PluginManager`, `parse_plugin_version_tuple()`, `is_newer_plugin_version()` |
| `plugins/manager_dialog.py` | 529 | Plugin and Add-On Manager Dialog for inspecting, enabling... | `PluginManagerDialog` |
| `plugins/translation/__init__.py` | 9 | Language Translation Plugin for Radio & TV Segmenter. | - |
| `plugins/translation/plugin.py` | 58 | Language Translation Plugin for Radio & TV Segmenter. | `Plugin` |
| `plugins/translation/runtime_entry.py` | 49 | CLI entry point for the isolated translation runtime. | `emit()`, `main()` |
| `plugins/translation/support.py` | 176 | Small dependency-light helpers shared by the translation ... | `configure_ssl_certificates()`, `get_app_data_dir()`, `get_legacy_models_storage_dirs()`, `get_models_storage_dir()` *(+2 more)* |
| `plugins/translation/worker.py` | 678 | Translation plugin worker. | `TranslationWorker` |
| `plugins/version_utils.py` | 30 | Version parsing and semantic comparison utilities for the... | `parse_plugin_version_tuple()`, `is_newer_plugin_version()` |
| `plugins/wordpress/__init__.py` | 6 | WordPress Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/wordpress/castos.py` | 722 | Seriously Simple Podcasting (Castos) integration for Word... | `format_castos_duration()`, `build_castos_post_meta()`, `copy_podcast_meta()`, `fetch_castos_feeds()` *(+5 more)* |
| `plugins/wordpress/client.py` | 1887 | WordPress Plugin — Client, Credential Storage, and Upload... | `WordPressClient`, `WordPressSettingsDialog`, `WordPressPreferencesPage`, `format_rich_text_to_html()` *(+6 more)* |
| `plugins/wordpress/export_destination.py` | 631 | WordPress Export Destination for UnifiedExportDialog. | `WordPressExportDestination`, `WordPressPostMetadataDialog` |
| `plugins/wordpress/plugin.py` | 897 | WordPress Publisher Plugin for Radio & TV Segmenter. | `WordPressPublishDialog`, `WordPressPublishWorker`, `WordPressStoryMetadataWidget`, `Plugin` *(+1 more)* |
| `plugins/wordpress/wordpress_dialog.py` | 886 | WordPress Export Tab Widget and Post Metadata Dialog. | `WordPressExportTabWidget`, `WordPressPostMetadataDialog`, `generate_wp_excerpt()`, `capture_video_frame()` |
| `plugins/wordpress/wp_post_builder.py` | 287 | Post item builder, transcript slicing, and video frame ex... | `capture_video_frame()`, `get_primary_text_slice()`, `build_wp_post_items()` |
| `plugins/wordpress/wp_tab_widget.py` | 995 | WordPress export tab configuration widget and preview con... | `WordPressExportTabWidget` |
| `plugins/wordpress/wp_ui_builder.py` | 731 | UI layout construction and widget setup for WordPressExpo... | `setup_wp_tab_ui()` |
| `plugins/youtube/__init__.py` | 9 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/youtube/export_destination.py` | 594 | YouTube Export Destination for UnifiedExportDialog with Z... | `YouTubeExportTabWidget`, `YouTubeExportDestination`, `capture_video_frame()` |
| `plugins/youtube/guide_dialog.py` | 147 | Interactive Assisted Upload Guide Dialog for YouTube Studio. | `YouTubeAssistedUploadGuideDialog` |
| `plugins/youtube/plugin.py` | 224 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | `YouTubeSettingsDialog`, `Plugin`, `capture_video_frame()` |
| `preferences_dialog.py` | 723 | Radio & TV Story Segmenter — Preferences Modal Dialog. | `PreferencesDialogMixin` |
| `preferences_reset.py` | 642 | Radio & TV Story Segmenter — Preferences Reset & Factory ... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_reset_dialog.py` | 621 | Radio & TV Segmenter — Preferences reset and factory defa... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_tabs_core.py` | 623 | Radio & TV Story Segmenter — Preferences Modal Core Tab B... | `build_general_tab()`, `build_shortcuts_tab()`, `build_audio_hardware_tab()`, `build_updates_tab()` *(+2 more)* |
| `preferences_tabs_media.py` | 650 | Radio & TV Story Segmenter — Preferences Modal Media & Wo... | `build_playback_timeline_tab()`, `build_detection_tab()`, `build_batch_tab()`, `build_cleanup_tab()` *(+1 more)* |
| `preview_manager.py` | 270 | AI Studio Web Preview Manager for Radio & TV Story Segmen... | `get_project_version()`, `restore_preview()`, `sync_version()`, `main()` |
| `process_lifecycle.py` | 191 | Radio & TV Segmenter — Subprocess tracking and OS-level j... | `init_child_process_job_isolation()`, `bind_subprocess_to_job()`, `register_process()`, `unregister_process()` *(+2 more)* |
| `processing.py` | 1216 | Radio & TV Segmenter v3.3.29 — processing responsibilities. | `RuntimeSetupWorker`, `ProcessingMixin` |
| `project_export.py` | 446 | Radio & TV Story Segmenter — Unified Project & Media Expo... | `ProjectExportMixin` |
| `project_lifecycle.py` | 992 | Radio & TV Story Segmenter — Project Lifecycle & Persiste... | `ProjectLifecycleMixin`, `ProjectDataPurgeDialog` |
| `project_serialization.py` | 126 | Radio & TV Segmenter — Project file serialization and saf... | `sanitize_project_data_for_storage()`, `serialize_rtvs_project()`, `deserialize_rtvs_project()`, `read_rtvs_project_file()` *(+1 more)* |
| `project_state_mixin.py` | 352 | Radio & TV Story Segmenter — Project State, Undo/Redo & P... | `ProjectStateMixin` |
| `prs_shared.py` | 1491 |  | `ProjectMetadataDict`, `ResizableTextEdit`, `CollapsibleSection`, `ExportDialog` *(+8 more)* |
| `qt_compat.py` | 768 | Radio & TV Segmenter — Headless Qt / PySide6 Compatibilit... | `MockClassMeta`, `DynamicMock`, `MockModule`, `_DummyQtMeta` *(+16 more)* |
| `radio_tv_story_segmenter_worker.py` | 226 | Radio & TV Story Segmenter — AI Background Subprocess Wor... | `main()` |
| `roadmap_manager.py` | 259 | roadmap_manager.py — Automated Roadmap & N-1 Sliding-Wind... | `RoadmapManager`, `get_current_app_version()`, `main()` |
| `runtime_manager.py` | 1037 |  | `RuntimeManager`, `register_process()`, `unregister_process()`, `kill_all_subprocesses()` *(+1 more)* |
| `scripts/generate_pyi_stubs.py` | 214 | generate_pyi_stubs.py — Automated Interface Typing Stub (... | `StubTransformer`, `generate_stub_source()`, `get_large_modules()`, `generate_stub_file()` *(+1 more)* |
| `scripts/generate_symbol_index.py` | 380 | generate_symbol_index.py — Fast AST Symbol Indexer & Repo... | `parse_function_signature()`, `analyze_file()`, `scan_repository()`, `generate_index_markdown()` *(+4 more)* |
| `scripts/log_summary.py` | 150 | log_summary.py — Compact Error & Exception Extraction Engine | `is_project_frame()`, `extract_log_summary()`, `main()` |
| `scripts/modular_audit.py` | 570 | scripts/modular_audit.py — AST Decomposition Suggester & ... | `ModuleStructure`, `DecompositionPlan`, `scan_repository()`, `print_audit_report()` *(+2 more)* |
| `shortcuts/__init__.py` | 26 | shortcuts package — Modular Keyboard Shortcuts Management... | - |
| `shortcuts/definitions.py` | 22 | shortcuts/definitions.py — Shortcut definitions and schem... | - |
| `shortcuts/dialogs.py` | 623 | shortcuts/dialogs.py — Preferences page for keyboard shor... | `KeyboardShortcutsPage` |
| `shortcuts/manager.py` | 208 | shortcuts/manager.py — Core ShortcutsManager coordinator ... | `ShortcutsManager` |
| `shortcuts/schema.py` | 858 | shortcuts/schema.py — Shortcut definitions, dataclass mod... | `ShortcutDef`, `get_platform_default()`, `format_sequence_display()`, `normalize_sequence_string()` |
| `shortcuts/widgets.py` | 151 | shortcuts/widgets.py — Interactive Key Sequence Recorder ... | `KeySequenceRecorderEdit` |
| `shortcuts_manager.py` | 30 | Shortcuts Manager for Radio & TV Story Segmenter (Compati... | - |
| `snapshot_manager.py` | 276 | Snapshot Manager for Radio & TV Story Segmenter | `load_manifest()`, `save_manifest()`, `get_current_project_version()`, `ensure_git_repo()` *(+4 more)* |
| `speaker_dialog_refinement_mixin.py` | 546 | Radio & TV Story Segmenter — Speaker Dialog Refinement & ... | `SpeakerDialogRefinementMixin` |
| `speaker_dialogs.py` | 782 | speaker_dialogs.py — Dialogs for speaker renaming, turn a... | `ChangeSpeakerDialog`, `SpeakerNameDelegate`, `SpeakerManagerDialog` |
| `speaker_editing_mixin.py` | 580 | Radio & TV Story Segmenter — Speaker Label, Renaming & Se... | `SpeakerEditingMixin` |
| `speaker_identity.py` | 260 | Radio & TV Segmenter | `VoiceMatch`, `cosine_similarity()`, `normalize_vector()`, `centroid()` *(+3 more)* |
| `speaker_palette.py` | 148 | Accessible adaptive speaker color palette for Radio & TV ... | `SpeakerColor`, `SpeakerColorAssigner`, `get_speaker_index()`, `get_speaker_color()` *(+3 more)* |
| `speaker_profiles.py` | 630 | speaker_profiles.py — Persistent Station Voice Profile Ma... | `StationVoiceProfile`, `StationVoiceProfileStore`, `ManageVoiceProfilesDialog` |
| `story_crud_mixin.py` | 814 | Radio & TV Story Segmenter — Story CRUD & Timeline Select... | `StoryCrudMixin` |
| `story_detection_processing.py` | 206 | Story boundary detection processing mixin for Radio & TV ... | `StoryDetectionProcessingMixin` |
| `story_fades_dialog.py` | 213 | story_fades_dialog.py — Dialog for fine-grained audio fad... | `StoryFadesDialog` |
| `story_metadata_dialog.py` | 307 | Radio & TV Story Segmenter — Universal Story & Post Metad... | `StoryMetadataDialog`, `generate_story_excerpt()` |
| `story_model.py` | 262 | Radio & TV Story Segmenter — Story Model, Boundaries & Un... | `Story`, `SetStoriesCommand`, `StoryBoundaryChangeCommand`, `SelectStoriesCommand` *(+3 more)* |
| `story_widgets.py` | 531 | Radio & TV Story Segmenter — Story Sidebar Widgets, Item ... | `FadeCurveVisualSelector`, `StoryFadesChangeCommand`, `SetStoriesCommand`, `StoryBoundaryChangeCommand` *(+3 more)* |
| `sync.py` | 161 | 2-Way Synchronization Engine for Radio & TV Story Segmenter. | `get_current_version()`, `run_cmd()`, `cmd_status()`, `cmd_pull()` *(+2 more)* |
| `terminology.py` | 275 | Model-independent terminology and glossary support. | `parse_glossary()`, `load_glossary()`, `normalize_text()`, `normalize_transcript()` *(+6 more)* |
| `theme_preferences.py` | 596 | Radio & TV Story Segmenter — Theme Preferences & Styling ... | `ThemePreferencesMixin` |
| `theme_qss.py` | 330 | Targeted QSS for the Radio & TV Segmenter visual design s... | - |
| `theme_tokens.py` | 307 | Theme Tokens for Radio & TV Story Segmenter. | `ThemeTokens`, `theme_tokens_for_mode()` |
| `timeline_context_menus.py` | 108 | Context menu builders and event handlers for the timeline... | `show_timeline_context_menu()`, `show_selection_context_menu()` |
| `timeline_overview.py` | 351 | Timeline Resize Handle and Overview Navigation Bar widgets. | `TimelineResizeHandle`, `TimelineOverviewBar` |
| `timeline_overview_widget.py` | 372 | Timeline overview bar, mini-map navigator, and resize han... | `TimelineResizeHandle`, `TimelineOverviewBar` |
| `timeline_painter.py` | 419 | Timeline canvas rendering engine, waveform drawing, and p... | `render_waveform_buffer()`, `paint_timeline_canvas()` |
| `timeline_snap.py` | 119 | Timeline snapping algorithms, edge detection, and collisi... | `snap_time()`, `find_edge_at_pos()`, `find_fade_handle_at_pos()`, `find_story_at_time()` *(+1 more)* |
| `timeline_widgets.py` | 974 | Radio & TV Story Segmenter — Timeline Ruler, Track Views,... | `TimelineCanvas`, `TimelineWidget` |
| `transcript_cleaner.py` | 216 | Radio & TV Segmenter — Transcript cleaning, loop collapsi... | `collapse_repeating_ngrams()`, `strip_hallucination_phrases()`, `trim_trailing_degenerate_tail()`, `scrub_transcript_segments()` *(+1 more)* |
| `transcript_context_menu_mixin.py` | 415 | Radio & TV Story Segmenter — Interactive Transcript Conte... | `TranscriptContextMenuMixin` |
| `transcript_editor.py` | 862 | transcript_editor.py - Interactive Transcript Editor & Vi... | `InteractiveTranscriptEdit` |
| `transcript_editor_dialogs.py` | 231 | transcript_editor_dialogs.py - Dialog and floating toolba... | `FindReplaceDialog`, `TranscriptSelectionBubble` |
| `transcript_formatting_mixin.py` | 340 | Radio & TV Story Segmenter — Interactive Transcript Forma... | `TranscriptFormattingMixin` |
| `transcript_navigation_mixin.py` | 299 | transcript_navigation_mixin.py - Timestamp discovery, car... | `TranscriptNavigationMixin` |
| `transcript_playback_highlight_mixin.py` | 276 | Radio & TV Story Segmenter — Interactive Transcript Playb... | `TranscriptPlaybackHighlightMixin` |
| `transcript_selection_mixin.py` | 420 | transcript_selection_mixin.py - Multi-selection, timeline... | `TranscriptSelectionMixin` |
| `transcript_story.py` | 847 | Radio & TV Segmenter v3.9.52-beta — transcript story resp... | `TranscriptStoryMixin` |
| `transcript_styles.py` | 104 | transcript_styles.py - Transcript view stylesheets and da... | `transcript_text_view_stylesheet()`, `clean_dark_mode_clipboard_html()` |
| `transcript_timeline_sync_mixin.py` | 566 | Radio & TV Story Segmenter — Transcript Timeline & Playba... | `TranscriptTimelineSyncMixin` |
| `transcription_processing.py` | 579 | Transcription background process management for Radio & T... | `TranscriptionProcessingMixin` |
| `translation.py` | 923 | Radio & TV Segmenter — Local Translation Mixin. | `TranslationEnvSetupWorker`, `TranslationMixin` |
| `ui_dialog_launchers.py` | 337 | Dialog launchers and external modal helpers for Radio & T... | `UiDialogLaunchersMixin` |
| `ui_layout.py` | 1060 | Radio & TV Segmenter — UI Layout & Menu Construction Mixin. | `UiLayoutMixin` |
| `ui_menus.py` | 809 | Main application menu bar and action assembly for Radio &... | `PersistentMenu`, `UiMenusMixin` |
| `updater.py` | 1460 | Update manager and GitHub release installer for Radio & T... | `CheckUpdateWorker`, `DownloadUpdateWorker`, `CheckUpdateDialog`, `UpdaterMixin` *(+9 more)* |
| `utils/__init__.py` | 36 | Utility modules for Radio & TV Story Segmenter. | - |
| `utils/constants.py` | 41 | Application constants and environment configuration. | - |
| `utils/time_format.py` | 19 | Time formatting and parsing utilities. | - |
| `voice_profile_dialog.py` | 1006 | voice_profile_dialog.py — Dialog for finding and reassign... | `VoiceProfileMatchDialog` |
| `voice_profile_ops_mixin.py` | 585 | Radio & TV Story Segmenter — Voice Profile Matching & Emb... | `VoiceProfileOpsMixin` |
| `waveform_envelope.py` | 55 | Waveform envelope data structures, downsampling pyramids,... | `WaveformEnvelope`, `build_waveform_pyramid()` |
| `worker_asr_engines.py` | 839 | worker_asr_engines.py - Faster-Whisper, CTranslate2 & She... | `set_emit_callback()`, `get_optimal_transcription_threads()`, `get_app_data_dir_pure()`, `get_models_storage_dir_pure()` *(+4 more)* |
| `worker_clustering.py` | 448 | worker_clustering.py - Acoustic clustering, VAD pause bri... | `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `fast_cluster_ahc()`, `apply_clustering_patches()` *(+2 more)* |
| `worker_diarization_clustering.py` | 297 | worker_diarization_clustering.py - Speaker Clustering, Ce... | `fast_cluster_ahc()`, `apply_clustering_patches()`, `assign_short_segments_to_centroids()` |
| `worker_diarization_engine.py` | 902 | worker_diarization_engine.py - Speaker Diarization, Neura... | `set_emit_callback()`, `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `extract_embeddings_batched()` *(+3 more)* |
| `worker_ipc.py` | 216 | worker_ipc.py - Subprocess IPC protocol, environment setu... | `emit()`, `emit_hello()` |
| `worker_story_engine.py` | 388 | worker_story_engine.py - Acoustic & Lexical Story Boundar... | `is_real_speech()`, `detect_story_boundaries()` |

## Detailed Symbol Catalog

### `RadioTVSegmenter.py` (646 lines)
*Radio & TV Segmenter — v3.9.52-beta*
- **class `MainWindow(ModelManagementMixin, MediaBatchMixin, PlaybackPreferencesMixin, UiLayoutMixin, ProcessingMixin, TranslationMixin, TranscriptStoryMixin, ProjectExportMixin, GpuAccelerationMixin, QMainWindow)`** (lines 160–543):
  *Main application window for Radio & TV Segmenter.*
  - `__init__(self)` [L178-L350]
  - `_setup_shortcuts_and_actions(self)` [L352-L404] — *Register customizable QShortcut and QAction objects on MainWindow.*
  - `handle_external_open_request(self, file_path)` [L406-L431] — *Called when another instance attempts to open a project file in single-instance mode.*
  - `load_persistent_settings(self)` [L433-L500] — *Loads all persistent user preferences from QSettings into MainWindow attributes.*
  - `changeEvent(self, event)` [L502-L509] — *Handle window state changes (e.g. maximize, restore, minimize) safely.*
  - `dragEnterEvent(self, event)` [L511-L518]
  - `dragMoveEvent(self, event)` [L520-L527]
  - `dropEvent(self, event)` [L529-L543]
- **Functions**:
  - `main()` [L546-L642]

### `audio_normalization.py` (541 lines)
*Radio & TV Story Segmenter — Audio Loudness Probing & Normalization Engine.*
- **class `LoudnessReport`** (lines 60–73):
  *Telemetry report representing measured loudness and peak metrics for an audio file.*
  - `to_dict(self)` [L72-L73]
- **class `AudioLoudnessProbeWorker(QThread)`** (lines 301–343):
  *Background worker thread to probe audio loudness without freezing Qt GUI.*
  - `__init__(self, media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout, parent)` [L307-L322]
  - `cancel(self)` [L324-L326] — *Request worker cancellation.*
  - `run(self)` [L328-L343] — *Execute non-blocking probe in background.*
- **Functions**:
  - `_safe_float(val_str, default)` [L76-L91] — *Parse string to float with safe handling for -inf, inf, nan.*
  - `parse_ebur128_summary(stderr_text)` [L94-L124] — *Parse FFmpeg ebur128 filter output to extract I (LUFS), LRA (LU), and Peak (dBTP/dBFS).*
  - `probe_media_duration_seconds(media_path, timeout)` [L127-L156] — *Fast probe of total media duration in seconds via ffprobe.*
  - `probe_media_loudness(media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout)` [L159-L298] — *Measure loudness (LUFS), dynamic range (LRA), and peak (dBTP) of an audio/video file.*
  - `normalize_audio_sidecar(media_path, report, target_lufs, max_true_peak, quiet_threshold_lufs, quiet_threshold_dbfs, timeout)` [L346-L461] — *Non-destructively generate a normalized 16 kHz mono WAV sidecar.*
  - `get_effective_audio_for_processing(media_path, settings_store, project_metadata)` [L464-L541] — *Return the audio path to feed into ASR or diarization.*

### `background_workers.py` (1015 lines)
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
- **class `VideoThumbnailWorker(QObject)`** (lines 945–1004):
  - `__init__(self, media_path, duration, output_dir, count)` [L949-L956]
  - `cancel(self)` [L958-L965]
  - `run(self)` [L967-L1004]
- **Functions**:
  - `get_waveform_peak_cache_path(audio_file, project_file)` [L483-L537] — *Return local project or appdata path for waveform peak binary cache file.*
  - `read_waveform_peak_cache(audio_file, points_per_second, project_file)` [L542-L611] — *Read cached waveform peak envelope from binary cache.*
  - `write_waveform_peak_cache(audio_file, peaks, points_per_second, project_file, levels)` [L613-L651] — *Write waveform peak envelope and multi-resolution mipmapped levels to binary cache with atomic rename.*
  - `invalidate_waveform_peak_cache(audio_file, project_file)` [L654-L674] — *Delete any cached waveform peak binary file for audio_file, including legacy paths.*
  - `get_video_thumbnail_cache_dir(media_file, project_file)` [L832-L871] — *Return the deterministic thumbnail cache directory for a media file, associating with project if available.*
  - `read_video_thumbnail_cache(media_file, duration, project_file)` [L874-L916] — *Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.*
  - `invalidate_video_thumbnail_cache(media_file, project_file)` [L919-L942] — *Delete the thumbnail cache directory for a given media file.*

### `backup_manager.py` (622 lines)
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

### `batch_dialog.py` (702 lines)
*Radio & TV Story Segmenter — Batch Processing Dialog & Droppable File List.*
- **class `BatchFileListWidget(QListWidget)`** (lines 43–149):
  - `__init__(self, parent)` [L46-L53]
  - `dragEnterEvent(self, event)` [L55-L64]
  - `dragMoveEvent(self, event)` [L66-L74]
  - `dragLeaveEvent(self, event)` [L76-L79]
  - `dropEvent(self, event)` [L81-L91]
  - `paintEvent(self, event)` [L93-L149]
- **class `BatchProcessingDialog(QDialog)`** (lines 151–690):
  - `__init__(self, parent)` [L152-L428]
  - `eventFilter(self, watched, event)` [L430-L446]
  - `_load_saved_options(self)` [L448-L508]
  - `save_options_to_settings(self, as_default)` [L510-L544]
  - `reset_options_to_defaults(self)` [L546-L586]
  - `_on_start_clicked(self)` [L588-L590]
  - `dragEnterEvent(self, event)` [L592-L599]
  - `dragMoveEvent(self, event)` [L601-L608]
  - `dropEvent(self, event)` [L610-L618]
  - `add_paths(self, paths)` [L620-L634]
  - `add_files(self)` [L636-L648]
  - `choose_output(self)` [L650-L655]
  - `choose_transcripts_output(self)` [L657-L667]
  - `auto_detect_options(self)` [L669-L690] — *Auto-detect available options based on imported file extensions.*

### `benchmark.py` (216 lines)
*Radio & TV Story Segmenter — Performance & Speed Benchmark Engine.*
- **Public Exports (`__all__`)**: BenchmarkMetric, ProcessingEstimates, get_app_data_dir, get_candidate_sample_audio_paths, find_available_sample_audio, get_sample_audio_target_path, delete_sample_audio_files, download_sample_audio, decode_audio_file_pcm, _get_seed_speech_pcm, generate_benchmark_audio, get_system_hardware_profile, is_translation_plugin_installed, format_duration_estimate, BenchmarkEngine, create_benchmark_dialog, run_cli_benchmark, main
- **Functions**:
  - `run_cli_benchmark(quick, duration_mode, as_json, use_sample, custom_file)` [L70-L156] — *Run performance benchmarks and print formatted terminal report.*
  - `main(argv)` [L159-L212]

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

### `bootstrap.py` (385 lines)
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
  - `ensure_sherpa_onnx_runtime()` [L293-L349] — *Make sure the Parakeet runtime is importable before the GUI starts.*
  - `ensure_keyring_runtime()` [L351-L377] — *Ensure keyring (and pywin32-ctypes on Windows) is installed for secure credential storage.*
  - `check_and_install_core()` [L379-L382] — *Backward-compatible startup dependency check.*

### `build_installer.py` (1079 lines)
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
  - `parse_build_args()` [L546-L621]
  - `package_plugins(app_root, include_wp, include_yt, include_tr)` [L624-L692] — *Package plugins into standalone .zip release artifacts in dist/plugins/*
  - `main()` [L695-L1075]

### `bump_version.py` (504 lines)
*bump_version.py — Automated Version Synchronization Engine*
- **Functions**:
  - `normalize_version(ver)` [L26-L30] — *Normalize version string: strip leading 'v', collapse double dots, trim.*
  - `get_current_version()` [L32-L46] — *Extract active version from core_utils.py or prs_shared.py.*
  - `compute_bump(current_version, bump_type)` [L48-L66] — *Calculate next semantic version (patch, minor, major) preserving any suffix (e.g. -beta, -stable).*
  - `detect_modified_plugins()` [L69-L92] — *Auto-detect plugins with uncommitted changes via git status for Lazy Catch-Up Policy.*
  - `check_all_versions()` [L94-L197] — *Inspect and report the version strings currently set across all files.*
  - `bump_all(new_version, dry_run, plugins)` [L199-L455] — *Execute synchronous version updates across all checklist targets.*
  - `main()` [L457-L501]

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

### `core_utils.py` (666 lines)
*Radio & TV Segmenter — Core filesystem, path, timing, and hash utilities.*
- **Functions**:
  - `safe_process_events()` [L37-L46] — *Safely process pending Qt GUI events only when called from the main GUI thread.*
  - `get_active_theme_mode(default)` [L49-L83] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast') with universal multi-scope resolution.*
  - `_apply_dwm_titlebar_hwnd(hwnd, theme_mode)` [L86-L139] — *Low-level Windows DWM call applying caption and text colors to a window HWND.*
  - `apply_window_titlebar_theme(widget, theme_mode)` [L142-L182] — *Configures Windows DWM title bar caption colors matching active theme mode.*
  - `_deferred_titlebar_theme(widget, theme_mode)` [L185-L199] — *Deferred callback ensuring DWM attributes persist after Qt window frame initialization.*
  - `make_dialog_maximizable(dialog)` [L202-L209] — *Enforce standard OS window maximize and restore title bar controls for resizable dialogs.*
  - `extract_dropped_file_paths(mime_data)` [L212-L263] — *Robustly extracts local filesystem paths from QMimeData supporting URLs, URIs, and raw text.*
  - `_ensure_runtime_bin_on_path()` [L266-L285] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `compute_file_sha256(file_path, chunk_size)` [L291-L297] — *Compute the SHA-256 hexadecimal digest of a file.*
  - `verify_file_sha256(file_path, expected_sha256)` [L300-L308] — *Verify that a file matches the expected SHA-256 checksum (case-insensitive).*
  - `safe_extract_zip(zip_source, dest_dir)` [L311-L329] — *Safely extracts a ZIP archive to a destination directory, guarding against path traversal (Zip Slip).*
  - `safe_extract_tar(tar_source, dest_dir)` [L332-L350] — *Safely extracts a TAR archive to a destination directory, guarding against path traversal.*
  - `safe_replace(src, dest)` [L353-L391] — *Safely and atomically replace dest with src, handling file locks, permissions,*
  - `get_github_repo()` [L394-L411] — *Return the configured GitHub repository owner/repo string.*
  - `get_update_channel()` [L414-L429] — *Return the configured software update release channel: 'stable' or 'beta'.*
  - `get_app_data_dir()` [L432-L447] — *Return the per-user writable application-data directory.*
  - `get_models_storage_dir()` [L450-L468] — *Return the directory configured for storing downloaded models.*
  - `set_models_storage_dir(new_path)` [L471-L492] — *Set and persist a custom models storage directory.*
  - `get_bundled_runtime_dir()` [L495-L507] — *Locate the installed/bundled runtime resource directory.*
  - `find_bundled_executable(name)` [L510-L532] — *Find a bundled executable first, then fall back to PATH and common macOS locations.*
  - `ffmpeg_path()` [L535-L536]
  - `ffprobe_path()` [L539-L540]
  - `format_byte_size(num_bytes)` [L543-L566] — *Format byte quantities into human-readable strings.*
  - `format_time(seconds, include_millis)` [L569-L586]
  - `parse_time(value)` [L589-L605]
  - `safe_filename(text)` [L608-L624]
  - `is_sentence_end(text)` [L627-L628]
  - `calculate_fade_curve_factor(u, fcurve)` [L631-L642] — *Calculate normalized fade-in multiplier (0.0 to 1.0) given progress `u` in [0, 1].*
  - `calculate_fade_out_factor(u, fcurve)` [L645-L665] — *Calculate normalized fade-out multiplier (1.0 to 0.0) given progress `u` from 0.0 (fade start) to 1.0 (silence).*

### `diagnostic_batch_tests.py` (1067 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticBatchTestsMixin`** (lines 26–1066):
  - `_test_batch_unified_transcripts_directory_export(self, item)` [L27-L200]
  - `_test_batch_drag_and_drop_ingestion_and_event_handling(self, item)` [L202-L311]
  - `_test_unified_export_destinations_and_youtube_auth_integrity(self, item)` [L313-L383]
  - `_test_pdf_transcript_export_and_bold_speaker_labels(self, item)` [L385-L440]
  - `_test_fade_curve_tables_and_auditioning_state(self, item)` [L442-L523]
  - `_test_translation_routing_and_key_priority_unit_test(self, item)` [L525-L638]
  - `_test_symmetrical_translation_editing_state_test(self, item)` [L640-L721]
  - `_test_interactive_change_speaker_dialogue_flow_test(self, item)` [L723-L788]
  - `_test_story_boundary_validation_and_overlap_test(self, item)` [L790-L867]
  - `_test_audio_subtitle_sync_drift_test(self, item)` [L869-L913]
  - `_test_interactive_transcript_editing_and_split_join_unit_tests(self, item)` [L915-L1022]
  - `_test_exporter_structure_invariant_tests(self, item)` [L1024-L1066]

### `diagnostic_cloud_and_system_tests.py` (1267 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticCloudAndSystemTestsMixin`** (lines 26–1265):
  - `_test_plugin_interface_sandbox_testing(self, item)` [L27-L105]
  - `_test_project_file_integrity_and_portable_path_resolution(self, item)` [L107-L177]
  - `_test_acoustic_voice_profile_matcher(self, item)` [L179-L441]
  - `_test_windows_detached_update_helper_architecture(self, item)` [L443-L473] — *Validates update helper architecture: helper script generation, exit polling, and logging.*
  - `_test_temporary_cache_management_and_storage_inspection(self, item)` [L475-L574] — *Validates cache usage stats calculation, preview categorization, and cache purging.*
  - `_test_youtube_data_api_and_direct_video_upload_engine(self, item)` [L576-L654] — *Validates YouTube Zero-Auth manual export packaging (MP4, thumbnail, SRT, metadata .txt with chapters & speakers).*
  - `_test_multiprocessing_freeze_support_and_spawn_intercept(self, item)` [L656-L677] — *Validates that frozen process spawn intercepts -c invocations from resource_tracker and multiprocessing.*
  - `_resolve_worker_cmd(self)` [L679-L693] — *Resolves the executable and arguments to launch the AI background worker.*
  - `_test_ai_worker_subprocess_execution_and_ipc_handshake(self, item)` [L695-L761] — *Spawns the AI worker binary in an isolated subprocess, verifying IPC hello handshake and self-test.*
  - `_test_frozen_subprocess_multiprocessing_spawn_protocol(self, item)` [L763-L801] — *Spawns the AI worker executable with Python -c to verify multiprocessing resource tracker interception.*
  - `_test_comprehensive_local_and_cloud_backup_and_restore_engine(self, item)` [L803-L915] — *Validates state serialization, SHA-256 verification, local backup roundtrip, and cloud payload integrity.*
  - `_test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting(self, item)` [L917-L970] — *Validates Option C muted low-contrast silver/fog palette and dark-mode clipboard rich styling.*
  - `_test_windows_ci_build_and_packaging_optimization_invariants(self, item)` [L972-L1004] — *Validates Inno Setup compression parameters, Stage 3 PyInstaller optimizations, and CI settings.*
  - `_test_roadmap_n_1_sliding_window_and_status_integrity(self, item)` [L1006-L1025] — *Validates roadmap.txt N-1 sliding window retention, status indicator syntax, and version sync.*
  - `_test_source_file_modularity_and_1000_line_budget_invariant(self, item)` [L1027-L1096] — *Validates that recently decomposed modules adhere to the 1,000-line modular budget,*
  - `_test_station_voice_profiles_store_and_matching_engine(self, item)` [L1098-L1213] — *Validates StationVoiceProfileStore persistence, vector normalization, profile addition, matching logic, and JSON export/import.*
  - `_test_multi_tier_mipmapped_waveform_peak_cache_serialization(self, item)` [L1215-L1252] — *Validates Version 2 .peaks binary cache read/write with 4x/16x/64x LOD pyramid levels and transparent Version 1 upgrade.*
  - `_test_speed_listening_proofreading_rate_and_context_controls(self, item)` [L1254-L1265] — *Validates playback speed rates (0.75x to 2.0x), WSOLA pitch preservation parameters, and proofreading pre-roll configuration.*

### `diagnostic_core_tests.py` (826 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticCoreTestsMixin`** (lines 26–825):
  - `_test_time_parsing_and_formatting(self, item)` [L27-L65]
  - `_test_project_serialization_round_trip(self, item)` [L67-L95]
  - `_test_waveform_peak_cache_generator(self, item)` [L97-L122]
  - `_test_process_lifecycle_and_subprocess_lock(self, item)` [L124-L130]
  - `_test_subrip_srt_timestamp_formatting(self, item)` [L132-L142]
  - `_test_webvtt_vtt_formatting(self, item)` [L144-L152]
  - `_test_red_book_cue_sheet_generation(self, item)` [L154-L170]
  - `_test_youtube_chapter_markers(self, item)` [L172-L188]
  - `_test_cockos_reaper_project_rpp_generator(self, item)` [L190-L218]
  - `_test_magix_samplitude_edl_v1_5_export(self, item)` [L220-L249]
  - `_test_pytorch_and_torch_native_extensions(self, item)` [L251-L260]
  - `_test_ctranslate2_acceleration_engine(self, item)` [L262-L271]
  - `_test_sherpa_onnx_and_onnx_runtime_engine(self, item)` [L273-L282]
  - `_test_directml_and_gpu_device_enumeration(self, item)` [L284-L308]
  - `_test_hugging_face_and_cdn_connectivity(self, item)` [L310-L327]
  - `_test_model_directory_storage_and_permissions(self, item)` [L329-L339]
  - `_test_safe_archive_extraction_sandbox(self, item)` [L341-L361]
  - `_test_story_boundary_detection_pipeline(self, item)` [L363-L394]
  - `_test_music_vs_voice_mode_filtering(self, item)` [L396-L408]
  - `_test_silero_neural_vad_initialization(self, item)` [L410-L418]
  - `_test_wespeaker_diarization_architecture(self, item)` [L420-L427]
  - `_test_translation_plugin_architecture_invariants(self, item)` [L429-L441]
  - `_test_speaker_reassignment_contiguous_turn_logic(self, item)` [L443-L495]
  - `_test_daw_timeline_interchange_and_gap_handling(self, item)` [L497-L613]
  - `_test_quick_sample_audio_preview_and_speaker_manager_dialog_invariants(self, item)` [L615-L825]

### `diagnostic_dialog.py` (288 lines)
*PySide6 Graphical Test Bench Dialog for Radio & TV Story Segmenter.*
- **Functions**:
  - `create_diagnostic_dialog(parent, include_dev_tests)` [L16-L288] — *Builds the Diagnostic Test Bench Qt Dialog.*

### `diagnostic_export_tests.py` (1699 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticExportTestsMixin`** (lines 26–1698):
  - `_test_wordpress_export_scope_post_builder(self, item)` [L27-L202]
  - `_test_wordpress_export_content_and_transcript_formatter(self, item)` [L204-L415]
  - `_test_multi_format_line_break_and_paragraph_parity(self, item)` [L417-L522]
  - `_test_wordpress_multi_story_upload_and_ui_pluralization(self, item)` [L524-L748]
  - `_test_gutenberg_html_structural_hygiene_audit(self, item)` [L750-L786]
  - `_test_export_scope_delta_and_gap_integrity_audit(self, item)` [L788-L839]
  - `_test_export_destination_interface_contract_verification(self, item)` [L841-L860]
  - `_test_multi_story_media_payload_disambiguation_test(self, item)` [L862-L900]
  - `_test_wordpress_audio_inclusion_toggle_and_error_resilience(self, item)` [L902-L1228]
  - `_test_wordpress_castos_podcast_integration(self, item)` [L1230-L1458]
  - `_test_multi_scope_story_and_full_episode_export_pipeline(self, item)` [L1460-L1541]
  - `_test_audio_export_non_blocking_and_cancellation_pipeline(self, item)` [L1543-L1653]
  - `_test_modal_dialog_maximizable_import_integrity(self, item)` [L1655-L1698]

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

### `diagnostic_loudness_tests.py` (382 lines)
*Radio & TV Story Segmenter — Diagnostic Loudness Normalization & Auto-Boost Test Suite.*
- **class `DiagnosticLoudnessTestsMixin`** (lines 16–381):
  *Diagnostic tests for Smart Hybrid Audio Loudness Probing & Normalization.*
  - `_test_smart_hybrid_audio_loudness_probing(self, item)` [L19-L87] — *Validates fast multi-window EBU R128 loudness & peak probing across synthetic test media.*
  - `_test_two_tier_hybrid_audio_loudness_normalization(self, item)` [L89-L183] — *Validates conditional bypass, Tier 1 linear gain + limiter, Tier 2 leveler, and integration.*
  - `_test_audio_loudness_preferences_and_manual_normalization_dialog(self, item)` [L185-L381] — *Validates Preferences persistence and manual normalization dialog telemetry.*

### `diagnostic_selector.py` (191 lines)
*Smart Diagnostic Test Selector for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_modified_files(root_dir)` [L29-L56] — *Return relative paths of modified or uncommitted files via git status.*
  - `has_git_changes(root_dir)` [L59-L61] — *Return True if there are modified or uncommitted python or plugin files in git.*
  - `detect_changed_tokens(root_dir)` [L64-L136] — *Return a set of lowercase module stems and plugin names from the most recently edited files.*
  - `select_diagnostic_items(engine, items, filter_expr, changed_only)` [L139-L191] — *Filter diagnostic items by explicit `--filter` keywords and/or `--changed` git diff analysis.*

### `dialogs.py` (433 lines)
*Radio & TV Story Segmenter — Audio Loudness Normalization & Telemetry Dialog.*
- **Public Exports (`__all__`)**: AudioLoudnessNormalizationDialog
- **class `AudioLoudnessNormalizationDialog(QDialog)`** (lines 41–433):
  *Dedicated modal dialog for inspecting media loudness metrics and manually normalizing.*
  - `__init__(self, parent, auto_probe)` [L44-L56]
  - `_stop_probe_worker(self)` [L58-L76]
  - `closeEvent(self, event)` [L78-L80]
  - `reject(self)` [L82-L84]
  - `accept(self)` [L86-L88]
  - `_build_ui(self)` [L90-L184]
  - `_load_current_data(self)` [L186-L237]
  - `_on_standard_changed(self, index)` [L239-L244]
  - `reanalyze(self)` [L246-L270]
  - `_on_probe_finished(self, report)` [L272-L277]
  - `_on_probe_error(self, err_msg)` [L279-L283]
  - `_display_report(self, report)` [L285-L311]
  - `_update_gain_preview(self)` [L313-L334]
  - `apply_normalization(self)` [L336-L409]
  - `reset_to_original(self)` [L411-L433]

### `diarization_processing.py` (769 lines)
*Speaker diarization process management for Radio & TV Story Segmenter.*
- **class `DiarizationProcessingMixin`** (lines 24–769):
  - `on_diarization_process_error(self, error)` [L25-L79] — *Handles QProcess execution errors for the diarization process.*
  - `start_diarization(self)` [L81-L278]
  - `on_diarization_output(self, force_flush)` [L280-L383]
  - `on_diarization_stderr(self)` [L385-L404] — *Route the worker's stderr straight to the log, separate from the*
  - `on_diarization_process_finished(self, exit_code, exit_status)` [L406-L439]
  - `cleanup_diarization_process(self)` [L441-L475]
  - `diarization_progress(self, message, percent)` [L477-L478]
  - `diarization_finished(self, result)` [L480-L519]
  - `_apply_diarization_result(self, result)` [L521-L641]
  - `diarization_error(self, message)` [L643-L689]
  - `_diar_segments_cache_key(self)` [L692-L696]
  - `_ensure_diar_speaker_index(self)` [L698-L728]
  - `speaker_at_time(self, start, end)` [L730-L763]
  - `get_effective_speaker_name(self, seg_idx, segment)` [L765-L769]

### `export/__init__.py` (67 lines)
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

### `export/dialog.py` (1441 lines)
*Unified Export Dialog for Radio & TV Story Segmenter.*
- **class `UnifiedExportDialog(QDialog)`** (lines 61–1441):
  *Unified Export Center supporting Local Files and dynamic plugin destinations.*
  - `__init__(self, main_window, initial_scope, initial_dest, parent)` [L64-L234]
  - `showEvent(self, event)` [L236-L238]
  - `_build_destinations_layout(self)` [L240-L385] — *Construct destination radio buttons in customized user order.*
  - `_on_reorder_destinations(self)` [L387-L406] — *Open reorder dialog and rebuild layout on change.*
  - `_create_local_page(self)` [L408-L766]
  - `_on_location_radio_toggled(self)` [L768-L771]
  - `_browse_custom_export_location(self)` [L773-L778]
  - `_create_timeline_page(self)` [L780-L942]
  - `_on_timeline_location_radio_toggled(self)` [L944-L947]
  - `_browse_custom_timeline_location(self)` [L949-L954]
  - `_toggle_all_sections(self)` [L956-L970]
  - `_update_export_button_label(self)` [L972-L985]
  - `_on_dest_changed(self)` [L987-L995]
  - `_on_scope_changed(self)` [L997-L1008]
  - `_open_id3_editor(self)` [L1010-L1020] — *Open the ID3 Tag Editor for MP3 files.*
  - `_copy_youtube_chapters(self)` [L1022-L1038]
  - `_load_saved_options(self)` [L1040-L1120]
  - `save_options_to_settings(self, as_default)` [L1122-L1173]
  - `_handle_accept(self)` [L1175-L1243]
  - `get_result(self)` [L1245-L1349]
  - `_persist_plugin_draft_states(self)` [L1351-L1359] — *Persist any unsaved plugin destination edits (such as WordPress post drafts) back to the project.*
  - `done(self, r)` [L1361-L1363]
  - `toggle_float_mode(self, pinned)` [L1365-L1381] — *Toggle whether the non-modal floating window stays pinned on top of other windows.*
  - `set_scope_and_destination(self, scope, dest_id)` [L1383-L1394] — *Update export scope and active destination tab on an open modeless export window.*
  - `refresh_from_main_window(self)` [L1396-L1418] — *Synchronize post items, excerpts, and story lists from the main window without losing draft edits.*
  - `_toggle_maximize(self)` [L1420-L1428]
  - `changeEvent(self, event)` [L1430-L1441]

### `export/docx.py` (541 lines)
*Word (.docx) export formatter for Radio & TV Story Segmenter.*
- **Functions**:
  - `_add_formatted_text_to_paragraph(p, text, words, block_fmt, include_highlights)` [L46-L127] — *Applies word-level or block-level rich text formatting (bold, italic, underline, strike, highlight) to DOCX runs.*
  - `inject_native_comments_to_docx(docx_bytes, comments_map, author, initials)` [L130-L376] — *Injects native OpenXML comment structures into a .docx ZIP archive.*
  - `create_story_docx(title, blocks, output_path, media_name, start_time, end_time, include_speakers, include_timestamps, include_milliseconds, include_comments, include_highlights, lang_code, source_segments, color_speakers)` [L379-L540] — *Creates a formatted Word (.docx) document with native OpenXML comments from story blocks and metadata.*

### `export/pdf.py` (369 lines)
*PDF export formatter for Radio & TV Story Segmenter.*
- **class `TranscriptPdfWriter`** (lines 62–369):
  *Lightweight, self-contained PDF 1.4 vector generator for transcript documents.*
  - `__init__(self, doc_title, page_width, page_height, margin)` [L67-L83]
  - `_escape_pdf(self, s)` [L85-L100]
  - `_flush_page(self)` [L102-L115]
  - `check_space(self, needed_pt)` [L117-L119]
  - `add_header(self, title, subtitle)` [L121-L136]
  - `_string_width(self, text, font_name, size)` [L138-L149] — *Calculate the precise rendered width in points using standard Helvetica font metrics.*
  - `_approx_char_width(self, font_name, size)` [L151-L153] — *Approximate average character width in points for legacy/backward compatibility.*
  - `_wrap_text(self, text, max_width, font_name, size)` [L155-L176]
  - `_wrap_paragraph_text(self, text, first_line_width, rest_line_width, font_name, size, has_prefix)` [L178-L216]
  - `add_paragraph(self, text, speaker, timestamp, comment, highlight, speaker_rgb)` [L218-L316]
  - `finish(self)` [L318-L366]
  - `get_pdf_bytes(self)` [L368-L369]

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

### `export/timeline.py` (801 lines)
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
  - `generate_samplitude_edl(stories, media_filename, project_title, sample_rate, apply_fades, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L390-L441] — *Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `generate_fcp7_xml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L444-L531] — *Generate Final Cut Pro 7 XML (xmeml v5) interchange format for Premiere Pro and Audition.*
  - `generate_fcpxml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L538-L594] — *Generate Apple Final Cut Pro X XML (.fcpxml) format for FCPX, DaVinci Resolve, and Logic Pro.*
  - `generate_aaf_interchange(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L597-L667] — *Generate Universal AAF XML Interchange format (.aaf) for Avid Media Composer and Pro Tools.*
  - `generate_hindenburg_session(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, apply_fades, scope, all_stories)` [L670-L747] — *Generate a Hindenburg Broadcast Session (.nhx) for Hindenburg Journalist and Broadcaster.*
  - `generate_audacity_labels(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L750-L762] — *Generate an Audacity Label Track (.txt) import file.*
  - `generate_cue_sheet(stories, media_filename, project_title, total_duration)` [L765-L776] — *Generate a standard Red Book Audio CD CUE sheet (.cue).*
  - `generate_daw_marker_csv(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L779-L801] — *Generate a Universal DAW & NLE Marker List (.csv) format.*

### `export_dialogs.py` (415 lines)
*Radio & TV Story Segmenter — Export Dialogs & Scope Selection Interface.*
- **class `ExportDialogsMixin`** (lines 53–415):
  *Provides dialog launchers, format selectors, and destination routing for MainWindow.*
  - `trigger_export(self)` [L56-L58] — *Standard trigger for Export (File menu Ctrl+E / toolbar).*
  - `export_full_transcript(self)` [L60-L62] — *Triggered from the Export Transcript button above the transcript view.*
  - `open_export_scope_dialog(self)` [L64-L66] — *Standard trigger for the main toolbar Export button.*
  - `open_unified_export_dialog(self, initial_scope, initial_dest, modal)` [L68-L129] — *Unified Export Dialog entry point for local file exports, WordPress publishing,*
  - `_dispatch_unified_export_result(self, result)` [L131-L262] — *Execute the selected export operation after UnifiedExportDialog is accepted.*
  - `_choose_export_formats(self, title, allow_media)` [L264-L415] — *Modal dialog to choose formats and transcript options for classic export flows.*
- **Functions**:
  - `show_export_completion_dialog(parent, title, message, export_path)` [L34-L50] — *Displays export completion with an actionable 'Open Folder' button (Milestone 3.11).*

### `export_documents.py` (776 lines)
*Radio & TV Story Segmenter — Document, Transcript & Timeline Interchange Exporter.*
- **class `ExportDocumentsMixin`** (lines 49–776):
  *Provides document formatting, subtitle generation, and DAW interchange exports.*
  - `_subtitle_timestamp(self, seconds, vtt)` [L52-L62]
  - `write_subtitles(self, blocks, path, fmt, include_speakers)` [L64-L80]
  - `transcript_for_range(self, start, end)` [L82-L100]
  - `speaker_for_segment(self, segment)` [L102-L111]
  - `clean_export_text(self, text, current_speaker)` [L113-L146]
  - `build_story_blocks(self, segments)` [L148-L269]
  - `story_text(self, segments)` [L271-L287]
  - `add_story_to_docx(self, document, segments)` [L289-L303]
  - `_get_transcript_text_slice(self, start, end)` [L305-L312]
  - `export_cue_sheet(self, destination_path)` [L314-L346] — *Export story/song segments to a standard .cue sheet.*
  - `export_tracklist(self, destination_path)` [L348-L378] — *Export story/song segments as YouTube chapters / tracklist formatted text.*
  - `_get_unselected_audio_mode_pref(self)` [L380-L385]
  - `export_reaper_project(self, destination_path, unselected_audio_mode)` [L387-L420] — *Export story segments as a Cockos REAPER project file (.rpp).*
  - `export_samplitude_edl(self, destination_path, unselected_audio_mode)` [L422-L455] — *Export story segments as a Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `export_audacity_labels(self, destination_path, unselected_audio_mode)` [L457-L489] — *Export story segments as an Audacity Label Track (.txt).*
  - `export_audition_xml(self, destination_path, unselected_audio_mode)` [L491-L524] — *Export story segments as Adobe Audition / Final Cut Pro XML (.xml).*
  - `export_daw_marker_csv(self, destination_path, unselected_audio_mode)` [L526-L558] — *Export story segments as a Universal DAW Marker List (.csv).*
  - `copy_youtube_chapters_to_clipboard(self)` [L560-L577] — *Format story segments as YouTube chapters and copy them directly to the system clipboard.*
  - `export_timeline_interchange(self, formats, base, options, directory, scope, is_custom_location)` [L579-L776] — *Export multi-platform timeline and DAW interchange project files.*

### `export_media_clipper.py` (337 lines)
*Radio & TV Story Segmenter — Media Clipper & Audio Track Renderer.*
- **class `ExportMediaClipperMixin`** (lines 26–337):
  *Provides audio/video track rendering, story clip extraction, and YouTube media handling.*
  - `cancel_export(self)` [L29-L34] — *Flag the running export operation to halt at the next iteration.*
  - `extract_media(self, start, end, output_file, fade_in, fade_out, cancel_check)` [L36-L63] — *Export a media range using the same container/format as the imported file,*
  - `extract_audio(self, start, end, output_file)` [L65-L71] — *Backward-compatible helper for older project/export code.*
  - `_generate_broadcast_slate_thumbnail(self, title, output_path)` [L73-L107] — *Render a clean 1280x720 dark broadcast slate image for audio-only YouTube exports.*
  - `_handle_youtube_export_result(self, result)` [L109-L337]

### `export_story_pipeline.py` (964 lines)
*Radio & TV Story Segmenter — Story & Full Episode Export Pipeline.*
- **class `ExportStoryPipelineMixin`** (lines 36–964):
  *Provides story batch export and full episode export orchestration.*
  - `_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L39-L69]
  - `_do_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L71-L349]
  - `_export_daw_interchange_files(self, formats, stories, base, transcripts_out, audio_file, options, default_track, default_scope)` [L351-L407]
  - `export_selected_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L409-L474]
  - `export_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L476-L537]
  - `export_full_and_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L539-L623]
  - `export_full_episode(self, custom_formats, custom_base, custom_options, directory, show_completion, progress_dialog, progress_value, is_custom_location)` [L625-L934]
  - `perform_stories_export(self, target_stories, custom_formats, custom_base, custom_options, directory, show_completion, is_custom_location)` [L936-L958]
  - `export_youtube_manual_package(self, export_data)` [L960-L964] — *Render and package zero-auth manual YouTube export (MP4, thumbnail, SRT, metadata .txt).*

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

### `media_batch.py` (1848 lines)
*Radio & TV Segmenter v1.1.1 — media batch responsibilities.*
- **class `MediaBatchMixin`** (lines 21–1848):
  - `probe_media_duration(self, path)` [L22-L36] — *Probe duration locally so video timelines can be populated immediately.*
  - `_track_worker_thread(self, thread)` [L38-L50] — *Keep a strong reference to active worker threads so Python GC never destroys them while executing.*
  - `stop_waveform_worker(self, timeout_ms)` [L52-L83] — *Stop the current waveform worker completely before replacing it or closing.*
  - `start_video_thumbnail_generation(self, force_regenerate)` [L85-L141]
  - `_video_thumbnail_thread_finished(self)` [L143-L150]
  - `_video_thumbnails_finished(self, items)` [L152-L158]
  - `stop_video_thumbnail_worker(self, timeout_ms)` [L160-L190]
  - `regenerate_waveform(self)` [L192-L213] — *Force recalculation of waveform peaks by clearing disk cache and restarting generation.*
  - `regenerate_video_thumbnails(self)` [L215-L228] — *Force regeneration of video filmstrip thumbnails.*
  - `load_waveform_async(self, force_regenerate)` [L230-L286]
  - `_waveform_finished(self, peaks, cancelled)` [L288-L301]
  - `_waveform_thread_finished(self)` [L303-L307]
  - `open_batch_processing_dialog(self)` [L309-L414]
  - `_batch_next_media(self)` [L416-L533]
  - `_batch_next_document(self)` [L535-L563]
  - `_batch_document_error(self, msg)` [L565-L574] — *Handles document batch translation errors safely.*
  - `_load_user_preferences(self)` [L576-L659]
  - `set_thumbnail_position(self, position)` [L661-L665]
  - `_remember_saved_project(self, path)` [L667-L698] — *Remember only projects that have actually been saved.*
  - `_dialog_directory(self, fallback)` [L700-L712]
  - `_remember_open_directory(self, path)` [L714-L721]
  - `_sync_startup_project_actions(self)` [L723-L729] — *Synchronize the Project Settings startup radio/check actions.*
  - `set_startup_project_mode(self, mode)` [L731-L737] — *Set the startup project policy.*
  - `restore_last_opened(self)` [L739-L875] — *Apply startup policy and offer recovery from a newer autosave snapshot.*
  - `toggle_speaker_labels(self, checked)` [L877-L882]
  - `toggle_colorize_speaker_labels(self, checked)` [L884-L891]
  - `toggle_timestamps(self, checked)` [L893-L900]
  - `toggle_milliseconds(self, checked)` [L902-L909]
  - `toggle_waveform_view(self, checked)` [L911-L915]
  - `toggle_thumbnail_view(self, checked)` [L917-L921]
  - `choose_default_project_directory(self)` [L923-L938]
  - `open_document_path(self, path)` [L940-L975]
  - `open_clear_cache_dialog(self)` [L977-L990]
  - `open_glossary_dialog(self)` [L992-L1230] — *Edit persistent terminology used by every ASR and translation backend.*
  - `_save_glossary(self)` [L1232-L1233]
  - `add_to_glossary(self, text)` [L1235-L1246]
  - `apply_glossary_to_whisper_context(self)` [L1248-L1259]
  - `add_custom_speaker_to_glossary(self, name)` [L1261-L1263]
  - `set_language(self, language, persist)` [L1265-L1286]
  - `_apply_localization(self)` [L1288-L1325]
  - `update_story_segment_terminology(self)` [L1327-L1431] — *Update all user-facing labels and tooltips to use 'Song' in Music mode and 'Story' in Voice mode.*
  - `open_document(self)` [L1433-L1485]
  - `export_text_file(self)` [L1487-L1495]
  - `open_media(self)` [L1497-L1506]
  - `prepare_for_new_media(self)` [L1508-L1534] — *Checks for unsaved changes before loading new media.*
  - `_batch_media_error(self, message)` [L1536-L1558]
  - `_get_batch_project_target_path(self, base_name)` [L1560-L1587] — *Determines consistent target .rtvs project file path during batch processing.*
  - `_batch_save_project_file(self)` [L1589-L1604] — *Saves project .rtvs to dedicated directory structure during batch processing.*
  - `_batch_export_current(self)` [L1606-L1690] — *Handles automatic export or project saving during batch processing.*
  - `load_media_file(self, filename, source, restore_adjacent_project)` [L1692-L1807]
  - `update_active_media_source(self)` [L1809-L1842] — *Update media player source and refresh waveform when normalization state changes.*
  - `open_audio(self)` [L1844-L1845]
  - `handle_media_drop(self, filename)` [L1847-L1848]

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

### `model_management.py` (989 lines)
*Radio & TV Segmenter v1.1.1 — model management responsibilities.*
- **class `_DummyTranslationWorker`** (lines 30–43):
  - `model_root(cls, variant)` [L32-L34]
  - `model_dir(cls, from_code, to_code, variant)` [L37-L38]
  - `model_is_installed(cls, from_code, to_code, variant)` [L41-L43]
- **class `ModelManagementMixin`** (lines 75–989):
  - `model_cache_candidates(self, model_name)` [L76-L163] — *Return all potential candidate directories where model weights might be stored.*
  - `model_cache_path(self, model_name)` [L165-L177]
  - `is_whisper_model_available(self, model_name)` [L179-L208]
  - `refresh_whisper_model_chooser(self)` [L210-L234]
  - `current_whisper_model(self)` [L236-L241]
  - `update_whisper_model_tooltip(self)` [L243-L249]
  - `set_whisper_model_from_ui(self, index)` [L251-L265]
  - `translation_model_display_name(self, variant)` [L267-L269]
  - `translation_model_root(self, variant)` [L271-L272]
  - `refresh_translation_model_chooser(self)` [L274-L284]
  - `set_translation_model_from_ui(self, index)` [L286-L295]
  - `prompt_translation_model(self)` [L297-L305]
  - `open_model_cleanup_dialog(self)` [L307-L663] — *Unified local model manager for Whisper and OPUS-MT models.*
  - `purge_all_data_action(self, parent_widget, on_complete)` [L665-L737] — *Purge all downloaded AI models, log files, updater cache, and translation runtimes.*
  - `open_translation_model_manager(self)` [L739-L741]
  - `install_whisper_model_for_manager(self, model_name, dialog)` [L743-L771]
  - `cancel_model_installation(self)` [L773-L778]
  - `_on_model_install_progress(self, percent, message)` [L780-L790]
  - `_install_whisper_model_background(self, model_name)` [L792-L830]
  - `_model_install_finished(self, error)` [L832-L833]
  - `_model_install_thread_finished(self)` [L835-L889]
  - `_poll_model_install(self, dialog)` [L891-L893]
  - `install_diarization_model_for_manager(self, dialog)` [L895-L923] — *Install or repair the WeSpeaker ResNet34 ONNX diarization voice embedding model.*
  - `install_translation_models_for_manager(self, from_code, to_code, variant, dialog)` [L925-L963] — *Install an OPUS-MT model through the translation plugin's isolated runtime.*
  - `_translation_manager_install_finished(self, from_code, to_code, variant, dialog)` [L966-L979]
  - `_translation_manager_install_error(self, message, dialog)` [L981-L989]
- **Functions**:
  - `_translation_worker_class()` [L46-L56] — *Load translation implementation dynamically without hard-importing from plugins.*
  - `_translation_plugin_installed(self)` [L58-L64]

### `playback_controller.py` (581 lines)
*Radio & TV Story Segmenter — Media Player Transport & Playback Controller.*
- **class `PlaybackControllerMixin`** (lines 25–581):
  *Provides audio/video media player transport, scrubbing, and fade controls.*
  - `is_video_file(self, path)` [L28-L33]
  - `update_video_preview_state(self)` [L35-L39]
  - `toggle_video_preview(self, checked)` [L41-L62]
  - `handle_scrub_position(self, seconds)` [L64-L67]
  - `execute_scrub_seek(self)` [L69-L76]
  - `eventFilter(self, watched, event)` [L78-L272]
  - `_is_text_entry_focused(self)` [L274-L289] — *Return True if a text entry widget or editable transcript currently has focus.*
  - `_matches_shortcut(self, event, action_id, default_seq)` [L291-L335] — *Return True if key event matches user configured shortcut for action_id.*
  - `_toggle_follow_playhead(self)` [L337-L343] — *Toggle automatic timeline view scrolling following the audio playhead.*
  - `mark_story_start_point(self)` [L345-L359] — *Mark start point at current playhead position.*
  - `mark_story_end_point(self)` [L361-L378] — *Mark end point at current playhead position and create story if valid range.*
  - `get_segment_index_at_time(self, target_time)` [L380-L388] — *Find transcript segment index active at target_time.*
  - `split_current_segment_at_playhead(self)` [L390-L395] — *Split the transcript segment active at current playhead position.*
  - `merge_current_segment_with_next(self)` [L397-L404] — *Merge the transcript segment active at current playhead with following segment.*
  - `set_skip_seconds_from_ui(self, value)` [L406-L413]
  - `set_playback_rate(self, rate)` [L415-L427]
  - `toggle_play(self)` [L429-L451]
  - `stop_audio(self)` [L453-L463]
  - `seek_to(self, seconds)` [L465-L478]
  - `seek_relative(self, delta_seconds)` [L480-L486]
  - `audio_position_changed(self, position)` [L488-L495]
  - `get_fade_volume_factor_at_time(self, t)` [L497-L540] — *Calculate the real-time audio volume fade factor [0.0, 1.0] for position `t`.*
  - `update_realtime_fade_volume(self)` [L542-L571] — *Modulate QAudioOutput volume in real-time according to story fade envelopes.*
  - `_on_fade_timer_tick(self)` [L573-L575]
  - `audio_duration_changed(self, duration)` [L577-L581]

### `playback_preferences.py` (650 lines)
*Radio & TV Story Segmenter — Playback Preferences & Application Facade.*
- **Public Exports (`__all__`)**: PlaybackPreferencesMixin, RestoreSelectedSettingsDialog, ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, PreferencesResetMixin, ProjectStateMixin
- **class `PlaybackPreferencesMixin(ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, ProjectStateMixin)`** (lines 51–650):
  *Aggregates all playback, preferences, styling, and application lifecycle mixins.*
  - `_install_diagnostic_logging(self)` [L54-L181] — *Install startup-safe diagnostics that never depend on the GUI widgets.*
  - `export_activity_log(self)` [L183-L216] — *Export session activity log entries to a timestamped plain-text file.*
  - `log_activity(self, action_text, mark_dirty)` [L218-L255]
  - `handle_activity_click(self, item)` [L257-L260]
  - `restore_snapshot(self, index)` [L262-L301]
  - `clear_activity_log(self)` [L303-L306]
  - `trigger_find_next(self)` [L308-L316] — *Find Next shortcut (F3) handler: advances to next search match.*
  - `trigger_find_prev(self)` [L318-L324] — *Find Previous shortcut (Shift+F3) handler: retreats to previous search match.*
  - `open_diagnostic_log_folder(self)` [L326-L341]
  - `show_about_dialog(self)` [L343-L382]
  - `check_for_updates(self, interactive)` [L384-L395] — *Open the Check for Updates dialog to query GitHub releases and install updates.*
  - `trigger_silent_update_check(self)` [L397-L422] — *Perform a background update check without showing UI unless an update is found.*
  - `apply_audio_output_device(self, device_name, volume)` [L424-L448] — *Apply selected audio output device and volume to the active player.*
  - `show_licenses_dialog(self)` [L450-L489]
  - `on_expected_speakers_changed(self, value)` [L491-L501] — *Kept as a public hook in case a future toolbar control adjusts the expected-speakers hint directly.*
  - `on_diarization_sensitivity_changed(self, value)` [L503-L513] — *Public hook for adjusting speaker separation sensitivity.*
  - `update_auto_save_timer(self)` [L515-L519]
  - `prompt_set_whisper_model(self)` [L521-L524]
  - `prompt_set_skip_seconds(self)` [L526-L540]
  - `prompt_set_auto_detect_thresholds(self)` [L542-L608]
  - `prompt_set_auto_save(self)` [L610-L628]
  - `trigger_auto_save(self)` [L630-L650]

### `plugin_base.py` (205 lines)
*Radio & TV Segmenter — Plugin Base Interfaces and Manifest.*
- **class `PluginManifest`** (lines 11–63):
  *Metadata describing a plugin, parsed from manifest.json.*
  - `from_dict(cls, data)` [L33-L53]
  - `from_file(cls, path)` [L56-L63]
- **class `BasePlugin`** (lines 66–166):
  *Base class for all Radio & TV Segmenter plugins.*
  - `__init__(self, manifest, app)` [L77-L80]
  - `id(self)` [L83-L84]
  - `name(self)` [L87-L88]
  - `version(self)` [L91-L92]
  - `is_enabled(self)` [L95-L96]
  - `get_enabled(self)` [L98-L99]
  - `set_enabled(self, enabled)` [L101-L108]
  - `on_load(self)` [L110-L114] — *Called immediately after the plugin module is loaded.*
  - `on_unload(self)` [L116-L118] — *Called when plugin is about to be unloaded or application closes.*
  - `on_enable(self)` [L120-L122] — *Called when the user enables the plugin.*
  - `on_disable(self)` [L124-L126] — *Called when the user disables the plugin.*
  - `get_export_actions(self)` [L128-L130] — *Return list of (Action Label, callback_function) for Export menu.*
  - `get_export_destinations(self)` [L132-L134] — *Return list of ExportDestination providers to embed into UnifiedExportDialog.*
  - `get_tools_actions(self)` [L136-L138] — *Return list of (Action Label, callback_function) for Tools menu.*
  - `get_story_actions(self, story)` [L140-L142] — *Return list of (Action Label, callback_function) for story context menu.*
  - `create_story_metadata_widget(self, parent)` [L144-L146] — *Return a QWidget to be embedded into the Stories panel for metadata editing, or None.*
  - `on_story_selected(self, story)` [L148-L150] — *Called when active story selection changes in the main editor.*
  - `get_preferences_widget(self, parent)` [L152-L154] — *Return a QWidget to be embedded into the Preferences dialog, or None.*
  - `save_preferences(self, widget)` [L156-L158] — *Called when the user saves the Preferences dialog.*
  - `on_project_loaded(self, project_data)` [L160-L162] — *Called when an .rtvs project is loaded. Allows reading plugin metadata.*
  - `on_project_saving(self, project_data)` [L164-L166] — *Called before an .rtvs project is saved. Allows injecting plugin metadata.*
- **class `ExportDestination`** (lines 169–205):
  *Base class for plugin-provided export destinations in UnifiedExportDialog.*
  - `__init__(self, id, title, description, icon, button_label)` [L172-L185]
  - `create_widget(self, parent, main_window)` [L187-L189] — *Create the configuration and preview widget embedded into the destination tab.*
  - `on_scope_changed(self, scope, stories)` [L191-L193] — *Called when export scope changes in the dialog (full, selected, all).*
  - `validate(self)` [L195-L197] — *Validate destination settings before export begins. Returns (ok, error_msg).*
  - `get_export_data(self)` [L199-L201] — *Collect export parameters to include in the final dialog result.*
  - `execute_export(self, main_window, export_data, progress_dialog)` [L203-L205] — *Execute the export action for this destination.*

### `plugin_dialogs.py` (447 lines)
*GitHub plugins dialogs, batch download workers, and PluginManagerDialog.*
- **class `GitHubPluginsWorker(QThread)`** (lines 42–91):
  *Fetches list of available plugins from GitHub release assets and official catalog.*
  - `__init__(self, repo, parent)` [L46-L48]
  - `run(self)` [L50-L91]
- **class `GitHubDownloadWorker(QThread)`** (lines 94–152):
  *Downloads and installs a `.rtvs-addon` plugin package from GitHub releases.*
  - `__init__(self, plugin_meta, plugins_dir, repo, parent)` [L98-L102]
  - `run(self)` [L104-L152]
- **class `GitHubBatchDownloadWorker(QThread)`** (lines 155–203):
  *Batch installs all missing or outdated official plugins.*
  - `__init__(self, plugins_to_install, plugins_dir, repo, parent)` [L160-L164]
  - `run(self)` [L166-L203]
- **class `GitHubPluginsDialog(QDialog)`** (lines 206–295):
  *Browse and install official and community plugins from GitHub releases.*
  - `__init__(self, plugin_manager, parent)` [L209-L241]
  - `fetch_catalog(self)` [L243-L248]
  - `on_catalog_fetched(self, success, catalog, err)` [L250-L256]
  - `populate_table(self)` [L258-L273]
  - `install_plugin(self, meta)` [L275-L285]
  - `on_installed(self, success, pid, msg)` [L287-L295]
- **class `PluginManagerDialog(QDialog)`** (lines 298–447):
  *Main management dialog for discovering, enabling, disabling, installing, and removing plugins.*
  - `__init__(self, plugin_manager, parent)` [L301-L351]
  - `refresh_list(self)` [L353-L367]
  - `on_selection_changed(self)` [L369-L398]
  - `on_enable_toggled(self, enabled)` [L400-L410]
  - `install_local_addon(self)` [L412-L442]
  - `browse_github_catalog(self)` [L444-L447]

### `plugins/__init__.py` (6 lines)
*Radio & TV Segmenter — Plugin Architecture Package.*
- **Public Exports (`__all__`)**: BasePlugin, PluginManifest

### `plugins/base.py` (6 lines)
*Radio & TV Segmenter — Plugin Base Interfaces and Manifest (Facade).*
- **Public Exports (`__all__`)**: PluginManifest, BasePlugin, ExportDestination

### `plugins/github_dialog.py` (580 lines)
*GitHub plugins browser and installer dialog with multi-selection.*
- **class `GitHubPluginsDialog(QDialog)`** (lines 41–579):
  *Browses, downloads, installs, and manages add-ons directly from GitHub releases with multi-selection.*
  - `__init__(self, manager, parent)` [L44-L60]
  - `setup_ui(self)` [L62-L165]
  - `fetch_plugins(self)` [L167-L173]
  - `on_plugins_fetched(self, success, catalog, note)` [L175-L182]
  - `render_table(self)` [L184-L282]
  - `update_all_available_plugins(self)` [L284-L317] — *Finds all installed plugins with available updates and updates them in batch.*
  - `select_all_plugins(self)` [L319-L322]
  - `deselect_all_plugins(self)` [L324-L327]
  - `get_selected_items(self)` [L329-L347] — *Returns list of plugin items that are either checked or part of extended row selection.*
  - `on_selection_changed(self)` [L349-L373]
  - `download_and_install_plugin(self, item)` [L375-L394]
  - `download_selected_plugins(self)` [L396-L426]
  - `on_batch_download_finished(self, succeeded, failed, errors)` [L428-L455]
  - `enable_selected_plugins(self)` [L457-L474]
  - `disable_selected_plugins(self)` [L476-L493]
  - `uninstall_selected_plugins(self)` [L495-L515]
  - `on_download_progress(self, percent, msg)` [L517-L519]
  - `on_download_finished(self, success, file_path, error_msg, plugin_name, plugin_id)` [L521-L555]
  - `toggle_plugin(self, plugin_id, enable)` [L557-L565]
  - `uninstall_plugin(self, plugin_id, plugin_name)` [L567-L579]

### `plugins/installer_workers.py` (293 lines)
*Background QThread workers for querying, downloading, and batch installing official plugins.*
- **class `GitHubPluginsWorker(QThread)`** (lines 59–120):
  *Fetches list of available plugins from GitHub release assets and official catalog.*
  - `__init__(self, repo, parent)` [L63-L65]
  - `run(self)` [L67-L120]
- **class `GitHubDownloadWorker(QThread)`** (lines 123–185):
  *Downloads an add-on package in background with progress updates.*
  - `__init__(self, download_url, local_dest, fallback_local_addon, parent)` [L128-L133]
  - `cancel(self)` [L135-L136]
  - `run(self)` [L138-L185]
- **class `GitHubBatchDownloadWorker(QThread)`** (lines 188–293):
  *Downloads and installs a batch of add-on packages in sequence with progress updates.*
  - `__init__(self, items, manager, enable_after, parent)` [L193-L198]
  - `cancel(self)` [L200-L201]
  - `run(self)` [L203-L293]
- **Functions**:
  - `get_official_plugins_catalog(repo)` [L20-L56] — *Returns the base catalog of official plugins for the repository.*

### `plugins/manager.py` (657 lines)
*Radio & TV Segmenter — Plugin Manager and Discovery Engine.*
- **Public Exports (`__all__`)**: PluginManager, PluginManagerDialog, GitHubPluginsDialog, GitHubPluginsWorker, GitHubDownloadWorker, GitHubBatchDownloadWorker, parse_plugin_version_tuple, is_newer_plugin_version
- **class `PluginManager`** (lines 68–638):
  *Manages discovery, lifecycle, settings, and GUI injection of plugins.*
  - `__init__(self, app)` [L71-L76]
  - `get_user_plugins_dir(cls)` [L79-L89] — *Returns the user-writable plugins folder.*
  - `get_bundled_plugins_dir(cls)` [L92-L103] — *Returns the application installation plugins folder.*
  - `discover_plugins(self)` [L105-L181] — *Scans plugin directories (bundled/repository and user folder) and loads manifests of available plugins.*
  - `sync_bundled_updates(self)` [L183-L268] — *Automatically updates installed plugins in the user directory if a newer version is bundled with an app update,*
  - `ensure_packaged_addons(self)` [L270-L300] — *Ensures that all bundled directory-based plugins have up-to-date .rtvs-addon files created.*
  - `get_bundled_addons(cls)` [L303-L319] — *Returns a map of plugin_id -> Path of bundled .rtvs-addon packages.*
  - `_is_uninstalled(self, plugin_id)` [L321-L325]
  - `is_plugin_installed(self, plugin_id)` [L327-L331] — *Checks whether the plugin is installed in the system.*
  - `is_plugin_enabled(self, plugin_id)` [L333-L341]
  - `plugin_runtime(self, plugin_id)` [L343-L347]
  - `set_plugin_enabled(self, plugin_id, enabled)` [L349-L361]
  - `load_all_plugins(self)` [L363-L368] — *Discovers and instantiates all enabled plugins.*
  - `load_plugin(self, plugin_id)` [L370-L422]
  - `unload_plugin(self, plugin_id)` [L424-L431]
  - `get_export_destinations(self)` [L433-L443] — *Returns all ExportDestination objects contributed by currently enabled plugins.*
  - `uninstall_plugin(self, plugin_id)` [L446-L547] — *Uninstalls and removes a plugin completely from the system.*
  - `install_addon(self, package_path, enable, expected_sha256, load_ui)` [L549-L614] — *Installs a .rtvs-addon or .zip package into the user plugins directory.*
  - `package_addon(cls, plugin_folder, output_zip)` [L617-L638] — *Zips a plugin directory into an .rtvs-addon file.*
- **Functions**:
  - `parse_plugin_version_tuple(version_str)` [L22-L37] — *Parse plugin version string into comparable numerical components and a stability weight.*
  - `is_newer_plugin_version(new_version, current_version)` [L40-L44] — *Returns True if new_version is strictly newer than current_version.*

### `plugins/manager_dialog.py` (529 lines)
*Plugin and Add-On Manager Dialog for inspecting, enabling, and installing add-ons.*
- **class `PluginManagerDialog(QDialog)`** (lines 40–529):
  *GUI Dialog for viewing, managing, enabling, installing, and removing plugins with multi-selection.*
  - `__init__(self, manager, parent)` [L43-L51]
  - `setup_ui(self)` [L53-L163]
  - `on_download_github(self)` [L165-L176]
  - `select_all_plugins(self)` [L178-L179]
  - `deselect_all_plugins(self)` [L181-L182]
  - `get_selected_plugin_ids(self)` [L184-L197] — *Returns the list of plugin_ids selected via multi-row selection.*
  - `refresh_list(self)` [L199-L244]
  - `on_toggle_plugin(self, plugin_id, state)` [L246-L254]
  - `on_selection_changed(self)` [L256-L282]
  - `configure_selected_plugin(self)` [L284-L305]
  - `enable_selected_plugins(self)` [L307-L320]
  - `disable_selected_plugins(self)` [L322-L335]
  - `uninstall_selected_plugins(self)` [L337-L361]
  - `on_install_addon(self)` [L363-L400]
  - `check_for_plugin_updates(self)` [L402-L481] — *Checks GitHub for newer versions of installed plugins without updating the core app.*
  - `run_batch_plugin_updates(self, update_items)` [L483-L517] — *Downloads and installs a batch of plugin updates.*
  - `on_open_folder(self)` [L519-L529]

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

### `plugins/version_utils.py` (30 lines)
*Version parsing and semantic comparison utilities for the plugin system.*
- **Functions**:
  - `parse_plugin_version_tuple(version_str)` [L8-L23] — *Parse plugin version string into comparable numerical components and a stability weight.*
  - `is_newer_plugin_version(new_version, current_version)` [L26-L30] — *Returns True if new_version is strictly newer than current_version.*

### `plugins/wordpress/__init__.py` (6 lines)
*WordPress Publisher Plugin for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: Plugin

### `plugins/wordpress/castos.py` (722 lines)
*Seriously Simple Podcasting (Castos) integration for WordPress export.*
- **Public Exports (`__all__`)**: SS_PODCAST_AUDIO_FILE, SS_PODCAST_AUDIO_FILE_ID, SS_PODCAST_DURATION, SS_PODCAST_FILESIZE, SS_PODCAST_FEED, SS_PODCAST_EPISODE_TYPE, SS_PODCAST_SEASON, SS_PODCAST_EPISODE_NUMBER, CASTOS_META_AUDIO_FILE, CASTOS_META_AUDIO_FILE_ID, CASTOS_META_DURATION, CASTOS_META_FILESIZE, CASTOS_META_EPISODE_TYPE, CASTOS_META_SEASON, CASTOS_META_EPISODE_NUMBER, CASTOS_TAXONOMY_SERIES, CASTOS_TAXONOMY_SERIES_FALLBACK, CASTOS_SHORTCODE, CASTOS_PLAYER_BLOCK, DEFAULT_FEED_SLUG, DEFAULT_FEED_NAME, format_castos_duration, build_castos_post_meta, copy_podcast_meta, fetch_castos_feeds, sanitize_castos_feeds, setup_castos_ui, populate_castos_feeds_combo, sync_castos_to_post, load_castos_from_post
- **Functions**:
  - `format_castos_duration(seconds)` [L58-L69] — *Format duration in seconds into HH:MM:SS for podcast RSS metadata.*
  - `build_castos_post_meta(audio_url, attachment_id, duration_seconds, filesize_bytes, feed_slug, episode_type, season, episode_number)` [L72-L140] — *Build the dictionary of Seriously Simple Podcasting post meta keys.*
  - `copy_podcast_meta(target, src)` [L143-L158] — *Copy Seriously Simple Podcasting metadata fields from src to target dictionary.*
  - `fetch_castos_feeds(client)` [L161-L307] — *Query WordPress REST API for Seriously Simple Podcasting series/feeds.*
  - `sanitize_castos_feeds(feeds)` [L310-L324] — *Filter out non-podcast/author items and ensure valid feed structures.*
  - `setup_castos_ui(tab_widget, editor_layout)` [L327-L503] — *Build and insert the Castos Seriously Simple Podcasting section into the post editor layout.*
  - `populate_castos_feeds_combo(tab_widget, feeds)` [L506-L543] — *Populate the podcast feed list and combo with discovered series/feeds.*
  - `sync_castos_to_post(tab_widget, post)` [L546-L609] — *Extract Castos UI state and write into post dictionary.*
  - `load_castos_from_post(tab_widget, post)` [L612-L688] — *Set Castos UI controls from post dictionary.*

### `plugins/wordpress/client.py` (1887 lines)
*WordPress Plugin — Client, Credential Storage, and Upload Engine.*
- **class `WordPressClient`** (lines 342–913):
  *Client for WordPress REST API using Application Passwords.*
  - `__init__(self, site_url, username, password)` [L345-L357]
  - `is_configured(self)` [L359-L366] — *Return True if site_url, username, and password are all non-empty and non-placeholder.*
  - `_get_auth(self)` [L368-L369]
  - `_discover_canonical_base(self)` [L371-L382] — *Pre-detect canonical site URL and REST base to prevent redirect failures.*
  - `_is_safe_redirect(self, current_url, next_url)` [L384-L393] — *Verify redirect does not cross domains or downgrade from HTTPS to HTTP.*
  - `_get_request(self, url, params, headers, timeout)` [L395-L426] — *Issue an HTTP GET with manual redirect protection and authentication.*
  - `_post_request(self, url, json_data, headers, timeout)` [L428-L455] — *Issue an HTTP POST with manual redirect protection to keep POST method & Auth header.*
  - `_post_multipart(self, url, path, upload_filename, mime_type, timeout)` [L457-L483] — *Issue a multipart file POST with manual redirect protection.*
  - `test_connection(self)` [L485-L508] — *Test credentials against /wp/v2/users/me or /wp/v2/posts.*
  - `get_categories(self)` [L510-L526] — *Fetch post categories from WordPress.*
  - `get_authors(self)` [L528-L625] — *Fetch PublishPress Authors profiles, including guest authors without users.*
  - `upload_media(self, file_path, filename)` [L627-L681] — *Upload media using WordPress's standard multipart API, with raw fallback.*
  - `get_podcast_feeds(self)` [L683-L686] — *Fetch Seriously Simple Podcasting feeds/series or return default feed.*
  - `create_post(self, title, content, excerpt, status, category_ids, author_ids, author_term_ids, featured_media_id, meta, podcast_series)` [L688-L860] — *Create a post in WordPress.*
  - `update_post(self, post_id, content, title, excerpt, status, category_ids, featured_media_id, meta, podcast_series)` [L862-L913] — *Update an existing post in WordPress.*
- **class `WordPressSettingsDialog(QDialog)`** (lines 916–1095):
  *Dialog for entering and testing WordPress site credentials.*
  - `__init__(self, parent)` [L919-L1043]
  - `_test_connection(self)` [L1045-L1066]
  - `_save_settings(self)` [L1068-L1095]
- **class `WordPressPreferencesPage(QWidget)`** (lines 1109–1277):
  *Preferences page widget for WordPress integration inside the application Preferences dialog.*
  - `__init__(self, parent, app)` [L1112-L1116]
  - `setup_ui(self)` [L1118-L1225]
  - `_test_connection(self)` [L1227-L1246]
  - `save_preferences(self, dialog)` [L1248-L1277]
- **Functions**:
  - `_get_keyring()` [L49-L55] — *Safely return keyring module if available.*
  - `_get_wp_fallback_cipher()` [L58-L72] — *Best-effort symmetric cipher bound to this machine, used only for*
  - `_get_wp_password(username)` [L75-L100] — *Retrieve the stored WordPress application password.*
  - `_set_wp_password(username, password)` [L103-L137] — *Store the WordPress application password securely.*
  - `format_rich_text_to_html(text, auto_link_urls, main_window)` [L140-L240] — *Format rich text, Markdown hyperlinks, and URLs into safe HTML for WordPress posts.*
  - `format_parent_episode_notice(episode_title, episode_url, template)` [L243-L276] — *Format the parent episode notice block to inject into a story post.*
  - `build_episode_stories_toc(stories)` [L279-L314] — *Build a Gutenberg Table of Contents block listing all stories in the episode.*
  - `generate_wp_excerpt(text, max_words)` [L317-L327] — *Generate a clean WordPress-style post excerpt from text (standard 55 words).*
  - `is_wp_auth_error(err)` [L330-L339] — *Check if an error string or exception indicates an authentication or credential failure.*
  - `get_wp_client()` [L1098-L1106] — *Instantiate WordPressClient from stored settings if configured.*
  - `_group_segments_into_paragraphs(segments, min_words)` [L1280-L1328] — *Group consecutive segments with same speaker into natural paragraph blocks.*
  - `_build_audio_fade_filter(duration, fade_in, fade_out, fade_curve)` [L1331-L1359] — *Construct FFmpeg afade audio filter chain for story clips.*
  - `execute_wordpress_upload(main_window, client, post_title, post_excerpt, start, end, task_label, include_english, include_spanish, spanish_presentation, primary_language, author_ids, author_term_ids, category_ids, show_completion_dialog, media_filename, progress_callback, featured_image_path, parent_episode_info, link_parent_episode, parent_episode_template, parent_episode_pos, include_audio, fade_in, fade_out, fade_curve, apply_fades, accordion_pos, is_podcast, podcast_feed, podcast_feed_id, podcast_feed_ids, podcast_feeds, podcast_episode_type, podcast_season, podcast_episode_number)` [L1362-L1887] — *Extract media clip, upload to WordPress media library, and create draft post.*

### `plugins/wordpress/export_destination.py` (631 lines)
*WordPress Export Destination for UnifiedExportDialog.*
- **Public Exports (`__all__`)**: WordPressExportDestination, WordPressExportTabWidget, WordPressPostMetadataDialog, capture_video_frame, build_wp_post_items, build_episode_stories_toc, format_parent_episode_notice, is_wp_auth_error, SS_PODCAST_AUDIO_FILE, SS_PODCAST_AUDIO_FILE_ID, SS_PODCAST_DURATION, SS_PODCAST_FILESIZE, SS_PODCAST_FEED, SS_PODCAST_EPISODE_TYPE, CASTOS_SHORTCODE, CASTOS_PLAYER_BLOCK, build_castos_post_meta, format_castos_duration, fetch_castos_feeds
- **class `WordPressExportDestination(ExportDestination)`** (lines 36–510):
  *Export destination handler for WordPress REST API Draft Posts.*
  - `__init__(self, plugin)` [L39-L47]
  - `button_label(self)` [L50-L55]
  - `button_label(self, val)` [L58-L59]
  - `get_export_button_label(self)` [L61-L62]
  - `widget(self)` [L65-L66]
  - `widget(self, val)` [L69-L70]
  - `create_widget(self, parent, main_window)` [L72-L74]
  - `on_scope_changed(self, scope, stories)` [L76-L78]
  - `validate(self)` [L80-L96]
  - `get_export_data(self)` [L98-L117]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L119-L510]
- **class `WordPressPostMetadataDialog(QDialog)`** (lines 513–593):
  *Full-featured WordPress post & story metadata editor dialog.*
  - `__init__(self, parent, main_window, target_story_index)` [L516-L572]
  - `_on_save_clicked(self)` [L574-L579]
  - `_on_close_clicked(self)` [L581-L583]
  - `_on_save_and_close(self)` [L585-L586]
  - `done(self, r)` [L588-L593]

### `plugins/wordpress/plugin.py` (897 lines)
*WordPress Publisher Plugin for Radio & TV Segmenter.*
- **class `WordPressPublishDialog(QDialog)`** (lines 91–517):
  *Publish a story or project to WordPress with featured image selection.*
  - `__init__(self, plugin, parent, story)` [L94-L109]
  - `setup_ui(self)` [L111-L263]
  - `load_custom_text_settings(self)` [L265-L278] — *Load persistent custom text defaults from application settings.*
  - `save_custom_text_defaults(self)` [L280-L286] — *Save active custom text, placement, and exclusion settings as persistent defaults.*
  - `load_metadata(self)` [L288-L329]
  - `do_capture_frame(self)` [L331-L341]
  - `on_image_mode_changed(self)` [L343-L358]
  - `on_browse_image(self)` [L360-L371]
  - `on_configure_credentials(self)` [L373-L379]
  - `on_publish(self)` [L381-L474]
  - `on_publish_finished(self, success, msg, post_data)` [L476-L510]
  - `closeEvent(self, event)` [L512-L517]
- **class `WordPressPublishWorker(QThread)`** (lines 520–557):
  - `__init__(self, client, title, content, excerpt, status, image_path)` [L523-L530]
  - `run(self)` [L532-L557]
- **class `WordPressStoryMetadataWidget(QGroupBox)`** (lines 560–836):
  *Clean, compact WordPress metadata launcher & inspector embedded in the Stories sidebar.*
  - `__init__(self, plugin, parent)` [L563-L575]
  - `setup_ui(self)` [L577-L665]
  - `refresh_targets_dropdown(self)` [L667-L690] — *Populate target_combo with Full Episode and all current project stories.*
  - `_on_target_changed(self, index)` [L692-L710]
  - `set_story(self, story)` [L712-L724] — *Called when user selects a story in the story list or timeline.*
  - `_get_active_wp_metadata(self)` [L726-L736]
  - `_load_current_target_metadata(self)` [L738-L791]
  - `_open_post_settings_dialog(self)` [L793-L799]
  - `_on_refresh_taxonomy(self)` [L801-L836]
- **class `Plugin(BasePlugin)`** (lines 839–896):
  *WordPress Plugin implementation hooking into RTVS.*
  - `__init__(self, manifest, app)` [L842-L844]
  - `on_load(self)` [L846-L847]
  - `get_export_destinations(self)` [L849-L851]
  - `get_export_actions(self)` [L853-L861]
  - `get_story_actions(self, story)` [L863-L867]
  - `create_story_metadata_widget(self, parent)` [L869-L871]
  - `on_story_selected(self, story)` [L873-L874]
  - `get_preferences_widget(self, parent)` [L876-L878]
  - `open_publish_dialog(self, parent, story)` [L880-L882]
  - `open_post_metadata_dialog(self, parent, story)` [L884-L896]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path, timeout)` [L66-L88] — *Extract a high quality single frame from a video using fast seeking FFmpeg.*

### `plugins/wordpress/wordpress_dialog.py` (886 lines)
*WordPress Export Tab Widget and Post Metadata Dialog.*
- **class `WordPressExportTabWidget(QWidget)`** (lines 79–843):
  *Configuration and preview panel for WordPress Draft Posts.*
  - `__init__(self, parent, main_window, metadata_editor_mode)` [L82-L101]
  - `_setup_ui(self)` [L103-L318]
  - `update_wp_pres_visibility(self)` [L320-L321]
  - `_update_wp_conn_status(self)` [L323-L324]
  - `_open_wp_settings(self)` [L326-L329]
  - `_filter_authors_list(self, text)` [L331-L332]
  - `_filter_categories_list(self, text)` [L334-L335]
  - `_on_title_edited(self, text)` [L337-L342]
  - `_on_excerpt_edited(self)` [L344-L348]
  - `_auto_generate_current_excerpt(self)` [L350-L359]
  - `_autofill_all_excerpts(self)` [L361-L368]
  - `_on_author_item_changed(self, item)` [L370-L376]
  - `_on_category_item_changed(self, item)` [L378-L383]
  - `_clear_current_authors(self)` [L385-L391]
  - `_clear_current_categories(self)` [L393-L399]
  - `_get_selected_story_indices(self)` [L401-L406]
  - `_apply_authors_to_selected_stories(self)` [L408-L416]
  - `_apply_categories_to_selected_stories(self)` [L418-L425]
  - `_apply_thumbnails_to_selected_stories(self)` [L427-L448]
  - `_apply_authors_to_all_posts(self)` [L450-L455]
  - `_apply_categories_to_all_posts(self)` [L457-L461]
  - `_apply_thumbnails_to_all_posts(self)` [L463-L482]
  - `_sync_post_to_project(self, idx)` [L484-L485]
  - `save_all_posts_to_project(self)` [L487-L488]
  - `_update_post_list_item_label(self, idx)` [L490-L494]
  - `_on_wp_post_selection_changed(self, row)` [L496-L500]
  - `_get_editor_checked_authors(self)` [L502-L514]
  - `_set_editor_checked_authors(self, author_ids, author_term_ids)` [L516-L526]
  - `_get_editor_checked_categories(self)` [L528-L536]
  - `_set_editor_checked_categories(self, cat_ids)` [L538-L547]
  - `_get_wp_post_bounds(self, post_index)` [L549-L554]
  - `_sync_wp_slider_to_pos(self, pos)` [L556-L564]
  - `_on_wp_slider_value_changed(self, val)` [L566-L575]
  - `_on_wp_scrub_timer_timeout(self)` [L577-L579]
  - `_on_wp_step(self, delta_secs)` [L581-L590]
  - `_on_wp_sync_playhead(self)` [L592-L601]
  - `_load_post_editor_state(self, index)` [L603-L634]
  - `_on_wp_thumb_mode_changed(self)` [L636-L651]
  - `_capture_wp_frame(self, pos)` [L653-L671]
  - `_on_wp_browse_thumb(self)` [L673-L686]
  - `rebuild_post_items(self, scope)` [L688-L803]
  - `_populate_wp_export_metadata(self, force_refresh)` [L805-L839]
  - `_refresh_wp_metadata(self)` [L841-L843]
- **class `WordPressPostMetadataDialog(QDialog)`** (lines 846–886):
  *Dialog for editing WordPress post metadata for an individual story.*
  - `__init__(self, parent, main_window, target_story_index)` [L849-L883]
  - `_on_save_and_close(self)` [L885-L886]
- **Functions**:
  - `generate_wp_excerpt(transcript_words, start_t, end_t)` [L59-L61]
  - `capture_video_frame(video_path, timestamp, output_path)` [L64-L76]

### `plugins/wordpress/wp_post_builder.py` (287 lines)
*Post item builder, transcript slicing, and video frame extraction for WordPress export.*
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path, timeout)` [L13-L35] — *Capture a single frame from video at timestamp using ffmpeg.*
  - `get_primary_text_slice(main_window, primary_lang, st_start, st_end)` [L38-L67] — *Extract transcript or translated text for the specified time slice.*
  - `build_wp_post_items(main_window, scope, primary_lang, existing_items)` [L70-L287] — *Build the list of WordPress post definitions according to the export scope.*

### `plugins/wordpress/wp_tab_widget.py` (995 lines)
*WordPress export tab configuration widget and preview controller.*
- **class `WordPressExportTabWidget(QWidget)`** (lines 37–994):
  *Configuration and preview panel for WordPress Draft Posts.*
  - `__init__(self, parent, main_window, metadata_editor_mode)` [L40-L59]
  - `_setup_ui(self)` [L61-L62]
  - `_on_wp_include_audio_toggled(self, checked)` [L64-L75]
  - `_update_wp_conn_status(self)` [L77-L85]
  - `_open_wp_settings(self)` [L87-L91]
  - `_filter_authors_list(self, text)` [L93-L97]
  - `_filter_categories_list(self, text)` [L99-L103]
  - `_sync_to_proj(self, idx)` [L105-L107]
  - `_on_title_edited(self, text)` [L109-L114]
  - `_on_excerpt_edited(self)` [L116-L120]
  - `_auto_generate_current_excerpt(self)` [L122-L130]
  - `_autofill_all_excerpts(self)` [L132-L139]
  - `_on_author_item_changed(self, item)` [L141-L149]
  - `_on_category_item_changed(self, item)` [L151-L158]
  - `_clear_current_authors(self)` [L160-L166]
  - `_clear_current_categories(self)` [L168-L173]
  - `_get_selected_story_indices(self)` [L175-L179]
  - `_apply_authors_to_selected_stories(self)` [L181-L214]
  - `_apply_categories_to_selected_stories(self)` [L216-L246]
  - `_apply_thumbnails_to_selected_stories(self)` [L248-L281]
  - `_apply_authors_to_all_posts(self)` [L283-L302]
  - `_apply_categories_to_all_posts(self)` [L304-L320]
  - `_apply_thumbnails_to_all_posts(self)` [L322-L342]
  - `_apply_podcast_to_selected_stories(self)` [L344-L374]
  - `_apply_podcast_to_all_posts(self)` [L376-L391]
  - `_sync_post_to_project(self, idx)` [L393-L494]
  - `save_all_posts_to_project(self)` [L496-L513] — *Persist all post metadata and export options back into stories and project_metadata.*
  - `_update_post_list_item_label(self, idx)` [L515-L530]
  - `_on_wp_post_selection_changed(self, row)` [L532-L535]
  - `_get_editor_checked_authors(self)` [L537-L553]
  - `_set_editor_checked_authors(self, author_ids, author_term_ids)` [L555-L573]
  - `_get_editor_checked_categories(self)` [L575-L583]
  - `_set_editor_checked_categories(self, cat_ids)` [L585-L593]
  - `_get_wp_post_bounds(self, post_index)` [L595-L604]
  - `_sync_wp_slider_to_pos(self, pos)` [L606-L616]
  - `_on_wp_slider_value_changed(self, val)` [L618-L626]
  - `_on_wp_scrub_timer_timeout(self)` [L628-L632]
  - `_on_wp_step(self, delta_secs)` [L634-L642]
  - `_on_wp_sync_playhead(self)` [L644-L651]
  - `_load_post_editor_state(self, index)` [L653-L710]
  - `_on_wp_thumb_mode_changed(self)` [L712-L747]
  - `_capture_wp_frame(self, pos)` [L749-L783]
  - `_on_wp_browse_thumb(self)` [L785-L803]
  - `_cleanup_temp_files(self)` [L805-L814] — *Purge temporary frame grabs and preview images.*
  - `closeEvent(self, event)` [L816-L824] — *Persist current post state and clean up temp files on widget/dialog closure.*
  - `rebuild_post_items(self, scope)` [L826-L864]
  - `_populate_wp_export_metadata(self, force_refresh)` [L866-L933]
  - `_refresh_castos_feeds(self)` [L935-L960]
  - `_refresh_wp_metadata(self)` [L962-L994]

### `plugins/wordpress/wp_ui_builder.py` (731 lines)
*UI layout construction and widget setup for WordPressExportTabWidget.*
- **Functions**:
  - `setup_wp_tab_ui(self)` [L36-L731] — *Construct all controls, forms, sliders, list widgets, and tabbed panels for the WordPress export tab.*

### `plugins/youtube/__init__.py` (9 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*

### `plugins/youtube/export_destination.py` (594 lines)
*YouTube Export Destination for UnifiedExportDialog with Zero-Auth Manual Publishing.*
- **class `YouTubeExportTabWidget(QWidget)`** (lines 87–529):
  *Configuration and preview panel for YouTube Zero-Auth Manual Publishing.*
  - `__init__(self, parent, main_window)` [L90-L103]
  - `_setup_ui(self)` [L105-L351]
  - `_get_yt_bounds(self)` [L353-L371]
  - `_on_yt_thumb_mode_changed(self)` [L373-L390]
  - `_update_yt_scrub_slider_range(self)` [L392-L401]
  - `_on_yt_slider_value_changed(self, value)` [L403-L409]
  - `_on_yt_step(self, delta_sec)` [L411-L416]
  - `_on_yt_sync_playhead(self)` [L418-L423]
  - `_schedule_yt_frame_preview(self)` [L425-L428]
  - `_on_yt_scrub_timer_timeout(self)` [L430-L444]
  - `_on_yt_browse_thumb(self)` [L446-L457]
  - `_cleanup_temp_files(self)` [L459-L468] — *Purge temporary thumbnail frame grabs.*
  - `closeEvent(self, event)` [L470-L473] — *Clean up temporary thumbnail files on closure.*
  - `reject(self)` [L475-L478] — *Ensure temp preview files are purged on dialog rejection.*
  - `done(self, r)` [L480-L483] — *Ensure temp preview files are purged on dialog completion.*
  - `populate_metadata(self)` [L485-L529] — *Builds default title, description, chapter timestamps, and speaker credits from current stories.*
- **class `YouTubeExportDestination(ExportDestination)`** (lines 532–594):
  *Export destination handler for YouTube Zero-Auth Manual Publishing.*
  - `__init__(self, plugin)` [L535-L543]
  - `create_widget(self, parent, main_window)` [L545-L547]
  - `on_scope_changed(self, scope, stories)` [L549-L551]
  - `validate(self)` [L553-L559]
  - `get_export_data(self)` [L561-L588]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L590-L594]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path)` [L69-L84]

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

### `plugins/youtube/plugin.py` (224 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*
- **class `YouTubeSettingsDialog(QDialog)`** (lines 63–187):
  *Preferences dialog for YouTube Publishing (Zero-Auth Assisted Upload defaults).*
  - `__init__(self, parent)` [L66-L73]
  - `setup_ui(self)` [L75-L175]
  - `on_save(self)` [L177-L187]
- **class `Plugin(BasePlugin)`** (lines 190–224):
  *YouTube Video Publisher plugin hooking into RTVS.*
  - `on_load(self)` [L193-L194]
  - `get_export_destinations(self)` [L196-L198]
  - `get_export_actions(self)` [L200-L203]
  - `get_preferences_widget(self, parent)` [L205-L220]
  - `open_publish_dialog(self)` [L222-L224]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path)` [L45-L60]

### `preferences_dialog.py` (723 lines)
*Radio & TV Story Segmenter — Preferences Modal Dialog.*
- **class `PreferencesDialogMixin(PreferencesResetMixin)`** (lines 30–723):
  *Provides the main open_preferences_dialog method and settings persistence.*
  - `open_preferences_dialog(self, initial_category, modal)` [L33-L723] — *Open the multi-category Preferences dialog as a non-modal floating inspector.*

### `preferences_reset.py` (642 lines)
*Radio & TV Story Segmenter — Preferences Reset & Factory Defaults Engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 21–164):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L42-L125]
  - `_select_all(self)` [L127-L129]
  - `_deselect_all(self)` [L131-L133]
  - `_handle_reset(self)` [L135-L164]
- **class `PreferencesResetMixin`** (lines 167–642):
  *Provides methods for resetting settings to defaults across all app categories.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L170-L631] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L633-L642] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_reset_dialog.py` (621 lines)
*Radio & TV Segmenter — Preferences reset and factory default restore engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 20–163):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L41-L124]
  - `_select_all(self)` [L126-L128]
  - `_deselect_all(self)` [L130-L132]
  - `_handle_reset(self)` [L134-L163]
- **class `PreferencesResetMixin`** (lines 166–620):
  *Mixin providing settings reset and restore dialog actions.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L169-L609] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L611-L620] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_tabs_core.py` (623 lines)
*Radio & TV Story Segmenter — Preferences Modal Core Tab Builders.*
- **Functions**:
  - `build_general_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L26-L187]
  - `build_shortcuts_tab(win, dialog, live_widgets)` [L190-L198]
  - `build_audio_hardware_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L201-L344]
  - `build_updates_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L347-L386]
  - `build_ai_models_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L389-L512]
  - `build_gpu_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L515-L623]

### `preferences_tabs_media.py` (650 lines)
*Radio & TV Story Segmenter — Preferences Modal Media & Workflow Tab Builders.*
- **Functions**:
  - `build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L22-L136]
  - `build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L139-L238]
  - `build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L241-L364]
  - `build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L367-L565]
  - `build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L568-L650]

### `preview_manager.py` (270 lines)
*AI Studio Web Preview Manager for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_project_version()` [L178-L187] — *Extract PROJECT_VERSION from prs_shared.py.*
  - `restore_preview(force)` [L190-L217] — *Ensure all preview scaffolding files exist with up-to-date version strings.*
  - `sync_version(version)` [L220-L252] — *Synchronize the application version into package.json, metadata.json, and index.html.*
  - `main()` [L255-L266]

### `process_lifecycle.py` (191 lines)
*Radio & TV Segmenter — Subprocess tracking and OS-level job object lifecycle isolation.*
- **Functions**:
  - `init_child_process_job_isolation()` [L20-L102] — *Initialize OS-level guarantees that child processes terminate when parent exits.*
  - `bind_subprocess_to_job(proc)` [L105-L137] — *Assign an individual process (by HANDLE or PID) to the Windows Job Object if needed.*
  - `register_process(proc)` [L140-L144] — *Register a QProcess or subprocess.Popen instance to track its lifecycle.*
  - `unregister_process(proc)` [L147-L149] — *Unregister a process when it exits naturally or is cleaned up.*
  - `get_registered_processes()` [L152-L154] — *Return a snapshot list of currently registered processes.*
  - `terminate_all_registered_processes()` [L160-L184] — *Terminate and wait on all active child processes upon application close.*

### `processing.py` (1216 lines)
*Radio & TV Segmenter v3.3.29 — processing responsibilities.*
- **class `RuntimeSetupWorker(QThread)`** (lines 56–85):
  *Runs runtime_manager.ensure_environment() off the GUI thread, so that*
  - `__init__(self, runtime_mgr, feature, parent, ensure_kwargs)` [L64-L69]
  - `cancel(self)` [L71-L72]
  - `run(self)` [L74-L85]
- **class `ProcessingMixin(TranscriptionProcessingMixin, DiarizationProcessingMixin, StoryDetectionProcessingMixin)`** (lines 92–1215):
  - `_ensure_runtime_environment_responsive(self, feature, **ensure_kwargs)` [L103-L193] — *Make sure the isolated venv for `feature` is ready before*
  - `cancel_current_process(self)` [L195-L329]
  - `update_skip_stage_button_visibility(self)` [L331-L341] — *Show or hide the 'Skip Stage' button based on active pipeline state.*
  - `skip_current_pipeline_stage(self)` [L343-L391] — *Cancel the active pipeline stage and advance directly to the next queued stage.*
  - `commit_story_change(self, old_stories, new_stories, description)` [L393-L408]
  - `apply_story_selection_indices(self, selected_rows, seek)` [L410-L477]
  - `on_timeline_story_clicked(self, index)` [L479-L489] — *Handle user clicking a story region directly on the timeline canvas.*
  - `story_selection_changed(self)` [L491-L508]
  - `handle_timeline_multi_selection(self, selected_indices)` [L510-L521]
  - `set_tools_actions_enabled(self, enabled)` [L523-L559]
  - `stop_story_detection_worker(self, timeout_ms)` [L561-L584] — *Cancel Story Detection and wait for its QThread to finish.*
  - `stop_all_processing(self, timeout_ms)` [L586-L601] — *Stop every local processing job before changing media/projects or exiting.*
  - `confirm_stop_processing_for_media_change(self)` [L603-L631]
  - `worker_thread_finished(self)` [L633-L635]
  - `start_full_auto_pipeline(self)` [L637-L786] — *Open a chooser for the processing stages to run, then run them in order.*
  - `_confirm_pipeline_rerun_if_needed(self, stages, parent)` [L788-L857] — *Look ahead at stages about to run in a pipeline. If any have already*
  - `_run_next_selected_processing(self)` [L859-L939]
  - `start_transcribe_and_diarize(self)` [L941-L960]
  - `_processing_choice(self, kind)` [L962-L1001] — *Return: run, continue, start_over, or cancel based on current state.*
  - `_worker_command(self, args)` [L1003-L1022] — *Return (executable, args, env_overrides) for the local AI worker,*
  - `_resolve_worker_command(self, args)` [L1024-L1071] — *Return (executable, args, env_overrides) for the local AI worker.*
  - `_apply_worker_env_overrides(self, process, env_overrides)` [L1074-L1110] — *Applies extra environment variables (e.g. GPU device selection, SSL certs,*
  - `_download_model_and_continue_transcription(self, model_name, label)` [L1112-L1145] — *Asynchronously download a missing model with responsive in-dialog progress and auto-resume.*
  - `_on_transcription_dl_progress(self, pct, msg)` [L1147-L1157]
  - `_on_transcription_dl_cancel(self)` [L1159-L1166]
  - `_on_transcription_dl_finished(self, err)` [L1168-L1201]
  - `_on_transcription_dl_thread_cleanup(self)` [L1203-L1215]

### `project_export.py` (446 lines)
*Radio & TV Story Segmenter — Unified Project & Media Export Facade.*
- **class `ProjectExportMixin(ExportDialogsMixin, ExportMediaClipperMixin, ExportDocumentsMixin, ExportStoryPipelineMixin, ProjectLifecycleMixin)`** (lines 87–446):
  *Unified application export mixin composed of focused export sub-mixins.*
  - `export_project_archive(self, destination_zip)` [L104-L178] — *Export current project state, transcripts, and media into a self-contained portable .zip archive.*
  - `ensure_project_for_processing_pipeline(self)` [L180-L203] — *Ensures a project file is established on disk before running multi-stage*
  - `resolve_project_media(self, project_file, audio_reference, audio_file_abs)` [L205-L263] — *Resolves portable or absolute project media reference with security extension validation.*
  - `closeEvent(self, event)` [L265-L446] — *MainWindow close event handling shutdown, worker cancellation, and QSettings sync.*

### `project_lifecycle.py` (992 lines)
*Radio & TV Story Segmenter — Project Lifecycle & Persistence Management.*
- **class `ProjectLifecycleMixin`** (lines 43–840):
  *Provides project lifecycle and persistence methods for MainWindow.*
  - `close_project(self, prompt)` [L46-L161]
  - `new_project(self)` [L163-L165]
  - `project_audio_reference(self)` [L167-L175]
  - `project_data(self)` [L177-L217]
  - `_write_project_file(self, file_path)` [L219-L282] — *Writes project state dictionary directly to disk.*
  - `prepare_export_directories(self, target_base_dir, default_name, prompt_user)` [L284-L345] — *Resolves project export subfolders (Transcripts, Media).*
  - `get_default_save_directory(self)` [L347-L360] — *Returns target base directory based on preferences and loaded media.*
  - `validate_project_data(self, data)` [L362-L420] — *Return a list of structural project-data problems before saving.*
  - `save_project_as(self)` [L422-L466]
  - `save_project(self, force)` [L468-L556]
  - `open_backup_restore_dialog(self)` [L558-L565] — *Opens the unified Backup & Restore Center dialog.*
  - `load_project_file(self, filename, prompt, preserve_media)` [L567-L677]
  - `load_project(self, filename)` [L679-L693]
  - `open_purge_project_data_dialog(self)` [L695-L707] — *Open the modal dialog allowing users to selectively wipe project data.*
  - `purge_project_data(self, purge_transcript, purge_translations, purge_speakers, purge_stories, purge_media)` [L709-L840] — *Selectively wipe project components while preserving user undo history.*
- **class `ProjectDataPurgeDialog(QDialog)`** (lines 843–991):
  *Modal dialog allowing users to selectively clear/purge project components.*
  - `__init__(self, parent, is_es)` [L846-L853]
  - `_init_ui(self)` [L855-L972]
  - `_set_all_checked(self, checked)` [L974-L976]
  - `_update_purge_button_state(self)` [L978-L982]
  - `get_purge_options(self)` [L984-L991]

### `project_serialization.py` (126 lines)
*Radio & TV Segmenter — Project file serialization and safe decompression.*
- **Functions**:
  - `sanitize_project_data_for_storage(data, parent_key)` [L21-L51] — *Recursively optimize project data before serialization:*
  - `serialize_rtvs_project(data)` [L54-L58] — *Serialize project dictionary into a transparently gzip-compressed payload.*
  - `_decompress_gzip_bounded(raw_bytes, max_bytes)` [L61-L79] — *Decompress a gzip payload in chunks, stopping with a clear error the*
  - `deserialize_rtvs_project(raw_bytes)` [L82-L98] — *Deserialize project payload, transparently handling both gzip-compressed (.rtvs)*
  - `read_rtvs_project_file(file_path)` [L101-L113] — *Transparently read an .rtvs or .json project file from disk (compressed or uncompressed).*
  - `write_rtvs_project_file(file_path, data)` [L116-L126] — *Safely and atomically write a gzip-compressed .rtvs project file.*

### `project_state_mixin.py` (352 lines)
*Radio & TV Story Segmenter — Project State, Undo/Redo & Processing Progress Mixin.*
- **class `ProjectStateMixin`** (lines 18–352):
  *Provides project state snapshotting, undo/redo state restoration, and progress tracking.*
  - `_format_elapsed_time(self, seconds)` [L21-L27]
  - `_format_time_remaining(self, seconds)` [L29-L39]
  - `_get_stage_estimated_duration(self, stage_key)` [L41-L52]
  - `calculate_processing_eta(self, percent)` [L54-L71]
  - `set_processing_stage(self, stage, detail)` [L73-L138]
  - `_on_progress_timer_tick(self)` [L140-L143]
  - `update_processing_progress(self, percent, message)` [L145-L219]
  - `update_processing_stage_summary(self)` [L221-L234]
  - `_clone_transcript_state(transcript)` [L237-L240]
  - `_capture_project_state(self)` [L242-L253] — *Capture all editable project data for the application undo stack.*
  - `get_project_state(self)` [L255-L257] — *Public alias for _capture_project_state for undo history capture.*
  - `_restore_project_state_for_undo(self, state)` [L259-L304] — *Restore a complete editable project state without creating another undo entry.*
  - `_commit_project_state_change(self, before_state, description)` [L306-L315] — *Push a complete project-state undo command after a mutation.*
  - `flush_pending_transcript_undo(self)` [L317-L325] — *Commit a pending grouped text edit before another project action or Ctrl+Z.*
  - `mark_project_dirty(self, reason)` [L327-L340] — *Mark the current project as needing a save and refresh the UI state.*
  - `update_window_title(self)` [L342-L352]

### `prs_shared.py` (1491 lines)
- **class `ProjectMetadataDict(dict)`** (lines 30–45):
  *Dictionary subclass supporting both dict key access and attribute access for project metadata.*
  - `__getattr__(self, name)` [L32-L36]
  - `__setattr__(self, name, value)` [L38-L39]
  - `__delattr__(self, name)` [L41-L45]
- **class `ResizableTextEdit(QWidget)`** (lines 487–634):
  *Multi-line text editor defaulted to ~2 lines of height with a drag handle for vertical expansion.*
  - `__init__(self, text, parent)` [L490-L529]
  - `_grip_press(self, event)` [L531-L539]
  - `_grip_move(self, event)` [L541-L559]
  - `_grip_release(self, event)` [L561-L563]
  - `sizeHint(self)` [L565-L566]
  - `minimumSizeHint(self)` [L568-L569]
  - `toPlainText(self)` [L571-L572]
  - `setPlainText(self, text)` [L574-L575]
  - `setText(self, text)` [L577-L578]
  - `text(self)` [L580-L581]
  - `clear(self)` [L583-L584]
  - `setPlaceholderText(self, text)` [L586-L587]
  - `placeholderText(self)` [L589-L590]
  - `setToolTip(self, tip)` [L592-L593]
  - `setAcceptRichText(self, accept)` [L595-L596]
  - `setTabChangesFocus(self, tab)` [L598-L599]
  - `setEnabled(self, enabled)` [L601-L604]
  - `setReadOnly(self, ro)` [L606-L607]
  - `isReadOnly(self)` [L609-L610]
  - `setFocus(self, *args, **kwargs)` [L612-L613]
  - `hasFocus(self)` [L615-L616]
  - `document(self)` [L618-L619]
  - `textCursor(self)` [L621-L622]
  - `setTextCursor(self, cursor)` [L624-L625]
  - `__getattr__(self, name)` [L627-L630]
  - `textChanged(self)` [L633-L634]
- **class `CollapsibleSection(QWidget)`** (lines 637–804):
  *A clean, collapsible and expandable section widget with a styled toggle button,*
  - `__init__(self, title, parent, is_expanded, subtitle)` [L644-L673]
  - `_update_ui(self)` [L675-L773]
  - `refresh_theme(self)` [L775-L777] — *Re-render header and container styling when application theme changes.*
  - `_on_btn_clicked(self)` [L779-L780]
  - `set_expanded(self, expanded)` [L782-L787]
  - `is_expanded(self)` [L789-L790]
  - `set_title(self, title)` [L792-L794]
  - `set_subtitle(self, subtitle)` [L796-L798]
  - `add_widget(self, widget)` [L800-L801]
  - `add_layout(self, layout)` [L803-L804]
- **class `ExportDialog(QDialog)`** (lines 914–1003):
  - `__init__(self, parent, has_media, default_name)` [L915-L923]
  - `init_ui(self)` [L925-L991]
  - `get_settings(self)` [L993-L1003]
- **class `Story`** (lines 1164–1242):
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L1165-L1210]
  - `to_dict(self)` [L1212-L1224]
  - `from_dict(cls, data)` [L1227-L1242]
- **class `ProjectStateCommand(QUndoCommand)`** (lines 1252–1276):
  *Undo/redo a complete editable project state.*
  - `__init__(self, main_window, before_state, after_state, description)` [L1259-L1267]
  - `undo(self)` [L1269-L1270]
  - `redo(self)` [L1272-L1276]
- **Functions**:
  - `_ensure_runtime_bin_on_path()` [L49-L68] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `platform_seq(key_str)` [L829-L838] — *Return a QKeySequence adapted for macOS vs Windows/Linux.*
  - `get_app_icon()` [L840-L886] — *Return the application QIcon loaded from bundled resources or fallback to empty.*
  - `get_license_file_path(filename)` [L888-L906] — *Return the path to a licensing or notice file, checking bundle and source paths.*
  - `create_fade_curve_pixmap(curve_type, width, height, is_selected, accent_color, bg_color)` [L1047-L1139] — *Render a high-DPI visual curve representation showing the volume attenuation shape.*
  - `create_fade_curve_icon(curve_type, width, height)` [L1142-L1157] — *Return a QIcon containing visual render of the specified audio fade curve.*
  - `read_document_text(path)` [L1314-L1380]
  - `__getattr__(name)` [L1467-L1484] — *Lazy resolver for extracted UI and worker components to eliminate circular import chains.*

### `qt_compat.py` (768 lines)
*Radio & TV Segmenter — Headless Qt / PySide6 Compatibility Engine.*
- **Public Exports (`__all__`)**: MockModule, DummyQt, DummyQSettings, DummyQMessageBox, DummyQApplication, DummyQTimer, DummyQHeaderView, DummyQAbstractItemView, DummyQLineEdit, DummyQComboBox, DummyQDoubleSpinBox, DummyQSpinBox, _ensure_pyside6_fallback
- **class `MockClassMeta(type)`** (lines 17–23):
  *Metaclass allowing class-level attributes, static methods, and constructor calls to mock gracefully.*
  - `__getattr__(cls, attr)` [L20-L23]
- **class `DynamicMock`** (lines 26–304):
  - `__init__(self, *args, **kwargs)` [L27-L36]
  - `column(self)` [L38-L39]
  - `row(self)` [L41-L42]
  - `__call__(self, *args, **kwargs)` [L44-L45]
  - `connect(self, *a, **k)` [L47-L48]
  - `disconnect(self, *a, **k)` [L50-L51]
  - `emit(self, *a, **k)` [L53-L54]
  - `__getattr__(self, attr)` [L56-L57]
  - `isEnabled(self)` [L59-L60]
  - `setEnabled(self, val)` [L62-L63]
  - `isChecked(self)` [L65-L66]
  - `setChecked(self, val)` [L68-L69]
  - `isVisible(self)` [L71-L72]
  - `setVisible(self, val)` [L74-L75]
  - `show(self)` [L77-L78]
  - `hide(self)` [L80-L81]
  - `setWindowModality(self, modality)` [L83-L84]
  - `windowModality(self)` [L86-L87]
  - `accept(self)` [L89-L90]
  - `reject(self)` [L92-L93]
  - `exec_(self)` [L95-L96]
  - `exec(self)` [L98-L99]
  - `__int__(self)` [L101-L102]
  - `__index__(self)` [L104-L105]
  - `__float__(self)` [L107-L108]
  - `__or__(self, other)` [L110-L116]
  - `__ror__(self, other)` [L118-L119]
  - `__and__(self, other)` [L121-L127]
  - `__rand__(self, other)` [L129-L130]
  - `__invert__(self)` [L132-L133]
  - `__xor__(self, other)` [L135-L136]
  - `__contains__(self, item)` [L138-L139]
  - `count(self, *a, **k)` [L141-L142]
  - `__ge__(self, other)` [L144-L148]
  - `__gt__(self, other)` [L150-L154]
  - `__le__(self, other)` [L156-L160]
  - `__lt__(self, other)` [L162-L166]
  - `__iter__(self)` [L168-L169]
  - `__setitem__(self, key, val)` [L171-L174]
  - `__getitem__(self, key)` [L176-L180]
  - `setFlags(self, flags)` [L182-L183]
  - `flags(self)` [L185-L186]
  - `setRowCount(self, count)` [L188-L189]
  - `rowCount(self, *a, **k)` [L191-L192]
  - `setText(self, val)` [L194-L198]
  - `text(self, *a, **k)` [L200-L201]
  - `setData(self, role, val)` [L203-L206]
  - `data(self, role)` [L208-L209]
  - `setItem(self, row, col, item)` [L211-L218]
  - `item(self, row, col)` [L220-L224]
  - `setCurrentCell(self, row, col)` [L226-L228]
  - `currentRow(self)` [L230-L231]
  - `currentColumn(self)` [L233-L234]
  - `setItemDelegateForColumn(self, col, delegate)` [L236-L246]
  - `itemDelegateForColumn(self, col)` [L248-L249]
  - `addTab(self, widget, label)` [L251-L256]
  - `editItem(self, item)` [L258-L277]
  - `findChild(self, cls, *args, **kwargs)` [L279-L286]
  - `installEventFilter(self, filter_obj)` [L288-L291]
  - `removeEventFilter(self, filter_obj)` [L293-L295]
  - `value(self, *args, **kwargs)` [L297-L304]
- **class `MockModule(ModuleType)`** (lines 307–327):
  *Dynamic mock module that automatically manufactures nested mock classes and attributes.*
  - `__init__(self, name)` [L310-L315]
  - `__getattr__(self, name)` [L317-L327]
- **class `_DummyQtMeta(type)`** (lines 330–332):
  - `__getattr__(cls, name)` [L331-L332]
- **class `DummyQt`** (lines 335–368):
  *Mock Qt namespace constants.*
- **class `DummyQEvent(DynamicMock)`** (lines 371–382):
  - `__init__(self, *args, **kwargs)` [L377-L379]
  - `type(self)` [L381-L382]
- **class `DummyQKeyEvent(DynamicMock)`** (lines 385–395):
  - `__init__(self, *args, **kwargs)` [L386-L389]
  - `type(self)` [L391-L392]
  - `key(self)` [L394-L395]
- **class `DummyQSettings`** (lines 398–424):
  *In-memory dictionary-backed QSettings fallback.*
  - `__init__(self, *a, **k)` [L402-L403]
  - `value(self, k, d)` [L405-L406]
  - `setValue(self, k, v)` [L408-L409]
  - `remove(self, k)` [L411-L412]
  - `clear(self)` [L414-L415]
  - `sync(self)` [L417-L418]
  - `beginGroup(self, *a)` [L420-L421]
  - `endGroup(self)` [L423-L424]
- **class `DummyQMessageBox`** (lines 427–445):
  *Non-blocking headless QMessageBox stub.*
  - `information(*args, **kwargs)` [L432-L433]
  - `warning(*args, **kwargs)` [L436-L437]
  - `critical(*args, **kwargs)` [L440-L441]
  - `question(*args, **kwargs)` [L444-L445]
- **class `DummyQApplication`** (lines 448–482):
  *Headless QApplication stub.*
  - `__init__(self, *args, **kwargs)` [L452-L453]
  - `processEvents(cls)` [L456-L463]
  - `sendEvent(cls, receiver, event)` [L466-L474]
  - `instance()` [L477-L478]
  - `topLevelWidgets()` [L481-L482]
- **class `DummyQTimer(DynamicMock)`** (lines 485–498):
  - `__init__(self, *args, **kwargs)` [L486-L488]
  - `start(self, *a, **k)` [L490-L491]
  - `stop(self)` [L493-L494]
  - `singleShot(ms, callback)` [L497-L498]
- **class `DummyQHeaderView`** (lines 501–502):
- **class `DummyQAbstractItemView`** (lines 505–509):
- **class `DummyQStyledItemDelegate(DynamicMock)`** (lines 512–518):
  - `__init__(self, *args, **kwargs)` [L515-L518]
- **class `DummyQLineEdit(DynamicMock)`** (lines 521–535):
  - `__init__(self, *args, **kwargs)` [L524-L526]
  - `setText(self, val)` [L528-L529]
  - `text(self, *a, **k)` [L531-L532]
  - `selectAll(self)` [L534-L535]
- **class `DummyQFont`** (lines 538–542):
  - `__init__(self, *args, **kwargs)` [L541-L542]
- **class `DummySignal`** (lines 545–564):
  - `__init__(self, *args, **kwargs)` [L546-L547]
  - `connect(self, callback)` [L549-L551]
  - `disconnect(self, callback)` [L553-L557]
  - `emit(self, *args, **kwargs)` [L559-L564]
- **class `DummyQComboBox(DynamicMock)`** (lines 567–632):
  - `__init__(self, *args, **kwargs)` [L568-L572]
  - `addItem(self, text, userData)` [L574-L575]
  - `addItems(self, texts)` [L577-L579]
  - `count(self)` [L581-L582]
  - `itemData(self, index, role)` [L584-L587]
  - `itemText(self, index)` [L589-L592]
  - `currentIndex(self)` [L594-L595]
  - `setCurrentIndex(self, index)` [L597-L598]
  - `findData(self, data, role)` [L600-L604]
  - `findText(self, text)` [L606-L611]
  - `currentText(self)` [L613-L615]
  - `currentData(self, role)` [L617-L619]
  - `clear(self)` [L621-L623]
  - `setEnabled(self, val)` [L625-L626]
  - `isEnabled(self)` [L628-L629]
  - `setStyleSheet(self, val)` [L631-L632]
- **class `DummyQDoubleSpinBox`** (lines 635–663):
  - `__init__(self, *args, **kwargs)` [L636-L638]
  - `value(self)` [L640-L641]
  - `setValue(self, v)` [L643-L645]
  - `setRange(self, mn, mx)` [L647-L648]
  - `setSingleStep(self, s)` [L650-L651]
  - `setSuffix(self, s)` [L653-L654]
  - `setEnabled(self, val)` [L656-L657]
  - `isEnabled(self)` [L659-L660]
  - `setStyleSheet(self, val)` [L662-L663]
- **class `DummyQSpinBox`** (lines 666–694):
  - `__init__(self, *args, **kwargs)` [L667-L669]
  - `value(self)` [L671-L672]
  - `setValue(self, v)` [L674-L676]
  - `setRange(self, mn, mx)` [L678-L679]
  - `setSingleStep(self, s)` [L681-L682]
  - `setSuffix(self, s)` [L684-L685]
  - `setEnabled(self, val)` [L687-L688]
  - `isEnabled(self)` [L690-L691]
  - `setStyleSheet(self, val)` [L693-L694]
- **Functions**:
  - `_ensure_pyside6_fallback(force)` [L697-L751] — *Ensures PySide6 modules are importable, installing the zero-dependency mock shim if unavailable.*

### `radio_tv_story_segmenter_worker.py` (226 lines)
*Radio & TV Story Segmenter — AI Background Subprocess Worker Facade.*
- **Public Exports (`__all__`)**: emit, emit_hello, _patch_av_open, _clamp_diarization_thread_env, _setup_windows_dll_directories, _safe_tensor_from_numpy, get_optimal_transcription_threads, get_app_data_dir_pure, get_models_storage_dir_pure, is_onnx_model_available, transcribe_parakeet_onnx, probe_audio_language, transcribe, normalize_audio_for_diarization, configure_optimal_pytorch_threads, _normalize_expected_speakers, _normalize_speaker_labels, _sensitivity_distance_threshold, fast_cluster_ahc, apply_clustering_patches, run_vad_two_pass, assign_short_segments_to_centroids, _calculate_embedding_for_interval, _diarize_solo_fast_path, _get_wespeaker_model, extract_embeddings_batched, run_transcript_guided_diarization, diarize, is_real_speech, detect_story_boundaries, main
- **Functions**:
  - `main(argv)` [L117-L222]

### `roadmap_manager.py` (259 lines)
*roadmap_manager.py — Automated Roadmap & N-1 Sliding-Window Management Engine*
- **class `RoadmapManager`** (lines 45–205):
  - `__init__(self, roadmap_path)` [L46-L49]
  - `load(self)` [L51-L54]
  - `save(self)` [L56-L57]
  - `get_sections_info(self)` [L59-L102] — *Parse TOC and identify release sections.*
  - `audit(self)` [L104-L148] — *Audit roadmap.txt against N-1 sliding window and status tracking invariants.*
  - `set_item_status(self, item_num, status)` [L150-L173] — *Synchronously update the status checkbox for an item (e.g. '2.1', '3.2') to [x], [-], or [ ].*
  - `sync_current_version(self, target_version)` [L175-L197] — *Synchronize the current release version in roadmap.txt to target_version or prs_shared.py.*
  - `count_item_statuses(self)` [L199-L205] — *Count completed, in-progress, and planned items in the roadmap.*
- **Functions**:
  - `get_current_app_version()` [L23-L43] — *Extract PROJECT_VERSION from core_utils.py or prs_shared.py.*
  - `main()` [L207-L256]

### `runtime_manager.py` (1037 lines)
- **class `RuntimeManager`** (lines 363–1037):
  *Manages isolated Python virtual environments for ML features with auto-upgrade support.*
  - `__init__(self, base_dir)` [L366-L377]
  - `get_last_error(self)` [L379-L381] — *Returns the most recent detailed error message from environment setup or execution.*
  - `get_env_dir(self, feature_name)` [L383-L384]
  - `get_manifest_path(self, feature_name)` [L386-L387]
  - `_get_raw_executable(self, feature_name)` [L389-L393]
  - `get_executable(self, feature_name)` [L395-L401] — *Returns the path to the python executable inside the target feature environment if valid.*
  - `resolve_target_python(self, target_version)` [L403-L435] — *Finds a matching Python binary on the host system for building the environment.*
  - `bundled_uv_path(self)` [L438-L466] — *Return the uv binary shipped with the application across Windows, macOS, and Linux, or None if unavailable.*
  - `ensure_uv(self, progress_cb)` [L468-L538] — *Locates bundled or system uv, or automatically downloads standalone uv for the active OS/arch.*
  - `_get_uv_env(self)` [L540-L554] — *Constructs environment dictionary with managed Python directory for uv.*
  - `_find_extracted_python(self, target_version)` [L556-L585] — *Scan managed python directory for a working extracted python binary.*
  - `_download_standalone_python(self, target_version, progress_cb)` [L587-L624] — *Directly download and extract standalone CPython distribution without symlinks.*
  - `ensure_managed_python(self, target_version, progress_cb)` [L626-L682] — *Provision a private Python runtime with uv when the host has no matching Python.*
  - `kill_all_subprocesses(self)` [L684-L686] — *Force terminate any lingering isolated worker subprocesses.*
  - `remove_environment(self, feature_name)` [L688-L728] — *Remove an isolated feature environment without touching its models.*
  - `prune_cuda_artifacts(env_dir)` [L731-L787] — *Strip unused CUDA/cuDNN packages, heavy C++ dev headers, test suites,*
  - `get_runtime_executable(self, feature_name, progress_cb)` [L789-L793] — *Ensure and return the executable for an isolated feature runtime.*
  - `get_plugin_requirements(self, feature_name, plugin_dir)` [L795-L824] — *Read requirements-runtime.txt from plugin directory if available, fallback to ENV_CONFIGS.*
  - `is_env_up_to_date(self, feature_name)` [L826-L849] — *Verifies if environment exists and matches current config version and specs.*
  - `write_manifest(self, feature_name, python_used, packages)` [L851-L862] — *Writes configuration metadata upon successful environment creation.*
  - `ensure_environment(self, feature_name, force_rebuild, progress_cb, plugin_dir, cancel_event)` [L864-L1037] — *Creates or upgrades an isolated feature environment.*
- **Functions**:
  - `register_process(proc)` [L41-L49] — *Register an active Popen process for teardown monitoring.*
  - `unregister_process(proc)` [L52-L60] — *Remove completed process from tracking.*
  - `kill_all_subprocesses()` [L63-L78] — *Force terminate any lingering isolated worker subprocesses.*
  - `_robust_urlretrieve(url, destination, timeout)` [L81-L123] — *Download url to destination with explicit timeout, SSL certificate verification, and atomic write.*
  - `_emit_progress(progress_cb, percent, message)` [L126-L139] — *Safely emit progress supporting both 1-argument (message) and 2-argument (percent, message) callbacks.*
  - `_run_pip_with_progress(cmd, feature_name, packages, progress_cb, env, creationflags, start_pct, end_pct, cancel_event)` [L142-L257] — *Execute pip or uv pip with real-time output monitoring and progress reporting.*
  - `detect_nvidia_gpu()` [L329-L343] — *Best-effort check for a usable NVIDIA GPU on this machine, so the*
  - `_remove_macos_quarantine(target_path)` [L346-L360] — *Strip Gatekeeper com.apple.quarantine attribute on macOS for standalone executables.*

### `scripts/generate_pyi_stubs.py` (214 lines)
*generate_pyi_stubs.py — Automated Interface Typing Stub (.pyi) Generator.*
- **class `StubTransformer(ast.NodeTransformer)`** (lines 48–87):
  *AST transformer that strips function bodies and replaces defaults with Ellipsis.*
  - `visit_FunctionDef(self, node)` [L51-L57]
  - `visit_AsyncFunctionDef(self, node)` [L59-L65]
  - `visit_ClassDef(self, node)` [L67-L87]
- **Functions**:
  - `generate_stub_source(py_path)` [L90-L128] — *Generate clean .pyi stub content from a Python source file using AST.*
  - `get_large_modules(root, line_threshold)` [L131-L146] — *Find all application Python modules exceeding the line threshold.*
  - `generate_stub_file(py_path)` [L149-L154] — *Generate and write a .pyi stub next to the source file.*
  - `main()` [L157-L210]

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

### `scripts/modular_audit.py` (570 lines)
*scripts/modular_audit.py — AST Decomposition Suggester & Modular Budget Guard.*
- **class `ModuleStructure`** (lines 53–226):
  *Detailed structural metrics extracted from a Python module.*
  - `__init__(self, file_path)` [L56-L73]
  - `_analyze(self)` [L75-L149]
  - `_extract_class_info(self, node, lines)` [L151-L179]
  - `_extract_func_info(self, node, lines)` [L181-L190]
  - `_classify_domain(name, bases, method_names)` [L193-L226] — *Classifies a class or function into a logical domain based on naming and signatures.*
- **class `DecompositionPlan`** (lines 233–395):
  *Proposed modular decomposition plan for a monolithic source file.*
  - `__init__(self, structure)` [L236-L244]
  - `_classify_method_domain(m_name)` [L247-L257]
  - `_build_plan(self)` [L259-L362]
  - `render_markdown_blueprint(self)` [L364-L395]
- **Functions**:
  - `scan_repository(root_dir)` [L402-L414] — *Scans all Python modules in the repository, excluding build/venv directories.*
  - `print_audit_report(structures, warn_threshold, hard_ceiling, sort_by)` [L417-L458] — *Prints a formatted terminal table showing modularity compliance.*
  - `check_budget_guard(structures, hard_ceiling, warn_threshold, exempt_paths)` [L461-L494] — *Programmatic budget check suitable for test runner and CI pipelines.*
  - `main()` [L497-L566]

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

### `shortcuts/manager.py` (208 lines)
*shortcuts/manager.py — Core ShortcutsManager coordinator and QSettings integration.*
- **class `ShortcutsManager(QObject)`** (lines 19–208):
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
  - `apply_to_window(self, window)` [L138-L208] — *Update shortcuts on all QAction and QShortcut objects on MainWindow,*

### `shortcuts/schema.py` (858 lines)
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

### `speaker_dialog_refinement_mixin.py` (546 lines)
*Radio & TV Story Segmenter — Speaker Dialog Refinement & Turn Merging Mixin.*
- **class `SpeakerDialogRefinementMixin`** (lines 45–546):
  *Mixin for competitive speaker run refinement, word synchronization, and turn merging.*
  - `refine_speaker_run_between_confirmed_anchors(self, start_idx, end_idx, spk_a, spk_b)` [L48-L128]
  - `prompt_refine_speaker_run(self, start_idx, end_idx)` [L130-L302]
  - `sync_segment_words(self, segment, new_text, word_formats)` [L304-L396]
  - `merge_speakers(self, source_speaker, target_speaker)` [L398-L465]
  - `open_speaker_manager_dialog(self, modal)` [L467-L493]
  - `merge_contiguous_speaker_segments(self)` [L495-L546]

### `speaker_dialogs.py` (782 lines)
*speaker_dialogs.py — Dialogs for speaker renaming, turn assignment, and cluster management.*
- **Public Exports (`__all__`)**: ChangeSpeakerDialog, SpeakerManagerDialog, SpeakerNameDelegate
- **class `ChangeSpeakerDialog(QDialog)`** (lines 23–82):
  *Dialog prompting whether to apply a speaker name change to all instances or a single turn.*
  - `__init__(self, current_name, target_name, seg_idx, parent)` [L26-L70]
  - `_on_all(self)` [L72-L74]
  - `_on_subsequent(self)` [L76-L78]
  - `_on_single(self)` [L80-L82]
- **class `SpeakerNameDelegate(QStyledItemDelegate)`** (lines 96–163):
  *Delegate for inline double-click editing of speaker names with Tab progression.*
  - `__init__(self, dialog)` [L99-L101]
  - `createEditor(self, parent, option, index)` [L103-L128]
  - `eventFilter(self, editor, event)` [L130-L163]
- **class `SpeakerManagerDialog(QDialog)`** (lines 166–782):
  *Manager dialog for inspecting, aliasing, and merging detected speaker clusters.*
  - `__init__(self, parent)` [L169-L221]
  - `_is_gui_thread(self)` [L223-L231] — *Check whether execution is on the main Qt GUI thread.*
  - `_get_audio_source_url(self)` [L233-L248]
  - `_get_sample_duration(self)` [L250-L258] — *Retrieve the configured speaker sample preview duration in seconds (default 3.0s).*
  - `_find_speaker_sample_range(self, speaker_name)` [L260-L288] — *Resolve a clean representative utterance (start_s, duration_s) for the speaker cluster.*
  - `_play_speaker_sample(self, speaker_name)` [L290-L333] — *Play a non-blocking 3-second sample for the specified speaker without altering timeline state.*
  - `_stop_sample_playback(self)` [L335-L349] — *Cease any active sample audio playback and reset UI button text.*
  - `_on_preview_playback_state_changed(self, state)` [L351-L354]
  - `_on_preview_media_status_changed(self, status)` [L356-L362]
  - `_init_ui(self)` [L364-L454]
  - `_schedule_debounced_save(self)` [L456-L459] — *Schedule a debounced full-project save 500ms after the last speaker rename.*
  - `_flush_debounced_save(self)` [L461-L466] — *Immediately execute any pending debounced project save.*
  - `_populate(self)` [L468-L593]
  - `_start_inline_edit_on_row(self, row)` [L595-L603]
  - `_on_table_item_changed(self, item)` [L605-L627]
  - `_rename_speaker(self, current_name, raw_id)` [L629-L637]
  - `_apply_speaker_rename(self, current_name, target, raw_id)` [L639-L681]
  - `_merge_speaker_into(self, source_name)` [L683-L710]
  - `_on_quick_merge(self)` [L712-L737]
  - `_on_open_voice_profiles(self)` [L739-L743]
  - `reject(self)` [L745-L748]
  - `accept(self)` [L750-L753]
  - `closeEvent(self, event)` [L755-L758]
  - `toggle_float_mode(self, pinned)` [L760-L776] — *Toggle whether the non-modal floating window stays pinned on top of other windows.*
  - `changeEvent(self, event)` [L778-L782]
- **Functions**:
  - `_is_gui_thread()` [L85-L93] — *Check whether execution is on the main Qt GUI thread.*

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

### `speaker_palette.py` (148 lines)
*Accessible adaptive speaker color palette for Radio & TV Story Segmenter.*
- **class `SpeakerColor`** (lines 16–23):
- **class `SpeakerColorAssigner`** (lines 118–148):
  *Maintains sequential appearance-order color assignments for a document/project.*
  - `__init__(self)` [L121-L123]
  - `get_index(self, speaker)` [L125-L132]
  - `get_color(self, speaker)` [L134-L136]
  - `get_hex(self, speaker, dark_mode, high_contrast)` [L138-L140]
  - `get_rgb(self, speaker, dark_mode)` [L142-L144]
  - `get_pdf_rgb(self, speaker)` [L146-L148]
- **Functions**:
  - `_hex_to_rgb(hex_str)` [L26-L30]
  - `_rgb_to_pdf(rgb)` [L33-L34]
  - `_make_speaker_color(name, light_hex, dark_hex, hc_hex)` [L37-L49]
  - `get_speaker_index(speaker, index)` [L65-L89] — *Derive a deterministic 0..7 index from an explicit index, speaker label, or hash.*
  - `get_speaker_color(speaker, index)` [L92-L95] — *Return the SpeakerColor dataclass instance for the given speaker name/index.*
  - `get_speaker_hex(speaker, dark_mode, high_contrast, index)` [L98-L103] — *Return hex color code ('#RRGGBB') adapted to the current display theme or export mode.*
  - `get_speaker_rgb(speaker, dark_mode, index)` [L106-L109] — *Return (R, G, B) integer tuple in 0..255 range.*
  - `get_speaker_pdf_rgb(speaker, index)` [L112-L115] — *Return (r, g, b) float tuple in 0.0..1.0 range suitable for PDF content streams.*

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

### `story_crud_mixin.py` (814 lines)
*Radio & TV Story Segmenter — Story CRUD & Timeline Selection Mixin.*
- **class `StoryCrudMixin`** (lines 46–814):
  *Mixin providing story list UI management, CRUD operations, and fade handling.*
  - `refresh_story_list(self)` [L49-L92]
  - `handle_new_story_started(self, start_time, end_time)` [L94-L104]
  - `handle_new_story_updated(self, start_time, end_time)` [L106-L118]
  - `handle_drag_story_region(self, index, start_time, end_time)` [L120-L132]
  - `audition_story(self, index)` [L134-L157]
  - `handle_drag_finished(self)` [L159-L188]
  - `update_selected_story(self)` [L190-L248]
  - `delete_selected_story(self)` [L250-L281]
  - `get_current_interaction_time(self, for_boundary)` [L283-L301]
  - `set_selected_story_start(self)` [L303-L348]
  - `set_selected_story_end(self)` [L350-L395]
  - `add_selection_to_story(self)` [L397-L508]
  - `play_transcript_selection(self)` [L510-L529]
  - `select_all_stories(self)` [L531-L538]
  - `handle_timeline_selection_range_changed(self, start_time, end_time)` [L540-L583]
  - `add_story_from_range(self, start_time, end_time)` [L585-L619]
  - `add_story_from_active_selection(self)` [L621-L638]
  - `open_story_fades_dialog(self, story_index)` [L640-L682]
  - `apply_fades_to_selected_stories(self, fade_in, fade_out, fade_curve)` [L684-L717]
  - `remove_fades_from_selected_stories(self)` [L719-L720]
  - `set_fade_curve_for_selected_stories(self, curve_type)` [L722-L745]
  - `open_story_metadata_dialog(self, target_story_index, modal)` [L747-L780]
  - `_notify_floating_dialogs(self)` [L782-L796] — *Refresh any open non-modal export, metadata, or speaker management floating windows after main window edits.*
  - `_close_floating_dialogs(self, persist_drafts)` [L798-L814] — *Persist drafts and close any active non-modal floating windows on project close or shutdown.*

### `story_detection_processing.py` (206 lines)
*Story boundary detection processing mixin for Radio & TV Story Segmenter.*
- **class `StoryDetectionProcessingMixin`** (lines 19–205):
  - `start_auto_detect_stories(self)` [L20-L83]
  - `auto_detect_progress(self, message, percent)` [L85-L86]
  - `auto_detect_finished(self, new_stories)` [L88-L159]
  - `auto_detect_error(self, message)` [L161-L205]

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

### `story_metadata_dialog.py` (307 lines)
*Radio & TV Story Segmenter — Universal Story & Post Metadata Architecture.*
- **class `StoryMetadataDialog(QDialog)`** (lines 66–307):
  *Universal non-modal dialog for inspecting and editing post and story metadata across the project.*
  - `__init__(self, parent, main_window, target_story_index)` [L69-L105]
  - `_init_ui(self)` [L107-L207]
  - `targets_list(self)` [L210-L212] — *Alias returning the post selector list widget for caller backward compatibility.*
  - `target_items(self)` [L215-L217] — *Alias returning the post items list for caller backward compatibility.*
  - `save_all_to_project(self)` [L219-L237] — *Commit all configured metadata into Project/Story data structures and sync UI.*
  - `rebuild_target_items(self)` [L239-L242] — *Rebuild post items in tab widget.*
  - `_on_save_clicked(self)` [L244-L248]
  - `_on_close_clicked(self)` [L250-L252]
  - `_on_save_and_close(self)` [L254-L255]
  - `toggle_float_mode(self, pinned)` [L257-L273] — *Toggle whether the non-modal floating window stays pinned on top of other windows.*
  - `refresh_from_main_window(self, target_story_index)` [L275-L295] — *Synchronize stories, excerpts, and transcript changes from the main window.*
  - `changeEvent(self, event)` [L297-L300]
  - `done(self, r)` [L302-L307]
- **Functions**:
  - `_get_metadata_theme_mode()` [L47-L49] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast').*
  - `generate_story_excerpt(text, max_words)` [L52-L63] — *Generate a clean, readable excerpt of up to max_words from transcript text.*

### `story_model.py` (262 lines)
*Radio & TV Story Segmenter — Story Model, Boundaries & Undo Commands.*
- **class `Story`** (lines 67–151):
  *Represents a segmented radio or TV news/broadcast story with boundaries and fade metadata.*
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L70-L112]
  - `duration(self)` [L115-L116]
  - `to_dict(self)` [L118-L130]
  - `from_dict(cls, data)` [L133-L148]
  - `__repr__(self)` [L150-L151]
- **class `SetStoriesCommand(QUndoCommand)`** (lines 179–204):
  *Undo/redo command for wholesale updates to the project's story list.*
  - `__init__(self, main_window, old_stories, new_stories, description)` [L182-L186]
  - `undo(self)` [L188-L195]
  - `redo(self)` [L197-L204]
- **class `StoryBoundaryChangeCommand(QUndoCommand)`** (lines 207–244):
  *Discrete undo/redo command for story boundary adjustments (start/end times).*
  - `__init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description)` [L210-L217]
  - `undo(self)` [L219-L223]
  - `redo(self)` [L225-L229]
  - `_sync_ui(self, start, end)` [L231-L244]
- **class `SelectStoriesCommand(QUndoCommand)`** (lines 247–262):
  *Undo/redo command for active story selection index changes.*
  - `__init__(self, main_window, old_selection, new_selection, description)` [L250-L254]
  - `undo(self)` [L256-L258]
  - `redo(self)` [L260-L262]
- **Functions**:
  - `get_fade_curve_factors(progress, curve)` [L54-L64] — *Calculate gain factor (0.0 to 1.0) given normalized fade progress (0.0 to 1.0).*
  - `validate_story_boundaries(start, end, media_duration)` [L154-L163] — *Clamp and ensure start < end within [0.0, media_duration].*
  - `check_story_overlap(stories)` [L166-L176] — *Return pairs of story indices that temporally overlap.*

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

### `sync.py` (161 lines)
*2-Way Synchronization Engine for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_current_version()` [L25-L34] — *Read PROJECT_VERSION from core_utils.py.*
  - `run_cmd(cmd, check)` [L37-L39] — *Run a subprocess command and stream output.*
  - `cmd_status()` [L42-L71] — *Display current git branch status and unpushed/unpulled commits.*
  - `cmd_pull()` [L74-L99] — *Pull latest changes from GitHub, then sync preview and symbol index.*
  - `cmd_push(commit_msg)` [L102-L137] — *Stage all changes, commit, and push to GitHub.*
  - `main()` [L140-L157]

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

### `theme_qss.py` (330 lines)
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

### `timeline_context_menus.py` (108 lines)
*Context menu builders and event handlers for the timeline canvas.*
- **Functions**:
  - `show_timeline_context_menu(canvas, global_pos, pos_x)` [L10-L64] — *Display the primary right-click context menu on the timeline canvas.*
  - `show_selection_context_menu(canvas, global_pos)` [L67-L108] — *Display the range selection context menu on the timeline canvas.*

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

### `timeline_overview_widget.py` (372 lines)
*Timeline overview bar, mini-map navigator, and resize handle widgets.*
- **class `TimelineResizeHandle(QWidget)`** (lines 13–73):
  *Visual drag-handle at the bottom of the timeline allowing vertical resizing.*
  - `__init__(self, target_widget, parent)` [L16-L24]
  - `paintEvent(self, event)` [L26-L40]
  - `mousePressEvent(self, event)` [L42-L49]
  - `mouseMoveEvent(self, event)` [L51-L60]
  - `mouseReleaseEvent(self, event)` [L62-L73]
- **class `TimelineOverviewBar(QWidget)`** (lines 76–372):
  *Interactive navigation overview pill below the timeline with drag-to-zoom edge handles.*
  - `__init__(self, canvas, parent, tokens)` [L83-L101]
  - `get_pill_rect(self)` [L103-L111]
  - `_hit_test(self, pos_x)` [L113-L124]
  - `paintEvent(self, event)` [L126-L195]
  - `mousePressEvent(self, event)` [L197-L243]
  - `mouseMoveEvent(self, event)` [L245-L307]
  - `mouseReleaseEvent(self, event)` [L309-L323]
  - `leaveEvent(self, event)` [L325-L328]
  - `dragEnterEvent(self, event)` [L330-L337]
  - `dragMoveEvent(self, event)` [L339-L346]
  - `dragLeaveEvent(self, event)` [L348-L349]
  - `dropEvent(self, event)` [L351-L360]
  - `setRange(self, min_val, max_val)` [L362-L363]
  - `setPageStep(self, step)` [L365-L366]
  - `setSingleStep(self, step)` [L368-L369]
  - `setValue(self, val)` [L371-L372]

### `timeline_painter.py` (419 lines)
*Timeline canvas rendering engine, waveform drawing, and paint pipeline.*
- **Functions**:
  - `render_waveform_buffer(canvas, width, height)` [L32-L195] — *Render background waveform peaks and video thumbnail strip onto an offscreen QPixmap.*
  - `paint_timeline_canvas(canvas, painter, event)` [L198-L419] — *Execute full timeline paint pipeline onto the canvas QPainter.*

### `timeline_snap.py` (119 lines)
*Timeline snapping algorithms, edge detection, and collision hit-testing.*
- **Functions**:
  - `snap_time(canvas, raw_time, exclude_story_idx, width, pixel_threshold)` [L7-L58] — *Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels.*
  - `find_edge_at_pos(canvas, pos_x, width)` [L61-L71] — *Determine if pos_x is hovering over a story segment start or end boundary edge.*
  - `find_fade_handle_at_pos(canvas, pos_x, pos_y, width)` [L74-L101] — *Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks.*
  - `find_story_at_time(canvas, time)` [L104-L113] — *Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping.*
  - `is_near_playhead(canvas, pos_x, width)` [L116-L119] — *Check if pos_x is within grab distance of the active playhead cursor.*

### `timeline_widgets.py` (974 lines)
*Radio & TV Story Segmenter — Timeline Ruler, Track Views, Playhead, Overview & Canvas Widgets.*
- **class `TimelineCanvas(QWidget)`** (lines 60–854):
  - `__init__(self, parent, tokens)` [L80-L170]
  - `set_is_video(self, is_video)` [L172-L175]
  - `set_background_generation_active(self, task_name, active)` [L177-L196] — *Set generation state for 'waveform' or 'thumbnails'.*
  - `_activate_background_banner(self)` [L198-L203]
  - `_update_background_status_text(self)` [L205-L218]
  - `dragEnterEvent(self, event)` [L220-L227]
  - `dragMoveEvent(self, event)` [L229-L236]
  - `dragLeaveEvent(self, event)` [L238-L239]
  - `dropEvent(self, event)` [L241-L249]
  - `set_audio_filename(self, filename)` [L251-L254]
  - `set_duration(self, duration)` [L256-L264]
  - `set_position(self, position)` [L266-L269]
  - `set_playing_state(self, is_playing)` [L271-L272]
  - `ensure_position_visible(self, target_time)` [L274-L297]
  - `set_transcript_selection_range(self, start, end)` [L299-L304]
  - `set_stories(self, stories, selected_indices)` [L306-L310]
  - `set_waveform_peaks(self, peaks, levels)` [L312-L323]
  - `set_timeline_views(self, show_waveform, show_thumbnails)` [L325-L329]
  - `set_video_thumbnails(self, thumbnails)` [L331-L338]
  - `set_skip_seconds(self, seconds)` [L340-L341]
  - `visible_duration(self)` [L343-L344]
  - `clamp_scroll_offset(self)` [L346-L349]
  - `time_to_x(self, time_val, width)` [L351-L354]
  - `x_to_time(self, x_val, width)` [L356-L358]
  - `snap_time(self, raw_time, exclude_story_idx, width, pixel_threshold)` [L360-L361]
  - `find_edge_at_pos(self, pos_x, width)` [L363-L364]
  - `find_fade_handle_at_pos(self, pos_x, pos_y, width)` [L368-L369]
  - `find_story_at_time(self, time)` [L371-L372]
  - `is_near_playhead(self, pos_x, width)` [L374-L375]
  - `set_zoom(self, new_zoom, center_x, focus_time)` [L377-L403]
  - `resizeEvent(self, event)` [L405-L407]
  - `wheelEvent(self, event)` [L409-L459]
  - `mousePressEvent(self, event)` [L461-L545]
  - `mouseMoveEvent(self, event)` [L547-L673]
  - `mouseReleaseEvent(self, event)` [L675-L745]
  - `_show_timeline_context_menu(self, global_pos, pos_x)` [L747-L748]
  - `_show_selection_context_menu(self, global_pos)` [L750-L751]
  - `keyPressEvent(self, event)` [L753-L834]
  - `set_thumbnail_position(self, position)` [L836-L840]
  - `render_waveform_buffer(self, width, height)` [L842-L843]
  - `paintEvent(self, event)` [L846-L854]
- **class `TimelineWidget(QWidget)`** (lines 857–972):
  - `__init__(self, parent, tokens)` [L860-L897]
  - `set_is_video(self, is_video)` [L899-L901]
  - `set_background_generation_active(self, task_name, active)` [L903-L905]
  - `dragEnterEvent(self, event)` [L907-L914]
  - `dragMoveEvent(self, event)` [L916-L923]
  - `dragLeaveEvent(self, event)` [L925-L926]
  - `dropEvent(self, event)` [L928-L936]
  - `update_scrollbar_range(self)` [L938-L947]
  - `update_scrollbar_from_canvas(self, offset)` [L949-L957]
  - `update_canvas_from_scrollbar(self, val)` [L959-L969]
  - `__getattr__(self, name)` [L971-L972]

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

### `transcript_editor_dialogs.py` (231 lines)
*transcript_editor_dialogs.py - Dialog and floating toolbar components for transcript editing.*
- **class `FindReplaceDialog(QDialog)`** (lines 42–147):
  *Modeless find-and-replace dialog for QTextEdit / InteractiveTranscriptEdit.*
  - `__init__(self, text_edit, parent)` [L45-L80]
  - `get_flags(self)` [L82-L86]
  - `find_next(self)` [L88-L100]
  - `find_prev(self)` [L102-L115]
  - `replace(self)` [L117-L125]
  - `replace_all(self)` [L127-L147]
- **class `TranscriptSelectionBubble(QFrame)`** (lines 150–231):
  *Floating quick-action toolbar on transcript selection (Milestone 3.12).*
  - `__init__(self, parent)` [L159-L226]
  - `_emit_comment(self)` [L228-L231]

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

### `transcript_story.py` (847 lines)
*Radio & TV Segmenter v3.9.52-beta — transcript story responsibilities.*
- **Public Exports (`__all__`)**: TranscriptStoryMixin, Story, SetStoriesCommand, SelectStoriesCommand, StoryBoundaryChangeCommand, StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin, ChangeSpeakerDialog, VoiceProfileMatchDialog, StoryFadesDialog, SpeakerManagerDialog, FADE_CURVE_TABLES, get_fade_curve_factors
- **class `TranscriptStoryMixin(StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin)`** (lines 63–846):
  - `render_transcript(self)` [L64-L463]
  - `on_transcript_selection_changed(self)` [L465-L497]
  - `on_transcript_text_changed(self)` [L499-L655]
  - `transcript_clicked(self, url)` [L657-L673]
  - `edit_segment_comment_dialog(self, seg_idx, sel_text, start_char, end_char, t_range, covered_indices)` [L675-L756]
  - `add_comment_from_selection(self)` [L760-L803]
  - `delete_segment_comment(self, seg_idx)` [L805-L825]
  - `toggle_comments_panel(self)` [L827-L830]
  - `toggle_show_comments(self, checked)` [L832-L838]
  - `toggle_comment_highlights(self, checked)` [L842-L846]

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

### `transcription_processing.py` (579 lines)
*Transcription background process management for Radio & TV Story Segmenter.*
- **class `TranscriptionProcessingMixin`** (lines 32–578):
  - `start_transcription(self)` [L33-L210]
  - `on_transcription_output(self, force_flush)` [L212-L296]
  - `on_transcription_stderr(self)` [L298-L321] — *Route the worker's stderr (third-party library warnings, C-level*
  - `_handle_live_streaming_segment(self, segment)` [L323-L362] — *Append an incoming live transcript chunk directly to the view without rebuilding the map.*
  - `on_transcription_process_finished(self, exit_code, exit_status)` [L364-L387]
  - `on_transcription_process_error(self, error)` [L389-L396]
  - `cleanup_transcription_process(self)` [L398-L415]
  - `transcription_progress(self, message, percent)` [L417-L418]
  - `transcription_finished(self, transcript)` [L420-L533]
  - `transcription_error(self, message)` [L535-L578]

### `translation.py` (923 lines)
*Radio & TV Segmenter — Local Translation Mixin.*
- **class `TranslationEnvSetupWorker(QObject)`** (lines 35–92):
  *Background worker that sets up the isolated translation runtime environment.*
  - `__init__(self, plugin_dir, runtime_mgr)` [L40-L45]
  - `cancel(self)` [L47-L49]
  - `run(self)` [L51-L92]
- **class `TranslationMixin`** (lines 132–923):
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
  - `_on_translation_finished(self, translated_transcript, translation_key)` [L812-L864] — *Handle successful translation results.*
  - `_on_translation_cancelled(self, results, translation_key)` [L866-L878] — *Handle translation worker cancellation.*
  - `_on_translation_error(self, error_message)` [L880-L914] — *Handle translation worker failures.*
  - `_on_translation_thread_finished(self)` [L916-L919] — *Clean up thread reference.*
  - `_translation_thread_finished(self)` [L921-L923] — *Alias for _on_translation_thread_finished.*
- **Functions**:
  - `_translation_worker_class()` [L22-L25] — *Load the translation worker only when the translation plugin is installed.*
  - `_translation_runtime_entry_path(app)` [L95-L121]
  - `_translation_runtime_manager(app)` [L123-L130]

### `ui_dialog_launchers.py` (337 lines)
*Dialog launchers and external modal helpers for Radio & TV Story Segmenter.*
- **class `UiDialogLaunchersMixin`** (lines 25–335):
  *Mixin providing dialog launcher methods for shortcuts, benchmarks, diagnostics, and plugins.*
  - `open_project_dialog(self)` [L27-L42] — *Prompt user to open a project file (*.rtvs).*
  - `open_find_dialog(self)` [L44-L50] — *Display the Find and Replace dialog window.*
  - `show_shortcuts_dialog(self)` [L53-L234] — *Display a searchable, dynamically generated reference table of all active shortcuts.*
  - `show_diagnostic_test_bench(self)` [L236-L248] — *Open the interactive System Diagnostic Test Bench dialog.*
  - `show_performance_benchmark(self)` [L250-L262] — *Open the interactive System Performance & Speed Benchmark dialog.*
  - `open_plugins_manager(self)` [L264-L271] — *Open the Plugin Manager dialog to enable, disable, or inspect plugins.*
  - `open_id3_tag_editor(self, mp3_path)` [L273-L285] — *Open the ID3 Tag Editor dialog to view and edit MP3 audio metadata.*
  - `open_youtube_publish_dialog(self, story)` [L288-L311] — *Open the YouTube video publishing dialog or export view from the YouTube plugin.*
  - `open_wordpress_publish_dialog(self, story)` [L313-L329] — *Open the WordPress direct publish dialog from the WordPress plugin.*
  - `open_loudness_normalization_dialog(self)` [L331-L335] — *Open the Audio Loudness Normalization & Telemetry modal dialog.*

### `ui_layout.py` (1060 lines)
*Radio & TV Segmenter — UI Layout & Menu Construction Mixin.*
- **class `UiLayoutMixin(UiMenusMixin, UiDialogLaunchersMixin)`** (lines 57–1056):
  *Mixin class providing UI construction, menu assembly, and UI event binding.*
  - `build_ui(self)` [L59-L733] — *Build and assemble all central widgets, layouts, and panels.*
  - `filter_transcript_search(self, target)` [L735-L752] — *Highlight and focus next occurrence of search term in transcript text view.*
  - `toggle_transcript_editing_mode(self, *args, **kwargs)` [L754-L776] — *Toggle between Viewing Mode (navigation/click-to-seek) and Editing Mode (text editing).*
  - `_on_transcript_editing_mode_changed(self, is_editing)` [L778-L813] — *Respond to changes in transcript edit vs view mode.*
  - `_sync_format_toolbar_buttons(self)` [L815-L835]
  - `_on_toolbar_split_speaker(self)` [L837-L844]
  - `_apply_transcript_font_scale(self, scale, persist)` [L846-L870] — *Apply a transcript-only font scale and optionally persist it.*
  - `_on_font_size_combo_changed(self, index)` [L872-L876]
  - `adjust_transcript_font_size(self, direction)` [L878-L880] — *Increase or decrease transcript font size by one 5% step.*
  - `reset_transcript_font_size(self)` [L882-L884] — *Restore the default transcript font size.*
  - `update_story_list_height(self)` [L886-L901] — *Size the story list to fit the current number of stories, leaving space for metadata and export fields.*
  - `auto_generate_selected_story_excerpt(self)` [L903-L948] — *Auto-generate an excerpt from the story transcript text for the currently selected story.*
  - `_on_story_excerpt_text_changed(self)` [L950-L967] — *Synchronize excerpt edits from the inline editor into story metadata.*
  - `toggle_maximize_stories_panel(self)` [L969-L1022] — *Toggle maximize/restore of the stories panel across the full application window.*
  - `setup_plugin_story_extensions(self)` [L1024-L1046] — *Populate plugin-provided widgets in the story panel.*
  - `notify_story_selection_to_plugins(self, selected_story)` [L1048-L1056] — *Notify all enabled plugins when the active story selection changes.*

### `ui_menus.py` (809 lines)
*Main application menu bar and action assembly for Radio & TV Story Segmenter.*
- **class `PersistentMenu(QMenu)`** (lines 50–73):
  *A QMenu subclass that stays open when checkable toggle options are activated,*
  - `addMenu(self, *args, **kwargs)` [L54-L59]
  - `mouseReleaseEvent(self, event)` [L61-L73]
- **class `UiMenusMixin`** (lines 78–808):
  *Mixin providing menu construction, action shortcut wiring, and menu synchronization.*
  - `build_menus(self)` [L80-L652] — *Construct the main application menu bar and associated keyboard shortcuts.*
  - `apply_user_shortcuts(self)` [L654-L659] — *Rebind all menu actions and application shortcuts according to user preferences.*
  - `_refresh_recent_projects_menu(self)` [L661-L689] — *Update recent projects submenu items based on user settings store.*
  - `_check_external_dependencies(self)` [L691-L705] — *Check bundled media tools and record actionable diagnostics.*
  - `_sync_undo_redo_actions(self)` [L707-L716] — *Synchronize undo/redo action states with QUndoStack.*
  - `_remember_directory(self, path)` [L718-L728] — *Persist directory of chosen file to improve user file dialog experience.*
  - `update_processing_menu_status(self)` [L731-L754] — *Update label annotations on Tools actions reflecting pipeline stage completion.*
  - `refresh_plugin_menus(self)` [L757-L808] — *Dynamically populate plugin export actions, tools menu actions, and core UI controls.*

### `updater.py` (1460 lines)
*Update manager and GitHub release installer for Radio & TV Segmenter.*
- **class `CheckUpdateWorker(QThread)`** (lines 649–707):
  - `__init__(self, repo, parent, channel)` [L655-L661]
  - `run(self)` [L663-L707]
- **class `DownloadUpdateWorker(QThread)`** (lines 772–857):
  - `__init__(self, download_url, file_name, parent, release_info)` [L777-L782]
  - `cancel(self)` [L784-L785]
  - `run(self)` [L787-L857]
- **class `CheckUpdateDialog(QDialog)`** (lines 860–1424):
  - `__init__(self, parent, auto_start)` [L861-L892]
  - `_build_ui(self)` [L894-L1029]
  - `_on_channel_changed(self, index)` [L1031-L1038]
  - `start_check(self)` [L1040-L1060]
  - `_on_releases_loaded(self, releases)` [L1062-L1097]
  - `_on_version_selected(self, index)` [L1099-L1103]
  - `_display_release(self, release_info)` [L1105-L1191]
  - `_on_up_to_date(self, current_ver, remote_tag)` [L1193-L1205]
  - `_on_update_available(self, release_info, asset_info, is_newer)` [L1207-L1208]
  - `_on_check_error(self, message)` [L1210-L1216]
  - `_handle_primary_action(self)` [L1218-L1232]
  - `_confirm_downgrade(self, target_version)` [L1234-L1249] — *Modal Warning Dialog when selecting a version lower than installed PROJECT_VERSION.*
  - `start_download(self)` [L1251-L1281]
  - `_on_download_progress(self, percent, downloaded, total, speed_str)` [L1283-L1287]
  - `_on_download_finished(self, file_path)` [L1289-L1296]
  - `_on_download_error(self, message)` [L1298-L1317]
  - `_install_and_restart(self)` [L1319-L1406]
  - `_open_github_release(self)` [L1408-L1410]
  - `_handle_close(self)` [L1412-L1424]
- **class `UpdaterMixin`** (lines 1427–1460):
  - `check_for_updates(self, interactive)` [L1428-L1434]
  - `trigger_silent_update_check(self)` [L1436-L1460]
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

### `waveform_envelope.py` (55 lines)
*Waveform envelope data structures, downsampling pyramids, and cache helpers.*
- **class `WaveformEnvelope(list)`** (lines 14–19):
  *Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels.*
  - `__init__(self, iterable, levels)` [L17-L19]
- **Functions**:
  - `build_waveform_pyramid(peaks)` [L22-L55] — *Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.*

### `worker_asr_engines.py` (839 lines)
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
  - `probe_audio_language(audio_file, sample_duration, preferred_model)` [L509-L609] — *Run a fast language detection probe using faster-whisper's mel feature extractor.*
  - `transcribe(audio_file, model_name, initial_prompt, beam_size)` [L612-L839] — *Transcribe media file using either Sherpa-ONNX or Faster-Whisper.*

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


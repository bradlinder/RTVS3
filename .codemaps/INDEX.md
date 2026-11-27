# Repository Symbol Index & API Map

> Generated: 2026-11-27 15:12:09 | Total Files: 210
> Use `python scripts/generate_symbol_index.py --outline <file>` for exact line numbers.

## Modules Overview

| Module | Lines | Summary | Primary Classes / Functions |
| :--- | :---: | :--- | :--- |
| `RadioTVSegmenter.py` | 686 | Radio & TV Segmenter — v3.10.30-beta | `MainWindow`, `main()` |
| `audio_normalization.py` | 474 | Radio & TV Story Segmenter — Audio Loudness Probing & Nor... | `LoudnessReport`, `parse_ebur128_summary()`, `probe_media_duration_seconds()`, `probe_media_loudness()` *(+2 more)* |
| `audio_normalization_worker.py` | 89 | Background QThread worker for non-blocking EBU R128 loudn... | `AudioLoudnessProbeWorker` |
| `background_workers.py` | 911 | Radio & TV Story Segmenter — Background Worker Threads & ... | `StoryAutoDetectWorker`, `WaveformWorker`, `get_waveform_peak_cache_path()`, `read_waveform_peak_cache()` *(+2 more)* |
| `backup_manager.py` | 622 | Unified State Serialization & Local Backup & Restore Engine. | `compute_data_checksum()`, `serialize_preferences()`, `serialize_keyboard_shortcuts()`, `serialize_glossary()` *(+7 more)* |
| `batch_dialog.py` | 702 | Radio & TV Story Segmenter — Batch Processing Dialog & Dr... | `BatchFileListWidget`, `BatchProcessingDialog` |
| `benchmark.py` | 216 | Radio & TV Story Segmenter — Performance & Speed Benchmar... | `run_cli_benchmark()`, `main()` |
| `benchmark_dialog.py` | 674 | benchmark_dialog.py - PySide6 Graphical Benchmark Dialog ... | `create_benchmark_dialog()` |
| `benchmark_engine.py` | 903 | benchmark_engine.py - Core High-Precision Performance Ben... | `BenchmarkEngine` |
| `benchmark_models.py` | 457 | benchmark_models.py - Benchmark Data Models, Audio Genera... | `BenchmarkMetric`, `ProcessingEstimates`, `get_app_data_dir()`, `get_candidate_sample_audio_paths()` *(+9 more)* |
| `bootstrap.py` | 385 | Install-safe startup environment configuration for Radio ... | `NullWriter`, `init_null_streams_and_hf_env()`, `patch_av_open()`, `app_data_dir()` *(+7 more)* |
| `build_installer.py` | 457 | Build the installable Radio & TV Segmenter application wi... | `find_tool()`, `run()`, `provision_optional_runtime_tools()`, `sync_installer_scripts()` *(+3 more)* |
| `bump_version.py` | 513 | bump_version.py — Automated Version Synchronization Engine | `normalize_version()`, `get_current_version()`, `compute_bump()`, `detect_modified_plugins()` *(+3 more)* |
| `cache_manager.py` | 685 | Radio & TV Segmenter — Cache management, disk usage scann... | `ClearCacheDialog`, `register_active_thumbnail_dir()`, `unregister_active_thumbnail_dir()`, `get_active_thumbnail_dirs()` *(+3 more)* |
| `comment_widgets.py` | 350 | comment_widgets.py - Range-Anchored Comments Panel & Comm... | `CommentEditorDialog`, `CommentCardWidget`, `CommentsPanel` |
| `core_utils.py` | 776 | Radio & TV Segmenter — Core filesystem, path, timing, and... | `StoryVocabulary`, `safe_process_events()`, `get_active_theme_mode()`, `apply_window_titlebar_theme()` *(+24 more)* |
| `diagnostic_batch_tests.py` | 19 | Diagnostic batch and editing workflow test bench facade. | `DiagnosticBatchTestsMixin` |
| `diagnostic_cloud_and_system_tests.py` | 22 | Diagnostic cloud, voice, and system runtime test bench fa... | `DiagnosticCloudAndSystemTestsMixin` |
| `diagnostic_core_tests.py` | 969 | Diagnostic test bench suite component. | `DiagnosticCoreTestsMixin` |
| `diagnostic_dialog.py` | 388 | PySide6 Graphical Test Bench Dialog for Radio & TV Story ... | `create_diagnostic_dialog()` |
| `diagnostic_editor_tests.py` | 19 | Diagnostic editor and find-replace test bench facade. | `DiagnosticEditorTestsMixin` |
| `diagnostic_export_tests.py` | 25 | Diagnostic export test bench facade aggregating modular t... | `DiagnosticExportTestsMixin` |
| `diagnostic_helpers.py` | 155 | Helper fixtures, module resolvers, and DiagnosticItem for... | `DiagnosticItem`, `generate_synthetic_wav()` |
| `diagnostic_loudness_tests.py` | 406 | Radio & TV Story Segmenter — Diagnostic Loudness Normaliz... | `DiagnosticLoudnessTestsMixin` |
| `diagnostic_selector.py` | 202 | Smart Diagnostic Test Selector for Radio & TV Story Segme... | `get_modified_files()`, `has_git_changes()`, `detect_changed_tokens()`, `select_diagnostic_items()` |
| `diagnostic_speaker_cleanup_tests.py` | 994 | Diagnostic tests for Phase 2 features: minimum story leng... | `DiagnosticSpeakerCleanupTestsMixin` |
| `diagnostic_wordpress_tests.py` | 109 | Diagnostic tests for WordPress PublishPress Author mappin... | `DiagnosticWordPressTestsMixin` |
| `diagnostics/__init__.py` | 28 | Modular diagnostic test mixin components for the RTVS Tes... | - |
| `diagnostics/batch_export_tests.py` | 469 | Batch processing, drag-and-drop ingestion, PDF, and DAW e... | `DiagnosticBatchExportTestsMixin` |
| `diagnostics/cloud_storage_tests.py` | 592 | Plugin interface, project persistence, cache management, ... | `DiagnosticCloudStorageTestsMixin` |
| `diagnostics/editing_workflow_tests.py` | 590 | Fades, translation routing, speaker dialog flow, story bo... | `DiagnosticEditingWorkflowTestsMixin` |
| `diagnostics/editor_guides_and_daw_tests.py` | 500 | Find-replace, user guides viewer, and REAPER DAW companio... | `DiagnosticEditorGuidesAndDawTestsMixin` |
| `diagnostics/editor_story_ui_tests.py` | 852 | Story transcript highlighting, smart copy, duration & hea... | `DiagnosticEditorStoryUiTestsMixin` |
| `diagnostics/export_pipeline.py` | 485 | Multi-format export pipeline, scope slicing, and audio ca... | `DiagnosticExportPipelineMixin` |
| `diagnostics/export_wordpress_core.py` | 830 | WordPress export scope, content formatting, and YouTube e... | `DiagnosticExportWordPressCoreMixin` |
| `diagnostics/export_wordpress_media.py` | 752 | WordPress featured image metadata and Castos podcast diag... | `DiagnosticExportWordPressMediaMixin` |
| `diagnostics/export_wordpress_upload.py` | 668 | WordPress multi-story upload, Gutenberg hygiene, and audi... | `DiagnosticExportWordPressUploadMixin` |
| `diagnostics/system_runtime_tests.py` | 446 | System runtime, updater, theme, packaging, roadmap, and m... | `DiagnosticSystemRuntimeTestsMixin` |
| `diagnostics/voice_and_media_tests.py` | 595 | Voice profile matching, waveform peak cache, and playback... | `DiagnosticVoiceAndMediaTestsMixin` |
| `diagnostics/youtube_import_cache_tests.py` | 350 | Diagnostic tests for YouTube Episode Import, yt-dlp runne... | `DiagnosticYouTubeImportCacheTestsMixin` |
| `dialogs.py` | 433 | Radio & TV Story Segmenter — Audio Loudness Normalization... | `AudioLoudnessNormalizationDialog` |
| `diarization_processing.py` | 772 | Speaker diarization process management for Radio & TV Sto... | `DiarizationProcessingMixin` |
| `embedded_guides.py` | 28 | Radio & TV Story Segmenter — Built-In Embedded User Guide... | `get_embedded_guide()`, `get_all_embedded_guide_ids()` |
| `export/__init__.py` | 67 | Export package for Radio & TV Story Segmenter. | - |
| `export/audio.py` | 287 | Radio & TV Story Segmenter — Broadcast Audio Rendering & ... | `build_audio_fade_filter()`, `export_audio_track()`, `extract_audio_clip()` |
| `export/daw.py` | 37 | DAW and NLE timeline interchange formatters for Radio & T... | - |
| `export/dialog.py` | 1716 | Unified Export Dialog for Radio & TV Story Segmenter. | `UnifiedExportDialog` |
| `export/docx.py` | 541 | Word (.docx) export formatter for Radio & TV Story Segmen... | `inject_native_comments_to_docx()`, `create_story_docx()` |
| `export/pdf.py` | 369 | PDF export formatter for Radio & TV Story Segmenter. | `TranscriptPdfWriter` |
| `export/reorder_dialog.py` | 255 | export/reorder_dialog.py — Dialog for customizing the dis... | `ReorderExportDestinationsDialog`, `get_export_destinations_order()`, `save_export_destinations_order()` |
| `export/story_selector.py` | 412 | Checkable story/segment selection sidebar for UnifiedExpo... | `ExportStorySelectorSidebar` |
| `export/subtitles.py` | 222 | Subtitle and timeline formatters for Radio & TV Story Seg... | `format_subtitle_timestamp()`, `format_srt_timestamp()`, `format_vtt_timestamp()`, `format_cue_timestamp()` *(+9 more)* |
| `export/timeline.py` | 873 | Multi-Platform Timeline and DAW Interchange Engine for Ra... | `reaper_color_from_hex()`, `format_edl_timestamp()`, `build_timeline_clips()`, `generate_reaper_project()` *(+8 more)* |
| `export_dialogs.py` | 476 | Radio & TV Story Segmenter — Export Dialogs & Scope Selec... | `ExportDialogsMixin`, `show_export_completion_dialog()` |
| `export_documents.py` | 796 | Radio & TV Story Segmenter — Document, Transcript & Timel... | `ExportDocumentsMixin` |
| `export_media_clipper.py` | 338 | Radio & TV Story Segmenter — Media Clipper & Audio Track ... | `ExportMediaClipperMixin` |
| `export_story_pipeline.py` | 968 | Radio & TV Story Segmenter — Story & Full Episode Export ... | `ExportStoryPipelineMixin` |
| `glossary_dialog.py` | 490 | Custom Vocabulary & Glossary Dialog. | `GlossaryDialog` |
| `gpu_acceleration.py` | 276 | Radio & TV Segmenter v1.1.1 — optional GPU acceleration r... | `GpuAccelerationInstallWorker`, `GpuAccelerationMixin` |
| `id3_editor.py` | 704 | ID3 Tag Editor module for Radio & TV Segmenter. | `ID3TagEditorDialog`, `read_id3_tags()`, `write_id3_tags()` |
| `installer/build_tools/__init__.py` | 50 | Modular build utilities for Radio & TV Segmenter PyInstal... | - |
| `installer/build_tools/config.py` | 214 | Build configuration constants and CLI argument parser. | `parse_build_args()` |
| `installer/build_tools/env_checks.py` | 188 | Environment validation, external tool resolution, and sub... | `exe_name()`, `find_tool()`, `check_cpu_only_torch()`, `torch_windows_binary_flags()` *(+1 more)* |
| `installer/build_tools/packaging.py` | 368 | Bundle pruning, plugin archive packaging, runtime tools, ... | `provision_optional_runtime_tools()`, `prune_unneeded_bundled_files()`, `sync_installer_scripts()`, `compile_windows_installer()` *(+1 more)* |
| `installer/pyinstaller/torch_dll_hook.py` | 70 | PyInstaller runtime hook for Windows ML/native DLL resolu... | - |
| `media_batch.py` | 1905 | Radio & TV Segmenter v1.1.1 — media batch responsibilities. | `MediaBatchMixin` |
| `model_cleanup_dialog.py` | 468 | Manage Models dialog and shared runtime cleanup helpers f... | `ModelCleanupDialog`, `format_directory_size()` |
| `model_install_workers.py` | 189 | Radio & TV Segmenter — Model Download and Installation Ba... | `WhisperModelInstallWorker`, `DiarizationModelInstallWorker`, `get_diarization_model_dir()`, `is_diarization_model_available()` |
| `model_management.py` | 621 | Radio & TV Segmenter v1.1.1 — model management responsibi... | `_DummyTranslationWorker`, `ModelManagementMixin` |
| `playback_controller.py` | 630 | Radio & TV Story Segmenter — Media Player Transport & Pla... | `PlaybackControllerMixin` |
| `playback_preferences.py` | 815 | Radio & TV Story Segmenter — Playback Preferences & Appli... | `PlaybackPreferencesMixin` |
| `plugin_base.py` | 225 | Radio & TV Segmenter — Plugin Base Interfaces and Manifest. | `PluginManifest`, `BasePlugin`, `ExportDestination` |
| `plugins/__init__.py` | 6 | Radio & TV Segmenter — Plugin Architecture Package. | - |
| `plugins/base.py` | 6 | Radio & TV Segmenter — Plugin Base Interfaces and Manifes... | - |
| `plugins/github_dialog.py` | 580 | GitHub plugins browser and installer dialog with multi-se... | `GitHubPluginsDialog` |
| `plugins/installer_workers.py` | 293 | Background QThread workers for querying, downloading, and... | `GitHubPluginsWorker`, `GitHubDownloadWorker`, `GitHubBatchDownloadWorker`, `get_official_plugins_catalog()` |
| `plugins/manager.py` | 657 | Radio & TV Segmenter — Plugin Manager and Discovery Engine. | `PluginManager`, `parse_plugin_version_tuple()`, `is_newer_plugin_version()` |
| `plugins/manager_dialog.py` | 532 | Plugin and Add-On Manager Dialog for inspecting, enabling... | `PluginManagerDialog` |
| `plugins/translation/__init__.py` | 9 | Language Translation Plugin for Radio & TV Segmenter. | - |
| `plugins/translation/plugin.py` | 58 | Language Translation Plugin for Radio & TV Segmenter. | `Plugin` |
| `plugins/translation/runtime_entry.py` | 49 | CLI entry point for the isolated translation runtime. | `emit()`, `main()` |
| `plugins/translation/support.py` | 176 | Small dependency-light helpers shared by the translation ... | `configure_ssl_certificates()`, `get_app_data_dir()`, `get_legacy_models_storage_dirs()`, `get_models_storage_dir()` *(+2 more)* |
| `plugins/translation/worker.py` | 678 | Translation plugin worker. | `TranslationWorker` |
| `plugins/version_utils.py` | 30 | Version parsing and semantic comparison utilities for the... | `parse_plugin_version_tuple()`, `is_newer_plugin_version()` |
| `plugins/wordpress/__init__.py` | 6 | WordPress Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/wordpress/authors.py` | 143 | Pure-Python helpers for WordPress user and PublishPress A... | `extract_checked_author_ids()`, `is_author_item_selected()`, `resolve_selected_author_names()`, `count_selected_authors()` *(+1 more)* |
| `plugins/wordpress/castos.py` | 725 | Seriously Simple Podcasting (Castos) integration for Word... | `format_castos_duration()`, `build_castos_post_meta()`, `copy_podcast_meta()`, `fetch_castos_feeds()` *(+5 more)* |
| `plugins/wordpress/client.py` | 2169 | WordPress Plugin — Client, Credential Storage, and Upload... | `WordPressClient`, `WordPressSettingsDialog`, `WordPressPreferencesPage`, `format_rich_text_to_html()` *(+6 more)* |
| `plugins/wordpress/episode_lookup.py` | 498 | Headless WordPress episode lookup, REST parsing, slug/dat... | `extract_slug_or_id_from_url()`, `clean_html_to_plain_excerpt()`, `build_story_slug()`, `normalize_wp_iso_date()` *(+3 more)* |
| `plugins/wordpress/episode_updater.py` | 56 | Backward-compatible facade for WordPress Existing Episode... | - |
| `plugins/wordpress/episode_updater_ui.py` | 570 | Qt UI panels and dialog for WordPress existing episode lo... | `LoadWordPressEpisodeDialog`, `sync_wp_audio_checkbox_label()`, `load_episode_updater_from_post()`, `apply_fetched_post_to_tab()` *(+2 more)* |
| `plugins/wordpress/export_destination.py` | 880 | WordPress Export Destination for UnifiedExportDialog. | `WordPressExportDestination`, `WordPressPostMetadataDialog` |
| `plugins/wordpress/plugin.py` | 112 | WordPress Publisher Plugin for Radio & TV Segmenter. | `Plugin` |
| `plugins/wordpress/pub_date_picker.py` | 338 | Non-focus-stealing click-to-drop-down calendar & time pic... | `_PublicationDatePickerPopup`, `PublicationDateLineEdit` |
| `plugins/wordpress/wordpress_dialog.py` | 28 | Backward-compatible facade for legacy WordPress dialog im... | `generate_wp_excerpt()` |
| `plugins/wordpress/wp_post_builder.py` | 456 | Post item builder, transcript slicing, and video frame ex... | `capture_video_frame()`, `get_primary_text_slice()`, `build_wp_post_items()`, `sync_featured_image_meta()` |
| `plugins/wordpress/wp_publish_dialog.py` | 524 | WordPress single-story publish dialog with featured image... | `WordPressPublishDialog` |
| `plugins/wordpress/wp_tab_widget.py` | 997 | WordPress export tab configuration widget and preview con... | `WordPressExportTabWidget` |
| `plugins/wordpress/wp_thumb_ui.py` | 399 | UI presentation controller for WordPress Featured Image c... | `ClickableThumbnailLabel`, `FeaturedImageLightboxDialog`, `set_preview_pixmap()`, `clear_preview_pixmap()` *(+4 more)* |
| `plugins/wordpress/wp_thumbnail_defaults.py` | 445 | Headless YouTube-source featured image defaults, thumbnai... | `extract_youtube_id_headless()`, `get_youtube_thumbnail_cache_path()`, `get_youtube_source_info()`, `resolve_post_youtube_video_id()` *(+6 more)* |
| `plugins/wordpress/wp_ui_builder.py` | 996 | UI layout construction and widget setup for WordPressExpo... | `setup_wp_tab_ui()`, `show_wp_excluded_placeholder()`, `hide_wp_excluded_placeholder()`, `include_excluded_item_in_export()` *(+1 more)* |
| `plugins/wordpress/wp_workers.py` | 106 | Background QThread worker for publishing individual WordP... | `WordPressPublishWorker`, `YouTubeThumbnailFetchWorker` |
| `plugins/wordpress/youtube_embed.py` | 672 | YouTube Video Embed helpers, Gutenberg iframe generator, ... | `extract_youtube_video_id()`, `build_youtube_embed_block()`, `setup_wp_youtube_ui()`, `update_youtube_status_label()` *(+4 more)* |
| `plugins/youtube/__init__.py` | 9 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | - |
| `plugins/youtube/export_destination.py` | 618 | YouTube Export Destination for UnifiedExportDialog with Z... | `YouTubeExportTabWidget`, `YouTubeExportDestination`, `capture_video_frame()` |
| `plugins/youtube/guide_dialog.py` | 147 | Interactive Assisted Upload Guide Dialog for YouTube Studio. | `YouTubeAssistedUploadGuideDialog` |
| `plugins/youtube/plugin.py` | 291 | YouTube Video Publisher Plugin for Radio & TV Segmenter. | `YouTubeSettingsDialog`, `Plugin`, `capture_video_frame()` |
| `plugins/youtube/yt_dlp_runner.py` | 871 | Headless yt-dlp runtime provisioner, URL parser, metadata... | `extract_youtube_id_strict()`, `normalize_quality_preset()`, `normalize_cookie_browser()`, `get_format_selector_for_preset()` *(+18 more)* |
| `plugins/youtube/yt_import_dialog.py` | 754 | Qt Dialogs for importing existing YouTube videos, re-down... | `LoadYouTubeEpisodeDialog`, `populate_project_from_youtube_import()`, `open_yt_dlp_updater_dialog()`, `prompt_load_youtube_episode_dialog()` *(+1 more)* |
| `plugins/youtube/yt_import_workers.py` | 250 | Background QThread workers for yt-dlp provisioning, YouTu... | `YtDlpInstallWorker`, `YouTubeProbeWorker`, `YouTubeDownloadWorker` |
| `preferences_dialog.py` | 911 | Radio & TV Story Segmenter — Preferences Modal Dialog. | `PreferencesDialogMixin` |
| `preferences_reset.py` | 684 | Radio & TV Story Segmenter — Preferences Reset & Factory ... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_reset_dialog.py` | 643 | Radio & TV Segmenter — Preferences reset and factory defa... | `RestoreSelectedSettingsDialog`, `PreferencesResetMixin` |
| `preferences_tab_daw.py` | 138 | preferences_tab_daw.py — External Audio & Video Editors P... | `build_external_editors_tab()` |
| `preferences_tabs_core.py` | 626 | Radio & TV Story Segmenter — Preferences Modal Core Tab B... | `build_general_tab()`, `build_shortcuts_tab()`, `build_audio_hardware_tab()`, `build_updates_tab()` *(+2 more)* |
| `preferences_tabs_media.py` | 731 | Radio & TV Story Segmenter — Preferences Modal Media & Wo... | `build_playback_timeline_tab()`, `build_detection_tab()`, `build_batch_tab()`, `build_cleanup_tab()` *(+1 more)* |
| `preview_manager.py` | 270 | AI Studio Web Preview Manager for Radio & TV Story Segmen... | `get_project_version()`, `restore_preview()`, `sync_version()`, `main()` |
| `process_lifecycle.py` | 191 | Radio & TV Segmenter — Subprocess tracking and OS-level j... | `init_child_process_job_isolation()`, `bind_subprocess_to_job()`, `register_process()`, `unregister_process()` *(+2 more)* |
| `processing.py` | 1273 | Radio & TV Segmenter v3.3.29 — processing responsibilities. | `RuntimeSetupWorker`, `ProcessingMixin` |
| `project_data_purge_dialog.py` | 169 | Modal dialog allowing users to selectively clear/purge pr... | `ProjectDataPurgeDialog` |
| `project_export.py` | 458 | Radio & TV Story Segmenter — Unified Project & Media Expo... | `ProjectExportMixin` |
| `project_lifecycle.py` | 994 | Radio & TV Story Segmenter — Project Lifecycle & Persiste... | `ProjectLifecycleMixin` |
| `project_serialization.py` | 126 | Radio & TV Segmenter — Project file serialization and saf... | `sanitize_project_data_for_storage()`, `serialize_rtvs_project()`, `deserialize_rtvs_project()`, `read_rtvs_project_file()` *(+1 more)* |
| `project_state_mixin.py` | 364 | Radio & TV Story Segmenter — Project State, Undo/Redo & P... | `ProjectStateMixin` |
| `prs_shared.py` | 1495 |  | `ProjectMetadataDict`, `ResizableTextEdit`, `CollapsibleSection`, `ExportDialog` *(+8 more)* |
| `qt_compat.py` | 962 | Radio & TV Segmenter — Headless Qt / PySide6 Compatibilit... | `MockClassMeta`, `DynamicMock`, `MockModule`, `_DummyQtMeta` *(+23 more)* |
| `radio_tv_story_segmenter_worker.py` | 226 | Radio & TV Story Segmenter — AI Background Subprocess Wor... | `main()` |
| `reaper_bridge.py` | 953 | reaper_bridge.py — REAPER DAW Companion Bridge & Inter-Pr... | `get_reaper_ipc_paths()`, `reaper_color_from_hex()`, `get_reaper_clip_notes_and_markers()`, `build_reaper_cue_payload()` *(+10 more)* |
| `remote_media_cache.py` | 610 | Headless Managed Remote Media Cache for YouTube and WordP... | `RemoteMediaCacheManager`, `format_bytes_human()`, `get_remote_media_cache_dir()`, `is_path_inside_cache()` *(+2 more)* |
| `remote_media_cache_dialog.py` | 447 | Qt Dialog for inspecting and managing the Managed Remote ... | `ManageCachedMediaDialog`, `get_configured_cache_cap_gb()`, `find_redownload_provider()`, `reattach_downloaded_media_to_project()` *(+1 more)* |
| `roadmap_manager.py` | 259 | roadmap_manager.py — Automated Roadmap & N-1 Sliding-Wind... | `RoadmapManager`, `get_current_app_version()`, `main()` |
| `runtime_manager.py` | 1037 |  | `RuntimeManager`, `register_process()`, `unregister_process()`, `kill_all_subprocesses()` *(+1 more)* |
| `scripts/capture_guide_screenshots.py` | 152 | Programmatic headless screenshot generator for RTVS3 user... | `MockCaptureMainWindow`, `capture_widget()`, `main()` |
| `scripts/dev_check.py` | 338 | scripts/dev_check.py - Ultra-Fast Pre-Flight Development ... | `check_syntax()`, `check_typing_stubs()`, `check_preview_sync()`, `check_modular_budget()` *(+3 more)* |
| `scripts/generate_pyi_stubs.py` | 214 | generate_pyi_stubs.py — Automated Interface Typing Stub (... | `StubTransformer`, `generate_stub_source()`, `get_large_modules()`, `generate_stub_file()` *(+1 more)* |
| `scripts/generate_symbol_index.py` | 380 | generate_symbol_index.py — Fast AST Symbol Indexer & Repo... | `parse_function_signature()`, `analyze_file()`, `scan_repository()`, `generate_index_markdown()` *(+4 more)* |
| `scripts/log_summary.py` | 150 | log_summary.py — Compact Error & Exception Extraction Engine | `is_project_frame()`, `extract_log_summary()`, `main()` |
| `scripts/modular_audit.py` | 770 | scripts/modular_audit.py — AST Decomposition Suggester & ... | `ModuleStructure`, `DecompositionPlan`, `scan_repository()`, `print_audit_report()` *(+4 more)* |
| `sentence_boundaries.py` | 140 | Context-aware sentence-boundary and abbreviation detectio... | `is_ambiguous_abbreviation()`, `is_non_terminal_abbreviation()`, `is_sentence_end()` |
| `shortcuts/__init__.py` | 26 | shortcuts package — Modular Keyboard Shortcuts Management... | - |
| `shortcuts/definitions.py` | 22 | shortcuts/definitions.py — Shortcut definitions and schem... | - |
| `shortcuts/dialogs.py` | 623 | shortcuts/dialogs.py — Preferences page for keyboard shor... | `KeyboardShortcutsPage` |
| `shortcuts/manager.py` | 215 | shortcuts/manager.py — Core ShortcutsManager coordinator ... | `ShortcutsManager` |
| `shortcuts/schema.py` | 951 | shortcuts/schema.py — Shortcut definitions, dataclass mod... | `ShortcutDef`, `get_platform_default()`, `format_sequence_display()`, `normalize_sequence_string()` |
| `shortcuts/widgets.py` | 151 | shortcuts/widgets.py — Interactive Key Sequence Recorder ... | `KeySequenceRecorderEdit` |
| `shortcuts_manager.py` | 30 | Shortcuts Manager for Radio & TV Story Segmenter (Compati... | - |
| `snapshot_manager.py` | 276 | Snapshot Manager for Radio & TV Story Segmenter | `load_manifest()`, `save_manifest()`, `get_current_project_version()`, `ensure_git_repo()` *(+4 more)* |
| `speaker_dialog_refinement_mixin.py` | 555 | Radio & TV Story Segmenter — Speaker Dialog Refinement & ... | `SpeakerDialogRefinementMixin` |
| `speaker_dialogs.py` | 897 | speaker_dialogs.py — Dialogs for speaker renaming, turn a... | `ChangeSpeakerDialog`, `SpeakerNameDelegate`, `SpeakerManagerDialog` |
| `speaker_editing_mixin.py` | 637 | Radio & TV Story Segmenter — Speaker Label, Renaming & Se... | `SpeakerEditingMixin` |
| `speaker_identity.py` | 260 | Radio & TV Segmenter | `VoiceMatch`, `cosine_similarity()`, `normalize_vector()`, `centroid()` *(+3 more)* |
| `speaker_name_cleanup_dialog.py` | 295 | speaker_name_cleanup_dialog.py — Modal review dialog for ... | `SpeakerNameCleanupDialog` |
| `speaker_name_matcher.py` | 583 | speaker_name_matcher.py — Headless phonetic and fuzzy cle... | `SpeakerNameCandidate`, `is_generic_speaker_label()`, `is_generic_role_label()`, `preserve_case_replace()` *(+7 more)* |
| `speaker_palette.py` | 148 | Accessible adaptive speaker color palette for Radio & TV ... | `SpeakerColor`, `SpeakerColorAssigner`, `get_speaker_index()`, `get_speaker_color()` *(+3 more)* |
| `speaker_profiles.py` | 249 | speaker_profiles.py — Persistent Station Voice Profile Ma... | `StationVoiceProfile`, `StationVoiceProfileStore` |
| `speaker_profiles_dialog.py` | 425 | speaker_profiles_dialog.py — UI management dialog for per... | `ManageVoiceProfilesDialog` |
| `spellcheck_helper.py` | 779 | spellcheck_helper.py — Headless Tier 1 Offline Spellcheck... | `SpellIssue`, `OfflineSpellChecker`, `is_pyspellchecker_available()`, `match_case()` *(+5 more)* |
| `spellcheck_widgets.py` | 697 | spellcheck_widgets.py — Inline Qt Spellcheck Highlighting... | `SpellCheckHighlighter`, `_LineEditSpellOverlay`, `SpellCheckController`, `add_word_to_glossary()` *(+2 more)* |
| `story_crud_mixin.py` | 931 | Radio & TV Story Segmenter — Story CRUD & Timeline Select... | `StoryCrudMixin` |
| `story_detect_dialog.py` | 333 | Lightweight two-step confirmation and threshold-override ... | `DetectStoriesSettingsDialog`, `StandaloneDetectStoriesDialog` |
| `story_detection_processing.py` | 290 | Story boundary detection processing mixin for Radio & TV ... | `StoryDetectionProcessingMixin` |
| `story_fades_dialog.py` | 215 | story_fades_dialog.py — Dialog for fine-grained audio fad... | `StoryFadesDialog` |
| `story_metadata_dialog.py` | 313 | Radio & TV Story Segmenter — Universal Story & Post Metad... | `StoryMetadataDialog`, `generate_story_excerpt()` |
| `story_model.py` | 273 | Radio & TV Story Segmenter — Story Model, Boundaries & Un... | `Story`, `SetStoriesCommand`, `StoryBoundaryChangeCommand`, `SelectStoriesCommand` *(+3 more)* |
| `story_widgets.py` | 592 | Radio & TV Story Segmenter — Story Sidebar Widgets, Item ... | `FadeCurveVisualSelector`, `StoryFadesChangeCommand`, `SetStoriesCommand`, `StoryBoundaryChangeCommand` *(+3 more)* |
| `sync.py` | 161 | 2-Way Synchronization Engine for Radio & TV Story Segmenter. | `get_current_version()`, `run_cmd()`, `cmd_status()`, `cmd_pull()` *(+2 more)* |
| `terminology.py` | 882 | Model-independent terminology and glossary support. | `split_source_variants()`, `format_source_variants()`, `parse_glossary()`, `expand_glossary_rules()` *(+11 more)* |
| `theme_preferences.py` | 606 | Radio & TV Story Segmenter — Theme Preferences & Styling ... | `ThemePreferencesMixin` |
| `theme_qss.py` | 330 | Targeted QSS for the Radio & TV Segmenter visual design s... | - |
| `theme_tokens.py` | 307 | Theme Tokens for Radio & TV Story Segmenter. | `ThemeTokens`, `theme_tokens_for_mode()` |
| `thumbnail_workers.py` | 523 | Video thumbnail cache helpers, network-share detection, a... | `VideoThumbnailCacheLoader`, `VideoThumbnailWorker`, `is_network_path()`, `normalize_thumbnail_density()` *(+6 more)* |
| `timeline_context_menus.py` | 197 | Context menu builders and event handlers for the timeline... | `show_timeline_context_menu()`, `show_selection_context_menu()` |
| `timeline_overview.py` | 351 | Timeline Resize Handle and Overview Navigation Bar widgets. | `TimelineResizeHandle`, `TimelineOverviewBar` |
| `timeline_overview_widget.py` | 372 | Timeline overview bar, mini-map navigator, and resize han... | `TimelineResizeHandle`, `TimelineOverviewBar` |
| `timeline_painter.py` | 436 | Timeline canvas rendering engine, waveform drawing, and p... | `render_waveform_buffer()`, `paint_timeline_canvas()` |
| `timeline_snap.py` | 195 | Timeline snapping algorithms, edge detection, and collisi... | `snap_time()`, `find_edge_at_pos()`, `find_fade_handle_at_pos()`, `find_story_at_time()` *(+4 more)* |
| `timeline_widgets.py` | 995 | Radio & TV Story Segmenter — Timeline Ruler, Track Views,... | `TimelineCanvas`, `TimelineWidget` |
| `transcript_cleaner.py` | 216 | Radio & TV Segmenter — Transcript cleaning, loop collapsi... | `collapse_repeating_ngrams()`, `strip_hallucination_phrases()`, `trim_trailing_degenerate_tail()`, `scrub_transcript_segments()` *(+1 more)* |
| `transcript_context_menu_mixin.py` | 746 | Radio & TV Story Segmenter — Interactive Transcript Conte... | `TranscriptContextMenuMixin` |
| `transcript_editor.py` | 953 | transcript_editor.py - Interactive Transcript Editor & Vi... | `InteractiveTranscriptEdit` |
| `transcript_editor_dialogs.py` | 808 | transcript_editor_dialogs.py - Dialog and floating toolba... | `FindReplaceDialog`, `TranscriptSelectionBubble` |
| `transcript_formatting_mixin.py` | 340 | Radio & TV Story Segmenter — Interactive Transcript Forma... | `TranscriptFormattingMixin` |
| `transcript_navigation_mixin.py` | 300 | transcript_navigation_mixin.py - Timestamp discovery, car... | `TranscriptNavigationMixin` |
| `transcript_playback_highlight_mixin.py` | 277 | Radio & TV Story Segmenter — Interactive Transcript Playb... | `TranscriptPlaybackHighlightMixin` |
| `transcript_selection_mixin.py` | 473 | transcript_selection_mixin.py - Multi-selection, timeline... | `TranscriptSelectionMixin` |
| `transcript_story.py` | 856 | Radio & TV Segmenter v3.10.30-beta — transcript story res... | `TranscriptStoryMixin` |
| `transcript_styles.py` | 104 | transcript_styles.py - Transcript view stylesheets and da... | `transcript_text_view_stylesheet()`, `clean_dark_mode_clipboard_html()` |
| `transcript_timeline_sync_mixin.py` | 655 | Radio & TV Story Segmenter — Transcript Timeline & Playba... | `TranscriptTimelineSyncMixin` |
| `transcription_processing.py` | 579 | Transcription background process management for Radio & T... | `TranscriptionProcessingMixin` |
| `translation.py` | 922 | Radio & TV Segmenter — Local Translation Mixin. | `TranslationEnvSetupWorker`, `TranslationMixin` |
| `ui_dialog_launchers.py` | 370 | Dialog launchers and external modal helpers for Radio & T... | `UiDialogLaunchersMixin` |
| `ui_layout.py` | 1103 | Radio & TV Segmenter — UI Layout & Menu Construction Mixin. | `UiLayoutMixin` |
| `ui_menus.py` | 923 | Main application menu bar and action assembly for Radio &... | `PersistentMenu`, `UiMenusMixin` |
| `updater.py` | 80 | Update manager and GitHub release installer facade for Ra... | - |
| `updater_core.py` | 758 | Headless GitHub release metadata, semantic versioning, ch... | `parse_version_tuple()`, `is_version_newer()`, `is_version_older()`, `format_byte_size()` *(+5 more)* |
| `updater_dialog.py` | 702 | Qt UI dialog and main-window mixin for checking, download... | `CheckUpdateDialog`, `UpdaterMixin` |
| `updater_workers.py` | 189 | Background QThread workers for GitHub release checking an... | `CheckUpdateWorker`, `DownloadUpdateWorker` |
| `user_guide_dialog.py` | 846 | Radio & TV Story Segmenter — In-App User Guide & Document... | `ResponsiveTextBrowser`, `UserGuideDialog` |
| `utils/__init__.py` | 36 | Utility modules for Radio & TV Story Segmenter. | - |
| `utils/constants.py` | 41 | Application constants and environment configuration. | - |
| `utils/time_format.py` | 19 | Time formatting and parsing utilities. | - |
| `voice_profile_dialog.py` | 1006 | voice_profile_dialog.py — Dialog for finding and reassign... | `VoiceProfileMatchDialog` |
| `voice_profile_ops_mixin.py` | 730 | Radio & TV Story Segmenter — Voice Profile Matching & Emb... | `VoiceProfileOpsMixin` |
| `waveform_envelope.py` | 55 | Waveform envelope data structures, downsampling pyramids,... | `WaveformEnvelope`, `build_waveform_pyramid()` |
| `worker_asr_engines.py` | 958 | worker_asr_engines.py - Faster-Whisper, CTranslate2 & She... | `set_emit_callback()`, `get_optimal_transcription_threads()`, `get_app_data_dir_pure()`, `get_models_storage_dir_pure()` *(+4 more)* |
| `worker_clustering.py` | 457 | worker_clustering.py - Acoustic clustering, VAD pause bri... | `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `fast_cluster_ahc()`, `apply_clustering_patches()` *(+2 more)* |
| `worker_diarization_clustering.py` | 634 | worker_diarization_clustering.py - Speaker Clustering, Ce... | `consolidate_speaker_clusters()`, `merge_adjacent_diarization_segments()`, `smooth_short_speaker_islands()`, `prepare_transcript_speech_segments()` *(+4 more)* |
| `worker_diarization_engine.py` | 979 | worker_diarization_engine.py - Speaker Diarization, Neura... | `set_emit_callback()`, `normalize_audio_for_diarization()`, `configure_optimal_pytorch_threads()`, `extract_embeddings_batched()` *(+3 more)* |
| `worker_ipc.py` | 216 | worker_ipc.py - Subprocess IPC protocol, environment setu... | `emit()`, `emit_hello()` |
| `worker_story_engine.py` | 396 | worker_story_engine.py - Acoustic & Lexical Story Boundar... | `is_real_speech()`, `detect_story_boundaries()` |

## Detailed Symbol Catalog

### `RadioTVSegmenter.py` (686 lines)
*Radio & TV Segmenter — v3.10.30-beta*
- **class `MainWindow(ModelManagementMixin, MediaBatchMixin, PlaybackPreferencesMixin, UiLayoutMixin, ProcessingMixin, TranslationMixin, TranscriptStoryMixin, ProjectExportMixin, GpuAccelerationMixin, QMainWindow)`** (lines 160–583):
  *Main application window for Radio & TV Segmenter.*
  - `__init__(self)` [L178-L355]
  - `_setup_shortcuts_and_actions(self)` [L357-L404] — *Register customizable QShortcut and QAction objects on MainWindow.*
  - `handle_external_open_request(self, file_path)` [L406-L431] — *Called when another instance attempts to open a project file in single-instance mode.*
  - `load_persistent_settings(self)` [L433-L528] — *Loads all persistent user preferences from QSettings into MainWindow attributes.*
  - `toggle_transcript_auto_scroll(self, checked)` [L530-L540] — *Toggle transcript auto-scrolling during playback and persist setting.*
  - `changeEvent(self, event)` [L542-L549] — *Handle window state changes (e.g. maximize, restore, minimize) safely.*
  - `dragEnterEvent(self, event)` [L551-L558]
  - `dragMoveEvent(self, event)` [L560-L567]
  - `dropEvent(self, event)` [L569-L583]
- **Functions**:
  - `main()` [L586-L682]

### `audio_normalization.py` (474 lines)
*Radio & TV Story Segmenter — Audio Loudness Probing & Normalization Engine.*
- **class `LoudnessReport`** (lines 31–44):
  *Telemetry report representing measured loudness and peak metrics for an audio file.*
  - `to_dict(self)` [L43-L44]
- **Functions**:
  - `_safe_float(val_str, default)` [L47-L62] — *Parse string to float with safe handling for -inf, inf, nan.*
  - `parse_ebur128_summary(stderr_text)` [L65-L95] — *Parse FFmpeg ebur128 filter output to extract I (LUFS), LRA (LU), and Peak (dBTP/dBFS).*
  - `probe_media_duration_seconds(media_path, timeout)` [L98-L127] — *Fast probe of total media duration in seconds via ffprobe.*
  - `probe_media_loudness(media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout)` [L130-L269] — *Measure loudness (LUFS), dynamic range (LRA), and peak (dBTP) of an audio/video file.*
  - `normalize_audio_sidecar(media_path, report, target_lufs, max_true_peak, quiet_threshold_lufs, quiet_threshold_dbfs, timeout)` [L272-L387] — *Non-destructively generate a normalized 16 kHz mono WAV sidecar.*
  - `get_effective_audio_for_processing(media_path, settings_store, project_metadata)` [L390-L467] — *Return the audio path to feed into ASR or diarization.*
  - `__getattr__(name)` [L470-L474]

### `audio_normalization_worker.py` (89 lines)
*Background QThread worker for non-blocking EBU R128 loudness probing.*
- **Public Exports (`__all__`)**: AudioLoudnessProbeWorker
- **class `AudioLoudnessProbeWorker(QThread)`** (lines 44–86):
  *Background worker thread to probe audio loudness without freezing Qt GUI.*
  - `__init__(self, media_path, target_lufs, quiet_threshold_lufs, quiet_threshold_dbfs, timeout, parent)` [L50-L65]
  - `cancel(self)` [L67-L69] — *Request worker cancellation.*
  - `run(self)` [L71-L86] — *Execute non-blocking probe in background.*

### `background_workers.py` (911 lines)
*Radio & TV Story Segmenter — Background Worker Threads & Waveform Cache Helpers.*
- **class `StoryAutoDetectWorker(QObject)`** (lines 94–468):
  - `__init__(self, audio_file, silence_threshold, lead_in_padding, audio_duration, transcript_segments, whisper_model, detection_mode, min_story_duration, **kwargs)` [L105-L129]
  - `cancel(self)` [L131-L132]
  - `_emit_progress(self, message, percent)` [L134-L148]
  - `_is_real_speech(self, text)` [L150-L156]
  - `run(self)` [L158-L468]
- **class `WaveformWorker(QObject)`** (lines 713–878):
  - `__init__(self, audio_file, points_per_second, project_file)` [L717-L724]
  - `cancel(self)` [L726-L734] — *Thread-safe cancellation request; also stops the FFmpeg child process.*
  - `run(self)` [L736-L878] — *Build a compact peak envelope without loading the whole recording into RAM.*
- **Functions**:
  - `get_waveform_peak_cache_path(audio_file, project_file)` [L492-L552] — *Return local project or appdata path for waveform peak binary cache file.*
  - `read_waveform_peak_cache(audio_file, points_per_second, project_file)` [L557-L636] — *Read cached waveform peak envelope from binary cache.*
  - `_pack_f32(values)` [L638-L642]
  - `write_waveform_peak_cache(audio_file, peaks, points_per_second, project_file, levels, skip_if_exists)` [L645-L687] — *Write waveform peak envelope and multi-resolution mipmapped levels to binary cache with atomic rename.*
  - `invalidate_waveform_peak_cache(audio_file, project_file)` [L690-L710] — *Delete any cached waveform peak binary file for audio_file, including legacy paths.*

### `backup_manager.py` (622 lines)
*Unified State Serialization & Local Backup & Restore Engine.*
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

### `build_installer.py` (457 lines)
*Build the installable Radio & TV Segmenter application with PyInstaller.*
- **Functions**:
  - `find_tool(name)` [L88-L89]
  - `run(cmd)` [L92-L93]
  - `provision_optional_runtime_tools(app_root)` [L96-L102]
  - `sync_installer_scripts(project_version)` [L105-L106]
  - `compile_windows_installer(project_version)` [L109-L110]
  - `package_plugins(app_root, include_wp, include_yt, include_tr)` [L113-L130] — *Package plugins into standalone .zip release artifacts in dist/plugins/*
  - `main()` [L133-L453]

### `bump_version.py` (513 lines)
*bump_version.py — Automated Version Synchronization Engine*
- **Functions**:
  - `normalize_version(ver)` [L26-L30] — *Normalize version string: strip leading 'v', collapse double dots, trim.*
  - `get_current_version()` [L32-L46] — *Extract active version from core_utils.py or prs_shared.py.*
  - `compute_bump(current_version, bump_type)` [L48-L66] — *Calculate next semantic version (patch, minor, major) preserving any suffix (e.g. -beta, -stable).*
  - `detect_modified_plugins()` [L69-L92] — *Auto-detect plugins with uncommitted changes via git status for Lazy Catch-Up Policy.*
  - `check_all_versions()` [L94-L197] — *Inspect and report the version strings currently set across all files.*
  - `bump_all(new_version, dry_run, plugins)` [L199-L464] — *Execute synchronous version updates across all checklist targets.*
  - `main()` [L466-L510]

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

### `core_utils.py` (776 lines)
*Radio & TV Segmenter — Core filesystem, path, timing, and hash utilities.*
- **class `StoryVocabulary(NamedTuple)`** (lines 698–711):
- **Functions**:
  - `safe_process_events()` [L38-L47] — *Safely process pending Qt GUI events only when called from the main GUI thread.*
  - `get_active_theme_mode(default)` [L50-L84] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast') with universal multi-scope resolution.*
  - `_apply_dwm_titlebar_hwnd(hwnd, theme_mode)` [L87-L140] — *Low-level Windows DWM call applying caption and text colors to a window HWND.*
  - `apply_window_titlebar_theme(widget, theme_mode)` [L143-L183] — *Configures Windows DWM title bar caption colors matching active theme mode.*
  - `_deferred_titlebar_theme(widget, theme_mode)` [L186-L200] — *Deferred callback ensuring DWM attributes persist after Qt window frame initialization.*
  - `make_dialog_maximizable(dialog)` [L203-L210] — *Enforce standard OS window maximize and restore title bar controls for resizable dialogs.*
  - `extract_dropped_file_paths(mime_data)` [L213-L264] — *Robustly extracts local filesystem paths from QMimeData supporting URLs, URIs, and raw text.*
  - `_ensure_runtime_bin_on_path()` [L267-L286] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `compute_file_sha256(file_path, chunk_size)` [L292-L298] — *Compute the SHA-256 hexadecimal digest of a file.*
  - `verify_file_sha256(file_path, expected_sha256)` [L301-L309] — *Verify that a file matches the expected SHA-256 checksum (case-insensitive).*
  - `safe_extract_zip(zip_source, dest_dir)` [L312-L330] — *Safely extracts a ZIP archive to a destination directory, guarding against path traversal (Zip Slip).*
  - `safe_extract_tar(tar_source, dest_dir)` [L333-L351] — *Safely extracts a TAR archive to a destination directory, guarding against path traversal.*
  - `safe_replace(src, dest)` [L354-L392] — *Safely and atomically replace dest with src, handling file locks, permissions,*
  - `get_github_repo()` [L395-L412] — *Return the configured GitHub repository owner/repo string.*
  - `get_update_channel()` [L415-L430] — *Return the configured software update release channel: 'stable' or 'beta'.*
  - `get_app_data_dir()` [L433-L448] — *Return the per-user writable application-data directory.*
  - `get_models_storage_dir()` [L451-L469] — *Return the directory configured for storing downloaded models.*
  - `set_models_storage_dir(new_path)` [L472-L493] — *Set and persist a custom models storage directory.*
  - `get_bundled_runtime_dir()` [L496-L508] — *Locate the installed/bundled runtime resource directory.*
  - `find_bundled_executable(name)` [L511-L533] — *Find a bundled executable first, then fall back to PATH and common macOS locations.*
  - `ffmpeg_path()` [L536-L537]
  - `ffprobe_path()` [L540-L541]
  - `format_byte_size(num_bytes)` [L544-L567] — *Format byte quantities into human-readable strings.*
  - `format_time(seconds, include_millis)` [L570-L587]
  - `format_clock_duration(seconds, include_millis)` [L590-L613] — *Format duration in seconds as clock time string (e.g. '02:30' or '02:30.5').*
  - `parse_time(value)` [L616-L632]
  - `safe_filename(text)` [L635-L651]
  - `calculate_fade_curve_factor(u, fcurve)` [L661-L672] — *Calculate normalized fade-in multiplier (0.0 to 1.0) given progress `u` in [0, 1].*
  - `calculate_fade_out_factor(u, fcurve)` [L675-L695] — *Calculate normalized fade-out multiplier (1.0 to 0.0) given progress `u` from 0.0 (fade start) to 1.0 (silence).*
  - `get_story_vocabulary(win_or_settings, language)` [L714-L775] — *Resolve active UI vocabulary nouns and action labels for timeline segments.*

### `diagnostic_batch_tests.py` (19 lines)
*Diagnostic batch and editing workflow test bench facade.*
- **Public Exports (`__all__`)**: DiagnosticBatchTestsMixin, DiagnosticBatchExportTestsMixin, DiagnosticEditingWorkflowTestsMixin
- **class `DiagnosticBatchTestsMixin(DiagnosticBatchExportTestsMixin, DiagnosticEditingWorkflowTestsMixin)`** (lines 8–12):
  *Backward-compatible facade for batch and editing workflow diagnostic tests.*

### `diagnostic_cloud_and_system_tests.py` (22 lines)
*Diagnostic cloud, voice, and system runtime test bench facade.*
- **Public Exports (`__all__`)**: DiagnosticCloudAndSystemTestsMixin, DiagnosticCloudStorageTestsMixin, DiagnosticVoiceAndMediaTestsMixin, DiagnosticSystemRuntimeTestsMixin
- **class `DiagnosticCloudAndSystemTestsMixin(DiagnosticCloudStorageTestsMixin, DiagnosticVoiceAndMediaTestsMixin, DiagnosticSystemRuntimeTestsMixin)`** (lines 9–14):
  *Backward-compatible facade for cloud, voice, and system runtime diagnostic tests.*

### `diagnostic_core_tests.py` (969 lines)
*Diagnostic test bench suite component.*
- **class `DiagnosticCoreTestsMixin`** (lines 26–968):
  - `_test_time_parsing_and_formatting(self, item)` [L27-L65]
  - `_test_project_serialization_round_trip(self, item)` [L67-L138]
  - `_test_waveform_peak_cache_generator(self, item)` [L140-L165]
  - `_test_process_lifecycle_and_subprocess_lock(self, item)` [L167-L173]
  - `_test_subrip_srt_timestamp_formatting(self, item)` [L175-L185]
  - `_test_webvtt_vtt_formatting(self, item)` [L187-L195]
  - `_test_red_book_cue_sheet_generation(self, item)` [L197-L213]
  - `_test_youtube_chapter_markers(self, item)` [L215-L231]
  - `_test_cockos_reaper_project_rpp_generator(self, item)` [L233-L315]
  - `_test_magix_samplitude_edl_v1_5_export(self, item)` [L317-L346]
  - `_test_pytorch_and_torch_native_extensions(self, item)` [L348-L357]
  - `_test_ctranslate2_acceleration_engine(self, item)` [L359-L368]
  - `_test_sherpa_onnx_and_onnx_runtime_engine(self, item)` [L370-L379]
  - `_test_directml_and_gpu_device_enumeration(self, item)` [L381-L405]
  - `_test_hugging_face_and_cdn_connectivity(self, item)` [L407-L424]
  - `_test_model_directory_storage_and_permissions(self, item)` [L426-L436]
  - `_test_safe_archive_extraction_sandbox(self, item)` [L438-L458]
  - `_test_story_boundary_detection_pipeline(self, item)` [L460-L491]
  - `_test_music_vs_voice_mode_filtering(self, item)` [L493-L505]
  - `_test_silero_neural_vad_initialization(self, item)` [L507-L515]
  - `_test_wespeaker_diarization_architecture(self, item)` [L517-L564]
  - `_test_translation_plugin_architecture_invariants(self, item)` [L566-L578]
  - `_test_speaker_reassignment_contiguous_turn_logic(self, item)` [L580-L632]
  - `_test_daw_timeline_interchange_and_gap_handling(self, item)` [L634-L750]
  - `_test_quick_sample_audio_preview_and_speaker_manager_dialog_invariants(self, item)` [L752-L968]

### `diagnostic_dialog.py` (388 lines)
*PySide6 Graphical Test Bench Dialog for Radio & TV Story Segmenter.*
- **Functions**:
  - `create_diagnostic_dialog(parent, include_dev_tests)` [L59-L388] — *Builds the Diagnostic Test Bench Qt Dialog.*

### `diagnostic_editor_tests.py` (19 lines)
*Diagnostic editor and find-replace test bench facade.*
- **Public Exports (`__all__`)**: DiagnosticEditorTestsMixin, DiagnosticEditorGuidesAndDawTestsMixin, DiagnosticEditorStoryUiTestsMixin
- **class `DiagnosticEditorTestsMixin(DiagnosticEditorGuidesAndDawTestsMixin, DiagnosticEditorStoryUiTestsMixin)`** (lines 8–12):
  *Backward-compatible facade for editor, guides, and REAPER DAW diagnostic tests.*

### `diagnostic_export_tests.py` (25 lines)
*Diagnostic export test bench facade aggregating modular test mixins.*
- **Public Exports (`__all__`)**: DiagnosticExportTestsMixin, DiagnosticExportWordPressCoreMixin, DiagnosticExportWordPressUploadMixin, DiagnosticExportWordPressMediaMixin, DiagnosticExportPipelineMixin
- **class `DiagnosticExportTestsMixin(DiagnosticExportWordPressCoreMixin, DiagnosticExportWordPressUploadMixin, DiagnosticExportWordPressMediaMixin, DiagnosticExportPipelineMixin)`** (lines 10–16):
  *Backward-compatible facade for export & WordPress diagnostic tests.*

### `diagnostic_helpers.py` (155 lines)
*Helper fixtures, module resolvers, and DiagnosticItem for test runner.*
- **Public Exports (`__all__`)**: PROJECT_ROOT, generate_synthetic_wav, DiagnosticItem, _resolve_export_subtitles_module, _resolve_export_daw_module
- **class `DiagnosticItem`** (lines 70–93):
  *Represents the execution outcome of an individual test or diagnostic probe.*
  - `__init__(self, name, category, description, dev_only)` [L73-L81]
  - `to_dict(self)` [L83-L93]
- **Functions**:
  - `generate_synthetic_wav(duration_seconds, sample_rate, frequencies, output_path)` [L21-L66] — *Generates a multi-frequency synthetic 16kHz mono WAV file in memory or on disk.*
  - `_resolve_export_subtitles_module()` [L98-L120] — *Resolves export.subtitles whether running from source, package, or frozen binary.*
  - `_resolve_export_daw_module()` [L123-L145] — *Resolves export.daw whether running from source, package, or frozen binary.*

### `diagnostic_loudness_tests.py` (406 lines)
*Radio & TV Story Segmenter — Diagnostic Loudness Normalization & Auto-Boost Test Suite.*
- **class `DiagnosticLoudnessTestsMixin`** (lines 16–405):
  *Diagnostic tests for Smart Hybrid Audio Loudness Probing & Normalization.*
  - `_test_smart_hybrid_audio_loudness_probing(self, item)` [L19-L102] — *Validates fast multi-window EBU R128 loudness & peak probing across synthetic test media.*
  - `_test_two_tier_hybrid_audio_loudness_normalization(self, item)` [L104-L198] — *Validates conditional bypass, Tier 1 linear gain + limiter, Tier 2 leveler, and integration.*
  - `_test_audio_loudness_preferences_and_manual_normalization_dialog(self, item)` [L200-L405] — *Validates Preferences persistence and manual normalization dialog telemetry.*

### `diagnostic_selector.py` (202 lines)
*Smart Diagnostic Test Selector for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_modified_files(root_dir)` [L29-L56] — *Return relative paths of modified or uncommitted files via git status.*
  - `has_git_changes(root_dir)` [L59-L61] — *Return True if there are modified or uncommitted python or plugin files in git.*
  - `detect_changed_tokens(root_dir)` [L64-L141] — *Return a set of lowercase module stems and plugin names from the most recently edited files.*
  - `select_diagnostic_items(engine, items, filter_expr, changed_only)` [L144-L202] — *Filter diagnostic items by explicit `--filter` keywords and/or `--changed` git diff analysis.*

### `diagnostic_speaker_cleanup_tests.py` (994 lines)
*Diagnostic tests for Phase 2 features: minimum story length, guest-name cleanup, and Station Voices.*
- **class `DiagnosticSpeakerCleanupTestsMixin`** (lines 13–994):
  *Mixin for Phase 2 regression diagnostics (story length, name cleanup, Station Voices).*
  - `_ensure_qt_app(self)` [L16-L21]
  - `_test_minimum_story_length_filtering_and_preferences(self, item)` [L23-L124]
  - `_test_guest_name_proper_noun_cleanup_and_preserve_case(self, item)` [L126-L258]
  - `_test_station_voice_checkbox_and_threshold_normalization(self, item)` [L260-L397]
  - `_test_offline_spellcheck_and_metadata_terminology_alignment(self, item)` [L399-L643]
  - `_test_menu_bar_deduplication_and_escaping_integrity(self, item)` [L645-L868] — *Validates main menu bar deduplication, Qt && escaping, checkable theme menu state, and shortcut metadata.*
  - `_test_abbreviation_sentence_boundaries_and_parakeet_rescue(self, item)` [L870-L994] — *Validates EN/ES title abbreviations, Parakeet chunk grouping & uncovered-speech tail rescue, diarization gap fallback, and WordPress paragraphing.*

### `diagnostic_wordpress_tests.py` (109 lines)
*Diagnostic tests for WordPress PublishPress Author mapping and update semantics.*
- **class `DiagnosticWordPressTestsMixin`** (lines 7–109):
  *Mixin for WordPress & PublishPress Author mapping regression diagnostics.*
  - `_test_wordpress_publishpress_author_mapping_and_update_semantics(self, item)` [L10-L109]

### `diagnostics/__init__.py` (28 lines)
*Modular diagnostic test mixin components for the RTVS Test Runner.*
- **Public Exports (`__all__`)**: DiagnosticExportWordPressCoreMixin, DiagnosticExportWordPressUploadMixin, DiagnosticExportWordPressMediaMixin, DiagnosticExportPipelineMixin, DiagnosticCloudStorageTestsMixin, DiagnosticVoiceAndMediaTestsMixin, DiagnosticSystemRuntimeTestsMixin, DiagnosticBatchExportTestsMixin, DiagnosticEditingWorkflowTestsMixin, DiagnosticEditorGuidesAndDawTestsMixin, DiagnosticEditorStoryUiTestsMixin

### `diagnostics/batch_export_tests.py` (469 lines)
*Batch processing, drag-and-drop ingestion, PDF, and DAW export structure tests.*
- **class `DiagnosticBatchExportTestsMixin`** (lines 15–469):
  - `_test_batch_unified_transcripts_directory_export(self, item)` [L16-L184]
  - `_test_batch_drag_and_drop_ingestion_and_event_handling(self, item)` [L186-L300]
  - `_test_unified_export_destinations_and_youtube_auth_integrity(self, item)` [L302-L369]
  - `_test_pdf_transcript_export_and_bold_speaker_labels(self, item)` [L371-L426]
  - `_test_exporter_structure_invariant_tests(self, item)` [L428-L469]

### `diagnostics/cloud_storage_tests.py` (592 lines)
*Plugin interface, project persistence, cache management, YouTube & backup diagnostic tests.*
- **class `DiagnosticCloudStorageTestsMixin`** (lines 15–592):
  - `_test_plugin_interface_sandbox_testing(self, item)` [L16-L195]
  - `_test_project_file_integrity_and_portable_path_resolution(self, item)` [L197-L301]
  - `_test_temporary_cache_management_and_storage_inspection(self, item)` [L303-L402] — *Validates cache usage stats calculation, preview categorization, and cache purging.*
  - `_test_youtube_data_api_and_direct_video_upload_engine(self, item)` [L404-L479] — *Validates YouTube Zero-Auth manual export packaging (MP4, thumbnail, SRT, metadata .txt with chapters & speakers).*
  - `_test_comprehensive_local_and_cloud_backup_and_restore_engine(self, item)` [L481-L592] — *Validates state serialization, SHA-256 verification, local backup roundtrip, and cloud payload integrity.*

### `diagnostics/editing_workflow_tests.py` (590 lines)
*Fades, translation routing, speaker dialog flow, story bounds, sync, and split/join tests.*
- **class `DiagnosticEditingWorkflowTestsMixin`** (lines 10–590):
  - `_test_fade_curve_tables_and_auditioning_state(self, item)` [L11-L92]
  - `_test_translation_routing_and_key_priority_unit_test(self, item)` [L94-L207]
  - `_test_symmetrical_translation_editing_state_test(self, item)` [L209-L290]
  - `_test_interactive_change_speaker_dialogue_flow_test(self, item)` [L292-L357]
  - `_test_story_boundary_validation_and_overlap_test(self, item)` [L359-L436]
  - `_test_audio_subtitle_sync_drift_test(self, item)` [L438-L481]
  - `_test_interactive_transcript_editing_and_split_join_unit_tests(self, item)` [L483-L590]

### `diagnostics/editor_guides_and_daw_tests.py` (500 lines)
*Find-replace, user guides viewer, and REAPER DAW companion diagnostic tests.*
- **class `DiagnosticEditorGuidesAndDawTestsMixin`** (lines 13–500):
  - `_test_find_and_replace_project_synchronization_and_undo(self, item)` [L14-L208] — *Validates that Find & Replace updates segments, word timings, speaker aliases,*
  - `_test_in_app_user_guides_and_documentation_viewer(self, item)` [L210-L301] — *Validates in-app user guide resolution, fallback to embedded content, and bundling invariants.*
  - `_test_reaper_daw_companion_and_universal_clipboard_pipeline(self, item)` [L303-L500] — *Validates REAPER DAW clip cue JSON schema, sidecar emission, Lua script syntax,*

### `diagnostics/editor_story_ui_tests.py` (852 lines)
*Story transcript highlighting, smart copy, duration & header diagnostic tests.*
- **class `DiagnosticEditorStoryUiTestsMixin`** (lines 9–852):
  - `_test_story_transcript_highlighting_and_smart_copy(self, item)` [L10-L669] — *Validates story selection synchronization with transcript highlight overlay and smart clipboard copying.*
  - `_test_story_duration_visibility_and_header_aggregation(self, item)` [L671-L852] — *Validates story clock duration formatting, 2-line sidebar item format, and multi-selection header aggregation.*

### `diagnostics/export_pipeline.py` (485 lines)
*Multi-format export pipeline, scope slicing, and audio cancellation tests.*
- **class `DiagnosticExportPipelineMixin`** (lines 13–485):
  - `_test_multi_format_line_break_and_paragraph_parity(self, item)` [L14-L119]
  - `_test_export_scope_delta_and_gap_integrity_audit(self, item)` [L121-L172]
  - `_test_export_destination_interface_contract_verification(self, item)` [L174-L210]
  - `_test_multi_story_media_payload_disambiguation_test(self, item)` [L212-L249]
  - `_test_multi_scope_story_and_full_episode_export_pipeline(self, item)` [L251-L332]
  - `_test_audio_export_non_blocking_and_cancellation_pipeline(self, item)` [L334-L443]
  - `_test_modal_dialog_maximizable_import_integrity(self, item)` [L445-L485]

### `diagnostics/export_wordpress_core.py` (830 lines)
*WordPress export scope, content formatting, and YouTube embed diagnostic tests.*
- **class `DiagnosticExportWordPressCoreMixin`** (lines 9–830):
  - `_test_wordpress_export_scope_post_builder(self, item)` [L10-L278]
  - `_test_wordpress_export_content_and_transcript_formatter(self, item)` [L280-L490]
  - `_test_wordpress_youtube_video_embed(self, item)` [L492-L830] — *Verify YouTube URL parsing, iframe block generation, video project defaults, and Gutenberg placement.*

### `diagnostics/export_wordpress_media.py` (752 lines)
*WordPress featured image metadata and Castos podcast diagnostic tests.*
- **class `DiagnosticExportWordPressMediaMixin`** (lines 10–752):
  - `_test_wordpress_featured_image_caption_and_alt_text(self, item)` [L11-L334] — *Verify Featured Image caption & alt_text across WordPressClient, post builder, tab UI, and PublishWorker.*
  - `_test_wordpress_castos_podcast_integration(self, item)` [L336-L752]

### `diagnostics/export_wordpress_upload.py` (668 lines)
*WordPress multi-story upload, Gutenberg hygiene, and audio toggle diagnostic tests.*
- **class `DiagnosticExportWordPressUploadMixin`** (lines 11–668):
  - `_test_wordpress_multi_story_upload_and_ui_pluralization(self, item)` [L12-L300]
  - `_test_gutenberg_html_structural_hygiene_audit(self, item)` [L302-L338]
  - `_test_wordpress_audio_inclusion_toggle_and_error_resilience(self, item)` [L340-L668]

### `diagnostics/system_runtime_tests.py` (446 lines)
*System runtime, updater, theme, packaging, roadmap, and modularity diagnostic tests.*
- **class `DiagnosticSystemRuntimeTestsMixin`** (lines 14–446):
  - `_test_windows_detached_update_helper_architecture(self, item)` [L15-L98] — *Validates update helper architecture: helper script generation, exit polling, and logging.*
  - `_test_multiprocessing_freeze_support_and_spawn_intercept(self, item)` [L100-L121] — *Validates that frozen process spawn intercepts -c invocations from resource_tracker and multiprocessing.*
  - `_resolve_worker_cmd(self)` [L123-L137] — *Resolves the executable and arguments to launch the AI background worker.*
  - `_test_ai_worker_subprocess_execution_and_ipc_handshake(self, item)` [L139-L205] — *Spawns the AI worker binary in an isolated subprocess, verifying IPC hello handshake and self-test.*
  - `_test_frozen_subprocess_multiprocessing_spawn_protocol(self, item)` [L207-L245] — *Spawns the AI worker executable with Python -c to verify multiprocessing resource tracker interception.*
  - `_test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting(self, item)` [L247-L300] — *Validates Option C muted low-contrast silver/fog palette and dark-mode clipboard rich styling.*
  - `_test_windows_ci_build_and_packaging_optimization_invariants(self, item)` [L302-L334] — *Validates Inno Setup compression parameters, Stage 3 PyInstaller optimizations, and CI settings.*
  - `_test_roadmap_n_1_sliding_window_and_status_integrity(self, item)` [L336-L355] — *Validates roadmap.txt N-1 sliding window retention, status indicator syntax, and version sync.*
  - `_test_source_file_modularity_and_1000_line_budget_invariant(self, item)` [L357-L446] — *Validates that recently decomposed modules adhere to the 1,000-line modular budget,*

### `diagnostics/voice_and_media_tests.py` (595 lines)
*Voice profile matching, waveform peak cache, and playback rate diagnostic tests.*
- **class `DiagnosticVoiceAndMediaTestsMixin`** (lines 13–595):
  - `_test_acoustic_voice_profile_matcher(self, item)` [L14-L273]
  - `_test_station_voice_profiles_store_and_matching_engine(self, item)` [L275-L388] — *Validates StationVoiceProfileStore persistence, vector normalization, profile addition, matching logic, and JSON export/import.*
  - `_test_multi_tier_mipmapped_waveform_peak_cache_serialization(self, item)` [L390-L425] — *Validates Version 2 .peaks binary cache read/write with 4x/16x/64x LOD pyramid levels and transparent Version 1 upgrade.*
  - `_test_speed_listening_proofreading_rate_and_context_controls(self, item)` [L427-L438] — *Validates playback speed rates (0.75x to 2.0x), WSOLA pitch preservation parameters, and proofreading pre-roll configuration.*
  - `_test_diarization_zero_padding_vad_trimming_and_speaker_labels(self, item)` [L440-L595] — *Validates exact-length zero-padding-free WeSpeaker batching, <1.0s tail right-alignment,*

### `diagnostics/youtube_import_cache_tests.py` (350 lines)
*Diagnostic tests for YouTube Episode Import, yt-dlp runner, Managed Remote Media Cache, and Shortcut/Guide sync.*
- **Public Exports (`__all__`)**: DiagnosticYouTubeImportCacheTestsMixin
- **class `DiagnosticYouTubeImportCacheTestsMixin`** (lines 10–347):
  *Automated verification mixin for YouTube import & Managed Remote Media Cache.*
  - `_test_youtube_episode_import_and_yt_dlp_provisioning(self, item)` [L13-L247]
  - `_test_managed_remote_media_cache_and_menu_shortcut_sync(self, item)` [L249-L347]

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

### `diarization_processing.py` (772 lines)
*Speaker diarization process management for Radio & TV Story Segmenter.*
- **class `DiarizationProcessingMixin`** (lines 24–772):
  - `on_diarization_process_error(self, error)` [L25-L79] — *Handles QProcess execution errors for the diarization process.*
  - `start_diarization(self)` [L81-L278]
  - `on_diarization_output(self, force_flush)` [L280-L383]
  - `on_diarization_stderr(self)` [L385-L404] — *Route the worker's stderr straight to the log, separate from the*
  - `on_diarization_process_finished(self, exit_code, exit_status)` [L406-L439]
  - `cleanup_diarization_process(self)` [L441-L475]
  - `diarization_progress(self, message, percent)` [L477-L478]
  - `diarization_finished(self, result)` [L480-L519]
  - `_apply_diarization_result(self, result)` [L521-L644]
  - `diarization_error(self, message)` [L646-L692]
  - `_diar_segments_cache_key(self)` [L695-L699]
  - `_ensure_diar_speaker_index(self)` [L701-L731]
  - `speaker_at_time(self, start, end)` [L733-L766]
  - `get_effective_speaker_name(self, seg_idx, segment)` [L768-L772]

### `embedded_guides.py` (28 lines)
*Radio & TV Story Segmenter — Built-In Embedded User Guides & Documentation.*
- **Functions**:
  - `get_embedded_guide(guide_id)` [L21-L23] — *Retrieve embedded markdown text for a guide topic ID, if available.*
  - `get_all_embedded_guide_ids()` [L26-L28] — *Return all guide IDs provided as embedded fallback content.*

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

### `export/dialog.py` (1716 lines)
*Unified Export Dialog for Radio & TV Story Segmenter.*
- **class `UnifiedExportDialog(QDialog)`** (lines 64–1716):
  *Unified Export Center supporting Local Files and dynamic plugin destinations.*
  - `__init__(self, main_window, initial_scope, initial_dest, parent)` [L67-L270]
  - `showEvent(self, event)` [L272-L274]
  - `_build_destinations_layout(self)` [L276-L442] — *Construct destination radio buttons in customized user order.*
  - `_on_reorder_destinations(self)` [L444-L463] — *Open reorder dialog and rebuild layout on change.*
  - `_create_local_page(self)` [L465-L823]
  - `_on_location_radio_toggled(self)` [L825-L828]
  - `_browse_custom_export_location(self)` [L830-L835]
  - `_create_timeline_page(self)` [L837-L1048]
  - `_on_timeline_location_radio_toggled(self)` [L1050-L1053]
  - `_browse_custom_timeline_location(self)` [L1055-L1060]
  - `_toggle_all_sections(self)` [L1062-L1076]
  - `_update_export_button_label(self)` [L1078-L1103]
  - `_sync_sidebar_decorations(self)` [L1105-L1127] — *Mirror destination-specific badges/tooltips (e.g. WordPress) onto checked sidebar rows.*
  - `_on_dest_changed(self)` [L1129-L1138]
  - `is_story_selector_visible(self)` [L1140-L1147] — *Return True when the Export Dialog's left selected-stories sidebar is active.*
  - `get_selected_story_indices(self)` [L1149-L1153] — *Return the currently checked 0-based story indices.*
  - `is_full_episode_selected(self)` [L1155-L1159] — *Return True when Full Episode is checked in the Custom Selection sidebar.*
  - `_sync_story_selector_visibility(self)` [L1161-L1169]
  - `_on_export_full_episode_toggled(self, include_full)` [L1171-L1180]
  - `_on_export_story_selection_changed(self, indices)` [L1182-L1202]
  - `_on_export_story_activated(self, story_idx)` [L1204-L1219]
  - `_on_scope_changed(self)` [L1221-L1234]
  - `_open_id3_editor(self)` [L1236-L1246] — *Open the ID3 Tag Editor for MP3 files.*
  - `_copy_youtube_chapters(self)` [L1248-L1264]
  - `_load_saved_options(self)` [L1266-L1355]
  - `save_options_to_settings(self, as_default)` [L1357-L1429]
  - `_handle_accept(self)` [L1431-L1509]
  - `get_result(self)` [L1511-L1623]
  - `_persist_plugin_draft_states(self)` [L1625-L1633] — *Persist any unsaved plugin destination edits (such as WordPress post drafts) back to the project.*
  - `done(self, r)` [L1635-L1637]
  - `toggle_float_mode(self, pinned)` [L1639-L1655] — *Toggle whether the non-modal floating window stays pinned on top of other windows.*
  - `set_scope_and_destination(self, scope, dest_id)` [L1657-L1668] — *Update export scope and active destination tab on an open modeless export window.*
  - `refresh_from_main_window(self)` [L1670-L1693] — *Synchronize post items, excerpts, and story lists from the main window without losing draft edits.*
  - `_toggle_maximize(self)` [L1695-L1703]
  - `changeEvent(self, event)` [L1705-L1716]

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

### `export/story_selector.py` (412 lines)
*Checkable story/segment selection sidebar for UnifiedExportDialog.*
- **Public Exports (`__all__`)**: ExportStorySelectorSidebar, FULL_EPISODE_ROLE_VALUE
- **class `ExportStorySelectorSidebar(QWidget)`** (lines 47–409):
  *Left sidebar with checkable Full Episode and story/segment items plus Select All / Clear.*
  - `__init__(self, main_window, parent)` [L54-L104]
  - `_resolve_full_episode_title(self)` [L106-L117]
  - `populate(self, stories, selected_indices, include_full_episode)` [L119-L208] — *Rebuild the checkable list with Full Episode at top followed by project stories.*
  - `is_full_episode_included(self)` [L210-L216] — *Return True if the Full Episode row is checked.*
  - `_apply_item_visual_state(self, item)` [L218-L243] — *Apply destination badges/tooltips to checked rows and visually mute unchecked rows.*
  - `set_item_decorations(self, decorations)` [L245-L262] — *Apply destination-specific (label, tooltip) overrides onto checked sidebar rows.*
  - `clear_item_decorations(self)` [L264-L267] — *Clear destination-specific badges/tooltips and restore default labels.*
  - `set_include_full_episode(self, checked, emit)` [L269-L287] — *Programmatically check or uncheck the Full Episode row.*
  - `get_selected_indices(self)` [L289-L298] — *Return sorted 0-based indices of all checked story items (excluding Full Episode).*
  - `has_any_selection(self)` [L300-L302] — *Return True if Full Episode or at least one story/segment is checked.*
  - `get_active_role_value(self)` [L304-L313] — *Return UserRole value (-1 for Full Episode, 0..N-1 for story) of the currently highlighted row.*
  - `is_role_checked(self, role_val)` [L315-L319] — *Return True if the row matching *role_val* (-1 or 0..N-1) is checked.*
  - `set_selected_indices(self, selected_indices, emit)` [L321-L341] — *Update story item check states without altering the Full Episode item.*
  - `select_all(self)` [L343-L347]
  - `clear_selection(self)` [L349-L353]
  - `update_count_label(self)` [L355-L358]
  - `_sync_current_item_quietly(self, item)` [L360-L367]
  - `_on_item_changed(self, item)` [L369-L392]
  - `_on_item_clicked(self, item)` [L394-L399]
  - `_on_current_row_changed(self, row)` [L401-L409]

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

### `export/timeline.py` (873 lines)
*Multi-Platform Timeline and DAW Interchange Engine for Radio & TV Story Segmenter.*
- **Functions**:
  - `_xml_escape(text)` [L24-L35] — *Escape special XML characters for well-formed interchange output.*
  - `reaper_color_from_hex(hex_str)` [L51-L62] — *Convert #RRGGBB hex color to Cockos REAPER custom color integer (0x1000000 | 0x1RRGGBB).*
  - `_reaper_fade_curve_index(curve_name)` [L65-L74] — *Map RTVS fade curve name to Cockos REAPER native curve shape index.*
  - `format_edl_timestamp(seconds)` [L77-L93] — *Format seconds into standard Samplitude EDL timecode (HH:MM:SS:mmm).*
  - `_get_story_start(s)` [L96-L101]
  - `_get_story_end(s, start_val)` [L104-L109]
  - `build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades, scope, all_stories)` [L112-L239] — *Build an ordered list of timeline clips, supporting Full Episode continuous splits and story cuts.*
  - `_build_reaper_track_block(track_name, clips, source_type, media_name_only, main_win, reaper_include_notes, reaper_include_markers, reaper_marker_style, reaper_speaker_colors, precomputed_sentences)` [L242-L351] — *Generate a clean Cockos REAPER <TRACK block with media items, fades, colors, notes, markers, and source offsets.*
  - `generate_reaper_project(stories, media_filename, project_title, apply_fades, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories, main_win, reaper_include_notes, reaper_include_markers, reaper_marker_style, reaper_speaker_colors)` [L354-L459] — *Generate a clean, warning-free Cockos REAPER project file (.rpp) with scope-aware tracks, fades, and regions.*
  - `generate_samplitude_edl(stories, media_filename, project_title, sample_rate, apply_fades, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L462-L513] — *Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `generate_fcp7_xml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L516-L603] — *Generate Final Cut Pro 7 XML (xmeml v5) interchange format for Premiere Pro and Audition.*
  - `generate_fcpxml(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L610-L666] — *Generate Apple Final Cut Pro X XML (.fcpxml) format for FCPX, DaVinci Resolve, and Logic Pro.*
  - `generate_aaf_interchange(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, scope, all_stories)` [L669-L739] — *Generate Universal AAF XML Interchange format (.aaf) for Avid Media Composer and Pro Tools.*
  - `generate_hindenburg_session(stories, media_filename, project_title, sample_rate, total_duration, unselected_audio_mode, track_name, apply_fades, scope, all_stories)` [L742-L819] — *Generate a Hindenburg Broadcast Session (.nhx) for Hindenburg Journalist and Broadcaster.*
  - `generate_audacity_labels(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L822-L834] — *Generate an Audacity Label Track (.txt) import file.*
  - `generate_cue_sheet(stories, media_filename, project_title, total_duration)` [L837-L848] — *Generate a standard Red Book Audio CD CUE sheet (.cue).*
  - `generate_daw_marker_csv(stories, total_duration, unselected_audio_mode, scope, all_stories)` [L851-L873] — *Generate a Universal DAW & NLE Marker List (.csv) format.*

### `export_dialogs.py` (476 lines)
*Radio & TV Story Segmenter — Export Dialogs & Scope Selection Interface.*
- **class `ExportDialogsMixin`** (lines 53–476):
  *Provides dialog launchers, format selectors, and destination routing for MainWindow.*
  - `trigger_export(self)` [L56-L58] — *Standard trigger for Export (File menu Ctrl+E / toolbar).*
  - `export_full_transcript(self)` [L60-L62] — *Triggered from the Export Transcript button above the transcript view.*
  - `open_export_scope_dialog(self)` [L64-L66] — *Standard trigger for the main toolbar Export button.*
  - `open_unified_export_dialog(self, initial_scope, initial_dest, modal)` [L68-L156] — *Unified Export Dialog entry point for local file exports, WordPress publishing,*
  - `_dispatch_unified_export_result(self, result)` [L158-L323] — *Execute the selected export operation after UnifiedExportDialog is accepted.*
  - `_choose_export_formats(self, title, allow_media)` [L325-L476] — *Modal dialog to choose formats and transcript options for classic export flows.*
- **Functions**:
  - `show_export_completion_dialog(parent, title, message, export_path)` [L34-L50] — *Displays export completion with an actionable 'Open Folder' button (Milestone 3.11).*

### `export_documents.py` (796 lines)
*Radio & TV Story Segmenter — Document, Transcript & Timeline Interchange Exporter.*
- **class `ExportDocumentsMixin`** (lines 49–796):
  *Provides document formatting, subtitle generation, and DAW interchange exports.*
  - `_subtitle_timestamp(self, seconds, vtt)` [L52-L62]
  - `write_subtitles(self, blocks, path, fmt, include_speakers)` [L64-L80]
  - `transcript_for_range(self, start, end)` [L82-L100]
  - `speaker_for_segment(self, segment)` [L102-L111]
  - `clean_export_text(self, text, current_speaker)` [L113-L146]
  - `build_story_blocks(self, segments)` [L148-L272]
  - `story_text(self, segments)` [L274-L290]
  - `add_story_to_docx(self, document, segments)` [L292-L306]
  - `_get_transcript_text_slice(self, start, end)` [L308-L315]
  - `export_cue_sheet(self, destination_path)` [L317-L349] — *Export story/song segments to a standard .cue sheet.*
  - `export_tracklist(self, destination_path)` [L351-L381] — *Export story/song segments as YouTube chapters / tracklist formatted text.*
  - `_get_unselected_audio_mode_pref(self)` [L383-L388]
  - `export_reaper_project(self, destination_path, unselected_audio_mode)` [L390-L435] — *Export story segments as a Cockos REAPER project file (.rpp).*
  - `export_samplitude_edl(self, destination_path, unselected_audio_mode)` [L437-L470] — *Export story segments as a Magix Samplitude EDL (v1.5) broadcast edit decision list.*
  - `export_audacity_labels(self, destination_path, unselected_audio_mode)` [L472-L504] — *Export story segments as an Audacity Label Track (.txt).*
  - `export_audition_xml(self, destination_path, unselected_audio_mode)` [L506-L539] — *Export story segments as Adobe Audition / Final Cut Pro XML (.xml).*
  - `export_daw_marker_csv(self, destination_path, unselected_audio_mode)` [L541-L573] — *Export story segments as a Universal DAW Marker List (.csv).*
  - `copy_youtube_chapters_to_clipboard(self)` [L575-L592] — *Format story segments as YouTube chapters and copy them directly to the system clipboard.*
  - `export_timeline_interchange(self, formats, base, options, directory, scope, is_custom_location)` [L594-L796] — *Export multi-platform timeline and DAW interchange project files.*

### `export_media_clipper.py` (338 lines)
*Radio & TV Story Segmenter — Media Clipper & Audio Track Renderer.*
- **class `ExportMediaClipperMixin`** (lines 26–338):
  *Provides audio/video track rendering, story clip extraction, and YouTube media handling.*
  - `cancel_export(self)` [L29-L34] — *Flag the running export operation to halt at the next iteration.*
  - `extract_media(self, start, end, output_file, fade_in, fade_out, cancel_check)` [L36-L63] — *Export a media range using the same container/format as the imported file,*
  - `extract_audio(self, start, end, output_file)` [L65-L71] — *Backward-compatible helper for older project/export code.*
  - `_generate_broadcast_slate_thumbnail(self, title, output_path)` [L73-L107] — *Render a clean 1280x720 dark broadcast slate image for audio-only YouTube exports.*
  - `_handle_youtube_export_result(self, result)` [L109-L338]

### `export_story_pipeline.py` (968 lines)
*Radio & TV Story Segmenter — Story & Full Episode Export Pipeline.*
- **class `ExportStoryPipelineMixin`** (lines 36–968):
  *Provides story batch export and full episode export orchestration.*
  - `_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L39-L69]
  - `_do_export_story_files(self, stories_with_indices, formats, base, options, directory, start_idx, total_batch, is_custom_location)` [L71-L349]
  - `_export_daw_interchange_files(self, formats, stories, base, transcripts_out, audio_file, options, default_track, default_scope)` [L351-L407]
  - `export_selected_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L409-L474]
  - `export_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location)` [L476-L537]
  - `export_full_and_all_stories(self, custom_formats, custom_base, custom_options, directory, is_custom_location, story_indices)` [L539-L627]
  - `export_full_episode(self, custom_formats, custom_base, custom_options, directory, show_completion, progress_dialog, progress_value, is_custom_location)` [L629-L938]
  - `perform_stories_export(self, target_stories, custom_formats, custom_base, custom_options, directory, show_completion, is_custom_location)` [L940-L962]
  - `export_youtube_manual_package(self, export_data)` [L964-L968] — *Render and package zero-auth manual YouTube export (MP4, thumbnail, SRT, metadata .txt).*

### `glossary_dialog.py` (490 lines)
*Custom Vocabulary & Glossary Dialog.*
- **class `GlossaryDialog(QDialog)`** (lines 46–490):
  *Dialog for editing persistent terminology, proper nouns, and alternate spellings.*
  - `__init__(self, parent)` [L49-L54]
  - `_init_ui(self)` [L56-L186]
  - `_populate_table(self, entries)` [L188-L194]
  - `_insert_entry_row(self, entry, row_idx)` [L196-L218]
  - `add_row(self, source_val, preferred_val, dnt_val, mc_val)` [L220-L231]
  - `remove_rows(self)` [L233-L240]
  - `_apply_filter(self, query)` [L242-L253]
  - `_on_sort_changed(self, index)` [L255-L259]
  - `_show_context_menu(self, pos)` [L261-L320]
  - `get_current_table_entries(self)` [L322-L354] — *Collect all table rows including hidden ones without data loss.*
  - `_apply_to_current_transcript(self)` [L356-L375]
  - `save_glossary(self)` [L377-L397]
  - `export_glossary_file(self)` [L399-L435]
  - `import_glossary_file(self)` [L437-L490]

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

### `installer/build_tools/__init__.py` (50 lines)
*Modular build utilities for Radio & TV Segmenter PyInstaller & installer packaging.*
- **Public Exports (`__all__`)**: UV_VERSION, UV_URLS, PYSIDE6_USED_SUBMODULES, PYSIDE6_EXCLUDES, TEST_AND_BENCHMARK_EXCLUDES, COLLECT_ALL_PACKAGES, COPY_METADATA_PACKAGES, HIDDEN_IMPORTS, parse_build_args, exe_name, find_tool, check_cpu_only_torch, torch_windows_binary_flags, run, provision_optional_runtime_tools, prune_unneeded_bundled_files, sync_installer_scripts, compile_windows_installer, package_plugins

### `installer/build_tools/config.py` (214 lines)
*Build configuration constants and CLI argument parser.*
- **Functions**:
  - `parse_build_args()` [L139-L214] — *Parse build target, plugin selection, installer, and version CLI flags.*

### `installer/build_tools/env_checks.py` (188 lines)
*Environment validation, external tool resolution, and subprocess execution helpers.*
- **Functions**:
  - `exe_name(base)` [L15-L17] — *Return platform-appropriate executable filename.*
  - `find_tool(name, root_dir)` [L20-L84] — *Locate required media runtime tools such as ffmpeg or ffprobe.*
  - `check_cpu_only_torch()` [L87-L128] — *Verify the build environment uses CPU-only PyTorch unless explicitly bypassed.*
  - `torch_windows_binary_flags()` [L131-L159] — *Collect explicit Windows PyTorch DLL binary flags for PyInstaller.*
  - `run(cmd, cwd)` [L162-L188] — *Execute a build subprocess streaming output line-by-line.*

### `installer/build_tools/packaging.py` (368 lines)
*Bundle pruning, plugin archive packaging, runtime tools, and Windows Inno Setup helpers.*
- **Functions**:
  - `provision_optional_runtime_tools(app_root, build_dir, uv_version, uv_urls)` [L23-L106] — *Bundle standalone uv binary into optional_runtime/ when explicitly requested.*
  - `prune_unneeded_bundled_files(app_root)` [L109-L242] — *Strip CUDA leftovers, development headers, test suites, and software OpenGL bloat.*
  - `sync_installer_scripts(project_version, root_dir)` [L245-L257] — *Ensure Inno Setup and other installer packaging scripts match PROJECT_VERSION.*
  - `compile_windows_installer(project_version, root_dir)` [L260-L295] — *Compile the Windows Inno Setup installer executable if ISCC is installed.*
  - `package_plugins(app_root, include_wp, include_yt, include_tr, root_dir, dist_dir, project_version)` [L298-L368] — *Package plugins into standalone .zip release artifacts in dist/plugins/*

### `installer/pyinstaller/torch_dll_hook.py` (70 lines)
*PyInstaller runtime hook for Windows ML/native DLL resolution.*

### `media_batch.py` (1905 lines)
*Radio & TV Segmenter v1.1.1 — media batch responsibilities.*
- **class `MediaBatchMixin`** (lines 22–1905):
  - `probe_media_duration(self, path)` [L23-L37] — *Probe duration locally so video timelines can be populated immediately.*
  - `_track_worker_thread(self, thread)` [L39-L51] — *Keep a strong reference to active worker threads so Python GC never destroys them while executing.*
  - `stop_waveform_worker(self, timeout_ms)` [L53-L84] — *Stop the current waveform worker completely before replacing it or closing.*
  - `_effective_thumbnail_density(self, density)` [L86-L93]
  - `start_video_thumbnail_generation(self, force_regenerate, density)` [L95-L241]
  - `_video_thumbnail_progress(self, pct)` [L243-L251]
  - `_video_thumbnail_thread_finished(self)` [L253-L261]
  - `_cached_thumbnails_loaded(self, items, req_key, eff_density, expected_count)` [L263-L281]
  - `_video_thumbnails_finished(self, items, req_key)` [L283-L298]
  - `stop_video_thumbnail_worker(self, timeout_ms)` [L300-L332]
  - `regenerate_waveform(self)` [L334-L355] — *Force recalculation of waveform peaks by clearing disk cache and restarting generation.*
  - `regenerate_video_thumbnails(self, density)` [L357-L394] — *Force regeneration of video filmstrip thumbnails (optionally updating density preset).*
  - `load_waveform_async(self, force_regenerate)` [L396-L453]
  - `_waveform_progress(self, partial_peaks, pps, pct)` [L455-L463]
  - `_waveform_finished(self, peaks, cancelled)` [L465-L482]
  - `_waveform_thread_finished(self)` [L484-L488]
  - `open_batch_processing_dialog(self)` [L490-L595]
  - `_batch_next_media(self)` [L597-L714]
  - `_batch_next_document(self)` [L716-L744]
  - `_batch_document_error(self, msg)` [L746-L755] — *Handles document batch translation errors safely.*
  - `_load_user_preferences(self)` [L757-L840]
  - `set_thumbnail_position(self, position)` [L842-L846]
  - `_remember_saved_project(self, path)` [L848-L879] — *Remember only projects that have actually been saved.*
  - `_dialog_directory(self, fallback)` [L881-L893]
  - `_remember_open_directory(self, path)` [L895-L902]
  - `_sync_startup_project_actions(self)` [L904-L910] — *Synchronize the Project Settings startup radio/check actions.*
  - `set_startup_project_mode(self, mode)` [L912-L918] — *Set the startup project policy.*
  - `restore_last_opened(self)` [L920-L1060] — *Apply startup policy and offer recovery from a newer autosave snapshot.*
  - `toggle_speaker_labels(self, checked)` [L1062-L1067]
  - `toggle_colorize_speaker_labels(self, checked)` [L1069-L1076]
  - `toggle_timestamps(self, checked)` [L1078-L1085]
  - `toggle_milliseconds(self, checked)` [L1087-L1094]
  - `toggle_waveform_view(self, checked)` [L1096-L1100]
  - `toggle_thumbnail_view(self, checked)` [L1102-L1106]
  - `choose_default_project_directory(self)` [L1108-L1123]
  - `open_document_path(self, path)` [L1125-L1160]
  - `open_clear_cache_dialog(self)` [L1162-L1175]
  - `open_manage_cached_media_dialog(self)` [L1177-L1180]
  - `redownload_current_project_remote_media(self)` [L1182-L1193]
  - `open_glossary_dialog(self)` [L1195-L1199] — *Edit persistent terminology used by every ASR and translation backend.*
  - `_save_glossary(self)` [L1201-L1208]
  - `apply_glossary_to_current_transcript(self, entries)` [L1210-L1242] — *Apply glossary rules and contextual name resolution to the active transcript with Undo support.*
  - `add_to_glossary(self, text)` [L1244-L1264]
  - `prompt_add_alternate_spelling(self, alternate_text)` [L1266-L1309] — *Prompt user for the preferred glossary spelling that `alternate_text` should map to.*
  - `apply_glossary_to_whisper_context(self)` [L1311-L1322]
  - `add_custom_speaker_to_glossary(self, name)` [L1324-L1326]
  - `set_language(self, language, persist)` [L1328-L1349]
  - `_apply_localization(self)` [L1351-L1388]
  - `update_story_segment_terminology(self)` [L1390-L1477] — *Update all user-facing labels and tooltips using active vocabulary settings.*
  - `open_document(self)` [L1479-L1533]
  - `export_text_file(self)` [L1535-L1543]
  - `open_media(self)` [L1545-L1554]
  - `prepare_for_new_media(self)` [L1556-L1589] — *Checks for unsaved changes before loading new media.*
  - `_batch_media_error(self, message)` [L1591-L1613]
  - `_get_batch_project_target_path(self, base_name)` [L1615-L1642] — *Determines consistent target .rtvs project file path during batch processing.*
  - `_batch_save_project_file(self)` [L1644-L1659] — *Saves project .rtvs to dedicated directory structure during batch processing.*
  - `_batch_export_current(self)` [L1661-L1745] — *Handles automatic export or project saving during batch processing.*
  - `load_media_file(self, filename, source, restore_adjacent_project)` [L1747-L1864]
  - `update_active_media_source(self)` [L1866-L1899] — *Update media player source and refresh waveform when normalization state changes.*
  - `open_audio(self)` [L1901-L1902]
  - `handle_media_drop(self, filename)` [L1904-L1905]

### `model_cleanup_dialog.py` (468 lines)
*Manage Models dialog and shared runtime cleanup helpers for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: WHISPER_MODEL_CATALOG, ModelCleanupDialog, format_directory_size, _stop_and_remove_runtime_env
- **class `ModelCleanupDialog(QDialog)`** (lines 63–460):
  *Unified local model manager dialog for ASR, diarization, translation, and cache.*
  - `__init__(self, owner, translation_worker_cls_fn, translation_plugin_installed_fn)` [L66-L83]
  - `_get_translation_worker_cls(self)` [L85-L88]
  - `_is_translation_active(self)` [L90-L93]
  - `_build_ui(self)` [L95-L328]
  - `update_install_progress(self, pct, msg)` [L330-L333]
  - `hide_install_progress(self)` [L335-L336]
  - `refresh_models(self)` [L338-L379]
  - `remove_selected(self)` [L381-L460]
- **Functions**:
  - `format_directory_size(path)` [L38-L44] — *Return total size in MB for files under path, or a fallback string.*
  - `_stop_and_remove_runtime_env(owner, *env_names)` [L47-L60] — *Stop tracked subprocesses and remove one or more isolated runtime environments.*

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

### `model_management.py` (621 lines)
*Radio & TV Segmenter v1.1.1 — model management responsibilities.*
- **class `_DummyTranslationWorker`** (lines 27–40):
  - `model_root(cls, variant)` [L29-L31]
  - `model_dir(cls, from_code, to_code, variant)` [L34-L35]
  - `model_is_installed(cls, from_code, to_code, variant)` [L38-L40]
- **class `ModelManagementMixin`** (lines 77–621):
  - `model_cache_candidates(self, model_name)` [L78-L165] — *Return all potential candidate directories where model weights might be stored.*
  - `model_cache_path(self, model_name)` [L167-L179]
  - `is_whisper_model_available(self, model_name)` [L181-L210]
  - `refresh_whisper_model_chooser(self)` [L212-L226]
  - `current_whisper_model(self)` [L228-L233]
  - `update_whisper_model_tooltip(self)` [L235-L241]
  - `set_whisper_model_from_ui(self, index)` [L243-L257]
  - `translation_model_display_name(self, variant)` [L259-L261]
  - `translation_model_root(self, variant)` [L263-L264]
  - `refresh_translation_model_chooser(self)` [L266-L276]
  - `set_translation_model_from_ui(self, index)` [L278-L287]
  - `prompt_translation_model(self)` [L289-L297]
  - `open_model_cleanup_dialog(self)` [L299-L306] — *Unified local model manager for Whisper and OPUS-MT models.*
  - `purge_all_data_action(self, parent_widget, on_complete)` [L308-L369] — *Purge all downloaded AI models, log files, updater cache, and translation runtimes.*
  - `open_translation_model_manager(self)` [L371-L373]
  - `install_whisper_model_for_manager(self, model_name, dialog)` [L375-L403]
  - `cancel_model_installation(self)` [L405-L410]
  - `_on_model_install_progress(self, percent, message)` [L412-L422]
  - `_install_whisper_model_background(self, model_name)` [L424-L462]
  - `_model_install_finished(self, error)` [L464-L465]
  - `_model_install_thread_finished(self)` [L467-L521]
  - `_poll_model_install(self, dialog)` [L523-L525]
  - `install_diarization_model_for_manager(self, dialog)` [L527-L555] — *Install or repair the WeSpeaker ResNet34 ONNX diarization voice embedding model.*
  - `install_translation_models_for_manager(self, from_code, to_code, variant, dialog)` [L557-L595] — *Install an OPUS-MT model through the translation plugin's isolated runtime.*
  - `_translation_manager_install_finished(self, from_code, to_code, variant, dialog)` [L598-L611]
  - `_translation_manager_install_error(self, message, dialog)` [L613-L621]
- **Functions**:
  - `_translation_worker_class()` [L43-L53] — *Load translation implementation dynamically without hard-importing from plugins.*
  - `_translation_plugin_installed(self)` [L55-L61]

### `playback_controller.py` (630 lines)
*Radio & TV Story Segmenter — Media Player Transport & Playback Controller.*
- **class `PlaybackControllerMixin`** (lines 25–630):
  *Provides audio/video media player transport, scrubbing, and fade controls.*
  - `is_video_file(self, path)` [L28-L33]
  - `_ensure_video_preview_dialog(self)` [L35-L64] — *Lazily initialize the floating video preview dialog and video sink widget.*
  - `update_video_preview_state(self)` [L66-L77]
  - `toggle_video_preview(self, checked)` [L79-L105]
  - `handle_scrub_position(self, seconds)` [L107-L110]
  - `execute_scrub_seek(self)` [L112-L119]
  - `eventFilter(self, watched, event)` [L121-L315]
  - `_is_text_entry_focused(self)` [L317-L332] — *Return True if a text entry widget or editable transcript currently has focus.*
  - `_matches_shortcut(self, event, action_id, default_seq)` [L334-L378] — *Return True if key event matches user configured shortcut for action_id.*
  - `_toggle_follow_playhead(self)` [L380-L386] — *Toggle automatic timeline view scrolling following the audio playhead.*
  - `mark_story_start_point(self)` [L388-L402] — *Mark start point at current playhead position.*
  - `mark_story_end_point(self)` [L404-L421] — *Mark end point at current playhead position and create story if valid range.*
  - `get_segment_index_at_time(self, target_time)` [L423-L431] — *Find transcript segment index active at target_time.*
  - `split_current_segment_at_playhead(self)` [L433-L438] — *Split the transcript segment active at current playhead position.*
  - `merge_current_segment_with_next(self)` [L440-L447] — *Merge the transcript segment active at current playhead with following segment.*
  - `set_skip_seconds_from_ui(self, value)` [L449-L459]
  - `set_playback_rate(self, rate)` [L461-L473]
  - `toggle_play(self)` [L475-L499]
  - `stop_audio(self)` [L501-L511]
  - `seek_to(self, seconds)` [L513-L527]
  - `seek_relative(self, delta_seconds)` [L529-L535]
  - `audio_position_changed(self, position)` [L537-L544]
  - `get_fade_volume_factor_at_time(self, t)` [L546-L589] — *Calculate the real-time audio volume fade factor [0.0, 1.0] for position `t`.*
  - `update_realtime_fade_volume(self)` [L591-L620] — *Modulate QAudioOutput volume in real-time according to story fade envelopes.*
  - `_on_fade_timer_tick(self)` [L622-L624]
  - `audio_duration_changed(self, duration)` [L626-L630]

### `playback_preferences.py` (815 lines)
*Radio & TV Story Segmenter — Playback Preferences & Application Facade.*
- **Public Exports (`__all__`)**: PlaybackPreferencesMixin, RestoreSelectedSettingsDialog, ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, PreferencesResetMixin, ProjectStateMixin
- **class `PlaybackPreferencesMixin(ThemePreferencesMixin, PlaybackControllerMixin, PreferencesDialogMixin, ProjectStateMixin)`** (lines 51–815):
  *Aggregates all playback, preferences, styling, and application lifecycle mixins.*
  - `_install_diagnostic_logging(self)` [L54-L181] — *Install startup-safe diagnostics that never depend on the GUI widgets.*
  - `export_activity_log(self)` [L183-L216] — *Export session activity log entries to a timestamped plain-text file.*
  - `log_activity(self, action_text, mark_dirty)` [L218-L256]
  - `handle_activity_click(self, item)` [L258-L261]
  - `restore_snapshot(self, index)` [L263-L302]
  - `clear_activity_log(self)` [L304-L307]
  - `_find_all_transcript_matches(self, query)` [L309-L327]
  - `_on_transcript_search_text_changed(self, text)` [L329-L370] — *Update auto-highlights and match count badge in real time as search query changes.*
  - `_sync_search_match_ui(self, scroll_to_match)` [L372-L411]
  - `trigger_find_next(self)` [L413-L443] — *Find Next shortcut (Ctrl+G) handler: advances to next search match in transcript.*
  - `trigger_find_prev(self)` [L445-L475] — *Find Previous shortcut (Ctrl+Shift+G) handler: retreats to previous search match in transcript.*
  - `open_diagnostic_log_folder(self)` [L477-L492]
  - `open_user_documentation(self, guide_id)` [L494-L504] — *Display the in-app User Guides & Documentation dialog.*
  - `show_about_dialog(self)` [L506-L545]
  - `check_for_updates(self, interactive)` [L547-L558] — *Open the Check for Updates dialog to query GitHub releases and install updates.*
  - `trigger_silent_update_check(self)` [L560-L585] — *Perform a background update check without showing UI unless an update is found.*
  - `apply_audio_output_device(self, device_name, volume)` [L587-L611] — *Apply selected audio output device and volume to the active player.*
  - `show_licenses_dialog(self)` [L613-L652]
  - `on_expected_speakers_changed(self, value)` [L654-L665] — *Kept as a public hook in case a future toolbar control adjusts the expected-speakers hint directly.*
  - `on_diarization_sensitivity_changed(self, value)` [L667-L678] — *Public hook for adjusting speaker separation sensitivity.*
  - `update_auto_save_timer(self)` [L680-L684]
  - `prompt_set_whisper_model(self)` [L686-L689]
  - `prompt_set_skip_seconds(self)` [L691-L705]
  - `prompt_set_auto_detect_thresholds(self)` [L707-L773]
  - `prompt_set_auto_save(self)` [L775-L793]
  - `trigger_auto_save(self)` [L795-L815]

### `plugin_base.py` (225 lines)
*Radio & TV Segmenter — Plugin Base Interfaces and Manifest.*
- **class `PluginManifest`** (lines 11–63):
  *Metadata describing a plugin, parsed from manifest.json.*
  - `from_dict(cls, data)` [L33-L53]
  - `from_file(cls, path)` [L56-L63]
- **class `BasePlugin`** (lines 66–186):
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
  - `get_file_open_actions(self)` [L128-L130] — *Return list of (Action Label, callback_function) for top Media Input section of File menu.*
  - `get_remote_open_actions(self)` [L132-L134] — *Return list of (Action Label, callback_function) for File > Open Remote Episode submenu.*
  - `get_cache_maintenance_actions(self)` [L136-L138] — *Return list of (Button Label, callback(parent_dialog)) for Manage Cached Remote Media dialog.*
  - `can_redownload_remote_source(self, source_meta)` [L140-L142] — *Return True if this plugin can re-download the given remote_media_source record.*
  - `redownload_remote_source(self, source_meta, parent)` [L144-L146] — *Re-download an archived remote media source and return its local Path, or None if cancelled.*
  - `get_export_actions(self)` [L148-L150] — *Return list of (Action Label, callback_function) for Export menu.*
  - `get_export_destinations(self)` [L152-L154] — *Return list of ExportDestination providers to embed into UnifiedExportDialog.*
  - `get_tools_actions(self)` [L156-L158] — *Return list of (Action Label, callback_function) for Tools menu.*
  - `get_story_actions(self, story)` [L160-L162] — *Return list of (Action Label, callback_function) for story context menu.*
  - `create_story_metadata_widget(self, parent)` [L164-L166] — *Return a QWidget to be embedded into the Stories panel for metadata editing, or None.*
  - `on_story_selected(self, story)` [L168-L170] — *Called when active story selection changes in the main editor.*
  - `get_preferences_widget(self, parent)` [L172-L174] — *Return a QWidget to be embedded into the Preferences dialog, or None.*
  - `save_preferences(self, widget)` [L176-L178] — *Called when the user saves the Preferences dialog.*
  - `on_project_loaded(self, project_data)` [L180-L182] — *Called when an .rtvs project is loaded. Allows reading plugin metadata.*
  - `on_project_saving(self, project_data)` [L184-L186] — *Called before an .rtvs project is saved. Allows injecting plugin metadata.*
- **class `ExportDestination`** (lines 189–225):
  *Base class for plugin-provided export destinations in UnifiedExportDialog.*
  - `__init__(self, id, title, description, icon, button_label)` [L192-L205]
  - `create_widget(self, parent, main_window)` [L207-L209] — *Create the configuration and preview widget embedded into the destination tab.*
  - `on_scope_changed(self, scope, stories)` [L211-L213] — *Called when export scope changes in the dialog (full, selected, all).*
  - `validate(self)` [L215-L217] — *Validate destination settings before export begins. Returns (ok, error_msg).*
  - `get_export_data(self)` [L219-L221] — *Collect export parameters to include in the final dialog result.*
  - `execute_export(self, main_window, export_data, progress_dialog)` [L223-L225] — *Execute the export action for this destination.*

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

### `plugins/manager_dialog.py` (532 lines)
*Plugin and Add-On Manager Dialog for inspecting, enabling, and installing add-ons.*
- **class `PluginManagerDialog(QDialog)`** (lines 41–532):
  *GUI Dialog for viewing, managing, enabling, installing, and removing plugins with multi-selection.*
  - `__init__(self, manager, parent)` [L44-L52]
  - `setup_ui(self)` [L54-L164]
  - `on_download_github(self)` [L166-L177]
  - `select_all_plugins(self)` [L179-L180]
  - `deselect_all_plugins(self)` [L182-L183]
  - `get_selected_plugin_ids(self)` [L185-L198] — *Returns the list of plugin_ids selected via multi-row selection.*
  - `refresh_list(self)` [L200-L245]
  - `on_toggle_plugin(self, plugin_id, state)` [L247-L255]
  - `on_selection_changed(self)` [L257-L283]
  - `configure_selected_plugin(self)` [L285-L306]
  - `enable_selected_plugins(self)` [L308-L321]
  - `disable_selected_plugins(self)` [L323-L336]
  - `uninstall_selected_plugins(self)` [L338-L362]
  - `on_install_addon(self)` [L364-L401]
  - `check_for_plugin_updates(self)` [L403-L483] — *Checks GitHub for newer versions of installed plugins without updating the core app.*
  - `run_batch_plugin_updates(self, update_items)` [L485-L520] — *Downloads and installs a batch of plugin updates.*
  - `on_open_folder(self)` [L522-L532]

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

### `plugins/wordpress/authors.py` (143 lines)
*Pure-Python helpers for WordPress user and PublishPress Author ID mapping.*
- **Public Exports (`__all__`)**: count_selected_authors, expand_legacy_author_term_ids, extract_checked_author_ids, is_author_item_selected, resolve_selected_author_names
- **Functions**:
  - `_pos_int(val)` [L15-L20]
  - `_dedupe_pos_ints(values)` [L23-L31]
  - `extract_checked_author_ids(checked_authors)` [L34-L65] — *Split checked author entries into WordPress ``author_ids`` and PublishPress ``author_term_ids``.*
  - `is_author_item_selected(author, author_ids, author_term_ids)` [L68-L91] — *Return True if an author item matches the post's selected user/PublishPress term IDs.*
  - `resolve_selected_author_names(cached_authors, author_ids, author_term_ids)` [L94-L109] — *Return display names for cached author entries selected on a post.*
  - `count_selected_authors(author_ids, author_term_ids)` [L112-L117] — *Return distinct selected author count without double-counting mapped WP/PublishPress users.*
  - `expand_legacy_author_term_ids(author_ids, author_term_ids, cached_authors)` [L120-L143] — *Backfill PublishPress ``term_id`` entries when legacy project data only stored ``author_ids``.*

### `plugins/wordpress/castos.py` (725 lines)
*Seriously Simple Podcasting (Castos) integration for WordPress export.*
- **Public Exports (`__all__`)**: SS_PODCAST_AUDIO_FILE, SS_PODCAST_AUDIO_FILE_ID, SS_PODCAST_DURATION, SS_PODCAST_FILESIZE, SS_PODCAST_FEED, SS_PODCAST_EPISODE_TYPE, SS_PODCAST_SEASON, SS_PODCAST_EPISODE_NUMBER, CASTOS_META_AUDIO_FILE, CASTOS_META_AUDIO_FILE_ID, CASTOS_META_DURATION, CASTOS_META_FILESIZE, CASTOS_META_EPISODE_TYPE, CASTOS_META_SEASON, CASTOS_META_EPISODE_NUMBER, CASTOS_TAXONOMY_SERIES, CASTOS_TAXONOMY_SERIES_FALLBACK, CASTOS_SHORTCODE, CASTOS_PLAYER_BLOCK, DEFAULT_FEED_SLUG, DEFAULT_FEED_NAME, format_castos_duration, build_castos_post_meta, copy_podcast_meta, fetch_castos_feeds, sanitize_castos_feeds, setup_castos_ui, populate_castos_feeds_combo, sync_castos_to_post, load_castos_from_post
- **Functions**:
  - `format_castos_duration(seconds)` [L61-L72] — *Format duration in seconds into HH:MM:SS for podcast RSS metadata.*
  - `build_castos_post_meta(audio_url, attachment_id, duration_seconds, filesize_bytes, feed_slug, episode_type, season, episode_number)` [L75-L143] — *Build the dictionary of Seriously Simple Podcasting post meta keys.*
  - `copy_podcast_meta(target, src)` [L146-L161] — *Copy Seriously Simple Podcasting metadata fields from src to target dictionary.*
  - `fetch_castos_feeds(client)` [L164-L310] — *Query WordPress REST API for Seriously Simple Podcasting series/feeds.*
  - `sanitize_castos_feeds(feeds)` [L313-L327] — *Filter out non-podcast/author items and ensure valid feed structures.*
  - `setup_castos_ui(tab_widget, editor_layout)` [L330-L506] — *Build and insert the Castos Seriously Simple Podcasting section into the post editor layout.*
  - `populate_castos_feeds_combo(tab_widget, feeds)` [L509-L546] — *Populate the podcast feed list and combo with discovered series/feeds.*
  - `sync_castos_to_post(tab_widget, post)` [L549-L612] — *Extract Castos UI state and write into post dictionary.*
  - `load_castos_from_post(tab_widget, post)` [L615-L691] — *Set Castos UI controls from post dictionary.*

### `plugins/wordpress/client.py` (2169 lines)
*WordPress Plugin — Client, Credential Storage, and Upload Engine.*
- **class `WordPressClient`** (lines 342–1013):
  *Client for WordPress REST API using Application Passwords.*
  - `__init__(self, site_url, username, password)` [L345-L357]
  - `is_configured(self)` [L359-L366] — *Return True if site_url, username, and password are all non-empty and non-placeholder.*
  - `_get_auth(self)` [L368-L369]
  - `_discover_canonical_base(self)` [L371-L384] — *Pre-detect canonical site URL and REST base to prevent redirect failures.*
  - `_is_safe_redirect(self, current_url, next_url)` [L386-L395] — *Verify redirect does not cross domains or downgrade from HTTPS to HTTP.*
  - `_get_request(self, url, params, headers, timeout)` [L397-L428] — *Issue an HTTP GET with manual redirect protection and authentication.*
  - `_post_request(self, url, json_data, headers, timeout)` [L430-L457] — *Issue an HTTP POST with manual redirect protection to keep POST method & Auth header.*
  - `_post_multipart(self, url, path, upload_filename, mime_type, timeout)` [L459-L485] — *Issue a multipart file POST with manual redirect protection.*
  - `test_connection(self)` [L487-L510] — *Test credentials against /wp/v2/users/me or /wp/v2/posts.*
  - `get_categories(self)` [L512-L528] — *Fetch post categories from WordPress.*
  - `get_authors(self)` [L530-L627] — *Fetch PublishPress Authors profiles, including guest authors without users.*
  - `upload_media(self, file_path, filename, caption, alt_text)` [L629-L701] — *Upload media using WordPress's standard multipart API, with raw fallback.*
  - `update_media_metadata(self, media_id, caption, alt_text)` [L703-L733] — *Update caption and alt_text fields on an existing WordPress Media Library attachment.*
  - `get_podcast_feeds(self)` [L735-L738] — *Fetch Seriously Simple Podcasting feeds/series or return default feed.*
  - `create_post(self, title, content, excerpt, status, category_ids, author_ids, author_term_ids, featured_media_id, meta, podcast_series, date, slug)` [L740-L918] — *Create a post in WordPress.*
  - `update_post(self, post_id, content, title, excerpt, status, category_ids, featured_media_id, meta, podcast_series, author_ids, author_term_ids, date, slug)` [L920-L1013] — *Update an existing post in WordPress.*
- **class `WordPressSettingsDialog(QDialog)`** (lines 1016–1227):
  *Dialog for entering and testing WordPress site credentials.*
  - `__init__(self, parent)` [L1019-L1171]
  - `_test_connection(self)` [L1173-L1194]
  - `_save_settings(self)` [L1196-L1227]
- **class `WordPressPreferencesPage(QWidget)`** (lines 1241–1441):
  *Preferences page widget for WordPress integration inside the application Preferences dialog.*
  - `__init__(self, parent, app)` [L1244-L1248]
  - `setup_ui(self)` [L1250-L1385]
  - `_test_connection(self)` [L1387-L1406]
  - `save_preferences(self, dialog)` [L1408-L1441]
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
  - `get_wp_client()` [L1230-L1238] — *Instantiate WordPressClient from stored settings if configured.*
  - `_group_segments_into_paragraphs(segments, min_words)` [L1444-L1506] — *Group consecutive segments with same speaker into natural paragraph blocks.*
  - `_build_audio_fade_filter(duration, fade_in, fade_out, fade_curve)` [L1509-L1537] — *Construct FFmpeg afade audio filter chain for story clips.*
  - `execute_wordpress_upload(main_window, client, post_title, post_excerpt, start, end, task_label, include_english, include_spanish, spanish_presentation, primary_language, author_ids, author_term_ids, category_ids, show_completion_dialog, media_filename, progress_callback, featured_image_path, parent_episode_info, link_parent_episode, parent_episode_template, parent_episode_pos, include_audio, fade_in, fade_out, fade_curve, apply_fades, accordion_pos, is_podcast, podcast_feed, podcast_feed_id, podcast_feed_ids, podcast_feeds, podcast_episode_type, podcast_season, podcast_episode_number, youtube_url, youtube_stop_at_end, youtube_placement, youtube_use_story_time, existing_post_id, replace_existing_audio_and_podcast, post_status, publication_date, post_slug, featured_image_caption, featured_image_alt_text)` [L1540-L2169] — *Extract media clip, upload to WordPress media library, and create or update a post.*

### `plugins/wordpress/episode_lookup.py` (498 lines)
*Headless WordPress episode lookup, REST parsing, slug/date helpers, and MP3 download.*
- **Public Exports (`__all__`)**: MODE_NEW_EPISODE, MODE_UPDATE_EXISTING, extract_slug_or_id_from_url, clean_html_to_plain_excerpt, build_story_slug, normalize_wp_iso_date, format_wp_date_for_input, resolve_wp_post_from_url, download_wp_episode_audio
- **Functions**:
  - `extract_slug_or_id_from_url(url_or_id)` [L24-L54] — *Parse a WordPress post URL, query URL, numeric ID, or slug into (post_id, slug).*
  - `clean_html_to_plain_excerpt(raw_html)` [L57-L74] — *Convert WordPress HTML/block content into clean plain text for post excerpts.*
  - `build_story_slug(title)` [L77-L83] — *Build a clean URL-safe WordPress slug from a post title.*
  - `normalize_wp_iso_date(date_str)` [L86-L121] — *Normalize a user-entered date/time string into WordPress ISO-8601 format (YYYY-MM-DDTHH:MM:SS).*
  - `format_wp_date_for_input(iso_date)` [L124-L135] — *Format a WordPress ISO-8601 date string for compact UI display (YYYY-MM-DD HH:MM).*
  - `_extract_audio_url_from_post_payload(post, html_fallback)` [L138-L177] — *Locate the episode MP3 URL from WordPress REST metadata, enclosures, or rendered HTML.*
  - `_parse_wp_post_json(post, client, fallback_url)` [L180-L259] — *Normalize a WordPress REST post dictionary and extract Option B excerpt & audio URL.*
  - `resolve_wp_post_from_url(client, url_or_id)` [L262-L321] — *Fetch an existing WordPress post by URL, slug, or ID via the WordPress REST API.*
  - `_resolve_download_dir(main_window, target_dir)` [L324-L344] — *Choose a writable directory for downloaded WordPress episode audio files.*
  - `download_wp_episode_audio(post_info, main_window, target_dir)` [L347-L420] — *Download the MP3 file associated with an existing WordPress episode post.*
  - `_copy_fetched_post_fields(target, post_info)` [L423-L440] — *Apply normalized WordPress post metadata onto a post item or project wp_meta dict.*
  - `_populate_project_from_fetched_post(main_window, post_info)` [L443-L485] — *Store fetched WordPress post details into main_window.project_metadata for Update mode.*

### `plugins/wordpress/episode_updater.py` (56 lines)
*Backward-compatible facade for WordPress Existing Episode Lookup, Backfill Mode & MP3 Import.*
- **Public Exports (`__all__`)**: MODE_NEW_EPISODE, MODE_UPDATE_EXISTING, extract_slug_or_id_from_url, clean_html_to_plain_excerpt, build_story_slug, normalize_wp_iso_date, format_wp_date_for_input, resolve_wp_post_from_url, download_wp_episode_audio, apply_fetched_post_to_tab, load_episode_updater_from_post, setup_wp_mode_and_date_ui, PublicationDateLineEdit, LoadWordPressEpisodeDialog, prompt_load_existing_wp_episode_dialog

### `plugins/wordpress/episode_updater_ui.py` (570 lines)
*Qt UI panels and dialog for WordPress existing episode lookup and backfill workflow.*
- **Public Exports (`__all__`)**: PublicationDateLineEdit, sync_wp_audio_checkbox_label, load_episode_updater_from_post, apply_fetched_post_to_tab, setup_wp_mode_and_date_ui, LoadWordPressEpisodeDialog, prompt_load_existing_wp_episode_dialog
- **class `LoadWordPressEpisodeDialog(QDialog)`** (lines 408–553):
  *Dialog for starting or updating a project from an existing WordPress/podcast episode URL.*
  - `__init__(self, main_window, parent)` [L411-L469]
  - `_sync_local_row_enabled(self)` [L471-L474]
  - `_on_browse_local(self)` [L476-L485]
  - `_resolve_target(self, url)` [L487-L500]
  - `_on_fetch_clicked(self)` [L502-L517]
  - `_on_load_clicked(self)` [L519-L553]
- **Functions**:
  - `_refresh_dialog_export_button(tab_widget)` [L24-L27]
  - `_is_update_mode(tab_widget)` [L30-L32]
  - `_get_current_tab_post(tab_widget)` [L35-L40]
  - `sync_wp_audio_checkbox_label(tab_widget)` [L43-L57] — *Update the Media tab audio checkbox wording so Update mode clarifies that only new Story clips upload audio.*
  - `_sync_mode_visibility(tab_widget)` [L60-L79] — *Update visibility of the Existing Episode panel and default status dropdowns.*
  - `load_episode_updater_from_post(tab_widget, post)` [L82-L122] — *Synchronize mode, URL, publication date, and status controls from project and post data.*
  - `_update_existing_status_label(tab_widget, post)` [L125-L144]
  - `apply_fetched_post_to_tab(tab_widget, post_info, target_idx)` [L147-L175] — *Populate tab_widget's target post (default: current or Full Episode) with fetched WP post data.*
  - `_get_configured_client(parent_widget)` [L178-L194]
  - `setup_wp_mode_and_date_ui(tab_widget, parent_section)` [L197-L405] — *Build workflow mode toggle, existing post URL lookup, publication date, and status controls.*
  - `prompt_load_existing_wp_episode_dialog(main_window, parent)` [L556-L559] — *Launch the Load Existing WordPress Episode dialog and return True if accepted.*

### `plugins/wordpress/export_destination.py` (880 lines)
*WordPress Export Destination for UnifiedExportDialog.*
- **Public Exports (`__all__`)**: WordPressExportDestination, WordPressExportTabWidget, WordPressPostMetadataDialog, capture_video_frame, build_wp_post_items, build_episode_stories_toc, format_parent_episode_notice, is_wp_auth_error, SS_PODCAST_AUDIO_FILE, SS_PODCAST_AUDIO_FILE_ID, SS_PODCAST_DURATION, SS_PODCAST_FILESIZE, SS_PODCAST_FEED, SS_PODCAST_EPISODE_TYPE, CASTOS_SHORTCODE, CASTOS_PLAYER_BLOCK, build_castos_post_meta, format_castos_duration, fetch_castos_feeds
- **class `WordPressExportDestination(ExportDestination)`** (lines 37–759):
  *Export destination handler for WordPress REST API Draft Posts.*
  - `__init__(self, plugin)` [L40-L48]
  - `button_label(self)` [L51-L61]
  - `button_label(self, val)` [L64-L65]
  - `get_export_button_label(self)` [L67-L68]
  - `widget(self)` [L71-L72]
  - `widget(self, val)` [L75-L76]
  - `create_widget(self, parent, main_window)` [L78-L80]
  - `_ensure_tab_widget(self)` [L82-L98] — *Defensive resolver to bind tab_widget from cached dialog entries if unlinked.*
  - `on_scope_changed(self, scope, stories)` [L100-L103]
  - `validate(self)` [L105-L141]
  - `get_export_data(self)` [L143-L176]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L178-L759]
- **class `WordPressPostMetadataDialog(QDialog)`** (lines 762–842):
  *Full-featured WordPress post & story metadata editor dialog.*
  - `__init__(self, parent, main_window, target_story_index)` [L765-L821]
  - `_on_save_clicked(self)` [L823-L828]
  - `_on_close_clicked(self)` [L830-L832]
  - `_on_save_and_close(self)` [L834-L835]
  - `done(self, r)` [L837-L842]

### `plugins/wordpress/plugin.py` (112 lines)
*WordPress Publisher Plugin for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: Plugin, WordPressPublishDialog, WordPressPublishWorker, capture_video_frame
- **class `Plugin(BasePlugin)`** (lines 17–104):
  *WordPress Plugin implementation hooking into RTVS.*
  - `__init__(self, manifest, app)` [L20-L21]
  - `on_load(self)` [L23-L24]
  - `get_export_destinations(self)` [L26-L28]
  - `get_file_open_actions(self)` [L30-L33]
  - `get_remote_open_actions(self)` [L35-L38]
  - `can_redownload_remote_source(self, source_meta)` [L40-L41]
  - `redownload_remote_source(self, source_meta, parent)` [L43-L56]
  - `get_export_actions(self)` [L58-L68]
  - `open_load_existing_episode_dialog(self)` [L70-L72]
  - `get_story_actions(self, story)` [L74-L78]
  - `create_story_metadata_widget(self, parent)` [L80-L82]
  - `on_story_selected(self, story)` [L84-L85]
  - `get_preferences_widget(self, parent)` [L87-L89]
  - `open_publish_dialog(self, parent, story)` [L91-L93]
  - `open_post_metadata_dialog(self, parent, story)` [L95-L104]

### `plugins/wordpress/pub_date_picker.py` (338 lines)
*Non-focus-stealing click-to-drop-down calendar & time picker for WordPress publication dates.*
- **Public Exports (`__all__`)**: PublicationDateLineEdit
- **class `_PublicationDatePickerPopup(QFrame)`** (lines 49–271):
  *Frameless, non-focus-stealing calendar and 24-hour time dropdown for PublicationDateLineEdit.*
  - `__init__(self, anchor, parent)` [L52-L109]
  - `sync_from_text(self, raw_text)` [L111-L128] — *Align calendar and time widgets to `raw_text`, or today's date/time when blank.*
  - `_apply_selected_datetime(self)` [L130-L141]
  - `_on_date_clicked(self, qdate)` [L143-L150]
  - `_on_date_activated(self, qdate)` [L152-L154]
  - `_on_time_changed(self, *_args)` [L156-L158]
  - `_on_now_clicked(self)` [L160-L168]
  - `_on_clear_clicked(self)` [L170-L174]
  - `_on_done_clicked(self)` [L176-L179]
  - `_install_filters(self)` [L181-L191]
  - `_remove_filters(self)` [L193-L208]
  - `show_for_anchor(self)` [L210-L235] — *Position below (or above if needed) the anchor QLineEdit without stealing focus.*
  - `hideEvent(self, event)` [L237-L239]
  - `keyPressEvent(self, event)` [L241-L248]
  - `eventFilter(self, obj, event)` [L250-L271]
- **class `PublicationDateLineEdit(QLineEdit)`** (lines 274–335):
  *Editable QLineEdit that opens a non-intrusive calendar/time dropdown on click.*
  - `__init__(self, parent)` [L277-L288]
  - `_ensure_popup(self)` [L290-L293]
  - `open_picker(self)` [L295-L301] — *Open the calendar/time dropdown anchored to this input without stealing focus.*
  - `close_picker(self)` [L303-L306] — *Close the dropdown if currently open.*
  - `_on_text_edited_sync_popup(self, text)` [L308-L310]
  - `mousePressEvent(self, event)` [L312-L315]
  - `keyPressEvent(self, event)` [L317-L335]
- **Functions**:
  - `_is_qt_valid(obj)` [L22-L31] — *Return False when `obj` is None or its underlying C++ Qt object was deleted.*
  - `_is_widget_or_descendant(candidate, ancestor)` [L34-L46] — *Return True if `candidate` is `ancestor` or nested beneath it in the widget tree.*

### `plugins/wordpress/wordpress_dialog.py` (28 lines)
*Backward-compatible facade for legacy WordPress dialog imports.*
- **Public Exports (`__all__`)**: WordPressExportTabWidget, WordPressPostMetadataDialog, capture_video_frame, generate_wp_excerpt
- **Functions**:
  - `generate_wp_excerpt(transcript_words, start_t, end_t)` [L15-L20] — *Legacy wrapper preserving the historical `(transcript_words, start_t, end_t)` signature.*

### `plugins/wordpress/wp_post_builder.py` (456 lines)
*Post item builder, transcript slicing, and video frame extraction for WordPress export.*
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path, timeout)` [L19-L41] — *Capture a single frame from video at timestamp using ffmpeg.*
  - `get_primary_text_slice(main_window, primary_lang, st_start, st_end)` [L44-L73] — *Extract transcript or translated text for the specified time slice.*
  - `build_wp_post_items(main_window, scope, primary_lang, existing_items, include_full_episode)` [L76-L431] — *Build the list of WordPress post definitions according to the export scope.*
  - `sync_featured_image_meta(wp_meta, post, container_meta)` [L434-L456] — *Persist featured image path, mode, user-set flag, caption, alt text, and frame position.*

### `plugins/wordpress/wp_publish_dialog.py` (524 lines)
*WordPress single-story publish dialog with featured image and notice options.*
- **Public Exports (`__all__`)**: WordPressPublishDialog
- **class `WordPressPublishDialog(QDialog)`** (lines 46–521):
  *Publish a story or project to WordPress with featured image selection.*
  - `__init__(self, plugin, parent, story)` [L49-L63]
  - `_resolve_spellcheck_context(self)` [L65-L68]
  - `setup_ui(self)` [L70-L263]
  - `load_custom_text_settings(self)` [L265-L278] — *Load persistent custom text defaults from application settings.*
  - `save_custom_text_defaults(self)` [L280-L286] — *Save active custom text, placement, and exclusion settings as persistent defaults.*
  - `load_metadata(self)` [L288-L329]
  - `do_capture_frame(self)` [L331-L341]
  - `on_image_mode_changed(self)` [L343-L360]
  - `on_browse_image(self)` [L362-L373]
  - `on_configure_credentials(self)` [L375-L380]
  - `on_publish(self)` [L382-L479]
  - `on_publish_finished(self, success, msg, post_data)` [L481-L514]
  - `closeEvent(self, event)` [L516-L521]

### `plugins/wordpress/wp_tab_widget.py` (997 lines)
*WordPress export tab configuration widget and preview controller.*
- **class `WordPressExportTabWidget(QWidget)`** (lines 43–996):
  *Configuration and preview panel for WordPress Draft Posts.*
  - `__init__(self, parent, main_window, metadata_editor_mode)` [L55-L75]
  - `_setup_ui(self)` [L77-L78]
  - `_on_wp_include_audio_toggled(self, checked)` [L80-L117]
  - `_update_wp_conn_status(self)` [L119-L127]
  - `_open_wp_settings(self)` [L129-L133]
  - `_filter_authors_list(self, text)` [L135-L139]
  - `_filter_categories_list(self, text)` [L141-L145]
  - `_sync_to_proj(self, idx)` [L147-L149]
  - `_on_title_edited(self, text)` [L151-L164]
  - `_on_excerpt_edited(self)` [L166-L171]
  - `_auto_generate_current_excerpt(self)` [L173-L181]
  - `_autofill_all_excerpts(self)` [L183-L194]
  - `_on_author_item_changed(self, item)` [L196-L204]
  - `_sync_categories_to_all_stories(self, cat_ids)` [L206-L213] — *Copy category_ids to every Story item in wp_post_items without altering Full Episode.*
  - `_on_cats_apply_all_stories_toggled(self, checked)` [L215-L222]
  - `_on_category_item_changed(self, item)` [L224-L233]
  - `_clear_current_authors(self)` [L235-L241]
  - `_clear_current_categories(self)` [L243-L251]
  - `_get_selected_story_indices(self)` [L253-L257]
  - `_apply_authors_to_selected_stories(self)` [L259-L260]
  - `_apply_categories_to_selected_stories(self)` [L262-L263]
  - `_apply_thumbnails_to_selected_stories(self)` [L265-L266]
  - `_bulk_apply_to_selected(self, *keys)` [L268-L300]
  - `_apply_authors_to_all_posts(self)` [L302-L303]
  - `_apply_categories_to_all_posts(self)` [L305-L306]
  - `_apply_thumbnails_to_all_posts(self)` [L308-L309]
  - `_bulk_apply_to_all(self, *keys)` [L311-L330]
  - `_apply_podcast_to_selected_stories(self)` [L332-L362]
  - `_apply_podcast_to_all_posts(self)` [L364-L379]
  - `_sync_post_to_project(self, idx, log_reason)` [L381-L483]
  - `save_all_posts_to_project(self)` [L485-L510] — *Persist all post metadata and export options back into stories and project_metadata.*
  - `get_sidebar_decorations(self)` [L512-L514]
  - `_notify_export_sidebar_decorations(self)` [L516-L521]
  - `_update_post_list_item_label(self, idx)` [L523-L533]
  - `_on_wp_post_selection_changed(self, row)` [L535-L538]
  - `_get_editor_checked_authors(self)` [L540-L548]
  - `_set_editor_checked_authors(self, author_ids, author_term_ids)` [L550-L557]
  - `_get_editor_checked_categories(self)` [L559-L567]
  - `_set_editor_checked_categories(self, cat_ids)` [L569-L577]
  - `_get_wp_post_bounds(self, post_index)` [L579-L588]
  - `_sync_wp_slider_to_pos(self, pos)` [L590-L600]
  - `_on_wp_slider_value_changed(self, val)` [L602-L611]
  - `_on_wp_scrub_timer_timeout(self)` [L613-L617]
  - `_on_wp_step(self, delta_secs)` [L619-L627]
  - `_on_wp_sync_playhead(self)` [L629-L636]
  - `_load_post_editor_state(self, index)` [L638-L672]
  - `_on_wp_thumb_mode_changed(self)` [L674-L675]
  - `_on_wp_thumb_meta_changed(self)` [L677-L684]
  - `_capture_wp_frame(self, pos, user_initiated)` [L686-L725]
  - `_on_wp_browse_thumb(self)` [L727-L749]
  - `_cleanup_temp_files(self)` [L751-L760] — *Purge temporary frame grabs and preview images.*
  - `closeEvent(self, event)` [L762-L779] — *Persist current post state, stop background thumbnail workers, and clean up temp files.*
  - `select_full_episode(self)` [L781-L790]
  - `select_story_index(self, story_idx)` [L792-L801]
  - `rebuild_post_items(self, scope)` [L803-L875]
  - `_populate_wp_export_metadata(self, force_refresh)` [L877-L944]
  - `_prompt_wp_credentials(self, title, message)` [L946-L959]
  - `_refresh_castos_feeds(self)` [L961-L978]
  - `_refresh_wp_metadata(self)` [L980-L996]

### `plugins/wordpress/wp_thumb_ui.py` (399 lines)
*UI presentation controller for WordPress Featured Image controls and preview.*
- **Public Exports (`__all__`)**: ClickableThumbnailLabel, FeaturedImageLightboxDialog, set_preview_pixmap, clear_preview_pixmap, open_featured_image_preview, load_featured_image_from_post, on_featured_image_mode_changed, on_youtube_thumbnail_fetched
- **class `ClickableThumbnailLabel(QLabel)`** (lines 21–59):
  *QLabel preview that opens a full-size preview dialog when clicked.*
  - `__init__(self, text, parent)` [L26-L29]
  - `set_full_image(self, image_path, source_description)` [L31-L38]
  - `clear_full_image(self)` [L40-L44]
  - `full_image_path(self)` [L46-L47]
  - `mousePressEvent(self, event)` [L49-L59]
- **class `FeaturedImageLightboxDialog(QDialog)`** (lines 62–134):
  *Lightweight resizable modal lightbox displaying a full-resolution featured image.*
  - `__init__(self, image_path, source_description, parent)` [L65-L115]
  - `_update_scaled_pixmap(self)` [L117-L130]
  - `resizeEvent(self, event)` [L132-L134]
- **Functions**:
  - `set_preview_pixmap(tab_widget, image_path, source_description)` [L137-L150] — *Display scaled preview thumbnail and enable click-to-enlarge for *image_path*.*
  - `clear_preview_pixmap(tab_widget, placeholder_text)` [L153-L161] — *Clear preview pixmap, disable click-to-enlarge, and show *placeholder_text*.*
  - `open_featured_image_preview(tab_widget)` [L164-L174] — *Open the full-resolution lightbox preview for the current WordPress featured image.*
  - `_set_preview_pixmap(tab_widget, image_path, source_description)` [L177-L178]
  - `_start_youtube_thumbnail_fetch(tab_widget, video_id, thumbnail_url)` [L181-L203] — *Kick off a non-blocking background QThread fetch for a YouTube default thumbnail.*
  - `on_youtube_thumbnail_fetched(tab_widget, video_id, local_path)` [L206-L235] — *Apply downloaded YouTube thumbnail preview on the Qt main thread if still relevant.*
  - `load_featured_image_from_post(tab_widget, index, post)` [L238-L316] — *Populate Featured Image radio buttons, scrubber, and preview from a post dict.*
  - `on_featured_image_mode_changed(tab_widget)` [L319-L387] — *Handle user selection of Featured Image radio buttons.*

### `plugins/wordpress/wp_thumbnail_defaults.py` (445 lines)
*Headless YouTube-source featured image defaults, thumbnail caching, and embed inheritance.*
- **Public Exports (`__all__`)**: extract_youtube_id_headless, get_youtube_thumbnail_cache_path, get_youtube_source_info, resolve_post_youtube_video_id, resolve_inherited_youtube_embed, compute_default_segment_frame_pos, should_apply_youtube_featured_default, build_youtube_thumbnail_candidates, ensure_youtube_thumbnail_cached, materialize_post_featured_image
- **Functions**:
  - `extract_youtube_id_headless(url_or_id)` [L35-L68] — *Extract a validated 11-character YouTube video ID without Qt dependencies.*
  - `get_youtube_thumbnail_cache_path(video_id, cache_dir)` [L71-L81] — *Return the deterministic local cache path for a YouTube video's default thumbnail.*
  - `get_youtube_source_info(main_window, cache_dir)` [L84-L131] — *Inspect project metadata to determine whether the active source media is from YouTube.*
  - `resolve_post_youtube_video_id(post, main_window)` [L134-L141] — *Resolve the active 11-character YouTube video ID for a post or YouTube-source project.*
  - `resolve_inherited_youtube_embed(main_window, story_wp_meta)` [L144-L199] — *Resolve episode-level YouTube embed settings that individual stories should inherit.*
  - `compute_default_segment_frame_pos(start, end, fallback)` [L202-L219] — *Compute a representative video timestamp strictly inside ``[start, end]``.*
  - `should_apply_youtube_featured_default(wp_meta, container_meta)` [L222-L244] — *Return True when no explicit featured image preference has been chosen yet.*
  - `build_youtube_thumbnail_candidates(video_id, thumbnail_url)` [L247-L269] — *Return ordered HTTPS YouTube thumbnail candidate URLs preferring high-res JPEG.*
  - `_normalize_thumbnail_bytes_to_jpeg(raw)` [L272-L300] — *Validate downloaded thumbnail bytes and normalize PNG/WEBP payloads to JPEG.*
  - `_default_http_fetch(url, timeout)` [L303-L312]
  - `ensure_youtube_thumbnail_cached(video_id, thumbnail_url, timeout, cache_dir, fetcher)` [L315-L346] — *Download (if needed) and atomically cache a YouTube video's default thumbnail.*
  - `materialize_post_featured_image(post, main_window, post_index, temp_files_out, allow_network, cache_dir, fetcher, frame_capturer)` [L349-L431] — *Ensure a post's configured featured image exists on disk and return its path.*

### `plugins/wordpress/wp_ui_builder.py` (996 lines)
*UI layout construction and widget setup for WordPressExportTabWidget.*
- **Functions**:
  - `setup_wp_tab_ui(self)` [L39-L885] — *Construct all controls, forms, sliders, list widgets, and tabbed panels for the WordPress export tab.*
  - `_format_excluded_role_label(tab_widget, role_value)` [L888-L903] — *Return a clean human-readable name for a sidebar role value (-1 or story index).*
  - `show_wp_excluded_placeholder(tab_widget, role_value)` [L906-L931] — *Hide per-post metadata controls and explain that the focused item is unchecked for export.*
  - `hide_wp_excluded_placeholder(tab_widget)` [L934-L939] — *Restore the active WordPress post metadata editor controls.*
  - `include_excluded_item_in_export(tab_widget)` [L942-L961] — *Check the currently focused excluded item in ExportStorySelectorSidebar and open its editor.*
  - `sync_wp_excluded_state_for_sidebar(tab_widget, ext_sidebar, fallback_row)` [L964-L996] — *Return the wp_post_items row to display, or None if the Not Included placeholder was shown.*

### `plugins/wordpress/wp_workers.py` (106 lines)
*Background QThread worker for publishing individual WordPress stories.*
- **Public Exports (`__all__`)**: WordPressPublishWorker, YouTubeThumbnailFetchWorker
- **class `WordPressPublishWorker(QThread)`** (lines 13–75):
  *Background thread that uploads featured media and publishes a WordPress post.*
  - `__init__(self, client, title, content, excerpt, status, image_path, image_caption, image_alt_text)` [L18-L37]
  - `run(self)` [L39-L75]
- **class `YouTubeThumbnailFetchWorker(QThread)`** (lines 78–103):
  *Background thread that downloads and caches a YouTube video's default thumbnail.*
  - `__init__(self, video_id, thumbnail_url, timeout)` [L83-L87]
  - `run(self)` [L89-L103]

### `plugins/wordpress/youtube_embed.py` (672 lines)
*YouTube Video Embed helpers, Gutenberg iframe generator, and UI setup for WordPress export.*
- **Functions**:
  - `extract_youtube_video_id(url_or_id)` [L29-L142] — *Extract the clean 11-character YouTube Video ID and optional start timestamp (seconds).*
  - `build_youtube_embed_block(video_id, start_sec, end_sec, stop_at_end)` [L145-L188] — *Generate a responsive Gutenberg HTML embed block for a YouTube video.*
  - `setup_wp_youtube_ui(tab_widget, parent_layout)` [L191-L273] — *Construct the 'YouTube Video Embed' CollapsibleSection inside the Media tab.*
  - `_get_current_post(tab_widget)` [L276-L282]
  - `_set_youtube_controls_enabled(tab_widget, enabled)` [L285-L322] — *Enable or disable YouTube embed options based on whether a valid video URL is present.*
  - `update_youtube_status_label(tab_widget)` [L325-L382] — *Refresh the dynamic status preview line below the YouTube URL input.*
  - `load_youtube_from_post(tab_widget, post)` [L385-L442] — *Populate YouTube controls from the given post dictionary.*
  - `sync_youtube_to_meta(target_meta, post)` [L445-L454] — *Sync YouTube embed settings from post to target_meta dictionary.*
  - `_on_youtube_url_changed(tab_widget, text)` [L457-L510]
  - `_on_youtube_apply_all_toggled(tab_widget, checked)` [L513-L522]
  - `_on_youtube_use_story_time_toggled(tab_widget, checked)` [L525-L535]
  - `_on_youtube_stop_at_end_toggled(tab_widget, checked)` [L538-L548]
  - `_on_youtube_placement_toggled(tab_widget, placement)` [L551-L561]
  - `format_post_list_label_and_tooltip(tab_widget, idx)` [L564-L654] — *Return formatted label text and rich multi-line tooltip for an item in wp_posts_list.*
  - `build_wp_sidebar_decorations(tab_widget)` [L657-L672] — *Build {role_value: (label_text, tooltip_text)} map for ExportStorySelectorSidebar.*

### `plugins/youtube/__init__.py` (9 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*

### `plugins/youtube/export_destination.py` (618 lines)
*YouTube Export Destination for UnifiedExportDialog with Zero-Auth Manual Publishing.*
- **class `YouTubeExportTabWidget(QWidget)`** (lines 87–534):
  *Configuration and preview panel for YouTube Zero-Auth Manual Publishing.*
  - `__init__(self, parent, main_window)` [L90-L103]
  - `_setup_ui(self)` [L105-L350]
  - `_get_yt_bounds(self)` [L352-L376]
  - `_on_yt_thumb_mode_changed(self)` [L378-L395]
  - `_update_yt_scrub_slider_range(self)` [L397-L406]
  - `_on_yt_slider_value_changed(self, value)` [L408-L414]
  - `_on_yt_step(self, delta_sec)` [L416-L421]
  - `_on_yt_sync_playhead(self)` [L423-L428]
  - `_schedule_yt_frame_preview(self)` [L430-L433]
  - `_on_yt_scrub_timer_timeout(self)` [L435-L449]
  - `_on_yt_browse_thumb(self)` [L451-L462]
  - `_cleanup_temp_files(self)` [L464-L473] — *Purge temporary thumbnail frame grabs.*
  - `closeEvent(self, event)` [L475-L478] — *Clean up temporary thumbnail files on closure.*
  - `reject(self)` [L480-L483] — *Ensure temp preview files are purged on dialog rejection.*
  - `done(self, r)` [L485-L488] — *Ensure temp preview files are purged on dialog completion.*
  - `populate_metadata(self)` [L490-L534] — *Builds default title, description, chapter timestamps, and speaker credits from current stories.*
- **class `YouTubeExportDestination(ExportDestination)`** (lines 537–618):
  *Export destination handler for YouTube Zero-Auth Manual Publishing.*
  - `__init__(self, plugin)` [L540-L548]
  - `create_widget(self, parent, main_window)` [L550-L552]
  - `_ensure_tab_widget(self)` [L554-L570] — *Defensive resolver to bind tab_widget from cached dialog entries if unlinked.*
  - `on_scope_changed(self, scope, stories)` [L572-L575]
  - `validate(self)` [L577-L583]
  - `get_export_data(self)` [L585-L612]
  - `execute_export(self, main_window, export_data, progress_dialog)` [L614-L618]
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

### `plugins/youtube/plugin.py` (291 lines)
*YouTube Video Publisher Plugin for Radio & TV Segmenter.*
- **class `YouTubeSettingsDialog(QDialog)`** (lines 63–224):
  *Preferences dialog for YouTube Publishing (Zero-Auth Assisted Upload defaults).*
  - `__init__(self, parent)` [L66-L73]
  - `setup_ui(self)` [L75-L208]
  - `on_save(self)` [L210-L224]
- **class `Plugin(BasePlugin)`** (lines 227–291):
  *YouTube Video Publisher plugin hooking into RTVS.*
  - `on_load(self)` [L230-L231]
  - `get_export_destinations(self)` [L233-L235]
  - `get_remote_open_actions(self)` [L237-L240]
  - `get_cache_maintenance_actions(self)` [L242-L246]
  - `can_redownload_remote_source(self, source_meta)` [L248-L249]
  - `redownload_remote_source(self, source_meta, parent)` [L251-L253]
  - `get_export_actions(self)` [L255-L258]
  - `get_preferences_widget(self, parent)` [L260-L283]
  - `open_load_youtube_video_dialog(self)` [L285-L287]
  - `open_publish_dialog(self)` [L289-L291]
- **Functions**:
  - `capture_video_frame(video_path, timestamp, output_path)` [L45-L60]

### `plugins/youtube/yt_dlp_runner.py` (871 lines)
*Headless yt-dlp runtime provisioner, URL parser, metadata prober, and downloader.*
- **Public Exports (`__all__`)**: DEFAULT_YOUTUBE_QUALITY, YOUTUBE_QUALITY_PRESETS, ALLOWED_COOKIE_BROWSERS, extract_youtube_id_strict, normalize_quality_preset, normalize_cookie_browser, get_format_selector_for_preset, get_yt_dlp_tools_dir, get_platform_yt_dlp_asset_name, get_managed_yt_dlp_path, find_yt_dlp_binary, get_yt_dlp_version, parse_sha256_sums, install_or_update_yt_dlp, format_upload_date, build_youtube_project_stem, estimate_preset_size_bytes, parse_youtube_chapters, parse_yt_dlp_metadata_json, classify_yt_dlp_error, parse_yt_dlp_progress_line, build_yt_dlp_probe_command, probe_youtube_video, build_yt_dlp_download_command, download_youtube_video
- **Functions**:
  - `_subprocess_creation_flags()` [L63-L64]
  - `_resolve_app_data_root()` [L67-L76]
  - `_resolve_ffmpeg_location()` [L79-L94] — *Return the bundled/configured FFmpeg path or directory if available.*
  - `extract_youtube_id_strict(url_or_id)` [L97-L148] — *Validate a YouTube URL or raw 11-char ID and return (video_id, canonical_url).*
  - `normalize_quality_preset(preset)` [L151-L154]
  - `normalize_cookie_browser(browser)` [L157-L159]
  - `get_format_selector_for_preset(preset)` [L162-L189] — *Return (yt-dlp -f format selector, target output extension) for a quality preset.*
  - `get_yt_dlp_tools_dir(base_dir)` [L192-L195]
  - `get_platform_yt_dlp_asset_name(platform_name)` [L198-L204]
  - `get_managed_yt_dlp_path(base_dir, platform_name)` [L207-L210]
  - `find_yt_dlp_binary(base_dir, allow_system_fallback)` [L213-L225] — *Locate the managed yt-dlp binary, optionally falling back to system PATH.*
  - `get_yt_dlp_version(binary_path)` [L228-L246] — *Return the version string reported by `yt-dlp --version`, or empty string.*
  - `parse_sha256_sums(sums_text, asset_name)` [L249-L261] — *Extract the expected lowercase SHA-256 hex digest for ``asset_name`` from SHA2-256SUMS.*
  - `_sha256_file(path)` [L264-L272]
  - `install_or_update_yt_dlp(base_dir, progress_callback, cancel_check, platform_name)` [L275-L364] — *Download, SHA-256 verify, and install the latest official standalone yt-dlp binary.*
  - `format_upload_date(raw_yyyymmdd)` [L367-L372] — *Convert yt-dlp upload_date ('20260412') into '2026-04-12'.*
  - `build_youtube_project_stem(title, upload_date, video_id)` [L375-L388] — *Build a clean, readable default .rtvs project stem from title + upload date.*
  - `estimate_preset_size_bytes(info, preset)` [L391-L453] — *Estimate download size in bytes for a quality preset from yt-dlp metadata.*
  - `parse_youtube_chapters(info)` [L456-L479] — *Normalize yt-dlp chapters list into [{title, start, end}].*
  - `parse_yt_dlp_metadata_json(raw_info, fallback_url)` [L482-L505] — *Normalize raw `yt-dlp --dump-single-json` output into a clean metadata dict.*
  - `classify_yt_dlp_error(stderr_text)` [L508-L586] — *Translate raw yt-dlp error stderr into actionable user-facing guidance.*
  - `parse_yt_dlp_progress_line(line)` [L596-L637] — *Parse a yt-dlp stdout line into structured download/merge progress.*
  - `build_yt_dlp_probe_command(yt_dlp_bin, canonical_url, cookies_browser)` [L640-L656]
  - `probe_youtube_video(url_or_id, yt_dlp_bin, cookies_browser, timeout)` [L659-L699] — *Fetch normalized metadata, chapters, and size estimates for a YouTube video.*
  - `build_yt_dlp_download_command(yt_dlp_bin, canonical_url, output_base_path, quality_preset, cookies_browser, ffmpeg_location)` [L702-L732] — *Construct a safe argument list for yt-dlp video/audio download.*
  - `download_youtube_video(url_or_id, output_dir, filename_stem, quality_preset, yt_dlp_bin, cookies_browser, progress_callback, cancel_check, process_callback)` [L735-L842] — *Download and remux a YouTube video into ``output_dir`` with streaming progress.*

### `plugins/youtube/yt_import_dialog.py` (754 lines)
*Qt Dialogs for importing existing YouTube videos, re-downloading archived sources, and updating yt-dlp.*
- **Public Exports (`__all__`)**: populate_project_from_youtube_import, LoadYouTubeEpisodeDialog, open_yt_dlp_updater_dialog, prompt_load_youtube_episode_dialog, redownload_youtube_source_dialog
- **class `LoadYouTubeEpisodeDialog(QDialog)`** (lines 186–632):
  *Dialog for fetching, configuring, downloading, and opening an existing YouTube video.*
  - `__init__(self, main_window, parent, initial_url, initial_quality, redownload_mode)` [L189-L218]
  - `_build_ui(self, initial_url, initial_quality)` [L220-L375]
  - `_refresh_yt_dlp_status(self)` [L377-L384]
  - `_set_busy(self, busy)` [L386-L395]
  - `_refresh_quality_estimate_and_cache(self)` [L397-L419]
  - `_render_meta_summary(self)` [L421-L435]
  - `_start_probe(self)` [L437-L459]
  - `_on_probe_finished(self, meta)` [L461-L476]
  - `_start_download(self)` [L478-L541]
  - `_on_download_finished(self, result)` [L543-L549]
  - `_on_worker_progress(self, pct, msg)` [L551-L553]
  - `_on_worker_failed(self, msg, err_meta)` [L555-L570]
  - `_start_yt_dlp_update(self, retry_after)` [L572-L602]
  - `_on_retry_with_cookies(self)` [L604-L615]
  - `_cancel_active_workers(self)` [L617-L620]
  - `_on_cancel_clicked(self)` [L622-L628]
  - `closeEvent(self, event)` [L630-L632]
- **Functions**:
  - `_trim_youtube_description_for_excerpt(description, max_chars)` [L59-L69] — *Extract a clean short summary from a YouTube description for the project excerpt.*
  - `populate_project_from_youtube_import(main_window, video_meta, file_path, quality_preset, cache_key, import_chapters, existing_wp_url)` [L72-L183] — *Populate project metadata, WordPress YouTube embed state, and optional chapters.*
  - `open_yt_dlp_updater_dialog(parent)` [L635-L681] — *Quick standalone updater dialog triggered from Cache Manager or Preferences.*
  - `prompt_load_youtube_episode_dialog(main_window, parent)` [L684-L722] — *Launch the YouTube import dialog, respect unsaved-project guard, and load downloaded media.*
  - `redownload_youtube_source_dialog(main_window, source_meta, parent)` [L725-L745] — *Re-download an archived YouTube source for an existing .rtvs project.*

### `plugins/youtube/yt_import_workers.py` (250 lines)
*Background QThread workers for yt-dlp provisioning, YouTube metadata probing, and video downloads.*
- **Public Exports (`__all__`)**: YtDlpInstallWorker, YouTubeProbeWorker, YouTubeDownloadWorker
- **class `YtDlpInstallWorker(QThread)`** (lines 30–56):
  *Background worker that installs or updates the managed yt-dlp binary.*
  - `__init__(self, parent, base_dir)` [L37-L40]
  - `cancel(self)` [L42-L43]
  - `run(self)` [L45-L56]
- **class `YouTubeProbeWorker(QThread)`** (lines 59–109):
  *Background worker that ensures yt-dlp is installed and probes YouTube video metadata.*
  - `__init__(self, url_or_id, cookies_browser, parent)` [L66-L75]
  - `cancel(self)` [L77-L78]
  - `run(self)` [L80-L109]
- **class `YouTubeDownloadWorker(QThread)`** (lines 112–243):
  *Background worker that downloads a YouTube video into the Managed Remote Media Cache.*
  - `__init__(self, url_or_id, video_meta, quality_preset, cookies_browser, force_redownload, cache_cap_gb, protected_paths, parent)` [L119-L139]
  - `cancel(self)` [L141-L148]
  - `_set_active_proc(self, proc)` [L150-L151]
  - `run(self)` [L153-L243]

### `preferences_dialog.py` (911 lines)
*Radio & TV Story Segmenter — Preferences Modal Dialog.*
- **class `PreferencesDialogMixin(PreferencesResetMixin)`** (lines 32–911):
  *Provides the main open_preferences_dialog method and settings persistence.*
  - `open_preferences_dialog(self, initial_category, modal)` [L35-L911] — *Open the multi-category Preferences dialog as a non-modal floating inspector.*

### `preferences_reset.py` (684 lines)
*Radio & TV Story Segmenter — Preferences Reset & Factory Defaults Engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 21–165):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L43-L126]
  - `_select_all(self)` [L128-L130]
  - `_deselect_all(self)` [L132-L134]
  - `_handle_reset(self)` [L136-L165]
- **class `PreferencesResetMixin`** (lines 168–684):
  *Provides methods for resetting settings to defaults across all app categories.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L171-L673] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L675-L684] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_reset_dialog.py` (643 lines)
*Radio & TV Segmenter — Preferences reset and factory default restore engine.*
- **class `RestoreSelectedSettingsDialog(QDialog)`** (lines 20–163):
  *Presents users with a list of customizable settings that can be restored to defaults.*
  - `__init__(self, parent, on_restore_selected)` [L41-L124]
  - `_select_all(self)` [L126-L128]
  - `_deselect_all(self)` [L130-L132]
  - `_handle_reset(self)` [L134-L163]
- **class `PreferencesResetMixin`** (lines 166–642):
  *Mixin providing settings reset and restore dialog actions.*
  - `apply_settings_reset(self, selected_ids, live_widgets)` [L169-L631] — *Apply factory default settings to the requested categories and update live widgets if present.*
  - `open_restore_system_defaults_dialog(self)` [L633-L642] — *Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center.*

### `preferences_tab_daw.py` (138 lines)
*preferences_tab_daw.py — External Audio & Video Editors Preferences Tab.*
- **Functions**:
  - `build_external_editors_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L22-L138] — *Construct the External Audio & Video Editors preferences tab.*

### `preferences_tabs_core.py` (626 lines)
*Radio & TV Story Segmenter — Preferences Modal Core Tab Builders.*
- **Functions**:
  - `build_general_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L26-L187]
  - `build_shortcuts_tab(win, dialog, live_widgets)` [L190-L198]
  - `build_audio_hardware_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L201-L344]
  - `build_updates_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L347-L386]
  - `build_ai_models_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L389-L515]
  - `build_gpu_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L518-L626]

### `preferences_tabs_media.py` (731 lines)
*Radio & TV Story Segmenter — Preferences Modal Media & Workflow Tab Builders.*
- **Functions**:
  - `build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L22-L182]
  - `build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L185-L310]
  - `build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L313-L436]
  - `build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L439-L646]
  - `build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn)` [L649-L731]

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

### `processing.py` (1273 lines)
*Radio & TV Segmenter v3.3.29 — processing responsibilities.*
- **class `RuntimeSetupWorker(QThread)`** (lines 56–85):
  *Runs runtime_manager.ensure_environment() off the GUI thread, so that*
  - `__init__(self, runtime_mgr, feature, parent, ensure_kwargs)` [L64-L69]
  - `cancel(self)` [L71-L72]
  - `run(self)` [L74-L85]
- **class `ProcessingMixin(TranscriptionProcessingMixin, DiarizationProcessingMixin, StoryDetectionProcessingMixin)`** (lines 92–1272):
  - `_ensure_runtime_environment_responsive(self, feature, **ensure_kwargs)` [L103-L193] — *Make sure the isolated venv for `feature` is ready before*
  - `cancel_current_process(self)` [L195-L329]
  - `update_skip_stage_button_visibility(self)` [L331-L341] — *Show or hide the 'Skip Stage' button based on active pipeline state.*
  - `skip_current_pipeline_stage(self)` [L343-L391] — *Cancel the active pipeline stage and advance directly to the next queued stage.*
  - `commit_story_change(self, old_stories, new_stories, description)` [L393-L408]
  - `apply_story_selection_indices(self, selected_rows, seek)` [L410-L499]
  - `on_timeline_story_clicked(self, index)` [L501-L511] — *Handle user clicking a story region directly on the timeline canvas.*
  - `story_selection_changed(self)` [L513-L530]
  - `handle_timeline_multi_selection(self, selected_indices)` [L532-L543]
  - `set_tools_actions_enabled(self, enabled)` [L545-L581]
  - `stop_story_detection_worker(self, timeout_ms)` [L583-L606] — *Cancel Story Detection and wait for its QThread to finish.*
  - `stop_all_processing(self, timeout_ms)` [L608-L623] — *Stop every local processing job before changing media/projects or exiting.*
  - `confirm_stop_processing_for_media_change(self)` [L625-L653]
  - `worker_thread_finished(self)` [L655-L657]
  - `_get_pipeline_stage_default(self, key, model_installed)` [L659-L674] — *Return remembered Run Processing checkbox state for a stage.*
  - `_save_pipeline_stage_prefs(self, stage_states)` [L676-L683] — *Persist user-chosen Run Processing checkbox defaults without clobbering already-complete stages.*
  - `start_full_auto_pipeline(self)` [L685-L843] — *Open a chooser for the processing stages to run, then run them in order.*
  - `_confirm_pipeline_rerun_if_needed(self, stages, parent)` [L845-L914] — *Look ahead at stages about to run in a pipeline. If any have already*
  - `_run_next_selected_processing(self)` [L916-L996]
  - `start_transcribe_and_diarize(self)` [L998-L1017]
  - `_processing_choice(self, kind)` [L1019-L1058] — *Return: run, continue, start_over, or cancel based on current state.*
  - `_worker_command(self, args)` [L1060-L1079] — *Return (executable, args, env_overrides) for the local AI worker,*
  - `_resolve_worker_command(self, args)` [L1081-L1128] — *Return (executable, args, env_overrides) for the local AI worker.*
  - `_apply_worker_env_overrides(self, process, env_overrides)` [L1131-L1167] — *Applies extra environment variables (e.g. GPU device selection, SSL certs,*
  - `_download_model_and_continue_transcription(self, model_name, label)` [L1169-L1202] — *Asynchronously download a missing model with responsive in-dialog progress and auto-resume.*
  - `_on_transcription_dl_progress(self, pct, msg)` [L1204-L1214]
  - `_on_transcription_dl_cancel(self)` [L1216-L1223]
  - `_on_transcription_dl_finished(self, err)` [L1225-L1258]
  - `_on_transcription_dl_thread_cleanup(self)` [L1260-L1272]

### `project_data_purge_dialog.py` (169 lines)
*Modal dialog allowing users to selectively clear/purge project components.*
- **class `ProjectDataPurgeDialog(QDialog)`** (lines 20–168):
  *Modal dialog allowing users to selectively clear/purge project components.*
  - `__init__(self, parent, is_es)` [L23-L30]
  - `_init_ui(self)` [L32-L149]
  - `_set_all_checked(self, checked)` [L151-L153]
  - `_update_purge_button_state(self)` [L155-L159]
  - `get_purge_options(self)` [L161-L168]

### `project_export.py` (458 lines)
*Radio & TV Story Segmenter — Unified Project & Media Export Facade.*
- **class `ProjectExportMixin(ExportDialogsMixin, ExportMediaClipperMixin, ExportDocumentsMixin, ExportStoryPipelineMixin, ProjectLifecycleMixin)`** (lines 87–458):
  *Unified application export mixin composed of focused export sub-mixins.*
  - `export_project_archive(self, destination_zip)` [L104-L178] — *Export current project state, transcripts, and media into a self-contained portable .zip archive.*
  - `ensure_project_for_processing_pipeline(self)` [L180-L203] — *Ensures a project file is established on disk before running multi-stage*
  - `resolve_project_media(self, project_file, audio_reference, audio_file_abs)` [L205-L263] — *Resolves portable or absolute project media reference with security extension validation.*
  - `closeEvent(self, event)` [L265-L458] — *MainWindow close event handling shutdown, worker cancellation, and QSettings sync.*

### `project_lifecycle.py` (994 lines)
*Radio & TV Story Segmenter — Project Lifecycle & Persistence Management.*
- **Public Exports (`__all__`)**: ProjectLifecycleMixin, ProjectDataPurgeDialog
- **class `ProjectLifecycleMixin`** (lines 49–990):
  *Provides project lifecycle and persistence methods for MainWindow.*
  - `close_project(self, prompt)` [L52-L184]
  - `new_project(self)` [L186-L188]
  - `project_audio_reference(self)` [L190-L198]
  - `project_data(self)` [L200-L240]
  - `_write_project_file(self, file_path)` [L242-L311] — *Writes project state dictionary directly to disk.*
  - `prepare_export_directories(self, target_base_dir, default_name, prompt_user)` [L313-L374] — *Resolves project export subfolders (Transcripts, Media).*
  - `get_default_save_directory(self)` [L376-L389] — *Returns target base directory based on preferences and loaded media.*
  - `validate_project_data(self, data)` [L391-L449] — *Return a list of structural project-data problems before saving.*
  - `save_project_as(self)` [L451-L501]
  - `schedule_project_save(self, delay_ms)` [L503-L523] — *Schedule a coalesced disk save after interactive micro-edits without prompting on unsaved projects.*
  - `_run_debounced_save(self)` [L525-L531]
  - `cancel_pending_project_save(self)` [L533-L538] — *Cancel any queued debounced save timer without writing to disk.*
  - `flush_pending_project_save(self)` [L540-L549] — *Immediately execute any pending debounced project save.*
  - `save_project(self, force)` [L551-L664]
  - `open_backup_restore_dialog(self)` [L666-L673] — *Opens the unified Backup & Restore Center dialog.*
  - `load_project_file(self, filename, prompt, preserve_media, preloaded_data)` [L675-L827]
  - `load_project(self, filename)` [L829-L843]
  - `open_purge_project_data_dialog(self)` [L845-L857] — *Open the modal dialog allowing users to selectively wipe project data.*
  - `purge_project_data(self, purge_transcript, purge_translations, purge_speakers, purge_stories, purge_media)` [L859-L990] — *Selectively wipe project components while preserving user undo history.*

### `project_serialization.py` (126 lines)
*Radio & TV Segmenter — Project file serialization and safe decompression.*
- **Functions**:
  - `sanitize_project_data_for_storage(data, parent_key)` [L21-L51] — *Recursively optimize project data before serialization:*
  - `serialize_rtvs_project(data)` [L54-L58] — *Serialize project dictionary into a transparently gzip-compressed payload.*
  - `_decompress_gzip_bounded(raw_bytes, max_bytes)` [L61-L79] — *Decompress a gzip payload in chunks, stopping with a clear error the*
  - `deserialize_rtvs_project(raw_bytes)` [L82-L98] — *Deserialize project payload, transparently handling both gzip-compressed (.rtvs)*
  - `read_rtvs_project_file(file_path)` [L101-L113] — *Transparently read an .rtvs or .json project file from disk (compressed or uncompressed).*
  - `write_rtvs_project_file(file_path, data)` [L116-L126] — *Safely and atomically write a gzip-compressed .rtvs project file.*

### `project_state_mixin.py` (364 lines)
*Radio & TV Story Segmenter — Project State, Undo/Redo & Processing Progress Mixin.*
- **class `ProjectStateMixin`** (lines 18–364):
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
  - `_restore_project_state_for_undo(self, state)` [L259-L307] — *Restore a complete editable project state without creating another undo entry.*
  - `_commit_project_state_change(self, before_state, description)` [L309-L318] — *Push a complete project-state undo command after a mutation.*
  - `flush_pending_transcript_undo(self)` [L320-L328] — *Commit a pending grouped text edit before another project action or Ctrl+Z.*
  - `mark_project_dirty(self, reason)` [L330-L343] — *Mark the current project as needing a save and refresh the UI state.*
  - `update_window_title(self)` [L345-L355]
  - `is_project_empty(self)` [L357-L364] — *Returns True if the current workspace has no loaded audio, project file, transcript text, or stories.*

### `prs_shared.py` (1495 lines)
- **class `ProjectMetadataDict(dict)`** (lines 30–45):
  *Dictionary subclass supporting both dict key access and attribute access for project metadata.*
  - `__getattr__(self, name)` [L32-L36]
  - `__setattr__(self, name, value)` [L38-L39]
  - `__delattr__(self, name)` [L41-L45]
- **class `ResizableTextEdit(QWidget)`** (lines 490–637):
  *Multi-line text editor defaulted to ~2 lines of height with a drag handle for vertical expansion.*
  - `__init__(self, text, parent)` [L493-L532]
  - `_grip_press(self, event)` [L534-L542]
  - `_grip_move(self, event)` [L544-L562]
  - `_grip_release(self, event)` [L564-L566]
  - `sizeHint(self)` [L568-L569]
  - `minimumSizeHint(self)` [L571-L572]
  - `toPlainText(self)` [L574-L575]
  - `setPlainText(self, text)` [L577-L578]
  - `setText(self, text)` [L580-L581]
  - `text(self)` [L583-L584]
  - `clear(self)` [L586-L587]
  - `setPlaceholderText(self, text)` [L589-L590]
  - `placeholderText(self)` [L592-L593]
  - `setToolTip(self, tip)` [L595-L596]
  - `setAcceptRichText(self, accept)` [L598-L599]
  - `setTabChangesFocus(self, tab)` [L601-L602]
  - `setEnabled(self, enabled)` [L604-L607]
  - `setReadOnly(self, ro)` [L609-L610]
  - `isReadOnly(self)` [L612-L613]
  - `setFocus(self, *args, **kwargs)` [L615-L616]
  - `hasFocus(self)` [L618-L619]
  - `document(self)` [L621-L622]
  - `textCursor(self)` [L624-L625]
  - `setTextCursor(self, cursor)` [L627-L628]
  - `__getattr__(self, name)` [L630-L633]
  - `textChanged(self)` [L636-L637]
- **class `CollapsibleSection(QWidget)`** (lines 640–808):
  *A clean, collapsible and expandable section widget with a styled toggle button,*
  - `__init__(self, title, parent, is_expanded, subtitle)` [L647-L677]
  - `_update_ui(self)` [L679-L777]
  - `refresh_theme(self)` [L779-L781] — *Re-render header and container styling when application theme changes.*
  - `_on_btn_clicked(self)` [L783-L784]
  - `set_expanded(self, expanded)` [L786-L791]
  - `is_expanded(self)` [L793-L794]
  - `set_title(self, title)` [L796-L798]
  - `set_subtitle(self, subtitle)` [L800-L802]
  - `add_widget(self, widget)` [L804-L805]
  - `add_layout(self, layout)` [L807-L808]
- **class `ExportDialog(QDialog)`** (lines 918–1007):
  - `__init__(self, parent, has_media, default_name)` [L919-L927]
  - `init_ui(self)` [L929-L995]
  - `get_settings(self)` [L997-L1007]
- **class `Story`** (lines 1168–1246):
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L1169-L1214]
  - `to_dict(self)` [L1216-L1228]
  - `from_dict(cls, data)` [L1231-L1246]
- **class `ProjectStateCommand(QUndoCommand)`** (lines 1256–1280):
  *Undo/redo a complete editable project state.*
  - `__init__(self, main_window, before_state, after_state, description)` [L1263-L1271]
  - `undo(self)` [L1273-L1274]
  - `redo(self)` [L1276-L1280]
- **Functions**:
  - `_ensure_runtime_bin_on_path()` [L49-L68] — *Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds.*
  - `platform_seq(key_str)` [L833-L842] — *Return a QKeySequence adapted for macOS vs Windows/Linux.*
  - `get_app_icon()` [L844-L890] — *Return the application QIcon loaded from bundled resources or fallback to empty.*
  - `get_license_file_path(filename)` [L892-L910] — *Return the path to a licensing or notice file, checking bundle and source paths.*
  - `create_fade_curve_pixmap(curve_type, width, height, is_selected, accent_color, bg_color)` [L1051-L1143] — *Render a high-DPI visual curve representation showing the volume attenuation shape.*
  - `create_fade_curve_icon(curve_type, width, height)` [L1146-L1161] — *Return a QIcon containing visual render of the specified audio fade curve.*
  - `read_document_text(path)` [L1318-L1384]
  - `__getattr__(name)` [L1471-L1488] — *Lazy resolver for extracted UI and worker components to eliminate circular import chains.*

### `qt_compat.py` (962 lines)
*Radio & TV Segmenter — Headless Qt / PySide6 Compatibility Engine.*
- **Public Exports (`__all__`)**: MockModule, DummyQt, DummyQSettings, DummyQMessageBox, DummyQApplication, DummyQTimer, DummyQHeaderView, DummyQAbstractItemView, DummyQLineEdit, DummyQLabel, DummyQListWidgetItem, DummyQListWidget, DummyQTextEdit, DummyQComboBox, DummyQDoubleSpinBox, DummyQSpinBox, _ensure_pyside6_fallback
- **class `MockClassMeta(type)`** (lines 17–23):
  *Metaclass allowing class-level attributes, static methods, and constructor calls to mock gracefully.*
  - `__getattr__(cls, attr)` [L20-L23]
- **class `DynamicMock`** (lines 26–310):
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
  - `setWindowTitle(self, title)` [L89-L90]
  - `windowTitle(self)` [L92-L93]
  - `accept(self)` [L95-L96]
  - `reject(self)` [L98-L99]
  - `exec_(self)` [L101-L102]
  - `exec(self)` [L104-L105]
  - `__int__(self)` [L107-L108]
  - `__index__(self)` [L110-L111]
  - `__float__(self)` [L113-L114]
  - `__or__(self, other)` [L116-L122]
  - `__ror__(self, other)` [L124-L125]
  - `__and__(self, other)` [L127-L133]
  - `__rand__(self, other)` [L135-L136]
  - `__invert__(self)` [L138-L139]
  - `__xor__(self, other)` [L141-L142]
  - `__contains__(self, item)` [L144-L145]
  - `count(self, *a, **k)` [L147-L148]
  - `__ge__(self, other)` [L150-L154]
  - `__gt__(self, other)` [L156-L160]
  - `__le__(self, other)` [L162-L166]
  - `__lt__(self, other)` [L168-L172]
  - `__iter__(self)` [L174-L175]
  - `__setitem__(self, key, val)` [L177-L180]
  - `__getitem__(self, key)` [L182-L186]
  - `setFlags(self, flags)` [L188-L189]
  - `flags(self)` [L191-L192]
  - `setRowCount(self, count)` [L194-L195]
  - `rowCount(self, *a, **k)` [L197-L198]
  - `setText(self, val)` [L200-L204]
  - `text(self, *a, **k)` [L206-L207]
  - `setData(self, role, val)` [L209-L212]
  - `data(self, role)` [L214-L215]
  - `setItem(self, row, col, item)` [L217-L224]
  - `item(self, row, col)` [L226-L230]
  - `setCurrentCell(self, row, col)` [L232-L234]
  - `currentRow(self)` [L236-L237]
  - `currentColumn(self)` [L239-L240]
  - `setItemDelegateForColumn(self, col, delegate)` [L242-L252]
  - `itemDelegateForColumn(self, col)` [L254-L255]
  - `addTab(self, widget, label)` [L257-L262]
  - `editItem(self, item)` [L264-L283]
  - `findChild(self, cls, *args, **kwargs)` [L285-L292]
  - `installEventFilter(self, filter_obj)` [L294-L297]
  - `removeEventFilter(self, filter_obj)` [L299-L301]
  - `value(self, *args, **kwargs)` [L303-L310]
- **class `MockModule(ModuleType)`** (lines 313–333):
  *Dynamic mock module that automatically manufactures nested mock classes and attributes.*
  - `__init__(self, name)` [L316-L321]
  - `__getattr__(self, name)` [L323-L333]
- **class `_DummyQtMeta(type)`** (lines 336–338):
  - `__getattr__(cls, name)` [L337-L338]
- **class `DummyQt`** (lines 341–374):
  *Mock Qt namespace constants.*
- **class `DummyQEvent(DynamicMock)`** (lines 377–388):
  - `__init__(self, *args, **kwargs)` [L383-L385]
  - `type(self)` [L387-L388]
- **class `DummyQKeyEvent(DynamicMock)`** (lines 391–401):
  - `__init__(self, *args, **kwargs)` [L392-L395]
  - `type(self)` [L397-L398]
  - `key(self)` [L400-L401]
- **class `DummyQSettings`** (lines 404–430):
  *In-memory dictionary-backed QSettings fallback.*
  - `__init__(self, *a, **k)` [L408-L409]
  - `value(self, k, d)` [L411-L412]
  - `setValue(self, k, v)` [L414-L415]
  - `remove(self, k)` [L417-L418]
  - `clear(self)` [L420-L421]
  - `sync(self)` [L423-L424]
  - `beginGroup(self, *a)` [L426-L427]
  - `endGroup(self)` [L429-L430]
- **class `DummyQMessageBox`** (lines 433–451):
  *Non-blocking headless QMessageBox stub.*
  - `information(*args, **kwargs)` [L438-L439]
  - `warning(*args, **kwargs)` [L442-L443]
  - `critical(*args, **kwargs)` [L446-L447]
  - `question(*args, **kwargs)` [L450-L451]
- **class `DummyQApplication`** (lines 454–496):
  *Headless QApplication stub.*
  - `__init__(self, *args, **kwargs)` [L458-L459]
  - `processEvents(cls)` [L462-L469]
  - `sendEvent(cls, receiver, event)` [L472-L480]
  - `instance()` [L483-L484]
  - `topLevelWidgets()` [L487-L488]
  - `thread()` [L491-L492]
  - `clipboard()` [L495-L496]
- **class `DummyQMimeData(DynamicMock)`** (lines 499–515):
  - `__init__(self, *args, **kwargs)` [L500-L503]
  - `setText(self, val)` [L505-L506]
  - `text(self)` [L508-L509]
  - `setHtml(self, val)` [L511-L512]
  - `html(self)` [L514-L515]
- **class `DummyClipboard(DynamicMock)`** (lines 518–532):
  - `setText(self, val)` [L521-L522]
  - `text(self)` [L524-L525]
  - `setMimeData(self, mime)` [L527-L532]
- **class `DummyQTimer(DynamicMock)`** (lines 535–548):
  - `__init__(self, *args, **kwargs)` [L536-L538]
  - `start(self, *a, **k)` [L540-L541]
  - `stop(self)` [L543-L544]
  - `singleShot(ms, callback)` [L547-L548]
- **class `DummyQHeaderView`** (lines 551–552):
- **class `DummyQAbstractItemView`** (lines 555–559):
- **class `DummyQStyledItemDelegate(DynamicMock)`** (lines 562–568):
  - `__init__(self, *args, **kwargs)` [L565-L568]
- **class `DummyQLineEdit(DynamicMock)`** (lines 571–585):
  - `__init__(self, *args, **kwargs)` [L574-L576]
  - `setText(self, val)` [L578-L579]
  - `text(self, *a, **k)` [L581-L582]
  - `selectAll(self)` [L584-L585]
- **class `DummyQLabel(DynamicMock)`** (lines 588–604):
  - `__init__(self, *args, **kwargs)` [L589-L592]
  - `setText(self, val)` [L594-L595]
  - `text(self, *a, **k)` [L597-L598]
  - `setToolTip(self, val)` [L600-L601]
  - `toolTip(self, *a, **k)` [L603-L604]
- **class `DummyQListWidgetItem(DynamicMock)`** (lines 607–630):
  - `__init__(self, *args, **kwargs)` [L608-L612]
  - `setText(self, val)` [L614-L615]
  - `text(self, *a, **k)` [L617-L618]
  - `setToolTip(self, val)` [L620-L621]
  - `toolTip(self, *a, **k)` [L623-L624]
  - `setData(self, role, val)` [L626-L627]
  - `data(self, role)` [L629-L630]
- **class `DummyQListWidget(DynamicMock)`** (lines 633–652):
  - `__init__(self, *args, **kwargs)` [L634-L636]
  - `addItem(self, item)` [L638-L641]
  - `count(self)` [L643-L644]
  - `item(self, idx)` [L646-L649]
  - `clear(self)` [L651-L652]
- **class `DummyQTextEdit(DynamicMock)`** (lines 655–673):
  - `__init__(self, *args, **kwargs)` [L656-L658]
  - `setPlainText(self, val)` [L660-L661]
  - `toPlainText(self)` [L663-L664]
  - `setText(self, val)` [L666-L667]
  - `toHtml(self)` [L669-L670]
  - `setHtml(self, val)` [L672-L673]
- **class `DummyQFont`** (lines 676–680):
  - `__init__(self, *args, **kwargs)` [L679-L680]
- **class `DummySignal`** (lines 683–702):
  - `__init__(self, *args, **kwargs)` [L684-L685]
  - `connect(self, callback)` [L687-L689]
  - `disconnect(self, callback)` [L691-L695]
  - `emit(self, *args, **kwargs)` [L697-L702]
- **class `DummyQComboBox(DynamicMock)`** (lines 705–770):
  - `__init__(self, *args, **kwargs)` [L706-L710]
  - `addItem(self, text, userData)` [L712-L713]
  - `addItems(self, texts)` [L715-L717]
  - `count(self)` [L719-L720]
  - `itemData(self, index, role)` [L722-L725]
  - `itemText(self, index)` [L727-L730]
  - `currentIndex(self)` [L732-L733]
  - `setCurrentIndex(self, index)` [L735-L736]
  - `findData(self, data, role)` [L738-L742]
  - `findText(self, text)` [L744-L749]
  - `currentText(self)` [L751-L753]
  - `currentData(self, role)` [L755-L757]
  - `clear(self)` [L759-L761]
  - `setEnabled(self, val)` [L763-L764]
  - `isEnabled(self)` [L766-L767]
  - `setStyleSheet(self, val)` [L769-L770]
- **class `DummyQDoubleSpinBox`** (lines 773–815):
  - `__init__(self, *args, **kwargs)` [L774-L778]
  - `value(self)` [L780-L781]
  - `setValue(self, v)` [L783-L785]
  - `setRange(self, mn, mx)` [L787-L788]
  - `setSingleStep(self, s)` [L790-L791]
  - `setDecimals(self, prec)` [L793-L794]
  - `decimals(self)` [L796-L797]
  - `setSuffix(self, s)` [L799-L800]
  - `setToolTip(self, tip)` [L802-L803]
  - `toolTip(self)` [L805-L806]
  - `setEnabled(self, val)` [L808-L809]
  - `isEnabled(self)` [L811-L812]
  - `setStyleSheet(self, val)` [L814-L815]
- **class `DummyQSpinBox`** (lines 818–853):
  - `__init__(self, *args, **kwargs)` [L819-L822]
  - `value(self)` [L824-L825]
  - `setValue(self, v)` [L827-L829]
  - `setRange(self, mn, mx)` [L831-L832]
  - `setSingleStep(self, s)` [L834-L835]
  - `setSuffix(self, s)` [L837-L838]
  - `setToolTip(self, tip)` [L840-L841]
  - `toolTip(self)` [L843-L844]
  - `setEnabled(self, val)` [L846-L847]
  - `isEnabled(self)` [L849-L850]
  - `setStyleSheet(self, val)` [L852-L853]
- **class `DummyQFormLayout(DynamicMock)`** (lines 856–876):
  - `__init__(self, *args, **kwargs)` [L857-L859]
  - `addRow(self, label_or_widget, field)` [L861-L870]
  - `labelForField(self, field)` [L872-L876]
- **Functions**:
  - `_ensure_pyside6_fallback(force)` [L879-L941] — *Ensures PySide6 modules are importable, installing the zero-dependency mock shim if unavailable.*

### `radio_tv_story_segmenter_worker.py` (226 lines)
*Radio & TV Story Segmenter — AI Background Subprocess Worker Facade.*
- **Public Exports (`__all__`)**: emit, emit_hello, _patch_av_open, _clamp_diarization_thread_env, _setup_windows_dll_directories, _safe_tensor_from_numpy, get_optimal_transcription_threads, get_app_data_dir_pure, get_models_storage_dir_pure, is_onnx_model_available, transcribe_parakeet_onnx, probe_audio_language, transcribe, normalize_audio_for_diarization, configure_optimal_pytorch_threads, _normalize_expected_speakers, _normalize_speaker_labels, _sensitivity_distance_threshold, fast_cluster_ahc, apply_clustering_patches, run_vad_two_pass, assign_short_segments_to_centroids, _calculate_embedding_for_interval, _diarize_solo_fast_path, _get_wespeaker_model, extract_embeddings_batched, run_transcript_guided_diarization, diarize, is_real_speech, detect_story_boundaries, main
- **Functions**:
  - `main(argv)` [L117-L222]

### `reaper_bridge.py` (953 lines)
*reaper_bridge.py — REAPER DAW Companion Bridge & Inter-Process Cue Emitter.*
- **Functions**:
  - `get_reaper_ipc_paths()` [L27-L47] — *Return the list of standard sidecar IPC file destinations.*
  - `reaper_color_from_hex(hex_str)` [L50-L61] — *Convert #RRGGBB hex color to Cockos REAPER custom color integer (0x1000000 | 0x1RRGGBB).*
  - `_fmt_clock(secs)` [L64-L68] — *Format seconds into MM:SS.S clock timecode.*
  - `_hex_to_rgb(hex_str)` [L71-L79] — *Convert hex color (#RRGGBB) to (R, G, B) tuple.*
  - `_is_sentence_terminator(text, next_word)` [L82-L85] — *Check whether a text fragment ends with terminal sentence punctuation (., ?, !, ...).*
  - `_build_phrase_preview(text, fallback_spk)` [L88-L99] — *Build a concise, readable 6-word phrase preview for REAPER take markers.*
  - `_extract_formatted_transcript_sentences(main_win)` [L103-L293] — *Build formatted grammatical sentences (with word timings and paragraph flags) matching RTVS transcript view.*
  - `get_reaper_clip_notes_and_markers(main_win, start_sec, end_sec, marker_style, apply_speaker_color, include_notes, include_markers, precomputed_sentences)` [L296-L397] — *Extract formatted transcript notes, take markers, and colors for a clip in an exported REAPER project.*
  - `build_reaper_cue_payload(main_win, start_sec, end_sec, plain_text, title, clip_type, story_obj, include_word_cues, rendered_wav_path, marker_style)` [L400-L548] — *Construct a standardized cross-language cue dictionary conforming to the 1.0 schema.*
  - `get_reaper_index_paths()` [L551-L565] — *Return IPC file paths for the full transcript and stories index used by the ReaImGui Dock.*
  - `write_reaper_transcript_index(main_win, precomputed_sentences)` [L568-L625] — *Emit the formatted project stories and sentence-level transcript index for REAPER companion scripts.*
  - `write_reaper_sidecar_cue(payload)` [L628-L647] — *Atomically write the cue payload JSON to all IPC sidecar locations.*
  - `attach_reaper_cue_to_mimedata(mime_data, payload)` [L650-L661] — *Encode cue payload as UTF-8 JSON into QMimeData and write atomic IPC sidecar.*
  - `get_default_reaper_scripts_dir()` [L664-L678] — *Return the standard platform-specific default REAPER Scripts/RTVS3 directory.*
  - `get_bundled_lua_scripts()` [L681-L707] — *Find the bundled RTVS3 ReaScript Lua files across source and frozen bundles.*
  - `install_reaper_scripts_to_resource_path(parent_widget, target_dir)` [L710-L785] — *Copy the RTVS3 ReaScript companion and dock scripts to the REAPER Scripts directory.*
  - `render_temp_daw_wav_clip(main_win, start_sec, end_sec, title)` [L788-L829] — *Render a temporary uncompressed WAV slice of the selected range for universal DAW clipboard paste.*
  - `copy_selection_as_daw_wav_clip(main_win, start_sec, end_sec, plain_text, html_text, title, story_obj)` [L832-L889] — *Render a temp WAV audio slice and attach it to the OS file clipboard (CF_HDROP / URLs)*
  - `populate_unified_copy_mimedata(main_win, mime_data, start_sec, end_sec, plain_text, title, clip_type, story_obj)` [L892-L952] — *Populates QMimeData with REAPER JSON cue payloads and optional WAV file attachments*

### `remote_media_cache.py` (610 lines)
*Headless Managed Remote Media Cache for YouTube and WordPress episode downloads.*
- **Public Exports (`__all__`)**: DEFAULT_CACHE_CAP_GB, CACHE_CAP_SETTING_KEY, CACHE_INDEX_FILENAME, format_bytes_human, get_remote_media_cache_dir, is_path_inside_cache, make_cache_key, build_remote_media_source_record, RemoteMediaCacheManager
- **class `RemoteMediaCacheManager`** (lines 151–597):
  *Manages cached YouTube and WordPress remote downloads with LRU size limits.*
  - `__init__(self, cache_dir)` [L154-L158]
  - `get_provider_dir(self, provider)` [L160-L167] — *Return a safe subdirectory inside the cache root for a specific provider.*
  - `load_index(self)` [L169-L211] — *Load and reconcile index.json against actual files on disk.*
  - `save_index(self)` [L213-L229] — *Atomically persist index.json using temp-file + fsync + os.replace.*
  - `_normalize_protected_set(self, protected_paths)` [L231-L240]
  - `get_entry(self, cache_key)` [L242-L245]
  - `find_entry_by_path(self, file_path)` [L247-L258]
  - `get_existing_cached_file(self, cache_key, touch)` [L260-L272] — *Return the existing cached Path for ``cache_key`` (instant cache-hit reuse).*
  - `register_download(self, cache_key, file_path, provider, source_url, source_id, quality_preset, title, upload_date, project_path)` [L274-L321] — *Register (or update) a downloaded remote file inside the managed cache.*
  - `mark_accessed(self, file_path_or_key)` [L323-L336] — *Refresh ``last_accessed_at`` for an entry matched by key or path.*
  - `mark_exported(self, file_path_or_key, export_target)` [L338-L357] — *Mark a cached media entry as exported so LRU eviction prefers it first.*
  - `link_project(self, file_path_or_key, project_path)` [L359-L378] — *Associate a saved `.rtvs` project path with a cached media entry.*
  - `list_entries(self)` [L380-L385] — *Return all cached entries sorted newest-accessed first.*
  - `get_total_size_bytes(self)` [L387-L389]
  - `get_stats(self, cap_gb)` [L391-L410]
  - `check_disk_space(self, estimated_bytes, cap_gb)` [L412-L445] — *Check free disk space and cache cap before starting a large download.*
  - `delete_entry(self, cache_key, protected_paths)` [L447-L478] — *Safely delete a single cached file by key, respecting path-jail and active-file guards.*
  - `enforce_size_cap(self, cap_gb, protected_paths)` [L480-L554] — *Evict cached files when total size exceeds ``cap_gb`` (0 or negative = Unlimited).*
  - `clear_cache(self, exported_only, protected_paths)` [L556-L597] — *Manually clear exported-only or all non-open cached remote media files.*
- **Functions**:
  - `_utc_now_iso()` [L27-L28]
  - `_parse_iso_ts(val)` [L31-L40]
  - `format_bytes_human(num_bytes)` [L43-L52] — *Format a byte count as a readable size string (e.g. '1.42 GB', '312.5 MB').*
  - `_resolve_app_data_root()` [L55-L65] — *Resolve the writable application data directory without importing Qt.*
  - `get_remote_media_cache_dir(base_dir)` [L68-L82] — *Return (and create if needed) the managed remote media cache root directory.*
  - `is_path_inside_cache(file_path, cache_dir)` [L85-L97] — *Strictly verify that ``file_path`` resides inside the managed cache directory.*
  - `make_cache_key(provider, source_id, quality_preset)` [L100-L107] — *Build a deterministic cache key for a remote source item.*
  - `build_remote_media_source_record(provider, source_url, source_id, quality_preset, cached_filename, cache_key, title, upload_date, estimated_size_bytes, extra)` [L110-L148] — *Create a portable `.rtvs` `remote_media_source` metadata dictionary.*

### `remote_media_cache_dialog.py` (447 lines)
*Qt Dialog for inspecting and managing the Managed Remote Media Cache (YouTube & WordPress).*
- **Public Exports (`__all__`)**: CACHE_CAP_OPTIONS, get_configured_cache_cap_gb, ManageCachedMediaDialog, find_redownload_provider, reattach_downloaded_media_to_project, prompt_redownload_missing_remote_media
- **class `ManageCachedMediaDialog(QDialog)`** (lines 52–338):
  *Inspect, cap, and manually prune cached YouTube and WordPress remote downloads.*
  - `__init__(self, parent, main_window, cache_manager)` [L55-L72]
  - `_active_protected_paths(self)` [L74-L82]
  - `_build_ui(self)` [L84-L172]
  - `_collect_plugin_maintenance_actions(self)` [L174-L190]
  - `refresh_table(self)` [L192-L242]
  - `_on_cap_changed(self)` [L244-L257]
  - `_on_delete_selected(self)` [L259-L300]
  - `_on_clear_exported(self)` [L302-L319]
  - `_on_clear_all(self)` [L321-L338]
- **Functions**:
  - `get_configured_cache_cap_gb(settings_store)` [L41-L49] — *Read the user's configured Remote Media Cache limit in GB (0.0 = Unlimited).*
  - `find_redownload_provider(main_window, source_meta)` [L341-L357] — *Locate an enabled plugin capable of re-downloading ``source_meta`` (decoupled from plugins/).*
  - `reattach_downloaded_media_to_project(main_window, media_path)` [L360-L391] — *Bind a newly re-downloaded remote media file onto an already-loaded .rtvs project.*
  - `prompt_redownload_missing_remote_media(main_window, source_meta, parent)` [L394-L437] — *Offer 1-click re-download when an opened .rtvs project's cached remote media is missing.*

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

### `scripts/capture_guide_screenshots.py` (152 lines)
*Programmatic headless screenshot generator for RTVS3 user guides.*
- **class `MockCaptureMainWindow`** (lines 24–69):
  *Mock main window providing realistic project data for guide screenshots.*
  - `__init__(self)` [L26-L63]
  - `_get_transcript_text_slice(self, start, end)` [L65-L66]
  - `get_effective_story_author_and_category_ids(self, story_idx)` [L68-L69]
- **Functions**:
  - `capture_widget(widget, output_path, size)` [L72-L87] — *Render a QWidget to a high-resolution PNG image file capped at max 850px width.*
  - `main()` [L90-L148]

### `scripts/dev_check.py` (338 lines)
*scripts/dev_check.py - Ultra-Fast Pre-Flight Development & AI Safety Gate*
- **Functions**:
  - `check_syntax()` [L34-L45] — *Compiles all tracked python files in root and scripts.*
  - `check_typing_stubs()` [L48-L54] — *Verifies interface stubs for modules exceeding 800 lines.*
  - `check_preview_sync()` [L57-L63] — *Ensures zero-dependency preview files match prs_shared.py.*
  - `check_modular_budget()` [L66-L100] — *Guards against new monolithic files exceeding the 1,000 line ceiling.*
  - `_ctor_has_explicit_parent(call_node, cname)` [L113-L130] — *Return True if a Qt widget constructor call passes an explicit parent argument.*
  - `_is_literal_false_visibility(call_node, attr)` [L133-L138]
  - `_iter_direct_nodes(stmts)` [L141-L153] — *Yield AST nodes inside *stmts* without descending into nested def/class definitions.*
  - `check_qt_orphan_widget_flashes(root_dir)` [L156-L281] — *Static AST guard: flag setVisible(non-False) / setRowVisible(..., non-False) on unparented*
  - `check_regression_tests()` [L284-L292] — *Executes change-aware Tier 2 diagnostic test suite.*
  - `main()` [L295-L334]

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

### `scripts/modular_audit.py` (770 lines)
*scripts/modular_audit.py — AST Decomposition Suggester & Modular Budget Guard.*
- **class `ModuleStructure`** (lines 75–248):
  *Detailed structural metrics extracted from a Python module.*
  - `__init__(self, file_path)` [L78-L95]
  - `_analyze(self)` [L97-L171]
  - `_extract_class_info(self, node, lines)` [L173-L201]
  - `_extract_func_info(self, node, lines)` [L203-L212]
  - `_classify_domain(name, bases, method_names)` [L215-L248] — *Classifies a class or function into a logical domain based on naming and signatures.*
- **class `DecompositionPlan`** (lines 255–417):
  *Proposed modular decomposition plan for a monolithic source file.*
  - `__init__(self, structure)` [L258-L266]
  - `_classify_method_domain(m_name)` [L269-L279]
  - `_build_plan(self)` [L281-L384]
  - `render_markdown_blueprint(self)` [L386-L417]
- **Functions**:
  - `scan_repository(root_dir)` [L424-L436] — *Scans all Python modules in the repository, excluding build/venv directories.*
  - `print_audit_report(structures, warn_threshold, hard_ceiling, sort_by)` [L439-L480] — *Prints a formatted terminal table showing modularity compliance.*
  - `check_budget_guard(structures, hard_ceiling, warn_threshold, exempt_paths)` [L483-L516] — *Programmatic budget check suitable for test runner and CI pipelines.*
  - `check_single_responsibility(structure, strict)` [L519-L607] — *Analyzes AST domain classification to verify Single Responsibility & Domain Separation.*
  - `print_srp_report(results, strict)` [L610-L654] — *Prints a structured terminal report for Single Responsibility & Domain Separation.*
  - `main()` [L657-L766]

### `sentence_boundaries.py` (140 lines)
*Context-aware sentence-boundary and abbreviation detection for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: ALWAYS_PRE_NOUN_TITLES, CAPITALIZED_PRE_NOUN_TITLES, MID_CLAUSE_CONNECTORS, MONTH_ABBREVS, NUMBER_PREFIX_ABBREVS, AMBIGUOUS_ABBREVS, is_ambiguous_abbreviation, is_non_terminal_abbreviation, is_sentence_end
- **Functions**:
  - `_extract_last_word(text)` [L57-L64]
  - `is_ambiguous_abbreviation(text)` [L67-L75] — *Return True when text ends with a multi-dot acronym or sentence-finalizable abbreviation.*
  - `is_non_terminal_abbreviation(text, next_word, language)` [L78-L109] — *Return True when a trailing period belongs to a non-terminal abbreviation rather than sentence end.*
  - `is_sentence_end(text, next_word, language)` [L112-L127] — *Return True if text terminates a sentence, honoring non-terminal abbreviations and titles.*

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

### `shortcuts/manager.py` (215 lines)
*shortcuts/manager.py — Core ShortcutsManager coordinator and QSettings integration.*
- **class `ShortcutsManager(QObject)`** (lines 19–215):
  *Central repository and coordinator for all configurable application shortcuts.*
  - `__init__(self, settings_store)` [L24-L30]
  - `load(self)` [L32-L51] — *Read customized shortcut overrides from QSettings.*
  - `get_definitions(self)` [L53-L54]
  - `get_definition(self, action_id)` [L56-L61]
  - `get_default_shortcut(self, action_id)` [L63-L68]
  - `get_current_shortcut(self, action_id)` [L70-L76]
  - `is_customized(self, action_id)` [L78-L84]
  - `set_shortcut(self, action_id, new_seq)` [L86-L101] — *Set a shortcut override for action_id. Passing empty string or None sets to None.*
  - `reset_shortcut(self, action_id)` [L103-L109] — *Reset a single shortcut back to its platform default.*
  - `reset_all(self)` [L111-L113] — *Reset all shortcuts back to application defaults.*
  - `save(self)` [L115-L126] — *Persist all overrides to QSettings and emit notification signal.*
  - `find_conflict(self, candidate_seq, excluding_action_id)` [L128-L144] — *Check if candidate_seq is already bound to another action.*
  - `apply_to_window(self, window)` [L146-L215] — *Update shortcuts on all QAction and QShortcut objects on MainWindow,*

### `shortcuts/schema.py` (951 lines)
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

### `speaker_dialog_refinement_mixin.py` (555 lines)
*Radio & TV Story Segmenter — Speaker Dialog Refinement & Turn Merging Mixin.*
- **class `SpeakerDialogRefinementMixin`** (lines 45–555):
  *Mixin for competitive speaker run refinement, word synchronization, and turn merging.*
  - `refine_speaker_run_between_confirmed_anchors(self, start_idx, end_idx, spk_a, spk_b)` [L48-L131]
  - `prompt_refine_speaker_run(self, start_idx, end_idx)` [L133-L305]
  - `sync_segment_words(self, segment, new_text, word_formats)` [L307-L399]
  - `merge_speakers(self, source_speaker, target_speaker)` [L401-L471]
  - `open_speaker_manager_dialog(self, modal)` [L473-L499]
  - `merge_contiguous_speaker_segments(self)` [L501-L555]

### `speaker_dialogs.py` (897 lines)
*speaker_dialogs.py — Dialogs for speaker renaming, turn assignment, and cluster management.*
- **Public Exports (`__all__`)**: ChangeSpeakerDialog, SpeakerManagerDialog, SpeakerNameDelegate
- **class `ChangeSpeakerDialog(QDialog)`** (lines 25–111):
  *Dialog prompting whether to apply a speaker name change to all instances or a single turn.*
  - `__init__(self, current_name, target_name, seg_idx, parent, show_save_voice_profile, already_saved_voice_profile)` [L28-L95]
  - `_on_all(self)` [L97-L99]
  - `_on_subsequent(self)` [L101-L103]
  - `_on_single(self)` [L105-L107]
  - `save_to_station_voices(self)` [L110-L111]
- **class `SpeakerNameDelegate(QStyledItemDelegate)`** (lines 135–202):
  *Delegate for inline double-click editing of speaker names with Tab progression.*
  - `__init__(self, dialog)` [L138-L140]
  - `createEditor(self, parent, option, index)` [L142-L167]
  - `eventFilter(self, editor, event)` [L169-L202]
- **class `SpeakerManagerDialog(QDialog)`** (lines 205–897):
  *Manager dialog for inspecting, aliasing, and merging detected speaker clusters.*
  - `__init__(self, parent)` [L208-L261]
  - `_is_gui_thread(self)` [L263-L271] — *Check whether execution is on the main Qt GUI thread.*
  - `_get_audio_source_url(self)` [L273-L288]
  - `_get_sample_duration(self)` [L290-L298] — *Retrieve the configured speaker sample preview duration in seconds (default 3.0s).*
  - `_find_speaker_sample_range(self, speaker_name)` [L300-L328] — *Resolve a clean representative utterance (start_s, duration_s) for the speaker cluster.*
  - `_play_speaker_sample(self, speaker_name)` [L330-L373] — *Play a non-blocking 3-second sample for the specified speaker without altering timeline state.*
  - `_stop_sample_playback(self)` [L375-L389] — *Cease any active sample audio playback and reset UI button text.*
  - `_on_preview_playback_state_changed(self, state)` [L391-L394]
  - `_on_preview_media_status_changed(self, status)` [L396-L402]
  - `_init_ui(self)` [L404-L500]
  - `_schedule_debounced_save(self)` [L502-L505] — *Schedule a debounced full-project save 500ms after the last speaker rename.*
  - `_flush_debounced_save(self)` [L507-L512] — *Immediately execute any pending debounced project save.*
  - `_populate(self)` [L514-L666]
  - `_start_inline_edit_on_row(self, row)` [L668-L676]
  - `_on_table_item_changed(self, item)` [L678-L700]
  - `_rename_speaker(self, current_name, raw_id)` [L702-L710]
  - `_apply_speaker_rename(self, current_name, target, raw_id)` [L712-L760]
  - `_merge_speaker_into(self, source_name)` [L762-L789]
  - `_on_quick_merge(self)` [L791-L816]
  - `_on_toggle_station_voice(self, speaker_name, checked, checkbox)` [L818-L843]
  - `_on_fix_speaker_names(self)` [L845-L852]
  - `_on_open_voice_profiles(self)` [L854-L858]
  - `reject(self)` [L860-L863]
  - `accept(self)` [L865-L868]
  - `closeEvent(self, event)` [L870-L873]
  - `toggle_float_mode(self, pinned)` [L875-L891] — *Toggle whether the non-modal floating window stays pinned on top of other windows.*
  - `changeEvent(self, event)` [L893-L897]
- **Functions**:
  - `_is_gui_thread()` [L114-L122] — *Check whether execution is on the main Qt GUI thread.*
  - `_should_init_audio_preview()` [L125-L132]

### `speaker_editing_mixin.py` (637 lines)
*Radio & TV Story Segmenter — Speaker Label, Renaming & Segment Editing Mixin.*
- **class `SpeakerEditingMixin(SpeakerDialogRefinementMixin)`** (lines 54–637):
  *Mixin for speaker labeling, splitting, renaming, and dialog turn refinement.*
  - `handle_insert_speaker_request(self, seg_idx, split_time, speaker_name)` [L57-L61]
  - `add_speaker_label_at(self, seg_idx, split_time, name)` [L63-L177]
  - `split_segment_at_time(self, seg_idx, split_time, new_speaker_name)` [L179-L284]
  - `prompt_rename_custom_speaker(self, old_name)` [L286-L307]
  - `display_speaker(self, speaker)` [L309-L325]
  - `get_all_known_speakers(self)` [L327-L357]
  - `execute_speaker_rename(self, seg_idx, raw_speaker, target_name)` [L359-L516]
  - `prompt_rename_speaker(self, seg_idx, speaker)` [L518-L519]
  - `remove_speaker_label_at_segment(self, seg_idx)` [L521-L604]
  - `register_confirmed_speaker_turn(self, seg_idx, speaker_name)` [L606-L634]
  - `register_confirmed_speaker_sample(self, seg_idx, speaker_name)` [L636-L637]

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

### `speaker_name_cleanup_dialog.py` (295 lines)
*speaker_name_cleanup_dialog.py — Modal review dialog for bulk speaker/guest name cleanup.*
- **Public Exports (`__all__`)**: SpeakerNameCleanupDialog
- **class `SpeakerNameCleanupDialog(QDialog)`** (lines 53–295):
  *Review and apply misspelled guest/host name fixes against confirmed speakers.*
  - `__init__(self, main_win, parent)` [L56-L137]
  - `_set_all_checked(self, checked)` [L139-L141]
  - `rescan(self)` [L143-L214]
  - `_apply_selected(self)` [L216-L295]

### `speaker_name_matcher.py` (583 lines)
*speaker_name_matcher.py — Headless phonetic and fuzzy cleanup for guest and speaker names.*
- **Public Exports (`__all__`)**: SpeakerNameCandidate, apply_bulk_text_replacements, consonant_skeleton, extract_confirmed_speaker_names, find_misspelled_speaker_names, is_generic_role_label, is_generic_speaker_label, name_similarity, phonetic_norm, phonetic_soundex, preserve_case_replace
- **class `SpeakerNameCandidate`** (lines 108–115):
- **Functions**:
  - `is_generic_speaker_label(name)` [L118-L126] — *Return True if a speaker label is empty, numeric, or an auto-generated placeholder.*
  - `is_generic_role_label(name)` [L129-L133] — *Return True for placeholder speaker IDs or generic role words like 'Host' or 'Guest'.*
  - `preserve_case_replace(matched, replacement)` [L136-L155] — *Preserve uppercase/title-case style when replacing matched text with a proper noun.*
  - `_ascii_letters_lower(text)` [L158-L161]
  - `phonetic_norm(token)` [L164-L187] — *Normalize English/broadcast ASR consonant & vowel spellings to a canonical phonetic key.*
  - `_voice_neutral(pnorm)` [L190-L192] — *Map voiced consonants to their unvoiced counterparts for final-stop resilience (e.g. Fahad/fahat).*
  - `consonant_skeleton(token)` [L195-L202] — *Keep initial letter plus non-vowel skeleton after phonetic normalization.*
  - `phonetic_soundex(token)` [L205-L223] — *Compute Soundex over phonetic_norm(token) so C/K/Q and PH/F share buckets.*
  - `name_similarity(candidate, target)` [L226-L259] — *Return [0.0, 1.0] similarity blending spelling, phonetic folding, consonant skeleton, and Soundex.*
  - `extract_confirmed_speaker_names(main_win)` [L262-L293] — *Collect confirmed non-generic speaker display names from a project window or state object.*
  - `_split_name_parts(name)` [L296-L297]
  - `_make_context_snippet(text, start, end, radius)` [L300-L308]
  - `_span_overlaps(span, covered)` [L311-L313]
  - `_needs_case_or_spelling_fix(found_phrase, target_name)` [L316-L322]
  - `_phrase_similarity(found_words, target_parts)` [L325-L339]
  - `find_misspelled_speaker_names(segments, confirmed_names, min_score)` [L342-L502] — *Scan transcript segments for likely ASR misspellings of confirmed speaker names.*
  - `apply_bulk_text_replacements(segments, replacements, preserve_case, sync_words_cb, transcript, translations)` [L505-L583] — *Apply whole-word replacements across transcript segments, full text, and translations.*

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

### `speaker_profiles.py` (249 lines)
*speaker_profiles.py — Persistent Station Voice Profile Manager & Storage Engine.*
- **Public Exports (`__all__`)**: StationVoiceProfile, StationVoiceProfileStore, ManageVoiceProfilesDialog
- **class `StationVoiceProfile`** (lines 34–63):
  - `to_dict(self)` [L44-L45]
  - `from_dict(cls, data)` [L48-L63]
- **class `StationVoiceProfileStore`** (lines 66–241):
  *Persistent storage manager for recurring station voice acoustic profiles.*
  - `__init__(self, storage_dir)` [L69-L76]
  - `get_profiles_file_path(self)` [L78-L79]
  - `load(self)` [L81-L99]
  - `save(self)` [L101-L117]
  - `list_profiles(self)` [L119-L120]
  - `get_profile(self, profile_id)` [L122-L123]
  - `find_profile_by_name(self, name)` [L125-L130]
  - `add_or_update_profile(self, name, vector, sample_count, notes, source_media, profile_id)` [L132-L191]
  - `remove_profile(self, profile_id)` [L193-L198]
  - `clear(self)` [L200-L202]
  - `match_vector(self, vector, threshold, min_margin)` [L204-L241] — *Compare an unknown candidate vector against all saved voice profiles.*
- **Functions**:
  - `__getattr__(name)` [L245-L249]

### `speaker_profiles_dialog.py` (425 lines)
*speaker_profiles_dialog.py — UI management dialog for persistent Station Voice Profiles.*
- **Public Exports (`__all__`)**: ManageVoiceProfilesDialog
- **class `ManageVoiceProfilesDialog(QDialog)`** (lines 62–425):
  *Management dialog for inspecting, auditing, adding, or deleting persistent station voice profiles.*
  - `__init__(self, parent, store, main_win)` [L65-L76]
  - `_init_ui(self)` [L78-L135]
  - `_populate_table(self)` [L137-L212]
  - `_on_rename(self, profile_id, old_name)` [L214-L227]
  - `_on_delete(self, profile_id, name)` [L229-L239]
  - `_on_match_project(self, prof)` [L241-L298]
  - `_on_add_from_active_turn(self)` [L300-L365]
  - `_on_export(self)` [L367-L395]
  - `_on_import(self)` [L397-L425]

### `spellcheck_helper.py` (779 lines)
*spellcheck_helper.py — Headless Tier 1 Offline Spellcheck Engine.*
- **Public Exports (`__all__`)**: SpellIssue, OfflineSpellChecker, is_pyspellchecker_available, collect_allowlist_words, iter_checkable_words, match_case, ignore_word_for_session, get_session_ignored_words, clear_session_ignored_words
- **class `SpellIssue`** (lines 35–40):
  *Represents a single misspelled word span in a text string.*
- **class `OfflineSpellChecker`** (lines 581–766):
  *Lightweight offline spellchecker seeded with Glossary + Speaker allowlists.*
  - `__init__(self, custom_words, main_window, use_pyspellchecker)` [L584-L602]
  - `backend_name(self)` [L605-L607] — *Return active backend name: `'pyspellchecker'` or `'fallback'`.*
  - `refresh_from_window(self, main_window)` [L609-L616] — *Reload Glossary terms and confirmed speaker names from `main_window`.*
  - `add_words(self, words)` [L618-L623] — *Add one or more words/phrases to this instance's explicit allowlist.*
  - `is_word_known(self, word)` [L625-L660] — *Return True if `word` is valid English or present in allowlist / session ignores.*
  - `find_misspelled_spans(self, text)` [L662-L680] — *Return all misspelled word spans in `text` in left-to-right order.*
  - `find_issue_at(self, text, char_index)` [L682-L689] — *Return the `SpellIssue` covering `char_index` (inclusive of boundaries), if any.*
  - `get_suggestions(self, word, max_suggestions)` [L691-L766] — *Return up to `max_suggestions` spelling suggestions preserving input case.*
- **Functions**:
  - `is_pyspellchecker_available()` [L315-L317] — *Return True if the `pyspellchecker` library is importable.*
  - `_get_base_pyspellchecker()` [L320-L331] — *Return a cached read-only `pyspellchecker.SpellChecker` instance if available.*
  - `_normalize_apostrophe(word)` [L334-L335]
  - `_extract_word_tokens(text)` [L338-L354] — *Extract lowercase alphabetic tokens (plus full hyphenated form) from a phrase.*
  - `match_case(source_word, suggestion)` [L357-L365] — *Apply the capitalization pattern of `source_word` onto `suggestion`.*
  - `ignore_word_for_session(word)` [L368-L374] — *Add `word` to the process-wide session ignore list.*
  - `get_session_ignored_words()` [L377-L380] — *Return a copy of the session-ignored lowercase words.*
  - `clear_session_ignored_words()` [L383-L386] — *Clear the process-wide session ignore list (primarily for tests).*
  - `collect_allowlist_words(main_window, glossary, speaker_names, extra_words)` [L389-L483] — *Build a lowercase word allowlist from custom Glossary preferred terms*
  - `_edits1(word)` [L486-L494] — *All strings one Levenshtein edit away from `word`.*
  - `_fallback_stem_matches(word, vocab)` [L497-L528] — *Check regular English inflections against the fallback vocabulary.*
  - `_is_camel_or_mixed_brand(token)` [L531-L537] — *Skip internal-capital identifiers like WordPress, YouTube, iPhone, PySide.*
  - `iter_checkable_words(text)` [L540-L578] — *Yield `(word, start, end)` spans in `text` that should be spellchecked.*

### `spellcheck_widgets.py` (697 lines)
*spellcheck_widgets.py — Inline Qt Spellcheck Highlighting & Context Menu UI.*
- **Public Exports (`__all__`)**: SpellCheckHighlighter, SpellCheckController, attach_spellcheck, refresh_all_spellcheckers, add_word_to_glossary
- **class `SpellCheckHighlighter(QSyntaxHighlighter)`** (lines 175–192):
  *QSyntaxHighlighter drawing red spellcheck underlines in QTextEdit / QPlainTextEdit.*
  - `__init__(self, document, spellchecker)` [L178-L181]
  - `refresh_format(self)` [L183-L184]
  - `highlightBlock(self, text)` [L186-L192]
- **class `_LineEditSpellOverlay(QWidget)`** (lines 225–305):
  *Mouse-transparent overlay painting wavy red underlines onto a QLineEdit.*
  - `__init__(self, line_edit, controller)` [L228-L236]
  - `paintEvent(self, event)` [L238-L305]
- **class `SpellCheckController(QObject)`** (lines 308–631):
  *Coordinates inline spellcheck highlighting and context menus on a text widget.*
  - `__init__(self, widget, main_window, spellchecker)` [L311-L328]
  - `is_alive(self)` [L330-L332] — *Return True when both this controller and its attached widget remain valid.*
  - `dispose(self)` [L334-L350] — *Unregister this controller and break cyclic references after widget teardown.*
  - `_detect_line_edit(widget)` [L353-L356]
  - `_install(self)` [L358-L396]
  - `eventFilter(self, obj, event)` [L398-L412]
  - `_on_line_edit_changed(self, *_args)` [L414-L420]
  - `_on_line_edit_cursor_changed(self, *_args)` [L422-L427]
  - `_recompute_line_edit_issues(self)` [L429-L436]
  - `_get_widget_text(self)` [L438-L453]
  - `get_issues(self)` [L455-L460] — *Return current misspelled `SpellIssue` spans for the attached widget.*
  - `refresh(self, main_window, added_word)` [L462-L484] — *Refresh allowlist from Glossary/speakers and re-run inline highlighting.*
  - `apply_suggestion(self, issue, replacement, block_offset)` [L486-L543] — *Replace the misspelled `issue` span with `replacement` in the attached widget.*
  - `_locate_issue_at_point(self, pos)` [L545-L568] — *Return `(SpellIssue, block_start_offset)` for a widget-local click position.*
  - `_on_context_menu_requested(self, pos)` [L570-L626]
  - `ignore_word(self, word)` [L628-L631] — *Ignore `word` for the remainder of the session and refresh all editors.*
- **Functions**:
  - `_is_qt_object_alive(obj)` [L62-L71] — *Return False when `obj` is None or its underlying C++ Qt object was deleted.*
  - `_make_destroyed_cleanup_callback(ctrl_ref)` [L74-L80]
  - `_is_real_qt_widget(widget)` [L83-L88] — *Return True when running under real PySide6 rather than qt_compat mocks.*
  - `_spell_underline_color()` [L91-L103] — *Select an accessible red underline color for the active application theme.*
  - `_make_misspelled_char_format()` [L106-L115]
  - `add_word_to_glossary(word, main_window)` [L118-L172] — *Persist `word` to the application's custom Glossary and refresh spellcheckers.*
  - `_compute_line_edit_scroll_offset(line_edit, text, font_metrics, contents_rect, inner_left)` [L195-L222] — *Compute horizontal pixel scroll offset for a single-line QLineEdit.*
  - `attach_spellcheck(widget, main_window, spellchecker)` [L634-L674] — *Attach Tier 1 offline spellchecking to a QLineEdit, QTextEdit, QPlainTextEdit,*
  - `refresh_all_spellcheckers(main_window, added_word)` [L677-L688] — *Re-sync Glossary/speaker allowlists and re-highlight every attached editor.*

### `story_crud_mixin.py` (931 lines)
*Radio & TV Story Segmenter — Story CRUD & Timeline Selection Mixin.*
- **class `StoryCrudMixin`** (lines 46–931):
  *Mixin providing story list UI management, CRUD operations, and fade handling.*
  - `update_stories_header(self)` [L49-L89] — *Update Stories section header label and tooltip with selection count and duration.*
  - `update_story_form_duration(self)` [L91-L105] — *Update Duration field in the story edit form below Range.*
  - `refresh_story_list(self)` [L107-L164]
  - `handle_new_story_started(self, start_time, end_time)` [L166-L176]
  - `handle_new_story_updated(self, start_time, end_time)` [L178-L194]
  - `handle_drag_story_region(self, index, start_time, end_time)` [L196-L212]
  - `audition_story(self, index)` [L214-L237]
  - `handle_drag_finished(self)` [L239-L271]
  - `update_selected_story(self)` [L273-L331]
  - `delete_selected_story(self)` [L333-L364]
  - `get_current_interaction_time(self, for_boundary)` [L366-L384]
  - `set_selected_story_start(self)` [L386-L434]
  - `set_selected_story_end(self)` [L436-L484]
  - `add_selection_to_story(self)` [L486-L597]
  - `play_transcript_selection(self)` [L599-L618]
  - `select_all_stories(self)` [L620-L627]
  - `handle_timeline_selection_range_changed(self, start_time, end_time)` [L629-L691]
  - `add_story_from_range(self, start_time, end_time)` [L693-L727]
  - `add_story_from_active_selection(self)` [L729-L746]
  - `open_story_fades_dialog(self, story_index)` [L748-L793]
  - `apply_fades_to_selected_stories(self, fade_in, fade_out, fade_curve)` [L795-L831]
  - `remove_fades_from_selected_stories(self)` [L833-L834]
  - `set_fade_curve_for_selected_stories(self, curve_type)` [L836-L862]
  - `open_story_metadata_dialog(self, target_story_index, modal)` [L864-L897]
  - `_notify_floating_dialogs(self)` [L899-L913] — *Refresh any open non-modal export, metadata, or speaker management floating windows after main window edits.*
  - `_close_floating_dialogs(self, persist_drafts)` [L915-L931] — *Persist drafts and close any active non-modal floating windows on project close or shutdown.*

### `story_detect_dialog.py` (333 lines)
*Lightweight two-step confirmation and threshold-override dialogs for standalone Story/Segment Detection.*
- **Public Exports (`__all__`)**: DetectStoriesSettingsDialog, StandaloneDetectStoriesDialog
- **class `DetectStoriesSettingsDialog(QDialog)`** (lines 22–168):
  *Dedicated dialog for adjusting silence/length detection thresholds for a run or as new defaults.*
  - `__init__(self, parent, *, silence_threshold, min_story_duration, detection_mode, lead_in_padding, save_as_defaults, default_silence, default_min_story, default_mode, default_padding, is_es)` [L25-L150]
  - `reset_to_defaults(self)` [L152-L159] — *Restore all fields to the saved Preferences defaults.*
  - `get_values(self)` [L161-L168]
- **class `StandaloneDetectStoriesDialog(QDialog)`** (lines 171–330):
  *Simple confirmation dialog for standalone detection with an Adjust Settings... button.*
  - `__init__(self, parent, *, existing_count, silence_threshold, min_story_duration, detection_mode, lead_in_padding, is_es, term, term_plural)` [L174-L262]
  - `_is_modified(self)` [L264-L270]
  - `_refresh_summary_label(self)` [L272-L292]
  - `create_settings_dialog(self)` [L294-L308] — *Build the secondary Detection Settings dialog pre-filled with the active staged values.*
  - `apply_settings_values(self, values)` [L310-L319] — *Apply confirmed threshold values from DetectStoriesSettingsDialog and refresh summary.*
  - `open_settings_dialog(self)` [L321-L327] — *Open the dedicated Detection Settings dialog and return to this confirmation dialog on Apply.*
  - `get_values(self)` [L329-L330]

### `story_detection_processing.py` (290 lines)
*Story boundary detection processing mixin for Radio & TV Story Segmenter.*
- **class `StoryDetectionProcessingMixin`** (lines 22–289):
  - `start_auto_detect_stories(self, overrides)` [L23-L145]
  - `_persist_story_detect_defaults(self, detection_mode, silence_threshold, lead_in_padding, min_story_duration)` [L147-L165]
  - `auto_detect_progress(self, message, percent)` [L167-L168]
  - `auto_detect_finished(self, new_stories)` [L170-L243]
  - `auto_detect_error(self, message)` [L245-L289]

### `story_fades_dialog.py` (215 lines)
*story_fades_dialog.py — Dialog for fine-grained audio fade-in, fade-out, and curve adjustment.*
- **Public Exports (`__all__`)**: StoryFadesDialog
- **class `StoryFadesDialog(QDialog)`** (lines 18–213):
  *Dialog for fine-grained numerical adjustment of audio fade-in and fade-out durations.*
  - `__init__(self, parent, story, story_index)` [L21-L38]
  - `_init_ui(self)` [L40-L129]
  - `_on_enable_fades_toggled(self, checked)` [L131-L140]
  - `_sync_fades_preference(self)` [L142-L152]
  - `apply_current(self)` [L154-L177]
  - `accept(self)` [L179-L181]
  - `reject(self)` [L183-L205]
  - `_restore_defaults(self)` [L207-L210]
  - `get_fades(self)` [L212-L213]

### `story_metadata_dialog.py` (313 lines)
*Radio & TV Story Segmenter — Universal Story & Post Metadata Architecture.*
- **class `StoryMetadataDialog(QDialog)`** (lines 66–313):
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
  - `refresh_from_main_window(self, target_story_index)` [L275-L301] — *Synchronize stories, excerpts, and transcript changes from the main window.*
  - `changeEvent(self, event)` [L303-L306]
  - `done(self, r)` [L308-L313]
- **Functions**:
  - `_get_metadata_theme_mode()` [L47-L49] — *Retrieve active theme mode ('light', 'dark', or 'high_contrast').*
  - `generate_story_excerpt(text, max_words)` [L52-L63] — *Generate a clean, readable excerpt of up to max_words from transcript text.*

### `story_model.py` (273 lines)
*Radio & TV Story Segmenter — Story Model, Boundaries & Undo Commands.*
- **class `Story`** (lines 67–162):
  *Represents a segmented radio or TV news/broadcast story with boundaries and fade metadata.*
  - `__init__(self, start, end, title, suggestion, metadata, fade_in, fade_out, fade_curve)` [L70-L123]
  - `duration(self)` [L126-L127]
  - `to_dict(self)` [L129-L141]
  - `from_dict(cls, data)` [L144-L159]
  - `__repr__(self)` [L161-L162]
- **class `SetStoriesCommand(QUndoCommand)`** (lines 190–215):
  *Undo/redo command for wholesale updates to the project's story list.*
  - `__init__(self, main_window, old_stories, new_stories, description)` [L193-L197]
  - `undo(self)` [L199-L206]
  - `redo(self)` [L208-L215]
- **class `StoryBoundaryChangeCommand(QUndoCommand)`** (lines 218–255):
  *Discrete undo/redo command for story boundary adjustments (start/end times).*
  - `__init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description)` [L221-L228]
  - `undo(self)` [L230-L234]
  - `redo(self)` [L236-L240]
  - `_sync_ui(self, start, end)` [L242-L255]
- **class `SelectStoriesCommand(QUndoCommand)`** (lines 258–273):
  *Undo/redo command for active story selection index changes.*
  - `__init__(self, main_window, old_selection, new_selection, description)` [L261-L265]
  - `undo(self)` [L267-L269]
  - `redo(self)` [L271-L273]
- **Functions**:
  - `get_fade_curve_factors(progress, curve)` [L54-L64] — *Calculate gain factor (0.0 to 1.0) given normalized fade progress (0.0 to 1.0).*
  - `validate_story_boundaries(start, end, media_duration)` [L165-L174] — *Clamp and ensure start < end within [0.0, media_duration].*
  - `check_story_overlap(stories)` [L177-L187] — *Return pairs of story indices that temporally overlap.*

### `story_widgets.py` (592 lines)
*Radio & TV Story Segmenter — Story Sidebar Widgets, Item Delegates, and Undo Commands.*
- **class `FadeCurveVisualSelector(QWidget)`** (lines 61–178):
  *Visual selector widget providing interactive card buttons for audio fade curves.*
  - `__init__(self, parent, button_width, button_height, columns)` [L66-L134]
  - `_on_button_toggled(self, checked)` [L136-L145]
  - `currentData(self)` [L147-L148]
  - `setCurrentData(self, curve_type)` [L150-L161]
  - `findData(self, curve_type)` [L163-L168]
  - `currentIndex(self)` [L170-L174]
  - `setCurrentIndex(self, idx)` [L176-L178]
- **class `StoryFadesChangeCommand(QUndoCommand)`** (lines 195–229):
  *Discrete undo/redo command for story audio fade-in, fade-out, and curve adjustments.*
  - `__init__(self, main_window, story_index, old_in, old_out, new_in, new_out, old_curve, new_curve, description)` [L198-L207]
  - `undo(self)` [L209-L214]
  - `redo(self)` [L216-L221]
  - `_sync_ui(self)` [L223-L229]
- **class `SetStoriesCommand(QUndoCommand)`** (lines 232–256):
  - `__init__(self, main_window, old_stories, new_stories, description)` [L233-L238]
  - `undo(self)` [L240-L247]
  - `redo(self)` [L249-L256]
- **class `StoryBoundaryChangeCommand(QUndoCommand)`** (lines 259–294):
  *Discrete undo/redo command for story boundary adjustments (start/end times).*
  - `__init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description)` [L262-L269]
  - `undo(self)` [L271-L275]
  - `redo(self)` [L277-L281]
  - `_sync_ui(self, start, end)` [L283-L294]
- **class `SelectStoriesCommand(QUndoCommand)`** (lines 297–308):
  - `__init__(self, main_window, old_selection, new_selection, description)` [L298-L302]
  - `undo(self)` [L304-L305]
  - `redo(self)` [L307-L308]
- **class `StoryCardDelegate(QStyledItemDelegate)`** (lines 315–442):
  *Renders story items as clean cards with color-coded accent bars, pill badges, and time metadata.*
  - `__init__(self, parent)` [L317-L318]
  - `sizeHint(self, option, index)` [L320-L322]
  - `paint(self, painter, option, index)` [L324-L442]
- **class `StoryListWidget(QListWidget)`** (lines 449–592):
  *QListWidget subclass for story segmentation list with right-click context menu and drag-drop support.*
  - `__init__(self, parent)` [L456-L460]
  - `dragEnterEvent(self, event)` [L462-L466]
  - `dragMoveEvent(self, event)` [L468-L472]
  - `dropEvent(self, event)` [L474-L481]
  - `keyPressEvent(self, event)` [L483-L515]
  - `_show_context_menu(self, pos)` [L517-L581]
  - `adjust_height_to_contents(self, min_h, max_h)` [L583-L592] — *Dynamically size the list widget to only fit the number of stories.*
- **Functions**:
  - `_get_fade_curve_profiles()` [L47-L49]
  - `_get_fade_curve_icon(cid, width, height)` [L52-L54]
  - `_trigger_project_save(main_window)` [L185-L192] — *Queue a debounced save when supported, falling back to immediate save.*

### `sync.py` (161 lines)
*2-Way Synchronization Engine for Radio & TV Story Segmenter.*
- **Functions**:
  - `get_current_version()` [L25-L34] — *Read PROJECT_VERSION from core_utils.py.*
  - `run_cmd(cmd, check)` [L37-L39] — *Run a subprocess command and stream output.*
  - `cmd_status()` [L42-L71] — *Display current git branch status and unpushed/unpulled commits.*
  - `cmd_pull()` [L74-L99] — *Pull latest changes from GitHub, then sync preview and symbol index.*
  - `cmd_push(commit_msg)` [L102-L137] — *Stage all changes, commit, and push to GitHub.*
  - `main()` [L140-L157]

### `terminology.py` (882 lines)
*Model-independent terminology and glossary support.*
- **Functions**:
  - `split_source_variants(source_raw, preferred, match_case)` [L35-L65] — *Split a source field (comma/semicolon separated or list) into unique variants.*
  - `format_source_variants(variants, match_case)` [L68-L74] — *Format a sequence of source variants into a clean comma-separated string.*
  - `parse_glossary(raw)` [L77-L138] — *Return normalized glossary entries while accepting legacy list strings.*
  - `expand_glossary_rules(glossary)` [L141-L181] — *Expand multi-variant glossary entries into atomic replacement rules (longest source first).*
  - `sort_glossary_entries(entries, mode)` [L184-L227] — *Return glossary entries sorted for UI presentation without mutating replacement order.*
  - `add_alternate_spelling(raw_glossary, preferred_term, alternate_spelling, do_not_translate, match_case)` [L230-L278] — *Add one or more alternate spellings for a preferred glossary term.*
  - `load_glossary(settings_store)` [L281-L289] — *Load the shared glossary from the application's QSettings object.*
  - `_replace_term(text, source, preferred, match_case)` [L292-L306]
  - `normalize_text(text, glossary)` [L309-L322] — *Canonicalize glossary terms without changing surrounding punctuation.*
  - `_phonetic_name_skeleton(token)` [L325-L349] — *Compute a normalized phonetic skeleton for English/Latin proper-noun comparison.*
  - `_name_token_similarity(a, b)` [L352-L374] — *Return orthographic + phonetic similarity [0.0, 1.0] between two name tokens.*
  - `_split_word_affixes(raw_word)` [L377-L387] — *Split a timed word token into (leading_punct_and_space, core_word, trailing_punct).*
  - `_has_sentence_break(trail)` [L390-L392] — *Return True if trailing punctuation marks a clause/sentence boundary.*
  - `_discover_project_contextual_rules(segments, base_entries, expanded_rules)` [L395-L585] — *Two-pass project-scoped proper-noun discovery and single-word co-reference resolution.*
  - `_normalize_timed_words(words, rules)` [L588-L658] — *Apply both multi-word and single-word glossary rules across timed word dicts.*
  - `normalize_transcript(transcript, glossary)` [L661-L713] — *Normalize transcript text and word labels for every ASR backend.*
  - `translation_rules(glossary)` [L716-L719] — *Return only entries explicitly marked as protected for translation.*
  - `replace_term(text, source, preferred, match_case)` [L722-L729] — *Public replacement helper for translation workers.*
  - `split_protected_text(text, glossary)` [L732-L782] — *Split text into translatable and protected pieces.*
  - `export_glossary_to_json(glossary)` [L785-L788] — *Serialize glossary entries to formatted JSON string.*
  - `export_glossary_to_csv(glossary)` [L791-L807] — *Serialize glossary entries to standard CSV string.*
  - `import_glossary_from_text(raw_text)` [L810-L882] — *Parse glossary entries from JSON, CSV, TSV, or plain text lines.*

### `theme_preferences.py` (606 lines)
*Radio & TV Story Segmenter — Theme Preferences & Styling Engine.*
- **class `ThemePreferencesMixin`** (lines 19–606):
  *Provides application theme switching and styling methods.*
  - `set_theme(self, mode)` [L22-L606]

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

### `thumbnail_workers.py` (523 lines)
*Video thumbnail cache helpers, network-share detection, and background thumbnail workers.*
- **Public Exports (`__all__`)**: TIMELINE_THUMBNAIL_DENSITY_SPECS, TIMELINE_THUMBNAIL_DENSITY_PRESETS, DEFAULT_TIMELINE_THUMBNAIL_DENSITY, MAX_TIMELINE_THUMBNAIL_COUNT, _LEGACY_DEFAULT_THUMBNAIL_COUNT, is_network_path, normalize_thumbnail_density, get_thumbnail_count_for_density, should_use_keyframe_skip, parse_ffmpeg_progress_seconds, get_video_thumbnail_cache_dir, read_video_thumbnail_cache, invalidate_video_thumbnail_cache, VideoThumbnailCacheLoader, VideoThumbnailWorker
- **class `VideoThumbnailCacheLoader(QObject)`** (lines 293–336):
  *Decode cached JPEG thumbnails into thread-safe QImages on a background QThread.*
  - `__init__(self, items, media_path, target_count, density)` [L299-L305]
  - `cancel(self)` [L307-L308]
  - `run(self)` [L310-L336]
- **class `VideoThumbnailWorker(QObject)`** (lines 339–504):
  *Background FFmpeg video thumbnail extractor with keyframe acceleration and live progress.*
  - `__init__(self, media_path, duration, output_dir, count, density, use_keyframe_skip)` [L346-L367]
  - `build_ffmpeg_command(self, keyframe_skip)` [L369-L388] — *Construct the FFmpeg command vector for thumbnail extraction.*
  - `cancel(self)` [L390-L398]
  - `_run_ffmpeg_pass(self, keyframe_skip)` [L400-L454]
  - `run(self)` [L456-L504]
- **Functions**:
  - `is_network_path(path)` [L47-L73] — *Return True if *path* points to a UNC network share or Windows mapped network drive.*
  - `normalize_thumbnail_density(density)` [L76-L79] — *Normalize a timeline thumbnail density setting to 'standard', 'detailed', 'high', or 'extra_high'.*
  - `get_thumbnail_count_for_density(density, duration)` [L82-L87] — *Return the duration-scaled, memory-bounded thumbnail count for a density preset.*
  - `should_use_keyframe_skip(duration, count, density)` [L90-L108] — *Return True when FFmpeg `-skip_frame nokey` can safely accelerate thumbnail extraction.*
  - `parse_ffmpeg_progress_seconds(line)` [L111-L135] — *Parse elapsed media seconds from an FFmpeg `-progress pipe:1` key=value line.*
  - `get_video_thumbnail_cache_dir(media_file, project_file, target_count)` [L138-L197] — *Return the deterministic thumbnail cache directory for a media file.*
  - `read_video_thumbnail_cache(media_file, duration, project_file, target_count)` [L200-L258] — *Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.*
  - `invalidate_video_thumbnail_cache(media_file, project_file, target_count)` [L261-L290] — *Delete the thumbnail cache directory for a given media file.*

### `timeline_context_menus.py` (197 lines)
*Context menu builders and event handlers for the timeline canvas.*
- **Functions**:
  - `show_timeline_context_menu(canvas, global_pos, pos_x, exec_menu)` [L12-L161] — *Display the primary right-click context menu on the timeline canvas.*
  - `show_selection_context_menu(canvas, global_pos, exec_menu)` [L164-L197] — *Display the range selection context menu on the timeline canvas.*

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

### `timeline_painter.py` (436 lines)
*Timeline canvas rendering engine, waveform drawing, and paint pipeline.*
- **Functions**:
  - `render_waveform_buffer(canvas, width, height)` [L32-L212] — *Render background waveform peaks and video thumbnail strip onto an offscreen QPixmap.*
  - `paint_timeline_canvas(canvas, painter, event)` [L215-L436] — *Execute full timeline paint pipeline onto the canvas QPainter.*

### `timeline_snap.py` (195 lines)
*Timeline snapping algorithms, edge detection, and collision hit-testing.*
- **Functions**:
  - `snap_time(canvas, raw_time, exclude_story_idx, width, pixel_threshold)` [L9-L60] — *Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels.*
  - `find_edge_at_pos(canvas, pos_x, width)` [L63-L73] — *Determine if pos_x is hovering over a story segment start or end boundary edge.*
  - `find_fade_handle_at_pos(canvas, pos_x, pos_y, width)` [L76-L103] — *Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks.*
  - `find_story_at_time(canvas, time)` [L106-L115] — *Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping.*
  - `is_near_playhead(canvas, pos_x, width)` [L118-L121] — *Check if pos_x is within grab distance of the active playhead cursor.*
  - `get_timeline_hover_info(canvas, pos_x, pos_y, width)` [L124-L174] — *Calculate tooltip and status bar readout for canvas hover interactions.*
  - `format_selection_drag_info(start, end)` [L177-L185] — *Format tooltip and status bar readout for live selection dragging.*
  - `format_edge_drag_info(story, edge_type, current_time)` [L188-L195] — *Format tooltip and status bar readout for live edge dragging.*

### `timeline_widgets.py` (995 lines)
*Radio & TV Story Segmenter — Timeline Ruler, Track Views, Playhead, Overview & Canvas Widgets.*
- **class `TimelineCanvas(QWidget)`** (lines 71–907):
  - `__init__(self, parent, tokens)` [L91-L181]
  - `set_is_video(self, is_video)` [L183-L186]
  - `set_background_generation_active(self, task_name, active)` [L188-L209] — *Set generation state for 'waveform' or 'thumbnails'.*
  - `_activate_background_banner(self)` [L211-L216]
  - `set_thumbnail_progress(self, pct)` [L218-L223] — *Update live percentage progress (1-99) for background video thumbnail extraction.*
  - `_update_background_status_text(self)` [L225-L244]
  - `dragEnterEvent(self, event)` [L246-L246]
  - `dragMoveEvent(self, event)` [L247-L247]
  - `dragLeaveEvent(self, event)` [L248-L248]
  - `dropEvent(self, event)` [L249-L249]
  - `set_audio_filename(self, filename)` [L251-L254]
  - `set_duration(self, duration)` [L256-L264]
  - `set_position(self, position)` [L266-L269]
  - `set_playing_state(self, is_playing)` [L271-L272]
  - `ensure_position_visible(self, target_time)` [L274-L297]
  - `clear_selection_range(self)` [L299-L304] — *Clear active timeline drag selection range without affecting committed stories.*
  - `set_transcript_selection_range(self, start, end)` [L306-L308]
  - `set_stories(self, stories, selected_indices)` [L310-L314]
  - `set_waveform_peaks(self, peaks, levels)` [L316-L327]
  - `set_progressive_waveform_peaks(self, peaks, pps, pct)` [L329-L336]
  - `set_timeline_views(self, show_waveform, show_thumbnails)` [L338-L342]
  - `set_video_thumbnails(self, thumbnails)` [L344-L358]
  - `set_skip_seconds(self, seconds)` [L360-L361]
  - `visible_duration(self)` [L363-L364]
  - `clamp_scroll_offset(self)` [L366-L369]
  - `time_to_x(self, time_val, width)` [L371-L374]
  - `x_to_time(self, x_val, width)` [L376-L378]
  - `snap_time(self, raw_time, exclude_story_idx, width, pixel_threshold)` [L380-L381]
  - `find_edge_at_pos(self, pos_x, width)` [L385-L386]
  - `find_fade_handle_at_pos(self, pos_x, pos_y, width)` [L388-L389]
  - `find_story_at_time(self, time)` [L391-L392]
  - `is_near_playhead(self, pos_x, width)` [L394-L395]
  - `set_zoom(self, new_zoom, center_x, focus_time)` [L397-L423]
  - `resizeEvent(self, event)` [L425-L427]
  - `wheelEvent(self, event)` [L429-L479]
  - `mousePressEvent(self, event)` [L481-L561]
  - `mouseMoveEvent(self, event)` [L563-L700]
  - `mouseReleaseEvent(self, event)` [L702-L774]
  - `_check_right_drag(self, pos_x)` [L776-L781]
  - `_show_timeline_context_menu(self, global_pos, pos_x)` [L783-L784]
  - `_show_selection_context_menu(self, global_pos)` [L786-L787]
  - `keyPressEvent(self, event)` [L789-L888]
  - `set_thumbnail_position(self, position)` [L890-L894]
  - `render_waveform_buffer(self, width, height)` [L896-L897]
  - `paintEvent(self, event)` [L899-L907]
- **class `TimelineWidget(QWidget)`** (lines 910–994):
  - `__init__(self, parent, tokens)` [L913-L947]
  - `set_is_video(self, is_video)` [L949-L951]
  - `set_background_generation_active(self, task_name, active)` [L953-L955]
  - `dragEnterEvent(self, event)` [L957-L957]
  - `dragMoveEvent(self, event)` [L958-L958]
  - `dragLeaveEvent(self, event)` [L959-L959]
  - `dropEvent(self, event)` [L960-L960]
  - `update_scrollbar_range(self)` [L962-L971]
  - `update_scrollbar_from_canvas(self, offset)` [L973-L980]
  - `update_canvas_from_scrollbar(self, val)` [L982-L991]
  - `__getattr__(self, name)` [L993-L994]
- **Functions**:
  - `_handle_media_drag_event(event, drop_signal)` [L59-L68]

### `transcript_cleaner.py` (216 lines)
*Radio & TV Segmenter — Transcript cleaning, loop collapsing, and hallucination scrubbing.*
- **Functions**:
  - `collapse_repeating_ngrams(text, max_n, min_repeats)` [L36-L87] — *Detect and collapse degenerate repeating word/token loops in transcription text.*
  - `strip_hallucination_phrases(text)` [L90-L106] — *Filter out standard Whisper hallucination phrases and repetitive acoustic tags.*
  - `trim_trailing_degenerate_tail(segments, min_tail_repeats)` [L109-L121] — *Inspect the trailing segments of a transcript and truncate degenerate infinite loops at the end.*
  - `scrub_transcript_segments(segments, collapse_loops)` [L124-L202] — *Comprehensive scrubber for transcript segment lists:*
  - `scrub_transcript(transcript)` [L205-L216] — *Clean and sanitize a complete transcript payload dictionary.*

### `transcript_context_menu_mixin.py` (746 lines)
*Radio & TV Story Segmenter — Interactive Transcript Context Menu & Bubble Actions Mixin.*
- **class `TranscriptContextMenuMixin`** (lines 48–745):
  *Mixin for context menu construction and selection bubble quick-actions.*
  - `_on_bubble_play(self)` [L51-L56]
  - `_on_bubble_story(self)` [L58-L63]
  - `_on_bubble_note(self)` [L65-L78]
  - `_on_bubble_cut(self)` [L80-L85]
  - `_on_bubble_export(self)` [L87-L92]
  - `show_context_menu(self, position)` [L94-L497]
  - `copy_highlighted_selection(self)` [L499-L628] — *Copy the active story or timeline selection span to clipboard when no cursor text is selected.*
  - `copy_selection_for_reaper(self)` [L630-L695] — *Explicitly build and copy REAPER DAW clip cue payload for the active text or story selection.*
  - `copy_selection_as_daw_wav(self)` [L697-L745] — *Render temporary WAV audio clip and copy it to the OS clipboard (CF_HDROP) for any DAW.*

### `transcript_editor.py` (953 lines)
*transcript_editor.py - Interactive Transcript Editor & Viewer Components*
- **Public Exports (`__all__`)**: FindReplaceDialog, TranscriptSelectionBubble, transcript_text_view_stylesheet, clean_dark_mode_clipboard_html, InteractiveTranscriptEdit
- **class `InteractiveTranscriptEdit(TranscriptContextMenuMixin, TranscriptFormattingMixin, TranscriptTimelineSyncMixin, QTextEdit)`** (lines 117–953):
  - `__init__(self, parent)` [L130-L192]
  - `clear(self)` [L194-L209] — *Clear document text and reset all word maps, anchors, and extra selections.*
  - `lock_scroll_position(self, v_val, h_val, duration_ms)` [L211-L232] — *Pin vertical and horizontal scrollbars to exact pixel values during layout reflows.*
  - `_release_scroll_lock(self)` [L234-L237]
  - `_on_v_range_changed(self, min_val, max_val)` [L239-L243]
  - `focusInEvent(self, event)` [L245-L261]
  - `_enforce_scroll_after_focus(self, target_v, target_h)` [L263-L269]
  - `createMimeDataFromSelection(self)` [L271-L306] — *Clean dark-mode white/light plain text colors to black (#000000) and attach REAPER cues when copying.*
  - `wheelEvent(self, event)` [L307-L313]
  - `event(self, e)` [L315-L364]
  - `paintEvent(self, event)` [L366-L429]
  - `dragEnterEvent(self, event)` [L431-L435]
  - `dragMoveEvent(self, event)` [L437-L441]
  - `dropEvent(self, event)` [L443-L453]
  - `apply_theme_style(self, mode)` [L455-L458]
  - `set_font_scale(self, scale)` [L460-L470] — *Set transcript font scale without affecting the rest of the UI.*
  - `set_editing_mode(self, enabled)` [L472-L488]
  - `mousePressEvent(self, event)` [L490-L530]
  - `mouseMoveEvent(self, event)` [L532-L580]
  - `leaveEvent(self, event)` [L582-L586]
  - `mouseReleaseEvent(self, event)` [L588-L674]
  - `keyPressEvent(self, event)` [L676-L953]

### `transcript_editor_dialogs.py` (808 lines)
*transcript_editor_dialogs.py - Dialog and floating toolbar components for transcript editing.*
- **class `FindReplaceDialog(QDialog)`** (lines 53–724):
  *Modeless find-and-replace dialog for QTextEdit / InteractiveTranscriptEdit.*
  - `__init__(self, text_edit, parent)` [L56-L191]
  - `keyPressEvent(self, event)` [L193-L219]
  - `_on_find_text_changed(self, text)` [L221-L225]
  - `_update_replace_field_helpers(self, *_args)` [L227-L237]
  - `_on_trim_replace_text(self)` [L239-L240]
  - `_on_add_to_glossary(self)` [L242-L271]
  - `_on_open_fix_speaker_names(self)` [L273-L280]
  - `_format_replacement(self, matched_text, replacement)` [L282-L285]
  - `_trigger_project_save(self, main_win)` [L287-L291]
  - `_update_local_match_count(self)` [L293-L303]
  - `_sync_parent_search(self, target)` [L305-L309]
  - `main_window(self)` [L312-L320]
  - `get_flags(self)` [L322-L328]
  - `find_next(self)` [L330-L370]
  - `find_prev(self)` [L372-L417]
  - `replace(self)` [L419-L564]
  - `replace_all(self)` [L566-L694]
  - `_fallback_widget_replace(self, replacement)` [L696-L700]
  - `_fallback_widget_replace_all(self, target, replacement)` [L702-L724]
- **class `TranscriptSelectionBubble(QFrame)`** (lines 727–808):
  *Floating quick-action toolbar on transcript selection (Milestone 3.12).*
  - `__init__(self, parent)` [L736-L803]
  - `_emit_comment(self)` [L805-L808]

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

### `transcript_navigation_mixin.py` (300 lines)
*transcript_navigation_mixin.py - Timestamp discovery, caret positioning, anchor indexing, and playback highlighting.*
- **class `TranscriptNavigationMixin`** (lines 34–300):
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
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L235-L300]

### `transcript_playback_highlight_mixin.py` (277 lines)
*Radio & TV Story Segmenter — Interactive Transcript Playback Highlighting Mixin.*
- **class `TranscriptPlaybackHighlightMixin`** (lines 24–277):
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
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L219-L277]

### `transcript_selection_mixin.py` (473 lines)
*transcript_selection_mixin.py - Multi-selection, timeline spans, comment ranges, and bubble actions.*
- **class `TranscriptSelectionMixin`** (lines 31–473):
  *Mixin managing selection state, multi-select accumulation, comment highlights,*
  - `set_selection_mode(self, mode)` [L35-L39]
  - `set_char_timestamp_map(self, mapping)` [L41-L42]
  - `has_active_selection(self)` [L44-L50]
  - `clear_all_selections(self)` [L52-L65]
  - `get_time_range_for_char_span(self, start_pos, end_pos)` [L67-L83]
  - `get_selected_time_range(self)` [L85-L98]
  - `get_all_selected_story_ranges(self)` [L100-L121] — *Returns a list of dicts: [{'start_time': float, 'end_time': float, 'text': str, ...}, ...]*
  - `select_comment_range(self, seg_idx)` [L123-L168] — *Navigate and select the exact comment text range in the transcript view.*
  - `update_extra_selections(self)` [L170-L302]
  - `set_search_highlights(self, ranges, active_idx)` [L304-L340] — *Highlight all search matches across transcript with prominent active match.*
  - `clear_search_highlights(self)` [L342-L345] — *Clear all search match highlights from transcript.*
  - `set_timeline_selection_span(self, start_char, end_char)` [L347-L352]
  - `_on_selection_completed(self, cursor)` [L354-L430]
  - `_on_bubble_play(self)` [L432-L437]
  - `_on_bubble_story(self)` [L439-L444]
  - `_on_bubble_note(self)` [L446-L459]
  - `_on_bubble_cut(self)` [L461-L466]
  - `_on_bubble_export(self)` [L468-L473]

### `transcript_story.py` (856 lines)
*Radio & TV Segmenter v3.10.30-beta — transcript story responsibilities.*
- **Public Exports (`__all__`)**: TranscriptStoryMixin, Story, SetStoriesCommand, SelectStoriesCommand, StoryBoundaryChangeCommand, StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin, ChangeSpeakerDialog, VoiceProfileMatchDialog, StoryFadesDialog, SpeakerManagerDialog, FADE_CURVE_TABLES, get_fade_curve_factors
- **class `TranscriptStoryMixin(StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin)`** (lines 63–855):
  - `render_transcript(self)` [L64-L471]
  - `on_transcript_selection_changed(self)` [L473-L505]
  - `on_transcript_text_changed(self)` [L507-L664]
  - `transcript_clicked(self, url)` [L666-L682]
  - `edit_segment_comment_dialog(self, seg_idx, sel_text, start_char, end_char, t_range, covered_indices)` [L684-L765]
  - `add_comment_from_selection(self)` [L769-L812]
  - `delete_segment_comment(self, seg_idx)` [L814-L834]
  - `toggle_comments_panel(self)` [L836-L839]
  - `toggle_show_comments(self, checked)` [L841-L847]
  - `toggle_comment_highlights(self, checked)` [L851-L855]

### `transcript_styles.py` (104 lines)
*transcript_styles.py - Transcript view stylesheets and dark-mode clipboard styling normalizers.*
- **Functions**:
  - `transcript_text_view_stylesheet(mode, font_size)` [L19-L62] — *Shared visual treatment for transcript-style views.*
  - `clean_dark_mode_clipboard_html(raw_html)` [L65-L104] — *Normalize plain text font colors to black (#000000) for external pasting.*

### `transcript_timeline_sync_mixin.py` (655 lines)
*Radio & TV Story Segmenter — Transcript Timeline & Playback Synchronization Mixin.*
- **class `TranscriptTimelineSyncMixin`** (lines 34–655):
  *Mixin for audio timecode synchronization, anchor indexing, and playback highlighting.*
  - `set_selection_mode(self, mode)` [L37-L41]
  - `set_char_timestamp_map(self, mapping)` [L43-L44]
  - `has_active_selection(self)` [L46-L52]
  - `clear_all_selections(self)` [L54-L67]
  - `get_time_range_for_char_span(self, start_pos, end_pos)` [L69-L85]
  - `get_selected_time_range(self)` [L87-L100]
  - `get_all_selected_story_ranges(self)` [L102-L122]
  - `select_comment_range(self, seg_idx)` [L124-L168]
  - `update_extra_selections(self)` [L170-L298]
  - `set_search_highlights(self, ranges, active_idx)` [L300-L336] — *Highlight all search matches across transcript with prominent active match.*
  - `clear_search_highlights(self)` [L338-L341] — *Clear all search match highlights from transcript.*
  - `set_timeline_selection_span(self, start_char, end_char)` [L343-L348]
  - `_on_selection_completed(self, cursor)` [L350-L382]
  - `_nearest_word_anchor(self, cursor)` [L384-L415]
  - `get_timestamp_at_cursor(self, cursor)` [L417-L436]
  - `get_block_start_timestamp(self, cursor)` [L438-L453]
  - `get_block_end_timestamp(self, cursor)` [L455-L473]
  - `get_segment_index_at_cursor(self, cursor)` [L475-L494]
  - `move_cursor_to_segment_start(self, seg_idx)` [L496-L511]
  - `rebuild_anchor_index(self)` [L513-L558]
  - `set_time_anchor_index(self, entries)` [L560-L562]
  - `clear_highlight(self)` [L564-L570]
  - `highlight_word_at_time(self, seconds, transcript_data, auto_scroll)` [L572-L655]

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

### `translation.py` (922 lines)
*Radio & TV Segmenter — Local Translation Mixin.*
- **class `TranslationEnvSetupWorker(QObject)`** (lines 35–92):
  *Background worker that sets up the isolated translation runtime environment.*
  - `__init__(self, plugin_dir, runtime_mgr)` [L40-L45]
  - `cancel(self)` [L47-L49]
  - `run(self)` [L51-L92]
- **class `TranslationMixin`** (lines 132–922):
  *Mixin class managing transcript translation, language toggling, and worker lifecycle.*
  - `source_language_code(self)` [L135-L168] — *Return the source language code for translation.*
  - `target_language_code(self)` [L170-L178] — *Return the target language code for translation (see source_language_code).*
  - `translation_key(self, from_code, to_code)` [L180-L182] — *Generate standardized dictionary key for language translation pair.*
  - `get_translation_item(self, from_code, to_code)` [L184-L193] — *Return a current translation for an explicit language pair.*
  - `translation_export_spec(self, options)` [L195-L208] — *Return (source, target, suffix) for batch translation exports.*
  - `translation_is_current(self, key)` [L210-L224] — *Check if translation for the given key exists, has content, and is not stale.*
  - `has_spanish_translation(self)` [L226-L232] — *Check if an English-to-Spanish translation is available.*
  - `get_spanish_translation_item(self)` [L234-L254] — *Return the translation dictionary for en-es or es-en if present.*
  - `mark_stale_translations(self)` [L256-L263] — *Mark all existing translations as stale when transcript text changes.*
  - `update_translation_language_selector(self)` [L265-L326] — *Update translation UI selector states (tabs / combobox / actions).*
  - `change_translation_display(self, mode)` [L328-L346] — *Change the active translation display mode ('en', 'es', or 'split').*
  - `render_translation_view(self)` [L348-L350] — *Re-render transcript or translation view based on current display settings.*
  - `check_translation_models_async(self)` [L352-L367] — *Asynchronously verify if required translation models are installed.*
  - `_cleanup_translation_env_thread(self)` [L369-L389]
  - `_on_translation_env_progress(self, percent_or_msg, message)` [L391-L404]
  - `stop_translation_worker(self, timeout_ms)` [L406-L459]
  - `_start_translation_runtime_request(self, request, on_finished)` [L461-L547] — *Run translation code in the plugin-owned isolated Python environment.*
  - `_on_translation_env_setup_finished(self, error)` [L549-L592]
  - `_launch_translation_process(self, request, on_finished, python_exe, entry)` [L594-L721]
  - `start_translation(self, from_code, to_code, install_if_missing)` [L723-L797] — *Start local translation in the translation plugin's isolated runtime.*
  - `_on_translation_progress(self, percent, message)` [L799-L809] — *Handle progress updates from _translation_worker_class().*
  - `_on_translation_finished(self, translated_transcript, translation_key)` [L811-L863] — *Handle successful translation results.*
  - `_on_translation_cancelled(self, results, translation_key)` [L865-L877] — *Handle translation worker cancellation.*
  - `_on_translation_error(self, error_message)` [L879-L913] — *Handle translation worker failures.*
  - `_on_translation_thread_finished(self)` [L915-L918] — *Clean up thread reference.*
  - `_translation_thread_finished(self)` [L920-L922] — *Alias for _on_translation_thread_finished.*
- **Functions**:
  - `_translation_worker_class()` [L22-L25] — *Load the translation worker only when the translation plugin is installed.*
  - `_translation_runtime_entry_path(app)` [L95-L121]
  - `_translation_runtime_manager(app)` [L123-L130]

### `ui_dialog_launchers.py` (370 lines)
*Dialog launchers and external modal helpers for Radio & TV Story Segmenter.*
- **class `UiDialogLaunchersMixin`** (lines 25–368):
  *Mixin providing dialog launcher methods for shortcuts, benchmarks, diagnostics, and plugins.*
  - `open_project_dialog(self)` [L27-L42] — *Prompt user to open a project file (*.rtvs).*
  - `open_find_dialog(self)` [L44-L79] — *Display the Find and Replace dialog window pre-populated with search term.*
  - `open_find_replace(self)` [L81-L83] — *Display the Find and Replace dialog window (alias for open_find_dialog).*
  - `show_shortcuts_dialog(self)` [L86-L267] — *Display a searchable, dynamically generated reference table of all active shortcuts.*
  - `show_diagnostic_test_bench(self)` [L269-L281] — *Open the interactive System Diagnostic Test Bench dialog.*
  - `show_performance_benchmark(self)` [L283-L295] — *Open the interactive System Performance & Speed Benchmark dialog.*
  - `open_plugins_manager(self)` [L297-L304] — *Open the Plugin Manager dialog to enable, disable, or inspect plugins.*
  - `open_id3_tag_editor(self, mp3_path)` [L306-L318] — *Open the ID3 Tag Editor dialog to view and edit MP3 audio metadata.*
  - `open_youtube_publish_dialog(self, story)` [L321-L344] — *Open the YouTube video publishing dialog or export view from the YouTube plugin.*
  - `open_wordpress_publish_dialog(self, story)` [L346-L362] — *Open the WordPress direct publish dialog from the WordPress plugin.*
  - `open_loudness_normalization_dialog(self)` [L364-L368] — *Open the Audio Loudness Normalization & Telemetry modal dialog.*

### `ui_layout.py` (1103 lines)
*Radio & TV Segmenter — UI Layout & Menu Construction Mixin.*
- **class `UiLayoutMixin(UiMenusMixin, UiDialogLaunchersMixin)`** (lines 58–1099):
  *Mixin class providing UI construction, menu assembly, and UI event binding.*
  - `build_ui(self)` [L60-L775] — *Build and assemble all central widgets, layouts, and panels.*
  - `filter_transcript_search(self, target)` [L777-L794] — *Highlight and focus next occurrence of search term in transcript text view.*
  - `toggle_transcript_editing_mode(self, *args, **kwargs)` [L796-L818] — *Toggle between Viewing Mode (navigation/click-to-seek) and Editing Mode (text editing).*
  - `_on_transcript_editing_mode_changed(self, is_editing)` [L820-L855] — *Respond to changes in transcript edit vs view mode.*
  - `_sync_format_toolbar_buttons(self)` [L857-L877]
  - `_on_toolbar_split_speaker(self)` [L879-L886]
  - `_apply_transcript_font_scale(self, scale, persist)` [L888-L912] — *Apply a transcript-only font scale and optionally persist it.*
  - `_on_font_size_combo_changed(self, index)` [L914-L918]
  - `adjust_transcript_font_size(self, direction)` [L920-L922] — *Increase or decrease transcript font size by one 5% step.*
  - `reset_transcript_font_size(self)` [L924-L926] — *Restore the default transcript font size.*
  - `update_story_list_height(self)` [L928-L943] — *Size the story list to fit the current number of stories, leaving space for metadata and export fields.*
  - `auto_generate_selected_story_excerpt(self)` [L945-L990] — *Auto-generate an excerpt from the story transcript text for the currently selected story.*
  - `_on_story_excerpt_text_changed(self)` [L992-L1010] — *Synchronize excerpt edits from the inline editor into story metadata.*
  - `toggle_maximize_stories_panel(self)` [L1012-L1065] — *Toggle maximize/restore of the stories panel across the full application window.*
  - `setup_plugin_story_extensions(self)` [L1067-L1089] — *Populate plugin-provided widgets in the story panel.*
  - `notify_story_selection_to_plugins(self, selected_story)` [L1091-L1099] — *Notify all enabled plugins when the active story selection changes.*

### `ui_menus.py` (923 lines)
*Main application menu bar and action assembly for Radio & TV Story Segmenter.*
- **class `PersistentMenu(QMenu)`** (lines 51–74):
  *A QMenu subclass that stays open when checkable toggle options are activated,*
  - `addMenu(self, *args, **kwargs)` [L55-L60]
  - `mouseReleaseEvent(self, event)` [L62-L74]
- **class `UiMenusMixin`** (lines 79–922):
  *Mixin providing menu construction, action shortcut wiring, and menu synchronization.*
  - `build_menus(self)` [L81-L690] — *Construct the main application menu bar and associated keyboard shortcuts.*
  - `apply_user_shortcuts(self)` [L692-L697] — *Rebind all menu actions and application shortcuts according to user preferences.*
  - `_refresh_recent_projects_menu(self)` [L699-L727] — *Update recent projects submenu items based on user settings store.*
  - `_check_external_dependencies(self)` [L729-L743] — *Check bundled media tools and record actionable diagnostics.*
  - `_sync_undo_redo_actions(self)` [L745-L754] — *Synchronize undo/redo action states with QUndoStack.*
  - `_remember_directory(self, path)` [L756-L766] — *Persist directory of chosen file to improve user file dialog experience.*
  - `update_processing_menu_status(self)` [L769-L785] — *Update label annotations on Tools actions reflecting pipeline stage completion.*
  - `refresh_plugin_menus(self)` [L788-L882] — *Dynamically populate plugin export actions, tools menu actions, and core UI controls.*
  - `trigger_smart_copy(self)` [L884-L904] — *Smart copy routing: active text cursor selection -> focused widget -> highlighted story transcript.*
  - `trigger_deselect_all(self)` [L906-L922] — *Clear all active selections across stories, timeline range, and transcript.*

### `updater.py` (80 lines)
*Update manager and GitHub release installer facade for Radio & TV Segmenter.*
- **Public Exports (`__all__`)**: APP_DISPLAY_NAME, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, PROJECT_VERSION, get_app_data_dir, get_github_repo, get_update_channel, get_app_icon, parse_version_tuple, is_version_newer, is_version_older, format_byte_size, _is_trusted_download_url, _find_release_checksum, select_best_asset_for_platform, fetch_releases, fetch_latest_release, _write_update_log, launch_and_install, cleanup_old_installers, CheckUpdateWorker, DownloadUpdateWorker, CheckUpdateDialog, UpdaterMixin

### `updater_core.py` (758 lines)
*Headless GitHub release metadata, semantic versioning, checksum verification,*
- **Public Exports (`__all__`)**: APP_DISPLAY_NAME, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, PROJECT_VERSION, get_app_data_dir, get_github_repo, get_update_channel, parse_version_tuple, is_version_newer, is_version_older, format_byte_size, _is_trusted_download_url, _find_release_checksum, select_best_asset_for_platform, fetch_releases, fetch_latest_release, _write_update_log, launch_and_install, cleanup_old_installers
- **Functions**:
  - `_show_install_error(parent, title, message)` [L75-L83] — *Lazy Qt error dialog helper invoked only when a GUI parent widget is provided.*
  - `parse_version_tuple(version_str)` [L86-L119] — *Parse version string into comparable numerical components and a pre-release weight tuple.*
  - `is_version_newer(remote_version_str, current_version_str)` [L122-L129] — *Return True if remote_version_str is strictly newer than current_version_str.*
  - `is_version_older(remote_version_str, current_version_str)` [L132-L139] — *Return True if remote_version_str is strictly older than current_version_str.*
  - `format_byte_size(num_bytes)` [L142-L149]
  - `_is_trusted_download_url(url)` [L152-L161]
  - `_find_release_checksum(release_info, asset_name)` [L164-L203]
  - `select_best_asset_for_platform(assets, target_version, repo)` [L206-L276] — *Select the most suitable release asset dictionary for the current operating system,*
  - `fetch_releases(repo, max_releases, channel)` [L279-L342] — *Query GitHub API for published releases, sorted semantically by version number.*
  - `fetch_latest_release(repo)` [L345-L350] — *Query GitHub API for the most recent release (backward-compatibility wrapper).*
  - `_write_update_log(msg)` [L353-L363] — *Append timestamped message to the update helper log in LocalAppData.*
  - `launch_and_install(file_path, parent)` [L366-L673]
  - `cleanup_old_installers(max_to_keep, force_all)` [L676-L735] — *Clean up old downloaded application update installers from AppData/updates directory.*

### `updater_dialog.py` (702 lines)
*Qt UI dialog and main-window mixin for checking, downloading, and installing updates.*
- **Public Exports (`__all__`)**: get_app_icon, CheckUpdateDialog, UpdaterMixin
- **class `CheckUpdateDialog(QDialog)`** (lines 78–659):
  - `__init__(self, parent, auto_start)` [L79-L109]
  - `_build_ui(self)` [L111-L246]
  - `_on_channel_changed(self, index)` [L248-L255]
  - `start_check(self)` [L257-L277]
  - `_on_releases_loaded(self, releases)` [L279-L314]
  - `_on_version_selected(self, index)` [L316-L320]
  - `_display_release(self, release_info)` [L322-L429]
  - `_on_up_to_date(self, current_ver, remote_tag)` [L431-L443]
  - `_on_update_available(self, release_info, asset_info, is_newer)` [L445-L446]
  - `_on_check_error(self, message)` [L448-L454]
  - `_handle_primary_action(self)` [L456-L470]
  - `_confirm_downgrade(self, target_version)` [L472-L487] — *Modal Warning Dialog when selecting a version lower than installed PROJECT_VERSION.*
  - `start_download(self)` [L489-L519]
  - `_on_download_progress(self, percent, downloaded, total, speed_str)` [L521-L525]
  - `_on_download_finished(self, file_path)` [L527-L534]
  - `_on_download_error(self, message)` [L536-L555]
  - `_install_and_restart(self)` [L557-L641]
  - `_open_github_release(self)` [L643-L645]
  - `_handle_close(self)` [L647-L659]
- **class `UpdaterMixin`** (lines 662–695):
  - `check_for_updates(self, interactive)` [L663-L669]
  - `trigger_silent_update_check(self)` [L671-L695]

### `updater_workers.py` (189 lines)
*Background QThread workers for GitHub release checking and installer downloads.*
- **Public Exports (`__all__`)**: CheckUpdateWorker, DownloadUpdateWorker
- **class `CheckUpdateWorker(QThread)`** (lines 37–95):
  - `__init__(self, repo, parent, channel)` [L43-L49]
  - `run(self)` [L51-L95]
- **class `DownloadUpdateWorker(QThread)`** (lines 98–183):
  - `__init__(self, download_url, file_name, parent, release_info)` [L103-L108]
  - `cancel(self)` [L110-L111]
  - `run(self)` [L113-L183]

### `user_guide_dialog.py` (846 lines)
*Radio & TV Story Segmenter — In-App User Guide & Documentation Viewer Dialog.*
- **class `ResponsiveTextBrowser(QTextBrowser)`** (lines 49–109):
  *QTextBrowser subclass that responsively scales embedded images to viewport width.*
  - `__init__(self, parent)` [L52-L54]
  - `resizeEvent(self, event)` [L56-L58]
  - `scale_images_to_viewport(self)` [L60-L109]
- **class `UserGuideDialog(QDialog)`** (lines 112–846):
  *In-app reader dialog displaying rich user guides with inline screenshots.*
  - `_find_docs_dir()` [L154-L188] — *Locate the docs directory across frozen executables, installed dirs, and dev trees.*
  - `__init__(self, parent, initial_guide_id)` [L190-L208]
  - `_setup_ui(self)` [L210-L362]
  - `_apply_browser_stylesheet(self)` [L364-L408]
  - `_resolve_image_urls(self, markdown_text)` [L410-L426] — *Replace relative image paths in markdown with absolute file URIs for instant rendering.*
  - `_load_guide_by_id(self, guide_id)` [L428-L486]
  - `_on_topic_selected(self, row)` [L488-L492]
  - `_focus_search(self)` [L494-L496]
  - `_get_guide_raw_text(self, guide_id)` [L498-L518]
  - `_update_cross_topic_badges(self, query)` [L520-L560]
  - `_on_search_query_changed(self, text)` [L562-L565]
  - `_execute_in_doc_search(self, query, other_matches_count)` [L567-L606]
  - `_update_match_label(self)` [L608-L617]
  - `_highlight_matches(self, scroll)` [L619-L646]
  - `_find_next_match(self)` [L648-L669]
  - `_find_prev_match(self)` [L671-L692]
  - `keyPressEvent(self, event)` [L694-L701]
  - `_zoom_in(self)` [L703-L706]
  - `_zoom_out(self)` [L708-L711]
  - `_reset_zoom(self)` [L713-L717]
  - `_open_in_external_browser(self)` [L719-L792] — *Export the current guide as a self-contained styled HTML file and launch the system web browser.*
  - `_build_dynamic_shortcuts_guide(self)` [L794-L846] — *Build complete keyboard shortcut documentation dynamically from active schema & user bindings.*

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

### `voice_profile_ops_mixin.py` (730 lines)
*Radio & TV Story Segmenter — Voice Profile Matching & Embedding Extraction Mixin.*
- **class `VoiceProfileOpsMixin`** (lines 45–730):
  *Mixin for acoustic voice profile matching, WeSpeaker embeddings, and voice training.*
  - `get_segment_embedding(self, seg_idx)` [L48-L163] — *Retrieve a genuine 256-dimensional acoustic embedding for this segment.*
  - `get_composite_embedding(self, seg_indices)` [L165-L175]
  - `_build_voice_profile_candidates(self, ref_indices, parent_widget)` [L177-L249] — *Precompute candidate acoustic vectors across transcript segments.*
  - `find_matching_voice_turns(self, ref_seg_idx, threshold, scope_cluster_only, ref_seg_indices, target_name, cached_candidates)` [L251-L401] — *Find transcript turns acoustically matching a verified voice.*
  - `match_acoustic_voice_profile(self, ref_seg_idx, target_speaker, threshold, scope_cluster_only, selected_indices, ref_seg_indices)` [L403-L497]
  - `teach_voice_profile_dialog(self, seg_idx, raw_speaker, prompt_new_speaker)` [L499-L579]
  - `_get_station_voice_store(self)` [L581-L587]
  - `is_speaker_saved_to_station_voices(self, speaker_name)` [L589-L595]
  - `_collect_speaker_segment_indices(self, speaker_name)` [L597-L610]
  - `has_speaker_voice_embedding_source(self, speaker_name, seg_indices)` [L612-L632]
  - `save_speaker_to_station_voices(self, speaker_name, seg_indices, allow_extract)` [L634-L708]
  - `remove_speaker_from_station_voices(self, speaker_name)` [L710-L724]
  - `open_manage_voice_profiles_dialog(self)` [L726-L730]

### `waveform_envelope.py` (55 lines)
*Waveform envelope data structures, downsampling pyramids, and cache helpers.*
- **class `WaveformEnvelope(list)`** (lines 14–19):
  *Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels.*
  - `__init__(self, iterable, levels)` [L17-L19]
- **Functions**:
  - `build_waveform_pyramid(peaks)` [L22-L55] — *Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.*

### `worker_asr_engines.py` (958 lines)
*worker_asr_engines.py - Faster-Whisper, CTranslate2 & Sherpa-ONNX ASR Engines.*
- **Functions**:
  - `set_emit_callback(fn)` [L35-L38] — *Set custom IPC emitter function.*
  - `_has_speech_energy(audio_slice, sr, rms_db_thresh, peak_db_thresh)` [L41-L65] — *Return True when >=2 half-second sub-windows show active audio above silence.*
  - `_decode_onnx_chunk_with_rescue(recognizer, samples, c_start, c_end, duration_sec, is_word_boundary_fn)` [L68-L182] — *Decode one acoustic chunk and rescue uncovered speech tails/heads from premature blanking.*
  - `_group_onnx_words_into_segments(chunk_words, duration_sec, language)` [L185-L228] — *Group word timestamps into readable transcript segments without splitting titles/abbreviations.*
  - `_emit(message_type, **payload)` [L231-L237]
  - `_patch_av_open()` [L240-L254] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `get_optimal_transcription_threads()` [L257-L276] — *Calculate optimal CPU threads for faster-whisper / CTranslate2 / ONNX.*
  - `get_app_data_dir_pure()` [L279-L297] — *Return platform-specific app data directory in pure Python without PySide6.*
  - `get_models_storage_dir_pure()` [L300-L310] — *Return models storage directory in pure Python without PySide6.*
  - `is_onnx_model_available(model_name)` [L313-L370] — *Check if sherpa-onnx runtime and target model files exist on disk.*
  - `transcribe_parakeet_onnx(audio_file, model_name, detected_lang, detected_confidence, initial_prompt, beam_size)` [L373-L625] — *Run installed ONNX models (Parakeet TDT, Spanish FastConformer, Multilingual FastConformer) through sherpa-onnx.*
  - `probe_audio_language(audio_file, sample_duration, preferred_model)` [L628-L728] — *Run a fast language detection probe using faster-whisper's mel feature extractor.*
  - `transcribe(audio_file, model_name, initial_prompt, beam_size)` [L731-L958] — *Transcribe media file using either Sherpa-ONNX or Faster-Whisper.*

### `worker_clustering.py` (457 lines)
*worker_clustering.py - Acoustic clustering, VAD pause bridging, and centroid assignments.*
- **Functions**:
  - `normalize_audio_for_diarization(source_path, apply_bandpass)` [L29-L92] — *Extract a normalized 16 kHz mono WAV using the local FFmpeg binary.*
  - `configure_optimal_pytorch_threads()` [L95-L109] — *Clamp torch's intra-op/inter-op thread pools to match the*
  - `_normalize_expected_speakers(value)` [L112-L121] — *Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'.*
  - `_normalize_speaker_labels(segments)` [L124-L137] — *Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',*
  - `_sensitivity_distance_threshold()` [L140-L146] — *Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.*
  - `fast_cluster_ahc(embeddings, k, distance_threshold)` [L149-L205] — *Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).*
  - `apply_clustering_patches()` [L208-L241] — *Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC.*
  - `run_vad_two_pass(audio_path, threshold, min_speech_duration_ms, min_silence_duration_ms, speech_pad_ms, bridge_pause_threshold_sec)` [L244-L317] — *Silero VAD with Pass 1 Pause Bridging (< 100ms).*
  - `assign_short_segments_to_centroids(short_segments, audio_path, centroids, label_values, raw_segments, min_confidence, model)` [L320-L429] — *Extract acoustic embeddings for short segments (< 0.8s) with symmetric audio context padding,*
  - `_calculate_embedding_for_interval(start, end, subsegments, embeddings)` [L432-L457] — *Compute unit-normalized 256-dimensional embedding vector for an interval [start, end].*

### `worker_diarization_clustering.py` (634 lines)
*worker_diarization_clustering.py - Speaker Clustering, Centroid Matching & Math Helpers.*
- **Functions**:
  - `_normalize_expected_speakers(value)` [L24-L33] — *Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'.*
  - `_normalize_speaker_labels(segments)` [L36-L49] — *Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',*
  - `_sensitivity_distance_threshold(sensitivity)` [L52-L60] — *Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.*
  - `_sensitivity_centroid_merge_threshold(sensitivity)` [L63-L68] — *Post-clustering centroid cosine-distance threshold calibrated for WeSpeaker embeddings.*
  - `consolidate_speaker_clusters(embeddings, labels, min_fraction, max_min_cluster, centroid_merge_dist)` [L71-L127] — *Absorb noisy micro-clusters into nearest major speakers and merge redundant centroids.*
  - `merge_adjacent_diarization_segments(segments, max_gap)` [L130-L151] — *Merge consecutive diarization segments from the same speaker separated by < max_gap seconds.*
  - `smooth_short_speaker_islands(segments, unconditional_threshold, gated_max_duration, max_foreign_margin, min_surround_sim, max_gap)` [L154-L259] — *Smooth brief A -> B -> A mid-turn speaker islands in place.*
  - `prepare_transcript_speech_segments(valid_segments, vad_segments, speech_segment_cls, min_primary_duration, min_vad_span, vad_bridge_gap, min_total_vad_coverage)` [L262-L347] — *Split transcript segments into primary (>= min_primary_duration) and short segments,*
  - `cluster_speakers_ahc(embeddings, min_speakers, max_speakers, num_speakers, distance_threshold, sensitivity)` [L350-L382] — *Cluster speaker embeddings with O(N^2) cosine AHC, honoring sensitivity and speaker bounds.*
  - `fast_cluster_ahc(embeddings, k, distance_threshold)` [L385-L441] — *Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).*
  - `apply_clustering_patches()` [L444-L481] — *Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC.*
  - `assign_short_segments_to_centroids(short_segments, audio_path, centroids, label_values, raw_segments, min_confidence, get_wespeaker_model_fn, safe_tensor_fn)` [L484-L606] — *Extract acoustic embeddings for short segments (< 0.8s) with symmetric context padding,*
  - `_calculate_embedding_for_interval(start, end, subsegments, embeddings)` [L609-L634] — *Compute unit-normalized 256-dimensional embedding vector for an interval [start, end].*

### `worker_diarization_engine.py` (979 lines)
*worker_diarization_engine.py - Speaker Diarization, Neural VAD & Embedding Pipeline.*
- **Functions**:
  - `set_emit_callback(fn)` [L55-L58] — *Set custom IPC emitter function.*
  - `_emit(message_type, **payload)` [L61-L67]
  - `_safe_tensor_from_numpy(arr)` [L70-L85] — *Safely convert a numpy float32 array into a PyTorch tensor.*
  - `normalize_audio_for_diarization(source_path, apply_bandpass)` [L88-L151] — *Extract a normalized 16 kHz mono WAV using the local FFmpeg binary.*
  - `configure_optimal_pytorch_threads()` [L154-L167] — *Clamp torch's intra-op/inter-op thread pools to match the*
  - `_diarize_solo_fast_path(audio_file, transcript_file)` [L170-L244] — *Solo fast-path: a single expected speaker means there is nothing to*
  - `_get_wespeaker_model()` [L252-L260] — *Retrieve or initialize the cached WeSpeaker ONNX model instance.*
  - `extract_embeddings_batched(audio_path, speech_segments, batch_size, min_segment_duration, embedding_window, embedding_step, progress_callback)` [L263-L407] — *Extract 256-dim speaker embeddings using WeSpeaker ResNet34-LM (ONNX)*
  - `run_vad_two_pass(audio_path, threshold, min_speech_duration_ms, min_silence_duration_ms, speech_pad_ms, bridge_pause_threshold_sec)` [L410-L480] — *Silero VAD with Pass 1 Pause Bridging (< 100ms).*
  - `run_transcript_guided_diarization(normalized_wav, transcript_file, expected_speakers, sensitivity, progress_callback)` [L483-L632] — *Execute transcript-guided speaker diarization directly from sentence boundaries.*
  - `diarize(audio_file, expected_speakers, transcript_file, sensitivity)` [L635-L979] — *Execute complete speaker diarization pipeline on an audio media file.*

### `worker_ipc.py` (216 lines)
*worker_ipc.py - Subprocess IPC protocol, environment setup, and DLL initialization.*
- **Functions**:
  - `emit(message_type, **payload)` [L24-L28] — *Serialize and send structured JSON message to parent process over stdout.*
  - `emit_hello()` [L31-L33] — *Emit startup handshake message identifying protocol version and worker capabilities.*
  - `_patch_av_open()` [L36-L54] — *Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.*
  - `_clamp_diarization_thread_env()` [L57-L82] — *Cap OMP/ONNX Runtime/BLAS thread pools before onnxruntime, torch, or the*
  - `_setup_windows_dll_directories()` [L85-L195] — *Register native DLL directories (PyTorch, CTranslate2, ONNX Runtime, etc.)*
  - `_safe_tensor_from_numpy(arr)` [L198-L216] — *Safely convert a numpy float32 array into a PyTorch tensor.*

### `worker_story_engine.py` (396 lines)
*worker_story_engine.py - Acoustic & Lexical Story Boundary Detection Engine.*
- **Functions**:
  - `is_real_speech(text)` [L41-L48] — *Return True if text represents actual spoken words rather than music/sound tokens.*
  - `detect_story_boundaries(audio_file, silence_threshold, lead_in_padding, audio_duration, transcript_segments, whisper_model, detection_mode, min_story_duration, is_cancelled_fn, progress_callback)` [L51-L396] — *Execute acoustic and lexical story boundary detection on an audio file.*


# Changelog

## v3.10.0-beta
- **Phase 1: Diarization Sensitivity & Speedup, Debounced Micro-Edit Saves, Run Processing Memory & Google Docs Remnant Cleanup (`worker_diarization_clustering.py`, `worker_diarization_engine.py`, `processing.py`, `project_lifecycle.py`, `project_export.py`, `story_widgets.py`, `story_crud_mixin.py`, `speaker_editing_mixin.py`, `speaker_dialog_refinement_mixin.py`, `voice_profile_ops_mixin.py`, `project_state_mixin.py`, `RadioTVSegmenter.py`, `export/reorder_dialog.py`, `preferences_tabs_media.py`, `embedded_guides.py`, `.github/workflows/build.yml`, `diagnostic_core_tests.py`, `diagnostic_cloud_and_system_tests.py`, `diagnostic_batch_tests.py`)**:
  - **Diarization Sensitivity, Double-Windowing & Progress Fixes (`worker_diarization_clustering.py`, `worker_diarization_engine.py`)**:
    - Passed `sensitivity` cleanly through `run_transcript_guided_diarization()` without resetting `PRS_DIARIZATION_SENSITIVITY` to `"normal"`, fixed missing `diarize._merge_adjacent_segments` import + 3-arg `_build_diarization_segments()` call (replacing with `merge_adjacent_diarization_segments()`), and eliminated redundant 3.0s/1.5s double-windowing on segments > 6s.
    - Added `cluster_speakers_ahc()` (patched into `diarize.clustering` via `apply_clustering_patches()`) to honor sensitivity thresholds in auto mode and bypass multi-model GMM BIC stalls.
    - Wired live window progress into `extract_embeddings_batched()` and standalone VAD fallback so the ticker no longer prematurely reports clustering while extraction is still running.
  - **Run Processing Stage Persistence (`processing.py`)**:
    - Saved and restored `pipeline_opt_*` checkbox preferences in `QSettings` (defaulting `Translate Transcript` off on first run unless Spanish export or batch translation is enabled) without clobbering already-completed stage defaults.
  - **Debounced Micro-Edit Saves & `.rtvs.backup` Throttling (`project_lifecycle.py`, `project_export.py`, `story_widgets.py`, `story_crud_mixin.py`, `speaker_editing_mixin.py`, `speaker_dialog_refinement_mixin.py`, `voice_profile_ops_mixin.py`, `project_state_mixin.py`)**:
    - Added `schedule_project_save()`, `flush_pending_project_save()`, and `cancel_pending_project_save()` (1.5s single-shot coalescing for saved `.rtvs` projects), flushed cleanly before close/load prompts while keeping explicit saves immediate.
    - Throttled `.rtvs.backup` rotation (`RECOVERY_BACKUP_MIN_INTERVAL_SEC = 300.0`) so recovery backups happen at most once per 5 minutes per project instead of on every drag.
  - **Google Docs Export Cleanup (`RadioTVSegmenter.py`, `export/reorder_dialog.py`, `preferences_tabs_media.py`, `embedded_guides.py`, `.github/workflows/build.yml`)**:
    - Scrubbed stale `gdocs` / `plugin_enabled_gdocs` keys from `QSettings` on startup, cleaned destination-order tooltips and guide bullets, and removed dead `plugin_gdocs` / `BUILD_PLUGIN_GDOCS` hooks from CI build workflows.
  - **Regression Tests (`diagnostic_core_tests.py`, `diagnostic_cloud_and_system_tests.py`, `diagnostic_batch_tests.py`)**:
    - Extended `_test_wespeaker_diarization_architecture` and `_test_project_serialization_round_trip` for sensitivity clustering, single-pass transcript-guided diarization, debounced saves, backup throttling, and `ProcessingMixin` checkbox persistence, and updated CI/UI Google Docs removal checks.

## v3.9.99-beta
- **UX Responsiveness, Timeline Right-Click Dead Zones & Floating Toolbar Fixes (`transcript_timeline_sync_mixin.py`, `timeline_widgets.py`, `background_workers.py`, `project_lifecycle.py`, `plugins/wordpress/wp_tab_widget.py`, `translation.py`, `diagnostic_editor_tests.py`, `diagnostic_export_tests.py`)**:
  - **Floating Selection Toolbar Guard & Positioning (`transcript_timeline_sync_mixin.py`)**:
    - Enforced the `show_floating_selection_toolbar` preference and `not is_editing_mode` guard inside `TranscriptTimelineSyncMixin._on_selection_completed()` (previously only enforced in an unimported legacy mixin), and positioned `selection_bubble` using viewport-local coordinates instead of global screen coordinates.
  - **Timeline Right-Click Dead Zones & Drag Hysteresis (`timeline_widgets.py`)**:
    - Guarded fade handle hit-testing to left mouse clicks so right-clicking near fade handles opens the timeline context menu immediately (including **Adjust Story Fades...**).
    - Added a 5px horizontal right-drag threshold (`_check_right_drag`) before starting range selection or edge drags on right-button press, opening the context menu cleanly on right-button release when clicking near segment edges or with minor cursor jitter.
    - Extracted shared `_handle_media_drag_event()` helper and removed dead left-drag fields.
  - **UI-Thread Save & Keystroke Lag Elimination (`background_workers.py`, `project_lifecycle.py`, `plugins/wordpress/wp_tab_widget.py`, `translation.py`)**:
    - Added a NumPy `tobytes()` fast path (`_pack_f32()`) and `skip_if_exists=True` valid cache check in `write_waveform_peak_cache()` so `save_project()` and `_write_project_file()` no longer rebuild and `os.fsync()` 360k-peak `.peaks` files synchronously on every auto-save.
    - Gated `refresh_story_list()` inside `WordPressExportTabWidget._sync_post_to_project()` strictly on actual story `title` or `author` changes, and added `log_reason: bool = False` to eliminate per-keystroke story list rebuilds and `[PROJECT] Update WordPress Metadata` log storms.
    - Removed per-lookup `[DEBUG] source_language_code` log spam from `translation.py`.
  - **Regression Verification (`diagnostic_editor_tests.py`, `diagnostic_export_tests.py`)**:
    - Added automated checks covering floating toolbar enable/disable + viewport geometry (`6d`), timeline right-click menus over fade handles, edges, and 2px jitter (`6e`), `skip_if_exists` peak cache preservation (`6f`), and zero `refresh_story_list` / `log_reason` triggers during WordPress caption/alt typing (plus updated `6c` `TimelineCanvas(None)` parentage for real PySide6 compatibility).

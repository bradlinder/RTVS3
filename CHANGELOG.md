# Changelog

## v3.10.1-beta
- **Phase 1.1: Diarization Outlier Consolidation, 1.5s Embedding Windows & Run Processing Partial-Stage Fix (`worker_diarization_clustering.py`, `worker_diarization_engine.py`, `processing.py`, `diagnostic_core_tests.py`)**:
  - **Micro-Cluster Absorption & Centroid Merging (`worker_diarization_clustering.py`)**:
    - Added `_sensitivity_centroid_merge_threshold()` and `consolidate_speaker_clusters()`, absorbing small noise/outlier micro-clusters into nearest major speaker centroids and iteratively merging near-duplicate centroids *before* enforcing `min_speakers`/`max_speakers` in `cluster_speakers_ahc()`, eliminating 20-speaker over-splitting on 2-speaker interviews.
  - **1.5s Transcript-Guided Windows & Sensitivity Pass-Through (`worker_diarization_engine.py`)**:
    - Updated `run_transcript_guided_diarization()` to pass `embedding_window=1.5, embedding_step=0.75` to `extract_embeddings_batched()` for cleaner speaker embeddings and faster CPU inference, and passed `sensitivity=sensitivity` into `cluster_speakers_ahc()`.
  - **Run Processing Existing-Data Preservation (`processing.py`)**:
    - Updated `start_full_auto_pipeline()` so unchecking any stage that already has loaded transcript or diarization data (`existing_map`) does not overwrite `pipeline_opt_*` to `false` for future fresh episodes.
  - **Regression Coverage (`diagnostic_core_tests.py`)**:
    - Added a 60-vector outlier-absorption test in `_test_wespeaker_diarization_architecture` and existing-data `pipeline_opt_*` preservation assertions in `_test_project_serialization_round_trip`.

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

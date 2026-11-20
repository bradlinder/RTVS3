# Changelog

## v3.10.2-beta
- **Phase 2: Adjustable Minimum Story Length, Guest Name & Proper-Noun Cleanup Pipeline & Save to Station Voices (`RadioTVSegmenter.py`, `preferences_tabs_media.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`, `story_detection_processing.py`, `background_workers.py`, `worker_story_engine.py`, `speaker_name_matcher.py`, `speaker_name_cleanup_dialog.py`, `transcript_editor_dialogs.py`, `speaker_dialogs.py`, `speaker_editing_mixin.py`, `voice_profile_ops_mixin.py`, `diarization_processing.py`, `diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
  - **Adjustable Minimum Story Length (`RadioTVSegmenter.py`, `preferences_tabs_media.py`, `preferences_dialog.py`, `preferences_reset.py`, `preferences_reset_dialog.py`, `story_detection_processing.py`, `background_workers.py`, `worker_story_engine.py`)**:
    - Added `Minimum Story Length:` (`min_story_duration`, `0.0–600.0 sec`, default `3.0 sec`) to **Preferences > Story Detection & Diarization**, persisted via `QSettings` with reset-to-defaults support, and enforced in both `StoryAutoDetectWorker` and `detect_story_boundaries()` (keeping the full-episode fallback if every candidate segment is shorter).
  - **Guest Name & Proper-Noun Cleanup Pipeline (`speaker_name_matcher.py`, `speaker_name_cleanup_dialog.py`, `transcript_editor_dialogs.py`, `speaker_dialogs.py`)**:
    - Created pure-Python `speaker_name_matcher.py` providing broadcast phonetic normalization, Soundex/skeleton matching against confirmed speakers, common-word suppression, `preserve_case_replace()` (`ife -> Iffy` also handles `IFE -> IFFY`), and bulk replacement with word-timing sync.
    - Created modal `SpeakerNameCleanupDialog` (`Fix Speaker Names...`) accessible from both `Find and Replace` and `Manage Speakers`, with editable `Replace With` cells, optional Glossary saving (`add_alternate_spelling`), and single-step grouped Undo.
    - Upgraded `FindReplaceDialog` with **Preserve Case** (on by default), trailing/leading whitespace warning banner + one-click **Trim** button, **Add to Glossary**, and **Fix Speaker Names...**.
  - **Save to Station Voices & `78 -> 0.78` Auto-Match Fix (`RadioTVSegmenter.py`, `diarization_processing.py`, `preferences_tabs_media.py`, `voice_profile_ops_mixin.py`, `speaker_dialogs.py`, `speaker_editing_mixin.py`)**:
    - Fixed `voice_profile_auto_match_threshold` (`78` saved by Preferences was previously clamped to `0.99` on launch instead of `0.78`).
    - Added shared `save_speaker_to_station_voices()` / `remove_speaker_from_station_voices()` helpers on `VoiceProfileOpsMixin` (reusing cached segment embeddings first), an opt-in **Save to Station Voices** checkbox inside `ChangeSpeakerDialog`, a per-row **Station Voice** column toggle in `SpeakerManagerDialog`, and an offscreen `QMediaPlayer` teardown guard for headless test runs.
  - **Automated Regression Verification (`diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
    - Added `DiagnosticSpeakerCleanupTestsMixin` covering `min_story_duration` filtering & Preferences spinbox, 9 real broadcast guest-name misspellings + stopword suppression + Preserve Case + Trim/Glossary/Undo, and Station Voice checkboxes + `78 -> 0.78` threshold normalization.

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

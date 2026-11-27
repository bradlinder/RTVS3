# Changelog

## v3.10.30-beta
- **Eliminate Phantom Extra Speakers in Diarization (Zero-Padding-Free WeSpeaker Batching, Silero VAD Pause Trimming, Embedding-Gated Island Smoothing & 1-Based Speaker Labeling) (`worker_diarization_engine.py`, `worker_diarization_clustering.py`, `speaker_editing_mixin.py`, `diagnostics/voice_and_media_tests.py`, `test_runner.py`)**:
  - **Zero-Padding-Free WeSpeaker Batching & Clean Tail Windows (`worker_diarization_engine.py`)**:
    - Replaced zero-padded 32-window batching in `extract_embeddings_batched()` with exact-frame-length bucketing (preserving exact 1-to-1 subsegment ordering and single-item fallback), eliminating artificial zero-frame contamination of WeSpeaker ResNet34-LM temporal statistics pooling that pulled short windows across an episode into a phantom speaker.
    - Stopped emitting redundant trailing `<0.75s` sub-windows once a sliding window reaches `seg_end`, and right-aligned `<1.0s` trailing stubs on longer segments to extract a full `1.5s` acoustic slice while keeping subsegment timestamps crisp.
  - **Silero VAD Pause Trimming for Transcript-Guided Diarization (`worker_diarization_engine.py`, `worker_diarization_clustering.py`)**:
    - Added `prepare_transcript_speech_segments()` and ran `run_vad_two_pass()` before embedding extraction in `run_transcript_guided_diarization()` to strip Whisper-padded silence, breaths, and room-tone tails (which otherwise clustered across an episode into an extra "room-tone" speaker), routing unvoiced turns safely to short fallback and gracefully falling back to untrimmed boundaries on very quiet or synthetic audio.
  - **Embedding-Gated `A → B → A` Short-Island Smoothing (`worker_diarization_clustering.py`, `worker_diarization_engine.py`)**:
    - Added `smooth_short_speaker_islands()` keeping unconditional smoothing at `<= 0.7s` while smoothing `0.7s–1.5s` tightly embedded mid-turn islands only when acoustic similarity favors or is ambiguous toward the surrounding speaker (preserving genuine 1-second interjections from distinct speakers and islands across `> 2.0s` silence gaps).
  - **Fix `+1` Off-by-One Speaker Numbering (`speaker_editing_mixin.py`)**:
    - Restricted `display_speaker()`'s `+1` increment strictly to legacy 0-indexed `SPEAKER_XX` IDs (`^SPEAKER_(\d+)$`) so already 1-indexed labels (`Speaker 1`..`Speaker N`) and custom names ending in digits (e.g. `Caller 1`) display accurately without shifting up by one.

## v3.10.29-beta
- **System-Wide Qt Zero-Flash Fix Across Export, Open Remote Episode & Classic Export Dialogs + Permanent AST & Multi-Dialog Guards (`plugins/youtube/export_destination.py`, `plugins/youtube/yt_import_dialog.py`, `plugins/youtube/manifest.json`, `export_dialogs.py`, `scripts/dev_check.py`, `AGENTS.md`, `diagnostics/editor_story_ui_tests.py`)**:
  - **Fix Remaining Orphan-Window Flashes (`plugins/youtube/export_destination.py`, `plugins/youtube/yt_import_dialog.py`, `export_dialogs.py`)**:
    - Fixed `YouTubeExportTabWidget._setup_ui()` (parented `yt_scrub_widget` / `yt_browse_widget` and moved initial `_on_yt_thumb_mode_changed()` after `yt_extras_section.add_layout(yt_extras_layout)`), eliminating the fleeting window flash when opening `UnifiedExportDialog` on video projects.
    - Fixed `LoadYouTubeEpisodeDialog._build_ui()` (`File > Open Remote Episode`) by parenting `fetch_btn` and `wp_link_edit` to `self` and applying initial `.setVisible()` after layout attachment, and fixed `export_dialogs.py:_choose_export_formats()` where `media.setVisible(media_available)` ran on an unparented `QCheckBox` before `layout.addWidget(media)`.
    - Repackaged `youtube.rtvs-addon` (`3.10.29-beta`).
  - **Permanent System-Wide Guards (`scripts/dev_check.py`, `diagnostics/editor_story_ui_tests.py`, `AGENTS.md`)**:
    - Added Pillar 5 (`check_qt_orphan_widget_flashes()`) to `scripts/dev_check.py` (statically auditing 180+ modules via AST for pre-attach non-`False` `.setVisible()` / `.setRowVisible()` calls, and removed now-modularized `background_workers.py` from `GRANDFATHERED`).
    - Upgraded the Qt `QEvent.Show` orphan-window spy in `diagnostics/editor_story_ui_tests.py` to sweep `UnifiedExportDialog` (with WordPress & YouTube plugins), `LoadYouTubeEpisodeDialog`, Preferences tabs, and core dialogs alongside the static AST check, and documented the zero-flash parenting rule in `AGENTS.md`.

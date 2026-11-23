# Changelog

## v3.10.11-beta
- **Abbreviation-Aware Sentence/Diarization Boundaries & Parakeet Uncovered-Speech Rescue (`sentence_boundaries.py`, `core_utils.py`, `transcript_story.py`, `export_documents.py`, `reaper_bridge.py`, `plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`, `worker_asr_engines.py`, `worker_diarization_engine.py`, `worker_diarization_clustering.py`, `worker_clustering.py`, `diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
  - **Shared Context-Aware Abbreviation Engine (`sentence_boundaries.py`, `core_utils.py`, `transcript_story.py`, `export_documents.py`, `reaper_bridge.py`, `plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`)**:
    - Created pure-Python `sentence_boundaries.py` classifying pre-noun titles (`Dr.`, `Mr.`, `Mrs.`, `Prof.`, `Sen.`, `Sra.`, `Sr.`, etc.), initials, mid-clause connectors, month/number prefixes (`Jan. 15`, `No. 5` vs. `"No. I"`), and next-word-sensitive dotted acronyms (`U.S. today` vs. `D.C. Then`).
    - Wired context-aware `is_sentence_end(text, next_word, language)` across `core_utils.py`, in-app paragraphing (`transcript_story.py`), TXT/DOCX/PDF export (`export_documents.py`), REAPER take cues (`reaper_bridge.py`), and WordPress paragraphing (`plugins/wordpress/client.py`, bumping `plugins/wordpress/manifest.json` to `3.10.11-beta`).
  - **Unfiltered Parakeet ONNX Audio, Tail/Head Speech Rescue & Abbreviation Chunking (`worker_asr_engines.py`, `worker_diarization_engine.py`, `worker_clustering.py`)**:
    - Added `apply_bandpass: bool = True` to `normalize_audio_for_diarization()` and disabled the 85–7500 Hz diarization bandpass during Parakeet/FastConformer ASR (`apply_bandpass=False`) so full-bandwidth 16 kHz audio matches its 128-bin mel filterbank.
    - Added `_decode_onnx_chunk_with_rescue()` and `_has_speech_energy()` to automatically recover trailing/leading speech spans (`>= 2.5s`) dropped by premature TDT blanking on loud→quiet speaker transitions while skipping true silence.
    - Extracted `_group_onnx_words_into_segments()` using context-aware `is_sentence_end()` and deferring 12-word flushes on non-terminal titles (`"Dr."`, `"Mr."`) so titles stay glued to the following surname.
  - **Diarization Abbreviation Glue & Edge-to-Edge Gap Fallback (`worker_diarization_engine.py`, `worker_diarization_clustering.py`, `worker_clustering.py`)**:
    - Merged pre-noun abbreviation segments into adjacent following speech (`gap < 0.45s`) before transcript-guided embedding extraction, and updated `assign_short_segments_to_centroids()` fallback from midpoint distance to nearest edge-to-edge gap.
  - **Regression Coverage (`diagnostic_speaker_cleanup_tests.py`, `test_runner.py`)**:
    - Added `Abbreviation Sentence Boundaries and Parakeet Rescue` covering EN/ES title rules, false-positive traps, 12-word boundary glue, tail speech rescue vs. silence skip, `0.00s` edge-gap snapping, and WordPress paragraphing.

## v3.10.10-beta
- **Diagnostic Parity Fixes: Embedded Guide Key, Action Button Polish & Story Fade Test Isolation (`embedded_guides.py`, `speaker_profiles_dialog.py`, `diagnostic_editor_tests.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **Fix `video_shows` Embedded Guide Lookup (`embedded_guides.py`, `diagnostic_speaker_cleanup_tests.py`)**:
    - Renamed `EMBEDDED_GUIDES["video_youtube"]` back to `"video_shows"` so frozen builds resolve *Video Shows & YouTube Publishing* properly and synced the key in `diagnostic_speaker_cleanup_tests.py`.
  - **Live-Theme QSS Polish Timing (`speaker_profiles_dialog.py`)**:
    - Attached `action_w` to column `4` via `setCellWidget()` and called `ensurePolished()` on each action button and wrapper before reading `sizeHint()` / enforcing `setMinimumWidth()`, eliminating the 2px live-stylesheet measurement drift (`63 < 65`).
  - **Test Isolation (`diagnostic_editor_tests.py`)**:
    - Patched `QSettings` around the disabled-fades `Story(...)` check in `_test_story_duration_visibility_and_header_aggregation` so real user Preferences never trigger a false failure.

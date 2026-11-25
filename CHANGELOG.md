# Changelog

## v3.10.12-beta
- **Milestone 3.4: Modular Diagnostic Test Suites & Installer Packaging Decomposition (`diagnostics/*.py`, `diagnostic_helpers.py`, `diagnostic_selector.py`, `diagnostic_export_tests.py`, `diagnostic_cloud_and_system_tests.py`, `diagnostic_batch_tests.py`, `diagnostic_editor_tests.py`, `installer/build_tools/*.py`, `build_installer.py`, `scripts/modular_audit.py`, `scripts/dev_check.py`)**:
  - **Modular `diagnostics/` Package (`diagnostics/*.py`, `diagnostic_helpers.py`, `diagnostic_selector.py`)**:
    - Decomposed `diagnostic_export_tests.py` (2,314 lines), `diagnostic_cloud_and_system_tests.py` (1,409 lines), `diagnostic_batch_tests.py` (1,076 lines), and `diagnostic_editor_tests.py` (1,005 lines) into 11 cohesive `<650`-line submodules under `diagnostics/` while turning the 4 original modules into minimal backward-compatible facades.
    - Added shared `PROJECT_ROOT` to `diagnostic_helpers.py`, updated `diagnostic_selector.py` to map `diagnostics/*.py` edits cleanly in smart change selection, and updated `_test_in_app_user_guides_and_documentation_viewer` and `_test_source_file_modularity_and_1000_line_budget_invariant` for the modular layout.
  - **Modular `installer/build_tools/` Package (`installer/build_tools/*.py`, `build_installer.py`)**:
    - Extracted `config.py`, `env_checks.py`, and `packaging.py` from `build_installer.py` (1,099 → ~375 lines), preserving all CLI entrypoints, PyInstaller worker exclusion flags, docs copytree steps, and backward-compatible wrapper functions.
  - **Audit & Stub Cleanup (`scripts/modular_audit.py`, `scripts/dev_check.py`)**:
    - Removed all 5 newly modularized files from `GRANDFATHERED_LEGACY_MODULES` / `GRANDFATHERED`, pruned unused imports across extracted modules, and removed now-unneeded `build_installer.pyi` and `diagnostic_editor_tests.pyi` stubs (`15 -> 10` >1,000-line modules repo-wide).
  - **GUI Diagnostic Bench Main-Thread Qt Dispatch Fix (`diagnostic_dialog.py`, `test_runner.py`, `diagnostic_selector.py`, `diagnostics/cloud_storage_tests.py`)**:
    - Extracted shared `DiagnosticEngine.resolve_test_method_name()` in `test_runner.py` (used by both `diagnostic_selector.py` and `diagnostic_dialog.py`).
    - Updated `TestRunnerWorker` in `diagnostic_dialog.py` so every Qt GUI diagnostic test (frozen allowlist + `inspect.getsource` marker scan) dispatches via `BlockingQueuedConnection` to the Qt main thread, preventing `QObject::setParent` cross-thread crashes when `Plugin Interface Sandbox Testing` runs `check_for_plugin_updates()`, and patched `QProgressDialog.forceShow()` in `diagnostics/cloud_storage_tests.py`.

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

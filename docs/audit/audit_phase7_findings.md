# Code Audit Findings  Phase 7: Repo-wide Cleanup & File Decomposition

> **Scope**: Repository-wide line count analysis (`scripts/modular_audit.py`), dead code eradication, duplicate assets, packaging configuration (`build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`), and roadmap maintenance compliance.  
> **Date**: October 2026  
> **Target Version**: `v3.9.45-beta`  
> **Status**: Master checklist for future point releases (`- [ ]` = actionable fix).

---

## Executive Summary of Findings

| ID | Severity | Scope | Category | Description | Suggested Fix Effort |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **P7-01** | `CRITICAL` | Repo-wide (16 files) | Architecture / Modularity | 16 modules exceed the 1,000-line hard ceiling (14 others approaching) | `L` (Multi-stage) |
| **P7-02** | `HIGH` | Root files | Dead Code Eradication | 3,085 lines across 4 orphaned duplicate files in repository root | `S` (< 15 mins) |
| **P7-03** | `HIGH` | Root build assets | Asset & Config Hygiene | Stale root `.iss`, duplicate `requirements-build.txt`, and dead Vite config files | `S` (< 15 mins) |
| **P7-04** | `HIGH` | `roadmap.txt` | Policy Violation | `roadmap.txt` violates $N-1$ sliding window policy, ballooning to 78KB | `S` (< 30 mins) |
| **P7-05** | `MEDIUM` | `build_installer.py:839-846` | Packaging Integrity | Missing `--hidden-import` for `export.audio` and `export.timeline` | `S` (< 15 mins) |
| **P7-06** | `MEDIUM` | `CHANGELOG.md` | Context & Asset Hygiene | `CHANGELOG.md` ballooned to 165KB; older entries should move to `CHANGELOG_ARCHIVE.md` | `S` (< 30 mins) |
| **P7-07** | `LOW` | Root scripts | Maintenance Hygiene | Unverified shell and batch scripts (`build_linux.sh`, `build_macos.sh`, `Run_RadioTVSegmenter.bat`) | `S` (< 15 mins) |

---

## Detailed Findings & Actionable Fix Checklists

### P7-01: [CRITICAL] 16 Monolithic Modules Exceed 1,000-Line Ceiling (Section 10 Violation)
- [ ] **Problem**: A full AST audit via `python scripts/modular_audit.py --audit` flags 16 files exceeding the 1,000-line hard ceiling:
  1. [`plugins/wordpress/client.py`](file:///d:/rtvs3/plugins/wordpress/client.py): **1,867 lines** (Largest in repo; monolithic API client, XML-RPC, REST, Castos, Podbean)
  2. [`media_batch.py`](file:///d:/rtvs3/media_batch.py): **1,836 lines** (Batch worker, queue UI, threading, document conversion, status reporting)
  3. [`diagnostic_export_tests.py`](file:///d:/rtvs3/diagnostic_export_tests.py): **1,682 lines** (Monolithic test suite)
  4. [`prs_shared.py`](file:///d:/rtvs3/prs_shared.py): **1,491 lines** (Omnibus shared definitions, widgets, color palettes, time formatters)
  5. [`export/dialog.py`](file:///d:/rtvs3/export/dialog.py): **1,447 lines** (Export UI, destination layout, theme stylesheets, format checkboxes)
  6. [`updater.py`](file:///d:/rtvs3/updater.py): **1,418 lines** (Release checker, GitHub API, detached updater, hash verification)
  7. [`timeline_canvas.py`](file:///d:/rtvs3/timeline_canvas.py): **1,344 lines** (*Orphaned dead code; see P7-02*)
  8. [`diagnostic_cloud_and_system_tests.py`](file:///d:/rtvs3/diagnostic_cloud_and_system_tests.py): **1,267 lines** (Monolithic test suite)
  9. [`processing.py`](file:///d:/rtvs3/processing.py): **1,150 lines** (Audio processing, VAD, normalization, whisper inference wrapper)
  10. [`preferences_tabs.py`](file:///d:/rtvs3/preferences_tabs.py): **1,142 lines** (*Orphaned dead code; see P7-02*)
  11. [`build_installer.py`](file:///d:/rtvs3/build_installer.py): **1,077 lines** (PyInstaller flags, uv bundler, Inno Setup sync, packaging)
  12. [`diagnostic_batch_tests.py`](file:///d:/rtvs3/diagnostic_batch_tests.py): **1,067 lines** (Monolithic test suite)
  13. [`runtime_manager.py`](file:///d:/rtvs3/runtime_manager.py): **1,037 lines** (Environment detection, uv execution, dependency checking)
  14. [`ui_layout.py`](file:///d:/rtvs3/ui_layout.py): **1,035 lines** (Main window UI assembly, excerpt handlers, font scaling)
  15. [`background_workers.py`](file:///d:/rtvs3/background_workers.py): **1,015 lines** (Transcription, diarization, model loading QThreads)
  16. [`voice_profile_dialog.py`](file:///d:/rtvs3/voice_profile_dialog.py): **1,006 lines** (Voice profile UI, table, player, recorder, waveform)

  *Files approaching the ceiling (801–1,000 lines)*:
  - `export_story_pipeline.py` (998), `plugins/wordpress/wp_tab_widget.py` (995), `timeline_widgets.py` (971), `project_lifecycle.py` (970), `model_management.py` (966), `benchmark_engine.py` (903), `worker_diarization_engine.py` (902), `plugins/wordpress/plugin.py` (897), `translation.py` (896), `plugins/wordpress/wordpress_dialog.py` (886), `transcript_editor.py` (862), `transcript_story.py` (847), `worker_asr_engines.py` (839), `shortcuts/schema.py` (834).
- [ ] **Impact**: Violates Section 10 ("Python files SHOULD be kept under 800 lines of code and MUST NOT exceed 1,000 lines"). Monolithic files cause high token consumption, cognitive overload, and merge conflicts.
- [ ] **Decomposition Blueprint**:
  - **Stage 1 (Immediate Dead Code Elimination)**: Delete `timeline_canvas.py` (-1,344 lines) and `preferences_tabs.py` (-1,142 lines). Immediately resolves 2 of the 16 violations.
  - **Stage 2 (Batch & Processing)**: Decompose `media_batch.py` into `batch/queue.py`, `batch/worker.py`, `batch/reporting.py`. Decompose `processing.py` into `processing/vad.py`, `processing/audio.py`, `processing/inference.py`.
  - **Stage 3 (Export & UI)**: Decompose `export/dialog.py` into `export/dialog_local.py`, `export/dialog_timeline.py`, `export/dialog_styles.py`. Decompose `ui_layout.py` into `ui/layout_builder.py`, `ui/story_panel_ops.py`.
  - **Stage 4 (WordPress & Network)**: Decompose `plugins/wordpress/client.py` into `client_base.py`, `client_posts.py`, `client_media.py`, `client_podcasts.py`.
  - **Stage 5 (Diagnostic Test Suites)**: Split monolithic test files into focused feature fixtures.
- [ ] **Effort**: `L` (Planned across point releases).

---

### P7-02: [HIGH] 3,085 Lines of Orphaned Dead Code in Repository Root [COMPLETED in v3.9.46-beta]
- [x] **Status**: Permanently deleted `timeline_canvas.py` (1,344 lines), `preferences_tabs.py` (1,142 lines), `voice_profile_matcher_mixin.py` (548 lines), and `timeline_envelope.py` (51 lines).
- [x] **Impact Resolved**: Removed 3,085 lines of dead weight, reducing modules >1,000 lines from 16 to 14.

---

### P7-03: [HIGH] Stale Root Assets, Duplicate Build Files & Dead Vite Scaffold Artifacts [COMPLETED in v3.9.46-beta]
- [x] **Status**: Permanently deleted stale root Inno Setup script `RadioTVStorySegmenter.iss` and dead Vite/React scaffold configuration files (`vite.config.ts`, `eslint.config.js`, `tailwind.config.js`, `postcss.config.js`, `tsconfig.json`).

---

### P7-04: [HIGH] `roadmap.txt` Violates $N-1$ Sliding-Window Policy [COMPLETED in v3.9.46-beta]
- [x] **Status**: Pruned all historical releases older than $N-1$ (`v3.9.45-beta`), reducing `roadmap.txt` from 78KB down to strict $N-1$ compliance and passing `roadmap_manager.py --check`.

---

### P7-05: [MEDIUM] `build_installer.py:839-846` Missing Hidden-Imports for Export Submodules [COMPLETED in v3.9.46-beta]
- [x] **Status**: Added `--hidden-import export.audio` and `--hidden-import export.timeline` to `build_installer.py` packaging flags.

---

### P7-06: [MEDIUM] `CHANGELOG.md` Context Ballooning (165KB)
- [ ] **Problem**: `CHANGELOG.md` is 164,629 bytes long and contains dozens of old release notes. While `CHANGELOG_ARCHIVE.md` exists (288KB), past releases have accumulated in `CHANGELOG.md` without periodic archiving.
- [ ] **Impact**: Increases file read tokens and repository size.
- [ ] **Fix**: Archive releases prior to `v3.8.0` from `CHANGELOG.md` into `CHANGELOG_ARCHIVE.md`.
- [ ] **Effort**: `S` (< 30 mins).

---

### P7-07: [LOW] Unverified Shell and Batch Scripts in Root
- [ ] **Problem**: Root directory contains auxiliary shell scripts:
  - `build_linux.sh`
  - `build_macos.sh`
  - `Run_RadioTVSegmenter.bat`
  These scripts reference legacy paths and are not covered by automated test runner validation.
- [ ] **Impact**: Minor developer maintenance friction.
- [ ] **Fix**: Audit arguments and paths in Linux/macOS build scripts or move ephemeral test scripts into `.archive/scripts/`.
- [ ] **Effort**: `S` (< 15 mins).

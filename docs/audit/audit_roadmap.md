# Code Audit Roadmap — Radio & TV Story Segmenter (v3.9.45-beta baseline)

Each phase is report-only. Every finding points to an exact file and line, quotes proving code, and provides a structured checklist for release planning.

## Audit Lenses (applied across all phases)

| # | Lens | What it covers |
|---|------|----------------|
| L1 | **Bugs** | Logic errors, broken call chains, mismatched data shapes, unhandled None, signal/slot wiring |
| L2 | **Orphaned / dead code** | Unused imports, functions, settings keys, assets; duplicated logic |
| L3 | **Vulnerabilities** | Path traversal, shell injection, credential handling, unverified downloads |
| L4 | **Performance** | GUI-thread blocking, unbounded memory, redundant redraws/IO |
| L5 | **Confusing UI** | Unclear labels, missing feedback/progress, inconsistent behavior, dead-end dialogs |
| L6 | **Outdated docs** | README, ARCHITECTURE.md, docstrings, `.pyi` stubs, F1 help vs. actual behavior |
| L7 | *Error handling & messaging* | Silent `except` blocks; errors users can't act on |
| L8 | *Data integrity & compatibility* | Atomic writes, older project files and settings still loading |
| L9 | *Resource leaks* | File handles, temp files, cache growth on disk, threads/timers not cleaned up |
| L10 | *Logging & privacy* | Tokens/paths/transcript content leaking into logs or diagnostic exports |
| L11 | *Test coverage gaps* | Critical paths in this phase with no diagnostic test |
| L12 | *Dependency & packaging health* | Outdated or vulnerable pinned packages, licenses, installer contents |

---

## Audit Phases & Artifact Index

- [x] **Phase 1: Project persistence and batch processing**  
  *Artifact*: [`audit_phase1_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase1_findings.md)  
  *Scope*: `project_lifecycle.py`, `prs_shared.py`, `project_state_mixin.py`, `media_batch.py`  
  *Findings*: **12 items** (2 Critical, 4 High, 4 Medium, 2 Low).

- [x] **Phase 2: Updater and installer security**  
  *Artifact*: [`audit_phase2_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase2_findings.md)  
  *Scope*: `updater.py`, `build_installer.py`, `installer/Windows/RadioTVStorySegmenter.iss`, `core_utils.py`  
  *Findings*: **10 items** (2 Critical, 2 High, 4 Medium, 2 Low).

- [x] **Phase 3: Threading and worker lifecycle**  
  *Artifact*: [`audit_phase3_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase3_findings.md)  
  *Scope*: `background_workers.py`, `timeline_canvas.py`, `timeline_widgets.py`, `RadioTVSegmenter.py`  
  *Findings*: **9 items** (1 Critical, 3 High, 3 Medium, 2 Low).

- [x] **Phase 4: Recently added features**  
  *Artifact*: [`audit_phase4_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase4_findings.md)  
  *Scope*: Speaker renaming, sample preview, shortcuts (79 actions), `voice_profile_dialog.py`  
  *Findings*: **7 items** (2 Critical, 2 High, 1 Medium, 2 Low).

- [x] **Phase 5: Plugins and credentials**  
  *Artifact*: [`audit_phase5_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase5_findings.md)  
  *Scope*: `plugins/wordpress/*`, `story_metadata_dialog.py`, `plugins/manager.py`, `plugins/youtube/*`  
  *Findings*: **8 items** (2 Critical, 3 High, 2 Medium, 1 Low).

- [x] **Phase 6: Export pipeline and remaining UI**  
  *Artifact*: [`audit_phase6_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase6_findings.md)  
  *Scope*: `export/dialog.py`, `export_story_pipeline.py`, `export/*.py`, `preferences_tabs.py`, `ui_layout.py`  
  *Findings*: **10 items** (2 Critical, 3 High, 3 Medium, 2 Low).

- [x] **Phase 7: Repo-wide cleanup and file-size decomposition**  
  *Artifact*: [`audit_phase7_findings.md`](file:///C:/Users/moonl/.gemini/antigravity/brain/67b49e6d-5746-4a09-8b3b-ba097d6b7d6b/audit_phase7_findings.md)  
  *Scope*: `scripts/modular_audit.py`, monolithic files >1000 lines, dead code sweep, packaging config, `roadmap.txt`  
  *Findings*: **7 items** (1 Critical, 3 High, 2 Medium, 1 Low).

---

## Master Severity Summary Across All 7 Phases

| Severity | Count | Primary Focus |
| :--- | :---: | :--- |
| **CRITICAL** | **12** | Batch data clobbering, unverified binary execution, force-kill unsaved edits, WordPress import crash, redirect credential leakage, FFmpeg pipe deadlock, shortcut blank schema, excerpt crash |
| **HIGH** | **20** | Stale worker overwrite, modal error dialogs halting queues, architectural plugin imports from core, silent mock releases, orphaned duplicate modules (3,085 lines), monolithic files |
| **MEDIUM** | **19** | Traversal filters, SSL verify fallbacks, Inno setup broad delete, monolithic constructors, PDF font wrap approximations, undo bypass on excerpt edits, missing hidden imports |
| **LOW** | **12** | Unused attributes, fallback tuple list gaps, unreferenced scripts |
| **TOTAL** | **63** | Actionable checklist items ready for phased point release scheduling |


---

## Phased Remediation Sequence & Release Plan

### Phase 1: Release `v3.9.46-beta` — Codebase De-Bloat & Orphaned Code Eradication [COMPLETED]
*Focus: Zero-risk elimination of 3,085 lines of dead duplicate files before modifying active business logic.*
- [x] **P7-02**: Permanently delete `timeline_canvas.py` (1,344 lines) and `timeline_envelope.py` (51 lines).
- [x] **P7-02**: Permanently delete `preferences_tabs.py` (1,142 lines).
- [x] **P7-02**: Permanently delete `voice_profile_matcher_mixin.py` (548 lines).
- [x] **P7-03**: Remove stale root `RadioTVStorySegmenter.iss` and dead Vite/React scaffold configuration files.
- [x] **P7-05**: Add `--hidden-import export.audio` and `--hidden-import export.timeline` to `build_installer.py`.

### Phase 2: Release `v3.9.47-beta` — Active Danger Zone: Data Loss, Security & Instant Crashes [COMPLETED]
*Focus: Critical failure modes that corrupt data, leak credentials, freeze operations, or crash.*
- [x] **P1-01**: Batch queue zero-byte overwrite protection when `skip_existing` is enabled (`media_batch.py`).
- [x] **P2-01**: Enforce SHA-256 installer checksum validation in `updater.py`.
- [x] **P2-02**: Prompt and guard `project_dirty` before restart termination in `updater.py`.
- [x] **P5-01**: Dynamic import resilience for WordPress tab in `story_metadata_dialog.py`.
- [x] **P5-02**: Strip HTTP Basic Auth on cross-domain redirects in `plugins/wordpress/client.py`.
- [x] **P6-01**: Fix `ui_layout.py` excerpt generation dictionary key iteration crash.
- [x] **P6-02**: Eliminate FFmpeg OS pipe buffer deadlock on long exports (`export/audio.py`).
- [x] **P1-02**: Suppress modal "Save Project As" dialog on Ctrl+Z for unsaved new projects (`project_state_mixin.py`).

### Phase 3: Release `v3.9.48-beta` — Concurrency, Batch Reliability & Export Fidelity
*Focus: High-severity operational defects that freeze queues or corrupt timeline exports.*
- [ ] **P1-03**: Stale worker overwrite guard checking `self.audio_file` before committing state.
- [ ] **P1-04**: Non-modal batch error logging to prevent overnight queue halts.
- [ ] **P3-02 & P3-04**: Thumbnail worker QThread teardown and Translate action re-entrancy button guards.
- [ ] **P6-04**: Unify DAW export format matrix across Local Disk and Timeline destinations.
- [ ] **P6-05**: Correct Samplitude EDL destination timecode calculations for excluded unselected audio.

### Phase 4: Release `v3.9.49-beta` — Keyboard Usability, Debounced I/O & Plugin Isolation
*Focus: Shortcut restoration, responsive UI during speaker labeling, and architectural boundaries.*
- [ ] **P4-01**: Wire `attr_name` bindings for all 24 schema actions in `shortcuts/schema.py`.
- [ ] **P4-02**: Un-hardcode Spacebar play/pause to respect user shortcut preferences.
- [ ] **P4-04**: Debounce full-project gzip writes during inline speaker renaming in `speaker_dialogs.py`.
- [ ] **P6-08**: Commit undo state snapshots before mutating story excerpts in `ui_layout.py`.
- [ ] **P5-03**: Decouple direct `plugins/` imports from core modules (`export/dialog.py`, `model_management.py`).

### Deferred Milestone: Monolithic File Decomposition & Lower-Priority Refinements
*Focus: Code health and cosmetic polish saved for future release cycles once active defects are resolved.*
- [ ] **P7-01**: AST-driven decomposition of 9 core monoliths exceeding 1,000 lines.
- [ ] **P6-06**: Remove unrequested emoji symbols and decorative checkmarks from buttons and comboboxes.
- [ ] **P6-07**: Refine Helvetica proportional font word-wrap measurements in `export/pdf.py`.
- [ ] **P6-09 & P6-10**: Clean orphaned temp preview set and restore `"timeline"` to fallback reorder list.
- [ ] **P7-06**: Prune older changelog entries into `CHANGELOG_ARCHIVE.md`.

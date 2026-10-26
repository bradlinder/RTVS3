# AI Studio Project Instructions

## 1. App Purpose & Web Preview Directive (CRITICAL RECOVERY DIRECTIVE)
- **What the AI Studio Preview MUST Display**: 
  The AI Studio web preview for this project MUST always display the **interactive changelog and release history viewer** powered by `/src/App.tsx` and synchronized with `CHANGELOG.md`.
- **STRICT PROHIBITION (Never Replace)**:
  Under NO circumstances should an agent rewrite, scaffold over, or replace `/src/App.tsx` or `/index.html` with:
  - Dummy/mock audio waveform players or simulated transcription editors
  - Promotional SaaS landing pages, "Hero" headers, or feature pitch marketing cards
  - Standalone single-purpose demo widgets or test audio uploaders
- **Why this exists**:
  The actual application is a native Python/PySide6 (Qt) desktop software suite. The Node/Vite web container in AI Studio exists exclusively to serve the live interactive changelog, release documentation, and version inspector on port 3000.
- **Recovery / Error Response & Zero-Token Restoration**:
  If the web preview breaks, fails linting, reports build errors, or if preview files are missing after a git update/pull (since web preview files are ignored in `.gitignore` to keep the desktop repository focused on the Python app):
  - **NEVER** rewrite, scaffold over, or regenerate the UI from scratch (which wastes tokens and risks hallucination).
  - Run `python preview_manager.py` (or `python preview_manager.py --restore`) to immediately restore all preview files in < 0.1s.
- **Changelog Synchronization**:
  `/src/App.tsx` imports `CHANGELOG.md` directly (`import CHANGELOG_MARKDOWN from '../CHANGELOG.md?raw'`). Whenever `CHANGELOG.md` is updated, the changes are automatically reflected in the web preview without needing to duplicate markdown strings in React code. Use `python preview_manager.py --sync` to align version numbers across preview files.

## 2. Standardized Version Bump Checklist
- **Incremental Point Release Policy**:
  - Incrementally update the version number with a point release (e.g., `v2.9.5` -> `v2.9.6`, `v2.9.7`, `v2.10.1`) whenever you make an update, bug fix, or feature enhancement to the core app, unless the user explicitly specifies a different version number to apply.
  - Always format version strings strictly as standard semantic numbers with single period delimiters (e.g. `2.9.6`, `2.9.7`, `2.10.1`). Never introduce double dots (e.g. `2.9..6`).
  - Execute the full version bump checklist below synchronously with every update.

When bumping or updating the application version number, you MUST update **ALL** of the following locations synchronously:
1. `prs_shared.py` (`PROJECT_VERSION`)
2. `updater.py` (`PROJECT_VERSION` fallback)
3. `build_installer.py` (`PROJECT_VERSION` fallback)
4. `installer/Windows/RadioTVStorySegmenter.iss` (`#define MyAppVersion`)
5. `plugins/*/manifest.json` (Selective / Lazy Catch-Up Policy):
   - **No Changes, No Bump**: If no code, schema, dependency, or asset changes are made to a specific plugin during a release cycle, DO NOT bump that plugin's `version` in `manifest.json`. It is completely expected and supported for a user running e.g. v3.2.20 of the application to run v3.2.15 of the YouTube plugin.
   - **Catch-Up Synchronization on Modification**: The next time a change *does* affect a plugin, its `version` field in `manifest.json` MUST be brought up to date to match the current application `PROJECT_VERSION` being released.
6. `transcript_story.py` (docstring version header)
7. `package.json`, `metadata.json`, and `index.html` (title & meta tags)
8. `CHANGELOG.md` & `/src/App.tsx` (version notes and expanded accordion defaults)
9. `roadmap.txt & CHANGELOG.md (N-1 Sliding-Window & Real-Time Sync Policy)`:
   - Whenever any code change, bug fix, packaging adjustment, or feature refinement is made during a release cycle, it MUST be recorded immediately in the current release section of `roadmap.txt` and `CHANGELOG.md` (even if it occurs after the initial version number bump).
   - Retain only the active release ($N$) and its immediate predecessor ($N-1$); prune any versions older than $N-1$ from `roadmap.txt`.
10. `Roadmap Item Status Tracking Policy (Social Digest Progress Indicator Style)`:
   - `roadmap.txt` milestones and feature items MUST be annotated with explicit progress checkboxes and status notations:
     * `[x]` for completed items / releases (e.g. `[x] 1.1 Feature Title` or `(Completed in vX.X)`)
     * `[-]` for in-progress items (e.g. `[-] 3.1 Feature Title`)
     * `[ ]` for planned / not started items (e.g. `[ ] 3.2 Feature Title` or `[NOT STARTED]`)
   - When work starts on an item in the roadmap, mark it immediately as in-progress (`[-]`).
   - Mark an item as completed (`[x]`) when implementation is finalized, or ask the user if it's time to mark an item as completed, or infer based on whether development has moved on to another part of the roadmap.

## 3. Pre-Completion Verification
Before completing code modifications:
- Run Python syntax compilation checks: `python -m py_compile RadioTVSegmenter.py prs_shared.py processing.py runtime_manager.py radio_tv_story_segmenter_worker.py updater.py build_installer.py plugins/manager.py`
- Run the web preview linter and build tools (`lint_applet` & `compile_applet`) to ensure zero regressions.
- **Three-Tier Diagnostic Verification Discipline**:
  Never execute the full 68-test suite (`python test_runner.py --all`) during routine turn-by-turn development. Adhere strictly to the three-tier hierarchy:
  1. **Tier 1 (Targeted Feature/Bug Test)**: When implementing or modifying a specific feature or bug fix, run only the relevant test by keyword:
     `python test_runner.py --quiet --filter "<keyword>"` (e.g. `--filter "Quick Sample"` or `--filter "Speaker"`). Completes in ~0.1–1s.
  2. **Tier 2 (Smart Change-Aware Test)**: When verifying multi-file localized changes across modules before committing:
     `python test_runner.py --quiet` (or `python test_runner.py --quiet --changed`). Auto-detects modified modules via git status and executes only related tests in ~1–3s.
  3. **Tier 3 (Full Diagnostic Suite)**: Reserved strictly for comprehensive release audits, final packaging, or when explicitly requested by the user:
     `python test_runner.py --quiet --all`.

## 4. Architectural Invariants Reference
Always adhere strictly to the invariants defined in `ARCHITECTURE.md`:
- Core modules must NEVER import from `plugins/`.
- Heavy translation runtimes must remain isolated inside `plugins/translation/`.
- Speaker diarization uses `wespeakerruntime` as the primary ONNX embedding engine.

## 5. Release Snapshots & Rollback Directive
- **Snapshot Manager (`snapshot_manager.py`)**:
  - The project maintains an automated snapshot and rollback manager in `snapshot_manager.py`.
  - Snapshots are preserved as standalone archives in `.snapshots/<name>.tar.gz` and cataloged in `.snapshots/manifest.json`.
  - A local Git repository with tags (e.g. `v2.9.6-stable`, `latest-stable`) and branch `stable` provides dual redundancy.
- **How to Revert to Stable Release**:
  - If the user asks to revert to the latest stable release (or a specific stable snapshot):
    Run `python snapshot_manager.py --restore stable` (or `python snapshot_manager.py --restore v2.9.6-stable`).
    Then run `python preview_manager.py --sync` and verify with `lint_applet` & `compile_applet`.
  - To create a new stable snapshot: `python snapshot_manager.py --create <name> --stable`.

## 6. Verified Stable Release Policy
- **User-Tested & Verified Stable Builds (`verified-stable`)**:
  - Whenever the user asks to mark a build or release as stable, the agent MUST explicitly ask: *"Would you like to mark this as 'verified-stable' to set it apart from automatic designations?"*
  - Ensure manually user-tested stable builds are explicitly tagged and recorded as `verified-stable` in snapshot metadata (`snapshot_manager.py`).

## 7. UI Design Discipline: Strict Prohibition on Unrequested Icons / Emojis
- **No Unrequested Icons or Emojis**:
  Do NOT add icons or emoji symbols (such as folders, clouds, disks, checkmarks, warning signs, labels, or decorative unicode glyphs) to tabs, buttons, dialog titles, menus, table headers, group boxes, or cards unless explicitly requested by the user. Maintain clean, professional, native desktop typography without decorative emoji clutter.

## 8. Ephemeral Scripts & Artifact Lifecycle Directive
- **Prompt for Deletion vs. Archival**:
  Whenever one-off or ephemeral scripts (such as visual mockup generators, test scratch scripts, one-time data patches, or benchmark inspectors) are created and utilized during a task, the agent MUST explicitly ask the user upon completion whether they would like to **delete** or **archive** them.
- **Archive Location & Git Exclusion (`.archive/`)**:
  - If the user chooses to archive, move the scripts into `.archive/` (e.g. `.archive/scripts/`).
  - `.archive/` is registered in `.gitignore` to prevent repository bloat, git status noise, or inclusion in frozen installer distributions.
  - The agent must know where to find archived scripts in `.archive/` if ever needed for historical context or reuse, but must safely exclude them from standard build, lint, and test runs.
- **Immediate Deletion**:
  - If the user chooses to delete, permanently remove the scripts and their temporary outputs.

## 9. Comprehensive Codebase Audit Directive
When instructed to audit the codebase (e.g. "audit the code", "run a code audit", "check for bloat/security/performance", "audit the full app"), the agent MUST NOT rely solely on running pre-existing diagnostic unit test suites (`test_runner.py`). Pre-existing unit tests only test what was previously conceived and often test isolated model components rather than full UI wiring.

Instead, the agent MUST actively perform deep, adversarial code-level inspection across the actual execution paths, UI plumbing, data structures, and lifecycle handlers covering ALL of the following pillars:

1. **Functional Operability Verification (Does Every Feature Actually Work as Expected?)**:
   - **Feature-by-Feature Execution Tracing**: Walk the actual call stack for every major app feature (transcription, diarization, translation, story segmentation, timeline scrub/zoom, audio playback/speed, ID3 tagging, batch processing, and each export format: TXT, DOCX, PDF, REAPER RPP, EDL, XML, AAF, Google Docs, Sheets, YouTube, WordPress). Confirm there are no broken imports, missing methods on target objects, unhandled None types, or disconnected callbacks that would prevent the feature from completing successfully.
   - **Data Shape & Contract Verification**: Inspect caller/callee boundaries between UI dialogs, background workers, and business logic. Ensure objects, dictionary keys, and return types match actual function signatures (e.g., verifying whether a function returns `[(idx, vector)]` vs `[{"vector": ...}]` or dict vs tuple).
   - **Silent Exception Swallowing**: Audit `try: ... except:` blocks in newly added or modified methods. Ensure that broad `except Exception:` blocks do not silently mask `AttributeError`, `TypeError`, or logic failures during critical user operations (such as saving voice profiles, applying edits, or exporting files).
   - **Undo/Redo State Mutation Integrity**: Inspect every function that mutates project state (segments, transcript words, speakers, overrides, stories, or timeline markers). Verify that `_commit_project_state_change()` or `undo_stack.push()` is explicitly called before mutation, and that `render_transcript()` / `save_project()` / `update_window_title()` are triggered.
   - **UI Action & Callback End-to-End Tracing**: Verify that every dialog button, checkbox, and context-menu action is properly connected to a live handler, that argument names in method calls match the signature, and that methods invoked on `self.main_win` or `self.parent()` actually exist and behave as expected.

2. **Edge-Case Robustness & Desktop Environmental Traps**:
   - **Cross-Platform Filesystem & Path Traps**:
     * Case sensitivity: Ensure extensions (`.lower().endswith(...)`) and path comparisons handle uppercase extensions (`.MP3`, `.WAV`) on Linux.
     * Cross-drive paths on Windows: Ensure `os.path.relpath()` across different mount drives (e.g., `D:\` media vs `C:\` project) is wrapped in `try: ... except ValueError:` to prevent crashes.
     * Non-ASCII & Unicode paths: Verify file open routines and subprocess argument vectors handle paths with spaces, apostrophes, ampersands, or Unicode characters.
   - **Media Duration & Asynchrony Traps**:
     * Zero-duration and VBR MP3 guards: Ensure duration math guards against zero (`dur = max(0.001, float(duration))`) to prevent `ZeroDivisionError` or `NaN` timeline coordinates.
     * Stale worker signal completion: Verify background worker callbacks check whether the active project/media has changed before mutating state (`if self.audio_file != worker.source_audio: return`).
     * Re-entrancy guards: Ensure long-running action triggers disable their buttons during processing to prevent rapid double-click race conditions.
   - **Display & High-DPI Traps**:
     * Geometry restoration: Ensure saved window/dialog coordinates in `QSettings` validate against available screen geometry (`QGuiApplication.screens()`) so windows never restore off-screen when monitors are disconnected.

3. **Security & Data Safety**:
   - Path traversal guards (`Path.resolve()`, `os.path.commonpath`) on all file imports, project loads, and archive extractions (`.zip`, `.tar.gz`).
   - Shell injection avoidance (safe `subprocess.run` with list arguments, `shell=False`, and `CREATE_NO_WINDOW` flags on Windows).
   - Credential & OAuth token hygiene (client-side only, no hardcoded secrets or leaked keys).
   - Atomic disk writes (`safe_replace` / `.tmp` rename with `flush()` and `os.fsync()`) for all projects, audio caches, and settings.

4. **Performance & Resource Usage**:
   - Memory efficiency on multi-hour media (bounded peak envelopes, chunked audio decoding, streaming FFmpeg pipes).
   - Viewport-scaled LOD rendering (mipmapped waveform pyramids, bounded redraws, dirty canvas pixmaps).
   - Responsive worker threading (dedicated background QThreads/subprocesses; no heavy compute or file I/O blocking the Qt main GUI loop).

5. **Qt / PySide6 Stability & Reliability**:
   - Thread affinity: No background workers directly touching GUI widgets (signals/slots only).
   - Object parentage & lifecycle: Proper widget hierarchy to prevent memory leaks and `Internal C++ object already deleted` crashes.
   - Clean timer and worker termination: `QTimer.stop()` and worker `.cancel()` / `.kill()` handlers on close events.

6. **Code Bloat, Dead Code & Asset Hygiene**:
   - Identification of unused imports, orphaned functions/classes, and dead legacy code.
   - Elimination of redundant or duplicated business logic across modules.
   - Asset auditing: Ensure unreferenced icons, test media, or scratch scripts are not packaged into distribution builds (`build_installer.py`, `.iss`).

7. **Architectural Invariants & Packaging**:
   - Strict module boundaries: Core modules (`RadioTVSegmenter.py`, `processing.py`, `ui_layout.py`) must NEVER import from `plugins/`.
   - Heavy AI/translation runtimes isolated to background worker subroutines.
   - Installer exclusion compliance: `.archive/`, `.snapshots/`, `.git/`, and dev tests excluded from PyInstaller and Inno Setup bundles.
   - Version coherence: Synchronous alignment across all 10 project locations with valid $N-1$ sliding-window roadmap tracking.

## 10. Modular Architecture & Monolithic File Size Discipline Directive
- **File Length Target Thresholds**:
  - Python files SHOULD be kept under **800 lines** of code and MUST NOT exceed **1,000 lines**.
  - Any file approaching or exceeding 1,000 lines is flagged for modular decomposition into a dedicated sub-package.
- **Prefer Submodule Creation Over Code Appending**:
  - When implementing new feature logic, UI dialogs, processing engines, or export formats, **create dedicated submodules** in appropriate sub-packages (e.g. `export/formats/`, `processing/engine/`, `ui/dialogs/`) and import them, rather than appending code to existing large files.
- **Zero-Breakage Facade Pattern Re-exports**:
  - When decomposing a monolithic file into submodules, preserve the original module filename as a lightweight facade that imports and re-exports public classes/functions (`from .submodule import ClassName`).
  - This guarantees 100% backward compatibility for external callers, plugins, and the automated diagnostic suite (`test_runner.py`).
- **Single Responsibility Discipline**:
  - Enforce strict single-responsibility boundaries: separate UI layout construction from event handling, audio decoding from AI model execution, and data serialization from presentation logic.
- **AST Decomposition Suggester & Automated Budget Guard (`scripts/modular_audit.py`)**:
  - Run `python scripts/modular_audit.py --suggest <file>` on any file approaching 850 lines to automatically generate an AST-driven decomposition blueprint with recommended submodules, method groupings, and backward-compatible re-exports.
  - Run `python scripts/modular_audit.py --audit` to inspect repository-wide line counts, or `python scripts/modular_audit.py --budget-guard` to verify compliance.

## 11. Token-Thrifty Development & Surgical Range-Editing Directive
- **Surgical Line-Slice Reading**:
  - Do NOT read whole files into context when inspecting or making localized edits.
  - Always consult `.codemaps/INDEX.md` or run `python scripts/generate_symbol_index.py --outline <file>` to find the exact class, method, and line range, then view only that targeted range with `view_file(StartLine, EndLine)`.
- **Targeted Contiguous Replacements**:
  - Never rewrite or overwrite entire source files to apply a bug fix or feature tweak. Use `replace_file_content` with minimal, contiguous diff chunks.
- **Consult `.pyi` Typing Stubs**:
  - When verifying method signatures, argument types, or public exports of central facades (`prs_shared.py`, `processing.py`, `playback_preferences.py`, `transcript_editor.py`, `project_export.py`), inspect the corresponding `.pyi` stub to save up to 97% of prompt tokens.
- **Diagnostic & Log Output Discipline**:
  - Adhere strictly to the Three-Tier Diagnostic Verification Discipline (Section 3). Routine verification MUST use Tier 1 (`--filter <keyword>`) or Tier 2 (`--quiet` / `--changed`). Full runs (`--all`) are strictly reserved for release audits or explicit user request.
  - When verifying localized changes, run `python test_runner.py --quiet` (auto-detects changed files via `diagnostic_selector.py`) or `python test_runner.py --quiet --filter <keyword>` to execute in ~0.5–2s.
  - Always use quiet mode (`--quiet`) to collapse passing test results into a single token-dense line.
  - Use `python bump_version.py --patch` (or `python bump_version.py <version>`) to update all version locations, modified plugin manifests/addons, and web preview files in a single command rather than editing 10 files individually.
  - Pipe or pass raw terminal error traces through `scripts/log_summary.py` to extract concise <15-line root cause reports instead of outputting massive traceback noise.

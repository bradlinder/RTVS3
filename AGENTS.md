# AI Studio Project Instructions

## 1. App Purpose & Web Preview Directive (CRITICAL RECOVERY DIRECTIVE)
- **What the AI Studio Preview MUST Display**: 
  The AI Studio web preview for this project MUST always display the **zero-dependency app status & version inspector** served by `node server.js` on port 3000 and synchronized with `prs_shared.py`.
- **STRICT PROHIBITION ON VITE / REACT / NPM INSTALLS (Zero-Dependency Mandatory)**:
  Under NO circumstances should an agent install `vite`, `react`, `react-dom`, `@vitejs/plugin-react`, or run `npm install` for the web preview.
  - Do NOT create or scaffold React components (`/src/App.tsx`), `vite.config.ts`, or build pipelines.
  - The preview uses standard Node.js built-in `node:http` (`node server.js`). It requires ZERO external npm packages.
  - Do NOT rewrite or scaffold over `server.js` or `package.json` with dummy audio players or SaaS marketing pages.
- **Why this exists**:
  The actual application is a native Python/PySide6 (Qt) desktop software suite. The Node web container in AI Studio exists exclusively to serve the live version inspector card on port 3000 without requiring heavy node_modules or Vite builds.
- **Recovery / Zero-Token Restoration**:
  If preview files (`server.js`, `package.json`) are missing or corrupted:
  - **NEVER** run `npm install` or scaffold a React app.
  - Run `python preview_manager.py` (or `python preview_manager.py --restore`) to immediately restore all zero-dependency preview files in < 0.1s.

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
7. `package.json`, `metadata.json`, and `index.html` (web preview entrypoints; update version string ONLY, NEVER alter "dev": "node server.js" or install npm packages)
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
- Verify zero-dependency web preview state: `python preview_manager.py --sync` to ensure `server.js` and `package.json` are valid and synchronized.
- Run the web preview linter and build tools (`lint_applet` & `compile_applet`) to ensure zero regressions.
- **Three-Tier Diagnostic Verification Discipline**:
  Never execute the full 68-test suite (`python test_runner.py --all`) during routine turn-by-turn development. Adhere strictly to the three-tier hierarchy:
  1. **Tier 1 (Targeted Feature/Bug Test)**: When implementing or modifying a specific feature or bug fix, run only the relevant test by keyword:
     `python test_runner.py --quiet --filter "<keyword>"` (e.g. `--filter "Quick Sample"` or `--filter "Speaker"`). Completes in ~0.1–1s.
  2. **Tier 2 (Smart Change-Aware Test)**: When verifying multi-file localized changes across modules before committing:
     `python test_runner.py --quiet` (or `python test_runner.py --quiet --changed`). Auto-detects modified modules via git status and executes only related tests in ~1–3s.
  3. **Tier 3 (Full Diagnostic Suite)**: Reserved strictly for comprehensive release audits, final packaging, or when explicitly requested by the user:
     `python test_runner.py --quiet --all`.
- **Early Stop on Test Harness & Methodology Failures**:
  If a test failure is attributed to headless test environment limitations, missing mock shim primitives (e.g. in `qt_compat.py`), or test suite methodology rather than an actual application code bug, STOP execution immediately and inform the user. Explain that the application code changes are complete, detail the mock/harness limitation encountered, and ask how to proceed rather than spending tokens repeatedly iterating on test stubs.

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

## 10. Modular Architecture, Single Responsibility & File Size Discipline Directive
- **Strict Single Responsibility & Desktop Domain Separation Invariant**:
  Every Python source file MUST have a single primary architectural purpose. Incompatible desktop domains MUST NOT be co-located in the same implementation file:
  1. **UI Presentation & Interaction** (`ui/`, `*_dialog.py`, `*_widgets.py`): QWidgets, QDialogs, QMainWindow, paint events, user input, layouts. Must NEVER contain heavy compute, DSP/FFmpeg processing, direct AI model execution, or background thread run loops.
  2. **Background Worker Coordination** (`workers/`, `*_worker.py`): QThread lifecycle, progress signals, cancellation, task queues. Must NEVER directly instantiate or touch GUI widgets (signals and slots only).
  3. **Headless Processing & Engine Logic** (`processing/`, `audio/`, `engine/`): Audio/video decoding, DSP filters, VAD, transcription, diarization, translation inference, timeline math. Must be 100% headless with zero PySide6/Qt GUI dependencies.
  4. **Data Models, State & Serialization** (`models/`, `export/formats/`, `project_lifecycle.py`): Schemas, dataclasses, project serialization, undo/redo state snapshots, document export format engines (DOCX, PDF, EDL, RPP, XML). Decoupled from interactive presentation.
- **Prohibited Domain Collisions**:
  - Prohibited: Co-locating UI widgets and headless audio/processing engines in one file.
  - Prohibited: Co-locating UI dialogs and background QThread worker definitions in one file.
  - Prohibited: Co-locating UI dialogs and large data model entities in one file (>400 lines).
  - Prohibited: Co-locating worker coordination with direct heavy engine computation.
  - Prohibited: Bundling multiple distinct, complex top-level dialogs in a single file (>2 dialogs).
- **Automated Single Responsibility Audit (`scripts/modular_audit.py --check-srp`)**:
  - Run `python scripts/modular_audit.py --check-srp` to audit repository-wide domain separation.
  - Run `python scripts/modular_audit.py --check-srp <file>` to inspect domain classification and collision diagnostics for a specific module.
  - Enforced automatically in the pre-flight gate (`scripts/dev_check.py`) and CI workflows.
- **File Length Target Thresholds & Purpose Balance**:
  - While line count is a useful proxy, **file purpose and cohesion supersede raw line count**. A 300-line file mixing UI with DSP engines is an architectural violation; conversely, a cohesive, single-domain engine or grammar parser approaching 700 lines is acceptable.
  - Python files SHOULD be kept under **800 lines** of code and MUST NOT exceed **1,000 lines**.
  - Any file approaching or exceeding 1,000 lines is flagged for modular decomposition into a dedicated sub-package.
- **Prefer Submodule Creation Over Code Appending**:
  - When implementing new feature logic, UI dialogs, processing engines, or export formats, **create dedicated submodules** in appropriate sub-packages (e.g. `export/formats/`, `processing/engine/`, `ui/dialogs/`) and import them, rather than appending code to existing large files.
- **Zero-Breakage Facade Pattern Re-exports**:
  - When decomposing a monolithic file into submodules, preserve the original module filename as a lightweight facade that imports and re-exports public classes/functions (`from .submodule import ClassName`).
  - This guarantees 100% backward compatibility for external callers, plugins, and the automated diagnostic suite (`test_runner.py`).
- **Grandfathered Legacy Monoliths vs. New Modules**:
  - Existing legacy monoliths (e.g. `prs_shared.py`, `processing.py`, `ui_layout.py`) that pre-date this rule are cataloged in `GRANDFATHERED_LEGACY_MODULES` and tracked in `roadmap.txt` Section 3 for phased, risk-managed decomposition.
  - All new files and modified modules must strictly comply with the single responsibility invariant.
- **AST Decomposition Suggester & Automated Budget Guard (`scripts/modular_audit.py`)**:
  - Run `python scripts/modular_audit.py --suggest <file>` on any file approaching 850 lines to automatically generate an AST-driven decomposition blueprint with recommended submodules, method groupings, and backward-compatible re-exports.
  - Run `python scripts/modular_audit.py --audit` to inspect repository-wide line counts, or `python scripts/modular_audit.py --budget-guard` to verify line budget compliance.

## 11. Token-Thrifty Development & Surgical Range-Editing Directive
- **Automated Symbol-First Range Reads**:
  - Do NOT read whole files into context when inspecting or making localized edits.
  - Before reading or editing any file over 150 lines, always consult `.codemaps/INDEX.md` or run `python scripts/generate_symbol_index.py --outline <file>` to identify the exact class, method, and line ranges.
  - View only that targeted range with `read_file(StartLine, EndLine)`. Never ingest full modules.
- **Consult & Maintain Automated `.pyi` Typing Stubs (`scripts/generate_pyi_stubs.py`)**:
  - When verifying method signatures, argument types, or public exports of any module exceeding 800 lines (such as `prs_shared.py`, `processing.py`, `media_batch.py`, `runtime_manager.py`, `project_lifecycle.py`, `updater.py`, `export/dialog.py`), inspect the corresponding `.pyi` stub to save up to 95% of prompt tokens.
  - Run `python scripts/generate_pyi_stubs.py --all` (or `--file <path>`) whenever public interfaces or mixins are updated, and `python scripts/generate_pyi_stubs.py --check` during release audits to guarantee stub synchronization across all 28 large modules.
- **Targeted Contiguous Replacements**:
  - Never rewrite or overwrite entire source files to apply a bug fix or feature tweak. Use `edit_file` with minimal, contiguous diff chunks.
- **Research Subagent Delegation for Wide Multi-File Explorations**:
  - When conducting multi-file code exploration, broad architecture tracing, or cross-subsystem audits across 3+ modules, invoke the `research` subagent (`invoke_subagent(TypeName="research", Role="Codebase Researcher", Prompt=...)`).
  - The subagent digests thousands of raw code tokens in its isolated sandbox and returns only a concise, structured 10-to-20 line findings summary to the main conversation, keeping the parent context lean and fast.
- **Sliding-Window Changelog & Roadmap Compaction Policy**:
  - Maintain a strict sliding window in `CHANGELOG.md`: historical release notes older than the active release cycle ($N$ and $N-1$) MUST be pruned into `CHANGELOG_ARCHIVE.md`, keeping the primary changelog lean.
  - In technical audit documents, task notes, and pull requests, reference clickable file/line links (`[filename:L10-L20](file:///path#L10-L20)`) and minimal 3-to-5 line reproduction diffs rather than duplicating full multi-line functions.
- **Diagnostic & Log Output Discipline**:
  - Adhere strictly to the Three-Tier Diagnostic Verification Discipline (Section 3). Routine verification MUST use Tier 1 (`--filter <keyword>`) or Tier 2 (`--quiet` / `--changed`). Full runs (`--all`) are strictly reserved for release audits or explicit user request.
  - When verifying localized changes, run `python test_runner.py --quiet` (auto-detects changed files via `diagnostic_selector.py`) or `python test_runner.py --quiet --filter <keyword>` to execute in ~0.5–2s.
  - Always use quiet mode (`--quiet`) to collapse passing test results into a single token-dense line.
  - Use `python bump_version.py --patch` (or `python bump_version.py <version>`) to update all version locations, modified plugin manifests/addons, and web preview files in a single command rather than editing 10 files individually.
  - Pipe or pass raw terminal error traces through `scripts/log_summary.py` to extract concise <15-line root cause reports instead of outputting massive traceback noise.

## 12. Conversation Lifecycle & Context Compaction Directive
- **Periodic Compaction Rule (`/compact`)**:
  - To prevent degradation of agent attention and eliminate stale command logs, the agent MUST proactively recommend the `/compact` slash command to the user:
    1. Immediately upon completing any major roadmap milestone or complex multi-phase task.
    2. When the conversation history approaches 15–20 active turns.
    3. Before embarking on large architectural refactorings or comprehensive audits.
  - Compacting summarizes past tool runs, test outputs, and diagnostic traces while cleanly retaining active workspace state, uncommitted changes, and active roadmap targets.

## 13. Automated Task Routing, Context Scaffolding & Escalation Directive
- **Adaptive Model-Tier Routing Policy**:
  - **Local Models (Qwen 14B/32B, DeepSeek, Ollama / LM Studio)**: Strict Surgical Mode. Local models MUST run `python scripts/task_router.py "<task query>"` prior to inspecting files or making edits. Local models must adhere to targeted symbol slice reads (`StartLine`/`EndLine`) and `.pyi` stubs to prevent VRAM exhaustion, KV cache overflow, and instruction drift.
  - **Frontier Cloud Models (Gemini 1.5/2.0/3, Claude 3.5 Sonnet, GPT-4o)**: Macro-Aware Mode. Frontier models are NOT strictly bound to micro-slices; they may inspect broader module blocks or entire source files directly to comprehend system-wide call graphs, Qt event loops, and cross-cutting dependencies. However, they must still use minimal contiguous diffs (`replace_file_content`) rather than full-file rewrites to prevent token snowballing across long conversation sessions.
- **Two-Strike Escalation Protocol for Bug Fixes**:
  - **Strikes 1 & 2 (Surgical First)**: On the initial bug-fixing attempt (and second attempt if needed), use targeted slice inspection and minimal diffs.
  - **Strike 3 Escalation (Broader Search)**: If a bug fix fails diagnostic verification (Tier 1/Tier 2 test) or regressions occur on the first or second attempt, the agent MUST immediately abandon micro-slicing and escalate to broader inspection:
    1. Trace all callers and call sites across the codebase using symbol search or grep.
    2. Inspect full parent classes, signal/slot wiring, or related lifecycle modules.
    3. If 3+ modules are involved in the regression, delegate to a `research` subagent to analyze cross-cutting dependencies without polluting the primary context.
- **Stub & Symbol Index Synchronization Cadence (Zero Drift)**:
  - **Immediate (On-Change)**: Whenever modifying or adding public methods, classes, or exported interfaces in large modules (>800 lines), update the corresponding `.pyi` stub or run `python scripts/generate_pyi_stubs.py --file <path>`.
  - **Periodic Full Scan (Release / Version Bump Sync)**: During version bumps (`bump_version.py`), release audits, or snapshot creation, a full scan (`python scripts/generate_pyi_stubs.py --all` and `python scripts/generate_symbol_index.py`) runs automatically to ensure `.codemaps/symbol_index.json` and all 29 `.pyi` stubs remain 100% synchronized with zero drift.

## 14. Version Control, AI Safety & Pre-Flight Gate Directive
- **3-Tier Branching & AI Safety (`docs/VERSION_CONTROL_GUIDE.md`)**:
  - The repository maintains three primary branch levels: `stable` (production releases), `beta` (pre-release candidate testing), and `dev` (active integration).
  - All AI agents (local and cloud) MUST work exclusively in disposable task branches (`ai/<feature>` or `fix/<bug>`) branched from `dev`. Never execute AI work directly on `stable` or `main`.
  - Consult `docs/VERSION_CONTROL_GUIDE.md` for standard workflows, emergency rollbacks (`git restore .`, `git reset --hard`), and promotion procedures.
- **Reverse-Caller & Blast-Radius Tracing (`task_router.py --impact <symbol>`)**:
  - Before modifying existing functions, methods, or signatures, run `python scripts/task_router.py --impact <symbol>` to inspect all AST definitions and caller sites across the codebase in <1s.
- **One-Shot Context Bundling (`scripts/bundle_context.py <symbol>`)**:
  - Use `python scripts/bundle_context.py <symbol>` to generate a token-bounded (~1,000-1,500 token) markdown bundle containing source slice, `.pyi` typing stub, caller sites, and targeted test command for copy-pasting into local AI chats.
- **Pre-Flight Verification Gate (`scripts/dev_check.py`)**:
  - Before committing or merging any task branch into `dev`, run `python scripts/dev_check.py` to verify syntax compilation, `.pyi` stub sync, preview sync, modular budget, and Tier 2 regression tests in <10s.


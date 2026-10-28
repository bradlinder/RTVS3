# Phase 1 Code Audit Findings & Actionable Checklist
**Focus Subsystems:** Project Lifecycle & Persistence (`project_lifecycle.py`), Batch Processing (`media_batch.py`), Undo/Redo Mutation Integrity (`project_state_mixin.py`), and Auto-Save / Worker State Race Conditions.
**App Baseline:** v3.9.45-beta

---

## Executive Summary

Phase 1 audit uncovered **12 verified findings** across project persistence, undo/redo state tracking, and batch processing:
- **2 Critical Findings**: Potential data destruction when `skip_existing` is checked in batch mode, and unhandled file dialog popups on Ctrl+Z during unsaved sessions.
- **4 High Findings**: Stale worker callbacks silently overwriting newly loaded project state on disk, batch jobs halting completely on a single file failure due to modal message boxes, loss of media link upon undoing a project purge, and absence of autosave for unsaved new projects.
- **4 Medium Findings**: Spurious background waveform and thumbnail generation during unattended headless batch runs, directory batch import adding non-media/unsupported files, incomplete project metadata/notes capture in undo snapshots, and side-effect directory creation inside a path resolution helper.
- **2 Low / Hygiene Findings**: Outdated module docstring version header (`v1.1.1` in `media_batch.py`), and unrequested unicode emoji icons in UI labels.

---

## Actionable Fix Checklist

### Critical Severity

- [ ] **P1-01 [CRITICAL] `skip_existing` in Batch Processing Clobbers Existing Transcripts with Empty Files**
  - **Lens:** L1 (Bug) / L8 (Data Integrity)
  - **Location:** [`media_batch.py:486-490`](file:///d:/rtvs3/media_batch.py#L486-L490)
  - **Evidence:**
    ```python
    if all_exist:
        self.log_activity(f"[BATCH] Requested outputs exist for {base_name}. Skipping AI pipeline and generating exports directly.")
        self._batch_export_current()
        QTimer.singleShot(0, self._batch_next_media)
        return
    ```
  - **Impact / Repro:** When a user runs a batch job with "Skip existing files" (`skip_existing=True`), `all_exist` evaluates to True. However, because `load_media_file()` does not load an adjacent project (or no adjacent project exists in the source media directory), `self.transcript` is `None`. `_batch_export_current()` then calls `export_full_episode()`, which proceeds with `segments = []` and **overwrites the existing `.txt`/`.docx` files with 0-byte or header-only empty files**!
  - **Suggested Fix:** When `all_exist` is True, do NOT call `self._batch_export_current()`. Log that the file is already complete and skip immediately to `self._batch_next_media()`.
  - **Effort:** Small (S)

- [ ] **P1-02 [CRITICAL] Ctrl+Z (Undo) on Unsaved Project Triggers Synchronous "Save As" Modal File Dialog**
  - **Lens:** L1 (Bug) / L5 (Confusing UI)
  - **Location:** [`project_state_mixin.py:286`](file:///d:/rtvs3/project_state_mixin.py#L286) and [`project_lifecycle.py:477`](file:///d:/rtvs3/project_lifecycle.py#L477)
  - **Evidence:**
    In `project_state_mixin.py`:
    ```python
    self.refresh_story_list()
    self.apply_story_selection_indices(self.current_selected_story_indices, seek=False)
    self.project_dirty = True
    self.update_window_title()
    self.save_project()
    ```
    In `project_lifecycle.py`:
    ```python
    if not self.project_file:
        return self.save_project_as()
    ```
  - **Impact / Repro:** If a user opens audio, transcribes it, edits a speaker or transcript word, and presses Ctrl+Z *before* explicitly saving the project to disk, `_restore_project_state_for_undo()` calls `self.save_project()`. Because `self.project_file` is `None`, it immediately pops open a modal `QFileDialog.getSaveFileName` ("Save Project As") dialog in the middle of pressing Ctrl+Z!
  - **Suggested Fix:** In `_restore_project_state_for_undo()`, mark `self.project_dirty = True` and update the title, but ONLY call `self.save_project()` if `self.project_file is not None`. Or remove `self.save_project()` from undo restoration altogether, leaving saving to explicit user saves or autosave.
  - **Effort:** Small (S)

---

### High Severity

- [ ] **P1-03 [HIGH] Stale Background Worker Callbacks Mutate & Overwrite Stale Projects on Disk**
  - **Lens:** L1 (Bug) / L8 (Data Integrity) / L5 (Confusing UI)
  - **Location:** [`transcription_processing.py:489`](file:///d:/rtvs3/transcription_processing.py#L489), [`diarization_processing.py:598`](file:///d:/rtvs3/diarization_processing.py#L598), [`story_detection_processing.py:108`](file:///d:/rtvs3/story_detection_processing.py#L108)
  - **Evidence:**
    In `transcription_processing.py`:
    ```python
    self.transcript = transcript
    ...
    self.render_transcript()
    ...
    self.save_project()
    ```
  - **Impact / Repro:** When a background worker (transcription, diarization, auto story detection) finishes, it does NOT check whether `self.audio_file` or `self.project_file` is still the original file that was submitted. If a user switches media files or opens a different project while a job is running, the finished worker assigns its results to the newly active project and immediately calls `self.save_project()`, overwriting the newly loaded project on disk with data from the previous file!
  - **Suggested Fix:** Bind a generation token or source audio path to every worker invocation (e.g. `worker_job_token` or `worker_source_audio`). In the completion handler, verify `if getattr(self, "worker_job_token", None) != finished_job_token: return` before mutating project state or calling `self.save_project()`.
  - **Effort:** Medium (M)

- [ ] **P1-04 [HIGH] Unattended Multi-File Batch Halts on Single Error Due to Blocking Modal Dialogs**
  - **Lens:** L1 (Bug) / L7 (Error Handling) / L5 (Confusing UI)
  - **Location:** [`media_batch.py:1530-1537`](file:///d:/rtvs3/media_batch.py#L1530-L1537), [`media_batch.py:562-571`](file:///d:/rtvs3/media_batch.py#L562-L571), [`transcription_processing.py:541`](file:///d:/rtvs3/transcription_processing.py#L541), [`diarization_processing.py:628`](file:///d:/rtvs3/diarization_processing.py#L628)
  - **Evidence:**
    In `media_batch.py`:
    ```python
    def _batch_media_error(self, message):
        self.log_activity(f"[BATCH ERROR] {message}")
        self.progress.hide()
        self.cancel_button.hide()
        self.set_processing_stage(None)
        self.batch_active = False
        QMessageBox.critical(self, "Batch Processing Error", message)
    ```
    In `transcription_processing.py`:
    ```python
    if getattr(self, "batch_active", False):
        self.batch_active = False
    ...
    QMessageBox.critical(self, "Transcription Error", message)
    ```
  - **Impact / Repro:** While commit `833f311` suppressed modal dialogs in `project_lifecycle.py`, modal `QMessageBox.critical` calls remain in `_batch_media_error`, `_batch_document_error`, `transcription_processing.py:541`, and `diarization_processing.py:628`. If a single media file in a 100-file batch fails (e.g. invalid codec or corrupted stream), the app pops a modal error, terminates `batch_active`, and halts the entire queue unattended.
  - **Suggested Fix:** If `self.batch_active` is True: log the failure, increment a failed file counter, record the error in a batch summary report, and schedule `QTimer.singleShot(0, self._batch_next_media)` to continue processing the remaining queue without modal popups.
  - **Effort:** Medium (M)

- [ ] **P1-05 [HIGH] Purging "Media Link" Irreversibly Destroys Media Reference (Undo Fails)**
  - **Lens:** L1 (Bug) / L8 (Data Integrity)
  - **Location:** [`project_lifecycle.py:774-791`](file:///d:/rtvs3/project_lifecycle.py#L774-L791) and [`project_state_mixin.py:234-243`](file:///d:/rtvs3/project_state_mixin.py#L234-L243)
  - **Evidence:**
    In `project_lifecycle.py`:
    ```python
    if purge_media:
        self.player.stop()
        self.player.setSource(QUrl())
        self.audio_file = None
    ...
    self.statusBar().showMessage("Purged: Media Link. Press Ctrl+Z to undo.")
    ```
    In `project_state_mixin.py` (`_capture_project_state`):
    `_capture_project_state()` only captures stories, transcript, diarization, speaker_names, overrides, and translations. It does **not** capture `self.audio_file`!
  - **Impact / Repro:** When a user purges "Media Link" from the Project Purge dialog, the UI advises that pressing Ctrl+Z will undo. When the user presses Ctrl+Z, `_restore_project_state_for_undo()` does not restore `self.audio_file`. The media link is permanently disconnected.
  - **Suggested Fix:** Include `"audio_file": str(self.audio_file) if self.audio_file else None` in `_capture_project_state()` and restore `self.audio_file` / player source in `_restore_project_state_for_undo()`.
  - **Effort:** Small (S)

- [ ] **P1-06 [HIGH] Periodic Auto-Save Never Runs for New Unsaved Projects**
  - **Lens:** L8 (Data Integrity)
  - **Location:** [`playback_preferences.py:621-622`](file:///d:/rtvs3/playback_preferences.py#L621-L622)
  - **Evidence:**
    ```python
    def trigger_auto_save(self):
        if not (getattr(self, "audio_file", None) and getattr(self, "project_file", None) and getattr(self, "project_dirty", False)):
            return
    ```
  - **Impact / Repro:** If a user opens a media file and works for hours without having yet chosen a save destination (`project_file` is `None`), the periodic auto-save timer does nothing. If the workstation loses power or the process crashes, work is lost because no auto-save snapshot is ever written.
  - **Suggested Fix:** When `self.project_file` is `None` but `self.audio_file` and `self.project_dirty` are present, write an emergency auto-save snapshot adjacent to `self.audio_file` (e.g. `audio_path.with_name(f"{audio_path.stem}.autosave")`) or into the app's cache directory.
  - **Effort:** Small (S)

---

### Medium Severity

- [ ] **P1-07 [MEDIUM] Spurious Background Waveform and Thumbnail Workers Spawned During Batch Jobs**
  - **Lens:** L4 (Performance) / L9 (Resource Leaks)
  - **Location:** [`media_batch.py:1785-1786`](file:///d:/rtvs3/media_batch.py#L1785-L1786)
  - **Evidence:**
    ```python
    self.load_waveform_async()
    self.start_video_thumbnail_generation()
    ```
  - **Impact / Repro:** Inside `load_media_file()`, `load_waveform_async()` and `start_video_thumbnail_generation()` are invoked unconditionally. In batch mode with 50 video files, CPU/GPU background threads are spawned to extract video thumbnails and calculate waveforms for files that are immediately closed upon advancing the queue, degrading ASR throughput.
  - **Suggested Fix:** Add `if not getattr(self, "batch_active", False):` guards before starting waveform and video thumbnail generation in `load_media_file()`.
  - **Effort:** Small (S)

- [ ] **P1-08 [MEDIUM] Batch Directory Ingestion Adds Non-Media & Unsupported Files to Queue**
  - **Lens:** L1 (Bug) / L5 (Confusing UI)
  - **Location:** [`batch_dialog.py:630-633`](file:///d:/rtvs3/batch_dialog.py#L630-L633)
  - **Evidence:**
    ```python
    elif p.is_dir():
        for sub in sorted(p.rglob("*")):
            if sub.is_file() and not any(self.files.item(i).text() == str(sub) for i in range(self.files.count())):
                self.files.addItem(str(sub))
    ```
  - **Impact / Repro:** Adding or dropping a directory onto the Batch dialog queues every single file found recursively (including `.py`, `.git`, `.DS_Store`, `.tmp`, etc.). When `_batch_next_media()` attempts to load these, it fails and triggers `_batch_media_error()`.
  - **Suggested Fix:** Filter `sub.suffix.lower()` against the supported media (`SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS`) and document (`.txt`, `.docx`, `.pdf`, `.html`, `.md`) extension sets before adding items to `self.files`.
  - **Effort:** Small (S)

- [ ] **P1-09 [MEDIUM] Incomplete Undo State Snapshot (Missing Notes and Project Metadata)**
  - **Lens:** L8 (Data Integrity)
  - **Location:** [`project_state_mixin.py:234-243`](file:///d:/rtvs3/project_state_mixin.py#L234-L243)
  - **Evidence:**
    ```python
    def _capture_project_state(self):
        return {
            "stories": [s.to_dict() for s in self.stories],
            "transcript": self._clone_transcript_state(self.transcript),
            "diarization": copy.deepcopy(self.diarization) if self.diarization is not None else None,
            "speaker_names": dict(self.speaker_names),
            "segment_speaker_overrides": {str(k): v for k, v in self.segment_speaker_overrides.items()},
            "translations": copy.deepcopy(self.translations),
            "translation_display_mode": getattr(self, "translation_display_mode", "en"),
            "selected_indices": list(getattr(self, "current_selected_story_indices", [])),
        }
    ```
  - **Impact / Repro:** `transcript_notes`, `project_metadata`, and `custom_speakers` are not included in `_capture_project_state()`. If a user modifies story notes or metadata, undoing another action does not preserve these fields correctly.
  - **Suggested Fix:** Add `transcript_notes`, `project_metadata`, and `custom_speakers` to `_capture_project_state()` and restore them in `_restore_project_state_for_undo()`.
  - **Effort:** Small (S)

- [ ] **P1-10 [MEDIUM] Path Resolution Helper Has Directory Creation Side Effects**
  - **Lens:** L1 (Bug) / L8 (Data Integrity)
  - **Location:** [`media_batch.py:1558`](file:///d:/rtvs3/media_batch.py#L1558) and [`media_batch.py:1561-1563`](file:///d:/rtvs3/media_batch.py#L1561-L1563)
  - **Evidence:**
    ```python
    def _get_batch_project_target_path(self, base_name: str) -> Path:
        ...
        if hasattr(self, "batch_settings") and self.batch_settings.get("unified_transcripts", False):
            projects_dir = Path(base_dir) / "Projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            return projects_dir / f"{base_name}.rtvs"
        else:
            project_dir, _, _, _ = self.prepare_export_directories(
                base_dir, default_name=base_name, prompt_user=False
            )
    ```
  - **Impact / Repro:** `_get_batch_project_target_path()` is a query/getter method, but calling it causes directories (`Projects/`, `Transcripts/`, `Media/`) to be created on disk immediately during queue pre-binding before verification or processing even starts.
  - **Suggested Fix:** Separate path resolution from directory creation. Defer `mkdir()` and `prepare_export_directories()` calls to the actual save/export execution methods.
  - **Effort:** Small (S)

---

### Low / Hygiene Severity

- [ ] **P1-11 [LOW] Outdated Docstring Version Header in `media_batch.py`**
  - **Lens:** L6 (Outdated Docs)
  - **Location:** [`media_batch.py:1`](file:///d:/rtvs3/media_batch.py#L1)
  - **Evidence:** `"""Radio & TV Segmenter v1.1.1 — media batch responsibilities.`
  - **Impact:** Misleading version attribution; current codebase baseline is `v3.9.45-beta`.
  - **Suggested Fix:** Update the docstring header to match the current release version.
  - **Effort:** Small (S)

- [ ] **P1-12 [LOW] Decorative Unicode Checkmark Glyph in Save State Label**
  - **Lens:** UI Discipline (Section 7 of `AGENTS.md`)
  - **Location:** [`project_lifecycle.py:541`](file:///d:/rtvs3/project_lifecycle.py#L541) and [`playback_preferences.py:638`](file:///d:/rtvs3/playback_preferences.py#L638)
  - **Evidence:**
    `self.save_state_label.setText(f"✓ Saved {saved_time}")`
    `self.save_state_label.setText(f"✓ Recovery snapshot {current_time}")`
  - **Impact:** Violates the UI design directive prohibiting unrequested icons/emojis in desktop typography.
  - **Suggested Fix:** Use standard typography: `"Saved " + saved_time` or `"Saved at " + saved_time`.
  - **Effort:** Small (S)

---

## Verified Robust / Architectural Highlights

During the Phase 1 audit, several key mechanisms were verified to be functioning properly according to architectural standards:

1. **Atomic Project Writes (`write_rtvs_project_file` in `project_serialization.py`)**:
   Atomically writes serialized gzip payloads to a `.tmp` file, calls `f.flush()` and `os.fsync(f.fileno())`, and executes `safe_replace(temp_file, p)` to prevent corrupted zero-byte files upon sudden process termination.
2. **Cross-Drive Path Handling (`os.path.relpath`)**:
   `project_audio_reference()` in `project_lifecycle.py` properly wraps `os.path.relpath()` in a `try ... except ValueError:` block to prevent Windows crashes when media and project files reside on different drive letters (e.g. `C:` vs `D:`).
3. **Transparent Serialization Decoding (`read_rtvs_project_file`)**:
   Correctly handles both modern gzip-compressed `.rtvs` bundles and legacy plain `.json` project files with strict byte decompression limits (`MAX_DECOMPRESSED_PROJECT_BYTES = 50 * 1024 * 1024`).

---

## Proposed Point Release Packaging Plan

To adhere to the standardized version bump policy and keep releases clean and regression-free, fixes can be grouped into two focused releases:

- **Release A (`v3.9.46-beta` — Persistence & Undo Safety)**:
  - Fix **P1-02**: Suppress modal file dialog during Ctrl+Z on unsaved projects.
  - Fix **P1-03**: Bind generation tokens to worker completions to stop cross-project state pollution.
  - Fix **P1-05**: Include media path in undo capture/restore.
  - Fix **P1-06**: Enable emergency autosave for unsaved new projects.
  - Fix **P1-09**: Capture notes, custom speakers, and metadata in undo stack.
  - Fix **P1-12**: Clean decorative checkmarks in save state labels.

- **Release B (`v3.9.47-beta` — Batch Processing Robustness)**:
  - Fix **P1-01**: Fix `skip_existing` logic to prevent clobbering completed files with blank exports.
  - Fix **P1-04**: Non-blocking batch error recovery (continue next file on failure instead of modal halts).
  - Fix **P1-07**: Suppress background waveform/thumbnail generation in headless batch runs.
  - Fix **P1-08**: Filter batch folder ingestion by supported file extensions.
  - Fix **P1-10**: Remove directory creation side effects from path getter.
  - Fix **P1-11**: Update `media_batch.py` version docstring.

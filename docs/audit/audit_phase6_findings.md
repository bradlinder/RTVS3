# Code Audit Findings  Phase 6: Export Pipeline & Remaining UI

> **Scope**: `export/dialog.py`, `export_story_pipeline.py`, `export/docx.py`, `export/pdf.py`, `export/subtitles.py`, `export/timeline.py`, `export/audio.py`, `preferences_tabs.py`, `ui_layout.py`.  
> **Date**: October 2026  
> **Target Version**: `v3.9.45-beta`  
> **Status**: Checklist for upcoming release cycles (`- [ ]` = actionable fix).

---

## Executive Summary of Findings

| ID | Severity | File(s) | Category | Description | Suggested Fix Effort |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **P6-01** | `CRITICAL` | `ui_layout.py:908` | Crash / Bug | `auto_generate_selected_story_excerpt` iterates `dict` keys, crashing with `AttributeError` | `S` (< 15 mins) |
| **P6-02** | `CRITICAL` | `export/audio.py:117-152` | Deadlock / Performance | `_run_ffmpeg_export` pipe buffer deadlock on multi-minute media exports | `M` (~ 1 hr) |
| **P6-03** | `HIGH` | `preferences_tabs.py:1-1142` | Dead Code / Bloat | Monolithic 1,142-line `preferences_tabs.py` is an orphaned dead duplicate | `S` (< 15 mins) |
| **P6-04** | `HIGH` | `export/dialog.py`, `export_story_pipeline.py` | UI Inconsistency / Functional Gap | DAW timeline formats bifurcated between Local Disk & Timeline with silent drops | `M` (~ 2 hrs) |
| **P6-05** | `HIGH` | `export/timeline.py:423-424` | Functional Defect | Samplitude EDL destination timecode hardcoded to source timecode, defeating gap omission | `S` (< 30 mins) |
| **P6-06** | `MEDIUM` | `ui_layout.py:307, 229-234` | UI Design Rule Violation | Unrequested emojis (💬, 🟡, 🟢) and checkmarks in buttons and combo boxes | `S` (< 15 mins) |
| **P6-07** | `MEDIUM` | `export/pdf.py:85-115, 252` | Visual / Rendering Defect | Custom PDF writer proportional wrap overflow & duplicate empty page on re-call | `M` (~ 1 hr) |
| **P6-08** | `MEDIUM` | `ui_layout.py:895-943` | Undo / Redo Integrity | Story excerpt editing and auto-generation bypasses Undo/Redo state snapshots | `S` (< 30 mins) |
| **P6-09** | `LOW` | `export/dialog.py:87, 1363` | Dead Code | `_temp_preview_files` initialized and cleared on reject but never populated | `S` (< 10 mins) |
| **P6-10** | `LOW` | `export/reorder_dialog.py:64-68` | Edge-Case Inconsistency | Default fallback list in reorder destinations dialog omits `"timeline"` | `S` (< 10 mins) |

---

## Detailed Findings & Actionable Fix Checklists

### P6-01: [CRITICAL] `ui_layout.py:908` Crashes with `AttributeError` on Excerpt Generation Fallback
- [ ] **Problem**: In [`ui_layout.py:906-913`](file:///d:/rtvs3/ui_layout.py#L906-L913), when auto-generating a story excerpt if `_get_transcript_text_slice` returns empty text, the fallback routine attempts:
  ```python
  if not raw_text and hasattr(self, "transcript"):
      words = []
      for seg in getattr(self, "transcript", []) or []:
          s_start = seg.get("start", 0.0)
          s_end = seg.get("end", 0.0)
          if (st.start is None or s_end >= st.start) and (st.end is None or s_start <= st.end):
              words.append(seg.get("text", ""))
      raw_text = " ".join(words)
  ```
  Throughout the codebase, `self.transcript` is a `dict` (e.g. `{"segments": [...], "language": "en"}`), NOT a `list`. Iterating over a dictionary yields string keys (`"segments"`, `"text"`). Calling `seg.get("start", 0.0)` raises:
  `AttributeError: 'str' object has no attribute 'get'`.
- [ ] **Impact**: Application crashes immediately if the user clicks "Auto Excerpt" on a story when `_get_transcript_text_slice` fails or returns empty.
- [ ] **Fix**: Safely extract segments list:
  ```python
  trans = getattr(self, "transcript", None) or {}
  segments = trans.get("segments", []) if isinstance(trans, dict) else (trans if isinstance(trans, list) else [])
  for seg in segments:
      ...
  ```
- [ ] **Effort**: `S` (< 15 mins).

---

### P6-02: [CRITICAL] `export/audio.py:117-152` FFmpeg Subprocess Pipe Buffer Deadlock
- [ ] **Problem**: In [`export/audio.py:87-152`](file:///d:/rtvs3/export/audio.py#L87-L152), `_run_ffmpeg_export` spawns FFmpeg with stdout and stderr captured via OS pipes:
  ```python
  proc = subprocess.Popen(
      command,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      encoding="utf-8",
      errors="replace",
      creationflags=creationflags,
  )
  ...
  while True:
      ...
      retcode = proc.poll()
      if retcode is not None:
          stdout, stderr = proc.communicate()
          return subprocess.CompletedProcess(command, retcode, stdout, stderr)
      ...
      safe_process_events()
      time.sleep(0.03)
  ```
  Neither `proc.stdout` nor `proc.stderr` is read during the polling loop. Neither `-loglevel error` nor `-nostats` is passed in FFmpeg commands. When FFmpeg produces more than the OS pipe buffer limit (64KB on Windows and Linux), FFmpeg blocks waiting for the pipe buffer to drain. Because Python is blocked in `time.sleep(0.03)` waiting for `proc.poll()`, a mutual deadlock occurs. The export freezes completely for 1,800 seconds (30 minutes) until killed by `subprocess.TimeoutExpired`.
- [ ] **Impact**: Long exports, video transcode fallback, or noisy media with container stream warnings freeze indefinitely.
- [ ] **Fix**: Pass `-loglevel error` / `-nostats` to minimize pipe chatter, and non-blockingly drain pipes in the loop or use a worker thread with `proc.communicate()`.
- [ ] **Effort**: `M` (~ 1 hr).

---

### P6-03: [HIGH] Monolithic 1,142-Line `preferences_tabs.py` is an Orphaned Dead Duplicate
- [ ] **Problem**: [`preferences_tabs.py`](file:///d:/rtvs3/preferences_tabs.py#L1-L1142) is 1,142 lines of code. However, [`preferences_dialog.py:18-25`](file:///d:/rtvs3/preferences_dialog.py#L18-L25) imports exclusively from `preferences_tabs_core.py` and `preferences_tabs_media.py`. A repository-wide regex search reveals ZERO occurrences of `preferences_tabs` being imported. The entire 1,142-line file is an abandoned duplicate left behind during modularization.
- [ ] **Impact**: 1,142 lines of dead code polluting the root directory, wasting developer attention, causing confusion during maintenance, and skewing line count audits.
- [ ] **Fix**: Delete `preferences_tabs.py` (or replace with a 5-line backward compatibility facade re-exporting from `preferences_tabs_core` and `preferences_tabs_media`).
- [ ] **Effort**: `S` (< 15 mins).

---

### P6-04: [HIGH] DAW Timeline Formats Bifurcated Between Local Disk & Timeline Pages with Silent Drop
- [ ] **Problem**: 
  1. In [`export/dialog.py:454-458`](file:///d:/rtvs3/export/dialog.py#L454-L458), the "Local Disk" page provides checkboxes for DAW formats: `cb_rpp`, `cb_edl`, `cb_audacity`, `cb_audition_xml`, `cb_daw_csv`.
  2. In [`export/dialog.py:809-811`](file:///d:/rtvs3/export/dialog.py#L809-L811), the "Timeline" destination page ALSO provides checkboxes for `rpp`, `edl`, `audition_xml`, `audacity`, `cue`, `daw_csv`, PLUS `fcpxml`, `aaf`, `hindenburg`.
  3. When exported via "Local Disk", [`export_dialogs.py:179-210`](file:///d:/rtvs3/export_dialogs.py#L179-L210) routes to [`export_story_pipeline.py`](file:///d:/rtvs3/export_story_pipeline.py#L358-L397). In `export_story_pipeline.py`:
     - `sample_rate` is NEVER passed (defaults to 44.1k/48k regardless of settings).
     - `track_name`, `scope`, and `all_stories` are NEVER passed.
     - In `export_full_episode()` lines 913-946, if `self.stories` is empty/None, all DAW timeline exports are SILENTLY SKIPPED with zero warning to the user!
  4. When exported via "Timeline", [`export_dialogs.py:241`](file:///d:/rtvs3/export_dialogs.py#L241) routes to [`export_documents.py:579`](file:///d:/rtvs3/export_documents.py#L579), which properly passes all options.
- [ ] **Impact**: Users exporting timeline files from the "Local Disk" page get incomplete, un-configured outputs, or zero files exported if no stories are defined.
- [ ] **Fix**: Unify DAW export routing to `export_documents.py:export_timeline_interchange` across both pages, or remove duplicate DAW checkboxes from the Local Disk page with an explicit note directing users to the "Timeline / DAW" destination tab.
- [ ] **Effort**: `M` (~ 2 hrs).

---

### P6-05: [HIGH] Samplitude EDL Destination Timecode Hardcoded to Source Timecode
- [ ] **Problem**: In [`export/timeline.py:421-424`](file:///d:/rtvs3/export/timeline.py#L421-L424):
  ```python
  src_in_tc = format_edl_timestamp(start)
  src_out_tc = format_edl_timestamp(end)
  dst_in_tc = src_in_tc
  dst_out_tc = src_out_tc
  ```
  `dst_in_tc` and `dst_out_tc` (destination timeline placement) are hardcoded to match `src_in_tc` and `src_out_tc` (source file position). When the user selects `unselected_audio_mode = "exclude"`, `build_timeline_clips` only returns the selected story segments. However, because destination timecode is equal to source timecode, Samplitude/Sequoia places the stories on the destination track separated by large blank gaps matching the unselected audio duration, instead of concatenating them sequentially!
- [ ] **Impact**: Broadcast editors importing the EDL into Samplitude/Sequoia get giant gaps on the destination timeline rather than a contiguous assembled edit.
- [ ] **Fix**: Maintain a running `dst_cursor` that advances by `clip["duration"]` when `unselected_audio_mode == "exclude"`, and only sync `dst = src` when continuous episode mode or split mode is active.
- [ ] **Effort**: `S` (< 30 mins).

---

### P6-06: [MEDIUM] UI Design Rule Violation (Section 7): Unrequested Emojis & Decorative Glyphs
- [ ] **Problem**:
  1. [`ui_layout.py:307`](file:///d:/rtvs3/ui_layout.py#L307): `self.comments_toggle_btn = QPushButton("\U0001f4ac Comments", self)` (speech bubble emoji 💬).
  2. [`ui_layout.py:229-234`](file:///d:/rtvs3/ui_layout.py#L229-L234): Color circle emojis (`🟡 Yellow`, `🟢 Green`, `🔵 Blue / Cyan`, `🌸 Pink`, `🟠 Orange`, `🟣 Purple`) in highlight color combobox.
  3. [`preferences_tabs_core.py:422, 486`](file:///d:/rtvs3/preferences_tabs_core.py#L422): Appends decorative checkmark `\u2713` into GPU combobox labels.
- [ ] **Impact**: Violates strict UI design directive (Section 7: *"Do NOT add icons or emoji symbols (such as folders, clouds, disks, checkmarks, warning signs, labels, or decorative unicode glyphs) to tabs, buttons, dialog titles, menus, table headers, group boxes, or cards"*). Emojis render inconsistently or as broken glyph boxes across different Windows versions and High-DPI screens.
- [ ] **Fix**: Replace `\U0001f4ac Comments` with plain `"Comments"`. Remove emoji circles from highlight color combo (e.g. `"Yellow"`, `"Green"`). Replace `\u2713` with `"(Installed)"`.
- [ ] **Effort**: `S` (< 15 mins).

---

### P6-07: [MEDIUM] Custom PDF Writer Proportional Font Word-Wrap Overflow & Empty Page Duplication
- [ ] **Problem**:
  1. In [`export/pdf.py:85-90`](file:///d:/rtvs3/export/pdf.py#L85-L90), `_approx_char_width` assumes a fixed monospace width (`size * 0.51` or `0.56`) for proportional Helvetica. When text contains many wide capital letters (acronyms, German titles, uppercase URLs), `_wrap_text` underestimates line width and text clips off the right page margin.
  2. Non-Windows-1252 characters are caught by `try: b = ch.encode('cp1252') except Exception: out.append('?')`, silently turning smart quotes, em-dashes, or non-Latin text into question marks.
  3. In `finish(self)` line 252, if called more than once (e.g. calling `get_pdf_bytes()` twice), `self._flush_page()` appends an extra blank page to `self.pages`.
- [ ] **Impact**: Potential clipping or corruption of non-Latin characters in exported PDF transcripts; accidental blank pages.
- [ ] **Fix**: Use character width tables for standard 14 Helvetica, normalize non-cp1252 quotes/dashes to ASCII equivalents before encoding, and add an idempotency flag `self._finished` in `finish()`.
- [ ] **Effort**: `M` (~ 1 hr).

---

### P6-08: [MEDIUM] Story Excerpt Editing and Auto-Generation Bypasses Undo/Redo State Snapshots
- [ ] **Problem**: In [`ui_layout.py:895-943`](file:///d:/rtvs3/ui_layout.py#L895-L943), both `auto_generate_selected_story_excerpt()` and `_on_story_excerpt_text_changed()` mutate story metadata directly (`st.metadata["excerpt"] = txt`) and set `self.project_dirty = True`. Neither method calls `_commit_project_state_change()`.
- [ ] **Impact**: Users cannot undo excerpt modifications or auto-generations via Ctrl+Z. If an auto-excerpt replaces a manually crafted excerpt, it cannot be reverted.
- [ ] **Fix**: Call `if hasattr(self, "_commit_project_state_change"): self._commit_project_state_change()` before mutating the excerpt in `auto_generate_selected_story_excerpt` and on excerpt editing finished.
- [ ] **Effort**: `S` (< 30 mins).

---

### P6-09: [LOW] Orphaned `self._temp_preview_files` in `UnifiedExportDialog`
- [ ] **Problem**: In [`export/dialog.py:87`](file:///d:/rtvs3/export/dialog.py#L87), `self._temp_preview_files = set()` is initialized. In [`export/dialog.py:1363`](file:///d:/rtvs3/export/dialog.py#L1363), `done()` iterates over `self._temp_preview_files` to delete them on dialog rejection. However, nowhere in `UnifiedExportDialog` is `self._temp_preview_files` ever populated.
- [ ] **Impact**: Minor dead code vestige. Plugin destinations (like WordPress and YouTube) track their own temporary files on their respective widgets.
- [ ] **Fix**: Query child plugin tab widgets for temp preview files or remove the unused set.
- [ ] **Effort**: `S` (< 10 mins).

---

### P6-10: [LOW] `ReorderExportDestinationsDialog` Default Fallback Omits `"timeline"`
- [ ] **Problem**: In [`export/reorder_dialog.py:64-68`](file:///d:/rtvs3/export/reorder_dialog.py#L64-L68), `self.available_dests` defaults to:
  ```python
  self.available_dests = available_dests or [
      ("local", "Local Files (Media & Transcripts)"),
      ("wordpress", "WordPress Draft Post"),
      ("youtube", "YouTube Studio (Assisted Upload)"),
  ]
  ```
  `DEFAULT_EXPORT_DESTINATIONS_ORDER` at line 22 is `["local", "timeline", "wordpress", "youtube"]`. The fallback list omits `("timeline", "DAW / Video Timeline")`.
- [ ] **Impact**: If `available_dests` is not passed by a caller, the Timeline destination is absent from the reordering dialog.
- [ ] **Fix**: Add `("timeline", "DAW / Video Timeline Interchange")` to the fallback list.
- [ ] **Effort**: `S` (< 10 mins).

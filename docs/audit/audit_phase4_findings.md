# Phase 4 Code Audit Findings & Actionable Checklist
**Focus Subsystems:** Inline Speaker Renaming (`speaker_dialogs.py`), Shortcut Wiring & Schema (`shortcuts/schema.py`, `shortcuts/manager.py`), Voice Profile Dialog & Mixins (`voice_profile_dialog.py`, `voice_profile_matcher_mixin.py`, `voice_profile_ops_mixin.py`), and Attribution (`playback_preferences.py`).
**App Baseline:** v3.9.45-beta

---

## Executive Summary

Phase 4 audit inspected recently added features from commits `e7255d3`, `7872367`, `b9b66bb`, and `2af2bf9`:
- **2 Critical Findings**: 24 out of 79 core actions in `shortcuts/schema.py` lack `attr_name` and can never be customized by the user, and playback keys (`Space`, `Left`, `Right`) are hardcoded in `eventFilter` in `playback_controller.py`, bypassing user preferences.
- **2 High Findings**: A 548-line byte-for-byte dead duplicate file ([`voice_profile_matcher_mixin.py`](file:///d:/rtvs3/voice_profile_matcher_mixin.py)), and synchronous whole-project disk saves (`self.main_win.save_project()`) executed on every Tab keystroke during inline speaker renaming.
- **1 Medium Finding**: A 634-line monolithic constructor `__init__` in `voice_profile_dialog.py` (file size exceeds the 1,000-line ceiling at 1,006 lines).
- **2 Low / Hygiene Findings**: Hardcoded "3-second" tooltips in speaker sample buttons after preview length was made configurable (1.0–15.0s), and omission of `sherpa-onnx` from the About dialog open-source credits.

---

## Actionable Fix Checklist

### Critical Severity

- [ ] **P4-01 [CRITICAL] 24 Core Action Shortcuts Inoperable for Customization (Missing `attr_name`)**
  - **Lens:** L1 (Bug) / L5 (Confusing UI)
  - **Location:** [`shortcuts/schema.py:430-830`](file:///d:/rtvs3/shortcuts/schema.py#L430-L830) and [`shortcuts/manager.py:151`](file:///d:/rtvs3/shortcuts/manager.py#L151)
  - **Evidence:**
    In `shortcuts/manager.py`:
    ```python
    if defn.attr_name and hasattr(window, defn.attr_name):
        target = getattr(window, defn.attr_name)
    ```
    Inspecting `shortcuts/schema.py` reveals that exactly 24 of the 79 defined actions have no `attr_name` assigned (`attr_name=""`). This includes:
    `play_pause`, `jump_back_short`, `jump_forward_short`, `jump_back_medium`, `jump_forward_medium`, `jump_back_long`, `jump_forward_long`, `jump_to_start`, `jump_to_end`, `play_current_story`, `toggle_follow_playhead`, `mark_story_start`, `mark_story_end`, `configure_fades`, `delete_selected_story`, `split_segment`, `merge_segments`, `find_next`, `find_prev`, `transcript_font_up`, `transcript_font_down`, `transcript_font_reset`, `zoom_in`, `zoom_out`.
  - **Impact / Repro:** Users are presented with a customization UI in Preferences for these 24 shortcuts, but modifying them has zero effect in the application because `apply_to_window()` skips any definition where `attr_name` is blank.
  - **Suggested Fix:** Map `attr_name` in `shortcuts/schema.py` to the actual `QAction` or `QShortcut` attribute on MainWindow (e.g. `shortcut_transcript_font_up`, `shortcut_find_next`, `play_pause_action`, etc.).
  - **Effort:** Small (S)

- [ ] **P4-02 [CRITICAL] Hardcoded Spacebar Key in `playback_controller.py` Bypasses Custom Shortcuts**
  - **Lens:** L1 (Bug) / L5 (Confusing UI)
  - **Location:** [`playback_controller.py:177`](file:///d:/rtvs3/playback_controller.py#L177)
  - **Evidence:**
    ```python
    is_play_key = (key == Qt.Key.Key_Space and not event.modifiers())
    ```
  - **Impact / Repro:** The playback key check is hardcoded directly to `Qt.Key.Key_Space` in the main window's `eventFilter`. Even if a user customizes Play/Pause in Preferences, Space continues to trigger play/pause unconditionally.
  - **Suggested Fix:** Query the active shortcut sequence for `play_pause` from `self.shortcuts_manager` inside the event filter, or route playback toggle via a standardized `QAction` / `QShortcut`.
  - **Effort:** Small (S)

---

### High Severity

- [ ] **P4-03 [HIGH] 548-Line Byte-for-Byte Dead Duplicate Module `voice_profile_matcher_mixin.py`**
  - **Lens:** L2 (Dead/Orphaned Code) / L12 (Code Hygiene)
  - **Location:** [`voice_profile_matcher_mixin.py:1-548`](file:///d:/rtvs3/voice_profile_matcher_mixin.py#L1-L548) and [`voice_profile_ops_mixin.py:1-548`](file:///d:/rtvs3/voice_profile_ops_mixin.py#L1-L548)
  - **Evidence:** Running `git diff voice_profile_matcher_mixin.py voice_profile_ops_mixin.py` yields zero diff. Both files are completely identical. `transcript_story.py` imports `VoiceProfileOpsMixin` from `voice_profile_ops_mixin.py`. `voice_profile_matcher_mixin.py` is not imported anywhere in the project.
  - **Impact:** 548 lines of duplicate code bloating repository size and confusing developers.
  - **Suggested Fix:** Remove `voice_profile_matcher_mixin.py` or turn it into a 2-line backward compatibility facade: `from voice_profile_ops_mixin import *`.
  - **Effort:** Small (S)

- [ ] **P4-04 [HIGH] Synchronous Whole-Project Disk Write on Every Tab Inline Speaker Rename**
  - **Lens:** L4 (Performance) / L5 (UI Responsiveness)
  - **Location:** [`speaker_dialogs.py:629-631`](file:///d:/rtvs3/speaker_dialogs.py#L629-L631)
  - **Evidence:**
    ```python
    self.main_win.render_transcript()
    self.main_win.save_project()
    self._populate()
    ```
  - **Impact / Repro:** When tabbing rapidly through speaker rows in the Speaker Manager, each edit commits immediately and calls `self.main_win.save_project()`. This synchronously serializes and writes the gzip-compressed `.rtvs` project file to disk on the main thread for each individual cell change, causing noticeable keystroke lag on multi-hour projects.
  - **Suggested Fix:** Mark `self.main_win.project_dirty = True`, but defer calling `save_project()` until the user closes the dialog or explicit save triggers occur, or debounce project auto-saving.
  - **Effort:** Small (S)

---

### Medium Severity

- [ ] **P4-05 [MEDIUM] 634-Line Monolithic Constructor `__init__` in `voice_profile_dialog.py`**
  - **Lens:** Section 10 Directive (Modular Architecture & File Size)
  - **Location:** [`voice_profile_dialog.py:32-666`](file:///d:/rtvs3/voice_profile_dialog.py#L32-L666)
  - **Evidence:** `VoiceProfileMatchDialog.__init__` is 634 contiguous lines containing widget creation, styling, and signal wiring in a single routine. The file is 1,006 lines long, exceeding the 1,000-line hard ceiling.
  - **Suggested Fix:** Decompose `__init__` into structured helper sub-methods: `_build_header_card()`, `_build_reference_card()`, `_build_candidates_table()`, and `_build_action_footer()`.
  - **Effort:** Small (S)

---

### Low / Hygiene Severity

- [ ] **P4-06 [LOW] Outdated "3-second" Tooltip Text After Sample Length Made Configurable**
  - **Lens:** L6 (Outdated Docs / UI Text)
  - **Location:** [`speaker_dialogs.py:262`](file:///d:/rtvs3/speaker_dialogs.py#L262) and [`speaker_dialogs.py:318`](file:///d:/rtvs3/speaker_dialogs.py#L318)
  - **Evidence:**
    `btn.setToolTip("Listen to a 3-second sample of this speaker's voice")`
    `"""Play a non-blocking 3-second sample for the specified speaker without altering timeline state."""`
  - **Impact:** Commit `7872367` added a user-configurable preview length (1.0s to 15.0s), making the static "3-second" tooltip inaccurate.
  - **Suggested Fix:** Update tooltip to dynamically display the configured sample length: `f"Listen to a {self._get_sample_duration():.1f}-second sample..."`.
  - **Effort:** Small (S)

- [ ] **P4-07 [LOW] Omission of `sherpa-onnx` from About Dialog Open-Source Credits**
  - **Lens:** L6 (Documentation / Compliance)
  - **Location:** [`playback_preferences.py:348-350`](file:///d:/rtvs3/playback_preferences.py#L348-L350)
  - **Evidence:** The About dialog lists Whisper, faster-whisper, CTranslate2, WeSpeaker, ONNX Runtime, and PyTorch, but omits `sherpa-onnx` (which is credited in `README.md` and provides Parakeet ONNX and FastConformer ONNX engines).
  - **Suggested Fix:** Add `sherpa-onnx (Apache 2.0)` to the AI & Speech credits line.
  - **Effort:** Small (S)

---

## Verified Robust / Architectural Highlights

1. **Inline Tab/Backtab Event Filtering (`SpeakerNameDelegate`)**:
   `eventFilter` cleanly catches `Qt.Key.Key_Tab` and `Qt.Key.Key_Backtab`, commits the editor data via `self.commitData.emit(editor)`, and schedules next row activation via `_pending_tab_advance` without crashing Qt item models.
2. **WeSpeaker ResNet34 ONNX Attribution**:
   Commit `7872367` properly credited WeSpeaker in the About dialog, aligning the desktop UI with `ARCHITECTURE.md` and `NOTICES.txt`.
3. **Dynamic F1 Reference Dialog Generation**:
   Generates a searchable, categorized shortcut reference dialog populated directly from `ShortcutsManager` without hardcoding redundant dialog strings.

---

## Proposed Point Release Packaging Plan

- **Release E (`v3.9.50-beta` — Shortcuts & Dialog Polish)**:
  - Fix **P4-01**: Map all 24 missing `attr_name` fields in `shortcuts/schema.py` so all 79 shortcuts are customizable.
  - Fix **P4-02**: Remove hardcoded `Key_Space` check in `playback_controller.py` to respect user shortcut bindings.
  - Fix **P4-03**: Delete or stub dead duplicate file `voice_profile_matcher_mixin.py`.
  - Fix **P4-04**: Defer synchronous `save_project()` calls during inline speaker table tabbing.
  - Fix **P4-05**: Decompose 634-line `__init__` in `voice_profile_dialog.py`.
  - Fix **P4-06**: Dynamic duration tooltip in speaker sample buttons.
  - Fix **P4-07**: Add `sherpa-onnx` to About dialog open-source credits.

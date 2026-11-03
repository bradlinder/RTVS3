# Changelog

## v3.9.68-beta
- **Windows Auto-Updater Syntax & Detached Handoff Hardening (`updater.py`)**:
  - **Python Helper Syntax & Indentation Resolution**: Fixed critical 4-space unexpected indent bug in `updater.py`'s dynamically generated Python helper template (`rtvs_update_helper.py`), which caused Python to crash on launch with `IndentationError` when updating between releases.
  - **Synchronous In-Memory Validation Guard**: Added `compile(python_helper_code, "rtvs_update_helper.py", "exec")` validation check before writing the helper script to disk. If template generation ever raises a syntax or indentation exception, execution safely aborts to the PowerShell supervisor instead of spawning an inoperable child process.
  - **Preserved UAC Elevation & Post-Install De-Elevation Architecture**: Maintained explicit elevated installer handoff (`runas`) for `C:\Program Files` authorization while guaranteeing standard user token execution on first run via `RadioTVStorySegmenter.iss`'s `{win}\explorer.exe` post-install hook, ensuring drag-and-drop and clipboard functionality work out of the box.

## v3.9.67-beta
- **False Unsaved Changes Prompt Elimination on Application Exit (`project_export.py`, `playback_preferences.py`, `media_batch.py`)**:
  - **Inversion of Activity Logger Default Parameter (`playback_preferences.py`)**: Changed `log_activity(self, action_text, mark_dirty=False)` default from `mark_dirty=True` to `mark_dirty=False`. Ephemeral activity telemetry and diagnostic console messages no longer mark the user's project file as dirty unless explicit project data mutations are committed.
  - **Shutdown Telemetry Self-Dirty Bug Resolution (`project_export.py`)**: In `closeEvent()`, `self.log_activity("[SYSTEM] Application shutdown requested.")` previously invoked `mark_project_dirty()` on every close attempt, converting a clean, saved project (`✓ Saved`) into a dirty project right before the exit prompt check. Explicitly passed `mark_dirty=False` and safeguarded shutdown telemetry.
  - **Graceful Cancel / Discard State Restoration (`project_export.py`)**: Reset `self._is_closing = False` when the user cancels the exit confirmation dialog or if project save fails, and cleared `self.project_dirty = False` upon user discard.
  - **Background Waveform & Story Selection False-Dirty Elimination (`media_batch.py`, `processing.py`, `export_documents.py`)**: Background waveform generation completion, timeline story selection, document/audio exports, and preference updates no longer inadvertently trigger dirty state.
  - **Window Title & State Label Synchronization (`media_batch.py`)**: Ensured `update_window_title()` is called immediately following crash recovery or autosave restore so `save_state_label` always accurately reflects project dirty status.

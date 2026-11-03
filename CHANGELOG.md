# Changelog

## v3.9.67-beta
- **False Unsaved Changes Prompt Elimination on Application Exit (`project_export.py`, `playback_preferences.py`, `media_batch.py`)**:
  - **Inversion of Activity Logger Default Parameter (`playback_preferences.py`)**: Changed `log_activity(self, action_text, mark_dirty=False)` default from `mark_dirty=True` to `mark_dirty=False`. Ephemeral activity telemetry and diagnostic console messages no longer mark the user's project file as dirty unless explicit project data mutations are committed.
  - **Shutdown Telemetry Self-Dirty Bug Resolution (`project_export.py`)**: In `closeEvent()`, `self.log_activity("[SYSTEM] Application shutdown requested.")` previously invoked `mark_project_dirty()` on every close attempt, converting a clean, saved project (`✓ Saved`) into a dirty project right before the exit prompt check. Explicitly passed `mark_dirty=False` and safeguarded shutdown telemetry.
  - **Graceful Cancel / Discard State Restoration (`project_export.py`)**: Reset `self._is_closing = False` when the user cancels the exit confirmation dialog or if project save fails, and cleared `self.project_dirty = False` upon user discard.
  - **Background Waveform & Story Selection False-Dirty Elimination (`media_batch.py`, `processing.py`, `export_documents.py`)**: Background waveform generation completion, timeline story selection, document/audio exports, and preference updates no longer inadvertently trigger dirty state.
  - **Window Title & State Label Synchronization (`media_batch.py`)**: Ensured `update_window_title()` is called immediately following crash recovery or autosave restore so `save_state_label` always accurately reflects project dirty status.

## v3.9.66-beta
- **Windows Detached Installer Handoff & Window Visibility Fix (`updater.py`, `project_data_purge_dialog.py`, `ui_layout.py`)**:
  - **Explicit `-WindowStyle Normal` Execution (`updater.py`)**: Added `-WindowStyle Normal` parameters to `Start-Process` calls in the PowerShell supervisor script (`rtvs_update_supervisor.ps1`). Previously, spawning `powershell.exe` with `CREATE_NO_WINDOW` caused child `Start-Process` invocations to inherit `Hidden` window style, causing Inno Setup (`RadioTVSegmenter-*-Setup.exe`) to execute invisibly in the background.
  - **Fail-Safe CMD Batch Supervisor Fallback (`updater.py`)**: Added a secondary `.cmd` batch supervisor (`rtvs_update_supervisor.cmd`) utilizing `start "" "%INSTALLER_PATH%"`. The Windows `start` command forces Windows Shell `ShellExecute` with `SW_SHOWNORMAL` (1) and native UAC elevation, guaranteeing the installer GUI wizard opens visibly on screen even if PowerShell is restricted or fails to spawn.
  - **Subprocess Cmd Launch Fallback (`updater.py`)**: Updated Python helper script fallback to `cmd.exe /c start "" "%INSTALLER_PATH%"`, ensuring shell window visibility across all launch paths.
  - **Startup Import Error Hotfix (`project_data_purge_dialog.py`, `ui_layout.py`)**: Fixed `ImportError: cannot import name 'make_dialog_maximizable'` by importing from `core_utils` and adding a backward-compatible re-export in `ui_layout.py`.


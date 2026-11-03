# Changelog

## v3.9.66-beta
- **Windows Detached Installer Handoff & Window Visibility Fix (`updater.py`)**:
  - **Explicit `-WindowStyle Normal` Execution (`updater.py`)**: Added `-WindowStyle Normal` parameters to `Start-Process` calls in the PowerShell supervisor script (`rtvs_update_supervisor.ps1`). Previously, spawning `powershell.exe` with `CREATE_NO_WINDOW` caused child `Start-Process` invocations to inherit `Hidden` window style, causing Inno Setup (`RadioTVSegmenter-*-Setup.exe`) to execute invisibly in the background.
  - **Fail-Safe CMD Batch Supervisor Fallback (`updater.py`)**: Added a secondary `.cmd` batch supervisor (`rtvs_update_supervisor.cmd`) utilizing `start "" "%INSTALLER_PATH%"`. The Windows `start` command forces Windows Shell `ShellExecute` with `SW_SHOWNORMAL` (1) and native UAC elevation, guaranteeing the installer GUI wizard opens visibly on screen even if PowerShell is restricted or fails to spawn.
  - **Subprocess Cmd Launch Fallback (`updater.py`)**: Updated Python helper script fallback to `cmd.exe /c start "" "%INSTALLER_PATH%"`, ensuring shell window visibility across all launch paths.

## v3.9.65-beta
- **Unsaved Changes Prompt Harmonization & False-Dirty Elimination (`playback_controller.py`, `project_lifecycle.py`, `media_batch.py`, `project_data_purge_dialog.py`)**:
  - **False-Dirty Elimination on UI Playback Controls (`playback_controller.py`)**: Removed erroneous `self.project_dirty = True` flag when updating skip duration (`set_skip_seconds_from_ui`), persisting user preferences directly to `QSettings` without dirtying clean projects.
  - **Standardized Save / Discard / Cancel Prompt Matrix (`project_lifecycle.py`, `media_batch.py`)**: Standardized all project close/open prompts to explicit `Save | Discard | Cancel` choices, aligning `close_project()` and `load_project_file()` with `closeEvent()` and clearing `self.project_dirty = False` immediately upon user discard or successful save.
  - **Eliminated Double-Prompts on New Project Workflow (`project_lifecycle.py`, `media_batch.py`)**: Guaranteed that closing or resetting a project immediately sets `project_dirty = False`, ensuring subsequent media loading dialogs do not re-prompt when opening new media.
  - **Modular Architecture & File Size Compliance (`project_data_purge_dialog.py`, `project_lifecycle.py`)**: Extracted `ProjectDataPurgeDialog` into a dedicated UI dialog submodule, reducing `project_lifecycle.py` from 999 to 864 lines while maintaining 100% backward compatibility via facade re-exports.


# Changelog

## v3.9.65-beta
- **Unsaved Changes Prompt Harmonization & False-Dirty Elimination (`playback_controller.py`, `project_lifecycle.py`, `media_batch.py`, `project_data_purge_dialog.py`)**:
  - **False-Dirty Elimination on UI Playback Controls (`playback_controller.py`)**: Removed erroneous `self.project_dirty = True` flag when updating skip duration (`set_skip_seconds_from_ui`), persisting user preferences directly to `QSettings` without dirtying clean projects.
  - **Standardized Save / Discard / Cancel Prompt Matrix (`project_lifecycle.py`, `media_batch.py`)**: Standardized all project close/open prompts to explicit `Save | Discard | Cancel` choices, aligning `close_project()` and `load_project_file()` with `closeEvent()` and clearing `self.project_dirty = False` immediately upon user discard or successful save.
  - **Eliminated Double-Prompts on New Project Workflow (`project_lifecycle.py`, `media_batch.py`)**: Guaranteed that closing or resetting a project immediately sets `project_dirty = False`, ensuring subsequent media loading dialogs do not re-prompt when opening new media.
  - **Modular Architecture & File Size Compliance (`project_data_purge_dialog.py`, `project_lifecycle.py`)**: Extracted `ProjectDataPurgeDialog` into a dedicated UI dialog submodule, reducing `project_lifecycle.py` from 999 to 864 lines while maintaining 100% backward compatibility via facade re-exports.

## v3.9.65-beta
- **Unsaved Changes Prompt Harmonization & False-Dirty Elimination (`playback_controller.py`, `project_lifecycle.py`, `media_batch.py`, `project_data_purge_dialog.py`)**:
  - **False-Dirty Elimination on UI Playback Controls (`playback_controller.py`)**: Removed erroneous `self.project_dirty = True` flag when updating skip duration (`set_skip_seconds_from_ui`), persisting user preferences directly to `QSettings` without dirtying clean projects.
  - **Standardized Save / Discard / Cancel Prompt Matrix (`project_lifecycle.py`, `media_batch.py`)**: Standardized all project close/open prompts to explicit `Save | Discard | Cancel` choices, aligning `close_project()` and `load_project_file()` with `closeEvent()` and clearing `self.project_dirty = False` immediately upon user discard or successful save.
  - **Eliminated Double-Prompts on New Project Workflow (`project_lifecycle.py`, `media_batch.py`)**: Guaranteed that closing or resetting a project immediately sets `project_dirty = False`, ensuring subsequent media loading dialogs do not re-prompt when opening new media.
  - **Modular Architecture & File Size Compliance (`project_data_purge_dialog.py`, `project_lifecycle.py`)**: Extracted `ProjectDataPurgeDialog` into a dedicated UI dialog submodule, reducing `project_lifecycle.py` from 999 to 864 lines while maintaining 100% backward compatibility via facade re-exports.


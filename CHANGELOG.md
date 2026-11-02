# Changelog

## v3.9.60-beta
- **Empty Project Close & Save Prompt Bypass (`project_state_mixin.py`, `media_batch.py`, `project_lifecycle.py`, `project_export.py`, `diagnostic_cloud_and_system_tests.py`)**:
  - **Workspace State Inspection (`is_project_empty()`)**: Added `is_project_empty()` to `ProjectStateMixin` to verify whether the workspace contains loaded audio (`audio_file`), an associated project file (`project_file`), transcript text/segments (`transcript`), or defined stories (`stories`).
  - **Silent Media Ingestion on Blank Canvas**: Updated `prepare_for_new_media()` in `media_batch.py` so opening or dragging an audio file into an empty workspace proceeds immediately without prompting *"The current project has unsaved changes. Would you like to save it before closing?"*.
  - **Silent Project Reset & Clean State Guarantee**: Updated `close_project()` and `load_project_file()` in `project_lifecycle.py` and `closeEvent()` in `project_export.py` to bypass confirmation dialogs when the workspace is empty, and ensured `self.project_dirty = False` is explicitly reset on project close so subsequent file operations always start with a clean state.

## v3.9.59-beta
- **Preferences Real-Time Category & Setting Search Filter (`preferences_dialog.py`, `diagnostic_loudness_tests.py`)**:
  - **Inline Search Box Above Navigation Tabs**: Added a dedicated settings search box directly above the category navigation sidebar on the left of the Preferences dialog, providing natural, desktop-standard discoverability.
  - **Instant Multi-Page Setting Text Indexing**: As the user types (e.g. *whisper*, *loudness*, *theme*, *gpu*, *shortcuts*), the dialog inspects labels, checkboxes, groupbox titles, combobox entries, table items, and tooltips across all stacked pages in real time (~2ms).
  - **Dynamic Category Filtering & Match Badging**: Automatically hides non-matching category tabs and appends live match count badges to matching categories (e.g. `AI Models (7)`, `Audio Settings (4)`). If the active tab no longer matches, focus auto-switches to the first matching category.
  - **Fluid Keyboard Navigation**: Added `Escape` key handling to instantly clear the search filter and restore full category visibility without closing the dialog, and `Down` arrow handling to transition focus seamlessly from the search field into the category list. Clearing the search box restores all original category names and visibility immediately.

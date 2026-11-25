# Changelog

## v3.10.13-beta
- **Milestone 3.1: `model_management.py` Modularization & `ModelCleanupDialog` Extraction (`model_management.py`, `model_cleanup_dialog.py`, `installer/build_tools/config.py`, `diagnostics/editor_story_ui_tests.py`, `diagnostics/system_runtime_tests.py`)**:
  - **Pure Qt UI Extraction (`model_cleanup_dialog.py`)**:
    - Extracted `ModelCleanupDialog`, `WHISPER_MODEL_CATALOG`, `format_directory_size()`, and shared `_stop_and_remove_runtime_env()` helper out of `model_management.py`, preserving all Manage Models controls, progress callbacks, selected-model removal, translation runtime cleanup prompts, and full purge hooks.
  - **Controller Cleanup & Duplication Pruning (`model_management.py`, `installer/build_tools/config.py`)**:
    - Reduced `model_management.py` from 989 lines to ~610 lines (well below the 800-line target), pruned unused Qt widget imports, reused `WHISPER_MODEL_CATALOG` and `_stop_and_remove_runtime_env()` in `refresh_whisper_model_chooser()` and `purge_all_data_action()`, kept all `ModelManagementMixin` & `WhisperModelInstallWorker` re-exports intact, removed obsolete `model_management.pyi`, and added `model_cleanup_dialog` to PyInstaller `HIDDEN_IMPORTS`.
  - **Regression Coverage (`diagnostics/editor_story_ui_tests.py`, `diagnostics/system_runtime_tests.py`)**:
    - Added `ModelCleanupDialog` instantiation, row/progress/refresh checks and `model_management` re-export assertions, and registered `model_management.py` + `model_cleanup_dialog.py` in modularity budget verification.

## v3.10.12-beta
- **Milestone 3.4: Modular Diagnostic Test Suites & Installer Packaging Decomposition (`diagnostics/*.py`, `diagnostic_helpers.py`, `diagnostic_selector.py`, `diagnostic_export_tests.py`, `diagnostic_cloud_and_system_tests.py`, `diagnostic_batch_tests.py`, `diagnostic_editor_tests.py`, `installer/build_tools/*.py`, `build_installer.py`, `scripts/modular_audit.py`, `scripts/dev_check.py`)**:
  - **Modular `diagnostics/` Package (`diagnostics/*.py`, `diagnostic_helpers.py`, `diagnostic_selector.py`)**:
    - Decomposed `diagnostic_export_tests.py` (2,314 lines), `diagnostic_cloud_and_system_tests.py` (1,409 lines), `diagnostic_batch_tests.py` (1,076 lines), and `diagnostic_editor_tests.py` (1,005 lines) into 11 cohesive `<650`-line submodules under `diagnostics/` while turning the 4 original modules into minimal backward-compatible facades.
    - Added shared `PROJECT_ROOT` to `diagnostic_helpers.py`, updated `diagnostic_selector.py` to map `diagnostics/*.py` edits cleanly in smart change selection, and updated `_test_in_app_user_guides_and_documentation_viewer` and `_test_source_file_modularity_and_1000_line_budget_invariant` for the modular layout.
  - **Modular `installer/build_tools/` Package (`installer/build_tools/*.py`, `build_installer.py`)**:
    - Extracted `config.py`, `env_checks.py`, and `packaging.py` from `build_installer.py` (1,099 → ~375 lines), preserving all CLI entrypoints, PyInstaller worker exclusion flags, docs copytree steps, and backward-compatible wrapper functions.
  - **Audit & Stub Cleanup (`scripts/modular_audit.py`, `scripts/dev_check.py`)**:
    - Removed all 5 newly modularized files from `GRANDFATHERED_LEGACY_MODULES` / `GRANDFATHERED`, pruned unused imports across extracted modules, and removed now-unneeded `build_installer.pyi` and `diagnostic_editor_tests.pyi` stubs (`15 -> 10` >1,000-line modules repo-wide).
  - **GUI Diagnostic Bench Main-Thread Qt Dispatch Fix (`diagnostic_dialog.py`, `test_runner.py`, `diagnostic_selector.py`, `diagnostics/cloud_storage_tests.py`)**:
    - Extracted shared `DiagnosticEngine.resolve_test_method_name()` in `test_runner.py` (used by both `diagnostic_selector.py` and `diagnostic_dialog.py`).
    - Updated `TestRunnerWorker` in `diagnostic_dialog.py` so every Qt GUI diagnostic test (frozen allowlist + `inspect.getsource` marker scan) dispatches via `BlockingQueuedConnection` to the Qt main thread, preventing `QObject::setParent` cross-thread crashes when `Plugin Interface Sandbox Testing` runs `check_for_plugin_updates()`, and patched `QProgressDialog.forceShow()` in `diagnostics/cloud_storage_tests.py`.

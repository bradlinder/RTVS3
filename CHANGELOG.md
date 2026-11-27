# Changelog

## v3.10.32-beta
- **Fix Missing Imports (`NameError` Crashes) in Activity Snapshot Restore, Preferences Reset & REAPER Clipboard Fallback + Dead Code & PyInstaller Hardening (`playback_preferences.py`, `preferences_reset_dialog.py`, `transcript_context_menu_mixin.py`, `runtime_manager.py`, `installer/build_tools/config.py`, `diagnostics/youtube_import_cache_tests.py`)**:
  - **Fix Activity Snapshot Restore Crash (`playback_preferences.py`)**: Added missing `import copy` and `Story` import from `prs_shared` so clicking saved snapshots in `restore_snapshot()` no longer raises `NameError`.
  - **Fix Preferences Reset ("Software Updates") Crash & Model Label (`preferences_reset_dialog.py`)**: Imported `DEFAULT_GITHUB_REPO` from `core_utils` so resetting Software Updates / Factory Defaults executes cleanly, and aligned the AI Models reset description with the `parakeet-onnx` default.
  - **Fix REAPER Clipboard Copy Fallback Logger (`transcript_context_menu_mixin.py`)**: Added `logging.getLogger(__name__)` so error-handling fallbacks in `copy_highlighted_selection()` and `copy_selection_for_reaper()` log warnings instead of raising `NameError`.
  - **Dead Code Removal & Frozen-Build Hardening (`runtime_manager.py`, `installer/build_tools/config.py`, `diagnostics/youtube_import_cache_tests.py`)**: Removed unreachable dead code referencing undefined `target` in `prune_cuda_artifacts()` (bringing `runtime_manager.py` under 1,000 lines), registered 8 lazy-imported core dialog/utility modules in PyInstaller `HIDDEN_IMPORTS`, and added regression guards.

## v3.10.31-beta
- **Fix Frozen Installed-App Startup Crash (`NameError: name 'Optional' is not defined`) (`media_batch.py`, `diagnostics/youtube_import_cache_tests.py`)**:
  - Added the missing `from typing import Optional` import at the top of `media_batch.py` required by `MediaBatchMixin._effective_thumbnail_density()` and `start_video_thumbnail_generation()` type annotations when imported in frozen PyInstaller builds where `Optional` is not leaked via `prs_shared`.
  - Audited all repository modules via AST for missing typing imports and added a direct `import media_batch` startup regression check in `diagnostics/youtube_import_cache_tests.py`.

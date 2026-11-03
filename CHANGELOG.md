# Changelog

## v3.9.70-beta
- **Version Source-of-Truth Harmonization & Updater Dialog Desync Resolution (`core_utils.py`, `updater.py`, `prs_shared.py`, `RadioTVSegmenter.py`)**:
  - **Resolution of Core Version Desync**: Harmonized `PROJECT_VERSION` across `core_utils.py`, `prs_shared.py`, `RadioTVSegmenter.py`, and `backup_manager.py` to `3.9.70-beta`, eliminating the desync where `updater.py` read an outdated version from `core_utils.py` while the main window title read from `prs_shared.py`.
  - **Updater Dual-Check Version Binding (`updater.py`)**: Bound `updater.py`'s `PROJECT_VERSION` to synchronize with `prs_shared.PROJECT_VERSION` at module import time, preventing future version drift across decoupled packages.
  - **Checklist & Verification Alignment (`AGENTS.md`, `bump_version.py`)**: Updated project release checklists and automated tooling to verify synchronization across all 13 canonical version entrypoints.

## v3.9.69-beta
- **Auto-Updater End-to-End Verification Release (`updater.py`, `RadioTVStorySegmenter.iss`)**:
  - **Handoff Verification Cycle**: Incremental release to verify live over-the-air update download, detached helper invocation, UAC elevation prompt, and automatic application relaunch from v3.9.68-beta.
  - **De-Elevated Desktop Shell Integrity**: Validates post-install launch via `{win}\explorer.exe` to guarantee uninhibited OLE drag-and-drop and clipboard operations on first launch.

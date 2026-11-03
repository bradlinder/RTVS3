# Changelog

## v3.9.69-beta
- **Auto-Updater End-to-End Verification Release (`updater.py`, `RadioTVStorySegmenter.iss`)**:
  - **Handoff Verification Cycle**: Incremental release to verify live over-the-air update download, detached helper invocation, UAC elevation prompt, and automatic application relaunch from v3.9.68-beta.
  - **De-Elevated Desktop Shell Integrity**: Validates post-install launch via `{win}\explorer.exe` to guarantee uninhibited OLE drag-and-drop and clipboard operations on first launch.

## v3.9.68-beta
- **Windows Auto-Updater Syntax & Detached Handoff Hardening (`updater.py`)**:
  - **Python Helper Syntax & Indentation Resolution**: Fixed critical 4-space unexpected indent bug in `updater.py`'s dynamically generated Python helper template (`rtvs_update_helper.py`), which caused Python to crash on launch with `IndentationError` when updating between releases.
  - **Synchronous In-Memory Validation Guard**: Added `compile(python_helper_code, "rtvs_update_helper.py", "exec")` validation check before writing the helper script to disk. If template generation ever raises a syntax or indentation exception, execution safely aborts to the PowerShell supervisor instead of spawning an inoperable child process.
  - **Preserved UAC Elevation & Post-Install De-Elevation Architecture**: Maintained explicit elevated installer handoff (`runas`) for `C:\Program Files` authorization while guaranteeing standard user token execution on first run via `RadioTVStorySegmenter.iss`'s `{win}\explorer.exe` post-install hook, ensuring drag-and-drop and clipboard functionality work out of the box.

# Changelog

## v3.10.7-beta
- **Milestone 3.1 & 3.3 Modularization: Retire Orphaned `plugin_dialogs.py` & Extract `AudioLoudnessProbeWorker` (`audio_normalization.py`, `audio_normalization_worker.py`, `prs_shared.py`, `scripts/modular_audit.py`, `diagnostic_loudness_tests.py`)**:
  - **Retire Dead Legacy Module (`plugin_dialogs.py`, `scripts/modular_audit.py`)**:
    - Deleted obsolete `plugin_dialogs.py` (`447` lines), which had zero callers and was superseded by `plugins/installer_workers.py`, `plugins/github_dialog.py`, and `plugins/manager_dialog.py`.
  - **100% Qt-Free Loudness Engine & Worker Extraction (`audio_normalization.py`, `audio_normalization_worker.py`, `prs_shared.py`, `scripts/modular_audit.py`)**:
    - Extracted `AudioLoudnessProbeWorker` and its `PySide6.QtCore` import block verbatim into dedicated `audio_normalization_worker.py`.
    - Updated `prs_shared.py` to import `AudioLoudnessProbeWorker` directly from `audio_normalization_worker` for static PyInstaller tracing, added a lazy `__getattr__` backward-compatibility shim in `audio_normalization.py` (now 100% Qt-free), and removed both `plugin_dialogs.py` and `audio_normalization.py` from `GRANDFATHERED_LEGACY_MODULES` (`7 -> 5` legacy exemptions).
  - **Regression Coverage (`diagnostic_loudness_tests.py`)**:
    - Extended `_test_smart_hybrid_audio_loudness_probing` with AST zero-`PySide6` verification on `audio_normalization.py` and identity checks for `AudioLoudnessProbeWorker` via both `audio_normalization` and `prs_shared`.

## v3.10.6-beta
- **`ManageVoiceProfilesDialog` Actions Column Sizing & Label Polish (`speaker_profiles_dialog.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **DPI-Aware Actions Column Sizing (`speaker_profiles_dialog.py`)**:
    - Widened default/minimum dialog dimensions (`900x520` / `820x460`), increased button horizontal padding (`padding: 3px 10px`) and action layout margins (`6, 2, 6, 2`), enforced `btn.setMinimumWidth(btn.sizeHint().width())` on `Rename`, `Match Project`, and `Delete`, and dynamically sized column `4` to `max(270, action_w.sizeHint().width() + 12)` so `Match Project` never clips under Windows DPI scaling.
  - **Samples / Turns Grammar Polish (`speaker_profiles_dialog.py`)**:
    - Formatted singular sample counts as `"1 turn"` and plural/zero counts as `"{N} turns"`.
  - **Regression Coverage (`diagnostic_speaker_cleanup_tests.py`)**:
    - Extended `_test_station_voice_checkbox_and_threshold_normalization` with layout assertions on `ManageVoiceProfilesDialog` verifying `"1 turn"` text, `columnWidth(4) >= action_w.sizeHint().width()`, and `btn.minimumWidth() >= btn.sizeHint().width()` across all three action buttons.

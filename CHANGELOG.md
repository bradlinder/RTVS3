# Changelog

## v3.10.6-beta
- **`ManageVoiceProfilesDialog` Actions Column Sizing & Label Polish (`speaker_profiles_dialog.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **DPI-Aware Actions Column Sizing (`speaker_profiles_dialog.py`)**:
    - Widened default/minimum dialog dimensions (`900x520` / `820x460`), increased button horizontal padding (`padding: 3px 10px`) and action layout margins (`6, 2, 6, 2`), enforced `btn.setMinimumWidth(btn.sizeHint().width())` on `Rename`, `Match Project`, and `Delete`, and dynamically sized column `4` to `max(270, action_w.sizeHint().width() + 12)` so `Match Project` never clips under Windows DPI scaling.
  - **Samples / Turns Grammar Polish (`speaker_profiles_dialog.py`)**:
    - Formatted singular sample counts as `"1 turn"` and plural/zero counts as `"{N} turns"`.
  - **Regression Coverage (`diagnostic_speaker_cleanup_tests.py`)**:
    - Extended `_test_station_voice_checkbox_and_threshold_normalization` with layout assertions on `ManageVoiceProfilesDialog` verifying `"1 turn"` text, `columnWidth(4) >= action_w.sizeHint().width()`, and `btn.minimumWidth() >= btn.sizeHint().width()` across all three action buttons.

## v3.10.5-beta
- **Milestone 3.3 Modularization: Extract `ManageVoiceProfilesDialog` from `speaker_profiles.py` (`speaker_profiles.py`, `speaker_profiles_dialog.py`, `voice_profile_ops_mixin.py`, `scripts/modular_audit.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **Pure Qt UI Extraction (`speaker_profiles_dialog.py`, `voice_profile_ops_mixin.py`)**:
    - Extracted `ManageVoiceProfilesDialog` verbatim into dedicated `speaker_profiles_dialog.py` and updated `VoiceProfileOpsMixin.open_manage_voice_profiles_dialog()` to import directly from `speaker_profiles_dialog` for static PyInstaller tracing.
  - **100% Qt-Free Headless Model & Store (`speaker_profiles.py`, `scripts/modular_audit.py`)**:
    - Removed all `PySide6` and UI imports from `speaker_profiles.py` (`249` lines), sourcing `get_app_data_dir` and `safe_replace` directly from `core_utils`, adding a lazy `__getattr__` backward-compatibility shim for `ManageVoiceProfilesDialog`, and removing `speaker_profiles.py` from `GRANDFATHERED_LEGACY_MODULES` (`8 -> 7` legacy exemptions).
  - **Verification (`diagnostic_speaker_cleanup_tests.py`)**:
    - Added AST zero-`PySide6` import check on `speaker_profiles.py` and lazy facade identity check in `_test_station_voice_checkbox_and_threshold_normalization`.

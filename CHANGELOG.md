# Changelog

## v3.10.5-beta
- **Milestone 3.3 Modularization: Extract `ManageVoiceProfilesDialog` from `speaker_profiles.py` (`speaker_profiles.py`, `speaker_profiles_dialog.py`, `voice_profile_ops_mixin.py`, `scripts/modular_audit.py`, `diagnostic_speaker_cleanup_tests.py`)**:
  - **Pure Qt UI Extraction (`speaker_profiles_dialog.py`, `voice_profile_ops_mixin.py`)**:
    - Extracted `ManageVoiceProfilesDialog` verbatim into dedicated `speaker_profiles_dialog.py` and updated `VoiceProfileOpsMixin.open_manage_voice_profiles_dialog()` to import directly from `speaker_profiles_dialog` for static PyInstaller tracing.
  - **100% Qt-Free Headless Model & Store (`speaker_profiles.py`, `scripts/modular_audit.py`)**:
    - Removed all `PySide6` and UI imports from `speaker_profiles.py` (`249` lines), sourcing `get_app_data_dir` and `safe_replace` directly from `core_utils`, adding a lazy `__getattr__` backward-compatibility shim for `ManageVoiceProfilesDialog`, and removing `speaker_profiles.py` from `GRANDFATHERED_LEGACY_MODULES` (`8 -> 7` legacy exemptions).
  - **Verification (`diagnostic_speaker_cleanup_tests.py`)**:
    - Added AST zero-`PySide6` import check on `speaker_profiles.py` and lazy facade identity check in `_test_station_voice_checkbox_and_threshold_normalization`.

## v3.10.4-beta
- **WordPress User vs. PublishPress Guest Author Mapping Fix (`plugins/wordpress/authors.py`, `plugins/wordpress/wp_tab_widget.py`, `plugins/wordpress/wordpress_dialog.py`, `plugins/wordpress/plugin.py`, `plugins/wordpress/youtube_embed.py`, `plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`, `plugins/wordpress/manifest.json`, `diagnostic_wordpress_tests.py`, `test_runner.py`)**:
  - **Shared Author Mapping Helper (`plugins/wordpress/authors.py`)**:
    - Created pure-Python `plugins/wordpress/authors.py` cleanly separating WordPress core `user_id` (`author`) from PublishPress Authors `term_id` (`ppma_author`) across `extract_checked_author_ids()`, `is_author_item_selected()`, `resolve_selected_author_names()`, `count_selected_authors()`, and `expand_legacy_author_term_ids()`.
    - Ensures mapped WordPress Users (`is_guest=False` with `term_id > 0`) populate both `author_ids` and `author_term_ids` so mixing a WordPress User and Guest Author (or selecting two mapped WordPress Users) preserves every checked author instead of PublishPress overwriting with just Guest Authors, and removing a Guest Author cleanly replaces `ppma_author` with the remaining user(s).
    - Keeps Guest Authors (`is_guest=True`) strictly in `author_term_ids` without leaking `term_id` into WordPress core `author`, avoids falsely pre-checking WordPress's core `post_author` creator on Guest-only posts when fetching existing posts, and avoids double-counting mapped users in post tooltips.
  - **Update Payload & Legacy Compatibility Fixes (`plugins/wordpress/export_destination.py`, `plugins/wordpress/client.py`)**:
    - Guarded existing-post auto-resolution so checking any author intentionally overwrites existing authors while leaving Authors completely empty preserves existing server authors.
    - Fixed `create_post()` duplicate-commit fallback parameter names (`author_ids`, `author_term_ids`, `category_ids`, `podcast_series`) and added a best-effort `ppma_author` follow-up `POST` when `update_post()` strips `ppma_author` on strict endpoints.
  - **Plugin Catch-Up & Regression Verification (`plugins/wordpress/manifest.json`, `diagnostic_wordpress_tests.py`, `test_runner.py`)**:
    - Bumped `plugins/wordpress/manifest.json` from `3.10.3-beta` to `3.10.4-beta` and added `_test_wordpress_publishpress_author_mapping_and_update_semantics` covering mixed User+Guest, multi-User, Guest-only, standard WP User, legacy `.rtvs` expansion, and overwrite vs. preserve semantics.

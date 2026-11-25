"""Backward-compatible facade for WordPress Existing Episode Lookup, Backfill Mode & MP3 Import.

Headless lookup/parsing/date/slug/download helpers live in ``episode_lookup``;
Qt workflow UI controls and dialogs live in ``episode_updater_ui``.
"""
from __future__ import annotations

from plugins.wordpress.episode_lookup import (
    MODE_NEW_EPISODE,
    MODE_UPDATE_EXISTING,
    _copy_fetched_post_fields,
    _extract_audio_url_from_post_payload,
    _parse_wp_post_json,
    _populate_project_from_fetched_post,
    _resolve_download_dir,
    build_story_slug,
    clean_html_to_plain_excerpt,
    download_wp_episode_audio,
    extract_slug_or_id_from_url,
    format_wp_date_for_input,
    normalize_wp_iso_date,
    resolve_wp_post_from_url,
)
from plugins.wordpress.episode_updater_ui import (
    LoadWordPressEpisodeDialog,
    PublicationDateLineEdit,
    _get_configured_client,
    _get_current_tab_post,
    _is_update_mode,
    _refresh_dialog_export_button,
    _sync_mode_visibility,
    _update_existing_status_label,
    apply_fetched_post_to_tab,
    load_episode_updater_from_post,
    prompt_load_existing_wp_episode_dialog,
    setup_wp_mode_and_date_ui,
    sync_wp_audio_checkbox_label,
)

__all__ = [
    "MODE_NEW_EPISODE",
    "MODE_UPDATE_EXISTING",
    "extract_slug_or_id_from_url",
    "clean_html_to_plain_excerpt",
    "build_story_slug",
    "normalize_wp_iso_date",
    "format_wp_date_for_input",
    "resolve_wp_post_from_url",
    "download_wp_episode_audio",
    "apply_fetched_post_to_tab",
    "load_episode_updater_from_post",
    "setup_wp_mode_and_date_ui",
    "PublicationDateLineEdit",
    "LoadWordPressEpisodeDialog",
    "prompt_load_existing_wp_episode_dialog",
]

"""Update manager and GitHub release installer facade for Radio & TV Segmenter.

Preserves 100% backward-compatible top-level exports across:
- ``updater_core``: Headless GitHub release metadata, semantic versioning, checksum
  verification, detached installer launch, and installer cache cleanup.
- ``updater_workers``: Background QThread workers (``CheckUpdateWorker``,
  ``DownloadUpdateWorker``).
- ``updater_dialog``: Qt UI presentation (``CheckUpdateDialog``, ``UpdaterMixin``).
"""
from __future__ import annotations

try:
    from core_utils import PROJECT_VERSION
    try:
        from prs_shared import PROJECT_VERSION as _PRS_PROJECT_VERSION
        PROJECT_VERSION = _PRS_PROJECT_VERSION
    except Exception:
        pass
except ImportError:
    try:
        from prs_shared import PROJECT_VERSION
    except Exception:
        PROJECT_VERSION = "3.10.19-beta"

from updater_core import (
    APP_DISPLAY_NAME,
    DEFAULT_GITHUB_REPO,
    INTERNAL_APP_ID,
    _find_release_checksum,
    _is_trusted_download_url,
    _write_update_log,
    cleanup_old_installers,
    fetch_latest_release,
    fetch_releases,
    format_byte_size,
    get_app_data_dir,
    get_github_repo,
    get_update_channel,
    is_version_newer,
    is_version_older,
    launch_and_install,
    parse_version_tuple,
    select_best_asset_for_platform,
)
from updater_workers import (
    CheckUpdateWorker,
    DownloadUpdateWorker,
)
from updater_dialog import (
    CheckUpdateDialog,
    UpdaterMixin,
    get_app_icon,
)

__all__ = [
    "APP_DISPLAY_NAME",
    "DEFAULT_GITHUB_REPO",
    "INTERNAL_APP_ID",
    "PROJECT_VERSION",
    "get_app_data_dir",
    "get_github_repo",
    "get_update_channel",
    "get_app_icon",
    "parse_version_tuple",
    "is_version_newer",
    "is_version_older",
    "format_byte_size",
    "_is_trusted_download_url",
    "_find_release_checksum",
    "select_best_asset_for_platform",
    "fetch_releases",
    "fetch_latest_release",
    "_write_update_log",
    "launch_and_install",
    "cleanup_old_installers",
    "CheckUpdateWorker",
    "DownloadUpdateWorker",
    "CheckUpdateDialog",
    "UpdaterMixin",
]

"""Application constants and environment configuration.

Re-exports authoritative constants from core_utils and prs_shared to prevent version/constant drift.
"""
from __future__ import annotations

from core_utils import (
    APP_DISPLAY_NAME,
    PROJECT_VERSION,
    DEFAULT_GITHUB_REPO,
    INTERNAL_APP_ID,
    get_github_repo,
)

try:
    from prs_shared import (
        HELPER_PROTOCOL_VERSION,
        WAVEFORM_ANALYSIS_RATE,
        WAVEFORM_POINTS_PER_SECOND,
        MIN_WORDS_PER_PARAGRAPH,
        MAX_ACTIVITY_SNAPSHOTS,
    )
except Exception:
    HELPER_PROTOCOL_VERSION = "1.0"
    WAVEFORM_ANALYSIS_RATE = 8000
    WAVEFORM_POINTS_PER_SECOND = 200
    MIN_WORDS_PER_PARAGRAPH = 65
    MAX_ACTIVITY_SNAPSHOTS = 50

__all__ = [
    "APP_DISPLAY_NAME",
    "PROJECT_VERSION",
    "DEFAULT_GITHUB_REPO",
    "INTERNAL_APP_ID",
    "HELPER_PROTOCOL_VERSION",
    "WAVEFORM_ANALYSIS_RATE",
    "WAVEFORM_POINTS_PER_SECOND",
    "MIN_WORDS_PER_PARAGRAPH",
    "MAX_ACTIVITY_SNAPSHOTS",
    "get_github_repo",
]

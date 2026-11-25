"""Backward-compatible facade for legacy WordPress dialog imports.

All live UI logic is consolidated into ``wp_tab_widget`` (canonical
``WordPressExportTabWidget``), ``export_destination`` (``WordPressPostMetadataDialog``),
and ``wp_post_builder`` (``capture_video_frame``).
"""
from __future__ import annotations

from plugins.wordpress.client import generate_wp_excerpt as _client_generate_wp_excerpt
from plugins.wordpress.export_destination import WordPressPostMetadataDialog
from plugins.wordpress.wp_post_builder import capture_video_frame
from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget


def generate_wp_excerpt(transcript_words, start_t, end_t):
    """Legacy wrapper preserving the historical `(transcript_words, start_t, end_t)` signature."""
    slice_text = " ".join(
        w.get("text", "") for w in transcript_words if start_t <= float(w.get("start", 0)) <= end_t
    )
    return _client_generate_wp_excerpt(slice_text)


__all__ = [
    "WordPressExportTabWidget",
    "WordPressPostMetadataDialog",
    "capture_video_frame",
    "generate_wp_excerpt",
]

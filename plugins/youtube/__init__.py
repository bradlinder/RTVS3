"""YouTube Video Publisher Plugin for Radio & TV Segmenter."""
from __future__ import annotations

try:
    from plugins.youtube.plugin import Plugin
    __all__ = ["Plugin"]
except ImportError:
    __all__ = []


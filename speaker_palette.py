"""Accessible adaptive speaker color palette for Radio & TV Story Segmenter.

Provides a transcription-optimized 8-color paired palette designed for maximum legibility
across both light/print media (DOCX, PDF, Light Mode UI) and dark desktop environments (Dark Mode UI).
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SpeakerColor:
    name: str
    light_hex: str
    dark_hex: str
    high_contrast_hex: str
    light_rgb: Tuple[int, int, int]
    dark_rgb: Tuple[int, int, int]
    pdf_rgb: Tuple[float, float, float]


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.strip().lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (0, 0, 0)


def _rgb_to_pdf(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    return (round(rgb[0] / 255.0, 3), round(rgb[1] / 255.0, 3), round(rgb[2] / 255.0, 3))


def _make_speaker_color(name: str, light_hex: str, dark_hex: str, hc_hex: str) -> SpeakerColor:
    l_rgb = _hex_to_rgb(light_hex)
    d_rgb = _hex_to_rgb(dark_hex)
    pdf_rgb = _rgb_to_pdf(l_rgb)
    return SpeakerColor(
        name=name,
        light_hex=light_hex,
        dark_hex=dark_hex,
        high_contrast_hex=hc_hex,
        light_rgb=l_rgb,
        dark_rgb=d_rgb,
        pdf_rgb=pdf_rgb,
    )


# 8 distinct accessible transcription color families
SPEAKER_PALETTE: Tuple[SpeakerColor, ...] = (
    _make_speaker_color("Sapphire Blue", "#1A56DB", "#60A5FA", "#00FFFF"),
    _make_speaker_color("Rose Crimson",  "#BE123C", "#FB7185", "#FF69B4"),
    _make_speaker_color("Emerald Green", "#047857", "#34D399", "#00FF00"),
    _make_speaker_color("Royal Violet",  "#6D28D9", "#A78BFA", "#E879F9"),
    _make_speaker_color("Amber Ochre",   "#B45309", "#FBBF24", "#FFFF00"),
    _make_speaker_color("Deep Teal",     "#0E7490", "#22D3EE", "#87CEFA"),
    _make_speaker_color("Berry Magenta", "#A21CAF", "#E879F9", "#FF00FF"),
    _make_speaker_color("Slate Indigo",  "#4338CA", "#818CF8", "#818CF8"),
)


def get_speaker_index(speaker: str, index: Optional[int] = None) -> int:
    """Derive a deterministic 0..7 index from an explicit index, speaker label, or hash."""
    if index is not None and index >= 0:
        return index % len(SPEAKER_PALETTE)

    spk_clean = str(speaker or "").strip()
    if not spk_clean:
        return 0

    # Match numeric patterns: SPEAKER_01, Speaker 2, S03, 1, etc.
    m = re.search(r"(?:speaker[_\s]*|spk[_\s]*|s)(\d+)", spk_clean, re.IGNORECASE)
    if m:
        try:
            val = int(m.group(1))
            return val % len(SPEAKER_PALETTE)
        except (ValueError, TypeError):
            pass

    # Pure number
    if spk_clean.isdigit():
        return int(spk_clean) % len(SPEAKER_PALETTE)

    # Deterministic CRC32 hash of string
    crc = zlib.crc32(spk_clean.lower().encode("utf-8"))
    return crc % len(SPEAKER_PALETTE)


def get_speaker_color(speaker: str, index: Optional[int] = None) -> SpeakerColor:
    """Return the SpeakerColor dataclass instance for the given speaker name/index."""
    idx = get_speaker_index(speaker, index)
    return SPEAKER_PALETTE[idx]


def get_speaker_hex(speaker: str, dark_mode: bool = False, high_contrast: bool = False, index: Optional[int] = None) -> str:
    """Return hex color code ('#RRGGBB') adapted to the current display theme or export mode."""
    c = get_speaker_color(speaker, index)
    if high_contrast:
        return c.high_contrast_hex
    return c.dark_hex if dark_mode else c.light_hex


def get_speaker_rgb(speaker: str, dark_mode: bool = False, index: Optional[int] = None) -> Tuple[int, int, int]:
    """Return (R, G, B) integer tuple in 0..255 range."""
    c = get_speaker_color(speaker, index)
    return c.dark_rgb if dark_mode else c.light_rgb


def get_speaker_pdf_rgb(speaker: str, index: Optional[int] = None) -> Tuple[float, float, float]:
    """Return (r, g, b) float tuple in 0.0..1.0 range suitable for PDF content streams."""
    c = get_speaker_color(speaker, index)
    return c.pdf_rgb


class SpeakerColorAssigner:
    """Maintains sequential appearance-order color assignments for a document/project."""

    def __init__(self):
        self._assigned: Dict[str, int] = {}
        self._next_idx = 0

    def get_index(self, speaker: str) -> int:
        clean = (speaker or "").strip()
        if not clean:
            return 0
        if clean not in self._assigned:
            self._assigned[clean] = self._next_idx % len(SPEAKER_PALETTE)
            self._next_idx += 1
        return self._assigned[clean]

    def get_color(self, speaker: str) -> SpeakerColor:
        idx = self.get_index(speaker)
        return SPEAKER_PALETTE[idx]

    def get_hex(self, speaker: str, dark_mode: bool = False, high_contrast: bool = False) -> str:
        idx = self.get_index(speaker)
        return get_speaker_hex(speaker, dark_mode=dark_mode, high_contrast=high_contrast, index=idx)

    def get_rgb(self, speaker: str, dark_mode: bool = False) -> Tuple[int, int, int]:
        idx = self.get_index(speaker)
        return get_speaker_rgb(speaker, dark_mode=dark_mode, index=idx)

    def get_pdf_rgb(self, speaker: str) -> Tuple[float, float, float]:
        idx = self.get_index(speaker)
        return get_speaker_pdf_rgb(speaker, index=idx)

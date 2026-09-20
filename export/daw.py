"""DAW and NLE timeline interchange formatters for Radio & TV Story Segmenter.

Provides formatting and project file generation for:
- Cockos REAPER Project (.rpp) with tracks, media items, fades, and regions
- Magix Samplitude EDL (v1.5) broadcast edit decision lists
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, List, Optional


def format_edl_timestamp(seconds: float) -> str:
    """Format seconds into standard Samplitude EDL timecode (HH:MM:SS:mmm)."""
    secs = max(0.0, float(seconds or 0.0))
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int(round((secs - int(secs)) * 1000))
    if ms >= 1000:
        s += 1
        ms = 0
    if s >= 60:
        m += 1
        s = 0
    if m >= 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}:{s:02d}:{ms:03d}"


def generate_reaper_project(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    apply_fades: bool = True,
    sample_rate: int = 44100,
) -> str:
    """Generate a clean Cockos REAPER project file (.rpp) with clips, fades, and regions.
    
    Compatible with REAPER v5, v6, and v7+.
    """
    sorted_stories = sorted(stories, key=lambda s: getattr(s, "start", 0.0))
    proj_guid = f"{{{str(uuid.uuid4()).upper()}}}"
    track_guid = f"{{{str(uuid.uuid4()).upper()}}}"

    clean_proj_title = (project_title or "Segmented Project").replace('"', "'")
    media_path_str = str(media_filename or "audio.wav")
    media_name_only = Path(media_path_str).name
    ext = Path(media_path_str).suffix.lower()

    if ext == ".mp3":
        source_type = "MP3"
    elif ext in (".flac", ".fla"):
        source_type = "FLAC"
    elif ext in (".ogg", ".oga"):
        source_type = "OGG"
    elif ext in (".aif", ".aiff"):
        source_type = "AIFF"
    else:
        source_type = "WAVE"

    lines: List[str] = [
        '<REAPER_PROJECT 0.1 "7.0/OSX64" 1710000000',
        '  RIPPLE 0',
        '  GROUPOVERRIDE 0 0 0',
        '  AUTOXFADE 1',
        '  ENVATTACH 1',
        '  POOLEDENVATTACH 0',
        '  MIXERSLIDERS 0',
        f'  SAMPLERATE {int(sample_rate)} 0 0',
        '  TIMEMODE 0 0 -1 30 0',
        f'  <NOTES\n    |{clean_proj_title} - Exported from Radio & TV Story Segmenter\n  >',
        f'  <TRACK {track_guid}',
        '    NAME "Segmented Stories"',
        '    PEAKCOL 16576',
        '    BEAT -1',
        '    VOLPAN 1 0 -1 -1 1',
        '    MUTESOLO 0 0 0',
        '    IPHASE 0',
        '    PLAYREC 1 0 0 0 0 0 0',
    ]

    # Generate audio item blocks for each story
    for i, story in enumerate(sorted_stories, 1):
        start = max(0.0, float(getattr(story, "start", 0.0)))
        end = max(start, float(getattr(story, "end", start)))
        length = max(0.001, end - start)
        title = (getattr(story, "title", "") or f"Story {i}").strip().replace('"', "'")
        item_guid = f"{{{str(uuid.uuid4()).upper()}}}"

        f_in = float(getattr(story, "fade_in", 0.0)) if apply_fades else 0.0
        f_out = float(getattr(story, "fade_out", 0.0)) if apply_fades else 0.0

        lines.extend([
            '    <ITEM',
            f'      POSITION {start:.6f}',
            '      SNAPOFFS 0.000000',
            f'      LENGTH {length:.6f}',
            '      LOOP 0',
            '      ALLTAKES 0',
            f'      FADEIN 1 {f_in:.6f} 0.000000 1 0 0 0',
            f'      FADEOUT 1 {f_out:.6f} 0.000000 1 0 0 0',
            '      MUTE 0',
            '      SEL 0',
            f'      IGUID {item_guid}',
            f'      NAME "{title}"',
            f'      SOFFS {start:.6f}',
            f'      <SOURCE {source_type}',
            f'        FILE "{media_name_only}"',
            '      >',
            '    >',
        ])

    lines.append('  >')  # Close TRACK

    # Generate REAPER Regions for each story (flag 1 indicates a region)
    for i, story in enumerate(sorted_stories, 1):
        start = max(0.0, float(getattr(story, "start", 0.0)))
        end = max(start, float(getattr(story, "end", start)))
        title = (getattr(story, "title", "") or f"Story {i}").strip().replace('"', "'")
        lines.append(f'  MARKER {i} {start:.6f} "{title}" 1 {end:.6f} 1 0')

    lines.append('>')  # Close REAPER_PROJECT
    return "\n".join(lines) + "\n"


def generate_samplitude_edl(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 44100,
    apply_fades: bool = True,
) -> str:
    """Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list."""
    sorted_stories = sorted(stories, key=lambda s: getattr(s, "start", 0.0))
    clean_proj_title = (project_title or "Segmented Project").replace('"', "'")
    media_name_only = Path(media_filename or "audio.wav").name

    lines: List[str] = [
        '"Samplitude EDL File Version 1.5"',
        f'"Project: {clean_proj_title}"',
        f'"Sample Rate: {int(sample_rate)}"',
        '"Tracks: 1"',
        '',
        '// Track   Index   Source-In      Source-Out     Dest-In        Dest-Out       FadeIn FadeOut Name             File',
    ]

    for i, story in enumerate(sorted_stories, 1):
        start = max(0.0, float(getattr(story, "start", 0.0)))
        end = max(start, float(getattr(story, "end", start)))
        title = (getattr(story, "title", "") or f"Story {i}").strip().replace('"', "'")
        f_in = float(getattr(story, "fade_in", 0.0)) if apply_fades else 0.0
        f_out = float(getattr(story, "fade_out", 0.0)) if apply_fades else 0.0

        src_in_tc = format_edl_timestamp(start)
        src_out_tc = format_edl_timestamp(end)
        dst_in_tc = src_in_tc
        dst_out_tc = src_out_tc

        lines.append(
            f'0001    {i:04d}    {src_in_tc}   {src_out_tc}   {dst_in_tc}   {dst_out_tc}   {f_in:06.3f} {f_out:06.3f}   "{title}"\t"{media_name_only}"'
        )

    return "\n".join(lines) + "\n"

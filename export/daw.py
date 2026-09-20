"""DAW and NLE timeline interchange formatters for Radio & TV Story Segmenter.

Provides formatting and project file generation for:
- Cockos REAPER Project (.rpp) with tracks, media items, fades, and regions
- Magix Samplitude EDL (v1.5) broadcast edit decision lists
- Audacity Label Track (.txt) marker import format
- Adobe Audition / Final Cut Pro / Premiere XML (.xml) sequence interchanges
- Universal DAW Marker List (.csv) timestamp and boundary metadata
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


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


def _get_story_start(s) -> float:
    if isinstance(s, dict):
        val = s.get("start", s.get("start_time", 0.0))
    else:
        val = getattr(s, "start", getattr(s, "start_time", 0.0))
    return max(0.0, float(val or 0.0))


def _get_story_end(s, start_val: float) -> float:
    if isinstance(s, dict):
        val = s.get("end", s.get("end_time", start_val))
    else:
        val = getattr(s, "end", getattr(s, "end_time", start_val))
    return max(start_val, float(val if val is not None else start_val))


def build_timeline_clips(
    stories: list,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    apply_fades: bool = True,
) -> List[Dict[str, Any]]:
    """Build an ordered list of timeline clips, optionally filling gaps with unselected audio."""
    sorted_stories = sorted(
        stories or [],
        key=lambda s: _get_story_start(s)
    )

    mode = str(unselected_audio_mode or "exclude").lower().strip()
    if mode not in ("split", "muted") or not sorted_stories:
        clips: List[Dict[str, Any]] = []
        for s in sorted_stories:
            start = _get_story_start(s)
            end = _get_story_end(s, start)
            title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or "Story"
            f_in = float(getattr(s, "fade_in", 0.0) if not isinstance(s, dict) else s.get("fade_in", 0.0)) if apply_fades else 0.0
            f_out = float(getattr(s, "fade_out", 0.0) if not isinstance(s, dict) else s.get("fade_out", 0.0)) if apply_fades else 0.0
            clips.append({
                "start": start,
                "end": end,
                "duration": max(0.0, end - start),
                "title": title,
                "is_unselected": False,
                "is_muted": False,
                "fade_in": f_in,
                "fade_out": f_out,
            })
        return clips

    clips: List[Dict[str, Any]] = []
    current_time = 0.0
    is_muted = (mode == "muted")
    gap_counter = 1

    for s in sorted_stories:
        start = _get_story_start(s)
        end = _get_story_end(s, start)
        title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or "Story"
        f_in = float(getattr(s, "fade_in", 0.0) if not isinstance(s, dict) else s.get("fade_in", 0.0)) if apply_fades else 0.0
        f_out = float(getattr(s, "fade_out", 0.0) if not isinstance(s, dict) else s.get("fade_out", 0.0)) if apply_fades else 0.0

        if start > current_time + 0.005:
            lbl = f"Unselected Audio {gap_counter}" + (" (Muted)" if is_muted else "")
            clips.append({
                "start": current_time,
                "end": start,
                "duration": max(0.0, start - current_time),
                "title": lbl,
                "is_unselected": True,
                "is_muted": is_muted,
                "fade_in": 0.0,
                "fade_out": 0.0,
            })
            gap_counter += 1

        clips.append({
            "start": start,
            "end": end,
            "duration": max(0.0, end - start),
            "title": title,
            "is_unselected": False,
            "is_muted": False,
            "fade_in": f_in,
            "fade_out": f_out,
        })
        current_time = max(current_time, end)

    eff_total = max(float(total_duration or 0.0), current_time)
    if eff_total > current_time + 0.005:
        lbl = f"Unselected Audio {gap_counter}" + (" (Muted)" if is_muted else "")
        clips.append({
            "start": current_time,
            "end": eff_total,
            "duration": max(0.0, eff_total - current_time),
            "title": lbl,
            "is_unselected": True,
            "is_muted": is_muted,
            "fade_in": 0.0,
            "fade_out": 0.0,
        })

    return clips


def generate_reaper_project(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    apply_fades: bool = True,
    sample_rate: int = 44100,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
) -> str:
    """Generate a clean Cockos REAPER project file (.rpp) with clips, fades, regions, and optional unselected audio."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades)
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

    for clip in clips:
        start = clip["start"]
        end = clip["end"]
        length = max(0.001, end - start)
        title = clip["title"].replace('"', "'")
        item_guid = f"{{{str(uuid.uuid4()).upper()}}}"
        mute_val = 1 if clip["is_muted"] else 0

        lines.extend([
            '    <ITEM',
            f'      POSITION {start:.6f}',
            '      SNAPOFFS 0.000000',
            f'      LENGTH {length:.6f}',
            '      LOOP 0',
            '      ALLTAKES 0',
            f'      FADEIN 1 {clip["fade_in"]:.6f} 0.000000 1 0 0 0',
            f'      FADEOUT 1 {clip["fade_out"]:.6f} 0.000000 1 0 0 0',
            f'      MUTE {mute_val}',
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

    # Generate REAPER Regions for clips
    for i, clip in enumerate(clips, 1):
        if unselected_audio_mode == "exclude" and clip["is_unselected"]:
            continue
        start = clip["start"]
        end = clip["end"]
        title = clip["title"].replace('"', "'")
        lines.append(f'  MARKER {i} {start:.6f} "{title}" 1 {end:.6f} 1 0')

    lines.append('>')  # Close REAPER_PROJECT
    return "\n".join(lines) + "\n"


def generate_samplitude_edl(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 44100,
    apply_fades: bool = True,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
) -> str:
    """Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades)
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

    for i, clip in enumerate(clips, 1):
        start = clip["start"]
        end = clip["end"]
        title = clip["title"].replace('"', "'")

        src_in_tc = format_edl_timestamp(start)
        src_out_tc = format_edl_timestamp(end)
        dst_in_tc = src_in_tc
        dst_out_tc = src_out_tc

        lines.append(
            f'0001    {i:04d}    {src_in_tc}   {src_out_tc}   {dst_in_tc}   {dst_out_tc}   {clip["fade_in"]:06.3f} {clip["fade_out"]:06.3f}   "{title}"\t"{media_name_only}"'
        )

    return "\n".join(lines) + "\n"


def generate_audacity_labels(
    stories: list,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
) -> str:
    """Generate an Audacity Label Track (.txt) import file."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode)
    lines: List[str] = []
    for clip in clips:
        lines.append(f"{clip['start']:.6f}\t{clip['end']:.6f}\t{clip['title']}")
    return "\n".join(lines) + ("\n" if lines else "")


def generate_audition_xml(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 44100,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
) -> str:
    """Generate Adobe Audition / Final Cut Pro XML (xmeml v5) interchange format."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode)
    clean_title = (project_title or "Segmented Project").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    media_name = Path(media_filename or "audio.wav").name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    timebase = 30
    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE xmeml>',
        '<xmeml version="5">',
        '  <sequence>',
        f'    <name>{clean_title}</name>',
        '    <rate>',
        f'      <timebase>{timebase}</timebase>',
        '      <ntsc>FALSE</ntsc>',
        '    </rate>',
        '    <media>',
        '      <audio>',
        '        <track>',
    ]

    for i, clip in enumerate(clips, 1):
        c_title = clip["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        start_frame = int(round(clip["start"] * timebase))
        end_frame = int(round(clip["end"] * timebase))
        in_frame = start_frame
        out_frame = end_frame
        mute_str = "TRUE" if clip["is_muted"] else "FALSE"

        lines.extend([
            f'          <clipitem id="clip-{i}">',
            f'            <name>{c_title}</name>',
            f'            <start>{start_frame}</start>',
            f'            <end>{end_frame}</end>',
            f'            <in>{in_frame}</in>',
            f'            <out>{out_frame}</out>',
            f'            <mute>{mute_str}</mute>',
            '            <file id="file-1">',
            f'              <name>{media_name}</name>',
            f'              <pathurl>{media_name}</pathurl>',
            '              <rate>',
            f'                <timebase>{timebase}</timebase>',
            '                <ntsc>FALSE</ntsc>',
            '              </rate>',
            '            </file>',
            '          </clipitem>',
        ])

    lines.extend([
        '        </track>',
        '      </audio>',
        '    </media>',
        '  </sequence>',
        '</xmeml>',
    ])

    return "\n".join(lines) + "\n"


def generate_daw_marker_csv(
    stories: list,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
) -> str:
    """Generate a Universal DAW & NLE Marker List (.csv) format."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode)
    lines: List[str] = [
        '"Marker Name","Start Time (s)","End Time (s)","Duration (s)","Type","Status"',
    ]

    for clip in clips:
        t_type = "Unselected" if clip["is_unselected"] else "Story"
        t_status = "Muted" if clip["is_muted"] else "Active"
        dur = max(0.0, clip["end"] - clip["start"])
        name_clean = clip["title"].replace('"', '""')
        lines.append(
            f'"{name_clean}","{clip["start"]:.3f}","{clip["end"]:.3f}","{dur:.3f}","{t_type}","{t_status}"'
        )

    return "\n".join(lines) + "\n"

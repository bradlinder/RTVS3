"""Multi-Platform Timeline and DAW Interchange Engine for Radio & TV Story Segmenter.

Provides production-grade timeline formatting and sequence project generators for:
- Cockos REAPER Project (.rpp) with tracks, media items, fades, and regions
- Magix Samplitude EDL (v1.5) broadcast edit decision lists
- Apple Final Cut Pro 7 XML (xmeml v5) / Adobe Premiere Pro / Audition sequence interchange
- Apple Final Cut Pro X XML (.fcpxml) / DaVinci Resolve sequence interchange
- Universal AAF Interchange (.aaf) Advanced Authoring Format XML sequence
- Hindenburg Broadcast Session (.nhx) radio and podcast broadcast timeline
- Audacity Label Track (.txt) marker import format
- Red Book Audio CD CUE Sheet (.cue) with 75 fps frames
- Universal DAW Marker List (.csv) timestamp and boundary metadata
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from export.subtitles import generate_cue_content


def _xml_escape(text: str) -> str:
    """Escape special XML characters for well-formed interchange output."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _reaper_fade_curve_index(curve_name: str) -> int:
    """Map RTVS fade curve name to Cockos REAPER native curve shape index."""
    c = str(curve_name or "").lower().strip()
    if c in ("s_curve", "scurve", "cosine", "smooth"):
        return 3
    elif c in ("exponential", "exp", "fast_start"):
        return 1
    elif c in ("logarithmic", "log", "fast_end"):
        return 2
    return 0  # Linear default


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


def _get_story_start(s: Any) -> float:
    if isinstance(s, dict):
        val = s.get("start", s.get("start_time", 0.0))
    else:
        val = getattr(s, "start", getattr(s, "start_time", 0.0))
    return max(0.0, float(val or 0.0))


def _get_story_end(s: Any, start_val: float) -> float:
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
    scope: str = "all_stories",
) -> List[Dict[str, Any]]:
    """Build an ordered list of timeline clips, supporting Full Episode continuous splits and story cuts."""
    sorted_stories = sorted(
        stories or [],
        key=lambda s: _get_story_start(s)
    )

    norm_scope = str(scope or "all_stories").lower().strip()
    is_full_episode_scope = norm_scope in ("full", "full_and_all_stories")
    mode = str(unselected_audio_mode or "exclude").lower().strip()

    # For Full Episode scope, the entire episode from 0:00 to total_duration must be continuous with splits.
    include_gaps = is_full_episode_scope or (mode in ("split", "muted"))

    if not include_gaps or not sorted_stories:
        clips: List[Dict[str, Any]] = []
        for s in sorted_stories:
            start = _get_story_start(s)
            end = _get_story_end(s, start)
            title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or "Story"
            f_in = float(getattr(s, "fade_in", 0.0) if not isinstance(s, dict) else s.get("fade_in", 0.0)) if apply_fades else 0.0
            f_out = float(getattr(s, "fade_out", 0.0) if not isinstance(s, dict) else s.get("fade_out", 0.0)) if apply_fades else 0.0
            f_curve = str(getattr(s, "fade_curve", "linear") if not isinstance(s, dict) else s.get("fade_curve", "linear")) or "linear"
            clips.append({
                "start": start,
                "end": end,
                "duration": max(0.0, end - start),
                "title": title,
                "is_unselected": False,
                "is_muted": False,
                "fade_in": f_in,
                "fade_out": f_out,
                "fade_curve": f_curve,
            })
        return clips

    clips = []
    current_time = 0.0
    is_muted = (mode == "muted")
    gap_counter = 1

    for s in sorted_stories:
        start = _get_story_start(s)
        end = _get_story_end(s, start)
        title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or "Story"
        f_in = float(getattr(s, "fade_in", 0.0) if not isinstance(s, dict) else s.get("fade_in", 0.0)) if apply_fades else 0.0
        f_out = float(getattr(s, "fade_out", 0.0) if not isinstance(s, dict) else s.get("fade_out", 0.0)) if apply_fades else 0.0
        f_curve = str(getattr(s, "fade_curve", "linear") if not isinstance(s, dict) else s.get("fade_curve", "linear")) or "linear"

        # Pre-story or interstitial gap segment
        if start > current_time + 0.005:
            if current_time < 0.005:
                gap_label = "Intro / Pre-Story" + (" (Muted)" if is_muted else "")
            else:
                gap_label = f"Interstitial Gap {gap_counter}" + (" (Muted)" if is_muted else "")
                gap_counter += 1

            clips.append({
                "start": current_time,
                "end": start,
                "duration": max(0.0, start - current_time),
                "title": gap_label,
                "is_unselected": True,
                "is_muted": is_muted,
                "fade_in": 0.0,
                "fade_out": 0.0,
                "fade_curve": "linear",
            })

        clips.append({
            "start": start,
            "end": end,
            "duration": max(0.0, end - start),
            "title": title,
            "is_unselected": False,
            "is_muted": False,
            "fade_in": f_in,
            "fade_out": f_out,
            "fade_curve": f_curve,
        })
        current_time = max(current_time, end)

    eff_total = max(float(total_duration or 0.0), current_time)
    if eff_total > current_time + 0.005:
        gap_label = "Outro / Post-Story" + (" (Muted)" if is_muted else "")
        clips.append({
            "start": current_time,
            "end": eff_total,
            "duration": max(0.0, eff_total - current_time),
            "title": gap_label,
            "is_unselected": True,
            "is_muted": is_muted,
            "fade_in": 0.0,
            "fade_out": 0.0,
            "fade_curve": "linear",
        })

    return clips


def _build_reaper_track_block(
    track_name: str,
    clips: List[Dict[str, Any]],
    source_type: str,
    media_name_only: str,
) -> List[str]:
    """Generate a clean Cockos REAPER <TRACK block with media items, fades, and source offsets."""
    track_guid = f"{{{str(uuid.uuid4()).upper()}}}"
    clean_track_name = track_name.replace('"', "'")

    lines: List[str] = [
        f'  <TRACK {track_guid}',
        f'    NAME "{clean_track_name}"',
        '    PEAKCOL 16576',
        '    BEAT -1',
        '    VOLPAN 1 0 -1 -1 1',
        '    MUTESOLO 0 0 0',
        '    IPHASE 0',
    ]

    for clip in clips:
        start = clip["start"]
        end = clip["end"]
        length = max(0.001, end - start)
        title = clip["title"].replace('"', "'")
        item_guid = f"{{{str(uuid.uuid4()).upper()}}}"
        mute_val = 1 if clip.get("is_muted") else 0
        f_in = clip.get("fade_in", 0.0)
        f_out = clip.get("fade_out", 0.0)
        c_in = _reaper_fade_curve_index(clip.get("fade_curve", "linear"))
        c_out = _reaper_fade_curve_index(clip.get("fade_curve", "linear"))

        lines.extend([
            '    <ITEM',
            f'      POSITION {start:.6f}',
            '      SNAPOFFS 0.000000',
            f'      LENGTH {length:.6f}',
            '      LOOP 0',
            '      ALLTAKES 0',
            f'      FADEIN {c_in} {f_in:.6f} 0.000000 1 0 0 0',
            f'      FADEOUT {c_out} {f_out:.6f} 0.000000 1 0 0 0',
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
    return lines


def generate_reaper_project(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    apply_fades: bool = True,
    sample_rate: int = 44100,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    track_name: str = "Segmented Stories",
    scope: str = "all_stories",
) -> str:
    """Generate a clean, warning-free Cockos REAPER project file (.rpp) with scope-aware tracks, fades, and regions."""
    norm_scope = str(scope or "all_stories").lower().strip()
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
        f'  SAMPLERATE {int(sample_rate)} 0 0',
        '  TIMEMODE 0 0 -1 30 0',
        f'  <NOTES\n    |{clean_proj_title} - Exported from Radio & TV Story Segmenter\n  >',
    ]

    if norm_scope == "full_and_all_stories":
        # Two tracks: Track 1 = Full Episode with story splits; Track 2 = Story Cuts
        full_clips = build_timeline_clips(
            stories, total_duration, unselected_audio_mode, apply_fades, scope="full"
        )
        lines.extend(_build_reaper_track_block("Full Episode (Splits)", full_clips, source_type, media_name_only))

        story_clips = build_timeline_clips(
            stories, total_duration, unselected_audio_mode="exclude", apply_fades=apply_fades, scope="all_stories"
        )
        lines.extend(_build_reaper_track_block("Story Cuts", story_clips, source_type, media_name_only))

    elif norm_scope == "full":
        # One track: Full Episode with story splits spanning 0:00 to total_duration
        full_clips = build_timeline_clips(
            stories, total_duration, unselected_audio_mode, apply_fades, scope="full"
        )
        lines.extend(_build_reaper_track_block("Full Episode (Splits)", full_clips, source_type, media_name_only))

    else:
        # One track: Isolated story clips
        story_clips = build_timeline_clips(
            stories, total_duration, unselected_audio_mode, apply_fades, scope="all_stories"
        )
        t_name = track_name or "Segmented Stories"
        lines.extend(_build_reaper_track_block(t_name, story_clips, source_type, media_name_only))

    # Generate REAPER Regions for each story across the timeline
    for i, s in enumerate(stories or [], 1):
        s_start = _get_story_start(s)
        s_end = _get_story_end(s, s_start)
        s_title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or f"Story {i}"
        clean_s_title = s_title.replace('"', "'")
        lines.append(f'  MARKER {i} {s_start:.6f} "{clean_s_title}" 1 {s_end:.6f} 1 0')

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
    track_name: str = "Segmented Stories",
    scope: str = "all_stories",
) -> str:
    """Generate a standard Magix Samplitude EDL (v1.5) broadcast edit decision list."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades, scope=scope)
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

        f_in = clip.get("fade_in", 0.0)
        f_out = clip.get("fade_out", 0.0)

        lines.append(
            f'0001    {i:04d}    {src_in_tc}   {src_out_tc}   {dst_in_tc}   {dst_out_tc}   {f_in:06.3f} {f_out:06.3f}   "{title}"\t"{media_name_only}"'
        )

    return "\n".join(lines) + "\n"


def generate_fcp7_xml(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 48000,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    track_name: str = "Segmented Stories",
    scope: str = "all_stories",
) -> str:
    """Generate Final Cut Pro 7 XML (xmeml v5) interchange format for Premiere Pro and Audition."""
    clean_title = _xml_escape(project_title or "Segmented Project")
    clean_track = _xml_escape(track_name or "Segmented Stories")
    media_name = _xml_escape(Path(media_filename or "audio.wav").name)
    timebase = 30

    norm_scope = str(scope or "all_stories").lower().strip()
    if norm_scope == "full_and_all_stories":
        track_configs = [
            ("Full Episode (Splits)", build_timeline_clips(stories, total_duration, unselected_audio_mode, scope="full")),
            ("Story Cuts", build_timeline_clips(stories, total_duration, unselected_audio_mode="exclude", scope="all_stories")),
        ]
    elif norm_scope == "full":
        track_configs = [
            ("Full Episode (Splits)", build_timeline_clips(stories, total_duration, unselected_audio_mode, scope="full")),
        ]
    else:
        track_configs = [
            (clean_track, build_timeline_clips(stories, total_duration, unselected_audio_mode, scope="all_stories")),
        ]

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
    ]

    clip_id_counter = 1
    for t_name, clips in track_configs:
        c_track_esc = _xml_escape(t_name)
        lines.append('        <track>')
        lines.append(f'          <name>{c_track_esc}</name>')

        for clip in clips:
            c_title = _xml_escape(clip["title"])
            start_frame = int(round(clip["start"] * timebase))
            end_frame = int(round(clip["end"] * timebase))
            mute_str = "TRUE" if clip.get("is_muted") else "FALSE"

            lines.extend([
                f'          <clipitem id="clip-{clip_id_counter}">',
                f'            <name>{c_title}</name>',
                f'            <start>{start_frame}</start>',
                f'            <end>{end_frame}</end>',
                f'            <in>{start_frame}</in>',
                f'            <out>{end_frame}</out>',
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
            clip_id_counter += 1

        lines.append('        </track>')

    lines.extend([
        '      </audio>',
        '    </media>',
        '  </sequence>',
        '</xmeml>',
    ])

    return "\n".join(lines) + "\n"


# Backward-compatible alias
generate_audition_xml = generate_fcp7_xml


def generate_fcpxml(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 48000,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    track_name: str = "Segmented Stories",
    scope: str = "all_stories",
) -> str:
    """Generate Apple Final Cut Pro X XML (.fcpxml) format for FCPX, DaVinci Resolve, and Logic Pro."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, scope=scope)
    clean_title = _xml_escape(project_title or "Segmented Project")
    media_name = _xml_escape(Path(media_filename or "audio.wav").name)
    eff_total = max(float(total_duration or 0.0), max((c["end"] for c in clips), default=0.0))
    total_ms = int(round(eff_total * 1000))

    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE fcpxml>',
        '<fcpxml version="1.9">',
        '  <resources>',
        '    <format id="r1" name="FFVideoFormatRateUndefined" frameDuration="1/30s"/>',
        f'    <asset id="r2" name="{media_name}" src="file://{media_name}" hasAudio="1" audioSources="1" audioChannels="2" audioRate="{int(sample_rate)}"/>',
        '  </resources>',
        '  <library>',
        f'    <event name="{clean_title}">',
        f'      <project name="{clean_title}">',
        f'        <sequence format="r1" duration="{total_ms}/1000s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="{int(sample_rate)}">',
        '          <spine>',
    ]

    for clip in clips:
        c_title = _xml_escape(clip["title"])
        start_ms = int(round(clip["start"] * 1000))
        dur_ms = int(round(clip["duration"] * 1000))
        enabled_attr = ' enabled="0"' if clip.get("is_muted") else ''

        lines.append(
            f'            <asset-clip ref="r2" offset="{start_ms}/1000s" name="{c_title}" start="{start_ms}/1000s" duration="{dur_ms}/1000s" audioRole="dialogue"{enabled_attr}>'
        )
        lines.append(
            f'              <marker start="{start_ms}/1000s" duration="0s" value="{c_title}"/>'
        )
        lines.append('            </asset-clip>')

    lines.extend([
        '          </spine>',
        '        </sequence>',
        '      </project>',
        '    </event>',
        '  </library>',
        '</fcpxml>',
    ])

    return "\n".join(lines) + "\n"


def generate_aaf_interchange(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 48000,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    track_name: str = "Segmented Stories",
    scope: str = "all_stories",
) -> str:
    """Generate Universal AAF XML Interchange format (.aaf) for Avid Media Composer and Pro Tools."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, scope=scope)
    clean_title = _xml_escape(project_title or "Segmented Project")
    clean_track = _xml_escape(track_name or "Segmented Stories")
    media_name = _xml_escape(Path(media_filename or "audio.wav").name)

    comp_mob_id = f"urn:smpte:umid:060a2b34.01010105.01010f20.13000000.{uuid.uuid4().hex[:16]}"
    master_mob_id = f"urn:smpte:umid:060a2b34.01010105.01010f20.13000000.{uuid.uuid4().hex[:16]}"
    timebase = 30

    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<AAF xmlns="http://www.amwa.tv/standards/rules/aaf" version="1.1">',
        '  <Header>',
        '    <Identification>',
        '      <ApplicationName>Radio &amp; TV Story Segmenter</ApplicationName>',
        '      <ApplicationVersion>3.8.9</ApplicationVersion>',
        '    </Identification>',
        '    <ContentStorage>',
        '      <Mob>',
        f'        <CompositionMob id="{comp_mob_id}">',
        f'          <Name>{clean_title}</Name>',
        '          <Slots>',
        f'            <TimelineMobSlot slotID="1" name="{clean_track}">',
        '              <Segment>',
        '                <Sequence>',
        '                  <Components>',
    ]

    for clip in clips:
        c_title = _xml_escape(clip["title"])
        start_frame = int(round(clip["start"] * timebase))
        dur_frame = max(1, int(round(clip["duration"] * timebase)))

        lines.extend([
            f'                    <SourceClip length="{dur_frame}">',
            f'                      <Name>{c_title}</Name>',
            f'                      <SourceID>{master_mob_id}</SourceID>',
            f'                      <StartTime>{start_frame}</StartTime>',
            '                    </SourceClip>',
        ])

    lines.extend([
        '                  </Components>',
        '                </Sequence>',
        '              </Segment>',
        '            </TimelineMobSlot>',
        '          </Slots>',
        '        </CompositionMob>',
        f'        <MasterMob id="{master_mob_id}">',
        f'          <Name>{media_name}</Name>',
        f'          <NetworkLocator url="{media_name}"/>',
        '        </MasterMob>',
        '      </Mob>',
        '    </ContentStorage>',
        '  </Header>',
        '</AAF>',
    ])

    return "\n".join(lines) + "\n"


def generate_hindenburg_session(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    sample_rate: int = 44100,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    track_name: str = "Segmented Stories",
    apply_fades: bool = True,
    scope: str = "all_stories",
) -> str:
    """Generate a Hindenburg Broadcast Session (.nhx) for Hindenburg Journalist and Broadcaster."""
    clean_title = _xml_escape(project_title or "Segmented Project")
    clean_track = _xml_escape(track_name or "Segmented Stories")
    media_name = _xml_escape(Path(media_filename or "audio.wav").name)

    norm_scope = str(scope or "all_stories").lower().strip()
    if norm_scope == "full_and_all_stories":
        track_configs = [
            ("Full Episode (Splits)", build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades=apply_fades, scope="full")),
            ("Story Cuts", build_timeline_clips(stories, total_duration, unselected_audio_mode="exclude", apply_fades=apply_fades, scope="all_stories")),
        ]
    elif norm_scope == "full":
        track_configs = [
            ("Full Episode (Splits)", build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades=apply_fades, scope="full")),
        ]
    else:
        track_configs = [
            (clean_track, build_timeline_clips(stories, total_duration, unselected_audio_mode, apply_fades=apply_fades, scope="all_stories")),
        ]

    lines: List[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<Session version="1.0" sampleRate="{int(sample_rate)}" channels="2">',
        f'  <Project name="{clean_title}">',
        '    <Tracks>',
    ]

    for t_name, clips in track_configs:
        t_name_esc = _xml_escape(t_name)
        lines.append(f'      <Track name="{t_name_esc}" volume="1.0" pan="0.0" muted="0">')
        lines.append('        <Clips>')
        for clip in clips:
            c_title = _xml_escape(clip["title"])
            mute_val = 1 if clip.get("is_muted") else 0
            f_in = clip.get("fade_in", 0.0)
            f_out = clip.get("fade_out", 0.0)
            lines.append(
                f'          <Clip name="{c_title}" file="{media_name}" start="{clip["start"]:.6f}" length="{clip["duration"]:.6f}" offset="{clip["start"]:.6f}" fadeIn="{f_in:.6f}" fadeOut="{f_out:.6f}" mute="{mute_val}"/>'
            )
        lines.append('        </Clips>')
        lines.append('      </Track>')

    lines.extend([
        '    </Tracks>',
        '    <Markers>',
    ])

    # Markers for stories
    for i, s in enumerate(stories or [], 1):
        s_start = _get_story_start(s)
        s_end = _get_story_end(s, s_start)
        s_dur = max(0.0, s_end - s_start)
        s_title = str(getattr(s, "title", "") if not isinstance(s, dict) else s.get("title", "")).strip() or f"Story {i}"
        c_title = _xml_escape(s_title)
        lines.append(
            f'      <Marker name="{c_title}" time="{s_start:.6f}" duration="{s_dur:.6f}"/>'
        )

    lines.extend([
        '    </Markers>',
        '  </Project>',
        '</Session>',
    ])

    return "\n".join(lines) + "\n"


def generate_audacity_labels(
    stories: list,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    scope: str = "all_stories",
) -> str:
    """Generate an Audacity Label Track (.txt) import file."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, scope=scope)
    lines: List[str] = []
    for clip in clips:
        lines.append(f"{clip['start']:.6f}\t{clip['end']:.6f}\t{clip['title']}")
    return "\n".join(lines) + ("\n" if lines else "")


def generate_cue_sheet(
    stories: list,
    media_filename: str = "",
    project_title: str = "Segmented Project",
    total_duration: float = 0.0,
) -> str:
    """Generate a standard Red Book Audio CD CUE sheet (.cue)."""
    return generate_cue_content(
        stories,
        media_filename=media_filename or "audio.wav",
        project_title=project_title or "Segmented Project",
    )


def generate_daw_marker_csv(
    stories: list,
    total_duration: float = 0.0,
    unselected_audio_mode: str = "exclude",
    scope: str = "all_stories",
) -> str:
    """Generate a Universal DAW & NLE Marker List (.csv) format."""
    clips = build_timeline_clips(stories, total_duration, unselected_audio_mode, scope=scope)
    lines: List[str] = [
        '"Marker Name","Start Time (s)","End Time (s)","Duration (s)","Type","Status"',
    ]

    for clip in clips:
        t_type = "Unselected" if clip.get("is_unselected") else "Story"
        t_status = "Muted" if clip.get("is_muted") else "Active"
        dur = max(0.0, clip["end"] - clip["start"])
        name_clean = clip["title"].replace('"', '""')
        lines.append(
            f'"{name_clean}","{clip["start"]:.3f}","{clip["end"]:.3f}","{dur:.3f}","{t_type}","{t_status}"'
        )

    return "\n".join(lines) + "\n"

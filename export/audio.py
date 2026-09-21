"""Radio & TV Story Segmenter — Broadcast Audio Rendering & Stem Processing.

Handles audio extraction, format transcoding, fade application, and stem rendering.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

from prs_shared import ffmpeg_path, safe_filename


def build_audio_fade_filter(
    duration: float,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    fade_curve: str = "linear",
) -> List[str]:
    """Build FFmpeg audio filter strings for fade in and fade out."""
    filters = []
    duration = max(0.0, float(duration))
    fin = max(0.0, min(float(fade_in or 0.0), duration))
    fout = max(0.0, min(float(fade_out or 0.0), max(0.0, duration - fin)))

    # Map curve types to FFmpeg curve parameters where applicable
    # Supported: tri (triangle/linear), qsin (quarter sine), esin (exponential sine), log (logarithmic)
    curve_map = {
        "linear": "tri",
        "exponential": "log",
        "logarithmic": "log",
        "s_curve": "qsin",
    }
    c_param = curve_map.get(str(fade_curve).lower(), "tri")

    if fin > 0:
        filters.append(f"afade=t=in:ss=0:d={fin:.3f}:curve={c_param}")
    if fout > 0:
        fout_start = max(0.0, duration - fout)
        filters.append(f"afade=t=out:st={fout_start:.3f}:d={fout:.3f}:curve={c_param}")

    return filters


def export_audio_track(
    source_media: str | Path,
    output_file: str | Path,
    start: float,
    end: float,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    fade_curve: str = "linear",
    fades_enabled: bool = True,
    is_video: bool = False,
    timeout_sec: int = 1800,
) -> None:
    """Render a segmented audio or video track with optional audio fades."""
    source_path = Path(source_media)
    if not source_path.is_file():
        raise RuntimeError(f"Source media file not found: {source_media}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.0, float(end) - float(start))
    if duration <= 0:
        raise RuntimeError("The selected media range is empty.")

    ext = output_path.suffix.lower()
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    ff_bin = ffmpeg_path() or "ffmpeg"

    fin = fade_in if fades_enabled else 0.0
    fout = fade_out if fades_enabled else 0.0
    af_chain = build_audio_fade_filter(duration, fin, fout, fade_curve)

    # Fast-path: stream-copy when no audio filters are needed and format matches
    if not af_chain:
        copy_cmd = [
            ff_bin, "-y", "-ss", str(start), "-i", str(source_path),
            "-t", str(duration), "-map", "0", "-c", "copy", str(output_path),
        ]
        result = subprocess.run(
            copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout_sec, creationflags=creationflags,
        )
        if result.returncode == 0:
            return

    af_args = ["-af", ",".join(af_chain)] if af_chain else []

    # When exporting video with audio fades, keep video stream copied where possible
    if is_video or ext in {".mp4", ".mov", ".webm", ".mkv", ".avi"}:
        if ext == ".webm":
            audio_codec = ["-c:a", "libopus"]
            fallback_vcodec = ["-c:v", "libvpx-vp9"]
        else:
            audio_codec = ["-c:a", "aac", "-b:a", "192k"]
            fallback_vcodec = ["-c:v", "libx264"]

        # Try stream-copying video while filtering audio
        video_copy_cmd = [
            ff_bin, "-y", "-ss", str(start), "-i", str(source_path),
            "-t", str(duration), "-map", "0", "-c:v", "copy",
        ] + audio_codec + af_args + [str(output_path)]

        res_vcopy = subprocess.run(
            video_copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout_sec, creationflags=creationflags,
        )
        if res_vcopy.returncode == 0:
            return

        # Fallback to full transcode if video copy failed
        transcode_cmd = [
            ff_bin, "-y", "-ss", str(start), "-i", str(source_path),
            "-t", str(duration), "-map", "0",
        ] + fallback_vcodec + audio_codec + af_args + [str(output_path)]

        result2 = subprocess.run(
            transcode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout_sec, creationflags=creationflags,
        )
        if result2.returncode != 0:
            raise RuntimeError(result2.stderr or res_vcopy.stderr)
        return

    # Audio-only containers
    audio_codecs = {
        ".wav": ["-c:a", "pcm_s16le"],
        ".mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
        ".flac": ["-c:a", "flac"],
        ".m4a": ["-c:a", "aac", "-b:a", "192k"],
        ".ogg": ["-c:a", "libvorbis"],
        ".aac": ["-c:a", "aac", "-b:a", "192k"],
    }
    codec_args = audio_codecs.get(ext, ["-c:a", "aac", "-b:a", "192k"])
    transcode_cmd = [
        ff_bin, "-y", "-ss", str(start), "-i", str(source_path),
        "-t", str(duration), "-map", "0:a",
    ] + codec_args + af_args + [str(output_path)]

    result2 = subprocess.run(
        transcode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=timeout_sec, creationflags=creationflags,
    )
    if result2.returncode != 0:
        raise RuntimeError(result2.stderr)


def extract_audio_clip(
    source_media: str | Path,
    start: float,
    end: float,
    output_file: str | Path,
    timeout_sec: int = 600,
) -> None:
    """Extract an audio clip without filtering (fast helper)."""
    duration = float(end) - float(start)
    ff_bin = ffmpeg_path() or "ffmpeg"
    command = [
        ff_bin, "-y", "-ss", str(start), "-i", str(source_media),
        "-t", str(duration), "-vn", "-codec:a", "libmp3lame", "-q:a", "2",
        str(output_file),
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=timeout_sec, creationflags=creationflags,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

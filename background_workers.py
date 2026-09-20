"""Radio & TV Story Segmenter — Background Worker Threads & Waveform Cache Helpers.

Extracted from prs_shared.py as part of Phase 2 Modularization.

Provides:
- StoryAutoDetectWorker: Background audio interval/energy story boundary detector thread.
- get_waveform_peak_cache_path: Compute atomic cache file path for audio peaks.
- read_waveform_peak_cache: Read cached waveform peak envelope from binary cache.
- write_waveform_peak_cache: Write waveform peak envelope to binary cache with atomic rename.
- invalidate_waveform_peak_cache: Invalidate and delete cached waveform peak files.
- WaveformWorker: Background audio waveform peak extraction worker thread using FFmpeg.
- VideoThumbnailWorker: Background video frame thumbnail extraction worker thread.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
from math import gcd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtCore import QObject, Signal

# Optional numeric/audio/scientific libraries
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    import torch
except ImportError:
    torch = None

try:
    from scipy.signal import resample_poly
except ImportError:
    resample_poly = None

# Core utilities & process lifecycle
from core_utils import (
    get_app_data_dir,
    safe_replace,
    ffmpeg_path,
    ffprobe_path,
)
from bootstrap import setup_windows_dll_directories
from runtime_manager import (
    register_process,
    unregister_process,
)
from timeline_widgets import (
    WaveformEnvelope,
    build_waveform_pyramid,
)

# Waveform Peak Cache Binary Format Constants
PEAKS_MAGIC = b"RTVSPEAK"
PEAKS_VERSION = 1
WAVEFORM_ANALYSIS_RATE = 8000
WAVEFORM_POINTS_PER_SECOND = 200

try:
    from prs_shared import Story
except ImportError:
    class Story:  # type: ignore
        def __init__(self, start=0.0, end=0.0, title="", summary="", **kwargs):
            self.start = float(start)
            self.end = float(end)
            self.title = title
            self.summary = summary
            for k, v in kwargs.items():
                setattr(self, k, v)


class StoryAutoDetectWorker(QObject):
    finished = Signal(list)
    progress = Signal((str, int), (str,))
    error = Signal(str)

    # Filter out Whisper music notes and non-speech sound tags
    MUSIC_TOKEN_RE = re.compile(
        r"^([♪♫♬\s]+|\[(?:music|applause|laughter|cheering|sound|singing|theme)\]|\((?:music|applause|laughter|singing)\))$",
        re.IGNORECASE
    )

    def __init__(
        self,
        audio_file,
        silence_threshold=3.0,
        lead_in_padding=0.5,
        audio_duration=0,
        transcript_segments=None,
        whisper_model="parakeet-onnx",
        detection_mode="voice",
        **kwargs,
    ):
        super().__init__()
        self.audio_file = str(audio_file)
        self.silence_threshold = float(silence_threshold or 3.0)
        self.lead_in_padding = float(lead_in_padding or 0.5)
        self.audio_duration = float(audio_duration or 0.0)
        self.transcript_segments = transcript_segments or []
        self.whisper_model = whisper_model or "parakeet-onnx"
        self.detection_mode = str(detection_mode or "voice").strip().lower()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _emit_progress(self, message: str, percent: int = 0):
        if self._is_cancelled:
            return
        pct = max(0, min(100, int(percent)))
        try:
            self.progress.emit(str(message), pct)
        except Exception:
            try:
                self.progress.emit(str(message))
            except Exception:
                pass
        try:
            self.progress[str].emit(str(message))
        except Exception:
            pass

    def _is_real_speech(self, text: str) -> bool:
        txt = str(text).strip()
        if not txt or self.MUSIC_TOKEN_RE.match(txt):
            return False
        if all(ch in "♪♫♬ \t\r\n" for ch in txt):
            return False
        return True

    def run(self):
        try:
            if self._is_cancelled:
                self.error.emit("Process canceled by user.")
                return

            detected_stories = []

            if not self.audio_file or not os.path.isfile(self.audio_file):
                raise FileNotFoundError(f"Audio file not found: {self.audio_file}")

            self._emit_progress("[Step 1/2] Detecting speech activity...", 25)

            speech_timestamps = None
            total_dur = self.audio_duration

            # Step 1: Read and normalize audio to 16kHz mono float32
            audio_data = None
            sample_rate = 16000

            try:
                setup_windows_dll_directories()
                import soundfile as sf
                audio_data, file_sr = sf.read(str(self.audio_file), dtype="float32")
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=-1)
                sample_rate = file_sr
            except Exception:
                # Fallback to FFmpeg decode if soundfile cannot read container/codec
                try:
                    import subprocess
                    import numpy as np
                    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
                    cmd = [
                        ffmpeg_bin, "-y", "-v", "error",
                        "-i", str(self.audio_file),
                        "-vn", "-sn", "-dn",
                        "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"
                    ]
                    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                    if p.returncode == 0 and len(p.stdout) > 0:
                        audio_data = np.frombuffer(p.stdout, dtype=np.float32)
                        sample_rate = 16000
                except Exception:
                    pass

            if audio_data is not None and len(audio_data) > 0:
                if sample_rate != 16000:
                    try:
                        from scipy.signal import resample_poly
                        from math import gcd
                        g = gcd(sample_rate, 16000)
                        audio_data = resample_poly(audio_data, 16000 // g, sample_rate // g).astype("float32")
                        sample_rate = 16000
                    except Exception:
                        pass

                total_dur = max(float(len(audio_data)) / 16000.0, self.audio_duration)

                # Try Neural Silero VAD (ONNX or Torch)
                try:
                    import torch
                    import numpy as np
                    from silero_vad import load_silero_vad, get_speech_timestamps
                    try:
                        if isinstance(audio_data, np.ndarray):
                            if not audio_data.flags.writeable or not audio_data.flags.c_contiguous:
                                audio_data = np.ascontiguousarray(audio_data, dtype=np.float32).copy()
                        wav = torch.from_numpy(audio_data)
                    except (RuntimeError, UserWarning, AttributeError, Exception):
                        try:
                            wav = torch.as_tensor(audio_data, dtype=torch.float32)
                        except (RuntimeError, UserWarning, AttributeError, Exception):
                            wav = torch.tensor(audio_data.tolist(), dtype=torch.float32)
                    try:
                        vad_model = load_silero_vad(onnx=True)
                    except Exception:
                        vad_model = load_silero_vad()

                    speech_timestamps = get_speech_timestamps(
                        wav,
                        vad_model,
                        sampling_rate=16000,
                        min_speech_duration_ms=250,
                        min_silence_duration_ms=400,
                        return_seconds=True,
                    )
                except Exception as vad_err:
                    self._emit_progress(
                        f"[Step 1/2] Neural voice detection unavailable ({type(vad_err).__name__}: {vad_err}); "
                        "falling back to a lower-accuracy volume-based detector for this file. "
                        "Background music or noise may prevent story breaks from being detected correctly.",
                        30,
                    )
                    # Pure NumPy / SciPy acoustic energy envelope fallback (no neural deps needed)
                    try:
                        import numpy as np
                        chunk_size = int(16000 * 0.1)  # 100ms frames
                        num_chunks = len(audio_data) // chunk_size
                        if num_chunks > 0:
                            chunks = audio_data[:num_chunks * chunk_size].reshape(num_chunks, chunk_size)
                            rms = np.sqrt(np.mean(chunks ** 2, axis=1) + 1e-12)
                            db = 20 * np.log10(rms + 1e-12)
                            silence_thresh_db = np.percentile(db, 20) + 6.0
                            is_speech = db > silence_thresh_db

                            raw_intervals = []
                            in_speech = False
                            start_f = 0
                            for f_idx, val in enumerate(is_speech):
                                if val and not in_speech:
                                    in_speech = True
                                    start_f = f_idx
                                elif not val and in_speech:
                                    in_speech = False
                                    raw_intervals.append({
                                        "start": round(start_f * 0.1, 2),
                                        "end": round(f_idx * 0.1, 2)
                                    })
                            if in_speech:
                                raw_intervals.append({
                                    "start": round(start_f * 0.1, 2),
                                    "end": round(num_chunks * 0.1, 2)
                                })
                            speech_timestamps = raw_intervals
                    except Exception:
                        pass

            if not speech_timestamps and self.transcript_segments:
                speech_timestamps = []
                for seg in self.transcript_segments:
                    text = seg.get("text", "")
                    if self._is_real_speech(text):
                        speech_timestamps.append({
                            "start": float(seg.get("start", 0.0)),
                            "end": float(seg.get("end", 0.0)),
                        })

            if self.detection_mode == "music":
                self._emit_progress("[Step 2/2] Detecting songs and track boundaries...", 80)
                # Music Mode: Detect song segments separated by non-musical transitions
                # (silence, dialog-only speech, or non-musical sounds lasting >= silence_threshold).
                music_hint_intervals = []
                if self.transcript_segments:
                    for seg in self.transcript_segments:
                        txt = seg.get("text", "")
                        st = float(seg.get("start", 0.0))
                        et = float(seg.get("end", 0.0))
                        if not self._is_real_speech(txt):
                            music_hint_intervals.append((st, et))

                frame_dur = 0.5
                num_frames = int(max(1, math.ceil(total_dur / frame_dur))) if total_dur > 0 else 0
                frame_is_music = [False] * num_frames

                if audio_data is not None and len(audio_data) > 0 and sample_rate > 0:
                    samples_per_frame = int(sample_rate * frame_dur)
                    rms_list = []
                    try:
                        import numpy as np
                        has_np = isinstance(audio_data, np.ndarray)
                    except Exception:
                        has_np = False

                    for f in range(num_frames):
                        s_idx = f * samples_per_frame
                        e_idx = min(len(audio_data), (f + 1) * samples_per_frame)
                        chunk = audio_data[s_idx:e_idx]
                        if len(chunk) > 0:
                            if has_np:
                                rms_val = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
                            else:
                                rms_val = math.sqrt(sum(float(x) ** 2 for x in chunk) / len(chunk) + 1e-12)
                            rms_list.append(rms_val)
                        else:
                            rms_list.append(0.0)

                    sorted_rms = sorted(rms_list)
                    silence_rms = sorted_rms[int(len(sorted_rms) * 0.12)] if sorted_rms else 0.001
                    silence_rms = max(silence_rms, 0.002)

                    window_radius = 2  # +/- 2 frames = 2.0s rolling window
                    for f in range(num_frames):
                        f_start = f * frame_dur
                        f_end = (f + 1) * frame_dur
                        f_rms = rms_list[f] if f < len(rms_list) else 0.0

                        if f_rms < silence_rms:
                            frame_is_music[f] = False
                            continue

                        in_speech = False
                        if speech_timestamps:
                            in_speech = any(
                                not (f_end <= sp["start"] or f_start >= sp["end"])
                                for sp in speech_timestamps
                            )

                        w_start = max(0, f - window_radius)
                        w_end = min(num_frames, f + window_radius + 1)
                        w_vals = rms_list[w_start:w_end]
                        min_w = min(w_vals) if w_vals else 0.0
                        max_w = max(w_vals) if w_vals else 1.0
                        valley_ratio = min_w / (max_w + 1e-6)

                        has_music_hint = any(
                            not (f_end <= mh[0] or f_start >= mh[1])
                            for mh in music_hint_intervals
                        )

                        if has_music_hint:
                            frame_is_music[f] = True
                        elif not in_speech:
                            # Sustained non-speech acoustic energy -> music instrumental/song
                            frame_is_music[f] = True
                        else:
                            # Speech active: check if accompanied by continuous musical rhythm
                            frame_is_music[f] = bool(valley_ratio >= 0.22)

                elif music_hint_intervals:
                    for f in range(num_frames):
                        f_start = f * frame_dur
                        f_end = (f + 1) * frame_dur
                        frame_is_music[f] = any(
                            not (f_end <= mh[0] or f_start >= mh[1])
                            for mh in music_hint_intervals
                        )

                min_break_frames = max(2, int(round(float(self.silence_threshold) / frame_dur)))
                music_intervals = []
                in_music = False
                seg_start_f = 0
                non_music_gap_count = 0

                for f_idx, is_mus in enumerate(frame_is_music):
                    if is_mus:
                        if not in_music:
                            in_music = True
                            seg_start_f = f_idx
                        non_music_gap_count = 0
                    else:
                        if in_music:
                            non_music_gap_count += 1
                            if non_music_gap_count >= min_break_frames:
                                seg_end_f = f_idx - non_music_gap_count + 1
                                music_intervals.append((
                                    round(seg_start_f * frame_dur, 2),
                                    round(seg_end_f * frame_dur, 2)
                                ))
                                in_music = False
                                non_music_gap_count = 0

                if in_music:
                    music_intervals.append((
                        round(seg_start_f * frame_dur, 2),
                        round(len(frame_is_music) * frame_dur, 2)
                    ))

                for idx, (mst, met) in enumerate(music_intervals):
                    st = max(0.0, mst - self.lead_in_padding)
                    et = min(total_dur, met + min(0.3, self.lead_in_padding))
                    if et - st >= 5.0:
                        detected_stories.append(Story(
                            start=round(st, 2),
                            end=round(et, 2),
                            title=f"Song {len(detected_stories) + 1}"
                        ))

            # Voice Mode or fallback if no music intervals detected
            if not detected_stories and speech_timestamps:
                self._emit_progress("[Step 2/2] Assembling stories from vocal intervals...", 85)
                story_starts = [max(0.0, speech_timestamps[0]["start"] - self.lead_in_padding)]
                story_ends = []
                target_gap = max(1.0, float(self.silence_threshold))

                for i in range(len(speech_timestamps) - 1):
                    if self._is_cancelled:
                        self.error.emit("Process canceled by user.")
                        return

                    curr_speech_end = speech_timestamps[i]["end"]
                    next_speech_start = speech_timestamps[i + 1]["start"]
                    gap = next_speech_start - curr_speech_end

                    if gap >= target_gap:
                        story_ends.append(curr_speech_end + min(0.3, self.lead_in_padding))
                        story_starts.append(max(0.0, next_speech_start - self.lead_in_padding))

                story_ends.append(max(float(speech_timestamps[-1]["end"]), total_dur))

                for idx, (st, et) in enumerate(zip(story_starts, story_ends)):
                    if et - st >= 3.0:  # Minimum story duration filter
                        detected_stories.append(Story(
                            start=round(st, 2),
                            end=round(et, 2),
                            title=f"Story {len(detected_stories) + 1}"
                        ))

            if not detected_stories and total_dur > 0:
                detected_stories = [Story(start=0.0, end=round(total_dur, 2), title="Story 1")]

            self._emit_progress("Story detection complete.", 100)
            self.finished.emit(detected_stories)

        except Exception as exc:
            if not self._is_cancelled:
                self.error.emit(str(exc))

# ============================================================
# Transcription worker
# ============================================================

# Transcription is executed by the same isolated local helper process used
# for Speaker Detection. This keeps ML model loading out of the Qt GUI process.



# ============================================================
# Speaker diarization worker
# ============================================================



# ============================================================
# Waveform Extraction Worker & Binary Peak Cache (.peaks)
# ============================================================

PEAKS_MAGIC = b"RTVSPEAK"
PEAKS_VERSION = 1

def get_waveform_peak_cache_path(audio_file, project_file=None):
    """
    Return local project or appdata path for waveform peak binary cache file.
    Prefers project-local hidden cache <Project>/.cache/peaks/<media_stem>.peaks,
    falling back to user appdata cache. Never creates .cache inside standalone media folders.
    """
    if not audio_file:
        return None
    try:
        audio_p = Path(audio_file).resolve()
        
        # 1. If explicit project_file provided, store in project folder's .cache/peaks/
        if project_file:
            proj_p = Path(project_file).resolve()
            proj_dir = proj_p.parent if (proj_p.is_file() or proj_p.suffix.lower() in ('.rtvs', '.json')) else proj_p
            if proj_dir.exists() and os.access(str(proj_dir), os.W_OK):
                cache_peaks_dir = proj_dir / ".cache" / "peaks"
                cache_peaks_dir.mkdir(parents=True, exist_ok=True)
                if sys.platform == "win32":
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(str(proj_dir / ".cache"), 0x02)
                    except Exception:
                        pass
                return cache_peaks_dir / f"{audio_p.stem}.peaks"

        # 2. Check if audio_file is located inside an existing project folder bundle
        candidate_proj = None
        if audio_p.parent.name.lower() in ("media", "audio"):
            if list(audio_p.parent.parent.glob("*.rtvs")) or (audio_p.parent.parent / ".cache").exists():
                candidate_proj = audio_p.parent.parent
        elif list(audio_p.parent.glob("*.rtvs")) or (audio_p.parent / ".cache").exists():
            candidate_proj = audio_p.parent

        if candidate_proj and candidate_proj.exists() and os.access(str(candidate_proj), os.W_OK):
            cache_peaks_dir = candidate_proj / ".cache" / "peaks"
            cache_peaks_dir.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(str(candidate_proj / ".cache"), 0x02)
                except Exception:
                    pass
            return cache_peaks_dir / f"{audio_p.stem}.peaks"
    except Exception:
        pass

    # 3. Safe fallback: global AppData cache (never write into arbitrary media folders)
    try:
        cache_dir = get_app_data_dir() / "cache" / "peaks"
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(str(audio_file).encode("utf-8")).hexdigest()[:16]
        return cache_dir / f"{key}_{Path(audio_file).stem}.peaks"
    except Exception:
        return None

from timeline_widgets import WaveformEnvelope, build_waveform_pyramid


def read_waveform_peak_cache(audio_file, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
    """
    Read cached waveform peak envelope from binary cache.
    Returns list of float peaks or None if cache is missing or stale.
    Supports transparent migration from legacy adjacent .peaks files.
    """
    cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
    audio_p = Path(audio_file) if audio_file else None
    
    # Check if primary cache path exists, otherwise look for legacy adjacent file or appdata fallback
    candidate_paths = []
    if cache_path:
        candidate_paths.append((cache_path, False))
    if audio_p:
        # Fallback to appdata cache
        try:
            appdata_p = get_app_data_dir() / "cache" / "peaks" / f"{hashlib.sha256(str(audio_file).encode('utf-8')).hexdigest()[:16]}_{audio_p.stem}.peaks"
            if appdata_p != cache_path:
                candidate_paths.append((appdata_p, False))
        except Exception:
            pass
        legacy_path = audio_p.with_name(audio_p.name + ".peaks")
        if legacy_path != cache_path:
            candidate_paths.append((legacy_path, True))

    for p, is_legacy in candidate_paths:
        if not p.exists():
            continue
        try:
            if audio_p and audio_p.exists() and audio_p.stat().st_mtime > p.stat().st_mtime:
                continue
            with open(p, "rb") as f:
                magic = f.read(8)
                if magic != PEAKS_MAGIC:
                    continue
                header_bytes = f.read(10)
                if len(header_bytes) < 10:
                    continue
                version, pps, count = struct.unpack("<HfI", header_bytes)
                if version != PEAKS_VERSION or count == 0:
                    continue
                raw_data = f.read(count * 4)
                if len(raw_data) != count * 4:
                    continue
                peaks = list(struct.unpack(f"<{count}f", raw_data))
                levels = build_waveform_pyramid(peaks)
                envelope = WaveformEnvelope(peaks, levels=levels)
                # If read from legacy path, migrate to project .cache/peaks/ atomically
                if is_legacy and cache_path and not cache_path.exists():
                    write_waveform_peak_cache(audio_file, peaks, points_per_second=pps, project_file=project_file)
                return envelope
        except Exception:
            continue
    return None

def write_waveform_peak_cache(audio_file, peaks, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
    """
    Write waveform peak envelope to binary cache with atomic rename.
    """
    if not audio_file or not peaks:
        return
    try:
        cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
        if not cache_path:
            return
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = cache_path.with_name(cache_path.name + ".tmp")
        count = len(peaks)
        with open(tmp_path, "wb") as f:
            f.write(PEAKS_MAGIC)
            f.write(struct.pack("<HfI", PEAKS_VERSION, float(points_per_second), count))
            f.write(struct.pack(f"<{count}f", *peaks))
            f.flush()
            os.fsync(f.fileno())
        safe_replace(tmp_path, cache_path)
    except Exception:
        pass


def invalidate_waveform_peak_cache(audio_file, project_file=None):
    """Delete any cached waveform peak binary file for audio_file, including legacy paths."""
    deleted = False
    try:
        cache_path = get_waveform_peak_cache_path(audio_file, project_file=project_file)
        if cache_path and cache_path.exists():
            cache_path.unlink(missing_ok=True)
            deleted = True
        if audio_file:
            audio_p = Path(audio_file)
            legacy_p = audio_p.with_name(audio_p.name + ".peaks")
            if legacy_p.exists():
                legacy_p.unlink(missing_ok=True)
                deleted = True
            appdata_p = get_app_data_dir() / "cache" / "peaks" / f"{hashlib.sha256(str(audio_file).encode('utf-8')).hexdigest()[:16]}_{audio_p.stem}.peaks"
            if appdata_p.exists():
                appdata_p.unlink(missing_ok=True)
                deleted = True
    except Exception:
        pass
    return deleted


class WaveformWorker(QObject):
    finished = Signal(list, bool)

    def __init__(self, audio_file, points_per_second=WAVEFORM_POINTS_PER_SECOND, project_file=None):
        super().__init__()
        self.audio_file = str(audio_file)
        self.points_per_second = points_per_second
        self.project_file = project_file
        self._cancel_event = threading.Event()
        self._process = None

    def cancel(self):
        """Thread-safe cancellation request; also stops the FFmpeg child process."""
        self._cancel_event.set()
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def run(self):
        """Build a compact peak envelope without loading the whole recording into RAM."""
        process = None
        try:
            # Keep the waveform envelope bounded for multi-hour recordings.
            # We still stream decoded PCM through FFmpeg; only the compact peak
            # envelope is retained in memory.
            effective_pps = int(self.points_per_second)
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                probe = subprocess.run(
                    [ffprobe_path() or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", self.audio_file],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10, check=True,
                    creationflags=creationflags,
                )
                duration = float(probe.stdout.strip() or 0)
                max_points = 800_000
                if duration > 0 and duration * effective_pps > max_points:
                    effective_pps = max(20, int(max_points / duration))
            except Exception:
                pass
            samples_per_peak = max(1, WAVEFORM_ANALYSIS_RATE // max(1, effective_pps))
            cmd = [
                ffmpeg_path() or "ffmpeg", "-vn", "-i", self.audio_file,
                "-f", "s16le", "-ac", "1",
                "-ar", str(WAVEFORM_ANALYSIS_RATE),
                "-v", "quiet", "pipe:1",
            ]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1024 * 1024,
                creationflags=creationflags,
            )
            self._process = process
            register_process(process)

            peaks = []
            max_possible_val = 32768.0
            samples_in_peak = 0
            peak_value = 0
            leftover_samples = np.empty(0, dtype=np.int16) if (HAVE_NUMPY and np is not None) else None

            while True:
                if self._cancel_event.is_set():
                    try:
                        process.kill()
                    except Exception:
                        pass
                    process.wait()
                    self.finished.emit([], True)
                    return

                raw = process.stdout.read(128 * 1024)
                if not raw:
                    break

                if self._cancel_event.is_set():
                    try:
                        process.kill()
                    except Exception:
                        pass
                    process.wait()
                    self.finished.emit([], True)
                    return

                if HAVE_NUMPY and np is not None:
                    chunk = np.frombuffer(raw, dtype=np.int16)
                    if chunk.size > 0:
                        if leftover_samples.size > 0:
                            chunk = np.concatenate((leftover_samples, chunk))
                        n_peaks = chunk.size // samples_per_peak
                        if n_peaks > 0:
                            usable = chunk[:n_peaks * samples_per_peak]
                            reshaped = np.abs(usable).reshape(n_peaks, samples_per_peak)
                            chunk_peaks = (np.max(reshaped, axis=1) / max_possible_val).astype(np.float32)
                            peaks.extend(chunk_peaks.tolist())
                            leftover_samples = chunk[n_peaks * samples_per_peak:]
                        else:
                            leftover_samples = chunk
                else:
                    sample_count = len(raw) // 2
                    if sample_count:
                        samples = struct.unpack(f"<{sample_count}h", raw[:sample_count * 2])
                        for sample in samples:
                            peak_value = max(peak_value, abs(sample))
                            samples_in_peak += 1
                            if samples_in_peak == samples_per_peak:
                                peaks.append(peak_value / max_possible_val)
                                samples_in_peak = 0
                                peak_value = 0

            return_code = process.wait()
            if self._cancel_event.is_set():
                self.finished.emit([], True)
                return
            if return_code != 0:
                self.finished.emit([], False)
                return

            if HAVE_NUMPY and np is not None and leftover_samples is not None and leftover_samples.size > 0:
                peaks.append(float(np.max(np.abs(leftover_samples)) / max_possible_val))
            elif samples_in_peak:
                peaks.append(peak_value / max_possible_val)

            if peaks:
                try:
                    write_waveform_peak_cache(self.audio_file, peaks, effective_pps, project_file=self.project_file)
                except Exception:
                    pass

            levels = build_waveform_pyramid(peaks)
            envelope = WaveformEnvelope(peaks, levels=levels)
            self.finished.emit(envelope, False)
        except Exception:
            if process is not None:
                try:
                    process.kill()
                    process.wait()
                except Exception:
                    pass
            self.finished.emit([], self._cancel_event.is_set())
        finally:
            if process is not None:
                unregister_process(process)
            self._process = None


# ============================================================
# Video Thumbnail Caching & Background Extraction
# ============================================================

def get_video_thumbnail_cache_dir(media_file: str | Path | None, project_file: str | Path | None = None) -> Path | None:
    """Return the deterministic thumbnail cache directory for a media file, associating with project if available."""
    if not media_file:
        return None
    try:
        p = Path(media_file).resolve()
        stat = p.stat()
        key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}"
        h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]
        
        # 1. Project-level thumbnail directory
        if project_file:
            proj_p = Path(project_file).resolve()
            proj_dir = proj_p.parent if (proj_p.is_file() or proj_p.suffix.lower() in ('.rtvs', '.json')) else proj_p
            if proj_dir.exists() and os.access(str(proj_dir), os.W_OK):
                base = proj_dir / ".cache" / "thumbnails"
                return base / h

        # 2. Check if media resides in project bundle
        candidate_proj = None
        if p.parent.name.lower() in ("media", "audio"):
            if list(p.parent.parent.glob("*.rtvs")) or (p.parent.parent / ".cache").exists():
                candidate_proj = p.parent.parent
        elif list(p.parent.glob("*.rtvs")) or (p.parent / ".cache").exists():
            candidate_proj = p.parent

        if candidate_proj and candidate_proj.exists() and os.access(str(candidate_proj), os.W_OK):
            base = candidate_proj / ".cache" / "thumbnails"
            return base / h

        # 3. Global AppData / Temp directory fallback
        base = get_app_data_dir() / "cache" / "thumbnails"
        return base / h
    except Exception:
        try:
            h = hashlib.sha256(str(Path(media_file)).encode("utf-8")).hexdigest()[:24]
            base = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
            return base / h
        except Exception:
            return None


def read_video_thumbnail_cache(media_file: str | Path | None, duration: float, project_file: str | Path | None = None) -> list | None:
    """Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.
    
    Returns list of items if the cache exists, contains valid thumbnail images, and is
    not older than the media file; otherwise returns None.
    """
    if not media_file or duration <= 0:
        return None
    try:
        cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file)
        if not cache_dir or not cache_dir.exists() or not cache_dir.is_dir():
            # Try global fallback
            alt_dir = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails" / hashlib.sha256(str(Path(media_file)).encode("utf-8")).hexdigest()[:24]
            if alt_dir.exists() and alt_dir.is_dir():
                cache_dir = alt_dir
            else:
                return None

        media_p = Path(media_file)
        if media_p.exists():
            if media_p.stat().st_mtime > cache_dir.stat().st_mtime:
                return None

        thumbs = sorted(cache_dir.glob("thumb_*.jpg"))
        if not thumbs or len(thumbs) < 2:
            return None

        valid_thumbs = []
        for t in thumbs:
            if t.exists() and t.stat().st_size > 0:
                valid_thumbs.append(t)

        if not valid_thumbs or len(valid_thumbs) != len(thumbs):
            return None

        items = []
        num = len(valid_thumbs)
        for i, p in enumerate(valid_thumbs):
            ts = (i / max(1, num - 1)) * duration if num > 1 else 0.0
            items.append((ts, str(p)))
        return items
    except Exception:
        return None


def invalidate_video_thumbnail_cache(media_file: str | Path | None, project_file: str | Path | None = None) -> bool:
    """Delete the thumbnail cache directory for a given media file."""
    deleted = False
    try:
        cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file)
        if cache_dir and cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            deleted = True
        # Also clean up tempdir thumbnail cache
        if media_file:
            try:
                p = Path(media_file).resolve()
                stat = p.stat()
                key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}"
                h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]
                t_dir = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails" / h
                if t_dir.exists():
                    shutil.rmtree(t_dir, ignore_errors=True)
                    deleted = True
            except Exception:
                pass
    except Exception:
        pass
    return deleted


class VideoThumbnailWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, media_path, duration, output_dir, count=36):
        super().__init__()
        self.media_path = Path(media_path)
        self.duration = max(0.1, float(duration or 0))
        self.output_dir = Path(output_dir)
        self.count = max(8, min(80, int(count)))
        self._cancelled = False
        self._process = None

    def cancel(self):
        self._cancelled = True
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def run(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            fps = self.count / self.duration
            vf = f"fps={fps:.8f},scale=320:-2:force_original_aspect_ratio=decrease"
            pattern = str(self.output_dir / "thumb_%03d.jpg")
            cmd = [ffmpeg_path() or "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(self.media_path), "-map", "0:v:0", "-vf", vf, "-q:v", "4", pattern]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
            register_process(self._process)
            _stdout, stderr = self._process.communicate()
            returncode = self._process.returncode
            if self._cancelled:
                self.finished.emit([])
                return
            if returncode != 0:
                raise RuntimeError(stderr.strip() or "FFmpeg could not create video thumbnails.")
            files = sorted(self.output_dir.glob("thumb_*.jpg"))
            if not files:
                raise RuntimeError("No video thumbnails were generated.")
            actual_count = len(files)
            items = []
            for i, path in enumerate(files):
                if self._cancelled:
                    break
                timestamp = (i / max(1, actual_count - 1)) * self.duration if actual_count > 1 else 0.0
                items.append((timestamp, str(path)))
            self.finished.emit(items)
        except Exception as exc:
            if not self._cancelled:
                self.error.emit(str(exc))
            else:
                self.finished.emit([])
        finally:
            if self._process is not None:
                unregister_process(self._process)
            self._process = None


# ============================================================
# Timeline Widgets (Extracted to timeline_widgets.py)
# ============================================================
from timeline_widgets import (
    TimelineCanvas,
    TimelineResizeHandle,
    TimelineOverviewBar,
    TimelineWidget,
)

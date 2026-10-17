"""worker_story_engine.py - Acoustic & Lexical Story Boundary Detection Engine.

Provides headless, decoupled story and song boundary detection:
- Neural Silero VAD speech activity detection (ONNX & Torch)
- Acoustic energy / RMS envelope fallback detector
- Dual detection modes: 'voice' (spoken stories) and 'music' (songs / tracks)
- Whisper / Parakeet transcript-guided speech interval validation
- Music note and sound tag token filtration
- Automatic boundary padding, silence threshold bridging, and minimum story length filtering
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from story_model import Story
except ImportError:
    from prs_shared import Story  # type: ignore

try:
    from bootstrap import setup_windows_dll_directories
except ImportError:
    def setup_windows_dll_directories():
        pass


# Filter out Whisper music notes and non-speech sound tags
MUSIC_TOKEN_RE = re.compile(
    r"^([♪♫♬\s]+|\[(?:music|applause|laughter|cheering|sound|singing|theme)\]|\((?:music|applause|laughter|singing)\))$",
    re.IGNORECASE,
)


def is_real_speech(text: str) -> bool:
    """Return True if text represents actual spoken words rather than music/sound tokens."""
    txt = str(text).strip()
    if not txt or MUSIC_TOKEN_RE.match(txt):
        return False
    if all(ch in "♪♫♬ \t\r\n" for ch in txt):
        return False
    return True


def detect_story_boundaries(
    audio_file: Union[str, os.PathLike],
    silence_threshold: float = 3.0,
    lead_in_padding: float = 0.5,
    audio_duration: float = 0.0,
    transcript_segments: Optional[List[Dict[str, Any]]] = None,
    whisper_model: str = "parakeet-onnx",
    detection_mode: str = "voice",
    is_cancelled_fn: Optional[Callable[[], bool]] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> List[Story]:
    """Execute acoustic and lexical story boundary detection on an audio file.

    Args:
        audio_file: Path to media file on disk.
        silence_threshold: Minimum silence duration (seconds) defining a story break.
        lead_in_padding: Padding (seconds) prepended to detected story starts.
        audio_duration: Total audio duration if known in advance.
        transcript_segments: Optional list of transcript segments for lexical guidance.
        whisper_model: Model name for acoustic tuning.
        detection_mode: 'voice' for broadcast speech/news, 'music' for song segmentation.
        is_cancelled_fn: Callback returning True if operation was cancelled by user.
        progress_callback: Callback receiving (message, percent) updates.

    Returns:
        List of detected Story instances with start, end, and title.
    """
    def _is_cancelled() -> bool:
        return bool(is_cancelled_fn and is_cancelled_fn())

    def _emit(msg: str, pct: int = 0):
        if progress_callback and not _is_cancelled():
            try:
                progress_callback(str(msg), max(0, min(100, int(pct))))
            except Exception:
                pass

    if _is_cancelled():
        return []

    audio_path = str(audio_file)
    if not audio_path or not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    silence_threshold = float(silence_threshold or 3.0)
    lead_in_padding = float(lead_in_padding or 0.5)
    audio_duration = float(audio_duration or 0.0)
    transcript_segments = transcript_segments or []
    detection_mode = str(detection_mode or "voice").strip().lower()

    _emit("[Step 1/2] Detecting speech activity...", 25)

    speech_timestamps = None
    total_dur = audio_duration
    audio_data = None
    sample_rate = 16000

    # Step 1: Read and normalize audio to 16kHz mono float32
    try:
        setup_windows_dll_directories()
        import soundfile as sf
        audio_data, file_sr = sf.read(audio_path, dtype="float32")
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=-1)
        sample_rate = file_sr
    except Exception:
        # Fallback to FFmpeg decode if soundfile cannot read container/codec
        try:
            import numpy as np
            ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
            cmd = [
                ffmpeg_bin, "-y", "-v", "error",
                "-i", audio_path,
                "-vn", "-sn", "-dn",
                "-ac", "1", "-ar", "16000",
                "-f", "f32le", "-",
            ]
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
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

        total_dur = max(float(len(audio_data)) / 16000.0, audio_duration)

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
            _emit(
                f"[Step 1/2] Neural voice detection unavailable ({type(vad_err).__name__}: {vad_err}); "
                "falling back to acoustic energy detector for this file.",
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
                    is_speech_frame = db > silence_thresh_db

                    raw_intervals = []
                    in_speech = False
                    start_f = 0
                    for f_idx, val in enumerate(is_speech_frame):
                        if val and not in_speech:
                            in_speech = True
                            start_f = f_idx
                        elif not val and in_speech:
                            in_speech = False
                            raw_intervals.append({
                                "start": round(start_f * 0.1, 2),
                                "end": round(f_idx * 0.1, 2),
                            })
                    if in_speech:
                        raw_intervals.append({
                            "start": round(start_f * 0.1, 2),
                            "end": round(num_chunks * 0.1, 2),
                        })
                    speech_timestamps = raw_intervals
            except Exception:
                pass

    if not speech_timestamps and transcript_segments:
        speech_timestamps = []
        for seg in transcript_segments:
            text = seg.get("text", "")
            if is_real_speech(text):
                speech_timestamps.append({
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                })

    detected_stories: List[Story] = []

    if detection_mode == "music":
        _emit("[Step 2/2] Detecting songs and track boundaries...", 80)
        music_hint_intervals = []
        if transcript_segments:
            for seg in transcript_segments:
                txt = seg.get("text", "")
                st = float(seg.get("start", 0.0))
                et = float(seg.get("end", 0.0))
                if not is_real_speech(txt):
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
                    frame_is_music[f] = True
                else:
                    frame_is_music[f] = bool(valley_ratio >= 0.22)

        elif music_hint_intervals:
            for f in range(num_frames):
                f_start = f * frame_dur
                f_end = (f + 1) * frame_dur
                frame_is_music[f] = any(
                    not (f_end <= mh[0] or f_start >= mh[1])
                    for mh in music_hint_intervals
                )

        min_break_frames = max(2, int(round(float(silence_threshold) / frame_dur)))
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
                            round(seg_end_f * frame_dur, 2),
                        ))
                        in_music = False
                        non_music_gap_count = 0

        if in_music:
            music_intervals.append((
                round(seg_start_f * frame_dur, 2),
                round(len(frame_is_music) * frame_dur, 2),
            ))

        for idx, (mst, met) in enumerate(music_intervals):
            st = max(0.0, mst - lead_in_padding)
            et = min(total_dur, met + min(0.3, lead_in_padding))
            if et - st >= 5.0:
                detected_stories.append(Story(
                    start=round(st, 2),
                    end=round(et, 2),
                    title=f"Song {len(detected_stories) + 1}",
                ))

    # Voice Mode or fallback if no music intervals detected
    if not detected_stories and speech_timestamps:
        _emit("[Step 2/2] Assembling stories from vocal intervals...", 85)
        story_starts = [max(0.0, speech_timestamps[0]["start"] - lead_in_padding)]
        story_ends = []
        target_gap = max(1.0, float(silence_threshold))

        for i in range(len(speech_timestamps) - 1):
            if _is_cancelled():
                return []

            curr_speech_end = speech_timestamps[i]["end"]
            next_speech_start = speech_timestamps[i + 1]["start"]
            gap = next_speech_start - curr_speech_end

            if gap >= target_gap:
                story_ends.append(curr_speech_end + min(0.3, lead_in_padding))
                story_starts.append(max(0.0, next_speech_start - lead_in_padding))

        story_ends.append(max(float(speech_timestamps[-1]["end"]), total_dur))

        for idx, (st, et) in enumerate(zip(story_starts, story_ends)):
            if et - st >= 3.0:  # Minimum story duration filter
                detected_stories.append(Story(
                    start=round(st, 2),
                    end=round(et, 2),
                    title=f"Story {len(detected_stories) + 1}",
                ))

    if not detected_stories and total_dur > 0:
        detected_stories = [Story(start=0.0, end=round(total_dur, 2), title="Story 1")]

    _emit("Story detection complete.", 100)
    return detected_stories

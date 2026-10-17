"""benchmark_models.py - Benchmark Data Models, Audio Generators & Hardware Profiler.

Provides:
- BenchmarkMetric & ProcessingEstimates data contracts
- Sample audio downloading, resolution, caching, and disk reclamation
- Zero-disk in-memory synthetic 16kHz speech WAV fixture generator
- FFmpeg PCM audio decode and real-time factor extractor
- Hardware and environment profiler (CPU cores, RAM, GPU/CUDA, ONNX providers)
- Human-readable duration formatting and plugin availability probes
"""

from __future__ import annotations

import io
import json
import math
import os
import platform
import shutil
import struct
import subprocess
import sys
import time
import urllib.request
import wave
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from qt_compat import _ensure_pyside6_fallback

_ensure_pyside6_fallback()

# ---------------------------------------------------------------------------
# Sample Audio Asset Constants & Management
# ---------------------------------------------------------------------------

SAMPLE_AUDIO_FILENAME = "performance_test_audio.mp3"
SAMPLE_AUDIO_URLS = [
    "https://raw.githubusercontent.com/bradlinder/RTVS3/main/samples/performance_test_audio.mp3",
    "https://github.com/bradlinder/RTVS3/raw/main/samples/performance_test_audio.mp3",
    "https://github.com/bradlinder/RTVS3/releases/download/v3.5.0-beta-6/performance_test_audio.mp3",
]


def get_app_data_dir() -> Path:
    """Returns application data directory consistent across platforms."""
    app_id = "RadioTVStorySegmenter"
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / app_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_candidate_sample_audio_paths() -> List[Path]:
    """Returns ordered list of file paths where sample audio may reside."""
    candidates = []
    base_dir = Path(__file__).resolve().parent

    candidates.append(base_dir / "samples" / SAMPLE_AUDIO_FILENAME)
    candidates.append(base_dir / "Performance Test Audio.mp3")
    candidates.append(base_dir / SAMPLE_AUDIO_FILENAME)
    candidates.append(get_app_data_dir() / "samples" / SAMPLE_AUDIO_FILENAME)
    candidates.append(Path.cwd() / "samples" / SAMPLE_AUDIO_FILENAME)
    candidates.append(Path.cwd() / "Performance Test Audio.mp3")

    unique_paths = []
    seen = set()
    for p in candidates:
        abs_p = p.resolve()
        if abs_p not in seen:
            seen.add(abs_p)
            unique_paths.append(p)
    return unique_paths


def find_available_sample_audio() -> Optional[Path]:
    """Finds the first existing valid sample audio file on disk."""
    for p in get_candidate_sample_audio_paths():
        try:
            if p.is_file() and p.stat().st_size > 10000:
                return p
        except Exception:
            pass
    return None


def get_sample_audio_target_path() -> Path:
    """Returns the primary target path for downloading the sample audio file."""
    local_samples = Path(__file__).resolve().parent / "samples"
    try:
        local_samples.mkdir(parents=True, exist_ok=True)
        test_file = local_samples / ".write_test"
        test_file.touch()
        test_file.unlink()
        return local_samples / SAMPLE_AUDIO_FILENAME
    except Exception:
        target_dir = get_app_data_dir() / "samples"
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / SAMPLE_AUDIO_FILENAME


def delete_sample_audio_files() -> Tuple[bool, int, str]:
    """Deletes all sample audio files across candidate locations to free disk space."""
    freed_bytes = 0
    deleted_paths = []
    errors = []

    for p in get_candidate_sample_audio_paths():
        try:
            if p.is_file():
                size = p.stat().st_size
                p.unlink()
                freed_bytes += size
                deleted_paths.append(str(p))
        except Exception as exc:
            errors.append(f"{p}: {exc}")

    if freed_bytes > 0:
        mb_freed = freed_bytes / (1024 * 1024)
        msg = f"Successfully deleted sample audio ({mb_freed:.1f} MB freed)."
        return True, freed_bytes, msg
    elif errors:
        return False, 0, f"Error deleting sample files: {'; '.join(errors)}"
    else:
        return False, 0, "No sample audio files were found to delete."


def download_sample_audio(
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Path:
    """Downloads the benchmark sample audio file with progress notifications."""
    dest_path = get_sample_audio_target_path()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".downloading.tmp")

    last_error = None
    for url in SAMPLE_AUDIO_URLS:
        if cancel_check and cancel_check():
            raise RuntimeError("Download cancelled by user.")

        try:
            if progress_callback:
                progress_callback(5, f"Connecting to sample repository ({url.split('/')[2]})...")

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "RadioTVSegmenter-Benchmark/3.5"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                with open(temp_path, "wb") as out_f:
                    while True:
                        if cancel_check and cancel_check():
                            raise RuntimeError("Download cancelled by user.")

                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0 and progress_callback:
                            pct = min(98, max(5, int((downloaded / total_size) * 100)))
                            mb_cur = downloaded / (1024 * 1024)
                            mb_tot = total_size / (1024 * 1024)
                            progress_callback(pct, f"Downloading sample audio: {mb_cur:.1f}/{mb_tot:.1f} MB ({pct}%)")

                if temp_path.exists() and temp_path.stat().st_size > 10000:
                    if dest_path.exists():
                        dest_path.unlink()
                    temp_path.rename(dest_path)
                    if progress_callback:
                        progress_callback(100, f"Download complete ({dest_path.stat().st_size / (1024*1024):.1f} MB).")
                    return dest_path
        except Exception as exc:
            last_error = exc
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass

    raise RuntimeError(f"Failed to download sample audio from all mirrors: {last_error}")


# ---------------------------------------------------------------------------
# Audio Decoding & PCM Extraction Helper
# ---------------------------------------------------------------------------

def decode_audio_file_pcm(
    file_path: Union[str, Path],
    max_duration_seconds: Optional[float] = None,
) -> Tuple[bytes, float, int, float]:
    """Decodes media file to 16kHz mono 16-bit PCM using FFmpeg."""
    path_str = str(file_path)
    if not os.path.isfile(path_str):
        raise FileNotFoundError(f"Audio file not found: {path_str}")

    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-v", "error",
        "-i", path_str,
        "-vn",
    ]
    if max_duration_seconds is not None and max_duration_seconds > 0:
        cmd.extend(["-t", str(max_duration_seconds)])

    cmd.extend([
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        "-f", "s16le",
        "pipe:1"
    ])

    t0 = time.perf_counter()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pcm_bytes, stderr_bytes = proc.communicate(timeout=60)
        if proc.returncode != 0:
            err_msg = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"FFmpeg decoding failed (exit code {proc.returncode}): {err_msg}")
    except Exception as exc:
        raise RuntimeError(f"Could not decode audio file with FFmpeg: {exc}")

    decode_time = max(0.0001, time.perf_counter() - t0)
    sample_rate = 16000
    duration_seconds = len(pcm_bytes) / (sample_rate * 2)
    decode_rtf = duration_seconds / decode_time if duration_seconds > 0 else 0.0

    return pcm_bytes, duration_seconds, sample_rate, decode_rtf


# ---------------------------------------------------------------------------
# Synthetic Audio Fixture (Zero-Dependency in-memory PCM generator)
# ---------------------------------------------------------------------------

_CACHED_SEED_PCM: Optional[bytes] = None


def _get_seed_speech_pcm(sample_rate: int = 16000) -> bytes:
    """Generates a 5-second realistic speech-modulated PCM audio seed in memory."""
    global _CACHED_SEED_PCM
    if _CACHED_SEED_PCM is not None:
        return _CACHED_SEED_PCM

    num_samples = sample_rate * 5
    frames = bytearray()
    freqs = [130.0, 260.0, 390.0, 1200.0, 2400.0]
    for i in range(num_samples):
        t = float(i) / sample_rate
        cycle_pos = t % 1.6
        if cycle_pos > 1.2:
            sample_val = 0
        else:
            combined = sum(math.sin(2.0 * math.pi * f * t) for f in freqs) / len(freqs)
            mod = 0.5 + 0.5 * math.sin(2.0 * math.pi * 3.0 * t)
            sample_val = int(combined * mod * 28000.0)
            sample_val = max(-32768, min(32767, sample_val))
        frames.extend(struct.pack("<h", sample_val))

    _CACHED_SEED_PCM = bytes(frames)
    return _CACHED_SEED_PCM


def generate_benchmark_audio(
    duration_seconds: float = 30.0,
    sample_rate: int = 16000,
) -> bytes:
    """Generates mono 16-bit 16kHz speech-like PCM WAV audio in memory via seed tiling."""
    seed_pcm = _get_seed_speech_pcm(sample_rate=sample_rate)
    seed_duration = 5.0
    repeat_count = max(1, int(math.ceil(duration_seconds / seed_duration)))
    target_bytes_len = int(duration_seconds * sample_rate * 2)

    tiled_pcm = (seed_pcm * repeat_count)[:target_bytes_len]

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(tiled_pcm)

    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Hardware & Environment Profiler
# ---------------------------------------------------------------------------

def get_system_hardware_profile() -> Dict[str, Any]:
    """Inspects CPU, RAM, OS, and GPU environment."""
    profile: Dict[str, Any] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor() or "Unknown CPU",
        "cpu_count_logical": os.cpu_count() or 1,
        "machine": platform.machine(),
    }

    try:
        if sys.platform.startswith("linux"):
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        profile["total_ram_gb"] = round(kb / (1024 * 1024), 1)
                        break
        elif sys.platform == "win32":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                profile["total_ram_gb"] = round(stat.ullTotalPhys / (1024 ** 3), 1)
    except Exception:
        pass

    gpu_devices = []
    try:
        import torch
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_devices.append({
                    "framework": "PyTorch CUDA",
                    "device_index": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_total_mb": round(torch.cuda.get_device_properties(i).total_memory / (1024 * 1024), 1),
                })
    except Exception:
        pass

    try:
        import onnxruntime as ort
        profile["onnx_providers"] = ort.get_available_providers()
    except Exception:
        profile["onnx_providers"] = ["CPUExecutionProvider"]

    profile["gpu_devices"] = gpu_devices
    return profile


# ---------------------------------------------------------------------------
# Benchmark Data Models
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkMetric:
    name: str
    category: str
    duration_seconds: float = 0.0
    audio_duration_seconds: float = 0.0
    throughput_mb_s: float = 0.0
    real_time_factor: float = 0.0
    operations_per_sec: float = 0.0
    score_points: int = 0
    peak_memory_mb: float = 0.0
    notes: str = ""
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, SKIPPED, FAILED
    error: str = ""


@dataclass
class ProcessingEstimates:
    """Estimated processing times for a standard 30-minute broadcast file."""
    audio_duration_minutes: float = 30.0
    story_detection_seconds: float = 0.0
    transcription_parakeet_seconds: float = 0.0
    transcription_parakeet_rtf: float = 0.0
    transcription_whisper_seconds: float = 0.0
    transcription_whisper_rtf: float = 0.0
    transcription_seconds: float = 0.0
    diarization_seconds: float = 0.0
    translation_seconds: float = 0.0
    translation_installed: bool = False
    total_with_parakeet_seconds: float = 0.0
    total_with_parakeet_rtf: float = 0.0
    total_with_whisper_seconds: float = 0.0
    total_with_whisper_rtf: float = 0.0
    total_seconds: float = 0.0
    real_time_factor: float = 0.0
    details: Dict[str, str] = field(default_factory=dict)


def is_translation_plugin_installed() -> bool:
    """Checks if the local neural translation plugin/runtime is installed and available."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.join(base_dir, "plugins", "translation")
        if not os.path.isdir(plugin_dir):
            return False

        try:
            import ctranslate2  # noqa: F401
            return True
        except ImportError:
            pass

        runtime_dirs = [
            os.path.join(plugin_dir, "venv"),
            os.path.join(plugin_dir, "env"),
            os.path.join(base_dir, "runtimes", "translate"),
        ]
        for r_dir in runtime_dirs:
            if os.path.isdir(r_dir):
                return True

        manifest_path = os.path.join(plugin_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("id") == "translation")
    except Exception:
        pass
    return False


def format_duration_estimate(seconds: float) -> str:
    """Formats seconds into a clear human-readable duration."""
    if seconds < 1.0:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60.0:
        return f"~{seconds:.1f}s" if seconds < 10.0 else f"~{int(round(seconds))}s"
    else:
        minutes = int(seconds // 60)
        rem_sec = int(round(seconds % 60))
        return f"~{minutes}m {rem_sec:02d}s"

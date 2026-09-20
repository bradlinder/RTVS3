#!/usr/bin/env python3
"""Radio & TV Story Segmenter — Performance & Speed Benchmark Engine.

Measures system throughput, multi-core scaling, memory footprints, and compute
speeds across the core processing pipeline with dual audio mode support:
- In-Memory Synthetic RAM Stream: Zero disk footprint, mathematical acoustic fixture.
- Real 30-Minute Broadcast Sample Audio: Low-bitrate (32/48/64 kbps MP3, ~6.9 MB)
  real-world broadcast recording with on-demand download & delete-to-free-space.
- Custom Media File: Select any active timeline or external audio/video file.

Pipeline Subsystem Benchmarks:
1. Waveform peak & multi-resolution envelope extraction (MB/s and Real-Time Factor).
2. Audio STFT & 80-bin Mel-scale filterbank extraction (AI feature pre-processing).
3. Multi-threaded concurrent speech segmentation (multi-core scaling efficiency).
4. Speaker diarization high-dimensional vector search & clustering (comparisons/sec).
5. Project serialization, deserialization & story interval graph indexing (MB/s).
6. UI transcript text formatting, word tokenization & lexical search throughput.
7. Neural transformer self-attention matrix compute kernel (GFLOPS).
8. Composite Hardware Performance Score ("RTVS Hardware Score") with rating tiers.
9. Hardware-calibrated 30-minute processing time estimates for both Parakeet & Whisper.

Callable via:
  1. CLI: python benchmark.py [--quick] [--json] [--sample] [--file PATH] [--download-sample] [--delete-sample]
  2. RadioTVSegmenter CLI: RadioTVSegmenter.exe --benchmark [--quick] [--json]
  3. Integrated GUI: Help -> Run Performance Benchmark... (Ctrl+Shift+B)
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
import tracemalloc
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


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

    # 1. Local workspace / repository 'samples/' directory
    candidates.append(base_dir / "samples" / SAMPLE_AUDIO_FILENAME)
    # 2. Workspace root 'Performance Test Audio.mp3'
    candidates.append(base_dir / "Performance Test Audio.mp3")
    candidates.append(base_dir / SAMPLE_AUDIO_FILENAME)
    # 3. User application data directory 'samples/' folder
    candidates.append(get_app_data_dir() / "samples" / SAMPLE_AUDIO_FILENAME)
    # 4. Current working directory fallback
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
    # Prefer local workspace/samples if writable, otherwise app data directory
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
    """Decodes media file to 16kHz mono 16-bit PCM using FFmpeg.

    Returns:
        (pcm_bytes, decoded_duration_seconds, sample_rate, decode_rtf)
    """
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
    """Generates mono 16-bit 16kHz speech-like PCM WAV audio in memory via seed tiling.

    Zero disk footprint, fast memory-only buffer allocation.
    """
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

    # Detect RAM if available
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

    # Detect CUDA / GPU if PyTorch or ONNX is present
    gpu_devices = []
    try:
        import torch  # type: ignore
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
        import onnxruntime as ort  # type: ignore
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
    # ASR Models
    transcription_parakeet_seconds: float = 0.0
    transcription_parakeet_rtf: float = 0.0
    transcription_whisper_seconds: float = 0.0
    transcription_whisper_rtf: float = 0.0
    # Default active model
    transcription_seconds: float = 0.0
    # Other subsystems
    diarization_seconds: float = 0.0
    translation_seconds: float = 0.0
    translation_installed: bool = False
    # Pipeline Totals
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
            import ctranslate2  # type: ignore
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


# ---------------------------------------------------------------------------
# Core Benchmark Runner Engine
# ---------------------------------------------------------------------------

class BenchmarkEngine:
    """Executes high-precision performance throughput benchmarks."""

    DURATION_MODES = {
        "quick": {
            "name": "Quick Spot-Check",
            "audio_min": 1.0,
            "audio_sec": 60.0,
            "audio_seconds": 60.0,
            "est_runtime": "~3–5s",
            "estimate_runtime": "~3–5s",
            "desc": "Instant hardware sanity check with lightweight workloads",
            "description": "Instant hardware sanity check with lightweight workloads",
        },
        "standard": {
            "name": "Standard Benchmark",
            "audio_min": 5.0,
            "audio_sec": 300.0,
            "audio_seconds": 300.0,
            "est_runtime": "~20–30s",
            "estimate_runtime": "~20–30s",
            "desc": "Balanced multi-core throughput rating (Default)",
            "description": "Balanced multi-core throughput rating (Default)",
        },
        "sustained": {
            "name": "Sustained Thermal Stress",
            "audio_min": 10.0,
            "audio_sec": 600.0,
            "audio_seconds": 600.0,
            "est_runtime": "~1–2m",
            "estimate_runtime": "~1–2m",
            "desc": "Measures sustained boost clocks and thermal dissipation under continuous load",
            "description": "Measures sustained boost clocks and thermal dissipation under continuous load",
        },
        "full": {
            "name": "Full Broadcast Pass",
            "audio_min": 30.0,
            "audio_sec": 1800.0,
            "audio_seconds": 1800.0,
            "est_runtime": "~3–6m",
            "estimate_runtime": "~3–6m",
            "desc": "Complete end-to-end stress test across all 30 minutes of broadcast audio",
            "description": "Complete end-to-end stress test across all 30 minutes of broadcast audio",
        },
    }

    def __init__(
        self,
        quick: bool = False,
        duration_mode: str = "standard",
        audio_source_mode: str = "synthetic",
        custom_audio_path: Optional[Union[str, Path]] = None,
    ):
        if quick:
            self.duration_mode = "quick"
        elif duration_mode in self.DURATION_MODES:
            self.duration_mode = duration_mode
        elif duration_mode in ("1m", "1min"):
            self.duration_mode = "quick"
        elif duration_mode in ("5m", "5min"):
            self.duration_mode = "standard"
        elif duration_mode in ("10m", "10min"):
            self.duration_mode = "sustained"
        elif duration_mode in ("30m", "30min", "full"):
            self.duration_mode = "full"
        else:
            self.duration_mode = "standard"

        self.quick = (self.duration_mode == "quick")
        self.audio_source_mode = audio_source_mode  # "synthetic", "sample", or "custom"
        self.custom_audio_path = Path(custom_audio_path) if custom_audio_path else None

        self.loaded_pcm_bytes: Optional[bytes] = None
        self.loaded_audio_duration: float = 0.0
        self.audio_decode_rtf: float = 0.0
        self.audio_source_description: str = ""

        self.metrics: List[BenchmarkMetric] = [
            BenchmarkMetric(
                name="Waveform Peak Extraction",
                category="Audio Pipeline",
                notes="Peak envelope generation across 16kHz audio stream",
            ),
            BenchmarkMetric(
                name="Audio STFT & Mel Filterbank",
                category="Audio Pipeline",
                notes="80-bin Mel scale filterbank feature extraction",
            ),
            BenchmarkMetric(
                name="Multi-Core Speech Segmentation",
                category="Multi-Core Compute",
                notes="Parallel vocal chunk boundary detection across cores",
            ),
            BenchmarkMetric(
                name="Speaker Diarization Vector Search",
                category="AI & Diarization",
                notes="256-dim pairwise cosine distance & centroid clustering",
            ),
            BenchmarkMetric(
                name="Project Serialization & Indexing",
                category="Memory & I/O",
                notes="JSON encoding/decoding & story interval tree indexing",
            ),
            BenchmarkMetric(
                name="Transcript Formatting & Search",
                category="UI & Text Engine",
                notes="Word tokenization, HTML span tagging & lexical lookup",
            ),
            BenchmarkMetric(
                name="Transformer Self-Attention Kernel",
                category="AI & Diarization",
                notes="Multi-head attention matrix GEMM simulation",
            ),
        ]
        self.hardware_profile = get_system_hardware_profile()
        self.on_update: Optional[Callable[[BenchmarkMetric], None]] = None
        self.composite_score: int = 0
        self.score_breakdown: Dict[str, int] = {}
        self.hardware_tier: str = "Unrated"
        self.processing_estimates: Optional[ProcessingEstimates] = None

    def _get_target_audio_seconds(self) -> float:
        """Returns the target audio window in seconds based on active duration mode."""
        cfg = self.DURATION_MODES.get(self.duration_mode, self.DURATION_MODES["standard"])
        return cfg["audio_sec"]

    def _prepare_audio_source(self):
        """Loads and prepares the configured audio stream (synthetic or real file)."""
        target_sec = self._get_target_audio_seconds()
        dur_label = f"{int(target_sec//60)}m" if target_sec >= 60 else f"{int(target_sec)}s"

        if self.audio_source_mode == "sample":
            sample_path = find_available_sample_audio()
            if sample_path:
                try:
                    max_dur = None if self.duration_mode == "full" else target_sec
                    pcm, dur, _, rtf = decode_audio_file_pcm(sample_path, max_duration_seconds=max_dur)
                    self.loaded_pcm_bytes = pcm
                    self.loaded_audio_duration = dur
                    self.audio_decode_rtf = rtf
                    self.audio_source_description = f"Broadcast Sample ({sample_path.name}, {dur:.1f}s / {dur_label} window)"
                    return
                except Exception as exc:
                    self.audio_source_description = f"Sample decode failed ({exc}), falling back to synthetic"
            else:
                self.audio_source_description = "Sample file missing, falling back to synthetic"

        elif self.audio_source_mode == "custom" and self.custom_audio_path:
            if self.custom_audio_path.is_file():
                try:
                    max_dur = None if self.duration_mode == "full" else target_sec
                    pcm, dur, _, rtf = decode_audio_file_pcm(self.custom_audio_path, max_duration_seconds=max_dur)
                    self.loaded_pcm_bytes = pcm
                    self.loaded_audio_duration = dur
                    self.audio_decode_rtf = rtf
                    self.audio_source_description = f"Custom File ({self.custom_audio_path.name}, {dur:.1f}s / {dur_label} window)"
                    return
                except Exception as exc:
                    self.audio_source_description = f"Custom audio decode failed ({exc}), falling back to synthetic"
            else:
                self.audio_source_description = "Custom audio file not found, falling back to synthetic"

        # Default: In-memory synthetic audio
        self.loaded_pcm_bytes = None
        self.loaded_audio_duration = 0.0
        self.audio_decode_rtf = 0.0
        self.audio_source_description = f"In-Memory Synthetic RAM Stream ({dur_label} audio fixture)"

    def run_all(self, stop_requested_fn: Optional[Callable[[], bool]] = None) -> List[BenchmarkMetric]:
        self._prepare_audio_source()

        for metric in self.metrics:
            if stop_requested_fn and stop_requested_fn():
                metric.status = "SKIPPED"
                metric.notes = "Cancelled by user"
                if self.on_update:
                    self.on_update(metric)
                continue

            metric.status = "RUNNING"
            if self.on_update:
                self.on_update(metric)

            method_name = f"_bench_{metric.name.lower().replace(' ', '_').replace('&', 'and').replace('/', '_').replace('-', '_')}"
            fn = getattr(self, method_name, None)
            if fn:
                tracemalloc.start()
                start_mem = tracemalloc.get_traced_memory()[0]
                t0 = time.perf_counter()
                try:
                    fn(metric)
                    t_dur = time.perf_counter() - t0
                    current_mem, peak_mem = tracemalloc.get_traced_memory()
                    metric.duration_seconds = round(t_dur, 4)
                    metric.peak_memory_mb = round((peak_mem - start_mem) / (1024 * 1024), 2)
                    metric.status = "COMPLETED"
                except Exception as exc:
                    metric.duration_seconds = round(time.perf_counter() - t0, 4)
                    metric.status = "FAILED"
                    metric.error = f"{type(exc).__name__}: {exc}"
                finally:
                    tracemalloc.stop()
            else:
                metric.status = "SKIPPED"
                metric.notes = "Benchmark harness method not found"

            if self.on_update:
                self.on_update(metric)

        self._compute_composite_score()
        self.processing_estimates = self.compute_processing_estimates(audio_duration_minutes=30.0)
        return self.metrics

    def _compute_composite_score(self):
        """Computes aggregate RTVS Hardware Performance Score normalized to baseline reference."""
        cat_scores: Dict[str, List[int]] = {}
        for m in self.metrics:
            if m.status == "COMPLETED" and m.score_points > 0:
                cat_scores.setdefault(m.category, []).append(m.score_points)

        self.score_breakdown = {}
        for cat, scores in cat_scores.items():
            self.score_breakdown[cat] = int(sum(scores) / len(scores))

        # Overall composite score is the weighted average across subsystems
        weights = {
            "Audio Pipeline": 0.25,
            "Multi-Core Compute": 0.30,
            "AI & Diarization": 0.25,
            "Memory & I/O": 0.10,
            "UI & Text Engine": 0.10,
        }
        total_score = 0.0
        weight_sum = 0.0
        for cat, weight in weights.items():
            if cat in self.score_breakdown:
                total_score += self.score_breakdown[cat] * weight
                weight_sum += weight

        self.composite_score = int(round(total_score / (weight_sum or 1.0)))

        # Tier classification
        if self.composite_score < 1800:
            self.hardware_tier = "Entry / Portable"
        elif self.composite_score < 3500:
            self.hardware_tier = "Mid-Range / Mainstream"
        elif self.composite_score < 6500:
            self.hardware_tier = "High Performance / Pro"
        else:
            self.hardware_tier = "Studio Workstation / Extreme"

    def compute_processing_estimates(self, audio_duration_minutes: float = 30.0) -> ProcessingEstimates:
        """Computes realistic estimated execution times for a standard broadcast file."""
        audio_duration_sec = audio_duration_minutes * 60.0  # 1800.0s
        hw = self.hardware_profile
        cores = max(1, int(hw.get("cpu_count_logical", 1)))
        has_gpu = bool(hw.get("gpu_devices"))

        # 1. Story & Boundary Detection (Waveform peak extraction + vocal pause energy analysis)
        peak_metric = next((m for m in self.metrics if m.name == "Waveform Peak Extraction"), None)
        seg_metric = next((m for m in self.metrics if m.name == "Multi-Core Speech Segmentation"), None)

        peak_rtf = peak_metric.real_time_factor if (peak_metric and peak_metric.real_time_factor > 0) else 120.0
        seg_mins_per_sec = (seg_metric.operations_per_sec * 15.0 / 60.0) if (seg_metric and seg_metric.operations_per_sec > 0) else 80.0

        peak_time = (audio_duration_sec / max(10.0, peak_rtf)) * 0.40  # C/NumPy peak acceleration factor
        seg_time = audio_duration_minutes / max(5.0, seg_mins_per_sec)
        story_detection_sec = max(1.0, peak_time + seg_time)

        att_metric = next((m for m in self.metrics if m.name == "Transformer Self-Attention Kernel"), None)

        # 2a. AI Transcription — Parakeet TDT 0.6B (Sherpa-ONNX FastConformer)
        if has_gpu:
            est_parakeet_rtf = 110.0 + min(90.0, cores * 3.5)
        else:
            est_parakeet_rtf = max(4.0, min(90.0, 4.2 * (float(cores) ** 0.82)))
            if att_metric and att_metric.score_points > 0:
                ratio = att_metric.score_points / 1000.0
                est_parakeet_rtf *= max(0.8, min(1.3, ratio ** 0.4))
        transcription_parakeet_sec = audio_duration_sec / est_parakeet_rtf

        # 2b. AI Transcription — Whisper INT8 / Distil-Whisper (Encoder-Decoder)
        if has_gpu:
            est_whisper_rtf = 24.0 + min(20.0, cores * 0.6)
        else:
            effective_cores = max(1.0, float(cores) ** 0.72)
            est_whisper_rtf = max(1.2, min(18.0, 1.25 * effective_cores))
            if att_metric and att_metric.score_points > 0:
                ratio = att_metric.score_points / 1000.0
                est_whisper_rtf *= max(0.7, min(1.4, ratio ** 0.5))
        transcription_whisper_sec = audio_duration_sec / est_whisper_rtf

        # 3. Speaker Diarization (WeSpeaker ONNX Embeddings + Spectral/AHC Clustering)
        diar_metric = next((m for m in self.metrics if m.name == "Speaker Diarization Vector Search"), None)
        comp_rate = diar_metric.operations_per_sec if (diar_metric and diar_metric.operations_per_sec > 0) else 20000.0

        if has_gpu:
            diarization_sec = 8.0 + (160.0 / max(10.0, comp_rate / 3000.0))
        else:
            diarization_sec = max(10.0, min(180.0, 110.0 / (math.sqrt(cores) * ((comp_rate / 20000.0) ** 0.4))))

        # 4. Neural Translation (MarianMT / NLLB-200 via CTranslate2 INT8)
        trans_installed = is_translation_plugin_installed()
        if has_gpu:
            words_per_sec = 450.0
        else:
            words_per_sec = max(25.0, min(400.0, 35.0 * (float(cores) ** 0.65)))
        translation_sec = 4200.0 / words_per_sec

        # Total Pipeline Durations
        total_parakeet_sec = story_detection_sec + transcription_parakeet_sec + diarization_sec
        total_parakeet_rtf = round(audio_duration_sec / total_parakeet_sec, 1)

        total_whisper_sec = story_detection_sec + transcription_whisper_sec + diarization_sec
        total_whisper_rtf = round(audio_duration_sec / total_whisper_sec, 1)

        details = {
            "story_detection": f"{format_duration_estimate(story_detection_sec)} (Audio peak & vocal pause analysis)",
            "transcription_parakeet": f"{format_duration_estimate(transcription_parakeet_sec)} (Est. {est_parakeet_rtf:.1f}x RTF, FastConformer TDT ONNX)",
            "transcription_whisper": f"{format_duration_estimate(transcription_whisper_sec)} (Est. {est_whisper_rtf:.1f}x RTF, Whisper INT8)",
            "diarization": f"{format_duration_estimate(diarization_sec)} (Voice embedding & cluster analysis)",
            "translation": f"{format_duration_estimate(translation_sec)} ({'Installed & Active' if trans_installed else 'Plugin Not Active — Est. if enabled'})",
            "total_with_parakeet": f"{format_duration_estimate(total_parakeet_sec)} ({total_parakeet_rtf}x Real-Time Factor)",
            "total_with_whisper": f"{format_duration_estimate(total_whisper_sec)} ({total_whisper_rtf}x Real-Time Factor)",
        }

        return ProcessingEstimates(
            audio_duration_minutes=audio_duration_minutes,
            story_detection_seconds=round(story_detection_sec, 2),
            transcription_parakeet_seconds=round(transcription_parakeet_sec, 2),
            transcription_parakeet_rtf=round(est_parakeet_rtf, 1),
            transcription_whisper_seconds=round(transcription_whisper_sec, 2),
            transcription_whisper_rtf=round(est_whisper_rtf, 1),
            transcription_seconds=round(transcription_parakeet_sec, 2),
            diarization_seconds=round(diarization_sec, 2),
            translation_seconds=round(translation_sec, 2),
            translation_installed=trans_installed,
            total_with_parakeet_seconds=round(total_parakeet_sec, 2),
            total_with_parakeet_rtf=total_parakeet_rtf,
            total_with_whisper_seconds=round(total_whisper_sec, 2),
            total_with_whisper_rtf=total_whisper_rtf,
            total_seconds=round(total_parakeet_sec, 2),
            real_time_factor=total_parakeet_rtf,
            details=details,
        )

    # 1. Waveform Peak & Multi-Tier Envelope Extraction
    def _bench_waveform_peak_extraction(self, metric: BenchmarkMetric):
        if self.loaded_pcm_bytes:
            raw_pcm = self.loaded_pcm_bytes
            audio_duration = self.loaded_audio_duration
            is_real = True
        else:
            audio_duration = self._get_target_audio_seconds()
            wav_bytes = generate_benchmark_audio(duration_seconds=audio_duration)
            raw_pcm = wav_bytes[44:]
            is_real = False

        data_size_mb = len(raw_pcm) / (1024 * 1024)

        t0 = time.perf_counter()
        num_samples = len(raw_pcm) // 2
        samples_per_peak = 160  # 100 peaks/sec at 16kHz
        num_peaks = num_samples // samples_per_peak

        peaks_100 = []
        peaks_10 = []
        rms_envelope = []

        chunk_size = samples_per_peak * 2
        for i in range(num_peaks):
            start = i * chunk_size
            chunk = raw_pcm[start:start + chunk_size]
            vals = struct.unpack("<160h", chunk)
            max_val = max(abs(v) for v in vals) if vals else 0
            scaled_peak = min(255, int((max_val / 32768.0) * 255))
            peaks_100.append(scaled_peak)

            if i % 10 == 0:
                peaks_10.append(scaled_peak)

            # RMS power calculation
            rms = int(math.sqrt(sum(v * v for v in vals) / 160.0))
            rms_envelope.append(rms)

        calc_time = max(0.0001, time.perf_counter() - t0)
        metric.audio_duration_seconds = audio_duration
        metric.real_time_factor = round(audio_duration / calc_time, 1)
        metric.throughput_mb_s = round(data_size_mb / calc_time, 2)
        metric.operations_per_sec = round(num_samples / calc_time, 0)
        # Baseline reference: 110x RTF = 1,000 pts
        metric.score_points = int(round((metric.real_time_factor / 110.0) * 1000))
        prefix = "Real MP3 Stream: " if is_real else "Synthetic: "
        decode_note = f" (FFmpeg decode @ {self.audio_decode_rtf:.1f}x RTF)" if is_real and self.audio_decode_rtf > 0 else ""
        metric.notes = f"{prefix}{metric.real_time_factor:,.1f}x RTF ({metric.throughput_mb_s} MB/s, {len(peaks_100):,} peak bins + RMS){decode_note}"

    # 2. Audio STFT & Mel-Scale Filterbank Extraction
    def _bench_audio_stft_and_mel_filterbank(self, metric: BenchmarkMetric):
        if self.duration_mode == "quick":
            num_frames = 150
        elif self.duration_mode == "sustained":
            num_frames = 1800
        elif self.duration_mode == "full":
            num_frames = 5000
        else:
            num_frames = 450

        fft_size = 256
        num_mel_bins = 80

        # Construct triangular Mel filterbank weights
        mel_filters = [[0.02 * ((k + m) % 7) for k in range(fft_size // 2)] for m in range(num_mel_bins)]
        hanning = [0.5 * (1.0 - math.cos(2.0 * math.pi * n / (fft_size - 1))) for n in range(fft_size)]

        pcm = self.loaded_pcm_bytes
        has_real_pcm = bool(pcm and len(pcm) >= (num_frames * 160 * 2))

        t0 = time.perf_counter()
        total_ops = 0
        for f_idx in range(num_frames):
            if has_real_pcm:
                offset = f_idx * 160 * 2
                chunk = pcm[offset:offset + fft_size * 2]
                if len(chunk) == fft_size * 2:
                    vals = struct.unpack(f"<{fft_size}h", chunk)
                    frame = [(v / 32768.0) * hanning[n] for n, v in enumerate(vals)]
                else:
                    frame = [math.sin((f_idx + n) * 0.15) * hanning[n] for n in range(fft_size)]
            else:
                frame = [math.sin((f_idx + n) * 0.15) * hanning[n] for n in range(fft_size)]

            # Power spectrum calculation
            spec = [sum(frame[n] * math.cos(2 * math.pi * k * n / fft_size) for n in range(0, fft_size, 4)) ** 2 for k in range(fft_size // 2)]
            total_ops += (fft_size // 4) * (fft_size // 2)

            # Mel filterbank dot-product projection
            mel_energies = [math.log(max(1e-5, sum(s * f for s, f in zip(spec, mf)))) for mf in mel_filters]
            total_ops += (fft_size // 2) * num_mel_bins

        calc_time = max(0.0001, time.perf_counter() - t0)
        frames_per_sec = num_frames / calc_time
        sim_audio_sec = num_frames * 0.010  # 10ms frame step
        rtf = round(sim_audio_sec / calc_time, 1)

        metric.real_time_factor = rtf
        metric.operations_per_sec = round(total_ops / calc_time, 0)
        # Baseline reference: 130 frames/sec = 1,000 pts
        metric.score_points = int(round((frames_per_sec / 130.0) * 1000))
        metric.notes = f"{frames_per_sec:,.0f} Mel frames/sec ({rtf}x RTF, {num_frames:,} frames, {num_mel_bins} Mel bins)"

    # 3. Multi-Core Speech Segmentation (Scaling Test)
    def _bench_multi_core_speech_segmentation(self, metric: BenchmarkMetric):
        logical_cores = os.cpu_count() or 1
        if self.duration_mode == "quick":
            chunks_per_core = 4
        elif self.duration_mode == "sustained":
            chunks_per_core = 45
        elif self.duration_mode == "full":
            chunks_per_core = 120
        else:
            chunks_per_core = 12

        total_chunks = logical_cores * chunks_per_core
        pcm = self.loaded_pcm_bytes

        def _process_audio_chunk(chunk_id: int) -> int:
            window_count = 1500
            if pcm and len(pcm) >= (chunk_id + 1) * window_count * 2:
                offset = chunk_id * window_count * 2
                chunk_bytes = pcm[offset:offset + window_count * 2]
                vals = struct.unpack(f"<{len(chunk_bytes)//2}h", chunk_bytes)
                energies = [(abs(v) / 32768.0) for v in vals]
            else:
                energies = [0.1 + 0.8 * (math.sin((chunk_id + i) * 0.04) ** 2) for i in range(window_count)]

            boundaries = 0
            in_speech = False
            for val in energies:
                if val >= 0.35 and not in_speech:
                    in_speech = True
                    boundaries += 1
                elif val < 0.35 and in_speech:
                    in_speech = False
            return boundaries

        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=logical_cores) as pool:
            results = list(pool.map(_process_audio_chunk, range(total_chunks)))

        calc_time = max(0.0001, time.perf_counter() - t0)
        chunks_per_sec = total_chunks / calc_time
        audio_mins_processed = (total_chunks * 15.0) / 60.0  # 15s simulated chunk
        mins_per_sec = audio_mins_processed / calc_time

        metric.operations_per_sec = round(chunks_per_sec, 1)
        # Baseline reference: 2 cores processing 400 chunks/sec = 1,000 pts
        metric.score_points = int(round((chunks_per_sec / 400.0) * 1000))
        metric.notes = f"{chunks_per_sec:,.1f} chunks/sec across {logical_cores} cores ({total_chunks:,} chunks, {mins_per_sec:.1f} audio mins/sec)"

    # 4. Speaker Diarization High-Dimensional Vector Search
    def _bench_speaker_diarization_vector_search(self, metric: BenchmarkMetric):
        dims = 256
        if self.duration_mode == "quick":
            num_embeddings = 100
        elif self.duration_mode == "sustained":
            num_embeddings = 600
        elif self.duration_mode == "full":
            num_embeddings = 1200
        else:
            num_embeddings = 260

        embeddings = [[math.sin(i * 0.2 + j * 0.1) for j in range(dims)] for i in range(num_embeddings)]

        t0 = time.perf_counter()
        norms = [math.sqrt(sum(x * x for x in v)) or 1.0 for v in embeddings]
        normed = [[x / norms[i] for x in embeddings[i]] for i in range(num_embeddings)]

        # Pairwise cosine distance matrix
        pairs_calculated = 0
        dist_matrix = []
        for i in range(num_embeddings):
            row = []
            for j in range(num_embeddings):
                if i == j:
                    row.append(0.0)
                else:
                    dot = sum(normed[i][d] * normed[j][d] for d in range(dims))
                    row.append(1.0 - dot)
                    pairs_calculated += 1
            dist_matrix.append(row)

        # Centroid clustering simulation
        centroids = [normed[0], normed[min(1, num_embeddings - 1)]]
        assignments = []
        for emb in normed:
            d0 = 1.0 - sum(emb[d] * centroids[0][d] for d in range(dims))
            d1 = 1.0 - sum(emb[d] * centroids[1][d] for d in range(dims))
            assignments.append(0 if d0 < d1 else 1)

        calc_time = max(0.0001, time.perf_counter() - t0)
        ops_per_sec = pairs_calculated / calc_time

        metric.operations_per_sec = round(ops_per_sec, 0)
        # Baseline reference: 20,000 comparisons/sec = 1,000 pts
        metric.score_points = int(round((ops_per_sec / 20000.0) * 1000))
        metric.notes = f"{ops_per_sec:,.0f} pairwise comparisons/sec ({num_embeddings:,} {dims}-dim turns, {pairs_calculated:,} pairs + clustering)"

    # 5. Project Serialization & Story Interval Graph Indexing
    def _bench_project_serialization_and_indexing(self, metric: BenchmarkMetric):
        if self.duration_mode == "quick":
            num_stories = 350
        elif self.duration_mode == "sustained":
            num_stories = 3800
        elif self.duration_mode == "full":
            num_stories = 9000
        else:
            num_stories = 1200

        words_per_story = 35

        stories_data = []
        cur_time = 0.0
        for s_id in range(num_stories):
            words = []
            for w_id in range(words_per_story):
                words.append({
                    "word": f"word_{w_id}",
                    "start": round(cur_time, 2),
                    "end": round(cur_time + 0.35, 2),
                    "confidence": 0.96,
                })
                cur_time += 0.40

            stories_data.append({
                "id": f"story_{s_id:04d}",
                "headline": f"Report on News Topic #{s_id}",
                "start_time": round(s_id * 14.0, 2),
                "end_time": round((s_id + 1) * 14.0, 2),
                "speaker": f"SPEAKER_{s_id % 4:02d}",
                "words": words,
                "color": "#3b82f6",
                "custom_metadata": {"tags": ["broadcast", "news", "bench"], "priority": 1},
            })

        t0 = time.perf_counter()
        json_str = json.dumps(stories_data)
        encoded_bytes = len(json_str.encode("utf-8"))
        decoded_obj = json.loads(json_str)

        # Interval graph binary lookup tree
        intervals = [(s["start_time"], s["end_time"], s["id"]) for s in decoded_obj]
        intervals.sort(key=lambda x: x[0])
        queries = [i * 10.0 for i in range(num_stories)]
        matches = 0
        for q in queries:
            for start, end, s_id in intervals:
                if start <= q <= end:
                    matches += 1
                    break

        calc_time = max(0.0001, time.perf_counter() - t0)
        throughput_mb = (encoded_bytes / (1024 * 1024)) / calc_time
        stories_per_sec = num_stories / calc_time

        metric.throughput_mb_s = round(throughput_mb, 2)
        metric.operations_per_sec = round(stories_per_sec, 0)
        # Baseline reference: 15,000 segments/sec = 1,000 pts
        metric.score_points = int(round((stories_per_sec / 15000.0) * 1000))
        metric.notes = f"{stories_per_sec:,.0f} segments/sec ({throughput_mb:.2f} MB/s JSON, {num_stories:,} segments indexed)"

    # 6. Transcript Formatting & Lexical Search Throughput
    def _bench_transcript_formatting_and_search(self, metric: BenchmarkMetric):
        if self.duration_mode == "quick":
            num_sentences = 400
        elif self.duration_mode == "sustained":
            num_sentences = 4500
        elif self.duration_mode == "full":
            num_sentences = 11000
        else:
            num_sentences = 1500

        words_vocab = ["segment", "broadcast", "transcription", "audio", "speaker", "timeline", "interval", "waveform"]

        transcript_words = []
        for i in range(num_sentences * 8):
            w = words_vocab[i % len(words_vocab)]
            transcript_words.append((w, round(i * 0.3, 2), round(i * 0.3 + 0.25, 2)))

        t0 = time.perf_counter()
        html_spans = []
        char_count = 0
        inverted_index: Dict[str, List[int]] = {}

        for idx, (word, start, end) in enumerate(transcript_words):
            span = f'<span class="word" data-start="{start}" data-end="{end}">{word}</span> '
            html_spans.append(span)
            char_count += len(word) + 1
            inverted_index.setdefault(word, []).append(idx)

        full_html = "".join(html_spans)

        search_terms = ["broadcast", "waveform", "speaker", "transcription"]
        hit_count = sum(len(inverted_index.get(term, [])) for term in search_terms)

        calc_time = max(0.0001, time.perf_counter() - t0)
        words_per_sec = len(transcript_words) / calc_time

        metric.operations_per_sec = round(words_per_sec, 0)
        # Baseline reference: 260,000 words/sec = 1,000 pts
        metric.score_points = int(round((words_per_sec / 260000.0) * 1000))
        metric.notes = f"{words_per_sec:,.0f} words/sec formatted ({len(full_html):,} chars, {len(transcript_words):,} tokens, index built)"

    # 7. Transformer Multi-Head Self-Attention GEMM Kernel
    def _bench_transformer_self_attention_kernel(self, metric: BenchmarkMetric):
        if self.duration_mode == "quick":
            seq_len = 120
        elif self.duration_mode == "sustained":
            seq_len = 450
        elif self.duration_mode == "full":
            seq_len = 650
        else:
            seq_len = 220

        d_model = 256
        num_heads = 4
        d_head = d_model // num_heads

        q = [[[math.sin(i * 0.1 + h * 0.2 + d * 0.05) for d in range(d_head)] for i in range(seq_len)] for h in range(num_heads)]
        k = [[[math.cos(j * 0.1 + h * 0.2 + d * 0.05) for d in range(d_head)] for j in range(seq_len)] for h in range(num_heads)]
        v = [[[math.sin(j * 0.05 + d * 0.1) for d in range(d_head)] for j in range(seq_len)] for h in range(num_heads)]

        t0 = time.perf_counter()
        total_flops = 0

        # Matrix Multiply Q x K^T for each head
        scale = 1.0 / math.sqrt(d_head)
        for h in range(num_heads):
            scores = []
            for i in range(seq_len):
                row = []
                for j in range(seq_len):
                    dot = sum(q[h][i][d] * k[h][j][d] for d in range(d_head)) * scale
                    row.append(dot)
                    total_flops += 2 * d_head
                # Softmax normalization
                max_val = max(row)
                exp_vals = [math.exp(x - max_val) for x in row]
                sum_exp = sum(exp_vals) or 1.0
                weights = [x / sum_exp for x in exp_vals]
                scores.append(weights)
                total_flops += 3 * seq_len

            # Matrix Multiply Attention Weights x V
            out_head = []
            for i in range(seq_len):
                out_vec = []
                for d in range(d_head):
                    val = sum(scores[i][j] * v[h][j][d] for j in range(seq_len))
                    out_vec.append(val)
                    total_flops += 2 * seq_len
                out_head.append(out_vec)

        calc_time = max(0.0001, time.perf_counter() - t0)
        gflops = (total_flops / (10 ** 9)) / calc_time

        metric.operations_per_sec = round(total_flops / calc_time, 0)
        # Baseline reference: 0.008 GFLOPS = 1,000 pts
        metric.score_points = int(round((gflops / 0.008) * 1000))
        metric.notes = f"{gflops:.3f} GFLOPS ({total_flops:,} matrix attention ops, {seq_len} seq len, {num_heads} heads)"


# ---------------------------------------------------------------------------
# CLI & Terminal Formatter
# ---------------------------------------------------------------------------

def run_cli_benchmark(
    quick: bool = False,
    duration_mode: str = "standard",
    as_json: bool = False,
    use_sample: bool = False,
    custom_file: Optional[str] = None,
) -> int:
    """Run performance benchmarks and print formatted terminal report."""
    if quick:
        duration_mode = "quick"

    mode = "sample" if use_sample else ("custom" if custom_file else "synthetic")
    engine = BenchmarkEngine(duration_mode=duration_mode, audio_source_mode=mode, custom_audio_path=custom_file)

    if not as_json:
        print("=" * 74)
        print(" Radio & TV Story Segmenter — Performance & Speed Benchmark")
        print("=" * 74)
        hw = engine.hardware_profile
        gpu_str = hw["gpu_devices"][0]["name"] if hw.get("gpu_devices") else "CPU execution mode (No dedicated GPU acceleration)"
        ram_str = f" | {hw['total_ram_gb']} GB RAM" if "total_ram_gb" in hw else ""
        print(f"Platform : {hw['platform']}")
        print(f"CPU      : {hw['processor']} ({hw['cpu_count_logical']} logical cores{ram_str})")
        print(f"GPU      : {gpu_str}")
        dur_info = engine.DURATION_MODES.get(duration_mode, engine.DURATION_MODES["standard"])
        print(f"Rigor    : {dur_info['name']} (Audio: {dur_info['audio_seconds']}s / {dur_info['audio_seconds']//60}m | Est: {dur_info['estimate_runtime']})")
        print(f"Audio    : {engine.audio_source_description or 'Preparing...'}")
        print("-" * 74)

    def _cli_update(m: BenchmarkMetric):
        if not as_json and m.status in ("COMPLETED", "FAILED"):
            idx = next((i + 1 for i, item in enumerate(engine.metrics) if item.name == m.name), 0)
            score_str = f"[{m.score_points:,} pts]".rjust(11)
            stat = "COMPLETED" if m.status == "COMPLETED" else "FAILED"
            print(f"{idx:02d}/07 [{stat}] {m.name.ljust(35)} ({m.duration_seconds:.2f}s) {score_str}")
            print(f"       -> {m.notes}")

    engine.on_update = _cli_update
    engine.run_all()

    if as_json:
        data = {
            "hardware_profile": engine.hardware_profile,
            "composite_score": engine.composite_score,
            "hardware_tier": engine.hardware_tier,
            "duration_mode": engine.duration_mode,
            "score_breakdown": engine.score_breakdown,
            "audio_source": engine.audio_source_description,
            "processing_estimates_30min": asdict(engine.processing_estimates) if engine.processing_estimates else None,
            "metrics": [asdict(m) for m in engine.metrics],
        }
        print(json.dumps(data, indent=2))
        return 0

    print("=" * 74)
    print(f" RTVS HARDWARE PERFORMANCE SCORE: {engine.composite_score:,} pts  ({engine.hardware_tier})")
    print("-" * 74)
    print(" Subsystem Breakdown:")
    for cat, pts in engine.score_breakdown.items():
        print(f"   • {cat.ljust(25)} : {pts:,} pts")

    if engine.processing_estimates:
        est = engine.processing_estimates
        print("-" * 74)
        print(" Estimated Processing Times (30-Minute Broadcast File):")
        print(f"   • Story & Boundary Detection   : {est.details.get('story_detection', '')}")
        print(f"   • AI Transcription (Parakeet)  : {est.details.get('transcription_parakeet', '')}")
        print(f"   • AI Transcription (Whisper)   : {est.details.get('transcription_whisper', '')}")
        print(f"   • Speaker Diarization          : {est.details.get('diarization', '')}")
        print(f"   • Neural Translation           : {est.details.get('translation', '')}")
        print("   " + "-" * 68)
        print(f"   • Complete Pipeline (Parakeet) : {est.details.get('total_with_parakeet', '')}")
        print(f"   • Complete Pipeline (Whisper)  : {est.details.get('total_with_whisper', '')}")

    print("=" * 74)
    return 0


# ---------------------------------------------------------------------------
# PySide6 Native Graphical Dialog
# ---------------------------------------------------------------------------

def create_benchmark_dialog(parent=None):
    """Factory creating the native PySide6 Benchmark Dialog."""
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )

    class BenchmarkWorker(QThread):
        item_updated = Signal(object)
        finished = Signal()

        def __init__(self, engine: BenchmarkEngine):
            super().__init__()
            self.engine = engine
            self._is_stopped = False

        def stop(self):
            self._is_stopped = True

        def run(self):
            self.engine.on_update = lambda m: self.item_updated.emit(m)
            self.engine.run_all(stop_requested_fn=lambda: self._is_stopped)
            self.finished.emit()

    class SampleDownloadWorker(QThread):
        progress = Signal(int, str)
        finished = Signal(bool, str)

        def __init__(self):
            super().__init__()
            self._is_cancelled = False

        def cancel(self):
            self._is_cancelled = True

        def run(self):
            try:
                dest = download_sample_audio(
                    progress_callback=lambda pct, msg: self.progress.emit(pct, msg),
                    cancel_check=lambda: self._is_cancelled,
                )
                self.finished.emit(True, f"Sample saved: {dest.name}")
            except Exception as exc:
                self.finished.emit(False, str(exc))

    class BenchmarkDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("System Performance & Speed Benchmark")
            self.resize(1000, 760)

            # Detect if parent has active media path
            self.active_parent_media = None
            if parent:
                for attr in ("current_media_path", "audio_file", "media_path", "current_file"):
                    val = getattr(parent, attr, None)
                    if val and os.path.isfile(str(val)):
                        self.active_parent_media = str(val)
                        break

            self.custom_selected_path = self.active_parent_media
            self.engine = BenchmarkEngine(quick=False)
            self.worker_thread: Optional[BenchmarkWorker] = None
            self.download_worker: Optional[SampleDownloadWorker] = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(10)

            # Header & System Specs
            header_layout = QVBoxLayout()
            title_lbl = QLabel("System Performance & Speed Benchmark")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_lbl.setFont(title_font)
            header_layout.addWidget(title_lbl)

            hw = self.engine.hardware_profile
            gpu_str = (
                f"GPU: {hw['gpu_devices'][0]['name']}"
                if hw.get("gpu_devices")
                else "Hardware: CPU Execution Mode"
            )
            ram_str = f" | {hw['total_ram_gb']} GB RAM" if "total_ram_gb" in hw else ""
            subtitle_lbl = QLabel(
                f"Profiles throughput, Real-Time Factor (RTF), memory footprints, and pipeline speeds.\n"
                f"System: {hw['processor']} ({hw['cpu_count_logical']} logical cores{ram_str}) | {gpu_str}"
            )
            subtitle_lbl.setWordWrap(True)
            subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            header_layout.addWidget(subtitle_lbl)
            layout.addLayout(header_layout)

            # Top Banners Container
            banners_layout = QHBoxLayout()
            banners_layout.setSpacing(10)

            # Score Card Banner
            self.score_card = QFrame()
            self.score_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(30, 41, 59, 0.7);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            score_layout = QVBoxLayout(self.score_card)
            score_layout.setContentsMargins(10, 8, 10, 8)
            score_layout.setSpacing(4)

            self.score_lbl = QLabel("RTVS Hardware Score: Ready")
            self.score_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
            score_layout.addWidget(self.score_lbl)

            self.tier_lbl = QLabel("Run benchmark to evaluate hardware rating")
            self.tier_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: 500;")
            score_layout.addWidget(self.tier_lbl)

            banners_layout.addWidget(self.score_card, stretch=2)

            # Estimated Processing Times Banner
            self.est_card = QFrame()
            self.est_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.7);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            est_layout = QVBoxLayout(self.est_card)
            est_layout.setContentsMargins(10, 8, 10, 8)
            est_layout.setSpacing(4)

            est_header_row = QHBoxLayout()
            self.est_title_lbl = QLabel("Estimated 30-Min Audio Process Time:")
            self.est_title_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #f8fafc;")
            est_header_row.addWidget(self.est_title_lbl)
            est_header_row.addStretch()

            asr_lbl = QLabel("Engine:")
            asr_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
            est_header_row.addWidget(asr_lbl)

            self.asr_combo = QComboBox()
            self.asr_combo.addItems([
                "Parakeet TDT (FastConformer ONNX)",
                "Whisper INT8 (Encoder-Decoder)"
            ])
            self.asr_combo.setToolTip("Switch ASR engine model to recalculate projected turnaround times")
            self.asr_combo.currentIndexChanged.connect(self._update_estimates_display)
            est_header_row.addWidget(self.asr_combo)
            est_layout.addLayout(est_header_row)

            self.est_summary_lbl = QLabel("Transcription: -- | Diarization: -- | Story: -- | Total: --")
            self.est_summary_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            est_layout.addWidget(self.est_summary_lbl)

            banners_layout.addWidget(self.est_card, stretch=3)
            layout.addLayout(banners_layout)

            # Audio Source Selection & Management Card
            self.source_card = QFrame()
            self.source_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.5);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
            source_card_layout = QVBoxLayout(self.source_card)
            source_card_layout.setContentsMargins(10, 8, 10, 8)
            source_card_layout.setSpacing(6)

            src_row1 = QHBoxLayout()
            src_lbl = QLabel("Audio Source:")
            src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #f8fafc;")
            src_row1.addWidget(src_lbl)

            self.source_combo = QComboBox()
            self.source_combo.addItems([
                "Synthetic RAM Stream (Zero Disk Footprint, Instant)",
                "Standard 30-Min Broadcast Sample (MP3 ~6.9 MB)",
                "Custom Audio File / Active Timeline Media...",
            ])
            self.source_combo.currentIndexChanged.connect(self._on_source_changed)
            src_row1.addWidget(self.source_combo, stretch=1)

            # Sample Action Buttons
            self.sample_action_btn = QPushButton("Download Sample (~6.9 MB)")
            self.sample_action_btn.clicked.connect(self._on_sample_action_clicked)
            src_row1.addWidget(self.sample_action_btn)

            self.delete_sample_btn = QPushButton("Delete Sample")
            self.delete_sample_btn.setToolTip("Delete local sample MP3 file to free up ~6.9 MB of disk space")
            self.delete_sample_btn.setStyleSheet("color: #f87171;")
            self.delete_sample_btn.clicked.connect(self._on_delete_sample_clicked)
            src_row1.addWidget(self.delete_sample_btn)

            self.browse_custom_btn = QPushButton("Browse...")
            self.browse_custom_btn.clicked.connect(self._on_browse_custom_clicked)
            src_row1.addWidget(self.browse_custom_btn)

            source_card_layout.addLayout(src_row1)

            # Source Details / Download Progress Row
            src_row2 = QHBoxLayout()
            self.source_status_lbl = QLabel("Ready")
            self.source_status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            src_row2.addWidget(self.source_status_lbl, stretch=1)

            self.download_progress_bar = QProgressBar()
            self.download_progress_bar.setRange(0, 100)
            self.download_progress_bar.setValue(0)
            self.download_progress_bar.setFixedWidth(180)
            self.download_progress_bar.setVisible(False)
            src_row2.addWidget(self.download_progress_bar)

            source_card_layout.addLayout(src_row2)
            layout.addWidget(self.source_card)

            # Progress Bar & Duration / Rigor Selector
            top_controls = QVBoxLayout()
            top_controls.setSpacing(4)

            dur_row = QHBoxLayout()
            dur_lbl = QLabel("Benchmark Rigor / Duration:")
            dur_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #f8fafc;")
            dur_row.addWidget(dur_lbl)

            self.duration_combo = QComboBox()
            self.duration_combo.addItems([
                "⚡ Quick Mode (1 Min Audio | ~3–5s Evaluation)",
                "🎯 Standard Benchmark (5 Min Audio | ~15–25s Run) [Recommended]",
                "🔥 Sustained Stress (10 Min Audio | ~45–90s Run)",
                "🏔️ Full 30-Min Endurance (30 Min Audio | ~2–5m Run)",
            ])
            self.duration_combo.setCurrentIndex(1)  # Default: Standard (5 min)
            self.duration_combo.setToolTip("Select workload scale and audio duration to balance speed vs thermal/boost clock evaluation")
            self.duration_combo.currentIndexChanged.connect(self._on_duration_changed)
            dur_row.addWidget(self.duration_combo, stretch=1)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.engine.metrics))
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%v / %m Tests Completed")
            self.progress_bar.setFixedWidth(240)
            dur_row.addWidget(self.progress_bar)

            top_controls.addLayout(dur_row)

            self.duration_desc_lbl = QLabel("")
            self.duration_desc_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; padding-left: 2px;")
            top_controls.addWidget(self.duration_desc_lbl)
            layout.addLayout(top_controls)

            # Metrics Tree
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Subsystem / Benchmark", "Status", "Duration", "Score", "Throughput / Details"])
            self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.tree.setAlternatingRowColors(True)
            layout.addWidget(self.tree)

            self._populate_tree()

            # Footer Controls
            btn_layout = QHBoxLayout()
            self.run_btn = QPushButton("Run Benchmark (5-Min Audio)")
            self.run_btn.setStyleSheet("font-weight: bold; padding: 6px 16px;")
            self.run_btn.clicked.connect(self._on_run_clicked)

            self.stop_btn = QPushButton("Cancel")
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self._on_stop_clicked)

            self.copy_btn = QPushButton("Copy Report to Clipboard")
            self.copy_btn.clicked.connect(self._on_copy_clicked)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.accept)

            btn_layout.addWidget(self.run_btn)
            btn_layout.addWidget(self.stop_btn)
            btn_layout.addWidget(self.copy_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(self.close_btn)
            layout.addLayout(btn_layout)

            # Auto-select sample audio if present
            sample_present = find_available_sample_audio() is not None
            if sample_present:
                self.source_combo.setCurrentIndex(1)
            else:
                self.source_combo.setCurrentIndex(0)
            self._update_source_ui()
            self._update_duration_desc()

        def _get_selected_duration_mode(self) -> str:
            if not hasattr(self, "duration_combo"):
                return "standard"
            idx = self.duration_combo.currentIndex()
            mode_keys = ["quick", "standard", "sustained", "full"]
            if 0 <= idx < len(mode_keys):
                return mode_keys[idx]
            return "standard"

        def _update_duration_desc(self):
            mode = self._get_selected_duration_mode()
            info = BenchmarkEngine.DURATION_MODES.get(mode, BenchmarkEngine.DURATION_MODES["standard"])
            if hasattr(self, "duration_desc_lbl"):
                self.duration_desc_lbl.setText(f"ℹ️ {info['name']}: {info['description']} (Est. duration: {info['estimate_runtime']})")
            dur_label = f"{int(info['audio_seconds'] // 60)}-Min Audio" if info['audio_seconds'] >= 60 else f"{int(info['audio_seconds'])}s Audio"
            if hasattr(self, "run_btn"):
                self.run_btn.setText(f"Run Benchmark ({dur_label})")

        def _on_duration_changed(self):
            self._update_duration_desc()

        def _update_source_ui(self):
            idx = self.source_combo.currentIndex()
            sample_path = find_available_sample_audio()

            if idx == 0:  # Synthetic
                self.sample_action_btn.setVisible(False)
                self.delete_sample_btn.setVisible(False)
                self.browse_custom_btn.setVisible(False)
                self.source_status_lbl.setText("Zero-disk synthetic speech fixture (instant RAM allocation).")
            elif idx == 1:  # Sample Audio
                self.browse_custom_btn.setVisible(False)
                if sample_path:
                    mb = sample_path.stat().st_size / (1024 * 1024)
                    self.sample_action_btn.setVisible(False)
                    self.delete_sample_btn.setVisible(True)
                    self.source_status_lbl.setText(f"✓ Broadcast sample ready ({sample_path.name}, {mb:.1f} MB, ~30m). Tests FFmpeg decoding & real speech.")
                else:
                    self.sample_action_btn.setVisible(True)
                    self.sample_action_btn.setText("📥 Download Sample (~6.9 MB)")
                    self.delete_sample_btn.setVisible(False)
                    self.source_status_lbl.setText("✗ Sample not downloaded. Click 'Download Sample' to fetch from GitHub.")
            elif idx == 2:  # Custom Audio
                self.sample_action_btn.setVisible(False)
                self.delete_sample_btn.setVisible(False)
                self.browse_custom_btn.setVisible(True)
                if self.custom_selected_path and os.path.isfile(self.custom_selected_path):
                    p = Path(self.custom_selected_path)
                    mb = p.stat().st_size / (1024 * 1024)
                    self.source_status_lbl.setText(f"Selected Media: {p.name} ({mb:.1f} MB)")
                else:
                    self.source_status_lbl.setText("No custom file selected. Click 'Browse...' to select an audio or video file.")

        def _on_source_changed(self):
            self._update_source_ui()

        def _on_browse_custom_clicked(self):
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Audio or Video File for Benchmark",
                "",
                "Media Files (*.mp3 *.wav *.mp4 *.m4a *.aac *.flac *.ogg *.mkv *.avi);;All Files (*)",
            )
            if file_path:
                self.custom_selected_path = file_path
                self._update_source_ui()

        def _on_sample_action_clicked(self):
            if self.download_worker and self.download_worker.isRunning():
                return
            self.download_progress_bar.setVisible(True)
            self.download_progress_bar.setValue(0)
            self.sample_action_btn.setEnabled(False)
            self.source_status_lbl.setText("Initiating sample download from GitHub...")

            self.download_worker = SampleDownloadWorker()
            self.download_worker.progress.connect(self._on_download_progress)
            self.download_worker.finished.connect(self._on_download_finished)
            self.download_worker.start()

        def _on_download_progress(self, pct: int, msg: str):
            self.download_progress_bar.setValue(pct)
            self.source_status_lbl.setText(msg)

        def _on_download_finished(self, ok: bool, msg: str):
            self.download_progress_bar.setVisible(False)
            self.sample_action_btn.setEnabled(True)
            if ok:
                self._update_source_ui()
                QMessageBox.information(self, "Download Complete", "The benchmark broadcast sample audio file has been downloaded successfully.")
            else:
                self.source_status_lbl.setText(f"Download failed: {msg}")
                QMessageBox.warning(self, "Download Error", f"Could not download sample audio file:\n\n{msg}")

        def _on_delete_sample_clicked(self):
            res = QMessageBox.question(
                self,
                "Delete Sample Audio?",
                "Are you sure you want to delete the local broadcast sample audio file to free up ~6.9 MB of disk space?\n\nYou can re-download it anytime from the benchmark dialog.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res == QMessageBox.StandardButton.Yes:
                ok, freed, msg = delete_sample_audio_files()
                self._update_source_ui()
                if ok:
                    QMessageBox.information(self, "Sample Deleted", msg)
                else:
                    QMessageBox.warning(self, "Delete Result", msg)

        def _populate_tree(self):
            self.tree.clear()
            self.tree_items = {}
            for m in self.engine.metrics:
                item = QTreeWidgetItem([m.name, m.status, "", "", m.notes])
                self.tree.addTopLevelItem(item)
                self.tree_items[m.name] = item

        def _on_run_clicked(self):
            idx = self.source_combo.currentIndex()
            mode = "synthetic" if idx == 0 else ("sample" if idx == 1 else "custom")
            duration_mode = self._get_selected_duration_mode()

            self.engine = BenchmarkEngine(
                duration_mode=duration_mode,
                audio_source_mode=mode,
                custom_audio_path=self.custom_selected_path,
            )
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.duration_combo.setEnabled(False)
            self.source_combo.setEnabled(False)
            self.sample_action_btn.setEnabled(False)
            self.delete_sample_btn.setEnabled(False)
            self.browse_custom_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.score_lbl.setText("Running benchmark suite...")
            self.tier_lbl.setText("Evaluating subsystem throughput...")
            self.est_summary_lbl.setText("Calculating processing throughput...")
            self._populate_tree()

            self.worker_thread = BenchmarkWorker(self.engine)
            self.worker_thread.item_updated.connect(self._on_item_updated)
            self.worker_thread.finished.connect(self._on_benchmarks_finished)
            self.worker_thread.start()

        def _on_stop_clicked(self):
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop()
                self.stop_btn.setEnabled(False)

        def _on_item_updated(self, metric: BenchmarkMetric):
            item = self.tree_items.get(metric.name)
            if not item:
                return
            item.setText(1, metric.status)
            if metric.duration_seconds > 0:
                item.setText(2, f"{metric.duration_seconds:.2f}s")
            if metric.score_points > 0:
                item.setText(3, f"{metric.score_points:,} pts")
            item.setText(4, metric.notes)

            if metric.status == "COMPLETED":
                item.setForeground(1, QColor("#16a34a"))  # Green
            elif metric.status == "FAILED":
                item.setForeground(1, QColor("#dc2626"))  # Red
            elif metric.status == "RUNNING":
                item.setForeground(1, QColor("#2563eb"))  # Blue
            elif metric.status == "SKIPPED":
                item.setForeground(1, QColor("#ca8a04"))  # Yellow

            completed_count = sum(1 for m in self.engine.metrics if m.status in ("COMPLETED", "FAILED", "SKIPPED"))
            self.progress_bar.setValue(completed_count)

        def _update_estimates_display(self):
            if not self.engine.processing_estimates:
                return
            est = self.engine.processing_estimates
            is_parakeet = (self.asr_combo.currentIndex() == 0)

            if is_parakeet:
                trans_sec = est.transcription_parakeet_seconds
                trans_rtf = est.transcription_parakeet_rtf
                total_sec = est.total_with_parakeet_seconds
                total_rtf = est.total_with_parakeet_rtf
                model_name = "Parakeet"
            else:
                trans_sec = est.transcription_whisper_seconds
                trans_rtf = est.transcription_whisper_rtf
                total_sec = est.total_with_whisper_seconds
                total_rtf = est.total_with_whisper_rtf
                model_name = "Whisper"

            trans_str = f"{format_duration_estimate(trans_sec)} ({trans_rtf:.1f}x)"
            diar_str = format_duration_estimate(est.diarization_seconds)
            story_str = format_duration_estimate(est.story_detection_seconds)
            total_str = format_duration_estimate(total_sec)
            trans_label = (
                f"Translate: {format_duration_estimate(est.translation_seconds)}"
                if est.translation_installed
                else "Translate: Off"
            )
            self.est_title_lbl.setText(
                f"Est. 30-Min Audio ({model_name}): {total_str} ({total_rtf:.1f}x RTF)"
            )
            self.est_summary_lbl.setText(
                f"{model_name}: {trans_str} | Diarize: {diar_str} | Stories: {story_str} | {trans_label}"
            )

        def _on_benchmarks_finished(self):
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.duration_combo.setEnabled(True)
            self.source_combo.setEnabled(True)
            self.sample_action_btn.setEnabled(True)
            self.delete_sample_btn.setEnabled(True)
            self.browse_custom_btn.setEnabled(True)

            score = self.engine.composite_score
            tier = self.engine.hardware_tier
            self.score_lbl.setText(f"RTVS Hardware Score: {score:,} pts")
            self.tier_lbl.setText(f"Rating Tier: {tier}")

            self._update_estimates_display()

        def _on_copy_clicked(self):
            lines = [
                "Radio & TV Story Segmenter — System Performance Benchmark Report",
                "=" * 65,
                f"Platform : {self.engine.hardware_profile['platform']}",
                f"CPU      : {self.engine.hardware_profile['processor']} ({self.engine.hardware_profile['cpu_count_logical']} cores)",
            ]
            if "total_ram_gb" in self.engine.hardware_profile:
                lines.append(f"RAM      : {self.engine.hardware_profile['total_ram_gb']} GB")
            dur_info = self.engine.DURATION_MODES.get(self.engine.duration_mode, self.engine.DURATION_MODES["standard"])
            lines.append(f"Rigor    : {dur_info['name']} ({dur_info['audio_seconds']}s audio window)")
            lines.append(f"Audio    : {self.engine.audio_source_description or 'Synthetic RAM Stream'}")
            lines.append("-" * 65)
            for m in self.engine.metrics:
                score_str = f" [{m.score_points:,} pts]" if m.score_points > 0 else ""
                lines.append(f"[{m.status}] {m.name} ({m.duration_seconds:.2f}s){score_str}: {m.notes}")
            lines.append("=" * 65)
            lines.append(f"RTVS HARDWARE SCORE: {self.engine.composite_score:,} pts  ({self.engine.hardware_tier})")
            if self.engine.score_breakdown:
                lines.append("-" * 65)
                lines.append("Subsystem Breakdown:")
                for cat, pts in self.engine.score_breakdown.items():
                    lines.append(f"  • {cat.ljust(22)} : {pts:,} pts")

            if self.engine.processing_estimates:
                est = self.engine.processing_estimates
                lines.append("-" * 65)
                lines.append("Estimated Processing Times (30-Minute Broadcast Audio):")
                lines.append(f"  • Story & Boundary Detection   : {est.details.get('story_detection', '')}")
                lines.append(f"  • AI Transcription (Parakeet)  : {est.details.get('transcription_parakeet', '')}")
                lines.append(f"  • AI Transcription (Whisper)   : {est.details.get('transcription_whisper', '')}")
                lines.append(f"  • Speaker Diarization          : {est.details.get('diarization', '')}")
                lines.append(f"  • Neural Translation           : {est.details.get('translation', '')}")
                lines.append("  " + "-" * 59)
                lines.append(f"  • Complete Pipeline (Parakeet) : {est.details.get('total_with_parakeet', '')}")
                lines.append(f"  • Complete Pipeline (Whisper)  : {est.details.get('total_with_whisper', '')}")

            lines.append("=" * 65)

            report_text = "\n".join(lines)
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(report_text)
                self.copy_btn.setText("Copied!")
                QApplication.processEvents()

    return BenchmarkDialog(parent=parent)


if __name__ == "__main__":
    if "--download-sample" in sys.argv:
        print(f"Downloading benchmark sample audio file from GitHub...")
        try:
            target = download_sample_audio(progress_callback=lambda pct, msg: print(f"  [{pct}%] {msg}"))
            print(f"Success: Sample downloaded to {target}")
            sys.exit(0)
        except Exception as err:
            print(f"Error downloading sample: {err}", file=sys.stderr)
            sys.exit(1)

    if "--delete-sample" in sys.argv:
        ok, freed, msg = delete_sample_audio_files()
        print(msg)
        sys.exit(0 if ok else 1)

    dur_mode = "standard"
    if "--quick" in sys.argv:
        dur_mode = "quick"
    elif "--sustained" in sys.argv or "--10min" in sys.argv:
        dur_mode = "sustained"
    elif "--full" in sys.argv or "--30min" in sys.argv:
        dur_mode = "full"
    elif "--standard" in sys.argv or "--5min" in sys.argv:
        dur_mode = "standard"
    else:
        for arg in sys.argv:
            if arg.startswith("--duration="):
                val = arg.split("=", 1)[1].strip().lower()
                if val in BenchmarkEngine.DURATION_MODES:
                    dur_mode = val

    is_json = "--json" in sys.argv
    use_sample = "--sample" in sys.argv or "--sample-audio" in sys.argv

    custom_file_arg = None
    if "--file" in sys.argv:
        try:
            idx = sys.argv.index("--file")
            custom_file_arg = sys.argv[idx + 1]
        except (ValueError, IndexError):
            pass

    if "--gui" in sys.argv:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        dlg = create_benchmark_dialog()
        dlg.exec()
        sys.exit(0)
    else:
        sys.exit(run_cli_benchmark(duration_mode=dur_mode, as_json=is_json, use_sample=use_sample, custom_file=custom_file_arg))

#!/usr/bin/env python3
"""Radio & TV Story Segmenter — Performance & Speed Benchmark Engine.

Measures system throughput, multi-core scaling, memory footprints, and compute
speeds across the core processing pipeline without requiring external media assets:
- Waveform peak & multi-resolution envelope extraction (MB/s and Real-Time Factor).
- Audio STFT & 80-bin Mel-scale filterbank extraction (AI feature pre-processing).
- Multi-threaded concurrent speech segmentation (multi-core scaling efficiency).
- Speaker diarization high-dimensional vector search & clustering (comparisons/sec).
- Project serialization, deserialization & story interval graph indexing (MB/s).
- UI transcript text formatting, word tokenization & lexical search throughput.
- Neural transformer self-attention matrix compute kernel (GFLOPS).
- Composite Hardware Performance Score ("RTVS Hardware Score") for hardware comparison.

Callable via:
  1. CLI: python benchmark.py [--quick] [--json]
  2. RadioTVSegmenter CLI: RadioTVSegmenter.exe --benchmark [--quick] [--json]
  3. Integrated GUI: Help -> Run Performance Benchmark... (Ctrl+Shift+B)
"""

from __future__ import annotations

import io
import json
import math
import os
import platform
import struct
import sys
import time
import tracemalloc
import wave
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


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


# ---------------------------------------------------------------------------
# Core Benchmark Runner Engine
# ---------------------------------------------------------------------------

class BenchmarkEngine:
    """Executes high-precision performance throughput benchmarks."""

    def __init__(self, quick: bool = False):
        self.quick = quick
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

    def run_all(self, stop_requested_fn: Optional[Callable[[], bool]] = None) -> List[BenchmarkMetric]:
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

    # 1. Waveform Peak & Multi-Tier Envelope Extraction
    def _bench_waveform_peak_extraction(self, metric: BenchmarkMetric):
        audio_duration = 20.0 if self.quick else 60.0
        wav_bytes = generate_benchmark_audio(duration_seconds=audio_duration)
        data_size_mb = len(wav_bytes) / (1024 * 1024)

        t0 = time.perf_counter()
        raw_pcm = wav_bytes[44:]
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
            vals = struct.unpack(f"<160h", chunk)
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
        metric.notes = f"{metric.real_time_factor:,.1f}x RTF ({metric.throughput_mb_s} MB/s, {len(peaks_100)} peak bins + RMS)"

    # 2. Audio STFT & Mel-Scale Filterbank Extraction
    def _bench_audio_stft_and_mel_filterbank(self, metric: BenchmarkMetric):
        num_frames = 150 if self.quick else 450
        fft_size = 256
        num_mel_bins = 80

        # Construct triangular Mel filterbank weights
        mel_filters = [[0.02 * ((k + m) % 7) for k in range(fft_size // 2)] for m in range(num_mel_bins)]
        hanning = [0.5 * (1.0 - math.cos(2.0 * math.pi * n / (fft_size - 1))) for n in range(fft_size)]

        t0 = time.perf_counter()
        total_ops = 0
        for f_idx in range(num_frames):
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
        metric.notes = f"{frames_per_sec:,.0f} Mel frames/sec ({rtf}x RTF, {num_mel_bins} Mel bins)"

    # 3. Multi-Core Speech Segmentation (Scaling Test)
    def _bench_multi_core_speech_segmentation(self, metric: BenchmarkMetric):
        logical_cores = os.cpu_count() or 1
        chunks_per_core = 4 if self.quick else 12
        total_chunks = logical_cores * chunks_per_core

        def _process_audio_chunk(chunk_id: int) -> int:
            window_count = 1500
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
        metric.notes = f"{chunks_per_sec:,.1f} chunks/sec across {logical_cores} cores ({mins_per_sec:.1f} audio mins/sec)"

    # 4. Speaker Diarization High-Dimensional Vector Search
    def _bench_speaker_diarization_vector_search(self, metric: BenchmarkMetric):
        dims = 256
        num_embeddings = 100 if self.quick else 260
        embeddings = [[math.sin(i * 0.2 + j * 0.1) for j in range(dims)] for i in range(num_embeddings)]

        t0 = time.perf_counter()
        norms = [math.sqrt(sum(x * x for x in v)) or 1.0 for v in embeddings]
        sim_count = 0
        similarity_matrix = []

        for i in range(num_embeddings):
            v1, n1 = embeddings[i], norms[i]
            row = []
            for j in range(num_embeddings):
                if i == j:
                    row.append(1.0)
                elif j < i:
                    row.append(similarity_matrix[j][i])
                else:
                    v2, n2 = embeddings[j], norms[j]
                    dot = sum(x * y for x, y in zip(v1, v2))
                    sim = dot / (n1 * n2)
                    row.append(sim)
                    sim_count += 1
            similarity_matrix.append(row)

        # Hierarchical agglomerative clustering centroid pass
        clusters = [[i] for i in range(min(num_embeddings, 20))]
        for _ in range(5):
            # Merge closest pair
            best_sim = -1.0
            best_pair = (0, 1)
            for ci in range(len(clusters)):
                for cj in range(ci + 1, len(clusters)):
                    avg_sim = sum(similarity_matrix[u][v] for u in clusters[ci] for v in clusters[cj]) / (len(clusters[ci]) * len(clusters[cj]))
                    if avg_sim > best_sim:
                        best_sim = avg_sim
                        best_pair = (ci, cj)
            if len(clusters) > 2:
                c1, c2 = best_pair
                merged = clusters[c1] + clusters[c2]
                clusters.pop(max(c1, c2))
                clusters.pop(min(c1, c2))
                clusters.append(merged)

        calc_time = max(0.0001, time.perf_counter() - t0)
        metric.operations_per_sec = round(sim_count / calc_time, 0)
        # Baseline reference: 20,000 comparisons/sec = 1,000 pts
        metric.score_points = int(round((metric.operations_per_sec / 20000.0) * 1000))
        metric.notes = f"{metric.operations_per_sec:,.0f} pairwise comparisons/sec ({num_embeddings} 256-dim turns + clustering)"

    # 5. Project Serialization, Deserialization & Story Interval Graph Indexing
    def _bench_project_serialization_and_indexing(self, metric: BenchmarkMetric):
        num_segments = 300 if self.quick else 1000
        mock_segments = []
        for i in range(num_segments):
            mock_segments.append({
                "id": f"story_{i:04d}",
                "title": f"Investigative Report Segment #{i}",
                "start": round(i * 4.2, 3),
                "end": round((i + 1) * 4.2, 3),
                "fade_in": 0.25,
                "fade_out": 0.50,
                "fade_curve": "exponential",
                "speaker": f"SPEAKER_{(i % 5) + 1}",
                "text": f"Broadcast story segment number {i} with aligned sentence boundaries.",
                "words": [
                    {"word": "Broadcast", "start": round(i * 4.2, 3), "end": round(i * 4.2 + 0.5, 3)},
                    {"word": "story", "start": round(i * 4.2 + 0.5, 3), "end": round(i * 4.2 + 0.9, 3)},
                    {"word": "segment", "start": round(i * 4.2 + 0.9, 3), "end": round(i * 4.2 + 1.4, 3)},
                ],
            })

        project_data = {
            "version": "3.5.0-beta-4",
            "media_file": "high_res_broadcast.wav",
            "duration": round(num_segments * 4.2, 2),
            "stories": mock_segments,
            "metadata": {"title": "Benchmark Project State", "created": time.time()},
        }

        iterations = 5 if self.quick else 15
        t0 = time.perf_counter()
        total_bytes = 0

        for _ in range(iterations):
            encoded = json.dumps(project_data, ensure_ascii=False)
            total_bytes += len(encoded.encode("utf-8"))
            decoded = json.loads(encoded)

            # Build binary interval search index for timeline seeking
            story_starts = [s["start"] for s in decoded["stories"]]
            # Binary search lookup simulation
            for test_time in [10.0, 50.5, 120.0, 300.0, 650.0]:
                idx = 0
                lo, hi = 0, len(story_starts) - 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if story_starts[mid] <= test_time:
                        idx = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1
                assert 0 <= idx < len(story_starts)

        calc_time = max(0.0001, time.perf_counter() - t0)
        mb_total = total_bytes / (1024 * 1024)
        metric.operations_per_sec = round((num_segments * iterations) / calc_time, 0)
        metric.throughput_mb_s = round(mb_total / calc_time, 2)
        # Baseline reference: 15,000 segments/sec = 1,000 pts
        metric.score_points = int(round((metric.operations_per_sec / 15000.0) * 1000))
        metric.notes = f"{metric.operations_per_sec:,.0f} segments/sec ({metric.throughput_mb_s} MB/s JSON throughput + binary index)"

    # 6. Transcript Text Formatting, Token Reflow & Lexical Search
    def _bench_transcript_formatting_and_search(self, metric: BenchmarkMetric):
        num_words = 12000 if self.quick else 35000
        words_vocab = ["investigative", "segment", "broadcast", "anchor", "interview", "audio", "timeline", "cut", "transition"]
        tokens = []
        for i in range(num_words):
            w = words_vocab[i % len(words_vocab)]
            tokens.append({
                "word": w,
                "start": i * 0.35,
                "end": (i + 1) * 0.35,
                "speaker": f"SPEAKER_{(i // 20) % 4 + 1}",
                "highlight": (i % 30 == 0),
            })

        t0 = time.perf_counter()
        # Inverted index for lexical search
        inverted_index: Dict[str, List[int]] = {}
        buffer = []
        current_speaker = None

        for idx, tok in enumerate(tokens):
            w = tok["word"]
            inverted_index.setdefault(w, []).append(idx)

            if tok["speaker"] != current_speaker:
                current_speaker = tok["speaker"]
                buffer.append(f"\n<div class='speaker-block' data-spk='{current_speaker}'>")

            if tok["highlight"]:
                buffer.append(f"<span class='hl' data-t='{tok['start']:.2f}'>{w}</span> ")
            else:
                buffer.append(f"<span data-t='{tok['start']:.2f}'>{w}</span> ")

        formatted_doc = "".join(buffer)

        # Execute 50 fast index query lookups
        search_hits = 0
        for q in ["broadcast", "investigative", "timeline", "missing_term"]:
            hits = inverted_index.get(q, [])
            search_hits += len(hits)

        calc_time = max(0.0001, time.perf_counter() - t0)
        metric.operations_per_sec = round(num_words / calc_time, 0)
        # Baseline reference: 260,000 words/sec = 1,000 pts
        metric.score_points = int(round((metric.operations_per_sec / 260000.0) * 1000))
        metric.notes = f"{metric.operations_per_sec:,.0f} words/sec formatted ({len(formatted_doc):,} chars, inverted index built)"

    # 7. Neural Transformer Self-Attention Kernel
    def _bench_transformer_self_attention_kernel(self, metric: BenchmarkMetric):
        seq_len = 64 if self.quick else 128
        d_head = 64
        num_heads = 4

        q = [[0.05 * math.sin(i + h) for i in range(d_head)] for h in range(seq_len)]
        k = [[0.05 * math.cos(i + h) for i in range(d_head)] for h in range(seq_len)]
        v = [[0.05 * math.sin(i * 2 + h) for i in range(d_head)] for h in range(seq_len)]

        t0 = time.perf_counter()
        total_ops = 0
        scale = 1.0 / math.sqrt(d_head)

        for _ in range(num_heads):
            # Q * K^T
            for i in range(seq_len):
                qi = q[i]
                row = [sum(qi[k_idx] * k[j][k_idx] for k_idx in range(d_head)) * scale for j in range(seq_len)]
                total_ops += seq_len * d_head * 2

                # Softmax
                max_val = max(row)
                exps = [math.exp(x - max_val) for x in row]
                sum_exps = sum(exps) or 1.0
                weights = [e / sum_exps for e in exps]
                total_ops += seq_len * 4

                # Attention * V
                out_vector = [sum(weights[j] * v[j][d_idx] for j in range(seq_len)) for d_idx in range(d_head)]
                total_ops += seq_len * d_head * 2

        calc_time = max(0.0001, time.perf_counter() - t0)
        gflops = (total_ops / calc_time) / 1e9
        metric.operations_per_sec = round(total_ops / calc_time, 0)
        # Baseline reference: 0.008 GFLOPS = 1,000 pts
        metric.score_points = int(round((gflops / 0.008) * 1000))
        metric.notes = f"{gflops:.3f} GFLOPS ({total_ops:,} matrix attention operations, {num_heads} heads)"


# ---------------------------------------------------------------------------
# CLI Execution & Reporting
# ---------------------------------------------------------------------------

def run_cli_benchmark(quick: bool = False, as_json: bool = False) -> int:
    """Run performance benchmarks and print formatted terminal report."""
    engine = BenchmarkEngine(quick=quick)
    if not as_json:
        print("=" * 74)
        print(" Radio & TV Story Segmenter — Performance & Speed Benchmark")
        print("=" * 74)
        hw = engine.hardware_profile
        ram_str = f" | {hw['total_ram_gb']} GB RAM" if "total_ram_gb" in hw else ""
        print(f"Platform : {hw['platform']}")
        print(f"CPU      : {hw['processor']} ({hw['cpu_count_logical']} logical cores{ram_str})")
        if hw.get("gpu_devices"):
            for g in hw["gpu_devices"]:
                print(f"GPU      : {g['name']} ({g['memory_total_mb']} MB VRAM)")
        else:
            print("GPU      : CPU execution mode (No dedicated GPU acceleration)")
        mode_str = "QUICK MODE" if quick else "FULL RIGOROUS SUITE"
        print(f"Suite    : {mode_str} (Zero disk footprint, in-memory RAM tests)")
        print("-" * 74)

    results = engine.run_all()

    if as_json:
        payload = {
            "hardware": engine.hardware_profile,
            "composite_score": engine.composite_score,
            "hardware_tier": engine.hardware_tier,
            "score_breakdown": engine.score_breakdown,
            "metrics": [asdict(m) for m in results],
            "timestamp": time.time(),
        }
        print(json.dumps(payload, indent=2))
        return 0

    for i, m in enumerate(results, start=1):
        status_badge = f"[{m.status}]".ljust(11)
        dur_str = f"({m.duration_seconds:.2f}s)"
        score_badge = f"[{m.score_points:,} pts]".rjust(12) if m.score_points > 0 else ""
        print(f"{i:02d}/{len(results):02d} {status_badge} {m.name.ljust(36)} {dur_str} {score_badge}")
        print(f"       -> {m.notes}")

    print("=" * 74)
    print(f" RTVS HARDWARE PERFORMANCE SCORE: {engine.composite_score:,} pts  ({engine.hardware_tier})")
    print("-" * 74)
    print(" Subsystem Breakdown:")
    for cat, score in engine.score_breakdown.items():
        print(f"   • {cat.ljust(25)} : {score:,} pts")
    print("=" * 74)
    return 0


# ---------------------------------------------------------------------------
# PySide6 Graphical Benchmark Dialog
# ---------------------------------------------------------------------------

def create_benchmark_dialog(parent=None):
    """Factory creating the native PySide6 Benchmark Dialog."""
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
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

    class BenchmarkDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("System Performance & Speed Benchmark")
            self.resize(920, 640)
            self.engine = BenchmarkEngine(quick=False)
            self.worker_thread: Optional[BenchmarkWorker] = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(12)

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

            # Score Card Banner (Prominent hardware rating)
            self.score_card = QFrame()
            self.score_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(30, 41, 59, 0.6);
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            score_layout = QHBoxLayout(self.score_card)
            score_layout.setContentsMargins(12, 6, 12, 6)

            self.score_lbl = QLabel("RTVS Hardware Score: Ready")
            self.score_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
            score_layout.addWidget(self.score_lbl)

            score_layout.addStretch()

            self.tier_lbl = QLabel("Run benchmark to evaluate system rating")
            self.tier_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 500;")
            score_layout.addWidget(self.tier_lbl)

            layout.addWidget(self.score_card)

            # Progress Bar & Quick Toggle
            top_controls = QHBoxLayout()
            self.quick_chk = QCheckBox("Quick Mode (~3s evaluation)")
            self.quick_chk.setChecked(False)
            self.quick_chk.setToolTip("Runs scaled workloads for rapid spot-checking")
            top_controls.addWidget(self.quick_chk)
            top_controls.addStretch()

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.engine.metrics))
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%v / %m Tests Completed")
            self.progress_bar.setFixedWidth(260)
            top_controls.addWidget(self.progress_bar)

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
            self.run_btn = QPushButton("Run Full Benchmark")
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

        def _populate_tree(self):
            self.tree.clear()
            self.tree_items = {}
            for m in self.engine.metrics:
                item = QTreeWidgetItem([m.name, m.status, "", "", m.notes])
                self.tree.addTopLevelItem(item)
                self.tree_items[m.name] = item

        def _on_run_clicked(self):
            self.engine = BenchmarkEngine(quick=self.quick_chk.isChecked())
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.quick_chk.setEnabled(False)
            self.progress_bar.setValue(0)
            self.score_lbl.setText("Running benchmark suite...")
            self.tier_lbl.setText("Evaluating subsystem throughput...")
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

        def _on_benchmarks_finished(self):
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.quick_chk.setEnabled(True)

            score = self.engine.composite_score
            tier = self.engine.hardware_tier
            self.score_lbl.setText(f"RTVS Hardware Score: {score:,} pts")
            self.tier_lbl.setText(f"Rating Tier: {tier}")

        def _on_copy_clicked(self):
            lines = [
                "Radio & TV Story Segmenter — System Performance Benchmark Report",
                "=" * 65,
                f"Platform : {self.engine.hardware_profile['platform']}",
                f"CPU      : {self.engine.hardware_profile['processor']} ({self.engine.hardware_profile['cpu_count_logical']} cores)",
            ]
            if "total_ram_gb" in self.engine.hardware_profile:
                lines.append(f"RAM      : {self.engine.hardware_profile['total_ram_gb']} GB")
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
            lines.append("=" * 65)

            report_text = "\n".join(lines)
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(report_text)
                self.copy_btn.setText("Copied!")
                QApplication.processEvents()

    return BenchmarkDialog(parent=parent)


if __name__ == "__main__":
    is_quick = "--quick" in sys.argv
    is_json = "--json" in sys.argv
    if "--gui" in sys.argv:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        dlg = create_benchmark_dialog()
        dlg.exec()
        sys.exit(0)
    else:
        sys.exit(run_cli_benchmark(quick=is_quick, as_json=is_json))

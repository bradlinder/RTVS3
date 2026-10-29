# benchmark_engine.pyi — Typing and Interface Stub for benchmark_engine
from __future__ import annotations
from __future__ import annotations
import json
import math
import os
import struct
import subprocess
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from benchmark_models import BenchmarkMetric, ProcessingEstimates, decode_audio_file_pcm, find_available_sample_audio, format_duration_estimate, generate_benchmark_audio, get_system_hardware_profile, is_translation_plugin_installed

class BenchmarkEngine:
    DURATION_MODES = ...

    def __init__(self, quick: bool=..., duration_mode: str=..., audio_source_mode: str=..., custom_audio_path: Optional[Union[str, Path]]=...):
        ...

    def _get_target_audio_seconds(self) -> float:
        ...

    def _prepare_audio_source(self):
        ...

    def run_all(self, stop_requested_fn: Optional[Callable[[], bool]]=...) -> List[BenchmarkMetric]:
        ...

    def _compute_composite_score(self):
        ...

    def compute_processing_estimates(self, audio_duration_minutes: float=...) -> ProcessingEstimates:
        ...

    def _bench_waveform_peak_extraction(self, metric: BenchmarkMetric):
        ...

    def _bench_audio_stft_and_mel_filterbank(self, metric: BenchmarkMetric):
        ...

    def _bench_multi_core_speech_segmentation(self, metric: BenchmarkMetric):
        ...

    def _bench_speaker_diarization_vector_search(self, metric: BenchmarkMetric):
        ...

    def _bench_project_serialization_and_indexing(self, metric: BenchmarkMetric):
        ...

    def _bench_transcript_formatting_and_search(self, metric: BenchmarkMetric):
        ...

    def _bench_multi_format_export_generation_throughput(self, metric: BenchmarkMetric):
        ...

    def _bench_transformer_self_attention_kernel(self, metric: BenchmarkMetric):
        ...

    def _bench_ai_background_worker_and_ipc_handshake(self, metric: BenchmarkMetric):
        ...

    def _bench_model_cache_storage_and_cdn_connectivity(self, metric: BenchmarkMetric):
        ...

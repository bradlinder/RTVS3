# worker_diarization_engine.pyi — Typing and Interface Stub for worker_diarization_engine
from __future__ import annotations
from __future__ import annotations
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from worker_diarization_clustering import SHORT_FRAGMENT_MERGE_THRESHOLD, _calculate_embedding_for_interval, _normalize_expected_speakers, _normalize_speaker_labels, _sensitivity_distance_threshold, apply_clustering_patches, assign_short_segments_to_centroids, fast_cluster_ahc
_EMIT_FN: Optional[Callable[..., None]] = ...

def set_emit_callback(fn: Callable[..., None]):
    ...

def _emit(message_type: str, **payload):
    ...

def _safe_tensor_from_numpy(arr):
    ...

def normalize_audio_for_diarization(source_path):
    ...

def configure_optimal_pytorch_threads():
    ...

def _diarize_solo_fast_path(audio_file, transcript_file=...):
    ...

def _get_wespeaker_model():
    ...

def extract_embeddings_batched(audio_path, speech_segments, batch_size=..., min_segment_duration=..., embedding_window=..., embedding_step=..., progress_callback=...):
    ...

def run_vad_two_pass(audio_path, threshold=..., min_speech_duration_ms=..., min_silence_duration_ms=..., speech_pad_ms=..., bridge_pause_threshold_sec=...):
    ...

def run_transcript_guided_diarization(normalized_wav, transcript_file, expected_speakers=..., sensitivity=..., progress_callback=...):
    ...

def diarize(audio_file, expected_speakers=..., transcript_file=..., sensitivity=...):
    ...

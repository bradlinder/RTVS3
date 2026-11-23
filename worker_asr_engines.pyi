# worker_asr_engines.pyi — Typing and Interface Stub for worker_asr_engines
from __future__ import annotations
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from sentence_boundaries import is_ambiguous_abbreviation, is_non_terminal_abbreviation, is_sentence_end
from worker_diarization_engine import normalize_audio_for_diarization
_EMIT_FN: Optional[Callable[..., None]] = ...

def set_emit_callback(fn: Callable[..., None]):
    ...

def _has_speech_energy(audio_slice, sr: int=..., rms_db_thresh: float=..., peak_db_thresh: float=...) -> bool:
    ...

def _decode_onnx_chunk_with_rescue(recognizer: Any, samples: Any, c_start: int, c_end: int, duration_sec: float, is_word_boundary_fn: Optional[Callable[[str], bool]]=...) -> Tuple[str, List[Dict[str, Any]]]:
    ...

def _group_onnx_words_into_segments(chunk_words: List[Dict[str, Any]], duration_sec: float, language: Optional[str]=...) -> List[Dict[str, Any]]:
    ...

def _emit(message_type: str, **payload):
    ...

def _patch_av_open():
    ...

def get_optimal_transcription_threads() -> int:
    ...

def get_app_data_dir_pure() -> Path:
    ...

def get_models_storage_dir_pure() -> Path:
    ...

def is_onnx_model_available(model_name: str) -> bool:
    ...

def transcribe_parakeet_onnx(audio_file, model_name=..., detected_lang=..., detected_confidence=..., initial_prompt=..., beam_size=...):
    ...

def probe_audio_language(audio_file, sample_duration=..., preferred_model=...):
    ...

def transcribe(audio_file, model_name, initial_prompt=..., beam_size=...):
    ...

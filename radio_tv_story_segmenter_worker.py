#!/usr/bin/env python3
"""Radio & TV Story Segmenter — AI Background Subprocess Worker Facade.

Dispatches ASR transcription, neural VAD, and WeSpeaker speaker diarization pipelines.
Decomposed in Wave 4 into focused domain submodules:
  - worker_ipc.py: Subprocess JSON IPC protocol, stream buffering, and DLL directories.
  - worker_asr_engines.py: Faster-Whisper, CTranslate2, and Sherpa-ONNX Parakeet transcription.
  - worker_diarization_engine.py: Silero Neural VAD, WeSpeaker embeddings, and diarization.
  - worker_clustering.py: Agglomerative hierarchical clustering and pause bridging.
  - worker_story_engine.py: Acoustic and lexical story boundary detection.
"""

from __future__ import annotations

import os
import sys
from typing import Any, List, Optional

# Re-exports from worker_ipc
from worker_ipc import (
    emit,
    emit_hello,
    _patch_av_open,
    _clamp_diarization_thread_env,
    _setup_windows_dll_directories,
    _safe_tensor_from_numpy,
)

# Re-exports from worker_asr_engines
from worker_asr_engines import (
    get_optimal_transcription_threads,
    get_app_data_dir_pure,
    get_models_storage_dir_pure,
    is_onnx_model_available,
    transcribe_parakeet_onnx,
    probe_audio_language,
    transcribe,
)

# Re-exports from worker_clustering
from worker_clustering import (
    normalize_audio_for_diarization,
    configure_optimal_pytorch_threads,
    _normalize_expected_speakers,
    _normalize_speaker_labels,
    _sensitivity_distance_threshold,
    fast_cluster_ahc,
    apply_clustering_patches,
    run_vad_two_pass,
    assign_short_segments_to_centroids,
    _calculate_embedding_for_interval,
)

# Re-exports from worker_diarization_engine
from worker_diarization_engine import (
    _diarize_solo_fast_path,
    _get_wespeaker_model,
    extract_embeddings_batched,
    run_transcript_guided_diarization,
    diarize,
)

# Re-exports from worker_story_engine
from worker_story_engine import (
    is_real_speech,
    detect_story_boundaries,
)

__all__ = [
    # IPC & Environment
    "emit",
    "emit_hello",
    "_patch_av_open",
    "_clamp_diarization_thread_env",
    "_setup_windows_dll_directories",
    "_safe_tensor_from_numpy",
    # ASR
    "get_optimal_transcription_threads",
    "get_app_data_dir_pure",
    "get_models_storage_dir_pure",
    "is_onnx_model_available",
    "transcribe_parakeet_onnx",
    "probe_audio_language",
    "transcribe",
    # Clustering & VAD
    "normalize_audio_for_diarization",
    "configure_optimal_pytorch_threads",
    "_normalize_expected_speakers",
    "_normalize_speaker_labels",
    "_sensitivity_distance_threshold",
    "fast_cluster_ahc",
    "apply_clustering_patches",
    "run_vad_two_pass",
    "assign_short_segments_to_centroids",
    "_calculate_embedding_for_interval",
    # Diarization
    "_diarize_solo_fast_path",
    "_get_wespeaker_model",
    "extract_embeddings_batched",
    "run_transcript_guided_diarization",
    "diarize",
    # Story
    "is_real_speech",
    "detect_story_boundaries",
    # CLI
    "main",
]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Handle multiprocessing -c or freeze support invocations in case main() is invoked with custom argv
    if "-c" in argv:
        try:
            c_idx = argv.index("-c")
            if c_idx + 1 < len(argv):
                code_str = argv[c_idx + 1]
                exec(code_str, {"__name__": "__main__"})
                return 0
        except Exception as _e:
            sys.stderr.write(f"[MULTIPROCESSING] Error executing -c in main(): {_e}\n")
            return 1

    # Strip any leading Python interpreter or wrapper arguments (e.g. -B, -u, --prs-worker, --worker)
    valid_modes = {"--transcribe", "--diarize", "--self-test"}
    while argv and argv[0] not in valid_modes and argv[0].startswith("-"):
        argv = argv[1:]

    emit_hello()
    if len(argv) < 1:
        emit("error", message="No processing mode was specified.")
        return 2

    mode = argv[0]
    if mode == "--self-test":
        failures = []
        checks = []
        def _check(label, fn):
            try:
                value = fn()
                checks.append(f"[SELF-TEST] {label}: PASS" + (f" ({value})" if value else ""))
            except Exception as exc:
                failures.append((label, exc))
                checks.append(f"[SELF-TEST] {label}: FAIL: {type(exc).__name__}: {exc}")
        def _torch_location_diagnostic():
            import importlib.util
            spec = importlib.util.find_spec("torch._C")
            return str(spec.origin if spec and spec.origin else "not-found")
        _check("PyTorch _C module discovery", _torch_location_diagnostic)
        _check("PyTorch", lambda: __import__("torch").__version__)
        _check("PyTorch C extension", lambda: str(__import__("torch")._C))
        _check("PyTorch tensor operation", lambda: str(__import__("torch").tensor([1, 2, 3]).tolist()))
        _check("torchaudio", lambda: __import__("torchaudio").__version__)
        _check("CTranslate2", lambda: __import__("ctranslate2").__version__)
        _check("Silero VAD", lambda: __import__("silero_vad").__name__)
        _check("NumPy", lambda: __import__("numpy").__version__)
        _check("SciPy", lambda: __import__("scipy").__version__)
        _check("Scikit-Learn", lambda: __import__("sklearn").__version__)
        _check("WeSpeaker Runtime", lambda: __import__("wespeakerruntime").__name__)
        def _check_diarize_full():
            import diarize
            import diarize.embeddings
            import diarize.clustering
            import diarize.vad
            import diarize.utils
            return diarize.__name__
        _check("diarize (full pipeline)", _check_diarize_full)
        try:
            import transformers
            checks.append(f"[SELF-TEST] Transformers (Optional/Plugin): PASS ({transformers.__version__})")
        except ImportError:
            checks.append("[SELF-TEST] Transformers (Optional/Plugin): Skipped (Isolated in translation plugin runtime)")
        for line in checks:
            print(line, flush=True)
        return 1 if failures else 0

    if mode == "--transcribe":
        if len(argv) < 3:
            emit("error", message="Transcription worker requires an audio-file path and model name.")
            return 2
        initial_prompt = argv[3] if len(argv) >= 4 else ""
        beam_size = int(argv[4]) if len(argv) >= 5 and str(argv[4]).isdigit() else 5
        return transcribe(argv[1], argv[2], initial_prompt, beam_size=beam_size)

    if mode == "--diarize":
        if len(argv) < 2:
            emit("error", message="Speaker Detection worker requires an audio-file path.")
            return 2
        audio_path = argv[1]
        expected_speakers = "auto"
        transcript_file = None
        sensitivity = "normal"
        i = 2
        while i < len(argv):
            arg = argv[i]
            if arg == "--expected-speakers" and i + 1 < len(argv):
                expected_speakers = argv[i + 1]
                i += 2
            elif arg in ("--diarization-sensitivity", "--sensitivity") and i + 1 < len(argv):
                sensitivity = argv[i + 1]
                i += 2
            elif arg == "--transcript-file" and i + 1 < len(argv):
                transcript_file = argv[i + 1]
                i += 2
            elif not arg.startswith("--"):
                expected_speakers = arg
                i += 1
            else:
                i += 1
        return diarize(audio_path, expected_speakers, transcript_file=transcript_file, sensitivity=sensitivity)

    emit("error", message=f"Unknown processing mode: {mode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

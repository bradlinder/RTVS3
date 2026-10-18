#!/usr/bin/env python3
"""Radio & TV Story Segmenter — Performance & Speed Benchmark Engine.

Hardware diagnostic suite and processing speed benchmark for ASR models,
diarization clustering, export throughput, and audio processing.

Decomposed in Wave 4 into focused domain submodules:
  - benchmark_models.py: Data models, sample audio retrieval, and hardware profiling.
  - benchmark_engine.py: Multi-stage benchmark execution engine and metrics.
  - benchmark_dialog.py: PySide6 graphical benchmark dialog and worker threads.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Re-exports from benchmark_models
from benchmark_models import (
    BenchmarkMetric,
    ProcessingEstimates,
    get_app_data_dir,
    get_candidate_sample_audio_paths,
    find_available_sample_audio,
    get_sample_audio_target_path,
    delete_sample_audio_files,
    download_sample_audio,
    decode_audio_file_pcm,
    _get_seed_speech_pcm,
    generate_benchmark_audio,
    get_system_hardware_profile,
    is_translation_plugin_installed,
    format_duration_estimate,
)

# Re-exports from benchmark_engine
from benchmark_engine import BenchmarkEngine

# Re-exports from benchmark_dialog
from benchmark_dialog import create_benchmark_dialog

__all__ = [
    # Models & Hardware
    "BenchmarkMetric",
    "ProcessingEstimates",
    "get_app_data_dir",
    "get_candidate_sample_audio_paths",
    "find_available_sample_audio",
    "get_sample_audio_target_path",
    "delete_sample_audio_files",
    "download_sample_audio",
    "decode_audio_file_pcm",
    "_get_seed_speech_pcm",
    "generate_benchmark_audio",
    "get_system_hardware_profile",
    "is_translation_plugin_installed",
    "format_duration_estimate",
    # Engine & Dialog
    "BenchmarkEngine",
    "create_benchmark_dialog",
    # CLI
    "run_cli_benchmark",
    "main",
]


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
            total_m = len(engine.metrics)
            print(f"{idx:02d}/{total_m:02d} [{stat}] {m.name.ljust(38)} ({m.duration_seconds:.2f}s) {score_str}")
            print(f"       -> {m.notes}")

    engine.on_update = _cli_update
    engine.run_all()

    completed_features = sum(1 for m in engine.metrics if m.status == "COMPLETED")
    total_features = len(engine.metrics)
    feature_pct = (completed_features / total_features) * 100 if total_features else 0

    if as_json:
        data = {
            "hardware_profile": engine.hardware_profile,
            "composite_score": engine.composite_score,
            "hardware_tier": engine.hardware_tier,
            "duration_mode": engine.duration_mode,
            "feature_verification": {
                "completed": completed_features,
                "total": total_features,
                "percentage": round(feature_pct, 1),
            },
            "score_breakdown": engine.score_breakdown,
            "audio_source": engine.audio_source_description,
            "processing_estimates_30min": asdict(engine.processing_estimates) if engine.processing_estimates else None,
            "metrics": [asdict(m) for m in engine.metrics],
        }
        print(json.dumps(data, indent=2))
        return 0

    print("=" * 74)
    print(f" USER-FACING FEATURE VERIFICATION: {completed_features}/{total_features} Functional ({feature_pct:.0f}% Verified)")
    print(f" RTVS HARDWARE PERFORMANCE SCORE : {engine.composite_score:,} pts  ({engine.hardware_tier})")
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


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if "--download-sample" in argv:
        print(f"Downloading benchmark sample audio file from GitHub...")
        try:
            target = download_sample_audio(progress_callback=lambda pct, msg: print(f"  [{pct}%] {msg}"))
            print(f"Success: Sample downloaded to {target}")
            return 0
        except Exception as err:
            print(f"Error downloading sample: {err}", file=sys.stderr)
            return 1

    if "--delete-sample" in argv:
        ok, freed, msg = delete_sample_audio_files()
        print(msg)
        return 0 if ok else 1

    dur_mode = "standard"
    if "--quick" in argv:
        dur_mode = "quick"
    elif "--sustained" in argv or "--10min" in argv:
        dur_mode = "sustained"
    elif "--full" in argv or "--30min" in argv:
        dur_mode = "full"
    elif "--standard" in argv or "--5min" in argv:
        dur_mode = "standard"
    else:
        for arg in argv:
            if arg.startswith("--duration="):
                val = arg.split("=", 1)[1].strip().lower()
                if val in BenchmarkEngine.DURATION_MODES:
                    dur_mode = val

    is_json = "--json" in argv
    use_sample = "--sample" in argv or "--sample-audio" in argv

    custom_file_arg = None
    if "--file" in argv:
        try:
            idx = argv.index("--file")
            custom_file_arg = argv[idx + 1]
        except (ValueError, IndexError):
            pass

    if "--gui" in argv:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        dlg = create_benchmark_dialog()
        dlg.exec()
        return 0
    else:
        return run_cli_benchmark(duration_mode=dur_mode, as_json=is_json, use_sample=use_sample, custom_file=custom_file_arg)


if __name__ == "__main__":
    raise SystemExit(main())

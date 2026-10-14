"""Helper fixtures, module resolvers, and DiagnosticItem for test runner."""
from __future__ import annotations

import io
import math
import os
import struct
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Synthetic Audio Generator (Zero-Dependency in-memory / wave file fixture)
# ---------------------------------------------------------------------------

def generate_synthetic_wav(
    duration_seconds: float = 3.0,
    sample_rate: int = 16000,
    frequencies: Optional[List[float]] = None,
    output_path: Optional[str] = None,
) -> Tuple[bytes, str]:
    """Generates a multi-frequency synthetic 16kHz mono WAV file in memory or on disk.

    Creates realistic acoustic waves with quiet pauses without external audio files.
    """
    if frequencies is None:
        frequencies = [440.0, 880.0]  # A4 and A5 dual tone

    num_samples = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)

        # Generate audio samples: sound burst then silence pause then sound
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Create a 0.5s pause in the middle to simulate speech pauses
            if 1.0 <= t <= 1.5:
                sample_val = 0
            else:
                # Combined sine waves with envelope ramp to prevent clicks
                combined = sum(math.sin(2.0 * math.pi * f * t) for f in frequencies) / len(frequencies)
                # Soft fade envelope
                amplitude = 0.7 * 32767.0
                sample_val = int(combined * amplitude)
                sample_val = max(-32768, min(32767, sample_val))
            frames.extend(struct.pack("<h", sample_val))

        wav_file.writeframes(frames)

    wav_bytes = buffer.getvalue()
    path_written = ""
    if output_path:
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        path_written = str(Path(output_path).resolve())

    return wav_bytes, path_written



class DiagnosticItem:
    """Represents the execution outcome of an individual test or diagnostic probe."""

    def __init__(self, name: str, category: str, description: str, dev_only: bool = False):
        self.name = name
        self.category = category
        self.description = description
        self.dev_only = dev_only
        self.status: str = "PENDING"  # PENDING, RUNNING, PASS, FAIL, SKIP, WARNING
        self.message: str = ""
        self.duration_sec: float = 0.0
        self.details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "dev_only": self.dev_only,
            "status": self.status,
            "message": self.message,
            "duration_sec": round(self.duration_sec, 3),
            "details": self.details,
        }




def _resolve_export_subtitles_module():
    """Resolves export.subtitles whether running from source, package, or frozen binary."""
    try:
        import export.subtitles as mod
        return mod
    except ImportError:
        pass
    import importlib.util
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "export", "subtitles.py"),
        os.path.join(os.getcwd(), "export", "subtitles.py"),
        os.path.join(getattr(sys, "_MEIPASS", ""), "export", "subtitles.py"),
        os.path.join(base_dir, "_internal", "export", "subtitles.py"),
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            spec = importlib.util.spec_from_file_location("export_subtitles", cand)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
    raise ImportError("Could not locate or import export.subtitles module")


def _resolve_export_daw_module():
    """Resolves export.daw whether running from source, package, or frozen binary."""
    try:
        import export.daw as mod
        return mod
    except ImportError:
        pass
    import importlib.util
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "export", "daw.py"),
        os.path.join(os.getcwd(), "export", "daw.py"),
        os.path.join(getattr(sys, "_MEIPASS", ""), "export", "daw.py"),
        os.path.join(base_dir, "_internal", "export", "daw.py"),
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            spec = importlib.util.spec_from_file_location("export_daw", cand)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
    raise ImportError("Could not locate or import export.daw module")



__all__ = [
    "generate_synthetic_wav",
    "DiagnosticItem",
    "_resolve_export_subtitles_module",
    "_resolve_export_daw_module",
]

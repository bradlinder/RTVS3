"""Radio & TV Segmenter — Model Download and Installation Background Workers.

Extracted background worker classes for AI speech models and speaker diarization weights.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtCore import QObject, Signal
except ImportError:
    class QObject:
        def __init__(self, parent=None):
            pass

    class DummySignal:
        def __init__(self, *args, **kwargs):
            pass
        def emit(self, *args, **kwargs):
            pass
        def connect(self, *args, **kwargs):
            pass

    def Signal(*args, **kwargs):
        return DummySignal()

from core_utils import get_models_storage_dir

logger = logging.getLogger(__name__)


def get_diarization_model_dir() -> Path:
    """Return canonical directory for WeSpeaker ONNX diarization models."""
    return get_models_storage_dir() / "wespeaker"


def is_diarization_model_available() -> bool:
    """Check if a valid WeSpeaker ONNX model is present in candidate directories."""
    candidates = [
        get_models_storage_dir() / "wespeaker",
        Path.home() / ".wespeaker",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            for f in candidate.rglob("*.onnx"):
                if f.is_file() and f.stat().st_size > 1024:
                    return True
            for f in candidate.rglob("*.bin"):
                if f.is_file() and f.stat().st_size > 1024:
                    return True
    return False


class WhisperModelInstallWorker(QObject):
    """Background worker for downloading Whisper, Parakeet, and FastConformer models."""

    progress = Signal(int, str)
    finished = Signal(object)

    def __init__(self, model_name: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model_name = str(model_name)
        self._cancelled = False

    def cancel(self):
        """Request cancellation of active download."""
        self._cancelled = True

    def run(self):
        """Execute download in background thread."""
        error = None
        try:
            model_name = self.model_name
            self.progress.emit(5, f"Preparing download for '{model_name}'...")
            if self._cancelled:
                self.finished.emit("Download cancelled")
                return

            if model_name.startswith("parakeet"):
                target_dir = get_models_storage_dir() / "parakeet_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
                files = ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]
                for idx, fname in enumerate(files):
                    if self._cancelled:
                        raise RuntimeError("Download cancelled by user")
                    pct = int(10 + (idx / len(files)) * 85)
                    self.progress.emit(pct, f"Downloading {fname}...")
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))

            elif model_name == "fastconformer-es-onnx":
                target_dir = get_models_storage_dir() / "fastconformer_es_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-fast-conformer-ctc-es-1424-int8"
                files = ["model.int8.onnx", "tokens.txt"]
                for idx, fname in enumerate(files):
                    if self._cancelled:
                        raise RuntimeError("Download cancelled by user")
                    pct = int(10 + (idx / len(files)) * 85)
                    self.progress.emit(pct, f"Downloading {fname}...")
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))

            elif model_name == "fastconformer-multilingual-onnx":
                target_dir = get_models_storage_dir() / "fastconformer_multilingual_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-fast-conformer-ctc-be-de-en-es-fr-hr-it-pl-ru-uk-20k"
                files = ["model.onnx", "tokens.txt"]
                for idx, fname in enumerate(files):
                    if self._cancelled:
                        raise RuntimeError("Download cancelled by user")
                    pct = int(10 + (idx / len(files)) * 85)
                    self.progress.emit(pct, f"Downloading {fname}...")
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))

            else:
                if "/" in model_name:
                    resolved = model_name
                else:
                    resolved = f"Systran/faster-whisper-{model_name}"

                cache_dir = str(get_models_storage_dir() / "huggingface" / "hub")
                Path(cache_dir).mkdir(parents=True, exist_ok=True)
                self.progress.emit(25, f"Downloading Hugging Face repository '{resolved}'...")
                from huggingface_hub import snapshot_download
                snapshot_download(repo_id=resolved, cache_dir=cache_dir)

            if self._cancelled:
                raise RuntimeError("Download cancelled by user")

            self.progress.emit(100, f"Model '{model_name}' download complete.")
        except Exception as exc:
            error = str(exc)

        self.finished.emit(error)


class DiarizationModelInstallWorker(QObject):
    """Background worker for downloading WeSpeaker ResNet34/CAM++ ONNX diarization models."""

    progress = Signal(int, str)
    finished = Signal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._cancelled = False

    def cancel(self):
        """Request cancellation of active download."""
        self._cancelled = True

    def run(self):
        """Execute download in background thread."""
        error = None
        try:
            self.progress.emit(10, "Preparing download for WeSpeaker diarization model...")
            if self._cancelled:
                self.finished.emit("Download cancelled")
                return

            target_dir = get_diarization_model_dir()
            target_dir.mkdir(parents=True, exist_ok=True)

            self.progress.emit(30, "Downloading WeSpeaker ResNet34 ONNX embedding model...")
            from huggingface_hub import hf_hub_download

            repo_id = "csukuangfj/sherpa-onnx-wespeaker-cam++-en-voxceleb-CAM++-onnx"
            try:
                hf_hub_download(
                    repo_id=repo_id,
                    filename="wespeaker_en_voxceleb_CAM++.onnx",
                    local_dir=str(target_dir),
                )
            except Exception:
                pass

            if self._cancelled:
                raise RuntimeError("Download cancelled by user")

            self.progress.emit(100, "Diarization model download complete.")
        except Exception as exc:
            error = str(exc)

        self.finished.emit(error)

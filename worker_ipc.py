"""worker_ipc.py - Subprocess IPC protocol, environment setup, and DLL initialization.

Provides:
- emit: JSON IPC message emitter to stdout
- emit_hello: Protocol handshake emitter
- _patch_av_open: PyAV 13+ compatibility patch
- _clamp_diarization_thread_env: OMP/BLAS/ONNX thread count environment limiter
- _setup_windows_dll_directories: Windows C-extension DLL path registry
- _safe_tensor_from_numpy: Resilient NumPy-to-PyTorch tensor converter
"""

import os
import sys
import json
from pathlib import Path

# Multiprocessing protocol constants
PROTOCOL_VERSION = "1.0"
CAPABILITIES = ["transcribe", "diarize"]

_GLOBAL_WORKER_DLL_HANDLES = []


def emit(message_type: str, **payload):
    """Serialize and send structured JSON message to parent process over stdout."""
    message = {"type": message_type, **payload}
    sys.stdout.buffer.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def emit_hello():
    """Emit startup handshake message identifying protocol version and worker capabilities."""
    emit("hello", protocol=PROTOCOL_VERSION, capabilities=CAPABILITIES)


def _patch_av_open():
    """Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed.
    PyAV >= 13 removed the 'metadata_errors' parameter from av.open(), causing
    faster-whisper's decode_audio to fail with:
    TypeError: open() got an unexpected keyword argument 'metadata_errors'.
    """
    try:
        import av
        if hasattr(av, "open") and not getattr(av.open, "_is_patched", False):
            orig_open = av.open

            def patched_open(*args, **kwargs):
                kwargs.pop("metadata_errors", None)
                return orig_open(*args, **kwargs)

            patched_open._is_patched = True
            av.open = patched_open
    except Exception:
        pass


def _clamp_diarization_thread_env():
    """Cap OMP/ONNX Runtime/BLAS thread pools before onnxruntime, torch, or the
    diarize package are ever imported anywhere in this process.
    """
    try:
        import psutil
        physical = psutil.cpu_count(logical=False) or 0
    except Exception:
        physical = 0
    if not physical:
        cpu_count = os.cpu_count() or 4
        physical = cpu_count // 2 if cpu_count > 2 else cpu_count
    capped = max(1, min(int(physical), 8))
    for var in (
        "OMP_NUM_THREADS",
        "ORT_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ.setdefault(var, str(capped))

    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def _setup_windows_dll_directories():
    """Register native DLL directories (PyTorch, CTranslate2, ONNX Runtime, etc.)
    on Windows before importing C-extensions or ML frameworks.
    """
    if sys.platform != "win32":
        return

    candidate_dirs = set()

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            meipass_path = Path(meipass)
            candidate_dirs.add(meipass_path)
            candidate_dirs.add(meipass_path / "torch" / "lib")
            candidate_dirs.add(meipass_path / "torch")
            candidate_dirs.add(meipass_path / "torchaudio" / "lib")
            candidate_dirs.add(meipass_path / "ctranslate2")
            candidate_dirs.add(meipass_path / "onnxruntime" / "capi")
            candidate_dirs.add(meipass_path / "sherpa_onnx" / "lib")
            candidate_dirs.add(meipass_path / "sherpa_onnx")

        exe_dir = Path(sys.executable).parent
        candidate_dirs.add(exe_dir)
        candidate_dirs.add(exe_dir / "_internal")
        candidate_dirs.add(exe_dir / "_internal" / "torch" / "lib")
        candidate_dirs.add(exe_dir / "_internal" / "torch")
        candidate_dirs.add(exe_dir / "_internal" / "torchaudio" / "lib")
        candidate_dirs.add(exe_dir / "_internal" / "ctranslate2")
        candidate_dirs.add(exe_dir / "_internal" / "onnxruntime" / "capi")
        candidate_dirs.add(exe_dir / "_internal" / "sherpa_onnx" / "lib")
        candidate_dirs.add(exe_dir / "torch" / "lib")
        candidate_dirs.add(exe_dir / "torch")

    # Add NumPy, SciPy, Scikit-Learn, and WeSpeaker runtime folders
    for base in list(candidate_dirs):
        candidate_dirs.add(base / "numpy")
        candidate_dirs.add(base / "numpy" / "core")
        candidate_dirs.add(base / "numpy" / "_core")
        candidate_dirs.add(base / "scipy")
        candidate_dirs.add(base / "sklearn")
        candidate_dirs.add(base / "wespeakerruntime")
        try:
            if base.is_dir():
                for lib_dir in base.glob("*.libs"):
                    if lib_dir.is_dir():
                        candidate_dirs.add(lib_dir)
                for lib_dir in base.glob("*/*.libs"):
                    if lib_dir.is_dir():
                        candidate_dirs.add(lib_dir)
        except Exception:
            pass

    for entry in list(sys.path):
        if not entry:
            continue
        try:
            p = Path(entry)
            if not p.is_dir():
                continue
            candidate_dirs.add(p)
            candidate_dirs.add(p / "torch" / "lib")
            candidate_dirs.add(p / "torch")
            candidate_dirs.add(p / "torchaudio" / "lib")
            candidate_dirs.add(p / "ctranslate2")
            candidate_dirs.add(p / "onnxruntime" / "capi")
            candidate_dirs.add(p / "sherpa_onnx" / "lib")
            candidate_dirs.add(p / "sherpa_onnx")
        except Exception:
            continue

    try:
        prefix = Path(sys.prefix)
        candidate_dirs.add(prefix / "bin")
        candidate_dirs.add(prefix / "Library" / "bin")
        candidate_dirs.add(prefix / "Lib" / "site-packages" / "torch" / "lib")
        candidate_dirs.add(prefix / "Lib" / "site-packages" / "torchaudio" / "lib")
        candidate_dirs.add(prefix / "Lib" / "site-packages" / "ctranslate2")
        candidate_dirs.add(prefix / "Lib" / "site-packages" / "onnxruntime" / "capi")
    except Exception:
        pass

    try:
        import importlib.util
        spec = importlib.util.find_spec("torch")
        if spec and spec.origin:
            torch_root = Path(spec.origin).parent
            candidate_dirs.add(torch_root / "lib")
            candidate_dirs.add(torch_root)
    except Exception:
        pass

    added_paths = []
    for d in candidate_dirs:
        try:
            resolved = d.resolve()
            if resolved.is_dir():
                str_path = str(resolved)
                if hasattr(os, "add_dll_directory"):
                    try:
                        handle = os.add_dll_directory(str_path)
                        _GLOBAL_WORKER_DLL_HANDLES.append(handle)
                    except Exception:
                        pass
                added_paths.append(str_path)
        except Exception:
            continue

    if added_paths:
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(added_paths) + os.pathsep + current_path


def _safe_tensor_from_numpy(arr):
    """Safely convert a numpy float32 array into a PyTorch tensor.
    Works even if PyTorch's native C-extension numpy bridge fails to locate
    the NumPy C-API symbols ('numpy.core._multiarray_umath') or if the array is read-only.
    """
    import torch
    import numpy as np
    try:
        if isinstance(arr, np.ndarray):
            if not arr.flags.writeable or not arr.flags.c_contiguous:
                arr = np.ascontiguousarray(arr, dtype=np.float32).copy()
        return torch.from_numpy(arr)
    except (RuntimeError, UserWarning, AttributeError, Exception):
        pass
    try:
        return torch.as_tensor(arr, dtype=torch.float32)
    except (RuntimeError, UserWarning, AttributeError, Exception):
        pass
    return torch.tensor(arr.tolist(), dtype=torch.float32)

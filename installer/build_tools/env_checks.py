"""Environment validation, external tool resolution, and subprocess execution helpers."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def exe_name(base: str) -> str:
    """Return platform-appropriate executable filename."""
    return base + (".exe" if os.name == "nt" else "")


def find_tool(name: str, root_dir: Path = _DEFAULT_ROOT) -> str:
    """Locate required media runtime tools such as ffmpeg or ffprobe."""
    env_dir = os.environ.get("PRS_FFMPEG_DIR")
    target_exe = exe_name(name)
    candidates = []

    if env_dir:
        candidates.append(Path(env_dir) / target_exe)
        candidates.append(Path(env_dir) / "bin" / target_exe)

    found = shutil.which(name)
    if found:
        candidates.append(Path(found))

    candidates.extend([
        root_dir / "bin" / target_exe,
        root_dir / "runtime" / "bin" / target_exe,
        root_dir / "ffmpeg" / "bin" / target_exe,
        root_dir / "ffmpeg" / target_exe,
    ])

    if sys.platform == "win32":
        win_candidates = [
            Path("C:/ffmpeg/bin") / target_exe,
            Path("C:/ffmpeg") / target_exe,
            Path("C:/Program Files/ffmpeg/bin") / target_exe,
            Path("C:/Program Files/ffmpeg") / target_exe,
            Path("C:/Program Files (x86)/ffmpeg/bin") / target_exe,
            Path(os.environ.get("LOCALAPPDATA", "C:/")) / "Microsoft/WinGet/Links" / target_exe,
            Path(os.environ.get("ProgramData", "C:/")) / "chocolatey/bin" / target_exe,
            Path.home() / "scoop/shims" / target_exe,
        ]
        candidates.extend(win_candidates)
    else:
        candidates.extend([
            Path("/usr/bin") / target_exe,
            Path("/usr/local/bin") / target_exe,
            Path("/opt/homebrew/bin") / target_exe,
            Path("/snap/bin") / target_exe,
            Path.home() / ".local/bin" / target_exe,
        ])

    for candidate in candidates:
        if candidate.is_file():
            resolved = str(candidate.resolve())
            print(f"[BUILD] Found {name}: {resolved}")
            return resolved

    if sys.stdin.isatty():
        print(f"\n[BUILD] {name} was not found automatically in PATH or standard folders.")
        user_input = input(f"Please enter the directory containing {name} (or leave empty to exit): ").strip()
        if user_input:
            user_path = Path(user_input).expanduser()
            if (user_path / target_exe).is_file():
                return str((user_path / target_exe).resolve())
            if user_path.is_file() and user_path.name.lower().startswith(name):
                return str(user_path.resolve())

    raise SystemExit(
        f"\n[ERROR] '{name}' was not found.\n"
        "To fix this, you can:\n"
        f"  1. Place {exe_name('ffmpeg')} and {exe_name('ffprobe')} in the project's 'bin/' folder: {root_dir / 'bin'}\n"
        "  2. Or set the PRS_FFMPEG_DIR environment variable to the folder containing them.\n"
        "  3. Or install FFmpeg and add it to your system PATH.\n"
    )


def check_cpu_only_torch() -> None:
    """Verify the build environment uses CPU-only PyTorch unless explicitly bypassed."""
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, "-c", "import torch; print(torch.version.cuda or '')"],
            capture_output=True, text=True, check=True,
            creationflags=creationflags,
        )
        cuda_version = result.stdout.strip()
    except Exception as exc:
        raise SystemExit(
            "[FATAL BUILD ERROR] PyTorch cannot be imported in the build environment: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if cuda_version:
        msg = (
            f"[BUILD] WARNING: torch installed in this build environment reports CUDA {cuda_version}.\n"
            "This build is intended to be CPU-only and small (<500MB). Installing CUDA packages will\n"
            "balloon the installer to >2GB and fail release asset limits.\n\n"
            "More importantly: prune_unneeded_bundled_files() below deletes cuDNN/cuBLAS/nvRTC/NCCL\n"
            "files by name to keep a CPU build small, but it does NOT remove torch_cuda.dll/c10_cuda.dll\n"
            "themselves. Building from a CUDA-enabled torch therefore does not just produce an oversized\n"
            "installer -- it produces one where torch's C extension (torch._C) fails to load at all,\n"
            "because the CUDA DLLs it still depends on have been stripped out. This has shipped broken\n"
            "builds before (NameError: name '_C' is not defined, breaking Speaker Detection and\n"
            "Translation, which both import torch) -- so this now always aborts the build rather than\n"
            "just warning.\n\n"
            "To fix, install CPU-only torch before building:\n"
            "  pip install 'torch>=2.0,<2.4' 'torchaudio>=2.0,<2.4' --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install -r installer/requirements.txt -r requirements-build.txt --extra-index-url https://download.pytorch.org/whl/cpu\n\n"
            "If you specifically need a CUDA build for local testing and understand the above risk,\n"
            "set PRS_ALLOW_CUDA_BUILD=1 to bypass this check."
        )
        if os.environ.get("PRS_ALLOW_CUDA_BUILD"):
            print(msg)
            print("[BUILD] PRS_ALLOW_CUDA_BUILD is set -- continuing with CUDA torch despite the risk above.")
            return
        raise SystemExit(f"\n[FATAL BUILD ERROR]\n{msg}")
    else:
        print("[BUILD] torch in the build environment is CPU-only. Good.")


def torch_windows_binary_flags() -> list[str]:
    """Collect explicit Windows PyTorch DLL binary flags for PyInstaller."""
    if sys.platform != "win32":
        return []
    try:
        spec = importlib.util.find_spec("torch")
        if not spec or not spec.origin:
            raise RuntimeError("could not locate the build environment's torch package")
        torch_root = Path(spec.origin).resolve().parent
        lib_dir = torch_root / "lib"
    except Exception as exc:
        raise SystemExit(f"[FATAL BUILD ERROR] Could not locate torch/lib for PyInstaller: {exc}") from exc
    if not lib_dir.is_dir():
        raise SystemExit(f"[FATAL BUILD ERROR] Expected PyTorch native library directory was not found: {lib_dir}")

    flags: list[str] = ["--paths", str(lib_dir)]
    dlls = sorted(lib_dir.glob("*.dll"))
    required = {"c10.dll", "torch_cpu.dll", "torch_python.dll"}
    present = {p.name.lower() for p in dlls}
    missing = sorted(name for name in required if name.lower() not in present)
    if missing:
        raise SystemExit(
            "[FATAL BUILD ERROR] The CPU PyTorch wheel is missing required native DLLs in "
            f"{lib_dir}: {', '.join(missing)}"
        )
    for dll in dlls:
        flags += ["--add-binary", f"{dll}{os.pathsep}torch/lib"]
    print(f"[BUILD] Explicitly packaging {len(dlls)} PyTorch native DLLs from {lib_dir}")
    return flags


def run(cmd: list[str], cwd: Path = _DEFAULT_ROOT) -> None:
    """Execute a build subprocess streaming output line-by-line."""
    timestamp = time.strftime("%H:%M:%S")
    cmd_str = " ".join(map(str, cmd))
    print(f"\n[BUILD {timestamp}] Executing: {cmd_str}", flush=True)
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # Stream output in real-time line-by-line so CI logs never stall or buffer
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        creationflags=creationflags,
    )
    if process.stdout:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line, end="", flush=True)
    ret = process.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd)

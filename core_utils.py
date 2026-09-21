"""Radio & TV Segmenter — Core filesystem, path, timing, and hash utilities.

Standalone utilities for file hashing, safe archive extraction, atomic replacement,
time string formatting/parsing, and runtime path discovery.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import sys
import time
from pathlib import Path

try:
    from PySide6.QtCore import QSettings
except ImportError:
    QSettings = None

INTERNAL_APP_ID = "RadioTVStorySegmenter"
APP_DISPLAY_NAME = "Radio & TV Segmenter"
PROJECT_VERSION = "3.5.19"
DEFAULT_GITHUB_REPO = "bradlinder/RTVS3"


def _ensure_runtime_bin_on_path():
    """Ensure bundled runtime/bin (ffmpeg/ffprobe) is on PATH in frozen builds."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    candidates = [
        exe_dir / "runtime" / "bin",
        exe_dir.parent / "runtime" / "bin",
        exe_dir / "bin",
        exe_dir.parent / "bin",
    ]
    for c in candidates:
        if c.is_dir():
            str_path = str(c.resolve())
            current_path = os.environ.get("PATH", "")
            if str_path not in current_path:
                os.environ["PATH"] = str_path + os.pathsep + current_path
            break


_ensure_runtime_bin_on_path()


def compute_file_sha256(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 hexadecimal digest of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file_sha256(file_path: str | Path, expected_sha256: str) -> bool:
    """Verify that a file matches the expected SHA-256 checksum (case-insensitive)."""
    if not expected_sha256:
        return True
    try:
        actual = compute_file_sha256(file_path)
        return actual.lower() == expected_sha256.strip().lower()
    except Exception:
        return False


def safe_extract_zip(zip_source, dest_dir) -> None:
    """Safely extracts a ZIP archive to a destination directory, guarding against path traversal (Zip Slip)."""
    import zipfile
    dest_path = Path(dest_dir).resolve()
    
    def _verify_and_extract(zf):
        for member in zf.infolist():
            normalized = Path(os.path.abspath(os.path.join(dest_path, member.filename)))
            try:
                normalized.relative_to(dest_path)
            except ValueError:
                raise PermissionError(f"Attempted path traversal in ZIP member: {member.filename}")
        zf.extractall(dest_path)

    if isinstance(zip_source, (str, Path)):
        with zipfile.ZipFile(zip_source, "r") as z:
            _verify_and_extract(z)
    else:
        _verify_and_extract(zip_source)


def safe_extract_tar(tar_source, dest_dir) -> None:
    """Safely extracts a TAR archive to a destination directory, guarding against path traversal."""
    import tarfile
    dest_path = Path(dest_dir).resolve()

    def _verify_and_extract(tf):
        for member in tf.getmembers():
            normalized = Path(os.path.abspath(os.path.join(dest_path, member.name)))
            try:
                normalized.relative_to(dest_path)
            except ValueError:
                raise PermissionError(f"Attempted path traversal in TAR member: {member.name}")
        tf.extractall(dest_path)

    if isinstance(tar_source, (str, Path)):
        with tarfile.open(tar_source, "r:*") as t:
            _verify_and_extract(t)
    else:
        _verify_and_extract(tar_source)


def safe_replace(src: str | Path, dest: str | Path) -> None:
    """Safely and atomically replace dest with src, handling file locks, permissions,
    and network share anomalies (e.g., WinError 5 PermissionError) with retry loops
    and a final robust write-copy stream fallback.
    """
    src_path = Path(src).resolve()
    dest_path = Path(dest).resolve()
    for i in range(5):
        try:
            os.replace(src_path, dest_path)
            return
        except PermissionError as e:
            if i < 4:
                time.sleep(0.05 * (2 ** i))  # exponential backoff (0.05s, 0.1s, 0.2s, 0.4s)
                continue
            else:
                # If atomic replace still fails, attempt copy-and-unlink fallback.
                # Writing directly to the existing destination handle/path bypasses 
                # rename lock constraints common on Windows SMB/UNC network shares.
                try:
                    shutil.copyfile(src_path, dest_path)
                    try:
                        os.unlink(src_path)
                    except Exception:
                        pass
                    return
                except Exception:
                    raise e
        except Exception:
            try:
                os.replace(src_path, dest_path)
                return
            except Exception:
                shutil.copyfile(src_path, dest_path)
                try:
                    os.unlink(src_path)
                except Exception:
                    pass
                return


def get_github_repo() -> str:
    """Return the configured GitHub repository owner/repo string."""
    env_repo = os.environ.get("GITHUB_REPO", "").strip()
    if env_repo:
        return env_repo
    try:
        if QSettings is not None:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            val = str(settings.value("github_repo", "") or "").strip()
            if val:
                # Transparently migrate legacy repository references to RTVS3
                if val.lower() in ("bradlinder/rtvs", "bradlinder/radiotvstorysegmenter", "radiotvstorysegmenter"):
                    settings.setValue("github_repo", DEFAULT_GITHUB_REPO)
                    return DEFAULT_GITHUB_REPO
                return val
    except Exception:
        pass
    return DEFAULT_GITHUB_REPO


def get_update_channel() -> str:
    """Return the configured software update release channel: 'stable' or 'beta'."""
    env_chan = os.environ.get("RTVS_UPDATE_CHANNEL", "").strip().lower()
    if env_chan in ("beta", "prerelease", "all"):
        return "beta"
    if env_chan == "stable":
        return "stable"
    try:
        if QSettings is not None:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            val = str(settings.value("update_channel", "stable") or "stable").strip().lower()
            if val in ("beta", "prerelease", "all"):
                return "beta"
    except Exception:
        pass
    return "stable"


def get_app_data_dir() -> Path:
    """Return the per-user writable application-data directory.

    Installed applications must not write mutable data beside the executable
    (for example, Program Files on Windows).
    """
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / INTERNAL_APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_models_storage_dir() -> Path:
    """Return the directory configured for storing downloaded models.
    Defaults to get_app_data_dir() / 'models' if not customized in settings."""
    if QSettings is not None:
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            custom = settings.value("models_dir", "")
            if custom and isinstance(custom, str) and custom.strip():
                p = Path(custom.strip())
                try:
                    p.mkdir(parents=True, exist_ok=True)
                    return p
                except Exception:
                    pass
        except Exception:
            pass
    default_path = get_app_data_dir() / "models"
    default_path.mkdir(parents=True, exist_ok=True)
    return default_path


def set_models_storage_dir(new_path=None) -> Path:
    """Set and persist a custom models storage directory."""
    if QSettings is not None:
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            if not new_path or not str(new_path).strip():
                settings.remove("models_dir")
                target = get_app_data_dir() / "models"
            else:
                p = Path(str(new_path).strip())
                p.mkdir(parents=True, exist_ok=True)
                settings.setValue("models_dir", str(p.resolve()))
                target = p
            hf_dir = target / "huggingface"
            hf_dir.mkdir(parents=True, exist_ok=True)
            os.environ["HF_HOME"] = str(hf_dir.resolve())
            return target
        except Exception:
            pass
    target = Path(str(new_path).strip()) if new_path and str(new_path).strip() else get_app_data_dir() / "models"
    target.mkdir(parents=True, exist_ok=True)
    return target


def get_bundled_runtime_dir() -> Path:
    """Locate the installed/bundled runtime resource directory."""
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "runtime")
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "runtime")
    candidates.append(Path(__file__).resolve().parent / "runtime")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def find_bundled_executable(name: str) -> str | None:
    """Find a bundled executable first, then fall back to PATH and common macOS locations."""
    filename = name + (".exe" if os.name == "nt" and not name.lower().endswith(".exe") else "")
    for root in (get_bundled_runtime_dir() / "bin", get_bundled_runtime_dir()):
        candidate = root / filename
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    if sys.platform == "darwin":
        for mac_bin in (
            Path("/opt/homebrew/bin") / name,
            Path("/opt/homebrew/sbin") / name,
            Path("/usr/local/bin") / name,
            Path("/usr/local/sbin") / name,
            Path("/opt/local/bin") / name,
            Path.home() / ".local" / "bin" / name,
            Path.home() / ".cargo" / "bin" / name,
        ):
            if mac_bin.is_file():
                return str(mac_bin)
    return None


def ffmpeg_path() -> str | None:
    return find_bundled_executable("ffmpeg")


def ffprobe_path() -> str | None:
    return find_bundled_executable("ffprobe")


def format_time(seconds, include_millis=True):
    seconds = max(0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    if include_millis:
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"
    else:
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


def parse_time(value):
    value = str(value).strip()
    try:
        return float(value)
    except ValueError:
        pass

    parts = value.split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return (
            float(parts[0]) * 3600
            + float(parts[1]) * 60
            + float(parts[2])
        )
    raise ValueError(f"Invalid time: {value}")


def safe_filename(text):
    text = str(text or "").strip()
    if not text:
        text = "Untitled Story"
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    text = re.sub(r"\s+", "_", text)
    text = text[:100]
    # A result that's nothing but dots (".", "..", "....") is a
    # current-dir/parent-dir path component when used as a single path
    # segment, not a real filename -- e.g. a project folder-name prompt or
    # a story title of ".." would otherwise resolve one level *above* the
    # intended export directory. This can come from direct user input or
    # from a loaded project file's own data, so guard it once here rather
    # than at each of this function's call sites.
    if not text.strip("."):
        text = "Untitled_Story"
    return text


def is_sentence_end(text):
    return bool(re.search(r"[.!?]+[\"'”’)\]]*$", str(text or "").strip()))


def calculate_fade_curve_factor(u: float, fcurve: str = "linear") -> float:
    """Calculate normalized fade-in multiplier (0.0 to 1.0) given progress `u` in [0, 1]."""
    u = max(0.0, min(1.0, float(u)))
    fcurve = str(fcurve).lower()
    if fcurve == "s_curve":
        return float(0.5 * (1.0 - math.cos(math.pi * u)))
    elif fcurve == "logarithmic":
        return float(math.log10(1.0 + 9.0 * u))
    elif fcurve == "exponential":
        return float((math.pow(10.0, u) - 1.0) / 9.0)
    else:  # "linear"
        return u


def calculate_fade_out_factor(u: float, fcurve: str = "linear") -> float:
    """Calculate normalized fade-out multiplier (1.0 to 0.0) given progress `u` from 0.0 (fade start) to 1.0 (silence).

    Accurately maps the visual preview cues to the applied fade-out:
    - Logarithmic (⌒): Gentle initial volume roll-off, steepening near the end (convex / domed).
    - Exponential (◞): Rapid initial volume attenuation, followed by a gentle tail to silence (concave / scooped).
    - S-Curve (∿): Smooth cosine ease-in and ease-out transition.
    - Linear (╱): Constant-rate linear attenuation (1.0 - u).
    """
    u = max(0.0, min(1.0, float(u)))
    fcurve = str(fcurve).lower()
    if fcurve == "s_curve":
        return float(0.5 * (1.0 + math.cos(math.pi * u)))
    elif fcurve == "logarithmic":
        # Matches Logarithmic preview (⌒): stays high initially before dropping at end
        return float(max(0.0, min(1.0, 1.0 - (math.pow(10.0, u) - 1.0) / 9.0)))
    elif fcurve == "exponential":
        # Matches Exponential preview (◞): drops fast initially then gently glides to silence
        return float(max(0.0, min(1.0, 1.0 - math.log10(1.0 + 9.0 * u))))
    else:
        return float(1.0 - u)


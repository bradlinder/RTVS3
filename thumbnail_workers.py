"""Video thumbnail cache helpers, network-share detection, and background thumbnail workers.

Extracted from background_workers.py to keep worker modules cohesive and under the
line budget while providing:
- is_network_path: Detect UNC shares and mapped network drives so derived caches stay local.
- Timeline thumbnail density presets and duration-scaled target counts.
- Single-pass os.scandir() thumbnail cache reading and invalidation.
- VideoThumbnailWorker: Keyframe-accelerated FFmpeg extraction with live % progress and lock-safe cancel.
- VideoThumbnailCacheLoader: Background QImage decoding so cached strips never freeze the UI thread.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

from core_utils import ffmpeg_path, get_app_data_dir
from process_lifecycle import register_process, unregister_process


TIMELINE_THUMBNAIL_DENSITY_SPECS = {
    "standard": {"per_min": 2, "min_count": 16, "max_count": 180},
    "detailed": {"per_min": 4, "min_count": 24, "max_count": 300},
    "high": {"per_min": 8, "min_count": 36, "max_count": 480},
    "extra_high": {"per_min": 16, "min_count": 48, "max_count": 960},
}
TIMELINE_THUMBNAIL_DENSITY_PRESETS = {
    k: spec["per_min"] for k, spec in TIMELINE_THUMBNAIL_DENSITY_SPECS.items()
}
DEFAULT_TIMELINE_THUMBNAIL_DENSITY = "standard"
MAX_TIMELINE_THUMBNAIL_COUNT = 960
_LEGACY_DEFAULT_THUMBNAIL_COUNT = 36

_DRIVE_REMOTE = 4
_OUT_TIME_RE = re.compile(r"^(\d+):(\d+):(\d+(?:\.\d+)?)$")


def is_network_path(path: str | Path | None) -> bool:
    """Return True if *path* points to a UNC network share or Windows mapped network drive.

    Derived caches (hundreds of tiny JPEG thumbnails and peak envelopes) should stay on
    local SSD storage rather than incurring hundreds of SMB round-trips on project open.
    """
    if not path:
        return False
    raw = str(path).strip()
    if not raw:
        return False
    if raw.startswith("\\\\") or raw.startswith("//"):
        return True
    if sys.platform == "win32":
        try:
            drive, _ = os.path.splitdrive(os.path.abspath(raw))
            if drive.startswith("\\\\") or drive.startswith("//"):
                return True
            if len(drive) == 2 and drive[1] == ":":
                import ctypes
                drive_root = drive + "\\"
                dtype = ctypes.windll.kernel32.GetDriveTypeW(drive_root)
                if dtype == _DRIVE_REMOTE:
                    return True
        except Exception:
            pass
    return False


def normalize_thumbnail_density(density) -> str:
    """Normalize a timeline thumbnail density setting to 'standard', 'detailed', 'high', or 'extra_high'."""
    key = str(density or DEFAULT_TIMELINE_THUMBNAIL_DENSITY).strip().lower()
    return key if key in TIMELINE_THUMBNAIL_DENSITY_SPECS else DEFAULT_TIMELINE_THUMBNAIL_DENSITY


def get_thumbnail_count_for_density(density, duration: float | None = None) -> int:
    """Return the duration-scaled, memory-bounded thumbnail count for a density preset."""
    spec = TIMELINE_THUMBNAIL_DENSITY_SPECS[normalize_thumbnail_density(density)]
    dur_sec = float(duration) if (duration is not None and float(duration) > 0) else 1800.0
    raw = int(round((dur_sec / 60.0) * spec["per_min"]))
    return max(spec["min_count"], min(spec["max_count"], raw))


def should_use_keyframe_skip(
    duration: float,
    count: int,
    density: Optional[str] = None,
) -> bool:
    """Return True when FFmpeg `-skip_frame nokey` can safely accelerate thumbnail extraction.

    Enabled for coarse/medium presets (standard = 2/min, detailed = 4/min) or whenever the
    average thumbnail spacing is >= 10 seconds (well above typical 2-5s GOP keyframe intervals).
    """
    if density is not None:
        norm = normalize_thumbnail_density(density)
        if norm in ("standard", "detailed"):
            return True
        if norm in ("high", "extra_high"):
            return False
    dur = max(0.0, float(duration or 0.0))
    cnt = max(1, int(count or 1))
    return (dur / cnt) >= 10.0


def parse_ffmpeg_progress_seconds(line: str) -> Optional[float]:
    """Parse elapsed media seconds from an FFmpeg `-progress pipe:1` key=value line."""
    if not line or "=" not in line:
        return None
    key, _, val = line.strip().partition("=")
    val = val.strip()
    if not val or val == "N/A":
        return None
    if key == "out_time_us":
        try:
            us = int(val)
            return (us / 1_000_000.0) if us >= 0 else None
        except ValueError:
            return None
    if key == "out_time":
        m = _OUT_TIME_RE.match(val)
        if m:
            try:
                hrs = int(m.group(1))
                mins = int(m.group(2))
                secs = float(m.group(3))
                return max(0.0, hrs * 3600.0 + mins * 60.0 + secs)
            except ValueError:
                return None
    return None


def get_video_thumbnail_cache_dir(
    media_file: str | Path | None,
    project_file: str | Path | None = None,
    target_count: int | None = None,
) -> Path | None:
    """Return the deterministic thumbnail cache directory for a media file.

    Uses project-local `.cache/thumbnails/` for fast local drives, and automatically routes
    network/UNC projects to local `%LOCALAPPDATA%/RadioTVStorySegmenter/cache/thumbnails/`
    to avoid hundreds of slow SMB file operations on project open.
    """
    if not media_file:
        return None
    count_suffix = ""
    if target_count is not None:
        eff_c = max(8, min(MAX_TIMELINE_THUMBNAIL_COUNT, int(target_count)))
        if eff_c != _LEGACY_DEFAULT_THUMBNAIL_COUNT:
            count_suffix = f"_n{eff_c}"
    try:
        p = Path(media_file).resolve()
        stat = p.stat()
        key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}{count_suffix}"
        h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]

        # 1. Project-level thumbnail directory (local drives only)
        if project_file and not is_network_path(project_file):
            proj_p = Path(project_file).resolve()
            proj_dir = proj_p.parent if (proj_p.is_file() or proj_p.suffix.lower() in (".rtvs", ".json")) else proj_p
            if not is_network_path(proj_dir) and proj_dir.exists() and os.access(str(proj_dir), os.W_OK):
                base = proj_dir / ".cache" / "thumbnails"
                return base / h

        # 2. Check if media resides in a local project bundle
        if not is_network_path(p):
            candidate_proj = None
            if p.parent.name.lower() in ("media", "audio"):
                if list(p.parent.parent.glob("*.rtvs")) or (p.parent.parent / ".cache").exists():
                    candidate_proj = p.parent.parent
            elif list(p.parent.glob("*.rtvs")) or (p.parent / ".cache").exists():
                candidate_proj = p.parent

            if (
                candidate_proj
                and not is_network_path(candidate_proj)
                and candidate_proj.exists()
                and os.access(str(candidate_proj), os.W_OK)
            ):
                base = candidate_proj / ".cache" / "thumbnails"
                return base / h

        # 3. Local AppData cache (fast SSD storage; always used for network/UNC projects)
        base = get_app_data_dir() / "cache" / "thumbnails"
        return base / h
    except Exception:
        try:
            h = hashlib.sha256(f"{Path(media_file)}{count_suffix}".encode("utf-8")).hexdigest()[:24]
            base = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
            return base / h
        except Exception:
            return None


def read_video_thumbnail_cache(
    media_file: str | Path | None,
    duration: float,
    project_file: str | Path | None = None,
    target_count: int | None = None,
) -> list | None:
    """Read pre-extracted video thumbnail items [(timestamp, image_path), ...] from disk cache.

    Uses a single `os.scandir()` pass to validate JPEG entries without per-file stat round-trips.
    """
    if not media_file or duration <= 0:
        return None
    try:
        cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file, target_count=target_count)
        if not cache_dir or not cache_dir.exists() or not cache_dir.is_dir():
            count_suffix = ""
            if target_count is not None:
                eff_c = max(8, min(MAX_TIMELINE_THUMBNAIL_COUNT, int(target_count)))
                if eff_c != _LEGACY_DEFAULT_THUMBNAIL_COUNT:
                    count_suffix = f"_n{eff_c}"
            alt_dir = (
                Path(tempfile.gettempdir())
                / "radio_tv_story_segmenter_thumbnails"
                / hashlib.sha256(f"{Path(media_file)}{count_suffix}".encode("utf-8")).hexdigest()[:24]
            )
            if alt_dir.exists() and alt_dir.is_dir():
                cache_dir = alt_dir
            else:
                return None

        media_p = Path(media_file)
        if media_p.exists():
            if media_p.stat().st_mtime > cache_dir.stat().st_mtime:
                return None

        entries: List[Tuple[str, str]] = []
        with os.scandir(cache_dir) as it:
            for entry in it:
                name = entry.name
                if name.startswith("thumb_") and name.endswith(".jpg") and entry.is_file():
                    try:
                        if entry.stat(follow_symlinks=False).st_size <= 0:
                            return None
                    except OSError:
                        return None
                    entries.append((name, entry.path))

        if len(entries) < 2:
            return None

        entries.sort(key=lambda pair: pair[0])
        num = len(entries)
        items = []
        for i, (_name, fpath) in enumerate(entries):
            ts = (i / max(1, num - 1)) * duration if num > 1 else 0.0
            items.append((ts, fpath))
        return items
    except Exception:
        return None


def invalidate_video_thumbnail_cache(
    media_file: str | Path | None,
    project_file: str | Path | None = None,
    target_count: int | None = None,
) -> bool:
    """Delete the thumbnail cache directory for a given media file."""
    deleted = False
    counts_to_clear = [target_count] if target_count is not None else [None, _LEGACY_DEFAULT_THUMBNAIL_COUNT]
    try:
        for tc in counts_to_clear:
            cache_dir = get_video_thumbnail_cache_dir(media_file, project_file=project_file, target_count=tc)
            if cache_dir and cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)
                deleted = True
            if media_file:
                try:
                    p = Path(media_file).resolve()
                    stat = p.stat()
                    c_suf = f"_n{int(tc)}" if (tc is not None and int(tc) != _LEGACY_DEFAULT_THUMBNAIL_COUNT) else ""
                    key_raw = f"{p.name}_{stat.st_size}_{int(stat.st_mtime)}{c_suf}"
                    h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:24]
                    t_dir = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails" / h
                    if t_dir.exists():
                        shutil.rmtree(t_dir, ignore_errors=True)
                        deleted = True
                except Exception:
                    pass
    except Exception:
        pass
    return deleted


class VideoThumbnailCacheLoader(QObject):
    """Decode cached JPEG thumbnails into thread-safe QImages on a background QThread."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, items: List[Tuple[float, str]], media_path: str = "", target_count: int = 0, density: str = ""):
        super().__init__()
        self.items = list(items or [])
        self.media_path = str(media_path or "")
        self.target_count = int(target_count or 0)
        self.density = str(density or "")
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            try:
                from PySide6.QtGui import QImage
            except Exception:
                QImage = None

            decoded: List[Tuple[float, Any]] = []
            for ts, fpath in self.items:
                if self._cancelled:
                    self.finished.emit([])
                    return
                if QImage is not None:
                    img = QImage(str(fpath))
                    if not img.isNull():
                        decoded.append((float(ts), img))
                else:
                    decoded.append((float(ts), str(fpath)))
            if self._cancelled:
                self.finished.emit([])
                return
            self.finished.emit(decoded)
        except Exception as exc:
            if not self._cancelled:
                self.error.emit(str(exc))
            else:
                self.finished.emit([])


class VideoThumbnailWorker(QObject):
    """Background FFmpeg video thumbnail extractor with keyframe acceleration and live progress."""

    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        media_path,
        duration,
        output_dir,
        count=36,
        density: Optional[str] = None,
        use_keyframe_skip: Optional[bool] = None,
    ):
        super().__init__()
        self.media_path = Path(media_path)
        self.duration = max(0.1, float(duration or 0))
        self.output_dir = Path(output_dir)
        self.count = max(8, min(MAX_TIMELINE_THUMBNAIL_COUNT, int(count)))
        self.density = normalize_thumbnail_density(density) if density is not None else None
        if use_keyframe_skip is None:
            self.use_keyframe_skip = should_use_keyframe_skip(self.duration, self.count, density=self.density)
        else:
            self.use_keyframe_skip = bool(use_keyframe_skip)
        self._cancelled = False
        self._process = None
        self._proc_lock = threading.Lock()

    def build_ffmpeg_command(self, keyframe_skip: Optional[bool] = None) -> List[str]:
        """Construct the FFmpeg command vector for thumbnail extraction."""
        dur = max(0.001, float(self.duration or 0.0))
        fps = max(0.001, float(self.count or 1)) / dur
        vf = f"fps={fps:.8f},scale=240:-2:force_original_aspect_ratio=decrease"
        pattern = str(self.output_dir / "thumb_%04d.jpg")
        use_kf = self.use_keyframe_skip if keyframe_skip is None else bool(keyframe_skip)
        cmd = [ffmpeg_path() or "ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if use_kf:
            cmd.extend(["-skip_frame", "nokey"])
        cmd.extend([
            "-i", str(self.media_path),
            "-map", "0:v:0",
            "-vf", vf,
            "-q:v", "4",
            "-progress", "pipe:1",
            "-nostats",
            pattern,
        ])
        return cmd

    def cancel(self):
        with self._proc_lock:
            self._cancelled = True
            process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def _run_ffmpeg_pass(self, keyframe_skip: bool) -> Tuple[int, str, List[Path]]:
        cmd = self.build_ffmpeg_command(keyframe_skip=keyframe_skip)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        with self._proc_lock:
            if self._cancelled:
                return 0, "", []
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
            )
            self._process = process
        register_process(process)

        stderr_chunks: List[str] = []

        def _drain_stderr():
            try:
                if process.stderr is not None:
                    stderr_chunks.append(process.stderr.read() or "")
            except Exception:
                pass

        err_thread = threading.Thread(target=_drain_stderr, daemon=True)
        err_thread.start()

        dur = max(0.001, float(self.duration or 0.0))
        last_pct = 0
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    if self._cancelled:
                        break
                    cur_sec = parse_ffmpeg_progress_seconds(line)
                    if cur_sec is not None:
                        pct = max(1, min(99, int(round((cur_sec / dur) * 100.0))))
                        if pct != last_pct:
                            last_pct = pct
                            self.progress.emit(pct)
            process.wait()
            err_thread.join(timeout=1.0)
            returncode = process.returncode
        finally:
            unregister_process(process)
            with self._proc_lock:
                if self._process is process:
                    self._process = None

        files = sorted(self.output_dir.glob("thumb_*.jpg")) if (not self._cancelled and returncode == 0) else []
        return returncode, "".join(stderr_chunks).strip(), files

    def run(self):
        try:
            if self._cancelled:
                self.finished.emit([])
                return
            self.output_dir.mkdir(parents=True, exist_ok=True)
            returncode, stderr, files = self._run_ffmpeg_pass(keyframe_skip=self.use_keyframe_skip)

            # Fallback to full frame decoding if keyframe-only mode produced too few frames
            if not self._cancelled and self.use_keyframe_skip and (returncode != 0 or len(files) < 2):
                for stale in self.output_dir.glob("thumb_*.jpg"):
                    try:
                        stale.unlink(missing_ok=True)
                    except Exception:
                        pass
                returncode, stderr, files = self._run_ffmpeg_pass(keyframe_skip=False)

            if self._cancelled:
                self.finished.emit([])
                return
            if returncode != 0:
                raise RuntimeError(stderr or "FFmpeg could not create video thumbnails.")
            if not files:
                raise RuntimeError("No video thumbnails were generated.")

            try:
                from PySide6.QtGui import QImage
            except Exception:
                QImage = None

            actual_count = len(files)
            items: List[Tuple[float, Any]] = []
            for i, path in enumerate(files):
                if self._cancelled:
                    self.finished.emit([])
                    return
                timestamp = (i / max(1, actual_count - 1)) * self.duration if actual_count > 1 else 0.0
                if QImage is not None:
                    img = QImage(str(path))
                    if not img.isNull():
                        items.append((timestamp, img))
                        continue
                items.append((timestamp, str(path)))
            self.finished.emit(items)
        except Exception as exc:
            if not self._cancelled:
                self.error.emit(str(exc))
            else:
                self.finished.emit([])


__all__ = [
    "TIMELINE_THUMBNAIL_DENSITY_SPECS",
    "TIMELINE_THUMBNAIL_DENSITY_PRESETS",
    "DEFAULT_TIMELINE_THUMBNAIL_DENSITY",
    "MAX_TIMELINE_THUMBNAIL_COUNT",
    "_LEGACY_DEFAULT_THUMBNAIL_COUNT",
    "is_network_path",
    "normalize_thumbnail_density",
    "get_thumbnail_count_for_density",
    "should_use_keyframe_skip",
    "parse_ffmpeg_progress_seconds",
    "get_video_thumbnail_cache_dir",
    "read_video_thumbnail_cache",
    "invalidate_video_thumbnail_cache",
    "VideoThumbnailCacheLoader",
    "VideoThumbnailWorker",
]

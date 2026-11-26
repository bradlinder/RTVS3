"""Headless yt-dlp runtime provisioner, URL parser, metadata prober, and downloader.

Handles:
- Strict YouTube URL validation and canonicalization
- On-demand yt-dlp binary installation and SHA-256 verification into app-data tools
- In-app yt-dlp self-updating
- Quality presets (defaulting to 1080p MP4 H.264/AAC for crisp screenshots)
- Metadata & chapter probing, format size estimation, progress parsing, and
  actionable error classification (extractor update vs. browser cookies)

Zero PySide6/Qt imports (pure Python headless engine).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

DEFAULT_YOUTUBE_QUALITY: str = "1080p"

YOUTUBE_QUALITY_PRESETS: List[Tuple[str, str]] = [
    ("1080p", "1080p Full HD MP4 (Default — crisp screenshots)"),
    ("best", "Best Available Video (up to 4K / 1440p MP4)"),
    ("720p", "720p HD MP4 (Balanced)"),
    ("480p", "480p SD MP4 (Fast / Smaller)"),
    ("audio_only", "Audio Only (M4A — Fastest / Smallest)"),
]

ALLOWED_COOKIE_BROWSERS: List[Tuple[str, str]] = [
    ("", "None (Public videos)"),
    ("chrome", "Google Chrome"),
    ("edge", "Microsoft Edge"),
    ("firefox", "Mozilla Firefox"),
    ("brave", "Brave Browser"),
    ("chromium", "Chromium"),
    ("safari", "Safari (macOS)"),
]

_VALID_COOKIE_BROWSER_IDS = {b[0] for b in ALLOWED_COOKIE_BROWSERS if b[0]}

_YT_DLP_RELEASES_BASE = "https://github.com/yt-dlp/yt-dlp/releases/latest/download"
_YOUTUBE_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "studio.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}


def _subprocess_creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _resolve_app_data_root() -> Path:
    try:
        from core_utils import get_app_data_dir
        return Path(get_app_data_dir())
    except Exception:
        pass
    xdg = os.environ.get("XDG_DATA_HOME") or os.environ.get("LOCALAPPDATA")
    if xdg:
        return Path(xdg) / "RadioTVStorySegmenter"
    return Path.home() / ".radio_tv_story_segmenter"


def _resolve_ffmpeg_location() -> Optional[str]:
    """Return the bundled/configured FFmpeg path or directory if available."""
    try:
        from core_utils import ffmpeg_path
        ff = ffmpeg_path()
        if ff:
            p = Path(ff)
            if p.exists():
                return str(p.parent)
            found = shutil.which(str(ff))
            if found:
                return str(Path(found).parent)
    except Exception:
        pass
    found = shutil.which("ffmpeg")
    return str(Path(found).parent) if found else None


def extract_youtube_id_strict(url_or_id: str) -> Tuple[str, Optional[str]]:
    """Validate a YouTube URL or raw 11-char ID and return (video_id, canonical_url).

    Rejects non-YouTube hosts, file:// schemes, and flag-like inputs starting with '-'.
    """
    raw = str(url_or_id or "").strip()
    if not raw or raw.startswith("-"):
        return "", None

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", raw):
        return raw, f"https://www.youtube.com/watch?v={raw}"

    candidate = raw if "://" in raw else f"https://{raw.lstrip('/')}"
    try:
        parsed = urlparse(candidate)
    except Exception:
        return "", None

    if parsed.scheme not in ("http", "https"):
        return "", None

    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_ALLOWED_HOSTS:
        return "", None

    path = parsed.path or ""
    qs = parse_qs(parsed.query)
    vid = ""

    if "youtu.be" in host:
        parts = [seg for seg in path.strip("/").split("/") if seg]
        if parts and re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[0]):
            vid = parts[0]
    elif "studio.youtube.com" in host and "/video/" in path:
        seg = path.split("/video/", 1)[1].split("/")[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", seg):
            vid = seg
    elif "/watch" in path:
        v_val = qs.get("v", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", v_val):
            vid = v_val
    else:
        for prefix in ("/embed/", "/live/", "/shorts/", "/v/"):
            if prefix in path:
                seg = path.split(prefix, 1)[1].split("/")[0]
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", seg):
                    vid = seg
                    break

    if not vid:
        return "", None
    return vid, f"https://www.youtube.com/watch?v={vid}"


def normalize_quality_preset(preset: str) -> str:
    val = str(preset or "").strip().lower()
    valid = {k for k, _ in YOUTUBE_QUALITY_PRESETS}
    return val if val in valid else DEFAULT_YOUTUBE_QUALITY


def normalize_cookie_browser(browser: str) -> str:
    val = str(browser or "").strip().lower()
    return val if val in _VALID_COOKIE_BROWSER_IDS else ""


def get_format_selector_for_preset(preset: str) -> Tuple[str, str]:
    """Return (yt-dlp -f format selector, target output extension) for a quality preset."""
    q = normalize_quality_preset(preset)
    if q == "audio_only":
        return "bestaudio[ext=m4a]/bestaudio/best", "m4a"
    if q == "best":
        return "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best", "mp4"
    if q == "720p":
        return (
            "bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/"
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "mp4",
        )
    if q == "480p":
        return (
            "bestvideo[height<=480][vcodec^=avc1]+bestaudio[ext=m4a]/"
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            "mp4",
        )
    # Default: 1080p Full HD MP4 (prefer H.264 + AAC for smooth Qt scrubbing & crisp screenshots)
    return (
        "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/"
        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "mp4",
    )


def get_yt_dlp_tools_dir(base_dir: Optional[Path | str] = None) -> Path:
    root = Path(base_dir).expanduser() if base_dir is not None else (_resolve_app_data_root() / "tools" / "yt-dlp")
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def get_platform_yt_dlp_asset_name(platform_name: Optional[str] = None) -> str:
    plat = (platform_name or sys.platform).lower()
    if plat.startswith("win"):
        return "yt-dlp.exe"
    if plat == "darwin":
        return "yt-dlp_macos"
    return "yt-dlp_linux"


def get_managed_yt_dlp_path(base_dir: Optional[Path | str] = None, platform_name: Optional[str] = None) -> Path:
    asset = get_platform_yt_dlp_asset_name(platform_name)
    local_name = "yt-dlp.exe" if asset.endswith(".exe") else "yt-dlp"
    return get_yt_dlp_tools_dir(base_dir) / local_name


def find_yt_dlp_binary(
    base_dir: Optional[Path | str] = None,
    allow_system_fallback: bool = True,
) -> Optional[Path]:
    """Locate the managed yt-dlp binary, optionally falling back to system PATH."""
    managed = get_managed_yt_dlp_path(base_dir=base_dir)
    if managed.exists() and managed.is_file():
        return managed
    if allow_system_fallback:
        sys_bin = shutil.which("yt-dlp")
        if sys_bin:
            return Path(sys_bin)
    return None


def get_yt_dlp_version(binary_path: Optional[Path | str] = None) -> str:
    """Return the version string reported by `yt-dlp --version`, or empty string."""
    bin_path = Path(binary_path) if binary_path else find_yt_dlp_binary()
    if not bin_path or not bin_path.exists():
        return ""
    try:
        res = subprocess.run(
            [str(bin_path), "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_subprocess_creation_flags(),
        )
        if res.returncode == 0:
            return (res.stdout or "").strip().splitlines()[0].strip()
    except Exception:
        pass
    return ""


def parse_sha256_sums(sums_text: str, asset_name: str) -> Optional[str]:
    """Extract the expected lowercase SHA-256 hex digest for ``asset_name`` from SHA2-256SUMS."""
    target = str(asset_name or "").strip()
    if not target or not sums_text:
        return None
    for line in sums_text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            digest = parts[0].strip().lower()
            fname = parts[-1].strip().lstrip("*")
            if fname == target and re.fullmatch(r"[0-9a-f]{64}", digest):
                return digest
    return None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()


def install_or_update_yt_dlp(
    base_dir: Optional[Path | str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    platform_name: Optional[str] = None,
) -> Tuple[Path, str]:
    """Download, SHA-256 verify, and install the latest official standalone yt-dlp binary."""
    import urllib.request

    asset = get_platform_yt_dlp_asset_name(platform_name)
    dest = get_managed_yt_dlp_path(base_dir=base_dir, platform_name=platform_name)
    dest.parent.mkdir(parents=True, exist_ok=True)

    sums_url = f"{_YT_DLP_RELEASES_BASE}/SHA2-256SUMS"
    bin_url = f"{_YT_DLP_RELEASES_BASE}/{asset}"

    def _emit(pct: int, msg: str) -> None:
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass

    def _cancelled() -> bool:
        return bool(cancel_check and cancel_check())

    _emit(5, f"Fetching yt-dlp release checksums ({asset})...")
    expected_sha: Optional[str] = None
    try:
        req = urllib.request.Request(sums_url, headers={"User-Agent": "RadioTVStorySegmenter"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            sums_text = resp.read().decode("utf-8", errors="replace")
        expected_sha = parse_sha256_sums(sums_text, asset)
    except Exception as exc:
        raise RuntimeError(f"Could not download yt-dlp release checksums: {exc}") from exc

    if not expected_sha:
        raise RuntimeError(f"Official yt-dlp SHA2-256SUMS did not include a checksum for '{asset}'.")

    if _cancelled():
        raise InterruptedError("yt-dlp installation cancelled.")

    tmp_path = dest.with_suffix(dest.suffix + ".part")
    _emit(15, f"Downloading {asset}...")
    try:
        req = urllib.request.Request(bin_url, headers={"User-Agent": "RadioTVStorySegmenter"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            with open(tmp_path, "wb") as out_f:
                while True:
                    if _cancelled():
                        raise InterruptedError("yt-dlp download cancelled.")
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = 15 + int((downloaded / total) * 75)
                        _emit(min(90, pct), f"Downloading {asset} ({downloaded / (1024 * 1024):.1f} MB)...")
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    _emit(92, "Verifying SHA-256 checksum...")
    actual_sha = _sha256_file(tmp_path)
    if actual_sha != expected_sha:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise RuntimeError(
            f"yt-dlp integrity verification failed (expected {expected_sha[:12]}..., got {actual_sha[:12]}...)."
        )

    if not (platform_name or sys.platform).lower().startswith("win"):
        try:
            mode = tmp_path.stat().st_mode
            tmp_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

    os.replace(tmp_path, dest)
    version = get_yt_dlp_version(dest) or "latest"
    _emit(100, f"yt-dlp {version} installed and verified.")
    return dest, version


def format_upload_date(raw_yyyymmdd: Optional[str]) -> str:
    """Convert yt-dlp upload_date ('20260412') into '2026-04-12'."""
    raw = str(raw_yyyymmdd or "").strip()
    if re.fullmatch(r"\d{8}", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def build_youtube_project_stem(title: str, upload_date: str = "", video_id: str = "") -> str:
    """Build a clean, readable default .rtvs project stem from title + upload date."""
    clean_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", str(title or "").strip())
    clean_title = re.sub(r"\s+", "_", clean_title).strip("._- ")
    if len(clean_title) > 64:
        clean_title = clean_title[:64].rstrip("._- ")
    clean_date = format_upload_date(upload_date)
    if clean_date and clean_title:
        return f"{clean_date}_{clean_title}"
    if clean_title:
        return clean_title
    if clean_date and video_id:
        return f"{clean_date}_YouTube_{video_id}"
    return f"YouTube_{video_id or 'Episode'}"


def estimate_preset_size_bytes(info: Dict[str, Any], preset: str) -> int:
    """Estimate download size in bytes for a quality preset from yt-dlp metadata."""
    q = normalize_quality_preset(preset)
    formats = info.get("formats") if isinstance(info.get("formats"), list) else []
    duration = float(info.get("duration") or 0.0)

    def _fmt_size(f: Dict[str, Any]) -> int:
        for key in ("filesize", "filesize_approx"):
            val = f.get(key)
            if val is not None:
                try:
                    iv = int(val)
                    if iv > 0:
                        return iv
                except (TypeError, ValueError):
                    pass
        tbr = f.get("tbr") or f.get("abr") or f.get("vbr")
        if tbr and duration > 0:
            try:
                return int((float(tbr) * 1000.0 / 8.0) * duration)
            except (TypeError, ValueError):
                pass
        return 0

    audio_fmts = [
        f for f in formats
        if isinstance(f, dict) and f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    best_audio_size = 0
    if audio_fmts:
        audio_fmts.sort(key=lambda f: (1 if f.get("ext") == "m4a" else 0, float(f.get("abr") or f.get("tbr") or 0)), reverse=True)
        best_audio_size = _fmt_size(audio_fmts[0])

    if q == "audio_only":
        return best_audio_size or (int(duration * 16000) if duration > 0 else 0)

    max_height = {"1080p": 1080, "720p": 720, "480p": 480, "best": 99999}.get(q, 1080)
    video_fmts = [
        f for f in formats
        if isinstance(f, dict)
        and f.get("vcodec") not in (None, "none")
        and int(f.get("height") or 0) > 0
        and int(f.get("height") or 0) <= max_height
    ]
    if video_fmts:
        video_fmts.sort(
            key=lambda f: (
                int(f.get("height") or 0),
                1 if str(f.get("vcodec") or "").startswith("avc1") else 0,
                float(f.get("tbr") or f.get("vbr") or 0),
            ),
            reverse=True,
        )
        chosen = video_fmts[0]
        v_size = _fmt_size(chosen)
        has_muxed_audio = chosen.get("acodec") not in (None, "none")
        return v_size if has_muxed_audio else (v_size + best_audio_size)

    # Heuristic fallback by resolution & duration when formats omit sizes
    if duration > 0:
        kbps = {"best": 5500, "1080p": 3200, "720p": 1800, "480p": 900}.get(q, 2500)
        return int((kbps * 1000.0 / 8.0) * duration)
    return 0


def parse_youtube_chapters(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize yt-dlp chapters list into [{title, start, end}]."""
    raw = info.get("chapters")
    if not isinstance(raw, list):
        return []
    duration = float(info.get("duration") or 0.0)
    out: List[Dict[str, Any]] = []
    for idx, ch in enumerate(raw):
        if not isinstance(ch, dict):
            continue
        try:
            start = max(0.0, float(ch.get("start_time", 0.0)))
        except (TypeError, ValueError):
            continue
        end_raw = ch.get("end_time")
        try:
            end = float(end_raw) if end_raw is not None else duration
        except (TypeError, ValueError):
            end = duration
        if end <= start:
            continue
        title = str(ch.get("title") or f"Chapter {idx + 1}").strip()
        out.append({"title": title, "start": round(start, 3), "end": round(end, 3)})
    return out


def parse_yt_dlp_metadata_json(raw_info: Dict[str, Any], fallback_url: str = "") -> Dict[str, Any]:
    """Normalize raw `yt-dlp --dump-single-json` output into a clean metadata dict."""
    vid = str(raw_info.get("id") or "").strip()
    canonical = f"https://www.youtube.com/watch?v={vid}" if vid else str(raw_info.get("webpage_url") or fallback_url).strip()
    upload_date = format_upload_date(raw_info.get("upload_date"))
    title = str(raw_info.get("title") or "").strip() or f"YouTube Video {vid}"
    size_estimates = {
        preset: estimate_preset_size_bytes(raw_info, preset)
        for preset, _ in YOUTUBE_QUALITY_PRESETS
    }
    return {
        "video_id": vid,
        "canonical_url": canonical,
        "title": title,
        "description": str(raw_info.get("description") or "").strip(),
        "channel": str(raw_info.get("channel") or raw_info.get("uploader") or "").strip(),
        "duration": max(0.0, float(raw_info.get("duration") or 0.0)),
        "upload_date": upload_date,
        "thumbnail_url": str(raw_info.get("thumbnail") or "").strip(),
        "is_live": bool(raw_info.get("is_live", False)),
        "chapters": parse_youtube_chapters(raw_info),
        "size_estimates": size_estimates,
        "suggested_project_stem": build_youtube_project_stem(title, upload_date, vid),
    }


def classify_yt_dlp_error(stderr_text: str) -> Dict[str, Any]:
    """Translate raw yt-dlp error stderr into actionable user-facing guidance."""
    raw = str(stderr_text or "").strip()
    low = raw.lower()

    # Keep the most informative ERROR line for concise diagnostics
    err_lines = [ln.strip() for ln in raw.splitlines() if "error:" in ln.lower()]
    summary = err_lines[-1] if err_lines else (raw.splitlines()[-1].strip() if raw else "Unknown yt-dlp error.")
    if len(summary) > 260:
        summary = summary[:257] + "..."

    if any(tok in low for tok in (
        "sign in to confirm you're not a bot",
        "sign in to confirm you\u2019re not a bot",
        "confirm your age",
        "age-restricted",
        "private video",
        "members-only",
        "join this channel to get access",
        "cookies",
        "login required",
    )):
        return {
            "category": "needs_cookies",
            "needs_update": False,
            "needs_cookies": True,
            "message": (
                "YouTube requires signed-in browser access for this video (unlisted, restricted, "
                "or bot-check challenge). Select your signed-in browser under Advanced > Browser Cookies and retry."
            ),
            "detail": summary,
        }

    if any(tok in low for tok in (
        "http error 403",
        "403: forbidden",
        "unable to extract",
        "nsig extraction failed",
        "signature extraction failed",
        "sabr",
        "requested format is not available",
        "failed to extract any player response",
    )):
        return {
            "category": "needs_update",
            "needs_update": True,
            "needs_cookies": False,
            "message": (
                "YouTube changed its playback format or blocked this older yt-dlp build. "
                "Click 'Update yt-dlp & Retry' to fetch the latest extractor."
            ),
            "detail": summary,
        }

    if any(tok in low for tok in ("this live event will begin", "premieres in", "is currently live")):
        return {
            "category": "is_live",
            "needs_update": False,
            "needs_cookies": False,
            "message": "This YouTube video is currently a live broadcast or upcoming premiere. Wait until the stream finishes processing before importing.",
            "detail": summary,
        }

    if any(tok in low for tok in ("video unavailable", "removed by the uploader", "copyright claim", "account associated with this video")):
        return {
            "category": "unavailable",
            "needs_update": False,
            "needs_cookies": False,
            "message": "This YouTube video is unavailable, deleted, or blocked in your region.",
            "detail": summary,
        }

    return {
        "category": "generic",
        "needs_update": False,
        "needs_cookies": False,
        "message": f"YouTube download error: {summary}",
        "detail": summary,
    }


_DL_PCT_RE = re.compile(
    r"\[download\]\s+(?P<pct>\d+(?:\.\d+)?)%\s+of\s+~?\s*(?P<total>\S+)"
    r"(?:\s+at\s+(?P<speed>\S+))?(?:\s+ETA\s+(?P<eta>\S+))?",
    re.IGNORECASE,
)


def parse_yt_dlp_progress_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a yt-dlp stdout line into structured download/merge progress."""
    txt = str(line or "").strip()
    if not txt:
        return None
    m = _DL_PCT_RE.search(txt)
    if m:
        pct = max(0.0, min(100.0, float(m.group("pct"))))
        speed = m.group("speed") or ""
        eta = m.group("eta") or ""
        total = m.group("total") or ""
        parts = [f"Downloading {pct:.1f}%"]
        if total and total.lower() != "unknown":
            parts.append(f"of {total}")
        if speed and speed.lower() not in ("unknown", "n/a"):
            parts.append(f"at {speed}")
        if eta and eta.lower() not in ("unknown", "n/a"):
            parts.append(f"(ETA {eta})")
        return {
            "percent": int(round(pct * 0.90)),  # Reserve 90..100% for FFmpeg merge
            "stage": "downloading",
            "detail": " ".join(parts),
            "speed": speed,
            "eta": eta,
        }
    if txt.startswith("[Merger]") or "Merging formats into" in txt:
        return {
            "percent": 94,
            "stage": "merging",
            "detail": "Merging video and audio into MP4 with FFmpeg...",
            "speed": "",
            "eta": "",
        }
    if txt.startswith("[ExtractAudio]"):
        return {
            "percent": 94,
            "stage": "merging",
            "detail": "Extracting audio track...",
            "speed": "",
            "eta": "",
        }
    return None


def build_yt_dlp_probe_command(
    yt_dlp_bin: Path | str,
    canonical_url: str,
    cookies_browser: str = "",
) -> List[str]:
    cmd = [
        str(yt_dlp_bin),
        "--dump-single-json",
        "--no-playlist",
        "--no-warnings",
        "--skip-download",
    ]
    browser = normalize_cookie_browser(cookies_browser)
    if browser:
        cmd.extend(["--cookies-from-browser", browser])
    cmd.extend(["--", canonical_url])
    return cmd


def probe_youtube_video(
    url_or_id: str,
    yt_dlp_bin: Optional[Path | str] = None,
    cookies_browser: str = "",
    timeout: int = 60,
) -> Dict[str, Any]:
    """Fetch normalized metadata, chapters, and size estimates for a YouTube video."""
    vid, canonical = extract_youtube_id_strict(url_or_id)
    if not vid or not canonical:
        raise ValueError("Please enter a valid YouTube video URL or 11-character video ID.")

    binary = Path(yt_dlp_bin) if yt_dlp_bin else find_yt_dlp_binary()
    if not binary or not binary.exists():
        raise FileNotFoundError("yt-dlp is not installed yet.")

    cmd = build_yt_dlp_probe_command(binary, canonical, cookies_browser=cookies_browser)
    res = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=_subprocess_creation_flags(),
    )
    if res.returncode != 0:
        err_info = classify_yt_dlp_error(res.stderr or res.stdout)
        err = RuntimeError(err_info["message"])
        setattr(err, "yt_dlp_error", err_info)
        raise err

    stdout = (res.stdout or "").strip()
    if not stdout:
        raise RuntimeError("yt-dlp returned empty metadata for this video.")
    # Handle any stray leading log lines before JSON object
    json_start = stdout.find("{")
    if json_start < 0:
        raise RuntimeError("Could not parse yt-dlp metadata response.")
    raw_info = json.loads(stdout[json_start:])
    return parse_yt_dlp_metadata_json(raw_info, fallback_url=canonical)


def build_yt_dlp_download_command(
    yt_dlp_bin: Path | str,
    canonical_url: str,
    output_base_path: Path | str,
    quality_preset: str = DEFAULT_YOUTUBE_QUALITY,
    cookies_browser: str = "",
    ffmpeg_location: Optional[str] = None,
) -> Tuple[List[str], str]:
    """Construct a safe argument list for yt-dlp video/audio download."""
    fmt_selector, target_ext = get_format_selector_for_preset(quality_preset)
    out_template = f"{output_base_path}.%(ext)s"
    cmd = [
        str(yt_dlp_bin),
        "--no-playlist",
        "--newline",
        "--progress",
        "--no-warnings",
        "-f", fmt_selector,
        "-o", out_template,
        "--print", "after_move:filepath",
    ]
    if target_ext == "mp4":
        cmd.extend(["--merge-output-format", "mp4"])
    ff_loc = ffmpeg_location if ffmpeg_location is not None else _resolve_ffmpeg_location()
    if ff_loc:
        cmd.extend(["--ffmpeg-location", str(ff_loc)])
    browser = normalize_cookie_browser(cookies_browser)
    if browser:
        cmd.extend(["--cookies-from-browser", browser])
    cmd.extend(["--", canonical_url])
    return cmd, target_ext


def download_youtube_video(
    url_or_id: str,
    output_dir: Path | str,
    filename_stem: str,
    quality_preset: str = DEFAULT_YOUTUBE_QUALITY,
    yt_dlp_bin: Optional[Path | str] = None,
    cookies_browser: str = "",
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    process_callback: Optional[Callable[[Optional[subprocess.Popen]], None]] = None,
) -> Path:
    """Download and remux a YouTube video into ``output_dir`` with streaming progress."""
    vid, canonical = extract_youtube_id_strict(url_or_id)
    if not vid or not canonical:
        raise ValueError("Please enter a valid YouTube video URL or 11-character video ID.")

    binary = Path(yt_dlp_bin) if yt_dlp_bin else find_yt_dlp_binary()
    if not binary or not binary.exists():
        raise FileNotFoundError("yt-dlp is not installed yet.")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(filename_stem or f"yt_{vid}")).strip("._ ") or f"yt_{vid}"
    base_path = out_dir / safe_stem

    cmd, target_ext = build_yt_dlp_download_command(
        binary,
        canonical,
        base_path,
        quality_preset=quality_preset,
        cookies_browser=cookies_browser,
    )

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_subprocess_creation_flags(),
    )
    if process_callback:
        process_callback(proc)

    reported_paths: List[str] = []
    stdout_lines: List[str] = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            if cancel_check and cancel_check():
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                raise InterruptedError("YouTube download cancelled.")

            stripped = line.strip()
            if not stripped:
                continue
            stdout_lines.append(stripped)
            prog = parse_yt_dlp_progress_line(stripped)
            if prog and progress_callback:
                progress_callback(int(prog["percent"]), str(prog["detail"]))
            else:
                # Check if --print after_move:filepath emitted a real path inside out_dir
                p_cand = Path(stripped)
                if p_cand.exists() and p_cand.is_file():
                    reported_paths.append(str(p_cand))

        stderr_text = proc.stderr.read() if proc.stderr else ""
        returncode = proc.wait()
    finally:
        if process_callback:
            process_callback(None)

    if returncode != 0:
        err_info = classify_yt_dlp_error(stderr_text or "\n".join(stdout_lines[-10:]))
        err = RuntimeError(err_info["message"])
        setattr(err, "yt_dlp_error", err_info)
        raise err

    # Locate final output file
    for rp in reversed(reported_paths):
        p = Path(rp)
        if p.exists() and p.is_file():
            if progress_callback:
                progress_callback(100, "Download complete.")
            return p.resolve()

    expected = base_path.with_suffix(f".{target_ext}")
    if expected.exists() and expected.is_file():
        if progress_callback:
            progress_callback(100, "Download complete.")
        return expected.resolve()

    for cand in sorted(out_dir.glob(f"{safe_stem}.*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if cand.is_file() and cand.suffix.lower() not in (".part", ".ytdl", ".tmp"):
            if progress_callback:
                progress_callback(100, "Download complete.")
            return cand.resolve()

    raise RuntimeError("yt-dlp finished without producing an output media file.")


__all__ = [
    "DEFAULT_YOUTUBE_QUALITY",
    "YOUTUBE_QUALITY_PRESETS",
    "ALLOWED_COOKIE_BROWSERS",
    "extract_youtube_id_strict",
    "normalize_quality_preset",
    "normalize_cookie_browser",
    "get_format_selector_for_preset",
    "get_yt_dlp_tools_dir",
    "get_platform_yt_dlp_asset_name",
    "get_managed_yt_dlp_path",
    "find_yt_dlp_binary",
    "get_yt_dlp_version",
    "parse_sha256_sums",
    "install_or_update_yt_dlp",
    "format_upload_date",
    "build_youtube_project_stem",
    "estimate_preset_size_bytes",
    "parse_youtube_chapters",
    "parse_yt_dlp_metadata_json",
    "classify_yt_dlp_error",
    "parse_yt_dlp_progress_line",
    "build_yt_dlp_probe_command",
    "probe_youtube_video",
    "build_yt_dlp_download_command",
    "download_youtube_video",
]

"""Headless YouTube-source featured image defaults, thumbnail caching, and embed inheritance.

Zero PySide6/Qt imports and zero cross-plugin imports from ``plugins.youtube``.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlparse

from remote_media_cache import RemoteMediaCacheManager

_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YT_EMBED_ID_RE = re.compile(
    r"(?:v=|/embed/|/live/|/shorts/|youtu\.be/|/video/)([A-Za-z0-9_-]{11})"
)
_ALLOWED_YT_THUMB_HOSTS = frozenset({
    "i.ytimg.com",
    "img.youtube.com",
    "i1.ytimg.com",
    "i2.ytimg.com",
    "i3.ytimg.com",
    "i4.ytimg.com",
    "i9.ytimg.com",
    "yt3.ggpht.com",
    "lh3.googleusercontent.com",
})


def extract_youtube_id_headless(url_or_id: str) -> str:
    """Extract a validated 11-character YouTube video ID without Qt dependencies."""
    raw = str(url_or_id or "").strip()
    if not raw:
        return ""
    if _YT_ID_RE.fullmatch(raw):
        return raw
    url_to_parse = raw if ("://" in raw or raw.startswith("//")) else f"https://{raw}"
    try:
        parsed = urlparse(url_to_parse)
        netloc = (parsed.netloc or "").lower()
        path = parsed.path or ""
        qs = parse_qs(parsed.query)
        if "youtube.com" in netloc and "/watch" in path:
            v_val = (qs.get("v") or [""])[0]
            if _YT_ID_RE.fullmatch(v_val):
                return v_val
        if "youtu.be" in netloc:
            parts = [p for p in path.strip("/").split("/") if p]
            if parts and _YT_ID_RE.fullmatch(parts[0]):
                return parts[0]
        for prefix in ("/embed/", "/live/", "/shorts/"):
            if prefix in path:
                seg = path.split(prefix, 1)[1].split("/")[0].split("?")[0]
                if _YT_ID_RE.fullmatch(seg):
                    return seg
        if "studio.youtube.com" in netloc and "/video/" in path:
            seg = path.split("/video/", 1)[1].split("/")[0].split("?")[0]
            if _YT_ID_RE.fullmatch(seg):
                return seg
    except Exception:
        pass
    match = _YT_EMBED_ID_RE.search(raw)
    return match.group(1) if match else ""


def get_youtube_thumbnail_cache_path(
    video_id: str,
    cache_dir: Optional[Path | str] = None,
) -> Optional[Path]:
    """Return the deterministic local cache path for a YouTube video's default thumbnail."""
    vid = extract_youtube_id_headless(video_id)
    if not vid:
        return None
    cache_mgr = RemoteMediaCacheManager(cache_dir=cache_dir)
    provider_dir = cache_mgr.get_provider_dir("youtube")
    return provider_dir / f"{vid}_yt_thumb.jpg"


def get_youtube_source_info(
    main_window: Any,
    cache_dir: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Inspect project metadata to determine whether the active source media is from YouTube."""
    proj_meta = getattr(main_window, "project_metadata", None)
    if not isinstance(proj_meta, dict):
        proj_meta = {}
    remote_src = proj_meta.get("remote_media_source")
    if not isinstance(remote_src, dict):
        remote_src = {}
    is_yt_source = str(remote_src.get("provider") or "").strip().lower() == "youtube"
    if not is_yt_source:
        return {
            "is_youtube_source": False,
            "video_id": "",
            "source_url": "",
            "thumbnail_url": "",
            "thumbnail_path": "",
        }

    video_id = extract_youtube_id_headless(
        remote_src.get("video_id")
        or remote_src.get("source_id")
        or remote_src.get("source_url")
        or ""
    )
    source_url = str(remote_src.get("source_url") or "").strip()
    if not source_url and video_id:
        source_url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail_url = str(remote_src.get("thumbnail_url") or "").strip()

    thumbnail_path = ""
    raw_saved_path = str(remote_src.get("thumbnail_path") or "").strip()
    if raw_saved_path and Path(raw_saved_path).is_file() and Path(raw_saved_path).stat().st_size > 0:
        thumbnail_path = raw_saved_path
    elif video_id:
        cached = get_youtube_thumbnail_cache_path(video_id, cache_dir=cache_dir)
        if cached and cached.is_file() and cached.stat().st_size > 0:
            thumbnail_path = str(cached)

    return {
        "is_youtube_source": True,
        "video_id": video_id,
        "source_url": source_url,
        "thumbnail_url": thumbnail_url,
        "thumbnail_path": thumbnail_path,
    }


def resolve_post_youtube_video_id(post: Optional[Dict[str, Any]], main_window: Any) -> str:
    """Resolve the active 11-character YouTube video ID for a post or YouTube-source project."""
    if isinstance(post, dict):
        vid = extract_youtube_id_headless(post.get("youtube_video_id") or post.get("youtube_url") or "")
        if vid:
            return vid
    yt_src = get_youtube_source_info(main_window)
    return yt_src["video_id"] if yt_src["is_youtube_source"] else ""


def resolve_inherited_youtube_embed(
    main_window: Any,
    story_wp_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve episode-level YouTube embed settings that individual stories should inherit.

    Returns an empty ``youtube_url`` if the story explicitly cleared its embed or
    project-level ``youtube_apply_all`` is disabled.
    """
    story_meta = story_wp_meta if isinstance(story_wp_meta, dict) else {}
    if story_meta.get("youtube_explicitly_cleared"):
        return {
            "youtube_url": "",
            "youtube_video_id": "",
            "youtube_use_story_time": bool(story_meta.get("youtube_use_story_time", True)),
            "youtube_stop_at_end": bool(story_meta.get("youtube_stop_at_end", False)),
            "youtube_placement": str(story_meta.get("youtube_placement") or "top"),
        }

    proj_meta = getattr(main_window, "project_metadata", None)
    if not isinstance(proj_meta, dict):
        proj_meta = {}
    proj_wp = proj_meta.get("wordpress")
    if not isinstance(proj_wp, dict):
        proj_wp = {}

    apply_all = proj_wp.get("youtube_apply_all", True)
    proj_url = str(proj_wp.get("youtube_url") or "").strip()
    proj_vid = extract_youtube_id_headless(proj_wp.get("youtube_video_id") or proj_url)

    yt_src = get_youtube_source_info(main_window)
    if yt_src["is_youtube_source"] and not proj_wp.get("youtube_explicitly_cleared"):
        if not proj_url and yt_src["source_url"]:
            proj_url = yt_src["source_url"]
        if not proj_vid and yt_src["video_id"]:
            proj_vid = yt_src["video_id"]

    if not proj_url and proj_vid:
        proj_url = f"https://www.youtube.com/watch?v={proj_vid}"

    if apply_all and proj_url:
        return {
            "youtube_url": proj_url,
            "youtube_video_id": proj_vid,
            "youtube_use_story_time": bool(proj_wp.get("youtube_use_story_time", True)),
            "youtube_stop_at_end": bool(proj_wp.get("youtube_stop_at_end", False)),
            "youtube_placement": str(proj_wp.get("youtube_placement") or "top"),
        }

    return {
        "youtube_url": "",
        "youtube_video_id": "",
        "youtube_use_story_time": bool(proj_wp.get("youtube_use_story_time", True)),
        "youtube_stop_at_end": bool(proj_wp.get("youtube_stop_at_end", False)),
        "youtube_placement": str(proj_wp.get("youtube_placement") or "top"),
    }


def compute_default_segment_frame_pos(
    start: Optional[float],
    end: Optional[float],
    fallback: float = 0.0,
) -> float:
    """Compute a representative video timestamp strictly inside ``[start, end]``."""
    if start is None:
        return max(0.0, float(fallback or 0.0))
    st = max(0.0, float(start))
    if end is not None:
        en = float(end)
        if en > st:
            span = en - st
            offset = min(5.0, span * 0.25)
            if span > 0.2:
                return min(en - 0.05, st + offset)
            return st + span * 0.5
    return st


def should_apply_youtube_featured_default(
    wp_meta: Optional[Dict[str, Any]],
    container_meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """Return True when no explicit featured image preference has been chosen yet.

    Legacy saved projects frequently persisted passive ``featured_image_mode='none'``
    without ``featured_image_user_set=True``. Those upgrade smoothly to YouTube-source
    defaults, whereas an explicit user click on 'None' is strictly preserved.
    """
    wp_d = wp_meta if isinstance(wp_meta, dict) else {}
    ct_d = container_meta if isinstance(container_meta, dict) else {}
    if bool(wp_d.get("featured_image_user_set") or ct_d.get("featured_image_user_set")):
        return False
    raw_mode = str(wp_d.get("featured_image_mode") or ct_d.get("featured_image_mode") or "").strip().lower()
    raw_img = wp_d.get("featured_image") if wp_d.get("featured_image") is not None else ct_d.get("featured_image")
    if raw_mode in ("grab", "youtube"):
        return False
    if raw_mode == "file" and raw_img:
        return False
    if raw_mode in ("", "none") and not raw_img:
        return True
    return False


def build_youtube_thumbnail_candidates(video_id: str, thumbnail_url: str = "") -> List[str]:
    """Return ordered HTTPS YouTube thumbnail candidate URLs preferring high-res JPEG."""
    vid = extract_youtube_id_headless(video_id)
    if not vid:
        return []

    candidates: List[str] = [f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"]

    clean_thumb = str(thumbnail_url or "").strip()
    if clean_thumb:
        try:
            parsed = urlparse(clean_thumb)
            if parsed.scheme == "https" and (parsed.hostname or "").lower() in _ALLOWED_YT_THUMB_HOSTS:
                if clean_thumb not in candidates:
                    candidates.append(clean_thumb)
        except Exception:
            pass

    for fallback_name in ("sddefault.jpg", "hqdefault.jpg"):
        url = f"https://i.ytimg.com/vi/{vid}/{fallback_name}"
        if url not in candidates:
            candidates.append(url)
    return candidates


def _normalize_thumbnail_bytes_to_jpeg(raw: bytes) -> Optional[bytes]:
    """Validate downloaded thumbnail bytes and normalize PNG/WEBP payloads to JPEG."""
    if not raw or len(raw) < 1024:
        return None

    is_jpeg = raw.startswith(b"\xff\xd8\xff")
    is_png = raw.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        return None

    try:
        from PIL import Image

        with Image.open(io.BytesIO(raw)) as img:
            w, h = img.size
            # Reject YouTube's tiny 120x90 grey missing-thumbnail placeholder
            if w <= 120 and h <= 90:
                return None
            if is_jpeg:
                return raw
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=92)
            converted = buf.getvalue()
            return converted if len(converted) >= 1024 else None
    except ImportError:
        return raw if is_jpeg else None
    except Exception:
        return raw if is_jpeg else None


def _default_http_fetch(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RadioTVStorySegmenter/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", 200)
        if status != 200:
            return b""
        return resp.read(15 * 1024 * 1024)


def ensure_youtube_thumbnail_cached(
    video_id: str,
    thumbnail_url: str = "",
    timeout: float = 8.0,
    cache_dir: Optional[Path | str] = None,
    fetcher: Optional[Callable[[str, float], bytes]] = None,
) -> Optional[Path]:
    """Download (if needed) and atomically cache a YouTube video's default thumbnail."""
    target = get_youtube_thumbnail_cache_path(video_id, cache_dir=cache_dir)
    if target is None:
        return None
    if target.is_file() and target.stat().st_size > 0:
        return target

    fetch_fn = fetcher or _default_http_fetch
    for candidate_url in build_youtube_thumbnail_candidates(video_id, thumbnail_url=thumbnail_url):
        try:
            raw = fetch_fn(candidate_url, timeout)
            jpeg_bytes = _normalize_thumbnail_bytes_to_jpeg(raw)
            if not jpeg_bytes:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = target.with_name(f"{target.name}.{os.getpid()}.tmp")
            with open(tmp_path, "wb") as f:
                f.write(jpeg_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
            return target
        except Exception:
            continue
    return None


def materialize_post_featured_image(
    post: Dict[str, Any],
    main_window: Any,
    post_index: int = 0,
    temp_files_out: Optional[Set[str]] = None,
    allow_network: bool = True,
    cache_dir: Optional[Path | str] = None,
    fetcher: Optional[Callable[[str, float], bytes]] = None,
    frame_capturer: Optional[Callable[..., bool]] = None,
) -> Optional[str]:
    """Ensure a post's configured featured image exists on disk and return its path."""
    if not isinstance(post, dict):
        return None
    mode = str(post.get("featured_image_mode") or "none").strip().lower()
    if mode == "none":
        return None

    existing = post.get("featured_image")
    if existing:
        existing_p = Path(str(existing))
        if existing_p.is_file() and existing_p.stat().st_size > 0:
            return str(existing_p)

    if mode == "file":
        return None

    if mode == "youtube":
        yt_src = get_youtube_source_info(main_window, cache_dir=cache_dir)
        vid = resolve_post_youtube_video_id(post, main_window)
        if not vid:
            return None
        cached = get_youtube_thumbnail_cache_path(vid, cache_dir=cache_dir)
        if cached and cached.is_file() and cached.stat().st_size > 0:
            post["featured_image"] = str(cached)
            return str(cached)
        if not allow_network:
            return None
        fetched = ensure_youtube_thumbnail_cached(
            vid,
            thumbnail_url=yt_src.get("thumbnail_url", ""),
            cache_dir=cache_dir,
            fetcher=fetcher,
        )
        if fetched and fetched.is_file():
            post["featured_image"] = str(fetched)
            return str(fetched)
        return None

    if mode == "grab":
        if not bool(getattr(main_window, "current_media_is_video", False)):
            return None
        media_file = getattr(main_window, "audio_file", None)
        if not media_file or not Path(str(media_file)).is_file():
            return None

        st = post.get("start")
        en = post.get("end")
        pos = post.get("frame_pos")
        if pos is None:
            pos = compute_default_segment_frame_pos(
                st,
                en,
                fallback=float(getattr(main_window, "current_position", 0.0) or 0.0),
            )
        else:
            pos = float(pos)
            if st is not None and en is not None and float(en) > float(st):
                pos = max(float(st), min(float(en), pos))
        post["frame_pos"] = float(pos)

        out_path = Path(tempfile.gettempdir()) / f"rtvs_wp_frame_{post_index}_{os.getpid()}.jpg"
        capturer = frame_capturer
        if capturer is None:
            from plugins.wordpress.wp_post_builder import capture_video_frame
            capturer = capture_video_frame
        if capturer(str(media_file), float(pos), str(out_path), timeout=8.0):
            post["featured_image"] = str(out_path)
            if temp_files_out is not None:
                temp_files_out.add(str(out_path))
            return str(out_path)
        return None

    return None


__all__ = [
    "extract_youtube_id_headless",
    "get_youtube_thumbnail_cache_path",
    "get_youtube_source_info",
    "resolve_post_youtube_video_id",
    "resolve_inherited_youtube_embed",
    "compute_default_segment_frame_pos",
    "should_apply_youtube_featured_default",
    "build_youtube_thumbnail_candidates",
    "ensure_youtube_thumbnail_cached",
    "materialize_post_featured_image",
]

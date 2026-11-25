"""Headless WordPress episode lookup, REST parsing, slug/date helpers, and MP3 download."""
from __future__ import annotations

import html
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from prs_shared import (
    INTERNAL_APP_ID,
    QSettings,
    get_app_data_dir,
    safe_filename,
)

MODE_NEW_EPISODE = "new_episode"
MODE_UPDATE_EXISTING = "update_existing"


def extract_slug_or_id_from_url(url_or_id: str) -> Tuple[Optional[int], str]:
    """Parse a WordPress post URL, query URL, numeric ID, or slug into (post_id, slug)."""
    raw = str(url_or_id or "").strip()
    if not raw:
        return None, ""

    if raw.isdigit():
        return int(raw), ""

    if "://" not in raw and "/" not in raw and "?" not in raw:
        return None, raw.strip("/")

    to_parse = raw if "://" in raw else f"https://{raw.lstrip('/')}"
    parsed = urlparse(to_parse)
    qs = parse_qs(parsed.query)

    for qk in ("p", "post", "post_id"):
        vals = qs.get(qk)
        if vals and str(vals[0]).strip().isdigit():
            return int(str(vals[0]).strip()), ""

    segments = [seg.strip() for seg in parsed.path.split("/") if seg.strip()]
    if segments:
        if len(segments) >= 2 and segments[-2] == "posts" and segments[-1].isdigit():
            return int(segments[-1]), ""
        slug = segments[-1]
        if slug.isdigit() and len(segments) >= 2 and segments[-2] in ("posts", "wp-json"):
            return int(slug), ""
        return None, slug

    return None, ""


def clean_html_to_plain_excerpt(raw_html: str) -> str:
    """Convert WordPress HTML/block content into clean plain text for post excerpts."""
    text = str(raw_html or "")
    if not text.strip():
        return ""

    # Remove block comments and embedded media/player elements before stripping tags
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<(script|style|figure|audio|video|iframe)\b[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[/?(?:ss_player|audio|video|podcast_episode|embed|caption)[^\]]*\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div|li|h[1-6]|blockquote)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)

    lines = [" ".join(ln.split()) for ln in text.splitlines()]
    cleaned_lines = [ln for ln in lines if ln]
    return "\n\n".join(cleaned_lines).strip()


def build_story_slug(title: str) -> str:
    """Build a clean URL-safe WordPress slug from a post title."""
    raw = str(title or "").strip().lower()
    raw = re.sub(r"['’\"`]", "", raw)
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:120].strip("-")


def normalize_wp_iso_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize a user-entered date/time string into WordPress ISO-8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns None when blank so WordPress assigns the current date and time.
    """
    raw = str(date_str or "").strip()
    if not raw or raw.lower() in ("now", "current", "auto"):
        return None

    # Handle ISO strings with timezone suffix (e.g. 2026-04-29T14:00:00Z or +00:00)
    iso_candidate = re.sub(r"(?:Z|[+-]\d{2}:?\d{2})$", "", raw).strip()
    patterns = [
        ("%Y-%m-%dT%H:%M:%S", True),
        ("%Y-%m-%dT%H:%M", True),
        ("%Y-%m-%d %H:%M:%S", True),
        ("%Y-%m-%d %H:%M", True),
        ("%Y-%m-%d", False),
        ("%m/%d/%Y %I:%M %p", True),
        ("%m/%d/%Y %H:%M:%S", True),
        ("%m/%d/%Y %H:%M", True),
        ("%m/%d/%Y", False),
        ("%B %d, %Y", False),
        ("%b %d, %Y", False),
    ]
    for fmt, has_time in patterns:
        try:
            dt = datetime.strptime(iso_candidate, fmt)
            if not has_time:
                dt = dt.replace(hour=9, minute=0, second=0)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue

    raise ValueError(
        f"Invalid publication date '{raw}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM (or leave blank for current time)."
    )


def format_wp_date_for_input(iso_date: Optional[str]) -> str:
    """Format a WordPress ISO-8601 date string for compact UI display (YYYY-MM-DD HH:MM)."""
    raw = str(iso_date or "").strip()
    if not raw:
        return ""
    try:
        normalized = normalize_wp_iso_date(raw)
        if normalized:
            return normalized.replace("T", " ")[:16]
    except ValueError:
        pass
    return raw.replace("T", " ")[:16]


def _extract_audio_url_from_post_payload(post: Dict[str, Any], html_fallback: str = "") -> str:
    """Locate the episode MP3 URL from WordPress REST metadata, enclosures, or rendered HTML."""
    meta = post.get("meta") if isinstance(post.get("meta"), dict) else {}
    for key in ("audio_file", "ss_podcast_audio_file"):
        val = str(meta.get(key) or "").strip()
        if val.startswith(("http://", "https://")):
            return val

    enclosure = str(meta.get("enclosure") or "").strip()
    if enclosure:
        first_line = enclosure.splitlines()[0].strip()
        if first_line.startswith(("http://", "https://")):
            return first_line

    for top_key in ("audio_file", "episode_player_link", "download_link"):
        val = str(post.get(top_key) or "").strip()
        if val.startswith(("http://", "https://")):
            return val

    content_obj = post.get("content") if isinstance(post.get("content"), dict) else {}
    raw_sources = [
        str(content_obj.get("rendered") or ""),
        str(content_obj.get("raw") or ""),
        str(html_fallback or ""),
    ]
    url_patterns = [
        r'<meta[^>]+property=["\']og:audio["\'][^>]+content=["\'](https?://[^"\']+)["\']',
        r'<(?:audio|source)[^>]+src=["\'](https?://[^"\']+)["\']',
        r'data-audio=["\'](https?://[^"\']+)["\']',
        r'(https?://[^\s"\'<>\\]+/podcast-download/\d+/[^\s"\'<>\\]+)',
        r'(https?://[^\s"\'<>\\]+\.mp3(?:\?[^\s"\'<>\\]*)?)',
    ]
    for src in raw_sources:
        if not src:
            continue
        for pat in url_patterns:
            m = re.search(pat, src, re.IGNORECASE)
            if m:
                return html.unescape(m.group(1).strip())
    return ""


def _parse_wp_post_json(post: Dict[str, Any], client: Any = None, fallback_url: str = "") -> Dict[str, Any]:
    """Normalize a WordPress REST post dictionary and extract Option B excerpt & audio URL."""
    title_obj = post.get("title")
    if isinstance(title_obj, dict):
        raw_title = title_obj.get("raw") or title_obj.get("rendered") or ""
    else:
        raw_title = str(title_obj or "")
    title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()

    excerpt_obj = post.get("excerpt")
    raw_excerpt = ""
    rendered_excerpt = ""
    if isinstance(excerpt_obj, dict):
        raw_excerpt = clean_html_to_plain_excerpt(str(excerpt_obj.get("raw") or ""))
        rendered_excerpt = clean_html_to_plain_excerpt(str(excerpt_obj.get("rendered") or ""))
    elif isinstance(excerpt_obj, str):
        raw_excerpt = clean_html_to_plain_excerpt(excerpt_obj)

    content_obj = post.get("content")
    raw_content = ""
    if isinstance(content_obj, dict):
        raw_content = str(content_obj.get("raw") or content_obj.get("rendered") or "")
    elif isinstance(content_obj, str):
        raw_content = content_obj
    content_text = clean_html_to_plain_excerpt(raw_content)

    # Option B: preserve explicit raw excerpt if set; otherwise promote existing body text to Excerpt
    resolved_excerpt = raw_excerpt or content_text or rendered_excerpt

    def _to_int_list(raw_vals: Any) -> List[int]:
        out: List[int] = []
        for raw_v in (raw_vals or []):
            try:
                iv = int(raw_v)
                if iv > 0:
                    out.append(iv)
            except (TypeError, ValueError):
                pass
        return out

    auth_ids = _to_int_list([post.get("author")] if post.get("author") else [])
    author_term_ids = _to_int_list(post.get("ppma_author") or post.get("author_term_ids"))
    category_ids = _to_int_list(post.get("categories"))

    audio_url = _extract_audio_url_from_post_payload(post)
    post_link = str(post.get("link") or fallback_url or "").strip()
    if not audio_url and post_link.startswith(("http://", "https://")) and client is not None and hasattr(client, "_get_request"):
        try:
            page_resp = client._get_request(post_link, timeout=12)
            if getattr(page_resp, "status_code", 0) == 200 and getattr(page_resp, "text", ""):
                audio_url = _extract_audio_url_from_post_payload(post, html_fallback=page_resp.text)
        except Exception:
            pass

    iso_date = str(post.get("date") or "").strip()
    featured_media = None
    try:
        fm_val = int(post.get("featured_media") or 0)
        if fm_val > 0:
            featured_media = fm_val
    except (TypeError, ValueError):
        pass

    return {
        "id": int(post["id"]),
        "url": post_link,
        "slug": str(post.get("slug") or "").strip(),
        "status": str(post.get("status") or "publish").strip(),
        "date": iso_date,
        "date_display": format_wp_date_for_input(iso_date),
        "title": title,
        "raw_excerpt": raw_excerpt,
        "content_text": content_text,
        "excerpt": resolved_excerpt,
        "author_ids": auth_ids,
        "author_term_ids": author_term_ids,
        "category_ids": category_ids,
        "featured_media_id": featured_media,
        "audio_url": audio_url,
    }


def resolve_wp_post_from_url(client: Any, url_or_id: str) -> Dict[str, Any]:
    """Fetch an existing WordPress post by URL, slug, or ID via the WordPress REST API."""
    if not client:
        raise RuntimeError("WordPress client is not configured.")

    post_id, slug = extract_slug_or_id_from_url(url_or_id)
    if post_id is None and not slug:
        raise ValueError("Please enter a valid WordPress post URL, slug, or numeric post ID.")

    api_base = getattr(client, "api_base", "").rstrip("/")
    post_json: Optional[Dict[str, Any]] = None
    last_status = 0
    last_err = ""

    if post_id is not None:
        for url, params in (
            (f"{api_base}/posts/{post_id}", {"context": "edit"}),
            (f"{api_base}/posts/{post_id}", None),
            (f"{api_base}/podcast/{post_id}", {"context": "edit"}),
            (f"{api_base}/podcast/{post_id}", None),
        ):
            try:
                resp = client._get_request(url, params=params, timeout=15)
                last_status = getattr(resp, "status_code", 0)
                if last_status == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("id"):
                        post_json = data
                        break
                last_err = str(getattr(resp, "text", ""))[:200]
            except Exception as exc:
                last_err = str(exc)
    else:
        for post_type in ("posts", "podcast"):
            for params in (
                {"slug": slug, "status": "publish,draft,future,private,pending", "context": "edit"},
                {"slug": slug, "status": "any"},
                {"slug": slug},
            ):
                try:
                    resp = client._get_request(f"{api_base}/{post_type}", params=params, timeout=15)
                    last_status = getattr(resp, "status_code", 0)
                    if last_status == 200:
                        data = resp.json()
                        if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("id"):
                            post_json = data[0]
                            break
                    else:
                        last_err = str(getattr(resp, "text", ""))[:200]
                except Exception as exc:
                    last_err = str(exc)
            if post_json:
                break

    if not post_json:
        target_desc = f"post #{post_id}" if post_id is not None else f"slug '{slug}'"
        detail = f" (HTTP {last_status}: {last_err})" if last_status or last_err else ""
        raise RuntimeError(f"Could not find WordPress post for {target_desc}{detail}.")

    return _parse_wp_post_json(post_json, client=client, fallback_url=url_or_id)


def _resolve_download_dir(main_window: Any = None, target_dir: Optional[Path] = None) -> Path:
    """Choose a writable directory for downloaded WordPress episode audio files."""
    if target_dir is not None:
        out = Path(target_dir)
        out.mkdir(parents=True, exist_ok=True)
        return out

    try:
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        default_proj = str(settings.value("default_project_dir", "") or "").strip()
        if default_proj:
            candidate = Path(default_proj) / "WordPress_Episodes"
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    except Exception:
        pass

    try:
        app_dir = get_app_data_dir() / "wordpress_episodes"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    except Exception:
        tmp = Path(tempfile.gettempdir()) / "rtvs_wordpress_episodes"
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp


def download_wp_episode_audio(
    post_info: Dict[str, Any],
    main_window: Any = None,
    target_dir: Optional[Path] = None,
) -> Path:
    """Download the MP3 file associated with an existing WordPress episode post."""
    import requests

    audio_url = str(post_info.get("audio_url") or "").strip()
    if not audio_url:
        raise RuntimeError(
            "No MP3 audio URL was found on this WordPress episode. "
            "Make sure Seriously Simple Podcasting has an audio file assigned, or open a local MP3 file instead."
        )

    out_dir = _resolve_download_dir(main_window=main_window, target_dir=target_dir)
    base = safe_filename(post_info.get("slug") or post_info.get("title") or f"episode_{post_info.get('id', 'audio')}")
    ext = Path(urlparse(audio_url).path).suffix.lower()
    if ext not in (".mp3", ".wav", ".m4a", ".ogg"):
        ext = ".mp3"
    dest_path = out_dir / f"{base}{ext}"

    resp = requests.get(audio_url, stream=True, timeout=60, allow_redirects=True)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to download episode audio from {audio_url} (HTTP {resp.status_code}).")

    tmp_path = dest_path.with_suffix(f"{ext}.part")
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    os.replace(tmp_path, dest_path)
    return dest_path


def _copy_fetched_post_fields(target: Dict[str, Any], post_info: Dict[str, Any]) -> None:
    """Apply normalized WordPress post metadata onto a post item or project wp_meta dict."""
    target.update({
        "existing_post_id": post_info["id"],
        "existing_post_url": post_info["url"],
        "existing_post_slug": post_info["slug"],
        "existing_post_status": post_info["status"],
        "existing_post_date": post_info["date_display"],
        "replace_existing_audio": False,
    })
    if post_info.get("title"):
        target["title"] = post_info["title"]
    if post_info.get("excerpt"):
        target["excerpt"] = post_info["excerpt"]
        target["excerpt_from_existing"] = True
    for list_k in ("author_ids", "author_term_ids", "category_ids"):
        if post_info.get(list_k):
            target[list_k] = list(post_info[list_k])


def _populate_project_from_fetched_post(main_window: Any, post_info: Dict[str, Any]) -> None:
    """Store fetched WordPress post details into main_window.project_metadata for Update mode."""
    if not main_window:
        return
    proj_meta = getattr(main_window, "project_metadata", None)
    if not isinstance(proj_meta, dict):
        from prs_shared import ProjectMetadataDict
        proj_meta = ProjectMetadataDict()
        main_window.project_metadata = proj_meta

    wp_meta = proj_meta.setdefault("wordpress", {})
    _copy_fetched_post_fields(wp_meta, post_info)
    wp_meta["export_mode"] = MODE_UPDATE_EXISTING
    wp_meta["publication_date"] = post_info["date_display"]
    wp_meta["full_episode_status"] = post_info["status"] or "publish"
    wp_meta["story_status"] = wp_meta.get("story_status") or "draft"
    if post_info.get("title"):
        proj_meta["title"] = post_info["title"]
    if post_info.get("excerpt"):
        proj_meta["excerpt"] = post_info["excerpt"]
    wp_meta["parent_episode"] = {
        "id": post_info["id"],
        "title": post_info.get("title") or "Full Episode",
        "link": post_info.get("url"),
    }


__all__ = [
    "MODE_NEW_EPISODE",
    "MODE_UPDATE_EXISTING",
    "extract_slug_or_id_from_url",
    "clean_html_to_plain_excerpt",
    "build_story_slug",
    "normalize_wp_iso_date",
    "format_wp_date_for_input",
    "resolve_wp_post_from_url",
    "download_wp_episode_audio",
]

"""Post item builder, transcript slicing, and video frame extraction for WordPress export."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from prs_shared import ffmpeg_path
from plugins.wordpress.client import generate_wp_excerpt


def capture_video_frame(video_path: str, timestamp: float, output_path: str, timeout: float = 10.0) -> bool:
    """Capture a single frame from video at timestamp using ffmpeg."""
    ff = ffmpeg_path() or "ffmpeg"
    cmd = [
        ff, "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{max(0.0, timestamp):.3f}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            creationflags=flags,
        )
        return res.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def get_primary_text_slice(main_window: Any, primary_lang: str, st_start: Optional[float], st_end: Optional[float] = None) -> str:
    """Extract transcript or translated text for the specified time slice."""
    src_code = main_window.source_language_code() if hasattr(main_window, "source_language_code") else "en"
    trans_dict = getattr(main_window, "translations", {}) if isinstance(getattr(main_window, "translations", None), dict) else {}
    has_es_en = bool(trans_dict.get("es-en") or trans_dict.get("es_en"))
    has_en_es = bool(trans_dict.get("en-es") or trans_dict.get("en_es"))
    source_is_es = (has_es_en and not has_en_es) or (src_code == "es")

    if primary_lang == "en" and source_is_es:
        en_item = trans_dict.get("es-en") or trans_dict.get("es_en")
        if isinstance(en_item, dict):
            segs = en_item.get("segments", [])
            st_val = float(st_start) if st_start is not None else 0.0
            et_val = float(st_end) if st_end is not None else float("inf")
            parts = [s.get("text", "").strip() for s in segs if float(s.get("end", 0.0)) > st_val and float(s.get("start", 0.0)) < et_val and s.get("text")]
            if parts:
                return " ".join(parts)
    elif primary_lang == "es" and not source_is_es:
        es_item = trans_dict.get("en-es") or trans_dict.get("en_es")
        if isinstance(es_item, dict):
            segs = es_item.get("segments", [])
            st_val = float(st_start) if st_start is not None else 0.0
            et_val = float(st_end) if st_end is not None else float("inf")
            parts = [s.get("text", "").strip() for s in segs if float(s.get("end", 0.0)) > st_val and float(s.get("start", 0.0)) < et_val and s.get("text")]
            if parts:
                return " ".join(parts)

    if hasattr(main_window, "_get_transcript_text_slice"):
        return main_window._get_transcript_text_slice(st_start, st_end)
    return ""


def build_wp_post_items(
    main_window: Any,
    scope: str,
    primary_lang: str = "en",
    existing_items: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Build the list of WordPress post definitions according to the export scope."""
    audio_file = getattr(main_window, "audio_file", None)
    base_name = Path(audio_file).stem if audio_file else "Draft Story"
    stories = getattr(main_window, "stories", []) or []

    existing_by_start: Dict[Any, Dict[str, Any]] = {}
    for old_item in (existing_items or []):
        st_key = old_item.get("start")
        task_lbl = old_item.get("task_label", "")
        existing_by_start[(task_lbl, st_key)] = old_item
        if st_key is not None:
            existing_by_start[st_key] = old_item
        if task_lbl == "Full Episode" or st_key is None:
            existing_by_start["full"] = old_item

    new_items: List[Dict[str, Any]] = []

    def build_story_item(idx: int, st: Any) -> Dict[str, Any]:
        st_title = st.title if getattr(st, "title", None) else f"{base_name} - Story {idx + 1}"
        raw_text = get_primary_text_slice(main_window, primary_lang, getattr(st, "start", 0.0), getattr(st, "end", None))
        default_excerpt = generate_wp_excerpt(raw_text, 55)
        wp_meta = getattr(st, "metadata", {}).get("wordpress", {}) if getattr(st, "metadata", None) else {}

        item: Dict[str, Any] = {
            "task_label": f"Story {idx + 1}" + (f": {st.title}" if getattr(st, "title", None) else ""),
            "title": wp_meta.get("title") or st_title,
            "excerpt": wp_meta.get("excerpt") or default_excerpt,
            "start": getattr(st, "start", None),
            "end": getattr(st, "end", None),
            "story_index": idx,
            "fade_in": float(getattr(st, "fade_in", 0.0) or 0.0),
            "fade_out": float(getattr(st, "fade_out", 0.0) or 0.0),
            "fade_curve": str(getattr(st, "fade_curve", "linear") or "linear"),
            "frame_pos": float(wp_meta.get("frame_pos") if wp_meta.get("frame_pos") is not None else (getattr(st, "start", 0.0) or (getattr(main_window, "current_position", 0.0) or 0.0))),
            "author_ids": list(wp_meta.get("author_ids") or []),
            "author_term_ids": list(wp_meta.get("author_term_ids") or []),
            "category_ids": list(wp_meta.get("category_ids") or []),
            "status": wp_meta.get("status", "draft"),
            "tags": list(wp_meta.get("tags") or []),
            "featured_image": wp_meta.get("featured_image", None),
            "featured_image_mode": wp_meta.get("featured_image_mode", "none"),
        }
        existing = existing_by_start.get((item["task_label"], item["start"])) or existing_by_start.get(item["start"])
        if existing:
            item["title"] = existing.get("title") or item["title"]
            item["excerpt"] = existing.get("excerpt") or item["excerpt"]
            item["author_ids"] = list(existing.get("author_ids", item["author_ids"]))
            item["author_term_ids"] = list(existing.get("author_term_ids", item["author_term_ids"]))
            item["category_ids"] = list(existing.get("category_ids", item["category_ids"]))
            item["featured_image"] = existing.get("featured_image", item["featured_image"])
            item["featured_image_mode"] = existing.get("featured_image_mode", item["featured_image_mode"])
            item["frame_pos"] = existing.get("frame_pos", item["frame_pos"])
            item["story_index"] = idx
            if "fade_in" in existing and existing["fade_in"] is not None:
                item["fade_in"] = float(existing["fade_in"])
            if "fade_out" in existing and existing["fade_out"] is not None:
                item["fade_out"] = float(existing["fade_out"])
            if "fade_curve" in existing and existing["fade_curve"]:
                item["fade_curve"] = str(existing["fade_curve"])
        return item

    def build_full_item() -> Dict[str, Any]:
        raw_text = main_window._get_transcript_text_slice(0.0, None) if hasattr(main_window, "_get_transcript_text_slice") else ""
        default_excerpt = generate_wp_excerpt(raw_text, 55)
        proj_meta = getattr(main_window, "project_metadata", {}) or {}
        wp_meta = proj_meta.get("wordpress", {}) if isinstance(proj_meta, dict) else {}
        item: Dict[str, Any] = {
            "task_label": "Full Episode",
            "title": wp_meta.get("title") or base_name,
            "excerpt": wp_meta.get("excerpt") or default_excerpt,
            "start": None,
            "end": None,
            "story_index": None,
            "fade_in": 0.0,
            "fade_out": 0.0,
            "fade_curve": "linear",
            "frame_pos": float(wp_meta.get("frame_pos") if wp_meta.get("frame_pos") is not None else (getattr(main_window, "current_position", 0.0) or 0.0)),
            "author_ids": list(wp_meta.get("author_ids") or []),
            "author_term_ids": list(wp_meta.get("author_term_ids") or []),
            "category_ids": list(wp_meta.get("category_ids") or []),
            "status": wp_meta.get("status", "draft"),
            "tags": list(wp_meta.get("tags") or []),
            "featured_image": wp_meta.get("featured_image", None),
            "featured_image_mode": wp_meta.get("featured_image_mode", "none"),
        }
        existing = existing_by_start.get("full")
        if existing:
            item["title"] = existing.get("title") or item["title"]
            item["excerpt"] = existing.get("excerpt") or item["excerpt"]
            item["author_ids"] = list(existing.get("author_ids", item["author_ids"]))
            item["author_term_ids"] = list(existing.get("author_term_ids", item["author_term_ids"]))
            item["category_ids"] = list(existing.get("category_ids", item["category_ids"]))
            item["featured_image"] = existing.get("featured_image", item["featured_image"])
            item["featured_image_mode"] = existing.get("featured_image_mode", item["featured_image_mode"])
            item["frame_pos"] = existing.get("frame_pos", item["frame_pos"])
        return item

    if scope == "full":
        new_items.append(build_full_item())
    elif scope == "selected_stories":
        indices = getattr(main_window, "current_selected_story_indices", []) or []
        if not indices and stories:
            indices = [0]
        for idx in indices:
            if 0 <= idx < len(stories):
                new_items.append(build_story_item(idx, stories[idx]))
    elif scope == "all_stories":
        for idx, st in enumerate(stories):
            new_items.append(build_story_item(idx, st))
    elif scope == "full_and_all_stories":
        new_items.append(build_full_item())
        for idx, st in enumerate(stories):
            new_items.append(build_story_item(idx, st))

    if not new_items:
        new_items.append({
            "task_label": "Draft Story",
            "title": base_name,
            "excerpt": "",
            "start": None,
            "end": None,
            "frame_pos": float(getattr(main_window, "current_position", 0.0) or 0.0),
            "author_ids": [],
            "author_term_ids": [],
            "category_ids": [],
            "featured_image": None,
            "featured_image_mode": "none",
        })

    return new_items

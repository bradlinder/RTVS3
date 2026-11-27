"""Post item builder, transcript slicing, and video frame extraction for WordPress export."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from prs_shared import ffmpeg_path
from plugins.wordpress.client import generate_wp_excerpt
from plugins.wordpress.wp_thumbnail_defaults import (
    compute_default_segment_frame_pos,
    get_youtube_source_info,
    resolve_inherited_youtube_embed,
    should_apply_youtube_featured_default,
)


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
    include_full_episode: bool = False,
) -> List[Dict[str, Any]]:
    """Build the list of WordPress post definitions according to the export scope."""
    audio_file = getattr(main_window, "audio_file", None)
    base_name = Path(audio_file).stem if audio_file else "Draft Story"
    stories = getattr(main_window, "stories", []) or []
    is_video = bool(getattr(main_window, "current_media_is_video", False))
    yt_src = get_youtube_source_info(main_window)

    existing_by_start: Dict[Any, Dict[str, Any]] = {}
    for old_item in (existing_items or []):
        st_key = old_item.get("start")
        task_lbl = old_item.get("task_label", "")
        existing_by_start[(task_lbl, st_key)] = old_item
        clean_lbl = task_lbl.split(":", 1)[0].strip() if ":" in task_lbl and task_lbl.lower().startswith("story ") else task_lbl
        existing_by_start[(clean_lbl, st_key)] = old_item
        if st_key is not None:
            existing_by_start[st_key] = old_item
        if task_lbl == "Full Episode" or st_key is None:
            existing_by_start["full"] = old_item

    new_items: List[Dict[str, Any]] = []

    def build_story_item(idx: int, st: Any) -> Dict[str, Any]:
        st_title = st.title if getattr(st, "title", None) else f"{base_name} - Story {idx + 1}"
        st_start = getattr(st, "start", None)
        st_end = getattr(st, "end", None)
        raw_text = get_primary_text_slice(main_window, primary_lang, st_start if st_start is not None else 0.0, st_end)
        default_excerpt = generate_wp_excerpt(raw_text, 55)
        st_meta = getattr(st, "metadata", {}) if isinstance(getattr(st, "metadata", None), dict) else {}
        wp_meta = st_meta.get("wordpress", {}) if isinstance(st_meta.get("wordpress"), dict) else {}
        season_val = wp_meta.get("podcast_season") if wp_meta.get("podcast_season") is not None else wp_meta.get("season")
        ep_num_val = wp_meta.get("podcast_episode_number") if wp_meta.get("podcast_episode_number") is not None else wp_meta.get("episode_number")

        # Inherit project-level YouTube embed onto individual stories unless explicitly cleared
        yt_explicitly_cleared = bool(wp_meta.get("youtube_explicitly_cleared", False))
        story_yt_url = str(wp_meta.get("youtube_url") or "").strip()
        story_yt_vid = str(wp_meta.get("youtube_video_id") or "").strip()
        inherited_yt = resolve_inherited_youtube_embed(main_window, wp_meta)
        if not story_yt_url and not yt_explicitly_cleared and inherited_yt["youtube_url"]:
            story_yt_url = inherited_yt["youtube_url"]
            story_yt_vid = inherited_yt["youtube_video_id"]
            yt_use_story_time = bool(wp_meta.get("youtube_use_story_time", inherited_yt["youtube_use_story_time"]))
            yt_stop_at_end = bool(wp_meta.get("youtube_stop_at_end", inherited_yt["youtube_stop_at_end"]))
            yt_placement = str(wp_meta.get("youtube_placement") or inherited_yt["youtube_placement"] or "top")
        else:
            yt_use_story_time = bool(wp_meta.get("youtube_use_story_time", True))
            yt_stop_at_end = bool(wp_meta.get("youtube_stop_at_end", False))
            yt_placement = str(wp_meta.get("youtube_placement") or "top")

        # YouTube-source individual segments default to grabbing a video frame inside [st_start, st_end]
        default_frame_pos = compute_default_segment_frame_pos(
            st_start,
            st_end,
            fallback=float(getattr(main_window, "current_position", 0.0) or 0.0),
        )
        feat_user_set = bool(wp_meta.get("featured_image_user_set") or st_meta.get("featured_image_user_set") or False)
        feat_img = wp_meta.get("featured_image") if wp_meta.get("featured_image") is not None else st_meta.get("featured_image")
        feat_mode = str(wp_meta.get("featured_image_mode") or st_meta.get("featured_image_mode") or "none")
        if yt_src["is_youtube_source"] and is_video and should_apply_youtube_featured_default(wp_meta, st_meta):
            feat_mode = "grab"
            feat_img = None
            frame_pos = default_frame_pos
        else:
            frame_pos = float(wp_meta.get("frame_pos") if wp_meta.get("frame_pos") is not None else default_frame_pos)

        item: Dict[str, Any] = {
            "task_label": f"Story {idx + 1}",
            "title": wp_meta.get("title") or st_title,
            "excerpt": wp_meta.get("excerpt") or st_meta.get("excerpt") or default_excerpt,
            "start": st_start,
            "end": st_end,
            "story_index": idx,
            "is_parent_episode": False,
            "fade_in": float(getattr(st, "fade_in", 0.0) or 0.0),
            "fade_out": float(getattr(st, "fade_out", 0.0) or 0.0),
            "fade_curve": str(getattr(st, "fade_curve", "linear") or "linear"),
            "frame_pos": frame_pos,
            "author_ids": list(wp_meta.get("author_ids") or []),
            "author_term_ids": list(wp_meta.get("author_term_ids") or []),
            "category_ids": list(wp_meta.get("category_ids") or []),
            "status": wp_meta.get("status", "draft"),
            "slug": wp_meta.get("slug", ""),
            "tags": list(wp_meta.get("tags") or st_meta.get("tags") or []),
            "featured_image": feat_img,
            "featured_image_mode": feat_mode,
            "featured_image_user_set": feat_user_set,
            "featured_image_caption": str(wp_meta.get("featured_image_caption") if wp_meta.get("featured_image_caption") is not None else (st_meta.get("featured_image_caption") or "")),
            "featured_image_alt_text": str(wp_meta.get("featured_image_alt_text") if wp_meta.get("featured_image_alt_text") is not None else (st_meta.get("featured_image_alt_text") or "")),
            "is_podcast": bool(wp_meta.get("is_podcast", False)),
            "podcast_feed": str(wp_meta.get("podcast_feed") or "default"),
            "podcast_feed_id": wp_meta.get("podcast_feed_id"),
            "podcast_feed_ids": list(wp_meta.get("podcast_feed_ids") or ([int(wp_meta.get("podcast_feed_id"))] if wp_meta.get("podcast_feed_id") else [])),
            "podcast_feeds": list(wp_meta.get("podcast_feeds") or ([str(wp_meta.get("podcast_feed"))] if wp_meta.get("podcast_feed") else [])),
            "podcast_episode_type": str(wp_meta.get("podcast_episode_type") or "full"),
            "podcast_season": season_val,
            "season": season_val,
            "podcast_episode_number": ep_num_val,
            "episode_number": ep_num_val,
            "youtube_url": story_yt_url,
            "youtube_video_id": story_yt_vid,
            "youtube_explicitly_cleared": yt_explicitly_cleared,
            "youtube_use_story_time": yt_use_story_time,
            "youtube_stop_at_end": yt_stop_at_end,
            "youtube_placement": yt_placement,
            "existing_post_url": str(wp_meta.get("existing_post_url") or ""),
            "existing_post_id": wp_meta.get("existing_post_id"),
            "existing_post_slug": str(wp_meta.get("existing_post_slug") or ""),
            "existing_post_status": str(wp_meta.get("existing_post_status") or ""),
            "existing_post_date": str(wp_meta.get("existing_post_date") or ""),
            "replace_existing_audio": bool(wp_meta.get("replace_existing_audio", False)),
            "excerpt_from_existing": bool(wp_meta.get("excerpt_from_existing", False)),
        }
        existing = existing_by_start.get((item["task_label"], item["start"])) or existing_by_start.get(item["start"])
        if existing:
            item["title"] = existing.get("title") or item["title"]
            item["excerpt"] = existing.get("excerpt") or item["excerpt"]
            item["author_ids"] = list(existing.get("author_ids", item["author_ids"]))
            item["author_term_ids"] = list(existing.get("author_term_ids", item["author_term_ids"]))
            item["category_ids"] = list(existing.get("category_ids", item["category_ids"]))
            ex_feat_mode = existing.get("featured_image_mode")
            ex_feat_user_set = bool(existing.get("featured_image_user_set", False))
            if ex_feat_user_set or ex_feat_mode in ("grab", "file", "youtube") or item["featured_image_mode"] == "none":
                item["featured_image"] = existing.get("featured_image", item["featured_image"])
                item["featured_image_mode"] = ex_feat_mode if ex_feat_mode is not None else item["featured_image_mode"]
                item["featured_image_user_set"] = ex_feat_user_set
                item["frame_pos"] = existing.get("frame_pos", item["frame_pos"])
            if "featured_image_caption" in existing:
                item["featured_image_caption"] = str(existing.get("featured_image_caption") or "")
            if "featured_image_alt_text" in existing:
                item["featured_image_alt_text"] = str(existing.get("featured_image_alt_text") or "")
            item["story_index"] = idx
            if "fade_in" in existing and existing["fade_in"] is not None:
                item["fade_in"] = float(existing["fade_in"])
            if "fade_out" in existing and existing["fade_out"] is not None:
                item["fade_out"] = float(existing["fade_out"])
            if "fade_curve" in existing and existing["fade_curve"]:
                item["fade_curve"] = str(existing["fade_curve"])
            if "is_podcast" in existing:
                item["is_podcast"] = bool(existing["is_podcast"])
            if "podcast_feed" in existing:
                item["podcast_feed"] = existing["podcast_feed"]
            if "podcast_feed_id" in existing:
                item["podcast_feed_id"] = existing["podcast_feed_id"]
            if "podcast_feed_ids" in existing:
                item["podcast_feed_ids"] = list(existing["podcast_feed_ids"] or [])
            if "podcast_feeds" in existing:
                item["podcast_feeds"] = list(existing["podcast_feeds"] or [])
            if "podcast_episode_type" in existing:
                item["podcast_episode_type"] = existing["podcast_episode_type"]
            if "podcast_season" in existing or "season" in existing:
                s_ex = existing.get("podcast_season") if existing.get("podcast_season") is not None else existing.get("season")
                item["podcast_season"] = s_ex
                item["season"] = s_ex
            if "podcast_episode_number" in existing or "episode_number" in existing:
                ep_ex = existing.get("podcast_episode_number") if existing.get("podcast_episode_number") is not None else existing.get("episode_number")
                item["podcast_episode_number"] = ep_ex
                item["episode_number"] = ep_ex
            ex_yt_cleared = bool(existing.get("youtube_explicitly_cleared", False))
            if existing.get("youtube_url") or ex_yt_cleared:
                item["youtube_url"] = str(existing.get("youtube_url") or "")
                item["youtube_video_id"] = str(existing.get("youtube_video_id") or "")
                item["youtube_explicitly_cleared"] = ex_yt_cleared
            if "youtube_use_story_time" in existing:
                item["youtube_use_story_time"] = bool(existing.get("youtube_use_story_time", True))
            if "youtube_stop_at_end" in existing:
                item["youtube_stop_at_end"] = bool(existing.get("youtube_stop_at_end", False))
            if "youtube_placement" in existing:
                item["youtube_placement"] = str(existing.get("youtube_placement") or "top")
            for k in ("existing_post_url", "existing_post_id", "existing_post_slug", "existing_post_status", "existing_post_date", "replace_existing_audio", "excerpt_from_existing"):
                if k in existing:
                    item[k] = existing[k]
        return item

    def build_full_item() -> Dict[str, Any]:
        raw_text = main_window._get_transcript_text_slice(0.0, None) if hasattr(main_window, "_get_transcript_text_slice") else ""
        default_excerpt = generate_wp_excerpt(raw_text, 55)
        proj_meta = getattr(main_window, "project_metadata", {}) or {}
        if not isinstance(proj_meta, dict):
            proj_meta = {}
        wp_meta = proj_meta.get("wordpress", {}) if isinstance(proj_meta.get("wordpress"), dict) else {}
        season_val = wp_meta.get("podcast_season") if wp_meta.get("podcast_season") is not None else wp_meta.get("season")
        ep_num_val = wp_meta.get("podcast_episode_number") if wp_meta.get("podcast_episode_number") is not None else wp_meta.get("episode_number")
        default_is_podcast = False if is_video else True

        yt_explicitly_cleared = bool(wp_meta.get("youtube_explicitly_cleared", False))
        full_yt_url = str(wp_meta.get("youtube_url") or "").strip()
        full_yt_vid = str(wp_meta.get("youtube_video_id") or "").strip()
        if not full_yt_url and not yt_explicitly_cleared and yt_src["is_youtube_source"] and yt_src["source_url"]:
            full_yt_url = yt_src["source_url"]
            full_yt_vid = yt_src["video_id"]

        # YouTube-source Full Episode defaults to the YouTube page's default thumbnail
        feat_user_set = bool(wp_meta.get("featured_image_user_set") or proj_meta.get("featured_image_user_set") or False)
        feat_img = wp_meta.get("featured_image") if wp_meta.get("featured_image") is not None else proj_meta.get("featured_image")
        feat_mode = str(wp_meta.get("featured_image_mode") or proj_meta.get("featured_image_mode") or "none")
        if yt_src["is_youtube_source"] and yt_src["video_id"] and should_apply_youtube_featured_default(wp_meta, proj_meta):
            feat_mode = "youtube"
            feat_img = yt_src["thumbnail_path"] or None

        item: Dict[str, Any] = {
            "task_label": "Full Episode",
            "title": wp_meta.get("title") or proj_meta.get("title") or base_name,
            "excerpt": wp_meta.get("excerpt") or proj_meta.get("excerpt") or default_excerpt,
            "start": None,
            "end": None,
            "story_index": None,
            "is_parent_episode": True,
            "fade_in": 0.0,
            "fade_out": 0.0,
            "fade_curve": "linear",
            "frame_pos": float(wp_meta.get("frame_pos") if wp_meta.get("frame_pos") is not None else (getattr(main_window, "current_position", 0.0) or 0.0)),
            "author_ids": list(wp_meta.get("author_ids") or []),
            "author_term_ids": list(wp_meta.get("author_term_ids") or []),
            "category_ids": list(wp_meta.get("category_ids") or []),
            "status": wp_meta.get("status", "draft"),
            "slug": wp_meta.get("slug", ""),
            "tags": list(wp_meta.get("tags") or proj_meta.get("tags") or []),
            "featured_image": feat_img,
            "featured_image_mode": feat_mode,
            "featured_image_user_set": feat_user_set,
            "featured_image_caption": str(wp_meta.get("featured_image_caption") if wp_meta.get("featured_image_caption") is not None else (proj_meta.get("featured_image_caption") or "")),
            "featured_image_alt_text": str(wp_meta.get("featured_image_alt_text") if wp_meta.get("featured_image_alt_text") is not None else (proj_meta.get("featured_image_alt_text") or "")),
            "is_podcast": bool(wp_meta.get("is_podcast", default_is_podcast)),
            "podcast_feed": str(wp_meta.get("podcast_feed") or "default"),
            "podcast_feed_id": wp_meta.get("podcast_feed_id"),
            "podcast_feed_ids": list(wp_meta.get("podcast_feed_ids") or ([int(wp_meta.get("podcast_feed_id"))] if wp_meta.get("podcast_feed_id") else [])),
            "podcast_feeds": list(wp_meta.get("podcast_feeds") or ([str(wp_meta.get("podcast_feed"))] if wp_meta.get("podcast_feed") else [])),
            "podcast_episode_type": str(wp_meta.get("podcast_episode_type") or "full"),
            "podcast_season": season_val,
            "season": season_val,
            "podcast_episode_number": ep_num_val,
            "episode_number": ep_num_val,
            "youtube_url": full_yt_url,
            "youtube_video_id": full_yt_vid,
            "youtube_explicitly_cleared": yt_explicitly_cleared,
            "youtube_use_story_time": bool(wp_meta.get("youtube_use_story_time", True)),
            "youtube_stop_at_end": bool(wp_meta.get("youtube_stop_at_end", False)),
            "youtube_placement": str(wp_meta.get("youtube_placement") or "top"),
            "existing_post_url": str(wp_meta.get("existing_post_url") or ""),
            "existing_post_id": wp_meta.get("existing_post_id"),
            "existing_post_slug": str(wp_meta.get("existing_post_slug") or ""),
            "existing_post_status": str(wp_meta.get("existing_post_status") or ""),
            "existing_post_date": str(wp_meta.get("existing_post_date") or ""),
            "replace_existing_audio": bool(wp_meta.get("replace_existing_audio", False)),
            "excerpt_from_existing": bool(wp_meta.get("excerpt_from_existing", False)),
        }
        existing = existing_by_start.get("full")
        is_full_existing = bool(existing and (existing.get("task_label") == "Full Episode" or existing.get("start") is None))
        if not existing and existing_items and len(existing_items) == 1:
            existing = existing_items[0]
            is_full_existing = bool(existing.get("task_label") == "Full Episode" or existing.get("start") is None)
        if existing:
            # Only copy title, excerpt, podcast, YouTube, and featured image settings if the existing item
            # was actually a Full Episode post; never overwrite Full Episode with child story properties!
            if is_full_existing:
                item["title"] = existing.get("title") or item["title"]
                item["excerpt"] = existing.get("excerpt") or item["excerpt"]
                if "is_podcast" in existing:
                    item["is_podcast"] = bool(existing["is_podcast"])
                if "podcast_feed" in existing:
                    item["podcast_feed"] = existing["podcast_feed"]
                if "podcast_feed_id" in existing:
                    item["podcast_feed_id"] = existing["podcast_feed_id"]
                if "podcast_feed_ids" in existing:
                    item["podcast_feed_ids"] = list(existing["podcast_feed_ids"] or [])
                if "podcast_feeds" in existing:
                    item["podcast_feeds"] = list(existing["podcast_feeds"] or [])
                if "podcast_episode_type" in existing:
                    item["podcast_episode_type"] = existing["podcast_episode_type"]
                if "podcast_season" in existing or "season" in existing:
                    s_ex = existing.get("podcast_season") if existing.get("podcast_season") is not None else existing.get("season")
                    item["podcast_season"] = s_ex
                    item["season"] = s_ex
                if "podcast_episode_number" in existing or "episode_number" in existing:
                    ep_ex = existing.get("podcast_episode_number") if existing.get("podcast_episode_number") is not None else existing.get("episode_number")
                    item["podcast_episode_number"] = ep_ex
                    item["episode_number"] = ep_ex
                ex_yt_cleared = bool(existing.get("youtube_explicitly_cleared", False))
                if existing.get("youtube_url") or ex_yt_cleared:
                    item["youtube_url"] = str(existing.get("youtube_url") or "")
                    item["youtube_video_id"] = str(existing.get("youtube_video_id") or "")
                    item["youtube_explicitly_cleared"] = ex_yt_cleared
                if "youtube_use_story_time" in existing:
                    item["youtube_use_story_time"] = bool(existing.get("youtube_use_story_time", True))
                if "youtube_stop_at_end" in existing:
                    item["youtube_stop_at_end"] = bool(existing.get("youtube_stop_at_end", False))
                if "youtube_placement" in existing:
                    item["youtube_placement"] = str(existing.get("youtube_placement") or "top")
                for k in ("existing_post_url", "existing_post_id", "existing_post_slug", "existing_post_status", "existing_post_date", "replace_existing_audio", "excerpt_from_existing"):
                    if k in existing:
                        item[k] = existing[k]
                ex_feat_mode = existing.get("featured_image_mode")
                ex_feat_user_set = bool(existing.get("featured_image_user_set", False))
                if ex_feat_user_set or ex_feat_mode in ("grab", "file", "youtube") or item["featured_image_mode"] == "none":
                    item["featured_image"] = existing.get("featured_image", item["featured_image"])
                    item["featured_image_mode"] = ex_feat_mode if ex_feat_mode is not None else item["featured_image_mode"]
                    item["featured_image_user_set"] = ex_feat_user_set
                    item["frame_pos"] = existing.get("frame_pos", item["frame_pos"])
                if "featured_image_caption" in existing:
                    item["featured_image_caption"] = str(existing.get("featured_image_caption") or "")
                if "featured_image_alt_text" in existing:
                    item["featured_image_alt_text"] = str(existing.get("featured_image_alt_text") or "")
            item["author_ids"] = list(existing.get("author_ids", item["author_ids"]))
            item["author_term_ids"] = list(existing.get("author_term_ids", item["author_term_ids"]))
            item["category_ids"] = list(existing.get("category_ids", item["category_ids"]))
        return item

    if scope == "full":
        new_items.append(build_full_item())
    elif scope == "selected_stories":
        if include_full_episode:
            new_items.append(build_full_item())
        indices = getattr(main_window, "current_selected_story_indices", []) or []
        if not indices and stories and not include_full_episode:
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
            "featured_image_caption": "",
            "featured_image_alt_text": "",
            "is_podcast": False,
            "podcast_feed": "default",
            "podcast_feed_id": None,
            "podcast_episode_type": "full",
            "podcast_season": None,
            "podcast_episode_number": None,
        })

    return new_items


def sync_featured_image_meta(
    wp_meta: Dict[str, Any],
    post: Dict[str, Any],
    container_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist featured image path, mode, user-set flag, caption, alt text, and frame position."""
    img = post.get("featured_image")
    mode = post.get("featured_image_mode", "none")
    user_set = bool(post.get("featured_image_user_set", False))
    caption = str(post.get("featured_image_caption") or "")
    alt_text = str(post.get("featured_image_alt_text") or "")
    wp_meta["featured_image"] = img
    wp_meta["featured_image_mode"] = mode
    wp_meta["featured_image_user_set"] = user_set
    wp_meta["featured_image_caption"] = caption
    wp_meta["featured_image_alt_text"] = alt_text
    wp_meta["frame_pos"] = post.get("frame_pos")
    if isinstance(container_meta, dict):
        container_meta["featured_image"] = img
        container_meta["featured_image_mode"] = mode
        container_meta["featured_image_user_set"] = user_set
        container_meta["featured_image_caption"] = caption
        container_meta["featured_image_alt_text"] = alt_text

"""YouTube Video Embed helpers, Gutenberg iframe generator, and UI setup for WordPress export."""
from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    CollapsibleSection,
    format_time,
)


def extract_youtube_video_id(url_or_id: str) -> Tuple[str, Optional[int]]:
    """Extract the clean 11-character YouTube Video ID and optional start timestamp (seconds).

    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID&t=120
    - https://youtu.be/VIDEO_ID?t=2m5s
    - https://www.youtube.com/embed/VIDEO_ID?start=90
    - https://www.youtube.com/live/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://studio.youtube.com/video/VIDEO_ID/edit
    - Raw 11-char ID: VIDEO_ID
    """
    if not url_or_id:
        return "", None

    raw = str(url_or_id).strip()
    if not raw:
        return "", None

    def _parse_time_param(val: str) -> Optional[int]:
        if not val:
            return None
        val = val.strip().lower()
        if val.endswith("s"):
            val_no_s = val[:-1]
            if "m" in val_no_s:
                parts = val_no_s.split("m")
                try:
                    m = int(parts[0])
                    s = int(parts[1]) if parts[1] else 0
                    return m * 60 + s
                except ValueError:
                    return None
            try:
                return int(val_no_s)
            except ValueError:
                return None
        if "m" in val:
            parts = val.split("m")
            try:
                m = int(parts[0])
                s = int(parts[1].rstrip("s")) if parts[1] else 0
                return m * 60 + s
            except ValueError:
                return None
        if "h" in val:
            match = re.match(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?", val)
            if match:
                h = int(match.group(1) or 0)
                m = int(match.group(2) or 0)
                s = int(match.group(3) or 0)
                return h * 3600 + m * 60 + s
        try:
            return int(float(val))
        except ValueError:
            return None

    parsed_time: Optional[int] = None

    # Check for raw 11-character alphanumeric/dash/underscore string
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", raw):
        return raw, None

    # Attempt standard URL parsing
    url_to_parse = raw if ("://" in raw or raw.startswith("//")) else f"https://{raw}"
    try:
        parsed = urlparse(url_to_parse)
        netloc = parsed.netloc.lower()
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Extract time if present in query params
        t_param = qs.get("t", [None])[0] or qs.get("start", [None])[0]
        if t_param:
            parsed_time = _parse_time_param(t_param)

        # 1. youtube.com/watch?v=ID
        if "youtube.com" in netloc and "/watch" in path:
            v_val = qs.get("v", [None])[0]
            if v_val and re.fullmatch(r"[A-Za-z0-9_-]{11}", v_val):
                return v_val, parsed_time

        # 2. youtu.be/ID
        if "youtu.be" in netloc:
            parts = [p for p in path.strip("/").split("/") if p]
            if parts and re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[0]):
                return parts[0], parsed_time

        # 3. youtube.com/embed/ID, /live/ID, /shorts/ID
        for prefix in ("/embed/", "/live/", "/shorts/"):
            if prefix in path:
                seg = path.split(prefix, 1)[1].split("/")[0].split("?")[0]
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", seg):
                    return seg, parsed_time

        # 4. studio.youtube.com/video/ID/edit
        if "studio.youtube.com" in netloc and "/video/" in path:
            seg = path.split("/video/", 1)[1].split("/")[0].split("?")[0]
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", seg):
                return seg, parsed_time

    except Exception:
        pass

    # Regex fallback for any embedded 11-char ID
    m = re.search(r"(?:v=|\/embed\/|\/live\/|\/shorts\/|youtu\.be\/|\/video\/)([A-Za-z0-9_-]{11})", raw)
    if m:
        vid = m.group(1)
        tm = re.search(r"[?&](?:t|start)=([0-9mh]+s?)", raw)
        if tm:
            parsed_time = _parse_time_param(tm.group(1))
        return vid, parsed_time

    return "", parsed_time


def build_youtube_embed_block(
    video_id: str,
    start_sec: float | int | None = None,
    end_sec: float | int | None = None,
    stop_at_end: bool = False,
) -> str:
    """Generate a responsive Gutenberg HTML embed block for a YouTube video.

    Using a custom HTML iframe block ensures both live and scheduled/private
    videos work seamlessly without relying on WordPress server-side oEmbed resolution.
    Always includes rel=0 to prevent third-party channel video recommendations.
    """
    clean_id, url_t = extract_youtube_video_id(video_id)
    if not clean_id:
        clean_id = str(video_id).strip()

    st_int: Optional[int] = None
    if start_sec is not None and float(start_sec) > 0.0:
        st_int = int(round(float(start_sec)))
    elif url_t is not None and url_t > 0:
        st_int = url_t

    query_params = ["rel=0"]
    if st_int is not None and st_int > 0:
        query_params.append(f"start={st_int}")

    if stop_at_end and end_sec is not None:
        end_int = int(round(float(end_sec)))
        effective_start = st_int or 0
        if end_int > effective_start:
            query_params.append(f"end={end_int}")

    param_str = "&amp;".join(query_params)
    src_url = f"https://www.youtube.com/embed/{clean_id}?{param_str}"

    return (
        '<!-- wp:html -->\n'
        '<div class="rtvs-youtube-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;margin:16px 0;">\n'
        f'  <iframe src="{src_url}" title="YouTube video player" frameborder="0" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        'allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"></iframe>\n'
        '</div>\n'
        '<!-- /wp:html -->'
    )


def setup_wp_youtube_ui(tab_widget: Any, parent_layout: QVBoxLayout) -> None:
    """Construct the 'YouTube Video Embed' CollapsibleSection inside the Media tab."""
    tab_widget.wp_youtube_section = CollapsibleSection("YouTube Video Embed", tab_widget, is_expanded=True)
    yt_layout = QVBoxLayout()
    yt_layout.setContentsMargins(4, 4, 4, 4)
    yt_layout.setSpacing(6)

    desc_lbl = QLabel(
        "Embed a responsive YouTube video player in this post. Paste an existing YouTube link or YouTube Studio link.<br>"
        "Works with scheduled or unlisted videos before they go public."
    )
    desc_lbl.setWordWrap(True)
    desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
    yt_layout.addWidget(desc_lbl)

    # URL input
    tab_widget.wp_yt_url_edit = QLineEdit()
    tab_widget.wp_yt_url_edit.setPlaceholderText("https://youtu.be/... or YouTube Studio link")
    tab_widget.wp_yt_url_edit.textChanged.connect(lambda txt: _on_youtube_url_changed(tab_widget, txt))
    yt_layout.addWidget(tab_widget.wp_yt_url_edit)

    # Status / parsed preview label
    tab_widget.wp_yt_status_label = QLabel("No YouTube video attached.")
    tab_widget.wp_yt_status_label.setWordWrap(True)
    tab_widget.wp_yt_status_label.setStyleSheet("color: #64748b; font-size: 11px;")
    yt_layout.addWidget(tab_widget.wp_yt_status_label)

    # Options checkboxes
    tab_widget.wp_cb_yt_apply_all = QCheckBox("Apply this YouTube URL to the full episode and all stories in this project")
    tab_widget.wp_cb_yt_apply_all.setChecked(True)
    tab_widget.wp_cb_yt_apply_all.setToolTip(
        "When enabled, updating this URL applies it across all stories in this project so each story automatically embeds the same YouTube video at its corresponding story timestamps."
    )
    tab_widget.wp_cb_yt_apply_all.toggled.connect(lambda chk: _on_youtube_apply_all_toggled(tab_widget, chk))
    yt_layout.addWidget(tab_widget.wp_cb_yt_apply_all)

    tab_widget.wp_cb_yt_use_story_time = QCheckBox("Start video at this story's episode timestamp")
    tab_widget.wp_cb_yt_use_story_time.setChecked(True)
    tab_widget.wp_cb_yt_use_story_time.setToolTip(
        "When checked, embeds the video starting at this story's start time in the broadcast. "
        "When unchecked on a custom single-story URL, starts playback at 0:00 (or the explicit timestamp in the URL)."
    )
    tab_widget.wp_cb_yt_use_story_time.toggled.connect(lambda chk: _on_youtube_use_story_time_toggled(tab_widget, chk))
    yt_layout.addWidget(tab_widget.wp_cb_yt_use_story_time)

    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    default_stop_at_end = str(settings.value("wp_yt_stop_at_story_end", "false")).lower() in ("true", "1", "yes")
    tab_widget.wp_cb_yt_stop_at_end = QCheckBox("Stop video playback at the end of each story")
    tab_widget.wp_cb_yt_stop_at_end.setChecked(default_stop_at_end)
    tab_widget.wp_cb_yt_stop_at_end.setToolTip(
        "When checked, appends an end timestamp to the YouTube embed parameter so playback stops when this story concludes."
    )
    tab_widget.wp_cb_yt_stop_at_end.toggled.connect(lambda chk: _on_youtube_stop_at_end_toggled(tab_widget, chk))
    yt_layout.addWidget(tab_widget.wp_cb_yt_stop_at_end)

    # Placement radio buttons
    pos_row = QHBoxLayout()
    pos_lbl = QLabel("Video Placement:")
    pos_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
    tab_widget.wp_yt_pos_label = pos_lbl
    pos_row.addWidget(pos_lbl)

    tab_widget.wp_yt_pos_group = QButtonGroup(tab_widget)
    tab_widget.wp_rad_yt_pos_top = QRadioButton("Place at top of post (above transcript)")
    tab_widget.wp_rad_yt_pos_bottom = QRadioButton("Place at bottom of post (below transcript)")
    tab_widget.wp_yt_pos_group.addButton(tab_widget.wp_rad_yt_pos_top)
    tab_widget.wp_yt_pos_group.addButton(tab_widget.wp_rad_yt_pos_bottom)

    default_pos = str(settings.value("wp_yt_embed_placement", "top")).lower()
    if default_pos == "bottom":
        tab_widget.wp_rad_yt_pos_bottom.setChecked(True)
    else:
        tab_widget.wp_rad_yt_pos_top.setChecked(True)

    tab_widget.wp_rad_yt_pos_top.toggled.connect(lambda chk: _on_youtube_placement_toggled(tab_widget, "top" if chk else "bottom"))
    pos_row.addWidget(tab_widget.wp_rad_yt_pos_top)
    pos_row.addWidget(tab_widget.wp_rad_yt_pos_bottom)
    pos_row.addStretch()
    yt_layout.addLayout(pos_row)

    tab_widget.wp_youtube_section.add_layout(yt_layout)
    parent_layout.addWidget(tab_widget.wp_youtube_section)
    _set_youtube_controls_enabled(tab_widget, False)


def _get_current_post(tab_widget: Any) -> Optional[Dict[str, Any]]:
    if not hasattr(tab_widget, "wp_post_items") or not tab_widget.wp_post_items:
        return None
    idx = getattr(tab_widget, "_current_post_index", 0)
    if 0 <= idx < len(tab_widget.wp_post_items):
        return tab_widget.wp_post_items[idx]
    return None


def _set_youtube_controls_enabled(tab_widget: Any, enabled: bool) -> None:
    """Enable or disable YouTube embed options based on whether a valid video URL is present."""
    for attr in (
        "wp_cb_yt_use_story_time",
        "wp_cb_yt_stop_at_end",
        "wp_yt_pos_label",
        "wp_rad_yt_pos_top",
        "wp_rad_yt_pos_bottom",
    ):
        w = getattr(tab_widget, attr, None)
        if w is not None and hasattr(w, "setEnabled"):
            w.setEnabled(enabled)

    if hasattr(tab_widget, "wp_rad_yt_pos_top") and hasattr(tab_widget, "wp_rad_yt_pos_bottom"):
        if enabled:
            tab_widget.wp_rad_yt_pos_top.setToolTip("Place the responsive YouTube video embed above the transcript")
            tab_widget.wp_rad_yt_pos_bottom.setToolTip("Place the responsive YouTube video embed below the transcript")
        else:
            hint = "Enter a valid YouTube URL above to configure video placement."
            tab_widget.wp_rad_yt_pos_top.setToolTip(hint)
            tab_widget.wp_rad_yt_pos_bottom.setToolTip(hint)

    if hasattr(tab_widget, "wp_cb_yt_use_story_time"):
        if enabled:
            tab_widget.wp_cb_yt_use_story_time.setToolTip(
                "When checked, embeds the video starting at this story's start time in the broadcast. "
                "When unchecked on a custom single-story URL, starts playback at 0:00 (or the explicit timestamp in the URL)."
            )
        else:
            tab_widget.wp_cb_yt_use_story_time.setToolTip("Enter a valid YouTube URL above to configure story timestamp start.")

    if hasattr(tab_widget, "wp_cb_yt_stop_at_end"):
        if enabled:
            tab_widget.wp_cb_yt_stop_at_end.setToolTip(
                "When checked, appends an end timestamp to the YouTube embed parameter so playback stops when this story concludes."
            )
        else:
            tab_widget.wp_cb_yt_stop_at_end.setToolTip("Enter a valid YouTube URL above to configure story timestamp end.")


def update_youtube_status_label(tab_widget: Any) -> None:
    """Refresh the dynamic status preview line below the YouTube URL input."""
    if not hasattr(tab_widget, "wp_yt_status_label") or not tab_widget.wp_yt_status_label:
        return
    post = _get_current_post(tab_widget)
    if not post:
        tab_widget.wp_yt_status_label.setText("No post selected.")
        _set_youtube_controls_enabled(tab_widget, False)
        return

    url = (tab_widget.wp_yt_url_edit.text() if hasattr(tab_widget, "wp_yt_url_edit") else "").strip()
    if not url:
        tab_widget.wp_yt_status_label.setText("No YouTube video attached. (Enter a YouTube URL above to configure embed options)")
        tab_widget.wp_yt_status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        _set_youtube_controls_enabled(tab_widget, False)
        return

    vid_id, url_t = extract_youtube_video_id(url)
    if not vid_id:
        tab_widget.wp_yt_status_label.setText("Invalid YouTube URL or ID.")
        tab_widget.wp_yt_status_label.setStyleSheet("color: #f87171; font-size: 11px;")
        _set_youtube_controls_enabled(tab_widget, False)
        return

    _set_youtube_controls_enabled(tab_widget, True)

    use_story_time = tab_widget.wp_cb_yt_use_story_time.isChecked() if hasattr(tab_widget, "wp_cb_yt_use_story_time") else True
    stop_at_end = tab_widget.wp_cb_yt_stop_at_end.isChecked() if hasattr(tab_widget, "wp_cb_yt_stop_at_end") else False
    pos = "top" if (hasattr(tab_widget, "wp_rad_yt_pos_top") and tab_widget.wp_rad_yt_pos_top.isChecked()) else "bottom"

    start_sec = None
    if use_story_time and post.get("start") is not None:
        start_sec = float(post["start"])
    elif url_t is not None and url_t > 0:
        start_sec = float(url_t)

    end_sec = None
    if stop_at_end and post.get("end") is not None:
        end_sec = float(post["end"])

    parts = [f"Valid YouTube ID: <b>{html.escape(vid_id)}</b>"]
    if start_sec is not None and start_sec > 0:
        start_fmt = format_time(start_sec)
        if end_sec is not None and end_sec > start_sec:
            end_fmt = format_time(end_sec)
            parts.append(f"Embed starts at {start_fmt} and stops at {end_fmt}")
        else:
            parts.append(f"Embed starts at {start_fmt}")
    else:
        if end_sec is not None and end_sec > 0:
            end_fmt = format_time(end_sec)
            parts.append(f"Embed starts at 00:00 and stops at {end_fmt}")
        else:
            parts.append("Embed starts at 00:00")

    parts.append(f"(at {pos} of post)")
    tab_widget.wp_yt_status_label.setText(" — ".join(parts))
    tab_widget.wp_yt_status_label.setStyleSheet("color: #4ade80; font-size: 11px;")


def load_youtube_from_post(tab_widget: Any, post: Dict[str, Any]) -> None:
    """Populate YouTube controls from the given post dictionary."""
    if not hasattr(tab_widget, "wp_yt_url_edit") or not tab_widget.wp_yt_url_edit:
        return

    tab_widget.wp_yt_url_edit.blockSignals(True)
    if hasattr(tab_widget, "wp_cb_yt_use_story_time"):
        tab_widget.wp_cb_yt_use_story_time.blockSignals(True)
    if hasattr(tab_widget, "wp_cb_yt_stop_at_end"):
        tab_widget.wp_cb_yt_stop_at_end.blockSignals(True)
    if hasattr(tab_widget, "wp_rad_yt_pos_top"):
        tab_widget.wp_rad_yt_pos_top.blockSignals(True)
        tab_widget.wp_rad_yt_pos_bottom.blockSignals(True)

    url = post.get("youtube_url") or ""
    tab_widget.wp_yt_url_edit.setText(url)

    if hasattr(tab_widget, "wp_cb_yt_use_story_time"):
        use_time = post.get("youtube_use_story_time")
        if use_time is None:
            use_time = True
        tab_widget.wp_cb_yt_use_story_time.setChecked(bool(use_time))

    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    if hasattr(tab_widget, "wp_cb_yt_stop_at_end"):
        stop_val = post.get("youtube_stop_at_end")
        if stop_val is None:
            stop_val = str(settings.value("wp_yt_stop_at_story_end", "false")).lower() in ("true", "1", "yes")
        tab_widget.wp_cb_yt_stop_at_end.setChecked(bool(stop_val))

    if hasattr(tab_widget, "wp_rad_yt_pos_top"):
        placement = post.get("youtube_placement")
        if not placement:
            placement = str(settings.value("wp_yt_embed_placement", "top")).lower()
        if placement == "bottom":
            tab_widget.wp_rad_yt_pos_bottom.setChecked(True)
        else:
            tab_widget.wp_rad_yt_pos_top.setChecked(True)

    tab_widget.wp_yt_url_edit.blockSignals(False)
    if hasattr(tab_widget, "wp_cb_yt_use_story_time"):
        tab_widget.wp_cb_yt_use_story_time.blockSignals(False)
    if hasattr(tab_widget, "wp_cb_yt_stop_at_end"):
        tab_widget.wp_cb_yt_stop_at_end.blockSignals(False)
    if hasattr(tab_widget, "wp_rad_yt_pos_top"):
        tab_widget.wp_rad_yt_pos_top.blockSignals(False)
        tab_widget.wp_rad_yt_pos_bottom.blockSignals(False)

    update_youtube_status_label(tab_widget)


def sync_youtube_to_meta(target_meta: Dict[str, Any], post: Dict[str, Any]) -> None:
    """Sync YouTube embed settings from post to target_meta dictionary."""
    if not isinstance(target_meta, dict) or not isinstance(post, dict):
        return
    target_meta["youtube_url"] = post.get("youtube_url", "")
    target_meta["youtube_video_id"] = post.get("youtube_video_id", "")
    target_meta["youtube_use_story_time"] = post.get("youtube_use_story_time", True)
    target_meta["youtube_stop_at_end"] = post.get("youtube_stop_at_end", False)
    target_meta["youtube_placement"] = post.get("youtube_placement", "top")


def _on_youtube_url_changed(tab_widget: Any, text: str) -> None:
    if getattr(tab_widget, "_syncing_post_editor", False):
        return
    post = _get_current_post(tab_widget)
    if not post:
        return

    url = text.strip()
    vid_id, _ = extract_youtube_video_id(url)
    apply_all = hasattr(tab_widget, "wp_cb_yt_apply_all") and tab_widget.wp_cb_yt_apply_all.isChecked()

    if apply_all and hasattr(tab_widget, "wp_post_items"):
        for p in tab_widget.wp_post_items:
            p["youtube_url"] = url
            p["youtube_video_id"] = vid_id
        # Also store to project_metadata.wordpress
        proj_meta = getattr(tab_widget.main_window, "project_metadata", None)
        if isinstance(proj_meta, dict):
            wp_meta = proj_meta.setdefault("wordpress", {})
            wp_meta["youtube_url"] = url
            wp_meta["youtube_video_id"] = vid_id
        # Also store to all stories
        stories = getattr(tab_widget.main_window, "stories", []) or []
        for st in stories:
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            st_wp = st.metadata.setdefault("wordpress", {})
            st_wp["youtube_url"] = url
            st_wp["youtube_video_id"] = vid_id
    else:
        post["youtube_url"] = url
        post["youtube_video_id"] = vid_id

    update_youtube_status_label(tab_widget)

    # Refresh post list indicators
    if hasattr(tab_widget, "wp_posts_list"):
        for idx in range(tab_widget.wp_posts_list.count()):
            tab_widget._update_post_list_item_label(idx)

    cur_idx = getattr(tab_widget, "_current_post_index", 0)
    if hasattr(tab_widget, "_sync_to_proj"):
        tab_widget._sync_to_proj(cur_idx)


def _on_youtube_apply_all_toggled(tab_widget: Any, checked: bool) -> None:
    if checked:
        url = (tab_widget.wp_yt_url_edit.text() if hasattr(tab_widget, "wp_yt_url_edit") else "").strip()
        if url:
            _on_youtube_url_changed(tab_widget, url)


def _on_youtube_use_story_time_toggled(tab_widget: Any, checked: bool) -> None:
    if getattr(tab_widget, "_syncing_post_editor", False):
        return
    post = _get_current_post(tab_widget)
    if not post:
        return
    post["youtube_use_story_time"] = checked
    update_youtube_status_label(tab_widget)
    cur_idx = getattr(tab_widget, "_current_post_index", 0)
    if hasattr(tab_widget, "_sync_to_proj"):
        tab_widget._sync_to_proj(cur_idx)


def _on_youtube_stop_at_end_toggled(tab_widget: Any, checked: bool) -> None:
    if getattr(tab_widget, "_syncing_post_editor", False):
        return
    post = _get_current_post(tab_widget)
    if not post:
        return
    post["youtube_stop_at_end"] = checked
    update_youtube_status_label(tab_widget)
    cur_idx = getattr(tab_widget, "_current_post_index", 0)
    if hasattr(tab_widget, "_sync_to_proj"):
        tab_widget._sync_to_proj(cur_idx)


def _on_youtube_placement_toggled(tab_widget: Any, placement: str) -> None:
    if getattr(tab_widget, "_syncing_post_editor", False):
        return
    post = _get_current_post(tab_widget)
    if not post:
        return
    post["youtube_placement"] = placement
    update_youtube_status_label(tab_widget)
    cur_idx = getattr(tab_widget, "_current_post_index", 0)
    if hasattr(tab_widget, "_sync_to_proj"):
        tab_widget._sync_to_proj(cur_idx)


def format_post_list_label_and_tooltip(tab_widget: Any, idx: int) -> Tuple[str, str]:
    """Return formatted label text and rich multi-line tooltip for an item in wp_posts_list."""
    if not hasattr(tab_widget, "wp_post_items") or not (0 <= idx < len(tab_widget.wp_post_items)):
        return "", ""

    post = tab_widget.wp_post_items[idx]
    task_label = post.get("task_label") or f"Post {idx + 1}"
    title = post.get("title") or task_label

    n_auths = len(post.get("author_ids", [])) + len(post.get("author_term_ids", []))
    n_cats = len(post.get("category_ids", []))
    is_podcast = bool(post.get("is_podcast", False))
    inc_audio = getattr(tab_widget, "wp_cb_include_audio", None) and tab_widget.wp_cb_include_audio.isChecked()
    has_yt = bool(post.get("youtube_url") or post.get("youtube_video_id"))
    img_mode = post.get("featured_image_mode", "none")
    has_img = bool(img_mode in ("grab", "file") and post.get("featured_image"))

    badges = []
    if n_auths:
        badges.append(f"{n_auths} author" + ("s" if n_auths > 1 else ""))
    if n_cats:
        badges.append(f"{n_cats} cat" + ("s" if n_cats > 1 else ""))
    if is_podcast:
        badges.append("Podcast")
    elif inc_audio:
        badges.append("Audio")
    if has_yt:
        badges.append("YouTube")
    if has_img:
        badges.append("Image")

    badge_str = f" ({', '.join(badges)})" if badges else ""
    label_text = f"{task_label}: {title}{badge_str}"

    # Build rich hover tooltip
    tt_lines = [f"<b>{html.escape(title)}</b>"]
    st = post.get("start")
    en = post.get("end")
    if st is not None and en is not None:
        tt_lines.append(f"Time Range: {format_time(st)} - {format_time(en)}")
    elif st is not None:
        tt_lines.append(f"Start: {format_time(st)}")
    else:
        tt_lines.append("Scope: Full Broadcast")

    media_types = []
    if is_podcast:
        media_types.append("Castos Podcast Episode")
    elif inc_audio:
        media_types.append("WordPress Audio Player (MP3)")
    if has_yt:
        media_types.append("YouTube Responsive Video Embed")
    if not media_types:
        media_types.append("Transcript Text Only")
    tt_lines.append(f"Media: {', '.join(media_types)}")

    if has_img:
        tt_lines.append(f"Featured Image: Attached ({img_mode})")
    else:
        tt_lines.append("Featured Image: None")

    if n_auths:
        tt_lines.append(f"Authors: {n_auths} selected")
    if n_cats:
        tt_lines.append(f"Categories: {n_cats} selected")

    tooltip_text = "\n".join(tt_lines)
    return label_text, tooltip_text

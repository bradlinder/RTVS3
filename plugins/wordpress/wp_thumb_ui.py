"""UI presentation controller for WordPress Featured Image controls and preview."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from prs_shared import format_time
from plugins.wordpress.wp_thumbnail_defaults import (
    compute_default_segment_frame_pos,
    get_youtube_source_info,
    materialize_post_featured_image,
    resolve_post_youtube_video_id,
)


def _set_preview_pixmap(tab_widget: Any, image_path: str) -> None:
    pix = QPixmap(str(image_path)).scaled(
        160,
        90,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    tab_widget.wp_thumb_preview_label.setPixmap(pix)


def _start_youtube_thumbnail_fetch(tab_widget: Any, video_id: str, thumbnail_url: str = "") -> None:
    """Kick off a non-blocking background QThread fetch for a YouTube default thumbnail."""
    if not video_id or os.environ.get("RTVS_TEST_MODE"):
        return
    active = getattr(tab_widget, "_yt_thumb_worker", None)
    if active is not None:
        try:
            if active.isRunning() and getattr(active, "video_id", "") == video_id:
                return
            if active.isRunning():
                active.requestInterruption()
        except RuntimeError:
            pass

    from plugins.wordpress.wp_workers import YouTubeThumbnailFetchWorker

    worker = YouTubeThumbnailFetchWorker(video_id=video_id, thumbnail_url=thumbnail_url)
    tab_widget._yt_thumb_worker = worker
    worker.finished_signal.connect(
        lambda vid, path: on_youtube_thumbnail_fetched(tab_widget, vid, path)
    )
    worker.finished.connect(worker.deleteLater)
    worker.start()


def on_youtube_thumbnail_fetched(tab_widget: Any, video_id: str, local_path: str) -> None:
    """Apply downloaded YouTube thumbnail preview on the Qt main thread if still relevant."""
    try:
        items = getattr(tab_widget, "wp_post_items", None) or []
        cur_idx = getattr(tab_widget, "_current_post_index", -1)
    except RuntimeError:
        return

    if local_path and Path(local_path).is_file():
        for idx, p in enumerate(items):
            if p.get("featured_image_mode") == "youtube" and resolve_post_youtube_video_id(p, tab_widget.main_window) == video_id:
                p["featured_image"] = local_path
                if hasattr(tab_widget, "_update_post_list_item_label"):
                    tab_widget._update_post_list_item_label(idx)

    if not (0 <= cur_idx < len(items)):
        return
    post = items[cur_idx]
    if post.get("featured_image_mode") != "youtube":
        return
    if resolve_post_youtube_video_id(post, tab_widget.main_window) != video_id:
        return

    if local_path and Path(local_path).is_file():
        tab_widget.wp_thumb_path_label.setText(f"YouTube default thumbnail ({Path(local_path).name})")
        _set_preview_pixmap(tab_widget, local_path)
    else:
        tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (will download on export)")
        tab_widget.wp_thumb_preview_label.clear()
        tab_widget.wp_thumb_preview_label.setText("YouTube\nThumbnail")


def load_featured_image_from_post(tab_widget: Any, index: int, post: Dict[str, Any]) -> None:
    """Populate Featured Image radio buttons, scrubber, and preview from a post dict."""
    yt_src = get_youtube_source_info(tab_widget.main_window)
    yt_vid = resolve_post_youtube_video_id(post, tab_widget.main_window)
    has_yt_option = bool(yt_vid)

    if hasattr(tab_widget, "wp_rad_thumb_youtube"):
        tab_widget.wp_rad_thumb_youtube.setVisible(has_yt_option)

    mode = str(post.get("featured_image_mode") or "none").strip().lower()
    img = post.get("featured_image")
    frame_pos = post.get("frame_pos")
    if frame_pos is None:
        frame_pos = compute_default_segment_frame_pos(
            post.get("start"),
            post.get("end"),
            fallback=float(getattr(tab_widget.main_window, "current_position", 0.0) or 0.0),
        )
        post["frame_pos"] = frame_pos

    if mode == "youtube" and has_yt_option and hasattr(tab_widget, "wp_rad_thumb_youtube"):
        tab_widget.wp_rad_thumb_youtube.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(False)
        cached_path = materialize_post_featured_image(
            post,
            tab_widget.main_window,
            post_index=index,
            allow_network=False,
        )
        if cached_path and Path(cached_path).is_file():
            tab_widget.wp_thumb_path_label.setText(f"YouTube default thumbnail ({Path(cached_path).name})")
            _set_preview_pixmap(tab_widget, cached_path)
        else:
            tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (fetching preview...)")
            tab_widget.wp_thumb_preview_label.clear()
            tab_widget.wp_thumb_preview_label.setText("YouTube\nThumbnail")
            _start_youtube_thumbnail_fetch(tab_widget, yt_vid, yt_src.get("thumbnail_url", ""))
    elif mode == "grab" and tab_widget._is_video_project:
        tab_widget.wp_rad_thumb_grab.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(True)
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget._sync_wp_slider_to_pos(frame_pos)
        if not (img and Path(str(img)).exists()):
            media_file = getattr(tab_widget.main_window, "audio_file", None)
            if media_file and Path(str(media_file)).is_file():
                img = tab_widget._capture_wp_frame(pos=frame_pos, user_initiated=False)
        if img and Path(str(img)).exists():
            tab_widget.wp_thumb_path_label.setText(f"Video frame captured at {format_time(frame_pos, include_millis=True)}")
            _set_preview_pixmap(tab_widget, str(img))
        else:
            tab_widget.wp_thumb_path_label.setText(f"Video frame will be captured at {format_time(frame_pos, include_millis=True)}")
            tab_widget.wp_thumb_preview_label.clear()
            tab_widget.wp_thumb_preview_label.setText("Video Frame")
    elif mode == "file" and img:
        tab_widget.wp_rad_thumb_file.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(True)
        tab_widget.wp_thumb_path_label.setText(Path(str(img)).name)
        if Path(str(img)).exists():
            _set_preview_pixmap(tab_widget, str(img))
        else:
            tab_widget.wp_thumb_preview_label.clear()
            tab_widget.wp_thumb_preview_label.setText("Image not found")
    else:
        tab_widget.wp_rad_thumb_none.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget.wp_thumb_path_label.setText("No image selected")
        tab_widget.wp_thumb_preview_label.clear()
        tab_widget.wp_thumb_preview_label.setText("No Thumbnail")

    tab_widget.wp_thumb_caption_edit.setText(str(post.get("featured_image_caption") or ""))
    tab_widget.wp_thumb_alt_edit.setText(str(post.get("featured_image_alt_text") or ""))
    show_meta = (
        (mode == "youtube" and has_yt_option)
        or (mode == "grab" and tab_widget._is_video_project)
        or (mode == "file" and bool(img))
    )
    tab_widget.wp_img_meta_widget.setVisible(show_meta)


def on_featured_image_mode_changed(tab_widget: Any) -> None:
    """Handle user selection of Featured Image radio buttons."""
    if tab_widget._syncing_post_editor or not (0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items)):
        return
    post = tab_widget.wp_post_items[tab_widget._current_post_index]
    post["featured_image_user_set"] = True

    if tab_widget.wp_rad_thumb_none.isChecked():
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget.wp_img_meta_widget.setVisible(False)
        tab_widget.wp_thumb_path_label.setText("No image selected")
        tab_widget.wp_thumb_preview_label.clear()
        tab_widget.wp_thumb_preview_label.setText("No Thumbnail")
        post["featured_image"] = None
        post["featured_image_mode"] = "none"
    elif hasattr(tab_widget, "wp_rad_thumb_youtube") and tab_widget.wp_rad_thumb_youtube.isChecked():
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget.wp_img_meta_widget.setVisible(True)
        post["featured_image_mode"] = "youtube"
        post["featured_image"] = None
        yt_src = get_youtube_source_info(tab_widget.main_window)
        yt_vid = resolve_post_youtube_video_id(post, tab_widget.main_window)
        cached_path = materialize_post_featured_image(
            post,
            tab_widget.main_window,
            post_index=tab_widget._current_post_index,
            allow_network=False,
        )
        if cached_path and Path(cached_path).is_file():
            tab_widget.wp_thumb_path_label.setText(f"YouTube default thumbnail ({Path(cached_path).name})")
            _set_preview_pixmap(tab_widget, cached_path)
        else:
            tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (fetching preview...)")
            tab_widget.wp_thumb_preview_label.clear()
            tab_widget.wp_thumb_preview_label.setText("YouTube\nThumbnail")
            _start_youtube_thumbnail_fetch(tab_widget, yt_vid, yt_src.get("thumbnail_url", ""))
    elif tab_widget.wp_rad_thumb_grab.isChecked():
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget.wp_scrub_widget.setVisible(True)
        tab_widget.wp_img_meta_widget.setVisible(True)
        post["featured_image_mode"] = "grab"
        if post.get("frame_pos") is None:
            post["frame_pos"] = compute_default_segment_frame_pos(
                post.get("start"),
                post.get("end"),
                fallback=float(getattr(tab_widget.main_window, "current_position", 0.0) or 0.0),
            )
        tab_widget._sync_wp_slider_to_pos(post["frame_pos"])
        tab_widget._capture_wp_frame(pos=post.get("frame_pos"), user_initiated=True)
    elif tab_widget.wp_rad_thumb_file.isChecked():
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(True)
        tab_widget.wp_img_meta_widget.setVisible(True)
        custom_path = post.get("featured_image")
        if custom_path and Path(str(custom_path)).exists() and post.get("featured_image_mode") == "file":
            tab_widget.wp_thumb_path_label.setText(Path(str(custom_path)).name)
            _set_preview_pixmap(tab_widget, str(custom_path))
        else:
            post["featured_image_mode"] = "file"
            post["featured_image"] = None
            tab_widget.wp_thumb_path_label.setText("Click Browse to select image file")
            tab_widget.wp_thumb_preview_label.clear()
            tab_widget.wp_thumb_preview_label.setText("No Image\nSelected")

    if hasattr(tab_widget, "_update_post_list_item_label"):
        tab_widget._update_post_list_item_label(tab_widget._current_post_index)
    if hasattr(tab_widget, "_sync_post_to_project"):
        tab_widget._sync_post_to_project(tab_widget._current_post_index)


__all__ = [
    "load_featured_image_from_post",
    "on_featured_image_mode_changed",
    "on_youtube_thumbnail_fetched",
]

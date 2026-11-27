"""UI presentation controller for WordPress Featured Image controls and preview."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from prs_shared import format_time
from plugins.wordpress.wp_thumbnail_defaults import (
    compute_default_segment_frame_pos,
    get_youtube_source_info,
    materialize_post_featured_image,
    resolve_post_youtube_video_id,
)


class ClickableThumbnailLabel(QLabel):
    """QLabel preview that opens a full-size preview dialog when clicked."""

    clicked = Signal()

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._full_image_path: Optional[str] = None
        self._source_description: str = ""

    def set_full_image(self, image_path: Optional[str], source_description: str = "") -> None:
        if image_path and Path(str(image_path)).is_file():
            self._full_image_path = str(image_path)
            self._source_description = str(source_description or "").strip()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip("Click to view full-size preview")
        else:
            self.clear_full_image()

    def clear_full_image(self) -> None:
        self._full_image_path = None
        self._source_description = ""
        self.unsetCursor()
        self.setToolTip("")

    def full_image_path(self) -> Optional[str]:
        return self._full_image_path

    def mousePressEvent(self, event: Any) -> None:
        if (
            event is not None
            and event.button() == Qt.MouseButton.LeftButton
            and self._full_image_path
            and Path(self._full_image_path).is_file()
        ):
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class FeaturedImageLightboxDialog(QDialog):
    """Lightweight resizable modal lightbox displaying a full-resolution featured image."""

    def __init__(self, image_path: str, source_description: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Featured Image Preview")
        self.setMinimumSize(420, 280)
        self._image_path = str(image_path)
        self._source_pixmap = QPixmap(self._image_path)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        w_px = self._source_pixmap.width()
        h_px = self._source_pixmap.height()
        dim_str = f"{w_px} x {h_px} px" if (w_px > 0 and h_px > 0) else "Unavailable"
        desc = str(source_description or Path(self._image_path).name).strip()
        header_text = f"{desc}  ({dim_str})" if desc else dim_str
        self.header_label = QLabel(header_text)
        self.header_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(320, 180)
        layout.addWidget(self.image_label, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        # Size dialog proportionally to image capped to available screen bounds
        max_w, max_h = 960, 620
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                max_w = max(480, int(avail.width() * 0.78))
                max_h = max(320, int(avail.height() * 0.78))
        except Exception:
            pass
        if w_px > 0 and h_px > 0:
            init_w = max(460, min(max_w, w_px + 32))
            init_h = max(320, min(max_h, h_px + 92))
            self.resize(init_w, init_h)
        else:
            self.resize(560, 380)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._source_pixmap.isNull():
            self.image_label.setText("Could not load preview image.")
            return
        avail = self.image_label.size()
        target_w = max(120, min(avail.width(), self._source_pixmap.width()))
        target_h = max(90, min(avail.height(), self._source_pixmap.height()))
        scaled = self._source_pixmap.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._update_scaled_pixmap()


def set_preview_pixmap(tab_widget: Any, image_path: str, source_description: str = "") -> None:
    """Display scaled preview thumbnail and enable click-to-enlarge for *image_path*."""
    lbl = getattr(tab_widget, "wp_thumb_preview_label", None)
    if lbl is None:
        return
    pix = QPixmap(str(image_path)).scaled(
        160,
        90,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    lbl.setPixmap(pix)
    if hasattr(lbl, "set_full_image"):
        lbl.set_full_image(str(image_path), source_description=source_description)


def clear_preview_pixmap(tab_widget: Any, placeholder_text: str) -> None:
    """Clear preview pixmap, disable click-to-enlarge, and show *placeholder_text*."""
    lbl = getattr(tab_widget, "wp_thumb_preview_label", None)
    if lbl is None:
        return
    lbl.clear()
    lbl.setText(placeholder_text)
    if hasattr(lbl, "clear_full_image"):
        lbl.clear_full_image()


def open_featured_image_preview(tab_widget: Any) -> Optional[FeaturedImageLightboxDialog]:
    """Open the full-resolution lightbox preview for the current WordPress featured image."""
    lbl = getattr(tab_widget, "wp_thumb_preview_label", None)
    img_path = lbl.full_image_path() if (lbl is not None and hasattr(lbl, "full_image_path")) else None
    if not img_path or not Path(img_path).is_file():
        return None
    desc = getattr(lbl, "_source_description", "") or ""
    dlg = FeaturedImageLightboxDialog(img_path, source_description=desc, parent=tab_widget)
    if not os.environ.get("RTVS_TEST_MODE"):
        dlg.exec()
    return dlg


def _set_preview_pixmap(tab_widget: Any, image_path: str, source_description: str = "") -> None:
    set_preview_pixmap(tab_widget, image_path, source_description=source_description)


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
        desc = f"YouTube default thumbnail ({Path(local_path).name})"
        tab_widget.wp_thumb_path_label.setText(desc)
        _set_preview_pixmap(tab_widget, local_path, source_description=desc)
    else:
        tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (will download on export)")
        clear_preview_pixmap(tab_widget, "YouTube\nThumbnail")


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
            desc = f"YouTube default thumbnail ({Path(cached_path).name})"
            tab_widget.wp_thumb_path_label.setText(desc)
            _set_preview_pixmap(tab_widget, cached_path, source_description=desc)
        else:
            tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (fetching preview...)")
            clear_preview_pixmap(tab_widget, "YouTube\nThumbnail")
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
            desc = f"Video frame captured at {format_time(frame_pos, include_millis=True)}"
            tab_widget.wp_thumb_path_label.setText(desc)
            _set_preview_pixmap(tab_widget, str(img), source_description=desc)
        else:
            tab_widget.wp_thumb_path_label.setText(f"Video frame will be captured at {format_time(frame_pos, include_millis=True)}")
            clear_preview_pixmap(tab_widget, "Video Frame")
    elif mode == "file" and img:
        tab_widget.wp_rad_thumb_file.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(True)
        desc = Path(str(img)).name
        tab_widget.wp_thumb_path_label.setText(desc)
        if Path(str(img)).exists():
            _set_preview_pixmap(tab_widget, str(img), source_description=desc)
        else:
            clear_preview_pixmap(tab_widget, "Image not found")
    else:
        tab_widget.wp_rad_thumb_none.setChecked(True)
        tab_widget.wp_scrub_widget.setVisible(False)
        tab_widget.wp_browse_widget.setVisible(False)
        tab_widget.wp_thumb_path_label.setText("No image selected")
        clear_preview_pixmap(tab_widget, "No Thumbnail")

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
        clear_preview_pixmap(tab_widget, "No Thumbnail")
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
            desc = f"YouTube default thumbnail ({Path(cached_path).name})"
            tab_widget.wp_thumb_path_label.setText(desc)
            _set_preview_pixmap(tab_widget, cached_path, source_description=desc)
        else:
            tab_widget.wp_thumb_path_label.setText("YouTube default thumbnail (fetching preview...)")
            clear_preview_pixmap(tab_widget, "YouTube\nThumbnail")
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
            desc = Path(str(custom_path)).name
            tab_widget.wp_thumb_path_label.setText(desc)
            _set_preview_pixmap(tab_widget, str(custom_path), source_description=desc)
        else:
            post["featured_image_mode"] = "file"
            post["featured_image"] = None
            tab_widget.wp_thumb_path_label.setText("Click Browse to select image file")
            clear_preview_pixmap(tab_widget, "No Image\nSelected")

    if hasattr(tab_widget, "_update_post_list_item_label"):
        tab_widget._update_post_list_item_label(tab_widget._current_post_index)
    if hasattr(tab_widget, "_sync_post_to_project"):
        tab_widget._sync_post_to_project(tab_widget._current_post_index)


__all__ = [
    "ClickableThumbnailLabel",
    "FeaturedImageLightboxDialog",
    "set_preview_pixmap",
    "clear_preview_pixmap",
    "open_featured_image_preview",
    "load_featured_image_from_post",
    "on_featured_image_mode_changed",
    "on_youtube_thumbnail_fetched",
]

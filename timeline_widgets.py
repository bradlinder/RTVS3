"""Radio & TV Story Segmenter — Timeline Ruler, Track Views, Playhead, Overview & Canvas Widgets.

Contains:
- WaveformEnvelope: Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels.
- build_waveform_pyramid: Multi-resolution downsampling pyramid generator for fast waveform rendering.
- TimelineCanvas: Interactive timeline widget rendering time rulers, waveform audio envelopes,
  video thumbnail strips, story segment blocks, fade envelope handles, and playhead cursor.
- TimelineResizeHandle: Drag-handle allowing vertical timeline resizing with persistent geometry.
- TimelineOverviewBar: High-level overview strip featuring mini story segment blocks and draggable viewport pill.
- TimelineWidget: Composite container widget combining TimelineCanvas, TimelineOverviewBar, and TimelineResizeHandle.
"""

from __future__ import annotations

import bisect
from bisect import bisect_left, bisect_right
import math
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

from PySide6.QtCore import QLineF, QPointF, QRectF, QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QToolTip, QVBoxLayout, QWidget

from core_utils import INTERNAL_APP_ID, calculate_fade_curve_factor, calculate_fade_out_factor
from theme_tokens import ThemeTokens
from story_widgets import StoryFadesChangeCommand

from waveform_envelope import WaveformEnvelope, build_waveform_pyramid
from timeline_overview_widget import TimelineResizeHandle, TimelineOverviewBar
from timeline_painter import (
    _FADE_STEPS,
    _FADE_IN_CURVE_TABLES,
    _FADE_OUT_CURVE_TABLES,
    render_waveform_buffer as _render_waveform_buffer_impl,
    paint_timeline_canvas as _paint_timeline_canvas_impl,
)
from timeline_context_menus import show_timeline_context_menu, show_selection_context_menu
from timeline_snap import (
    snap_time as _snap_time_impl,
    find_edge_at_pos as _find_edge_impl,
    find_fade_handle_at_pos as _find_fade_impl,
    find_story_at_time as _find_story_impl,
    is_near_playhead as _is_near_playhead_impl,
)

class TimelineCanvas(QWidget):
    positionClicked = Signal(float)
    scrubPositionChanged = Signal(float)
    storyRegionUpdated = Signal(int, float, float)
    newRegionStarted = Signal(float, float)
    newRegionUpdated = Signal(float, float)
    multiSelectionChanged = Signal(list)
    dragOperationFinished = Signal()
    scrollOffsetChanged = Signal(float)
    zoomChanged = Signal()
    mediaDropped = Signal(str)
    selectionRangeChanged = Signal(object, object)
    storyCreatedFromSelection = Signal(float, float)
    storyClicked = Signal(int)

    RULER_HEIGHT = 24
    EDGE_HANDLE_THRESHOLD = 8
    CURSOR_GRAB_THRESHOLD = 12
    DRAG_PIXEL_THRESHOLD = 5

    def __init__(self, parent=None, tokens=None):
        super().__init__(parent)
        self.tokens = tokens if tokens is not None else ThemeTokens()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.duration = 1
        self.position = 0
        self.skip_seconds = 5
        self.is_playing = False
        self.audio_file_name = None

        self.selection_start = None
        self.selection_end = None
        self.is_right_dragging = False
        self.active_selection_handle = None
        self.active_fade_target = None  # Tuple: (story_index, 'fade_in' | 'fade_out')
        self._fade_drag_start_val = 0.0
        self.show_audio_fades = False
        self.enable_magnetic_snapping = False
        self._last_tooltip_text = ""

        self.stories = []
        self.waveform_peaks = []
        self.waveform_levels = []
        self.video_thumbnails = []
        self.is_video = False
        self.show_waveform = True
        self.show_thumbnails = True
        self.thumbnail_position = "below"
        self.selected_story_indices = []
        self.transcript_selection_range = None

        self.zoom_level = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 300.0
        self.scroll_offset = 0.0

        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_offset = 0.0

        self.is_left_down = False
        self.is_scrubbing = False
        self.left_down_x = 0
        self.has_dragged = False
        self.selection_start_time = 0.0

        self.is_box_selecting = False
        self.box_start_time = 0.0

        self.active_edge_target = None

        self.waveform_pixmap = None
        self.pixmap_dirty = True
        self.buffered_total_width = 0
        self._last_rendered_width = 0
        self._last_rendered_height = 0
        self._last_rendered_scroll = None
        self._last_rendered_zoom = None

        # Drag performance optimization caches & event rate limiter
        self._last_drag_throttle_time = 0.0
        self._cached_story_snap_points = []
        self._fade_fill_brush_sel = QColor(0, 0, 0, 85)
        self._fade_fill_brush_unsel = QColor(0, 0, 0, 55)
        self._fade_in_ramp_pen_sel = QPen(QColor("#38bdf8"), 1.2)
        self._fade_in_ramp_pen_unsel = QPen(QColor("#7dd3fc"), 1.2)
        self._fade_out_ramp_pen_sel = QPen(QColor("#f43f5e"), 1.2)
        self._fade_out_ramp_pen_unsel = QPen(QColor("#fb7185"), 1.2)
        self._fade_in_handle_pen_sel = QPen(QColor("#38bdf8").darker(130), 1)
        self._fade_in_handle_pen_unsel = QPen(QColor("#60a5fa").darker(130), 1)
        self._fade_in_handle_brush_sel = QColor("#38bdf8")
        self._fade_in_handle_brush_unsel = QColor("#60a5fa")
        self._fade_out_handle_pen_sel = QPen(QColor("#f43f5e").darker(130), 1)
        self._fade_out_handle_pen_unsel = QPen(QColor("#f87171").darker(130), 1)
        self._fade_out_handle_brush_sel = QColor("#f43f5e")
        self._fade_out_handle_brush_unsel = QColor("#f87171")

        # Background generation activity indicators
        self.active_background_tasks = set()
        self.background_status_text = ""
        self.show_background_banner = False
        self._background_delay_timer = QTimer(self)
        self._background_delay_timer.setSingleShot(True)
        self._background_delay_timer.setInterval(100)
        self._background_delay_timer.timeout.connect(self._activate_background_banner)

        self.setMinimumHeight(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

    def set_is_video(self, is_video: bool):
        self.is_video = bool(is_video)
        self.pixmap_dirty = True
        self.update()

    def set_background_generation_active(self, task_name: str, active: bool):
        """Set generation state for 'waveform' or 'thumbnails'."""
        if active:
            self.active_background_tasks.add(task_name)
            self.show_background_banner = True
            if self._background_delay_timer.isActive():
                self._background_delay_timer.stop()
        else:
            self.active_background_tasks.discard(task_name)
            if not self.active_background_tasks:
                self._background_delay_timer.stop()
                self.show_background_banner = False
                self.background_status_text = ""
                self.pixmap_dirty = True
                self.update()
                return

        self._update_background_status_text()
        self.pixmap_dirty = True
        self.update()

    def _activate_background_banner(self):
        if self.active_background_tasks:
            self.show_background_banner = True
            self._update_background_status_text()
            self.pixmap_dirty = True
            self.update()

    def _update_background_status_text(self):
        win = self.window()
        is_es = getattr(win, "language", "en") == "es"
        labels = []
        if "waveform" in self.active_background_tasks:
            labels.append("forma de onda" if is_es else "audio waveform")
        if "thumbnails" in self.active_background_tasks:
            labels.append("miniaturas de video" if is_es else "video thumbnails")
        if labels:
            prefix = "Generando " if is_es else "Generating "
            sep = " y " if is_es else " and "
            self.background_status_text = f"{prefix}{sep.join(labels)}..."
        else:
            self.background_status_text = ""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            local_files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if local_files:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.mediaDropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def set_audio_filename(self, filename):
        self.audio_file_name = filename
        self.pixmap_dirty = True
        self.update()

    def set_duration(self, duration):
        self.duration = max(1, duration)
        # Upper limit on zoom level: clamp minimum visible window to 0.25s across all file lengths
        min_visible_seconds = 0.25
        self.max_zoom = max(1.0, float(self.duration) / min_visible_seconds)
        self.clamp_scroll_offset()
        self.zoomChanged.emit()
        self.pixmap_dirty = True
        self.update()

    def set_position(self, position):
        self.position = position
        self.ensure_position_visible(self.position)
        self.update()

    def set_playing_state(self, is_playing):
        self.is_playing = is_playing

    def ensure_position_visible(self, target_time):
        if self.zoom_level <= 1.0:
            return

        vis_dur = self.visible_duration()
        old_offset = self.scroll_offset

        if self.is_playing:
            self.scroll_offset = target_time - (vis_dur / 2.0)
            self.clamp_scroll_offset()
        else:
            view_start = self.scroll_offset
            view_end = self.scroll_offset + vis_dur
            margin = vis_dur * 0.05
            if target_time < (view_start + margin) or target_time > (view_end - margin):
                self.scroll_offset = target_time - (vis_dur / 2.0)
                self.clamp_scroll_offset()

        if self.scroll_offset != old_offset:
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True

    def set_transcript_selection_range(self, start, end):
        if start is None or end is None:
            self.transcript_selection_range = None
        else:
            self.transcript_selection_range = (max(0.0, float(start)), min(self.duration, float(end)))
        self.update()

    def set_stories(self, stories, selected_indices=None):
        self.stories = stories
        self.selected_story_indices = selected_indices if selected_indices is not None else []
        self._cached_story_snap_points = [(idx, float(s.start), float(s.end)) for idx, s in enumerate(self.stories or [])]
        self.update()

    def set_waveform_peaks(self, peaks, levels=None):
        self.waveform_peaks = peaks or []
        if levels is not None:
            self.waveform_levels = levels
        elif hasattr(peaks, "waveform_levels") and peaks.waveform_levels:
            self.waveform_levels = peaks.waveform_levels
        elif self.waveform_peaks:
            self.waveform_levels = build_waveform_pyramid(self.waveform_peaks)
        else:
            self.waveform_levels = []
        self.pixmap_dirty = True
        self.update()

    def set_timeline_views(self, show_waveform=True, show_thumbnails=True):
        self.show_waveform = bool(show_waveform)
        self.show_thumbnails = bool(show_thumbnails)
        self.pixmap_dirty = True
        self.update()

    def set_video_thumbnails(self, thumbnails):
        self.video_thumbnails = []
        for timestamp, filename in thumbnails or []:
            pix = QPixmap(str(filename))
            if not pix.isNull():
                self.video_thumbnails.append((float(timestamp), pix))
        self.pixmap_dirty = True
        self.update()

    def set_skip_seconds(self, seconds):
        self.skip_seconds = max(1, int(seconds))

    def visible_duration(self):
        return self.duration / self.zoom_level

    def clamp_scroll_offset(self):
        max_offset = max(0.0, self.duration - self.visible_duration())
        self.scroll_offset = max(0.0, min(max_offset, self.scroll_offset))
        self.scrollOffsetChanged.emit(self.scroll_offset)

    def time_to_x(self, time_val, width):
        if self.visible_duration() <= 0:
            return 0
        return ((time_val - self.scroll_offset) / self.visible_duration()) * width

    def x_to_time(self, x_val, width):
        ratio = x_val / max(1, width)
        return self.scroll_offset + (ratio * self.visible_duration())

    def snap_time(self, raw_time: float, exclude_story_idx: int = None, width: int = None, pixel_threshold: int = 10) -> float:
        return _snap_time_impl(self, raw_time, exclude_story_idx, width, pixel_threshold)

    def find_edge_at_pos(self, pos_x, width):
        return _find_edge_impl(self, pos_x, width)

    FADE_HANDLE_THRESHOLD = 12

    def find_fade_handle_at_pos(self, pos_x, pos_y, width):
        return _find_fade_impl(self, pos_x, pos_y, width)

    def find_story_at_time(self, time):
        return _find_story_impl(self, time)

    def is_near_playhead(self, pos_x, width):
        return _is_near_playhead_impl(self, pos_x, width)

    def set_zoom(self, new_zoom, center_x=None, focus_time=None):
        width = max(1, self.width())
        if focus_time is None:
            # Anchor zoom around the active cursor position (self.position)
            focus_time = getattr(self, "position", 0.0)
            if focus_time is None:
                focus_time = 0.0

        if center_x is None:
            # Keep the active cursor at its current screen x position, or center if off-screen
            cur_x = self.time_to_x(focus_time, width)
            if 0 <= cur_x <= width:
                center_x = cur_x
            else:
                center_x = width / 2.0

        self.zoom_level = max(self.min_zoom, min(self.max_zoom, new_zoom))

        new_visible = self.visible_duration()
        ratio = center_x / max(1, width)
        self.scroll_offset = focus_time - (ratio * new_visible)

        self.clamp_scroll_offset()
        self.zoomChanged.emit()
        self.scrollOffsetChanged.emit(self.scroll_offset)
        self.pixmap_dirty = True
        self.update()

    def resizeEvent(self, event):
        self.pixmap_dirty = True
        super().resizeEvent(event)

    def wheelEvent(self, event):
        # 1. Check for horizontal scrolling (trackpad 2-finger horizontal gesture, horizontal tilt/side wheel, or Shift+vertical wheel)
        h_delta_px = event.pixelDelta().x() if hasattr(event, "pixelDelta") else 0
        h_delta_angle = event.angleDelta().x() if hasattr(event, "angleDelta") else 0
        v_delta_angle = event.angleDelta().y() if hasattr(event, "angleDelta") else 0
        v_delta_px = event.pixelDelta().y() if hasattr(event, "pixelDelta") else 0
        modifiers = event.modifiers()

        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        # Explicit horizontal input (horizontal scroll wheel or trackpad 2-finger horizontal pan)
        if h_delta_px != 0 or h_delta_angle != 0:
            if h_delta_px != 0:
                pan_dt = (h_delta_px / max(1, self.width())) * self.visible_duration()
                self.scroll_offset -= pan_dt
            else:
                pan_dt = (h_delta_angle / 120.0) * (self.visible_duration() * 0.1)
                self.scroll_offset -= pan_dt
            self.clamp_scroll_offset()
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True
            self.update()
            event.accept()
            return

        # Shift + vertical wheel -> horizontal scrolling
        if is_shift:
            if v_delta_px != 0:
                pan_dt = (v_delta_px / max(1, self.width())) * self.visible_duration()
                self.scroll_offset -= pan_dt
            else:
                pan_dt = (v_delta_angle / 120.0) * (self.visible_duration() * 0.1)
                self.scroll_offset -= pan_dt
            self.clamp_scroll_offset()
            self.scrollOffsetChanged.emit(self.scroll_offset)
            self.pixmap_dirty = True
            self.update()
            event.accept()
            return

        # Vertical scroll wheel / standard wheel -> Zoom centered on active cursor
        if v_delta_angle != 0:
            factor = 1.15 ** (abs(v_delta_angle) / 120.0)
            if v_delta_angle > 0:
                self.set_zoom(self.zoom_level * factor)
            else:
                self.set_zoom(self.zoom_level / factor)
            event.accept()
            return

        super().wheelEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        pos_x = event.position().x()
        width = self.width()

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.pan_start_x = pos_x
            self.pan_start_offset = self.scroll_offset
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # --- FADE ENVELOPE HANDLE INTERACTION ---
        fade_hit = self.find_fade_handle_at_pos(pos_x, event.position().y(), width)
        if fade_hit:
            self.active_fade_target = fade_hit
            idx, f_type = fade_hit
            self._fade_drag_start_val = getattr(self.stories[idx], f_type, 0.0)
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()
            return

        # --- RIGHT-CLICK: Drag Selection, Handle Adjustments, or Context Menu ---
        if event.button() == Qt.MouseButton.RightButton:
            curr_t = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))

            # Check if clicking a handle on an existing right-click selection
            if self.selection_start is not None and self.selection_end is not None:
                x_start = self.time_to_x(self.selection_start, width)
                x_end = self.time_to_x(self.selection_end, width)
                x_min = min(x_start, x_end)
                x_max = max(x_start, x_end)

                if abs(pos_x - x_min) <= self.EDGE_HANDLE_THRESHOLD:
                    self.active_selection_handle = "start" if x_start <= x_end else "end"
                    self.is_right_dragging = True
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                    event.accept()
                    return
                elif abs(pos_x - x_max) <= self.EDGE_HANDLE_THRESHOLD:
                    self.active_selection_handle = "end" if x_start <= x_end else "start"
                    self.is_right_dragging = True
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                    event.accept()
                    return
                elif x_min < pos_x < x_max:
                    self._show_selection_context_menu(event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos())
                    event.accept()
                    return

            # Check if grabbing an existing story edge
            edge_hit = self.find_edge_at_pos(pos_x, width)
            if edge_hit:
                self.active_edge_target = edge_hit
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return

            # Otherwise, begin drawing a new selection region
            self.selection_start = curr_t
            self.selection_end = curr_t
            self.active_selection_handle = "end"
            self.is_right_dragging = True
            self.selectionRangeChanged.emit(self.selection_start, self.selection_end)
            self.update()
            event.accept()
            return

        # --- LEFT-CLICK: Continuous Audio Scrubbing & Playhead Navigation ---
        # Story boundaries cannot be moved by left-clicking/dragging handles.
        # Use right-click + drag on handles or the Set Story Start/End buttons.
        if event.button() == Qt.MouseButton.LeftButton:
            time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            self.position = time
            self.is_left_down = True
            self.is_scrubbing = True
            self.positionClicked.emit(time)
            self.scrubPositionChanged.emit(time)
            story_idx = self.find_story_at_time(time)
            if story_idx is not None:
                self.storyClicked.emit(story_idx)
            self.update()
            event.accept()
            return

    def mouseMoveEvent(self, event):
        pos_x = event.position().x()
        width = self.width()

        # Check if an active drag or pan operation is underway
        is_active_drag = bool(
            self.is_panning
            or self.is_right_dragging
            or (self.is_left_down and self.is_scrubbing)
            or self.active_fade_target
            or self.active_edge_target
        )

        if is_active_drag:
            # 60 FPS (16ms) rate limiting for continuous drag & scrub calculations
            now = time.perf_counter()
            if now - self._last_drag_throttle_time < 0.016:
                event.accept()
                return
            self._last_drag_throttle_time = now

        if self.is_panning:
            dx = pos_x - self.pan_start_x
            dt = (dx / max(1, width)) * self.visible_duration()
            self.scroll_offset = self.pan_start_offset - dt
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        # --- RIGHT-CLICK DRAG: Update Selection Region and Handles ---
        if self.is_right_dragging:
            raw_time = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))
            curr_time = self.snap_time(raw_time, width=width)
            if self.active_selection_handle == "start":
                self.selection_start = curr_time
            elif self.active_selection_handle == "end":
                self.selection_end = curr_time

            s = min(self.selection_start, self.selection_end)
            e = max(self.selection_start, self.selection_end)
            self.selectionRangeChanged.emit(s, e)
            self.update()
            event.accept()
            return

        # --- LEFT-CLICK DRAG: Continuous Audio Scrubbing ---
        if self.is_left_down and self.is_scrubbing:
            raw_time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            curr_time = self.snap_time(raw_time, width=width)
            self.scrubPositionChanged.emit(curr_time)
            event.accept()
            return

        # --- FADE HANDLE DRAG ---
        if self.active_fade_target:
            idx, f_type = self.active_fade_target
            if 0 <= idx < len(self.stories):
                story = self.stories[idx]
                story_dur = max(0.01, story.end - story.start)
                raw_time = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))
                curr_time = self.snap_time(raw_time, width=width)
                if f_type == "fade_in":
                    max_in = max(0.0, story_dur - getattr(story, "fade_out", 0.0))
                    story.fade_in = round(max(0.0, min(max_in, curr_time - story.start)), 2)
                elif f_type == "fade_out":
                    max_out = max(0.0, story_dur - getattr(story, "fade_in", 0.0))
                    story.fade_out = round(max(0.0, min(max_out, story.end - curr_time)), 2)
                self.update()
            event.accept()
            return

        if self.active_edge_target:
            idx, edge_type = self.active_edge_target
            if 0 <= idx < len(self.stories):
                raw_time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
                curr_time = self.snap_time(raw_time, exclude_story_idx=idx, width=width)
                story = self.stories[idx]

                if edge_type == 'start':
                    new_start = min(curr_time, story.end - 0.1)
                    story.start = new_start
                    self.storyRegionUpdated.emit(idx, new_start, story.end)
                elif edge_type == 'end':
                    new_end = max(curr_time, story.start + 0.1)
                    story.end = new_end
                    self.storyRegionUpdated.emit(idx, story.start, new_end)

                if hasattr(self, "_cached_story_snap_points"):
                    self._cached_story_snap_points = [(i, float(s.start), float(s.end)) for i, s in enumerate(self.stories)]
                self.update()

            event.accept()
            return

        pos_y = event.position().y()
        edge_hit = self.find_edge_at_pos(pos_x, width)
        fade_hit = self.find_fade_handle_at_pos(pos_x, pos_y, width)

        if self.is_near_playhead(pos_x, width) or edge_hit or fade_hit:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.unsetCursor()

        if not (self.is_panning or self.is_left_down or self.is_right_dragging or self.active_edge_target or self.active_fade_target):
            tooltip_text = ""
            if fade_hit:
                idx, f_type = fade_hit
                if 0 <= idx < len(self.stories):
                    f_dur = getattr(self.stories[idx], f_type, 0.0)
                    f_name = "Fade-In" if f_type == "fade_in" else "Fade-Out"
                    tooltip_text = f"{self.stories[idx].title} ({f_name}: {f_dur:.2f}s)\nDrag handle horizontally to adjust audio fade"
            elif edge_hit:
                idx, edge_type = edge_hit
                title = self.stories[idx].title if 0 <= idx < len(self.stories) else f"Story #{idx+1}"
                tooltip_text = f"{title} ({edge_type.capitalize()} Boundary)\nRight-click and drag to adjust"

            if tooltip_text:
                if tooltip_text != getattr(self, "_last_tooltip_text", ""):
                    self._last_tooltip_text = tooltip_text
                    QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
            else:
                if getattr(self, "_last_tooltip_text", ""):
                    self._last_tooltip_text = ""
                    QToolTip.hideText()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active_fade_target:
            idx, f_type = self.active_fade_target
            self.active_fade_target = None
            self.unsetCursor()
            if 0 <= idx < len(self.stories):
                win = self.window()
                curr_val = getattr(self.stories[idx], f_type, 0.0)
                if abs(curr_val - self._fade_drag_start_val) >= 0.01:
                    if f_type == "fade_in":
                        old_in, new_in = self._fade_drag_start_val, curr_val
                        old_out, new_out = self.stories[idx].fade_out, self.stories[idx].fade_out
                    else:
                        old_in, new_in = self.stories[idx].fade_in, self.stories[idx].fade_in
                        old_out, new_out = self._fade_drag_start_val, curr_val
                    if hasattr(win, "undo_stack"):
                        win.undo_stack.push(StoryFadesChangeCommand(win, idx, old_in, old_out, new_in, new_out))
                    elif hasattr(win, "save_project"):
                        win.save_project()
                if hasattr(win, "refresh_story_list"):
                    win.refresh_story_list()
            self.update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.unsetCursor()
            event.accept()
            return

        # --- RIGHT-CLICK RELEASE: Finalize Selection Boundaries ---
        if event.button() == Qt.MouseButton.RightButton:
            if self.is_right_dragging:
                self.is_right_dragging = False
                self.active_selection_handle = None
                self.unsetCursor()
                if self.selection_start is not None and self.selection_end is not None:
                    if abs(self.selection_start - self.selection_end) < 0.05:
                        self.selection_start = None
                        self.selection_end = None
                        self.selectionRangeChanged.emit(None, None)
                        self.update()
                        gpos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
                        self._show_timeline_context_menu(gpos, event.position().x())
                        event.accept()
                        return
                    else:
                        s = min(self.selection_start, self.selection_end)
                        e = max(self.selection_start, self.selection_end)
                        self.selection_start, self.selection_end = s, e
                        self.selectionRangeChanged.emit(s, e)
                self.update()
                event.accept()
                return

            if self.active_edge_target:
                self.active_edge_target = None
                self.unsetCursor()
                self.dragOperationFinished.emit()
                event.accept()
                return

        # --- LEFT-CLICK RELEASE: Finalize Audio Scrubbing ---
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_left_down:
                self.is_left_down = False
                self.is_scrubbing = False
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def _show_timeline_context_menu(self, global_pos, pos_x):
        show_timeline_context_menu(self, global_pos, pos_x)

    def _show_selection_context_menu(self, global_pos):
        show_selection_context_menu(self, global_pos)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Undo):
            main_win = self.window()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.undo()
                event.accept()
                return

        if event.matches(QKeySequence.StandardKey.Redo):
            main_win = self.window()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.redo()
                event.accept()
                return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            main_win = self.window()
            # If there is a selected/highlighted story, delete it directly from the timeline
            if hasattr(main_win, "delete_selected_story") and getattr(main_win, "current_selected_story_indices", None):
                main_win.delete_selected_story()
                event.accept()
                return
            elif self.selected_story_indices and hasattr(main_win, "delete_selected_story"):
                if hasattr(main_win, "apply_story_selection_indices"):
                    main_win.apply_story_selection_indices(self.selected_story_indices, seek=False)
                main_win.delete_selected_story()
                event.accept()
                return
            # If there is an active timeline drag selection range without a selected story, clear it
            elif self.selection_start is not None or self.selection_end is not None:
                self.selection_start = None
                self.selection_end = None
                self.selectionRangeChanged.emit(None, None)
                self.update()
                event.accept()
                return

        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.set_zoom(self.zoom_level * 1.2)
            event.accept()
            return

        if event.key() == Qt.Key.Key_Minus:
            self.set_zoom(self.zoom_level / 1.2)
            event.accept()
            return

        if event.key() == Qt.Key.Key_A or (event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.scroll_offset -= self.visible_duration() * 0.1
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        if event.key() == Qt.Key.Key_D or (event.key() == Qt.Key.Key_Right and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.scroll_offset += self.visible_duration() * 0.1
            self.clamp_scroll_offset()
            self.update()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Left:
            self.positionClicked.emit(max(0, self.position - self.skip_seconds))
            event.accept()
            return

        if event.key() == Qt.Key.Key_Right:
            self.positionClicked.emit(min(self.duration, self.position + self.skip_seconds))
            event.accept()
            return

        if event.key() == Qt.Key.Key_Home:
            self.positionClicked.emit(0)
            event.accept()
            return

        if event.key() == Qt.Key.Key_End:
            self.positionClicked.emit(self.duration)
            event.accept()
            return

        super().keyPressEvent(event)

    def set_thumbnail_position(self, position):
        if position in ("above", "below") and self.thumbnail_position != position:
            self.thumbnail_position = position
            self.pixmap_dirty = True
            self.update()

    def render_waveform_buffer(self, width, height):
        return _render_waveform_buffer_impl(self, width, height)


    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        try:
            _paint_timeline_canvas_impl(self, painter, event)
        finally:
            painter.end()


class TimelineWidget(QWidget):
    mediaDropped = Signal(str)

    def __init__(self, parent=None, tokens=None):
        super().__init__(parent)
        self.tokens = tokens if tokens is not None else getattr(parent, "tokens", ThemeTokens())
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas = TimelineCanvas(self, tokens=self.tokens)
        self.overview_bar = TimelineOverviewBar(self.canvas, parent=self, tokens=self.tokens)
        self.scrollbar = self.overview_bar
        self.resize_handle = TimelineResizeHandle(self)

        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.overview_bar)
        layout.addWidget(self.resize_handle)

        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        saved_h = settings.value("timeline_height", 140)
        try:
            saved_h = int(saved_h)
        except (ValueError, TypeError):
            saved_h = 140
        saved_h = max(90, min(500, saved_h))
        self.setFixedHeight(saved_h)

        self.canvas.scrollOffsetChanged.connect(self.update_scrollbar_from_canvas)
        self.canvas.mediaDropped.connect(self.mediaDropped.emit)
        self.canvas.zoomChanged.connect(self.update_scrollbar_range)
        self.scrollbar.valueChanged.connect(self.update_canvas_from_scrollbar)

        self.selectionRangeChanged = self.canvas.selectionRangeChanged
        self.storyCreatedFromSelection = self.canvas.storyCreatedFromSelection
        self.storyClicked = self.canvas.storyClicked

        self.is_internal_scrollbar_update = False
        self.update_scrollbar_range()

    def set_is_video(self, is_video: bool):
        if hasattr(self, "canvas") and hasattr(self.canvas, "set_is_video"):
            self.canvas.set_is_video(is_video)

    def set_background_generation_active(self, task_name: str, active: bool):
        if hasattr(self, "canvas") and hasattr(self.canvas, "set_background_generation_active"):
            self.canvas.set_background_generation_active(task_name, active)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.mediaDropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def update_scrollbar_range(self):
        self.is_internal_scrollbar_update = True
        total = int(self.canvas.duration * 1000)
        visible = int(self.canvas.visible_duration() * 1000)

        self.scrollbar.setRange(0, max(0, total - visible))
        self.scrollbar.setPageStep(visible)
        self.scrollbar.setSingleStep(max(100, visible // 10))
        self.is_internal_scrollbar_update = False
        self.update_scrollbar_from_canvas(self.canvas.scroll_offset)

    def update_scrollbar_from_canvas(self, offset):
        if self.is_internal_scrollbar_update:
            return

        self.is_internal_scrollbar_update = True
        try:
            self.scrollbar.setValue(int(offset * 1000))
        finally:
            self.is_internal_scrollbar_update = False

    def update_canvas_from_scrollbar(self, val):
        if self.is_internal_scrollbar_update:
            return

        self.is_internal_scrollbar_update = True
        try:
            self.canvas.scroll_offset = val / 1000.0
            self.canvas.clamp_scroll_offset()
            self.canvas.update()
        finally:
            self.is_internal_scrollbar_update = False

    def __getattr__(self, name):
        return getattr(self.canvas, name)



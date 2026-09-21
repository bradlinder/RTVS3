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

# Precomputed fade lookup tables for 60+ FPS curve rendering (16 segments per envelope)
_FADE_STEPS = 16
_FADE_IN_CURVE_TABLES = {
    c: [calculate_fade_curve_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}
_FADE_OUT_CURVE_TABLES = {
    c: [calculate_fade_out_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}


class WaveformEnvelope(list):
    """Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels."""
    def __init__(self, iterable=None, levels=None):
        super().__init__(iterable or [])
        self.waveform_levels = levels or []


def build_waveform_pyramid(peaks):
    """Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.
    
    Each level downsamples the previous level by 4x, allowing instantaneous O(1) viewport-scaled
    waveform rendering on long audio files (>60 min) without UI thread lag.
    """
    if not peaks:
        return []
    if HAVE_NUMPY and np is not None:
        try:
            arr = np.asarray(peaks, dtype=np.float32)
            levels = [arr]
            curr = arr
            while len(curr) > 4:
                pad = (4 - (len(curr) % 4)) % 4
                if pad:
                    curr_padded = np.pad(curr, (0, pad), mode="edge")
                else:
                    curr_padded = curr
                curr = np.max(curr_padded.reshape(-1, 4), axis=1)
                levels.append(curr)
            return levels
        except Exception:
            pass

    # Pure Python fallback
    levels = [list(peaks)]
    curr = levels[0]
    while len(curr) > 4:
        next_level = [max(curr[i:i + 4]) for i in range(0, len(curr), 4)]
        levels.append(next_level)
        curr = next_level
    return levels



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
        self.max_zoom = 80.0
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
        """Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels."""
        if not getattr(self, "enable_magnetic_snapping", True):
            return raw_time

        width = width or max(1, self.width())
        vis_dur = max(0.001, self.visible_duration())
        threshold_dt = (pixel_threshold / max(1, width)) * vis_dur

        snap_points = []

        # 1. Playhead position
        if hasattr(self, "position") and self.position is not None:
            snap_points.append(float(self.position))

        # 2. Selection region anchors
        if getattr(self, "selection_start", None) is not None:
            snap_points.append(float(self.selection_start))
        if getattr(self, "selection_end", None) is not None:
            snap_points.append(float(self.selection_end))

        # 3. Story boundaries
        cached_points = getattr(self, "_cached_story_snap_points", None)
        if cached_points is not None and len(cached_points) == len(getattr(self, "stories", [])):
            for idx, s_start, s_end in cached_points:
                if exclude_story_idx is not None and idx == exclude_story_idx:
                    continue
                snap_points.append(s_start)
                snap_points.append(s_end)
        else:
            for idx, story in enumerate(getattr(self, "stories", [])):
                if exclude_story_idx is not None and idx == exclude_story_idx:
                    continue
                snap_points.append(float(story.start))
                snap_points.append(float(story.end))

        best_snap = raw_time
        min_diff = threshold_dt + 0.00001

        for pt in snap_points:
            diff = abs(raw_time - pt)
            if diff <= threshold_dt and diff < min_diff:
                min_diff = diff
                best_snap = pt

        return best_snap

    def find_edge_at_pos(self, pos_x, width):
        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)

            if abs(pos_x - start_x) <= self.EDGE_HANDLE_THRESHOLD:
                return (index, 'start')
            elif abs(pos_x - end_x) <= self.EDGE_HANDLE_THRESHOLD:
                return (index, 'end')
        return None

    FADE_HANDLE_THRESHOLD = 12

    def find_fade_handle_at_pos(self, pos_x, pos_y, width):
        """Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks."""
        if not getattr(self, "show_audio_fades", False):
            return None

        top_y = self.RULER_HEIGHT
        if pos_y < (top_y - 8) or pos_y > (top_y + 26):
            return None

        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)
            if end_x < -16 or start_x > width + 16:
                continue

            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)

            # Fade-in handle apex sits at (start + fade_in) along top edge
            fin_x = self.time_to_x(story.start + fin, width)
            if abs(pos_x - fin_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_in")

            # Fade-out handle apex sits at (end - fade_out) along top edge
            fout_x = self.time_to_x(story.end - fout, width)
            if abs(pos_x - fout_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_out")
        return None

    def find_story_at_time(self, time):
        """Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping."""
        candidates = []
        for index, story in enumerate(self.stories):
            if story.start <= time <= story.end:
                candidates.append((story.end - story.start, index))
        if candidates:
            candidates.sort()
            return candidates[0][1]
        return None

    def is_near_playhead(self, pos_x, width):
        cursor_x = self.time_to_x(self.position, width)
        return abs(pos_x - cursor_x) <= self.CURSOR_GRAB_THRESHOLD

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
        win = self.window()
        menu = QMenu(self)
        width = self.width()
        time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
        story_idx = self.find_story_at_time(time)

        is_music = getattr(win, "story_detection_mode", "voice") == "music"
        is_es = getattr(win, "language", "en") == "es"
        term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

        select_action = None
        fades_action = None
        delete_action = None
        if story_idx is not None and 0 <= story_idx < len(self.stories):
            select_action = menu.addAction(f"{('Seleccionar' if is_es else 'Select')} {term} #{story_idx + 1}")
            if hasattr(win, "open_story_fades_dialog"):
                fades_action = menu.addAction("Ajustar fundidos de audio..." if is_es else "Set Audio Fades...")
            delete_action = menu.addAction(f"{('Eliminar' if is_es else 'Delete')} {term} #{story_idx + 1}")
            menu.addSeparator()

        has_audio = bool(getattr(win, "audio_file", None))
        has_video = bool(getattr(win, "current_media_is_video", False))

        regen_wf_act = None
        regen_th_act = None
        if hasattr(win, "regenerate_waveform"):
            label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
            regen_wf_act = menu.addAction(label)
            regen_wf_act.setEnabled(has_audio)

        if hasattr(win, "regenerate_video_thumbnails"):
            label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
            regen_th_act = menu.addAction(label)
            regen_th_act.setEnabled(has_audio and has_video)

        if not menu.actions():
            return

        selected = menu.exec(global_pos)
        if story_idx is not None and 0 <= story_idx < len(self.stories):
            if select_action and selected == select_action:
                self.storyClicked.emit(story_idx)
            elif fades_action and selected == fades_action:
                if hasattr(win, "open_story_fades_dialog"):
                    win.open_story_fades_dialog(story_index=story_idx)
            elif delete_action and selected == delete_action:
                if hasattr(win, "apply_story_selection_indices") and hasattr(win, "delete_selected_story"):
                    win.apply_story_selection_indices([story_idx], seek=False)
                    win.delete_selected_story()
        if regen_wf_act and selected == regen_wf_act:
            win.regenerate_waveform()
        elif regen_th_act and selected == regen_th_act:
            win.regenerate_video_thumbnails()

    def _show_selection_context_menu(self, global_pos):
        if self.selection_start is None or self.selection_end is None:
            return
        s = min(self.selection_start, self.selection_end)
        e = max(self.selection_start, self.selection_end)
        win = self.window()
        is_music = getattr(win, "story_detection_mode", "voice") == "music"
        is_es = getattr(win, "language", "en") == "es"
        term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")
        menu = QMenu(self)
        add_action = menu.addAction(f"{('Agregar' if is_es else 'Add')} {term} {('desde la selección' if is_es else 'from Selection')}")
        clear_action = menu.addAction("Borrar selección" if is_es else "Clear Selection")

        menu.addSeparator()
        has_audio = bool(getattr(win, "audio_file", None))
        has_video = bool(getattr(win, "current_media_is_video", False))

        regen_wf_act = None
        regen_th_act = None
        if hasattr(win, "regenerate_waveform"):
            label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
            regen_wf_act = menu.addAction(label)
            regen_wf_act.setEnabled(has_audio)

        if hasattr(win, "regenerate_video_thumbnails"):
            label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
            regen_th_act = menu.addAction(label)
            regen_th_act.setEnabled(has_audio and has_video)

        selected = menu.exec(global_pos)
        if selected == add_action:
            self.storyCreatedFromSelection.emit(s, e)
        elif selected == clear_action:
            self.selection_start = None
            self.selection_end = None
            self.selectionRangeChanged.emit(None, None)
            self.update()
        elif regen_wf_act and selected == regen_wf_act:
            win.regenerate_waveform()
        elif regen_th_act and selected == regen_th_act:
            win.regenerate_video_thumbnails()

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
        dpi_scale = self.devicePixelRatioF()
        phys_width = max(1, int(width * dpi_scale))
        phys_height = max(1, int(height * dpi_scale))

        pixmap = QPixmap(phys_width, phys_height)
        pixmap.setDevicePixelRatio(dpi_scale)
        pixmap.fill(self.tokens.color(self.tokens.bg_surface))

        painter = QPainter(pixmap)
        if not painter.isActive():
            return pixmap
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        available = max(20, height - self.RULER_HEIGHT)
        is_video_mode = getattr(self, "is_video", False) or bool(self.video_thumbnails) or ("thumbnails" in self.active_background_tasks)
        has_thumbs = bool(self.show_thumbnails and (self.video_thumbnails or is_video_mode))

        if has_thumbs and self.show_waveform:
            thumbnail_height = int(available * 0.46)
            waveform_height = available - thumbnail_height
        elif has_thumbs:
            thumbnail_height = available
            waveform_height = 0
        elif self.show_waveform:
            thumbnail_height = 0
            waveform_height = available
        else:
            thumbnail_height = 0
            waveform_height = 0

        if self.thumbnail_position == "below" and self.show_waveform and has_thumbs:
            waveform_y = self.RULER_HEIGHT
            thumbnail_y = self.RULER_HEIGHT + waveform_height
        else:
            thumbnail_y = self.RULER_HEIGHT
            waveform_y = self.RULER_HEIGHT + thumbnail_height

        middle_y = waveform_y + (waveform_height / 2.0)

        # Draw subtle divider line between waveform and thumbnail tracks when both are visible
        if has_thumbs and self.show_waveform and thumbnail_height > 0 and waveform_height > 0:
            divider_y = thumbnail_y if self.thumbnail_position == "below" else waveform_y
            painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
            painter.drawLine(QPointF(0, divider_y), QPointF(width, divider_y))

        if has_thumbs and thumbnail_height > 0:
            if self.video_thumbnails:
                target_h = max(14, int((thumbnail_height - 6) * 0.88))
                vis_dur = max(0.001, self.visible_duration())

                # Resizing logic: scale thumbnail width dynamically with track height
                sample_pix = self.video_thumbnails[0][1] if self.video_thumbnails else None
                aspect = (sample_pix.width() / max(1, sample_pix.height())) if (sample_pix and not sample_pix.isNull() and sample_pix.height() > 0) else (16.0 / 9.0)
                target_w = max(24, int(target_h * aspect))

                # Buffer based on scaled thumbnail width to avoid pop-in at borders
                dt_buffer = (target_w / max(1, width)) * vis_dur * 1.5
                t_min = max(0.0, self.scroll_offset - dt_buffer)
                t_max = min(self.duration, self.scroll_offset + vis_dur + dt_buffer)

                ts_list = [item[0] for item in self.video_thumbnails]
                start_idx = max(0, bisect_left(ts_list, t_min) - 1)
                end_idx = min(len(self.video_thumbnails), bisect_right(ts_list, t_max) + 1)

                # Prevent thumbnails from overlapping or cropping when zoomed out.
                # Prioritize full-size, uncropped display of frames over crowding.
                last_drawn_right = -100000.0
                min_gap_px = 2.0

                for i in range(start_idx, end_idx):
                    timestamp, pix = self.video_thumbnails[i]
                    x = self.time_to_x(timestamp, width)
                    if x + target_w < 0 or x - target_w > width:
                        continue
                    scaled = pix.scaled(
                        target_w,
                        target_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    draw_x = int(x - scaled.width() // 2)
                    # If drawing this thumbnail would overlap/clip the previous full-size thumbnail, skip it
                    if draw_x < (last_drawn_right + min_gap_px):
                        continue

                    draw_y = thumbnail_y + (thumbnail_height - scaled.height()) // 2
                    painter.drawPixmap(draw_x, int(draw_y), scaled)
                    painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
                    painter.drawRect(draw_x, int(draw_y), scaled.width(), scaled.height())
                    last_drawn_right = draw_x + scaled.width()
            elif "thumbnails" in self.active_background_tasks or is_video_mode:
                # Placeholder preview track while generating video thumbnails
                win = self.window()
                is_es = getattr(win, "language", "en") == "es"
                gen_text = "Generando miniaturas de video..." if is_es else "Generating video thumbnails..."
                
                # Draw subtle filmstrip frame placeholder boxes along the track
                target_h = max(14, int((thumbnail_height - 6) * 0.88))
                aspect = 16.0 / 9.0
                target_w = max(24, int(target_h * aspect))
                draw_y = thumbnail_y + (thumbnail_height - target_h) // 2
                
                painter.save()
                box_pen = self.tokens.pen(self.tokens.border_subtle, 1.0)
                box_pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(box_pen)
                
                step_px = target_w + 8
                x_pos = 12
                while x_pos + target_w < width - 12:
                    painter.drawRoundedRect(QRectF(x_pos, draw_y, target_w, target_h), 2.0, 2.0)
                    x_pos += step_px
                
                # Draw centered preview badge with text
                painter.setFont(self.font())
                fm = painter.fontMetrics()
                text_w = fm.horizontalAdvance(gen_text)
                text_badge_w = text_w + 24
                text_badge_h = min(26, max(18, thumbnail_height - 6))
                text_badge_x = (width - text_badge_w) / 2.0
                text_badge_y = thumbnail_y + (thumbnail_height - text_badge_h) / 2.0
                text_badge_rect = QRectF(text_badge_x, text_badge_y, text_badge_w, text_badge_h)
                
                painter.setPen(self.tokens.pen(self.tokens.status_banner_border, 1.0))
                painter.setBrush(self.tokens.brush(self.tokens.status_banner_bg, 235))
                painter.drawRoundedRect(text_badge_rect, 4.0, 4.0)
                painter.setPen(self.tokens.color(self.tokens.status_banner_text))
                painter.drawText(text_badge_rect, Qt.AlignmentFlag.AlignCenter, gen_text)
                painter.restore()

        if self.show_waveform and self.waveform_peaks and waveform_height > 0:
            painter.setPen(self.tokens.pen(self.tokens.waveform_stroke, 1.0))
            levels = self.waveform_levels or [self.waveform_peaks]
            total_pixel_width = max(width, int(width * self.zoom_level))
            level_index = 0
            while level_index + 1 < len(levels) and (len(levels[level_index]) / max(1, total_pixel_width)) > 2.0:
                level_index += 1
            peaks = levels[level_index]
            total_peaks = len(peaks)
            dur = max(0.001, self.duration)
            waveform_lines = []
            for x in range(width):
                t0 = self.x_to_time(x, width)
                t1 = self.x_to_time(x + 1, width)
                start_idx = int((t0 / dur) * total_peaks)
                end_idx = int((t1 / dur) * total_peaks)
                end_idx = max(start_idx + 1, end_idx)
                start_idx = max(0, min(total_peaks, start_idx))
                end_idx = max(0, min(total_peaks, end_idx))
                if start_idx >= total_peaks or end_idx <= start_idx:
                    continue

                peak_slice = peaks[start_idx:end_idx]
                if hasattr(peak_slice, "__len__") and len(peak_slice) > 0:
                    try:
                        max_val = float(np.max(peak_slice)) if (HAVE_NUMPY and np is not None and isinstance(peak_slice, np.ndarray)) else float(max(peak_slice))
                    except Exception:
                        max_val = float(max(peak_slice))
                    amplitude = max_val * (waveform_height * 0.88)
                    if amplitude > 0.5:
                        waveform_lines.append(
                            QLineF(x + 0.5, middle_y - amplitude / 2.0, x + 0.5, middle_y + amplitude / 2.0)
                        )
            if waveform_lines:
                painter.drawLines(waveform_lines)
        elif self.show_waveform and waveform_height > 0:
            painter.setPen(self.tokens.pen(self.tokens.waveform_baseline, 1))
            painter.drawLine(QPointF(0, middle_y), QPointF(width, middle_y))

        painter.end()
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        waveform_height = height - self.RULER_HEIGHT

        if (self.pixmap_dirty or self.waveform_pixmap is None or 
            self._last_rendered_width != width or 
            self._last_rendered_height != height or
            self._last_rendered_scroll != self.scroll_offset or
            self._last_rendered_zoom != self.zoom_level):
            
            self.waveform_pixmap = self.render_waveform_buffer(width, height)
            self._last_rendered_width = width
            self._last_rendered_height = height
            self._last_rendered_scroll = self.scroll_offset
            self._last_rendered_zoom = self.zoom_level
            self.buffered_total_width = width
            self.pixmap_dirty = False

        if self.waveform_pixmap is not None:
            painter.drawPixmap(0, 0, self.waveform_pixmap)

        ruler_rect = QRectF(0, 0, width, self.RULER_HEIGHT)
        painter.fillRect(ruler_rect, self.tokens.ruler_background_color())
        painter.setPen(self.tokens.ruler_divider_pen())
        painter.drawLine(QPointF(0, self.RULER_HEIGHT), QPointF(width, self.RULER_HEIGHT))

        visible_dur = self.visible_duration()
        target_ticks = max(2, width // 100)
        base_interval = visible_dur / target_ticks

        nice_intervals = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
        chosen_interval = nice_intervals[-1]
        for step in nice_intervals:
            if base_interval <= step:
                chosen_interval = step
                break

        painter.setFont(self.font())
        painter.setPen(self.tokens.ruler_tick_pen())

        start_tick = (self.scroll_offset // chosen_interval) * chosen_interval
        t = start_tick

        while t <= self.scroll_offset + visible_dur:
            x = self.time_to_x(t, width)
            if 0 <= x <= width:
                painter.drawLine(QPointF(x, self.RULER_HEIGHT - 6), QPointF(x, self.RULER_HEIGHT))

                mins = int(t // 60)
                secs = int(t % 60)
                hrs = int(mins // 60)
                mins = mins % 60

                label = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"
                text_rect = QRectF(x + 3, 2, 60, self.RULER_HEIGHT - 4)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

            t += chosen_interval

        audio_name = getattr(self, "audio_file_name", None)
        if audio_name:
            painter.setPen(self.tokens.pen(self.tokens.audio_label_text, 1.0))
            filename_rect = QRectF(8, self.RULER_HEIGHT + 4, 300, 18)
            painter.drawText(filename_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Audio: {audio_name}")

        if self.transcript_selection_range:
            sel_start, sel_end = self.transcript_selection_range
            sx = self.time_to_x(sel_start, width)
            ex = self.time_to_x(sel_end, width)
            left = max(0, min(width, sx))
            right = max(0, min(width, ex))
            if right > left:
                painter.fillRect(QRectF(left, self.RULER_HEIGHT, right-left, waveform_height), self.tokens.selection_rect_brush(is_transcript=True))
                painter.setPen(self.tokens.selection_rect_pen())
                painter.drawLine(QPointF(left, self.RULER_HEIGHT), QPointF(left, height))
                painter.drawLine(QPointF(right, self.RULER_HEIGHT), QPointF(right, height))

        # Draw active right-click drag selection with adjustable edge handles
        if self.selection_start is not None and self.selection_end is not None:
            sx = self.time_to_x(self.selection_start, width)
            ex = self.time_to_x(self.selection_end, width)
            left = max(0.0, min(float(width), min(sx, ex)))
            right = max(0.0, min(float(width), max(sx, ex)))
            if right > left:
                painter.fillRect(QRectF(left, self.RULER_HEIGHT, right - left, waveform_height), self.tokens.selection_rect_brush(is_transcript=False))
                painter.setPen(self.tokens.selection_rect_pen())
                painter.drawRect(QRectF(left, self.RULER_HEIGHT, right - left, waveform_height))
                painter.fillRect(QRectF(left - 3, self.RULER_HEIGHT, 6, waveform_height), self.tokens.selection_handle_brush())
                painter.fillRect(QRectF(right - 3, self.RULER_HEIGHT, 6, waveform_height), self.tokens.selection_handle_brush())

        for index, story in enumerate(self.stories):
            start_x = self.time_to_x(story.start, width)
            end_x = self.time_to_x(story.end, width)

            if end_x < 0 or start_x > width:
                continue

            is_selected = index in self.selected_story_indices
            rect_start = max(0, start_x)
            rect_end = min(width, end_x)

            painter.fillRect(
                QRectF(rect_start, self.RULER_HEIGHT, max(1, rect_end - rect_start), waveform_height),
                self.tokens.story_segment_brush(index, is_selected=is_selected),
            )

            # --- Audio Fade Ramps & Envelope Visualization ---
            if getattr(self, "show_audio_fades", False):
                fin = getattr(story, "fade_in", 0.0)
                fout = getattr(story, "fade_out", 0.0)
                fcurve = getattr(story, "fade_curve", "linear") or "linear"
                fcurve = str(fcurve).lower()
                story_dur = max(0.001, story.end - story.start)
                fin = max(0.0, min(fin, story_dur))
                fout = max(0.0, min(fout, max(0.0, story_dur - fin)))

                top_y = float(self.RULER_HEIGHT)
                bottom_y = float(height)

                fin_apex_x = self.time_to_x(story.start + fin, width)
                if fin > 0 and fin_apex_x >= 0 and start_x <= width:
                    in_table = _FADE_IN_CURVE_TABLES.get(fcurve, _FADE_IN_CURVE_TABLES["linear"])
                    in_path = QPainterPath()
                    in_path.moveTo(start_x, bottom_y)
                    dx = fin_apex_x - start_x
                    dy = bottom_y - top_y
                    for step_i, val in enumerate(in_table, 1):
                        px = start_x + (step_i / float(_FADE_STEPS)) * dx
                        py = bottom_y - val * dy
                        in_path.lineTo(px, py)

                    # Fill shaded polygon area under curve
                    fill_path = QPainterPath(in_path)
                    fill_path.lineTo(start_x, top_y)
                    fill_path.lineTo(start_x, bottom_y)
                    fill_path.closeSubpath()

                    painter.setBrush(self._fade_fill_brush_sel if is_selected else self._fade_fill_brush_unsel)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(fill_path)

                    # Smooth ramp stroke
                    painter.setPen(self._fade_in_ramp_pen_sel if is_selected else self._fade_in_ramp_pen_unsel)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(in_path)

                # Tactile Grab Handle for Fade-In at apex along top edge
                if 0 <= fin_apex_x <= width:
                    painter.setPen(self._fade_in_handle_pen_sel if is_selected else self._fade_in_handle_pen_unsel)
                    painter.setBrush(self._fade_in_handle_brush_sel if is_selected else self._fade_in_handle_brush_unsel)
                    painter.drawRoundedRect(QRectF(fin_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

                fout_apex_x = self.time_to_x(story.end - fout, width)
                if fout > 0 and end_x >= 0 and fout_apex_x <= width:
                    out_table = _FADE_OUT_CURVE_TABLES.get(fcurve, _FADE_OUT_CURVE_TABLES["linear"])
                    out_path = QPainterPath()
                    out_path.moveTo(fout_apex_x, top_y)
                    dx = end_x - fout_apex_x
                    dy = bottom_y - top_y
                    for step_i, val in enumerate(out_table, 1):
                        px = fout_apex_x + (step_i / float(_FADE_STEPS)) * dx
                        py = bottom_y - val * dy
                        out_path.lineTo(px, py)

                    fill_path = QPainterPath(out_path)
                    fill_path.lineTo(end_x, top_y)
                    fill_path.lineTo(fout_apex_x, top_y)
                    fill_path.closeSubpath()

                    painter.setBrush(self._fade_fill_brush_sel if is_selected else self._fade_fill_brush_unsel)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(fill_path)

                    # Smooth ramp stroke
                    painter.setPen(self._fade_out_ramp_pen_sel if is_selected else self._fade_out_ramp_pen_unsel)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(out_path)

                # Tactile Grab Handle for Fade-Out at apex along top edge
                if 0 <= fout_apex_x <= width:
                    painter.setPen(self._fade_out_handle_pen_sel if is_selected else self._fade_out_handle_pen_unsel)
                    painter.setBrush(self._fade_out_handle_brush_sel if is_selected else self._fade_out_handle_brush_unsel)
                    painter.drawRoundedRect(QRectF(fout_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

            painter.setPen(self.tokens.story_segment_pen(index, is_selected=is_selected))
            if 0 <= start_x <= width:
                painter.drawLine(QPointF(start_x, self.RULER_HEIGHT), QPointF(start_x, height))
            if 0 <= end_x <= width:
                painter.drawLine(QPointF(end_x, self.RULER_HEIGHT), QPointF(end_x, height))

        # Draw Playhead Line
        cursor_x = self.time_to_x(self.position, width)
        if 0 <= cursor_x <= width:
            painter.setPen(self.tokens.playhead_pen(2.0))
            painter.drawLine(QPointF(cursor_x, 0), QPointF(cursor_x, height))

        # Draw Background Task Status Banner (Waveform / Thumbnail Generation)
        if self.show_background_banner and self.background_status_text:
            painter.save()
            font = self.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(self.background_status_text)
            badge_w = text_w + 24
            badge_h = 24
            badge_x = (width - badge_w) / 2.0
            badge_y = self.RULER_HEIGHT + 8

            badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
            painter.setPen(self.tokens.pen(self.tokens.status_banner_border, 1.5))
            painter.setBrush(self.tokens.brush(self.tokens.status_banner_bg, 230))
            painter.drawRoundedRect(badge_rect, 4.0, 4.0)

            painter.setPen(self.tokens.color(self.tokens.status_banner_text))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.background_status_text)
            painter.restore()


class TimelineResizeHandle(QWidget):
    """Visual drag-handle at the bottom of the timeline allowing vertical resizing."""
    def __init__(self, target_widget, parent=None):
        super().__init__(parent or target_widget)
        self.target_widget = target_widget
        self.setFixedHeight(7)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setToolTip("Drag down/up to resize timeline height")
        self._dragging = False
        self._start_y = 0
        self._start_h = 140

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Background bar
        is_dark = self.palette().window().color().value() < 128
        bg_color = QColor("#161b22") if is_dark else QColor("#e1e4e8")
        painter.fillRect(self.rect(), bg_color)

        # Center grip pill
        grip_color = QColor("#484f58") if is_dark else QColor("#8c959f")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grip_color)
        cx = self.width() // 2
        cy = self.height() // 2
        painter.drawRoundedRect(QRectF(cx - 24, cy - 1.5, 48, 3), 1.5, 1.5)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            self._start_h = self.target_widget.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            cur_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            delta = int(cur_y - self._start_y)
            new_h = max(90, min(500, self._start_h + delta))
            if new_h != self.target_widget.height():
                self.target_widget.setFixedHeight(new_h)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            try:
                settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                settings.setValue("timeline_height", self.target_widget.height())
                settings.sync()
            except Exception:
                pass
            event.accept()
            return
        super().mouseReleaseEvent(event)


class TimelineOverviewBar(QWidget):
    """Interactive navigation overview pill below the timeline with drag-to-zoom edge handles."""
    valueChanged = Signal(int)

    HANDLE_WIDTH = 7
    BAR_HEIGHT = 16

    def __init__(self, canvas, parent=None, tokens=None):
        super().__init__(parent)
        self.canvas = canvas
        self.tokens = tokens if tokens is not None else ThemeTokens()
        self.setFixedHeight(self.BAR_HEIGHT)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._dragging = None  # None, 'pan', 'left_handle', 'right_handle'
        self._drag_start_x = 0
        self._drag_start_offset = 0.0
        self._drag_fixed_left = 0.0
        self._drag_fixed_right = 0.0
        self._hover_handle = None

        if hasattr(self.canvas, "scrollOffsetChanged"):
            self.canvas.scrollOffsetChanged.connect(lambda _: self.update())
        if hasattr(self.canvas, "zoomChanged"):
            self.canvas.zoomChanged.connect(self.update)

    def get_pill_rect(self):
        w = max(1, self.width())
        dur = max(0.001, getattr(self.canvas, "duration", 1.0))
        vis = min(dur, max(0.001, self.canvas.visible_duration()))
        offset = max(0.0, min(dur - vis, getattr(self.canvas, "scroll_offset", 0.0)))

        pill_x = (offset / dur) * w
        pill_w = max(16.0, (vis / dur) * w)
        if pill_x + pill_w > w:
            pill_x = max(0.0, w - pill_w)

        return QRectF(pill_x, 2.0, pill_w, max(4.0, self.height() - 4.0))

    def _hit_test(self, pos_x):
        pill = self.get_pill_rect()
        if not pill.contains(QPointF(pos_x, self.height() / 2.0)):
            return 'track'

        # Left edge handle hit (resizable)
        if abs(pos_x - pill.left()) <= self.HANDLE_WIDTH:
            return 'left'
        # Right edge handle hit (resizable)
        if abs(pos_x - pill.right()) <= self.HANDLE_WIDTH:
            return 'right'

        return 'pill'

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            w = max(1, self.width())
            h = max(1, self.height())
            dur = max(0.001, getattr(self.canvas, "duration", 1.0))

            is_dark = self.palette().window().color().value() < 128

            # 1. Track background
            track_bg = QColor("#161b22") if is_dark else QColor("#e8ecf1")
            track_border = QColor("#21262d") if is_dark else QColor("#d0d7de")
            painter.setPen(QPen(track_border, 1.0))
            painter.setBrush(track_bg)
            painter.drawRoundedRect(QRectF(0.5, 1.0, w - 1.0, h - 2.0), 3.0, 3.0)

            # 2. Mini story segments in overview
            stories = getattr(self.canvas, "stories", [])
            if stories and dur > 0:
                for s_idx, story in enumerate(stories):
                    s_start = max(0.0, min(dur, getattr(story, "start", 0.0)))
                    s_end = max(s_start, min(dur, getattr(story, "end", 0.0)))
                    if s_end > s_start:
                        sx = (s_start / dur) * w
                        sw = max(2.0, ((s_end - s_start) / dur) * w)
                        s_color = self.tokens.story_segment_color(s_idx, alpha=110 if is_dark else 130)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(s_color)
                        painter.drawRect(QRectF(sx, 3.0, sw, h - 6.0))

            # 3. Viewport Pill
            pill = self.get_pill_rect()

            # Pill base style
            if self._dragging == 'pan' or self._hover_handle == 'pill':
                pill_bg = QColor("#3f4c60") if is_dark else QColor("#9aa8ba")
                pill_border = QColor("#58a6ff") if is_dark else QColor("#0969da")
            else:
                pill_bg = QColor("#303846") if is_dark else QColor("#afbccb")
                pill_border = QColor("#485569") if is_dark else QColor("#8c99a8")

            painter.setPen(QPen(pill_border, 1.0))
            painter.setBrush(pill_bg)
            painter.drawRoundedRect(pill, 4.0, 4.0)

            # 4. Resizable Left & Right edge grab handles
            left_h_active = (self._hover_handle == 'left' or self._dragging == 'left_handle')
            right_h_active = (self._hover_handle == 'right' or self._dragging == 'right_handle')

            # Left handle styling
            if left_h_active:
                painter.setBrush(QColor("#38bdf8" if is_dark else "#0284c7"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(pill.left(), pill.top(), 5.0, pill.height()), 2.0, 2.0)
            else:
                painter.setPen(QPen(QColor("#8b949e" if is_dark else "#ffffff"), 1.2))
                mid_y = pill.top() + pill.height() / 2.0
                painter.drawLine(QPointF(pill.left() + 3.0, mid_y - 3.0), QPointF(pill.left() + 3.0, mid_y + 3.0))

            # Right handle styling
            if right_h_active:
                painter.setBrush(QColor("#38bdf8" if is_dark else "#0284c7"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(pill.right() - 5.0, pill.top(), 5.0, pill.height()), 2.0, 2.0)
            else:
                painter.setPen(QPen(QColor("#8b949e" if is_dark else "#ffffff"), 1.2))
                mid_y = pill.top() + pill.height() / 2.0
                painter.drawLine(QPointF(pill.right() - 3.0, mid_y - 3.0), QPointF(pill.right() - 3.0, mid_y + 3.0))

            # 5. Playhead indicator tick
            pos = getattr(self.canvas, "position", 0.0)
            if 0 <= pos <= dur:
                cur_x = (pos / dur) * w
                painter.setPen(QPen(QColor("#ef4444" if is_dark else "#dc2626"), 1.5))
                painter.drawLine(QPointF(cur_x, 1.0), QPointF(cur_x, h - 1.0))
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos_x = event.position().x()
            w = max(1, self.width())
            dur = max(0.001, getattr(self.canvas, "duration", 1.0))
            hit = self._hit_test(pos_x)

            if hit == 'left':
                self._dragging = 'left_handle'
                self._drag_start_x = pos_x
                self._drag_fixed_right = self.canvas.scroll_offset + self.canvas.visible_duration()
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.update()
                event.accept()
                return

            elif hit == 'right':
                self._dragging = 'right_handle'
                self._drag_start_x = pos_x
                self._drag_fixed_left = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.update()
                event.accept()
                return

            elif hit == 'pill':
                self._dragging = 'pan'
                self._drag_start_x = pos_x
                self._drag_start_offset = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                event.accept()
                return

            elif hit == 'track':
                # Center viewport around clicked position
                clicked_time = (pos_x / w) * dur
                vis = self.canvas.visible_duration()
                self.canvas.scroll_offset = clicked_time - (vis / 2.0)
                self.canvas.clamp_scroll_offset()
                self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
                self.canvas.pixmap_dirty = True
                self.canvas.update()

                self._dragging = 'pan'
                self._drag_start_x = pos_x
                self._drag_start_offset = self.canvas.scroll_offset
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos_x = event.position().x()
        w = max(1, self.width())
        dur = max(0.001, getattr(self.canvas, "duration", 1.0))

        if self._dragging == 'pan':
            dx = pos_x - self._drag_start_x
            dt = (dx / w) * dur
            self.canvas.scroll_offset = self._drag_start_offset + dt
            self.canvas.clamp_scroll_offset()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        elif self._dragging == 'left_handle':
            new_left_time = max(0.0, min(self._drag_fixed_right - 0.1, (pos_x / w) * dur))
            new_vis_dur = max(0.05, self._drag_fixed_right - new_left_time)
            min_vis = dur / self.canvas.max_zoom
            max_vis = dur / self.canvas.min_zoom
            new_vis_dur = max(min_vis, min(max_vis, new_vis_dur))
            new_left_time = max(0.0, self._drag_fixed_right - new_vis_dur)

            self.canvas.zoom_level = max(self.canvas.min_zoom, min(self.canvas.max_zoom, dur / new_vis_dur))
            self.canvas.scroll_offset = new_left_time
            self.canvas.clamp_scroll_offset()
            self.canvas.zoomChanged.emit()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        elif self._dragging == 'right_handle':
            new_right_time = min(dur, max(self._drag_fixed_left + 0.1, (pos_x / w) * dur))
            new_vis_dur = max(0.05, new_right_time - self._drag_fixed_left)
            min_vis = dur / self.canvas.max_zoom
            max_vis = dur / self.canvas.min_zoom
            new_vis_dur = max(min_vis, min(max_vis, new_vis_dur))

            self.canvas.zoom_level = max(self.canvas.min_zoom, min(self.canvas.max_zoom, dur / new_vis_dur))
            self.canvas.scroll_offset = self._drag_fixed_left
            self.canvas.clamp_scroll_offset()
            self.canvas.zoomChanged.emit()
            self.canvas.scrollOffsetChanged.emit(self.canvas.scroll_offset)
            self.canvas.pixmap_dirty = True
            self.canvas.update()
            self.update()
            event.accept()
            return

        hit = self._hit_test(pos_x)
        self._hover_handle = hit
        if hit in ('left', 'right'):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.setToolTip("Drag edge to zoom in or out")
        elif hit == 'pill':
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setToolTip("Drag pill to scroll timeline")
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip("Click to jump to point in timeline")
        self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging is not None:
            self._dragging = None
            pos_x = event.position().x()
            hit = self._hit_test(pos_x)
            if hit in ('left', 'right'):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif hit == 'pill':
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self._hover_handle = None
        self.update()
        super().leaveEvent(event)

    def setRange(self, min_val, max_val):
        self.update()

    def setPageStep(self, step):
        self.update()

    def setSingleStep(self, step):
        self.update()

    def setValue(self, val):
        self.update()


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



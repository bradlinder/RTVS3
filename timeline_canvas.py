"""TimelineCanvas: Interactive timeline widget rendering time rulers, waveforms, video thumbnails, and story segments."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
import math
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QToolTip, QWidget

from theme_tokens import ThemeTokens
from story_widgets import StoryFadesChangeCommand
from timeline_envelope import build_waveform_pyramid

# Precomputed fade lookup tables for 60+ FPS curve rendering (16 segments per envelope)
_FADE_STEPS = 16
from core_utils import calculate_fade_curve_factor, calculate_fade_out_factor
_FADE_IN_CURVE_TABLES = {
    c: [calculate_fade_curve_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}
_FADE_OUT_CURVE_TABLES = {
    c: [calculate_fade_out_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}


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
        self.active_fade_target = None
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
        if not getattr(self, "enable_magnetic_snapping", True):
            return raw_time

        width = width or max(1, self.width())
        vis_dur = max(0.001, self.visible_duration())
        threshold_dt = (pixel_threshold / max(1, width)) * vis_dur

        snap_points = []
        if hasattr(self, "position") and self.position is not None:
            snap_points.append(float(self.position))
        if getattr(self, "selection_start", None) is not None:
            snap_points.append(float(self.selection_start))
        if getattr(self, "selection_end", None) is not None:
            snap_points.append(float(self.selection_end))

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

            fin_x = self.time_to_x(story.start + fin, width)
            if abs(pos_x - fin_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_in")

            fout_x = self.time_to_x(story.end - fout, width)
            if abs(pos_x - fout_x) <= self.FADE_HANDLE_THRESHOLD:
                return (index, "fade_out")
        return None

    def find_story_at_time(self, time):
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
            focus_time = getattr(self, "position", 0.0)
            if focus_time is None:
                focus_time = 0.0

        if center_x is None:
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
        h_delta_px = event.pixelDelta().x() if hasattr(event, "pixelDelta") else 0
        h_delta_angle = event.angleDelta().x() if hasattr(event, "angleDelta") else 0
        v_delta_angle = event.angleDelta().y() if hasattr(event, "angleDelta") else 0
        v_delta_px = event.pixelDelta().y() if hasattr(event, "pixelDelta") else 0
        modifiers = event.modifiers()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

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

        fade_hit = self.find_fade_handle_at_pos(pos_x, event.position().y(), width)
        if fade_hit:
            self.active_fade_target = fade_hit
            idx, f_type = fade_hit
            self._fade_drag_start_val = getattr(self.stories[idx], f_type, 0.0)
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            curr_t = max(0.0, min(self.duration, self.x_to_time(pos_x, width)))

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

            edge_hit = self.find_edge_at_pos(pos_x, width)
            if edge_hit:
                self.active_edge_target = edge_hit
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return

            self.selection_start = curr_t
            self.selection_end = curr_t
            self.active_selection_handle = "end"
            self.is_right_dragging = True
            self.selectionRangeChanged.emit(self.selection_start, self.selection_end)
            self.update()
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            time_val = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            self.position = time_val
            self.is_left_down = True
            self.is_scrubbing = True
            self.positionClicked.emit(time_val)
            self.scrubPositionChanged.emit(time_val)
            story_idx = self.find_story_at_time(time_val)
            if story_idx is not None:
                self.storyClicked.emit(story_idx)
            self.update()
            event.accept()
            return

    def mouseMoveEvent(self, event):
        pos_x = event.position().x()
        width = self.width()

        is_active_drag = bool(
            self.is_panning
            or self.is_right_dragging
            or (self.is_left_down and self.is_scrubbing)
            or self.active_fade_target
            or self.active_edge_target
        )

        if is_active_drag:
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

        if self.is_left_down and self.is_scrubbing:
            raw_time = max(0, min(self.duration, self.x_to_time(pos_x, width)))
            curr_time = self.snap_time(raw_time, width=width)
            self.scrubPositionChanged.emit(curr_time)
            event.accept()
            return

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
        time_val = max(0, min(self.duration, self.x_to_time(pos_x, width)))
        story_idx = self.find_story_at_time(time_val)

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

        if has_thumbs and self.show_waveform and thumbnail_height > 0 and waveform_height > 0:
            divider_y = thumbnail_y if self.thumbnail_position == "below" else waveform_y
            painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
            painter.drawLine(QPointF(0, divider_y), QPointF(width, divider_y))

        if has_thumbs and thumbnail_height > 0:
            if self.video_thumbnails:
                target_h = max(14, int((thumbnail_height - 6) * 0.88))
                vis_dur = max(0.001, self.visible_duration())

                sample_pix = self.video_thumbnails[0][1] if self.video_thumbnails else None
                aspect = (sample_pix.width() / max(1, sample_pix.height())) if (sample_pix and not sample_pix.isNull() and sample_pix.height() > 0) else (16.0 / 9.0)
                target_w = max(24, int(target_h * aspect))

                dt_buffer = (target_w / max(1, width)) * vis_dur * 1.5
                t_min = max(0.0, self.scroll_offset - dt_buffer)
                t_max = min(self.duration, self.scroll_offset + vis_dur + dt_buffer)

                ts_list = [item[0] for item in self.video_thumbnails]
                start_idx = max(0, bisect_left(ts_list, t_min) - 1)
                end_idx = min(len(self.video_thumbnails), bisect_right(ts_list, t_max) + 1)

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
                    if draw_x < (last_drawn_right + min_gap_px):
                        continue

                    draw_y = thumbnail_y + (thumbnail_height - scaled.height()) // 2
                    painter.drawPixmap(draw_x, int(draw_y), scaled)
                    painter.setPen(self.tokens.pen(self.tokens.border_subtle, 1.0))
                    painter.drawRect(draw_x, int(draw_y), scaled.width(), scaled.height())
                    last_drawn_right = draw_x + scaled.width()
            elif "thumbnails" in self.active_background_tasks or is_video_mode:
                win = self.window()
                is_es = getattr(win, "language", "en") == "es"
                gen_text = "Generando miniaturas de video..." if is_es else "Generating video thumbnails..."
                
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

        nice_intervals = [0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
        chosen_interval = nice_intervals[-1]
        for step in nice_intervals:
            if base_interval <= step:
                chosen_interval = step
                break

        painter.setFont(self.font())
        painter.setPen(self.tokens.ruler_tick_pen())

        start_tick = math.floor(self.scroll_offset / chosen_interval) * chosen_interval
        t = start_tick

        while t <= self.scroll_offset + visible_dur + (chosen_interval * 0.1):
            t_rounded = round(t, 4)
            x = self.time_to_x(t_rounded, width)
            if 0 <= x <= width:
                painter.drawLine(QPointF(x, self.RULER_HEIGHT - 6), QPointF(x, self.RULER_HEIGHT))

                if chosen_interval < 1.0:
                    total_sec = abs(t_rounded)
                    hrs = int(total_sec // 3600)
                    mins = int((total_sec % 3600) // 60)
                    secs = total_sec % 60
                    sec_str = f"{secs:04.1f}" if chosen_interval >= 0.2 else f"{secs:05.2f}"
                    label = f"{hrs}:{mins:02d}:{sec_str}" if hrs > 0 else f"{mins:02d}:{sec_str}"
                else:
                    mins = int(t_rounded // 60)
                    secs = int(t_rounded % 60)
                    hrs = int(mins // 60)
                    mins = mins % 60
                    label = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

                text_rect = QRectF(x + 3, 2, 70 if chosen_interval < 1.0 else 60, self.RULER_HEIGHT - 4)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

            t += chosen_interval

        audio_name = getattr(self, "audio_file_name", None)
        if audio_name:
            painter.setPen(self.tokens.pen(self.tokens.audio_label_text, 1.0))
            filename_rect = QRectF(8, self.RULER_HEIGHT + 4, 300, 18)
            painter.drawText(filename_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Audio: {audio_name}")

        if self.transcript_selection_range and not self.is_right_dragging and (self.selection_start is None or self.selection_end is None):
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

                    fill_path = QPainterPath(in_path)
                    fill_path.lineTo(start_x, top_y)
                    fill_path.lineTo(start_x, bottom_y)
                    fill_path.closeSubpath()

                    painter.setBrush(self._fade_fill_brush_sel if is_selected else self._fade_fill_brush_unsel)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(fill_path)

                    painter.setPen(self._fade_in_ramp_pen_sel if is_selected else self._fade_in_ramp_pen_unsel)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(in_path)

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

                    painter.setPen(self._fade_out_ramp_pen_sel if is_selected else self._fade_out_ramp_pen_unsel)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(out_path)

                if 0 <= fout_apex_x <= width:
                    painter.setPen(self._fade_out_handle_pen_sel if is_selected else self._fade_out_handle_pen_unsel)
                    painter.setBrush(self._fade_out_handle_brush_sel if is_selected else self._fade_out_handle_brush_unsel)
                    painter.drawRoundedRect(QRectF(fout_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

            painter.setPen(self.tokens.story_segment_pen(index, is_selected=is_selected))
            if 0 <= start_x <= width:
                painter.drawLine(QPointF(start_x, self.RULER_HEIGHT), QPointF(start_x, height))
            if 0 <= end_x <= width:
                painter.drawLine(QPointF(end_x, self.RULER_HEIGHT), QPointF(end_x, height))

        cursor_x = self.time_to_x(self.position, width)
        if 0 <= cursor_x <= width:
            painter.setPen(self.tokens.playhead_pen(2.0))
            painter.drawLine(QPointF(cursor_x, 0), QPointF(cursor_x, height))

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

"""Timeline overview bar, mini-map navigator, and resize handle widgets."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QPointF, QRectF, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from prs_shared import INTERNAL_APP_ID, ThemeTokens


class TimelineResizeHandle(QWidget):
    """Visual drag-handle at the bottom of the timeline allowing vertical resizing."""

    def __init__(self, target_widget: QWidget, parent: Optional[QWidget] = None):
        super().__init__(parent or target_widget)
        self.target_widget = target_widget
        self.setFixedHeight(7)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setToolTip("Drag down/up to resize timeline height")
        self._dragging = False
        self._start_y = 0
        self._start_h = 140

    def paintEvent(self, event: Any):
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

    def mousePressEvent(self, event: Any):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            self._start_h = self.target_widget.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any):
        if self._dragging:
            cur_y = event.globalPosition().y() if hasattr(event, "globalPosition") else event.globalY()
            delta = int(cur_y - self._start_y)
            new_h = max(90, min(500, self._start_h + delta))
            if new_h != self.target_widget.height():
                self.target_widget.setFixedHeight(new_h)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any):
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

    def __init__(self, canvas: Any, parent: Optional[QWidget] = None, tokens: Optional[ThemeTokens] = None):
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

    def get_pill_rect(self) -> QRectF:
        w = max(1, self.width())
        dur = max(0.001, getattr(self.canvas, "duration", 1.0))
        vis_dur = max(0.001, self.canvas.visible_duration())
        scroll_off = max(0.0, self.canvas.scroll_offset)

        pill_w = max(16.0, (vis_dur / dur) * w)
        pill_x = min(w - pill_w, (scroll_off / dur) * w)
        return QRectF(pill_x, 2.0, pill_w, self.height() - 4.0)

    def _hit_test(self, pos_x: float) -> Optional[str]:
        pill = self.get_pill_rect()
        if not pill.contains(pos_x, self.height() / 2.0):
            return 'track'

        # Check handles
        if pos_x <= pill.left() + self.HANDLE_WIDTH:
            return 'left'
        elif pos_x >= pill.right() - self.HANDLE_WIDTH:
            return 'right'
        else:
            return 'pill'

    def paintEvent(self, event: Any):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        try:
            w = max(1, self.width())
            h = self.height()
            dur = max(0.001, getattr(self.canvas, "duration", 1.0))
            is_dark = self.palette().window().color().value() < 128

            # 1. Track background
            track_bg = QColor("#0d1117") if is_dark else QColor("#e8ecf1")
            painter.fillRect(self.rect(), track_bg)

            # 2. Render miniature story regions inside overview track
            stories = getattr(self.canvas, "stories", [])
            for st in stories:
                st_start = max(0.0, getattr(st, "start", 0.0))
                st_end = min(dur, getattr(st, "end", dur))
                if st_end > st_start:
                    sx = (st_start / dur) * w
                    sw = max(2.0, ((st_end - st_start) / dur) * w)
                    st_color = QColor(getattr(st, "color", "#3b82f6"))
                    st_color.setAlpha(120 if is_dark else 150)
                    painter.fillRect(QRectF(sx, 3.0, sw, h - 6.0), st_color)

            # 3. Viewport Pill
            pill = self.get_pill_rect()
            if self._dragging is not None or self._hover_handle == 'pill':
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

    def mousePressEvent(self, event: Any):
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

    def mouseMoveEvent(self, event: Any):
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

    def mouseReleaseEvent(self, event: Any):
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

    def leaveEvent(self, event: Any):
        self._hover_handle = None
        self.update()
        super().leaveEvent(event)

    def setRange(self, min_val: int, max_val: int):
        self.update()

    def setPageStep(self, step: int):
        self.update()

    def setSingleStep(self, step: int):
        self.update()

    def setValue(self, val: int):
        self.update()

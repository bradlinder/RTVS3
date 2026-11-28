"""Non-focus-stealing click-to-drop-down calendar & time picker for WordPress publication dates."""
from __future__ import annotations

import os
import weakref
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import QDate, QEvent, QPoint, QTime, Qt
from PySide6.QtWidgets import (
    QApplication, QCalendarWidget, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTimeEdit, QVBoxLayout, QWidget,
)

from plugins.wordpress.episode_lookup import normalize_wp_iso_date

try:
    from shiboken6 import isValid as _shiboken_is_valid
except Exception:
    _shiboken_is_valid = None


def _is_qt_valid(obj: Any) -> bool:
    """Return False when `obj` is None or its underlying C++ Qt object was deleted."""
    if obj is None:
        return False
    if _shiboken_is_valid is not None:
        try:
            return bool(_shiboken_is_valid(obj))
        except Exception:
            return False
    return True


def _is_widget_or_descendant(candidate: Any, ancestor: Any) -> bool:
    """Return True if `candidate` is `ancestor` or nested beneath it in the widget tree."""
    cur = candidate
    hops = 0
    while cur is not None and hops < 32:
        if cur is ancestor:
            return True
        try:
            cur = cur.parentWidget()
        except Exception:
            break
        hops += 1
    return False


class _PublicationDatePickerPopup(QFrame):
    """Frameless, non-focus-stealing calendar and 24-hour time dropdown for PublicationDateLineEdit."""

    def __init__(self, anchor: "PublicationDateLineEdit", parent: Optional[QWidget] = None):
        win = anchor.window() if (anchor is not None and hasattr(anchor, "window")) else None
        popup_parent = win if (win is not None and isinstance(win, QWidget)) else parent
        super().__init__(popup_parent)
        self._anchor = anchor
        self._watched_window: Optional[QWidget] = None
        self._filters_installed = False
        self._syncing = False

        self.setObjectName("wp_pub_date_picker_popup")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.calendar = QCalendarWidget(self)
        if hasattr(self.calendar, "setGridVisible"):
            self.calendar.setGridVisible(True)
        if hasattr(self.calendar, "setVerticalHeaderFormat"):
            self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        if hasattr(self.calendar, "weekdayTextFormat") and hasattr(self.calendar, "setWeekdayTextFormat"):
            weekday_fmt = self.calendar.weekdayTextFormat(Qt.DayOfWeek.Monday)
            self.calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekday_fmt)
            self.calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekday_fmt)
        layout.addWidget(self.calendar)

        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        time_row.addWidget(QLabel("Time (24h):", self))
        self.time_edit = QTimeEdit(self)
        if hasattr(self.time_edit, "setDisplayFormat"):
            self.time_edit.setDisplayFormat("HH:mm")
        time_row.addWidget(self.time_edit)
        time_row.addStretch()
        layout.addLayout(time_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.now_btn = QPushButton("Now", self)
        self.clear_btn = QPushButton("Clear", self)
        self.done_btn = QPushButton("Done", self)
        btn_row.addWidget(self.now_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.done_btn)
        layout.addLayout(btn_row)

        self.calendar.clicked.connect(self._on_date_clicked)
        self.calendar.activated.connect(self._on_date_activated)
        self.time_edit.timeChanged.connect(self._on_time_changed)
        self.now_btn.clicked.connect(self._on_now_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.done_btn.clicked.connect(self._on_done_clicked)

    def sync_from_text(self, raw_text: str) -> None:
        """Align calendar and time widgets to `raw_text`, or today's date/time when blank."""
        raw = str(raw_text or "").strip()
        if not raw:
            dt = datetime.now()
        else:
            try:
                iso = normalize_wp_iso_date(raw)
            except ValueError:
                return
            dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S") if iso else datetime.now()

        self._syncing = True
        try:
            self.calendar.setSelectedDate(QDate(dt.year, dt.month, dt.day))
            self.time_edit.setTime(QTime(dt.hour, dt.minute))
        finally:
            self._syncing = False

    def _apply_selected_datetime(self) -> None:
        if not _is_qt_valid(self._anchor):
            return
        qdate = self.calendar.selectedDate()
        qtime = self.time_edit.time()
        formatted = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d} {qtime.hour():02d}:{qtime.minute():02d}"
        self._syncing = True
        try:
            self._anchor.setText(formatted)
            self._anchor.textEdited.emit(formatted)
        finally:
            self._syncing = False

    def _on_date_clicked(self, qdate: Any = None) -> None:
        if isinstance(qdate, QDate) and qdate.isValid():
            self._syncing = True
            try:
                self.calendar.setSelectedDate(qdate)
            finally:
                self._syncing = False
        self._apply_selected_datetime()

    def _on_date_activated(self, qdate: Any = None) -> None:
        self._on_date_clicked(qdate)
        self.hide()

    def _on_time_changed(self, *_args: Any) -> None:
        if not self._syncing:
            self._apply_selected_datetime()

    def _on_now_clicked(self) -> None:
        now = datetime.now()
        self._syncing = True
        try:
            self.calendar.setSelectedDate(QDate(now.year, now.month, now.day))
            self.time_edit.setTime(QTime(now.hour, now.minute))
        finally:
            self._syncing = False
        self._apply_selected_datetime()

    def _on_clear_clicked(self) -> None:
        if _is_qt_valid(self._anchor):
            self._anchor.setText("")
            self._anchor.textEdited.emit("")
        self.hide()

    def _on_done_clicked(self) -> None:
        self.hide()
        if _is_qt_valid(self._anchor):
            self._anchor.setFocus(Qt.FocusReason.PopupFocusReason)

    def _install_filters(self) -> None:
        if self._filters_installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        win = self._anchor.window() if _is_qt_valid(self._anchor) and hasattr(self._anchor, "window") else None
        if win is not None and _is_qt_valid(win) and win is not self:
            win.installEventFilter(self)
            self._watched_window = win
        self._filters_installed = True

    def _remove_filters(self) -> None:
        if not self._filters_installed:
            return
        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except Exception:
                pass
        if _is_qt_valid(self._watched_window):
            try:
                self._watched_window.removeEventFilter(self)
            except Exception:
                pass
        self._watched_window = None
        self._filters_installed = False

    def show_for_anchor(self) -> None:
        """Position below (or above if needed) the anchor QLineEdit without stealing focus."""
        if not _is_qt_valid(self._anchor):
            return
        self.sync_from_text(self._anchor.text())
        self.adjustSize()
        sz = self.sizeHint()
        popup_w = max(260, sz.width())
        popup_h = max(240, sz.height())

        anchor_top_left = self._anchor.mapToGlobal(QPoint(0, 0))
        x = anchor_top_left.x()
        y = anchor_top_left.y() + self._anchor.height() + 2

        screen = QApplication.screenAt(anchor_top_left) or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            if y + popup_h > avail.bottom():
                above_y = anchor_top_left.y() - popup_h - 2
                if above_y >= avail.top():
                    y = above_y
            x = max(avail.left(), min(x, avail.right() - popup_w))

        self.move(x, y)
        self._install_filters()
        if os.environ.get("RTVS_TEST_MODE"):
            self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self.show()

    def hideEvent(self, event: Any) -> None:
        self._remove_filters()
        super().hideEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        if event is not None and event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.hide()
            if _is_qt_valid(self._anchor):
                self._anchor.setFocus(Qt.FocusReason.PopupFocusReason)
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        if not self.isVisible() or event is None:
            return False
        etype = event.type()
        if obj is self._watched_window and etype in (
            QEvent.Type.Move,
            QEvent.Type.Resize,
            QEvent.Type.Hide,
            QEvent.Type.Close,
        ):
            self.hide()
            return False
        if etype == QEvent.Type.MouseButtonPress:
            global_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            target = QApplication.widgetAt(global_pos)
            if target is not None and (
                _is_widget_or_descendant(target, self)
                or (_is_qt_valid(self._anchor) and _is_widget_or_descendant(target, self._anchor))
            ):
                return False
            self.hide()
        return False


class PublicationDateLineEdit(QLineEdit):
    """Editable QLineEdit that opens a non-intrusive calendar/time dropdown on click."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._picker_popup: Optional[_PublicationDatePickerPopup] = None
        self.textEdited.connect(self._on_text_edited_sync_popup)
        self_ref = weakref.ref(self)

        def _cleanup(*_args: Any) -> None:
            inst = self_ref()
            if inst is not None:
                inst.close_picker()

        self.destroyed.connect(_cleanup)

    def _ensure_popup(self) -> _PublicationDatePickerPopup:
        if not _is_qt_valid(self._picker_popup):
            self._picker_popup = _PublicationDatePickerPopup(anchor=self)
        return self._picker_popup

    def open_picker(self) -> Optional[_PublicationDatePickerPopup]:
        """Open the calendar/time dropdown anchored to this input without stealing focus."""
        if not self.isEnabled() or self.isReadOnly():
            return None
        popup = self._ensure_popup()
        popup.show_for_anchor()
        return popup

    def close_picker(self) -> None:
        """Close the dropdown if currently open."""
        if _is_qt_valid(self._picker_popup):
            self._picker_popup.hide()

    def _on_text_edited_sync_popup(self, text: str) -> None:
        if _is_qt_valid(self._picker_popup) and self._picker_popup.isVisible():
            self._picker_popup.sync_from_text(text)

    def mousePressEvent(self, event: Any) -> None:
        super().mousePressEvent(event)
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.open_picker()

    def keyPressEvent(self, event: Any) -> None:
        if event is not None:
            key = event.key()
            popup_open = _is_qt_valid(self._picker_popup) and self._picker_popup.isVisible()
            if key == Qt.Key.Key_Escape and popup_open:
                self.close_picker()
                event.accept()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and popup_open:
                self.close_picker()
                event.accept()
                return
            if key == Qt.Key.Key_Down and (
                bool(event.modifiers() & Qt.KeyboardModifier.AltModifier) or not self.text().strip()
            ):
                self.open_picker()
                event.accept()
                return
        super().keyPressEvent(event)


__all__ = ["PublicationDateLineEdit"]

"""
transcript_editor.py - Interactive Transcript Editor & Viewer Components
Extracted from prs_shared.py as part of Phase 2 Modularization (Milestone 3.2).
Refactored into dedicated mixins (Milestone 3.5 Wave 3):
- transcript_editor_dialogs.py: FindReplaceDialog, TranscriptSelectionBubble
- transcript_styles.py: transcript_text_view_stylesheet, clean_dark_mode_clipboard_html
- transcript_context_menu_mixin.py: TranscriptContextMenuMixin
- transcript_formatting_mixin.py: TranscriptFormattingMixin
- transcript_timeline_sync_mixin.py: TranscriptTimelineSyncMixin

Provides:
- FindReplaceDialog: Modeless find-and-replace dialog for QTextEdit/InteractiveTranscriptEdit
- TranscriptSelectionBubble: Floating quick-action toolbar on transcript selection
- InteractiveTranscriptEdit: Rich interactive transcript editor with word-level playback
  synchronization, speaker attribution, search highlighting, and custom context menus
- transcript_text_view_stylesheet: Dynamic theme/font stylesheet generator for transcript views
- clean_dark_mode_clipboard_html: Normalizes plain white text to #000000 while preserving rich styles
"""

import sys
import os
import re
import time
import html
from bisect import bisect_right
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    from PySide6.QtCore import (
        Qt,
        Signal,
        QTimer,
        QSettings,
        QPointF,
        QRectF,
        QUrl,
        QEvent,
        QMimeData,
    )
    from PySide6.QtGui import (
        QPainter,
        QPainterPath,
        QPen,
        QColor,
        QFont,
        QTextCursor,
        QTextCharFormat,
        QAction,
        QCursor,
        QKeySequence,
        QShortcut,
        QBrush,
        QTextDocument,
        QKeyEvent,
        QMouseEvent,
        QWheelEvent,
        QDragEnterEvent,
        QDropEvent,
    )
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QMenu,
        QToolTip,
        QDialog,
        QFrame,
        QToolButton,
        QTextEdit,
        QLineEdit,
        QCheckBox,
        QPushButton,
        QMessageBox,
        QScrollBar,
        QApplication,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import (
        Qt, QTimer, Signal, QSettings, QPointF, QRectF, QUrl, QEvent, QMimeData
    )
    from PySide6.QtGui import (
        QPainter, QPainterPath, QPen, QColor, QFont, QTextCursor, QTextCharFormat,
        QAction, QCursor, QKeySequence, QShortcut, QBrush, QTextDocument,
        QKeyEvent, QMouseEvent, QWheelEvent, QDragEnterEvent, QDropEvent
    )
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QMenu, QToolTip,
        QDialog, QFrame, QToolButton, QTextEdit, QLineEdit, QCheckBox, QPushButton,
        QMessageBox, QScrollBar, QApplication,
    )

from core_utils import format_time

# Re-exported modular dialogs and stylesheet helpers (Milestone 3.5)
from transcript_editor_dialogs import FindReplaceDialog, TranscriptSelectionBubble
from transcript_styles import transcript_text_view_stylesheet, clean_dark_mode_clipboard_html

# Mixins for domain behavior decomposition
from transcript_context_menu_mixin import TranscriptContextMenuMixin
from transcript_formatting_mixin import TranscriptFormattingMixin
from transcript_timeline_sync_mixin import TranscriptTimelineSyncMixin

__all__ = [
    "FindReplaceDialog",
    "TranscriptSelectionBubble",
    "transcript_text_view_stylesheet",
    "clean_dark_mode_clipboard_html",
    "InteractiveTranscriptEdit",
]


class InteractiveTranscriptEdit(
    TranscriptContextMenuMixin,
    TranscriptFormattingMixin,
    TranscriptTimelineSyncMixin,
    QTextEdit,
):
    linkClicked = Signal(QUrl)
    editingModeChanged = Signal(bool)
    formatChanged = Signal()
    requestInsertSpeaker = Signal(int, float, str)
    requestSplitAtCursor = Signal(int, float)
    requestRemoveSpeakerAtBlock = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.is_editing_mode = False
        self.setReadOnly(True)
        self.setTabChangesFocus(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAcceptDrops(True)

        self.current_theme = "dark"
        self.font_scale = 1.0
        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        self.anchor_ranges = {}
        self.time_anchor_index = []
        self.time_anchor_starts = []

        self.char_timestamp_map = []
        self._context_menu_cursor_position = None

        # Text selection state and preferences
        self.selection_mode = "replace"  # "replace" or "keep"
        self.saved_selections = []  # List of dicts for multi-selection mode
        self._is_left_down = False
        self._is_left_dragging = False
        self._left_press_pos = None
        self._pending_click_href = None
        self._is_right_down = False
        self._is_right_dragging = False
        self._right_press_pos = None
        self._right_press_cursor_pos = None
        self._suppress_next_context_menu = False

        # Floating Quick-Action Bubble (Milestone 3.12)
        self.selection_bubble = TranscriptSelectionBubble(self.viewport())
        self.selection_bubble.playRequested.connect(self._on_bubble_play)
        self.selection_bubble.storyRequested.connect(self._on_bubble_story)
        self.selection_bubble.noteRequested.connect(self._on_bubble_note)
        self.selection_bubble.cutRequested.connect(self._on_bubble_cut)
        self.selection_bubble.exportRequested.connect(self._on_bubble_export)
        self.selection_bubble.hide()

        self.apply_theme_style("dark")
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # Scroll stability & lock tracking
        self._is_scroll_locked = False
        self._scroll_lock_target_v = None
        self._scroll_lock_target_h = None
        self._scroll_lock_timer = None
        self._user_scrolled_recently = False

        if self.verticalScrollBar():
            self.verticalScrollBar().rangeChanged.connect(self._on_v_range_changed)
            self.verticalScrollBar().sliderPressed.connect(self._release_scroll_lock)

    def lock_scroll_position(self, v_val: int, h_val: int = 0, duration_ms: int = 400):
        """Pin vertical and horizontal scrollbars to exact pixel values during layout reflows.
        Automatically detaches when the layout stabilizes or when the user manually scrolls."""
        self._scroll_lock_target_v = max(0, int(v_val))
        self._scroll_lock_target_h = max(0, int(h_val))
        self._is_scroll_locked = True

        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()

        if v_bar:
            v_bar.setValue(self._scroll_lock_target_v)
        if h_bar:
            h_bar.setValue(self._scroll_lock_target_h)

        if not hasattr(self, "_scroll_lock_timer") or self._scroll_lock_timer is None:
            self._scroll_lock_timer = QTimer(self)
            self._scroll_lock_timer.setSingleShot(True)
            self._scroll_lock_timer.timeout.connect(self._release_scroll_lock)

        self._scroll_lock_timer.stop()
        self._scroll_lock_timer.start(max(50, int(duration_ms)))

    def _release_scroll_lock(self):
        self._is_scroll_locked = False
        self._scroll_lock_target_v = None
        self._scroll_lock_target_h = None

    def _on_v_range_changed(self, min_val, max_val):
        if getattr(self, "_is_scroll_locked", False) and self._scroll_lock_target_v is not None:
            v_bar = self.verticalScrollBar()
            if v_bar and v_bar.value() != self._scroll_lock_target_v:
                v_bar.setValue(self._scroll_lock_target_v)

    def focusInEvent(self, event):
        # Override QTextEdit's default focusInEvent which invokes ensureCursorVisible()
        # and causes unwanted viewport jumps when dialogs close.
        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()
        v_val = v_bar.value() if v_bar else 0
        h_val = h_bar.value() if h_bar else 0

        super().focusInEvent(event)

        if v_bar and v_bar.value() != v_val:
            v_bar.setValue(v_val)
        if h_bar and h_bar.value() != h_val:
            h_bar.setValue(h_val)

        # Defend against delayed Qt event-loop cursor visibility enforcement
        QTimer.singleShot(0, lambda: self._enforce_scroll_after_focus(v_val, h_val))

    def _enforce_scroll_after_focus(self, target_v: int, target_h: int):
        v_bar = self.verticalScrollBar()
        h_bar = self.horizontalScrollBar()
        if v_bar and v_bar.value() != target_v and not getattr(self, "_user_scrolled_recently", False):
            v_bar.setValue(target_v)
        if h_bar and h_bar.value() != target_h and not getattr(self, "_user_scrolled_recently", False):
            h_bar.setValue(target_h)

    def createMimeDataFromSelection(self):
        """Clean dark-mode white/light plain text colors to black (#000000) when copying.

        Preserves rich styling such as blue speaker labels, highlight backgrounds and text,
        bold, italic, underline, and timestamps so pasting into Word, Google Docs, or email
        pastes as clean, readable black text rather than invisible white-on-white text.
        """
        mime_data = super().createMimeDataFromSelection()
        if mime_data is not None and mime_data.hasHtml():
            theme = getattr(self, "current_theme", "dark")
            if theme in ("dark", "high_contrast"):
                raw_html = mime_data.html()
                cleaned_html = clean_dark_mode_clipboard_html(raw_html)
                mime_data.setHtml(cleaned_html)
        return mime_data

    def wheelEvent(self, event):
        # Manual user scroll cancels any active scroll lock
        self._release_scroll_lock()
        self._user_scrolled_recently = True
        QTimer.singleShot(500, lambda: setattr(self, "_user_scrolled_recently", False))
        super().wheelEvent(event)

    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            main_win = self.window()
            show_highlights = str(getattr(main_win, "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
            if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
                cursor = self.cursorForPosition(e.pos())
                cpos = cursor.position()
                matching_span = None
                for span in self.comment_spans:
                    if span["start"] <= cpos <= span["end"]:
                        matching_span = span
                        break
                if matching_span:
                    st = matching_span.get("start_time", 0.0)
                    m, s = divmod(int(st), 60)
                    h, m = divmod(m, 60)
                    time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

                    quote_txt = matching_span.get("selected_text", "").strip()
                    if quote_txt:
                        trunc = quote_txt[:90] + ("..." if len(quote_txt) > 90 else "")
                        quote_html = (
                            f"<div style='font-size: 11px; color: #94a3b8; font-style: italic; margin-bottom: 5px; "
                            f"border-left: 2px solid #f59e0b; padding-left: 6px;'>&ldquo;{html.escape(trunc)}&rdquo;</div>"
                        )
                    else:
                        quote_html = ""

                    c_body = html.escape(matching_span.get("comment", ""))
                    is_light = getattr(self, "current_theme", "dark") == "light"
                    bg_col = "#ffffff" if is_light else "#0f172a"
                    text_col = "#0f172a" if is_light else "#f8fafc"
                    border_col = "#d97706" if is_light else "#f59e0b"

                    tooltip_html = (
                        f"<div style='background-color: {bg_col}; color: {text_col}; border: 1.5px solid {border_col}; "
                        f"border-radius: 6px; padding: 7px 11px; font-family: sans-serif; max-width: 360px;'>"
                        f"<div style='font-weight: bold; color: {border_col}; margin-bottom: 4px; font-size: 12px;'>"
                        f"💬 Comment &bull; {time_str}</div>"
                        f"{quote_html}"
                        f"<div style='white-space: pre-wrap; line-height: 1.4; font-size: 12px; margin-bottom: 6px;'>{c_body}</div>"
                        f"<div style='font-size: 10px; color: #64748b; border-top: 1px solid rgba(245, 158, 11, 0.3); padding-top: 3px;'>"
                        f"Click highlight to open comment window &bull; Spacebar to play</div>"
                        f"</div>"
                    )
                    pos = e.globalPos() if hasattr(e, "globalPos") else (e.globalPosition().toPoint() if hasattr(e, "globalPosition") else self.mapToGlobal(e.pos()))
                    QToolTip.showText(pos, tooltip_html, self.viewport())
                    return True
            QToolTip.hideText()
        return super().event(e)

    def paintEvent(self, event):
        super().paintEvent(event)
        win = self.window()
        has_media = bool(getattr(win, "audio_file", None) or getattr(self, "audio_file", None))
        if has_media:
            return
        if self.document().isEmpty() or not self.toPlainText().strip():
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self.viewport().rect()

            card_w = min(540, rect.width() - 40)
            card_h = min(240, rect.height() - 40)
            if card_w > 140 and card_h > 90:
                card_x = rect.x() + (rect.width() - card_w) // 2
                card_y = rect.y() + (rect.height() - card_h) // 2
                card_rect = QRectF(card_x, card_y, card_w, card_h)

                is_dark = self.current_theme == "dark"
                pen = QPen(QColor("#3b82f6" if is_dark else "#2563eb"), 1.5, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                fill_color = QColor(30, 41, 59, 120) if is_dark else QColor(241, 245, 249, 180)
                painter.setBrush(fill_color)
                painter.drawRoundedRect(card_rect, 10.0, 10.0)

                wrap_flags = int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)

                title_font = QFont(self.font())
                title_font.setPointSize(12)
                title_font.setBold(True)
                painter.setFont(title_font)
                painter.setPen(QColor("#f8fafc" if is_dark else "#0f172a"))
                t_rect = QRectF(card_x + 16, card_y + 18, card_w - 32, 28)
                painter.drawText(t_rect, wrap_flags, "Drop an Audio or Video File Here to Begin")

                sub_font = QFont(self.font())
                sub_font.setPointSize(9)
                painter.setFont(sub_font)
                painter.setPen(QColor("#94a3b8" if is_dark else "#64748b"))
                s_rect = QRectF(card_x + 16, card_y + 48, card_w - 32, 60)
                painter.drawText(
                    s_rect,
                    wrap_flags,
                    "Supports all standard audio & video formats (WAV, MP3, MP4, MOV, MKV, FLAC, etc.)\nAuto-generates synchronized word-level transcription",
                )

                btn_font = QFont(self.font())
                btn_font.setPointSize(9)
                btn_font.setBold(True)
                painter.setFont(btn_font)
                btn_w = min(220, card_w - 40)
                btn_rect = QRectF(card_x + (card_w - btn_w) // 2, card_y + 120, btn_w, 32)
                painter.fillRect(btn_rect, QColor("#2563eb"))
                painter.setPen(QColor("#ffffff"))
                painter.drawRoundedRect(btn_rect, 5.0, 5.0)
                painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Open Media File... (Ctrl+O)")

                hint_font = QFont(self.font())
                hint_font.setPointSize(8)
                painter.setFont(hint_font)
                painter.setPen(QColor("#64748b"))
                h_rect = QRectF(card_x + 16, card_y + 166, card_w - 32, 24)
                painter.drawText(h_rect, wrap_flags, "Or click File > Open Media in the menu bar")
            painter.end()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                if u.isLocalFile():
                    path = u.toLocalFile()
                    win = self.window()
                    if hasattr(win, "load_media_file"):
                        win.load_media_file(path)
                        event.acceptProposedAction()
                        return
        super().dropEvent(event)

    def apply_theme_style(self, mode):
        self.current_theme = mode
        self.setStyleSheet(transcript_text_view_stylesheet(mode, 14 * self.font_scale))
        self.update_extra_selections()

    def set_font_scale(self, scale):
        """Set transcript font scale without affecting the rest of the UI."""
        self.font_scale = max(0.80, min(1.80, float(scale)))
        # Update the widget font as well as its stylesheet so QTextDocument's
        # inherited HTML text follows the scale consistently.
        font = QFont(self.font())
        font.setPointSizeF(16.0 * self.font_scale * 72.0 / 96.0)
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.setStyleSheet(transcript_text_view_stylesheet(self.current_theme, 14 * self.font_scale))
        self.update_extra_selections()

    def set_editing_mode(self, enabled):
        if self.is_editing_mode == enabled:
            return
        self.is_editing_mode = enabled
        self.setReadOnly(not enabled)
        if enabled:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.clear_highlight()
            self.setFocus()
        else:
            self.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
        self.setTabChangesFocus(False)
        self.editingModeChanged.emit(enabled)

    def mousePressEvent(self, event):
        if self.is_editing_mode:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            self._left_press_pos = pos
            self._is_left_down = True
            self._is_left_dragging = False
            self._pending_click_href = None

            # Check if clicked on a timestamp/word link
            hit_cursor = self.cursorForPosition(pos)
            href = hit_cursor.charFormat().anchorHref()
            if not href and hit_cursor.position() > 0:
                probe = QTextCursor(hit_cursor)
                probe.setPosition(max(0, hit_cursor.position() - 1))
                href = probe.charFormat().anchorHref()

            if href and (href.startswith("word:") or href.startswith("time:") or href.startswith("speaker:")):
                self._pending_click_href = href

            if self.selection_mode == "replace" and self.saved_selections:
                self.saved_selections = []
                self.update_extra_selections()

            super().mousePressEvent(event)
            return

        elif event.button() == Qt.MouseButton.RightButton:
            self._right_press_pos = pos
            self._is_right_down = True
            self._is_right_dragging = False
            self._right_press_cursor_pos = self.cursorForPosition(pos).position()
            self._suppress_next_context_menu = False
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_editing_mode:
            super().mouseMoveEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        drag_dist = QApplication.startDragDistance() if hasattr(QApplication, "startDragDistance") else 4
        if drag_dist < 4:
            drag_dist = 4

        if getattr(self, "_is_left_down", False):
            press_pos = getattr(self, "_left_press_pos", pos)
            if (pos - press_pos).manhattanLength() >= drag_dist:
                self._is_left_dragging = True
            super().mouseMoveEvent(event)
            return

        if getattr(self, "_is_right_down", False):
            press_pos = getattr(self, "_right_press_pos", pos)
            if (pos - press_pos).manhattanLength() >= drag_dist:
                self._is_right_dragging = True
                curr_pos = self.cursorForPosition(pos).position()
                start_pos = getattr(self, "_right_drag_start_cursor_pos", curr_pos)

                cursor = QTextCursor(self.document())
                cursor.setPosition(start_pos)
                cursor.setPosition(curr_pos, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                event.accept()
                return

        # Passive Hover: cursor shape indicator over comment highlights
        hit_cursor = self.cursorForPosition(pos)
        hit_pos = hit_cursor.position()
        over_comment = False
        show_highlights = str(getattr(self.window(), "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
        if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
            for span in self.comment_spans:
                if span["start"] <= hit_pos <= span["end"]:
                    over_comment = True
                    break
        if over_comment:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            href = hit_cursor.charFormat().anchorHref()
            if not href:
                self.viewport().unsetCursor()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        if not getattr(self, "is_editing_mode", False):
            self.viewport().unsetCursor()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_editing_mode:
            super().mouseReleaseEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = getattr(self, "_is_left_dragging", False)
            self._is_left_down = False
            self._is_left_dragging = False
            pending_href = getattr(self, "_pending_click_href", None)
            self._pending_click_href = None

            super().mouseReleaseEvent(event)

            cursor = self.textCursor()
            has_sel = cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0)

            if not was_dragging and not has_sel:
                # Single Left-Click without dragging -> check for comment highlight or seek/navigation
                if self.selection_mode == "replace":
                    self.clear_all_selections()

                hit_cursor = self.cursorForPosition(pos)
                hit_pos = hit_cursor.position()
                clicked_span = None
                show_highlights = str(getattr(self.window(), "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}
                if show_highlights and hasattr(self, "comment_spans") and self.comment_spans:
                    for span in self.comment_spans:
                        if span["start"] <= hit_pos <= span["end"]:
                            clicked_span = span
                            break

                if clicked_span:
                    main_win = self.window()
                    # 1. Open the comments window/pane if closed
                    if hasattr(main_win, "toggle_show_comments"):
                        main_win.toggle_show_comments(True)
                    # 2. Highlight and scroll to this comment card in comments panel
                    if hasattr(main_win, "comments_panel") and hasattr(main_win.comments_panel, "highlight_segment"):
                        main_win.comments_panel.highlight_segment(clicked_span["seg_idx"])
                    # 3. Seek to time position WITHOUT starting playback
                    seek_time = clicked_span["start_time"]
                    if hasattr(main_win, "seek_to"):
                        main_win.seek_to(seek_time)
                    if hasattr(main_win, "timeline") and hasattr(main_win.timeline, "ensure_position_visible"):
                        main_win.timeline.ensure_position_visible(seek_time)
                    event.accept()
                    return

                if pending_href and (pending_href.startswith("word:") or pending_href.startswith("time:") or pending_href.startswith("speaker:")):
                    self.linkClicked.emit(QUrl(pending_href))
                    event.accept()
                    return
                else:
                    href = hit_cursor.charFormat().anchorHref()
                    if href and (href.startswith("word:") or href.startswith("time:") or href.startswith("speaker:")):
                        self.linkClicked.emit(QUrl(href))
                        event.accept()
                        return
            else:
                # Left-drag selection completed
                if has_sel:
                    self._on_selection_completed(cursor)
                event.accept()
                return

        elif event.button() == Qt.MouseButton.RightButton:
            was_right_dragging = getattr(self, "_is_right_dragging", False)
            self._is_right_down = False
            self._is_right_dragging = False

            if was_right_dragging:
                self._suppress_next_context_menu = True
                cursor = self.textCursor()
                if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
                    self._on_selection_completed(cursor)
                event.accept()
                return
            else:
                self._suppress_next_context_menu = False
                self.show_context_menu(pos)
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Allow standard Copy (Ctrl+C / Cmd+C) in both viewing and editing modes
        if event.matches(QKeySequence.StandardKey.Copy) or (
            event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)
            and event.key() == Qt.Key.Key_C
        ):
            if self.textCursor().hasSelection():
                self.copy()
                event.accept()
                return
        # The application owns undo/redo for project edits.  Do this before
        # QTextEdit's native undo stack so Ctrl+Z / Ctrl+Shift+Z is consistent
        # with speaker-label, story and other project-state operations.
        if event.matches(QKeySequence.StandardKey.Undo):
            main_win = self.window()
            if hasattr(main_win, "flush_pending_transcript_undo"):
                main_win.flush_pending_transcript_undo()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.undo()
                event.accept()
                return
        if event.matches(QKeySequence.StandardKey.Redo):
            main_win = self.window()
            if hasattr(main_win, "flush_pending_transcript_undo"):
                main_win.flush_pending_transcript_undo()
            if hasattr(main_win, "undo_stack"):
                main_win.undo_stack.redo()
                event.accept()
                return

        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))
        is_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        key = event.key()

        # Add / Edit Comment shortcut (Ctrl+M, Ctrl+Alt+M)
        if (is_ctrl and key == Qt.Key.Key_M and not is_shift and not is_alt) or \
           (is_ctrl and is_alt and key == Qt.Key.Key_M):
            main_win = self.window()
            if hasattr(main_win, "add_comment_from_selection"):
                main_win.add_comment_from_selection()
                event.accept()
                return
            elif hasattr(main_win, "edit_segment_comment_dialog"):
                cursor = self.textCursor()
                seg_idx = self.get_segment_index_at_cursor(cursor)
                if seg_idx is None:
                    seg_idx = cursor.blockNumber()
                main_win.edit_segment_comment_dialog(seg_idx)
                event.accept()
                return

        # Toggle Comments Sidebar shortcut (Ctrl+Alt+C or Alt+5)
        if (is_ctrl and is_alt and key == Qt.Key.Key_C and not is_shift) or \
           (is_alt and key == Qt.Key.Key_5 and not is_ctrl and not is_shift):
            main_win = self.window()
            if hasattr(main_win, "toggle_comments_panel"):
                main_win.toggle_comments_panel()
                event.accept()
                return

        # Speed-Listening / Proofreading Tab & Toggle Shortcuts (Tab / F2 / Ctrl+T)
        # Pressing Tab, F2, or Ctrl+T in viewing mode pauses audio, enters edit mode, and positions the cursor
        # directly at the active spoken word for instantaneous correction.
        # Pressing Tab, F2, or Ctrl+T in editing mode exits editing mode and resumes playback (with optional pre-roll).
        if (key == Qt.Key.Key_Tab and not is_ctrl and not is_alt) or \
           (key == Qt.Key.Key_F2 and not is_ctrl and not is_alt) or \
           (is_ctrl and key == Qt.Key.Key_T and not is_alt and not is_shift):
            main_win = self.window()
            if not self.is_editing_mode:
                last_anchor = getattr(self, "last_active_highlight_anchor", None) or getattr(self, "active_highlight_anchor", None)
                if hasattr(main_win, "player") and main_win.player.playbackState() == main_win.player.PlaybackState.PlayingState:
                    main_win.toggle_play()
                self.set_editing_mode(True)
                if last_anchor:
                    positions = self.anchor_ranges.get(last_anchor)
                    if positions:
                        cur = QTextCursor(self.document())
                        cur.setPosition(positions[0])
                        cur.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
                        self.setTextCursor(cur)
                        self.ensureCursorVisible()
                event.accept()
                return
            else:
                self.set_editing_mode(False)
                if hasattr(main_win, "toggle_play"):
                    preroll = float(getattr(main_win, "speed_listening_preroll_seconds", 0.5) or 0.5)
                    if preroll > 0.0 and hasattr(main_win, "seek_relative"):
                        main_win.seek_relative(-preroll)
                    if hasattr(main_win, "player") and main_win.player.playbackState() != main_win.player.PlaybackState.PlayingState:
                        main_win.toggle_play()
                event.accept()
                return

        if self.is_editing_mode:
            if is_ctrl and not is_shift and not is_alt:
                if key == Qt.Key.Key_B:
                    self.toggle_bold()
                    event.accept()
                    return
                elif key == Qt.Key.Key_I:
                    self.toggle_italic()
                    event.accept()
                    return
                elif key == Qt.Key.Key_U:
                    self.toggle_underline()
                    event.accept()
                    return
                elif key == Qt.Key.Key_K:
                    self.toggle_strikethrough()
                    event.accept()
                    return
                elif key in (Qt.Key.Key_Backslash, Qt.Key.Key_Space):
                    self.clear_formatting()
                    event.accept()
                    return
            elif is_ctrl and is_shift and not is_alt:
                if key in (Qt.Key.Key_X, Qt.Key.Key_S):
                    self.toggle_strikethrough()
                    event.accept()
                    return

        if self.is_editing_mode and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()

            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter: add a speaker label break (split the segment here).
                seg_idx = self.get_segment_index_at_cursor(cursor)
                if seg_idx is None:
                    seg_idx = cursor.blockNumber()
                split_time = self.get_timestamp_at_cursor(cursor)
                self.requestSplitAtCursor.emit(seg_idx, split_time)
                event.accept()
                return

            main_win = self.window()
            ts = self.get_timestamp_at_cursor(cursor)
            show_ms = getattr(main_win, "show_milliseconds", False)
            time_str = format_time(ts, include_millis=show_ms)

            cursor.insertBlock()

            ts_html = (
                f'<a href="time:{ts}" style="color:#8b949e !important; text-decoration:none;">'
                f'<b>{time_str}</b></a>&nbsp;'
            )
            cursor.insertHtml(ts_html)
            event.accept()
            return

        if self.is_editing_mode and event.key() == Qt.Key.Key_Backspace and self.textCursor().atBlockStart():
            cursor = self.textCursor()
            seg_idx = self.get_segment_index_at_cursor(cursor)
            if seg_idx is not None and seg_idx > 0:
                self.requestRemoveSpeakerAtBlock.emit(seg_idx)
                event.accept()
                return

        if event.key() == Qt.Key.Key_Escape:
            if self.has_active_selection():
                self.clear_all_selections()
                event.accept()
                return
            if self.is_editing_mode:
                self.set_editing_mode(False)
                main_win = self.window()
                if hasattr(main_win, "toggle_play"):
                    preroll = float(getattr(main_win, "speed_listening_preroll_seconds", 0.5) or 0.5)
                    if preroll > 0.0 and hasattr(main_win, "seek_relative"):
                        main_win.seek_relative(-preroll)
                    if hasattr(main_win, "player") and main_win.player.playbackState() != main_win.player.PlaybackState.PlayingState:
                        main_win.toggle_play()
                event.accept()
                return

        if event.matches(QKeySequence.StandardKey.Find):
            main_win = self.window()
            if hasattr(main_win, "open_find_replace"):
                main_win.open_find_replace()
                event.accept()
                return

        if not self.is_editing_mode and event.key() in (
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown
        ):
            main_win = self.window()
            skip_sec = float(getattr(main_win, "skip_seconds", 5.0) or 5.0)
            cursor = self.textCursor()
            key = event.key()

            if key == Qt.Key.Key_Home:
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                t = self.get_block_start_timestamp(cursor)
                if t is not None and hasattr(main_win, "seek_to"):
                    main_win.seek_to(t)
                event.accept()
                return
            elif key == Qt.Key.Key_End:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                t = self.get_block_end_timestamp(cursor)
                if t is not None and hasattr(main_win, "seek_to"):
                    main_win.seek_to(t)
                event.accept()
                return
            elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
                if hasattr(main_win, "seek_relative"):
                    main_win.last_position_source = "transcript"
                    main_win.seek_relative(-skip_sec)
                    if hasattr(main_win, "transcript") and hasattr(self, "move_cursor_to_time"):
                        self.move_cursor_to_time(getattr(main_win, "current_position", 0.0), main_win.transcript)
                event.accept()
                return
            elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
                if hasattr(main_win, "seek_relative"):
                    main_win.last_position_source = "transcript"
                    main_win.seek_relative(skip_sec)
                    if hasattr(main_win, "transcript") and hasattr(self, "move_cursor_to_time"):
                        self.move_cursor_to_time(getattr(main_win, "current_position", 0.0), main_win.transcript)
                event.accept()
                return

        super().keyPressEvent(event)

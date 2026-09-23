"""
transcript_editor.py - Interactive Transcript Editor & Viewer Components
Extracted from prs_shared.py as part of Phase 2 Modularization (Milestone 3.2).

Provides:
- FindReplaceDialog: Modeless find-and-replace dialog for QTextEdit/InteractiveTranscriptEdit
- TranscriptSelectionBubble: Floating quick-action toolbar on transcript selection
- InteractiveTranscriptEdit: Rich interactive transcript editor with word-level playback
  synchronization, speaker attribution, search highlighting, and custom context menus
- transcript_text_view_stylesheet: Dynamic theme/font stylesheet generator for transcript views
"""

import sys
import os
import re
import time
import html
from bisect import bisect_right
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

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

from core_utils import format_time


class FindReplaceDialog(QDialog):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.find_input = QLineEdit()
        self.replace_input = QLineEdit()
        self.case_checkbox = QCheckBox("Match Case")

        form.addRow("Find:", self.find_input)
        form.addRow("Replace with:", self.replace_input)
        layout.addLayout(form)
        layout.addWidget(self.case_checkbox)

        btn_layout = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")

        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

        self.find_next_btn.clicked.connect(self.find_next)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)

        self.shortcut_find_next = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_find_next.activated.connect(self.find_next)

    def get_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        target = self.find_input.text()
        if not target:
            return False

        found = self.text_edit.find(target, self.get_flags())
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, self.get_flags())

        return found

    def replace(self):
        target = self.find_input.text()
        if not target:
            return

        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        target = self.find_input.text()
        replacement = self.replace_input.text()
        if not target:
            return

        # Perform cursor-based forward pass to prevent infinite matching loops
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        self.text_edit.setTextCursor(cursor)

        count = 0
        flags = self.get_flags()
        while self.text_edit.find(target, flags):
            match_cursor = self.text_edit.textCursor()
            match_cursor.insertText(replacement)
            count += 1

        cursor.endEditBlock()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")


def transcript_text_view_stylesheet(mode, font_size=16):
    """Shared visual treatment for transcript-style views.

    ``font_size`` is deliberately supplied at runtime so the user's transcript
    zoom preference changes only transcript text, not the surrounding UI.
    """
    font_size = max(11, min(25, float(font_size)))
    if mode == "light":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #c5c5cb;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
            }}
        """
    elif mode == "high_contrast":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffff00;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
            }}
        """
    return f"""
        QTextEdit, QTextBrowser {{
            background-color: #121417;
            color: #f0f3f6;
            border: 1px solid #282c35;
            border-radius: 8px;
            padding: 12px;
            font-size: {font_size:.1f}px;
            line-height: 1.6;
            selection-background-color: #38bdf8;
            selection-color: #ffffff;
        }}
    """


class TranscriptSelectionBubble(QFrame):
    """Floating quick-action toolbar on transcript selection (Milestone 3.12)."""
    playRequested = Signal()
    storyRequested = Signal()
    cutRequested = Signal()
    exportRequested = Signal()
    commentRequested = Signal()
    noteRequested = Signal()  # alias for backward compatibility

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("transcript_selection_bubble")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self.play_btn = QToolButton(self)
        self.play_btn.setText("▶ Play")
        self.play_btn.setToolTip("Preview audio for this selection (Space)")
        self.play_btn.clicked.connect(self.playRequested.emit)
        layout.addWidget(self.play_btn)

        self.story_btn = QToolButton(self)
        self.story_btn.setText("+ Story")
        self.story_btn.setToolTip("Create a new story cut from highlighted text (Enter)")
        self.story_btn.clicked.connect(self.storyRequested.emit)
        layout.addWidget(self.story_btn)

        self.comment_btn = QToolButton(self)
        self.comment_btn.setText("💬 Comment")
        self.comment_btn.setToolTip("Add comment to highlighted section (Ctrl+M)")
        self.comment_btn.clicked.connect(self._emit_comment)
        layout.addWidget(self.comment_btn)

        self.note_btn = self.comment_btn  # alias

        self.cut_btn = QToolButton(self)
        self.cut_btn.setText("✂ Exclude")
        self.cut_btn.setToolTip("Exclude or cut this range")
        self.cut_btn.clicked.connect(self.cutRequested.emit)
        layout.addWidget(self.cut_btn)

        self.export_btn = QToolButton(self)
        self.export_btn.setText("⚡ Export")
        self.export_btn.setToolTip("Quick export selection as audio soundbite")
        self.export_btn.clicked.connect(self.exportRequested.emit)
        layout.addWidget(self.export_btn)

        self.setStyleSheet("""
            QFrame#transcript_selection_bubble {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
            }
            QToolButton {
                background-color: transparent;
                color: #f1f5f9;
                border: none;
                border-radius: 4px;
                padding: 4px 9px;
                font-size: 11px;
                font-weight: bold;
                min-width: 52px;
            }
            QToolButton:hover {
                background-color: #334155;
                color: #38bdf8;
            }
            QToolButton:pressed {
                background-color: #0f172a;
            }
        """)
        self.hide()

    def _emit_comment(self):
        self.commentRequested.emit()
        self.noteRequested.emit()
        self.hide()


class InteractiveTranscriptEdit(QTextEdit):
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

    def _on_bubble_play(self):
        win = self.window()
        if hasattr(win, "play_active_transcript_selection"):
            win.play_active_transcript_selection()
        elif hasattr(win, "play_selection"):
            win.play_selection()

    def _on_bubble_story(self):
        win = self.window()
        if hasattr(win, "add_story_from_active_selection"):
            win.add_story_from_active_selection()
        self.selection_bubble.hide()

    def _on_bubble_note(self):
        win = self.window()
        if hasattr(win, "add_comment_from_selection"):
            win.add_comment_from_selection()
        elif hasattr(win, "edit_segment_comment_dialog"):
            cursor = self.textCursor()
            seg_idx = self.get_segment_index_at_cursor(cursor)
            if seg_idx is None:
                seg_idx = cursor.blockNumber()
            win.edit_segment_comment_dialog(seg_idx)
        elif hasattr(win, "add_note_dialog"):
            win.add_note_dialog()
        self.selection_bubble.hide()

    def _on_bubble_cut(self):
        win = self.window()
        if hasattr(win, "exclude_selection"):
            win.exclude_selection()
        self.selection_bubble.hide()

    def _on_bubble_export(self):
        win = self.window()
        if hasattr(win, "quick_export_selection"):
            win.quick_export_selection()
        self.selection_bubble.hide()

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

            card_w = min(460, rect.width() - 40)
            card_h = min(220, rect.height() - 40)
            if card_w > 120 and card_h > 80:
                card_x = rect.x() + (rect.width() - card_w) // 2
                card_y = rect.y() + (rect.height() - card_h) // 2
                card_rect = QRectF(card_x, card_y, card_w, card_h)

                is_dark = self.current_theme == "dark"
                pen = QPen(QColor("#3b82f6" if is_dark else "#2563eb"), 1.5, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                fill_color = QColor(30, 41, 59, 120) if is_dark else QColor(241, 245, 249, 180)
                painter.setBrush(fill_color)
                painter.drawRoundedRect(card_rect, 10.0, 10.0)

                title_font = QFont(self.font())
                title_font.setPointSize(12)
                title_font.setBold(True)
                painter.setFont(title_font)
                painter.setPen(QColor("#f8fafc" if is_dark else "#0f172a"))
                t_rect = QRectF(card_x + 16, card_y + 24, card_w - 32, 28)
                painter.drawText(t_rect, Qt.AlignmentFlag.AlignCenter, "Drop an Audio or Video File Here to Begin")

                sub_font = QFont(self.font())
                sub_font.setPointSize(9)
                painter.setFont(sub_font)
                painter.setPen(QColor("#94a3b8" if is_dark else "#64748b"))
                s_rect = QRectF(card_x + 16, card_y + 58, card_w - 32, 42)
                painter.drawText(s_rect, Qt.AlignmentFlag.AlignCenter, "Supports WAV, MP3, MP4, M4A, MKV, FLAC, and OGG\nAuto-generates synchronized word-level transcription")

                btn_font = QFont(self.font())
                btn_font.setPointSize(9)
                btn_font.setBold(True)
                painter.setFont(btn_font)
                btn_rect = QRectF(card_x + (card_w - 200) // 2, card_y + 115, 200, 32)
                painter.fillRect(btn_rect, QColor("#2563eb"))
                painter.setPen(QColor("#ffffff"))
                painter.drawRoundedRect(btn_rect, 5.0, 5.0)
                painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Open Media File... (Ctrl+O)")

                hint_font = QFont(self.font())
                hint_font.setPointSize(8)
                painter.setFont(hint_font)
                painter.setPen(QColor("#64748b"))
                h_rect = QRectF(card_x + 16, card_y + 155, card_w - 32, 24)
                painter.drawText(h_rect, Qt.AlignmentFlag.AlignCenter, "Or click File > Open Media in the menu bar")
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

    def set_selection_mode(self, mode):
        self.selection_mode = mode if mode in ("replace", "keep") else "replace"
        if self.selection_mode == "replace" and self.saved_selections:
            self.saved_selections = []
            self.update_extra_selections()

    def set_char_timestamp_map(self, mapping):
        self.char_timestamp_map = mapping

    def has_active_selection(self):
        cursor = self.textCursor()
        if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
            return True
        if getattr(self, "saved_selections", None) and len(self.saved_selections) > 0:
            return True
        return False

    def clear_all_selections(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.clearSelection()
            self.setTextCursor(cursor)
        self.saved_selections = []
        self.setExtraSelections([])
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()
        main_win = self.window()
        if hasattr(main_win, "timeline"):
            main_win.timeline.set_transcript_selection_range(None, None)
        if hasattr(main_win, "statusBar"):
            main_win.statusBar().showMessage("Cleared transcript selection.")

    def get_time_range_for_char_span(self, start_pos, end_pos):
        if not self.char_timestamp_map:
            return None
        s_pos = min(start_pos, end_pos)
        e_pos = max(start_pos, end_pos)
        overlaps = []
        for item in self.char_timestamp_map:
            if len(item) >= 4:
                a, b, ts_start, ts_end = item[0], item[1], item[2], item[3]
            else:
                a, b, ts_start = item
                ts_end = ts_start
            if b > s_pos and a < e_pos:
                overlaps.append((float(ts_start), float(ts_end)))
        if not overlaps:
            return None
        return min(x[0] for x in overlaps), max(x[1] for x in overlaps)

    def get_selected_time_range(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            s_pos = min(cursor.selectionStart(), cursor.selectionEnd())
            e_pos = max(cursor.selectionStart(), cursor.selectionEnd())
            res = self.get_time_range_for_char_span(s_pos, e_pos)
            if res is not None:
                return res
        if getattr(self, "saved_selections", None):
            return (
                min(s["start_time"] for s in self.saved_selections),
                max(s["end_time"] for s in self.saved_selections),
            )
        return None

    def get_all_selected_story_ranges(self):
        """Returns a list of dicts: [{'start_time': float, 'end_time': float, 'text': str, ...}, ...]"""
        if self.selection_mode == "keep" and self.saved_selections:
            return sorted(self.saved_selections, key=lambda x: x.get("start_time", 0.0))

        cursor = self.textCursor()
        if cursor.hasSelection() and (cursor.selectionEnd() - cursor.selectionStart() > 0):
            s_pos = min(cursor.selectionStart(), cursor.selectionEnd())
            e_pos = max(cursor.selectionStart(), cursor.selectionEnd())
            t_range = self.get_time_range_for_char_span(s_pos, e_pos)
            if not t_range:
                main_win = self.window()
                st = getattr(main_win, "current_position", 0.0)
                t_range = (st, st + 5.0)
            return [{
                "start_char": s_pos,
                "end_char": e_pos,
                "start_time": t_range[0],
                "end_time": t_range[1],
                "text": cursor.selectedText().strip(),
            }]
        return []

    def select_comment_range(self, seg_idx):
        """Navigate and select the exact comment text range in the transcript view."""
        main_win = self.window()
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript
        if not t_data or not isinstance(t_data, dict) or "segments" not in t_data:
            return
        segments = t_data.get("segments", [])
        if not (0 <= seg_idx < len(segments)):
            return
        seg = segments[seg_idx]
        c_selected = (seg.get("comment_selected_text") or "").strip()
        c_start = seg.get("comment_char_start")
        c_end = seg.get("comment_char_end")

        doc = self.document()
        doc_text = doc.toPlainText()
        positions = None
        if c_selected:
            pos_in_doc = doc_text.find(c_selected)
            if pos_in_doc >= 0:
                positions = (pos_in_doc, pos_in_doc + len(c_selected))
            else:
                block = doc.findBlockByNumber(seg_idx)
                if block.isValid():
                    block_text = block.text()
                    pos_in_block = block_text.find(c_selected)
                    if pos_in_block >= 0:
                        start_p = block.position() + pos_in_block
                        positions = (start_p, start_p + len(c_selected))
        if not positions and c_start is not None and c_end is not None and c_end > c_start and c_end <= doc.characterCount():
            positions = (c_start, c_end)

        if not positions:
            block = doc.findBlockByNumber(seg_idx)
            if block.isValid():
                positions = (block.position(), block.position() + max(1, block.length() - 1))

        if positions:
            cursor = QTextCursor(doc)
            cursor.setPosition(positions[0])
            cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self.setFocus()

    def update_extra_selections(self):
        extras = []
        main_win = self.window()
        self.comment_spans = []
        show_highlights = str(getattr(main_win, "show_comment_highlights", getattr(self, "show_comment_highlights", True))).lower() in {"1", "true", "yes"}

        # Amber / Yellow Comment Highlights (Word & Google Docs Style)
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript
        if t_data and isinstance(t_data, dict) and "segments" in t_data:
            segments = t_data.get("segments", [])
            doc = self.document()
            doc_text = doc.toPlainText()
            seen_spans = set()
            for idx, seg in enumerate(segments):
                comment_text = seg.get("comments") or seg.get("notes", "")
                if comment_text and comment_text.strip():
                    c_start = seg.get("comment_char_start")
                    c_end = seg.get("comment_char_end")
                    c_selected = (seg.get("comment_selected_text") or "").strip()

                    span_key = (comment_text.strip(), c_selected, c_start, c_end)
                    if span_key in seen_spans:
                        continue
                    seen_spans.add(span_key)

                    positions = None
                    if c_selected:
                        pos_in_doc = doc_text.find(c_selected)
                        if pos_in_doc >= 0:
                            positions = (pos_in_doc, pos_in_doc + len(c_selected))
                        else:
                            block = doc.findBlockByNumber(idx)
                            if block.isValid():
                                block_text = block.text()
                                pos_in_block = block_text.find(c_selected)
                                if pos_in_block >= 0:
                                    start_p = block.position() + pos_in_block
                                    positions = (start_p, start_p + len(c_selected))

                    if not positions and c_start is not None and c_end is not None and c_end > c_start and c_end <= doc.characterCount():
                        positions = (c_start, c_end)

                    if not positions:
                        target_anchor = f"seg_{idx}"
                        positions = self.anchor_ranges.get(target_anchor)
                        if not positions:
                            block = doc.findBlockByNumber(idx)
                            if block.isValid():
                                positions = (block.position(), block.position() + max(1, block.length() - 1))

                    if positions:
                        # Always register span for hover tooltips and click navigation
                        self.comment_spans.append({
                            "start": positions[0],
                            "end": positions[1],
                            "seg_idx": idx,
                            "comment": comment_text.strip(),
                            "selected_text": c_selected,
                            "start_time": float(seg.get("start", 0.0)),
                            "end_time": float(seg.get("end", 0.0)),
                        })

                        # Amber highlight extra selection (toggled by Show/Hide Highlights)
                        if show_highlights:
                            comment_fmt = QTextCharFormat()
                            if getattr(self, "current_theme", "dark") == "light":
                                comment_fmt.setBackground(QColor(254, 240, 138, 220))  # Warm amber highlight
                                comment_fmt.setForeground(QColor(133, 77, 14))
                            else:
                                comment_fmt.setBackground(QColor(133, 77, 14, 200))  # Dark warm amber highlight
                                comment_fmt.setForeground(QColor(254, 240, 138))
                            comment_cursor = QTextCursor(doc)
                            comment_cursor.setPosition(positions[0])
                            comment_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
                            extra = QTextEdit.ExtraSelection()
                            extra.format = comment_fmt
                            extra.cursor = comment_cursor
                            extras.append(extra)

        if hasattr(self, "saved_selections") and self.saved_selections:
            fmt = QTextCharFormat()
            if getattr(self, "current_theme", "dark") == "light":
                fmt.setBackground(QColor(186, 215, 255, 170))
                fmt.setForeground(QColor(15, 23, 42))
            else:
                fmt.setBackground(QColor(40, 105, 215, 170))
                fmt.setForeground(QColor(255, 255, 255))

            for sel in self.saved_selections:
                extra = QTextEdit.ExtraSelection()
                extra.format = fmt
                cursor = QTextCursor(self.document())
                cursor.setPosition(sel["start_char"])
                cursor.setPosition(sel["end_char"], QTextCursor.MoveMode.KeepAnchor)
                extra.cursor = cursor
                extras.append(extra)

        if getattr(self, "_playback_highlight_selection", None) is not None:
            extras.append(self._playback_highlight_selection)

        self.setExtraSelections(extras)

    def _on_selection_completed(self, cursor):
        if not cursor.hasSelection():
            return
        start_char = min(cursor.selectionStart(), cursor.selectionEnd())
        end_char = max(cursor.selectionStart(), cursor.selectionEnd())
        if end_char <= start_char:
            return

        t_range = self.get_time_range_for_char_span(start_char, end_char)
        if not t_range:
            main_win = self.window()
            start_t = getattr(main_win, "current_position", 0.0)
            end_t = start_t + 5.0
            t_range = (start_t, end_t)

        selected_text = cursor.selectedText().strip()

        if self.selection_mode == "keep":
            # Multi-selection mode: accumulate selections without clearing previous ones
            merged = False
            for s in self.saved_selections:
                if not (end_char < s["start_char"] or start_char > s["end_char"]):
                    s["start_char"] = min(s["start_char"], start_char)
                    s["end_char"] = max(s["end_char"], end_char)
                    merged_tr = self.get_time_range_for_char_span(s["start_char"], s["end_char"])
                    if merged_tr:
                        s["start_time"], s["end_time"] = merged_tr
                    c = QTextCursor(self.document())
                    c.setPosition(s["start_char"])
                    c.setPosition(s["end_char"], QTextCursor.MoveMode.KeepAnchor)
                    s["text"] = c.selectedText().strip()
                    merged = True
                    break
            if not merged:
                self.saved_selections.append({
                    "start_char": start_char,
                    "end_char": end_char,
                    "start_time": t_range[0],
                    "end_time": t_range[1],
                    "text": selected_text
                })

            # Clear active cursor selection so extraSelections render clearly
            temp_cursor = QTextCursor(cursor)
            temp_cursor.clearSelection()
            self.setTextCursor(temp_cursor)
            self.update_extra_selections()

            main_win = self.window()
            if hasattr(main_win, "statusBar"):
                count = len(self.saved_selections)
                main_win.statusBar().showMessage(f"Selected {count} sections. Right-click or click 'Add Story' to save.")
        else:
            # Single selection mode: replace previous selection
            self.saved_selections = []
            self.setExtraSelections([])
            main_win = self.window()
            if hasattr(main_win, "timeline") and t_range:
                main_win.timeline.set_transcript_selection_range(t_range[0], t_range[1])
            if hasattr(main_win, "statusBar") and t_range:
                main_win.statusBar().showMessage(f"Transcript selection: {format_time(t_range[0])} – {format_time(t_range[1])}")

        main_win = self.window()
        show_floating = str(getattr(main_win, "show_floating_selection_toolbar", getattr(self, "show_floating_selection_toolbar", True))).lower() in {"1", "true", "yes"}
        if hasattr(self, "selection_bubble") and not self.is_editing_mode and show_floating:
            c_rect = self.cursorRect(cursor)
            bubble_hint = self.selection_bubble.sizeHint()
            b_w = max(336, bubble_hint.width() + 16)
            b_h = max(34, bubble_hint.height())
            bx = max(8, min(self.viewport().width() - b_w - 8, c_rect.center().x() - b_w // 2))
            by = max(4, c_rect.top() - b_h - 6)
            self.selection_bubble.setFixedSize(b_w, b_h)
            self.selection_bubble.setGeometry(bx, by, b_w, b_h)
            self.selection_bubble.show()
            self.selection_bubble.raise_()
        elif hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

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
        self.editingModeChanged.emit(enabled)

    def toggle_bold(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        curr_weight = self.fontWeight()
        new_weight = QFont.Weight.Normal if curr_weight > QFont.Weight.Medium else QFont.Weight.Bold
        fmt.setFontWeight(new_weight)
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_italic(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.fontItalic())
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_underline(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.fontUnderline())
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_strikethrough(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        is_strike = self.currentCharFormat().fontStrikeOut()
        fmt.setFontStrikeOut(not is_strike)
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)
        self.setFocus()
        self.formatChanged.emit()

    def toggle_highlight(self, color_name="#fef08a", force_apply=False):
        """Toggle or change color of rich highlighting on active text selection or contiguous highlighted region."""
        cursor = self.textCursor()
        main_win = self.window()
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        cur_fmt = self.currentCharFormat()
        curr_bg = cur_fmt.background().color()
        has_active_highlight = (
            cur_fmt.background().style() != Qt.BrushStyle.NoBrush
            and curr_bg.isValid()
            and curr_bg.alpha() > 0
            and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
        )

        target_color = QColor(color_name)
        target_hex = target_color.name().lower()

        # If already highlighted with exact same color and force_apply is False, toggle it off
        if has_active_highlight and not force_apply and curr_bg.name().lower() == target_hex:
            self.remove_highlight()
            return

        # 1. Update underlying transcript data model (for both View and Edit modes)
        segs = main_win.transcript.get("segments", []) if (hasattr(main_win, "transcript") and main_win.transcript) else []

        target_segs = set()
        if cursor.hasSelection():
            sel_start = min(cursor.selectionStart(), cursor.selectionEnd())
            sel_end = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self, "get_time_range_for_char_span"):
                t_range = self.get_time_range_for_char_span(sel_start, sel_end)
                if t_range and t_range[0] is not None and t_range[1] is not None:
                    st, et = t_range
                    for i, s in enumerate(segs):
                        s_st = s.get("start", 0.0)
                        s_et = s.get("end", 0.0)
                        if s_st <= et and s_et >= st:
                            target_segs.add(i)

        if not target_segs:
            c_seg = self.get_segment_index_at_cursor(cursor)
            if c_seg is not None and 0 <= c_seg < len(segs):
                target_segs.add(c_seg)
            else:
                blk = cursor.blockNumber()
                if 0 <= blk < len(segs):
                    target_segs.add(blk)

        # Build flattened word list to identify contiguous highlighted regions
        flat_words = []
        for s_idx, seg in enumerate(segs):
            if not isinstance(seg, dict):
                continue
            seg_hl = seg.get("highlight")
            words = seg.get("words", [])
            if isinstance(words, list) and words:
                for w_idx, w in enumerate(words):
                    if isinstance(w, dict):
                        w_hl = w.get("highlight") or seg_hl
                        is_hl = bool(w_hl and w_hl not in (False, "false", "False", 0, None))
                        flat_words.append({
                            "seg_idx": s_idx,
                            "word_idx": w_idx,
                            "word_dict": w,
                            "seg_dict": seg,
                            "is_hl": is_hl
                        })
            else:
                text = seg.get("text", "")
                for w_idx, word_str in enumerate(text.split()):
                    is_hl = bool(seg_hl and seg_hl not in (False, "false", "False", 0, None))
                    flat_words.append({
                        "seg_idx": s_idx,
                        "word_idx": w_idx,
                        "word_dict": None,
                        "seg_dict": seg,
                        "is_hl": is_hl
                    })

        total_words = len(flat_words)
        targeted_flat_indices = set()
        for idx, fw in enumerate(flat_words):
            if fw["seg_idx"] in target_segs:
                targeted_flat_indices.add(idx)

        # Expand backwards and forwards across contiguous highlighted word blocks to recolor full region
        indices_to_recolor = set()
        for t_idx in targeted_flat_indices:
            if 0 <= t_idx < total_words:
                if flat_words[t_idx]["is_hl"]:
                    start_i = t_idx
                    while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                        start_i -= 1
                    end_i = t_idx
                    while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                        end_i += 1
                    for k in range(start_i, end_i + 1):
                        indices_to_recolor.add(k)
                elif cursor.hasSelection():
                    indices_to_recolor.add(t_idx)

        # If user clicked near a highlighted region (e.g. adjacent word boundary)
        if not indices_to_recolor and targeted_flat_indices:
            for t_idx in targeted_flat_indices:
                for offset in (-1, 1, -2, 2):
                    adj = t_idx + offset
                    if 0 <= adj < total_words and flat_words[adj]["is_hl"]:
                        start_i = adj
                        while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                            start_i -= 1
                        end_i = adj
                        while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                            end_i += 1
                        for k in range(start_i, end_i + 1):
                            indices_to_recolor.add(k)

        # Apply new highlight color to targeted data words & segments
        affected_segs = set()
        if indices_to_recolor:
            for k in indices_to_recolor:
                fw = flat_words[k]
                if fw["word_dict"]:
                    fw["word_dict"]["highlight"] = target_hex
                affected_segs.add(fw["seg_idx"])
            for s_idx in affected_segs:
                seg = segs[s_idx]
                seg["highlight"] = target_hex
        else:
            for s_idx in target_segs:
                if 0 <= s_idx < len(segs):
                    seg = segs[s_idx]
                    seg["highlight"] = target_hex
                    if "words" in seg and isinstance(seg["words"], list):
                        for w in seg["words"]:
                            if isinstance(w, dict):
                                w["highlight"] = target_hex

        # 2. Update QTextCharFormat on editor / view
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(target_color))
        fmt.setForeground(QBrush(QColor("#0f172a")))

        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.mergeCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.mergeCurrentCharFormat(fmt)

        if hasattr(main_win, "mark_project_dirty"):
            main_win.mark_project_dirty()

        # Re-render transcript view so HTML reflects updated colors in both View and Edit modes
        if hasattr(main_win, "render_transcript"):
            main_win.render_transcript()

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Change Highlight Color")

        self.setFocus()
        self.formatChanged.emit()
        self.update_extra_selections()

    def remove_highlight(self):
        """Removes background highlighting for the entire contiguous highlighted section(s) intersecting active selection or cursor."""
        cursor = self.textCursor()
        main_win = self.window()

        # Capture baseline for universal undo / redo history
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None
        segs = main_win.transcript.get("segments", []) if (hasattr(main_win, "transcript") and main_win.transcript) else []

        # 1. Determine target segment index/indices from selection or cursor position
        target_segs = set()
        if cursor.hasSelection():
            sel_start = min(cursor.selectionStart(), cursor.selectionEnd())
            sel_end = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self, "get_time_range_for_char_span"):
                t_range = self.get_time_range_for_char_span(sel_start, sel_end)
                if t_range and t_range[0] is not None and t_range[1] is not None:
                    st, et = t_range
                    for i, s in enumerate(segs):
                        s_st = s.get("start", 0.0)
                        s_et = s.get("end", 0.0)
                        if s_st <= et and s_et >= st:
                            target_segs.add(i)

        if not target_segs:
            c_seg = self.get_segment_index_at_cursor(cursor)
            if c_seg is not None and 0 <= c_seg < len(segs):
                target_segs.add(c_seg)
            else:
                blk = cursor.blockNumber()
                if 0 <= blk < len(segs):
                    target_segs.add(blk)

        # 2. Build flattened word list to identify contiguous highlighted regions
        flat_words = []
        for s_idx, seg in enumerate(segs):
            if not isinstance(seg, dict):
                continue
            seg_hl = seg.get("highlight")
            words = seg.get("words", [])
            if isinstance(words, list) and words:
                for w_idx, w in enumerate(words):
                    if isinstance(w, dict):
                        w_hl = w.get("highlight") or seg_hl
                        is_hl = bool(w_hl and w_hl not in (False, "false", "False", 0, None))
                        flat_words.append({
                            "seg_idx": s_idx,
                            "word_idx": w_idx,
                            "word_dict": w,
                            "seg_dict": seg,
                            "is_hl": is_hl
                        })
            else:
                text = seg.get("text", "")
                for w_idx, word_str in enumerate(text.split()):
                    is_hl = bool(seg_hl and seg_hl not in (False, "false", "False", 0, None))
                    flat_words.append({
                        "seg_idx": s_idx,
                        "word_idx": w_idx,
                        "word_dict": None,
                        "seg_dict": seg,
                        "is_hl": is_hl
                    })

        total_words = len(flat_words)
        targeted_flat_indices = set()
        for idx, fw in enumerate(flat_words):
            if fw["seg_idx"] in target_segs:
                targeted_flat_indices.add(idx)

        # 3. Expand backwards and forwards across contiguous highlighted word blocks
        indices_to_clear = set()
        for t_idx in targeted_flat_indices:
            if 0 <= t_idx < total_words and flat_words[t_idx]["is_hl"]:
                start_i = t_idx
                while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                    start_i -= 1
                end_i = t_idx
                while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                    end_i += 1
                for k in range(start_i, end_i + 1):
                    indices_to_clear.add(k)

        # If user clicked near a highlighted region (e.g. adjacent space or word boundary)
        if not indices_to_clear and targeted_flat_indices:
            for t_idx in targeted_flat_indices:
                for offset in (-1, 1, -2, 2):
                    adj = t_idx + offset
                    if 0 <= adj < total_words and flat_words[adj]["is_hl"]:
                        start_i = adj
                        while start_i > 0 and flat_words[start_i - 1]["is_hl"]:
                            start_i -= 1
                        end_i = adj
                        while end_i < total_words - 1 and flat_words[end_i + 1]["is_hl"]:
                            end_i += 1
                        for k in range(start_i, end_i + 1):
                            indices_to_clear.add(k)

        # 4. Clear highlight on all contiguous words and clean up segment metadata
        if not indices_to_clear:
            for s_idx in target_segs:
                if 0 <= s_idx < len(segs):
                    seg = segs[s_idx]
                    seg.pop("highlight", None)
                    if "words" in seg and isinstance(seg["words"], list):
                        for w in seg["words"]:
                            if isinstance(w, dict):
                                w.pop("highlight", None)
        else:
            affected_segs = set()
            for k in indices_to_clear:
                fw = flat_words[k]
                if fw["word_dict"]:
                    fw["word_dict"].pop("highlight", None)
                affected_segs.add(fw["seg_idx"])

            for s_idx in affected_segs:
                seg = segs[s_idx]
                words = seg.get("words", [])
                if isinstance(words, list):
                    has_remaining_hl = any(
                        isinstance(w, dict) and bool(w.get("highlight"))
                        for w in words
                    )
                    if not has_remaining_hl:
                        seg.pop("highlight", None)
                else:
                    seg.pop("highlight", None)

        # Clear character format background brush on cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.setCurrentCharFormat(fmt)

        if hasattr(main_win, "mark_project_dirty"):
            main_win.mark_project_dirty()

        # Re-render transcript to reflect exact updated state
        if hasattr(main_win, "render_transcript"):
            main_win.render_transcript()

        # Commit project state change for undo stack
        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Remove Highlight")

        self.formatChanged.emit()
        self.update_extra_selections()

    def clear_formatting(self):
        cursor = self.textCursor()
        main_win = self.window()
        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        fmt.setForeground(QBrush(Qt.BrushStyle.NoBrush))
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            cursor.setCharFormat(fmt)
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            self.setCurrentCharFormat(fmt)

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Clear Formatting")

        self.setFocus()
        self.formatChanged.emit()

    def get_current_formatting(self):
        fmt = self.currentCharFormat()
        bg = fmt.background().color()
        has_highlight = bg.isValid() and bg.alpha() > 0 and fmt.background().style() != Qt.BrushStyle.NoBrush
        return {
            "bold": fmt.fontWeight() > QFont.Weight.Medium,
            "italic": fmt.fontItalic(),
            "underline": fmt.fontUnderline(),
            "strike": fmt.fontStrikeOut(),
            "highlight": has_highlight,
        }

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

    def _nearest_word_anchor(self, cursor):
        """Return the word anchor nearest the actual QTextDocument cursor."""
        pos = cursor.position()
        best = None
        best_distance = None
        for href, (start_pos, end_pos) in self.anchor_ranges.items():
            if not href.startswith("word:"):
                continue
            if start_pos <= pos <= end_pos:
                distance = 0
            elif pos < start_pos:
                distance = start_pos - pos
            else:
                distance = pos - end_pos
            if best_distance is None or distance < best_distance:
                parts = href.split(":")
                if len(parts) >= 3 and parts[2].isdigit():
                    try:
                        best = (float(parts[1]), int(parts[2]), href)
                        best_distance = distance
                    except ValueError:
                        pass

        # Fallback to char_timestamp_map if anchor_ranges has no match
        if best is None and getattr(self, "char_timestamp_map", None):
            for entry in self.char_timestamp_map:
                c_start, c_end = entry[0], entry[1]
                ts = entry[2]
                s_idx = entry[4] if len(entry) >= 5 else None
                if c_start <= pos <= c_end and s_idx is not None:
                    return (float(ts), int(s_idx), f"word:{ts}:{s_idx}")

        return best

    def get_timestamp_at_cursor(self, cursor):
        nearest = self._nearest_word_anchor(cursor)
        if nearest is not None:
            return nearest[0]
        # Search the current block in the document for any anchor
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            pass
            it += 1
        main_win = self.window()
        return getattr(main_win, "current_position", 0.0)

    def get_block_start_timestamp(self, cursor):
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            pass
            it += 1
        return self.get_timestamp_at_cursor(cursor)

    def get_block_end_timestamp(self, cursor):
        block = cursor.block()
        last_ts = None
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 2:
                        try:
                            last_ts = float(parts[1])
                        except ValueError:
                            pass
            it += 1
        if last_ts is not None:
            return last_ts
        return self.get_timestamp_at_cursor(cursor)

    def get_segment_index_at_cursor(self, cursor):
        nearest = self._nearest_word_anchor(cursor)
        if nearest is not None:
            return nearest[1]
        # Search current block for segment index
        block = cursor.block()
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                href = frag.charFormat().anchorHref()
                if href and href.startswith("word:"):
                    parts = href.split(":")
                    if len(parts) >= 3 and parts[2].isdigit():
                        return int(parts[2])
                elif href and href.startswith("speaker:"):
                    parts = href.split(":")
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
            it += 1
        return None

    def move_cursor_to_segment_start(self, seg_idx):
        """Best-effort: places the caret at the first word of seg_idx after
        a render_transcript() refresh, so editing can continue in place."""
        target_href = None
        for _start, _end, href in self.time_anchor_index:
            if href.endswith(f":{seg_idx}"):
                target_href = href
                break
        if not target_href:
            return
        positions = self.anchor_ranges.get(target_href)
        if not positions:
            return
        cursor = QTextCursor(self.document())
        cursor.setPosition(positions[0])
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

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

            ts = self.get_timestamp_at_cursor(cursor)
            time_str = format_time(ts)

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

    def show_context_menu(self, position):
        """Context menu for both viewing and editing modes.  Speaker labels
        are interactive targets, while right-clicking anywhere else offers a
        speaker insertion at the nearest transcript timestamp.
        """
        if getattr(self, "_suppress_next_context_menu", False):
            self._suppress_next_context_menu = False
            return

        hit_cursor = self.cursorForPosition(position)
        href = hit_cursor.charFormat().anchorHref()
        if not href and hit_cursor.position() > 0:
            probe = QTextCursor(hit_cursor)
            probe.setPosition(max(0, hit_cursor.position() - 1))
            href = probe.charFormat().anchorHref()

        speaker_target = None
        if href and href.startswith("speaker:"):
            parts = href.split(":", 2)
            if len(parts) >= 3 and parts[1].isdigit():
                speaker_target = (int(parts[1]), parts[2])

        # Preserve active text selection when right-clicking so the user can easily
        # add the selection to a story, play it, or clear it from the context menu.
        if not self.has_active_selection():
            self.setTextCursor(hit_cursor)

        # Store the exact document position that opened the menu.  QAction
        # execution can otherwise move the QTextCursor, which used to make a
        # speaker insertion land at an unrelated earlier timestamp.
        self._context_menu_cursor_position = hit_cursor.position()

        menu = self.createStandardContextMenu() if self.is_editing_mode else QMenu(self)
        main_win = self.window()

        if self.has_active_selection():
            # Add Copy action to context menu when text is highlighted
            copy_action = QAction("Copy", self)
            copy_action.setShortcut(QKeySequence.StandardKey.Copy)
            copy_action.triggered.connect(self.copy)
            menu.addAction(copy_action)

            ranges = self.get_all_selected_story_ranges()
            count = len(ranges)
            title = f"Add Selected Sections to New Stories ({count})" if count > 1 else "Add Selected Text to New Story"
            add_selection = QAction(title, self)
            add_selection.triggered.connect(lambda: main_win.add_selection_to_story())
            menu.addAction(add_selection)

            play_selection = QAction("Play Selected Text", self)
            play_selection.triggered.connect(lambda: main_win.play_transcript_selection())
            menu.addAction(play_selection)

            clear_selection = QAction("Clear Selection", self)
            clear_selection.setShortcut(QKeySequence("Esc"))
            clear_selection.triggered.connect(self.clear_all_selections)
            menu.addAction(clear_selection)

            menu.addSeparator()

        # Speaker controls are deliberately available in BOTH modes.
        if speaker_target:
            seg_idx, raw_speaker = speaker_target
            
            change_menu = menu.addMenu("Change Speaker To")
            known_speakers = []
            if hasattr(main_win, "get_all_known_speakers"):
                known_speakers = main_win.get_all_known_speakers()
            for spk in known_speakers:
                action = change_menu.addAction(spk)
                action.triggered.connect(
                    lambda _, i=seg_idx, s=raw_speaker, name=spk: main_win.execute_speaker_rename(i, s, name)
                )
            change_menu.addSeparator()
            new_change_action = change_menu.addAction("Add New Speaker...")
            new_change_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.execute_speaker_rename(i, s, "__NEW__")
            )

            remove_action = QAction("Remove Speaker Label", self)
            remove_action.setEnabled(seg_idx > 0)
            remove_action.triggered.connect(
                lambda _, i=seg_idx: main_win.remove_speaker_label_at_segment(i)
            )
            menu.addAction(remove_action)

            teach_action = QAction("Teach This Voice: Match Similar Turns...", self)
            teach_action.setToolTip("Use this speaker turn as a reference voice profile to find and reassign matching turns across the timeline")
            teach_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.teach_voice_profile_dialog(i, s)
            )
            menu.addAction(teach_action)

            ref_action = QAction("Set as Reference Profile for New Speaker...", self)
            ref_action.setToolTip("Prompt for a new speaker name and immediately match similar turns using this acoustic profile")
            ref_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.teach_voice_profile_dialog(i, s, prompt_new_speaker=True)
            )
            menu.addAction(ref_action)

            if hasattr(main_win, "prompt_refine_speaker_run"):
                refine_action = QAction("Refine Rapid Dialog Turns (Competitive Classifier)...", self)
                refine_action.setToolTip("Competitively assign turns in a range between two confirmed speakers by relative acoustic distance")
                refine_action.triggered.connect(
                    lambda _, i=seg_idx: main_win.prompt_refine_speaker_run(i, i + 10)
                )
                menu.addAction(refine_action)

            menu.addSeparator()

        insert_menu = menu.addMenu("Add Speaker Label Here")
        target_cursor = hit_cursor
        target_seg_idx = self.get_segment_index_at_cursor(target_cursor)
        if target_seg_idx is None:
            target_seg_idx = target_cursor.blockNumber()
        target_time = self.get_timestamp_at_cursor(target_cursor)

        known_speakers = []
        if hasattr(main_win, "get_all_known_speakers"):
            known_speakers = main_win.get_all_known_speakers()
        for spk in known_speakers:
            action = insert_menu.addAction(spk)
            action.triggered.connect(
                lambda _, s=target_seg_idx, t=target_time, name=spk: self.requestInsertSpeaker.emit(s, t, name)
            )
        insert_menu.addSeparator()
        new_spk_action = insert_menu.addAction("Add New Speaker...")
        new_spk_action.triggered.connect(
            lambda _, s=target_seg_idx, t=target_time: self.requestInsertSpeaker.emit(s, t, "__NEW__")
        )

        if hasattr(main_win, "open_speaker_manager_dialog"):
            manage_spk_act = QAction("Manage Speakers & Detection Clusters...", self)
            manage_spk_act.triggered.connect(main_win.open_speaker_manager_dialog)
            menu.addAction(manage_spk_act)
            menu.addSeparator()

        target_seg = self.get_segment_index_at_cursor(hit_cursor)
        if target_seg is None:
            target_seg = hit_cursor.blockNumber()
        has_comment = False
        if hasattr(main_win, "transcript") and main_win.transcript:
            segs = main_win.transcript.get("segments", [])
            if 0 <= target_seg < len(segs):
                has_comment = bool(segs[target_seg].get("comments") or segs[target_seg].get("notes"))
        comment_title = "💬 Edit Comment..." if has_comment else "💬 Add Comment..."

        if not self.is_editing_mode:
            add_vocab = QAction("Add Selected Text to Glossary", menu)
            add_vocab.setEnabled(self.has_active_selection())
            def _add_vocab_from_selection():
                ranges = self.get_all_selected_story_ranges()
                txt = ranges[0]["text"] if ranges else self.textCursor().selectedText()
                main_win.add_to_glossary(txt)
            add_vocab.triggered.connect(_add_vocab_from_selection)
            menu.addAction(add_vocab)

            edit_comment_act = QAction(f"{comment_title}\tCtrl+M", menu)
            edit_comment_act.triggered.connect(
                lambda _, s=target_seg: getattr(
                    main_win, "add_comment_from_selection",
                    lambda: getattr(main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None))(s)
                )() if self.has_active_selection() else getattr(
                    main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None)
                )(s)
            )
            menu.addAction(edit_comment_act)

            if has_comment:
                del_comment_act = QAction("🗑️ Delete Comment", menu)
                del_comment_act.triggered.connect(
                    lambda _, s=target_seg: getattr(main_win, "delete_segment_comment", lambda x: None)(s)
                )
                menu.addAction(del_comment_act)

            cur_fmt = hit_cursor.charFormat() if hit_cursor else self.currentCharFormat()
            curr_bg = cur_fmt.background().color()
            active_hl_hex = None
            if (
                cur_fmt.background().style() != Qt.BrushStyle.NoBrush
                and curr_bg.isValid()
                and curr_bg.alpha() > 0
                and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
            ):
                active_hl_hex = curr_bg.name().lower()

            if not active_hl_hex and hasattr(main_win, "transcript") and main_win.transcript:
                segs = main_win.transcript.get("segments", [])
                target_seg_i = self.get_segment_index_at_cursor(hit_cursor)
                if target_seg_i is not None and 0 <= target_seg_i < len(segs):
                    seg = segs[target_seg_i]
                    s_hl = seg.get("highlight")
                    if s_hl and s_hl not in (False, "false", "False", 0, None):
                        active_hl_hex = "#fef08a" if isinstance(s_hl, bool) else str(s_hl).lower()

            hl_title = "🎨 Change Highlight Color" if active_hl_hex else "🖊️ Highlight Text"

            hl_colors = [
                ("🟡 Yellow", "#fef08a"),
                ("🟢 Green", "#bbf7d0"),
                ("🔵 Blue / Cyan", "#bae6fd"),
                ("🌸 Pink", "#fbcfe8"),
                ("🟠 Orange", "#fed7aa"),
                ("🟣 Purple", "#e9d5ff"),
            ]

            hl_menu = menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            hl_menu.addSeparator()
            act_rem_hl = hl_menu.addAction("⚪ Remove Highlight")
            act_rem_hl.triggered.connect(self.remove_highlight)

            toggle_comments_act = QAction("💬 Toggle Comments Sidebar\tCtrl+Alt+C", menu)
            toggle_comments_act.triggered.connect(lambda: getattr(main_win, "toggle_comments_panel", lambda: None)())
            menu.addAction(toggle_comments_act)

            menu.addSeparator()
            edit_action = QAction("Edit Transcript\tF2", menu)
            edit_action.triggered.connect(lambda: self.set_editing_mode(True))
            menu.addAction(edit_action)
        else:
            fmt_menu = menu.addMenu("Format Text")
            act_bold = fmt_menu.addAction("Bold\tCtrl+B")
            act_bold.triggered.connect(self.toggle_bold)

            act_italic = fmt_menu.addAction("Italic\tCtrl+I")
            act_italic.triggered.connect(self.toggle_italic)

            act_underline = fmt_menu.addAction("Underline\tCtrl+U")
            act_underline.triggered.connect(self.toggle_underline)

            act_strike = fmt_menu.addAction("Strikethrough\tCtrl+K")
            act_strike.triggered.connect(self.toggle_strikethrough)

            fmt_menu.addSeparator()

            cur_fmt = hit_cursor.charFormat() if hit_cursor else self.currentCharFormat()
            curr_bg = cur_fmt.background().color()
            active_hl_hex = None
            if (
                cur_fmt.background().style() != Qt.BrushStyle.NoBrush
                and curr_bg.isValid()
                and curr_bg.alpha() > 0
                and curr_bg.name().lower() not in ["#000000", "#1e1e1e", "#0f172a", "#ffffff", "#00000000"]
            ):
                active_hl_hex = curr_bg.name().lower()

            if not active_hl_hex and hasattr(main_win, "transcript") and main_win.transcript:
                segs = main_win.transcript.get("segments", [])
                target_seg_i = self.get_segment_index_at_cursor(hit_cursor)
                if target_seg_i is not None and 0 <= target_seg_i < len(segs):
                    seg = segs[target_seg_i]
                    s_hl = seg.get("highlight")
                    if s_hl and s_hl not in (False, "false", "False", 0, None):
                        active_hl_hex = "#fef08a" if isinstance(s_hl, bool) else str(s_hl).lower()

            hl_title = "🎨 Change Highlight Color" if active_hl_hex else "🖊️ Highlight Text"

            hl_menu = fmt_menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            hl_menu.addSeparator()
            act_rem_hl = hl_menu.addAction("⚪ Remove Highlight")
            act_rem_hl.triggered.connect(self.remove_highlight)

            act_clear = fmt_menu.addAction("Clear Formatting\tCtrl+\\")
            act_clear.triggered.connect(self.clear_formatting)

            menu.addSeparator()
            edit_comment_act = QAction(f"{comment_title}\tCtrl+M", menu)
            edit_comment_act.triggered.connect(
                lambda _, s=target_seg: getattr(
                    main_win, "add_comment_from_selection",
                    lambda: getattr(main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None))(s)
                )() if self.textCursor().hasSelection() else getattr(
                    main_win, "edit_segment_comment_dialog", getattr(main_win, "edit_segment_note_dialog", lambda x: None)
                )(s)
            )
            menu.addAction(edit_comment_act)

            if has_comment:
                del_comment_act = QAction("🗑️ Delete Comment", menu)
                del_comment_act.triggered.connect(
                    lambda _, s=target_seg: getattr(main_win, "delete_segment_comment", lambda x: None)(s)
                )
                menu.addAction(del_comment_act)

            rem_hl_act = QAction("🎨 Remove Highlight", menu)
            rem_hl_act.triggered.connect(self.remove_highlight)
            menu.addAction(rem_hl_act)

            toggle_comments_act = QAction("💬 Toggle Comments Sidebar\tCtrl+Alt+C", menu)
            toggle_comments_act.triggered.connect(lambda: getattr(main_win, "toggle_comments_panel", lambda: None)())
            menu.addAction(toggle_comments_act)

            menu.addSeparator()
            find_action = QAction("Find and Replace...\tCtrl+F", menu)
            find_action.triggered.connect(lambda: main_win.open_find_replace())
            menu.addAction(find_action)

            menu.addSeparator()
            exit_action = QAction("View Transcript\tF2", menu)
            exit_action.triggered.connect(lambda: self.set_editing_mode(False))
            menu.addAction(exit_action)

        menu.exec(self.mapToGlobal(position))

    def rebuild_anchor_index(self):
        """Index transcript anchors once so playback highlighting is O(1) lookup."""
        self.anchor_ranges = {}
        doc = self.document()
        block = doc.begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    href = fragment.charFormat().anchorHref()
                    if href:
                        self.anchor_ranges[href] = (
                            fragment.position(),
                            fragment.position() + fragment.length(),
                        )
                it += 1
            block = block.next()

    def set_time_anchor_index(self, entries):
        self.time_anchor_index = sorted(entries, key=lambda item: item[0])
        self.time_anchor_starts = [item[0] for item in self.time_anchor_index]

    def clear_highlight(self):
        if not self.active_highlight_anchor and getattr(self, "_playback_highlight_selection", None) is None:
            return

        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        self.update_extra_selections()

    def highlight_word_at_time(self, seconds, transcript_data, auto_scroll: bool = False):
        if self.is_editing_mode or not transcript_data:
            return

        target_anchor = None
        if self.time_anchor_index:
            idx = bisect_right(self.time_anchor_starts, seconds) - 1
            if idx >= 0:
                start_time, end_time, anchor = self.time_anchor_index[idx]
                # Allow a small tolerance window or match if within the timestamp block
                if start_time <= seconds <= end_time or (seconds - end_time) < 0.3:
                    target_anchor = anchor
            elif self.time_anchor_starts and seconds < self.time_anchor_starts[0]:
                target_anchor = self.time_anchor_index[0][2]

        if not target_anchor or target_anchor == self.active_highlight_anchor:
            return

        doc = self.document()
        positions = self.anchor_ranges.get(target_anchor)
        if not positions:
            self.rebuild_anchor_index()
            positions = self.anchor_ranges.get(target_anchor)

        if not positions:
            self.clear_highlight()
            return

        target_cursor = QTextCursor(doc)
        target_cursor.setPosition(positions[0])
        target_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)

        # Overlay Word Highlighting using QTextEdit.ExtraSelection
        # Prevents document mutations and expensive text reflows during playback
        highlight_fmt = QTextCharFormat()
        if self.current_theme == "light":
            highlight_fmt.setForeground(QColor("#0056b3"))
            highlight_fmt.setBackground(QColor(186, 215, 255, 120))
        elif self.current_theme == "high_contrast":
            highlight_fmt.setForeground(QColor("#ffff00"))
            highlight_fmt.setBackground(QColor(255, 255, 0, 80))
        else:
            highlight_fmt.setForeground(QColor("#58a6ff"))
            highlight_fmt.setBackground(QColor(88, 166, 255, 75))
        highlight_fmt.setFontWeight(QFont.Weight.Bold)

        extra = QTextEdit.ExtraSelection()
        extra.format = highlight_fmt
        extra.cursor = target_cursor

        self.active_highlight_anchor = target_anchor
        self._playback_highlight_selection = extra
        self.update_extra_selections()

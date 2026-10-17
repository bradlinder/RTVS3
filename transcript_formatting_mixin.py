"""Radio & TV Story Segmenter — Interactive Transcript Formatting Mixin.

Provides:
- TranscriptFormattingMixin: Bold, italic, underline, strikethrough, highlight,
  and formatting clear/query methods for InteractiveTranscriptEdit.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Set

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QFont,
        QTextCharFormat,
        QTextCursor,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QFont,
        QTextCharFormat,
        QTextCursor,
    )


class TranscriptFormattingMixin:
    """Mixin for text formatting actions (bold, italic, underline, highlight, clear)."""

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
        if hasattr(self, "formatChanged"):
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
        if hasattr(self, "formatChanged"):
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
        if hasattr(self, "formatChanged"):
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
        if hasattr(self, "formatChanged"):
            self.formatChanged.emit()

    def _get_target_word_indices_for_selection_or_cursor(self, flat_words):
        cursor = self.textCursor()
        total_words = len(flat_words)
        if total_words == 0:
            return set()

        targeted_indices = set()
        seg_word_to_fi = {}
        for f_i, fw in enumerate(flat_words):
            seg_word_to_fi[(fw["seg_idx"], fw["word_idx"])] = f_i

        if cursor.hasSelection():
            sel_start = min(cursor.selectionStart(), cursor.selectionEnd())
            sel_end = max(cursor.selectionStart(), cursor.selectionEnd())

            if hasattr(self, "char_timestamp_map") and self.char_timestamp_map:
                for item in self.char_timestamp_map:
                    if len(item) >= 4:
                        a, b, s_idx, w_idx = item[0], item[1], item[2], item[3]
                        if b > sel_start and a < sel_end:
                            fi = seg_word_to_fi.get((s_idx, w_idx))
                            if fi is not None:
                                targeted_indices.add(fi)

            if not targeted_indices and hasattr(self, "anchor_ranges") and self.anchor_ranges:
                for anchor_name, (a_start, a_end) in self.anchor_ranges.items():
                    if a_end > sel_start and a_start < sel_end:
                        if anchor_name.startswith("w_"):
                            parts = anchor_name.split("_")
                            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                                fi = seg_word_to_fi.get((int(parts[1]), int(parts[2])))
                                if fi is not None:
                                    targeted_indices.add(fi)

            if not targeted_indices:
                doc = self.document()
                start_block = doc.findBlock(sel_start).blockNumber()
                end_block = doc.findBlock(sel_end).blockNumber()
                for f_i, fw in enumerate(flat_words):
                    if start_block <= fw["seg_idx"] <= end_block:
                        targeted_indices.add(f_i)
        else:
            pos = cursor.position()
            if hasattr(self, "char_timestamp_map") and self.char_timestamp_map:
                for item in self.char_timestamp_map:
                    if len(item) >= 4:
                        a, b, s_idx, w_idx = item[0], item[1], item[2], item[3]
                        if a <= pos <= b:
                            fi = seg_word_to_fi.get((s_idx, w_idx))
                            if fi is not None:
                                targeted_indices.add(fi)
                                break

            if not targeted_indices and hasattr(self, "anchor_ranges") and self.anchor_ranges:
                for anchor_name, (a_start, a_end) in self.anchor_ranges.items():
                    if a_start <= pos <= a_end and anchor_name.startswith("w_"):
                        parts = anchor_name.split("_")
                        if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                            fi = seg_word_to_fi.get((int(parts[1]), int(parts[2])))
                            if fi is not None:
                                targeted_indices.add(fi)
                                break

            if not targeted_indices:
                doc = self.document()
                curr_block = doc.findBlock(pos).blockNumber()
                for f_i, fw in enumerate(flat_words):
                    if fw["seg_idx"] == curr_block:
                        targeted_indices.add(f_i)

        return targeted_indices

    def toggle_highlight(self, color_name="#fef08a", force_apply=False):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        current_bg = self.currentCharFormat().background().color()
        has_color = current_bg.isValid() and current_bg.alpha() > 0 and self.currentCharFormat().background().style() != Qt.BrushStyle.NoBrush
        should_apply = force_apply or not has_color

        if should_apply:
            c = QColor(color_name)
            c.setAlpha(220)
            fmt.setBackground(QBrush(c))
            fmt.setForeground(QBrush(QColor("#1e293b")))
        else:
            fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
            fmt.setForeground(QBrush(Qt.BrushStyle.NoBrush))

        main_win = self.window()
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript

        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        if hasattr(main_win, "is_updating_transcript_view"):
            main_win.is_updating_transcript_view = True

        try:
            if cursor.hasSelection():
                sel_start = cursor.selectionStart()
                sel_end = cursor.selectionEnd()
                cursor.mergeCharFormat(fmt)
                cursor.setPosition(sel_start)
                cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
            else:
                self.mergeCurrentCharFormat(fmt)

            if t_data and isinstance(t_data, dict) and "segments" in t_data:
                segments = t_data["segments"]
                flat_words = []
                for s_i, seg in enumerate(segments):
                    words = seg.get("words", [])
                    if words:
                        for w_i, w in enumerate(words):
                            flat_words.append({"seg_idx": s_i, "word_idx": w_i, "word_dict": w})
                    else:
                        flat_words.append({"seg_idx": s_i, "word_idx": -1, "word_dict": seg})

                targeted = self._get_target_word_indices_for_selection_or_cursor(flat_words)
                for f_i in targeted:
                    w_dict = flat_words[f_i]["word_dict"]
                    if should_apply:
                        w_dict["highlight"] = color_name
                    else:
                        w_dict.pop("highlight", None)
        finally:
            if hasattr(main_win, "is_updating_transcript_view"):
                main_win.is_updating_transcript_view = False

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Apply Highlight" if should_apply else "Remove Highlight")

        self.setFocus()
        if hasattr(self, "formatChanged"):
            self.formatChanged.emit()
        if hasattr(self, "update_extra_selections"):
            self.update_extra_selections()

    def remove_highlight(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        fmt.setForeground(QBrush(Qt.BrushStyle.NoBrush))

        main_win = self.window()
        t_data = getattr(self, "transcript_data", None)
        if not t_data and hasattr(main_win, "transcript"):
            t_data = main_win.transcript

        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        if hasattr(main_win, "is_updating_transcript_view"):
            main_win.is_updating_transcript_view = True

        try:
            if cursor.hasSelection():
                sel_start = cursor.selectionStart()
                sel_end = cursor.selectionEnd()
                cursor.mergeCharFormat(fmt)
                cursor.setPosition(sel_start)
                cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
            else:
                self.mergeCurrentCharFormat(fmt)

            if t_data and isinstance(t_data, dict) and "segments" in t_data:
                segments = t_data["segments"]
                flat_words = []
                for s_i, seg in enumerate(segments):
                    words = seg.get("words", [])
                    if words:
                        for w_i, w in enumerate(words):
                            flat_words.append({"seg_idx": s_i, "word_idx": w_i, "word_dict": w})
                    else:
                        flat_words.append({"seg_idx": s_i, "word_idx": -1, "word_dict": seg})

                targeted = self._get_target_word_indices_for_selection_or_cursor(flat_words)
                for f_i in targeted:
                    flat_words[f_i]["word_dict"].pop("highlight", None)
        finally:
            if hasattr(main_win, "is_updating_transcript_view"):
                main_win.is_updating_transcript_view = False

        if before_state and hasattr(main_win, "_commit_project_state_change"):
            main_win._commit_project_state_change(before_state, "Remove Highlight")

        self.setFocus()
        if hasattr(self, "formatChanged"):
            self.formatChanged.emit()
        if hasattr(self, "update_extra_selections"):
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
        if hasattr(self, "formatChanged"):
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

"""transcript_selection_mixin.py - Multi-selection, timeline spans, comment ranges, and bubble actions.

Provides:
- TranscriptSelectionMixin: Mixin for InteractiveTranscriptEdit managing single/multi text selections,
  word/character timestamp mapping, comment extra-selections, and quick-action bubble triggers.
"""

from typing import Optional, List, Dict, Any, Tuple
from core_utils import format_time

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QColor,
        QTextCursor,
        QTextCharFormat,
    )
    from PySide6.QtWidgets import QTextEdit
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QColor,
        QTextCursor,
        QTextCharFormat,
    )
    from PySide6.QtWidgets import QTextEdit


class TranscriptSelectionMixin:
    """Mixin managing selection state, multi-select accumulation, comment highlights,
    and bubble events for InteractiveTranscriptEdit."""

    def set_selection_mode(self, mode: str):
        self.selection_mode = mode if mode in ("replace", "keep") else "replace"
        if self.selection_mode == "replace" and getattr(self, "saved_selections", None):
            self.saved_selections = []
            self.update_extra_selections()

    def set_char_timestamp_map(self, mapping: list):
        self.char_timestamp_map = mapping

    def has_active_selection(self) -> bool:
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

    def get_time_range_for_char_span(self, start_pos: int, end_pos: int) -> Optional[Tuple[float, float]]:
        if not getattr(self, "char_timestamp_map", None):
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

    def get_selected_time_range(self) -> Optional[Tuple[float, float]]:
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

    def get_all_selected_story_ranges(self) -> List[Dict[str, Any]]:
        """Returns a list of dicts: [{'start_time': float, 'end_time': float, 'text': str, ...}, ...]"""
        if getattr(self, "selection_mode", "replace") == "keep" and getattr(self, "saved_selections", None):
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

    def select_comment_range(self, seg_idx: int):
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
                        positions = getattr(self, "anchor_ranges", {}).get(target_anchor)
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

        # Section / Timeline Selection Overlay (Rendered BEFORE playback word so active word stays visible on top)
        if getattr(self, "timeline_selection_span", None) is not None:
            s_char, e_char = self.timeline_selection_span
            fmt = QTextCharFormat()
            if getattr(self, "current_theme", "dark") == "light":
                fmt.setBackground(QColor(186, 215, 255, 170))
                fmt.setForeground(QColor(15, 23, 42))
            else:
                fmt.setBackground(QColor(40, 105, 215, 170))
                fmt.setForeground(QColor(255, 255, 255))

            extra = QTextEdit.ExtraSelection()
            extra.format = fmt
            cursor = QTextCursor(self.document())
            cursor.setPosition(s_char)
            cursor.setPosition(e_char, QTextCursor.MoveMode.KeepAnchor)
            extra.cursor = cursor
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

    def set_timeline_selection_span(self, start_char: Optional[int], end_char: Optional[int]):
        if start_char is not None and end_char is not None and end_char > start_char:
            self.timeline_selection_span = (start_char, end_char)
        else:
            self.timeline_selection_span = None
        self.update_extra_selections()

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

        if getattr(self, "selection_mode", "replace") == "keep":
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
        if hasattr(self, "selection_bubble") and not getattr(self, "is_editing_mode", False) and show_floating:
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
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

    def _on_bubble_note(self):
        win = self.window()
        if hasattr(win, "add_comment_from_selection"):
            win.add_comment_from_selection()
        elif hasattr(win, "edit_segment_comment_dialog"):
            cursor = self.textCursor()
            seg_idx = self.get_segment_index_at_cursor(cursor) if hasattr(self, "get_segment_index_at_cursor") else None
            if seg_idx is None:
                seg_idx = cursor.blockNumber()
            win.edit_segment_comment_dialog(seg_idx)
        elif hasattr(win, "add_note_dialog"):
            win.add_note_dialog()
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

    def _on_bubble_cut(self):
        win = self.window()
        if hasattr(win, "exclude_selection"):
            win.exclude_selection()
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

    def _on_bubble_export(self):
        win = self.window()
        if hasattr(win, "quick_export_selection"):
            win.quick_export_selection()
        if hasattr(self, "selection_bubble"):
            self.selection_bubble.hide()

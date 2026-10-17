"""Radio & TV Story Segmenter — Transcript Timeline & Playback Synchronization Mixin.

Provides:
- TranscriptTimelineSyncMixin: Time anchor maps, document-to-audio timecode lookup,
  extra-selections highlighting for playback, comments, and selection bubbles.
"""

from __future__ import annotations
from bisect import bisect_right
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QColor,
        QFont,
        QTextCharFormat,
        QTextCursor,
    )
    from PySide6.QtWidgets import QTextEdit
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QColor,
        QFont,
        QTextCharFormat,
        QTextCursor,
    )
    from PySide6.QtWidgets import QTextEdit


class TranscriptTimelineSyncMixin:
    """Mixin for audio timecode synchronization, anchor indexing, and playback highlighting."""

    def set_selection_mode(self, mode: str):
        self.selection_mode = mode if mode in ("replace", "keep") else "replace"
        if self.selection_mode == "replace" and getattr(self, "saved_selections", None):
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
        if hasattr(main_win, "statusBar") and main_win.statusBar():
            main_win.statusBar().showMessage("Cleared transcript selection.")

    def get_time_range_for_char_span(self, start_pos, end_pos):
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

    def select_comment_range(self, seg_idx):
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
                        self.comment_spans.append({
                            "start": positions[0],
                            "end": positions[1],
                            "seg_idx": idx,
                            "comment": comment_text.strip(),
                            "selected_text": c_selected,
                            "start_time": float(seg.get("start", 0.0)),
                            "end_time": float(seg.get("end", 0.0)),
                        })

                        if show_highlights:
                            comment_fmt = QTextCharFormat()
                            if getattr(self, "current_theme", "dark") == "light":
                                comment_fmt.setBackground(QColor(254, 240, 138, 220))
                                comment_fmt.setForeground(QColor(133, 77, 14))
                            else:
                                comment_fmt.setBackground(QColor(133, 77, 14, 200))
                                comment_fmt.setForeground(QColor(254, 240, 138))
                            comment_cursor = QTextCursor(doc)
                            comment_cursor.setPosition(positions[0])
                            comment_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)
                            extra = QTextEdit.ExtraSelection()
                            extra.format = comment_fmt
                            extra.cursor = comment_cursor
                            extras.append(extra)

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

        if getattr(self, "saved_selections", None):
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

    def set_timeline_selection_span(self, start_char, end_char):
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

        time_range = self.get_time_range_for_char_span(start_char, end_char)
        if not time_range:
            return

        main_win = self.window()
        if hasattr(main_win, "timeline"):
            main_win.timeline.set_transcript_selection_range(time_range[0], time_range[1])

        if hasattr(self, "selection_bubble"):
            sel_rect = self.cursorRect(cursor)
            bubble_pos = self.mapToGlobal(sel_rect.topLeft())
            self.selection_bubble.move(bubble_pos.x(), max(10, bubble_pos.y() - 40))
            self.selection_bubble.show()

    def _nearest_word_anchor(self, cursor):
        pos = cursor.position()
        best = None
        best_distance = None
        anchor_ranges = getattr(self, "anchor_ranges", {})
        for href, (start_pos, end_pos) in anchor_ranges.items():
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
        target_href = None
        time_anchors = getattr(self, "time_anchor_index", [])
        for _start, _end, href in time_anchors:
            if href.endswith(f":{seg_idx}"):
                target_href = href
                break
        if not target_href:
            return
        positions = getattr(self, "anchor_ranges", {}).get(target_href)
        if not positions:
            return
        cursor = QTextCursor(self.document())
        cursor.setPosition(positions[0])
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def rebuild_anchor_index(self):
        self.anchor_ranges = {}
        exact_char_map = []
        doc = self.document()
        block = doc.begin()
        main_win = self.window()
        segs = (
            main_win.transcript.get("segments", [])
            if hasattr(main_win, "transcript") and main_win.transcript
            else getattr(self, "transcript_data", {}).get("segments", [])
            if isinstance(getattr(self, "transcript_data", None), dict)
            else []
        )
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    href = fragment.charFormat().anchorHref()
                    if href:
                        f_pos = fragment.position()
                        f_len = fragment.length()
                        f_end = f_pos + f_len
                        self.anchor_ranges[href] = (f_pos, f_end)
                        if href.startswith("word:"):
                            parts = href.split(":")
                            if len(parts) >= 3:
                                try:
                                    w_start = float(parts[1])
                                    w_seg = int(parts[2])
                                    w_idx = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else None
                                    w_end = w_start
                                    if 0 <= w_seg < len(segs):
                                        seg = segs[w_seg]
                                        s_words = seg.get("words", [])
                                        if w_idx is not None and 0 <= w_idx < len(s_words) and isinstance(s_words[w_idx], dict):
                                            w_end = float(s_words[w_idx].get("end", seg.get("end", w_start)))
                                        else:
                                            w_end = float(seg.get("end", w_start))
                                    exact_char_map.append((f_pos, f_end, w_start, w_end, w_seg, w_idx))
                                except (ValueError, IndexError):
                                    pass
                it += 1
            block = block.next()
        if exact_char_map:
            self.char_timestamp_map = exact_char_map

    def set_time_anchor_index(self, entries):
        self.time_anchor_index = sorted(entries, key=lambda item: item[0])
        self.time_anchor_starts = [item[0] for item in self.time_anchor_index]

    def clear_highlight(self):
        if not getattr(self, "active_highlight_anchor", None) and getattr(self, "_playback_highlight_selection", None) is None:
            return

        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        self.update_extra_selections()

    def highlight_word_at_time(self, seconds, transcript_data, auto_scroll: bool = False):
        if getattr(self, "is_editing_mode", False) or not transcript_data:
            return

        target_anchor = None
        time_anchors = getattr(self, "time_anchor_index", [])
        anchor_starts = getattr(self, "time_anchor_starts", [])
        if time_anchors:
            idx = bisect_right(anchor_starts, seconds) - 1
            if idx >= 0:
                start_time, end_time, anchor = time_anchors[idx]
                if start_time <= seconds <= end_time or (seconds - end_time) < 0.3:
                    target_anchor = anchor
            elif anchor_starts and seconds < anchor_starts[0]:
                target_anchor = time_anchors[0][2]

        if not target_anchor or target_anchor == getattr(self, "active_highlight_anchor", None):
            return

        doc = self.document()
        anchor_ranges = getattr(self, "anchor_ranges", {})
        positions = anchor_ranges.get(target_anchor)
        if not positions:
            self.rebuild_anchor_index()
            positions = getattr(self, "anchor_ranges", {}).get(target_anchor)

        if not positions:
            self.clear_highlight()
            return

        target_cursor = QTextCursor(doc)
        target_cursor.setPosition(positions[0])
        target_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)

        highlight_fmt = QTextCharFormat()
        theme = getattr(self, "current_theme", "dark")
        if theme == "light":
            highlight_fmt.setForeground(QColor("#0f172a"))
            highlight_fmt.setBackground(QColor(250, 204, 21, 230))
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(217, 119, 6))
        elif theme == "high_contrast":
            highlight_fmt.setForeground(QColor("#000000"))
            highlight_fmt.setBackground(QColor(255, 255, 0, 255))
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(255, 255, 255))
        else:
            highlight_fmt.setForeground(QColor("#000000"))
            highlight_fmt.setBackground(QColor(251, 191, 36, 230))
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(245, 158, 11))
        highlight_fmt.setFontWeight(QFont.Weight.Bold)

        extra = QTextEdit.ExtraSelection()
        extra.format = highlight_fmt
        extra.cursor = target_cursor

        self.active_highlight_anchor = target_anchor
        self.last_active_highlight_anchor = target_anchor
        self._playback_highlight_selection = extra
        self.update_extra_selections()

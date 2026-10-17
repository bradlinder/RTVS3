"""transcript_navigation_mixin.py - Timestamp discovery, caret positioning, anchor indexing, and playback highlighting.

Provides:
- TranscriptNavigationMixin: Mixin for InteractiveTranscriptEdit handling fast O(log N)
  playback word highlighting via QTextEdit.ExtraSelection, anchor map building from live QTextDocument,
  and cursor timestamp/segment resolution.
"""

from bisect import bisect_right
from typing import Optional, Tuple, List, Dict, Any

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QColor,
        QFont,
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
        QFont,
        QTextCursor,
        QTextCharFormat,
    )
    from PySide6.QtWidgets import QTextEdit


class TranscriptNavigationMixin:
    """Mixin managing time anchor indexing, cursor timestamp discovery, and live playback highlighting."""

    def _nearest_word_anchor(self, cursor) -> Optional[Tuple[float, int, str]]:
        """Return the word anchor nearest the actual QTextDocument cursor."""
        pos = cursor.position()
        best = None
        best_distance = None
        ranges = getattr(self, "anchor_ranges", {})
        for href, (start_pos, end_pos) in ranges.items():
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

    def get_timestamp_at_cursor(self, cursor) -> float:
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

    def get_block_start_timestamp(self, cursor) -> float:
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

    def get_block_end_timestamp(self, cursor) -> float:
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

    def get_segment_index_at_cursor(self, cursor) -> Optional[int]:
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

    def move_cursor_to_segment_start(self, seg_idx: int):
        """Best-effort: places the caret at the first word of seg_idx after
        a render_transcript() refresh, so editing can continue in place."""
        target_href = None
        time_index = getattr(self, "time_anchor_index", [])
        for _start, _end, href in time_index:
            if href.endswith(f":{seg_idx}"):
                target_href = href
                break
        if not target_href:
            return
        ranges = getattr(self, "anchor_ranges", {})
        positions = ranges.get(target_href)
        if not positions:
            return
        cursor = QTextCursor(self.document())
        cursor.setPosition(positions[0])
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def rebuild_anchor_index(self):
        """Index transcript anchors once so playback highlighting is O(1) lookup,
        and build 100% document-accurate char_timestamp_map from the live QTextDocument."""
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

    def set_time_anchor_index(self, entries: list):
        self.time_anchor_index = sorted(entries, key=lambda item: item[0])
        self.time_anchor_starts = [item[0] for item in self.time_anchor_index]

    def clear_highlight(self):
        if not getattr(self, "active_highlight_anchor", None) and getattr(self, "_playback_highlight_selection", None) is None:
            return

        self.active_highlight_anchor = None
        self._playback_highlight_selection = None
        if hasattr(self, "update_extra_selections"):
            self.update_extra_selections()

    def highlight_word_at_time(self, seconds: float, transcript_data: dict, auto_scroll: bool = False):
        if getattr(self, "is_editing_mode", False) or not transcript_data:
            return

        target_anchor = None
        time_index = getattr(self, "time_anchor_index", [])
        time_starts = getattr(self, "time_anchor_starts", [])
        if time_index:
            idx = bisect_right(time_starts, seconds) - 1
            if idx >= 0:
                start_time, end_time, anchor = time_index[idx]
                # Allow a small tolerance window or match if within the timestamp block
                if start_time <= seconds <= end_time or (seconds - end_time) < 0.3:
                    target_anchor = anchor
            elif time_starts and seconds < time_starts[0]:
                target_anchor = time_index[0][2]

        if not target_anchor or target_anchor == getattr(self, "active_highlight_anchor", None):
            return

        doc = self.document()
        ranges = getattr(self, "anchor_ranges", {})
        positions = ranges.get(target_anchor)
        if not positions:
            self.rebuild_anchor_index()
            positions = getattr(self, "anchor_ranges", {}).get(target_anchor)

        if not positions:
            self.clear_highlight()
            return

        target_cursor = QTextCursor(doc)
        target_cursor.setPosition(positions[0])
        target_cursor.setPosition(positions[1], QTextCursor.MoveMode.KeepAnchor)

        # Overlay Word Highlighting using QTextEdit.ExtraSelection
        # Prevents document mutations and expensive text reflows during playback
        highlight_fmt = QTextCharFormat()
        theme = getattr(self, "current_theme", "dark")
        if theme == "light":
            highlight_fmt.setForeground(QColor("#0f172a"))  # Sharp dark text for high contrast
            highlight_fmt.setBackground(QColor(250, 204, 21, 230))  # Vibrant gold/yellow background (#facc15)
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(217, 119, 6))
        elif theme == "high_contrast":
            highlight_fmt.setForeground(QColor("#000000"))  # Pure black text
            highlight_fmt.setBackground(QColor(255, 255, 0, 255))  # Pure yellow background
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(255, 255, 255))
        else:
            highlight_fmt.setForeground(QColor("#000000"))  # Sharp black text on gold background
            highlight_fmt.setBackground(QColor(251, 191, 36, 230))  # Vibrant amber/gold (#fbbf24)
            highlight_fmt.setFontUnderline(True)
            highlight_fmt.setUnderlineColor(QColor(245, 158, 11))
        highlight_fmt.setFontWeight(QFont.Weight.Bold)

        extra = QTextEdit.ExtraSelection()
        extra.format = highlight_fmt
        extra.cursor = target_cursor

        self.active_highlight_anchor = target_anchor
        self.last_active_highlight_anchor = target_anchor
        self._playback_highlight_selection = extra
        if hasattr(self, "update_extra_selections"):
            self.update_extra_selections()

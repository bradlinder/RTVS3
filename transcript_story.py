"""Radio & TV Segmenter v3.8.9-beta.15 — transcript story responsibilities.

Methods intentionally retain the MainWindow-facing API so behavior remains
maintaining the established MainWindow-facing API while responsibilities are isolated.
"""

from typing import List, Optional, Tuple
import html
import re
from prs_shared import *
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QRadioButton, QButtonGroup, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox,
    QFrame, QLineEdit, QInputDialog, QListWidgetItem, QDoubleSpinBox, QFormLayout,
    QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor
from speaker_identity import (
    cosine_similarity,
    robust_reference_profile,
    compare_against_profiles,
    is_confident_match,
    centroid,
)


from voice_profile_dialog import VoiceProfileMatchDialog
from speaker_dialogs import ChangeSpeakerDialog, SpeakerManagerDialog
from story_fades_dialog import StoryFadesDialog

__all__ = [
    "TranscriptStoryMixin",
    "ChangeSpeakerDialog",
    "VoiceProfileMatchDialog",
    "StoryFadesDialog",
    "SpeakerManagerDialog",
]

class TranscriptStoryMixin:
    def render_transcript(self):
        if not self.transcript:
            return

        v_scroll = 0
        h_scroll = 0
        if hasattr(self, "transcript_view") and self.transcript_view:
            v_scroll = self.transcript_view.verticalScrollBar().value()
            h_scroll = self.transcript_view.horizontalScrollBar().value()
            self.transcript_view.active_highlight_anchor = None

        self.is_updating_transcript_view = True
        display_mode = getattr(self, "translation_display_mode", "en")
        if display_mode == "bilingual":
            display_mode = "split"
        segments = self.transcript.get("segments", [])
        es_item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else None
        es_segments = es_item.get("segments", []) if isinstance(es_item, dict) else []

        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        active_segments = segments
        is_rendering_translation = False
        if src_code == "es":
            if display_mode == "en" and es_segments:
                active_segments = es_segments
                is_rendering_translation = True
        else:
            if display_mode == "es" and es_segments:
                active_segments = es_segments
                is_rendering_translation = True

        if not active_segments:
            self.transcript_view.setHtml("")
            self.transcript_view.set_char_timestamp_map([])
            self._block_segment_groups = []
            if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
                self._transcript_edit_baseline = self._capture_project_state()
            self.is_updating_transcript_view = False
            return

        word_tokens = []
        for seg_idx, segment in enumerate(active_segments):
            start = segment.get("start", 0.0) if isinstance(segment, dict) else getattr(segment, "start", 0.0)
            end = segment.get("end", start) if isinstance(segment, dict) else getattr(segment, "end", start)
            raw_spk = self.segment_speaker_overrides.get(seg_idx) or self.speaker_at_time(start, end)
            orig_segment = segments[seg_idx] if 0 <= seg_idx < len(segments) else segment
            spk_name = self.get_effective_speaker_name(seg_idx, orig_segment)

            words = [] if is_rendering_translation else segment.get("words", [])
            if words:
                for w_idx, w in enumerate(words):
                    token = {
                        "word": w.get("word", ""),
                        "start": w.get("start", start),
                        "end": w.get("end", end),
                        "seg_idx": seg_idx,
                        "word_idx": w_idx,
                        "speaker_name": spk_name,
                        "raw_speaker": raw_spk,
                        "deleted": bool(w.get("deleted", False)),
                    }
                    if w.get("bold"): token["bold"] = True
                    if w.get("italic"): token["italic"] = True
                    if w.get("underline"): token["underline"] = True
                    if w.get("strike"): token["strike"] = True
                    if w.get("highlight"):
                        hl = w.get("highlight")
                        token["highlight"] = "#fef08a" if isinstance(hl, bool) or hl in ("True", "true", 1) else str(hl)
                    elif segment.get("highlight"):
                        hl = segment.get("highlight")
                        token["highlight"] = "#fef08a" if isinstance(hl, bool) or hl in ("True", "true", 1) else str(hl)
                    word_tokens.append(token)
            else:
                seg_text = segment.get("text", "")
                seg_hl = segment.get("highlight")
                for w_idx, word in enumerate(seg_text.split()):
                    token = {
                        "word": word,
                        "start": start,
                        "end": end,
                        "seg_idx": seg_idx,
                        "word_idx": w_idx,
                        "speaker_name": spk_name,
                        "raw_speaker": raw_spk,
                        "deleted": False,
                    }
                    if seg_hl:
                        token["highlight"] = "#fef08a" if isinstance(seg_hl, bool) or seg_hl in ("True", "true", 1) else str(seg_hl)
                    word_tokens.append(token)

        if not word_tokens:
            self.transcript_view.setHtml("")
            self.transcript_view.set_char_timestamp_map([])
            self._block_segment_groups = []
            if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
                self._transcript_edit_baseline = self._capture_project_state()
            self.is_updating_transcript_view = False
            return

        doc = self.transcript_view.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()

        html_parts = []
        char_timestamp_map = []
        current_char_pos = 0
        block_segment_groups = []

        curr_theme = getattr(self.transcript_view, "current_theme", "dark")
        if curr_theme == "light":
            word_color = "#22262c"
            speaker_color = "#205493"
            time_color = "#545b66"
            spanish_color = "#15803d"
            spanish_tag_color = "#545b66"
        elif curr_theme == "high_contrast":
            word_color = "#ffffff"
            speaker_color = "#00ffff"
            time_color = "#ffff00"
            spanish_color = "#00ff00"
            spanish_tag_color = "#ffff00"
        else:
            word_color = "#ffffff"
            speaker_color = "#58a6ff"
            time_color = "#8b949e"
            spanish_color = "#7ee787"
            spanish_tag_color = "#8b949e"

        curr_para_words = []
        curr_speaker_name = None
        curr_raw_speaker = None
        last_rendered_speaker_name = None

        def render_paragraph_block(p_words, p_speaker_name, p_raw_speaker, is_speaker_change):
            nonlocal current_char_pos
            if not p_words:
                return ""

            start_time = p_words[0]["start"]
            first_seg_idx = p_words[0]["seg_idx"]
            time_str = format_time(start_time, include_millis=getattr(self, "show_milliseconds", False))

            if p_speaker_name and is_speaker_change and self.show_speaker_labels:
                esc_spk = html.escape(p_speaker_name)
                esc_raw = html.escape(str(p_raw_speaker or ""))
                speaker_html = (
                    f'<a href="speaker:{first_seg_idx}:{esc_raw}" style="color:{speaker_color}; font-weight:bold; text-decoration:none;">'
                    f'{esc_spk}:</a> '
                )
            else:
                speaker_html = ""
            plain_prefix = (f"{time_str} " if self.show_timestamps else "")
            if self.show_speaker_labels and p_speaker_name and is_speaker_change:
                plain_prefix += f"{p_speaker_name}: "

            current_char_pos += len(plain_prefix)

            word_html_list = []
            current_hl_color = None
            current_hl_words = []

            def _flush_hl_group():
                nonlocal current_hl_words, current_hl_color
                if not current_hl_words:
                    return
                joined_html = " ".join(current_hl_words)
                if current_hl_color:
                    word_html_list.append(
                        f'<span style="background-color:{current_hl_color}; color:#0f172a; padding:1px 0px; border-radius:2px;">{joined_html}</span>'
                    )
                else:
                    word_html_list.append(joined_html)
                current_hl_words = []

            for i_idx, item in enumerate(p_words):
                w_text = item["word"]
                w_start = item["start"]
                w_seg = item["seg_idx"]
                w_idx = item.get("word_idx", i_idx)

                w_len = len(w_text)
                char_timestamp_map.append((current_char_pos, current_char_pos + w_len, w_start, item.get("end", w_start), w_seg, w_idx))
                current_char_pos += w_len + (1 if i_idx < len(p_words) - 1 else 0)

                esc_w = html.escape(w_text)
                w_style = f"color:{word_color}; text-decoration:none;"
                if item.get("bold"):
                    w_style += " font-weight:bold;"
                if item.get("italic"):
                    w_style += " font-style:italic;"
                if item.get("underline") and item.get("strike"):
                    w_style += " text-decoration:underline line-through;"
                elif item.get("underline"):
                    w_style += " text-decoration:underline;"
                elif item.get("strike"):
                    w_style += " text-decoration:line-through;"

                hl_val = item.get("highlight")
                item_hl_color = None
                if hl_val:
                    item_hl_color = "#fef08a" if isinstance(hl_val, bool) or hl_val in ("True", "true", 1) else str(hl_val)
                    w_style += f" color:#0f172a;"

                if item_hl_color != current_hl_color:
                    _flush_hl_group()
                    current_hl_color = item_hl_color

                current_hl_words.append(f'<a href="word:{w_start}:{w_seg}:{w_idx}" style="{w_style}">{esc_w}</a>')

            _flush_hl_group()
            current_char_pos += 1

            body_content = " ".join(word_html_list)

            timestamp_html = (
                f'<a href="time:{start_time}" style="color:{time_color}; text-decoration:none;"><b>{time_str}</b></a> '
                if self.show_timestamps else ""
            )

            if display_mode in ("split", "bilingual") and es_segments:
                seg_indices = list(dict.fromkeys(item["seg_idx"] for item in p_words))
                es_text_parts = [es_segments[idx].get("text", "") for idx in seg_indices if 0 <= idx < len(es_segments)]
                es_text = " ".join(t.strip() for t in es_text_parts if t.strip())
                if es_text:
                    esc_es_text = html.escape(es_text)
                    src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
                    tag_label = "EN: " if src_code == "es" else "ES: "
                    return (
                        f'<p style="margin-bottom: 14px;">'
                        f'{timestamp_html}{speaker_html}'
                        f'<span style="color:{word_color};">{body_content}</span><br/>'
                        f'<span style="color:{spanish_tag_color}; font-weight:bold; font-size:0.86em;">{tag_label}</span>'
                        f'<span style="color:{spanish_color};"><i>{esc_es_text}</i></span>'
                        f'</p>'
                    )

            return (
                f'<p style="margin-bottom: 14px; color: {word_color};">'
                f'{timestamp_html}{speaker_html}'
                f'<span style="color:{word_color};">{body_content}</span>'
                f'</p>'
            )

        def _summarize_paragraph_segments(p_words):
            groups = []
            for w in p_words:
                seg_idx = w["seg_idx"]
                if groups and groups[-1][0] == seg_idx:
                    groups[-1] = (seg_idx, groups[-1][1] + 1)
                else:
                    groups.append((seg_idx, 1))
            return groups

        min_words = int(
            getattr(self, "min_words_per_paragraph", None)
            or getattr(getattr(self, "transcript_view", None), "min_words_per_paragraph", None)
            or (self.settings_store.value("min_words_per_paragraph", MIN_WORDS_PER_PARAGRAPH) if hasattr(self, "settings_store") else MIN_WORDS_PER_PARAGRAPH)
            or MIN_WORDS_PER_PARAGRAPH
        )

        for token_idx, token in enumerate(word_tokens):
            spk_name = token["speaker_name"]
            raw_spk = token["raw_speaker"]

            if curr_speaker_name is None:
                curr_speaker_name = spk_name
                curr_raw_speaker = raw_spk

            # Inherit current speaker over short unassigned or unknown speaker gaps
            if not spk_name and curr_speaker_name:
                spk_name = curr_speaker_name
                raw_spk = curr_raw_speaker

            speaker_changed = (spk_name != curr_speaker_name)
            prev_token = curr_para_words[-1] if curr_para_words else None
            time_gap = (token["start"] - prev_token["end"]) if prev_token and "end" in prev_token and "start" in token else 0.0
            prev_word_ended_sentence = prev_token and is_sentence_end(prev_token["word"])
            word_count = len(curr_para_words)

            silence_thresh = float(getattr(self, "silence_threshold", 3.0) or 3.0)
            major_silence = (time_gap >= max(2.5, silence_thresh))

            # Prevent orphan sentences: If breaking now would leave an isolated, short sentence fragment
            # (< 25 words) before the current speaker's turn ends, keep the remaining words in the current
            # paragraph instead of creating an unnatural single-sentence paragraph.
            leave_orphan = False
            if word_count >= min_words and prev_word_ended_sentence and not speaker_changed:
                rem_speaker_words = 0
                for nxt in word_tokens[token_idx:]:
                    nxt_spk = nxt["speaker_name"] or curr_speaker_name
                    if nxt_spk != curr_speaker_name:
                        break
                    rem_speaker_words += 1
                if 0 < rem_speaker_words < 25 and word_count < (min_words * 2):
                    leave_orphan = True

            # Within the same speaker turn, paragraph breaks must only occur at
            # natural sentence boundaries to prevent mid-sentence fragments with
            # stray timecode markers.
            should_break = (
                speaker_changed
                or (major_silence and prev_word_ended_sentence)
                or (word_count >= min_words and prev_word_ended_sentence and not leave_orphan)
            )

            if curr_para_words and should_break:
                is_change = (curr_speaker_name != last_rendered_speaker_name)
                html_parts.append(render_paragraph_block(curr_para_words, curr_speaker_name, curr_raw_speaker, is_change))
                block_segment_groups.append(_summarize_paragraph_segments(curr_para_words))
                last_rendered_speaker_name = curr_speaker_name

                curr_para_words = [token]
                curr_speaker_name = spk_name
                curr_raw_speaker = raw_spk
            else:
                curr_para_words.append(token)

        if curr_para_words:
            is_change = (curr_speaker_name != last_rendered_speaker_name)
            html_parts.append(render_paragraph_block(curr_para_words, curr_speaker_name, curr_raw_speaker, is_change))
            block_segment_groups.append(_summarize_paragraph_segments(curr_para_words))

        self.transcript_view.setHtml("".join(html_parts))
        cursor.endEditBlock()
        self._block_segment_groups = block_segment_groups

        self.timeline.set_transcript_selection_range(None, None)
        self.transcript_view.rebuild_anchor_index()
        self.transcript_view.set_time_anchor_index(
            [
                (item["start"], item["end"], f"word:{item['start']}:{item['seg_idx']}:{item.get('word_idx', 0)}")
                for item in word_tokens
            ]
        )
        self.transcript_view.set_char_timestamp_map(char_timestamp_map)
        if hasattr(self, "comments_panel"):
            self.comments_panel.set_comments(self.transcript.get("segments", []))
        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

        if hasattr(self, "transcript_view") and self.transcript_view:
            self.transcript_view.active_highlight_anchor = None
            if hasattr(self.transcript_view, "lock_scroll_position"):
                self.transcript_view.lock_scroll_position(v_scroll, h_scroll, duration_ms=400)
            else:
                self.transcript_view.verticalScrollBar().setValue(v_scroll)
                self.transcript_view.horizontalScrollBar().setValue(h_scroll)

            def _restore_scroll(vs=v_scroll, hs=h_scroll):
                if hasattr(self, "transcript_view") and self.transcript_view:
                    self.transcript_view.verticalScrollBar().setValue(vs)
                    self.transcript_view.horizontalScrollBar().setValue(hs)
            QTimer.singleShot(0, _restore_scroll)
            QTimer.singleShot(25, _restore_scroll)
            QTimer.singleShot(60, _restore_scroll)
            QTimer.singleShot(150, _restore_scroll)

            cur_pos = getattr(self, "current_position", 0.0)
            if cur_pos >= 0 and hasattr(self.transcript_view, "highlight_word_at_time"):
                self.transcript_view.highlight_word_at_time(cur_pos, self.transcript, auto_scroll=False)

        if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
            self._transcript_edit_baseline = self._capture_project_state()
        self.is_updating_transcript_view = False

        if hasattr(self, "transcript_mode_toggle_btn"):
            if display_mode in ("split", "bilingual"):
                self.transcript_mode_toggle_btn.setEnabled(False)
                self.transcript_mode_toggle_btn.setChecked(False)
                self.transcript_mode_toggle_btn.setText("Edit Transcript")
                self.transcript_mode_toggle_btn.setStyleSheet("")
            else:
                self.transcript_mode_toggle_btn.setEnabled(True)
                is_editing = getattr(self.transcript_view, "is_editing_mode", False)
                self.transcript_mode_toggle_btn.setChecked(is_editing)
                if is_editing:
                    self.transcript_mode_toggle_btn.setText("View Transcript")
                    self.transcript_mode_toggle_btn.setStyleSheet("font-weight: bold; background-color: #2b5278; color: white;")
                else:
                    self.transcript_mode_toggle_btn.setText("Edit Transcript")
                    self.transcript_mode_toggle_btn.setStyleSheet("")

        if display_mode in ("split", "bilingual"):
            self.transcript_view.setReadOnly(True)
        else:
            self.transcript_view.setReadOnly(not getattr(self.transcript_view, "is_editing_mode", False))

    def on_transcript_selection_changed(self):
        if self.is_updating_transcript_view:
            return
        selected_range = self.transcript_view.get_selected_time_range()
        if selected_range:
            self.last_position_source = "transcript"
            self.timeline.set_transcript_selection_range(*selected_range)
            self.statusBar().showMessage(
                f"Transcript selection: {format_time(selected_range[0])} – {format_time(selected_range[1])}"
            )
        else:
            if not getattr(self.transcript_view, "has_active_selection", lambda: False)():
                self.timeline.set_transcript_selection_range(None, None)
            cursor = self.transcript_view.textCursor()
            ts = self.transcript_view.get_timestamp_at_cursor(cursor)
            if ts is not None and ts >= 0:
                self.last_transcript_cursor_time = ts
                self.last_position_source = "transcript"

        cursor = self.transcript_view.textCursor()
        target_seg = self.transcript_view.get_segment_index_at_cursor(cursor)
        if target_seg is None:
            target_seg = cursor.blockNumber()

        active_comment_seg = None
        segments = self.transcript.get("segments", []) if self.transcript else []
        if 0 <= target_seg < len(segments):
            seg = segments[target_seg]
            if (seg.get("comments") or seg.get("notes", "")).strip():
                active_comment_seg = target_seg

        if hasattr(self, "comments_panel"):
            self.comments_panel.highlight_segment(active_comment_seg)

    def on_transcript_text_changed(self):
        if self.is_updating_transcript_view or getattr(self, "is_restoring_undo", False) or not self.transcript:
            return
        if hasattr(self, "transcript_view") and not getattr(self.transcript_view, "is_editing_mode", False):
            return
        display_mode = getattr(self, "translation_display_mode", "en")
        if display_mode in ("split", "bilingual"):
            return

        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        use_translation = (display_mode == "en") if src_code == "es" else (display_mode == "es")

        if use_translation:
            es_item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else None
            if not es_item or not isinstance(es_item, dict):
                return
            target_segments = es_item.get("segments", [])
        else:
            target_segments = self.transcript.get("segments", [])

        if not target_segments:
            return

        doc = self.transcript_view.document()
        blocks_count = doc.blockCount()
        block_groups = getattr(self, "_block_segment_groups", None) or []
        known_speaker_labels = None

        def _extract_block_word_formatting(block, prefix_len=0):
            word_formats = []
            it = block.begin()
            curr_pos = 0
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    frag_text = frag.text()
                    fmt = frag.charFormat()
                    frag_len = len(frag_text)
                    frag_start = curr_pos
                    frag_end = curr_pos + frag_len
                    if frag_end > prefix_len:
                        start_in_frag = max(0, prefix_len - frag_start)
                        usable_text = frag_text[start_in_frag:]
                        is_bold = fmt.fontWeight() > QFont.Weight.Medium
                        is_italic = fmt.fontItalic()
                        is_underline = fmt.fontUnderline()
                        is_strike = fmt.fontStrikeOut()
                        bg = fmt.background().color()
                        highlight = bg.name() if (bg.isValid() and bg.alpha() > 0 and fmt.background().style() != Qt.BrushStyle.NoBrush) else None
                        for w in usable_text.split():
                            word_formats.append({
                                "word": w,
                                "bold": is_bold,
                                "italic": is_italic,
                                "underline": is_underline,
                                "strike": is_strike,
                                "highlight": highlight,
                            })
                    curr_pos += frag_len
                it += 1
            return word_formats

        for i in range(min(blocks_count, len(block_groups))):
            groups = [g for g in block_groups[i] if 0 <= g[0] < len(target_segments)]
            if not groups:
                continue

            block = doc.findBlockByNumber(i)
            block_text = block.text()
            # Strip optional leading bracketed or bare timestamp e.g. "0:27", "00:27", "01:02:30.500", "[00:27]"
            cleaned_text = re.sub(r'^\s*\[?(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\.\d{1,3})?\]?\s+', '', block_text)
            if ": " in cleaned_text:
                prefix, remainder = cleaned_text.split(": ", 1)
                if known_speaker_labels is None:
                    known_speaker_labels = set(str(x).strip() for x in self.speaker_names.values() if x)
                    known_speaker_labels.update(
                        str(x).strip() for x in (self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []) if x
                    )
                if prefix.strip() in known_speaker_labels or re.match(r'^Speaker\s+\d+$', prefix.strip(), re.IGNORECASE):
                    cleaned_text = remainder
            cleaned_text = re.sub(r'^Speaker\s+\d+:\s*', '', cleaned_text, flags=re.IGNORECASE).strip()

            prefix_len = block_text.find(cleaned_text) if (cleaned_text and cleaned_text in block_text) else 0
            block_fmts = _extract_block_word_formatting(block, prefix_len)

            if len(groups) == 1:
                target_seg = target_segments[groups[0][0]]
                target_seg["text"] = cleaned_text
                self.sync_segment_words(target_seg, cleaned_text, block_fmts)
                continue

            words = cleaned_text.split()
            total_original_words = sum(g[1] for g in groups) or 1
            remaining_words = words
            remaining_fmts = block_fmts
            for gi, (seg_idx, orig_count) in enumerate(groups):
                if gi == len(groups) - 1:
                    share, remaining_words = remaining_words, []
                    share_fmts, remaining_fmts = remaining_fmts, []
                else:
                    n = round(len(words) * (orig_count / total_original_words))
                    n = max(0, min(n, len(remaining_words)))
                    share, remaining_words = remaining_words[:n], remaining_words[n:]
                    share_fmts, remaining_fmts = remaining_fmts[:n], remaining_fmts[n:]
                seg_text = " ".join(share)
                target_segments[seg_idx]["text"] = seg_text
                self.sync_segment_words(target_segments[seg_idx], seg_text, share_fmts)

        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

        if getattr(self, "_pending_transcript_edit_before", None) is None:
            baseline = getattr(self, "_transcript_edit_baseline", None)
            if baseline is not None:
                self._pending_transcript_edit_before = baseline

        timer = getattr(self, "_transcript_undo_timer", None)
        if timer is not None:
            timer.start()

        self.mark_project_dirty()

    def transcript_clicked(self, url):
        text = url.toString()
        if text.startswith("time:") or text.startswith("word:"):
            parts = text.split(":")
            seconds = float(parts[1])
            self.last_position_source = "transcript"
            self.last_transcript_cursor_time = seconds
            self.seek_to(seconds)
            if hasattr(self.transcript_view, "move_cursor_to_time"):
                self.transcript_view.move_cursor_to_time(seconds, self.transcript)
        elif text.startswith("speaker:"):
            parts = text.split(":", 2)
            if len(parts) >= 2 and parts[1].isdigit():
                seg_idx = int(parts[1])
                raw_spk = parts[2] if len(parts) > 2 else ""
                if hasattr(self, "prompt_rename_speaker"):
                    self.prompt_rename_speaker(seg_idx, raw_spk)

    def edit_segment_comment_dialog(
        self,
        seg_idx: int,
        sel_text: str = "",
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
        t_range: Optional[tuple[float, float]] = None,
        covered_indices: Optional[List[int]] = None
    ):
        if not self.transcript or "segments" not in self.transcript:
            QMessageBox.information(self, "No Transcript", "No transcript is currently loaded.")
            return
        segments = self.transcript["segments"]
        if not (0 <= seg_idx < len(segments)):
            return
        seg = segments[seg_idx]
        current_comment = seg.get("comments") or seg.get("notes", "")

        if not sel_text:
            sel_text = seg.get("comment_selected_text", "")

        prompt = f"Comment for Segment {seg_idx + 1} ({format_time(seg.get('start', 0.0))}):"
        if sel_text:
            disp_quote = sel_text if len(sel_text) <= 80 else sel_text[:77] + "..."
            prompt = f'Comment for selection: "{disp_quote}"'

        dialog = CommentEditorDialog(
            self,
            comment_text=current_comment,
            title="Edit Comment" if current_comment else "Add Comment",
            prompt=prompt,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
            target_indices = [seg_idx]
            if dialog.is_deleted():
                for idx in target_indices:
                    if 0 <= idx < len(segments):
                        s = segments[idx]
                        s.pop("comments", None)
                        s.pop("notes", None)
                        s.pop("comment_selected_text", None)
                        s.pop("comment_char_start", None)
                        s.pop("comment_char_end", None)
                        s.pop("comment_start_time", None)
                        s.pop("comment_end_time", None)
            else:
                text = dialog.get_comment_text()
                if text.strip():
                    for idx in target_indices:
                        if 0 <= idx < len(segments):
                            s = segments[idx]
                            s["comments"] = text
                            s["notes"] = text
                            if sel_text:
                                s["comment_selected_text"] = sel_text
                            if start_char is not None and end_char is not None:
                                s["comment_char_start"] = start_char
                                s["comment_char_end"] = end_char
                            if t_range:
                                s["comment_start_time"] = t_range[0]
                                s["comment_end_time"] = t_range[1]
                else:
                    for idx in target_indices:
                        if 0 <= idx < len(segments):
                            s = segments[idx]
                            s.pop("comments", None)
                            s.pop("notes", None)
                            s.pop("comment_selected_text", None)
                            s.pop("comment_char_start", None)
                            s.pop("comment_char_end", None)
                            s.pop("comment_start_time", None)
                            s.pop("comment_end_time", None)

            self.mark_project_dirty()
            if hasattr(self, "transcript_view"):
                self.transcript_view.update_extra_selections()
            if hasattr(self, "comments_panel"):
                self.comments_panel.set_comments(segments)
                self.comments_panel.highlight_segment(seg_idx)
            if before_state and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, "Update Comment")

    edit_segment_note_dialog = edit_segment_comment_dialog

    def add_comment_from_selection(self):
        if not hasattr(self, "transcript_view") or not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript.get("segments", [])
        cursor = self.transcript_view.textCursor()
        sel_text = ""
        start_char = None
        end_char = None
        t_range = None
        covered_indices = []

        if cursor.hasSelection():
            sel_text = cursor.selectedText().replace('\u2029', '\n').strip()
            start_char = min(cursor.selectionStart(), cursor.selectionEnd())
            end_char = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self.transcript_view, "get_time_range_for_char_span"):
                t_range = self.transcript_view.get_time_range_for_char_span(start_char, end_char)

        if t_range and t_range[0] is not None and t_range[1] is not None:
            st, et = t_range
            for i, s in enumerate(segments):
                s_start = s.get("start", 0.0)
                s_end = s.get("end", 0.0)
                if s_start < et and s_end > st:
                    covered_indices.append(i)

        seg_idx = None
        if covered_indices:
            seg_idx = covered_indices[0]
        else:
            seg_idx = self.transcript_view.get_segment_index_at_cursor(cursor)
            if seg_idx is None:
                seg_idx = cursor.blockNumber()

        if seg_idx is not None and 0 <= seg_idx < len(segments):
            self.edit_segment_comment_dialog(
                seg_idx,
                sel_text=sel_text,
                start_char=start_char,
                end_char=end_char,
                t_range=t_range,
                covered_indices=covered_indices
            )

    def delete_segment_comment(self, seg_idx):
        if not self.transcript or "segments" not in self.transcript:
            return
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        segments = self.transcript["segments"]
        if 0 <= seg_idx < len(segments):
            seg = segments[seg_idx]
            seg.pop("comments", None)
            seg.pop("notes", None)
            seg.pop("comment_selected_text", None)
            seg.pop("comment_char_start", None)
            seg.pop("comment_char_end", None)
            seg.pop("comment_start_time", None)
            seg.pop("comment_end_time", None)
            self.mark_project_dirty()
            if hasattr(self, "transcript_view"):
                self.transcript_view.update_extra_selections()
            if hasattr(self, "comments_panel"):
                self.comments_panel.set_comments(segments)
            if before_state and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, "Delete Comment")

    def toggle_comments_panel(self):
        if hasattr(self, "comments_panel"):
            is_vis = not self.comments_panel.isVisible()
            self.toggle_show_comments(is_vis)

    def toggle_show_comments(self, checked):
        self.show_comments = checked
        self.show_notes = checked
        if hasattr(self, "comments_panel"):
            self.comments_panel.setVisible(checked)
        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

    toggle_show_notes = toggle_show_comments

    def toggle_comment_highlights(self, checked):
        self.show_comment_highlights = checked
        if hasattr(self, "transcript_view"):
            self.transcript_view.show_comment_highlights = checked
            self.transcript_view.update_extra_selections()

    def handle_insert_speaker_request(self, seg_idx, split_time, speaker_name):
        if speaker_name == "__NEW__":
            self.add_speaker_label_at(seg_idx, split_time, name=None)
        else:
            self.add_speaker_label_at(seg_idx, split_time, name=speaker_name)

    def add_speaker_label_at(self, seg_idx, split_time, name=None):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if not segments:
            return False

        if seg_idx is None or seg_idx < 0 or seg_idx >= len(segments):
            for i, seg in enumerate(segments):
                s_start = float(seg.get("start", 0.0))
                s_end = float(seg.get("end", s_start))
                if s_start <= split_time <= s_end:
                    seg_idx = i
                    break
            if seg_idx is None:
                seg_idx = max(0, min(len(segments) - 1, int(seg_idx or 0)))

        if name is None:
            known = self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []
            if known:
                name, accepted = QInputDialog.getItem(
                    self, "Add Speaker Label", "Speaker name for this label:", known, 0, True
                )
            else:
                name, accepted = QInputDialog.getText(self, "Add Speaker Label", "Speaker name for this label:")
            if not accepted:
                return False

        name = (name or "").strip()
        if not name:
            return False

        target_seg = segments[seg_idx]
        words = target_seg.get("words", [])

        is_at_segment_start = False
        if words:
            if split_time <= words[0].get("start", target_seg["start"]) + 0.05:
                is_at_segment_start = True
        else:
            if split_time <= float(target_seg.get("start", 0.0)) + 0.1:
                is_at_segment_start = True

        if is_at_segment_start:
            self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

            current_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = name
                self.segment_speaker_overrides[idx] = override_key
            self._diar_index_key = None

            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Add Speaker Label ({name})")

            self.add_custom_speaker_to_glossary(name)
            self.save_project()
            self.render_transcript()
            return True

        if not self.split_segment_at_time(seg_idx, split_time, new_speaker_name=name):
            self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

            current_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = name
                self.segment_speaker_overrides[idx] = override_key
            self._diar_index_key = None

            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Add Speaker Label ({name})")

            self.add_custom_speaker_to_glossary(name)
            self.save_project()
            self.render_transcript()
            return True

        self.add_custom_speaker_to_glossary(name)
        return True

    def split_segment_at_time(self, seg_idx, split_time, new_speaker_name=None):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return False

        target_seg = segments[seg_idx]
        words = target_seg.get("words", [])

        if words:
            split_idx = -1
            for w_i, w in enumerate(words):
                if w.get("start", target_seg["start"]) >= split_time - 0.01:
                    split_idx = w_i
                    break

            if split_idx <= 0 or split_idx >= len(words):
                return False

            left_words = words[:split_idx]
            right_words = words[split_idx:]

            seg1 = dict(target_seg)
            seg1["end"] = left_words[-1].get("end", split_time)
            seg1["words"] = left_words
            seg1["text"] = " ".join(w.get("word", "") for w in left_words)

            seg2 = dict(target_seg)
            seg2["start"] = right_words[0].get("start", split_time)
            seg2["words"] = right_words
            seg2["text"] = " ".join(w.get("word", "") for w in right_words)
        else:
            seg_text = target_seg.get("text", "").split()
            if len(seg_text) < 2:
                return False

            seg_start = float(target_seg.get("start", split_time))
            seg_end = float(target_seg.get("end", split_time))
            duration = max(0.0, seg_end - seg_start)
            ratio = max(0.0, min(1.0, (float(split_time) - seg_start) / duration)) if duration > 0 else 0.5
            split_word = max(1, min(len(seg_text) - 1, round(len(seg_text) * ratio)))

            seg1 = dict(target_seg)
            seg1["end"] = float(split_time)
            seg1["text"] = " ".join(seg_text[:split_word])

            seg2 = dict(target_seg)
            seg2["start"] = float(split_time)
            seg2["text"] = " ".join(seg_text[split_word:])

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        orig_spk_name = self.get_effective_speaker_name(seg_idx, target_seg)
        segments[seg_idx] = seg1
        segments.insert(seg_idx + 1, seg2)

        new_overrides = {}
        for idx_k, spk in self.segment_speaker_overrides.items():
            k = int(idx_k)
            if k <= seg_idx:
                new_overrides[k] = spk
            else:
                new_overrides[k + 1] = spk
        self.segment_speaker_overrides = new_overrides

        if new_speaker_name:
            target_spk = str(new_speaker_name).strip()
            section_indices = [seg_idx + 1]
            for i in range(seg_idx + 2, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == orig_spk_name:
                    section_indices.append(i)
                else:
                    break

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target_spk
                self.segment_speaker_overrides[idx] = override_key

        self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Add Speaker Label{' (' + str(new_speaker_name) + ')' if new_speaker_name else ''}"
            )

        segments[seg_idx].pop("embedding", None)
        segments[seg_idx + 1].pop("embedding", None)

        left_speaker = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        right_speaker = self.get_effective_speaker_name(seg_idx + 1, segments[seg_idx + 1])

        self.register_confirmed_speaker_turn(seg_idx, left_speaker)
        self.register_confirmed_speaker_turn(seg_idx + 1, right_speaker)
        
        self.save_project()
        self.render_transcript()
        return True

    def prompt_rename_custom_speaker(self, old_name):
        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        new_name, accepted = QInputDialog.getText(
            self,
            "Rename Speaker",
            f"Enter new name for {old_name}:",
            QLineEdit.EchoMode.Normal,
            old_name,
        )
        if accepted and new_name.strip():
            self.speaker_names[f"CUSTOM_{old_name}"] = new_name.strip()
            self.add_custom_speaker_to_glossary(new_name.strip())
            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Rename Speaker: {old_name} → {new_name.strip()}")
            self.render_transcript()
            self.save_project()

    def display_speaker(self, speaker):
        if speaker is None:
            return ""

        speaker = str(speaker)
        custom_name = self.speaker_names.get(speaker)
        if custom_name:
            return custom_name

        match = re.search(r"(\d+)$", speaker)
        if match:
            number = int(match.group(1)) + 1
            return f"Speaker {number}"

        return speaker

    def get_all_known_speakers(self):
        speakers = set()
        if hasattr(self, "speaker_names") and self.speaker_names:
            for k, v in self.speaker_names.items():
                if v and isinstance(v, str) and v.strip() and not k.startswith("SEG_"):
                    speakers.add(v.strip())
        if getattr(self, "transcript", None) and isinstance(self.transcript, dict) and "segments" in self.transcript:
            for idx, seg in enumerate(self.transcript["segments"]):
                name = self.get_effective_speaker_name(idx, seg)
                if name and name.strip():
                    speakers.add(name.strip())
        diar_data = getattr(self, "diarization_result", None) or getattr(self, "diarization", None)
        if isinstance(diar_data, dict) and "segments" in diar_data:
            for seg in diar_data["segments"]:
                spk = seg.get("speaker")
                if spk:
                    disp = self.display_speaker(spk)
                    if disp and disp.strip():
                        speakers.add(disp.strip())
        if hasattr(self, "custom_speakers") and self.custom_speakers:
            for spk in self.custom_speakers:
                if spk and isinstance(spk, str) and spk.strip():
                    speakers.add(spk.strip())

        def natural_sort_key(s):
            is_speaker_num = s.startswith("Speaker ") and s[8:].isdigit()
            if is_speaker_num:
                return (0, int(s[8:]), s.lower())
            return (1, 0, [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)])

        return sorted(speakers, key=natural_sort_key)

    def execute_speaker_rename(self, seg_idx, raw_speaker, target_name):
        if not self.transcript or "segments" not in self.transcript:
            return
        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return

        v_scroll_before = self.transcript_view.verticalScrollBar().value() if hasattr(self, "transcript_view") and self.transcript_view else 0
        h_scroll_before = self.transcript_view.horizontalScrollBar().value() if hasattr(self, "transcript_view") and self.transcript_view else 0

        current_name = (
            self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            if seg_idx < len(segments)
            else self.display_speaker(raw_speaker)
        )

        if target_name == "__NEW__":
            new_name, accepted = QInputDialog.getText(
                self,
                "New Speaker Name",
                f"Enter new name for '{current_name}':",
                QLineEdit.EchoMode.Normal,
                "",
            )
            if not accepted or not new_name.strip():
                if hasattr(self, "transcript_view") and self.transcript_view:
                    self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
                return
            target_name = new_name.strip()
        else:
            target_name = str(target_name).strip()

        if not target_name or target_name == current_name:
            if hasattr(self, "transcript_view") and self.transcript_view:
                self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
            return

        spk_dlg = ChangeSpeakerDialog(current_name, target_name, seg_idx=seg_idx, parent=self)
        spk_dlg.exec()
        if spk_dlg.choice not in ("all", "subsequent", "single"):
            if hasattr(self, "transcript_view") and self.transcript_view:
                self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
            return

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        if spk_dlg.choice == "all":
            if raw_speaker:
                self.speaker_names[str(raw_speaker)] = target_name
            self.add_custom_speaker_to_glossary(target_name)
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == current_name:
                    override_key = f"SEG_{idx}_SPEAKER"
                    self.speaker_names[override_key] = target_name
                    self.segment_speaker_overrides[idx] = override_key
        elif spk_dlg.choice == "subsequent":
            self.add_custom_speaker_to_glossary(target_name)
            start_seg_idx = seg_idx if seg_idx >= 0 else 0
            for idx in range(start_seg_idx, len(segments)):
                if self.get_effective_speaker_name(idx, segments[idx]) == current_name:
                    override_key = f"SEG_{idx}_SPEAKER"
                    self.speaker_names[override_key] = target_name
                    self.segment_speaker_overrides[idx] = override_key

            if self.diarization and isinstance(self.diarization, dict):
                sec_start = float(segments[start_seg_idx].get("start", 0.0))
                if "segments" in self.diarization:
                    for d_seg in self.diarization["segments"]:
                        d_start = float(d_seg.get("start", 0.0))
                        if d_start >= sec_start:
                            disp = self.display_speaker(str(d_seg.get("speaker", "")))
                            if disp == current_name or d_seg.get("speaker") == current_name:
                                d_seg["speaker"] = target_name
                    self._diar_index_key = None
        elif spk_dlg.choice == "single":
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            self.add_custom_speaker_to_glossary(target_name)
            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target_name
                self.segment_speaker_overrides[idx] = override_key

            if self.diarization and isinstance(self.diarization, dict):
                sec_start = float(segments[section_indices[0]].get("start", 0.0))
                sec_end = float(segments[section_indices[-1]].get("end", sec_start))
                if "segments" in self.diarization:
                    for d_seg in self.diarization["segments"]:
                        d_start = float(d_seg.get("start", 0.0))
                        d_end = float(d_seg.get("end", 0.0))
                        if d_start < sec_end and d_end > sec_start:
                            disp = self.display_speaker(str(d_seg.get("speaker", "")))
                            if disp == current_name or d_seg.get("speaker") == current_name:
                                d_seg["speaker"] = target_name
                    self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, f"Change Speaker: {current_name} → {target_name}")

        if hasattr(self, "transcript_view") and self.transcript_view:
            self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=400)

        self.render_transcript()
        self.save_project()
        self.statusBar().showMessage(f"Updated speaker to: {target_name}")

    def prompt_rename_speaker(self, seg_idx, speaker):
        self.execute_speaker_rename(seg_idx, speaker, "__NEW__")

    def remove_speaker_label_at_segment(self, seg_idx):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if seg_idx <= 0 or seg_idx >= len(segments):
            return False

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        prev_seg_idx = seg_idx - 1
        target_name = self.get_effective_speaker_name(prev_seg_idx, segments[prev_seg_idx])
        target_raw = (
            self.segment_speaker_overrides.get(prev_seg_idx) 
            or self.speaker_for_segment(segments[prev_seg_idx])
        )

        removed_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        section_indices = []
        for i in range(seg_idx, len(segments)):
            if self.get_effective_speaker_name(i, segments[i]) == removed_name:
                section_indices.append(i)
            else:
                break

        if not section_indices:
            return False

        section_indices_set = set(section_indices)

        for idx in section_indices:
            instance_key = f"SEG_{idx}_SPEAKER"
            self.speaker_names[instance_key] = target_name
            self.segment_speaker_overrides[idx] = instance_key

        if self.diarization and isinstance(self.diarization, dict):
            sec_start = float(segments[section_indices[0]].get("start", 0.0))
            sec_end = float(segments[section_indices[-1]].get("end", sec_start))
            diar_segs = self.diarization.get("segments", [])
            updated_diar = False
            new_diar_speaker = target_raw or f"SEG_{prev_seg_idx}_SPEAKER"

            for d_seg in diar_segs:
                d_start = float(d_seg.get("start", 0.0))
                d_end = float(d_seg.get("end", d_start))
                overlap = min(sec_end, d_end) - max(sec_start, d_start)
                if overlap <= 0.001:
                    continue

                best_seg_idx = None
                best_seg_overlap = 0.0

                for s_idx in section_indices:
                    t_seg = segments[s_idx]
                    t_start = float(t_seg.get("start", 0.0))
                    t_end = float(t_seg.get("end", t_start))
                    cur_overlap = min(t_end, d_end) - max(t_start, d_start)
                    if cur_overlap > best_seg_overlap:
                        best_seg_overlap = cur_overlap
                        best_seg_idx = s_idx

                if best_seg_idx in section_indices_set:
                    d_seg["speaker"] = new_diar_speaker
                    updated_diar = True

            if updated_diar:
                self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Remove Speaker Label: {removed_name} → {target_name} (turn at #{seg_idx + 1})"
            )

        self.save_project()
        self.render_transcript()
        self.statusBar().showMessage(f"Removed '{removed_name}' label at {format_time(segments[seg_idx].get('start', 0))}.")
        return True

    def register_confirmed_speaker_turn(self, seg_idx: int, speaker_name: str):
        """
        Active learning hook: When a user confirms or splits a speaker turn,
        extract its clean acoustic slice and add it to that speaker's reference bank.
        """
        if not speaker_name or not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript.get("segments", [])
        if not (0 <= seg_idx < len(segments)):
            return

        name = speaker_name.strip()
        emb = self.get_segment_embedding(seg_idx)
        if not emb:
            return

        if not hasattr(self, "_session_speaker_profiles"):
            self._session_speaker_profiles = {}

        if name not in self._session_speaker_profiles:
            self._session_speaker_profiles[name] = []

        # Maintain up to 6 confirmed reference vectors per speaker
        self._session_speaker_profiles[name].append(emb)
        if len(self._session_speaker_profiles[name]) > 6:
            self._session_speaker_profiles[name].pop(0)

        if hasattr(self, "log_activity"):
            self.log_activity(
                f"[VOICE MODEL] Updated acoustic signature for '{name}' "
                f"from confirmed turn #{seg_idx + 1} ({len(self._session_speaker_profiles[name])} sample(s)).",
                mark_dirty=False,
            )

    def register_confirmed_speaker_sample(self, seg_idx: int, speaker_name: str):
        """Alias for register_confirmed_speaker_turn."""
        self.register_confirmed_speaker_turn(seg_idx, speaker_name)

    def refine_speaker_run_between_confirmed_anchors(
        self, start_idx: int, end_idx: int, spk_a: str, spk_b: str
    ):
        """
        Competitive classifier: For all turns between start_idx and end_idx,
        assign to spk_a or spk_b based on relative cosine distance rather than a static threshold.
        """
        if not hasattr(self, "_session_speaker_profiles"):
            self._session_speaker_profiles = {}

        segments = self.transcript.get("segments", []) if self.transcript else []
        if not segments:
            return

        prof_a = self._session_speaker_profiles.get(spk_a)
        if not prof_a:
            prof_a = []
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == spk_a:
                    emb = self.get_segment_embedding(idx)
                    if emb:
                        prof_a.append(emb)
                        if len(prof_a) >= 4:
                            break
            if prof_a:
                self._session_speaker_profiles[spk_a] = prof_a

        prof_b = self._session_speaker_profiles.get(spk_b)
        if not prof_b:
            prof_b = []
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == spk_b:
                    emb = self.get_segment_embedding(idx)
                    if emb:
                        prof_b.append(emb)
                        if len(prof_b) >= 4:
                            break
            if prof_b:
                self._session_speaker_profiles[spk_b] = prof_b

        if not prof_a or not prof_b:
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(
                    f"Competitive refinement requires acoustic samples for both '{spk_a}' and '{spk_b}'.", 4000
                )
            return

        from speaker_identity import centroid, cosine_similarity
        cA = centroid(prof_a)
        cB = centroid(prof_b)
        if cA is None or cB is None:
            return

        reassigned = 0

        for idx in range(start_idx, min(end_idx + 1, len(segments))):
            emb = self.get_segment_embedding(idx)
            if not emb:
                continue

            simA = cosine_similarity(emb, cA)
            simB = cosine_similarity(emb, cB)

            winner = spk_a if simA >= simB else spk_b
            curr = self.get_effective_speaker_name(idx, segments[idx])

            if winner != curr:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = winner
                self.segment_speaker_overrides[idx] = override_key
                reassigned += 1

        if reassigned > 0:
            self._diar_index_key = None
            self.render_transcript()
            self.save_project()
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(
                    f"Refined {reassigned} turn(s) between '{spk_a}' and '{spk_b}'.", 4000
                )

    def prompt_refine_speaker_run(self, start_idx: int = -1, end_idx: int = -1):
        """Prompt user to competitively re-classify rapid dialog turns between two confirmed voices."""
        if not self.transcript or "segments" not in self.transcript:
            QMessageBox.information(self, "No Transcript", "Project has no transcript segments.")
            return

        segments = self.transcript.get("segments", [])
        if not segments:
            return

        known = self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []
        if len(known) < 2:
            QMessageBox.information(
                self,
                "Multiple Speakers Required",
                "Competitive re-classification requires at least two distinct speaker profiles in the project.",
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Refine Rapid Dialog Turns (Competitive Classifier)")
        dlg.resize(640, 480)
        dlg.setMinimumSize(580, 420)
        make_dialog_maximizable(dlg)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info = QLabel(
            "<b>Competitive Voice Separation & Cross-Talk Resolver</b><br>"
            "Classify every turn within the selected range by relative acoustic distance between "
            "two confirmed speaker signatures rather than a fixed global threshold. "
            "Ideal for rapid-fire dialog, interviews, and alternating banter."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        spk_a_combo = QComboBox(dlg)
        spk_a_combo.addItems(known)
        form.addRow("Speaker A (Confirmed):", spk_a_combo)

        spk_b_combo = QComboBox(dlg)
        spk_b_combo.addItems(known)
        if len(known) > 1:
            spk_b_combo.setCurrentIndex(1)
        form.addRow("Speaker B (Confirmed):", spk_b_combo)

        def _format_seg_label(idx, seg):
            st = float(seg.get("start", 0.0))
            t_str = format_time(st, include_millis=getattr(self, "show_milliseconds", False))
            spk = self.get_effective_speaker_name(idx, seg) or "Speaker"
            raw_text = seg.get("text", "").strip()
            snippet = (raw_text[:38] + "…") if len(raw_text) > 38 else (raw_text or "(no speech)")
            return f"[{t_str}] Turn #{idx + 1} ({spk}): “{snippet}”"

        start_combo = QComboBox(dlg)
        start_combo.setMaxVisibleItems(15)
        start_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        start_combo.setMinimumContentsLength(40)

        end_combo = QComboBox(dlg)
        end_combo.setMaxVisibleItems(15)
        end_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        end_combo.setMinimumContentsLength(40)

        for i, seg in enumerate(segments):
            label = _format_seg_label(i, seg)
            start_combo.addItem(label, i)
            end_combo.addItem(label, i)

        init_s = max(0, min(start_idx, len(segments) - 1)) if start_idx >= 0 else 0
        init_e = max(0, min(end_idx, len(segments) - 1)) if end_idx >= 0 else (len(segments) - 1)
        start_combo.setCurrentIndex(init_s)
        end_combo.setCurrentIndex(init_e)

        form.addRow("Start Turn (Timestamp & Words):", start_combo)
        form.addRow("End Turn (Timestamp & Words):", end_combo)

        layout.addLayout(form)

        # Interactive Range & Context Preview Card
        from PySide6.QtWidgets import QGroupBox, QDialogButtonBox
        preview_box = QGroupBox("Selected Dialog Range & Context Preview", dlg)
        preview_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
                background-color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(6)

        range_summary_lbl = QLabel(preview_box)
        range_summary_lbl.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 12px;")
        preview_layout.addWidget(range_summary_lbl)

        start_preview_lbl = QLabel(preview_box)
        start_preview_lbl.setWordWrap(True)
        start_preview_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        preview_layout.addWidget(start_preview_lbl)

        end_preview_lbl = QLabel(preview_box)
        end_preview_lbl.setWordWrap(True)
        end_preview_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        preview_layout.addWidget(end_preview_lbl)

        def _update_preview():
            s_idx = start_combo.currentData()
            e_idx = end_combo.currentData()
            if s_idx is None or e_idx is None:
                return
            lo, hi = min(s_idx, e_idx), max(s_idx, e_idx)
            count = hi - lo + 1
            s_seg = segments[lo]
            e_seg = segments[hi]
            st = float(s_seg.get("start", 0.0))
            en = float(e_seg.get("end", 0.0))
            dur = max(0.0, en - st)

            range_summary_lbl.setText(
                f"Range: Turns #{lo + 1} to #{hi + 1} ({count} turn{'s' if count != 1 else ''})  •  "
                f"Time: {format_time(st)} – {format_time(en)} ({dur:.2f}s)"
            )
            s_spk = self.get_effective_speaker_name(lo, s_seg) or "Speaker"
            s_txt = s_seg.get("text", "").strip() or "(no speech)"
            start_preview_lbl.setText(
                f"<b>Start Turn #{lo + 1}</b> [{format_time(st)}] <span style='color: #fbbf24;'>{html.escape(s_spk)}</span>: "
                f"<i>“{html.escape(s_txt)}”</i>"
            )
            e_spk = self.get_effective_speaker_name(hi, e_seg) or "Speaker"
            e_txt = e_seg.get("text", "").strip() or "(no speech)"
            end_preview_lbl.setText(
                f"<b>End Turn #{hi + 1}</b> [{format_time(en)}] <span style='color: #fbbf24;'>{html.escape(e_spk)}</span>: "
                f"<i>“{html.escape(e_txt)}”</i>"
            )

        start_combo.currentIndexChanged.connect(lambda _: _update_preview())
        end_combo.currentIndexChanged.connect(lambda _: _update_preview())
        _update_preview()

        layout.addWidget(preview_box)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            a_name = spk_a_combo.currentText().strip()
            b_name = spk_b_combo.currentText().strip()
            if a_name == b_name:
                QMessageBox.warning(self, "Invalid Selection", "Speaker A and Speaker B must be different speakers.")
                return
            s_val = start_combo.currentData()
            e_val = end_combo.currentData()
            s_i = int(s_val) if s_val is not None else 0
            e_i = int(e_val) if e_val is not None else (len(segments) - 1)
            if s_i > e_i:
                s_i, e_i = e_i, s_i
            self.refine_speaker_run_between_confirmed_anchors(s_i, e_i, a_name, b_name)
  
    def get_segment_embedding(self, seg_idx: int) -> Optional[List[float]]:
        """
        Retrieve a genuine 256-dimensional acoustic embedding for this segment.
        Extracts on-the-fly directly from any media container (.mp4, .mkv, .wav, etc.)
        using ffmpeg piped to memory.
        """
        if not self.transcript or "segments" not in self.transcript:
            return None

        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return None

        seg = segments[seg_idx]
        st = float(seg.get("start", 0.0))
        en = float(seg.get("end", st))
        dur = en - st

        if dur < 0.35:
            return None

        # 1. Use existing clean embedding if already present
        embedding = seg.get("embedding")
        if isinstance(embedding, (list, tuple)) and len(embedding) == 256:
            try:
                return [float(x) for x in embedding]
            except (TypeError, ValueError):
                pass

        # 2. Resolve media file path
        media_path = (
            getattr(self, "audio_file", None)
            or getattr(self, "media_file", None)
            or getattr(self, "current_media_path", None)
            or getattr(self, "audio_path", None)
        )
        if not media_path or not os.path.exists(str(media_path)):
            if hasattr(self, "project_metadata") and hasattr(self.project_metadata, "media_path"):
                media_path = self.project_metadata.media_path

        if not media_path or not os.path.exists(str(media_path)):
            return None

        # 3. Extract genuine acoustic slice embedding via ffmpeg PCM pipe
        try:
            import subprocess
            import numpy as np
            import wespeakerruntime as wespeaker_rt
            import torchaudio.compliance.kaldi as kaldi
            import torch
            from prs_shared import ffmpeg_path

            ff_exe = ffmpeg_path() or "ffmpeg"

            # Pipe exactly this time window decoded to 16kHz mono raw float32/int16
            cmd = [
                str(ff_exe),
                "-ss", f"{st:.3f}",
                "-t", f"{dur:.3f}",
                "-i", str(media_path),
                "-vn", "-sn", "-dn",
                "-ac", "1",
                "-ar", "16000",
                "-f", "s16le",
                "pipe:1"
            ]

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                creationflags=creationflags
            )

            raw_bytes = proc.stdout
            if len(raw_bytes) < int(0.25 * 16000 * 2):  # Require at least 250ms of audio
                return None

            data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Compute 80-bin filterbank features
            chunk_wave = torch.from_numpy(data).unsqueeze(0) * (1 << 15)
            mat = kaldi.fbank(
                chunk_wave,
                num_mel_bins=80,
                frame_length=25,
                frame_shift=10,
                dither=0.0,
                sample_frequency=16000,
                window_type="hamming",
                use_energy=False,
            ).numpy()
            mat = mat - np.mean(mat, axis=0)

            # Lazy-load WeSpeaker model on the main window instance
            if not hasattr(self, "_wespeaker_model") or self._wespeaker_model is None:
                self._wespeaker_model = wespeaker_rt.Speaker(lang="en")

            single_in = np.expand_dims(mat, 0).astype(np.float32)
            emb = self._wespeaker_model.session.run(
                output_names=["embs"], input_feed={"feats": single_in}
            )[0][0]

            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            vector = [round(float(x), 6) for x in emb.tolist()]
            seg["embedding"] = vector  # Cache vector so future checks are instantaneous
            return vector

        except Exception as exc:
            print(f"[DEBUG] Slice extraction failed for seg #{seg_idx + 1} ({st:.2f}s - {en:.2f}s): {exc}")
            return None

    def get_composite_embedding(self, seg_indices: List[int]) -> Optional[List[float]]:
        if not seg_indices:
            return None
        vectors = []
        for idx in seg_indices:
            embedding = self.get_segment_embedding(idx)
            if embedding is not None:
                vectors.append(embedding)
        if not vectors:
            return None
        return centroid(vectors)

    def _build_voice_profile_candidates(
        self,
        ref_indices: List[int],
        parent_widget: Optional[QWidget] = None,
    ) -> Tuple[List[Tuple[int, List[float]]], bool]:
        """
        Precompute candidate acoustic vectors across transcript segments.
        If more than 12 uncached segments require extraction, displays a cooperative
        QProgressDialog with a Cancel button. Returns (candidates, was_canceled).
        """
        if not self.transcript or "segments" not in self.transcript:
            return [], False

        segments = self.transcript.get("segments", [])
        ref_set = set(ref_indices)

        # Identify candidate segments needing evaluation and count those needing extraction
        eligible_indices = []
        uncached_count = 0
        for idx, segment in enumerate(segments):
            if idx in ref_set:
                continue
            st = float(segment.get("start", 0.0))
            en = float(segment.get("end", st))
            if (en - st) < 0.6:
                continue
            eligible_indices.append(idx)
            emb = segment.get("embedding")
            if not (isinstance(emb, (list, tuple)) and len(emb) == 256):
                uncached_count += 1

        candidates = []
        progress_dlg = None
        was_canceled = False

        # Only present progress dialog when substantial uncached extraction is needed and UI parent exists
        if uncached_count > 12 and parent_widget is not None:
            try:
                progress_dlg = QProgressDialog(
                    "Extracting acoustic voice signatures...",
                    "Cancel",
                    0,
                    len(eligible_indices),
                    parent_widget,
                )
                progress_dlg.setWindowTitle("Analyzing Voices")
                progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
                progress_dlg.setMinimumDuration(250)
                progress_dlg.setValue(0)
            except Exception:
                progress_dlg = None

        try:
            for step, idx in enumerate(eligible_indices):
                if progress_dlg is not None:
                    if progress_dlg.wasCanceled():
                        was_canceled = True
                        break
                    progress_dlg.setValue(step)
                    progress_dlg.setLabelText(
                        f"Extracting acoustic voice signatures (turn {step + 1} of {len(eligible_indices)})..."
                    )
                    QApplication.processEvents()

                embedding = self.get_segment_embedding(idx)
                if embedding is not None:
                    candidates.append((idx, embedding))

            if progress_dlg is not None:
                progress_dlg.setValue(len(eligible_indices))
        finally:
            if progress_dlg is not None:
                progress_dlg.close()

        return candidates, was_canceled

    def find_matching_voice_turns(
        self,
        ref_seg_idx: int,
        threshold: float = 0.78,
        scope_cluster_only: bool = False,
        ref_seg_indices: Optional[List[int]] = None,
        target_name: Optional[str] = None,
        cached_candidates: Optional[List[Tuple[int, List[float]]]] = None,
    ) -> List[dict]:
        """Find transcript turns acoustically matching a verified voice."""
        if not self.transcript or "segments" not in self.transcript:
            return []

        segments = self.transcript.get("segments", [])
        if ref_seg_idx < 0 or ref_seg_idx >= len(segments):
            return []

        if ref_seg_indices:
            reference_indices = [int(i) for i in ref_seg_indices if 0 <= int(i) < len(segments)]
        else:
            reference_indices = [ref_seg_idx]

        if ref_seg_idx not in reference_indices:
            reference_indices.insert(0, ref_seg_idx)

        reference_vectors = []
        for idx in reference_indices:
            embedding = self.get_segment_embedding(idx)
            if embedding is not None:
                reference_vectors.append(embedding)

        # Include any confirmed reference samples accumulated this session for this speaker
        reference_name = self.get_effective_speaker_name(ref_seg_idx, segments[ref_seg_idx])
        session_vectors = []
        if hasattr(self, "_session_speaker_profiles"):
            session_vectors = list(self._session_speaker_profiles.get(reference_name, []))
            if target_name and target_name != reference_name:
                session_vectors.extend(self._session_speaker_profiles.get(target_name, []))

        all_candidate_refs = reference_vectors + session_vectors
        if not all_candidate_refs:
            return []

        # Target profile is constructed via robust reference profile synthesis
        seed_vectors = reference_vectors[:1] if reference_vectors else all_candidate_refs[:1]
        secondary_refs = all_candidate_refs[1:]
        if secondary_refs:
            target_profile, _ = robust_reference_profile(
                seed_vectors, secondary_refs, seed_similarity=0.78
            )
            if target_profile is None:
                target_profile = centroid(all_candidate_refs)
        else:
            target_profile = seed_vectors[0]

        if target_profile is None:
            return []

        ref_set = set(reference_indices)
        if cached_candidates is not None:
            candidates = [(i, v) for i, v in cached_candidates if i not in ref_set]
        else:
            raw_c = self._build_voice_profile_candidates(reference_indices)
            candidates = raw_c[0] if isinstance(raw_c, tuple) else raw_c

        # Form competitor profiles from turns assigned to OTHER names
        competing_groups = {}
        same_cluster_embeddings = []
        excluded_names = {reference_name}
        if target_name:
            excluded_names.add(target_name)

        for idx, embedding in candidates:
            speaker = self.get_effective_speaker_name(idx, segments[idx])
            if speaker not in excluded_names:
                competing_groups.setdefault(speaker, []).append((idx, embedding))
            elif speaker == reference_name:
                same_cluster_embeddings.append((idx, embedding))

        # In-group sub-clustering: if a single cluster contains an imposter voice,
        # discover outliers in the same cluster that diverge from target_profile
        # and treat them as an internal competitor.
        internal_competitor = None
        divergent_indices = set()
        if same_cluster_embeddings:
            divergent_items = [
                (i, v) for i, v in same_cluster_embeddings
                if cosine_similarity(v, target_profile) < 0.72
            ]
            if len(divergent_items) >= 2:
                internal_competitor = centroid([v for _, v in divergent_items[:10]])
                divergent_indices = {i for i, _ in divergent_items}

        # Precompute base competitor centroids once outside candidate loop so the matching loop
        # avoids recalculating centroids for identical competitor speaker turns
        base_competitor_centroids = {}
        for spk_name, items in competing_groups.items():
            if items:
                top_items = items[:12]
                c_prof = centroid([v for _, v in top_items])
                if c_prof is not None:
                    base_competitor_centroids[spk_name] = (c_prof, {i for i, _ in top_items})

        matches = []

        for idx, embedding in candidates:
            if scope_cluster_only:
                speaker = self.get_effective_speaker_name(idx, segments[idx])
                if speaker != reference_name:
                    continue

            # Build competitor profiles for THIS candidate turn (using precomputed base centroids)
            item_competitor_profiles = []
            for spk_name, (c_prof, top_ids) in base_competitor_centroids.items():
                if idx not in top_ids:
                    item_competitor_profiles.append(c_prof)
                else:
                    # Candidate's own embedding was part of this speaker's top-12; recalculate excluding it
                    items = competing_groups[spk_name]
                    other_vecs = [v for (i, v) in items if i != idx]
                    if other_vecs:
                        c_ex = centroid(other_vecs[:12])
                        if c_ex is not None:
                            item_competitor_profiles.append(c_ex)

            if internal_competitor is not None and idx not in divergent_indices:
                item_competitor_profiles.append(internal_competitor)

            has_competitors = len(item_competitor_profiles) > 0

            comparison = compare_against_profiles(
                embedding,
                target_profile,
                item_competitor_profiles,
            )

            if not is_confident_match(
                comparison,
                threshold=threshold,
                margin=0.035,
                has_competitors=has_competitors,
            ):
                continue

            segment = segments[idx]
            matches.append({
                "seg_idx": idx,
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "speaker": self.get_effective_speaker_name(idx, segment),
                "similarity": round(comparison.target_similarity, 4),
                "margin": round(comparison.margin, 4),
                "competitor_similarity": round(comparison.competitor_similarity, 4),
                "text": segment.get("text", "").strip(),
            })

        matches.sort(
            key=lambda item: (item["similarity"], item["margin"]),
            reverse=True,
        )
        return matches

    def match_acoustic_voice_profile(
        self,
        ref_seg_idx: int,
        target_speaker: str,
        threshold: float = 0.78,
        scope_cluster_only: bool = False,
        selected_indices: Optional[List[int]] = None,
        ref_seg_indices: Optional[List[int]] = None,
    ) -> int:
        if not self.transcript or "segments" not in self.transcript or not target_speaker:
            return 0

        segments = self.transcript.get("segments", [])
        if ref_seg_idx < 0 or ref_seg_idx >= len(segments):
            return 0

        target_name = target_speaker.strip()
        if not target_name:
            return 0

        if selected_indices is None:
            matches = self.find_matching_voice_turns(
                ref_seg_idx,
                threshold=threshold,
                scope_cluster_only=scope_cluster_only,
                ref_seg_indices=ref_seg_indices,
                target_name=target_name,
            )
            selected_indices = [match["seg_idx"] for match in matches]

        all_to_reassign = set(selected_indices or [])
        if ref_seg_indices:
            all_to_reassign.update(int(idx) for idx in ref_seg_indices if 0 <= int(idx) < len(segments))
        else:
            all_to_reassign.add(ref_seg_idx)

        if not all_to_reassign:
            return 0

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()

        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        for idx in sorted(all_to_reassign):
            instance_key = f"SEG_{idx}_SPEAKER"
            self.speaker_names[instance_key] = target_name
            self.segment_speaker_overrides[idx] = instance_key

        if isinstance(getattr(self, "diarization", None), dict):
            diar_segments = self.diarization.get("segments", [])
            for idx in sorted(all_to_reassign):
                if idx >= len(segments):
                    continue
                transcript_segment = segments[idx]
                t_start = float(transcript_segment.get("start", 0.0))
                t_end = float(transcript_segment.get("end", t_start))

                for diar_segment in diar_segments:
                    d_start = float(diar_segment.get("start", 0.0))
                    d_end = float(diar_segment.get("end", d_start))
                    overlap = min(t_end, d_end) - max(t_start, d_start)
                    if overlap > 0.01:
                        diar_segment["speaker"] = f"SEG_{idx}_SPEAKER"

            self._diar_index_key = None

        if hasattr(self, "add_custom_speaker_to_glossary"):
            self.add_custom_speaker_to_glossary(target_name)

        # Register confirmed speaker samples into session voice profiles
        if hasattr(self, "register_confirmed_speaker_sample"):
            for idx in sorted(all_to_reassign):
                self.register_confirmed_speaker_sample(idx, target_name)

        count = len(all_to_reassign)
        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Acoustic Voice Identification: {count} turn(s) → '{target_name}'",
            )

        self.log_activity(
            f"[SPEAKER] Voice Identification: {count} confirmed turn(s) assigned to '{target_name}'."
        )
        self.save_project()
        self.render_transcript()
        self.statusBar().showMessage(
            f"Voice identification complete: {count} turn(s) assigned to '{target_name}'."
        )
        return count

    def teach_voice_profile_dialog(
        self,
        seg_idx: int = -1,
        raw_speaker: str = None,
        prompt_new_speaker: bool = False,
    ):
        if not self.transcript or "segments" not in self.transcript:
            QMessageBox.information(
                self,
                "No Transcript Loaded",
                "Please open or transcribe a project before using the Acoustic Voice Profile Matcher.",
            )
            return

        segments = self.transcript.get("segments", [])
        if not segments:
            QMessageBox.information(
                self,
                "Empty Transcript",
                "Project has no speech segments to match voice profiles against.",
            )
            return

        if seg_idx < 0 or seg_idx >= len(segments):
            # Attempt to infer active segment from transcript cursor or audio playback position
            inferred = -1
            if hasattr(self, "transcript_view"):
                cursor = self.transcript_view.textCursor()
                inferred = self.transcript_view.get_segment_index_at_cursor(cursor)
                if inferred is None or inferred < 0:
                    inferred = cursor.blockNumber()
            if (inferred is None or inferred < 0 or inferred >= len(segments)) and hasattr(self, "player"):
                curr_t = (self.player.position() / 1000.0) if hasattr(self.player, "position") else 0.0
                for i, s in enumerate(segments):
                    if s.get("start", 0.0) <= curr_t <= s.get("end", 0.0):
                        inferred = i
                        break
            seg_idx = inferred if (inferred is not None and 0 <= inferred < len(segments)) else 0

        current_speaker = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        dlg = VoiceProfileMatchDialog(
            ref_seg_idx=seg_idx,
            current_speaker=current_speaker,
            target_speaker="" if prompt_new_speaker else current_speaker,
            prompt_new_speaker=prompt_new_speaker,
            parent=self,
        )

        if dlg.exec() == QDialog.DialogCode.Accepted:
            active_refs = dlg.get_active_ref_indices()
            self.match_acoustic_voice_profile(
                ref_seg_idx=seg_idx,
                target_speaker=dlg.target_name,
                threshold=dlg.thresh_slider.value() / 100.0,
                scope_cluster_only=dlg.scope_cluster_radio.isChecked(),
                selected_indices=dlg.selected_indices,
                ref_seg_indices=active_refs,
            )

    def sync_segment_words(self, segment, new_text, word_formats=None):
        if not isinstance(segment, dict):
            return

        old_words = segment.get("words")
        new_tokens = [tok.strip() for tok in new_text.split()] if isinstance(new_text, str) else []
        seg_start = float(segment.get("start", 0.0))
        seg_end = float(segment.get("end", seg_start + 1.0))
        total_dur = max(0.01, seg_end - seg_start)

        if not old_words or not isinstance(old_words, list):
            if not new_tokens:
                segment["words"] = []
                return

            w_dur = total_dur / len(new_tokens)
            new_words = [
                {
                    "word": tok,
                    "start": round(seg_start + i * w_dur, 3),
                    "end": round(seg_start + (i + 1) * w_dur, 3),
                    "deleted": False,
                }
                for i, tok in enumerate(new_tokens)
            ]

            if word_formats:
                for idx, w_dict in enumerate(new_words):
                    if 0 <= idx < len(word_formats):
                        fmt = word_formats[idx]
                        if fmt.get("bold"): w_dict["bold"] = True
                        if fmt.get("italic"): w_dict["italic"] = True
                        if fmt.get("underline"): w_dict["underline"] = True
                        if fmt.get("strike"): w_dict["strike"] = True
                        if fmt.get("highlight"): w_dict["highlight"] = fmt["highlight"]

            segment["words"] = new_words
            return

        if not new_tokens:
            segment["words"] = []
            return

        import difflib
        old_toks = [str(w.get("word", "")).strip() for w in old_words]
        matcher = difflib.SequenceMatcher(None, [t.lower() for t in old_toks], [t.lower() for t in new_tokens])
        new_words_list = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for old_idx, new_idx in zip(range(i1, i2), range(j1, j2)):
                    w_obj = dict(old_words[old_idx])
                    w_obj["word"] = new_tokens[new_idx]
                    new_words_list.append(w_obj)
            elif tag == "replace":
                t_start = float(old_words[i1].get("start", seg_start))
                t_end = float(old_words[i2 - 1].get("end", seg_end))
                t_span = max(0.01, t_end - t_start)
                num_new = max(1, j2 - j1)
                w_dur = t_span / num_new
                for k, new_idx in enumerate(range(j1, j2)):
                    new_words_list.append({
                        "word": new_tokens[new_idx],
                        "start": round(t_start + k * w_dur, 3),
                        "end": round(t_start + (k + 1) * w_dur, 3),
                        "deleted": False,
                    })
            elif tag == "insert":
                t_start = float(old_words[i1 - 1].get("end", seg_start)) if (0 < i1 <= len(old_words)) else seg_start
                t_end = float(old_words[i1].get("start", seg_end)) if i1 < len(old_words) else seg_end
                if t_end < t_start:
                    t_end = t_start + 0.2 * (j2 - j1)
                t_span = max(0.01, t_end - t_start)
                num_new = max(1, j2 - j1)
                w_dur = t_span / num_new
                for k, new_idx in enumerate(range(j1, j2)):
                    new_words_list.append({
                        "word": new_tokens[new_idx],
                        "start": round(t_start + k * w_dur, 3),
                        "end": round(t_start + (k + 1) * w_dur, 3),
                        "deleted": False,
                    })

        if word_formats:
            for idx, w_dict in enumerate(new_words_list):
                if 0 <= idx < len(word_formats):
                    fmt = word_formats[idx]
                    if fmt.get("bold"): w_dict["bold"] = True
                    if fmt.get("italic"): w_dict["italic"] = True
                    if fmt.get("underline"): w_dict["underline"] = True
                    if fmt.get("strike"): w_dict["strike"] = True
                    if fmt.get("highlight"): w_dict["highlight"] = fmt["highlight"]

        segment["words"] = new_words_list

    def merge_speakers(self, source_speaker: str, target_speaker: str) -> bool:
        source = (source_speaker or "").strip()
        target = (target_speaker or "").strip()
        if not source or not target or source == target:
            return False
        if not self.transcript or not self.transcript.get("segments"):
            return False

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()

        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        segments = self.transcript.get("segments", [])
        reassigned_segments = 0

        for idx, seg in enumerate(segments):
            curr_name = self.get_effective_speaker_name(idx, seg)
            raw_spk = self.segment_speaker_overrides.get(idx) or seg.get("speaker")
            if curr_name == source or str(raw_spk) == source:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target
                self.segment_speaker_overrides[idx] = override_key
                seg["speaker"] = target
                reassigned_segments += 1

        diar_data = getattr(self, "diarization", None)
        if isinstance(diar_data, dict) and "segments" in diar_data:
            for d_seg in diar_data["segments"]:
                raw_d = str(d_seg.get("speaker", ""))
                disp_d = self.display_speaker(raw_d)
                if disp_d == source or raw_d == source:
                    d_seg["speaker"] = target

            unique_speakers = {s.get("speaker") for s in diar_data["segments"] if s.get("speaker")}
            diar_data["num_speakers"] = len(unique_speakers)
            self._diar_index_key = None

        self.speaker_names[source] = target
        if hasattr(self, "custom_speakers"):
            if source in self.custom_speakers:
                self.custom_speakers.remove(source)
            if target not in self.custom_speakers:
                self.custom_speakers.append(target)

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, f"Merge Speaker '{source}' into '{target}'")

        self.save_project()
        self.render_transcript()
        if hasattr(self, "timeline"):
            self.timeline.update()
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Merged '{source}' into '{target}'.")
        return True

    def open_speaker_manager_dialog(self):
        dialog = SpeakerManagerDialog(self)
        dialog.exec()

    def merge_contiguous_speaker_segments(self):
        if not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript["segments"]
        if not segments:
            return

        merged_segments = []
        new_overrides = {}
        curr_block = None
        curr_effective_name = None

        for idx, seg in enumerate(segments):
            effective_name = self.get_effective_speaker_name(idx, seg)
            if curr_block is None:
                curr_block = dict(seg)
                curr_block["words"] = list(seg.get("words", []))
                curr_effective_name = effective_name
            else:
                if effective_name == curr_effective_name:
                    curr_block["end"] = seg["end"]
                    curr_block["text"] = (curr_block["text"].strip() + " " + seg.get("text", "").strip()).strip()
                    curr_block["words"].extend(seg.get("words", []))
                else:
                    merged_idx = len(merged_segments)
                    merged_segments.append(curr_block)
                    if idx - 1 in self.segment_speaker_overrides:
                        new_overrides[merged_idx] = self.segment_speaker_overrides[idx - 1]
                    curr_block = dict(seg)
                    curr_block["words"] = list(seg.get("words", []))
                    curr_effective_name = effective_name

        if curr_block:
            merged_idx = len(merged_segments)
            merged_segments.append(curr_block)
            if len(segments) - 1 in self.segment_speaker_overrides:
                new_overrides[merged_idx] = self.segment_speaker_overrides[len(segments) - 1]

        self.transcript["segments"] = merged_segments
        self.segment_speaker_overrides = new_overrides

    def refresh_story_list(self):
        selected_indices = list(self.current_selected_story_indices)
        self.story_list.blockSignals(True)
        self.story_list.clear()

        curve_labels = {
            "linear": "Linear",
            "s_curve": "S-Curve",
            "logarithmic": "Logarithmic",
            "exponential": "Exponential",
        }

        for index, story in enumerate(self.stories, start=1):
            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)
            fcurve = getattr(story, "fade_curve", "linear") or "linear"

            fade_parts = []
            if fin > 0: fade_parts.append(f"In:{fin:.1f}s")
            if fout > 0: fade_parts.append(f"Out:{fout:.1f}s")
            fade_badge = f"  [{' '.join(fade_parts)}]" if fade_parts else ""

            text = f"{index}. {format_time(story.start)} – {format_time(story.end)}  {story.title}{fade_badge}"
            item = QListWidgetItem(text)
            curve_name = curve_labels.get(fcurve, fcurve.capitalize())
            fade_info = f"Fade-In: {fin:.2f}s | Fade-Out: {fout:.2f}s ({curve_name} Curve)" if (fin > 0 or fout > 0) else "No Fades Applied"

            item.setToolTip(f"Story #{index}: {story.title}\nTime Range: {format_time(story.start)} – {format_time(story.end)}\n{fade_info}")
            item.setData(Qt.ItemDataRole.UserRole, story.to_dict())
            self.story_list.addItem(item)

        for idx in selected_indices:
            if 0 <= idx < self.story_list.count():
                self.story_list.item(idx).setSelected(True)

        self.story_list.blockSignals(False)
        self.timeline.set_stories(self.stories, selected_indices)
        if hasattr(self, "update_story_list_height"):
            self.update_story_list_height()
        if hasattr(self, "notify_story_selection_to_plugins"):
            st = self.stories[selected_indices[0]] if (len(selected_indices) == 1 and 0 <= selected_indices[0] < len(self.stories)) else None
            self.notify_story_selection_to_plugins(st)

    def handle_new_story_started(self, start_time, end_time):
        self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]
        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        default_title = "Untitled Song" if is_music else "Untitled Story"
        story = Story(start=start_time, end=end_time, title=default_title)
        self.stories.append(story)
        self.refresh_story_list()
        self.story_selection_changed()
        self.start_input.setText(format_time(story.start))
        self.end_input.setText(format_time(story.end))
        self.title_input.setText(story.title)

    def handle_new_story_updated(self, start_time, end_time):
        if self.stories:
            story = self.stories[-1]
            story.start = start_time
            story.end = end_time
            self.start_input.setText(format_time(story.start))
            self.end_input.setText(format_time(story.end))
            if hasattr(self, "story_list") and self.story_list.count() > 0:
                last_idx = self.story_list.count() - 1
                item = self.story_list.item(last_idx)
                if item:
                    item.setText(f"{len(self.stories)}. {format_time(story.start)} – {format_time(story.end)}  {story.title}")
                    item.setData(Qt.ItemDataRole.UserRole, story.to_dict())

    def handle_drag_story_region(self, index, start_time, end_time):
        if not self.pre_drag_stories_snapshot:
            self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]

        if 0 <= index < len(self.stories):
            story = self.stories[index]
            story.start = start_time
            story.end = end_time
            if self.current_selected_story_indices != [index]:
                self.apply_story_selection_indices([index], seek=False)
            else:
                self.start_input.setText(format_time(story.start))
                self.end_input.setText(format_time(story.end))

    def audition_story(self, index: int):
        if not (0 <= index < len(self.stories)):
            return

        story = self.stories[index]
        self._audition_story_index = index
        self.apply_story_selection_indices([index], seek=False)
        self.seek_to(story.start)

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            fin = getattr(story, "fade_in", 0.0)
            if fin > 0 and hasattr(self, "audio_output"):
                self.audio_output.setVolume(0.0)
                self._last_applied_fade_vol = 0.0

        self.player.play()

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            if hasattr(self, "fade_preview_timer"):
                self.fade_preview_timer.start(35)
            self.update_realtime_fade_volume()

        self.timeline.set_playing_state(True)
        self.play_button.setText("❚❚ Pause")

    def handle_drag_finished(self):
        if self.pre_drag_stories_snapshot:
            old_stories = self.pre_drag_stories_snapshot
            self.pre_drag_stories_snapshot = []
            changed_idx = None

            for i in range(min(len(old_stories), len(self.stories))):
                if (abs(old_stories[i].start - self.stories[i].start) > 0.001 or abs(old_stories[i].end - self.stories[i].end) > 0.001):
                    changed_idx = i
                    break

            if changed_idx is not None and hasattr(self, "undo_stack"):
                old_start = old_stories[changed_idx].start
                old_end = old_stories[changed_idx].end
                new_start = self.stories[changed_idx].start
                new_end = self.stories[changed_idx].end
                desc = f"Adjust Story #{changed_idx + 1} Boundary"

                self.stories[changed_idx].start = old_start
                self.stories[changed_idx].end = old_end

                cmd = StoryBoundaryChangeCommand(
                    self, changed_idx, old_start, old_end, new_start, new_end, desc
                )
                self.undo_stack.push(cmd)
            else:
                new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
                self.commit_story_change(old_stories, new_stories, "Adjust Story Selection")
                self.refresh_story_list()
                self.save_project()

    def update_selected_story(self):
        selected_rows = list(self.current_selected_story_indices)
        if not selected_rows:
            return

        try:
            start = parse_time(self.start_input.text())
            end = parse_time(self.end_input.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Time", str(exc))
            return

        if end <= start:
            QMessageBox.warning(self, "Invalid Story", "End time must be after start time.")
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        new_stories[index].start = start
        new_stories[index].end = end
        new_stories[index].title = self.title_input.text().strip() or "Untitled Story"

        author_val = self.author_input.text().strip() if hasattr(self, "author_input") else ""
        excerpt_val = self.excerpt_edit.toPlainText().strip() if hasattr(self, "excerpt_edit") else ""

        if not hasattr(new_stories[index], "metadata") or new_stories[index].metadata is None:
            new_stories[index].metadata = {}

        old_author = old_stories[index].metadata.get("author", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""
        old_excerpt = old_stories[index].metadata.get("excerpt", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""

        new_stories[index].metadata["author"] = author_val
        new_stories[index].metadata["excerpt"] = excerpt_val

        start_changed = abs(new_stories[index].start - old_stories[index].start) >= 0.001
        end_changed = abs(new_stories[index].end - old_stories[index].end) >= 0.001
        title_changed = new_stories[index].title != old_stories[index].title
        author_changed = author_val != old_author
        excerpt_changed = excerpt_val != old_excerpt

        if not (start_changed or end_changed or title_changed or author_changed or excerpt_changed):
            return

        if (start_changed or end_changed) and not title_changed and not author_changed and not excerpt_changed and hasattr(self, "undo_stack"):
            desc = f"Adjust Story #{index + 1} Boundary"
            cmd = StoryBoundaryChangeCommand(
                self, index, old_stories[index].start, old_stories[index].end, new_stories[index].start, new_stories[index].end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
            return

        self.commit_story_change(old_stories, new_stories, "Update Story Details")
        self.apply_story_selection_indices([index], seek=False)

    def delete_selected_story(self):
        selected_rows = sorted(list(self.current_selected_story_indices), reverse=True)
        if not selected_rows:
            return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for idx in selected_rows:
            del new_stories[idx]

        count = len(selected_rows)
        self.apply_story_selection_indices([], seek=False)

        if hasattr(self, "timeline") and hasattr(self.timeline, "canvas"):
            self.timeline.canvas.selection_start = None
            self.timeline.canvas.selection_end = None
            self.timeline.canvas.selectionRangeChanged.emit(None, None)
            self.timeline.canvas.update()

        desc = f"Delete {term if count == 1 else term_plural}"
        self.commit_story_change(old_stories, new_stories, desc)

    def get_current_interaction_time(self, for_boundary="start"):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            return s if for_boundary == "start" else e

        if hasattr(self, "transcript_view"):
            if self.transcript_view.has_active_selection():
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range:
                    return sel_range[0] if for_boundary == "start" else sel_range[1]

            if getattr(self, "last_position_source", None) == "transcript":
                last_ts = getattr(self, "last_transcript_cursor_time", None)
                if last_ts is not None and last_ts >= 0:
                    return last_ts

        return getattr(self, "current_position", 0.0)

    def set_selected_story_start(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="start")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time >= current_story.end:
            QMessageBox.warning(
                self, "Invalid Boundary", f"Start time ({format_time(target_time)}) must be earlier than story end time ({format_time(current_story.end)})."
            )
            return

        if abs(target_time - current_story.start) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} Start Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, target_time, current_story.end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=True)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].start = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=True)
            self.mark_project_dirty(desc)
            self.save_project()

    def set_selected_story_end(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="end")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time <= current_story.start:
            QMessageBox.warning(
                self, "Invalid Boundary", f"End time ({format_time(target_time)}) must be later than story start time ({format_time(current_story.start)})."
            )
            return

        if abs(target_time - current_story.end) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} End Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, current_story.start, target_time, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].end = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=False)
            self.mark_project_dirty(desc)
            self.save_project()

    def add_selection_to_story(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges:
            cursor = self.transcript_view.textCursor()
            if not cursor.hasSelection():
                QMessageBox.information(
                    self, "No Selection", "Highlight a portion of the transcript first to create a story from it."
                )
                return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        if len(ranges) > 1:
            old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
            created_stories = []

            for r in ranges:
                s_time = r.get("start_time", 0.0)
                e_time = r.get("end_time", s_time + 1.0)
                if e_time <= s_time:
                    e_time = s_time + 1.0
                text = r.get("text", "").strip()
                words = text.split()
                t = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"
                created_stories.append(Story(start=s_time, end=e_time, title=t))

            new_stories = sorted(old_stories + created_stories, key=lambda s: s.start)
            if hasattr(self, "commit_story_change"):
                self.commit_story_change(old_stories, new_stories, f"Add {len(created_stories)} {term_plural} from Multi-Selection")
            else:
                self.stories = new_stories
                self.refresh_story_list()

            new_indices = [new_stories.index(s) for s in created_stories]
            if hasattr(self, "apply_story_selection_indices"):
                self.apply_story_selection_indices(new_indices)

            self.transcript_view.clear_all_selections()
            self.statusBar().showMessage(f"Created {len(created_stories)} {term_plural.lower()} from multiple selections.")
            return

        start_time = None
        end_time = None
        selected_text = ""

        if ranges:
            start_time = ranges[0].get("start_time")
            end_time = ranges[0].get("end_time")
            selected_text = ranges[0].get("text", "")
        else:
            cursor = self.transcript_view.textCursor()
            selected_text = cursor.selectedText().strip()
            if hasattr(self.transcript_view, "get_selected_time_range"):
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range and sel_range[0] is not None and sel_range[1] is not None:
                    start_time, end_time = sel_range

        if start_time is None or end_time is None:
            cursor = self.transcript_view.textCursor()
            start_char = cursor.selectionStart()
            end_char = cursor.selectionEnd()
            char_map = getattr(self.transcript_view, "char_timestamp_map", [])

            for entry in char_map:
                c_start, c_end, w_start, w_end = entry[0], entry[1], entry[2], entry[3]
                if c_start <= start_char <= c_end and start_time is None:
                    start_time = w_start
                if c_start <= end_char <= c_end:
                    end_time = w_end

        if start_time is None:
            start_time = getattr(self, "current_position", 0.0)
        if end_time is None:
            end_time = min(getattr(self, "duration", start_time + 5.0), start_time + 5.0)

        if end_time <= start_time:
            end_time = start_time + 1.0

        words = selected_text.split()
        default_title = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(start_time))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(end_time))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=start_time, end=end_time, title=default_title)
        old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda s: s.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add {term} from Selection: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.transcript_view.clear_all_selections()
        self.statusBar().showMessage(f"Created {term.lower()}: {default_title}")

    def play_transcript_selection(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges and hasattr(self.transcript_view, "get_selected_time_range"):
            tr = self.transcript_view.get_selected_time_range()
            if tr and tr[0] is not None:
                ranges = [{"start_time": tr[0], "end_time": tr[1]}]

        if ranges:
            start_t = ranges[0].get("start_time", 0.0)
            self.seek_to(start_t)
            if hasattr(self, "player") and hasattr(self, "toggle_play"):
                from PySide6.QtMultimedia import QMediaPlayer
                if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self.toggle_play()

    def select_all_stories(self):
        if not getattr(self, "stories", []):
            return
        all_indices = list(range(len(self.stories)))
        self.apply_story_selection_indices(all_indices)
        if hasattr(self, "timeline"):
            self.timeline.set_stories(self.stories, all_indices)
        self.statusBar().showMessage(f"Selected all {len(self.stories)} stories.")

    def handle_timeline_selection_range_changed(self, start_time, end_time):
        if not hasattr(self, "transcript_view"):
            return

        if start_time is None or end_time is None:
            cursor = self.transcript_view.textCursor()
            if cursor.hasSelection():
                cursor.clearSelection()
                self.transcript_view.setTextCursor(cursor)
            return

        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        char_map = getattr(self.transcript_view, "char_timestamp_map", [])
        if not char_map:
            return

        first_char = None
        last_char = None

        for item in char_map:
            c_start = item[0]
            c_end = item[1]
            w_start = item[2]
            w_end = item[3] if len(item) >= 4 else w_start

            if w_end >= s and first_char is None:
                first_char = c_start
            if w_start <= e:
                last_char = c_end

        if first_char is not None and last_char is not None and last_char > first_char:
            cursor = self.transcript_view.textCursor()
            cursor.setPosition(first_char)
            cursor.setPosition(last_char, QTextCursor.MoveMode.KeepAnchor)
            self.transcript_view.setTextCursor(cursor)
            self.transcript_view.ensureCursorVisible()

    def add_story_from_range(self, start_time, end_time):
        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        if e <= s:
            e = s + 1.0

        default_title = "New Story"
        if hasattr(self, "transcript_for_range"):
            segs = self.transcript_for_range(s, e)
            words = " ".join(seg.get("text", "").strip() for seg in segs).split()
            if words:
                default_title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(s))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(e))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=s, end=e, title=default_title)
        old_stories = [Story.from_dict(item.to_dict()) for item in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda item: item.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add Story: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.statusBar().showMessage(f"Created story: {default_title}")

    def add_story_from_active_selection(self):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()
            self.add_story_from_range(s, e)
            return

        if hasattr(self, "transcript_view") and self.transcript_view.has_active_selection():
            self.add_selection_to_story()
            return

        QMessageBox.information(
            self, "No Selection", "Make a selection first by right-click dragging across the timeline or highlighting transcript text."
        )

    def open_story_fades_dialog(self, story_index=None):
        if not hasattr(self, "stories") or not self.stories:
            QMessageBox.information(self, "No Stories", "There are no stories created yet.")
            return

        if story_index is None:
            if hasattr(self, "current_selected_story_indices") and self.current_selected_story_indices:
                story_index = self.current_selected_story_indices[0]
            else:
                story_index = 0

        if not (0 <= story_index < len(self.stories)):
            return

        story = self.stories[story_index]
        dlg = StoryFadesDialog(self, story=story, story_index=story_index)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_in, new_out, new_curve, apply_all = dlg.get_fades()
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

            if apply_all:
                for s in new_stories:
                    s.fade_in = new_in
                    s.fade_out = new_out
                    s.fade_curve = new_curve
                desc = "Set Audio Fades on All Stories"
            else:
                new_stories[story_index].fade_in = new_in
                new_stories[story_index].fade_out = new_out
                new_stories[story_index].fade_curve = new_curve
                desc = f"Set Audio Fades on Story #{story_index + 1}"

            if hasattr(self, "undo_stack"):
                self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, desc))
            else:
                self.stories = new_stories
                self.refresh_story_list()
                if hasattr(self, "timeline"):
                    self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                    self.timeline.update()
                self.save_project()

    def apply_fades_to_selected_stories(self, fade_in=None, fade_out=None, fade_curve=None):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        if fade_in is None:
            fade_in = float(settings.value("default_fade_in_duration", 0.0))
        if fade_out is None:
            fade_out = float(settings.value("default_fade_out_duration", 1.0))
        if fade_curve is None:
            fade_curve = str(settings.value("default_fade_curve", "linear") or "linear")

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_in = fade_in
                new_stories[i].fade_out = fade_out
                new_stories[i].fade_curve = fade_curve

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, "Apply Audio Fades to Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def remove_fades_from_selected_stories(self):
        self.apply_fades_to_selected_stories(fade_in=0.0, fade_out=0.0)

    def set_fade_curve_for_selected_stories(self, curve_type: str):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_curve = curve_type

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, f"Set Fade Curve ({curve_type}) on Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def open_story_metadata_dialog(self, target_story_index: Optional[int] = None):
        from story_metadata_dialog import StoryMetadataDialog
        if target_story_index is None and getattr(self, "current_selected_story_indices", None):
            target_story_index = self.current_selected_story_indices[0]

        dlg = StoryMetadataDialog(self, main_window=self, target_story_index=target_story_index)
        dlg.exec()



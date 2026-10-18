"""Radio & TV Segmenter v3.9.16-beta — transcript story responsibilities.

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
from PySide6.QtCore import Qt, QTimer, QSettings, QObject
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
from story_model import (
    Story,
    SetStoriesCommand,
    SelectStoriesCommand,
    StoryBoundaryChangeCommand,
    FADE_CURVE_TABLES,
    get_fade_curve_factors,
)
from story_crud_mixin import StoryCrudMixin
from speaker_editing_mixin import SpeakerEditingMixin
from voice_profile_ops_mixin import VoiceProfileOpsMixin

__all__ = [
    "TranscriptStoryMixin",
    "Story",
    "SetStoriesCommand",
    "SelectStoriesCommand",
    "StoryBoundaryChangeCommand",
    "StoryCrudMixin",
    "SpeakerEditingMixin",
    "VoiceProfileOpsMixin",
    "ChangeSpeakerDialog",
    "VoiceProfileMatchDialog",
    "StoryFadesDialog",
    "SpeakerManagerDialog",
    "FADE_CURVE_TABLES",
    "get_fade_curve_factors",
]

class TranscriptStoryMixin(StoryCrudMixin, SpeakerEditingMixin, VoiceProfileOpsMixin):
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
        self._block_text_cache = {
            i: (doc.findBlockByNumber(i).text(), doc.findBlockByNumber(i).revision())
            for i in range(doc.blockCount())
        }

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

        cache = getattr(self, "_block_text_cache", None)
        if not isinstance(cache, dict):
            cache = {}

        cursor_block_num = -1
        if hasattr(self.transcript_view, "textCursor"):
            tc = self.transcript_view.textCursor()
            if tc and not tc.isNull():
                cursor_block_num = tc.blockNumber()

        any_block_changed = False
        new_cache = {}

        for i in range(min(blocks_count, len(block_groups))):
            groups = [g for g in block_groups[i] if 0 <= g[0] < len(target_segments)]
            if not groups:
                continue

            block = doc.findBlockByNumber(i)
            b_text = block.text()
            b_rev = block.revision()

            cached = cache.get(i)
            is_active_cursor = (i == cursor_block_num)

            if (blocks_count != len(block_groups)) or (cached is None) or (cached[0] != b_text) or (cached[1] != b_rev) or is_active_cursor:
                block_text = b_text
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
                else:
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

                if cached is None or cached[0] != b_text or cached[1] != b_rev:
                    any_block_changed = True

            new_cache[i] = (b_text, b_rev)

        self._block_text_cache = new_cache

        if not use_translation and any_block_changed and hasattr(self, "mark_stale_translations"):
            self.mark_stale_translations()

        if hasattr(self, "transcript_view"):
            timer = getattr(self, "_extra_selections_timer", None)
            if timer is None:
                timer = QTimer(self) if isinstance(self, QObject) else QTimer()
                timer.setSingleShot(True)
                timer.setInterval(150)
                timer.timeout.connect(lambda: hasattr(self, "transcript_view") and self.transcript_view and self.transcript_view.update_extra_selections())
                self._extra_selections_timer = timer
            timer.start()

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


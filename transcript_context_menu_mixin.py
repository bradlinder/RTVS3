"""Radio & TV Story Segmenter — Interactive Transcript Context Menu & Bubble Actions Mixin.

Provides:
- TranscriptContextMenuMixin: Context menu actions (speaker labeling, acoustic
  voice profile matching, comment editing, text highlighting, and formatting)
  and floating selection bubble dispatch actions.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from reaper_bridge import (
    build_reaper_cue_payload,
    attach_reaper_cue_to_mimedata,
    write_reaper_sidecar_cue,
)
from transcript_styles import clean_dark_mode_clipboard_html

try:
    from PySide6.QtCore import Qt, QThread
    from PySide6.QtGui import (
        QAction,
        QKeySequence,
        QTextCursor,
        QTextDocumentFragment,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QMenu,
    )
    from PySide6.QtCore import QMimeData
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, QThread, QMimeData
    from PySide6.QtGui import (
        QAction,
        QKeySequence,
        QTextCursor,
        QTextDocumentFragment,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QMenu,
    )


class TranscriptContextMenuMixin:
    """Mixin for context menu construction and selection bubble quick-actions."""

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
            seg_idx = self.get_segment_index_at_cursor(cursor)
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

    def show_context_menu(self, position):
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

        if not self.has_active_selection():
            self.setTextCursor(hit_cursor)

        self._context_menu_cursor_position = hit_cursor.position()

        menu = self.createStandardContextMenu() if getattr(self, "is_editing_mode", False) else QMenu(self)
        main_win = self.window()

        if self.has_active_selection():
            copy_action = QAction("Copy", self)
            copy_action.setShortcut(QKeySequence.StandardKey.Copy)
            copy_action.triggered.connect(self.copy)
            menu.addAction(copy_action)

            copy_audio_action = QAction("Copy as Audio Clip", self)
            copy_audio_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
            copy_audio_action.triggered.connect(self.copy_selection_as_daw_wav)
            menu.addAction(copy_audio_action)

            ranges = self.get_all_selected_story_ranges()
            count = len(ranges)
            title = f"Add Selected Sections to New Stories ({count})" if count > 1 else "Add Selected Text to New Story"
            add_selection = QAction(title, self)
            add_selection.triggered.connect(lambda: getattr(main_win, "add_selection_to_story", lambda: None)())
            menu.addAction(add_selection)

            play_selection = QAction("Play Selected Text", self)
            play_selection.triggered.connect(lambda: getattr(main_win, "play_transcript_selection", lambda: None)())
            menu.addAction(play_selection)

            clear_selection = QAction("Clear Selection", self)
            clear_selection.setShortcut(QKeySequence("Esc"))
            clear_selection.triggered.connect(self.clear_all_selections)
            menu.addAction(clear_selection)

            menu.addSeparator()
        elif getattr(self, "timeline_selection_span", None) is not None:
            sel_indices = getattr(main_win, "current_selected_story_indices", []) or []
            active_story_idx = sel_indices[0] if len(sel_indices) == 1 else None

            if active_story_idx is not None:
                if hasattr(main_win, "audition_story"):
                    audition_span_act = QAction("Audition Story Playback", self)
                    audition_span_act.triggered.connect(lambda _, idx=active_story_idx: main_win.audition_story(idx))
                    menu.addAction(audition_span_act)

                copy_span_action = QAction("Copy Story Transcript", self)
                copy_span_action.setShortcut(QKeySequence.StandardKey.Copy)
                copy_span_action.triggered.connect(lambda: getattr(self, "copy_highlighted_selection", lambda: False)())
                menu.addAction(copy_span_action)

                copy_story_audio_action = QAction("Copy Story as Audio Clip", self)
                copy_story_audio_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
                copy_story_audio_action.triggered.connect(self.copy_selection_as_daw_wav)
                menu.addAction(copy_story_audio_action)

                if hasattr(main_win, "open_story_metadata_dialog"):
                    meta_span_act = QAction("Story & Post Metadata...", self)
                    meta_span_act.triggered.connect(lambda _, idx=active_story_idx: main_win.open_story_metadata_dialog(idx))
                    menu.addAction(meta_span_act)

                clear_span_action = QAction("Clear Selection", self)
                clear_span_action.setShortcut(QKeySequence("Esc"))
                clear_span_action.triggered.connect(lambda: getattr(main_win, "apply_story_selection_indices", lambda x: None)([]))
                menu.addAction(clear_span_action)
            else:
                copy_span_action = QAction("Copy Highlighted Text", self)
                copy_span_action.setShortcut(QKeySequence.StandardKey.Copy)
                copy_span_action.triggered.connect(lambda: getattr(self, "copy_highlighted_selection", lambda: False)())
                menu.addAction(copy_span_action)

                copy_span_audio_action = QAction("Copy Selection as Audio Clip", self)
                copy_span_audio_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
                copy_span_audio_action.triggered.connect(self.copy_selection_as_daw_wav)
                menu.addAction(copy_span_audio_action)

                clear_span_action = QAction("Clear Selection", self)
                clear_span_action.setShortcut(QKeySequence("Esc"))
                clear_span_action.triggered.connect(lambda: (
                    getattr(main_win, "apply_story_selection_indices", lambda x: None)([])
                    if getattr(main_win, "current_selected_story_indices", None)
                    else self.clear_all_selections()
                ))
                menu.addAction(clear_span_action)

            menu.addSeparator()

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

        voice_tools_menu = menu.addMenu("Voice Profile Tools")

        target_cursor = hit_cursor
        target_seg_idx = self.get_segment_index_at_cursor(target_cursor)
        if target_seg_idx is None:
            target_seg_idx = target_cursor.blockNumber()
        target_time = self.get_timestamp_at_cursor(target_cursor)

        if speaker_target:
            seg_idx, raw_speaker = speaker_target
            teach_action = QAction("Teach / Match This Voice Across Project...", self)
            teach_action.setToolTip("Use this speaker turn as a reference voice profile to find and reassign matching turns across the timeline")
            teach_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.teach_voice_profile_dialog(i, s)
            )
            voice_tools_menu.addAction(teach_action)

            ref_action = QAction("Set as Reference Profile for New Speaker...", self)
            ref_action.setToolTip("Prompt for a new speaker name and immediately match similar turns using this acoustic profile")
            ref_action.triggered.connect(
                lambda _, i=seg_idx, s=raw_speaker: main_win.teach_voice_profile_dialog(i, s, prompt_new_speaker=True)
            )
            voice_tools_menu.addAction(ref_action)

            if hasattr(main_win, "prompt_refine_speaker_run"):
                refine_action = QAction("Refine Rapid Dialog Turns (A/B Classifier)...", self)
                refine_action.setToolTip("Competitively classify turns in a conversational range between two confirmed speakers")
                refine_action.triggered.connect(
                    lambda _, i=seg_idx: main_win.prompt_refine_speaker_run(i, i + 10)
                )
                voice_tools_menu.addAction(refine_action)
        else:
            fallback_idx = target_seg_idx if target_seg_idx is not None else 0
            teach_action = QAction("Teach / Match Voice Across Project...", self)
            teach_action.setToolTip("Use active speaker turn as a reference voice profile to find and reassign matching turns across the timeline")
            teach_action.triggered.connect(
                lambda _, i=fallback_idx: main_win.teach_voice_profile_dialog(i)
            )
            voice_tools_menu.addAction(teach_action)

            ref_action = QAction("Set as Reference Profile for New Speaker...", self)
            ref_action.setToolTip("Prompt for a new speaker name and match similar turns using active acoustic profile")
            ref_action.triggered.connect(
                lambda _, i=fallback_idx: main_win.teach_voice_profile_dialog(i, prompt_new_speaker=True)
            )
            voice_tools_menu.addAction(ref_action)

            if hasattr(main_win, "prompt_refine_speaker_run"):
                refine_action = QAction("Refine Rapid Dialog Turns (A/B Classifier)...", self)
                refine_action.setToolTip("Competitively classify turns in a conversational range between two confirmed speakers")
                refine_action.triggered.connect(
                    lambda _, i=fallback_idx: main_win.prompt_refine_speaker_run(i, i + 10)
                )
                voice_tools_menu.addAction(refine_action)

        voice_tools_menu.addSeparator()

        if hasattr(main_win, "open_speaker_manager_dialog"):
            manage_spk_act = QAction("Manage Speakers & Detection Clusters...", self)
            manage_spk_act.setToolTip("Inspect speaker durations, rename or assign aliases, and merge duplicate acoustic clusters")
            manage_spk_act.triggered.connect(main_win.open_speaker_manager_dialog)
            voice_tools_menu.addAction(manage_spk_act)

        menu.addSeparator()

        insert_menu = menu.addMenu("Add Speaker Label Here")
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

        target_seg = self.get_segment_index_at_cursor(hit_cursor)
        if target_seg is None:
            target_seg = hit_cursor.blockNumber()
        has_comment = False
        if hasattr(main_win, "transcript") and main_win.transcript:
            segs = main_win.transcript.get("segments", [])
            if 0 <= target_seg < len(segs):
                has_comment = bool(segs[target_seg].get("comments") or segs[target_seg].get("notes"))
        comment_title = "Edit Comment..." if has_comment else "Add Comment..."

        hl_colors = [
            ("Yellow", "#fef08a"),
            ("Green", "#bbf7d0"),
            ("Blue / Cyan", "#bae6fd"),
            ("Pink", "#fbcfe8"),
            ("Orange", "#fed7aa"),
            ("Purple", "#e9d5ff"),
        ]

        if not getattr(self, "is_editing_mode", False):
            if self.has_active_selection():
                add_vocab = QAction("Add Selected Text to Glossary", menu)
                def _add_vocab_from_selection():
                    ranges = self.get_all_selected_story_ranges()
                    txt = ranges[0]["text"] if ranges else self.textCursor().selectedText()
                    if hasattr(main_win, "add_to_glossary"):
                        main_win.add_to_glossary(txt)
                add_vocab.triggered.connect(_add_vocab_from_selection)
                menu.addAction(add_vocab)

                add_alt_spelling_act = QAction("Add Selected Text as Alternate Spelling For...", menu)
                def _add_alt_from_selection():
                    ranges = self.get_all_selected_story_ranges()
                    txt = ranges[0]["text"] if ranges else self.textCursor().selectedText()
                    if hasattr(main_win, "prompt_add_alternate_spelling"):
                        main_win.prompt_add_alternate_spelling(txt)
                add_alt_spelling_act.triggered.connect(_add_alt_from_selection)
                menu.addAction(add_alt_spelling_act)

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
                del_comment_act = QAction("Delete Comment", menu)
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

            hl_title = "Change Highlight Color" if active_hl_hex else "Highlight Text"

            hl_menu = menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            if active_hl_hex:
                hl_menu.addSeparator()
                act_rem_hl = hl_menu.addAction("Remove Highlight")
                act_rem_hl.triggered.connect(self.remove_highlight)

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

            hl_title = "Change Highlight Color" if active_hl_hex else "Highlight Text"

            hl_menu = fmt_menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
            if active_hl_hex:
                hl_menu.addSeparator()
                act_rem_hl = hl_menu.addAction("Remove Highlight")
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
                del_comment_act = QAction("Delete Comment", menu)
                del_comment_act.triggered.connect(
                    lambda _, s=target_seg: getattr(main_win, "delete_segment_comment", lambda x: None)(s)
                )
                menu.addAction(del_comment_act)

            menu.addSeparator()
            find_action = QAction("Find and Replace...\tCtrl+F", menu)
            find_action.triggered.connect(lambda: getattr(main_win, "open_find_replace", lambda: None)())
            menu.addAction(find_action)

            menu.addSeparator()
            exit_action = QAction("View Transcript\tF2", menu)
            exit_action.triggered.connect(lambda: self.set_editing_mode(False))
            menu.addAction(exit_action)

        menu.exec(self.mapToGlobal(position))

    def copy_highlighted_selection(self) -> bool:
        """Copy the active story or timeline selection span to clipboard when no cursor text is selected.

        Preserves rich HTML styling with dark-mode black text normalization, sets plain text,
        attaches REAPER DAW clip cue payload, and posts a notification to the main window status bar.
        Returns True if text was copied.
        """
        span = getattr(self, "timeline_selection_span", None)
        if not span:
            return False
        s_char, e_char = span
        doc = self.document()
        if not doc:
            return False
        raw_count = doc.characterCount() if doc else None
        doc_len = raw_count if isinstance(raw_count, int) else 1000000
        if not (0 <= s_char < doc_len and 0 < e_char <= doc_len and s_char < e_char):
            return False

        cursor = QTextCursor(doc)
        cursor.setPosition(s_char)
        cursor.setPosition(e_char, QTextCursor.MoveMode.KeepAnchor)

        plain_text = ""
        html_text = ""

        try:
            fragment = QTextDocumentFragment(cursor)
            p_text = fragment.toPlainText()
            if isinstance(p_text, str) and p_text:
                plain_text = p_text.strip()
            html_text = fragment.toHtml()
        except Exception:
            pass

        if not plain_text and hasattr(cursor, "selectedText"):
            raw_sel = cursor.selectedText()
            if isinstance(raw_sel, str) and raw_sel:
                plain_text = raw_sel.strip()

        if not plain_text:
            full_txt = self.toPlainText() if hasattr(self, "toPlainText") else ""
            if isinstance(full_txt, str) and full_txt:
                plain_text = full_txt[s_char:e_char].strip()
                html_text = plain_text

        if not plain_text:
            return False

        theme = getattr(self, "current_theme", "dark")
        if theme in ("dark", "high_contrast") and html_text:
            html_text = clean_dark_mode_clipboard_html(html_text)

        self._last_copied_text = plain_text
        self._last_copied_html = html_text

        main_win = self.window()
        story_obj = None
        story_title = ""
        st_sec = None
        en_sec = None

        # 1. Exact Story boundary priority
        indices = getattr(main_win, "current_selected_story_indices", [])
        stories = getattr(main_win, "stories", [])
        if isinstance(indices, list) and isinstance(stories, list):
            if len(indices) == 1 and 0 <= indices[0] < len(stories):
                story_obj = stories[indices[0]]
                story_title = f" for '{story_obj.title}'"
                st_sec = getattr(story_obj, "start", None)
                en_sec = getattr(story_obj, "end", None)
            elif len(indices) > 1:
                story_title = f" for {len(indices)} stories"

        # 2. Timeline drag selection range priority
        if st_sec is None or en_sec is None:
            tl = getattr(main_win, "timeline", None)
            if tl is not None:
                sel_st = getattr(tl, "selection_start", None)
                sel_en = getattr(tl, "selection_end", None)
                if sel_st is None or sel_en is None:
                    canvas = getattr(tl, "canvas", None)
                    if canvas is not None:
                        sel_st = getattr(canvas, "selection_start", None)
                        sel_en = getattr(canvas, "selection_end", None)
                if sel_st is not None and sel_en is not None and sel_en != sel_st:
                    st_sec = min(float(sel_st), float(sel_en))
                    en_sec = max(float(sel_st), float(sel_en))

        # 3. Fall back to character span timestamp mapping
        if st_sec is None or en_sec is None:
            if hasattr(self, "get_time_range_for_char_span"):
                time_range = self.get_time_range_for_char_span(s_char, e_char)
                if time_range and len(time_range) == 2 and time_range[1] > time_range[0]:
                    st_sec, en_sec = time_range

        app = QApplication.instance()
        if app is not None and hasattr(app, "thread") and callable(getattr(app, "thread", None)) and QThread.currentThread() == app.thread():
            mime_data = QMimeData()
            mime_data.setText(plain_text)
            if html_text:
                mime_data.setHtml(html_text)

            # Unified multi-channel attachment (REAPER cue & optional DAW WAV)
            if st_sec is not None and en_sec is not None and en_sec > st_sec:
                try:
                    from reaper_bridge import populate_unified_copy_mimedata
                    populate_unified_copy_mimedata(
                        main_win=main_win,
                        mime_data=mime_data,
                        start_sec=st_sec,
                        end_sec=en_sec,
                        plain_text=plain_text,
                        title=getattr(story_obj, "title", ""),
                        clip_type="story" if story_obj is not None else "selection",
                        story_obj=story_obj,
                    )
                except Exception as exc:
                    logger.warning(f"Failed to populate unified copy payload: {exc}")

            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setMimeData(mime_data)

        if hasattr(main_win, "statusBar") and main_win.statusBar():
            main_win.statusBar().showMessage(
                f"Copied story transcript{story_title} ({len(plain_text)} characters) to clipboard.",
                3500,
            )
        return True

    def copy_selection_for_reaper(self) -> bool:
        """Explicitly build and copy REAPER DAW clip cue payload for the active text or story selection."""
        main_win = self.window()
        plain_text = ""
        st_sec = 0.0
        en_sec = 0.0
        story_obj = None
        title = ""

        # 1. Active cursor text selection
        if self.has_active_selection():
            cursor = self.textCursor()
            plain_text = cursor.selectedText().strip()
            time_range = self.get_selected_time_range()
            if time_range and len(time_range) == 2 and time_range[1] > time_range[0]:
                st_sec, en_sec = time_range
        # 2. Timeline story selection span
        elif getattr(self, "timeline_selection_span", None) is not None:
            span = getattr(self, "timeline_selection_span")
            time_range = self.get_time_range_for_char_span(span[0], span[1])
            if time_range and len(time_range) == 2 and time_range[1] > time_range[0]:
                st_sec, en_sec = time_range
            indices = getattr(main_win, "current_selected_story_indices", [])
            stories = getattr(main_win, "stories", [])
            if isinstance(indices, list) and isinstance(stories, list) and len(indices) == 1:
                if 0 <= indices[0] < len(stories):
                    story_obj = stories[indices[0]]
                    title = getattr(story_obj, "title", "")
            cursor = QTextCursor(self.document())
            cursor.setPosition(span[0])
            cursor.setPosition(span[1], QTextCursor.MoveMode.KeepAnchor)
            plain_text = cursor.selectedText().strip()

        if en_sec <= st_sec or not plain_text:
            if hasattr(main_win, "statusBar") and main_win.statusBar():
                main_win.statusBar().showMessage("No active time range found for REAPER clip cue.", 3000)
            return False

        app = QApplication.instance()
        if app is not None and hasattr(app, "thread") and callable(getattr(app, "thread", None)) and QThread.currentThread() == app.thread():
            mime_data = QMimeData()
            mime_data.setText(plain_text)
            try:
                payload = build_reaper_cue_payload(
                    main_win=main_win,
                    start_sec=st_sec,
                    end_sec=en_sec,
                    plain_text=plain_text,
                    title=title,
                    clip_type="story" if story_obj is not None else "selection",
                    story_obj=story_obj,
                )
                attach_reaper_cue_to_mimedata(mime_data, payload)
            except Exception as exc:
                logger.warning(f"Failed to build REAPER cue: {exc}")

            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setMimeData(mime_data)

        if hasattr(main_win, "statusBar") and main_win.statusBar():
            main_win.statusBar().showMessage(
                f"Copied REAPER DAW clip cue for '{title or plain_text[:30]}' ({st_sec:.1f}s - {en_sec:.1f}s) to clipboard & sidecar.",
                4000,
            )
        return True

    def copy_selection_as_daw_wav(self) -> bool:
        """Render temporary WAV audio clip and copy it to the OS clipboard (CF_HDROP) for any DAW."""
        main_win = self.window()
        plain_text = ""
        st_sec = 0.0
        en_sec = 0.0
        story_obj = None
        title = ""

        # 1. Active cursor text selection
        if self.has_active_selection():
            cursor = self.textCursor()
            plain_text = cursor.selectedText().strip()
            time_range = self.get_selected_time_range()
            if time_range and len(time_range) == 2 and time_range[1] > time_range[0]:
                st_sec, en_sec = time_range
        # 2. Timeline story selection span
        elif getattr(self, "timeline_selection_span", None) is not None:
            span = getattr(self, "timeline_selection_span")
            time_range = self.get_time_range_for_char_span(span[0], span[1])
            if time_range and len(time_range) == 2 and time_range[1] > time_range[0]:
                st_sec, en_sec = time_range
            indices = getattr(main_win, "current_selected_story_indices", [])
            stories = getattr(main_win, "stories", [])
            if isinstance(indices, list) and isinstance(stories, list) and len(indices) == 1:
                if 0 <= indices[0] < len(stories):
                    story_obj = stories[indices[0]]
                    title = getattr(story_obj, "title", "")
            cursor = QTextCursor(self.document())
            cursor.setPosition(span[0])
            cursor.setPosition(span[1], QTextCursor.MoveMode.KeepAnchor)
            plain_text = cursor.selectedText().strip()

        if en_sec <= st_sec or not plain_text:
            if hasattr(main_win, "statusBar") and main_win.statusBar():
                main_win.statusBar().showMessage("No active time range found to render DAW audio clip.", 3000)
            return False

        from reaper_bridge import copy_selection_as_daw_wav_clip
        wav_path = copy_selection_as_daw_wav_clip(
            main_win=main_win,
            start_sec=st_sec,
            end_sec=en_sec,
            plain_text=plain_text,
            html_text="",
            title=title,
            story_obj=story_obj,
        )
        return wav_path is not None


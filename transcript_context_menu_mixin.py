"""Radio & TV Story Segmenter — Interactive Transcript Context Menu & Bubble Actions Mixin.

Provides:
- TranscriptContextMenuMixin: Context menu actions (speaker labeling, acoustic
  voice profile matching, comment editing, text highlighting, and formatting)
  and floating selection bubble dispatch actions.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QAction,
        QKeySequence,
        QTextCursor,
    )
    from PySide6.QtWidgets import (
        QMenu,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtGui import (
        QAction,
        QKeySequence,
        QTextCursor,
    )
    from PySide6.QtWidgets import (
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
            add_vocab = QAction("Add Selected Text to Glossary", menu)
            add_vocab.setEnabled(self.has_active_selection())
            def _add_vocab_from_selection():
                ranges = self.get_all_selected_story_ranges()
                txt = ranges[0]["text"] if ranges else self.textCursor().selectedText()
                if hasattr(main_win, "add_to_glossary"):
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
            hl_menu.addSeparator()
            act_rem_hl = hl_menu.addAction("Remove Highlight")
            act_rem_hl.triggered.connect(self.remove_highlight)

            toggle_comments_act = QAction("Toggle Comments Sidebar\tCtrl+Alt+C", menu)
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

            hl_title = "Change Highlight Color" if active_hl_hex else "Highlight Text"

            hl_menu = fmt_menu.addMenu(hl_title)
            for label, hex_code in hl_colors:
                lbl_text = label
                if active_hl_hex and hex_code.lower() == active_hl_hex:
                    lbl_text += " (Current)"
                act = hl_menu.addAction(lbl_text)
                act.triggered.connect(lambda _, c=hex_code: self.toggle_highlight(c, force_apply=True))
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

            rem_hl_act = QAction("Remove Highlight", menu)
            rem_hl_act.triggered.connect(self.remove_highlight)
            menu.addAction(rem_hl_act)

            toggle_comments_act = QAction("Toggle Comments Sidebar\tCtrl+Alt+C", menu)
            toggle_comments_act.triggered.connect(lambda: getattr(main_win, "toggle_comments_panel", lambda: None)())
            menu.addAction(toggle_comments_act)

            menu.addSeparator()
            find_action = QAction("Find and Replace...\tCtrl+F", menu)
            find_action.triggered.connect(lambda: getattr(main_win, "open_find_replace", lambda: None)())
            menu.addAction(find_action)

            menu.addSeparator()
            exit_action = QAction("View Transcript\tF2", menu)
            exit_action.triggered.connect(lambda: self.set_editing_mode(False))
            menu.addAction(exit_action)

        menu.exec(self.mapToGlobal(position))

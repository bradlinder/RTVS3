"""transcript_editor_dialogs.py - Dialog and floating toolbar components for transcript editing.

Provides:
- FindReplaceDialog: Modeless find-and-replace dialog for QTextEdit/InteractiveTranscriptEdit
- TranscriptSelectionBubble: Floating quick-action toolbar on transcript selection
"""

import os
import re
from typing import Optional, Any

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
    from PySide6.QtWidgets import (
        QDialog,
        QWidget,
        QFrame,
        QLabel,
        QToolButton,
        QLineEdit,
        QCheckBox,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QMessageBox,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
    from PySide6.QtWidgets import (
        QDialog,
        QWidget,
        QFrame,
        QLabel,
        QToolButton,
        QLineEdit,
        QCheckBox,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QMessageBox,
    )


class FindReplaceDialog(QDialog):
    """Modeless find-and-replace dialog for QTextEdit / InteractiveTranscriptEdit."""

    def __init__(self, text_edit, parent=None):
        dlg_parent = parent if (isinstance(parent, QWidget) or hasattr(parent, "winId")) else None
        super().__init__(dlg_parent)
        self._custom_parent = parent
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Search phrase...")
        self.count_label = QLabel("", self)
        self.count_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; padding: 0 4px;")
        find_row = QHBoxLayout()
        find_row.addWidget(self.find_input, 1)
        find_row.addWidget(self.count_label)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replacement text...")

        form.addRow("Find:", find_row)
        form.addRow("Replace with:", self.replace_input)
        layout.addLayout(form)

        options_layout = QHBoxLayout()
        self.case_checkbox = QCheckBox("Match Case")
        self.whole_word_checkbox = QCheckBox("Whole Word")
        self.speakers_checkbox = QCheckBox("Include Speakers")
        self.speakers_checkbox.setChecked(True)
        self.speakers_checkbox.setToolTip("Also replace occurrences matching speaker display aliases")
        options_layout.addWidget(self.case_checkbox)
        options_layout.addWidget(self.whole_word_checkbox)
        options_layout.addWidget(self.speakers_checkbox)
        layout.addLayout(options_layout)

        btn_layout = QHBoxLayout()
        self.find_prev_btn = QPushButton("Find Prev")
        self.find_prev_btn.setToolTip("Find previous occurrence (Shift+Enter / Ctrl+Shift+G)")
        self.find_prev_btn.clicked.connect(self.find_prev)
        self.find_next_btn = QPushButton("Find Next")
        self.find_next_btn.setToolTip("Find next occurrence (Enter / Ctrl+G)")
        self.find_next_btn.clicked.connect(self.find_next)
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setToolTip("Replace current match")
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setToolTip("Replace all occurrences in transcript")
        self.replace_all_btn.clicked.connect(self.replace_all)

        btn_layout.addWidget(self.find_prev_btn)
        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

        self.find_input.textChanged.connect(self._on_find_text_changed)

        orig_find_key_press = self.find_input.keyPressEvent
        def _find_input_key_press(event):
            ctrl = bool(event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier))
            shift = bool(event.modifiers() & Qt.ShiftModifier)
            if (ctrl and event.key() == Qt.Key_G) or event.key() == Qt.Key_F3:
                if shift:
                    self.find_prev()
                else:
                    self.find_next()
                event.accept()
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if shift:
                    self.find_prev()
                else:
                    self.find_next()
                event.accept()
                return
            orig_find_key_press(event)
        self.find_input.keyPressEvent = _find_input_key_press

        orig_replace_key_press = self.replace_input.keyPressEvent
        def _replace_input_key_press(event):
            ctrl = bool(event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier))
            shift = bool(event.modifiers() & Qt.ShiftModifier)
            if (ctrl and event.key() == Qt.Key_G) or event.key() == Qt.Key_F3:
                if shift:
                    self.find_prev()
                else:
                    self.find_next()
                event.accept()
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.replace()
                event.accept()
                return
            orig_replace_key_press(event)
        self.replace_input.keyPressEvent = _replace_input_key_press

    def keyPressEvent(self, event):
        ctrl = bool(event.modifiers() & Qt.ControlModifier or event.modifiers() & Qt.MetaModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)

        # Ctrl+G / Cmd+G or F3: Find Next (or Find Previous with Shift)
        if (ctrl and event.key() == Qt.Key_G) or event.key() == Qt.Key_F3:
            if shift:
                self.find_prev()
            else:
                self.find_next()
            event.accept()
            return

        # Ctrl+F / Cmd+F: Refocus search query
        if ctrl and event.key() == Qt.Key_F:
            self.find_input.setFocus()
            self.find_input.selectAll()
            event.accept()
            return

        # Shift+Enter inside Find input: Find Previous
        if shift and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.find_prev()
            event.accept()
            return

        super().keyPressEvent(event)

    def _on_find_text_changed(self, text: str):
        target = text.strip()
        self._sync_parent_search(target)
        self._update_local_match_count()

    def _update_local_match_count(self):
        parent = self.parent()
        if parent and hasattr(parent, "transcript_search_count_lbl") and parent.transcript_search_count_lbl:
            self.count_label.setText(parent.transcript_search_count_lbl.text())
        elif parent and hasattr(parent, "_search_match_ranges"):
            matches = getattr(parent, "_search_match_ranges", [])
            idx = getattr(parent, "_search_match_index", -1)
            if matches:
                self.count_label.setText(f"{idx + 1} / {len(matches)}")
            else:
                self.count_label.setText("0 / 0" if self.find_input.text().strip() else "")

    def _sync_parent_search(self, target: str):
        parent = self.parent()
        if parent and hasattr(parent, "transcript_search_input") and parent.transcript_search_input:
            if parent.transcript_search_input.text() != target:
                parent.transcript_search_input.setText(target)

    @property
    def main_window(self):
        parent = getattr(self, "_custom_parent", None) or self.parent()
        if parent and hasattr(parent, "transcript"):
            return parent
        if self.text_edit:
            win = getattr(self.text_edit, "window", lambda: None)()
            if win and hasattr(win, "transcript"):
                return win
        return parent

    def get_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if getattr(self, "whole_word_checkbox", None) and self.whole_word_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        return flags

    def find_next(self):
        target = self.find_input.text()
        if not target:
            return False

        parent = self.parent()
        self._sync_parent_search(target)

        # Advance via parent match tracker if active and no custom case/word flags
        flags = self.get_flags()
        if not self.case_checkbox.isChecked() and not (getattr(self, "whole_word_checkbox", None) and self.whole_word_checkbox.isChecked()):
            if parent and hasattr(parent, "_search_match_ranges") and isinstance(getattr(parent, "_search_match_ranges", None), list) and parent._search_match_ranges:
                curr_idx = getattr(parent, "_search_match_index", 0)
                if not isinstance(curr_idx, int):
                    curr_idx = 0
                parent._search_match_index = (curr_idx + 1) % len(parent._search_match_ranges)
                parent._sync_search_match_ui(scroll_to_match=True)
                self._update_local_match_count()
                return True

        found = self.text_edit.find(target, flags)
        wrapped = False
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, flags)
            wrapped = True

        if found:
            self.text_edit.ensureCursorVisible()

        if parent and hasattr(parent, "statusBar") and parent.statusBar():
            if found:
                msg = f"Found next: '{target}'" + (" (wrapped to start)" if wrapped else "")
                parent.statusBar().showMessage(msg, 2000)
            else:
                parent.statusBar().showMessage(f"Phrase not found: '{target}'", 2500)

        self._update_local_match_count()
        return found

    def find_prev(self):
        target = self.find_input.text()
        if not target:
            return False

        parent = self.parent()
        self._sync_parent_search(target)

        flags = self.get_flags() | QTextDocument.FindFlag.FindBackward
        if not self.case_checkbox.isChecked() and not (getattr(self, "whole_word_checkbox", None) and self.whole_word_checkbox.isChecked()):
            if parent and hasattr(parent, "_search_match_ranges") and isinstance(getattr(parent, "_search_match_ranges", None), list) and parent._search_match_ranges:
                curr_idx = getattr(parent, "_search_match_index", 0)
                if not isinstance(curr_idx, int):
                    curr_idx = 0
                parent._search_match_index = (curr_idx - 1) % len(parent._search_match_ranges)
                parent._sync_search_match_ui(scroll_to_match=True)
                self._update_local_match_count()
                return True

        # Move cursor to beginning of existing selection so backward search advances to the prior match
        cur = self.text_edit.textCursor()
        if cur.hasSelection():
            cur.setPosition(cur.selectionStart())
            self.text_edit.setTextCursor(cur)

        found = self.text_edit.find(target, flags)
        wrapped = False
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, flags)
            wrapped = True

        if found:
            self.text_edit.ensureCursorVisible()

        if parent and hasattr(parent, "statusBar") and parent.statusBar():
            if found:
                msg = f"Found previous: '{target}'" + (" (wrapped to end)" if wrapped else "")
                parent.statusBar().showMessage(msg, 2000)
            else:
                parent.statusBar().showMessage(f"Phrase not found: '{target}'", 2500)

        self._update_local_match_count()
        return found

    def replace(self):
        target = self.find_input.text()
        replacement = self.replace_input.text()
        if not target:
            return

        cursor = self.text_edit.textCursor() if self.text_edit else None
        if not cursor or not cursor.hasSelection():
            if not self.find_next():
                return
            cursor = self.text_edit.textCursor()
            if not cursor or not cursor.hasSelection():
                return

        case_sensitive = self.case_checkbox.isChecked()
        sel_text = cursor.selectedText()
        matches = (sel_text == target) if case_sensitive else (sel_text.lower() == target.lower())
        if not matches:
            if not self.find_next():
                return
            cursor = self.text_edit.textCursor()
            sel_text = cursor.selectedText()
            matches = (sel_text == target) if case_sensitive else (sel_text.lower() == target.lower())
            if not matches:
                return

        main_win = self.main_window
        if not main_win or not getattr(main_win, "transcript", None):
            self._fallback_widget_replace(replacement)
            return

        if hasattr(main_win, "flush_pending_transcript_undo"):
            main_win.flush_pending_transcript_undo()

        sel_start = cursor.selectionStart()
        probe_cur = QTextCursor(cursor)
        probe_cur.setPosition(sel_start)
        href = probe_cur.charFormat().anchorHref() or ""
        if not href and sel_start + 1 <= self.text_edit.document().characterCount():
            probe_cur.setPosition(sel_start + 1)
            href = probe_cur.charFormat().anchorHref() or ""

        # Case A: Match is on a speaker anchor
        if href.startswith("speaker:"):
            parts = href.split(":", 2)
            seg_idx = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1
            raw_spk = parts[2] if len(parts) > 2 else ""

            before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None
            curr_name = main_win.display_speaker(raw_spk) if hasattr(main_win, "display_speaker") else sel_text
            pattern = re.compile(re.escape(target), 0 if case_sensitive else re.IGNORECASE)
            new_spk_name = pattern.sub(lambda m: replacement, curr_name, count=1)

            if hasattr(main_win, "speaker_names"):
                if raw_spk:
                    main_win.speaker_names[str(raw_spk)] = new_spk_name
                override_key = f"SEG_{seg_idx}_SPEAKER"
                main_win.speaker_names[override_key] = new_spk_name
                if hasattr(main_win, "segment_speaker_overrides") and seg_idx >= 0:
                    main_win.segment_speaker_overrides[seg_idx] = override_key
                if hasattr(main_win, "add_custom_speaker_to_glossary"):
                    main_win.add_custom_speaker_to_glossary(new_spk_name)

            if before_state is not None and hasattr(main_win, "_commit_project_state_change"):
                main_win._commit_project_state_change(before_state, f"Replace Speaker Name: '{target}' → '{replacement}'")
            if hasattr(main_win, "render_transcript"):
                main_win.render_transcript()
            if hasattr(main_win, "save_project"):
                main_win.save_project()
            if hasattr(main_win, "mark_project_dirty"):
                main_win.mark_project_dirty(f"Replace Speaker Name: '{target}' → '{replacement}'")
            self.find_next()
            return

        # Case B: Match is in transcript text
        target_seg_idx = None
        target_word_idx = None

        if href.startswith("word:"):
            parts = href.split(":")
            if len(parts) >= 4 and parts[2].isdigit():
                target_seg_idx = int(parts[2])
                target_word_idx = int(parts[3]) if parts[3].isdigit() else None

        if target_seg_idx is None:
            char_map = getattr(self.text_edit, "char_timestamp_map", [])
            for c_start, c_end, w_start, w_end, s_idx, w_idx in char_map:
                if (c_start <= sel_start < c_end) or (c_start >= sel_start and c_end <= cursor.selectionEnd()):
                    target_seg_idx = s_idx
                    target_word_idx = w_idx
                    break

        if target_seg_idx is None:
            block_num = cursor.blockNumber()
            block_groups = getattr(main_win, "_block_segment_groups", [])
            if block_num < len(block_groups) and block_groups[block_num]:
                target_seg_idx = block_groups[block_num][0][0]

        segments = main_win.transcript.get("segments", [])
        if target_seg_idx is not None and 0 <= target_seg_idx < len(segments):
            seg = segments[target_seg_idx]
            before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

            pattern = re.compile(
                r'\b' + re.escape(target) + r'\b' if (getattr(self, "whole_word_checkbox", None) and self.whole_word_checkbox.isChecked()) else re.escape(target),
                0 if case_sensitive else re.IGNORECASE
            )

            replaced_in_word = False
            words = seg.get("words", [])
            if target_word_idx is not None and 0 <= target_word_idx < len(words):
                w_obj = words[target_word_idx]
                w_text = w_obj.get("word", "")
                if pattern.search(w_text):
                    w_obj["word"] = pattern.sub(lambda m: replacement, w_text, count=1)
                    replaced_in_word = True
                    seg["text"] = " ".join(w.get("word", "") for w in words)

            if not replaced_in_word:
                old_text = seg.get("text", "")
                new_text, n = pattern.subn(lambda m: replacement, old_text, count=1)
                seg["text"] = new_text
                if hasattr(main_win, "sync_segment_words"):
                    main_win.sync_segment_words(seg, new_text)
            elif hasattr(main_win, "sync_segment_words"):
                main_win.sync_segment_words(seg, seg.get("text", ""))

            # Sync full transcript text string if present
            if "text" in main_win.transcript and isinstance(main_win.transcript["text"], str):
                main_win.transcript["text"] = pattern.sub(lambda m: replacement, main_win.transcript["text"], count=1)

            if before_state is not None and hasattr(main_win, "_commit_project_state_change"):
                main_win._commit_project_state_change(before_state, f"Replace: '{target}' → '{replacement}'")
            if hasattr(main_win, "render_transcript"):
                main_win.render_transcript()
            if hasattr(main_win, "save_project"):
                main_win.save_project()
            if hasattr(main_win, "mark_project_dirty"):
                main_win.mark_project_dirty(f"Replace: '{target}' → '{replacement}'")

            self.find_next()
            return

        self._fallback_widget_replace(replacement)

    def replace_all(self):
        target = self.find_input.text()
        replacement = self.replace_input.text()
        if not target:
            return

        main_win = self.main_window
        if not main_win or not getattr(main_win, "transcript", None):
            self._fallback_widget_replace_all(target, replacement)
            return

        if hasattr(main_win, "flush_pending_transcript_undo"):
            main_win.flush_pending_transcript_undo()

        before_state = main_win._capture_project_state() if hasattr(main_win, "_capture_project_state") else None

        case_sensitive = self.case_checkbox.isChecked()
        whole_word = getattr(self, "whole_word_checkbox", None) and self.whole_word_checkbox.isChecked()
        include_speakers = getattr(self, "speakers_checkbox", None) and self.speakers_checkbox.isChecked()

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern_str = r'\b' + re.escape(target) + r'\b' if whole_word else re.escape(target)
        try:
            regex = re.compile(pattern_str, flags)
        except Exception:
            regex = re.compile(re.escape(target), flags)

        count = 0
        transcript = main_win.transcript
        segments = transcript.get("segments", [])

        # 1. Replace in transcript segments & update word timings
        for seg in segments:
            text = seg.get("text", "")
            if text and regex.search(text):
                new_text, n = regex.subn(lambda m: replacement, text)
                if n > 0:
                    count += n
                    seg["text"] = new_text
                    if hasattr(main_win, "sync_segment_words"):
                        main_win.sync_segment_words(seg, new_text)

        # 2. Replace in full transcript text string if present
        if "text" in transcript and isinstance(transcript["text"], str):
            new_full_text, _ = regex.subn(lambda m: replacement, transcript["text"])
            transcript["text"] = new_full_text

        # 3. Replace in translation segments if present
        translations = getattr(main_win, "translations", {})
        if isinstance(translations, dict):
            for t_item in translations.values():
                if isinstance(t_item, dict):
                    t_segs = t_item.get("segments", [])
                    for t_seg in t_segs:
                        t_text = t_seg.get("text", "")
                        if t_text and regex.search(t_text):
                            new_t_text, n = regex.subn(lambda m: replacement, t_text)
                            if n > 0:
                                t_seg["text"] = new_t_text
                    if "text" in t_item and isinstance(t_item["text"], str):
                        new_t_full, _ = regex.subn(lambda m: replacement, t_item["text"])
                        t_item["text"] = new_t_full

        # 4. Replace in speaker names if enabled
        if include_speakers and hasattr(main_win, "speaker_names"):
            spk_names = main_win.speaker_names
            spk_count = 0
            for k in list(spk_names.keys()):
                old_spk = spk_names[k]
                if isinstance(old_spk, str) and regex.search(old_spk):
                    new_spk, n = regex.subn(lambda m: replacement, old_spk)
                    if n > 0:
                        spk_names[k] = new_spk
                        spk_count += n
            count += spk_count

            # Update custom_speakers_glossary
            glossary = getattr(main_win, "custom_speakers_glossary", None)
            if isinstance(glossary, (list, set)):
                new_glossary = []
                for g in glossary:
                    if isinstance(g, str) and regex.search(g):
                        new_g, _ = regex.subn(lambda m: replacement, g)
                        new_glossary.append(new_g)
                    else:
                        new_glossary.append(g)
                main_win.custom_speakers_glossary = type(glossary)(new_glossary)

        if count > 0:
            if before_state is not None and hasattr(main_win, "_commit_project_state_change"):
                main_win._commit_project_state_change(
                    before_state,
                    f"Replace All: '{target}' → '{replacement}'"
                )
            if hasattr(main_win, "mark_project_dirty"):
                main_win.mark_project_dirty(f"Replace All: '{target}' → '{replacement}'")
            if hasattr(main_win, "render_transcript"):
                main_win.render_transcript()
            if hasattr(main_win, "save_project"):
                main_win.save_project()

            if hasattr(main_win, "_on_transcript_search_text_changed"):
                main_win._on_transcript_search_text_changed(target)
            self._update_local_match_count()
            if os.environ.get("RTVS_TEST_MODE") != "1":
                try:
                    QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s) across the project.")
                except Exception:
                    pass
        else:
            if os.environ.get("RTVS_TEST_MODE") != "1":
                try:
                    QMessageBox.information(self, "Replace All", f"Phrase '{target}' not found.")
                except Exception:
                    pass

    def _fallback_widget_replace(self, replacement: str):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replacement)
        self.find_next()

    def _fallback_widget_replace_all(self, target: str, replacement: str):
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
        parent = self.parent()
        if parent and hasattr(parent, "_on_transcript_search_text_changed"):
            parent._on_transcript_search_text_changed(target)
        self._update_local_match_count()
        if os.environ.get("RTVS_TEST_MODE") != "1":
            try:
                QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")
            except Exception:
                pass


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

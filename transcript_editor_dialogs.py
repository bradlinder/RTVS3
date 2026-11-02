"""transcript_editor_dialogs.py - Dialog and floating toolbar components for transcript editing.

Provides:
- FindReplaceDialog: Modeless find-and-replace dialog for QTextEdit/InteractiveTranscriptEdit
- TranscriptSelectionBubble: Floating quick-action toolbar on transcript selection
"""

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
    from PySide6.QtWidgets import (
        QDialog,
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
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")
        self.setFixedWidth(360)

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
        self.case_checkbox = QCheckBox("Match Case")

        form.addRow("Find:", find_row)
        form.addRow("Replace with:", self.replace_input)
        layout.addLayout(form)
        layout.addWidget(self.case_checkbox)

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

    def get_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        target = self.find_input.text()
        if not target:
            return False

        parent = self.parent()
        self._sync_parent_search(target)

        # Advance via parent match tracker if active
        if parent and hasattr(parent, "_search_match_ranges") and parent._search_match_ranges:
            parent._search_match_index = (parent._search_match_index + 1) % len(parent._search_match_ranges)
            parent._sync_search_match_ui(scroll_to_match=True)
            self._update_local_match_count()
            return True

        found = self.text_edit.find(target, self.get_flags())
        wrapped = False
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, self.get_flags())
            wrapped = True

        if found:
            self.text_edit.ensureCursorVisible()

        parent = self.parent()
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

        # Retreat via parent match tracker if active
        if parent and hasattr(parent, "_search_match_ranges") and parent._search_match_ranges:
            parent._search_match_index = (parent._search_match_index - 1) % len(parent._search_match_ranges)
            parent._sync_search_match_ui(scroll_to_match=True)
            self._update_local_match_count()
            return True

        # Move cursor to beginning of existing selection so backward search advances to the prior match
        cur = self.text_edit.textCursor()
        if cur.hasSelection():
            cur.setPosition(cur.selectionStart())
            self.text_edit.setTextCursor(cur)

        flags = self.get_flags() | QTextDocument.FindFlag.FindBackward
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

        parent = self.parent()
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
        parent = self.parent()
        if parent and hasattr(parent, "_on_transcript_search_text_changed"):
            parent._on_transcript_search_text_changed(target)
        self._update_local_match_count()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")


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

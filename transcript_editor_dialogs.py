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
        self.replace_input = QLineEdit()
        self.case_checkbox = QCheckBox("Match Case")

        form.addRow("Find:", self.find_input)
        form.addRow("Replace with:", self.replace_input)
        layout.addLayout(form)
        layout.addWidget(self.case_checkbox)

        btn_layout = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")

        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

        self.find_next_btn.clicked.connect(self.find_next)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)

        self.shortcut_find_next = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_find_next.activated.connect(self.find_next)

    def get_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        target = self.find_input.text()
        if not target:
            return False

        found = self.text_edit.find(target, self.get_flags())
        if not found:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(target, self.get_flags())

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

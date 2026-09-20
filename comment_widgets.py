"""
comment_widgets.py - Range-Anchored Comments Panel & Comment Editor Widgets
Extracted from prs_shared.py as part of Phase 2 Modularization.

Provides:
- CommentEditorDialog: Multi-line document-style comment and note editor dialog
- NoteEditorDialog: Alias for CommentEditorDialog (backward compatibility)
- CommentCardWidget: Individual comment card with time span, excerpt, and action buttons
- CommentsPanel: Collapsible docked Comments Sidebar / Drawer component
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QFrame,
    QLabel,
    QTextEdit,
    QPushButton,
    QToolButton,
    QScrollArea,
    QMessageBox,
)

from core_utils import format_time


class CommentEditorDialog(QDialog):
    """Multi-line document-style comment editor supporting spaces, line breaks, and paragraph breaks."""
    def __init__(self, parent=None, comment_text="", title="Add Comment", prompt="Enter comment details:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        label = QLabel(prompt, self)
        label.setWordWrap(True)
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(label)

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(comment_text)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setPlaceholderText("Type your comment here... (Spaces, tabs, Enter line breaks, and Ctrl+Enter to save supported)")
        self.text_edit.setStyleSheet("font-size: 13px; line-height: 1.5; padding: 6px;")
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ Delete Comment", self)
        self.delete_btn.setStyleSheet("color: #dc2626; font-weight: bold;")
        self.delete_btn.setVisible(bool(comment_text and comment_text.strip()))

        self.save_btn = QPushButton("Save Comment", self)
        self.save_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel", self)

        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.delete_btn.clicked.connect(self._on_delete)
        self._is_deleted = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.accept()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_delete(self):
        self._is_deleted = True
        self.accept()

    def get_comment_text(self):
        if self._is_deleted:
            return ""
        return self.text_edit.toPlainText()

    def get_note_text(self):
        return self.get_comment_text()

    def is_deleted(self):
        return self._is_deleted


# Alias for backward compatibility
NoteEditorDialog = CommentEditorDialog


class CommentCardWidget(QFrame):
    """Card representing a single range-anchored comment in the Comments side panel."""
    editRequested = Signal(int)
    deleteRequested = Signal(int)
    seekRequested = Signal(float, int)

    def __init__(self, seg_idx, start_time, end_time, comment_text, quote_text="", parent=None):
        super().__init__(parent)
        self.seg_idx = seg_idx
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.setObjectName("comment_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        time_str = f"[{format_time(self.start_time)} - {format_time(self.end_time)}]"
        self.time_lbl = QLabel(f"<b>{time_str}</b>", self)
        self.time_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
        header_layout.addWidget(self.time_lbl)
        header_layout.addStretch()

        self.edit_btn = QToolButton(self)
        self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("Edit comment")
        self.edit_btn.setStyleSheet("border: none; padding: 2px;")
        self.edit_btn.clicked.connect(lambda: self.editRequested.emit(self.seg_idx))
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QToolButton(self)
        self.delete_btn.setText("🗑️")
        self.delete_btn.setToolTip("Delete comment")
        self.delete_btn.setStyleSheet("border: none; padding: 2px; color: #ef4444;")
        self.delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.seg_idx))
        header_layout.addWidget(self.delete_btn)
        layout.addLayout(header_layout)

        if quote_text and quote_text.strip():
            esc_q = quote_text.strip()
            if len(esc_q) > 90:
                esc_q = esc_q[:87] + "..."
            self.quote_lbl = QLabel(f'<i>"{esc_q}"</i>', self)
            self.quote_lbl.setWordWrap(True)
            self.quote_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; margin-bottom: 2px;")
            layout.addWidget(self.quote_lbl)

        self.comment_lbl = QLabel(comment_text, self)
        self.comment_lbl.setWordWrap(True)
        self.comment_lbl.setStyleSheet("font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.comment_lbl)

        self.set_selected(False)

    def set_selected(self, is_selected=True, theme="dark"):
        """Apply distinct active/selected visual indication to card."""
        self._is_selected = is_selected
        if is_selected:
            if theme == "light":
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: #fef08a;
                        border: 2px solid #ca8a04;
                        border-left: 6px solid #a16207;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: rgba(250, 204, 21, 0.35);
                        border: 2px solid #f59e0b;
                        border-left: 6px solid #d97706;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                """)
        else:
            if theme == "light":
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: #fef9c3;
                        border: 1px solid #fde047;
                        border-left: 4px solid #eab308;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                    QFrame#comment_card:hover {
                        background-color: #fef08a;
                        border-color: #ca8a04;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame#comment_card {
                        background-color: rgba(254, 240, 138, 0.08);
                        border: 1px solid rgba(234, 179, 8, 0.35);
                        border-left: 4px solid #eab308;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    }
                    QFrame#comment_card:hover {
                        background-color: rgba(254, 240, 138, 0.16);
                        border-color: #eab308;
                    }
                """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.seekRequested.emit(self.start_time, self.seg_idx)
            event.accept()
            return
        super().mousePressEvent(event)


class CommentsPanel(QWidget):
    """Collapsible docked Comments Sidebar / Pane sitting beside the transcript view."""
    commentSeekRequested = Signal(float, int)
    commentEditRequested = Signal(int)
    commentDeleteRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("comments_panel")
        self.setMinimumWidth(220)
        self.setMaximumWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 4)
        self.title_lbl = QLabel("<b>💬 Comments (0)</b>", self)
        self.title_lbl.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        self.add_btn = QToolButton(self)
        self.add_btn.setText("+ Add")
        self.add_btn.setToolTip("Add comment to current transcript selection (Ctrl+M)")
        self.add_btn.setStyleSheet("padding: 2px 6px; font-weight: bold;")
        self.add_btn.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self.add_btn)

        self.close_btn = QToolButton(self)
        self.close_btn.setText("✕")
        self.close_btn.setToolTip("Close Comments Sidebar (Ctrl+Alt+C)")
        self.close_btn.setStyleSheet("border: none; padding: 2px 4px; color: #94a3b8;")
        self.close_btn.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # Scroll area for cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_widget)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # Empty state label
        self.empty_lbl = QLabel(
            "No comments yet.\n\nHighlight text in the transcript and select '💬 Add Comment' to annotate.",
            self
        )
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 24px 12px;")
        main_layout.addWidget(self.empty_lbl)

    def _on_add_clicked(self):
        win = self.window()
        if hasattr(win, "add_comment_from_selection"):
            win.add_comment_from_selection()
        elif hasattr(win, "transcript_view"):
            cursor = win.transcript_view.textCursor()
            seg_idx = win.transcript_view.get_segment_index_at_cursor(cursor)
            if seg_idx is not None and hasattr(win, "edit_segment_comment_dialog"):
                win.edit_segment_comment_dialog(seg_idx)

    def _on_close_clicked(self):
        win = self.window()
        if hasattr(win, "toggle_show_comments"):
            win.toggle_show_comments(False)
        else:
            self.hide()

    def set_comments(self, segments):
        """Populate the comment cards from transcript segments."""
        # Clear existing card widgets
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        comment_count = 0
        if segments:
            for idx, seg in enumerate(segments):
                c_text = seg.get("comments") or seg.get("notes", "")
                if c_text and c_text.strip():
                    comment_count += 1
                    quote = seg.get("comment_selected_text") or seg.get("text", "")
                    card = CommentCardWidget(
                        seg_idx=idx,
                        start_time=seg.get("start", 0.0),
                        end_time=seg.get("end", 0.0),
                        comment_text=c_text.strip(),
                        quote_text=quote,
                        parent=self.scroll_widget
                    )
                    card.seekRequested.connect(self.commentSeekRequested.emit)
                    card.editRequested.connect(self.commentEditRequested.emit)
                    card.deleteRequested.connect(self.commentDeleteRequested.emit)
                    self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self.title_lbl.setText(f"<b>💬 Comments ({comment_count})</b>")
        if comment_count > 0:
            self.empty_lbl.hide()
            self.scroll_area.show()
        else:
            self.empty_lbl.show()
            self.scroll_area.hide()

    def highlight_segment(self, target_seg_idx):
        """Visually flash/highlight a specific comment card."""
        main_win = self.window()
        theme = getattr(main_win, "current_theme", "dark")
        for i in range(self.cards_layout.count() - 1):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), CommentCardWidget):
                card = item.widget()
                is_sel = (target_seg_idx is not None and card.seg_idx == target_seg_idx)
                card.set_selected(is_sel, theme)
                if is_sel:
                    self.scroll_area.ensureWidgetVisible(card)

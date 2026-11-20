"""spellcheck_widgets.py — Inline Qt Spellcheck Highlighting & Context Menu UI.

Provides non-intrusive Tier 1 offline spellcheck presentation for short
editorial metadata widgets (`QLineEdit`, `QTextEdit`, `QPlainTextEdit`, and
`ResizableTextEdit`) such as WordPress Title, Excerpt, Image Caption, Alt Text,
Custom Notice, and Segment Title editors.

Features:
- Red wavy/spellcheck underline on misspelled words (`QSyntaxHighlighter` for
  multi-line text editors; transparent paint overlay for single-line `QLineEdit`).
- Native right-click context menu augmented with bold spelling suggestions,
  "Add '<word>' to Glossary", and "Ignore '<word>' (This Session)".
- Weak-reference attachment registry so adding a word to the Glossary or
  confirming a speaker name refreshes highlights across all open editors.
"""

from __future__ import annotations

import logging
import math
import weakref
from typing import Any, List, Optional, Tuple

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QStyle,
    QStyleOptionFrame,
    QTextEdit,
    QWidget,
)

from spellcheck_helper import (
    OfflineSpellChecker,
    SpellIssue,
    ignore_word_for_session,
)

_logger = logging.getLogger(__name__)
_ACTIVE_CONTROLLERS: "weakref.WeakSet[SpellCheckController]" = weakref.WeakSet()


def _is_real_qt_widget(widget: Any) -> bool:
    """Return True when running under real PySide6 rather than qt_compat mocks."""
    if widget is None:
        return False
    mod_name = getattr(type(widget), "__module__", "")
    return str(mod_name).startswith("PySide6.")


def _spell_underline_color() -> QColor:
    """Select an accessible red underline color for the active application theme."""
    try:
        from core_utils import get_active_theme_mode
        mode = get_active_theme_mode("dark")
    except Exception:
        mode = "dark"
    if mode == "light":
        return QColor("#dc2626")
    if mode == "high_contrast":
        return QColor("#ff5555")
    return QColor("#ef4444")


def _make_misspelled_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    underline_style = getattr(
        QTextCharFormat.UnderlineStyle,
        "SpellCheckUnderline",
        getattr(QTextCharFormat.UnderlineStyle, "WaveUnderline", 1),
    )
    fmt.setUnderlineStyle(underline_style)
    fmt.setUnderlineColor(_spell_underline_color())
    return fmt


def add_word_to_glossary(word: str, main_window: Any = None) -> bool:
    """Persist `word` to the application's custom Glossary and refresh spellcheckers."""
    cleaned = str(word or "").strip().strip(".,!?;:()[]{}\"'“”‘’")
    if not cleaned:
        return False

    persisted = False
    if main_window is not None:
        if hasattr(main_window, "add_to_glossary") and callable(main_window.add_to_glossary):
            try:
                main_window.add_to_glossary(cleaned)
                persisted = True
            except Exception:
                persisted = False

        if not persisted:
            try:
                from terminology import parse_glossary, expand_glossary_rules
                entries = parse_glossary(getattr(main_window, "glossary", []))
                existing_sources = {
                    str(r.get("source", "")).casefold()
                    for r in expand_glossary_rules(entries)
                    if isinstance(r, dict)
                }
                existing_prefs = {
                    str(e.get("preferred", "")).casefold()
                    for e in entries
                    if isinstance(e, dict)
                }
                if cleaned.casefold() not in existing_sources and cleaned.casefold() not in existing_prefs:
                    entries.append({
                        "source": cleaned,
                        "preferred": cleaned,
                        "do_not_translate": True,
                        "match_case": False,
                    })
                    main_window.glossary = parse_glossary(entries)
                if hasattr(main_window, "_save_glossary") and callable(main_window._save_glossary):
                    main_window._save_glossary()
                if hasattr(main_window, "apply_glossary_to_whisper_context") and callable(main_window.apply_glossary_to_whisper_context):
                    main_window.apply_glossary_to_whisper_context()
                persisted = True
            except Exception:
                persisted = False

    # Only fall back to process-wide session ignore when no Glossary persistence exists
    if not persisted:
        ignore_word_for_session(cleaned)
    refresh_all_spellcheckers(
        main_window=main_window,
        added_word=None if persisted else cleaned,
    )
    return persisted or True


class SpellCheckHighlighter(QSyntaxHighlighter):
    """QSyntaxHighlighter drawing red spellcheck underlines in QTextEdit / QPlainTextEdit."""

    def __init__(self, document: Any, spellchecker: OfflineSpellChecker):
        super().__init__(document)
        self.spellchecker = spellchecker
        self._format = _make_misspelled_char_format()

    def refresh_format(self) -> None:
        self._format = _make_misspelled_char_format()

    def highlightBlock(self, text: str) -> None:
        if not text:
            return
        for issue in self.spellchecker.find_misspelled_spans(text):
            length = max(0, issue.end - issue.start)
            if length > 0:
                self.setFormat(issue.start, length, self._format)


class _LineEditSpellOverlay(QWidget):
    """Mouse-transparent overlay painting wavy red underlines onto a QLineEdit."""

    def __init__(self, line_edit: QLineEdit, controller: "SpellCheckController"):
        super().__init__(line_edit)
        self._line_edit = line_edit
        self._controller = controller
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setGeometry(line_edit.rect())
        self.show()

    def paintEvent(self, event: Any) -> None:
        le = self._line_edit
        if le is None or not le.isVisible():
            return
        try:
            if le.echoMode() != QLineEdit.EchoMode.Normal:
                return
        except Exception:
            return

        text = le.text()
        if not text:
            return

        issues = self._controller.get_issues()
        if not issues:
            return

        opt = QStyleOptionFrame()
        le.initStyleOption(opt)
        contents = le.style().subElementRect(QStyle.SubElement.SE_LineEditContents, opt, le)
        margins = le.textMargins()
        contents = contents.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        if contents.width() <= 4 or contents.height() <= 4:
            return

        fm = QFontMetrics(le.font())
        # Account for internal horizontal padding (Qt adds ~2px horizontal margin inside contents)
        inner_left = contents.left() + 2
        total_w = fm.horizontalAdvance(text)
        scroll_offset = 0
        if total_w > contents.width() - 4:
            cursor_x = fm.horizontalAdvance(text[: le.cursorPosition()])
            if cursor_x > contents.width() - 8:
                scroll_offset = cursor_x - (contents.width() - 8)

        baseline_y = contents.top() + (contents.height() + fm.ascent() - fm.descent()) / 2.0 + 2.0
        baseline_y = min(float(contents.bottom() - 1), baseline_y)

        painter = QPainter(self)
        try:
            painter.setClipRect(contents)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(_spell_underline_color(), 1.25)
            painter.setPen(pen)

            for issue in issues:
                x1 = inner_left + fm.horizontalAdvance(text[: issue.start]) - scroll_offset
                x2 = inner_left + fm.horizontalAdvance(text[: issue.end]) - scroll_offset
                if x2 <= contents.left() or x1 >= contents.right():
                    continue
                x1 = max(float(contents.left()), float(x1))
                x2 = min(float(contents.right()), float(x2))
                if x2 - x1 < 2.0:
                    continue

                path = QPainterPath()
                step = 3.0
                amp = 1.2
                path.moveTo(x1, baseline_y)
                x = x1
                idx = 0
                while x < x2:
                    nx = min(x + step, x2)
                    ny = baseline_y + (amp if (idx % 2 == 0) else -amp)
                    path.lineTo(nx, ny)
                    x = nx
                    idx += 1
                painter.drawPath(path)
        finally:
            painter.end()


class SpellCheckController(QObject):
    """Coordinates inline spellcheck highlighting and context menus on a text widget."""

    def __init__(
        self,
        widget: Any,
        main_window: Any = None,
        spellchecker: Optional[OfflineSpellChecker] = None,
    ):
        super().__init__(widget if _is_real_qt_widget(widget) else None)
        self.widget = widget
        self.main_window = main_window
        self.spellchecker = spellchecker or OfflineSpellChecker(main_window=main_window)
        self.highlighter: Optional[SpellCheckHighlighter] = None
        self._overlay: Optional[_LineEditSpellOverlay] = None
        self._is_line_edit = self._detect_line_edit(widget)
        self._cached_issues: List[SpellIssue] = []

        self._install()
        _ACTIVE_CONTROLLERS.add(self)

    @staticmethod
    def _detect_line_edit(widget: Any) -> bool:
        if isinstance(widget, QLineEdit):
            return True
        return hasattr(widget, "text") and not hasattr(widget, "toPlainText")

    def _install(self) -> None:
        w = self.widget
        if w is None:
            return

        if self._is_line_edit:
            if _is_real_qt_widget(w):
                self._overlay = _LineEditSpellOverlay(w, self)
                w.installEventFilter(self)
            if hasattr(w, "textChanged"):
                try:
                    w.textChanged.connect(self._on_line_edit_changed)
                except Exception:
                    pass
            if hasattr(w, "cursorPositionChanged"):
                try:
                    w.cursorPositionChanged.connect(self._on_line_edit_cursor_changed)
                except Exception:
                    pass
            self._recompute_line_edit_issues()
        else:
            if _is_real_qt_widget(w) and hasattr(w, "document"):
                self.highlighter = SpellCheckHighlighter(w.document(), self.spellchecker)

        if hasattr(w, "setContextMenuPolicy") and hasattr(w, "customContextMenuRequested"):
            try:
                w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                w.customContextMenuRequested.connect(self._on_context_menu_requested)
            except Exception:
                pass

    def eventFilter(self, obj: Any, event: Any) -> bool:
        if obj is self.widget and self._overlay is not None and event is not None:
            try:
                etype = event.type()
                if etype in (QEvent.Type.Resize, QEvent.Type.FontChange, QEvent.Type.Show):
                    self._overlay.setGeometry(self.widget.rect())
                    self._overlay.update()
            except Exception:
                pass
        return False

    def _on_line_edit_changed(self, *_args: Any) -> None:
        self._recompute_line_edit_issues()
        if self._overlay is not None:
            self._overlay.update()

    def _on_line_edit_cursor_changed(self, *_args: Any) -> None:
        if self._overlay is not None:
            self._overlay.update()

    def _recompute_line_edit_issues(self) -> List[SpellIssue]:
        text = self._get_widget_text()
        self._cached_issues = self.spellchecker.find_misspelled_spans(text)
        return self._cached_issues

    def _get_widget_text(self) -> str:
        w = self.widget
        if w is None:
            return ""
        if self._is_line_edit:
            return str(w.text() if hasattr(w, "text") else "")
        if hasattr(w, "toPlainText"):
            return str(w.toPlainText())
        if hasattr(w, "text"):
            return str(w.text())
        return ""

    def get_issues(self) -> List[SpellIssue]:
        """Return current misspelled `SpellIssue` spans for the attached widget."""
        return self.spellchecker.find_misspelled_spans(self._get_widget_text())

    def refresh(self, main_window: Any = None, added_word: Optional[str] = None) -> None:
        """Refresh allowlist from Glossary/speakers and re-run inline highlighting."""
        if added_word:
            self.spellchecker.add_words([added_word])
        win = main_window if main_window is not None else self.main_window
        if win is not None:
            self.spellchecker.refresh_from_window(win)

        if self._is_line_edit:
            self._recompute_line_edit_issues()
            if self._overlay is not None:
                self._overlay.update()
        elif self.highlighter is not None:
            try:
                self.highlighter.refresh_format()
                self.highlighter.rehighlight()
            except Exception:
                pass

    def apply_suggestion(self, issue: SpellIssue, replacement: str, block_offset: int = 0) -> bool:
        """Replace the misspelled `issue` span with `replacement` in the attached widget."""
        w = self.widget
        if w is None or issue is None:
            return False

        abs_start = block_offset + issue.start
        abs_end = block_offset + issue.end

        if self._is_line_edit:
            text = self._get_widget_text()
            if abs_start < 0 or abs_end > len(text):
                return False
            if _is_real_qt_widget(w) and hasattr(w, "setSelection") and hasattr(w, "insert"):
                # Preserve native QLineEdit Undo stack (Ctrl+Z) and fire native textEdited/textChanged
                w.setSelection(abs_start, abs_end - abs_start)
                w.insert(replacement)
            else:
                new_text = text[:abs_start] + replacement + text[abs_end:]
                if hasattr(w, "setText"):
                    w.setText(new_text)
                if hasattr(w, "setCursorPosition"):
                    try:
                        w.setCursorPosition(abs_start + len(replacement))
                    except Exception:
                        pass
                # Emit textEdited so listeners like _on_title_edited stay synchronized
                if hasattr(w, "textEdited") and hasattr(w.textEdited, "emit"):
                    try:
                        w.textEdited.emit(new_text)
                    except Exception:
                        pass
            self._recompute_line_edit_issues()
            if self._overlay is not None:
                self._overlay.update()
            return True

        # Multi-line QTextEdit / QPlainTextEdit: use QTextCursor to preserve native Undo stack
        if _is_real_qt_widget(w) and hasattr(w, "textCursor"):
            cursor = w.textCursor()
            cursor.setPosition(abs_start)
            cursor.setPosition(abs_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.beginEditBlock()
            cursor.insertText(replacement)
            cursor.endEditBlock()
            w.setTextCursor(cursor)
            return True

        # Headless fallback for DummyQTextEdit
        text = self._get_widget_text()
        if abs_start < 0 or abs_end > len(text):
            return False
        new_text = text[:abs_start] + replacement + text[abs_end:]
        if hasattr(w, "setPlainText"):
            w.setPlainText(new_text)
        elif hasattr(w, "setText"):
            w.setText(new_text)
        return True

    def _locate_issue_at_point(self, pos: QPoint) -> Tuple[Optional[SpellIssue], int]:
        """Return `(SpellIssue, block_start_offset)` for a widget-local click position."""
        w = self.widget
        if w is None:
            return None, 0

        if self._is_line_edit:
            try:
                char_idx = int(w.cursorPositionAt(pos))
            except Exception:
                char_idx = 0
            issue = self.spellchecker.find_issue_at(self._get_widget_text(), char_idx)
            return issue, 0

        if _is_real_qt_widget(w) and hasattr(w, "cursorForPosition"):
            cursor = w.cursorForPosition(pos)
            block = cursor.block()
            block_text = block.text()
            pos_in_block = cursor.positionInBlock()
            issue = self.spellchecker.find_issue_at(block_text, pos_in_block)
            return issue, block.position()

        return None, 0

    def _on_context_menu_requested(self, pos: QPoint) -> None:
        w = self.widget
        if w is None or not _is_real_qt_widget(w):
            return

        # Refresh allowlist lazily right before showing context menu
        if self.main_window is not None:
            self.spellchecker.refresh_from_window(self.main_window)

        menu = w.createStandardContextMenu() if hasattr(w, "createStandardContextMenu") else QMenu(w)
        issue, block_offset = self._locate_issue_at_point(pos)

        if issue is not None:
            first_action = menu.actions()[0] if menu.actions() else None
            suggestions = self.spellchecker.get_suggestions(issue.word, max_suggestions=5)

            bold_font = QFont(menu.font())
            bold_font.setBold(True)

            if suggestions:
                for cand in suggestions:
                    act = QAction(cand, menu)
                    act.setFont(bold_font)
                    act.triggered.connect(
                        lambda _checked=False, iss=issue, rep=cand, off=block_offset: self.apply_suggestion(iss, rep, off)
                    )
                    menu.insertAction(first_action, act)
            else:
                no_sug = QAction("No spelling suggestions", menu)
                no_sug.setEnabled(False)
                menu.insertAction(first_action, no_sug)

            menu.insertSeparator(first_action)

            add_act = QAction(f'Add "{issue.word}" to Glossary', menu)
            add_act.triggered.connect(
                lambda _checked=False, word=issue.word: add_word_to_glossary(word, self.main_window)
            )
            menu.insertAction(first_action, add_act)

            ignore_act = QAction(f'Ignore "{issue.word}" (This Session)', menu)
            ignore_act.triggered.connect(
                lambda _checked=False, word=issue.word: self.ignore_word(word)
            )
            menu.insertAction(first_action, ignore_act)

            menu.insertSeparator(first_action)

        global_pos = w.mapToGlobal(pos) if hasattr(w, "mapToGlobal") else pos
        menu.exec(global_pos)

    def ignore_word(self, word: str) -> None:
        """Ignore `word` for the remainder of the session and refresh all editors."""
        ignore_word_for_session(word)
        refresh_all_spellcheckers(main_window=self.main_window, added_word=word)


def attach_spellcheck(
    widget: Any,
    main_window: Any = None,
    spellchecker: Optional[OfflineSpellChecker] = None,
) -> Optional[SpellCheckController]:
    """Attach Tier 1 offline spellchecking to a QLineEdit, QTextEdit, QPlainTextEdit,
    or ResizableTextEdit widget.

    Idempotent: calling again on an already-attached widget refreshes and returns
    its existing `SpellCheckController`.
    """
    if widget is None:
        return None

    # Unwrap ResizableTextEdit wrapper to its inner QTextEdit without triggering DynamicMock.__getattr__
    target = widget
    widget_dict = getattr(widget, "__dict__", {})
    inner = widget_dict.get("text_edit") if isinstance(widget_dict, dict) else None
    if inner is not None and (isinstance(inner, (QTextEdit, QPlainTextEdit)) or hasattr(inner, "toPlainText")):
        target = inner

    target_dict = getattr(target, "__dict__", {})
    existing = target_dict.get("_spellcheck_controller") if isinstance(target_dict, dict) else None
    if isinstance(existing, SpellCheckController):
        if main_window is not None and existing.main_window is None:
            existing.main_window = main_window
        existing.refresh(main_window=main_window)
        return existing

    controller = SpellCheckController(
        target,
        main_window=main_window,
        spellchecker=spellchecker,
    )
    try:
        target._spellcheck_controller = controller
        if target is not widget:
            widget._spellcheck_controller = controller
    except Exception:
        pass
    return controller


def refresh_all_spellcheckers(main_window: Any = None, added_word: Optional[str] = None) -> None:
    """Re-sync Glossary/speaker allowlists and re-highlight every attached editor."""
    for controller in list(_ACTIVE_CONTROLLERS):
        try:
            controller.refresh(main_window=main_window, added_word=added_word)
        except Exception:
            _logger.warning("Failed to refresh spellcheck controller", exc_info=True)


__all__ = [
    "SpellCheckHighlighter",
    "SpellCheckController",
    "attach_spellcheck",
    "refresh_all_spellcheckers",
    "add_word_to_glossary",
]

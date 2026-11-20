"""speaker_name_cleanup_dialog.py — Modal review dialog for bulk speaker/guest name cleanup."""
from __future__ import annotations

import os
from typing import Any, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

from core_utils import make_dialog_maximizable
from speaker_name_matcher import (
    SpeakerNameCandidate,
    apply_bulk_text_replacements,
    extract_confirmed_speaker_names,
    find_misspelled_speaker_names,
)

__all__ = ["SpeakerNameCleanupDialog"]


class SpeakerNameCleanupDialog(QDialog):
    """Review and apply misspelled guest/host name fixes against confirmed speakers."""

    def __init__(self, main_win: Any, parent: Optional[QWidget] = None):
        qparent = parent if (isinstance(parent, QWidget) or hasattr(parent, "winId")) else (
            main_win if isinstance(main_win, QWidget) else None
        )
        super().__init__(qparent)
        self.main_win = main_win
        self.setWindowTitle("Fix Misspelled Speaker Names")
        self.setMinimumSize(780, 460)
        make_dialog_maximizable(self)

        self._candidates: List[SpeakerNameCandidate] = []
        self._row_checkboxes: List[QCheckBox] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.info_label = QLabel("", self)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Apply",
            "Found in Transcript",
            "Replace With",
            "Count",
            "Sample Context",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 65)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

        opts_row = QHBoxLayout()
        self.chk_preserve_case = QCheckBox("Preserve Case (e.g. IFE -> IFFY)", self)
        self.chk_preserve_case.setChecked(True)
        opts_row.addWidget(self.chk_preserve_case)

        self.chk_save_glossary = QCheckBox("Also save applied corrections to Glossary", self)
        self.chk_save_glossary.setChecked(True)
        opts_row.addWidget(self.chk_save_glossary)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All", self)
        self.btn_select_all.clicked.connect(lambda: self._set_all_checked(True))
        btn_row.addWidget(self.btn_select_all)

        self.btn_clear_all = QPushButton("Clear All", self)
        self.btn_clear_all.clicked.connect(lambda: self._set_all_checked(False))
        btn_row.addWidget(self.btn_clear_all)

        self.btn_rescan = QPushButton("Rescan", self)
        self.btn_rescan.clicked.connect(self.rescan)
        btn_row.addWidget(self.btn_rescan)

        btn_row.addStretch()

        self.btn_apply = QPushButton("Apply Selected", self)
        self.btn_apply.setDefault(True)
        self.btn_apply.clicked.connect(self._apply_selected)
        btn_row.addWidget(self.btn_apply)

        self.btn_close = QPushButton("Close", self)
        self.btn_close.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        self.rescan()

    def _set_all_checked(self, checked: bool) -> None:
        for cb in self._row_checkboxes:
            cb.setChecked(checked)

    def rescan(self) -> None:
        self._row_checkboxes.clear()
        self.table.setRowCount(0)

        confirmed = extract_confirmed_speaker_names(self.main_win)
        transcript = getattr(self.main_win, "transcript", None)
        segments = transcript.get("segments", []) if isinstance(transcript, dict) else []

        if not confirmed:
            self.info_label.setText(
                "No named speakers found yet. Rename speakers from generic labels (e.g. Speaker 1) "
                "first so the scanner knows which names to check."
            )
            self._candidates = []
            self.status_label.setText("0 possible misspellings found.")
            self.btn_apply.setEnabled(False)
            return

        shown_names = ", ".join(confirmed[:6])
        if len(confirmed) > 6:
            shown_names += f", ... (+{len(confirmed) - 6} more)"
        self.info_label.setText(
            f"Scanning transcript against confirmed speakers: {shown_names}. "
            "Review suggested fixes below (you can double-click 'Replace With' to edit before applying)."
        )

        self._candidates = find_misspelled_speaker_names(segments, confirmed)
        self.table.setRowCount(len(self._candidates))
        for row, cand in enumerate(self._candidates):
            self.table.setRowHeight(row, 34)

            cb_wrap = QWidget(self.table)
            cb_lay = QHBoxLayout(cb_wrap)
            cb_lay.setContentsMargins(0, 0, 0, 0)
            cb_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb = QCheckBox(cb_wrap)
            cb.setChecked(cand.score >= 0.80 or cand.match_kind == "full_name")
            cb_lay.addWidget(cb)
            self._row_checkboxes.append(cb)
            self.table.setCellWidget(row, 0, cb_wrap)

            found_item = QTableWidgetItem(cand.found_text)
            found_item.setFlags(found_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, found_item)

            repl_item = QTableWidgetItem(cand.suggested_name)
            repl_item.setFlags(
                repl_item.flags()
                | Qt.ItemFlag.ItemIsEditable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            self.table.setItem(row, 2, repl_item)

            cnt_item = QTableWidgetItem(str(cand.count))
            cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cnt_item.setFlags(cnt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, cnt_item)

            ctx_item = QTableWidgetItem(cand.sample_context)
            ctx_item.setFlags(ctx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            ctx_item.setToolTip(cand.sample_context)
            self.table.setItem(row, 4, ctx_item)

        self.btn_apply.setEnabled(bool(self._candidates))
        if self._candidates:
            total_occ = sum(c.count for c in self._candidates)
            self.status_label.setText(
                f"Found {len(self._candidates)} candidate spelling(s) ({total_occ} total occurrence(s))."
            )
        else:
            self.status_label.setText("No probable speaker-name misspellings found.")

    def _apply_selected(self) -> int:
        if not self.main_win or not isinstance(getattr(self.main_win, "transcript", None), dict):
            return 0

        pairs: List[Tuple[str, str]] = []
        for row, cb in enumerate(self._row_checkboxes):
            if not cb.isChecked():
                continue
            found_item = self.table.item(row, 1)
            repl_item = self.table.item(row, 2)
            found_txt = found_item.text().strip() if found_item else ""
            repl_txt = repl_item.text().strip() if repl_item else ""
            if found_txt and repl_txt and found_txt != repl_txt:
                pairs.append((found_txt, repl_txt))

        if not pairs:
            self.status_label.setText("No checked replacements selected.")
            return 0

        if hasattr(self.main_win, "flush_pending_transcript_undo"):
            self.main_win.flush_pending_transcript_undo()
        before_state = self.main_win._capture_project_state() if hasattr(self.main_win, "_capture_project_state") else None

        segments = self.main_win.transcript.get("segments", [])
        total_replaced, mod_segs = apply_bulk_text_replacements(
            segments=segments,
            replacements=pairs,
            preserve_case=self.chk_preserve_case.isChecked(),
            sync_words_cb=getattr(self.main_win, "sync_segment_words", None),
            transcript=self.main_win.transcript,
            translations=getattr(self.main_win, "translations", None),
        )

        glossary_added = 0
        if total_replaced > 0 and self.chk_save_glossary.isChecked():
            try:
                from terminology import add_alternate_spelling
                entries = getattr(self.main_win, "glossary", [])
                for found_txt, repl_txt in pairs:
                    entries = add_alternate_spelling(
                        entries,
                        preferred_term=repl_txt,
                        alternate_spelling=found_txt,
                    )
                    glossary_added += 1
                self.main_win.glossary = entries
                if hasattr(self.main_win, "_save_glossary"):
                    self.main_win._save_glossary()
                if hasattr(self.main_win, "apply_glossary_to_whisper_context"):
                    self.main_win.apply_glossary_to_whisper_context()
            except Exception:
                pass

        if total_replaced > 0:
            desc = f"Fix Speaker Names ({total_replaced} replacements)"
            if before_state is not None and hasattr(self.main_win, "_commit_project_state_change"):
                self.main_win._commit_project_state_change(before_state, desc)
            if hasattr(self.main_win, "mark_project_dirty"):
                self.main_win.mark_project_dirty(desc)
            if hasattr(self.main_win, "render_transcript"):
                self.main_win.render_transcript()
            if hasattr(self.main_win, "schedule_project_save"):
                self.main_win.schedule_project_save()
            elif hasattr(self.main_win, "save_project"):
                self.main_win.save_project()

            self.rescan()
            msg = f"Applied {total_replaced} replacement(s) across {mod_segs} segment(s)."
            if glossary_added:
                msg += f" Saved {glossary_added} mapping(s) to Glossary."
            self.status_label.setText(msg)
            if os.environ.get("RTVS_TEST_MODE") != "1":
                try:
                    QMessageBox.information(self, "Speaker Name Cleanup", msg)
                except Exception:
                    pass
        else:
            self.status_label.setText("No matching text needed replacement.")

        return total_replaced

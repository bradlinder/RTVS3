"""Checkable story/segment selection sidebar for UnifiedExportDialog.

Displayed when Export Scope is set to 'Selected Stories / Segments' so users can
choose which segments to export directly inside the Export Dialog across all
destinations (Local Files, WordPress, Timeline/DAW, and YouTube).
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except Exception:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from prs_shared import format_time, get_story_vocabulary


class ExportStorySelectorSidebar(QWidget):
    """Left sidebar with checkable story/segment items and quick Select All / Clear controls."""

    selection_changed = Signal(list)  # sorted List[int] of checked 0-based story indices
    story_activated = Signal(int)     # 0-based story index clicked/focused by the user

    def __init__(self, main_window: Any = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = main_window
        self._syncing = False
        self._stories_count = 0

        self.setObjectName("export_story_selector_sidebar")
        self.setMinimumWidth(185)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)

        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(2, 0, 2, 0)
        hdr_row.setSpacing(6)

        vocab = get_story_vocabulary(self.main_window)
        self.title_label = QLabel(f"<b>{vocab.plural} to Export:</b>")
        self.count_label = QLabel("(0 of 0)")
        self.count_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        hdr_row.addWidget(self.title_label)
        hdr_row.addStretch()
        hdr_row.addWidget(self.count_label)
        layout.addLayout(hdr_row)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        self.select_all_btn.clicked.connect(self.select_all)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        self.clear_btn.clicked.connect(self.clear_selection)

        btn_row.addWidget(self.select_all_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.story_list = QListWidget()
        self.story_list.setObjectName("export_story_selector_list")
        self.story_list.setMinimumWidth(175)
        self.story_list.itemChanged.connect(self._on_item_changed)
        self.story_list.currentRowChanged.connect(self._on_current_row_changed)
        layout.addWidget(self.story_list, 1)

    def populate(self, stories: List[Any], selected_indices: Iterable[int]) -> None:
        """Rebuild the checkable list from project stories and active selection indices."""
        vocab = get_story_vocabulary(self.main_window)
        self.title_label.setText(f"<b>{vocab.plural} to Export:</b>")

        valid_sel = {int(i) for i in (selected_indices or []) if 0 <= int(i) < len(stories)}
        prev_row = self.story_list.currentRow()

        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            self.story_list.clear()
            self._stories_count = len(stories)
            for idx, st in enumerate(stories):
                raw_title = str(getattr(st, "title", "") or "").strip()
                st_start = getattr(st, "start", None)
                st_end = getattr(st, "end", None)
                time_suffix = ""
                if st_start is not None and st_end is not None:
                    try:
                        time_suffix = f" ({format_time(float(st_start))} - {format_time(float(st_end))})"
                    except Exception:
                        time_suffix = ""

                prefix = f"{vocab.singular} {idx + 1}"
                if raw_title and raw_title.lower() != prefix.lower():
                    label = f"{prefix}: {raw_title}"
                else:
                    label = prefix

                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, idx)
                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                item.setCheckState(Qt.CheckState.Checked if idx in valid_sel else Qt.CheckState.Unchecked)
                item.setToolTip(f"{label}{time_suffix}")
                self.story_list.addItem(item)

            if self.story_list.count() > 0:
                if 0 <= prev_row < self.story_list.count():
                    self.story_list.setCurrentRow(prev_row)
                elif valid_sel:
                    self.story_list.setCurrentRow(min(valid_sel))
                else:
                    self.story_list.setCurrentRow(0)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False

        self.update_count_label()

    def get_selected_indices(self) -> List[int]:
        """Return sorted 0-based indices of all checked story items."""
        indices: List[int] = []
        for row in range(self.story_list.count()):
            item = self.story_list.item(row)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                idx = item.data(Qt.ItemDataRole.UserRole)
                indices.append(int(idx) if idx is not None else row)
        return sorted(set(indices))

    def set_selected_indices(self, selected_indices: Iterable[int], emit: bool = False) -> None:
        """Update item check states without rebuilding the list."""
        target = {int(i) for i in (selected_indices or [])}
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            for row in range(self.story_list.count()):
                item = self.story_list.item(row)
                if item is None:
                    continue
                idx = item.data(Qt.ItemDataRole.UserRole)
                idx_int = int(idx) if idx is not None else row
                item.setCheckState(Qt.CheckState.Checked if idx_int in target else Qt.CheckState.Unchecked)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False
        self.update_count_label()
        if emit:
            self.selection_changed.emit(self.get_selected_indices())

    def select_all(self) -> None:
        self.set_selected_indices(range(self.story_list.count()), emit=True)

    def clear_selection(self) -> None:
        self.set_selected_indices([], emit=True)

    def update_count_label(self) -> None:
        checked = len(self.get_selected_indices())
        total = self.story_list.count()
        self.count_label.setText(f"({checked} of {total})")

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._syncing:
            return
        self.update_count_label()
        self.selection_changed.emit(self.get_selected_indices())
        if item is not None and item.checkState() == Qt.CheckState.Checked:
            idx = item.data(Qt.ItemDataRole.UserRole)
            if idx is not None:
                self.story_activated.emit(int(idx))

    def _on_current_row_changed(self, row: int) -> None:
        if self._syncing or row < 0 or row >= self.story_list.count():
            return
        item = self.story_list.item(row)
        if item is None:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.story_activated.emit(int(idx) if idx is not None else row)


__all__ = ["ExportStorySelectorSidebar"]

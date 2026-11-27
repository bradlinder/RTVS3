"""Checkable story/segment selection sidebar for UnifiedExportDialog.

Displayed when Export Scope is set to 'Selected Stories / Segments' so users can
choose which segments to export directly inside the Export Dialog across all
destinations (Local Files, WordPress, Timeline/DAW, and YouTube).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QBrush, QColor
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
    from PySide6.QtGui import QBrush, QColor
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from pathlib import Path
from prs_shared import format_time, get_story_vocabulary

FULL_EPISODE_ROLE_VALUE = -1
_BASE_LABEL_ROLE = int(Qt.ItemDataRole.UserRole) + 1
_BASE_TOOLTIP_ROLE = int(Qt.ItemDataRole.UserRole) + 2
_UNCHECKED_MUTED_COLOR = QColor("#64748b")


class ExportStorySelectorSidebar(QWidget):
    """Left sidebar with checkable Full Episode and story/segment items plus Select All / Clear."""

    selection_changed = Signal(list)   # sorted List[int] of checked 0-based story indices
    full_episode_toggled = Signal(bool)  # True when the Full Episode item is checked
    story_activated = Signal(int)      # 0-based story index or FULL_EPISODE_ROLE_VALUE (-1)

    def __init__(self, main_window: Any = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = main_window
        self._syncing = False
        self._stories_count = 0
        self._include_full_episode = False
        self._decorations: Dict[int, Tuple[str, str]] = {}

        self.setObjectName("export_story_selector_sidebar")
        self.setMinimumWidth(185)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)

        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(2, 0, 2, 0)
        hdr_row.setSpacing(6)

        self.title_label = QLabel("<b>Items to Export:</b>")
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
        self.story_list.itemClicked.connect(self._on_item_clicked)
        self.story_list.currentRowChanged.connect(self._on_current_row_changed)
        layout.addWidget(self.story_list, 1)

    def _resolve_full_episode_title(self) -> str:
        proj_meta = getattr(self.main_window, "project_metadata", None)
        if isinstance(proj_meta, dict):
            wp_meta = proj_meta.get("wordpress")
            if isinstance(wp_meta, dict) and str(wp_meta.get("title") or "").strip():
                return str(wp_meta.get("title")).strip()
            if str(proj_meta.get("title") or "").strip():
                return str(proj_meta.get("title")).strip()
        audio_file = getattr(self.main_window, "audio_file", None)
        if audio_file:
            return Path(str(audio_file)).stem
        return ""

    def populate(
        self,
        stories: List[Any],
        selected_indices: Iterable[int],
        include_full_episode: Optional[bool] = None,
    ) -> None:
        """Rebuild the checkable list with Full Episode at top followed by project stories."""
        vocab = get_story_vocabulary(self.main_window)
        self.title_label.setText("<b>Items to Export:</b>")

        if include_full_episode is not None:
            self._include_full_episode = bool(include_full_episode)

        valid_sel = {int(i) for i in (selected_indices or []) if 0 <= int(i) < len(stories)}
        prev_row = self.story_list.currentRow()

        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            self.story_list.clear()
            self._stories_count = len(stories)

            # Row 0: Checkable Full Episode option
            ep_title = self._resolve_full_episode_title()
            full_label = f"Full Episode: {ep_title}" if ep_title else "Full Episode"
            full_item = QListWidgetItem(full_label)
            full_item.setData(Qt.ItemDataRole.UserRole, FULL_EPISODE_ROLE_VALUE)
            full_tooltip = (
                f"{full_label}\nCheck to include the Full Episode alongside selected {vocab.plural.lower()}."
            )
            full_item.setData(_BASE_LABEL_ROLE, full_label)
            full_item.setData(_BASE_TOOLTIP_ROLE, full_tooltip)
            font = full_item.font()
            font.setBold(True)
            full_item.setFont(font)
            full_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            full_item.setCheckState(
                Qt.CheckState.Checked if self._include_full_episode else Qt.CheckState.Unchecked
            )
            self._apply_item_visual_state(full_item)
            self.story_list.addItem(full_item)

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
                item.setData(_BASE_LABEL_ROLE, label)
                item.setData(_BASE_TOOLTIP_ROLE, f"{label}{time_suffix}")
                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                item.setCheckState(Qt.CheckState.Checked if idx in valid_sel else Qt.CheckState.Unchecked)
                self._apply_item_visual_state(item)
                self.story_list.addItem(item)

            if self.story_list.count() > 0:
                if 0 <= prev_row < self.story_list.count():
                    self.story_list.setCurrentRow(prev_row)
                elif self._include_full_episode:
                    self.story_list.setCurrentRow(0)
                elif valid_sel:
                    self.story_list.setCurrentRow(min(valid_sel) + 1)
                else:
                    self.story_list.setCurrentRow(0)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False

        self.update_count_label()

    def is_full_episode_included(self) -> bool:
        """Return True if the Full Episode row is checked."""
        if self.story_list.count() > 0:
            first = self.story_list.item(0)
            if first is not None and first.data(Qt.ItemDataRole.UserRole) == FULL_EPISODE_ROLE_VALUE:
                return first.checkState() == Qt.CheckState.Checked
        return bool(self._include_full_episode)

    def _apply_item_visual_state(self, item: Optional[QListWidgetItem]) -> None:
        """Apply destination badges/tooltips to checked rows and visually mute unchecked rows."""
        if item is None:
            return
        role_val = item.data(Qt.ItemDataRole.UserRole)
        base_label = item.data(_BASE_LABEL_ROLE)
        if base_label is None:
            base_label = item.text()
        base_tooltip = item.data(_BASE_TOOLTIP_ROLE)
        if base_tooltip is None:
            base_tooltip = item.toolTip()

        checked = item.checkState() == Qt.CheckState.Checked
        dec = self._decorations.get(int(role_val)) if (checked and role_val is not None) else None
        if dec:
            dec_label, dec_tooltip = dec
            item.setText(str(dec_label or base_label))
            item.setToolTip(str(dec_tooltip or base_tooltip))
        else:
            item.setText(str(base_label))
            item.setToolTip(str(base_tooltip))

        if checked:
            item.setData(Qt.ItemDataRole.ForegroundRole, None)
        else:
            item.setForeground(QBrush(_UNCHECKED_MUTED_COLOR))

    def set_item_decorations(self, decorations: Optional[Dict[int, Tuple[str, str]]]) -> None:
        """Apply destination-specific (label, tooltip) overrides onto checked sidebar rows."""
        normalized: Dict[int, Tuple[str, str]] = {}
        for k, v in (decorations or {}).items():
            try:
                if isinstance(v, (tuple, list)) and len(v) >= 2:
                    normalized[int(k)] = (str(v[0] or ""), str(v[1] or ""))
            except Exception:
                continue
        self._decorations = normalized
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            for row in range(self.story_list.count()):
                self._apply_item_visual_state(self.story_list.item(row))
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False

    def clear_item_decorations(self) -> None:
        """Clear destination-specific badges/tooltips and restore default labels."""
        if self._decorations:
            self.set_item_decorations({})

    def set_include_full_episode(self, checked: bool, emit: bool = False) -> None:
        """Programmatically check or uncheck the Full Episode row."""
        self._include_full_episode = bool(checked)
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            if self.story_list.count() > 0:
                first = self.story_list.item(0)
                if first is not None and first.data(Qt.ItemDataRole.UserRole) == FULL_EPISODE_ROLE_VALUE:
                    first.setCheckState(
                        Qt.CheckState.Checked if self._include_full_episode else Qt.CheckState.Unchecked
                    )
                    self._apply_item_visual_state(first)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False
        self.update_count_label()
        if emit:
            self.full_episode_toggled.emit(self._include_full_episode)

    def get_selected_indices(self) -> List[int]:
        """Return sorted 0-based indices of all checked story items (excluding Full Episode)."""
        indices: List[int] = []
        for row in range(self.story_list.count()):
            item = self.story_list.item(row)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                idx = item.data(Qt.ItemDataRole.UserRole)
                if idx is not None and int(idx) >= 0:
                    indices.append(int(idx))
        return sorted(set(indices))

    def has_any_selection(self) -> bool:
        """Return True if Full Episode or at least one story/segment is checked."""
        return self.is_full_episode_included() or bool(self.get_selected_indices())

    def set_selected_indices(self, selected_indices: Iterable[int], emit: bool = False) -> None:
        """Update story item check states without altering the Full Episode item."""
        target = {int(i) for i in (selected_indices or []) if int(i) >= 0}
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            for row in range(self.story_list.count()):
                item = self.story_list.item(row)
                if item is None:
                    continue
                idx = item.data(Qt.ItemDataRole.UserRole)
                if idx is None or int(idx) < 0:
                    continue
                item.setCheckState(Qt.CheckState.Checked if int(idx) in target else Qt.CheckState.Unchecked)
                self._apply_item_visual_state(item)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False
        self.update_count_label()
        if emit:
            self.selection_changed.emit(self.get_selected_indices())

    def select_all(self) -> None:
        self.set_include_full_episode(True, emit=False)
        self.set_selected_indices(range(self._stories_count), emit=False)
        self.full_episode_toggled.emit(True)
        self.selection_changed.emit(self.get_selected_indices())

    def clear_selection(self) -> None:
        self.set_include_full_episode(False, emit=False)
        self.set_selected_indices([], emit=False)
        self.full_episode_toggled.emit(False)
        self.selection_changed.emit([])

    def update_count_label(self) -> None:
        checked = len(self.get_selected_indices()) + (1 if self.is_full_episode_included() else 0)
        total = self.story_list.count()
        self.count_label.setText(f"({checked} of {total})")

    def _sync_current_item_quietly(self, item: QListWidgetItem) -> None:
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            self.story_list.setCurrentItem(item)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._syncing or item is None:
            return
        role_val = item.data(Qt.ItemDataRole.UserRole)
        self._syncing = True
        self.story_list.blockSignals(True)
        try:
            self._apply_item_visual_state(item)
        finally:
            self.story_list.blockSignals(False)
            self._syncing = False
        self.update_count_label()
        if role_val == FULL_EPISODE_ROLE_VALUE:
            checked = item.checkState() == Qt.CheckState.Checked
            self._include_full_episode = checked
            self.full_episode_toggled.emit(checked)
            if checked:
                self._sync_current_item_quietly(item)
                self.story_activated.emit(FULL_EPISODE_ROLE_VALUE)
            return
        self.selection_changed.emit(self.get_selected_indices())
        if item.checkState() == Qt.CheckState.Checked and role_val is not None:
            self._sync_current_item_quietly(item)
            self.story_activated.emit(int(role_val))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        if self._syncing or item is None:
            return
        role_val = item.data(Qt.ItemDataRole.UserRole)
        if role_val is not None:
            self.story_activated.emit(int(role_val))

    def _on_current_row_changed(self, row: int) -> None:
        if self._syncing or row < 0 or row >= self.story_list.count():
            return
        item = self.story_list.item(row)
        if item is None:
            return
        role_val = item.data(Qt.ItemDataRole.UserRole)
        if role_val is not None:
            self.story_activated.emit(int(role_val))


__all__ = ["ExportStorySelectorSidebar", "FULL_EPISODE_ROLE_VALUE"]

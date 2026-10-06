"""export/reorder_dialog.py — Dialog for customizing the display order of export destinations."""
from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import INTERNAL_APP_ID
from core_utils import apply_window_titlebar_theme, get_active_theme_mode, make_dialog_maximizable

DEFAULT_EXPORT_DESTINATIONS_ORDER = ["local", "wordpress", "gdocs", "youtube"]


def _get_export_theme_mode() -> str:
    """Retrieve active theme mode ('light', 'dark', or 'high_contrast')."""
    return get_active_theme_mode("dark")


def get_export_destinations_order() -> List[str]:
    """Retrieve user-configured export destination ordering."""
    if not QSettings:
        return list(DEFAULT_EXPORT_DESTINATIONS_ORDER)
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    raw = settings.value("export_destinations_order", None)
    if raw:
        if isinstance(raw, list):
            return [str(x) for x in raw]
        elif isinstance(raw, str):
            return [x.strip() for x in raw.split(",") if x.strip()]
    return list(DEFAULT_EXPORT_DESTINATIONS_ORDER)


def save_export_destinations_order(order: List[str]) -> None:
    """Persist user-configured export destination ordering."""
    if not QSettings:
        return
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    settings.setValue("export_destinations_order", order)


class ReorderExportDestinationsDialog(QDialog):
    """Dialog allowing the user to reorder export destinations via drag-and-drop or Move Up/Down."""

    def __init__(self, parent: Optional[QWidget] = None, available_dests: Optional[List[Tuple[str, str]]] = None):
        super().__init__(parent)
        self.setWindowTitle("Customize Export Destinations Order")
        self.resize(460, 360)
        self.setMinimumSize(400, 300)
        make_dialog_maximizable(self)
        apply_window_titlebar_theme(self)

        # available_dests is a list of (dest_id, dest_title)
        self.available_dests = available_dests or [
            ("local", "Local Files (Media & Transcripts)"),
            ("wordpress", "WordPress Draft Post"),
            ("gdocs", "Google Docs"),
            ("youtube", "YouTube Studio (Assisted Upload)"),
        ]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        theme_mode = _get_export_theme_mode()

        info_lbl = QLabel(
            "Drag and drop destinations to customize their display order in the Export window, "
            "or use the <b>Move Up</b> / <b>Move Down</b> buttons:"
        )
        info_lbl.setWordWrap(True)
        if theme_mode == "light":
            info_lbl.setStyleSheet("color: #545b66; font-size: 12px;")
        elif theme_mode == "high_contrast":
            info_lbl.setStyleSheet("color: #ffffff; font-size: 12px;")
        else:
            info_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(info_lbl)

        content_row = QHBoxLayout()
        self.list_widget = QListWidget(self)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        if theme_mode == "light":
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #eaedf0;
                    border: 1px solid #b6bcc4;
                    border-radius: 6px;
                    padding: 4px;
                    color: #22262c;
                    font-size: 13px;
                }
                QListWidget::item {
                    padding: 8px 10px;
                    border-bottom: 1px solid #d0d4d9;
                    border-radius: 4px;
                    margin-bottom: 2px;
                    color: #22262c;
                }
                QListWidget::item:selected {
                    background-color: #2e74b5;
                    color: #ffffff;
                    font-weight: bold;
                }
            """)
        elif theme_mode == "high_contrast":
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #000000;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 4px;
                    color: #ffffff;
                    font-size: 13px;
                }
                QListWidget::item {
                    padding: 8px 10px;
                    border-bottom: 1px solid #ffffff;
                    border-radius: 4px;
                    margin-bottom: 2px;
                    color: #ffffff;
                }
                QListWidget::item:selected {
                    background-color: #ffffff;
                    color: #000000;
                    font-weight: bold;
                }
            """)
        else:
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 4px;
                    color: #f8fafc;
                    font-size: 13px;
                }
                QListWidget::item {
                    padding: 8px 10px;
                    border-bottom: 1px solid #334155;
                    border-radius: 4px;
                    margin-bottom: 2px;
                }
                QListWidget::item:selected {
                    background-color: #0284c7;
                    color: #ffffff;
                    font-weight: bold;
                }
            """)

        # Populate according to current saved order
        current_order = get_export_destinations_order()
        dest_map = {d_id: title for d_id, title in self.available_dests}

        # First add items in current_order
        added_ids = set()
        for d_id in current_order:
            if d_id in dest_map:
                item = QListWidgetItem(f"☰  {dest_map[d_id]}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)
                added_ids.add(d_id)

        # Then add any missing available destinations
        for d_id, title in self.available_dests:
            if d_id not in added_ids:
                item = QListWidgetItem(f"☰  {title}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)

        content_row.addWidget(self.list_widget, 1)

        # Buttons on the right: Move Up, Move Down, Reset
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)

        self.up_btn = QPushButton("▲ Move Up")
        self.up_btn.clicked.connect(self._move_up)
        btn_col.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼ Move Down")
        self.down_btn.clicked.connect(self._move_down)
        btn_col.addWidget(self.down_btn)

        btn_col.addSpacing(10)
        self.reset_btn = QPushButton("Reset Default")
        self.reset_btn.setToolTip("Reset order to: Local, WordPress, Google Docs, YouTube Studio")
        self.reset_btn.clicked.connect(self._reset_default)
        btn_col.addWidget(self.reset_btn)

        btn_col.addStretch()
        content_row.addLayout(btn_col)
        layout.addLayout(content_row)

        # Dialog buttons (Save Order, Cancel)
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.ok_btn = QPushButton("Save Order")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._save_and_accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.ok_btn)
        btn_box.addWidget(self.cancel_btn)
        layout.addLayout(btn_box)

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row >= 0 and row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _reset_default(self):
        self.list_widget.clear()
        dest_map = {d_id: title for d_id, title in self.available_dests}
        for d_id in DEFAULT_EXPORT_DESTINATIONS_ORDER:
            if d_id in dest_map:
                item = QListWidgetItem(f"☰  {dest_map[d_id]}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)
        for d_id, title in self.available_dests:
            if d_id not in DEFAULT_EXPORT_DESTINATIONS_ORDER:
                item = QListWidgetItem(f"☰  {title}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)

    def _save_and_accept(self):
        order = []
        for i in range(self.list_widget.count()):
            d_id = self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            if d_id:
                order.append(str(d_id))
        save_export_destinations_order(order)
        self.accept()

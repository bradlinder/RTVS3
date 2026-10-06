"""shortcuts/dialogs.py — Preferences page for keyboard shortcuts configuration."""
from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from shortcuts.manager import ShortcutsManager
from shortcuts.schema import (
    _get_shortcuts_theme_mode,
    format_sequence_display,
    normalize_sequence_string,
)
from shortcuts.widgets import KeySequenceRecorderEdit


class KeyboardShortcutsPage(QWidget):
    """Preferences page that provides a searchable table of all customizable shortcuts,
    an interactive recorder, conflict resolution, and reset controls."""

    def __init__(self, shortcuts_manager: ShortcutsManager, parent_window=None, parent=None):
        super().__init__(parent)
        self.mgr = shortcuts_manager
        self.parent_window = parent_window
        # Working copy of shortcuts so changes can be cancelled or applied
        self.pending_shortcuts: Dict[str, str] = {}
        for defn in self.mgr.get_definitions():
            self.pending_shortcuts[defn.action_id] = self.mgr.get_current_shortcut(defn.action_id)

        self.selected_action_id: Optional[str] = None
        self._sort_column = 0  # 0 = Action (Alphabetical default), 1 = Category
        self._sort_order = Qt.SortOrder.AscendingOrder

        self._init_ui()
        self._populate_table()
        self._sort_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header description
        desc_lbl = QLabel(
            "<b>Customize Keyboard Shortcuts</b><br>"
            "<span style='color: #64748b; font-size: 12px;'>"
            "Select any menu action, playback command, or navigation tool to assign a custom shortcut key. "
            "Conflicts are flagged in real-time, and you can restore system defaults at any time.</span>"
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Search & Category Filter Toolbar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        search_lbl = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by action name, shortcut, or category...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_table)
        filter_bar.addWidget(search_lbl)
        filter_bar.addWidget(self.search_input, 2)

        cat_lbl = QLabel("Category:")
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All Categories", "all")
        categories = sorted(list({d.category for d in self.mgr.get_definitions()}))
        for c in categories:
            self.cat_combo.addItem(c, c)
        self.cat_combo.currentIndexChanged.connect(self._filter_table)
        filter_bar.addWidget(cat_lbl)
        filter_bar.addWidget(self.cat_combo, 1)

        # Arrange / Sort Tab Toggle Buttons
        sort_lbl = QLabel("Arrange By:")
        self.btn_sort_action = QPushButton("Action (Alphabetical)")
        self.btn_sort_action.setCheckable(True)
        self.btn_sort_action.setChecked(True)
        self.btn_sort_action.setToolTip("Arrange shortcuts alphabetically by Action Name (A-Z)")
        self.btn_sort_action.clicked.connect(self._sort_by_action_name)

        self.btn_sort_category = QPushButton("Category")
        self.btn_sort_category.setCheckable(True)
        self.btn_sort_category.setChecked(False)
        self.btn_sort_category.setToolTip("Arrange shortcuts grouped by functional Category")
        self.btn_sort_category.clicked.connect(self._sort_by_category)

        filter_bar.addWidget(sort_lbl)
        filter_bar.addWidget(self.btn_sort_action)
        filter_bar.addWidget(self.btn_sort_category)

        layout.addLayout(filter_bar)

        # Shortcut Lookup Tool (Lookup assigned command for any key combination)
        self.lookup_matched_action_id: Optional[str] = None
        self.lookup_group = QGroupBox("🔍 Shortcut Lookup Tool (Find Bound Action)")
        lookup_layout = QVBoxLayout(self.lookup_group)
        lookup_layout.setSpacing(6)

        lookup_input_row = QHBoxLayout()
        lookup_input_row.setSpacing(8)

        self.lookup_edit = KeySequenceRecorderEdit(self)
        self.lookup_edit.setToolTip("Click and press any key combination to look up what action it triggers")
        self.lookup_edit.keySequenceChanged.connect(self._on_lookup_sequence_changed)
        lookup_input_row.addWidget(self.lookup_edit, 2)

        self.lookup_clear_btn = QPushButton("Clear Lookup")
        self.lookup_clear_btn.setToolTip("Clear lookup input")
        self.lookup_clear_btn.clicked.connect(self._clear_lookup)
        lookup_input_row.addWidget(self.lookup_clear_btn)

        lookup_layout.addLayout(lookup_input_row)

        # Lookup Result Card
        self.lookup_result_card = QFrame()
        tm = _get_shortcuts_theme_mode()
        if tm == "light":
            self.lookup_result_card.setStyleSheet(
                "QFrame { background-color: #eaedf0; border: 1px solid #b6bcc4; border-radius: 4px; padding: 6px 10px; }"
            )
        elif tm == "high_contrast":
            self.lookup_result_card.setStyleSheet(
                "QFrame { background-color: #000000; border: 1px solid #ffffff; border-radius: 4px; padding: 6px 10px; }"
            )
        else:
            self.lookup_result_card.setStyleSheet(
                "QFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 4px; padding: 6px 10px; }"
            )
        lookup_res_layout = QHBoxLayout(self.lookup_result_card)
        lookup_res_layout.setContentsMargins(6, 4, 6, 4)

        self.lookup_result_lbl = QLabel("Click the box above and press any key combination to look up its assigned function.")
        if tm == "light":
            self.lookup_result_lbl.setStyleSheet("color: #545b66; font-size: 12px;")
        elif tm == "high_contrast":
            self.lookup_result_lbl.setStyleSheet("color: #ffffff; font-size: 12px;")
        else:
            self.lookup_result_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        self.lookup_result_lbl.setWordWrap(True)
        lookup_res_layout.addWidget(self.lookup_result_lbl, 1)

        self.lookup_jump_btn = QPushButton("📍 Select in Table")
        self.lookup_jump_btn.setStyleSheet(
            "QPushButton { background-color: #0284c7; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background-color: #0369a1; }"
        )
        self.lookup_jump_btn.setVisible(False)
        self.lookup_jump_btn.clicked.connect(self._on_lookup_jump_clicked)
        lookup_res_layout.addWidget(self.lookup_jump_btn)

        lookup_layout.addWidget(self.lookup_result_card)
        layout.addWidget(self.lookup_group)

        # Main Shortcuts Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Action", "Category", "Current Shortcut", "Default", "Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._on_header_section_clicked)

        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.table.itemDoubleClicked.connect(lambda item: self.recorder_edit.start_recording() if not self.recorder_edit.is_recording else None)
        layout.addWidget(self.table, 1)

        # Editor Group Box
        self.edit_group = QGroupBox("Edit Selected Shortcut")
        edit_layout = QVBoxLayout(self.edit_group)
        edit_layout.setSpacing(8)

        action_info_layout = QHBoxLayout()
        self.selected_name_lbl = QLabel("<b>Select an action above to modify its shortcut</b>")
        self.selected_desc_lbl = QLabel("")
        self.selected_desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        self.selected_desc_lbl.setWordWrap(True)
        action_info_layout.addWidget(self.selected_name_lbl, 1)
        edit_layout.addLayout(action_info_layout)
        edit_layout.addWidget(self.selected_desc_lbl)

        recorder_row = QHBoxLayout()
        recorder_row.setSpacing(8)

        self.recorder_edit = KeySequenceRecorderEdit(self)
        self.recorder_edit.keySequenceChanged.connect(self._on_new_sequence_recorded)
        self.recorder_edit.setEnabled(False)
        recorder_row.addWidget(self.recorder_edit, 2)

        self.record_btn = QPushButton("Record Keys")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self.recorder_edit.start_recording)
        recorder_row.addWidget(self.record_btn)

        self.clear_btn = QPushButton("Clear (None)")
        self.clear_btn.setEnabled(False)
        self.clear_btn.setToolTip("Disable shortcut for selected action")
        self.clear_btn.clicked.connect(lambda: self._apply_pending_change(self.selected_action_id, "None"))
        recorder_row.addWidget(self.clear_btn)

        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.setEnabled(False)
        self.reset_btn.setToolTip("Restore factory default shortcut for this action")
        self.reset_btn.clicked.connect(self._reset_selected_to_default)
        recorder_row.addWidget(self.reset_btn)

        edit_layout.addLayout(recorder_row)

        # Conflict Warning Box
        self.conflict_frame = QFrame()
        self.conflict_frame.setStyleSheet(
            "QFrame { background-color: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 4px; padding: 6px; }"
        )
        conflict_layout = QHBoxLayout(self.conflict_frame)
        conflict_layout.setContentsMargins(6, 4, 6, 4)

        self.conflict_lbl = QLabel("")
        self.conflict_lbl.setStyleSheet("color: #ef4444; font-size: 12px;")
        self.conflict_lbl.setWordWrap(True)
        conflict_layout.addWidget(self.conflict_lbl, 1)

        self.reassign_btn = QPushButton("Reassign to This Action")
        self.reassign_btn.setStyleSheet(
            "QPushButton { background-color: #ef4444; color: white; font-weight: bold; border-radius: 3px; padding: 4px 8px; }"
            "QPushButton:hover { background-color: #dc2626; }"
        )
        self.reassign_btn.clicked.connect(self._reassign_conflict)
        conflict_layout.addWidget(self.reassign_btn)

        self.conflict_frame.setVisible(False)
        edit_layout.addWidget(self.conflict_frame)

        layout.addWidget(self.edit_group)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        self.reset_all_btn = QPushButton("Reset All to Defaults")
        self.reset_all_btn.setToolTip("Restore all keyboard shortcuts across the application to factory defaults")
        self.reset_all_btn.clicked.connect(self._confirm_reset_all)
        bottom_bar.addWidget(self.reset_all_btn)

        bottom_bar.addStretch()

        self.save_btn = QPushButton("Apply & Save Shortcuts")
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: white; font-weight: bold; border-radius: 4px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        self.save_btn.clicked.connect(self._on_save_clicked)
        bottom_bar.addWidget(self.save_btn)

        layout.addLayout(bottom_bar)

    def _sort_by_action_name(self):
        """Arrange table alphabetically by Action Name (Column 0)."""
        self.btn_sort_action.setChecked(True)
        self.btn_sort_category.setChecked(False)
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._sort_table()

    def _sort_by_category(self):
        """Arrange table grouped by Category (Column 1)."""
        self.btn_sort_category.setChecked(True)
        self.btn_sort_action.setChecked(False)
        self._sort_column = 1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._sort_table()

    def _on_header_section_clicked(self, logical_index: int):
        """Handle header column click to sort and update arrange toggle buttons."""
        if logical_index == 0:
            self.btn_sort_action.setChecked(True)
            self.btn_sort_category.setChecked(False)
        elif logical_index == 1:
            self.btn_sort_category.setChecked(True)
            self.btn_sort_action.setChecked(False)
        else:
            self.btn_sort_action.setChecked(False)
            self.btn_sort_category.setChecked(False)

        if self._sort_column == logical_index:
            self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            self._sort_column = logical_index
            self._sort_order = Qt.SortOrder.AscendingOrder
        self._sort_table()

    def _sort_table(self):
        """Sort table rows by active sort column and order."""
        self.table.sortItems(self._sort_column, self._sort_order)
        self.table.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    def _on_lookup_sequence_changed(self, candidate_seq: str):
        """Lookup action bound to candidate key sequence and update UI card."""
        if not candidate_seq or candidate_seq in ("None", "<none>", ""):
            self._clear_lookup()
            return

        norm_candidate = normalize_sequence_string(candidate_seq).lower()
        matched_defn = None

        for defn in self.mgr.get_definitions():
            cur = self.pending_shortcuts.get(defn.action_id, self.mgr.get_default_shortcut(defn.action_id))
            if not cur or cur in ("None", "<none>"):
                continue
            if normalize_sequence_string(cur).lower() == norm_candidate:
                matched_defn = defn
                break

        disp_str = format_sequence_display(candidate_seq)
        tm = _get_shortcuts_theme_mode()

        if matched_defn:
            self.lookup_matched_action_id = matched_defn.action_id
            if tm == "light":
                self.lookup_result_lbl.setText(
                    f"✅ '<b>{disp_str}</b>' triggers: <b>{matched_defn.name}</b> "
                    f"(<span style='color: #2e74b5;'>{matched_defn.category}</span>)<br>"
                    f"<span style='color: #545b66; font-size: 11px;'>{matched_defn.description}</span>"
                )
            elif tm == "high_contrast":
                self.lookup_result_lbl.setText(
                    f"✅ '<b>{disp_str}</b>' triggers: <b>{matched_defn.name}</b> "
                    f"(<span style='color: #ffff00;'>{matched_defn.category}</span>)<br>"
                    f"<span style='color: #ffffff; font-size: 11px;'>{matched_defn.description}</span>"
                )
            else:
                self.lookup_result_lbl.setText(
                    f"✅ '<b>{disp_str}</b>' triggers: <b>{matched_defn.name}</b> "
                    f"(<span style='color: #38bdf8;'>{matched_defn.category}</span>)<br>"
                    f"<span style='color: #94a3b8; font-size: 11px;'>{matched_defn.description}</span>"
                )
            self.lookup_jump_btn.setVisible(True)
        else:
            self.lookup_matched_action_id = None
            if tm == "light":
                self.lookup_result_lbl.setText(
                    f"ℹ️ '<b>{disp_str}</b>' is <b>Unassigned</b> (Available for binding)."
                )
            elif tm == "high_contrast":
                self.lookup_result_lbl.setText(
                    f"ℹ️ '<b>{disp_str}</b>' is <b>Unassigned</b> (Available for binding)."
                )
            else:
                self.lookup_result_lbl.setText(
                    f"ℹ️ '<b>{disp_str}</b>' is <b>Unassigned</b> (Available for binding)."
                )
            self.lookup_jump_btn.setVisible(False)

    def _clear_lookup(self):
        """Reset lookup tool state."""
        self.lookup_edit.set_sequence("")
        self.lookup_matched_action_id = None
        self.lookup_jump_btn.setVisible(False)
        self.lookup_result_lbl.setText("Click the box above and press any key combination to look up its assigned function.")

    def _on_lookup_jump_clicked(self):
        """Scroll to and select the matched action in the table."""
        if not self.lookup_matched_action_id:
            return

        # Clear active filter to ensure matched row is visible
        if self.search_input.text() or self.cat_combo.currentIndex() > 0:
            self.search_input.clear()
            self.cat_combo.setCurrentIndex(0)

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == self.lookup_matched_action_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                break

    def _populate_table(self):
        definitions = self.mgr.get_definitions()
        self.table.setRowCount(len(definitions))

        for row, defn in enumerate(definitions):
            # Column 0: Action Name
            name_item = QTableWidgetItem(defn.name)
            name_item.setData(Qt.ItemDataRole.UserRole, defn.action_id)
            name_item.setToolTip(defn.description or defn.name)
            self.table.setItem(row, 0, name_item)

            # Column 1: Category
            cat_item = QTableWidgetItem(defn.category)
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, cat_item)

            # Column 2: Current Shortcut
            cur_seq = self.pending_shortcuts.get(defn.action_id, "")
            cur_disp = format_sequence_display(cur_seq)
            cur_item = QTableWidgetItem(cur_disp)
            cur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = cur_item.font()
            font.setBold(True)
            cur_item.setFont(font)
            self.table.setItem(row, 2, cur_item)

            # Column 3: Default Shortcut
            def_seq = self.mgr.get_default_shortcut(defn.action_id)
            def_disp = format_sequence_display(def_seq)
            def_item = QTableWidgetItem(def_disp)
            def_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            def_item.setForeground(QColor("#64748b"))
            self.table.setItem(row, 3, def_item)

            # Column 4: Status
            status_item = QTableWidgetItem()
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_status_item(status_item, defn.action_id)
            self.table.setItem(row, 4, status_item)

    def _update_status_item(self, item: QTableWidgetItem, action_id: str):
        cur = normalize_sequence_string(self.pending_shortcuts.get(action_id, ""))
        default_seq = normalize_sequence_string(self.mgr.get_default_shortcut(action_id))
        tm = _get_shortcuts_theme_mode()

        if cur == "None" or (not cur and default_seq):
            item.setText("Disabled")
            if tm == "light":
                item.setForeground(QColor("#94a3b8"))
            elif tm == "high_contrast":
                item.setForeground(QColor("#ffffff"))
            else:
                item.setForeground(QColor("#64748b"))
        elif cur != default_seq:
            item.setText("Customized")
            if tm == "light":
                item.setForeground(QColor("#2e74b5"))
            elif tm == "high_contrast":
                item.setForeground(QColor("#ffff00"))
            else:
                item.setForeground(QColor("#38bdf8"))
        else:
            item.setText("Default")
            if tm == "light":
                item.setForeground(QColor("#16a34a"))
            elif tm == "high_contrast":
                item.setForeground(QColor("#00ff00"))
            else:
                item.setForeground(QColor("#22c55e"))

    def _filter_table(self):
        query = self.search_input.text().strip().lower()
        selected_cat = self.cat_combo.currentData()

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            cat_item = self.table.item(row, 1)
            cur_item = self.table.item(row, 2)

            if not name_item or not cat_item:
                continue

            name_text = name_item.text().lower()
            cat_text = cat_item.text()
            cur_text = cur_item.text().lower() if cur_item else ""

            match_cat = (selected_cat == "all" or cat_text == selected_cat)
            match_query = (not query or query in name_text or query in cat_text.lower() or query in cur_text)

            self.table.setRowHidden(row, not (match_cat and match_query))

    def _on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            self.selected_action_id = None
            self.selected_name_lbl.setText("<b>Select an action above to modify its shortcut</b>")
            self.selected_desc_lbl.setText("")
            self.recorder_edit.setEnabled(False)
            self.recorder_edit.set_sequence("")
            self.record_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.conflict_frame.setVisible(False)
            return

        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        action_id = name_item.data(Qt.ItemDataRole.UserRole)
        defn = self.mgr.get_definition(action_id)

        if not defn:
            return

        self.selected_action_id = action_id
        self.selected_name_lbl.setText(f"<b>{defn.name}</b> ({defn.category})")
        self.selected_desc_lbl.setText(defn.description or "")

        cur_seq = self.pending_shortcuts.get(action_id, self.mgr.get_default_shortcut(action_id))
        self.recorder_edit.setEnabled(True)
        self.recorder_edit.set_sequence(cur_seq)
        self.record_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)

        self._check_conflict(cur_seq, excluding_action_id=action_id)

    def _on_new_sequence_recorded(self, new_seq: str):
        if not self.selected_action_id:
            return
        self._apply_pending_change(self.selected_action_id, new_seq)

    def _reset_selected_to_default(self):
        if not self.selected_action_id:
            return
        default_seq = self.mgr.get_default_shortcut(self.selected_action_id)
        self._apply_pending_change(self.selected_action_id, default_seq)

    def _apply_pending_change(self, action_id: str, new_seq: str):
        self.pending_shortcuts[action_id] = new_seq
        self.recorder_edit.set_sequence(new_seq)

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == action_id:
                cur_item = self.table.item(row, 2)
                if cur_item:
                    cur_item.setText(format_sequence_display(new_seq))
                status_item = self.table.item(row, 4)
                if status_item:
                    self._update_status_item(status_item, action_id)
                break

        self._check_conflict(new_seq, excluding_action_id=action_id)

    def _check_conflict(self, candidate_seq: str, excluding_action_id: str):
        if not candidate_seq or candidate_seq in ("None", "<none>", ""):
            self.conflict_frame.setVisible(False)
            return

        norm_candidate = normalize_sequence_string(candidate_seq).lower()
        conflicting_defn = None

        for defn in self.mgr.get_definitions():
            if defn.action_id == excluding_action_id:
                continue
            cur = self.pending_shortcuts.get(defn.action_id, self.mgr.get_default_shortcut(defn.action_id))
            if not cur or cur in ("None", "<none>"):
                continue
            if normalize_sequence_string(cur).lower() == norm_candidate:
                conflicting_defn = defn
                break

        if conflicting_defn:
            self.conflict_lbl.setText(
                f"⚠️ <b>Conflict Detected:</b> '<b>{format_sequence_display(candidate_seq)}</b>' "
                f"is currently assigned to '<b>{conflicting_defn.name}</b>' ({conflicting_defn.category})."
            )
            self.conflicting_action_id = conflicting_defn.action_id
            self.conflict_frame.setVisible(True)
        else:
            self.conflict_frame.setVisible(False)

    def _reassign_conflict(self):
        """Remove shortcut from conflicting action and assign to current selected action."""
        if hasattr(self, "conflicting_action_id") and self.conflicting_action_id:
            # Clear shortcut on conflicting action
            self._apply_pending_change(self.conflicting_action_id, "None")
            self.conflict_frame.setVisible(False)

    def _confirm_reset_all(self):
        reply = QMessageBox.question(
            self,
            "Reset All Shortcuts",
            "Are you sure you want to reset ALL keyboard shortcuts to their factory defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.pending_shortcuts.clear()
            for defn in self.mgr.get_definitions():
                self.pending_shortcuts[defn.action_id] = self.mgr.get_default_shortcut(defn.action_id)
            self._populate_table()
            self._on_row_selected()

    def _on_save_clicked(self):
        self.save_shortcuts()
        QMessageBox.information(
            self,
            "Shortcuts Applied",
            "Keyboard shortcuts have been saved and applied successfully.",
            QMessageBox.StandardButton.Ok,
        )

    def save_shortcuts(self):
        """Commit all pending shortcut changes to QSettings and apply to the MainWindow."""
        for action_id, seq in self.pending_shortcuts.items():
            self.mgr.set_shortcut(action_id, seq)
        self.mgr.save()
        if self.parent_window:
            self.mgr.apply_to_window(self.parent_window)

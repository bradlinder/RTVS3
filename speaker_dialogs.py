"""speaker_dialogs.py — Dialogs for speaker renaming, turn assignment, and cluster management."""
from __future__ import annotations

import html
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QWidget,
    QCheckBox, QAbstractItemView, QMessageBox, QFrame, QLineEdit, QInputDialog,
    QApplication
)

from prs_shared import format_time, parse_time, INTERNAL_APP_ID
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode

__all__ = ["ChangeSpeakerDialog", "SpeakerManagerDialog"]

class ChangeSpeakerDialog(QDialog):
    """Dialog prompting whether to apply a speaker name change to all instances or a single turn."""

    def __init__(self, current_name: str, target_name: str, seg_idx: int = -1, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Speaker")
        self.setMinimumWidth(520)
        make_dialog_maximizable(self)
        self.choice = None  # 'all', 'single', or None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        prompt_lbl = QLabel(
            f"Change <b>'{html.escape(current_name)}'</b> to <b>'{html.escape(target_name)}'</b> for:",
            self,
        )
        prompt_lbl.setWordWrap(True)
        prompt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(prompt_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_all = QPushButton("All Instances", self)
        self.btn_all.setDefault(True)
        self.btn_all.setMinimumHeight(36)
        self.btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_all.setToolTip("Apply this name change to every occurrence of this speaker across the entire project")
        self.btn_all.clicked.connect(self._on_all)
        btn_layout.addWidget(self.btn_all, 1)

        self.btn_single = QPushButton("This Instance Only", self)
        self.btn_single.setMinimumHeight(36)
        self.btn_single.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_single.setToolTip("Apply this name change strictly to this instance (contiguous speaker turn)")
        self.btn_single.clicked.connect(self._on_single)
        btn_layout.addWidget(self.btn_single, 1)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setMinimumHeight(36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel, 1)

        layout.addLayout(btn_layout)
        self.adjustSize()

    def _on_all(self):
        self.choice = "all"
        self.accept()

    def _on_subsequent(self):
        self.choice = "subsequent"
        self.accept()

    def _on_single(self):
        self.choice = "single"
        self.accept()




class SpeakerManagerDialog(QDialog):
    """Manager dialog for inspecting, aliasing, and merging detected speaker clusters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_win = parent
        self.setWindowTitle("Manage Speakers & Detection Clusters")
        self.resize(800, 500)
        self.setMinimumSize(760, 460)
        make_dialog_maximizable(self)
        self._init_ui()
        self._populate()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            "<b>Speakers & Detection Clusters</b><br>"
            "Inspect all detected speaker clusters, rename / assign global aliases, or merge redundant clusters."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Speaker Name / Alias", "Cluster / Raw ID", "Turns", "Total Duration", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 240)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.merge_all_btn = QPushButton("Merge Two Speakers...", self)
        self.merge_all_btn.clicked.connect(self._on_quick_merge)
        btn_row.addWidget(self.merge_all_btn)
        btn_row.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _populate(self):
        self.table.setRowCount(0)
        if not self.main_win or not getattr(self.main_win, "transcript", None):
            return

        segments = self.main_win.transcript.get("segments", [])
        speaker_stats = {}

        for idx, seg in enumerate(segments):
            name = self.main_win.get_effective_speaker_name(idx, seg) or "Unknown Speaker"
            raw = str(self.main_win.segment_speaker_overrides.get(idx) or seg.get("speaker") or name)
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            dur = max(0.0, end - start)

            if name not in speaker_stats:
                speaker_stats[name] = {"raw": raw, "turns": 0, "duration": 0.0}
            speaker_stats[name]["turns"] += 1
            speaker_stats[name]["duration"] += dur

        self.table.setRowCount(len(speaker_stats))
        for row, (name, info) in enumerate(sorted(speaker_stats.items(), key=lambda x: -x[1]["duration"])):
            self.table.setRowHeight(row, 46)

            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)

            raw_item = QTableWidgetItem(info["raw"])
            raw_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, raw_item)

            turns_item = QTableWidgetItem(str(info["turns"]))
            turns_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, turns_item)

            dur_item = QTableWidgetItem(format_time(info["duration"]))
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, dur_item)

            action_widget = QWidget(self)
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 4, 6, 4)
            action_layout.setSpacing(8)

            btn_style = """
                QPushButton {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    border: 1px solid #475569;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 26px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    border-color: #38bdf8;
                    color: #38bdf8;
                }
                QPushButton:pressed {
                    background-color: #0f172a;
                }
            """

            rename_btn = QPushButton("Rename / Alias", action_widget)
            rename_btn.setStyleSheet(btn_style)
            rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rename_btn.clicked.connect(lambda _, n=name, r=info["raw"]: self._rename_speaker(n, r))
            action_layout.addWidget(rename_btn)

            merge_btn = QPushButton("Merge Into...", action_widget)
            merge_btn.setStyleSheet(btn_style)
            merge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            merge_btn.clicked.connect(lambda _, n=name: self._merge_speaker_into(n))
            action_layout.addWidget(merge_btn)

            self.table.setCellWidget(row, 4, action_widget)

    def _rename_speaker(self, current_name, raw_id):
        new_name, accepted = QInputDialog.getText(
            self, "Rename Speaker Alias",
            f"Enter new display alias for '{current_name}':",
            QLineEdit.EchoMode.Normal, current_name
        )
        if accepted and new_name.strip() and new_name.strip() != current_name:
            target = new_name.strip()
            self.main_win.speaker_names[str(raw_id)] = target
            self.main_win.speaker_names[current_name] = target
            self.main_win.add_custom_speaker_to_glossary(target)

            segments = self.main_win.transcript.get("segments", [])
            for idx, seg in enumerate(segments):
                if self.main_win.get_effective_speaker_name(idx, seg) == current_name:
                    override_key = f"SEG_{idx}_SPEAKER"
                    self.main_win.speaker_names[override_key] = target
                    self.main_win.segment_speaker_overrides[idx] = override_key

            self.main_win.render_transcript()
            self.main_win.save_project()
            self._populate()

    def _merge_speaker_into(self, source_name):
        known = [s for s in self.main_win.get_all_known_speakers() if s != source_name]
        if not known:
            QMessageBox.information(self, "Merge Speakers", "No other speakers available to merge into.")
            return

        target, accepted = QInputDialog.getItem(
            self, "Merge Speaker",
            f"Merge all turns from '{source_name}' into which speaker?",
            known, 0, False
        )
        if accepted and target:
            confirm = QMessageBox.question(
                self, "Confirm Merge",
                f"Are you sure you want to merge all occurrences of '{source_name}' into '{target}'?\n\n"
                f"This will reassign all segments and diarization tracks across the entire timeline.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.main_win.merge_speakers(source_name, target)
                self._populate()

    def _on_quick_merge(self):
        known = self.main_win.get_all_known_speakers()
        if len(known) < 2:
            QMessageBox.information(self, "Merge Speakers", "At least two distinct speakers are required to merge.")
            return

        source, ok1 = QInputDialog.getItem(
            self, "Merge Speakers", "Select Source Speaker to merge (will be replaced):", known, 0, False
        )
        if not ok1 or not source:
            return

        candidates = [s for s in known if s != source]
        target, ok2 = QInputDialog.getItem(
            self, "Merge Speakers", f"Select Target Speaker (to receive '{source}'):", candidates, 0, False
        )
        if not ok2 or not target:
            return

        self.main_win.merge_speakers(source, target)
        self._populate()

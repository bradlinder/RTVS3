"""Radio & TV Segmenter v3.7.4-beta — transcript story responsibilities.

Methods intentionally retain the MainWindow-facing API so behavior remains
maintaining the established MainWindow-facing API while responsibilities are isolated.
"""

from typing import List, Optional, Tuple
import html
import re
from prs_shared import *
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QRadioButton, QButtonGroup, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox,
    QFrame, QLineEdit, QInputDialog, QListWidgetItem, QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor
from speaker_identity import (
    cosine_similarity,
    robust_reference_profile,
    compare_against_profiles,
    is_confident_match,
    centroid,
)


class ChangeSpeakerDialog(QDialog):
    """Dialog prompting whether to apply a speaker name change to all instances or a single turn."""

    def __init__(self, current_name: str, target_name: str, seg_idx: int = -1, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Speaker")
        self.setMinimumWidth(520)
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


class VoiceProfileMatchDialog(QDialog):
    """Dialog for finding and reassigning matching speaker turns using a 256-dimensional acoustic voice profile."""

    def __init__(
        self,
        ref_seg_idx: int,
        current_speaker: str,
        target_speaker: str = "",
        prompt_new_speaker: bool = False,
        ref_seg_indices: Optional[List[int]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.ref_seg_idx = ref_seg_idx
        self.ref_seg_indices = ref_seg_indices or []
        self.current_speaker = current_speaker or "Unknown Speaker"
        self.target_name = target_speaker or self.current_speaker
        self.prompt_new_speaker = prompt_new_speaker
        self.parent_window = parent
        self.matched_turns = []
        self.selected_indices = []

        self.cluster_seg_indices = []
        if self.parent_window and getattr(self.parent_window, "transcript", None):
            segs = self.parent_window.transcript.get("segments", [])
            for idx, s in enumerate(segs):
                spk = self.parent_window.get_effective_speaker_name(idx, s)
                if spk == self.current_speaker:
                    self.cluster_seg_indices.append(idx)

        self.setWindowTitle("Teach This Voice: Acoustic Profile Matcher")
        self.setMinimumSize(720, 580)
        self.resize(760, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Title & Description
        header_layout = QVBoxLayout()
        header_layout.setSpacing(3)

        header_top_layout = QHBoxLayout()
        title_lbl = QLabel("Acoustic Voice Profile Matcher & Re-Clustering", self)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #f1f5f9;")
        header_top_layout.addWidget(title_lbl, 1)

        self.btn_toggle_hints = QPushButton("💡 Usage Hints", self)
        self.btn_toggle_hints.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_hints.setMaximumHeight(26)
        self.btn_toggle_hints.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #7dd3fc;
            }
        """)
        self.btn_toggle_hints.clicked.connect(self._toggle_hints)
        header_top_layout.addWidget(self.btn_toggle_hints)
        header_layout.addLayout(header_top_layout)

        desc_lbl = QLabel(
            "Use this speaker turn as a reference voice profile to find and reassign matching turns across the timeline using acoustic embedding similarity.",
            self,
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        header_layout.addWidget(desc_lbl)
        layout.addLayout(header_layout)

        # Collapsible Usage Hints Card
        self.hints_box = QGroupBox("💡 Acoustic Voice Profile Matcher — Quick Usage Guide", self)
        self.hints_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 6px;
                margin-top: 4px;
                padding-top: 14px;
                background-color: #0c4a6e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        hints_layout = QVBoxLayout(self.hints_box)
        hints_layout.setContentsMargins(12, 8, 12, 10)
        hints_layout.setSpacing(6)

        hints_html = """
        <div style="color: #e0f2fe; font-size: 11px; line-height: 1.45;">
            <b>How to use the Acoustic Voice Profile Matcher:</b>
            <ol style="margin-top: 4px; margin-bottom: 4px; padding-left: 18px;">
                <li><b>Reference Baseline Mode:</b> Single reference turn prevents cluster contamination. Use composite only across turns verified to be the same speaker.</li>
                <li><b>Assign Target Label:</b> Select or type the correct speaker name in <b>"Assign Matched Turns To"</b>.</li>
                <li><b>Choose Search Scope:</b> Global search discovers turns misattributed to other speakers.</li>
                <li><b>Calibrated Threshold:</b> ResNet-34 broadcast baseline is 78–82%. Values below 75% risk cross-speaker merging.</li>
                <li><b>Audition & Review:</b> Select any row to seek, press <b>Spacebar</b> or click <b>Audition Turn</b> to play/pause audio before confirming.</li>
            </ol>
        </div>
        """
        hints_lbl = QLabel(hints_html, self.hints_box)
        hints_lbl.setWordWrap(True)
        hints_layout.addWidget(hints_lbl)

        hints_btn_layout = QHBoxLayout()
        hints_btn_layout.addStretch()
        btn_minimize_hints = QPushButton("Minimize / Hide Hints", self.hints_box)
        btn_minimize_hints.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minimize_hints.setStyleSheet("""
            QPushButton {
                background-color: #0369a1;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0284c7;
            }
        """)
        btn_minimize_hints.clicked.connect(self._toggle_hints)
        hints_btn_layout.addWidget(btn_minimize_hints)
        hints_layout.addLayout(hints_btn_layout)
        layout.addWidget(self.hints_box)

        show_hints = True
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            show_hints = settings.value("voice_profile_matcher_show_hints", True, type=bool)
        except Exception:
            show_hints = True

        self.hints_box.setVisible(show_hints)
        self.btn_toggle_hints.setText("💡 Hide Hints" if show_hints else "💡 Usage Hints")

        ref_card = QGroupBox("Reference Speaker Turn & Profile Baseline", self)
        ref_card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 14px;
                background-color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        ref_card_layout = QVBoxLayout(ref_card)
        ref_card_layout.setContentsMargins(12, 10, 12, 12)
        ref_card_layout.setSpacing(6)

        ref_text = ""
        ref_time_str = ""
        if self.parent_window and getattr(self.parent_window, "transcript", None):
            segs = self.parent_window.transcript.get("segments", [])
            if 0 <= self.ref_seg_idx < len(segs):
                s = segs[self.ref_seg_idx]
                st = float(s.get("start", 0.0))
                en = float(s.get("end", st))
                ref_time_str = f"{format_time(st)} – {format_time(en)}"
                ref_text = s.get("text", "").strip()

        ref_info_lbl = QLabel(
            f"<b>Primary Turn #{self.ref_seg_idx + 1}</b> • Time: <b>{ref_time_str}</b> • Current Label: <span style='color: #fbbf24;'><b>{html.escape(self.current_speaker)}</b></span>",
            ref_card,
        )
        ref_card_layout.addWidget(ref_info_lbl)

        if ref_text:
            ref_text_lbl = QLabel(f"<i>“{html.escape(ref_text)}”</i>", ref_card)
            ref_text_lbl.setWordWrap(True)
            ref_text_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            ref_card_layout.addWidget(ref_text_lbl)

        mode_hdr = QLabel("Reference Vector Baseline Mode:", ref_card)
        mode_hdr.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px; margin-top: 4px;")
        ref_card_layout.addWidget(mode_hdr)

        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(4)

        self.ref_mode_single_radio = QRadioButton(
            f"Single Reference Turn (Use strictly Segment #{self.ref_seg_idx + 1} audio vector)", ref_card
        )

        cluster_count = len(self.cluster_seg_indices)
        self.ref_mode_composite_radio = QRadioButton(
            f"Composite Profile (Average acoustic vectors across verified turns of '{html.escape(self.current_speaker)}')", ref_card
        )

        if self.ref_seg_indices and len(self.ref_seg_indices) > 1:
            sel_count = len(self.ref_seg_indices)
            self.ref_mode_selected_radio = QRadioButton(
                f"Composite Profile (Average acoustic vectors across {sel_count} selected reference turns)", ref_card
            )
            self.ref_mode_selected_radio.setChecked(True)
            mode_layout.addWidget(self.ref_mode_selected_radio)
        else:
            self.ref_mode_single_radio.setChecked(True)

        mode_layout.addWidget(self.ref_mode_single_radio)
        mode_layout.addWidget(self.ref_mode_composite_radio)
        ref_card_layout.addLayout(mode_layout)

        layout.addWidget(ref_card)

        # Target Speaker Assignment Section
        target_group = QGroupBox("Target Speaker Assignment", self)
        target_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        target_layout = QHBoxLayout(target_group)
        target_layout.setContentsMargins(12, 10, 12, 12)
        target_layout.setSpacing(10)

        target_lbl = QLabel("Assign Matched Turns To:", target_group)
        target_layout.addWidget(target_lbl)

        self.spk_combo = QComboBox(target_group)
        self.spk_combo.setEditable(True)
        self.spk_combo.setMinimumWidth(260)
        self.spk_combo.setMinimumHeight(30)

        known = []
        if self.parent_window and hasattr(self.parent_window, "get_all_known_speakers"):
            known = self.parent_window.get_all_known_speakers()
        for k in known:
            self.spk_combo.addItem(k)

        if self.prompt_new_speaker:
            self.spk_combo.setEditText("")
            self.spk_combo.setFocus()
        elif self.target_name:
            idx = self.spk_combo.findText(self.target_name)
            if idx >= 0:
                self.spk_combo.setCurrentIndex(idx)
            else:
                self.spk_combo.setEditText(self.target_name)

        self.spk_combo.currentTextChanged.connect(lambda _: self._update_action_summary())
        target_layout.addWidget(self.spk_combo, 1)
        layout.addWidget(target_group)

        # Controls Grid
        controls_group = QGroupBox("Matching Search Scope & Sensitivity", self)
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(12, 10, 12, 12)
        controls_layout.setSpacing(10)

        scope_layout = QHBoxLayout()
        scope_layout.setSpacing(20)
        self.scope_all_radio = QRadioButton("Search across all speakers on timeline (Find mislabeled turns)", controls_group)
        scope_layout.addWidget(self.scope_all_radio)

        self.scope_cluster_radio = QRadioButton(
            f"Search within '{self.current_speaker}' turns only", controls_group
        )
        scope_layout.addWidget(self.scope_cluster_radio)
        self.scope_all_radio.setChecked(True)

        scope_layout.addStretch()
        controls_layout.addLayout(scope_layout)

        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(12)

        self.thresh_slider = QSlider(Qt.Orientation.Horizontal, controls_group)
        self.thresh_slider.setRange(60, 95)
        self.thresh_slider.setValue(78)
        self.thresh_slider.setTickInterval(5)
        self.thresh_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.thresh_slider.valueChanged.connect(self._on_slider_changed)

        self.thresh_label = QLabel("Similarity Threshold: 78% (Calibrated)", controls_group)
        self.thresh_label.setMinimumWidth(230)
        self.thresh_label.setStyleSheet("color: #38bdf8; font-weight: bold;")

        slider_layout.addWidget(self.thresh_slider, 1)
        slider_layout.addWidget(self.thresh_label)
        controls_layout.addLayout(slider_layout)

        self.scope_all_radio.toggled.connect(self._on_controls_changed)
        self.scope_cluster_radio.toggled.connect(self._on_controls_changed)
        self.ref_mode_single_radio.toggled.connect(self._on_controls_changed)
        self.ref_mode_composite_radio.toggled.connect(self._on_controls_changed)
        if hasattr(self, "ref_mode_selected_radio"):
            self.ref_mode_selected_radio.toggled.connect(self._on_controls_changed)

        layout.addWidget(controls_group)

        # Matched Turns Table & Batch Actions
        table_header_layout = QHBoxLayout()
        self.match_count_label = QLabel("Candidate Matching Turns (0 found):", self)
        self.match_count_label.setStyleSheet("font-weight: bold; color: #e2e8f0;")
        table_header_layout.addWidget(self.match_count_label)
        table_header_layout.addStretch()

        self.chk_master = QCheckBox("Select All", self)
        self.chk_master.setChecked(True)
        self.chk_master.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_master.setStyleSheet("color: #38bdf8; font-weight: bold; margin-right: 10px;")
        self.chk_master.toggled.connect(self._toggle_master_checkbox)
        table_header_layout.addWidget(self.chk_master)
        
        
        self.btn_audition = QPushButton("▶ Audition Turn", self)
        self.btn_audition.setMaximumHeight(26)
        self.btn_audition.setToolTip("Play or pause audio for the selected turn (Spacebar)")
        self.btn_audition.clicked.connect(self._toggle_audition_button)
        table_header_layout.addWidget(self.btn_audition)

        btn_select_all = QPushButton("Select All", self)
        btn_select_all.setMaximumHeight(26)
        btn_select_all.clicked.connect(self._select_all_matches)
        table_header_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Deselect All", self)
        btn_deselect_all.setMaximumHeight(26)
        btn_deselect_all.clicked.connect(self._deselect_all_matches)
        table_header_layout.addWidget(btn_deselect_all)

        layout.addLayout(table_header_layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Reassign", "Segment", "Current Speaker", "Acoustic Match", "Transcript Preview"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        
        # Install Event Filter on QTableWidget so it does NOT swallow the Spacebar key!
        self.table.installEventFilter(self)

        layout.addWidget(self.table, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_apply = QPushButton("Reassign Matching Turns", self)
        self.btn_apply.setDefault(True)
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.btn_apply, 2)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel, 1)

        layout.addLayout(btn_layout)

        # Hook up playback state monitoring if player exists
        if self.parent_window and hasattr(self.parent_window, "player"):
            player = getattr(self.parent_window, "player", None)
            if player and hasattr(player, "playbackStateChanged"):
                player.playbackStateChanged.connect(self._on_playback_state_changed)

        self._on_slider_changed(self.thresh_slider.value())

    def _on_playback_state_changed(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_audition.setText("❚❚ Pause")
        else:
            self.btn_audition.setText("▶ Audition Turn")

    def _toggle_hints(self):
        is_visible = self.hints_box.isVisible()
        self.hints_box.setVisible(not is_visible)
        self.btn_toggle_hints.setText("💡 Usage Hints" if is_visible else "💡 Hide Hints")
        try:
            settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
            settings.setValue("voice_profile_matcher_show_hints", not is_visible)
        except Exception:
            pass

    def _on_slider_changed(self, val):
        threshold_float = val / 100.0
        dist_max = 1.0 - threshold_float
        desc = "Permissive" if val < 75 else ("Optimal" if val <= 82 else "Very Strict")
        self.thresh_label.setText(f"Similarity Threshold: {val}% ({desc}, Cosine dist ≤ {dist_max:.2f})")
        self._update_matches()

    def get_active_ref_indices(self) -> List[int]:
        if hasattr(self, "ref_mode_composite_radio") and self.ref_mode_composite_radio.isChecked():
            return self.cluster_seg_indices or [self.ref_seg_idx]
        elif hasattr(self, "ref_mode_selected_radio") and self.ref_mode_selected_radio.isChecked():
            return self.ref_seg_indices or [self.ref_seg_idx]
        return [self.ref_seg_idx]

    def _on_controls_changed(self):
        self._update_matches()

    def _update_matches(self):
        if not hasattr(self, "thresh_slider") or not hasattr(self, "scope_cluster_radio"):
            return
        if not self.parent_window or not hasattr(self.parent_window, "find_matching_voice_turns"):
            return

        threshold = self.thresh_slider.value() / 100.0
        scope_cluster_only = self.scope_cluster_radio.isChecked()
        active_ref_indices = self.get_active_ref_indices()

        self.matched_turns = self.parent_window.find_matching_voice_turns(
            self.ref_seg_idx,
            threshold=threshold,
            scope_cluster_only=scope_cluster_only,
            ref_seg_indices=active_ref_indices,
        )

        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for row_idx, turn in enumerate(self.matched_turns):
            self.table.insertRow(row_idx)

            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked)
            chk_item.setData(Qt.ItemDataRole.UserRole, turn["seg_idx"])
            self.table.setItem(row_idx, 0, chk_item)

            st_str = format_time(turn["start"])
            en_str = format_time(turn["end"])
            seg_item = QTableWidgetItem(f"#{turn['seg_idx'] + 1} ({st_str} – {en_str})")
            seg_item.setToolTip(f"Segment #{turn['seg_idx'] + 1}\nStart: {turn['start']:.2f}s, End: {turn['end']:.2f}s")
            self.table.setItem(row_idx, 1, seg_item)

            spk_item = QTableWidgetItem(turn["speaker"])
            self.table.setItem(row_idx, 2, spk_item)

            sim_pct = turn["similarity"] * 100.0
            match_item = QTableWidgetItem(f"{sim_pct:.1f}% Match")
            match_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if sim_pct >= 85.0:
                match_item.setForeground(QBrush(QColor("#4ade80")))
            elif sim_pct >= 78.0:
                match_item.setForeground(QBrush(QColor("#38bdf8")))
            else:
                match_item.setForeground(QBrush(QColor("#fbbf24")))
            self.table.setItem(row_idx, 3, match_item)

            txt_item = QTableWidgetItem(turn["text"])
            txt_item.setToolTip(turn["text"])
            self.table.setItem(row_idx, 4, txt_item)

        self.table.blockSignals(False)
        self._update_action_summary()

    def _select_all_matches(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self.table.blockSignals(False)
        self._update_action_summary()

    def _deselect_all_matches(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.table.blockSignals(False)
        self._update_action_summary()

    def _toggle_master_checkbox(self, checked: bool):
        """Batch toggle every row checkbox to match the master checkbox state."""
        self.table.blockSignals(True)
        target_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(target_state)
        self.table.blockSignals(False)
        self._update_action_summary()
        
    def _on_table_item_changed(self, item):
        if item.column() == 0:
            self._update_action_summary()

    def _get_selected_segment_indices(self) -> List[int]:
        indices = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                seg_idx = item.data(Qt.ItemDataRole.UserRole)
                if seg_idx is not None:
                    indices.append(int(seg_idx))
        return indices

    def _update_action_summary(self):
        selected = self._get_selected_segment_indices()
        total = self.table.rowCount()
        self.match_count_label.setText(
            f"Candidate Matching Turns ({len(selected)} of {total} selected):"
        )
        target = self.spk_combo.currentText().strip() or "Target Speaker"
        self.btn_apply.setText(f"Reassign {len(selected)} Matching Turn(s) to '{target}'")
        self.btn_apply.setEnabled(len(selected) > 0 or self.ref_seg_idx >= 0)

        # ADD IT HERE AT THE END OF THE METHOD:
        if hasattr(self, "chk_master"):
            self.chk_master.blockSignals(True)
            all_selected = (len(selected) == total and total > 0)
            self.chk_master.setChecked(all_selected)
            self.chk_master.setText("Deselect All" if all_selected else "Select All")
            self.chk_master.blockSignals(False)

    def _on_apply(self):
        self._stop_playback()
        target = self.spk_combo.currentText().strip()
        if not target:
            QMessageBox.warning(
                self,
                "Target Speaker Required",
                "Please enter or select a target speaker name before applying.",
            )
            self.spk_combo.setFocus()
            return

        self.target_name = target
        self.selected_indices = self._get_selected_segment_indices()
        self.accept()

    def reject(self):
        self._stop_playback()
        super().reject()

    def _seek_to_time(self, seconds: float):
        if self.parent_window and hasattr(self.parent_window, "seek_to"):
            try:
                self.parent_window.seek_to(seconds)
            except Exception:
                pass

    def _is_playing(self) -> bool:
        if not self.parent_window:
            return False
        player = getattr(self.parent_window, "player", None)
        if player and hasattr(player, "playbackState"):
            from PySide6.QtMultimedia import QMediaPlayer
            return player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        return False

    def _stop_playback(self):
        if not self.parent_window:
            return
        player = getattr(self.parent_window, "player", None)
        if player and hasattr(player, "pause"):
            try:
                player.pause()
            except Exception:
                pass
        self.btn_audition.setText("▶ Audition Turn")

    def _toggle_playback(self):
        if not self.parent_window:
            return
        player = getattr(self.parent_window, "player", None)
        if player and hasattr(player, "playbackState"):
            from PySide6.QtMultimedia import QMediaPlayer
            if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                player.pause()
                self.btn_audition.setText("▶ Audition Turn")
            else:
                player.play()
                self.btn_audition.setText("❚❚ Pause")
        elif hasattr(self.parent_window, "toggle_play"):
            self.parent_window.toggle_play()

    def _toggle_audition_button(self):
        if self._is_playing():
            self._stop_playback()
        else:
            row = self.table.currentRow()
            if 0 <= row < len(self.matched_turns):
                turn = self.matched_turns[row]
                start_t = turn.get("start", 0.0)
                self._seek_to_time(start_t)
            self._toggle_playback()

    def _on_table_selection_changed(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.matched_turns):
            turn = self.matched_turns[row]
            start_t = turn.get("start", 0.0)
            self._seek_to_time(start_t)

    def _on_table_cell_double_clicked(self, row, col):
        if 0 <= row < len(self.matched_turns):
            turn = self.matched_turns[row]
            start_t = turn.get("start", 0.0)
            self._seek_to_time(start_t)
            if not self._is_playing():
                self._toggle_playback()

    def eventFilter(self, watched, event):
        """Intercept Spacebar on the table widget so it controls playback instead of row selection."""
        if watched == self.table and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space:
                self._toggle_audition_button()
                return True  # Event handled, do not pass to table
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            focused = self.focusWidget()
            if focused and (
                isinstance(focused, QLineEdit)
                or (isinstance(focused, QComboBox) and focused.isEditable() and focused.lineEdit() and focused.lineEdit().hasFocus())
            ):
                super().keyPressEvent(event)
                return

            self._toggle_audition_button()
            event.accept()
            return

        super().keyPressEvent(event)


class TranscriptStoryMixin:
    def render_transcript(self):
        if not self.transcript:
            return

        v_scroll = 0
        h_scroll = 0
        if hasattr(self, "transcript_view") and self.transcript_view:
            v_scroll = self.transcript_view.verticalScrollBar().value()
            h_scroll = self.transcript_view.horizontalScrollBar().value()
            self.transcript_view.active_highlight_anchor = None

        self.is_updating_transcript_view = True
        display_mode = getattr(self, "translation_display_mode", "en")
        if display_mode == "bilingual":
            display_mode = "split"
        segments = self.transcript.get("segments", [])
        es_item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else None
        es_segments = es_item.get("segments", []) if isinstance(es_item, dict) else []

        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        active_segments = segments
        is_rendering_translation = False
        if src_code == "es":
            if display_mode == "en" and es_segments:
                active_segments = es_segments
                is_rendering_translation = True
        else:
            if display_mode == "es" and es_segments:
                active_segments = es_segments
                is_rendering_translation = True

        if not active_segments:
            self.transcript_view.setHtml("")
            self.transcript_view.set_char_timestamp_map([])
            self._block_segment_groups = []
            if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
                self._transcript_edit_baseline = self._capture_project_state()
            self.is_updating_transcript_view = False
            return

        word_tokens = []
        for seg_idx, segment in enumerate(active_segments):
            start = segment.get("start", 0.0) if isinstance(segment, dict) else getattr(segment, "start", 0.0)
            end = segment.get("end", start) if isinstance(segment, dict) else getattr(segment, "end", start)
            raw_spk = self.segment_speaker_overrides.get(seg_idx) or self.speaker_at_time(start, end)
            orig_segment = segments[seg_idx] if 0 <= seg_idx < len(segments) else segment
            spk_name = self.get_effective_speaker_name(seg_idx, orig_segment)

            words = [] if is_rendering_translation else segment.get("words", [])
            if words:
                for w in words:
                    token = {
                        "word": w.get("word", ""),
                        "start": w.get("start", start),
                        "end": w.get("end", end),
                        "seg_idx": seg_idx,
                        "speaker_name": spk_name,
                        "raw_speaker": raw_spk,
                        "deleted": bool(w.get("deleted", False)),
                    }
                    if w.get("bold"): token["bold"] = True
                    if w.get("italic"): token["italic"] = True
                    if w.get("underline"): token["underline"] = True
                    if w.get("strike"): token["strike"] = True
                    if w.get("highlight"):
                        hl = w.get("highlight")
                        token["highlight"] = "#fef08a" if isinstance(hl, bool) or hl in ("True", "true", 1) else str(hl)
                    word_tokens.append(token)
            else:
                seg_text = segment.get("text", "")
                for word in seg_text.split():
                    word_tokens.append({
                        "word": word,
                        "start": start,
                        "end": end,
                        "seg_idx": seg_idx,
                        "speaker_name": spk_name,
                        "raw_speaker": raw_spk,
                        "deleted": False,
                    })

        if not word_tokens:
            self.transcript_view.setHtml("")
            self.transcript_view.set_char_timestamp_map([])
            self._block_segment_groups = []
            if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
                self._transcript_edit_baseline = self._capture_project_state()
            self.is_updating_transcript_view = False
            return

        doc = self.transcript_view.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()

        html_parts = []
        char_timestamp_map = []
        current_char_pos = 0
        block_segment_groups = []

        curr_theme = getattr(self.transcript_view, "current_theme", "dark")
        if curr_theme == "light":
            word_color = "#111111"
            speaker_color = "#0056b3"
            time_color = "#555c68"
            spanish_color = "#1a7f37"
            spanish_tag_color = "#57606a"
        elif curr_theme == "high_contrast":
            word_color = "#ffffff"
            speaker_color = "#00ffff"
            time_color = "#ffff00"
            spanish_color = "#00ff00"
            spanish_tag_color = "#ffff00"
        else:
            word_color = "#ffffff"
            speaker_color = "#58a6ff"
            time_color = "#8b949e"
            spanish_color = "#7ee787"
            spanish_tag_color = "#8b949e"

        curr_para_words = []
        curr_speaker_name = None
        curr_raw_speaker = None
        last_rendered_speaker_name = None

        def render_paragraph_block(p_words, p_speaker_name, p_raw_speaker, is_speaker_change):
            nonlocal current_char_pos
            if not p_words:
                return ""

            start_time = p_words[0]["start"]
            first_seg_idx = p_words[0]["seg_idx"]
            time_str = format_time(start_time)

            if p_speaker_name and is_speaker_change and self.show_speaker_labels:
                esc_spk = html.escape(p_speaker_name)
                esc_raw = html.escape(str(p_raw_speaker or ""))
                speaker_html = (
                    f'<a href="speaker:{first_seg_idx}:{esc_raw}" style="color:{speaker_color}; font-weight:bold; text-decoration:none;">'
                    f'{esc_spk}:</a> '
                )
            else:
                speaker_html = ""
            plain_prefix = (f"{time_str} " if self.show_timestamps else "")
            if self.show_speaker_labels and p_speaker_name and is_speaker_change:
                plain_prefix += f"{p_speaker_name}: "

            current_char_pos += len(plain_prefix)

            word_html_list = []
            current_hl_color = None
            current_hl_words = []

            def _flush_hl_group():
                nonlocal current_hl_words, current_hl_color
                if not current_hl_words:
                    return
                joined_html = " ".join(current_hl_words)
                if current_hl_color:
                    word_html_list.append(
                        f'<span style="background-color:{current_hl_color}; color:#0f172a; padding:1px 0px; border-radius:2px;">{joined_html}</span>'
                    )
                else:
                    word_html_list.append(joined_html)
                current_hl_words = []

            for item in p_words:
                w_text = item["word"]
                w_start = item["start"]
                w_seg = item["seg_idx"]

                w_len = len(w_text) + 1
                char_timestamp_map.append((current_char_pos, current_char_pos + w_len, w_start, item.get("end", w_start), w_seg))
                current_char_pos += w_len

                esc_w = html.escape(w_text)
                w_style = f"color:{word_color}; text-decoration:none;"
                if item.get("bold"):
                    w_style += " font-weight:bold;"
                if item.get("italic"):
                    w_style += " font-style:italic;"
                if item.get("underline") and item.get("strike"):
                    w_style += " text-decoration:underline line-through;"
                elif item.get("underline"):
                    w_style += " text-decoration:underline;"
                elif item.get("strike"):
                    w_style += " text-decoration:line-through;"

                hl_val = item.get("highlight")
                item_hl_color = None
                if hl_val:
                    item_hl_color = "#fef08a" if isinstance(hl_val, bool) or hl_val in ("True", "true", 1) else str(hl_val)
                    w_style += f" color:#0f172a;"

                if item_hl_color != current_hl_color:
                    _flush_hl_group()
                    current_hl_color = item_hl_color

                current_hl_words.append(f'<a href="word:{w_start}:{w_seg}" style="{w_style}">{esc_w}</a>')

            _flush_hl_group()
            current_char_pos += 2

            body_content = " ".join(word_html_list)

            timestamp_html = (
                f'<a href="time:{start_time}" style="color:{time_color}; text-decoration:none;"><b>{time_str}</b></a> '
                if self.show_timestamps else ""
            )

            if display_mode in ("split", "bilingual") and es_segments:
                seg_indices = list(dict.fromkeys(item["seg_idx"] for item in p_words))
                es_text_parts = [es_segments[idx].get("text", "") for idx in seg_indices if 0 <= idx < len(es_segments)]
                es_text = " ".join(t.strip() for t in es_text_parts if t.strip())
                if es_text:
                    esc_es_text = html.escape(es_text)
                    src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
                    tag_label = "EN: " if src_code == "es" else "ES: "
                    return (
                        f'<p style="margin-bottom: 14px;">'
                        f'{timestamp_html}{speaker_html}'
                        f'<span style="color:{word_color};">{body_content}</span><br/>'
                        f'<span style="color:{spanish_tag_color}; font-weight:bold; font-size:0.86em;">{tag_label}</span>'
                        f'<span style="color:{spanish_color};"><i>{esc_es_text}</i></span>'
                        f'</p>'
                    )

            return (
                f'<p style="margin-bottom: 14px; color: {word_color};">'
                f'{timestamp_html}{speaker_html}'
                f'<span style="color:{word_color};">{body_content}</span>'
                f'</p>'
            )

        def _summarize_paragraph_segments(p_words):
            groups = []
            for w in p_words:
                seg_idx = w["seg_idx"]
                if groups and groups[-1][0] == seg_idx:
                    groups[-1] = (seg_idx, groups[-1][1] + 1)
                else:
                    groups.append((seg_idx, 1))
            return groups

        for token in word_tokens:
            spk_name = token["speaker_name"]
            raw_spk = token["raw_speaker"]

            if curr_speaker_name is None:
                curr_speaker_name = spk_name
                curr_raw_speaker = raw_spk

            speaker_changed = (spk_name != curr_speaker_name)
            prev_token = curr_para_words[-1] if curr_para_words else None
            time_gap = (token["start"] - prev_token["end"]) if prev_token and "end" in prev_token and "start" in token else 0.0
            prev_word_ended_sentence = prev_token and is_sentence_end(prev_token["word"])
            word_count = len(curr_para_words)

            silence_thresh = float(getattr(self, "silence_threshold", 3.0) or 3.0)
            major_silence = (time_gap >= max(2.5, silence_thresh))

            should_break = (
                speaker_changed
                or major_silence
                or (word_count >= MIN_WORDS_PER_PARAGRAPH and prev_word_ended_sentence)
                or (word_count >= 50)
            )

            if curr_para_words and should_break:
                is_change = (curr_speaker_name != last_rendered_speaker_name)
                html_parts.append(render_paragraph_block(curr_para_words, curr_speaker_name, curr_raw_speaker, is_change))
                block_segment_groups.append(_summarize_paragraph_segments(curr_para_words))
                last_rendered_speaker_name = curr_speaker_name

                curr_para_words = [token]
                curr_speaker_name = spk_name
                curr_raw_speaker = raw_spk
            else:
                curr_para_words.append(token)

        if curr_para_words:
            is_change = (curr_speaker_name != last_rendered_speaker_name)
            html_parts.append(render_paragraph_block(curr_para_words, curr_speaker_name, curr_raw_speaker, is_change))
            block_segment_groups.append(_summarize_paragraph_segments(curr_para_words))

        self.transcript_view.setHtml("".join(html_parts))
        cursor.endEditBlock()
        self._block_segment_groups = block_segment_groups

        self.timeline.set_transcript_selection_range(None, None)
        self.transcript_view.rebuild_anchor_index()
        self.transcript_view.set_time_anchor_index(
            [
                (item["start"], item["end"], f"word:{item['start']}:{item['seg_idx']}")
                for item in word_tokens
            ]
        )
        self.transcript_view.set_char_timestamp_map(char_timestamp_map)
        if hasattr(self, "comments_panel"):
            self.comments_panel.set_comments(self.transcript.get("segments", []))
        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

        if hasattr(self, "transcript_view") and self.transcript_view:
            self.transcript_view.active_highlight_anchor = None
            if hasattr(self.transcript_view, "lock_scroll_position"):
                self.transcript_view.lock_scroll_position(v_scroll, h_scroll, duration_ms=400)
            else:
                self.transcript_view.verticalScrollBar().setValue(v_scroll)
                self.transcript_view.horizontalScrollBar().setValue(h_scroll)

            def _restore_scroll(vs=v_scroll, hs=h_scroll):
                if hasattr(self, "transcript_view") and self.transcript_view:
                    self.transcript_view.verticalScrollBar().setValue(vs)
                    self.transcript_view.horizontalScrollBar().setValue(hs)
            QTimer.singleShot(0, _restore_scroll)
            QTimer.singleShot(25, _restore_scroll)
            QTimer.singleShot(60, _restore_scroll)
            QTimer.singleShot(150, _restore_scroll)

            cur_pos = getattr(self, "current_position", 0.0)
            if cur_pos >= 0 and hasattr(self.transcript_view, "highlight_word_at_time"):
                self.transcript_view.highlight_word_at_time(cur_pos, self.transcript, auto_scroll=False)

        if hasattr(self, "_capture_project_state") and not getattr(self, "is_restoring_undo", False):
            self._transcript_edit_baseline = self._capture_project_state()
        self.is_updating_transcript_view = False

        if hasattr(self, "transcript_mode_toggle_btn"):
            if display_mode in ("split", "bilingual"):
                self.transcript_mode_toggle_btn.setEnabled(False)
                self.transcript_mode_toggle_btn.setChecked(False)
                self.transcript_mode_toggle_btn.setText("Edit Transcript")
                self.transcript_mode_toggle_btn.setStyleSheet("")
            else:
                self.transcript_mode_toggle_btn.setEnabled(True)
                is_editing = getattr(self.transcript_view, "is_editing_mode", False)
                self.transcript_mode_toggle_btn.setChecked(is_editing)
                if is_editing:
                    self.transcript_mode_toggle_btn.setText("View Transcript")
                    self.transcript_mode_toggle_btn.setStyleSheet("font-weight: bold; background-color: #2b5278; color: white;")
                else:
                    self.transcript_mode_toggle_btn.setText("Edit Transcript")
                    self.transcript_mode_toggle_btn.setStyleSheet("")

        if display_mode in ("split", "bilingual"):
            self.transcript_view.setReadOnly(True)
        else:
            self.transcript_view.setReadOnly(not getattr(self.transcript_view, "is_editing_mode", False))

    def on_transcript_selection_changed(self):
        if self.is_updating_transcript_view:
            return
        selected_range = self.transcript_view.get_selected_time_range()
        if selected_range:
            self.last_position_source = "transcript"
            self.timeline.set_transcript_selection_range(*selected_range)
            self.statusBar().showMessage(
                f"Transcript selection: {format_time(selected_range[0])} – {format_time(selected_range[1])}"
            )
        else:
            if not getattr(self.transcript_view, "has_active_selection", lambda: False)():
                self.timeline.set_transcript_selection_range(None, None)
            cursor = self.transcript_view.textCursor()
            ts = self.transcript_view.get_timestamp_at_cursor(cursor)
            if ts is not None and ts >= 0:
                self.last_transcript_cursor_time = ts
                self.last_position_source = "transcript"

        cursor = self.transcript_view.textCursor()
        target_seg = self.transcript_view.get_segment_index_at_cursor(cursor)
        if target_seg is None:
            target_seg = cursor.blockNumber()

        active_comment_seg = None
        segments = self.transcript.get("segments", []) if self.transcript else []
        if 0 <= target_seg < len(segments):
            seg = segments[target_seg]
            if (seg.get("comments") or seg.get("notes", "")).strip():
                active_comment_seg = target_seg

        if hasattr(self, "comments_panel"):
            self.comments_panel.highlight_segment(active_comment_seg)

    def on_transcript_text_changed(self):
        if self.is_updating_transcript_view or getattr(self, "is_restoring_undo", False) or not self.transcript:
            return
        display_mode = getattr(self, "translation_display_mode", "en")
        if display_mode in ("split", "bilingual"):
            return

        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        use_translation = (display_mode == "en") if src_code == "es" else (display_mode == "es")

        if use_translation:
            es_item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else None
            if not es_item or not isinstance(es_item, dict):
                return
            target_segments = es_item.get("segments", [])
        else:
            target_segments = self.transcript.get("segments", [])

        if not target_segments:
            return

        doc = self.transcript_view.document()
        blocks_count = doc.blockCount()
        block_groups = getattr(self, "_block_segment_groups", None) or []
        known_speaker_labels = None

        def _extract_block_word_formatting(block, prefix_len=0):
            word_formats = []
            it = block.begin()
            curr_pos = 0
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    frag_text = frag.text()
                    fmt = frag.charFormat()
                    frag_len = len(frag_text)
                    frag_start = curr_pos
                    frag_end = curr_pos + frag_len
                    if frag_end > prefix_len:
                        start_in_frag = max(0, prefix_len - frag_start)
                        usable_text = frag_text[start_in_frag:]
                        is_bold = fmt.fontWeight() > QFont.Weight.Medium
                        is_italic = fmt.fontItalic()
                        is_underline = fmt.fontUnderline()
                        is_strike = fmt.fontStrikeOut()
                        bg = fmt.background().color()
                        highlight = bg.name() if (bg.isValid() and bg.alpha() > 0 and fmt.background().style() != Qt.BrushStyle.NoBrush) else None
                        for w in usable_text.split():
                            word_formats.append({
                                "word": w,
                                "bold": is_bold,
                                "italic": is_italic,
                                "underline": is_underline,
                                "strike": is_strike,
                                "highlight": highlight,
                            })
                    curr_pos += frag_len
                it += 1
            return word_formats

        for i in range(min(blocks_count, len(block_groups))):
            groups = [g for g in block_groups[i] if 0 <= g[0] < len(target_segments)]
            if not groups:
                continue

            block = doc.findBlockByNumber(i)
            block_text = block.text()
            cleaned_text = re.sub(r'^\d{2}:\d{2}(?::\d{2})?\.\d{3}\s+', '', block_text)
            if ": " in cleaned_text:
                prefix, remainder = cleaned_text.split(": ", 1)
                if known_speaker_labels is None:
                    known_speaker_labels = set(self.speaker_names.values())
                    known_speaker_labels.update(
                        self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []
                    )
                if prefix.strip() in {str(x).strip() for x in known_speaker_labels if x}:
                    cleaned_text = remainder
            cleaned_text = re.sub(r'^Speaker \d+:\s+', '', cleaned_text).strip()

            prefix_len = block_text.find(cleaned_text) if (cleaned_text and cleaned_text in block_text) else 0
            block_fmts = _extract_block_word_formatting(block, prefix_len)

            if len(groups) == 1:
                target_seg = target_segments[groups[0][0]]
                target_seg["text"] = cleaned_text
                self.sync_segment_words(target_seg, cleaned_text, block_fmts)
                continue

            words = cleaned_text.split()
            total_original_words = sum(g[1] for g in groups) or 1
            remaining_words = words
            remaining_fmts = block_fmts
            for gi, (seg_idx, orig_count) in enumerate(groups):
                if gi == len(groups) - 1:
                    share, remaining_words = remaining_words, []
                    share_fmts, remaining_fmts = remaining_fmts, []
                else:
                    n = round(len(words) * (orig_count / total_original_words))
                    n = max(0, min(n, len(remaining_words)))
                    share, remaining_words = remaining_words[:n], remaining_words[n:]
                    share_fmts, remaining_fmts = remaining_fmts[:n], remaining_fmts[n:]
                seg_text = " ".join(share)
                target_segments[seg_idx]["text"] = seg_text
                self.sync_segment_words(target_segments[seg_idx], seg_text, share_fmts)

        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

        if getattr(self, "_pending_transcript_edit_before", None) is None:
            baseline = getattr(self, "_transcript_edit_baseline", None)
            if baseline is not None:
                self._pending_transcript_edit_before = baseline

        timer = getattr(self, "_transcript_undo_timer", None)
        if timer is not None:
            timer.start()

        self.mark_project_dirty()

    def transcript_clicked(self, url):
        text = url.toString()
        if text.startswith("time:") or text.startswith("word:"):
            parts = text.split(":")
            seconds = float(parts[1])
            self.last_position_source = "transcript"
            self.last_transcript_cursor_time = seconds
            self.seek_to(seconds)
            if hasattr(self.transcript_view, "move_cursor_to_time"):
                self.transcript_view.move_cursor_to_time(seconds, self.transcript)
        elif text.startswith("speaker:"):
            parts = text.split(":", 2)
            if len(parts) >= 2 and parts[1].isdigit():
                seg_idx = int(parts[1])
                raw_spk = parts[2] if len(parts) > 2 else ""
                if hasattr(self, "prompt_rename_speaker"):
                    self.prompt_rename_speaker(seg_idx, raw_spk)

    def edit_segment_comment_dialog(
        self,
        seg_idx: int,
        sel_text: str = "",
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
        t_range: Optional[tuple[float, float]] = None,
        covered_indices: Optional[List[int]] = None
    ):
        if not self.transcript or "segments" not in self.transcript:
            QMessageBox.information(self, "No Transcript", "No transcript is currently loaded.")
            return
        segments = self.transcript["segments"]
        if not (0 <= seg_idx < len(segments)):
            return
        seg = segments[seg_idx]
        current_comment = seg.get("comments") or seg.get("notes", "")

        if not sel_text:
            sel_text = seg.get("comment_selected_text", "")

        prompt = f"Comment for Segment {seg_idx + 1} ({format_time(seg.get('start', 0.0))}):"
        if sel_text:
            disp_quote = sel_text if len(sel_text) <= 80 else sel_text[:77] + "..."
            prompt = f'Comment for selection: "{disp_quote}"'

        dialog = CommentEditorDialog(
            self,
            comment_text=current_comment,
            title="Edit Comment" if current_comment else "Add Comment",
            prompt=prompt,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
            target_indices = [seg_idx]
            if dialog.is_deleted():
                for idx in target_indices:
                    if 0 <= idx < len(segments):
                        s = segments[idx]
                        s.pop("comments", None)
                        s.pop("notes", None)
                        s.pop("comment_selected_text", None)
                        s.pop("comment_char_start", None)
                        s.pop("comment_char_end", None)
                        s.pop("comment_start_time", None)
                        s.pop("comment_end_time", None)
            else:
                text = dialog.get_comment_text()
                if text.strip():
                    for idx in target_indices:
                        if 0 <= idx < len(segments):
                            s = segments[idx]
                            s["comments"] = text
                            s["notes"] = text
                            if sel_text:
                                s["comment_selected_text"] = sel_text
                            if start_char is not None and end_char is not None:
                                s["comment_char_start"] = start_char
                                s["comment_char_end"] = end_char
                            if t_range:
                                s["comment_start_time"] = t_range[0]
                                s["comment_end_time"] = t_range[1]
                else:
                    for idx in target_indices:
                        if 0 <= idx < len(segments):
                            s = segments[idx]
                            s.pop("comments", None)
                            s.pop("notes", None)
                            s.pop("comment_selected_text", None)
                            s.pop("comment_char_start", None)
                            s.pop("comment_char_end", None)
                            s.pop("comment_start_time", None)
                            s.pop("comment_end_time", None)

            self.mark_project_dirty()
            if hasattr(self, "transcript_view"):
                self.transcript_view.update_extra_selections()
            if hasattr(self, "comments_panel"):
                self.comments_panel.set_comments(segments)
                self.comments_panel.highlight_segment(seg_idx)
            if before_state and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, "Update Comment")

    edit_segment_note_dialog = edit_segment_comment_dialog

    def add_comment_from_selection(self):
        if not hasattr(self, "transcript_view") or not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript.get("segments", [])
        cursor = self.transcript_view.textCursor()
        sel_text = ""
        start_char = None
        end_char = None
        t_range = None
        covered_indices = []

        if cursor.hasSelection():
            sel_text = cursor.selectedText().replace('\u2029', '\n').strip()
            start_char = min(cursor.selectionStart(), cursor.selectionEnd())
            end_char = max(cursor.selectionStart(), cursor.selectionEnd())
            if hasattr(self.transcript_view, "get_time_range_for_char_span"):
                t_range = self.transcript_view.get_time_range_for_char_span(start_char, end_char)

        if t_range and t_range[0] is not None and t_range[1] is not None:
            st, et = t_range
            for i, s in enumerate(segments):
                s_start = s.get("start", 0.0)
                s_end = s.get("end", 0.0)
                if s_start < et and s_end > st:
                    covered_indices.append(i)

        seg_idx = None
        if covered_indices:
            seg_idx = covered_indices[0]
        else:
            seg_idx = self.transcript_view.get_segment_index_at_cursor(cursor)
            if seg_idx is None:
                seg_idx = cursor.blockNumber()

        if seg_idx is not None and 0 <= seg_idx < len(segments):
            self.edit_segment_comment_dialog(
                seg_idx,
                sel_text=sel_text,
                start_char=start_char,
                end_char=end_char,
                t_range=t_range,
                covered_indices=covered_indices
            )

    def delete_segment_comment(self, seg_idx):
        if not self.transcript or "segments" not in self.transcript:
            return
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        segments = self.transcript["segments"]
        if 0 <= seg_idx < len(segments):
            seg = segments[seg_idx]
            seg.pop("comments", None)
            seg.pop("notes", None)
            seg.pop("comment_selected_text", None)
            seg.pop("comment_char_start", None)
            seg.pop("comment_char_end", None)
            seg.pop("comment_start_time", None)
            seg.pop("comment_end_time", None)
            self.mark_project_dirty()
            if hasattr(self, "transcript_view"):
                self.transcript_view.update_extra_selections()
            if hasattr(self, "comments_panel"):
                self.comments_panel.set_comments(segments)
            if before_state and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, "Delete Comment")

    def toggle_comments_panel(self):
        if hasattr(self, "comments_panel"):
            is_vis = not self.comments_panel.isVisible()
            self.toggle_show_comments(is_vis)

    def toggle_show_comments(self, checked):
        self.show_comments = checked
        self.show_notes = checked
        if hasattr(self, "comments_panel"):
            self.comments_panel.setVisible(checked)
        if hasattr(self, "transcript_view"):
            self.transcript_view.update_extra_selections()

    toggle_show_notes = toggle_show_comments

    def toggle_comment_highlights(self, checked):
        self.show_comment_highlights = checked
        if hasattr(self, "transcript_view"):
            self.transcript_view.show_comment_highlights = checked
            self.transcript_view.update_extra_selections()

    def handle_insert_speaker_request(self, seg_idx, split_time, speaker_name):
        if speaker_name == "__NEW__":
            self.add_speaker_label_at(seg_idx, split_time, name=None)
        else:
            self.add_speaker_label_at(seg_idx, split_time, name=speaker_name)

    def add_speaker_label_at(self, seg_idx, split_time, name=None):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if not segments:
            return False

        if seg_idx is None or seg_idx < 0 or seg_idx >= len(segments):
            for i, seg in enumerate(segments):
                s_start = float(seg.get("start", 0.0))
                s_end = float(seg.get("end", s_start))
                if s_start <= split_time <= s_end:
                    seg_idx = i
                    break
            if seg_idx is None:
                seg_idx = max(0, min(len(segments) - 1, int(seg_idx or 0)))

        if name is None:
            known = self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []
            if known:
                name, accepted = QInputDialog.getItem(
                    self, "Add Speaker Label", "Speaker name for this label:", known, 0, True
                )
            else:
                name, accepted = QInputDialog.getText(self, "Add Speaker Label", "Speaker name for this label:")
            if not accepted:
                return False

        name = (name or "").strip()
        if not name:
            return False

        target_seg = segments[seg_idx]
        words = target_seg.get("words", [])

        is_at_segment_start = False
        if words:
            if split_time <= words[0].get("start", target_seg["start"]) + 0.05:
                is_at_segment_start = True
        else:
            if split_time <= float(target_seg.get("start", 0.0)) + 0.1:
                is_at_segment_start = True

        if is_at_segment_start:
            self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

            current_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = name
                self.segment_speaker_overrides[idx] = override_key
            self._diar_index_key = None

            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Add Speaker Label ({name})")

            self.add_custom_speaker_to_glossary(name)
            self.save_project()
            self.render_transcript()
            return True

        if not self.split_segment_at_time(seg_idx, split_time, new_speaker_name=name):
            self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
            before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

            current_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = name
                self.segment_speaker_overrides[idx] = override_key
            self._diar_index_key = None

            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Add Speaker Label ({name})")

            self.add_custom_speaker_to_glossary(name)
            self.save_project()
            self.render_transcript()
            return True

        self.add_custom_speaker_to_glossary(name)
        return True

    def split_segment_at_time(self, seg_idx, split_time, new_speaker_name=None):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return False

        target_seg = segments[seg_idx]
        words = target_seg.get("words", [])

        if words:
            split_idx = -1
            for w_i, w in enumerate(words):
                if w.get("start", target_seg["start"]) >= split_time - 0.01:
                    split_idx = w_i
                    break

            if split_idx <= 0 or split_idx >= len(words):
                return False

            left_words = words[:split_idx]
            right_words = words[split_idx:]

            seg1 = dict(target_seg)
            seg1["end"] = left_words[-1].get("end", split_time)
            seg1["words"] = left_words
            seg1["text"] = " ".join(w.get("word", "") for w in left_words)

            seg2 = dict(target_seg)
            seg2["start"] = right_words[0].get("start", split_time)
            seg2["words"] = right_words
            seg2["text"] = " ".join(w.get("word", "") for w in right_words)
        else:
            seg_text = target_seg.get("text", "").split()
            if len(seg_text) < 2:
                return False

            seg_start = float(target_seg.get("start", split_time))
            seg_end = float(target_seg.get("end", split_time))
            duration = max(0.0, seg_end - seg_start)
            ratio = max(0.0, min(1.0, (float(split_time) - seg_start) / duration)) if duration > 0 else 0.5
            split_word = max(1, min(len(seg_text) - 1, round(len(seg_text) * ratio)))

            seg1 = dict(target_seg)
            seg1["end"] = float(split_time)
            seg1["text"] = " ".join(seg_text[:split_word])

            seg2 = dict(target_seg)
            seg2["start"] = float(split_time)
            seg2["text"] = " ".join(seg_text[split_word:])

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        orig_spk_name = self.get_effective_speaker_name(seg_idx, target_seg)
        segments[seg_idx] = seg1
        segments.insert(seg_idx + 1, seg2)

        new_overrides = {}
        for idx_k, spk in self.segment_speaker_overrides.items():
            k = int(idx_k)
            if k <= seg_idx:
                new_overrides[k] = spk
            else:
                new_overrides[k + 1] = spk
        self.segment_speaker_overrides = new_overrides

        if new_speaker_name:
            target_spk = str(new_speaker_name).strip()
            section_indices = [seg_idx + 1]
            for i in range(seg_idx + 2, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == orig_spk_name:
                    section_indices.append(i)
                else:
                    break

            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target_spk
                self.segment_speaker_overrides[idx] = override_key

        self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Add Speaker Label{' (' + str(new_speaker_name) + ')' if new_speaker_name else ''}"
            )

        segments[seg_idx].pop("embedding", None)
        segments[seg_idx + 1].pop("embedding", None)

        left_speaker = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        right_speaker = self.get_effective_speaker_name(seg_idx + 1, segments[seg_idx + 1])

        self.register_confirmed_speaker_turn(seg_idx, left_speaker)
        self.register_confirmed_speaker_turn(seg_idx + 1, right_speaker)
        
        self.save_project()
        self.render_transcript()
        return True

    def prompt_rename_custom_speaker(self, old_name):
        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        new_name, accepted = QInputDialog.getText(
            self,
            "Rename Speaker",
            f"Enter new name for {old_name}:",
            QLineEdit.EchoMode.Normal,
            old_name,
        )
        if accepted and new_name.strip():
            self.speaker_names[f"CUSTOM_{old_name}"] = new_name.strip()
            self.add_custom_speaker_to_glossary(new_name.strip())
            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Rename Speaker: {old_name} → {new_name.strip()}")
            self.render_transcript()
            self.save_project()

    def display_speaker(self, speaker):
        if speaker is None:
            return ""

        speaker = str(speaker)
        custom_name = self.speaker_names.get(speaker)
        if custom_name:
            return custom_name

        match = re.search(r"(\d+)$", speaker)
        if match:
            number = int(match.group(1)) + 1
            return f"Speaker {number}"

        return speaker

    def get_all_known_speakers(self):
        speakers = set()
        if hasattr(self, "speaker_names") and self.speaker_names:
            for k, v in self.speaker_names.items():
                if v and isinstance(v, str) and v.strip() and not k.startswith("SEG_"):
                    speakers.add(v.strip())
        if getattr(self, "transcript", None) and isinstance(self.transcript, dict) and "segments" in self.transcript:
            for idx, seg in enumerate(self.transcript["segments"]):
                name = self.get_effective_speaker_name(idx, seg)
                if name and name.strip():
                    speakers.add(name.strip())
        diar_data = getattr(self, "diarization_result", None) or getattr(self, "diarization", None)
        if isinstance(diar_data, dict) and "segments" in diar_data:
            for seg in diar_data["segments"]:
                spk = seg.get("speaker")
                if spk:
                    disp = self.display_speaker(spk)
                    if disp and disp.strip():
                        speakers.add(disp.strip())
        if hasattr(self, "custom_speakers") and self.custom_speakers:
            for spk in self.custom_speakers:
                if spk and isinstance(spk, str) and spk.strip():
                    speakers.add(spk.strip())

        def natural_sort_key(s):
            is_speaker_num = s.startswith("Speaker ") and s[8:].isdigit()
            if is_speaker_num:
                return (0, int(s[8:]), s.lower())
            return (1, 0, [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)])

        return sorted(speakers, key=natural_sort_key)

    def execute_speaker_rename(self, seg_idx, raw_speaker, target_name):
        if not self.transcript or "segments" not in self.transcript:
            return
        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return

        v_scroll_before = self.transcript_view.verticalScrollBar().value() if hasattr(self, "transcript_view") and self.transcript_view else 0
        h_scroll_before = self.transcript_view.horizontalScrollBar().value() if hasattr(self, "transcript_view") and self.transcript_view else 0

        current_name = (
            self.get_effective_speaker_name(seg_idx, segments[seg_idx])
            if seg_idx < len(segments)
            else self.display_speaker(raw_speaker)
        )

        if target_name == "__NEW__":
            new_name, accepted = QInputDialog.getText(
                self,
                "New Speaker Name",
                f"Enter new name for '{current_name}':",
                QLineEdit.EchoMode.Normal,
                "",
            )
            if not accepted or not new_name.strip():
                if hasattr(self, "transcript_view") and self.transcript_view:
                    self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
                return
            target_name = new_name.strip()
        else:
            target_name = str(target_name).strip()

        if not target_name or target_name == current_name:
            if hasattr(self, "transcript_view") and self.transcript_view:
                self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
            return

        spk_dlg = ChangeSpeakerDialog(current_name, target_name, seg_idx=seg_idx, parent=self)
        spk_dlg.exec()
        if spk_dlg.choice not in ("all", "subsequent", "single"):
            if hasattr(self, "transcript_view") and self.transcript_view:
                self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=200)
            return

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        if spk_dlg.choice == "all":
            if raw_speaker:
                self.speaker_names[str(raw_speaker)] = target_name
            self.add_custom_speaker_to_glossary(target_name)
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == current_name:
                    override_key = f"SEG_{idx}_SPEAKER"
                    self.speaker_names[override_key] = target_name
                    self.segment_speaker_overrides[idx] = override_key
        elif spk_dlg.choice == "subsequent":
            self.add_custom_speaker_to_glossary(target_name)
            start_seg_idx = seg_idx if seg_idx >= 0 else 0
            for idx in range(start_seg_idx, len(segments)):
                if self.get_effective_speaker_name(idx, segments[idx]) == current_name:
                    override_key = f"SEG_{idx}_SPEAKER"
                    self.speaker_names[override_key] = target_name
                    self.segment_speaker_overrides[idx] = override_key

            if self.diarization and isinstance(self.diarization, dict):
                sec_start = float(segments[start_seg_idx].get("start", 0.0))
                if "segments" in self.diarization:
                    for d_seg in self.diarization["segments"]:
                        d_start = float(d_seg.get("start", 0.0))
                        if d_start >= sec_start:
                            disp = self.display_speaker(str(d_seg.get("speaker", "")))
                            if disp == current_name or d_seg.get("speaker") == current_name:
                                d_seg["speaker"] = target_name
                    self._diar_index_key = None
        elif spk_dlg.choice == "single":
            section_indices = []
            for i in range(seg_idx, len(segments)):
                if self.get_effective_speaker_name(i, segments[i]) == current_name:
                    section_indices.append(i)
                else:
                    break

            if not section_indices:
                section_indices = [seg_idx]

            self.add_custom_speaker_to_glossary(target_name)
            for idx in section_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target_name
                self.segment_speaker_overrides[idx] = override_key

            if self.diarization and isinstance(self.diarization, dict):
                sec_start = float(segments[section_indices[0]].get("start", 0.0))
                sec_end = float(segments[section_indices[-1]].get("end", sec_start))
                if "segments" in self.diarization:
                    for d_seg in self.diarization["segments"]:
                        d_start = float(d_seg.get("start", 0.0))
                        d_end = float(d_seg.get("end", 0.0))
                        if d_start < sec_end and d_end > sec_start:
                            disp = self.display_speaker(str(d_seg.get("speaker", "")))
                            if disp == current_name or d_seg.get("speaker") == current_name:
                                d_seg["speaker"] = target_name
                    self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, f"Change Speaker: {current_name} → {target_name}")

        if hasattr(self, "transcript_view") and self.transcript_view:
            self.transcript_view.lock_scroll_position(v_scroll_before, h_scroll_before, duration_ms=400)

        self.render_transcript()
        self.save_project()
        self.statusBar().showMessage(f"Updated speaker to: {target_name}")

    def prompt_rename_speaker(self, seg_idx, speaker):
        self.execute_speaker_rename(seg_idx, speaker, "__NEW__")

    def remove_speaker_label_at_segment(self, seg_idx):
        if not self.transcript or "segments" not in self.transcript:
            return False

        segments = self.transcript.get("segments", [])
        if seg_idx <= 0 or seg_idx >= len(segments):
            return False

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        prev_seg_idx = seg_idx - 1
        target_name = self.get_effective_speaker_name(prev_seg_idx, segments[prev_seg_idx])
        target_raw = (
            self.segment_speaker_overrides.get(prev_seg_idx) 
            or self.speaker_for_segment(segments[prev_seg_idx])
        )

        removed_name = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        section_indices = []
        for i in range(seg_idx, len(segments)):
            if self.get_effective_speaker_name(i, segments[i]) == removed_name:
                section_indices.append(i)
            else:
                break

        if not section_indices:
            return False

        section_indices_set = set(section_indices)

        for idx in section_indices:
            instance_key = f"SEG_{idx}_SPEAKER"
            self.speaker_names[instance_key] = target_name
            self.segment_speaker_overrides[idx] = instance_key

        if self.diarization and isinstance(self.diarization, dict):
            sec_start = float(segments[section_indices[0]].get("start", 0.0))
            sec_end = float(segments[section_indices[-1]].get("end", sec_start))
            diar_segs = self.diarization.get("segments", [])
            updated_diar = False
            new_diar_speaker = target_raw or f"SEG_{prev_seg_idx}_SPEAKER"

            for d_seg in diar_segs:
                d_start = float(d_seg.get("start", 0.0))
                d_end = float(d_seg.get("end", d_start))
                overlap = min(sec_end, d_end) - max(sec_start, d_start)
                if overlap <= 0.001:
                    continue

                best_seg_idx = None
                best_seg_overlap = 0.0

                for s_idx in section_indices:
                    t_seg = segments[s_idx]
                    t_start = float(t_seg.get("start", 0.0))
                    t_end = float(t_seg.get("end", t_start))
                    cur_overlap = min(t_end, d_end) - max(t_start, d_start)
                    if cur_overlap > best_seg_overlap:
                        best_seg_overlap = cur_overlap
                        best_seg_idx = s_idx

                if best_seg_idx in section_indices_set:
                    d_seg["speaker"] = new_diar_speaker
                    updated_diar = True

            if updated_diar:
                self._diar_index_key = None

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Remove Speaker Label: {removed_name} → {target_name} (turn at #{seg_idx + 1})"
            )

        self.save_project()
        self.render_transcript()
        self.statusBar().showMessage(f"Removed '{removed_name}' label at {format_time(segments[seg_idx].get('start', 0))}.")
        return True

    def register_confirmed_speaker_turn(self, seg_idx: int, speaker_name: str):
        """
        Active learning hook: When a user confirms or splits a speaker turn,
        extract its clean acoustic slice and add it to that speaker's reference bank.
        """
        if not speaker_name or not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript.get("segments", [])
        if not (0 <= seg_idx < len(segments)):
            return

        name = speaker_name.strip()
        emb = self.get_segment_embedding(seg_idx)
        if not emb:
            return

        if not hasattr(self, "_session_speaker_profiles"):
            self._session_speaker_profiles = {}

        if name not in self._session_speaker_profiles:
            self._session_speaker_profiles[name] = []

        # Maintain up to 6 confirmed reference vectors per speaker
        self._session_speaker_profiles[name].append(emb)
        if len(self._session_speaker_profiles[name]) > 6:
            self._session_speaker_profiles[name].pop(0)

        if hasattr(self, "log_activity"):
            self.log_activity(
                f"[VOICE MODEL] Updated acoustic signature for '{name}' "
                f"from confirmed turn #{seg_idx + 1} ({len(self._session_speaker_profiles[name])} sample(s)).",
                mark_dirty=False,
            )

    def refine_speaker_run_between_confirmed_anchors(
        self, start_idx: int, end_idx: int, spk_a: str, spk_b: str
    ):
        """
        Competitive classifier: For all turns between start_idx and end_idx,
        assign to spk_a or spk_b based on relative cosine distance rather than a static threshold.
        """
        if not hasattr(self, "_session_speaker_profiles"):
            return

        prof_a = self._session_speaker_profiles.get(spk_a)
        prof_b = self._session_speaker_profiles.get(spk_b)
        if not prof_a or not prof_b:
            return

        from speaker_identity import centroid, cosine_similarity
        cA = centroid(prof_a)
        cB = centroid(prof_b)
        if cA is None or cB is None:
            return

        segments = self.transcript.get("segments", []) if self.transcript else []
        reassigned = 0

        for idx in range(start_idx, min(end_idx + 1, len(segments))):
            emb = self.get_segment_embedding(idx)
            if not emb:
                continue

            simA = cosine_similarity(emb, cA)
            simB = cosine_similarity(emb, cB)

            winner = spk_a if simA >= simB else spk_b
            curr = self.get_effective_speaker_name(idx, segments[idx])

            if winner != curr:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = winner
                self.segment_speaker_overrides[idx] = override_key
                reassigned += 1

        if reassigned > 0:
            self._diar_index_key = None
            self.render_transcript()
            self.save_project()
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(
                    f"Refined {reassigned} turn(s) between '{spk_a}' and '{spk_b}'.", 4000
                )
  
    def get_segment_embedding(self, seg_idx: int) -> Optional[List[float]]:
        """
        Retrieve a genuine 256-dimensional acoustic embedding for this segment.
        Extracts on-the-fly directly from any media container (.mp4, .mkv, .wav, etc.)
        using ffmpeg piped to memory.
        """
        if not self.transcript or "segments" not in self.transcript:
            return None

        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return None

        seg = segments[seg_idx]
        st = float(seg.get("start", 0.0))
        en = float(seg.get("end", st))
        dur = en - st

        if dur < 0.35:
            return None

        # 1. Use existing clean embedding if already present
        embedding = seg.get("embedding")
        if isinstance(embedding, (list, tuple)) and len(embedding) == 256:
            try:
                return [float(x) for x in embedding]
            except (TypeError, ValueError):
                pass

        # 2. Resolve media file path
        media_path = (
            getattr(self, "audio_file", None)
            or getattr(self, "media_file", None)
            or getattr(self, "current_media_path", None)
            or getattr(self, "audio_path", None)
        )
        if not media_path or not os.path.exists(str(media_path)):
            if hasattr(self, "project_metadata") and hasattr(self.project_metadata, "media_path"):
                media_path = self.project_metadata.media_path

        if not media_path or not os.path.exists(str(media_path)):
            return None

        # 3. Extract genuine acoustic slice embedding via ffmpeg PCM pipe
        try:
            import subprocess
            import numpy as np
            import wespeakerruntime as wespeaker_rt
            import torchaudio.compliance.kaldi as kaldi
            import torch
            from prs_shared import ffmpeg_path

            ff_exe = ffmpeg_path() or "ffmpeg"

            # Pipe exactly this time window decoded to 16kHz mono raw float32/int16
            cmd = [
                str(ff_exe),
                "-ss", f"{st:.3f}",
                "-t", f"{dur:.3f}",
                "-i", str(media_path),
                "-vn", "-sn", "-dn",
                "-ac", "1",
                "-ar", "16000",
                "-f", "s16le",
                "pipe:1"
            ]

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                creationflags=creationflags
            )

            raw_bytes = proc.stdout
            if len(raw_bytes) < int(0.25 * 16000 * 2):  # Require at least 250ms of audio
                return None

            data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Compute 80-bin filterbank features
            chunk_wave = torch.from_numpy(data).unsqueeze(0) * (1 << 15)
            mat = kaldi.fbank(
                chunk_wave,
                num_mel_bins=80,
                frame_length=25,
                frame_shift=10,
                dither=0.0,
                sample_frequency=16000,
                window_type="hamming",
                use_energy=False,
            ).numpy()
            mat = mat - np.mean(mat, axis=0)

            # Lazy-load WeSpeaker model on the main window instance
            if not hasattr(self, "_wespeaker_model") or self._wespeaker_model is None:
                self._wespeaker_model = wespeaker_rt.Speaker(lang="en")

            single_in = np.expand_dims(mat, 0).astype(np.float32)
            emb = self._wespeaker_model.session.run(
                output_names=["embs"], input_feed={"feats": single_in}
            )[0][0]

            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            vector = [round(float(x), 6) for x in emb.tolist()]
            seg["embedding"] = vector  # Cache vector so future checks are instantaneous
            return vector

        except Exception as exc:
            print(f"[DEBUG] Slice extraction failed for seg #{seg_idx + 1} ({st:.2f}s - {en:.2f}s): {exc}")
            return None

    def get_composite_embedding(self, seg_indices: List[int]) -> Optional[List[float]]:
        if not seg_indices:
            return None
        vectors = []
        for idx in seg_indices:
            embedding = self.get_segment_embedding(idx)
            if embedding is not None:
                vectors.append(embedding)
        if not vectors:
            return None
        return centroid(vectors)

    def _build_voice_profile_candidates(self, ref_indices: List[int]) -> List[Tuple[int, List[float]]]:
        if not self.transcript or "segments" not in self.transcript:
            return []

        segments = self.transcript.get("segments", [])
        ref_set = set(ref_indices)
        candidates = []

        for idx, segment in enumerate(segments):
            if idx in ref_set:
                continue

            # Skip micro-segments under 0.6 seconds where embeddings suffer high timbral variance
            st = float(segment.get("start", 0.0))
            en = float(segment.get("end", st))
            if (en - st) < 0.6:
                continue

            embedding = self.get_segment_embedding(idx)
            if embedding is None:
                continue

            candidates.append((idx, embedding))

        return candidates

    def find_matching_voice_turns(
        self,
        ref_seg_idx: int,
        threshold: float = 0.78,
        scope_cluster_only: bool = False,
        ref_seg_indices: Optional[List[int]] = None,
    ) -> List[dict]:
        """Find transcript turns acoustically matching a verified voice."""
        if not self.transcript or "segments" not in self.transcript:
            return []

        segments = self.transcript.get("segments", [])
        if ref_seg_idx < 0 or ref_seg_idx >= len(segments):
            return []

        if ref_seg_indices:
            reference_indices = [int(i) for i in ref_seg_indices if 0 <= int(i) < len(segments)]
        else:
            reference_indices = [ref_seg_idx]

        if ref_seg_idx not in reference_indices:
            reference_indices.insert(0, ref_seg_idx)

        reference_vectors = []
        for idx in reference_indices:
            embedding = self.get_segment_embedding(idx)
            if embedding is not None:
                reference_vectors.append(embedding)

        # Include any confirmed reference samples accumulated this session for this speaker
        reference_name = self.get_effective_speaker_name(ref_seg_idx, segments[ref_seg_idx])
        if hasattr(self, "_session_speaker_profiles"):
            session_vectors = self._session_speaker_profiles.get(reference_name, [])
            reference_vectors.extend(session_vectors)
            
        if not reference_vectors:
            return []

        # Target profile is constructed STRICTLY from explicitly chosen reference vectors.
        # This completely prevents candidate turns from corrupting the enrolled voice.
        target_profile = centroid(reference_vectors)
        if target_profile is None:
            return []

        candidates = self._build_voice_profile_candidates(reference_indices)
        reference_name = self.get_effective_speaker_name(ref_seg_idx, segments[ref_seg_idx])

        # Form competitor profiles from turns assigned to OTHER names
        competing_groups = {}
        same_cluster_embeddings = []
        for idx, embedding in candidates:
            speaker = self.get_effective_speaker_name(idx, segments[idx])
            if speaker != reference_name:
                competing_groups.setdefault(speaker, []).append((idx, embedding))
            else:
                same_cluster_embeddings.append((idx, embedding))

        # In-group sub-clustering: if a single cluster contains an imposter voice,
        # discover outliers in the same cluster that diverge from target_profile
        # and treat them as an internal competitor.
        internal_competitor = None
        divergent_indices = set()
        if same_cluster_embeddings:
            divergent_items = [
                (i, v) for i, v in same_cluster_embeddings
                if cosine_similarity(v, target_profile) < 0.72
            ]
            if len(divergent_items) >= 2:
                internal_competitor = centroid([v for _, v in divergent_items[:10]])
                divergent_indices = {i for i, _ in divergent_items}

        matches = []

        for idx, embedding in candidates:
            if scope_cluster_only:
                speaker = self.get_effective_speaker_name(idx, segments[idx])
                if speaker != reference_name:
                    continue

            # Build competitor profiles for THIS candidate turn (excluding candidate's own embedding)
            item_competitor_profiles = []
            for spk_name, items in competing_groups.items():
                other_vecs = [v for (i, v) in items if i != idx]
                if other_vecs:
                    c_prof = centroid(other_vecs[:12])
                    if c_prof is not None:
                        item_competitor_profiles.append(c_prof)

            if internal_competitor is not None and idx not in divergent_indices:
                item_competitor_profiles.append(internal_competitor)

            has_competitors = len(item_competitor_profiles) > 0

            comparison = compare_against_profiles(
                embedding,
                target_profile,
                item_competitor_profiles,
            )

            if not is_confident_match(
                comparison,
                threshold=threshold,
                margin=0.035,
                has_competitors=has_competitors,
            ):
                continue

            segment = segments[idx]
            matches.append({
                "seg_idx": idx,
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "speaker": self.get_effective_speaker_name(idx, segment),
                "similarity": round(comparison.target_similarity, 4),
                "margin": round(comparison.margin, 4),
                "competitor_similarity": round(comparison.competitor_similarity, 4),
                "text": segment.get("text", "").strip(),
            })

        matches.sort(
            key=lambda item: (item["similarity"], item["margin"]),
            reverse=True,
        )
        return matches

    def match_acoustic_voice_profile(
        self,
        ref_seg_idx: int,
        target_speaker: str,
        threshold: float = 0.78,
        scope_cluster_only: bool = False,
        selected_indices: Optional[List[int]] = None,
        ref_seg_indices: Optional[List[int]] = None,
    ) -> int:
        if not self.transcript or "segments" not in self.transcript or not target_speaker:
            return 0

        segments = self.transcript.get("segments", [])
        if ref_seg_idx < 0 or ref_seg_idx >= len(segments):
            return 0

        target_name = target_speaker.strip()
        if not target_name:
            return 0

        if selected_indices is None:
            matches = self.find_matching_voice_turns(
                ref_seg_idx,
                threshold=threshold,
                scope_cluster_only=scope_cluster_only,
                ref_seg_indices=ref_seg_indices,
            )
            selected_indices = [match["seg_idx"] for match in matches]

        all_to_reassign = set(selected_indices or [])
        if ref_seg_indices:
            all_to_reassign.update(int(idx) for idx in ref_seg_indices if 0 <= int(idx) < len(segments))
        else:
            all_to_reassign.add(ref_seg_idx)

        if not all_to_reassign:
            return 0

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()

        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None

        for idx in sorted(all_to_reassign):
            instance_key = f"SEG_{idx}_SPEAKER"
            self.speaker_names[instance_key] = target_name
            self.segment_speaker_overrides[idx] = instance_key

        if isinstance(getattr(self, "diarization", None), dict):
            diar_segments = self.diarization.get("segments", [])
            for idx in sorted(all_to_reassign):
                if idx >= len(segments):
                    continue
                transcript_segment = segments[idx]
                t_start = float(transcript_segment.get("start", 0.0))
                t_end = float(transcript_segment.get("end", t_start))

                for diar_segment in diar_segments:
                    d_start = float(diar_segment.get("start", 0.0))
                    d_end = float(diar_segment.get("end", d_start))
                    overlap = min(t_end, d_end) - max(t_start, d_start)
                    if overlap > 0.01:
                        diar_segment["speaker"] = f"SEG_{idx}_SPEAKER"

            self._diar_index_key = None

        if hasattr(self, "add_custom_speaker_to_glossary"):
            self.add_custom_speaker_to_glossary(target_name)

        count = len(all_to_reassign)
        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Acoustic Voice Identification: {count} turn(s) → '{target_name}'",
            )

        self.log_activity(
            f"[SPEAKER] Voice Identification: {count} confirmed turn(s) assigned to '{target_name}'."
        )
        self.save_project()
        self.render_transcript()
        self.statusBar().showMessage(
            f"Voice identification complete: {count} turn(s) assigned to '{target_name}'."
        )
        return count

    def teach_voice_profile_dialog(
        self,
        seg_idx: int,
        raw_speaker: str = None,
        prompt_new_speaker: bool = False,
    ):
        if not self.transcript or "segments" not in self.transcript:
            QMessageBox.information(
                self,
                "No Transcript Loaded",
                "Please open or transcribe a project before using the Acoustic Voice Profile Matcher.",
            )
            return

        segments = self.transcript.get("segments", [])
        if seg_idx < 0 or seg_idx >= len(segments):
            return

        current_speaker = self.get_effective_speaker_name(seg_idx, segments[seg_idx])
        dlg = VoiceProfileMatchDialog(
            ref_seg_idx=seg_idx,
            current_speaker=current_speaker,
            target_speaker="" if prompt_new_speaker else current_speaker,
            prompt_new_speaker=prompt_new_speaker,
            parent=self,
        )

        if dlg.exec() == QDialog.DialogCode.Accepted:
            active_refs = dlg.get_active_ref_indices()
            self.match_acoustic_voice_profile(
                ref_seg_idx=seg_idx,
                target_speaker=dlg.target_name,
                threshold=dlg.thresh_slider.value() / 100.0,
                scope_cluster_only=dlg.scope_cluster_radio.isChecked(),
                selected_indices=dlg.selected_indices,
                ref_seg_indices=active_refs,
            )

    def sync_segment_words(self, segment, new_text, word_formats=None):
        if not isinstance(segment, dict):
            return

        old_words = segment.get("words")
        new_tokens = [tok.strip() for tok in new_text.split()] if isinstance(new_text, str) else []
        seg_start = float(segment.get("start", 0.0))
        seg_end = float(segment.get("end", seg_start + 1.0))
        total_dur = max(0.01, seg_end - seg_start)

        if not old_words or not isinstance(old_words, list):
            if not new_tokens:
                segment["words"] = []
                return

            w_dur = total_dur / len(new_tokens)
            new_words = [
                {
                    "word": tok,
                    "start": round(seg_start + i * w_dur, 3),
                    "end": round(seg_start + (i + 1) * w_dur, 3),
                    "deleted": False,
                }
                for i, tok in enumerate(new_tokens)
            ]

            if word_formats:
                for idx, w_dict in enumerate(new_words):
                    if 0 <= idx < len(word_formats):
                        fmt = word_formats[idx]
                        if fmt.get("bold"): w_dict["bold"] = True
                        if fmt.get("italic"): w_dict["italic"] = True
                        if fmt.get("underline"): w_dict["underline"] = True
                        if fmt.get("strike"): w_dict["strike"] = True
                        if fmt.get("highlight"): w_dict["highlight"] = fmt["highlight"]

            segment["words"] = new_words
            return

        if not new_tokens:
            segment["words"] = []
            return

        import difflib
        old_toks = [str(w.get("word", "")).strip() for w in old_words]
        matcher = difflib.SequenceMatcher(None, [t.lower() for t in old_toks], [t.lower() for t in new_tokens])
        new_words_list = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for old_idx, new_idx in zip(range(i1, i2), range(j1, j2)):
                    w_obj = dict(old_words[old_idx])
                    w_obj["word"] = new_tokens[new_idx]
                    new_words_list.append(w_obj)
            elif tag == "replace":
                t_start = float(old_words[i1].get("start", seg_start))
                t_end = float(old_words[i2 - 1].get("end", seg_end))
                t_span = max(0.01, t_end - t_start)
                num_new = max(1, j2 - j1)
                w_dur = t_span / num_new
                for k, new_idx in enumerate(range(j1, j2)):
                    new_words_list.append({
                        "word": new_tokens[new_idx],
                        "start": round(t_start + k * w_dur, 3),
                        "end": round(t_start + (k + 1) * w_dur, 3),
                        "deleted": False,
                    })
            elif tag == "insert":
                t_start = float(old_words[i1 - 1].get("end", seg_start)) if (0 < i1 <= len(old_words)) else seg_start
                t_end = float(old_words[i1].get("start", seg_end)) if i1 < len(old_words) else seg_end
                if t_end < t_start:
                    t_end = t_start + 0.2 * (j2 - j1)
                t_span = max(0.01, t_end - t_start)
                num_new = max(1, j2 - j1)
                w_dur = t_span / num_new
                for k, new_idx in enumerate(range(j1, j2)):
                    new_words_list.append({
                        "word": new_tokens[new_idx],
                        "start": round(t_start + k * w_dur, 3),
                        "end": round(t_start + (k + 1) * w_dur, 3),
                        "deleted": False,
                    })

        if word_formats:
            for idx, w_dict in enumerate(new_words_list):
                if 0 <= idx < len(word_formats):
                    fmt = word_formats[idx]
                    if fmt.get("bold"): w_dict["bold"] = True
                    if fmt.get("italic"): w_dict["italic"] = True
                    if fmt.get("underline"): w_dict["underline"] = True
                    if fmt.get("strike"): w_dict["strike"] = True
                    if fmt.get("highlight"): w_dict["highlight"] = fmt["highlight"]

        segment["words"] = new_words_list

    def merge_speakers(self, source_speaker: str, target_speaker: str) -> bool:
        source = (source_speaker or "").strip()
        target = (target_speaker or "").strip()
        if not source or not target or source == target:
            return False
        if not self.transcript or not self.transcript.get("segments"):
            return False

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()

        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        segments = self.transcript.get("segments", [])
        reassigned_segments = 0

        for idx, seg in enumerate(segments):
            curr_name = self.get_effective_speaker_name(idx, seg)
            raw_spk = self.segment_speaker_overrides.get(idx) or seg.get("speaker")
            if curr_name == source or str(raw_spk) == source:
                override_key = f"SEG_{idx}_SPEAKER"
                self.speaker_names[override_key] = target
                self.segment_speaker_overrides[idx] = override_key
                seg["speaker"] = target
                reassigned_segments += 1

        diar_data = getattr(self, "diarization", None)
        if isinstance(diar_data, dict) and "segments" in diar_data:
            for d_seg in diar_data["segments"]:
                raw_d = str(d_seg.get("speaker", ""))
                disp_d = self.display_speaker(raw_d)
                if disp_d == source or raw_d == source:
                    d_seg["speaker"] = target

            unique_speakers = {s.get("speaker") for s in diar_data["segments"] if s.get("speaker")}
            diar_data["num_speakers"] = len(unique_speakers)
            self._diar_index_key = None

        self.speaker_names[source] = target
        if hasattr(self, "custom_speakers"):
            if source in self.custom_speakers:
                self.custom_speakers.remove(source)
            if target not in self.custom_speakers:
                self.custom_speakers.append(target)

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, f"Merge Speaker '{source}' into '{target}'")

        self.save_project()
        self.render_transcript()
        if hasattr(self, "timeline"):
            self.timeline.update()
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Merged '{source}' into '{target}'.")
        return True

    def open_speaker_manager_dialog(self):
        dialog = SpeakerManagerDialog(self)
        dialog.exec()

    def merge_contiguous_speaker_segments(self):
        if not self.transcript or "segments" not in self.transcript:
            return

        segments = self.transcript["segments"]
        if not segments:
            return

        merged_segments = []
        new_overrides = {}
        curr_block = None
        curr_effective_name = None

        for idx, seg in enumerate(segments):
            effective_name = self.get_effective_speaker_name(idx, seg)
            if curr_block is None:
                curr_block = dict(seg)
                curr_block["words"] = list(seg.get("words", []))
                curr_effective_name = effective_name
            else:
                if effective_name == curr_effective_name:
                    curr_block["end"] = seg["end"]
                    curr_block["text"] = (curr_block["text"].strip() + " " + seg.get("text", "").strip()).strip()
                    curr_block["words"].extend(seg.get("words", []))
                else:
                    merged_idx = len(merged_segments)
                    merged_segments.append(curr_block)
                    if idx - 1 in self.segment_speaker_overrides:
                        new_overrides[merged_idx] = self.segment_speaker_overrides[idx - 1]
                    curr_block = dict(seg)
                    curr_block["words"] = list(seg.get("words", []))
                    curr_effective_name = effective_name

        if curr_block:
            merged_idx = len(merged_segments)
            merged_segments.append(curr_block)
            if len(segments) - 1 in self.segment_speaker_overrides:
                new_overrides[merged_idx] = self.segment_speaker_overrides[len(segments) - 1]

        self.transcript["segments"] = merged_segments
        self.segment_speaker_overrides = new_overrides

    def refresh_story_list(self):
        selected_indices = list(self.current_selected_story_indices)
        self.story_list.blockSignals(True)
        self.story_list.clear()

        curve_labels = {
            "linear": "Linear",
            "s_curve": "S-Curve",
            "logarithmic": "Logarithmic",
            "exponential": "Exponential",
        }

        for index, story in enumerate(self.stories, start=1):
            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)
            fcurve = getattr(story, "fade_curve", "linear") or "linear"

            fade_parts = []
            if fin > 0: fade_parts.append(f"In:{fin:.1f}s")
            if fout > 0: fade_parts.append(f"Out:{fout:.1f}s")
            fade_badge = f"  [{' '.join(fade_parts)}]" if fade_parts else ""

            text = f"{index}. {format_time(story.start)} – {format_time(story.end)}  {story.title}{fade_badge}"
            item = QListWidgetItem(text)
            curve_name = curve_labels.get(fcurve, fcurve.capitalize())
            fade_info = f"Fade-In: {fin:.2f}s | Fade-Out: {fout:.2f}s ({curve_name} Curve)" if (fin > 0 or fout > 0) else "No Fades Applied"

            item.setToolTip(f"Story #{index}: {story.title}\nTime Range: {format_time(story.start)} – {format_time(story.end)}\n{fade_info}")
            item.setData(Qt.ItemDataRole.UserRole, story.to_dict())
            self.story_list.addItem(item)

        for idx in selected_indices:
            if 0 <= idx < self.story_list.count():
                self.story_list.item(idx).setSelected(True)

        self.story_list.blockSignals(False)
        self.timeline.set_stories(self.stories, selected_indices)
        if hasattr(self, "update_story_list_height"):
            self.update_story_list_height()
        if hasattr(self, "notify_story_selection_to_plugins"):
            st = self.stories[selected_indices[0]] if (len(selected_indices) == 1 and 0 <= selected_indices[0] < len(self.stories)) else None
            self.notify_story_selection_to_plugins(st)

    def handle_new_story_started(self, start_time, end_time):
        self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]
        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        default_title = "Untitled Song" if is_music else "Untitled Story"
        story = Story(start=start_time, end=end_time, title=default_title)
        self.stories.append(story)
        self.refresh_story_list()
        self.story_selection_changed()
        self.start_input.setText(format_time(story.start))
        self.end_input.setText(format_time(story.end))
        self.title_input.setText(story.title)

    def handle_new_story_updated(self, start_time, end_time):
        if self.stories:
            story = self.stories[-1]
            story.start = start_time
            story.end = end_time
            self.start_input.setText(format_time(story.start))
            self.end_input.setText(format_time(story.end))
            if hasattr(self, "story_list") and self.story_list.count() > 0:
                last_idx = self.story_list.count() - 1
                item = self.story_list.item(last_idx)
                if item:
                    item.setText(f"{len(self.stories)}. {format_time(story.start)} – {format_time(story.end)}  {story.title}")
                    item.setData(Qt.ItemDataRole.UserRole, story.to_dict())

    def handle_drag_story_region(self, index, start_time, end_time):
        if not self.pre_drag_stories_snapshot:
            self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]

        if 0 <= index < len(self.stories):
            story = self.stories[index]
            story.start = start_time
            story.end = end_time
            if self.current_selected_story_indices != [index]:
                self.apply_story_selection_indices([index], seek=False)
            else:
                self.start_input.setText(format_time(story.start))
                self.end_input.setText(format_time(story.end))

    def audition_story(self, index: int):
        if not (0 <= index < len(self.stories)):
            return

        story = self.stories[index]
        self._audition_story_index = index
        self.apply_story_selection_indices([index], seek=False)
        self.seek_to(story.start)

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            fin = getattr(story, "fade_in", 0.0)
            if fin > 0 and hasattr(self, "audio_output"):
                self.audio_output.setVolume(0.0)
                self._last_applied_fade_vol = 0.0

        self.player.play()

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            if hasattr(self, "fade_preview_timer"):
                self.fade_preview_timer.start(35)
            self.update_realtime_fade_volume()

        self.timeline.set_playing_state(True)
        self.play_button.setText("❚❚ Pause")

    def handle_drag_finished(self):
        if self.pre_drag_stories_snapshot:
            old_stories = self.pre_drag_stories_snapshot
            self.pre_drag_stories_snapshot = []
            changed_idx = None

            for i in range(min(len(old_stories), len(self.stories))):
                if (abs(old_stories[i].start - self.stories[i].start) > 0.001 or abs(old_stories[i].end - self.stories[i].end) > 0.001):
                    changed_idx = i
                    break

            if changed_idx is not None and hasattr(self, "undo_stack"):
                old_start = old_stories[changed_idx].start
                old_end = old_stories[changed_idx].end
                new_start = self.stories[changed_idx].start
                new_end = self.stories[changed_idx].end
                desc = f"Adjust Story #{changed_idx + 1} Boundary"

                self.stories[changed_idx].start = old_start
                self.stories[changed_idx].end = old_end

                cmd = StoryBoundaryChangeCommand(
                    self, changed_idx, old_start, old_end, new_start, new_end, desc
                )
                self.undo_stack.push(cmd)
            else:
                new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
                self.commit_story_change(old_stories, new_stories, "Adjust Story Selection")
                self.refresh_story_list()
                self.save_project()

    def update_selected_story(self):
        selected_rows = list(self.current_selected_story_indices)
        if not selected_rows:
            return

        try:
            start = parse_time(self.start_input.text())
            end = parse_time(self.end_input.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Time", str(exc))
            return

        if end <= start:
            QMessageBox.warning(self, "Invalid Story", "End time must be after start time.")
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        new_stories[index].start = start
        new_stories[index].end = end
        new_stories[index].title = self.title_input.text().strip() or "Untitled Story"

        author_val = self.author_input.text().strip() if hasattr(self, "author_input") else ""
        excerpt_val = self.excerpt_edit.toPlainText().strip() if hasattr(self, "excerpt_edit") else ""

        if not hasattr(new_stories[index], "metadata") or new_stories[index].metadata is None:
            new_stories[index].metadata = {}

        old_author = old_stories[index].metadata.get("author", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""
        old_excerpt = old_stories[index].metadata.get("excerpt", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""

        new_stories[index].metadata["author"] = author_val
        new_stories[index].metadata["excerpt"] = excerpt_val

        start_changed = abs(new_stories[index].start - old_stories[index].start) >= 0.001
        end_changed = abs(new_stories[index].end - old_stories[index].end) >= 0.001
        title_changed = new_stories[index].title != old_stories[index].title
        author_changed = author_val != old_author
        excerpt_changed = excerpt_val != old_excerpt

        if not (start_changed or end_changed or title_changed or author_changed or excerpt_changed):
            return

        if (start_changed or end_changed) and not title_changed and not author_changed and not excerpt_changed and hasattr(self, "undo_stack"):
            desc = f"Adjust Story #{index + 1} Boundary"
            cmd = StoryBoundaryChangeCommand(
                self, index, old_stories[index].start, old_stories[index].end, new_stories[index].start, new_stories[index].end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
            return

        self.commit_story_change(old_stories, new_stories, "Update Story Details")
        self.apply_story_selection_indices([index], seek=False)

    def delete_selected_story(self):
        selected_rows = sorted(list(self.current_selected_story_indices), reverse=True)
        if not selected_rows:
            return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for idx in selected_rows:
            del new_stories[idx]

        count = len(selected_rows)
        self.apply_story_selection_indices([], seek=False)

        if hasattr(self, "timeline") and hasattr(self.timeline, "canvas"):
            self.timeline.canvas.selection_start = None
            self.timeline.canvas.selection_end = None
            self.timeline.canvas.selectionRangeChanged.emit(None, None)
            self.timeline.canvas.update()

        desc = f"Delete {term if count == 1 else term_plural}"
        self.commit_story_change(old_stories, new_stories, desc)

    def get_current_interaction_time(self, for_boundary="start"):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            return s if for_boundary == "start" else e

        if hasattr(self, "transcript_view"):
            if self.transcript_view.has_active_selection():
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range:
                    return sel_range[0] if for_boundary == "start" else sel_range[1]

            if getattr(self, "last_position_source", None) == "transcript":
                last_ts = getattr(self, "last_transcript_cursor_time", None)
                if last_ts is not None and last_ts >= 0:
                    return last_ts

        return getattr(self, "current_position", 0.0)

    def set_selected_story_start(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="start")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time >= current_story.end:
            QMessageBox.warning(
                self, "Invalid Boundary", f"Start time ({format_time(target_time)}) must be earlier than story end time ({format_time(current_story.end)})."
            )
            return

        if abs(target_time - current_story.start) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} Start Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, target_time, current_story.end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=True)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].start = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=True)
            self.mark_project_dirty(desc)
            self.save_project()

    def set_selected_story_end(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="end")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time <= current_story.start:
            QMessageBox.warning(
                self, "Invalid Boundary", f"End time ({format_time(target_time)}) must be later than story start time ({format_time(current_story.start)})."
            )
            return

        if abs(target_time - current_story.end) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} End Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, current_story.start, target_time, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].end = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=False)
            self.mark_project_dirty(desc)
            self.save_project()

    def add_selection_to_story(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges:
            cursor = self.transcript_view.textCursor()
            if not cursor.hasSelection():
                QMessageBox.information(
                    self, "No Selection", "Highlight a portion of the transcript first to create a story from it."
                )
                return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        if len(ranges) > 1:
            old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
            created_stories = []

            for r in ranges:
                s_time = r.get("start_time", 0.0)
                e_time = r.get("end_time", s_time + 1.0)
                if e_time <= s_time:
                    e_time = s_time + 1.0
                text = r.get("text", "").strip()
                words = text.split()
                t = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"
                created_stories.append(Story(start=s_time, end=e_time, title=t))

            new_stories = sorted(old_stories + created_stories, key=lambda s: s.start)
            if hasattr(self, "commit_story_change"):
                self.commit_story_change(old_stories, new_stories, f"Add {len(created_stories)} {term_plural} from Multi-Selection")
            else:
                self.stories = new_stories
                self.refresh_story_list()

            new_indices = [new_stories.index(s) for s in created_stories]
            if hasattr(self, "apply_story_selection_indices"):
                self.apply_story_selection_indices(new_indices)

            self.transcript_view.clear_all_selections()
            self.statusBar().showMessage(f"Created {len(created_stories)} {term_plural.lower()} from multiple selections.")
            return

        start_time = None
        end_time = None
        selected_text = ""

        if ranges:
            start_time = ranges[0].get("start_time")
            end_time = ranges[0].get("end_time")
            selected_text = ranges[0].get("text", "")
        else:
            cursor = self.transcript_view.textCursor()
            selected_text = cursor.selectedText().strip()
            if hasattr(self.transcript_view, "get_selected_time_range"):
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range and sel_range[0] is not None and sel_range[1] is not None:
                    start_time, end_time = sel_range

        if start_time is None or end_time is None:
            cursor = self.transcript_view.textCursor()
            start_char = cursor.selectionStart()
            end_char = cursor.selectionEnd()
            char_map = getattr(self.transcript_view, "char_timestamp_map", [])

            for (c_start, c_end, w_start, w_end, _) in char_map:
                if c_start <= start_char <= c_end and start_time is None:
                    start_time = w_start
                if c_start <= end_char <= c_end:
                    end_time = w_end

        if start_time is None:
            start_time = getattr(self, "current_position", 0.0)
        if end_time is None:
            end_time = min(getattr(self, "duration", start_time + 5.0), start_time + 5.0)

        if end_time <= start_time:
            end_time = start_time + 1.0

        words = selected_text.split()
        default_title = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(start_time))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(end_time))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=start_time, end=end_time, title=default_title)
        old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda s: s.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add {term} from Selection: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.transcript_view.clear_all_selections()
        self.statusBar().showMessage(f"Created {term.lower()}: {default_title}")

    def play_transcript_selection(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges and hasattr(self.transcript_view, "get_selected_time_range"):
            tr = self.transcript_view.get_selected_time_range()
            if tr and tr[0] is not None:
                ranges = [{"start_time": tr[0], "end_time": tr[1]}]

        if ranges:
            start_t = ranges[0].get("start_time", 0.0)
            self.seek_to(start_t)
            if hasattr(self, "player") and hasattr(self, "toggle_play"):
                from PySide6.QtMultimedia import QMediaPlayer
                if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self.toggle_play()

    def select_all_stories(self):
        if not getattr(self, "stories", []):
            return
        all_indices = list(range(len(self.stories)))
        self.apply_story_selection_indices(all_indices)
        if hasattr(self, "timeline"):
            self.timeline.set_stories(self.stories, all_indices)
        self.statusBar().showMessage(f"Selected all {len(self.stories)} stories.")

    def handle_timeline_selection_range_changed(self, start_time, end_time):
        if not hasattr(self, "transcript_view"):
            return

        if start_time is None or end_time is None:
            cursor = self.transcript_view.textCursor()
            if cursor.hasSelection():
                cursor.clearSelection()
                self.transcript_view.setTextCursor(cursor)
            return

        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        char_map = getattr(self.transcript_view, "char_timestamp_map", [])
        if not char_map:
            return

        first_char = None
        last_char = None

        for item in char_map:
            c_start = item[0]
            c_end = item[1]
            w_start = item[2]
            w_end = item[3] if len(item) >= 4 else w_start

            if w_end >= s and first_char is None:
                first_char = c_start
            if w_start <= e:
                last_char = c_end

        if first_char is not None and last_char is not None and last_char > first_char:
            cursor = self.transcript_view.textCursor()
            cursor.setPosition(first_char)
            cursor.setPosition(last_char, QTextCursor.MoveMode.KeepAnchor)
            self.transcript_view.setTextCursor(cursor)
            self.transcript_view.ensureCursorVisible()

    def add_story_from_range(self, start_time, end_time):
        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        if e <= s:
            e = s + 1.0

        default_title = "New Story"
        if hasattr(self, "transcript_for_range"):
            segs = self.transcript_for_range(s, e)
            words = " ".join(seg.get("text", "").strip() for seg in segs).split()
            if words:
                default_title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(s))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(e))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=s, end=e, title=default_title)
        old_stories = [Story.from_dict(item.to_dict()) for item in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda item: item.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add Story: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.statusBar().showMessage(f"Created story: {default_title}")

    def add_story_from_active_selection(self):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()
            self.add_story_from_range(s, e)
            return

        if hasattr(self, "transcript_view") and self.transcript_view.has_active_selection():
            self.add_selection_to_story()
            return

        QMessageBox.information(
            self, "No Selection", "Make a selection first by right-click dragging across the timeline or highlighting transcript text."
        )

    def open_story_fades_dialog(self, story_index=None):
        if not hasattr(self, "stories") or not self.stories:
            QMessageBox.information(self, "No Stories", "There are no stories created yet.")
            return

        if story_index is None:
            if hasattr(self, "current_selected_story_indices") and self.current_selected_story_indices:
                story_index = self.current_selected_story_indices[0]
            else:
                story_index = 0

        if not (0 <= story_index < len(self.stories)):
            return

        story = self.stories[story_index]
        dlg = StoryFadesDialog(self, story=story, story_index=story_index)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_in, new_out, new_curve, apply_all = dlg.get_fades()
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

            if apply_all:
                for s in new_stories:
                    s.fade_in = new_in
                    s.fade_out = new_out
                    s.fade_curve = new_curve
                desc = "Set Audio Fades on All Stories"
            else:
                new_stories[story_index].fade_in = new_in
                new_stories[story_index].fade_out = new_out
                new_stories[story_index].fade_curve = new_curve
                desc = f"Set Audio Fades on Story #{story_index + 1}"

            if hasattr(self, "undo_stack"):
                self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, desc))
            else:
                self.stories = new_stories
                self.refresh_story_list()
                if hasattr(self, "timeline"):
                    self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                    self.timeline.update()
                self.save_project()

    def apply_fades_to_selected_stories(self, fade_in=None, fade_out=None, fade_curve=None):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        if fade_in is None:
            fade_in = float(settings.value("default_fade_in_duration", 0.0))
        if fade_out is None:
            fade_out = float(settings.value("default_fade_out_duration", 1.0))
        if fade_curve is None:
            fade_curve = str(settings.value("default_fade_curve", "linear") or "linear")

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_in = fade_in
                new_stories[i].fade_out = fade_out
                new_stories[i].fade_curve = fade_curve

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, "Apply Audio Fades to Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def remove_fades_from_selected_stories(self):
        self.apply_fades_to_selected_stories(fade_in=0.0, fade_out=0.0)

    def set_fade_curve_for_selected_stories(self, curve_type: str):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_curve = curve_type

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, f"Set Fade Curve ({curve_type}) on Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def open_story_metadata_dialog(self, target_story_index: Optional[int] = None):
        from story_metadata_dialog import StoryMetadataDialog
        if target_story_index is None and getattr(self, "current_selected_story_indices", None):
            target_story_index = self.current_selected_story_indices[0]

        dlg = StoryMetadataDialog(self, main_window=self, target_story_index=target_story_index)
        dlg.exec()


class StoryFadesDialog(QDialog):
    """Dialog for fine-grained numerical adjustment of audio fade-in and fade-out durations."""

    def __init__(self, parent=None, story=None, story_index=0):
        super().__init__(parent)
        self.main_win = parent
        self.story = story
        self.story_index = story_index
        self._initial_fades = []
        if self.main_win and hasattr(self.main_win, "stories"):
            self._initial_fades = [
                (getattr(s, "fade_in", 0.0), getattr(s, "fade_out", 0.0), getattr(s, "fade_curve", "linear") or "linear")
                for s in self.main_win.stories
            ]
        self._has_applied = False
        title = story.title if story and getattr(story, "title", None) else f"Story #{story_index + 1}"
        self.setWindowTitle(f"Audio Fades — {title}")
        self.resize(450, 310)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        story_dur = max(0.01, (self.story.end - self.story.start)) if self.story else 10.0
        header_text = (
            f"<b>Story #{self.story_index + 1}: {html.escape(self.story.title if self.story else '')}</b><br>"
            f"<span style='color: #8b949e;'>Duration: {format_time(story_dur, include_millis=True)} ({story_dur:.2f}s)</span>"
        )
        header_label = QLabel(header_text, self)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)

        form_group = QGroupBox("Audio Fade Durations & Profile", self)
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(14, 14, 14, 14)
        form_layout.setSpacing(10)

        self.fade_in_spin = QDoubleSpinBox(self)
        self.fade_in_spin.setRange(0.0, story_dur)
        self.fade_in_spin.setSingleStep(0.1)
        self.fade_in_spin.setDecimals(2)
        self.fade_in_spin.setSuffix(" s")
        curr_in = getattr(self.story, "fade_in", 0.0) if self.story else 0.0
        self.fade_in_spin.setValue(curr_in)
        form_layout.addRow("Fade In Duration:", self.fade_in_spin)

        self.fade_out_spin = QDoubleSpinBox(self)
        self.fade_out_spin.setRange(0.0, story_dur)
        self.fade_out_spin.setSingleStep(0.1)
        self.fade_out_spin.setDecimals(2)
        self.fade_out_spin.setSuffix(" s")
        curr_out = getattr(self.story, "fade_out", 0.0) if self.story else 0.0
        self.fade_out_spin.setValue(curr_out)
        form_layout.addRow("Fade Out Duration:", self.fade_out_spin)

        from prs_shared import FadeCurveVisualSelector
        self.fade_curve_combo = FadeCurveVisualSelector(self, button_width=86, button_height=56)
        curr_curve = getattr(self.story, "fade_curve", "linear") if self.story else "linear"
        self.fade_curve_combo.setCurrentData(curr_curve)
        form_layout.addRow("Fade Curve Profile:", self.fade_curve_combo)

        layout.addWidget(form_group)

        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:", self)
        preset_layout.addWidget(preset_label)

        btn_none = QPushButton("No Fades (0s)", self)
        btn_none.clicked.connect(lambda: (self.fade_in_spin.setValue(0.0), self.fade_out_spin.setValue(0.0)))
        preset_layout.addWidget(btn_none)

        btn_default = QPushButton("Restore Defaults", self)
        btn_default.clicked.connect(self._restore_defaults)
        preset_layout.addWidget(btn_default)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        self.apply_all_cb = QCheckBox("Apply these fade settings to all stories in project", self)
        layout.addWidget(self.apply_all_cb)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        apply_btn = QPushButton("Apply", self)
        apply_btn.setToolTip("Apply current fade curve and durations to audition live on timeline without closing")
        apply_btn.clicked.connect(self.apply_current)
        btn_box.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save Fades", self)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def apply_current(self):
        new_in, new_out, new_curve, apply_all = self.get_fades()
        if not self.main_win or not hasattr(self.main_win, "stories"):
            return

        if apply_all:
            for s in self.main_win.stories:
                s.fade_in = new_in
                s.fade_out = new_out
                s.fade_curve = new_curve
        else:
            if 0 <= self.story_index < len(self.main_win.stories):
                st = self.main_win.stories[self.story_index]
                st.fade_in = new_in
                st.fade_out = new_out
                st.fade_curve = new_curve

        if hasattr(self.main_win, "refresh_story_list"):
            self.main_win.refresh_story_list()
        if hasattr(self.main_win, "timeline"):
            self.main_win.timeline.set_stories(self.main_win.stories, getattr(self.main_win, "current_selected_story_indices", []))
            self.main_win.timeline.update()
        self._has_applied = True

    def reject(self):
        if self._has_applied and self.main_win and hasattr(self.main_win, "stories"):
            for idx, (fin, fout, fcur) in enumerate(self._initial_fades):
                if idx < len(self.main_win.stories):
                    st = self.main_win.stories[idx]
                    st.fade_in = fin
                    st.fade_out = fout
                    st.fade_curve = fcur
            if hasattr(self.main_win, "refresh_story_list"):
                self.main_win.refresh_story_list()
            if hasattr(self.main_win, "timeline"):
                self.main_win.timeline.set_stories(self.main_win.stories, getattr(self.main_win, "current_selected_story_indices", []))
                self.main_win.timeline.update()
        super().reject()

    def _restore_defaults(self):
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        def_in = float(settings.value("default_fade_in_duration", 0.0))
        def_out = float(settings.value("default_fade_out_duration", 1.0))
        def_curve = str(settings.value("default_fade_curve", "linear") or "linear")
        self.fade_in_spin.setValue(def_in)
        self.fade_out_spin.setValue(def_out)
        self.fade_curve_combo.setCurrentData(def_curve)

    def get_fades(self):
        return self.fade_in_spin.value(), self.fade_out_spin.value(), self.fade_curve_combo.currentData(), self.apply_all_cb.isChecked()


class SpeakerManagerDialog(QDialog):
    """Manager dialog for inspecting, aliasing, and merging detected speaker clusters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_win = parent
        self.setWindowTitle("Manage Speakers & Detection Clusters")
        self.resize(720, 460)
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
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
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
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            rename_btn = QPushButton("Rename / Alias", action_widget)
            rename_btn.clicked.connect(lambda _, n=name, r=info["raw"]: self._rename_speaker(n, r))
            action_layout.addWidget(rename_btn)

            merge_btn = QPushButton("Merge Into...", action_widget)
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

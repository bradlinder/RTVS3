"""voice_profile_dialog.py — Dialog for finding and reassigning matching speaker turns using acoustic voice profiles."""
from __future__ import annotations

import html
import re
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QRadioButton, QButtonGroup, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QWidget, QCheckBox, QAbstractItemView, QMessageBox,
    QFrame, QLineEdit, QInputDialog, QListWidgetItem, QDoubleSpinBox, QFormLayout,
    QProgressDialog, QApplication
)

from prs_shared import format_time, parse_time, INTERNAL_APP_ID
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode
from speaker_identity import (
    cosine_similarity,
    robust_reference_profile,
    compare_against_profiles,
    is_confident_match,
)

__all__ = ["VoiceProfileMatchDialog"]

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
        make_dialog_maximizable(self)
        apply_window_titlebar_theme(self)

        vp_mode = get_active_theme_mode("dark")

        # Precompute candidate acoustic embeddings once upon launch so threshold slider drags are instantaneous
        self.cached_candidates = []
        if self.parent_window and hasattr(self.parent_window, "_build_voice_profile_candidates"):
            res = self.parent_window._build_voice_profile_candidates(
                [self.ref_seg_idx] + self.ref_seg_indices,
                parent_widget=self.parent_window,
            )
            if isinstance(res, tuple):
                self.cached_candidates = res[0]
            else:
                self.cached_candidates = res

        # High-performance debounce timer & state guards for 60+ FPS slider responsiveness
        self._slider_timer = QTimer(self)
        self._slider_timer.setSingleShot(True)
        self._slider_timer.timeout.connect(self._update_matches)
        self._user_deselected_ids = set()
        self._is_updating_table = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Title & Description
        header_layout = QVBoxLayout()
        header_layout.setSpacing(3)

        header_top_layout = QHBoxLayout()
        title_lbl = QLabel("Acoustic Voice Profile Matcher & Re-Clustering", self)
        if vp_mode == "light":
            title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #22262c;")
        elif vp_mode == "high_contrast":
            title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        else:
            title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #f1f5f9;")
        header_top_layout.addWidget(title_lbl, 1)

        self.btn_toggle_hints = QPushButton("💡 Usage Hints", self)
        self.btn_toggle_hints.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_hints.setMaximumHeight(26)
        if vp_mode == "light":
            self.btn_toggle_hints.setStyleSheet("""
                QPushButton {
                    background-color: #e3e6ea;
                    color: #2e74b5;
                    border: 1px solid #b6bcc4;
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d0d4d9;
                    color: #205493;
                }
            """)
        elif vp_mode == "high_contrast":
            self.btn_toggle_hints.setStyleSheet("""
                QPushButton {
                    background-color: #000000;
                    color: #ffff00;
                    border: 1px solid #ffff00;
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ffff00;
                    color: #000000;
                }
            """)
        else:
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
        if vp_mode == "light":
            desc_lbl.setStyleSheet("color: #545b66; font-size: 12px;")
        elif vp_mode == "high_contrast":
            desc_lbl.setStyleSheet("color: #ffffff; font-size: 12px;")
        else:
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        header_layout.addWidget(desc_lbl)
        layout.addLayout(header_layout)

        # Collapsible Usage Hints Card
        self.hints_box = QGroupBox("💡 Acoustic Voice Profile Matcher — Quick Usage Guide", self)
        if vp_mode == "light":
            self.hints_box.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #0369a1;
                    border: 1px solid #7dd3fc;
                    border-radius: 6px;
                    margin-top: 4px;
                    padding-top: 14px;
                    background-color: #f0f9ff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        elif vp_mode == "high_contrast":
            self.hints_box.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #ffff00;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    margin-top: 4px;
                    padding-top: 14px;
                    background-color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        else:
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

        hints_color = "#0c4a6e" if vp_mode == "light" else ("#ffffff" if vp_mode == "high_contrast" else "#e0f2fe")
        hints_html = f"""
        <div style="color: {hints_color}; font-size: 11px; line-height: 1.45;">
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
        if vp_mode == "light":
            btn_minimize_hints.setStyleSheet("""
                QPushButton {
                    background-color: #2e74b5;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #205493;
                }
            """)
        elif vp_mode == "high_contrast":
            btn_minimize_hints.setStyleSheet("""
                QPushButton {
                    background-color: #ffff00;
                    color: #000000;
                    border: none;
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ffffff;
                }
            """)
        else:
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
        if vp_mode == "light":
            ref_card.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #22262c;
                    border: 1px solid #b6bcc4;
                    border-radius: 6px;
                    margin-top: 6px;
                    padding-top: 14px;
                    background-color: #eaedf0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        elif vp_mode == "high_contrast":
            ref_card.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    margin-top: 6px;
                    padding-top: 14px;
                    background-color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        else:
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
            f"<b>Primary Turn #{self.ref_seg_idx + 1}</b> • Time: <b>{ref_time_str}</b> • Current Label: <span style='color: {'#b45309' if vp_mode == 'light' else '#fbbf24'};'><b>{html.escape(self.current_speaker)}</b></span>",
            ref_card,
        )
        ref_card_layout.addWidget(ref_info_lbl)

        if ref_text:
            ref_text_lbl = QLabel(f"<i>“{html.escape(ref_text)}”</i>", ref_card)
            ref_text_lbl.setWordWrap(True)
            if vp_mode == "light":
                ref_text_lbl.setStyleSheet("color: #545b66; font-size: 12px;")
            elif vp_mode == "high_contrast":
                ref_text_lbl.setStyleSheet("color: #ffffff; font-size: 12px;")
            else:
                ref_text_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            ref_card_layout.addWidget(ref_text_lbl)

        mode_hdr = QLabel("Reference Vector Baseline Mode:", ref_card)
        if vp_mode == "light":
            mode_hdr.setStyleSheet("color: #2e74b5; font-weight: bold; font-size: 11px; margin-top: 4px;")
        elif vp_mode == "high_contrast":
            mode_hdr.setStyleSheet("color: #ffff00; font-weight: bold; font-size: 11px; margin-top: 4px;")
        else:
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
        if vp_mode == "light":
            target_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #22262c;
                    border: 1px solid #b6bcc4;
                    border-radius: 6px;
                    margin-top: 6px;
                    padding-top: 14px;
                    background-color: #eaedf0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        elif vp_mode == "high_contrast":
            target_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    margin-top: 6px;
                    padding-top: 14px;
                    background-color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        else:
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
        self.chk_master.setStyleSheet("color: #38bdf8; font-weight: bold; margin-right: 14px;")
        self.chk_master.toggled.connect(self._toggle_master_checkbox)
        table_header_layout.addWidget(self.chk_master)

        self.btn_audition = QPushButton("▶ Audition Turn", self)
        self.btn_audition.setMaximumHeight(26)
        self.btn_audition.setToolTip("Play or pause audio for the selected turn (Spacebar)")
        self.btn_audition.clicked.connect(self._toggle_audition_button)
        table_header_layout.addWidget(self.btn_audition)

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
        # Debounce the heavy table repopulation so rapid slider dragging is completely smooth (60+ FPS)
        if hasattr(self, "_slider_timer"):
            self._slider_timer.start(60)
        else:
            self._update_matches()

    def get_active_ref_indices(self) -> List[int]:
        if hasattr(self, "ref_mode_composite_radio") and self.ref_mode_composite_radio.isChecked():
            return self.cluster_seg_indices or [self.ref_seg_idx]
        elif hasattr(self, "ref_mode_selected_radio") and self.ref_mode_selected_radio.isChecked():
            return self.ref_seg_indices or [self.ref_seg_idx]
        return [self.ref_seg_idx]

    def _on_controls_changed(self):
        if hasattr(self, "_slider_timer"):
            self._slider_timer.stop()
        self._update_matches()

    def _update_matches(self):
        if not hasattr(self, "thresh_slider") or not hasattr(self, "scope_cluster_radio"):
            return
        if not self.parent_window or not hasattr(self.parent_window, "find_matching_voice_turns"):
            return

        self._is_updating_table = True
        try:
            threshold = self.thresh_slider.value() / 100.0
            scope_cluster_only = self.scope_cluster_radio.isChecked()
            active_ref_indices = self.get_active_ref_indices()
            target_name = self.spk_combo.currentText().strip() or None

            self.matched_turns = self.parent_window.find_matching_voice_turns(
                self.ref_seg_idx,
                threshold=threshold,
                scope_cluster_only=scope_cluster_only,
                ref_seg_indices=active_ref_indices,
                target_name=target_name,
                cached_candidates=getattr(self, "cached_candidates", None),
            )

            self.table.blockSignals(True)
            self.table.setUpdatesEnabled(False)
            self.table.setRowCount(len(self.matched_turns))

            for row_idx, turn in enumerate(self.matched_turns):
                seg_id = turn["seg_idx"]
                chk_item = QTableWidgetItem()
                chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                is_checked = (seg_id not in self._user_deselected_ids)
                chk_item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
                chk_item.setData(Qt.ItemDataRole.UserRole, seg_id)
                self.table.setItem(row_idx, 0, chk_item)

                st_str = format_time(turn["start"])
                en_str = format_time(turn["end"])
                seg_item = QTableWidgetItem(f"#{seg_id + 1} ({st_str} – {en_str})")
                seg_item.setToolTip(f"Segment #{seg_id + 1}\nStart: {turn['start']:.2f}s, End: {turn['end']:.2f}s")
                self.table.setItem(row_idx, 1, seg_item)

                spk_item = QTableWidgetItem(turn["speaker"])
                self.table.setItem(row_idx, 2, spk_item)

                sim_pct = turn["similarity"] * 100.0
                margin_pct = turn.get("margin", 0.0) * 100.0
                comp_sim_pct = turn.get("competitor_similarity", 0.0) * 100.0
                match_item = QTableWidgetItem(f"{sim_pct:.1f}% Match")
                match_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                match_item.setToolTip(
                    f"Acoustic Similarity: {sim_pct:.1f}%\n"
                    f"Nearest Competitor: {comp_sim_pct:.1f}%\n"
                    f"Separation Margin: +{margin_pct:.1f}%\n"
                    f"Status: Confident match exceeding sensitivity threshold"
                )
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
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.blockSignals(False)
            self._is_updating_table = False

        self._update_action_summary()

    def _select_all_matches(self):
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                seg_id = item.data(Qt.ItemDataRole.UserRole)
                if seg_id is not None:
                    self._user_deselected_ids.discard(seg_id)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self._update_action_summary()

    def _deselect_all_matches(self):
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
                seg_id = item.data(Qt.ItemDataRole.UserRole)
                if seg_id is not None:
                    self._user_deselected_ids.add(seg_id)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self._update_action_summary()

    def _toggle_master_checkbox(self, checked: bool):
        """Batch toggle every row checkbox to match the master checkbox state."""
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        target_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(target_state)
                seg_id = item.data(Qt.ItemDataRole.UserRole)
                if seg_id is not None:
                    if checked:
                        self._user_deselected_ids.discard(seg_id)
                    else:
                        self._user_deselected_ids.add(seg_id)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self._update_action_summary()
        
    def _on_table_item_changed(self, item):
        if item.column() == 0 and not getattr(self, "_is_updating_table", False):
            seg_id = item.data(Qt.ItemDataRole.UserRole)
            if seg_id is not None:
                if item.checkState() == Qt.CheckState.Unchecked:
                    self._user_deselected_ids.add(seg_id)
                else:
                    self._user_deselected_ids.discard(seg_id)
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
        if len(selected) > 0:
            self.btn_apply.setText(f"Reassign {len(selected)} Matching Turn(s) to '{target}'")
            self.btn_apply.setEnabled(True)
        elif self.ref_seg_idx >= 0:
            segs = getattr(self.parent_window, "transcript", {}).get("segments", []) if self.parent_window else []
            curr_ref_spk = ""
            if 0 <= self.ref_seg_idx < len(segs):
                curr_ref_spk = self.parent_window.get_effective_speaker_name(self.ref_seg_idx, segs[self.ref_seg_idx])
            if target and target != curr_ref_spk:
                self.btn_apply.setText(f"Reassign Reference Turn #{self.ref_seg_idx + 1} Only to '{target}'")
                self.btn_apply.setEnabled(True)
            else:
                self.btn_apply.setText(f"No Turns Selected (Reference already '{target}')")
                self.btn_apply.setEnabled(False)
        else:
            self.btn_apply.setText("No Matching Turns Selected")
            self.btn_apply.setEnabled(False)

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
        if getattr(self, "_is_updating_table", False):
            return
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
        """Intercept Spacebar on the table widget for playback and Return/Enter/X for checkbox toggling."""
        if watched == self.table and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space:
                self._toggle_audition_button()
                return True  # Event handled, do not pass to table
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_X):
                row = self.table.currentRow()
                if 0 <= row < self.table.rowCount():
                    item = self.table.item(row, 0)
                    if item:
                        new_state = (
                            Qt.CheckState.Unchecked
                            if item.checkState() == Qt.CheckState.Checked
                            else Qt.CheckState.Checked
                        )
                        item.setCheckState(new_state)
                        return True
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



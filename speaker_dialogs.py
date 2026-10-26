"""speaker_dialogs.py — Dialogs for speaker renaming, turn assignment, and cluster management."""
from __future__ import annotations

import html
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QSettings, QUrl, QEvent
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QWidget,
    QCheckBox, QAbstractItemView, QMessageBox, QFrame, QLineEdit, QInputDialog,
    QApplication, QStyledItemDelegate, QAbstractItemDelegate
)

from prs_shared import format_time, parse_time, INTERNAL_APP_ID
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme, get_active_theme_mode

__all__ = ["ChangeSpeakerDialog", "SpeakerManagerDialog", "SpeakerNameDelegate"]

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


class SpeakerNameDelegate(QStyledItemDelegate):
    """Delegate for inline double-click editing of speaker names with Tab progression."""

    def __init__(self, dialog: SpeakerManagerDialog):
        super().__init__(dialog.table)
        self.dialog = dialog

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            editor = QLineEdit(parent)
            theme_mode = get_active_theme_mode("dark")
            if theme_mode == "light":
                editor.setStyleSheet(
                    "QLineEdit { background-color: #ffffff; color: #0f172a; "
                    "border: 2px solid #2e74b5; border-radius: 4px; padding: 2px 6px; "
                    "font-size: 12px; font-weight: 600; }"
                )
            elif theme_mode == "high_contrast":
                editor.setStyleSheet(
                    "QLineEdit { background-color: #000000; color: #ffff00; "
                    "border: 2px solid #ffff00; border-radius: 4px; padding: 2px 6px; "
                    "font-size: 12px; font-weight: 600; }"
                )
            else:
                editor.setStyleSheet(
                    "QLineEdit { background-color: #0f172a; color: #38bdf8; "
                    "border: 2px solid #38bdf8; border-radius: 4px; padding: 2px 6px; "
                    "font-size: 12px; font-weight: 600; }"
                )
            QTimer.singleShot(0, editor.selectAll)
            return editor
        return super().createEditor(parent, option, index)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                row = self.dialog.table.currentRow()
                total = self.dialog.table.rowCount()
                nxt = (row + 1) % total if total > 0 else 0
                old_text = self.dialog.table.item(row, 0).text() if self.dialog.table.item(row, 0) else ""
                new_text = editor.text().strip()
                if new_text != old_text and new_text:
                    self.dialog._pending_tab_advance = nxt
                    self.commitData.emit(editor)
                    self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                else:
                    self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.RevertModelCache)
                    QTimer.singleShot(0, lambda: self.dialog._start_inline_edit_on_row(nxt))
                return True
            elif event.key() == Qt.Key.Key_Backtab:
                row = self.dialog.table.currentRow()
                total = self.dialog.table.rowCount()
                prev = (row - 1) % total if total > 0 else 0
                old_text = self.dialog.table.item(row, 0).text() if self.dialog.table.item(row, 0) else ""
                new_text = editor.text().strip()
                if new_text != old_text and new_text:
                    self.dialog._pending_tab_advance = prev
                    self.commitData.emit(editor)
                    self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                else:
                    self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.RevertModelCache)
                    QTimer.singleShot(0, lambda: self.dialog._start_inline_edit_on_row(prev))
                return True
        return super().eventFilter(editor, event)


class SpeakerManagerDialog(QDialog):
    """Manager dialog for inspecting, aliasing, and merging detected speaker clusters."""

    def __init__(self, parent=None):
        qparent = parent if isinstance(parent, QWidget) else None
        super().__init__(qparent)
        self.main_win = parent
        self.setWindowTitle("Manage Speakers & Detection Clusters")
        self.resize(880, 520)
        self.setMinimumSize(800, 460)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._stay_on_top = False
        make_dialog_maximizable(self)
        apply_window_titlebar_theme(self)

        self._sample_buttons = {}
        self._active_sample_speaker = None
        self._pending_play_pos_ms = None
        self._is_populating = False
        self._pending_tab_advance: Optional[int] = None

        self._sample_timer = QTimer(self)
        self._sample_timer.setSingleShot(True)
        self._sample_timer.timeout.connect(self._stop_sample_playback)

        self._preview_audio_output = QAudioOutput(self)
        self._preview_player = QMediaPlayer(self)
        self._preview_player.setAudioOutput(self._preview_audio_output)
        if hasattr(self.main_win, "apply_audio_output_device"):
            try:
                dev = getattr(getattr(self.main_win, "audio_output", None), "device", None)
                if callable(dev):
                    self._preview_audio_output.setDevice(dev())
            except Exception:
                pass
        if hasattr(self.main_win, "master_volume"):
            try:
                self._preview_audio_output.setVolume(float(self.main_win.master_volume))
            except Exception:
                self._preview_audio_output.setVolume(1.0)
        self._preview_player.playbackStateChanged.connect(self._on_preview_playback_state_changed)
        self._preview_player.mediaStatusChanged.connect(self._on_preview_media_status_changed)

        self._init_ui()
        self._populate()

    def _get_audio_source_url(self) -> Optional[QUrl]:
        if not self.main_win:
            return None
        audio_file = getattr(self.main_win, "audio_file", None)
        if audio_file:
            p = Path(audio_file).resolve()
            if p.exists():
                return QUrl.fromLocalFile(str(p))
        if hasattr(self.main_win, "player") and self.main_win.player:
            try:
                src = self.main_win.player.source()
                if src and not src.isEmpty():
                    return src
            except Exception:
                pass
        return None

    def _get_sample_duration(self) -> float:
        """Retrieve the configured speaker sample preview duration in seconds (default 3.0s)."""
        dur = 3.0
        if self.main_win and hasattr(self.main_win, "settings_store") and self.main_win.settings_store:
            try:
                dur = float(self.main_win.settings_store.value("speaker_sample_duration", 3.0))
            except (ValueError, TypeError):
                dur = 3.0
        return max(0.5, min(15.0, dur))

    def _find_speaker_sample_range(self, speaker_name: str) -> Optional[Tuple[float, float]]:
        """Resolve a clean representative utterance (start_s, duration_s) for the speaker cluster."""
        if not self.main_win or not getattr(self.main_win, "transcript", None):
            return None
        segments = self.main_win.transcript.get("segments", [])
        candidates = []
        for idx, seg in enumerate(segments):
            eff_name = self.main_win.get_effective_speaker_name(idx, seg) or "Unknown Speaker"
            if eff_name == speaker_name:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", start))
                dur = max(0.0, end - start)
                if dur > 0:
                    candidates.append((start, dur))

        if not candidates:
            return None

        target_dur = self._get_sample_duration()
        # Prefer longest continuous utterance >= target_dur
        long_candidates = [c for c in candidates if c[1] >= target_dur]
        if long_candidates:
            best_start, best_dur = max(long_candidates, key=lambda c: c[1])
        else:
            # First utterance if none >= target_dur
            best_start, best_dur = candidates[0]

        sample_dur = min(target_dur, best_dur) if best_dur > 0 else target_dur
        return (best_start, sample_dur)

    def _play_speaker_sample(self, speaker_name: str):
        """Play a non-blocking 3-second sample for the specified speaker without altering timeline state."""
        if self._active_sample_speaker == speaker_name:
            self._stop_sample_playback()
            return

        self._stop_sample_playback()

        source_url = self._get_audio_source_url()
        if not source_url:
            return

        sample_range = self._find_speaker_sample_range(speaker_name)
        if not sample_range:
            return

        start_sec, sample_dur = sample_range
        pos_ms = int(max(0.0, start_sec) * 1000)
        dur_ms = int(max(0.5, sample_dur) * 1000)

        if hasattr(self.main_win, "master_volume"):
            try:
                self._preview_audio_output.setVolume(float(self.main_win.master_volume))
            except Exception:
                pass

        if self._preview_player.source() != source_url:
            self._pending_play_pos_ms = pos_ms
            self._preview_player.setSource(source_url)
        else:
            self._pending_play_pos_ms = None
            self._preview_player.setPosition(pos_ms)
            self._preview_player.play()

        self._active_sample_speaker = speaker_name
        btn = self._sample_buttons.get(speaker_name)
        if btn:
            btn.setText("Stop")
            btn.setToolTip(f"Stop voice sample for {speaker_name}")

        self._sample_timer.stop()
        self._sample_timer.setInterval(dur_ms)
        self._sample_timer.start()

    def _stop_sample_playback(self):
        """Cease any active sample audio playback and reset UI button text."""
        self._sample_timer.stop()
        self._pending_play_pos_ms = None
        if hasattr(self, "_preview_player"):
            try:
                self._preview_player.pause()
            except Exception:
                pass
        if self._active_sample_speaker:
            btn = self._sample_buttons.get(self._active_sample_speaker)
            if btn:
                btn.setText("Play Sample")
                btn.setToolTip("Listen to a 3-second sample of this speaker's voice")
            self._active_sample_speaker = None

    def _on_preview_playback_state_changed(self, state):
        if state != QMediaPlayer.PlaybackState.PlayingState:
            if self._active_sample_speaker:
                self._stop_sample_playback()

    def _on_preview_media_status_changed(self, status):
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if self._pending_play_pos_ms is not None:
                pos = self._pending_play_pos_ms
                self._pending_play_pos_ms = None
                self._preview_player.setPosition(pos)
                self._preview_player.play()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        theme_mode = get_active_theme_mode("dark")
        if theme_mode == "light":
            b_bg, b_fg, b_bd, h_bg, h_fg = "#e3e6ea", "#2e74b5", "#2e74b5", "#2e74b5", "#ffffff"
        elif theme_mode == "high_contrast":
            b_bg, b_fg, b_bd, h_bg, h_fg = "#000000", "#ffff00", "#ffff00", "#ffff00", "#000000"
        else:
            b_bg, b_fg, b_bd, h_bg, h_fg = "#1e293b", "#38bdf8", "#0284c7", "#0284c7", "#ffffff"

        hdr_btn_qss = (
            f"QPushButton {{ background-color: {b_bg}; color: {b_fg}; border: 1px solid {b_bd}; border-radius: 4px; padding: 3px 10px; font-size: 11px; font-weight: 500; }}\n"
            f"QPushButton:hover {{ background-color: {h_bg}; color: {h_fg}; }}\n"
            f"QPushButton:checked {{ background-color: {h_bg}; color: {h_fg}; font-weight: bold; }}"
        )

        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(0, 0, 0, 0)
        hdr_row.setSpacing(8)

        desc = QLabel(
            "<b>Speakers & Detection Clusters</b> — Inspect all detected speaker clusters, rename / assign global aliases, or merge redundant clusters."
        )
        desc.setWordWrap(True)
        hdr_row.addWidget(desc, 1)

        self.refresh_btn = QPushButton("Refresh", self)
        self.refresh_btn.setToolTip("Refresh speaker clusters and turn counts from active transcript")
        self.refresh_btn.setStyleSheet(hdr_btn_qss)
        self.refresh_btn.clicked.connect(self._populate)
        hdr_row.addWidget(self.refresh_btn)

        self.float_btn = QPushButton("Pin on Top", self)
        self.float_btn.setCheckable(True)
        self.float_btn.setToolTip(
            "This window is non-modal so you can freely edit the transcript in the main window. "
            "Toggle 'Pin on Top' to keep this window above the main window while co-editing."
        )
        self.float_btn.setStyleSheet(hdr_btn_qss)
        self.float_btn.toggled.connect(self.toggle_float_mode)
        hdr_row.addWidget(self.float_btn)

        layout.addLayout(hdr_row)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Speaker Name / Alias", "Cluster / Raw ID", "Turns", "Total Duration", "Actions"
        ])
        header_item = self.table.horizontalHeaderItem(0)
        if header_item:
            header_item.setToolTip("Double-click any name to edit inline; press Tab to jump directly to the next speaker")
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 330)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.table.setItemDelegateForColumn(0, SpeakerNameDelegate(self))
        self.table.itemChanged.connect(self._on_table_item_changed)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.merge_all_btn = QPushButton("Merge Two Speakers...", self)
        self.merge_all_btn.clicked.connect(self._on_quick_merge)
        btn_row.addWidget(self.merge_all_btn)

        self.btn_voice_profiles = QPushButton("Manage Voice Profiles...", self)
        self.btn_voice_profiles.setToolTip("Open the persistent station voice profiles library")
        self.btn_voice_profiles.clicked.connect(self._on_open_voice_profiles)
        btn_row.addWidget(self.btn_voice_profiles)

        btn_row.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _populate(self):
        self._is_populating = True
        try:
            self._stop_sample_playback()
            self._sample_buttons.clear()
            self.table.setRowCount(0)
            if not self.main_win or not getattr(self.main_win, "transcript", None):
                return

            source_url = self._get_audio_source_url()
            if source_url and self._preview_player.source() != source_url:
                self._preview_player.setSource(source_url)

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
                name_item.setFlags(
                    name_item.flags()
                    | Qt.ItemFlag.ItemIsEditable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                name_item.setData(Qt.ItemDataRole.UserRole, name)
                name_item.setData(Qt.ItemDataRole.UserRole + 1, info["raw"])
                name_item.setToolTip("Double-click to rename this speaker directly (press Tab to advance to next speaker)")
                self.table.setItem(row, 0, name_item)

                raw_item = QTableWidgetItem(info["raw"])
                raw_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                raw_item.setFlags(raw_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, raw_item)

                turns_item = QTableWidgetItem(str(info["turns"]))
                turns_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                turns_item.setFlags(turns_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, turns_item)

                dur_item = QTableWidgetItem(format_time(info["duration"]))
                dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                dur_item.setFlags(dur_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, dur_item)

                action_widget = QWidget(self)
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(6, 4, 6, 4)
                action_layout.setSpacing(6)

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
                    QPushButton:disabled {
                        background-color: #0f172a;
                        color: #64748b;
                        border-color: #334155;
                    }
                """

                sample_btn = QPushButton("Play Sample", action_widget)
                sample_btn.setStyleSheet(btn_style)
                sample_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                sample_range = self._find_speaker_sample_range(name)
                if not source_url or not sample_range:
                    sample_btn.setEnabled(False)
                    sample_btn.setToolTip("No audio sample available for this speaker" if source_url else "No audio media loaded for this project")
                else:
                    sample_btn.setToolTip(f"Listen to a {sample_range[1]:.1f}s sample of {name}'s voice")
                    sample_btn.clicked.connect(lambda _, n=name: self._play_speaker_sample(n))
                self._sample_buttons[name] = sample_btn
                action_layout.addWidget(sample_btn)

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
        finally:
            self._is_populating = False

        if self._pending_tab_advance is not None:
            nxt = self._pending_tab_advance
            self._pending_tab_advance = None
            QTimer.singleShot(0, lambda: self._start_inline_edit_on_row(nxt))

    def _start_inline_edit_on_row(self, row: int):
        total = self.table.rowCount()
        if total <= 0:
            return
        target_row = row % total
        self.table.setCurrentCell(target_row, 0)
        item = self.table.item(target_row, 0)
        if item:
            self.table.editItem(item)

    def _on_table_item_changed(self, item: QTableWidgetItem):
        if self._is_populating or item.column() != 0:
            return
        old_name = item.data(Qt.ItemDataRole.UserRole)
        raw_id = item.data(Qt.ItemDataRole.UserRole + 1)
        new_name = item.text().strip()

        if not old_name:
            return

        if not new_name or new_name == old_name:
            self._is_populating = True
            try:
                item.setText(old_name)
            finally:
                self._is_populating = False
            if self._pending_tab_advance is not None:
                nxt = self._pending_tab_advance
                self._pending_tab_advance = None
                QTimer.singleShot(0, lambda: self._start_inline_edit_on_row(nxt))
            return

        self._apply_speaker_rename(old_name, new_name, raw_id)

    def _rename_speaker(self, current_name, raw_id):
        self._stop_sample_playback()
        new_name, accepted = QInputDialog.getText(
            self, "Rename Speaker Alias",
            f"Enter new display alias for '{current_name}':",
            QLineEdit.EchoMode.Normal, current_name
        )
        if accepted and new_name.strip() and new_name.strip() != current_name:
            self._apply_speaker_rename(current_name, new_name.strip(), raw_id)

    def _apply_speaker_rename(self, current_name: str, target: str, raw_id: Any):
        if not self.main_win:
            return
        self._stop_sample_playback()
        if hasattr(self.main_win, "flush_pending_transcript_undo"):
            self.main_win.flush_pending_transcript_undo()
        if hasattr(self.main_win, "_capture_project_state"):
            before_state = self.main_win._capture_project_state()
        elif hasattr(self.main_win, "get_project_state"):
            before_state = self.main_win.get_project_state()
        else:
            before_state = None
        is_unknown = current_name.strip().lower() in ("unknown speaker", "unknown", "unassigned")
        if not is_unknown:
            self.main_win.speaker_names[str(raw_id)] = target
            self.main_win.speaker_names[current_name] = target
        else:
            self.main_win.speaker_names.pop("Unknown Speaker", None)
            self.main_win.speaker_names.pop("unknown speaker", None)
        self.main_win.add_custom_speaker_to_glossary(target)

        segments = self.main_win.transcript.get("segments", [])
        for idx, seg in enumerate(segments):
            curr = self.main_win.get_effective_speaker_name(idx, seg)
            matches = False
            if curr == current_name:
                matches = True
            elif is_unknown:
                if not curr or curr.strip().lower() in ("unknown speaker", "unknown", "unassigned", "none", ""):
                    matches = True

            if matches:
                override_key = f"SEG_{idx}_SPEAKER"
                self.main_win.speaker_names[override_key] = target
                self.main_win.segment_speaker_overrides[idx] = override_key
                seg["speaker"] = target

        if before_state is not None and hasattr(self.main_win, "_commit_project_state_change"):
            self.main_win._commit_project_state_change(before_state, f"Rename Speaker: {current_name} → {target}")

        self.main_win.render_transcript()
        self.main_win.save_project()
        self._populate()

    def _merge_speaker_into(self, source_name):
        self._stop_sample_playback()
        table_speakers = [
            self.table.item(r, 0).text() for r in range(self.table.rowCount())
            if self.table.item(r, 0) and self.table.item(r, 0).text().strip()
        ]
        all_candidates = list(dict.fromkeys(table_speakers + self.main_win.get_all_known_speakers()))
        known = [s for s in all_candidates if s != source_name]
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
        self._stop_sample_playback()
        table_speakers = [
            self.table.item(r, 0).text() for r in range(self.table.rowCount())
            if self.table.item(r, 0) and self.table.item(r, 0).text().strip()
        ]
        known = list(dict.fromkeys(table_speakers + self.main_win.get_all_known_speakers()))
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

    def _on_open_voice_profiles(self):
        self._stop_sample_playback()
        if hasattr(self.main_win, "open_manage_voice_profiles_dialog"):
            self.main_win.open_manage_voice_profiles_dialog()
            self._populate()

    def reject(self):
        self._stop_sample_playback()
        super().reject()

    def accept(self):
        self._stop_sample_playback()
        super().accept()

    def closeEvent(self, event):
        self._stop_sample_playback()
        super().closeEvent(event)

    def toggle_float_mode(self, pinned: Optional[bool] = None):
        """Toggle whether the non-modal floating window stays pinned on top of other windows."""
        if pinned is None:
            pinned = not getattr(self, "_stay_on_top", False)
        self._stay_on_top = bool(pinned)
        if hasattr(self, "float_btn"):
            self.float_btn.blockSignals(True)
            self.float_btn.setChecked(self._stay_on_top)
            self.float_btn.setText("Pinned on Top" if self._stay_on_top else "Pin on Top")
            self.float_btn.blockSignals(False)
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._stay_on_top)
        if was_visible:
            self.show()
            apply_window_titlebar_theme(self)
            self.raise_()
            self.activateWindow()

    def changeEvent(self, event):
        super().changeEvent(event)
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowActivate:
            self._populate()

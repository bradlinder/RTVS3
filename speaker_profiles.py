"""
speaker_profiles.py — Persistent Station Voice Profile Manager & Storage Engine.

Provides:
- StationVoiceProfile: Data class representing an acoustic voice identity vector and metadata.
- StationVoiceProfileStore: Thread-safe persistent JSON storage in application data directory.
- ManageVoiceProfilesDialog: Dialog for browsing, renaming, auditing, manually adding,
  exporting, importing, or deleting recurring speaker acoustic profiles.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core_utils import (
    apply_window_titlebar_theme,
    get_active_theme_mode,
    make_dialog_maximizable,
)
from prs_shared import format_time, get_app_data_dir, safe_replace
from speaker_identity import (
    VECTOR_DIMENSION,
    VoiceMatch,
    _as_vector,
    centroid,
    compare_against_profiles,
    cosine_similarity,
    is_confident_match,
    normalize_vector,
    robust_reference_profile,
)


@dataclass
class StationVoiceProfile:
    id: str
    name: str
    vector: List[float]
    sample_count: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    notes: str = ""
    source_media: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Optional["StationVoiceProfile"]:
        if not isinstance(data, dict):
            return None
        vec = _as_vector(data.get("vector"))
        if vec is None:
            return None
        return cls(
            id=str(data.get("id", "") or f"spk_{int(time.time() * 1000)}"),
            name=str(data.get("name", "Unknown Voice")).strip() or "Unknown Voice",
            vector=vec,
            sample_count=int(data.get("sample_count", 1) or 1),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            notes=str(data.get("notes", "")),
            source_media=str(data.get("source_media", "")),
        )


class StationVoiceProfileStore:
    """Persistent storage manager for recurring station voice acoustic profiles."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            self.storage_dir = Path(get_app_data_dir())
        else:
            self.storage_dir = Path(storage_dir)
        self.file_path = self.storage_dir / "voice_profiles.json"
        self._profiles: Dict[str, StationVoiceProfile] = {}
        self.load()

    def get_profiles_file_path(self) -> Path:
        return self.file_path

    def load(self) -> None:
        self._profiles.clear()
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    prof = StationVoiceProfile.from_dict(item)
                    if prof:
                        self._profiles[prof.id] = prof
            elif isinstance(data, dict) and "profiles" in data:
                for item in data["profiles"]:
                    prof = StationVoiceProfile.from_dict(item)
                    if prof:
                        self._profiles[prof.id] = prof
        except Exception:
            pass

    def save(self) -> bool:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = self.file_path.with_name(self.file_path.name + ".tmp")
            payload = {
                "version": 1,
                "count": len(self._profiles),
                "profiles": [p.to_dict() for p in self._profiles.values()],
            }
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            safe_replace(tmp_path, self.file_path)
            return True
        except Exception:
            return False

    def list_profiles(self) -> List[StationVoiceProfile]:
        return sorted(self._profiles.values(), key=lambda p: p.name.lower())

    def get_profile(self, profile_id: str) -> Optional[StationVoiceProfile]:
        return self._profiles.get(profile_id)

    def find_profile_by_name(self, name: str) -> Optional[StationVoiceProfile]:
        target = name.strip().lower()
        for p in self._profiles.values():
            if p.name.strip().lower() == target:
                return p
        return None

    def add_or_update_profile(
        self,
        name: str,
        vector: Sequence[float],
        sample_count: int = 1,
        notes: str = "",
        source_media: str = "",
        profile_id: Optional[str] = None,
    ) -> Optional[StationVoiceProfile]:
        norm_vec = _as_vector(vector)
        if norm_vec is None:
            return None
        clean_name = name.strip() or "Unnamed Voice"

        if profile_id and profile_id in self._profiles:
            prof = self._profiles[profile_id]
            prof.name = clean_name
            # If updating with additional turns, blend centroids
            if sample_count > 1:
                blended = centroid([prof.vector, norm_vec])
                if blended:
                    prof.vector = blended
            else:
                prof.vector = norm_vec
            prof.sample_count = max(prof.sample_count, sample_count)
            prof.updated_at = time.time()
            if notes:
                prof.notes = notes
            if source_media:
                prof.source_media = source_media
            self.save()
            return prof

        # Check existing by name
        existing = self.find_profile_by_name(clean_name)
        if existing:
            existing.vector = norm_vec
            existing.sample_count = max(existing.sample_count, sample_count)
            existing.updated_at = time.time()
            if notes:
                existing.notes = notes
            if source_media:
                existing.source_media = source_media
            self.save()
            return existing

        pid = profile_id or f"spk_{int(time.time() * 1000)}"
        prof = StationVoiceProfile(
            id=pid,
            name=clean_name,
            vector=norm_vec,
            sample_count=sample_count,
            created_at=time.time(),
            updated_at=time.time(),
            notes=notes,
            source_media=source_media,
        )
        self._profiles[pid] = prof
        self.save()
        return prof

    def remove_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self.save()
            return True
        return False

    def clear(self) -> None:
        self._profiles.clear()
        self.save()

    def match_vector(
        self,
        vector: Sequence[float],
        threshold: float = 0.78,
        min_margin: float = 0.04,
    ) -> Optional[Tuple[StationVoiceProfile, float, float]]:
        """
        Compare an unknown candidate vector against all saved voice profiles.
        Returns (best_profile, similarity, margin) if a confident match is found, else None.
        """
        vec = _as_vector(vector)
        if vec is None or not self._profiles:
            return None

        profiles = list(self._profiles.values())
        if len(profiles) == 1:
            sim = cosine_similarity(vec, profiles[0].vector)
            if sim >= threshold:
                return profiles[0], sim, 1.0
            return None

        best_p = None
        best_sim = -1.0
        second_sim = -1.0

        for p in profiles:
            sim = cosine_similarity(vec, p.vector)
            if sim > best_sim:
                second_sim = best_sim
                best_sim = sim
                best_p = p
            elif sim > second_sim:
                second_sim = sim

        margin = best_sim - max(0.0, second_sim)
        if best_sim >= threshold and margin >= min_margin and best_p is not None:
            return best_p, best_sim, margin
        return None


class ManageVoiceProfilesDialog(QDialog):
    """Management dialog for inspecting, auditing, adding, or deleting persistent station voice profiles."""

    def __init__(self, parent=None, store: Optional[StationVoiceProfileStore] = None, main_win=None):
        super().__init__(parent)
        self.main_win = main_win or parent
        self.store = store or StationVoiceProfileStore()
        self.setWindowTitle("Manage Voice Profiles")
        self.resize(840, 520)
        self.setMinimumSize(780, 460)
        make_dialog_maximizable(self)
        apply_window_titlebar_theme(self)

        self._init_ui()
        self._populate_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header description
        desc_lbl = QLabel(
            "<b>Manage Voice Profiles</b><br>"
            "Persistent acoustic profiles for recurring hosts, news anchors, and contributors. "
            "Profiles automatically identify and tag known speakers across recordings.",
            self,
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Voice Profile Name", "Samples / Turns", "Created", "Source / Notes", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 210)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom button toolbar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_teach_active = QPushButton("Add Active Turn as Profile...", self)
        self.btn_teach_active.setToolTip("Create a new persistent voice profile using the current selection in the timeline or transcript")
        self.btn_teach_active.clicked.connect(self._on_add_from_active_turn)
        btn_layout.addWidget(self.btn_teach_active)

        self.btn_import = QPushButton("Import...", self)
        self.btn_import.setToolTip("Import voice profiles from an external JSON file")
        self.btn_import.clicked.connect(self._on_import)
        btn_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton("Export...", self)
        self.btn_export.setToolTip("Export voice profiles to a JSON file")
        self.btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(self.btn_export)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Close", self)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _populate_table(self):
        self.table.setRowCount(0)
        profiles = self.store.list_profiles()
        self.table.setRowCount(len(profiles))

        btn_style = """
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """

        for row, prof in enumerate(profiles):
            self.table.setRowHeight(row, 44)

            name_item = QTableWidgetItem(prof.name)
            name_item.setData(Qt.ItemDataRole.UserRole, prof.id)
            self.table.setItem(row, 0, name_item)

            samples_item = QTableWidgetItem(f"{prof.sample_count} turns")
            samples_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, samples_item)

            created_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(prof.created_at))
            created_item = QTableWidgetItem(created_str)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, created_item)

            notes_display = prof.notes or prof.source_media or "—"
            notes_item = QTableWidgetItem(notes_display)
            self.table.setItem(row, 3, notes_item)

            # Actions
            action_w = QWidget(self)
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 2, 4, 2)
            action_l.setSpacing(6)

            rename_btn = QPushButton("Rename", action_w)
            rename_btn.setStyleSheet(btn_style)
            rename_btn.clicked.connect(lambda _, pid=prof.id, pnm=prof.name: self._on_rename(pid, pnm))
            action_l.addWidget(rename_btn)

            match_btn = QPushButton("Match Project", action_w)
            match_btn.setStyleSheet(btn_style)
            match_btn.setToolTip("Scan current project segments for this voice profile")
            match_btn.clicked.connect(lambda _, p=prof: self._on_match_project(p))
            action_l.addWidget(match_btn)

            del_btn = QPushButton("Delete", action_w)
            del_btn.setStyleSheet(btn_style)
            del_btn.clicked.connect(lambda _, pid=prof.id, pnm=prof.name: self._on_delete(pid, pnm))
            action_l.addWidget(del_btn)

            self.table.setCellWidget(row, 4, action_w)

    def _on_rename(self, profile_id: str, old_name: str):
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Voice Profile",
            f"Enter new name for voice profile '{old_name}':",
            QLineEdit.EchoMode.Normal,
            old_name,
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            prof = self.store.get_profile(profile_id)
            if prof:
                prof.name = new_name.strip()
                self.store.save()
                self._populate_table()

    def _on_delete(self, profile_id: str, name: str):
        res = QMessageBox.question(
            self,
            "Delete Voice Profile",
            f"Are you sure you want to delete the voice profile '{name}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            self.store.remove_profile(profile_id)
            self._populate_table()

    def _on_match_project(self, prof: StationVoiceProfile):
        if not self.main_win or not getattr(self.main_win, "transcript", None):
            QMessageBox.information(self, "No Transcript", "Please load an audio recording and transcript first.")
            return
        segs = self.main_win.transcript.get("segments", [])
        if not segs:
            QMessageBox.information(self, "Empty Transcript", "No transcript segments found to match.")
            return

        # Score segments with embeddings
        matches = []
        for idx, s in enumerate(segs):
            emb = s.get("embedding")
            if not emb:
                continue
            sim = cosine_similarity(prof.vector, emb)
            if sim >= 0.75:
                matches.append((idx, sim, s))

        if not matches:
            QMessageBox.information(
                self,
                "No Matches Found",
                f"No transcript segments matched '{prof.name}' above 75% similarity.",
            )
            return

        res = QMessageBox.question(
            self,
            "Matches Found",
            f"Found {len(matches)} segment(s) matching '{prof.name}' (highest: {max(m[1] for m in matches):.1%}).\n"
            f"Would you like to assign '{prof.name}' to these segments?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if res == QMessageBox.StandardButton.Yes:
            matched_indices = [m[0] for m in matches]
            before_state = self.main_win.get_project_state() if hasattr(self.main_win, "get_project_state") else None
            for idx in matched_indices:
                override_key = f"SEG_{idx}_SPEAKER"
                self.main_win.speaker_names[override_key] = prof.name
                self.main_win.segment_speaker_overrides[idx] = override_key
            if before_state is not None and hasattr(self.main_win, "_commit_project_state_change"):
                self.main_win._commit_project_state_change(before_state, f"Match Voice Profile: {prof.name}")
            if hasattr(self.main_win, "render_transcript"):
                self.main_win.render_transcript()
            if hasattr(self.main_win, "save_project"):
                self.main_win.save_project()
            if hasattr(self.main_win, "statusBar"):
                self.main_win.statusBar().showMessage(f"Assigned '{prof.name}' to {len(matched_indices)} segment(s).")
            QMessageBox.information(self, "Assigned", f"Successfully assigned '{prof.name}' to {len(matched_indices)} segment(s).")

    def _on_add_from_active_turn(self):
        if not self.main_win or not getattr(self.main_win, "transcript", None):
            QMessageBox.information(self, "No Transcript", "Please open a project with an active transcript first.")
            return

        segments = self.main_win.transcript.get("segments", [])
        if not segments:
            QMessageBox.information(self, "Empty Transcript", "Project has no segments.")
            return

        # Infer active segment from cursor or playback
        inferred = -1
        if hasattr(self.main_win, "transcript_view"):
            cursor = self.main_win.transcript_view.textCursor()
            inferred = self.main_win.transcript_view.get_segment_index_at_cursor(cursor)
            if inferred is None or inferred < 0:
                inferred = cursor.blockNumber()
        if (inferred is None or inferred < 0 or inferred >= len(segments)) and hasattr(self.main_win, "player"):
            curr_t = (self.main_win.player.position() / 1000.0) if hasattr(self.main_win.player, "position") else 0.0
            for i, s in enumerate(segments):
                if s.get("start", 0.0) <= curr_t <= s.get("end", 0.0):
                    inferred = i
                    break
        seg_idx = inferred if (inferred is not None and 0 <= inferred < len(segments)) else 0

        # Extract embedding for selected reference turn
        vec = None
        if hasattr(self.main_win, "get_segment_embedding"):
            vec = self.main_win.get_segment_embedding(seg_idx)
        elif segments[seg_idx].get("embedding"):
            vec = segments[seg_idx]["embedding"]

        if vec is None and hasattr(self.main_win, "_build_voice_profile_candidates"):
            res = self.main_win._build_voice_profile_candidates([], parent_widget=self)
            candidates = res[0] if isinstance(res, tuple) else res
            for c_idx, c_emb in candidates:
                if c_idx == seg_idx:
                    vec = c_emb
                    break

        if vec is None:
            QMessageBox.warning(
                self,
                "No Acoustic Vector",
                "Unable to extract acoustic embedding for the selected turn. Please run Speaker Detection first.",
            )
            return

        def_name = self.main_win.get_effective_speaker_name(seg_idx, segments[seg_idx])
        name, ok = QInputDialog.getText(
            self,
            "Save Voice Profile",
            "Enter name for this recurring voice profile (e.g. 'Jane Doe (Host)'):",
            QLineEdit.EchoMode.Normal,
            def_name,
        )
        if ok and name.strip():
            source_file = Path(self.main_win.audio_file).name if getattr(self.main_win, "audio_file", None) else ""
            self.store.add_or_update_profile(
                name=name.strip(),
                vector=vec,
                sample_count=1,
                source_media=source_file,
            )
            self._populate_table()
            QMessageBox.information(self, "Profile Saved", f"Saved acoustic voice profile '{name.strip()}'.")

    def _on_export(self):
        profiles = self.store.list_profiles()
        if not profiles:
            QMessageBox.information(self, "No Profiles", "There are no voice profiles to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Voice Profiles",
            "voice_profiles.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if file_path:
            try:
                dest_p = Path(file_path)
                tmp_p = dest_p.with_name(dest_p.name + ".tmp")
                payload = {
                    "version": 1,
                    "count": len(profiles),
                    "profiles": [p.to_dict() for p in profiles],
                }
                with open(tmp_p, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                safe_replace(tmp_p, dest_p)
                QMessageBox.information(self, "Export Complete", f"Exported {len(profiles)} voice profiles to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export voice profiles:\n{e}")

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Voice Profiles",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("profiles", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                count = 0
                for item in items:
                    prof = StationVoiceProfile.from_dict(item)
                    if prof:
                        self.store.add_or_update_profile(
                            name=prof.name,
                            vector=prof.vector,
                            sample_count=prof.sample_count,
                            notes=prof.notes,
                            source_media=prof.source_media,
                            profile_id=prof.id,
                        )
                        count += 1
                self._populate_table()
                QMessageBox.information(self, "Import Complete", f"Successfully imported {count} voice profile(s).")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import voice profiles:\n{e}")

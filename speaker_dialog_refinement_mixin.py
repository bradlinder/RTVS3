"""Radio & TV Story Segmenter — Speaker Dialog Refinement & Turn Merging Mixin.

Provides:
- SpeakerDialogRefinementMixin: Competitive dialog refinement between confirmed
  speaker anchors, dialog turn classification prompts, word-level alignment diffs,
  speaker merging, and contiguous turn consolidation.
"""

from __future__ import annotations
import difflib
import html
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QMessageBox,
        QVBoxLayout,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QMessageBox,
        QVBoxLayout,
    )

from core_utils import INTERNAL_APP_ID, format_time, make_dialog_maximizable
from speaker_dialogs import SpeakerManagerDialog


class SpeakerDialogRefinementMixin:
    """Mixin for competitive speaker run refinement, word synchronization, and turn merging."""

    def refine_speaker_run_between_confirmed_anchors(
        self, start_idx: int, end_idx: int, spk_a: str, spk_b: str
    ):
        if not hasattr(self, "_session_speaker_profiles"):
            self._session_speaker_profiles = {}

        segments = self.transcript.get("segments", []) if getattr(self, "transcript", None) else []
        if not segments:
            return

        prof_a = self._session_speaker_profiles.get(spk_a)
        if not prof_a:
            prof_a = []
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == spk_a:
                    emb = self.get_segment_embedding(idx) if hasattr(self, "get_segment_embedding") else None
                    if emb:
                        prof_a.append(emb)
                        if len(prof_a) >= 4:
                            break
            if prof_a:
                self._session_speaker_profiles[spk_a] = prof_a

        prof_b = self._session_speaker_profiles.get(spk_b)
        if not prof_b:
            prof_b = []
            for idx, seg in enumerate(segments):
                if self.get_effective_speaker_name(idx, seg) == spk_b:
                    emb = self.get_segment_embedding(idx) if hasattr(self, "get_segment_embedding") else None
                    if emb:
                        prof_b.append(emb)
                        if len(prof_b) >= 4:
                            break
            if prof_b:
                self._session_speaker_profiles[spk_b] = prof_b

        if not prof_a or not prof_b:
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(
                    f"Competitive refinement requires acoustic samples for both '{spk_a}' and '{spk_b}'.", 4000
                )
            return

        from speaker_identity import centroid, cosine_similarity
        cA = centroid(prof_a)
        cB = centroid(prof_b)
        if cA is None or cB is None:
            return

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        reassigned = 0

        for idx in range(start_idx, min(end_idx + 1, len(segments))):
            emb = self.get_segment_embedding(idx) if hasattr(self, "get_segment_embedding") else None
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
            if before_state is not None and hasattr(self, "_commit_project_state_change"):
                self._commit_project_state_change(before_state, f"Refine Dialog: {spk_a} vs {spk_b}")
            self._diar_index_key = None
            self.render_transcript()
            self.save_project()
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(
                    f"Refined {reassigned} turn(s) between '{spk_a}' and '{spk_b}'.", 4000
                )

    def prompt_refine_speaker_run(self, start_idx: int = -1, end_idx: int = -1):
        if not getattr(self, "transcript", None) or "segments" not in self.transcript:
            QMessageBox.information(self, "No Transcript", "Project has no transcript segments.")
            return

        segments = self.transcript.get("segments", [])
        if not segments:
            return

        known = self.get_all_known_speakers() if hasattr(self, "get_all_known_speakers") else []
        if len(known) < 2:
            QMessageBox.information(
                self,
                "Multiple Speakers Required",
                "Competitive re-classification requires at least two distinct speaker profiles in the project.",
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Refine Rapid Dialog Turns (Competitive Classifier)")
        dlg.resize(640, 480)
        dlg.setMinimumSize(580, 420)
        make_dialog_maximizable(dlg)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info = QLabel(
            "<b>Competitive Voice Separation & Cross-Talk Resolver</b><br>"
            "Classify every turn within the selected range by relative acoustic distance between "
            "two confirmed speaker signatures rather than a fixed global threshold. "
            "Ideal for rapid-fire dialog, interviews, and alternating banter."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        spk_a_combo = QComboBox(dlg)
        spk_a_combo.addItems(known)
        form.addRow("Speaker A (Confirmed):", spk_a_combo)

        spk_b_combo = QComboBox(dlg)
        spk_b_combo.addItems(known)
        if len(known) > 1:
            spk_b_combo.setCurrentIndex(1)
        form.addRow("Speaker B (Confirmed):", spk_b_combo)

        def _format_seg_label(idx, seg):
            st = float(seg.get("start", 0.0))
            t_str = format_time(st, include_millis=getattr(self, "show_milliseconds", False))
            spk = self.get_effective_speaker_name(idx, seg) or "Speaker"
            raw_text = seg.get("text", "").strip()
            snippet = (raw_text[:38] + "…") if len(raw_text) > 38 else (raw_text or "(no speech)")
            return f"[{t_str}] Turn #{idx + 1} ({spk}): “{snippet}”"

        start_combo = QComboBox(dlg)
        start_combo.setMaxVisibleItems(15)
        start_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        start_combo.setMinimumContentsLength(40)

        end_combo = QComboBox(dlg)
        end_combo.setMaxVisibleItems(15)
        end_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        end_combo.setMinimumContentsLength(40)

        for i, seg in enumerate(segments):
            label = _format_seg_label(i, seg)
            start_combo.addItem(label, i)
            end_combo.addItem(label, i)

        init_s = max(0, min(start_idx, len(segments) - 1)) if start_idx >= 0 else 0
        init_e = max(0, min(end_idx, len(segments) - 1)) if end_idx >= 0 else (len(segments) - 1)
        start_combo.setCurrentIndex(init_s)
        end_combo.setCurrentIndex(init_e)

        form.addRow("Start Turn (Timestamp & Words):", start_combo)
        form.addRow("End Turn (Timestamp & Words):", end_combo)

        layout.addLayout(form)

        preview_box = QGroupBox("Selected Dialog Range & Context Preview", dlg)
        preview_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
                background-color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(6)

        range_summary_lbl = QLabel(preview_box)
        range_summary_lbl.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 12px;")
        preview_layout.addWidget(range_summary_lbl)

        start_preview_lbl = QLabel(preview_box)
        start_preview_lbl.setWordWrap(True)
        start_preview_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        preview_layout.addWidget(start_preview_lbl)

        end_preview_lbl = QLabel(preview_box)
        end_preview_lbl.setWordWrap(True)
        end_preview_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        preview_layout.addWidget(end_preview_lbl)

        def _update_preview():
            s_idx = start_combo.currentData()
            e_idx = end_combo.currentData()
            if s_idx is None or e_idx is None:
                return
            lo, hi = min(s_idx, e_idx), max(s_idx, e_idx)
            count = hi - lo + 1
            s_seg = segments[lo]
            e_seg = segments[hi]
            st = float(s_seg.get("start", 0.0))
            en = float(e_seg.get("end", 0.0))
            dur = max(0.0, en - st)

            range_summary_lbl.setText(
                f"Range: Turns #{lo + 1} to #{hi + 1} ({count} turn{'s' if count != 1 else ''})  •  "
                f"Time: {format_time(st)} – {format_time(en)} ({dur:.2f}s)"
            )
            s_spk = self.get_effective_speaker_name(lo, s_seg) or "Speaker"
            s_txt = s_seg.get("text", "").strip() or "(no speech)"
            start_preview_lbl.setText(
                f"<b>Start Turn #{lo + 1}</b> [{format_time(st)}] <span style='color: #fbbf24;'>{html.escape(s_spk)}</span>: "
                f"<i>“{html.escape(s_txt)}”</i>"
            )
            e_spk = self.get_effective_speaker_name(hi, e_seg) or "Speaker"
            e_txt = e_seg.get("text", "").strip() or "(no speech)"
            end_preview_lbl.setText(
                f"<b>End Turn #{hi + 1}</b> [{format_time(en)}] <span style='color: #fbbf24;'>{html.escape(e_spk)}</span>: "
                f"<i>“{html.escape(e_txt)}”</i>"
            )

        start_combo.currentIndexChanged.connect(lambda _: _update_preview())
        end_combo.currentIndexChanged.connect(lambda _: _update_preview())
        _update_preview()

        layout.addWidget(preview_box)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            a_name = spk_a_combo.currentText().strip()
            b_name = spk_b_combo.currentText().strip()
            if a_name == b_name:
                QMessageBox.warning(self, "Invalid Selection", "Speaker A and Speaker B must be different speakers.")
                return
            s_val = start_combo.currentData()
            e_val = end_combo.currentData()
            s_i = int(s_val) if s_val is not None else 0
            e_i = int(e_val) if e_val is not None else (len(segments) - 1)
            if s_i > e_i:
                s_i, e_i = e_i, s_i
            self.refine_speaker_run_between_confirmed_anchors(s_i, e_i, a_name, b_name)

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
        if not getattr(self, "transcript", None) or not self.transcript.get("segments"):
            return False

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()

        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        segments = self.transcript.get("segments", [])
        reassigned_segments = 0
        is_unknown_source = source.lower() in ("unknown speaker", "unknown", "unassigned")

        for idx, seg in enumerate(segments):
            curr_name = self.get_effective_speaker_name(idx, seg)
            raw_spk = self.segment_speaker_overrides.get(idx) or seg.get("speaker")
            matches = False
            if curr_name == source or (raw_spk and str(raw_spk) == source):
                matches = True
            elif is_unknown_source:
                if not curr_name or str(curr_name).strip().lower() in ("unknown speaker", "unknown", "unassigned", "none", ""):
                    matches = True

            if matches:
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
                elif is_unknown_source and (raw_d.lower() in ("unknown", "unknown speaker") or disp_d.lower() in ("unknown", "unknown speaker")):
                    d_seg["speaker"] = target

            unique_speakers = {s.get("speaker") for s in diar_data["segments"] if s.get("speaker")}
            diar_data["num_speakers"] = len(unique_speakers)
            self._diar_index_key = None

        if not is_unknown_source:
            self.speaker_names[source] = target
        else:
            self.speaker_names.pop("Unknown Speaker", None)
            self.speaker_names.pop("unknown speaker", None)
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
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage(f"Merged '{source}' into '{target}'.")
        return True

    def open_speaker_manager_dialog(self, modal: bool = False):
        existing = getattr(self, "_active_speaker_manager_dialog", None)
        if existing is not None and existing.isVisible():
            existing._populate()
            if existing.isMinimized():
                existing.showNormal()
            existing.raise_()
            existing.activateWindow()
            return existing

        dialog = SpeakerManagerDialog(self)
        self._active_speaker_manager_dialog = dialog

        def _on_finished(_code: int = 0):
            if getattr(self, "_active_speaker_manager_dialog", None) is dialog:
                self._active_speaker_manager_dialog = None

        dialog.finished.connect(_on_finished)
        if modal:
            dialog.exec()
            return dialog

        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def merge_contiguous_speaker_segments(self):
        if not getattr(self, "transcript", None) or "segments" not in self.transcript:
            return

        segments = self.transcript.get("segments", [])
        if not segments:
            return

        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
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

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, "Merge Contiguous Turns")

        self.render_transcript()
        self.save_project()
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage("Merged contiguous speaker turns.")

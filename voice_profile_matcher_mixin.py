"""Radio & TV Story Segmenter — Acoustic Voice Profile Matching Mixin.

Provides:
- VoiceProfileMatcherMixin: Extraction of 256-dimensional acoustic slice embeddings
  (via WeSpeaker / Kaldi filterbanks), candidate pre-caching, cosine similarity matching
  against competitor profiles, active learning confirmation, and the Teach Voice Profile dialog.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QMessageBox,
        QProgressDialog,
        QWidget,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QMessageBox,
        QProgressDialog,
        QWidget,
    )

from core_utils import safe_process_events
from speaker_identity import (
    cosine_similarity,
    robust_reference_profile,
    compare_against_profiles,
    is_confident_match,
    centroid,
)
from voice_profile_dialog import VoiceProfileMatchDialog


class VoiceProfileMatcherMixin:
    """Mixin handling WeSpeaker 256-d embeddings and acoustic voice matching."""

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

    def _build_voice_profile_candidates(
        self,
        ref_indices: List[int],
        parent_widget: Optional[QWidget] = None,
    ) -> Tuple[List[Tuple[int, List[float]]], bool]:
        """
        Precompute candidate acoustic vectors across transcript segments.
        If more than 12 uncached segments require extraction, displays a cooperative
        QProgressDialog with a Cancel button. Returns (candidates, was_canceled).
        """
        if not self.transcript or "segments" not in self.transcript:
            return [], False

        segments = self.transcript.get("segments", [])
        ref_set = set(ref_indices)

        eligible_indices = []
        uncached_count = 0
        for idx, segment in enumerate(segments):
            if idx in ref_set:
                continue
            st = float(segment.get("start", 0.0))
            en = float(segment.get("end", st))
            if (en - st) < 0.6:
                continue
            eligible_indices.append(idx)
            emb = segment.get("embedding")
            if not (isinstance(emb, (list, tuple)) and len(emb) == 256):
                uncached_count += 1

        candidates = []
        progress_dlg = None
        was_canceled = False

        if uncached_count > 12 and parent_widget is not None:
            try:
                progress_dlg = QProgressDialog(
                    "Extracting acoustic voice signatures...",
                    "Cancel",
                    0,
                    len(eligible_indices),
                    parent_widget,
                )
                progress_dlg.setWindowTitle("Analyzing Voices")
                progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
                progress_dlg.setMinimumDuration(250)
                progress_dlg.setValue(0)
            except Exception:
                progress_dlg = None

        try:
            for step, idx in enumerate(eligible_indices):
                if progress_dlg is not None:
                    if progress_dlg.wasCanceled():
                        was_canceled = True
                        break
                    progress_dlg.setValue(step)
                    progress_dlg.setLabelText(
                        f"Extracting acoustic voice signatures (turn {step + 1} of {len(eligible_indices)})..."
                    )
                    safe_process_events()

                embedding = self.get_segment_embedding(idx)
                if embedding is not None:
                    candidates.append((idx, embedding))

            if progress_dlg is not None:
                progress_dlg.setValue(len(eligible_indices))
        finally:
            if progress_dlg is not None:
                progress_dlg.close()

        return candidates, was_canceled

    def find_matching_voice_turns(
        self,
        ref_seg_idx: int,
        threshold: float = 0.78,
        scope_cluster_only: bool = False,
        ref_seg_indices: Optional[List[int]] = None,
        target_name: Optional[str] = None,
        cached_candidates: Optional[List[Tuple[int, List[float]]]] = None,
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

        reference_name = self.get_effective_speaker_name(ref_seg_idx, segments[ref_seg_idx])
        session_vectors = []
        if hasattr(self, "_session_speaker_profiles"):
            session_vectors = list(self._session_speaker_profiles.get(reference_name, []))
            if target_name and target_name != reference_name:
                session_vectors.extend(self._session_speaker_profiles.get(target_name, []))

        all_candidate_refs = reference_vectors + session_vectors
        if not all_candidate_refs:
            return []

        seed_vectors = reference_vectors[:1] if reference_vectors else all_candidate_refs[:1]
        secondary_refs = all_candidate_refs[1:]
        if secondary_refs:
            target_profile, _ = robust_reference_profile(
                seed_vectors, secondary_refs, seed_similarity=0.78
            )
            if target_profile is None:
                target_profile = centroid(all_candidate_refs)
        else:
            target_profile = seed_vectors[0]

        if target_profile is None:
            return []

        ref_set = set(reference_indices)
        if cached_candidates is not None:
            candidates = [(i, v) for i, v in cached_candidates if i not in ref_set]
        else:
            raw_c = self._build_voice_profile_candidates(reference_indices)
            candidates = raw_c[0] if isinstance(raw_c, tuple) else raw_c

        competing_groups: Dict[str, List[Tuple[int, List[float]]]] = {}
        same_cluster_embeddings: List[Tuple[int, List[float]]] = []
        excluded_names = {reference_name}
        if target_name:
            excluded_names.add(target_name)

        for idx, embedding in candidates:
            speaker = self.get_effective_speaker_name(idx, segments[idx])
            if speaker not in excluded_names:
                competing_groups.setdefault(speaker, []).append((idx, embedding))
            elif speaker == reference_name:
                same_cluster_embeddings.append((idx, embedding))

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

        base_competitor_centroids = {}
        for spk_name, items in competing_groups.items():
            if items:
                top_items = items[:12]
                c_prof = centroid([v for _, v in top_items])
                if c_prof is not None:
                    base_competitor_centroids[spk_name] = (c_prof, {i for i, _ in top_items})

        matches = []

        for idx, embedding in candidates:
            if scope_cluster_only:
                speaker = self.get_effective_speaker_name(idx, segments[idx])
                if speaker != reference_name:
                    continue

            item_competitor_profiles = []
            for spk_name, (c_prof, top_ids) in base_competitor_centroids.items():
                if idx not in top_ids:
                    item_competitor_profiles.append(c_prof)
                else:
                    items = competing_groups[spk_name]
                    other_vecs = [v for (i, v) in items if i != idx]
                    if other_vecs:
                        c_ex = centroid(other_vecs[:12])
                        if c_ex is not None:
                            item_competitor_profiles.append(c_ex)

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
                target_name=target_name,
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

        if hasattr(self, "register_confirmed_speaker_sample"):
            for idx in sorted(all_to_reassign):
                self.register_confirmed_speaker_sample(idx, target_name)

        count = len(all_to_reassign)
        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(
                before_state,
                f"Acoustic Voice Identification: {count} turn(s) → '{target_name}'",
            )

        if hasattr(self, "log_activity"):
            self.log_activity(
                f"[SPEAKER] Voice Identification: {count} confirmed turn(s) assigned to '{target_name}'."
            )
        if hasattr(self, "save_project"):
            self.save_project()
        if hasattr(self, "render_transcript"):
            self.render_transcript()
        self.statusBar().showMessage(
            f"Voice identification complete: {count} turn(s) assigned to '{target_name}'."
        )
        return count

    def teach_voice_profile_dialog(
        self,
        seg_idx: int = -1,
        raw_speaker: Optional[str] = None,
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
        if not segments:
            QMessageBox.information(
                self,
                "Empty Transcript",
                "Project has no speech segments to match voice profiles against.",
            )
            return

        if seg_idx < 0 or seg_idx >= len(segments):
            inferred = -1
            if hasattr(self, "transcript_view"):
                cursor = self.transcript_view.textCursor()
                inferred = self.transcript_view.get_segment_index_at_cursor(cursor)
                if inferred is None or inferred < 0:
                    inferred = cursor.blockNumber()
            if (inferred is None or inferred < 0 or inferred >= len(segments)) and hasattr(self, "player"):
                curr_t = (self.player.position() / 1000.0) if hasattr(self.player, "position") else 0.0
                for i, s in enumerate(segments):
                    if s.get("start", 0.0) <= curr_t <= s.get("end", 0.0):
                        inferred = i
                        break
            seg_idx = inferred if (inferred is not None and 0 <= inferred < len(segments)) else 0

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
            if getattr(dlg, "chk_save_persistent", None) and dlg.chk_save_persistent.isChecked():
                try:
                    from speaker_profiles import StationVoiceProfileStore
                    store = getattr(self, "voice_profile_store", None)
                    if store is None:
                        store = StationVoiceProfileStore()
                        self.voice_profile_store = store
                    ref_vectors = []
                    all_refs = [seg_idx] + [r for r in active_refs if r != seg_idx]
                    for r_idx in all_refs:
                        emb = self.get_segment_embedding(r_idx)
                        if emb:
                            ref_vectors.append(emb)
                    vec = centroid(ref_vectors) if ref_vectors else None
                    if vec:
                        src = Path(self.audio_file).name if getattr(self, "audio_file", None) else ""
                        store.add_or_update_profile(
                            name=dlg.target_name,
                            vector=vec,
                            sample_count=len(ref_vectors),
                            source_media=src,
                        )
                except Exception:
                    pass

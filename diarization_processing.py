"""Speaker diarization process management for Radio & TV Story Segmenter."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from prs_shared import (
    HELPER_PROTOCOL_VERSION,
    format_time,
    register_process,
    unregister_process,
)

logger = logging.getLogger(__name__)


class DiarizationProcessingMixin:
    def on_diarization_process_error(self, error):
        """Handles QProcess execution errors for the diarization process."""
        if getattr(self, "_diarization_canceled_by_user", False):
            self.cleanup_diarization_process()
            return

        if getattr(self, "diarization_result_received", False):
            self.cleanup_diarization_process()
            return

        if self.diarization_process is None:
            self.cleanup_diarization_process()
            return

        error_descriptions = {
            QProcess.ProcessError.FailedToStart: "The diarization helper process failed to start. Ensure Python and dependencies are correctly installed.",
            QProcess.ProcessError.Crashed: "The diarization helper process crashed unexpectedly (segmentation fault or unhandled native/Python exception).",
            QProcess.ProcessError.Timedout: "The diarization process timed out.",
            QProcess.ProcessError.WriteError: "An error occurred while writing to the diarization process.",
            QProcess.ProcessError.ReadError: "An error occurred while reading from the diarization process.",
            QProcess.ProcessError.UnknownError: "An unknown error occurred in the diarization process.",
        }
        desc = error_descriptions.get(
            error, f"Diarization process error occurred (code: {error})"
        )

        detail_msg = desc
        if self.diarization_output_buffer.strip():
            detail_msg += (
                f"\n\nCaptured Output Buffer:\n{self.diarization_output_buffer.strip()}"
            )

        if hasattr(self, "log_activity"):
            self.log_activity(f"[ERROR] {desc}")

        if hasattr(self, "set_processing_stage"):
            self.set_processing_stage(None)

        self.cleanup_diarization_process()

        if getattr(self, "batch_active", False):
            self.log_activity(
                "[BATCH WARNING] Diarization failed; proceeding with export using available transcript data."
            )
            self._batch_export_current()

            if self.pipeline_active and self.pipeline_queue:
                QTimer.singleShot(0, self._run_next_selected_processing)
            else:
                self.pipeline_active = False
                QTimer.singleShot(0, self._batch_next_media)
        else:
            QMessageBox.critical(
                self, "Diarization Error", f"Failed to run diarization process:\n\n{detail_msg}"
            )

    def start_diarization(self):
        self.log_activity("[SPEAKER DETECT] Speaker Detection startup requested.")
        self._diar_stage_idx = 0
        self._diar_last_raw_pct = 0.0
        self._diar_last_overall_percent = 0

        if not self.audio_file:
            self.log_activity("[SPEAKER DETECT] Aborted: no audio file is loaded.")
            self.diarization_error("No audio file is loaded.")
            return

        # Stop background thumbnail and waveform workers during heavy ML tasks to free CPU/disk I/O
        self.stop_waveform_worker()
        self.stop_video_thumbnail_worker()

        if not self.batch_active and not self.pipeline_active and not getattr(self, "pipeline_rerun_confirmed", False):
            choice = self._processing_choice("diarization")
            if choice == "cancel":
                self.log_activity("[SPEAKER DETECT] User canceled processing choice.")
                return
            elif choice == "start_over":
                self.diarization = {}
                self.processing_status["diarization"] = False
        else:
            if self.batch_active:
                self.diarization = {}
                self.processing_status["diarization"] = False

        if self.diarization_process is not None:
            self.log_activity("[SPEAKER DETECT] A job is already running.")
            return

        expected_speakers = str(getattr(self, "expected_speakers", "auto") or "auto")
        # Interactive speaker estimate: batch processing and multi-stage automated pipelines
        # are deliberately non-interactive and use auto without prompting, while standalone
        # Detect Speakers runs can still prompt if enabled.
        ask_each_time = str(self.settings_store.value("ask_expected_speakers", "true")).lower() in {"1", "true", "yes"}
        if not getattr(self, "batch_active", False) and not getattr(self, "pipeline_active", False) and ask_each_time:
            choices = [
                "Auto-Detect",
                "1 Speaker (Solo)",
                "2 Speakers (Interview)",
                "3+ Speakers (Panel / Group)",
            ]
            current_map = {"auto": 0, "1": 1, "2": 2, "3+": 3}
            choice, ok = QInputDialog.getItem(
                self,
                "Detect Speakers",
                "Estimated number of speakers:",
                choices,
                current_map.get(expected_speakers, 0),
                False,
            )
            if not ok:
                self.log_activity("[SPEAKER DETECT] Speaker estimate dialog canceled by user.")
                if getattr(self, "pipeline_active", False):
                    self.pipeline_queue = []
                    self.pipeline_active = False
                    self.pipeline_rerun_confirmed = False
                    self.set_tools_actions_enabled(True)
                return
            expected_speakers = {
                "Auto-Detect": "auto",
                "1 Speaker (Solo)": "1",
                "2 Speakers (Interview)": "2",
                "3+ Speakers (Panel / Group)": "3+",
            }.get(choice, "auto")
            self.expected_speakers = expected_speakers
        else:
            # During automated pipelines, batch jobs, or when prompting is disabled,
            # default directly to auto speaker detection.
            expected_speakers = "auto"
            self.expected_speakers = "auto"

        # Pre-transcribed bypass: with a single expected speaker there is
        # nothing to detect that the transcript doesn't already imply --
        # skip spawning the local worker process entirely and just label
        # every existing transcript segment "Speaker 1" in memory.
        transcript_segments = (self.transcript or {}).get("segments") if self.transcript else None
        if expected_speakers == "1" and transcript_segments:
            self.log_activity(
                "[SPEAKER DETECT] Single expected speaker with an existing transcript -- "
                "assigning \"Speaker 1\" to every segment without running the local helper."
            )
            last_end = max((float(seg.get("end", 0.0) or 0.0) for seg in transcript_segments), default=0.0)
            result = {
                "num_speakers": 1,
                "speakers": ["Speaker 1"],
                "audio_duration": float(self.duration) if self.duration else last_end,
                "segments": [
                    {
                        "start": float(seg.get("start", 0.0) or 0.0),
                        "end": float(seg.get("end", 0.0) or 0.0),
                        "speaker": "Speaker 1",
                    }
                    for seg in transcript_segments
                ],
            }
            self.diarization_finished(result)
            return

        if not self._ensure_runtime_environment_responsive("diarize"):
            return

        self.set_tools_actions_enabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_button.show()
        self.set_processing_stage("Speaker Detection")
        if not self.pipeline_active:
            self.processing_status["diarization"] = False

        self.log_activity("[SPEAKER DETECT] Starting isolated local diarization helper...")
        self.log_activity(
            "[SPEAKER DETECT] Processing backend: CPU (hardware acceleration not enabled in this version)."
        )
        self.statusBar().showMessage("Starting local Speaker Detection...")

        self.diarization_output_buffer = ""
        self.diarization_helper_ready = False
        self.diarization_result_received = False
        self._diarization_canceled_by_user = False

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(self.on_diarization_output)
        process.readyReadStandardError.connect(self.on_diarization_stderr)
        process.finished.connect(self.on_diarization_process_finished)
        process.finished.connect(lambda: unregister_process(process))
        process.errorOccurred.connect(self.on_diarization_process_error)
        process.errorOccurred.connect(lambda: unregister_process(process))

        self.diarization_process = process

        sens = str(self.settings_store.value("diarization_sensitivity", getattr(self, "diarization_sensitivity", "normal")) or "normal")
        worker_cmd = [
            "--diarize", str(self.audio_file),
            "--expected-speakers", str(expected_speakers),
            "--diarization-sensitivity", str(sens)
        ]
        if transcript_segments:
            try:
                import tempfile
                import json
                tf = tempfile.NamedTemporaryFile(
                    prefix="diarize_transcript_", suffix=".json", delete=False, mode="w", encoding="utf-8"
                )
                json.dump({"segments": transcript_segments}, tf)
                tf.close()
                self.diarization_transcript_file = tf.name
                worker_cmd.extend(["--transcript-file", str(tf.name)])
                self.log_activity(
                    f"[SPEAKER DETECT] Fast transcript-guided diarization enabled ({len(transcript_segments)} segments)."
                )
            except Exception as exc:
                self.log_activity(f"[SPEAKER DETECT] Could not write temporary transcript file: {exc}")

        try:
            worker_executable, worker_args, env_overrides = self._worker_command(worker_cmd)
        except FileNotFoundError as exc:
            self.cleanup_diarization_process()
            self.diarization_error(str(exc))
            return

        self._apply_worker_env_overrides(process, env_overrides)
        process.start(worker_executable, worker_args)

        if not process.waitForStarted(3000):
            error = process.errorString() or "Unknown process-start error."
            self.cleanup_diarization_process()
            self.diarization_error(
                f"Could not start the local Speaker Detection process:\n\n{error}"
            )
            return

        register_process(process)
        
        self.log_activity(
            f"[SPEAKER DETECT] Local helper process started (PID {process.processId()})."
        )

    def on_diarization_output(self, force_flush=False):
        process = self.diarization_process
        if process is None:
            return

        data = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.diarization_output_buffer += data
        
        if force_flush and "\n" not in self.diarization_output_buffer and self.diarization_output_buffer.strip():
            self.diarization_output_buffer += "\n"

        while "\n" in self.diarization_output_buffer:
            line, self.diarization_output_buffer = self.diarization_output_buffer.split(
                "\n", 1
            )
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                lowered = line.lower()
                if "warning" in lowered or "warnings.warn" in lowered:
                    level = "[WARNING]"
                elif "error" in lowered or "traceback" in lowered or "exception" in lowered:
                    level = "[ERROR]"
                else:
                    level = "[INFO]"
                self.log_activity(f"[SPEAKER DETECT] {level} Helper: {line}")
                continue

            kind = message.get("type")

            if kind == "hello":
                version = str(message.get("protocol", ""))
                capabilities = message.get("capabilities", [])
                if version != HELPER_PROTOCOL_VERSION:
                    self.diarization_error(
                        "The local processing helper is incompatible with this version of the application.\n\n"
                        f"Expected helper protocol {HELPER_PROTOCOL_VERSION}, but found {version or 'unknown'}.\n\n"
                        "Please use the helper included with this version of Radio & TV Story Segmenter."
                    )
                    return
                if "diarize" not in capabilities:
                    self.diarization_error(
                        "The installed local helper does not support Speaker Detection.\n\n"
                        "Please use the helper included with this version of Radio & TV Story Segmenter."
                    )
                    return
                self.diarization_helper_ready = True
                self.log_activity(
                    f"[SPEAKER DETECT] Helper protocol {version} verified; diarization capability available."
                )

            elif kind == "progress":
                percent = int(message.get("percent", 0))
                status = str(message.get("message", "Speaker Detection in progress..."))
                status_lower = status.lower()

                # Map stage index reliably using status keywords instead of brittle percentage drops
                if any(k in status_lower for k in ["vad", "speech", "detect", "init", "load", "audio"]):
                    stage_idx = 0
                elif any(k in status_lower for k in ["embed", "vector", "extract", "feature", "compute"]):
                    stage_idx = 1
                elif any(k in status_lower for k in ["cluster", "group", "assemble", "final", "segment"]):
                    stage_idx = 2
                else:
                    stage_idx = getattr(self, "_diar_stage_idx", 0)

                self._diar_stage_idx = stage_idx
                total_stages = 3
                effective_stage = min(stage_idx, total_stages - 1)
                calculated_percent = int(((effective_stage * 100.0) + float(percent)) / float(total_stages))

                last_overall = getattr(self, "_diar_last_overall_percent", 0)
                overall_percent = max(last_overall, calculated_percent)
                overall_percent = max(0, min(99, overall_percent))
                self._diar_last_overall_percent = overall_percent

                self.current_processing_stage_detail = status
                self.update_processing_progress(overall_percent, status)
                
                # Rate limit logging of speaker detection progress to prevent Qt UI thread lockup on long files.
                import time as _time
                now = _time.monotonic()
                last_log = getattr(self, "_last_diar_log_time", 0.0)
                is_milestone = any(k in status_lower for k in ["init", "load", "analyzing", "bypassing", "complete", "finished", "error"])
                if is_milestone or now - last_log >= 3.0:
                    self._last_diar_log_time = now
                    self.log_activity(f"[SPEAKER DETECT] {status}")

            elif kind == "finished":
                if not self.diarization_helper_ready:
                    self.diarization_helper_ready = True

                self.diarization_result_received = True
                result = message.get("result", {})
                self.diarization_finished(result)

            elif kind == "error":
                self.diarization_error(
                    str(message.get("message", "Speaker Detection failed."))
                )

    def on_diarization_stderr(self):
        """Route the worker's stderr straight to the log, separate from the
        stdout JSON protocol (see SeparateChannels above) so third-party
        library output can't corrupt an in-flight JSON message."""
        process = self.diarization_process
        if process is None:
            return
        data = bytes(process.readAllStandardError()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            lowered = line.lower()
            if "error" in lowered or "traceback" in lowered or "exception" in lowered:
                level = "[ERROR]"
            elif "warning" in lowered or "warnings.warn" in lowered:
                level = "[WARNING]"
            else:
                level = "[INFO]"
            self.log_activity(f"[SPEAKER DETECT] {level} Helper (stderr): {line}", mark_dirty=False)

    def on_diarization_process_finished(self, exit_code, exit_status):
        self.on_diarization_output(force_flush=True)

        if getattr(self, "_diarization_canceled_by_user", False):
            self.cleanup_diarization_process()
            return

        if self.diarization_process is None:
            return

        error_text = self.diarization_output_buffer.strip()
        was_successful = self.diarization_result_received

        self.cleanup_diarization_process()

        if was_successful:
            self.log_activity("[SPEAKER DETECT] Local helper process exited normally.")
            if self.pipeline_active and self.pipeline_queue:
                QTimer.singleShot(0, self._run_next_selected_processing)
            elif self.batch_active and self.pipeline_active:
                self._batch_export_current()
                self.pipeline_active = False
                QTimer.singleShot(0, self._batch_next_media)
            return

        if exit_code != 0:
            self.diarization_error(
                "The local Speaker Detection helper exited unexpectedly "
                f"(exit code {exit_code})."
                + (f"\n\nHelper output:\n{error_text}" if error_text else "")
            )
            return

        self.diarization_error("Speaker Detection ended without returning results.")

    def cleanup_diarization_process(self):
        process = self.diarization_process
        if process is not None and not getattr(self, "diarization_result_received", False):
            self._diarization_canceled_by_user = True
        self.diarization_process = None
        self.diarization_output_buffer = ""
        self.diarization_helper_ready = False
        self.diarization_result_received = False
        self._diar_stage_idx = 0
        self._diar_last_raw_pct = 0.0
        self._diar_last_overall_percent = 0

        if process is not None:
            
            unregister_process(process)
            
            try:
                if process.state() != QProcess.ProcessState.NotRunning:
                    process.kill()
                    process.waitForFinished(2000)
            except Exception:
                pass
            try:
                process.deleteLater()
            except Exception:
                pass

        transcript_tmp = getattr(self, "diarization_transcript_file", None)
        if transcript_tmp:
            self.diarization_transcript_file = None
            try:
                if os.path.exists(transcript_tmp):
                    os.unlink(transcript_tmp)
            except OSError:
                pass

    def diarization_progress(self, message, percent):
        self.update_processing_progress(percent, message)

    def diarization_finished(self, result):
        self._diar_stage_idx = 0
        self._diar_last_raw_pct = 0.0
        self._diar_last_overall_percent = 0
        self.progress.hide()
        self.cancel_button.hide()
        self.set_tools_actions_enabled(True)

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        self.diarization = result
        self.processing_status["diarization"] = True

        # Map acoustic embeddings to transcript segments
        if isinstance(self.transcript, dict) and "segments" in self.transcript:
            window_segs = result.get("window_embeddings", []) if isinstance(result, dict) else []
            diar_segs = result.get("segments", []) if isinstance(result, dict) else []
            for t_idx, t_seg in enumerate(self.transcript["segments"]):
                t_st = float(t_seg.get("start", 0.0))
                t_en = float(t_seg.get("end", t_st))
                t_dur = max(0.001, t_en - t_st)

                best_emb = None

                # First, try matching against fine-grained window embeddings
                if window_segs:
                    try:
                        import numpy as np
                        overlapping_embs = []
                        weights = []
                        for w_item in window_segs:
                            w_st = float(w_item.get("start", 0.0))
                            w_en = float(w_item.get("end", w_st))
                            ov = max(0.0, min(t_en, w_en) - max(t_st, w_st))
                            if ov > 0 and "embedding" in w_item:
                                overlapping_embs.append(np.array(w_item["embedding"], dtype=np.float32))
                                weights.append(ov)

                        if overlapping_embs:
                            weights = np.array(weights, dtype=np.float32)
                            sum_w = np.sum(weights)
                            if sum_w > 0:
                                weighted_emb = np.sum([e * w for e, w in zip(overlapping_embs, weights)], axis=0) / sum_w
                                norm = np.linalg.norm(weighted_emb)
                                if norm > 0:
                                    weighted_emb = weighted_emb / norm
                                best_emb = [round(float(x), 6) for x in weighted_emb.tolist()]
                    except Exception:
                        best_emb = None

                # Fallback to diarization segments if window embeddings were absent or didn't overlap
                if best_emb is None and diar_segs:
                    best_overlap = 0.0
                    for d_seg in diar_segs:
                        d_st = float(d_seg.get("start", 0.0))
                        d_en = float(d_seg.get("end", d_st))
                        d_dur = d_en - d_st

                        # DO NOT allow a macro-block (longer than 8s or 3x the segment)
                        # to stamp its pooled embedding onto this segment!
                        if d_dur > 8.0 and d_dur > (t_dur * 2.5):
                            continue

                        overlap = max(0.0, min(t_en, d_en) - max(t_st, d_st))
                        if overlap > best_overlap and "embedding" in d_seg:
                            best_overlap = overlap
                            best_emb = d_seg["embedding"]

                    if best_emb is not None and not (best_overlap >= 0.5 * t_dur or best_overlap >= 0.8):
                        best_emb = None

                if best_emb is not None:
                    t_seg["embedding"] = best_emb
                else:
                    # Remove any old poisoned shared embedding so the app knows 
                    # it needs a fresh slice instead of reusing a contaminated cluster
                    t_seg.pop("embedding", None)

            # Auto-match known station voice profiles across detected turns if enabled in preferences
            if getattr(self, "enable_voice_profiles", True):
                try:
                    from speaker_profiles import StationVoiceProfileStore
                    vp_store = getattr(self, "voice_profile_store", None)
                    if vp_store is None:
                        vp_store = StationVoiceProfileStore()
                        self.voice_profile_store = vp_store
                    
                    profiles = vp_store.list_profiles()
                    if profiles:
                        thresh = float(getattr(self, "voice_profile_auto_match_threshold", 0.78) or 0.78)
                        matched_counts = {}
                        for t_idx, t_seg in enumerate(self.transcript["segments"]):
                            emb = t_seg.get("embedding")
                            if not emb:
                                continue
                            match_res = vp_store.match_vector(emb, threshold=thresh)
                            if match_res:
                                prof, sim, margin = match_res
                                override_key = f"SEG_{t_idx}_SPEAKER"
                                self.speaker_names[override_key] = prof.name
                                self.segment_speaker_overrides[t_idx] = override_key
                                matched_counts[prof.name] = matched_counts.get(prof.name, 0) + 1
                        if matched_counts:
                            summary_str = ", ".join(f"{name} ({count} turns)" for name, count in matched_counts.items())
                            self.log_activity(f"[VOICE PROFILES] Auto-matched recurring station voices: {summary_str}")
                except Exception as vp_err:
                    self.log_activity(f"[VOICE PROFILES] Notice during auto-match: {vp_err}", mark_dirty=False)

        number = result.get("num_speakers", 0)
        self.speaker_status.setText(
            f"Speaker detection complete: {number} speaker(s) detected."
        )

        self.render_transcript()
        # The progress-stage label is a transient processing indicator.  Do not
        # leave the last diarization percentage (for example, 95%) above the
        # timeline after speaker detection has completed.
        self.set_processing_stage(None)
        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, "Speaker Detection")
        self.save_project()

        self.log_activity(
            f"[SPEAKER DETECT] Complete: identified {number} speaker(s) locally."
        )
        self.update_processing_stage_summary()
        self.statusBar().showMessage(f"Speaker detection complete: {number} speaker(s) detected.")

    def diarization_error(self, message):
        self._diar_stage_idx = 0
        self._diar_last_raw_pct = 0.0
        self._diar_last_overall_percent = 0
        self.pending_diarization = False
        self.pipeline_speaker_detection_requested = False
        self.pipeline_active = False
        self.pipeline_queue = []
        self.pipeline_rerun_confirmed = False
        self.pending_auto_detect_stories = False
        if getattr(self, "batch_active", False):
            self.batch_active = False
        self.progress.hide()
        self.cancel_button.hide()
        self.set_processing_stage(None)
        self.set_tools_actions_enabled(True)

        if message == "Process canceled by user.":
            self.statusBar().showMessage("Speaker detection canceled by user.")
            self.log_activity("[SPEAKER DETECT] Canceled by user.")
        else:
            self.log_activity(f"[SPEAKER DETECT] Error: {message}")
            QMessageBox.critical(self, "Speaker Detection Error", message)


    def _diar_segments_cache_key(self):
        segments = self.diarization.get("segments") if self.diarization else None
        if not segments:
            return None
        return (id(segments), len(segments))

    def _ensure_diar_speaker_index(self):
        key = self._diar_segments_cache_key()
        if key == self._diar_index_key:
            return
        if key is None:
            self._diar_sorted_segments = []
            self._diar_sorted_orig_idx = []
            self._diar_sorted_starts = []
            self._diar_max_end_prefix = []
            self._diar_speaker_labels = set()
            self._diar_index_key = None
            return

        segments = self.diarization.get("segments", [])
        order = sorted(range(len(segments)), key=lambda i: segments[i]["start"])
        sorted_segments = [segments[i] for i in order]
        starts = [segments[i]["start"] for i in order]
        max_end_prefix = []
        running_max = float("-inf")
        for seg in sorted_segments:
            running_max = max(running_max, seg["end"])
            max_end_prefix.append(running_max)

        self._diar_sorted_segments = sorted_segments
        self._diar_sorted_orig_idx = order
        self._diar_sorted_starts = starts
        self._diar_max_end_prefix = max_end_prefix
        self._diar_speaker_labels = {
            self.display_speaker(s["speaker"]) for s in segments if s.get("speaker")
        }
        self._diar_index_key = key

    def speaker_at_time(self, start, end):
        if not self.diarization:
            return None

        self._ensure_diar_speaker_index()
        segments = self._diar_sorted_segments
        if not segments:
            return None

        from bisect import bisect_right

        hi = bisect_right(self._diar_sorted_starts, end)
        if hi == 0:
            return None
        lo = bisect_right(self._diar_max_end_prefix, start, 0, hi)

        best_speaker = None
        best_key = None
        orig_idx = self._diar_sorted_orig_idx

        for i in range(lo, hi):
            diar_segment = segments[i]
            overlap_start = max(start, diar_segment["start"])
            overlap_end = min(end, diar_segment["end"])
            overlap = overlap_end - overlap_start
            if overlap <= 0:
                continue

            key = (overlap, -orig_idx[i])
            if best_key is None or key > best_key:
                best_key = key
                best_speaker = diar_segment["speaker"]

        return best_speaker

    def get_effective_speaker_name(self, seg_idx, segment):
        raw_speaker = self.segment_speaker_overrides.get(
            seg_idx
        ) or self.speaker_for_segment(segment)
        return self.display_speaker(raw_speaker)

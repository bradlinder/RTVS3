"""Transcription background process management for Radio & TV Story Segmenter."""
from __future__ import annotations

import html
import json
import logging
import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QMessageBox

from prs_shared import (
    HELPER_PROTOCOL_VERSION,
    format_time,
    register_process,
    unregister_process,
    collapse_repeating_ngrams,
    strip_hallucination_phrases,
    trim_trailing_degenerate_tail,
    scrub_transcript_segments,
    scrub_transcript,
    get_effective_audio_for_processing,
)

logger = logging.getLogger(__name__)


class TranscriptionProcessingMixin:
    def start_transcription(self):
        if not self.audio_file:
            self.log_activity("[TRANSCRIPTION] Aborted: no media file is loaded.")
            return

        # Stop background thumbnail and waveform workers during heavy ML tasks to free CPU/disk I/O
        self.stop_waveform_worker()
        self.stop_video_thumbnail_worker()

        if not self.pipeline_active and not getattr(self, "pipeline_rerun_confirmed", False):
            choice = self._processing_choice("transcription")
            if choice == "cancel":
                self.log_activity("[TRANSCRIPTION] User canceled processing choice.")
                return
            if choice == "start_over":
                self.transcript = []
                self.processing_status["transcription"] = False
                self.log_activity("[TRANSCRIPTION] Starting over; previous transcript discarded.")
            elif choice == "continue":
                self.log_activity("[TRANSCRIPTION] Continuing from existing partial transcript.")

        if self.transcription_process is not None:
            self.log_activity("[TRANSCRIPTION] A transcription job is already running.")
            return

        if not self._ensure_runtime_environment_responsive("transcribe"):
            return

        self.set_tools_actions_enabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_button.show()

        model_name = self.current_whisper_model()
        self.whisper_model = model_name
        try:
            if not self.is_whisper_model_available(model_name):
                label = model_name.replace("-v3", "").title()
                answer = QMessageBox.question(
                    self,
                    "Model Not Installed",
                    f"Whisper {label} is not yet installed locally.\n\n"
                    "Would you like to download it now? Once downloaded, transcription will begin automatically.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    self.log_activity(
                        f"[TRANSCRIPTION] Model '{model_name}' is not installed; transcription canceled by user.",
                        mark_dirty=False
                    )
                    self.pipeline_active = False
                    self.pipeline_queue = []
                    self.progress.hide()
                    self.cancel_button.hide()
                    self.set_tools_actions_enabled(True)
                    return

                self._download_model_and_continue_transcription(model_name, label)
                return
        except Exception as exc:
            self.set_tools_actions_enabled(True)
            self.progress.hide()
            self.cancel_button.hide()
            self.pipeline_active = False
            self.pipeline_queue = []
            self.log_activity(f"[TRANSCRIPTION] Error preparing model '{model_name}': {exc}")
            QMessageBox.critical(self, "Transcription Error", f"Failed to prepare model '{model_name}':\n\n{exc}")
            return

        if not self.pipeline_active:
            self.processing_status["transcription"] = False

        if model_name.startswith("parakeet"):
            stage_desc = "Parakeet ONNX"
        elif model_name == "fastconformer-es-onnx":
            stage_desc = "Spanish FastConformer"
            if hasattr(self, "project_metadata") and isinstance(getattr(self, "project_metadata", None), object):
                try: setattr(self.project_metadata, "source_language", "es")
                except Exception: pass
            self.translation_display_mode = "es"
            if hasattr(self, "update_translation_language_selector"):
                self.update_translation_language_selector()
        elif model_name == "fastconformer-multilingual-onnx":
            stage_desc = "Multilingual FastConformer"
            if hasattr(self, "project_metadata") and getattr(self.project_metadata, "source_language", "").startswith("es"):
                self.translation_display_mode = "es"
                if hasattr(self, "update_translation_language_selector"):
                    self.update_translation_language_selector()
        elif str(model_name).lower().startswith("whisper"):
            stage_desc = model_name
        else:
            stage_desc = f"Whisper {model_name}"

        self.set_processing_stage("Transcription", stage_desc)
        self.transcription_output_buffer = ""
        self.transcription_helper_ready = False
        self.transcription_result_received = False
        
        # Prepare transcript view for live streaming preview
        if hasattr(self, "transcript_view"):
            self.transcript_view.setReadOnly(True)
            self.transcript_view.clear()
            self.transcript_view.set_char_timestamp_map([])
        self.streaming_transcript_segments = []
        self.log_activity(
            f"[TRANSCRIPTION] Started local Whisper transcription (Model: '{model_name}')."
        )
        self.log_activity("[TRANSCRIPTION] Starting isolated local transcription helper...")
        self.log_activity(
            "[TRANSCRIPTION] Processing backend: CPU (hardware acceleration not enabled in this version)."
        )
        self.statusBar().showMessage("Starting local transcription...")

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(self.on_transcription_output)
        process.readyReadStandardError.connect(self.on_transcription_stderr)
        process.finished.connect(self.on_transcription_process_finished)
        process.finished.connect(lambda: unregister_process(process))
        process.errorOccurred.connect(self.on_transcription_process_error)
        process.errorOccurred.connect(lambda: unregister_process(process))
        
        self.transcription_process = process

        beam_size = getattr(self, "whisper_beam_size", 5)
        if hasattr(self, "settings_store"):
            try:
                beam_size = int(self.settings_store.value("whisper_beam_size", beam_size) or 5)
            except Exception:
                beam_size = 5

        audio_for_transcription = str(self.audio_file)
        try:
            effective_audio = get_effective_audio_for_processing(
                self.audio_file,
                settings_store=getattr(self, "settings_store", None),
                project_metadata=getattr(self, "project_metadata", None),
            )
            if effective_audio and Path(effective_audio).is_file():
                if Path(effective_audio).resolve() != Path(self.audio_file).resolve():
                    self.log_activity(
                        f"[TRANSCRIPTION] Auto-loudness normalization active: feeding normalized sidecar ({Path(effective_audio).name}) to ASR engine."
                    )
                audio_for_transcription = str(effective_audio)
        except Exception as exc:
            self.log_activity(f"[TRANSCRIPTION] Note: audio normalization check skipped: {exc}")

        try:
            worker_executable, worker_args, env_overrides = self._worker_command([
                "--transcribe",
                audio_for_transcription,
                model_name,
                getattr(self, "whisper_initial_prompt", ""),
                str(beam_size),
            ])
        except FileNotFoundError as exc:
            self.cleanup_transcription_process()
            self.transcription_error(str(exc))
            return

        self._apply_worker_env_overrides(process, env_overrides)
        process.start(worker_executable, worker_args)

        if not process.waitForStarted(3000):
            error = process.errorString() or "Unknown process-start error."
            self.cleanup_transcription_process()
            self.transcription_error(
                f"Could not start the local transcription process:\n\n{error}"
            )
            return

        register_process(process)
        
        self.log_activity(
            f"[TRANSCRIPTION] Local helper process started (PID {process.processId()})."
        )

    def on_transcription_output(self, force_flush=False):
        process = self.transcription_process
        if process is None:
            return

        data = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.transcription_output_buffer += data
        
        if force_flush and "\n" not in self.transcription_output_buffer and self.transcription_output_buffer.strip():
            self.transcription_output_buffer += "\n"

        while "\n" in self.transcription_output_buffer:
            line, self.transcription_output_buffer = self.transcription_output_buffer.split(
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
                self.log_activity(f"[TRANSCRIPTION] {level} Helper: {line}")
                continue

            kind = message.get("type")
            if kind == "hello":
                version = str(message.get("protocol", ""))
                capabilities = message.get("capabilities", [])
                if version != HELPER_PROTOCOL_VERSION:
                    self.transcription_error(
                        "The local processing helper is incompatible with this version of the application.\n\n"
                        f"Expected helper protocol {HELPER_PROTOCOL_VERSION}, but found {version or 'unknown'}.\n\n"
                        "Please use the helper included with this version of Radio & TV Story Segmenter."
                    )
                    return
                if "transcribe" not in capabilities:
                    self.transcription_error(
                        "The installed local helper does not support Whisper transcription.\n\n"
                        "Please use the helper included with this version of Radio & TV Story Segmenter."
                    )
                    return
                self.transcription_helper_ready = True
                self.log_activity(
                    f"[TRANSCRIPTION] Helper protocol {version} verified; transcription capability available."
                )
            elif kind == "streaming_segment":
                seg = message.get("segment")
                if seg:
                    self._handle_live_streaming_segment(seg)
            elif kind == "progress":
                percent = int(message.get("percent", 0))
                status = str(message.get("message", "Transcription in progress..."))
                if "Spanish" in status or "detected spanish" in status.lower() or "switching to spanish" in status.lower():
                    if "switching to Whisper" in status or "No Spanish FastConformer" in status:
                        self.current_processing_stage_detail = "Whisper Small"
                    elif "Spanish FastConformer" in status:
                        self.current_processing_stage_detail = "Spanish FastConformer ONNX"
                    elif "Multilingual FastConformer" in status:
                        self.current_processing_stage_detail = "Multilingual FastConformer ONNX"
                    if hasattr(self, "project_metadata") and isinstance(getattr(self, "project_metadata", None), object):
                        try: setattr(self.project_metadata, "source_language", "es")
                        except Exception: pass
                    self.translation_display_mode = "es"
                    if hasattr(self, "update_translation_language_selector"):
                        self.update_translation_language_selector()
                self.transcription_progress(status, percent)
                self.log_activity(f"[TRANSCRIPTION] {status}")
            elif kind == "finished":
                if not self.transcription_helper_ready:
                    self.transcription_helper_ready = True

                self.transcription_result_received = True
                self.transcription_finished(message.get("result", {}))
            elif kind == "warning":
                self.log_activity(f"[WARNING] Transcription helper: {message.get('message', '')}")
            elif kind == "error":
                self.transcription_error(str(message.get("message", "Transcription failed.")))

    def on_transcription_stderr(self):
        """Route the worker's stderr (third-party library warnings, C-level
        driver output) straight to the log. This is deliberately a separate
        channel from stdout (see SeparateChannels above) rather than merged
        with it -- stdout carries the line-based JSON protocol, and a stray
        stderr write landing mid-line there could corrupt a JSON message
        (e.g. the final "finished" result) and silently fail the job.
        """
        process = self.transcription_process
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
            self.log_activity(f"[TRANSCRIPTION] {level} Helper (stderr): {line}", mark_dirty=False)

    def _handle_live_streaming_segment(self, segment):
        """Append an incoming live transcript chunk directly to the view without rebuilding the map."""
        if not hasattr(self, "streaming_transcript_segments"):
            self.streaming_transcript_segments = []
        self.streaming_transcript_segments.append(segment)

        if not hasattr(self, "transcript_view"):
            return

        text = segment.get("text", "").strip()
        if not text:
            return

        start_time = segment.get("start", 0.0)
        time_str = format_time(start_time)

        curr_theme = getattr(self.transcript_view, "current_theme", "dark")
        if curr_theme == "light":
            text_color = "#24292f"
            time_color = "#57606a"
        elif curr_theme == "high_contrast":
            text_color = "#ffffff"
            time_color = "#ffff00"
        else:
            text_color = "#c9d1d9"
            time_color = "#8b949e"

        time_html = f'<span style="color: {time_color}; font-weight: bold;">[{time_str}]</span> ' if getattr(self, "show_timestamps", True) else ""
        escaped_text = html.escape(text)
        para_html = f'<p style="margin-bottom: 8px; color: {text_color};">{time_html}{escaped_text}</p>'

        cursor = self.transcript_view.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(para_html)
        cursor.endEditBlock()

        v_bar = self.transcript_view.verticalScrollBar()
        if v_bar:
            v_bar.setValue(v_bar.maximum())
    
    def on_transcription_process_finished(self, exit_code, exit_status):
        self.on_transcription_output(force_flush=True)
        if self.transcription_process is None:
            return

        output = self.transcription_output_buffer.strip()
        was_successful = self.transcription_result_received

        self.cleanup_transcription_process()

        if was_successful:
            self.log_activity("[TRANSCRIPTION] Local helper process completed successfully.")
            return

        if exit_code != 0:
            self.cleanup_transcription_process()
            self.transcription_error(
                f"The local transcription helper exited unexpectedly (exit code {exit_code})."
                + (f"\n\nHelper output:\n{output}" if output else "")
            )
            return

        self.cleanup_transcription_process()
        self.transcription_error("Transcription ended without returning results.")

    def on_transcription_process_error(self, error):
        if self.transcription_process is None:
            return
        message = self.transcription_process.errorString()
        self.cleanup_transcription_process()
        self.transcription_error(
            f"The local transcription process reported an error:\n\n{message}"
        )

    def cleanup_transcription_process(self):
        process = self.transcription_process
        self.transcription_process = None
        self.transcription_output_buffer = ""
        self.transcription_helper_ready = False
        self.transcription_result_received = False
        if process is not None:
            unregister_process(process)
            try:
                if process.state() != QProcess.ProcessState.NotRunning:
                    process.kill()
                    process.waitForFinished(3000)
            except Exception:
                pass
            try:
                process.deleteLater()
            except Exception:
                pass

    def transcription_progress(self, message, percent):
        self.update_processing_progress(percent, message)

    def transcription_finished(self, transcript):
        if not isinstance(transcript, dict) or "segments" not in transcript:
            self.transcription_error(
                "The transcription helper returned an invalid transcript result."
            )
            return

        try:
            transcript = scrub_transcript(transcript)
        except Exception as scrub_err:
            logger.warning(f"Failed to scrub transcript payload: {scrub_err}")

        # Apply the model-independent glossary after ASR. This is the
        # authoritative spelling pass for every transcription backend; model
        # prompts/hotwords are only optional recognition hints.
        try:
            from terminology import normalize_transcript, load_glossary
            transcript = normalize_transcript(
                transcript, load_glossary(getattr(self, "settings_store", None))
            )
        except Exception as glossary_err:
            logger.warning(f"Failed to normalize transcript glossary: {glossary_err}")

        self.flush_pending_transcript_undo() if hasattr(self, "flush_pending_transcript_undo") else None
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        self.progress.setValue(100)
        self.transcript = transcript
        self.processing_status["transcription"] = True

        # Sync detected spoken language
        detected_lang = str((transcript or {}).get("language", "en") or "en").lower()
        if hasattr(self, "project_metadata") and self.project_metadata is not None:
            try:
                setattr(self.project_metadata, "source_language", detected_lang)
            except Exception:
                pass
        if detected_lang.startswith("es"):
            self.translation_display_mode = "es"
            self.log_activity("[TRANSCRIPTION] Spoken language detected: Spanish (es). Setting source view to Español.", mark_dirty=False)
        else:
            self.translation_display_mode = "en"
            self.log_activity(f"[TRANSCRIPTION] Spoken language detected: {detected_lang.upper()}.", mark_dirty=False)

        self.progress.hide()
        self.cancel_button.hide()

        self.set_tools_actions_enabled(True)
        self.update_translation_language_selector()

        # If Diarization is scheduled to run immediately next in the pipeline,
        # skip rebuilding the document layout here so the final speaker tags
        # and anchor map can be built cleanly once diarization finishes.
        will_diarize_next = (
            getattr(self, "pipeline_active", False)
            and "diarization" in getattr(self, "pipeline_queue", [])
        )
        if not will_diarize_next:
            self.set_processing_stage(None)
            self.render_transcript()
        else:
            self.log_activity("[TRANSCRIPTION] Live text ready. Speaker detection will assign speakers next.", mark_dirty=False)

        self.render_translation_view()

        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, "Transcription")

        self.log_activity("[TRANSCRIPTION] Complete. Rendered interactive transcript.")
        self.update_processing_stage_summary()
        self.statusBar().showMessage("Transcription complete.")
        self.save_project()

        # Prompt user if Spanish was detected and no Spanish FastConformer model is installed
        # (Worker sets need_spanish_model_prompt=True when it had to fall back to Whisper)
        if (
            detected_lang.startswith("es")
            and isinstance(transcript, dict)
            and transcript.get("need_spanish_model_prompt") is True
        ):
            if not getattr(self, "_prompted_spanish_model_download", False):
                self._prompted_spanish_model_download = True
                try:
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        "Spanish Speech Detected — Model Download Recommended",
                        "Spanish speech was detected in this audio file.\n\n"
                        "Would you like to open Manage AI Models to download the Spanish FastConformer or Multilingual FastConformer model (~250MB) for up to 10x faster Spanish transcriptions?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.open_model_cleanup_dialog()
                except Exception as p_err:
                    logger.warning(f"Failed to display Spanish model download prompt: {p_err}")

        if self.pipeline_active and self.pipeline_queue:
            QTimer.singleShot(0, self._run_next_selected_processing)
        elif self.batch_active and self.pipeline_active:
            self.pipeline_active = False
            self._batch_export_current()
            QTimer.singleShot(0, self._batch_next_media)

    def transcription_error(self, message):
        self.cleanup_transcription_process()
        self.pending_diarization = False
        self.pending_auto_detect_stories = False
        self.pipeline_speaker_detection_requested = False
        self.pipeline_active = False
        self.pipeline_queue = []
        self.pipeline_rerun_confirmed = False
        if getattr(self, "batch_active", False):
            self.batch_active = False
        self.progress.hide()
        self.cancel_button.hide()
        self.set_processing_stage(None)
        self.set_tools_actions_enabled(True)

        if message == "Process canceled by user.":
            self.statusBar().showMessage("Transcription canceled by user.")
        else:
            QMessageBox.critical(self, "Transcription Error", message)


"""Radio & TV Segmenter v1.1.1 — media batch responsibilities.

Methods intentionally retain the MainWindow-facing API so behavior remains
maintaining the established MainWindow-facing API while responsibilities are isolated.
"""

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QGroupBox, QLabel, QMessageBox, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout, QTableWidget, QHeaderView, QAbstractItemView
)
from prs_shared import *
from background_workers import (
    get_video_thumbnail_cache_dir,
    read_video_thumbnail_cache,
    invalidate_video_thumbnail_cache,
)


class MediaBatchMixin:
    def probe_media_duration(self, path):
        """Probe duration locally so video timelines can be populated immediately."""
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run(
                [ffprobe_path() or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, check=True,
                creationflags=creationflags,
            )
            value = float(result.stdout.strip())
            return value if value > 0 else None
        except Exception:
            return None

    def _track_worker_thread(self, thread):
        """Keep a strong reference to active worker threads so Python GC never destroys them while executing."""
        if not hasattr(self, "_active_worker_threads"):
            self._active_worker_threads = set()
        if thread is not None:
            self._active_worker_threads.add(thread)
            def _cleanup():
                if thread in self._active_worker_threads:
                    if not thread.isRunning():
                        self._active_worker_threads.discard(thread)
                    else:
                        QTimer.singleShot(200, _cleanup)
            thread.finished.connect(lambda: QTimer.singleShot(100, _cleanup))

    def stop_waveform_worker(self, timeout_ms=5000):
        """Stop the current waveform worker completely before replacing it or closing."""
        thread = getattr(self, "wf_thread", None)
        worker = getattr(self, "wf_worker", None)
        if thread is None:
            return True

        if thread.isRunning():
            if worker is not None:
                try:
                    worker.cancel()
                except Exception:
                    pass
            thread.quit()
            if not thread.wait(timeout_ms):
                if worker is not None:
                    try:
                        worker.cancel()
                    except Exception:
                        pass
                if not thread.wait(1000):
                    self.log_activity("[WARNING] Waveform worker did not stop within the normal shutdown window; leaving it tracked until Qt finishes cleanup.", mark_dirty=False)
                    return False

        if hasattr(self, "timeline"):
            try:
                self.timeline.set_background_generation_active("waveform", False)
            except Exception:
                pass
        self.wf_thread = None
        self.wf_worker = None
        return True

    def start_video_thumbnail_generation(self, force_regenerate: bool = False):
        if not self.current_media_is_video or not self.audio_file or self.duration <= 0:
            if hasattr(self, "timeline"):
                self.timeline.set_video_thumbnails([])
            return

        if not force_regenerate:
            cached_thumbs = read_video_thumbnail_cache(self.audio_file, self.duration)
            if cached_thumbs:
                self.video_thumbnail_dir = get_video_thumbnail_cache_dir(self.audio_file)
                if self.video_thumbnail_dir:
                    register_active_thumbnail_dir(self.video_thumbnail_dir)
                if hasattr(self, "timeline"):
                    try:
                        self.timeline.set_background_generation_active("thumbnails", False)
                    except Exception:
                        pass
                    self.timeline.set_video_thumbnails(cached_thumbs)
                self.log_activity(f"[MEDIA] Loaded {len(cached_thumbs)} cached video thumbnails.", mark_dirty=False)
                return

        if not self.stop_video_thumbnail_worker():
            self._pending_thumbnail_restart = True
            self.log_activity("[MEDIA] Previous thumbnail worker is still stopping; thumbnail generation will restart once it finishes.", mark_dirty=False)
            return
        try:
            job = get_video_thumbnail_cache_dir(self.audio_file)
            if job is None:
                base = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
                base.mkdir(parents=True, exist_ok=True)
                job = base / hashlib.sha1(str(self.audio_file).encode("utf-8")).hexdigest()[:16]
            if job.exists():
                shutil.rmtree(job, ignore_errors=True)
            job.mkdir(parents=True, exist_ok=True)
            self.video_thumbnail_dir = job
            register_active_thumbnail_dir(self.video_thumbnail_dir)
            thread = QThread(self)
            worker = VideoThumbnailWorker(self.audio_file, self.duration, job)
            worker.moveToThread(thread)
            self.video_thumbnail_thread = thread
            self.video_thumbnail_worker = worker
            self._track_worker_thread(thread)

            thread.started.connect(worker.run)
            worker.finished.connect(self._video_thumbnails_finished)
            worker.finished.connect(thread.quit)
            worker.error.connect(lambda msg: self.log_activity(f"[MEDIA] Video thumbnail generation failed: {msg}", mark_dirty=False))
            worker.error.connect(thread.quit)
            thread.finished.connect(self._video_thumbnail_thread_finished)
            if hasattr(self, "timeline"):
                try:
                    self.timeline.set_background_generation_active("thumbnails", True)
                except Exception:
                    pass
            thread.start()
        except Exception as exc:
            self.log_activity(f"[MEDIA] Could not start thumbnail generation: {exc}", mark_dirty=False)

    def _video_thumbnail_thread_finished(self):
        thread = self.sender()
        if thread is getattr(self, "video_thumbnail_thread", None):
            self.video_thumbnail_thread = None
            self.video_thumbnail_worker = None
        if getattr(self, "_pending_thumbnail_restart", False):
            self._pending_thumbnail_restart = False
            QTimer.singleShot(50, self.start_video_thumbnail_generation)

    def _video_thumbnails_finished(self, items):
        if hasattr(self, "timeline"):
            try:
                self.timeline.set_background_generation_active("thumbnails", False)
            except Exception:
                pass
            self.timeline.set_video_thumbnails(items)

    def stop_video_thumbnail_worker(self, timeout_ms=3000):
        thread = getattr(self, "video_thumbnail_thread", None)
        worker = getattr(self, "video_thumbnail_worker", None)
        if thread is None:
            return True
        if worker:
            try:
                worker.cancel()
            except Exception:
                pass
        if thread.isRunning():
            thread.quit()
            if not thread.wait(timeout_ms):
                if worker:
                    try:
                        worker.cancel()
                    except Exception:
                        pass
                if not thread.wait(1000):
                    self.log_activity("[WARNING] Video thumbnail worker did not finish in time.", mark_dirty=False)
                    if hasattr(self, "_track_worker_thread"):
                        self._track_worker_thread(thread)
                    return False
        if hasattr(self, "timeline"):
            try:
                self.timeline.set_background_generation_active("thumbnails", False)
            except Exception:
                pass
        self.video_thumbnail_thread = None
        self.video_thumbnail_worker = None
        return True

    def regenerate_waveform(self):
        """Force recalculation of waveform peaks by clearing disk cache and restarting generation."""
        if not getattr(self, "audio_file", None):
            return
        invalidate_waveform_peak_cache(self.audio_file)
        try:
            from audio_normalization import get_effective_audio_for_processing
            eff = get_effective_audio_for_processing(
                self.audio_file,
                settings_store=getattr(self, "settings_store", None),
                project_metadata=getattr(self, "project_metadata", None),
            )
            if eff and Path(eff).is_file():
                invalidate_waveform_peak_cache(eff)
        except Exception:
            pass
        if hasattr(self, "timeline"):
            self.timeline.set_waveform_peaks([])
        self.log_activity("[WAVEFORM] Manually regenerating waveform from active audio source...")
        is_es = getattr(self, "language", "en") == "es"
        self.statusBar().showMessage("Regenerando forma de onda..." if is_es else "Regenerating waveform...")
        self.load_waveform_async(force_regenerate=True)

    def regenerate_video_thumbnails(self):
        """Force regeneration of video filmstrip thumbnails."""
        if not getattr(self, "audio_file", None) or not getattr(self, "current_media_is_video", False):
            return
        self.stop_video_thumbnail_worker()
        if hasattr(self, "timeline"):
            self.timeline.set_video_thumbnails([])
        invalidate_video_thumbnail_cache(self.audio_file)
        unregister_active_thumbnail_dir(self.video_thumbnail_dir)
        self.video_thumbnail_dir = None
        self.log_activity("[MEDIA] Manually regenerating video thumbnails...")
        is_es = getattr(self, "language", "en") == "es"
        self.statusBar().showMessage("Regenerando miniaturas de video..." if is_es else "Regenerating video thumbnails...")
        self.start_video_thumbnail_generation(force_regenerate=True)

    def load_waveform_async(self, force_regenerate: bool = False):
        if not self.audio_file:
            return

        proj_file = getattr(self, "project_file", None)
        target_audio = str(Path(self.audio_file).resolve())
        try:
            from audio_normalization import get_effective_audio_for_processing
            eff = get_effective_audio_for_processing(
                self.audio_file,
                settings_store=getattr(self, "settings_store", None),
                project_metadata=getattr(self, "project_metadata", None),
            )
            if eff and Path(eff).is_file():
                target_audio = str(Path(eff).resolve())
        except Exception:
            pass

        if force_regenerate:
            invalidate_waveform_peak_cache(target_audio, project_file=proj_file)
            invalidate_waveform_peak_cache(self.audio_file, project_file=proj_file)

        if not force_regenerate:
            cached_peaks = read_waveform_peak_cache(target_audio, project_file=proj_file)
            if cached_peaks:
                if hasattr(self, "timeline"):
                    try:
                        self.timeline.set_background_generation_active("waveform", False)
                    except Exception:
                        pass
                    self.timeline.set_waveform_peaks(cached_peaks)
                self.log_activity(f"[WAVEFORM] Loaded cached waveform ({len(cached_peaks):,} peaks).", mark_dirty=False)
                return

        # Never replace an active QThread. This is the critical lifetime rule
        # that prevents "QThread: Destroyed while thread is still running".
        if not self.stop_waveform_worker():
            self.log_activity("[ERROR] Could not safely stop the previous waveform worker; waveform generation was not restarted.")
            return

        thread = QThread(self)
        worker = WaveformWorker(target_audio, project_file=proj_file)
        worker.moveToThread(thread)
        self.wf_thread = thread
        self.wf_worker = worker
        self._track_worker_thread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self._waveform_progress)
        worker.finished.connect(self._waveform_finished)
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._waveform_thread_finished)
        if hasattr(self, "timeline"):
            try:
                self.timeline.set_background_generation_active("waveform", True)
            except Exception:
                pass
        thread.start()

    def _waveform_progress(self, partial_peaks, pps, pct):
        worker = self.sender()
        if worker is not None and worker is not getattr(self, "wf_worker", None):
            return
        if hasattr(self, "timeline"):
            try:
                self.timeline.set_progressive_waveform_peaks(partial_peaks, pps, pct)
            except Exception:
                pass

    def _waveform_finished(self, peaks, cancelled=False):
        if hasattr(self, "timeline"):
            try:
                self.timeline.set_background_generation_active("waveform", False)
            except Exception:
                pass
        if cancelled:
            self.log_activity("[WAVEFORM] Waveform generation canceled.")
            return
        self.timeline.set_waveform_peaks(peaks)
        if peaks:
            self.log_activity(f"[WAVEFORM] Waveform generation complete ({len(peaks):,} peaks).")
        else:
            err_msg = getattr(getattr(self, "wf_worker", None), "error_message", "")
            if err_msg:
                self.log_activity(f"[ERROR] Waveform generation failed: {err_msg}")
            else:
                self.log_activity("[ERROR] Waveform generation produced no audio data. The media may not contain a readable audio stream or network path is unreachable.")

    def _waveform_thread_finished(self):
        thread = self.sender()
        if thread is getattr(self, "wf_thread", None):
            self.wf_thread = None
            self.wf_worker = None

    def open_batch_processing_dialog(self):
        if self.batch_active:
            QMessageBox.information(self, "Batch Processing", "A batch job is already running.")
            return

        dialog = BatchProcessingDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        files = [dialog.files.item(i).text() for i in range(dialog.files.count())]
        if not files:
            QMessageBox.warning(self, "Batch Processing", "Add at least one file.")
            return

        output = dialog.output.text().strip()
        if not output:
            output = self.default_project_directory or ""
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)

        if output:
            self._remember_directory(output)

        # Minimize user input: Auto-save active project before starting
        if self.project_dirty and self.audio_file:
            self.save_project(force=True)

        import time
        self.batch_active = True
        self.batch_total_files = len(files)
        self.batch_current_file_idx = 0
        self.batch_start_time = time.monotonic()
        self.batch_completed_durations = []
        self.batch_file_start_time = None

        # Mute and stop media player during batch runs to prevent GPU/Audio engine contention
        if hasattr(self, "player") and self.player:
            self.player.stop()
            self.player.setSource(QUrl())
        self.batch_queue = files
        self.progress.show()
        self.cancel_button.show()
        
        scope = dialog.scope_combo.currentData()
        pipeline_mode = "custom" if dialog.pipeline_custom_radio.isChecked() else "full"
        save_project_only = dialog.save_project_only_check.isChecked()
        save_project = dialog.save_project_check.isChecked() or save_project_only

        unified_transcripts = dialog.unified_transcripts_check.isChecked() and not save_project_only
        transcripts_output = dialog.transcripts_output.text().strip() if unified_transcripts else ""
        if unified_transcripts and not transcripts_output and output:
            transcripts_output = str(Path(output) / "Transcripts")

        do_transcribe = dialog.proc_transcribe.isChecked() if pipeline_mode == "custom" else True
        do_diarize = dialog.proc_diarize.isChecked() if pipeline_mode == "custom" else True
        do_stories = dialog.proc_stories.isChecked() if pipeline_mode == "custom" else True
        translate_pipeline = dialog.proc_translate.isChecked() if pipeline_mode == "custom" else dialog.translate_check.isChecked()

        self.batch_settings = {
            "output": output,
            "unified_transcripts": unified_transcripts,
            "transcripts_output": transcripts_output,
            "pipeline_mode": pipeline_mode,
            "save_project_only": save_project_only,
            "save_project": save_project,
            "do_transcribe": do_transcribe,
            "do_diarize": do_diarize,
            "do_stories": do_stories,
            "scope": scope,
            "skip_existing": dialog.skip_existing_check.isChecked() and not save_project_only,
            "full_txt": dialog.fmt_txt.isChecked() and scope in ("full", "both") and not save_project_only,
            "full_docx": dialog.fmt_docx.isChecked() and scope in ("full", "both") and not save_project_only,
            "full_srt": dialog.fmt_srt.isChecked() and scope in ("full", "both") and not save_project_only,
            "full_vtt": dialog.fmt_vtt.isChecked() and scope in ("full", "both") and not save_project_only,
            "story_txt": dialog.fmt_txt.isChecked() and scope in ("stories", "both") and not save_project_only,
            "story_docx": dialog.fmt_docx.isChecked() and scope in ("stories", "both") and not save_project_only,
            "story_srt": dialog.fmt_srt.isChecked() and scope in ("stories", "both") and not save_project_only,
            "include_speakers": dialog.include_speakers.isChecked(),
            "color_speakers": dialog.color_speakers.isChecked() if hasattr(dialog, "color_speakers") else False,
            "colorize_speakers": dialog.color_speakers.isChecked() if hasattr(dialog, "color_speakers") else False,
            "include_timestamps": dialog.include_times.isChecked(),
            "translate_es": translate_pipeline,
            "translate_stories": translate_pipeline and scope in ("stories", "both"),
            "expected_speakers": str(dialog.batch_expected_speakers_combo.currentData() or "auto"),
            "story_gap": dialog.batch_gap_spin.value(),
            "story_pad": dialog.batch_pad_spin.value(),
            "translate_direction": str(dialog.batch_export_translate_direction_combo.currentData() or "auto"),
        }

        # Apply the batch job's per-run Speaker Detection / Story Detection
        # settings now, so start_diarization()/detect_stories() (which read
        # these as instance attributes, same as the interactive UI) pick up
        # the values chosen in this dialog rather than whatever was left
        # over from Preferences or a previous project.
        self.expected_speakers = self.batch_settings["expected_speakers"]
        self.silence_threshold = self.batch_settings["story_gap"]
        self.lead_in_padding = self.batch_settings["story_pad"]
        self.translation_direction = self.batch_settings["translate_direction"]

        # Auto-route between media processing and document translation
        first_file = Path(files[0])
        if first_file.suffix.lower() in {".txt", ".docx", ".pdf", ".html", ".htm", ".md"}:
            self.batch_document_queue = list(files)
            self._batch_next_document()
        else:
            self._batch_next_media()

    def _batch_next_media(self):
        import time
        if getattr(self, "batch_file_start_time", None):
            self.batch_completed_durations.append(time.monotonic() - self.batch_file_start_time)
            self.batch_file_start_time = None

        if not hasattr(self, "batch_queue") or not self.batch_queue:
            self.batch_active = False  # Reset active flag when queue is empty
            self.batch_total_files = 0
            self.batch_current_file_idx = 0
            self.progress.hide()
            self.cancel_button.hide()
            self.set_processing_stage(None)
            self.log_activity("[BATCH] All media batch processing completed.")
            QMessageBox.information(self, "Batch Processing", "Batch processing completed successfully!")
            return

        # Fetch next media file
        current_file = self.batch_queue.pop(0)
        self.batch_current_file_idx += 1
        self.batch_file_start_time = time.monotonic()
        self.log_activity(f"[BATCH] Processing media file ({self.batch_current_file_idx} of {self.batch_total_files}): {current_file}")

        try:
            output_dir = Path(self.batch_settings.get("output", ""))
            base_name = safe_filename(Path(current_file).stem)
            skip_existing = self.batch_settings.get("skip_existing", False)

            # Build expected output extension list based on requested formats
            required_exts = []
            if self.batch_settings.get("full_txt") or self.batch_settings.get("story_txt"):
                required_exts.append(".txt")
            if self.batch_settings.get("full_docx") or self.batch_settings.get("story_docx"):
                required_exts.append(".docx")
            if self.batch_settings.get("full_srt") or self.batch_settings.get("story_srt"):
                required_exts.append(".srt")
            if self.batch_settings.get("full_vtt") or self.batch_settings.get("story_vtt"):
                required_exts.append(".vtt")

            # Check if all target output files already exist on disk
            all_exist = False
            if skip_existing and required_exts:
                if self.batch_settings.get("unified_transcripts", False):
                    custom_trans_dir = self.batch_settings.get("transcripts_output", "").strip()
                    trans_dir = Path(custom_trans_dir) if custom_trans_dir else (output_dir / "Transcripts")
                    all_exist = trans_dir.exists() and all((trans_dir / f"{base_name}{ext}").exists() for ext in required_exts)
                else:
                    sub_trans_dir = output_dir / base_name / "Transcripts"
                    legacy_dir = output_dir / base_name
                    all_exist = (
                        (output_dir.exists() and all((output_dir / f"{base_name}{ext}").exists() for ext in required_exts)) or
                        (sub_trans_dir.exists() and all((sub_trans_dir / f"{base_name}{ext}").exists() for ext in required_exts)) or
                        (legacy_dir.exists() and all((legacy_dir / f"{base_name}{ext}").exists() for ext in required_exts))
                    )

            # Silence auto-save prompts before switching contexts
            if self.project_dirty and self.audio_file:
                if self.project_file:
                    self.save_project(force=True)
                elif hasattr(self, "_batch_save_project_file"):
                    self._batch_save_project_file()

            # Load the media file
            if not self.load_media_file(current_file):
                self._batch_media_error(f"Could not load file {current_file}")
                return

            # Pre-bind the project file path so intermediate pipeline stages auto-save silently
            if self.batch_settings.get("save_project", True) or self.batch_settings.get("save_project_only", False):
                self.project_file = self._get_batch_project_target_path(base_name)

            # If skipping re-processing, trigger immediate export from existing data
            if all_exist:
                self.log_activity(f"[BATCH] Requested outputs already exist for {base_name}. Skipping re-processing (Skip Existing enabled).")
                # Target outputs already exist on disk; skip export to preserve files
                QTimer.singleShot(0, self._batch_next_media)
                return

            # Non-interactive automated pipeline setup for batch execution
            pipeline_stages = []
            pipeline_mode = self.batch_settings.get("pipeline_mode", "full")

            if pipeline_mode == "full":
                if not self.transcript or not self.processing_status.get("transcription"):
                    pipeline_stages.append("transcription")

                if self.batch_settings.get("include_speakers") and (not self.diarization or not self.processing_status.get("diarization")):
                    pipeline_stages.append("diarization")

                if self.batch_settings.get("scope") in ("stories", "both") and not self.stories:
                    pipeline_stages.append("stories")

                if self.batch_settings.get("translate_es"):
                    pipeline_stages.append("translation")
            else:
                if self.batch_settings.get("do_transcribe", True) and (not self.transcript or not self.processing_status.get("transcription")):
                    pipeline_stages.append("transcription")

                if self.batch_settings.get("do_diarize", True) and (not self.diarization or not self.processing_status.get("diarization")):
                    pipeline_stages.append("diarization")

                if self.batch_settings.get("do_stories", True) and not self.stories:
                    pipeline_stages.append("stories")

                if self.batch_settings.get("translate_es"):
                    pipeline_stages.append("translation")

            if pipeline_stages:
                self.pipeline_queue = pipeline_stages
                self.pipeline_active = True
                QTimer.singleShot(0, self._run_next_selected_processing)
            else:
                if getattr(self, "transcript", None) is not None:
                    self._batch_export_current()
                QTimer.singleShot(0, self._batch_next_media)

        except Exception as e:
            self._batch_media_error(f"Failed to process {current_file}: {str(e)}")

    def _batch_next_document(self):
        import time
        if getattr(self, "batch_file_start_time", None):
            self.batch_completed_durations.append(time.monotonic() - self.batch_file_start_time)
            self.batch_file_start_time = None

        if not hasattr(self, "batch_document_queue") or not self.batch_document_queue:
            self.batch_active = False
            self.batch_total_files = 0
            self.batch_current_file_idx = 0
            self.progress.hide()
            self.cancel_button.hide()
            self.set_processing_stage(None)
            self.log_activity("[BATCH] All document batch processing completed.")
            QMessageBox.information(self, "Batch Processing", "Batch document translation completed successfully!")
            return

        current_doc = self.batch_document_queue.pop(0)
        self.batch_current_file_idx += 1
        self.batch_file_start_time = time.monotonic()
        self.log_activity(f"[BATCH] Translating document ({self.batch_current_file_idx} of {self.batch_total_files}): {current_doc}")
        try:
            if hasattr(self, "translate_document_file"):
                self.translate_document_file(current_doc)
            else:
                self.log_activity(f"[BATCH] Processed {current_doc}")
                QTimer.singleShot(50, self._batch_next_document)
        except Exception as exc:
            self._batch_document_error(f"Error translating {current_doc}: {exc}")

    def _batch_document_error(self, msg):
        """Handles document batch translation errors safely."""
        self.log_activity(f"[BATCH] Document translation failed: {msg}")
        self.progress.hide()
        self.cancel_button.hide()
        self.batch_document_state = None

        # Reset active status so dialog reopening is not blocked
        self.batch_active = False 
        QTimer.singleShot(0, self._batch_next_document)

    def _load_user_preferences(self):
        self.language = str(self.settings_store.value("language", "en") or "en")
        self.show_speaker_labels = str(self.settings_store.value("show_speaker_labels", "true")).lower() in {"1", "true", "yes"}
        self.show_timestamps = str(self.settings_store.value("show_timestamps", "true")).lower() in {"1", "true", "yes"}
        self.show_milliseconds = str(self.settings_store.value("show_milliseconds", "false")).lower() in {"1", "true", "yes"}
        self.default_project_directory = str(self.settings_store.value("default_project_directory", "") or "")
        self.startup_project_mode = str(self.settings_store.value("startup_project_mode", "last") or "last")
        if self.startup_project_mode not in {"new", "last", "prompt"}:
            self.startup_project_mode = "last"
        self.timeline_show_waveform = str(self.settings_store.value("timeline_show_waveform", "true")).lower() in {"1", "true", "yes"}
        self.timeline_show_thumbnails = str(self.settings_store.value("timeline_show_thumbnails", "true")).lower() in {"1", "true", "yes"}

        self.timeline_thumbnail_position = str(self.settings_store.value("timeline_thumbnail_position", "below")).lower()
        if self.timeline_thumbnail_position not in ("above", "below"):
            self.timeline_thumbnail_position = "below"

        self.transcript_selection_mode = str(self.settings_store.value("transcript_selection_mode", "replace") or "replace")
        if self.transcript_selection_mode not in ("replace", "keep"):
            self.transcript_selection_mode = "replace"
        if hasattr(self, "transcript_view") and hasattr(self.transcript_view, "set_selection_mode"):
            self.transcript_view.set_selection_mode(self.transcript_selection_mode)

        if hasattr(self, "timeline"):
            self.timeline.set_timeline_views(self.timeline_show_waveform, self.timeline_show_thumbnails)
            self.timeline.set_thumbnail_position(self.timeline_thumbnail_position)
        saved_theme = str(self.settings_store.value("theme_mode", "dark") or "dark")
        if saved_theme not in ("dark", "light", "high_contrast"):
            saved_theme = "dark"
        self.set_theme(saved_theme)

        # Models & AI settings
        self.whisper_model = str(self.settings_store.value("whisper_model", "parakeet-onnx") or "parakeet-onnx")
        try:
            self.whisper_beam_size = int(self.settings_store.value("whisper_beam_size", 5) or 5)
        except Exception:
            self.whisper_beam_size = 5
        self.translation_model_variant = str(self.settings_store.value("translation_model_variant", "tiny") or "tiny")
        if hasattr(self, "refresh_whisper_model_chooser"):
            self.refresh_whisper_model_chooser()
        if hasattr(self, "refresh_translation_model_chooser"):
            self.refresh_translation_model_chooser()

        # Playback & Timing
        try:
            self.skip_seconds = int(self.settings_store.value("skip_seconds", 5) or 5)
        except Exception:
            self.skip_seconds = 5
        if hasattr(self, "timeline") and hasattr(self.timeline, "set_skip_seconds"):
            self.timeline.set_skip_seconds(self.skip_seconds)

        # Detection Thresholds
        try:
            self.silence_threshold = float(self.settings_store.value("silence_threshold", 3.0) or 3.0)
            self.lead_in_padding = float(self.settings_store.value("lead_in_padding", 0.5) or 0.5)
            self.expected_speakers = str(self.settings_store.value("default_expected_speakers", "auto") or "auto")
            self.story_detection_mode = str(self.settings_store.value("story_detection_mode", "voice") or "voice")
        except Exception:
            pass

        # Auto-save
        try:
            self.auto_save_minutes = int(self.settings_store.value("auto_save_minutes", 5) or 5)
        except Exception:
            self.auto_save_minutes = 5
        if hasattr(self, "update_auto_save_timer"):
            self.update_auto_save_timer()

        # Audio Hardware
        if hasattr(self, "apply_audio_output_device"):
            self.apply_audio_output_device()

        # Load custom vocabulary / glossary on startup.  The terminology
        # layer accepts the older plain-string format as well as the newer
        # structured entries used by the glossary editor.
        try:
            from terminology import parse_glossary
            raw_glossary = self.settings_store.value("glossary", "")
            self.glossary = parse_glossary(raw_glossary)
        except Exception:
            self.glossary = []

        self.apply_glossary_to_whisper_context()
        if self.language == "es":
            self.set_language("es", persist=False)

    def set_thumbnail_position(self, position):
        self.timeline_thumbnail_position = position
        self.settings_store.setValue("timeline_thumbnail_position", position)
        if hasattr(self, "timeline"):
            self.timeline.set_thumbnail_position(position)

    def _remember_saved_project(self, path):
        """Remember only projects that have actually been saved.

        Opening a project or media file must not change the startup target.
        """
        if not path:
            return
        try:
            p = Path(path).resolve()
            if p.suffix.lower() in {".rtvs", ".json"}:
                resolved = str(p)
                self.settings_store.setValue("last_saved_project_path", resolved)
                raw = self.settings_store.value("recent_projects", [])
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        raw = [raw] if raw else []
                recent = [resolved]
                for item in raw if isinstance(raw, list) else []:
                    item = str(item)
                    if item and item != resolved:
                        recent.append(item)
                self.settings_store.setValue("recent_projects", json.dumps(recent[:10]))
                # Flush now rather than relying on QSettings' own timing --
                # this is the exact write "restore last project" depends on,
                # so it needs to reliably survive an app close shortly after.
                self.settings_store.sync()
                if hasattr(self, "_refresh_recent_projects_menu"):
                    self._refresh_recent_projects_menu()
        except Exception:
            pass

    def _dialog_directory(self, fallback=None):
        # Open Media / Open Document / Open Project share the most recently
        # used folder, while retaining the configured project directory as a
        # first-run fallback.
        try:
            remembered = str(self.settings_store.value("last_open_directory", "") or "")
            if remembered and Path(remembered).is_dir():
                return remembered
        except Exception:
            pass
        if self.default_project_directory:
            return self.default_project_directory
        return str(Path(fallback).parent) if fallback else ""

    def _remember_open_directory(self, path):
        try:
            directory = Path(path).resolve().parent if Path(path).suffix else Path(path).resolve()
            if directory.is_dir():
                self.settings_store.setValue("last_open_directory", str(directory))
                self.settings_store.sync()
        except Exception:
            pass

    def _sync_startup_project_actions(self):
        """Synchronize the Project Settings startup radio/check actions."""
        mode = getattr(self, "startup_project_mode", "last")
        if hasattr(self, "startup_new_action"):
            self.startup_new_action.setChecked(mode == "new")
            self.startup_last_action.setChecked(mode == "last")
            self.startup_prompt_action.setChecked(mode == "prompt")

    def set_startup_project_mode(self, mode):
        """Set the startup project policy."""
        if mode not in {"new", "last", "prompt"}:
            return
        self.startup_project_mode = mode
        self.settings_store.setValue("startup_project_mode", mode)
        self._sync_startup_project_actions()

    def restore_last_opened(self):
        """Apply startup policy and offer recovery from a newer autosave snapshot."""
        # If launched with a file argument (e.g. associated .rtvs project or media file), open it directly
        for arg in sys.argv[1:]:
            if not arg.startswith("-"):
                try:
                    arg_path = Path(arg).resolve()
                    if arg_path.is_file():
                        if arg_path.suffix.lower() in (".rtvs", ".json"):
                            self.load_project_file(arg_path, prompt=False, preserve_media=False)
                            self.log_activity(f"[STARTUP] Opened project from command line: {arg_path.name}", mark_dirty=False)
                            return
                        elif arg_path.suffix.lower() in (".txt", ".docx", ".pdf", ".html", ".htm", ".md"):
                            self.open_document_path(arg_path)
                            return
                        else:
                            self.load_media_file(arg_path)
                            return
                except Exception as exc:
                    self.log_activity(f"[STARTUP] Could not open argument '{arg}': {exc}", mark_dirty=False)

        mode = getattr(self, "startup_project_mode", "last")
        raw_saved = str(self.settings_store.value("last_saved_project_path", "") or "")
        if raw_saved:
            saved_path = Path(raw_saved)
            crash_recovery = saved_path.with_suffix(".crash_recovery.rtvs")
            autosave = saved_path.with_suffix(saved_path.suffix + ".autosave")
            try:
                # Check for emergency crash recovery snapshot first
                if crash_recovery.exists() and crash_recovery.is_file():
                    answer = QMessageBox.question(
                        self,
                        "Crash Recovery Found",
                        f"An emergency crash recovery snapshot was found for {saved_path.name}.\n\n"
                        "This snapshot was created immediately prior to an unexpected application termination.\n"
                        "Would you like to recover this unsaved session?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        if self.load_project_file(crash_recovery, prompt=False, preserve_media=False):
                            self.project_file = saved_path
                            self.project_dirty = True
                            if hasattr(self, "update_window_title"):
                                self.update_window_title()
                            self.log_activity(f"[CRASH-RECOVERY] Recovered emergency crash snapshot for {saved_path.name}.", mark_dirty=False)
                            try:
                                crash_recovery.unlink(missing_ok=True)
                            except Exception:
                                pass
                            return
                    else:
                        try:
                            crash_recovery.unlink(missing_ok=True)
                        except Exception:
                            pass

                if autosave.exists() and saved_path.exists() and autosave.stat().st_mtime > saved_path.stat().st_mtime:
                    answer = QMessageBox.question(self, "Recover Auto-Saved Project", f"A newer recovery snapshot was found for {saved_path.name}. Would you like to recover it?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if answer == QMessageBox.StandardButton.Yes:
                        if self.load_project_file(autosave, prompt=False, preserve_media=False):
                            self.project_file = saved_path
                            self.project_dirty = True
                            if hasattr(self, "update_window_title"):
                                self.update_window_title()
                            # The autosave is a recovery artifact, not a recent project.
                            raw_recent = self.settings_store.value("recent_projects", [])
                            try:
                                recent = json.loads(raw_recent) if isinstance(raw_recent, str) else list(raw_recent or [])
                            except Exception:
                                recent = []
                            self.settings_store.setValue("recent_projects", json.dumps([str(x) for x in recent if str(x) != str(autosave.resolve())][:10]))
                            if hasattr(self, "_refresh_recent_projects_menu"):
                                self._refresh_recent_projects_menu()
                            self.log_activity(f"[AUTOSAVE] Recovered newer snapshot for {saved_path.name}.", mark_dirty=False)
                            return
            except Exception as exc:
                self.log_activity(f"[RECOVERY] Recovery check failed: {exc}", mark_dirty=False)

        if mode == "new":
            self.log_activity("[STARTUP] Starting with a new, unsaved project by preference.", mark_dirty=False)
            return

        raw = str(self.settings_store.value("last_saved_project_path", "") or "")
        path = Path(raw) if raw else None
        valid_last = bool(path and path.exists() and path.is_file() and path.suffix.lower() in (".rtvs", ".json"))

        # If last_saved_project_path is missing or stale, fall back to the most recent entry from recent_projects
        if not valid_last:
            raw_recent = self.settings_store.value("recent_projects", [])
            if isinstance(raw_recent, str):
                try:
                    raw_recent = json.loads(raw_recent)
                except Exception:
                    raw_recent = []
            if isinstance(raw_recent, list):
                for candidate in raw_recent:
                    cand_path = Path(str(candidate))
                    if cand_path.exists() and cand_path.is_file() and cand_path.suffix.lower() in (".rtvs", ".json"):
                        path = cand_path
                        valid_last = True
                        self.settings_store.setValue("last_saved_project_path", str(path))
                        self.settings_store.sync()
                        break

        if mode == "prompt":
            if not valid_last:
                self.log_activity("[STARTUP] No previous project is available; starting with a new, unsaved project.", mark_dirty=False)
                return

            box = QMessageBox(self)
            box.setWindowTitle("Project Startup")
            box.setText("What would you like to open?")
            box.setInformativeText(
                "Choose whether to start with a new, unsaved project or reopen "
                "the last project you saved."
            )
            open_last_btn = box.addButton("Open Last Saved Project", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("New Unsaved Project", QMessageBox.ButtonRole.DestructiveRole)
            box.exec()
            if box.clickedButton() is not open_last_btn:
                self.log_activity("[STARTUP] Starting with a new, unsaved project by user choice.", mark_dirty=False)
                return

        if not valid_last:
            self.log_activity("[STARTUP] Last project is unavailable; starting with a new, unsaved project.", mark_dirty=False)
            return

        try:
            data = read_rtvs_project_file(path)
            media = self.resolve_project_media(path, data.get("audio_file"))
            if not data.get("audio_file") or media is not None:
                self.load_project_file(path, prompt=False, preserve_media=False)
                self.log_activity(f"[STARTUP] Restored last project: {path.name}", mark_dirty=False)
            else:
                self.log_activity(
                    "[STARTUP] Last project is available but its media file is missing; starting blank.",
                    mark_dirty=False,
                )
        except Exception as exc:
            self.log_activity(f"[STARTUP] Could not restore last project: {exc}", mark_dirty=False)

    def toggle_speaker_labels(self, checked):
        self.show_speaker_labels = bool(checked)
        self.settings_store.setValue("show_speaker_labels", self.show_speaker_labels)
        if hasattr(self, "colorize_speaker_labels_action"):
            self.colorize_speaker_labels_action.setEnabled(self.show_speaker_labels)
        self.render_transcript()

    def toggle_colorize_speaker_labels(self, checked):
        self.colorize_speaker_labels = bool(checked)
        self.settings_store.setValue("colorize_speaker_labels", self.colorize_speaker_labels)
        if hasattr(self, "colorize_speaker_labels_action"):
            self.colorize_speaker_labels_action.blockSignals(True)
            self.colorize_speaker_labels_action.setChecked(self.colorize_speaker_labels)
            self.colorize_speaker_labels_action.blockSignals(False)
        self.render_transcript()

    def toggle_timestamps(self, checked):
        self.show_timestamps = bool(checked)
        self.settings_store.setValue("show_timestamps", self.show_timestamps)
        if hasattr(self, "show_timestamps_action"):
            self.show_timestamps_action.blockSignals(True)
            self.show_timestamps_action.setChecked(self.show_timestamps)
            self.show_timestamps_action.blockSignals(False)
        self.render_transcript()

    def toggle_milliseconds(self, checked):
        self.show_milliseconds = bool(checked)
        self.settings_store.setValue("show_milliseconds", self.show_milliseconds)
        if hasattr(self, "show_milliseconds_action"):
            self.show_milliseconds_action.blockSignals(True)
            self.show_milliseconds_action.setChecked(self.show_milliseconds)
            self.show_milliseconds_action.blockSignals(False)
        self.render_transcript()

    def toggle_waveform_view(self, checked):
        self.timeline_show_waveform = bool(checked)
        self.settings_store.setValue("timeline_show_waveform", self.timeline_show_waveform)
        if hasattr(self, "timeline"):
            self.timeline.set_timeline_views(self.timeline_show_waveform, self.timeline_show_thumbnails)

    def toggle_thumbnail_view(self, checked):
        self.timeline_show_thumbnails = bool(checked)
        self.settings_store.setValue("timeline_show_thumbnails", self.timeline_show_thumbnails)
        if hasattr(self, "timeline"):
            self.timeline.set_timeline_views(self.timeline_show_waveform, self.timeline_show_thumbnails)

    def choose_default_project_directory(self):
        start = self.default_project_directory or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose Default Project Directory",
            start
        )
        if directory:
            self.default_project_directory = str(Path(directory).resolve())
            self.settings_store.setValue(
                "default_project_directory",
                self.default_project_directory
            )
            self.statusBar().showMessage(
                f"Default project directory: {self.default_project_directory}"
            )

    def open_document_path(self, path):
        path = Path(path).resolve()
        if not path.exists(): return False
        if not self.batch_active and (self.audio_file or self.transcript or self.project_file):
            if not self.prepare_for_new_media(): return False
        try:
            text = read_document_text(path)
        except Exception as exc:
            if not self.batch_active:
                QMessageBox.critical(self, "Open Document Error", f"Could not read document:\n\n{exc}")
            return False
        lines = text.splitlines()
        segments=[]; cursor=0.0
        for line in lines:
            value=line.strip()
            if value:
                segments.append({"text":value,"start":cursor,"end":cursor})
                cursor += 0.001
        # Clear active media player source and waveform peaks when switching to document-only mode
        if hasattr(self, "player") and self.player:
            self.player.stop()
            self.player.setSource(QUrl())
        if hasattr(self, "timeline"):
            self.timeline.set_waveform_peaks([])
            self.timeline.set_audio_filename(None)

        self.audio_file=None; self.project_file=None; self.duration=0.0
        self.transcript={"text":text,"segments":segments,"language":"en"}
        self.diarization=None; self.stories=[]; self.translations={}; self.translation_display_mode="en"
        self.project_dirty=True
        if hasattr(self, "save_action"): self.save_action.setEnabled(True)
        if hasattr(self, "save_as_action"): self.save_as_action.setEnabled(True)
        if hasattr(self, "quick_save_button"): self.quick_save_button.setEnabled(True)
        self.update_translation_language_selector(); self.render_transcript(); self.update_processing_menu_status(); self.set_tools_actions_enabled(True)
        self.statusBar().showMessage(f"Document loaded: {path.name}")
        return True

    def open_clear_cache_dialog(self):
        project_dirs = []
        if getattr(self, "project_file", None):
            try:
                project_dirs.append(Path(self.project_file).parent)
            except Exception:
                pass
        if getattr(self, "audio_file", None):
            try:
                project_dirs.append(Path(self.audio_file).parent)
            except Exception:
                pass
        dialog = ClearCacheDialog(self, language=getattr(self, "language", "en"), project_dirs=project_dirs)
        dialog.exec()

    def open_glossary_dialog(self):
        """Edit persistent terminology used by every ASR and translation backend."""
        from glossary_dialog import GlossaryDialog
        dialog = GlossaryDialog(self)
        dialog.exec()

    def _save_glossary(self):
        self.settings_store.setValue("glossary", json.dumps(self.glossary, ensure_ascii=False))

    def apply_glossary_to_current_transcript(self, entries=None) -> bool:
        """Apply glossary rules and contextual name resolution to the active transcript with Undo support."""
        if not getattr(self, "transcript", None) or not isinstance(self.transcript, dict):
            return False
        if not self.transcript.get("segments"):
            return False
        from terminology import normalize_transcript
        if hasattr(self, "flush_pending_transcript_undo"):
            self.flush_pending_transcript_undo()
        before_state = self._capture_project_state() if hasattr(self, "_capture_project_state") else None
        active_glossary = entries if entries is not None else getattr(self, "glossary", [])
        normalized = normalize_transcript(self.transcript, active_glossary)
        if normalized == self.transcript:
            return False
        self.transcript = normalized
        self.project_dirty = True
        if before_state is not None and hasattr(self, "_commit_project_state_change"):
            self._commit_project_state_change(before_state, "Apply Glossary to Transcript")
        if hasattr(self, "render_transcript"):
            self.render_transcript()
        if hasattr(self, "update_window_title"):
            self.update_window_title()
        if getattr(self, "project_file", None) and hasattr(self, "save_project"):
            try:
                self.save_project()
            except Exception:
                pass
        if hasattr(self, "statusBar") and self.statusBar():
            is_es = getattr(self, "language", "en") == "es"
            self.statusBar().showMessage(
                "Glosario aplicado a la transcripción actual" if is_es else "Applied glossary to current transcript"
            )
        return True

    def add_to_glossary(self, text):
        text = str(text or "").strip().strip(".,!?;:()[]{}\"'“”‘’")
        if not text:
            return
        from terminology import parse_glossary, expand_glossary_rules
        entries = parse_glossary(self.glossary)
        existing_sources = {str(r["source"]).casefold() for r in expand_glossary_rules(entries)}
        if text.casefold() not in existing_sources:
            entries.append({"source": text, "preferred": text, "do_not_translate": True, "match_case": False})
            self.glossary = parse_glossary(entries)
            self._save_glossary()
            self.apply_glossary_to_whisper_context()
            self.apply_glossary_to_current_transcript(self.glossary)
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(f"Added to glossary: {text}")

    def prompt_add_alternate_spelling(self, alternate_text: str):
        """Prompt user for the preferred glossary spelling that `alternate_text` should map to."""
        from PySide6.QtWidgets import QInputDialog
        alt = str(alternate_text or "").strip().strip(".,!?;:()[]{}\"'“”‘’")
        if not alt:
            return
        from terminology import parse_glossary, add_alternate_spelling, sort_glossary_entries
        is_es = getattr(self, "language", "en") == "es"
        entries = sort_glossary_entries(parse_glossary(getattr(self, "glossary", [])), mode="preferred_asc")
        preferred_choices = []
        seen_pref = set()
        for entry in entries:
            p = str(entry.get("preferred", "")).strip()
            if p and p.casefold() not in seen_pref:
                seen_pref.add(p.casefold())
                preferred_choices.append(p)

        title = "Añadir ortografía alternativa" if is_es else "Add Alternate Spelling to Glossary"
        label = (
            f"Seleccione o escriba la ortografía preferida para '{alt}':"
            if is_es else
            f"Select or type the preferred spelling for '{alt}':"
        )
        preferred_term, ok = QInputDialog.getItem(
            self,
            title,
            label,
            preferred_choices if preferred_choices else [alt],
            0,
            True,
        )
        if not ok or not str(preferred_term or "").strip():
            return
        pref_clean = str(preferred_term).strip()
        self.glossary = add_alternate_spelling(
            getattr(self, "glossary", []),
            preferred_term=pref_clean,
            alternate_spelling=alt,
        )
        self._save_glossary()
        self.apply_glossary_to_whisper_context()
        self.apply_glossary_to_current_transcript(self.glossary)
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage(f"Mapped '{alt}' -> '{pref_clean}' in glossary")

    def apply_glossary_to_whisper_context(self):
        # Whisper can use the glossary as contextual vocabulary, but this is
        # only an optional hint. Final spelling is normalized after every ASR
        # backend (Whisper, Parakeet, FastConformer, and future models).
        try:
            from terminology import parse_glossary
            entries = parse_glossary(self.glossary)
            self.whisper_initial_prompt = ", ".join(
                str(e["preferred"]) for e in entries[:200]
            )
        except Exception:
            self.whisper_initial_prompt = ""

    def add_custom_speaker_to_glossary(self, name):
        if name and name.strip():
            self.add_to_glossary(name.strip())

    def set_language(self, language, persist=True):
        self.language = "es" if language == "es" else "en"
        if persist:
            self.settings_store.setValue("language", self.language)
        if hasattr(self, "ui_lang_en_action"):
            self.ui_lang_en_action.blockSignals(True)
            self.ui_lang_en_action.setChecked(self.language != "es")
            self.ui_lang_en_action.blockSignals(False)
        elif hasattr(self, "lang_en_action"):
            self.lang_en_action.blockSignals(True)
            self.lang_en_action.setChecked(self.language != "es")
            self.lang_en_action.blockSignals(False)

        if hasattr(self, "ui_lang_es_action"):
            self.ui_lang_es_action.blockSignals(True)
            self.ui_lang_es_action.setChecked(self.language == "es")
            self.ui_lang_es_action.blockSignals(False)
        elif hasattr(self, "lang_es_action"):
            self.lang_es_action.blockSignals(True)
            self.lang_es_action.setChecked(self.language == "es")
            self.lang_es_action.blockSignals(False)
        self._apply_localization()

    def _apply_localization(self):
        mapping = {
            "&File": "&Archivo", "&Edit": "&Editar", "&View": "&Ver", "&Tools": "&Herramientas", "&Settings": "&Configuración", "&Help": "&Ayuda",
            "&New Project": "&Nuevo proyecto", "&Load Project...": "&Cargar proyecto...", "&Save Project": "&Guardar proyecto", "Save &As...": "Guardar &como...", "&Close Project": "&Cerrar proyecto",
            "&Open Media...": "&Abrir medio...", "Open Document...": "Abrir documento...", "&Export...": "&Exportar...", "E&xit": "&Salir", "&Undo": "&Deshacer", "&Redo": "&Rehacer",
            "&Preferences...": "&Preferencias...", "&Language / Idioma": "&Idioma / Language",
            "Find and Replace...": "Buscar y reemplazar...", "Video Preview": "Vista previa de video", "Timeline": "Línea de tiempo", "Transcript": "Transcripción", "Stories": "Historias", "Activity Log": "Registro de actividad",
            "&Transcribe": "&Transcribir", "&Detect Speakers": "&Detectar hablantes", "&Detect Stories": "&Detectar historias", "&Translate Transcript...": "&Traducir transcripción...", "Manage Models...": "Administrar modelos...",
            "Run Processing…": "Ejecutar procesamiento…", "Custom Vocabulary / Glossary...": "Vocabulario personalizado / glosario...", "Batch Processing...": "Procesamiento por lotes...",
            "Speaker Labels": "Etiquetas de hablantes", "Timestamps": "Marcas de tiempo", "Language": "Idioma", "English": "Inglés", "Spanish": "Español",
            "Search:": "Buscar:", "View:": "Vista:", "Translate…": "Traducir…", "Edit Transcript": "Editar transcripción", "Export Transcript": "Exportar transcripción",
            "Start:": "Inicio:", "End:": "Fin:", "Title:": "Título:", "Range:": "Rango:",
            "Set Story Start": "Fijar inicio de historia", "Set Story End": "Fijar fin de historia",
            "Add Story": "Agregar historia", "Split Story": "Dividir historia", "Merge Stories": "Combinar historias", "Delete Story": "Eliminar historia",
            "Update Selected Story": "Actualizar historia seleccionada", "Delete Selected Story": "Eliminar historia seleccionada",
            "&Regenerate Waveform": "&Regenerar forma de onda", "Regenerate Video &Thumbnails": "Regenerar minia&turas de video",
            "&Clear Temporary Cache...": "&Limpiar caché temporal...", "Clear &Temporary Cache...": "Limpiar caché &temporal...",
            "Cancel Process": "Cancelar proceso", "Export Activity Log": "Exportar registro de actividad", "Clear Log": "Borrar registro", "Speaker Sensitivity": "Sensibilidad de hablantes",
            "▶ Play": "▶ Reproducir", "❚❚ Pause": "❚❚ Pausa", "■ Stop": "■ Detener",
        }
        reverse = {v: k for k, v in mapping.items()}
        active = mapping if self.language == "es" else reverse
        for action in self.findChildren(QAction):
            txt = action.text()
            if txt in active:
                action.setText(active[txt])
        for w in self.findChildren(QLabel):
            if w.text() in active:
                w.setText(active[w.text()])
        for w in self.findChildren(QPushButton):
            if w.text() in active:
                w.setText(active[w.text()])
        for w in self.findChildren(QGroupBox):
            if w.title() in active:
                w.setTitle(active[w.title()])
        if hasattr(self, "transcript_search_input"):
            self.transcript_search_input.setPlaceholderText("Buscar en la transcripción..." if self.language == "es" else "Find in transcript...")
        self.update_story_segment_terminology()

    def update_story_segment_terminology(self):
        """Update all user-facing labels and tooltips using active vocabulary settings."""
        vocab = get_story_vocabulary(self)
        is_es = vocab.is_es

        # Header: "Stories" / "Clips" / "Segments" / "Songs" (or Spanish)
        if hasattr(self, "update_stories_header"):
            self.update_stories_header()
        elif hasattr(self, "stories_header") and self.stories_header is not None:
            self.stories_header.setText(vocab.plural)

        # Add Story / Clip / Segment / Song Button
        if hasattr(self, "add_story_btn") and self.add_story_btn is not None:
            self.add_story_btn.setText(vocab.add_label)
            self.add_story_btn.setToolTip(
                f"Agregar {vocab.singular_lower} desde la selección activa de la línea de tiempo o transcripción" if is_es
                else f"Add {vocab.singular_lower} from active timeline selection or highlighted transcript text"
            )

        # Set Story / Clip / Segment / Song Start Button
        if hasattr(self, "set_story_start_btn") and self.set_story_start_btn is not None:
            self.set_story_start_btn.setText(vocab.set_start)
            self.set_story_start_btn.setToolTip(
                f"Fijar inicio de la {vocab.singular_lower} seleccionada a la posición actual de transcripción o línea de tiempo" if is_es
                else f"Set start time of selected {vocab.singular_lower} to current transcript or timeline position"
            )

        # Set Story / Clip / Segment / Song End Button
        if hasattr(self, "set_story_end_btn") and self.set_story_end_btn is not None:
            self.set_story_end_btn.setText(vocab.set_end)
            self.set_story_end_btn.setToolTip(
                f"Fijar fin de la {vocab.singular_lower} seleccionada a la posición actual de transcripción o línea de tiempo" if is_es
                else f"Set end time of selected {vocab.singular_lower} to current transcript or timeline position"
            )

        # Story Metadata Button
        if hasattr(self, "story_metadata_btn") and self.story_metadata_btn is not None:
            self.story_metadata_btn.setText(vocab.metadata_btn)
            self.story_metadata_btn.setToolTip(
                f"Configurar títulos, autores, categorías, extractos e imágenes destacadas para {vocab.plural_lower} y el episodio completo" if is_es
                else f"Configure titles, authors, categories, excerpts, and featured images for all {vocab.plural_lower} and full episode"
            )

        # Story Settings / Popout Button
        if hasattr(self, "popout_stories_btn") and self.popout_stories_btn is not None:
            self.popout_stories_btn.setText(vocab.settings_btn)

        # Title / Headline input placeholder
        if hasattr(self, "title_input") and self.title_input is not None:
            self.title_input.setPlaceholderText("Título / titular del segmento" if is_es else "Segment title / headline")

        # Author input placeholder
        if hasattr(self, "author_input") and self.author_input is not None:
            self.author_input.setPlaceholderText("Autor / reportero / colaborador del segmento" if is_es else "Segment author / reporter / contributor")

        # Select All Tooltip
        if hasattr(self, "select_all_stories_btn") and self.select_all_stories_btn is not None:
            self.select_all_stories_btn.setToolTip(
                f"Seleccionar todas las {vocab.plural_lower} de la lista" if is_es
                else f"Select all {vocab.plural_lower} in the list"
            )

        # Delete Tooltip
        if hasattr(self, "delete_story_btn") and self.delete_story_btn is not None:
            self.delete_story_btn.setToolTip(
                f"Eliminar {vocab.singular_lower}(s) seleccionada(s)" if is_es
                else f"Delete selected {vocab.singular_lower}(s)"
            )

        # Export Tooltip
        if hasattr(self, "export_stories_btn") and self.export_stories_btn is not None:
            self.export_stories_btn.setToolTip(
                f"Exportar episodio o {vocab.plural_lower} seleccionadas" if is_es
                else f"Export full episode, selected {vocab.plural_lower}, or draft to WordPress"
            )

        # Tools Menu: Detect Stories / Clips / Segments / Songs
        if hasattr(self, "auto_detect_action") and self.auto_detect_action is not None:
            has_stories = hasattr(self, "processing_status") and bool(self.processing_status.get("stories"))
            action_base = vocab.detect_action
            if is_es:
                self.auto_detect_action.setText(f"&{action_base} (Completado)" if has_stories else f"&{action_base}...")
            else:
                self.auto_detect_action.setText(f"{action_base} (Complete)" if has_stories else f"&{action_base}...")

        # View Menu: Stories Panel / Clips Panel / Segments Panel / Songs Panel
        if hasattr(self, "toggle_stories_action") and self.toggle_stories_action is not None:
            self.toggle_stories_action.setText(f"&{vocab.panel_title}")

    def open_document(self):
        filters = (
            "Supported Documents (*.txt *.docx *.pdf *.html *.htm *.md);;"
            "Text Files (*.txt *.md);;"
            "Word Documents (*.docx);;"
            "PDF Files (*.pdf);;"
            "HTML Files (*.html *.htm);;"
            "All Files (*)"
        )
        filename, _ = QFileDialog.getOpenFileName(self, "Open Document", self._dialog_directory(), filters)
        if not filename:
            return

        path = Path(filename).resolve()
        self._remember_open_directory(path)

        if self.audio_file or self.transcript or self.project_file:
            if not self.prepare_for_new_media():
                return

        try:
            text = read_document_text(path)
        except Exception as exc:
            self.log_activity(f"[ERROR] Failed to open document '{path.name}': {exc}")
            QMessageBox.critical(self, "Open Document Error", f"Could not read document:\n\n{exc}")
            return

        lines = text.splitlines()
        segments = []
        cursor = 0.0

        for line in lines:
            value = line.strip()
            if value:
                segments.append({"text": value, "start": cursor, "end": cursor})
                cursor += 0.001

        self.audio_file = None
        self.project_file = None
        self.duration = 0.0
        self.transcript = {"text": text, "segments": segments, "language": "en"}
        self.diarization = None
        self.stories = []
        self.translations = {}
        self.translation_display_mode = "en"
        self.project_dirty = True
        if hasattr(self, "update_window_title"):
            self.update_window_title()

        self.update_translation_language_selector()
        self.render_transcript()
        self.update_processing_menu_status()
        self.set_tools_actions_enabled(True)
        self.statusBar().showMessage(f"Document loaded: {path.name}")
        self.log_activity(f"[FILE] Imported document: {path}")

    def export_text_file(self):
        if not self.transcript: QMessageBox.warning(self,"No Text","There is no transcript/text to export."); return
        default=Path(self.project_file.stem if self.project_file else (self.audio_file.stem if self.audio_file else "transcript")).with_suffix('.txt').name
        filename,_=QFileDialog.getSaveFileName(self,"Export Text",str(Path(self._dialog_directory(default)).joinpath(default)),"Text Files (*.txt);;All Files (*)")
        if not filename: return
        path=Path(filename)
        if path.suffix.lower()!='.txt': path=path.with_suffix('.txt')
        text=self.story_text(self.transcript.get('segments',[])) if self.transcript.get('segments') else self.transcript.get('text','')
        path.write_text(text,encoding='utf-8'); self.log_activity(f"[EXPORT] Exported text to {path.name}"); QMessageBox.information(self,"Export Complete",f"Text exported to:\n{path}")

    def open_media(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Media",
            self._dialog_directory(),
            "Media Files (*.*);;All Files (*)",
        )
        if filename:
            self._remember_open_directory(filename)
            self.load_media_file(filename, source="file dialog")

    def prepare_for_new_media(self):
        """
        Checks for unsaved changes before loading new media.
        Bypasses interactive prompt during batch processing by auto-saving.
        Silently skips prompts if the current project workspace is completely empty.
        """
        is_empty = self.is_project_empty() if hasattr(self, "is_project_empty") else (
            not getattr(self, "audio_file", None) and not getattr(self, "project_file", None)
        )
        if getattr(self, "project_dirty", False) and not is_empty:
            # If running a batch process, auto-save instead of asking via dialog
            if getattr(self, "batch_active", False):
                if self.project_file:
                    self.save_project(force=True)
                elif hasattr(self, "_batch_save_project_file"):
                    self._batch_save_project_file()
                return True

            save_answer = QMessageBox.question(
                self,
                "Save Project?",
                "The current project has unsaved changes. Would you like to save it before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if save_answer == QMessageBox.StandardButton.Cancel:
                return False
            if save_answer == QMessageBox.StandardButton.Save:
                if not self.save_project(force=True):
                    return False
            else:
                self.project_dirty = False

        return True

    def _batch_media_error(self, message: str):
        if hasattr(self, "log_activity"):
            self.log_activity(f"[BATCH ERROR] {message}")
        if not hasattr(self, "batch_failed_items"):
            self.batch_failed_items = []
        curr = getattr(self, "audio_file", None) or "unknown"
        self.batch_failed_items.append((curr, message))

        # If there are remaining files in the batch queue, log and continue processing
        if getattr(self, "batch_active", False) and getattr(self, "batch_queue", None):
            self.log_activity(f"[BATCH WARNING] Skipping failed file '{curr}' and advancing to next item ({len(self.batch_queue)} remaining).")
            self.progress.hide()
            self.cancel_button.hide()
            self.set_processing_stage(None)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self._batch_next_media)
            return

        self.batch_active = False  # Reset active flag on batch failure
        self.progress.hide()
        self.cancel_button.hide()
        self.set_processing_stage(None)
        self.set_tools_actions_enabled(True)

    def _get_batch_project_target_path(self, base_name: str) -> Path:
        """Determines consistent target .rtvs project file path during batch processing."""
        base_dir = self.batch_settings.get("output") if hasattr(self, "batch_settings") else ""
        if not base_dir:
            if hasattr(self, "batch_settings") and self.batch_settings.get("transcripts_output"):
                custom_t = str(self.batch_settings.get("transcripts_output", "")).strip()
                if custom_t:
                    p = Path(custom_t.replace("\\", "/"))
                    if p.name.lower() == "transcripts":
                        base_dir = str(p.parent)
                    else:
                        base_dir = str(p.parent if p.is_dir() or p.suffix else p)
            if not base_dir and self.audio_file:
                base_dir = str(Path(self.audio_file).parent)
            if not base_dir:
                base_dir = self.get_default_save_directory()

        if hasattr(self, "batch_settings") and self.batch_settings.get("unified_transcripts", False):
            projects_dir = Path(base_dir) / "Projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            return projects_dir / f"{base_name}.rtvs"
        else:
            project_dir, _, _, _ = self.prepare_export_directories(
                base_dir, default_name=base_name, prompt_user=False
            )
            if not project_dir:
                project_dir = Path(base_dir)
            return Path(project_dir) / f"{base_name}.rtvs"

    def _batch_save_project_file(self):
        """Saves project .rtvs to dedicated directory structure during batch processing."""
        if not self.audio_file:
            return

        base_name = safe_filename(Path(self.audio_file).stem)

        try:
            target_path = self._get_batch_project_target_path(base_name)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_project_file(str(target_path))
            self.project_file = target_path
            self.project_dirty = False
            self.log_activity(f"[BATCH] Auto-saved project file to {target_path}")
        except Exception as e:
            self.log_activity(f"[BATCH ERROR] Failed to save project file for {self.audio_file}: {e}")

    def _batch_export_current(self):
        """Handles automatic export or project saving during batch processing."""
        if not getattr(self, "batch_active", False) or not hasattr(self, "batch_settings"):
            return

        # 1. Save the project file (.json)
        if self.batch_settings.get("save_project", True) or self.batch_settings.get("save_project_only", False):
            self._batch_save_project_file()

        # 2. If 'Save projects only' is checked, skip generating .txt, .docx, .srt, and media files
        if self.batch_settings.get("save_project_only", False):
            base_name = safe_filename(Path(self.audio_file).stem if self.audio_file else "file")
            self.log_activity(
                f"[BATCH] Finished processing {base_name}. Project session saved (exports skipped: 'Save projects only' mode).",
                mark_dirty=False
            )
            return

        # 3. Otherwise, proceed with requested transcript, subtitle, and media exports
        base_dir = self.batch_settings.get("output") or self.get_default_save_directory()
        if not base_dir or not os.path.exists(base_dir):
            return

        base_name = safe_filename(Path(self.audio_file).stem if self.audio_file else "batch_output")
        unified_transcripts = self.batch_settings.get("unified_transcripts", False)

        if unified_transcripts:
            custom_trans = self.batch_settings.get("transcripts_output", "").strip()
            if custom_trans:
                export_target_dir = Path(custom_trans)
            else:
                export_target_dir = Path(base_dir) / "Transcripts"
            export_target_dir.mkdir(parents=True, exist_ok=True)
            export_directory = str(export_target_dir)
            is_custom = True
        else:
            project_dir, _, _, _ = self.prepare_export_directories(base_dir, default_name=base_name, prompt_user=False)
            export_directory = str(project_dir)
            is_custom = False

        formats = {
            "txt": self.batch_settings.get("full_txt", True) or self.batch_settings.get("story_txt", False),
            "docx": self.batch_settings.get("full_docx", True) or self.batch_settings.get("story_docx", False),
            "srt": self.batch_settings.get("full_srt", False) or self.batch_settings.get("story_srt", False),
            "vtt": self.batch_settings.get("full_vtt", False) or self.batch_settings.get("story_vtt", False),
            "media": False,
        }

        options = {
            "include_speakers": self.batch_settings.get("include_speakers", True),
            "color_speakers": self.batch_settings.get("color_speakers", False),
            "colorize_speakers": self.batch_settings.get("colorize_speakers", False),
            "include_timestamps": self.batch_settings.get("include_timestamps", False),
            "include_english": True,
            "include_spanish": self.batch_settings.get("translate_es", False),
            "translation_direction": self.batch_settings.get("translate_direction", "auto"),
        }

        scope = self.batch_settings.get("scope", "full")

        try:
            if scope in ("full", "both"):
                self.export_full_episode(
                    custom_formats=formats,
                    custom_base=base_name,
                    custom_options=options,
                    directory=export_directory,
                    show_completion=False,
                    is_custom_location=is_custom,
                )

            if scope in ("stories", "both") and self.stories:
                self.perform_stories_export(
                    target_stories=self.stories,
                    custom_formats=formats,
                    custom_base=base_name,
                    custom_options=options,
                    directory=export_directory,
                    show_completion=False,
                    is_custom_location=is_custom,
                )

            self.log_activity(f"[BATCH] Successfully exported files for {base_name} to {export_directory}")
        except Exception as e:
            self.log_activity(f"[BATCH ERROR] Export failed for {base_name}: {e}")

    def load_media_file(self, filename, source="media load", restore_adjacent_project=False):
        path = Path(filename).resolve()
        if not path.exists() or not path.is_file():
            QMessageBox.warning(self, "Open Media", "The selected media file could not be found.")
            return False

        try:
            # This triggers the save/discard/cancel workflow before opening new media[cite: 1]
            if not self.prepare_for_new_media():
                return False
            if not self.confirm_stop_processing_for_media_change():
                return False

            self.media_generation += 1
            self.story_job_token += 1
            self.stop_waveform_worker()
            self.stop_video_thumbnail_worker()

            # Immediately clear existing transcript and project state so stale text doesn't linger
            self.transcript = None
            self.diarization = None
            self.stories = []
            self.translations = {}
            self.segment_speaker_overrides = {}
            self.speaker_names = {}
            from prs_shared import ProjectMetadataDict
            self.project_metadata = ProjectMetadataDict()
            if hasattr(self, "transcript_view"):
                self.transcript_view.clear()
            if hasattr(self, "story_list"):
                self.story_list.clear()

            self.audio_file = path

            # Perform automatic loudness probing & sidecar normalization on import
            eff_media = path
            try:
                from audio_normalization import get_effective_audio_for_processing
                eff = get_effective_audio_for_processing(
                    path,
                    settings_store=getattr(self, "settings_store", None),
                    project_metadata=getattr(self, "project_metadata", None),
                )
                if eff and Path(eff).is_file():
                    eff_media = eff
                norm_info = (getattr(self, "project_metadata", {}) or {}).get("audio_normalization", {})
                if norm_info and "probed_integrated_lufs" in norm_info:
                    lufs = norm_info.get("probed_integrated_lufs")
                    gain = norm_info.get("loudness_gain_db", 0.0)
                    is_q = norm_info.get("is_quiet", False)
                    if is_q:
                        self.log_activity(f"[LOUDNESS] Audio probing complete: Quiet media detected ({lufs:.1f} LUFS, Auto-Boost Gain: +{gain:.1f} dB).", mark_dirty=False)
                    else:
                        self.log_activity(f"[LOUDNESS] Audio probing complete: Compliant media ({lufs:.1f} LUFS).", mark_dirty=False)
            except Exception as norm_err:
                pass

            probed_duration = self.probe_media_duration(eff_media)
            try:
                self.player.setSource(QUrl.fromLocalFile(str(eff_media)))
            except Exception as player_err:
                self.log_activity(f"[MEDIA] Media player initialization notice: {player_err}", mark_dirty=False)
            self.current_media_is_video = self.is_video_file(path)
            self.update_video_preview_state()
            if hasattr(self, "timeline") and hasattr(self.timeline, "set_is_video"):
                self.timeline.set_is_video(self.current_media_is_video)
            if probed_duration is not None:
                self.duration = probed_duration
                self.timeline.set_duration(probed_duration)
                self.time_label.setText(f"{format_time(0)} / {format_time(self.duration)}")

            self.transcribe_action.setEnabled(True)
            self.diarize_action.setEnabled(True)
            self.auto_detect_action.setEnabled(True)
            self.transcribe_diarize_action.setEnabled(True)
            self.transcribe_diarize_detect_action.setEnabled(True)
            if hasattr(self, "regen_waveform_action"):
                self.regen_waveform_action.setEnabled(True)
            if hasattr(self, "regen_thumbnails_action"):
                self.regen_thumbnails_action.setEnabled(bool(self.current_media_is_video))
            if hasattr(self, "normalize_loudness_action"):
                self.normalize_loudness_action.setEnabled(True)
            self.save_action.setEnabled(True)
            if hasattr(self, "quick_save_button"):
                self.quick_save_button.setEnabled(True)
            self.save_as_action.setEnabled(True)

            self.processing_status = {"transcription": False, "diarization": False, "stories": False}
            self.current_selected_story_indices = []
            self.refresh_story_list()

            self.timeline.set_audio_filename(path.name)
            self.timeline.set_waveform_peaks([])
            self.timeline.set_position(0)
            self.timeline.set_zoom(1.0)
            self.timeline.scroll_offset = 0.0
            self.current_position = 0
            self.speaker_status.setText("Speaker detection has not been run.")

            self.log_activity(f"[FILE] Opened media: {path.name} ({source})")

            if self.current_media_is_video:
                self.log_activity("[MEDIA] Video detected; extracting its audio track for waveform generation.")
            self.log_activity("[WAVEFORM] Starting local waveform generation.")
            self.statusBar().showMessage(f"Loaded: {path.name}")
            self.load_waveform_async()
            self.start_video_thumbnail_generation()

            self.project_file = None
            self.project_dirty = False
            self.update_window_title()
            return True
        except Exception as exc:
            self.log_activity(f"[ERROR] Failed to open media '{path.name}': {exc}")
            QMessageBox.critical(self, "Open Media Error", str(exc))
            return False

    def update_active_media_source(self):
        """Update media player source and refresh waveform when normalization state changes."""
        if not getattr(self, "audio_file", None):
            return
        eff_path = Path(self.audio_file).resolve()
        try:
            from audio_normalization import get_effective_audio_for_processing
            eff = get_effective_audio_for_processing(
                self.audio_file,
                settings_store=getattr(self, "settings_store", None),
                project_metadata=getattr(self, "project_metadata", None),
            )
            if eff and Path(eff).is_file():
                eff_path = Path(eff).resolve()
        except Exception:
            pass

        if hasattr(self, "player") and self.player:
            try:
                is_playing = (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
                pos = self.player.position()
                self.player.stop()
                self.player.setSource(QUrl.fromLocalFile(str(eff_path)))
                if pos > 0:
                    self.player.setPosition(pos)
                if is_playing:
                    self.player.play()
            except Exception as err:
                self.log_activity(f"[MEDIA] Player source update notice: {err}", mark_dirty=False)

        proj_file = getattr(self, "project_file", None)
        invalidate_waveform_peak_cache(self.audio_file, project_file=proj_file)
        invalidate_waveform_peak_cache(eff_path, project_file=proj_file)
        self.load_waveform_async(force_regenerate=True)

    def open_audio(self):
        self.open_media()

    def handle_media_drop(self, filename):
        self.load_media_file(filename, source="timeline drag-and-drop")

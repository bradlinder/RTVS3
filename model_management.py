"""Radio & TV Segmenter v1.1.1 — model management responsibilities.

Methods intentionally retain the MainWindow-facing API so behavior remains
maintaining the established MainWindow-facing API while responsibilities are isolated.
"""

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QInputDialog, QMessageBox
from prs_shared import *
try:
    from bootstrap import configure_ssl_certificates
    configure_ssl_certificates()
except Exception:
    pass


from bootstrap import NullWriter, init_null_streams_and_hf_env
init_null_streams_and_hf_env()

try:
    from huggingface_hub.utils import disable_progress_bars
    disable_progress_bars()
except Exception:
    pass


class _DummyTranslationWorker:
    @classmethod
    def model_root(cls, variant="tiny"):
        from core_utils import get_models_storage_dir
        return get_models_storage_dir() / f"opus-mt-{variant}"

    @classmethod
    def model_dir(cls, from_code, to_code, variant="tiny"):
        return cls.model_root(variant) / f"{from_code}-{to_code}"

    @classmethod
    def model_is_installed(cls, from_code, to_code, variant="tiny"):
        target = cls.model_dir(from_code, to_code, variant)
        return (target / "model.bin").exists() or (target / "model.onnx").exists()


def _translation_worker_class():
    """Load translation implementation dynamically without hard-importing from plugins."""
    try:
        import importlib
        mod = importlib.import_module("plugins.translation.worker")
        worker_cls = getattr(mod, "TranslationWorker", None)
        if worker_cls is not None:
            return worker_cls
    except Exception:
        pass
    return _DummyTranslationWorker

def _translation_plugin_installed(self) -> bool:
    manager = getattr(self, "plugin_manager", None)
    return bool(
        manager and
        manager.is_plugin_installed("translation") and
        manager.is_plugin_enabled("translation")
    )


from model_install_workers import (
    WhisperModelInstallWorker,
    DiarizationModelInstallWorker,
    get_diarization_model_dir,
    is_diarization_model_available,
)
from model_cleanup_dialog import (
    ModelCleanupDialog,
    WHISPER_MODEL_CATALOG,
    _stop_and_remove_runtime_env,
)


class ModelManagementMixin:
    def model_cache_candidates(self, model_name):
        """Return all potential candidate directories where model weights might be stored."""
        models_dir = get_models_storage_dir()
        env_dir = os.environ.get("PRS_MODELS_DIR")
        env_path = Path(env_dir) if env_dir else None

        if model_name.startswith("parakeet"):
            res = []
            if env_path:
                res.extend([env_path / "parakeet_onnx", env_path])
            res.extend([
                models_dir / "parakeet_onnx",
                get_app_data_dir() / "models" / "parakeet_onnx",
                Path(__file__).resolve().parent / "models" / "parakeet_onnx",
            ])
            return res
        elif model_name == "fastconformer-es-onnx":
            res = []
            if env_path:
                res.extend([env_path / "fastconformer_es_onnx", env_path])
            res.extend([
                models_dir / "fastconformer_es_onnx",
                get_app_data_dir() / "models" / "fastconformer_es_onnx",
                Path(__file__).resolve().parent / "models" / "fastconformer_es_onnx",
            ])
            return res
        elif model_name == "fastconformer-multilingual-onnx":
            res = []
            if env_path:
                res.extend([env_path / "fastconformer_multilingual_onnx", env_path])
            res.extend([
                models_dir / "fastconformer_multilingual_onnx",
                get_app_data_dir() / "models" / "fastconformer_multilingual_onnx",
                Path(__file__).resolve().parent / "models" / "fastconformer_multilingual_onnx",
            ])
            return res

        # Determine the canonical Hugging Face hub folder slugs
        slugs = []
        if model_name == "distil-large-v3":
            slugs.extend([
                "models--Systran--faster-distil-whisper-large-v3",
                "models--Systran--faster-whisper-distil-large-v3",
                "models--distil-large-v3",
            ])
        elif model_name in ("distil-medium.en", "distil-medium"):
            slugs.extend([
                "models--Systran--faster-distil-whisper-medium.en",
                "models--Systran--faster-whisper-distil-medium.en",
                "models--distil-medium.en",
            ])
        elif model_name.startswith("distil-"):
            slugs.extend([
                f"models--Systran--faster-{model_name}",
                f"models--{model_name}",
            ])
        else:
            slugs.extend([
                f"models--guillaumekcln--faster-whisper-{model_name}",
                f"models--Systran--faster-whisper-{model_name}",
                f"models--openai--whisper-{model_name}",
                f"models--faster-whisper-{model_name}",
                f"models--{model_name}",
            ])

        cache_roots = []
        if env_path:
            cache_roots.extend([env_path / "huggingface" / "hub", env_path / "hub", env_path])
        cache_roots.extend([
            models_dir / "huggingface" / "hub",
            models_dir / "hub",
            models_dir,
            get_app_data_dir() / "models" / "huggingface" / "hub",
            get_app_data_dir() / "models",
            Path.home() / ".cache" / "huggingface" / "hub",
            Path(__file__).resolve().parent / "models",
        ])

        candidates = []
        for cr in cache_roots:
            for slug in slugs:
                candidates.append(cr / slug)
        for slug in slugs:
            clean_dir_name = slug.replace("models--guillaumekcln--", "").replace("models--Systran--", "").replace("models--openai--", "")
            for cr in cache_roots:
                candidates.append(cr / clean_dir_name)
        candidates.append(models_dir / model_name)
        return candidates

    def model_cache_path(self, model_name):
        candidates = self.model_cache_candidates(model_name)
        # 1. Prefer candidate containing actual weights
        for p in candidates:
            if p.exists() and (any(p.rglob("model.bin")) or any(p.rglob("*.bin")) or any(p.rglob("*.safetensors")) or any(p.rglob("*.onnx"))):
                return p

        # 2. Fallback to first existing directory
        for p in candidates:
            if p.exists():
                return p

        return candidates[0]

    def is_whisper_model_available(self, model_name):
        candidates = self.model_cache_candidates(model_name)
        if model_name.startswith("parakeet") or model_name in ("fastconformer-es-onnx", "fastconformer-multilingual-onnx") or model_name.endswith("-onnx"):
            try:
                import sherpa_onnx
            except Exception:
                try:
                    from bootstrap import ensure_sherpa_onnx_runtime
                    if not ensure_sherpa_onnx_runtime():
                        return False
                    import sherpa_onnx
                except Exception:
                    return False
            for p in candidates:
                if not p.exists():
                    continue
                has_tokens = any(f.is_file() and f.name == "tokens.txt" for f in p.rglob("*"))
                has_onnx = any(f.is_file() and f.stat().st_size > 1024 and f.name.endswith(".onnx") for f in p.rglob("*"))
                if has_tokens and has_onnx:
                    return True
            return False

        for p in candidates:
            if not p.exists():
                continue
            has_bin = any(f.is_file() and f.stat().st_size > 1024 and f.name.endswith(".bin") for f in p.rglob("*"))
            has_safetensors = any(f.is_file() and f.stat().st_size > 1024 and f.name.endswith(".safetensors") for f in p.rglob("*"))
            if has_bin or has_safetensors:
                return True
        return False

    def refresh_whisper_model_chooser(self):
        if not hasattr(self, "model_input"):
            return
        current = self.whisper_model
        self.model_input.blockSignals(True)
        self.model_input.clear()
        for model_id, label in WHISPER_MODEL_CATALOG:
            available = self.is_whisper_model_available(model_id)
            display = f"{label} ✓" if available else f"{label} — download when used"
            self.model_input.addItem(display, model_id)
            self.model_input.setItemData(self.model_input.count()-1, model_id, Qt.ItemDataRole.UserRole)
        idx = max(0, self.model_input.findData(current))
        self.model_input.setCurrentIndex(idx)
        self.model_input.blockSignals(False)
        self.update_whisper_model_tooltip()

    def current_whisper_model(self):
        if hasattr(self, "model_input"):
            value = self.model_input.currentData(Qt.ItemDataRole.UserRole)
            if value:
                return str(value)
        return self.whisper_model

    def update_whisper_model_tooltip(self):
        model = self.current_whisper_model()
        available = self.is_whisper_model_available(model)
        label = model.replace("-v3", "").title()
        state = "installed locally" if available else "not downloaded; it will download locally on first use"
        if hasattr(self, "model_input"):
            self.model_input.setToolTip(f"Whisper {label}: {state}. No cloud service is used for processing.")

    def set_whisper_model_from_ui(self, index):
        model = self.model_input.itemData(index, Qt.ItemDataRole.UserRole)
        if not model:
            return
        new_model = str(model)
        changed = new_model != self.whisper_model
        self.whisper_model = new_model
        self.update_whisper_model_tooltip()
        if changed and self.transcript is not None:
            self.processing_status["transcription"] = False
            self.log_activity("[PROCESSING] Whisper model changed; existing transcription is marked for reprocessing.", mark_dirty=False)
        self.mark_project_dirty()
        available = self.is_whisper_model_available(self.whisper_model)
        self.log_activity(f"[SETTINGS] Whisper model set to {self.whisper_model} ({'installed' if available else 'will download locally on first use'}).")
        self.statusBar().showMessage(f"Whisper model: {self.whisper_model}")

    def translation_model_display_name(self, variant=None):
        variant = variant or self.translation_model_variant
        return "OPUS-MT-tiny" if variant == "tiny" else "OPUS-MT"

    def translation_model_root(self, variant=None):
        return _translation_worker_class().model_root(variant or self.translation_model_variant)

    def refresh_translation_model_chooser(self):
        if not hasattr(self, "translation_model_input"): return
        self.translation_model_input.blockSignals(True)
        self.translation_model_input.clear()
        for vid, label in (("tiny", "OPUS-MT-tiny"), ("standard", "OPUS-MT")):
            self.translation_model_input.addItem(label, vid)
        idx = self.translation_model_input.findData(self.translation_model_variant)
        self.translation_model_input.setCurrentIndex(max(0, idx))
        self.translation_model_input.blockSignals(False)
        if hasattr(self, "translation_model_input"):
            self.translation_model_input.setToolTip(f"Preferred local translation model: {self.translation_model_display_name()} . Models download only when needed and remain available offline.")

    def set_translation_model_from_ui(self, index):
        value = self.translation_model_input.itemData(index, Qt.ItemDataRole.UserRole)
        if not value: return
        value = str(value)
        if value == self.translation_model_variant: return
        self.translation_model_variant = value
        self.mark_project_dirty()
        self.log_activity(f"[SETTINGS] Translation model set to {self.translation_model_display_name()}.")
        self.statusBar().showMessage(f"Translation model: {self.translation_model_display_name()}")
        self.refresh_translation_model_chooser()

    def prompt_translation_model(self):
        items = ["OPUS-MT-tiny", "OPUS-MT"]
        current = 0 if self.translation_model_variant == "tiny" else 1
        choice, ok = QInputDialog.getItem(self, "Translation Model", "Preferred translation model:", items, current, False)
        if ok:
            self.translation_model_variant = "tiny" if choice == "OPUS-MT-tiny" else "standard"
            self.refresh_translation_model_chooser()
            self.mark_project_dirty()
            self.log_activity(f"[SETTINGS] Translation model set to {choice}.")

    def open_model_cleanup_dialog(self):
        """Unified local model manager for Whisper and OPUS-MT models."""
        dialog = ModelCleanupDialog(
            self,
            translation_worker_cls_fn=_translation_worker_class,
            translation_plugin_installed_fn=_translation_plugin_installed,
        )
        dialog.exec()

    def purge_all_data_action(self, parent_widget=None, on_complete=None):
        """Purge all downloaded AI models, log files, updater cache, and translation runtimes."""
        parent = parent_widget if parent_widget is not None else getattr(self, "main_window", self)
        answer = QMessageBox.question(
            parent, "Purge All Downloaded Models & Cache",
            "Are you sure you want to purge all downloaded AI models, log files, and runtime caches?\n\n"
            "This will free up disk space across all platforms. Exported audio, video, and project files will NOT be deleted.\n\n"
            "Models can be re-downloaded at any time when needed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            _stop_and_remove_runtime_env(self, "translate", "diarize")
        except Exception:
            pass

        models_dir = get_models_storage_dir()
        if models_dir.exists():
            try:
                shutil.rmtree(models_dir)
                models_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                self.log_activity(f"[MODELS] Error purging models directory: {exc}", mark_dirty=False)

        for wespeaker_path in [Path.home() / ".wespeaker", get_models_storage_dir() / "wespeaker"]:
            if wespeaker_path.exists():
                try:
                    shutil.rmtree(wespeaker_path)
                except Exception as exc:
                    self.log_activity(f"[MODELS] Error purging WeSpeaker cache: {exc}", mark_dirty=False)

        log_dir = get_app_data_dir() / "logs"
        if log_dir.exists():
            try:
                for f in log_dir.glob("*"):
                    if f.is_file():
                        try:
                            f.unlink(missing_ok=True)
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            from updater import cleanup_old_installers
            cleanup_old_installers(force_all=True)
        except Exception:
            pass

        self.log_activity("[MODELS] Purged all downloaded models, log files, and runtime caches.", mark_dirty=False)
        QMessageBox.information(parent, "Purge Complete", "All downloaded AI models, log files, and runtime caches have been removed.")
        self.refresh_whisper_model_chooser()
        if _translation_plugin_installed(self):
            self.refresh_translation_model_chooser()
        if callable(on_complete):
            try:
                on_complete()
            except Exception:
                pass

    def open_translation_model_manager(self):
        # Compatibility alias: translation model management is now consolidated.
        self.open_model_cleanup_dialog()

    def install_whisper_model_for_manager(self, model_name, dialog):
        if getattr(self, "_model_install_thread", None) is not None:
            return

        self._model_install_dialog = dialog
        self._model_install_model = model_name
        self._model_install_kind = "whisper"
        self._model_install_error = None

        # Show main window progress indicator
        self.set_processing_stage("Model Download", f"Whisper {model_name}")
        self.progress.setValue(0)
        self.progress.show()

        self.log_activity(f"[MODELS] Starting download/install for Whisper '{model_name}'...")

        self._model_install_qthread = QThread(self)
        self._model_install_worker = WhisperModelInstallWorker(model_name)
        self._model_install_worker.moveToThread(self._model_install_qthread)
        if hasattr(self, "_track_worker_thread"):
            self._track_worker_thread(self._model_install_qthread)
        self._model_install_qthread.started.connect(self._model_install_worker.run)
        self._model_install_worker.progress.connect(self._on_model_install_progress)
        self._model_install_worker.finished.connect(self._model_install_finished)
        self._model_install_worker.finished.connect(self._model_install_qthread.quit)
        self._model_install_qthread.finished.connect(self._model_install_thread_finished)
        self._model_install_thread = self._model_install_qthread
        self._model_install_qthread.start()
        dialog.refresh_models()

    def cancel_model_installation(self):
        worker = getattr(self, "_model_install_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
        if hasattr(self, "log_activity"):
            self.log_activity("[MODELS] Model download cancellation requested by user.", mark_dirty=False)

    def _on_model_install_progress(self, percent: int, message: str):
        dialog = getattr(self, "_model_install_dialog", None)
        if dialog is not None and hasattr(dialog, "update_install_progress"):
            try:
                dialog.update_install_progress(percent, message)
            except Exception:
                pass
        if hasattr(self, "update_processing_progress"):
            self.update_processing_progress(percent, message)
        elif hasattr(self, "progress"):
            self.progress.setValue(percent)

    def _install_whisper_model_background(self, model_name):
        # Retained as a compatibility method for callers; the actual work now
        # runs in WhisperModelInstallWorker on a QThread.
        error = None
        try:
            if model_name.startswith("parakeet"):
                target_dir = get_models_storage_dir() / "parakeet_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
                for fname in ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]:
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))
            elif model_name == "fastconformer-es-onnx":
                target_dir = get_models_storage_dir() / "fastconformer_es_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-fast-conformer-ctc-es-1424-int8"
                for fname in ["model.int8.onnx", "tokens.txt"]:
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))
            elif model_name == "fastconformer-multilingual-onnx":
                target_dir = get_models_storage_dir() / "fastconformer_multilingual_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                from huggingface_hub import hf_hub_download
                repo_id = "csukuangfj/sherpa-onnx-nemo-fast-conformer-ctc-be-de-en-es-fr-hr-it-pl-ru-uk-20k"
                for fname in ["model.onnx", "tokens.txt"]:
                    hf_hub_download(repo_id=repo_id, filename=fname, local_dir=str(target_dir))
            else:
                if "/" in model_name:
                    resolved = model_name
                else:
                    resolved = f"Systran/faster-whisper-{model_name}"

                cache_dir = str(get_models_storage_dir() / "huggingface" / "hub")
                Path(cache_dir).mkdir(parents=True, exist_ok=True)
                from huggingface_hub import snapshot_download
                snapshot_download(repo_id=resolved, cache_dir=cache_dir)
        except Exception as exc:
            error = str(exc)
        return error

    def _model_install_finished(self, error):
        self._model_install_error = error

    def _model_install_thread_finished(self):
        dialog = getattr(self, "_model_install_dialog", None)
        model_name = getattr(self, "_model_install_model", "")
        error = getattr(self, "_model_install_error", None)
        thread = getattr(self, "_model_install_thread", None)
        if thread is not None:
            thread.deleteLater()
        self._model_install_thread = None
        self._model_install_qthread = None
        self._model_install_worker = None

        self.progress.setValue(100)
        self.progress.hide()
        self.set_processing_stage(None)
        self._model_install_dialog = None
        self._model_install_model = None
        self._model_install_kind = None

        if dialog is not None and hasattr(dialog, "hide_install_progress"):
            try:
                dialog.hide_install_progress()
            except Exception:
                pass

        dialog_is_active = dialog is not None and getattr(dialog, "isVisible", lambda: False)()
        parent_w = dialog if dialog_is_active else getattr(self, "main_window", self)

        if error:
            is_cancelled = "cancelled" in str(error).lower() or "interrupted" in str(error).lower()
            if is_cancelled:
                self.log_activity(f"[MODELS] {model_name} download was cancelled.", mark_dirty=False)
            else:
                self.log_activity(f"[MODELS] {model_name} installation failed: {error}", mark_dirty=False)
                try:
                    QMessageBox.critical(parent_w, "Model Installation Error", f"Could not install {model_name}:\n\n{error}")
                except Exception:
                    pass
        else:
            self.log_activity(f"[MODELS] {model_name} installed and verified.", mark_dirty=False)
            self.refresh_whisper_model_chooser()
            if hasattr(self, "refresh_translation_model_chooser"):
                try:
                    self.refresh_translation_model_chooser()
                except Exception:
                    pass
            try:
                QMessageBox.information(parent_w, "Model Ready", f"Model '{model_name}' is installed and ready for offline use.")
            except Exception:
                pass

        if dialog is not None and hasattr(dialog, "refresh_models"):
            try:
                dialog.refresh_models()
            except Exception:
                pass

    def _poll_model_install(self, dialog):
        # Compatibility no-op; model installation completion is signal-driven.
        return

    def install_diarization_model_for_manager(self, dialog):
        """Install or repair the WeSpeaker ResNet34 ONNX diarization voice embedding model."""
        if getattr(self, "_model_install_thread", None) is not None:
            return

        self._model_install_dialog = dialog
        self._model_install_model = "Speaker Diarization (WeSpeaker ResNet34)"
        self._model_install_kind = "diarize"
        self._model_install_error = None

        self.set_processing_stage("Model Download", "Speaker Diarization Model")
        self.progress.setValue(0)
        self.progress.show()

        self.log_activity("[MODELS] Starting download/install for Speaker Diarization model (WeSpeaker ResNet34 ONNX)...")

        self._model_install_qthread = QThread(self)
        self._model_install_worker = DiarizationModelInstallWorker()
        self._model_install_worker.moveToThread(self._model_install_qthread)
        if hasattr(self, "_track_worker_thread"):
            self._track_worker_thread(self._model_install_qthread)
        self._model_install_qthread.started.connect(self._model_install_worker.run)
        self._model_install_worker.progress.connect(self._on_model_install_progress)
        self._model_install_worker.finished.connect(self._model_install_finished)
        self._model_install_worker.finished.connect(self._model_install_qthread.quit)
        self._model_install_qthread.finished.connect(self._model_install_thread_finished)
        self._model_install_thread = self._model_install_qthread
        self._model_install_qthread.start()
        dialog.refresh_models()

    def install_translation_models_for_manager(self, from_code, to_code, variant, dialog):
        """Install an OPUS-MT model through the translation plugin's isolated runtime."""
        if getattr(self, "_model_install_process", None) is not None or getattr(self, "translation_process", None) is not None:
            return
        if isinstance(from_code, bool): from_code = "en"
        if isinstance(to_code, bool): to_code = "es"
        from_code, to_code, variant = str(from_code), str(to_code), str(variant)

        self._model_install_dialog = dialog
        self._model_install_model = f"OPUS-MT-{variant} ({from_code.upper()} → {to_code.upper()})"
        self._model_install_error = None
        self.set_processing_stage("Model Download", self._model_install_model)
        self.progress.setValue(0); self.progress.show()
        self.log_activity(f"[MODELS] Starting isolated download/install for {self._model_install_model}...")

        request = {
            "segments": [], "from_code": from_code, "to_code": to_code,
            "install_if_missing": True, "installation_only": True,
            "model_variant": variant, "variant": variant, "device": "cpu"
        }

        # Reuse the translation runtime launcher, but keep model-install state separate.
        if not hasattr(self, "_start_translation_runtime_request"):
            self._model_install_error = "Translation runtime support is unavailable."
            self._model_install_thread_finished()
            return

        self._model_install_process = True
        def done(exit_code, stderr, output):
            self._model_install_error = stderr if exit_code != 0 else None
            self._model_install_process = None
            self._model_install_thread_finished()

        # The common launcher tracks translation_process; temporarily use it while
        # model installation is active, then clear it in the completion callback.
        started = self._start_translation_runtime_request(request, on_finished=done)
        if not started:
            self._model_install_process = None
            return


    def _translation_manager_install_finished(self, from_code, to_code, variant, dialog):
        self.progress.setValue(100)
        self.progress.hide()
        self.set_processing_stage(None)

        model_label = f"OPUS-MT-{variant} ({from_code.upper()} → {to_code.upper()})"
        self.log_activity(f"[MODELS] {model_label} installed and verified.", mark_dirty=False)
        self.refresh_translation_model_chooser()

        QMessageBox.information(dialog, "Model Ready", f"{model_label} is installed and ready for offline use.")

        # Post the dialog refresh back onto the main event loop
        if hasattr(dialog, "refresh_models"):
            QTimer.singleShot(0, dialog.refresh_models)

    def _translation_manager_install_error(self, message, dialog):
        self.progress.hide()
        self.set_processing_stage(None)

        self.log_activity(f"[MODELS] Translation model installation failed: {message}", mark_dirty=False)
        QMessageBox.critical(dialog, "Model Installation Error", f"Could not install translation model:\n\n{message}")

        if hasattr(dialog, "refresh_models"):
            QTimer.singleShot(0, dialog.refresh_models)

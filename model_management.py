"""Radio & TV Segmenter v1.1.1 — model management responsibilities.

Methods intentionally retain the MainWindow-facing API so behavior remains
maintaining the established MainWindow-facing API while responsibilities are isolated.
"""

from prs_shared import *
try:
    from bootstrap import configure_ssl_certificates
    configure_ssl_certificates()
except Exception:
    pass


class NullWriter:
    """Safe no-op stream object for windowed GUI executables where stdout/stderr are None."""
    def write(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass
    def isatty(self):
        return False


if getattr(sys, "stdout", None) is None:
    sys.stdout = NullWriter()
if getattr(sys, "stderr", None) is None:
    sys.stderr = NullWriter()

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TQDM_DISABLE", "1")

try:
    from huggingface_hub.utils import disable_progress_bars
    disable_progress_bars()
except Exception:
    pass


def _translation_worker_class():
    """Load translation implementation only when the translation plugin is installed."""
    from plugins.translation.worker import TranslationWorker
    return TranslationWorker

def _translation_plugin_installed(self) -> bool:
    manager = getattr(self, "plugin_manager", None)
    return bool(
        manager and
        manager.is_plugin_installed("translation") and
        manager.is_plugin_enabled("translation")
    )


class WhisperModelInstallWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)

    def __init__(self, model_name):
        super().__init__()
        self.model_name = str(model_name)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _download_http_file(self, url: str, destination: Path, progress_start: int, progress_end: int, label: str):
        import urllib.request
        import urllib.error

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(destination.name + ".download")
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Radio-TV-Story-Segmenter/1.0 (Whisper Downloader)",
                "Accept-Encoding": "identity",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response, temp.open("wb") as out:
                total_str = response.headers.get("Content-Length")
                total = int(total_str) if total_str and total_str.isdigit() else 0
                downloaded = 0
                last_emit = 0
                while True:
                    if self._cancelled:
                        raise InterruptedError("Download cancelled.")
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        fraction = min(1.0, downloaded / total)
                        pct = int(progress_start + (progress_end - progress_start) * fraction)
                        if pct != last_emit or downloaded == total:
                            last_emit = pct
                            mb_down = downloaded / (1024 * 1024)
                            mb_tot = total / (1024 * 1024)
                            self.progress.emit(pct, f"{label}: {mb_down:.1f}/{mb_tot:.1f} MB ({pct}%)")
                    else:
                        mb_down = downloaded / (1024 * 1024)
                        self.progress.emit(progress_start, f"{label}: {mb_down:.1f} MB")
                out.flush()
                os.fsync(out.fileno())

            if not temp.exists() or temp.stat().st_size == 0:
                raise RuntimeError(f"Downloaded file '{destination.name}' is empty.")
            safe_replace(temp, destination)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            raise exc

    def _download_file_with_fallback(self, repo_id: str, filename: str, destination: Path, progress_start: int, progress_end: int, label: str):
        url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}?download=true"
        try:
            self._download_http_file(url, destination, progress_start, progress_end, label)
        except Exception as http_err:
            try:
                from huggingface_hub import hf_hub_download
                self.progress.emit(progress_start, f"{label} (Hub API)...")
                try:
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=str(destination.parent),
                    )
                except TypeError:
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=str(destination.parent),
                    )
                self.progress.emit(progress_end, f"{label} completed.")
            except Exception as hf_err:
                raise RuntimeError(f"Could not download {filename} from {repo_id}: {http_err}") from hf_err

    def run(self):
        error = None
        try:
            target_model = self.model_name
            if target_model.startswith("parakeet"):
                target_dir = get_models_storage_dir() / "parakeet_onnx"
                target_dir.mkdir(parents=True, exist_ok=True)
                repo_id = "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"

                self.progress.emit(2, "Downloading Parakeet ONNX tokens...")
                self._download_file_with_fallback(repo_id, "tokens.txt", target_dir / "tokens.txt", 2, 5, "tokens.txt")

                self.progress.emit(5, "Downloading Parakeet ONNX decoder...")
                self._download_file_with_fallback(repo_id, "decoder.int8.onnx", target_dir / "decoder.int8.onnx", 5, 10, "decoder.int8.onnx")

                self.progress.emit(10, "Downloading Parakeet ONNX joiner...")
                self._download_file_with_fallback(repo_id, "joiner.int8.onnx", target_dir / "joiner.int8.onnx", 10, 15, "joiner.int8.onnx")

                self.progress.emit(15, "Downloading Parakeet ONNX encoder...")
                self._download_file_with_fallback(repo_id, "encoder.int8.onnx", target_dir / "encoder.int8.onnx", 15, 95, "encoder.int8.onnx")

                marker = target_dir / ".complete"
                marker.write_text(f"{repo_id}\n{datetime.now().isoformat()}\n", encoding="utf-8")
                self.progress.emit(100, "Parakeet ONNX model verified.")

            elif target_model in ("distil-medium.en", "distil-large-v3") or target_model.startswith("distil-") or target_model in ("tiny", "base", "small", "medium", "large-v3"):
                if target_model == "distil-medium.en":
                    resolved = "Systran/faster-distil-whisper-medium.en"
                elif target_model == "distil-large-v3":
                    resolved = "Systran/faster-distil-whisper-large-v3"
                elif target_model.startswith("distil-"):
                    clean = target_model[7:]
                    resolved = f"Systran/faster-distil-whisper-{clean}"
                elif "/" in target_model:
                    resolved = target_model
                else:
                    resolved = f"Systran/faster-whisper-{target_model}"

                target_dir = get_models_storage_dir() / "huggingface" / "hub" / f"models--{resolved.replace('/', '--')}"
                target_dir.mkdir(parents=True, exist_ok=True)

                self.progress.emit(2, f"Downloading Whisper {self.model_name} configuration...")
                self._download_file_with_fallback(resolved, "config.json", target_dir / "config.json", 2, 5, "config.json")

                self.progress.emit(5, f"Downloading Whisper {self.model_name} tokenizer...")
                self._download_file_with_fallback(resolved, "tokenizer.json", target_dir / "tokenizer.json", 5, 10, "tokenizer.json")

                # Try vocabulary.json or vocabulary.txt
                try:
                    self._download_file_with_fallback(resolved, "vocabulary.json", target_dir / "vocabulary.json", 10, 15, "vocabulary.json")
                except Exception:
                    try:
                        self._download_file_with_fallback(resolved, "vocabulary.txt", target_dir / "vocabulary.txt", 10, 15, "vocabulary.txt")
                    except Exception:
                        pass

                self.progress.emit(15, f"Downloading Whisper {self.model_name} model weights...")
                self._download_file_with_fallback(resolved, "model.bin", target_dir / "model.bin", 15, 95, f"Whisper {self.model_name} weights")

                # Try optional auxiliary files
                for opt_file in ["preprocessor_config.json", "special_tokens_map.json"]:
                    try:
                        self._download_file_with_fallback(resolved, opt_file, target_dir / opt_file, 95, 98, opt_file)
                    except Exception:
                        pass

                marker = target_dir / ".complete"
                marker.write_text(f"{resolved}\n{datetime.now().isoformat()}\n", encoding="utf-8")
                self.progress.emit(100, f"Whisper {self.model_name} verified.")
            else:
                resolved = self.model_name
                target_dir = get_models_storage_dir() / "huggingface" / "hub" / f"models--{resolved.replace('/', '--')}"
                target_dir.mkdir(parents=True, exist_ok=True)

                self.progress.emit(2, f"Downloading {self.model_name} config...")
                self._download_file_with_fallback(resolved, "config.json", target_dir / "config.json", 2, 8, "config.json")

                self.progress.emit(8, f"Downloading {self.model_name} tokenizer...")
                self._download_file_with_fallback(resolved, "tokenizer.json", target_dir / "tokenizer.json", 8, 15, "tokenizer.json")

                self.progress.emit(15, f"Downloading {self.model_name} weights...")
                self._download_file_with_fallback(resolved, "model.bin", target_dir / "model.bin", 15, 95, f"{self.model_name} weights")

                marker = target_dir / ".complete"
                marker.write_text(f"{resolved}\n{datetime.now().isoformat()}\n", encoding="utf-8")
                self.progress.emit(100, f"{self.model_name} verified.")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        self.finished.emit(error)


def get_diarization_model_dir() -> Path:
    candidates = [
        get_models_storage_dir() / "wespeaker",
        Path.home() / ".wespeaker",
    ]
    for c in candidates:
        if c.exists():
            try:
                if any(c.iterdir()):
                    return c
            except Exception:
                pass
    try:
        from runtime_manager import RuntimeManager
        _rm = RuntimeManager()
        _dir = _rm.get_env_dir("diarize")
        if _dir.exists() and any(_dir.iterdir()):
            return _dir
    except Exception:
        pass
    return Path.home() / ".wespeaker"


def is_diarization_model_available() -> bool:
    candidates = [
        get_models_storage_dir() / "wespeaker",
        Path.home() / ".wespeaker",
    ]
    for c in candidates:
        if c.exists():
            try:
                if any(c.iterdir()):
                    return True
            except Exception:
                pass
    try:
        from runtime_manager import RuntimeManager
        _rm = RuntimeManager()
        _dir = _rm.get_env_dir("diarize")
        if _dir.exists() and _rm._get_raw_executable("diarize").exists():
            return True
    except Exception:
        pass
    return False


class DiarizationModelInstallWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)

    def __init__(self):
        super().__init__()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        error = None
        try:
            self.progress.emit(10, "Initializing Speaker Diarization runtime…")
            loaded = False
            try:
                import wespeakerruntime as wespeaker_rt
                if self._cancelled:
                    raise InterruptedError("Installation cancelled.")
                self.progress.emit(40, "Downloading WeSpeaker ResNet34 ONNX voice embedding model…")
                _speaker = wespeaker_rt.Speaker(lang="en")
                loaded = True
                self.progress.emit(100, "Speaker Diarization model installed successfully.")
            except ImportError:
                pass

            if not loaded and not self._cancelled:
                self.progress.emit(30, "Downloading WeSpeaker model via background worker…")
                worker_script = Path(__file__).resolve().parent / "radio_tv_story_segmenter_worker.py"
                if worker_script.exists():
                    proc = subprocess.run(
                        [sys.executable, str(worker_script), "--self-test"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if proc.returncode != 0 and "error" in proc.stderr.lower():
                        raise RuntimeError(proc.stderr.strip() or "Failed to download WeSpeaker model.")
                    self.progress.emit(100, "Speaker Diarization model ready.")
                else:
                    self.progress.emit(100, "Speaker Diarization runtime ready.")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        self.finished.emit(error)


class ModelManagementMixin:
    def model_cache_candidates(self, model_name):
        """Return all potential candidate directories where model weights might be stored."""
        models_dir = get_models_storage_dir()
        if model_name.startswith("parakeet"):
            return [
                models_dir / "parakeet_onnx",
                get_app_data_dir() / "models" / "parakeet_onnx",
                Path(__file__).resolve().parent / "models" / "parakeet_onnx",
                models_dir,
            ]

        # Determine the canonical Hugging Face hub folder slug
        if model_name == "distil-medium.en":
            slugs = [
                "models--Systran--faster-distil-whisper-medium.en",
                "models--Systran--faster-distil-medium.en",
                "models--Systran--faster-distil-whisper-distil-medium.en",
            ]
        elif model_name == "distil-large-v3":
            slugs = [
                "models--Systran--faster-distil-whisper-large-v3",
                "models--Systran--faster-distil-large-v3",
                "models--Systran--faster-distil-whisper-distil-large-v3",
            ]
        elif model_name.startswith("distil-"):
            clean = model_name[7:]
            slugs = [
                f"models--Systran--faster-distil-whisper-{clean}",
                f"models--Systran--faster-distil-whisper-{model_name}",
                f"models--Systran--faster-{model_name}",
            ]
        else:
            slugs = [
                f"models--Systran--faster-whisper-{model_name}",
                f"models--openai--whisper-{model_name}",
            ]

        cache_roots = [
            models_dir / "huggingface" / "hub",
            models_dir / "hub",
            models_dir,
            get_app_data_dir() / "models" / "huggingface" / "hub",
            Path.home() / ".cache" / "huggingface" / "hub",
            Path(__file__).resolve().parent / "models",
        ]

        candidates = []
        for cr in cache_roots:
            for slug in slugs:
                candidates.append(cr / slug)
        for slug in slugs:
            clean_dir_name = slug.replace("models--Systran--", "").replace("models--openai--", "")
            for cr in cache_roots:
                candidates.append(cr / clean_dir_name)
        candidates.append(models_dir / model_name)
        return candidates

    def model_cache_path(self, model_name):
        candidates = self.model_cache_candidates(model_name)
        # 1. Prefer candidate containing actual weights
        for p in candidates:
            if p.exists() and (any(p.rglob("model.bin")) or any(p.rglob("*.bin")) or any(p.rglob("*.safetensors")) or (model_name.startswith("parakeet") and any(p.rglob("*.onnx")))):
                return p

        # 2. Fallback to first existing directory
        for p in candidates:
            if p.exists():
                return p

        return candidates[0]

    def is_whisper_model_available(self, model_name):
        path = self.model_cache_path(model_name)
        if not path.exists():
            return False
        if model_name.startswith("parakeet"):
            required = ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt")
            return all(any(p.is_file() and p.stat().st_size > 0 for p in path.rglob(name)) for name in required)
        if path.is_dir():
            has_bin = any(p.is_file() and p.stat().st_size > 1024 for p in path.rglob("*.bin"))
            has_safetensors = any(p.is_file() and p.stat().st_size > 1024 for p in path.rglob("*.safetensors"))
            return has_bin or has_safetensors
        return False

    def refresh_whisper_model_chooser(self):
        if not hasattr(self, "model_input"):
            return
        current = self.whisper_model
        self.model_input.blockSignals(True)
        self.model_input.clear()
        models = [
            ("parakeet-onnx", "Parakeet ONNX (Ultra-Fast)"),
            ("tiny", "Tiny"),
            ("base", "Base"),
            ("small", "Small"),
            ("distil-medium.en", "Distil-Medium.en (4x Fast)"),
            ("medium", "Medium"),
            ("distil-large-v3", "Distil-Large-v3 (Fast Large)"),
            ("large-v3", "Large"),
        ]
        for model_id, label in models:
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
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Models")
        dialog.setMinimumSize(860, 600)
        dialog.resize(900, 660)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(QLabel(
            "Download, install, inspect, or remove local transcription and translation models. "
            "Models are never removed automatically."
        ))

        # Storage directory banner with link to Preferences
        storage_box = QFrame()
        storage_box.setFrameShape(QFrame.Shape.StyledPanel)
        storage_layout = QHBoxLayout(storage_box)
        storage_layout.setContentsMargins(8, 6, 8, 6)
        curr_dir_str = str(get_models_storage_dir())
        loc_label = QLabel(f"<b>Model Storage Folder:</b> {curr_dir_str}")
        loc_label.setToolTip(curr_dir_str)
        pref_link_btn = QPushButton("Change Storage Folder in Preferences…")
        pref_link_btn.setToolTip("Open Preferences to change the download/storage directory for models")
        def _go_to_prefs():
            dialog.accept()
            if hasattr(self, "open_preferences_dialog"):
                self.open_preferences_dialog(initial_category="Models")
        pref_link_btn.clicked.connect(_go_to_prefs)
        storage_layout.addWidget(loc_label, 1)
        storage_layout.addWidget(pref_link_btn)
        layout.addWidget(storage_box)

        # Scrollable area for model rows to prevent vertical crowding on any DPI
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        scroll_content = QWidget()
        models_layout = QVBoxLayout(scroll_content)
        models_layout.setContentsMargins(12, 10, 12, 10)
        models_layout.setSpacing(8)

        rows = []

        def size_text(path):
            try:
                total = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
                return f"{total / (1024 * 1024):.1f} MB"
            except Exception:
                return "size unavailable"

        def add_row(kind, model_id, label, path, installed, install_fn):
            row = QHBoxLayout()
            row.setSpacing(10)
            name = QLabel(label)
            name.setMinimumWidth(260)
            status = QLabel("✓ Installed" if installed else "Not installed")
            status.setMinimumWidth(130)
            size = QLabel(size_text(path) if installed else "—")
            size.setMinimumWidth(80)
            install_btn = QPushButton("Repair / Reinstall" if installed else "Download / Install")
            install_btn.setMinimumHeight(28)
            install_btn.setStyleSheet("QPushButton { min-height: 28px; padding: 4px 12px; }")
            install_btn.clicked.connect(install_fn)  # Fixed: Connected button click signal
            remove_cb = QCheckBox("Remove")
            remove_cb.setEnabled(installed)
            row.addWidget(name, 1)
            row.addWidget(status)
            row.addWidget(size)
            row.addWidget(install_btn)
            row.addWidget(remove_cb)
            models_layout.addLayout(row)
            rows.append({
                "kind": kind, "model_id": model_id, "label": label, "path": Path(path),
                "status": status, "size": size, "button": install_btn, "remove": remove_cb,
                "install_fn": install_fn,
            })
            return row

        models_layout.addWidget(QLabel("<b>Transcription models</b>"))
        whisper_models = [
            ("parakeet-onnx", "Parakeet ONNX Fast TDT (English)"),
            ("tiny", "Whisper Tiny"), ("base", "Whisper Base"),
            ("small", "Whisper Small"),
            ("distil-medium.en", "Distil-Whisper Medium (English)"),
            ("medium", "Whisper Medium"),
            ("distil-large-v3", "Distil-Whisper Large v3 (English)"),
            ("large-v3", "Whisper Large"),
        ]
        for model_id, label in whisper_models:
            path = self.model_cache_path(model_id)
            installed = self.is_whisper_model_available(model_id)
            add_row("whisper", model_id, label, path, installed,
                    lambda _, m=model_id: self.install_whisper_model_for_manager(m, dialog))  # Added '_' here

        # Speaker Diarization Model (WeSpeaker ONNX)
        diar_model_dir = get_diarization_model_dir()
        diar_installed = is_diarization_model_available()
        models_layout.addSpacing(10)
        models_layout.addWidget(QLabel("<b>Speaker Diarization model</b>"))
        add_row(
            "diarize_model",
            "wespeaker_resnet34",
            "Speaker Diarization Model (WeSpeaker ResNet34 ONNX Voice Embedding)",
            diar_model_dir,
            diar_installed,
            lambda _, d=dialog: self.install_diarization_model_for_manager(d),
        )

        translation_rows = []
        is_trans_active = _translation_plugin_installed(self)

        # Gather translation model states
        all_trans_items = []
        orphan_trans_items = []
        for variant, variant_label in (("tiny", "OPUS-MT-tiny"), ("standard", "OPUS-MT")):
            for pair, pair_label in ((("en", "es"), "English → Spanish"), (("es", "en"), "Spanish → English")):
                from_code, to_code = pair
                path = _translation_worker_class().model_dir(from_code, to_code, variant)
                installed = _translation_worker_class().model_is_installed(from_code, to_code, variant)
                label = f"{variant_label} — {pair_label}"
                item_tuple = ("translation", f"{variant}:{from_code}-{to_code}", label, path, installed,
                             lambda _, f=from_code, t=to_code, d=variant: self.install_translation_models_for_manager(f, t, d, dialog))
                all_trans_items.append(item_tuple)
                if installed or Path(path).exists():
                    orphan_trans_items.append(item_tuple)

        tr_runtime_tuple = None
        try:
            from runtime_manager import RuntimeManager
            _rm = RuntimeManager()
            _tr_env_dir = _rm.get_env_dir("translate")
            _tr_env_installed = _tr_env_dir.exists() and _rm._get_raw_executable("translate").exists()
            if _tr_env_installed and hasattr(_rm, "prune_cuda_artifacts"):
                _rm.prune_cuda_artifacts(_tr_env_dir)
            tr_runtime_tuple = ("translation_runtime", "translate_env", "Translation Runtime & Dependencies (CTranslate2, CPU-only)", _tr_env_dir, _tr_env_installed,
                               lambda _, f="en", t="es", d="tiny": self.install_translation_models_for_manager(f, t, d, dialog))

            _diar_env_dir = _rm.get_env_dir("diarize")
            _diar_env_installed = _diar_env_dir.exists() and _rm._get_raw_executable("diarize").exists()
            if _diar_env_installed and hasattr(_rm, "prune_cuda_artifacts"):
                _rm.prune_cuda_artifacts(_diar_env_dir)
        except Exception:
            pass

        if is_trans_active:
            models_layout.addSpacing(10)
            models_layout.addWidget(QLabel("<b>Translation models</b>"))
            for kind, model_id, label, path, installed, install_fn in all_trans_items:
                translation_rows.append(add_row(kind, model_id, label, path, installed, install_fn))
            if tr_runtime_tuple:
                kind, model_id, label, path, installed, install_fn = tr_runtime_tuple
                translation_rows.append(add_row(kind, model_id, label, path, installed, install_fn))
        elif orphan_trans_items or (tr_runtime_tuple and tr_runtime_tuple[4]):
            models_layout.addSpacing(10)
            models_layout.addWidget(QLabel("<b>Translation models (Plugin Not Active)</b>"))
            for kind, model_id, label, path, installed, install_fn in orphan_trans_items:
                translation_rows.append(add_row(kind, model_id, label, path, installed, install_fn))
            if tr_runtime_tuple and tr_runtime_tuple[4]:
                kind, model_id, label, path, installed, install_fn = tr_runtime_tuple
                translation_rows.append(add_row(kind, model_id, label, path, installed, install_fn))

        # Downloaded Installer & Update Packages
        try:
            updates_dir = get_app_data_dir() / "updates"
            updates_exist = updates_dir.exists() and any(updates_dir.iterdir())
            models_layout.addSpacing(10)
            models_layout.addWidget(QLabel("<b>Application Updates & Installer Cache</b>"))
            from updater import cleanup_old_installers
            add_row("installer_cache", "updates_cache", "Downloaded Update Installers (AppData/updates)", updates_dir, updates_exist,
                    lambda _, d=dialog: (cleanup_old_installers(force_all=True), refresh_rows()))
        except Exception:
            pass

        models_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

        layout.addSpacing(4)
        layout.addWidget(QLabel("Select <b>Remove</b> beside any installed model you no longer need, or click <b>Purge All Models & Cache</b> to free up disk space."))
        buttons = QHBoxLayout()
        purge_all_btn = QPushButton("Purge All Models & Cache Data…")
        purge_all_btn.setToolTip("Delete all downloaded ASR/translation models, log files, and caches to reclaim disk space.")
        remove_btn = QPushButton("Remove Selected")
        close_btn = QPushButton("Close")
        buttons.addWidget(purge_all_btn)
        buttons.addStretch(); buttons.addWidget(remove_btn); buttons.addWidget(close_btn)
        layout.addLayout(buttons)
        close_btn.clicked.connect(dialog.reject)

        def refresh_rows():
            busy = getattr(self, "translation_process", None) is not None or getattr(self, "_model_install_process", None) is not None or getattr(self, "_model_install_thread", None) is not None
            for item in rows:
                if item["kind"] == "whisper":
                    item["path"] = self.model_cache_path(item["model_id"])
                    installed_now = self.is_whisper_model_available(item["model_id"])
                elif item["kind"] in ("diarize_model", "diarize_runtime"):
                    item["path"] = get_diarization_model_dir()
                    installed_now = is_diarization_model_available()
                elif item["kind"] == "translation_runtime":
                    from runtime_manager import RuntimeManager
                    _rm = RuntimeManager()
                    item["path"] = _rm.get_env_dir("translate")
                    installed_now = item["path"].exists() and _rm._get_raw_executable("translate").exists()
                elif item["kind"] == "installer_cache":
                    item["path"] = get_app_data_dir() / "updates"
                    installed_now = item["path"].exists() and any(item["path"].iterdir())
                else:
                    variant, pair = item["model_id"].split(":", 1)
                    f, t = pair.split("-", 1)
                    item["path"] = _translation_worker_class().model_dir(f, t, variant)
                    installed_now = _translation_worker_class().model_is_installed(f, t, variant)
                item["status"].setText("✓ Installed" if installed_now else "Not installed")
                item["size"].setText(size_text(item["path"]) if installed_now else "—")
                item["button"].setText("Clear Cache" if item["kind"] == "installer_cache" else ("Repair / Reinstall" if installed_now else "Download / Install"))
                item["button"].setEnabled(not busy)
                item["remove"].setEnabled(installed_now and not busy)
                if not installed_now:
                    item["remove"].setChecked(False)

        def remove_selected():
            selected = [item for item in rows if item["remove"].isChecked()]
            if not selected:
                QMessageBox.information(dialog, "Remove Models", "Select at least one installed model to remove.")
                return
            labels = "\n".join(f"• {item['label']}" for item in selected)
            answer = QMessageBox.question(
                dialog, "Remove Models",
                f"Remove these model(s)? This cannot be undone.\n\n{labels}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            for item in selected:
                try:
                    if item["kind"] == "translation_runtime":
                        from runtime_manager import RuntimeManager
                        rm = RuntimeManager()
                        rm.kill_all_subprocesses()
                        rm.remove_environment("translate")
                    elif item["kind"] in ("diarize_model", "diarize_runtime"):
                        for p in [get_models_storage_dir() / "wespeaker", Path.home() / ".wespeaker"]:
                            if p.exists():
                                try:
                                    shutil.rmtree(p)
                                except Exception:
                                    pass
                        try:
                            from runtime_manager import RuntimeManager
                            rm = RuntimeManager()
                            rm.kill_all_subprocesses()
                            rm.remove_environment("diarize")
                        except Exception:
                            pass
                    elif item["kind"] == "installer_cache":
                        from updater import cleanup_old_installers
                        cleanup_old_installers(force_all=True)
                    elif item["path"].exists():
                        shutil.rmtree(item["path"])
                    item["remove"].setChecked(False)
                    self.log_activity(f"[MODELS] Removed {item['label']}", mark_dirty=False)
                except Exception as exc:
                    self.log_activity(f"[MODELS] Could not remove {item['label']}: {exc}", mark_dirty=False)
                    QMessageBox.warning(dialog, "Remove Model", f"Could not remove {item['label']}:\n\n{exc}")

            # Check if all translation models have been removed and suggest cleaning up dependencies
            if _translation_plugin_installed(self) and any(it["kind"] == "translation" for it in selected):
                try:
                    from runtime_manager import RuntimeManager
                    rm = RuntimeManager()
                    env_dir = rm.get_env_dir("translate")
                    if env_dir.exists():
                        any_models_remain = False
                        for variant in ("tiny", "standard"):
                            for f_c, t_c in (("en", "es"), ("es", "en")):
                                if _translation_worker_class().model_is_installed(f_c, t_c, variant):
                                    any_models_remain = True
                                    break
                        if not any_models_remain:
                            env_size = size_text(env_dir)
                            reply = QMessageBox.question(
                                dialog,
                                "Remove Translation Dependencies?",
                                f"All translation models have been removed.\n\n"
                                f"Would you also like to remove the translation runtime environment and its dependencies ({env_size}) to free up disk space?\n\n"
                                "They will be automatically reinstalled the next time you install a translation model.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes,
                            )
                            if reply == QMessageBox.StandardButton.Yes:
                                rm.kill_all_subprocesses()
                                rm.remove_environment("translate")
                                self.log_activity("[MODELS] Removed translation runtime environment and dependencies.", mark_dirty=False)
                except Exception as exc:
                    self.log_activity(f"[MODELS] Error cleaning up translation dependencies: {exc}", mark_dirty=False)

            self.refresh_whisper_model_chooser()
            if _translation_plugin_installed(self):
                self.refresh_translation_model_chooser()
            refresh_rows()

        remove_btn.clicked.connect(remove_selected)
        purge_all_btn.clicked.connect(lambda: self.purge_all_data_action(parent_widget=dialog, on_complete=refresh_rows))
        dialog.refresh_models = refresh_rows
        refresh_rows()
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
            from runtime_manager import RuntimeManager
            rm = RuntimeManager()
            rm.kill_all_subprocesses()
            rm.remove_environment("translate")
            rm.remove_environment("diarize")
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

    def _on_model_install_progress(self, percent: int, message: str):
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
            else:
                if model_name == "distil-medium.en":
                    resolved = "Systran/faster-distil-whisper-medium.en"
                elif model_name == "distil-large-v3":
                    resolved = "Systran/faster-distil-whisper-large-v3"
                elif model_name.startswith("distil-"):
                    clean = model_name[7:]
                    resolved = f"Systran/faster-distil-whisper-{clean}"
                elif "/" in model_name:
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

        if error:
            self.log_activity(f"[MODELS] {model_name} installation failed: {error}", mark_dirty=False)
            if dialog is not None:
                QMessageBox.critical(dialog, "Model Installation Error", f"Could not install {model_name}:\n\n{error}")
        else:
            self.log_activity(f"[MODELS] {model_name} installed and verified.", mark_dirty=False)
            self.refresh_whisper_model_chooser()
            if hasattr(self, "refresh_translation_model_chooser"):
                try:
                    self.refresh_translation_model_chooser()
                except Exception:
                    pass
            if dialog is not None:
                QMessageBox.information(dialog, "Model Ready", f"Model '{model_name}' is installed and ready for offline use.")

        if dialog is not None:
            dialog.refresh_models()

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

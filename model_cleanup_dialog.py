"""Manage Models dialog and shared runtime cleanup helpers for Radio & TV Segmenter."""
from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any, Callable, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core_utils import get_app_data_dir, get_models_storage_dir
from model_install_workers import get_diarization_model_dir, is_diarization_model_available


WHISPER_MODEL_CATALOG = (
    ("parakeet-onnx", "Parakeet ONNX Fast TDT (English)"),
    ("fastconformer-es-onnx", "Spanish FastConformer (Spanish)"),
    ("fastconformer-multilingual-onnx", "Multilingual FastConformer (English & Spanish)"),
    ("tiny", "Whisper Tiny"),
    ("base", "Whisper Base"),
    ("small", "Whisper Small"),
    ("medium", "Whisper Medium"),
    ("large-v3", "Whisper Large v3"),
)


def format_directory_size(path: Any) -> str:
    """Return total size in MB for files under path, or a fallback string."""
    try:
        total = sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
        return f"{total / (1024 * 1024):.1f} MB"
    except Exception:
        return "size unavailable"


def _stop_and_remove_runtime_env(owner: Any, *env_names: str) -> None:
    """Stop tracked subprocesses and remove one or more isolated runtime environments."""
    import runtime_manager

    rm = getattr(owner, "runtime_mgr", None)
    if rm is None:
        rm = runtime_manager.RuntimeManager()
    if hasattr(rm, "kill_all_subprocesses"):
        rm.kill_all_subprocesses()
    else:
        runtime_manager.kill_all_subprocesses()
    if hasattr(rm, "remove_environment"):
        for env_name in env_names:
            rm.remove_environment(env_name)


class ModelCleanupDialog(QDialog):
    """Unified local model manager dialog for ASR, diarization, translation, and cache."""

    def __init__(
        self,
        owner: Any,
        translation_worker_cls_fn: Optional[Callable[[], Any]] = None,
        translation_plugin_installed_fn: Optional[Callable[[Any], bool]] = None,
    ):
        parent = owner if isinstance(owner, QWidget) else None
        super().__init__(parent)
        self.owner = owner
        self._translation_worker_cls_fn = translation_worker_cls_fn
        self._translation_plugin_installed_fn = translation_plugin_installed_fn
        self.rows = []

        self.setWindowTitle("Manage Models")
        self.setMinimumSize(860, 600)
        self.resize(900, 660)
        self._build_ui()
        self.refresh_models()

    def _get_translation_worker_cls(self) -> Any:
        if callable(self._translation_worker_cls_fn):
            return self._translation_worker_cls_fn()
        return None

    def _is_translation_active(self) -> bool:
        if callable(self._translation_plugin_installed_fn):
            return bool(self._translation_plugin_installed_fn(self.owner))
        return False

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
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
            self.accept()
            if hasattr(self.owner, "open_preferences_dialog"):
                self.owner.open_preferences_dialog(initial_category="Models")

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

        def add_row(kind, model_id, label, path, installed, install_fn):
            row = QHBoxLayout()
            row.setSpacing(10)
            name = QLabel(label)
            name.setMinimumWidth(260)
            status = QLabel("✓ Installed" if installed else "Not installed")
            status.setMinimumWidth(130)
            size = QLabel(format_directory_size(path) if installed else "—")
            size.setMinimumWidth(80)
            install_btn = QPushButton("Repair / Reinstall" if installed else "Download / Install")
            install_btn.setMinimumHeight(28)
            install_btn.setStyleSheet("QPushButton { min-height: 28px; padding: 4px 12px; }")
            install_btn.clicked.connect(install_fn)
            remove_cb = QCheckBox("Remove")
            remove_cb.setEnabled(installed)
            row.addWidget(name, 1)
            row.addWidget(status)
            row.addWidget(size)
            row.addWidget(install_btn)
            row.addWidget(remove_cb)
            models_layout.addLayout(row)
            self.rows.append({
                "kind": kind,
                "model_id": model_id,
                "label": label,
                "path": Path(path),
                "status": status,
                "size": size,
                "button": install_btn,
                "remove": remove_cb,
                "install_fn": install_fn,
            })
            return row

        models_layout.addWidget(QLabel("<b>Transcription models</b>"))
        for model_id, label in WHISPER_MODEL_CATALOG:
            path = self.owner.model_cache_path(model_id)
            installed = self.owner.is_whisper_model_available(model_id)
            add_row(
                "whisper",
                model_id,
                label,
                path,
                installed,
                lambda _, m=model_id: self.owner.install_whisper_model_for_manager(m, self),
            )

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
            lambda _, d=self: self.owner.install_diarization_model_for_manager(d),
        )

        # Gather translation model states
        is_trans_active = self._is_translation_active()
        worker_cls = self._get_translation_worker_cls()
        all_trans_items = []
        orphan_trans_items = []
        if worker_cls is not None:
            for variant, variant_label in (("tiny", "OPUS-MT-tiny"), ("standard", "OPUS-MT")):
                for (from_code, to_code), pair_label in ((("en", "es"), "English → Spanish"), (("es", "en"), "Spanish → English")):
                    path = worker_cls.model_dir(from_code, to_code, variant)
                    installed = worker_cls.model_is_installed(from_code, to_code, variant)
                    label = f"{variant_label} — {pair_label}"
                    item_tuple = (
                        "translation",
                        f"{variant}:{from_code}-{to_code}",
                        label,
                        path,
                        installed,
                        lambda _, f=from_code, t=to_code, d=variant: self.owner.install_translation_models_for_manager(f, t, d, self),
                    )
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
            tr_runtime_tuple = (
                "translation_runtime",
                "translate_env",
                "Translation Runtime & Dependencies (CTranslate2, CPU-only)",
                _tr_env_dir,
                _tr_env_installed,
                lambda _, f="en", t="es", d="tiny": self.owner.install_translation_models_for_manager(f, t, d, self),
            )

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
                add_row(kind, model_id, label, path, installed, install_fn)
            if tr_runtime_tuple:
                add_row(*tr_runtime_tuple)
        elif orphan_trans_items or (tr_runtime_tuple and tr_runtime_tuple[4]):
            models_layout.addSpacing(10)
            models_layout.addWidget(QLabel("<b>Translation models (Plugin Not Active)</b>"))
            for kind, model_id, label, path, installed, install_fn in orphan_trans_items:
                add_row(kind, model_id, label, path, installed, install_fn)
            if tr_runtime_tuple and tr_runtime_tuple[4]:
                add_row(*tr_runtime_tuple)

        # Downloaded Installer & Update Packages
        try:
            updates_dir = get_app_data_dir() / "updates"
            updates_exist = updates_dir.exists() and any(updates_dir.iterdir())
            models_layout.addSpacing(10)
            models_layout.addWidget(QLabel("<b>Application Updates & Installer Cache</b>"))
            from updater import cleanup_old_installers

            add_row(
                "installer_cache",
                "updates_cache",
                "Downloaded Update Installers (AppData/updates)",
                updates_dir,
                updates_exist,
                lambda _, d=self: (cleanup_old_installers(force_all=True), self.refresh_models()),
            )
        except Exception:
            pass

        models_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

        # In-dialog progress panel for model downloads
        self.progress_panel = QFrame()
        self.progress_panel.setFrameShape(QFrame.Shape.StyledPanel)
        progress_panel_layout = QVBoxLayout(self.progress_panel)
        progress_panel_layout.setContentsMargins(10, 8, 10, 8)
        progress_panel_layout.setSpacing(6)

        prog_header_row = QHBoxLayout()
        self.prog_status_label = QLabel("Preparing download…")
        self.prog_cancel_btn = QPushButton("Cancel Download")
        self.prog_cancel_btn.setMinimumHeight(24)
        prog_header_row.addWidget(self.prog_status_label, 1)
        prog_header_row.addWidget(self.prog_cancel_btn)
        progress_panel_layout.addLayout(prog_header_row)

        self.dlg_progress_bar = QProgressBar()
        self.dlg_progress_bar.setRange(0, 100)
        self.dlg_progress_bar.setValue(0)
        self.dlg_progress_bar.setTextVisible(True)
        progress_panel_layout.addWidget(self.dlg_progress_bar)

        self.progress_panel.setVisible(False)
        layout.addWidget(self.progress_panel)

        layout.addSpacing(4)
        layout.addWidget(QLabel(
            "Select <b>Remove</b> beside any installed model you no longer need, "
            "or click <b>Purge All Models & Cache</b> to free up disk space."
        ))
        buttons = QHBoxLayout()
        purge_all_btn = QPushButton("Purge All Models & Cache Data…")
        purge_all_btn.setToolTip(
            "Delete all downloaded ASR/translation models, log files, and caches to reclaim disk space."
        )
        remove_btn = QPushButton("Remove Selected")
        close_btn = QPushButton("Close")
        buttons.addWidget(purge_all_btn)
        buttons.addStretch()
        buttons.addWidget(remove_btn)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        close_btn.clicked.connect(self.reject)
        self.prog_cancel_btn.clicked.connect(self.owner.cancel_model_installation)
        remove_btn.clicked.connect(self.remove_selected)
        purge_all_btn.clicked.connect(
            lambda: self.owner.purge_all_data_action(parent_widget=self, on_complete=self.refresh_models)
        )

    def update_install_progress(self, pct: int, msg: str) -> None:
        self.progress_panel.setVisible(True)
        self.dlg_progress_bar.setValue(pct)
        self.prog_status_label.setText(msg)

    def hide_install_progress(self) -> None:
        self.progress_panel.setVisible(False)

    def refresh_models(self) -> None:
        busy = (
            getattr(self.owner, "translation_process", None) is not None
            or getattr(self.owner, "_model_install_process", None) is not None
            or getattr(self.owner, "_model_install_thread", None) is not None
        )
        worker_cls = self._get_translation_worker_cls()
        for item in self.rows:
            if item["kind"] == "whisper":
                item["path"] = self.owner.model_cache_path(item["model_id"])
                installed_now = self.owner.is_whisper_model_available(item["model_id"])
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
                if worker_cls is not None:
                    item["path"] = worker_cls.model_dir(f, t, variant)
                    installed_now = worker_cls.model_is_installed(f, t, variant)
                else:
                    installed_now = False
            item["status"].setText("✓ Installed" if installed_now else "Not installed")
            item["size"].setText(format_directory_size(item["path"]) if installed_now else "—")
            item["button"].setText(
                "Clear Cache"
                if item["kind"] == "installer_cache"
                else ("Repair / Reinstall" if installed_now else "Download / Install")
            )
            item["button"].setEnabled(not busy)
            item["remove"].setEnabled(installed_now and not busy)
            if not installed_now:
                item["remove"].setChecked(False)

    def remove_selected(self) -> None:
        selected = [item for item in self.rows if item["remove"].isChecked()]
        if not selected:
            QMessageBox.information(self, "Remove Models", "Select at least one installed model to remove.")
            return
        labels = "\n".join(f"• {item['label']}" for item in selected)
        answer = QMessageBox.question(
            self,
            "Remove Models",
            f"Remove these model(s)? This cannot be undone.\n\n{labels}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        for item in selected:
            try:
                if item["kind"] == "translation_runtime":
                    _stop_and_remove_runtime_env(self.owner, "translate")
                elif item["kind"] in ("diarize_model", "diarize_runtime"):
                    for p in [get_models_storage_dir() / "wespeaker", Path.home() / ".wespeaker"]:
                        if p.exists():
                            try:
                                shutil.rmtree(p)
                            except Exception:
                                pass
                    try:
                        _stop_and_remove_runtime_env(self.owner, "diarize")
                    except Exception:
                        pass
                elif item["kind"] == "installer_cache":
                    from updater import cleanup_old_installers

                    cleanup_old_installers(force_all=True)
                elif item["path"].exists():
                    shutil.rmtree(item["path"])
                item["remove"].setChecked(False)
                self.owner.log_activity(f"[MODELS] Removed {item['label']}", mark_dirty=False)
            except Exception as exc:
                self.owner.log_activity(f"[MODELS] Could not remove {item['label']}: {exc}", mark_dirty=False)
                QMessageBox.warning(self, "Remove Model", f"Could not remove {item['label']}:\n\n{exc}")

        # Check if all translation models have been removed and suggest cleaning up dependencies
        if self._is_translation_active() and any(it["kind"] == "translation" for it in selected):
            try:
                from runtime_manager import RuntimeManager

                rm = RuntimeManager()
                env_dir = rm.get_env_dir("translate")
                worker_cls = self._get_translation_worker_cls()
                if env_dir.exists() and worker_cls is not None:
                    any_models_remain = any(
                        worker_cls.model_is_installed(f_c, t_c, variant)
                        for variant in ("tiny", "standard")
                        for f_c, t_c in (("en", "es"), ("es", "en"))
                    )
                    if not any_models_remain:
                        env_size = format_directory_size(env_dir)
                        reply = QMessageBox.question(
                            self,
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
                            self.owner.log_activity(
                                "[MODELS] Removed translation runtime environment and dependencies.",
                                mark_dirty=False,
                            )
            except Exception as exc:
                self.owner.log_activity(f"[MODELS] Error cleaning up translation dependencies: {exc}", mark_dirty=False)

        self.owner.refresh_whisper_model_chooser()
        if self._is_translation_active():
            self.owner.refresh_translation_model_chooser()
        self.refresh_models()


__all__ = [
    "WHISPER_MODEL_CATALOG",
    "ModelCleanupDialog",
    "format_directory_size",
    "_stop_and_remove_runtime_env",
]

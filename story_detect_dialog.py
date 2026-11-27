"""Lightweight two-step confirmation and threshold-override dialogs for standalone Story/Segment Detection."""
from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core_utils import apply_window_titlebar_theme


class DetectStoriesSettingsDialog(QDialog):
    """Dedicated dialog for adjusting silence/length detection thresholds for a run or as new defaults."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        silence_threshold: float = 3.0,
        min_story_duration: float = 3.0,
        detection_mode: str = "voice",
        lead_in_padding: float = 0.5,
        save_as_defaults: bool = False,
        default_silence: Optional[float] = None,
        default_min_story: Optional[float] = None,
        default_mode: Optional[str] = None,
        default_padding: Optional[float] = None,
        is_es: bool = False,
    ):
        super().__init__(parent)
        self._is_es = bool(is_es)
        self._default_silence = max(0.5, min(30.0, float(default_silence if default_silence is not None else silence_threshold)))
        self._default_min_story = max(0.0, min(600.0, float(default_min_story if default_min_story is not None else min_story_duration)))
        raw_def_mode = str(default_mode if default_mode is not None else detection_mode).strip().lower()
        self._default_mode = raw_def_mode if raw_def_mode in ("voice", "music") else "voice"
        self._default_padding = max(0.0, min(5.0, float(default_padding if default_padding is not None else lead_in_padding)))

        self.setWindowTitle("Configuración de detección" if self._is_es else "Detection Settings")
        self.setMinimumWidth(400)
        apply_window_titlebar_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        note_txt = (
            "Los cambios se aplicarán solo a esta ejecución a menos que marque la casilla inferior."
            if self._is_es
            else "Changes apply to this run only unless you check the option below."
        )
        note_lbl = QLabel(note_txt)
        note_lbl.setWordWrap(True)
        note_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(note_lbl)

        form = QFormLayout()
        form.setSpacing(8)

        self.silence_spin = QDoubleSpinBox()
        self.silence_spin.setRange(0.5, 30.0)
        self.silence_spin.setSingleStep(0.5)
        self.silence_spin.setDecimals(1)
        self.silence_spin.setSuffix(" sec")
        self.silence_spin.setValue(max(0.5, min(30.0, float(silence_threshold))))
        self.silence_spin.setToolTip("Minimum silence pause duration used to split segments.")
        form.addRow(
            "Umbral de silencio:" if self._is_es else "Silence Gap Threshold:",
            self.silence_spin,
        )

        self.min_story_spin = QDoubleSpinBox()
        self.min_story_spin.setRange(0.0, 600.0)
        self.min_story_spin.setSingleStep(5.0)
        self.min_story_spin.setDecimals(1)
        self.min_story_spin.setSuffix(" sec")
        self.min_story_spin.setValue(max(0.0, min(600.0, float(min_story_duration))))
        self.min_story_spin.setToolTip(
            "Ignore detected segments shorter than this duration to avoid false splits on short pauses."
        )
        form.addRow(
            "Duración mínima:" if self._is_es else "Minimum Segment Length:",
            self.min_story_spin,
        )

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(
            "Voz / Habla (pausas de diálogo)" if self._is_es else "Voice / Speech (Dialog Pauses)",
            "voice",
        )
        self.mode_combo.addItem(
            "Música / Canciones (programas musicales)" if self._is_es else "Music / Track Breaks (Music Programs)",
            "music",
        )
        curr_mode = str(detection_mode or "voice").strip().lower()
        idx_mode = self.mode_combo.findData(curr_mode)
        self.mode_combo.setCurrentIndex(idx_mode if idx_mode >= 0 else 0)
        form.addRow(
            "Base de detección:" if self._is_es else "Detection Basis:",
            self.mode_combo,
        )

        self.pad_spin = QDoubleSpinBox()
        self.pad_spin.setRange(0.0, 5.0)
        self.pad_spin.setSingleStep(0.1)
        self.pad_spin.setDecimals(1)
        self.pad_spin.setSuffix(" sec")
        self.pad_spin.setValue(max(0.0, min(5.0, float(lead_in_padding))))
        form.addRow(
            "Margen inicial:" if self._is_es else "Lead-In Padding:",
            self.pad_spin,
        )
        layout.addLayout(form)

        self.save_defaults_chk = QCheckBox(
            "Guardar estos valores como mis nuevos predeterminados"
            if self._is_es
            else "Save these values as my new defaults"
        )
        self.save_defaults_chk.setChecked(bool(save_as_defaults))
        self.save_defaults_chk.setToolTip(
            "When unchecked, changes apply to this run only and leave Preferences unchanged."
        )
        layout.addWidget(self.save_defaults_chk)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.reset_btn = QPushButton("Restaurar predeterminados" if self._is_es else "Reset to Defaults")
        self.reset_btn.setToolTip("Restore your saved Preferences defaults.")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancelar" if self._is_es else "Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn = QPushButton("Aplicar" if self._is_es else "Apply")
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.apply_btn)
        layout.addLayout(btn_row)

    def reset_to_defaults(self) -> None:
        """Restore all fields to the saved Preferences defaults."""
        self.silence_spin.setValue(self._default_silence)
        self.min_story_spin.setValue(self._default_min_story)
        idx_mode = self.mode_combo.findData(self._default_mode)
        self.mode_combo.setCurrentIndex(idx_mode if idx_mode >= 0 else 0)
        self.pad_spin.setValue(self._default_padding)
        self.save_defaults_chk.setChecked(False)

    def get_values(self) -> Dict[str, Any]:
        return {
            "silence_threshold": float(self.silence_spin.value()),
            "min_story_duration": float(self.min_story_spin.value()),
            "story_detection_mode": str(self.mode_combo.currentData() or "voice"),
            "lead_in_padding": float(self.pad_spin.value()),
            "save_as_defaults": bool(self.save_defaults_chk.isChecked()),
        }


class StandaloneDetectStoriesDialog(QDialog):
    """Simple confirmation dialog for standalone detection with an Adjust Settings... button."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        existing_count: int = 0,
        silence_threshold: float = 3.0,
        min_story_duration: float = 3.0,
        detection_mode: str = "voice",
        lead_in_padding: float = 0.5,
        is_es: bool = False,
        term: str = "Story",
        term_plural: str = "Stories",
    ):
        super().__init__(parent)
        self._is_es = bool(is_es)
        self._term = str(term or "Story")
        self._term_plural = str(term_plural or "Stories")

        self._default_silence = max(0.5, min(30.0, float(silence_threshold or 3.0)))
        self._default_min_story = max(0.0, min(600.0, float(min_story_duration if min_story_duration is not None else 3.0)))
        raw_mode = str(detection_mode or "voice").strip().lower()
        self._default_mode = raw_mode if raw_mode in ("voice", "music") else "voice"
        self._default_padding = max(0.0, min(5.0, float(lead_in_padding if lead_in_padding is not None else 0.5)))

        self._values: Dict[str, Any] = {
            "silence_threshold": self._default_silence,
            "min_story_duration": self._default_min_story,
            "story_detection_mode": self._default_mode,
            "lead_in_padding": self._default_padding,
            "save_as_defaults": False,
        }

        title = f"Detectar {self._term_plural}" if self._is_es else f"Detect {self._term_plural}"
        self.setWindowTitle(title)
        self.setMinimumWidth(390)
        apply_window_titlebar_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        if existing_count > 0:
            if self._is_es:
                msg_txt = (
                    f"La detección reemplazará sus {existing_count} {self._term_plural.lower()} actuales. "
                    "Puede deshacer este cambio con Ctrl+Z."
                )
            else:
                noun = self._term.lower() if existing_count == 1 else self._term_plural.lower()
                msg_txt = (
                    f"Detecting {self._term.lower()} boundaries will replace your current {existing_count} {noun}. "
                    "You can undo this change with Ctrl+Z."
                )
            self.replace_warning_label = QLabel(msg_txt)
            self.replace_warning_label.setWordWrap(True)
            layout.addWidget(self.replace_warning_label)
        else:
            self.replace_warning_label = None
            prompt_txt = (
                f"¿Detectar límites de {self._term_plural.lower()} en este archivo multimedia?"
                if self._is_es
                else f"Detect {self._term.lower()} boundaries across this media file?"
            )
            self.prompt_label = QLabel(prompt_txt)
            self.prompt_label.setWordWrap(True)
            layout.addWidget(self.prompt_label)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.summary_label)
        self._refresh_summary_label()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.adjust_btn = QPushButton("Ajustar configuración..." if self._is_es else "Adjust Settings...")
        self.adjust_btn.setToolTip("Adjust silence gap and segment detection thresholds for this run.")
        self.adjust_btn.clicked.connect(self.open_settings_dialog)
        btn_row.addWidget(self.adjust_btn)
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancelar" if self._is_es else "Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.run_btn = QPushButton(title)
        self.run_btn.setDefault(True)
        self.run_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

    def _is_modified(self) -> bool:
        return (
            abs(self._values["silence_threshold"] - self._default_silence) > 1e-6
            or abs(self._values["min_story_duration"] - self._default_min_story) > 1e-6
            or self._values["story_detection_mode"] != self._default_mode
            or abs(self._values["lead_in_padding"] - self._default_padding) > 1e-6
        )

    def _refresh_summary_label(self) -> None:
        v = self._values
        mode_lbl = (
            ("Música" if v["story_detection_mode"] == "music" else "Voz")
            if self._is_es
            else ("Music" if v["story_detection_mode"] == "music" else "Voice")
        )
        parts = [
            f"{v['silence_threshold']:.1f}s {'silencio' if self._is_es else 'silence gap'}",
            f"{v['min_story_duration']:.1f}s {'mín.' if self._is_es else 'min length'}",
        ]
        if v["story_detection_mode"] != self._default_mode or abs(v["lead_in_padding"] - self._default_padding) > 1e-6:
            parts.append(f"{mode_lbl}, {v['lead_in_padding']:.1f}s {'margen' if self._is_es else 'padding'}")
        suffix = ""
        if self._is_modified() or v["save_as_defaults"]:
            if v["save_as_defaults"]:
                suffix = " (se guardará como predeterminado)" if self._is_es else " (will save as defaults)"
            else:
                suffix = " (solo para esta ejecución)" if self._is_es else " (this run only)"
        prefix = "Configuración:" if self._is_es else "Current settings:"
        self.summary_label.setText(f"{prefix} {', '.join(parts)}{suffix}")

    def create_settings_dialog(self) -> DetectStoriesSettingsDialog:
        """Build the secondary Detection Settings dialog pre-filled with the active staged values."""
        return DetectStoriesSettingsDialog(
            parent=self,
            silence_threshold=self._values["silence_threshold"],
            min_story_duration=self._values["min_story_duration"],
            detection_mode=self._values["story_detection_mode"],
            lead_in_padding=self._values["lead_in_padding"],
            save_as_defaults=self._values["save_as_defaults"],
            default_silence=self._default_silence,
            default_min_story=self._default_min_story,
            default_mode=self._default_mode,
            default_padding=self._default_padding,
            is_es=self._is_es,
        )

    def apply_settings_values(self, values: Dict[str, Any]) -> None:
        """Apply confirmed threshold values from DetectStoriesSettingsDialog and refresh summary."""
        self._values = {
            "silence_threshold": float(values["silence_threshold"]),
            "min_story_duration": float(values["min_story_duration"]),
            "story_detection_mode": str(values["story_detection_mode"] or "voice"),
            "lead_in_padding": float(values["lead_in_padding"]),
            "save_as_defaults": bool(values.get("save_as_defaults", False)),
        }
        self._refresh_summary_label()

    def open_settings_dialog(self) -> bool:
        """Open the dedicated Detection Settings dialog and return to this confirmation dialog on Apply."""
        dlg = self.create_settings_dialog()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.apply_settings_values(dlg.get_values())
            return True
        return False

    def get_values(self) -> Dict[str, Any]:
        return dict(self._values)


__all__ = ["DetectStoriesSettingsDialog", "StandaloneDetectStoriesDialog"]

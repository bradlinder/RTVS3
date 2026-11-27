"""Compact one-time threshold override dialog for standalone Story/Segment Detection."""
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
from prs_shared import CollapsibleSection


class StandaloneDetectStoriesDialog(QDialog):
    """Run-time dialog allowing one-time overrides of silence/length thresholds for standalone detection."""

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
        self._default_mode = str(detection_mode or "voice").strip().lower()
        if self._default_mode not in ("voice", "music"):
            self._default_mode = "voice"
        self._default_padding = max(0.0, min(5.0, float(lead_in_padding if lead_in_padding is not None else 0.5)))

        title = f"Detectar {self._term_plural}" if self._is_es else f"Detect {self._term_plural}"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        apply_window_titlebar_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        if existing_count > 0:
            if self._is_es:
                warn_txt = (
                    f"Esto reemplazará sus {existing_count} {self._term_plural.lower()} actuales. "
                    "Puede deshacer este cambio con Ctrl+Z."
                )
            else:
                noun = self._term.lower() if existing_count == 1 else self._term_plural.lower()
                warn_txt = (
                    f"This will replace your current {existing_count} {noun}. "
                    "You can undo this change with Ctrl+Z."
                )
            self.replace_warning_label = QLabel(warn_txt)
            self.replace_warning_label.setWordWrap(True)
            self.replace_warning_label.setStyleSheet(
                "color: #d97706; font-weight: 600; font-size: 12px;"
            )
            layout.addWidget(self.replace_warning_label)
        else:
            self.replace_warning_label = None

        subtitle_txt = (
            "Ajuste los umbrales solo para esta ejecución o marque la opción inferior para guardarlos como predeterminados."
            if self._is_es
            else "Adjust thresholds for this run only, or check the option below to save them as your defaults."
        )
        self.subtitle_label = QLabel(subtitle_txt)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.subtitle_label)

        primary_form = QFormLayout()
        primary_form.setSpacing(8)

        self.silence_spin = QDoubleSpinBox()
        self.silence_spin.setRange(0.5, 30.0)
        self.silence_spin.setSingleStep(0.5)
        self.silence_spin.setDecimals(1)
        self.silence_spin.setSuffix(" sec")
        self.silence_spin.setValue(self._default_silence)
        self.silence_spin.setToolTip(
            "Minimum silence pause duration used to split segments."
        )
        primary_form.addRow(
            "Umbral de silencio:" if self._is_es else "Silence Gap Threshold:",
            self.silence_spin,
        )

        self.min_story_spin = QDoubleSpinBox()
        self.min_story_spin.setRange(0.0, 600.0)
        self.min_story_spin.setSingleStep(5.0)
        self.min_story_spin.setDecimals(1)
        self.min_story_spin.setSuffix(" sec")
        self.min_story_spin.setValue(self._default_min_story)
        self.min_story_spin.setToolTip(
            "Ignore detected segments shorter than this duration (set higher to avoid false splits on short pauses)."
        )
        primary_form.addRow(
            "Duración mínima:" if self._is_es else "Minimum Segment Length:",
            self.min_story_spin,
        )
        layout.addLayout(primary_form)

        # Secondary parameters tucked inside a collapsed More Options section
        self.more_options_section = CollapsibleSection(
            "Más opciones" if self._is_es else "More Options",
            self,
            is_expanded=False,
        )
        more_form = QFormLayout()
        more_form.setContentsMargins(4, 4, 4, 4)
        more_form.setSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(
            "Voz / Habla (pausas de diálogo)" if self._is_es else "Voice / Speech (Dialog Pauses)",
            "voice",
        )
        self.mode_combo.addItem(
            "Música / Canciones (programas musicales)" if self._is_es else "Music / Track Breaks (Music Programs)",
            "music",
        )
        idx_mode = self.mode_combo.findData(self._default_mode)
        self.mode_combo.setCurrentIndex(idx_mode if idx_mode >= 0 else 0)
        more_form.addRow(
            "Base de detección:" if self._is_es else "Detection Basis:",
            self.mode_combo,
        )

        self.pad_spin = QDoubleSpinBox()
        self.pad_spin.setRange(0.0, 5.0)
        self.pad_spin.setSingleStep(0.1)
        self.pad_spin.setDecimals(1)
        self.pad_spin.setSuffix(" sec")
        self.pad_spin.setValue(self._default_padding)
        more_form.addRow(
            "Margen inicial:" if self._is_es else "Lead-In Padding:",
            self.pad_spin,
        )
        self.more_options_section.add_layout(more_form)
        layout.addWidget(self.more_options_section)

        self.save_defaults_chk = QCheckBox(
            "Guardar estos valores como mis nuevos predeterminados"
            if self._is_es
            else "Save these values as my new defaults"
        )
        self.save_defaults_chk.setChecked(False)
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
        self.run_btn = QPushButton(title)
        self.run_btn.setDefault(True)
        self.run_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

    def reset_to_defaults(self) -> None:
        """Restore spinboxes and mode selector back to the caller's saved Preferences defaults."""
        self.silence_spin.setValue(self._default_silence)
        self.min_story_spin.setValue(self._default_min_story)
        idx_mode = self.mode_combo.findData(self._default_mode)
        self.mode_combo.setCurrentIndex(idx_mode if idx_mode >= 0 else 0)
        self.pad_spin.setValue(self._default_padding)
        self.save_defaults_chk.setChecked(False)

    def get_values(self) -> Dict[str, Any]:
        """Return the selected run-time parameters and default-save flag."""
        return {
            "silence_threshold": float(self.silence_spin.value()),
            "min_story_duration": float(self.min_story_spin.value()),
            "story_detection_mode": str(self.mode_combo.currentData() or "voice"),
            "lead_in_padding": float(self.pad_spin.value()),
            "save_as_defaults": bool(self.save_defaults_chk.isChecked()),
        }


__all__ = ["StandaloneDetectStoriesDialog"]

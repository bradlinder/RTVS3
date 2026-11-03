"""Modal dialog allowing users to selectively clear/purge project components."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core_utils import make_dialog_maximizable


class ProjectDataPurgeDialog(QDialog):
    """Modal dialog allowing users to selectively clear/purge project components."""

    def __init__(self, parent=None, is_es=False):
        super().__init__(parent)
        self.is_es = is_es
        self.setWindowTitle("Limpiar / Purgar datos del proyecto" if is_es else "Clear / Purge Project Data")
        self.resize(540, 440)
        make_dialog_maximizable(self)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header description
        desc_text = (
            "Seleccione los componentes del proyecto que desea purgar o restablecer. "
            "Esta acción se puede deshacer inmediatamente con Edición > Deshacer (Ctrl+Z)."
            if self.is_es else
            "Select the project components you wish to purge or reset. "
            "This action can be undone immediately with Edit > Undo (Ctrl+Z)."
        )
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Warning banner
        warning_box = QLabel(
            "⚠️ Los datos seleccionados se eliminarán de la memoria de la sesión actual."
            if self.is_es else
            "⚠️ Selected data components will be cleared from the active session memory."
        )
        warning_box.setWordWrap(True)
        warning_box.setStyleSheet(
            "background-color: rgba(220, 53, 69, 0.12); color: #dc3545; "
            "border: 1px solid rgba(220, 53, 69, 0.3); border-radius: 6px; padding: 8px 12px; font-weight: bold;"
        )
        layout.addWidget(warning_box)

        # Group box of options
        group_title = "Componentes a purgar" if self.is_es else "Components to Purge"
        group = QGroupBox(group_title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        # Checkboxes
        self.chk_transcript = QCheckBox(
            "Transcripción y palabras temporizadas" if self.is_es else "Transcript & Timed Words"
        )
        self.chk_transcript.setToolTip(
            "Eliminar segmentos de transcripción, marcas de tiempo por palabra y mapas de caracteres."
            if self.is_es else
            "Wipe transcription segments, word-level timestamps, and character maps."
        )

        self.chk_translations = QCheckBox(
            "Traducciones guardadas" if self.is_es else "Saved Translations"
        )
        self.chk_translations.setToolTip(
            "Eliminar traducciones de español/inglés y alineaciones bilingües."
            if self.is_es else
            "Delete saved Spanish/English translation segments and bilingual alignments."
        )

        self.chk_speakers = QCheckBox(
            "Diarización de hablantes" if self.is_es else "Speaker Diarization"
        )
        self.chk_speakers.setToolTip(
            "Restablecer etiquetas de hablantes y nombres personalizados al estado inicial."
            if self.is_es else
            "Reset speaker labels and custom speaker names to unassigned state."
        )

        self.chk_stories = QCheckBox(
            "Historias y metadatos segmentados" if self.is_es else "Stories & Segmented Metadata"
        )
        self.chk_stories.setToolTip(
            "Eliminar todas las historias, límites de tiempo, títulos y resúmenes."
            if self.is_es else
            "Remove all segmented story boundaries, custom titles, and excerpts."
        )

        self.chk_media = QCheckBox(
            "Vínculo de archivo de audio/video" if self.is_es else "Audio / Video Media Link"
        )
        self.chk_media.setToolTip(
            "Desvincular el archivo de medios activo y restablecer la posición de reproducción."
            if self.is_es else
            "Unlink active media file and reset playback position / duration."
        )

        for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media):
            group_layout.addWidget(chk)
            chk.toggled.connect(self._update_purge_button_state)

        layout.addWidget(group)

        # Selection helpers
        sel_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar todo" if self.is_es else "Select All")
        deselect_all_btn = QPushButton("Deseleccionar todo" if self.is_es else "Deselect All")
        select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        deselect_all_btn.clicked.connect(lambda: self._set_all_checked(False))
        sel_layout.addWidget(select_all_btn)
        sel_layout.addWidget(deselect_all_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        layout.addSpacing(6)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar" if self.is_es else "Cancel")
        cancel_btn.clicked.connect(self.reject)

        self.purge_btn = QPushButton("Purgar datos seleccionados" if self.is_es else "Purge Selected Data")
        self.purge_btn.setStyleSheet(
            "QPushButton { background-color: #d9534f; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #c9302c; }"
            "QPushButton:disabled { background-color: #e0e0e0; color: #888888; }"
        )
        self.purge_btn.clicked.connect(self.accept)
        self.purge_btn.setEnabled(False)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.purge_btn)
        layout.addLayout(btn_layout)

    def _set_all_checked(self, checked: bool):
        for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media):
            chk.setChecked(checked)

    def _update_purge_button_state(self):
        any_checked = any(
            chk.isChecked() for chk in (self.chk_transcript, self.chk_translations, self.chk_speakers, self.chk_stories, self.chk_media)
        )
        self.purge_btn.setEnabled(any_checked)

    def get_purge_options(self) -> dict[str, bool]:
        return {
            "transcript": self.chk_transcript.isChecked(),
            "translations": self.chk_translations.isChecked(),
            "speakers": self.chk_speakers.isChecked(),
            "stories": self.chk_stories.isChecked(),
            "media": self.chk_media.isChecked(),
        }


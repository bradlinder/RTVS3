"""Radio & TV Story Segmenter — Export Dialogs & Scope Selection Interface.

Provides dialog UI classes, export format selection modals, export scope routing
(Full Episode, Selected Stories, All Stories), and export completion alerts.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core_utils import safe_filename
from export.dialog import UnifiedExportDialog


def show_export_completion_dialog(parent, title: str, message: str, export_path: str = ""):
    """Displays export completion with an actionable 'Open Folder' button (Milestone 3.11)."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Information)

    open_btn = box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
    close_btn = box.addButton("Close", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(close_btn)

    box.exec()
    if box.clickedButton() == open_btn and export_path:
        folder_to_open = Path(export_path)
        if folder_to_open.is_file():
            folder_to_open = folder_to_open.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_to_open)))


class ExportDialogsMixin:
    """Provides dialog launchers, format selectors, and destination routing for MainWindow."""

    def trigger_export(self):
        """Standard trigger for Export (File menu Ctrl+E / toolbar)."""
        self.open_unified_export_dialog()

    def export_full_transcript(self):
        """Triggered from the Export Transcript button above the transcript view."""
        self.open_unified_export_dialog(initial_scope="full")

    def open_export_scope_dialog(self):
        """Standard trigger for the main toolbar Export button."""
        self.open_unified_export_dialog()

    def open_unified_export_dialog(self, initial_scope: Optional[str] = None, initial_dest: Optional[str] = None, modal: bool = False):
        """Unified Export Dialog entry point for local file exports, WordPress publishing,
        and YouTube Studio assisted exports. Opens as a non-modal floating window by default
        so users can continue editing the transcript side-by-side.
        """
        if not getattr(self, "transcript", None) and not getattr(self, "audio_file", None):
            QMessageBox.warning(self, "Nothing to Export", "There is no transcript or media available to export.")
            return None

        if hasattr(self, "flush_pending_transcript_undo"):
            try:
                self.flush_pending_transcript_undo()
            except Exception:
                pass

        existing = getattr(self, "_active_export_dialog", None)
        if existing is not None and existing.isVisible():
            existing.set_scope_and_destination(scope=initial_scope, dest_id=initial_dest)
            existing.refresh_from_main_window()
            if existing.isMinimized():
                existing.showNormal()
            existing.raise_()
            existing.activateWindow()
            return existing

        if initial_scope is None:
            proj_meta = getattr(self, "project_metadata", None)
            saved_scope = proj_meta.get("last_export_scope") if isinstance(proj_meta, dict) else None
            if saved_scope in ("selected_stories", "all_stories", "full", "full_and_all_stories"):
                initial_scope = saved_scope
            else:
                sel = getattr(self, "current_selected_story_indices", [])
                if sel:
                    initial_scope = "selected_stories"
                elif getattr(self, "stories", []):
                    initial_scope = "all_stories"
                else:
                    initial_scope = "full"

        dialog = UnifiedExportDialog(self, initial_scope=initial_scope, initial_dest=initial_dest)
        self._active_export_dialog = dialog

        def _on_accepted():
            res = dialog.get_result()
            self._dispatch_unified_export_result(res)

        def _on_finished(_code: int):
            if getattr(self, "_active_export_dialog", None) is dialog:
                self._active_export_dialog = None

        dialog.accepted.connect(_on_accepted)
        dialog.finished.connect(_on_finished)

        if modal:
            dialog.exec()
            return dialog

        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def _dispatch_unified_export_result(self, result: dict):
        """Execute the selected export operation after UnifiedExportDialog is accepted."""
        dest = result.get("destination", "local")
        scope = result.get("scope", "full")

        if dest == "local":
            formats = result.get("formats", {})
            base = result.get("base", "")
            options = result.get("options", {})
            export_dir = result.get("export_dir")
            is_custom = bool(export_dir and os.path.isdir(export_dir))

            # Check if user explicitly chose a custom export directory
            if is_custom:
                project_dir = Path(export_dir)
                chosen_name = base
            # Otherwise check if project already lives in an existing folder containing Transcripts/Media
            elif getattr(self, "project_file", None) and (
                (self.project_file.parent / "Transcripts").is_dir()
                or (self.project_file.parent / "Media").is_dir()
            ):
                project_dir, trans_dir, media_dir, chosen_name = self.prepare_export_directories()
            else:
                parent_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Choose Export Location",
                    self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home()),
                )
                if not parent_dir:
                    return
                project_dir, trans_dir, media_dir, chosen_name = self.prepare_export_directories(
                    parent_dir, default_name=base, prompt_user=True
                )

            if not project_dir:
                return

            # Keep project session file saved in project folder, NOT in custom export directory
            if not is_custom:
                if getattr(self, "audio_file", None) or getattr(self, "transcript", None):
                    self._write_project_file(str(project_dir / f"{chosen_name}.rtvs"))
            else:
                if getattr(self, "project_file", None) and (
                    getattr(self, "audio_file", None) or getattr(self, "transcript", None)
                ):
                    self._write_project_file(str(self.project_file))

            # Route exports directly to project_dir
            if scope == "full":
                self.export_full_episode(
                    custom_formats=formats,
                    custom_base=chosen_name,
                    custom_options=options,
                    directory=str(project_dir),
                    is_custom_location=is_custom,
                )
            elif scope == "selected_stories":
                self.export_selected_stories(
                    custom_formats=formats,
                    custom_base=chosen_name,
                    custom_options=options,
                    directory=str(project_dir),
                    is_custom_location=is_custom,
                )
            elif scope == "all_stories":
                self.export_all_stories(
                    custom_formats=formats,
                    custom_base=chosen_name,
                    custom_options=options,
                    directory=str(project_dir),
                    is_custom_location=is_custom,
                )
            elif scope == "full_and_all_stories":
                self.export_full_and_all_stories(
                    custom_formats=formats,
                    custom_base=chosen_name,
                    custom_options=options,
                    directory=str(project_dir),
                    is_custom_location=is_custom,
                )
        elif dest == "timeline":
            formats = result.get("formats", {})
            base = result.get("base", "")
            options = result.get("options", {})
            export_dir = result.get("export_dir")
            is_custom = bool(export_dir and os.path.isdir(export_dir))

            if is_custom:
                project_dir = Path(export_dir)
                chosen_name = base
            elif getattr(self, "project_file", None) and (
                (self.project_file.parent / "Transcripts").is_dir()
                or (self.project_file.parent / "Media").is_dir()
            ):
                project_dir, trans_dir, media_dir, chosen_name = self.prepare_export_directories()
            else:
                parent_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Choose Export Location",
                    self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home()),
                )
                if not parent_dir:
                    return
                project_dir, trans_dir, media_dir, chosen_name = self.prepare_export_directories(
                    parent_dir, default_name=base, prompt_user=True
                )

            if not project_dir:
                return

            self.export_timeline_interchange(
                formats=formats,
                base=chosen_name or base,
                options=options,
                directory=str(project_dir),
                scope=scope,
                is_custom_location=is_custom,
            )
        else:
            handled = False
            if hasattr(self, "plugin_manager") and self.plugin_manager:
                for d in self.plugin_manager.get_export_destinations():
                    if getattr(d, "id", None) == dest and hasattr(d, "execute_export"):
                        d.execute_export(self, result)
                        handled = True
                        break
            if not handled and dest == "youtube":
                if hasattr(self, "_handle_youtube_export_result"):
                    self._handle_youtube_export_result(result)
                handled = True
            elif not handled and getattr(self, "log_activity", None):
                self.log_activity(f"[EXPORT] No handler available for export destination '{dest}'")

    def _choose_export_formats(self, title: str = "Export", allow_media: bool = True):
        """Modal dialog to choose formats and transcript options for classic export flows."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Choose the formats to export."))

        audio_file = getattr(self, "audio_file", None)
        project_file = getattr(self, "project_file", None)

        txt = QCheckBox("Text (.txt)")
        docx = QCheckBox("DOCX (.docx)")
        pdf = QCheckBox("PDF document (.pdf)")
        srt = QCheckBox("SubRip subtitles (.srt)")
        vtt = QCheckBox("WebVTT subtitles (.vtt)")
        media = QCheckBox(f"Media ({audio_file.suffix.lower() if audio_file else 'source format'})")
        media_available = allow_media and audio_file is not None

        txt.setChecked(True)
        docx.setChecked(True)
        pdf.setChecked(True)
        media.setChecked(media_available)
        media.setVisible(media_available)

        layout.addWidget(txt)
        layout.addWidget(docx)
        layout.addWidget(pdf)
        layout.addWidget(srt)
        layout.addWidget(vtt)
        if allow_media:
            layout.addWidget(media)

        default = safe_filename(
            project_file.stem if project_file else (audio_file.stem if audio_file else "export")
        )
        name = QLineEdit(default)
        form = QFormLayout()
        form.addRow("File Name:", name)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        ok = QPushButton("Next")
        cancel = QPushButton("Cancel")
        buttons.addStretch()
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        cancel.clicked.connect(dialog.reject)
        ok.clicked.connect(dialog.accept)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        formats = {
            "txt": txt.isChecked(),
            "docx": docx.isChecked(),
            "pdf": pdf.isChecked(),
            "srt": srt.isChecked(),
            "vtt": vtt.isChecked(),
            "media": media.isChecked() if allow_media else False,
        }
        if not any(formats.values()):
            QMessageBox.warning(self, "Export", "Select at least one export format.")
            return None

        base = safe_filename(name.text().strip() or default)

        opt_dialog = QDialog(self)
        opt_dialog.setWindowTitle("Transcript Content Options")
        opt_dialog.setMinimumWidth(360)
        opt_layout = QVBoxLayout(opt_dialog)
        opt_layout.addWidget(QLabel("Configure content elements for text exports:"))

        include_speakers_cb = QCheckBox("Include Speaker Labels")
        include_speakers_cb.setChecked(True)

        include_timestamps_cb = QCheckBox("Include Timestamps")
        include_timestamps_cb.setChecked(False)

        opt_layout.addWidget(include_speakers_cb)
        opt_layout.addWidget(include_timestamps_cb)

        opt_layout.addSpacing(6)
        opt_layout.addWidget(QLabel("<b>Language Tracks:</b>"))

        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        has_translation = False
        if hasattr(self, "get_spanish_translation_item"):
            trans_item = self.get_spanish_translation_item()
            if trans_item and isinstance(trans_item, dict):
                has_translation = bool(trans_item.get("segments"))

        if src_code == "es":
            include_spanish_cb = QCheckBox("Include Spanish Transcript")
            include_spanish_cb.setChecked(True)
            include_spanish_cb.setEnabled(True)

            include_english_cb = QCheckBox("Include English Transcript (Translated)")
            include_english_cb.setChecked(has_translation)
            include_english_cb.setEnabled(has_translation)
            if not has_translation:
                include_english_cb.setToolTip("English translation is not available or up to date for this project.")
        else:
            include_english_cb = QCheckBox("Include English Transcript")
            include_english_cb.setChecked(True)
            include_english_cb.setEnabled(True)

            include_spanish_cb = QCheckBox("Include Spanish Transcript (Translated)")
            include_spanish_cb.setChecked(has_translation)
            include_spanish_cb.setEnabled(has_translation)
            if not has_translation:
                include_spanish_cb.setToolTip("Spanish translation is not available or up to date for this project.")

        opt_layout.addWidget(include_english_cb)
        opt_layout.addWidget(include_spanish_cb)

        opt_buttons = QHBoxLayout()
        opt_ok = QPushButton("Export")
        opt_cancel = QPushButton("Cancel")
        opt_buttons.addStretch()
        opt_buttons.addWidget(opt_ok)
        opt_buttons.addWidget(opt_cancel)
        opt_layout.addLayout(opt_buttons)

        opt_cancel.clicked.connect(opt_dialog.reject)
        opt_ok.clicked.connect(opt_dialog.accept)

        if opt_dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        if (
            (formats["txt"] or formats["docx"])
            and not include_english_cb.isChecked()
            and not include_spanish_cb.isChecked()
        ):
            QMessageBox.warning(
                self,
                "Export Options",
                "Please select at least one language track (English or Spanish) to export text content.",
            )
            return None

        options = {
            "include_speakers": include_speakers_cb.isChecked(),
            "include_timestamps": include_timestamps_cb.isChecked(),
            "include_english": include_english_cb.isChecked(),
            "include_spanish": include_spanish_cb.isChecked(),
        }

        return formats, base, options

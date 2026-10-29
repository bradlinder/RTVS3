# project_export.pyi — Typing and Interface Stub for project_export
from __future__ import annotations
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
import sys
import warnings
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressDialog, QPushButton, QVBoxLayout
from core_utils import safe_filename, safe_process_events, format_time, is_sentence_end, ffmpeg_path
from prs_shared import *
from project_lifecycle import ProjectLifecycleMixin
from export_dialogs import show_export_completion_dialog, ExportDialogsMixin, UnifiedExportDialog
from export_media_clipper import ExportMediaClipperMixin, render_audio_track, extract_audio_clip
from export_documents import ExportDocumentsMixin, TranscriptPdfWriter, create_story_docx, seconds_to_cue_time, generate_cue_sheet, generate_youtube_chapters, generate_srt_content, generate_vtt_content, generate_cue_content, generate_reaper_project, generate_samplitude_edl, generate_fcp7_xml, generate_fcpxml, generate_aaf_interchange, generate_hindenburg_session, generate_audacity_labels, generate_audition_xml, generate_daw_marker_csv, MIN_WORDS_PER_PARAGRAPH
from export_story_pipeline import ExportStoryPipelineMixin

class ProjectExportMixin(ExportDialogsMixin, ExportMediaClipperMixin, ExportDocumentsMixin, ExportStoryPipelineMixin, ProjectLifecycleMixin):
    _VALID_MEDIA_EXTENSIONS = ...

    def export_project_archive(self, destination_zip: Optional[str]=...) -> bool:
        ...

    def ensure_project_for_processing_pipeline(self) -> bool:
        ...

    def resolve_project_media(self, project_file: Path, audio_reference: Optional[str], audio_file_abs: Optional[str]=...) -> Optional[Path]:
        ...

    def closeEvent(self, event):
        ...

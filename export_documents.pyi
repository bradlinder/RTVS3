# export_documents.pyi — Typing and Interface Stub for export_documents
from __future__ import annotations
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from core_utils import safe_filename, is_sentence_end
from export_dialogs import show_export_completion_dialog
from export.pdf import TranscriptPdfWriter
from export.docx import create_story_docx
from export.subtitles import seconds_to_cue_time, generate_cue_sheet, generate_youtube_chapters, generate_srt_content, generate_vtt_content, generate_cue_content
from export.timeline import generate_reaper_project, generate_samplitude_edl, generate_fcp7_xml, generate_fcpxml, generate_aaf_interchange, generate_hindenburg_session, generate_audacity_labels, generate_audition_xml, generate_cue_sheet as generate_timeline_cue_sheet, generate_daw_marker_csv

class ExportDocumentsMixin:

    def _subtitle_timestamp(self, seconds: float, vtt: bool=...) -> str:
        ...

    def write_subtitles(self, blocks: List[Dict[str, Any]], path: str, fmt: str=..., include_speakers: bool=...):
        ...

    def transcript_for_range(self, start: Optional[float], end: Optional[float]) -> List[Dict[str, Any]]:
        ...

    def speaker_for_segment(self, segment: Any) -> str:
        ...

    def clean_export_text(self, text: Any, current_speaker: str=...) -> str:
        ...

    def build_story_blocks(self, segments: List[Any]) -> List[Dict[str, Any]]:
        ...

    def story_text(self, segments: List[Any]) -> str:
        ...

    def add_story_to_docx(self, document: Any, segments: List[Any]):
        ...

    def _get_transcript_text_slice(self, start: float, end: float | None=...) -> str:
        ...

    def export_cue_sheet(self, destination_path: Optional[str]=...) -> bool:
        ...

    def export_tracklist(self, destination_path: Optional[str]=...) -> bool:
        ...

    def _get_unselected_audio_mode_pref(self) -> str:
        ...

    def export_reaper_project(self, destination_path: Optional[str]=..., unselected_audio_mode: Optional[str]=...) -> bool:
        ...

    def export_samplitude_edl(self, destination_path: Optional[str]=..., unselected_audio_mode: Optional[str]=...) -> bool:
        ...

    def export_audacity_labels(self, destination_path: Optional[str]=..., unselected_audio_mode: Optional[str]=...) -> bool:
        ...

    def export_audition_xml(self, destination_path: Optional[str]=..., unselected_audio_mode: Optional[str]=...) -> bool:
        ...

    def export_daw_marker_csv(self, destination_path: Optional[str]=..., unselected_audio_mode: Optional[str]=...) -> bool:
        ...

    def copy_youtube_chapters_to_clipboard(self) -> bool:
        ...

    def export_timeline_interchange(self, formats: dict, base: str, options: dict, directory: str, scope: str=..., is_custom_location: bool=...) -> bool:
        ...

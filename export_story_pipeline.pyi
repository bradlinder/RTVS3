# export_story_pipeline.pyi — Typing and Interface Stub for export_story_pipeline
from __future__ import annotations
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from core_utils import safe_filename, safe_process_events, format_time
from export_dialogs import show_export_completion_dialog
from export.pdf import TranscriptPdfWriter
from export.docx import create_story_docx
from speaker_palette import SpeakerColorAssigner
from export.subtitles import generate_cue_sheet, generate_youtube_chapters
from export.timeline import generate_reaper_project, generate_samplitude_edl, generate_audacity_labels, generate_audition_xml, generate_daw_marker_csv

class ExportStoryPipelineMixin:

    def _export_story_files(self, stories_with_indices: List[Tuple[int, Any]], formats: Dict[str, bool], base: str, options: Dict[str, Any], directory: str, start_idx: int=..., total_batch: Optional[int]=..., is_custom_location: bool=...) -> bool:
        ...

    def _do_export_story_files(self, stories_with_indices: List[Tuple[int, Any]], formats: Dict[str, bool], base: str, options: Dict[str, Any], directory: str, start_idx: int=..., total_batch: Optional[int]=..., is_custom_location: bool=...) -> bool:
        ...

    def _export_daw_interchange_files(self, formats: Dict[str, bool], stories: List[Any], base: str, transcripts_out: Path, audio_file: Optional[Path], options: Dict[str, Any], default_track: str=..., default_scope: str=...) -> None:
        ...

    def export_selected_stories(self, custom_formats: Optional[Dict[str, bool]]=..., custom_base: Optional[str]=..., custom_options: Optional[Dict[str, Any]]=..., directory: Optional[str]=..., is_custom_location: bool=...):
        ...

    def export_all_stories(self, custom_formats: Optional[Dict[str, bool]]=..., custom_base: Optional[str]=..., custom_options: Optional[Dict[str, Any]]=..., directory: Optional[str]=..., is_custom_location: bool=...):
        ...

    def export_full_and_all_stories(self, custom_formats: Optional[Dict[str, bool]]=..., custom_base: Optional[str]=..., custom_options: Optional[Dict[str, Any]]=..., directory: Optional[str]=..., is_custom_location: bool=...):
        ...

    def export_full_episode(self, custom_formats: Optional[Dict[str, bool]]=..., custom_base: Optional[str]=..., custom_options: Optional[Dict[str, Any]]=..., directory: Optional[str]=..., show_completion: bool=..., progress_dialog: Optional[QProgressDialog]=..., progress_value: int=..., is_custom_location: bool=...) -> bool:
        ...

    def perform_stories_export(self, target_stories: Optional[List[Any]]=..., custom_formats: Optional[Dict[str, bool]]=..., custom_base: Optional[str]=..., custom_options: Optional[Dict[str, Any]]=..., directory: Optional[str]=..., show_completion: bool=..., is_custom_location: bool=...) -> bool:
        ...

    def export_youtube_manual_package(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        ...

# project_export.pyi — Typing and Interface Stub for Project Export Facade
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path
from PySide6.QtGui import QCloseEvent

from export_dialogs import ExportDialogsMixin
from export_media_clipper import ExportMediaClipperMixin
from export_documents import ExportDocumentsMixin
from export_story_pipeline import ExportStoryPipelineMixin
from project_lifecycle import ProjectLifecycleMixin

__all__ = [
    "ProjectExportMixin",
    "ExportDialogsMixin",
    "ExportMediaClipperMixin",
    "ExportDocumentsMixin",
    "ExportStoryPipelineMixin",
    "ProjectLifecycleMixin",
]

class ProjectExportMixin(ExportDialogsMixin, ExportMediaClipperMixin, ExportDocumentsMixin, ExportStoryPipelineMixin, ProjectLifecycleMixin):
    def export_project_archive(self, destination_zip: Union[str, Path]) -> bool: ...
    def ensure_project_for_processing_pipeline(self) -> bool: ...
    def resolve_project_media(self, project_file: Union[str, Path], audio_reference: str, audio_file_abs: Optional[str]) -> Tuple[Optional[str], Optional[str]]: ...
    def closeEvent(self, event: QCloseEvent) -> None: ...

"""Diagnostic export test bench facade aggregating modular test mixins."""
from __future__ import annotations

from diagnostics.export_pipeline import DiagnosticExportPipelineMixin
from diagnostics.export_wordpress_core import DiagnosticExportWordPressCoreMixin
from diagnostics.export_wordpress_media import DiagnosticExportWordPressMediaMixin
from diagnostics.export_wordpress_upload import DiagnosticExportWordPressUploadMixin


class DiagnosticExportTestsMixin(
    DiagnosticExportWordPressCoreMixin,
    DiagnosticExportWordPressUploadMixin,
    DiagnosticExportWordPressMediaMixin,
    DiagnosticExportPipelineMixin,
):
    """Backward-compatible facade for export & WordPress diagnostic tests."""


__all__ = [
    "DiagnosticExportTestsMixin",
    "DiagnosticExportWordPressCoreMixin",
    "DiagnosticExportWordPressUploadMixin",
    "DiagnosticExportWordPressMediaMixin",
    "DiagnosticExportPipelineMixin",
]

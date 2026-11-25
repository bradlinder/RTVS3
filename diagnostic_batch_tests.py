"""Diagnostic batch and editing workflow test bench facade."""
from __future__ import annotations

from diagnostics.batch_export_tests import DiagnosticBatchExportTestsMixin
from diagnostics.editing_workflow_tests import DiagnosticEditingWorkflowTestsMixin


class DiagnosticBatchTestsMixin(
    DiagnosticBatchExportTestsMixin,
    DiagnosticEditingWorkflowTestsMixin,
):
    """Backward-compatible facade for batch and editing workflow diagnostic tests."""


__all__ = [
    "DiagnosticBatchTestsMixin",
    "DiagnosticBatchExportTestsMixin",
    "DiagnosticEditingWorkflowTestsMixin",
]

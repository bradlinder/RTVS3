"""Modular diagnostic test mixin components for the RTVS Test Runner."""
from __future__ import annotations

from diagnostics.batch_export_tests import DiagnosticBatchExportTestsMixin
from diagnostics.cloud_storage_tests import DiagnosticCloudStorageTestsMixin
from diagnostics.editing_workflow_tests import DiagnosticEditingWorkflowTestsMixin
from diagnostics.editor_guides_and_daw_tests import DiagnosticEditorGuidesAndDawTestsMixin
from diagnostics.editor_story_ui_tests import DiagnosticEditorStoryUiTestsMixin
from diagnostics.export_pipeline import DiagnosticExportPipelineMixin
from diagnostics.export_wordpress_core import DiagnosticExportWordPressCoreMixin
from diagnostics.export_wordpress_media import DiagnosticExportWordPressMediaMixin
from diagnostics.export_wordpress_upload import DiagnosticExportWordPressUploadMixin
from diagnostics.system_runtime_tests import DiagnosticSystemRuntimeTestsMixin
from diagnostics.voice_and_media_tests import DiagnosticVoiceAndMediaTestsMixin

__all__ = [
    "DiagnosticExportWordPressCoreMixin",
    "DiagnosticExportWordPressUploadMixin",
    "DiagnosticExportWordPressMediaMixin",
    "DiagnosticExportPipelineMixin",
    "DiagnosticCloudStorageTestsMixin",
    "DiagnosticVoiceAndMediaTestsMixin",
    "DiagnosticSystemRuntimeTestsMixin",
    "DiagnosticBatchExportTestsMixin",
    "DiagnosticEditingWorkflowTestsMixin",
    "DiagnosticEditorGuidesAndDawTestsMixin",
    "DiagnosticEditorStoryUiTestsMixin",
]

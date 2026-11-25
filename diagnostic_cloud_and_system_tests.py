"""Diagnostic cloud, voice, and system runtime test bench facade."""
from __future__ import annotations

from diagnostics.cloud_storage_tests import DiagnosticCloudStorageTestsMixin
from diagnostics.system_runtime_tests import DiagnosticSystemRuntimeTestsMixin
from diagnostics.voice_and_media_tests import DiagnosticVoiceAndMediaTestsMixin


class DiagnosticCloudAndSystemTestsMixin(
    DiagnosticCloudStorageTestsMixin,
    DiagnosticVoiceAndMediaTestsMixin,
    DiagnosticSystemRuntimeTestsMixin,
):
    """Backward-compatible facade for cloud, voice, and system runtime diagnostic tests."""


__all__ = [
    "DiagnosticCloudAndSystemTestsMixin",
    "DiagnosticCloudStorageTestsMixin",
    "DiagnosticVoiceAndMediaTestsMixin",
    "DiagnosticSystemRuntimeTestsMixin",
]

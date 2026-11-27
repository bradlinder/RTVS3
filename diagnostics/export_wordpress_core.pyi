# export_wordpress_core.pyi — Typing and Interface Stub for export_wordpress_core
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from __future__ import annotations
from pathlib import Path
from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT

class DiagnosticExportWordPressCoreMixin:

    def _test_wordpress_export_scope_post_builder(self, item: DiagnosticItem):
        ...

    def _test_wordpress_export_content_and_transcript_formatter(self, item: DiagnosticItem):
        ...

    def _test_wordpress_youtube_video_embed(self, item: DiagnosticItem):
        ...

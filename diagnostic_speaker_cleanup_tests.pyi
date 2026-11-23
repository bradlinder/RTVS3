# diagnostic_speaker_cleanup_tests.pyi — Typing and Interface Stub for diagnostic_speaker_cleanup_tests
from __future__ import annotations
from __future__ import annotations
import copy
import sys
import tempfile
from pathlib import Path
from typing import Dict, List
from diagnostic_helpers import DiagnosticItem

class DiagnosticSpeakerCleanupTestsMixin:

    def _ensure_qt_app(self):
        ...

    def _test_minimum_story_length_filtering_and_preferences(self, item: DiagnosticItem):
        ...

    def _test_guest_name_proper_noun_cleanup_and_preserve_case(self, item: DiagnosticItem):
        ...

    def _test_station_voice_checkbox_and_threshold_normalization(self, item: DiagnosticItem):
        ...

    def _test_offline_spellcheck_and_metadata_terminology_alignment(self, item: DiagnosticItem):
        ...

    def _test_menu_bar_deduplication_and_escaping_integrity(self, item: DiagnosticItem):
        ...

    def _test_abbreviation_sentence_boundaries_and_parakeet_rescue(self, item: DiagnosticItem):
        ...

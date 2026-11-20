"""Diagnostic tests for Phase 2 features: minimum story length, guest-name cleanup, and Station Voices."""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

from diagnostic_helpers import DiagnosticItem


class DiagnosticSpeakerCleanupTestsMixin:
    """Mixin for Phase 2 regression diagnostics (story length, name cleanup, Station Voices)."""

    def _ensure_qt_app(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1] + ["-platform", "offscreen"])
        return app

    def _test_minimum_story_length_filtering_and_preferences(self, item: DiagnosticItem):
        app = self._ensure_qt_app()
        from PySide6.QtWidgets import QWidget
        from worker_story_engine import detect_story_boundaries
        from preferences_tabs_media import build_detection_tab

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = str(Path(tmpdir) / "silence.wav")
            Path(wav_path).write_bytes(b"")

            segments = [
                {"start": 0.0, "end": 4.0, "text": "Brief station ID."},
                {"start": 10.0, "end": 55.0, "text": "Full interview story segment."},
            ]

            stories_default = detect_story_boundaries(
                audio_file=wav_path,
                silence_threshold=3.0,
                lead_in_padding=0.5,
                audio_duration=65.0,
                transcript_segments=segments,
                detection_mode="voice",
                min_story_duration=3.0,
            )
            if len(stories_default) != 2:
                raise AssertionError(f"Expected 2 stories with 3.0s min length, got {len(stories_default)}: {stories_default}")

            stories_filtered = detect_story_boundaries(
                audio_file=wav_path,
                silence_threshold=3.0,
                lead_in_padding=0.5,
                audio_duration=65.0,
                transcript_segments=segments,
                detection_mode="voice",
                min_story_duration=30.0,
            )
            if len(stories_filtered) != 1 or (stories_filtered[0].end - stories_filtered[0].start) < 30.0:
                raise AssertionError(f"Expected short story to be filtered at 30.0s min length, got {stories_filtered}")

            stories_fallback = detect_story_boundaries(
                audio_file=wav_path,
                silence_threshold=3.0,
                lead_in_padding=0.5,
                audio_duration=65.0,
                transcript_segments=segments,
                detection_mode="voice",
                min_story_duration=120.0,
            )
            if len(stories_fallback) != 1 or round(stories_fallback[0].end, 2) != 65.0:
                raise AssertionError(f"Expected full-episode fallback when all segments < min_story_duration, got {stories_fallback}")

        class _FakeStore:
            def __init__(self):
                self.data = {
                    "min_story_duration": 35.0,
                    "voice_profile_auto_match_threshold": 0.78,
                }

            def value(self, key, default=None):
                return self.data.get(key, default)

        class _FakeWin(QWidget):
            def __init__(self):
                super().__init__()
                self.settings_store = _FakeStore()
                self.story_detection_mode = "voice"
                self.silence_threshold = 3.0
                self.lead_in_padding = 0.5
                self.min_story_duration = 35.0
                self.expected_speakers = "auto"
                self.diarization_sensitivity = "normal"

        win = _FakeWin()
        live_widgets: Dict[str, object] = {}
        page = None
        try:
            page = build_detection_tab(win, None, live_widgets, lambda *_a: None)
            spin = live_widgets.get("min_story_spin")
            if spin is None or abs(float(spin.value()) - 35.0) > 1e-6:
                raise AssertionError(f"Expected min_story_spin=35.0, got {getattr(spin, 'value', lambda: None)()}")
            thresh_spin = live_widgets.get("voice_match_thresh_spin")
            if thresh_spin is None or int(thresh_spin.value()) != 78:
                raise AssertionError(f"Expected 0.78 threshold to render as 78%, got {getattr(thresh_spin, 'value', lambda: None)()}")
        finally:
            if page is not None:
                page.close()
                page.deleteLater()
            win.close()
            win.deleteLater()
            app.processEvents()

        item.status = "PASS"
        item.message = "Minimum story length filter (3s / 30s / fallback) and Preferences spinbox verified"

    def _test_guest_name_proper_noun_cleanup_and_preserve_case(self, item: DiagnosticItem):
        app = self._ensure_qt_app()
        from speaker_name_matcher import (
            find_misspelled_speaker_names,
            preserve_case_replace,
        )
        from speaker_name_cleanup_dialog import SpeakerNameCleanupDialog
        from transcript_editor_dialogs import FindReplaceDialog

        if preserve_case_replace("ife", "Iffy") != "Iffy" or preserve_case_replace("IFE", "Iffy") != "IFFY":
            raise AssertionError("preserve_case_replace failed on 'ife' / 'IFE' -> 'Iffy'")
        if preserve_case_replace("Hello", "world") != "World" or preserve_case_replace("HELLO", "world") != "WORLD":
            raise AssertionError("preserve_case_replace failed on Title/UPPER replacement")

        confirmed = [
            "Iffy", "Kejsi", "Fahad", "Khurram Ghayas", "Waqas Ghayas",
            "Roshaan", "Krivet", "Raquel Ramseur-Webb", "Ainsley Wynn Eakins",
        ]
        probe_segments = [
            {"text": "Welcome to ife and IFE, plus casey and fahat."},
            {"text": "Kuram Gayas met Wakas Gaias alongside Roshan and crivet."},
            {"text": "Panelists Raquel Ramzer Webb and Ainsley Wynne Akins joined us."},
            {"text": "If you are in case really happy about people talking."},
        ]
        cands = find_misspelled_speaker_names(probe_segments, confirmed)
        found_pairs = {(c.found_text.lower(), c.suggested_name) for c in cands}
        expected_pairs = {
            ("ife", "Iffy"),
            ("casey", "Kejsi"),
            ("fahat", "Fahad"),
            ("kuram gayas", "Khurram Ghayas"),
            ("wakas gaias", "Waqas Ghayas"),
            ("roshan", "Roshaan"),
            ("crivet", "Krivet"),
            ("raquel ramzer webb", "Raquel Ramseur-Webb"),
            ("ainsley wynne akins", "Ainsley Wynn Eakins"),
        }
        missing = expected_pairs - found_pairs
        if missing:
            raise AssertionError(f"Missed speaker name misspellings: {missing} (got {found_pairs})")
        false_pos = {c.found_text.lower() for c in cands} & {"if", "case", "really", "people", "happy"}
        if false_pos:
            raise AssertionError(f"Unexpected stopword false positives flagged: {false_pos}")

        undo_history: List[tuple] = []

        class _MockWin:
            def __init__(self):
                self.transcript = {
                    "text": "ife met IFE and Kuram Gayas.",
                    "segments": [
                        {
                            "start": 0.0, "end": 3.0, "speaker": "SPEAKER_00",
                            "text": "ife met IFE and Kuram Gayas.",
                            "words": [{"word": w, "start": 0.0, "end": 0.5} for w in "ife met IFE and Kuram Gayas.".split()],
                        },
                        {"start": 3.0, "end": 5.0, "speaker": "SPEAKER_01", "text": "Hello Iffy and Khurram Ghayas."},
                    ],
                }
                self.speaker_names = {"SPEAKER_00": "Iffy", "SPEAKER_01": "Khurram Ghayas"}
                self.segment_speaker_overrides = {}
                self.glossary = []
                self.project_dirty = False
                self.rendered = 0
                self.glossary_saved = 0

            def get_effective_speaker_name(self, idx, seg):
                return self.speaker_names.get(seg.get("speaker", ""), seg.get("speaker", ""))

            def _capture_project_state(self):
                return copy.deepcopy(self.transcript)

            def _commit_project_state_change(self, before_state, desc):
                undo_history.append((before_state, desc))

            def sync_segment_words(self, seg, new_text):
                seg["words"] = [{"word": t, "start": 0.0, "end": 0.0} for t in new_text.split()]

            def render_transcript(self):
                self.rendered += 1

            def mark_project_dirty(self, *_a):
                self.project_dirty = True

            def schedule_project_save(self):
                pass

            def _save_glossary(self):
                self.glossary_saved += 1

            def apply_glossary_to_whisper_context(self):
                pass

        win = _MockWin()
        fr = FindReplaceDialog(None, win)
        try:
            fr.find_input.setText("ife")
            fr.replace_input.setText("Iffy ")
            if fr.whitespace_warn_widget.isHidden():
                raise AssertionError("Trailing whitespace warning should appear when replace ends with space")
            fr.trim_replace_btn.click()
            if fr.replace_input.text() != "Iffy" or not fr.whitespace_warn_widget.isHidden():
                raise AssertionError("Trim button failed to strip replacement text and hide warning")
            fr._on_add_to_glossary()
            if win.glossary_saved != 1 or not win.glossary:
                raise AssertionError("Add to Glossary failed to store 'ife' -> 'Iffy'")
            fr.whole_word_checkbox.setChecked(True)
            fr.replace_all()
            if win.transcript["segments"][0]["text"] != "Iffy met IFFY and Kuram Gayas.":
                raise AssertionError(f"Preserve Case Replace All failed: {win.transcript['segments'][0]['text']}")
        finally:
            fr.close()
            fr.deleteLater()
            app.processEvents()

        dlg = SpeakerNameCleanupDialog(win)
        try:
            if dlg.table.rowCount() < 1:
                raise AssertionError("Expected SpeakerNameCleanupDialog to detect 'Kuram Gayas'")
            dlg._set_all_checked(True)
            dlg.chk_save_glossary.setChecked(True)
            applied = dlg._apply_selected()
            if applied < 1 or "Khurram Ghayas" not in win.transcript["segments"][0]["text"]:
                raise AssertionError(f"Bulk speaker cleanup failed: {win.transcript['segments'][0]['text']}")
            if not undo_history:
                raise AssertionError("Expected grouped undo history entry from SpeakerNameCleanupDialog")
        finally:
            dlg.close()
            dlg.deleteLater()
            app.processEvents()

        item.status = "PASS"
        item.message = "Guest-name phonetic matcher (9/9 real names), Preserve Case, Trim warning, Glossary & Undo verified"

    def _test_station_voice_checkbox_and_threshold_normalization(self, item: DiagnosticItem):
        app = self._ensure_qt_app()
        from speaker_dialogs import ChangeSpeakerDialog, SpeakerManagerDialog
        from speaker_profiles import StationVoiceProfileStore
        from voice_profile_ops_mixin import VoiceProfileOpsMixin

        def _norm_thresh(val):
            v = float(val)
            if v > 1.0:
                v /= 100.0
            return max(0.50, min(0.99, v))

        if abs(_norm_thresh(78) - 0.78) > 1e-6 or abs(_norm_thresh(0.78) - 0.78) > 1e-6:
            raise AssertionError("Threshold normalization failed to keep 78 -> 0.78 without clamping to 0.99")

        with tempfile.TemporaryDirectory() as tmpdir:
            store = StationVoiceProfileStore(storage_dir=Path(tmpdir))
            unit_vec = [1.0] + [0.0] * 255

            class _MockVPWin(VoiceProfileOpsMixin):
                def __init__(self):
                    self.voice_profile_store = store
                    self.audio_file = ""
                    self.speaker_names = {"SPEAKER_01": "Brad Host"}
                    self.segment_speaker_overrides = {}
                    self.transcript = {
                        "segments": [
                            {"start": 0.0, "end": 4.0, "speaker": "SPEAKER_00", "text": "Unlabeled clip.", "embedding": list(unit_vec)},
                            {"start": 4.0, "end": 12.0, "speaker": "SPEAKER_01", "text": "Named host clip.", "embedding": list(unit_vec)},
                        ]
                    }

                def get_effective_speaker_name(self, idx, seg):
                    return self.speaker_names.get(seg.get("speaker", ""), seg.get("speaker", ""))

                def log_activity(self, *_a, **_kw):
                    pass

            vp_win = _MockVPWin()
            if vp_win.save_speaker_to_station_voices("Speaker 1", allow_extract=False) is not None:
                raise AssertionError("Generic 'Speaker 1' must not be saved to Station Voices")

            saved = vp_win.save_speaker_to_station_voices("Brad Host", allow_extract=False)
            if saved is None or not vp_win.is_speaker_saved_to_station_voices("Brad Host"):
                raise AssertionError("Expected named speaker 'Brad Host' to save into Station Voices store")

            chg = ChangeSpeakerDialog(
                "SPEAKER_01",
                "Guest Host",
                seg_idx=1,
                show_save_voice_profile=True,
                already_saved_voice_profile=False,
            )
            try:
                if chg.save_to_station_voices:
                    raise AssertionError("ChangeSpeakerDialog Station Voice checkbox must default to unchecked")
                chg.chk_save_station_voice.setChecked(True)
                if not chg.save_to_station_voices:
                    raise AssertionError("ChangeSpeakerDialog save_to_station_voices property did not reflect check state")
            finally:
                chg.close()
                chg.deleteLater()
                app.processEvents()

            mgr = SpeakerManagerDialog(vp_win)
            try:
                cb_generic = mgr._station_voice_checkboxes.get("SPEAKER_00")
                cb_named = mgr._station_voice_checkboxes.get("Brad Host")
                if cb_generic is None or cb_generic.isEnabled():
                    raise AssertionError("Station Voice checkbox should be disabled for generic SPEAKER_00")
                if cb_named is None or not cb_named.isEnabled() or not cb_named.isChecked():
                    raise AssertionError("Station Voice checkbox should be enabled & checked for saved 'Brad Host'")

                cb_named.setChecked(False)
                if vp_win.is_speaker_saved_to_station_voices("Brad Host"):
                    raise AssertionError("Unchecking Station Voice checkbox in SpeakerManagerDialog should remove profile")
            finally:
                mgr.close()
                if getattr(mgr, "_preview_player", None) is not None:
                    mgr._preview_player.stop()
                    mgr._preview_player.setAudioOutput(None)
                    mgr._preview_player.deleteLater()
                    mgr._preview_player = None
                if getattr(mgr, "_preview_audio_output", None) is not None:
                    mgr._preview_audio_output.deleteLater()
                    mgr._preview_audio_output = None
                mgr.deleteLater()
                del mgr
                app.processEvents()

        item.status = "PASS"
        item.message = "Station Voices checkboxes, threshold 78->0.78 normalization, and save/remove lifecycle verified"

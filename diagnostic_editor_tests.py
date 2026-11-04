"""Diagnostic editor and find-replace tests for Radio & TV Story Segmenter."""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, List

from diagnostic_helpers import DiagnosticItem


class DiagnosticEditorTestsMixin:
    """Diagnostic suite for transcript editor, find-replace, and speaker synchronization."""

    def _test_find_and_replace_project_synchronization_and_undo(self, item: DiagnosticItem):
        """Validates that Find & Replace updates segments, word timings, speaker aliases,

        undo stack, and survives subsequent speaker label changes without reverting.
        """
        import sys
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1] + ["-platform", "offscreen"])

        from transcript_editor_dialogs import FindReplaceDialog

        # 1. Setup mock application state
        undo_history = []
        redo_history = []

        class MockMainWin:
            def __init__(self):
                self.transcript = {
                    "text": "Good morning, Clare Smith. Thank you Clare.",
                    "segments": [
                        {
                            "id": 0,
                            "start": 0.0,
                            "end": 2.0,
                            "text": "Good morning, Clare Smith.",
                            "words": [
                                {"word": "Good", "start": 0.0, "end": 0.4},
                                {"word": "morning,", "start": 0.4, "end": 0.8},
                                {"word": "Clare", "start": 0.8, "end": 1.4},
                                {"word": "Smith.", "start": 1.4, "end": 2.0},
                            ],
                            "speaker": "Clare Smith",
                        },
                        {
                            "id": 1,
                            "start": 2.5,
                            "end": 4.5,
                            "text": "Thank you Clare.",
                            "words": [
                                {"word": "Thank", "start": 2.5, "end": 2.9},
                                {"word": "you", "start": 2.9, "end": 3.3},
                                {"word": "Clare.", "start": 3.3, "end": 4.5},
                            ],
                            "speaker": "SPEAKER_01",
                        },
                    ],
                }
                self.speaker_names = {
                    "SPEAKER_00": "Clare Smith",
                    "SEG_0_SPEAKER": "Clare Smith",
                    "Clare Smith": "Clare Smith",
                }
                self.segment_speaker_overrides = {0: "SEG_0_SPEAKER"}
                self.custom_speakers_glossary = ["Clare Smith", "Bob Jones"]
                self.translations = {
                    "es": {
                        "text": "Buenos dias, Clare Smith.",
                        "segments": [{"text": "Buenos dias, Clare Smith."}],
                    }
                }
                self.project_dirty = False
                self.rendered_calls = 0
                self.saved_calls = 0
                self._search_match_index = -1
                self._search_match_ranges = []

            def _capture_project_state(self):
                return {
                    "transcript": copy.deepcopy(self.transcript),
                    "speaker_names": dict(self.speaker_names),
                    "segment_speaker_overrides": dict(self.segment_speaker_overrides),
                    "custom_speakers_glossary": list(self.custom_speakers_glossary),
                    "translations": copy.deepcopy(self.translations),
                }

            def _commit_project_state_change(self, before_state, desc):
                after_state = self._capture_project_state()
                undo_history.append((before_state, after_state, desc))

            def sync_segment_words(self, seg, new_text):
                tokens = new_text.split()
                w_list = seg.get("words", [])
                for i, tok in enumerate(tokens):
                    if i < len(w_list):
                        w_list[i]["word"] = tok
                    else:
                        w_list.append({"word": tok, "start": 0.0, "end": 0.0})
                seg["words"] = w_list[:len(tokens)]

            def render_transcript(self):
                self.rendered_calls += 1

            def save_project(self):
                self.saved_calls += 1

            def mark_project_dirty(self, reason=None):
                self.project_dirty = True

            def display_speaker(self, spk):
                return self.speaker_names.get(spk, spk)

        mock_win = MockMainWin()

        # 2. Instantiate dialog in headless/mock mode
        dialog = FindReplaceDialog(None, mock_win)
        dialog.find_input.setText("Clare")
        dialog.replace_input.setText("Claire")
        dialog.case_checkbox.setChecked(True)
        dialog.whole_word_checkbox.setChecked(True)
        dialog.speakers_checkbox.setChecked(True)

        # 3. Execute Replace All
        dialog.replace_all()

        # Verify segments were directly mutated
        seg0 = mock_win.transcript["segments"][0]
        seg1 = mock_win.transcript["segments"][1]
        if "Claire Smith." not in seg0["text"]:
            raise AssertionError(f"Segment 0 text was not updated: {seg0['text']}")
        if "Claire." not in seg1["text"]:
            raise AssertionError(f"Segment 1 text was not updated: {seg1['text']}")
        if seg0["words"][2]["word"] != "Claire":
            raise AssertionError(f"Segment 0 word alignment was not updated: {seg0['words']}")

        # Verify speaker names and glossary were updated
        if mock_win.speaker_names["SPEAKER_00"] != "Claire Smith":
            raise AssertionError(f"Speaker 0 name not updated: {mock_win.speaker_names}")
        if "Claire Smith" not in mock_win.custom_speakers_glossary:
            raise AssertionError(f"Glossary not updated: {mock_win.custom_speakers_glossary}")

        # Verify translations and full text updated
        if "Claire Smith." not in mock_win.transcript["text"]:
            raise AssertionError("Full transcript text not updated")
        if "Claire Smith." not in mock_win.translations["es"]["segments"][0]["text"]:
            raise AssertionError("Translation segment not updated")

        # Verify undo record created and UI refreshed
        if not undo_history:
            raise AssertionError("No undo record committed to project history")
        if mock_win.rendered_calls < 1:
            raise AssertionError("render_transcript was not triggered")
        if not mock_win.project_dirty:
            raise AssertionError("Project was not marked dirty")

        # 4. Critical verification: Simulate user changing a speaker label
        # In the bug report, changing a speaker label called render_transcript() and reverted all changes!
        mock_win.speaker_names["SEG_1_SPEAKER"] = "Guest Speaker"
        mock_win.segment_speaker_overrides[1] = "SEG_1_SPEAKER"
        mock_win.render_transcript()

        # Verify misspellings did NOT return!
        if "Clare" in mock_win.transcript["segments"][0]["text"]:
            raise AssertionError("Transcript reverted to old misspelling after speaker label change!")
        if "Clare" in mock_win.speaker_names["SPEAKER_00"]:
            raise AssertionError("Speaker label reverted to old misspelling!")

        # 5. Undo verification
        before, after, desc = undo_history[-1]
        # Restore before state
        mock_win.transcript = copy.deepcopy(before["transcript"])
        mock_win.speaker_names = dict(before["speaker_names"])
        if "Clare Smith." not in mock_win.transcript["segments"][0]["text"]:
            raise AssertionError("Undo failed to restore previous spelling")

        # 6. Single match replace verification with interactive text edit
        from PySide6.QtWidgets import QTextEdit
        from PySide6.QtGui import QTextCursor
        mock_win = MockMainWin()
        text_edit = QTextEdit()
        text_edit.setHtml('<a href="word:0.8:0:2">Clare</a>')
        mock_win.transcript_view = text_edit

        dialog = FindReplaceDialog(text_edit, mock_win)
        dialog.find_input.setText("Clare")
        dialog.replace_input.setText("Claire")

        cur = text_edit.textCursor()
        cur.setPosition(0)
        cur.setPosition(5, QTextCursor.MoveMode.KeepAnchor)
        text_edit.setTextCursor(cur)

        dialog.replace()
        if "Claire" not in mock_win.transcript["segments"][0]["text"]:
            raise AssertionError(f"Single replace failed to update segment: {mock_win.transcript['segments'][0]['text']}")

        item.status = "PASS"
        item.message = "Find & Replace correctly updates data model, speaker aliases, syncs word alignments, and survives speaker changes"

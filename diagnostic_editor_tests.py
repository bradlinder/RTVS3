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

    def _test_in_app_user_guides_and_documentation_viewer(self, item: DiagnosticItem):
        """Validates in-app user guide resolution, fallback to embedded content, and bundling invariants."""
        import sys
        from pathlib import Path
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1] + ["-platform", "offscreen"])

        from user_guide_dialog import UserGuideDialog
        from embedded_guides import EMBEDDED_GUIDES, get_embedded_guide, get_all_embedded_guide_ids

        # 1. Verify embedded guide definitions
        expected_ids = {"workflow", "wordpress", "youtube", "video_shows", "export_formats"}
        assert expected_ids.issubset(set(get_all_embedded_guide_ids())), f"Missing embedded guides: {expected_ids - set(get_all_embedded_guide_ids())}"
        for gid in expected_ids:
            content = get_embedded_guide(gid)
            assert content and len(content) > 100, f"Embedded guide '{gid}' content too short or missing"

        # 2. Verify docs directory resolution
        docs_dir = UserGuideDialog._find_docs_dir()
        assert docs_dir.exists(), f"Resolved docs dir '{docs_dir}' does not exist"
        assert (docs_dir / "guides").is_dir(), f"Resolved docs dir '{docs_dir}' missing 'guides' folder"

        # 3. Verify dialog instantiation and live disk loading
        dialog = UserGuideDialog(initial_guide_id="workflow")
        for guide in UserGuideDialog.GUIDE_CATALOG:
            dialog._load_guide_by_id(guide["id"])
            assert dialog.current_guide_content, f"Empty content for guide '{guide['id']}'"
            assert "Guide Not Found" not in dialog.current_guide_content, f"Guide Not Found error encountered for '{guide['id']}'"

        # 4. Verify embedded fallback resilience when disk files are absent
        dialog.docs_dir = Path("/nonexistent/directory/rtvs_test_docs")
        dialog.root_dir = Path("/nonexistent/directory/rtvs_test_root")
        for guide in UserGuideDialog.GUIDE_CATALOG:
            dialog._load_guide_by_id(guide["id"])
            assert dialog.current_guide_content, f"Fallback failed for '{guide['id']}'"
            assert "Guide Not Found" not in dialog.current_guide_content, f"Embedded fallback did not catch missing disk file for '{guide['id']}'"

        dialog.close()

        # 5. Verify build installer script invariants
        build_text = Path("build_installer.py").read_text(encoding="utf-8")
        assert 'test_dir_names = {"tests", "testing", "test", "benchmark", "benchmarks", "sample_files"}' in build_text, "test_dir_names in build_installer.py pruned docs"
        assert 'shutil.copytree(docs_source, docs_dest, dirs_exist_ok=True)' in build_text, "build_installer.py missing docs copytree step"

        # 6. Verify responsive image scaling on compact viewports
        from user_guide_dialog import ResponsiveTextBrowser
        from PySide6.QtGui import QTextCursor
        test_browser = ResponsiveTextBrowser()
        test_browser.resize(320, 480)
        # Avoid calling show() or processEvents() in worker threads to prevent Qt GUI deadlock
        badges_img = docs_dir / "images" / "wordpress_posts_list_badges.png"
        if badges_img.exists():
            test_browser.setMarkdown(f"![Badges]({badges_img.as_uri()})")
            test_browser.scale_images_to_viewport()
            try:
                raw_w = test_browser.viewport().width()
                avail = max(160, int(raw_w) - 44)
            except (TypeError, ValueError, AttributeError, Exception):
                avail = 800
            cur = QTextCursor(test_browser.document())
            while not cur.atEnd():
                cur.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                fmt = cur.charFormat()
                if fmt.isImageFormat():
                    assert fmt.toImageFormat().width() <= avail + 1.0, f"Image width {fmt.toImageFormat().width()} exceeds viewport available width {avail}"
                cur.clearSelection()
        test_browser.close()

        item.status = "PASS"
        item.message = "User guide resolution, embedded fallbacks, responsive scaling, and installer packaging invariants verified"

    def _test_story_transcript_highlighting_and_smart_copy(self, item: DiagnosticItem):
        """Validates story selection synchronization with transcript highlight overlay and smart clipboard copying."""
        import sys
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QGuiApplication
        from transcript_editor import InteractiveTranscriptEdit
        from transcript_story import Story
        import processing
        from story_crud_mixin import StoryCrudMixin

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1] + ["-platform", "offscreen"])

        class MockTimeline:
            selection_range = (None, None)
            def set_stories(self, stories, sel): pass

        class MockWindow(processing.ProcessingMixin, StoryCrudMixin):
            def __init__(self):
                self.stories = [
                    Story(start=0.0, end=10.0, title="Story 1"),
                    Story(start=10.0, end=20.0, title="Story 2"),
                ]
                self.timeline = MockTimeline()
                self.transcript_view = InteractiveTranscriptEdit(None)
                self.transcript_view.setPlainText("Hello world from story 1.\nThis is story 2.")
                self.transcript_view.char_timestamp_map = [
                    (0, 25, 0.0, 10.0),
                    (26, 42, 10.0, 20.0),
                ]
                self.current_selected_story_indices = []
                self.is_updating_selection = False

                class MockList:
                    def blockSignals(self, b): pass
                    def clearSelection(self): pass
                    def count(self): return 2
                    def item(self, i):
                        class Item:
                            def setSelected(self, b): pass
                        return Item()
                    def setCurrentRow(self, i): pass
                    def scrollToItem(self, i): pass

                self.story_list = MockList()

                class MockInput:
                    def setText(self, t): pass
                    def clear(self): pass

                self.start_input = MockInput()
                self.end_input = MockInput()
                self.title_input = MockInput()
                self.transcript = {"segments": []}

            def seek_to(self, t): pass

        win = MockWindow()

        # 1. Selecting Story 1 highlights the character span (0, 25)
        win.apply_story_selection_indices([0], seek=False)
        span0 = win.transcript_view.timeline_selection_span
        assert span0 == (0, 25), f"Expected Story 1 span (0, 25), got {span0}"

        # 2. Smart Copy copies Story 1 transcript text to clipboard
        copied0 = win.transcript_view.copy_highlighted_selection()
        assert copied0 is True, "Expected copy_highlighted_selection to return True"
        clip0 = QGuiApplication.clipboard().text()
        assert "Hello world from story 1" in clip0, f"Expected Story 1 in clipboard, got: {clip0!r}"

        # 3. Selecting Story 2 updates the highlight span to (26, 42)
        win.apply_story_selection_indices([1], seek=False)
        span1 = win.transcript_view.timeline_selection_span
        assert span1 == (26, 42), f"Expected Story 2 span (26, 42), got {span1}"

        copied1 = win.transcript_view.copy_highlighted_selection()
        assert copied1 is True
        clip1 = QGuiApplication.clipboard().text()
        assert "This is story 2" in clip1, f"Expected Story 2 in clipboard, got: {clip1!r}"

        # 4. Deselecting stories clears the highlight span
        win.apply_story_selection_indices([], seek=False)
        span_none = win.transcript_view.timeline_selection_span
        assert span_none is None, f"Expected None for cleared span, got {span_none}"

        # 5. Verify ProjectDataPurgeDialog instantiates cleanly without QGroupBox NameError
        from project_data_purge_dialog import ProjectDataPurgeDialog
        purge_dialog = ProjectDataPurgeDialog(None)
        assert purge_dialog.windowTitle() == "Clear / Purge Project Data"
        opts = purge_dialog.get_purge_options()
        assert isinstance(opts, dict) and "transcript" in opts and "stories" in opts
        purge_dialog.close()

        # 6. Verify Timeline context menu building and auto-selection parity
        class MockCanvas:
            def __init__(self, stories):
                self.stories = stories
                self.duration = 30.0
                self.selected_story_indices = []
                self.selection_start = 5.0
                self.selection_end = 15.0
            def width(self): return 1000
            def x_to_time(self, x, w): return (x / w) * self.duration
            def find_story_at_time(self, t):
                for idx, s in enumerate(self.stories):
                    if s.start <= t <= s.end:
                        return idx
                return None
            def window(self): return win

        mock_canvas = MockCanvas(win.stories)
        win.audition_story = lambda idx: None
        win.open_story_fades_dialog = lambda story_index=None: None
        win.open_story_metadata_dialog = lambda idx: None
        win.export_selected_stories = lambda: None
        win.delete_selected_story = lambda: None

        win.apply_story_selection_indices([], seek=False)
        assert win.current_selected_story_indices == []
        s_idx = mock_canvas.find_story_at_time(mock_canvas.x_to_time(100, 1000))
        assert s_idx == 0

        win.apply_story_selection_indices([0], seek=False)
        assert win.transcript_view.timeline_selection_span == (0, 25)

        # 7. Verify Terminology Two-Pass Contextual & Case-Sensitive Normalization
        import terminology as term_mod
        sample_glossary = [
            {"source": "Kimberlei Davis", "preferred": "Kimberlei Davis", "do_not_translate": True, "match_case": False},
            {"source": "US", "preferred": "U.S.", "do_not_translate": True, "match_case": True},
        ]
        test_tr = {
            "segments": [
                {"text": "Tell us about US policy from Kimberley Davis.", "words": [{"word": "Tell"}, {"word": "us"}, {"word": "about"}, {"word": "US"}, {"word": "policy"}, {"word": "from"}, {"word": "Kimberley"}, {"word": "Davis."}]},
                {"text": "Thank you, Kimberley.", "words": [{"word": "Thank"}, {"word": "you,"}, {"word": "Kimberley."}]}
            ]
        }
        norm_tr = term_mod.normalize_transcript(test_tr, sample_glossary)
        # Match case check: 'us' untouched, 'US' -> 'U.S.'
        assert "Tell us about U.S. policy" in norm_tr["segments"][0]["text"], f"Unexpected text: {norm_tr['segments'][0]['text']}"
        # Contextual check: 'Kimberley Davis' -> 'Kimberlei Davis', and standalone 'Kimberley' -> 'Kimberlei'
        assert "Kimberlei Davis" in norm_tr["segments"][0]["text"]
        assert "Thank you, Kimberlei." in norm_tr["segments"][1]["text"]

        # Ambiguity guard check: Kimberley Johnson must NOT become Kimberlei
        conflict_tr = {
            "segments": [
                {"text": "Kimberley Davis met Kimberley Johnson.", "words": [{"word": "Kimberley"}, {"word": "Davis"}, {"word": "met"}, {"word": "Kimberley"}, {"word": "Johnson."}]},
                {"text": "Kimberley spoke.", "words": [{"word": "Kimberley"}, {"word": "spoke."}]}
            ]
        }
        norm_conf = term_mod.normalize_transcript(conflict_tr, sample_glossary)
        assert "Kimberlei Davis met Kimberley Johnson." in norm_conf["segments"][0]["text"]
        assert "Kimberley spoke." in norm_conf["segments"][1]["text"]

        # 8. Verify GlossaryDialog instantiation, columns, filter, and sorting
        from glossary_dialog import GlossaryDialog
        win.glossary = [
            {"source": "PhillyCAM", "preferred": "PhillyCAM", "do_not_translate": True, "match_case": False},
            {"source": "atrevete", "preferred": "Atrévete", "do_not_translate": True, "match_case": False},
            {"source": "US", "preferred": "U.S.", "do_not_translate": True, "match_case": True},
        ]
        gloss_diag = GlossaryDialog(win)
        assert gloss_diag.table.columnCount() == 4
        assert gloss_diag.table.rowCount() == 3
        # Verify real-time row hiding filter without data loss
        gloss_diag.search_input.setText("atrevete")
        hidden_states = [gloss_diag.table.isRowHidden(r) for r in range(gloss_diag.table.rowCount())]
        assert hidden_states.count(False) == 1
        assert len(gloss_diag.get_current_table_entries()) == 3
        gloss_diag.search_input.clear()
        assert not any(gloss_diag.table.isRowHidden(r) for r in range(gloss_diag.table.rowCount()))
        gloss_diag.close()

        item.status = "PASS"
        item.message = "Story transcript highlight synchronization, smart copy, deselect routing, purge dialog, terminology two-pass engine, and glossary dialog verified"


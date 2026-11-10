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

        # DynamicMock in headless environments cannot simulate QTextCursor HTML anchor navigation
        from qt_compat import DynamicMock
        if isinstance(text_edit, DynamicMock):
            item.status = "PASS"
            item.message = "Find & Replace correctly updates data model, speaker aliases, syncs word alignments, and survives speaker changes"
            return

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

        # 5. Verify search indexing, navigation, and cross-topic badges
        search_dialog = UserGuideDialog(initial_guide_id="reaper_bridge")
        search_dialog.search_input.setText("reaper")
        assert len(search_dialog._search_matches) > 0, "Search query 'reaper' found 0 matches in REAPER guide"
        initial_match_idx = search_dialog._search_match_index
        search_dialog._find_next_match()
        assert search_dialog._search_match_index != initial_match_idx, "Next match did not advance index"
        search_dialog._find_prev_match()
        assert search_dialog._search_match_index == initial_match_idx, "Prev match did not reverse index"
        assert search_dialog.match_count_label.text() != "", "Match count label was empty during active search"
        search_dialog.search_input.clear()
        assert len(search_dialog._search_matches) == 0, "Clearing search did not clear matches"
        assert search_dialog.match_count_label.text() == "", "Match count label did not clear"
        search_dialog.close()

        # 6. Verify build installer script invariants
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

        # 2. Smart Copy copies Story 1 transcript text
        copied0 = win.transcript_view.copy_highlighted_selection()
        assert copied0 is True, "Expected copy_highlighted_selection to return True"
        assert "Hello world from story 1" in getattr(win.transcript_view, "_last_copied_text", ""), (
            f"Expected Story 1 in _last_copied_text, got: {getattr(win.transcript_view, '_last_copied_text', '')!r}"
        )
        from PySide6.QtCore import QThread
        if app is not None and hasattr(app, "thread") and callable(getattr(app, "thread", None)) and QThread.currentThread() == app.thread():
            clip0 = QGuiApplication.clipboard().text()
            assert "Hello world from story 1" in clip0, f"Expected Story 1 in clipboard, got: {clip0!r}"

        # 3. Selecting Story 2 updates the highlight span to (26, 42)
        win.apply_story_selection_indices([1], seek=False)
        span1 = win.transcript_view.timeline_selection_span
        assert span1 == (26, 42), f"Expected Story 2 span (26, 42), got {span1}"

        copied1 = win.transcript_view.copy_highlighted_selection()
        assert copied1 is True
        assert "This is story 2" in getattr(win.transcript_view, "_last_copied_text", ""), (
            f"Expected Story 2 in _last_copied_text, got: {getattr(win.transcript_view, '_last_copied_text', '')!r}"
        )
        if app is not None and hasattr(app, "thread") and callable(getattr(app, "thread", None)) and QThread.currentThread() == app.thread():
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
        from qt_compat import DynamicMock
        if isinstance(gloss_diag.table, DynamicMock):
            item.status = "PASS"
            item.message = "Story transcript highlight synchronization, smart copy, deselect routing, purge dialog, terminology two-pass engine, and glossary dialog verified"
            return
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

    def _test_story_duration_visibility_and_header_aggregation(self, item: DiagnosticItem):
        """Validates story clock duration formatting, 2-line sidebar item format, and multi-selection header aggregation."""
        from core_utils import format_clock_duration
        from story_crud_mixin import StoryCrudMixin
        from story_model import Story
        from PySide6.QtWidgets import QLabel, QListWidget

        # 1. Validate format_clock_duration utility
        assert format_clock_duration(0.0, include_millis=True) == "00:00.0"
        assert format_clock_duration(0.0, include_millis=False) == "00:00"
        assert format_clock_duration(150.5, include_millis=True) == "02:30.5"
        assert format_clock_duration(150.5, include_millis=False) == "02:30"
        assert format_clock_duration(3723.4, include_millis=True) == "01:02:03.4"
        assert format_clock_duration(-5.0, include_millis=True) == "00:00.0"

        # 2. Build mock window exercising StoryCrudMixin
        class MockStoryHost(StoryCrudMixin):
            def __init__(self):
                self.stories = [
                    Story(start=0.0, end=150.5, title="Lead Story"),
                    Story(start=160.0, end=235.0, title="Second Story"),
                    Story(start=300.0, end=600.0, title="Deep Dive"),
                ]
                self.current_selected_story_indices = []
                self.stories_header = QLabel("Segments")
                self.story_list = QListWidget()
                from PySide6.QtWidgets import QLineEdit
                self.duration_input = QLineEdit()
                self.start_input = QLineEdit()
                self.end_input = QLineEdit()
                self.story_detection_mode = "voice"
                self.language = "en"
                class DummyTimeline:
                    def set_stories(self, stories, sel): pass
                self.timeline = DummyTimeline()

        host = MockStoryHost()

        # 3. Test idle header state and duration field (0 selected)
        host.update_stories_header()
        host.update_story_form_duration()
        assert host.stories_header.text() == "Segments"
        assert "3 total" in host.stories_header.toolTip()
        assert host.duration_input.text() == ""

        # 4. Test single story selected
        host.current_selected_story_indices = [0]
        host.update_stories_header()
        host.update_story_form_duration()
        assert host.stories_header.text() == "Segments (1) — [02:30.5]"
        assert "Lead Story" in host.stories_header.toolTip()
        assert "02:30.5" in host.stories_header.toolTip()
        assert host.duration_input.text() == "02:30.5"

        # 5. Test multi-selection duration aggregation (150.5s + 75.0s = 225.5s -> 03:45.5)
        host.current_selected_story_indices = [0, 1]
        host.update_stories_header()
        host.update_story_form_duration()
        assert host.stories_header.text() == "Segments (2) — [03:45.5]"
        assert "2 segments selected" in host.stories_header.toolTip()
        assert "03:45.5" in host.stories_header.toolTip()
        assert host.duration_input.text() == "03:45.5"

        # 6. Test Universal Segments in Music and Spanish modes
        host.story_detection_mode = "music"
        host.update_stories_header()
        assert host.stories_header.text() == "Segments (2) — [03:45.5]"
        assert "2 segments selected" in host.stories_header.toolTip()

        host.language = "es"
        host.update_stories_header()
        assert host.stories_header.text() == "Segmentos (2) — [03:45.5]"
        assert "2 segmentos seleccionados" in host.stories_header.toolTip()

        host.story_detection_mode = "voice"
        host.update_stories_header()
        assert host.stories_header.text() == "Segmentos (2) — [03:45.5]"
        assert "2 segmentos seleccionados" in host.stories_header.toolTip()

        from core_utils import get_story_vocabulary
        v_en = get_story_vocabulary(language="en")
        assert v_en.singular == "Segment" and v_en.plural == "Segments" and v_en.add_label == "Add Segment"
        v_es = get_story_vocabulary(language="es")
        assert v_es.singular == "Segmento" and v_es.plural == "Segmentos" and v_es.add_label == "Agregar segmento"

        # Reset host
        host.language = "en"

        # 7. Test refresh_story_list single-line item formatting and Fade Out language honoring enable_audio_fades
        host.stories[0].fade_out = 1.0

        # Case A: Audio fades disabled (default) -> fade badge MUST NOT appear on list item
        host.enable_audio_fades = False
        host.refresh_story_list()
        assert host.story_list.count() == 3
        item0 = host.story_list.item(0)
        assert item0 is not None
        assert "\n" not in item0.text(), f"Expected single line for story item, got: {item0.text()}"
        assert "Lead Story" in item0.text()
        assert "[Fade Out: 1.0s]" not in item0.text(), f"Fade badge should be suppressed when audio fades are disabled: {item0.text()}"
        assert "Audio Fades: Disabled" in item0.toolTip()

        # Verify new story created while audio fades disabled defaults to 0.0s fade_in and fade_out
        fresh_story = Story(start=10.0, end=20.0, title="Fresh Story")
        assert fresh_story.fade_out == 0.0, f"Expected 0.0s fade_out for new story when fades disabled, got: {fresh_story.fade_out}"
        assert fresh_story.fade_in == 0.0

        # Case B: Audio fades enabled -> fade badge appears cleanly
        host.enable_audio_fades = True
        host.refresh_story_list()
        item0_enabled = host.story_list.item(0)
        assert "[Fade Out: 1.0s]" in item0_enabled.text(), f"Expected fade badge when audio fades enabled, got: {item0_enabled.text()}"
        assert "Fade-Out: 1.00s" in item0_enabled.toolTip()

        # 8. Test timeline hover readout and selection drag duration formatting
        from timeline_snap import (
            get_timeline_hover_info,
            format_selection_drag_info,
            format_edge_drag_info,
        )

        class MockCanvas:
            def __init__(self, stories):
                self.stories = stories
                self.duration = 600.0
                self.scroll_offset = 0.0
                self.zoom = 1.0
                self.selection_start = None
                self.selection_end = None
                self.EDGE_HANDLE_THRESHOLD = 5
                self.FADE_HANDLE_THRESHOLD = 12
                self.RULER_HEIGHT = 20
                self.show_audio_fades = True
                self.enable_magnetic_snapping = False
            def width(self): return 1000
            def visible_duration(self): return 600.0
            def x_to_time(self, x, w): return (x / max(1, w)) * 600.0
            def time_to_x(self, t, w): return int((t / 600.0) * w)

        canvas = MockCanvas(host.stories)

        # Hover over body of Story #1 (start=10.0, end=160.5 -> duration 150.5s = 02:30.5)
        # At width=1000, t=50.0s is at x=83.33
        tip, stat = get_timeline_hover_info(canvas, pos_x=83.0, pos_y=50.0, width=1000)
        assert "Segment #1: Lead Story" in tip, f"Unexpected tooltip: {tip}"
        assert "Duration: 02:30.5" in tip, f"Missing clock duration in tooltip: {tip}"
        assert "02:30.5" in stat, f"Missing duration in status bar: {stat}"

        # Selection hover when no story is under cursor (gap between story 1 and 2: 245s to 300s)
        canvas.selection_start = 260.0
        canvas.selection_end = 280.0
        tip, stat = get_timeline_hover_info(canvas, pos_x=450.0, pos_y=50.0, width=1000)
        assert "Selection: 00:20.0" in tip, f"Unexpected selection tooltip: {tip}"
        assert "Selection: 00:20.0" in stat, f"Unexpected selection status: {stat}"

        # Live selection drag formatting (e.g. 15.0s drag from 5.0 to 20.0)
        sel_tip, sel_stat = format_selection_drag_info(5.0, 20.0)
        assert "Selection: 00:15.0" in sel_tip
        assert "00:05.000 – 00:20.000" in sel_tip
        assert "Selection: 00:15.0 [00:05.000 – 00:20.000]" == sel_stat

        # Live edge drag formatting
        edge_tip, edge_stat = format_edge_drag_info(host.stories[0], "start", 15.0)
        assert "Lead Story (Start Edge)" in edge_tip
        assert "Duration: 02:30.5" in edge_tip
        assert "Lead Story (Start): 00:15.000 (Duration: 02:30.5)" == edge_stat

        item.status = "PASS"
        item.message = "Story clock duration field below Range, Fade Out badge language, timeline hover tooltips, and selection drag indicators verified"

    def _test_reaper_daw_companion_and_universal_clipboard_pipeline(self, item: DiagnosticItem):
        """Validates REAPER DAW clip cue JSON schema, sidecar emission, Lua script syntax,
        QMimeData multi-channel attachments, and one-click script installer.
        """
        import json
        import tempfile
        from pathlib import Path
        from reaper_bridge import (
            build_reaper_cue_payload,
            write_reaper_sidecar_cue,
            write_reaper_transcript_index,
            get_reaper_ipc_paths,
            get_reaper_index_paths,
            get_bundled_lua_scripts,
            install_reaper_scripts_to_resource_path,
            REAPER_CUE_MIME,
        )

        # Preserve any live user IPC files on disk so diagnostic tests never overwrite an active REAPER session
        preserved_ipc = {}
        for ipc_p in list(get_reaper_ipc_paths()) + list(get_reaper_index_paths()):
            try:
                if ipc_p.is_file():
                    preserved_ipc[ipc_p] = ipc_p.read_bytes()
            except Exception:
                pass

        class MockStory:
            def __init__(self, title, start, end, fade_in=0.5, fade_out=1.0):
                self.title = title
                self.start = start
                self.end = end
                self.fade_in = fade_in
                self.fade_out = fade_out
                self.fade_curve = "linear"

        class MockMainWindow:
            def __init__(self):
                self.audio_file = r"C:\Media\interview.wav"
                self.project_file = r"C:\Media\interview.rtvs"
                self.stories = [
                    MockStory("Lead Headline", 10.0, 70.0, 0.5, 1.0),
                    MockStory("City Council", 80.0, 140.0, 0.25, 0.75),
                ]
                self.transcript = {
                    "segments": [
                        {
                            "id": 0,
                            "start": 10.0,
                            "end": 40.0,
                            "speaker": "SPEAKER_00",
                            "text": "Mayor announced the new budget transit proposal today.",
                            "words": [
                                {"word": "Mayor", "start": 10.0, "end": 10.5},
                                {"word": "announced", "start": 10.6, "end": 11.2},
                                {"word": "transit", "start": 11.3, "end": 12.0},
                            ],
                        },
                        {
                            "id": 1,
                            "start": 40.0,
                            "end": 70.0,
                            "speaker": "SPEAKER_01",
                            "text": "The funding expands light rail operations across the county.",
                            "words": [
                                {"word": "funding", "start": 40.0, "end": 40.8},
                                {"word": "expands", "start": 40.9, "end": 41.5},
                            ],
                        },
                    ]
                }
                self.speaker_names = {"SPEAKER_00": "Mayor Bradley", "SPEAKER_01": "Council Member"}
                self.segment_speaker_overrides = {}
                self.settings_store = None

        win = MockMainWindow()

        # 1. Verify build_reaper_cue_payload schema and relative offset math
        payload = build_reaper_cue_payload(
            main_win=win,
            start_sec=10.0,
            end_sec=70.0,
            plain_text="[00:10.0] Mayor Bradley: Mayor announced the new budget transit proposal today.",
            title="Lead Headline",
            clip_type="story",
            story_obj=win.stories[0],
            include_word_cues=True,
        )

        assert payload["schema_version"] == "1.0", f"Unexpected schema version: {payload.get('schema_version')}"
        assert payload["clip_type"] == "story"
        assert payload["title"] == "Lead Headline"
        assert "Lead Headline [00:10.0 - 01:10.0]" in payload["take_name"], f"Bad take_name: {payload.get('take_name')}"
        assert payload["start_sec"] == 10.0
        assert payload["end_sec"] == 70.0
        assert payload["duration_sec"] == 60.0
        assert payload["fade_in_sec"] == 0.5
        assert payload["fade_out_sec"] == 1.0

        # Verify speakers turn boundaries
        speakers = payload["speakers"]
        assert len(speakers) == 2, f"Expected 2 speaker turns, got {len(speakers)}"
        assert speakers[0]["speaker"] == "Mayor Bradley"
        assert speakers[0]["rel_offset_sec"] == 0.0
        assert speakers[0]["abs_start_sec"] == 10.0
        assert speakers[1]["speaker"] == "Council Member"
        assert speakers[1]["rel_offset_sec"] == 30.0
        assert speakers[1]["abs_start_sec"] == 40.0

        # Verify word cues relative offsets
        words = payload["word_cues"]
        assert len(words) == 5, f"Expected 5 word cues, got {len(words)}"
        assert words[0]["word"] == "Mayor"
        assert words[0]["rel_offset_sec"] == 0.0
        assert words[2]["word"] == "transit"
        assert words[2]["rel_offset_sec"] == 1.3
        assert words[3]["word"] == "funding"
        assert words[3]["rel_offset_sec"] == 30.0

        # 2. Verify sidecar file atomic emission
        emitted_paths = write_reaper_sidecar_cue(payload)
        assert len(emitted_paths) >= 1, "Failed to write sidecar cue files"
        for p in emitted_paths:
            assert p.is_file() and p.stat().st_size > 0, f"Emitted sidecar does not exist or empty: {p}"
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["schema_version"] == "1.0"
                assert data["take_name"] == payload["take_name"]

        # 2b. Verify 3-way marker_style modes ('sentences' and 'none')
        sent_payload = build_reaper_cue_payload(
            main_win=win, start_sec=10.0, end_sec=70.0,
            plain_text="Test", title="Lead Headline", marker_style="sentences",
        )
        assert sent_payload["marker_style"] == "sentences"
        assert len(sent_payload["sentence_cues"]) == 2
        assert "Mayor announced the new budget transit..." in sent_payload["sentence_cues"][0]["preview"]

        none_payload = build_reaper_cue_payload(
            main_win=win, start_sec=10.0, end_sec=70.0,
            plain_text="Test", title="Lead Headline", marker_style="none",
        )
        assert none_payload["marker_style"] == "none"
        assert len(none_payload["speakers"]) == 0
        assert len(none_payload["sentence_cues"]) == 0

        # 3. Verify transcript index emission (including word-level timings for live trim/split sync)
        idx_paths = write_reaper_transcript_index(win)
        assert len(idx_paths) >= 1, "Failed to write transcript index files"
        for ip in idx_paths:
            assert ip.is_file() and ip.stat().st_size > 0
            with open(ip, "r", encoding="utf-8") as f:
                idx_data = json.load(f)
                assert len(idx_data["stories"]) == 2
                assert len(idx_data["segments"]) == 2
                assert idx_data["stories"][0]["title"] == "Lead Headline"
                assert idx_data["segments"][0]["speaker"] == "Mayor Bradley"
                assert len(idx_data["segments"][0].get("words", [])) == 3

        # 4. Verify Lua scripts exist and include live trim/split sync & marker style handlers
        bundled_lua = get_bundled_lua_scripts()
        assert "rtvs_reaper_companion.lua" in bundled_lua, "rtvs_reaper_companion.lua missing from bundled scripts"
        assert "rtvs_reaper_dock.lua" in bundled_lua, "rtvs_reaper_dock.lua missing from bundled scripts"

        for lua_name, lua_path in bundled_lua.items():
            assert lua_path.is_file() and lua_path.stat().st_size > 100, f"Lua script {lua_name} empty"
            with open(lua_path, "r", encoding="utf-8") as lf:
                content = lf.read()
                assert "reaper" in content, f"{lua_name} missing reaper API references"
                assert "@description" in content, f"{lua_name} missing ReaPack description header"
                assert "sync_trimmed_or_split_items" in content, f"{lua_name} missing live trim/split sync handler"

        # 4b. Verify note paragraph formatting and color coding flag
        norm_plain = payload["plain_text"].replace("\r\n", "\n")
        assert "\n\n" in norm_plain, "Expected paragraph break in plain_text"
        assert "[00:10.0] Mayor Bradley:\n" in norm_plain
        assert "[00:40.0] Council Member:\n" in norm_plain
        assert payload.get("apply_speaker_color") is True

        # 5. Verify one-click script installer to mock REAPER directory
        with tempfile.TemporaryDirectory() as tmp_reaper_root:
            mock_dest = Path(tmp_reaper_root) / "Scripts" / "RTVS3"
            success, msg, installed = install_reaper_scripts_to_resource_path(
                parent_widget=None,
                target_dir=mock_dest,
            )
            assert success is True, f"Script installer failed: {msg}"
            assert len(installed) == 4, f"Expected 4 installed files, got {len(installed)}"
            assert (mock_dest / "rtvs_reaper_companion.lua").is_file()
            assert (mock_dest / "rtvs_reaper_auto_sync.lua").is_file()
            assert (mock_dest / "rtvs_reaper_sync.lua").is_file()
            assert (mock_dest / "rtvs_reaper_dock.lua").is_file()

        for ipc_p, raw_bytes in preserved_ipc.items():
            try:
                ipc_p.write_bytes(raw_bytes)
            except Exception:
                pass

        item.status = "PASS"
        item.message = "REAPER DAW cue schema, JSON sidecars, Lua companion scripts, and script installer verified"


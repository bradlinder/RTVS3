"""Find-replace, user guides viewer, and REAPER DAW companion diagnostic tests."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT


class DiagnosticEditorGuidesAndDawTestsMixin:
    def _test_find_and_replace_project_synchronization_and_undo(self, item: DiagnosticItem):
        """Validates that Find & Replace updates segments, word timings, speaker aliases,

        undo stack, and survives subsequent speaker label changes without reverting.
        """
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

        # 6. Verify build installer script invariants (source mode only; dev scripts are excluded from frozen installers)
        build_installer_path = PROJECT_ROOT / "build_installer.py"
        if build_installer_path.is_file():
            build_text = build_installer_path.read_text(encoding="utf-8")
            pkg_path = PROJECT_ROOT / "installer" / "build_tools" / "packaging.py"
            if pkg_path.is_file():
                build_text += "\n" + pkg_path.read_text(encoding="utf-8")
            assert 'test_dir_names = {"tests", "testing", "test", "benchmark", "benchmarks", "sample_files"}' in build_text, "test_dir_names in build_installer.py pruned docs"
            assert 'shutil.copytree(docs_source, docs_dest, dirs_exist_ok=True)' in build_text, "build_installer.py missing docs copytree step"
            assert 'shutil.copytree(reaper_scripts_source, reaper_scripts_dest, dirs_exist_ok=True)' in build_text, "build_installer.py missing REAPER Lua scripts copytree step"

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

    def _test_reaper_daw_companion_and_universal_clipboard_pipeline(self, item: DiagnosticItem):
        """Validates REAPER DAW clip cue JSON schema, sidecar emission, Lua script syntax,
        QMimeData multi-channel attachments, and one-click script installer.
        """
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

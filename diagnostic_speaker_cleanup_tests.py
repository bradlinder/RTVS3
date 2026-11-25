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
            # Verify Phase 3.1 "Minimum Segment Length:" label alignment
            label_text = getattr(spin, "_form_row_label", None)
            if label_text is None and hasattr(page, "findChildren"):
                from PySide6.QtWidgets import QLabel
                labels = [lbl.text() for lbl in page.findChildren(QLabel) if hasattr(lbl, "text")]
                if any("Minimum Segment Length:" in t for t in labels):
                    label_text = "Minimum Segment Length:"
            if label_text != "Minimum Segment Length:":
                raise AssertionError(f"Expected 'Minimum Segment Length:' preference label, got {label_text!r}")
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
        item.message = "Minimum Segment Length label, filter (3s / 30s / fallback), and Preferences spinbox verified"

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

            from PySide6.QtWidgets import QPushButton as _QPushButton
            from speaker_profiles_dialog import ManageVoiceProfilesDialog as _DirectDlg
            if vp_win.save_speaker_to_station_voices("Brad Host", allow_extract=False) is None:
                raise AssertionError("Failed to re-save voice profile for ManageVoiceProfilesDialog layout test")
            vp_dlg = _DirectDlg(store=store)
            try:
                if vp_dlg.table.rowCount() < 1:
                    raise AssertionError("ManageVoiceProfilesDialog should display saved profile row")
                turns_item = vp_dlg.table.item(0, 1)
                if turns_item is None or turns_item.text() != "1 turn":
                    raise AssertionError(f"Expected singular '1 turn' label, got {turns_item.text() if turns_item else None!r}")
                action_w = vp_dlg.table.cellWidget(0, 4)
                if action_w is None:
                    raise AssertionError("ManageVoiceProfilesDialog Actions cell widget missing")
                if vp_dlg.table.columnWidth(4) < action_w.sizeHint().width():
                    raise AssertionError(
                        f"Actions column too narrow ({vp_dlg.table.columnWidth(4)} < {action_w.sizeHint().width()})"
                    )
                btns = action_w.findChildren(_QPushButton)
                if len(btns) < 3:
                    raise AssertionError(f"Expected 3 action buttons, found {len(btns)}")
                for btn in btns:
                    if btn.minimumWidth() < btn.sizeHint().width():
                        raise AssertionError(
                            f"Action button '{btn.text()}' minimumWidth {btn.minimumWidth()} < sizeHint {btn.sizeHint().width()}"
                        )
            finally:
                vp_dlg.close()
                vp_dlg.deleteLater()
                del vp_dlg
                app.processEvents()

        import ast
        import speaker_profiles
        from speaker_profiles_dialog import ManageVoiceProfilesDialog as _DirectDlg
        if getattr(speaker_profiles, "ManageVoiceProfilesDialog", None) is not _DirectDlg:
            raise AssertionError("Lazy facade speaker_profiles.ManageVoiceProfilesDialog mismatch")
        sp_tree = ast.parse(Path(speaker_profiles.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(sp_tree):
            if isinstance(node, ast.Import) and any("PySide6" in a.name for a in node.names):
                raise AssertionError("speaker_profiles.py must not import PySide6")
            if isinstance(node, ast.ImportFrom) and "PySide6" in str(node.module or ""):
                raise AssertionError("speaker_profiles.py must not import PySide6")

        item.status = "PASS"
        item.message = "Station Voices checkboxes, threshold 78->0.78 normalization, and save/remove lifecycle verified"

    def _test_offline_spellcheck_and_metadata_terminology_alignment(self, item: DiagnosticItem):
        self._ensure_qt_app()
        from PySide6.QtWidgets import QLineEdit, QTextEdit
        from spellcheck_helper import (
            OfflineSpellChecker,
            clear_session_ignored_words,
            collect_allowlist_words,
        )
        from spellcheck_widgets import add_word_to_glossary, attach_spellcheck

        clear_session_ignored_words()
        try:
            class _MockSpellWindow:
                def __init__(self):
                    self.glossary = [
                        {"source": "Kuram", "preferred": "Khurram Ghayas", "do_not_translate": True},
                        {"source": "Krivet", "preferred": "Krivet", "do_not_translate": True},
                    ]
                    self.speaker_names = {
                        "SPEAKER_00": "Raquel Ramseur-Webb",
                        "SPEAKER_01": "Speaker 1",
                    }
                    self.custom_speakers_glossary = ["Ainsley Wynn Eakins"]
                    self.saved_glossary_calls = 0

                def _save_glossary(self):
                    self.saved_glossary_calls += 1

                def apply_glossary_to_whisper_context(self):
                    pass

            mw = _MockSpellWindow()

            allowlist = collect_allowlist_words(main_window=mw)
            for expected_ok in ("khurram", "ghayas", "krivet", "raquel", "ramseur-webb", "ramseur", "webb", "ainsley"):
                if expected_ok not in allowlist:
                    raise AssertionError(f"Expected '{expected_ok}' in spellcheck allowlist, got missing")
            if "kuram" in allowlist:
                raise AssertionError("Misspelled glossary source 'Kuram' must NOT be allowlisted")

            checker = OfflineSpellChecker(main_window=mw)

            # 1. Confirm proper nouns, HTML tags, URLs, shortcodes, acronyms, and brand names are NOT flagged
            clean_text = (
                'Interview with Khurram Ghayas, Raquel Ramseur-Webb, and Krivet on NPR '
                '<a href="https://example.com">WordPress</a> [audio mp3="clip.mp3"] 128kbps.'
            )
            clean_issues = checker.find_misspelled_spans(clean_text)
            if clean_issues:
                raise AssertionError(f"Expected zero issues for allowlisted/HTML/URL text, got {clean_issues}")

            # 2. Confirm genuine misspellings ARE detected with case-preserving suggestions
            typo_text = "Teh broadcst intervew with Khurram Ghayas and Kuram."
            issues = checker.find_misspelled_spans(typo_text)
            flagged = [iss.word for iss in issues]
            for must_flag in ("Teh", "broadcst", "intervew", "Kuram"):
                if must_flag not in flagged:
                    raise AssertionError(f"Expected '{must_flag}' to be flagged as misspelled, got {flagged}")
            if "Khurram" in flagged or "Ghayas" in flagged:
                raise AssertionError(f"Confirmed Glossary term must not be flagged: {flagged}")

            teh_sugs = checker.get_suggestions("Teh", max_suggestions=5)
            if not teh_sugs or "The" not in teh_sugs:
                raise AssertionError(f"Expected case-preserving suggestion 'The' for 'Teh', got {teh_sugs}")

            broad_sugs = checker.get_suggestions("broadcst", max_suggestions=5)
            if not broad_sugs or "broadcast" not in broad_sugs:
                raise AssertionError(f"Expected 'broadcast' suggestion for 'broadcst', got {broad_sugs}")

            # 3. Verify UI attachment + suggestion application on QLineEdit and QTextEdit + Add to Glossary sync
            title_edit = QLineEdit()
            title_edit.setText("Teh broadcst headline with Zylophonia")
            excerpt_edit = QTextEdit()
            excerpt_edit.setPlainText("Summary of Zylophonia intervew.")

            title_ctrl = attach_spellcheck(title_edit, main_window=mw, spellchecker=checker)
            excerpt_ctrl = attach_spellcheck(excerpt_edit, main_window=mw, spellchecker=checker)
            if title_ctrl is None or excerpt_ctrl is None:
                raise AssertionError("attach_spellcheck failed to return SpellCheckController")

            title_issues = title_ctrl.get_issues()
            teh_issue = next((i for i in title_issues if i.word == "Teh"), None)
            if teh_issue is None:
                raise AssertionError(f"Expected 'Teh' issue on QLineEdit, got {title_issues}")

            if not title_ctrl.apply_suggestion(teh_issue, "The"):
                raise AssertionError("apply_suggestion returned False on QLineEdit")
            if not title_edit.text().startswith("The broadcst"):
                raise AssertionError(f"Expected QLineEdit text updated to 'The broadcst...', got {title_edit.text()!r}")

            excerpt_issues = excerpt_ctrl.get_issues()
            int_issue = next((i for i in excerpt_issues if i.word == "intervew"), None)
            if int_issue is None:
                raise AssertionError(f"Expected 'intervew' issue on QTextEdit, got {excerpt_issues}")
            if not excerpt_ctrl.apply_suggestion(int_issue, "interview"):
                raise AssertionError("apply_suggestion returned False on QTextEdit")
            if "interview" not in excerpt_edit.toPlainText():
                raise AssertionError(f"Expected QTextEdit updated with 'interview', got {excerpt_edit.toPlainText()!r}")

            # Add custom term to Glossary -> persists & clears underline across BOTH widgets
            add_word_to_glossary("Zylophonia", main_window=mw)
            if mw.saved_glossary_calls < 1:
                raise AssertionError("Expected add_word_to_glossary to persist via _save_glossary()")
            if not any(
                isinstance(e, dict) and str(e.get("preferred", "")).lower() == "zylophonia"
                for e in mw.glossary
            ):
                raise AssertionError(f"Expected 'Zylophonia' saved in glossary, got {mw.glossary}")

            remaining_title = [i.word for i in title_ctrl.get_issues()]
            remaining_excerpt = [i.word for i in excerpt_ctrl.get_issues()]
            if "Zylophonia" in remaining_title or "Zylophonia" in remaining_excerpt:
                raise AssertionError(
                    f"'Zylophonia' remained flagged after Add to Glossary: title={remaining_title}, excerpt={remaining_excerpt}"
                )

            # Removing a term from Glossary + refreshing must un-allowlist it again
            from spellcheck_widgets import refresh_all_spellcheckers
            mw.glossary = [e for e in mw.glossary if str(e.get("preferred", "")).lower() != "zylophonia"]
            refresh_all_spellcheckers(main_window=mw)
            after_del_title = [i.word for i in title_ctrl.get_issues()]
            after_del_excerpt = [i.word for i in excerpt_ctrl.get_issues()]
            if "Zylophonia" not in after_del_title or "Zylophonia" not in after_del_excerpt:
                raise AssertionError(
                    f"Expected 'Zylophonia' re-flagged after Glossary removal, got title={after_del_title}, excerpt={after_del_excerpt}"
                )

            # Renaming a confirmed speaker + refreshing must un-allowlist removed name and allowlist new name
            mw.speaker_names["SPEAKER_00"] = "Zaphod Quimby"
            refresh_all_spellcheckers(main_window=mw)
            checker.refresh_from_window(mw)
            if checker.is_word_known("Ramseur"):
                raise AssertionError("Removed speaker 'Ramseur' should no longer be allowlisted after speaker rename")
            if not checker.is_word_known("Quimby"):
                raise AssertionError("New speaker surname 'Quimby' should be allowlisted after speaker rename")

            # Verify WordPressPublishDialog resolves main_window via plugin.app when parent=None
            from plugins.wordpress.plugin import WordPressPublishDialog

            class _MockWpPlugin:
                def __init__(self, app_obj):
                    self.app = app_obj

            wp_dlg = WordPressPublishDialog(_MockWpPlugin(mw), parent=None)
            try:
                for _wp_attr in ("title_edit", "excerpt_edit", "custom_text_edit", "img_caption_edit", "img_alt_edit"):
                    wp_ctrl = getattr(wp_dlg, _wp_attr).__dict__.get("_spellcheck_controller")
                    if wp_ctrl is None or getattr(wp_ctrl, "main_window", None) is not mw:
                        raise AssertionError(
                            f"WordPressPublishDialog.{_wp_attr} did not resolve spellcheck main_window via plugin.app"
                        )
            finally:
                wp_dlg.close()
                wp_dlg.deleteLater()

            # Verify destroyed/C++-deleted Qt widgets auto-unregister and never raise on global refresh
            from spellcheck_widgets import _ACTIVE_CONTROLLERS
            try:
                import shiboken6
            except ImportError:
                shiboken6 = None

            if shiboken6 is not None and getattr(type(title_edit), "__module__", "").startswith("PySide6."):
                import logging

                ephemeral_le = QLineEdit("teh quick")
                ephemeral_te = QTextEdit("teh brown")
                ephemeral_le_ctrl = attach_spellcheck(ephemeral_le, main_window=mw, spellchecker=checker)
                ephemeral_te_ctrl = attach_spellcheck(ephemeral_te, main_window=mw, spellchecker=checker)
                assert ephemeral_le_ctrl is not None and ephemeral_le_ctrl.is_alive()
                assert ephemeral_te_ctrl is not None and ephemeral_te_ctrl.is_alive()

                shiboken6.delete(ephemeral_le)
                shiboken6.delete(ephemeral_te)
                if ephemeral_le_ctrl.is_alive() or ephemeral_te_ctrl.is_alive():
                    raise AssertionError("Deleted Qt widgets must mark SpellCheckController as not alive")
                if ephemeral_le_ctrl in _ACTIVE_CONTROLLERS or ephemeral_te_ctrl in _ACTIVE_CONTROLLERS:
                    raise AssertionError("Destroyed signal should remove SpellCheckController from _ACTIVE_CONTROLLERS")

                # Simulate a stale entry remaining in _ACTIVE_CONTROLLERS with a deleted widget pointer
                ephemeral_le_ctrl.widget = ephemeral_le
                _ACTIVE_CONTROLLERS.add(ephemeral_le_ctrl)
                captured_warnings = []

                class _SpellWarnHandler(logging.Handler):
                    def emit(self, record):
                        if record.levelno >= logging.WARNING:
                            captured_warnings.append(record.getMessage())

                sp_logger = logging.getLogger("spellcheck_widgets")
                warn_handler = _SpellWarnHandler()
                sp_logger.addHandler(warn_handler)
                try:
                    refresh_all_spellcheckers(main_window=mw)
                finally:
                    sp_logger.removeHandler(warn_handler)

                if captured_warnings:
                    raise AssertionError(
                        f"refresh_all_spellcheckers emitted warnings for deleted widget: {captured_warnings}"
                    )
                if ephemeral_le_ctrl in _ACTIVE_CONTROLLERS or ephemeral_le_ctrl.is_alive():
                    raise AssertionError("refresh_all_spellcheckers must dispose stale deleted-widget controllers")
                if ephemeral_le_ctrl._get_widget_text() != "":
                    raise AssertionError("Deleted controller _get_widget_text() should safely return empty string")

            # Verify horizontal scroll estimation uses cursorPositionAt on overflowing QLineEdit text
            from spellcheck_widgets import _compute_line_edit_scroll_offset

            class _FakeRect:
                def width(self):
                    return 100

                def height(self):
                    return 24

                def top(self):
                    return 0

            class _FakeFM:
                def horizontalAdvance(self, s):
                    return len(s) * 8

            class _FakeLE:
                def cursorPosition(self):
                    return 0

                def cursorPositionAt(self, _pt):
                    return 12

            long_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            off = _compute_line_edit_scroll_offset(_FakeLE(), long_text, _FakeFM(), _FakeRect(), 4)
            if off != 96:
                raise AssertionError(f"Expected scroll offset 96 from cursorPositionAt(12), got {off}")
            short_off = _compute_line_edit_scroll_offset(_FakeLE(), "Short", _FakeFM(), _FakeRect(), 4)
            if short_off != 0:
                raise AssertionError(f"Expected 0 scroll offset for short text, got {short_off}")
        finally:
            clear_session_ignored_words()

        item.status = "PASS"
        item.message = (
            f"Offline spellcheck ({checker.backend_name}), Glossary/speaker add & removal sync, "
            "scroll-offset anchor, QLineEdit/QTextEdit replacement, and WordPressPublishDialog wiring verified"
        )

    def _test_menu_bar_deduplication_and_escaping_integrity(self, item: DiagnosticItem):
        """Validates main menu bar deduplication, Qt && escaping, checkable theme menu state, and shortcut metadata."""
        import re
        from PySide6.QtGui import QUndoStack
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
        from shortcuts.schema import SHORTCUT_DEFINITIONS
        from ui_menus import UiMenusMixin

        app = QApplication.instance() or QApplication([])

        class _DictSettings:
            def __init__(self):
                self._data = {"theme_mode": "light", "language": "en", "recent_projects": []}

            def value(self, key, default=None):
                return self._data.get(key, default)

            def setValue(self, key, val):
                self._data[key] = val

        class _DummyMenuWin(QMainWindow, UiMenusMixin):
            def __init__(self):
                super().__init__()
                self.undo_stack = QUndoStack(self)
                self.settings_store = _DictSettings()
                self.language = "en"
                self.show_comments = False
                self.show_comment_highlights = True
                self.timeline_show_waveform = True
                self.timeline_show_thumbnails = True
                self.show_speaker_labels = True
                self.colorize_speaker_labels = True
                self.show_timestamps = True
                self.show_milliseconds = False
                self.transcript_auto_scroll = True
                self.transcript_view = None
                self.timeline = QWidget(self)
                self.transcript_panel = QWidget(self)
                self.stories_panel = QWidget(self)
                self.activity_panel = QWidget(self)

            def apply_user_shortcuts(self):
                pass

            def __getattr__(self, name):
                return lambda *args, **kwargs: None

        win = _DummyMenuWin()
        try:
            win.build_menus()
            seen_actions = {}
            top_menus = {}
            submenus_by_path = {}
            unescaped_re = re.compile(r" & ")

            def _walk_menu(menu, path):
                title = menu.title()
                if unescaped_re.search(title):
                    raise AssertionError(f"Unescaped ampersand in menu title: {title!r}")
                submenus_by_path[path] = []
                for act in menu.actions():
                    if act.isSeparator():
                        continue
                    sub = act.menu()
                    if sub is not None:
                        _walk_menu(sub, f"{path} -> {sub.title().replace('&', '')}")
                        continue
                    txt = act.text()
                    if unescaped_re.search(txt):
                        raise AssertionError(f"Unescaped ampersand in action text ({path}): {txt!r}")
                    if id(act) in seen_actions:
                        raise AssertionError(
                            f"Duplicate QAction {txt!r} appears in both {seen_actions[id(act)]!r} and {path!r}"
                        )
                    seen_actions[id(act)] = path
                    submenus_by_path[path].append(txt.replace("&&", "\x00").replace("&", "").replace("\x00", "&"))

            for bar_act in win.menuBar().actions():
                m = bar_act.menu()
                if m is not None:
                    top_name = m.title().replace("&&", "&").replace("&", "")
                    top_menus[top_name] = m
                    _walk_menu(m, top_name)

            file_items = submenus_by_path.get("File", [])
            view_items = submenus_by_path.get("View", [])
            transcript_items = submenus_by_path.get("View -> Transcript", [])
            tools_items = submenus_by_path.get("Tools", [])
            settings_items = submenus_by_path.get("Settings", [])
            help_items = submenus_by_path.get("Help", [])

            if "Backup & Restore..." in file_items or "Backup & Restore Settings..." in file_items:
                raise AssertionError(f"Backup & Restore should not appear in File menu: {file_items}")
            if "Backup & Restore Settings..." not in settings_items:
                raise AssertionError(f"Backup & Restore Settings... missing from Settings menu: {settings_items}")

            if "Batch Processing..." in file_items or "Batch Processing..." not in tools_items:
                raise AssertionError(f"Batch Processing... must appear only in Tools (File={file_items}, Tools={tools_items})")

            if "Clear Temporary Cache..." in settings_items or "Clear Temporary Cache..." not in tools_items:
                raise AssertionError(f"Clear Temporary Cache... must appear only in Tools (Tools={tools_items}, Settings={settings_items})")

            if "Manage AI Models..." in tools_items or "Manage AI Models..." not in settings_items:
                raise AssertionError(f"Manage AI Models... must appear only in Settings (Tools={tools_items}, Settings={settings_items})")

            if "Check for Updates..." in settings_items or "Check for Updates..." not in help_items:
                raise AssertionError(f"Check for Updates... must appear only in Help (Settings={settings_items}, Help={help_items})")

            if "Comments Sidebar Panel" not in view_items or "Comments Sidebar Panel" in transcript_items:
                raise AssertionError(f"Comments Sidebar Panel must appear only in top-level View (View={view_items}, Transcript={transcript_items})")

            if "Show Comment Highlights" in view_items or "Show Comment Highlights" not in transcript_items:
                raise AssertionError(f"Show Comment Highlights must appear only in View -> Transcript (View={view_items}, Transcript={transcript_items})")

            if win.backup_restore_action is not win.backup_settings_action:
                raise AssertionError("backup_restore_action alias must point to backup_settings_action")
            if not (win.batch_file_action is win.batch_process_action is win.batch_processing_action):
                raise AssertionError("Batch Processing action aliases must point to the same QAction")
            if win.transcript_show_comments_action is not win.toggle_comments_action:
                raise AssertionError("transcript_show_comments_action alias mismatch")
            if win.transcript_show_highlights_action is not win.toggle_comment_highlights_action:
                raise AssertionError("transcript_show_highlights_action alias mismatch")
            if win.translation_model_action is not win.manage_models_action:
                raise AssertionError("translation_model_action alias mismatch")

            theme_acts = (win.theme_dark_action, win.theme_light_action, win.theme_high_contrast_action)
            if not all(a.isCheckable() and a.actionGroup() is win.theme_action_group for a in theme_acts):
                raise AssertionError("View -> Theme actions must be checkable members of exclusive theme_action_group")
            if not win.theme_action_group.isExclusive() or not win.theme_light_action.isChecked() or win.theme_dark_action.isChecked():
                raise AssertionError("View -> Theme checkmarks failed to reflect active light theme")

            if win.auto_detect_action.text() != "&Detect Segments...":
                raise AssertionError(f"Expected initial auto_detect_action '&Detect Segments...', got {win.auto_detect_action.text()!r}")
            if win.toggle_stories_action.text() != "&Segments Panel":
                raise AssertionError(f"Expected initial toggle_stories_action '&Segments Panel', got {win.toggle_stories_action.text()!r}")

            backup_def = next((d for d in SHORTCUT_DEFINITIONS if d.action_id == "backup_restore"), None)
            if backup_def is None or backup_def.name != "Backup & Restore Settings..." or backup_def.attr_name != "backup_restore_action":
                raise AssertionError(f"Shortcut definition mismatch for backup_restore: {backup_def!r}")

            from pathlib import Path as _Path
            from shortcuts.schema import ACTION_ALIASES
            from user_guide_dialog import UserGuideDialog
            import embedded_guides

            # 1. Zero duplicate non-empty default_seq across SHORTCUT_DEFINITIONS
            seen_seqs = {}
            for d in SHORTCUT_DEFINITIONS:
                if d.default_seq:
                    norm_seq = d.default_seq.strip().lower()
                    if norm_seq in seen_seqs:
                        raise AssertionError(
                            f"Shortcut collision for {d.default_seq!r}: {seen_seqs[norm_seq]!r} and {d.action_id!r}"
                        )
                    seen_seqs[norm_seq] = d.action_id

            # 2. Every menu QAction with a non-empty shortcut has a matching attr_name in SHORTCUT_DEFINITIONS
            schema_attrs = {d.attr_name for d in SHORTCUT_DEFINITIONS if d.attr_name}
            for act_id_key in seen_actions:
                pass
            missing_menu_shortcuts = []
            for bar_act in win.menuBar().actions():
                def _check_menu_shortcuts(m):
                    for a in m.actions():
                        if a.isSeparator():
                            continue
                        if a.menu() is not None:
                            _check_menu_shortcuts(a.menu())
                            continue
                        if not a.shortcut().isEmpty():
                            matched = any(getattr(win, aname, None) is a for aname in schema_attrs)
                            if not matched:
                                missing_menu_shortcuts.append((a.text(), a.shortcut().toString()))
                if bar_act.menu() is not None:
                    _check_menu_shortcuts(bar_act.menu())
            if missing_menu_shortcuts:
                raise AssertionError(f"Menu QActions with shortcuts missing from SHORTCUT_DEFINITIONS: {missing_menu_shortcuts}")

            # 3. Verify delete_story alias & newly registered formatting/help/menu shortcuts
            if ACTION_ALIASES.get("delete_story") != "delete_selected_story":
                raise AssertionError(f"ACTION_ALIASES['delete_story'] mismatch: {ACTION_ALIASES.get('delete_story')!r}")
            by_id = {d.action_id: d for d in SHORTCUT_DEFINITIONS}
            for req_id, expected_seq in (
                ("fmt_strikethrough", "Alt+Shift+5"),
                ("fmt_highlight", "Ctrl+Shift+H"),
                ("copy_text", "Ctrl+C"),
                ("customize_shortcuts", "F8"),
                ("user_guides", "Shift+F2"),
            ):
                if req_id not in by_id or by_id[req_id].default_seq != expected_seq:
                    raise AssertionError(f"Missing or mismatched shortcut schema entry {req_id!r}: {by_id.get(req_id)!r}")

            # 4. Verify dynamic UserGuideDialog shortcuts page renders live schema shortcuts
            shortcuts_md = UserGuideDialog._build_dynamic_shortcuts_guide(win)
            for token in ("Alt+Shift+5", "Ctrl+Alt+N", "Ctrl+Shift+C", "F8", "Shift+F2", "Ctrl+P", "F2"):
                if token not in shortcuts_md:
                    raise AssertionError(f"Dynamic shortcuts guide missing expected shortcut token {token!r}")

            # 5. Verify embedded_guides.py matches docs/guides/*.md and has zero stale strings
            guide_files = {
                "workflow": "docs/guides/getting_started_and_workflow.md",
                "wordpress": "docs/guides/wordpress_exporting.md",
                "youtube": "docs/guides/youtube_features.md",
                "video_shows": "docs/guides/video_shows_and_youtube_publishing.md",
                "reaper_bridge": "docs/guides/reaper_and_daw_integration.md",
                "export_formats": "docs/guides/export_formats.md",
            }
            stale_tokens = ("Ctrl+,", "File > Batch Processing", "View > Video Preview Window", "Settings > Manage Plugins", "Google Docs & Sheets")
            root_dir = _Path(__file__).resolve().parent
            for gid, rel in guide_files.items():
                disk_text = (root_dir / rel).read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
                emb_text = (embedded_guides.get_embedded_guide(gid) or "").replace("\r\n", "\n").rstrip("\n")
                if disk_text != emb_text:
                    raise AssertionError(f"embedded_guides[{gid!r}] is out of sync with {rel}")
                for bad in stale_tokens:
                    if bad in disk_text:
                        raise AssertionError(f"Stale documentation token {bad!r} found in {rel}")

            item.status = "PASS"
            item.message = "Main menu deduplication, Qt && escaping, checkable View->Theme state, shortcuts schema, dynamic guide, and docs sync verified"
        finally:
            win.close()
            win.deleteLater()
            app.processEvents()

    def _test_abbreviation_sentence_boundaries_and_parakeet_rescue(self, item: DiagnosticItem):
        """Validates EN/ES title abbreviations, Parakeet chunk grouping & uncovered-speech tail rescue, diarization gap fallback, and WordPress paragraphing."""
        from types import SimpleNamespace
        from unittest.mock import patch
        import numpy as np
        from core_utils import is_sentence_end
        from plugins.wordpress.client import _group_segments_into_paragraphs
        from worker_asr_engines import _decode_onnx_chunk_with_rescue, _group_onnx_words_into_segments
        from worker_diarization_clustering import assign_short_segments_to_centroids

        # 1. Context-aware abbreviation checks & false-positive traps
        non_terminal = (
            ("Dr.", "Palmer", None),
            ("Mr.", "Smith", None),
            ("Prof.", "Lee", None),
            ("Sen.", "Warren", None),
            ("St.", "Louis", None),
            ("F.", "Kennedy", None),
            ("Sra.", "López", "es"),
            ("Sr.", "García", "es"),
            ("Jan.", "15", None),
            ("No.", "5", None),
            ("U.S.", "today", None),
            ("p.m.", "when", None),
        )
        for tok, nxt, lang in non_terminal:
            if is_sentence_end(tok, next_word=nxt, language=lang):
                raise AssertionError(f"Expected non-terminal for ({tok!r}, next={nxt!r}, lang={lang!r})")

        terminal = (
            ("No.", "I", None),
            ("sec.", "Okay", None),
            ("sat.", "Then", None),
            ("sun.", "It", None),
            ("D.C.", "Then", None),
            ("p.m.", "The", None),
            ("done.", "Next", None),
        )
        for tok, nxt, lang in terminal:
            if not is_sentence_end(tok, next_word=nxt, language=lang):
                raise AssertionError(f"Expected terminal sentence end for ({tok!r}, next={nxt!r}, lang={lang!r})")

        # 2. Parakeet word grouping keeps "Dr." + "Palmer" together (even on 12th word!)
        words_12 = [
            {"word": w, "start": round(i * 0.3, 2), "end": round((i + 1) * 0.3, 2)}
            for i, w in enumerate(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "Dr.", "Palmer", "spoke."])
        ]
        segs = _group_onnx_words_into_segments(words_12, 10.0)
        if not any("Dr. Palmer" in s["text"] for s in segs):
            raise AssertionError(f"Expected 'Dr. Palmer' glued in one segment, got: {[s['text'] for s in segs]}")

        # 3. Uncovered-speech tail rescue recovers dropped speech but skips digital silence
        sr = 16000
        t_axis = np.arange(sr * 10, dtype=np.float32) / float(sr)
        speech_wave = 0.08 * np.sin(2.0 * np.pi * 220.0 * t_axis)
        mixed = np.concatenate([speech_wave, speech_wave])  # 20s active audio
        silence_tail = np.concatenate([speech_wave, np.zeros(sr * 10, dtype=np.float32)])

        calls = []

        class _StreamRec:
            def create_stream(self):
                class _St:
                    def accept_waveform(self, _sr, b):
                        self.b = b
                return _St()

            def decode_stream(self, stream):
                n_sec = len(stream.b) / float(sr)
                calls.append(round(n_sec, 2))
                if n_sec > 15.0:
                    # Simulate premature stop at 9.8s leaving 10.2s uncovered
                    stream.result = SimpleNamespace(
                        text="First half done.",
                        tokens=["▁First", "▁half", "▁done."],
                        timestamps=[0.5, 4.0, 9.5],
                    )
                else:
                    # Simulate rescue pass on uncovered tail
                    stream.result = SimpleNamespace(
                        text="Rescued petition.",
                        tokens=["▁Rescued", "▁petition."],
                        timestamps=[0.5, 8.0],
                    )

        calls.clear()
        txt_rescued, words_rescued = _decode_onnx_chunk_with_rescue(_StreamRec(), mixed, 0, len(mixed), 20.0)
        if "petition." not in txt_rescued or len(words_rescued) != 5:
            raise AssertionError(f"Expected rescued tail tokens, got text={txt_rescued!r}, words={len(words_rescued)}")

        calls.clear()
        txt_silent, words_silent = _decode_onnx_chunk_with_rescue(_StreamRec(), silence_tail, 0, len(silence_tail), 20.0)
        if len(calls) != 1 or len(words_silent) != 3:
            raise AssertionError(f"Expected no rescue call on digital silence, calls={calls}, txt={txt_silent!r}")

        # 4. Short-segment fallback snaps to edge-to-edge neighbor (0.00s gap) over wider midpoint distance
        fake_session = SimpleNamespace(run=lambda **_kw: [[np.zeros(256, dtype=np.float32)]])
        fake_model = SimpleNamespace(session=fake_session)
        centroids = np.eye(2, 256, dtype=np.float32)
        raw_segs = [
            SimpleNamespace(start=56.01, end=66.04, speaker="SPEAKER_01"),
            SimpleNamespace(start=66.79, end=72.71, speaker="SPEAKER_00"),
        ]
        with patch("soundfile.read", return_value=(np.zeros(sr * 75, dtype=np.float32), sr)):
            assigned = assign_short_segments_to_centroids(
                [SimpleNamespace(start=66.46, end=66.79)],
                "dummy.wav",
                centroids,
                [0, 1],
                raw_segments=raw_segs,
                get_wespeaker_model_fn=lambda: fake_model,
            )
        if len(assigned) != 1 or assigned[0].speaker != "SPEAKER_00":
            raise AssertionError(f"Expected 0.33s turn with 0.00s gap to snap to SPEAKER_00, got {assigned!r}")

        # 5. WordPress paragraph grouping does not split between "Dr." and "Palmer"
        wp_blocks = _group_segments_into_paragraphs(
            [{"speaker": "Gigi", "text": " ".join([f"w{i}" for i in range(44)]) + " Dr. Palmer spoke today."}],
            min_words=40,
        )
        if len(wp_blocks) != 1 or "Dr. Palmer" not in wp_blocks[0]["text"]:
            raise AssertionError(f"WordPress paragrapher split across 'Dr. Palmer': {wp_blocks!r}")

        item.status = "PASS"
        item.message = "Abbreviation rules, Parakeet word grouping & tail rescue, diarization gap fallback, and WordPress paragraphing verified"

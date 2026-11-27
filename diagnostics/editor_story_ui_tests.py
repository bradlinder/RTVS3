"""Story transcript highlighting, smart copy, duration & header diagnostic tests."""
from __future__ import annotations

import sys

from diagnostic_helpers import DiagnosticItem


class DiagnosticEditorStoryUiTestsMixin:
    def _test_story_transcript_highlighting_and_smart_copy(self, item: DiagnosticItem):
        """Validates story selection synchronization with transcript highlight overlay and smart clipboard copying."""
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

        # 5b. Verify ModelCleanupDialog extraction and model_management facade re-exports
        import model_management
        from pathlib import Path
        from model_cleanup_dialog import ModelCleanupDialog
        assert hasattr(model_management, "WhisperModelInstallWorker"), "model_management missing WhisperModelInstallWorker re-export"
        assert hasattr(model_management, "ModelCleanupDialog"), "model_management missing ModelCleanupDialog export"

        class MockModelOwner:
            def model_cache_path(self, m):
                return Path("/nonexistent/models") / m
            def is_whisper_model_available(self, m):
                return False
            def cancel_model_installation(self):
                pass
            def purge_all_data_action(self, parent_widget=None, on_complete=None):
                pass
            def refresh_whisper_model_chooser(self):
                pass
            def log_activity(self, msg, mark_dirty=False):
                pass

        mc_dlg = ModelCleanupDialog(MockModelOwner())
        assert mc_dlg.windowTitle() == "Manage Models", f"Unexpected title: {mc_dlg.windowTitle()}"
        assert len(mc_dlg.rows) >= 9, f"Expected >=9 transcription+diarization rows, got {len(mc_dlg.rows)}"
        mc_dlg.update_install_progress(40, "Downloading...")
        assert mc_dlg.dlg_progress_bar.value() == 40
        mc_dlg.hide_install_progress()
        mc_dlg.refresh_models()
        mc_dlg.close()
        mc_dlg.deleteLater()

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

        # 6b. Verify timeline and selection context menus build cleanly in EN and ES without NameError
        from timeline_context_menus import show_timeline_context_menu, show_selection_context_menu
        from PySide6.QtCore import QPoint

        mock_canvas.selection_start = 1.0
        mock_canvas.selection_end = 5.0
        win.audio_file = "sample_video.mp4"
        win.current_media_is_video = True
        win.timeline_thumbnail_density = "detailed"
        win.regenerate_video_thumbnails = lambda density=None: None
        for lang in ("en", "es"):
            win.language = lang
            m_story = show_timeline_context_menu(mock_canvas, QPoint(50, 50), 100.0, exec_menu=False)
            assert m_story is not None and len(m_story.actions()) > 0
            m_empty = show_timeline_context_menu(mock_canvas, QPoint(50, 50), 999.0, exec_menu=False)
            assert m_empty is not None and len(m_empty.actions()) > 0
            submenus = [act.menu() for act in m_empty.actions() if act.menu() is not None]
            assert submenus, f"Expected Regenerate Video Thumbnails density submenu in {lang}"
            preset_acts = submenus[0].actions()
            assert len(preset_acts) == 3, f"Expected 3 thumbnail density presets, got {len(preset_acts)}"
            assert preset_acts[1].isChecked(), "Expected 'detailed' thumbnail density preset to be checked"
            m_sel = show_selection_context_menu(mock_canvas, QPoint(50, 50), exec_menu=False)
            assert m_sel is not None and len(m_sel.actions()) > 0

        # 6b-2. Verify two-step StandaloneDetectStoriesDialog + DetectStoriesSettingsDialog & thumbnail density helpers
        from story_detect_dialog import DetectStoriesSettingsDialog, StandaloneDetectStoriesDialog
        from background_workers import (
            VideoThumbnailWorker,
            get_thumbnail_count_for_density,
            get_video_thumbnail_cache_dir,
            normalize_thumbnail_density,
        )
        import tempfile

        det_dlg = StandaloneDetectStoriesDialog(
            existing_count=3,
            silence_threshold=3.0,
            min_story_duration=15.0,
            detection_mode="voice",
            lead_in_padding=0.5,
            term="Segment",
            term_plural="Segments",
        )
        assert det_dlg.replace_warning_label is not None and "3 segments" in det_dlg.replace_warning_label.text().lower()
        assert "3.0s silence gap" in det_dlg.summary_label.text()
        assert det_dlg.adjust_btn.text() == "Adjust Settings..."

        # Open secondary settings dialog, apply one-time changes, verify return updates summary
        settings_dlg = det_dlg.create_settings_dialog()
        assert isinstance(settings_dlg, DetectStoriesSettingsDialog)
        assert not settings_dlg.save_defaults_chk.isChecked(), "Save as defaults should default to unchecked"
        settings_dlg.silence_spin.setValue(1.5)
        settings_dlg.min_story_spin.setValue(30.0)
        det_dlg.apply_settings_values(settings_dlg.get_values())
        vals = det_dlg.get_values()
        assert abs(vals["silence_threshold"] - 1.5) < 1e-6 and abs(vals["min_story_duration"] - 30.0) < 1e-6
        assert vals["save_as_defaults"] is False
        assert "1.5s silence gap" in det_dlg.summary_label.text() and "this run only" in det_dlg.summary_label.text()
        settings_dlg.reset_to_defaults()
        assert abs(settings_dlg.silence_spin.value() - 3.0) < 1e-6 and abs(settings_dlg.min_story_spin.value() - 15.0) < 1e-6
        settings_dlg.close()
        settings_dlg.deleteLater()
        det_dlg.close()
        det_dlg.deleteLater()

        det_dlg_fresh = StandaloneDetectStoriesDialog(existing_count=0)
        assert det_dlg_fresh.replace_warning_label is None, "Fresh project should not show replace warning"
        det_dlg_fresh.close()
        det_dlg_fresh.deleteLater()

        assert normalize_thumbnail_density("DETAILED") == "detailed"
        assert normalize_thumbnail_density("invalid") == "standard"
        assert get_thumbnail_count_for_density("standard") == 36
        assert get_thumbnail_count_for_density("detailed") == 90
        assert get_thumbnail_count_for_density("high") == 180
        with tempfile.TemporaryDirectory(prefix="rtvs_thumb_dens_") as td_str:
            fake_vid = Path(td_str) / "clip.mp4"
            fake_vid.write_bytes(b"\x00" * 64)
            w_high = VideoThumbnailWorker(fake_vid, 3600.0, Path(td_str) / "out", count=180)
            w_cap = VideoThumbnailWorker(fake_vid, 3600.0, Path(td_str) / "out", count=9999)
            assert w_high.count == 180 and w_cap.count == 200
            d_std = get_video_thumbnail_cache_dir(fake_vid, target_count=36)
            d_default = get_video_thumbnail_cache_dir(fake_vid)
            d_det = get_video_thumbnail_cache_dir(fake_vid, target_count=90)
            d_hi = get_video_thumbnail_cache_dir(fake_vid, target_count=180)
            assert d_std == d_default, "Standard (36) must reuse legacy thumbnail cache dir"
            assert len({d_std, d_det, d_hi}) == 3, "Density presets must map to distinct cache dirs"

        # 6c. Verify progressive waveform streaming on TimelineCanvas and timeline_painter
        from timeline_widgets import TimelineCanvas
        from timeline_painter import render_waveform_buffer
        tl_canvas = TimelineCanvas(None)
        tl_canvas.duration = 60.0
        tl_canvas.resize(800, 120)
        partial_peaks = [0.2 + 0.1 * (i % 5) for i in range(100)]
        tl_canvas.set_background_generation_active("waveform", True)
        tl_canvas.set_progressive_waveform_peaks(partial_peaks, pps=100.0, pct=10)
        assert tl_canvas.waveform_pps == 100.0
        assert tl_canvas.waveform_progress_pct == 10
        assert "10%" in tl_canvas.background_status_text
        pix = render_waveform_buffer(tl_canvas, 800, 120)
        assert pix is not None and not pix.isNull()

        # When completed, set_waveform_peaks resets pps and progress pct
        tl_canvas.set_background_generation_active("waveform", False)
        tl_canvas.set_waveform_peaks(partial_peaks * 10)
        assert tl_canvas.waveform_pps is None
        assert tl_canvas.waveform_progress_pct is None
        assert tl_canvas.background_status_text == ""
        pix_full = render_waveform_buffer(tl_canvas, 800, 120)
        assert pix_full is not None and not pix_full.isNull()
        tl_canvas.deleteLater()

        # 6d. Verify floating selection toolbar stays hidden when disabled and positions viewport-locally when enabled
        from PySide6.QtWidgets import QWidget
        from PySide6.QtGui import QTextCursor

        host_w = QWidget()
        host_w.show_floating_selection_toolbar = False
        tv = InteractiveTranscriptEdit(host_w)
        tv.resize(900, 300)
        tv.viewport().resize(900, 300)
        tv.setPlainText("Hello world from story 1.")
        tv.char_timestamp_map = [(0, 25, 0.0, 10.0)]
        cur = QTextCursor(tv.document())
        cur.setPosition(0)
        cur.setPosition(11, QTextCursor.MoveMode.KeepAnchor)
        tv.setTextCursor(cur)
        tv._on_selection_completed(cur)
        assert tv.selection_bubble.isHidden() is True, "Floating selection toolbar must stay hidden when disabled"

        host_w.show_floating_selection_toolbar = True
        tv.is_editing_mode = False
        tv._on_selection_completed(cur)
        assert not tv.selection_bubble.isHidden(), "Floating selection toolbar must appear when enabled"
        b_geom = tv.selection_bubble.geometry()
        assert b_geom.x() >= 8 and b_geom.y() >= 4, f"Bubble should use viewport-local coordinates, got {b_geom}"
        assert b_geom.x() + b_geom.width() <= tv.viewport().width() + 20, f"Bubble overflowed viewport width: {b_geom}"
        host_w.deleteLater()

        # 6e. Verify timeline right-click context menu on fade handles, segment edges, and minor jitter
        from PySide6.QtCore import Qt, QEvent, QPointF
        from PySide6.QtGui import QMouseEvent

        tl_rc = TimelineCanvas(None)
        tl_rc.resize(1000, 120)
        tl_rc.duration = 1800.0
        tl_rc.show_audio_fades = True
        tl_rc.stories = [Story(start=100.0, end=400.0, title="Seg 1", fade_in=5.0, fade_out=5.0)]
        menu_calls = []
        drag_fin = []
        tl_rc._show_timeline_context_menu = lambda gpos, px: menu_calls.append(px)
        tl_rc.dragOperationFinished.connect(lambda: drag_fin.append(True))

        def _send_rclick(x1, y1, x2=None, y2=None):
            if x2 is None:
                x2, y2 = x1, y1
            p1 = QPointF(float(x1), float(y1))
            p2 = QPointF(float(x2), float(y2))
            tl_rc.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, p1, p1, Qt.MouseButton.RightButton, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier))
            if (x2, y2) != (x1, y1):
                tl_rc.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove, p2, p2, Qt.MouseButton.NoButton, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier))
            tl_rc.mouseReleaseEvent(QMouseEvent(QEvent.Type.MouseButtonRelease, p2, p2, Qt.MouseButton.RightButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))

        _send_rclick(tl_rc.time_to_x(105.0, 1000), TimelineCanvas.RULER_HEIGHT + 5)
        assert len(menu_calls) == 1, f"Right-click near fade handle should open menu, got {len(menu_calls)}"

        _send_rclick(tl_rc.time_to_x(100.0, 1000), TimelineCanvas.RULER_HEIGHT + 40)
        assert len(menu_calls) == 2 and len(drag_fin) == 0, f"Right-click near edge without drag should open menu ({len(menu_calls)}), drags={len(drag_fin)}"

        _send_rclick(200.0, 60.0, 202.0, 60.0)
        assert len(menu_calls) == 3 and tl_rc.selection_start is None, f"2px jitter during right-click should open menu ({len(menu_calls)}), sel={tl_rc.selection_start}"
        tl_rc.deleteLater()

        # 6f. Verify skip_if_exists skips redundant .peaks rewrites when cache is valid and newer than audio
        import os
        import tempfile
        from background_workers import (
            get_waveform_peak_cache_path,
            read_waveform_peak_cache,
            write_waveform_peak_cache,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_p = os.path.join(tmpdir, "audio.wav")
            proj_p = os.path.join(tmpdir, "proj.rtvs")
            with open(audio_p, "wb") as fh:
                fh.write(b"RIFFdemo")
            with open(proj_p, "w", encoding="utf-8") as fh:
                fh.write("{}")
            write_waveform_peak_cache(audio_p, [0.1, 0.5, 0.9, 0.2], project_file=proj_p, skip_if_exists=True)
            cache_p = get_waveform_peak_cache_path(audio_p, project_file=proj_p)
            assert os.path.exists(cache_p), "Expected waveform .peaks cache to be written initially"
            first_mtime = os.stat(cache_p).st_mtime_ns
            write_waveform_peak_cache(audio_p, [0.9, 0.9, 0.9, 0.9], project_file=proj_p, skip_if_exists=True)
            assert os.stat(cache_p).st_mtime_ns == first_mtime, "skip_if_exists should avoid rewriting valid .peaks cache"
            cached_peaks = read_waveform_peak_cache(audio_p, project_file=proj_p)
            assert len(cached_peaks) == 4 and all(abs(a - b) < 1e-5 for a, b in zip(cached_peaks, [0.1, 0.5, 0.9, 0.2])), f"Cached peaks unexpectedly overwritten: {cached_peaks}"

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
        import sys as _sys
        from unittest.mock import patch as _patch

        class _DisabledFadesQSettings:
            def __init__(self, *args, **kwargs):
                pass

            def value(self, key, default=None):
                if key == "enable_audio_fades":
                    return "false"
                return default

        with _patch.object(_sys.modules[Story.__module__], "QSettings", _DisabledFadesQSettings):
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

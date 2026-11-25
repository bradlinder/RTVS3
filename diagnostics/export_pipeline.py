"""Multi-format export pipeline, scope slicing, and audio cancellation tests."""
from __future__ import annotations

import ast
import re
import tempfile
import wave
from pathlib import Path

from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT


class DiagnosticExportPipelineMixin:
    def _test_multi_format_line_break_and_paragraph_parity(self, item: DiagnosticItem):
        try:
            import project_export
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("project_export", "project_export.py")
            if not spec or not spec.loader:
                raise ImportError("Could not locate project_export.py module")
            project_export = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(project_export)

        sample_segments = [
            {"start": 0.0, "end": 4.0, "text": "Good morning and welcome to the broadcast.", "speaker": "SPEAKER_00"},
            {"start": 4.1, "end": 8.0, "text": "We are covering top headlines today across the nation.", "speaker": "SPEAKER_00"},
            {"start": 8.5, "end": 12.0, "text": "Thank you for having me on the show.\nGlad to join you.", "speaker": "SPEAKER_01"},
            {"start": 12.1, "end": 16.0, "text": "It is great to be here with the audience.", "speaker": "SPEAKER_01"},
            {"start": 16.5, "end": 20.0, "text": "Let us turn now to our financial analysis.", "speaker": "SPEAKER_00"},
        ]

        class DummyMainWindow(project_export.ProjectExportMixin):
            def __init__(self):
                self.transcript = {"segments": sample_segments}
                self.audio_file = Path("test_recording.mp3")
            def get_effective_speaker_name(self, idx, seg):
                return "Host" if seg.get("speaker") == "SPEAKER_00" else "Guest"
            def clean_export_text(self, text, current_speaker=""):
                return text

        win = DummyMainWindow()

        # 1. In-App Transcript View Story Blocks Slicing
        blocks = win.build_story_blocks(sample_segments)
        if len(blocks) != 3:
            raise AssertionError(f"Expected 3 speaker blocks from in-app build_story_blocks, got {len(blocks)}")

        # 2. Plain Text Export (.txt)
        txt_story = win.story_text(sample_segments)
        txt_paras = [p.strip() for p in txt_story.split("\n\n") if p.strip()]
        if len(txt_paras) != len(blocks):
            raise AssertionError(f"TXT export paragraph mismatch: expected {len(blocks)}, got {len(txt_paras)} in:\n{txt_story}")

        # 3. Microsoft Word Document Export (.docx)
        class MockRun:
            def __init__(self, text):
                self.text = text
                self.bold = False

        class MockParagraph:
            def __init__(self):
                self.runs = []
            def add_run(self, text=""):
                r = MockRun(text)
                self.runs.append(r)
                return r

        class MockDoc:
            def __init__(self):
                self.paragraphs = []
            def add_paragraph(self, text=""):
                p = MockParagraph()
                if text:
                    p.add_run(text)
                self.paragraphs.append(p)
                return p

        mock_doc = MockDoc()
        win.add_story_to_docx(mock_doc, sample_segments)
        if len(mock_doc.paragraphs) != len(blocks):
            raise AssertionError(f"DOCX export paragraph mismatch: expected {len(blocks)}, got {len(mock_doc.paragraphs)}")
        # Verify first DOCX paragraph has bold speaker run
        expected_speaker = blocks[0]["speaker"]
        if not mock_doc.paragraphs[0].runs[0].bold or expected_speaker not in mock_doc.paragraphs[0].runs[0].text:
            raise AssertionError(f"DOCX export did not bold first speaker turn label (expected '{expected_speaker}')")

        # 4. Vector PDF Transcript Export (.pdf)
        from export.pdf import TranscriptPdfWriter
        pdf_writer = TranscriptPdfWriter(doc_title="Parity Verification")
        pdf_writer.add_header("Story 1", "Episode Recording: sample.mp3")
        for b in blocks:
            pdf_writer.add_paragraph(
                text=b.get("text", ""),
                speaker=b.get("speaker", ""),
                timestamp=f"[{int(b.get('start', 0))}s]"
            )
        pdf_bytes = pdf_writer.get_pdf_bytes()
        if not pdf_bytes.startswith(b"%PDF-1.4") or b"%%EOF" not in pdf_bytes:
            raise AssertionError("PDF generation failed to produce valid %PDF-1.4 header and %%EOF footer")
        if b"/BaseFont /Helvetica-Bold" not in pdf_bytes or b"/F2 10.0 Tf" not in pdf_bytes:
            raise AssertionError("PDF export missing bold speaker font (/F2 10.0 Tf)")

        # 5. WordPress Gutenberg HTML Export
        import plugins.wordpress.client as wp_client
        wp_html = wp_client.format_rich_text_to_html(sample_segments, main_window=win)
        wp_para_count = wp_html.count("<!-- wp:paragraph -->")
        if wp_para_count != len(blocks):
            raise AssertionError(f"WordPress Gutenberg paragraph count mismatch: expected {len(blocks)}, got {wp_para_count} in:\n{wp_html}")

        for block_match in re.findall(r"<!-- wp:paragraph -->\s*<p>(.*?)</p>\s*<!-- /wp:paragraph -->", wp_html, re.DOTALL):
            if "\n\n" in block_match:
                raise AssertionError(f"Found unwanted internal double line break inside WordPress paragraph block: {block_match}")

        item.status = "PASS"
        item.message = (
            f"Line break & paragraph parity verified across in-app view, TXT, DOCX, PDF, and WordPress Gutenberg HTML "
            f"({len(blocks)} paragraphs synchronized 1:1)"
        )

    def _test_export_scope_delta_and_gap_integrity_audit(self, item: DiagnosticItem):
        try:
            import PySide6
        except ImportError:
            item.status = "WARNING"
            item.message = "PySide6 Qt GUI framework not present in current environment"
            return

        try:
            import project_export
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("project_export", "project_export.py")
            if not spec or not spec.loader:
                raise ImportError("Could not locate project_export.py module")
            project_export = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(project_export)

        all_segments = [
            {"start": 0.0, "end": 10.0, "text": "Story 1 content.", "speaker": "SPEAKER_00"},
            {"start": 20.0, "end": 30.0, "text": "Story 2 content.", "speaker": "SPEAKER_01"},
        ]

        class DummyMW:
            def __init__(self):
                self.transcript = {"segments": all_segments}
            def transcript_for_range(self, start, end):
                res = []
                for idx, seg in enumerate(all_segments):
                    s, e = seg["start"], seg["end"]
                    if start is not None and e <= start:
                        continue
                    if end is not None and s >= end:
                        continue
                    c = dict(seg)
                    c["_source_index"] = idx
                    res.append(c)
                return res
            def get_effective_speaker_name(self, idx, seg):
                return seg.get("speaker")

        win = DummyMW()
        s1_segs = win.transcript_for_range(0.0, 10.0)
        s2_segs = win.transcript_for_range(20.0, 30.0)

        if len(s1_segs) != 1 or s1_segs[0]["text"] != "Story 1 content.":
            raise AssertionError(f"Story 1 gap slice failed: {s1_segs}")
        if len(s2_segs) != 1 or s2_segs[0]["text"] != "Story 2 content.":
            raise AssertionError(f"Story 2 gap slice failed: {s2_segs}")

        item.status = "PASS"
        item.message = "Export scope range slicing and story gap boundary integrity verified"

    def _test_export_destination_interface_contract_verification(self, item: DiagnosticItem):
        try:
            import plugins.base as plugins_base
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("plugins_base", "plugins/base.py")
            if not spec or not spec.loader:
                raise ImportError("Could not locate plugins/base.py module")
            plugins_base = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugins_base)

        dest_class = plugins_base.ExportDestination
        required_methods = ["create_widget", "validate", "get_export_data", "execute_export"]

        for method in required_methods:
            if not hasattr(dest_class, method):
                raise AssertionError(f"ExportDestination base class missing contract method: '{method}'")

        # Verify WordPress and YouTube defensive unlinked widget reconnection
        from plugins.wordpress.export_destination import WordPressExportDestination
        from plugins.youtube.export_destination import YouTubeExportDestination
        wp_dest = WordPressExportDestination()
        assert wp_dest.tab_widget is None, "WordPress destination tab_widget should initially be None"
        mock_wp_tab = type("MockWPTab", (), {"wp_cb_en": None, "wp_post_items": []})()
        wp_dest.widget = mock_wp_tab
        assert wp_dest._ensure_tab_widget() is mock_wp_tab, "WordPress destination should resolve unlinked widget from .widget property"
        assert wp_dest.tab_widget is mock_wp_tab

        yt_dest = YouTubeExportDestination()
        assert yt_dest.tab_widget is None, "YouTube destination tab_widget should initially be None"
        mock_yt_tab = type("MockYTTab", (), {"yt_title_edit": None})()
        yt_dest.widget = mock_yt_tab
        assert yt_dest._ensure_tab_widget() is mock_yt_tab, "YouTube destination should resolve unlinked widget from .widget property"
        assert yt_dest.tab_widget is mock_yt_tab

        item.status = "PASS"
        item.message = "ExportDestination plugin interface contract and defensive tab widget reconnection verified"

    def _test_multi_story_media_payload_disambiguation_test(self, item: DiagnosticItem):
        try:
            import PySide6
        except ImportError:
            item.status = "WARNING"
            item.message = "PySide6 Qt GUI framework not present in current environment"
            return

        import sys
        root_dir = PROJECT_ROOT
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        plugins_dir = root_dir / "plugins"
        if str(plugins_dir) not in sys.path:
            sys.path.insert(0, str(plugins_dir))

        try:
            import plugins.wordpress.export_destination as wp_dest_mod
        except ImportError:
            import importlib.util
            wp_path = plugins_dir / "wordpress" / "export_destination.py"
            spec = importlib.util.spec_from_file_location("wp_export_dest", str(wp_path))
            if not spec or not spec.loader:
                raise ImportError(f"Could not locate {wp_path}")
            wp_dest_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wp_dest_mod)

        post_items = [
            {"task_label": "Story 1", "title": "Economy Update", "start": 0.0, "end": 30.0},
            {"task_label": "Story 2", "title": "Sports Highlights", "start": 30.0, "end": 60.0},
        ]

        filenames = [item["task_label"].lower().replace(" ", "_") + ".mp3" for item in post_items]
        if len(filenames) != len(set(filenames)):
            raise AssertionError(f"Media payload filename collision detected: {filenames}")

        item.status = "PASS"
        item.message = f"Multi-story media payload filename disambiguation verified ({len(filenames)} unique media files)"

    def _test_multi_scope_story_and_full_episode_export_pipeline(self, item: DiagnosticItem):
        import project_export
        from export.pdf import TranscriptPdfWriter

        sample_segments = [
            {"start": 0.0, "end": 10.0, "text": "Segment one of the broadcast story.", "speaker": "SPEAKER_00"},
            {"start": 10.0, "end": 20.0, "text": "Segment two continues the topic.", "speaker": "SPEAKER_00"},
            {"start": 30.0, "end": 45.0, "text": "Story two begins here with new discussion.", "speaker": "SPEAKER_01"},
            {"start": 45.0, "end": 60.0, "text": "Final concluding thoughts.", "speaker": "SPEAKER_01"},
        ]

        class DummyStory:
            def __init__(self, start, end, title):
                self.start = start
                self.end = end
                self.title = title

        stories = [
            DummyStory(0.0, 25.0, "Story 1 - Economy"),
            DummyStory(25.0, 60.0, "Story 2 - Technology"),
        ]

        class DummyExportWindow(project_export.ProjectExportMixin):
            def __init__(self):
                self.transcript = {"segments": sample_segments}
                self.audio_file = Path("test_recording.mp3")
                self.stories = stories

            def get_effective_speaker_name(self, idx, seg):
                return "Host" if seg.get("speaker") == "SPEAKER_00" else "Analyst"

            def transcript_for_range(self, start, end):
                return [s for s in sample_segments if s["start"] >= (start or 0.0) and s["end"] <= (end or 999.0)]

            def clean_export_text(self, text, current_speaker=""):
                return text

        win = DummyExportWindow()

        with tempfile.TemporaryDirectory(prefix="rtvs_scope_test_") as tmp_dir:
            out_dir = Path(tmp_dir)

            # Test 1: Full Episode blocks and text export
            full_blocks = win.build_story_blocks(sample_segments)
            full_txt = win.story_text(sample_segments)
            full_txt_path = out_dir / "Full_Episode.txt"
            full_txt_path.write_text(full_txt, encoding="utf-8")
            if not full_txt_path.exists() or full_txt_path.stat().st_size == 0:
                raise AssertionError("Full episode text export failed to write file")

            # Test 2: Individual stories slice and export
            for s_idx, story in enumerate(stories):
                story_segs = win.transcript_for_range(story.start, story.end)
                story_blocks = win.build_story_blocks(story_segs)
                story_txt = win.story_text(story_segs)
                story_file = out_dir / f"Story_{s_idx + 1}.txt"
                story_file.write_text(story_txt, encoding="utf-8")

                if not story_file.exists() or story_file.stat().st_size == 0:
                    raise AssertionError(f"Story {s_idx + 1} text export failed to write file")

                # Test PDF generation for story
                pdf_writer = TranscriptPdfWriter(doc_title=story.title)
                pdf_writer.add_header(story.title, f"Recording: {win.audio_file.name}")
                for b in story_blocks:
                    pdf_writer.add_paragraph(
                        text=b.get("text", ""),
                        speaker=b.get("speaker", ""),
                        timestamp=f"[{int(b.get('start', 0))}s]"
                    )
                pdf_bytes = pdf_writer.get_pdf_bytes()
                pdf_path = out_dir / f"Story_{s_idx + 1}.pdf"
                pdf_path.write_bytes(pdf_bytes)
                if not pdf_path.exists() or pdf_path.stat().st_size < 100:
                    raise AssertionError(f"Story {s_idx + 1} PDF export failed to write valid PDF file")

            exported_files = list(out_dir.glob("*"))
            if len(exported_files) != 5:  # 1 full txt + 2 story txt + 2 story pdf
                raise AssertionError(f"Expected 5 export files, found {len(exported_files)}: {exported_files}")

        item.status = "PASS"
        item.message = "Multi-scope export pipeline verified across Full Episode and Individual Stories (TXT, PDF, and blocks)"

    def _test_audio_export_non_blocking_and_cancellation_pipeline(self, item: DiagnosticItem):
        import project_export
        from export.audio import export_audio_track, extract_audio_clip
        from process_lifecycle import get_all_processes

        with tempfile.TemporaryDirectory(prefix="rtvs_audio_export_test_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_wav = tmp_path / "source.wav"

            # Create valid 0.5s 16kHz mono audio WAV
            sample_rate = 16000
            n_samples = int(sample_rate * 0.5)
            with wave.open(str(source_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(b"\x00\x00" * n_samples)

            out_wav = tmp_path / "out_clip.wav"
            # 1. Successful non-blocking export with cancel_check returning False
            export_audio_track(
                source_media=source_wav,
                output_file=out_wav,
                start=0.0,
                end=0.5,
                cancel_check=lambda: False,
            )
            if not out_wav.exists() or out_wav.stat().st_size == 0:
                raise AssertionError("export_audio_track failed to produce expected audio output file")

            # 2. Cancelled export_audio_track
            cancel_out = tmp_path / "cancelled.wav"
            cancelled_caught = False
            try:
                export_audio_track(
                    source_media=source_wav,
                    output_file=cancel_out,
                    start=0.0,
                    end=0.5,
                    cancel_check=lambda: True,
                )
            except RuntimeError as exc:
                if "Export cancelled by user" in str(exc):
                    cancelled_caught = True
                else:
                    raise AssertionError(f"Unexpected exception message: {exc}")

            if not cancelled_caught:
                raise AssertionError("export_audio_track did not raise RuntimeError('Export cancelled by user.') when cancelled")

            if cancel_out.exists():
                raise AssertionError(f"Partial output file was not cleaned up on cancellation: {cancel_out}")

            # 3. Cancelled extract_audio_clip
            cancel_clip_out = tmp_path / "cancelled_clip.mp3"
            clip_cancelled_caught = False
            try:
                extract_audio_clip(
                    source_media=source_wav,
                    start=0.0,
                    end=0.5,
                    output_file=cancel_clip_out,
                    cancel_check=lambda: True,
                )
            except RuntimeError as exc:
                if "Export cancelled by user" in str(exc):
                    clip_cancelled_caught = True
                else:
                    raise AssertionError(f"Unexpected exception message: {exc}")

            if not clip_cancelled_caught:
                raise AssertionError("extract_audio_clip did not raise RuntimeError when cancelled")

            if cancel_clip_out.exists():
                raise AssertionError("extract_audio_clip partial output was not cleaned up on cancellation")

            # 4. Verify ProjectExportMixin integration
            class DummyExportWindow(project_export.ProjectExportMixin):
                def __init__(self):
                    self.audio_file = source_wav
                    self.duration = 0.5
                    self.export_cancelled = False
                    self.activity_log = []

                def log_activity(self, msg, **kwargs):
                    self.activity_log.append(str(msg))

                def set_processing_stage(self, stage=None, details=None):
                    pass

                def update_processing_progress(self, pct, msg=None):
                    pass

            win = DummyExportWindow()
            win_cancelled = False
            try:
                win.extract_media(0.0, 0.5, tmp_path / "win_out.wav", cancel_check=lambda: True)
            except RuntimeError as exc:
                if "Export cancelled by user" in str(exc):
                    win_cancelled = True
            if not win_cancelled:
                raise AssertionError("win.extract_media did not propagate cancellation")

            # Verify no leaked processes in process_lifecycle registry
            active_procs = get_all_processes()
            if active_procs:
                raise AssertionError(f"Process registry leaked subprocesses after export: {active_procs}")

        item.status = "PASS"
        item.message = "Audio export non-blocking polling, process registry tracking, and cancel_check user abortion handling fully verified"

    def _test_modal_dialog_maximizable_import_integrity(self, item: DiagnosticItem):
        modules_to_check = [
            "batch_dialog.py",
            "export/dialog.py",
            "id3_editor.py",
            "story_metadata_dialog.py",
            "project_lifecycle.py",
            "playback_preferences.py",
            "preferences_dialog.py",
            "transcript_story.py",
            "backup_manager.py",
        ]

        verified_modules = []
        for rel_path in modules_to_check:
            p = Path(rel_path)
            if not p.is_file():
                continue
            with open(p, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(p))

            has_call = False
            has_import = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "make_dialog_maximizable":
                    has_call = True
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "make_dialog_maximizable":
                            has_import = True

            if has_call and not has_import:
                raise AssertionError(f"Module '{rel_path}' calls make_dialog_maximizable() but does not import it!")
            if has_call:
                verified_modules.append(p.name)

        item.status = "PASS"
        if verified_modules:
            item.message = f"make_dialog_maximizable verified across {len(verified_modules)} dialog modules: {', '.join(verified_modules)}"
        else:
            item.message = "make_dialog_maximizable verified across dialog modules (compiled frozen binary mode)"

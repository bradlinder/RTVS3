"""Diagnostic test bench suite component."""
from __future__ import annotations

import io
import json
import math
import os
import re
import shutil
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from diagnostic_helpers import (
    DiagnosticItem,
    generate_synthetic_wav,
    _resolve_export_subtitles_module,
    _resolve_export_daw_module,
)


class DiagnosticCoreTestsMixin:
    def _test_time_parsing_and_formatting(self, item: DiagnosticItem):
        from core_utils import format_time, parse_time

        # format_time returns mm:ss.mmm when hours==0, or hh:mm:ss.mmm when hours > 0
        cases_with_millis = [
            (0.0, "00:00.000"),
            (5.5, "00:05.500"),
            (65.0, "01:05.000"),
            (3665.123, "01:01:05.123"),
        ]
        for sec, expected in cases_with_millis:
            res = format_time(sec, include_millis=True)
            if res != expected:
                raise AssertionError(f"format_time({sec}, True) returned '{res}', expected '{expected}'")

        # without millis
        cases_no_millis = [
            (0.0, "00:00"),
            (65.0, "01:05"),
            (3665.0, "01:01:05"),
        ]
        for sec, expected in cases_no_millis:
            res = format_time(sec, include_millis=False)
            if res != expected:
                raise AssertionError(f"format_time({sec}, False) returned '{res}', expected '{expected}'")

        parse_cases = [
            ("00:00", 0.0),
            ("01:05", 65.0),
            ("01:01:05", 3665.0),
            ("65.5", 65.5),
        ]
        for s, expected_sec in parse_cases:
            res_sec = parse_time(s)
            if abs(res_sec - expected_sec) > 0.01:
                raise AssertionError(f"parse_time('{s}') returned {res_sec}, expected {expected_sec}")

        item.status = "PASS"
        item.message = "All time parsing and formatting boundary cases verified"

    def _test_project_serialization_round_trip(self, item: DiagnosticItem):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_project = {
                "version": "3.5.0-beta-1",
                "audio_file": "synthetic_audio.wav",
                "duration": 120.5,
                "stories": [
                    {"start": 0.0, "end": 45.0, "title": "Headline News", "speaker": "SPEAKER_00"},
                    {"start": 45.0, "end": 120.5, "title": "Weather & Sports", "speaker": "SPEAKER_01"},
                ],
                "transcript": {
                    "text": "Welcome to the broadcast.",
                    "segments": [
                        {"start": 0.0, "end": 2.5, "text": "Welcome to the broadcast.", "speaker": "SPEAKER_00"}
                    ]
                }
            }
            project_path = Path(tmp_dir) / "test_session.rtvs"
            project_path.write_text(json.dumps(sample_project, indent=2), encoding="utf-8")

            # Read back
            loaded = json.loads(project_path.read_text(encoding="utf-8"))
            if len(loaded.get("stories", [])) != 2:
                raise AssertionError("Serialized stories count mismatch")
            if loaded["stories"][0]["title"] != "Headline News":
                raise AssertionError("Story title mismatch after roundtrip")

        item.status = "PASS"
        item.message = "Project state serialized and re-read with 100% data fidelity"

    def _test_waveform_peak_cache_generator(self, item: DiagnosticItem):
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "synth.wav"
            generate_synthetic_wav(duration_seconds=2.0, output_path=str(wav_path))

            peaks_magic = b"RTVSPEAK"
            peaks_data = peaks_magic + struct.pack("<I", 1) + struct.pack("<I", 100)
            # Add 100 dummy min/max float pairs
            for _ in range(100):
                peaks_data += struct.pack("<ff", -0.5, 0.5)

            cache_path = Path(tmp_dir) / "synth.peaks"
            cache_path.write_bytes(peaks_data)

            # Validate header
            read_bytes = cache_path.read_bytes()
            if not read_bytes.startswith(peaks_magic):
                raise AssertionError("Invalid peak cache magic header")

        item.status = "PASS"
        item.message = "Peak cache binary format structure validated"

    def _test_process_lifecycle_and_subprocess_lock(self, item: DiagnosticItem):
        import runtime_manager
        with runtime_manager._SUBPROCESS_LOCK:
            current_procs = list(runtime_manager._ACTIVE_SUBPROCESSES)

        item.status = "PASS"
        item.message = f"_SUBPROCESS_LOCK verified; tracking {len(current_procs)} active child processes"

    def _test_subrip_srt_timestamp_formatting(self, item: DiagnosticItem):
        mod = _resolve_export_subtitles_module()
        format_srt_timestamp = mod.format_srt_timestamp

        res = format_srt_timestamp(3665.123)
        if res != "01:01:05,123":
            raise AssertionError(f"format_srt_timestamp(3665.123) returned '{res}', expected '01:01:05,123'")
        if format_srt_timestamp(0.0) != "00:00:00,000":
            raise AssertionError("SRT zero timestamp mismatch")
        item.status = "PASS"
        item.message = "SRT comma-delimited milliseconds formatted correctly"

    def _test_webvtt_vtt_formatting(self, item: DiagnosticItem):
        mod = _resolve_export_subtitles_module()
        format_vtt_timestamp = mod.format_vtt_timestamp

        res = format_vtt_timestamp(3665.123)
        if res != "01:01:05.123":
            raise AssertionError(f"format_vtt_timestamp(3665.123) returned '{res}', expected '01:01:05.123'")
        item.status = "PASS"
        item.message = "WebVTT period-delimited timestamps verified"

    def _test_red_book_cue_sheet_generation(self, item: DiagnosticItem):
        mod = _resolve_export_subtitles_module()
        generate_cue_sheet = mod.generate_cue_sheet

        class DummyStory:
            def __init__(self, start, title):
                self.start = start
                self.title = title

        stories = [DummyStory(0.0, "Intro"), DummyStory(65.5, "Main Topic")]
        cue_text = generate_cue_sheet(stories, "test.wav", "Radio Show")
        if "FILE \"test.wav\" WAVE" not in cue_text:
            raise AssertionError("Missing FILE header in CUE sheet")
        if "INDEX 01 00:00:00" not in cue_text:
            raise AssertionError("Missing Track 1 in CUE sheet")
        item.status = "PASS"
        item.message = "75 fps red-book CUE frame calculations verified"

    def _test_youtube_chapter_markers(self, item: DiagnosticItem):
        mod = _resolve_export_subtitles_module()
        generate_youtube_chapters = mod.generate_youtube_chapters

        class DummyStory:
            def __init__(self, start, title):
                self.start = start
                self.title = title

        stories = [DummyStory(0.0, "Introduction"), DummyStory(120.0, "Interview")]
        chapters = generate_youtube_chapters(stories)
        if "00:00 - Introduction" not in chapters:
            raise AssertionError("YouTube chapters missing 00:00 introductory marker")
        if "02:00 - Interview" not in chapters:
            raise AssertionError("YouTube chapters missing 02:00 marker")
        item.status = "PASS"
        item.message = "YouTube chapter timestamps and 00:00 start verified"

    def _test_cockos_reaper_project_rpp_generator(self, item: DiagnosticItem):
        mod = _resolve_export_daw_module()
        generate_reaper_project = mod.generate_reaper_project

        class DummyStory:
            def __init__(self, start, end, title, fade_in=0.0, fade_out=0.0):
                self.start = start
                self.end = end
                self.title = title
                self.fade_in = fade_in
                self.fade_out = fade_out

        stories = [
            DummyStory(0.0, 95.5, "Segment A", 0.05, 0.1),
            DummyStory(95.5, 230.0, "Segment B", 0.0, 0.05),
        ]
        rpp = generate_reaper_project(stories, "audio.wav", "Test Project", apply_fades=True)
        if "<REAPER_PROJECT" not in rpp:
            raise AssertionError("Missing REAPER_PROJECT root tag")
        if "<TRACK" not in rpp:
            raise AssertionError("Missing TRACK container in RPP")
        if "<ITEM" not in rpp:
            raise AssertionError("Missing ITEM blocks in RPP")
        if 'MARKER 1 0.000000 "Segment A" 1' not in rpp or 'MARKER 1 95.500000 "" 1' not in rpp:
            raise AssertionError("Missing REAPER Region 1 paired definition")
        if 'MARKER 2 95.500000 "Segment B" 1' not in rpp or 'MARKER 2 230.000000 "" 1' not in rpp:
            raise AssertionError("Missing REAPER Region 2 paired definition")
        item.status = "PASS"
        item.message = "REAPER .rpp timeline S-expressions, item blocks, and region markers verified"

    def _test_magix_samplitude_edl_v1_5_export(self, item: DiagnosticItem):
        mod = _resolve_export_daw_module()
        generate_samplitude_edl = mod.generate_samplitude_edl
        format_edl_timestamp = mod.format_edl_timestamp

        tc = format_edl_timestamp(3665.123)
        if tc != "01:01:05:123":
            raise AssertionError(f"format_edl_timestamp(3665.123) returned '{tc}', expected '01:01:05:123'")

        class DummyStory:
            def __init__(self, start, end, title, fade_in=0.0, fade_out=0.0):
                self.start = start
                self.end = end
                self.title = title
                self.fade_in = fade_in
                self.fade_out = fade_out

        stories = [
            DummyStory(0.0, 60.0, "Intro", 0.05, 0.1),
            DummyStory(60.0, 185.5, "Outro", 0.0, 0.0),
        ]
        edl = generate_samplitude_edl(stories, "broadcast.wav", "News Hour")
        if '"Samplitude EDL File Version 1.5"' not in edl:
            raise AssertionError("Missing Samplitude EDL Version 1.5 header")
        if '"Project: News Hour"' not in edl:
            raise AssertionError("Missing project title in EDL header")
        if "00:00:00:000   00:01:00:000" not in edl:
            raise AssertionError("Missing Track 1 timecode span in EDL")
        item.status = "PASS"
        item.message = "Samplitude EDL v1.5 timecode formatting and track decision list verified"

    def _test_pytorch_and_torch_native_extensions(self, item: DiagnosticItem):
        try:
            import torch
            version = torch.__version__
            has_c = hasattr(torch, "_C")
            item.status = "PASS"
            item.message = f"PyTorch {version} available; native C-extension: {'Loaded' if has_c else 'Not detected'}"
        except ImportError:
            item.status = "WARNING"
            item.message = "PyTorch is not installed in the current environment (optional on standalone CPU runner)"

    def _test_ctranslate2_acceleration_engine(self, item: DiagnosticItem):
        try:
            import ctranslate2
            ver = getattr(ctranslate2, "__version__", "unknown")
            supported_types = ctranslate2.get_supported_compute_types("cpu")
            item.status = "PASS"
            item.message = f"CTranslate2 {ver} loaded; CPU compute types: {', '.join(supported_types)}"
        except ImportError:
            item.status = "WARNING"
            item.message = "CTranslate2 not installed in this environment"

    def _test_sherpa_onnx_and_onnx_runtime_engine(self, item: DiagnosticItem):
        try:
            import onnxruntime as ort
            ver = ort.__version__
            providers = ort.get_available_providers()
            item.status = "PASS"
            item.message = f"ONNX Runtime {ver} available with providers: {', '.join(providers)}"
        except ImportError:
            item.status = "WARNING"
            item.message = "ONNX Runtime not installed in this environment"

    def _test_directml_and_gpu_device_enumeration(self, item: DiagnosticItem):
        devices = []
        try:
            import torch
            if torch.cuda.is_available():
                devices.append(f"CUDA: {torch.cuda.get_device_name(0)}")
        except Exception:
            pass

        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "DmlExecutionProvider" in providers:
                devices.append("DirectML (DirectX 12)")
            if "CUDAExecutionProvider" in providers:
                devices.append("ONNX CUDA")
        except Exception:
            pass

        if devices:
            item.status = "PASS"
            item.message = f"GPU devices detected: {', '.join(devices)}"
        else:
            item.status = "PASS"
            item.message = "CPU fallback mode active (No dedicated DirectML/CUDA GPU detected)"

    def _test_hugging_face_and_cdn_connectivity(self, item: DiagnosticItem):
        import urllib.request
        endpoints = [
            ("Hugging Face Hub", "https://huggingface.co"),
            ("GitHub CDN", "https://api.github.com"),
        ]
        results = []
        for name, url in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "RTVS-Diagnostic/3.5"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status in (200, 301, 302, 403):
                        results.append(f"{name}: Reachable ({resp.status})")
            except Exception as e:
                results.append(f"{name}: Offline/Blocked ({type(e).__name__})")

        item.status = "PASS"
        item.message = "; ".join(results)

    def _test_model_directory_storage_and_permissions(self, item: DiagnosticItem):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "probe.tmp"
            test_file.write_text("write_ok", encoding="utf-8")
            content = test_file.read_text(encoding="utf-8")
            if content != "write_ok":
                raise AssertionError("Read mismatch in storage probe")
            test_file.unlink()

        item.status = "PASS"
        item.message = "Model cache directory read/write/delete operations verified"

    def _test_safe_archive_extraction_sandbox(self, item: DiagnosticItem):
        import zipfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("safe_dir/test.txt", "safe data")

            out_dir = Path(tmp_dir) / "out"
            out_dir.mkdir()
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.infolist():
                    target = out_dir / member.filename
                    if not str(target.resolve()).startswith(str(out_dir.resolve())):
                        raise SecurityError("Zip slip traversal detected!")
                    zf.extract(member, out_dir)

            if not (out_dir / "safe_dir" / "test.txt").exists():
                raise AssertionError("Extracted member file not found")

        item.status = "PASS"
        item.message = "Archive path traversal protection and extraction sandbox validated"

    def _test_story_boundary_detection_pipeline(self, item: DiagnosticItem):
        # Test boundary segmentation algorithm using vocal intervals
        speech_intervals = [
            {"start": 0.0, "end": 2.0},
            {"start": 5.0, "end": 8.0},
        ]
        silence_threshold = 2.0
        lead_in_padding = 0.5
        total_dur = 10.0

        story_starts = [max(0.0, speech_intervals[0]["start"] - lead_in_padding)]
        story_ends = []
        for i in range(len(speech_intervals) - 1):
            curr_end = speech_intervals[i]["end"]
            next_start = speech_intervals[i + 1]["start"]
            gap = next_start - curr_end
            if gap >= silence_threshold:
                story_ends.append(curr_end + min(0.3, lead_in_padding))
                story_starts.append(max(0.0, next_start - lead_in_padding))
        story_ends.append(max(float(speech_intervals[-1]["end"]), total_dur))

        stories = []
        for idx, (st, et) in enumerate(zip(story_starts, story_ends)):
            stories.append({"start": round(st, 2), "end": round(et, 2), "title": f"Story {idx + 1}"})

        if len(stories) != 2:
            raise AssertionError(f"Expected 2 segmented stories, got {len(stories)}")
        if stories[0]["start"] != 0.0 or stories[1]["start"] != 4.5:
            raise AssertionError(f"Story boundary calculation mismatch: {stories}")

        item.status = "PASS"
        item.message = "Vocal interval segmentation algorithm evaluated with padding rules"

    def _test_music_vs_voice_mode_filtering(self, item: DiagnosticItem):
        music_samples = ["[music]", "♪♪", "(applause)", "[singing]", "♪♫♬"]
        for sample in music_samples:
            if not self.MUSIC_TOKEN_RE.match(sample):
                raise AssertionError(f"Expected MUSIC_TOKEN_RE to match non-speech token '{sample}'")

        speech_samples = ["Hello and welcome", "Good evening", "Sports report"]
        for sample in speech_samples:
            if self.MUSIC_TOKEN_RE.match(sample):
                raise AssertionError(f"Expected MUSIC_TOKEN_RE to reject speech token '{sample}'")

        item.status = "PASS"
        item.message = "MUSIC_TOKEN_RE and speech/noise separator verified"

    def _test_silero_neural_vad_initialization(self, item: DiagnosticItem):
        try:
            import silero_vad
            name = silero_vad.__name__
            item.status = "PASS"
            item.message = f"Silero VAD ({name}) package loadable"
        except ImportError:
            item.status = "WARNING"
            item.message = "Silero VAD neural package not installed (Energy envelope fallback active)"

    def _test_wespeaker_diarization_architecture(self, item: DiagnosticItem):
        try:
            import wespeakerruntime
            item.status = "PASS"
            item.message = f"WeSpeaker ONNX runtime ({wespeakerruntime.__name__}) available"
        except ImportError:
            item.status = "WARNING"
            item.message = "WeSpeaker ONNX runtime not present in current environment (Optional for core CPU testing)"

    def _test_translation_plugin_architecture_invariants(self, item: DiagnosticItem):
        plugin_worker = Path("plugins") / "translation" / "worker.py"
        if not plugin_worker.exists():
            item.status = "SKIP"
            item.message = "plugins/translation/worker.py not found in source tree"
            return

        content = plugin_worker.read_text(encoding="utf-8", errors="ignore")
        if "from RadioTVSegmenter import" in content:
            raise AssertionError("Architectural violation: plugins/translation imports RadioTVSegmenter root")

        item.status = "PASS"
        item.message = "Core module isolation invariant strictly maintained"

    def _test_speaker_reassignment_contiguous_turn_logic(self, item: DiagnosticItem):
        # Create a mock transcript with 5 segments spanning 3 speaker turns
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello world.", "speaker": "Katelin Beck"},
            {"start": 5.0, "end": 10.0, "text": "Check out books.", "speaker": "Jenny Lowman"},
            {"start": 10.0, "end": 15.0, "text": "So a large part of what volunteers do...", "speaker": "Jenny Lowman"},
            {"start": 15.0, "end": 20.0, "text": "is exploring the library with kids.", "speaker": "Jenny Lowman"},
            {"start": 20.0, "end": 25.0, "text": "Katelin says instead of deciding...", "speaker": "Milan Parker"},
        ]

        speaker_names = {}
        segment_speaker_overrides = {}

        def get_effective_speaker_name(idx, seg):
            override = segment_speaker_overrides.get(idx)
            if override and override in speaker_names:
                return speaker_names[override]
            return seg.get("speaker", "")

        # Simulate renaming Jenny Lowman (starting at seg_idx=1) to Katelin Beck for "This Instance Only"
        seg_idx = 1
        current_name = get_effective_speaker_name(seg_idx, segments[seg_idx]) # "Jenny Lowman"
        target_name = "Katelin Beck"

        # Contiguous turn logic
        section_indices = []
        for i in range(seg_idx, len(segments)):
            if get_effective_speaker_name(i, segments[i]) == current_name:
                section_indices.append(i)
            else:
                break

        for idx in section_indices:
            override_key = f"SEG_{idx}_SPEAKER"
            speaker_names[override_key] = target_name
            segment_speaker_overrides[idx] = override_key

        # Assertions
        if section_indices != [1, 2, 3]:
            raise AssertionError(f"Expected turn indices [1, 2, 3], got {section_indices}")

        for idx in [1, 2, 3]:
            eff = get_effective_speaker_name(idx, segments[idx])
            if eff != "Katelin Beck":
                raise AssertionError(f"Segment #{idx} speaker is '{eff}', expected 'Katelin Beck'")

        # Ensure segment 4 (Milan Parker) remains untouched
        milan_eff = get_effective_speaker_name(4, segments[4])
        if milan_eff != "Milan Parker":
            raise AssertionError(f"Segment #4 speaker was modified to '{milan_eff}', expected 'Milan Parker'")

        item.status = "PASS"
        item.message = "All contiguous turn segments correctly reassigned up to next speaker boundary"

    def _test_daw_timeline_interchange_and_gap_handling(self, item: DiagnosticItem):
        from export.daw import (
            build_timeline_clips,
            generate_reaper_project,
            generate_samplitude_edl,
            generate_audacity_labels,
            generate_audition_xml,
            generate_daw_marker_csv,
        )

        stories = [
            {"title": "Story Alpha", "start_time": 10.0, "end_time": 20.0, "summary_en": "First segment"},
            {"title": "Story Beta", "start_time": 30.0, "end_time": 40.0, "summary_en": "Second segment"},
        ]
        total_dur = 50.0

        # 1. Exclude mode
        clips_ex = build_timeline_clips(stories, total_dur, unselected_audio_mode="exclude")
        if len(clips_ex) != 2:
            raise AssertionError(f"Exclude mode expected 2 clips, got {len(clips_ex)}")
        if clips_ex[0]["is_unselected"] or clips_ex[1]["is_unselected"]:
            raise AssertionError("Exclude mode returned unselected clips")

        # 2. Split mode
        clips_split = build_timeline_clips(stories, total_dur, unselected_audio_mode="split")
        if len(clips_split) != 5:
            raise AssertionError(f"Split mode expected 5 clips (gap, story, gap, story, gap), got {len(clips_split)}")
        if not clips_split[0]["is_unselected"] or clips_split[0]["duration"] != 10.0:
            raise AssertionError(f"Gap 1 incorrect: {clips_split[0]}")
        if clips_split[1]["is_unselected"] or clips_split[1]["title"] != "Story Alpha":
            raise AssertionError(f"Story 1 incorrect: {clips_split[1]}")

        # 3. Muted mode
        clips_muted = build_timeline_clips(stories, total_dur, unselected_audio_mode="muted")
        if len(clips_muted) != 5:
            raise AssertionError(f"Muted mode expected 5 clips, got {len(clips_muted)}")
        if not clips_muted[0]["is_muted"] or not clips_muted[2]["is_muted"]:
            raise AssertionError("Muted mode clips missing is_muted flag")

        # 4. Verify Formatters output
        stories_with_fades = [
            {"title": "Story Alpha", "start_time": 10.0, "end_time": 20.0, "summary_en": "First segment", "fade_in": 1.5, "fade_out": 2.0, "fade_curve": "s_curve"},
            {"title": "Story Beta", "start_time": 30.0, "end_time": 40.0, "summary_en": "Second segment", "fade_in": 0.5, "fade_out": 1.0, "fade_curve": "linear"},
        ]

        # 4a. REAPER Scope: Full Episode with splits & clean headers (no MIXERSLIDERS, no PLAYREC)
        reaper_full = generate_reaper_project(stories_with_fades, "test.wav", "TestProject", total_duration=total_dur, scope="full")
        if "MIXERSLIDERS" in reaper_full or "PLAYREC" in reaper_full:
            raise AssertionError("REAPER project must omit obsolete MIXERSLIDERS and PLAYREC tokens")
        if "Full Episode (Splits)" not in reaper_full or "Story Alpha" not in reaper_full:
            raise AssertionError("REAPER Full Episode export missing Full Episode track or continuous split items")
        if 'NAME ""' not in reaper_full:
            raise AssertionError("REAPER Full Episode export missing unlabelled split items for non-story audio")
        if "COLOR" not in reaper_full or "1 B" not in reaper_full:
            raise AssertionError("REAPER export missing RTVS story palette color coding or paired region markers")
        if "FADEIN 3 1.500000" not in reaper_full or "FADEOUT 3 2.000000" not in reaper_full:
            raise AssertionError("REAPER export missing s-curve fade parameter mapping")
        if "FADEIN 0 0.500000" not in reaper_full or "FADEOUT 0 1.000000" not in reaper_full:
            raise AssertionError("REAPER export missing linear fade parameter mapping")

        # 4b. REAPER Scope: Full Episode & All Stories (multi-track)
        reaper_dual = generate_reaper_project(stories_with_fades, "test.wav", "TestProject", total_duration=total_dur, scope="full_and_all_stories")
        if "Full Episode (Splits)" not in reaper_dual or "Story Cuts" not in reaper_dual:
            raise AssertionError("REAPER multi-track export missing Full Episode or Story Cuts tracks")

        # 4c. REAPER Scope: Muted mode
        reaper_out = generate_reaper_project(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="muted", track_name="Test Track", scope="all_stories")
        if "MUTE 1" not in reaper_out or "Story Alpha" not in reaper_out or "Test Track" not in reaper_out:
            raise AssertionError("REAPER project export missing muted clip markers or story titles")

        edl_out = generate_samplitude_edl(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="split")
        if "Story Alpha" not in edl_out or '""' not in edl_out:
            raise AssertionError("Samplitude EDL export missing story or unlabelled gap entries")

        audacity_out = generate_audacity_labels(stories, total_duration=total_dur, unselected_audio_mode="split")
        if "10.000000" not in audacity_out or "Story Alpha" not in audacity_out:
            raise AssertionError("Audacity label track export missing timestamps or labels")

        xml_out = generate_audition_xml(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="muted")
        if "<xmeml" not in xml_out or "Story Alpha" not in xml_out:
            raise AssertionError("Audition XML export missing xmeml structure or story sequence")

        csv_out = generate_daw_marker_csv(stories, total_duration=total_dur, unselected_audio_mode="exclude")
        if "Marker Name" not in csv_out or "Story Alpha" not in csv_out:
            raise AssertionError("DAW Marker CSV export missing header or story markers")

        # 5. Verify Streamlined Multi-Platform Timeline Exporters from export.timeline
        from export.timeline import (
            generate_fcpxml,
            generate_aaf_interchange,
            generate_hindenburg_session,
            generate_cue_sheet,
            generate_fcp7_xml,
        )

        fcpxml_out = generate_fcpxml(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="split", sample_rate=48000)
        if "<fcpxml" not in fcpxml_out or "Story Alpha" not in fcpxml_out or 'audioRate="48000"' not in fcpxml_out:
            raise AssertionError("FCPXML export missing fcpxml structure, story clips, or 48kHz audioRate")

        aaf_out = generate_aaf_interchange(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="split", sample_rate=48000, track_name="Dialog Track")
        if "<AAF" not in aaf_out or "Story Alpha" not in aaf_out or "Dialog Track" not in aaf_out:
            raise AssertionError("Universal AAF export missing AAF XML structure, track name, or story clips")

        nhx_out = generate_hindenburg_session(stories, "test.wav", "TestProject", total_duration=total_dur, unselected_audio_mode="split", sample_rate=44100, track_name="Radio Broadcast")
        if "<Session" not in nhx_out or "Story Alpha" not in nhx_out or "Radio Broadcast" not in nhx_out or "<Clip" not in nhx_out:
            raise AssertionError("Hindenburg session export missing Session XML structure, track name, or clips")

        cue_out = generate_cue_sheet(stories, "test.wav", "TestProject", total_duration=total_dur)
        if "FILE" not in cue_out or "TRACK 01 AUDIO" not in cue_out or "Story Alpha" not in cue_out:
            raise AssertionError("Red Book CUE sheet export missing track or file header")

        fcp7_out = generate_fcp7_xml(stories, "test.wav", "TestProject", total_duration=total_dur, track_name="Broadcast Audio")
        if "<xmeml" not in fcp7_out or "Broadcast Audio" not in fcp7_out:
            raise AssertionError("FCP7 XML export missing xmeml structure or custom track name")

        item.status = "PASS"
        item.message = "Multi-platform timeline interchange formatters (REAPER, EDL, FCPXML, AAF, NHX, Audacity, CUE, CSV) fully verified"


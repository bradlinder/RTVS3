#!/usr/bin/env python3
"""Radio & TV Story Segmenter — Test Runner & Diagnostic Test Bench.

Executes zero-dependency automated unit and integration tests, hardware checks,
and AI model validation for transcription, diarization, translation, and story detection.

Can be run:
  1. Headless CLI mode: python test_runner.py [--verbose] [--all]
  2. Standalone PySide6 GUI Dialog: python test_runner.py --gui
  3. Integrated inside RadioTVSegmenter: Help -> Run Diagnostic Test Bench...
  4. Bundled Windows executable: RadioTVSegmenter.exe --run-diagnostics
"""

from __future__ import annotations

import io
import json
import math
import os
os.environ["RTVS_TEST_MODE"] = "1"
import re
import shutil
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Headless PySide6 Fallback Engine (Centralized in qt_compat.py)
# ---------------------------------------------------------------------------

_ROOT_DIR = str(Path(__file__).resolve().parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from qt_compat import _ensure_pyside6_fallback

_ensure_pyside6_fallback()


from diagnostic_helpers import (
    generate_synthetic_wav,
    DiagnosticItem,
    _resolve_export_subtitles_module,
    _resolve_export_daw_module,
)
from diagnostic_core_tests import DiagnosticCoreTestsMixin
from diagnostic_export_tests import DiagnosticExportTestsMixin
from diagnostic_batch_tests import DiagnosticBatchTestsMixin
from diagnostic_cloud_and_system_tests import DiagnosticCloudAndSystemTestsMixin
from diagnostic_loudness_tests import DiagnosticLoudnessTestsMixin


# ---------------------------------------------------------------------------
# Core Diagnostic Test Bench Engine
# ---------------------------------------------------------------------------

class DiagnosticEngine(
    DiagnosticCoreTestsMixin,
    DiagnosticExportTestsMixin,
    DiagnosticBatchTestsMixin,
    DiagnosticCloudAndSystemTestsMixin,
    DiagnosticLoudnessTestsMixin,
):
    """Executes tests across Core File Formats, Subtitle Generators, AI Runtimes,
    and Download Pipelines with optional progress reporting.
    """

    CATEGORIES = [
        "Core Logic & File I/O",
        "Subtitles & Export Formats",
        "AI Runtimes & Inference Stack",
        "Model Download & Provisioning",
        "Story & Boundary Detection",
        "Audio Diarization & VAD",
        "Translation & Bilingual Engine",
        "Transcript & Speaker Management",
        "Export & Packaging Engines",
        "Timeline & Audio Performance",
        "Plugin Architecture & Sandboxing",
    ]

    MUSIC_TOKEN_RE = re.compile(
        r"^([♪♫♬\s]+|\[(?:music|applause|laughter|cheering|sound|singing|theme)\]|\((?:music|applause|laughter|singing)\))$",
        re.IGNORECASE
    )

    def __init__(
        self,
        on_update_callback: Optional[Callable[[DiagnosticItem], None]] = None,
        include_dev_tests: Optional[bool] = None,
    ):
        self.on_update = on_update_callback
        if include_dev_tests is None:
            is_frozen = getattr(sys, "frozen", False)
            has_dev_flag = (
                os.environ.get("RTVS_DEV_MODE") == "1"
                or "--developer-mode" in sys.argv
                or "--dev" in sys.argv
                or "--all" in sys.argv
            )
            self.include_dev_tests = (not is_frozen) or has_dev_flag
        else:
            self.include_dev_tests = include_dev_tests

        self.items: List[DiagnosticItem] = []
        self._init_item_registry()
        if not self.include_dev_tests:
            self.items = [it for it in self.items if not it.dev_only]

    def _init_item_registry(self):
        self.items = [
            # 1. Core Logic & File I/O
            DiagnosticItem(
                "Time Parsing & Formatting",
                "Core Logic & File I/O",
                "Fuzz tests format_time() and parse_time() against boundaries (0.0s, 65.0s, 3665.0s, and precision formats)",
            ),
            DiagnosticItem(
                "Project Serialization Round-Trip",
                "Core Logic & File I/O",
                "Tests saving and restoring project dictionaries (.rtvs JSON) preserving word timestamps and story metadata",
            ),
            DiagnosticItem(
                "Waveform Peak Cache Generator",
                "Core Logic & File I/O",
                "Generates binary waveform peak cache (.peaks) from synthetic audio and validates format header",
            ),
            DiagnosticItem(
                "Process Lifecycle & Subprocess Lock",
                "Core Logic & File I/O",
                "Verifies _SUBPROCESS_LOCK and register_process / kill_all_subprocesses teardown safety",
            ),

            # 2. Subtitles & Export Formats
            DiagnosticItem(
                "SubRip (.srt) Timestamp Formatting",
                "Subtitles & Export Formats",
                "Validates format_srt_timestamp() millisecond rounding and sequence ordering",
            ),
            DiagnosticItem(
                "WebVTT (.vtt) Formatting",
                "Subtitles & Export Formats",
                "Validates format_vtt_timestamp() header markers and cue periods",
            ),
            DiagnosticItem(
                "Red Book CUE Sheet Generation",
                "Subtitles & Export Formats",
                "Validates generate_cue_sheet() 75 fps frame calculation and track index formatting",
            ),
            DiagnosticItem(
                "YouTube Chapter Markers",
                "Subtitles & Export Formats",
                "Validates generate_youtube_chapters() zero-start enforcement and time alignment",
            ),
            DiagnosticItem(
                "Cockos REAPER Project (.rpp) Generator",
                "Subtitles & Export Formats",
                "Validates generate_reaper_project() track S-expressions, item bounds, fades, and regions",
            ),
            DiagnosticItem(
                "Magix Samplitude EDL (v1.5) Export",
                "Subtitles & Export Formats",
                "Validates generate_samplitude_edl() header structure, timecode parsing, and track entries",
            ),

            # 3. AI Runtimes & Inference Stack
            DiagnosticItem(
                "PyTorch & Torch Native Extensions",
                "AI Runtimes & Inference Stack",
                "Checks PyTorch version, _C C-extension loadability, and TorchScript runtime availability",
            ),
            DiagnosticItem(
                "CTranslate2 Acceleration Engine",
                "AI Runtimes & Inference Stack",
                "Verifies CTranslate2 library presence and CPU/GPU compute types",
            ),
            DiagnosticItem(
                "Sherpa-ONNX & ONNX Runtime Engine",
                "AI Runtimes & Inference Stack",
                "Validates ONNX Runtime and Sherpa-ONNX execution providers",
            ),
            DiagnosticItem(
                "DirectML & GPU Device Enumeration",
                "AI Runtimes & Inference Stack",
                "Detects DirectX DirectML / NVIDIA CUDA acceleration devices on current host",
            ),

            # 4. Model Download & Provisioning
            DiagnosticItem(
                "Hugging Face & CDN Connectivity",
                "Model Download & Provisioning",
                "Verifies network connectivity to Hugging Face, GitHub CDN, and download mirror endpoints",
            ),
            DiagnosticItem(
                "Model Directory Storage & Permissions",
                "Model Download & Provisioning",
                "Validates read/write/delete permissions across default and custom model storage directories",
            ),
            DiagnosticItem(
                "Safe Archive Extraction Sandbox",
                "Model Download & Provisioning",
                "Tests zip/tar extraction safety against malicious path-traversal slips and corrupted archives",
            ),

            # 5. Story & Boundary Detection
            DiagnosticItem(
                "Story Boundary Detection Pipeline",
                "Story & Boundary Detection",
                "Tests vocal and acoustic energy boundary detector against synthetic segmented speech",
            ),
            DiagnosticItem(
                "Music vs. Voice Mode Filtering",
                "Story & Boundary Detection",
                "Tests MUSIC_TOKEN_RE filtering of non-speech tokens and transcript cue stripping",
            ),

            # 6. Audio Diarization & VAD
            DiagnosticItem(
                "Silero Neural VAD Initialization",
                "Audio Diarization & VAD",
                "Checks Silero VAD model presence and speech timestamp evaluation",
            ),
            DiagnosticItem(
                "WeSpeaker Diarization Architecture",
                "Audio Diarization & VAD",
                "Verifies WeSpeaker ONNX embedding engine and speaker clustering imports",
            ),
            DiagnosticItem(
                "Translation Plugin Architecture Invariants",
                "Audio Diarization & VAD",
                "Verifies that translation modules remain cleanly isolated inside plugins/translation",
            ),
            DiagnosticItem(
                "Speaker Reassignment Contiguous Turn Logic",
                "Transcript & Speaker Management",
                "Verifies that reassigning a speaker label applies across all contiguous turn segments until the next speaker change",
            ),
            DiagnosticItem(
                "DAW Timeline Interchange and Gap Handling",
                "Export & Packaging Engines",
                "Validates multi-format DAW timeline clip generation, gap detection, split and muted unselected audio modes across REAPER, Samplitude EDL, Audacity, Audition XML, and CSV",
            ),
            DiagnosticItem(
                "WordPress Export Scope Post Builder",
                "Subtitles & Export Formats",
                "Validates WordPress export post items rebuilding across selected stories, all stories, full episode, and full episode + all stories scope modes",
            ),
            DiagnosticItem(
                "WordPress Export Content & Transcript Formatter",
                "Subtitles & Export Formats",
                "Validates WordPress upload post content generation, dict transcript extraction, range filtering, Spanish translation integration, and robust media guid resolution",
            ),
            DiagnosticItem(
                "Multi-Format Line Break & Paragraph Parity",
                "Subtitles & Export Formats",
                "Validates line break frequency and paragraph structure consistency between in-app transcript view and export formats (WordPress, DOCX, TXT, Subtitles)",
            ),
            DiagnosticItem(
                "WordPress Multi-Story Upload & UI Pluralization",
                "Subtitles & Export Formats",
                "Validates multi-story export upload execution loop and dynamic export button label pluralization ('Export to WordPress Draft' vs 'Export to WordPress Drafts...')",
            ),
            DiagnosticItem(
                "Gutenberg HTML Structural Hygiene Audit",
                "Subtitles & Export Formats",
                "Validates balanced <!-- wp:paragraph --> and <!-- wp:audio --> comment blocks, escaping, and no double-nested paragraph tags",
            ),
            DiagnosticItem(
                "Export Scope Delta & Gap Integrity Audit",
                "Export & Packaging Engines",
                "Validates transcript slice extraction and speaker block grouping across unselected timeline gaps and multi-story boundaries",
            ),
            DiagnosticItem(
                "Export Destination Interface Contract Verification",
                "Plugin Architecture & Sandboxing",
                "Audits all export destination plugins to verify they inherit ExportDestination and satisfy required contract properties",
            ),
            DiagnosticItem(
                "Multi-Story Media Payload Disambiguation Test",
                "Subtitles & Export Formats",
                "Validates unique audio/video file naming across concurrent story uploads to prevent media library overwrites",
            ),
            DiagnosticItem(
                "WordPress Audio Inclusion Toggle & Error Resilience",
                "Subtitles & Export Formats",
                "Validates WordPress text/image-only export mode with audio omitted, audio player inclusion, and multi-story upload error isolation",
            ),
            DiagnosticItem(
                "Multi-Scope Story and Full Episode Export Pipeline",
                "Export & Packaging Engines",
                "Validates end-to-end file generation across Full Episode, Selected Stories, and All Stories across TXT, DOCX, and PDF formats",
            ),
            DiagnosticItem(
                "Audio Export Non-Blocking and Cancellation Pipeline",
                "Export & Packaging Engines",
                "Validates export_audio_track and extract_audio_clip non-blocking polling, process registry tracking, and cancel_check user abortion handling",
            ),
            DiagnosticItem(
                "Modal Dialog Maximizable Import Integrity",
                "UI & Application Lifecycle",
                "Validates make_dialog_maximizable imports and execution across batch processing, export, id3, preferences, and project dialogs",
            ),
            DiagnosticItem(
                "Batch Unified Transcripts Directory Export",
                "Export & Packaging Engines",
                "Validates batch processing unified transcripts directory routing, Projects/ session file isolation, and skip-existing check",
            ),
            DiagnosticItem(
                "Batch Drag and Drop Ingestion and Event Handling",
                "UI & Application Lifecycle",
                "Validates drag-and-drop file/folder ingestion, MIME extraction, duplicate deduplication, and dialog-wide drop event filtering in batch processing",
            ),
            DiagnosticItem(
                "Unified Export Destinations and YouTube Auth Integrity",
                "Export & Packaging Engines",
                "Validates YouTube and Google Docs auth manager email methods, export destination error guards, and WordPress story panel clean separation",
            ),
            DiagnosticItem(
                "PDF Transcript Export and Bold Speaker Labels",
                "Export & Packaging Engines",
                "Validates lightweight vector PDF transcript generator, bold speaker labels (/F2), timestamps, comments, highlights, and multiline wrapping",
            ),
            DiagnosticItem(
                "Fade Curve Tables and Auditioning State",
                "Timeline & Audio Performance",
                "Validates precomputed fade curve lookup tables, monotonicity, boundary conditions, and dialog state rollback semantics",
            ),
            # Milestone 4 Coverage Extension
            DiagnosticItem(
                "Translation Routing & Key Priority Unit Test",
                "Translation & Bilingual Engine",
                "Asserts source_language_code() detects correct language and get_spanish_translation_item() selects correct translation keys",
            ),
            DiagnosticItem(
                "Symmetrical Translation Editing State Test",
                "Translation & Bilingual Engine",
                "Validates editing translation segments updates core dictionary and mark_stale_translations() marks stale states",
            ),
            DiagnosticItem(
                "Interactive Change Speaker Dialogue Flow Test",
                "Transcript & Speaker Management",
                "Validates all speaker rename choices (all, single contiguous turn, subsequent, cancel) without desynchronizing segment state",
            ),
            DiagnosticItem(
                "Story Boundary Validation & Overlap Test",
                "Story & Boundary Detection",
                "Asserts non-overlapping constraints, boundary clamping, duration validation, and fade curve serialization across Story instances",
            ),
            DiagnosticItem(
                "Audio / Subtitle Sync Drift Test",
                "Subtitles & Export Formats",
                "Ensures SRT, WebVTT, YouTube chapters, and Red Book CUE markers maintain millisecond timestamp synchronization",
            ),
            DiagnosticItem(
                "Interactive Transcript Editing & Split/Join Unit Tests",
                "Transcript & Speaker Management",
                "Validates segment splitting with/without word timestamps, proportional interpolation, segment merging, and speaker override index shifting",
            ),
            DiagnosticItem(
                "Exporter Structure Invariant Tests",
                "Export & Packaging Engines",
                "Validates structural syntax trees and well-formedness for REAPER .rpp, Samplitude .edl, and Audition/FCP XML",
            ),
            DiagnosticItem(
                "Plugin Interface Sandbox Testing",
                "Plugin Architecture & Sandboxing",
                "Validates plugin manifest schemas, base plugin lifecycle hooks, and Google Docs export payload serialization",
            ),
            DiagnosticItem(
                "Project File Integrity & Portable Path Resolution",
                "Core Logic & File I/O",
                "Validates structural error catching on malformed project data and tests relative/absolute portable media resolution",
            ),
            DiagnosticItem(
                "Google Docs Export Integrity",
                "Export & Packaging Engines",
                "Validates Google Docs export title fallback, enforced bold speaker styling, and optional H2 Table of Contents headers",
            ),
            DiagnosticItem(
                "Acoustic Voice Profile Matcher",
                "Audio Diarization & VAD",
                "Validates 256-dimensional WeSpeaker embedding vector persistence, cosine similarity scoring, threshold filtering, and re-clustering state integrity",
            ),
            DiagnosticItem(
                "Windows Detached Update Helper Architecture",
                "Core Logic & File I/O",
                "Validates detached update helper script generation, process exit polling semantics, elevated UAC execution fallback, and update logging",
            ),
            DiagnosticItem(
                "Google Docs OAuth and PKCE Security",
                "Plugin Architecture & Sandboxing",
                "Validates PKCE pair generation, cryptographic state tokens, zero-config public client credentials, and callback state verification",
            ),
            DiagnosticItem(
                "Temporary Cache Management and Storage Inspection",
                "Project & Filesystem Lifecycle",
                "Validates disk cache statistics calculation, preview inspection data, and temporary cache purging",
            ),
            DiagnosticItem(
                "YouTube Data API and Direct Video Upload Engine",
                "Subtitles & Export Formats",
                "Validates YouTube resumable upload chunking protocol, custom thumbnail submission, caption track insertion, and dual-mode publishing",
            ),
            DiagnosticItem(
                "Google Sheets Tabular Export and Formatting Engine",
                "Export & Packaging Engines",
                "Validates Google Sheets spreadsheet creation payloads, tabular rundown row conversion, speaker talk-time airtime analytics, and A1 range appending",
            ),
            DiagnosticItem(
                "Multiprocessing Freeze Support and Spawn Intercept",
                "Core Logic & File I/O",
                "Validates PyInstaller frozen process freeze_support initialization and macOS/Linux multiprocessing -c command dispatch",
            ),
            DiagnosticItem(
                "AI Worker Subprocess Execution and IPC Handshake",
                "AI Runtimes & Inference Stack",
                "Spawns the local AI worker executable in an external subprocess to validate execution permissions, dynamic library loading, and IPC handshake",
            ),
            DiagnosticItem(
                "Frozen Subprocess Multiprocessing Spawn Protocol",
                "AI Runtimes & Inference Stack",
                "Spawns the AI worker executable as a child process using Python multiprocessing -c syntax to verify resource tracker and spawn handler compatibility",
            ),
            DiagnosticItem(
                "Comprehensive Local and Cloud Backup and Restore Engine",
                "Core Logic & File I/O",
                "Validates unified state serialization (preferences, shortcuts, glossary, plugins), SHA-256 cryptographic verification, local archive roundtrip, and Google Drive cloud payload integrity",
            ),
            DiagnosticItem(
                "Option C Muted Silver Fog Light Theme and Dark Mode Clipboard Formatting",
                "Core Logic & File I/O",
                "Validates Option C muted low-contrast silver/fog palette and dark-mode clipboard rich styling (black plain text, blue speaker labels, highlight backgrounds and text)",
            ),
            DiagnosticItem(
                "Windows CI Build and Packaging Optimization Invariants",
                "CI & Packaging",
                "Validates Inno Setup LZMA2 multi-threading and compression parameters, PyInstaller Stage 3 dedicated worker wheel omission and PySide6 exclusion, and CI curl download resilience",
                dev_only=True,
            ),
            DiagnosticItem(
                "Roadmap N-1 Sliding Window and Status Integrity",
                "Release Engineering & Documentation",
                "Validates roadmap.txt N-1 sliding window retention, social digest status indicator compliance ([x], [-], [ ]), and synchronization with prs_shared.py PROJECT_VERSION via roadmap_manager",
                dev_only=True,
            ),
            # Milestone 3 & v3.9.0-beta.1 Verification
            DiagnosticItem(
                "Station Voice Profiles Store and Matching Engine",
                "Audio Diarization & VAD",
                "Validates StationVoiceProfileStore persistence, vector normalization, profile addition, matching logic, and JSON export/import",
            ),
            DiagnosticItem(
                "Multi-Tier Mipmapped Waveform Peak Cache Serialization",
                "Timeline & Audio Performance",
                "Validates Version 2 .peaks binary cache read/write with 4x/16x/64x LOD pyramid levels and transparent Version 1 upgrade",
            ),
            DiagnosticItem(
                "Speed-Listening Proofreading Rate and Context Controls",
                "Timeline & Audio Performance",
                "Validates playback speed rates (0.75x to 2.0x), WSOLA pitch preservation parameters, and proofreading pre-roll configuration",
            ),
            # Milestone 4 / Smart Hybrid Audio Normalization Suite
            DiagnosticItem(
                "Smart Hybrid Audio Loudness Probing",
                "Timeline & Audio Performance",
                "Validates fast multi-window EBU R128 loudness and peak probing across synthetic test media",
            ),
        ]

    def run_all(self, stop_requested_fn: Optional[Callable[[], bool]] = None) -> List[DiagnosticItem]:
        """Executes all diagnostics sequentially, updating status and duration."""
        for item in self.items:
            if stop_requested_fn and stop_requested_fn():
                item.status = "SKIP"
                item.message = "Cancelled by user"
                if self.on_update:
                    self.on_update(item)
                continue

            item.status = "RUNNING"
            item.message = "Running diagnostic test..."
            if self.on_update:
                self.on_update(item)

            start_t = time.perf_counter()
            try:
                self._dispatch_test(item)
            except Exception as exc:
                item.status = "FAIL"
                item.message = f"{type(exc).__name__}: {exc}"
                item.details = str(exc)
            finally:
                item.duration_sec = time.perf_counter() - start_t
                if self.on_update:
                    self.on_update(item)

        return self.items

    def _normalize_name(self, name: str) -> str:
        s = name.lower()
        s = s.replace("&", "and")
        for ch in [" ", "(", ")", ".", "-", "/"]:
            s = s.replace(ch, "_")
        while "__" in s:
            s = s.replace("__", "_")
        return s.strip("_")

    def _dispatch_test(self, item: DiagnosticItem):
        clean_name = self._normalize_name(item.name)
        method_name = f"_test_{clean_name}"
        handler = getattr(self, method_name, None)
        if handler:
            handler(item)
        else:
            item.status = "SKIP"
            item.message = f"Test handler '{method_name}' not implemented"

    # --- Test Implementations ---

def generate_diagnostic_report(engine: DiagnosticEngine) -> str:
    """Compiles a complete system, runtime, and diagnostic test report with root-cause analysis."""
    import platform
    import multiprocessing

    now = time.strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        "=" * 78,
        "RADIO & TV STORY SEGMENTER — SYSTEM & PIPELINE DIAGNOSTIC REPORT",
        "=" * 78,
        f"Generated:           {now}",
        f"Operating System:    {platform.system()} {platform.release()} ({platform.version()})",
        f"Platform Machine:    {platform.machine()} ({'Apple Silicon arm64' if platform.machine() == 'arm64' and platform.system() == 'Darwin' else 'Intel/AMD x86_64' if 'x86' in platform.machine() or 'amd64' in platform.machine().lower() else platform.machine()})",
        f"Python Version:      {platform.python_version()} ({platform.python_implementation()})",
        f"Executable Path:     {sys.executable}",
        f"PyInstaller Frozen:  {getattr(sys, 'frozen', False)}",
        f"Multiprocessing:     {multiprocessing.get_start_method(allow_none=True) or 'default'} (spawn mode on macOS/Windows)",
    ]

    models_dir = os.environ.get("PRS_MODELS_DIR", "")
    hf_home = os.environ.get("HF_HOME", "")
    lines.append(f"Models Directory:    {models_dir or 'Default Application Support / AppData'}")
    lines.append(f"HuggingFace Cache:   {hf_home or 'Default (~/.cache/huggingface)'}")

    try:
        worker_exe, worker_args = engine._resolve_worker_cmd()
        lines.append(f"Resolved AI Worker:  {worker_exe} {' '.join(worker_args)}".strip())
    except Exception as exc:
        lines.append(f"Resolved AI Worker:  [Resolution Error: {exc}]")

    lines.append("")
    lines.append("-" * 78)
    lines.append("DIAGNOSTIC TEST RESULTS")
    lines.append("-" * 78)

    passed = [it for it in engine.items if it.status == "PASS"]
    failed = [it for it in engine.items if it.status == "FAIL"]
    warnings = [it for it in engine.items if it.status == "WARNING"]
    skipped = [it for it in engine.items if it.status == "SKIP"]

    lines.append(f"Summary: {len(passed)} Passed, {len(failed)} Failed, {len(warnings)} Warnings, {len(skipped)} Skipped (Total: {len(engine.items)})")
    lines.append("")

    for it in engine.items:
        badge = f"[{it.status}]"
        lines.append(f"{badge:<10} {it.category} > {it.name}")
        lines.append(f"           Duration: {it.duration_sec:.3f}s")
        lines.append(f"           Message:  {it.message or it.description}")
        if it.details and it.details.strip() and it.details.strip() != (it.message or "").strip():
            for detail_line in it.details.strip().splitlines()[:10]:
                lines.append(f"           | {detail_line}")
        lines.append("")

    lines.append("-" * 78)
    lines.append("ACTIONABLE TROUBLESHOOTING & RECOMMENDATIONS")
    lines.append("-" * 78)

    if not failed and not warnings:
        lines.append("✓ All core file formats, AI runtime frameworks, out-of-process worker spawns,")
        lines.append("  and export engines are fully operational. No issues detected.")
    else:
        for it in failed + warnings:
            lines.append(f"• [{it.status}] {it.name}:")
            lines.append(f"  Issue: {it.message}")
            if "Multiprocessing" in it.name or "Spawn" in it.name:
                lines.append("  Root Cause: Python multiprocessing on macOS/POSIX spawned a child process via -c.")
                lines.append("  Solution: Ensure freeze_support() and -c handling are active at top of entry points.")
            elif "Worker Subprocess" in it.name or "IPC" in it.name:
                lines.append("  Root Cause: Background AI worker executable failed to launch or communicate.")
                lines.append("  Solution: Check file execution permissions (chmod +x prs_worker on macOS),")
                lines.append("            verify required shared dynamic libraries, or inspect captured stderr above.")
            elif "Model" in it.name or "Storage" in it.name:
                lines.append("  Root Cause: AI model storage directory permissions or disk space issue.")
                lines.append("  Solution: Check write permissions on the models folder in Settings > Preferences.")
            else:
                lines.append("  Troubleshooting: Review detailed traceback and logs above.")
            lines.append("")

    lines.append("=" * 78)
    return "\n".join(lines)






# ---------------------------------------------------------------------------
# Standalone PySide6 Graphical Test Bench Dialog
# ---------------------------------------------------------------------------

def create_diagnostic_dialog(parent=None, include_dev_tests: Optional[bool] = None):
    """Builds the Diagnostic Test Bench Qt Dialog."""
    from PySide6.QtCore import Qt, QThread, Signal, QObject
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTreeWidget, QTreeWidgetItem, QProgressBar, QTextEdit,
        QHeaderView, QMessageBox, QFrame
    )
    from PySide6.QtGui import QColor, QFont, QIcon

    class TestRunnerWorker(QObject):
        item_updated = Signal(object)
        finished = Signal()

        def __init__(self, engine: DiagnosticEngine):
            super().__init__()
            self.engine = engine
            self._is_stopped = False

        def stop(self):
            self._is_stopped = True

        def run(self):
            self.engine.on_update = lambda it: self.item_updated.emit(it)
            self.engine.run_all(stop_requested_fn=lambda: self._is_stopped)
            self.finished.emit()

    class DiagnosticDialog(QDialog):
        def __init__(self, parent=None, include_dev_tests: Optional[bool] = None):
            super().__init__(parent)
            self.setWindowTitle("System Diagnostic Test Bench & Hardware Health")
            self.resize(880, 620)
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            self.engine = DiagnosticEngine(include_dev_tests=include_dev_tests)
            self.worker_thread: Optional[QThread] = None
            self.worker: Optional[TestRunnerWorker] = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Header Card
            header_layout = QVBoxLayout()
            title_lbl = QLabel("System Diagnostic Test Bench")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_lbl.setFont(title_font)
            header_layout.addWidget(title_lbl)

            subtitle_lbl = QLabel(
                "Executes comprehensive health checks across audio engines, subtitle formatters, "
                "AI runtime frameworks, model storage pipelines, and boundary detectors."
            )
            subtitle_lbl.setWordWrap(True)
            subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            header_layout.addWidget(subtitle_lbl)
            layout.addLayout(header_layout)

            # Progress Bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.engine.items))
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%v / %m Tests Completed")
            layout.addWidget(self.progress_bar)

            # Category / Test Tree
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Test Name", "Status", "Duration", "Result Summary"])
            self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            self.tree.setAlternatingRowColors(True)
            layout.addWidget(self.tree, 1)

            # Populate Tree Categories
            self.category_nodes: Dict[str, QTreeWidgetItem] = {}
            self.item_nodes: Dict[str, QTreeWidgetItem] = {}

            for cat in self.engine.CATEGORIES:
                cat_node = QTreeWidgetItem(self.tree, [cat, "", "", ""])
                f = cat_node.font(0)
                f.setBold(True)
                cat_node.setFont(0, f)
                cat_node.setExpanded(True)
                self.category_nodes[cat] = cat_node

            for it in self.engine.items:
                cat_node = self.category_nodes.get(it.category, self.tree.invisibleRootItem())
                node = QTreeWidgetItem(cat_node, [it.name, "Ready", "—", it.description])
                self.item_nodes[it.name] = node

            # Bottom Controls & Buttons
            bottom_layout = QHBoxLayout()

            self.status_lbl = QLabel("Ready to run diagnostics.")
            self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            bottom_layout.addWidget(self.status_lbl)
            bottom_layout.addStretch()

            self.run_btn = QPushButton("▶ Run All Diagnostics")
            self.run_btn.setMinimumHeight(32)
            self.run_btn.clicked.connect(self.start_diagnostics)
            bottom_layout.addWidget(self.run_btn)

            self.stop_btn = QPushButton("Stop")
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self.stop_diagnostics)
            bottom_layout.addWidget(self.stop_btn)

            self.export_btn = QPushButton("Copy Report")
            self.export_btn.clicked.connect(self.copy_report)
            bottom_layout.addWidget(self.export_btn)

            self.save_btn = QPushButton("Save Report to File...")
            self.save_btn.clicked.connect(self.save_report)
            bottom_layout.addWidget(self.save_btn)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.accept)
            bottom_layout.addWidget(self.close_btn)

            layout.addLayout(bottom_layout)

        def start_diagnostics(self):
            if self.worker_thread is not None:
                try:
                    if self.worker_thread.isRunning():
                        return
                except RuntimeError:
                    self.worker_thread = None

            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.status_lbl.setText("Running diagnostic tests...")

            # Reset tree display
            for it in self.engine.items:
                node = self.item_nodes.get(it.name)
                if node:
                    node.setText(1, "Pending")
                    node.setText(2, "—")
                    node.setForeground(1, QColor("#94a3b8"))

            self.worker_thread = QThread(self)
            self.worker = TestRunnerWorker(self.engine)
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.run)
            self.worker.item_updated.connect(self.on_item_updated)
            self.worker.finished.connect(self.on_diagnostics_finished)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()

        def stop_diagnostics(self):
            if self.worker is not None:
                try:
                    self.worker.stop()
                except RuntimeError:
                    self.worker = None
                self.status_lbl.setText("Stopping tests...")
                self.stop_btn.setEnabled(False)

        def on_item_updated(self, item: DiagnosticItem):
            node = self.item_nodes.get(item.name)
            if not node:
                return

            node.setText(0, item.name)
            node.setText(1, item.status)
            node.setText(2, f"{item.duration_sec:.2f}s" if item.duration_sec > 0 else "—")
            node.setText(3, item.message or item.description)

            # Status Colors
            if item.status == "PASS":
                node.setForeground(1, QColor("#10b981"))  # Green
            elif item.status == "FAIL":
                node.setForeground(1, QColor("#ef4444"))  # Red
            elif item.status == "WARNING":
                node.setForeground(1, QColor("#f59e0b"))  # Amber
            elif item.status == "RUNNING":
                node.setForeground(1, QColor("#38bdf8"))  # Cyan/Blue
            else:
                node.setForeground(1, QColor("#94a3b8"))  # Slate Gray

            # Update overall progress
            completed_count = sum(1 for it in self.engine.items if it.status in ("PASS", "FAIL", "WARNING", "SKIP"))
            self.progress_bar.setValue(completed_count)

        def on_diagnostics_finished(self):
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            passed = sum(1 for it in self.engine.items if it.status == "PASS")
            failed = sum(1 for it in self.engine.items if it.status == "FAIL")
            warn = sum(1 for it in self.engine.items if it.status == "WARNING")
            self.status_lbl.setText(f"Diagnostics complete: {passed} passed, {failed} failed, {warn} warnings.")
            self.worker = None
            self.worker_thread = None

        def copy_report(self):
            from PySide6.QtGui import QGuiApplication
            report_text = generate_diagnostic_report(self.engine)
            QGuiApplication.clipboard().setText(report_text)
            QMessageBox.information(
                self,
                "Report Copied",
                "The comprehensive system, pipeline, and diagnostic report has been copied to your clipboard.\n\n"
                "It includes host environment specifications, out-of-process worker status, and actionable troubleshooting guidance."
            )

        def save_report(self):
            from PySide6.QtWidgets import QFileDialog
            report_text = generate_diagnostic_report(self.engine)
            default_name = f"RTVS_Diagnostic_Report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Diagnostic Report",
                default_name,
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report_text)
                    QMessageBox.information(
                        self,
                        "Report Saved",
                        f"Diagnostic report successfully saved to:\n{file_path}"
                    )
                except Exception as exc:
                    QMessageBox.critical(
                        self,
                        "Error Saving Report",
                        f"Could not write diagnostic report to file:\n{exc}"
                    )

        def closeEvent(self, event):
            try:
                if self.worker_thread is not None:
                    is_running = False
                    try:
                        is_running = self.worker_thread.isRunning()
                    except RuntimeError:
                        is_running = False

                    if is_running:
                        if self.worker is not None:
                            try:
                                self.worker.stop()
                            except RuntimeError:
                                pass
                        self.worker_thread.quit()
                        self.worker_thread.wait(1000)
            except Exception:
                pass
            finally:
                self.worker = None
                self.worker_thread = None
                event.accept()

    return DiagnosticDialog(parent, include_dev_tests=include_dev_tests)


# ---------------------------------------------------------------------------
# CLI Test Runner Entrypoint
# ---------------------------------------------------------------------------

def run_cli_diagnostics(verbose: bool = True, include_dev_tests: Optional[bool] = None) -> int:
    """Executes the diagnostic engine in headless console mode with human-readable output."""
    print("=" * 65)
    print(" Radio & TV Story Segmenter — System Diagnostic Test Bench")
    print("=" * 65)

    engine = DiagnosticEngine(include_dev_tests=include_dev_tests)
    total_tests = len(engine.items)
    passed_count = 0
    failed_count = 0
    warn_count = 0

    for i, item in enumerate(engine.items, 1):
        start_t = time.perf_counter()
        try:
            engine._dispatch_test(item)
        except Exception as e:
            item.status = "FAIL"
            item.message = str(e)
        finally:
            item.duration_sec = time.perf_counter() - start_t

        badge = f"[{item.status}]"
        if item.status == "PASS":
            passed_count += 1
        elif item.status == "FAIL":
            failed_count += 1
        elif item.status == "WARNING":
            warn_count += 1

        print(f"{i:02d}/{total_tests:02d} {badge:<9} {item.name:<38} ({item.duration_sec:.2f}s)")
        if verbose and item.message:
            print(f"       -> {item.message}")

    print("=" * 65)
    print(f"Diagnostic Summary: {passed_count} Passed, {failed_count} Failed, {warn_count} Warnings.")
    print("=" * 65)

    if "--report" in sys.argv or "-r" in sys.argv or failed_count > 0:
        print("\n" + generate_diagnostic_report(engine) + "\n")

    return 1 if failed_count > 0 else 0


def main():
    if "--gui" in sys.argv:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        dlg = create_diagnostic_dialog()
        dlg.exec()
        return 0
    else:
        return run_cli_diagnostics(verbose=True)


if __name__ == "__main__":
    raise SystemExit(main())

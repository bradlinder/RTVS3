"""shortcuts/schema.py — Shortcut definitions, dataclass models, and string helpers."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List

from PySide6.QtGui import QKeySequence
from core_utils import get_active_theme_mode


@dataclass
class ShortcutDef:
    action_id: str
    name: str
    category: str
    default_seq: str
    default_mac: str = ""
    description: str = ""
    attr_name: str = ""
    is_qshortcut: bool = False
    is_custom_event: bool = False


def _get_shortcuts_theme_mode() -> str:
    """Retrieve active theme mode ('light', 'dark', or 'high_contrast')."""
    return get_active_theme_mode("dark")


def get_platform_default(defn: ShortcutDef) -> str:
    """Return the platform-adapted default shortcut string for a definition."""
    if sys.platform == "darwin":
        if defn.default_mac:
            return defn.default_mac
        if "Ctrl+" in defn.default_seq:
            return defn.default_seq.replace("Ctrl+", "Meta+")
    return defn.default_seq


def format_sequence_display(seq_str: str) -> str:
    """Format key sequence into clean user-readable text for current OS."""
    if not seq_str or seq_str in ("None", "<none>", ""):
        return "None"
    seq = QKeySequence(seq_str)
    if not seq.isEmpty():
        native = seq.toString(QKeySequence.SequenceFormat.NativeText)
        if native:
            return native
    return seq_str


def normalize_sequence_string(seq_str: str) -> str:
    """Return portable normalized representation of a shortcut string."""
    if not seq_str or seq_str.strip() in ("", "None", "<none>"):
        return ""
    seq = QKeySequence(seq_str.strip())
    if seq.isEmpty():
        return seq_str.strip()
    return seq.toString(QKeySequence.SequenceFormat.PortableText)


# Comprehensive registry of all application functions that have keyboard shortcuts assigned.
SHORTCUT_DEFINITIONS: List[ShortcutDef] = [
    # -------------------------------------------------------------
    # File & Project
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="open_media",
        name="Open Media...",
        category="File & Project",
        default_seq="Ctrl+O",
        default_mac="Meta+O",
        description="Select an audio or video file to open and process",
        attr_name="open_media_action",
    ),
    ShortcutDef(
        action_id="open_document",
        name="Open Document...",
        category="File & Project",
        default_seq="Ctrl+Alt+O",
        default_mac="Meta+Alt+O",
        description="Open an existing .rtvs project document file",
        attr_name="open_doc_action",
    ),
    ShortcutDef(
        action_id="save_document",
        name="Save Document",
        category="File & Project",
        default_seq="Ctrl+S",
        default_mac="Meta+S",
        description="Save current project, audio offsets, stories, and edits to .rtvs file",
        attr_name="save_doc_action",
    ),
    ShortcutDef(
        action_id="save_document_as",
        name="Save Document As...",
        category="File & Project",
        default_seq="Ctrl+Shift+S",
        default_mac="Meta+Shift+S",
        description="Save current project to a new .rtvs file location",
        attr_name="save_doc_as_action",
    ),
    ShortcutDef(
        action_id="export_unified",
        name="Export Center...",
        category="File & Project",
        default_seq="Ctrl+E",
        default_mac="Meta+E",
        description="Open the Unified Export Center for audio, text, transcripts, and plugins",
        attr_name="unified_export_action",
    ),
    ShortcutDef(
        action_id="batch_transcribe",
        name="Batch Processing...",
        category="File & Project",
        default_seq="Ctrl+Shift+P",
        default_mac="Meta+Shift+P",
        description="Open Batch Audio / Video Transcription and Diarization Manager",
        attr_name="batch_process_action",
    ),
    ShortcutDef(
        action_id="multi_stage_pipeline",
        name="Multi-Stage Pipeline...",
        category="File & Project",
        default_seq="Ctrl+Shift+M",
        default_mac="Meta+Shift+M",
        description="Open automated multi-model pipeline configuration",
        attr_name="pipeline_action",
    ),
    ShortcutDef(
        action_id="manage_models",
        name="Manage AI Models...",
        category="File & Project",
        default_seq="Ctrl+M",
        default_mac="Meta+M",
        description="Download, delete, verify, and monitor Whisper and ASR neural weights",
        attr_name="manage_models_action",
    ),
    ShortcutDef(
        action_id="preferences",
        name="Preferences...",
        category="File & Project",
        default_seq="Ctrl+,",
        default_mac="Meta+,",
        description="Open application settings, audio playback, theming, and shortcuts",
        attr_name="prefs_action",
    ),
    ShortcutDef(
        action_id="export_diagnostics",
        name="Export Diagnostic Bundle...",
        category="File & Project",
        default_seq="Ctrl+Alt+D",
        default_mac="Meta+Alt+D",
        description="Export system diagnostic zip bundle for bug reports and support",
        attr_name="diag_bundle_action",
    ),
    ShortcutDef(
        action_id="quit_app",
        name="Exit Application",
        category="File & Project",
        default_seq="Ctrl+Q",
        default_mac="Meta+Q",
        description="Close the application",
        attr_name="quit_action",
    ),

    # -------------------------------------------------------------
    # Playback & Transport
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="play_pause",
        name="Play / Pause Audio",
        category="Playback & Transport",
        default_seq="Space",
        default_mac="Space",
        description="Toggle audio playback on/off from current playhead position",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_back_short",
        name="Jump Back (Short / 5s)",
        category="Playback & Transport",
        default_seq="Left",
        default_mac="Left",
        description="Rewind audio playhead by configured short jump distance (default 5s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_short",
        name="Jump Forward (Short / 5s)",
        category="Playback & Transport",
        default_seq="Right",
        default_mac="Right",
        description="Advance audio playhead by configured short jump distance (default 5s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_back_medium",
        name="Jump Back (Medium / 15s)",
        category="Playback & Transport",
        default_seq="Shift+Left",
        default_mac="Shift+Left",
        description="Rewind audio playhead by medium jump distance (default 15s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_medium",
        name="Jump Forward (Medium / 15s)",
        category="Playback & Transport",
        default_seq="Shift+Right",
        default_mac="Shift+Right",
        description="Advance audio playhead by medium jump distance (default 15s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_back_long",
        name="Jump Back (Long / 30s)",
        category="Playback & Transport",
        default_seq="Ctrl+Left",
        default_mac="Meta+Left",
        description="Rewind audio playhead by long jump distance (default 30s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_long",
        name="Jump Forward (Long / 30s)",
        category="Playback & Transport",
        default_seq="Ctrl+Right",
        default_mac="Meta+Right",
        description="Advance audio playhead by long jump distance (default 30s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_to_start",
        name="Jump to Start of Recording",
        category="Playback & Transport",
        default_seq="Home",
        default_mac="Home",
        description="Seek playhead to 00:00:00",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_to_end",
        name="Jump to End of Recording",
        category="Playback & Transport",
        default_seq="End",
        default_mac="End",
        description="Seek playhead to the end of the loaded media",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="play_current_story",
        name="Play Current Story Only",
        category="Playback & Transport",
        default_seq="Ctrl+Alt+Space",
        default_mac="Meta+Alt+Space",
        description="Play selected story block from in-point to out-point then stop",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="toggle_follow_playhead",
        name="Toggle Auto-Follow Playhead",
        category="Playback & Transport",
        default_seq="Ctrl+F12",
        default_mac="Meta+F12",
        description="Enable or disable automatic timeline scrolling following the playhead",
        is_qshortcut=True,
    ),

    # -------------------------------------------------------------
    # Story & Segment Editing
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="mark_story_start",
        name="Mark Story In-Point ([)",
        category="Story & Segment Editing",
        default_seq="[",
        default_mac="[",
        description="Set the beginning timestamp of a new story segment at current playhead",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="mark_story_end",
        name="Mark Story Out-Point (])",
        category="Story & Segment Editing",
        default_seq="]",
        default_mac="]",
        description="Set the ending timestamp of the current story segment at playhead and save story",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="edit_story_metadata",
        name="Edit Story Metadata...",
        category="Story & Segment Editing",
        default_seq="Ctrl+Shift+E",
        default_mac="Meta+Shift+E",
        description="Open story metadata editor for headline, author, excerpt, tags, and category",
        attr_name="edit_meta_action",
    ),
    ShortcutDef(
        action_id="configure_fades",
        name="Audio Fades & Crossfades...",
        category="Story & Segment Editing",
        default_seq="Ctrl+Shift+F",
        default_mac="Meta+Shift+F",
        description="Configure audio fade-in, fade-out, crossfade curves, and ducking parameters",
        attr_name="fades_action",
    ),
    ShortcutDef(
        action_id="edit_id3_tags",
        name="Edit ID3 / Broadcast Tags...",
        category="Story & Segment Editing",
        default_seq="Ctrl+I",
        default_mac="Meta+I",
        description="Open ID3v2 metadata tag editor for broadcast episode and podcast tagging",
        attr_name="id3_action",
    ),
    ShortcutDef(
        action_id="delete_selected_story",
        name="Delete Selected Story",
        category="Story & Segment Editing",
        default_seq="Delete",
        default_mac="Backspace",
        description="Remove currently highlighted story cut from project",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="rename_speaker",
        name="Rename Speaker...",
        category="Story & Segment Editing",
        default_seq="Ctrl+R",
        default_mac="Meta+R",
        description="Open speaker rename and identity manager for current segment",
        attr_name="rename_speaker_action",
    ),
    ShortcutDef(
        action_id="split_segment",
        name="Split Segment at Playhead",
        category="Story & Segment Editing",
        default_seq="Ctrl+K",
        default_mac="Meta+K",
        description="Split the highlighted transcript segment into two pieces at playhead timestamp",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="merge_segments",
        name="Merge with Next Segment",
        category="Story & Segment Editing",
        default_seq="Ctrl+J",
        default_mac="Meta+J",
        description="Combine selected transcript segment with following segment",
        is_qshortcut=True,
    ),

    # -------------------------------------------------------------
    # Search & Transcript Tools
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="find_text",
        name="Find in Transcript...",
        category="Search & Transcript Tools",
        default_seq="Ctrl+F",
        default_mac="Meta+F",
        description="Focus search bar to highlight words and phrases across transcript",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="find_next",
        name="Find Next Occurrence",
        category="Search & Transcript Tools",
        default_seq="F3",
        default_mac="Meta+G",
        description="Jump to next occurrence of search term in transcript",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="find_prev",
        name="Find Previous Occurrence",
        category="Search & Transcript Tools",
        default_seq="Shift+F3",
        default_mac="Meta+Shift+G",
        description="Jump to previous occurrence of search term in transcript",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="add_comment",
        name="Add Comment / Marker",
        category="Search & Transcript Tools",
        default_seq="Ctrl+Alt+C",
        default_mac="Meta+Alt+C",
        description="Attach an editorial comment or production marker to current playhead / text selection",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="manage_terminology",
        name="Glossary / Terminology...",
        category="Search & Transcript Tools",
        default_seq="Ctrl+T",
        default_mac="Meta+T",
        description="Open custom vocabulary, acronyms, station glossary, and ASR phonetic hints",
        attr_name="terminology_action",
    ),

    # -------------------------------------------------------------
    # Timeline & Zoom Navigation
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="zoom_in",
        name="Zoom In Timeline",
        category="Timeline & Navigation",
        default_seq="Ctrl+=",
        default_mac="Meta+=",
        description="Increase timeline horizontal zoom resolution",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="zoom_out",
        name="Zoom Out Timeline",
        category="Timeline & Navigation",
        default_seq="Ctrl+-",
        default_mac="Meta+-",
        description="Decrease timeline horizontal zoom resolution",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="zoom_fit",
        name="Fit Entire Timeline in View",
        category="Timeline & Navigation",
        default_seq="Ctrl+0",
        default_mac="Meta+0",
        description="Scale timeline zoom to show full audio duration within window width",
        is_qshortcut=True,
    ),

    # -------------------------------------------------------------
    # Help & Diagnostics
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="run_benchmark",
        name="Run Performance Benchmark...",
        category="Help & Diagnostics",
        default_seq="Ctrl+Shift+B",
        default_mac="Meta+Shift+B",
        description="Execute CPU, GPU, memory, and ASR model transcription speed benchmark",
        attr_name="benchmark_action",
    ),
    ShortcutDef(
        action_id="run_diagnostics",
        name="Run Diagnostic Test Bench...",
        category="Help & Diagnostics",
        default_seq="Ctrl+Shift+T",
        default_mac="Meta+Shift+T",
        description="Execute automated self-tests across all application engines and plugins",
        attr_name="tests_action",
    ),
    ShortcutDef(
        action_id="check_updates",
        name="Check for Updates...",
        category="Help & Diagnostics",
        default_seq="Ctrl+U",
        default_mac="Meta+U",
        description="Check GitHub releases for new versions and patches",
        attr_name="update_action",
    ),
]

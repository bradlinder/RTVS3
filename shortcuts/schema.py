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


# Alias dictionary mapping legacy/UI action IDs to primary schema action IDs
ACTION_ALIASES = {
    # Transport aliases
    "seek_backward": "jump_back_short",
    "seek_forward": "jump_forward_short",
    "seek_start": "jump_to_start",
    "seek_end": "jump_to_end",
    # Story aliases
    "set_story_start": "mark_story_start",
    "set_story_end": "mark_story_end",
    "mark_story_in": "mark_story_start",
    "mark_story_out": "mark_story_end",
    # Legacy export & project aliases
    "export": "export_unified",
    "export_stories": "export_unified",
    "batch_processing": "batch_transcribe",
    "batch_process": "batch_transcribe",
    "run_pipeline": "multi_stage_pipeline",
    "pipeline": "multi_stage_pipeline",
    "save_project": "save_document",
    "save_project_as": "save_document_as",
    "exit_app": "quit_app",
    "find_replace": "find_text",
    "glossary": "manage_terminology",
    "id3_tags": "edit_id3_tags",
    "fades": "configure_fades",
}

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
        description="Import an external text document into transcript workspace",
        attr_name="open_doc_action",
    ),
    ShortcutDef(
        action_id="new_project",
        name="New Project",
        category="File & Project",
        default_seq="Ctrl+N",
        default_mac="Meta+N",
        description="Create a new project session",
        attr_name="new_proj_action",
    ),
    ShortcutDef(
        action_id="open_project",
        name="Open Project...",
        category="File & Project",
        default_seq="Ctrl+Shift+O",
        default_mac="Meta+Shift+O",
        description="Open an existing .rtvs project session",
        attr_name="open_proj_action",
    ),
    ShortcutDef(
        action_id="close_project",
        name="Close Project",
        category="File & Project",
        default_seq="Ctrl+W",
        default_mac="Meta+W",
        description="Close current project session",
        attr_name="close_proj_action",
    ),
    ShortcutDef(
        action_id="save_document",
        name="Save Project",
        category="File & Project",
        default_seq="Ctrl+S",
        default_mac="Meta+S",
        description="Save current project, audio offsets, stories, and edits",
        attr_name="save_action",
    ),
    ShortcutDef(
        action_id="save_document_as",
        name="Save Project As...",
        category="File & Project",
        default_seq="Ctrl+Shift+S",
        default_mac="Meta+Shift+S",
        description="Save current project to a new file location",
        attr_name="save_as_action",
    ),
    ShortcutDef(
        action_id="export_zip",
        name="Export Project Archive (.zip)...",
        category="File & Project",
        default_seq="Ctrl+Shift+E",
        default_mac="Meta+Shift+E",
        description="Export complete project archive with audio and transcript to a .zip file",
        attr_name="export_zip_action",
    ),
    ShortcutDef(
        action_id="export_unified",
        name="Unified Export Center...",
        category="File & Project",
        default_seq="Ctrl+E",
        default_mac="Meta+E",
        description="Open the Unified Export Center for audio, text, transcripts, and plugins",
        attr_name="export_action",
    ),
    ShortcutDef(
        action_id="copy_yt_chapters",
        name="Copy YouTube Chapters to Clipboard",
        category="File & Project",
        default_seq="Ctrl+Shift+Y",
        default_mac="Meta+Shift+Y",
        description="Copy zero-based timestamps and story headlines formatted for YouTube descriptions",
        attr_name="copy_yt_chapters_action",
    ),
    ShortcutDef(
        action_id="batch_transcribe",
        name="Batch Processing...",
        category="File & Project",
        default_seq="Ctrl+Shift+B",
        default_mac="Meta+Shift+B",
        description="Open Batch Audio / Video Transcription and Diarization Manager",
        attr_name="batch_process_action",
    ),
    ShortcutDef(
        action_id="backup_restore",
        name="Backup & Restore...",
        category="File & Project",
        default_seq="",
        default_mac="",
        description="Open project snapshot backup and restore manager",
        attr_name="backup_restore_action",
    ),
    ShortcutDef(
        action_id="manage_models",
        name="Manage AI Models...",
        category="File & Project",
        default_seq="Ctrl+Alt+M",
        default_mac="Meta+Alt+M",
        description="Download, delete, verify, and monitor Whisper and ASR neural weights",
        attr_name="manage_models_action",
    ),
    ShortcutDef(
        action_id="preferences",
        name="Preferences...",
        category="File & Project",
        default_seq="Ctrl+P",
        default_mac="Meta+P",
        description="Open application settings, audio playback, theming, and shortcuts",
        attr_name="pref_action",
    ),
    ShortcutDef(
        action_id="manage_plugins",
        name="Manage Plugins & Add-ons...",
        category="File & Project",
        default_seq="Ctrl+Shift+X",
        default_mac="Meta+Shift+X",
        description="Enable, disable, or inspect external plugins and integrations",
        attr_name="manage_plugins_action",
    ),
    ShortcutDef(
        action_id="gpu_settings",
        name="GPU Acceleration Settings...",
        category="File & Project",
        default_seq="Ctrl+Alt+G",
        default_mac="Meta+Alt+G",
        description="Configure CUDA, ROCm, or DirectML GPU hardware acceleration",
        attr_name="gpu_action",
    ),
    ShortcutDef(
        action_id="quit_app",
        name="Exit Application",
        category="File & Project",
        default_seq="Ctrl+Q",
        default_mac="Meta+Q",
        description="Close the application",
        attr_name="exit_action",
    ),

    # -------------------------------------------------------------
    # AI Pipeline & Tools
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="transcribe",
        name="Transcribe Audio...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+T",
        default_mac="Meta+T",
        description="Run automated speech-to-text transcription on loaded media",
        attr_name="transcribe_action",
    ),
    ShortcutDef(
        action_id="detect_speakers",
        name="Detect Speakers (Diarization)...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+D",
        default_mac="Meta+D",
        description="Perform speaker diarization and voice cluster detection",
        attr_name="diarize_action",
    ),
    ShortcutDef(
        action_id="detect_stories",
        name="Detect Stories...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+Shift+A",
        default_mac="Meta+Shift+A",
        description="Automatically segment recording into stories or songs based on pauses",
        attr_name="auto_detect_action",
    ),
    ShortcutDef(
        action_id="translate",
        name="Translate Transcript...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+Shift+L",
        default_mac="Meta+Shift+L",
        description="Translate transcript text into Spanish or target language",
        attr_name="translate_action",
    ),
    ShortcutDef(
        action_id="multi_stage_pipeline",
        name="Multi-Stage Processing Pipeline...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+R",
        default_mac="Meta+R",
        description="Execute automated multi-model transcription, diarization, and story segmentation",
        attr_name="transcribe_diarize_detect_action",
    ),
    ShortcutDef(
        action_id="regen_waveform",
        name="Regenerate Waveform",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+Shift+W",
        default_mac="Meta+Shift+W",
        description="Rebuild audio peak envelope cache for the timeline",
        attr_name="regen_waveform_action",
    ),
    ShortcutDef(
        action_id="regen_thumbnails",
        name="Regenerate Video Thumbnails",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+Shift+T",
        default_mac="Meta+Shift+T",
        description="Extract new frame thumbnails across video duration",
        attr_name="regen_thumbnails_action",
    ),
    ShortcutDef(
        action_id="normalize_loudness",
        name="Normalize Audio Loudness...",
        category="AI Pipeline & Tools",
        default_seq="Ctrl+Alt+N",
        default_mac="Meta+Alt+N",
        description="Analyze and normalize broadcast loudness according to EBU R128 / ITU BS.1770",
        attr_name="normalize_loudness_action",
    ),

    # -------------------------------------------------------------
    # Panels & Views
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="toggle_timeline",
        name="Toggle Timeline Panel",
        category="Panels & Views",
        default_seq="Alt+1",
        default_mac="Ctrl+Alt+1",
        description="Show or hide the audio/video timeline and waveform panel",
        attr_name="toggle_timeline_action",
    ),
    ShortcutDef(
        action_id="toggle_transcript",
        name="Toggle Transcript Panel",
        category="Panels & Views",
        default_seq="Alt+2",
        default_mac="Ctrl+Alt+2",
        description="Show or hide the interactive text transcript panel",
        attr_name="toggle_transcript_action",
    ),
    ShortcutDef(
        action_id="toggle_stories",
        name="Toggle Stories Panel",
        category="Panels & Views",
        default_seq="Alt+3",
        default_mac="Ctrl+Alt+3",
        description="Show or hide the story cuts and segment list panel",
        attr_name="toggle_stories_action",
    ),
    ShortcutDef(
        action_id="toggle_activity",
        name="Toggle Activity History Panel",
        category="Panels & Views",
        default_seq="Alt+4",
        default_mac="Ctrl+Alt+4",
        description="Show or hide the background job and activity log panel",
        attr_name="toggle_activity_action",
    ),
    ShortcutDef(
        action_id="toggle_comments",
        name="Toggle Comments Sidebar",
        category="Panels & Views",
        default_seq="Ctrl+Alt+C",
        default_mac="Meta+Alt+C",
        description="Show or hide the editorial comments and annotations sidebar",
        attr_name="toggle_comments_action",
    ),
    ShortcutDef(
        action_id="toggle_comment_highlights",
        name="Show Comment Highlights",
        category="Panels & Views",
        default_seq="Ctrl+Alt+H",
        default_mac="Meta+Alt+H",
        description="Toggle yellow editorial comment highlight overlays in transcript",
        attr_name="toggle_comment_highlights_action",
    ),
    ShortcutDef(
        action_id="show_waveform",
        name="Show Waveform",
        category="Panels & Views",
        default_seq="Ctrl+Alt+W",
        default_mac="Meta+Alt+W",
        description="Toggle visual audio waveform display in the timeline",
        attr_name="show_waveform_action",
    ),
    ShortcutDef(
        action_id="show_thumbnails",
        name="Show Video Thumbnails",
        category="Panels & Views",
        default_seq="Ctrl+Alt+T",
        default_mac="Meta+Alt+T",
        description="Toggle thumbnail preview strip along the video timeline",
        attr_name="show_thumbnails_action",
    ),
    ShortcutDef(
        action_id="video_preview",
        name="Video Preview Window",
        category="Panels & Views",
        default_seq="Ctrl+Shift+V",
        default_mac="Meta+Shift+V",
        description="Open or toggle the floating video preview monitor window",
        attr_name="video_preview_action",
    ),
    ShortcutDef(
        action_id="show_speaker_labels",
        name="Show Speaker Labels",
        category="Panels & Views",
        default_seq="Ctrl+Alt+S",
        default_mac="Meta+Alt+S",
        description="Show or hide speaker names before each transcript turn",
        attr_name="show_speaker_labels_action",
    ),
    ShortcutDef(
        action_id="show_timestamps",
        name="Show Timestamps",
        category="Panels & Views",
        default_seq="Ctrl+Alt+I",
        default_mac="Meta+Alt+I",
        description="Show or hide timecode markers in the transcript",
        attr_name="show_timestamps_action",
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
        name="Skip Backward (5s)",
        category="Playback & Transport",
        default_seq="Left",
        default_mac="Left",
        description="Rewind audio playhead by configured short jump distance (default 5s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_short",
        name="Skip Forward (5s)",
        category="Playback & Transport",
        default_seq="Right",
        default_mac="Right",
        description="Advance audio playhead by configured short jump distance (default 5s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_back_medium",
        name="Jump Back (15s)",
        category="Playback & Transport",
        default_seq="Shift+Left",
        default_mac="Shift+Left",
        description="Rewind audio playhead by medium jump distance (default 15s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_medium",
        name="Jump Forward (15s)",
        category="Playback & Transport",
        default_seq="Shift+Right",
        default_mac="Shift+Right",
        description="Advance audio playhead by medium jump distance (default 15s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_back_long",
        name="Jump Back (30s)",
        category="Playback & Transport",
        default_seq="Ctrl+Left",
        default_mac="Meta+Left",
        description="Rewind audio playhead by long jump distance (default 30s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_forward_long",
        name="Jump Forward (30s)",
        category="Playback & Transport",
        default_seq="Ctrl+Right",
        default_mac="Meta+Right",
        description="Advance audio playhead by long jump distance (default 30s)",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_to_start",
        name="Seek to Start",
        category="Playback & Transport",
        default_seq="Home",
        default_mac="Home",
        description="Seek playhead to 00:00:00",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="jump_to_end",
        name="Seek to End",
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
        action_id="configure_fades",
        name="Audio Fades & Crossfades...",
        category="Story & Segment Editing",
        default_seq="Ctrl+Shift+F",
        default_mac="Meta+Shift+F",
        description="Configure audio fade-in, fade-out, crossfade curves, and ducking parameters",
        is_custom_event=True,
    ),
    ShortcutDef(
        action_id="edit_id3_tags",
        name="ID3 Tag Editor (MP3)...",
        category="Story & Segment Editing",
        default_seq="Ctrl+Shift+I",
        default_mac="Meta+Shift+I",
        description="Open ID3v2 metadata tag editor for broadcast episode and podcast tagging",
        attr_name="id3_editor_action",
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
        action_id="toggle_edit_mode",
        name="Toggle Proofreading / Edit Mode",
        category="Story & Segment Editing",
        default_seq="F2",
        default_mac="F2",
        description="Toggle between viewing and proofreading edit mode",
        attr_name="transcript_edit_mode_action",
    ),
    ShortcutDef(
        action_id="split_speaker",
        name="Split Speaker Segment",
        category="Story & Segment Editing",
        default_seq="Shift+Return",
        default_mac="Shift+Return",
        description="Split current segment at cursor position and insert a new speaker turn",
        attr_name="fmt_split_action",
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
    ShortcutDef(
        action_id="undo",
        name="Undo",
        category="Story & Segment Editing",
        default_seq="Ctrl+Z",
        default_mac="Meta+Z",
        description="Undo previous transcript or story edit",
        attr_name="undo_action",
    ),
    ShortcutDef(
        action_id="redo",
        name="Redo",
        category="Story & Segment Editing",
        default_seq="Ctrl+Shift+Z",
        default_mac="Meta+Shift+Z",
        description="Redo previously undone edit",
        attr_name="redo_action",
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
        attr_name="find_action",
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
        name="Add / Edit Comment...",
        category="Search & Transcript Tools",
        default_seq="Ctrl+M",
        default_mac="Meta+M",
        description="Attach an editorial comment or production marker to current playhead / text selection",
        attr_name="add_comment_action",
    ),
    ShortcutDef(
        action_id="manage_terminology",
        name="Glossary & Custom Vocabulary...",
        category="Search & Transcript Tools",
        default_seq="Ctrl+Shift+G",
        default_mac="Meta+Shift+G",
        description="Open custom vocabulary, acronyms, station glossary, and ASR phonetic hints",
        attr_name="glossary_action",
    ),
    ShortcutDef(
        action_id="fmt_bold",
        name="Bold Text",
        category="Search & Transcript Tools",
        default_seq="Ctrl+B",
        default_mac="Meta+B",
        description="Toggle bold formatting on selected transcript text",
        attr_name="fmt_bold_action",
    ),
    ShortcutDef(
        action_id="fmt_italic",
        name="Italic Text",
        category="Search & Transcript Tools",
        default_seq="Ctrl+I",
        default_mac="Meta+I",
        description="Toggle italic formatting on selected transcript text",
        attr_name="fmt_italic_action",
    ),
    ShortcutDef(
        action_id="fmt_underline",
        name="Underline Text",
        category="Search & Transcript Tools",
        default_seq="Ctrl+U",
        default_mac="Meta+U",
        description="Toggle underline formatting on selected transcript text",
        attr_name="fmt_underline_action",
    ),
    ShortcutDef(
        action_id="fmt_clear",
        name="Clear Text Formatting",
        category="Search & Transcript Tools",
        default_seq="Ctrl+\\",
        default_mac="Meta+\\",
        description="Remove rich formatting and color styles from selected transcript text",
        attr_name="fmt_clear_action",
    ),
    ShortcutDef(
        action_id="transcript_font_up",
        name="Increase Transcript Text Size",
        category="Search & Transcript Tools",
        default_seq="Ctrl++",
        default_mac="Meta++",
        description="Increase transcript display font size by 1 point",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="transcript_font_down",
        name="Decrease Transcript Text Size",
        category="Search & Transcript Tools",
        default_seq="Ctrl+-",
        default_mac="Meta+-",
        description="Decrease transcript display font size by 1 point",
        is_qshortcut=True,
    ),
    ShortcutDef(
        action_id="transcript_font_reset",
        name="Reset Transcript Text Size",
        category="Search & Transcript Tools",
        default_seq="Ctrl+0",
        default_mac="Meta+0",
        description="Reset transcript display font size to default",
        is_qshortcut=True,
    ),

    # -------------------------------------------------------------
    # Timeline & Navigation
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="zoom_in",
        name="Zoom In Timeline",
        category="Timeline & Navigation",
        default_seq="+",
        default_mac="+",
        description="Increase timeline horizontal zoom resolution (or Mouse Wheel)",
        is_custom_event=True,
    ),
    ShortcutDef(
        action_id="zoom_out",
        name="Zoom Out Timeline",
        category="Timeline & Navigation",
        default_seq="-",
        default_mac="-",
        description="Decrease timeline horizontal zoom resolution (or Mouse Wheel)",
        is_custom_event=True,
    ),

    # -------------------------------------------------------------
    # Help & Diagnostics
    # -------------------------------------------------------------
    ShortcutDef(
        action_id="run_benchmark",
        name="Run Performance Benchmark...",
        category="Help & Diagnostics",
        default_seq="Ctrl+Alt+B",
        default_mac="Meta+Alt+B",
        description="Execute CPU, GPU, memory, and ASR model transcription speed benchmark",
        attr_name="benchmark_action",
    ),
    ShortcutDef(
        action_id="run_diagnostics",
        name="Run Diagnostic Test Bench...",
        category="Help & Diagnostics",
        default_seq="Ctrl+Shift+D",
        default_mac="Meta+Shift+D",
        description="Execute automated self-tests across all application engines and plugins",
        attr_name="test_bench_action",
    ),
    ShortcutDef(
        action_id="check_updates",
        name="Check for Updates...",
        category="Help & Diagnostics",
        default_seq="Ctrl+Alt+U",
        default_mac="Meta+Alt+U",
        description="Check GitHub releases for new versions and patches",
        attr_name="update_action",
    ),
    ShortcutDef(
        action_id="help_shortcuts",
        name="Keyboard Shortcuts Reference",
        category="Help & Diagnostics",
        default_seq="F1",
        default_mac="Meta+?",
        description="Open interactive keyboard shortcuts reference table",
        attr_name="shortcuts_help_action",
    ),
    ShortcutDef(
        action_id="about",
        name="About Application",
        category="Help & Diagnostics",
        default_seq="Shift+F1",
        default_mac="Shift+F1",
        description="Display version, build, and system diagnostic overview",
        attr_name="about_action",
    ),
    ShortcutDef(
        action_id="diagnostic_log",
        name="Open Diagnostic Log Folder",
        category="Help & Diagnostics",
        default_seq="Ctrl+Shift+K",
        default_mac="Meta+Shift+K",
        description="Open the application diagnostic logs directory in file explorer",
        attr_name="log_action",
    ),
    ShortcutDef(
        action_id="licenses",
        name="Third-Party Licenses",
        category="Help & Diagnostics",
        default_seq="Ctrl+Shift+F1",
        default_mac="Meta+Shift+F1",
        description="View open-source licenses and attribution disclosures",
        attr_name="licenses_action",
    ),
]

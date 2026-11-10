# reaper_bridge.pyi — Typing and Interface Stub for reaper_bridge
from __future__ import annotations
from __future__ import annotations
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core_utils import get_app_data_dir, safe_replace
from speaker_palette import get_speaker_color

def get_reaper_ipc_paths() -> List[Path]:
    ...

def reaper_color_from_hex(hex_str: str) -> int:
    ...

def _fmt_clock(secs: float) -> str:
    ...

def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    ...

def _is_sentence_terminator(text: str) -> bool:
    ...

def _build_phrase_preview(text: str, fallback_spk: str=...) -> str:
    ...

def _extract_formatted_transcript_sentences(main_win: Any) -> List[Dict[str, Any]]:
    ...

def get_reaper_clip_notes_and_markers(main_win: Any, start_sec: float, end_sec: float, marker_style: str=..., apply_speaker_color: bool=..., include_notes: bool=..., include_markers: bool=..., precomputed_sentences: Optional[List[Dict[str, Any]]]=...) -> Dict[str, Any]:
    ...

def build_reaper_cue_payload(main_win: Any, start_sec: float, end_sec: float, plain_text: str, title: str=..., clip_type: str=..., story_obj: Any=..., include_word_cues: bool=..., rendered_wav_path: str=..., marker_style: Optional[str]=...) -> Dict[str, Any]:
    ...

def get_reaper_index_paths() -> List[Path]:
    ...

def write_reaper_transcript_index(main_win: Any, precomputed_sentences: Optional[List[Dict[str, Any]]]=...) -> List[Path]:
    ...

def write_reaper_sidecar_cue(payload: Dict[str, Any]) -> List[Path]:
    ...

def attach_reaper_cue_to_mimedata(mime_data: Any, payload: Dict[str, Any]) -> None:
    ...

def get_default_reaper_scripts_dir() -> Path:
    ...

def get_bundled_lua_scripts() -> Dict[str, Path]:
    ...

def install_reaper_scripts_to_resource_path(parent_widget: Any=..., target_dir: Optional[Path]=...) -> Tuple[bool, str, List[Path]]:
    ...

def render_temp_daw_wav_clip(main_win: Any, start_sec: float, end_sec: float, title: str=...) -> Optional[Path]:
    ...

def copy_selection_as_daw_wav_clip(main_win: Any, start_sec: float, end_sec: float, plain_text: str, html_text: str=..., title: str=..., story_obj: Any=...) -> Optional[Path]:
    ...

def populate_unified_copy_mimedata(main_win: Any, mime_data: Any, start_sec: Optional[float]=..., end_sec: Optional[float]=..., plain_text: str=..., title: str=..., clip_type: str=..., story_obj: Any=...) -> None:
    ...

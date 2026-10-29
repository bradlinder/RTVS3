# timeline.pyi — Typing and Interface Stub for timeline
from __future__ import annotations
from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from export.subtitles import generate_cue_content

def _xml_escape(text: str) -> str:
    ...
RTVS_STORY_PALETTE: tuple[str, ...] = ...

def reaper_color_from_hex(hex_str: str) -> int:
    ...

def _reaper_fade_curve_index(curve_name: str) -> int:
    ...

def format_edl_timestamp(seconds: float) -> str:
    ...

def _get_story_start(s: Any) -> float:
    ...

def _get_story_end(s: Any, start_val: float) -> float:
    ...

def build_timeline_clips(stories: list, total_duration: float=..., unselected_audio_mode: str=..., apply_fades: bool=..., scope: str=..., all_stories: Optional[list]=...) -> List[Dict[str, Any]]:
    ...

def _build_reaper_track_block(track_name: str, clips: List[Dict[str, Any]], source_type: str, media_name_only: str) -> List[str]:
    ...

def generate_reaper_project(stories: list, media_filename: str=..., project_title: str=..., apply_fades: bool=..., sample_rate: int=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_samplitude_edl(stories: list, media_filename: str=..., project_title: str=..., sample_rate: int=..., apply_fades: bool=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_fcp7_xml(stories: list, media_filename: str=..., project_title: str=..., sample_rate: int=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_fcpxml(stories: list, media_filename: str=..., project_title: str=..., sample_rate: int=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_aaf_interchange(stories: list, media_filename: str=..., project_title: str=..., sample_rate: int=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_hindenburg_session(stories: list, media_filename: str=..., project_title: str=..., sample_rate: int=..., total_duration: float=..., unselected_audio_mode: str=..., track_name: str=..., apply_fades: bool=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_audacity_labels(stories: list, total_duration: float=..., unselected_audio_mode: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

def generate_cue_sheet(stories: list, media_filename: str=..., project_title: str=..., total_duration: float=...) -> str:
    ...

def generate_daw_marker_csv(stories: list, total_duration: float=..., unselected_audio_mode: str=..., scope: str=..., all_stories: Optional[list]=...) -> str:
    ...

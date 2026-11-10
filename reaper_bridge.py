"""reaper_bridge.py — REAPER DAW Companion Bridge & Inter-Process Cue Emitter.

Provides zero-dependency data modeling, atomic sidecar file emission,
and Qt QMimeData payload formatting for interoperability between
Radio & TV Story Segmenter and REAPER DAW (as well as ReaScript Lua companions).
"""

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

logger = logging.getLogger(__name__)

REAPER_CUE_MIME = "application/x-rtvs-reaper-cue+json"


def get_reaper_ipc_paths() -> List[Path]:
    """Return the list of standard sidecar IPC file destinations.

    Returns primary IPC file in AppData and a fast tempdir fallback
    accessible by ReaScript across Windows, macOS, and Linux.
    """
    paths: List[Path] = []
    try:
        app_ipc = get_app_data_dir() / "reaper_ipc" / "latest_clip_cue.json"
        paths.append(app_ipc)
    except Exception:
        pass

    try:
        tmp_ipc = Path(tempfile.gettempdir()) / "rtvs3_reaper_cue.json"
        if tmp_ipc not in paths:
            paths.append(tmp_ipc)
    except Exception:
        pass

    return paths


def reaper_color_from_hex(hex_str: str) -> int:
    """Convert #RRGGBB hex color to Cockos REAPER custom color integer (0x1000000 | 0x1RRGGBB)."""
    h = str(hex_str or "").strip().lstrip("#")
    if len(h) != 6:
        return 0
    try:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return 0x1000000 | (r << 16) | (g << 8) | b
    except Exception:
        return 0


def _fmt_clock(secs: float) -> str:
    """Format seconds into MM:SS.S clock timecode."""
    m = int(secs) // 60
    s = secs - (m * 60)
    return f"{m:02d}:{s:04.1f}"


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex color (#RRGGBB) to (R, G, B) tuple."""
    h = str(hex_str or "").strip().lstrip("#")
    if len(h) == 6:
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            pass
    return (56, 189, 248)


_COMMON_ABBREVIATIONS = frozenset({
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "vs.", "etc.",
    "e.g.", "i.e.", "u.s.", "inc.", "ltd.", "co.", "corp.", "st.", "ave.", "blvd.",
    "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.", "oct.", "nov.", "dec."
})


def _is_sentence_terminator(text: str) -> bool:
    """Check whether a text fragment ends with terminal sentence punctuation (., ?, !, ...)."""
    if not text:
        return False
    cleaned = text.rstrip(' "\'\u201c\u201d\u2018\u2019)»]')
    if not cleaned:
        return False
    if cleaned.endswith("...") or cleaned.endswith("\u2026"):
        return True
    if cleaned.endswith(("?", "!")):
        return True
    if cleaned.endswith("."):
        parts = cleaned.split()
        last_word = parts[-1].lower() if parts else ""
        if last_word in _COMMON_ABBREVIATIONS:
            return False
        if len(last_word) == 2 and last_word[0].isalpha() and last_word[1] == ".":
            return False
        return True
    return False


def _build_phrase_preview(text: str, fallback_spk: str = "Speaker") -> str:
    """Build a concise, readable 6-word phrase preview for REAPER take markers."""
    raw = str(text or "").strip()
    words = raw.split()
    if not words:
        return str(fallback_spk or "Speaker")
    phrase = " ".join(words[:6])
    if len(phrase) > 42:
        phrase = phrase[:39].rstrip() + "..."
    elif len(words) > 6:
        phrase += "..."
    return phrase



def _extract_formatted_transcript_sentences(main_win: Any) -> List[Dict[str, Any]]:
    """Build formatted grammatical sentences (with word timings and paragraph flags) matching RTVS transcript view."""
    if main_win is None:
        return []
    t_data = getattr(main_win, "transcript", None)
    if not isinstance(t_data, dict):
        return []
    raw_segs = t_data.get("segments", [])
    if not isinstance(raw_segs, list) or not raw_segs:
        return []

    spk_overrides = getattr(main_win, "segment_speaker_overrides", {}) or {}
    spk_names = getattr(main_win, "speaker_names", {}) or {}
    speaker_at_time_fn = getattr(main_win, "speaker_at_time", None)
    eff_spk_fn = getattr(main_win, "get_effective_speaker_name", None)
    disp_spk_fn = getattr(main_win, "display_speaker", None)
    min_words = int(getattr(main_win, "min_words_per_paragraph", 40) or 40)
    silence_thresh = max(2.5, float(getattr(main_win, "silence_threshold", 3.0) or 3.0))

    def _resolve_raw_seg_speaker(seg_i: int, seg_dict: Dict[str, Any], s_t: float, e_t: float) -> str:
        if callable(eff_spk_fn):
            try:
                eff = str(eff_spk_fn(seg_i, seg_dict) or "").strip()
                if eff:
                    return eff
            except Exception:
                pass
        override_key = spk_overrides.get(seg_i) or spk_overrides.get(str(seg_i))
        if override_key:
            if callable(disp_spk_fn):
                return str(disp_spk_fn(override_key) or override_key)
            return str(spk_names.get(override_key, override_key))
        raw_spk = None
        if callable(speaker_at_time_fn):
            try:
                raw_spk = speaker_at_time_fn(s_t, e_t)
            except Exception:
                raw_spk = None
        if not raw_spk:
            raw_spk = seg_dict.get("speaker")
        if not raw_spk:
            return ""
        raw_str = str(raw_spk).strip()
        if callable(disp_spk_fn):
            return str(disp_spk_fn(raw_str) or raw_str)
        if raw_str in spk_names:
            return str(spk_names[raw_str])
        return raw_str

    sentences_out: List[Dict[str, Any]] = []
    curr_texts: List[str] = []
    curr_words: List[Dict[str, Any]] = []
    curr_start: Optional[float] = None
    curr_end: Optional[float] = None
    curr_spk: Optional[str] = None
    curr_is_para_start: bool = True
    para_word_count: int = 0
    last_flushed_end: Optional[float] = None
    last_flushed_spk: Optional[str] = None

    def _flush_current_sentence() -> None:
        nonlocal curr_texts, curr_words, curr_start, curr_end, curr_is_para_start, para_word_count, last_flushed_end, last_flushed_spk
        if not curr_texts or curr_start is None:
            curr_texts = []
            curr_words = []
            curr_start = None
            curr_end = None
            return
        sent_text = " ".join(t for t in curr_texts if t).strip()
        if not sent_text:
            curr_texts = []
            curr_words = []
            curr_start = None
            curr_end = None
            return
        spk_final = curr_spk or "Speaker"
        sc = get_speaker_color(spk_final)
        c_hex = sc.dark_hex if hasattr(sc, "dark_hex") else "#38bdf8"
        is_spk_change = (spk_final != last_flushed_spk)
        sentences_out.append({
            "index": len(sentences_out),
            "start_sec": round(curr_start, 4),
            "end_sec": round(curr_end or curr_start, 4),
            "speaker": spk_final,
            "is_speaker_change": is_spk_change,
            "is_paragraph_start": bool(curr_is_para_start or is_spk_change),
            "color_hex": c_hex,
            "reaper_rgb": list(_hex_to_rgb(c_hex)),
            "text": sent_text,
            "preview": _build_phrase_preview(sent_text, spk_final),
            "words": list(curr_words),
        })
        para_word_count += len(sent_text.split())
        last_flushed_end = curr_end or curr_start
        last_flushed_spk = spk_final
        curr_is_para_start = (para_word_count >= min_words)
        if curr_is_para_start:
            para_word_count = 0
        curr_texts = []
        curr_words = []
        curr_start = None
        curr_end = None

    active_speaker_carry: str = ""
    for idx, seg in enumerate(raw_segs):
        if not isinstance(seg, dict):
            continue
        s_sec = float(seg.get("start", 0.0) or 0.0)
        e_sec = float(seg.get("end", s_sec) or s_sec)
        resolved_spk = _resolve_raw_seg_speaker(idx, seg, s_sec, e_sec)
        if not resolved_spk or resolved_spk == "Speaker":
            if active_speaker_carry:
                resolved_spk = active_speaker_carry
            else:
                resolved_spk = "Speaker"
        else:
            active_speaker_carry = resolved_spk

        raw_w_list = seg.get("words", [])
        seg_words_out: List[Dict[str, Any]] = []
        had_deleted = False
        if isinstance(raw_w_list, list) and raw_w_list:
            for w_item in raw_w_list:
                if not isinstance(w_item, dict):
                    continue
                if bool(w_item.get("deleted", False)):
                    had_deleted = True
                    continue
                w_str = str(w_item.get("word", "")).strip()
                if w_str:
                    seg_words_out.append({
                        "word": w_str,
                        "start": round(float(w_item.get("start", s_sec)), 4),
                        "end": round(float(w_item.get("end", e_sec)), 4),
                    })

        seg_text_clean = str(seg.get("text", "")).strip()
        if had_deleted:
            seg_text_clean = " ".join(w["word"] for w in seg_words_out).strip()
        if not seg_text_clean and not seg_words_out:
            continue

        if not seg_words_out and seg_text_clean:
            tokens = seg_text_clean.split()
            if tokens:
                dur = max(0.01, e_sec - s_sec)
                tok_dur = dur / len(tokens)
                for t_idx, tok in enumerate(tokens):
                    seg_words_out.append({
                        "word": tok,
                        "start": round(s_sec + (t_idx * tok_dur), 4),
                        "end": round(s_sec + ((t_idx + 1) * tok_dur), 4),
                    })

        if curr_spk is not None and resolved_spk != curr_spk:
            _flush_current_sentence()
            curr_is_para_start = True
            para_word_count = 0

        curr_spk = resolved_spk

        if not curr_texts and last_flushed_end is not None and (s_sec - last_flushed_end) >= silence_thresh:
            curr_is_para_start = True
            para_word_count = 0

        text_tokens = seg_text_clean.split()
        if len(seg_words_out) == len(text_tokens) and len(seg_words_out) > 0:
            for w_obj in seg_words_out:
                w_str = w_obj["word"]
                w_st = float(w_obj["start"])
                w_en = float(w_obj["end"])
                if curr_start is None:
                    curr_start = w_st
                curr_end = w_en
                curr_texts.append(w_str)
                curr_words.append(w_obj)
                if _is_sentence_terminator(w_str):
                    _flush_current_sentence()
        else:
            if curr_start is None:
                curr_start = s_sec
            curr_end = e_sec
            curr_texts.append(seg_text_clean)
            curr_words.extend(seg_words_out)
            if _is_sentence_terminator(seg_text_clean):
                _flush_current_sentence()

    if curr_texts:
        _flush_current_sentence()

    return sentences_out


def get_reaper_clip_notes_and_markers(
    main_win: Any,
    start_sec: float,
    end_sec: float,
    marker_style: str = "speakers",
    apply_speaker_color: bool = False,
    include_notes: bool = True,
    include_markers: bool = True,
    precomputed_sentences: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Extract formatted transcript notes, take markers, and colors for a clip in an exported REAPER project."""
    s_sec = max(0.0, float(start_sec or 0.0))
    e_sec = max(s_sec, float(end_sec or s_sec))
    sents = precomputed_sentences if precomputed_sentences is not None else _extract_formatted_transcript_sentences(main_win)
    in_range = [s for s in sents if float(s.get("end_sec", 0.0)) > s_sec and float(s.get("start_sec", 0.0)) < e_sec]

    notes_str = ""
    if include_notes and in_range:
        paras: List[str] = []
        cur_spk, cur_words, cur_st = None, [], s_sec
        for s in in_range:
            spk = str(s.get("speaker", "Speaker"))
            st = max(s_sec, float(s.get("start_sec", s_sec)))
            w_list = s.get("words", [])
            in_words = [
                str(w.get("word", "")).strip()
                for w in w_list
                if isinstance(w, dict) and float(w.get("end", 0.0)) > s_sec and float(w.get("start", 0.0)) < e_sec
            ] if w_list else []
            body = " ".join(in_words) if in_words else str(s.get("text", "")).strip()
            if not body:
                continue
            if cur_spk is not None and (spk != cur_spk or bool(s.get("is_paragraph_start", False))):
                if cur_words:
                    paras.append(f"[{_fmt_clock(cur_st)}] {cur_spk}:\r\n{' '.join(cur_words)}")
                cur_spk, cur_words, cur_st = spk, [body], st
            elif cur_spk is None:
                cur_spk, cur_words, cur_st = spk, [body], st
            else:
                cur_words.append(body)
        if cur_spk and cur_words:
            paras.append(f"[{_fmt_clock(cur_st)}] {cur_spk}:\r\n{' '.join(cur_words)}")
        notes_str = "\r\n\r\n".join(paras)

    speakers_list: List[Dict[str, Any]] = []
    sentence_cues_list: List[Dict[str, Any]] = []
    markers: List[Dict[str, Any]] = []
    style = str(marker_style or "speakers").lower().strip()
    last_spk = None

    for s in in_range:
        spk = str(s.get("speaker", "Speaker"))
        st = float(s.get("start_sec", s_sec))
        eff_st = max(s_sec, st)
        rel_off = round(max(0.0, eff_st - s_sec), 4)
        c_hex = s.get("color_hex") if apply_speaker_color else None
        r_rgb = s.get("reaper_rgb") if apply_speaker_color else None
        c_int = reaper_color_from_hex(s.get("color_hex", "")) if apply_speaker_color else 0

        if style in ("speakers", "sentences"):
            if spk != last_spk or not speakers_list:
                speakers_list.append({
                    "speaker": spk,
                    "rel_offset_sec": rel_off,
                    "abs_start_sec": round(eff_st, 4),
                    "color_hex": c_hex,
                    "reaper_rgb": r_rgb,
                })

        if style == "sentences" and (st >= (s_sec - 0.15) and st <= (e_sec + 0.05)):
            sent_rel = round(max(0.0, st - s_sec), 4)
            prev = str(s.get("preview") or _build_phrase_preview(s.get("text", ""), spk))
            sentence_cues_list.append({
                "preview": prev,
                "speaker": spk,
                "rel_offset_sec": sent_rel,
                "abs_start_sec": round(st, 4),
                "color_hex": c_hex,
                "reaper_rgb": r_rgb,
            })
            if include_markers:
                lbl = f"{spk}: {prev}" if (last_spk != spk and prev and prev != spk) else prev
                markers.append({"rel_offset_sec": sent_rel, "name": lbl, "color": c_int})

        elif style == "speakers" and include_markers and (spk != last_spk):
            markers.append({"rel_offset_sec": rel_off, "name": spk, "color": c_int})

        last_spk = spk

    primary_hex = in_range[0].get("color_hex") if (apply_speaker_color and in_range) else None
    primary_rgb = in_range[0].get("reaper_rgb") if (apply_speaker_color and in_range) else None
    prim_col = reaper_color_from_hex(primary_hex) if primary_hex else 0

    return {
        "notes": notes_str,
        "speakers": speakers_list,
        "sentence_cues": sentence_cues_list,
        "markers": markers,
        "primary_color_hex": primary_hex,
        "primary_reaper_rgb": primary_rgb,
        "primary_color": prim_col,
    }


def build_reaper_cue_payload(
    main_win: Any,
    start_sec: float,
    end_sec: float,
    plain_text: str,
    title: str = "",
    clip_type: str = "selection",
    story_obj: Any = None,
    include_word_cues: bool = False,
    rendered_wav_path: str = "",
    marker_style: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a standardized cross-language cue dictionary conforming to the 1.0 schema."""
    s_sec = max(0.0, float(start_sec))
    e_sec = max(s_sec, float(end_sec))
    duration_sec = round(max(0.001, e_sec - s_sec), 4)

    app_version = "3.9.93-beta"
    try:
        import prs_shared
        app_version = getattr(prs_shared, "PROJECT_VERSION", app_version)
    except Exception:
        pass

    source_media = ""
    if hasattr(main_win, "audio_file") and main_win.audio_file:
        source_media = str(Path(main_win.audio_file).resolve())

    project_path = ""
    if hasattr(main_win, "project_file") and main_win.project_file:
        project_path = str(Path(main_win.project_file).resolve())

    fade_in_sec = 0.0
    fade_out_sec = 0.0
    fade_curve = "linear"
    story_title = str(title or "").strip()

    if story_obj is not None:
        if not story_title:
            story_title = str(getattr(story_obj, "title", "")).strip()
        fade_in_sec = float(getattr(story_obj, "fade_in", 0.0) or 0.0)
        fade_out_sec = float(getattr(story_obj, "fade_out", 0.0) or 0.0)
        fade_curve = str(getattr(story_obj, "fade_curve", "linear") or "linear")

    time_range_str = f"[{_fmt_clock(s_sec)} - {_fmt_clock(e_sec)}]"

    if story_title:
        take_name = f"{story_title} {time_range_str}"
    else:
        preview = " ".join((plain_text or "").strip().split())
        if len(preview) > 48:
            preview = preview[:45].rstrip() + "..."
        if preview:
            take_name = f"{preview} {time_range_str}"
        else:
            take_name = f"RTVS Clip {time_range_str}"

    resolved_marker_style = str(marker_style or "").strip().lower()
    if not resolved_marker_style:
        if hasattr(main_win, "settings_store") and main_win.settings_store:
            try:
                resolved_marker_style = str(main_win.settings_store.value("reaper_marker_style", "speakers") or "speakers").strip().lower()
            except Exception:
                resolved_marker_style = "speakers"
        else:
            resolved_marker_style = "speakers"

    if resolved_marker_style not in ("speakers", "sentences", "none"):
        resolved_marker_style = "speakers"

    apply_speaker_color = True
    if hasattr(main_win, "settings_store") and main_win.settings_store:
        try:
            c_val = main_win.settings_store.value("reaper_color_items", "true")
            apply_speaker_color = str(c_val).strip().lower() in ("1", "true", "yes")
        except Exception:
            apply_speaker_color = True

    all_sentences = _extract_formatted_transcript_sentences(main_win)
    clip_data = get_reaper_clip_notes_and_markers(
        main_win=main_win,
        start_sec=s_sec,
        end_sec=e_sec,
        marker_style=resolved_marker_style,
        apply_speaker_color=apply_speaker_color,
        include_notes=True,
        include_markers=True,
        precomputed_sentences=all_sentences,
    )

    speakers_list = clip_data["speakers"]
    sentence_cues_list = clip_data["sentence_cues"]
    primary_color_hex = clip_data["primary_color_hex"]
    reaper_native_rgb = clip_data["primary_reaper_rgb"]

    word_cues_list: List[Dict[str, Any]] = []
    if include_word_cues:
        for sent in [s for s in all_sentences if float(s.get("end_sec", 0.0)) > s_sec and float(s.get("start_sec", 0.0)) < e_sec]:
            spk_label = str(sent.get("speaker", "Speaker"))
            for w in sent.get("words", []):
                if not isinstance(w, dict):
                    continue
                w_st = float(w.get("start", 0.0))
                w_en = float(w.get("end", w_st))
                w_txt = str(w.get("word", "")).strip()
                if w_txt and w_en > s_sec and w_st < e_sec:
                    word_cues_list.append({
                        "word": w_txt,
                        "rel_offset_sec": round(max(0.0, w_st - s_sec), 4),
                        "abs_start_sec": round(w_st, 4),
                        "abs_end_sec": round(w_en, 4),
                        "speaker": spk_label,
                    })

    formatted_plain_text = clip_data["notes"] or str(plain_text or "").replace("\u2029", "\r\n\r\n").replace("\r\n", "\n").replace("\n", "\r\n").strip()

    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "app_version": app_version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_media_path": source_media,
        "project_path": project_path,
        "clip_type": clip_type,
        "title": story_title or (preview if 'preview' in locals() else "RTVS Clip"),
        "take_name": take_name,
        "start_sec": round(s_sec, 4),
        "end_sec": round(e_sec, 4),
        "duration_sec": duration_sec,
        "fade_in_sec": round(fade_in_sec, 4),
        "fade_out_sec": round(fade_out_sec, 4),
        "fade_curve": fade_curve,
        "plain_text": formatted_plain_text,
        "apply_speaker_color": apply_speaker_color,
        "speaker_color_hex": primary_color_hex if apply_speaker_color else None,
        "reaper_native_color_rgb": reaper_native_rgb if apply_speaker_color else None,
        "marker_style": resolved_marker_style,
        "speakers": speakers_list,
        "sentence_cues": sentence_cues_list,
        "word_cues": word_cues_list,
        "rendered_wav_path": str(rendered_wav_path or ""),
    }

    if main_win is not None:
        try:
            write_reaper_transcript_index(main_win, precomputed_sentences=all_sentences)
        except Exception:
            pass

    return payload


def get_reaper_index_paths() -> List[Path]:
    """Return IPC file paths for the full transcript and stories index used by the ReaImGui Dock."""
    paths: List[Path] = []
    try:
        app_idx = get_app_data_dir() / "reaper_ipc" / "latest_transcript_index.json"
        paths.append(app_idx)
    except Exception:
        pass
    try:
        tmp_idx = Path(tempfile.gettempdir()) / "rtvs3_reaper_index.json"
        if tmp_idx not in paths:
            paths.append(tmp_idx)
    except Exception:
        pass
    return paths


def write_reaper_transcript_index(main_win: Any, precomputed_sentences: Optional[List[Dict[str, Any]]] = None) -> List[Path]:
    """Emit the formatted project stories and sentence-level transcript index for REAPER companion scripts."""
    if main_win is None:
        return []

    source_media = ""
    if hasattr(main_win, "audio_file") and main_win.audio_file:
        source_media = str(Path(main_win.audio_file).resolve())

    project_path = ""
    if hasattr(main_win, "project_file") and main_win.project_file:
        project_path = str(Path(main_win.project_file).resolve())

    stories_out: List[Dict[str, Any]] = []
    for idx, st in enumerate(getattr(main_win, "stories", []) or []):
        s_sec = float(getattr(st, "start", 0.0) or 0.0)
        e_sec = float(getattr(st, "end", s_sec) or s_sec)
        stories_out.append({
            "index": idx,
            "title": str(getattr(st, "title", f"Story {idx + 1}")),
            "start_sec": round(s_sec, 4),
            "end_sec": round(e_sec, 4),
            "duration_sec": round(max(0.001, e_sec - s_sec), 4),
            "fade_in_sec": round(float(getattr(st, "fade_in", 0.0) or 0.0), 4),
            "fade_out_sec": round(float(getattr(st, "fade_out", 0.0) or 0.0), 4),
        })

    formatted_sentences = (
        precomputed_sentences
        if precomputed_sentences is not None
        else _extract_formatted_transcript_sentences(main_win)
    )

    index_payload = {
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_media_path": source_media,
        "project_path": project_path,
        "stories": stories_out,
        "segments": formatted_sentences,
        "sentences": formatted_sentences,
    }

    written: List[Path] = []
    raw_json = json.dumps(index_payload, indent=2, ensure_ascii=False)
    for target_path in get_reaper_index_paths():
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = target_path.with_name(f"{target_path.name}.tmp.{os.getpid()}")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(raw_json)
                f.flush()
                os.fsync(f.fileno())
            safe_replace(tmp_path, target_path)
            written.append(target_path)
        except Exception as exc:
            logger.debug(f"[REAPER BRIDGE] Could not write index file {target_path}: {exc}")
    return written


def write_reaper_sidecar_cue(payload: Dict[str, Any]) -> List[Path]:
    """Atomically write the cue payload JSON to all IPC sidecar locations."""
    written: List[Path] = []
    raw_json = json.dumps(payload, indent=2, ensure_ascii=False)

    for target_path in get_reaper_ipc_paths():
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temporary file alongside the target, then atomically safe_replace
            tmp_path = target_path.with_name(f"{target_path.name}.tmp.{os.getpid()}")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(raw_json)
                f.flush()
                os.fsync(f.fileno())
            safe_replace(tmp_path, target_path)
            written.append(target_path)
        except Exception as exc:
            logger.warning(f"[REAPER BRIDGE] Could not write IPC file to {target_path}: {exc}")

    return written


def attach_reaper_cue_to_mimedata(mime_data: Any, payload: Dict[str, Any]) -> None:
    """Encode cue payload as UTF-8 JSON into QMimeData and write atomic IPC sidecar."""
    try:
        from PySide6.QtCore import QByteArray
        raw_json = json.dumps(payload, ensure_ascii=False)
        qbyte = QByteArray(raw_json.encode("utf-8"))
        mime_data.setData(REAPER_CUE_MIME, qbyte)
    except Exception as exc:
        logger.warning(f"[REAPER BRIDGE] Failed to attach QMimeData payload: {exc}")

    # Emit atomic sidecar file so ReaScript can pick it up without depending on QMimeData
    write_reaper_sidecar_cue(payload)


def get_default_reaper_scripts_dir() -> Path:
    """Return the standard platform-specific default REAPER Scripts/RTVS3 directory."""
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "REAPER" / "Scripts" / "RTVS3"
        return Path.home() / "AppData" / "Roaming" / "REAPER" / "Scripts" / "RTVS3"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "REAPER" / "Scripts" / "RTVS3"
    else:
        # Linux / XDG
        xdg_cfg = os.environ.get("XDG_CONFIG_HOME")
        if xdg_cfg:
            return Path(xdg_cfg) / "REAPER" / "Scripts" / "RTVS3"
        return Path.home() / ".config" / "REAPER" / "Scripts" / "RTVS3"


def get_bundled_lua_scripts() -> Dict[str, Path]:
    """Find the bundled RTVS3 ReaScript Lua files."""
    base_dir = Path(__file__).resolve().parent / "scripts" / "reaper"
    scripts: Dict[str, Path] = {}
    for name in (
        "rtvs_reaper_companion.lua",
        "rtvs_reaper_sync.lua",
        "rtvs_reaper_auto_sync.lua",
        "rtvs_reaper_dock.lua",
    ):
        p = base_dir / name
        if p.is_file():
            scripts[name] = p
    return scripts


def install_reaper_scripts_to_resource_path(
    parent_widget: Any = None,
    target_dir: Optional[Path] = None,
) -> Tuple[bool, str, List[Path]]:
    """Copy the RTVS3 ReaScript companion and dock scripts to the REAPER Scripts directory.

    If target_dir is not provided, auto-detects standard REAPER installation paths.
    If the auto-detected directory does not exist and interactive GUI is active, prompts
    the user with a directory selection dialog.
    """
    dest_dir = target_dir or get_default_reaper_scripts_dir()
    bundled = get_bundled_lua_scripts()
    if not bundled:
        msg = "Bundled Lua scripts (rtvs_reaper_companion.lua, rtvs_reaper_dock.lua) not found."
        return False, msg, []

    # If parent REAPER directory does not exist and we are interactive, ask user to locate it
    if target_dir is None and not dest_dir.parent.is_dir():
        if parent_widget is not None:
            try:
                from PySide6.QtWidgets import QFileDialog, QMessageBox
                choice = QMessageBox.question(
                    parent_widget,
                    "REAPER Scripts Directory Not Found",
                    f"Default REAPER Scripts directory was not detected at:\n{dest_dir.parent}\n\n"
                    "Would you like to locate your REAPER resource directory manually?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                )
                if choice == QMessageBox.StandardButton.Yes:
                    selected = QFileDialog.getExistingDirectory(
                        parent_widget,
                        "Select REAPER Scripts Directory",
                        str(Path.home()),
                    )
                    if selected:
                        dest_dir = Path(selected) / "RTVS3"
                    else:
                        return False, "Installation cancelled by user.", []
                else:
                    return False, "Installation cancelled.", []
            except Exception:
                pass

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        msg = f"Failed to create directory {dest_dir}: {exc}"
        return False, msg, []

    installed_files: List[Path] = []
    import shutil
    for fname, src_path in bundled.items():
        out_path = dest_dir / fname
        try:
            shutil.copy2(src_path, out_path)
            installed_files.append(out_path)
        except Exception as exc:
            msg = f"Failed to copy {fname} to {dest_dir}: {exc}"
            return False, msg, installed_files

    summary = (
        f"Successfully installed {len(installed_files)} RTVS3 ReaScript file(s) to:\n{dest_dir}\n\n"
        "In REAPER:\n"
        "1. Open Actions > Show action list (or press '?')\n"
        "2. Click 'New action...' > 'Load ReaScript...'\n"
        "3. Select 'rtvs_reaper_companion.lua' to bind a shortcut or toolbar button\n"
        "4. (Optional) Select 'rtvs_reaper_dock.lua' to run the dockable transcript browser."
    )
    if parent_widget is not None:
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(parent_widget, "REAPER Scripts Installed", summary)
        except Exception:
            pass

    return True, summary, installed_files


def render_temp_daw_wav_clip(
    main_win: Any,
    start_sec: float,
    end_sec: float,
    title: str = "",
) -> Optional[Path]:
    """Render a temporary uncompressed WAV slice of the selected range for universal DAW clipboard paste."""
    if main_win is None or not getattr(main_win, "audio_file", None):
        return None

    src_media = getattr(main_win, "audio_file")
    s_sec = max(0.0, float(start_sec))
    e_sec = max(s_sec, float(end_sec))
    dur = max(0.001, e_sec - s_sec)

    safe_title = "".join(c for c in (title or "rtvs_clip") if c.isalnum() or c in ("-", "_")).strip() or "rtvs_clip"
    out_dir = Path(tempfile.gettempdir()) / "rtvs3_daw_clips"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    out_file = out_dir / f"{safe_title}_{s_sec:.2f}_{e_sec:.2f}.wav"

    try:
        from core_utils import ffmpeg_path
        ff_bin = ffmpeg_path() or "ffmpeg"
        cmd = [
            ff_bin, "-y", "-nostats", "-loglevel", "error",
            "-ss", str(s_sec), "-i", str(src_media),
            "-t", str(dur), "-vn", "-c:a", "pcm_s16le",
            str(out_file)
        ]
        import subprocess
        creation_flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags, timeout=60)
        if res.returncode == 0 and out_file.is_file() and out_file.stat().st_size > 0:
            return out_file
    except Exception as exc:
        logger.warning(f"[REAPER BRIDGE] Failed to render temp DAW WAV clip: {exc}")

    return None


def copy_selection_as_daw_wav_clip(
    main_win: Any,
    start_sec: float,
    end_sec: float,
    plain_text: str,
    html_text: str = "",
    title: str = "",
    story_obj: Any = None,
) -> Optional[Path]:
    """Render a temp WAV audio slice and attach it to the OS file clipboard (CF_HDROP / URLs)
    alongside plain text, rich HTML, and REAPER JSON cue payloads for universal DAW compatibility.
    """
    wav_path = render_temp_daw_wav_clip(main_win, start_sec, end_sec, title)

    try:
        from PySide6.QtCore import QMimeData, QUrl, QThread
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None and hasattr(app, "thread") and callable(getattr(app, "thread", None)) and QThread.currentThread() == app.thread():
            mime_data = QMimeData()
            if plain_text:
                mime_data.setText(plain_text)
            if html_text:
                mime_data.setHtml(html_text)

            # Build REAPER cue with rendered_wav_path populated
            payload = build_reaper_cue_payload(
                main_win=main_win,
                start_sec=start_sec,
                end_sec=end_sec,
                plain_text=plain_text,
                title=title,
                clip_type="story" if story_obj is not None else "selection",
                story_obj=story_obj,
                rendered_wav_path=str(wav_path) if wav_path else "",
            )
            attach_reaper_cue_to_mimedata(mime_data, payload)

            # Set file URLs for OS clipboard / DAW drag-and-drop paste
            if wav_path and wav_path.is_file():
                url = QUrl.fromLocalFile(str(wav_path.resolve()))
                mime_data.setUrls([url])

            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setMimeData(mime_data)

            if hasattr(main_win, "statusBar") and main_win.statusBar():
                f_name = wav_path.name if wav_path else "clip"
                main_win.statusBar().showMessage(
                    f"Copied DAW audio clip ({f_name}) and transcript to OS clipboard.",
                    4000,
                )
    except Exception as exc:
        logger.warning(f"[REAPER BRIDGE] Error in copy_selection_as_daw_wav_clip: {exc}")

    return wav_path


def populate_unified_copy_mimedata(
    main_win: Any,
    mime_data: Any,
    start_sec: Optional[float] = None,
    end_sec: Optional[float] = None,
    plain_text: str = "",
    title: str = "",
    clip_type: str = "selection",
    story_obj: Any = None,
) -> None:
    """Populates QMimeData with REAPER JSON cue payloads and optional WAV file attachments
    according to active user preferences, enabling unified, clutter-free single-shortcut copy.
    """
    if mime_data is None:
        return

    # Check if time boundaries are valid
    has_valid_time = (
        start_sec is not None
        and end_sec is not None
        and float(end_sec) > float(start_sec)
    )

    if not has_valid_time:
        return

    s_sec = float(start_sec)
    e_sec = float(end_sec)

    # 1. Check user preferences for REAPER sidecar (standard Ctrl+C is strictly text/metadata)
    settings = getattr(main_win, "settings_store", None)
    auto_reaper = True

    if settings is not None:
        try:
            val_r = settings.value("reaper_auto_sidecar", "true")
            auto_reaper = str(val_r).strip().lower() in ("1", "true", "yes")
        except Exception:
            auto_reaper = True

    # Note: Standard Ctrl+C NEVER attaches OS file URLs (CF_HDROP) so pasting into
    # text editors, chat windows, and browsers remains 100% text-only.
    # Dedicated audio clip rendering is triggered explicitly via Ctrl+Shift+C.
    rendered_wav = ""

    # 2. Attach REAPER cue payload if enabled
    if auto_reaper:
        try:
            payload = build_reaper_cue_payload(
                main_win=main_win,
                start_sec=s_sec,
                end_sec=e_sec,
                plain_text=plain_text,
                title=title,
                clip_type=clip_type,
                story_obj=story_obj,
                rendered_wav_path=rendered_wav,
            )
            attach_reaper_cue_to_mimedata(mime_data, payload)
        except Exception as exc:
            logger.warning(f"[REAPER BRIDGE] Error attaching unified REAPER cue: {exc}")


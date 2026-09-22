"""Google Docs Document Serializer and Formatting Engine.

Converts transcripts, speaker turns, story segmentations, and metadata
into native Google Docs REST API structures (UTF-16 indexed batchUpdate requests).
Emulates the layout and styling of DOCX and WordPress exports:
- Natural paragraph grouping by speaker turns and sentence boundaries
- Bold inline speaker labels (SPEAKER: text)
- Bracketed timecodes [00:01:23] in muted styling
- Story chapter headers with time range annotations
- Native margin comments for editorial notes
- Support for full episode, selected stories, all stories, and full + stories
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

MIN_WORDS_PER_PARAGRAPH = 35


def format_time(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS string."""
    if seconds is None:
        return "00:00"
    try:
        s = max(0.0, float(seconds))
        hrs = int(s // 3600)
        mins = int((s % 3600) // 60)
        secs = int(s % 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
    except Exception:
        return "00:00"


def utf16_len(s: str) -> int:
    """Return the length of a string in UTF-16 code units.
    Google Docs REST API requires character offsets indexed by UTF-16 code units.
    """
    return len(s.encode("utf-16-le")) // 2


def is_sentence_end(word: str) -> bool:
    """Check if word ends with terminal punctuation."""
    w = word.strip().rstrip("\"'’”»)")
    return bool(w and w[-1] in ".?!")


def clean_transcript_text(text: str, current_speaker: str = "", all_speakers: Optional[List[str]] = None) -> str:
    """Strip redundant baked-in speaker labels from the start of segment text."""
    text = str(text or "").strip()
    if not text:
        return ""

    candidates = set()
    if current_speaker:
        candidates.add(str(current_speaker).strip())
    if all_speakers:
        for s in all_speakers:
            if s and str(s).strip():
                candidates.add(str(s).strip())

    candidates = sorted((c for c in candidates if c), key=len, reverse=True)
    if not candidates:
        return text

    changed = True
    while changed:
        changed = False
        for name in candidates:
            pattern = rf"^\s*(?:\[{re.escape(name)}\]|\({re.escape(name)}\)|{re.escape(name)})\s*[:\-\—]?\s*"
            new_text = re.sub(pattern, "", text, count=1, flags=re.IGNORECASE)
            if new_text != text:
                text = new_text.strip()
                changed = True
                break
    return text


def build_coherent_blocks(
    segments: List[Dict[str, Any]],
    main_window: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Group whisper/asr segments into coherent speaker-turn paragraphs matching DOCX export layout."""
    if not segments:
        return []

    # If main_window provides build_story_blocks, use its authoritative implementation
    if main_window and hasattr(main_window, "build_story_blocks"):
        try:
            return main_window.build_story_blocks(segments)
        except Exception:
            pass

    # Extract all known speaker labels for stripping baked-in prefixes
    known_speakers = []
    if main_window:
        spk_names = getattr(main_window, "speaker_names", {}) or {}
        known_speakers.extend(spk_names.values())

    word_tokens = []
    for seg_idx, segment in enumerate(segments):
        start = segment.get("start", 0.0) if isinstance(segment, dict) else getattr(segment, "start", 0.0)
        end = segment.get("end", start) if isinstance(segment, dict) else getattr(segment, "end", start)
        source_idx = segment.get("_source_index", seg_idx)

        # Resolve speaker label
        spk_name = ""
        if main_window and hasattr(main_window, "get_effective_speaker_name"):
            try:
                spk_name = main_window.get_effective_speaker_name(source_idx, segment)
            except Exception:
                pass
        if not spk_name and isinstance(segment, dict):
            spk_name = segment.get("speaker", "")
            if main_window and hasattr(main_window, "speaker_names"):
                spk_name = main_window.speaker_names.get(spk_name, spk_name)

        spk_name = (spk_name or "").strip()

        words = segment.get("words", []) if isinstance(segment, dict) else []
        if words:
            for w in words:
                w_text = w.get("word", "").strip() if isinstance(w, dict) else str(w).strip()
                if not w_text or (isinstance(w, dict) and bool(w.get("deleted", False))):
                    continue
                w_dict = {
                    "word": w_text,
                    "start": w.get("start", start) if isinstance(w, dict) else start,
                    "end": w.get("end", end) if isinstance(w, dict) else end,
                    "seg_idx": source_idx,
                    "speaker_name": spk_name,
                }
                if isinstance(w, dict):
                    for k in ("bold", "italic", "underline", "strike", "highlight"):
                        if w.get(k):
                            w_dict[k] = w[k]
                word_tokens.append(w_dict)
        else:
            seg_text = segment.get("text", "").strip() if isinstance(segment, dict) else ""
            cleaned = clean_transcript_text(seg_text, spk_name, known_speakers)
            for w in cleaned.split():
                word_tokens.append({
                    "word": w,
                    "start": start,
                    "end": end,
                    "seg_idx": source_idx,
                    "speaker_name": spk_name,
                })

    if not word_tokens:
        return []

    blocks = []
    curr_para_words: List[Dict[str, Any]] = []
    curr_speaker_name: Optional[str] = None
    last_rendered_speaker_name: Optional[str] = None

    def flush_para():
        nonlocal curr_para_words, curr_speaker_name, last_rendered_speaker_name
        if not curr_para_words:
            return

        p_text = " ".join(t["word"] for t in curr_para_words).strip()
        p_text = clean_transcript_text(p_text, curr_speaker_name, known_speakers)
        if p_text:
            is_change = (curr_speaker_name != last_rendered_speaker_name)
            para_source_indices = []
            for t in curr_para_words:
                s_idx = t.get("seg_idx")
                if s_idx is not None and s_idx not in para_source_indices:
                    para_source_indices.append(s_idx)

            # Comments
            para_comments = []
            for s in segments:
                if isinstance(s, dict):
                    s_idx = s.get("_source_index", s.get("seg_idx"))
                    if s_idx in para_source_indices:
                        c = (s.get("comments") or s.get("notes", "")).strip()
                        if c and c not in para_comments:
                            para_comments.append(c)

            block_dict: Dict[str, Any] = {
                "speaker": curr_speaker_name or "",
                "text": p_text,
                "start": curr_para_words[0]["start"],
                "end": curr_para_words[-1]["end"],
                "is_speaker_change": is_change,
                "_source_index": para_source_indices[0] if para_source_indices else None,
                "source_indices": para_source_indices,
                "words": curr_para_words,
            }
            if para_comments:
                block_dict["comments"] = "\n".join(para_comments)
                block_dict["notes"] = block_dict["comments"]

            blocks.append(block_dict)
            last_rendered_speaker_name = curr_speaker_name
        curr_para_words = []

    for token in word_tokens:
        spk_name = token["speaker_name"]
        if curr_speaker_name is None:
            curr_speaker_name = spk_name

        if not spk_name and curr_speaker_name:
            spk_name = curr_speaker_name

        speaker_changed = (spk_name != curr_speaker_name)
        word_count_exceeded = (len(curr_para_words) >= MIN_WORDS_PER_PARAGRAPH)
        prev_ended = curr_para_words and is_sentence_end(curr_para_words[-1]["word"])

        if curr_para_words and (speaker_changed or (word_count_exceeded and prev_ended)):
            flush_para()
            curr_para_words = [token]
            curr_speaker_name = spk_name
        else:
            curr_para_words.append(token)

    if curr_para_words:
        flush_para()

    return blocks


class GoogleDocsSerializer:
    """Serializes broadcast news transcript projects into Google Docs batchUpdate payloads."""

    def __init__(self):
        pass

    def serialize_document(
        self,
        document_title: str,
        stories: List[Any],
        transcript_segments: List[Dict[str, Any]],
        project_metadata: Optional[Dict[str, Any]] = None,
        scope: str = "full",
        selected_story_indices: Optional[List[int]] = None,
        main_window: Optional[Any] = None,
        include_speakers: bool = True,
        bold_speakers: bool = True,
        include_story_chapters: bool = False,
        include_timestamps: bool = True,
        include_word_timestamps: bool = False,
        include_comments: bool = True,
        include_highlights: bool = True,
        lang_code: str = "en",
        secondary_segments: Optional[List[Dict[str, Any]]] = None,
        secondary_title: Optional[str] = None,
        secondary_lang_code: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate plain document text, Google Docs batchUpdate requests, and comment anchor points.

        Returns:
            (full_text, batch_update_requests, comment_anchors)
        """
        full_text = ""
        para_requests: List[Dict[str, Any]] = []
        text_requests: List[Dict[str, Any]] = []
        comment_anchors: List[Dict[str, Any]] = []

        cursor = 1

        # 1. Document Title
        title_text = f"{document_title}\n"
        title_start = cursor
        title_end = cursor + utf16_len(title_text)
        full_text += title_text
        cursor = title_end

        para_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": title_start, "endIndex": title_end},
                "paragraphStyle": {"namedStyleType": "TITLE", "spaceBelow": {"magnitude": 10, "unit": "PT"}},
                "fields": "namedStyleType,spaceBelow",
            }
        })
        text_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": title_start, "endIndex": title_end - 1},
                "textStyle": {
                    "bold": True,
                    "fontSize": {"magnitude": 22, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.18, "blue": 0.36}}},
                },
                "fields": "bold,fontSize,foregroundColor",
            }
        })

        # 2. Metadata Header Block
        meta_lines = []
        if project_metadata:
            source = project_metadata.get("media_filename") or project_metadata.get("filename")
            if source:
                import os
                meta_lines.append(f"Recording: {os.path.basename(source)}")
            dur = project_metadata.get("duration")
            if dur is not None and isinstance(dur, (int, float)) and dur > 0:
                meta_lines.append(f"Duration: {format_time(dur)}")
            lang = project_metadata.get("language") or lang_code
            if lang:
                meta_lines.append(f"Language: {str(lang).upper()}")
            if stories:
                meta_lines.append(f"Stories: {len(stories)}")

        if meta_lines:
            meta_text = " • ".join(meta_lines) + "\n\n"
            meta_start = cursor
            meta_end = cursor + utf16_len(meta_text)
            full_text += meta_text
            cursor = meta_end

            text_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": meta_start, "endIndex": meta_end - 1},
                    "textStyle": {
                        "italic": True,
                        "fontSize": {"magnitude": 10, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.45, "blue": 0.52}}},
                    },
                    "fields": "italic,fontSize,foregroundColor",
                }
            })

        # Determine target stories based on scope
        effective_stories = []
        if scope == "selected_stories":
            if selected_story_indices is not None and len(selected_story_indices) > 0:
                for idx in selected_story_indices:
                    if 0 <= idx < len(stories):
                        effective_stories.append((idx + 1, stories[idx]))
            elif stories:
                # If scope is selected_stories but no indices specified, use first or active
                effective_stories = [(1, stories[0])]
        elif scope in ("all_stories", "full_and_all_stories", "full"):
            effective_stories = [(i + 1, s) for i, s in enumerate(stories)]

        def render_story_blocks(blocks: List[Dict[str, Any]], story_num: Optional[int] = None):
            nonlocal cursor, full_text, para_requests, text_requests, comment_anchors
            last_speaker = None

            for block in blocks:
                speaker = (block.get("speaker") or "").strip() if include_speakers else ""
                p_text = block.get("text", "").strip()
                if not p_text:
                    continue

                if speaker:
                    p_text = clean_transcript_text(p_text, current_speaker=speaker)

                b_start = cursor

                # A. Timecode prefix [00:01:23]
                time_prefix = ""
                if include_timestamps and block.get("start") is not None:
                    time_prefix = f"[{format_time(block['start'])}] "
                    t_start = cursor
                    t_end = cursor + utf16_len(time_prefix)
                    full_text += time_prefix
                    cursor = t_end

                    text_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": t_start, "endIndex": t_end},
                            "textStyle": {
                                "fontSize": {"magnitude": 9.5, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.42, "green": 0.45, "blue": 0.49}}},
                            },
                            "fields": "fontSize,foregroundColor",
                        }
                    })

                # B. Inline Speaker prefix (Speaker Name: ) - ALWAYS BOLD
                is_change = block.get("is_speaker_change", (speaker != last_speaker))
                spk_prefix = ""
                if speaker and (is_change or speaker != last_speaker):
                    spk_prefix = f"{speaker}: "
                    s_start = cursor
                    s_end = cursor + utf16_len(spk_prefix)
                    full_text += spk_prefix
                    cursor = s_end

                    text_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": s_start, "endIndex": s_end},
                            "textStyle": {
                                "bold": True,
                                "fontSize": {"magnitude": 11, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.12, "blue": 0.2}}},
                            },
                            "fields": "bold,fontSize,foregroundColor",
                        }
                    })
                    last_speaker = speaker

                # C. Body text
                body_str = p_text + "\n\n"
                p_body_start = cursor
                p_body_end = cursor + utf16_len(body_str)
                full_text += body_str
                cursor = p_body_end

                # Normal Paragraph Styling: paragraph margins and line spacing
                para_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": b_start, "endIndex": p_body_end},
                        "paragraphStyle": {
                            "lineSpacing": 115,
                            "spaceBelow": {"magnitude": 6, "unit": "PT"},
                        },
                        "fields": "lineSpacing,spaceBelow",
                    }
                })

                # Rich Highlights or Formatting if words exist
                if include_highlights and block.get("words"):
                    w_cursor = p_body_start
                    for w in block["words"]:
                        w_str = w.get("word", "")
                        w_len = utf16_len(w_str)
                        if w.get("highlight"):
                            text_requests.append({
                                "updateTextStyle": {
                                    "range": {"startIndex": w_cursor, "endIndex": w_cursor + w_len},
                                    "textStyle": {
                                        "backgroundColor": {"color": {"rgbColor": {"red": 1.0, "green": 0.95, "blue": 0.6}}},
                                    },
                                    "fields": "backgroundColor",
                                }
                            })
                        if w.get("bold"):
                            text_requests.append({
                                "updateTextStyle": {
                                    "range": {"startIndex": w_cursor, "endIndex": w_cursor + w_len},
                                    "textStyle": {"bold": True},
                                    "fields": "bold",
                                }
                            })
                        if w.get("italic"):
                            text_requests.append({
                                "updateTextStyle": {
                                    "range": {"startIndex": w_cursor, "endIndex": w_cursor + w_len},
                                    "textStyle": {"italic": True},
                                    "fields": "italic",
                                }
                            })
                        w_cursor += w_len + 1  # space between words

                # Margin Comments on Paragraph
                if include_comments and (block.get("comments") or block.get("notes")):
                    c_note = (block.get("comments") or block.get("notes", "")).strip()
                    if c_note:
                        comment_anchors.append({
                            "type": "paragraph_note",
                            "story_id": story_num,
                            "text": c_note,
                            "start_index": b_start,
                            "end_index": p_body_end - 2,
                            "quoted_text": p_text[:120],
                        })

        # 3. Render according to scope
        if scope == "full" or not effective_stories:
            if effective_stories and scope == "full" and include_story_chapters:
                # Include story chapters as H2 headings for Table of Contents navigation
                sorted_stories = sorted(
                    effective_stories,
                    key=lambda pair: getattr(pair[1], "start", 0.0) if not isinstance(pair[1], dict) else pair[1].get("start", 0.0)
                )

                # A. Segments before first story (if any)
                first_st_start = getattr(sorted_stories[0][1], "start", 0.0) if not isinstance(sorted_stories[0][1], dict) else sorted_stories[0][1].get("start", 0.0)
                intro_segs = [s for s in transcript_segments if s.get("end", 0.0) <= first_st_start + 0.05 and s.get("start", 0.0) < first_st_start - 0.05]
                if intro_segs:
                    intro_blocks = build_coherent_blocks(intro_segs, main_window=main_window)
                    render_story_blocks(intro_blocks)

                # B. Stories with H2 Headers
                for s_num, story in sorted_stories:
                    s_title = (
                        getattr(story, "name", None)
                        or getattr(story, "title", None)
                        or (story.get("name") or story.get("title") if isinstance(story, dict) else None)
                        or f"Story {s_num}"
                    )
                    s_start = getattr(story, "start", 0.0) or (story.get("start", 0.0) if isinstance(story, dict) else 0.0)
                    s_end = getattr(story, "end", 0.0) or (story.get("end", 0.0) if isinstance(story, dict) else 0.0)
                    s_notes = getattr(story, "notes", None) or (story.get("notes") if isinstance(story, dict) else "")

                    time_range = f"[{format_time(s_start)} – {format_time(s_end)}]" if include_timestamps else ""
                    header_text = f"Story {s_num}: {s_title} {time_range}".strip() + "\n"
                    sec_start = cursor
                    sec_end = cursor + utf16_len(header_text)
                    full_text += header_text
                    cursor = sec_end

                    para_requests.append({
                        "updateParagraphStyle": {
                            "range": {"startIndex": sec_start, "endIndex": sec_end},
                            "paragraphStyle": {
                                "namedStyleType": "HEADING_2",
                                "spaceAbove": {"magnitude": 16, "unit": "PT"},
                                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                            },
                            "fields": "namedStyleType,spaceAbove,spaceBelow",
                        }
                    })
                    text_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": sec_start, "endIndex": sec_end - 1},
                            "textStyle": {
                                "bold": True,
                                "fontSize": {"magnitude": 14, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.02, "green": 0.45, "blue": 0.70}}},
                            },
                            "fields": "bold,fontSize,foregroundColor",
                        }
                    })

                    if s_notes and include_comments:
                        comment_anchors.append({
                            "type": "story_notes",
                            "story_id": s_num,
                            "title": s_title,
                            "text": s_notes,
                            "start_index": sec_start,
                            "end_index": sec_end - 1,
                            "quoted_text": header_text.strip(),
                        })

                    story_segs = [
                        seg for seg in transcript_segments
                        if (seg.get("start", 0.0) >= s_start - 0.05 and seg.get("end", 0.0) <= s_end + 0.05)
                        or (s_start <= seg.get("start", 0.0) < s_end)
                    ]
                    if story_segs:
                        story_blocks = build_coherent_blocks(story_segs, main_window=main_window)
                        render_story_blocks(story_blocks, story_num=s_num)

                # C. Segments after last story (if any)
                last_st_end = getattr(sorted_stories[-1][1], "end", 0.0) if not isinstance(sorted_stories[-1][1], dict) else sorted_stories[-1][1].get("end", 0.0)
                outro_segs = [s for s in transcript_segments if s.get("start", 0.0) >= last_st_end - 0.05]
                if outro_segs:
                    outro_blocks = build_coherent_blocks(outro_segs, main_window=main_window)
                    render_story_blocks(outro_blocks)

            else:
                # Default: clean continuous full episode transcript without story chapters
                full_blocks = build_coherent_blocks(transcript_segments, main_window=main_window)
                render_story_blocks(full_blocks)

                # If stories have notes and comments requested, anchor to story's starting block
                if effective_stories and include_comments:
                    for s_num, story in effective_stories:
                        s_notes = getattr(story, "notes", None) or (story.get("notes") if isinstance(story, dict) else "")
                        if not s_notes:
                            continue
                        s_title = (
                            getattr(story, "name", None)
                            or getattr(story, "title", None)
                            or (story.get("name") or story.get("title") if isinstance(story, dict) else None)
                            or f"Story {s_num}"
                        )
                        b_anchor_start = 1
                        b_anchor_end = min(len(full_text), b_anchor_start + 50)
                        comment_anchors.append({
                            "type": "story_notes",
                            "story_id": s_num,
                            "title": s_title,
                            "text": s_notes,
                            "start_index": b_anchor_start,
                            "end_index": b_anchor_end,
                            "quoted_text": full_text[b_anchor_start:b_anchor_end].strip(),
                        })

        elif scope in ("all_stories", "selected_stories"):
            for s_num, story in effective_stories:
                s_title = (
                    getattr(story, "name", None)
                    or getattr(story, "title", None)
                    or (story.get("name") or story.get("title") if isinstance(story, dict) else None)
                    or f"Story {s_num}"
                )
                s_start = getattr(story, "start", 0.0) or (story.get("start", 0.0) if isinstance(story, dict) else 0.0)
                s_end = getattr(story, "end", 0.0) or (story.get("end", 0.0) if isinstance(story, dict) else 0.0)
                s_notes = getattr(story, "notes", None) or (story.get("notes") if isinstance(story, dict) else "")

                # Story Header - H2 Header
                time_range = f"[{format_time(s_start)} – {format_time(s_end)}]" if include_timestamps else ""
                header_text = f"Story {s_num}: {s_title} {time_range}".strip() + "\n"
                sec_start = cursor
                sec_end = cursor + utf16_len(header_text)
                full_text += header_text
                cursor = sec_end

                para_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": sec_start, "endIndex": sec_end},
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_2",
                            "spaceAbove": {"magnitude": 16, "unit": "PT"},
                            "spaceBelow": {"magnitude": 6, "unit": "PT"},
                        },
                        "fields": "namedStyleType,spaceAbove,spaceBelow",
                    }
                })
                text_requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": sec_start, "endIndex": sec_end - 1},
                        "textStyle": {
                            "bold": True,
                            "fontSize": {"magnitude": 14, "unit": "PT"},
                            "foregroundColor": {"color": {"rgbColor": {"red": 0.02, "green": 0.45, "blue": 0.70}}},
                        },
                        "fields": "bold,fontSize,foregroundColor",
                    }
                })

                if s_notes and include_comments:
                    comment_anchors.append({
                        "type": "story_notes",
                        "story_id": s_num,
                        "title": s_title,
                        "text": s_notes,
                        "start_index": sec_start,
                        "end_index": sec_end - 1,
                        "quoted_text": header_text.strip(),
                    })

                # Filter segments for this story
                story_segs = [
                    seg for seg in transcript_segments
                    if (seg.get("start", 0.0) >= s_start - 0.05 and seg.get("end", 0.0) <= s_end + 0.05)
                    or (s_start <= seg.get("start", 0.0) < s_end)
                ]
                if not story_segs and len(effective_stories) == 1:
                    story_segs = transcript_segments

                story_blocks = build_coherent_blocks(story_segs, main_window=main_window)
                render_story_blocks(story_blocks, story_num=s_num)

        elif scope == "full_and_all_stories":
            # 1. Full Episode Section
            ep_hdr = "Full Episode Transcript\n"
            h_start = cursor
            h_end = cursor + utf16_len(ep_hdr)
            full_text += ep_hdr
            cursor = h_end

            para_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": h_start, "endIndex": h_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_1", "spaceAbove": {"magnitude": 14, "unit": "PT"}},
                    "fields": "namedStyleType,spaceAbove",
                }
            })
            text_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": h_start, "endIndex": h_end - 1},
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": 16, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.18, "blue": 0.36}}},
                    },
                    "fields": "bold,fontSize,foregroundColor",
                }
            })

            full_blocks = build_coherent_blocks(transcript_segments, main_window=main_window)
            render_story_blocks(full_blocks)

            # 2. Individual Story Chapters Section
            if effective_stories:
                ch_hdr = "Story Segments & Chapters\n"
                ch_start = cursor
                ch_end = cursor + utf16_len(ch_hdr)
                full_text += ch_hdr
                cursor = ch_end

                para_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": ch_start, "endIndex": ch_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_1", "spaceAbove": {"magnitude": 18, "unit": "PT"}},
                        "fields": "namedStyleType,spaceAbove",
                    }
                })
                text_requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": ch_start, "endIndex": ch_end - 1},
                        "textStyle": {
                            "bold": True,
                            "fontSize": {"magnitude": 16, "unit": "PT"},
                            "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.18, "blue": 0.36}}},
                        },
                        "fields": "bold,fontSize,foregroundColor",
                    }
                })

                for s_num, story in effective_stories:
                    s_title = getattr(story, "title", None) or (story.get("title") if isinstance(story, dict) else f"Story {s_num}")
                    s_start = getattr(story, "start", 0.0) or (story.get("start", 0.0) if isinstance(story, dict) else 0.0)
                    s_end = getattr(story, "end", 0.0) or (story.get("end", 0.0) if isinstance(story, dict) else 0.0)
                    s_notes = getattr(story, "notes", None) or (story.get("notes") if isinstance(story, dict) else "")

                    header_text = f"Story {s_num}: {s_title} [{format_time(s_start)} – {format_time(s_end)}]\n"
                    sec_start = cursor
                    sec_end = cursor + utf16_len(header_text)
                    full_text += header_text
                    cursor = sec_end

                    para_requests.append({
                        "updateParagraphStyle": {
                            "range": {"startIndex": sec_start, "endIndex": sec_end},
                            "paragraphStyle": {
                                "namedStyleType": "HEADING_2",
                                "spaceAbove": {"magnitude": 16, "unit": "PT"},
                                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                            },
                            "fields": "namedStyleType,spaceAbove,spaceBelow",
                        }
                    })
                    text_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": sec_start, "endIndex": sec_end - 1},
                            "textStyle": {
                                "bold": True,
                                "fontSize": {"magnitude": 14, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.02, "green": 0.45, "blue": 0.70}}},
                            },
                            "fields": "bold,fontSize,foregroundColor",
                        }
                    })

                    if s_notes and include_comments:
                        comment_anchors.append({
                            "type": "story_notes",
                            "story_id": s_num,
                            "title": s_title,
                            "text": s_notes,
                            "start_index": sec_start,
                            "end_index": sec_end - 1,
                            "quoted_text": header_text.strip(),
                        })

                    story_segs = [
                        seg for seg in transcript_segments
                        if (seg.get("start", 0.0) >= s_start - 0.05 and seg.get("end", 0.0) <= s_end + 0.05)
                        or (s_start <= seg.get("start", 0.0) < s_end)
                    ]
                    story_blocks = build_coherent_blocks(story_segs, main_window=main_window)
                    render_story_blocks(story_blocks, story_num=s_num)

        # 4. Optional Secondary / Bilingual Language Section
        if secondary_segments:
            sec_sec_title = secondary_title or ("Spanish Translation" if str(secondary_lang_code).lower() == "es" else "English Translation")
            sec_hdr_text = f"\n\n--- {sec_sec_title} ---\n\n"
            sec_hdr_start = cursor
            sec_hdr_end = cursor + utf16_len(sec_hdr_text)
            full_text += sec_hdr_text
            cursor = sec_hdr_end

            para_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": sec_hdr_start, "endIndex": sec_hdr_end},
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "spaceAbove": {"magnitude": 20, "unit": "PT"},
                        "spaceBelow": {"magnitude": 10, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceAbove,spaceBelow",
                }
            })
            text_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": sec_hdr_start, "endIndex": sec_hdr_end - 1},
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": 16, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.18, "blue": 0.36}}},
                    },
                    "fields": "bold,fontSize,foregroundColor",
                }
            })

            sec_blocks = build_coherent_blocks(secondary_segments, main_window=main_window)
            render_story_blocks(sec_blocks)

        # 5. Insert text request must be first in batchUpdate, followed by all paragraph styling, followed by character text styling
        insert_request = {
            "insertText": {
                "location": {"index": 1},
                "text": full_text,
            }
        }
        all_requests = [insert_request] + para_requests + text_requests

        return full_text, all_requests, comment_anchors


def create_google_doc(
    access_token: str,
    title: str,
    folder_id: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Create a new Google Doc via Google Docs REST API and optionally place in folder.

    Returns:
        (success, doc_id_or_error, doc_metadata)
    """
    create_url = "https://docs.googleapis.com/v1/documents"
    payload = json.dumps({"title": title}).encode("utf-8")

    req = urllib.request.Request(create_url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            doc_data = json.loads(resp.read().decode("utf-8"))
            doc_id = doc_data.get("documentId")
            if not doc_id:
                return False, "Response missing documentId", {}

            # Move document to target folder if specified
            if folder_id and folder_id.strip():
                try:
                    fid = folder_id.strip()
                    move_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}?addParents={urllib.parse.quote(fid)}&removeParents=root&fields=id,parents"
                    m_req = urllib.request.Request(move_url, data=b"", method="PATCH")
                    m_req.add_header("Authorization", f"Bearer {access_token}")
                    urllib.request.urlopen(m_req, timeout=12)
                except Exception as e:
                    print(f"[GDOCS] Warning: Could not place doc in folder {folder_id}: {e}")

            return True, doc_id, doc_data
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {he.code}: {err}", {}
    except Exception as e:
        return False, f"API Error: {e}", {}


def batch_update_google_doc(
    access_token: str,
    doc_id: str,
    requests: List[Dict[str, Any]],
) -> Tuple[bool, str]:
    """Execute batchUpdate styling and text insertion requests on a Google Doc."""
    if not requests:
        return True, "No requests to apply"

    url = f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate"
    payload = json.dumps({"requests": requests}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            json.loads(resp.read().decode("utf-8"))
            return True, "Batch update applied successfully"
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, f"Batch update error: {e}"

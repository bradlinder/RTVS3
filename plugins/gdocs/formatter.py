"""Google Docs Document Serializer and Formatting Engine.

Converts transcripts, speaker turns, story segmentations, and metadata
into native Google Docs REST API structures (UTF-16 indexed batchUpdate requests).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


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
        include_speakers: bool = True,
        include_timestamps: bool = True,
        include_word_timestamps: bool = False,
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate plain document text, Google Docs batchUpdate requests, and comment anchor points.

        Returns:
            (full_text, batch_update_requests, comment_anchors)
        """
        full_text = ""
        requests: List[Dict[str, Any]] = []
        comment_anchors: List[Dict[str, Any]] = []

        # Google Docs documents start with index 1 (index 0 is reserved)
        cursor = 1

        # 1. Document Title
        title_text = f"{document_title}\n"
        title_start = cursor
        title_end = cursor + utf16_len(title_text)
        full_text += title_text
        cursor = title_end

        # Style Title
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": title_start, "endIndex": title_end},
                "paragraphStyle": {"namedStyleType": "TITLE", "spaceBelow": {"magnitude": 12, "unit": "PT"}},
                "fields": "namedStyleType,spaceBelow",
            }
        })
        requests.append({
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

        # 2. Metadata Summary Block
        meta_lines = []
        if project_metadata:
            source = project_metadata.get("media_filename") or project_metadata.get("filename")
            if source:
                meta_lines.append(f"Source Media: {source}")
            dur = project_metadata.get("duration")
            if dur is not None and isinstance(dur, (int, float)) and dur > 0:
                meta_lines.append(f"Duration: {format_time(dur)}")
            lang = project_metadata.get("language") or project_metadata.get("source_language")
            if lang:
                meta_lines.append(f"Language: {str(lang).upper()}")
            meta_lines.append(f"Total Stories: {len(stories)}")
            meta_lines.append(f"Transcript Segments: {len(transcript_segments)}")

        if meta_lines:
            meta_text = " • ".join(meta_lines) + "\n\n"
            meta_start = cursor
            meta_end = cursor + utf16_len(meta_text)
            full_text += meta_text
            cursor = meta_end

            requests.append({
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

        # 3. Story Sections and Segments
        # Organize segments by story or chronological order
        story_index = 1
        for story in stories:
            s_title = getattr(story, "title", None) or (story.get("title") if isinstance(story, dict) else f"Story {story_index}")
            s_start = getattr(story, "start", None) or (story.get("start") if isinstance(story, dict) else 0.0)
            s_end = getattr(story, "end", None) or (story.get("end") if isinstance(story, dict) else 0.0)
            s_notes = getattr(story, "notes", None) or (story.get("notes") if isinstance(story, dict) else "")

            # Story Header
            time_str = f"[{format_time(s_start)} – {format_time(s_end)}]" if include_timestamps else ""
            header_text = f"Story {story_index}: {s_title} {time_str}".strip() + "\n"
            sec_start = cursor
            sec_end = cursor + utf16_len(header_text)
            full_text += header_text
            cursor = sec_end

            # Style Story Header as HEADING_2
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": sec_start, "endIndex": sec_end},
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_2",
                        "spaceAbove": {"magnitude": 14, "unit": "PT"},
                        "spaceBelow": {"magnitude": 6, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceAbove,spaceBelow",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": sec_start, "endIndex": sec_end - 1},
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": 14, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.12, "green": 0.35, "blue": 0.65}}},
                    },
                    "fields": "bold,fontSize,foregroundColor",
                }
            })

            # Record story comment anchor if editorial notes exist
            if s_notes:
                comment_anchors.append({
                    "type": "story_notes",
                    "story_id": story_index,
                    "title": s_title,
                    "text": s_notes,
                    "start_index": sec_start,
                    "end_index": sec_end - 1,
                    "quoted_text": header_text.strip(),
                })

            # Find segments belonging to this story interval
            in_story_segs = [
                seg for seg in transcript_segments
                if (seg.get("start", 0.0) >= s_start - 0.05 and seg.get("end", 0.0) <= s_end + 0.05)
                or (s_start <= seg.get("start", 0.0) < s_end)
            ]

            if not in_story_segs:
                # If no segment matched, fallback to all segments if only 1 story
                if len(stories) == 1:
                    in_story_segs = transcript_segments

            for seg in in_story_segs:
                spk = seg.get("speaker", "Speaker")
                seg_start = seg.get("start", 0.0)
                seg_text = str(seg.get("text", "")).strip()
                if not seg_text:
                    continue

                # Speaker and timestamp line
                spk_parts = []
                if include_speakers:
                    spk_parts.append(str(spk).upper())
                if include_timestamps:
                    spk_parts.append(f"({format_time(seg_start)})")

                if spk_parts:
                    spk_line = " ".join(spk_parts) + "\n"
                    spk_start = cursor
                    spk_end = cursor + utf16_len(spk_line)
                    full_text += spk_line
                    cursor = spk_end

                    requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": spk_start, "endIndex": spk_end - 1},
                            "textStyle": {
                                "bold": True,
                                "fontSize": {"magnitude": 10.5, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.25, "green": 0.3, "blue": 0.38}}},
                            },
                            "fields": "bold,fontSize,foregroundColor",
                        }
                    })

                # Body text paragraph
                body_content = seg_text
                if include_word_timestamps and "words" in seg and isinstance(seg["words"], list):
                    # Format with inline word brackets: word [00:12.3]
                    word_tokens = []
                    for w in seg["words"]:
                        w_txt = w.get("word", "").strip()
                        w_st = w.get("start", 0.0)
                        if w_txt:
                            word_tokens.append(f"{w_txt} [{format_time(w_st)}]")
                    if word_tokens:
                        body_content = " ".join(word_tokens)

                body_line = body_content + "\n\n"
                body_start = cursor
                body_end = cursor + utf16_len(body_line)
                full_text += body_line
                cursor = body_end

                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": body_start, "endIndex": body_end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "lineSpacing": 115,
                            "spaceBelow": {"magnitude": 6, "unit": "PT"},
                        },
                        "fields": "namedStyleType,lineSpacing,spaceBelow",
                    }
                })

            story_index += 1

        # If no stories were provided, output all segments cleanly
        if not stories and transcript_segments:
            for seg in transcript_segments:
                spk = seg.get("speaker", "Speaker")
                seg_start = seg.get("start", 0.0)
                seg_text = str(seg.get("text", "")).strip()
                if not seg_text:
                    continue

                if include_speakers or include_timestamps:
                    spk_line = f"{str(spk).upper()} ({format_time(seg_start)})\n"
                    spk_start = cursor
                    spk_end = cursor + utf16_len(spk_line)
                    full_text += spk_line
                    cursor = spk_end

                    requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": spk_start, "endIndex": spk_end - 1},
                            "textStyle": {"bold": True, "fontSize": {"magnitude": 10.5, "unit": "PT"}},
                            "fields": "bold,fontSize",
                        }
                    })

                body_line = seg_text + "\n\n"
                b_start = cursor
                b_end = cursor + utf16_len(body_line)
                full_text += body_line
                cursor = b_end

                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": b_start, "endIndex": b_end},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "lineSpacing": 115},
                        "fields": "namedStyleType,lineSpacing",
                    }
                })

        # InsertTextRequest goes first in the batch
        insert_request = {
            "insertText": {
                "location": {"index": 1},
                "text": full_text,
            }
        }
        all_requests = [insert_request] + requests

        return full_text, all_requests, comment_anchors


def create_google_doc(
    access_token: str,
    title: str,
    folder_id: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Create a new Google Doc via Google Docs REST API and optionally move to folder.

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

            # If folder_id specified, move file using Drive API
            if folder_id and folder_id.strip():
                try:
                    move_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}?addParents={urllib.parse.quote(folder_id.strip())}&fields=id,parents"
                    m_req = urllib.request.Request(move_url, data=b"", method="PATCH")
                    m_req.add_header("Authorization", f"Bearer {access_token}")
                    urllib.request.urlopen(m_req, timeout=10)
                except Exception as e:
                    print(f"[GDOCS] Warning: Could not move doc to folder {folder_id}: {e}")

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

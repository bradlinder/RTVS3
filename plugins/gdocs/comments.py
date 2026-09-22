"""Google Docs & Drive Native Margin Comments and Anchoring Engine.

Integrates with Google Drive Comments API (drive.comments.create & drive.comments.list)
to attach editorial notes, transcript annotations, review remarks, and terminology tags
directly into the margin of the exported Google Doc.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def create_drive_comment(
    access_token: str,
    file_id: str,
    content: str,
    quoted_text: Optional[str] = None,
    anchor_info: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Create a native margin comment attached to a document file via Google Drive API.

    Args:
        access_token: OAuth 2.0 bearer token
        file_id: Google Doc document ID
        content: Comment body text (markdown/plain text)
        quoted_text: Context snippet to anchor to in the document body
        anchor_info: Optional anchor specification dictionary

    Returns:
        (success, comment_id_or_error, comment_data)
    """
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/comments?fields=id,content,quotedFileContent,author,createdTime"
    payload: Dict[str, Any] = {
        "content": content,
    }

    if quoted_text and quoted_text.strip():
        payload["quotedFileContent"] = {
            "mimeType": "text/plain",
            "value": quoted_text.strip()[:250],
        }

    if anchor_info:
        payload["anchor"] = json.dumps(anchor_info)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            cid = res_json.get("id", "")
            return True, cid, res_json
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {he.code}: {err}", {}
    except Exception as e:
        return False, f"Comment creation error: {e}", {}


def list_drive_comments(
    access_token: str,
    file_id: str,
    include_deleted: bool = False,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """Retrieve all margin comments and discussion threads from a document."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/comments?fields=comments(id,content,quotedFileContent,author,createdTime,resolved,replies)&includeDeleted={str(include_deleted).lower()}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            comments = data.get("comments", [])
            return True, comments, ""
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, [], f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, [], f"Error fetching comments: {e}"


def attach_editorial_notes_as_comments(
    access_token: str,
    file_id: str,
    comment_anchors: List[Dict[str, Any]],
) -> int:
    """Iterate through comment anchors and attach margin comments for editorial notes.
    Returns count of successfully created comments.
    """
    created_count = 0
    for anchor in comment_anchors:
        note_text = anchor.get("text", "").strip()
        quoted = anchor.get("quoted_text", "").strip()
        if not note_text:
            continue

        comment_body = f"📝 RTVS Editorial Note:\n{note_text}"
        ok, cid, _ = create_drive_comment(
            access_token=access_token,
            file_id=file_id,
            content=comment_body,
            quoted_text=quoted,
        )
        if ok:
            created_count += 1
        else:
            print(f"[GDOCS COMMENTS] Note comment creation warning: {cid}")

    return created_count

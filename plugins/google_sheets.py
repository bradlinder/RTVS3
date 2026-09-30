"""Google Sheets Integration Engine for Radio & TV Segmenter.

================================================================================
ARCHITECTURE & FUTURE ROADMAP NOTICE:
This module provides a complete, production-ready Google Sheets API v4 client and
authentication manager for exporting broadcast rundowns, music/cue sheets, story
metadata matrices, and speaker talk-time analytics to Google Sheets.

CURRENT STATUS (v3.7.12-stable):
- Core API client, token exchange, and sheet formatting functions are fully implemented
  and unit-tested.
- The Graphical User Interface (UI) is intentionally dormant/unlinked until user-facing
  rundown and cue sheet export workflows are scheduled in the development roadmap (see roadmap.txt).
- Broadcasters and developers can enable the Google Sheets API in Google Cloud Console
  alongside Docs, Drive, and YouTube Data API v3 with the scope:
  https://www.googleapis.com/auth/spreadsheets
================================================================================
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("rtvs.sheets")

try:
    from plugins.gdocs.auth import GoogleDocsAuthManager
except ImportError:
    GoogleDocsAuthManager = None

SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
]


class GoogleSheetsApiClient:
    """Client for Google Sheets API v4 operations."""

    def __init__(self, auth_manager: Optional[Any] = None):
        if auth_manager is not None:
            self.auth = auth_manager
        elif GoogleDocsAuthManager is not None:
            self.auth = GoogleDocsAuthManager()
        else:
            self.auth = None

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        if not self.auth:
            raise RuntimeError("Google Sheets Auth Manager is not configured")
        token = self.auth.get_valid_access_token()
        if not token:
            raise PermissionError("Not authenticated with Google Sheets. Please link your Google account.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    def create_spreadsheet(self, title: str, sheet_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new Google Spreadsheet with optional initial sheet tab names.
        
        Returns:
            Dict response with 'spreadsheetId', 'spreadsheetUrl', etc.
        """
        url = SHEETS_API_BASE
        headers = self._get_headers()
        sheets_def = []
        if sheet_names:
            for sname in sheet_names:
                sheets_def.append({"properties": {"title": sname}})
        else:
            sheets_def.append({"properties": {"title": "Sheet1"}})

        payload = {
            "properties": {"title": title},
            "sheets": sheets_def,
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def append_rows(self, spreadsheet_id: str, range_name: str, rows: List[List[Any]]) -> Dict[str, Any]:
        """Append one or more rows of tabular data to the specified sheet range.
        
        Args:
            spreadsheet_id: The ID of the target spreadsheet.
            range_name: A1 notation range (e.g. 'Sheet1!A1' or 'Rundown!A:F').
            rows: 2D list of row values (strings, numbers, booleans).
        """
        encoded_range = urllib.parse.quote(range_name)
        url = f"{SHEETS_API_BASE}/{spreadsheet_id}/values/{encoded_range}:append?valueInputOption=USER_ENTERED"
        headers = self._get_headers()
        payload = {
            "range": range_name,
            "majorDimension": "ROWS",
            "values": rows,
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def write_table(self, spreadsheet_id: str, range_name: str, rows: List[List[Any]]) -> Dict[str, Any]:
        """Overwrite/write tabular data to the specified sheet range using PUT."""
        encoded_range = urllib.parse.quote(range_name)
        url = f"{SHEETS_API_BASE}/{spreadsheet_id}/values/{encoded_range}?valueInputOption=USER_ENTERED"
        headers = self._get_headers()
        payload = {
            "range": range_name,
            "majorDimension": "ROWS",
            "values": rows,
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Return canonical Google Sheets browser URL."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


# ==============================================================================
# Domain Formatter Helpers for Future Rundown & Cue Sheet Workflows
# ==============================================================================

def format_story_rundown_table(stories: List[Dict[str, Any]], format_time_fn: Optional[Any] = None) -> List[List[Any]]:
    """Convert story segment metadata into standard broadcast rundown rows.
    
    Columns: Story #, Title, Start Time, End Time, Duration, Speaker/Talent, Summary/Notes
    """
    fmt = format_time_fn or (lambda s: f"{s:.2f}s")
    header = ["Story #", "Title / Segment", "Start Time", "End Time", "Duration (sec)", "Formatted Duration", "Speaker(s)", "Excerpt / Notes"]
    rows = [header]

    for idx, st in enumerate(stories, 1):
        s_start = float(st.get("start", 0.0) or 0.0)
        s_end = float(st.get("end", 0.0) or 0.0)
        dur = max(0.0, s_end - s_start)
        title = st.get("title") or st.get("name") or f"Story {idx}"
        speakers = ", ".join(st.get("speakers", [])) if isinstance(st.get("speakers"), list) else str(st.get("speakers", "") or "")
        excerpt = st.get("excerpt") or st.get("summary") or ""
        rows.append([
            idx,
            title,
            fmt(s_start),
            fmt(s_end),
            round(dur, 2),
            fmt(dur),
            speakers,
            excerpt,
        ])
    return rows


def format_speaker_analytics_table(transcript_segments: List[Dict[str, Any]], format_time_fn: Optional[Any] = None) -> List[List[Any]]:
    """Calculate and format per-speaker talk-time metrics and percentages into tabular rows.
    
    Columns: Speaker, Total Turns, Total Talk Time, Percentage of Airtime, Total Words
    """
    fmt = format_time_fn or (lambda s: f"{s:.2f}s")
    stats: Dict[str, Dict[str, Any]] = {}
    total_time = 0.0
    total_words = 0

    for seg in transcript_segments:
        spk = seg.get("speaker") or "Unassigned"
        dur = max(0.0, float(seg.get("end", 0.0)) - float(seg.get("start", 0.0)))
        words = len((seg.get("text") or "").split())
        total_time += dur
        total_words += words

        if spk not in stats:
            stats[spk] = {"turns": 0, "duration": 0.0, "words": 0}
        stats[spk]["turns"] += 1
        stats[spk]["duration"] += dur
        stats[spk]["words"] += words

    header = ["Speaker Identifier / Name", "Speaking Turns", "Total Talk Time", "Airtime %", "Word Count", "Words Per Minute (WPM)"]
    rows = [header]

    for spk, data in sorted(stats.items(), key=lambda x: x[1]["duration"], reverse=True):
        pct = (data["duration"] / total_time * 100.0) if total_time > 0 else 0.0
        wpm = (data["words"] / (data["duration"] / 60.0)) if data["duration"] > 0 else 0.0
        rows.append([
            spk,
            data["turns"],
            fmt(data["duration"]),
            f"{pct:.1f}%",
            data["words"],
            round(wpm, 1),
        ])
    return rows

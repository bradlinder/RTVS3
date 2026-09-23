"""Google Docs Review and Comment Pull Integration.

Enables editorial staff to inspect revisions and margin comments made in Google Docs
and pull reviewed transcript corrections back into the active RTVS project.
"""
from __future__ import annotations

import difflib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QSplitter,
        QHeaderView,
        QMessageBox,
        QCheckBox,
        QGroupBox,
        QWidget,
    )
except ImportError:
    # Minimal fallback for headless or test environments
    class QDialog:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def exec(self): return 0
    class QWidget: pass  # type: ignore

from plugins.gdocs.comments import list_drive_comments


def extract_doc_id_from_url(url_or_id: str) -> str:
    """Extract document ID from a full Google Docs URL or return raw ID."""
    clean = url_or_id.strip()
    match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", clean)
    if match:
        return match.group(1)
    # Check if raw alphanumeric string of typical doc ID length
    if re.match(r"^[a-zA-Z0-9_-]{20,}$", clean):
        return clean
    return clean


def fetch_google_doc_content(access_token: str, doc_id: str) -> Tuple[bool, str, Dict[str, Any], str]:
    """Retrieve Google Doc JSON structure and extract plain text."""
    url = f"https://docs.googleapis.com/v1/documents/{doc_id}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            doc_data = json.loads(resp.read().decode("utf-8"))

        full_text = ""
        body = doc_data.get("body", {})
        for elem in body.get("content", []):
            p = elem.get("paragraph")
            if p:
                for pe in p.get("elements", []):
                    tr = pe.get("textRun")
                    if tr and "content" in tr:
                        full_text += tr["content"]

        return True, full_text, doc_data, ""
    except urllib.error.HTTPError as he:
        err = he.read().decode("utf-8", errors="ignore")
        return False, "", {}, f"HTTP {he.code}: {err}"
    except Exception as e:
        return False, "", {}, f"Error reading Google Doc: {e}"


def compute_segment_diffs(
    local_segments: List[Dict[str, Any]],
    remote_text: str,
) -> List[Dict[str, Any]]:
    """Compare local transcript segments with paragraphs from the remote Google Doc."""
    diff_results: List[Dict[str, Any]] = []

    # Clean and split remote text into non-empty lines
    remote_lines = [l.strip() for l in remote_text.splitlines() if l.strip()]

    # Filter out title and story headers (e.g., "Story 1:", "ALICE (00:01)")
    clean_remote_paragraphs: List[str] = []
    for line in remote_lines:
        if re.match(r"^Story\s+\d+:", line, re.IGNORECASE):
            continue
        if re.match(r"^[A-Z0-9_\s-]+\s*\(\d+:\d+", line):
            continue
        if line.startswith("Source Media:") or line.startswith("Language:"):
            continue
        clean_remote_paragraphs.append(line)

    remote_combined = " ".join(clean_remote_paragraphs)

    for idx, seg in enumerate(local_segments):
        orig_text = str(seg.get("text", "")).strip()
        speaker = seg.get("speaker", "Speaker")
        if not orig_text:
            continue

        # Look for the segment or its updated version in remote paragraphs
        best_match = None
        best_ratio = 0.0
        for r_para in clean_remote_paragraphs:
            ratio = difflib.SequenceMatcher(None, orig_text, r_para).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = r_para

        has_change = False
        revised_text = orig_text
        if best_match and best_ratio > 0.60 and best_ratio < 0.999:
            has_change = True
            revised_text = best_match

        diff_results.append({
            "segment_index": idx,
            "speaker": speaker,
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0),
            "original_text": orig_text,
            "revised_text": revised_text,
            "has_change": has_change,
            "similarity": best_ratio,
        })

    return diff_results


class GoogleDocsReviewDialog(QDialog):
    """Dialog for inspecting Google Doc edits, margin comments, and applying transcript updates."""

    def __init__(self, auth_manager: Any, main_window: Any = None, parent: Any = None):
        super().__init__(parent or main_window)
        self.auth_manager = auth_manager
        self.main_window = main_window
        self.setWindowTitle("Google Docs: Review & Pull Editorial Corrections")
        self.setMinimumSize(820, 560)
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.diff_data: List[Dict[str, Any]] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Info
        header = QLabel(
            "<b>Review Editorial Corrections from Google Docs</b><br>"
            "Enter the Google Doc URL or Document ID to compare editorial revisions and margin comments "
            "with your current project transcript."
        )
        header.setStyleSheet("font-size: 12px; color: #334155;")
        layout.addWidget(header)

        # URL Input Row
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Google Doc URL / ID:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.google.com/document/d/.../edit")
        url_layout.addWidget(self.url_input)

        self.fetch_btn = QPushButton("Fetch Revisions & Comments")
        self.fetch_btn.clicked.connect(self.on_fetch_clicked)
        url_layout.addWidget(self.fetch_btn)
        layout.addLayout(url_layout)

        # Splitter: Diff Table on Left, Comments / Detail on Right
        splitter = QSplitter(Qt.Horizontal)

        # Table of segments
        table_box = QGroupBox("Transcript Differences")
        t_layout = QVBoxLayout(table_box)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Apply", "Speaker", "Original Transcript", "Reviewed in Google Doc"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        t_layout.addWidget(self.table)
        splitter.addWidget(table_box)

        # Side panel: Comments from Drive
        comment_box = QGroupBox("Margin Comments from Google Drive")
        c_layout = QVBoxLayout(comment_box)
        self.comments_view = QTextEdit()
        self.comments_view.setReadOnly(True)
        self.comments_view.setPlaceholderText("Drive margin comments will appear here...")
        c_layout.addWidget(self.comments_view)
        splitter.addWidget(comment_box)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        # Bottom actions
        b_layout = QHBoxLayout()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #64748b;")
        b_layout.addWidget(self.status_lbl)
        b_layout.addStretch()

        self.apply_btn = QPushButton("Apply Selected Corrections to Transcript")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        b_layout.addWidget(self.apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        b_layout.addWidget(close_btn)
        layout.addLayout(b_layout)

    def on_fetch_clicked(self):
        raw_url = self.url_input.text().strip()
        doc_id = extract_doc_id_from_url(raw_url)
        if not doc_id:
            QMessageBox.warning(self, "Invalid Document ID", "Please enter a valid Google Doc URL or Document ID.")
            return

        token = self.auth_manager.get_valid_access_token()
        if not token:
            QMessageBox.warning(self, "Not Authenticated", "Please sign in to Google in Preferences or Unified Export Center first.")
            return

        self.status_lbl.setText("Fetching document and margin comments...")
        ok, doc_text, _, err = fetch_google_doc_content(token, doc_id)
        if not ok:
            QMessageBox.critical(self, "Error Fetching Doc", f"Failed to retrieve Google Doc:\n{err}")
            self.status_lbl.setText("Fetch failed.")
            return

        # Fetch comments
        _, comments, _ = list_drive_comments(token, doc_id)
        if comments:
            c_text = ""
            for c in comments:
                author = c.get("author", {}).get("displayName", "Reviewer")
                content = c.get("content", "")
                quoted = c.get("quotedFileContent", {}).get("value", "")
                c_text += f"💬 <b>{author}</b>:\n{content}\n"
                if quoted:
                    c_text += f"   <i>Anchored on: \"{quoted}\"</i>\n"
                c_text += "—" * 30 + "\n\n"
            self.comments_view.setHtml(c_text.replace("\n", "<br>"))
        else:
            self.comments_view.setPlainText("No margin comments found on this document.")

        # Compute diffs against active transcript
        local_segs = []
        if self.main_window and hasattr(self.main_window, "transcript") and self.main_window.transcript:
            local_segs = self.main_window.transcript.get("segments", [])

        self.diff_data = compute_segment_diffs(local_segs, doc_text)
        self.populate_table()

        changed_count = sum(1 for d in self.diff_data if d["has_change"])
        self.status_lbl.setText(f"Found {changed_count} changed segments in Google Doc.")
        self.apply_btn.setEnabled(changed_count > 0)

    def populate_table(self):
        self.table.setRowCount(0)
        for row_idx, diff in enumerate(self.diff_data):
            self.table.insertRow(row_idx)

            cb = QCheckBox()
            cb.setChecked(diff["has_change"])
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_idx, 0, cb_widget)

            spk_item = QTableWidgetItem(diff["speaker"])
            self.table.setItem(row_idx, 1, spk_item)

            orig_item = QTableWidgetItem(diff["original_text"])
            self.table.setItem(row_idx, 2, orig_item)

            rev_item = QTableWidgetItem(diff["revised_text"])
            if diff["has_change"]:
                rev_item.setBackground(Qt.yellow)
            self.table.setItem(row_idx, 3, rev_item)

    def on_apply_clicked(self):
        if not self.main_window or not hasattr(self.main_window, "transcript"):
            return

        applied = 0
        segs = self.main_window.transcript.get("segments", [])
        for row in range(self.table.rowCount()):
            cb_widget = self.table.cellWidget(row, 0)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb and cb.isChecked() and row < len(self.diff_data):
                    diff = self.diff_data[row]
                    seg_i = diff["segment_index"]
                    if seg_i < len(segs) and diff["has_change"]:
                        segs[seg_i]["text"] = diff["revised_text"]
                        applied += 1

        if applied > 0:
            if hasattr(self.main_window, "update_transcript_display"):
                self.main_window.update_transcript_display()
            if hasattr(self.main_window, "mark_project_dirty"):
                self.main_window.mark_project_dirty()
            QMessageBox.information(
                self,
                "Corrections Applied",
                f"Successfully updated {applied} transcript segment(s) with editorial revisions from Google Docs.",
            )
            self.accept()
        else:
            QMessageBox.information(self, "No Changes", "No segment corrections were selected to apply.")

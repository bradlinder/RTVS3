"""Radio & TV Story Segmenter — In-App User Guide & Documentation Viewer Dialog.

Provides a native, interactive desktop reader for RTVS3 user guides with
inline image rendering, topic navigation sidebar, zoom controls, and theme synchronization.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from embedded_guides import get_embedded_guide
from core_utils import (
    apply_window_titlebar_theme,
    get_active_theme_mode,
    make_dialog_maximizable,
)


class UserGuideDialog(QDialog):
    """In-app reader dialog displaying rich user guides with inline screenshots."""

    GUIDE_CATALOG: List[Dict[str, str]] = [
        {
            "id": "workflow",
            "title": "Getting Started & Essential Workflow",
            "path": "docs/guides/getting_started_and_workflow.md",
        },
        {
            "id": "wordpress",
            "title": "WordPress Exporting & Setup",
            "path": "docs/guides/wordpress_exporting.md",
        },
        {
            "id": "youtube",
            "title": "YouTube Features & Chapter Generation",
            "path": "docs/guides/youtube_features.md",
        },
        {
            "id": "video_shows",
            "title": "Video Shows & YouTube Publishing",
            "path": "docs/guides/video_shows_and_youtube_publishing.md",
        },
        {
            "id": "export_formats",
            "title": "Export Formats & DAW Integration",
            "path": "docs/guides/export_formats.md",
        },
        {
            "id": "shortcuts",
            "title": "Keyboard Shortcuts & Controls",
            "path": "docs/guides/shortcuts_overview.md",
        },
    ]

    @staticmethod
    def _find_docs_dir() -> Path:
        """Locate the docs directory across frozen executables, installed dirs, and dev trees."""
        candidates: List[Path] = []

        # 1. Next to sys.executable (e.g. C:\Program Files\Radio & TV Segmenter\docs)
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            candidates.append(exe_dir / "docs")
            candidates.append(exe_dir / "_internal" / "docs")
            # macOS .app bundle Contents/Resources/docs
            candidates.append(exe_dir.parent / "Resources" / "docs")

        # 2. PyInstaller temporary/bundled extraction directory (_MEIPASS)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "docs")

        # 3. Source repository locations relative to this file
        current_dir = Path(__file__).resolve().parent
        candidates.append(current_dir / "docs")
        candidates.append(current_dir.parent / "docs")

        # 4. Current working directory
        candidates.append(Path.cwd() / "docs")

        # Prioritize candidates that contain the guides subdirectory
        for c in candidates:
            if c.is_dir() and (c / "guides").is_dir():
                return c

        for c in candidates:
            if c.is_dir():
                return c

        return current_dir / "docs"

    def __init__(self, parent: Optional[QWidget] = None, initial_guide_id: str = "workflow"):
        super().__init__(parent)
        self.setWindowTitle("User Guides & Documentation — Radio & TV Story Segmenter")
        make_dialog_maximizable(self)
        self.resize(1020, 720)
        self.setMinimumSize(740, 500)

        self.docs_dir = self._find_docs_dir()
        self.root_dir = self.docs_dir.parent if self.docs_dir.name == "docs" else self.docs_dir
        self.theme_mode = get_active_theme_mode("dark")
        self.current_zoom = 0
        self.current_guide_content = ""
        self.current_guide_title = ""

        self._setup_ui()
        self._load_guide_by_id(initial_guide_id)
        apply_window_titlebar_theme(self, self.theme_mode)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top Control & Navigation Header Bar
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 0)
        header_bar.setSpacing(8)

        self.guide_heading_label = QLabel("User Documentation")
        heading_font = self.guide_heading_label.font()
        heading_font.setPointSize(13)
        heading_font.setBold(True)
        self.guide_heading_label.setFont(heading_font)
        header_bar.addWidget(self.guide_heading_label, 1)

        # Zoom Controls
        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_out_btn.setToolTip("Decrease document text size (Ctrl+-)")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        header_bar.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_in_btn.setToolTip("Increase document text size (Ctrl++)")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        header_bar.addWidget(self.zoom_in_btn)

        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.setToolTip("Reset text size to default (Ctrl+0)")
        self.reset_zoom_btn.clicked.connect(self._reset_zoom)
        header_bar.addWidget(self.reset_zoom_btn)

        self.browser_btn = QPushButton("Open in Web Browser")
        self.browser_btn.setToolTip("Open this guide with images in your default external web browser")
        self.browser_btn.clicked.connect(self._open_in_external_browser)
        header_bar.addWidget(self.browser_btn)

        main_layout.addLayout(header_bar)

        # Splitter: Topics Sidebar + Content Browser
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)

        # Left Sidebar: Guide Topics List
        sidebar_widget = QWidget(splitter)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(6)

        sidebar_title = QLabel("Topics")
        sidebar_title_font = sidebar_title.font()
        sidebar_title_font.setBold(True)
        sidebar_title.setFont(sidebar_title_font)
        sidebar_layout.addWidget(sidebar_title)

        self.topics_list = QListWidget(sidebar_widget)
        self.topics_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for guide in self.GUIDE_CATALOG:
            item = QListWidgetItem(guide["title"])
            item.setData(Qt.ItemDataRole.UserRole, guide["id"])
            self.topics_list.addItem(item)
        self.topics_list.currentRowChanged.connect(self._on_topic_selected)
        sidebar_layout.addWidget(self.topics_list)

        splitter.addWidget(sidebar_widget)

        # Right Pane: Rich Text Browser
        self.browser = QTextBrowser(splitter)
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)
        self.browser.setSearchPaths([
            str(self.docs_dir / "images"),
            str(self.docs_dir / "guides"),
            str(self.docs_dir),
            str(self.root_dir / "docs" / "images"),
        ])
        self._apply_browser_stylesheet()

        splitter.addWidget(self.browser)
        splitter.setSizes([260, 740])
        main_layout.addWidget(splitter, 1)

        # Bottom Button Box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

        # Shortcut actions for zooming
        zoom_in_act = QAction(self)
        zoom_in_act.setShortcuts([QKeySequence.StandardKey.ZoomIn, QKeySequence("Ctrl+=")])
        zoom_in_act.triggered.connect(self._zoom_in)
        self.addAction(zoom_in_act)

        zoom_out_act = QAction(self)
        zoom_out_act.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_act.triggered.connect(self._zoom_out)
        self.addAction(zoom_out_act)

        zoom_reset_act = QAction(self)
        zoom_reset_act.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_act.triggered.connect(self._reset_zoom)
        self.addAction(zoom_reset_act)

    def _apply_browser_stylesheet(self):
        is_dark = (self.theme_mode == "dark")
        bg_color = "#1e293b" if is_dark else "#ffffff"
        text_color = "#f8fafc" if is_dark else "#0f172a"
        code_bg = "#0f172a" if is_dark else "#f1f5f9"
        border_color = "#334155" if is_dark else "#e2e8f0"
        link_color = "#38bdf8" if is_dark else "#0284c7"
        sidebar_bg = "#0f172a" if is_dark else "#f8fafc"

        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {sidebar_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
            }}
            QTextBrowser {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 16px;
                line-height: 1.6;
            }}
        """)

    def _resolve_image_urls(self, markdown_text: str) -> str:
        """Replace relative image paths in markdown with absolute file URIs for instant rendering."""
        images_dir = (self.docs_dir / "images").resolve()
        if not images_dir.exists():
            images_dir = (self.root_dir / "docs" / "images").resolve()

        def _replace_img(match):
            alt_text = match.group(1)
            raw_path = match.group(2).strip()
            filename = Path(raw_path).name
            abs_image = (images_dir / filename).resolve()
            if abs_image.exists():
                return f"![{alt_text}]({abs_image.as_uri()})"
            return match.group(0)

        # Match ![alt text](path)
        return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _replace_img, markdown_text)

    def _load_guide_by_id(self, guide_id: str):
        guide = next((g for g in self.GUIDE_CATALOG if g["id"] == guide_id), None)
        if not guide:
            guide = self.GUIDE_CATALOG[0]

        self.current_guide_title = guide["title"]
        self.guide_heading_label.setText(guide["title"])

        # Try resolving file on disk across candidate locations
        target_name = Path(guide["path"]).name
        candidates = [
            self.docs_dir / "guides" / target_name,
            self.docs_dir / guide["path"],
            self.root_dir / guide["path"],
            self.docs_dir / target_name,
        ]

        file_path = next((c for c in candidates if c.is_file()), None)
        raw_text = None
        if file_path:
            try:
                raw_text = file_path.read_text(encoding="utf-8")
            except Exception:
                raw_text = None

        if not raw_text:
            if guide["id"] == "shortcuts":
                raw_text = self._build_dynamic_shortcuts_guide()
            else:
                embedded = get_embedded_guide(guide["id"])
                if embedded:
                    raw_text = embedded
                else:
                    raw_text = f"# Guide Not Found\n\nThe guide at `{guide['path']}` could not be located."

        self.current_guide_content = raw_text
        resolved_md = self._resolve_image_urls(raw_text)

        # Render CommonMark markdown directly into QTextBrowser
        self.browser.setMarkdown(resolved_md)

        # Scroll to top of the document
        self.browser.verticalScrollBar().setValue(0)

        # Select corresponding topic in the sidebar list without recursive signals
        for row in range(self.topics_list.count()):
            item = self.topics_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == guide["id"]:
                self.topics_list.blockSignals(True)
                self.topics_list.setCurrentRow(row)
                self.topics_list.blockSignals(False)
                break

    def _on_topic_selected(self, row: int):
        if row < 0 or row >= len(self.GUIDE_CATALOG):
            return
        guide_id = self.GUIDE_CATALOG[row]["id"]
        self._load_guide_by_id(guide_id)

    def _zoom_in(self):
        self.browser.zoomIn(1)
        self.current_zoom += 1

    def _zoom_out(self):
        self.browser.zoomOut(1)
        self.current_zoom -= 1

    def _reset_zoom(self):
        if self.current_zoom != 0:
            self.browser.zoomOut(self.current_zoom) if self.current_zoom > 0 else self.browser.zoomIn(-self.current_zoom)
            self.current_zoom = 0

    def _open_in_external_browser(self):
        """Export the current guide as a self-contained styled HTML file and launch the system web browser."""
        try:
            html_body = self.browser.toHtml()
            is_dark = (self.theme_mode == "dark")
            bg_color = "#0f172a" if is_dark else "#ffffff"
            text_color = "#f8fafc" if is_dark else "#0f172a"

            styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{self.current_guide_title} — RTVS3 Guide</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: {bg_color};
      color: {text_color};
      max-width: 960px;
      margin: 0 auto;
      padding: 40px 20px;
      line-height: 1.6;
    }}
    img {{
      max-width: 100%;
      height: auto;
      border-radius: 6px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
      margin: 16px 0;
      border: 1px solid #334155;
    }}
    pre, code {{
      background-color: #1e293b;
      color: #38bdf8;
      border-radius: 4px;
      padding: 2px 6px;
    }}
    pre {{
      padding: 12px;
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 20px 0;
    }}
    th, td {{
      border: 1px solid #334155;
      padding: 8px 12px;
      text-align: left;
    }}
    th {{
      background-color: #1e293b;
    }}
    a {{
      color: #38bdf8;
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""
            temp_dir = Path(tempfile.gettempdir()) / "rtvs3_guides"
            temp_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', self.current_guide_title.lower())
            html_file = temp_dir / f"{safe_name}.html"
            html_file.write_text(styled_html, encoding="utf-8")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(html_file)))
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Browser View", f"Could not open external browser: {e}")

    def _build_dynamic_shortcuts_guide(self) -> str:
        """Build dynamic keyboard shortcut documentation from active settings."""
        return """# Keyboard Shortcuts & Controls

Radio & TV Story Segmenter provides extensive keyboard control across timeline scrubbing, audio playback, transcript editing, and story segmentation.

---

## 1. Transport & Playback Shortcuts

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Play / Pause** | `Space` | `Space` | Toggle audio playback at playhead position. |
| **Stop** | `Esc` | `Esc` | Stop playback and return playhead to start. |
| **Seek Backward (Small)** | `Left Arrow` | `Left Arrow` | Jump backward 2 seconds. |
| **Seek Forward (Small)** | `Right Arrow` | `Right Arrow` | Jump forward 2 seconds. |
| **Seek Backward (Large)** | `Shift + Left` | `Shift + Left` | Jump backward 10 seconds. |
| **Seek Forward (Large)** | `Shift + Right` | `Shift + Right` | Jump forward 10 seconds. |
| **Timeline Zoom In** | `+` / `Ctrl + Wheel` | `+` / `Cmd + Wheel` | Zoom into waveform timeline up to 300x. |
| **Timeline Zoom Out** | `-` / `Ctrl + Wheel` | `-` / `Cmd + Wheel` | Zoom out toward episode overview. |

---

## 2. Story Segmentation & Editing

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Mark Story Start** | `[` | `[` | Set story in-point at current playhead position. |
| **Mark Story End** | `]` | `]` | Set story out-point and create story segment. |
| **Auto-Detect Stories** | `Ctrl + D` | `Cmd + D` | Run AI topic and pause boundary detection. |
| **Transcribe & Diarize** | `Ctrl + T` | `Cmd + T` | Run speech transcription and speaker recognition. |
| **Unified Export Center** | `Ctrl + E` | `Cmd + E` | Open export panel for audio, docs, and WordPress. |
| **Video Preview Window** | `Ctrl + Shift + V` | `Cmd + Shift + V` | Open floating, synchronized video player. |

---

## 3. Transcript Editor Controls

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Find & Replace** | `Ctrl + F` | `Cmd + F` | Open modeless Find and Replace dialog. |
| **Toggle Edit Mode** | `Ctrl + E` | `Cmd + E` | Toggle between viewing and direct text editing. |
| **Word Highlighting** | `Click Word` | `Click Word` | Seek audio playback directly to spoken word. |
"""

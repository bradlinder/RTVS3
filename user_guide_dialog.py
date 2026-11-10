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

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QFont,
    QImageReader,
    QKeySequence,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from embedded_guides import get_embedded_guide
from core_utils import (
    apply_window_titlebar_theme,
    get_active_theme_mode,
    make_dialog_maximizable,
)


class ResponsiveTextBrowser(QTextBrowser):
    """QTextBrowser subclass that responsively scales embedded images to viewport width."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._image_cache: Dict[str, QSize] = {}

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_images_to_viewport()

    def scale_images_to_viewport(self):
        doc = self.document()
        if not doc:
            return

        # Viewport width minus document padding margins
        try:
            vp_width = self.viewport().width()
            avail_width = max(160, int(vp_width) - 44)
        except (TypeError, ValueError, AttributeError, Exception):
            avail_width = 800
        cursor = QTextCursor(doc)
        doc.blockSignals(True)
        cursor.beginEditBlock()
        try:
            while not cursor.atEnd():
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                fmt = cursor.charFormat()
                if fmt.isImageFormat():
                    img_fmt = fmt.toImageFormat()
                    name = img_fmt.name()
                    if name not in self._image_cache:
                        local_path = QUrl(name).toLocalFile() if name.startswith("file:") else name
                        reader = QImageReader(local_path)
                        sz = reader.size()
                        if not sz.isValid() or sz.width() <= 0:
                            sz = QSize(int(img_fmt.width()) or 600, int(img_fmt.height()) or 400)
                        self._image_cache[name] = sz

                    orig_sz = self._image_cache[name]
                    orig_w = orig_sz.width()
                    orig_h = orig_sz.height()

                    if orig_w > avail_width:
                        scale = avail_width / orig_w
                        target_w = float(avail_width)
                        target_h = float(max(1, int(orig_h * scale)))
                    else:
                        target_w = float(orig_w)
                        target_h = float(orig_h)

                    if img_fmt.width() != target_w or img_fmt.height() != target_h:
                        img_fmt.setWidth(target_w)
                        img_fmt.setHeight(target_h)
                        cursor.setCharFormat(img_fmt)

                cursor.clearSelection()
        finally:
            cursor.endEditBlock()
            doc.blockSignals(False)


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
            "id": "reaper_bridge",
            "title": "REAPER & DAW Live Bridge",
            "path": "docs/guides/reaper_and_daw_integration.md",
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
        self.setWindowTitle("User Guides & Documentation — Radio & TV Segmenter")
        make_dialog_maximizable(self)
        self.resize(1020, 720)
        self.setMinimumSize(740, 500)

        self.docs_dir = self._find_docs_dir()
        self.root_dir = self.docs_dir.parent if self.docs_dir.name == "docs" else self.docs_dir
        self.theme_mode = get_active_theme_mode("dark")
        self.current_zoom = 0
        self.current_guide_content = ""
        self.current_guide_title = ""
        self._search_matches: List[QTextCursor] = []
        self._search_match_index: int = -1

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

        # Search Bar Strip (Filter & In-Document Find)
        search_bar = QHBoxLayout()
        search_bar.setContentsMargins(0, 0, 0, 0)
        search_bar.setSpacing(6)

        search_lbl = QLabel("Search:")
        search_lbl_font = search_lbl.font()
        search_lbl_font.setBold(True)
        search_lbl.setFont(search_lbl_font)
        search_bar.addWidget(search_lbl)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search documentation (Ctrl+F)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_query_changed)
        self.search_input.returnPressed.connect(self._find_next_match)
        search_bar.addWidget(self.search_input, 1)

        self.match_count_label = QLabel("")
        self.match_count_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 0 4px;")
        search_bar.addWidget(self.match_count_label)

        self.find_prev_btn = QPushButton("Prev")
        self.find_prev_btn.setToolTip("Previous match (Shift+Enter or Shift+F3)")
        self.find_prev_btn.clicked.connect(self._find_prev_match)
        search_bar.addWidget(self.find_prev_btn)

        self.find_next_btn = QPushButton("Next")
        self.find_next_btn.setToolTip("Next match (Enter or F3)")
        self.find_next_btn.clicked.connect(self._find_next_match)
        search_bar.addWidget(self.find_next_btn)

        main_layout.addLayout(search_bar)

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
        self.browser = ResponsiveTextBrowser(splitter)
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
        splitter.splitterMoved.connect(lambda pos, idx: self.browser.scale_images_to_viewport())
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

        find_act = QAction(self)
        find_act.setShortcut(QKeySequence.StandardKey.Find)
        find_act.triggered.connect(self._focus_search)
        self.addAction(find_act)

        find_next_act = QAction(self)
        find_next_act.setShortcut(QKeySequence("F3"))
        find_next_act.triggered.connect(self._find_next_match)
        self.addAction(find_next_act)

        find_prev_act = QAction(self)
        find_prev_act.setShortcut(QKeySequence("Shift+F3"))
        find_prev_act.triggered.connect(self._find_prev_match)
        self.addAction(find_prev_act)

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
            QLineEdit {{
                background-color: {sidebar_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid #2563eb;
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
        self.browser.scale_images_to_viewport()

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

        # Re-apply active search query to the newly loaded topic
        if hasattr(self, "search_input") and self.search_input.text().strip():
            query = self.search_input.text().strip()
            other_cnt = self._update_cross_topic_badges(query)
            self._execute_in_doc_search(query, other_cnt)

    def _on_topic_selected(self, row: int):
        if row < 0 or row >= len(self.GUIDE_CATALOG):
            return
        guide_id = self.GUIDE_CATALOG[row]["id"]
        self._load_guide_by_id(guide_id)

    def _focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _get_guide_raw_text(self, guide_id: str) -> str:
        if guide_id == "shortcuts":
            return self._build_dynamic_shortcuts_guide()
        guide = next((g for g in self.GUIDE_CATALOG if g["id"] == guide_id), None)
        if not guide:
            return ""
        target_name = Path(guide["path"]).name
        candidates = [
            self.docs_dir / "guides" / target_name,
            self.docs_dir / guide["path"],
            self.root_dir / guide["path"],
            self.docs_dir / target_name,
        ]
        file_path = next((c for c in candidates if c.is_file()), None)
        if file_path:
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                pass
        embedded = get_embedded_guide(guide_id)
        return embedded or ""

    def _update_cross_topic_badges(self, query: str) -> int:
        q_lower = query.lower()
        other_matches = 0
        total_matches = 0
        cur_row = self.topics_list.currentRow()
        cur_id = self.GUIDE_CATALOG[cur_row]["id"] if 0 <= cur_row < len(self.GUIDE_CATALOG) else ""
        first_match_row = None

        for row in range(self.topics_list.count()):
            item = self.topics_list.item(row)
            g_id = item.data(Qt.ItemDataRole.UserRole)
            guide = next((g for g in self.GUIDE_CATALOG if g["id"] == g_id), None)
            base_title = guide["title"] if guide else ""
            if not q_lower:
                item.setText(base_title)
            else:
                raw_txt = self._get_guide_raw_text(g_id)
                cnt = raw_txt.lower().count(q_lower)
                total_matches += cnt
                if cnt > 0:
                    item.setText(f"{base_title} ({cnt})")
                    if first_match_row is None:
                        first_match_row = row
                    if g_id != cur_id:
                        other_matches += cnt
                else:
                    item.setText(base_title)

        self._total_guide_matches = total_matches

        # Universal search: if current topic has 0 matches, auto-switch to first topic with matches
        if q_lower and total_matches > 0 and (total_matches - other_matches) == 0:
            if first_match_row is not None and first_match_row != cur_row:
                self.topics_list.blockSignals(True)
                self.topics_list.setCurrentRow(first_match_row)
                self.topics_list.blockSignals(False)
                new_id = self.GUIDE_CATALOG[first_match_row]["id"]
                self._load_guide_by_id(new_id)
                return total_matches - self._get_guide_raw_text(new_id).lower().count(q_lower)

        return other_matches

    def _on_search_query_changed(self, text: str):
        query = text.strip()
        other_cnt = self._update_cross_topic_badges(query)
        self._execute_in_doc_search(query, other_cnt)

    def _execute_in_doc_search(self, query: str, other_matches_count: int = 0):
        if not query:
            self._search_matches = []
            self._search_match_index = -1
            self.browser.setExtraSelections([])
            self.match_count_label.setText("")
            return

        doc = self.browser.document()
        if not doc:
            return

        matches: List[QTextCursor] = []
        cursor = QTextCursor(doc)
        while not cursor.isNull() and not cursor.atEnd():
            cursor = doc.find(query, cursor)
            if not cursor.isNull():
                matches.append(QTextCursor(cursor))

        self._search_matches = matches
        if matches:
            target_idx = getattr(self, "_target_match_index", None)
            if target_idx == -1:
                self._search_match_index = len(matches) - 1
            elif isinstance(target_idx, int) and 0 <= target_idx < len(matches):
                self._search_match_index = target_idx
            else:
                self._search_match_index = 0
            self._target_match_index = None
            self._highlight_matches(scroll=True)
            self._update_match_label()
        else:
            self._search_match_index = -1
            self._target_match_index = None
            self.browser.setExtraSelections([])
            total_across = getattr(self, "_total_guide_matches", 0)
            if total_across > 0:
                self.match_count_label.setText(f"0 in section ({total_across} across guide)")
            else:
                self.match_count_label.setText("No matches")

    def _update_match_label(self):
        if not self._search_matches or self._search_match_index < 0:
            return
        total_across = getattr(self, "_total_guide_matches", len(self._search_matches))
        if total_across > len(self._search_matches):
            self.match_count_label.setText(
                f"{self._search_match_index + 1} / {len(self._search_matches)} in section ({total_across} across guide)"
            )
        else:
            self.match_count_label.setText(f"{self._search_match_index + 1} / {len(self._search_matches)}")

    def _highlight_matches(self, scroll: bool = True):
        if not self._search_matches or self._search_match_index < 0:
            self.browser.setExtraSelections([])
            return

        is_dark = (self.theme_mode == "dark")
        bg_match = QColor("#854d0e") if is_dark else QColor("#fef08a")
        bg_current = QColor("#ca8a04") if is_dark else QColor("#f59e0b")
        fg_current = QColor("#ffffff") if is_dark else QColor("#000000")

        selections: List[QTextEdit.ExtraSelection] = []
        for idx, cur in enumerate(self._search_matches):
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            if idx == self._search_match_index:
                sel.format.setBackground(bg_current)
                sel.format.setForeground(fg_current)
                sel.format.setFontWeight(QFont.Weight.Bold)
            else:
                sel.format.setBackground(bg_match)
            selections.append(sel)

        self.browser.setExtraSelections(selections)

        if scroll and 0 <= self._search_match_index < len(self._search_matches):
            cur = self._search_matches[self._search_match_index]
            self.browser.setTextCursor(cur)
            self.browser.ensureCursorVisible()

    def _find_next_match(self):
        query = self.search_input.text().strip()
        if not query:
            return

        cur_row = self.topics_list.currentRow()
        if self._search_matches and self._search_match_index < len(self._search_matches) - 1:
            self._search_match_index += 1
            self._highlight_matches(scroll=True)
            self._update_match_label()
            return

        # Advance cyclically to the next topic containing matches
        num_topics = self.topics_list.count()
        for step in range(1, num_topics + 1):
            next_row = (cur_row + step) % num_topics
            g_id = self.GUIDE_CATALOG[next_row]["id"]
            cnt = self._get_guide_raw_text(g_id).lower().count(query.lower())
            if cnt > 0:
                self._target_match_index = 0
                self.topics_list.setCurrentRow(next_row)
                return

    def _find_prev_match(self):
        query = self.search_input.text().strip()
        if not query:
            return

        cur_row = self.topics_list.currentRow()
        if self._search_matches and self._search_match_index > 0:
            self._search_match_index -= 1
            self._highlight_matches(scroll=True)
            self._update_match_label()
            return

        # Move backwards cyclically to the previous topic containing matches
        num_topics = self.topics_list.count()
        for step in range(1, num_topics + 1):
            prev_row = (cur_row - step) % num_topics
            g_id = self.GUIDE_CATALOG[prev_row]["id"]
            cnt = self._get_guide_raw_text(g_id).lower().count(query.lower())
            if cnt > 0:
                self._target_match_index = -1
                self.topics_list.setCurrentRow(prev_row)
                return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, "search_input") and self.search_input.text():
                self.search_input.clear()
                self.browser.setFocus()
                event.accept()
                return
        super().keyPressEvent(event)

    def _zoom_in(self):
        self.browser.zoomIn(1)
        self.current_zoom += 1
        self.browser.scale_images_to_viewport()

    def _zoom_out(self):
        self.browser.zoomOut(1)
        self.current_zoom -= 1
        self.browser.scale_images_to_viewport()

    def _reset_zoom(self):
        if self.current_zoom != 0:
            self.browser.zoomOut(self.current_zoom) if self.current_zoom > 0 else self.browser.zoomIn(-self.current_zoom)
            self.current_zoom = 0
            self.browser.scale_images_to_viewport()

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

Radio & TV Segmenter provides extensive keyboard control across timeline scrubbing, audio playback, transcript editing, and segment editing.

---

## 1. Transport & Playback Shortcuts

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Play / Pause** | `Space` | `Space` | Toggle audio playback at playhead position. |
| **Skip Backward (Short)** | `Left Arrow` | `Left Arrow` | Jump backward 5 seconds (configurable). |
| **Skip Forward (Short)** | `Right Arrow` | `Right Arrow` | Jump forward 5 seconds (configurable). |
| **Jump Backward (Medium)** | `Shift + Left` | `Shift + Left` | Jump backward 15 seconds. |
| **Jump Forward (Medium)** | `Shift + Right` | `Shift + Right` | Jump forward 15 seconds. |
| **Jump Backward (Long)** | `Ctrl + Left` | `Cmd + Left` | Jump backward 30 seconds. |
| **Jump Forward (Long)** | `Ctrl + Right` | `Cmd + Right` | Jump forward 30 seconds. |
| **Seek to Start** | `Home` | `Home` | Return playhead to start of audio (00:00.0). |
| **Seek to End** | `End` | `End` | Move playhead to end of audio file. |
| **Timeline Zoom In** | `+` / `Ctrl + Wheel` | `+` / `Cmd + Wheel` | Zoom into waveform timeline up to 300x. |
| **Timeline Zoom Out** | `-` / `Ctrl + Wheel` | `-` / `Cmd + Wheel` | Zoom out toward episode overview. |

---

## 2. Segment Editing & Detection

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Mark Segment Start** | `[` | `[` | Set segment in-point at current playhead position. |
| **Mark Segment End** | `]` | `]` | Set segment out-point and create segment. |
| **Deselect All / Clear Selection** | `Esc` | `Esc` | Clear active segment selections, timeline selection range, or transcript selection. |
| **Detect Segments** | `Ctrl + Shift + A` | `Cmd + Shift + A` | Run AI topic and pause boundary detection. |
| **Transcribe Audio** | `Ctrl + T` | `Cmd + T` | Run speech-to-text transcription. |
| **Detect Speakers (Diarization)** | `Ctrl + D` | `Cmd + D` | Run AI speaker clustering and identification. |
| **Audio Fades & Crossfades** | `Ctrl + Shift + F` | `Cmd + Shift + F` | Configure segment volume fade curves. |
| **Unified Export Center** | `Ctrl + E` | `Cmd + E` | Open export panel for audio, docs, and WordPress. |
| **Video Preview Window** | `Ctrl + Shift + V` | `Cmd + Shift + V` | Open floating, synchronized video player. |

---

## 3. Transcript Editor Controls

| Action | Shortcut (Windows/Linux) | Shortcut (macOS) | Description |
| :--- | :--- | :--- | :--- |
| **Find & Replace** | `Ctrl + F` | `Cmd + F` | Open modeless Find and Replace dialog. |
| **Toggle Proofreading / Edit Mode** | `F2` | `F2` | Toggle between viewing and direct text editing. |
| **Split Speaker Block** | `Shift + Enter` | `Shift + Enter` | Split dialogue turn and insert speaker at cursor. |
| **Split Block at Playhead** | `Ctrl + K` | `Cmd + K` | Cut active transcript block at current playback timestamp. |
| **Merge with Next Block** | `Ctrl + J` | `Cmd + J` | Combine current transcript block with following turn. |
| **Word Highlighting & Seek** | `Click Word` | `Click Word` | Seek audio playback directly to spoken word. |
"""

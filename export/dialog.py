"""Unified Export Dialog for Radio & TV Story Segmenter.

Dynamically discovers export destinations from enabled plugins via PluginManager.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PySide6.QtCore import Qt, QSettings, QEvent
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSpinBox,
        QStackedWidget,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    Qt = None
    QSettings = None
    QDialog = object

from prs_shared import (
    INTERNAL_APP_ID,
    CollapsibleSection,
    format_time,
    safe_filename,
)
from plugins.base import ExportDestination


DEFAULT_EXPORT_DESTINATIONS_ORDER = ["local", "wordpress", "gdocs", "youtube"]


def get_export_destinations_order() -> List[str]:
    """Retrieve user-configured export destination ordering."""
    if not QSettings:
        return list(DEFAULT_EXPORT_DESTINATIONS_ORDER)
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    raw = settings.value("export_destinations_order", None)
    if raw:
        if isinstance(raw, list):
            return [str(x) for x in raw]
        elif isinstance(raw, str):
            return [x.strip() for x in raw.split(",") if x.strip()]
    return list(DEFAULT_EXPORT_DESTINATIONS_ORDER)


def save_export_destinations_order(order: List[str]) -> None:
    """Persist user-configured export destination ordering."""
    if not QSettings:
        return
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    settings.setValue("export_destinations_order", order)


class ReorderExportDestinationsDialog(QDialog):
    """Dialog allowing the user to reorder export destinations via drag-and-drop or Move Up/Down."""

    def __init__(self, parent: Optional[QWidget] = None, available_dests: Optional[List[Tuple[str, str]]] = None):
        super().__init__(parent)
        self.setWindowTitle("Customize Export Destinations Order")
        self.resize(460, 360)
        self.setMinimumSize(400, 300)
        make_dialog_maximizable(self)

        # available_dests is a list of (dest_id, dest_title)
        self.available_dests = available_dests or [
            ("local", "Local Files (Media & Transcripts)"),
            ("wordpress", "WordPress Draft Post"),
            ("gdocs", "Google Docs"),
            ("youtube", "YouTube Studio (Assisted Upload)"),
        ]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info_lbl = QLabel(
            "Drag and drop destinations to customize their display order in the Export window, "
            "or use the <b>Move Up</b> / <b>Move Down</b> buttons:"
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(info_lbl)

        content_row = QHBoxLayout()
        self.list_widget = QListWidget(self)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
                color: #f8fafc;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #334155;
                border-radius: 4px;
                margin-bottom: 2px;
            }
            QListWidget::item:selected {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
            }
        """)

        # Populate according to current saved order
        current_order = get_export_destinations_order()
        dest_map = {d_id: title for d_id, title in self.available_dests}

        # First add items in current_order
        added_ids = set()
        for d_id in current_order:
            if d_id in dest_map:
                item = QListWidgetItem(f"☰  {dest_map[d_id]}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)
                added_ids.add(d_id)

        # Then add any missing available destinations
        for d_id, title in self.available_dests:
            if d_id not in added_ids:
                item = QListWidgetItem(f"☰  {title}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)

        content_row.addWidget(self.list_widget, 1)

        # Buttons on the right: Move Up, Move Down, Reset
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)

        self.up_btn = QPushButton("▲ Move Up")
        self.up_btn.clicked.connect(self._move_up)
        btn_col.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼ Move Down")
        self.down_btn.clicked.connect(self._move_down)
        btn_col.addWidget(self.down_btn)

        btn_col.addSpacing(10)
        self.reset_btn = QPushButton("Reset Default")
        self.reset_btn.setToolTip("Reset order to: Local, WordPress, Google Docs, YouTube Studio")
        self.reset_btn.clicked.connect(self._reset_default)
        btn_col.addWidget(self.reset_btn)

        btn_col.addStretch()
        content_row.addLayout(btn_col)
        layout.addLayout(content_row)

        # Dialog buttons (Save Order, Cancel)
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.ok_btn = QPushButton("Save Order")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._save_and_accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.ok_btn)
        btn_box.addWidget(self.cancel_btn)
        layout.addLayout(btn_box)

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row >= 0 and row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _reset_default(self):
        self.list_widget.clear()
        dest_map = {d_id: title for d_id, title in self.available_dests}
        for d_id in DEFAULT_EXPORT_DESTINATIONS_ORDER:
            if d_id in dest_map:
                item = QListWidgetItem(f"☰  {dest_map[d_id]}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)
        for d_id, title in self.available_dests:
            if d_id not in DEFAULT_EXPORT_DESTINATIONS_ORDER:
                item = QListWidgetItem(f"☰  {title}")
                item.setData(Qt.ItemDataRole.UserRole, d_id)
                self.list_widget.addItem(item)

    def _save_and_accept(self):
        order = []
        for i in range(self.list_widget.count()):
            d_id = self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            if d_id:
                order.append(str(d_id))
        save_export_destinations_order(order)
        self.accept()


class UnifiedExportDialog(QDialog):
    """Unified Export Center supporting Local Files and dynamic plugin destinations."""

    def __init__(self, main_window: Any, initial_scope: str = "full", initial_dest: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.setWindowTitle("Export")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.setSizeGripEnabled(True)
        self.setMinimumWidth(780)
        self.setMinimumHeight(560)
        self.resize(860, 700)

        self._dest_entries: List[Dict[str, Any]] = []
        self._plugin_destinations: List[Tuple[QRadioButton, ExportDestination, QWidget]] = []
        self._temp_preview_files = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header bar with Expand / Collapse All control and Maximize / Restore button
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(2, 0, 2, 0)
        hdr_row.setSpacing(6)
        hdr_label = QLabel("<b>Unified Export Center</b>")
        hdr_label.setStyleSheet("font-size: 13px; color: #f1f5f9;")
        self.toggle_all_btn = QPushButton("▾ Collapse All")
        self.toggle_all_btn.setToolTip("Toggle expand/collapse for all sections on the current page")
        self.toggle_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
        """)
        self.toggle_all_btn.clicked.connect(self._toggle_all_sections)

        self.maximize_btn = QPushButton("⛶", self)
        self.maximize_btn.setToolTip("Maximize Export window")
        self.maximize_btn.setFixedSize(28, 24)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 0px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
        """)
        self.maximize_btn.clicked.connect(self._toggle_maximize)

        hdr_row.addWidget(hdr_label)
        hdr_row.addStretch()
        hdr_row.addWidget(self.toggle_all_btn)
        hdr_row.addWidget(self.maximize_btn)
        layout.addLayout(hdr_row)

        # Export Destination Selection
        self.dest_section = CollapsibleSection("Export Destination", self, is_expanded=True)
        self.dest_content_layout = QHBoxLayout()
        self.dest_button_group = QButtonGroup(self)

        # Scope Selection
        is_music = getattr(self.main_window, "story_detection_mode", "voice") == "music"
        term_plural = "Songs" if is_music else "Stories"
        self.scope_section = CollapsibleSection("Export Scope", self, is_expanded=True)
        self.scope_combo = QComboBox()
        self.scope_combo.addItem(f"Selected {term_plural}", "selected_stories")
        self.scope_combo.addItem(f"All {term_plural}", "all_stories")
        self.scope_combo.addItem("Full Episode", "full")
        self.scope_combo.addItem(f"Full Episode & All {term_plural}", "full_and_all_stories")

        idx = self.scope_combo.findData(initial_scope)
        if idx >= 0:
            self.scope_combo.setCurrentIndex(idx)
        else:
            selected_rows = getattr(self.main_window, "current_selected_story_indices", [])
            if selected_rows:
                self.scope_combo.setCurrentIndex(0)
            elif getattr(self.main_window, "stories", []):
                self.scope_combo.setCurrentIndex(1)
            else:
                self.scope_combo.setCurrentIndex(2)

        self.scope_section.add_widget(self.scope_combo)
        layout.addWidget(self.dest_section)
        layout.addWidget(self.scope_section)

        # Stacked Widget for Destinations
        self.stacked_widget = QStackedWidget()

        # Bottom Buttons & Actions initialized early to prevent AttributeError during destination setup
        self.export_btn = QPushButton("Export Files...")
        self.export_btn.setDefault(True)
        self.save_defaults_btn = QPushButton("Save Options as Default")
        self.save_defaults_btn.setToolTip("Save the current export options as the default for future exports.")
        self.cancel_btn = QPushButton("Cancel")

        # Build Destination Radio Buttons and Pages
        self.radio_local = QRadioButton("Local Files (Media && Transcripts)")
        self.local_page = self._create_local_page()
        self.stacked_widget.addWidget(self.local_page)

        self._build_destinations_layout()
        self.dest_section.add_layout(self.dest_content_layout)

        layout.addWidget(self.stacked_widget)

        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)

        # Bottom Buttons layout
        btns = QHBoxLayout()
        btns.addWidget(self.save_defaults_btn)
        btns.addStretch()
        btns.addWidget(self.export_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.save_defaults_btn.clicked.connect(lambda: self.save_options_to_settings(as_default=True))
        self.cancel_btn.clicked.connect(self.reject)
        self.export_btn.clicked.connect(self._handle_accept)

        self._load_saved_options()

        # Handle initial_dest routing
        if initial_dest:
            for entry in self._dest_entries:
                if entry["id"] == initial_dest:
                    entry["radio"].setChecked(True)
                    break

        self._on_dest_changed()

    def _build_destinations_layout(self):
        """Construct destination radio buttons in customized user order."""
        # Clear existing buttons in dest_content_layout
        while self.dest_content_layout.count():
            item = self.dest_content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Discover plugin destinations
        plugin_mgr = getattr(self.main_window, "plugin_manager", None)
        registered_dests: List[ExportDestination] = []
        if plugin_mgr and hasattr(plugin_mgr, "get_export_destinations"):
            registered_dests = plugin_mgr.get_export_destinations()

        # Prepare registry of all available destinations
        # Format: {"id": str, "title": str, "radio": QRadioButton, "page": QWidget, "dest_obj": Optional[ExportDestination]}
        raw_entries = []
        
        # Local
        raw_entries.append({
            "id": "local",
            "title": "Local Files (Media && Transcripts)",
            "clean_title": "Local Files (Media & Transcripts)",
            "radio": self.radio_local,
            "page": self.local_page,
            "dest_obj": None,
        })

        # Plugin destinations
        self._plugin_destinations = []
        for dest in registered_dests:
            # Check if page already exists or create new
            page = None
            for entry in getattr(self, "_dest_entries", []):
                if entry["id"] == dest.id and entry.get("page"):
                    page = entry["page"]
                    break
            if page is None:
                page = dest.create_widget(self.stacked_widget, self.main_window)
                self.stacked_widget.addWidget(page)

            clean_t = dest.title.replace("&&", "&")
            radio = QRadioButton(clean_t)
            raw_entries.append({
                "id": dest.id,
                "title": clean_t,
                "clean_title": clean_t,
                "radio": radio,
                "page": page,
                "dest_obj": dest,
            })
            self._plugin_destinations.append((radio, dest, page))

        # Order entries according to user preferences
        order = get_export_destinations_order()
        order_index_map = {d_id: i for i, d_id in enumerate(order)}

        def _sort_key(e):
            return order_index_map.get(e["id"], 999)

        sorted_entries = sorted(raw_entries, key=_sort_key)
        self._dest_entries = sorted_entries

        # Add to button group and layout
        for entry in sorted_entries:
            radio = entry["radio"]
            self.dest_button_group.addButton(radio)
            self.dest_content_layout.addWidget(radio)
            radio.toggled.connect(self._on_dest_changed)

        # Add Reorder Button
        self.reorder_dests_btn = QPushButton("⇅ Reorder…")
        self.reorder_dests_btn.setToolTip("Customize the display order of export destinations")
        self.reorder_dests_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0284c7;
                border: 1px solid #0284c7;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.reorder_dests_btn.clicked.connect(self._on_reorder_destinations)
        self.dest_content_layout.addStretch()
        self.dest_content_layout.addWidget(self.reorder_dests_btn)

        # Select first destination if none selected
        if not any(e["radio"].isChecked() for e in sorted_entries):
            sorted_entries[0]["radio"].setChecked(True)

    def _on_reorder_destinations(self):
        """Open reorder dialog and rebuild layout on change."""
        available = [(e["id"], e["clean_title"]) for e in self._dest_entries]
        dlg = ReorderExportDestinationsDialog(self, available_dests=available)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Remember currently checked ID
            current_id = "local"
            for e in self._dest_entries:
                if e["radio"].isChecked():
                    current_id = e["id"]
                    break

            self._build_destinations_layout()

            # Restore checked ID
            for e in self._dest_entries:
                if e["id"] == current_id:
                    e["radio"].setChecked(True)
                    break
            self._on_dest_changed()
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)

        # Bottom Buttons
        btns = QHBoxLayout()
        self.save_defaults_btn = QPushButton("Save Options as Default")
        self.save_defaults_btn.setToolTip("Save the current export options as the default for future exports.")
        btns.addWidget(self.save_defaults_btn)
        btns.addStretch()
        self.export_btn = QPushButton("Export Files...")
        self.export_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        btns.addWidget(self.export_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.save_defaults_btn.clicked.connect(lambda: self.save_options_to_settings(as_default=True))
        self.cancel_btn.clicked.connect(self.reject)
        self.export_btn.clicked.connect(self._handle_accept)

        self._load_saved_options()

        # Handle initial_dest routing
        if initial_dest:
            for r, d, _ in self._plugin_destinations:
                if d.id == initial_dest:
                    r.setChecked(True)
                    break

        self._on_dest_changed()

    def _create_local_page(self) -> QWidget:
        local_page = QWidget()
        local_page_layout = QVBoxLayout(local_page)
        local_page_layout.setContentsMargins(0, 0, 0, 0)

        local_scroll = QScrollArea()
        local_scroll.setWidgetResizable(True)
        local_scroll.setFrameShape(QFrame.Shape.NoFrame)
        local_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        local_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        local_scroll_content = QWidget()
        local_layout = QVBoxLayout(local_scroll_content)
        local_layout.setContentsMargins(2, 2, 2, 2)
        local_layout.setSpacing(10)

        self.formats_section = CollapsibleSection("Export Formats", self, is_expanded=True, subtitle="TXT, DOCX, PDF, Media...")
        self.cb_txt = QCheckBox("Text transcript (.txt)")
        self.cb_docx = QCheckBox("Word document (.docx)")
        self.cb_pdf = QCheckBox("PDF document (.pdf)")
        self.cb_srt = QCheckBox("SubRip subtitles (.srt)")
        self.cb_vtt = QCheckBox("WebVTT subtitles (.vtt)")
        self.cb_cue = QCheckBox("CUE sheet (.cue)")
        self.cb_tracklist = QCheckBox("Tracklist / YouTube Chapters (.txt)")
        self.cb_rpp = QCheckBox("Cockos REAPER project (.rpp)")
        self.cb_edl = QCheckBox("Samplitude EDL v1.5 (.edl)")
        self.cb_audacity = QCheckBox("Audacity label track (.txt)")
        self.cb_audition_xml = QCheckBox("Adobe Audition / FCP XML (.xml)")
        self.cb_daw_csv = QCheckBox("Universal DAW marker list (.csv)")

        audio_file = getattr(self.main_window, "audio_file", None)
        media_ext = audio_file.suffix.lower() if audio_file else "media"
        self.cb_media = QCheckBox(f"Media clip ({media_ext})")

        self.cb_apply_fades = QCheckBox("Apply audio fade-in & fade-out")
        self.cb_apply_fades.setToolTip("Renders smooth audio fade ramps at start and end of exported story media clips.")
        settings = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
        self.cb_apply_fades.setChecked(str(settings.value("export_apply_audio_fades", "true")).lower() in {"1", "true", "yes"})

        is_music_mode = getattr(self.main_window, "story_detection_mode", "") == "music"
        self.cb_txt.setChecked(not is_music_mode)
        self.cb_docx.setChecked(not is_music_mode)
        self.cb_pdf.setChecked(not is_music_mode)
        self.cb_cue.setChecked(is_music_mode)
        self.cb_tracklist.setChecked(is_music_mode)
        self.cb_rpp.setChecked(False)
        self.cb_edl.setChecked(False)
        self.cb_audacity.setChecked(False)
        self.cb_audition_xml.setChecked(False)
        self.cb_daw_csv.setChecked(False)
        self.cb_media.setChecked(audio_file is not None)
        self.cb_media.setEnabled(audio_file is not None)
        self.cb_apply_fades.setEnabled(audio_file is not None and self.cb_media.isChecked())
        self.cb_media.toggled.connect(lambda checked: self.cb_apply_fades.setEnabled(checked))

        self.formats_section.add_widget(self.cb_txt)
        self.formats_section.add_widget(self.cb_docx)
        self.formats_section.add_widget(self.cb_pdf)
        self.formats_section.add_widget(self.cb_srt)
        self.formats_section.add_widget(self.cb_vtt)
        self.formats_section.add_widget(self.cb_cue)

        tracklist_row = QHBoxLayout()
        tracklist_row.addWidget(self.cb_tracklist)
        self.copy_yt_btn = QPushButton("📋 Copy Chapters")
        self.copy_yt_btn.setToolTip("Copy formatted YouTube chapter markers to clipboard immediately")
        self.copy_yt_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.copy_yt_btn.clicked.connect(self._copy_youtube_chapters)
        tracklist_row.addWidget(self.copy_yt_btn)
        tracklist_row.addStretch()
        self.formats_section.add_layout(tracklist_row)

        self.formats_section.add_widget(self.cb_rpp)
        self.formats_section.add_widget(self.cb_edl)
        self.formats_section.add_widget(self.cb_audacity)
        self.formats_section.add_widget(self.cb_audition_xml)
        self.formats_section.add_widget(self.cb_daw_csv)

        unselected_row = QHBoxLayout()
        unselected_row.setSpacing(8)
        lbl_unsel = QLabel("Unselected Audio Mode:")
        lbl_unsel.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        unselected_row.addWidget(lbl_unsel)
        self.unselected_audio_combo = QComboBox()
        self.unselected_audio_combo.addItem("Exclude unselected audio", "exclude")
        self.unselected_audio_combo.addItem("Include unselected audio (Split Clips)", "split")
        self.unselected_audio_combo.addItem("Include unselected audio (Muted Clips)", "muted")
        self.unselected_audio_combo.setToolTip("Controls how unselected audio gaps between story segments are handled in DAW timeline exports.")
        self.unselected_audio_combo.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                selection-background-color: #0284c7;
            }
        """)
        unselected_row.addWidget(self.unselected_audio_combo)
        unselected_row.addStretch()
        self.formats_section.add_layout(unselected_row)

        media_row = QHBoxLayout()
        media_row.setSpacing(10)
        media_row.addWidget(self.cb_media)
        media_row.addWidget(self.cb_apply_fades)

        self.edit_id3_btn = QPushButton("🏷️ Edit ID3 Tags")
        self.edit_id3_btn.setToolTip("Open MP3 ID3 Tag Editor dialog")
        self.edit_id3_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.edit_id3_btn.clicked.connect(self._open_id3_editor)
        media_row.addWidget(self.edit_id3_btn)
        media_row.addStretch()

        self.formats_section.add_layout(media_row)
        local_layout.addWidget(self.formats_section)

        # Content & Language options
        self.content_section = CollapsibleSection("Content & Language Options", self, is_expanded=True, subtitle="Speakers, Timestamps, Comments")
        self.cb_speakers = QCheckBox("Include Speaker Labels")
        self.cb_speakers.setChecked(True)
        self.cb_timestamps = QCheckBox("Include Timestamps")
        self.cb_timestamps.setChecked(False)
        self.cb_notes = QCheckBox("Include Comments")
        self.cb_notes.setToolTip("Include transcript comments in exported DOCX and PDF documents")
        self.cb_notes.setChecked(True)
        self.cb_highlights = QCheckBox("Include Comment Highlights")
        self.cb_highlights.setToolTip("Apply visual highlights to commented sections in exported DOCX and PDF documents")
        self.cb_highlights.setChecked(True)

        src_code = self.main_window.source_language_code() if hasattr(self.main_window, "source_language_code") else "en"
        has_translation = False
        if hasattr(self.main_window, "get_spanish_translation_item"):
            trans_item = self.main_window.get_spanish_translation_item()
            if trans_item and isinstance(trans_item, dict):
                has_translation = bool(trans_item.get("segments"))

        if src_code == "es":
            self.cb_es = QCheckBox("Spanish")
            self.cb_es.setChecked(True)
            self.cb_es.setEnabled(True)

            self.cb_en = QCheckBox("English (Translated)")
            self.cb_en.setChecked(has_translation)
            self.cb_en.setEnabled(has_translation)
            if not has_translation:
                self.cb_en.setToolTip("English translation is not available for this project. Generate a translation first to enable.")
        else:
            self.cb_en = QCheckBox("English")
            self.cb_en.setChecked(True)
            self.cb_en.setEnabled(True)

            self.cb_es = QCheckBox("Spanish (Translated)")
            self.cb_es.setChecked(has_translation)
            self.cb_es.setEnabled(has_translation)
            if not has_translation:
                self.cb_es.setToolTip("Spanish translation is not available for this project. Generate a translation first to enable.")

        self.content_section.add_widget(self.cb_speakers)
        self.content_section.add_widget(self.cb_timestamps)
        self.content_section.add_widget(self.cb_notes)
        self.content_section.add_widget(self.cb_highlights)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.cb_en)
        lang_layout.addWidget(self.cb_es)
        lang_layout.addStretch()
        self.content_section.add_layout(lang_layout)
        local_layout.addWidget(self.content_section)

        # Location & Filename Section
        self.loc_section = CollapsibleSection("Export Location & Filename", self, is_expanded=True)
        fn_row = QHBoxLayout()
        fn_row.addWidget(QLabel("Base Filename:"))
        default_name = Path(audio_file).stem if audio_file else "export"
        self.filename_edit = QLineEdit(default_name)
        fn_row.addWidget(self.filename_edit)
        self.loc_section.add_layout(fn_row)

        self.loc_group = QButtonGroup(self)
        self.loc_radio_default = QRadioButton("Project Folder (or prompt on export)")
        self.loc_radio_custom = QRadioButton("Custom Folder:")
        self.loc_radio_default.setChecked(True)
        self.loc_group.addButton(self.loc_radio_default)
        self.loc_group.addButton(self.loc_radio_custom)
        self.loc_section.add_widget(self.loc_radio_default)

        custom_row = QHBoxLayout()
        custom_row.addWidget(self.loc_radio_custom)
        self.loc_custom_path_edit = QLineEdit()
        self.loc_custom_path_edit.setEnabled(False)
        custom_row.addWidget(self.loc_custom_path_edit, 1)
        self.loc_browse_btn = QPushButton("Browse...")
        self.loc_browse_btn.setEnabled(False)
        self.loc_browse_btn.clicked.connect(self._browse_custom_export_location)
        custom_row.addWidget(self.loc_browse_btn)
        self.loc_section.add_layout(custom_row)

        self.loc_radio_default.toggled.connect(self._on_location_radio_toggled)
        self.loc_radio_custom.toggled.connect(self._on_location_radio_toggled)
        local_layout.addWidget(self.loc_section)

        local_layout.addStretch()
        local_scroll.setWidget(local_scroll_content)
        local_page_layout.addWidget(local_scroll)
        return local_page

    def _on_location_radio_toggled(self):
        use_custom = self.loc_radio_custom.isChecked()
        self.loc_custom_path_edit.setEnabled(use_custom)
        self.loc_browse_btn.setEnabled(use_custom)

    def _browse_custom_export_location(self):
        initial = self.loc_custom_path_edit.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Export Location", initial)
        if folder:
            self.loc_custom_path_edit.setText(folder)
            self.loc_radio_custom.setChecked(True)

    def _toggle_all_sections(self):
        all_sections = [self.dest_section, self.scope_section]
        curr_widget = self.stacked_widget.currentWidget()
        if curr_widget:
            child_sections = curr_widget.findChildren(CollapsibleSection)
            all_sections.extend(child_sections)

        active_sections = [s for s in all_sections if s is not None and s.isVisible()]
        if not active_sections:
            return
        any_expanded = any(s.is_expanded() for s in active_sections)
        new_state = not any_expanded
        for s in active_sections:
            s.set_expanded(new_state)
        self.toggle_all_btn.setText("▾ Collapse All" if new_state else "▸ Expand All")

    def _on_dest_changed(self):
        for entry in self._dest_entries:
            if entry["radio"].isChecked():
                self.stacked_widget.setCurrentWidget(entry["page"])
                if hasattr(self, "export_btn") and self.export_btn:
                    if entry["id"] == "local":
                        self.export_btn.setText("Export Files...")
                    else:
                        dest = entry.get("dest_obj")
                        btn_lbl = getattr(dest, "button_label", None) or f"Export to {getattr(dest, 'title', 'Destination')}..."
                        self.export_btn.setText(btn_lbl)
                break

    def _on_scope_changed(self):
        scope = self.scope_combo.currentData()
        stories = getattr(self.main_window, "stories", []) or []
        for _, dest, _ in self._plugin_destinations:
            dest.on_scope_changed(scope, stories)

    def _open_id3_editor(self):
        """Open the ID3 Tag Editor for MP3 files."""
        if hasattr(self.main_window, "open_id3_tag_editor"):
            self.main_window.open_id3_tag_editor()
        else:
            try:
                from id3_editor import ID3TagEditorDialog
                dlg = ID3TagEditorDialog(parent=self.main_window or self)
                dlg.exec()
            except Exception as exc:
                QMessageBox.critical(self, "ID3 Editor Error", f"Failed to launch ID3 Tag Editor:\n\n{exc}")

    def _copy_youtube_chapters(self):
        if hasattr(self.main_window, "copy_youtube_chapters_to_clipboard"):
            copied = self.main_window.copy_youtube_chapters_to_clipboard()
            if copied:
                QMessageBox.information(self, "Chapters Copied", "YouTube chapter markers copied to clipboard!")
        else:
            from export.subtitles import generate_youtube_chapters
            stories = getattr(self.main_window, "stories", [])
            if not stories:
                QMessageBox.warning(self, "No Stories", "No stories available to generate chapters.")
                return
            chapters = generate_youtube_chapters(stories)
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(chapters)
                QMessageBox.information(self, "Chapters Copied", "YouTube chapter markers copied to clipboard!")

    def _load_saved_options(self):
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.cb_txt.setChecked(str(settings.value("export_opt_fmt_txt", "true")).lower() in {"1", "true", "yes"})
        self.cb_docx.setChecked(str(settings.value("export_opt_fmt_docx", "true")).lower() in {"1", "true", "yes"})
        self.cb_pdf.setChecked(str(settings.value("export_opt_fmt_pdf", "true")).lower() in {"1", "true", "yes"})
        self.cb_srt.setChecked(str(settings.value("export_opt_fmt_srt", "false")).lower() in {"1", "true", "yes"})
        self.cb_vtt.setChecked(str(settings.value("export_opt_fmt_vtt", "false")).lower() in {"1", "true", "yes"})
        self.cb_cue.setChecked(str(settings.value("export_opt_fmt_cue", "false")).lower() in {"1", "true", "yes"})
        self.cb_tracklist.setChecked(str(settings.value("export_opt_fmt_tracklist", "false")).lower() in {"1", "true", "yes"})
        self.cb_rpp.setChecked(str(settings.value("export_opt_fmt_rpp", "false")).lower() in {"1", "true", "yes"})
        self.cb_edl.setChecked(str(settings.value("export_opt_fmt_edl", "false")).lower() in {"1", "true", "yes"})
        self.cb_audacity.setChecked(str(settings.value("export_opt_fmt_audacity", "false")).lower() in {"1", "true", "yes"})
        self.cb_audition_xml.setChecked(str(settings.value("export_opt_fmt_audition_xml", "false")).lower() in {"1", "true", "yes"})
        self.cb_daw_csv.setChecked(str(settings.value("export_opt_fmt_daw_csv", "false")).lower() in {"1", "true", "yes"})

        unsel_mode = str(settings.value("export_opt_unselected_audio_mode", "exclude")).lower().strip()
        idx = self.unselected_audio_combo.findData(unsel_mode)
        if idx >= 0:
            self.unselected_audio_combo.setCurrentIndex(idx)

        if self.cb_media.isEnabled():
            self.cb_media.setChecked(str(settings.value("export_opt_fmt_media", "false")).lower() in {"1", "true", "yes"})

        self.cb_speakers.setChecked(str(settings.value("export_opt_include_speakers", "true")).lower() in {"1", "true", "yes"})
        self.cb_timestamps.setChecked(str(settings.value("export_opt_include_timestamps", "false")).lower() in {"1", "true", "yes"})
        self.cb_notes.setChecked(str(settings.value("export_opt_include_notes", "true")).lower() in {"1", "true", "yes"})
        src_code = self.main_window.source_language_code() if hasattr(self.main_window, "source_language_code") else "en"
        if src_code == "es":
            if self.cb_es.isEnabled():
                self.cb_es.setChecked(str(settings.value("export_opt_include_es", "true")).lower() in {"1", "true", "yes"})
            if self.cb_en.isEnabled():
                self.cb_en.setChecked(str(settings.value("export_opt_include_en", "true")).lower() in {"1", "true", "yes"})
        else:
            if self.cb_en.isEnabled():
                self.cb_en.setChecked(str(settings.value("export_opt_include_en", "true")).lower() in {"1", "true", "yes"})
            if self.cb_es.isEnabled():
                self.cb_es.setChecked(str(settings.value("export_opt_include_es", "false")).lower() in {"1", "true", "yes"})

        use_custom_loc = str(settings.value("export_opt_custom_loc_enabled", "false")).lower() in {"1", "true", "yes"}
        saved_custom_dir = str(settings.value("export_opt_custom_dir", "") or "").strip()
        if saved_custom_dir and os.path.isdir(saved_custom_dir):
            self.loc_custom_path_edit.setText(saved_custom_dir)
            if use_custom_loc:
                self.loc_radio_custom.setChecked(True)
        self._on_location_radio_toggled()

    def save_options_to_settings(self, as_default: bool = False):
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        settings.setValue("export_opt_fmt_txt", self.cb_txt.isChecked())
        settings.setValue("export_opt_fmt_docx", self.cb_docx.isChecked())
        settings.setValue("export_opt_fmt_pdf", self.cb_pdf.isChecked())
        settings.setValue("export_opt_fmt_srt", self.cb_srt.isChecked())
        settings.setValue("export_opt_fmt_vtt", self.cb_vtt.isChecked())
        settings.setValue("export_opt_fmt_cue", self.cb_cue.isChecked())
        settings.setValue("export_opt_fmt_tracklist", self.cb_tracklist.isChecked())
        settings.setValue("export_opt_fmt_rpp", self.cb_rpp.isChecked())
        settings.setValue("export_opt_fmt_edl", self.cb_edl.isChecked())
        settings.setValue("export_opt_fmt_audacity", self.cb_audacity.isChecked())
        settings.setValue("export_opt_fmt_audition_xml", self.cb_audition_xml.isChecked())
        settings.setValue("export_opt_fmt_daw_csv", self.cb_daw_csv.isChecked())
        settings.setValue("export_opt_unselected_audio_mode", self.unselected_audio_combo.currentData())
        settings.setValue("export_opt_fmt_media", self.cb_media.isChecked())

        settings.setValue("export_opt_include_speakers", self.cb_speakers.isChecked())
        settings.setValue("export_opt_include_timestamps", self.cb_timestamps.isChecked())
        settings.setValue("export_opt_include_notes", self.cb_notes.isChecked())
        settings.setValue("export_opt_include_en", self.cb_en.isChecked())
        settings.setValue("export_opt_include_es", self.cb_es.isChecked())

        settings.setValue("export_opt_custom_loc_enabled", self.loc_radio_custom.isChecked())
        custom_dir = self.loc_custom_path_edit.text().strip()
        if custom_dir:
            settings.setValue("export_opt_custom_dir", custom_dir)

        settings.sync()
        if as_default:
            QMessageBox.information(self, "Export Options", "Current export options have been saved as defaults.")

    def _handle_accept(self):
        if self.radio_local.isChecked():
            if self.loc_radio_custom.isChecked():
                custom_path = self.loc_custom_path_edit.text().strip()
                if not custom_path or not os.path.isdir(custom_path):
                    QMessageBox.warning(self, "Export Location", "Please select a valid directory for the custom export location.")
                    return

            formats = {
                "txt": self.cb_txt.isChecked(),
                "docx": self.cb_docx.isChecked(),
                "pdf": self.cb_pdf.isChecked(),
                "srt": self.cb_srt.isChecked(),
                "vtt": self.cb_vtt.isChecked(),
                "media": self.cb_media.isChecked(),
                "cue": self.cb_cue.isChecked(),
                "tracklist": self.cb_tracklist.isChecked(),
                "rpp": self.cb_rpp.isChecked(),
                "edl": self.cb_edl.isChecked(),
                "audacity": self.cb_audacity.isChecked(),
                "audition_xml": self.cb_audition_xml.isChecked(),
                "daw_csv": self.cb_daw_csv.isChecked(),
            }
            if not any(formats.values()):
                QMessageBox.warning(self, "Export", "Please select at least one format to export.")
                return

            if (formats["txt"] or formats["docx"] or formats["pdf"]) and not self.cb_en.isChecked() and not self.cb_es.isChecked():
                QMessageBox.warning(self, "Export", "Please select at least one language track (English or Spanish).")
                return
        else:
            for radio, dest, _ in self._plugin_destinations:
                if radio.isChecked():
                    valid, err = dest.validate()
                    if not valid:
                        QMessageBox.warning(self, "Export", err or "Export validation failed.")
                        return
                    break

        self.accept()

    def get_result(self) -> Dict[str, Any]:
        scope = self.scope_combo.currentData()
        if self.radio_local.isChecked():
            formats = {
                "txt": self.cb_txt.isChecked(),
                "docx": self.cb_docx.isChecked(),
                "pdf": self.cb_pdf.isChecked(),
                "srt": self.cb_srt.isChecked(),
                "vtt": self.cb_vtt.isChecked(),
                "media": self.cb_media.isChecked(),
                "cue": self.cb_cue.isChecked(),
                "tracklist": self.cb_tracklist.isChecked(),
                "rpp": self.cb_rpp.isChecked(),
                "edl": self.cb_edl.isChecked(),
                "audacity": self.cb_audacity.isChecked(),
                "audition_xml": self.cb_audition_xml.isChecked(),
                "daw_csv": self.cb_daw_csv.isChecked(),
            }
            apply_fades = self.cb_apply_fades.isChecked()
            unselected_mode = self.unselected_audio_combo.currentData() or "exclude"
            settings = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
            settings.setValue("export_apply_audio_fades", "true" if apply_fades else "false")
            settings.setValue("export_opt_unselected_audio_mode", unselected_mode)

            options = {
                "include_speakers": self.cb_speakers.isChecked(),
                "include_timestamps": self.cb_timestamps.isChecked(),
                "include_comments": self.cb_notes.isChecked(),
                "include_notes": self.cb_notes.isChecked(),
                "include_highlights": self.cb_highlights.isChecked(),
                "include_english": self.cb_en.isChecked(),
                "include_spanish": self.cb_es.isChecked(),
                "apply_audio_fades": apply_fades,
                "unselected_audio_mode": unselected_mode,
            }
            base = safe_filename(self.filename_edit.text().strip() or "export")
            export_dir = None
            if self.loc_radio_custom.isChecked() and self.loc_custom_path_edit.text().strip():
                export_dir = self.loc_custom_path_edit.text().strip()
            return {
                "destination": "local",
                "scope": scope,
                "formats": formats,
                "options": options,
                "base": base,
                "export_dir": export_dir,
            }

        for radio, dest, _ in self._plugin_destinations:
            if radio.isChecked():
                data = dest.get_export_data()
                return {
                    "destination": dest.id,
                    "scope": scope,
                    **data,
                }

        return {"destination": "local", "scope": scope}

    def done(self, r: int):
        if r != QDialog.DialogCode.Accepted:
            for temp_f in self._temp_preview_files:
                try:
                    if temp_f and Path(temp_f).exists():
                        Path(temp_f).unlink(missing_ok=True)
                except Exception:
                    pass
        super().done(r)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("⛶")
            self.maximize_btn.setToolTip("Maximize Export window")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Restore normal size")

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, "maximize_btn"):
                if self.isMaximized():
                    self.maximize_btn.setText("❐")
                    self.maximize_btn.setToolTip("Restore normal size")
                else:
                    self.maximize_btn.setText("⛶")
                    self.maximize_btn.setToolTip("Maximize Export window")

"""Radio & TV Segmenter — UI Layout & Menu Construction Mixin.

Builds the main window visual hierarchy, menu bar, status bar, timeline canvas,
interactive transcript editor, story segmentation panel, and search bar.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer, QSize
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QTextCursor, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    CommentsPanel,
    FindReplaceDialog,
    InteractiveTranscriptEdit,
    StoryListWidget,
    TimelineWidget,
    ffmpeg_path,
    ffprobe_path,
    format_time,
    platform_seq,
    safe_filename,
)


from ui_menus import PersistentMenu, UiMenusMixin
from ui_dialog_launchers import UiDialogLaunchersMixin

class UiLayoutMixin(UiMenusMixin, UiDialogLaunchersMixin):
    """Mixin class providing UI construction, menu assembly, and UI event binding."""
    def build_ui(self):
        """Build and assemble all central widgets, layouts, and panels."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # -----------------------------------------------------------
        # Top Controls: Playback, Time, Save, and Status
        # -----------------------------------------------------------
        self.controls_panel = QWidget(self)
        self.controls_panel.setObjectName("controls_panel")
        controls_panel_layout = QVBoxLayout(self.controls_panel)
        controls_panel_layout.setContentsMargins(0, 0, 0, 0)
        controls_panel_layout.setSpacing(4)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self.play_button = QPushButton("Play", self)
        self.play_button.setObjectName("play_button")
        self.play_button.setMinimumWidth(80)
        self.play_button.clicked.connect(self.toggle_play)
        controls_row.addWidget(self.play_button)

        self.speed_combo = QComboBox(self)
        self.speed_combo.setObjectName("speed_combo")
        self.speed_combo.setToolTip("Playback Speed & Pitch-Preserving Audio Rate (WSOLA)")
        for rate_label, rate_val in [
            ("0.75x", 0.75),
            ("1.0x", 1.0),
            ("1.25x", 1.25),
            ("1.5x", 1.5),
            ("1.75x", 1.75),
            ("2.0x", 2.0),
        ]:
            self.speed_combo.addItem(rate_label, rate_val)
        curr_rate = float(getattr(self, "playback_rate", 1.0) or 1.0)
        idx_rate = self.speed_combo.findData(curr_rate)
        self.speed_combo.setCurrentIndex(idx_rate if idx_rate >= 0 else 1)
        self.speed_combo.currentIndexChanged.connect(
            lambda: getattr(self, "set_playback_rate", lambda v: None)(float(self.speed_combo.currentData() or 1.0))
        )
        controls_row.addWidget(self.speed_combo)

        self.time_label = QLabel("00:00:00 / 00:00:00", self)
        self.time_label.setObjectName("time_label")
        self.time_label.setMinimumWidth(160)
        controls_row.addWidget(self.time_label)

        self.speaker_status = QLabel("Speaker detection has not been run.", self)
        self.speaker_status.setStyleSheet("color: #888888; font-size: 11px;")
        controls_row.addWidget(self.speaker_status)

        controls_row.addStretch()

        self.save_state_label = QLabel("", self)
        self.save_state_label.setStyleSheet("color: #888888; font-size: 11px;")
        controls_row.addWidget(self.save_state_label)

        self.quick_save_button = QPushButton("Save Project", self)
        self.quick_save_button.setObjectName("quick_save_button")
        self.quick_save_button.clicked.connect(self.save_project)
        controls_row.addWidget(self.quick_save_button)

        controls_panel_layout.addLayout(controls_row)
        main_layout.addWidget(self.controls_panel)

        # -----------------------------------------------------------
        # Progress / Pipeline Execution Bar (Always visible when active,
        # independent of whether the timeline widget is shown or hidden)
        # -----------------------------------------------------------
        self.progress_panel = QWidget(self)
        self.progress_panel.setObjectName("progress_panel")
        progress_panel_layout = QVBoxLayout(self.progress_panel)
        progress_panel_layout.setContentsMargins(0, 0, 0, 0)
        progress_panel_layout.setSpacing(4)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)

        self.processing_stage_label = QLabel("", self)
        self.processing_stage_label.setObjectName("processing_stage_label")
        self.processing_stage_label.setStyleSheet("font-weight: bold; color: #4a90e2;")
        progress_row.addWidget(self.processing_stage_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress = self.progress_bar  # Alias used in media_batch and processing
        progress_row.addWidget(self.progress_bar, 1)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.clicked.connect(self.cancel_current_process)
        self.cancel_btn = self.cancel_button
        progress_row.addWidget(self.cancel_button)

        self.processing_stage_label.hide()
        self.progress_bar.hide()
        self.cancel_button.hide()

        progress_panel_layout.addLayout(progress_row)
        main_layout.addWidget(self.progress_panel)

        # -----------------------------------------------------------
        # Timeline and Waveform Canvas Widget
        # -----------------------------------------------------------
        self.timeline = TimelineWidget(self)
        self.timeline.setObjectName("timeline_widget")
        if hasattr(self.timeline, "canvas"):
            self.timeline.canvas.show_audio_fades = getattr(self, "enable_audio_fades", False)
        self.top_panel = self.timeline  # Compatibility alias
        main_layout.addWidget(self.timeline)

        # -----------------------------------------------------------
        # Center Panel: Splitter with Transcript View and Story Manager
        # -----------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("center_splitter")
        splitter.setChildrenCollapsible(False)
        self.center_splitter = splitter

        # Left Container: Search Header + Interactive Transcript
        self.transcript_panel = QWidget(self)
        left_widget = self.transcript_panel
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        search_bar = QHBoxLayout()
        search_bar.setSpacing(6)

        self.transcript_search_input = QLineEdit(self)
        self.transcript_search_input.setObjectName("transcript_search_input")
        self.transcript_search_input.setPlaceholderText("Search transcript...")
        self.transcript_search_input.returnPressed.connect(self.trigger_find_next)
        search_bar.addWidget(self.transcript_search_input, 1)

        self.find_next_btn = QPushButton("Find Next", self)
        self.find_next_btn.setObjectName("find_next_btn")
        self.find_next_btn.clicked.connect(self.trigger_find_next)
        search_bar.addWidget(self.find_next_btn)

        self.transcript_language_selector = QComboBox(self)
        self.transcript_language_selector.addItem("English (Original)", "en")
        self.transcript_language_selector.currentIndexChanged.connect(self.change_translation_display)
        search_bar.addWidget(self.transcript_language_selector)

        self.transcript_mode_toggle_btn = QPushButton("Edit Transcript", self)
        self.transcript_mode_toggle_btn.setCheckable(True)
        self.transcript_mode_toggle_btn.setChecked(False)
        self.transcript_mode_toggle_btn.setToolTip("Switch between interactive playback and text editing mode (F2)")
        self.transcript_mode_toggle_btn.clicked.connect(self.toggle_transcript_editing_mode)
        search_bar.addWidget(self.transcript_mode_toggle_btn)

        # 6-Color Persistent Transcript Highlighter (accessible in both View and Edit modes)
        self.current_highlight_color = "#fef08a"
        self.transcript_highlight_btn = QToolButton(self)
        self.transcript_highlight_btn.setObjectName("transcript_highlight_btn")
        self.transcript_highlight_btn.setText("Highlight ▾")
        self.transcript_highlight_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.transcript_highlight_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transcript_highlight_btn.setToolTip("Highlight selected text (Yellow) (Ctrl+Shift+H)")
        self.transcript_highlight_btn.setStyleSheet("padding: 2px 6px;")

        hdr_highlight_menu = QMenu(self.transcript_highlight_btn)
        hl_colors = [
            ("🟡 Yellow", "#fef08a"),
            ("🟢 Green", "#bbf7d0"),
            ("🔵 Blue / Cyan", "#bae6fd"),
            ("🌸 Pink", "#fbcfe8"),
            ("🟠 Orange", "#fed7aa"),
            ("🟣 Purple", "#e9d5ff"),
        ]

        def _make_hdr_hl_handler(col_hex, label_name):
            def _handler():
                self.current_highlight_color = col_hex
                self.transcript_highlight_btn.setToolTip(f"Highlight text ({label_name}) (Ctrl+Shift+H)")
                if hasattr(self, "transcript_view") and hasattr(self.transcript_view, "toggle_highlight"):
                    self.transcript_view.toggle_highlight(col_hex, force_apply=True)
            return _handler

        for label, hex_code in hl_colors:
            act = hdr_highlight_menu.addAction(label)
            act.triggered.connect(_make_hdr_hl_handler(hex_code, label))

        hdr_highlight_menu.addSeparator()
        clear_hl_act = hdr_highlight_menu.addAction("Remove Highlight")
        clear_hl_act.triggered.connect(
            lambda: getattr(self.transcript_view, "remove_highlight", lambda: None)()
        )

        self.transcript_highlight_btn.setMenu(hdr_highlight_menu)
        self.transcript_highlight_btn.clicked.connect(
            lambda: getattr(self.transcript_view, "toggle_highlight", lambda c: None)(getattr(self, "current_highlight_color", "#fef08a"))
        )
        search_bar.addWidget(self.transcript_highlight_btn)

        # Single consolidated transcript font size dropdown. The font size is independent of the
        # rest of the application and is persisted between sessions.
        self.transcript_font_size_combo = QComboBox(self)
        self.transcript_font_size_combo.setObjectName("transcript_font_size_combo")
        self.transcript_font_size_combo.setToolTip("Transcript font size (Ctrl++, Ctrl+-, Ctrl+0)")
        self.transcript_font_size_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transcript_font_size_combo.setStyleSheet("padding: 2px 6px;")
        font_scales = [
            ("80%", 0.80),
            ("90%", 0.90),
            ("100%", 1.00),
            ("110%", 1.10),
            ("120%", 1.20),
            ("130%", 1.30),
            ("140%", 1.40),
            ("150%", 1.50),
            ("160%", 1.60),
            ("175%", 1.75),
            ("180%", 1.80),
        ]
        for label, scale_val in font_scales:
            self.transcript_font_size_combo.addItem(label, scale_val)

        init_scale = getattr(self, "transcript_font_scale", 1.0)
        best_init_idx = 2
        min_diff = 999.0
        for i in range(self.transcript_font_size_combo.count()):
            val = float(self.transcript_font_size_combo.itemData(i))
            diff = abs(val - init_scale)
            if diff < min_diff:
                min_diff = diff
                best_init_idx = i
        self.transcript_font_size_combo.setCurrentIndex(best_init_idx)
        self.transcript_font_size_combo.currentIndexChanged.connect(self._on_font_size_combo_changed)
        search_bar.addWidget(self.transcript_font_size_combo)

        open_comments = False
        if hasattr(self, "settings_store") and self.settings_store is not None:
            open_comments = str(self.settings_store.value("open_comments_on_launch", "false")).lower() in {"1", "true", "yes"}
        self.show_comments = open_comments

        show_hl = True
        if hasattr(self, "settings_store") and self.settings_store is not None:
            show_hl = str(self.settings_store.value("show_comment_highlights", "true")).lower() in {"1", "true", "yes"}
        self.show_comment_highlights = show_hl

        self.comments_toggle_btn = QPushButton("💬 Comments", self)
        self.comments_toggle_btn.setObjectName("comments_toggle_btn")
        self.comments_toggle_btn.setCheckable(True)
        self.comments_toggle_btn.setChecked(self.show_comments)
        self.comments_toggle_btn.setToolTip("Toggle comments sidebar (Ctrl+Alt+C)")
        self.comments_toggle_btn.clicked.connect(lambda: getattr(self, "toggle_comments_panel", lambda: None)())
        search_bar.addWidget(self.comments_toggle_btn)

        left_layout.addLayout(search_bar)

        # Rich Text Formatting Toolbar (visible only when Editing Mode is active)
        self.transcript_format_toolbar = QWidget(self)
        self.transcript_format_toolbar.setObjectName("transcript_format_toolbar")
        fmt_layout = QHBoxLayout(self.transcript_format_toolbar)
        fmt_layout.setContentsMargins(2, 2, 2, 4)
        fmt_layout.setSpacing(4)

        self.fmt_bold_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_bold_btn.setText("B")
        self.fmt_bold_btn.setCheckable(True)
        self.fmt_bold_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_bold_btn.setToolTip("Bold (Ctrl+B)")
        self.fmt_bold_btn.setStyleSheet("font-weight: bold; min-width: 26px; padding: 2px 6px;")
        self.fmt_bold_btn.clicked.connect(lambda: getattr(self.transcript_view, "toggle_bold", lambda: None)())
        fmt_layout.addWidget(self.fmt_bold_btn)

        self.fmt_italic_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_italic_btn.setText("I")
        self.fmt_italic_btn.setCheckable(True)
        self.fmt_italic_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_italic_btn.setToolTip("Italic (Ctrl+I)")
        self.fmt_italic_btn.setStyleSheet("font-style: italic; min-width: 26px; padding: 2px 6px;")
        self.fmt_italic_btn.clicked.connect(lambda: getattr(self.transcript_view, "toggle_italic", lambda: None)())
        fmt_layout.addWidget(self.fmt_italic_btn)

        self.fmt_underline_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_underline_btn.setText("U")
        self.fmt_underline_btn.setCheckable(True)
        self.fmt_underline_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_underline_btn.setToolTip("Underline (Ctrl+U)")
        self.fmt_underline_btn.setStyleSheet("text-decoration: underline; min-width: 26px; padding: 2px 6px;")
        self.fmt_underline_btn.clicked.connect(lambda: getattr(self.transcript_view, "toggle_underline", lambda: None)())
        fmt_layout.addWidget(self.fmt_underline_btn)

        self.fmt_strike_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_strike_btn.setText("S")
        self.fmt_strike_btn.setCheckable(True)
        self.fmt_strike_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_strike_btn.setToolTip("Strikethrough (Ctrl+K)")
        self.fmt_strike_btn.setStyleSheet("text-decoration: line-through; min-width: 26px; padding: 2px 6px;")
        self.fmt_strike_btn.clicked.connect(lambda: getattr(self.transcript_view, "toggle_strikethrough", lambda: None)())
        fmt_layout.addWidget(self.fmt_strike_btn)

        fmt_sep1 = QFrame(self.transcript_format_toolbar)
        fmt_sep1.setFrameShape(QFrame.Shape.VLine)
        fmt_sep1.setFrameShadow(QFrame.Shadow.Sunken)
        fmt_layout.addWidget(fmt_sep1)

        self.fmt_clear_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_clear_btn.setText("Tx Clear")
        self.fmt_clear_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_clear_btn.setToolTip("Clear text formatting (Ctrl+\\)")
        self.fmt_clear_btn.setStyleSheet("padding: 2px 6px;")
        self.fmt_clear_btn.clicked.connect(lambda: getattr(self.transcript_view, "clear_formatting", lambda: None)())
        fmt_layout.addWidget(self.fmt_clear_btn)

        fmt_sep2 = QFrame(self.transcript_format_toolbar)
        fmt_sep2.setFrameShape(QFrame.Shape.VLine)
        fmt_sep2.setFrameShadow(QFrame.Shadow.Sunken)
        fmt_layout.addWidget(fmt_sep2)

        self.fmt_split_btn = QToolButton(self.transcript_format_toolbar)
        self.fmt_split_btn.setText("Split Speaker")
        self.fmt_split_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fmt_split_btn.setToolTip("Split speaker segment at cursor (Shift+Enter)")
        self.fmt_split_btn.setStyleSheet("padding: 2px 6px;")
        self.fmt_split_btn.clicked.connect(self._on_toolbar_split_speaker)
        fmt_layout.addWidget(self.fmt_split_btn)

        fmt_layout.addStretch()

        self.fmt_hint_lbl = QLabel("Editing Mode • Ctrl+B: Bold • Ctrl+I: Italic • Ctrl+U: Underline • Ctrl+K: Strike", self.transcript_format_toolbar)
        self.fmt_hint_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        fmt_layout.addWidget(self.fmt_hint_lbl)

        self.transcript_format_toolbar.setVisible(False)
        left_layout.addWidget(self.transcript_format_toolbar)

        self.transcript_comments_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.transcript_comments_splitter.setObjectName("transcript_comments_splitter")
        self.transcript_comments_splitter.setChildrenCollapsible(True)

        self.transcript_view = InteractiveTranscriptEdit(self)
        self.transcript_view.setObjectName("transcript_view")
        self.transcript_view.set_font_scale(getattr(self, "transcript_font_scale", 1.0))
        if hasattr(self, "show_floating_selection_toolbar"):
            self.transcript_view.show_floating_selection_toolbar = self.show_floating_selection_toolbar
        self.transcript_comments_splitter.addWidget(self.transcript_view)

        self.comments_panel = CommentsPanel(self)
        self.comments_panel.setObjectName("comments_panel")
        def _on_comment_seek(start_time, seg_idx):
            self.seek_to(start_time)
            if hasattr(self, "transcript_view") and hasattr(self.transcript_view, "select_comment_range"):
                self.transcript_view.select_comment_range(seg_idx)
        self.comments_panel.commentSeekRequested.connect(_on_comment_seek)
        self.comments_panel.commentEditRequested.connect(lambda s: getattr(self, "edit_segment_comment_dialog", getattr(self, "edit_segment_note_dialog", lambda x: None))(s))
        self.comments_panel.commentDeleteRequested.connect(lambda s: getattr(self, "delete_segment_comment", lambda x: None)(s))
        self.transcript_comments_splitter.addWidget(self.comments_panel)
        self.comments_panel.setVisible(getattr(self, "show_comments", False))
        self.transcript_comments_splitter.setStretchFactor(0, 3)
        self.transcript_comments_splitter.setStretchFactor(1, 1)

        left_layout.addWidget(self.transcript_comments_splitter, 1)

        splitter.addWidget(left_widget)

        # Right Container: Vertical Splitter dividing Stories List and Activity History
        self.right_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.right_splitter.setObjectName("right_splitter")
        self.right_splitter.setChildrenCollapsible(False)

        # Stories Box
        self.stories_panel = QWidget(self)
        self.stories_panel.setObjectName("stories_panel")
        self.stories_panel.setMinimumHeight(150)
        stories_box = self.stories_panel
        stories_box_layout = QVBoxLayout(stories_box)
        stories_box_layout.setContentsMargins(8, 8, 8, 8)
        stories_box_layout.setSpacing(6)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        self.stories_header = QLabel("Stories", stories_box)
        self.stories_header.setObjectName("stories_section_header")
        header_row.addWidget(self.stories_header)
        header_row.addStretch()

        self.popout_stories_btn = QPushButton("Pop Out", stories_box)
        self.popout_stories_btn.setObjectName("popout_stories_btn")
        self.popout_stories_btn.setToolTip("Open Story & Post Metadata in a floating window without obscuring the transcript")
        self.popout_stories_btn.setFixedHeight(20)
        self.popout_stories_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 0px 6px; margin: 0px; border-radius: 3px; }")
        self.popout_stories_btn.clicked.connect(lambda: self.open_story_metadata_dialog())
        header_row.addWidget(self.popout_stories_btn)

        self.maximize_stories_btn = QPushButton("⛶", stories_box)
        self.maximize_stories_btn.setObjectName("maximize_stories_btn")
        self.maximize_stories_btn.setToolTip("Toggle expand Stories panel across full height")
        self.maximize_stories_btn.setFixedSize(24, 20)
        self.maximize_stories_btn.setStyleSheet("QPushButton { font-size: 13px; padding: 0px; margin: 0px; border-radius: 3px; }")
        self.maximize_stories_btn.clicked.connect(self.toggle_maximize_stories_panel)
        header_row.addWidget(self.maximize_stories_btn)
        stories_box_layout.addLayout(header_row)
        stories_box_layout.setContentsMargins(6, 8, 6, 6)
        stories_box_layout.setSpacing(4)

        self.story_list = StoryListWidget(self)
        self.story_list.setObjectName("story_list")
        self.story_list.setSelectionMode(StoryListWidget.SelectionMode.ExtendedSelection)
        self.story_list.setMinimumHeight(65)
        self.story_list.setMaximumHeight(180)
        stories_box_layout.addWidget(self.story_list, 0)

        # Story Details Scroll Area
        self.story_details_scroll = QScrollArea(stories_box)
        self.story_details_scroll.setObjectName("story_details_scroll")
        self.story_details_scroll.setWidgetResizable(True)
        self.story_details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.story_details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.story_details_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.story_details_container = QWidget()
        self.story_details_container.setObjectName("story_details_container")
        details_layout = QVBoxLayout(self.story_details_container)
        details_layout.setContentsMargins(0, 2, 0, 2)
        details_layout.setSpacing(5)

        # Story Edit Inputs
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 2, 0, 2)
        form_layout.setSpacing(4)

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Story headline / title")
        self.title_input.editingFinished.connect(self.update_selected_story)
        form_layout.addRow("Title:", self.title_input)

        times_layout = QHBoxLayout()
        self.start_input = QLineEdit(self)
        self.start_input.setPlaceholderText("00:00:00")
        self.start_input.editingFinished.connect(self.update_selected_story)
        times_layout.addWidget(self.start_input)

        times_layout.addWidget(QLabel("to"))

        self.end_input = QLineEdit(self)
        self.end_input.setPlaceholderText("00:00:00")
        self.end_input.editingFinished.connect(self.update_selected_story)
        times_layout.addWidget(self.end_input)

        form_layout.addRow("Range:", times_layout)

        self.author_input = QLineEdit(self)
        self.author_input.setPlaceholderText("Story author / reporter / contributor")
        self.author_input.editingFinished.connect(self.update_selected_story)
        form_layout.addRow("Author:", self.author_input)

        details_layout.addLayout(form_layout)

        # Boundary Buttons Container (Visible only when exactly one story is selected)
        self.story_boundary_container = QWidget(self)
        self.story_boundary_container.setObjectName("story_boundary_container")
        boundary_layout = QHBoxLayout(self.story_boundary_container)
        boundary_layout.setContentsMargins(0, 0, 0, 0)
        boundary_layout.setSpacing(4)

        self.set_story_start_btn = QPushButton("Set Story Start", self.story_boundary_container)
        self.set_story_start_btn.setObjectName("set_story_start_btn")
        self.set_story_start_btn.setToolTip("Set start time of selected story to current transcript or timeline position")
        self.set_story_start_btn.clicked.connect(self.set_selected_story_start)
        boundary_layout.addWidget(self.set_story_start_btn)

        self.set_story_end_btn = QPushButton("Set Story End", self.story_boundary_container)
        self.set_story_end_btn.setObjectName("set_story_end_btn")
        self.set_story_end_btn.setToolTip("Set end time of selected story to current transcript or timeline position")
        self.set_story_end_btn.clicked.connect(self.set_selected_story_end)
        boundary_layout.addWidget(self.set_story_end_btn)

        self.story_boundary_container.hide()
        details_layout.addWidget(self.story_boundary_container)

        # Plugin Story Extensions Container (for plugin-provided story widgets)
        self.plugin_story_extensions_container = QWidget(self)
        self.plugin_story_extensions_container.setObjectName("plugin_story_extensions_container")
        self.plugin_story_extensions_layout = QVBoxLayout(self.plugin_story_extensions_container)
        self.plugin_story_extensions_layout.setContentsMargins(0, 0, 0, 0)
        self.plugin_story_extensions_layout.setSpacing(4)
        self.plugin_story_extensions_container.hide()
        details_layout.addWidget(self.plugin_story_extensions_container)

        self.story_details_scroll.setWidget(self.story_details_container)
        stories_box_layout.addWidget(self.story_details_scroll, 1)

        # Story action buttons
        story_btns_row = QHBoxLayout()
        story_btns_row.setSpacing(4)

        self.add_story_btn = QPushButton("Add Story", self)
        self.add_story_btn.setObjectName("add_story_btn")
        self.add_story_btn.setToolTip("Add story from active timeline selection or highlighted transcript text")
        self.add_story_btn.clicked.connect(self.add_story_from_active_selection)
        story_btns_row.addWidget(self.add_story_btn)

        self.select_all_stories_btn = QPushButton("Select All", self)
        self.select_all_stories_btn.setObjectName("select_all_stories_btn")
        self.select_all_stories_btn.setToolTip("Select all stories in the list")
        self.select_all_stories_btn.clicked.connect(self.select_all_stories)
        story_btns_row.addWidget(self.select_all_stories_btn)

        self.delete_story_btn = QPushButton("Delete", self)
        self.delete_story_btn.setObjectName("delete_story_btn")
        self.delete_story_btn.clicked.connect(self.delete_selected_story)
        story_btns_row.addWidget(self.delete_story_btn)

        story_action_row2 = QHBoxLayout()
        story_action_row2.setSpacing(4)

        self.story_metadata_btn = QPushButton("Story Metadata...", self)
        self.story_metadata_btn.setObjectName("story_metadata_btn")
        self.story_metadata_btn.setToolTip("Configure titles, authors, categories, excerpts, and featured images for all stories and full episode")
        self.story_metadata_btn.clicked.connect(lambda: self.open_story_metadata_dialog())
        story_action_row2.addWidget(self.story_metadata_btn, 1)

        self.export_stories_btn = QPushButton("Export...", self)
        self.export_stories_btn.setObjectName("export_stories_btn")
        self.export_stories_btn.setToolTip("Export full episode, selected stories, or external formats")
        self.export_stories_btn.clicked.connect(self.open_unified_export_dialog)
        story_action_row2.addWidget(self.export_stories_btn)
        
        stories_box_layout.addLayout(story_btns_row)
        stories_box_layout.addLayout(story_action_row2)
        self.right_splitter.addWidget(stories_box)

        # Activity / History Box
        self.activity_panel = QWidget(self)
        self.activity_panel.setObjectName("activity_panel")
        self.activity_panel.setMinimumHeight(90)
        activity_box = self.activity_panel
        activity_box_layout = QVBoxLayout(activity_box)
        activity_box_layout.setContentsMargins(8, 8, 8, 8)
        activity_box_layout.setSpacing(6)
        activity_header = QLabel("Activity History & Recovery", activity_box)
        activity_header.setObjectName("activity_section_header")
        activity_box_layout.addWidget(activity_header)
        activity_box_layout.setContentsMargins(6, 8, 6, 6)
        activity_box_layout.setSpacing(4)

        self.activity_list = QListWidget(self)
        self.activity_list.itemClicked.connect(self.handle_activity_click)
        activity_box_layout.addWidget(self.activity_list, 1)

        act_btns_row = QHBoxLayout()
        clear_act_btn = QPushButton("Clear Log", self)
        clear_act_btn.setObjectName("clear_activity_btn")
        clear_act_btn.clicked.connect(self.clear_activity_log)
        act_btns_row.addWidget(clear_act_btn)

        export_act_btn = QPushButton("Export Log...", self)
        export_act_btn.setObjectName("export_activity_btn")
        export_act_btn.clicked.connect(self.export_activity_log)
        act_btns_row.addWidget(export_act_btn)

        activity_box_layout.addLayout(act_btns_row)
        self.right_splitter.addWidget(activity_box)

        self.right_splitter.setStretchFactor(0, 3)
        self.right_splitter.setStretchFactor(1, 2)

        splitter.addWidget(self.right_splitter)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, 1)

        # Connect Timeline signals
        self.timeline.canvas.positionClicked.connect(self.seek_to)
        self.timeline.canvas.scrubPositionChanged.connect(self.handle_scrub_position)
        self.timeline.canvas.storyRegionUpdated.connect(self.handle_drag_story_region)
        self.timeline.canvas.newRegionStarted.connect(self.handle_new_story_started)
        self.timeline.canvas.newRegionUpdated.connect(self.handle_new_story_updated)
        self.timeline.canvas.multiSelectionChanged.connect(self.handle_timeline_multi_selection)
        self.timeline.canvas.storyClicked.connect(self.on_timeline_story_clicked)
        self.timeline.canvas.dragOperationFinished.connect(self.handle_drag_finished)
        self.timeline.mediaDropped.connect(self.load_media_file)
        
        self.timeline.selectionRangeChanged.connect(self.handle_timeline_selection_range_changed)
        self.timeline.storyCreatedFromSelection.connect(self.add_story_from_range)

        # Connect Transcript View signals
        self.transcript_view.linkClicked.connect(self.transcript_clicked)
        self.transcript_view.requestSplitAtCursor.connect(self.split_segment_at_time)
        self.transcript_view.requestInsertSpeaker.connect(self.handle_insert_speaker_request)
        self.transcript_view.requestRemoveSpeakerAtBlock.connect(self.remove_speaker_label_at_segment)
        self.transcript_view.textChanged.connect(self.on_transcript_text_changed)
        self.transcript_view.cursorPositionChanged.connect(self.on_transcript_selection_changed)
        self.transcript_view.cursorPositionChanged.connect(self._sync_format_toolbar_buttons)
        if hasattr(self.transcript_view, "formatChanged"):
            self.transcript_view.formatChanged.connect(self._sync_format_toolbar_buttons)
        self.transcript_view.editingModeChanged.connect(self._on_transcript_editing_mode_changed)

        # Transcript zoom shortcuts. Use platform_seq so Ctrl becomes Command on macOS.
        self.shortcut_transcript_font_up = QShortcut(platform_seq("Ctrl++"), self)
        self.shortcut_transcript_font_up.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_transcript_font_up.activated.connect(lambda: self.adjust_transcript_font_size(1))
        self.shortcut_transcript_font_down = QShortcut(platform_seq("Ctrl+-"), self)
        self.shortcut_transcript_font_down.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_transcript_font_down.activated.connect(lambda: self.adjust_transcript_font_size(-1))
        self.shortcut_transcript_font_reset = QShortcut(platform_seq("Ctrl+0"), self)
        self.shortcut_transcript_font_reset.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_transcript_font_reset.activated.connect(self.reset_transcript_font_size)

        # Formatting actions
        self.fmt_bold_action = QAction("Bold Text", self)
        self.fmt_bold_action.setShortcut(platform_seq("Ctrl+B"))
        self.fmt_bold_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_bold_action.triggered.connect(lambda: getattr(self.transcript_view, "toggle_bold", lambda: None)())
        self.addAction(self.fmt_bold_action)

        self.fmt_italic_action = QAction("Italic Text", self)
        self.fmt_italic_action.setShortcut(platform_seq("Ctrl+I"))
        self.fmt_italic_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_italic_action.triggered.connect(lambda: getattr(self.transcript_view, "toggle_italic", lambda: None)())
        self.addAction(self.fmt_italic_action)

        self.fmt_underline_action = QAction("Underline Text", self)
        self.fmt_underline_action.setShortcut(platform_seq("Ctrl+U"))
        self.fmt_underline_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_underline_action.triggered.connect(lambda: getattr(self.transcript_view, "toggle_underline", lambda: None)())
        self.addAction(self.fmt_underline_action)

        self.fmt_strike_action = QAction("Strikethrough Text", self)
        self.fmt_strike_action.setShortcut(platform_seq("Ctrl+K"))
        self.fmt_strike_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_strike_action.triggered.connect(lambda: getattr(self.transcript_view, "toggle_strikethrough", lambda: None)())
        self.addAction(self.fmt_strike_action)

        self.fmt_highlight_action = QAction("Highlight Text", self)
        self.fmt_highlight_action.setShortcut(platform_seq("Ctrl+Shift+H"))
        self.fmt_highlight_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_highlight_action.triggered.connect(
            lambda: getattr(self.transcript_view, "toggle_highlight", lambda c: None)(getattr(self, "current_highlight_color", "#fef08a"))
        )
        self.addAction(self.fmt_highlight_action)

        self.fmt_clear_action = QAction("Clear Text Formatting", self)
        self.fmt_clear_action.setShortcut(platform_seq("Ctrl+\\"))
        self.fmt_clear_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_clear_action.triggered.connect(lambda: getattr(self.transcript_view, "clear_formatting", lambda: None)())
        self.addAction(self.fmt_clear_action)

        self.fmt_split_action = QAction("Split Speaker Segment", self)
        self.fmt_split_action.setShortcut(platform_seq("Shift+Return"))
        self.fmt_split_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fmt_split_action.triggered.connect(self._on_toolbar_split_speaker)
        self.addAction(self.fmt_split_action)

        # Connect Story List signals
        self.story_list.itemSelectionChanged.connect(self.story_selection_changed)
        self.story_list.deleteRequested.connect(self.delete_selected_story)
        self.story_list.exportRequested.connect(self.export_selected_stories)
        self.story_list.exportStoryWordPressRequested.connect(lambda: self.open_unified_export_dialog(initial_dest="wordpress"))
        self.story_list.filesDropped.connect(lambda paths: getattr(self, "open_media_file", lambda p: None)(paths[0]) if paths else None)

        # Initialize status bar
        self.statusBar().showMessage("Ready")

        # Update terminology (Story vs. Segment) based on initial detection mode
        if hasattr(self, "update_story_segment_terminology"):
            self.update_story_segment_terminology()

    def filter_transcript_search(self, target: str):
        """Highlight and focus next occurrence of search term in transcript text view."""
        if not target or not hasattr(self, "transcript_view"):
            return

        cursor = self.transcript_view.textCursor()
        document = self.transcript_view.document()
        found = document.find(target, cursor)
        if found.isNull():
            # Wrap around to document beginning
            cursor.setPosition(0)
            found = document.find(target, cursor)

        if not found.isNull():
            self.transcript_view.setTextCursor(found)
            self.transcript_view.ensureCursorVisible()
        else:
            self.statusBar().showMessage(f"No occurrences of '{target}' found.", 3000)

    def toggle_transcript_editing_mode(self, *args, **kwargs):
        """Toggle between Viewing Mode (navigation/click-to-seek) and Editing Mode (text editing)."""
        if not hasattr(self, "transcript_view"):
            return
        display_mode = getattr(self, "translation_display_mode", "en")
        if display_mode in ("split", "bilingual"):
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage("Editing is only available in single-language views (English or Español).", 4000)
            if hasattr(self, "transcript_edit_mode_action"):
                self.transcript_edit_mode_action.blockSignals(True)
                self.transcript_edit_mode_action.setChecked(False)
                self.transcript_edit_mode_action.blockSignals(False)
            if hasattr(self, "transcript_mode_toggle_btn"):
                self.transcript_mode_toggle_btn.blockSignals(True)
                self.transcript_mode_toggle_btn.setChecked(False)
                self.transcript_mode_toggle_btn.blockSignals(False)
            return

        if args and isinstance(args[0], bool):
            new_mode = args[0]
        else:
            new_mode = not getattr(self.transcript_view, "is_editing_mode", False)
        self.transcript_view.set_editing_mode(new_mode)

    def _on_transcript_editing_mode_changed(self, is_editing: bool):
        """Respond to changes in transcript edit vs view mode."""
        display_mode = getattr(self, "translation_display_mode", "en")
        if hasattr(self, "transcript_mode_toggle_btn"):
            if display_mode in ("split", "bilingual"):
                self.transcript_mode_toggle_btn.setChecked(False)
                self.transcript_mode_toggle_btn.setEnabled(False)
                self.transcript_mode_toggle_btn.setText("Edit Transcript")
                self.transcript_mode_toggle_btn.setToolTip("Editing is only available in single-language views (English or Español).")
                self.transcript_mode_toggle_btn.setStyleSheet("")
            else:
                self.transcript_mode_toggle_btn.setEnabled(True)
                self.transcript_mode_toggle_btn.setChecked(is_editing)
                if is_editing:
                    self.transcript_mode_toggle_btn.setText("View Transcript")
                    self.transcript_mode_toggle_btn.setToolTip("Click to exit editing mode and return to interactive viewing.")
                    self.transcript_mode_toggle_btn.setStyleSheet("font-weight: bold; background-color: #2b5278; color: white;")
                else:
                    self.transcript_mode_toggle_btn.setText("Edit Transcript")
                    if display_mode == "es":
                        self.transcript_mode_toggle_btn.setToolTip("Toggle between Viewing Mode and Editing Mode for Spanish translation (F2)")
                    else:
                        self.transcript_mode_toggle_btn.setToolTip("Toggle between Viewing Mode (click to play/seek audio) and Editing Mode (type/edit transcript text) (F2)")
                    self.transcript_mode_toggle_btn.setStyleSheet("")
        if hasattr(self, "transcript_format_toolbar"):
            self.transcript_format_toolbar.setVisible(is_editing)
        if hasattr(self, "transcript_edit_mode_action"):
            self.transcript_edit_mode_action.blockSignals(True)
            self.transcript_edit_mode_action.setChecked(is_editing)
            self.transcript_edit_mode_action.setEnabled(display_mode not in ("split", "bilingual"))
            self.transcript_edit_mode_action.blockSignals(False)
        if is_editing:
            self._sync_format_toolbar_buttons()
        if not is_editing and hasattr(self, "render_transcript"):
            # Re-render so word-level clickable anchors and highlights are freshly constructed
            self.render_transcript()

    def _sync_format_toolbar_buttons(self):
        if not hasattr(self, "transcript_view") or not getattr(self.transcript_view, "is_editing_mode", False):
            return
        if hasattr(self.transcript_view, "get_current_formatting"):
            fmt = self.transcript_view.get_current_formatting()
            if hasattr(self, "fmt_bold_btn"):
                self.fmt_bold_btn.blockSignals(True)
                self.fmt_bold_btn.setChecked(fmt.get("bold", False))
                self.fmt_bold_btn.blockSignals(False)
            if hasattr(self, "fmt_italic_btn"):
                self.fmt_italic_btn.blockSignals(True)
                self.fmt_italic_btn.setChecked(fmt.get("italic", False))
                self.fmt_italic_btn.blockSignals(False)
            if hasattr(self, "fmt_underline_btn"):
                self.fmt_underline_btn.blockSignals(True)
                self.fmt_underline_btn.setChecked(fmt.get("underline", False))
                self.fmt_underline_btn.blockSignals(False)
            if hasattr(self, "fmt_strike_btn"):
                self.fmt_strike_btn.blockSignals(True)
                self.fmt_strike_btn.setChecked(fmt.get("strike", False))
                self.fmt_strike_btn.blockSignals(False)

    def _on_toolbar_split_speaker(self):
        if hasattr(self, "transcript_view"):
            cursor = self.transcript_view.textCursor()
            seg_idx = self.transcript_view.get_segment_index_at_cursor(cursor)
            if seg_idx is None:
                seg_idx = cursor.blockNumber()
            split_time = self.transcript_view.get_timestamp_at_cursor(cursor)
            self.transcript_view.requestSplitAtCursor.emit(seg_idx, split_time)

    def _apply_transcript_font_scale(self, scale, persist=True):
        """Apply a transcript-only font scale and optionally persist it."""
        scale = max(0.80, min(1.80, float(scale)))
        # Snap to 5% increments for predictable keyboard/button behavior.
        scale = round(scale / 0.05) * 0.05
        self.transcript_font_scale = scale
        if hasattr(self, "transcript_view"):
            self.transcript_view.set_font_scale(scale)
        if hasattr(self, "transcript_font_size_combo") and self.transcript_font_size_combo is not None:
            self.transcript_font_size_combo.blockSignals(True)
            best_idx = 0
            min_diff = 999.0
            for i in range(self.transcript_font_size_combo.count()):
                val = float(self.transcript_font_size_combo.itemData(i))
                diff = abs(val - scale)
                if diff < min_diff:
                    min_diff = diff
                    best_idx = i
            self.transcript_font_size_combo.setCurrentIndex(best_idx)
            self.transcript_font_size_combo.blockSignals(False)
        if persist and hasattr(self, "settings_store"):
            self.settings_store.setValue("transcript_font_scale", scale)
            self.settings_store.sync()
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Transcript font size: {round(scale * 100)}%", 1500)

    def _on_font_size_combo_changed(self, index: int):
        if hasattr(self, "transcript_font_size_combo") and self.transcript_font_size_combo is not None:
            scale_val = self.transcript_font_size_combo.itemData(index)
            if scale_val is not None:
                self._apply_transcript_font_scale(float(scale_val))

    def adjust_transcript_font_size(self, direction):
        """Increase or decrease transcript font size by one 5% step."""
        self._apply_transcript_font_scale(self.transcript_font_scale + (0.05 * (1 if direction > 0 else -1)))

    def reset_transcript_font_size(self):
        """Restore the default transcript font size."""
        self._apply_transcript_font_scale(1.0)

    def update_story_list_height(self):
        """Size the story list to fit the current number of stories, leaving space for metadata and export fields."""
        if not hasattr(self, "story_list") or self.story_list is None:
            return
        cnt = self.story_list.count()
        row_h = self.story_list.sizeHintForRow(0) if cnt > 0 and self.story_list.sizeHintForRow(0) > 0 else 28
        content_h = max(65, cnt * row_h + self.story_list.frameWidth() * 2 + 8)
        if getattr(self, "_stories_panel_maximized", False):
            # When maximized across the full window, only size the list as large as needed
            # to show the stories (capping at 220px if there are dozens), reserving the rest for metadata
            target_h = min(220, content_h)
            self.story_list.setFixedHeight(target_h)
        else:
            target_h = min(180, content_h)
            self.story_list.setMaximumHeight(target_h)
            self.story_list.setMinimumHeight(65)

    def auto_generate_selected_story_excerpt(self):
        """Auto-generate an excerpt from the story transcript text for the currently selected story."""
        if not getattr(self, "current_selected_story_indices", None) or len(self.current_selected_story_indices) != 1:
            return
        idx = self.current_selected_story_indices[0]
        if not (0 <= idx < len(self.stories)):
            return
        st = self.stories[idx]
        raw_text = ""
        if hasattr(self, "_get_transcript_text_slice"):
            raw_text = self._get_transcript_text_slice(st.start, st.end)
        if not raw_text and hasattr(self, "transcript"):
            words = []
            for seg in getattr(self, "transcript", []) or []:
                s_start = seg.get("start", 0.0)
                s_end = seg.get("end", 0.0)
                if (st.start is None or s_end >= st.start) and (st.end is None or s_start <= st.end):
                    words.append(seg.get("text", ""))
            raw_text = " ".join(words)
        words = raw_text.split()
        if len(words) <= 55:
            excerpt = raw_text.strip()
        else:
            excerpt = " ".join(words[:55]).rstrip(".,;:!?") + "..."
        if hasattr(self, "excerpt_edit"):
            self.excerpt_edit.blockSignals(True)
            self.excerpt_edit.setPlainText(excerpt)
            self.excerpt_edit.blockSignals(False)
        self._on_story_excerpt_text_changed()

    def _on_story_excerpt_text_changed(self):
        """Synchronize excerpt edits from the inline editor into story metadata."""
        if getattr(self, "is_updating_selection", False):
            return
        if not getattr(self, "current_selected_story_indices", None) or len(self.current_selected_story_indices) != 1:
            return
        idx = self.current_selected_story_indices[0]
        if 0 <= idx < len(self.stories):
            st = self.stories[idx]
            txt = self.excerpt_edit.toPlainText().strip()
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            st.metadata["excerpt"] = txt
            wp_meta = st.metadata.setdefault("wordpress", {})
            wp_meta["excerpt"] = txt
            self.project_dirty = True
            if hasattr(self, "update_window_title"):
                self.update_window_title()

    def toggle_maximize_stories_panel(self):
        """Toggle maximize/restore of the stories panel across the full application window."""
        if not hasattr(self, "right_splitter") or not hasattr(self, "activity_panel"):
            return
        is_max = getattr(self, "_stories_panel_maximized", False)
        if not is_max:
            # Save prior visibility and splitter proportions
            self._saved_timeline_visible = self.timeline.isVisible() if hasattr(self, "timeline") else True
            self._saved_transcript_visible = self.transcript_panel.isVisible() if hasattr(self, "transcript_panel") else True
            self._saved_activity_visible = self.activity_panel.isVisible() if hasattr(self, "activity_panel") else True
            if hasattr(self, "center_splitter"):
                self._saved_center_splitter_sizes = self.center_splitter.sizes()
            self._saved_right_splitter_sizes = self.right_splitter.sizes()

            # Minimize timeline and transcript widgets, and hide activity log
            if hasattr(self, "timeline"):
                self.timeline.hide()
            if hasattr(self, "transcript_panel"):
                self.transcript_panel.hide()
            self.activity_panel.hide()

            # Expand splitters to give Stories panel 100% full application window space
            if hasattr(self, "center_splitter"):
                self.center_splitter.setSizes([0, 1000])
            self.right_splitter.setSizes([1000, 0])
            self._stories_panel_maximized = True

            if hasattr(self, "maximize_stories_btn"):
                self.maximize_stories_btn.setText("❐")
                self.maximize_stories_btn.setToolTip("Restore normal application window layout")
            self.update_story_list_height()
        else:
            # Restore timeline, transcript, and activity widgets
            if hasattr(self, "timeline") and getattr(self, "_saved_timeline_visible", True):
                self.timeline.show()
            if hasattr(self, "transcript_panel") and getattr(self, "_saved_transcript_visible", True):
                self.transcript_panel.show()
            if getattr(self, "_saved_activity_visible", True):
                self.activity_panel.show()

            if hasattr(self, "center_splitter"):
                c_sizes = getattr(self, "_saved_center_splitter_sizes", [600, 300])
                if sum(c_sizes) > 0:
                    self.center_splitter.setSizes(c_sizes)
            sizes = getattr(self, "_saved_right_splitter_sizes", [600, 250])
            if sum(sizes) <= 0:
                sizes = [600, 250]
            self.right_splitter.setSizes(sizes)
            self._stories_panel_maximized = False

            if hasattr(self, "maximize_stories_btn"):
                self.maximize_stories_btn.setText("⛶")
                self.maximize_stories_btn.setToolTip("Maximize Stories panel across full application window")
            self.update_story_list_height()

    def setup_plugin_story_extensions(self):
        """Populate plugin-provided widgets in the story panel."""
        if not hasattr(self, "plugin_story_extensions_layout") or not self.plugin_story_extensions_layout:
            return
        # Clear existing child widgets
        while self.plugin_story_extensions_layout.count():
            child = self.plugin_story_extensions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        count = 0
        if hasattr(self, "plugin_manager") and self.plugin_manager:
            for plugin in self.plugin_manager.plugins.values():
                if getattr(plugin, "is_enabled", False) and hasattr(plugin, "create_story_metadata_widget"):
                    try:
                        w = plugin.create_story_metadata_widget(parent=self.plugin_story_extensions_container)
                        if w:
                            self.plugin_story_extensions_layout.addWidget(w)
                            count += 1
                    except Exception as exc:
                        print(f"[PLUGINS] Error creating story metadata widget: {exc}")
        if hasattr(self, "plugin_story_extensions_container") and self.plugin_story_extensions_container:
            self.plugin_story_extensions_container.setVisible(count > 0)

    def notify_story_selection_to_plugins(self, selected_story=None):
        """Notify all enabled plugins when the active story selection changes."""
        if hasattr(self, "plugin_manager") and self.plugin_manager:
            for plugin in self.plugin_manager.plugins.values():
                if getattr(plugin, "is_enabled", False) and hasattr(plugin, "on_story_selected"):
                    try:
                        plugin.on_story_selected(selected_story)
                    except Exception as exc:
                        pass





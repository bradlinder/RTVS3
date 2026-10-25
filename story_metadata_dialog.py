"""Radio & TV Story Segmenter — Universal Story & Post Metadata Architecture.

Provides a unified, non-modal floating dialog (StoryMetadataDialog) cloning the
WordPress draft export view for configuring story and post metadata (titles,
authors, categories/tags, excerpts, video frame thumbnails, audio attachments,
fades, and Castos podcast feeds).

Features:
- Exact parity with the WordPress draft export view (4-tab interface).
- "Save" and "Close" bottom-right action buttons.
- "Sync Transcript" header button for live co-editing without modal lockout.
- "Pin on Top" toggle to float comfortably beside the main transcript window.
- Instant two-way synchronization directly to Story.title, Story.metadata,
  and project_metadata, auto-saving to the .rtvs project.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QEvent, QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    get_active_theme_mode,
)
from core_utils import (
    apply_window_titlebar_theme,
    make_dialog_maximizable,
)
from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget


def _get_metadata_theme_mode() -> str:
    """Retrieve active theme mode ('light', 'dark', or 'high_contrast')."""
    return get_active_theme_mode("dark")


def generate_story_excerpt(text: str, max_words: int = 55) -> str:
    """Generate a clean, readable excerpt of up to max_words from transcript text."""
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return " ".join(words)
    trimmed = " ".join(words[:max_words])
    # Avoid trailing punctuation before ellipsis
    while trimmed and trimmed[-1] in ",;:-\"'":
        trimmed = trimmed[:-1]
    return trimmed + "…"


class StoryMetadataDialog(QDialog):
    """Universal non-modal dialog for inspecting and editing post and story metadata across the project."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        main_window: Any = None,
        target_story_index: Optional[int] = None,
    ):
        super().__init__(None)
        self.main_window = main_window or parent
        self.target_story_index = target_story_index
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._is_floating = True
        self._stay_on_top = False
        self._syncing_from_main = False

        self.setWindowTitle("Story Settings & Metadata")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(980, 740)
        self.setMinimumSize(800, 580)
        make_dialog_maximizable(self)
        apply_window_titlebar_theme(self)
        self.setObjectName("story_metadata_dialog")

        self._init_ui()

        # Focus initial story if provided
        if self.target_story_index is not None and hasattr(self.tab_widget, "wp_posts_list"):
            # index 0 is Full Episode, index 1..N are stories
            item_row = self.target_story_index + 1
            if 0 <= item_row < self.tab_widget.wp_posts_list.count():
                self.tab_widget.wp_posts_list.setCurrentRow(item_row)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        theme_mode = _get_metadata_theme_mode()
        if theme_mode == "light":
            b_bg, b_fg, b_bd, h_bg, h_fg = "#e3e6ea", "#2e74b5", "#2e74b5", "#2e74b5", "#ffffff"
        elif theme_mode == "high_contrast":
            b_bg, b_fg, b_bd, h_bg, h_fg = "#000000", "#ffff00", "#ffff00", "#ffff00", "#000000"
        else:
            b_bg, b_fg, b_bd, h_bg, h_fg = "#1e293b", "#38bdf8", "#0284c7", "#0284c7", "#ffffff"

        hdr_btn_qss = (
            f"QPushButton {{ background-color: {b_bg}; color: {b_fg}; border: 1px solid {b_bd}; border-radius: 4px; padding: 4px 12px; font-size: 11px; font-weight: 500; }}\n"
            f"QPushButton:hover {{ background-color: {h_bg}; color: {h_fg}; }}\n"
            f"QPushButton:checked {{ background-color: {h_bg}; color: {h_fg}; font-weight: bold; }}"
        )

        # Header bar with live co-editing controls
        header_widget = QWidget(self)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        info_label = QLabel(
            "<b>Story Settings & Metadata</b> — Configure titles, authors, categories, "
            "excerpts, featured images, and podcast metadata for full episodes and individual stories.",
            self
        )
        info_label.setWordWrap(True)
        header_layout.addWidget(info_label, 1)

        self.refresh_btn = QPushButton("Sync Transcript", self)
        self.refresh_btn.setToolTip("Synchronize transcript text, timing boundaries, and word counts from the main window without closing")
        self.refresh_btn.setStyleSheet(hdr_btn_qss)
        self.refresh_btn.clicked.connect(lambda: self.refresh_from_main_window())
        header_layout.addWidget(self.refresh_btn)

        self.float_btn = QPushButton("Pin on Top", self)
        self.float_btn.setCheckable(True)
        self.float_btn.setToolTip(
            "This window is non-modal so you can freely edit the transcript in the main window. "
            "Toggle 'Pin on Top' to keep this window above the main window while co-editing."
        )
        self.float_btn.setStyleSheet(hdr_btn_qss)
        self.float_btn.toggled.connect(self.toggle_float_mode)
        header_layout.addWidget(self.float_btn)

        main_layout.addWidget(header_widget)

        # Clone of the WordPress Draft Export view (4-tab layout, media scrubber, taxonomy, Castos, notices)
        self.tab_widget = WordPressExportTabWidget(self, self.main_window, metadata_editor_mode=False)
        main_layout.addWidget(self.tab_widget, 1)

        # Bottom Button Bar: Save and Close in bottom right
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        btn_box.addStretch()

        self.save_btn = QPushButton("Save", self)
        self.save_btn.setObjectName("story_settings_save_btn")
        self.save_btn.setToolTip("Save all story and post settings to project")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 18px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.save_btn.clicked.connect(self._on_save_clicked)
        btn_box.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setObjectName("story_settings_close_btn")
        self.close_btn.setToolTip("Close the story settings window")
        self.close_btn.setStyleSheet("QPushButton { padding: 6px 14px; border-radius: 4px; }")
        self.close_btn.clicked.connect(self._on_close_clicked)
        btn_box.addWidget(self.close_btn)

        # Backward compatibility aliases
        self.save_close_btn = self.close_btn
        self.apply_btn = self.save_btn
        self.cancel_btn = self.close_btn

        main_layout.addLayout(btn_box)

    @property
    def targets_list(self) -> Any:
        """Alias returning the post selector list widget for caller backward compatibility."""
        return getattr(self.tab_widget, "wp_posts_list", None)

    @property
    def target_items(self) -> List[Dict[str, Any]]:
        """Alias returning the post items list for caller backward compatibility."""
        return getattr(self.tab_widget, "wp_post_items", [])

    def save_all_to_project(self):
        """Commit all configured metadata into Project/Story data structures and sync UI."""
        if hasattr(self.tab_widget, "save_all_posts_to_project"):
            self.tab_widget.save_all_posts_to_project()

        # Update main window story list and current fields
        if hasattr(self.main_window, "refresh_story_list"):
            self.main_window.refresh_story_list()

        if hasattr(self.main_window, "mark_project_dirty"):
            self.main_window.mark_project_dirty("Update Story Metadata")
        elif hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)

        if hasattr(self.main_window, "save_project"):
            try:
                self.main_window.save_project()
            except Exception as e:
                print(f"[STORY SETTINGS] Error auto-saving project: {e}")

    def rebuild_target_items(self):
        """Rebuild post items in tab widget."""
        if hasattr(self.tab_widget, "rebuild_post_items"):
            self.tab_widget.rebuild_post_items()

    def _on_save_clicked(self):
        self.save_all_to_project()
        orig_text = self.save_btn.text()
        self.save_btn.setText("Saved ✓")
        QTimer.singleShot(1500, lambda: self.save_btn.setText(orig_text) if not self.isHidden() else None)

    def _on_close_clicked(self):
        self.save_all_to_project()
        self.accept()

    def _on_save_and_close(self):
        self._on_close_clicked()

    def toggle_float_mode(self, pinned: Optional[bool] = None):
        """Toggle whether the non-modal floating window stays pinned on top of other windows."""
        if pinned is None:
            pinned = not getattr(self, "_stay_on_top", False)
        self._stay_on_top = bool(pinned)
        if hasattr(self, "float_btn"):
            self.float_btn.blockSignals(True)
            self.float_btn.setChecked(self._stay_on_top)
            self.float_btn.setText("Pinned on Top" if self._stay_on_top else "Pin on Top")
            self.float_btn.blockSignals(False)
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._stay_on_top)
        if was_visible:
            self.show()
            apply_window_titlebar_theme(self)
            self.raise_()
            self.activateWindow()

    def refresh_from_main_window(self, target_story_index: Optional[int] = None):
        """Synchronize stories, excerpts, and transcript changes from the main window."""
        if getattr(self, "_syncing_from_main", False):
            return
        self._syncing_from_main = True
        try:
            if hasattr(self.main_window, "flush_pending_transcript_undo"):
                try:
                    self.main_window.flush_pending_transcript_undo()
                except Exception:
                    pass
            self.save_all_to_project()
            cur_row = (target_story_index + 1) if target_story_index is not None else (
                self.tab_widget.wp_posts_list.currentRow() if hasattr(self.tab_widget, "wp_posts_list") else 0
            )
            if hasattr(self.tab_widget, "rebuild_post_items"):
                self.tab_widget.rebuild_post_items()
            if hasattr(self.tab_widget, "wp_posts_list") and 0 <= cur_row < self.tab_widget.wp_posts_list.count():
                self.tab_widget.wp_posts_list.setCurrentRow(cur_row)
        finally:
            self._syncing_from_main = False

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowActivate:
            self.refresh_from_main_window()

    def done(self, r: int):
        try:
            self.save_all_to_project()
        except Exception:
            pass
        super().done(r)

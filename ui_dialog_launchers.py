"""Dialog launchers and external modal helpers for Radio & TV Story Segmenter."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from transcript_editor import FindReplaceDialog

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class UiDialogLaunchersMixin:
    """Mixin providing dialog launcher methods for shortcuts, benchmarks, diagnostics, and plugins."""
    def open_project_dialog(self):
        """Prompt user to open a project file (*.rtvs)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            self._dialog_directory(),
            "RadioTV Story Segmenter Projects (*.rtvs *.zip *.json);;Project Archives (*.zip);;Legacy Projects (*.json);;All Files (*.*)",
        )
        if file_path:
            try:
                directory = str(Path(file_path).resolve().parent)
                self.settings_store.setValue("last_open_directory", directory)
                self.settings_store.sync()
            except Exception:
                pass
            self.load_project_file(file_path, prompt=True, preserve_media=False)

    def open_find_dialog(self):
        """Display the Find and Replace dialog window."""
        if not getattr(self, "find_dialog", None):
            self.find_dialog = FindReplaceDialog(self.transcript_view, self)
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()


    def show_shortcuts_dialog(self):
        """Display a searchable or structured reference table of all active shortcuts."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.resize(620, 540)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet("""
            QTextBrowser {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                font-size: 13px;
                padding: 10px;
            }
        """)

        is_mac = sys.platform == "darwin"
        cmd = "Cmd" if is_mac else "Ctrl"
        opt = "Option" if is_mac else "Alt"
        panel_mod = "Ctrl+Option" if is_mac else "Alt"

        def get_sc(action_id: str, fallback: str = "") -> str:
            if hasattr(self, "shortcuts_manager") and self.shortcuts_manager:
                sc = self.shortcuts_manager.get_current_shortcut(action_id)
                if sc and sc != "None":
                    from shortcuts_manager import format_sequence_display
                    return format_sequence_display(sc)
                if sc == "None":
                    return "Unassigned"
            return fallback

        clear_fmt_sc = get_sc("fmt_clear", f"{cmd}+\\")

        html_content = f"""
        <style>
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
            th {{ text-align: left; padding: 6px 8px; border-bottom: 2px solid #555; }}
            td {{ padding: 5px 8px; border-bottom: 1px solid #333; }}
            kbd {{
                background-color: #2b303c;
                border: 1px solid #4f5666;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: monospace;
                font-size: 12px;
                color: #e6edf3;
            }}
            h3 {{ margin-top: 14px; margin-bottom: 6px; color: #58a6ff; }}
        </style>

        <h3>Playback & Navigation</h3>
        <table>
            <tr><td><b>Play / Pause</b></td><td><kbd>{get_sc("play_pause", "Space")}</kbd> or <kbd>Media Play/Pause</kbd></td></tr>
            <tr><td><b>Skip Backward / Forward</b></td><td><kbd>{get_sc("seek_backward", "Left")}</kbd> / <kbd>{get_sc("seek_forward", "Right")}</kbd></td></tr>
            <tr><td><b>Seek to Start / End</b></td><td><kbd>{get_sc("seek_start", "Home")}</kbd> / <kbd>{get_sc("seek_end", "End")}</kbd></td></tr>
            <tr><td><b>Zoom In / Out on Timeline</b></td><td><kbd>{get_sc("zoom_in", "+")}</kbd> / <kbd>{get_sc("zoom_out", "-")}</kbd> or <kbd>Mouse Wheel</kbd></td></tr>
            <tr><td><b>Pan Timeline View</b></td><td><kbd>Shift + Wheel</kbd> or <kbd>Middle-Click Drag</kbd></td></tr>
            <tr><td><b>Increase / Decrease Transcript Text</b></td><td><kbd>{get_sc("transcript_font_up", f"{cmd}++")}</kbd> / <kbd>{get_sc("transcript_font_down", f"{cmd}+-")}</kbd></td></tr>
            <tr><td><b>Reset Transcript Text Size</b></td><td><kbd>{get_sc("transcript_font_reset", f"{cmd}+0")}</kbd></td></tr>
        </table>

        <h3>File & Project</h3>
        <table>
            <tr><td><b>New Project</b></td><td><kbd>{get_sc("new_project", f"{cmd}+N")}</kbd></td></tr>
            <tr><td><b>Open Media File</b></td><td><kbd>{get_sc("open_media", f"{cmd}+O")}</kbd></td></tr>
            <tr><td><b>Open Document</b></td><td><kbd>{get_sc("open_document", f"{cmd}+{opt}+O")}</kbd></td></tr>
            <tr><td><b>Open Project Session</b></td><td><kbd>{get_sc("open_project", f"{cmd}+Shift+O")}</kbd></td></tr>
            <tr><td><b>Close Project Session</b></td><td><kbd>{get_sc("close_project", f"{cmd}+W")}</kbd></td></tr>
            <tr><td><b>Save Project</b></td><td><kbd>{get_sc("save_project", f"{cmd}+S")}</kbd></td></tr>
            <tr><td><b>Save Project As...</b></td><td><kbd>{get_sc("save_project_as", f"{cmd}+Shift+S")}</kbd></td></tr>
            <tr><td><b>Export Dialog</b></td><td><kbd>{get_sc("export", f"{cmd}+E")}</kbd></td></tr>
            <tr><td><b>Batch Processing</b></td><td><kbd>{get_sc("batch_processing", f"{cmd}+Shift+B")}</kbd></td></tr>
            <tr><td><b>Preferences</b></td><td><kbd>{get_sc("preferences", f"{cmd}+P")}</kbd></td></tr>
            <tr><td><b>Customize Keyboard Shortcuts</b></td><td><kbd>{get_sc("customize_shortcuts", f"{cmd}+K")}</kbd></td></tr>
            <tr><td><b>Exit Application</b></td><td><kbd>{get_sc("exit_app", f"{cmd}+Q")}</kbd></td></tr>
        </table>

        <h3>Panels & Views</h3>
        <table>
            <tr><td><b>Toggle Timeline Panel</b></td><td><kbd>{get_sc("toggle_timeline", f"{panel_mod}+1")}</kbd></td></tr>
            <tr><td><b>Toggle Transcript Panel</b></td><td><kbd>{get_sc("toggle_transcript", f"{panel_mod}+2")}</kbd></td></tr>
            <tr><td><b>Toggle Stories Panel</b></td><td><kbd>{get_sc("toggle_stories", f"{panel_mod}+3")}</kbd></td></tr>
            <tr><td><b>Toggle Activity History Panel</b></td><td><kbd>{get_sc("toggle_activity", f"{panel_mod}+4")}</kbd></td></tr>
            <tr><td><b>Toggle Comments Sidebar & Annotations</b></td><td><kbd>{get_sc("toggle_comments", f"{cmd}+{opt}+C")}</kbd></td></tr>
            <tr><td><b>Toggle Waveform Display</b></td><td><kbd>{get_sc("toggle_waveform", f"{cmd}+{opt}+W")}</kbd></td></tr>
            <tr><td><b>Toggle Video Thumbnails</b></td><td><kbd>{get_sc("toggle_thumbnails", f"{cmd}+{opt}+T")}</kbd></td></tr>
            <tr><td><b>Toggle Video Preview Window</b></td><td><kbd>{get_sc("toggle_video_preview", f"{cmd}+Shift+M")}</kbd></td></tr>
            <tr><td><b>Toggle Speaker Labels</b></td><td><kbd>{get_sc("toggle_speaker_labels", f"{cmd}+{opt}+S")}</kbd></td></tr>
            <tr><td><b>Toggle Timestamps</b></td><td><kbd>{get_sc("toggle_timestamps", f"{cmd}+{opt}+I")}</kbd></td></tr>
        </table>

        <h3>Editing & Transcript</h3>
        <table>
            <tr><td><b>Toggle Transcript Edit Mode</b></td><td><kbd>{get_sc("toggle_edit_mode", "F2")}</kbd></td></tr>
            <tr><td><b>Undo / Redo</b></td><td><kbd>{get_sc("undo", f"{cmd}+Z")}</kbd> / <kbd>{get_sc("redo", f"{cmd}+Y")}</kbd></td></tr>
            <tr><td><b>Bold / Italic / Underline / Strike</b></td><td><kbd>{get_sc("fmt_bold", f"{cmd}+B")}</kbd> / <kbd>{get_sc("fmt_italic", f"{cmd}+I")}</kbd> / <kbd>{get_sc("fmt_underline", f"{cmd}+U")}</kbd> / <kbd>{get_sc("fmt_strikethrough", f"{cmd}+K")}</kbd></td></tr>
            <tr><td><b>Highlight Text (Yellow)</b></td><td><kbd>{get_sc("fmt_highlight", f"{cmd}+Shift+H")}</kbd></td></tr>
            <tr><td><b>Clear Text Formatting</b></td><td><kbd>{clear_fmt_sc}</kbd></td></tr>
            <tr><td><b>Add / Edit Comment</b></td><td><kbd>{get_sc("add_comment", f"{cmd}+M")}</kbd></td></tr>
            <tr><td><b>Split Speaker Segment</b></td><td><kbd>{get_sc("split_speaker", "Shift+Enter")}</kbd></td></tr>
            <tr><td><b>Find and Replace</b></td><td><kbd>{get_sc("find_replace", f"{cmd}+F")}</kbd></td></tr>
            <tr><td><b>Find Next Match</b></td><td><kbd>{get_sc("find_next", f"{cmd}+G")}</kbd></td></tr>
            <tr><td><b>Insert Timestamp Line (Edit Mode)</b></td><td><kbd>Enter</kbd></td></tr>
            <tr><td><b>Exit Editing Mode</b></td><td><kbd>Esc</kbd></td></tr>
        </table>

        <h3>AI Pipeline & Tools</h3>
        <table>
            <tr><td><b>Transcribe Audio</b></td><td><kbd>{get_sc("transcribe", f"{cmd}+T")}</kbd></td></tr>
            <tr><td><b>Detect Speakers (Diarization)</b></td><td><kbd>{get_sc("detect_speakers", f"{cmd}+D")}</kbd></td></tr>
            <tr><td><b>Detect Stories</b></td><td><kbd>{get_sc("detect_stories", f"{cmd}+Shift+A")}</kbd></td></tr>
            <tr><td><b>Translate Transcript</b></td><td><kbd>{get_sc("translate", f"{cmd}+Shift+L")}</kbd></td></tr>
            <tr><td><b>Multi-Stage Processing Pipeline</b></td><td><kbd>{get_sc("run_pipeline", f"{cmd}+R")}</kbd></td></tr>
            <tr><td><b>Regenerate Waveform</b></td><td><kbd>{get_sc("regen_waveform", f"{cmd}+Shift+W")}</kbd></td></tr>
            <tr><td><b>Regenerate Video Thumbnails</b></td><td><kbd>{get_sc("regen_thumbnails", f"{cmd}+Shift+T")}</kbd></td></tr>
            <tr><td><b>Clear Temporary Cache</b></td><td><kbd>{get_sc("clear_cache", f"{cmd}+{opt}+C")}</kbd></td></tr>
            <tr><td><b>Normalize Audio Loudness</b></td><td><kbd>{get_sc("normalize_loudness", f"{cmd}+{opt}+N")}</kbd></td></tr>
            <tr><td><b>Manage AI Models</b></td><td><kbd>{get_sc("manage_models", f"{cmd}+M")}</kbd></td></tr>
            <tr><td><b>Manage Plugins & Add-ons</b></td><td><kbd>{get_sc("manage_plugins", f"{cmd}+Shift+X")}</kbd></td></tr>
        </table>

        <h3>Settings & Diagnostics</h3>
        <table>
            <tr><td><b>Preferences</b></td><td><kbd>{get_sc("preferences", f"{cmd}+P")}</kbd></td></tr>
            <tr><td><b>Customize Keyboard Shortcuts</b></td><td><kbd>{get_sc("customize_shortcuts", f"{cmd}+K")}</kbd></td></tr>
            <tr><td><b>GPU Acceleration Settings</b></td><td><kbd>{get_sc("gpu_settings", f"{cmd}+{opt}+G")}</kbd></td></tr>
            <tr><td><b>Glossary & Custom Vocabulary</b></td><td><kbd>{get_sc("glossary", f"{cmd}+Shift+G")}</kbd></td></tr>
            <tr><td><b>Check for Updates</b></td><td><kbd>{get_sc("check_updates", f"{cmd}+U")}</kbd></td></tr>
            <tr><td><b>Keyboard Shortcuts Reference</b></td><td><kbd>{get_sc("help_shortcuts", "F1" if not is_mac else "Cmd+?")}</kbd></td></tr>
            <tr><td><b>About Radio & TV Story Segmenter</b></td><td><kbd>{get_sc("about", "Shift+F1")}</kbd></td></tr>
            <tr><td><b>Open Diagnostic Log Folder</b></td><td><kbd>{get_sc("diagnostic_log", f"{cmd}+Shift+K")}</kbd></td></tr>
            <tr><td><b>Third-Party Licenses</b></td><td><kbd>{get_sc("licenses", f"{cmd}+Shift+F1")}</kbd></td></tr>
        </table>
        """

        browser.setHtml(html_content)
        layout.addWidget(browser)

        button_box = QDialogButtonBox(dialog)
        customize_btn = button_box.addButton("Customize Shortcuts...", QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        def _open_customize():
            dialog.accept()
            self.open_preferences_dialog(initial_category="Keyboard Shortcuts")

        customize_btn.clicked.connect(_open_customize)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def show_diagnostic_test_bench(self):
        """Open the interactive System Diagnostic Test Bench dialog."""
        try:
            from test_runner import create_diagnostic_dialog
            dlg = create_diagnostic_dialog(parent=self)
            dlg.exec()
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Diagnostic Test Bench Error",
                f"Failed to launch the Diagnostic Test Bench dialog:\n\n{exc}"
            )

    def show_performance_benchmark(self):
        """Open the interactive System Performance & Speed Benchmark dialog."""
        try:
            from benchmark import create_benchmark_dialog
            dlg = create_benchmark_dialog(parent=self)
            dlg.exec()
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Performance Benchmark Error",
                f"Failed to launch the Performance Benchmark dialog:\n\n{exc}"
            )

    def open_plugins_manager(self):
        """Open the Plugin Manager dialog to enable, disable, or inspect plugins."""
        if not hasattr(self, "plugin_manager"):
            return
        from plugins.manager import PluginManagerDialog
        dlg = PluginManagerDialog(self.plugin_manager, self)
        dlg.exec()
        self.refresh_plugin_menus()

    def open_id3_tag_editor(self, mp3_path: str | None = None):
        """Open the ID3 Tag Editor dialog to view and edit MP3 audio metadata."""
        try:
            from id3_editor import ID3TagEditorDialog
            dlg = ID3TagEditorDialog(parent=self, mp3_path=mp3_path)
            dlg.exec()
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "ID3 Tag Editor Error",
                f"Failed to launch the ID3 Tag Editor dialog:\n\n{exc}"
            )


    def open_youtube_publish_dialog(self, story=None):
        """Open the YouTube video publishing dialog or export view from the YouTube plugin."""
        if hasattr(self, "plugin_manager") and self.plugin_manager.is_plugin_enabled("youtube"):
            if hasattr(self, "open_unified_export_dialog"):
                initial_scope = "selected_stories" if story is not None else None
                self.open_unified_export_dialog(initial_scope=initial_scope, initial_dest="youtube")
                return
            plugin = self.plugin_manager.plugins.get("youtube")
            if plugin:
                from plugins.youtube.plugin import YouTubePublishDialog
                # If no story was explicitly passed, check selected story in UI
                if story is None and hasattr(self, "stories") and hasattr(self, "current_selected_story_indices"):
                    sel = getattr(self, "current_selected_story_indices", [])
                    if sel and 0 <= sel[0] < len(self.stories):
                        story = self.stories[sel[0]]
                dlg = YouTubePublishDialog(plugin, parent=self, story=story)
                dlg.exec()
                return
        QMessageBox.information(
            self,
            "YouTube Plugin Required",
            "The YouTube Video Publisher plugin is not enabled or not loaded.\n"
            "You can enable it under Settings > Manage Plugins & Add-ons.",
        )

    def open_wordpress_publish_dialog(self, story=None):
        """Open the WordPress direct publish dialog from the WordPress plugin."""
        if hasattr(self, "plugin_manager") and self.plugin_manager.is_plugin_enabled("wordpress"):
            plugin = self.plugin_manager.plugins.get("wordpress")
            if plugin and hasattr(plugin, "open_publish_dialog"):
                if story is None and hasattr(self, "stories") and hasattr(self, "current_selected_story_indices"):
                    sel = getattr(self, "current_selected_story_indices", [])
                    if sel and 0 <= sel[0] < len(self.stories):
                        story = self.stories[sel[0]]
                plugin.open_publish_dialog(parent=self, story=story)
                return
        QMessageBox.information(
            self,
            "WordPress Plugin Required",
            "The WordPress Publisher plugin is not enabled or not loaded.\n"
            "You can enable it under Settings > Manage Plugins & Add-ons.",
        )

    def open_loudness_normalization_dialog(self):
        """Open the Audio Loudness Normalization & Telemetry modal dialog."""
        from dialogs import AudioLoudnessNormalizationDialog
        dlg = AudioLoudnessNormalizationDialog(self)
        dlg.exec()



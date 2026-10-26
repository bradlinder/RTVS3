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
        """Display a searchable, dynamically generated reference table of all active shortcuts."""
        import html
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QLineEdit, QTextBrowser, QDialogButtonBox
        )
        from shortcuts.manager import ShortcutsManager
        from shortcuts.schema import format_sequence_display, _get_shortcuts_theme_mode

        mgr = getattr(self, "shortcuts_manager", None)
        if mgr is None:
            mgr = ShortcutsManager(getattr(self, "settings_store", None))

        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts Reference")
        dialog.resize(680, 580)
        dialog.setMinimumSize(540, 420)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        search_bar = QLineEdit(dialog)
        search_bar.setPlaceholderText("Search shortcuts by action name, key, or category...")
        search_bar.setClearButtonEnabled(True)
        layout.addWidget(search_bar)

        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(False)
        layout.addWidget(browser)

        category_order = [
            "File & Project",
            "Playback & Transport",
            "Story & Segment Editing",
            "Search & Transcript Tools",
            "Timeline & Navigation",
            "Help & Diagnostics",
        ]

        definitions = mgr.get_definitions()

        def render_html(query: str = "") -> str:
            query = query.strip().lower()
            theme_mode = _get_shortcuts_theme_mode()
            is_light = theme_mode == "light"

            bg_color = "#ffffff" if is_light else "#1e222b"
            text_color = "#1e293b" if is_light else "#e2e8f0"
            header_color = "#0969da" if is_light else "#58a6ff"
            border_color = "#e2e8f0" if is_light else "#334155"
            th_border = "#94a3b8" if is_light else "#475569"
            kbd_bg = "#f1f5f9" if is_light else "#2b303c"
            kbd_border = "#cbd5e1" if is_light else "#4f5666"
            kbd_text = "#0f172a" if is_light else "#f1f5f9"
            desc_color = "#64748b" if is_light else "#94a3b8"

            grouped = {}
            for defn in definitions:
                cur_seq = mgr.get_current_shortcut(defn.action_id)
                disp_seq = format_sequence_display(cur_seq) if (cur_seq and cur_seq != "None") else "Unassigned"

                if query:
                    searchable = f"{defn.name} {defn.category} {defn.description} {disp_seq}".lower()
                    if query not in searchable:
                        continue

                grouped.setdefault(defn.category, []).append((defn, disp_seq))

            if not grouped:
                return (
                    f"<body style='font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Arial, sans-serif; "
                    f"font-size: 13px; color: {text_color}; background-color: {bg_color}; padding: 20px; text-align: center;'>"
                    f"<p style='color: {desc_color}; margin-top: 40px; font-size: 14px;'>"
                    f"No shortcuts found matching \"<b>{html.escape(query)}</b>\".</p></body>"
                )

            html_parts = [
                f"""
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                        font-size: 13px;
                        color: {text_color};
                        background-color: {bg_color};
                        padding: 12px;
                        margin: 0;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }}
                    th {{
                        text-align: left;
                        padding: 6px 8px;
                        border-bottom: 2px solid {th_border};
                        font-weight: 600;
                        color: {text_color};
                    }}
                    td {{
                        padding: 6px 8px;
                        border-bottom: 1px solid {border_color};
                        vertical-align: middle;
                    }}
                    kbd {{
                        background-color: {kbd_bg};
                        border: 1px solid {kbd_border};
                        border-radius: 4px;
                        padding: 2px 7px;
                        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
                        font-size: 12px;
                        color: {kbd_text};
                        white-space: nowrap;
                    }}
                    h3 {{
                        margin-top: 14px;
                        margin-bottom: 8px;
                        color: {header_color};
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    .desc {{
                        color: {desc_color};
                        font-size: 11px;
                        margin-top: 2px;
                    }}
                    .unassigned {{
                        color: {desc_color};
                        font-style: italic;
                    }}
                </style>
                <body>
                """
            ]

            all_cats = list(category_order)
            for c in grouped.keys():
                if c not in all_cats:
                    all_cats.append(c)

            for cat in all_cats:
                items = grouped.get(cat)
                if not items:
                    continue
                html_parts.append(f"<h3>{html.escape(cat)}</h3>")
                html_parts.append("<table>")
                html_parts.append("<thead><tr><th style='width: 60%;'>Action</th><th style='width: 40%;'>Shortcut</th></tr></thead>")
                html_parts.append("<tbody>")
                for defn, disp_seq in items:
                    desc_html = f"<div class='desc'>{html.escape(defn.description)}</div>" if defn.description else ""
                    if disp_seq == "Unassigned":
                        key_html = "<span class='unassigned'>Unassigned</span>"
                    else:
                        key_html = f"<kbd>{html.escape(disp_seq)}</kbd>"
                    html_parts.append(
                        f"<tr><td><b>{html.escape(defn.name)}</b>{desc_html}</td><td>{key_html}</td></tr>"
                    )
                html_parts.append("</tbody></table>")

            html_parts.append("</body>")
            return "".join(html_parts)

        browser.setHtml(render_html())
        search_bar.textChanged.connect(lambda txt: browser.setHtml(render_html(txt)))

        button_box = QDialogButtonBox(dialog)
        customize_btn = button_box.addButton("Customize Shortcuts...", QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        def _open_customize():
            dialog.accept()
            self.open_preferences_dialog(initial_category="Keyboard Shortcuts")

        customize_btn.clicked.connect(_open_customize)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(button_box)

        search_bar.setFocus()
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



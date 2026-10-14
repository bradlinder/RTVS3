"""Main application menu bar and action assembly for Radio & TV Story Segmenter."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    APP_DISPLAY_NAME,
    PROJECT_VERSION,
    ffmpeg_path,
    ffprobe_path,
    format_time,
    platform_seq,
    safe_filename,
)

class PersistentMenu(QMenu):
    """A QMenu subclass that stays open when checkable toggle options are activated,
    allowing users to toggle multiple items without the menu immediately closing."""

    def addMenu(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            menu = PersistentMenu(args[0], self)
            super().addMenu(menu)
            return menu
        return super().addMenu(*args, **kwargs)

    def mouseReleaseEvent(self, event):
        is_left = True
        if hasattr(event, "button"):
            btn = event.button()
            is_left = (btn == Qt.MouseButton.LeftButton if hasattr(Qt, "MouseButton") else btn == Qt.LeftButton)
        if is_left:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            action = self.actionAt(pos)
            if action and action.isCheckable() and not action.menu():
                action.trigger()
                self.update()
                return
        super().mouseReleaseEvent(event)




class UiMenusMixin:
    """Mixin providing menu construction, action shortcut wiring, and menu synchronization."""
    def build_menus(self):
        """Construct the main application menu bar and associated keyboard shortcuts."""
        menubar = self.menuBar()
        menubar.clear()

        # ==========================================
        # File Menu
        # NOTE FOR FUTURE MENU ADDITIONS: Every action added to any menu MUST have an explicit
        # keyboard shortcut assigned via platform_seq(...) or QKeySequence, and MUST be documented
        # in show_shortcuts_dialog() and the README.
        # ==========================================
        file_menu = menubar.addMenu("&File")

        # 1. Media Input
        open_media_act = QAction("&Open Media...", self)
        open_media_act.setShortcut(QKeySequence.Open)
        open_media_act.setToolTip("Open an audio or video file (WAV, MP3, MP4, MOV, MKV, FLAC, AIFF, etc.).")
        open_media_act.setStatusTip("Open an audio or video file (WAV, MP3, MP4, MOV, MKV, FLAC, AIFF, etc.).")
        open_media_act.triggered.connect(self.open_media)
        self.open_media_action = open_media_act
        file_menu.addAction(open_media_act)

        open_doc_act = QAction("Open &Document...", self)
        open_doc_act.setShortcut(platform_seq("Ctrl+Alt+O"))
        open_doc_act.setToolTip("Import an external text document (.txt, .docx, .pdf, .html, .md) directly into the transcript workspace.")
        open_doc_act.setStatusTip("Import an external text document (.txt, .docx, .pdf, .html, .md) directly into the transcript workspace.")
        open_doc_act.triggered.connect(self.open_document)
        self.open_doc_action = open_doc_act
        file_menu.addAction(open_doc_act)

        file_menu.addSeparator()

        # 2. Project Creation & Loading
        new_proj_act = QAction("&New Project", self)
        new_proj_act.setShortcut(QKeySequence.New)
        new_proj_act.triggered.connect(self.new_project)
        self.new_proj_action = new_proj_act
        file_menu.addAction(new_proj_act)

        open_proj_act = QAction("Open &Project...", self)
        open_proj_act.setShortcut(platform_seq("Ctrl+Shift+O"))
        open_proj_act.triggered.connect(self.open_project_dialog)
        self.open_proj_action = open_proj_act
        file_menu.addAction(open_proj_act)

        self.recent_menu = file_menu.addMenu("Recent Projects")
        self._refresh_recent_projects_menu()

        close_proj_act = QAction("&Close Project", self)
        close_proj_act.setShortcut(QKeySequence.Close)
        close_proj_act.triggered.connect(self.close_project)
        self.close_proj_action = close_proj_act
        file_menu.addAction(close_proj_act)

        file_menu.addSeparator()

        # 3. Project Persistence
        self.save_action = QAction("&Save Project", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self.save_project)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction("Save Project &As...", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)
        self.save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(self.save_as_action)

        self.export_zip_action = QAction("Export &Project Archive (.zip)...", self)
        self.export_zip_action.setShortcut(platform_seq("Ctrl+Shift+E"))
        self.export_zip_action.triggered.connect(self.export_project_archive)
        file_menu.addAction(self.export_zip_action)

        file_menu.addSeparator()

        # 4. Export & Batch Processing
        export_act = QAction("&Export...", self)
        export_act.setShortcut(platform_seq("Ctrl+E"))
        export_act.triggered.connect(self.open_unified_export_dialog)
        self.export_action = export_act
        file_menu.addAction(export_act)

        copy_yt_act = QAction("Copy &YouTube Chapters to Clipboard", self)
        copy_yt_act.setShortcut(platform_seq("Ctrl+Shift+Y"))
        copy_yt_act.triggered.connect(lambda: self.copy_youtube_chapters_to_clipboard() if hasattr(self, "copy_youtube_chapters_to_clipboard") else None)
        self.copy_yt_chapters_action = copy_yt_act
        file_menu.addAction(copy_yt_act)

        batch_act = QAction("&Batch Processing...", self)
        batch_act.setShortcut(platform_seq("Ctrl+Shift+B"))
        batch_act.triggered.connect(self.open_batch_processing_dialog)
        self.batch_file_action = batch_act
        self.batch_process_action = batch_act
        file_menu.addAction(batch_act)

        self.plugins_export_menu = file_menu.addMenu("Publishing & Plugins")

        backup_act = QAction("&Backup & Restore...", self)
        backup_act.triggered.connect(getattr(self, "open_backup_restore_dialog", lambda: None))
        self.backup_restore_action = backup_act
        file_menu.addAction(backup_act)

        file_menu.addSeparator()

        # 5. Application Exit
        exit_act = QAction("E&xit", self)
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.triggered.connect(self.close)
        self.exit_action = exit_act
        file_menu.addAction(exit_act)

        # ==========================================
        # Edit Menu
        # ==========================================
        edit_menu = menubar.addMenu("&Edit")

        self.undo_action = self.undo_stack.createUndoAction(self, "&Undo")
        self.undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = self.undo_stack.createRedoAction(self, "&Redo")
        self.redo_action.setShortcut(platform_seq("Ctrl+Shift+Z"))
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        add_comment_act = QAction("Add / Edit &Comment...", self)
        add_comment_act.setShortcut(platform_seq("Ctrl+M"))
        add_comment_act.triggered.connect(lambda: getattr(self, "add_comment_from_selection", lambda: None)())
        self.add_comment_action = add_comment_act
        edit_menu.addAction(add_comment_act)

        edit_menu.addSeparator()

        find_act = QAction("&Find and Replace...", self)
        find_act.setShortcut(QKeySequence.Find)
        find_act.triggered.connect(self.open_find_dialog)
        self.find_action = find_act
        edit_menu.addAction(find_act)

        edit_menu.addSeparator()

        purge_data_act = QAction("Clear / &Purge Project Data...", self)
        purge_data_act.setToolTip("Selectively wipe transcript, translations, speakers, stories, or media")
        purge_data_act.triggered.connect(lambda: getattr(self, "open_purge_project_data_dialog", lambda: None)())
        self.purge_data_action = purge_data_act
        edit_menu.addAction(purge_data_act)

        # ==========================================
        # View Menu
        # ==========================================
        view_menu = PersistentMenu("&View", self)
        menubar.addMenu(view_menu)

        # Main Panel Visibility Toggles (Alt+1-5 on Win/Linux, Ctrl+Alt+1-5 on Mac)
        panel_mod = "Ctrl+Alt" if sys.platform == "darwin" else "Alt"

        self.toggle_timeline_action = QAction("&Timeline Panel", self, checkable=True)
        self.toggle_timeline_action.setShortcut(QKeySequence(f"{panel_mod}+1"))
        self.toggle_timeline_action.setChecked(True)
        self.toggle_timeline_action.toggled.connect(lambda checked: self.timeline.setVisible(checked))
        view_menu.addAction(self.toggle_timeline_action)

        self.toggle_transcript_action = QAction("&Transcript Panel", self, checkable=True)
        self.toggle_transcript_action.setShortcut(QKeySequence(f"{panel_mod}+2"))
        self.toggle_transcript_action.setChecked(True)
        self.toggle_transcript_action.toggled.connect(lambda checked: self.transcript_panel.setVisible(checked))
        view_menu.addAction(self.toggle_transcript_action)

        self.toggle_stories_action = QAction("&Stories Panel", self, checkable=True)
        self.toggle_stories_action.setShortcut(QKeySequence(f"{panel_mod}+3"))
        self.toggle_stories_action.setChecked(True)
        self.toggle_stories_action.toggled.connect(lambda checked: self.stories_panel.setVisible(checked))
        view_menu.addAction(self.toggle_stories_action)

        self.toggle_activity_action = QAction("&Activity History Panel", self, checkable=True)
        self.toggle_activity_action.setShortcut(QKeySequence(f"{panel_mod}+4"))
        self.toggle_activity_action.setChecked(True)
        self.toggle_activity_action.toggled.connect(lambda checked: self.activity_panel.setVisible(checked))
        view_menu.addAction(self.toggle_activity_action)

        self.toggle_comments_action = QAction("&Comments Sidebar Panel", self, checkable=True)
        self.toggle_comments_action.setShortcut(platform_seq("Ctrl+Alt+C"))
        self.toggle_comments_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.toggle_comments_action.setChecked(str(getattr(self, "show_comments", False)).lower() in {"1", "true", "yes"})
        self.toggle_comments_action.toggled.connect(lambda checked: getattr(self, "toggle_show_comments", getattr(self, "toggle_show_notes", lambda c: None))(checked))
        view_menu.addAction(self.toggle_comments_action)
        self.toggle_notes_action = self.toggle_comments_action

        self.toggle_comment_highlights_action = QAction("Show &Comment Highlights", self, checkable=True)
        self.toggle_comment_highlights_action.setShortcut(platform_seq("Ctrl+Alt+H"))
        self.toggle_comment_highlights_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.toggle_comment_highlights_action.setChecked(str(getattr(self, "show_comment_highlights", True)).lower() in {"1", "true", "yes"})
        self.toggle_comment_highlights_action.toggled.connect(lambda checked: getattr(self, "toggle_comment_highlights", lambda c: None)(checked))
        view_menu.addAction(self.toggle_comment_highlights_action)

        view_menu.addSeparator()

        # 1. Timeline Submenu
        timeline_menu = view_menu.addMenu("&Timeline")

        self.show_waveform_action = QAction("Show &Waveform", self, checkable=True)
        self.show_waveform_action.setShortcut(platform_seq("Ctrl+Alt+W"))
        self.show_waveform_action.setChecked(getattr(self, "timeline_show_waveform", True))
        self.show_waveform_action.toggled.connect(self.toggle_waveform_view)
        timeline_menu.addAction(self.show_waveform_action)

        self.show_thumbnails_action = QAction("Show Video &Thumbnails", self, checkable=True)
        self.show_thumbnails_action.setShortcut(platform_seq("Ctrl+Alt+T"))
        self.show_thumbnails_action.setChecked(getattr(self, "timeline_show_thumbnails", True))
        self.show_thumbnails_action.toggled.connect(self.toggle_thumbnail_view)
        timeline_menu.addAction(self.show_thumbnails_action)

        timeline_menu.addSeparator()

        self.video_preview_action = QAction("&Video Preview Window", self, checkable=True)
        self.video_preview_action.setShortcut(platform_seq("Ctrl+Shift+V"))
        self.video_preview_action.setEnabled(False)
        self.video_preview_action.toggled.connect(self.toggle_video_preview)
        timeline_menu.addAction(self.video_preview_action)

        # 2. Transcript Submenu
        transcript_menu = view_menu.addMenu("T&ranscript")

        self.show_speaker_labels_action = QAction("Show &Speaker Labels", self, checkable=True)
        self.show_speaker_labels_action.setShortcut(platform_seq("Ctrl+Alt+S"))
        self.show_speaker_labels_action.setChecked(getattr(self, "show_speaker_labels", True))
        self.show_speaker_labels_action.toggled.connect(self.toggle_speaker_labels)
        transcript_menu.addAction(self.show_speaker_labels_action)

        self.show_timestamps_action = QAction("Show T&imestamps", self, checkable=True)
        self.show_timestamps_action.setShortcut(platform_seq("Ctrl+Alt+I"))
        self.show_timestamps_action.setChecked(getattr(self, "show_timestamps", True))
        self.show_timestamps_action.toggled.connect(self.toggle_timestamps)
        transcript_menu.addAction(self.show_timestamps_action)

        self.show_milliseconds_action = QAction("Show &Milliseconds in Timestamps", self, checkable=True)
        self.show_milliseconds_action.setChecked(getattr(self, "show_milliseconds", False))
        self.show_milliseconds_action.toggled.connect(getattr(self, "toggle_milliseconds", lambda c: None))
        transcript_menu.addAction(self.show_milliseconds_action)

        transcript_menu.addSeparator()

        self.transcript_show_comments_action = self.toggle_comments_action
        transcript_menu.addAction(self.transcript_show_comments_action)

        self.transcript_show_highlights_action = self.toggle_comment_highlights_action
        transcript_menu.addAction(self.transcript_show_highlights_action)

        self.transcript_edit_mode_action = QAction("&Edit Transcript Mode", self, checkable=True)
        self.transcript_edit_mode_action.setShortcut(platform_seq("F2"))
        self.transcript_edit_mode_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.transcript_edit_mode_action.setChecked(getattr(self.transcript_view, "is_editing_mode", False) if hasattr(self, "transcript_view") else False)
        self.transcript_edit_mode_action.triggered.connect(lambda checked: getattr(self, "toggle_transcript_editing_mode", lambda: None)(checked))
        self.addAction(self.transcript_edit_mode_action)
        transcript_menu.addAction(self.transcript_edit_mode_action)

        transcript_menu.addSeparator()

        # Language Display Submenu
        self.language_display_menu = transcript_menu.addMenu("&Language Display")
        self.lang_action_group = QActionGroup(self)
        self.lang_action_group.setExclusive(True)

        self.lang_en_action = QAction("English (Original)", self, checkable=True)
        self.lang_en_action.setChecked(True)
        self.lang_en_action.triggered.connect(lambda: getattr(self, "change_translation_display", lambda m: None)("en"))
        self.lang_action_group.addAction(self.lang_en_action)
        self.language_display_menu.addAction(self.lang_en_action)

        self.lang_es_action = QAction("Español (Translation)", self, checkable=True)
        self.lang_es_action.setEnabled(False)
        self.lang_es_action.triggered.connect(lambda: getattr(self, "change_translation_display", lambda m: None)("es"))
        self.lang_action_group.addAction(self.lang_es_action)
        self.language_display_menu.addAction(self.lang_es_action)

        self.lang_split_action = QAction("Bilingual (Split View)", self, checkable=True)
        self.lang_split_action.setEnabled(False)
        self.lang_split_action.triggered.connect(lambda: getattr(self, "change_translation_display", lambda m: None)("split"))
        self.lang_action_group.addAction(self.lang_split_action)
        self.language_display_menu.addAction(self.lang_split_action)

        view_menu.addSeparator()

        theme_menu = view_menu.addMenu("&Theme")
        dark_theme_act = QAction("&Dark", self)
        dark_theme_act.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_act)

        light_theme_act = QAction("&Light", self)
        light_theme_act.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_act)

        hc_theme_act = QAction("&High Contrast", self)
        hc_theme_act.triggered.connect(lambda: self.set_theme("high_contrast"))
        theme_menu.addAction(hc_theme_act)

        # ==========================================
        # Tools Menu (AI Pipeline)
        # ==========================================
        tools_menu = menubar.addMenu("&Tools")
        self.tools_menu = tools_menu
        self.plugin_tools_actions = []

        self.transcribe_action = QAction("&Transcribe Audio...", self)
        self.transcribe_action.setShortcut(platform_seq("Ctrl+T"))
        self.transcribe_action.setEnabled(False)
        self.transcribe_action.triggered.connect(self.start_transcription)
        tools_menu.addAction(self.transcribe_action)

        self.diarize_action = QAction("&Detect Speakers...", self)
        self.diarize_action.setShortcut(platform_seq("Ctrl+D"))
        self.diarize_action.setEnabled(False)
        self.diarize_action.triggered.connect(self.start_diarization)
        tools_menu.addAction(self.diarize_action)

        self.auto_detect_action = QAction("&Detect Stories...", self)
        self.auto_detect_action.setShortcut(platform_seq("Ctrl+Shift+A"))
        self.auto_detect_action.setEnabled(False)
        self.auto_detect_action.triggered.connect(self.start_auto_detect_stories)
        tools_menu.addAction(self.auto_detect_action)

        self.translate_action = QAction("&Translate...", self)
        self.translate_action.setShortcut(platform_seq("Ctrl+Shift+L"))
        self.translate_action.setEnabled(False)
        self.translate_action.triggered.connect(lambda: self.start_translation("en", "es"))
        self.tools_translate_action = self.translate_action
        self.translate_action.setVisible(False)
        tools_menu.addAction(self.translate_action)

        tools_menu.addSeparator()

        # Retained as an instance attribute so set_tools_actions_enabled() calls do not fail
        self.transcribe_diarize_action = QAction("Transcribe && Detect &Speakers...", self)
        self.transcribe_diarize_action.setEnabled(False)
        self.transcribe_diarize_action.triggered.connect(self.start_transcribe_and_diarize)

        self.transcribe_diarize_detect_action = QAction("&Multi-Stage Processing...", self)
        self.transcribe_diarize_detect_action.setShortcut(platform_seq("Ctrl+R"))
        self.transcribe_diarize_detect_action.setEnabled(False)
        self.transcribe_diarize_detect_action.triggered.connect(self.start_full_auto_pipeline)
        tools_menu.addAction(self.transcribe_diarize_detect_action)

        tools_menu.addSeparator()

        # ==========================================
        # Voice Profile Tools Submenu
        # ==========================================
        self.voice_tools_menu = tools_menu.addMenu("&Voice Profile Tools")

        self.teach_voice_action = QAction("&Teach / Match Voice Across Project...", self)
        self.teach_voice_action.setToolTip("Use active speaker turn as a reference voice profile to find and reassign matching turns across the timeline")
        self.teach_voice_action.setEnabled(False)
        self.teach_voice_action.triggered.connect(lambda: getattr(self, "teach_voice_profile_dialog", lambda *a, **k: None)(-1))
        self.voice_tools_menu.addAction(self.teach_voice_action)

        self.ref_profile_new_spk_action = QAction("&Set as Reference Profile for New Speaker...", self)
        self.ref_profile_new_spk_action.setToolTip("Prompt for a new speaker name and immediately match similar turns using active acoustic profile")
        self.ref_profile_new_spk_action.setEnabled(False)
        self.ref_profile_new_spk_action.triggered.connect(lambda: getattr(self, "teach_voice_profile_dialog", lambda *a, **k: None)(-1, prompt_new_speaker=True))
        self.voice_tools_menu.addAction(self.ref_profile_new_spk_action)

        self.refine_dialog_action = QAction("&Refine Rapid Dialog Turns (A/B Classifier)...", self)
        self.refine_dialog_action.setToolTip("Competitively classify turns in a conversational range between two confirmed speakers")
        self.refine_dialog_action.setEnabled(False)
        self.refine_dialog_action.triggered.connect(lambda: getattr(self, "prompt_refine_speaker_run", lambda *a, **k: None)())
        self.voice_tools_menu.addAction(self.refine_dialog_action)

        self.voice_tools_menu.addSeparator()

        self.manage_speakers_action = QAction("&Manage Speakers && Detection Clusters...", self)
        self.manage_speakers_action.setToolTip("Inspect speaker durations, rename or assign aliases, and merge duplicate acoustic clusters")
        self.manage_speakers_action.setEnabled(False)
        self.manage_speakers_action.triggered.connect(lambda: getattr(self, "open_speaker_manager_dialog", lambda: None)())
        self.voice_tools_menu.addAction(self.manage_speakers_action)

        self.manage_voice_profiles_action = QAction("&Manage Voice Profiles...", self)
        self.manage_voice_profiles_action.setToolTip("Inspect, edit, import, or delete persistent station voice profiles across recordings")
        self.manage_voice_profiles_action.setEnabled(True)
        self.manage_voice_profiles_action.triggered.connect(lambda: getattr(self, "open_manage_voice_profiles_dialog", lambda: None)())
        self.voice_tools_menu.addAction(self.manage_voice_profiles_action)

        tools_menu.addSeparator()

        self.batch_processing_action = self.batch_file_action
        tools_menu.addAction(self.batch_processing_action)

        tools_menu.addSeparator()

        self.regen_waveform_action = QAction("&Regenerate Waveform", self)
        self.regen_waveform_action.setShortcut(platform_seq("Ctrl+Shift+W"))
        self.regen_waveform_action.setEnabled(False)
        self.regen_waveform_action.triggered.connect(self.regenerate_waveform)
        tools_menu.addAction(self.regen_waveform_action)

        self.regen_thumbnails_action = QAction("Regenerate Video &Thumbnails", self)
        self.regen_thumbnails_action.setShortcut(platform_seq("Ctrl+Shift+T"))
        self.regen_thumbnails_action.setEnabled(False)
        self.regen_thumbnails_action.triggered.connect(self.regenerate_video_thumbnails)
        tools_menu.addAction(self.regen_thumbnails_action)

        self.clear_cache_action = QAction("&Clear Temporary Cache...", self)
        self.clear_cache_action.triggered.connect(self.open_clear_cache_dialog)
        tools_menu.addAction(self.clear_cache_action)

        tools_menu.addSeparator()

        self.manage_models_action = QAction("&Manage AI Models...", self)
        self.manage_models_action.setShortcut(platform_seq("Ctrl+Alt+M"))
        self.manage_models_action.triggered.connect(self.open_model_cleanup_dialog)
        self.translation_model_action = self.manage_models_action
        tools_menu.addAction(self.manage_models_action)

        self.manage_plugins_action = QAction("&Manage Plugins && Add-ons...", self)
        self.manage_plugins_action.setShortcut(platform_seq("Ctrl+Shift+X"))
        self.manage_plugins_action.triggered.connect(self.open_plugins_manager)
        tools_menu.addAction(self.manage_plugins_action)

        self.id3_editor_action = QAction("ID3 &Tag Editor (MP3)...", self)
        self.id3_editor_action.setShortcut(platform_seq("Ctrl+Shift+I"))
        self.id3_editor_action.triggered.connect(lambda: self.open_id3_tag_editor())
        tools_menu.addAction(self.id3_editor_action)

        # ==========================================
        # Settings Menu
        # ==========================================
        settings_menu = menubar.addMenu("&Settings")

        pref_act = QAction("&Preferences...", self)
        # Ctrl+P on Windows/Linux, Cmd+P on macOS (platform_seq automatically adapts Meta/Ctrl)
        pref_act.setShortcut(platform_seq("Ctrl+P"))
        pref_act.triggered.connect(self.open_preferences_dialog)
        self.pref_action = pref_act
        settings_menu.addAction(pref_act)

        shortcuts_pref_act = QAction("Customize &Keyboard Shortcuts...", self)
        shortcuts_pref_act.setShortcut(platform_seq("F8"))
        shortcuts_pref_act.triggered.connect(lambda: self.open_preferences_dialog(initial_category="Keyboard Shortcuts"))
        self.shortcuts_pref_action = shortcuts_pref_act
        settings_menu.addAction(shortcuts_pref_act)

        clear_cache_settings_act = QAction("Clear &Temporary Cache...", self)
        clear_cache_settings_act.triggered.connect(self.open_clear_cache_dialog)
        settings_menu.addAction(clear_cache_settings_act)

        settings_menu.addAction(self.manage_models_action)

        gpu_act = QAction("&GPU Acceleration Settings...", self)
        gpu_act.setShortcut(platform_seq("Ctrl+Alt+G"))
        gpu_act.triggered.connect(self.open_gpu_acceleration_settings)
        self.gpu_action = gpu_act
        settings_menu.addAction(gpu_act)

        glossary_act = QAction("&Glossary & Custom Vocabulary...", self)
        glossary_act.setShortcut(platform_seq("Ctrl+Shift+G"))
        glossary_act.triggered.connect(self.open_glossary_dialog)
        self.glossary_action = glossary_act
        settings_menu.addAction(glossary_act)

        backup_settings_act = QAction("&Backup & Restore Settings...", self)
        backup_settings_act.triggered.connect(getattr(self, "open_backup_restore_dialog", lambda: None))
        self.backup_settings_action = backup_settings_act
        settings_menu.addAction(backup_settings_act)

        restore_defaults_act = QAction("&Restore System Defaults...", self)
        restore_defaults_act.triggered.connect(getattr(self, "open_restore_system_defaults_dialog", lambda: None))
        self.restore_defaults_action = restore_defaults_act
        settings_menu.addAction(restore_defaults_act)

        # Language submenu in Settings menu
        self.language_menu = settings_menu.addMenu("&Language / Idioma")
        self.ui_lang_action_group = QActionGroup(self)
        self.ui_lang_action_group.setExclusive(True)

        self.ui_lang_en_action = QAction("English", self, checkable=True)
        self.ui_lang_en_action.setChecked(getattr(self, "language", "en") != "es")
        self.ui_lang_en_action.triggered.connect(lambda: self.set_language("en"))
        self.ui_lang_action_group.addAction(self.ui_lang_en_action)
        self.language_menu.addAction(self.ui_lang_en_action)

        self.ui_lang_es_action = QAction("Español (Spanish)", self, checkable=True)
        self.ui_lang_es_action.setChecked(getattr(self, "language", "en") == "es")
        self.ui_lang_es_action.triggered.connect(lambda: self.set_language("es"))
        self.ui_lang_action_group.addAction(self.ui_lang_es_action)
        self.language_menu.addAction(self.ui_lang_es_action)

        settings_menu.addSeparator()

        update_act = QAction("Check for &Updates...", self)
        update_act.setShortcut(platform_seq("Ctrl+Alt+U"))
        update_act.triggered.connect(self.check_for_updates)
        self.update_action = update_act
        settings_menu.addAction(update_act)

        # ==========================================
        # Help Menu
        # ==========================================
        help_menu = menubar.addMenu("&Help")

        shortcuts_act = QAction("&Keyboard Shortcuts", self)
        # HelpContents maps to F1 on Windows/Linux, and Cmd+? on macOS (avoiding brightness key conflict)
        shortcuts_act.setShortcut(QKeySequence.HelpContents)
        shortcuts_act.triggered.connect(self.show_shortcuts_dialog)
        self.shortcuts_help_action = shortcuts_act
        help_menu.addAction(shortcuts_act)

        help_menu.addSeparator()

        about_act = QAction("&About Radio & TV Story Segmenter", self)
        about_act.setShortcut(platform_seq("Shift+F1"))
        about_act.triggered.connect(self.show_about_dialog)
        self.about_action = about_act
        help_menu.addAction(about_act)

        log_act = QAction("Open &Diagnostic Log Folder", self)
        log_act.setShortcut(platform_seq("Ctrl+Shift+K"))
        log_act.triggered.connect(self.open_diagnostic_log_folder)
        self.log_action = log_act
        help_menu.addAction(log_act)

        test_bench_act = QAction("&Run Diagnostic Test Bench...", self)
        test_bench_act.setShortcut(platform_seq("Ctrl+Shift+D"))
        test_bench_act.triggered.connect(self.show_diagnostic_test_bench)
        self.test_bench_action = test_bench_act
        help_menu.addAction(test_bench_act)

        benchmark_act = QAction("Run &Feature & Performance Benchmark...", self)
        benchmark_act.setShortcut(platform_seq("Ctrl+Alt+B"))
        benchmark_act.triggered.connect(self.show_performance_benchmark)
        self.benchmark_action = benchmark_act
        help_menu.addAction(benchmark_act)

        licenses_act = QAction("&Third-Party Licenses", self)
        licenses_act.setShortcut(platform_seq("Ctrl+Shift+F1"))
        licenses_act.triggered.connect(self.show_licenses_dialog)
        self.licenses_action = licenses_act
        help_menu.addAction(licenses_act)

        # Apply any saved user custom keyboard shortcut mappings
        self.apply_user_shortcuts()

    def apply_user_shortcuts(self):
        """Rebind all menu actions and application shortcuts according to user preferences."""
        if not hasattr(self, "shortcuts_manager") or not self.shortcuts_manager:
            from shortcuts_manager import ShortcutsManager
            self.shortcuts_manager = ShortcutsManager(getattr(self, "settings_store", None))
        self.shortcuts_manager.apply_to_window(self)

    def _refresh_recent_projects_menu(self):
        """Update recent projects submenu items based on user settings store."""
        if not hasattr(self, "recent_menu") or self.recent_menu is None:
            return
        self.recent_menu.clear()
        recent_paths = self.settings_store.value("recent_projects", [])
        if isinstance(recent_paths, str):
            try:
                recent_paths = json.loads(recent_paths)
            except Exception:
                recent_paths = []

        if not isinstance(recent_paths, list) or not recent_paths:
            empty_act = QAction("No Recent Projects", self)
            empty_act.setEnabled(False)
            self.recent_menu.addAction(empty_act)
            return

        for p_str in recent_paths:
            path = Path(p_str)
            label = path.name if path.name else str(path)
            act = QAction(label, self)
            act.setData(str(path))
            act.triggered.connect(
                lambda checked=False, target=str(path): self.load_project_file(
                    target, prompt=True, preserve_media=False
                )
            )
            self.recent_menu.addAction(act)

    def _check_external_dependencies(self):
        """Check bundled media tools and record actionable diagnostics."""
        missing = []
        if ffmpeg_path() is None:
            missing.append("ffmpeg")
        if ffprobe_path() is None:
            missing.append("ffprobe")
        if missing:
            self.log_activity(
                "[DEPENDENCIES] Missing bundled media tool(s): " + ", ".join(missing) +
                ". Install media runtime components or place them in the application's runtime/bin folder.",
                mark_dirty=False,
            )
        else:
            self.log_activity("[DEPENDENCIES] FFmpeg and ffprobe detected.", mark_dirty=False)

    def _sync_undo_redo_actions(self):
        """Synchronize undo/redo action states with QUndoStack."""
        if hasattr(self, "undo_action") and hasattr(self, "undo_stack"):
            self.undo_action.setEnabled(self.undo_stack.canUndo())
            desc = self.undo_stack.undoText()
            self.undo_action.setText(f"&Undo {desc}".strip() if self.undo_stack.canUndo() else "&Undo")
        if hasattr(self, "redo_action") and hasattr(self, "undo_stack"):
            self.redo_action.setEnabled(self.undo_stack.canRedo())
            desc = self.undo_stack.redoText()
            self.redo_action.setText(f"&Redo {desc}".strip() if self.undo_stack.canRedo() else "&Redo")

    def _remember_directory(self, path):
        """Persist directory of chosen file to improve user file dialog experience."""
        if not path:
            return
        try:
            p = Path(path)
            folder = p if p.is_dir() else p.parent
            if folder.exists():
                self.settings_store.setValue("last_directory", str(folder))
        except Exception:
            pass


    def update_processing_menu_status(self):
        """Update label annotations on Tools actions reflecting pipeline stage completion."""
        status = getattr(self, "processing_status", {})
        has_transcription = bool(status.get("transcription"))
        has_diarization = bool(status.get("diarization"))
        has_stories = bool(status.get("stories"))

        if hasattr(self, "transcribe_action"):
            self.transcribe_action.setText("Transcribe Audio (Complete)" if has_transcription else "Transcribe Audio...")
        if hasattr(self, "diarize_action"):
            self.diarize_action.setText("Detect Speakers (Complete)" if has_diarization else "Detect Speakers...")
        if hasattr(self, "auto_detect_action"):
            is_music = (getattr(self, "story_detection_mode", "voice") == "music")
            is_es = (getattr(self, "language", "en") == "es")
            if is_music:
                if is_es:
                    self.auto_detect_action.setText("&Detectar canciones (Completado)" if has_stories else "&Detectar canciones...")
                else:
                    self.auto_detect_action.setText("Detect Songs (Complete)" if has_stories else "&Detect Songs...")
            else:
                if is_es:
                    self.auto_detect_action.setText("&Detectar historias (Completado)" if has_stories else "&Detectar historias...")
                else:
                    self.auto_detect_action.setText("Detect Stories (Complete)" if has_stories else "&Detect Stories...")


    def refresh_plugin_menus(self):
        """Dynamically populate plugin export actions, tools menu actions, and core UI controls."""
        if not hasattr(self, "plugin_manager"):
            return

        # 1. Refresh Export & Publishing menu
        if hasattr(self, "plugins_export_menu"):
            self.plugins_export_menu.clear()
            has_export_actions = False
            for p in self.plugin_manager.plugins.values():
                is_p_enabled = getattr(p, "is_enabled", True)
                if callable(is_p_enabled):
                    is_p_enabled = is_p_enabled()
                if is_p_enabled and self.plugin_manager.is_plugin_enabled(p.id):
                    for label, callback in p.get_export_actions():
                        act = self.plugins_export_menu.addAction(label)
                        act.triggered.connect(callback)
                        has_export_actions = True
            self.plugins_export_menu.menuAction().setVisible(has_export_actions)

        # 2. Refresh Tools menu dynamic actions
        if hasattr(self, "plugin_tools_actions") and hasattr(self, "tools_menu"):
            for act in self.plugin_tools_actions:
                self.tools_menu.removeAction(act)
            self.plugin_tools_actions.clear()

            for p in self.plugin_manager.plugins.values():
                is_p_enabled = getattr(p, "is_enabled", True)
                if callable(is_p_enabled):
                    is_p_enabled = is_p_enabled()
                if is_p_enabled and self.plugin_manager.is_plugin_enabled(p.id):
                    for label, callback in p.get_tools_actions():
                        act = QAction(label, self)
                        act.triggered.connect(callback)
                        self.tools_menu.addAction(act)
                        self.plugin_tools_actions.append(act)

        # 3. Synchronize core UI elements according to plugin enabled state
        is_translation_enabled = self.plugin_manager.is_plugin_enabled("translation")
        has_translations = getattr(self, "has_spanish_translation", lambda: False)() or bool(getattr(self, "translations", {})) or getattr(self, "translation_display_mode", "en") != "en"
        if hasattr(self, "translate_button"):
            self.translate_button.setVisible(is_translation_enabled)
        if hasattr(self, "transcript_language_selector"):
            self.transcript_language_selector.setVisible(is_translation_enabled or has_translations)
        if hasattr(self, "translate_action"):
            self.translate_action.setVisible(is_translation_enabled)
        if hasattr(self, "tools_translate_action"):
            self.tools_translate_action.setVisible(is_translation_enabled)

        # 4. Populate plugin-provided story extensions (e.g. WordPress Post Settings widget)
        if hasattr(self, "setup_plugin_story_extensions"):
            self.setup_plugin_story_extensions()


"""Radio & TV Segmenter — Preferences reset and factory default restore engine.

Provides selective settings restoration dialog and handlers for resetting individual
preference categories or all settings to factory defaults.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QCheckBox, QMessageBox
)

from core_utils import make_dialog_maximizable, INTERNAL_APP_ID

logger = logging.getLogger(__name__)


class RestoreSelectedSettingsDialog(QDialog):
    """Presents users with a list of customizable settings that can be restored to defaults."""

    CATEGORIES = [
        ("general_appearance", "Theme & Startup Mode", "Theme mode (Dark), paragraph word count (65 words), and startup project behavior (Open last project)."),
        ("general_project_dirs", "Default Project Directory & Bundling", "Default projects folder, project subfolders (Transcripts/Media), and media copy settings."),
        ("general_autosave", "Auto-save Interval", "Automatic project save interval (5 minutes)."),
        ("keyboard_shortcuts", "Keyboard Shortcuts", "Custom keyboard shortcut assignments for all menu actions, tools, navigation, and editing commands."),
        ("audio_hardware", "Audio Settings & Volume", "Audio output device (System Default), default volume (100%), and automatic loudness normalization settings."),
        ("software_updates", "Software Updates & Repository", "Automatic update checks (Enabled), release channel (Stable), and official GitHub repository."),
        ("ai_models", "AI Models & Storage Directory", "Whisper speech recognition model (small, beam size 5), translation model (tiny), and models storage folder."),
        ("gpu_acceleration", "Hardware / GPU Acceleration", "GPU and DirectML hardware acceleration settings."),
        ("playback_timeline", "Playback & Timeline Display", "Skip duration (5s), waveform visibility, thumbnail strip, and transcript selection mode."),
        ("audio_fades", "Audio Fades & Fade Curve Defaults", "Enable audio fades (disabled), fade audio preview (disabled), default fade-in duration (0.0s), default fade-out duration (1.0s), and default fade curve (linear)."),
        ("detection_diarization", "Story Detection & Diarization Defaults", "Detection basis/mode (Voice), silence gap threshold / speech detection length (3.0s), lead-in padding (0.5s), default expected speakers (auto), speaker estimate prompt (enabled), and separation sensitivity (normal)."),
        ("batch_processing", "Batch Processing Tool Options", "Batch tasks (transcribe, diarize, detect stories), output formats, and batch custom directory."),
        ("export_options", "Export Window: Formats & Content Options", "Export formats (TXT, DOCX, Media enabled; SRT, VTT disabled) and content options (speakers, timestamps, languages)."),
        ("export_directory", "Export Window: Custom Location", "Clear saved custom export location and restore default project folder export routing."),
        ("wordpress_settings", "WordPress: Site Connection & Credentials", "Configured WordPress site URL, credentials, and cached categories/authors."),
    ]

    def __init__(self, parent=None, on_restore_selected=None):
        super().__init__(parent)
        self.setWindowTitle("Restore System Defaults")
        self.resize(540, 560)
        make_dialog_maximizable(self)
        self.on_restore_selected = on_restore_selected
        self.checkboxes = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        title_lbl = QLabel("<b>Select Settings to Restore to Defaults</b>")
        title_lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Choose which customizable areas and preferences you would like to reset back to factory defaults. "
            "Unchecked items will remain unchanged."
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Select all / Deselect all toolbar
        sel_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn.clicked.connect(self._deselect_all)
        sel_btn_layout.addWidget(select_all_btn)
        sel_btn_layout.addWidget(deselect_all_btn)
        sel_btn_layout.addStretch()
        layout.addLayout(sel_btn_layout)

        # Scroll area with customizable categories
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(8, 8, 8, 8)

        for cat_id, label_text, desc_text in self.CATEGORIES:
            if cat_id == "wordpress_settings":
                win = self.parent()
                show_wp = hasattr(win, "plugin_manager") and win.plugin_manager and win.plugin_manager.is_plugin_enabled("wordpress")
                if not show_wp:
                    continue
            item_box = QWidget()
            item_layout = QVBoxLayout(item_box)
            item_layout.setContentsMargins(4, 4, 4, 4)
            item_layout.setSpacing(2)

            cb = QCheckBox(label_text)
            cb.setStyleSheet("font-weight: bold;")
            cb.setChecked(True)
            self.checkboxes[cat_id] = cb
            item_layout.addWidget(cb)

            sub_lbl = QLabel(desc_text)
            sub_lbl.setStyleSheet("color: #888888; margin-left: 20px; font-size: 11px;")
            sub_lbl.setWordWrap(True)
            item_layout.addWidget(sub_lbl)

            scroll_layout.addWidget(item_box)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setDefault(True)
        reset_btn.setStyleSheet("font-weight: bold;")
        cancel_btn = QPushButton("Cancel")

        reset_btn.clicked.connect(self._handle_reset)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def _handle_reset(self):
        selected_ids = [cat_id for cat_id, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected_ids:
            QMessageBox.information(
                self,
                "No Settings Selected",
                "Please select at least one customizable setting category to restore to defaults."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Reset to Defaults",
            f"Are you sure you want to restore the {len(selected_ids)} selected setting category/categories to defaults?\n\n"
            "This will reset the chosen settings to their initial factory values.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if callable(self.on_restore_selected):
            self.on_restore_selected(selected_ids)

        QMessageBox.information(
            self,
            "Defaults Restored",
            f"The {len(selected_ids)} selected setting category/categories have been successfully restored to defaults."
        )
        self.accept()


class PreferencesResetMixin:
    """Mixin providing settings reset and restore dialog actions."""

    def apply_settings_reset(self, selected_ids, live_widgets=None):
        """Apply factory default settings to the requested categories and update live widgets if present."""
        if not selected_ids:
            return
        selected_set = set(selected_ids)
        lw = live_widgets or {}

        # 1. General Appearance
        if "general_appearance" in selected_set:
            self.settings_store.setValue("theme_mode", "dark")
            self.settings_store.setValue("startup_project_mode", "last")
            self.settings_store.setValue("single_instance_mode", "single")
            self.settings_store.setValue("show_floating_selection_toolbar", "true")
            self.settings_store.setValue("open_comments_on_launch", "false")
            self.settings_store.setValue("show_comment_highlights", "true")
            self.settings_store.setValue("show_timestamps", "true")
            self.settings_store.setValue("show_milliseconds", "false")
            self.settings_store.setValue("min_words_per_paragraph", 65)
            self.show_floating_selection_toolbar = True
            self.show_comment_highlights = True
            self.show_timestamps = True
            self.show_milliseconds = False
            self.min_words_per_paragraph = 65
            self.startup_project_mode = "last"
            if hasattr(self, "set_theme"):
                try:
                    self.set_theme("dark")
                except Exception:
                    pass
            if hasattr(self, "set_startup_project_mode"):
                try:
                    self.set_startup_project_mode("last")
                except Exception:
                    pass
            if hasattr(self, "show_timestamps_action"):
                self.show_timestamps_action.setChecked(True)
            if hasattr(self, "show_milliseconds_action"):
                self.show_milliseconds_action.setChecked(False)
            if hasattr(self, "toggle_comment_highlights"):
                try:
                    self.toggle_comment_highlights(True)
                except Exception:
                    pass
            if hasattr(self, "render_transcript"):
                try:
                    self.render_transcript()
                except Exception:
                    pass
            if "theme_combo" in lw and lw["theme_combo"]:
                idx = lw["theme_combo"].findText("dark")
                if idx >= 0:
                    lw["theme_combo"].setCurrentIndex(idx)
            if "startup_combo" in lw and lw["startup_combo"]:
                idx = lw["startup_combo"].findData("last")
                if idx >= 0:
                    lw["startup_combo"].setCurrentIndex(idx)
            if "single_instance_combo" in lw and lw["single_instance_combo"]:
                idx_si = lw["single_instance_combo"].findData("single")
                if idx_si >= 0:
                    lw["single_instance_combo"].setCurrentIndex(idx_si)
            if "floating_toolbar_chk" in lw and lw["floating_toolbar_chk"]:
                lw["floating_toolbar_chk"].setChecked(True)
            if "open_comments_chk" in lw and lw["open_comments_chk"]:
                lw["open_comments_chk"].setChecked(False)
            if "show_highlights_chk" in lw and lw["show_highlights_chk"]:
                lw["show_highlights_chk"].setChecked(True)
            if "show_timestamps_chk" in lw and lw["show_timestamps_chk"]:
                lw["show_timestamps_chk"].setChecked(True)
            if "show_millis_chk" in lw and lw["show_millis_chk"]:
                lw["show_millis_chk"].setChecked(False)
                lw["show_millis_chk"].setEnabled(True)
            if "min_words_spin" in lw and lw["min_words_spin"]:
                lw["min_words_spin"].setValue(65)

        # 2. General Project Directories & Bundling
        if "general_project_dirs" in selected_set:
            self.settings_store.setValue("default_project_directory", "")
            self.settings_store.setValue("save_project_with_media", "false")
            self.settings_store.setValue("create_project_subfolders", "true")
            self.settings_store.setValue("media_ingest_mode", "reference")
            self.settings_store.setValue("copy_media_to_project_folder", "false")
            self.settings_store.setValue("last_directory", "")
            self.settings_store.setValue("last_open_directory", "")
            self.settings_store.setValue("last_saved_project_path", "")
            self.default_project_directory = ""
            if "proj_dir_edit" in lw and lw["proj_dir_edit"]:
                lw["proj_dir_edit"].setText("")
            if "save_with_media_chk" in lw and lw["save_with_media_chk"]:
                lw["save_with_media_chk"].setChecked(False)
            if "bundle_folder_chk" in lw and lw["bundle_folder_chk"]:
                lw["bundle_folder_chk"].setChecked(True)
            if "ingest_mode_combo" in lw and lw["ingest_mode_combo"]:
                lw["ingest_mode_combo"].setCurrentIndex(0)

        # 3. General Auto-save
        if "general_autosave" in selected_set:
            self.settings_store.setValue("auto_save_minutes", 5)
            self.auto_save_minutes = 5
            if hasattr(self, "update_auto_save_timer"):
                try:
                    self.update_auto_save_timer()
                except Exception:
                    pass
            if "autosave_spin" in lw and lw["autosave_spin"]:
                lw["autosave_spin"].setValue(5)

        # Keyboard Shortcuts
        if "keyboard_shortcuts" in selected_set:
            if hasattr(self, "shortcuts_manager") and self.shortcuts_manager:
                self.shortcuts_manager.reset_all()
                self.shortcuts_manager.save()
                self.shortcuts_manager.apply_to_window(self)
            else:
                try:
                    from PySide6.QtCore import QSettings
                    sc_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                    sc_settings.remove("keyboard_shortcuts")
                    sc_settings.sync()
                except Exception:
                    pass
            if "page_shortcuts" in lw and lw["page_shortcuts"]:
                if hasattr(lw["page_shortcuts"], "_populate_table"):
                    try:
                        lw["page_shortcuts"]._populate_table()
                    except Exception:
                        pass
                elif hasattr(lw["page_shortcuts"], "revert_changes"):
                    lw["page_shortcuts"].revert_changes()

        # 4. Audio Hardware
        if "audio_hardware" in selected_set:
            self.settings_store.setValue("audio_output_device", "System Default")
            self.settings_store.setValue("audio_output_volume", 100)
            self.master_volume = 1.0
            if hasattr(self, "apply_audio_output_device"):
                try:
                    self.apply_audio_output_device("System Default", 1.0)
                except Exception:
                    pass
            if "audio_dev_combo" in lw and lw["audio_dev_combo"]:
                lw["audio_dev_combo"].setCurrentIndex(0)
            if "vol_slider" in lw and lw["vol_slider"]:
                lw["vol_slider"].setValue(100)

        # 5. Software Updates
        if "software_updates" in selected_set:
            self.settings_store.setValue("auto_check_updates", "true")
            self.settings_store.setValue("github_repo", DEFAULT_GITHUB_REPO)
            self.settings_store.setValue("update_channel", "stable")
            if "auto_update_chk" in lw and lw["auto_update_chk"]:
                lw["auto_update_chk"].setChecked(True)
            if "repo_edit" in lw and lw["repo_edit"]:
                lw["repo_edit"].setText(DEFAULT_GITHUB_REPO)
            if "update_channel_combo" in lw and lw["update_channel_combo"]:
                lw["update_channel_combo"].setCurrentIndex(0)

        # 6. AI Models & Storage
        if "ai_models" in selected_set:
            try:
                from prs_shared import get_app_data_dir
                from processing import set_models_storage_dir
                def_model_dir = str(get_app_data_dir() / "models")
                set_models_storage_dir(def_model_dir)
            except Exception:
                def_model_dir = ""
            self.settings_store.setValue("whisper_model", "parakeet-onnx")
            self.settings_store.setValue("whisper_beam_size", 5)
            self.settings_store.setValue("translation_model_variant", "tiny")
            self.settings_store.setValue("auto_detect_fallback_whisper", "true")
            self.whisper_model = "parakeet-onnx"
            self.whisper_beam_size = 5
            self.translation_model_variant = "tiny"
            if hasattr(self, "refresh_whisper_model_chooser"):
                try:
                    self.refresh_whisper_model_chooser()
                except Exception:
                    pass
            if hasattr(self, "refresh_translation_model_chooser"):
                try:
                    self.refresh_translation_model_chooser()
                except Exception:
                    pass
            if "model_dir_edit" in lw and lw["model_dir_edit"] and def_model_dir:
                lw["model_dir_edit"].setText(def_model_dir)
            if "pref_whisper_combo" in lw and lw["pref_whisper_combo"]:
                idx = lw["pref_whisper_combo"].findData("parakeet-onnx")
                if idx >= 0:
                    lw["pref_whisper_combo"].setCurrentIndex(idx)
            if "pref_beam_combo" in lw and lw["pref_beam_combo"]:
                idx = lw["pref_beam_combo"].findData(5)
                if idx >= 0:
                    lw["pref_beam_combo"].setCurrentIndex(idx)
            if "pref_trans_combo" in lw and lw["pref_trans_combo"]:
                idx = lw["pref_trans_combo"].findData("tiny")
                if idx >= 0:
                    lw["pref_trans_combo"].setCurrentIndex(idx)
            if "pref_auto_lang_chk" in lw and lw["pref_auto_lang_chk"]:
                lw["pref_auto_lang_chk"].setChecked(True)

        # 7. Hardware / GPU Acceleration
        if "gpu_acceleration" in selected_set:
            if hasattr(self, "gpu_acceleration_settings_key"):
                try:
                    self.settings_store.setValue(self.gpu_acceleration_settings_key(), "false")
                except Exception:
                    pass
            self.settings_store.setValue("gpu_acceleration_enabled", "false")
            self.settings_store.setValue("gpu_transcription_enabled", "true")
            self.settings_store.setValue("gpu_translation_enabled", "true")
            self.settings_store.setValue("gpu_diarization_enabled", "true")
            if "global_gpu_chk" in lw and lw["global_gpu_chk"]:
                lw["global_gpu_chk"].setChecked(False)
            if "gpu_trans_chk" in lw and lw["gpu_trans_chk"]:
                lw["gpu_trans_chk"].setChecked(True)
            if "gpu_translate_chk" in lw and lw["gpu_translate_chk"]:
                lw["gpu_translate_chk"].setChecked(True)
            if "gpu_diarize_chk" in lw and lw["gpu_diarize_chk"]:
                lw["gpu_diarize_chk"].setChecked(True)

        # 8. Playback & Timeline
        if "playback_timeline" in selected_set:
            self.settings_store.setValue("skip_seconds", 5)
            self.settings_store.setValue("timeline_show_waveform", "true")
            self.settings_store.setValue("timeline_show_thumbnails", "true")
            self.settings_store.setValue("timeline_thumbnail_position", "below")
            self.settings_store.setValue("transcript_selection_mode", "replace")
            self.settings_store.setValue("transcript_font_scale", 1.0)
            self.settings_store.setValue("show_speaker_labels", "true")
            self.skip_seconds = 5
            self.timeline_show_waveform = True
            self.timeline_show_thumbnails = True
            self.timeline_thumbnail_position = "below"
            self.transcript_selection_mode = "replace"
            self.transcript_font_scale = 1.0
            self.show_speaker_labels = True
            if hasattr(self, "show_speaker_labels_action"):
                self.show_speaker_labels_action.setChecked(True)
            if hasattr(self, "timeline"):
                try:
                    self.timeline.set_skip_seconds(5)
                    self.timeline.set_timeline_views(True, True)
                    if hasattr(self.timeline, "set_thumbnail_position"):
                        self.timeline.set_thumbnail_position("below")
                except Exception:
                    pass
            if hasattr(self, "transcript_view") and hasattr(self.transcript_view, "set_selection_mode"):
                try:
                    self.transcript_view.set_selection_mode("replace")
                except Exception:
                    pass
            if hasattr(self, "skip_display"):
                try:
                    self.skip_display.setValue(5)
                except Exception:
                    pass
            if "skip_spin" in lw and lw["skip_spin"]:
                lw["skip_spin"].setValue(5)
            if "wave_chk" in lw and lw["wave_chk"]:
                lw["wave_chk"].setChecked(True)
            if "thumb_chk" in lw and lw["thumb_chk"]:
                lw["thumb_chk"].setChecked(True)
            if "thumb_pos_combo" in lw and lw["thumb_pos_combo"]:
                pos_idx = lw["thumb_pos_combo"].findData("below")
                if pos_idx >= 0:
                    lw["thumb_pos_combo"].setCurrentIndex(pos_idx)
            if "sel_mode_combo" in lw and lw["sel_mode_combo"]:
                idx = lw["sel_mode_combo"].findData("replace")
                if idx >= 0:
                    lw["sel_mode_combo"].setCurrentIndex(idx)

        # 8b. Audio Fades & Defaults
        if "audio_fades" in selected_set or "playback_timeline" in selected_set:
            self.settings_store.setValue("enable_audio_fades", "false")
            self.settings_store.setValue("preview_audio_fades", "false")
            self.settings_store.setValue("default_fade_in_duration", 0.0)
            self.settings_store.setValue("default_fade_out_duration", 1.0)
            self.settings_store.setValue("default_fade_curve", "linear")
            self.enable_audio_fades = False
            self.preview_audio_fades = False
            if hasattr(self, "timeline") and hasattr(self.timeline, "canvas"):
                self.timeline.canvas.show_audio_fades = False
                self.timeline.canvas.update()
            if hasattr(self, "story_list"):
                self.story_list.viewport().update()
            if "enable_fades_chk" in lw and lw["enable_fades_chk"]:
                lw["enable_fades_chk"].setChecked(False)
            if "preview_fades_chk" in lw and lw["preview_fades_chk"]:
                lw["preview_fades_chk"].setChecked(False)
            if "fade_in_spin" in lw and lw["fade_in_spin"]:
                lw["fade_in_spin"].setValue(0.0)
            if "fade_out_spin" in lw and lw["fade_out_spin"]:
                lw["fade_out_spin"].setValue(1.0)
            if "fade_curve_combo" in lw and lw["fade_curve_combo"]:
                lw["fade_curve_combo"].setCurrentData("linear")

        # 9. Story Detection & Diarization
        if "detection_diarization" in selected_set:
            self.settings_store.setValue("story_detection_mode", "voice")
            self.settings_store.setValue("silence_threshold", 3.0)
            self.settings_store.setValue("lead_in_padding", 0.5)
            self.settings_store.setValue("default_expected_speakers", "auto")
            self.settings_store.setValue("ask_expected_speakers", True)
            self.settings_store.setValue("diarization_sensitivity", "normal")
            self.story_detection_mode = "voice"
            self.silence_threshold = 3.0
            self.lead_in_padding = 0.5
            self.expected_speakers = "auto"
            self.diarization_sensitivity = "normal"
            if hasattr(self, "update_story_segment_terminology"):
                try:
                    self.update_story_segment_terminology()
                except Exception:
                    pass
            if "det_mode_combo" in lw and lw["det_mode_combo"]:
                idx_m = lw["det_mode_combo"].findData("voice")
                if idx_m >= 0:
                    lw["det_mode_combo"].setCurrentIndex(idx_m)
            if "gap_spin" in lw and lw["gap_spin"]:
                lw["gap_spin"].setValue(3.0)
            if "pad_spin" in lw and lw["pad_spin"]:
                lw["pad_spin"].setValue(0.5)
            if "expected_speakers_combo" in lw and lw["expected_speakers_combo"]:
                idx = lw["expected_speakers_combo"].findData("auto")
                if idx >= 0:
                    lw["expected_speakers_combo"].setCurrentIndex(idx)
            if "sensitivity_combo" in lw and lw["sensitivity_combo"]:
                idx_s = lw["sensitivity_combo"].findData("normal")
                if idx_s >= 0:
                    lw["sensitivity_combo"].setCurrentIndex(idx_s)
            if "ask_speakers_chk" in lw and lw["ask_speakers_chk"]:
                lw["ask_speakers_chk"].setChecked(True)

        # 10. Batch Processing Tool Options
        if "batch_processing" in selected_set:
            self.settings_store.setValue("batch_custom_output_dir", "")
            self.settings_store.setValue("batch_opt_proc_transcribe", True)
            self.settings_store.setValue("batch_opt_proc_diarize", True)
            self.settings_store.setValue("batch_opt_proc_stories", True)
            self.settings_store.setValue("batch_opt_proc_translate", False)
            self.settings_store.setValue("batch_opt_save_project", True)
            self.settings_store.setValue("batch_opt_skip_existing", True)
            self.settings_store.setValue("batch_opt_save_project_only", False)
            self.settings_store.setValue("batch_opt_fmt_txt", True)
            self.settings_store.setValue("batch_opt_fmt_docx", True)
            self.settings_store.setValue("batch_opt_fmt_srt", False)
            self.settings_store.setValue("batch_opt_fmt_vtt", False)
            self.settings_store.setValue("batch_opt_include_speakers", True)
            self.settings_store.setValue("batch_opt_include_times", False)
            if "batch_dir_edit" in lw and lw["batch_dir_edit"]:
                lw["batch_dir_edit"].setText("")
            if "batch_transcribe_chk" in lw and lw["batch_transcribe_chk"]:
                lw["batch_transcribe_chk"].setChecked(True)
            if "batch_diarize_chk" in lw and lw["batch_diarize_chk"]:
                lw["batch_diarize_chk"].setChecked(True)
            if "batch_stories_chk" in lw and lw["batch_stories_chk"]:
                lw["batch_stories_chk"].setChecked(True)
            if "batch_translate_chk" in lw and lw["batch_translate_chk"]:
                lw["batch_translate_chk"].setChecked(False)
            if "batch_save_proj_chk" in lw and lw["batch_save_proj_chk"]:
                lw["batch_save_proj_chk"].setChecked(True)
            if "batch_skip_exist_chk" in lw and lw["batch_skip_exist_chk"]:
                lw["batch_skip_exist_chk"].setChecked(True)
            if "batch_proj_only_chk" in lw and lw["batch_proj_only_chk"]:
                lw["batch_proj_only_chk"].setChecked(False)
            if "batch_txt_chk" in lw and lw["batch_txt_chk"]:
                lw["batch_txt_chk"].setChecked(True)
            if "batch_docx_chk" in lw and lw["batch_docx_chk"]:
                lw["batch_docx_chk"].setChecked(True)
            if "batch_srt_chk" in lw and lw["batch_srt_chk"]:
                lw["batch_srt_chk"].setChecked(False)
            if "batch_vtt_chk" in lw and lw["batch_vtt_chk"]:
                lw["batch_vtt_chk"].setChecked(False)
            if "batch_spk_chk" in lw and lw["batch_spk_chk"]:
                lw["batch_spk_chk"].setChecked(True)
            if "batch_time_chk" in lw and lw["batch_time_chk"]:
                lw["batch_time_chk"].setChecked(False)

        # 11. Export Window Options & Formats
        if "export_options" in selected_set:
            try:
                from PySide6.QtCore import QSettings
                exp_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                for k in [
                    "export_opt_fmt_txt", "export_opt_fmt_docx", "export_opt_fmt_srt", "export_opt_fmt_vtt",
                    "export_opt_fmt_media", "export_opt_include_speakers", "export_opt_include_timestamps",
                    "export_opt_include_en", "export_opt_include_es"
                ]:
                    exp_settings.remove(k)
                exp_settings.sync()
            except Exception:
                pass

        # 12. Export Window Custom Location
        if "export_directory" in selected_set:
            try:
                from PySide6.QtCore import QSettings
                exp_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                exp_settings.remove("export_opt_custom_loc_enabled")
                exp_settings.remove("export_opt_custom_dir")
                exp_settings.sync()
            except Exception:
                pass

        # 13. WordPress Connection & Credentials
        if "wordpress_settings" in selected_set:
            try:
                from PySide6.QtCore import QSettings
                wp_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                wp_user = str(wp_settings.value("wp_username", "") or "").strip()
                wp_settings.remove("wp_site_url")
                wp_settings.remove("wp_username")
                wp_settings.remove("wp_custom_text")
                wp_settings.remove("wp_custom_text_pos")
                wp_settings.remove("wp_custom_text_no_snippet")
                wp_settings.remove("wp_custom_text_no_excerpt")
                wp_settings.remove("wp_cached_categories")
                wp_settings.remove("wp_cached_authors")
                if wp_user:
                    wp_settings.remove(f"wp_pass_{wp_user}")
                    try:
                        import keyring
                        keyring.delete_password("RadioTVStorySegmenter", f"wp_{wp_user}")
                    except Exception:
                        pass
                wp_settings.sync()
            except Exception:
                pass

        if hasattr(self, "load_persistent_settings"):
            self.load_persistent_settings()

        try:
            self.settings_store.sync()
        except Exception:
            pass

        self.log_activity(f"[SETTINGS] Restored default settings for {len(selected_ids)} category/categories.")

    def open_restore_system_defaults_dialog(self):
        """Open the Restore System Defaults dialog directly from Settings menu or Backup & Restore Center."""
        dlg = RestoreSelectedSettingsDialog(
            parent=self,
            on_restore_selected=lambda chosen_ids: (
                self.apply_settings_reset(chosen_ids),
                self.settings_store.sync()
            )
        )
        dlg.exec()


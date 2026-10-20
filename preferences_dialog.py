"""Radio & TV Story Segmenter — Preferences Modal Dialog.

Provides the multi-category Preferences dialog shell, navigation list,
custom defaults saving, category reset wiring, and settings persistence.
"""

import logging
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QPushButton, QDialogButtonBox, QMessageBox
)

from prs_shared import APP_DISPLAY_NAME, DEFAULT_GITHUB_REPO, INTERNAL_APP_ID, set_models_storage_dir
from core_utils import make_dialog_maximizable
from preferences_reset import RestoreSelectedSettingsDialog, PreferencesResetMixin
from preferences_tabs_core import (
    build_general_tab, build_shortcuts_tab, build_audio_hardware_tab,
    build_updates_tab, build_ai_models_tab, build_gpu_tab
)
from preferences_tabs_media import (
    build_playback_timeline_tab, build_detection_tab, build_batch_tab,
    build_cleanup_tab, build_youtube_tab
)

logger = logging.getLogger(__name__)


class PreferencesDialogMixin(PreferencesResetMixin):
    """Provides the main open_preferences_dialog method and settings persistence."""

    def open_preferences_dialog(self, initial_category="General"):
        """Open the multi-category Preferences dialog."""
        if not isinstance(initial_category, str):
            initial_category = "General"

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Preferences — {APP_DISPLAY_NAME}")
        dialog.resize(700, 500)
        make_dialog_maximizable(dialog)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Left category tree / list
        cat_list = QListWidget(dialog)
        cat_list.setFixedWidth(160)
        categories = [
            "General", "Keyboard Shortcuts", "Audio Settings", "Updates & GitHub",
            "AI Models", "GPU Acceleration", "Playback & Timeline", "Detection",
            "Batch Processing", "Cleanup Data"
        ]
        show_wp = hasattr(self, "plugin_manager") and self.plugin_manager and self.plugin_manager.is_plugin_enabled("wordpress")
        show_yt = hasattr(self, "plugin_manager") and self.plugin_manager and self.plugin_manager.is_plugin_enabled("youtube")
        show_gd = hasattr(self, "plugin_manager") and self.plugin_manager and self.plugin_manager.is_plugin_enabled("gdocs")
        if show_wp:
            categories.append("WordPress")
        if show_yt:
            categories.append("YouTube")
        if show_gd:
            categories.append("Google Docs")

        for cat in categories:
            cat_list.addItem(QListWidgetItem(cat))
        content_layout.addWidget(cat_list)

        # Right stacked pages
        stack = QStackedWidget(dialog)
        live_widgets = {}

        def _add_custom_defaults_btn(layout, cat_title, cat_ids=None):
            row = QHBoxLayout()
            btn = QPushButton("Save as Custom Defaults")
            btn.setToolTip(f"Save current {cat_title} settings as your custom defaults.")
            def _save_custom():
                _save_preferences(close_dialog=False)
                QMessageBox.information(dialog, "Custom Defaults Saved", f"Current {cat_title} settings have been saved as your custom defaults.")
            btn.clicked.connect(_save_custom)
            row.addWidget(btn)

            if cat_ids:
                rst_btn = QPushButton("Restore Category Defaults")
                rst_btn.setToolTip(f"Reset {cat_title} settings back to system factory defaults.")
                def _restore_cat():
                    self.apply_settings_reset(cat_ids, live_widgets=live_widgets)
                    self.settings_store.sync()
                    QMessageBox.information(dialog, "Category Defaults Restored", f"Default settings for {cat_title} have been restored.")
                rst_btn.clicked.connect(_restore_cat)
                row.addWidget(rst_btn)

            row.addStretch()
            layout.addLayout(row)

        # Build Core Tabs
        stack.addWidget(build_general_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_shortcuts_tab(self, dialog, live_widgets))
        stack.addWidget(build_audio_hardware_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_updates_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_ai_models_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_gpu_tab(self, dialog, live_widgets, _add_custom_defaults_btn))

        # Build Media & Processing Tabs
        stack.addWidget(build_playback_timeline_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_detection_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_batch_tab(self, dialog, live_widgets, _add_custom_defaults_btn))
        stack.addWidget(build_cleanup_tab(self, dialog, live_widgets, _add_custom_defaults_btn))

        # Build Plugin Tabs
        page_wp = None
        if show_wp and hasattr(self, "plugin_manager") and self.plugin_manager:
            wp_plugin = self.plugin_manager.plugins.get("wordpress")
            if wp_plugin and hasattr(wp_plugin, "get_preferences_widget"):
                page_wp = wp_plugin.get_preferences_widget(dialog)
                if page_wp and page_wp.layout():
                    _add_custom_defaults_btn(page_wp.layout(), "WordPress Connection")
                stack.addWidget(page_wp)

        if show_yt:
            stack.addWidget(build_youtube_tab(self, dialog, live_widgets, _add_custom_defaults_btn))

        page_gd = None
        if show_gd and hasattr(self, "plugin_manager") and self.plugin_manager:
            gd_plugin = self.plugin_manager.plugins.get("gdocs")
            if gd_plugin and hasattr(gd_plugin, "get_preferences_widget"):
                page_gd = gd_plugin.get_preferences_widget(dialog)
                if page_gd:
                    if page_gd.layout():
                        _add_custom_defaults_btn(page_gd.layout(), "Google Docs & Drive")
                    stack.addWidget(page_gd)

        content_layout.addWidget(stack, 1)
        main_layout.addLayout(content_layout)

        # Switch page on category selection
        cat_list.currentRowChanged.connect(stack.setCurrentIndex)
        aliases = {
            "general": "general",
            "shortcuts": "keyboard shortcuts",
            "shortcut": "keyboard shortcuts",
            "keyboard": "keyboard shortcuts",
            "keys": "keyboard shortcuts",
            "hotkeys": "keyboard shortcuts",
            "key": "keyboard shortcuts",
            "keyboard shortcuts": "keyboard shortcuts",
            "audio": "audio hardware",
            "sound": "audio hardware",
            "updates": "updates & github",
            "github": "updates & github",
            "models": "ai models",
            "ai": "ai models",
            "ai models": "ai models",
            "gpu": "gpu acceleration",
            "cuda": "gpu acceleration",
            "gpu acceleration": "gpu acceleration",
            "playback": "playback & timeline",
            "timeline": "playback & timeline",
            "detection": "detection",
            "detect": "detection",
            "batch": "batch processing",
            "cleanup": "cleanup data",
            "cleanup data": "cleanup data",
            "purge": "cleanup data",
            "clear": "cleanup data",
            "cache": "cleanup data",
            "wordpress": "wordpress",
            "youtube": "youtube",
            "gdocs": "google docs",
            "google docs": "google docs",
            "googledocs": "google docs",
            "google": "google docs",
            "drive": "google docs",
        }
        requested = str(initial_category).strip().lower() if initial_category else "general"
        target = aliases.get(requested, requested)
        selected_index = 0
        for i, c in enumerate(categories):
            if c.lower() == target or c.lower().startswith(target):
                selected_index = i
                break
        cat_list.setCurrentRow(selected_index)

        # Dialog bottom bar
        bottom_bar = QHBoxLayout()
        restore_sel_btn = QPushButton("Restore System Defaults…")
        restore_sel_btn.setToolTip("Select specific settings and categories to restore to system factory defaults.")
        bottom_bar.addWidget(restore_sel_btn)
        bottom_bar.addStretch()

        btn_box = QDialogButtonBox(dialog)
        save_btn = btn_box.addButton("Save", QDialogButtonBox.ButtonRole.AcceptRole)
        apply_btn = btn_box.addButton("Apply", QDialogButtonBox.ButtonRole.ApplyRole)
        close_btn = btn_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        bottom_bar.addWidget(btn_box)
        main_layout.addLayout(bottom_bar)

        def _open_restore_selected_dialog():
            sel_dlg = RestoreSelectedSettingsDialog(
                parent=dialog,
                on_restore_selected=lambda chosen_ids: (
                    self.apply_settings_reset(chosen_ids, live_widgets=live_widgets),
                    self.settings_store.sync()
                )
            )
            sel_dlg.exec()

        restore_sel_btn.clicked.connect(_open_restore_selected_dialog)

        def _save_preferences(*args, close_dialog=True):
            # Save Keyboard Shortcuts
            page_shortcuts = live_widgets.get("page_shortcuts")
            if page_shortcuts is not None:
                page_shortcuts.save_shortcuts()
                if hasattr(self, "shortcuts_manager") and self.shortcuts_manager:
                    self.shortcuts_manager.apply_to_window(self)

            # Save General
            theme_combo = live_widgets.get("theme_combo")
            if theme_combo:
                new_theme = theme_combo.currentText()
                self.settings_store.setValue("theme_mode", new_theme)
                self.set_theme(new_theme)

            lang_combo = live_widgets.get("lang_combo")
            if lang_combo:
                new_lang = lang_combo.currentData()
                if new_lang and new_lang != getattr(self, "language", "en"):
                    self.set_language(new_lang, persist=True)

            startup_combo = live_widgets.get("startup_combo")
            if startup_combo:
                new_startup = startup_combo.currentData()
                if hasattr(self, "set_startup_project_mode"):
                    self.set_startup_project_mode(new_startup)
                else:
                    self.startup_project_mode = new_startup
                    self.settings_store.setValue("startup_project_mode", new_startup)

            proj_dir_edit = live_widgets.get("proj_dir_edit")
            if proj_dir_edit:
                self.default_project_directory = proj_dir_edit.text().strip()
                self.settings_store.setValue("default_project_directory", self.default_project_directory)

            save_with_media_chk = live_widgets.get("save_with_media_chk")
            if save_with_media_chk:
                self.settings_store.setValue("save_project_with_media", "true" if save_with_media_chk.isChecked() else "false")

            bundle_folder_chk = live_widgets.get("bundle_folder_chk")
            if bundle_folder_chk:
                self.settings_store.setValue("create_project_subfolders", "true" if bundle_folder_chk.isChecked() else "false")

            ingest_mode_combo = live_widgets.get("ingest_mode_combo")
            if ingest_mode_combo:
                chosen_ingest_mode = ingest_mode_combo.currentData()
                self.settings_store.setValue("media_ingest_mode", chosen_ingest_mode)
                self.settings_store.setValue("copy_media_to_project_folder", "true" if chosen_ingest_mode == "copy" else "false")

            single_instance_combo = live_widgets.get("single_instance_combo")
            if single_instance_combo:
                self.settings_store.setValue("single_instance_mode", single_instance_combo.currentData())

            autosave_spin = live_widgets.get("autosave_spin")
            if autosave_spin:
                self.auto_save_minutes = autosave_spin.value()
                self.settings_store.setValue("auto_save_minutes", self.auto_save_minutes)
                self.update_auto_save_timer()

            open_comments_chk = live_widgets.get("open_comments_chk")
            if open_comments_chk:
                self.settings_store.setValue("open_comments_on_launch", "true" if open_comments_chk.isChecked() else "false")

            show_highlights_chk = live_widgets.get("show_highlights_chk")
            if show_highlights_chk:
                new_show_hl = show_highlights_chk.isChecked()
                self.settings_store.setValue("show_comment_highlights", "true" if new_show_hl else "false")
                if hasattr(self, "toggle_comment_highlights"):
                    self.toggle_comment_highlights(new_show_hl)

            show_timestamps_chk = live_widgets.get("show_timestamps_chk")
            if show_timestamps_chk:
                new_show_ts = show_timestamps_chk.isChecked()
                self.settings_store.setValue("show_timestamps", "true" if new_show_ts else "false")
                self.show_timestamps = new_show_ts
                if hasattr(self, "show_timestamps_action"):
                    self.show_timestamps_action.setChecked(new_show_ts)

            show_millis_chk = live_widgets.get("show_millis_chk")
            if show_millis_chk:
                new_show_ms = show_millis_chk.isChecked()
                self.settings_store.setValue("show_milliseconds", "true" if new_show_ms else "false")
                self.show_milliseconds = new_show_ms
                if hasattr(self, "show_milliseconds_action"):
                    self.show_milliseconds_action.setChecked(new_show_ms)

            min_words_spin = live_widgets.get("min_words_spin")
            if min_words_spin:
                new_min_words = min_words_spin.value()
                self.settings_store.setValue("min_words_per_paragraph", new_min_words)
                self.min_words_per_paragraph = new_min_words

            if hasattr(self, "render_transcript"):
                self.render_transcript()

            # Save Audio Hardware
            audio_dev_combo = live_widgets.get("audio_dev_combo")
            vol_slider = live_widgets.get("vol_slider")
            if audio_dev_combo and vol_slider:
                new_dev = audio_dev_combo.currentText()
                self.settings_store.setValue("audio_output_device", new_dev)
                new_vol = vol_slider.value()
                self.settings_store.setValue("audio_output_volume", new_vol)
                if hasattr(self, "apply_audio_output_device"):
                    self.apply_audio_output_device(new_dev, new_vol / 100.0)

            # Save Audio Loudness Normalization & Auto-Boost
            auto_norm_chk = live_widgets.get("auto_norm_chk")
            if auto_norm_chk is not None:
                self.settings_store.setValue("auto_loudness_normalization", "true" if auto_norm_chk.isChecked() else "false")
            target_standard_combo = live_widgets.get("target_standard_combo")
            if target_standard_combo is not None:
                data = target_standard_combo.currentData()
                if isinstance(data, dict):
                    self.settings_store.setValue("target_standard", data.get("code", "broadcast"))
            target_lufs_spin = live_widgets.get("target_lufs_spin")
            if target_lufs_spin is not None:
                self.settings_store.setValue("target_lufs", float(target_lufs_spin.value()))
            max_true_peak_spin = live_widgets.get("max_true_peak_spin")
            if max_true_peak_spin is not None:
                self.settings_store.setValue("max_true_peak", float(max_true_peak_spin.value()))
            quiet_threshold_lufs_spin = live_widgets.get("quiet_threshold_lufs_spin")
            if quiet_threshold_lufs_spin is not None:
                self.settings_store.setValue("quiet_threshold_lufs", float(quiet_threshold_lufs_spin.value()))
            quiet_threshold_dbfs_spin = live_widgets.get("quiet_threshold_dbfs_spin")
            if quiet_threshold_dbfs_spin is not None:
                self.settings_store.setValue("quiet_threshold_dbfs", float(quiet_threshold_dbfs_spin.value()))
            apply_boost_playback_chk = live_widgets.get("apply_boost_playback_chk")
            if apply_boost_playback_chk is not None:
                self.settings_store.setValue("apply_boost_playback", "true" if apply_boost_playback_chk.isChecked() else "false")

            # Save Updates
            auto_update_chk = live_widgets.get("auto_update_chk")
            update_channel_combo = live_widgets.get("update_channel_combo")
            repo_edit = live_widgets.get("repo_edit")
            if auto_update_chk:
                self.settings_store.setValue("auto_check_updates", str(auto_update_chk.isChecked()).lower())
            if update_channel_combo:
                new_chan = update_channel_combo.currentData() or "stable"
                self.settings_store.setValue("update_channel", new_chan)
            if repo_edit:
                new_repo = repo_edit.text().strip()
                if new_repo:
                    if new_repo.lower() in ("bradlinder/rtvs", "bradlinder/radiotvstorysegmenter", "radiotvstorysegmenter"):
                        new_repo = DEFAULT_GITHUB_REPO
                    self.settings_store.setValue("github_repo", new_repo)

            # Save Models dir & selections
            model_dir_edit = live_widgets.get("model_dir_edit")
            if model_dir_edit:
                new_model_dir = model_dir_edit.text().strip()
                if new_model_dir:
                    set_models_storage_dir(new_model_dir)

            pref_whisper_combo = live_widgets.get("pref_whisper_combo")
            if pref_whisper_combo:
                new_whisper = pref_whisper_combo.currentData()
                if new_whisper:
                    self.whisper_model = str(new_whisper)
                    self.settings_store.setValue("whisper_model", self.whisper_model)
                    if hasattr(self, "refresh_whisper_model_chooser"):
                        self.refresh_whisper_model_chooser()

            pref_auto_lang_chk = live_widgets.get("pref_auto_lang_chk")
            if pref_auto_lang_chk:
                self.settings_store.setValue("auto_detect_fallback_whisper", str(pref_auto_lang_chk.isChecked()).lower())

            pref_beam_combo = live_widgets.get("pref_beam_combo")
            if pref_beam_combo:
                new_beam = pref_beam_combo.currentData()
                if new_beam is not None:
                    self.whisper_beam_size = int(new_beam)
                    self.settings_store.setValue("whisper_beam_size", self.whisper_beam_size)

            pref_trans_combo = live_widgets.get("pref_trans_combo")
            if pref_trans_combo:
                new_trans = pref_trans_combo.currentData()
                if new_trans:
                    self.translation_model_variant = str(new_trans)
                    self.settings_store.setValue("translation_model_variant", self.translation_model_variant)
                    if hasattr(self, "refresh_translation_model_chooser"):
                        self.refresh_translation_model_chooser()

            # Save Playback
            skip_spin = live_widgets.get("skip_spin")
            if skip_spin:
                self.skip_seconds = skip_spin.value()
                self.settings_store.setValue("skip_seconds", self.skip_seconds)
                if hasattr(self, "timeline"):
                    self.timeline.set_skip_seconds(self.skip_seconds)

            play_rate_combo = live_widgets.get("play_rate_combo")
            if play_rate_combo:
                new_rate = float(play_rate_combo.currentData() or 1.0)
                self.playback_rate = new_rate
                self.settings_store.setValue("playback_rate", new_rate)
                if hasattr(self, "set_playback_rate"):
                    self.set_playback_rate(new_rate)

            preroll_spin = live_widgets.get("preroll_spin")
            if preroll_spin:
                self.speed_listening_preroll_seconds = preroll_spin.value()
                self.settings_store.setValue("speed_listening_preroll_seconds", self.speed_listening_preroll_seconds)

            wave_chk = live_widgets.get("wave_chk")
            if wave_chk:
                self.timeline_show_waveform = wave_chk.isChecked()
                self.settings_store.setValue("timeline_show_waveform", str(self.timeline_show_waveform).lower())

            thumb_chk = live_widgets.get("thumb_chk")
            if thumb_chk:
                self.timeline_show_thumbnails = thumb_chk.isChecked()
                self.settings_store.setValue("timeline_show_thumbnails", str(self.timeline_show_thumbnails).lower())

            thumb_pos_combo = live_widgets.get("thumb_pos_combo")
            if thumb_pos_combo:
                new_thumb_pos = thumb_pos_combo.currentData() or "below"
                self.timeline_thumbnail_position = new_thumb_pos
                self.settings_store.setValue("timeline_thumbnail_position", new_thumb_pos)

            if hasattr(self, "timeline"):
                self.timeline.set_timeline_views(getattr(self, "timeline_show_waveform", True), getattr(self, "timeline_show_thumbnails", True))
                if hasattr(self.timeline, "set_thumbnail_position"):
                    self.timeline.set_thumbnail_position(getattr(self, "timeline_thumbnail_position", "below"))

            # Save Selection Mode
            sel_mode_combo = live_widgets.get("sel_mode_combo")
            if sel_mode_combo:
                new_sel_mode = sel_mode_combo.currentData() or "replace"
                self.transcript_selection_mode = new_sel_mode
                self.settings_store.setValue("transcript_selection_mode", new_sel_mode)
                if hasattr(self, "transcript_view") and hasattr(self.transcript_view, "set_selection_mode"):
                    self.transcript_view.set_selection_mode(new_sel_mode)

            # Save Floating Selection Toolbar Preference
            floating_toolbar_chk = live_widgets.get("floating_toolbar_chk")
            if floating_toolbar_chk:
                self.show_floating_selection_toolbar = floating_toolbar_chk.isChecked()
                self.settings_store.setValue("show_floating_selection_toolbar", str(self.show_floating_selection_toolbar).lower())
                if hasattr(self, "transcript_view"):
                    self.transcript_view.show_floating_selection_toolbar = self.show_floating_selection_toolbar
                    if hasattr(self.transcript_view, "selection_bubble") and not self.show_floating_selection_toolbar:
                        self.transcript_view.selection_bubble.hide()

            # Save Audio Fades Preferences
            enable_fades_chk = live_widgets.get("enable_fades_chk")
            preview_fades_chk = live_widgets.get("preview_fades_chk")
            fade_in_spin = live_widgets.get("fade_in_spin")
            fade_out_spin = live_widgets.get("fade_out_spin")
            fade_curve_combo = live_widgets.get("fade_curve_combo")
            if enable_fades_chk:
                self.enable_audio_fades = enable_fades_chk.isChecked()
                self.settings_store.setValue("enable_audio_fades", "true" if self.enable_audio_fades else "false")
            if preview_fades_chk:
                self.preview_audio_fades = preview_fades_chk.isChecked()
                self.settings_store.setValue("preview_audio_fades", "true" if self.preview_audio_fades else "false")
            if fade_in_spin:
                self.settings_store.setValue("default_fade_in_duration", fade_in_spin.value())
            if fade_out_spin:
                self.settings_store.setValue("default_fade_out_duration", fade_out_spin.value())
            if fade_curve_combo:
                self.settings_store.setValue("default_fade_curve", fade_curve_combo.currentData() or "linear")
            if hasattr(self, "timeline") and hasattr(self.timeline, "canvas"):
                self.timeline.canvas.show_audio_fades = getattr(self, "enable_audio_fades", False)
                self.timeline.canvas.update()
            if hasattr(self, "story_list"):
                self.story_list.viewport().update()

            # Save Detection
            det_mode_combo = live_widgets.get("det_mode_combo")
            gap_spin = live_widgets.get("gap_spin")
            pad_spin = live_widgets.get("pad_spin")
            expected_speakers_combo = live_widgets.get("expected_speakers_combo")
            sensitivity_combo = live_widgets.get("sensitivity_combo")
            ask_speakers_chk = live_widgets.get("ask_speakers_chk")
            voice_profiles_chk = live_widgets.get("voice_profiles_chk")
            voice_match_thresh_spin = live_widgets.get("voice_match_thresh_spin")

            if det_mode_combo:
                self.story_detection_mode = str(det_mode_combo.currentData() or "voice")
                self.settings_store.setValue("story_detection_mode", self.story_detection_mode)
                if hasattr(self, "update_story_segment_terminology"):
                    self.update_story_segment_terminology()
            if gap_spin:
                self.silence_threshold = gap_spin.value()
                self.settings_store.setValue("silence_threshold", self.silence_threshold)
            if pad_spin:
                self.lead_in_padding = pad_spin.value()
                self.settings_store.setValue("lead_in_padding", self.lead_in_padding)
            if expected_speakers_combo:
                self.expected_speakers = str(expected_speakers_combo.currentData() or "auto")
                self.settings_store.setValue("default_expected_speakers", self.expected_speakers)
            if sensitivity_combo:
                self.diarization_sensitivity = str(sensitivity_combo.currentData() or "normal")
                self.settings_store.setValue("diarization_sensitivity", self.diarization_sensitivity)
            if ask_speakers_chk:
                self.settings_store.setValue("ask_expected_speakers", ask_speakers_chk.isChecked())
            if voice_profiles_chk:
                self.enable_voice_profiles = voice_profiles_chk.isChecked()
                self.settings_store.setValue("enable_voice_profiles", "true" if self.enable_voice_profiles else "false")
            if voice_match_thresh_spin:
                self.voice_profile_auto_match_threshold = voice_match_thresh_spin.value() / 100.0
                self.settings_store.setValue("voice_profile_auto_match_threshold", voice_match_thresh_spin.value())

            # Save Batch Processing
            batch_dir_edit = live_widgets.get("batch_dir_edit")
            if batch_dir_edit:
                self.settings_store.setValue("batch_custom_output_dir", batch_dir_edit.text().strip())
            for chk_key in [
                "batch_transcribe_chk", "batch_diarize_chk", "batch_stories_chk", "batch_translate_chk",
                "batch_save_proj_chk", "batch_skip_exist_chk", "batch_proj_only_chk", "batch_txt_chk",
                "batch_docx_chk", "batch_srt_chk", "batch_vtt_chk", "batch_spk_chk", "batch_time_chk"
            ]:
                widget = live_widgets.get(chk_key)
                if widget:
                    pref_name = {
                        "batch_transcribe_chk": "batch_opt_proc_transcribe",
                        "batch_diarize_chk": "batch_opt_proc_diarize",
                        "batch_stories_chk": "batch_opt_proc_stories",
                        "batch_translate_chk": "batch_opt_proc_translate",
                        "batch_save_proj_chk": "batch_opt_save_project",
                        "batch_skip_exist_chk": "batch_opt_skip_existing",
                        "batch_proj_only_chk": "batch_opt_save_project_only",
                        "batch_txt_chk": "batch_opt_fmt_txt",
                        "batch_docx_chk": "batch_opt_fmt_docx",
                        "batch_srt_chk": "batch_opt_fmt_srt",
                        "batch_vtt_chk": "batch_opt_fmt_vtt",
                        "batch_spk_chk": "batch_opt_include_speakers",
                        "batch_time_chk": "batch_opt_include_times",
                    }[chk_key]
                    self.settings_store.setValue(pref_name, widget.isChecked())

            # Save GPU Acceleration
            global_gpu_chk = live_widgets.get("global_gpu_chk")
            gpu_trans_chk = live_widgets.get("gpu_trans_chk")
            gpu_translate_chk = live_widgets.get("gpu_translate_chk")
            gpu_diarize_chk = live_widgets.get("gpu_diarize_chk")
            if global_gpu_chk:
                self.settings_store.setValue("gpu_acceleration_enabled", "true" if global_gpu_chk.isChecked() else "false")
            if gpu_trans_chk:
                self.settings_store.setValue("gpu_transcription_enabled", "true" if gpu_trans_chk.isChecked() else "false")
            if gpu_translate_chk:
                self.settings_store.setValue("gpu_translation_enabled", "true" if gpu_translate_chk.isChecked() else "false")
            if gpu_diarize_chk:
                self.settings_store.setValue("gpu_diarization_enabled", "true" if gpu_diarize_chk.isChecked() else "false")

            # Save WordPress preferences if plugin page was loaded and active
            if show_wp and page_wp and hasattr(page_wp, "save_preferences"):
                page_wp.save_preferences(dialog)

            # Save Google Docs preferences if plugin page was loaded and active
            if show_gd and page_gd and hasattr(page_gd, "save_preferences"):
                page_gd.save_preferences(dialog)
            elif show_gd and hasattr(self, "plugin_manager") and self.plugin_manager:
                gd_plugin = self.plugin_manager.plugins.get("gdocs")
                if gd_plugin and hasattr(gd_plugin, "save_preferences") and page_gd:
                    gd_plugin.save_preferences(page_gd)

            # Save YouTube preferences
            if show_yt:
                try:
                    yt_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
                    yt_cat_combo = live_widgets.get("yt_cat_combo")
                    yt_priv_combo = live_widgets.get("yt_priv_combo")
                    yt_tags_input = live_widgets.get("yt_tags_input")
                    yt_cb_copy_input = live_widgets.get("yt_cb_copy_input")
                    yt_cb_browser_input = live_widgets.get("yt_cb_browser_input")
                    yt_cb_subs_input = live_widgets.get("yt_cb_subs_input")
                    yt_cb_folder_input = live_widgets.get("yt_cb_folder_input")

                    if yt_cat_combo and yt_cat_combo.currentData():
                        yt_settings.setValue("export_yt_category", yt_cat_combo.currentData())
                    if yt_priv_combo and yt_priv_combo.currentData():
                        yt_settings.setValue("export_yt_privacy", yt_priv_combo.currentData())
                    if yt_tags_input:
                        yt_settings.setValue("export_yt_tags", yt_tags_input.text().strip())
                    if yt_cb_copy_input:
                        yt_settings.setValue("export_yt_copy_clipboard", yt_cb_copy_input.isChecked())
                    if yt_cb_browser_input:
                        yt_settings.setValue("export_yt_open_browser", yt_cb_browser_input.isChecked())
                    if yt_cb_subs_input:
                        yt_settings.setValue("export_yt_subtitles", yt_cb_subs_input.isChecked())
                    if yt_cb_folder_input:
                        yt_settings.setValue("export_yt_open_folder", yt_cb_folder_input.isChecked())
                    yt_settings.sync()
                except Exception as exc:
                    logger.warning(f"Failed to save YouTube settings: {exc}")

            try:
                self.settings_store.sync()
            except Exception:
                pass

            self.log_activity("[SETTINGS] Preferences updated.")
            if close_dialog:
                dialog.accept()

        btn_box.accepted.connect(lambda: _save_preferences(close_dialog=True))
        btn_box.rejected.connect(dialog.reject)
        apply_btn.clicked.connect(lambda: _save_preferences(close_dialog=False))

        dialog.exec()

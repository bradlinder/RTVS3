"""Radio & TV Story Segmenter — Preferences Modal Core Tab Builders.

Constructs core configuration tabs:
General, Keyboard Shortcuts, Audio Hardware, Software Updates & GitHub, AI Models & Storage,
and optional NVIDIA CUDA GPU Acceleration.
"""

import logging
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QSlider, QMessageBox
)

from prs_shared import (
    DEFAULT_GITHUB_REPO, PROJECT_VERSION,
    get_models_storage_dir, set_models_storage_dir, get_update_channel,
    get_github_repo
)

logger = logging.getLogger(__name__)


def build_general_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_general = QWidget()
    gen_layout = QVBoxLayout(page_general)
    gen_form = QFormLayout()

    theme_combo = QComboBox()
    theme_combo.addItems(["dark", "light", "high_contrast"])
    curr_theme = str(win.settings_store.value("theme_mode", "dark") or "dark")
    idx = theme_combo.findText(curr_theme)
    if idx >= 0:
        theme_combo.setCurrentIndex(idx)
    gen_form.addRow("Theme Mode:", theme_combo)
    live_widgets["theme_combo"] = theme_combo

    lang_combo = QComboBox()
    lang_combo.addItem("English", "en")
    lang_combo.addItem("Español (Spanish)", "es")
    curr_lang = getattr(win, "language", "en") or "en"
    idx = lang_combo.findData(curr_lang)
    if idx >= 0:
        lang_combo.setCurrentIndex(idx)
    else:
        lang_combo.setCurrentIndex(0)
    gen_form.addRow("UI Language / Idioma:", lang_combo)
    live_widgets["lang_combo"] = lang_combo

    startup_combo = QComboBox()
    startup_combo.addItem("Open last project", "last")
    startup_combo.addItem("Start new project", "new")
    startup_combo.addItem("Ask me", "prompt")
    curr_startup = getattr(
        win, "startup_project_mode",
        str(win.settings_store.value("startup_project_mode", "last") or "last")
    )
    idx = startup_combo.findData(curr_startup)
    startup_combo.setCurrentIndex(idx if idx >= 0 else 0)
    gen_form.addRow("Startup Project:", startup_combo)
    live_widgets["startup_combo"] = startup_combo

    # Project Directory & Organization Settings
    proj_dir_edit = QLineEdit(str(win.settings_store.value("default_project_directory", "") or ""))
    proj_dir_btn = QPushButton("Browse…")
    def _browse_proj_dir():
        chosen = QFileDialog.getExistingDirectory(dialog, "Select Default Projects Directory", proj_dir_edit.text() or str(Path.home()))
        if chosen:
            proj_dir_edit.setText(chosen)
    proj_dir_btn.clicked.connect(_browse_proj_dir)

    p_dir_layout = QHBoxLayout()
    p_dir_layout.addWidget(proj_dir_edit)
    p_dir_layout.addWidget(proj_dir_btn)
    gen_form.addRow("Default Projects Folder:", p_dir_layout)
    live_widgets["proj_dir_edit"] = proj_dir_edit

    save_with_media_chk = QCheckBox("Save projects in the same folder as original media file")
    save_with_media_chk.setChecked(str(win.settings_store.value("save_project_with_media", "false")).lower() in {"1", "true", "yes"})
    gen_form.addRow("", save_with_media_chk)
    live_widgets["save_with_media_chk"] = save_with_media_chk

    bundle_folder_chk = QCheckBox("Create dedicated project bundle with subfolders for exports and media")
    bundle_folder_chk.setToolTip("Creates [ProjectName]/ containing .rtvs project, with media/, exports/audio/, exports/transcripts/, and hidden .cache/ subfolders.")
    bundle_folder_chk.setChecked(str(win.settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"})
    gen_form.addRow("", bundle_folder_chk)
    live_widgets["bundle_folder_chk"] = bundle_folder_chk

    ingest_mode_combo = QComboBox()
    ingest_mode_combo.addItem("Reference in place (Save disk space / default)", "reference")
    ingest_mode_combo.addItem("Copy source media to project bundle (Portable)", "copy")
    ingest_mode_combo.addItem("Prompt every time when saving project", "ask")
    current_ingest_mode = str(win.settings_store.value("media_ingest_mode", "")).strip().lower()
    if not current_ingest_mode:
        was_copy = str(win.settings_store.value("copy_media_to_project_folder", "false")).lower() in {"1", "true", "yes"}
        current_ingest_mode = "copy" if was_copy else "reference"
    idx = ingest_mode_combo.findData(current_ingest_mode)
    ingest_mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
    gen_form.addRow("Media Ingest Mode:", ingest_mode_combo)
    live_widgets["ingest_mode_combo"] = ingest_mode_combo

    single_instance_combo = QComboBox()
    single_instance_combo.addItem("Open files in existing app instance (Single Instance)", "single")
    single_instance_combo.addItem("Allow multiple independent app instances", "multi")
    curr_single_inst = str(win.settings_store.value("single_instance_mode", "single")).strip().lower()
    idx_si = single_instance_combo.findData(curr_single_inst)
    single_instance_combo.setCurrentIndex(idx_si if idx_si >= 0 else 0)
    gen_form.addRow("Instance Handling Mode:", single_instance_combo)
    live_widgets["single_instance_combo"] = single_instance_combo

    floating_toolbar_chk = QCheckBox("Show floating quick-action toolbar on text selection in transcript")
    floating_toolbar_chk.setToolTip("Controls visibility of the floating popup toolbar (Play, Story, Comment, Exclude, Export) that appears when text is selected in the transcript.")
    curr_floating = str(getattr(win, "show_floating_selection_toolbar", win.settings_store.value("show_floating_selection_toolbar", "true"))).lower() in {"1", "true", "yes"}
    floating_toolbar_chk.setChecked(curr_floating)
    gen_form.addRow("Selection Popup:", floating_toolbar_chk)
    live_widgets["floating_toolbar_chk"] = floating_toolbar_chk

    open_comments_chk = QCheckBox("Open Comments sidebar on startup")
    open_comments_chk.setToolTip("When unchecked (default), the Comments sidebar remains closed at startup until opened explicitly.")
    open_comments_chk.setChecked(str(win.settings_store.value("open_comments_on_launch", "false")).lower() in {"1", "true", "yes"})
    gen_form.addRow("Comments Sidebar:", open_comments_chk)
    live_widgets["open_comments_chk"] = open_comments_chk

    show_highlights_chk = QCheckBox("Show Comment highlights in transcript")
    show_highlights_chk.setToolTip("When checked (default), amber/yellow highlights mark commented text in the transcript.")
    show_highlights_chk.setChecked(str(win.settings_store.value("show_comment_highlights", "true")).lower() in {"1", "true", "yes"})
    live_widgets["show_highlights_chk"] = show_highlights_chk

    show_speaker_chk = QCheckBox("Show speaker labels in transcript viewer")
    show_speaker_chk.setToolTip("Displays speaker turn headers (e.g. SPEAKER_01:) in the transcript window.")
    show_speaker_chk.setChecked(str(win.settings_store.value("show_speaker_labels", "true")).lower() in {"1", "true", "yes"})
    gen_form.addRow("Speaker Labels:", show_speaker_chk)
    live_widgets["show_speaker_chk"] = show_speaker_chk

    colorize_speakers_chk = QCheckBox("Colorize speaker labels in transcript")
    colorize_speakers_chk.setToolTip("Applies distinct, theme-adaptive colors to each speaker label for quick visual scanning.")
    colorize_speakers_chk.setChecked(str(win.settings_store.value("colorize_speaker_labels", "true")).lower() in {"1", "true", "yes"})
    colorize_speakers_chk.setEnabled(show_speaker_chk.isChecked())
    show_speaker_chk.toggled.connect(lambda checked: colorize_speakers_chk.setEnabled(checked))
    gen_form.addRow("Colorize Speakers:", colorize_speakers_chk)
    live_widgets["colorize_speakers_chk"] = colorize_speakers_chk

    show_timestamps_chk = QCheckBox("Show timestamps in transcript viewer")
    show_timestamps_chk.setToolTip("Displays timecodes at speaker turns in the transcript window.")
    show_timestamps_chk.setChecked(str(win.settings_store.value("show_timestamps", "true")).lower() in {"1", "true", "yes"})
    gen_form.addRow("Timestamps:", show_timestamps_chk)
    live_widgets["show_timestamps_chk"] = show_timestamps_chk

    show_millis_chk = QCheckBox("Show milliseconds in timestamps (MM:SS.mmm)")
    show_millis_chk.setToolTip("When unchecked (default), displays clean human-readable timestamps (MM:SS) in transcript viewer and text exports. Subtitle/DAW exports always retain millisecond precision.")
    show_millis_chk.setChecked(str(win.settings_store.value("show_milliseconds", "false")).lower() in {"1", "true", "yes"})
    show_millis_chk.setEnabled(show_timestamps_chk.isChecked())
    show_timestamps_chk.toggled.connect(lambda checked: show_millis_chk.setEnabled(checked))
    gen_form.addRow("Timecode Precision:", show_millis_chk)
    live_widgets["show_millis_chk"] = show_millis_chk

    min_words_spin = QSpinBox()
    min_words_spin.setRange(20, 250)
    min_words_spin.setValue(int(getattr(win, "min_words_per_paragraph", 65) or 65))
    min_words_spin.setSuffix(" words")
    min_words_spin.setToolTip("Target minimum word count before starting a new paragraph at a natural sentence boundary within the same speaker turn. (Default: 65 words).")
    gen_form.addRow("Paragraph Length:", min_words_spin)
    live_widgets["min_words_spin"] = min_words_spin

    font_scale_spin = QSpinBox()
    font_scale_spin.setRange(80, 180)
    font_scale_spin.setSingleStep(5)
    curr_scale = int(round(float(getattr(win, "transcript_font_scale", 1.0) or 1.0) * 100))
    font_scale_spin.setValue(curr_scale)
    font_scale_spin.setSuffix("%")
    font_scale_spin.setToolTip("Scale transcript display font size (80% to 180%).")
    gen_form.addRow("Transcript Font Scale:", font_scale_spin)
    live_widgets["font_scale_spin"] = font_scale_spin

    autosave_spin = QSpinBox()
    autosave_spin.setRange(0, 120)
    autosave_spin.setValue(getattr(win, "auto_save_minutes", 5))
    autosave_spin.setSuffix(" min (0 = off)")
    gen_form.addRow("Auto-save Interval:", autosave_spin)
    live_widgets["autosave_spin"] = autosave_spin

    gen_layout.addLayout(gen_form)
    add_custom_defaults_btn(gen_layout, "General", ["general_appearance", "general_project_dirs", "general_autosave"])
    gen_layout.addStretch()
    return page_general


def build_shortcuts_tab(win, dialog, live_widgets) -> QWidget:
    if not hasattr(win, "shortcuts_manager") or not win.shortcuts_manager:
        from shortcuts_manager import ShortcutsManager
        win.shortcuts_manager = ShortcutsManager(getattr(win, "settings_store", None))

    from shortcuts_manager import KeyboardShortcutsPage
    page_shortcuts = KeyboardShortcutsPage(win.shortcuts_manager, parent_window=win)
    live_widgets["page_shortcuts"] = page_shortcuts
    return page_shortcuts


def build_audio_hardware_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_audio = QWidget()
    audio_layout = QVBoxLayout(page_audio)
    audio_form = QFormLayout()

    audio_dev_combo = QComboBox()
    audio_dev_combo.addItem("System Default")
    try:
        from PySide6.QtMultimedia import QMediaDevices
        for dev in QMediaDevices.audioOutputs():
            d_name = dev.description()
            if d_name and audio_dev_combo.findText(d_name) < 0:
                audio_dev_combo.addItem(d_name)
    except Exception as dev_err:
        logger.warning(f"Could not enumerate audio devices: {dev_err}")

    saved_dev = str(win.settings_store.value("audio_output_device", "System Default") or "System Default")
    found_dev_idx = audio_dev_combo.findText(saved_dev)
    audio_dev_combo.setCurrentIndex(found_dev_idx if found_dev_idx >= 0 else 0)
    audio_form.addRow("Audio Output Device:", audio_dev_combo)
    live_widgets["audio_dev_combo"] = audio_dev_combo

    vol_layout = QHBoxLayout()
    vol_slider = QSlider(Qt.Orientation.Horizontal)
    vol_slider.setRange(0, 100)
    curr_vol = int(float(win.settings_store.value("audio_output_volume", 100) or 100))
    vol_slider.setValue(curr_vol)
    vol_label = QLabel(f"{curr_vol}%")
    vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
    vol_layout.addWidget(vol_slider, 1)
    vol_layout.addWidget(vol_label)
    audio_form.addRow("Default Output Volume:", vol_layout)
    live_widgets["vol_slider"] = vol_slider

    def _test_audio_device():
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            try:
                from PySide6.QtWidgets import QApplication
                QApplication.beep()
            except Exception:
                pass

    test_btn = QPushButton("Test Audio Output")
    test_btn.clicked.connect(_test_audio_device)
    audio_form.addRow("Device Test:", test_btn)

    audio_layout.addLayout(audio_form)

    # --- Audio Loudness Normalization & Auto-Boost Group ---
    norm_group = QGroupBox("Audio Loudness Normalization & Auto-Boost")
    norm_layout = QVBoxLayout(norm_group)
    norm_form = QFormLayout()

    auto_norm_chk = QCheckBox("Automatically boost quiet audio on import for transcription & speaker detection")
    curr_auto_norm = str(win.settings_store.value("auto_loudness_normalization", "true")).lower() in {"1", "true", "yes"}
    auto_norm_chk.setChecked(curr_auto_norm)
    norm_form.addRow("Auto-Boost on Import:", auto_norm_chk)
    live_widgets["auto_norm_chk"] = auto_norm_chk

    target_standard_combo = QComboBox()
    standards_data = [
        ("Broadcast Standard (-16.0 LUFS / -1.5 dBTP)", "broadcast", -16.0, -1.5, -24.0, -6.0),
        ("Podcast / Web Standard (-14.0 LUFS / -1.0 dBTP)", "podcast", -14.0, -1.0, -20.0, -5.0),
        ("EBU R128 Television Standard (-24.0 LUFS / -1.0 dBTP)", "ebur128", -24.0, -1.0, -30.0, -6.0),
        ("Peak Normalization (-3.0 dBFS)", "peak", -18.0, -3.0, -24.0, -6.0),
    ]
    for label, code, t_lufs, t_tp, q_lufs, q_tp in standards_data:
        target_standard_combo.addItem(label, {"code": code, "target_lufs": t_lufs, "max_true_peak": t_tp, "quiet_lufs": q_lufs, "quiet_dbfs": q_tp})

    saved_std = str(win.settings_store.value("target_standard", "broadcast") or "broadcast").lower()
    sel_idx = 0
    for idx in range(target_standard_combo.count()):
        d = target_standard_combo.itemData(idx)
        if d and d.get("code") == saved_std:
            sel_idx = idx
            break
    target_standard_combo.setCurrentIndex(sel_idx)
    norm_form.addRow("Target Standard:", target_standard_combo)
    live_widgets["target_standard_combo"] = target_standard_combo

    target_lufs_spin = QDoubleSpinBox()
    target_lufs_spin.setRange(-36.0, -10.0)
    target_lufs_spin.setSingleStep(0.5)
    target_lufs_spin.setDecimals(1)
    target_lufs_spin.setSuffix(" LUFS")
    target_lufs_spin.setValue(float(win.settings_store.value("target_lufs", -16.0) or -16.0))
    norm_form.addRow("Target Integrated Loudness:", target_lufs_spin)
    live_widgets["target_lufs_spin"] = target_lufs_spin

    max_true_peak_spin = QDoubleSpinBox()
    max_true_peak_spin.setRange(-12.0, 0.0)
    max_true_peak_spin.setSingleStep(0.5)
    max_true_peak_spin.setDecimals(1)
    max_true_peak_spin.setSuffix(" dBTP")
    max_true_peak_spin.setValue(float(win.settings_store.value("max_true_peak", -1.5) or -1.5))
    norm_form.addRow("Maximum True Peak:", max_true_peak_spin)
    live_widgets["max_true_peak_spin"] = max_true_peak_spin

    quiet_lufs_spin = QDoubleSpinBox()
    quiet_lufs_spin.setRange(-36.0, -14.0)
    quiet_lufs_spin.setSingleStep(0.5)
    quiet_lufs_spin.setDecimals(1)
    quiet_lufs_spin.setSuffix(" LUFS")
    quiet_lufs_spin.setValue(float(win.settings_store.value("quiet_threshold_lufs", -24.0) or -24.0))
    quiet_lufs_spin.setToolTip("Audio quieter than this threshold triggers automatic normalization.")
    norm_form.addRow("Quiet LUFS Threshold:", quiet_lufs_spin)
    live_widgets["quiet_threshold_lufs_spin"] = quiet_lufs_spin

    quiet_dbfs_spin = QDoubleSpinBox()
    quiet_dbfs_spin.setRange(-18.0, -1.0)
    quiet_dbfs_spin.setSingleStep(0.5)
    quiet_dbfs_spin.setDecimals(1)
    quiet_dbfs_spin.setSuffix(" dBFS")
    quiet_dbfs_spin.setValue(float(win.settings_store.value("quiet_threshold_dbfs", -6.0) or -6.0))
    quiet_dbfs_spin.setToolTip("Audio with true-peak below this threshold triggers automatic normalization.")
    norm_form.addRow("Quiet Peak/dBFS Threshold:", quiet_dbfs_spin)
    live_widgets["quiet_threshold_dbfs_spin"] = quiet_dbfs_spin

    def _on_standard_changed(index):
        data = target_standard_combo.itemData(index)
        if data:
            target_lufs_spin.setValue(data["target_lufs"])
            max_true_peak_spin.setValue(data["max_true_peak"])
            quiet_lufs_spin.setValue(data["quiet_lufs"])
            quiet_dbfs_spin.setValue(data["quiet_dbfs"])

    target_standard_combo.currentIndexChanged.connect(_on_standard_changed)

    apply_boost_playback_chk = QCheckBox("Apply loudness boost to in-app playback and exported audio clips")
    apply_boost_playback_chk.setToolTip("When enabled, applies the calculated loudness gain during playback and exported story clips. Default is disabled to preserve original broadcast dynamics unless requested.")
    curr_boost_play = str(win.settings_store.value("apply_boost_playback", "false")).lower() in {"1", "true", "yes"}
    apply_boost_playback_chk.setChecked(curr_boost_play)
    norm_form.addRow("Playback & Export Boost:", apply_boost_playback_chk)
    live_widgets["apply_boost_playback_chk"] = apply_boost_playback_chk

    norm_layout.addLayout(norm_form)
    audio_layout.addWidget(norm_group)

    add_custom_defaults_btn(audio_layout, "Audio Settings", ["audio_hardware", "audio_normalization"])
    audio_layout.addStretch()
    return page_audio


def build_updates_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_updates = QWidget()
    up_layout = QVBoxLayout(page_updates)
    up_form = QFormLayout()

    auto_update_chk = QCheckBox("Automatically check for new releases on startup")
    curr_auto = str(win.settings_store.value("auto_check_updates", "true")).lower() in {"1", "true", "yes"}
    auto_update_chk.setChecked(curr_auto)
    up_form.addRow("Auto-Check:", auto_update_chk)
    live_widgets["auto_update_chk"] = auto_update_chk

    update_channel_combo = QComboBox()
    update_channel_combo.addItem("Stable Releases Only (Recommended)", "stable")
    update_channel_combo.addItem("Stable & Beta Releases", "beta")
    curr_chan = get_update_channel()
    update_channel_combo.setCurrentIndex(1 if curr_chan == "beta" else 0)
    up_form.addRow("Update Channel:", update_channel_combo)
    live_widgets["update_channel_combo"] = update_channel_combo

    repo_edit = QLineEdit(get_github_repo())
    repo_edit.setPlaceholderText("owner/repository")
    up_form.addRow("GitHub Repository:", repo_edit)
    live_widgets["repo_edit"] = repo_edit

    up_layout.addLayout(up_form)

    check_now_btn = QPushButton("Check for Updates Now…")
    check_now_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 14px; }")
    check_now_btn.clicked.connect(lambda: win.check_for_updates(interactive=True))
    up_layout.addWidget(check_now_btn)

    up_info = QLabel(
        f"Current application version: <b>v{PROJECT_VERSION}</b><br>"
        "Releases are published automatically via GitHub Actions CI/CD workflows."
    )
    up_info.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
    up_layout.addWidget(up_info)
    add_custom_defaults_btn(up_layout, "Updates & GitHub", ["software_updates"])
    up_layout.addStretch()
    return page_updates


def build_ai_models_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_models = QWidget()
    mod_layout = QVBoxLayout(page_models)
    mod_form = QFormLayout()

    curr_model_dir = str(get_models_storage_dir())
    model_dir_edit = QLineEdit(curr_model_dir)
    model_dir_btn = QPushButton("Browse…")
    def _browse_model_dir():
        chosen = QFileDialog.getExistingDirectory(dialog, "Select AI Models Storage Directory", model_dir_edit.text())
        if chosen:
            model_dir_edit.setText(chosen)
    model_dir_btn.clicked.connect(_browse_model_dir)

    m_dir_layout = QHBoxLayout()
    m_dir_layout.addWidget(model_dir_edit)
    m_dir_layout.addWidget(model_dir_btn)
    mod_form.addRow("Model Storage Directory:", m_dir_layout)
    live_widgets["model_dir_edit"] = model_dir_edit

    pref_whisper_combo = QComboBox()
    whisper_models = [
        ("parakeet-onnx", "Parakeet ONNX Fast TDT (English)"),
        ("fastconformer-es-onnx", "Spanish FastConformer (Spanish)"),
        ("fastconformer-multilingual-onnx", "Multilingual FastConformer (English & Spanish)"),
        ("tiny", "Whisper Tiny"),
        ("base", "Whisper Base"),
        ("small", "Whisper Small"),
        ("medium", "Whisper Medium"),
        ("large-v3", "Whisper Large v3"),
    ]
    for m_id, label in whisper_models:
        installed = win.is_whisper_model_available(m_id) if hasattr(win, "is_whisper_model_available") else False
        display = f"{label} ✓" if installed else label
        pref_whisper_combo.addItem(display, m_id)

    curr_whisper = getattr(win, "whisper_model", "parakeet-onnx")
    w_idx = pref_whisper_combo.findData(curr_whisper)
    if w_idx >= 0:
        pref_whisper_combo.setCurrentIndex(w_idx)
    mod_form.addRow("Transcription Model:", pref_whisper_combo)
    live_widgets["pref_whisper_combo"] = pref_whisper_combo

    pref_auto_lang_chk = QCheckBox("Auto-detect non-English speech & fall back to Whisper Small for non-English audio")
    pref_auto_lang_chk.setToolTip("When Parakeet ONNX (English-only) is selected, inspects the initial audio. If non-English speech (such as Spanish) is detected, automatically switches to Whisper Small.")
    curr_auto_lang = str(win.settings_store.value("auto_detect_fallback_whisper", "true")).lower() == "true"
    pref_auto_lang_chk.setChecked(curr_auto_lang)
    mod_form.addRow("Language Detection:", pref_auto_lang_chk)
    live_widgets["pref_auto_lang_chk"] = pref_auto_lang_chk

    pref_beam_combo = QComboBox()
    pref_beam_combo.addItem("High-Speed Greedy Decoding (beam_size=1, up to 2x faster)", 1)
    pref_beam_combo.addItem("Standard Quality Decoding (beam_size=5, default)", 5)
    curr_beam = int(win.settings_store.value("whisper_beam_size", getattr(win, "whisper_beam_size", 5)) or 5)
    beam_idx = pref_beam_combo.findData(curr_beam)
    pref_beam_combo.setCurrentIndex(beam_idx if beam_idx >= 0 else 1)
    pref_beam_label = QLabel("Transcription Speed / Quality:")
    mod_form.addRow(pref_beam_label, pref_beam_combo)
    live_widgets["pref_beam_combo"] = pref_beam_combo

    def _update_beam_visibility():
        selected_model = str(pref_whisper_combo.currentData() or "").lower()
        is_whisper = selected_model != "parakeet-onnx" and bool(selected_model)
        pref_beam_label.setVisible(is_whisper)
        pref_beam_combo.setVisible(is_whisper)

    pref_whisper_combo.currentIndexChanged.connect(_update_beam_visibility)
    _update_beam_visibility()

    pref_trans_combo = QComboBox()
    translation_installed = (
        hasattr(win, "plugin_manager") and win.plugin_manager and
        win.plugin_manager.is_plugin_installed("translation") and
        win.plugin_manager.is_plugin_enabled("translation")
    )
    if translation_installed:
        trans_variants = [
            ("tiny", "OPUS-MT-tiny"),
            ("standard", "OPUS-MT (Standard)")
        ]
        try:
            from plugins.translation.support import model_is_installed as _trans_model_is_installed
        except Exception:
            def _trans_model_is_installed(f, t, v):
                from translation import _translation_worker_class
                w_cls = _translation_worker_class(win) if callable(_translation_worker_class) else None
                if w_cls and hasattr(w_cls, "model_is_installed"):
                    return w_cls.model_is_installed(f, t, v)
                return False

        for v_id, label in trans_variants:
            try:
                installed_en_es = _trans_model_is_installed("en", "es", v_id)
                installed_es_en = _trans_model_is_installed("es", "en", v_id)
            except Exception:
                installed_en_es, installed_es_en = False, False
            installed = installed_en_es and installed_es_en
            display = f"{label} ✓" if installed else label
            pref_trans_combo.addItem(display, v_id)
        curr_trans = getattr(win, "translation_model_variant", "tiny")
        t_idx = pref_trans_combo.findData(curr_trans)
        if t_idx >= 0:
            pref_trans_combo.setCurrentIndex(t_idx)
        mod_form.addRow("Default Translation Model:", pref_trans_combo)
        live_widgets["pref_trans_combo"] = pref_trans_combo
    else:
        unavailable = QLabel("Translation plugin is not installed.")
        unavailable.setStyleSheet("color: #888;")
        mod_form.addRow("Translation Model:", unavailable)

    mod_layout.addLayout(mod_form)

    manage_models_btn = QPushButton("Open Model Manager (Download / Remove Models)…")
    manage_models_btn.setToolTip("View exact disk sizes, pre-download, or delete local models.")
    def _open_mgr():
        dialog.accept()
        if hasattr(win, "open_model_cleanup_dialog"):
            win.open_model_cleanup_dialog()
    manage_models_btn.clicked.connect(_open_mgr)
    mod_layout.addWidget(manage_models_btn)

    add_custom_defaults_btn(mod_layout, "AI Models", ["ai_models"])
    mod_layout.addStretch()
    return page_models


def build_gpu_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_gpu = QWidget()
    gpu_layout = QVBoxLayout(page_gpu)
    gpu_layout.setSpacing(10)

    gpu_desc = QLabel(
        "<b>Optional NVIDIA CUDA GPU Acceleration</b><br>"
        "<span style='color: #64748b; font-size: 12px;'>"
        "By default, all processing runs on the CPU to keep installer size small and maximize portability. "
        "If you have an NVIDIA graphics card, you can enable 100% optional GPU acceleration below. "
        "When disabled or uninstalled, it consumes <b>0 MB</b> of disk space.</span>"
    )
    gpu_desc.setWordWrap(True)
    gpu_layout.addWidget(gpu_desc)

    from runtime_manager import detect_nvidia_gpu, RuntimeManager
    has_nvidia = detect_nvidia_gpu()
    rm = RuntimeManager()
    gpu_installed = False
    try:
        gpu_installed = rm.is_env_up_to_date("gpu_transcribe")
    except Exception:
        gpu_installed = False

    status_box = QGroupBox("Hardware & Runtime Status")
    status_form = QFormLayout(status_box)

    hw_label = QLabel("NVIDIA GPU detected on system" if has_nvidia else "No NVIDIA GPU detected (CPU mode only)")
    hw_label.setStyleSheet("color: #15803d; font-weight: bold;" if has_nvidia else "color: #b45309;")
    status_form.addRow("Hardware:", hw_label)

    rt_label = QLabel("Installed (CUDA Ready)" if gpu_installed else "Not Installed (0 MB disk footprint)")
    rt_label.setStyleSheet("color: #15803d; font-weight: bold;" if gpu_installed else "color: #64748b;")
    status_form.addRow("Runtime:", rt_label)
    gpu_layout.addWidget(status_box)

    feat_group = QGroupBox("Accelerated Workflows")
    feat_layout = QVBoxLayout(feat_group)

    global_gpu_chk = QCheckBox("Enable GPU Acceleration (Master Switch)")
    curr_global_gpu = str(win.settings_store.value("gpu_acceleration_enabled", "false")).lower() in {"1", "true", "yes"}
    global_gpu_chk.setChecked(curr_global_gpu)
    global_gpu_chk.setEnabled(has_nvidia and gpu_installed)
    feat_layout.addWidget(global_gpu_chk)
    live_widgets["global_gpu_chk"] = global_gpu_chk

    gpu_trans_chk = QCheckBox("Transcription ASR (Faster-Whisper on CUDA)")
    curr_trans = str(win.settings_store.value("gpu_transcription_enabled", "true")).lower() in {"1", "true", "yes"}
    gpu_trans_chk.setChecked(curr_trans)
    gpu_trans_chk.setEnabled(has_nvidia and gpu_installed)
    feat_layout.addWidget(gpu_trans_chk)
    live_widgets["gpu_trans_chk"] = gpu_trans_chk

    gpu_translate_chk = QCheckBox("Machine Translation (MarianMT / CTranslate2 on CUDA)")
    curr_translate = str(win.settings_store.value("gpu_translation_enabled", "true")).lower() in {"1", "true", "yes"}
    gpu_translate_chk.setChecked(curr_translate)
    gpu_translate_chk.setEnabled(has_nvidia and gpu_installed)
    feat_layout.addWidget(gpu_translate_chk)
    live_widgets["gpu_translate_chk"] = gpu_translate_chk

    gpu_diarize_chk = QCheckBox("Speaker Detection / Diarization (WeSpeaker on CUDA/ONNX-GPU)")
    curr_diarize = str(win.settings_store.value("gpu_diarization_enabled", "true")).lower() in {"1", "true", "yes"}
    gpu_diarize_chk.setChecked(curr_diarize)
    gpu_diarize_chk.setEnabled(has_nvidia and gpu_installed)
    feat_layout.addWidget(gpu_diarize_chk)
    live_widgets["gpu_diarize_chk"] = gpu_diarize_chk

    gpu_layout.addWidget(feat_group)

    action_layout = QHBoxLayout()
    install_gpu_btn = QPushButton("Download & Install GPU Runtime…" if not gpu_installed else "Update / Reinstall GPU Runtime…")
    install_gpu_btn.setEnabled(has_nvidia)
    def _on_install_gpu():
        dialog.accept()
        if hasattr(win, "_start_gpu_acceleration_install"):
            win._start_gpu_acceleration_install(dialog)
    install_gpu_btn.clicked.connect(_on_install_gpu)
    action_layout.addWidget(install_gpu_btn)

    uninstall_gpu_btn = QPushButton("Uninstall GPU Runtime (Reclaim Disk Space)")
    uninstall_gpu_btn.setEnabled(gpu_installed)
    def _on_uninstall_gpu():
        ans = QMessageBox.question(
            dialog, "Uninstall GPU Runtime",
            "Are you sure you want to remove the optional GPU acceleration environment?\n\n"
            "All workflows will automatically fall back to CPU execution, and ~1.5 GB of disk space will be reclaimed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                rm_inner = RuntimeManager()
                env_dir = rm_inner.get_env_dir("gpu_transcribe")
                shutil.rmtree(env_dir, ignore_errors=True)
            except Exception as exc:
                QMessageBox.warning(dialog, "Uninstall Notice", f"Error removing environment directory: {exc}")
            win.settings_store.setValue("gpu_acceleration_enabled", "false")
            win.settings_store.sync()
            QMessageBox.information(dialog, "GPU Runtime Removed", "GPU acceleration runtime has been removed and disk space reclaimed.")
            dialog.accept()
            win.open_preferences_dialog(initial_category="GPU Acceleration")
    uninstall_gpu_btn.clicked.connect(_on_uninstall_gpu)
    action_layout.addWidget(uninstall_gpu_btn)

    gpu_layout.addLayout(action_layout)
    add_custom_defaults_btn(gpu_layout, "GPU Acceleration", ["gpu_acceleration"])
    gpu_layout.addStretch()
    return page_gpu

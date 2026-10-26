"""Radio & TV Story Segmenter — Preferences Modal Tab Builders.

Constructs individual stacked category pages for the multi-category Preferences dialog:
General, Keyboard Shortcuts, Audio Hardware, Software Updates, AI Models, GPU Acceleration,
Playback & Timeline, Story Detection & Diarization, Batch Processing, Data Cleanup,
and dynamic Plugin tabs (WordPress, YouTube Studio, Google Docs).
"""

import logging
from pathlib import Path
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QSlider, QMessageBox
)

from prs_shared import (
    INTERNAL_APP_ID, DEFAULT_GITHUB_REPO, PROJECT_VERSION,
    get_models_storage_dir, set_models_storage_dir, get_update_channel,
    get_github_repo, FadeCurveVisualSelector
)
from preferences_reset import RestoreSelectedSettingsDialog

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
    gen_form.addRow("Transcript Highlights:", show_highlights_chk)
    live_widgets["show_highlights_chk"] = show_highlights_chk

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
    add_custom_defaults_btn(audio_layout, "Audio Settings", ["audio_hardware"])
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


def build_playback_timeline_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_play = QWidget()
    play_layout = QVBoxLayout(page_play)
    play_form = QFormLayout()

    skip_spin = QSpinBox()
    skip_spin.setRange(1, 300)
    skip_spin.setValue(getattr(win, "skip_seconds", 5))
    skip_spin.setSuffix(" sec")
    play_form.addRow("Arrow Key Skip Length:", skip_spin)
    live_widgets["skip_spin"] = skip_spin

    play_rate_combo = QComboBox()
    for r_lbl, r_val in [("0.75x", 0.75), ("1.0x (Normal)", 1.0), ("1.25x (Speed-Listen)", 1.25), ("1.5x (Fast)", 1.5), ("1.75x", 1.75), ("2.0x", 2.0)]:
        play_rate_combo.addItem(r_lbl, r_val)
    curr_rate = float(getattr(win, "playback_rate", 1.0) or 1.0)
    r_idx = play_rate_combo.findData(curr_rate)
    play_rate_combo.setCurrentIndex(r_idx if r_idx >= 0 else 1)
    play_form.addRow("Default Playback Speed:", play_rate_combo)
    live_widgets["play_rate_combo"] = play_rate_combo

    preroll_spin = QDoubleSpinBox()
    preroll_spin.setRange(0.0, 5.0)
    preroll_spin.setSingleStep(0.1)
    preroll_spin.setDecimals(1)
    preroll_spin.setValue(float(getattr(win, "speed_listening_preroll_seconds", 0.5) or 0.5))
    preroll_spin.setSuffix(" sec")
    preroll_spin.setToolTip("Pre-roll rewind jump applied when resuming playback with Tab in speed-listening proofreading mode.")
    play_form.addRow("Speed-Listening Tab Pre-Roll:", preroll_spin)
    live_widgets["preroll_spin"] = preroll_spin

    wave_chk = QCheckBox("Show audio waveform on timeline")
    wave_chk.setChecked(getattr(win, "timeline_show_waveform", True))
    play_form.addRow("Timeline Waveform:", wave_chk)
    live_widgets["wave_chk"] = wave_chk

    thumb_chk = QCheckBox("Show video thumbnails on timeline")
    thumb_chk.setChecked(getattr(win, "timeline_show_thumbnails", True))
    play_form.addRow("Timeline Thumbnails:", thumb_chk)
    live_widgets["thumb_chk"] = thumb_chk

    thumb_pos_combo = QComboBox()
    thumb_pos_combo.addItem("Below audio waveform", "below")
    thumb_pos_combo.addItem("Above audio waveform", "above")
    curr_thumb_pos = getattr(win, "timeline_thumbnail_position", str(win.settings_store.value("timeline_thumbnail_position", "below")).lower())
    pos_idx = thumb_pos_combo.findData(curr_thumb_pos)
    if pos_idx >= 0:
        thumb_pos_combo.setCurrentIndex(pos_idx)
    play_form.addRow("Thumbnail Placement:", thumb_pos_combo)
    live_widgets["thumb_pos_combo"] = thumb_pos_combo

    sel_mode_combo = QComboBox()
    sel_mode_combo.addItem("Clear previous selection (Single selection)", "replace")
    sel_mode_combo.addItem("Keep previous selections (Multi-selection: create separate stories)", "keep")
    curr_sel_mode = getattr(win, "transcript_selection_mode", str(win.settings_store.value("transcript_selection_mode", "replace") or "replace"))
    sel_idx = sel_mode_combo.findData(curr_sel_mode)
    sel_mode_combo.setCurrentIndex(sel_idx if sel_idx >= 0 else 0)
    play_form.addRow("New Text Selection Behavior:", sel_mode_combo)
    live_widgets["sel_mode_combo"] = sel_mode_combo

    enable_fades_chk = QCheckBox("Enable story audio fades and timeline envelope handles")
    enable_fades_chk.setToolTip("Enables tactile fade-in and fade-out handles on the timeline and applies fade ramps to exported stories. Disabling this turns off fade envelope rendering and export processing for maximum timeline responsiveness.")
    enable_fades_chk.setChecked(getattr(win, "enable_audio_fades", False))
    play_form.addRow("Audio Fades:", enable_fades_chk)
    live_widgets["enable_fades_chk"] = enable_fades_chk

    fades_sub_widget = QWidget()
    fades_sub_layout = QFormLayout(fades_sub_widget)
    fades_sub_layout.setContentsMargins(0, 0, 0, 0)

    preview_fades_chk = QCheckBox("Preview audio fades in real-time during playback")
    preview_fades_chk.setToolTip("Modulates preview audio playback volume in real-time when crossing story fade-in and fade-out envelopes.")
    preview_fades_chk.setChecked(getattr(win, "preview_audio_fades", False))
    fades_sub_layout.addRow("Fade Audio Preview:", preview_fades_chk)
    live_widgets["preview_fades_chk"] = preview_fades_chk

    fade_in_spin = QDoubleSpinBox()
    fade_in_spin.setRange(0.0, 10.0)
    fade_in_spin.setSingleStep(0.1)
    fade_in_spin.setDecimals(2)
    fade_in_spin.setValue(float(win.settings_store.value("default_fade_in_duration", 0.0)))
    fade_in_spin.setSuffix(" sec")
    fade_in_spin.setToolTip("Default audio fade-in duration automatically applied to newly created stories.")
    fades_sub_layout.addRow("Default Story Fade-In:", fade_in_spin)
    live_widgets["fade_in_spin"] = fade_in_spin

    fade_out_spin = QDoubleSpinBox()
    fade_out_spin.setRange(0.0, 10.0)
    fade_out_spin.setSingleStep(0.1)
    fade_out_spin.setDecimals(2)
    fade_out_spin.setValue(float(win.settings_store.value("default_fade_out_duration", 1.0)))
    fade_out_spin.setSuffix(" sec")
    fade_out_spin.setToolTip("Default audio fade-out duration automatically applied to newly created stories.")
    fades_sub_layout.addRow("Default Story Fade-Out:", fade_out_spin)
    live_widgets["fade_out_spin"] = fade_out_spin

    fade_curve_combo = FadeCurveVisualSelector(parent=fades_sub_widget)
    curr_def_curve = str(win.settings_store.value("default_fade_curve", "linear") or "linear")
    fade_curve_combo.setCurrentData(curr_def_curve)
    fade_curve_combo.setToolTip("Default volume envelope curve profile applied to audio fade transitions.")
    fades_sub_layout.addRow("Default Fade Curve:", fade_curve_combo)
    live_widgets["fade_curve_combo"] = fade_curve_combo

    play_form.addRow("", fades_sub_widget)

    def _update_fades_options_visibility(enabled):
        fades_sub_widget.setVisible(bool(enabled))

    enable_fades_chk.toggled.connect(_update_fades_options_visibility)
    _update_fades_options_visibility(enable_fades_chk.isChecked())

    play_layout.addLayout(play_form)
    add_custom_defaults_btn(play_layout, "Playback & Timeline", ["playback_timeline", "audio_fades"])
    play_layout.addStretch()
    return page_play


def build_detection_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_detect = QWidget()
    det_layout = QVBoxLayout(page_detect)
    det_form = QFormLayout()

    det_mode_combo = QComboBox()
    det_mode_combo.addItem("Voice / Speech (Standard Dialog Pauses)", "voice")
    det_mode_combo.addItem("Music / Songs (Music Programs & Song Breaks)", "music")
    curr_det_mode = str(getattr(win, "story_detection_mode", "voice") or "voice")
    idx = det_mode_combo.findData(curr_det_mode)
    det_mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
    det_mode_combo.setToolTip(
        "Detection Basis:\n"
        "• Voice Mode: Segments audio based on silences and pauses in spoken dialogue.\n"
        "• Music Mode: Designed for music programs. Detects songs; sets song boundaries when a track ends and there is silence, dialog only, or non-musical sounds for the threshold duration."
    )
    det_form.addRow("Detection Basis / Mode:", det_mode_combo)
    live_widgets["det_mode_combo"] = det_mode_combo

    gap_spin = QDoubleSpinBox()
    gap_spin.setRange(0.5, 30.0)
    gap_spin.setSingleStep(0.5)
    gap_spin.setValue(getattr(win, "silence_threshold", 3.0))
    gap_spin.setSuffix(" sec")
    det_form.addRow("Silence Gap Threshold:", gap_spin)
    live_widgets["gap_spin"] = gap_spin

    pad_spin = QDoubleSpinBox()
    pad_spin.setRange(0.0, 5.0)
    pad_spin.setSingleStep(0.1)
    pad_spin.setValue(getattr(win, "lead_in_padding", 0.5))
    pad_spin.setSuffix(" sec")
    det_form.addRow("Lead-In Padding:", pad_spin)
    live_widgets["pad_spin"] = pad_spin

    expected_speakers_combo = QComboBox()
    expected_speakers_combo.addItem("Auto-Detect", "auto")
    expected_speakers_combo.addItem("1 Speaker (Solo Fast-Path)", "1")
    expected_speakers_combo.addItem("2 Speakers (Interview)", "2")
    expected_speakers_combo.addItem("3+ Speakers (Panel / Group)", "3+")
    current_expected = str(getattr(win, "expected_speakers", "auto") or "auto")
    idx = expected_speakers_combo.findData(current_expected)
    expected_speakers_combo.setCurrentIndex(idx if idx >= 0 else 0)
    expected_speakers_combo.setToolTip(
        "Default number of speakers to expect for new Speaker Detection jobs.\n"
        "\"1 Speaker\" skips voice-embedding/clustering entirely for a large speedup on solo recordings."
    )
    det_form.addRow("Default Expected Speakers:", expected_speakers_combo)
    live_widgets["expected_speakers_combo"] = expected_speakers_combo

    ask_speakers_chk = QCheckBox("Ask for speaker estimate each time")
    ask_speakers_chk.setChecked(str(win.settings_store.value("ask_expected_speakers", "true")).lower() in {"1", "true", "yes"})
    ask_speakers_chk.setToolTip("When enabled, Detect Speakers asks for an estimated speaker count before each non-batch detection job. Batch jobs always use their selected setting without prompting.")
    det_form.addRow("Speaker Estimate Prompt:", ask_speakers_chk)
    live_widgets["ask_speakers_chk"] = ask_speakers_chk

    sensitivity_combo = QComboBox()
    sensitivity_combo.addItem("Low (Loose — Merges similar voices)", "low")
    sensitivity_combo.addItem("Normal (Balanced default)", "normal")
    sensitivity_combo.addItem("High (Strict — Keeps similar voices separate)", "high")
    sensitivity_combo.addItem("Very High (Aggressive — Maximum separation)", "very_high")
    sensitivity_combo.addItem("Ultra (Studio — Extreme strictness for near-identical voices)", "ultra")
    current_sens = str(win.settings_store.value("diarization_sensitivity", getattr(win, "diarization_sensitivity", "normal")) or "normal")
    idx_sens = sensitivity_combo.findData(current_sens)
    sensitivity_combo.setCurrentIndex(idx_sens if idx_sens >= 0 else 1)
    sensitivity_combo.setToolTip(
        "Controls acoustic separation sensitivity when auto-detecting speakers.\n"
        "• High / Very High / Ultra: Prevents distinct speakers with similar pitches from being merged into one label.\n"
        "• Low: Merges looser voice clusters to avoid splitting one speaker across multiple labels."
    )
    det_form.addRow("Speaker Separation Sensitivity:", sensitivity_combo)
    live_widgets["sensitivity_combo"] = sensitivity_combo

    sample_dur_spin = QDoubleSpinBox()
    sample_dur_spin.setRange(1.0, 15.0)
    sample_dur_spin.setSingleStep(0.5)
    sample_dur_spin.setValue(float(win.settings_store.value("speaker_sample_duration", 3.0) or 3.0))
    sample_dur_spin.setSuffix(" sec")
    sample_dur_spin.setToolTip("Duration in seconds to play when auditioning representative voice samples in the Speaker Manager.")
    det_form.addRow("Speaker Sample Preview Length:", sample_dur_spin)
    live_widgets["sample_dur_spin"] = sample_dur_spin

    voice_profiles_chk = QCheckBox("Enable persistent Voice Profiles library and cross-show matching")
    voice_profiles_chk.setChecked(str(win.settings_store.value("enable_voice_profiles", "true")).lower() in {"1", "true", "yes"})
    voice_profiles_chk.setToolTip("When enabled, RTVS automatically matches recurring speaker voices against the persistent station voice profiles library across recordings.")
    det_form.addRow("Voice Profiles:", voice_profiles_chk)
    live_widgets["voice_profiles_chk"] = voice_profiles_chk

    voice_match_thresh_spin = QSpinBox()
    voice_match_thresh_spin.setRange(50, 99)
    voice_match_thresh_spin.setValue(int(float(win.settings_store.value("voice_profile_auto_match_threshold", 78) or 78)))
    voice_match_thresh_spin.setSuffix("%")
    voice_match_thresh_spin.setToolTip("Minimum acoustic similarity score (75-85% optimal) required to automatically associate a detected speaker cluster with a known voice profile.")
    det_form.addRow("Voice Profile Auto-Match Threshold:", voice_match_thresh_spin)
    live_widgets["voice_match_thresh_spin"] = voice_match_thresh_spin

    det_layout.addLayout(det_form)
    add_custom_defaults_btn(det_layout, "Story Detection & Diarization", ["detection_diarization"])
    det_layout.addStretch()
    return page_detect


def build_batch_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_batch = QWidget()
    batch_layout = QVBoxLayout(page_batch)
    batch_form = QFormLayout()

    batch_dir_edit = QLineEdit(str(win.settings_store.value("batch_custom_output_dir", "") or ""))
    batch_dir_btn = QPushButton("Browse…")
    def _browse_batch_dir():
        chosen = QFileDialog.getExistingDirectory(dialog, "Select Default Batch Output Directory", batch_dir_edit.text() or str(Path.home()))
        if chosen:
            batch_dir_edit.setText(chosen)
    batch_dir_btn.clicked.connect(_browse_batch_dir)
    b_dir_layout = QHBoxLayout()
    b_dir_layout.addWidget(batch_dir_edit)
    b_dir_layout.addWidget(batch_dir_btn)
    batch_form.addRow("Default Output Folder:", b_dir_layout)
    live_widgets["batch_dir_edit"] = batch_dir_edit

    batch_transcribe_chk = QCheckBox("Transcribe audio with Whisper")
    batch_transcribe_chk.setChecked(str(win.settings_store.value("batch_opt_proc_transcribe", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Transcription:", batch_transcribe_chk)
    live_widgets["batch_transcribe_chk"] = batch_transcribe_chk

    batch_diarize_chk = QCheckBox("Detect Speakers")
    batch_diarize_chk.setChecked(str(win.settings_store.value("batch_opt_proc_diarize", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Detect Speakers:", batch_diarize_chk)
    live_widgets["batch_diarize_chk"] = batch_diarize_chk

    batch_stories_chk = QCheckBox("Auto-detect stories / segments")
    batch_stories_chk.setChecked(str(win.settings_store.value("batch_opt_proc_stories", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Stories:", batch_stories_chk)
    live_widgets["batch_stories_chk"] = batch_stories_chk

    batch_translate_chk = QCheckBox("Translate to Spanish")
    batch_translate_chk.setChecked(str(win.settings_store.value("batch_opt_proc_translate", "false")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Translation:", batch_translate_chk)
    live_widgets["batch_translate_chk"] = batch_translate_chk

    batch_save_proj_chk = QCheckBox("Auto-save project (.rtvs) files")
    batch_save_proj_chk.setChecked(str(win.settings_store.value("batch_opt_save_project", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Projects (.rtvs):", batch_save_proj_chk)
    live_widgets["batch_save_proj_chk"] = batch_save_proj_chk

    batch_skip_exist_chk = QCheckBox("Skip re-processing if project already exists")
    batch_skip_exist_chk.setChecked(str(win.settings_store.value("batch_opt_skip_existing", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Skip Existing:", batch_skip_exist_chk)
    live_widgets["batch_skip_exist_chk"] = batch_skip_exist_chk

    batch_proj_only_chk = QCheckBox("Save project file only (skip exporting media/text)")
    batch_proj_only_chk.setChecked(str(win.settings_store.value("batch_opt_save_project_only", "false")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Project Only:", batch_proj_only_chk)
    live_widgets["batch_proj_only_chk"] = batch_proj_only_chk

    fmt_layout = QHBoxLayout()
    batch_txt_chk = QCheckBox("TXT")
    batch_txt_chk.setChecked(str(win.settings_store.value("batch_opt_fmt_txt", "true")).lower() in {"1", "true", "yes"})
    batch_docx_chk = QCheckBox("Word (.docx)")
    batch_docx_chk.setChecked(str(win.settings_store.value("batch_opt_fmt_docx", "true")).lower() in {"1", "true", "yes"})
    batch_srt_chk = QCheckBox("SRT")
    batch_srt_chk.setChecked(str(win.settings_store.value("batch_opt_fmt_srt", "false")).lower() in {"1", "true", "yes"})
    batch_vtt_chk = QCheckBox("VTT")
    batch_vtt_chk.setChecked(str(win.settings_store.value("batch_opt_fmt_vtt", "false")).lower() in {"1", "true", "yes"})
    fmt_layout.addWidget(batch_txt_chk)
    fmt_layout.addWidget(batch_docx_chk)
    fmt_layout.addWidget(batch_srt_chk)
    fmt_layout.addWidget(batch_vtt_chk)
    batch_form.addRow("Default Export Formats:", fmt_layout)
    live_widgets["batch_txt_chk"] = batch_txt_chk
    live_widgets["batch_docx_chk"] = batch_docx_chk
    live_widgets["batch_srt_chk"] = batch_srt_chk
    live_widgets["batch_vtt_chk"] = batch_vtt_chk

    batch_spk_chk = QCheckBox("Include speaker names in exports")
    batch_spk_chk.setChecked(str(win.settings_store.value("batch_opt_include_speakers", "true")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Speaker Labels:", batch_spk_chk)
    live_widgets["batch_spk_chk"] = batch_spk_chk

    batch_time_chk = QCheckBox("Include timestamps in exports")
    batch_time_chk.setChecked(str(win.settings_store.value("batch_opt_include_times", "false")).lower() in {"1", "true", "yes"})
    batch_form.addRow("Timestamps:", batch_time_chk)
    live_widgets["batch_time_chk"] = batch_time_chk

    reorder_dest_btn = QPushButton("Customize Export Destinations Order…")
    reorder_dest_btn.setToolTip("Customize the default display order of destinations in the Export dialog (Local Files, WordPress, Google Docs, YouTube Studio).")
    def _on_reorder_dest_prefs():
        try:
            from export.dialog import ReorderExportDestinationsDialog
            dlg = ReorderExportDestinationsDialog(dialog)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(dialog, "Error", f"Failed to open Destination Ordering dialog:\n\n{exc}")
    reorder_dest_btn.clicked.connect(_on_reorder_dest_prefs)
    batch_form.addRow("Destinations Order:", reorder_dest_btn)

    batch_reset_btn = QPushButton("Reset Batch Add Files Location")
    batch_reset_btn.setToolTip("Forget the last directory used by Batch Processing > Add Files and return to the normal default location.")
    def _reset_batch_add_location():
        win.settings_store.remove("batch_add_files_directory")
        QMessageBox.information(dialog, "Batch Add Files Location", "The Batch Processing Add Files location has been reset to the default.")
    batch_reset_btn.clicked.connect(_reset_batch_add_location)
    batch_form.addRow("Add Files Location:", batch_reset_btn)

    batch_options_reset_btn = QPushButton("Reset Batch Options to Factory Defaults…")
    batch_options_reset_btn.setToolTip("Reset saved batch processing and export options back to factory defaults.")
    def _reset_batch_export_defaults():
        keys = [
            "batch_opt_pipeline_mode", "batch_opt_proc_transcribe", "batch_opt_proc_diarize",
            "batch_opt_proc_stories", "batch_opt_proc_translate", "batch_opt_save_project",
            "batch_opt_skip_existing", "batch_opt_save_project_only", "batch_opt_scope",
            "batch_opt_fmt_txt", "batch_opt_fmt_docx", "batch_opt_fmt_srt", "batch_opt_fmt_vtt",
            "batch_opt_include_speakers", "batch_opt_include_times", "batch_custom_output_dir",
            "batch_subfolders", "batch_auto_speakers", "batch_auto_detect_stories", "batch_auto_translate",
        ]
        for k in keys:
            win.settings_store.remove(k)
        win.settings_store.sync()
        QMessageBox.information(dialog, "Batch Options", "Batch processing options have been reset to factory defaults.")
    batch_options_reset_btn.clicked.connect(_reset_batch_export_defaults)
    batch_form.addRow("Factory Defaults:", batch_options_reset_btn)

    batch_layout.addLayout(batch_form)
    add_custom_defaults_btn(batch_layout, "Batch Processing", ["batch_processing"])
    batch_layout.addStretch()
    return page_batch


def build_cleanup_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_cleanup = QWidget()
    cleanup_layout = QVBoxLayout(page_cleanup)
    cleanup_layout.setSpacing(12)

    cleanup_desc = QLabel(
        "<b>Storage & Application Data Cleanup</b><br>"
        "<span style='color: #64748b; font-size: 12px;'>"
        "Manage local disk space by clearing downloaded AI model weights, temporary media caches, user preferences, or application activity logs.</span>"
    )
    cleanup_desc.setWordWrap(True)
    cleanup_layout.addWidget(cleanup_desc)

    cleanup_group = QGroupBox("Data Management & Cleanup Controls")
    cleanup_form = QVBoxLayout(cleanup_group)
    cleanup_form.setSpacing(10)

    clear_models_btn = QPushButton("Clear All Downloaded AI Models…")
    clear_models_btn.setToolTip("Purge all downloaded speech recognition and machine translation model files from disk.")
    def _on_clear_models():
        ans = QMessageBox.question(
            dialog, "Clear All Downloaded AI Models",
            "Are you sure you want to delete all locally downloaded AI model files (Whisper, Parakeet, OPUS-MT)?\n\n"
            "Models can be downloaded again when needed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            if hasattr(win, "purge_all_data_action"):
                win.purge_all_data_action(parent_widget=dialog)
            elif hasattr(win, "open_model_cleanup_dialog"):
                dialog.accept()
                win.open_model_cleanup_dialog()
    clear_models_btn.clicked.connect(_on_clear_models)
    cleanup_form.addWidget(clear_models_btn)

    open_mgr_btn = QPushButton("Clear Select AI Models…")
    open_mgr_btn.setToolTip("Open the detailed Model Management window to inspect exact disk sizes or delete specific individual models.")
    def _on_open_mgr():
        dialog.accept()
        if hasattr(win, "open_model_cleanup_dialog"):
            win.open_model_cleanup_dialog()
    open_mgr_btn.clicked.connect(_on_open_mgr)
    cleanup_form.addWidget(open_mgr_btn)

    clear_cache_btn = QPushButton("Clear Temporary Caches (Waveforms, Audio Extracts, & Thumbnails)…")
    clear_cache_btn.setToolTip("Inspect disk space usage and clear generated waveform peak files, temporary audio segment extracts, and video thumbnails.")
    def _on_clear_cache():
        project_dirs = []
        if hasattr(win, "project_file") and win.project_file:
            try:
                project_dirs.append(Path(win.project_file).parent)
            except Exception:
                pass
        if hasattr(win, "audio_file") and win.audio_file:
            try:
                project_dirs.append(Path(win.audio_file).parent)
            except Exception:
                pass
        from cache_manager import ClearCacheDialog
        dlg_cc = ClearCacheDialog(dialog, language=getattr(win, "language", "en"), project_dirs=project_dirs)
        dlg_cc.exec()
    clear_cache_btn.clicked.connect(_on_clear_cache)
    cleanup_form.addWidget(clear_cache_btn)

    clear_prefs_btn = QPushButton("Clear All User Preferences (Reset Settings to Defaults)…")
    clear_prefs_btn.setToolTip("Reset all user preferences and options back to factory defaults.")
    def _on_clear_prefs():
        ans = QMessageBox.question(
            dialog, "Clear All User Preferences",
            "Are you sure you want to reset all user preferences and settings to factory defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            win.settings_store.clear()
            all_cats = [c[0] for c in RestoreSelectedSettingsDialog.CATEGORIES]
            win.apply_settings_reset(all_cats, live_widgets=live_widgets)
            win.settings_store.sync()
            QMessageBox.information(
                dialog, "Preferences Reset",
                "All user preferences and settings have been restored to factory defaults."
            )
            dialog.accept()
            win.open_preferences_dialog(initial_category="Cleanup Data")
    clear_prefs_btn.clicked.connect(_on_clear_prefs)
    cleanup_form.addWidget(clear_prefs_btn)

    clear_logs_btn = QPushButton("Clear All other App Data, Activity Logs & Update Packages…")
    clear_logs_btn.setToolTip("Delete application activity logs, crash reports, and downloaded update installer packages.")
    def _on_clear_logs():
        ans = QMessageBox.question(
            dialog, "Clear App Data & Logs",
            "Are you sure you want to clear activity log files and downloaded update installer packages from AppData?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                from updater import cleanup_old_installers, get_app_data_dir
                purged_installers = cleanup_old_installers(force_all=True)
                app_data = get_app_data_dir()
                logs_cleared = 0
                for file_path in app_data.glob("*.log"):
                    try:
                        file_path.unlink(missing_ok=True)
                        logs_cleared += 1
                    except Exception:
                        pass
                for file_path in app_data.glob("*.txt"):
                    if "activity" in file_path.name.lower() or "log" in file_path.name.lower():
                        try:
                            file_path.unlink(missing_ok=True)
                            logs_cleared += 1
                        except Exception:
                            pass
                QMessageBox.information(
                    dialog, "App Data & Logs Cleared",
                    f"Successfully cleared application logs and updater files:\n\n"
                    f"• Update installer packages purged: {purged_installers}\n"
                    f"• Log files cleared: {logs_cleared}"
                )
            except Exception as exc:
                QMessageBox.warning(dialog, "Clear App Data Error", f"Failed to clear app data: {exc}")
    clear_logs_btn.clicked.connect(_on_clear_logs)
    cleanup_form.addWidget(clear_logs_btn)

    clear_everything_btn = QPushButton("Clear Everything (All Models, Caches, Preferences & App Data)…")
    clear_everything_btn.setToolTip("Completely purge all downloaded AI models, temporary caches, reset all user preferences to defaults, and clear app logs and updater files.")
    clear_everything_btn.setStyleSheet("color: #b3261e; font-weight: 600; padding: 6px;")
    def _on_clear_everything():
        ans = QMessageBox.warning(
            dialog, "Clear Everything",
            "<b>Are you sure you want to CLEAR EVERYTHING?</b><br><br>"
            "This action will perform a complete cleanup:<br>"
            "• Delete all downloaded AI models (Whisper, Parakeet, OPUS-MT)<br>"
            "• Delete all temporary caches (waveforms, audio extracts, thumbnails)<br>"
            "• Reset all user preferences and settings to factory defaults<br>"
            "• Purge all application activity logs and downloaded installer packages<br><br>"
            "<b>This cannot be undone. Do you wish to proceed?</b>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            summary_lines = []
            try:
                from prs_shared import purge_caches
                files_deleted, bytes_freed = purge_caches(clear_thumbnails=True, clear_waveforms=True, clear_audio_extracts=True)
                from updater import format_byte_size
                freed_str = format_byte_size(bytes_freed)
                summary_lines.append(f"• Temporary Caches: Cleared {files_deleted} files ({freed_str} reclaimed)")
            except Exception as exc:
                summary_lines.append(f"• Temporary Caches: Error ({exc})")

            try:
                from updater import cleanup_old_installers, get_app_data_dir
                purged_installers = cleanup_old_installers(force_all=True)
                app_data = get_app_data_dir()
                logs_cleared = 0
                for file_path in app_data.glob("*.log"):
                    try:
                        file_path.unlink(missing_ok=True)
                        logs_cleared += 1
                    except Exception:
                        pass
                for file_path in app_data.glob("*.txt"):
                    if "activity" in file_path.name.lower() or "log" in file_path.name.lower():
                        try:
                            file_path.unlink(missing_ok=True)
                            logs_cleared += 1
                        except Exception:
                            pass
                summary_lines.append(f"• App Data & Logs: Cleared {logs_cleared} log files and {purged_installers} update installer packages")
            except Exception as exc:
                summary_lines.append(f"• App Data & Logs: Error ({exc})")

            try:
                win.settings_store.clear()
                win.settings_store.sync()
                summary_lines.append("• User Preferences: Reset all settings to factory defaults")
            except Exception as exc:
                summary_lines.append(f"• User Preferences: Error ({exc})")

            if hasattr(win, "purge_all_data_action"):
                win.purge_all_data_action(parent_widget=dialog)
                summary_lines.append("• AI Models: Purged downloaded AI models and model caches")

            summary_msg = "Successfully cleared all requested data:\n\n" + "\n".join(summary_lines)
            QMessageBox.information(dialog, "Clear Everything Complete", summary_msg)
            dialog.accept()
            win.open_preferences_dialog(initial_category="Cleanup Data")

    clear_everything_btn.clicked.connect(_on_clear_everything)
    cleanup_form.addWidget(clear_everything_btn)

    cleanup_layout.addWidget(cleanup_group)
    add_custom_defaults_btn(cleanup_layout, "Cleanup Data Defaults")
    cleanup_layout.addStretch()
    return page_cleanup


def build_youtube_tab(win, dialog, live_widgets, add_custom_defaults_btn) -> QWidget:
    page_yt = QWidget()
    yt_layout = QVBoxLayout(page_yt)
    yt_desc = QLabel(
        "<b>YouTube Studio Assisted Upload (Zero-API Publishing)</b><br>"
        "<span style='color: #64748b; font-size: 12px;'>"
        "Radio & TV Segmenter formats video clips with interactive chapter markers, generates thumbnails, "
        "and exports subtitles (.srt), then opens YouTube Studio in your web browser with metadata pre-copied "
        "to the clipboard for immediate manual upload. No Google Cloud project or API credentials required.</span>"
    )
    yt_desc.setWordWrap(True)
    yt_layout.addWidget(yt_desc)

    yt_form_group = QGroupBox("Default Video Metadata")
    yt_form = QFormLayout(yt_form_group)

    yt_settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

    yt_cat_combo = QComboBox()
    yt_categories = [
        ("News & Politics", "25"),
        ("Entertainment", "24"),
        ("Education", "27"),
        ("People & Blogs", "22"),
        ("Music", "10"),
        ("Film & Animation", "1"),
        ("Science & Technology", "28"),
        ("Howto & Style", "26"),
        ("Travel & Events", "19"),
        ("Sports", "17"),
    ]
    for name, cid in yt_categories:
        yt_cat_combo.addItem(name, cid)
    saved_cat = str(yt_settings.value("export_yt_category", "25"))
    c_idx = yt_cat_combo.findData(saved_cat)
    yt_cat_combo.setCurrentIndex(c_idx if c_idx >= 0 else 0)
    yt_form.addRow("Default Category:", yt_cat_combo)
    live_widgets["yt_cat_combo"] = yt_cat_combo

    yt_priv_combo = QComboBox()
    yt_priv_combo.addItem("Unlisted (Recommended)", "unlisted")
    yt_priv_combo.addItem("Public", "public")
    yt_priv_combo.addItem("Private", "private")
    saved_priv = str(yt_settings.value("export_yt_privacy", "unlisted"))
    p_idx = yt_priv_combo.findData(saved_priv)
    yt_priv_combo.setCurrentIndex(p_idx if p_idx >= 0 else 0)
    yt_form.addRow("Default Privacy:", yt_priv_combo)
    live_widgets["yt_priv_combo"] = yt_priv_combo

    yt_tags_input = QLineEdit()
    yt_tags_input.setPlaceholderText("news, broadcast, interview, segment")
    yt_tags_input.setText(str(yt_settings.value("export_yt_tags", "news, broadcast, segment")))
    yt_form.addRow("Default Tags:", yt_tags_input)
    live_widgets["yt_tags_input"] = yt_tags_input
    yt_layout.addWidget(yt_form_group)

    yt_auto_group = QGroupBox("Workflow Automation Defaults")
    yt_auto_layout = QVBoxLayout(yt_auto_group)

    yt_cb_copy_input = QCheckBox("Automatically copy Title, Description & Chapters to clipboard")
    yt_cb_copy_input.setChecked(yt_settings.value("export_yt_copy_clipboard", True, type=bool))
    yt_auto_layout.addWidget(yt_cb_copy_input)
    live_widgets["yt_cb_copy_input"] = yt_cb_copy_input

    yt_cb_browser_input = QCheckBox("Automatically launch YouTube Studio upload page in browser")
    yt_cb_browser_input.setChecked(yt_settings.value("export_yt_open_browser", True, type=bool))
    yt_auto_layout.addWidget(yt_cb_browser_input)
    live_widgets["yt_cb_browser_input"] = yt_cb_browser_input

    yt_cb_subs_input = QCheckBox("Automatically generate Closed Captions (.srt) for YouTube")
    yt_cb_subs_input.setChecked(yt_settings.value("export_yt_subtitles", True, type=bool))
    yt_auto_layout.addWidget(yt_cb_subs_input)
    live_widgets["yt_cb_subs_input"] = yt_cb_subs_input

    yt_cb_folder_input = QCheckBox("Open export directory in file explorer after packaging")
    yt_cb_folder_input.setChecked(yt_settings.value("export_yt_open_folder", True, type=bool))
    yt_auto_layout.addWidget(yt_cb_folder_input)
    live_widgets["yt_cb_folder_input"] = yt_cb_folder_input

    yt_layout.addWidget(yt_auto_group)
    add_custom_defaults_btn(yt_layout, "YouTube Defaults")
    yt_layout.addStretch()
    return page_yt

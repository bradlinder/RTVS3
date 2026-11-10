"""
preferences_tab_daw.py — External Audio & Video Editors Preferences Tab.

Builds the dedicated settings panel for configuring integrations with external
DAWs and NLEs (Cockos REAPER, Adobe Audition, Premiere Pro, DaVinci Resolve, etc.).
"""

from typing import Any, Callable, Dict
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
)


def build_external_editors_tab(
    win: Any,
    dialog: Any,
    live_widgets: Dict[str, Any],
    add_custom_defaults_btn: Callable,
) -> QWidget:
    """Construct the External Audio & Video Editors preferences tab."""
    page = QWidget()
    tab_layout = QVBoxLayout(page)
    tab_layout.setSpacing(12)

    # 1. REAPER Companion Integration Group
    reaper_group = QGroupBox("REAPER DAW Companion Bridge")
    reaper_layout = QVBoxLayout(reaper_group)
    reaper_layout.setSpacing(10)

    reaper_auto_chk = QCheckBox("Automatically emit REAPER DAW clip cues when copying transcript text or stories")
    auto_cue_val = win.settings_store.value("reaper_auto_sidecar", "true")
    reaper_auto_chk.setChecked(str(auto_cue_val).strip().lower() in ("1", "true", "yes"))
    reaper_auto_chk.setToolTip("Writes JSON clip sidecar to disk and QMimeData whenever text or stories are copied.")
    reaper_layout.addWidget(reaper_auto_chk)
    live_widgets["reaper_auto_sidecar_chk"] = reaper_auto_chk

    reaper_color_chk = QCheckBox("Apply speaker color coding to pasted DAW clips")
    reaper_color_val = win.settings_store.value("reaper_color_items", "true")
    reaper_color_chk.setChecked(str(reaper_color_val).strip().lower() in ("1", "true", "yes"))
    reaper_color_chk.setToolTip("Applies speaker turn colors to media items and takes when pasting into REAPER.")
    reaper_layout.addWidget(reaper_color_chk)
    live_widgets["reaper_color_items_chk"] = reaper_color_chk

    marker_row = QHBoxLayout()
    marker_lbl = QLabel("REAPER Take Marker Style:")
    marker_combo = QComboBox()
    marker_combo.addItem("Speaker Changes Only (Default)", "speakers")
    marker_combo.addItem("Speaker Changes + True Sentence Cues", "sentences")
    marker_combo.addItem("None (No Take Markers)", "none")

    curr_marker_style = str(win.settings_store.value("reaper_marker_style", "speakers") or "speakers").strip().lower()
    if curr_marker_style not in ("speakers", "sentences", "none"):
        legacy_w = str(win.settings_store.value("reaper_include_word_markers", "false")).strip().lower()
        curr_marker_style = "sentences" if legacy_w in ("1", "true", "yes") else "speakers"

    idx = marker_combo.findData(curr_marker_style)
    if idx >= 0:
        marker_combo.setCurrentIndex(idx)
    marker_combo.setToolTip(
        "Controls what take markers are created on media items when pasted into REAPER. "
        "Sentence cues place take markers only at true grammatical sentence breaks or long pauses (>= 1.5s)."
    )
    marker_row.addWidget(marker_lbl)
    marker_row.addWidget(marker_combo, 1)
    reaper_layout.addLayout(marker_row)
    live_widgets["reaper_marker_style_combo"] = marker_combo

    install_btn_row = QHBoxLayout()
    install_reaper_btn = QPushButton("Install REAPER Companion Scripts...")
    install_reaper_btn.setToolTip("Copy rtvs_reaper_companion.lua, rtvs_reaper_auto_sync.lua, and dock scripts into your REAPER Scripts directory.")

    def _on_install_reaper_scripts():
        try:
            from reaper_bridge import install_reaper_scripts_to_resource_path
            install_reaper_scripts_to_resource_path(parent_widget=dialog)
        except Exception as exc:
            QMessageBox.warning(dialog, "Script Installation Error", str(exc))

    install_reaper_btn.clicked.connect(_on_install_reaper_scripts)
    install_btn_row.addWidget(install_reaper_btn)

    guide_btn = QPushButton("View DAW & Video Integration Guide...")
    guide_btn.setToolTip("Open the comprehensive documentation for the REAPER and DAW copy/paste bridge.")

    def _on_view_daw_guide():
        if hasattr(win, "open_user_documentation"):
            win.open_user_documentation("reaper_bridge")
        else:
            from user_guide_dialog import UserGuideDialog
            d = UserGuideDialog(dialog, initial_guide_id="reaper_bridge")
            d.exec()

    guide_btn.clicked.connect(_on_view_daw_guide)
    install_btn_row.addWidget(guide_btn)
    install_btn_row.addStretch()
    reaper_layout.addLayout(install_btn_row)

    tab_layout.addWidget(reaper_group)

    # 2. Non-REAPER DAWs & Video Editors Group
    other_group = QGroupBox("Non-REAPER DAWs & Video Editors (Audition, Premiere Pro, DaVinci Resolve)")
    other_layout = QVBoxLayout(other_group)
    other_layout.setSpacing(8)

    daw_wav_chk = QCheckBox("Enable WAV audio clip rendering (Ctrl+Shift+C) for non-REAPER DAWs")
    wav_clip_val = win.settings_store.value("daw_wav_clipboard", "false")
    daw_wav_chk.setChecked(str(wav_clip_val).strip().lower() in ("1", "true", "yes"))
    daw_wav_chk.setToolTip(
        "Renders uncompressed 24-bit 48kHz WAV audio slice to OS clipboard file list (CF_HDROP) via Ctrl+Shift+C "
        "or right-click menu for direct paste into Audition, Premiere, or DaVinci Resolve. Standard Ctrl+C remains strictly text-only."
    )
    other_layout.addWidget(daw_wav_chk)
    live_widgets["daw_wav_clipboard_chk"] = daw_wav_chk

    info_lbl = QLabel(
        "<b>Dedicated Audio Clip Copying:</b> When enabled, pressing <b>Ctrl+Shift+C</b> (or choosing "
        "<i>Copy Selection as Audio Clip</i> from the context menu) renders an uncompressed WAV slice to the system "
        "file clipboard for direct pasting into external timeline editors.<br><br>"
        "Standard <b>Ctrl+C</b> remains strictly clean text (+ REAPER JSON sidecar) so copying quotes never triggers "
        "unintended file uploads in chat apps or word processors."
    )
    info_lbl.setWordWrap(True)
    info_lbl.setStyleSheet("color: #888888; font-size: 11px; margin-top: 4px; margin-bottom: 4px;")
    other_layout.addWidget(info_lbl)

    tab_layout.addWidget(other_group)

    add_custom_defaults_btn(tab_layout, "External Audio & Video Editors", ["reaper_companion", "external_editors", "daw_wav_clipboard"])
    tab_layout.addStretch()
    return page

"""story_fades_dialog.py — Dialog for fine-grained audio fade-in, fade-out, and curve adjustment."""
from __future__ import annotations

import html
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QDoubleSpinBox, QFormLayout, QWidget
)

from prs_shared import format_time, FadeCurveVisualSelector
from core_utils import make_dialog_maximizable, apply_window_titlebar_theme

__all__ = ["StoryFadesDialog"]

class StoryFadesDialog(QDialog):
    """Dialog for fine-grained numerical adjustment of audio fade-in and fade-out durations."""

    def __init__(self, parent=None, story=None, story_index=0):
        super().__init__(parent)
        self.main_win = parent
        self.story = story
        self.story_index = story_index
        self._initial_fades = []
        if self.main_win and hasattr(self.main_win, "stories"):
            self._initial_fades = [
                (getattr(s, "fade_in", 0.0), getattr(s, "fade_out", 0.0), getattr(s, "fade_curve", "linear") or "linear")
                for s in self.main_win.stories
            ]
        self._initial_enable_fades = getattr(self.main_win, "enable_audio_fades", False) if self.main_win else False
        self._has_applied = False
        title = story.title if story and getattr(story, "title", None) else f"Story #{story_index + 1}"
        self.setWindowTitle(f"Audio Fades — {title}")
        self.resize(450, 310)
        make_dialog_maximizable(self)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        story_dur = max(0.01, (self.story.end - self.story.start)) if self.story else 10.0
        header_text = (
            f"<b>Story #{self.story_index + 1}: {html.escape(self.story.title if self.story else '')}</b><br>"
            f"<span style='color: #8b949e;'>Duration: {format_time(story_dur, include_millis=True)} ({story_dur:.2f}s)</span>"
        )
        header_label = QLabel(header_text, self)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)

        # Permanent Enable / Disable Audio Fades option on this screen
        self.enable_fades_cb = QCheckBox("Enable audio fades (timeline envelope handles and playback auditioning)", self)
        fades_enabled = bool(getattr(self.main_win, "enable_audio_fades", False)) if self.main_win else False
        self.enable_fades_cb.setChecked(fades_enabled)
        self.enable_fades_cb.setStyleSheet("font-weight: 600; padding: 2px 0;")
        self.enable_fades_cb.setToolTip("When checked, audio fade handles appear on the timeline and volume envelopes modulate playback. Also syncs with Preferences.")
        self.enable_fades_cb.toggled.connect(self._on_enable_fades_toggled)
        layout.addWidget(self.enable_fades_cb)

        form_group = QGroupBox("Audio Fade Durations & Profile", self)
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(14, 14, 14, 14)
        form_layout.setSpacing(10)

        self.fade_in_spin = QDoubleSpinBox(self)
        self.fade_in_spin.setRange(0.0, story_dur)
        self.fade_in_spin.setSingleStep(0.1)
        self.fade_in_spin.setDecimals(2)
        self.fade_in_spin.setSuffix(" s")
        curr_in = getattr(self.story, "fade_in", 0.0) if self.story else 0.0
        self.fade_in_spin.setValue(curr_in)
        form_layout.addRow("Fade In Duration:", self.fade_in_spin)

        self.fade_out_spin = QDoubleSpinBox(self)
        self.fade_out_spin.setRange(0.0, story_dur)
        self.fade_out_spin.setSingleStep(0.1)
        self.fade_out_spin.setDecimals(2)
        self.fade_out_spin.setSuffix(" s")
        curr_out = getattr(self.story, "fade_out", 0.0) if self.story else 0.0
        self.fade_out_spin.setValue(curr_out)
        form_layout.addRow("Fade Out Duration:", self.fade_out_spin)

        from prs_shared import FadeCurveVisualSelector
        self.fade_curve_combo = FadeCurveVisualSelector(self, button_width=86, button_height=56)
        curr_curve = getattr(self.story, "fade_curve", "linear") if self.story else "linear"
        self.fade_curve_combo.setCurrentData(curr_curve)
        form_layout.addRow("Fade Curve Profile:", self.fade_curve_combo)

        layout.addWidget(form_group)

        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:", self)
        preset_layout.addWidget(preset_label)

        btn_none = QPushButton("No Fades (0s)", self)
        btn_none.clicked.connect(lambda: (self.fade_in_spin.setValue(0.0), self.fade_out_spin.setValue(0.0)))
        preset_layout.addWidget(btn_none)

        btn_default = QPushButton("Restore Defaults", self)
        btn_default.clicked.connect(self._restore_defaults)
        preset_layout.addWidget(btn_default)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        self.apply_all_cb = QCheckBox("Apply these fade settings to all stories in project", self)
        layout.addWidget(self.apply_all_cb)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        apply_btn = QPushButton("Apply", self)
        apply_btn.setToolTip("Apply current fade curve and durations to audition live on timeline without closing")
        apply_btn.clicked.connect(self.apply_current)
        btn_box.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save Fades", self)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def _on_enable_fades_toggled(self, checked: bool):
        if self.main_win:
            self.main_win.enable_audio_fades = checked
            if hasattr(self.main_win, "settings_store") and self.main_win.settings_store:
                self.main_win.settings_store.setValue("enable_audio_fades", "true" if checked else "false")
            if hasattr(self.main_win, "timeline") and hasattr(self.main_win.timeline, "canvas"):
                self.main_win.timeline.canvas.show_audio_fades = checked
                self.main_win.timeline.canvas.update()
            if hasattr(self.main_win, "refresh_story_list"):
                self.main_win.refresh_story_list()

    def _sync_fades_preference(self):
        if getattr(self, "enable_fades_cb", None) and self.main_win:
            checked = self.enable_fades_cb.isChecked()
            self.main_win.enable_audio_fades = checked
            if hasattr(self.main_win, "settings_store") and self.main_win.settings_store:
                self.main_win.settings_store.setValue("enable_audio_fades", "true" if checked else "false")
            if hasattr(self.main_win, "timeline") and hasattr(self.main_win.timeline, "canvas"):
                self.main_win.timeline.canvas.show_audio_fades = checked
                self.main_win.timeline.canvas.update()
            if hasattr(self.main_win, "refresh_story_list"):
                self.main_win.refresh_story_list()

    def apply_current(self):
        self._sync_fades_preference()
        new_in, new_out, new_curve, apply_all = self.get_fades()
        if not self.main_win or not hasattr(self.main_win, "stories"):
            return

        if apply_all:
            for s in self.main_win.stories:
                s.fade_in = new_in
                s.fade_out = new_out
                s.fade_curve = new_curve
        else:
            if 0 <= self.story_index < len(self.main_win.stories):
                st = self.main_win.stories[self.story_index]
                st.fade_in = new_in
                st.fade_out = new_out
                st.fade_curve = new_curve

        if hasattr(self.main_win, "refresh_story_list"):
            self.main_win.refresh_story_list()
        if hasattr(self.main_win, "timeline"):
            self.main_win.timeline.set_stories(self.main_win.stories, getattr(self.main_win, "current_selected_story_indices", []))
            self.main_win.timeline.update()
        self._has_applied = True

    def accept(self):
        self._sync_fades_preference()
        super().accept()

    def reject(self):
        if getattr(self, "_initial_enable_fades", None) is not None and self.main_win:
            self.main_win.enable_audio_fades = self._initial_enable_fades
            if hasattr(self.main_win, "settings_store") and self.main_win.settings_store:
                self.main_win.settings_store.setValue("enable_audio_fades", "true" if self._initial_enable_fades else "false")
            if hasattr(self.main_win, "timeline") and hasattr(self.main_win.timeline, "canvas"):
                self.main_win.timeline.canvas.show_audio_fades = self._initial_enable_fades
                self.main_win.timeline.canvas.update()
            if hasattr(self.main_win, "refresh_story_list"):
                self.main_win.refresh_story_list()
        if self._has_applied and self.main_win and hasattr(self.main_win, "stories"):
            for idx, (fin, fout, fcur) in enumerate(self._initial_fades):
                if idx < len(self.main_win.stories):
                    st = self.main_win.stories[idx]
                    st.fade_in = fin
                    st.fade_out = fout
                    st.fade_curve = fcur
            if hasattr(self.main_win, "refresh_story_list"):
                self.main_win.refresh_story_list()
            if hasattr(self.main_win, "timeline"):
                self.main_win.timeline.set_stories(self.main_win.stories, getattr(self.main_win, "current_selected_story_indices", []))
                self.main_win.timeline.update()
        super().reject()

    def _restore_defaults(self):
        self.fade_in_spin.setValue(0.0)
        self.fade_out_spin.setValue(1.0)
        self.fade_curve_combo.setCurrentData("linear")

    def get_fades(self):
        return self.fade_in_spin.value(), self.fade_out_spin.value(), self.fade_curve_combo.currentData(), self.apply_all_cb.isChecked()



"""Radio & TV Story Segmenter — Media Player Transport & Playback Controller.

Handles media player transport controls (play, pause, stop, seek, scrub),
variable playback speeds (0.5x - 3.0x), real-time audio volume fading,
video preview floating window toggle, and global transport shortcut events.
"""

import logging
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLineEdit, QTextEdit,
    QPlainTextEdit, QAbstractSpinBox, QComboBox, QWidget
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from prs_shared import format_time, calculate_fade_curve_factor, calculate_fade_out_factor, InteractiveTranscriptEdit
from core_utils import apply_window_titlebar_theme

logger = logging.getLogger(__name__)


class PlaybackControllerMixin:
    """Provides audio/video media player transport, scrubbing, and fade controls."""

    def is_video_file(self, path):
        return Path(path).suffix.lower() in {
            ".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".wmv",
            ".mpeg", ".mpg", ".m2v", ".mts", ".m2ts", ".ts", ".flv", ".3gp",
            ".ogv", ".vob", ".asf", ".rm", ".rmvb"
        }

    def update_video_preview_state(self):
        if self.video_preview_action is not None:
            self.video_preview_action.setEnabled(bool(self.current_media_is_video))
        if not self.current_media_is_video and self.video_preview_dialog is not None:
            self.video_preview_dialog.hide()

    def toggle_video_preview(self, checked=None):
        if not self.current_media_is_video:
            return
        if self.video_preview_dialog is None:
            self.video_preview_dialog = QDialog(self)
            self.video_preview_dialog.setWindowTitle("Video Preview — Radio & TV Story Segmenter")
            self.video_preview_dialog.resize(720, 405)
            layout = QVBoxLayout(self.video_preview_dialog)
            self.video_preview_widget = QVideoWidget(self.video_preview_dialog)
            layout.addWidget(self.video_preview_widget)
            self.player.setVideoOutput(self.video_preview_widget)
        visible = self.video_preview_dialog.isVisible()
        if checked is None:
            checked = not visible
        if checked:
            self.video_preview_dialog.show()
            self.video_preview_dialog.raise_()
            self.video_preview_dialog.activateWindow()
        else:
            self.video_preview_dialog.hide()
        if self.video_preview_action is not None:
            self.video_preview_action.setChecked(bool(checked))

    def handle_scrub_position(self, seconds):
        self.pending_scrub_target = seconds
        if not self.scrub_timer.isActive():
            self.scrub_timer.start(35)

    def execute_scrub_seek(self):
        if self.pending_scrub_target is not None:
            seconds = self.pending_scrub_target
            self.pending_scrub_target = None

            self.player.setPosition(int(seconds * 1000))
            self.timeline.ensure_position_visible(seconds)
            self.transcript_view.highlight_word_at_time(seconds, self.transcript)

    def eventFilter(self, watched, event):
        # Automatically synchronize OS title bar theme across all windows and pop-up dialogs on show/activate
        if event.type() in (QEvent.Type.Show, QEvent.Type.ShowToParent, QEvent.Type.WindowActivate, QEvent.Type.Polish):
            try:
                if hasattr(watched, "isWindow") and watched.isWindow():
                    apply_window_titlebar_theme(watched, getattr(self, "theme_mode", None))
            except Exception:
                pass

        # Timeline and window media drag-and-drop event filtering
        if event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            timeline = getattr(self, "timeline", None)
            is_timeline_target = False
            if timeline is not None:
                if watched is timeline or watched is getattr(timeline, "canvas", None) or watched is getattr(timeline, "overview_bar", None):
                    is_timeline_target = True
                elif isinstance(watched, QWidget) and hasattr(timeline, "isAncestorOf"):
                    try:
                        if timeline.isAncestorOf(watched):
                            is_timeline_target = True
                    except Exception:
                        pass

            if is_timeline_target or watched is self:
                from core_utils import extract_dropped_file_paths
                paths = extract_dropped_file_paths(event.mimeData())
                if paths:
                    if event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove):
                        event.setDropAction(Qt.DropAction.CopyAction)
                        event.acceptProposedAction()
                        event.accept()
                        return True
                    elif event.type() == QEvent.Type.Drop:
                        first_path = paths[0]
                        if first_path.lower().endswith((".rtvs", ".rtvs3")):
                            if hasattr(self, "load_project_file"):
                                self.load_project_file(first_path)
                        else:
                            if hasattr(self, "load_media_file"):
                                self.load_media_file(first_path)
                        event.setDropAction(Qt.DropAction.CopyAction)
                        event.acceptProposedAction()
                        event.accept()
                        return True

        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            media_keys = {
                Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaPause, Qt.Key.Key_MediaTogglePlayPause,
                Qt.Key.Key_MediaStop, Qt.Key.Key_MediaNext, Qt.Key.Key_MediaPrevious,
            }
            if key in media_keys:
                if key in (Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaTogglePlayPause):
                    self.toggle_play()
                elif key == Qt.Key.Key_MediaPause:
                    self.player.pause()
                    self.timeline.set_playing_state(False)
                    self.play_button.setText("▶ Play")
                elif key == Qt.Key.Key_MediaStop:
                    self.stop_audio()
                elif key == Qt.Key.Key_MediaNext:
                    self.seek_to(min(self.duration, self.current_position + self.skip_seconds))
                elif key == Qt.Key.Key_MediaPrevious:
                    self.seek_to(max(0, self.current_position - self.skip_seconds))
                event.accept()
                return True

            if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and key in (Qt.Key.Key_Z, Qt.Key.Key_Y):
                focused_widget = QApplication.focusWidget()
                story_inputs = (
                    getattr(self, "start_input", None),
                    getattr(self, "end_input", None),
                    getattr(self, "title_input", None),
                )
                if focused_widget in story_inputs and focused_widget is not None:
                    if hasattr(focused_widget, "isModified") and focused_widget.isModified():
                        self.update_selected_story()
                    is_redo = bool(
                        key == Qt.Key.Key_Y or (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                    )
                    if is_redo:
                        if hasattr(self, "undo_stack") and self.undo_stack.canRedo():
                            self.undo_stack.redo()
                            event.accept()
                            return True
                    else:
                        if hasattr(self, "undo_stack") and self.undo_stack.canUndo():
                            self.undo_stack.undo()
                            event.accept()
                            return True

            # Play / Pause shortcut check (default Space, or custom user assignment)
            play_seq = "Space"
            if hasattr(self, "shortcuts_manager") and self.shortcuts_manager:
                play_seq = self.shortcuts_manager.get_current_shortcut("play_pause") or "Space"

            is_play_key = False
            if play_seq.lower() in ("space", ""):
                is_play_key = (key == Qt.Key.Key_Space and not event.modifiers())
            elif play_seq and play_seq != "None":
                is_play_key = (QKeySequence(int(event.modifiers()) | key) == QKeySequence(play_seq))

            if is_play_key:
                focused_widget = QApplication.focusWidget()
                if focused_widget and isinstance(focused_widget, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox)):
                    if isinstance(focused_widget, InteractiveTranscriptEdit) and not focused_widget.is_editing_mode:
                        pass
                    else:
                        return super().eventFilter(watched, event)
                if QApplication.activeModalWidget() is not None:
                    return super().eventFilter(watched, event)
                if focused_widget and (focused_widget.window() != self or isinstance(focused_widget.window(), QDialog)):
                    return super().eventFilter(watched, event)
                if focused_widget and isinstance(focused_widget, InteractiveTranscriptEdit) and focused_widget.is_editing_mode:
                    return super().eventFilter(watched, event)
                self.toggle_play()
                return True

        return super().eventFilter(watched, event)

    def set_skip_seconds_from_ui(self, value):
        self.skip_seconds = max(1, int(value))
        if hasattr(self, "timeline"):
            self.timeline.set_skip_seconds(self.skip_seconds)
        if hasattr(self, "skip_display") and self.skip_display.value() != self.skip_seconds:
            self.skip_display.setValue(self.skip_seconds)
        self.project_dirty = True
        self.update_window_title()

    def set_playback_rate(self, rate: float):
        self.playback_rate = max(0.5, min(3.0, float(rate)))
        if hasattr(self, "player") and self.player:
            try:
                self.player.setPlaybackRate(self.playback_rate)
            except Exception:
                pass
        if hasattr(self, "speed_combo") and self.speed_combo:
            idx = self.speed_combo.findData(self.playback_rate)
            if idx >= 0 and self.speed_combo.currentIndex() != idx:
                self.speed_combo.blockSignals(True)
                self.speed_combo.setCurrentIndex(idx)
                self.speed_combo.blockSignals(False)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            if hasattr(self, "fade_preview_timer"):
                self.fade_preview_timer.stop()
            self._audition_story_index = None
            if hasattr(self, "audio_output") and self.audio_output:
                self.audio_output.setVolume(getattr(self, "master_volume", 1.0))
            self.timeline.set_playing_state(False)
            self.play_button.setText("▶ Play")
        else:
            rate = float(getattr(self, "playback_rate", 1.0) or 1.0)
            try:
                self.player.setPlaybackRate(rate)
            except Exception:
                pass
            self.player.play()
            if getattr(self, "enable_audio_fades", False) and getattr(self, "preview_audio_fades", False):
                if hasattr(self, "fade_preview_timer"):
                    self.fade_preview_timer.start(35)
                self.update_realtime_fade_volume()
            self.timeline.set_playing_state(True)
            self.play_button.setText("❚❚ Pause")

    def stop_audio(self):
        self.player.stop()
        if hasattr(self, "fade_preview_timer"):
            self.fade_preview_timer.stop()
        self._audition_story_index = None
        if hasattr(self, "audio_output") and self.audio_output:
            master_vol = getattr(self, "master_volume", 1.0)
            self.audio_output.setVolume(master_vol)
            self._last_applied_fade_vol = master_vol
        self.timeline.set_playing_state(False)
        self.play_button.setText("▶ Play")

    def seek_to(self, seconds):
        self.current_position = float(seconds)
        self.player.setPosition(int(seconds * 1000))
        if hasattr(self, "timeline"):
            self.timeline.set_position(self.current_position)
            self.timeline.ensure_position_visible(seconds)
        if hasattr(self, "time_label"):
            self.time_label.setText(
                f"{format_time(self.current_position)} / {format_time(getattr(self, 'duration', 0.0))}"
            )
        if hasattr(self, "transcript_view"):
            self.transcript_view.highlight_word_at_time(seconds, self.transcript)
        if hasattr(self, "player") and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.update_realtime_fade_volume()

    def seek_relative(self, delta_seconds):
        duration = float(getattr(self, "duration", 0.0) or 0.0)
        curr = float(getattr(self, "current_position", 0.0) or 0.0)
        target = max(0.0, curr + float(delta_seconds))
        if duration > 0:
            target = min(duration, target)
        self.seek_to(target)

    def audio_position_changed(self, position):
        self.current_position = position / 1000
        self.timeline.set_position(self.current_position)
        self.time_label.setText(
            f"{format_time(self.current_position)} / {format_time(self.duration)}"
        )
        self.transcript_view.highlight_word_at_time(self.current_position, self.transcript)
        self.update_realtime_fade_volume()

    def get_fade_volume_factor_at_time(self, t: float) -> float:
        """Calculate the real-time audio volume fade factor [0.0, 1.0] for position `t`."""
        if not getattr(self, "enable_audio_fades", False) or not getattr(self, "preview_audio_fades", False):
            return 1.0

        stories = getattr(self, "stories", [])
        if not stories:
            return 1.0

        # If auditioning a specific story, check that story
        audition_idx = getattr(self, "_audition_story_index", None)
        if audition_idx is not None and 0 <= audition_idx < len(stories):
            active_stories = [stories[audition_idx]]
        else:
            # Check story under playhead, prioritizing currently selected stories
            selected_indices = getattr(self, "current_selected_story_indices", [])
            selected_matching = [stories[i] for i in selected_indices if 0 <= i < len(stories) and stories[i].start <= t <= stories[i].end]
            if selected_matching:
                active_stories = selected_matching
            else:
                active_stories = [s for s in stories if s.start <= t <= s.end]

        if not active_stories:
            return 1.0

        # Calculate volume envelope for active story
        story = active_stories[0]
        story_dur = max(0.001, story.end - story.start)
        fin = min(getattr(story, "fade_in", 0.0), story_dur)
        fout = min(getattr(story, "fade_out", 0.0), max(0.0, story_dur - fin))
        fcurve = getattr(story, "fade_curve", "linear") or "linear"

        factor = 1.0
        # Fade In ramp
        if fin > 0 and t >= story.start and t < (story.start + fin):
            u = (t - story.start) / fin
            factor = min(factor, calculate_fade_curve_factor(u, fcurve))

        # Fade Out ramp (progress u from 0.0 at fade start to 1.0 at silence)
        if fout > 0 and t > (story.end - fout) and t <= story.end:
            u = (t - (story.end - fout)) / fout
            factor = min(factor, calculate_fade_out_factor(u, fcurve))

        return factor

    def update_realtime_fade_volume(self):
        """Modulate QAudioOutput volume in real-time according to story fade envelopes."""
        if not hasattr(self, "audio_output") or not self.audio_output:
            return

        master_vol = getattr(self, "master_volume", 1.0)

        # Check if auditioning reached end of story
        audition_idx = getattr(self, "_audition_story_index", None)
        if audition_idx is not None and 0 <= audition_idx < len(getattr(self, "stories", [])):
            target_story = self.stories[audition_idx]
            if self.current_position >= (target_story.end + 0.05):
                self._audition_story_index = None
                self.stop_audio()
                return

        factor = self.get_fade_volume_factor_at_time(self.current_position)
        target_vol = max(0.0, min(1.0, master_vol * factor))
        last_vol = getattr(self, "_last_applied_fade_vol", None)
        if last_vol is None or abs(target_vol - last_vol) >= 0.005:
            self.audio_output.setVolume(target_vol)
            self._last_applied_fade_vol = target_vol

    def _on_fade_timer_tick(self):
        if hasattr(self, "player") and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.update_realtime_fade_volume()

    def audio_duration_changed(self, duration):
        self.duration = duration / 1000
        self.timeline.set_duration(self.duration)
        if self.current_media_is_video:
            QTimer.singleShot(0, self.start_video_thumbnail_generation)

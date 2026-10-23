"""Radio & TV Story Segmenter — Story CRUD & Timeline Selection Mixin.

Provides:
- StoryCrudMixin: Methods for story list synchronization, story creation from
  timeline ranges or transcript text selections, boundary editing, auditioning,
  deletion, audio fade application, and metadata editing.
"""

from __future__ import annotations
from typing import Any, List, Optional

try:
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QDialog,
        QListWidgetItem,
        QMessageBox,
    )
except ImportError:
    from qt_compat import _ensure_pyside6_fallback
    _ensure_pyside6_fallback()
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtWidgets import (
        QDialog,
        QListWidgetItem,
        QMessageBox,
    )

from core_utils import INTERNAL_APP_ID, format_time, parse_time
from story_model import Story, SetStoriesCommand, StoryBoundaryChangeCommand
from story_fades_dialog import StoryFadesDialog


class StoryCrudMixin:
    """Mixin providing story list UI management, CRUD operations, and fade handling."""

    def refresh_story_list(self):
        selected_indices = list(self.current_selected_story_indices)
        self.story_list.blockSignals(True)
        self.story_list.clear()

        curve_labels = {
            "linear": "Linear",
            "s_curve": "S-Curve",
            "logarithmic": "Logarithmic",
            "exponential": "Exponential",
        }

        for index, story in enumerate(self.stories, start=1):
            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)
            fcurve = getattr(story, "fade_curve", "linear") or "linear"

            fade_parts = []
            if fin > 0:
                fade_parts.append(f"In:{fin:.1f}s")
            if fout > 0:
                fade_parts.append(f"Out:{fout:.1f}s")
            fade_badge = f"  [{' '.join(fade_parts)}]" if fade_parts else ""

            text = f"{index}. {format_time(story.start)} – {format_time(story.end)}  {story.title}{fade_badge}"
            item = QListWidgetItem(text)
            curve_name = curve_labels.get(fcurve, fcurve.capitalize())
            fade_info = f"Fade-In: {fin:.2f}s | Fade-Out: {fout:.2f}s ({curve_name} Curve)" if (fin > 0 or fout > 0) else "No Fades Applied"

            item.setToolTip(f"Story #{index}: {story.title}\nTime Range: {format_time(story.start)} – {format_time(story.end)}\n{fade_info}")
            item.setData(Qt.ItemDataRole.UserRole, story.to_dict())
            self.story_list.addItem(item)

        for idx in selected_indices:
            if 0 <= idx < self.story_list.count():
                self.story_list.item(idx).setSelected(True)

        self.story_list.blockSignals(False)
        self.timeline.set_stories(self.stories, selected_indices)
        if hasattr(self, "update_story_list_height"):
            self.update_story_list_height()
        if hasattr(self, "notify_story_selection_to_plugins"):
            st = self.stories[selected_indices[0]] if (len(selected_indices) == 1 and 0 <= selected_indices[0] < len(self.stories)) else None
            self.notify_story_selection_to_plugins(st)

    def handle_new_story_started(self, start_time: float, end_time: float):
        self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]
        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        default_title = "Untitled Song" if is_music else "Untitled Story"
        story = Story(start=start_time, end=end_time, title=default_title)
        self.stories.append(story)
        self.refresh_story_list()
        self.story_selection_changed()
        self.start_input.setText(format_time(story.start))
        self.end_input.setText(format_time(story.end))
        self.title_input.setText(story.title)

    def handle_new_story_updated(self, start_time: float, end_time: float):
        if self.stories:
            story = self.stories[-1]
            story.start = start_time
            story.end = end_time
            self.start_input.setText(format_time(story.start))
            self.end_input.setText(format_time(story.end))
            if hasattr(self, "story_list") and self.story_list.count() > 0:
                last_idx = self.story_list.count() - 1
                item = self.story_list.item(last_idx)
                if item:
                    item.setText(f"{len(self.stories)}. {format_time(story.start)} – {format_time(story.end)}  {story.title}")
                    item.setData(Qt.ItemDataRole.UserRole, story.to_dict())

    def handle_drag_story_region(self, index: int, start_time: float, end_time: float):
        if not self.pre_drag_stories_snapshot:
            self.pre_drag_stories_snapshot = [Story.from_dict(s.to_dict()) for s in self.stories]

        if 0 <= index < len(self.stories):
            story = self.stories[index]
            story.start = start_time
            story.end = end_time
            if self.current_selected_story_indices != [index]:
                self.apply_story_selection_indices([index], seek=False)
            else:
                self.start_input.setText(format_time(story.start))
                self.end_input.setText(format_time(story.end))

    def audition_story(self, index: int):
        if not (0 <= index < len(self.stories)):
            return

        story = self.stories[index]
        self._audition_story_index = index
        self.apply_story_selection_indices([index], seek=False)
        self.seek_to(story.start)

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            fin = getattr(story, "fade_in", 0.0)
            if fin > 0 and hasattr(self, "audio_output"):
                self.audio_output.setVolume(0.0)
                self._last_applied_fade_vol = 0.0

        self.player.play()

        if getattr(self, "preview_audio_fades", False) and getattr(self, "enable_audio_fades", False):
            if hasattr(self, "fade_preview_timer"):
                self.fade_preview_timer.start(35)
            self.update_realtime_fade_volume()

        self.timeline.set_playing_state(True)
        self.play_button.setText("❚❚ Pause")

    def handle_drag_finished(self):
        if self.pre_drag_stories_snapshot:
            old_stories = self.pre_drag_stories_snapshot
            self.pre_drag_stories_snapshot = []
            changed_idx = None

            for i in range(min(len(old_stories), len(self.stories))):
                if (abs(old_stories[i].start - self.stories[i].start) > 0.001 or abs(old_stories[i].end - self.stories[i].end) > 0.001):
                    changed_idx = i
                    break

            if changed_idx is not None and hasattr(self, "undo_stack"):
                old_start = old_stories[changed_idx].start
                old_end = old_stories[changed_idx].end
                new_start = self.stories[changed_idx].start
                new_end = self.stories[changed_idx].end
                desc = f"Adjust Story #{changed_idx + 1} Boundary"

                self.stories[changed_idx].start = old_start
                self.stories[changed_idx].end = old_end

                cmd = StoryBoundaryChangeCommand(
                    self, changed_idx, old_start, old_end, new_start, new_end, desc
                )
                self.undo_stack.push(cmd)
            else:
                new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
                self.commit_story_change(old_stories, new_stories, "Adjust Story Selection")
                self.refresh_story_list()
                self.save_project()

    def update_selected_story(self):
        selected_rows = list(self.current_selected_story_indices)
        if not selected_rows:
            return

        try:
            start = parse_time(self.start_input.text())
            end = parse_time(self.end_input.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Time", str(exc))
            return

        if end <= start:
            QMessageBox.warning(self, "Invalid Story", "End time must be after start time.")
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        new_stories[index].start = start
        new_stories[index].end = end
        new_stories[index].title = self.title_input.text().strip() or "Untitled Story"

        author_val = self.author_input.text().strip() if hasattr(self, "author_input") else ""
        excerpt_val = self.excerpt_edit.toPlainText().strip() if hasattr(self, "excerpt_edit") else ""

        if not hasattr(new_stories[index], "metadata") or new_stories[index].metadata is None:
            new_stories[index].metadata = {}

        old_author = old_stories[index].metadata.get("author", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""
        old_excerpt = old_stories[index].metadata.get("excerpt", "") if (hasattr(old_stories[index], "metadata") and old_stories[index].metadata) else ""

        new_stories[index].metadata["author"] = author_val
        new_stories[index].metadata["excerpt"] = excerpt_val

        start_changed = abs(new_stories[index].start - old_stories[index].start) >= 0.001
        end_changed = abs(new_stories[index].end - old_stories[index].end) >= 0.001
        title_changed = new_stories[index].title != old_stories[index].title
        author_changed = author_val != old_author
        excerpt_changed = excerpt_val != old_excerpt

        if not (start_changed or end_changed or title_changed or author_changed or excerpt_changed):
            return

        if (start_changed or end_changed) and not title_changed and not author_changed and not excerpt_changed and hasattr(self, "undo_stack"):
            desc = f"Adjust Story #{index + 1} Boundary"
            cmd = StoryBoundaryChangeCommand(
                self, index, old_stories[index].start, old_stories[index].end, new_stories[index].start, new_stories[index].end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
            return

        self.commit_story_change(old_stories, new_stories, "Update Story Details")
        self.apply_story_selection_indices([index], seek=False)

    def delete_selected_story(self):
        selected_rows = sorted(list(self.current_selected_story_indices), reverse=True)
        if not selected_rows:
            return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for idx in selected_rows:
            del new_stories[idx]

        count = len(selected_rows)
        self.apply_story_selection_indices([], seek=False)

        if hasattr(self, "timeline") and hasattr(self.timeline, "canvas"):
            self.timeline.canvas.selection_start = None
            self.timeline.canvas.selection_end = None
            self.timeline.canvas.selectionRangeChanged.emit(None, None)
            self.timeline.canvas.update()

        desc = f"Delete {term if count == 1 else term_plural}"
        self.commit_story_change(old_stories, new_stories, desc)

    def get_current_interaction_time(self, for_boundary="start"):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            return s if for_boundary == "start" else e

        if hasattr(self, "transcript_view"):
            if self.transcript_view.has_active_selection():
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range:
                    return sel_range[0] if for_boundary == "start" else sel_range[1]

            if getattr(self, "last_position_source", None) == "transcript":
                last_ts = getattr(self, "last_transcript_cursor_time", None)
                if last_ts is not None and last_ts >= 0:
                    return last_ts

        return getattr(self, "current_position", 0.0)

    def set_selected_story_start(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="start")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time >= current_story.end:
            QMessageBox.warning(
                self, "Invalid Boundary", f"Start time ({format_time(target_time)}) must be earlier than story end time ({format_time(current_story.end)})."
            )
            return

        if abs(target_time - current_story.start) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} Start Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, target_time, current_story.end, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=True)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].start = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=True)
            self.mark_project_dirty(desc)
            self.save_project()

    def set_selected_story_end(self):
        selected_rows = list(self.current_selected_story_indices)
        if len(selected_rows) != 1:
            return

        index = selected_rows[0]
        if not (0 <= index < len(self.stories)):
            return

        current_story = self.stories[index]
        target_time = self.get_current_interaction_time(for_boundary="end")
        if target_time is None:
            target_time = getattr(self, "current_position", 0.0)

        target_time = round(max(0.0, float(target_time)), 3)
        if target_time <= current_story.start:
            QMessageBox.warning(
                self, "Invalid Boundary", f"End time ({format_time(target_time)}) must be later than story start time ({format_time(current_story.start)})."
            )
            return

        if abs(target_time - current_story.end) < 0.001:
            return

        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None:
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()

        desc = f"Set Story #{index + 1} End Time to {format_time(target_time)}"
        if hasattr(self, "undo_stack"):
            cmd = StoryBoundaryChangeCommand(
                self, index, current_story.start, current_story.end, current_story.start, target_time, desc
            )
            self.undo_stack.push(cmd)
            self.apply_story_selection_indices([index], seek=False)
        else:
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories[index].end = target_time
            self.commit_story_change(old_stories, new_stories, desc)
            self.refresh_story_list()
            self.apply_story_selection_indices([index], seek=False)
            self.mark_project_dirty(desc)
            self.save_project()

    def add_selection_to_story(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges:
            cursor = self.transcript_view.textCursor()
            if not cursor.hasSelection():
                QMessageBox.information(
                    self, "No Selection", "Highlight a portion of the transcript first to create a story from it."
                )
                return

        is_music = (getattr(self, "story_detection_mode", "voice") == "music")
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"

        if len(ranges) > 1:
            old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
            created_stories = []

            for r in ranges:
                s_time = r.get("start_time", 0.0)
                e_time = r.get("end_time", s_time + 1.0)
                if e_time <= s_time:
                    e_time = s_time + 1.0
                text = r.get("text", "").strip()
                words = text.split()
                t = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"
                created_stories.append(Story(start=s_time, end=e_time, title=t))

            new_stories = sorted(old_stories + created_stories, key=lambda s: s.start)
            if hasattr(self, "commit_story_change"):
                self.commit_story_change(old_stories, new_stories, f"Add {len(created_stories)} {term_plural} from Multi-Selection")
            else:
                self.stories = new_stories
                self.refresh_story_list()

            new_indices = [new_stories.index(s) for s in created_stories]
            if hasattr(self, "apply_story_selection_indices"):
                self.apply_story_selection_indices(new_indices)

            self.transcript_view.clear_all_selections()
            self.statusBar().showMessage(f"Created {len(created_stories)} {term_plural.lower()} from multiple selections.")
            return

        start_time = None
        end_time = None
        selected_text = ""

        if ranges:
            start_time = ranges[0].get("start_time")
            end_time = ranges[0].get("end_time")
            selected_text = ranges[0].get("text", "")
        else:
            cursor = self.transcript_view.textCursor()
            selected_text = cursor.selectedText().strip()
            if hasattr(self.transcript_view, "get_selected_time_range"):
                sel_range = self.transcript_view.get_selected_time_range()
                if sel_range and sel_range[0] is not None and sel_range[1] is not None:
                    start_time, end_time = sel_range

        if start_time is None or end_time is None:
            cursor = self.transcript_view.textCursor()
            start_char = cursor.selectionStart()
            end_char = cursor.selectionEnd()
            char_map = getattr(self.transcript_view, "char_timestamp_map", [])

            for entry in char_map:
                c_start, c_end, w_start, w_end = entry[0], entry[1], entry[2], entry[3]
                if c_start <= start_char <= c_end and start_time is None:
                    start_time = w_start
                if c_start <= end_char <= c_end:
                    end_time = w_end

        if start_time is None:
            start_time = getattr(self, "current_position", 0.0)
        if end_time is None:
            end_time = min(getattr(self, "duration", start_time + 5.0), start_time + 5.0)

        if end_time <= start_time:
            end_time = start_time + 1.0

        words = selected_text.split()
        default_title = (" ".join(words[:6]) + ("..." if len(words) > 6 else "")) if words else f"New {term}"

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(start_time))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(end_time))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=start_time, end=end_time, title=default_title)
        old_stories = [Story.from_dict(s.to_dict()) for s in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda s: s.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add {term} from Selection: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.transcript_view.clear_all_selections()
        self.statusBar().showMessage(f"Created {term.lower()}: {default_title}")

    def play_transcript_selection(self):
        if not hasattr(self, "transcript_view"):
            return

        ranges = []
        if hasattr(self.transcript_view, "get_all_selected_story_ranges"):
            ranges = self.transcript_view.get_all_selected_story_ranges()

        if not ranges and hasattr(self.transcript_view, "get_selected_time_range"):
            tr = self.transcript_view.get_selected_time_range()
            if tr and tr[0] is not None:
                ranges = [{"start_time": tr[0], "end_time": tr[1]}]

        if ranges:
            start_t = ranges[0].get("start_time", 0.0)
            self.seek_to(start_t)
            if hasattr(self, "player") and hasattr(self, "toggle_play"):
                from PySide6.QtMultimedia import QMediaPlayer
                if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self.toggle_play()

    def select_all_stories(self):
        if not getattr(self, "stories", []):
            return
        all_indices = list(range(len(self.stories)))
        self.apply_story_selection_indices(all_indices)
        if hasattr(self, "timeline"):
            self.timeline.set_stories(self.stories, all_indices)
        self.statusBar().showMessage(f"Selected all {len(self.stories)} stories.")

    def handle_timeline_selection_range_changed(self, start_time: Optional[float], end_time: Optional[float]):
        if not hasattr(self, "transcript_view"):
            return

        if start_time is None or end_time is None:
            if hasattr(self.transcript_view, "set_timeline_selection_span"):
                self.transcript_view.set_timeline_selection_span(None, None)
            cursor = self.transcript_view.textCursor()
            if cursor.hasSelection():
                cursor.clearSelection()
                self.transcript_view.setTextCursor(cursor)
            return

        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        char_map = getattr(self.transcript_view, "char_timestamp_map", [])
        if not char_map:
            return

        first_char = None
        last_char = None

        for item in char_map:
            c_start = item[0]
            c_end = item[1]
            w_start = item[2]
            w_end = item[3] if len(item) >= 4 else w_start

            if w_end >= s and first_char is None:
                first_char = c_start
            if w_start <= e:
                last_char = c_end

        if first_char is not None and last_char is not None and last_char > first_char:
            if hasattr(self.transcript_view, "set_timeline_selection_span"):
                self.transcript_view.set_timeline_selection_span(first_char, last_char)
            cursor = self.transcript_view.textCursor()
            cursor.clearSelection()
            cursor.setPosition(first_char)
            self.transcript_view.setTextCursor(cursor)
            self.transcript_view.ensureCursorVisible()
        else:
            if hasattr(self.transcript_view, "set_timeline_selection_span"):
                self.transcript_view.set_timeline_selection_span(None, None)

    def add_story_from_range(self, start_time: float, end_time: float):
        s = min(float(start_time), float(end_time))
        e = max(float(start_time), float(end_time))
        if e <= s:
            e = s + 1.0

        default_title = "New Story"
        if hasattr(self, "transcript_for_range"):
            segs = self.transcript_for_range(s, e)
            words = " ".join(seg.get("text", "").strip() for seg in segs).split()
            if words:
                default_title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")

        if hasattr(self, "start_input"):
            self.start_input.setText(format_time(s))
        if hasattr(self, "end_input"):
            self.end_input.setText(format_time(e))
        if hasattr(self, "title_input"):
            self.title_input.setText(default_title)

        new_story = Story(start=s, end=e, title=default_title)
        old_stories = [Story.from_dict(item.to_dict()) for item in getattr(self, "stories", [])]
        new_stories = sorted(old_stories + [new_story], key=lambda item: item.start)

        if hasattr(self, "commit_story_change"):
            self.commit_story_change(old_stories, new_stories, f"Add Story: '{default_title}'")
        else:
            self.stories = new_stories
            self.refresh_story_list()

        new_idx = new_stories.index(new_story)
        if hasattr(self, "apply_story_selection_indices"):
            self.apply_story_selection_indices([new_idx])

        self.statusBar().showMessage(f"Created story: {default_title}")

    def add_story_from_active_selection(self):
        canvas = getattr(getattr(self, "timeline", None), "canvas", None)
        if canvas and canvas.selection_start is not None and canvas.selection_end is not None:
            s = min(canvas.selection_start, canvas.selection_end)
            e = max(canvas.selection_start, canvas.selection_end)
            canvas.selection_start = None
            canvas.selection_end = None
            canvas.update()
            self.add_story_from_range(s, e)
            return

        if hasattr(self, "transcript_view") and self.transcript_view.has_active_selection():
            self.add_selection_to_story()
            return

        QMessageBox.information(
            self, "No Selection", "Make a selection first by right-click dragging across the timeline or highlighting transcript text."
        )

    def open_story_fades_dialog(self, story_index: Optional[int] = None):
        if not hasattr(self, "stories") or not self.stories:
            QMessageBox.information(self, "No Stories", "There are no stories created yet.")
            return

        if story_index is None:
            if hasattr(self, "current_selected_story_indices") and self.current_selected_story_indices:
                story_index = self.current_selected_story_indices[0]
            else:
                story_index = 0

        if not (0 <= story_index < len(self.stories)):
            return

        story = self.stories[story_index]
        dlg = StoryFadesDialog(self, story=story, story_index=story_index)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_in, new_out, new_curve, apply_all = dlg.get_fades()
            old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
            new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

            if apply_all:
                for s in new_stories:
                    s.fade_in = new_in
                    s.fade_out = new_out
                    s.fade_curve = new_curve
                desc = "Set Audio Fades on All Stories"
            else:
                new_stories[story_index].fade_in = new_in
                new_stories[story_index].fade_out = new_out
                new_stories[story_index].fade_curve = new_curve
                desc = f"Set Audio Fades on Story #{story_index + 1}"

            if hasattr(self, "undo_stack"):
                self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, desc))
            else:
                self.stories = new_stories
                self.refresh_story_list()
                if hasattr(self, "timeline"):
                    self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                    self.timeline.update()
                self.save_project()

    def apply_fades_to_selected_stories(self, fade_in: Optional[float] = None, fade_out: Optional[float] = None, fade_curve: Optional[str] = None):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        if fade_in is None:
            fade_in = float(settings.value("default_fade_in_duration", 0.0))
        if fade_out is None:
            fade_out = float(settings.value("default_fade_out_duration", 1.0))
        if fade_curve is None:
            fade_curve = str(settings.value("default_fade_curve", "linear") or "linear")

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_in = fade_in
                new_stories[i].fade_out = fade_out
                new_stories[i].fade_curve = fade_curve

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, "Apply Audio Fades to Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def remove_fades_from_selected_stories(self):
        self.apply_fades_to_selected_stories(fade_in=0.0, fade_out=0.0)

    def set_fade_curve_for_selected_stories(self, curve_type: str):
        if not hasattr(self, "stories") or not self.stories:
            return

        indices = list(getattr(self, "current_selected_story_indices", []))
        if not indices:
            indices = list(range(len(self.stories)))

        old_stories = [Story.from_dict(s.to_dict()) for s in self.stories]
        new_stories = [Story.from_dict(s.to_dict()) for s in self.stories]

        for i in indices:
            if 0 <= i < len(new_stories):
                new_stories[i].fade_curve = curve_type

        if hasattr(self, "undo_stack"):
            self.undo_stack.push(SetStoriesCommand(self, old_stories, new_stories, f"Set Fade Curve ({curve_type}) on Selected Stories"))
        else:
            self.stories = new_stories
            self.refresh_story_list()
            if hasattr(self, "timeline"):
                self.timeline.set_stories(self.stories, self.current_selected_story_indices)
                self.timeline.update()
            self.save_project()

    def open_story_metadata_dialog(self, target_story_index: Optional[int] = None, modal: bool = False):
        from story_metadata_dialog import StoryMetadataDialog
        if target_story_index is None and getattr(self, "current_selected_story_indices", None):
            target_story_index = self.current_selected_story_indices[0]

        if getattr(self, "_stories_panel_maximized", False) and hasattr(self, "toggle_maximize_stories_panel"):
            self.toggle_maximize_stories_panel()

        existing = getattr(self, "_active_metadata_dialog", None)
        if existing is not None and existing.isVisible():
            existing.refresh_from_main_window(target_story_index=target_story_index)
            if existing.isMinimized():
                existing.showNormal()
            existing.raise_()
            existing.activateWindow()
            return existing

        dlg = StoryMetadataDialog(self, main_window=self, target_story_index=target_story_index)
        self._active_metadata_dialog = dlg

        def _on_finished(_code: int):
            if getattr(self, "_active_metadata_dialog", None) is dlg:
                self._active_metadata_dialog = None

        dlg.finished.connect(_on_finished)
        if modal:
            dlg.exec()
            return dlg

        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        return dlg

    def _notify_floating_dialogs(self):
        """Refresh any open non-modal export or metadata floating windows after main window edits."""
        for attr in ("_active_export_dialog", "_active_metadata_dialog"):
            dlg = getattr(self, attr, None)
            if dlg is not None and dlg.isVisible() and not dlg.isActiveWindow():
                if hasattr(dlg, "refresh_from_main_window"):
                    try:
                        dlg.refresh_from_main_window()
                    except Exception:
                        pass

    def _close_floating_dialogs(self, persist_drafts: bool = True):
        """Persist drafts and close any active non-modal floating windows on project close or shutdown."""
        for attr in ("_active_export_dialog", "_active_metadata_dialog"):
            dlg = getattr(self, attr, None)
            if dlg is not None:
                try:
                    if persist_drafts:
                        if hasattr(dlg, "_persist_plugin_draft_states"):
                            dlg._persist_plugin_draft_states()
                        if hasattr(dlg, "save_all_to_project"):
                            dlg.save_all_to_project()
                    dlg.close()
                except Exception:
                    pass
                setattr(self, attr, None)

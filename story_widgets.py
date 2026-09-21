"""Radio & TV Story Segmenter — Story Sidebar Widgets, Item Delegates, and Undo Commands.

Contains:
- StoryCardDelegate: Custom QStyledItemDelegate rendering story cards with color-coded
  accent bars, numbered pills, time ranges, and audio fade badges.
- StoryListWidget: Interactive sidebar QListWidget supporting drag-and-drop,
  keyboard deletion, and custom right-click context menus.
- FadeCurveVisualSelector: Interactive card selector for audio fade curve profiles.
- Undo/Redo commands: StoryFadesChangeCommand, StoryBoundaryChangeCommand,
  SetStoriesCommand, SelectStoriesCommand.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QUndoCommand,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QToolButton,
    QHBoxLayout,
    QWidget,
)

from core_utils import format_time
from theme_tokens import ThemeTokens
from story_metadata_dialog import StoryMetadataDialog


def _get_fade_curve_profiles() -> List[Dict[str, Any]]:
    from prs_shared import FADE_CURVE_PROFILES
    return FADE_CURVE_PROFILES


def _get_fade_curve_icon(cid: str, width: int = 44, height: int = 22) -> QIcon:
    from prs_shared import create_fade_curve_icon
    return create_fade_curve_icon(cid, width=width, height=height)


# ============================================================
# Fade Curve Visual Selector
# ============================================================

class FadeCurveVisualSelector(QWidget):
    """Visual selector widget providing interactive card buttons for audio fade curves."""
    currentDataChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None, button_width=92, button_height=60):
        super().__init__(parent)
        self._current_data = "linear"
        self._buttons = []
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        profiles = _get_fade_curve_profiles()
        for idx, profile in enumerate(profiles):
            cid = profile["id"]
            btn = QToolButton(self)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(56, 28))
            btn.setIcon(_get_fade_curve_icon(cid, width=56, height=28))
            btn.setText(f"{profile['symbol']} {profile['title']}")
            btn.setToolTip(f"{profile['full_name']}\n{profile['desc']}")
            btn.setFixedSize(button_width, button_height)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn.setStyleSheet("""
                QToolButton {
                    background-color: rgba(30, 41, 59, 0.7);
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #cbd5e1;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 2px;
                }
                QToolButton:hover {
                    background-color: rgba(51, 65, 85, 0.85);
                    border: 1px solid #94a3b8;
                    color: #f8fafc;
                }
                QToolButton:checked {
                    background-color: rgba(14, 116, 144, 0.35);
                    border: 2px solid #38bdf8;
                    color: #38bdf8;
                    font-weight: bold;
                }
            """)

            self._button_group.addButton(btn, idx)
            btn.toggled.connect(self._on_button_toggled)
            layout.addWidget(btn)
            self._buttons.append((cid, btn))

        layout.addStretch()
        self.setCurrentData("linear")

    def _on_button_toggled(self, checked):
        if not checked:
            return
        for idx, (cid, btn) in enumerate(self._buttons):
            if btn.isChecked():
                if self._current_data != cid:
                    self._current_data = cid
                    self.currentDataChanged.emit(cid)
                    self.currentIndexChanged.emit(idx)
                break

    def currentData(self) -> str:
        return self._current_data

    def setCurrentData(self, curve_type: str):
        target = str(curve_type or "linear").lower().strip()
        found = False
        for idx, (cid, btn) in enumerate(self._buttons):
            if cid == target:
                btn.setChecked(True)
                self._current_data = cid
                found = True
                break
        if not found and self._buttons:
            self._buttons[0][1].setChecked(True)
            self._current_data = self._buttons[0][0]

    def findData(self, curve_type: str) -> int:
        target = str(curve_type or "linear").lower().strip()
        for idx, (cid, _) in enumerate(self._buttons):
            if cid == target:
                return idx
        return -1

    def currentIndex(self) -> int:
        for idx, (cid, _) in enumerate(self._buttons):
            if cid == self._current_data:
                return idx
        return 0

    def setCurrentIndex(self, idx: int):
        if 0 <= idx < len(self._buttons):
            self.setCurrentData(self._buttons[idx][0])


# ============================================================
# Story Undo / Redo Commands
# ============================================================

class StoryFadesChangeCommand(QUndoCommand):
    """Discrete undo/redo command for story audio fade-in, fade-out, and curve adjustments."""

    def __init__(self, main_window, story_index, old_in, old_out, new_in, new_out, old_curve="linear", new_curve="linear", description="Adjust Audio Fades"):
        super().__init__(description)
        self.main_window = main_window
        self.story_index = story_index
        self.old_in = round(float(old_in), 3)
        self.old_out = round(float(old_out), 3)
        self.new_in = round(float(new_in), 3)
        self.new_out = round(float(new_out), 3)
        self.old_curve = str(old_curve)
        self.new_curve = str(new_curve)

    def undo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].fade_in = self.old_in
            self.main_window.stories[self.story_index].fade_out = self.old_out
            self.main_window.stories[self.story_index].fade_curve = self.old_curve
            self._sync_ui()

    def redo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].fade_in = self.new_in
            self.main_window.stories[self.story_index].fade_out = self.new_out
            self.main_window.stories[self.story_index].fade_curve = self.new_curve
            self._sync_ui()

    def _sync_ui(self):
        if hasattr(self.main_window, "refresh_story_list"):
            self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if hasattr(self.main_window, "save_project"):
            self.main_window.save_project()


class SetStoriesCommand(QUndoCommand):
    def __init__(self, main_window, old_stories, new_stories, description="Modify Stories"):
        super().__init__(description)
        from prs_shared import Story
        self.main_window = main_window
        self.old_stories = [Story.from_dict(s.to_dict()) for s in old_stories]
        self.new_stories = [Story.from_dict(s.to_dict()) for s in new_stories]

    def undo(self):
        from prs_shared import Story
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.old_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        self.main_window.save_project()

    def redo(self):
        from prs_shared import Story
        self.main_window.stories = [Story.from_dict(s.to_dict()) for s in self.new_stories]
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        self.main_window.save_project()


class StoryBoundaryChangeCommand(QUndoCommand):
    """Discrete undo/redo command for story boundary adjustments (start/end times)."""

    def __init__(self, main_window, story_index, old_start, old_end, new_start, new_end, description="Adjust Story Boundary"):
        super().__init__(description)
        self.main_window = main_window
        self.story_index = story_index
        self.old_start = round(float(old_start), 3)
        self.old_end = round(float(old_end), 3)
        self.new_start = round(float(new_start), 3)
        self.new_end = round(float(new_end), 3)

    def undo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.old_start
            self.main_window.stories[self.story_index].end = self.old_end
            self._sync_ui(self.old_start, self.old_end)

    def redo(self):
        if 0 <= self.story_index < len(self.main_window.stories):
            self.main_window.stories[self.story_index].start = self.new_start
            self.main_window.stories[self.story_index].end = self.new_end
            self._sync_ui(self.new_start, self.new_end)

    def _sync_ui(self, start, end):
        self.main_window.refresh_story_list()
        if hasattr(self.main_window, "timeline"):
            self.main_window.timeline.set_stories(self.main_window.stories, self.main_window.current_selected_story_indices)
            self.main_window.timeline.update()
        if getattr(self.main_window, "current_selected_story_indices", []) == [self.story_index]:
            if hasattr(self.main_window, "start_input"):
                self.main_window.start_input.setText(format_time(start))
            if hasattr(self.main_window, "end_input"):
                self.main_window.end_input.setText(format_time(end))
        self.main_window.mark_project_dirty(self.text())
        self.main_window.save_project()


class SelectStoriesCommand(QUndoCommand):
    def __init__(self, main_window, old_selection, new_selection, description="Change Story Selection"):
        super().__init__(description)
        self.main_window = main_window
        self.old_selection = list(old_selection)
        self.new_selection = list(new_selection)

    def undo(self):
        self.main_window.apply_story_selection_indices(self.old_selection)

    def redo(self):
        self.main_window.apply_story_selection_indices(self.new_selection)


# ============================================================
# Story Card Delegate
# ============================================================

class StoryCardDelegate(QStyledItemDelegate):
    """Renders story items as clean cards with color-coded accent bars, pill badges, and time metadata."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        w = option.rect.width() if (option and option.rect and option.rect.width() > 0) else 240
        return QSize(max(120, w), 46)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        try:
            rect = option.rect
            list_widget = option.widget
            win = list_widget.window() if list_widget else None
            tokens = getattr(win, "tokens", ThemeTokens())
            palette = getattr(tokens, "story_palette", ("#2563eb", "#d97706", "#059669", "#7c3aed", "#e11d48", "#0d9488", "#4f46e5", "#db2777"))

            row = index.row()
            item_color = QColor(palette[row % len(palette)])

            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

            card_rect = QRectF(rect.x() + 3, rect.y() + 2, rect.width() - 6, rect.height() - 4)

            # Card Background & Outline
            if is_selected:
                bg = tokens.color(getattr(tokens, "selection_fill", "#38bdf8"))
                bg.setAlpha(90)
                border_pen = QPen(tokens.color(getattr(tokens, "selection_border", "#38bdf8")), 1.5)
            elif is_hovered:
                hover_hex = getattr(tokens, "bg_surface", getattr(tokens, "btn_hover_bg", "#181b20"))
                bg = tokens.color(hover_hex)
                border_pen = QPen(tokens.color(getattr(tokens, "border_subtle", "#282c35")), 1.0)
            else:
                card_hex = getattr(tokens, "bg_card", getattr(tokens, "card_bg", "#1e222a"))
                bg = tokens.color(card_hex)
                border_pen = QPen(tokens.color(getattr(tokens, "border_subtle", "#282c35")), 1.0)

            painter.fillRect(card_rect, bg)
            painter.setPen(border_pen)
            painter.drawRoundedRect(card_rect, 4.0, 4.0)

            # 4px Left Accent Bar in assigned story color
            bar_rect = QRectF(card_rect.x(), card_rect.y(), 4, card_rect.height())
            painter.fillRect(bar_rect, item_color)

            # Story Data
            story_data = index.data(Qt.ItemDataRole.UserRole)
            is_music = getattr(win, "story_detection_mode", "voice") == "music"
            is_es = getattr(win, "language", "en") == "es"
            badge_prefix = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

            if isinstance(story_data, dict):
                title = story_data.get("title", f"{badge_prefix} {row + 1}")
                start = float(story_data.get("start", 0.0))
                end = float(story_data.get("end", 0.0))
                dur = max(0.0, end - start)
                time_str = f"{format_time(start, include_millis=False)} – {format_time(end, include_millis=False)}  ({format_time(dur, include_millis=False)})"
            else:
                raw_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
                # Parse legacy string format "1. 00:00:00 – 00:02:15  Title"
                parts = raw_text.split("  ", 1)
                if len(parts) == 2:
                    time_str = parts[0].split(". ", 1)[-1] if ". " in parts[0] else parts[0]
                    title = parts[1]
                else:
                    time_str = ""
                    title = raw_text

            # Numbered Pill Badge (Story 1, Story 2...)
            badge_text = f"{badge_prefix} {row + 1}"
            badge_font = QFont(option.font)
            badge_font.setPointSize(8)
            badge_font.setBold(True)
            painter.setFont(badge_font)

            badge_w = max(48, painter.fontMetrics().horizontalAdvance(badge_text) + 12)
            badge_rect = QRectF(card_rect.x() + 9, card_rect.y() + 5, badge_w, 17)
            pill_bg = QColor(item_color)
            pill_bg.setAlpha(220)
            painter.fillRect(badge_rect, pill_bg)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

            # Story Headline / Title
            title_font = QFont(option.font)
            title_font.setPointSize(9)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(tokens.color(getattr(tokens, "text_primary", "#f0f3f6")))

            title_rect = QRectF(card_rect.x() + 15 + badge_w, card_rect.y() + 5, card_rect.width() - (22 + badge_w), 17)
            elided_title = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, int(title_rect.width()))
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_title)

            # Time range & fade metadata
            if time_str:
                win = list_widget.window() if list_widget else None
                fades_enabled = getattr(win, "enable_audio_fades", False)
                if fades_enabled:
                    fade_in = 0.0
                    fade_out = 0.0
                    if isinstance(story_data, dict):
                        fade_in = float(story_data.get("fade_in", 0.0))
                        fade_out = float(story_data.get("fade_out", 0.0))
                    elif win and hasattr(win, "stories") and 0 <= row < len(win.stories):
                        st = win.stories[row]
                        fade_in = getattr(st, "fade_in", 0.0)
                        fade_out = getattr(st, "fade_out", 0.0)
                    if fade_in > 0 or fade_out > 0:
                        time_str += f"  •  Fades: {fade_in:.1f}s / {fade_out:.1f}s"

                time_font = QFont(option.font)
                time_font.setPointSize(8)
                painter.setFont(time_font)
                painter.setPen(tokens.color(getattr(tokens, "text_secondary", "#8b949e")))
                time_rect = QRectF(card_rect.x() + 9, card_rect.y() + 24, card_rect.width() - 18, 14)
                painter.drawText(time_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, time_str)
        except Exception:
            # Fallback safe card painting
            painter.fillRect(option.rect, QColor("#1e222a"))
            painter.setPen(QColor("#ffffff"))
            raw_text = index.data(Qt.ItemDataRole.DisplayRole) or f"Story {index.row() + 1}"
            painter.drawText(option.rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, str(raw_text))
        finally:
            painter.restore()


# ============================================================
# Story List Widget
# ============================================================

class StoryListWidget(QListWidget):
    """QListWidget subclass for story segmentation list with right-click context menu and drag-drop support."""
    deleteRequested = Signal()
    exportRequested = Signal()
    exportStoryWordPressRequested = Signal()
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.filesDropped.emit(paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _show_context_menu(self, pos):
        parent = self.parent()
        while parent and not hasattr(parent, "open_story_fades_dialog"):
            parent = parent.parent()
        if not parent:
            return

        if not self.selectedItems():
            return

        menu = QMenu(self)

        audition_act = QAction("Audition Story Playback", self)
        audition_act.triggered.connect(lambda: parent.audition_story(self.currentRow()))
        menu.addAction(audition_act)

        menu.addSeparator()

        fade_menu = menu.addMenu("Audio Fades")

        adjust_fades_act = QAction("Adjust Fades for Selected Story...", self)
        adjust_fades_act.triggered.connect(lambda: parent.open_story_fades_dialog())
        fade_menu.addAction(adjust_fades_act)

        apply_default_fades_act = QAction("Apply Default Fades to Selected Stories", self)
        apply_default_fades_act.triggered.connect(lambda: parent.apply_fades_to_selected_stories())
        fade_menu.addAction(apply_default_fades_act)

        remove_fades_act = QAction("Remove Fades from Selected Stories", self)
        remove_fades_act.triggered.connect(lambda: parent.remove_fades_from_selected_stories())
        fade_menu.addAction(remove_fades_act)

        fade_menu.addSeparator()
        curve_menu = fade_menu.addMenu("Set Fade Curve Profile")

        # Determine current curve from selected story if available
        curr_curve = "linear"
        if hasattr(parent, "stories") and parent.stories:
            curr_row = self.currentRow()
            if 0 <= curr_row < len(parent.stories):
                curr_curve = getattr(parent.stories[curr_row], "fade_curve", "linear") or "linear"

        profiles = _get_fade_curve_profiles()
        for profile in profiles:
            cid = profile["id"]
            icon = _get_fade_curve_icon(cid, width=44, height=22)
            act = QAction(icon, f"{profile['symbol']}  {profile['full_name']}", self)
            act.setIconVisibleInMenu(True)
            act.setCheckable(True)
            act.setChecked(cid == curr_curve)
            act.setToolTip(profile["desc"])
            act.triggered.connect(lambda checked=False, ck=cid: parent.set_fade_curve_for_selected_stories(ck))
            curve_menu.addAction(act)

        menu.addSeparator()

        meta_act = QAction("Story & Post Metadata...", self)
        meta_act.triggered.connect(lambda: parent.open_story_metadata_dialog(self.currentRow()) if hasattr(parent, "open_story_metadata_dialog") else None)
        menu.addAction(meta_act)

        export_act = QAction("Export Selected Stories...", self)
        export_act.triggered.connect(lambda: self.exportRequested.emit())
        menu.addAction(export_act)

        # Dynamic plugin story actions (e.g. WordPress publish)
        if hasattr(parent, "plugin_manager") and parent.plugin_manager:
            selected_story = None
            if hasattr(parent, "stories") and hasattr(parent, "current_selected_story_indices"):
                sel = parent.current_selected_story_indices
                if len(sel) == 1 and 0 <= sel[0] < len(parent.stories):
                    selected_story = parent.stories[sel[0]]
            for plugin in parent.plugin_manager.plugins.values():
                if getattr(plugin, "is_enabled", False) and hasattr(plugin, "get_story_actions"):
                    try:
                        for label, callback in plugin.get_story_actions(story=selected_story):
                            action = QAction(label, self)
                            action.triggered.connect(callback)
                            menu.addAction(action)
                    except Exception as exc:
                        print(f"[PLUGINS] Error loading story actions from {getattr(plugin, 'id', 'unknown')}: {exc}")

        menu.addSeparator()

        del_act = QAction("Delete Selected Story", self)
        del_act.triggered.connect(lambda: self.deleteRequested.emit())
        menu.addAction(del_act)

        menu.exec(self.mapToGlobal(pos))

    def adjust_height_to_contents(self, min_h: int = 65, max_h: int = 220) -> int:
        """Dynamically size the list widget to only fit the number of stories."""
        cnt = self.count()
        if cnt == 0:
            h = min_h
        else:
            row_h = self.sizeHintForRow(0) if self.sizeHintForRow(0) > 0 else 28
            h = max(min_h, min(max_h, cnt * row_h + self.frameWidth() * 2 + 8))
        self.setFixedHeight(h)
        return h

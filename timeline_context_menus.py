"""Context menu builders and event handlers for the timeline canvas."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QWidget


def show_timeline_context_menu(canvas: Any, global_pos: QPoint, pos_x: float):
    """Display the primary right-click context menu on the timeline canvas."""
    win = canvas.window()
    menu = QMenu(canvas)
    width = canvas.width()
    time = max(0, min(canvas.duration, canvas.x_to_time(pos_x, width)))
    story_idx = canvas.find_story_at_time(time)

    is_music = getattr(win, "story_detection_mode", "voice") == "music"
    is_es = getattr(win, "language", "en") == "es"
    term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

    select_action = None
    fades_action = None
    delete_action = None
    if story_idx is not None and 0 <= story_idx < len(canvas.stories):
        select_action = menu.addAction(f"{('Seleccionar' if is_es else 'Select')} {term} #{story_idx + 1}")
        if hasattr(win, "open_story_fades_dialog"):
            fades_action = menu.addAction("Ajustar fundidos de audio..." if is_es else "Set Audio Fades...")
        delete_action = menu.addAction(f"{('Eliminar' if is_es else 'Delete')} {term} #{story_idx + 1}")
        menu.addSeparator()

    has_audio = bool(getattr(win, "audio_file", None))
    has_video = bool(getattr(win, "current_media_is_video", False))

    regen_wf_act = None
    regen_th_act = None
    if hasattr(win, "regenerate_waveform"):
        label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
        regen_wf_act = menu.addAction(label)
        regen_wf_act.setEnabled(has_audio)

    if hasattr(win, "regenerate_video_thumbnails"):
        label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
        regen_th_act = menu.addAction(label)
        regen_th_act.setEnabled(has_audio and has_video)

    if not menu.actions():
        return

    selected = menu.exec(global_pos)
    if story_idx is not None and 0 <= story_idx < len(canvas.stories):
        if select_action and selected == select_action:
            canvas.storyClicked.emit(story_idx)
        elif fades_action and selected == fades_action:
            if hasattr(win, "open_story_fades_dialog"):
                win.open_story_fades_dialog(story_index=story_idx)
        elif delete_action and selected == delete_action:
            if hasattr(win, "apply_story_selection_indices") and hasattr(win, "delete_selected_story"):
                win.apply_story_selection_indices([story_idx], seek=False)
                win.delete_selected_story()
    if regen_wf_act and selected == regen_wf_act:
        win.regenerate_waveform()
    elif regen_th_act and selected == regen_th_act:
        win.regenerate_video_thumbnails()


def show_selection_context_menu(canvas: Any, global_pos: QPoint):
    """Display the range selection context menu on the timeline canvas."""
    if canvas.selection_start is None or canvas.selection_end is None:
        return
    s = min(canvas.selection_start, canvas.selection_end)
    e = max(canvas.selection_start, canvas.selection_end)
    win = canvas.window()
    is_music = getattr(win, "story_detection_mode", "voice") == "music"
    is_es = getattr(win, "language", "en") == "es"
    term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")
    menu = QMenu(canvas)
    add_action = menu.addAction(f"{('Agregar' if is_es else 'Add')} {term} {('desde la selección' if is_es else 'from Selection')}")
    clear_action = menu.addAction("Borrar selección" if is_es else "Clear Selection")

    menu.addSeparator()
    has_audio = bool(getattr(win, "audio_file", None))
    has_video = bool(getattr(win, "current_media_is_video", False))

    regen_wf_act = None
    regen_th_act = None
    if hasattr(win, "regenerate_waveform"):
        label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
        regen_wf_act = menu.addAction(label)
        regen_wf_act.setEnabled(has_audio)

    if hasattr(win, "regenerate_video_thumbnails"):
        label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
        regen_th_act = menu.addAction(label)
        regen_th_act.setEnabled(has_audio and has_video)

    selected = menu.exec(global_pos)
    if selected == add_action:
        canvas.storyCreatedFromSelection.emit(s, e)
    elif selected == clear_action:
        canvas.selection_start = None
        canvas.selection_end = None
        canvas.selectionRangeChanged.emit(None, None)
        canvas.update()
    elif regen_wf_act and selected == regen_wf_act:
        win.regenerate_waveform()
    elif regen_th_act and selected == regen_th_act:
        win.regenerate_video_thumbnails()

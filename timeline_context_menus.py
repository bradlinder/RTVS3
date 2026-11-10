"""Context menu builders and event handlers for the timeline canvas."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QWidget


def show_timeline_context_menu(canvas: Any, global_pos: QPoint, pos_x: float):
    """Display the primary right-click context menu on the timeline canvas."""
    win = canvas.window()
    menu = QMenu(win if win is not None else canvas)
    width = canvas.width()
    time = max(0, min(canvas.duration, canvas.x_to_time(pos_x, width)))
    story_idx = canvas.find_story_at_time(time)

    is_music = getattr(win, "story_detection_mode", "voice") == "music"
    is_es = getattr(win, "language", "en") == "es"
    term = ("Canción" if is_es else "Song") if is_music else ("Historia" if is_es else "Story")

    audition_action = None
    copy_action = None
    clear_action = None
    fades_action = None
    meta_action = None
    export_action = None
    delete_action = None

    if story_idx is not None and 0 <= story_idx < len(canvas.stories):
        # Auto-select story if not already selected
        current_sel = getattr(win, "current_selected_story_indices", []) or []
        if story_idx not in current_sel:
            if hasattr(win, "apply_story_selection_indices"):
                win.apply_story_selection_indices([story_idx], seek=False)
            elif hasattr(canvas, "storyClicked"):
                canvas.storyClicked.emit(story_idx)

        # 1. Audition Story Playback
        if hasattr(win, "audition_story"):
            audition_action = menu.addAction("Escuchar historia" if is_es else "Audition Story Playback")

        # 2. Copy Story Transcript (Ctrl+C) & Audio Clip (Ctrl+Shift+C)
        copy_action = menu.addAction(f"{('Copiar transcripción' if is_es else 'Copy Story Transcript')} (Ctrl+C)")
        copy_wav_action = menu.addAction(f"{('Copiar clip de audio' if is_es else 'Copy Story as Audio Clip')} (Ctrl+Shift+C)")

        # 3. Clear Selection (Esc)
        clear_action = menu.addAction("Borrar selección (Esc)" if is_es else "Clear Selection (Esc)")

        # 4. Separator
        menu.addSeparator()

        # 5. Audio Fades...
        if hasattr(win, "open_story_fades_dialog"):
            fades_action = menu.addAction("Fundidos de audio..." if is_es else "Audio Fades...")

        # 6. Separator
        menu.addSeparator()

        # 7. Story & Post Metadata...
        if hasattr(win, "open_story_metadata_dialog"):
            meta_action = menu.addAction("Metadatos de historia y publicación..." if is_es else "Story & Post Metadata...")

        # 8. Export Selected Stories...
        if hasattr(win, "export_selected_stories") or hasattr(getattr(win, "story_panel", None), "exportRequested"):
            export_action = menu.addAction("Exportar historias seleccionadas..." if is_es else "Export Selected Stories...")

        # 9. Separator
        menu.addSeparator()

        # 10. Delete Story #N
        delete_action = menu.addAction(f"{('Eliminar' if is_es else 'Delete')} {term} #{story_idx + 1}")
    else:
        # Empty timeline space
        has_selected_stories = bool(getattr(canvas, "selected_story_indices", None) or getattr(win, "current_selected_story_indices", None))
        if has_selected_stories:
            clear_action = menu.addAction("Borrar selección (Esc)" if is_es else "Clear Selection (Esc)")
            menu.addSeparator()

        has_audio = bool(getattr(win, "audio_file", None))
        has_video = bool(getattr(win, "current_media_is_video", False))

        regen_wf_act = None
        regen_th_act = None
        if hasattr(win, "regenerate_waveform"):
            label = "Regenerar forma de onda" if is_es else "Regenerate Waveform"
            regen_wf_act = menu.addAction(label)
            regen_wf_act.setEnabled(has_audio)

        if has_video and hasattr(win, "regenerate_video_thumbnails"):
            label = "Regenerar miniaturas de video" if is_es else "Regenerate Video Thumbnails"
            regen_th_act = menu.addAction(label)
            regen_th_act.setEnabled(has_audio)

    if not menu.actions():
        return

    selected = menu.exec(global_pos)
    if story_idx is not None and 0 <= story_idx < len(canvas.stories):
        if audition_action and selected == audition_action:
            if hasattr(win, "audition_story"):
                win.audition_story(story_idx)
        elif copy_action and selected == copy_action:
            if hasattr(win, "transcript_view") and hasattr(win.transcript_view, "copy_highlighted_selection"):
                win.transcript_view.copy_highlighted_selection()
        elif copy_wav_action and selected == copy_wav_action:
            if hasattr(win, "transcript_view") and hasattr(win.transcript_view, "copy_selection_as_daw_wav"):
                win.transcript_view.copy_selection_as_daw_wav()
        elif clear_action and selected == clear_action:
            if hasattr(win, "apply_story_selection_indices"):
                win.apply_story_selection_indices([])
        elif fades_action and selected == fades_action:
            if hasattr(win, "open_story_fades_dialog"):
                win.open_story_fades_dialog(story_index=story_idx)
        elif meta_action and selected == meta_action:
            if hasattr(win, "open_story_metadata_dialog"):
                win.open_story_metadata_dialog(story_idx)
        elif export_action and selected == export_action:
            if hasattr(win, "export_selected_stories"):
                win.export_selected_stories()
            elif hasattr(getattr(win, "story_panel", None), "exportRequested"):
                win.story_panel.exportRequested.emit()
        elif delete_action and selected == delete_action:
            if hasattr(win, "delete_selected_story"):
                win.delete_selected_story()
    else:
        if clear_action and selected == clear_action:
            if hasattr(win, "apply_story_selection_indices"):
                win.apply_story_selection_indices([])
        elif 'regen_wf_act' in locals() and regen_wf_act and selected == regen_wf_act:
            win.regenerate_waveform()
        elif 'regen_th_act' in locals() and regen_th_act and selected == regen_th_act:
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
    menu = QMenu(win if win is not None else canvas)
    add_action = menu.addAction(f"{('Agregar' if is_es else 'Add')} {term} {('desde la selección' if is_es else 'from Selection')}")
    copy_action = menu.addAction("Copiar selección (Ctrl+C)" if is_es else "Copy Selection (Ctrl+C)")
    copy_wav_action = menu.addAction("Copiar clip de audio (Ctrl+Shift+C)" if is_es else "Copy Selection as Audio Clip (Ctrl+Shift+C)")
    clear_action = menu.addAction("Borrar selección (Esc)" if is_es else "Clear Selection (Esc)")

    selected = menu.exec(global_pos)
    if selected == add_action:
        canvas.storyCreatedFromSelection.emit(s, e)
    elif selected == copy_action:
        if hasattr(win, "transcript_view") and hasattr(win.transcript_view, "copy_highlighted_selection"):
            win.transcript_view.copy_highlighted_selection()
    elif selected == copy_wav_action:
        if hasattr(win, "transcript_view") and hasattr(win.transcript_view, "copy_selection_as_daw_wav"):
            win.transcript_view.copy_selection_as_daw_wav()
    elif selected == clear_action:
        canvas.selection_start = None
        canvas.selection_end = None
        canvas.selectionRangeChanged.emit(None, None)
        canvas.update()

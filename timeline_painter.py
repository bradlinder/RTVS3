"""Timeline canvas rendering engine, waveform drawing, and paint pipeline."""
from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from typing import Any, Optional

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from core_utils import calculate_fade_curve_factor, calculate_fade_out_factor

# Precomputed fade lookup tables for 60+ FPS curve rendering (16 segments per envelope)
_FADE_STEPS = 16
_FADE_IN_CURVE_TABLES = {
    c: [calculate_fade_curve_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}
_FADE_OUT_CURVE_TABLES = {
    c: [calculate_fade_out_factor(i / float(_FADE_STEPS), c) for i in range(1, _FADE_STEPS + 1)]
    for c in ("linear", "s_curve", "logarithmic", "exponential")
}


def render_waveform_buffer(canvas: Any, width: int, height: int) -> QPixmap:
    """Render background waveform peaks and video thumbnail strip onto an offscreen QPixmap."""
    dpi_scale = canvas.devicePixelRatioF()
    phys_width = max(1, int(width * dpi_scale))
    phys_height = max(1, int(height * dpi_scale))

    pixmap = QPixmap(phys_width, phys_height)
    pixmap.setDevicePixelRatio(dpi_scale)
    pixmap.fill(canvas.tokens.color(canvas.tokens.bg_surface))

    painter = QPainter(pixmap)
    if not painter.isActive():
        return pixmap
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    available = max(20, height - canvas.RULER_HEIGHT)
    is_video_mode = getattr(canvas, "is_video", False) or bool(canvas.video_thumbnails) or ("thumbnails" in canvas.active_background_tasks)
    has_thumbs = bool(canvas.show_thumbnails and (canvas.video_thumbnails or is_video_mode))

    if has_thumbs and canvas.show_waveform:
        thumbnail_height = int(available * 0.46)
        waveform_height = available - thumbnail_height
    elif has_thumbs:
        thumbnail_height = available
        waveform_height = 0
    elif canvas.show_waveform:
        thumbnail_height = 0
        waveform_height = available
    else:
        thumbnail_height = 0
        waveform_height = 0

    if canvas.thumbnail_position == "below" and canvas.show_waveform and has_thumbs:
        waveform_y = canvas.RULER_HEIGHT
        thumbnail_y = canvas.RULER_HEIGHT + waveform_height
    else:
        thumbnail_y = canvas.RULER_HEIGHT
        waveform_y = canvas.RULER_HEIGHT + thumbnail_height

    middle_y = waveform_y + (waveform_height / 2.0)

    # Draw subtle divider line between waveform and thumbnail tracks when both are visible
    if has_thumbs and canvas.show_waveform and thumbnail_height > 0 and waveform_height > 0:
        divider_y = thumbnail_y if canvas.thumbnail_position == "below" else waveform_y
        painter.setPen(canvas.tokens.pen(canvas.tokens.border_subtle, 1.0))
        painter.drawLine(QPointF(0, divider_y), QPointF(width, divider_y))

    if has_thumbs and thumbnail_height > 0:
        if canvas.video_thumbnails:
            target_h = max(14, int((thumbnail_height - 6) * 0.88))
            vis_dur = max(0.001, canvas.visible_duration())
            sample_pix = canvas.video_thumbnails[0][1] if canvas.video_thumbnails else None
            aspect = (sample_pix.width() / max(1, sample_pix.height())) if (sample_pix and not sample_pix.isNull() and sample_pix.height() > 0) else (16.0 / 9.0)
            target_w = max(24, int(target_h * aspect))

            dt_buffer = (target_w / max(1, width)) * vis_dur * 1.5
            t_min = max(0.0, canvas.scroll_offset - dt_buffer)
            t_max = min(canvas.duration, canvas.scroll_offset + vis_dur + dt_buffer)

            ts_list = [item[0] for item in canvas.video_thumbnails]
            start_idx = max(0, bisect_left(ts_list, t_min) - 1)
            end_idx = min(len(canvas.video_thumbnails), bisect_right(ts_list, t_max) + 1)

            last_drawn_right = -100000.0
            min_gap_px = 2.0

            for i in range(start_idx, end_idx):
                timestamp, pix = canvas.video_thumbnails[i]
                x = canvas.time_to_x(timestamp, width)
                if x + target_w < 0 or x - target_w > width:
                    continue
                scaled = pix.scaled(
                    target_w,
                    target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                draw_x = int(x - scaled.width() // 2)
                if draw_x < (last_drawn_right + min_gap_px):
                    continue

                draw_y = thumbnail_y + (thumbnail_height - scaled.height()) // 2
                painter.drawPixmap(draw_x, int(draw_y), scaled)
                painter.setPen(canvas.tokens.pen(canvas.tokens.border_subtle, 1.0))
                painter.drawRect(draw_x, int(draw_y), scaled.width(), scaled.height())
                last_drawn_right = draw_x + scaled.width()
        elif "thumbnails" in canvas.active_background_tasks or is_video_mode:
            win = canvas.window()
            is_es = getattr(win, "language", "en") == "es"
            gen_text = "Generando miniaturas de video..." if is_es else "Generating video thumbnails..."

            target_h = max(14, int((thumbnail_height - 6) * 0.88))
            aspect = 16.0 / 9.0
            target_w = max(24, int(target_h * aspect))
            draw_y = thumbnail_y + (thumbnail_height - target_h) // 2

            painter.save()
            box_pen = canvas.tokens.pen(canvas.tokens.border_subtle, 1.0)
            box_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(box_pen)

            step_px = target_w + 8
            x_pos = 12
            while x_pos + target_w < width - 12:
                painter.drawRoundedRect(QRectF(x_pos, draw_y, target_w, target_h), 2.0, 2.0)
                x_pos += step_px

            painter.setFont(canvas.font())
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(gen_text)
            text_badge_w = text_w + 24
            text_badge_h = min(26, max(18, thumbnail_height - 6))
            text_badge_x = (width - text_badge_w) / 2.0
            text_badge_y = thumbnail_y + (thumbnail_height - text_badge_h) / 2.0
            text_badge_rect = QRectF(text_badge_x, text_badge_y, text_badge_w, text_badge_h)

            painter.setPen(canvas.tokens.pen(canvas.tokens.status_banner_border, 1.0))
            painter.setBrush(canvas.tokens.brush(canvas.tokens.status_banner_bg, 235))
            painter.drawRoundedRect(text_badge_rect, 4.0, 4.0)
            painter.setPen(canvas.tokens.color(canvas.tokens.status_banner_text))
            painter.drawText(text_badge_rect, Qt.AlignmentFlag.AlignCenter, gen_text)
            painter.restore()

    if canvas.show_waveform and canvas.waveform_peaks and waveform_height > 0:
        painter.setPen(canvas.tokens.pen(canvas.tokens.waveform_stroke, 1.0))
        levels = canvas.waveform_levels or [canvas.waveform_peaks]
        total_pixel_width = max(width, int(width * canvas.zoom_level))
        level_index = 0
        while level_index + 1 < len(levels) and (len(levels[level_index]) / max(1, total_pixel_width)) > 2.0:
            level_index += 1
        peaks = levels[level_index]
        total_peaks = len(peaks)
        dur = max(0.001, canvas.duration)
        waveform_lines = []
        for x in range(width):
            t0 = canvas.x_to_time(x, width)
            t1 = canvas.x_to_time(x + 1, width)
            start_idx = int((t0 / dur) * total_peaks)
            end_idx = int((t1 / dur) * total_peaks)
            end_idx = max(start_idx + 1, end_idx)
            start_idx = max(0, min(total_peaks, start_idx))
            end_idx = max(0, min(total_peaks, end_idx))
            if start_idx >= total_peaks or end_idx <= start_idx:
                continue

            peak_slice = peaks[start_idx:end_idx]
            if hasattr(peak_slice, "__len__") and len(peak_slice) > 0:
                try:
                    max_val = float(np.max(peak_slice)) if (HAVE_NUMPY and np is not None and isinstance(peak_slice, np.ndarray)) else float(max(peak_slice))
                except Exception:
                    max_val = float(max(peak_slice))
                amplitude = max_val * (waveform_height * 0.88)
                if amplitude > 0.5:
                    waveform_lines.append(
                        QLineF(x + 0.5, middle_y - amplitude / 2.0, x + 0.5, middle_y + amplitude / 2.0)
                    )
        if waveform_lines:
            painter.drawLines(waveform_lines)
    elif canvas.show_waveform and waveform_height > 0:
        painter.setPen(canvas.tokens.pen(canvas.tokens.waveform_baseline, 1))
        painter.drawLine(QPointF(0, middle_y), QPointF(width, middle_y))

    painter.end()
    return pixmap


def paint_timeline_canvas(canvas: Any, painter: QPainter, event: Any):
    """Execute full timeline paint pipeline onto the canvas QPainter."""
    width = canvas.width()
    height = canvas.height()
    waveform_height = height - canvas.RULER_HEIGHT

    if (canvas.pixmap_dirty or canvas.waveform_pixmap is None or 
        canvas._last_rendered_width != width or 
        canvas._last_rendered_height != height or
        canvas._last_rendered_scroll != canvas.scroll_offset or
        canvas._last_rendered_zoom != canvas.zoom_level):
        
        canvas.waveform_pixmap = render_waveform_buffer(canvas, width, height)
        canvas._last_rendered_width = width
        canvas._last_rendered_height = height
        canvas._last_rendered_scroll = canvas.scroll_offset
        canvas._last_rendered_zoom = canvas.zoom_level
        canvas.buffered_total_width = width
        canvas.pixmap_dirty = False

    if canvas.waveform_pixmap is not None:
        painter.drawPixmap(0, 0, canvas.waveform_pixmap)

    # Time ruler track
    ruler_rect = QRectF(0, 0, width, canvas.RULER_HEIGHT)
    painter.fillRect(ruler_rect, canvas.tokens.ruler_background_color())
    painter.setPen(canvas.tokens.ruler_divider_pen())
    painter.drawLine(QPointF(0, canvas.RULER_HEIGHT), QPointF(width, canvas.RULER_HEIGHT))

    visible_dur = canvas.visible_duration()
    target_ticks = max(2, width // 100)
    base_interval = visible_dur / target_ticks
    nice_intervals = [0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
    chosen_interval = nice_intervals[-1]
    for step in nice_intervals:
        if base_interval <= step:
            chosen_interval = step
            break

    painter.setFont(canvas.font())
    painter.setPen(canvas.tokens.ruler_tick_pen())
    start_tick = math.floor(canvas.scroll_offset / chosen_interval) * chosen_interval
    t = start_tick
    while t <= canvas.scroll_offset + visible_dur + (chosen_interval * 0.1):
        t_rounded = round(t, 4)
        x = canvas.time_to_x(t_rounded, width)
        if 0 <= x <= width:
            painter.drawLine(QPointF(x, canvas.RULER_HEIGHT - 6), QPointF(x, canvas.RULER_HEIGHT))
            if chosen_interval < 1.0:
                total_sec = abs(t_rounded)
                hrs = int(total_sec // 3600)
                mins = int((total_sec % 3600) // 60)
                secs = total_sec % 60
                sec_str = f"{secs:04.1f}" if chosen_interval >= 0.2 else f"{secs:05.2f}"
                label = f"{hrs}:{mins:02d}:{sec_str}" if hrs > 0 else f"{mins:02d}:{sec_str}"
            else:
                mins = int(t_rounded // 60)
                secs = int(t_rounded % 60)
                hrs = int(mins // 60)
                mins = mins % 60
                label = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"
            text_rect = QRectF(x + 3, 2, 70 if chosen_interval < 1.0 else 60, canvas.RULER_HEIGHT - 4)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
        t += chosen_interval

    audio_name = getattr(canvas, "audio_file_name", None)
    if audio_name:
        painter.setPen(canvas.tokens.pen(canvas.tokens.audio_label_text, 1.0))
        filename_rect = QRectF(8, canvas.RULER_HEIGHT + 4, 300, 18)
        painter.drawText(filename_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Audio: {audio_name}")

    if canvas.transcript_selection_range and not canvas.is_right_dragging and (canvas.selection_start is None or canvas.selection_end is None):
        sel_start, sel_end = canvas.transcript_selection_range
        sx = canvas.time_to_x(sel_start, width)
        ex = canvas.time_to_x(sel_end, width)
        left = max(0, min(width, sx))
        right = max(0, min(width, ex))
        if right > left:
            painter.fillRect(QRectF(left, canvas.RULER_HEIGHT, right-left, waveform_height), canvas.tokens.selection_rect_brush(is_transcript=True))
            painter.setPen(canvas.tokens.selection_rect_pen())
            painter.drawLine(QPointF(left, canvas.RULER_HEIGHT), QPointF(left, height))
            painter.drawLine(QPointF(right, canvas.RULER_HEIGHT), QPointF(right, height))

    # Draw active right-click drag selection with adjustable edge handles
    if canvas.selection_start is not None and canvas.selection_end is not None:
        sx = canvas.time_to_x(canvas.selection_start, width)
        ex = canvas.time_to_x(canvas.selection_end, width)
        left = max(0.0, min(float(width), min(sx, ex)))
        right = max(0.0, min(float(width), max(sx, ex)))
        if right > left:
            painter.fillRect(QRectF(left, canvas.RULER_HEIGHT, right - left, waveform_height), canvas.tokens.selection_rect_brush(is_transcript=False))
            painter.setPen(canvas.tokens.selection_rect_pen())
            painter.drawRect(QRectF(left, canvas.RULER_HEIGHT, right - left, waveform_height))
            painter.fillRect(QRectF(left - 3, canvas.RULER_HEIGHT, 6, waveform_height), canvas.tokens.selection_handle_brush())
            painter.fillRect(QRectF(right - 3, canvas.RULER_HEIGHT, 6, waveform_height), canvas.tokens.selection_handle_brush())

    for index, story in enumerate(canvas.stories):
        start_x = canvas.time_to_x(story.start, width)
        end_x = canvas.time_to_x(story.end, width)
        if end_x < 0 or start_x > width:
            continue

        is_selected = index in canvas.selected_story_indices
        rect_start = max(0, start_x)
        rect_end = min(width, end_x)

        painter.fillRect(
            QRectF(rect_start, canvas.RULER_HEIGHT, max(1, rect_end - rect_start), waveform_height),
            canvas.tokens.story_segment_brush(index, is_selected=is_selected),
        )

        # --- Audio Fade Ramps & Envelope Visualization ---
        if getattr(canvas, "show_audio_fades", False):
            fin = getattr(story, "fade_in", 0.0)
            fout = getattr(story, "fade_out", 0.0)
            fcurve = getattr(story, "fade_curve", "linear") or "linear"
            fcurve = str(fcurve).lower()

            story_dur = max(0.001, story.end - story.start)
            fin = max(0.0, min(fin, story_dur))
            fout = max(0.0, min(fout, max(0.0, story_dur - fin)))

            top_y = float(canvas.RULER_HEIGHT)
            bottom_y = float(height)

            fin_apex_x = canvas.time_to_x(story.start + fin, width)
            if fin > 0 and fin_apex_x >= 0 and start_x <= width:
                in_table = _FADE_IN_CURVE_TABLES.get(fcurve, _FADE_IN_CURVE_TABLES["linear"])
                in_path = QPainterPath()
                in_path.moveTo(start_x, bottom_y)
                dx = fin_apex_x - start_x
                dy = bottom_y - top_y
                for step_i, val in enumerate(in_table, 1):
                    px = start_x + (step_i / float(_FADE_STEPS)) * dx
                    py = bottom_y - val * dy
                    in_path.lineTo(px, py)

                fill_path = QPainterPath(in_path)
                fill_path.lineTo(start_x, top_y)
                fill_path.lineTo(start_x, bottom_y)
                fill_path.closeSubpath()

                painter.setBrush(canvas._fade_fill_brush_sel if is_selected else canvas._fade_fill_brush_unsel)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(fill_path)

                # Smooth ramp stroke
                painter.setPen(canvas._fade_in_ramp_pen_sel if is_selected else canvas._fade_in_ramp_pen_unsel)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(in_path)

            # Tactile Grab Handle for Fade-In at apex along top edge
            if 0 <= fin_apex_x <= width:
                painter.setPen(canvas._fade_in_handle_pen_sel if is_selected else canvas._fade_in_handle_pen_unsel)
                painter.setBrush(canvas._fade_in_handle_brush_sel if is_selected else canvas._fade_in_handle_brush_unsel)
                painter.drawRoundedRect(QRectF(fin_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

            fout_apex_x = canvas.time_to_x(story.end - fout, width)
            if fout > 0 and end_x >= 0 and fout_apex_x <= width:
                out_table = _FADE_OUT_CURVE_TABLES.get(fcurve, _FADE_OUT_CURVE_TABLES["linear"])
                out_path = QPainterPath()
                out_path.moveTo(fout_apex_x, top_y)
                dx = end_x - fout_apex_x
                dy = bottom_y - top_y
                for step_i, val in enumerate(out_table, 1):
                    px = fout_apex_x + (step_i / float(_FADE_STEPS)) * dx
                    py = bottom_y - val * dy
                    out_path.lineTo(px, py)

                fill_path = QPainterPath(out_path)
                fill_path.lineTo(end_x, top_y)
                fill_path.lineTo(fout_apex_x, top_y)
                fill_path.closeSubpath()

                painter.setBrush(canvas._fade_fill_brush_sel if is_selected else canvas._fade_fill_brush_unsel)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(fill_path)

                # Smooth ramp stroke
                painter.setPen(canvas._fade_out_ramp_pen_sel if is_selected else canvas._fade_out_ramp_pen_unsel)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(out_path)

            # Tactile Grab Handle for Fade-Out at apex along top edge
            if 0 <= fout_apex_x <= width:
                painter.setPen(canvas._fade_out_handle_pen_sel if is_selected else canvas._fade_out_handle_pen_unsel)
                painter.setBrush(canvas._fade_out_handle_brush_sel if is_selected else canvas._fade_out_handle_brush_unsel)
                painter.drawRoundedRect(QRectF(fout_apex_x - 4, top_y + 1, 8, 10), 2.0, 2.0)

        painter.setPen(canvas.tokens.story_segment_pen(index, is_selected=is_selected))
        if 0 <= start_x <= width:
            painter.drawLine(QPointF(start_x, canvas.RULER_HEIGHT), QPointF(start_x, height))
        if 0 <= end_x <= width:
            painter.drawLine(QPointF(end_x, canvas.RULER_HEIGHT), QPointF(end_x, height))

    # Draw Playhead Line
    cursor_x = canvas.time_to_x(canvas.position, width)
    if 0 <= cursor_x <= width:
        painter.setPen(canvas.tokens.playhead_pen(2.0))
        painter.drawLine(QPointF(cursor_x, 0), QPointF(cursor_x, height))

    # Draw Background Task Status Banner (Waveform / Thumbnail Generation)
    if canvas.show_background_banner and canvas.background_status_text:
        canvas_font = canvas.font()
        canvas_font.setPointSize(9)
        canvas_font.setBold(True)
        painter.setFont(canvas_font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(canvas.background_status_text)
        badge_w = text_w + 24
        badge_h = 24
        badge_x = (width - badge_w) / 2.0
        badge_y = canvas.RULER_HEIGHT + 8
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        painter.setPen(canvas.tokens.pen(canvas.tokens.status_banner_border, 1.5))
        painter.setBrush(canvas.tokens.brush(canvas.tokens.status_banner_bg, 230))
        painter.drawRoundedRect(badge_rect, 4.0, 4.0)

        painter.setPen(canvas.tokens.color(canvas.tokens.status_banner_text))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, canvas.background_status_text)

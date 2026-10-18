"""Timeline snapping algorithms, edge detection, and collision hit-testing."""
from __future__ import annotations

from typing import Any, Optional, Tuple


def snap_time(
    canvas: Any,
    raw_time: float,
    exclude_story_idx: Optional[int] = None,
    width: Optional[int] = None,
    pixel_threshold: int = 10,
) -> float:
    """Snap raw_time to nearby story boundaries, playhead, or selection anchors if within pixel_threshold pixels."""
    if not getattr(canvas, "enable_magnetic_snapping", True):
        return raw_time

    width = width or max(1, canvas.width())
    vis_dur = max(0.001, canvas.visible_duration())
    threshold_dt = (pixel_threshold / max(1, width)) * vis_dur

    snap_points = []

    # 1. Playhead position
    if hasattr(canvas, "position") and canvas.position is not None:
        snap_points.append(float(canvas.position))

    # 2. Selection region anchors
    if getattr(canvas, "selection_start", None) is not None:
        snap_points.append(float(canvas.selection_start))
    if getattr(canvas, "selection_end", None) is not None:
        snap_points.append(float(canvas.selection_end))

    # 3. Story boundaries
    cached_points = getattr(canvas, "_cached_story_snap_points", None)
    if cached_points is not None and len(cached_points) == len(getattr(canvas, "stories", [])):
        for idx, s_start, s_end in cached_points:
            if exclude_story_idx is not None and idx == exclude_story_idx:
                continue
            snap_points.append(s_start)
            snap_points.append(s_end)
    else:
        for idx, story in enumerate(getattr(canvas, "stories", [])):
            if exclude_story_idx is not None and idx == exclude_story_idx:
                continue
            snap_points.append(float(story.start))
            snap_points.append(float(story.end))

    best_snap = raw_time
    min_diff = threshold_dt + 0.00001

    for pt in snap_points:
        diff = abs(raw_time - pt)
        if diff <= threshold_dt and diff < min_diff:
            min_diff = diff
            best_snap = pt

    return best_snap


def find_edge_at_pos(canvas: Any, pos_x: float, width: int) -> Optional[Tuple[int, str]]:
    """Determine if pos_x is hovering over a story segment start or end boundary edge."""
    for index, story in enumerate(canvas.stories):
        start_x = canvas.time_to_x(story.start, width)
        end_x = canvas.time_to_x(story.end, width)

        if abs(pos_x - start_x) <= canvas.EDGE_HANDLE_THRESHOLD:
            return (index, 'start')
        elif abs(pos_x - end_x) <= canvas.EDGE_HANDLE_THRESHOLD:
            return (index, 'end')
    return None


def find_fade_handle_at_pos(canvas: Any, pos_x: float, pos_y: float, width: int) -> Optional[Tuple[int, str]]:
    """Hit-test tactile fade-in and fade-out envelope handles near the top edge of story blocks."""
    if not getattr(canvas, "show_audio_fades", False):
        return None

    top_y = canvas.RULER_HEIGHT
    if pos_y < (top_y - 8) or pos_y > (top_y + 26):
        return None

    for index, story in enumerate(canvas.stories):
        start_x = canvas.time_to_x(story.start, width)
        end_x = canvas.time_to_x(story.end, width)
        if end_x < -16 or start_x > width + 16:
            continue

        fin = getattr(story, "fade_in", 0.0)
        fout = getattr(story, "fade_out", 0.0)

        # Fade-in handle apex sits at (start + fade_in) along top edge
        fin_x = canvas.time_to_x(story.start + fin, width)
        if abs(pos_x - fin_x) <= canvas.FADE_HANDLE_THRESHOLD:
            return (index, "fade_in")

        # Fade-out handle apex sits at (end - fade_out) along top edge
        fout_x = canvas.time_to_x(story.end - fout, width)
        if abs(pos_x - fout_x) <= canvas.FADE_HANDLE_THRESHOLD:
            return (index, "fade_out")
    return None


def find_story_at_time(canvas: Any, time: float) -> Optional[int]:
    """Return the index of the story enclosing `time`, picking the most specific (shortest) if overlapping."""
    candidates = []
    for index, story in enumerate(canvas.stories):
        if story.start <= time <= story.end:
            candidates.append((story.end - story.start, index))
    if candidates:
        candidates.sort()
        return candidates[0][1]
    return None


def is_near_playhead(canvas: Any, pos_x: float, width: int) -> bool:
    """Check if pos_x is within grab distance of the active playhead cursor."""
    cursor_x = canvas.time_to_x(canvas.position, width)
    return abs(pos_x - cursor_x) <= canvas.CURSOR_GRAB_THRESHOLD

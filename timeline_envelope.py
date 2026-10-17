"""Waveform envelope data structure and multi-resolution pyramid downsampling."""
from __future__ import annotations

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False


class WaveformEnvelope(list):
    """Subclass of list holding waveform peaks and precomputed multi-resolution pyramid levels."""
    def __init__(self, iterable=None, levels=None):
        super().__init__(iterable or [])
        self.waveform_levels = levels or []


def build_waveform_pyramid(peaks):
    """Generate a multi-resolution downsampling pyramid for peaks using vectorized operations.
    
    Each level downsamples the previous level by 4x, allowing instantaneous O(1) viewport-scaled
    waveform rendering on long audio files (>60 min) without UI thread lag.
    """
    if not peaks:
        return []
    if HAVE_NUMPY and np is not None:
        try:
            arr = np.asarray(peaks, dtype=np.float32)
            levels = [arr]
            curr = arr
            while len(curr) > 4:
                pad = (4 - (len(curr) % 4)) % 4
                if pad:
                    curr_padded = np.pad(curr, (0, pad), mode="edge")
                else:
                    curr_padded = curr
                curr = np.max(curr_padded.reshape(-1, 4), axis=1)
                levels.append(curr)
            return levels
        except Exception:
            pass

    # Pure Python fallback
    levels = [list(peaks)]
    curr = levels[0]
    while len(curr) > 4:
        next_level = [max(curr[i:i + 4]) for i in range(0, len(curr), 4)]
        levels.append(next_level)
        curr = next_level
    return levels

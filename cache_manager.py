"""Radio & TV Segmenter — Cache management, disk usage scanning, and purging utilities.

Provides utilities for:
- Formatting byte quantities into human-readable representations.
- Scanning disk usage across video thumbnails, waveform peak envelopes (.peaks), and temporary audio extractions.
- Background worker for purging stale thumbnail caches older than a specified age.
- Safe deletion and cache purging functions.
- The PySide6 ClearCacheDialog for graphical cache inspection and cleanup.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

try:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )
    from cache_workers import CacheScanWorker, CachePurgeWorker, detach_cache_worker
except ImportError:
    QDialog = object
    QSettings = None
    CacheScanWorker = None
    CachePurgeWorker = None
    detach_cache_worker = None

from core_utils import get_app_data_dir, format_byte_size


INTERNAL_APP_ID = "RadioTVStorySegmenter"

_ACTIVE_THUMBNAIL_DIRS: set[str] = set()
_ACTIVE_DIRS_LOCK = threading.Lock()


def register_active_thumbnail_dir(path: Path | str | None) -> None:
    """Register an active thumbnail directory so cache cleanup routines will never touch it."""
    if not path:
        return
    try:
        resolved = str(Path(path).resolve())
        with _ACTIVE_DIRS_LOCK:
            _ACTIVE_THUMBNAIL_DIRS.add(resolved)
    except Exception:
        pass


def unregister_active_thumbnail_dir(path: Path | str | None) -> None:
    """Unregister an active thumbnail directory when the project or session closes."""
    if not path:
        return
    try:
        resolved = str(Path(path).resolve())
        with _ACTIVE_DIRS_LOCK:
            _ACTIVE_THUMBNAIL_DIRS.discard(resolved)
    except Exception:
        pass


def get_active_thumbnail_dirs() -> set[str]:
    """Return a copy of currently registered active thumbnail directories."""
    with _ACTIVE_DIRS_LOCK:
        return set(_ACTIVE_THUMBNAIL_DIRS)



def cleanup_old_thumbnail_cache(
    max_age_hours: int = 168,
    active_dir: Path | str | None = None,
    exclude_dirs: list | set | None = None,
    blocking: bool = False,
    base_dir: Path | str | None = None,
) -> threading.Thread | None:
    """Purge temporary thumbnail directories older than max_age_hours in a background thread.
    
    Guards against race conditions and ensures active session thumbnail directories
    are never deleted while a project is open.
    """
    def _worker():
        try:
            base = Path(base_dir) if base_dir is not None else (Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails")
            if not base.exists():
                return
            cutoff = time.time() - (max(0.001, float(max_age_hours)) * 3600)

            # Collect all active thumbnail directories that must be preserved
            active_set: set[str] = set()
            with _ACTIVE_DIRS_LOCK:
                active_set.update(_ACTIVE_THUMBNAIL_DIRS)
            if active_dir:
                try:
                    active_set.add(str(Path(active_dir).resolve()))
                except Exception:
                    pass
            if exclude_dirs:
                for ed in exclude_dirs:
                    if ed:
                        try:
                            active_set.add(str(Path(ed).resolve()))
                        except Exception:
                            pass

            # Inspect active Qt application main window and open projects if present
            try:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    for widget in app.topLevelWidgets():
                        vtd = getattr(widget, "video_thumbnail_dir", None)
                        if vtd:
                            try:
                                active_set.add(str(Path(vtd).resolve()))
                            except Exception:
                                pass
                        af = getattr(widget, "audio_file", None)
                        if af:
                            try:
                                from background_workers import get_video_thumbnail_cache_dir
                                cache_d = get_video_thumbnail_cache_dir(af)
                                if cache_d:
                                    active_set.add(str(Path(cache_d).resolve()))
                            except Exception:
                                pass
            except Exception:
                pass

            try:
                subdirs = list(base.iterdir())
            except (FileNotFoundError, OSError):
                return

            for sub in subdirs:
                try:
                    if not sub.is_dir():
                        continue

                    # Guard: Check if directory is in active set or is a subpath of an active directory
                    try:
                        resolved_sub = str(sub.resolve())
                    except (FileNotFoundError, OSError):
                        continue

                    is_active = False
                    for active_p in active_set:
                        if resolved_sub == active_p or active_p.startswith(resolved_sub) or resolved_sub.startswith(active_p):
                            is_active = True
                            break
                    if is_active:
                        continue

                    # Check modification time of the directory and any contained files
                    try:
                        mtime = sub.stat().st_mtime
                    except (FileNotFoundError, OSError):
                        continue

                    if mtime >= cutoff:
                        continue

                    # Deep check: ensure no recently generated thumbnails exist inside
                    has_recent_file = False
                    try:
                        for child in sub.iterdir():
                            try:
                                if child.stat().st_mtime >= cutoff:
                                    has_recent_file = True
                                    break
                            except (FileNotFoundError, OSError):
                                pass
                    except (FileNotFoundError, OSError):
                        continue

                    if has_recent_file:
                        continue

                    # Atomic rename before rmtree to eliminate race conditions with concurrent access
                    tombstone = sub.with_name(f"{sub.name}.deleting_{os.getpid()}_{time.time_ns()}")
                    try:
                        sub.rename(tombstone)
                        target_to_delete = tombstone
                    except (FileNotFoundError, PermissionError, OSError):
                        target_to_delete = sub

                    shutil.rmtree(target_to_delete, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass

    if blocking:
        _worker()
        return None
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


_TMP_AUDIO_WAV_PREFIXES = ("prs_tmp_", "rtvs_tmp_", "prs_extract_", "rtvs_diarization_")
_TMP_AUDIO_ANY_PREFIXES = ("rtvs_translate_", "rtvs_wp_")
_FILE_SUFFIX_HINTS = {
    ".rtvs", ".json", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".oga",
    ".opus", ".wma", ".aiff", ".aif", ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm",
}


def _is_temp_audio_workfile(name: str) -> bool:
    """Return True if *name* matches any temporary audio/translation/wp scratch file pattern."""
    low = name.lower()
    if low.startswith(_TMP_AUDIO_ANY_PREFIXES):
        return True
    return low.endswith(".wav") and low.startswith(_TMP_AUDIO_WAV_PREFIXES)


def _is_network_path(path: Path | str | None) -> bool:
    """Return True if *path* points to a UNC share or mapped network drive."""
    if not path:
        return False
    try:
        from thumbnail_workers import is_network_path as _tw_is_network_path
        return bool(_tw_is_network_path(path))
    except Exception:
        pass
    raw = str(path).strip()
    if not raw:
        return False
    if raw.startswith("\\\\") or raw.startswith("//"):
        return True
    if sys.platform == "win32":
        try:
            drive, _ = os.path.splitdrive(os.path.abspath(raw))
            if drive.startswith("\\\\") or drive.startswith("//"):
                return True
            if len(drive) == 2 and drive[1] == ":":
                import ctypes
                return ctypes.windll.kernel32.GetDriveTypeW(drive + "\\") == 4
        except Exception:
            pass
    return False


def _norm_dedup_key(path_str: str) -> str:
    return os.path.normcase(os.path.abspath(path_str))


def _resolve_local_search_dirs(raw_dirs, skip_network: bool = True, cancel_check=None) -> list[Path]:
    """Deduplicate and resolve candidate project directories without touching network shares."""
    search_dirs: list[Path] = []
    seen_dirs: set[str] = set()
    for raw in raw_dirs or ():
        if cancel_check is not None and cancel_check():
            break
        if not raw:
            continue
        raw_str = str(raw).strip()
        if not raw_str:
            continue
        if skip_network and _is_network_path(raw_str):
            continue
        try:
            cand = os.path.abspath(raw_str)
            _, ext = os.path.splitext(cand)
            if ext.lower() in _FILE_SUFFIX_HINTS:
                cand = os.path.dirname(cand)
            key = os.path.normcase(cand)
            if key in seen_dirs:
                continue
            if os.path.isfile(cand):
                cand = os.path.dirname(cand)
                key = os.path.normcase(cand)
                if key in seen_dirs:
                    continue
            if os.path.isdir(cand):
                seen_dirs.add(key)
                search_dirs.append(Path(cand))
        except Exception:
            pass
    return search_dirs


def _walk_cache_tree(
    root_dir: Path,
    suffix: str | None = None,
    recursive: bool = True,
    seen: set[str] | None = None,
    delete: bool = False,
    remove_root: bool = False,
    cancel_check=None,
) -> tuple[int, int]:
    """Iterative os.scandir() walker that counts or deletes matching files, returning (count, bytes)."""
    count = 0
    total_bytes = 0
    root_str = str(root_dir)
    if not os.path.isdir(root_str):
        return 0, 0
    stack = [root_str]
    while stack:
        if cancel_check is not None and cancel_check():
            return count, total_bytes
        curr = stack.pop()
        try:
            with os.scandir(curr) as it:
                entries = list(it) if delete else it
                for idx, entry in enumerate(entries):
                    if cancel_check is not None and (idx & 63) == 0 and cancel_check():
                        return count, total_bytes
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if recursive:
                                stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            if suffix is not None and not entry.name.lower().endswith(suffix):
                                continue
                            if seen is not None:
                                key = _norm_dedup_key(entry.path)
                                if key in seen:
                                    continue
                                seen.add(key)
                            sz = 0
                            try:
                                sz = entry.stat(follow_symlinks=False).st_size
                            except Exception:
                                pass
                            if delete:
                                os.unlink(entry.path)
                            total_bytes += sz
                            count += 1
                    except Exception:
                        pass
        except Exception:
            pass
    if delete and remove_root and (cancel_check is None or not cancel_check()):
        shutil.rmtree(root_dir, ignore_errors=True)
    return count, total_bytes


def collect_settings_project_dirs() -> list:
    """Collect candidate project directories from QSettings on the GUI thread."""
    p_candidates = []
    if QSettings is None:
        return p_candidates
    try:
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        for key in ("default_project_directory", "last_saved_project_path", "last_open_directory"):
            val = settings.value(key)
            if val:
                p_candidates.append(val)
        recents = settings.value("recent_projects")
        if recents:
            if isinstance(recents, str):
                try:
                    recents = json.loads(recents)
                except Exception:
                    recents = [recents]
            if isinstance(recents, (list, tuple)):
                p_candidates.extend(recents)
    except Exception:
        pass
    return p_candidates


def get_cache_disk_usage(
    project_dirs=None,
    include_global_caches: bool = True,
    include_settings_dirs: bool = True,
    cancel_check=None,
    skip_network_dirs: bool = True,
) -> dict:
    """Scan and compute disk usage for all temporary cache stores across appdata, temp dirs, and project folders.
    
    Returns a dict with statistics for:
      - 'thumbnails': {'label': 'Video Thumbnails & Filmstrips', 'path': Path, 'count': int, 'bytes': int}
      - 'waveforms': {'label': 'Audio Waveform Peaks', 'path': Path, 'count': int, 'bytes': int}
      - 'audio_extracts': {'label': 'Temporary Audio Workfiles', 'path': Path, 'count': int, 'bytes': int}
      - 'total_bytes': int
      - 'total_files': int
    """
    stats = {}

    def _cancelled() -> bool:
        if cancel_check is None:
            return False
        try:
            return bool(cancel_check())
        except Exception:
            return False

    # Auto-populate search dirs from QSettings if requested
    p_candidates = list(project_dirs or [])
    if include_settings_dirs:
        p_candidates.extend(collect_settings_project_dirs())

    search_dirs = _resolve_local_search_dirs(
        p_candidates,
        skip_network=skip_network_dirs,
        cancel_check=_cancelled,
    )

    # 1. Video Thumbnails
    thumb_bytes = 0
    thumb_files = 0
    default_thumb_path = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
    thumb_locations = (
        [default_thumb_path, get_app_data_dir() / "cache" / "thumbnails"]
        if include_global_caches else []
    )
    for pd in search_dirs:
        t_cand = pd / ".cache" / "thumbnails"
        if t_cand not in thumb_locations:
            thumb_locations.append(t_cand)

    seen_thumb_files: set[str] = set()
    for thumb_dir in thumb_locations:
        if _cancelled():
            break
        cnt, bts = _walk_cache_tree(thumb_dir, recursive=True, seen=seen_thumb_files, cancel_check=_cancelled)
        thumb_files += cnt
        thumb_bytes += bts

    stats["thumbnails"] = {
        "label": "Video Thumbnails & Filmstrips",
        "path": thumb_locations[0] if thumb_locations else default_thumb_path,
        "count": thumb_files,
        "bytes": thumb_bytes,
    }

    # 2. Waveform Peaks Cache (AppData + Project .cache/peaks/ + legacy adjacent .peaks)
    peaks_bytes = 0
    peaks_files = 0
    default_peaks_path = get_app_data_dir() / "cache" / "peaks" if include_global_caches else Path(tempfile.gettempdir())
    peak_locations = [default_peaks_path] if include_global_caches else []
    for pd in search_dirs:
        p_cand = pd / ".cache" / "peaks"
        if p_cand not in peak_locations:
            peak_locations.append(p_cand)

    seen_peak_files: set[str] = set()
    for peaks_dir in peak_locations:
        if _cancelled():
            break
        cnt, bts = _walk_cache_tree(peaks_dir, suffix=".peaks", recursive=True, seen=seen_peak_files, cancel_check=_cancelled)
        peaks_files += cnt
        peaks_bytes += bts

    # Scan any legacy .peaks directly in app cache root or active project folders
    if include_global_caches and not _cancelled():
        cnt, bts = _walk_cache_tree(get_app_data_dir() / "cache", suffix=".peaks", recursive=False, seen=seen_peak_files, cancel_check=_cancelled)
        peaks_files += cnt
        peaks_bytes += bts

    for pd in search_dirs:
        if _cancelled():
            break
        cnt, bts = _walk_cache_tree(pd, suffix=".peaks", recursive=False, seen=seen_peak_files, cancel_check=_cancelled)
        peaks_files += cnt
        peaks_bytes += bts

    stats["waveforms"] = {
        "label": "Audio Waveform Peaks",
        "path": peak_locations[0] if peak_locations else default_peaks_path,
        "count": peaks_files,
        "bytes": peaks_bytes,
    }

    # 3. Temporary Audio Extracts & Scratch Workfiles
    audio_bytes = 0
    audio_files = 0
    default_audio_path = Path(tempfile.gettempdir()) / "prs_audio_extracts"
    audio_locations = (
        [
            default_audio_path,
            get_app_data_dir() / "cache" / "audio",
            get_app_data_dir() / "cache" / "temp",
        ]
        if include_global_caches else []
    )
    for pd in search_dirs:
        a_cand = pd / ".cache" / "audio"
        if a_cand not in audio_locations:
            audio_locations.append(a_cand)

    seen_audio_files: set[str] = set()
    for audio_dir in audio_locations:
        if _cancelled():
            break
        cnt, bts = _walk_cache_tree(audio_dir, recursive=True, seen=seen_audio_files, cancel_check=_cancelled)
        audio_files += cnt
        audio_bytes += bts

    if include_global_caches and not _cancelled():
        temp_dir_str = tempfile.gettempdir()
        try:
            with os.scandir(temp_dir_str) as it:
                for idx, entry in enumerate(it):
                    if (idx & 127) == 0 and _cancelled():
                        break
                    if _is_temp_audio_workfile(entry.name):
                        try:
                            if entry.is_file(follow_symlinks=False):
                                key = _norm_dedup_key(entry.path)
                                if key not in seen_audio_files:
                                    seen_audio_files.add(key)
                                    audio_files += 1
                                    audio_bytes += entry.stat(follow_symlinks=False).st_size
                        except Exception:
                            pass
        except Exception:
            pass

    stats["audio_extracts"] = {
        "label": "Temporary Audio Workfiles",
        "path": audio_locations[0] if audio_locations else default_audio_path,
        "count": audio_files,
        "bytes": audio_bytes,
    }

    stats["total_bytes"] = thumb_bytes + peaks_bytes + audio_bytes
    stats["total_files"] = thumb_files + peaks_files + audio_files
    return stats


def purge_caches(
    clear_thumbnails=True,
    clear_waveforms=True,
    clear_audio_extracts=True,
    project_dirs=None,
    include_global_caches: bool = True,
    cancel_check=None,
    skip_network_dirs: bool = True,
) -> tuple[int, int]:
    """Purge requested cache stores safely from disk.
    
    Returns:
        (files_deleted, bytes_freed)
    """
    def _cancelled() -> bool:
        if cancel_check is None:
            return False
        try:
            return bool(cancel_check())
        except Exception:
            return False

    freed_bytes = 0
    freed_files = 0
    search_dirs = _resolve_local_search_dirs(
        project_dirs,
        skip_network=skip_network_dirs,
        cancel_check=_cancelled,
    )

    if clear_thumbnails and not _cancelled():
        thumb_locations = (
            [
                Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails",
                get_app_data_dir() / "cache" / "thumbnails",
            ]
            if include_global_caches else []
        )
        for pd in search_dirs:
            t_cand = pd / ".cache" / "thumbnails"
            if t_cand not in thumb_locations:
                thumb_locations.append(t_cand)

        for thumb_dir in thumb_locations:
            if _cancelled():
                return freed_files, freed_bytes
            cnt, bts = _walk_cache_tree(thumb_dir, recursive=True, delete=True, remove_root=True, cancel_check=_cancelled)
            freed_files += cnt
            freed_bytes += bts

    if clear_waveforms and not _cancelled():
        peak_locations = (
            [get_app_data_dir() / "cache" / "peaks"]
            if include_global_caches else []
        )
        for pd in search_dirs:
            p_cand = pd / ".cache" / "peaks"
            if p_cand not in peak_locations:
                peak_locations.append(p_cand)

        for peaks_dir in peak_locations:
            if _cancelled():
                return freed_files, freed_bytes
            cnt, bts = _walk_cache_tree(peaks_dir, suffix=".peaks", recursive=True, delete=True, remove_root=True, cancel_check=_cancelled)
            freed_files += cnt
            freed_bytes += bts

        for pd in search_dirs:
            if _cancelled():
                return freed_files, freed_bytes
            cnt, bts = _walk_cache_tree(pd, suffix=".peaks", recursive=False, delete=True, remove_root=False, cancel_check=_cancelled)
            freed_files += cnt
            freed_bytes += bts

    if clear_audio_extracts and not _cancelled():
        audio_locations = (
            [
                Path(tempfile.gettempdir()) / "prs_audio_extracts",
                get_app_data_dir() / "cache" / "audio",
                get_app_data_dir() / "cache" / "temp",
            ]
            if include_global_caches else []
        )
        for pd in search_dirs:
            a_cand = pd / ".cache" / "audio"
            if a_cand not in audio_locations:
                audio_locations.append(a_cand)
        for audio_dir in audio_locations:
            if _cancelled():
                return freed_files, freed_bytes
            cnt, bts = _walk_cache_tree(audio_dir, recursive=True, delete=True, remove_root=True, cancel_check=_cancelled)
            freed_files += cnt
            freed_bytes += bts
        if include_global_caches and not _cancelled():
            temp_dir_str = tempfile.gettempdir()
            try:
                with os.scandir(temp_dir_str) as it:
                    for idx, entry in enumerate(it):
                        if (idx & 127) == 0 and _cancelled():
                            return freed_files, freed_bytes
                        if _is_temp_audio_workfile(entry.name):
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    sz = entry.stat(follow_symlinks=False).st_size
                                    os.unlink(entry.path)
                                    freed_bytes += sz
                                    freed_files += 1
                            except Exception:
                                pass
            except Exception:
                pass

    return freed_files, freed_bytes


class ClearCacheDialog(QDialog):
    """Dialog for inspecting disk cache sizes and clearing temporary data."""

    def __init__(
        self,
        parent=None,
        language="en",
        project_dirs=None,
        auto_refresh=True,
        include_global_caches: bool = True,
        include_settings_dirs: bool = True,
    ):
        super().__init__(parent)
        self.language = language
        self.is_es = (language == "es")
        self.project_dirs = list(project_dirs) if project_dirs else []
        self._include_global_caches = bool(include_global_caches)
        self._include_settings_dirs = bool(include_settings_dirs)
        self._active_worker = None
        self._workers = set()
        self._is_closing = False
        self._worker_gen = 0
        self.setWindowTitle("Limpiar caché temporal" if self.is_es else "Clear Temporary Cache")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        if auto_refresh:
            self.refresh_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        desc_text = (
            "Libere espacio en disco eliminando miniaturas de video en caché, picos de forma de onda y archivos de audio temporales. Los archivos necesarios se regenerarán automáticamente al abrirlos."
            if self.is_es else
            "Free up disk space by clearing cached video thumbnails, waveform peak envelopes, and temporary audio files. Active projects will recompute cache files on demand."
        )
        desc_lbl = QLabel(desc_text)
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        group = QGroupBox("Cachés disponibles" if self.is_es else "Cached Data Stores")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        self.chk_thumbs = QCheckBox("Miniaturas y tiras de película de video" if self.is_es else "Video Thumbnails & Filmstrips")
        self.chk_thumbs.setChecked(True)
        self.lbl_thumbs_size = QLabel("...")
        self.lbl_thumbs_size.setStyleSheet("color: #888888; font-size: 11px;")
        row_thumbs = QHBoxLayout()
        row_thumbs.addWidget(self.chk_thumbs)
        row_thumbs.addStretch()
        row_thumbs.addWidget(self.lbl_thumbs_size)
        group_layout.addLayout(row_thumbs)

        self.chk_waveforms = QCheckBox("Picos de forma de onda de audio (.peaks)" if self.is_es else "Audio Waveform Peak Envelopes (.peaks)")
        self.chk_waveforms.setChecked(True)
        self.lbl_waveforms_size = QLabel("...")
        self.lbl_waveforms_size.setStyleSheet("color: #888888; font-size: 11px;")
        row_waves = QHBoxLayout()
        row_waves.addWidget(self.chk_waveforms)
        row_waves.addStretch()
        row_waves.addWidget(self.lbl_waveforms_size)
        group_layout.addLayout(row_waves)

        self.chk_audio = QCheckBox("Archivos de trabajo de audio temporales" if self.is_es else "Temporary Audio Extraction Workfiles")
        self.chk_audio.setChecked(True)
        self.lbl_audio_size = QLabel("...")
        self.lbl_audio_size.setStyleSheet("color: #888888; font-size: 11px;")
        row_audio = QHBoxLayout()
        row_audio.addWidget(self.chk_audio)
        row_audio.addStretch()
        row_audio.addWidget(self.lbl_audio_size)
        group_layout.addLayout(row_audio)

        layout.addWidget(group)

        total_box = QFrame()
        total_box.setFrameShape(QFrame.StyledPanel)
        total_layout = QHBoxLayout(total_box)
        total_layout.setContentsMargins(10, 8, 10, 8)

        self.lbl_total_label = QLabel("Espacio total en caché:" if self.is_es else "Total Temporary Cache Size:")
        font = self.lbl_total_label.font()
        font.setBold(True)
        self.lbl_total_label.setFont(font)

        self.lbl_total_val = QLabel("0 B (0 archivos)" if self.is_es else "0 B (0 files)")
        self.lbl_total_val.setFont(font)

        total_layout.addWidget(self.lbl_total_label)
        total_layout.addStretch()
        total_layout.addWidget(self.lbl_total_val)
        layout.addWidget(total_box)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #2e7d32; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_clear_all = QPushButton("Limpiar toda la caché" if self.is_es else "Clear All Caches")
        self.btn_clear_all.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.btn_clear_all.clicked.connect(self._on_clear_all)

        self.btn_clear_sel = QPushButton("Limpiar selección" if self.is_es else "Clear Selected")
        self.btn_clear_sel.clicked.connect(self._on_clear_selected)

        self.btn_close = QPushButton("Cerrar" if self.is_es else "Close")
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_clear_all)
        btn_layout.addWidget(self.btn_clear_sel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _build_scan_dirs(self) -> list:
        dirs = list(self.project_dirs)
        if self._include_settings_dirs:
            dirs.extend(collect_settings_project_dirs())
        return dirs

    def _set_busy_state(self, busy: bool, status_text: str | None = None, is_error: bool = False):
        for widget in (self.chk_thumbs, self.chk_waveforms, self.chk_audio):
            widget.setEnabled(not busy)
        if busy:
            self.btn_clear_all.setEnabled(False)
            self.btn_clear_sel.setEnabled(False)
        if status_text is not None:
            if busy:
                self.lbl_status.setStyleSheet("color: #888888; font-weight: normal;")
            elif is_error:
                self.lbl_status.setStyleSheet("color: #c62828; font-weight: bold;")
            else:
                self.lbl_status.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self.lbl_status.setText(status_text)

    def _apply_stats(self, stats: dict):
        t_stat = stats["thumbnails"]
        w_stat = stats["waveforms"]
        a_stat = stats["audio_extracts"]

        self.lbl_thumbs_size.setText(
            f"{format_byte_size(t_stat['bytes'])} ({t_stat['count']} {'archivos' if self.is_es else 'files'})"
        )
        self.lbl_waveforms_size.setText(
            f"{format_byte_size(w_stat['bytes'])} ({w_stat['count']} {'archivos' if self.is_es else 'files'})"
        )
        self.lbl_audio_size.setText(
            f"{format_byte_size(a_stat['bytes'])} ({a_stat['count']} {'archivos' if self.is_es else 'files'})"
        )

        total_bytes = stats["total_bytes"]
        total_files = stats["total_files"]
        self.lbl_total_val.setText(
            f"{format_byte_size(total_bytes)} ({total_files} {'archivos' if self.is_es else 'files'})"
        )

        has_data = total_bytes > 0 or total_files > 0
        self.btn_clear_all.setEnabled(has_data)
        self.btn_clear_sel.setEnabled(has_data)

    def _start_worker(self, worker):
        if self._active_worker is not None:
            detach_cache_worker(self._active_worker)
            self._workers.discard(self._active_worker)
            self._active_worker = None
        self._active_worker = worker
        self._workers.add(worker)
        worker.finished.connect(lambda w=worker: self._workers.discard(w))
        worker.start()

    def refresh_stats(self):
        if self._is_closing or CacheScanWorker is None:
            return
        self._worker_gen += 1
        gen = self._worker_gen
        scanning_lbl = "Escaneando..." if self.is_es else "Scanning..."
        self.lbl_thumbs_size.setText(scanning_lbl)
        self.lbl_waveforms_size.setText(scanning_lbl)
        self.lbl_audio_size.setText(scanning_lbl)
        self.lbl_total_val.setText(scanning_lbl)
        self._set_busy_state(
            True,
            "Escaneando cachés temporales..." if self.is_es else "Scanning temporary caches...",
        )

        worker = CacheScanWorker(
            project_dirs=self._build_scan_dirs(),
            include_global_caches=self._include_global_caches,
            include_settings_dirs=False,
            parent=self,
        )
        worker.finished_scan.connect(lambda stats, g=gen: self._on_scan_finished(stats, g))
        worker.failed_scan.connect(lambda err, g=gen: self._on_worker_error(err, g))
        self._start_worker(worker)

    def _on_scan_finished(self, stats: dict, gen: int):
        if self._is_closing or gen != self._worker_gen:
            return
        self._active_worker = None
        self._set_busy_state(False, "")
        self._apply_stats(stats)

    def _on_purge_finished(self, files_deleted: int, bytes_freed: int, stats: dict, gen: int):
        if self._is_closing or gen != self._worker_gen:
            return
        self._active_worker = None
        freed_str = format_byte_size(bytes_freed)
        msg = (
            f"Se liberaron exitosamente {freed_str} en {files_deleted} archivos."
            if self.is_es else
            f"Successfully freed {freed_str} across {files_deleted} files."
        )
        self._set_busy_state(False, msg)
        self._apply_stats(stats)

    def _on_worker_error(self, error_msg: str, gen: int):
        if self._is_closing or gen != self._worker_gen:
            return
        self._active_worker = None
        prefix = "Error de caché:" if self.is_es else "Cache operation error:"
        self._set_busy_state(False, f"{prefix} {error_msg}", is_error=True)

    def _cleanup_workers(self):
        self._is_closing = True
        self._worker_gen += 1
        to_detach = list(self._workers)
        if self._active_worker is not None and self._active_worker not in to_detach:
            to_detach.append(self._active_worker)
        self._workers.clear()
        self._active_worker = None
        if detach_cache_worker is not None:
            for w in to_detach:
                detach_cache_worker(w)

    def accept(self):
        self._cleanup_workers()
        super().accept()

    def reject(self):
        self._cleanup_workers()
        super().reject()

    def closeEvent(self, event):
        self._cleanup_workers()
        super().closeEvent(event)

    def _on_clear_all(self):
        self.chk_thumbs.setChecked(True)
        self.chk_waveforms.setChecked(True)
        self.chk_audio.setChecked(True)
        self._do_purge(clear_thumbs=True, clear_waves=True, clear_audio=True)

    def _on_clear_selected(self):
        ct = self.chk_thumbs.isChecked()
        cw = self.chk_waveforms.isChecked()
        ca = self.chk_audio.isChecked()
        if not (ct or cw or ca):
            QMessageBox.information(
                self,
                "Sin selección" if self.is_es else "No Cache Selected",
                "Por favor seleccione al menos una opción de caché para limpiar." if self.is_es else "Please select at least one cache category to clear."
            )
            return
        self._do_purge(clear_thumbs=ct, clear_waves=cw, clear_audio=ca)

    def _do_purge(self, clear_thumbs: bool, clear_waves: bool, clear_audio: bool):
        if self._is_closing or CachePurgeWorker is None:
            return
        if self._active_worker is not None and self._active_worker.isRunning():
            return
        self._worker_gen += 1
        gen = self._worker_gen
        scan_dirs = self._build_scan_dirs()
        self._set_busy_state(
            True,
            "Limpiando cachés seleccionadas..." if self.is_es else "Clearing selected caches...",
        )
        worker = CachePurgeWorker(
            clear_thumbnails=clear_thumbs,
            clear_waveforms=clear_waves,
            clear_audio_extracts=clear_audio,
            purge_project_dirs=scan_dirs,
            scan_project_dirs=scan_dirs,
            include_global_caches=self._include_global_caches,
            include_settings_dirs=False,
            parent=self,
        )
        worker.finished_purge.connect(
            lambda files_del, bytes_freed, stats, g=gen: self._on_purge_finished(files_del, bytes_freed, stats, g)
        )
        worker.failed_purge.connect(lambda err, g=gen: self._on_worker_error(err, g))
        self._start_worker(worker)

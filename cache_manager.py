"""Radio & TV Segmenter — Cache management, disk usage scanning, and purging utilities.

Provides utilities for:
- Formatting byte quantities into human-readable representations.
- Scanning disk usage across video thumbnails, waveform peak envelopes (.peaks), and temporary audio extractions.
- Background worker for purging stale thumbnail caches older than a specified age.
- Safe deletion and cache purging functions.
- The PySide6 ClearCacheDialog for graphical cache inspection and cleanup.
"""

import json
import shutil
import tempfile
import threading
import time
from pathlib import Path

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

from core_utils import get_app_data_dir


INTERNAL_APP_ID = "RadioTVStorySegmenter"


def format_byte_size(size_bytes: int) -> str:
    """Format byte count to human-readable string (e.g. 1.2 MB, 450 KB)."""
    if size_bytes <= 0:
        return "0 B"
    num = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}" if unit in ["MB", "GB", "TB"] else f"{int(num)} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def cleanup_old_thumbnail_cache(max_age_hours: int = 168):
    """Purge temporary thumbnail directories older than max_age_hours in a background thread."""
    def _worker():
        try:
            base = Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails"
            if not base.exists():
                return
            cutoff = time.time() - (max_age_hours * 3600)
            for sub in base.iterdir():
                if sub.is_dir():
                    try:
                        mtime = sub.stat().st_mtime
                        if mtime < cutoff:
                            shutil.rmtree(sub, ignore_errors=True)
                    except Exception:
                        pass
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_cache_disk_usage(project_dirs=None) -> dict:
    """Scan and compute disk usage for all temporary cache stores across appdata, temp dirs, and project folders.
    
    Returns a dict with statistics for:
      - 'thumbnails': {'label': 'Video Thumbnails & Filmstrips', 'path': Path, 'count': int, 'bytes': int}
      - 'waveforms': {'label': 'Audio Waveform Peaks', 'path': Path, 'count': int, 'bytes': int}
      - 'audio_extracts': {'label': 'Temporary Audio Workfiles', 'path': Path, 'count': int, 'bytes': int}
      - 'total_bytes': int
      - 'total_files': int
    """
    stats = {}
    search_dirs = []

    # Auto-populate search dirs from QSettings if not provided
    p_candidates = list(project_dirs or [])
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

    for p in p_candidates:
        if p:
            try:
                pd = Path(p).resolve()
                if pd.is_file():
                    pd = pd.parent
                if pd.exists() and pd not in search_dirs:
                    search_dirs.append(pd)
            except Exception:
                pass

    # 1. Video Thumbnails
    thumb_bytes = 0
    thumb_files = 0
    thumb_locations = [
        Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails",
        get_app_data_dir() / "cache" / "thumbnails",
    ]
    for pd in search_dirs:
        t_cand = pd / ".cache" / "thumbnails"
        if t_cand not in thumb_locations:
            thumb_locations.append(t_cand)

    seen_thumb_files = set()
    for thumb_dir in thumb_locations:
        if thumb_dir.exists() and thumb_dir.is_dir():
            try:
                for p in thumb_dir.rglob("*"):
                    if p.is_file() and str(p.resolve()) not in seen_thumb_files:
                        seen_thumb_files.add(str(p.resolve()))
                        thumb_files += 1
                        try:
                            thumb_bytes += p.stat().st_size
                        except Exception:
                            pass
            except Exception:
                pass

    stats["thumbnails"] = {
        "label": "Video Thumbnails & Filmstrips",
        "path": thumb_locations[0],
        "count": thumb_files,
        "bytes": thumb_bytes,
    }

    # 2. Waveform Peaks Cache (AppData + Project .cache/peaks/ + legacy adjacent .peaks)
    peaks_bytes = 0
    peaks_files = 0
    peak_locations = [
        get_app_data_dir() / "cache" / "peaks",
    ]
    for pd in search_dirs:
        p_cand = pd / ".cache" / "peaks"
        if p_cand not in peak_locations:
            peak_locations.append(p_cand)

    seen_peak_files = set()
    for peaks_dir in peak_locations:
        if peaks_dir.exists() and peaks_dir.is_dir():
            try:
                for p in peaks_dir.rglob("*.peaks"):
                    if p.is_file() and str(p.resolve()) not in seen_peak_files:
                        seen_peak_files.add(str(p.resolve()))
                        peaks_files += 1
                        try:
                            peaks_bytes += p.stat().st_size
                        except Exception:
                            pass
            except Exception:
                pass

    # Scan any legacy .peaks directly in app cache root or active project folders
    cache_root = get_app_data_dir() / "cache"
    if cache_root.exists() and cache_root.is_dir():
        try:
            for p in cache_root.glob("*.peaks"):
                if p.is_file() and str(p.resolve()) not in seen_peak_files:
                    seen_peak_files.add(str(p.resolve()))
                    peaks_files += 1
                    try:
                        peaks_bytes += p.stat().st_size
                    except Exception:
                        pass
        except Exception:
            pass

    for pd in search_dirs:
        try:
            for p in pd.glob("*.peaks"):
                if p.is_file() and str(p.resolve()) not in seen_peak_files:
                    seen_peak_files.add(str(p.resolve()))
                    peaks_files += 1
                    try:
                        peaks_bytes += p.stat().st_size
                    except Exception:
                        pass
        except Exception:
            pass

    stats["waveforms"] = {
        "label": "Audio Waveform Peaks",
        "path": peak_locations[0],
        "count": peaks_files,
        "bytes": peaks_bytes,
    }

    # 3. Temporary Audio Extracts & Scratch Workfiles
    audio_bytes = 0
    audio_files = 0
    audio_locations = [
        Path(tempfile.gettempdir()) / "prs_audio_extracts",
        get_app_data_dir() / "cache" / "audio",
        get_app_data_dir() / "cache" / "temp",
    ]
    for pd in search_dirs:
        a_cand = pd / ".cache" / "audio"
        if a_cand not in audio_locations:
            audio_locations.append(a_cand)
    for audio_dir in audio_locations:
        if audio_dir.exists() and audio_dir.is_dir():
            try:
                for p in audio_dir.rglob("*"):
                    if p.is_file():
                        audio_files += 1
                        try:
                            audio_bytes += p.stat().st_size
                        except Exception:
                            pass
            except Exception:
                pass
    temp_dir = Path(tempfile.gettempdir())
    try:
        for pat in ("prs_tmp_*.wav", "rtvs_tmp_*.wav", "prs_extract_*.wav", "rtvs_diarization_*.wav", "rtvs_translate_*", "rtvs_wp_*"):
            for p in temp_dir.glob(pat):
                if p.is_file():
                    audio_files += 1
                    try:
                        audio_bytes += p.stat().st_size
                    except Exception:
                        pass
    except Exception:
        pass

    stats["audio_extracts"] = {
        "label": "Temporary Audio Workfiles",
        "path": audio_locations[0],
        "count": audio_files,
        "bytes": audio_bytes,
    }

    stats["total_bytes"] = thumb_bytes + peaks_bytes + audio_bytes
    stats["total_files"] = thumb_files + peaks_files + audio_files
    return stats


def purge_caches(clear_thumbnails=True, clear_waveforms=True, clear_audio_extracts=True, project_dirs=None) -> tuple[int, int]:
    """Purge requested cache stores safely from disk.
    
    Returns:
        (files_deleted, bytes_freed)
    """
    freed_bytes = 0
    freed_files = 0
    search_dirs = []
    if project_dirs:
        for p in project_dirs:
            if p:
                try:
                    pd = Path(p).resolve()
                    if pd.is_file():
                        pd = pd.parent
                    if pd.exists() and pd not in search_dirs:
                        search_dirs.append(pd)
                except Exception:
                    pass

    if clear_thumbnails:
        thumb_locations = [
            Path(tempfile.gettempdir()) / "radio_tv_story_segmenter_thumbnails",
            get_app_data_dir() / "cache" / "thumbnails",
        ]
        for pd in search_dirs:
            t_cand = pd / ".cache" / "thumbnails"
            if t_cand not in thumb_locations:
                thumb_locations.append(t_cand)

        for thumb_dir in thumb_locations:
            if thumb_dir.exists():
                try:
                    for p in list(thumb_dir.rglob("*")):
                        if p.is_file():
                            try:
                                sz = p.stat().st_size
                                p.unlink(missing_ok=True)
                                freed_bytes += sz
                                freed_files += 1
                            except Exception:
                                pass
                    shutil.rmtree(thumb_dir, ignore_errors=True)
                except Exception:
                    pass

    if clear_waveforms:
        peak_locations = [
            get_app_data_dir() / "cache" / "peaks",
        ]
        for pd in search_dirs:
            p_cand = pd / ".cache" / "peaks"
            if p_cand not in peak_locations:
                peak_locations.append(p_cand)

        for peaks_dir in peak_locations:
            if peaks_dir.exists():
                try:
                    for p in list(peaks_dir.glob("*.peaks")):
                        if p.is_file():
                            try:
                                sz = p.stat().st_size
                                p.unlink(missing_ok=True)
                                freed_bytes += sz
                                freed_files += 1
                            except Exception:
                                pass
                    shutil.rmtree(peaks_dir, ignore_errors=True)
                except Exception:
                    pass

        for pd in search_dirs:
            try:
                for p in list(pd.glob("*.peaks")):
                    if p.is_file():
                        try:
                            sz = p.stat().st_size
                            p.unlink(missing_ok=True)
                            freed_bytes += sz
                            freed_files += 1
                        except Exception:
                            pass
            except Exception:
                pass

    if clear_audio_extracts:
        audio_locations = [
            Path(tempfile.gettempdir()) / "prs_audio_extracts",
            get_app_data_dir() / "cache" / "audio",
            get_app_data_dir() / "cache" / "temp",
        ]
        for audio_dir in audio_locations:
            if audio_dir.exists():
                try:
                    for p in list(audio_dir.rglob("*")):
                        if p.is_file():
                            try:
                                sz = p.stat().st_size
                                p.unlink(missing_ok=True)
                                freed_bytes += sz
                                freed_files += 1
                            except Exception:
                                pass
                    shutil.rmtree(audio_dir, ignore_errors=True)
                except Exception:
                    pass
        temp_dir = Path(tempfile.gettempdir())
        try:
            for pat in ("prs_tmp_*.wav", "rtvs_tmp_*.wav", "prs_extract_*.wav", "rtvs_diarization_*.wav", "rtvs_translate_*", "rtvs_wp_*"):
                for p in list(temp_dir.glob(pat)):
                    if p.is_file():
                        try:
                            sz = p.stat().st_size
                            p.unlink(missing_ok=True)
                            freed_bytes += sz
                            freed_files += 1
                        except Exception:
                            pass
        except Exception:
            pass

    return freed_files, freed_bytes


class ClearCacheDialog(QDialog):
    """Dialog for inspecting disk cache sizes and clearing temporary data."""

    def __init__(self, parent=None, language="en", project_dirs=None):
        super().__init__(parent)
        self.language = language
        self.is_es = (language == "es")
        self.project_dirs = project_dirs or []
        self.setWindowTitle("Limpiar caché temporal" if self.is_es else "Clear Temporary Cache")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
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

    def refresh_stats(self):
        stats = get_cache_disk_usage(project_dirs=self.project_dirs)
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
        files_deleted, bytes_freed = purge_caches(
            clear_thumbnails=clear_thumbs,
            clear_waveforms=clear_waves,
            clear_audio_extracts=clear_audio,
            project_dirs=self.project_dirs,
        )
        self.refresh_stats()
        freed_str = format_byte_size(bytes_freed)
        msg = (
            f"Se liberaron exitosamente {freed_str} en {files_deleted} archivos."
            if self.is_es else
            f"Successfully freed {freed_str} across {files_deleted} files."
        )
        self.lbl_status.setText(msg)

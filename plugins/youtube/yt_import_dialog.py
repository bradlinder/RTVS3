"""Qt Dialogs for importing existing YouTube videos, re-downloading archived sources, and updating yt-dlp.

Strict Single Responsibility: Qt presentation and project-state wiring only.
All yt-dlp execution lives in yt_dlp_runner.py; background QThreads live in yt_import_workers.py.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    CollapsibleSection,
    ProjectMetadataDict,
    Story,
    format_time,
)
from remote_media_cache import (
    RemoteMediaCacheManager,
    build_remote_media_source_record,
    format_bytes_human,
    make_cache_key,
)
from remote_media_cache_dialog import get_configured_cache_cap_gb
from plugins.youtube.yt_dlp_runner import (
    ALLOWED_COOKIE_BROWSERS,
    DEFAULT_YOUTUBE_QUALITY,
    YOUTUBE_QUALITY_PRESETS,
    build_youtube_project_stem,
    extract_youtube_id_strict,
    find_yt_dlp_binary,
    get_yt_dlp_version,
    normalize_cookie_browser,
    normalize_quality_preset,
)
from plugins.youtube.yt_import_workers import (
    YouTubeDownloadWorker,
    YouTubeProbeWorker,
    YtDlpInstallWorker,
)


def _trim_youtube_description_for_excerpt(description: str, max_chars: int = 420) -> str:
    """Extract a clean short summary from a YouTube description for the project excerpt."""
    raw = str(description or "").strip()
    if not raw:
        return ""
    # Drop chapter lists or URL-only lines when pulling the leading summary paragraph
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    chosen = paragraphs[0] if paragraphs else raw
    if len(chosen) > max_chars:
        chosen = chosen[: max_chars - 3].rstrip() + "..."
    return chosen


def populate_project_from_youtube_import(
    main_window: Any,
    video_meta: Dict[str, Any],
    file_path: Path | str,
    quality_preset: str,
    cache_key: str,
    import_chapters: bool = False,
    existing_wp_url: str = "",
) -> None:
    """Populate project metadata, WordPress YouTube embed state, and optional chapters."""
    if not main_window:
        return

    proj_meta = getattr(main_window, "project_metadata", None)
    if not isinstance(proj_meta, dict):
        proj_meta = ProjectMetadataDict()
        main_window.project_metadata = proj_meta

    vid = str(video_meta.get("video_id") or "").strip()
    canonical_url = str(video_meta.get("canonical_url") or "").strip()
    title = str(video_meta.get("title") or "").strip()
    description = str(video_meta.get("description") or "").strip()
    upload_date = str(video_meta.get("upload_date") or "").strip()
    stem = str(video_meta.get("suggested_project_stem") or build_youtube_project_stem(title, upload_date, vid))
    fp = Path(file_path)

    est_sizes = video_meta.get("size_estimates") if isinstance(video_meta.get("size_estimates"), dict) else {}
    est_bytes = int(est_sizes.get(quality_preset, 0) or 0)
    if est_bytes <= 0 and fp.exists():
        try:
            est_bytes = int(fp.stat().st_size)
        except OSError:
            est_bytes = 0

    thumb_url = str(video_meta.get("thumbnail_url") or "").strip()
    proj_meta["remote_media_source"] = build_remote_media_source_record(
        provider="youtube",
        source_url=canonical_url,
        source_id=vid,
        quality_preset=quality_preset,
        cached_filename=fp.name,
        cache_key=cache_key,
        title=title,
        upload_date=upload_date,
        estimated_size_bytes=est_bytes,
        extra={"thumbnail_url": thumb_url} if thumb_url else None,
    )
    proj_meta["suggested_project_stem"] = stem
    if title:
        proj_meta["title"] = title
    excerpt = _trim_youtube_description_for_excerpt(description)
    if excerpt and not proj_meta.get("excerpt"):
        proj_meta["excerpt"] = excerpt

    # Pre-populate WordPress YouTube embed metadata so Full Episode and Stories auto-embed cleanly
    wp_meta = proj_meta.setdefault("wordpress", {})
    if canonical_url:
        wp_meta["youtube_url"] = canonical_url
    if vid:
        wp_meta["youtube_video_id"] = vid
    wp_meta["youtube_apply_all"] = True
    wp_meta["youtube_use_story_time"] = True
    wp_meta.setdefault("include_audio", False)
    if title and not wp_meta.get("title"):
        wp_meta["title"] = title
    if excerpt and not wp_meta.get("excerpt"):
        wp_meta["excerpt"] = excerpt
    if upload_date and not wp_meta.get("publication_date"):
        wp_meta["publication_date"] = upload_date

    clean_wp_url = str(existing_wp_url or "").strip()
    if clean_wp_url:
        wp_meta["export_mode"] = "update_existing"
        wp_meta["existing_post_url"] = clean_wp_url
        wp_meta["replace_existing_audio"] = False
    else:
        wp_meta.setdefault("export_mode", "new_episode")

    # Optionally seed initial stories from YouTube chapters when no stories exist yet
    chapters = video_meta.get("chapters") if isinstance(video_meta.get("chapters"), list) else []
    if import_chapters and chapters:
        existing_stories = getattr(main_window, "stories", None)
        if isinstance(existing_stories, list) and len(existing_stories) == 0:
            seeded: List[Story] = []
            for ch in chapters:
                try:
                    st = float(ch.get("start", 0.0))
                    en = float(ch.get("end", 0.0))
                    ch_title = str(ch.get("title") or "").strip()
                    if en > st and ch_title:
                        story_obj = Story(title=ch_title, start=st, end=en)
                        if canonical_url and vid:
                            story_obj.metadata = dict(getattr(story_obj, "metadata", {}) or {})
                            st_wp = story_obj.metadata.setdefault("wordpress", {})
                            st_wp["youtube_url"] = canonical_url
                            st_wp["youtube_video_id"] = vid
                        seeded.append(story_obj)
                except Exception:
                    continue
            if seeded:
                main_window.stories = seeded
                if hasattr(main_window, "timeline") and hasattr(main_window.timeline, "set_stories"):
                    main_window.timeline.set_stories(seeded)
                if hasattr(main_window, "refresh_story_list"):
                    main_window.refresh_story_list()

    if hasattr(main_window, "redownload_remote_media_action"):
        main_window.redownload_remote_media_action.setEnabled(True)
    if hasattr(main_window, "project_dirty"):
        main_window.project_dirty = True
    if hasattr(main_window, "update_window_title"):
        main_window.update_window_title()


class LoadYouTubeEpisodeDialog(QDialog):
    """Dialog for fetching, configuring, downloading, and opening an existing YouTube video."""

    def __init__(
        self,
        main_window: Any = None,
        parent: Optional[QWidget] = None,
        initial_url: str = "",
        initial_quality: str = "",
        redownload_mode: bool = False,
    ):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.redownload_mode = bool(redownload_mode)
        self.settings = getattr(main_window, "settings_store", None) or QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.cache_manager = RemoteMediaCacheManager()

        self._probe_worker: Optional[YouTubeProbeWorker] = None
        self._download_worker: Optional[YouTubeDownloadWorker] = None
        self._update_worker: Optional[YtDlpInstallWorker] = None
        self._video_meta: Dict[str, Any] = {}
        self._last_failed_action: str = ""
        self.download_result: Optional[Dict[str, Any]] = None

        self.setWindowTitle("Re-download YouTube Source Media" if self.redownload_mode else "Open Existing YouTube Video")
        self.setMinimumSize(620, 460)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self._build_ui(initial_url=initial_url, initial_quality=initial_quality)
        self._refresh_yt_dlp_status()

        if initial_url and self.redownload_mode:
            self._start_download()

    def _build_ui(self, initial_url: str = "", initial_quality: str = "") -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        intro_text = (
            "<b>Re-download YouTube Source Video</b><br>"
            "<span style='color: #64748b; font-size: 11px;'>"
            "Restores the cached YouTube video for this project without modifying your transcript, stories, or edits.</span>"
            if self.redownload_mode
            else
            "<b>Open Existing YouTube Video</b><br>"
            "<span style='color: #64748b; font-size: 11px;'>"
            "Paste a YouTube video link to download it into the Managed Media Cache, process transcripts and stories, "
            "and export to WordPress with automatic full-episode and per-story YouTube embeds.</span>"
        )
        intro = QLabel(intro_text)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # URL input row
        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=... or https://youtu.be/...")
        if initial_url:
            self.url_edit.setText(initial_url)
        if self.redownload_mode:
            self.url_edit.setReadOnly(True)
        self.url_edit.returnPressed.connect(self._start_probe)
        url_row.addWidget(self.url_edit, 1)

        self.fetch_btn = QPushButton("Fetch Info", self)
        self.fetch_btn.clicked.connect(self._start_probe)
        url_row.addWidget(self.fetch_btn)
        layout.addLayout(url_row)
        self.fetch_btn.setVisible(not self.redownload_mode)

        # Video metadata summary
        self.meta_label = QLabel("Paste a YouTube URL and click Fetch Info (or Download & Open directly).")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.meta_label)

        # Cache hit notice + force redownload
        cache_row = QHBoxLayout()
        self.cache_hit_label = QLabel("")
        self.cache_hit_label.setStyleSheet("color: #0284c7; font-size: 11px; font-weight: bold;")
        self.cache_hit_label.setVisible(False)
        cache_row.addWidget(self.cache_hit_label, 1)

        self.force_redownload_chk = QCheckBox("Force re-download")
        self.force_redownload_chk.setVisible(False)
        cache_row.addWidget(self.force_redownload_chk)
        layout.addLayout(cache_row)

        # Quality & options form
        form = QFormLayout()
        form.setSpacing(8)

        self.quality_combo = QComboBox()
        for q_key, q_label in YOUTUBE_QUALITY_PRESETS:
            self.quality_combo.addItem(q_label, q_key)
        saved_q = normalize_quality_preset(
            initial_quality or str(self.settings.value("yt_import_default_quality", DEFAULT_YOUTUBE_QUALITY) or DEFAULT_YOUTUBE_QUALITY)
        )
        q_idx = self.quality_combo.findData(saved_q)
        self.quality_combo.setCurrentIndex(q_idx if q_idx >= 0 else 0)
        self.quality_combo.currentIndexChanged.connect(self._refresh_quality_estimate_and_cache)
        form.addRow("Download Quality:", self.quality_combo)

        self.chapters_chk = QCheckBox("Import YouTube chapters as initial story markers")
        self.chapters_chk.setChecked(False)
        self.chapters_chk.setVisible(False)
        form.addRow("", self.chapters_chk)

        self.wp_link_edit = QLineEdit(self)
        self.wp_link_edit.setPlaceholderText("Optional: paste existing WordPress post URL to enable Update Mode on export")
        if not self.redownload_mode:
            form.addRow("Existing WordPress Post:", self.wp_link_edit)

        layout.addLayout(form)
        self.wp_link_edit.setVisible(not self.redownload_mode)

        # Advanced collapsible section: Browser Cookies + yt-dlp status/update
        self.advanced_section = CollapsibleSection("Advanced (Browser Cookies & yt-dlp)", self, is_expanded=False)
        adv_layout = QVBoxLayout()
        adv_layout.setContentsMargins(4, 4, 4, 4)
        adv_layout.setSpacing(6)

        adv_form = QFormLayout()
        self.cookies_combo = QComboBox()
        for b_key, b_label in ALLOWED_COOKIE_BROWSERS:
            self.cookies_combo.addItem(b_label, b_key)
        saved_browser = normalize_cookie_browser(str(self.settings.value("yt_dlp_cookies_browser", "") or ""))
        b_idx = self.cookies_combo.findData(saved_browser)
        self.cookies_combo.setCurrentIndex(b_idx if b_idx >= 0 else 0)
        self.cookies_combo.setToolTip(
            "Optional: read cookies from a local browser where you are signed into YouTube "
            "(useful for unlisted, scheduled, age-restricted, or bot-checked videos)."
        )
        adv_form.addRow("Browser Cookies:", self.cookies_combo)
        adv_layout.addLayout(adv_form)

        ytdlp_row = QHBoxLayout()
        self.ytdlp_status_label = QLabel("Checking yt-dlp...")
        self.ytdlp_status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        ytdlp_row.addWidget(self.ytdlp_status_label, 1)

        self.update_ytdlp_btn = QPushButton("Check / Update yt-dlp")
        self.update_ytdlp_btn.clicked.connect(lambda: self._start_yt_dlp_update(retry_after=False))
        ytdlp_row.addWidget(self.update_ytdlp_btn)
        adv_layout.addLayout(ytdlp_row)

        self.advanced_section.add_layout(adv_layout)
        layout.addWidget(self.advanced_section)

        # Progress & error recovery bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_label)

        recovery_row = QHBoxLayout()
        self.retry_update_btn = QPushButton("Update yt-dlp && Retry")
        self.retry_update_btn.setVisible(False)
        self.retry_update_btn.clicked.connect(lambda: self._start_yt_dlp_update(retry_after=True))
        recovery_row.addWidget(self.retry_update_btn)

        self.retry_cookies_btn = QPushButton("Retry with Browser Cookies")
        self.retry_cookies_btn.setVisible(False)
        self.retry_cookies_btn.clicked.connect(self._on_retry_with_cookies)
        recovery_row.addWidget(self.retry_cookies_btn)
        recovery_row.addStretch()
        layout.addLayout(recovery_row)

        layout.addStretch()

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_row.addWidget(self.cancel_btn)

        action_lbl = "Re-download" if self.redownload_mode else "Download && Open"
        self.download_btn = QPushButton(action_lbl)
        self.download_btn.setStyleSheet("font-weight: bold;")
        self.download_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self.download_btn)
        layout.addLayout(btn_row)

    def _refresh_yt_dlp_status(self) -> None:
        bin_path = find_yt_dlp_binary()
        if bin_path is None:
            self.ytdlp_status_label.setText("yt-dlp: Not installed yet (will auto-install on first use).")
        else:
            ver = "" if os.environ.get("RTVS_TEST_MODE") else get_yt_dlp_version(bin_path)
            ver_str = f"v{ver}" if ver else "installed"
            self.ytdlp_status_label.setText(f"yt-dlp: {ver_str} ({bin_path.name})")

    def _set_busy(self, busy: bool) -> None:
        self.fetch_btn.setEnabled(not busy)
        self.download_btn.setEnabled(not busy)
        self.update_ytdlp_btn.setEnabled(not busy)
        self.quality_combo.setEnabled(not busy)
        self.url_edit.setEnabled((not busy) and (not self.redownload_mode))
        self.progress_bar.setVisible(busy)
        if busy:
            self.retry_update_btn.setVisible(False)
            self.retry_cookies_btn.setVisible(False)

    def _refresh_quality_estimate_and_cache(self) -> None:
        preset = str(self.quality_combo.currentData() or DEFAULT_YOUTUBE_QUALITY)
        vid = str(self._video_meta.get("video_id") or "")
        if not vid:
            vid, _ = extract_youtube_id_strict(self.url_edit.text().strip())

        # Update cache-hit badge
        cached_file = None
        if vid:
            key = make_cache_key("youtube", vid, preset)
            cached_file = self.cache_manager.get_existing_cached_file(key, touch=False)
        if cached_file is not None:
            sz_txt = format_bytes_human(cached_file.stat().st_size) if cached_file.exists() else ""
            self.cache_hit_label.setText(f"Already in local cache ({sz_txt}) — opens immediately.")
            self.cache_hit_label.setVisible(True)
            self.force_redownload_chk.setVisible(True)
        else:
            self.cache_hit_label.setVisible(False)
            self.force_redownload_chk.setVisible(False)
            self.force_redownload_chk.setChecked(False)

        if self._video_meta:
            self._render_meta_summary()

    def _render_meta_summary(self) -> None:
        m = self._video_meta
        preset = str(self.quality_combo.currentData() or DEFAULT_YOUTUBE_QUALITY)
        est_map = m.get("size_estimates") if isinstance(m.get("size_estimates"), dict) else {}
        est_bytes = int(est_map.get(preset, 0) or 0)
        est_txt = format_bytes_human(est_bytes) if est_bytes > 0 else "Unknown"
        dur_txt = format_time(float(m.get("duration") or 0.0)) if m.get("duration") else "Unknown"
        date_txt = str(m.get("upload_date") or "Unknown")
        channel_txt = str(m.get("channel") or "Unknown channel")
        title_txt = str(m.get("title") or "Untitled Video")
        self.meta_label.setStyleSheet("font-size: 11px;")
        self.meta_label.setText(
            f"<b>{title_txt}</b><br>"
            f"Channel: {channel_txt} | Duration: {dur_txt} | Uploaded: {date_txt} | Est. Size ({preset}): {est_txt}"
        )

    def _start_probe(self) -> None:
        raw_url = self.url_edit.text().strip()
        vid, _canonical = extract_youtube_id_strict(raw_url)
        if not vid:
            QMessageBox.warning(self, "Invalid YouTube URL", "Please enter a valid YouTube video URL or 11-character video ID.")
            return
        if self._probe_worker and self._probe_worker.isRunning():
            return

        browser = str(self.cookies_combo.currentData() or "")
        self.settings.setValue("yt_dlp_cookies_browser", browser)
        self._last_failed_action = "probe"
        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.status_label.setText("Checking yt-dlp and fetching video metadata...")

        worker = YouTubeProbeWorker(raw_url, cookies_browser=browser, parent=self)
        self._probe_worker = worker
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_probe_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.start()

    def _on_probe_finished(self, meta: Dict[str, Any]) -> None:
        self._set_busy(False)
        self._video_meta = dict(meta or {})
        self._refresh_yt_dlp_status()
        self._render_meta_summary()

        chapters = self._video_meta.get("chapters") if isinstance(self._video_meta.get("chapters"), list) else []
        if chapters and not self.redownload_mode:
            self.chapters_chk.setText(f"Import {len(chapters)} YouTube chapters as initial story markers")
            self.chapters_chk.setVisible(True)
        else:
            self.chapters_chk.setVisible(False)
            self.chapters_chk.setChecked(False)

        self._refresh_quality_estimate_and_cache()
        self.status_label.setText("Video metadata loaded. Choose quality and click Download & Open.")

    def _start_download(self) -> None:
        raw_url = self.url_edit.text().strip()
        vid, _canonical = extract_youtube_id_strict(raw_url)
        if not vid:
            QMessageBox.warning(self, "Invalid YouTube URL", "Please enter a valid YouTube video URL or 11-character video ID.")
            return
        if self._download_worker and self._download_worker.isRunning():
            return

        preset = str(self.quality_combo.currentData() or DEFAULT_YOUTUBE_QUALITY)
        browser = str(self.cookies_combo.currentData() or "")
        if not self.redownload_mode:
            self.settings.setValue("yt_import_default_quality", preset)
        self.settings.setValue("yt_dlp_cookies_browser", browser)
        self.settings.sync()

        cap_gb = get_configured_cache_cap_gb(self.settings)
        force_dl = bool(self.force_redownload_chk.isChecked())
        cache_key = make_cache_key("youtube", vid, preset)
        has_cache_hit = (not force_dl) and (self.cache_manager.get_existing_cached_file(cache_key, touch=False) is not None)

        # Free disk space & cap pre-check for fresh downloads
        if not has_cache_hit and self._video_meta:
            est_map = self._video_meta.get("size_estimates") or {}
            est_bytes = int(est_map.get(preset, 0) or 0)
            if est_bytes > 0:
                space_check = self.cache_manager.check_disk_space(est_bytes, cap_gb=cap_gb)
                if space_check.get("warnings"):
                    ans = QMessageBox.warning(
                        self,
                        "Storage Check",
                        "\n\n".join(space_check["warnings"]) + "\n\nContinue downloading?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes if not space_check.get("low_disk_space") else QMessageBox.StandardButton.No,
                    )
                    if ans != QMessageBox.StandardButton.Yes:
                        return

        protected: List[str] = []
        active_audio = getattr(self.main_window, "audio_file", None)
        if active_audio:
            protected.append(str(active_audio))

        self._last_failed_action = "download"
        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.status_label.setText("Preparing YouTube download...")

        worker = YouTubeDownloadWorker(
            raw_url,
            video_meta=self._video_meta,
            quality_preset=preset,
            cookies_browser=browser,
            force_redownload=force_dl,
            cache_cap_gb=cap_gb,
            protected_paths=protected,
            parent=self,
        )
        self._download_worker = worker
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_download_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.start()

    def _on_download_finished(self, result: Dict[str, Any]) -> None:
        self._set_busy(False)
        self._refresh_yt_dlp_status()
        self.download_result = dict(result or {})
        self.download_result["import_chapters"] = bool(self.chapters_chk.isChecked())
        self.download_result["existing_wp_url"] = self.wp_link_edit.text().strip()
        self.accept()

    def _on_worker_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(max(0, min(100, int(pct))))
        self.status_label.setText(str(msg))

    def _on_worker_failed(self, msg: str, err_meta: Dict[str, Any]) -> None:
        self._set_busy(False)
        cat = str((err_meta or {}).get("category") or "")
        if cat == "cancelled":
            self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
            self.status_label.setText(msg)
            return

        self.status_label.setStyleSheet("color: #b3261e; font-size: 11px;")
        self.status_label.setText(msg)
        if (err_meta or {}).get("needs_update"):
            self.retry_update_btn.setVisible(True)
        if (err_meta or {}).get("needs_cookies"):
            if hasattr(self.advanced_section, "set_expanded"):
                self.advanced_section.set_expanded(True)
            self.retry_cookies_btn.setVisible(True)

    def _start_yt_dlp_update(self, retry_after: bool = False) -> None:
        if self._update_worker and self._update_worker.isRunning():
            return
        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.status_label.setText("Updating yt-dlp to latest release...")

        worker = YtDlpInstallWorker(parent=self)
        self._update_worker = worker
        worker.progress.connect(self._on_worker_progress)

        def _done(_path: str, version: str) -> None:
            self._set_busy(False)
            self._refresh_yt_dlp_status()
            self.status_label.setStyleSheet("color: #15803d; font-size: 11px;")
            self.status_label.setText(f"yt-dlp updated ({version}).")
            if retry_after:
                if self._last_failed_action == "probe":
                    self._start_probe()
                else:
                    self._start_download()

        def _fail(err_msg: str) -> None:
            self._set_busy(False)
            self.status_label.setStyleSheet("color: #b3261e; font-size: 11px;")
            self.status_label.setText(f"yt-dlp update failed: {err_msg}")

        worker.finished.connect(_done)
        worker.failed.connect(_fail)
        worker.start()

    def _on_retry_with_cookies(self) -> None:
        if not str(self.cookies_combo.currentData() or ""):
            QMessageBox.information(
                self,
                "Select a Browser",
                "Choose the browser where you are signed into YouTube under Advanced > Browser Cookies, then click Retry again.",
            )
            return
        if self._last_failed_action == "probe":
            self._start_probe()
        else:
            self._start_download()

    def _cancel_active_workers(self, detach: bool = False) -> None:
        for attr in ("_probe_worker", "_download_worker", "_update_worker"):
            w = getattr(self, attr, None)
            if w is None:
                continue
            if detach:
                setattr(self, attr, None)
                _detach_or_wait_yt_worker(w)
            else:
                try:
                    if w.isRunning():
                        w.cancel()
                except RuntimeError:
                    pass

    def _on_cancel_clicked(self) -> None:
        running = any(w is not None and w.isRunning() for w in (self._probe_worker, self._download_worker, self._update_worker))
        if running:
            self._cancel_active_workers(detach=False)
            self.status_label.setText("Cancelling...")
        else:
            self.reject()

    def reject(self) -> None:
        self._cancel_active_workers(detach=True)
        super().reject()

    def closeEvent(self, event) -> None:
        self._cancel_active_workers(detach=True)
        super().closeEvent(event)


_DETACHED_YT_WORKERS: set = set()


def _detach_or_wait_yt_worker(worker: Any, wait_ms: int = 300) -> None:
    """Cancel a YouTube/yt-dlp QThread and detach it if still winding down so Qt never aborts on dialog teardown."""
    if worker is None:
        return
    for sig_name in ("progress", "finished", "failed", "metadata_ready"):
        sig = getattr(worker, sig_name, None)
        if sig is not None:
            try:
                sig.disconnect()
            except Exception:
                pass
    try:
        if worker.isRunning():
            if hasattr(worker, "cancel"):
                worker.cancel()
            worker.requestInterruption()
            if not worker.wait(wait_ms):
                worker.setParent(None)
                _DETACHED_YT_WORKERS.add(worker)
                worker.finished.connect(lambda *_, w=worker: _DETACHED_YT_WORKERS.discard(w))
                worker.finished.connect(worker.deleteLater)
    except RuntimeError:
        pass


def open_yt_dlp_updater_dialog(parent: Optional[QWidget] = None) -> None:
    """Quick standalone updater dialog triggered from Cache Manager or Preferences."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Check / Update yt-dlp")
    dlg.setMinimumWidth(440)
    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)

    curr = find_yt_dlp_binary()
    curr_ver = get_yt_dlp_version(curr) if curr else "Not installed"
    status_lbl = QLabel(f"Current yt-dlp version: <b>{curr_ver}</b>")
    status_lbl.setWordWrap(True)
    layout.addWidget(status_lbl)

    pbar = QProgressBar()
    pbar.setRange(0, 100)
    pbar.setVisible(False)
    layout.addWidget(pbar)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    update_btn = QPushButton("Install / Update to Latest")
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(update_btn)
    btn_row.addWidget(close_btn)
    layout.addLayout(btn_row)

    worker_holder: List[YtDlpInstallWorker] = []

    def _run_update():
        update_btn.setEnabled(False)
        pbar.setVisible(True)
        pbar.setValue(0)
        w = YtDlpInstallWorker(parent=dlg)
        worker_holder.append(w)
        w.progress.connect(lambda pct, msg: (pbar.setValue(pct), status_lbl.setText(msg)))
        w.finished.connect(lambda _p, ver: (pbar.setValue(100), status_lbl.setText(f"yt-dlp is up to date (<b>{ver}</b>)."), update_btn.setEnabled(True)))
        w.failed.connect(lambda err: (status_lbl.setText(f"Update failed: {err}"), update_btn.setEnabled(True)))
        w.start()

    update_btn.clicked.connect(_run_update)
    dlg.exec()
    for w in worker_holder:
        _detach_or_wait_yt_worker(w)


def prompt_load_youtube_episode_dialog(main_window: Any, parent: Optional[QWidget] = None) -> bool:
    """Launch the YouTube import dialog, respect unsaved-project guard, and load downloaded media."""
    dlg = LoadYouTubeEpisodeDialog(main_window=main_window, parent=parent or main_window)
    if not dlg.exec() or not dlg.download_result:
        return False

    res = dlg.download_result
    file_path = Path(str(res.get("file_path") or ""))
    if not file_path.exists():
        QMessageBox.warning(parent or main_window, "Media Missing", f"Downloaded media file was not found:\n{file_path}")
        return False

    # Load the downloaded media into MainWindow (handles unsaved-changes prompt & workspace reset)
    if hasattr(main_window, "load_media_file"):
        if not main_window.load_media_file(str(file_path), source="YouTube video URL"):
            return False
    else:
        QMessageBox.critical(
            parent or main_window,
            "Media Loader Unavailable",
            "Could not open the downloaded YouTube video because the main window media loader is unavailable.",
        )
        return False

    populate_project_from_youtube_import(
        main_window=main_window,
        video_meta=res.get("video_meta") or {},
        file_path=file_path,
        quality_preset=str(res.get("quality_preset") or DEFAULT_YOUTUBE_QUALITY),
        cache_key=str(res.get("cache_key") or ""),
        import_chapters=bool(res.get("import_chapters", False)),
        existing_wp_url=str(res.get("existing_wp_url") or ""),
    )

    if hasattr(main_window, "statusBar"):
        title = str((res.get("video_meta") or {}).get("title") or file_path.name)
        src_note = " (from cache)" if res.get("from_cache") else ""
        main_window.statusBar().showMessage(f"Loaded YouTube video{src_note}: {title}")
    return True


def redownload_youtube_source_dialog(
    main_window: Any,
    source_meta: Dict[str, Any],
    parent: Optional[QWidget] = None,
) -> Optional[Path]:
    """Re-download an archived YouTube source for an existing .rtvs project."""
    url = str(source_meta.get("source_url") or source_meta.get("video_id") or "").strip()
    quality = normalize_quality_preset(str(source_meta.get("quality_preset") or DEFAULT_YOUTUBE_QUALITY))
    if not url:
        return None
    dlg = LoadYouTubeEpisodeDialog(
        main_window=main_window,
        parent=parent or main_window,
        initial_url=url,
        initial_quality=quality,
        redownload_mode=True,
    )
    if not dlg.exec() or not dlg.download_result:
        return None
    fp = Path(str(dlg.download_result.get("file_path") or ""))
    return fp if fp.exists() else None


__all__ = [
    "populate_project_from_youtube_import",
    "LoadYouTubeEpisodeDialog",
    "open_yt_dlp_updater_dialog",
    "prompt_load_youtube_episode_dialog",
    "redownload_youtube_source_dialog",
]

"""Qt UI panels and dialog for WordPress existing episode lookup and backfill workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QRadioButton,
    QVBoxLayout, QWidget,
)

from plugins.wordpress.episode_lookup import (
    MODE_NEW_EPISODE,
    MODE_UPDATE_EXISTING,
    _copy_fetched_post_fields,
    _populate_project_from_fetched_post,
    download_wp_episode_audio,
    resolve_wp_post_from_url,
)
from plugins.wordpress.pub_date_picker import PublicationDateLineEdit


def _refresh_dialog_export_button(tab_widget: Any) -> None:
    dlg = tab_widget.window() if hasattr(tab_widget, "window") else None
    if dlg and hasattr(dlg, "_update_export_button_label") and callable(dlg._update_export_button_label):
        dlg._update_export_button_label()


def _is_update_mode(tab_widget: Any) -> bool:
    rad_upd = getattr(tab_widget, "wp_rad_mode_update", None)
    return bool(rad_upd and rad_upd.isChecked())


def _get_current_tab_post(tab_widget: Any) -> Optional[Dict[str, Any]]:
    items = getattr(tab_widget, "wp_post_items", None) or []
    idx = getattr(tab_widget, "_current_post_index", 0)
    if 0 <= idx < len(items):
        return items[idx]
    return None


def sync_wp_audio_checkbox_label(tab_widget: Any) -> None:
    """Update the Media tab audio checkbox wording so Update mode clarifies that only new Story clips upload audio."""
    cb = getattr(tab_widget, "wp_cb_include_audio", None)
    if cb is None:
        return
    is_upd = _is_update_mode(tab_widget)
    post = _get_current_tab_post(tab_widget)
    has_post_url = bool(post and str(post.get("existing_post_url") or "").strip())
    replace_existing = hasattr(tab_widget, "wp_cb_replace_existing_audio") and tab_widget.wp_cb_replace_existing_audio.isChecked()
    if (is_upd or has_post_url) and not replace_existing:
        cb.setText("Include audio files for new Story clips (existing Full Episode MP3 preserved)")
        cb.setToolTip("Keep checked so new Story posts receive segmented MP3 clips and audio players. The existing Full Episode MP3 and Castos podcast metadata remain untouched.")
    else:
        cb.setText("Include audio files in WordPress export (upload audio and embed player)")
        cb.setToolTip("When enabled, uploads audio recordings to the WordPress Media Library and embeds an audio player in each post. When disabled, exports only transcript text (and featured images, when selected), omitting audio file uploads.")


def _sync_mode_visibility(tab_widget: Any) -> None:
    """Update visibility of the Existing Episode panel and default status dropdowns."""
    is_upd = _is_update_mode(tab_widget)
    post = _get_current_tab_post(tab_widget)
    has_post_url = bool(post and str(post.get("existing_post_url") or "").strip())

    box = getattr(tab_widget, "wp_existing_episode_box", None)
    if box is not None:
        box.setVisible(is_upd or has_post_url)

    if hasattr(tab_widget, "wp_cb_replace_existing_audio"):
        tab_widget.wp_cb_replace_existing_audio.setVisible(is_upd or has_post_url)
    if hasattr(tab_widget, "wp_load_existing_mp3_btn"):
        tab_widget.wp_load_existing_mp3_btn.setVisible(is_upd)
    sync_wp_audio_checkbox_label(tab_widget)

    proj_meta = getattr(getattr(tab_widget, "main_window", None), "project_metadata", None)
    if isinstance(proj_meta, dict):
        wp_meta = proj_meta.setdefault("wordpress", {})
        wp_meta["export_mode"] = MODE_UPDATE_EXISTING if is_upd else MODE_NEW_EPISODE


def load_episode_updater_from_post(tab_widget: Any, post: Dict[str, Any]) -> None:
    """Synchronize mode, URL, publication date, and status controls from project and post data."""
    if not hasattr(tab_widget, "wp_existing_url_edit"):
        return

    proj_meta = getattr(getattr(tab_widget, "main_window", None), "project_metadata", {}) or {}
    wp_proj = proj_meta.get("wordpress", {}) if isinstance(proj_meta, dict) and isinstance(proj_meta.get("wordpress"), dict) else {}

    tab_widget._syncing_post_editor = True
    try:
        saved_mode = str(wp_proj.get("export_mode") or MODE_NEW_EPISODE).strip()
        if hasattr(tab_widget, "wp_rad_mode_update") and hasattr(tab_widget, "wp_rad_mode_new"):
            if saved_mode == MODE_UPDATE_EXISTING:
                tab_widget.wp_rad_mode_update.setChecked(True)
            else:
                tab_widget.wp_rad_mode_new.setChecked(True)

        tab_widget.wp_existing_url_edit.setText(str(post.get("existing_post_url") or ""))
        replace_aud = bool(post.get("replace_existing_audio", False))
        if hasattr(tab_widget, "wp_cb_replace_existing_audio"):
            tab_widget.wp_cb_replace_existing_audio.setChecked(replace_aud)

        if hasattr(tab_widget, "wp_pub_date_edit"):
            tab_widget.wp_pub_date_edit.setText(str(wp_proj.get("publication_date") or ""))

        if hasattr(tab_widget, "wp_full_status_combo"):
            default_full = "publish" if saved_mode == MODE_UPDATE_EXISTING else "draft"
            full_st = str(wp_proj.get("full_episode_status") or default_full)
            idx = tab_widget.wp_full_status_combo.findData(full_st)
            tab_widget.wp_full_status_combo.setCurrentIndex(max(0, idx))

        if hasattr(tab_widget, "wp_story_status_combo"):
            story_st = str(wp_proj.get("story_status") or "draft")
            idx = tab_widget.wp_story_status_combo.findData(story_st)
            tab_widget.wp_story_status_combo.setCurrentIndex(max(0, idx))

        _update_existing_status_label(tab_widget, post)
    finally:
        tab_widget._syncing_post_editor = False

    _sync_mode_visibility(tab_widget)


def _update_existing_status_label(tab_widget: Any, post: Optional[Dict[str, Any]]) -> None:
    lbl = getattr(tab_widget, "wp_existing_status_label", None)
    if not lbl:
        return
    if not post:
        lbl.setText("Enter the URL of an existing WordPress post to update in place.")
        lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        return

    pid = post.get("existing_post_id")
    if pid:
        p_status = str(post.get("existing_post_status") or "publish").capitalize()
        p_date = str(post.get("existing_post_date") or "")
        date_note = f", Date: {p_date}" if p_date else ""
        exc_note = " (Existing text preserved in Excerpt)" if post.get("excerpt_from_existing") else ""
        lbl.setText(f"Linked to WordPress Post #{pid} (Status: {p_status}{date_note}){exc_note}")
        lbl.setStyleSheet("color: #4ade80; font-size: 11px;")
    else:
        lbl.setText("Paste an existing WordPress episode URL and click Fetch Post Info (or Export to resolve automatically).")
        lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")


def apply_fetched_post_to_tab(tab_widget: Any, post_info: Dict[str, Any], target_idx: Optional[int] = None) -> None:
    """Populate tab_widget's target post (default: current or Full Episode) with fetched WP post data."""
    items = getattr(tab_widget, "wp_post_items", None) or []
    if not items:
        return

    idx = target_idx if target_idx is not None else getattr(tab_widget, "_current_post_index", 0)
    if not (0 <= idx < len(items)):
        idx = 0
    post = items[idx]
    _copy_fetched_post_fields(post, post_info)

    proj_meta = getattr(getattr(tab_widget, "main_window", None), "project_metadata", None)
    if isinstance(proj_meta, dict):
        wp_meta = proj_meta.setdefault("wordpress", {})
        wp_meta["export_mode"] = MODE_UPDATE_EXISTING
        if post_info.get("date_display"):
            wp_meta["publication_date"] = post_info["date_display"]
        wp_meta["full_episode_status"] = post_info["status"] or "publish"
        for k in ("existing_post_id", "existing_post_url", "existing_post_slug", "existing_post_status", "excerpt_from_existing"):
            wp_meta[k] = post.get(k)

    if hasattr(tab_widget, "_sync_post_to_project"):
        tab_widget._sync_post_to_project(idx)
    if hasattr(tab_widget, "_update_post_list_item_label"):
        tab_widget._update_post_list_item_label(idx)
    if hasattr(tab_widget, "_load_post_editor_state") and idx == getattr(tab_widget, "_current_post_index", 0):
        tab_widget._load_post_editor_state(idx)
    _refresh_dialog_export_button(tab_widget)


def _get_configured_client(parent_widget: QWidget) -> Any:
    from plugins.wordpress.client import WordPressSettingsDialog, get_wp_client
    client = get_wp_client()
    if client and client.is_configured():
        return client
    reply = QMessageBox.question(
        parent_widget,
        "WordPress Credentials Required",
        "WordPress site connection settings are missing or incomplete.\n\nWould you like to configure them now?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if reply == QMessageBox.StandardButton.Yes:
        dlg = WordPressSettingsDialog(parent=parent_widget)
        if dlg.exec():
            return get_wp_client()
    return None


def setup_wp_mode_and_date_ui(tab_widget: Any, parent_section: Any) -> None:
    """Build workflow mode toggle, existing post URL lookup, publication date, and status controls."""
    container = QWidget(tab_widget)
    vbox = QVBoxLayout(container)
    vbox.setContentsMargins(0, 4, 0, 4)
    vbox.setSpacing(6)

    # Row 1: Workflow Mode Toggle
    mode_row = QHBoxLayout()
    mode_row.setSpacing(10)
    mode_lbl = QLabel("<b>Workflow Mode:</b>")
    tab_widget.wp_mode_button_group = QButtonGroup(tab_widget)
    tab_widget.wp_rad_mode_new = QRadioButton("Create New Episode && Stories")
    tab_widget.wp_rad_mode_update = QRadioButton("Update Existing Episode && Backfill Stories")
    tab_widget.wp_mode_button_group.addButton(tab_widget.wp_rad_mode_new)
    tab_widget.wp_mode_button_group.addButton(tab_widget.wp_rad_mode_update)
    tab_widget.wp_rad_mode_new.setChecked(True)
    tab_widget.wp_rad_mode_new.setToolTip("Creates new WordPress draft posts for the episode and/or selected stories.")
    tab_widget.wp_rad_mode_update.setToolTip(
        "Updates an existing published episode page in-place without changing its URL, published status, or podcast MP3, "
        "moves existing page text into the Excerpt, and creates backdated story drafts."
    )
    mode_row.addWidget(mode_lbl)
    mode_row.addWidget(tab_widget.wp_rad_mode_new)
    mode_row.addWidget(tab_widget.wp_rad_mode_update)
    mode_row.addStretch()
    vbox.addLayout(mode_row)

    # Row 2: Existing Episode URL Box (shown in Update mode)
    tab_widget.wp_existing_episode_box = QFrame(container)
    tab_widget.wp_existing_episode_box.setFrameShape(QFrame.Shape.StyledPanel)
    ex_layout = QVBoxLayout(tab_widget.wp_existing_episode_box)
    ex_layout.setContentsMargins(8, 6, 8, 6)
    ex_layout.setSpacing(6)

    url_row = QHBoxLayout()
    url_row.setSpacing(6)
    url_row.addWidget(QLabel("Existing Post URL:"))
    tab_widget.wp_existing_url_edit = QLineEdit()
    tab_widget.wp_existing_url_edit.setPlaceholderText("Paste existing WordPress post URL or ID...")
    url_row.addWidget(tab_widget.wp_existing_url_edit, 1)

    tab_widget.wp_fetch_existing_btn = QPushButton("Fetch Post Info")
    tab_widget.wp_fetch_existing_btn.setToolTip(
        "Look up the existing WordPress post by URL, populate its title, date, authors, categories, and move existing page text into the Excerpt."
    )
    url_row.addWidget(tab_widget.wp_fetch_existing_btn)

    tab_widget.wp_load_existing_mp3_btn = QPushButton("Download && Load Episode MP3")
    tab_widget.wp_load_existing_mp3_btn.setToolTip(
        "Download the episode's existing MP3 from WordPress and open it in this project for segmentation and transcription."
    )
    url_row.addWidget(tab_widget.wp_load_existing_mp3_btn)
    ex_layout.addLayout(url_row)

    tab_widget.wp_cb_replace_existing_audio = QCheckBox(
        "Replace existing Full Episode MP3 file and Seriously Simple Podcasting metadata"
    )
    tab_widget.wp_cb_replace_existing_audio.setChecked(False)
    tab_widget.wp_cb_replace_existing_audio.setToolTip(
        "Leave unchecked to preserve the existing episode MP3 and podcast RSS feed metadata while still uploading audio clips for individual story pages."
    )
    ex_layout.addWidget(tab_widget.wp_cb_replace_existing_audio)

    tab_widget.wp_existing_status_label = QLabel(
        "Paste an existing WordPress episode URL and click Fetch Post Info (or Export to resolve automatically)."
    )
    tab_widget.wp_existing_status_label.setWordWrap(True)
    tab_widget.wp_existing_status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
    ex_layout.addWidget(tab_widget.wp_existing_status_label)

    tab_widget.wp_existing_episode_box.setVisible(False)
    vbox.addWidget(tab_widget.wp_existing_episode_box)

    # Row 3: Shared Publication Date & Post Status Controls (Visible in Both Modes)
    sched_row = QHBoxLayout()
    sched_row.setSpacing(8)
    sched_row.addWidget(QLabel("Publication Date:"))
    tab_widget.wp_pub_date_edit = PublicationDateLineEdit()
    tab_widget.wp_pub_date_edit.setPlaceholderText("Leave blank for current time (click for calendar or type YYYY-MM-DD HH:MM)")
    tab_widget.wp_pub_date_edit.setToolTip(
        "Optional publication date/time applied to the Full Episode and all Stories in this export. "
        "Click to pick from the calendar/time popup or type a date directly; leave blank for the current time."
    )
    tab_widget.wp_pub_date_edit.setMinimumWidth(260)
    sched_row.addWidget(tab_widget.wp_pub_date_edit, 1)

    tab_widget.wp_clear_date_btn = QPushButton("Clear")
    tab_widget.wp_clear_date_btn.setToolTip("Clear custom date to use the current date and time")
    sched_row.addWidget(tab_widget.wp_clear_date_btn)

    sched_row.addWidget(QLabel("Full Episode:"))
    tab_widget.wp_full_status_combo = QComboBox()
    tab_widget.wp_full_status_combo.addItem("Draft", "draft")
    tab_widget.wp_full_status_combo.addItem("Published (Keep Live)", "publish")
    sched_row.addWidget(tab_widget.wp_full_status_combo)

    sched_row.addWidget(QLabel("Stories:"))
    tab_widget.wp_story_status_combo = QComboBox()
    tab_widget.wp_story_status_combo.addItem("Draft", "draft")
    tab_widget.wp_story_status_combo.addItem("Published", "publish")
    sched_row.addWidget(tab_widget.wp_story_status_combo)
    vbox.addLayout(sched_row)

    parent_section.add_widget(container)

    # Event wiring
    def _on_mode_toggled():
        if getattr(tab_widget, "_syncing_post_editor", False):
            return
        is_upd = _is_update_mode(tab_widget)
        target_status = "publish" if is_upd else "draft"
        idx = tab_widget.wp_full_status_combo.findData(target_status)
        if idx >= 0:
            tab_widget.wp_full_status_combo.setCurrentIndex(idx)
        if is_upd and hasattr(tab_widget, "wp_cb_replace_existing_audio"):
            tab_widget.wp_cb_replace_existing_audio.setChecked(False)
        _on_status_changed()
        _sync_mode_visibility(tab_widget)
        _refresh_dialog_export_button(tab_widget)

    def _on_existing_url_edited(text: str):
        if getattr(tab_widget, "_syncing_post_editor", False):
            return
        post = _get_current_tab_post(tab_widget)
        if post:
            cleaned = text.strip()
            if post.get("existing_post_url") != cleaned:
                post["existing_post_id"] = None
            post["existing_post_url"] = cleaned
            _update_existing_status_label(tab_widget, post)
            if hasattr(tab_widget, "_sync_to_proj"):
                tab_widget._sync_to_proj(tab_widget._current_post_index)
        _refresh_dialog_export_button(tab_widget)

    def _on_replace_audio_toggled(checked: bool):
        if getattr(tab_widget, "_syncing_post_editor", False):
            return
        post = _get_current_tab_post(tab_widget)
        if post:
            post["replace_existing_audio"] = bool(checked)
            if hasattr(tab_widget, "_sync_to_proj"):
                tab_widget._sync_to_proj(tab_widget._current_post_index)
        sync_wp_audio_checkbox_label(tab_widget)

    def _on_pub_date_edited(text: str):
        if getattr(tab_widget, "_syncing_post_editor", False):
            return
        pm = getattr(getattr(tab_widget, "main_window", None), "project_metadata", None)
        if isinstance(pm, dict):
            pm.setdefault("wordpress", {})["publication_date"] = text.strip()

    def _on_status_changed():
        if getattr(tab_widget, "_syncing_post_editor", False):
            return
        pm = getattr(getattr(tab_widget, "main_window", None), "project_metadata", None)
        if isinstance(pm, dict):
            wpm = pm.setdefault("wordpress", {})
            wpm["full_episode_status"] = tab_widget.wp_full_status_combo.currentData() or "draft"
            wpm["story_status"] = tab_widget.wp_story_status_combo.currentData() or "draft"

    def _resolve_url_from_tab() -> Optional[Dict[str, Any]]:
        url = tab_widget.wp_existing_url_edit.text().strip()
        if not url:
            QMessageBox.information(tab_widget, "WordPress URL Required", "Please paste an existing WordPress post URL first.")
            return None
        client = _get_configured_client(tab_widget)
        return resolve_wp_post_from_url(client, url) if client else None

    def _on_fetch_clicked():
        try:
            post_info = _resolve_url_from_tab()
            if not post_info:
                return
            apply_fetched_post_to_tab(tab_widget, post_info)
            QMessageBox.information(tab_widget, "WordPress Post Loaded", f"Linked to existing Post #{post_info['id']} ({post_info['status']}).\n\nTitle: {post_info['title']}\nOriginal Date: {post_info['date_display']}\nExisting page text has been placed into the Excerpt field.")
        except Exception as exc:
            QMessageBox.warning(tab_widget, "Fetch Post Failed", str(exc))

    def _on_download_mp3_clicked():
        try:
            post_info = _resolve_url_from_tab()
            if not post_info:
                return
            mp3_path = download_wp_episode_audio(post_info, main_window=getattr(tab_widget, "main_window", None))
            mw = getattr(tab_widget, "main_window", None)
            if mw and hasattr(mw, "load_media_file") and mw.load_media_file(str(mp3_path), source="WordPress episode URL"):
                _populate_project_from_fetched_post(mw, post_info)
                if hasattr(tab_widget, "rebuild_post_items"):
                    tab_widget.rebuild_post_items()
                QMessageBox.information(tab_widget, "Episode MP3 Loaded", f"Downloaded '{mp3_path.name}' and loaded WordPress metadata for '{post_info['title']}'.")
        except Exception as exc:
            QMessageBox.warning(tab_widget, "Download Episode MP3 Failed", str(exc))

    def _on_clear_date_clicked():
        tab_widget.wp_pub_date_edit.setText("")
        if hasattr(tab_widget.wp_pub_date_edit, "close_picker"):
            tab_widget.wp_pub_date_edit.close_picker()
        _on_pub_date_edited("")

    tab_widget.wp_rad_mode_update.toggled.connect(lambda _: _on_mode_toggled())
    tab_widget.wp_existing_url_edit.textEdited.connect(_on_existing_url_edited)
    tab_widget.wp_cb_replace_existing_audio.toggled.connect(_on_replace_audio_toggled)
    tab_widget.wp_pub_date_edit.textEdited.connect(_on_pub_date_edited)
    tab_widget.wp_clear_date_btn.clicked.connect(_on_clear_date_clicked)
    tab_widget.wp_full_status_combo.currentIndexChanged.connect(lambda _: _on_status_changed())
    tab_widget.wp_story_status_combo.currentIndexChanged.connect(lambda _: _on_status_changed())
    tab_widget.wp_fetch_existing_btn.clicked.connect(_on_fetch_clicked)
    tab_widget.wp_load_existing_mp3_btn.clicked.connect(_on_download_mp3_clicked)


class LoadWordPressEpisodeDialog(QDialog):
    """Dialog for starting or updating a project from an existing WordPress/podcast episode URL."""

    def __init__(self, main_window: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = main_window
        self._cached_url: str = ""
        self._resolved_info: Optional[Dict[str, Any]] = None
        self.setWindowTitle("Open Existing WordPress Episode")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        desc = QLabel("Enter an older WordPress episode URL (or direct podcast MP3 URL) to load its original publication date, title, show-notes excerpt, categories, and authors into a backfill project.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Episode / MP3 URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste WordPress episode URL or direct MP3 URL...")
        self.fetch_btn = QPushButton("Fetch Info")
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(self.fetch_btn)
        layout.addLayout(url_row)
        self.status_lbl = QLabel("Paste a WordPress post URL and click Fetch Info (or Load Episode directly).")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.status_lbl)
        self.audio_src_group = QButtonGroup(self)
        self.rb_download_mp3 = QRadioButton("Download and load MP3 from WordPress episode / URL")
        self.rb_local_file = QRadioButton("Use local audio file from computer:")
        self.rb_metadata_only = QRadioButton("Load WordPress episode metadata only (keep current project audio)")
        for rb in (self.rb_download_mp3, self.rb_local_file, self.rb_metadata_only):
            self.audio_src_group.addButton(rb)
        self.rb_download_mp3.setChecked(True)
        layout.addWidget(self.rb_download_mp3)
        layout.addWidget(self.rb_local_file)
        local_row = QHBoxLayout()
        local_row.setContentsMargins(20, 0, 0, 0)
        self.local_file_edit = QLineEdit()
        self.local_file_edit.setPlaceholderText("Select an audio or video file...")
        self.browse_local_btn = QPushButton("Browse...")
        local_row.addWidget(self.local_file_edit, 1)
        local_row.addWidget(self.browse_local_btn)
        layout.addLayout(local_row)
        layout.addWidget(self.rb_metadata_only)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.load_btn = QPushButton("Load Episode")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self._sync_local_row_enabled()
        self.rb_local_file.toggled.connect(lambda _: self._sync_local_row_enabled())
        self.browse_local_btn.clicked.connect(self._on_browse_local)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        self.cancel_btn.clicked.connect(self.reject)
        self.load_btn.clicked.connect(self._on_load_clicked)

    def _sync_local_row_enabled(self):
        use_local = self.rb_local_file.isChecked()
        self.local_file_edit.setEnabled(use_local)
        self.browse_local_btn.setEnabled(use_local)

    def _on_browse_local(self):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select Local Episode Audio/Video File",
            "",
            "Audio/Video Files (*.mp3 *.wav *.m4a *.flac *.ogg *.mp4 *.mov *.mkv);;All Files (*.*)",
        )
        if fn:
            self.local_file_edit.setText(fn)
            self.rb_local_file.setChecked(True)

    def _resolve_target(self, url: str) -> Dict[str, Any]:
        clean_path = url.lower().split("?")[0]
        if clean_path.endswith((".mp3", ".wav", ".m4a", ".ogg")) and "/wp-json/" not in url.lower():
            stem = Path(clean_path).stem or "episode"
            return {"id": None, "url": url, "slug": stem, "status": "publish", "date": "", "date_display": "", "title": stem, "excerpt": "", "author_ids": [], "author_term_ids": [], "category_ids": [], "audio_url": url}
        if self._resolved_info and self._cached_url == url:
            return self._resolved_info
        client = _get_configured_client(self)
        if not client:
            raise RuntimeError("WordPress credentials are required to look up this URL.")
        info = resolve_wp_post_from_url(client, url)
        self._cached_url = url
        self._resolved_info = info
        return info

    def _on_fetch_clicked(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Required", "Please enter a WordPress episode URL first.")
            return
        try:
            info = self._resolve_target(url)
            if info.get("id"):
                aud_note = "MP3 URL detected" if info.get("audio_url") else "No MP3 URL found in post"
                self.status_lbl.setText(f"Found Post #{info['id']}: '{info['title']}' ({info['status']}, {info['date_display']}) — {aud_note}")
            else:
                self.status_lbl.setText(f"Direct audio URL ready: {Path(url.split('?')[0]).name}")
            self.status_lbl.setStyleSheet("color: #4ade80; font-size: 11px;")
        except Exception as exc:
            self.status_lbl.setText(str(exc))
            self.status_lbl.setStyleSheet("color: #f87171; font-size: 11px;")

    def _on_load_clicked(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Required", "Please enter a WordPress episode or MP3 URL.")
            return
        local_path = self.local_file_edit.text().strip()
        if self.rb_local_file.isChecked() and (not local_path or not Path(local_path).is_file()):
            QMessageBox.warning(self, "Local File Required", "Please select a valid local audio or video file.")
            return

        self.load_btn.setEnabled(False)
        try:
            post_info = self._resolve_target(url)
            if self.rb_download_mp3.isChecked():
                mp3_path = download_wp_episode_audio(post_info, main_window=self.main_window)
                if self.main_window and hasattr(self.main_window, "load_media_file"):
                    if not self.main_window.load_media_file(str(mp3_path), source="WordPress episode URL"):
                        self.load_btn.setEnabled(True)
                        return
            elif self.rb_local_file.isChecked():
                if self.main_window and hasattr(self.main_window, "load_media_file"):
                    if not self.main_window.load_media_file(local_path, source="Local audio for WordPress episode"):
                        self.load_btn.setEnabled(True)
                        return

            if post_info.get("id"):
                _populate_project_from_fetched_post(self.main_window, post_info)
                msg = f"Loaded Post #{post_info['id']} ({post_info['date_display']}).\nWordPress export is now set to Update Existing Episode mode."
            else:
                msg = f"Loaded audio from {url}."
            QMessageBox.information(self, "WordPress Episode Loaded", msg)
            self.accept()
        except Exception as exc:
            self.load_btn.setEnabled(True)
            QMessageBox.critical(self, "Load Episode Failed", str(exc))


def prompt_load_existing_wp_episode_dialog(main_window: Any, parent: Optional[QWidget] = None) -> bool:
    """Launch the Load Existing WordPress Episode dialog and return True if accepted."""
    dlg = LoadWordPressEpisodeDialog(main_window=main_window, parent=parent)
    return bool(dlg.exec())


__all__ = [
    "PublicationDateLineEdit",
    "sync_wp_audio_checkbox_label",
    "load_episode_updater_from_post",
    "apply_fetched_post_to_tab",
    "setup_wp_mode_and_date_ui",
    "LoadWordPressEpisodeDialog",
    "prompt_load_existing_wp_episode_dialog",
]

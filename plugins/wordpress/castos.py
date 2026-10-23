"""Seriously Simple Podcasting (Castos) integration for WordPress export.

Provides data models, post meta mappings, REST API series feed discovery,
and UI controls for designating draft posts as Castos podcast episodes.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import CollapsibleSection

# Seriously Simple Podcasting (Castos) Custom Post Meta Keys (Legacy / Compat)
SS_PODCAST_AUDIO_FILE = "ss_podcast_audio_file"
SS_PODCAST_AUDIO_FILE_ID = "ss_podcast_audio_file_id"
SS_PODCAST_DURATION = "ss_podcast_duration"
SS_PODCAST_FILESIZE = "ss_podcast_filesize"
SS_PODCAST_FEED = "ss_podcast_feed"
SS_PODCAST_EPISODE_TYPE = "ss_podcast_episode_type"
SS_PODCAST_SEASON = "ss_podcast_season"
SS_PODCAST_EPISODE_NUMBER = "ss_podcast_episode_number"

# Native Seriously Simple Podcasting (Castos) Custom Post Meta Keys
CASTOS_META_AUDIO_FILE = "audio_file"
CASTOS_META_AUDIO_FILE_ID = "audio_file_id"
CASTOS_META_DURATION = "duration"
CASTOS_META_FILESIZE = "filesize"
CASTOS_META_EPISODE_TYPE = "episode_type"
CASTOS_META_SEASON = "season"
CASTOS_META_EPISODE_NUMBER = "episode_number"

# WordPress Taxonomy and Shortcode
CASTOS_TAXONOMY_SERIES = "series"
CASTOS_TAXONOMY_SERIES_FALLBACK = "podcast_series"
CASTOS_SHORTCODE = "[ss_player]"
CASTOS_PLAYER_BLOCK = '<!-- wp:shortcode -->\n[ss_player]\n<!-- /wp:shortcode -->'

DEFAULT_FEED_SLUG = "default"
DEFAULT_FEED_NAME = "Default Podcast Feed"


def format_castos_duration(seconds: float | int | None) -> str:
    """Format duration in seconds into HH:MM:SS for podcast RSS metadata."""
    if seconds is None:
        return "00:00:00"
    try:
        total_sec = max(0, int(round(float(seconds))))
    except (ValueError, TypeError):
        return "00:00:00"
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def build_castos_post_meta(
    audio_url: str,
    attachment_id: Optional[int] = None,
    duration_seconds: float = 0.0,
    filesize_bytes: Optional[int] = None,
    feed_slug: str = DEFAULT_FEED_SLUG,
    episode_type: str = "full",
    season: Optional[Any] = None,
    episode_number: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build the dictionary of Seriously Simple Podcasting post meta keys.

    Populates native Castos fields (audio_file, duration, filesize, episode_type,
    season, episode_number) as well as compatibility aliases (ss_podcast_*).
    Strictly excludes private leading-underscore keys to avoid WordPress REST API
    HTTP 400 Bad Request rejections.
    """
    clean_audio = str(audio_url or "").strip()
    clean_feed = str(feed_slug or DEFAULT_FEED_SLUG).strip()
    meta: Dict[str, Any] = {
        CASTOS_META_AUDIO_FILE: clean_audio,
        SS_PODCAST_AUDIO_FILE: clean_audio,
        SS_PODCAST_FEED: clean_feed,
    }
    if attachment_id is not None:
        try:
            att_int = int(attachment_id)
            meta[CASTOS_META_AUDIO_FILE_ID] = att_int
            meta[SS_PODCAST_AUDIO_FILE_ID] = att_int
        except (ValueError, TypeError):
            pass

    if duration_seconds > 0:
        dur_str = format_castos_duration(duration_seconds)
        meta[CASTOS_META_DURATION] = dur_str
        meta[SS_PODCAST_DURATION] = dur_str

    if filesize_bytes is not None:
        try:
            fs_int = int(filesize_bytes)
            meta[CASTOS_META_FILESIZE] = fs_int
            meta[SS_PODCAST_FILESIZE] = fs_int
        except (ValueError, TypeError):
            pass

    if episode_type:
        ep_type_str = str(episode_type).strip()
        meta[CASTOS_META_EPISODE_TYPE] = ep_type_str
        meta[SS_PODCAST_EPISODE_TYPE] = ep_type_str

    if season is not None and str(season).strip():
        s_val: Any = str(season).strip()
        try:
            s_val = int(s_val)
        except ValueError:
            pass
        meta[CASTOS_META_SEASON] = s_val
        meta[SS_PODCAST_SEASON] = s_val

    if episode_number is not None and str(episode_number).strip():
        ep_val: Any = str(episode_number).strip()
        try:
            ep_val = int(ep_val)
        except ValueError:
            pass
        meta[CASTOS_META_EPISODE_NUMBER] = ep_val
        meta[SS_PODCAST_EPISODE_NUMBER] = ep_val

    return meta


def copy_podcast_meta(target: Dict[str, Any], src: Dict[str, Any]) -> None:
    """Copy Seriously Simple Podcasting metadata fields from src to target dictionary."""
    target["is_podcast"] = bool(src.get("is_podcast", False))
    target["podcast_feed"] = str(src.get("podcast_feed") or DEFAULT_FEED_SLUG)
    target["podcast_feed_id"] = src.get("podcast_feed_id")
    target["podcast_feed_ids"] = list(src.get("podcast_feed_ids") or [])
    target["podcast_feeds"] = list(src.get("podcast_feeds") or [])
    target["podcast_episode_type"] = str(src.get("podcast_episode_type") or "full")
    if "podcast_season" in src:
        target["podcast_season"] = src.get("podcast_season")
    if "podcast_episode_number" in src:
        target["podcast_episode_number"] = src.get("podcast_episode_number")


def fetch_castos_feeds(client: Any) -> List[Dict[str, Any]]:
    """Query WordPress REST API for Seriously Simple Podcasting series/feeds.
    
    Discovers feeds through canonical Seriously Simple Podcasting series endpoints
    and dynamic taxonomy inspection (strictly filtering out authors, categories, and tags).
    Returns a list of dicts with 'id', 'name', 'slug'.
    """
    default_feed_placeholder = {"id": 0, "name": DEFAULT_FEED_NAME, "slug": DEFAULT_FEED_SLUG}

    if not client or not hasattr(client, "is_configured") or not client.is_configured():
        return [default_feed_placeholder]

    api_base = getattr(client, "api_base", "").rstrip("/")
    site_url = getattr(client, "site_url", "").rstrip("/")

    NON_PODCAST_TAXONOMIES = {
        "author", "ppma_author", "authors", "user", "users",
        "category", "categories", "post_tag", "tags", "tag",
        "nav_menu", "link_category", "post_format", "wp_theme",
        "wp_template_part_area", "wp_pattern_category",
        "wp_action_types", "post_status",
    }

    # 1. Canonical Seriously Simple Podcasting series endpoints (probed first)
    canonical_endpoints = [
        f"{api_base}/series",
        f"{api_base}/series/",
        f"{api_base}/podcast_series",
        f"{api_base}/podcast_series/",
        f"{api_base}/podcast-series",
        f"{api_base}/podcast-series/",
        f"{api_base}/ssp_series",
        f"{api_base}/podcasts",
        f"{site_url}/wp-json/wp/v2/series",
        f"{site_url}/wp-json/wp/v2/series/",
        f"{site_url}/wp-json/wp/v2/podcast_series",
        f"{site_url}/wp-json/ssp/v1/feeds",
        f"{site_url}/?rest_route=/wp/v2/series",
        f"{site_url}/?rest_route=/wp/v2/podcast_series",
        f"{site_url}/?rest_route=/ssp/v1/feeds",
    ]

    # 2. Dynamic taxonomy auto-discovery from /wp-json/wp/v2/taxonomies
    discovered_endpoints: List[str] = []
    tax_urls = [
        f"{api_base}/taxonomies",
        f"{api_base}/taxonomies/",
        f"{site_url}/?rest_route=/wp/v2/taxonomies",
    ]
    for t_url in tax_urls:
        try:
            resp = client._get_request(t_url, headers={"Accept": "application/json"}, timeout=10)
            if hasattr(resp, "status_code") and resp.status_code == 200:
                tax_data = resp.json()
                if isinstance(tax_data, dict):
                    for tax_key, tax_info in tax_data.items():
                        if isinstance(tax_info, dict):
                            t_slug = str(tax_info.get("slug", tax_key)).lower().strip()
                            t_name = str(tax_info.get("name", "")).lower().strip()
                            t_label = str(tax_info.get("label", "")).lower().strip()
                            if t_slug in NON_PODCAST_TAXONOMIES or tax_key.lower() in NON_PODCAST_TAXONOMIES:
                                continue
                            if any(ex in t_name for ex in ("author", "category", "tag", "menu", "format")):
                                continue

                            is_podcast_tax = (
                                t_slug in ("series", "podcast_series", "podcast-series", "ssp_series", "podcasts")
                                or "series" in t_slug
                                or (t_slug.startswith("podcast") and t_slug not in ("podcast", "podcasts"))
                                or "series" in t_name
                                or any(w in t_name for w in ("podcast series", "all podcasts"))
                            )
                            if is_podcast_tax:
                                rest_base = tax_info.get("rest_base") or t_slug
                                discovered_endpoints.append(f"{api_base}/{rest_base}")
                                discovered_endpoints.append(f"{api_base}/{rest_base}/")
                                links = tax_info.get("_links", {})
                                for link_item in links.get("wp:items", []):
                                    if isinstance(link_item, dict) and link_item.get("href"):
                                        discovered_endpoints.append(str(link_item["href"]))
                    if discovered_endpoints:
                        break
        except Exception:
            pass

    # Complete candidate endpoints list
    endpoints: List[str] = canonical_endpoints + discovered_endpoints
    seen_endpoints = set()
    discovered_feeds: List[Dict[str, Any]] = []

    for raw_url in endpoints:
        url = raw_url.strip()
        if not url or url in seen_endpoints:
            continue
        seen_endpoints.add(url)

        try:
            resp = client._get_request(
                url,
                params={"per_page": 100},
                headers={"Accept": "application/json"},
                timeout=15,
            )
            if hasattr(resp, "status_code") and resp.status_code == 200:
                data = resp.json()
                raw_items: List[Any] = []
                if isinstance(data, list):
                    raw_items = data
                elif isinstance(data, dict):
                    for sub_k in ("terms", "data", "feeds", "series", "items"):
                        sub_v = data.get(sub_k)
                        if isinstance(sub_v, list):
                            raw_items = sub_v
                            break
                    if not raw_items and ("name" in data or "id" in data or "slug" in data):
                        raw_items = [data]

                for item in raw_items:
                    if isinstance(item, dict):
                        try:
                            f_id = int(item.get("id") or item.get("term_id") or 0)
                        except (ValueError, TypeError):
                            f_id = 0
                        f_slug = str(item.get("slug") or item.get("term_id") or (f_id if f_id > 0 else "")).strip()
                        f_name = str(item.get("name") or item.get("title") or f_slug or DEFAULT_FEED_NAME).strip()

                        if f_name and (f_slug or f_id > 0):
                            if f_slug.lower() in ("admin", "author", "user") or "author" in f_slug.lower():
                                continue
                            if not any(f.get("id") == f_id or (f.get("slug") and f.get("slug") == f_slug) for f in discovered_feeds):
                                discovered_feeds.append({
                                    "id": f_id,
                                    "name": f_name,
                                    "slug": f_slug or f"feed-{f_id}",
                                })

                if discovered_feeds:
                    break
        except Exception:
            pass

    if discovered_feeds:
        default_items = [f for f in discovered_feeds if "(default)" in f.get("name", "").lower() or f.get("slug") == "default"]
        other_items = [f for f in discovered_feeds if f not in default_items]
        return default_items + other_items

    return [default_feed_placeholder]


def sanitize_castos_feeds(feeds: Any) -> List[Dict[str, Any]]:
    """Filter out non-podcast/author items and ensure valid feed structures."""
    if not isinstance(feeds, list):
        return []
    valid = []
    for item in feeds:
        if isinstance(item, dict):
            s = str(item.get("slug", "")).lower()
            n = str(item.get("name", "")).lower()
            if any(bad in s for bad in ("author", "admin", "user", "category", "tag", "ppma")):
                continue
            if any(bad in n for bad in ("author", "guest author", "wp user", "brad linder")):
                continue
            valid.append(item)
    return valid


def setup_castos_ui(tab_widget: Any, editor_layout: QVBoxLayout) -> None:
    """Build and insert the Castos Seriously Simple Podcasting section into the post editor layout."""
    tab_widget.wp_castos_section = CollapsibleSection(
        "Seriously Simple Podcasting (Castos)",
        tab_widget,
        is_expanded=False,
        subtitle="Podcast Feed, Episode Meta & Castos Player",
    )
    castos_container = QVBoxLayout()
    castos_container.setContentsMargins(4, 4, 4, 4)
    castos_container.setSpacing(6)

    # Checkbox: Designate this post as a Podcast Episode
    tab_widget.wp_cb_is_podcast = QCheckBox(
        "Designate this post as a Podcast Episode (Seriously Simple Podcasting / Castos)"
    )
    tab_widget.wp_cb_is_podcast.setToolTip(
        "When enabled, registers this post with Seriously Simple Podcasting, assigns the uploaded "
        "audio to your podcast RSS feed via post meta, and embeds the Castos web player while "
        "omitting the standard audio block."
    )
    castos_container.addWidget(tab_widget.wp_cb_is_podcast)

    # Dynamic Options Container (visible only when designated as a podcast)
    tab_widget.wp_podcast_options_widget = QWidget()
    opt_layout = QVBoxLayout(tab_widget.wp_podcast_options_widget)
    opt_layout.setContentsMargins(12, 4, 4, 4)
    opt_layout.setSpacing(6)

    # Feed selection header row
    feed_header = QHBoxLayout()
    feed_label = QLabel("Podcast Feeds / Series (select one or more):")
    tab_widget.wp_refresh_feeds_btn = QPushButton("Refresh Feeds")
    tab_widget.wp_refresh_feeds_btn.setToolTip("Query WordPress site for available podcast series feeds")
    tab_widget.wp_refresh_feeds_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")

    feed_header.addWidget(feed_label)
    feed_header.addStretch()
    feed_header.addWidget(tab_widget.wp_refresh_feeds_btn)
    opt_layout.addLayout(feed_header)

    # Multi-select checkable feeds list
    tab_widget.wp_podcast_feeds_list = QListWidget()
    tab_widget.wp_podcast_feeds_list.setMaximumHeight(85)
    tab_widget.wp_podcast_feeds_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    opt_layout.addWidget(tab_widget.wp_podcast_feeds_list)

    # Hidden combo kept for backwards compatibility with any external callers
    tab_widget.wp_podcast_feed_combo = QComboBox()
    tab_widget.wp_podcast_feed_combo.setVisible(False)
    tab_widget.wp_podcast_feed_combo.addItem(DEFAULT_FEED_NAME, DEFAULT_FEED_SLUG)

    # Episode Type and Numbers row
    meta_form = QHBoxLayout()
    meta_form.setSpacing(10)

    type_box = QHBoxLayout()
    type_box.addWidget(QLabel("Type:"))
    tab_widget.wp_podcast_type_combo = QComboBox()
    tab_widget.wp_podcast_type_combo.addItem("Full Episode", "full")
    tab_widget.wp_podcast_type_combo.addItem("Trailer", "trailer")
    tab_widget.wp_podcast_type_combo.addItem("Bonus", "bonus")
    type_box.addWidget(tab_widget.wp_podcast_type_combo)
    meta_form.addLayout(type_box)

    season_box = QHBoxLayout()
    season_box.addWidget(QLabel("Season #:"))
    tab_widget.wp_podcast_season_edit = QLineEdit()
    tab_widget.wp_podcast_season_edit.setMaximumWidth(60)
    tab_widget.wp_podcast_season_edit.setPlaceholderText("Optional")
    season_box.addWidget(tab_widget.wp_podcast_season_edit)
    meta_form.addLayout(season_box)

    ep_box = QHBoxLayout()
    ep_box.addWidget(QLabel("Episode #:"))
    tab_widget.wp_podcast_episode_num_edit = QLineEdit()
    tab_widget.wp_podcast_episode_num_edit.setMaximumWidth(60)
    tab_widget.wp_podcast_episode_num_edit.setPlaceholderText("Optional")
    ep_box.addWidget(tab_widget.wp_podcast_episode_num_edit)
    meta_form.addLayout(ep_box)

    meta_form.addStretch()
    opt_layout.addLayout(meta_form)

    # Castos player info notice
    notice_lbl = QLabel(
        "<b>Castos Player Embedding:</b> Displays the embedded Castos web player on this post page. "
        "The standard WordPress audio block is automatically omitted to prevent duplicate players."
    )
    notice_lbl.setWordWrap(True)
    notice_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding-top: 4px;")
    opt_layout.addWidget(notice_lbl)

    castos_container.addWidget(tab_widget.wp_podcast_options_widget)
    tab_widget.wp_castos_section.add_layout(castos_container)
    editor_layout.addWidget(tab_widget.wp_castos_section)

    # Initial visibility
    tab_widget.wp_podcast_options_widget.setVisible(False)

    # Wire event handlers
    def _on_podcast_toggled(checked: bool):
        tab_widget.wp_podcast_options_widget.setVisible(checked)
        if checked:
            if hasattr(tab_widget, "wp_cb_include_audio") and not tab_widget.wp_cb_include_audio.isChecked():
                tab_widget.wp_cb_include_audio.setChecked(True)
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                post = tab_widget.wp_post_items[tab_widget._current_post_index]
                post["is_podcast"] = checked
                if hasattr(tab_widget, "_update_post_list_item_label"):
                    tab_widget._update_post_list_item_label(tab_widget._current_post_index)

    tab_widget.wp_cb_is_podcast.toggled.connect(_on_podcast_toggled)

    def _on_feed_item_changed(item: QListWidgetItem):
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                sync_castos_to_post(tab_widget, tab_widget.wp_post_items[tab_widget._current_post_index])

    tab_widget.wp_podcast_feeds_list.itemChanged.connect(_on_feed_item_changed)

    def _on_feed_changed():
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                post = tab_widget.wp_post_items[tab_widget._current_post_index]
                feed_slug = tab_widget.wp_podcast_feed_combo.currentData()
                post["podcast_feed"] = feed_slug
                idx = tab_widget.wp_podcast_feed_combo.currentIndex()
                feed_data = tab_widget.wp_podcast_feed_combo.itemData(idx, Qt.ItemDataRole.UserRole + 1)
                post["podcast_feed_id"] = feed_data.get("id") if isinstance(feed_data, dict) else None

    tab_widget.wp_podcast_feed_combo.currentIndexChanged.connect(_on_feed_changed)

    def _on_type_changed():
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                tab_widget.wp_post_items[tab_widget._current_post_index]["podcast_episode_type"] = (
                    tab_widget.wp_podcast_type_combo.currentData()
                )

    tab_widget.wp_podcast_type_combo.currentIndexChanged.connect(_on_type_changed)

    def _on_season_edited(text: str):
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                tab_widget.wp_post_items[tab_widget._current_post_index]["podcast_season"] = text.strip()

    tab_widget.wp_podcast_season_edit.textEdited.connect(_on_season_edited)

    def _on_ep_num_edited(text: str):
        if not getattr(tab_widget, "_syncing_post_editor", False):
            if 0 <= tab_widget._current_post_index < len(tab_widget.wp_post_items):
                tab_widget.wp_post_items[tab_widget._current_post_index]["podcast_episode_number"] = text.strip()

    tab_widget.wp_podcast_episode_num_edit.textEdited.connect(_on_ep_num_edited)

    def _on_refresh_feeds_clicked():
        tab_widget._refresh_castos_feeds()

    tab_widget.wp_refresh_feeds_btn.clicked.connect(_on_refresh_feeds_clicked)


def populate_castos_feeds_combo(tab_widget: Any, feeds: List[Dict[str, Any]]) -> None:
    """Populate the podcast feed list and combo with discovered series/feeds."""
    valid_feeds = [f for f in (feeds or []) if isinstance(f, dict) and f.get("name")]
    if not valid_feeds:
        valid_feeds = [{"id": 0, "name": DEFAULT_FEED_NAME, "slug": DEFAULT_FEED_SLUG}]

    # Populate checkable feeds list
    if hasattr(tab_widget, "wp_podcast_feeds_list") and tab_widget.wp_podcast_feeds_list:
        feed_list = tab_widget.wp_podcast_feeds_list
        feed_list.blockSignals(True)
        feed_list.clear()
        for f in valid_feeds:
            name = f.get("name") or f.get("slug") or DEFAULT_FEED_NAME
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, f.get("id"))
            item.setData(Qt.ItemDataRole.UserRole + 1, f.get("slug") or DEFAULT_FEED_SLUG)
            item.setData(Qt.ItemDataRole.UserRole + 2, f)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            feed_list.addItem(item)
        feed_list.blockSignals(False)

    # Populate backward-compatible combo box
    if hasattr(tab_widget, "wp_podcast_feed_combo") and tab_widget.wp_podcast_feed_combo:
        combo = tab_widget.wp_podcast_feed_combo
        cur_slug = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for f in valid_feeds:
            name = f.get("name") or f.get("slug") or DEFAULT_FEED_NAME
            slug = f.get("slug") or DEFAULT_FEED_SLUG
            combo.addItem(name, slug)
            idx = combo.count() - 1
            combo.setItemData(idx, f, Qt.ItemDataRole.UserRole + 1)

        found_idx = combo.findData(cur_slug) if cur_slug else -1
        combo.setCurrentIndex(max(0, found_idx))
        combo.blockSignals(False)


def sync_castos_to_post(tab_widget: Any, post: Dict[str, Any]) -> None:
    """Extract Castos UI state and write into post dictionary."""
    if not hasattr(tab_widget, "wp_cb_is_podcast"):
        return
    post["is_podcast"] = tab_widget.wp_cb_is_podcast.isChecked()

    checked_ids: List[int] = []
    checked_slugs: List[str] = []

    if hasattr(tab_widget, "wp_podcast_feeds_list") and tab_widget.wp_podcast_feeds_list:
        feed_list = tab_widget.wp_podcast_feeds_list
        for i in range(feed_list.count()):
            it = feed_list.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                fid = it.data(Qt.ItemDataRole.UserRole)
                fslug = it.data(Qt.ItemDataRole.UserRole + 1)
                if fid is not None:
                    try:
                        fid_int = int(fid)
                        if fid_int > 0:
                            checked_ids.append(fid_int)
                    except (ValueError, TypeError):
                        pass
                if fslug:
                    checked_slugs.append(str(fslug))

    if not checked_slugs and hasattr(tab_widget, "wp_podcast_feed_combo"):
        slug = tab_widget.wp_podcast_feed_combo.currentData() or DEFAULT_FEED_SLUG
        idx = tab_widget.wp_podcast_feed_combo.currentIndex()
        feed_data = tab_widget.wp_podcast_feed_combo.itemData(idx, Qt.ItemDataRole.UserRole + 1)
        fid = feed_data.get("id") if isinstance(feed_data, dict) else None
        checked_slugs = [slug]
        if fid is not None:
            try:
                fid_int = int(fid)
                if fid_int > 0:
                    checked_ids = [fid_int]
            except (ValueError, TypeError):
                pass

    post["podcast_feed_ids"] = checked_ids
    post["podcast_feeds"] = checked_slugs
    post["podcast_feed"] = checked_slugs[0] if checked_slugs else DEFAULT_FEED_SLUG
    post["podcast_feed_id"] = checked_ids[0] if checked_ids else None

    if hasattr(tab_widget, "wp_podcast_type_combo"):
        post["podcast_episode_type"] = tab_widget.wp_podcast_type_combo.currentData() or "full"
    if hasattr(tab_widget, "wp_podcast_season_edit"):
        post["podcast_season"] = tab_widget.wp_podcast_season_edit.text().strip()
    if hasattr(tab_widget, "wp_podcast_episode_num_edit"):
        post["podcast_episode_number"] = tab_widget.wp_podcast_episode_num_edit.text().strip()

    if getattr(tab_widget, "wp_post_items", None) and len(tab_widget.wp_post_items) == 2:
        other_post = tab_widget.wp_post_items[0] if post is tab_widget.wp_post_items[1] else tab_widget.wp_post_items[1]
        p_title = post.get("title", "").strip().lower()
        o_title = other_post.get("title", "").strip().lower()
        stories = getattr(tab_widget.main_window, "stories", []) or []
        if p_title == o_title or len(stories) <= 1:
            for k in ("is_podcast", "podcast_feed_ids", "podcast_feeds", "podcast_feed", "podcast_feed_id", "podcast_episode_type", "podcast_season", "podcast_episode_number"):
                other_post[k] = post.get(k)


def load_castos_from_post(tab_widget: Any, post: Dict[str, Any]) -> None:
    """Set Castos UI controls from post dictionary."""
    if not hasattr(tab_widget, "wp_cb_is_podcast"):
        return
    is_pod = bool(post.get("is_podcast", False))
    tab_widget.wp_cb_is_podcast.setChecked(is_pod)
    tab_widget.wp_podcast_options_widget.setVisible(is_pod)

    target_ids = set()
    target_slugs = set()
    for x in (post.get("podcast_feed_ids") or []):
        try:
            xi = int(x)
            if xi > 0:
                target_ids.add(xi)
        except (ValueError, TypeError):
            pass
    for x in (post.get("podcast_feeds") or []):
        if str(x).strip():
            target_slugs.add(str(x).strip().lower())
    if post.get("podcast_feed_id"):
        try:
            xi = int(post.get("podcast_feed_id"))
            if xi > 0:
                target_ids.add(xi)
        except (ValueError, TypeError):
            pass
    if post.get("podcast_feed"):
        target_slugs.add(str(post.get("podcast_feed")).strip().lower())

    if hasattr(tab_widget, "wp_podcast_feeds_list") and tab_widget.wp_podcast_feeds_list:
        feed_list = tab_widget.wp_podcast_feeds_list
        feed_list.blockSignals(True)
        checked_any = False
        for i in range(feed_list.count()):
            it = feed_list.item(i)
            fid = it.data(Qt.ItemDataRole.UserRole)
            fslug = str(it.data(Qt.ItemDataRole.UserRole + 1) or "").strip().lower()
            should_check = False
            if fid is not None:
                try:
                    if int(fid) in target_ids:
                        should_check = True
                except (ValueError, TypeError):
                    pass
            if fslug and fslug in target_slugs:
                should_check = True

            if should_check:
                it.setCheckState(Qt.CheckState.Checked)
                checked_any = True
            else:
                it.setCheckState(Qt.CheckState.Unchecked)

        if is_pod and not checked_any and feed_list.count() > 0:
            feed_list.item(0).setCheckState(Qt.CheckState.Checked)
        feed_list.blockSignals(False)

    if hasattr(tab_widget, "wp_podcast_feed_combo") and tab_widget.wp_podcast_feed_combo:
        feed_slug = post.get("podcast_feed") or (list(target_slugs)[0] if target_slugs else DEFAULT_FEED_SLUG)
        idx = tab_widget.wp_podcast_feed_combo.findData(feed_slug)
        if idx >= 0:
            tab_widget.wp_podcast_feed_combo.setCurrentIndex(idx)
        else:
            tab_widget.wp_podcast_feed_combo.setCurrentIndex(0)

    if hasattr(tab_widget, "wp_podcast_type_combo"):
        ep_type = post.get("podcast_episode_type") or "full"
        t_idx = tab_widget.wp_podcast_type_combo.findData(ep_type)
        tab_widget.wp_podcast_type_combo.setCurrentIndex(max(0, t_idx))

    if hasattr(tab_widget, "wp_podcast_season_edit"):
        tab_widget.wp_podcast_season_edit.setText(str(post.get("podcast_season") or ""))
    if hasattr(tab_widget, "wp_podcast_episode_num_edit"):
        tab_widget.wp_podcast_episode_num_edit.setText(str(post.get("podcast_episode_number") or ""))


__all__ = [
    "SS_PODCAST_AUDIO_FILE",
    "SS_PODCAST_AUDIO_FILE_ID",
    "SS_PODCAST_DURATION",
    "SS_PODCAST_FILESIZE",
    "SS_PODCAST_FEED",
    "SS_PODCAST_EPISODE_TYPE",
    "SS_PODCAST_SEASON",
    "SS_PODCAST_EPISODE_NUMBER",
    "CASTOS_META_AUDIO_FILE",
    "CASTOS_META_AUDIO_FILE_ID",
    "CASTOS_META_DURATION",
    "CASTOS_META_FILESIZE",
    "CASTOS_META_EPISODE_TYPE",
    "CASTOS_META_SEASON",
    "CASTOS_META_EPISODE_NUMBER",
    "CASTOS_TAXONOMY_SERIES",
    "CASTOS_TAXONOMY_SERIES_FALLBACK",
    "CASTOS_SHORTCODE",
    "CASTOS_PLAYER_BLOCK",
    "DEFAULT_FEED_SLUG",
    "DEFAULT_FEED_NAME",
    "format_castos_duration",
    "build_castos_post_meta",
    "copy_podcast_meta",
    "fetch_castos_feeds",
    "sanitize_castos_feeds",
    "setup_castos_ui",
    "populate_castos_feeds_combo",
    "sync_castos_to_post",
    "load_castos_from_post",
]

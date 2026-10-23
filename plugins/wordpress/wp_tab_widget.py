"""WordPress export tab configuration widget and preview controller."""
from __future__ import annotations

import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QListWidgetItem,
    QMessageBox,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    format_time,
    safe_filename,
)
from plugins.wordpress.client import (
    WordPressClient,
    WordPressSettingsDialog,
    generate_wp_excerpt,
    _get_wp_password,
    is_wp_auth_error,
)
from plugins.wordpress.wp_post_builder import capture_video_frame, build_wp_post_items
from plugins.wordpress.wp_ui_builder import setup_wp_tab_ui

class WordPressExportTabWidget(QWidget):
    """Configuration and preview panel for WordPress Draft Posts."""

    def __init__(self, parent: QWidget, main_window: Any, metadata_editor_mode: bool = False):
        super().__init__(parent)
        self.main_window = main_window
        self.metadata_editor_mode = metadata_editor_mode
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._is_video_project = bool(getattr(self.main_window, "current_media_is_video", False))
        self._temp_preview_files = set()

        self._wp_scrub_timer = QTimer(self)
        self._wp_scrub_timer.setSingleShot(True)
        self._wp_scrub_timer.setInterval(120)
        self._wp_scrub_timer.timeout.connect(self._on_wp_scrub_timer_timeout)

        self.wp_cached_authors_data: List[Dict[str, Any]] = []
        self.wp_cached_categories_data: List[Dict[str, Any]] = []
        self.wp_post_items: List[Dict[str, Any]] = []
        self._current_post_index = 0
        self._syncing_post_editor = False

        self._setup_ui()

    def _setup_ui(self):
        setup_wp_tab_ui(self)

    def _on_wp_include_audio_toggled(self, checked: bool):
        self.settings.setValue("wp_include_audio", checked)
        if not checked:
            has_pod = any(p.get("is_podcast") for p in getattr(self, "wp_post_items", []))
            if hasattr(self, "wp_cb_is_podcast") and self.wp_cb_is_podcast.isChecked():
                has_pod = True
            if has_pod:
                QMessageBox.information(
                    self,
                    "Podcast Audio File Required",
                    "One or more posts are designated as a Podcast Episode. Seriously Simple Podcasting (Castos) requires an audio file upload to populate the episode file field and RSS feed.",
                )

    def _update_wp_conn_status(self):
        url = str(self.settings.value("wp_site_url", "") or "").rstrip("/")
        user = str(self.settings.value("wp_username", "") or "")
        if url and user:
            self.wp_conn_status.setText(f"Connected to: <b>{url}</b> (as {user})")
            self.wp_conn_status.setStyleSheet("color: #4ade80; font-size: 11px;")
        else:
            self.wp_conn_status.setText("WordPress credentials not configured.")
            self.wp_conn_status.setStyleSheet("color: #f87171; font-size: 11px;")

    def _open_wp_settings(self):
        dlg = WordPressSettingsDialog(parent=self)
        if dlg.exec():
            self._update_wp_conn_status()
            self._populate_wp_export_metadata(force_refresh=True)

    def _filter_authors_list(self, text: str):
        query = text.strip().lower()
        for i in range(self.wp_author_list.count()):
            item = self.wp_author_list.item(i)
            item.setHidden(query != "" and query not in item.text().lower())

    def _filter_categories_list(self, text: str):
        query = text.strip().lower()
        for i in range(self.wp_category_list.count()):
            item = self.wp_category_list.item(i)
            item.setHidden(query != "" and query not in item.text().lower())

    def _sync_to_proj(self, idx: int):
        if hasattr(self, "_sync_post_to_project"):
            self._sync_post_to_project(idx)

    def _on_title_edited(self, text: str):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        self.wp_post_items[self._current_post_index]["title"] = text.strip()
        self._update_post_list_item_label(self._current_post_index)
        self._sync_to_proj(self._current_post_index)

    def _on_excerpt_edited(self):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        self.wp_post_items[self._current_post_index]["excerpt"] = self.wp_excerpt_edit.toPlainText().strip()
        self._sync_to_proj(self._current_post_index)

    def _auto_generate_current_excerpt(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[self._current_post_index]
        raw_text = self.main_window._get_transcript_text_slice(post.get("start"), post.get("end")) if hasattr(self.main_window, "_get_transcript_text_slice") else ""
        excerpt = generate_wp_excerpt(raw_text, 55)
        self.wp_excerpt_edit.setPlainText(excerpt)
        post["excerpt"] = excerpt
        self._sync_to_proj(self._current_post_index)

    def _autofill_all_excerpts(self):
        for idx, post in enumerate(self.wp_post_items):
            raw_text = self.main_window._get_transcript_text_slice(post.get("start"), post.get("end")) if hasattr(self.main_window, "_get_transcript_text_slice") else ""
            post["excerpt"] = generate_wp_excerpt(raw_text, 55)
            self._sync_to_proj(idx)
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_excerpt_edit.setPlainText(self.wp_post_items[self._current_post_index].get("excerpt", ""))
        QMessageBox.information(self, "Auto-fill Excerpts", f"Generated transcript excerpts for all {len(self.wp_post_items)} posts.")

    def _on_author_item_changed(self, item):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        auth_ids, term_ids = self._get_editor_checked_authors()
        post = self.wp_post_items[self._current_post_index]
        post["author_ids"] = auth_ids
        post["author_term_ids"] = term_ids
        self._update_post_list_item_label(self._current_post_index)
        self._sync_to_proj(self._current_post_index)

    def _on_category_item_changed(self, item):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        cat_ids = self._get_editor_checked_categories()
        post = self.wp_post_items[self._current_post_index]
        post["category_ids"] = cat_ids
        self._update_post_list_item_label(self._current_post_index)
        self._sync_to_proj(self._current_post_index)

    def _clear_current_authors(self):
        self._set_editor_checked_authors([], [])
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["author_ids"] = []
            self.wp_post_items[self._current_post_index]["author_term_ids"] = []
            self._update_post_list_item_label(self._current_post_index)
            self._sync_to_proj(self._current_post_index)

    def _clear_current_categories(self):
        self._set_editor_checked_categories([])
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["category_ids"] = []
            self._update_post_list_item_label(self._current_post_index)
            self._sync_to_proj(self._current_post_index)

    def _get_selected_story_indices(self) -> List[int]:
        indices = list(getattr(self.main_window, "current_selected_story_indices", []) or [])
        if not indices and hasattr(self.main_window, "story_list"):
            indices = [self.main_window.story_list.row(it) for it in self.main_window.story_list.selectedItems()]
        return [i for i in indices if i >= 0]

    def _apply_authors_to_selected_stories(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_auth_ids = list(self.wp_post_items[self._current_post_index].get("author_ids", []))
        current_term_ids = list(self.wp_post_items[self._current_post_index].get("author_term_ids", []))
        selected_indices = self._get_selected_story_indices()
        stories = getattr(self.main_window, "stories", []) or []
        if not selected_indices:
            QMessageBox.information(self, "No Stories Selected", "Please select one or more stories in the story list.")
            return

        applied = 0
        for idx in selected_indices:
            if 0 <= idx < len(stories):
                st = stories[idx]
                if not hasattr(st, "metadata") or st.metadata is None:
                    st.metadata = {}
                wp_meta = st.metadata.setdefault("wordpress", {})
                wp_meta["author_ids"] = list(current_auth_ids)
                wp_meta["author_term_ids"] = list(current_term_ids)
                applied += 1

        for post in self.wp_post_items:
            for idx in selected_indices:
                if 0 <= idx < len(stories) and post.get("start") == stories[idx].start:
                    post["author_ids"] = list(current_auth_ids)
                    post["author_term_ids"] = list(current_term_ids)

        for i in range(len(self.wp_post_items)):
            self._update_post_list_item_label(i)

        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Authors", f"Applied author selection to {applied} selected stories.")

    def _apply_categories_to_selected_stories(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_cat_ids = list(self.wp_post_items[self._current_post_index].get("category_ids", []))
        selected_indices = self._get_selected_story_indices()
        stories = getattr(self.main_window, "stories", []) or []
        if not selected_indices:
            QMessageBox.information(self, "No Stories Selected", "Please select one or more stories in the story list.")
            return

        applied = 0
        for idx in selected_indices:
            if 0 <= idx < len(stories):
                st = stories[idx]
                if not hasattr(st, "metadata") or st.metadata is None:
                    st.metadata = {}
                wp_meta = st.metadata.setdefault("wordpress", {})
                wp_meta["category_ids"] = list(current_cat_ids)
                applied += 1

        for post in self.wp_post_items:
            for idx in selected_indices:
                if 0 <= idx < len(stories) and post.get("start") == stories[idx].start:
                    post["category_ids"] = list(current_cat_ids)

        for i in range(len(self.wp_post_items)):
            self._update_post_list_item_label(i)

        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Categories", f"Applied category selection to {applied} selected stories.")

    def _apply_thumbnails_to_selected_stories(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_img = self.wp_post_items[self._current_post_index].get("featured_image")
        current_mode = self.wp_post_items[self._current_post_index].get("featured_image_mode", "none")
        current_pos = self.wp_post_items[self._current_post_index].get("frame_pos")
        selected_indices = self._get_selected_story_indices()
        stories = getattr(self.main_window, "stories", []) or []
        if not selected_indices:
            QMessageBox.information(self, "No Stories Selected", "Please select one or more stories in the story list.")
            return

        applied = 0
        for idx in selected_indices:
            if 0 <= idx < len(stories):
                st = stories[idx]
                if not hasattr(st, "metadata") or st.metadata is None:
                    st.metadata = {}
                wp_meta = st.metadata.setdefault("wordpress", {})
                wp_meta["featured_image"] = current_img
                wp_meta["featured_image_mode"] = current_mode
                wp_meta["frame_pos"] = current_pos
                applied += 1

        for post in self.wp_post_items:
            for idx in selected_indices:
                if 0 <= idx < len(stories) and post.get("start") == stories[idx].start:
                    post["featured_image"] = current_img
                    post["featured_image_mode"] = current_mode
                    post["frame_pos"] = current_pos

        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Thumbnails", f"Applied thumbnail settings to {applied} selected stories.")

    def _apply_authors_to_all_posts(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_auth_ids = list(self.wp_post_items[self._current_post_index].get("author_ids", []))
        current_term_ids = list(self.wp_post_items[self._current_post_index].get("author_term_ids", []))
        for post in self.wp_post_items:
            post["author_ids"] = list(current_auth_ids)
            post["author_term_ids"] = list(current_term_ids)
        stories = getattr(self.main_window, "stories", []) or []
        for st in stories:
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            wp_meta = st.metadata.setdefault("wordpress", {})
            wp_meta["author_ids"] = list(current_auth_ids)
            wp_meta["author_term_ids"] = list(current_term_ids)
        for idx in range(len(self.wp_post_items)):
            self._update_post_list_item_label(idx)
        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Authors", f"Assigned author selection to all {len(self.wp_post_items)} posts.")

    def _apply_categories_to_all_posts(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_cat_ids = list(self.wp_post_items[self._current_post_index].get("category_ids", []))
        for post in self.wp_post_items:
            post["category_ids"] = list(current_cat_ids)
        stories = getattr(self.main_window, "stories", []) or []
        for st in stories:
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            wp_meta = st.metadata.setdefault("wordpress", {})
            wp_meta["category_ids"] = list(current_cat_ids)
        for idx in range(len(self.wp_post_items)):
            self._update_post_list_item_label(idx)
        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Categories", f"Assigned category selection to all {len(self.wp_post_items)} posts.")

    def _apply_thumbnails_to_all_posts(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        current_img = self.wp_post_items[self._current_post_index].get("featured_image")
        current_mode = self.wp_post_items[self._current_post_index].get("featured_image_mode", "none")
        current_pos = self.wp_post_items[self._current_post_index].get("frame_pos")
        for post in self.wp_post_items:
            post["featured_image"] = current_img
            post["featured_image_mode"] = current_mode
            post["frame_pos"] = current_pos
        stories = getattr(self.main_window, "stories", []) or []
        for st in stories:
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            wp_meta = st.metadata.setdefault("wordpress", {})
            wp_meta["featured_image"] = current_img
            wp_meta["featured_image_mode"] = current_mode
            wp_meta["frame_pos"] = current_pos
        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Thumbnails", f"Applied thumbnail settings to all {len(self.wp_post_items)} posts.")

    def _apply_podcast_to_selected_stories(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        from plugins.wordpress.castos import copy_podcast_meta
        cur_post = self.wp_post_items[self._current_post_index]
        selected_indices = self._get_selected_story_indices()
        stories = getattr(self.main_window, "stories", []) or []
        if not selected_indices:
            QMessageBox.information(self, "No Stories Selected", "Please select one or more stories in the story list.")
            return

        applied = 0
        for idx in selected_indices:
            if 0 <= idx < len(stories):
                st = stories[idx]
                if not hasattr(st, "metadata") or st.metadata is None:
                    st.metadata = {}
                copy_podcast_meta(st.metadata.setdefault("wordpress", {}), cur_post)
                applied += 1

        for post in self.wp_post_items:
            for idx in selected_indices:
                if 0 <= idx < len(stories) and post.get("start") == stories[idx].start:
                    copy_podcast_meta(post, cur_post)

        for i in range(len(self.wp_post_items)):
            self._update_post_list_item_label(i)

        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Podcast Settings", f"Applied podcast settings to {applied} selected stories.")

    def _apply_podcast_to_all_posts(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        from plugins.wordpress.castos import copy_podcast_meta
        cur_post = self.wp_post_items[self._current_post_index]
        for post in self.wp_post_items:
            copy_podcast_meta(post, cur_post)
        for st in (getattr(self.main_window, "stories", []) or []):
            if not hasattr(st, "metadata") or st.metadata is None:
                st.metadata = {}
            copy_podcast_meta(st.metadata.setdefault("wordpress", {}), cur_post)
        for idx in range(len(self.wp_post_items)):
            self._update_post_list_item_label(idx)
        if hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)
        QMessageBox.information(self, "Applied Podcast Settings", f"Assigned podcast settings to all {len(self.wp_post_items)} posts.")

    def _sync_post_to_project(self, idx: int):
        if not (0 <= idx < len(self.wp_post_items)):
            return
        post = self.wp_post_items[idx]
        task_label = post.get("task_label", "")
        # Full Episode
        if task_label == "Full Episode" or post.get("start") is None:
            proj_meta = getattr(self.main_window, "project_metadata", None)
            if not isinstance(proj_meta, dict):
                proj_meta = {}
                self.main_window.project_metadata = proj_meta
            wp_meta = proj_meta.setdefault("wordpress", {})
            wp_meta["title"] = post.get("title", "")
            wp_meta["excerpt"] = post.get("excerpt", "")
            proj_meta["title"] = post.get("title", "")
            proj_meta["excerpt"] = post.get("excerpt", "")
            wp_meta["author_ids"] = list(post.get("author_ids") or [])
            wp_meta["author_term_ids"] = list(post.get("author_term_ids") or [])
            wp_meta["category_ids"] = list(post.get("category_ids") or [])
            wp_meta["featured_image"] = post.get("featured_image")
            wp_meta["featured_image_mode"] = post.get("featured_image_mode", "none")
            wp_meta["frame_pos"] = post.get("frame_pos")
            wp_meta["status"] = post.get("status", "draft")
            wp_meta["slug"] = post.get("slug", "")
            wp_meta["tags"] = list(post.get("tags") or [])
            from plugins.wordpress.castos import copy_podcast_meta
            copy_podcast_meta(wp_meta, post)
        else:
            stories = getattr(self.main_window, "stories", []) or []
            target_story = None
            st_start = post.get("start")
            for st in stories:
                if st.start == st_start:
                    target_story = st
                    break
            if not target_story and task_label.startswith("Story "):
                try:
                    num_part = task_label.split(":")[0].replace("Story ", "").strip()
                    s_idx = int(num_part) - 1
                    if 0 <= s_idx < len(stories):
                        target_story = stories[s_idx]
                except Exception:
                    pass
            if target_story:
                if not hasattr(target_story, "metadata") or target_story.metadata is None:
                    target_story.metadata = {}
                wp_meta = target_story.metadata.setdefault("wordpress", {})
                new_title = post.get("title", "")
                wp_meta["title"] = new_title
                wp_meta["excerpt"] = post.get("excerpt", "")
                target_story.metadata["excerpt"] = post.get("excerpt", "")
                if new_title:
                    target_story.title = new_title

                # Resolve and sync author name to Story.metadata["author"]
                auth_names = []
                auth_ids_set = set(int(x) for x in (post.get("author_ids") or []))
                term_ids_set = set(int(x) for x in (post.get("author_term_ids") or []))
                for a in getattr(self, "wp_cached_authors_data", []):
                    if isinstance(a, dict):
                        if not a.get("is_guest") and (a.get("user_id") in auth_ids_set or a.get("id") in auth_ids_set):
                            auth_names.append(a.get("name", "User"))
                        elif a.get("is_guest") and (a.get("term_id") in term_ids_set or a.get("id") in term_ids_set):
                            auth_names.append(a.get("name", "Guest"))
                if auth_names:
                    target_story.metadata["author"] = ", ".join(auth_names)
                elif post.get("manual_author"):
                    target_story.metadata["author"] = post.get("manual_author", "")

                wp_meta["author_ids"] = list(post.get("author_ids") or [])
                wp_meta["author_term_ids"] = list(post.get("author_term_ids") or [])
                wp_meta["category_ids"] = list(post.get("category_ids") or [])
                wp_meta["featured_image"] = post.get("featured_image")
                wp_meta["featured_image_mode"] = post.get("featured_image_mode", "none")
                target_story.metadata["featured_image"] = post.get("featured_image")
                target_story.metadata["featured_image_mode"] = post.get("featured_image_mode", "none")
                wp_meta["frame_pos"] = post.get("frame_pos")
                wp_meta["status"] = post.get("status", "draft")
                wp_meta["slug"] = post.get("slug", "")
                wp_meta["tags"] = list(post.get("tags") or [])
                from plugins.wordpress.castos import copy_podcast_meta
                copy_podcast_meta(wp_meta, post)

                # Update main window story list display
                if hasattr(self.main_window, "refresh_story_list"):
                    self.main_window.refresh_story_list()

                # If this target story is currently active in the main window, update its UI fields
                selected_indices = getattr(self.main_window, "current_selected_story_indices", []) or []
                is_selected = (target_story in stories and stories.index(target_story) in selected_indices)
                if is_selected or getattr(self.main_window, "current_story", None) == target_story:
                    if hasattr(self.main_window, "title_input") and self.main_window.title_input:
                        self.main_window.title_input.setText(target_story.title or "")
                    if hasattr(self.main_window, "excerpt_edit") and self.main_window.excerpt_edit:
                        self.main_window.excerpt_edit.setText(target_story.metadata.get("excerpt", "") or "")
                    if hasattr(self.main_window, "author_input") and self.main_window.author_input:
                        self.main_window.author_input.setText(target_story.metadata.get("author", "") or "")

        if hasattr(self.main_window, "mark_project_dirty"):
            self.main_window.mark_project_dirty("Update WordPress Metadata")
        elif hasattr(self.main_window, "set_unsaved_changes"):
            self.main_window.set_unsaved_changes(True)

    def save_all_posts_to_project(self):
        """Persist all post metadata and export options back into stories and project_metadata."""
        for idx in range(len(self.wp_post_items)):
            self._sync_post_to_project(idx)
        proj_meta = getattr(self.main_window, "project_metadata", None)
        if not isinstance(proj_meta, dict):
            proj_meta = {}
            self.main_window.project_metadata = proj_meta
        wp_meta = proj_meta.setdefault("wordpress", {})
        if hasattr(self, "wp_custom_text_edit") and self.wp_custom_text_edit:
            wp_meta["custom_notice"] = self.wp_custom_text_edit.toPlainText().strip()
        if hasattr(self, "wp_rad_pos_top") and self.wp_rad_pos_top:
            wp_meta["notice_placement"] = "top" if self.wp_rad_pos_top.isChecked() else "bottom"
        if hasattr(self.main_window, "save_project"):
            try:
                self.main_window.save_project()
            except Exception as e:
                print(f"[WP METADATA] Error auto-saving project: {e}")

    def _update_post_list_item_label(self, idx: int):
        if not (0 <= idx < len(self.wp_post_items)) or not hasattr(self, "wp_posts_list") or idx >= self.wp_posts_list.count():
            return
        post = self.wp_post_items[idx]
        title = post.get("title") or post.get("task_label", f"Post {idx + 1}")
        n_auths = len(post.get("author_ids", [])) + len(post.get("author_term_ids", []))
        n_cats = len(post.get("category_ids", []))
        meta_sub = []
        if n_auths:
            meta_sub.append(f"{n_auths} author" + ("s" if n_auths > 1 else ""))
        if n_cats:
            meta_sub.append(f"{n_cats} cat" + ("s" if n_cats > 1 else ""))
        if post.get("is_podcast"):
            meta_sub.append("Podcast")
        meta_str = f" ({', '.join(meta_sub)})" if meta_sub else ""
        self.wp_posts_list.item(idx).setText(f"{post.get('task_label', 'Post')}: {title}{meta_str}")

    def _on_wp_post_selection_changed(self, row: int):
        if row < 0 or row >= len(self.wp_post_items):
            return
        self._load_post_editor_state(row)

    def _get_editor_checked_authors(self) -> Tuple[List[int], List[int]]:
        author_ids = []
        author_term_ids = []
        for i in range(self.wp_author_list.count()):
            item = self.wp_author_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    if data.get("is_guest"):
                        tid = data.get("term_id") or data.get("id")
                        if tid:
                            author_term_ids.append(int(tid))
                    else:
                        uid = data.get("user_id") or data.get("id")
                        if uid:
                            author_ids.append(int(uid))
        return author_ids, author_term_ids

    def _set_editor_checked_authors(self, author_ids: List[int], author_term_ids: List[int]):
        self._syncing_post_editor = True
        auth_set = set(int(x) for x in (author_ids or []))
        term_set = set(int(x) for x in (author_term_ids or []))
        for i in range(self.wp_author_list.count()):
            item = self.wp_author_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            checked = False
            if isinstance(data, dict):
                if data.get("is_guest"):
                    tid = data.get("term_id") or data.get("id")
                    if tid and int(tid) in term_set:
                        checked = True
                else:
                    uid = data.get("user_id") or data.get("id")
                    if uid and int(uid) in auth_set:
                        checked = True
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_post_editor = False

    def _get_editor_checked_categories(self) -> List[int]:
        cat_ids = []
        for i in range(self.wp_category_list.count()):
            item = self.wp_category_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                cid = item.data(Qt.ItemDataRole.UserRole)
                if cid is not None:
                    cat_ids.append(int(cid))
        return cat_ids

    def _set_editor_checked_categories(self, cat_ids: List[int]):
        self._syncing_post_editor = True
        cid_set = set(int(x) for x in (cat_ids or []))
        for i in range(self.wp_category_list.count()):
            item = self.wp_category_list.item(i)
            cid = item.data(Qt.ItemDataRole.UserRole)
            checked = (cid is not None and int(cid) in cid_set)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._syncing_post_editor = False

    def _get_wp_post_bounds(self, post_index=None) -> Tuple[float, float]:
        idx = self._current_post_index if post_index is None else post_index
        if 0 <= idx < len(self.wp_post_items):
            p = self.wp_post_items[idx]
            if p.get("start") is not None and p.get("end") is not None:
                t_start = float(p["start"])
                t_end = float(p["end"])
                return t_start, max(t_start + 0.1, t_end)
        dur = max(0.1, float(getattr(self.main_window, "duration", 0.0) or 0.0))
        return 0.0, dur

    def _sync_wp_slider_to_pos(self, pos: float):
        t_min, t_max = self._get_wp_post_bounds()
        clamped = max(t_min, min(t_max, float(pos)))
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self.wp_post_items[self._current_post_index]["frame_pos"] = clamped
        span = max(0.001, t_max - t_min)
        val = int(round(((clamped - t_min) / span) * 10000))
        self.wp_scrub_slider.blockSignals(True)
        self.wp_scrub_slider.setValue(max(0, min(10000, val)))
        self.wp_scrub_slider.blockSignals(False)
        self.wp_scrub_time_label.setText(format_time(clamped, include_millis=True))

    def _on_wp_slider_value_changed(self, val: int):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        t_min, t_max = self._get_wp_post_bounds()
        pos = t_min + (val / 10000.0) * (t_max - t_min)
        post = self.wp_post_items[self._current_post_index]
        post["frame_pos"] = pos
        self.wp_scrub_time_label.setText(format_time(pos, include_millis=True))
        self._wp_scrub_timer.start(120)

    def _on_wp_scrub_timer_timeout(self):
        if 0 <= self._current_post_index < len(self.wp_post_items):
            post = self.wp_post_items[self._current_post_index]
            pos = post.get("frame_pos")
            self._capture_wp_frame(pos=pos)

    def _on_wp_step(self, delta_secs: float):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[self._current_post_index]
        t_min, t_max = self._get_wp_post_bounds()
        cur_pos = post.get("frame_pos", t_min)
        new_pos = max(t_min, min(t_max, cur_pos + delta_secs))
        self._sync_wp_slider_to_pos(new_pos)
        self._capture_wp_frame(pos=new_pos)

    def _on_wp_sync_playhead(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        t_min, t_max = self._get_wp_post_bounds()
        playhead_pos = float(getattr(self.main_window, "current_position", 0.0) or 0.0)
        new_pos = max(t_min, min(t_max, playhead_pos))
        self._sync_wp_slider_to_pos(new_pos)
        self._capture_wp_frame(pos=new_pos)

    def _load_post_editor_state(self, index: int):
        if not (0 <= index < len(self.wp_post_items)):
            return
        self._current_post_index = index
        post = self.wp_post_items[index]

        self._syncing_post_editor = True
        self.wp_current_post_header.setText(f"<b>Post Settings: {html.escape(post.get('task_label', 'Post'))}</b>")
        self.wp_title_edit.setText(post.get("title", ""))
        self.wp_excerpt_edit.setPlainText(post.get("excerpt", ""))

        mode = post.get("featured_image_mode", "none")
        img = post.get("featured_image")
        frame_pos = post.get("frame_pos")
        if frame_pos is None:
            t_min, _ = self._get_wp_post_bounds(index)
            frame_pos = t_min
            post["frame_pos"] = frame_pos

        if mode == "grab" and self._is_video_project:
            self.wp_rad_thumb_grab.setChecked(True)
            self.wp_scrub_widget.setVisible(True)
            self.wp_browse_widget.setVisible(False)
            self._sync_wp_slider_to_pos(frame_pos)
            if img and Path(img).exists():
                self.wp_thumb_path_label.setText(f"Video frame captured at {format_time(frame_pos, include_millis=True)}")
                pix = QPixmap(str(img)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.wp_thumb_preview_label.setPixmap(pix)
            else:
                self.wp_thumb_path_label.setText("Frame will be captured from video")
                self.wp_thumb_preview_label.clear()
                self.wp_thumb_preview_label.setText("Video Frame")
        elif mode == "file" and img:
            self.wp_rad_thumb_file.setChecked(True)
            self.wp_scrub_widget.setVisible(False)
            self.wp_browse_widget.setVisible(True)
            self.wp_thumb_path_label.setText(Path(img).name)
            if Path(img).exists():
                pix = QPixmap(str(img)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.wp_thumb_preview_label.setPixmap(pix)
            else:
                self.wp_thumb_preview_label.clear()
                self.wp_thumb_preview_label.setText("Image not found")
        else:
            self.wp_rad_thumb_none.setChecked(True)
            self.wp_scrub_widget.setVisible(False)
            self.wp_browse_widget.setVisible(False)
            self.wp_thumb_path_label.setText("No image selected")
            self.wp_thumb_preview_label.clear()
            self.wp_thumb_preview_label.setText("No Thumbnail")

        self._syncing_post_editor = False

        self._set_editor_checked_authors(post.get("author_ids", []), post.get("author_term_ids", []))
        self._set_editor_checked_categories(post.get("category_ids", []))

        from plugins.wordpress.castos import load_castos_from_post
        load_castos_from_post(self, post)

    def _on_wp_thumb_mode_changed(self):
        if self._syncing_post_editor or not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        post = self.wp_post_items[self._current_post_index]
        if self.wp_rad_thumb_none.isChecked():
            self.wp_scrub_widget.setVisible(False)
            self.wp_browse_widget.setVisible(False)
            self.wp_thumb_path_label.setText("No image selected")
            self.wp_thumb_preview_label.clear()
            self.wp_thumb_preview_label.setText("No Thumbnail")
            post["featured_image"] = None
            post["featured_image_mode"] = "none"
            if hasattr(self, "_sync_post_to_project"):
                self._sync_post_to_project(self._current_post_index)
        elif self.wp_rad_thumb_grab.isChecked():
            self.wp_browse_widget.setVisible(False)
            self.wp_scrub_widget.setVisible(True)
            if post.get("frame_pos") is None:
                t_min, _ = self._get_wp_post_bounds()
                post["frame_pos"] = t_min
            self._sync_wp_slider_to_pos(post["frame_pos"])
            self._capture_wp_frame(pos=post.get("frame_pos"))
        elif self.wp_rad_thumb_file.isChecked():
            self.wp_scrub_widget.setVisible(False)
            self.wp_browse_widget.setVisible(True)
            custom_path = post.get("featured_image")
            if custom_path and Path(custom_path).exists() and post.get("featured_image_mode") == "file":
                self.wp_thumb_path_label.setText(Path(custom_path).name)
                pix = QPixmap(str(custom_path)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.wp_thumb_preview_label.setPixmap(pix)
            else:
                self.wp_thumb_path_label.setText("Click Browse to select image file")
                self.wp_thumb_preview_label.clear()
                self.wp_thumb_preview_label.setText("No Image\nSelected")
            if hasattr(self, "_sync_post_to_project"):
                self._sync_post_to_project(self._current_post_index)

    def _capture_wp_frame(self, pos=None):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return None
        if not self._is_video_project:
            self.wp_thumb_preview_label.setText("Audio-only media\n(No video frames)")
            return None
        post = self.wp_post_items[self._current_post_index]
        media_file = getattr(self.main_window, "audio_file", None)
        if not media_file or not Path(media_file).exists():
            self.wp_thumb_preview_label.setText("No media\nloaded")
            return None

        if pos is None:
            if post.get("frame_pos") is not None:
                pos = float(post["frame_pos"])
            elif post.get("start") is not None:
                pos = float(post["start"])
            else:
                pos = float(getattr(self.main_window, "current_position", 0.0) or 0.0)

        post["frame_pos"] = float(pos)
        out_dir = Path(tempfile.gettempdir())
        out_path = out_dir / f"rtvs_wp_frame_{self._current_post_index}_{os.getpid()}.jpg"
        if capture_video_frame(str(media_file), float(pos), str(out_path), timeout=5.0):
            post["featured_image"] = str(out_path)
            post["featured_image_mode"] = "grab"
            self._temp_preview_files.add(str(out_path))
            self.wp_thumb_path_label.setText(f"Video frame captured at {format_time(pos, include_millis=True)}")
            pix = QPixmap(str(out_path)).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.wp_thumb_preview_label.setPixmap(pix)
            if hasattr(self, "_sync_post_to_project"):
                self._sync_post_to_project(self._current_post_index)
            return str(out_path)
        self.wp_thumb_preview_label.setText("Frame capture\nfailed")
        return None

    def _on_wp_browse_thumb(self):
        if not (0 <= self._current_post_index < len(self.wp_post_items)):
            return
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select WordPress Featured Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*.*)",
        )
        if fn:
            post = self.wp_post_items[self._current_post_index]
            post["featured_image"] = fn
            post["featured_image_mode"] = "file"
            self.wp_rad_thumb_file.setChecked(True)
            self.wp_thumb_path_label.setText(Path(fn).name)
            pix = QPixmap(fn).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.wp_thumb_preview_label.setPixmap(pix)
            if hasattr(self, "_sync_post_to_project"):
                self._sync_post_to_project(self._current_post_index)

    def _cleanup_temp_files(self) -> None:
        """Purge temporary frame grabs and preview images."""
        if hasattr(self, "_temp_preview_files") and self._temp_preview_files:
            for temp_f in list(self._temp_preview_files):
                try:
                    if temp_f and Path(temp_f).exists():
                        Path(temp_f).unlink(missing_ok=True)
                except Exception:
                    pass
            self._temp_preview_files.clear()

    def closeEvent(self, event: Any) -> None:
        """Persist current post state and clean up temp files on widget/dialog closure."""
        try:
            if hasattr(self, "save_all_posts_to_project"):
                self.save_all_posts_to_project()
        except Exception:
            pass
        self._cleanup_temp_files()
        super().closeEvent(event)

    def rebuild_post_items(self, scope: Optional[str] = None):
        if getattr(self, "wp_post_items", None) and hasattr(self, "_sync_post_to_project"):
            for idx in range(len(self.wp_post_items)):
                self._sync_post_to_project(idx)
        if getattr(self, "metadata_editor_mode", False):
            scope = "full_and_all_stories"
        elif scope is None:
            dlg = self.window()
            if hasattr(dlg, "scope_combo"):
                scope = dlg.scope_combo.currentData()
            elif hasattr(self.parent(), "scope_combo"):
                scope = self.parent().scope_combo.currentData()
            else:
                scope = "full"
        prim_lang = self.wp_primary_lang_combo.currentData() if hasattr(self, "wp_primary_lang_combo") and self.wp_primary_lang_combo else "en"
        self.wp_post_items = build_wp_post_items(self.main_window, scope, prim_lang, getattr(self, "wp_post_items", []))
        self._current_post_index = 0

        self.wp_posts_list.blockSignals(True)
        self.wp_posts_list.clear()
        for idx in range(len(self.wp_post_items)):
            self.wp_posts_list.addItem("")
            self._update_post_list_item_label(idx)
        self.wp_posts_list.blockSignals(False)

        has_multi = len(self.wp_post_items) > 1
        self.wp_post_nav_widget.setVisible(has_multi)
        self.wp_bulk_box.setVisible(has_multi)

        if self.wp_posts_list.count() > 0:
            self.wp_posts_list.setCurrentRow(0)
        self._load_post_editor_state(0)

        dlg = self.window()
        if hasattr(dlg, "_update_export_button_label") and callable(dlg._update_export_button_label):
            dlg._update_export_button_label()
        elif hasattr(self.parent(), "_update_export_button_label") and callable(self.parent()._update_export_button_label):
            self.parent()._update_export_button_label()

    def _populate_wp_export_metadata(self, force_refresh: bool = False):
        categories = []
        authors = []
        podcast_feeds = []

        if not force_refresh:
            cached_cats = self.settings.value("wp_cached_categories", "")
            cached_auths = self.settings.value("wp_cached_authors", "")
            cached_feeds = self.settings.value("wp_cached_podcast_feeds", "")
            if cached_cats and cached_auths:
                try:
                    categories = json.loads(cached_cats)
                    authors = json.loads(cached_auths)
                except Exception:
                    pass
            if cached_feeds:
                try:
                    from plugins.wordpress.castos import sanitize_castos_feeds
                    podcast_feeds = sanitize_castos_feeds(json.loads(cached_feeds))
                except Exception:
                    pass

        if not categories or not authors or not podcast_feeds or len(podcast_feeds) <= 1 or force_refresh:
            from plugins.wordpress.client import get_wp_client
            client = get_wp_client()
            if client:
                try:
                    categories = client.get_categories() if hasattr(client, "get_categories") else []
                    authors = client.get_authors() if hasattr(client, "get_authors") else []
                    podcast_feeds = client.get_podcast_feeds() if hasattr(client, "get_podcast_feeds") else []
                    self.settings.setValue("wp_cached_categories", json.dumps(categories))
                    self.settings.setValue("wp_cached_authors", json.dumps(authors))
                    self.settings.setValue("wp_cached_podcast_feeds", json.dumps(podcast_feeds))
                except Exception as exc:
                    print(f"[WORDPRESS EXPORT UI] Failed to fetch metadata: {exc}")

        self.wp_cached_authors_data = authors or []
        self.wp_cached_categories_data = categories or []
        self.wp_cached_podcast_feeds = podcast_feeds or [{"id": 0, "name": "Default Podcast Feed", "slug": "default"}]

        from plugins.wordpress.castos import populate_castos_feeds_combo
        populate_castos_feeds_combo(self, self.wp_cached_podcast_feeds)

        self.wp_author_list.blockSignals(True)
        self.wp_author_list.clear()
        for author in self.wp_cached_authors_data:
            if isinstance(author, dict):
                name = author.get("name", "Unknown Author")
                slug = author.get("slug", "")
                slug_str = f" (@{slug})" if slug else ""
                auth_type = author.get("type", "Guest Author" if author.get("is_guest") else "WP User")
                item = QListWidgetItem(f"{name}{slug_str} [{auth_type}]")
                item.setData(Qt.ItemDataRole.UserRole, author)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.wp_author_list.addItem(item)
        self.wp_author_list.blockSignals(False)

        self.wp_category_list.blockSignals(True)
        self.wp_category_list.clear()
        for cat in self.wp_cached_categories_data:
            if isinstance(cat, dict):
                item = QListWidgetItem(cat.get("name", "Unnamed Category"))
                item.setData(Qt.ItemDataRole.UserRole, cat.get("id"))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.wp_category_list.addItem(item)
        self.wp_category_list.blockSignals(False)

    def _refresh_castos_feeds(self):
        from plugins.wordpress.client import get_wp_client
        from plugins.wordpress.castos import populate_castos_feeds_combo
        client = get_wp_client()
        if not client or not client.is_configured():
            reply = QMessageBox.question(
                self,
                "WordPress Credentials Required",
                "WordPress site connection is not configured or missing login credentials.\n\nWould you like to enter or correct your website URL and login details now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_wp_settings()
            return

        feeds = []
        if hasattr(client, "get_podcast_feeds"):
            try:
                feeds = client.get_podcast_feeds()
                self.settings.setValue("wp_cached_podcast_feeds", json.dumps(feeds))
            except Exception as exc:
                print(f"[CASTOS] Error refreshing feeds: {exc}")
        self.wp_cached_podcast_feeds = feeds or [{"id": 0, "name": "Default Podcast Feed", "slug": "default"}]
        populate_castos_feeds_combo(self, self.wp_cached_podcast_feeds)
        QMessageBox.information(self, "Podcast Feeds", f"Refreshed podcast feeds ({len(self.wp_cached_podcast_feeds)} available).")

    def _refresh_wp_metadata(self):
        from plugins.wordpress.client import get_wp_client
        client = get_wp_client()
        if not client or not client.is_configured():
            reply = QMessageBox.question(
                self,
                "WordPress Credentials Required",
                "WordPress site connection is not configured or missing login credentials.\n\nWould you like to enter or correct your website URL and login details now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_wp_settings()
            return

        if not os.environ.get("RTVS_TEST_MODE"):
            ok, test_msg = client.test_connection()
            if not ok:
                reply = QMessageBox.question(
                    self,
                    "WordPress Connection Failed",
                    f"Could not connect to WordPress:\n{test_msg}\n\nWould you like to enter or correct your website URL and login details now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._open_wp_settings()
                return

        self._populate_wp_export_metadata(force_refresh=True)
        if 0 <= self._current_post_index < len(self.wp_post_items):
            self._load_post_editor_state(self._current_post_index)
        QMessageBox.information(self, "WordPress Metadata", "Author, Category, and Podcast Feed lists refreshed successfully.")


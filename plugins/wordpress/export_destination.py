"""WordPress Export Destination for UnifiedExportDialog."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    INTERNAL_APP_ID,
    safe_filename,
    safe_process_events,
)
from plugins.base import ExportDestination
from plugins.wordpress.client import (
    WordPressClient,
    WordPressSettingsDialog,
    execute_wordpress_upload,
    _get_wp_password,
    build_episode_stories_toc,
    format_parent_episode_notice,
    is_wp_auth_error,
)
from plugins.wordpress.wp_post_builder import capture_video_frame, build_wp_post_items
from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget

class WordPressExportDestination(ExportDestination):
    """Export destination handler for WordPress REST API Draft Posts."""

    def __init__(self, plugin: Any = None):
        super().__init__(
            id="wordpress",
            title="WordPress Draft Post",
            description="Extracts audio and publishes formatted draft posts directly to your WordPress site.",
            icon="wordpress",
        )
        self.plugin = plugin
        self.tab_widget: Optional[WordPressExportTabWidget] = None

    @property
    def button_label(self) -> str:
        tab = getattr(self, "tab_widget", None)
        if tab and hasattr(tab, "wp_post_items") and tab.wp_post_items:
            count = len(tab.wp_post_items)
            return "Export to WordPress Drafts..." if count > 1 else "Export to WordPress Draft"
        return "Export to WordPress Draft"

    @button_label.setter
    def button_label(self, val: Any) -> None:
        self._button_label_override = val

    def get_export_button_label(self) -> str:
        return self.button_label

    @property
    def widget(self) -> Any:
        return self.tab_widget

    @widget.setter
    def widget(self, val: Any) -> None:
        self.tab_widget = val

    def create_widget(self, parent: Any, main_window: Any) -> Any:
        self.tab_widget = WordPressExportTabWidget(parent, main_window)
        return self.tab_widget

    def on_scope_changed(self, scope: str, stories: list) -> None:
        if self.tab_widget:
            self.tab_widget.rebuild_post_items(scope=scope)

    def validate(self) -> Tuple[bool, str]:
        if not self.tab_widget:
            return False, "WordPress tab not initialized."
        w = self.tab_widget
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        url = str(settings.value("wp_site_url", "") or "").strip()
        user = str(settings.value("wp_username", "") or "").strip()
        pwd = _get_wp_password(user) if user else ""
        if not (url and user and pwd):
            return False, "WordPress is not configured. Please enter your Site URL, Username, and Application Password in Settings before exporting."
        if url in ("https://example.com", "http://example.com", "example.com") and not os.environ.get("RTVS_TEST_MODE"):
            return False, f"WordPress Site URL '{url}' is set to the default example.com placeholder. Please enter your actual website URL in WordPress Settings."
        if not w.wp_cb_en.isChecked() and not w.wp_cb_es.isChecked():
            return False, "Please select at least one language for WordPress export (English or Spanish)."
        if not w.wp_post_items:
            return False, "No posts configured for WordPress export."
        return True, ""

    def get_export_data(self) -> Dict[str, Any]:
        if not self.tab_widget:
            return {}
        w = self.tab_widget
        return {
            "wp_posts": list(w.wp_post_items),
            "include_english": w.wp_cb_en.isChecked(),
            "include_spanish": w.wp_cb_es.isChecked(),
            "spanish_presentation": w.wp_pres_combo.currentData(),
            "accordion_pos": "bottom" if (hasattr(w, "wp_rad_acc_bottom") and w.wp_rad_acc_bottom.isChecked()) else "top",
            "primary_language": w.wp_primary_lang_combo.currentData(),
            "custom_notice": w.wp_custom_text_edit.toPlainText().strip(),
            "notice_placement": "top" if w.wp_rad_pos_top.isChecked() else "bottom",
            "link_parent_episode": w.wp_cb_link_parent.isChecked() if hasattr(w, "wp_cb_link_parent") else True,
            "parent_episode_pos": ("bottom" if w.wp_rad_parent_bottom.isChecked() else "top") if hasattr(w, "wp_rad_parent_bottom") else "bottom",
            "parent_episode_template": w.wp_parent_template_edit.text().strip() if hasattr(w, "wp_parent_template_edit") else "",
            "update_parent_toc": w.wp_cb_update_parent_toc.isChecked() if hasattr(w, "wp_cb_update_parent_toc") else True,
            "include_audio": w.wp_cb_include_audio.isChecked() if hasattr(w, "wp_cb_include_audio") else True,
            "apply_audio_fades": w.wp_cb_apply_fades.isChecked() if hasattr(w, "wp_cb_apply_fades") else True,
        }

    def execute_export(self, main_window: Any, export_data: Dict[str, Any], progress_dialog: Any = None) -> bool:
        settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        url = str(settings.value("wp_site_url", "") or "").strip()
        user = str(settings.value("wp_username", "") or "").strip()
        pwd = _get_wp_password(user) if user else ""
        parent_widget = main_window if isinstance(main_window, QWidget) else (self.tab_widget if isinstance(getattr(self, "tab_widget", None), QWidget) else None)
        show_summary_dialog = bool(export_data.get("show_completion_dialog", True))

        def prompt_configure_credentials(reason_text: str) -> bool:
            reply = QMessageBox.question(
                parent_widget,
                "WordPress Credentials Required",
                f"{reason_text}\n\nWould you like to enter or correct your website URL and login details now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                dlg = WordPressSettingsDialog(parent=parent_widget)
                if dlg.exec():
                    if self.tab_widget:
                        self.tab_widget._update_wp_conn_status()
                        self.tab_widget._populate_wp_export_metadata(force_refresh=True)
                    return True
            return False

        if not (url and user and pwd):
            if show_summary_dialog:
                if prompt_configure_credentials("WordPress site connection is not configured or missing login credentials."):
                    url = str(settings.value("wp_site_url", "") or "").strip()
                    user = str(settings.value("wp_username", "") or "").strip()
                    pwd = _get_wp_password(user) if user else ""
            if not (url and user and pwd):
                return False

        if url in ("https://example.com", "http://example.com", "example.com") and not os.environ.get("RTVS_TEST_MODE"):
            if show_summary_dialog:
                if prompt_configure_credentials(f"The WordPress Site URL in your settings ('{url}') is set to 'example.com'."):
                    url = str(settings.value("wp_site_url", "") or "").strip()
                    user = str(settings.value("wp_username", "") or "").strip()
                    pwd = _get_wp_password(user) if user else ""
            if url in ("https://example.com", "http://example.com", "example.com") and not os.environ.get("RTVS_TEST_MODE"):
                return False

        client = WordPressClient(url, user, pwd)

        if not os.environ.get("RTVS_TEST_MODE"):
            ok, conn_msg = client.test_connection()
            if not ok:
                if show_summary_dialog:
                    if prompt_configure_credentials(f"Could not connect to WordPress site:\n{conn_msg}"):
                        url = str(settings.value("wp_site_url", "") or "").strip()
                        user = str(settings.value("wp_username", "") or "").strip()
                        pwd = _get_wp_password(user) if user else ""
                        if not (url and user and pwd):
                            return False
                        client = WordPressClient(url, user, pwd)
                        ok, conn_msg = client.test_connection()
                        if not ok:
                            QMessageBox.critical(parent_widget, "Connection Failed", conn_msg)
                            return False
                    else:
                        return False
                else:
                    return False

        wp_posts = export_data.get("wp_posts", [])
        if not wp_posts:
            if show_summary_dialog:
                QMessageBox.warning(parent_widget, "No Posts", "No posts were configured for export.")
            return False

        # Save user preferences
        settings.setValue("wp_link_parent_episode", export_data.get("link_parent_episode", True))
        settings.setValue("wp_parent_episode_pos", export_data.get("parent_episode_pos", "bottom"))
        settings.setValue("wp_parent_template", export_data.get("parent_episode_template", "This story was broadcast as part of {episode_link}."))
        settings.setValue("wp_update_parent_toc", export_data.get("update_parent_toc", True))
        inc_audio = export_data.get("include_audio", True)
        settings.setValue("wp_include_audio", inc_audio)
        apply_audio_fades = export_data.get("apply_audio_fades", True)
        settings.setValue("wp_apply_audio_fades", apply_audio_fades)
        acc_pos = export_data.get("accordion_pos", "top")
        settings.setValue("wp_accordion_pos", acc_pos)

        inc_en = export_data.get("include_english", True)
        inc_es = export_data.get("include_spanish", False)
        pres = export_data.get("spanish_presentation", "accordion")
        primary = export_data.get("primary_language", "en")
        link_parent = export_data.get("link_parent_episode", True)
        parent_pos = export_data.get("parent_episode_pos", "bottom")
        parent_template = export_data.get("parent_episode_template", "")
        update_toc = export_data.get("update_parent_toc", True)

        main_window.export_cancelled = False
        if hasattr(main_window, "cancel_button"):
            main_window.cancel_button.show()

        created_posts = []
        failed_posts = []
        parent_episode_info = export_data.get("parent_episode_info")
        parent_episode_post_id = parent_episode_info.get("id") if isinstance(parent_episode_info, dict) else None
        parent_episode_content = None
        story_posts = []

        # Check if project metadata already contains a previously exported full episode post info
        proj_meta = getattr(main_window, "project_metadata", {}) or {}
        wp_meta = proj_meta.get("wordpress", {}) if isinstance(proj_meta, dict) else {}
        if not parent_episode_info and (wp_meta.get("parent_episode") or wp_meta.get("full_episode_link") or wp_meta.get("link")):
            existing_parent = wp_meta.get("parent_episode")
            if isinstance(existing_parent, dict) and (existing_parent.get("link") or existing_parent.get("url")):
                parent_episode_info = dict(existing_parent)
                parent_episode_post_id = existing_parent.get("id")
            elif wp_meta.get("full_episode_link") or wp_meta.get("link"):
                parent_episode_info = {
                    "id": wp_meta.get("full_episode_post_id") or wp_meta.get("id"),
                    "title": wp_meta.get("full_episode_title") or wp_meta.get("title") or "Full Episode",
                    "link": wp_meta.get("full_episode_link") or wp_meta.get("link"),
                }
                parent_episode_post_id = parent_episode_info.get("id")

        # Function to determine if a post is the parent Full Episode
        def _is_parent(p: Dict[str, Any], p_idx: int) -> bool:
            if p.get("is_parent_episode") is not None:
                return bool(p.get("is_parent_episode"))
            t_lbl = p.get("task_label") or p.get("title") or ""
            return (t_lbl == "Full Episode") or (p_idx == 0 and p.get("start") is None and p.get("end") is None and len(wp_posts) > 1)

        # Sort posts so that any parent full episode is uploaded first, capturing its live URL for story footer correspondence notices
        parent_posts = [p for i, p in enumerate(wp_posts) if _is_parent(p, i)]
        child_posts = [p for i, p in enumerate(wp_posts) if not _is_parent(p, i)]
        ordered_wp_posts = parent_posts + child_posts
        total_posts = len(ordered_wp_posts)

        try:
            for idx, post in enumerate(ordered_wp_posts):
                if getattr(main_window, "export_cancelled", False):
                    if hasattr(main_window, "log_activity"):
                        main_window.log_activity("[WORDPRESS] Export canceled by user.")
                    break

                post_title = post.get("title") or "Untitled Post"
                task_label = post.get("task_label") or post_title
                media_name = safe_filename(post_title) if post_title else "audio"
                is_parent_episode = (post in parent_posts) if parent_posts else _is_parent(post, idx)
                if not is_parent_episode and len(ordered_wp_posts) > 1:
                    media_filename = f"{media_name}_{idx + 1}.mp3"
                else:
                    media_filename = f"{media_name}.mp3"

                pct = int((idx / max(1, total_posts)) * 100)
                if hasattr(main_window, "set_processing_stage"):
                    main_window.set_processing_stage("WordPress Publishing", f"Post {idx + 1} of {total_posts}: '{post_title}'")
                if hasattr(main_window, "update_processing_progress"):
                    main_window.update_processing_progress(pct, f"Starting WordPress export for '{post_title}'…")
                safe_process_events()

                def wp_progress(step, step_total, description, _idx=idx, _title=post_title):
                    fraction = max(0.0, min(1.0, ((step - 1) / step_total)))
                    overall = ((_idx + fraction) / max(1, total_posts)) * 100
                    if hasattr(main_window, "update_processing_progress"):
                        main_window.update_processing_progress(int(overall), description)
                    safe_process_events()

                # Resolve story fades
                st_fade_in = float(post.get("fade_in", 0.0) or 0.0)
                st_fade_out = float(post.get("fade_out", 0.0) or 0.0)
                st_fade_curve = str(post.get("fade_curve", "linear") or "linear")
                if st_fade_in == 0.0 and st_fade_out == 0.0 and hasattr(main_window, "stories") and main_window.stories:
                    st_idx = post.get("story_index")
                    matching_st = None
                    if st_idx is not None and isinstance(st_idx, int) and 0 <= st_idx < len(main_window.stories):
                        matching_st = main_window.stories[st_idx]
                    elif post.get("start") is not None and post.get("end") is not None:
                        p_start = float(post.get("start"))
                        p_end = float(post.get("end"))
                        for candidate in main_window.stories:
                            if abs(float(getattr(candidate, "start", -999)) - p_start) < 0.05 and abs(float(getattr(candidate, "end", -999)) - p_end) < 0.05:
                                matching_st = candidate
                                break
                    if matching_st:
                        st_fade_in = float(getattr(matching_st, "fade_in", 0.0) or 0.0)
                        st_fade_out = float(getattr(matching_st, "fade_out", 0.0) or 0.0)
                        st_fade_curve = str(getattr(matching_st, "fade_curve", "linear") or "linear")

                try:
                    post_data = execute_wordpress_upload(
                        main_window=main_window,
                        client=client,
                        post_title=post_title,
                        post_excerpt=post.get("excerpt", ""),
                        start=post.get("start"),
                        end=post.get("end"),
                        task_label=task_label,
                        include_english=inc_en,
                        include_spanish=inc_es,
                        spanish_presentation=pres,
                        primary_language=primary,
                        author_ids=post.get("author_ids", []),
                        author_term_ids=post.get("author_term_ids", []),
                        category_ids=post.get("category_ids", []),
                        show_completion_dialog=False,
                        media_filename=media_filename,
                        featured_image_path=post.get("featured_image"),
                        progress_callback=wp_progress,
                        parent_episode_info=parent_episode_info if not is_parent_episode else None,
                        link_parent_episode=link_parent if not is_parent_episode else False,
                        parent_episode_template=parent_template,
                        parent_episode_pos=parent_pos,
                        include_audio=inc_audio,
                        fade_in=st_fade_in,
                        fade_out=st_fade_out,
                        fade_curve=st_fade_curve,
                        apply_fades=bool(apply_audio_fades),
                        accordion_pos=acc_pos,
                    )
                    if post_data and isinstance(post_data, dict):
                        if hasattr(main_window, "update_processing_progress"):
                            main_window.update_processing_progress(int(((idx + 1) / max(1, total_posts)) * 100), f"Finished '{post_title}'.")
                        safe_process_events()
                        post_id = post_data.get("id", "Draft")
                        post_link = post_data.get("link") or f"{client.site_url}/?p={post_id}"
                        created_posts.append({
                            "title": post_title,
                            "id": post_id,
                            "link": post_link,
                        })

                        if is_parent_episode and (parent_episode_info is None or not parent_episode_info.get("link")):
                            parent_episode_info = {
                                "id": post_id,
                                "title": post_title,
                                "link": post_link,
                            }
                            parent_episode_post_id = post_id
                            parent_episode_content = post_data.get("_generated_content") or (post_data.get("content", {}).get("raw", "") if isinstance(post_data.get("content"), dict) else "")
                            if hasattr(main_window, "project_metadata") and isinstance(getattr(main_window, "project_metadata", None), dict):
                                main_window.project_metadata.setdefault("wordpress", {})["parent_episode"] = dict(parent_episode_info)
                                main_window.project_metadata["wordpress"]["full_episode_link"] = post_link
                                main_window.project_metadata["wordpress"]["full_episode_post_id"] = post_id
                                main_window.project_metadata["wordpress"]["full_episode_title"] = post_title
                        elif not is_parent_episode:
                            story_posts.append({
                                "id": post_id,
                                "title": post_title,
                                "link": post_link,
                                "start": post.get("start"),
                                "end": post.get("end"),
                            })
                except Exception as exc:
                    if hasattr(main_window, "log_activity"):
                        main_window.log_activity(f"[WORDPRESS ERROR] Failed to export '{post_title}': {exc}")
                    failed_posts.append({
                        "title": post_title,
                        "error": str(exc),
                    })

            # Append Table of Contents to Full Episode post if requested
            if parent_episode_post_id and story_posts and update_toc:
                try:
                    toc_html = build_episode_stories_toc(story_posts)
                    if toc_html and parent_episode_content:
                        updated_content = f"{parent_episode_content}\n\n{toc_html}"
                        client.update_post(parent_episode_post_id, content=updated_content)
                        if hasattr(main_window, "log_activity"):
                            main_window.log_activity(f"[WORDPRESS] Appended story index table of contents to Full Episode Post #{parent_episode_post_id}.")
                except Exception as toc_exc:
                    if hasattr(main_window, "log_activity"):
                        main_window.log_activity(f"[WORDPRESS WARNING] Failed to append story index to Full Episode post #{parent_episode_post_id}: {toc_exc}")

        finally:
            if hasattr(main_window, "set_processing_stage"):
                main_window.set_processing_stage(None)
            if hasattr(main_window, "cancel_button"):
                main_window.cancel_button.hide()

        # Final summaries
        if show_summary_dialog and parent_widget is not None:
            if created_posts and not failed_posts:
                if len(created_posts) == 1:
                    p = created_posts[0]
                    QMessageBox.information(
                        parent_widget,
                        "WordPress Export Complete",
                        f"Draft post created successfully on {client.site_url}!\n\n"
                        f"Post Title: {p['title']}\n"
                        f"Post ID: {p['id']}\n"
                        f"Status: Draft\n"
                        f"Preview Link: {p['link']}",
                    )
                else:
                    posts_summary = "\n".join([f"  #{p['id']}: {p['title']}" for p in created_posts])
                    QMessageBox.information(
                        parent_widget,
                        "WordPress Export Complete",
                        f"All {len(created_posts)} stories have been posted successfully as drafts to {client.site_url}!\n\n"
                        f"Created Posts:\n{posts_summary}",
                    )
            elif created_posts and failed_posts:
                success_summary = "\n".join([f"  #{p['id']}: {p['title']}" for p in created_posts])
                fail_summary = "\n".join([f"  {f['title']}: {f['error']}" for f in failed_posts])
                QMessageBox.warning(
                    parent_widget,
                    "WordPress Export Finished with Errors",
                    f"Completed {len(created_posts)} of {total_posts} draft posts.\n\n"
                    f"Created Posts:\n{success_summary}\n\n"
                    f"Failed Posts:\n{fail_summary}",
                )
            elif failed_posts:
                fail_summary = "\n".join([f"  {f['title']}: {f['error']}" for f in failed_posts])
                has_auth_err = any(is_wp_auth_error(f.get("error", "")) for f in failed_posts)
                if has_auth_err:
                    reply = QMessageBox.question(
                        parent_widget,
                        "WordPress Credentials Required",
                        f"WordPress export failed due to invalid or expired credentials:\n\n{fail_summary}\n\nWould you like to enter or correct your website URL and login details now?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        dlg = WordPressSettingsDialog(parent=parent_widget)
                        if dlg.exec():
                            if self.tab_widget:
                                self.tab_widget._update_wp_conn_status()
                                self.tab_widget._populate_wp_export_metadata(force_refresh=True)
                else:
                    QMessageBox.critical(
                        parent_widget,
                        "WordPress Export Failed",
                        f"None of the {len(failed_posts)} posts could be exported to WordPress.\n\n"
                        f"Errors:\n{fail_summary}",
                    )
        return len(created_posts) > 0


class WordPressPostMetadataDialog(QDialog):
    """Full-featured WordPress post & story metadata editor dialog."""

    def __init__(self, parent: Optional[QWidget], main_window: Any, target_story_index: Optional[int] = None):
        super().__init__(parent)
        self.main_window = main_window
        self.target_story_index = target_story_index
        self.setObjectName("wordpress_post_metadata_dialog")
        self.setWindowTitle("WordPress Post Metadata & Story Settings")
        self.resize(920, 720)
        self.setMinimumSize(720, 540)
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.tab_widget = WordPressExportTabWidget(self, self.main_window, metadata_editor_mode=True)
        layout.addWidget(self.tab_widget, 1)

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.save_close_btn = QPushButton("Save & Close", self)
        self.save_close_btn.setObjectName("wp_save_close_btn")
        self.save_close_btn.setDefault(True)
        self.save_close_btn.clicked.connect(self._on_save_and_close)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setObjectName("wp_close_btn")
        self.close_btn.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(self.close_btn)
        btn_box.addWidget(self.save_close_btn)
        layout.addLayout(btn_box)

        # Select target story if specified
        if self.target_story_index is not None and hasattr(self.tab_widget, "wp_posts_list"):
            # index 0 is Full Episode, index 1..N are stories
            post_idx = self.target_story_index + 1
            if 0 <= post_idx < self.tab_widget.wp_posts_list.count():
                self.tab_widget.wp_posts_list.setCurrentRow(post_idx)

    def _on_save_and_close(self):
        self.tab_widget.save_all_posts_to_project()
        self.accept()



__all__ = [
    "WordPressExportDestination",
    "WordPressExportTabWidget",
    "WordPressPostMetadataDialog",
    "capture_video_frame",
    "build_wp_post_items",
    "build_episode_stories_toc",
    "format_parent_episode_notice",
    "is_wp_auth_error",
]

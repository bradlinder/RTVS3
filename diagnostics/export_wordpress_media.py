"""WordPress featured image metadata and Castos podcast diagnostic tests."""
from __future__ import annotations

import tempfile
from pathlib import Path

from diagnostic_helpers import DiagnosticItem


class DiagnosticExportWordPressMediaMixin:
    def _test_wordpress_featured_image_caption_and_alt_text(self, item: DiagnosticItem):
        """Verify Featured Image caption & alt_text across WordPressClient, post builder, tab UI, and PublishWorker."""
        from PySide6.QtWidgets import QApplication, QMessageBox
        _app = QApplication.instance() or QApplication([])
        import plugins.wordpress.client as wp_client
        from plugins.wordpress.wp_post_builder import build_wp_post_items, sync_featured_image_meta
        from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget
        from plugins.wordpress.plugin import WordPressPublishWorker

        # 1. WordPressClient.update_media_metadata primary, fallback, and no-op behavior
        calls = []

        class FakeResp:
            def __init__(self, status_code, data=None, text=""):
                self.status_code = status_code
                self._data = data or {}
                self.text = text

            def json(self):
                return self._data

        client = wp_client.WordPressClient("https://example.org", "editor", "app-pw")
        client._post_request = lambda url, json_data=None, headers=None, timeout=30: (
            calls.append((url, json_data))
            or FakeResp(200, {"id": 77, "caption": {"raw": json_data.get("caption", "")}, "alt_text": json_data.get("alt_text", "")})
        )
        res_primary = client.update_media_metadata(77, caption="Photo: Jane Doe", alt_text="Mayor speaking at podium")
        assert calls[-1][0] == "https://example.org/wp-json/wp/v2/media/77", f"Unexpected endpoint: {calls[-1][0]}"
        assert calls[-1][1] == {"caption": "Photo: Jane Doe", "alt_text": "Mayor speaking at podium"}
        assert res_primary.get("id") == 77

        # No-op when both caption and alt_text are None
        pre_count = len(calls)
        noop_res = client.update_media_metadata(77)
        assert len(calls) == pre_count and noop_res == {"id": 77}

        # Fallback to ?rest_route=/wp/v2/media/77 when primary fails
        calls.clear()

        def fallback_post(url, json_data=None, headers=None, timeout=30):
            calls.append((url, json_data))
            if "rest_route" in url:
                return FakeResp(200, {"id": 77, "caption": json_data.get("caption")})
            return FakeResp(404, text="Not found")

        client._post_request = fallback_post
        res_fb = client.update_media_metadata(77, caption="Fallback caption")
        assert len(calls) == 2 and "rest_route=/wp/v2/media/77" in calls[1][0]
        assert res_fb.get("id") == 77

        # 2. WordPressClient.upload_media(..., caption=..., alt_text=...) delegates to update_media_metadata
        import base64
        _VALID_1X1_PNG = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(_VALID_1X1_PNG)
            tmp_img = tf.name

        try:
            meta_calls = []
            client._post_multipart = lambda *a, **k: FakeResp(201, {"id": 88, "source_url": "https://example.org/img.png"})
            client.update_media_metadata = lambda mid, caption=None, alt_text=None: (
                meta_calls.append((mid, caption, alt_text)) or {"id": mid, "caption": caption, "alt_text": alt_text}
            )
            up_res = client.upload_media(tmp_img, caption="Studio still", alt_text="Host at mic")
            assert meta_calls == [(88, "Studio still", "Host at mic")], f"Unexpected upload_media delegation: {meta_calls}"
            assert up_res.get("caption") == "Studio still"

            # 3. execute_wordpress_upload metadata behavior & warning resilience
            class DummyMainWin:
                def __init__(self):
                    self.audio_file = None
                    self.duration = 20.0
                    self.stories = []
                    self.logs = []
                    self.transcript_segments = [{"start": 0.0, "end": 5.0, "speaker": "Host", "text": "Hello world"}]

                def get_effective_speaker_name(self, idx, seg):
                    return "Host"

                def _get_transcript_text_slice(self, start, end):
                    return "Hello world"

                def transcript_for_range(self, start, end):
                    return self.transcript_segments

                def clean_export_text(self, text, current_speaker=""):
                    return text

                def log_activity(self, msg, **kwargs):
                    self.logs.append(str(msg))

            class UploadMockClient:
                def __init__(self, fail_meta=False):
                    self.site_url = "https://example.org"
                    self.api_base = f"{self.site_url}/wp-json/wp/v2"
                    self.fail_meta = fail_meta
                    self.meta_updates = []
                    self.created = []

                def upload_media(self, file_path, filename=None):
                    return {"id": 91, "source_url": "https://example.org/thumb.png"}

                def update_media_metadata(self, media_id, caption=None, alt_text=None):
                    if self.fail_meta:
                        raise RuntimeError("Simulated metadata failure")
                    self.meta_updates.append((media_id, caption, alt_text))
                    return {"id": media_id}

                def create_post(self, title, content, excerpt="", status="draft", featured_media_id=None, **kwargs):
                    post = {"id": 301, "title": title, "featured_media": featured_media_id, "status": status}
                    self.created.append(post)
                    return post

            mw_ok = DummyMainWin()
            c_ok = UploadMockClient(fail_meta=False)
            post_ok = wp_client.execute_wordpress_upload(
                mw_ok, c_ok, post_title="Cap Post", include_audio=False,
                featured_image_path=tmp_img,
                featured_image_caption="  Credit: City Hall  ",
                featured_image_alt_text="  City Hall exterior  ",
            )
            assert c_ok.meta_updates == [(91, "Credit: City Hall", "City Hall exterior")], f"Unexpected meta_updates: {c_ok.meta_updates}"
            assert post_ok.get("featured_media") == 91

            c_empty = UploadMockClient(fail_meta=False)
            wp_client.execute_wordpress_upload(
                mw_ok, c_empty, post_title="Empty Meta Post", include_audio=False,
                featured_image_path=tmp_img,
            )
            assert c_empty.meta_updates == [], "update_media_metadata must not run when caption and alt_text are empty"

            mw_warn = DummyMainWin()
            c_fail = UploadMockClient(fail_meta=True)
            post_warn = wp_client.execute_wordpress_upload(
                mw_warn, c_fail, post_title="Warn Resilience Post", include_audio=False,
                featured_image_path=tmp_img, featured_image_caption="Will warn",
            )
            assert post_warn.get("featured_media") == 91, "Post creation must keep featured_media even if metadata update fails"
            assert any("setting caption/alt text failed" in m for m in mw_warn.logs), f"Missing warning log: {mw_warn.logs}"

            # 4. WordPressPublishWorker metadata propagation & modular facade contracts
            import plugins.wordpress.plugin as wp_plugin_mod
            import plugins.wordpress.wordpress_dialog as wp_legacy_dlg_mod
            from plugins.wordpress.wp_workers import WordPressPublishWorker as CanonicalPublishWorker
            from plugins.wordpress.wp_publish_dialog import WordPressPublishDialog as CanonicalPublishDialog
            from plugins.wordpress.wp_post_builder import capture_video_frame as canonical_capture_frame
            from plugins.wordpress.export_destination import WordPressPostMetadataDialog as CanonicalMetaDialog

            assert WordPressPublishWorker is CanonicalPublishWorker, "plugin.WordPressPublishWorker must re-export wp_workers.WordPressPublishWorker"
            assert CanonicalPublishWorker.__module__ == "plugins.wordpress.wp_workers", f"Unexpected worker module: {CanonicalPublishWorker.__module__}"
            assert wp_plugin_mod.WordPressPublishDialog is CanonicalPublishDialog, "plugin.WordPressPublishDialog must re-export wp_publish_dialog.WordPressPublishDialog"
            assert CanonicalPublishDialog.__module__ == "plugins.wordpress.wp_publish_dialog", f"Unexpected dialog module: {CanonicalPublishDialog.__module__}"
            assert wp_plugin_mod.capture_video_frame is canonical_capture_frame, "plugin.capture_video_frame must re-export wp_post_builder.capture_video_frame"
            assert wp_legacy_dlg_mod.capture_video_frame is canonical_capture_frame, "wordpress_dialog.capture_video_frame must re-export wp_post_builder.capture_video_frame"
            assert wp_legacy_dlg_mod.WordPressExportTabWidget is WordPressExportTabWidget, "wordpress_dialog facade must re-export canonical WordPressExportTabWidget"
            assert wp_legacy_dlg_mod.WordPressPostMetadataDialog is CanonicalMetaDialog, "wordpress_dialog facade must re-export canonical WordPressPostMetadataDialog"
            assert wp_legacy_dlg_mod.generate_wp_excerpt([{"start": 1.0, "text": "Hello"}, {"start": 2.0, "text": "world"}], 0.0, 5.0) == "Hello world"
            assert not hasattr(wp_plugin_mod, "WordPressStoryMetadataWidget"), "Dead WordPressStoryMetadataWidget must remain pruned from plugin.py"

            c_worker = UploadMockClient(fail_meta=False)
            worker = WordPressPublishWorker(
                c_worker, "Worker Post", "<p>Body</p>", "Ex", "draft", tmp_img,
                image_caption="Worker Caption", image_alt_text="Worker Alt",
            )
            worker.run()
            assert c_worker.meta_updates == [(91, "Worker Caption", "Worker Alt")], f"Worker failed to update metadata: {c_worker.meta_updates}"

            # 5. post builder + sync_featured_image_meta + WordPressExportTabWidget UI
            class DummyStory:
                def __init__(self, start, end, title):
                    self.start = start
                    self.end = end
                    self.title = title
                    self.fade_in = 0.0
                    self.fade_out = 0.0
                    self.fade_curve = "linear"
                    self.metadata = {}

            class TabDummyMainWin(DummyMainWin):
                def __init__(self):
                    super().__init__()
                    self.audio_file = tmp_img
                    self.current_media_is_video = True
                    self.project_metadata = {}
                    self.stories = [DummyStory(0.0, 10.0, "Story One"), DummyStory(10.0, 20.0, "Story Two")]
                    self.current_selected_story_indices = [1]
                    self.refresh_calls = 0
                    self.dirty_reasons = []

                def refresh_story_list(self):
                    self.refresh_calls += 1

                def mark_project_dirty(self, reason=None):
                    self.dirty_reasons.append(reason)

            tab_mw = TabDummyMainWin()
            tab = WordPressExportTabWidget(None, tab_mw)
            tab.rebuild_post_items("full_and_all_stories")
            assert len(tab.wp_post_items) == 3, f"Expected 3 post items, got {len(tab.wp_post_items)}"
            tab._load_post_editor_state(0)
            assert tab.wp_img_meta_widget.isHidden(), "Metadata inputs must be hidden in None mode"

            tab.wp_rad_thumb_file.setChecked(True)
            assert not tab.wp_img_meta_widget.isHidden(), "Metadata inputs must show in custom file mode"
            tab.wp_thumb_caption_edit.setText("Episode Caption")
            tab.wp_thumb_alt_edit.setText("Episode Alt")
            assert tab.wp_post_items[0]["featured_image_caption"] == "Episode Caption"
            assert tab.wp_post_items[0]["featured_image_alt_text"] == "Episode Alt"
            assert tab_mw.project_metadata["wordpress"]["featured_image_caption"] == "Episode Caption"
            assert tab_mw.project_metadata["wordpress"]["featured_image_alt_text"] == "Episode Alt"

            # Verify video frame grab mode also reveals metadata inputs
            tab._load_post_editor_state(1)
            assert tab.wp_img_meta_widget.isHidden(), "Story 1 starts in None mode with hidden metadata widget"
            tab.wp_rad_thumb_grab.setChecked(True)
            assert not tab.wp_img_meta_widget.isHidden(), "Metadata inputs must show in grab mode"
            tab.wp_thumb_caption_edit.setText("Story 1 Caption")
            tab.wp_thumb_alt_edit.setText("Story 1 Alt")
            assert tab_mw.refresh_calls == 0, f"Typing caption/alt must not trigger refresh_story_list, got {tab_mw.refresh_calls}"
            assert "Update WordPress Metadata" not in tab_mw.dirty_reasons, f"Typing must not emit log_reason dirty notifications: {tab_mw.dirty_reasons}"

            # Verify post switching & rebuild persistence
            rebuilt = build_wp_post_items(tab_mw, scope="full_and_all_stories")
            assert rebuilt[0]["featured_image_caption"] == "Episode Caption"
            assert rebuilt[1]["featured_image_caption"] == "Story 1 Caption"
            assert rebuilt[1]["featured_image_alt_text"] == "Story 1 Alt"

            # Bulk apply to selected & all stories (stub modal QMessageBox.information)
            orig_info = QMessageBox.information
            QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Ok
            try:
                tab._apply_thumbnails_to_selected_stories()
                assert tab_mw.stories[1].metadata["wordpress"]["featured_image_caption"] == "Story 1 Caption"
                assert tab_mw.stories[1].metadata["wordpress"]["featured_image_alt_text"] == "Story 1 Alt"
                tab._apply_thumbnails_to_all_posts()
                assert tab.wp_post_items[2]["featured_image_caption"] == "Story 1 Caption"
            finally:
                QMessageBox.information = orig_info

            # 6. Click-to-enlarge Featured Image preview + Custom Selection sidebar parity & live export count (v3.10.27-beta)
            from plugins.wordpress.wp_thumb_ui import (
                ClickableThumbnailLabel,
                FeaturedImageLightboxDialog,
                open_featured_image_preview,
                set_preview_pixmap,
                clear_preview_pixmap,
            )
            from export.story_selector import ExportStorySelectorSidebar, FULL_EPISODE_ROLE_VALUE
            from export.dialog import UnifiedExportDialog
            from PySide6.QtCore import Qt

            assert isinstance(tab.wp_thumb_preview_label, ClickableThumbnailLabel)
            set_preview_pixmap(tab, tmp_img, source_description="Test Featured Image")
            assert not tab.wp_thumb_preview_label.pixmap().isNull()
            assert tab.wp_thumb_preview_label.full_image_path() == tmp_img
            assert "full-size" in tab.wp_thumb_preview_label.toolTip().lower()
            lb_dlg = open_featured_image_preview(tab)
            assert isinstance(lb_dlg, FeaturedImageLightboxDialog)
            assert "Test Featured Image" in lb_dlg.header_label.text()
            assert "1 x 1 px" in lb_dlg.header_label.text()
            lb_dlg.close()
            lb_dlg.deleteLater()
            clear_preview_pixmap(tab, "No Thumbnail")
            assert tab.wp_thumb_preview_label.full_image_path() is None
            assert tab.wp_thumb_preview_label.toolTip() == ""

            # Verify WordPress sidebar decorations, unchecked dimming, inline Auto-fill All Excerpts, and live count
            decs = tab.get_sidebar_decorations()
            assert FULL_EPISODE_ROLE_VALUE in decs and 0 in decs and 1 in decs, f"Missing sidebar decorations: {decs.keys()}"
            sidebar = ExportStorySelectorSidebar(tab_mw)
            sidebar.populate(tab_mw.stories, selected_indices=[0], include_full_episode=False)
            sidebar.set_item_decorations(decs)
            full_row = sidebar.story_list.item(0)
            st0_row = sidebar.story_list.item(1)
            st1_row = sidebar.story_list.item(2)
            assert full_row.data(Qt.ItemDataRole.ForegroundRole) is not None, "Unchecked Full Episode row must be muted"
            assert st0_row.data(Qt.ItemDataRole.ForegroundRole) is None, "Checked story row must use normal foreground"
            assert st1_row.data(Qt.ItemDataRole.ForegroundRole) is not None, "Unchecked story row must be muted"
            assert "[" in st0_row.text() and "Img" in st0_row.text(), f"Checked row should mirror WP badge: {st0_row.text()}"
            assert "[" not in st1_row.text(), f"Unchecked row should not show active WP badge: {st1_row.text()}"
            sidebar.close()
            sidebar.deleteLater()

            exp_dlg = UnifiedExportDialog(tab_mw, initial_scope="selected_stories", initial_dest="local")
            try:
                assert exp_dlg.is_story_selector_visible()
                assert "(1)" in exp_dlg.export_btn.text(), f"Expected live count (1), got: {exp_dlg.export_btn.text()}"
                exp_dlg.story_selector_sidebar.set_include_full_episode(True, emit=True)
                assert "(2)" in exp_dlg.export_btn.text(), f"Expected live count (2), got: {exp_dlg.export_btn.text()}"

                # 7. WordPress "Not Included in Export" placeholder on unchecked Custom Selection items (v3.10.28-beta)
                from plugins.wordpress.wp_ui_builder import include_excluded_item_in_export
                wp_tab_in_dlg = WordPressExportTabWidget(exp_dlg, tab_mw)
                exp_dlg._plugin_destinations.append(("wordpress", type("FakeDest", (), {
                    "id": "wordpress",
                    "tab_widget": wp_tab_in_dlg,
                    "on_scope_changed": lambda s, sc, sts: wp_tab_in_dlg.rebuild_post_items(scope=sc),
                })(), wp_tab_in_dlg))
                exp_dlg.story_selector_sidebar.set_include_full_episode(False, emit=True)
                exp_dlg.story_selector_sidebar.set_selected_indices([1], emit=True)
                # Click unchecked Story 1 (index 0) -> must hide metadata and show Not Included placeholder
                assert wp_tab_in_dlg.select_story_index(0) is False
                assert wp_tab_in_dlg.wp_post_editor_stack.currentWidget() is wp_tab_in_dlg.wp_excluded_placeholder
                assert "not included" in wp_tab_in_dlg.wp_excluded_title_label.text().lower()
                assert wp_tab_in_dlg.wp_include_in_export_btn.isVisible() or not wp_tab_in_dlg.wp_include_in_export_btn.isHidden()
                # Click unchecked Full Episode -> placeholder switches to Full Episode
                assert wp_tab_in_dlg.select_full_episode() is False
                assert wp_tab_in_dlg.wp_post_editor_stack.currentWidget() is wp_tab_in_dlg.wp_excluded_placeholder
                assert "full episode" in wp_tab_in_dlg.wp_excluded_title_label.text().lower()
                # One-click Include in Export checks Full Episode and restores full metadata editor
                assert include_excluded_item_in_export(wp_tab_in_dlg) is True
                assert exp_dlg.story_selector_sidebar.is_full_episode_included() is True
                assert wp_tab_in_dlg.wp_post_editor_stack.currentWidget() is wp_tab_in_dlg.wp_editor_body_page
                # Clearing all items shows Not Included placeholder rather than stale story metadata
                exp_dlg.story_selector_sidebar.clear_selection()
                assert wp_tab_in_dlg.wp_post_editor_stack.currentWidget() is wp_tab_in_dlg.wp_excluded_placeholder
                wp_tab_in_dlg.close()
                wp_tab_in_dlg.deleteLater()
            finally:
                exp_dlg.close()
                exp_dlg.deleteLater()

            tab.close()
        finally:
            try:
                Path(tmp_img).unlink(missing_ok=True)
            except Exception:
                pass

    def _test_wordpress_castos_podcast_integration(self, item: DiagnosticItem):
        import plugins.wordpress.client as wp_client
        from plugins.wordpress.castos import (
            format_castos_duration,
            build_castos_post_meta,
            fetch_castos_feeds,
            SS_PODCAST_AUDIO_FILE,
            SS_PODCAST_AUDIO_FILE_ID,
            SS_PODCAST_DURATION,
            SS_PODCAST_FILESIZE,
            SS_PODCAST_FEED,
            SS_PODCAST_EPISODE_TYPE,
            CASTOS_META_AUDIO_FILE,
            CASTOS_META_DURATION,
            CASTOS_META_FILESIZE,
            CASTOS_META_EPISODE_TYPE,
        )

        # 1. Test Duration Formatting
        if format_castos_duration(0) != "00:00:00":
            raise AssertionError(f"Expected '00:00:00', got {format_castos_duration(0)}")
        if format_castos_duration(930) != "00:15:30":
            raise AssertionError(f"Expected '00:15:30', got {format_castos_duration(930)}")
        if format_castos_duration(3661) != "01:01:01":
            raise AssertionError(f"Expected '01:01:01', got {format_castos_duration(3661)}")

        # 2. Test Castos Post Meta Construction
        meta = build_castos_post_meta(
            audio_url="https://example.com/podcast.mp3",
            attachment_id=888,
            duration_seconds=930.0,
            filesize_bytes=1234567,
            feed_slug="daily-news",
            episode_type="full",
            season=1,
            episode_number=5,
        )
        if meta.get(SS_PODCAST_AUDIO_FILE) != "https://example.com/podcast.mp3":
            raise AssertionError(f"Incorrect ss_podcast_audio_file meta: {meta}")
        if meta.get(SS_PODCAST_AUDIO_FILE_ID) != 888:
            raise AssertionError(f"Incorrect ss_podcast_audio_file_id meta: {meta}")
        if meta.get(SS_PODCAST_DURATION) != "00:15:30":
            raise AssertionError(f"Incorrect ss_podcast_duration meta: {meta}")
        if meta.get(SS_PODCAST_FILESIZE) not in (1234567, "1234567"):
            raise AssertionError(f"Incorrect ss_podcast_filesize meta: {meta}")
        if meta.get(SS_PODCAST_FEED) != "daily-news":
            raise AssertionError(f"Incorrect ss_podcast_feed meta: {meta}")
        if meta.get(SS_PODCAST_EPISODE_TYPE) != "full":
            raise AssertionError(f"Incorrect ss_podcast_episode_type meta: {meta}")
        if meta.get(CASTOS_META_AUDIO_FILE) != "https://example.com/podcast.mp3":
            raise AssertionError(f"Incorrect native Castos audio_file meta: {meta}")
        if meta.get(CASTOS_META_DURATION) != "00:15:30":
            raise AssertionError(f"Incorrect native Castos duration meta: {meta}")
        if meta.get(CASTOS_META_FILESIZE) not in (1234567, "1234567"):
            raise AssertionError(f"Incorrect native Castos filesize meta: {meta}")
        if meta.get(CASTOS_META_EPISODE_TYPE) != "full":
            raise AssertionError(f"Incorrect native Castos episode_type meta: {meta}")
        for k in meta:
            if k.startswith("_"):
                raise AssertionError(f"Protected leading-underscore meta key found: {k}")

        # 3. Test Castos Feed Discovery & Author Exclusion
        class MockFeedDiscoveryClient:
            def __init__(self):
                self.site_url = "https://example.com"
                self.api_base = "https://example.com/wp-json/wp/v2"

            def is_configured(self):
                return True

            def _get_request(self, url, params=None, headers=None, timeout=30):
                if "/series" in url:
                    return type("Resp", (), {
                        "status_code": 200,
                        "json": lambda *args, **kwargs: [
                            {"id": 12, "name": "Block by Block (default)", "slug": "block-by-block"},
                            {"id": 15, "name": "Around the Block", "slug": "around-the-block"},
                        ],
                    })()
                if "/taxonomies" in url:
                    return type("Resp", (), {
                        "status_code": 200,
                        "json": lambda *args, **kwargs: {
                            "series": {"name": "Podcast Series", "slug": "series", "rest_base": "series"},
                            "author": {"name": "Authors", "slug": "author", "rest_base": "author", "types": ["post", "podcast"]},
                        },
                    })()
                if "/author" in url:
                    return type("Resp", (), {
                        "status_code": 200,
                        "json": lambda *args, **kwargs: [{"id": 1, "name": "brad linder", "slug": "brad-linder"}],
                    })()
                return type("Resp", (), {"status_code": 404, "json": lambda *args, **kwargs: []})()

        disc_client = MockFeedDiscoveryClient()
        disc_feeds = fetch_castos_feeds(disc_client)
        if len(disc_feeds) != 2:
            raise AssertionError(f"Expected exactly 2 discovered podcast feeds, got {disc_feeds}")
        if disc_feeds[0]["name"] != "Block by Block (default)" or disc_feeds[0]["id"] != 12:
            raise AssertionError(f"Expected 'Block by Block (default)' first with id 12, got {disc_feeds[0]}")
        if disc_feeds[1]["name"] != "Around the Block" or disc_feeds[1]["id"] != 15:
            raise AssertionError(f"Expected 'Around the Block' second with id 15, got {disc_feeds[1]}")
        if any("brad" in f["name"].lower() or "author" in f.get("slug", "").lower() for f in disc_feeds):
            raise AssertionError(f"Author unexpectedly included in podcast feeds: {disc_feeds}")

        # 4. Test Podcast Upload Execution (is_podcast=True vs False)
        class MockCastosClient:
            def __init__(self):
                self.site_url = "https://example.com"
                self.api_base = "https://example.com/wp-json/wp/v2"
                self.uploaded_files = []
                self.created_posts = []

            def is_configured(self):
                return True

            def _post_request(self, url, json_data=None, headers=None, timeout=30):
                return type("Resp", (), {"status_code": 404, "json": lambda *args, **kwargs: []})()

            def upload_media(self, file_path, filename=None):
                fname = filename or Path(file_path).name
                self.uploaded_files.append(fname)
                return {
                    "id": 888,
                    "source_url": f"https://example.com/wp-content/uploads/{fname}",
                    "media_details": {"filesize": 50000},
                }

            def create_post(self, title, content, excerpt="", status="draft", **kwargs):
                post_id = 900 + len(self.created_posts)
                post = {
                    "id": post_id,
                    "title": {"rendered": title},
                    "content": {"rendered": content},
                    "excerpt": {"rendered": excerpt},
                    "link": f"https://example.com/?p={post_id}",
                    "kwargs": kwargs,
                }
                self.created_posts.append(post)
                return post

        class DummyPodcastWin:
            def __init__(self, audio_path):
                self.audio_file = audio_path
                self.duration = 300.0
                self.transcript = {"segments": [{"start": 0.0, "end": 5.0, "text": "Podcast intro."}]}
                self.logged = []

            def transcript_for_range(self, start, end):
                return self.transcript["segments"]

            def clean_export_text(self, text, current_speaker=""):
                return text

            def log_activity(self, msg, level="info"):
                self.logged.append(msg)

        # Create audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_aud:
            f_aud.write(b"ID3mockaudiodata" + b"\x00" * 100)
            aud_path = f_aud.name

        try:
            orig_sub_run = wp_client.subprocess.run
            wp_client.subprocess.run = lambda *a, **k: type("Res", (), {"returncode": 0, "stderr": ""})()

            client_pod = MockCastosClient()
            win_pod = DummyPodcastWin(aud_path)

            # 3a. Podcast Episode Export (is_podcast=True)
            post_pod = wp_client.execute_wordpress_upload(
                main_window=win_pod,
                client=client_pod,
                post_title="Daily News Episode 1",
                post_excerpt="Today's headlines.",
                include_audio=True,
                is_podcast=True,
                podcast_feed="daily-news",
                podcast_episode_type="full",
                podcast_season=1,
                podcast_episode_number=1,
            )

            if not post_pod or post_pod.get("id") != 900:
                raise AssertionError(f"Expected podcast post id 900, got {post_pod}")

            pod_content = client_pod.created_posts[0]["content"]["rendered"]
            if "<!-- wp:audio -->" in pod_content or "<audio" in pod_content:
                raise AssertionError(f"Standard wp:audio block unexpectedly present in podcast post:\n{pod_content}")
            if "[ss_player]" in pod_content:
                raise AssertionError(f"Legacy compact [ss_player] shortcode unexpectedly present in podcast post:\n{pod_content}")

            sent_kwargs = client_pod.created_posts[0]["kwargs"]
            sent_meta = sent_kwargs.get("meta")
            if not sent_meta or sent_meta.get(SS_PODCAST_FEED) != "daily-news":
                raise AssertionError(f"Podcast meta missing or incorrect in create_post kwargs: {sent_kwargs}")
            if sent_meta.get(SS_PODCAST_AUDIO_FILE_ID) != 888:
                raise AssertionError(f"Podcast attachment ID missing from meta: {sent_meta}")

            # 3b. Standard Non-Podcast Export (is_podcast=False)
            client_std = MockCastosClient()
            post_std = wp_client.execute_wordpress_upload(
                main_window=win_pod,
                client=client_std,
                post_title="Standard Blog Post",
                post_excerpt="Standard blog excerpt.",
                include_audio=True,
                is_podcast=False,
            )

            std_content = client_std.created_posts[0]["content"]["rendered"]
            if "<!-- wp:audio -->" not in std_content:
                raise AssertionError("Standard wp:audio block missing from non-podcast export")
            if "[ss_player]" in std_content:
                raise AssertionError("Castos [ss_player] shortcode unexpectedly present in standard export")

            std_kwargs = client_std.created_posts[0]["kwargs"]
            if std_kwargs.get("meta"):
                raise AssertionError(f"Castos podcast meta unexpectedly present in standard export: {std_kwargs}")

            # 4. Test WordPress Episode Backfill / Update Mode, Option B Excerpt, & Publication Date
            import plugins.wordpress.episode_updater as wp_ep_facade
            import plugins.wordpress.episode_lookup as wp_ep_lookup
            import plugins.wordpress.episode_updater_ui as wp_ep_ui
            from plugins.wordpress.episode_updater import (
                extract_slug_or_id_from_url,
                clean_html_to_plain_excerpt,
                build_story_slug,
                normalize_wp_iso_date,
                resolve_wp_post_from_url,
            )

            assert wp_ep_facade.resolve_wp_post_from_url is wp_ep_lookup.resolve_wp_post_from_url
            assert wp_ep_lookup.resolve_wp_post_from_url.__module__ == "plugins.wordpress.episode_lookup"
            assert wp_ep_facade.normalize_wp_iso_date is wp_ep_lookup.normalize_wp_iso_date
            assert wp_ep_facade.LoadWordPressEpisodeDialog is wp_ep_ui.LoadWordPressEpisodeDialog
            assert wp_ep_ui.LoadWordPressEpisodeDialog.__module__ == "plugins.wordpress.episode_updater_ui"
            assert wp_ep_facade.setup_wp_mode_and_date_ui is wp_ep_ui.setup_wp_mode_and_date_ui
            assert wp_ep_facade.prompt_load_existing_wp_episode_dialog is wp_ep_ui.prompt_load_existing_wp_episode_dialog
            ep_lookup_file = Path("plugins/wordpress/episode_lookup.py")
            if ep_lookup_file.is_file():
                assert "PySide6" not in ep_lookup_file.read_text(encoding="utf-8"), (
                    "Headless plugins/wordpress/episode_lookup.py must not import PySide6"
                )

            # Verify hybrid PublicationDateLineEdit calendar/time dropdown + direct typing
            from PySide6.QtCore import QDate, QTime, Qt
            from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

            _qt_app = QApplication.instance() or QApplication([])
            if getattr(type(QWidget()), "__module__", "").startswith("PySide6."):
                class _PickerHost(QWidget):
                    def __init__(self):
                        super().__init__()
                        self.main_window = type("MW", (), {"project_metadata": {}})()
                        self.wp_post_items = []
                        self._current_post_index = 0
                        self._syncing_post_editor = False
                        self._lay = QVBoxLayout(self)

                    def add_widget(self, w):
                        self._lay.addWidget(w)

                host = _PickerHost()
                wp_ep_ui.setup_wp_mode_and_date_ui(host, host)
                try:
                    assert isinstance(host.wp_pub_date_edit, wp_ep_ui.PublicationDateLineEdit)
                    assert host.wp_pub_date_edit.text() == "", "Publication Date must default to blank"

                    popup = host.wp_pub_date_edit.open_picker()
                    assert popup is not None and popup.isVisible(), "Opening calendar popup failed"
                    assert host.wp_pub_date_edit.text() == "", "Opening popup must keep blank value until user selects a date"
                    mon_fg_style = popup.calendar.weekdayTextFormat(Qt.DayOfWeek.Monday).foreground().style()
                    assert popup.calendar.weekdayTextFormat(Qt.DayOfWeek.Saturday).foreground().style() == mon_fg_style
                    assert popup.calendar.weekdayTextFormat(Qt.DayOfWeek.Sunday).foreground().style() == mon_fg_style

                    popup.time_edit.setTime(QTime(14, 30))
                    popup.calendar.clicked.emit(QDate(2026, 4, 29))
                    assert host.wp_pub_date_edit.text() == "2026-04-29 14:30", f"Unexpected picked date: {host.wp_pub_date_edit.text()!r}"
                    assert host.main_window.project_metadata["wordpress"]["publication_date"] == "2026-04-29 14:30"

                    host.wp_pub_date_edit.setText("2026-05-10 08:15")
                    host.wp_pub_date_edit.textEdited.emit("2026-05-10 08:15")
                    assert popup.calendar.selectedDate() == QDate(2026, 5, 10)
                    assert popup.time_edit.time().hour() == 8 and popup.time_edit.time().minute() == 15
                    assert host.main_window.project_metadata["wordpress"]["publication_date"] == "2026-05-10 08:15"

                    popup.clear_btn.click()
                    assert host.wp_pub_date_edit.text() == ""
                    assert host.main_window.project_metadata["wordpress"]["publication_date"] == ""
                    assert not popup.isVisible()
                finally:
                    host.wp_pub_date_edit.close_picker()
                    host.close()
                    host.deleteLater()

            if extract_slug_or_id_from_url("https://rss.phillycam.org/april-29-2026/") != (None, "april-29-2026"):
                raise AssertionError("Failed to extract slug from WordPress episode URL")
            if extract_slug_or_id_from_url("https://rss.phillycam.org/?p=456") != (456, ""):
                raise AssertionError("Failed to extract numeric post ID from query URL")
            if normalize_wp_iso_date("2026-04-29") != "2026-04-29T09:00:00":
                raise AssertionError("Date-only normalization failed")
            if normalize_wp_iso_date("2026-04-29 14:30") != "2026-04-29T14:30:00":
                raise AssertionError("Date+time normalization failed")
            if normalize_wp_iso_date("") is not None:
                raise AssertionError("Blank date should normalize to None")
            if build_story_slug("City Council Budget Hearing!") != "city-council-budget-hearing":
                raise AssertionError("Story slug generation mismatch")
            if clean_html_to_plain_excerpt("<p>Hello &amp; welcome</p><audio src='x.mp3'></audio>") != "Hello & welcome":
                raise AssertionError("HTML cleanup for Option B excerpt mismatch")

            class MockBackfillClient(MockCastosClient):
                def __init__(self):
                    super().__init__()
                    self.updated_calls = []

                def _get_request(self, url, params=None, headers=None, timeout=30):
                    if params and params.get("slug") == "april-29-2026":
                        return type("Resp", (), {
                            "status_code": 200,
                            "json": lambda *a, **k: [{
                                "id": 555,
                                "link": "https://rss.phillycam.org/april-29-2026/",
                                "slug": "april-29-2026",
                                "status": "publish",
                                "date": "2026-04-29T14:00:00",
                                "title": {"raw": "April 29, 2026 Broadcast", "rendered": "April 29, 2026 Broadcast"},
                                "excerpt": {"raw": "", "rendered": ""},
                                "content": {
                                    "raw": "<p>Original episode show notes for podcast feed.</p><audio src='https://rss.phillycam.org/wp-content/uploads/ep.mp3'></audio>",
                                    "rendered": "<p>Original episode show notes for podcast feed.</p><audio src='https://rss.phillycam.org/wp-content/uploads/ep.mp3'></audio>",
                                },
                                "categories": [12],
                                "author": 3,
                            }],
                        })()
                    return type("Resp", (), {"status_code": 404, "text": "Not Found", "json": lambda *a, **k: []})()

                def update_post(self, post_id, **kwargs):
                    self.updated_calls.append((post_id, kwargs))
                    return {"id": post_id, "link": "https://rss.phillycam.org/april-29-2026/", "slug": "april-29-2026", "status": kwargs.get("status", "publish")}

            client_upd = MockBackfillClient()
            resolved = resolve_wp_post_from_url(client_upd, "https://rss.phillycam.org/april-29-2026/")
            if resolved["id"] != 555 or resolved["status"] != "publish" or resolved["date_display"] != "2026-04-29 14:00":
                raise AssertionError(f"Unexpected resolved post metadata: {resolved}")
            if resolved["audio_url"] != "https://rss.phillycam.org/wp-content/uploads/ep.mp3":
                raise AssertionError(f"Unexpected resolved audio URL: {resolved}")
            if resolved["excerpt"] != "Original episode show notes for podcast feed.":
                raise AssertionError(f"Option B excerpt extraction mismatch: {resolved['excerpt']}")

            # 4a. Update existing Full Episode preserving MP3, Castos metadata, and published status
            upd_post = wp_client.execute_wordpress_upload(
                main_window=win_pod,
                client=client_upd,
                post_title=resolved["title"],
                post_excerpt=resolved["excerpt"],
                include_audio=True,
                is_podcast=True,
                existing_post_id=555,
                replace_existing_audio_and_podcast=False,
                post_status="publish",
                publication_date="2026-04-29 14:00",
            )
            if not upd_post or upd_post.get("id") != 555:
                raise AssertionError(f"Expected updated post 555, got {upd_post}")
            if client_upd.created_posts:
                raise AssertionError("Update Existing Episode mode must not call create_post")
            if client_upd.uploaded_files:
                raise AssertionError(f"Expected zero media uploads when preserving existing MP3, got {client_upd.uploaded_files}")
            if not client_upd.updated_calls:
                raise AssertionError("Expected client.update_post to be called")
            _, upd_kw = client_upd.updated_calls[0]
            if "meta" in upd_kw or "podcast_series" in upd_kw:
                raise AssertionError(f"Castos meta/series must not be overwritten when preserving existing podcast audio: {upd_kw}")
            if upd_kw.get("status") != "publish" or upd_kw.get("date") != "2026-04-29T14:00:00":
                raise AssertionError(f"Unexpected status/date on existing post update: {upd_kw}")
            if "<!-- wp:audio -->" in upd_kw.get("content", ""):
                raise AssertionError("Duplicate wp:audio block should not be injected when preserving existing episode player")

            # 4b. Create backdated Story draft with clean slug and uploaded story audio clip
            def fake_sub_write(cmd, *a, **k):
                Path(cmd[-1]).write_bytes(b"ID3FakeMP3Data")
                return type("Res", (), {"returncode": 0, "stderr": ""})()

            wp_client.subprocess.run = fake_sub_write
            client_story = MockBackfillClient()
            story_res = wp_client.execute_wordpress_upload(
                main_window=win_pod,
                client=client_story,
                post_title="Story 1 Backdated",
                post_excerpt="Story excerpt.",
                start=0.0,
                end=5.0,
                include_audio=True,
                is_podcast=False,
                post_status="draft",
                publication_date="2026-04-29 14:00",
                post_slug="story-1-slug",
            )
            if not story_res or len(client_story.uploaded_files) != 1:
                raise AssertionError(f"Expected 1 story audio upload, got {client_story.uploaded_files}")
            st_kw = client_story.created_posts[0]["kwargs"]
            if st_kw.get("date") != "2026-04-29T14:00:00" or st_kw.get("slug") != "story-1-slug":
                raise AssertionError(f"Unexpected story date/slug kwargs: {st_kw}")
            if "<!-- wp:audio -->" not in client_story.created_posts[0]["content"]["rendered"]:
                raise AssertionError("Story post missing wp:audio block")

        finally:
            wp_client.subprocess.run = orig_sub_run
            try:
                Path(aud_path).unlink(missing_ok=True)
            except Exception:
                pass

        item.status = "PASS"
        item.message = "WordPress Seriously Simple Podcasting (Castos) integration verified"

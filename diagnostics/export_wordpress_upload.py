"""WordPress multi-story upload, Gutenberg hygiene, and audio toggle diagnostic tests."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT, generate_synthetic_wav


class DiagnosticExportWordPressUploadMixin:
    def _test_wordpress_multi_story_upload_and_ui_pluralization(self, item: DiagnosticItem):
        try:
            import PySide6
        except ImportError:
            item.status = "WARNING"
            item.message = "PySide6 Qt GUI framework not present in current environment"
            return

        import sys
        root_dir = PROJECT_ROOT
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        plugins_dir = root_dir / "plugins"
        if str(plugins_dir) not in sys.path:
            sys.path.insert(0, str(plugins_dir))

        try:
            import plugins.wordpress.export_destination as wp_dest_mod
            import plugins.wordpress.client as wp_client_mod
        except ImportError:
            import importlib.util
            wp_path = plugins_dir / "wordpress" / "export_destination.py"
            spec = importlib.util.spec_from_file_location("wp_export_dest", str(wp_path))
            if not spec or not spec.loader:
                raise ImportError(f"Could not locate {wp_path}")
            wp_dest_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wp_dest_mod)

            client_path = plugins_dir / "wordpress" / "client.py"
            spec_c = importlib.util.spec_from_file_location("wp_client", str(client_path))
            if not spec_c or not spec_c.loader:
                raise ImportError(f"Could not locate {client_path}")
            wp_client_mod = importlib.util.module_from_spec(spec_c)
            spec_c.loader.exec_module(wp_client_mod)

        # 1. Test button label pluralization
        wp_dest = wp_dest_mod.WordPressExportDestination()

        class DummyWpWidget:
            def __init__(self, items):
                self.wp_post_items = items
                self.wp_posts_list = type("MockList", (), {"selectedIndexes": lambda self: []})()

        wp_dest.widget = DummyWpWidget([{"title": "Single Story"}])
        label_single = wp_dest.get_export_button_label()
        if label_single != "Export to WordPress Draft":
            raise AssertionError(f"Expected singular label 'Export to WordPress Draft', got '{label_single}'")

        wp_dest.widget = DummyWpWidget([{"title": "Story 1"}, {"title": "Story 2"}])
        label_multi = wp_dest.get_export_button_label()
        if label_multi != "Export to WordPress Drafts...":
            raise AssertionError(f"Expected plural label 'Export to WordPress Drafts...', got '{label_multi}'")

        # 2. Test multi-story execution loop
        uploaded_posts = []
        updated_posts = []

        class DummyMockClient:
            site_url = "https://example.com"
            api_base = "https://example.com/wp-json/wp/v2"
            def upload_media(self, file_path, filename=None):
                return {"id": 100, "source_url": "https://example.com/audio.mp3"}
            def create_post(self, title, content, excerpt="", status="draft", **kwargs):
                post_id = len(uploaded_posts) + 1
                post_data = {"id": post_id, "link": f"https://example.com/post/{post_id}"}
                uploaded_posts.append((title, content))
                return post_data
            def update_post(self, post_id, content=None, **kwargs):
                updated_posts.append((post_id, content))
                return {"id": post_id, "content": content}

        class DummyStory:
            def __init__(self, start, end, title):
                self.start = start
                self.end = end
                self.title = title

        class DummyMW:
            def __init__(self, audio_path=""):
                self.audio_file = audio_path
                self.duration = 100.0
                self.stories = [DummyStory(0.0, 50.0, "Story A"), DummyStory(50.0, 100.0, "Story B")]
                self.current_selected_story_indices = [0, 1]
                self.transcript = {"segments": [{"start": 0.0, "end": 100.0, "text": "Sample"}]}
                self.project_metadata = {}
            def transcript_for_range(self, start, end):
                return [{"start": start or 0.0, "end": end or 50.0, "text": "Story text", "speaker": "Host"}]
            def log_activity(self, msg, level=""):
                pass

        orig_wp_client_cls = getattr(wp_dest_mod, "WordPressClient", None)
        orig_sub_run = wp_client_mod.subprocess.run
        captured_cmds = []

        try:
            wp_dest_mod.WordPressClient = lambda *a, **k: DummyMockClient()
            def fake_sub_run(cmd, *a, **k):
                captured_cmds.append(list(cmd))
                out_file = cmd[-1]
                Path(out_file).write_bytes(b"ID3FakeMP3Data")
                return type("Res", (), {"returncode": 0, "stderr": ""})()
            wp_client_mod.subprocess.run = fake_sub_run

            from PySide6.QtCore import QSettings
            import prs_shared
            settings = QSettings(prs_shared.INTERNAL_APP_ID, prs_shared.INTERNAL_APP_ID)
            old_wp_url = settings.value("wp_site_url")
            old_wp_user = settings.value("wp_username")
            settings.setValue("wp_site_url", "https://example.com")
            settings.setValue("wp_username", "admin")
            wp_client_mod._set_wp_password("admin", "pass")

            dest_obj = wp_dest_mod.WordPressExportDestination()
            post_items = [
                {"task_label": "Story 1", "title": "Story A", "start": 0.0, "end": 50.0, "excerpt": "", "is_parent_episode": False, "fade_in": 1.5, "fade_out": 2.0, "fade_curve": "linear"},
                {"task_label": "Story 2", "title": "Story B", "start": 50.0, "end": 100.0, "excerpt": "", "is_parent_episode": False, "fade_in": 0.5, "fade_out": 1.0, "fade_curve": "linear"},
            ]
            dest_obj.widget = DummyWpWidget(post_items)
            dest_obj.widget.client = DummyMockClient()

            # Test A: Text-only export (include_audio=False) — works without local audio file
            dest_obj.widget.main_window = DummyMW("")
            export_data_text = {
                "wp_posts": post_items,
                "include_english": True,
                "include_spanish": False,
                "include_audio": False,
                "show_completion_dialog": False,
            }
            res_text = dest_obj.execute_export(dest_obj.widget.main_window, export_data_text)
            if not res_text or len(uploaded_posts) != 2:
                raise AssertionError(f"Multi-story text-only export failed: expected 2 uploaded posts, got {len(uploaded_posts)}")
            for p_title, p_content in uploaded_posts:
                if "<!-- wp:audio -->" in p_content:
                    raise AssertionError(f"Text-only export post '{p_title}' should not contain audio block")

            # Test B: Audio-included export (include_audio=True) — embeds audio player block and applies fades
            uploaded_posts.clear()
            captured_cmds.clear()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_f:
                tmp_audio_path = tmp_f.name
            generate_synthetic_wav(duration_seconds=2.0, output_path=tmp_audio_path)

            try:
                dest_obj.widget.main_window = DummyMW(tmp_audio_path)
                export_data_audio = {
                    "wp_posts": post_items,
                    "include_english": True,
                    "include_spanish": False,
                    "include_audio": True,
                    "apply_audio_fades": True,
                    "show_completion_dialog": False,
                }
                res_audio = dest_obj.execute_export(dest_obj.widget.main_window, export_data_audio)
                if not res_audio or len(uploaded_posts) != 2:
                    raise AssertionError(f"Multi-story audio export failed: expected 2 uploaded posts, got {len(uploaded_posts)}")
                for p_title, p_content in uploaded_posts:
                    if "<!-- wp:audio -->" not in p_content:
                        raise AssertionError(f"Audio-included export post '{p_title}' must contain <!-- wp:audio --> block")
                # Verify that fades were applied in ffmpeg invocation
                if not captured_cmds or not any("-af" in cmd for cmd in captured_cmds):
                    raise AssertionError(f"Fades were not passed to FFmpeg during execute_export: {captured_cmds}")
            finally:
                if os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)

            # Test C: Full Episode + Stories cross-linking footer correspondence and TOC audit
            uploaded_posts.clear()
            updated_posts.clear()
            mw_c = DummyMW("")
            dest_obj.widget.main_window = mw_c
            post_items_c = [
                {"task_label": "Story 1", "title": "Story A", "start": 0.0, "end": 50.0, "excerpt": "", "is_parent_episode": False},
                {"task_label": "Full Episode", "title": "Full Episode 101", "start": None, "end": None, "excerpt": "", "is_parent_episode": True},
                {"task_label": "Story 2", "title": "Story B", "start": 50.0, "end": 100.0, "excerpt": "", "is_parent_episode": False},
            ]
            export_data_crosslink = {
                "wp_posts": post_items_c,
                "include_english": True,
                "include_spanish": False,
                "include_audio": False,
                "link_parent_episode": True,
                "parent_episode_pos": "bottom",
                "update_parent_toc": True,
                "show_completion_dialog": False,
            }
            res_crosslink = dest_obj.execute_export(dest_obj.widget.main_window, export_data_crosslink)
            if not res_crosslink or len(uploaded_posts) != 3:
                raise AssertionError(f"Cross-linking export failed: expected 3 posts, got {len(uploaded_posts)}")
            # Full episode must have been published first
            if uploaded_posts[0][0] != "Full Episode 101":
                raise AssertionError(f"Expected Full Episode to be exported first, got '{uploaded_posts[0][0]}'")
            # Stories must have parent episode notice appended at the bottom
            for p_title, p_content in uploaded_posts[1:]:
                if "rtvs-parent-episode-notice" not in p_content:
                    raise AssertionError(f"Story post '{p_title}' missing parent episode correspondence notice: {p_content}")
                if "https://example.com/post/1" not in p_content:
                    raise AssertionError(f"Story post '{p_title}' notice did not link to parent episode URL: {p_content}")
                notice_idx = p_content.rfind("rtvs-parent-episode-notice")
                para_idx = p_content.find("<!-- wp:paragraph -->")
                if notice_idx <= para_idx:
                    raise AssertionError(f"Parent episode notice not placed at bottom of story post '{p_title}'")
            # Verify Full Episode TOC update was called
            if not updated_posts:
                raise AssertionError("Full Episode TOC update was not called via update_post")
            if "rtvs-episode-stories-list" not in updated_posts[0][1]:
                raise AssertionError("Updated Full Episode content missing Table of Contents HTML")
            # Verify project_metadata stored the parent episode info
            if not mw_c.project_metadata.get("wordpress", {}).get("parent_episode"):
                raise AssertionError("project_metadata['wordpress']['parent_episode'] was not set")

            # Test D: End-to-end Update Existing Episode & Backfill Stories with auto-resolve, Option B excerpt, & clean TOC slugs
            d_created = []
            d_updated = []

            class DummyBackfillDestClient:
                site_url = "https://rss.phillycam.org"
                api_base = "https://rss.phillycam.org/wp-json/wp/v2"
                def upload_media(self, file_path, filename=None):
                    return {"id": 200, "source_url": f"https://rss.phillycam.org/wp-content/uploads/{filename or 'clip.mp3'}"}
                def _get_request(self, url, params=None, headers=None, timeout=30):
                    if params and params.get("slug") == "april-29-2026":
                        return type("Resp", (), {
                            "status_code": 200,
                            "json": lambda *a, **k: [{
                                "id": 777,
                                "link": "https://rss.phillycam.org/april-29-2026/",
                                "slug": "april-29-2026",
                                "status": "publish",
                                "date": "2026-04-29T14:00:00",
                                "title": {"raw": "April 29 Show", "rendered": "April 29 Show"},
                                "excerpt": {"raw": "", "rendered": ""},
                                "content": {"raw": "<p>Original show notes text.</p>", "rendered": "<p>Original show notes text.</p>"},
                            }],
                        })()
                    return type("Resp", (), {"status_code": 404, "text": "Not found", "json": lambda *a, **k: []})()
                def create_post(self, title, content, excerpt="", status="draft", **kwargs):
                    pid = 800 + len(d_created)
                    d_created.append({"id": pid, "title": title, "content": content, "status": status, "kwargs": kwargs})
                    return {"id": pid, "link": f"https://rss.phillycam.org/?p={pid}", "slug": kwargs.get("slug", "")}
                def update_post(self, post_id, content=None, **kwargs):
                    d_updated.append({"id": post_id, "content": content, "kwargs": kwargs})
                    return {"id": post_id, "link": "https://rss.phillycam.org/april-29-2026/", "slug": "april-29-2026"}

            wp_dest_mod.WordPressClient = lambda *a, **k: DummyBackfillDestClient()
            mw_d = DummyMW("")
            post_items_d = [
                {"task_label": "Full Episode", "title": "April 29 Show", "start": None, "end": None, "excerpt": "", "is_parent_episode": True, "existing_post_url": "https://rss.phillycam.org/april-29-2026/", "replace_existing_audio": False, "is_podcast": True},
                {"task_label": "Story 1", "title": "Story One Title", "start": 0.0, "end": 50.0, "excerpt": "", "is_parent_episode": False},
            ]
            dest_obj.widget = DummyWpWidget(post_items_d)
            res_d = dest_obj.execute_export(mw_d, {
                "wp_posts": post_items_d,
                "export_mode": "update_existing",
                "include_english": True,
                "include_spanish": False,
                "include_audio": False,
                "link_parent_episode": True,
                "parent_episode_pos": "bottom",
                "update_parent_toc": True,
                "show_completion_dialog": False,
            })
            if not res_d:
                raise AssertionError("Update Existing Episode export returned False")
            if len(d_updated) < 2 or d_updated[0]["id"] != 777:
                raise AssertionError(f"Expected initial update + TOC update on Post #777, got {d_updated}")
            if d_updated[0]["kwargs"].get("excerpt") != "Original show notes text.":
                raise AssertionError(f"Option B excerpt not moved from existing post body: {d_updated[0]}")
            if d_updated[0]["kwargs"].get("status") != "publish" or d_updated[0]["kwargs"].get("date") != "2026-04-29T14:00:00":
                raise AssertionError(f"Full episode status/date mismatch: {d_updated[0]}")
            if len(d_created) != 1 or d_created[0]["status"] != "draft" or d_created[0]["kwargs"].get("date") != "2026-04-29T14:00:00":
                raise AssertionError(f"Backdated story draft mismatch: {d_created}")
            if "https://rss.phillycam.org/story-one-title/" not in (d_updated[-1]["content"] or ""):
                raise AssertionError(f"TOC on live episode must link to clean story slug URL instead of ?p= draft link: {d_updated[-1]['content']}")
        finally:
            if orig_wp_client_cls:
                wp_dest_mod.WordPressClient = orig_wp_client_cls
            wp_client_mod.subprocess.run = orig_sub_run
            if old_wp_url is not None:
                settings.setValue("wp_site_url", old_wp_url)
            else:
                settings.remove("wp_site_url")
            if old_wp_user is not None:
                settings.setValue("wp_username", old_wp_user)
            else:
                settings.remove("wp_username")

        item.status = "PASS"
        item.message = "WordPress multi-story upload (text-only and audio-included modes) and UI export button pluralization fully verified"

    def _test_gutenberg_html_structural_hygiene_audit(self, item: DiagnosticItem):
        try:
            import PySide6
        except ImportError:
            item.status = "WARNING"
            item.message = "PySide6 Qt GUI framework not present in current environment"
            return

        try:
            import plugins.wordpress.client as wp_client
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("wp_client", "plugins/wordpress/client.py")
            if not spec or not spec.loader:
                raise ImportError("Could not locate plugins/wordpress/client.py module")
            wp_client = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wp_client)

        sample_segments = [
            {"start": 0.0, "end": 5.0, "text": "Segment with <special> & 'escaped' chars.", "speaker": "SPEAKER_00"}
        ]
        class DummyMW:
            def get_effective_speaker_name(self, idx, seg):
                return "Host"

        html_out = wp_client.format_rich_text_to_html(sample_segments, main_window=DummyMW())

        open_para = html_out.count("<!-- wp:paragraph -->")
        close_para = html_out.count("<!-- /wp:paragraph -->")
        if open_para != close_para:
            raise AssertionError(f"Unbalanced Gutenberg paragraph blocks: {open_para} open vs {close_para} close")

        if "<p><p>" in html_out or "</p></p>" in html_out:
            raise AssertionError(f"Detected double-nested <p> tags in Gutenberg output: {html_out}")

        item.status = "PASS"
        item.message = f"Gutenberg HTML comment block balancing and paragraph tag hygiene fully verified ({open_para} blocks balanced)"

    def _test_wordpress_audio_inclusion_toggle_and_error_resilience(self, item: DiagnosticItem):
        import plugins.wordpress.client as wp_client

        class MockWpClient:
            def __init__(self):
                self.site_url = "https://example.com"
                self.uploaded_files = []
                self.created_posts = []

            def upload_media(self, file_path, filename=None):
                fname = filename or Path(file_path).name
                self.uploaded_files.append(fname)
                if fname.endswith(".png") or fname.endswith(".jpg"):
                    return {"id": 101, "source_url": f"https://example.com/wp-content/uploads/{fname}"}
                return {"id": 102, "source_url": f"https://example.com/wp-content/uploads/{fname}", "guid": {"rendered": f"https://example.com/wp-content/uploads/{fname}"}}

            def create_post(self, title, content, excerpt="", status="draft", featured_media_id=None, **kwargs):
                post_id = 500 + len(self.created_posts)
                post = {
                    "id": post_id,
                    "title": {"rendered": title},
                    "content": {"rendered": content},
                    "excerpt": {"rendered": excerpt},
                    "featured_media": featured_media_id or kwargs.get("featured_media"),
                    "link": f"https://example.com/?p={post_id}",
                }
                self.created_posts.append(post)
                return post

        class DummyMainWindow:
            def __init__(self, audio_path=None):
                self.audio_file = audio_path
                self.transcript = {
                    "segments": [
                        {"start": 0.0, "end": 5.0, "text": "Testing audio toggle feature.", "speaker": "SPEAKER_00"}
                    ]
                }
                self.logged = []

            def get_effective_speaker_name(self, idx, seg):
                return "Speaker 1"

            def transcript_for_range(self, start, end):
                return self.transcript["segments"]

            def clean_export_text(self, text, current_speaker=""):
                return text

            def log_activity(self, msg, level="info"):
                self.logged.append(msg)

        # 1. Test execute_wordpress_upload with include_audio=False (Text & Image only)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_img:
            f_img.write(b"\x89PNG\r\n\x1a\nfakeimage")
            img_path = f_img.name

        try:
            client1 = MockWpClient()
            win1 = DummyMainWindow(audio_path=None)  # No audio file loaded

            post_data = wp_client.execute_wordpress_upload(
                main_window=win1,
                client=client1,
                post_title="Text and Image Only Story",
                post_excerpt="Summary of text story",
                start=0.0,
                end=5.0,
                task_label="Story 1",
                include_english=True,
                include_spanish=False,
                spanish_presentation="accordion",
                primary_language="en",
                featured_image_path=img_path,
                include_audio=False,
            )

            # Assertions for text/image only mode:
            if not post_data or post_data.get("id") != 500:
                raise AssertionError(f"Expected draft post created in text-only mode, got {post_data}")
            # Ensure audio was NOT uploaded
            audio_uploads = [f for f in client1.uploaded_files if f.endswith(".mp3")]
            if audio_uploads:
                raise AssertionError(f"Audio was unexpectedly uploaded when include_audio=False: {audio_uploads}")
            # Ensure featured image WAS uploaded
            if not any(f.endswith(".png") for f in client1.uploaded_files):
                raise AssertionError("Featured image was not uploaded in text/image only mode")
            # Ensure post content contains NO <!-- wp:audio -->
            created_content = client1.created_posts[0]["content"]["rendered"]
            if "<!-- wp:audio -->" in created_content or "<audio" in created_content:
                raise AssertionError(f"Found unexpected wp:audio block in text-only post content:\n{created_content}")

            # 2. Test execute_wordpress_upload with include_audio=True
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_audio:
                f_audio.write(b"ID3fakeaudiodata")
                audio_path = f_audio.name

            try:
                orig_sub_run = wp_client.subprocess.run
                wp_client.subprocess.run = lambda *a, **k: type("Res", (), {"returncode": 0, "stderr": ""})()
                client2 = MockWpClient()
                win2 = DummyMainWindow(audio_path=audio_path)

                post_data_aud = wp_client.execute_wordpress_upload(
                    main_window=win2,
                    client=client2,
                    post_title="Audio Enabled Story",
                    post_excerpt="",
                    start=None,
                    end=None,
                    task_label="Full Episode",
                    include_english=True,
                    include_spanish=False,
                    spanish_presentation="accordion",
                    primary_language="en",
                    include_audio=True,
                )

                if not post_data_aud or post_data_aud.get("id") != 500:
                    raise AssertionError("Audio enabled export failed to create post")
                aud_content = client2.created_posts[0]["content"]["rendered"]
                if "<!-- wp:audio -->" not in aud_content:
                    raise AssertionError("Audio enabled export missing <!-- wp:audio --> block in post content")
            finally:
                wp_client.subprocess.run = orig_sub_run
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except Exception:
                    pass

            # 3. Test multi-story batch upload error resilience (Story 2 fails, stories 1 & 3 succeed)
            class ResilientBatchClient:
                def __init__(self):
                    self.site_url = "https://example.com"
                    self.posts = []
                def upload_media(self, p, filename=None):
                    return {"id": 10, "source_url": f"https://example.com/{filename or 'media.mp3'}"}
                def create_post(self, title, content, **k):
                    if "Failing Story" in title:
                        raise RuntimeError("HTTP 500 Internal Server Error from WordPress API")
                    p_id = len(self.posts) + 1
                    self.posts.append({"id": p_id, "title": title, "link": f"https://example.com/?p={p_id}"})
                    return self.posts[-1]

            batch_client = ResilientBatchClient()
            batch_stories = [
                {"title": "Story 1 Success", "task_label": "Story 1"},
                {"title": "Story 2 Failing Story", "task_label": "Story 2"},
                {"title": "Story 3 Success", "task_label": "Story 3"},
            ]

            results = []
            errors = []
            for st in batch_stories:
                try:
                    res = wp_client.execute_wordpress_upload(
                        main_window=win1,
                        client=batch_client,
                        post_title=st["title"],
                        post_excerpt="",
                        start=0.0,
                        end=5.0,
                        task_label=st["task_label"],
                        include_english=True,
                        include_spanish=False,
                        spanish_presentation="accordion",
                        primary_language="en",
                        include_audio=False,
                    )
                    results.append(res)
                except Exception as ex:
                    errors.append((st["title"], str(ex)))

            if len(results) != 2:
                raise AssertionError(f"Expected 2 successful posts, got {len(results)}")
            if len(errors) != 1 or "Failing Story" not in errors[0][0]:
                raise AssertionError(f"Expected 1 isolated failure for Story 2, got errors: {errors}")

            # 4. Test bilingual translation accordion placement (top vs bottom)
            bilingual_win = DummyMainWindow()
            bilingual_win.translations = {
                "en-es": {
                    "segments": [{"start": 0.0, "end": 5.0, "text": "Prueba de función de audio en español.", "speaker": "SPEAKER_00"}]
                }
            }
            client_acc = MockWpClient()

            # 4a. Accordion at TOP (before transcript)
            wp_client.execute_wordpress_upload(
                main_window=bilingual_win,
                client=client_acc,
                post_title="Accordion Top Story",
                post_excerpt="",
                start=0.0,
                end=5.0,
                task_label="Story 1",
                include_english=True,
                include_spanish=True,
                spanish_presentation="accordion",
                accordion_pos="top",
                primary_language="en",
                include_audio=False,
            )
            top_content = client_acc.created_posts[-1]["content"]["rendered"]
            acc_top_idx = top_content.find("rtvs-language-accordion")
            en_top_idx = top_content.find("Testing audio toggle feature")
            if acc_top_idx == -1 or en_top_idx == -1:
                raise AssertionError(f"Missing accordion or transcript in top placement post: {top_content}")
            if acc_top_idx > en_top_idx:
                raise AssertionError(f"Accordion was not placed at top (before transcript). acc_pos={acc_top_idx}, text_pos={en_top_idx}")

            # 4b. Accordion at BOTTOM (after transcript)
            wp_client.execute_wordpress_upload(
                main_window=bilingual_win,
                client=client_acc,
                post_title="Accordion Bottom Story",
                post_excerpt="",
                start=0.0,
                end=5.0,
                task_label="Story 1",
                include_english=True,
                include_spanish=True,
                spanish_presentation="accordion",
                accordion_pos="bottom",
                primary_language="en",
                include_audio=False,
            )
            bot_content = client_acc.created_posts[-1]["content"]["rendered"]
            acc_bot_idx = bot_content.find("rtvs-language-accordion")
            en_bot_idx = bot_content.find("Testing audio toggle feature")
            if acc_bot_idx == -1 or en_bot_idx == -1:
                raise AssertionError(f"Missing accordion or transcript in bottom placement post: {bot_content}")
            if acc_bot_idx < en_bot_idx:
                raise AssertionError(f"Accordion was not placed at bottom (after transcript). acc_pos={acc_bot_idx}, text_pos={en_bot_idx}")

            # 5. Test audio fades rendering as new MP3 and upload to WordPress
            captured_ffmpeg_cmds = []
            def fade_sub_run(cmd, *a, **k):
                captured_ffmpeg_cmds.append(list(cmd))
                out_f = Path(cmd[-1])
                out_f.write_bytes(b"ID3FadedMP3Bytes" + b"\x00" * 64)
                return type("Res", (), {"returncode": 0, "stderr": ""})()

            orig_wp_sub = wp_client.subprocess.run
            try:
                wp_client.subprocess.run = fade_sub_run
                client_fades = MockWpClient()
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_src:
                    f_src.write(b"ID3FakeSourceAudio")
                    src_audio = f_src.name

                win_fade = DummyMainWindow(audio_path=src_audio)

                # 5a. With fades enabled: fade_in=1.0s, fade_out=1.5s
                res_fade = wp_client.execute_wordpress_upload(
                    main_window=win_fade,
                    client=client_fades,
                    post_title="Story With Fades",
                    post_excerpt="",
                    start=0.0,
                    end=5.0,
                    task_label="Story 1",
                    include_english=True,
                    include_spanish=False,
                    include_audio=True,
                    fade_in=1.0,
                    fade_out=1.5,
                    fade_curve="linear",
                    apply_fades=True,
                )
                if not res_fade or not captured_ffmpeg_cmds:
                    raise AssertionError("FFmpeg was not called to render new MP3 with fades")
                last_cmd = captured_ffmpeg_cmds[-1]
                af_args = [last_cmd[i+1] for i, arg in enumerate(last_cmd) if arg == "-af"]
                if not af_args or "afade=t=in" not in af_args[0] or "afade=t=out" not in af_args[0]:
                    raise AssertionError(f"Expected afade filters in FFmpeg command, got: {last_cmd}")
                if "afade=t=in:ss=0:d=1.000:curve=tri" not in af_args[0]:
                    raise AssertionError(f"Expected linear 1.000s fade-in filter, got: {af_args[0]}")
                if "afade=t=out:st=3.500:d=1.500:curve=tri" not in af_args[0]:
                    raise AssertionError(f"Expected linear 1.500s fade-out filter starting at 3.500s, got: {af_args[0]}")

                # Ensure rendered file was uploaded to media library
                if not any("Story_With_Fades" in f or "audio" in f for f in client_fades.uploaded_files):
                    raise AssertionError(f"Rendered faded MP3 was not uploaded: {client_fades.uploaded_files}")
                fade_post_content = client_fades.created_posts[-1]["content"]["rendered"]
                if "<!-- wp:audio -->" not in fade_post_content:
                    raise AssertionError("Audio figure block missing from faded post content")

                # 5b. With fades disabled: apply_fades=False
                captured_ffmpeg_cmds.clear()
                wp_client.execute_wordpress_upload(
                    main_window=win_fade,
                    client=client_fades,
                    post_title="Story Without Fades",
                    post_excerpt="",
                    start=0.0,
                    end=5.0,
                    task_label="Story 1",
                    include_english=True,
                    include_spanish=False,
                    include_audio=True,
                    fade_in=1.0,
                    fade_out=1.5,
                    fade_curve="linear",
                    apply_fades=False,
                )
                if captured_ffmpeg_cmds:
                    last_cmd_nofade = captured_ffmpeg_cmds[-1]
                    if "-af" in last_cmd_nofade:
                        raise AssertionError(f"Unexpected -af filter present when apply_fades=False: {last_cmd_nofade}")
            finally:
                wp_client.subprocess.run = orig_wp_sub
                try:
                    Path(src_audio).unlink(missing_ok=True)
                except Exception:
                    pass

        finally:
            try:
                Path(img_path).unlink(missing_ok=True)
            except Exception:
                pass

        # Execute Castos podcast integration check
        self._test_wordpress_castos_podcast_integration(item)
        # Execute Featured Image Caption & Alt Text integration check
        self._test_wordpress_featured_image_caption_and_alt_text(item)

        item.status = "PASS"
        item.message = "WordPress audio inclusion toggle, error resilience, Castos podcast, and image caption/alt integration verified"

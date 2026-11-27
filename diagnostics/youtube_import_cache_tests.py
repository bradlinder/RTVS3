"""Diagnostic tests for YouTube Episode Import, yt-dlp runner, Managed Remote Media Cache, and Shortcut/Guide sync."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
from types import SimpleNamespace


class DiagnosticYouTubeImportCacheTestsMixin:
    """Automated verification mixin for YouTube import & Managed Remote Media Cache."""

    def _test_youtube_episode_import_and_yt_dlp_provisioning(self, item):
        from plugins.youtube.yt_dlp_runner import (
            DEFAULT_YOUTUBE_QUALITY,
            build_yt_dlp_download_command,
            build_yt_dlp_probe_command,
            build_youtube_project_stem,
            classify_yt_dlp_error,
            extract_youtube_id_strict,
            get_format_selector_for_preset,
            normalize_cookie_browser,
            parse_sha256_sums,
            parse_yt_dlp_metadata_json,
            parse_yt_dlp_progress_line,
        )
        from plugins.youtube.yt_import_dialog import populate_project_from_youtube_import
        from prs_shared import ProjectMetadataDict

        # 1. Strict URL validation & rejection of unsafe inputs
        vid, canon = extract_youtube_id_strict("https://youtu.be/dQw4w9WgXcQ?t=45")
        assert vid == "dQw4w9WgXcQ" and canon == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        vid2, _ = extract_youtube_id_strict("https://studio.youtube.com/video/AbCdEf12345/edit")
        assert vid2 == "AbCdEf12345"
        vid3, _ = extract_youtube_id_strict("AbCdEf12345")
        assert vid3 == "AbCdEf12345"
        for bad in ("--exec=whoami", "file:///etc/passwd", "https://evil.example.com/watch?v=dQw4w9WgXcQ", "not_a_url"):
            bvid, bcanon = extract_youtube_id_strict(bad)
            assert bvid == "" and bcanon is None, f"Should reject unsafe input: {bad}"

        # 2. Quality presets (default 1080p MP4 H.264/AAC) & cookie browser whitelist
        assert DEFAULT_YOUTUBE_QUALITY == "1080p"
        fmt_1080, ext_1080 = get_format_selector_for_preset("1080p")
        assert "height<=1080" in fmt_1080 and "avc1" in fmt_1080 and ext_1080 == "mp4"
        fmt_aud, ext_aud = get_format_selector_for_preset("audio_only")
        assert "bestaudio" in fmt_aud and ext_aud == "m4a"
        assert normalize_cookie_browser("chrome") == "chrome"
        assert normalize_cookie_browser("chrome;rm -rf /") == ""

        # 3. Safe subprocess command construction (list args, '--' separator, whitelisted cookies)
        cmd, out_ext = build_yt_dlp_download_command(
            "/usr/local/bin/yt-dlp",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "/tmp/test_out",
            quality_preset="1080p",
            cookies_browser="firefox",
            ffmpeg_location="/usr/bin",
        )
        assert out_ext == "mp4"
        assert "--merge-output-format" in cmd and "mp4" in cmd
        assert "--cookies-from-browser" in cmd and "firefox" in cmd
        assert "--ffmpeg-location" in cmd
        assert cmd[-2:] == ["--", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"]

        probe_cmd = build_yt_dlp_probe_command("/usr/local/bin/yt-dlp", canon, cookies_browser="invalid_browser")
        assert "--cookies-from-browser" not in probe_cmd
        assert probe_cmd[-2:] == ["--", canon]

        # 4. SHA-256 manifest parsing
        fake_digest = "a" * 64
        sums = f"{fake_digest}  yt-dlp.exe\n{'b'*64}  yt-dlp_linux\n"
        assert parse_sha256_sums(sums, "yt-dlp.exe") == fake_digest
        assert parse_sha256_sums(sums, "missing.bin") is None

        # 5. Metadata normalization, chapter extraction, size estimation, clean project stem
        raw_info = {
            "id": "AbCdEf12345",
            "title": "City Council Hearing: Transit & Budget",
            "description": "Full coverage of the transit budget hearing.\n\n00:00 Intro",
            "channel": "Community News Network",
            "duration": 1800,
            "upload_date": "20260412",
            "chapters": [
                {"title": "Opening Remarks", "start_time": 0, "end_time": 300},
                {"title": "Budget Vote", "start_time": 300, "end_time": 1800},
            ],
            "formats": [
                {"height": 1080, "vcodec": "avc1.640028", "acodec": "none", "filesize": 400_000_000},
                {"vcodec": "none", "acodec": "mp4a.40.2", "ext": "m4a", "filesize": 30_000_000},
            ],
        }
        meta = parse_yt_dlp_metadata_json(raw_info)
        assert meta["upload_date"] == "2026-04-12"
        assert len(meta["chapters"]) == 2
        assert meta["size_estimates"]["1080p"] == 430_000_000
        assert meta["size_estimates"]["audio_only"] == 30_000_000
        assert meta["suggested_project_stem"].startswith("2026-04-12_City_Council")
        assert "AbCdEf12345" not in build_youtube_project_stem(raw_info["title"], "20260412", "AbCdEf12345")

        # 6. Progress parsing & actionable error classification
        p_dl = parse_yt_dlp_progress_line("[download]  50.0% of  410.0MiB at  10.2MiB/s ETA 00:20")
        assert p_dl and p_dl["stage"] == "downloading" and 40 <= p_dl["percent"] <= 50
        p_merge = parse_yt_dlp_progress_line('[Merger] Merging formats into "/tmp/out.mp4"')
        assert p_merge and p_merge["stage"] == "merging" and p_merge["percent"] >= 90

        err_403 = classify_yt_dlp_error("ERROR: unable to download video data: HTTP Error 403: Forbidden")
        assert err_403["needs_update"] is True
        err_bot = classify_yt_dlp_error("ERROR: [youtube] AbCdEf12345: Sign in to confirm you're not a bot.")
        assert err_bot["needs_cookies"] is True

        # 7. Project & WordPress metadata population (New + Update modes + chapter seeding)
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mp4 = Path(tmpdir) / "episode.mp4"
            fake_mp4.write_bytes(b"0" * 1024)

            win_new = SimpleNamespace(project_metadata=ProjectMetadataDict(), stories=[], project_dirty=False)
            populate_project_from_youtube_import(
                win_new,
                meta,
                fake_mp4,
                quality_preset="1080p",
                cache_key="youtube:AbCdEf12345:1080p",
                import_chapters=True,
                existing_wp_url="",
            )
            assert win_new.project_metadata["remote_media_source"]["provider"] == "youtube"
            assert win_new.project_metadata["remote_media_source"]["video_id"] == "AbCdEf12345"
            assert win_new.project_metadata["wordpress"]["youtube_video_id"] == "AbCdEf12345"
            assert win_new.project_metadata["wordpress"]["youtube_apply_all"] is True
            assert win_new.project_metadata["wordpress"]["include_audio"] is False
            assert win_new.project_metadata["wordpress"]["export_mode"] == "new_episode"
            assert len(win_new.stories) == 2
            assert win_new.stories[0].title == "Opening Remarks"

            win_upd = SimpleNamespace(project_metadata=ProjectMetadataDict(), stories=[], project_dirty=False)
            populate_project_from_youtube_import(
                win_upd,
                meta,
                fake_mp4,
                quality_preset="1080p",
                cache_key="youtube:AbCdEf12345:1080p",
                import_chapters=False,
                existing_wp_url="https://station.example.org/2026/04/city-council/",
            )
            assert win_upd.project_metadata["wordpress"]["export_mode"] == "update_existing"
            assert win_upd.project_metadata["wordpress"]["existing_post_url"] == "https://station.example.org/2026/04/city-council/"
            assert win_upd.project_metadata["wordpress"]["youtube_video_id"] == "AbCdEf12345"

            # 8. End-to-end MainWindow media-loader contract for prompt_load_youtube_episode_dialog
            from unittest.mock import patch
            from media_batch import MediaBatchMixin
            import plugins.youtube.yt_import_dialog as yt_dlg_mod
            from remote_media_cache_dialog import reattach_downloaded_media_to_project

            assert hasattr(MediaBatchMixin, "load_media_file"), "MainWindow must expose load_media_file"

            class _FakeAction:
                def __init__(self):
                    self.enabled = False
                def setEnabled(self, val):
                    self.enabled = bool(val)

            class _FakeStatusBar:
                def __init__(self):
                    self.last_msg = ""
                def showMessage(self, msg):
                    self.last_msg = msg

            class _FakeDialog:
                def __init__(self, *args, **kwargs):
                    self.download_result = {
                        "file_path": str(fake_mp4),
                        "video_meta": meta,
                        "quality_preset": "1080p",
                        "cache_key": "youtube:AbCdEf12345:1080p",
                        "import_chapters": True,
                        "existing_wp_url": "",
                        "from_cache": False,
                    }
                def exec(self):
                    return True

            calls = []
            sb = _FakeStatusBar()
            redl_act = _FakeAction()

            def _fake_load_media(path_str, source="media load", restore_adjacent_project=False):
                calls.append(("load_media_file", path_str, source))
                fake_win.audio_file = Path(path_str)
                fake_win.project_metadata = ProjectMetadataDict()
                fake_win.stories = []
                return True

            def _forbidden_close(prompt=True):
                calls.append(("close_project", prompt))
                return True

            fake_win = SimpleNamespace(
                audio_file=None,
                project_metadata=ProjectMetadataDict(),
                stories=[],
                project_dirty=False,
                redownload_remote_media_action=redl_act,
                load_media_file=_fake_load_media,
                close_project=_forbidden_close,
                statusBar=lambda: sb,
            )

            with patch.object(yt_dlg_mod, "LoadYouTubeEpisodeDialog", _FakeDialog):
                ok = yt_dlg_mod.prompt_load_youtube_episode_dialog(fake_win)
            assert ok is True
            assert len(calls) == 1 and calls[0][0] == "load_media_file"
            assert Path(calls[0][1]) == fake_mp4
            assert fake_win.audio_file == fake_mp4
            assert fake_win.project_metadata["remote_media_source"]["video_id"] == "AbCdEf12345"
            assert len(fake_win.stories) == 2
            assert redl_act.enabled is True
            assert "Loaded YouTube video" in sb.last_msg

            # Cancelled unsaved-project prompt inside load_media_file must abort without mutating project state
            sentinel_meta = ProjectMetadataDict({"title": "Keep Existing Project"})
            cancel_win = SimpleNamespace(
                audio_file=Path("existing.mp3"),
                project_metadata=sentinel_meta,
                stories=[],
                load_media_file=lambda *a, **kw: False,
            )
            with patch.object(yt_dlg_mod, "LoadYouTubeEpisodeDialog", _FakeDialog):
                ok_cancel = yt_dlg_mod.prompt_load_youtube_episode_dialog(cancel_win)
            assert ok_cancel is False
            assert cancel_win.project_metadata["title"] == "Keep Existing Project"
            assert "remote_media_source" not in cancel_win.project_metadata

            # Re-attaching re-downloaded media must re-enable processing actions
            tools_enabled = []
            reattach_win = SimpleNamespace(
                audio_file=None,
                current_media_is_video=False,
                set_tools_actions_enabled=lambda val: tools_enabled.append(bool(val)),
            )
            assert reattach_downloaded_media_to_project(reattach_win, fake_mp4) is True
            assert reattach_win.audio_file == fake_mp4.resolve()
            assert reattach_win.current_media_is_video is True
            assert tools_enabled == [True]

        item.status = "PASS"
        item.message = "YouTube URL validation, 1080p format selection, SHA-256 verification, MainWindow load_media_file handoff, chapter seeding, error recovery, and WP New/Update wiring verified"

    def _test_managed_remote_media_cache_and_menu_shortcut_sync(self, item):
        from remote_media_cache import (
            RemoteMediaCacheManager,
            is_path_inside_cache,
            make_cache_key,
        )
        from plugin_base import BasePlugin, PluginManifest
        from plugins.youtube.plugin import Plugin as YouTubePlugin
        from plugins.wordpress.plugin import Plugin as WordPressPlugin
        from shortcuts.schema import SHORTCUT_DEFINITIONS
        import embedded_guides
        import media_batch

        assert hasattr(media_batch.MediaBatchMixin, "open_manage_cached_media_dialog")
        assert hasattr(media_batch.MediaBatchMixin, "redownload_current_project_remote_media")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache_dir = root / "cache"
            outside_file = root / "user_recording.mp4"
            outside_file.write_bytes(b"USER_OWNED" * 100)

            mgr = RemoteMediaCacheManager(cache_dir=cache_dir)

            # 1. Path-jail enforcement: outside files must be rejected
            assert is_path_inside_cache(outside_file, cache_dir) is False
            try:
                mgr.register_download("youtube:bad:1080p", outside_file, "youtube", "https://youtu.be/bad12345678")
                raise AssertionError("Should refuse registering file outside managed cache")
            except ValueError:
                pass

            # 2. Register 3 files (~400 KB each) and verify cache-hit reuse
            yt_dir = mgr.get_provider_dir("youtube")
            wp_dir = mgr.get_provider_dir("wordpress")
            f1 = yt_dir / "ep1.mp4"
            f2 = wp_dir / "ep2.mp3"
            f3 = yt_dir / "ep3.mp4"
            for f in (f1, f2, f3):
                f.write_bytes(b"X" * (400 * 1024))

            k1 = make_cache_key("youtube", "vid11111111", "1080p")
            k2 = make_cache_key("wordpress", "202")
            k3 = make_cache_key("youtube", "vid33333333", "1080p")

            mgr.register_download(k1, f1, "youtube", "https://www.youtube.com/watch?v=vid11111111", "vid11111111", "1080p", "Ep 1")
            mgr.register_download(k2, f2, "wordpress", "https://example.org/ep2", "202", "audio", "Ep 2")
            mgr.register_download(k3, f3, "youtube", "https://www.youtube.com/watch?v=vid33333333", "vid33333333", "1080p", "Ep 3")

            assert mgr.get_existing_cached_file(k1) == f1.resolve()

            # Mark k2 exported so LRU cap evicts k2 BEFORE unexported k1; protect k3 as active open file
            mgr.mark_exported(k2, export_target="wordpress")
            # Cap at ~0.0008 GB (~859 KB) so 1 of 3 files (1.2 MB total -> <= 859 KB) must be evicted
            evict_res = mgr.enforce_size_cap(cap_gb=0.0008, protected_paths=[f3])
            assert evict_res["deleted_count"] == 1
            assert evict_res["deleted_keys"] == [k2], f"Expected exported k2 evicted first, got {evict_res['deleted_keys']}"
            assert not f2.exists() and f1.exists() and f3.exists()

            # Active-file immunity: even with a tiny cap (1 byte), protected active file f3 MUST NOT be evicted
            evict_tiny = mgr.enforce_size_cap(cap_gb=0.0000001, protected_paths=[f3])
            assert f3.exists(), "Active open media file must never be evicted"
            assert not f1.exists()
            assert outside_file.exists(), "User-owned file outside cache must never be touched"

            # Disk-space cap-exceed warning check
            space = mgr.check_disk_space(estimated_bytes=5 * (1024 ** 3), cap_gb=2.0)
            assert space["exceeds_cap"] is True and len(space["warnings"]) >= 1

        # 3. Decoupled Plugin Manager hooks on BasePlugin, YouTube, and WordPress
        assert hasattr(BasePlugin, "get_remote_open_actions")
        assert hasattr(BasePlugin, "can_redownload_remote_source")
        assert hasattr(BasePlugin, "redownload_remote_source")
        assert hasattr(BasePlugin, "get_cache_maintenance_actions")

        yt_plugin = YouTubePlugin(PluginManifest(id="youtube", name="YouTube"), app=None)
        wp_plugin = WordPressPlugin(PluginManifest(id="wordpress", name="WordPress"), app=None)
        assert any("YouTube" in lbl for lbl, _ in yt_plugin.get_remote_open_actions())
        assert any("WordPress" in lbl for lbl, _ in wp_plugin.get_remote_open_actions())
        assert yt_plugin.can_redownload_remote_source({"provider": "youtube"}) is True
        assert yt_plugin.can_redownload_remote_source({"provider": "wordpress"}) is False
        assert wp_plugin.can_redownload_remote_source({"provider": "wordpress"}) is True
        assert len(yt_plugin.get_cache_maintenance_actions()) >= 1

        # 4. Shortcuts & Guides Parity
        by_id = {d.action_id: d for d in SHORTCUT_DEFINITIONS}
        assert "open_remote_youtube" in by_id and by_id["open_remote_youtube"].default_seq == "Ctrl+Alt+Y"
        assert "open_remote_wordpress" in by_id
        assert "manage_cached_media" in by_id
        # Verify no shortcut collision on Ctrl+Alt+Y
        seqs = [d.action_id for d in SHORTCUT_DEFINITIONS if d.default_seq == "Ctrl+Alt+Y"]
        assert seqs == ["open_remote_youtube"], f"Collision on Ctrl+Alt+Y: {seqs}"

        readme_text = Path("README.md").read_text(encoding="utf-8")
        assert "Ctrl+Alt+Y" in readme_text
        assert "Open Remote Episode" in readme_text
        assert "Manage Cached Remote Media" in readme_text
        assert "Open Remote Episode" in embedded_guides.get_embedded_guide("workflow")
        assert "From YouTube Video" in embedded_guides.get_embedded_guide("video_shows")
        assert "Managed Remote Media Cache" in embedded_guides.get_embedded_guide("youtube")

        # 5. Core module NameError regression guards (v3.10.32-beta)
        import playback_preferences as _pp_mod
        import preferences_reset_dialog as _prd_mod
        import transcript_context_menu_mixin as _tcmm_mod
        assert hasattr(_pp_mod, "Story") and hasattr(_pp_mod, "copy")
        assert hasattr(_prd_mod, "DEFAULT_GITHUB_REPO") and bool(_prd_mod.DEFAULT_GITHUB_REPO)
        assert hasattr(_tcmm_mod, "logger") and hasattr(_tcmm_mod.logger, "warning")

        item.status = "PASS"
        item.message = "Managed Remote Media Cache (LRU, path jail, active-file immunity), plugin hooks, shortcuts, and user guides parity verified"


__all__ = ["DiagnosticYouTubeImportCacheTestsMixin"]

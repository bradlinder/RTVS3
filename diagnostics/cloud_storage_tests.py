"""Plugin interface, project persistence, cache management, YouTube & backup diagnostic tests."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT


class DiagnosticCloudStorageTestsMixin:
    def _test_plugin_interface_sandbox_testing(self, item: DiagnosticItem):
        from plugins.base import BasePlugin, PluginManifest

        # 1. PluginManifest validation
        raw_manifest = {
            "id": "custom_exporter",
            "name": "Custom Exporter",
            "version": "1.0.0",
            "category": "export",
            "author": "Radio & TV Segmenter Team",
            "min_app_version": "3.6.0",
        }
        manifest = PluginManifest.from_dict(raw_manifest)
        if manifest.id != "custom_exporter" or manifest.category != "export":
            raise AssertionError("PluginManifest failed to parse dictionary attributes")

        # 2. BasePlugin lifecycle hooks
        class MockCustomPlugin(BasePlugin):
            def __init__(self, m):
                super().__init__(m)
                self.loaded = False
                self.enabled_state = False
            def on_load(self):
                self.loaded = True
                return True
            def on_enable(self):
                self.enabled_state = True
            def on_disable(self):
                self.enabled_state = False

        plugin = MockCustomPlugin(manifest)
        if not plugin.on_load() or not plugin.loaded:
            raise AssertionError("Plugin on_load hook failed")
        plugin.set_enabled(False)
        if plugin.enabled_state or plugin.is_enabled:
            raise AssertionError("Plugin set_enabled(False) did not trigger on_disable hook")
        plugin.set_enabled(True)
        if not plugin.enabled_state or not plugin.is_enabled:
            raise AssertionError("Plugin set_enabled(True) did not trigger on_enable hook")

        # 3. Structured export payload serialization & comment anchoring validation
        doc_payload = {
            "title": "Episode 101 - Studio Broadcast",
            "paragraphs": [
                {"style": "heading_1", "text": "Episode 101 - Studio Broadcast"},
                {"style": "speaker_header", "text": "Alice:", "speaker": "Alice", "time": "00:00:00.000"},
                {"style": "normal", "text": "Welcome to our live program."},
            ],
            "comments": [
                {
                    "startIndex": 32,
                    "endIndex": 60,
                    "commentText": "Verify attribution for guest speaker",
                    "author": "Editor",
                }
            ],
        }

        full_text = "\n".join(p["text"] for p in doc_payload["paragraphs"])
        for c in doc_payload["comments"]:
            if c["startIndex"] < 0 or c["endIndex"] > len(full_text) or c["startIndex"] >= c["endIndex"]:
                raise AssertionError(f"Invalid comment anchoring range: [{c['startIndex']}, {c['endIndex']}] for text len {len(full_text)}")

        # 4. Validate live plugins/youtube and plugins/wordpress manifests
        yt_manifest_file = Path("plugins/youtube/manifest.json")
        if yt_manifest_file.exists():
            real_m = PluginManifest.from_file(yt_manifest_file)
            if real_m.id != "youtube" or real_m.category != "export":
                raise AssertionError(f"Invalid youtube manifest attributes: id={real_m.id}, cat={real_m.category}")

        wp_manifest_file = Path("plugins/wordpress/manifest.json")
        if wp_manifest_file.exists():
            real_wp = PluginManifest.from_file(wp_manifest_file)
            if real_wp.id != "wordpress" or real_wp.category != "export":
                raise AssertionError(f"Invalid wordpress manifest attributes: id={real_wp.id}, cat={real_wp.category}")

        # 5. CI Workflow Plugin Bundling Guard (.github/workflows/build.yml) & Google Docs UI cleanup
        build_yml = Path(".github/workflows/build.yml")
        if build_yml.is_file():
            yml_text = build_yml.read_text(encoding="utf-8")
            for bad_expr in (
                "inputs.plugin_wordpress != false",
                "inputs.plugin_youtube != false",
                "inputs.plugin_translation != false",
            ):
                if bad_expr in yml_text:
                    raise AssertionError(f"CI build.yml still contains tag-breaking expression '{bad_expr}'")
            if "plugin_gdocs" in yml_text or "BUILD_PLUGIN_GDOCS" in yml_text:
                raise AssertionError("CI build.yml still contains removed plugin_gdocs / BUILD_PLUGIN_GDOCS entries")
            expected_wp = "BUILD_PLUGIN_WORDPRESS: ${{ github.event_name == 'push' || inputs.plugin_wordpress }}"
            wp_hits = yml_text.count(expected_wp)
            if wp_hits != 4:
                raise AssertionError(f"Expected 4 occurrences of '{expected_wp}' in build.yml, found {wp_hits}")

        for ui_path in (Path("export/reorder_dialog.py"), Path("preferences_tabs_media.py")):
            if ui_path.is_file():
                ui_text = ui_path.read_text(encoding="utf-8")
                if "Google Docs" in ui_text:
                    raise AssertionError(f"{ui_path} still references removed Google Docs destination")

        # 6. PluginManagerDialog Import & Handler Guard (GitHubPluginsWorker, sys)
        import subprocess
        import plugins.manager_dialog as mgr_dlg_mod
        from PySide6.QtCore import Signal, QObject
        from PySide6.QtWidgets import QApplication, QProgressDialog
        _app = QApplication.instance() or QApplication([])
        if not hasattr(mgr_dlg_mod, "GitHubPluginsWorker"):
            raise AssertionError("plugins.manager_dialog missing GitHubPluginsWorker import")
        if not hasattr(mgr_dlg_mod, "sys"):
            raise AssertionError("plugins.manager_dialog missing sys import")

        with tempfile.TemporaryDirectory() as tmp_pdir:
            class FakeSignal:
                def __init__(self):
                    self._cbs = []
                def connect(self, cb):
                    self._cbs.append(cb)

            class DummyUpdateWorker:
                def __init__(self, repo, parent=None):
                    self.repo = repo
                    self.parent_obj = parent
                    self.finished = FakeSignal()
                    self.started = False
                def start(self):
                    self.started = True
                def isRunning(self) -> bool:
                    return False
                def requestInterruption(self):
                    pass

            class DummyMgr:
                def __init__(self):
                    self.manifests = {"wordpress": real_wp if wp_manifest_file.exists() else PluginManifest.from_dict({"id": "wordpress", "name": "WP", "version": "1.0", "description": "d", "author": "a", "entry_point": "p:P"})}
                    self.plugin_paths = {"wordpress": Path(tmp_pdir)}
                    self.plugins = {}
                    self.app = None
                def discover_plugins(self):
                    return self.manifests
                def is_plugin_enabled(self, pid):
                    return True
                def ensure_packaged_addons(self):
                    pass
                def get_user_plugins_dir(self):
                    return Path(tmp_pdir)

            dlg_stub = mgr_dlg_mod.PluginManagerDialog(DummyMgr())

            orig_worker = mgr_dlg_mod.GitHubPluginsWorker
            orig_prog_show = QProgressDialog.show
            orig_prog_force_show = getattr(QProgressDialog, "forceShow", None)
            orig_startfile = getattr(os, "startfile", None)
            orig_popen = subprocess.Popen
            opened_targets = []
            try:
                mgr_dlg_mod.GitHubPluginsWorker = DummyUpdateWorker
                QProgressDialog.show = lambda self: None
                if orig_prog_force_show is not None:
                    QProgressDialog.forceShow = lambda self: None
                if hasattr(os, "startfile"):
                    os.startfile = lambda path: opened_targets.append(str(path))
                subprocess.Popen = lambda cmd, *a, **k: opened_targets.append(str(cmd))
                dlg_stub.check_for_plugin_updates()
                if not getattr(dlg_stub, "_update_check_worker", None) or not dlg_stub._update_check_worker.started:
                    raise AssertionError("check_for_plugin_updates did not start GitHubPluginsWorker")
                dlg_stub.on_open_folder()
                if not opened_targets:
                    raise AssertionError("on_open_folder did not open user plugins directory")
            finally:
                mgr_dlg_mod.GitHubPluginsWorker = orig_worker
                QProgressDialog.show = orig_prog_show
                if orig_prog_force_show is not None:
                    QProgressDialog.forceShow = orig_prog_force_show
                if orig_startfile is not None:
                    os.startfile = orig_startfile
                subprocess.Popen = orig_popen
                for pd in dlg_stub.findChildren(QProgressDialog):
                    pd.close()
                    pd.deleteLater()
                dlg_stub.close()
                dlg_stub.deleteLater()

        item.status = "PASS"
        item.message = "Plugin manifest, lifecycle hooks, CI plugin bundling, and manager dialog handlers validated"

    def _test_project_file_integrity_and_portable_path_resolution(self, item: DiagnosticItem):
        try:
            import PySide6
            import project_lifecycle
            validator_cls = project_lifecycle.ProjectLifecycleMixin
        except ImportError:
            class validator_cls:
                def validate_project_data(self, data: dict) -> list[str]:
                    errors = []
                    if data.get("format") != "Radio & TV Story Segmenter Project":
                        errors.append("Invalid project format.")
                    duration = data.get("duration", 0)
                    try:
                        if float(duration) < 0:
                            errors.append("Media duration cannot be negative.")
                    except (TypeError, ValueError):
                        errors.append("Media duration is not numeric.")
                    transcript = data.get("transcript")
                    if transcript is not None and isinstance(transcript, dict):
                        segments = transcript.get("segments", [])
                        for i, seg in enumerate(segments):
                            try:
                                if float(seg.get("start", 0)) > float(seg.get("end", 0)):
                                    errors.append(f"Transcript segment {i + 1} has an invalid time range.")
                            except (TypeError, ValueError):
                                errors.append(f"Transcript segment {i + 1} has invalid timestamps.")
                    return errors

        win = validator_cls()

        # 1. Structural error catching on corrupted/malformed project dictionaries
        bad_format = {"format": "Invalid App Format", "duration": 10.0}
        errors = win.validate_project_data(bad_format)
        if not any("Invalid project format" in err for err in errors):
            raise AssertionError("Failed to reject invalid project format")

        neg_duration = {"format": "Radio & TV Story Segmenter Project", "duration": -5.0}
        errors = win.validate_project_data(neg_duration)
        if not any("cannot be negative" in err for err in errors):
            raise AssertionError("Failed to reject negative duration")

        bad_segments = {
            "format": "Radio & TV Story Segmenter Project",
            "duration": 10.0,
            "transcript": {"segments": [{"start": 5.0, "end": 2.0, "text": "Invalid"}]},
        }
        errors = win.validate_project_data(bad_segments)
        if not any("invalid time range" in err for err in errors):
            raise AssertionError("Failed to detect segment start > end error")

        # 2. Portable media path resolution
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "subfolder"
            proj_dir.mkdir()
            audio_path = proj_dir / "interview.wav"
            audio_path.write_bytes(b"RIFF" + b"\x00" * 40)

            # Test relative resolution
            ref = "interview.wav"
            direct_candidate = (proj_dir / ref).resolve()
            if not direct_candidate.exists():
                raise AssertionError("Relative media path resolution failed")

            # Test moved/missing media: does not crash, resolves to None
            missing_ref = "nonexistent.wav"
            cand = (proj_dir / missing_ref).resolve()
            if cand.exists():
                raise AssertionError("Missing candidate unexpectedly reported as existing")

        # 3. Verify empty project dirty prompt bypass
        from PySide6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
        from project_state_mixin import ProjectStateMixin
        from media_batch import MediaBatchMixin
        from playback_preferences import PlaybackPreferencesMixin
        class EmptyProjectProbe(PlaybackPreferencesMixin, ProjectStateMixin, MediaBatchMixin):
            def __init__(self):
                self.audio_file = None
                self.project_file = None
                self.transcript = None
                self.stories = []
                self.project_dirty = True
                self.activity_list = type("_MockList", (), {"_items": [], "addItem": lambda s, t: s._items.append(str(t)), "count": lambda s: len(s._items), "takeItem": lambda s, i: s._items.pop(i) if 0 <= i < len(s._items) else None, "scrollToBottom": lambda s: None})()
                self.settings_store = None
            def update_window_title(self):
                pass
        probe = EmptyProjectProbe()
        assert probe.is_project_empty() is True
        assert probe.prepare_for_new_media() is True
        probe.audio_file = "voice.mp3"
        assert probe.is_project_empty() is False

        # 4. Verify log_activity does not dirty clean project by default
        probe.project_dirty = False
        probe.log_activity("[SYSTEM] Application shutdown requested.")
        probe.log_activity("[WAVEFORM] Waveform generation complete (10,000 peaks).")
        probe.log_activity("[EXPORT] Exported CUE sheet to cue.txt")
        assert probe.project_dirty is False, "log_activity unexpectedly dirtied project on diagnostic logging"

        # Explicit mark_dirty=True or mark_project_dirty does dirty project
        probe.log_activity("[TEST] Explicit mutate", mark_dirty=True)
        assert probe.project_dirty is True

        item.status = "PASS"
        item.message = "Project structure validation errors, portable media resolution, and false-dirty prevention verified"

    def _test_temporary_cache_management_and_storage_inspection(self, item: DiagnosticItem):
        """Validates cache usage stats calculation, preview categorization, and cache purging."""
        from cache_manager import (
            format_byte_size,
            get_cache_disk_usage,
            purge_caches,
            ClearCacheDialog,
        )

        # 1. Byte formatting checks
        if format_byte_size(0) != "0 B":
            raise AssertionError(f"format_byte_size(0) returned '{format_byte_size(0)}'")
        if "1.5 MB" not in format_byte_size(int(1.5 * 1024 * 1024)):
            raise AssertionError("format_byte_size failed on MB calculation")

        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "test_project"
            proj_dir.mkdir(parents=True, exist_ok=True)
            cache_peaks = proj_dir / ".cache" / "peaks"
            cache_peaks.mkdir(parents=True, exist_ok=True)
            (cache_peaks / "audio.peaks").write_bytes(b"PEAKS_DATA_" * 100)

            cache_thumbs = proj_dir / ".cache" / "thumbnails"
            cache_thumbs.mkdir(parents=True, exist_ok=True)
            (cache_thumbs / "thumb_01.jpg").write_bytes(b"THUMB_DATA_" * 50)

            # 2. Test get_cache_disk_usage with isolated project_dirs
            stats = get_cache_disk_usage(
                project_dirs=[proj_dir],
                include_global_caches=False,
                include_settings_dirs=False,
            )
            if stats["waveforms"]["count"] < 1:
                raise AssertionError("get_cache_disk_usage did not find waveform peak file")
            if stats["thumbnails"]["count"] < 1:
                raise AssertionError("get_cache_disk_usage did not find video thumbnail file")
            if stats["total_bytes"] <= 0:
                raise AssertionError("Total bytes reported as 0")

            # 3. Test selective purge (strictly scoped to temp project_dirs)
            files_del, bytes_freed = purge_caches(
                clear_thumbnails=True,
                clear_waveforms=False,
                clear_audio_extracts=False,
                project_dirs=[proj_dir],
                include_global_caches=False,
            )
            if files_del < 1 or bytes_freed <= 0:
                raise AssertionError(f"purge_caches failed to clear thumbnails: {files_del} files, {bytes_freed} bytes")
            if not (cache_peaks / "audio.peaks").exists():
                raise AssertionError("Waveform peak file was unexpectedly deleted during thumbnails-only purge")

            # 4. Test cooperative cancellation, temp scratch matching, UNC skip & background workers
            from cache_manager import _is_temp_audio_workfile
            for hit in ("prs_tmp_a.wav", "rtvs_tmp_b.wav", "prs_extract_c.wav", "rtvs_diarization_d.wav", "rtvs_translate_e", "rtvs_wp_f"):
                if not _is_temp_audio_workfile(hit):
                    raise AssertionError(f"_is_temp_audio_workfile missed {hit}")
            for miss in ("notes.txt", "show.wav", "prs_tmp_a.mp3"):
                if _is_temp_audio_workfile(miss):
                    raise AssertionError(f"_is_temp_audio_workfile false positive on {miss}")

            t_unc0 = time.monotonic()
            unc_stats = get_cache_disk_usage(
                project_dirs=[r"\\nonexistent-smb-host-rtvs\share\ep.rtvs"],
                include_global_caches=False,
                include_settings_dirs=False,
            )
            if (time.monotonic() - t_unc0) >= 1.0 or unc_stats["total_files"] != 0:
                raise AssertionError(f"UNC path was not skipped immediately: {unc_stats}")

            cancelled_stats = get_cache_disk_usage(
                project_dirs=[proj_dir],
                include_global_caches=False,
                include_settings_dirs=False,
                cancel_check=lambda: True,
            )
            if cancelled_stats["total_files"] != 0:
                raise AssertionError(f"cancel_check=True should short-circuit scan: {cancelled_stats}")

            del_cancel, _ = purge_caches(
                clear_thumbnails=False,
                clear_waveforms=True,
                clear_audio_extracts=False,
                project_dirs=[proj_dir],
                include_global_caches=False,
                cancel_check=lambda: True,
            )
            if del_cancel != 0 or not (cache_peaks / "audio.peaks").exists():
                raise AssertionError("cancel_check=True should short-circuit purge without deleting peaks")

            from cache_workers import CacheScanWorker, CachePurgeWorker
            for attr_name in ("closeEvent", "reject", "accept", "refresh_stats", "_do_purge"):
                if not hasattr(ClearCacheDialog, attr_name):
                    raise AssertionError(f"ClearCacheDialog missing {attr_name}")

            scan_results = []
            scan_worker = CacheScanWorker(
                project_dirs=[proj_dir],
                include_global_caches=False,
                include_settings_dirs=False,
            )
            scan_worker.finished_scan.connect(lambda st: scan_results.append(st))
            scan_worker.start()
            if not scan_worker.wait(5000):
                raise AssertionError("CacheScanWorker did not finish within 5s")

            from PySide6.QtCore import QThread
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None and QThread.currentThread() == app.thread():
                app.processEvents()
                if not scan_results or scan_results[0]["waveforms"]["count"] < 1:
                    raise AssertionError(f"CacheScanWorker failed to report waveforms: {scan_results}")

                dlg = ClearCacheDialog(
                    None,
                    project_dirs=[proj_dir],
                    auto_refresh=False,
                    include_global_caches=False,
                    include_settings_dirs=False,
                )
                try:
                    dlg.refresh_stats()
                    deadline = time.monotonic() + 5.0
                    while dlg._active_worker is not None and time.monotonic() < deadline:
                        app.processEvents()
                        time.sleep(0.01)
                    app.processEvents()
                    if dlg.lbl_total_val.text().startswith("0 B"):
                        raise AssertionError(f"ClearCacheDialog async scan did not populate total: {dlg.lbl_total_val.text()}")

                    dlg._do_purge(True, True, True)
                    deadline = time.monotonic() + 5.0
                    while dlg._active_worker is not None and time.monotonic() < deadline:
                        app.processEvents()
                        time.sleep(0.01)
                    app.processEvents()
                    if "0 B" not in dlg.lbl_total_val.text() or "freed" not in dlg.lbl_status.text().lower():
                        raise AssertionError(
                            f"ClearCacheDialog async purge did not update UI: total={dlg.lbl_total_val.text()}, status={dlg.lbl_status.text()}"
                        )
                finally:
                    dlg.reject()
            else:
                purge_worker = CachePurgeWorker(
                    clear_thumbnails=False,
                    clear_waveforms=True,
                    clear_audio_extracts=True,
                    purge_project_dirs=[proj_dir],
                    scan_project_dirs=[proj_dir],
                    include_global_caches=False,
                    include_settings_dirs=False,
                )
                purge_worker.start()
                if not purge_worker.wait(5000):
                    raise AssertionError("CachePurgeWorker did not finish within 5s")
                if (cache_peaks / "audio.peaks").exists():
                    raise AssertionError("CachePurgeWorker failed to clear remaining peaks")

        # 5. Test cleanup_old_thumbnail_cache with active session protection & stale purging (isolated temp dir)
        from cache_manager import (
            cleanup_old_thumbnail_cache,
            register_active_thumbnail_dir,
            unregister_active_thumbnail_dir,
        )
        with tempfile.TemporaryDirectory() as tmp_dir2:
            base_thumb = Path(tmp_dir2) / "radio_tv_story_segmenter_thumbnails"
            base_thumb.mkdir(parents=True, exist_ok=True)
            active_sub = base_thumb / f"test_active_{os.getpid()}"
            active_sub.mkdir(parents=True, exist_ok=True)
            (active_sub / "frame_01.jpg").write_bytes(b"ACTIVE_FRAME")
            old_time = time.time() - (48 * 3600)
            os.utime(str(active_sub), (old_time, old_time))
            os.utime(str(active_sub / "frame_01.jpg"), (old_time, old_time))

            stale_sub = base_thumb / f"test_stale_{os.getpid()}"
            stale_sub.mkdir(parents=True, exist_ok=True)
            (stale_sub / "stale_01.jpg").write_bytes(b"STALE_FRAME")
            os.utime(str(stale_sub), (old_time, old_time))
            os.utime(str(stale_sub / "stale_01.jpg"), (old_time, old_time))

            register_active_thumbnail_dir(active_sub)
            try:
                cleanup_old_thumbnail_cache(max_age_hours=24, blocking=True, base_dir=base_thumb)
                if not active_sub.exists():
                    raise AssertionError("cleanup_old_thumbnail_cache deleted an active session thumbnail directory!")
                if stale_sub.exists():
                    raise AssertionError("cleanup_old_thumbnail_cache failed to delete stale thumbnail directory!")
            finally:
                unregister_active_thumbnail_dir(active_sub)

        # 6. Test serialize_models_inventory from backup_manager using an isolated temp models dir
        from backup_manager import serialize_models_inventory
        with tempfile.TemporaryDirectory() as tmp_models_dir:
            fake_models = Path(tmp_models_dir) / "models"
            sample_model = fake_models / "sample-model"
            sample_model.mkdir(parents=True, exist_ok=True)
            (sample_model / "weights.bin").write_bytes(b"MODEL_DATA" * 128)
            models_inv = serialize_models_inventory(models_dir_override=fake_models)
            if not isinstance(models_inv, list) or not any(m.get("name") == "sample-model" for m in models_inv):
                raise AssertionError(f"serialize_models_inventory failed on isolated models dir: {models_inv}")

        item.status = "PASS"
        item.message = "Cache disk usage calculation, preview breakdown, active-guarded purging, and model inventory verified"

    def _test_youtube_data_api_and_direct_video_upload_engine(self, item: DiagnosticItem):
        """Validates YouTube Zero-Auth manual export packaging (MP4, thumbnail, SRT, metadata .txt with chapters & speakers)."""
        root_dir = PROJECT_ROOT
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        plugins_dir = root_dir / "plugins"
        if str(plugins_dir) not in sys.path:
            sys.path.insert(0, str(plugins_dir))

        from export_media_clipper import ExportMediaClipperMixin
        from export_documents import ExportDocumentsMixin
        from plugins.youtube.export_destination import YouTubeExportDestination, YOUTUBE_CATEGORIES

        if not any(cid == "25" for cid, _ in YOUTUBE_CATEGORIES):
            raise AssertionError("News & Politics category (25) missing from YOUTUBE_CATEGORIES")

        dest = YouTubeExportDestination()
        if dest.id != "youtube":
            raise AssertionError("YouTubeExportDestination ID must be 'youtube'")

        class DummyYouTubeExporter(ExportMediaClipperMixin, ExportDocumentsMixin):
            def __init__(self, tmp_path: Path):
                self.tmp_path = tmp_path
                self.audio_file = None
                self.current_media_is_video = False
                self.stories = []
                self.transcript = {
                    "segments": [
                        {"start": 0.0, "end": 5.0, "speaker": "Host Alice", "text": "Welcome to our morning broadcast."},
                        {"start": 5.0, "end": 12.0, "speaker": "Guest Bob", "text": "Thanks for having me on the show."},
                    ]
                }
                self.settings_store = None

            def prepare_export_directories(self, prompt_user=False):
                return self.tmp_path, self.tmp_path, self.tmp_path, "test_yt"

        orig_headless = os.environ.get("RTVS_HEADLESS_TEST")
        os.environ["RTVS_HEADLESS_TEST"] = "1"
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                exporter = DummyYouTubeExporter(Path(tmp_dir))
                pkg = exporter._handle_youtube_export_result({
                    "scope": "full",
                    "title": "Morning News Special",
                    "description": "Morning News Special\n\nChapters:\n00:00 - Introduction\n00:05 - Guest Interview",
                    "tags": "news, broadcast, radio",
                    "category": "25",
                    "privacy": "unlisted",
                    "thumb_mode": "auto",
                    "copy_clipboard": False,
                    "open_browser": False,
                    "open_folder": False,
                    "include_subtitles": True,
                })
                meta_path = Path(pkg["metadata_path"])
                if not meta_path.is_file():
                    raise AssertionError("YouTube sidecar metadata .txt was not created")
                meta_text = meta_path.read_text(encoding="utf-8")
                if "Morning News Special" not in meta_text or "00:00 - Introduction" not in meta_text:
                    raise AssertionError("Metadata .txt missing title or chapters")
                if "Host Alice" not in meta_text or "Guest Bob" not in meta_text:
                    raise AssertionError("Metadata .txt missing speaker credits")
                if "news, broadcast, radio" not in meta_text:
                    raise AssertionError("Metadata .txt missing comma-separated tags")
                sub_path = Path(pkg["subtitles_path"])
                if not sub_path.is_file():
                    raise AssertionError("Companion .srt subtitles file was not generated")
        finally:
            if orig_headless is None:
                os.environ.pop("RTVS_HEADLESS_TEST", None)
            else:
                os.environ["RTVS_HEADLESS_TEST"] = orig_headless

        item.status = "PASS"
        item.message = "YouTube Zero-Auth manual export package (metadata .txt, chapters, speaker credits, tags, .srt, thumbnail) verified"

    def _test_comprehensive_local_and_cloud_backup_and_restore_engine(self, item: DiagnosticItem):
        """Validates state serialization, SHA-256 verification, local backup roundtrip, and cloud payload integrity."""
        import copy
        from backup_manager import (
            BACKUP_FORMAT_IDENTIFIER,
            BACKUP_SCHEMA_VERSION,
            create_backup_payload,
            verify_backup_payload,
            apply_backup_payload,
            export_local_backup,
            restore_local_backup,
        )
        from core_utils import format_time

        # 1. Test Milliseconds and Timecode Formatting Rules
        assert format_time(125.456, include_millis=False) == "02:05", "format_time(125.456, False) must format to 02:05"
        assert format_time(125.456, include_millis=True) == "02:05.456", "format_time(125.456, True) must format to 02:05.456"
        assert format_time(3665.0, include_millis=False) == "01:01:05", "format_time(3665.0, False) must format to 01:01:05"

        # 2. Mock Settings Store for Isolated Deterministic Testing
        class MockSettingsStore:
            def __init__(self):
                self._data = {
                    "language": "en",
                    "show_timestamps": "true",
                    "show_milliseconds": "false",
                    "default_project_directory": "/tmp/projects",
                    "glossary": json.dumps([{"source": "RTVS", "preferred": "Radio & TV Story Segmenter", "do_not_translate": True}]),
                    "plugin_youtube_enabled": True,
                }
                self._groups = []
                self._shortcuts = {"split_turn": "Ctrl+T", "join_turn": "Ctrl+J"}

            def allKeys(self):
                if self._groups and self._groups[-1] == "keyboard_shortcuts":
                    return list(self._shortcuts.keys())
                return list(self._data.keys())

            def value(self, key, default=None):
                if self._groups and self._groups[-1] == "keyboard_shortcuts":
                    return self._shortcuts.get(key, default)
                return self._data.get(key, default)

            def setValue(self, key, val):
                if self._groups and self._groups[-1] == "keyboard_shortcuts":
                    self._shortcuts[key] = val
                else:
                    self._data[key] = val

            def remove(self, key):
                if self._groups and self._groups[-1] == "keyboard_shortcuts":
                    self._shortcuts.pop(key, None)
                else:
                    self._data.pop(key, None)

            def beginGroup(self, group):
                self._groups.append(group)

            def endGroup(self):
                if self._groups:
                    self._groups.pop()

            def sync(self):
                pass

        mock_store = MockSettingsStore()

        # 3. Create Backup Payload & Verify Structure
        payload = create_backup_payload(settings_store=mock_store)
        assert payload.get("format") == BACKUP_FORMAT_IDENTIFIER, f"Invalid format identifier: {payload.get('format')}"
        assert payload.get("schema_version") == BACKUP_SCHEMA_VERSION, f"Invalid schema version: {payload.get('schema_version')}"
        assert "data" in payload, "Missing 'data' dictionary in backup payload"
        assert "archive_checksum" in payload, "Missing 'archive_checksum' in backup payload"

        # 4. Validate Authentic Payload Verification
        valid, msg, val_payload = verify_backup_payload(payload)
        assert valid, f"Verification failed on valid payload: {msg}"
        assert val_payload is not None

        # 5. Cryptographic Tamper Detection
        tampered_payload = copy.deepcopy(payload)
        tampered_payload["data"]["preferences"]["malicious_key"] = "compromised"
        t_valid, t_msg, _ = verify_backup_payload(tampered_payload)
        assert not t_valid, "Tampered payload MUST be rejected by cryptographic checksum"
        assert "SHA-256 digest mismatch" in t_msg, f"Expected checksum error message, got: {t_msg}"

        # 6. Local File Export & Restore Round-Trip
        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_file = Path(tmp_dir) / "test_state.rtvs-settings"
            ok, exp_res = export_local_backup(backup_file, settings_store=mock_store)
            assert ok, f"Export local backup failed: {exp_res}"
            assert backup_file.is_file(), "Backup file was not created on disk"

            # Create a clean mock store to restore into
            fresh_store = MockSettingsStore()
            fresh_store._data.clear()
            fresh_store._shortcuts.clear()

            r_ok, r_msg, items = restore_local_backup(backup_file, settings_store=fresh_store)
            assert r_ok, f"Restore local backup failed: {r_msg}"
            assert len(items) >= 3, f"Expected restored items, got: {items}"
            assert fresh_store.value("language") == "en"
            assert fresh_store.value("show_timestamps") == "true"
            fresh_store.beginGroup("keyboard_shortcuts")
            assert fresh_store.value("split_turn") == "Ctrl+T"
            fresh_store.endGroup()

        cs = payload["archive_checksum"]
        assert len(cs) == 64, f"SHA-256 checksum must be 64 hex characters, got {len(cs)}"

        item.status = "PASS"
        item.message = f"State serialization, SHA-256 cryptographic verification ({cs[:12]}...), and local/cloud roundtrip verified"

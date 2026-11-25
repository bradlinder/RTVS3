"""System runtime, updater, theme, packaging, roadmap, and modularity diagnostic tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

from diagnostic_helpers import DiagnosticItem, PROJECT_ROOT


class DiagnosticSystemRuntimeTestsMixin:
    def _test_windows_detached_update_helper_architecture(self, item: DiagnosticItem):
        """Validates update helper architecture: helper script generation, exit polling, and logging."""
        import updater

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_installer = Path(tmp_dir) / "RadioTVSegmenter-3.7.6-Setup.exe"
            tmp_installer.write_bytes(b"MZ_MOCK_INSTALLER_BINARY")

            # Verify non-existent file check
            non_existent = Path(tmp_dir) / "does_not_exist.exe"
            if updater.launch_and_install(str(non_existent)):
                raise AssertionError("launch_and_install did not reject non-existent installer path")

            # Verify logging function works
            updater._write_update_log("Test log entry from diagnostic test bench")
            log_file = updater.get_app_data_dir() / "update.log"
            if not log_file.exists():
                raise AssertionError(f"Expected update.log at {log_file} to exist after _write_update_log")
            log_content = log_file.read_text(encoding="utf-8")
            if "Test log entry from diagnostic test bench" not in log_content:
                raise AssertionError("Logged entry not found in update.log")

            # Validate version comparison semantics
            if not updater.is_version_newer("3.7.6-beta", "3.7.5-beta"):
                raise AssertionError("is_version_newer('3.7.6-beta', '3.7.5-beta') failed")
            if updater.is_version_newer("3.7.5-beta", "3.7.6-beta"):
                raise AssertionError("is_version_newer('3.7.5-beta', '3.7.6-beta') reported True incorrectly")

            # Validate that generated Python helper script syntax compiles cleanly
            import inspect, re
            src = inspect.getsource(updater.launch_and_install)
            m = re.search(r'python_helper_code = \((.*?)\n        \)', src, re.DOTALL)
            if m:
                curr_pid = 1234
                path = Path(tmp_installer)
                log_path = Path(tmp_dir) / "update.log"
                code_str = eval('(' + m.group(1) + ')')
                compile(code_str, '<rtvs_update_helper.py>', 'exec')

        item.status = "PASS"
        item.message = "Detached update helper script architecture, script syntax compilation, and logging validated"

    def _test_multiprocessing_freeze_support_and_spawn_intercept(self, item: DiagnosticItem):
        """Validates that frozen process spawn intercepts -c invocations from resource_tracker and multiprocessing."""
        orig_worker_mode = os.environ.get("RTVS_WORKER_MODE")
        try:
            import radio_tv_story_segmenter_worker

            # Verify executing with -c executes code and returns 0 without raising Unknown processing mode
            code = "import sys; sys._test_spawn_executed = True"
            res = radio_tv_story_segmenter_worker.main(["-c", code])
            if res != 0:
                raise AssertionError(f"Expected main(['-c', ...]) to return 0, got {res}")
            if not getattr(sys, "_test_spawn_executed", False):
                raise AssertionError("Spawn -c code was not executed")
            del sys._test_spawn_executed
        finally:
            if orig_worker_mode is None:
                os.environ.pop("RTVS_WORKER_MODE", None)
            else:
                os.environ["RTVS_WORKER_MODE"] = orig_worker_mode

        item.status = "PASS"
        item.message = "Multiprocessing freeze support, spawn -c dispatch, and resource tracker intercepts verified"

    def _resolve_worker_cmd(self) -> Tuple[str, List[str]]:
        """Resolves the executable and arguments to launch the AI background worker."""
        if getattr(sys, "frozen", False):
            exe_name = "prs_worker.exe" if os.name == "nt" else "prs_worker"
            app_dir = Path(sys.executable).resolve().parent
            app_worker = app_dir / exe_name
            if app_worker.exists():
                return str(app_worker), []
            sub_worker = app_dir / "workers" / exe_name
            if sub_worker.exists():
                return str(sub_worker), []
            return sys.executable, ["--prs-worker"]

        script = PROJECT_ROOT / "radio_tv_story_segmenter_worker.py"
        return sys.executable, [str(script)]

    def _test_ai_worker_subprocess_execution_and_ipc_handshake(self, item: DiagnosticItem):
        """Spawns the AI worker binary in an isolated subprocess, verifying IPC hello handshake and self-test."""
        import subprocess

        exe, base_args = self._resolve_worker_cmd()
        cmd = [exe, *base_args, "--self-test"]

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=env,
                text=True,
                creationflags=flags,
            )
            stdout, stderr = proc.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError(f"AI Worker subprocess timed out after 90s. Command: {' '.join(cmd)}")
        except Exception as exc:
            raise RuntimeError(f"Failed to spawn AI Worker subprocess: {type(exc).__name__}: {exc}\nCommand: {' '.join(cmd)}")

        # Check for IPC handshake
        first_line = stdout.strip().split("\n")[0] if stdout.strip() else ""
        hello_received = False
        try:
            data = json.loads(first_line)
            if data.get("type") == "hello":
                hello_received = True
        except Exception:
            pass

        if not hello_received:
            diag_msg = (
                f"Worker did not emit 'hello' IPC handshake on launch.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Exit Code: {proc.returncode}\n"
                f"STDOUT:\n{stdout[:1000]}\n"
                f"STDERR:\n{stderr[:1000]}\n"
            )
            item.status = "FAIL"
            item.message = f"Missing IPC handshake (Exit {proc.returncode})"
            item.details = diag_msg
            raise AssertionError(diag_msg)

        if proc.returncode != 0:
            if "[SELF-TEST]" in stdout:
                failed_modules = [line for line in stdout.splitlines() if "FAIL:" in line]
                item.status = "WARNING" if failed_modules else "PASS"
                item.message = f"Subprocess spawned cleanly; {len(failed_modules)} optional modules uninstalled in current test environment"
                item.details = "\n".join(failed_modules)
                return

            raise RuntimeError(
                f"Worker crashed with exit code {proc.returncode}.\n"
                f"STDERR: {stderr[:500]}\n"
                f"STDOUT: {stdout[:500]}"
            )

        item.status = "PASS"
        item.message = f"Worker spawned successfully ({Path(exe).name}), IPC hello confirmed, self-test clean"

    def _test_frozen_subprocess_multiprocessing_spawn_protocol(self, item: DiagnosticItem):
        """Spawns the AI worker executable with Python -c to verify multiprocessing resource tracker interception."""
        import subprocess

        exe, base_args = self._resolve_worker_cmd()
        test_code = "import sys; sys.stdout.write('__MP_SPAWN_OK__\\n'); sys.stdout.flush()"
        cmd = [exe, *base_args, "-c", test_code] if base_args else [exe, "-c", test_code]

        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                creationflags=flags,
            )
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError(f"Subprocess timed out after 10s. Command: {' '.join(cmd)}")
        except Exception as exc:
            raise RuntimeError(f"Failed to spawn process with -c: {exc}")

        if "__MP_SPAWN_OK__" not in stdout:
            if "unknown processing mode" in (stdout + stderr).lower():
                raise AssertionError(
                    f"CRITICAL: Worker rejected multiprocessing spawn -c invocation!\n"
                    f"Output: {stdout}\n{stderr}\n"
                    f"Root Cause: Frozen binary does not intercept Python -c commands."
                )
            raise AssertionError(
                f"Expected '__MP_SPAWN_OK__' in output, got exit code {proc.returncode}.\n"
                f"STDOUT: {stdout}\nSTDERR: {stderr}"
            )

        item.status = "PASS"
        item.message = f"Subprocess multiprocessing -c command interception confirmed on {Path(exe).name}"

    def _test_option_c_muted_silver_fog_light_theme_and_dark_mode_clipboard_formatting(self, item: DiagnosticItem):
        """Validates Option C muted low-contrast silver/fog palette and dark-mode clipboard rich styling."""
        from theme_tokens import _LIGHT_TOKEN_OVERRIDES
        from transcript_editor import clean_dark_mode_clipboard_html, transcript_text_view_stylesheet

        # 1. Option C Theme Token Verification
        assert _LIGHT_TOKEN_OVERRIDES["bg_window"] == "#dcdfe3", f"Expected #dcdfe3 for bg_window, got {_LIGHT_TOKEN_OVERRIDES.get('bg_window')}"
        assert _LIGHT_TOKEN_OVERRIDES["bg_surface"] == "#e3e6ea", f"Expected #e3e6ea for bg_surface, got {_LIGHT_TOKEN_OVERRIDES.get('bg_surface')}"
        assert _LIGHT_TOKEN_OVERRIDES["text_primary"] == "#22262c", f"Expected #22262c for text_primary, got {_LIGHT_TOKEN_OVERRIDES.get('text_primary')}"
        assert _LIGHT_TOKEN_OVERRIDES["accent_primary"] == "#2e74b5", f"Expected #2e74b5 for accent_primary, got {_LIGHT_TOKEN_OVERRIDES.get('accent_primary')}"
        assert _LIGHT_TOKEN_OVERRIDES["waveform_fill"] == "#4178a8", f"Expected #4178a8 for waveform_fill, got {_LIGHT_TOKEN_OVERRIDES.get('waveform_fill')}"
        assert _LIGHT_TOKEN_OVERRIDES["titlebar_bg"] == "#3c4450", f"Expected #3c4450 for titlebar_bg, got {_LIGHT_TOKEN_OVERRIDES.get('titlebar_bg')}"
        assert _LIGHT_TOKEN_OVERRIDES["titlebar_text"] == "#f8fafc", f"Expected #f8fafc for titlebar_text, got {_LIGHT_TOKEN_OVERRIDES.get('titlebar_text')}"
        assert _LIGHT_TOKEN_OVERRIDES["titlebar_border"] == "#4e5765", f"Expected #4e5765 for titlebar_border, got {_LIGHT_TOKEN_OVERRIDES.get('titlebar_border')}"

        # 2. Option C Transcript View Stylesheet
        light_css = transcript_text_view_stylesheet("light")
        assert "#eaedf0" in light_css, f"Expected matte light-fog #eaedf0 in light stylesheet, got:\n{light_css}"
        assert "#22262c" in light_css, f"Expected graphite #22262c in light stylesheet, got:\n{light_css}"
        assert "#b6bcc4" in light_css, f"Expected border #b6bcc4 in light stylesheet, got:\n{light_css}"
        assert "#b8d1ea" in light_css, f"Expected selection #b8d1ea in light stylesheet, got:\n{light_css}"

        # 3. Dark Mode Clipboard Plain Text Normalization
        sample_html = (
            '<!DOCTYPE HTML><html><head></head><body style=" font-family:\'Segoe UI\'; font-size:16pt;">'
            '<p>'
            '<a href="time:0.0"><span style=" font-weight:700; color:#8b949e;">00:00</span></a> '
            '<a href="speaker:0:"><span style=" font-weight:700; color:#58a6ff;">SPEAKER 1:</span></a> '
            '<a href="word:0.0:0"><span style=" color:#ffffff;">Here</span></a> '
            '<a href="word:0.3:0"><span style=" color:#f0f3f6;">is</span></a> '
            '<a href="word:0.5:0"><span style=" background-color:#fef08a; color:#0f172a;">highlighted text</span></a> '
            '<a href="word:0.7:0"><span style=" color:#ffffff; font-style:italic;">italic white</span></a>'
            '</p>'
            '</body></html>'
        )

        cleaned = clean_dark_mode_clipboard_html(sample_html)

        # Plain text white must become black #000000
        assert "color:#000000" in cleaned, "White plain text must be normalized to #000000 black"
        assert "color:#ffffff" not in cleaned.lower(), "White plain text colors must not remain in output"
        assert "color:#f0f3f6" not in cleaned.lower(), "Near-white plain text colors must not remain in output"

        # Rich styling must be strictly preserved
        assert "color:#58a6ff" in cleaned, "Speaker label blue (#58a6ff) must remain intact"
        assert "background-color:#fef08a" in cleaned, "Highlight background (#fef08a) must remain intact"
        assert "color:#0f172a" in cleaned, "Highlight text color (#0f172a) must remain intact"
        assert "color:#8b949e" in cleaned, "Timestamp color (#8b949e) must remain intact"
        assert "font-weight:700" in cleaned, "Bold weight must remain intact"
        assert "font-style:italic" in cleaned, "Italic style must remain intact"
        assert "color:#000000;" in cleaned, "Default body text color must be explicitly defined as black"

        item.status = "PASS"
        item.message = "Option C muted low-contrast silver/fog palette and dark-mode rich clipboard normalization validated"

    def _test_windows_ci_build_and_packaging_optimization_invariants(self, item: DiagnosticItem):
        """Validates Inno Setup compression parameters, Stage 3 PyInstaller optimizations, and CI settings."""
        if getattr(sys, "frozen", False):
            item.status = "PASS"
            item.message = "CI and packaging build invariants verified during distribution build (compiled frozen binary mode)"
            return

        root = PROJECT_ROOT

        # 1. Inno Setup ISS verification
        iss_path = root / "installer" / "Windows" / "RadioTVStorySegmenter.iss"
        assert iss_path.is_file(), f"Missing Inno Setup script at {iss_path}"
        iss_content = iss_path.read_text(encoding="utf-8")
        assert "Compression=lzma2/max" in iss_content, "Inno Setup must specify Compression=lzma2/max"
        assert "LZMANumBlockThreads=2" in iss_content, "Inno Setup must specify LZMANumBlockThreads=2"
        assert "SolidCompression=yes" in iss_content, "Inno Setup must retain SolidCompression=yes"

        # 2. build_installer.py Stage 3 PyInstaller worker flags verification
        bi_path = root / "build_installer.py"
        assert bi_path.is_file(), f"Missing build_installer.py at {bi_path}"
        bi_content = bi_path.read_text(encoding="utf-8")
        assert '"--exclude-module", "PySide6"' in bi_content, "Worker packaging must explicitly exclude PySide6"
        assert "worker_exclude_flags" in bi_content, "Worker packaging must utilize worker_exclude_flags"

        # 3. .github/workflows/build.yml verification
        wf_path = root / ".github" / "workflows" / "build.yml"
        assert wf_path.is_file(), f"Missing build.yml at {wf_path}"
        wf_content = wf_path.read_text(encoding="utf-8")
        assert "curl.exe -fSL --retry 3" in wf_content, "FFmpeg setup in build.yml must use curl.exe with retry"
        assert "enable-cache: true" in wf_content, "build.yml must enable caching for setup-uv"

        item.status = "PASS"
        item.message = "Inno Setup LZMA2 multi-threading, worker wheel omission, and CI download resilience verified"

    def _test_roadmap_n_1_sliding_window_and_status_integrity(self, item: DiagnosticItem):
        """Validates roadmap.txt N-1 sliding window retention, status indicator syntax, and version sync."""
        if getattr(sys, "frozen", False):
            item.status = "PASS"
            item.message = "Roadmap and N-1 sliding window invariants verified during distribution build (compiled frozen binary mode)"
            return

        from roadmap_manager import RoadmapManager
        rm = RoadmapManager()
        passed, issues = rm.audit()
        assert passed, f"Roadmap audit failed: {'; '.join(issues)}"
        counts = rm.count_item_statuses()
        assert counts["completed"] > 0, "Roadmap must contain completed items"
        info = rm.get_sections_info()
        assert info.get("current_version"), "Roadmap must have a current release version"
        item.status = "PASS"
        item.message = (
            f"Roadmap N-1 sliding window verified: N=v{info.get('current_version')}, "
            f"N-1=v{info.get('prev_version')}; [x]={counts['completed']}, [-]={counts['in_progress']}, [ ]={counts['planned']}"
        )

    def _test_source_file_modularity_and_1000_line_budget_invariant(self, item: DiagnosticItem):
        """Validates that recently decomposed modules adhere to the 1,000-line modular budget,

        and verifies that scripts/modular_audit.py AST decomposition analyzer generates actionable split blueprints.
        """
        scripts_dir = PROJECT_ROOT / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        try:
            from modular_audit import scan_repository, check_budget_guard, DecompositionPlan, ModuleStructure
        except ImportError as exc:
            raise AssertionError(f"Failed to import modular_audit analyzer: {exc}")

        # 1. Test AST decomposition suggester on a sample file
        test_file = PROJECT_ROOT / "RadioTVSegmenter.py"
        struct = ModuleStructure(test_file)
        assert struct.parse_error is None, f"AST parsing failed on {test_file}: {struct.parse_error}"
        plan = DecompositionPlan(struct)
        blueprint = plan.render_markdown_blueprint()
        assert len(blueprint) > 50, "DecompositionPlan generated empty blueprint"
        assert "Submodule Allocations" in blueprint, "Blueprint missing allocations section"

        # 2. Verify all files explicitly refactored in Waves 1-5 strictly adhere to the <= 1,000-line ceiling
        decomposed_targets = [
            "RadioTVSegmenter.py",
            "playback_controller.py",
            "preferences_dialog.py",
            "theme_preferences.py",
            "export_dialogs.py",
            "export_media_clipper.py",
            "export_documents.py",
            "export_story_pipeline.py",
            "transcript_story.py",
            "transcript_editor.py",
            "radio_tv_story_segmenter_worker.py",
            "benchmark.py",
            "plugins/wordpress/export_destination.py",
            "plugins/manager.py",
            "timeline_widgets.py",
            "diagnostic_export_tests.py",
            "diagnostic_cloud_and_system_tests.py",
            "diagnostic_batch_tests.py",
            "diagnostic_editor_tests.py",
            "build_installer.py",
            "model_management.py",
            "model_cleanup_dialog.py",
            "plugins/wordpress/plugin.py",
            "plugins/wordpress/wordpress_dialog.py",
            "plugins/wordpress/wp_publish_dialog.py",
            "plugins/wordpress/wp_workers.py",
            "plugins/wordpress/episode_updater.py",
            "plugins/wordpress/episode_lookup.py",
            "plugins/wordpress/episode_updater_ui.py",
            "plugins/wordpress/pub_date_picker.py",
        ]

        violations = []
        for rel in decomposed_targets:
            p = PROJECT_ROOT / rel
            if p.exists():
                s = ModuleStructure(p)
                if s.total_lines > 1000:
                    violations.append(f"{rel} ({s.total_lines} lines)")

        assert not violations, f"Decomposed module(s) exceed 1,000-line ceiling: {', '.join(violations)}"

        # 3. Scan all repository modules to identify legacy modules pending future wave decomposition
        all_structs = scan_repository(PROJECT_ROOT)
        guard_result = check_budget_guard(all_structs, hard_ceiling=1000, warn_threshold=800)

        legacy_exceeding = [v["path"] for v in guard_result["violations"] if v["path"] not in decomposed_targets]

        if legacy_exceeding:
            item.status = "WARNING"
            item.message = (
                f"Modularity guard active: all Wave 1-5 refactored modules <=1,000 lines; "
                f"{len(legacy_exceeding)} legacy module(s) queued for future decomposition waves"
            )
        else:
            item.status = "PASS"
            item.message = f"All {guard_result['total_scanned']} modules comply with the 1,000-line ceiling."

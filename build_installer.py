#!/usr/bin/env python3
"""Build the installable Radio & TV Segmenter application with PyInstaller.

Run this script on the target operating system (Windows installers must be built on
Windows, macOS ones on macOS -- PyInstaller does not cross-compile). It intentionally
refuses to produce a release package unless FFmpeg and ffprobe are available at build time,
because the finished application is expected to carry its own media runtime rather than
require end users to install FFmpeg.

This build is CPU-only by design (see installer/requirements.txt): GPU acceleration is an optional,
separately-downloaded component the user can enable from Settings after installing,
not something bundled into the installer.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_NAME = "RadioTVSegmenter"
ENTRY_POINT = "RadioTVSegmenter.py"

try:
    from prs_shared import APP_DISPLAY_NAME, PROJECT_VERSION
    print(f"[BUILD] Loaded metadata from prs_shared: APP_DISPLAY_NAME='{APP_DISPLAY_NAME}', PROJECT_VERSION='{PROJECT_VERSION}'")
except ImportError as e:
    print(f"[BUILD] Warning: Could not import prs_shared ({e}), using fallback values")
    APP_DISPLAY_NAME = "Radio & TV Segmenter"
    PROJECT_VERSION = "3.10.23-beta"
except Exception as e:
    print(f"[BUILD] Unexpected error importing prs_shared: {type(e).__name__}: {e}")
    raise

# Ensure PROJECT_VERSION is clean and free of duplicate dots
PROJECT_VERSION = re.sub(r"\.+", ".", str(PROJECT_VERSION).strip().lstrip("v"))

# Allow environment variable override if set by CI or build runner
if os.environ.get("BUILD_VERSION"):
    PROJECT_VERSION = os.environ.get("BUILD_VERSION").strip().lstrip("v")
    PROJECT_VERSION = re.sub(r"\.+", ".", PROJECT_VERSION)
    print(f"[BUILD] Overriding PROJECT_VERSION with BUILD_VERSION environment variable: '{PROJECT_VERSION}'")

from installer.build_tools.config import (
    COLLECT_ALL_PACKAGES,
    COPY_METADATA_PACKAGES,
    HIDDEN_IMPORTS,
    PYSIDE6_EXCLUDES,
    PYSIDE6_USED_SUBMODULES,
    TEST_AND_BENCHMARK_EXCLUDES,
    UV_URLS,
    UV_VERSION,
    parse_build_args,
)
from installer.build_tools.env_checks import (
    check_cpu_only_torch,
    exe_name,
    find_tool as _find_tool,
    run as _run,
    torch_windows_binary_flags,
)
from installer.build_tools.packaging import (
    compile_windows_installer as _compile_windows_installer,
    package_plugins as _package_plugins,
    provision_optional_runtime_tools as _provision_optional_runtime_tools,
    prune_unneeded_bundled_files,
    sync_installer_scripts as _sync_installer_scripts,
)


def find_tool(name: str) -> str:
    return _find_tool(name, root_dir=ROOT)


def run(cmd: list[str]) -> None:
    _run(cmd, cwd=ROOT)


def provision_optional_runtime_tools(app_root: Path) -> None:
    _provision_optional_runtime_tools(
        app_root,
        build_dir=BUILD,
        uv_version=UV_VERSION,
        uv_urls=UV_URLS,
    )


def sync_installer_scripts(project_version: str) -> None:
    _sync_installer_scripts(project_version, root_dir=ROOT)


def compile_windows_installer(project_version: str) -> bool:
    return _compile_windows_installer(project_version, root_dir=ROOT)


def package_plugins(
    app_root: Path | None = None,
    include_wp: bool = True,
    include_yt: bool = True,
    include_tr: bool = True,
) -> list[Path]:
    """Package plugins into standalone .zip release artifacts in dist/plugins/
    and optionally bundle them into app_root/plugins/.
    """
    return _package_plugins(
        app_root=app_root,
        include_wp=include_wp,
        include_yt=include_yt,
        include_tr=include_tr,
        root_dir=ROOT,
        dist_dir=DIST,
        project_version=PROJECT_VERSION,
    )


def main() -> None:
    prs_shared_file = ROOT / "prs_shared.py"
    if not prs_shared_file.exists():
        raise SystemExit(
            f"[FATAL BUILD ERROR] Required file not found: {prs_shared_file}\n"
            "This file must exist in the project root and contain PROJECT_VERSION and APP_DISPLAY_NAME."
        )
    args = parse_build_args()
    if getattr(args, "version", None):
        global PROJECT_VERSION
        PROJECT_VERSION = str(args.version).strip().lstrip("v")
        print(f"[BUILD] Overriding PROJECT_VERSION with CLI --version argument: '{PROJECT_VERSION}'")
    sync_installer_scripts(PROJECT_VERSION)
    target = str(args.target).strip().lower()
    is_plugins_only = target in ("plugins", "plugins only")
    is_core_only = target in ("core", "core app only")
    is_all = not is_plugins_only and not is_core_only

    if is_plugins_only:
        print("[BUILD] Target: 'Plugins Only'. Packaging selected plugins...")
        DIST.mkdir(parents=True, exist_ok=True)
        zips = package_plugins(
            app_root=None,
            include_wp=args.plugin_wordpress,
            include_yt=args.plugin_youtube,
            include_tr=args.plugin_translation,
        )
        print(f"\n[SUCCESS] Packaged {len(zips)} plugins into dist/plugins/:")
        for z in zips:
            print(f"  - {z.name}")
        return

    if sys.version_info[:2] != (3, 12):
        raise SystemExit("ERROR: Build with Python 3.12. The AI dependency set is not guaranteed to support other Python versions.")
    if not shutil.which("pyinstaller"):
        raise SystemExit("ERROR: PyInstaller is not installed. Install requirements-build.txt first.")

    ffmpeg = find_tool("ffmpeg")
    ffprobe = find_tool("ffprobe")
    check_cpu_only_torch()

    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)

    pyside6_flags = []
    for module in PYSIDE6_USED_SUBMODULES:
        pyside6_flags += ["--collect-submodules", f"PySide6.{module}"]

    torch_binary_flags = torch_windows_binary_flags()

    general_excludes = [
        *PYSIDE6_EXCLUDES,
        *TEST_AND_BENCHMARK_EXCLUDES,
    ]
    exclude_flags = []
    for module in general_excludes:
        exclude_flags += ["--exclude-module", module]

    collect_flags = []
    for pkg in COLLECT_ALL_PACKAGES:
        if importlib.util.find_spec(pkg):
            collect_flags.extend(["--collect-all", pkg])
        else:
            print(f"[BUILD] Note: package '{pkg}' not installed in build environment; skipping --collect-all.")
    for meta in COPY_METADATA_PACKAGES:
        found_name = None
        for candidate in (meta, meta.replace("_", "-"), meta.replace("-", "_")):
            try:
                importlib.metadata.distribution(candidate)
                found_name = candidate
                break
            except Exception:
                continue
        if found_name:
            collect_flags.extend(["--copy-metadata", found_name])
        else:
            print(f"[BUILD] Note: distribution metadata '{meta}' not found in build environment; skipping --copy-metadata.")
    for hidden_mod in HIDDEN_IMPORTS:
        collect_flags.extend(["--hidden-import", hidden_mod])

    icon_file = ROOT / "resources" / ("icon.ico" if sys.platform == "win32" else "icon.png")
    icon_flags = ["--icon", str(icon_file)] if icon_file.exists() else []

    doc_flags = []
    for doc in ("NOTICES.txt", "LICENSE"):
        doc_file = ROOT / doc
        if doc_file.exists():
            doc_flags.extend(["--add-data", f"{doc_file}{os.pathsep}."])
    if (ROOT / "docs").exists():
        doc_flags.extend(["--add-data", f"{ROOT / 'docs'}{os.pathsep}docs"])
    if (ROOT / "scripts" / "reaper").exists():
        doc_flags.extend(["--add-data", f"{ROOT / 'scripts' / 'reaper'}{os.pathsep}scripts/reaper"])

    runtime_hook = ROOT / "installer" / "pyinstaller" / "torch_dll_hook.py"

    print("\n" + "=" * 70, flush=True)
    print("[BUILD STAGE 1/5] Compiling primary application with PyInstaller (GUI & AI runtime)...", flush=True)
    print("=" * 70 + "\n", flush=True)
    run([
        "pyinstaller", "--noconfirm", "--onedir", "--windowed", "--noupx",
        "--log-level", "INFO",
        "--name", APP_NAME,
        "--runtime-hook", str(runtime_hook),
        *torch_binary_flags,
        *icon_flags,
        *doc_flags,
        *pyside6_flags,
        *exclude_flags,
        *collect_flags,
        str(ROOT / ENTRY_POINT),
    ])

    if sys.platform == "darwin":
        app_root = DIST / f"{APP_NAME}.app" / "Contents" / "MacOS"
        plist_path = DIST / f"{APP_NAME}.app" / "Contents" / "Info.plist"
        if plist_path.exists():
            try:
                with open(plist_path, "rb") as fp:
                    pl = plistlib.load(fp)
                pl["CFBundleDocumentTypes"] = [
                    {
                        "CFBundleTypeName": "Radio & TV Segmenter Project",
                        "CFBundleTypeRole": "Editor",
                        "CFBundleTypeExtensions": ["rtvs", "json"],
                        "CFBundleTypeIconFile": "icon.icns",
                        "LSHandlerRank": "Owner",
                    }
                ]
                with open(plist_path, "wb") as fp:
                    plistlib.dump(pl, fp)
                print(f"[BUILD] Registered .rtvs file association in {plist_path}")
            except Exception as e:
                print(f"[BUILD WARNING] Could not update Info.plist document types: {e}")
    else:
        app_root = DIST / APP_NAME

    runtime_bin = app_root / "runtime" / "bin"
    workers_dir = app_root / "workers"
    resources_dir = app_root / "resources"
    runtime_bin.mkdir(parents=True, exist_ok=True)
    workers_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    if (ROOT / "resources").exists():
        for res in (ROOT / "resources").iterdir():
            if res.is_file():
                shutil.copy2(res, resources_dir / res.name)

    samples_dir = app_root / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    if (ROOT / "samples").exists():
        for s_file in (ROOT / "samples").iterdir():
            if s_file.is_file():
                shutil.copy2(s_file, samples_dir / s_file.name)

    shutil.copy2(ffmpeg, runtime_bin / Path(ffmpeg).name)
    shutil.copy2(ffprobe, runtime_bin / Path(ffprobe).name)

    for doc in ("NOTICES.txt", "LICENSE"):
        doc_file = ROOT / doc
        if doc_file.exists():
            shutil.copy2(doc_file, app_root / doc)
            if sys.platform == "darwin":
                resources_bundle = app_root.parent / "Resources"
                resources_bundle.mkdir(parents=True, exist_ok=True)
                shutil.copy2(doc_file, resources_bundle / doc)

    # Bundle documentation and user guides directly into the application directory
    docs_source = ROOT / "docs"
    docs_dest = app_root / "docs"
    if docs_source.exists():
        shutil.copytree(docs_source, docs_dest, dirs_exist_ok=True)
        print(f"[BUILD] Bundled documentation & user guides into {docs_dest}")
        if sys.platform == "darwin":
            resources_docs = app_root.parent / "Resources" / "docs"
            shutil.copytree(docs_source, resources_docs, dirs_exist_ok=True)

    # Bundle REAPER ReaScript Lua companion scripts into the application directory
    reaper_scripts_source = ROOT / "scripts" / "reaper"
    reaper_scripts_dest = app_root / "scripts" / "reaper"
    if reaper_scripts_source.exists():
        shutil.copytree(reaper_scripts_source, reaper_scripts_dest, dirs_exist_ok=True)
        print(f"[BUILD] Bundled REAPER companion Lua scripts into {reaper_scripts_dest}")
        if sys.platform == "darwin":
            resources_reaper = app_root.parent / "Resources" / "scripts" / "reaper"
            shutil.copytree(reaper_scripts_source, resources_reaper, dirs_exist_ok=True)

    # Bundle plugins based on selected build target and options
    print("\n" + "=" * 70, flush=True)
    print("[BUILD STAGE 2/5] Bundling runtime tools, resources, and selected plugins...", flush=True)
    print("=" * 70 + "\n", flush=True)
    if is_all:
        print("[BUILD] Target: 'Core App + Selected Plugins'. Bundling selected plugins...")
        package_plugins(
            app_root=app_root,
            include_wp=args.plugin_wordpress,
            include_yt=args.plugin_youtube,
            include_tr=args.plugin_translation,
        )
    elif is_core_only:
        print("[BUILD] Target: 'Core App Only'. Omitting bundled plugins from installer.")

    # Build dedicated worker binary sharing the same runtime
    print("\n" + "=" * 70, flush=True)
    print("[BUILD STAGE 3/5] Compiling dedicated AI background worker (prs_worker)...", flush=True)
    print("=" * 70 + "\n", flush=True)
    worker_target_exe = exe_name("prs_worker")
    worker_dest = app_root / worker_target_exe
    worker_in_subdir = workers_dir / worker_target_exe

    worker_build = BUILD / "worker_entry"
    worker_dist = BUILD / "worker_dist"
    shutil.rmtree(worker_build, ignore_errors=True)
    shutil.rmtree(worker_dist, ignore_errors=True)

    worker_exclude_flags = [
        *exclude_flags,
        "--exclude-module", "PySide6",
        "--exclude-module", "PySide6.QtCore",
        "--exclude-module", "PySide6.QtGui",
        "--exclude-module", "PySide6.QtWidgets",
        "--exclude-module", "PySide6.QtNetwork",
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtMultimediaWidgets",
    ]

    run([
        "pyinstaller", "--noconfirm", "--onedir", "--console", "--noupx",
        "--log-level", "INFO",
        "--name", "prs_worker",
        "--distpath", str(worker_dist),
        "--workpath", str(worker_build),
        "--runtime-hook", str(runtime_hook),
        *icon_flags,
        *worker_exclude_flags,
        str(ROOT / "radio_tv_story_segmenter_worker.py"),
    ])

    # Copy the compiled standalone prs_worker binary into app_root
    generated_worker = worker_dist / "prs_worker" / worker_target_exe
    if generated_worker.exists():
        shutil.copy2(generated_worker, worker_dest)
        if sys.platform != "win32":
            try:
                if worker_in_subdir.exists() or worker_in_subdir.is_symlink():
                    worker_in_subdir.unlink()
                worker_in_subdir.symlink_to(f"../{worker_target_exe}")
            except Exception:
                pass
        else:
            if worker_in_subdir.exists():
                try:
                    worker_in_subdir.unlink()
                except Exception:
                    pass

    # Ensure worker python source is available for isolated virtual environments (e.g. GPU acceleration)
    worker_py_src = ROOT / "radio_tv_story_segmenter_worker.py"
    if worker_py_src.exists():
        shutil.copy2(worker_py_src, workers_dir / "radio_tv_story_segmenter_worker.py")
        shutil.copy2(worker_py_src, app_root / "radio_tv_story_segmenter_worker.py")
    shutil.rmtree(worker_dist, ignore_errors=True)

    print("\n" + "=" * 70, flush=True)
    print("[BUILD STAGE 4/5] Provisioning optional runtime tools & pruning asset bloat...", flush=True)
    print("=" * 70 + "\n", flush=True)
    if getattr(args, "bundle_uv", False):
        provision_optional_runtime_tools(app_root)
    else:
        print("[BUILD] Skipping pre-bundled uv binary (saves ~50MB; runtime_manager fetches on-demand when optional runtimes are requested).")
        shutil.rmtree(app_root / "optional_runtime", ignore_errors=True)
    prune_unneeded_bundled_files(app_root)

    print("\n" + "=" * 70, flush=True)
    print("[BUILD STAGE 5/5] Running frozen AI runtime smoke tests...", flush=True)
    print("=" * 70 + "\n", flush=True)
    print("[BUILD] Running frozen AI worker self-test...")
    test_target = worker_dest if worker_dest.exists() else worker_in_subdir
    smoke = subprocess.run(
        [str(test_target), "--self-test"],
        cwd=app_root, capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if smoke.stdout:
        print(smoke.stdout.strip())
    if smoke.stderr:
        print(smoke.stderr.strip())
    if smoke.returncode != 0:
        raise SystemExit(
            "[FATAL BUILD ERROR] Frozen AI worker self-test failed. "
            "The installer was NOT produced. See the worker diagnostics above."
        )

    print("[BUILD] Running frozen GUI AI self-test...")
    main_test_file = app_root / "ai_self_test.txt"
    main_smoke = subprocess.run(
        [str(app_root / exe_name(APP_NAME)), "--self-test"],
        cwd=app_root, capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if main_test_file.exists():
        print(main_test_file.read_text(encoding="utf-8").strip())
        main_test_file.unlink(missing_ok=True)
    if main_smoke.returncode != 0:
        raise SystemExit(
            "[FATAL BUILD ERROR] Frozen GUI AI self-test failed. "
            "The installer was NOT produced."
        )

    if os.name != "nt":
        for item in runtime_bin.iterdir():
            item.chmod(0o755)
        if worker_dest.exists():
            worker_dest.chmod(0o755)
        if worker_in_subdir.exists() and not worker_in_subdir.is_symlink():
            worker_in_subdir.chmod(0o755)

    print(f"\n[BUILD] {APP_DISPLAY_NAME} v{PROJECT_VERSION} build complete: {app_root.parent if sys.platform == 'darwin' else app_root}")

    if not getattr(args, "no_installer", False) and (sys.platform == "win32" or getattr(args, "installer", False)):
        compile_windows_installer(PROJECT_VERSION)


if __name__ == "__main__":
    main()

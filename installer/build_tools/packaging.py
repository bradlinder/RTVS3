"""Bundle pruning, plugin archive packaging, runtime tools, and Windows Inno Setup helpers."""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from installer.build_tools.config import UV_URLS, UV_VERSION

_DEFAULT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DIST = _DEFAULT_ROOT / "dist"
_DEFAULT_BUILD = _DEFAULT_ROOT / "build"


def provision_optional_runtime_tools(
    app_root: Path,
    build_dir: Path = _DEFAULT_BUILD,
    uv_version: str = UV_VERSION,
    uv_urls: dict[str, str] = UV_URLS,
) -> None:
    """Bundle standalone uv binary into optional_runtime/ when explicitly requested."""
    dest_dir = app_root / "optional_runtime"
    dest_dir.mkdir(parents=True, exist_ok=True)
    binary_name = "uv.exe" if sys.platform == "win32" else "uv"
    uv_dest = dest_dir / binary_name
    if uv_dest.exists():
        if sys.platform != "win32":
            try:
                uv_dest.chmod(uv_dest.stat().st_mode | 0o755)
            except Exception:
                pass
        return

    # Check if uv is already in PATH on the host (e.g. installed by setup-uv in CI)
    host_uv = shutil.which("uv") or shutil.which("uv.exe")
    if host_uv and Path(host_uv).is_file():
        try:
            shutil.copy2(host_uv, uv_dest)
            if sys.platform != "win32":
                try:
                    uv_dest.chmod(0o755)
                except Exception:
                    pass
            print(f"[BUILD] Bundled host uv from {host_uv} into {dest_dir}.")
            return
        except Exception as exc:
            print(f"[BUILD] Warning copying host uv: {exc}")

    # Determine platform architecture key
    machine = (os.environ.get("PROCESSOR_ARCHITECTURE", "") or platform.machine()).lower()
    is_arm = "arm" in machine or "aarch64" in machine
    if sys.platform == "win32":
        arch_key = "win32-arm64" if is_arm else "win32-x86_64"
    elif sys.platform == "darwin":
        arch_key = "darwin-arm64" if is_arm else "darwin-x86_64"
    else:
        arch_key = "linux-aarch64" if is_arm else "linux-x86_64"

    url = uv_urls.get(arch_key)
    if not url:
        print(f"[BUILD] Warning: No uv download URL found for platform key '{arch_key}'.")
        return

    build_dir.mkdir(parents=True, exist_ok=True)
    archive_ext = ".zip" if url.endswith(".zip") else ".tar.gz"
    archive = build_dir / f"uv{archive_ext}"
    print(f"[BUILD] Downloading uv {uv_version} ({arch_key}) for optional runtime provisioning...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Radio-TV-Story-Segmenter-Build"})
        with urllib.request.urlopen(req) as resp, archive.open("wb") as out:
            shutil.copyfileobj(resp, out)
        if archive_ext == ".zip":
            with zipfile.ZipFile(archive) as zf:
                member = next((n for n in zf.namelist() if n.lower().endswith("/" + binary_name) or n.lower() == binary_name), None)
                if not member:
                    raise SystemExit(f"ERROR: The downloaded uv archive did not contain {binary_name}.")
                with zf.open(member) as src, uv_dest.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        else:
            with tarfile.open(archive, "r:gz") as tf:
                member = next((m for m in tf.getmembers() if m.name.endswith("/" + binary_name) or m.name == binary_name), None)
                if not member:
                    raise SystemExit(f"ERROR: The downloaded uv archive did not contain {binary_name}.")
                extracted = tf.extractfile(member)
                if extracted:
                    with extracted as src, uv_dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)

        if sys.platform != "win32":
            try:
                uv_dest.chmod(0o755)
            except Exception:
                pass
        print(f"[BUILD] Successfully bundled {binary_name} into {dest_dir}.")
    except Exception as exc:
        print(f"[BUILD] Warning: Could not download or extract uv: {exc}")
    finally:
        archive.unlink(missing_ok=True)


def prune_unneeded_bundled_files(app_root: Path) -> None:
    """Strip CUDA leftovers, development headers, test suites, and software OpenGL bloat."""
    print("[BUILD] Pruning non-runtime assets and symbol bloat from bundle...")
    main_internal = app_root / "_internal"
    internal_dirs = [main_internal] if main_internal.exists() else [app_root]

    cuda_purged = 0
    cuda_lib_prefixes = (
        "libnvrtc", "nvrtc", "libcudnn", "cudnn",
        "libcublas", "cublas", "libcusolver", "cusolver", "libcurand", "curand",
        "libcufft", "cufft", "libnccl", "nccl", "libnvJitLink", "libnvblas",
        "nvjitlink", "cusparse", "nvjpeg",
    )
    for base in internal_dirs:
        if not base.exists():
            continue
        for nvidia_dir in base.glob("**/nvidia"):
            if nvidia_dir.is_dir() and "workers" not in nvidia_dir.parts:
                print(f"[BUILD] Purging CUDA package directory: {nvidia_dir}")
                shutil.rmtree(nvidia_dir, ignore_errors=True)
                cuda_purged += 1
        for item in list(base.rglob("*")):
            if "workers" in item.parts:
                continue
            if item.is_file() and any(item.name.lower().startswith(p.lower()) for p in cuda_lib_prefixes):
                item.unlink(missing_ok=True)
                cuda_purged += 1

    if cuda_purged:
        print(f"[BUILD] Purged {cuda_purged} accidental CUDA files/directories from bundle.")

    unneeded_dirs = [
        "torch/include", "torch/share", "torchaudio/include", "scipy/include",
        "PySide6/include", "PySide6/glue", "PySide6/typesystems", "PySide6/scripts",
        "PySide6/translations",
        "PySide6/plugins/generic", "PySide6/plugins/sqldrivers",
        "PySide6/plugins/sensorgestures", "PySide6/plugins/position",
        "PySide6/plugins/scenegraph", "PySide6/plugins/qmltooling",
        "PySide6/plugins/networkinformation", "PySide6/plugins/geometryloaders",
        "onnxruntime/include", "sentencepiece/include", "tokenizers/include",
    ]
    for base in internal_dirs:
        if not base.exists():
            continue
        for hp in unneeded_dirs:
            target = base / Path(hp)
            if target.is_dir() and "workers" not in target.parts:
                print(f"[BUILD] Removing unneeded directory: {target}")
                shutil.rmtree(target, ignore_errors=True)

    pruned_files = 0
    test_dir_names = {"tests", "testing", "test", "benchmark", "benchmarks", "sample_files"}
    dist_info_junk = {"RECORD", "INSTALLER", "REQUESTED", "WHEEL", "direct_url.json"}
    for base in internal_dirs:
        if not base.exists():
            continue
        for item in list(base.rglob("*")):
            if "workers" in item.parts:
                continue
            if item.is_file():
                if item.suffix in (".pdb", ".pyi", ".c", ".cpp", ".h", ".hpp", ".pyx", ".pxd"):
                    item.unlink(missing_ok=True)
                    pruned_files += 1
                elif item.name in dist_info_junk and ".dist-info" in str(item):
                    item.unlink(missing_ok=True)
                    pruned_files += 1
            elif item.is_dir():
                if item.name.lower() in test_dir_names:
                    shutil.rmtree(item, ignore_errors=True)
                elif item.name.lower() in ("doc", "docs") and "site-packages" in item.parts:
                    shutil.rmtree(item, ignore_errors=True)

    if pruned_files:
        print(f"[BUILD] Pruned {pruned_files} debug/stub/source files from bundle.")

    # Prune software OpenGL rasterizer (~30MB) not needed by QtWidgets / Direct3D 11
    opengl_purged = 0
    for base in internal_dirs:
        if not base.exists():
            continue
        for opengl_dll in base.glob("**/opengl32sw.dll"):
            if opengl_dll.is_file():
                print(f"[BUILD] Pruning software OpenGL rasterizer: {opengl_dll}")
                opengl_dll.unlink(missing_ok=True)
                opengl_purged += 1
    if opengl_purged:
        print(f"[BUILD] Pruned {opengl_purged} opengl32sw.dll binaries from bundle.")

    # Binary symbol stripping for Linux and macOS
    if sys.platform.startswith("linux") and shutil.which("strip"):
        stripped_count = 0
        for base in internal_dirs:
            if not base.exists():
                continue
            for item in list(base.rglob("*")):
                if "workers" in item.parts:
                    continue
                if item.is_file() and not item.is_symlink():
                    if item.suffix == ".so" or ".so." in item.name or (item.stat().st_mode & 0o111 and not item.suffix):
                        try:
                            res = subprocess.run(
                                ["strip", "--strip-unneeded", str(item)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=False,
                            )
                            if res.returncode == 0:
                                stripped_count += 1
                        except Exception:
                            pass
        if stripped_count:
            print(f"[BUILD] Stripped unneeded symbols from {stripped_count} Linux binaries/libraries.")
    elif sys.platform == "darwin" and shutil.which("strip"):
        stripped_count = 0
        for base in internal_dirs:
            if not base.exists():
                continue
            for item in list(base.rglob("*")):
                if "workers" in item.parts:
                    continue
                if item.is_file() and not item.is_symlink() and item.suffix in (".dylib", ".so"):
                    try:
                        res = subprocess.run(
                            ["strip", "-x", str(item)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                        if res.returncode == 0:
                            stripped_count += 1
                    except Exception:
                        pass
        if stripped_count:
            print(f"[BUILD] Stripped unneeded symbols from {stripped_count} macOS dynamic libraries.")


def sync_installer_scripts(project_version: str, root_dir: Path = _DEFAULT_ROOT) -> None:
    """Ensure Inno Setup and other installer packaging scripts match PROJECT_VERSION."""
    iss_file = root_dir / "installer" / "Windows" / "RadioTVStorySegmenter.iss"
    if iss_file.exists():
        content = iss_file.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(#define\s+MyAppVersion\s+)"[^"]*"',
            rf'\g<1>"{project_version}"',
            content,
        )
        if new_content != content:
            iss_file.write_text(new_content, encoding="utf-8")
            print(f"[BUILD] Synchronized Inno Setup script {iss_file.name} to version {project_version}")


def compile_windows_installer(project_version: str, root_dir: Path = _DEFAULT_ROOT) -> bool:
    """Compile the Windows Inno Setup installer executable if ISCC is installed."""
    iss_file = root_dir / "installer" / "Windows" / "RadioTVStorySegmenter.iss"
    if not iss_file.exists():
        return False

    iscc_candidates = [
        shutil.which("iscc"),
        shutil.which("ISCC"),
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path(os.environ.get("ProgramData", "C:/")) / "chocolatey" / "bin" / "iscc.exe",
    ]
    iscc_path = None
    for cand in iscc_candidates:
        if cand and Path(cand).is_file():
            iscc_path = str(cand)
            break

    clean_version = re.sub(r"\.+", ".", str(project_version).strip().lstrip("v"))
    if not iscc_path:
        print("\n[BUILD] Note: Inno Setup compiler (ISCC.exe) was not found in PATH or standard directories.")
        print(f"[BUILD] To compile the Windows installer package, run: iscc /DMyAppVersion=\"{clean_version}\" {iss_file}")
        return False

    print(f"\n[BUILD] Compiling Windows setup installer executable (v{clean_version}) with {iscc_path}...")
    cmd = [iscc_path, f"/DMyAppVersion={clean_version}", str(iss_file)]
    ret = subprocess.run(cmd, cwd=str(root_dir))
    if ret.returncode == 0:
        print(f"[SUCCESS] Windows Installer created for v{project_version} in dist/installer/")
        return True
    else:
        print(f"[WARNING] Inno Setup compilation exited with code {ret.returncode}.")
        return False


def package_plugins(
    app_root: Path | None = None,
    include_wp: bool = True,
    include_yt: bool = True,
    include_tr: bool = True,
    root_dir: Path = _DEFAULT_ROOT,
    dist_dir: Path = _DEFAULT_DIST,
    project_version: str = "",
) -> list[Path]:
    """Package plugins into standalone .zip release artifacts in dist/plugins/
    and optionally bundle them into app_root/plugins/.
    """
    plugins_src = root_dir / "plugins"
    dist_plugins = dist_dir / "plugins"
    dist_plugins.mkdir(parents=True, exist_ok=True)
    generated_zips = []

    plugin_configs = [
        ("wordpress", include_wp),
        ("youtube", include_yt),
        ("translation", include_tr),
    ]

    for plugin_id, enabled in plugin_configs:
        p_dir = plugins_src / plugin_id
        if not p_dir.is_dir() or not enabled:
            continue

        p_ver = project_version
        manifest_file = p_dir / "manifest.json"
        if manifest_file.exists():
            try:
                m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                p_ver = m_data.get("version", project_version)
            except Exception:
                pass

        zip_path = dist_plugins / f"rtvs-plugin-{plugin_id}-v{p_ver}.zip"
        addon_ver_path = dist_plugins / f"rtvs-plugin-{plugin_id}-v{p_ver}.rtvs-addon"
        local_addon_in_sub = p_dir / f"{plugin_id}.rtvs-addon"
        local_addon_in_root = plugins_src / f"{plugin_id}.rtvs-addon"

        print(f"[BUILD] Packaging plugin '{plugin_id}' (v{p_ver}) -> {addon_ver_path.name}")
        # Build versioned .rtvs-addon archive (which contains the plugin files)
        with zipfile.ZipFile(addon_ver_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in p_dir.rglob("*"):
                if item.is_file() and "__pycache__" not in item.parts and not item.name.endswith((".pyc", ".pyo", ".rtvs-addon")):
                    rel = item.relative_to(p_dir)
                    zf.write(item, rel)

        # Mirror as versioned .zip for release downloads (same archive payload)
        shutil.copy2(addon_ver_path, zip_path)
        shutil.copy2(addon_ver_path, local_addon_in_sub)
        shutil.copy2(addon_ver_path, local_addon_in_root)
        generated_zips.extend([addon_ver_path, zip_path])

        if app_root is not None:
            dest_plugin_dir = app_root / "plugins" / plugin_id
            dest_plugin_dir.mkdir(parents=True, exist_ok=True)
            for item in p_dir.rglob("*"):
                if item.is_file() and "__pycache__" not in item.parts and not item.name.endswith((".pyc", ".pyo")):
                    rel = item.relative_to(p_dir)
                    target = dest_plugin_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
            # Ensure unversioned .rtvs-addon copy exists locally for fallback loading
            shutil.copy2(addon_ver_path, dest_plugin_dir / f"{plugin_id}.rtvs-addon")
            shutil.copy2(addon_ver_path, app_root / "plugins" / f"{plugin_id}.rtvs-addon")
            print(f"[BUILD] Bundled plugin '{plugin_id}' and versioned add-on into {dest_plugin_dir}")

    return generated_zips

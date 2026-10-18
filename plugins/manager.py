"""Radio & TV Segmenter — Plugin Manager and Discovery Engine."""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from prs_shared import INTERNAL_APP_ID, PROJECT_VERSION, QSettings, get_github_repo, safe_extract_zip, verify_file_sha256
from plugins.base import BasePlugin, PluginManifest

import re

def parse_plugin_version_tuple(version_str: str) -> tuple[tuple[int, ...], int]:
    """Parse plugin version string into comparable numerical components and a stability weight."""
    if not version_str:
        return ((0, 0, 0), 0)
    cleaned = re.sub(r"^(?:version|ver|v)?[.\s_-]*", "", str(version_str).strip(), flags=re.IGNORECASE)
    is_prerelease = bool(re.search(r"[-_.]?(beta|alpha|rc|dev|preview)", str(version_str), re.IGNORECASE))
    parts = []
    for chunk in cleaned.split("."):
        m = re.match(r"^(\d+)", chunk)
        if m:
            parts.append(int(m.group(1)))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return (tuple(parts), 0 if is_prerelease else 1)


def is_newer_plugin_version(new_version: str, current_version: str) -> bool:
    """Returns True if new_version is strictly newer than current_version."""
    if not new_version or not current_version:
        return False
    return parse_plugin_version_tuple(new_version) > parse_plugin_version_tuple(current_version)

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QGroupBox,
    QTextEdit,
    QWidget,
    QProgressBar,
)


class PluginManager:
    """Manages discovery, lifecycle, settings, and GUI injection of plugins."""

    def __init__(self, app: Any = None):
        self.app = app
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.manifests: Dict[str, PluginManifest] = {}
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_paths: Dict[str, Path] = {}

    @classmethod
    def get_user_plugins_dir(cls) -> Path:
        """Returns the user-writable plugins folder."""
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".local" / "share"
        p = base / "RadioTVSegmenter" / "plugins"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_bundled_plugins_dir(cls) -> Path:
        """Returns the application installation plugins folder."""
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
            if sys.platform == "darwin":
                # Inside Contents/MacOS
                bundled = base.parent / "Resources" / "plugins"
                if bundled.exists():
                    return bundled
            return base / "plugins"
        # Development / source tree
        return Path(__file__).resolve().parent.parent / "plugins"

    def discover_plugins(self) -> Dict[str, PluginManifest]:
        """Scans plugin directories (bundled/repository and user folder) and loads manifests of available plugins."""
        self.manifests.clear()
        self.plugin_paths.clear()

        is_frozen = getattr(sys, "frozen", False)

        # 1. Scan bundled/repository plugins directory
        bundled_dir = self.get_bundled_plugins_dir()
        if bundled_dir.exists() and bundled_dir.is_dir():
            for item in bundled_dir.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    if manifest_file.exists():
                        try:
                            manifest = PluginManifest.from_file(manifest_file)
                            if self._is_uninstalled(manifest.id):
                                continue
                            self.manifests[manifest.id] = manifest
                            self.plugin_paths[manifest.id] = item
                        except Exception as exc:
                            print(f"[PLUGINS] Failed to load bundled manifest from {manifest_file}: {exc}")
                elif item.is_file() and item.name.endswith(".rtvs-addon"):
                    try:
                        with zipfile.ZipFile(item, "r") as zf:
                            if "manifest.json" in zf.namelist():
                                m_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                                manifest = PluginManifest.from_dict(m_data)
                                if self._is_uninstalled(manifest.id):
                                    continue
                                if manifest.id not in self.manifests:
                                    self.manifests[manifest.id] = manifest
                                    self.plugin_paths[manifest.id] = item
                    except Exception as exc:
                        print(f"[PLUGINS] Failed to read bundled addon manifest from {item}: {exc}")

        # 2. Scan user plugin directory (in frozen mode, installed plugins in user directory take precedence)
        user_dir = self.get_user_plugins_dir()
        if user_dir.exists() and user_dir.is_dir():
            for item in user_dir.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    if manifest_file.exists():
                        try:
                            manifest = PluginManifest.from_file(manifest_file)
                            if self._is_uninstalled(manifest.id):
                                continue
                            if is_frozen or manifest.id not in self.manifests:
                                self.manifests[manifest.id] = manifest
                                self.plugin_paths[manifest.id] = item
                        except Exception as exc:
                            print(f"[PLUGINS] Failed to load manifest from {manifest_file}: {exc}")
                elif item.is_file() and item.name.endswith(".rtvs-addon"):
                    try:
                        with zipfile.ZipFile(item, "r") as zf:
                            if "manifest.json" in zf.namelist():
                                m_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                                manifest = PluginManifest.from_dict(m_data)
                                if self._is_uninstalled(manifest.id):
                                    continue
                                if is_frozen or manifest.id not in self.manifests:
                                    self.manifests[manifest.id] = manifest
                                    self.plugin_paths[manifest.id] = item
                    except Exception as exc:
                        print(f"[PLUGINS] Failed to read addon manifest from {item}: {exc}")

        # Auto-update any previously-installed plugins if a newer version is shipped with the app update
        self.sync_bundled_updates()

        # Ensure .rtvs-addon packages are generated in bundled directory for export/download
        self.ensure_packaged_addons()

        return self.manifests

    def sync_bundled_updates(self) -> None:
        """Automatically updates installed plugins in the user directory if a newer version is bundled with an app update."""
        bundled_dir = self.get_bundled_plugins_dir()
        user_dir = self.get_user_plugins_dir()
        if not bundled_dir.exists() or not bundled_dir.is_dir():
            return

        for item in bundled_dir.iterdir():
            if item.name.startswith("."):
                continue
            bundled_manifest: Optional[PluginManifest] = None
            source_to_install: Optional[Path] = None

            if item.is_dir() and (item / "manifest.json").exists():
                try:
                    bundled_manifest = PluginManifest.from_file(item / "manifest.json")
                    source_to_install = item
                except Exception:
                    pass
            elif item.is_file() and item.name.endswith(".rtvs-addon"):
                try:
                    with zipfile.ZipFile(item, "r") as zf:
                        if "manifest.json" in zf.namelist():
                            m_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                            bundled_manifest = PluginManifest.from_dict(m_data)
                            source_to_install = item
                except Exception:
                    pass

            if not bundled_manifest or not source_to_install:
                continue

            pid = bundled_manifest.id
            if pid in self.manifests:
                current_user_manifest = self.manifests[pid]
                if is_newer_plugin_version(bundled_manifest.version, current_user_manifest.version):
                    print(f"[PLUGINS] App update detected newer bundled plugin for '{pid}' (v{current_user_manifest.version} -> v{bundled_manifest.version}). Auto-updating...")
                    try:
                        dest = user_dir / pid
                        if source_to_install.is_dir():
                            if dest.exists():
                                shutil.rmtree(dest, ignore_errors=True)
                            shutil.copytree(source_to_install, dest)
                        elif source_to_install.is_file():
                            if dest.exists():
                                shutil.rmtree(dest, ignore_errors=True)
                            dest.mkdir(parents=True, exist_ok=True)
                            with zipfile.ZipFile(source_to_install, "r") as z:
                                safe_extract_zip(z, dest)
                            if not (dest / "manifest.json").exists():
                                for sub in list(dest.iterdir()):
                                    if sub.is_dir() and (sub / "manifest.json").exists():
                                        for f in sub.iterdir():
                                            shutil.move(str(f), str(dest / f.name))
                                        shutil.rmtree(sub, ignore_errors=True)
                                        break
                        old_addon = user_dir / f"{pid}.rtvs-addon"
                        if old_addon.exists():
                            old_addon.unlink(missing_ok=True)

                        self.manifests[pid] = bundled_manifest
                        self.plugin_paths[pid] = dest
                    except Exception as e:
                        print(f"[PLUGINS] Failed to auto-update installed plugin '{pid}' from bundled package: {e}")

    def ensure_packaged_addons(self) -> None:
        """Ensures that all bundled directory-based plugins have up-to-date .rtvs-addon files created."""
        bundled_dir = self.get_bundled_plugins_dir()
        if bundled_dir.exists() and bundled_dir.is_dir():
            for item in bundled_dir.iterdir():
                if item.is_dir() and (item / "manifest.json").exists():
                    plugin_id = item.name
                    bundled_addon = bundled_dir / f"{plugin_id}.rtvs-addon"
                    sub_addon = item / f"{plugin_id}.rtvs-addon"
                    manifest_path = item / "manifest.json"
                    needs_package = not bundled_addon.exists()
                    if not needs_package:
                        try:
                            with zipfile.ZipFile(bundled_addon, "r") as zf:
                                if "manifest.json" in zf.namelist():
                                    data = json.loads(zf.read("manifest.json").decode("utf-8"))
                                    dir_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                                    if data.get("version") != dir_data.get("version"):
                                        needs_package = True
                                else:
                                    needs_package = True
                        except Exception:
                            needs_package = True

                    if needs_package:
                        try:
                            self.package_addon(item, bundled_addon)
                            if sub_addon.exists() or bundled_addon.exists():
                                self.package_addon(item, sub_addon)
                        except Exception as exc:
                            print(f"[PLUGINS] Could not auto-package {bundled_addon}: {exc}")

    @classmethod
    def get_bundled_addons(cls) -> Dict[str, Path]:
        """Returns a map of plugin_id -> Path of bundled .rtvs-addon packages."""
        res: Dict[str, Path] = {}
        bundled_dir = cls.get_bundled_plugins_dir()
        if bundled_dir.exists() and bundled_dir.is_dir():
            for item in bundled_dir.iterdir():
                if item.is_file() and item.name.endswith(".rtvs-addon"):
                    res[item.stem] = item
                elif item.is_dir() and (item / "manifest.json").exists():
                    addon_file = item / f"{item.name}.rtvs-addon"
                    if addon_file.exists():
                        res[item.name] = addon_file
                    else:
                        root_addon = bundled_dir / f"{item.name}.rtvs-addon"
                        if root_addon.exists():
                            res[item.name] = root_addon
        return res

    def _is_uninstalled(self, plugin_id: str) -> bool:
        val = self.settings.value(f"plugins/{plugin_id}/uninstalled", False)
        if isinstance(val, bool):
            return val
        return str(val).lower() in {"1", "true", "yes"}

    def is_plugin_installed(self, plugin_id: str) -> bool:
        """Checks whether the plugin is installed in the system."""
        if self._is_uninstalled(plugin_id):
            return False
        return plugin_id in self.manifests

    def is_plugin_enabled(self, plugin_id: str) -> bool:
        if not self.is_plugin_installed(plugin_id):
            return False
        manifest = self.manifests.get(plugin_id)
        default_val = manifest.enabled_by_default if manifest else False
        val = self.settings.value(f"plugins/{plugin_id}/enabled", default_val)
        if isinstance(val, bool):
            return val
        return str(val).lower() in {"1", "true", "yes"}

    def plugin_runtime(self, plugin_id: str) -> dict:
        manifest = self.manifests.get(plugin_id)
        if not manifest:
            return {"type": "core", "name": ""}
        return {"type": manifest.runtime_type, "name": manifest.runtime_name or manifest.id}

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> None:
        self.settings.setValue(f"plugins/{plugin_id}/enabled", enabled)
        self.settings.sync()
        if enabled:
            if plugin_id not in self.plugins:
                self.load_plugin(plugin_id)
            else:
                self.plugins[plugin_id].set_enabled(True)
        else:
            if plugin_id in self.plugins:
                self.plugins[plugin_id].set_enabled(False)
        if self.app and hasattr(self.app, "refresh_plugin_menus"):
            self.app.refresh_plugin_menus()

    def load_all_plugins(self) -> None:
        """Discovers and instantiates all enabled plugins."""
        self.discover_plugins()
        for plugin_id, manifest in self.manifests.items():
            if self.is_plugin_enabled(plugin_id):
                self.load_plugin(plugin_id)

    def load_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        if plugin_id in self.plugins:
            return self.plugins[plugin_id]

        manifest = self.manifests.get(plugin_id)
        folder = self.plugin_paths.get(plugin_id)
        if not manifest or not folder:
            return None

        entry_point = manifest.entry_point or "plugin:Plugin"
        module_name, class_name = entry_point.split(":", 1) if ":" in entry_point else ("plugin", "Plugin")

        try:
            plugin_cls = None
            # If plugin exists as files in user/extracted plugin folder, prefer loading dynamically from file
            py_file = (folder / f"{module_name}.py") if (folder and folder.is_dir()) else None
            if py_file and py_file.exists():
                try:
                    spec = importlib.util.spec_from_file_location(f"rtvs_plugin_{plugin_id}", py_file)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[f"rtvs_plugin_{plugin_id}"] = mod
                        spec.loader.exec_module(mod)
                        plugin_cls = getattr(mod, class_name, None)
                except Exception as file_load_err:
                    print(f"[PLUGINS] Direct file load failed for '{plugin_id}': {file_load_err}")

            # Fall back to importing directly if inside plugins package (bundled/frozen)
            if plugin_cls is None:
                try:
                    mod = importlib.import_module(f"plugins.{plugin_id}.{module_name}")
                    plugin_cls = getattr(mod, class_name, None)
                except (ImportError, ModuleNotFoundError):
                    pass

            if plugin_cls is None:
                print(f"[PLUGINS] Could not find class {class_name} in {plugin_id}")
                return None

            instance: BasePlugin = plugin_cls(manifest, self.app)
            instance.set_enabled(True)
            if instance.on_load():
                self.plugins[plugin_id] = instance
                print(f"[PLUGINS] Successfully loaded plugin: {manifest.name} v{manifest.version}")
                return instance
            else:
                print(f"[PLUGINS] Plugin {manifest.name} on_load returned False; disabling.")
                return None
        except Exception as exc:
            print(f"[PLUGINS] Error loading plugin '{plugin_id}': {exc}")
            import traceback
            traceback.print_exc()
            return None

    def unload_plugin(self, plugin_id: str) -> None:
        if plugin_id in self.plugins:
            try:
                self.plugins[plugin_id].set_enabled(False)
                self.plugins[plugin_id].on_unload()
            except Exception as exc:
                print(f"[PLUGINS] Error during unload of {plugin_id}: {exc}")
            del self.plugins[plugin_id]

    def get_export_destinations(self) -> List[Any]:
        """Returns all ExportDestination objects contributed by currently enabled plugins."""
        destinations = []
        for plugin_id, plugin in self.plugins.items():
            if plugin.is_enabled:
                try:
                    for dest in plugin.get_export_destinations():
                        destinations.append(dest)
                except Exception as exc:
                    print(f"[PLUGINS] Error getting export destinations from {plugin_id}: {exc}")
        return destinations


    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstalls and removes a plugin completely from the system."""
        # Unload if currently loaded
        self.unload_plugin(plugin_id)

        # Clear enabled status and plugin settings
        self.set_plugin_enabled(plugin_id, False)
        manifest = self.manifests.get(plugin_id)
        runtimes_to_remove = []
        if manifest and manifest.runtime_type == "isolated":
            rname = manifest.runtime_name or manifest.id
            if rname:
                runtimes_to_remove.append(rname)
        if plugin_id == "translation" and "translate" not in runtimes_to_remove:
            runtimes_to_remove.append("translate")

        for rname in runtimes_to_remove:
            try:
                import runtime_manager
                rm = getattr(self, "runtime_mgr", None) or runtime_manager.RuntimeManager()
                if hasattr(rm, "kill_all_subprocesses"):
                    rm.kill_all_subprocesses()
                else:
                    runtime_manager.kill_all_subprocesses()
                if hasattr(rm, "remove_environment"):
                    rm.remove_environment(rname)
            except Exception as exc:
                print(f"[PLUGINS] Could not remove isolated runtime {rname} for {plugin_id}: {exc}")

        # If uninstalling translation plugin, also remove downloaded translation models to prevent bloat
        if plugin_id == "translation":
            try:
                from prs_shared import get_app_storage_dir
                tr_models_dir = get_app_storage_dir() / "models" / "translation"
                if tr_models_dir.exists():
                    shutil.rmtree(tr_models_dir, ignore_errors=True)
            except Exception:
                pass

        self.settings.remove(f"plugins/{plugin_id}")
        self.settings.sync()

        # Remove from user plugins directory
        user_dir = self.get_user_plugins_dir()
        target_dir = user_dir / plugin_id
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception as exc:
                print(f"[PLUGINS] Error deleting directory {target_dir}: {exc}")

        # Remove standalone addon package in user directory if present
        addon_file = user_dir / f"{plugin_id}.rtvs-addon"
        if addon_file.exists():
            try:
                addon_file.unlink(missing_ok=True)
            except Exception as exc:
                print(f"[PLUGINS] Error removing addon file {addon_file}: {exc}")

        # Remove from bundled plugins directory
        bundled_dir = self.get_bundled_plugins_dir()
        bundled_target = bundled_dir / plugin_id
        if bundled_target.exists():
            try:
                shutil.rmtree(bundled_target, ignore_errors=True)
            except Exception as exc:
                print(f"[PLUGINS] Error deleting bundled directory {bundled_target}: {exc}")

        bundled_addon_file = bundled_dir / f"{plugin_id}.rtvs-addon"
        if bundled_addon_file.exists():
            try:
                bundled_addon_file.unlink(missing_ok=True)
            except Exception as exc:
                print(f"[PLUGINS] Error removing bundled addon file {bundled_addon_file}: {exc}")

        # Check if plugin_path was registered and remove from disk if inside plugins folders
        if plugin_id in self.plugin_paths:
            ppath = self.plugin_paths[plugin_id]
            if (user_dir in ppath.parents or bundled_dir in ppath.parents or ppath.parent in (user_dir, bundled_dir)) and ppath not in (user_dir, bundled_dir):
                if ppath.is_dir():
                    shutil.rmtree(ppath, ignore_errors=True)
                elif ppath.is_file():
                    try:
                        ppath.unlink(missing_ok=True)
                    except Exception:
                        pass

        # Mark explicitly uninstalled in settings so it is ignored if files cannot be deleted
        self.settings.setValue(f"plugins/{plugin_id}/uninstalled", True)
        self.settings.sync()

        if plugin_id in self.manifests:
            del self.manifests[plugin_id]
        if plugin_id in self.plugin_paths:
            del self.plugin_paths[plugin_id]

        self.discover_plugins()

        if self.app and hasattr(self.app, "refresh_plugin_menus"):
            self.app.refresh_plugin_menus()

        return True

    def install_addon(
        self,
        package_path: Path | str,
        enable: bool = False,
        expected_sha256: Optional[str] = None,
        load_ui: bool = True,
    ) -> bool:
        """Installs a .rtvs-addon or .zip package into the user plugins directory."""
        package_path = Path(package_path)
        if not package_path.exists():
            return False

        if expected_sha256:
            if not verify_file_sha256(package_path, expected_sha256):
                raise ValueError(f"Integrity check failed: package SHA-256 does not match expected checksum.")

        user_dir = self.get_user_plugins_dir()
        temp_extract = user_dir / ".tmp_install"
        shutil.rmtree(temp_extract, ignore_errors=True)
        temp_extract.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(package_path, "r") as z:
                safe_extract_zip(z, temp_extract)

            # Find folder with manifest.json
            manifest_file = None
            if (temp_extract / "manifest.json").exists():
                manifest_file = temp_extract / "manifest.json"
                source_folder = temp_extract
            else:
                for sub in temp_extract.iterdir():
                    if sub.is_dir() and (sub / "manifest.json").exists():
                        manifest_file = sub / "manifest.json"
                        source_folder = sub
                        break

            if not manifest_file:
                raise ValueError("The package does not contain a valid manifest.json")

            manifest = PluginManifest.from_file(manifest_file)
            dest = user_dir / manifest.id
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)

            shutil.copytree(source_folder, dest)

            # Clear uninstalled flag if previously uninstalled and persist enabled setting
            self.settings.remove(f"plugins/{manifest.id}/uninstalled")
            self.settings.setValue(f"plugins/{manifest.id}/enabled", enable)
            self.settings.sync()

            if load_ui:
                self.discover_plugins()
                self.set_plugin_enabled(manifest.id, enable)
                if enable:
                    self.load_plugin(manifest.id)
                else:
                    self.unload_plugin(manifest.id)

                if self.app and hasattr(self.app, "refresh_plugin_menus"):
                    self.app.refresh_plugin_menus()

            return True
        finally:
            shutil.rmtree(temp_extract, ignore_errors=True)

    @classmethod
    def package_addon(cls, plugin_folder: Path | str, output_zip: Path | str) -> bool:
        """Zips a plugin directory into an .rtvs-addon file."""
        src = Path(plugin_folder)
        dest = Path(output_zip)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not (src / "manifest.json").exists():
            print(f"[PLUGINS] Cannot package {src}: missing manifest.json")
            return False

        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(src):
                # Ignore __pycache__ and git
                dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", ".pytest_cache"}]
                for file in files:
                    if file.endswith((".pyc", ".pyo")):
                        continue
                    full = Path(root) / file
                    rel = full.relative_to(src)
                    z.write(full, rel)
        print(f"[PLUGINS] Packaged addon -> {dest}")
        return True



# Re-exported worker and dialog classes for 100% backward compatibility
from plugins.version_utils import parse_plugin_version_tuple, is_newer_plugin_version
from plugins.installer_workers import GitHubPluginsWorker, GitHubDownloadWorker, GitHubBatchDownloadWorker
from plugins.github_dialog import GitHubPluginsDialog
from plugins.manager_dialog import PluginManagerDialog

__all__ = [
    "PluginManager",
    "PluginManagerDialog",
    "GitHubPluginsDialog",
    "GitHubPluginsWorker",
    "GitHubDownloadWorker",
    "GitHubBatchDownloadWorker",
    "parse_plugin_version_tuple",
    "is_newer_plugin_version",
]

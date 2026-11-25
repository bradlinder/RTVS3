"""Modular build utilities for Radio & TV Segmenter PyInstaller & installer packaging."""
from __future__ import annotations

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
    find_tool,
    run,
    torch_windows_binary_flags,
)
from installer.build_tools.packaging import (
    compile_windows_installer,
    package_plugins,
    provision_optional_runtime_tools,
    prune_unneeded_bundled_files,
    sync_installer_scripts,
)

__all__ = [
    "UV_VERSION",
    "UV_URLS",
    "PYSIDE6_USED_SUBMODULES",
    "PYSIDE6_EXCLUDES",
    "TEST_AND_BENCHMARK_EXCLUDES",
    "COLLECT_ALL_PACKAGES",
    "COPY_METADATA_PACKAGES",
    "HIDDEN_IMPORTS",
    "parse_build_args",
    "exe_name",
    "find_tool",
    "check_cpu_only_torch",
    "torch_windows_binary_flags",
    "run",
    "provision_optional_runtime_tools",
    "prune_unneeded_bundled_files",
    "sync_installer_scripts",
    "compile_windows_installer",
    "package_plugins",
]

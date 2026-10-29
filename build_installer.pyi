# build_installer.pyi — Typing and Interface Stub for build_installer
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from __future__ import annotations
import argparse
import importlib
import importlib.util
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

def exe_name(base: str) -> str:
    ...

def find_tool(name: str) -> str:
    ...

def check_cpu_only_torch() -> None:
    ...

def torch_windows_binary_flags() -> list[str]:
    ...

def run(cmd: list[str]) -> None:
    ...

def provision_optional_runtime_tools(app_root: Path) -> None:
    ...

def prune_unneeded_bundled_files(app_root: Path) -> None:
    ...

def sync_installer_scripts(project_version: str) -> None:
    ...

def compile_windows_installer(project_version: str) -> bool:
    ...

def parse_build_args():
    ...

def package_plugins(app_root: Path | None=..., include_wp: bool=..., include_yt: bool=..., include_tr: bool=...) -> list[Path]:
    ...

def main() -> None:
    ...

"""Version parsing and semantic comparison utilities for the plugin system."""
from __future__ import annotations

import re
from typing import Tuple


def parse_plugin_version_tuple(version_str: str) -> Tuple[Tuple[int, ...], int]:
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

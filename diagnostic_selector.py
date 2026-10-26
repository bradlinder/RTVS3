"""Smart Diagnostic Test Selector for Radio & TV Story Segmenter.

Provides automated test filtering for `test_runner.py`:
- `--changed` / `--smart`: Inspects `git status --porcelain` (and recent file mtimes) to identify
  modified modules/plugins, then filters `DiagnosticEngine.items` to only those tests whose
  implementation or metadata references the modified modules.
- `--filter <kw1,kw2>` / `-k <kw>`: Filters `DiagnosticEngine.items` by substring match against
  test name, category, handler method name, or referenced modules.
"""

from __future__ import annotations

import inspect
import subprocess
import time
from pathlib import Path
from typing import Any, List, Sequence, Set


_ROOT_DIR = Path(__file__).resolve().parent

# Fast core smoke tests always included if `--changed` matches only metadata/docs
_DEFAULT_FAST_SMOKE_TESTS = {
    "Time Parsing & Formatting",
    "Project Serialization Round-Trip",
}


def get_modified_files(root_dir: Path = _ROOT_DIR) -> List[str]:
    """Return relative paths of modified or uncommitted files via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        if res.returncode == 0:
            modified = []
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    _status, path_str = parts
                    path_str = path_str.strip('"').replace("\\", "/")
                    # Focus on Python modules and plugins
                    if path_str.endswith(".py") or path_str.startswith("plugins/"):
                        modified.append(path_str)
            return modified
    except Exception:
        pass
    return []


def has_git_changes(root_dir: Path = _ROOT_DIR) -> bool:
    """Return True if there are modified or uncommitted python or plugin files in git."""
    return bool(get_modified_files(root_dir))


def detect_changed_tokens(root_dir: Path = _ROOT_DIR) -> Set[str]:
    """Return a set of lowercase module stems and plugin names from the most recently edited files."""
    tokens: Set[str] = set()

    ignored_names = {
        "CHANGELOG.md", "roadmap.txt", "package.json", "metadata.json",
        "index.html", "App.tsx", "AGENTS.md", "GEMINI.md",
        "bump_version.py", "diagnostic_selector.py", "test_runner.py",
        "preview_manager.py", "roadmap_manager.py", "generate_symbol_index.py",
        "core_utils.py", "prs_shared.py", "RadioTVSegmenter.py",
        "updater.py", "build_installer.py", "transcript_story.py",
    }

    # 1. First consult git status for uncommitted/modified files
    git_files = get_modified_files(root_dir)
    changed_paths: List[str] = [
        f for f in git_files
        if Path(f).name not in ignored_names
    ]

    # 2. If git detected modified files, populate tokens directly
    for rel in changed_paths:
        p = Path(rel)
        if p.stem.startswith("diagnostic_") and p.stem.endswith("_tests"):
            topic = p.stem.replace("diagnostic_", "").replace("_tests", "")
            for word in topic.split("_"):
                if word and word not in ("and", "tests", "test"):
                    tokens.add(word)
            continue

        stem = p.stem.lower()
        if stem and stem not in ("__init__", "plugin", "export_destination", "base", "client", "castos"):
            tokens.add(stem)

        parts = [pt.lower() for pt in p.parts]
        if len(parts) >= 2 and parts[0] == "plugins":
            tokens.add(parts[1])

    # 3. If git found changed tokens, return them immediately
    if tokens:
        return tokens

    # 4. Fallback: inspect recent filesystem mtimes
    candidates: List[tuple[float, str]] = []
    now = time.time()
    for p in root_dir.rglob("*.py"):
        if any(part in (".venv", "node_modules", ".git", ".snapshots", ".codemaps", "__pycache__") for part in p.parts):
            continue
        if p.name in ignored_names or (p.stem.startswith("diagnostic_") and p.stem.endswith("_tests")):
            continue
        try:
            mtime = p.stat().st_mtime
            if mtime <= now + 5.0:
                candidates.append((mtime, str(p.relative_to(root_dir)).replace("\\", "/")))
        except OSError:
            pass

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        newest_mtime = candidates[0][0]
        # Select only files modified within 600s of the latest local edit (up to 6 most recent files)
        mtime_paths = [rel for mtime, rel in candidates[:6] if (newest_mtime - mtime) <= 600.0]
        for rel in mtime_paths:
            p = Path(rel)
            stem = p.stem.lower()
            if stem and stem not in ("__init__", "plugin", "export_destination", "base", "client", "castos"):
                tokens.add(stem)

            parts = [pt.lower() for pt in p.parts]
            if len(parts) >= 2 and parts[0] == "plugins":
                tokens.add(parts[1])

    return tokens


def select_diagnostic_items(
    engine: Any,
    items: Sequence[Any],
    filter_expr: str = "",
    changed_only: bool = False,
) -> List[Any]:
    """Filter diagnostic items by explicit `--filter` keywords and/or `--changed` git diff analysis."""
    selected = list(items)

    if filter_expr:
        keywords = [k.strip().lower() for k in filter_expr.split(",") if k.strip()]
        if keywords:
            filtered = []
            for it in selected:
                clean_name = engine._normalize_name(it.name)
                method_name = f"_test_{clean_name}"
                handler = getattr(engine, method_name, None)
                src = ""
                if handler is not None:
                    try:
                        src = inspect.getsource(handler).lower()
                    except Exception:
                        src = ""
                haystack = f"{it.name.lower()} {it.category.lower()} {method_name.lower()} {src}"
                if any(kw in haystack for kw in keywords):
                    filtered.append(it)
            selected = filtered

    if changed_only:
        tokens = detect_changed_tokens()
        if tokens:
            matched = []
            for it in selected:
                clean_name = engine._normalize_name(it.name)
                method_name = f"_test_{clean_name}"
                handler = getattr(engine, method_name, None)
                src = ""
                if handler is not None:
                    try:
                        src = inspect.getsource(handler).lower()
                    except Exception:
                        src = ""
                haystack = f"{it.name.lower()} {it.category.lower()} {method_name.lower()} {src}"
                if any(tok in haystack for tok in tokens):
                    matched.append(it)
            if matched:
                selected = matched
            else:
                selected = [it for it in selected if it.name in _DEFAULT_FAST_SMOKE_TESTS] or selected[:2]
        else:
            selected = [it for it in selected if it.name in _DEFAULT_FAST_SMOKE_TESTS] or selected[:2]

    return selected

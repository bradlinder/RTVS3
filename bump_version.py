#!/usr/bin/env python3
"""bump_version.py — Automated Version Synchronization Engine

Synchronizes the application version across all 10 required project locations
in strict adherence to AGENTS.md / GEMINI.md standardized version bump checklist:
1. prs_shared.py (PROJECT_VERSION)
2. updater.py (PROJECT_VERSION fallback)
3. build_installer.py (PROJECT_VERSION fallback)
4. installer/Windows/RadioTVStorySegmenter.iss (#define MyAppVersion)
5. plugins/*/manifest.json (Selective / Lazy Catch-Up Policy)
6. transcript_story.py (docstring version header)
7. package.json, metadata.json, index.html (web preview entrypoints)
8. src/App.tsx (default expanded accordion state)
9. CHANGELOG.md & roadmap.txt verification / integration
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parent

def normalize_version(ver: str) -> str:
    """Normalize version string: strip leading 'v', collapse double dots, trim."""
    cleaned = ver.strip().lstrip("v")
    cleaned = re.sub(r"\.+", ".", cleaned)
    return cleaned

def get_current_version() -> str:
    """Extract active version from prs_shared.py."""
    prs_path = ROOT_DIR / "prs_shared.py"
    if not prs_path.is_file():
        raise FileNotFoundError(f"Missing {prs_path}")
    content = prs_path.read_text(encoding="utf-8")
    m = re.search(r'PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if not m:
        raise ValueError("Could not find PROJECT_VERSION in prs_shared.py")
    return normalize_version(m.group(1))

def compute_bump(current_version: str, bump_type: str) -> str:
    """Calculate next semantic version (patch, minor, major) preserving suffix."""
    has_stable = "-stable" in current_version
    base = current_version.replace("-stable", "")
    parts = base.split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"Cannot parse semantic version from: {current_version}")

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0

    new_ver = f"{major}.{minor}.{patch}"
    if has_stable:
        new_ver += "-stable"
    return new_ver

def check_all_versions() -> dict[str, str]:
    """Inspect and report the version strings currently set across all files."""
    report = {}

    # 1. prs_shared.py
    prs_path = ROOT_DIR / "prs_shared.py"
    if prs_path.is_file():
        m = re.search(r'PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', prs_path.read_text(encoding="utf-8"))
        report["prs_shared.py"] = m.group(1) if m else "NOT FOUND"

    # 2. updater.py
    updater_path = ROOT_DIR / "updater.py"
    if updater_path.is_file():
        m = re.search(r'^\s*PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', updater_path.read_text(encoding="utf-8"), re.MULTILINE)
        report["updater.py"] = m.group(1) if m else "NOT FOUND"

    # 3. build_installer.py
    bi_path = ROOT_DIR / "build_installer.py"
    if bi_path.is_file():
        m = re.search(r'^\s*PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', bi_path.read_text(encoding="utf-8"), re.MULTILINE)
        report["build_installer.py"] = m.group(1) if m else "NOT FOUND"

    # 4. Inno Setup ISS
    iss_path = ROOT_DIR / "installer" / "Windows" / "RadioTVStorySegmenter.iss"
    if iss_path.is_file():
        m = re.search(r'#define\s+MyAppVersion\s+["\']([^"\']+)["\']', iss_path.read_text(encoding="utf-8"))
        report["installer/...iss"] = m.group(1) if m else "NOT FOUND"

    # 5. transcript_story.py
    ts_path = ROOT_DIR / "transcript_story.py"
    if ts_path.is_file():
        m = re.search(r'Radio & TV Segmenter v([^\s—]+)', ts_path.read_text(encoding="utf-8"))
        report["transcript_story.py"] = m.group(1) if m else "NOT FOUND"

    # 6. package.json
    pkg_path = ROOT_DIR / "package.json"
    if pkg_path.is_file():
        try:
            d = json.loads(pkg_path.read_text(encoding="utf-8"))
            report["package.json"] = d.get("version", "NOT FOUND")
        except Exception:
            report["package.json"] = "ERROR"

    # 7. metadata.json
    meta_path = ROOT_DIR / "metadata.json"
    if meta_path.is_file():
        try:
            d = json.loads(meta_path.read_text(encoding="utf-8"))
            desc = d.get("description", "")
            m = re.search(r'v([0-9a-zA-Z_.-]+)', desc)
            report["metadata.json"] = m.group(1) if m else "NOT FOUND"
        except Exception:
            report["metadata.json"] = "ERROR"

    # 8. index.html
    html_path = ROOT_DIR / "index.html"
    if html_path.is_file():
        m = re.search(r'<title>Radio & TV Segmenter v([^<]+)</title>', html_path.read_text(encoding="utf-8"))
        report["index.html"] = m.group(1) if m else "NOT FOUND"

    # 9. src/App.tsx
    app_path = ROOT_DIR / "src" / "App.tsx"
    if app_path.is_file():
        m = re.search(r'expandedVersions.*?{\s*[\'"]v([^\'"]+)[\'"]', app_path.read_text(encoding="utf-8"))
        report["src/App.tsx"] = m.group(1) if m else "NOT FOUND"

    # 10. roadmap.txt (N-1 Sliding Window: Section 2)
    roadmap_path = ROOT_DIR / "roadmap.txt"
    if roadmap_path.is_file():
        try:
            from roadmap_manager import RoadmapManager
            info = RoadmapManager(roadmap_path).get_sections_info()
            report["roadmap.txt (Section 2)"] = info.get("current_version", "NOT FOUND")
        except Exception:
            report["roadmap.txt (Section 2)"] = "ERROR"

    # 11. Plugins
    for p in sorted((ROOT_DIR / "plugins").glob("*/manifest.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            rel = str(p.relative_to(ROOT_DIR))
            report[rel] = d.get("version", "UNKNOWN")
        except Exception:
            pass

    return report

def bump_all(new_version: str, dry_run: bool = False, plugins: list[str] | None = None) -> bool:
    """Execute synchronous version updates across all checklist targets."""
    clean_ver = normalize_version(new_version)
    print(f"[BUMP] Synchronizing application version to: {clean_ver}")
    modifications = []

    # 1. prs_shared.py
    prs_path = ROOT_DIR / "prs_shared.py"
    if prs_path.is_file():
        content = prs_path.read_text(encoding="utf-8")
        new_content, count = re.subn(
            r'(PROJECT_VERSION\s*=\s*)["\'][^"\']+["\']',
            f'\\g<1>"{clean_ver}"',
            content,
            count=1
        )
        if count:
            modifications.append((prs_path, new_content))
            print(f"  [x] prs_shared.py -> {clean_ver}")
        else:
            print("  [!] Failed to match PROJECT_VERSION in prs_shared.py")

    # 2. updater.py
    updater_path = ROOT_DIR / "updater.py"
    if updater_path.is_file():
        content = updater_path.read_text(encoding="utf-8")
        new_content, count = re.subn(
            r'(^\s*PROJECT_VERSION\s*=\s*)["\'][^"\']+["\']',
            f'\\g<1>"{clean_ver}"',
            content,
            count=1,
            flags=re.MULTILINE
        )
        if count:
            modifications.append((updater_path, new_content))
            print(f"  [x] updater.py -> {clean_ver}")

    # 3. build_installer.py
    bi_path = ROOT_DIR / "build_installer.py"
    if bi_path.is_file():
        content = bi_path.read_text(encoding="utf-8")
        new_content, count = re.subn(
            r'(^\s*PROJECT_VERSION\s*=\s*)["\'][^"\']+["\']',
            f'\\g<1>"{clean_ver}"',
            content,
            count=1,
            flags=re.MULTILINE
        )
        if count:
            modifications.append((bi_path, new_content))
            print(f"  [x] build_installer.py -> {clean_ver}")

    # 4. installer/Windows/RadioTVStorySegmenter.iss
    iss_path = ROOT_DIR / "installer" / "Windows" / "RadioTVStorySegmenter.iss"
    if iss_path.is_file():
        content = iss_path.read_text(encoding="utf-8")
        new_content, count = re.subn(
            r'(#define\s+MyAppVersion\s+)["\'][^"\']+["\']',
            f'\\g<1>"{clean_ver}"',
            content,
            count=1
        )
        if count:
            modifications.append((iss_path, new_content))
            print(f"  [x] installer/Windows/RadioTVStorySegmenter.iss -> {clean_ver}")

    # 5. transcript_story.py
    ts_path = ROOT_DIR / "transcript_story.py"
    if ts_path.is_file():
        content = ts_path.read_text(encoding="utf-8")
        new_content, count = re.subn(
            r'("""Radio & TV Segmenter v)[^\s—]+',
            f'\\g<1>{clean_ver}',
            content,
            count=1
        )
        if count:
            modifications.append((ts_path, new_content))
            print(f"  [x] transcript_story.py -> {clean_ver}")

    # 6. package.json
    pkg_path = ROOT_DIR / "package.json"
    if pkg_path.is_file():
        try:
            d = json.loads(pkg_path.read_text(encoding="utf-8"))
            d["version"] = clean_ver
            new_content = json.dumps(d, indent=2) + "\n"
            modifications.append((pkg_path, new_content))
            print(f"  [x] package.json -> {clean_ver}")
        except Exception as e:
            print(f"  [!] package.json error: {e}")

    # 7. metadata.json
    meta_path = ROOT_DIR / "metadata.json"
    if meta_path.is_file():
        try:
            d = json.loads(meta_path.read_text(encoding="utf-8"))
            d["description"] = f"Radio & TV Segmenter v{clean_ver} - AI-powered audio/video transcription, diarization, translation, and story segmentation suite."
            new_content = json.dumps(d, indent=2) + "\n"
            modifications.append((meta_path, new_content))
            print(f"  [x] metadata.json -> {clean_ver}")
        except Exception as e:
            print(f"  [!] metadata.json error: {e}")

    # 8. index.html
    html_path = ROOT_DIR / "index.html"
    if html_path.is_file():
        content = html_path.read_text(encoding="utf-8")
        c1 = re.sub(r'<title>Radio & TV Segmenter v[^<]+</title>', f'<title>Radio & TV Segmenter v{clean_ver}</title>', content)
        c2 = re.sub(r'content="Radio & TV Segmenter v[^"-]+ -', f'content="Radio & TV Segmenter v{clean_ver} -', c1)
        c3 = re.sub(r'content="Radio & TV Segmenter v[^"]+"', f'content="Radio & TV Segmenter v{clean_ver}"', c2)
        modifications.append((html_path, c3))
        print(f"  [x] index.html -> {clean_ver}")

    # 9. src/App.tsx
    app_path = ROOT_DIR / "src" / "App.tsx"
    if app_path.is_file():
        content = app_path.read_text(encoding="utf-8")
        # replace default expanded accordion
        c1 = re.sub(
            r"expandedVersions,\s*setExpandedVersions\s*\]\s*=\s*useState<Record<string,\s*boolean>>\(\{\s*'v[^']+':\s*true\s*\}\);",
            f"expandedVersions, setExpandedVersions] = useState<Record<string, boolean>>({{ 'v{clean_ver}': true }});",
            content
        )
        c2 = re.sub(
            r"release\.version === 'v[^']+'\s*\|\|\s*release\.version === 'v3\.5\.34'",
            f"release.version === 'v{clean_ver}' || release.version === 'v3.5.34'",
            c1
        )
        modifications.append((app_path, c2))
        print(f"  [x] src/App.tsx -> v{clean_ver}")

    # 10. Plugins (Selective / Lazy Catch-Up Policy)
    if plugins:
        plugin_targets = [p.strip().lower() for p in plugins]
        for manifest in (ROOT_DIR / "plugins").glob("*/manifest.json"):
            plugin_name = manifest.parent.name.lower()
            if "all" in plugin_targets or plugin_name in plugin_targets:
                try:
                    d = json.loads(manifest.read_text(encoding="utf-8"))
                    d["version"] = clean_ver
                    new_content = json.dumps(d, indent=2) + "\n"
                    modifications.append((manifest, new_content))
                    print(f"  [x] plugin {manifest.parent.name}/manifest.json -> {clean_ver}")
                except Exception as e:
                    print(f"  [!] Plugin {plugin_name} error: {e}")

    if dry_run:
        print(f"\n[DRY RUN] Would write updates to {len(modifications)} files. No changes written.")
        return True

    for path, new_content in modifications:
        path.write_text(new_content, encoding="utf-8")

    # Synchronize roadmap.txt Section 2
    roadmap_path = ROOT_DIR / "roadmap.txt"
    if roadmap_path.is_file():
        try:
            from roadmap_manager import RoadmapManager
            rm = RoadmapManager(roadmap_path)
            rm.sync_current_version(clean_ver)
            print(f"  [x] roadmap.txt (Section 2) -> v{clean_ver}")
        except Exception as e:
            print(f"  [!] Failed to sync roadmap.txt: {e}")

    print(f"[BUMP] Successfully updated {len(modifications)} files to v{clean_ver}.")
    return True

def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize application versions across all project files.")
    parser.add_argument("version", nargs="?", help="Explicit target version (e.g. 3.8.7 or 3.8.7-stable)")
    parser.add_argument("--patch", action="store_true", help="Increment patch number (e.g. 3.8.6 -> 3.8.7)")
    parser.add_argument("--minor", action="store_true", help="Increment minor number (e.g. 3.8.6 -> 3.9.0)")
    parser.add_argument("--major", action="store_true", help="Increment major number (e.g. 3.8.6 -> 4.0.0)")
    parser.add_argument("--check", action="store_true", help="Check and print versions across all files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate changes without writing to disk")
    parser.add_argument("--plugins", nargs="*", help="Specific plugin names to bump (or 'all' for all plugins)")

    args = parser.parse_args()

    if args.check:
        print("=== Version Synchronization Status ===")
        statuses = check_all_versions()
        current = get_current_version()
        mismatches = 0
        for k, v in statuses.items():
            is_match = (v == current) or ("plugin" in k.lower() or "manifest" in k.lower())
            flag = "[OK]  " if is_match else "[MIS]"
            if not is_match:
                mismatches += 1
            print(f"  {flag} {k:35} : {v}")
        print("=======================================")
        if mismatches:
            print(f"[!] Warning: {mismatches} core files differ from active {current}.")
            return 1
        print(f"[OK] All core files synchronized on v{current}.")
        return 0

    target_ver = None
    if args.version:
        target_ver = normalize_version(args.version)
    elif args.patch:
        target_ver = compute_bump(get_current_version(), "patch")
    elif args.minor:
        target_ver = compute_bump(get_current_version(), "minor")
    elif args.major:
        target_ver = compute_bump(get_current_version(), "major")
    else:
        parser.print_help()
        return 1

    success = bump_all(target_ver, dry_run=args.dry_run, plugins=args.plugins)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

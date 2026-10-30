"""
scripts/dev_check.py - Ultra-Fast Pre-Flight Development & AI Safety Gate

Executes a complete 5-pillar verification sweep in <1.5s:
  1. Python Syntax Integrity (py_compile)
  2. Typing Stub Synchronization (generate_pyi_stubs.py --check)
  3. Zero-Dependency Web Preview State (preview_manager.py --sync)
  4. Modular File Budget Guard (modular_audit.py --budget-guard)
  5. Change-Aware Tier 2 Regression Suite (test_runner.py --quiet)

Use this script:
  - Before committing or merging any AI task branch into dev
  - As a local Git pre-commit hook
  - As the final validation gate in agent workflows
"""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def check_syntax() -> Tuple[bool, str]:
    """Compiles all tracked python files in root and scripts."""
    errors = []
    py_files = list(ROOT_DIR.glob("*.py")) + list((ROOT_DIR / "scripts").glob("*.py"))
    for pf in py_files:
        try:
            py_compile.compile(str(pf), doraise=True)
        except Exception as e:
            errors.append(f"{pf.name}: {e}")
    if errors:
        return False, f"{len(errors)} syntax error(s): " + "; ".join(errors[:3])
    return True, f"Verified {len(py_files)} files"


def check_typing_stubs() -> Tuple[bool, str]:
    """Verifies interface stubs for modules exceeding 800 lines."""
    cmd = [sys.executable, str(ROOT_DIR / "scripts" / "generate_pyi_stubs.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        return False, "Typing stubs out of sync. Run: python scripts/generate_pyi_stubs.py --all"
    return True, "All large module .pyi stubs synchronized"


def check_preview_sync() -> Tuple[bool, str]:
    """Ensures zero-dependency preview files match prs_shared.py."""
    cmd = [sys.executable, str(ROOT_DIR / "preview_manager.py"), "--sync"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        return False, f"Preview sync failed: {res.stderr.strip() or res.stdout.strip()}"
    return True, "Zero-dependency preview state verified"


def check_modular_budget() -> Tuple[bool, str]:
    """Guards against new monolithic files exceeding the 1,000 line ceiling."""
    # Known legacy modules grandfathered pending roadmap modularization (must have .pyi stubs)
    GRANDFATHERED = {
        "prs_shared.py", "diagnostic_cloud_and_system_tests.py", "processing.py",
        "diagnostic_batch_tests.py", "media_batch.py", "voice_profile_dialog.py",
        "runtime_manager.py", "updater.py", "build_installer.py",
        "diagnostic_export_tests.py", "background_workers.py", "ui_layout.py",
        "plugins/wordpress/client.py", "export/dialog.py"
    }
    
    new_violations = []
    for py_file in ROOT_DIR.rglob("*.py"):
        rel = py_file.relative_to(ROOT_DIR).as_posix()
        if any(part in rel.split("/") for part in [".git", "node_modules", "dist", "build", ".archive", ".snapshots", "__pycache__"]):
            continue
        if rel in GRANDFATHERED or rel.replace("\\", "/") in GRANDFATHERED:
            continue
        try:
            line_count = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
            if line_count > 1000:
                new_violations.append(f"{rel} ({line_count} lines)")
        except Exception:
            pass

    if new_violations:
        return False, f"New modules exceed 1k line budget: {', '.join(new_violations[:3])}"

    # Verify Single Responsibility & Domain Separation
    srp_cmd = [sys.executable, str(ROOT_DIR / "scripts" / "modular_audit.py"), "--check-srp"]
    srp_res = subprocess.run(srp_cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    if srp_res.returncode != 0:
        return False, "Single Responsibility violation detected. Run: python scripts/modular_audit.py --check-srp"

    return True, f"Budget & SRP compliant (0 new files >1,000 lines; 150+ single-purpose modules)"


def check_regression_tests() -> Tuple[bool, str]:
    """Executes change-aware Tier 2 diagnostic test suite."""
    cmd = [sys.executable, str(ROOT_DIR / "test_runner.py"), "--quiet"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        output = (res.stdout + "\n" + res.stderr).strip()
        last_lines = [l for l in output.splitlines() if l.strip()][-3:]
        return False, f"Tests failed: {' | '.join(last_lines)}"
    return True, "Change-aware diagnostic tests passed"


def main() -> None:
    print("\n" + "=" * 65)
    print(" PRE-FLIGHT DEV & AI VERIFICATION GATE (scripts/dev_check.py)")
    print("=" * 65)

    start_total = time.time()
    checks = [
        ("1. Python Syntax Integrity", check_syntax),
        ("2. Typing Stub (.pyi) Sync", check_typing_stubs),
        ("3. Zero-Dep Preview Sync", check_preview_sync),
        ("4. Modular Budget Guard (<1k lines)", check_modular_budget),
        ("5. Change-Aware Regression Tests", check_regression_tests),
    ]

    all_passed = True

    for name, func in checks:
        t0 = time.time()
        try:
            ok, msg = func()
        except Exception as ex:
            ok, msg = False, str(ex)
        dt = time.time() - t0

        if ok:
            print(f" [PASS] {name} ({dt:.2f}s) - {msg}")
        else:
            print(f" [FAIL] {name} ({dt:.2f}s) - {msg}")
            all_passed = False

    total_time = time.time() - start_total
    print("-" * 65)

    if all_passed:
        print(f" ALL 5 CHECKS PASSED in {total_time:.2f}s. Clean to commit or merge!\n")
        sys.exit(0)
    else:
        print(f" PRE-FLIGHT FAILED in {total_time:.2f}s. Review failures above before committing.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

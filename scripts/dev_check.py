"""
scripts/dev_check.py - Ultra-Fast Pre-Flight Development & AI Safety Gate

Executes a complete 6-pillar verification sweep in <2s:
  1. Python Syntax Integrity (py_compile)
  2. Typing Stub Synchronization (generate_pyi_stubs.py --check)
  3. Zero-Dependency Web Preview State (preview_manager.py --sync)
  4. Modular File Budget Guard (modular_audit.py --budget-guard)
  5. Qt Orphan-Window Flash Guard (AST pre-attach visibility check)
  6. Change-Aware Tier 2 Regression Suite (test_runner.py --quiet)

Use this script:
  - Before committing or merging any AI task branch into dev
  - As a local Git pre-commit hook
  - As the final validation gate in agent workflows
"""

from __future__ import annotations

import ast
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
        "prs_shared.py", "processing.py",
        "media_batch.py", "voice_profile_dialog.py",
        "runtime_manager.py",
        "ui_layout.py",
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


_QT_WIDGET_CTORS = {
    "QWidget", "QLabel", "QPushButton", "QLineEdit", "QComboBox", "QCheckBox",
    "QRadioButton", "QSpinBox", "QDoubleSpinBox", "QGroupBox", "QFrame",
    "QTextEdit", "QPlainTextEdit", "QSlider", "QListWidget", "QTableWidget",
    "QTabWidget", "QScrollArea", "QSplitter", "QProgressBar",
}
_QT_LAYOUT_CTORS = {"QVBoxLayout", "QHBoxLayout", "QFormLayout", "QGridLayout"}
_WIDGET_TEXT_ARG_CTORS = {"QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QGroupBox", "QLineEdit"}


def _ctor_has_explicit_parent(call_node: ast.Call, cname: str) -> bool:
    """Return True if a Qt widget constructor call passes an explicit parent argument."""
    for kw in call_node.keywords:
        if kw.arg == "parent":
            return not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
    if cname in _WIDGET_TEXT_ARG_CTORS:
        # e.g. QPushButton("Text", self) has >=2 positional args; QLineEdit(self) has 1 non-str arg
        if len(call_node.args) >= 2:
            return True
        if len(call_node.args) == 1 and isinstance(call_node.args[0], ast.Name) and call_node.args[0].id in {"self", "parent", "dialog", "dlg"}:
            return True
        return False
    # QWidget(self), QComboBox(self), QSpinBox(self), etc.
    if len(call_node.args) >= 1:
        a0 = call_node.args[0]
        if not (isinstance(a0, ast.Constant) and a0.value is None):
            return True
    return False


def _is_literal_false_visibility(call_node: ast.Call, attr: str) -> bool:
    if attr == "setVisible" and call_node.args:
        return isinstance(call_node.args[0], ast.Constant) and call_node.args[0].value is False
    if attr == "setRowVisible" and len(call_node.args) >= 2:
        return isinstance(call_node.args[1], ast.Constant) and call_node.args[1].value is False
    return False


def _iter_direct_nodes(stmts: list[ast.stmt]):
    """Yield AST nodes inside *stmts* without descending into nested def/class definitions."""
    stack = [
        s for s in stmts
        if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    while stack:
        node = stack.pop(0)
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            stack.append(child)


def check_qt_orphan_widget_flashes(root_dir: Path | None = None) -> Tuple[bool, str]:
    """Static AST guard: flag setVisible(non-False) / setRowVisible(..., non-False) on unparented
    widgets before their containing layout is attached to a parent widget or layout."""
    base = Path(root_dir) if root_dir is not None else ROOT_DIR
    skip_dirs = {".git", ".snapshots", ".archive", "build", "dist", "tests", "diagnostics", "scripts", "__pycache__", ".venv", "node_modules"}
    violations: List[str] = []
    scanned = 0

    for py_file in sorted(base.rglob("*.py")):
        rel = py_file.relative_to(base).as_posix()
        parts = rel.split("/")
        if any(part in skip_dirs for part in parts):
            continue
        if py_file.name.startswith("diagnostic") or py_file.name.startswith("test_"):
            continue
        try:
            src = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(py_file))
        except Exception:
            continue
        scanned += 1

        # Map function/method names -> set of target expressions they call setVisible(non-False) / setRowVisible on
        helper_vis_targets: dict[str, set[str]] = {}
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            targets: set[str] = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    attr = node.func.attr
                    if attr in ("setVisible", "setRowVisible") and not _is_literal_false_visibility(node, attr):
                        try:
                            targets.add(ast.unparse(node.func.value))
                        except Exception:
                            pass
            if targets:
                helper_vis_targets[fn.name] = targets

        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            unparented_widgets: dict[str, int] = {}
            unparented_layouts: dict[str, int] = {}
            layout_widgets: dict[str, str] = {}
            layout_attached: dict[str, int] = {}
            parented_added: dict[str, int] = {}
            direct_vis_calls: list[tuple[int, str, str]] = []
            direct_helper_calls: list[tuple[int, str]] = []

            for node in _iter_direct_nodes(fn.body):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    cname = getattr(node.value.func, "id", None) or getattr(node.value.func, "attr", None)
                    if cname in _QT_LAYOUT_CTORS and len(node.value.args) == 0:
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                unparented_layouts[t.id] = node.lineno
                    elif cname in _QT_WIDGET_CTORS and not _ctor_has_explicit_parent(node.value, cname):
                        for t in node.targets:
                            try:
                                unparented_widgets[ast.unparse(t)] = node.lineno
                            except Exception:
                                pass
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        attr = node.func.attr
                        if attr in ("addWidget", "add_widget", "addRow", "setWidget", "addTab"):
                            owner = node.func.value.id if isinstance(node.func.value, ast.Name) else None
                            if owner in unparented_layouts:
                                for arg in node.args:
                                    try:
                                        expr = ast.unparse(arg)
                                        if expr in unparented_widgets:
                                            layout_widgets[expr] = owner
                                    except Exception:
                                        pass
                            else:
                                for arg in node.args:
                                    try:
                                        expr = ast.unparse(arg)
                                        if expr in unparented_widgets:
                                            parented_added[expr] = min(parented_added.get(expr, 10**9), node.lineno)
                                    except Exception:
                                        pass
                        elif attr in ("addLayout", "add_layout", "setLayout") and node.args:
                            arg0 = node.args[0]
                            if isinstance(arg0, ast.Name) and arg0.id in unparented_layouts:
                                layout_attached[arg0.id] = min(layout_attached.get(arg0.id, 10**9), node.lineno)
                        elif attr in ("setVisible", "setRowVisible") and not _is_literal_false_visibility(node, attr):
                            try:
                                direct_vis_calls.append((node.lineno, attr, ast.unparse(node.func.value)))
                            except Exception:
                                pass
                        elif attr in helper_vis_targets and attr != fn.name:
                            direct_helper_calls.append((node.lineno, attr))
                    elif isinstance(node.func, ast.Name) and node.func.id in helper_vis_targets and node.func.id != fn.name:
                        direct_helper_calls.append((node.lineno, node.func.id))

            for lineno, attr, target_expr in direct_vis_calls:
                if attr == "setRowVisible" and target_expr in unparented_layouts:
                    att = layout_attached.get(target_expr, 10**9)
                    if lineno < att:
                        violations.append(f"{rel}:{lineno} ({fn.name}) {target_expr}.setRowVisible before attach at L{att}")
                elif attr == "setVisible" and target_expr in unparented_widgets:
                    if target_expr in parented_added and parented_added[target_expr] < lineno:
                        continue
                    lname = layout_widgets.get(target_expr)
                    att = layout_attached.get(lname, 10**9) if lname else 10**9
                    if lineno < att:
                        violations.append(f"{rel}:{lineno} ({fn.name}) unparented {target_expr}.setVisible before attach")

            for lineno, hname in direct_helper_calls:
                for target_expr in helper_vis_targets.get(hname, set()):
                    if target_expr in unparented_layouts and lineno < layout_attached.get(target_expr, 10**9):
                        violations.append(f"{rel}:{lineno} ({fn.name}) {hname}() touches unattached layout {target_expr}")
                    elif target_expr in unparented_widgets:
                        if target_expr in parented_added and parented_added[target_expr] < lineno:
                            continue
                        lname = layout_widgets.get(target_expr)
                        att = layout_attached.get(lname, 10**9) if lname else 10**9
                        if lineno < att:
                            violations.append(f"{rel}:{lineno} ({fn.name}) {hname}() shows unparented {target_expr} before attach")

    if violations:
        return False, f"{len(violations)} orphan-window flash risk(s): " + "; ".join(violations[:3])
    return True, f"Scanned {scanned} modules (0 pre-attach orphan widget flashes)"


def _iter_prod_py_files(root_dir: Path) -> List[Path]:
    skip = {".git", ".snapshots", ".archive", "__pycache__", "node_modules", "build", "dist", ".venv", "diagnostics", "scripts", "tests", "installer"}
    out: List[Path] = []
    for p in sorted(root_dir.rglob("*.py")):
        if any(part in skip for part in p.parts):
            continue
        if p.name.startswith(("diagnostic", "test_", "bump_", "sync", "preview_", "snapshot_", "build_", "roadmap_")):
            continue
        out.append(p)
    return out


def check_mainwindow_contracts(root_dir: Path | None = None) -> Tuple[bool, str]:
    """Static contract guard: verify MainWindow mixin self.<method>() and main_window/app/owner calls exist."""
    base = Path(root_dir) if root_dir is not None else ROOT_DIR
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    from RadioTVSegmenter import MainWindow

    mw_attrs = set(dir(MainWindow))
    mixin_files: List[Tuple[str, Path]] = []
    for cls in MainWindow.__mro__:
        mod = getattr(cls, "__module__", "")
        if mod and mod != "builtins":
            p = base / (mod.replace(".", "/") + ".py")
            if p.is_file():
                mixin_files.append((cls.__name__, p))
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                    for n in ast.walk(tree):
                        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self" and isinstance(n.ctx, ast.Store):
                            mw_attrs.add(n.attr)
                        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "setattr" and len(n.args) >= 2:
                            if isinstance(n.args[0], ast.Name) and n.args[0].id == "self" and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                                mw_attrs.add(n.args[1].value)
                except Exception:
                    pass

    qapp_allow = {"exec", "processEvents", "instance", "quit", "topLevelWidgets", "primaryScreen", "clipboard", "setPalette", "setStyleSheet", "setFont"}
    legacy_allow = {
        ("media_batch.py", "translate_document_file"),
        ("plugins/wordpress/wp_publish_dialog.py", "get_story_transcript"),
    }
    violations: List[str] = []

    for cname, p in mixin_files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = p.relative_to(base).as_posix()
        for cls_node in tree.body:
            if isinstance(cls_node, ast.ClassDef) and cls_node.name == cname:
                for n in ast.walk(cls_node):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                        if isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
                            attr = n.func.attr
                            if attr not in mw_attrs and (rel, attr) not in legacy_allow:
                                violations.append(f"{rel}:{n.lineno} ({cname}) self.{attr}()")

    for p in _iter_prod_py_files(base):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = p.relative_to(base).as_posix()
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                try:
                    target = ast.unparse(n.func.value)
                except Exception:
                    continue
                if target in ("main_window", "self.main_window", "self.app", "self.owner", "self.main_win"):
                    attr = n.func.attr
                    if attr not in mw_attrs and attr not in qapp_allow and (rel, attr) not in legacy_allow:
                        violations.append(f"{rel}:{n.lineno} {target}.{attr}()")

    if violations:
        return False, f"{len(violations)} missing MainWindow contract call(s): " + "; ".join(violations[:4])
    return True, f"Verified {len(mixin_files)} mixins & all cross-module MainWindow calls"


def check_qt_safety_hygiene(root_dir: Path | None = None) -> Tuple[bool, str]:
    """Static guard: QDialog classes starting QThread/Worker must handle closeEvent & reject/done; no unguarded QPixmap().scaled()."""
    base = Path(root_dir) if root_dir is not None else ROOT_DIR
    violations: List[str] = []
    files = _iter_prod_py_files(base)
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        rel = p.relative_to(base).as_posix()
        for idx, line in enumerate(text.splitlines(), 1):
            if "QPixmap(" in line and ".scaled(" in line:
                violations.append(f"{rel}:{idx} inline QPixmap(...).scaled() without isNull() check")
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                if any(b == "QDialog" or b.endswith(".QDialog") for b in bases):
                    seg = ast.get_source_segment(text, node) or ""
                    if ".start()" in seg and ("Worker" in seg or "QThread" in seg):
                        methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
                        if not ("closeEvent" in methods and ("reject" in methods or "done" in methods)):
                            violations.append(f"{rel}:{node.lineno} {node.name} missing closeEvent+reject/done worker teardown")

    if violations:
        return False, f"{len(violations)} Qt safety violation(s): " + "; ".join(violations[:4])
    return True, f"Scanned {len(files)} modules (0 unguarded QPixmap.scaled or QDialog thread leaks)"


def check_windows_and_frozen_hygiene(root_dir: Path | None = None) -> Tuple[bool, str]:
    """Static guard: Windows subprocess CREATE_NO_WINDOW flags and frozen-safe diagnostic tests."""
    base = Path(root_dir) if root_dir is not None else ROOT_DIR
    violations: List[str] = []
    for p in _iter_prod_py_files(base):
        text = p.read_text(encoding="utf-8", errors="ignore")
        rel = p.relative_to(base).as_posix()
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("run", "Popen", "check_output", "check_call"):
                    func_str = ast.unparse(node.func)
                    if "subprocess" in func_str:
                        kw_names = {kw.arg for kw in node.keywords}
                        seg = ast.get_source_segment(text, node) or ""
                        if any(posix_cmd in seg for posix_cmd in ('["open"', '["xdg-open"', '["xattr"')):
                            continue
                        ctx_lines = "\n".join(text.splitlines()[max(0, node.lineno - 6):node.lineno])
                        if ".appimage" in ctx_lines.lower() or 'sys.platform == "darwin"' in ctx_lines or 'sys.platform.startswith("linux")' in ctx_lines:
                            continue
                        if "creationflags" not in kw_names and "**" not in seg and "subprocess_kwargs" not in seg and "kwargs" not in seg:
                            violations.append(f"{rel}:{node.lineno} subprocess.{node.func.attr} missing creationflags")

    diag_files = list((base / "diagnostics").glob("*.py")) + list(base.glob("diagnostic_*.py"))
    for dp in diag_files:
        dtext = dp.read_text(encoding="utf-8", errors="ignore")
        drel = dp.relative_to(base).as_posix()
        if "Path(\"README.md\").read_text" in dtext or "Path('README.md').read_text" in dtext:
            violations.append(f"{drel} unguarded Path('README.md').read_text()")
        for idx, line in enumerate(dtext.splitlines(), 1):
            s = line.strip()
            if s.startswith(("from scripts.", "import scripts.")):
                ctx = "\n".join(dtext.splitlines()[max(0, idx - 5):idx])
                if "frozen" not in ctx:
                    violations.append(f"{drel}:{idx} unguarded scripts.* import")

    if violations:
        return False, f"{len(violations)} Windows/frozen hygiene issue(s): " + "; ".join(violations[:4])
    return True, "Windows CREATE_NO_WINDOW & frozen-test hygiene verified"


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
        ("5. Qt Orphan-Window Flash Guard", check_qt_orphan_widget_flashes),
        ("6. MainWindow & Mixin Contract Guard", check_mainwindow_contracts),
        ("7. Qt Thread Teardown & QPixmap Guard", check_qt_safety_hygiene),
        ("8. Windows & Frozen-Test Hygiene", check_windows_and_frozen_hygiene),
        ("9. Change-Aware Regression Tests", check_regression_tests),
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
        print(f" ALL {len(checks)} CHECKS PASSED in {total_time:.2f}s. Clean to commit or merge!\n")
        sys.exit(0)
    else:
        print(f" PRE-FLIGHT FAILED in {total_time:.2f}s. Review failures above before committing.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

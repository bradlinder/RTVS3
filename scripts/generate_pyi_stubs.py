#!/usr/bin/env python3
"""generate_pyi_stubs.py — Automated Interface Typing Stub (.pyi) Generator.

Scans Python modules using Python's standard AST library to extract class structures,
method signatures, type annotations, and module-level constants into lightweight
`.pyi` typing stubs. This allows agents and IDEs to inspect interface definitions
with a 90-95% reduction in context window tokens without loading implementation bodies.

Usage:
    python scripts/generate_pyi_stubs.py --all         # Generate/update stubs for all large modules (>800 lines)
    python scripts/generate_pyi_stubs.py --file <path> # Generate stub for a specific module
    python scripts/generate_pyi_stubs.py --check        # Verify stubs exist for all modules exceeding budget
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    ".archive",
    ".snapshots",
    "__pycache__",
    ".pytest_cache",
    ".vscode",
    "build",
    "installer",
}

EXCLUDED_FILES = {
    "test_runner.py",
    "diagnostic_export_tests.py",
    "diagnostic_cloud_and_system_tests.py",
    "diagnostic_batch_tests.py",
    "diagnostic_core_tests.py",
}


class StubTransformer(ast.NodeTransformer):
    """AST transformer that strips function bodies and replaces defaults with Ellipsis."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        node.args.defaults = [ast.Constant(value=Ellipsis) for _ in node.args.defaults]
        node.args.kw_defaults = [
            ast.Constant(value=Ellipsis) if d is not None else None for d in node.args.kw_defaults
        ]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        node.args.defaults = [ast.Constant(value=Ellipsis) for _ in node.args.defaults]
        node.args.kw_defaults = [
            ast.Constant(value=Ellipsis) if d is not None else None for d in node.args.kw_defaults
        ]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        new_body = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                new_body.append(self.visit(item))
            elif isinstance(item, ast.AnnAssign):
                new_node = ast.AnnAssign(
                    target=item.target,
                    annotation=item.annotation,
                    value=ast.Constant(value=Ellipsis) if item.value else None,
                    simple=item.simple,
                )
                new_body.append(ast.copy_location(new_node, item))
            elif isinstance(item, ast.Assign) and all(isinstance(t, ast.Name) for t in item.targets):
                new_node = ast.Assign(targets=item.targets, value=ast.Constant(value=Ellipsis))
                new_body.append(ast.copy_location(new_node, item))
        if not new_body:
            ellipsis_expr = ast.Expr(value=ast.Constant(value=Ellipsis))
            new_body = [ast.copy_location(ellipsis_expr, node)]
        node.body = new_body
        return node


def generate_stub_source(py_path: Path) -> str:
    """Generate clean .pyi stub content from a Python source file using AST."""
    source = py_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(py_path))

    new_body = []
    has_typing_import = False

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                has_typing_import = True
            new_body.append(node)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            transformed = StubTransformer().visit(node)
            new_body.append(transformed)
        elif isinstance(node, ast.AnnAssign):
            new_node = ast.AnnAssign(
                target=node.target,
                annotation=node.annotation,
                value=ast.Constant(value=Ellipsis) if node.value else None,
                simple=node.simple,
            )
            new_body.append(ast.copy_location(new_node, node))

    stub_tree = ast.Module(body=new_body, type_ignores=[])
    ast.fix_missing_locations(stub_tree)
    stub_text = ast.unparse(stub_tree)

    header_lines = [
        f"# {py_path.name}i — Typing and Interface Stub for {py_path.stem}",
        "from __future__ import annotations",
        "",
    ]
    if not has_typing_import:
        header_lines.append("from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union")
        header_lines.append("")

    return "\n".join(header_lines) + stub_text + "\n"


def get_large_modules(root: Path, line_threshold: int = 800) -> List[Path]:
    """Find all application Python modules exceeding the line threshold."""
    large_modules = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if not filename.endswith(".py") or filename in EXCLUDED_FILES:
                continue
            filepath = Path(dirpath) / filename
            try:
                line_count = len(filepath.read_text(encoding="utf-8", errors="replace").splitlines())
                if line_count >= line_threshold:
                    large_modules.append(filepath)
            except Exception:
                continue
    return sorted(large_modules)


def generate_stub_file(py_path: Path) -> Path:
    """Generate and write a .pyi stub next to the source file."""
    pyi_path = py_path.with_suffix(".pyi")
    content = generate_stub_source(py_path)
    pyi_path.write_text(content, encoding="utf-8", newline="\n")
    return pyi_path


def main():
    parser = argparse.ArgumentParser(description="Generate and maintain .pyi interface typing stubs.")
    parser.add_argument("--all", action="store_true", help="Generate stubs for all large modules (>=800 lines)")
    parser.add_argument("--file", type=str, help="Generate stub for a specific module")
    parser.add_argument("--threshold", type=int, default=800, help="Line threshold for --all (default: 800)")
    parser.add_argument("--check", action="store_true", help="Check whether all large modules have .pyi stubs")

    args = parser.parse_args()

    if args.file:
        target = Path(args.file).resolve()
        if not target.exists():
            print(f"[ERROR] File not found: {target}")
            sys.exit(1)
        pyi = generate_stub_file(target)
        orig_lines = len(target.read_text(encoding="utf-8").splitlines())
        stub_lines = len(pyi.read_text(encoding="utf-8").splitlines())
        print(f"[GENERATED] {pyi.name}: {orig_lines} -> {stub_lines} lines ({(1 - stub_lines/orig_lines)*100:.1f}% token reduction)")
        return

    large_modules = get_large_modules(ROOT_DIR, line_threshold=args.threshold)

    if args.check:
        missing = [p for p in large_modules if not p.with_suffix(".pyi").exists()]
        if missing:
            print(f"[WARN] {len(missing)} large module(s) missing .pyi stubs:")
            for m in missing:
                rel = m.relative_to(ROOT_DIR)
                print(f"  - {rel}")
            sys.exit(1)
        else:
            print(f"[PASS] All {len(large_modules)} large modules have .pyi stubs.")
            return

    # Default to generating all if --all is passed or no args
    print(f"[STUB GENERATOR] Processing {len(large_modules)} modules exceeding {args.threshold} lines...")
    total_orig = 0
    total_stub = 0

    for py_path in large_modules:
        rel = py_path.relative_to(ROOT_DIR)
        orig_lines = len(py_path.read_text(encoding="utf-8", errors="replace").splitlines())
        try:
            pyi = generate_stub_file(py_path)
            stub_lines = len(pyi.read_text(encoding="utf-8").splitlines())
            total_orig += orig_lines
            total_stub += stub_lines
            reduction = (1 - stub_lines / orig_lines) * 100
            print(f"  * {rel} ({orig_lines} lines) -> {pyi.name} ({stub_lines} lines, -{reduction:.1f}%)")
        except Exception as e:
            print(f"  ! Error generating stub for {rel}: {e}")

    savings = (1 - total_stub / total_orig) * 100 if total_orig else 0
    print(f"[COMPLETE] Generated {len(large_modules)} stubs: {total_orig:,} lines -> {total_stub:,} lines (-{savings:.1f}% context tokens).")


if __name__ == "__main__":
    main()

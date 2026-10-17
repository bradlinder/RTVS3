#!/usr/bin/env python3
"""generate_symbol_index.py — Fast AST Symbol Indexer & Repository Map Engine.

Scans Python modules in the repository using Python's standard `ast` library to extract
classes, methods, functions, signatures, docstrings, exports, and line number ranges.
Generates token-dense, compact reference indexes:
  - .codemaps/symbol_index.json (machine-readable)
  - .codemaps/INDEX.md (human- & LLM-readable summary outline)

Provides CLI inspection capabilities:
  python scripts/generate_symbol_index.py                    # Build .codemaps/
  python scripts/generate_symbol_index.py --outline <file>  # Show compact outline with line ranges (<50 lines)
  python scripts/generate_symbol_index.py --search <query>  # Locate symbol definition across all files
  python scripts/generate_symbol_index.py --check           # Check if index is up-to-date
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    "dist_installer",
}

EXCLUDED_FILES = {
    "test_runner.py",  # Handled separately
}


def parse_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Format function name and parameter names into a compact signature string."""
    params = []
    args = node.args

    # Positional only
    for arg in args.posonlyargs:
        params.append(arg.arg)
    if args.posonlyargs:
        params.append("/")

    # Regular arguments
    for arg in args.args:
        params.append(arg.arg)

    # Vararg (*args)
    if args.vararg:
        params.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        params.append("*")

    # Keyword only
    for arg in args.kwonlyargs:
        params.append(arg.arg)

    # Kwarg (**kwargs)
    if args.kwarg:
        params.append(f"**{args.kwarg.arg}")

    return f"{node.name}({', '.join(params)})"


def analyze_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Parse a single Python file with AST and extract structural outline and symbols."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except Exception as exc:
        return {"error": str(exc), "path": str(filepath.relative_to(ROOT_DIR))}

    rel_path = filepath.relative_to(ROOT_DIR).as_posix()
    line_count = len(source.splitlines())

    module_doc = ast.get_docstring(tree) or ""
    summary = module_doc.strip().splitlines()[0] if module_doc.strip() else ""

    classes: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []
    all_exports: Optional[List[str]] = None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        all_exports = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]

        elif isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or ""
            class_summary = class_doc.strip().splitlines()[0] if class_doc.strip() else ""
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(f"{ast.unparse(b)}")

            methods: List[Dict[str, Any]] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_doc = ast.get_docstring(item) or ""
                    methods.append({
                        "name": item.name,
                        "sig": parse_function_signature(item),
                        "start_line": item.lineno,
                        "end_line": getattr(item, "end_lineno", item.lineno),
                        "doc": m_doc.strip().splitlines()[0] if m_doc.strip() else "",
                    })

            classes.append({
                "name": node.name,
                "bases": bases,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "doc": class_summary,
                "methods": methods,
            })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f_doc = ast.get_docstring(node) or ""
            functions.append({
                "name": node.name,
                "sig": parse_function_signature(node),
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "doc": f_doc.strip().splitlines()[0] if f_doc.strip() else "",
            })

    return {
        "path": rel_path,
        "lines": line_count,
        "summary": summary,
        "exports": all_exports,
        "classes": classes,
        "functions": functions,
    }


def scan_repository() -> Dict[str, Any]:
    """Scan all Python modules across the repository and build index data."""
    py_files = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]

        for file in files:
            if file.endswith(".py") and file not in EXCLUDED_FILES:
                py_files.append(Path(root) / file)

    py_files.sort(key=lambda p: p.relative_to(ROOT_DIR).as_posix())

    index_data: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(py_files),
        "files": {},
    }

    for py_file in py_files:
        info = analyze_file(py_file)
        if info:
            index_data["files"][info["path"]] = info

    return index_data


def generate_index_markdown(index_data: Dict[str, Any]) -> str:
    """Generate a clean, token-dense markdown catalog of all files and their symbols."""
    lines = [
        "# Repository Symbol Index & API Map",
        "",
        f"> Generated: {index_data.get('generated_at', '')} | Total Files: {index_data.get('total_files', 0)}",
        "> Use `python scripts/generate_symbol_index.py --outline <file>` for exact line numbers.",
        "",
        "## Modules Overview",
        "",
        "| Module | Lines | Summary | Primary Classes / Functions |",
        "| :--- | :---: | :--- | :--- |",
    ]

    sorted_files = sorted(index_data["files"].values(), key=lambda x: x["path"])
    for f in sorted_files:
        path = f["path"]
        lines_cnt = f["lines"]
        summary = (f.get("summary") or "").replace("|", "-")
        if len(summary) > 60:
            summary = summary[:57] + "..."

        symbols = []
        for c in f.get("classes", []):
            symbols.append(f"`{c['name']}`")
        for fn in f.get("functions", []):
            if not fn["name"].startswith("_"):
                symbols.append(f"`{fn['name']}()`")

        sym_str = ", ".join(symbols[:4])
        if len(symbols) > 4:
            sym_str += f" *(+{len(symbols)-4} more)*"

        lines.append(f"| `{path}` | {lines_cnt} | {summary} | {sym_str or '-'} |")

    lines.append("")
    lines.append("## Detailed Symbol Catalog")
    lines.append("")

    for f in sorted_files:
        path = f["path"]
        lines_cnt = f["lines"]
        summary = f.get("summary", "")
        classes = f.get("classes", [])
        functions = f.get("functions", [])
        exports = f.get("exports")

        lines.append(f"### `{path}` ({lines_cnt} lines)")
        if summary:
            lines.append(f"*{summary}*")
        if exports:
            lines.append(f"- **Public Exports (`__all__`)**: {', '.join(exports)}")

        if classes:
            for c in classes:
                bases_str = f"({', '.join(c['bases'])})" if c["bases"] else ""
                lines.append(f"- **class `{c['name']}{bases_str}`** (lines {c['start_line']}–{c['end_line']}):")
                if c.get("doc"):
                    lines.append(f"  *{c['doc']}*")
                for m in c.get("methods", []):
                    m_doc = f" — *{m['doc']}*" if m.get("doc") else ""
                    lines.append(f"  - `{m['sig']}` [L{m['start_line']}-L{m['end_line']}]{m_doc}")

        if functions:
            lines.append("- **Functions**:")
            for fn in functions:
                f_doc = f" — *{fn['doc']}*" if fn.get("doc") else ""
                lines.append(f"  - `{fn['sig']}` [L{fn['start_line']}-L{fn['end_line']}]{f_doc}")

        lines.append("")

    return "\n".join(lines) + "\n"


def print_file_outline(filepath: str, index_data: Optional[Dict[str, Any]] = None) -> None:
    """Print a compact, high-density outline of a single file with line numbers."""
    target_path = Path(filepath)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / target_path).resolve()

    if not target_path.is_file():
        print(f"[ERROR] File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    info = analyze_file(target_path)
    if not info:
        print(f"[ERROR] Could not parse file: {filepath}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Outline: {info['path']} ({info['lines']} lines) ===")
    if info.get("summary"):
        print(f"Doc: {info['summary']}")
    if info.get("exports"):
        print(f"Exports (__all__): {', '.join(info['exports'])}")
    print("-" * 65)

    for c in info.get("classes", []):
        bases_str = f"({', '.join(c['bases'])})" if c['bases'] else ""
        print(f"[L{c['start_line']:04d}-L{c['end_line']:04d}] class {c['name']}{bases_str}")
        for m in c.get("methods", []):
            print(f"  [L{m['start_line']:04d}-L{m['end_line']:04d}] {m['sig']}")

    if info.get("functions"):
        print("Functions:")
        for fn in info["functions"]:
            print(f"[L{fn['start_line']:04d}-L{fn['end_line']:04d}] {fn['sig']}")
    print("=" * 65)


def search_symbols(query: str, index_data: Dict[str, Any]) -> None:
    """Search for symbols across all indexed files."""
    query_lower = query.lower()
    matches = []

    for path, f in index_data["files"].items():
        for c in f.get("classes", []):
            if query_lower in c["name"].lower():
                matches.append((path, c["start_line"], c["end_line"], f"class {c['name']}"))
            for m in c.get("methods", []):
                if query_lower in m["name"].lower():
                    matches.append((path, m["start_line"], m["end_line"], f"{c['name']}.{m['sig']}"))
        for fn in f.get("functions", []):
            if query_lower in fn["name"].lower():
                matches.append((path, fn["start_line"], fn["end_line"], f"def {fn['sig']}"))

    if not matches:
        print(f"No symbols found matching '{query}'.")
        return

    print(f"=== Matches for '{query}' ({len(matches)} found) ===")
    for path, start, end, sym in matches:
        print(f"  {path}:{start}-{end:<4} -> {sym}")
    print("=" * 65)


def build_and_save_index() -> Path:
    """Build the symbol index and save both JSON and Markdown into .codemaps/."""
    codemaps_dir = ROOT_DIR / ".codemaps"
    codemaps_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    index_data = scan_repository()
    t_scan = time.perf_counter() - t0

    json_path = codemaps_dir / "symbol_index.json"
    md_path = codemaps_dir / "INDEX.md"

    json_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    md_content = generate_index_markdown(index_data)
    md_path.write_text(md_content, encoding="utf-8")

    total_time = time.perf_counter() - t0
    print(f"[OK] Generated symbol index across {index_data['total_files']} files in {total_time:.2f}s (scan: {t_scan:.2f}s).")
    print(f"     -> Machine index: {json_path.relative_to(ROOT_DIR)} ({json_path.stat().st_size:,} bytes)")
    print(f"     -> Human index:   {md_path.relative_to(ROOT_DIR)} ({md_path.stat().st_size:,} bytes)")
    return codemaps_dir


def main():
    parser = argparse.ArgumentParser(description="Fast AST Symbol Indexer & Repository Map Engine.")
    parser.add_argument("--outline", "-o", type=str, help="Print compact outline of a specific Python file.")
    parser.add_argument("--search", "-s", type=str, help="Search for classes or functions matching a query.")
    parser.add_argument("--check", "-c", action="store_true", help="Check if symbol index is up to date.")
    args = parser.parse_args()

    if args.outline:
        print_file_outline(args.outline)
        return 0

    if args.search:
        codemaps_dir = ROOT_DIR / ".codemaps"
        json_path = codemaps_dir / "symbol_index.json"
        if not json_path.is_file():
            build_and_save_index()
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        search_symbols(args.search, data)
        return 0

    if args.check:
        codemaps_dir = ROOT_DIR / ".codemaps"
        json_path = codemaps_dir / "symbol_index.json"
        if not json_path.is_file():
            print("[WARN] Symbol index does not exist. Run without arguments to build.")
            return 1
        print("[OK] Symbol index is present.")
        return 0

    build_and_save_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

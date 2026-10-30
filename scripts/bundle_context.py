"""
scripts/bundle_context.py - One-Shot Context Bundler for Local AI & Editor LLMs

Extracts targeted symbol implementation slices, typing stubs (.pyi), reverse call sites,
and test verification filters into a single token-bounded markdown bundle (~1,000-1,500 tokens).
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from typing import Any, Dict, List, Optional, Tuple
from scripts.task_router import ASTImpactAnalyzer


def find_symbol_in_file(filepath: Path, symbol: str) -> Optional[Tuple[int, int, str]]:
    """Finds start and end line for a class or function definition in a file."""
    if not filepath.is_file():
        return None
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(filepath))
    except Exception:
        return None

    lines = content.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", None)
                if end_line is None:
                    # Fallback if end_lineno not set
                    end_line = min(start_line + 50, len(lines))
                slice_code = "\n".join(
                    f"{i:4d} | {lines[i - 1]}" for i in range(start_line, min(end_line + 1, len(lines) + 1))
                )
                return start_line, end_line, slice_code
    return None


def get_pyi_stub_slice(filepath: Path, symbol: str) -> Optional[str]:
    """Retrieves relevant stub definition from .pyi file if available."""
    pyi_candidates = [
        filepath.with_suffix(".pyi"),
        Path(f"{filepath.stem}.pyi"),
        Path(".pyi") / f"{filepath.stem}.pyi",
    ]
    for pyi in pyi_candidates:
        if pyi.is_file():
            try:
                lines = pyi.read_text(encoding="utf-8", errors="ignore").splitlines()
                matched_lines = []
                capturing = False
                base_indent = 0
                for line in lines:
                    stripped = line.strip()
                    if symbol in stripped and (stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith(f"{symbol}:")):
                        capturing = True
                        base_indent = len(line) - len(line.lstrip())
                        matched_lines.append(line)
                        continue
                    if capturing:
                        cur_indent = len(line) - len(line.lstrip())
                        if line.strip() and cur_indent <= base_indent:
                            break
                        matched_lines.append(line)
                if matched_lines:
                    return "\n".join(matched_lines)
            except Exception:
                pass
    return None


def build_bundle(symbol: str, target_file: Optional[str] = None) -> str:
    """Builds a token-dense markdown context bundle for local AI."""
    impact = ASTImpactAnalyzer.analyze(symbol)
    definitions = impact.get("definitions", [])

    def_file = None
    slice_output = None
    start_l, end_l = 0, 0

    if target_file and Path(target_file).is_file():
        res = find_symbol_in_file(Path(target_file), symbol)
        if res:
            start_l, end_l, slice_output = res
            def_file = target_file
    elif definitions:
        first_def = definitions[0]
        def_file = first_def["file"]
        res = find_symbol_in_file(Path(def_file), symbol)
        if res:
            start_l, end_l, slice_output = res

    # Stubs
    stub_content = None
    if def_file:
        stub_content = get_pyi_stub_slice(Path(def_file), symbol)

    # Output assembly
    md: List[str] = []
    md.append(f"# AI Context Scaffolding: `{symbol}`")
    md.append("")
    md.append(f"> **Target**: `{symbol}` in `{def_file or 'Unknown'}`")
    md.append(f"> **Verification Command**: `python test_runner.py --quiet --filter \"{symbol.replace('_', ' ').strip()}\"`")
    md.append("")

    if slice_output and def_file:
        md.append(f"## 1. Targeted Source Slice (`{def_file}`: Lines {start_l}-{end_l})")
        md.append("```python")
        md.append(slice_output)
        md.append("```")
        md.append("")

    if stub_content:
        md.append("## 2. Type Signature Stub (`.pyi`)")
        md.append("```python")
        md.append(stub_content)
        md.append("```")
        md.append("")

    md.append(f"## 3. Reverse Callers & Blast Radius ({impact.get('total_calls', 0)} calls)")
    call_sites = impact.get("call_sites", [])
    if call_sites:
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for cs in call_sites:
            by_file.setdefault(cs["file"], []).append(cs)
        for f, items in sorted(by_file.items()):
            md.append(f"- **{f}** ({len(items)} calls):")
            for item in items[:5]:  # limit to top 5 per file to conserve tokens
                md.append(f"  - L{item['line']} in `{item['caller']}()`: `{item['expr']}`")
            if len(items) > 5:
                md.append(f"  - *(+{len(items)-5} more calls in this file)*")
    else:
        md.append("- *No callers found in AST. Safe for isolated edit.*")
    md.append("")

    md.append("## 4. Instructions for Local AI")
    md.append("1. **Do NOT output the entire file**. Output ONLY a standard search & replace block or unified diff.")
    md.append("2. **Preserve existing method signature and return types** to avoid breaking the callers listed in Section 3.")
    md.append("3. After applying, verify immediately with the verification command above.")
    md.append("")

    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(description="One-shot token-bounded context bundler for local AI")
    parser.add_argument("query", nargs="?", default="", help="Symbol name or task query")
    parser.add_argument("--symbol", "-s", help="Exact symbol name to bundle")
    parser.add_argument("--file", "-f", help="Target source file path")
    parser.add_argument("--out", "-o", help="Optional output markdown file path")

    args = parser.parse_args()

    symbol = args.symbol or args.query
    if not symbol:
        print("Error: Specify a symbol to bundle: python scripts/bundle_context.py <symbol>")
        sys.exit(1)

    bundle = build_bundle(symbol.strip(), args.file)

    if args.out:
        Path(args.out).write_text(bundle, encoding="utf-8")
        print(f"Context bundle written to {args.out}")
    else:
        print(bundle)


if __name__ == "__main__":
    main()

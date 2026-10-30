"""
scripts/task_router.py - Token-Budget Task-to-Model Router & CI Invariant Verifier
Milestone 2.5: Token-Budget Task-to-Model Router & CI Pipeline Verification

Analyzes coding tasks, file scopes, and complexity to route work to the most token-efficient
local model tier (7B, 14B, 32B, R1, or Vision), and verifies repository CI invariants.
"""

from __future__ import annotations

import ast
import json
import os
import py_compile
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RouteRecommendation:
    task_query: str
    target_files: List[str]
    category: str
    recommended_model: str
    model_role: str
    context_budget: int
    rationale: str
    suggested_action: str


class TaskRouter:
    """Routes coding tasks to the optimal local model based on token budgets and file scope."""

    REASONING_KEYWORDS = [
        "race condition", "deadlock", "mutex", "thread", "concurrency",
        "lockup", "hang", "proof", "math", "algorithm", "state machine",
        "leak", "lifecycle", "flaky", "heisenbug"
    ]
    VISION_KEYWORDS = [
        "screenshot", "image", "ui", "mockup", "layout", "visual", "gui",
        "waveform", "painter", "dpi", "theme", "color", "qss", "dialog layout"
    ]
    REFACTOR_KEYWORDS = [
        "decompose", "split", "monolith", "architecture", "modular",
        "refactor", "facade", "submodule", "redesign", "clean architecture"
    ]

    @classmethod
    def load_symbol_index(cls) -> Dict[str, Any]:
        p = Path(".codemaps/symbol_index.json")
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("files", {})
            except Exception:
                pass
        return {}

    @classmethod
    def identify_target_files(cls, query: str, symbol_index: Dict[str, Any]) -> List[str]:
        words = re.findall(r"[\w\.-]+", query)
        found: List[str] = []
        for w in words:
            if w in symbol_index or (w.endswith(".py") and Path(w).is_file()):
                if w not in found:
                    found.append(w)
            else:
                for k in symbol_index.keys():
                    if w.lower() in k.lower() and len(w) > 4:
                        if k not in found:
                            found.append(k)
        return found

    @classmethod
    def route_task(cls, query: str) -> RouteRecommendation:
        symbol_index = cls.load_symbol_index()
        targets = cls.identify_target_files(query, symbol_index)
        q_lower = query.lower()

        # 1. Vision Tasks
        if any(vk in q_lower for vk in cls.VISION_KEYWORDS) and ("screenshot" in q_lower or "png" in q_lower or "image" in q_lower):
            return RouteRecommendation(
                task_query=query,
                target_files=targets,
                category="Visual & UI Layout Inspection",
                recommended_model="minicpm-v:latest",
                model_role="UI Inspector",
                context_budget=4096,
                rationale="Visual / screenshot inspection requires multimodal visual encoder.",
                suggested_action="Pass screenshot image directly to minicpm-v in Continue / Ollama.",
            )

        # 2. Concurrency & Deep Reasoning Tasks
        if any(rk in q_lower for rk in cls.REASONING_KEYWORDS):
            return RouteRecommendation(
                task_query=query,
                target_files=targets,
                category="Concurrency, Threading & Deep Deductive Reasoning",
                recommended_model="deepseek-r1:14b",
                model_role="Deductive QA Auditor",
                context_budget=16384,
                rationale="Concurrency and race conditions benefit from chain-of-thought (<think>) execution path simulation.",
                suggested_action="Invoke deepseek-r1:14b with targeted thread/signal lifecycle excerpt.",
            )

        # 3. Architectural Decomposition & Large Monolithic Files
        is_large_target = False
        target_lines = 0
        if targets:
            first_target = targets[0]
            target_lines = symbol_index.get(first_target, {}).get("lines", 0)
            if not target_lines and Path(first_target).is_file():
                target_lines = len(Path(first_target).read_text(encoding="utf-8", errors="ignore").splitlines())
            if target_lines >= 800:
                is_large_target = True

        if is_large_target or any(rf in q_lower for rf in cls.REFACTOR_KEYWORDS):
            action = f"Run `python scripts/modular_audit.py --suggest {targets[0]}`" if targets else "Run modular audit"
            return RouteRecommendation(
                task_query=query,
                target_files=targets,
                category="Architectural Planning & Large File Decomposition",
                recommended_model="qwen2.5-coder:32b-rtvs",
                model_role="Lead Architect",
                context_budget=16384,
                rationale=f"Large file scope ({target_lines} lines) or refactoring requires 32B code comprehension and AST preservation.",
                suggested_action=f"{action} and prompt qwen2.5-coder:32b-rtvs with the generated AST blueprint.",
            )

        # 4. Multi-File Changes (Moderate Scope)
        if len(targets) >= 2 or (targets and target_lines >= 300):
            return RouteRecommendation(
                task_query=query,
                target_files=targets,
                category="Multi-File Changes & Subsystem Wiring",
                recommended_model="qwen2.5-coder:14b-rtvs",
                model_role="Standard Developer",
                context_budget=32768,
                rationale=f"Target file scope ({target_lines} lines) or multi-file wiring fits 14B sweet spot (8.3 tok/s, 32k context).",
                suggested_action="Use qwen2.5-coder:14b-rtvs with symbol-first targeted slice retrieval.",
            )

        # 5. Localized Bug Fixes & Small File Changes (< 300 lines)
        return RouteRecommendation(
            task_query=query,
            target_files=targets,
            category="Localized Edits & Fast Unit Tests",
            recommended_model="qwen2.5-coder:7b-rtvs",
            model_role="Fast Edits",
            context_budget=8192,
            rationale="Small scope (<300 lines) completes fastest on 7B (17.4 tok/s) with minimal VRAM and power draw.",
            suggested_action="Apply minimal contiguous diff using qwen2.5-coder:7b-rtvs.",
        )


class CIInvariantVerifier:
    """Verifies repository build, modularity, and CI packaging invariants."""

    @classmethod
    def verify_all(cls) -> Dict[str, Any]:
        results: Dict[str, Any] = {"success": True, "checks": []}

        # Check 1: Core Module Isolation from Dev / Scripts
        core_files = ["RadioTVSegmenter.py", "processing.py", "prs_shared.py", "runtime_manager.py"]
        violations = []
        for cf in core_files:
            p = Path(cf)
            if p.is_file():
                content = p.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    if line.strip().startswith("import scripts") or line.strip().startswith("from scripts"):
                        violations.append(f"{cf}: {line.strip()}")
        results["checks"].append({
            "name": "Core Module Script Decoupling",
            "passed": len(violations) == 0,
            "details": "Core modules must never import from scripts/ or dev tools",
            "violations": violations,
        })
        if violations:
            results["success"] = False

        # Check 2: Python Syntax Compilation Across All Tracked Files
        syntax_errors = []
        for py_path in Path(".").glob("*.py"):
            try:
                py_compile.compile(str(py_path), doraise=True)
            except Exception as e:
                syntax_errors.append(f"{py_path.name}: {e}")
        for script_py in Path("scripts").glob("*.py"):
            try:
                py_compile.compile(str(script_py), doraise=True)
            except Exception as e:
                syntax_errors.append(f"{script_py.name}: {e}")

        results["checks"].append({
            "name": "Python Syntax Integrity",
            "passed": len(syntax_errors) == 0,
            "details": f"Verified syntax across root and scripts/ ({len(syntax_errors)} errors)",
            "errors": syntax_errors,
        })
        if syntax_errors:
            results["success"] = False

        # Check 3: Version Coherence Across Key Files
        version_mismatches = []
        prs_path = Path("prs_shared.py")
        expected_ver = ""
        if prs_path.is_file():
            m = re.search(r'PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', prs_path.read_text(encoding="utf-8"))
            if m:
                expected_ver = m.group(1)

        if expected_ver:
            # Check package.json
            pkg_path = Path("package.json")
            if pkg_path.is_file():
                try:
                    pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
                    if pkg_data.get("version") != expected_ver:
                        version_mismatches.append(f"package.json has {pkg_data.get('version')} != {expected_ver}")
                except Exception:
                    pass

        results["checks"].append({
            "name": "Version Coherence",
            "passed": len(version_mismatches) == 0,
            "details": f"Expected version {expected_ver} synchronized",
            "mismatches": version_mismatches,
        })
        if version_mismatches:
            results["success"] = False

        return results



class ASTImpactAnalyzer:
    """Performs AST-driven reverse call-site and definition impact analysis."""

    EXCLUDED_DIRS = {".git", ".snapshots", ".archive", "dist", "build", "node_modules", "__pycache__", ".vscode", ".continue"}

    class _Visitor(ast.NodeVisitor):
        def __init__(self, target_symbol: str, filepath: str):
            self.target_symbol = target_symbol
            self.filepath = filepath
            self.current_scope = "<module>"
            self.definitions: List[Dict[str, Any]] = []
            self.call_sites: List[Dict[str, Any]] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name == self.target_symbol:
                self.definitions.append({
                    "file": self.filepath,
                    "line": node.lineno,
                    "kind": "function",
                    "name": node.name,
                })
            prev = self.current_scope
            self.current_scope = node.name
            self.generic_visit(node)
            self.current_scope = prev

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node.name == self.target_symbol:
                self.definitions.append({
                    "file": self.filepath,
                    "line": node.lineno,
                    "kind": "async_function",
                    "name": node.name,
                })
            prev = self.current_scope
            self.current_scope = node.name
            self.generic_visit(node)
            self.current_scope = prev

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if node.name == self.target_symbol:
                self.definitions.append({
                    "file": self.filepath,
                    "line": node.lineno,
                    "kind": "class",
                    "name": node.name,
                })
            prev = self.current_scope
            self.current_scope = f"class {node.name}"
            self.generic_visit(node)
            self.current_scope = prev

        def visit_Call(self, node: ast.Call) -> None:
            matched = False
            expr_label = ""
            if isinstance(node.func, ast.Name) and node.func.id == self.target_symbol:
                matched = True
                expr_label = f"{self.target_symbol}(...)"
            elif isinstance(node.func, ast.Attribute) and node.func.attr == self.target_symbol:
                matched = True
                expr_label = f".{self.target_symbol}(...)"

            if matched:
                self.call_sites.append({
                    "file": self.filepath,
                    "line": node.lineno,
                    "caller": self.current_scope,
                    "expr": expr_label,
                })
            self.generic_visit(node)

    @classmethod
    def analyze(cls, symbol: str, root_dir: str = ".") -> Dict[str, Any]:
        """Scans python files for definitions and calls of the target symbol."""
        definitions: List[Dict[str, Any]] = []
        call_sites: List[Dict[str, Any]] = []
        scanned_files = 0

        root_path = Path(root_dir)
        for py_path in root_path.rglob("*.py"):
            parts = set(py_path.parts)
            if parts.intersection(cls.EXCLUDED_DIRS):
                continue
            if py_path.name.endswith(".pyi"):
                continue

            try:
                code = py_path.read_text(encoding="utf-8", errors="ignore")
                # Fast keyword check before AST parsing
                if symbol not in code:
                    continue
                tree = ast.parse(code, filename=str(py_path))
                visitor = cls._Visitor(symbol, str(py_path.as_posix()))
                visitor.visit(tree)
                definitions.extend(visitor.definitions)
                call_sites.extend(visitor.call_sites)
                scanned_files += 1
            except Exception:
                continue

        impacted_files = sorted(list({cs["file"] for cs in call_sites}))

        return {
            "symbol": symbol,
            "definitions": definitions,
            "call_sites": call_sites,
            "impacted_files": impacted_files,
            "scanned_matches": scanned_files,
            "total_calls": len(call_sites),
        }

    @classmethod
    def format_report(cls, analysis: Dict[str, Any]) -> str:
        sym = analysis["symbol"]
        defs = analysis["definitions"]
        calls = analysis["call_sites"]
        impacted = analysis["impacted_files"]

        lines = [
            "=" * 60,
            f" AST REVERSE-CALLER & IMPACT ANALYSIS: '{sym}'",
            "=" * 60,
        ]

        if defs:
            lines.append(" DEFINITION SITES:")
            for d in defs:
                lines.append(f"   - {d['file']}:{d['line']} ({d['kind']} {d['name']})")
        else:
            lines.append(" DEFINITION SITES: (None found in AST; might be a builtin, mixin attr, or dynamic property)")

        lines.append("")
        lines.append(f" CALL SITES ({analysis['total_calls']} calls across {len(impacted)} files):")
        if calls:
            by_file: Dict[str, List[Dict[str, Any]]] = {}
            for cs in calls:
                by_file.setdefault(cs["file"], []).append(cs)
            for f, items in sorted(by_file.items()):
                lines.append(f"   [File: {f}] ({len(items)} calls)")
                for item in items:
                    lines.append(f"     * L{item['line']} in {item['caller']}(): {item['expr']}")
        else:
            lines.append("   - No explicit ast.Call occurrences found.")

        lines.append("-" * 60)
        lines.append(f" IMPACT ASSESSMENT:")
        if len(impacted) > 5:
            lines.append(f"   HIGH BLAST RADIUS: Modifying '{sym}' directly affects {len(impacted)} files.")
            lines.append("   Recommendation: Use cloud model (Gemini) or preserve backward-compatible default arguments.")
        elif len(impacted) > 0:
            lines.append(f"   MODERATE BLAST RADIUS: Affects {len(impacted)} files.")
            lines.append(f"   Targeted verification: python test_runner.py --quiet --filter \"{sym.replace('_', ' ').strip()}\"")
        else:
            lines.append(f"   ISOLATED: No callers detected. Safe for localized refactoring.")
        lines.append("=" * 60)

        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("--verify", "--ci"):
        res = CIInvariantVerifier.verify_all()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["success"] else 1)

    if len(sys.argv) > 1 and sys.argv[1] in ("--impact", "--callers"):
        if len(sys.argv) < 3:
            print("Error: Specify a symbol name: python scripts/task_router.py --impact <symbol_name>")
            sys.exit(1)
        sym = sys.argv[2]
        analysis = ASTImpactAnalyzer.analyze(sym)
        print(ASTImpactAnalyzer.format_report(analysis))
        sys.exit(0)

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "General coding task"
    rec = TaskRouter.route_task(query)

    print("\n" + "=" * 60)
    print(" TASK ROUTER & CONTEXT RECOMMENDATION")
    print("=" * 60)
    print(f" Query: {rec.task_query}")
    print(f" Category: {rec.category}")
    print(f" Target Files: {', '.join(rec.target_files) if rec.target_files else 'None detected (broad search required)'}")
    print(f" Recommended Model: {rec.recommended_model} ({rec.model_role})")
    print(f" Context Budget: {rec.context_budget} tokens")
    print(f" Rationale: {rec.rationale}")
    print(f" Action: {rec.suggested_action}")
    print("=" * 60 + "\n")


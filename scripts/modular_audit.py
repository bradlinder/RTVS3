#!/usr/bin/env python3
"""scripts/modular_audit.py — AST Decomposition Suggester & Modular Budget Guard.

Analyzes Python module file sizes, computes structural complexity, detects domain
boundaries using Python's standard `ast` engine, and automatically generates actionable
submodule decomposition blueprints with 100% backward-compatible facade re-exports.

Capabilities:
  1. Repository Audit:
     python scripts/modular_audit.py                       # Audit all production modules
     python scripts/modular_audit.py --audit --sort lines  # Table sorted by total lines
  2. AST Decomposition Suggester:
     python scripts/modular_audit.py --suggest <file>      # Proposes domain submodules & re-exports
  3. Budget Guard / CI Linter:
     python scripts/modular_audit.py --budget-guard        # Verifies files against the 1,000-line ceiling
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".archive",
    ".snapshots",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".codemaps",
}

DEFAULT_WARN_THRESHOLD = 800
DEFAULT_HARD_CEILING = 1000

# Known legacy monoliths grandfathered pending incremental roadmap decomposition
GRANDFATHERED_LEGACY_MODULES = {
    "prs_shared.py",
    "processing.py",
    "ui_layout.py",
    "media_batch.py",
    "voice_profile_dialog.py",
    "runtime_manager.py",
    "updater.py",
    "build_installer.py",
    "background_workers.py",
    "speaker_dialogs.py",
    "speaker_profiles.py",
    "plugin_dialogs.py",
    "audio_normalization.py",
    "worker_asr_engines.py",
    "worker_diarization_engine.py",
    "core_utils.py",
    "export/dialog.py",
    "plugins/wordpress/client.py",
    "plugins/wordpress/plugin.py",
    "plugins/wordpress/wordpress_dialog.py",
    "plugins/wordpress/export_destination.py",
    "plugins/youtube/plugin.py",
    "plugins/youtube/export_destination.py",
    "diagnostic_cloud_and_system_tests.py",
    "diagnostic_batch_tests.py",
    "diagnostic_export_tests.py",
    "radio_tv_story_segmenter_worker.py",
    "RadioTVSegmenter.py",
}


# ---------------------------------------------------------------------------
# AST Structural Analyzer
# ---------------------------------------------------------------------------

class ModuleStructure:
    """Detailed structural metrics extracted from a Python module."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.rel_path = str(file_path.relative_to(ROOT_DIR)) if file_path.is_relative_to(ROOT_DIR) else str(file_path)
        self.total_lines = 0
        self.code_lines = 0
        self.comment_lines = 0
        self.blank_lines = 0
        self.docstring_lines = 0

        self.imports: List[str] = []
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.all_exports: Optional[List[str]] = None
        self.parse_error: Optional[str] = None
        self.ast_tree: Optional[ast.AST] = None

        self._analyze()

    def _analyze(self):
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as exc:
            self.parse_error = f"File read error: {exc}"
            return

        lines = content.splitlines()
        self.total_lines = len(lines)

        in_multiline_str = False
        multiline_delimiter = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                self.blank_lines += 1
                continue

            # Detect comments
            if not in_multiline_str and stripped.startswith("#"):
                self.comment_lines += 1
                continue

            # Simple triple-quote tracking
            for delim in ('"""', "'''"):
                occurrences = stripped.count(delim)
                if occurrences % 2 == 1:
                    if not in_multiline_str:
                        in_multiline_str = True
                        multiline_delimiter = delim
                    elif multiline_delimiter == delim:
                        in_multiline_str = False
                        multiline_delimiter = None

            if in_multiline_str:
                self.docstring_lines += 1
            else:
                self.code_lines += 1

        try:
            self.ast_tree = ast.parse(content, filename=str(self.file_path))
        except SyntaxError as syn_err:
            self.parse_error = f"Syntax error at line {syn_err.lineno}: {syn_err.msg}"
            return
        except Exception as exc:
            self.parse_error = f"AST parse error: {exc}"
            return

        for node in ast.iter_child_nodes(self.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for name in getattr(node, "names", []):
                    self.imports.append(name.name)

            elif isinstance(node, ast.ClassDef):
                c_info = self._extract_class_info(node, lines)
                self.classes.append(c_info)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                f_info = self._extract_func_info(node, lines)
                self.functions.append(f_info)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                            self.all_exports = [
                                elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
                        elif target.id.isupper() or not target.id.startswith("_"):
                            self.constants.append({
                                "name": target.id,
                                "line": getattr(node, "lineno", 0),
                            })

    def _extract_class_info(self, node: ast.ClassDef, lines: List[str]) -> Dict[str, Any]:
        end_line = getattr(node, "end_lineno", node.lineno)
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    "name": child.name,
                    "start": child.lineno,
                    "end": getattr(child, "end_lineno", child.lineno),
                    "is_private": child.name.startswith("_") and not child.name.startswith("__"),
                })

        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(f"{getattr(base.value, 'id', '')}.{base.attr}")

        return {
            "name": node.name,
            "start": node.lineno,
            "end": end_line,
            "lines": max(1, end_line - node.lineno + 1),
            "methods": methods,
            "method_count": len(methods),
            "bases": base_names,
            "domain": self._classify_domain(node.name, base_names, [m["name"] for m in methods]),
        }

    def _extract_func_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef, lines: List[str]) -> Dict[str, Any]:
        end_line = getattr(node, "end_lineno", node.lineno)
        return {
            "name": node.name,
            "start": node.lineno,
            "end": end_line,
            "lines": max(1, end_line - node.lineno + 1),
            "is_private": node.name.startswith("_") and not node.name.startswith("__"),
            "domain": self._classify_domain(node.name, [], []),
        }

    @staticmethod
    def _classify_domain(name: str, bases: List[str], method_names: List[str]) -> str:
        """Classifies a class or function into a logical domain based on naming and signatures."""
        n_lower = name.lower()
        bases_lower = [b.lower() for b in bases]
        m_lower = [m.lower() for m in method_names]

        # 1. UI & Dialogs
        if any(b in ("qwidget", "qdialog", "qmainwindow", "qtableview", "qlistwidget", "qgraphicsview") for b in bases_lower):
            return "ui"
        if "dialog" in n_lower or "widget" in n_lower or "view" in n_lower or "panel" in n_lower or "card" in n_lower or "window" in n_lower:
            return "ui"
        if any(m.startswith("paint") or m.startswith("mouse") or m.startswith("key") or "layout" in m for m in m_lower):
            return "ui"

        # 2. Background Workers & Concurrency
        if any(b in ("qthread", "qrunnable", "thread", "process") for b in bases_lower):
            return "worker"
        if "worker" in n_lower or "thread" in n_lower or "runner" in n_lower or "task" in n_lower:
            return "worker"

        # 3. Data Models, Schemas & Serialization
        if "model" in n_lower or "schema" in n_lower or "store" in n_lower or "dict" in n_lower:
            return "model"
        if any(m in ("to_dict", "from_dict", "serialize", "deserialize") for m in m_lower):
            return "model"

        # 4. Engine & Heavy Processing
        if "engine" in n_lower or "pipeline" in n_lower or "processor" in n_lower:
            return "engine"
        if any(w in n_lower for w in ("waveform", "ffmpeg", "transcription", "diarization", "vad", "detector", "denoiser", "normaliz", "resample")):
            return "engine"

        # 5. Utilities & Helpers
        return "utils"


# ---------------------------------------------------------------------------
# Decomposition Suggester Engine
# ---------------------------------------------------------------------------

class DecompositionPlan:
    """Proposed modular decomposition plan for a monolithic source file."""

    def __init__(self, structure: ModuleStructure):
        self.structure = structure
        self.target_file = structure.rel_path
        self.stem = structure.file_path.stem
        self.parent_dir = structure.file_path.parent
        self.proposed_submodules: List[Dict[str, Any]] = []
        self.facade_exports: List[str] = []
        self.dead_code_candidates: List[str] = []
        self._build_plan()

    @staticmethod
    def _classify_method_domain(m_name: str) -> str:
        name = m_name.lower()
        if any(k in name for k in ("video", "thumb", "waveform", "probe", "duration", "cache")):
            return "media_cache"
        if any(k in name for k in ("batch", "queue", "worker", "process", "run")):
            return "batch_ops"
        if any(k in name for k in ("load", "open", "save", "recent", "dialog", "file")):
            return "lifecycle"
        if any(k in name for k in ("ui", "layout", "click", "mouse", "key", "paint")):
            return "ui"
        return "core"

    def _build_plan(self):
        items_by_domain: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Check if we have monolithic classes (> 500 lines) with many methods
        for c in self.structure.classes:
            if c["lines"] > 500 and c["method_count"] > 4:
                # Monolithic class: inspect method clusters
                methods_by_domain: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                for m in c["methods"]:
                    d = self._classify_method_domain(m["name"])
                    methods_by_domain[d].append(m)

                # If methods span multiple domains, propose split mixins
                if len(methods_by_domain) > 1:
                    for d, m_list in methods_by_domain.items():
                        m_lines = sum(max(1, m["end"] - m["start"] + 1) for m in m_list)
                        clean_stem = self.stem.replace("_mixin", "")
                        sub_file = f"{clean_stem}_{d}_mixin.py" if "mixin" in c["name"].lower() else f"{clean_stem}_{d}.py"
                        mixin_name = f"{c['name']}{d.capitalize()}Part" if not "mixin" in c["name"].lower() else c["name"].replace("Mixin", f"{d.capitalize()}Mixin")
                        items_by_domain[d].append({
                            "type": "mixin_slice",
                            "name": mixin_name,
                            "parent_class": c["name"],
                            "lines": m_lines,
                            "methods": [m["name"] for m in m_list],
                        })
                    continue

            items_by_domain[c["domain"]].append({"type": "class", "name": c["name"], "lines": c["lines"], "info": c})

        for f in self.structure.functions:
            items_by_domain[f["domain"]].append({"type": "function", "name": f["name"], "lines": f["lines"], "info": f})

        # Suggest split files based on domain clusters
        domain_submodule_map = {
            "model": f"{self.stem}_model.py",
            "ui": f"{self.stem}_dialogs.py",
            "worker": f"{self.stem}_workers.py",
            "engine": f"{self.stem}_engine.py",
            "utils": f"{self.stem}_utils.py",
            "media_cache": f"{self.stem}_media_cache.py",
            "batch_ops": f"{self.stem}_batch_ops.py",
            "lifecycle": f"{self.stem}_lifecycle.py",
            "core": f"{self.stem}_core.py",
        }

        # If file only has one or two domains, create focused logical clusters
        if len(items_by_domain) <= 1:
            all_items = []
            for c in self.structure.classes:
                all_items.append({"type": "class", "name": c["name"], "lines": c["lines"], "info": c})
            for f in self.structure.functions:
                all_items.append({"type": "function", "name": f["name"], "lines": f["lines"], "info": f})

            midpoint = len(all_items) // 2
            part1 = all_items[:midpoint]
            part2 = all_items[midpoint:]

            if part1:
                self.proposed_submodules.append({
                    "filename": f"{self.stem}_core.py",
                    "domain": "core",
                    "items": part1,
                    "estimated_lines": sum(it["lines"] for it in part1),
                })
            if part2:
                self.proposed_submodules.append({
                    "filename": f"{self.stem}_ops.py",
                    "domain": "operations",
                    "items": part2,
                    "estimated_lines": sum(it["lines"] for it in part2),
                })
        else:
            for domain, items in items_by_domain.items():
                mod_name = domain_submodule_map.get(domain, f"{self.stem}_{domain}.py")
                total_domain_lines = sum(it["lines"] for it in items)
                self.proposed_submodules.append({
                    "filename": mod_name,
                    "domain": domain,
                    "items": items,
                    "estimated_lines": total_domain_lines,
                })

        # Collect facade re-export lines
        for sub in self.proposed_submodules:
            exported_names = [it["name"] for it in sub["items"] if not it["name"].startswith("_")]
            if exported_names:
                mod_stem = Path(sub["filename"]).stem
                self.facade_exports.append(f"from .{mod_stem} import (\n    " + ",\n    ".join(exported_names) + ",\n)")

        # Dead code heuristic: private top-level functions defined but never called
        all_text = ""
        try:
            with open(self.structure.file_path, "r", encoding="utf-8", errors="replace") as f:
                all_text = f.read()
        except Exception:
            pass

        for fn in self.structure.functions:
            if fn["is_private"]:
                # If only appears once (its definition), it may be dead code
                occurrences = all_text.count(fn["name"])
                if occurrences <= 1:
                    self.dead_code_candidates.append(fn["name"])

    def render_markdown_blueprint(self) -> str:
        out = [
            f"# Modular Decomposition Blueprint for `{self.target_file}`",
            f"- **Current Size**: {self.structure.total_lines:,} lines ({self.structure.code_lines:,} code, {self.structure.comment_lines:,} comments, {self.structure.docstring_lines:,} docstrings)",
            f"- **Target**: <= 800 lines (Hard ceiling: <= 1,000 lines)",
            f"- **Proposed Submodules**: {len(self.proposed_submodules)} files",
            "",
            "## 1. Submodule Allocations",
        ]

        for i, sub in enumerate(self.proposed_submodules, 1):
            out.append(f"### Submodule {i}: `{sub['filename']}` (~{sub['estimated_lines']:,} lines, Domain: {sub['domain'].upper()})")
            for it in sub["items"]:
                out.append(f"  - `{it['type']}` **{it['name']}** (lines: {it['lines']})")
            out.append("")

        out.append("## 2. Zero-Breakage Facade Re-Exports")
        out.append("Add the following re-exports to the original module to preserve 100% backward compatibility:")
        out.append("```python")
        out.append("# --- Submodule Re-Exports (100% Backward Compatibility) ---")
        out.extend(self.facade_exports)
        out.append("```")
        out.append("")

        if self.dead_code_candidates:
            out.append("## 3. Potential Dead Code Candidates")
            out.append("The following private functions only appear once (at definition) and can likely be safely purged:")
            for dc in self.dead_code_candidates:
                out.append(f"  - `def {dc}()`")
            out.append("")

        return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI & Repository Auditing
# ---------------------------------------------------------------------------

def scan_repository(root_dir: Path) -> List[ModuleStructure]:
    """Scans all Python modules in the repository, excluding build/venv directories."""
    structures = []
    for root, dirs, files in os.walk(root_dir):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                structures.append(ModuleStructure(file_path))

    return structures


def print_audit_report(structures: List[ModuleStructure], warn_threshold: int = DEFAULT_WARN_THRESHOLD, hard_ceiling: int = DEFAULT_HARD_CEILING, sort_by: str = "lines"):
    """Prints a formatted terminal table showing modularity compliance."""
    if sort_by == "lines":
        structures.sort(key=lambda s: s.total_lines, reverse=True)
    elif sort_by == "name":
        structures.sort(key=lambda s: s.rel_path)

    total_modules = len(structures)
    ok_count = sum(1 for s in structures if s.total_lines <= warn_threshold)
    warn_count = sum(1 for s in structures if warn_threshold < s.total_lines <= hard_ceiling)
    exceeds_count = sum(1 for s in structures if s.total_lines > hard_ceiling)

    print("=" * 88)
    print("RADIO & TV STORY SEGMENTER — MODULAR ARCHITECTURE AUDIT REPORT")
    print("=" * 88)
    print(f"Target Budget:    <= {warn_threshold} lines (Soft warning)")
    print(f"Hard Ceiling:     <= {hard_ceiling} lines (Mandatory decomposition threshold)")
    print(f"Total Modules:    {total_modules} files")
    print(f"Status Summary:   {ok_count} OK (<=800) | {warn_count} WARN (801-1000) | {exceeds_count} EXCEEDS (>1000)")
    print("-" * 88)
    print(f"{'STATUS':<10} {'LINES':<8} {'CODE':<8} {'CLASSES':<8} {'FUNCS':<8} {'MODULE PATH'}")
    print("-" * 88)

    for s in structures:
        if s.total_lines > hard_ceiling:
            badge = "[EXCEEDS]"
        elif s.total_lines > warn_threshold:
            badge = "[WARN]"
        else:
            badge = "[OK]"

        class_count = len(s.classes)
        func_count = len(s.functions)
        print(f"{badge:<10} {s.total_lines:<8} {s.code_lines:<8} {class_count:<8} {func_count:<8} {s.rel_path}")

    print("=" * 88)

    if exceeds_count > 0:
        print(f"\nACTION REQUIRED: {exceeds_count} module(s) exceed the {hard_ceiling}-line hard ceiling.")
        print("Run 'python scripts/modular_audit.py --suggest <file>' to generate automated decomposition blueprints.\n")
    else:
        print("\nAll modules comply with the 1,000-line modular ceiling.\n")


def check_budget_guard(
    structures: List[ModuleStructure],
    hard_ceiling: int = DEFAULT_HARD_CEILING,
    warn_threshold: int = DEFAULT_WARN_THRESHOLD,
    exempt_paths: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Programmatic budget check suitable for test runner and CI pipelines."""
    exempt = exempt_paths or set()
    violations = []
    warnings = []

    for s in structures:
        if s.rel_path in exempt or s.file_path.name in exempt:
            continue

        if s.total_lines > hard_ceiling:
            plan = DecompositionPlan(s)
            violations.append({
                "path": s.rel_path,
                "lines": s.total_lines,
                "suggested_submodules": [sub["filename"] for sub in plan.proposed_submodules],
            })
        elif s.total_lines > warn_threshold:
            warnings.append({
                "path": s.rel_path,
                "lines": s.total_lines,
            })

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "total_scanned": len(structures),
    }


def check_single_responsibility(
    structure: ModuleStructure,
    strict: bool = False,
) -> Dict[str, Any]:
    """Analyzes AST domain classification to verify Single Responsibility & Domain Separation.

    Verifies that the module does not mix incompatible desktop architectural domains:
      - UI presentation (QWidget, QDialog, QMainWindow, paint/layout)
      - Background worker concurrency (QThread, QRunnable, Worker)
      - Headless engine processing (audio/video, transcription, diarization, DSP)
      - Data models & state serialization (schemas, dataclasses, export format engines)
    """
    domain_counts: Dict[str, int] = defaultdict(int)
    classes_by_domain: Dict[str, List[str]] = defaultdict(list)
    funcs_by_domain: Dict[str, List[str]] = defaultdict(list)

    for c in structure.classes:
        classes_by_domain[c["domain"]].append(c["name"])
        domain_counts[c["domain"]] += 1

    for f in structure.functions:
        funcs_by_domain[f["domain"]].append(f["name"])
        domain_counts[f["domain"]] += 1

    collisions: List[str] = []

    # 1. UI presentation co-located with heavy headless engine logic
    has_ui = bool(classes_by_domain.get("ui"))
    has_engine = bool(classes_by_domain.get("engine"))
    if has_ui and has_engine:
        collisions.append("UI presentation co-located with Headless Audio/Processing Engine")

    # 2. UI presentation co-located with background worker thread definitions
    has_worker = bool(classes_by_domain.get("worker"))
    if has_ui and has_worker:
        collisions.append("UI presentation co-located with Background QThread Worker logic")

    # 3. UI presentation co-located with data models in large files (>400 lines)
    has_model = bool(classes_by_domain.get("model"))
    if has_ui and has_model and structure.total_lines > 400:
        collisions.append("UI presentation co-located with Data Model entities in a large file (>400 lines)")

    # 4. Background worker coordination co-located with direct engine computation
    if has_worker and has_engine:
        collisions.append("Background Worker coordination co-located with direct Engine implementation")

    # 5. Multiple distinct top-level dialogs in a single file (>2 dialogs)
    dialog_classes = [c["name"] for c in structure.classes if "dialog" in c["name"].lower() and "base" not in c["name"].lower()]
    if len(dialog_classes) > 2:
        collisions.append(f"Multiple top-level dialogs in single file ({len(dialog_classes)} dialogs: {', '.join(dialog_classes)})")

    # 6. Multi-domain sprawl (>= 3 distinct non-utils domains)
    non_utils_domains = [d for d in domain_counts if d != "utils" and domain_counts[d] > 0]
    if len(non_utils_domains) >= 3:
        collisions.append(f"Multi-domain sprawl across {len(non_utils_domains)} domains ({', '.join(non_utils_domains)})")

    # Primary domain calculation
    primary_domain = "utils"
    if domain_counts:
        primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0]

    is_facade = len(structure.classes) == 0 and len(structure.functions) == 0 and len(structure.imports) > 0
    if is_facade:
        collisions = []
        primary_domain = "facade"

    norm_rel = structure.rel_path.replace("\\", "/")
    is_legacy = (
        norm_rel in GRANDFATHERED_LEGACY_MODULES
        or structure.file_path.name in GRANDFATHERED_LEGACY_MODULES
        or any(norm_rel == m or norm_rel.endswith("/" + m) for m in GRANDFATHERED_LEGACY_MODULES)
    )

    is_compliant = len(collisions) == 0
    passed = is_compliant or (is_legacy and not strict)

    return {
        "path": structure.rel_path,
        "primary_domain": primary_domain,
        "domain_counts": dict(domain_counts),
        "classes_by_domain": dict(classes_by_domain),
        "funcs_by_domain": dict(funcs_by_domain),
        "collisions": collisions,
        "is_facade": is_facade,
        "is_legacy": is_legacy,
        "is_compliant": is_compliant,
        "passed": passed,
        "total_lines": structure.total_lines,
    }


def print_srp_report(results: List[Dict[str, Any]], strict: bool = False) -> bool:
    """Prints a structured terminal report for Single Responsibility & Domain Separation."""
    total = len(results)
    compliant = [r for r in results if r["is_compliant"]]
    legacy_collisions = [r for r in results if not r["is_compliant"] and r["is_legacy"]]
    new_violations = [r for r in results if not r["is_compliant"] and not r["is_legacy"]]

    print("=" * 88)
    print("RADIO & TV STORY SEGMENTER — SINGLE RESPONSIBILITY & DOMAIN SEPARATION AUDIT")
    print("=" * 88)
    print("Architectural Domain Boundaries:")
    print("  1. UI Presentation:      Widgets, dialogs, views, canvas, layout (no heavy compute/engines)")
    print("  2. Concurrency/Workers:  QThread lifecycle, background runners, cancellation (no GUI widgets)")
    print("  3. Headless Engines:     Audio/video decoding, transcription, diarization, DSP pipelines")
    print("  4. Models/Serialization: Schemas, dataclasses, export format engines, state snapshots")
    print("-" * 88)
    print(f"Total Modules Scanned:    {total}")
    print(f"Single-Purpose Compliant: {len(compliant)}")
    print(f"Grandfathered Legacy:     {len(legacy_collisions)} (tracked for incremental decomposition in roadmap)")
    print(f"New Unexempted Collisions:{len(new_violations)}")
    print("=" * 88)

    if new_violations:
        print("\n[FAIL] NEW SINGLE RESPONSIBILITY VIOLATIONS DETECTED:")
        for r in new_violations:
            print(f"\n  File: {r['path']} ({r['total_lines']} lines, Primary Domain: {r['primary_domain'].upper()})")
            for col in r["collisions"]:
                print(f"    - Collision: {col}")
            print("    Suggested Fix: Split into dedicated submodules and export via facade pattern.")
        print("")

    if legacy_collisions:
        print(f"\n[INFO] {len(legacy_collisions)} Grandfathered Legacy Monoliths with Multi-Domain Overlap:")
        for r in legacy_collisions:
            cols_str = "; ".join(r["collisions"])
            print(f"  - {r['path']:<35} ({r['total_lines']:>4} lines) -> {cols_str}")
        print("\nNote: Legacy monoliths are protected by .pyi stubs and prioritized in roadmap.txt Section 3.")

    if not new_violations:
        if strict and legacy_collisions:
            print("\n[FAIL] Strict mode enabled: Legacy multi-domain technical debt must be resolved.\n")
            return False
        print("\n[PASS] Single Responsibility & Domain Separation Invariants verified successfully.\n")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="AST Decomposition Suggester & Modular Budget Guard.")
    parser.add_argument("--audit", action="store_true", help="Audit all modules and print compliance table.")
    parser.add_argument("--suggest", type=str, metavar="FILE", help="Generate decomposition blueprint for target file.")
    parser.add_argument("--budget-guard", action="store_true", help="Run budget guard verification (exit code 1 on violations).")
    parser.add_argument(
        "--check-srp",
        "--responsibility-check",
        dest="check_srp",
        nargs="?",
        const="ALL",
        metavar="FILE",
        help="Audit Single Responsibility & Domain Separation for target FILE or all repository modules.",
    )
    parser.add_argument("--strict", action="store_true", help="Enforce strict compliance without legacy exemptions.")
    parser.add_argument("--warn-threshold", type=int, default=DEFAULT_WARN_THRESHOLD, help="Warning threshold lines (default: 800).")
    parser.add_argument("--hard-ceiling", type=int, default=DEFAULT_HARD_CEILING, help="Hard ceiling lines (default: 1000).")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    # 1. Suggest Mode
    if args.suggest:
        target = Path(args.suggest).resolve()
        if not target.exists():
            print(f"Error: Target file not found: {args.suggest}", file=sys.stderr)
            sys.exit(1)

        struct = ModuleStructure(target)
        if struct.parse_error:
            print(f"Error: {struct.parse_error}", file=sys.stderr)
            sys.exit(1)

        plan = DecompositionPlan(struct)
        if args.json:
            data = {
                "file": struct.rel_path,
                "total_lines": struct.total_lines,
                "proposed_submodules": plan.proposed_submodules,
                "facade_exports": plan.facade_exports,
                "dead_code_candidates": plan.dead_code_candidates,
            }
            print(json.dumps(data, indent=2))
        else:
            print(plan.render_markdown_blueprint())
        return

    # 2. Single Responsibility & Domain Separation Check Mode
    if args.check_srp:
        if args.check_srp != "ALL":
            target = Path(args.check_srp)
            if not target.is_absolute():
                target = (ROOT_DIR / target).resolve()
            if not target.exists():
                print(f"Error: Target file not found: {args.check_srp}", file=sys.stderr)
                sys.exit(1)
            struct = ModuleStructure(target)
            if struct.parse_error:
                print(f"Error: {struct.parse_error}", file=sys.stderr)
                sys.exit(1)
            res = check_single_responsibility(struct, strict=args.strict)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                passed = print_srp_report([res], strict=args.strict)
                sys.exit(0 if passed else 1)
            return

        structures = scan_repository(ROOT_DIR)
        results = [check_single_responsibility(s, strict=args.strict) for s in structures]
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            passed = print_srp_report(results, strict=args.strict)
            sys.exit(0 if passed else 1)
        return

    # 3. Repository Scan (Audit or Budget Guard)
    structures = scan_repository(ROOT_DIR)

    if args.budget_guard:
        result = check_budget_guard(structures, hard_ceiling=args.hard_ceiling, warn_threshold=args.warn_threshold)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["passed"]:
                print(f"[PASS] All {result['total_scanned']} modules comply with the {args.hard_ceiling}-line ceiling.")
                sys.exit(0)
            else:
                print(f"[FAIL] {len(result['violations'])} module(s) exceed the {args.hard_ceiling}-line ceiling:")
                for v in result["violations"]:
                    print(f"  - {v['path']}: {v['lines']:,} lines -> Suggested split: {', '.join(v['suggested_submodules'])}")
                sys.exit(1)
        return

    # Default / Audit Mode
    if args.json:
        data = [
            {
                "path": s.rel_path,
                "lines": s.total_lines,
                "code": s.code_lines,
                "classes": len(s.classes),
                "functions": len(s.functions),
            }
            for s in structures
        ]
        print(json.dumps(data, indent=2))
    else:
        print_audit_report(structures, warn_threshold=args.warn_threshold, hard_ceiling=args.hard_ceiling)


if __name__ == "__main__":
    main()

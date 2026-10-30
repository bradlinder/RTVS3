"""
scripts/ide_config.py - Token-Thrifty IDE Configuration & Rule Provisioner
Milestone 2.4: Token-Thrift IDE Configuration & AST Suggester Integration

Generates tuned configurations for Continue, Cline, Cursor, and VS Code, enforcing
symbol-first range reads, diff-only edits, line budgets, and local Ollama model routing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_vscode_settings() -> Dict[str, Any]:
    return {
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.diagnosticSeverityOverrides": {
            "reportMissingImports": "warning",
            "reportUndefinedVariable": "error",
        },
        "python.analysis.extraPaths": [
            ".",
            "plugins",
            "plugins/wordpress",
            "plugins/youtube",
            "plugins/translation",
        ],
        "editor.formatOnSave": False,
        "editor.tabSize": 4,
        "editor.insertSpaces": True,
        "files.exclude": {
            "**/.git": True,
            "**/.snapshots": True,
            "**/.archive": True,
            "**/__pycache__": True,
            "**/*.pyc": True,
            "**/*.egg-info": True,
            "**/.pytest_cache": True,
        },
        "search.exclude": {
            "**/.git": True,
            "**/.snapshots": True,
            "**/.archive": True,
            "**/CHANGELOG_ARCHIVE.md": True,
            "**/*.pyc": True,
        },
    }


def build_continue_config() -> Dict[str, Any]:
    return {
        "models": [
            {
                "title": "Smart Router (Autonomous NL Dispatcher)",
                "provider": "openai",
                "model": "rtvs-smart-router",
                "apiBase": "http://127.0.0.1:8000/v1",
                "apiKey": "local-no-key",
            },
            {
                "title": "Lead Architect & Refactor (Qwen 3.8 27B)",
                "provider": "ollama",
                "model": "qwen3.8-27b",
                "apiBase": "http://127.0.0.1:11434",
            },
            {
                "title": "Fast Chat & Debug (Qwen 3 14B)",
                "provider": "ollama",
                "model": "qwen3:14b",
                "apiBase": "http://127.0.0.1:11434",
            },
            {
                "title": "Surgical Diff & Patch (Qwen 2.5 Coder 32B)",
                "provider": "ollama",
                "model": "qwen2.5-coder:32b",
                "apiBase": "http://127.0.0.1:11434",
            },
            {
                "title": "Deep Reasoning & Concurrency (R1 14B)",
                "provider": "ollama",
                "model": "deepseek-r1:14b",
                "apiBase": "http://127.0.0.1:11434",
            },
            {
                "title": "Targeted Bug Fixes (Qwen 3.5 9B)",
                "provider": "ollama",
                "model": "qwen3.5:9b",
                "apiBase": "http://127.0.0.1:11434",
            },
            {
                "title": "UI & Screenshot Inspector (MiniCPM-V)",
                "provider": "ollama",
                "model": "minicpm-v:latest",
                "apiBase": "http://127.0.0.1:11434",
            },
        ],
        "tabAutocompleteModel": {
            "title": "Autocomplete (Qwen 1.5B FIM)",
            "provider": "ollama",
            "model": "qwen2.5-coder:1.5b",
            "apiBase": "http://127.0.0.1:11434",
        },
        "embeddingsProvider": {
            "provider": "ollama",
            "model": "nomic-embed-text",
            "apiBase": "http://127.0.0.1:11434",
        },
        "customCommands": [
            {
                "name": "audit",
                "prompt": "Run python scripts/modular_audit.py --suggest on {{{ input }}} and generate an AST-driven decomposition blueprint.",
                "description": "Suggest AST modular decomposition for files approaching 850 lines.",
            },
            {
                "name": "verify",
                "prompt": "Run python test_runner.py --quiet to run Tier 2 change-aware diagnostic tests.",
                "description": "Execute change-aware diagnostic test suite.",
            },
            {
                "name": "symbols",
                "prompt": "Consult .codemaps/INDEX.md to find class and method line ranges for {{{ input }}} before reading full files.",
                "description": "Find targeted symbol ranges.",
            },
        ],
        "contextProviders": [
            {"name": "codebase", "params": {}},
            {"name": "diff", "params": {}},
            {"name": "terminal", "params": {}},
            {"name": "open", "params": {}},
        ],
    }


def build_cline_rules() -> str:
    return """# Radio & TV Story Segmenter — AI Coding Directives & Token-Thrift Guidelines

## 1. Symbol-First Range Reads (Token Optimization)
- NEVER read entire source files exceeding 150 lines into context.
- Before inspecting or editing any large file, consult `.codemaps/INDEX.md` or `.codemaps/symbol_index.json` to identify exact class and function line ranges.
- View only that targeted line slice using range reads.

## 2. Monolithic File Budget Invariants (Rule 10)
- Python source files SHOULD be kept under 800 lines and MUST NOT exceed 1,000 lines.
- When implementing new feature logic, create dedicated submodules in appropriate sub-packages rather than appending code to large files.
- If any file approaches 850 lines, run `python scripts/modular_audit.py --suggest <file>` to generate an AST decomposition blueprint.
- Preserve backward compatibility 100% by re-exporting public classes/functions in the original module facade.

## 3. Targeted Contiguous Diffs
- Never rewrite or overwrite entire source files to apply a bug fix or feature.
- Use minimal, drop-in contiguous replacements.

## 4. UI Design Discipline: Ban on Unrequested Emojis / Decorative Icons
- Do NOT add icons or emoji symbols (such as folders, checkmarks, warning signs, or decorative unicode glyphs) to tabs, buttons, dialog titles, menus, table headers, or cards unless explicitly requested by the user.
- Maintain clean, native desktop typography.

## 5. Architectural Invariants
- Core modules (`RadioTVSegmenter.py`, `processing.py`, `runtime_manager.py`) must NEVER import from `plugins/`.
- Heavy AI/translation runtimes remain isolated inside `plugins/translation/`.
- Speaker diarization uses `wespeakerruntime` as the primary ONNX embedding engine.

## 6. Diagnostic Hierarchy (Three-Tier Discipline)
- Routine turn-by-turn verification must use Tier 1 (`python test_runner.py --quiet --filter "<keyword>"`) or Tier 2 (`python test_runner.py --quiet`).
- Full runs (`--all`) are strictly reserved for release audits.

## 7. Autonomous Smart Router & Antigravity Setup
- Start proxy: `python scripts/task_router.py --serve-proxy` (runs on http://127.0.0.1:8000/v1).
- Use model: `rtvs-smart-router` in Cline / Continue / Antigravity for zero-friction natural language routing.
- Automatically dispatches to Qwen3.8-27B (refactoring), Qwen2.5-Coder:32B (surgical diffs), Qwen3:14B (chat), or DeepSeek-R1 (proofs).
"""


def setup_all_ide_configs(workspace_root: Path = Path(".")) -> Dict[str, str]:
    created: Dict[str, str] = {}

    # 1. .vscode/settings.json
    vscode_dir = workspace_root / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    vscode_file = vscode_dir / "settings.json"
    vscode_file.write_text(json.dumps(build_vscode_settings(), indent=2), encoding="utf-8")
    created[str(vscode_file)] = "Configured Python analysis, search exclusions & IDE defaults"

    # 2. .continue/config.json
    continue_dir = workspace_root / ".continue"
    continue_dir.mkdir(parents=True, exist_ok=True)
    continue_file = continue_dir / "config.json"
    continue_file.write_text(json.dumps(build_continue_config(), indent=2), encoding="utf-8")
    created[str(continue_file)] = "Configured Continue coding assistant with tiered Ollama models & slash commands"

    # 3. .clinerules
    cline_file = workspace_root / ".clinerules"
    cline_file.write_text(build_cline_rules(), encoding="utf-8")
    created[str(cline_file)] = "Enforced symbol-first reads, 800-line budget ceiling & token-thrift rules for Cline"

    # 4. .cursorrules
    cursor_file = workspace_root / ".cursorrules"
    cursor_file.write_text(build_cline_rules(), encoding="utf-8")
    created[str(cursor_file)] = "Enforced symbol-first reads, 800-line budget ceiling & token-thrift rules for Cursor"

    return created

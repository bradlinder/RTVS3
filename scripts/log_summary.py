#!/usr/bin/env python3
"""log_summary.py — Compact Error & Exception Extraction Engine

Parses verbose console logs, crash traces, and Python/Qt exceptions into token-dense summaries.
Filters out standard library and C++/PySide6 internal frames, isolating the application call chain,
failing source lines, and root cause exception in <15 lines.

Usage:
    python scripts/log_summary.py <path_to_log>
    python scripts/log_summary.py "Traceback (most recent call last)..."
    cat error.log | python scripts/log_summary.py
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

FRAME_REGEX = re.compile(r'^\s*File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+([^\n]+)')
CODE_LINE_REGEX = re.compile(r'^\s{4,}(.+)$')
EXCEPTION_REGEX = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_.]*(?:Error|Exception|Warning|Exit|Interrupt|Fault)):\s*(.*)$')
TIMESTAMP_HEADER_REGEX = re.compile(r'^\[(\d{4}-\d{2}-\d{2}[^\]]+)\]\s+\[([^\]]+)\]\s+([^\n]+)')

IGNORED_FRAME_SUBSTRINGS = [
    "lib/python",
    "site-packages/PySide6",
    "site-packages/shiboken6",
    "importlib",
    "unittest",
    "threading.py",
]

def is_project_frame(filepath: str) -> bool:
    """Determine if a file path belongs to the application rather than external/standard libraries."""
    for ignored in IGNORED_FRAME_SUBSTRINGS:
        if ignored in filepath.replace("\\", "/"):
            return False
    return True

def extract_log_summary(raw_log: str) -> str:
    """Extract a high-density summary from a raw log or traceback string."""
    lines = raw_log.strip().splitlines()
    if not lines:
        return "[LOG SUMMARY] Empty log input."

    timestamp_hdr = None
    frames: List[Tuple[str, str, str, str]] = []  # (filename, line, func, code_line)
    exception_type = None
    exception_msg = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for [YYYY-MM-DD HH:MM:SS] [CRASH/EXCEPTION] header
        m_hdr = TIMESTAMP_HEADER_REGEX.match(line)
        if m_hdr:
            timestamp_hdr = f"[{m_hdr.group(1)}] [{m_hdr.group(2)}] {m_hdr.group(3)}"
            i += 1
            continue

        # Check for stack frames
        m_frame = FRAME_REGEX.match(line)
        if m_frame:
            f_path, f_line, f_func = m_frame.group(1), m_frame.group(2), m_frame.group(3)
            code_line = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                m_code = CODE_LINE_REGEX.match(next_line)
                if m_code and not FRAME_REGEX.match(next_line):
                    code_line = m_code.group(1).strip()
                    i += 1
            frames.append((f_path, f_line, f_func, code_line))
            i += 1
            continue

        # Check for trailing exception
        m_exc = EXCEPTION_REGEX.match(line.strip())
        if m_exc:
            exception_type = m_exc.group(1)
            exception_msg = m_exc.group(2).strip()

        i += 1

    # Filter frames for application scope
    project_frames = [f for f in frames if is_project_frame(f[0])]
    display_frames = project_frames if project_frames else frames

    out: List[str] = []
    out.append("=" * 65)
    out.append(" COMPACT ERROR & EXCEPTION SUMMARY")
    out.append("=" * 65)

    if timestamp_hdr:
        out.append(f"Event Context: {timestamp_hdr}")

    if exception_type:
        out.append(f"Exception:     {exception_type}: {exception_msg}")
    else:
        # Fallback: last non-empty line
        for l in reversed(lines):
            if l.strip():
                out.append(f"Last Trace:    {l.strip()}")
                break

    out.append("Application Call Trace (Project Frames Only):")
    if display_frames:
        for idx, (f_path, f_line, f_func, code) in enumerate(display_frames, 1):
            short_path = Path(f_path).name
            parent = Path(f_path).parent.name
            rel = f"{parent}/{short_path}" if parent and parent != "." else short_path
            out.append(f"  {idx:02d}. {rel}:{f_line} in {f_func}")
            if code:
                out.append(f"      -> {code}")
    else:
        out.append("  (No Python traceback frames identified)")

    if display_frames:
        failing_file, failing_line, failing_func, code = display_frames[-1]
        out.append("-" * 65)
        out.append(f"Root Failure Location: {failing_file}:{failing_line} ({failing_func})")
        if code:
            out.append(f"Failing Statement:     {code}")
    out.append("=" * 65)

    return "\n".join(out)

def main():
    raw_input = ""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            raw_input = Path(arg).read_text(encoding="utf-8", errors="replace")
        else:
            raw_input = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()

    if not raw_input.strip():
        print("Usage: python scripts/log_summary.py <path_to_log | 'error text'>")
        print("       cat crash.log | python scripts/log_summary.py")
        return 1

    print(extract_log_summary(raw_input))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

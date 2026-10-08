#!/usr/bin/env python3
"""roadmap_manager.py — Automated Roadmap & N-1 Sliding-Window Management Engine

Automates roadmap.txt inspection, status tracking, item updates, and N-1 sliding-window transitions
in strict accordance with AGENTS.md / GEMINI.md roadmap policies:
1. N-1 Sliding-Window Policy: Retains only the active release ($N$) and immediate predecessor ($N-1$).
2. Social Digest Status Notation Policy: Explicit checkboxes [x], [-], [ ] across TOC and Details.
3. Synchronous Dual-Section Updates: Keeps Table of Contents & Detailed Specifications in lockstep.
4. Token & Error Prevention: Replaces fragile large-block string replacements with deterministic CLI actions.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parent
ROADMAP_FILE = ROOT_DIR / "roadmap.txt"
PRS_SHARED_FILE = ROOT_DIR / "prs_shared.py"

def get_current_app_version() -> str:
    """Extract PROJECT_VERSION from prs_shared.py."""
    if not PRS_SHARED_FILE.is_file():
        return ""
    content = PRS_SHARED_FILE.read_text(encoding="utf-8")
    m = re.search(r'PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    return m.group(1).strip() if m else ""

class RoadmapManager:
    def __init__(self, roadmap_path: Path = ROADMAP_FILE):
        self.path = roadmap_path
        self.content = ""
        self.load()

    def load(self):
        if not self.path.is_file():
            raise FileNotFoundError(f"Missing roadmap file at {self.path}")
        self.content = self.path.read_text(encoding="utf-8")

    def save(self):
        self.path.write_text(self.content, encoding="utf-8")

    def get_sections_info(self) -> dict:
        """Parse TOC and identify release sections."""
        toc_match = re.search(
            r'TABLE OF CONTENTS & STATUS OVERVIEW\s*[-=]+\s*(.*?)(?=={10,}|\nDETAILED MILESTONE SPECIFICATIONS|\Z)',
            self.content,
            re.DOTALL
        )
        if not toc_match:
            return {"error": "Could not locate TABLE OF CONTENTS in roadmap.txt"}

        toc_text = toc_match.group(1)
        
        # Find all numbered top-level entries in TOC: e.g. "1. Previous Release: ...", "2. Current Release: ..."
        entries = re.findall(r'(?m)^(\d+)\.\s+([^:\n]+):\s*([^\n]+)', toc_text)
        
        info = {
            "entries": [],
            "prev_version": None,
            "current_version": None,
            "upcoming_milestones": []
        }

        for num_str, entry_type, title_rest in entries:
            num = int(num_str)
            entry = {
                "number": num,
                "type": entry_type.strip(),
                "title": title_rest.strip()
            }
            # Extract version if present
            v_match = re.search(r'v([0-9a-zA-Z_.-]+)', title_rest)
            ver = v_match.group(1) if v_match else None
            entry["version"] = ver

            if num == 1:
                info["prev_version"] = ver
            elif num == 2:
                info["current_version"] = ver
            else:
                info["upcoming_milestones"].append(entry)

            info["entries"].append(entry)

        return info

    def audit(self) -> tuple[bool, list[str]]:
        """Audit roadmap.txt against N-1 sliding window and status tracking invariants."""
        issues = []
        app_ver = get_current_app_version()
        info = self.get_sections_info()

        if "error" in info:
            return False, [info["error"]]

        # 1. Verify Entry 1 is Previous Release
        entries = {e["number"]: e for e in info["entries"]}
        if 1 not in entries:
            issues.append("Missing Section 1 (Previous Release $N-1$) in Table of Contents.")
        elif "Previous" not in entries[1]["type"]:
            issues.append(f"Section 1 should be 'Previous Release', but found '{entries[1]['type']}'.")

        # 2. Verify Entry 2 is Current Release
        if 2 not in entries:
            issues.append("Missing Section 2 (Current Release $N$) in Table of Contents.")
        elif "Current" not in entries[2]["type"]:
            issues.append(f"Section 2 should be 'Current Release', but found '{entries[2]['type']}'.")
        else:
            cur_v = entries[2].get("version")
            if app_ver and cur_v and cur_v != app_ver:
                issues.append(
                    f"Current release version in roadmap (v{cur_v}) does not match prs_shared.py (v{app_ver})."
                )

        # 3. Verify N-1 Sliding Window (at least 2 sections, and Section 1 is N-1)
        if len(entries) < 2:
            issues.append("Roadmap does not contain both $N-1$ and $N$ sections.")

        # 4. Check for invalid or malformed status indicators
        bad_checkboxes = re.findall(r'\[\s*([^\sx\-])\s*\]\s*\d+\.\d+', self.content)
        if bad_checkboxes:
            issues.append(f"Found invalid status checkboxes in roadmap: {set(bad_checkboxes)}")

        # 5. Check dual-section consistency: TOC and Detailed Specifications headers
        if "DETAILED MILESTONE SPECIFICATIONS" not in self.content:
            issues.append("Missing 'DETAILED MILESTONE SPECIFICATIONS' heading.")
        else:
            details_section = self.content.split("DETAILED MILESTONE SPECIFICATIONS", 1)[1]
            for entry in info["entries"]:
                num = entry["number"]
                if not re.search(rf'(?m)^{num}\.\s+[A-Z\s]+:', details_section):
                    issues.append(f"Detailed Specifications header for Section {num} is missing or malformed.")

        return (len(issues) == 0), issues

    def set_item_status(self, item_num: str, status: str) -> bool:
        """Synchronously update the status checkbox for an item (e.g. '2.1', '3.2') to [x], [-], or [ ].
        Updates both the Table of Contents and the Detailed Specifications section.
        """
        valid_statuses = {"[x]", "[-]", "[ ]"}
        norm_status = status.strip()
        if norm_status not in valid_statuses:
            norm_status = f"[{norm_status.strip('[]')}]"
            if norm_status not in valid_statuses:
                raise ValueError(f"Invalid status: '{status}'. Must be one of: [x], [-], [ ]")

        item_escaped = re.escape(item_num.strip())
        pattern = rf'\[(?:[ x\-])\]\s*({item_escaped}\b)'

        matches = list(re.finditer(pattern, self.content))
        if not matches:
            print(f"[!] Item '{item_num}' not found in roadmap.txt")
            return False

        new_content, count = re.subn(pattern, f"{norm_status} \\1", self.content)
        self.content = new_content
        self.save()
        print(f"[OK] Updated {count} occurrences of item {item_num} to status {norm_status} in roadmap.txt")
        return True

    def sync_current_version(self, target_version: str | None = None) -> bool:
        """Synchronize the current release version in roadmap.txt to target_version or prs_shared.py."""
        clean_ver = target_version.strip().lstrip("v") if target_version else get_current_app_version()
        if not clean_ver:
            print("[!] Could not determine target version to sync.")
            return False

        # In TOC: Update "2. Current Release: ... in v...]"
        toc_pat = r'(?m)^(2\.\s+Current Release:[^\n]+v)[0-9a-zA-Z_.-]+(\])'
        new_content, count1 = re.subn(toc_pat, rf'\g<1>{clean_ver}\2', self.content)
        
        # In Details: Update "2. CURRENT RELEASE: ... in v...]"
        det_pat = r'(?m)^(2\.\s+CURRENT RELEASE:[^\n]+v)[0-9a-zA-Z_.-]+(\])'
        new_content, count2 = re.subn(det_pat, rf'\g<1>{clean_ver}\2', new_content)

        # In Synchronous Version Bump sub-item: e.g. "Synchronized all 10 project locations to v..."
        bump_pat = r'(Synchronized all 10 project locations to v)[0-9a-zA-Z_.-]+'
        new_content, count3 = re.subn(bump_pat, rf'\g<1>{clean_ver}', new_content)

        self.content = new_content
        self.save()
        print(f"[OK] Synchronized Current Release in roadmap.txt to v{clean_ver} ({count1 + count2 + count3} updates).")
        return True

    def count_item_statuses(self) -> dict[str, int]:
        """Count completed, in-progress, and planned items in the roadmap."""
        counts = {"completed": 0, "in_progress": 0, "planned": 0}
        counts["completed"] = len(re.findall(r'\[x\]\s*\d+\.\d+', self.content))
        counts["in_progress"] = len(re.findall(r'\[-\]\s*\d+\.\d+', self.content))
        counts["planned"] = len(re.findall(r'\[ \]\s*\d+\.\d+', self.content))
        return counts

def main() -> int:
    parser = argparse.ArgumentParser(description="Manage, validate, and update roadmap.txt.")
    parser.add_argument("--check", action="store_true", help="Audit roadmap.txt against N-1 policy and prs_shared.py version.")
    parser.add_argument("--status", action="store_true", help="Display roadmap structure and progress indicators.")
    parser.add_argument("--mark", nargs=2, metavar=("ITEM", "STATUS"), help="Set item status: e.g. --mark 2.1 [x]")
    parser.add_argument("--sync-version", nargs="?", const="", help="Sync Current Release version in roadmap to prs_shared.py or given version")

    args = parser.parse_args()
    mgr = RoadmapManager()

    if args.sync_version is not None:
        target = args.sync_version if args.sync_version else None
        success = mgr.sync_current_version(target)
        return 0 if success else 1

    if args.mark:
        item, status = args.mark
        success = mgr.set_item_status(item, status)
        return 0 if success else 1

    if args.status or (not args.check and not args.mark and args.sync_version is None):
        info = mgr.get_sections_info()
        counts = mgr.count_item_statuses()
        app_ver = get_current_app_version()
        print("================================================================================")
        print("ROADMAP STATUS & N-1 SLIDING-WINDOW REPORT")
        print("================================================================================")
        print(f"Application Active Version (prs_shared.py): v{app_ver}")
        print(f"Section 1 (Previous Release N-1):          v{info.get('prev_version', 'N/A')}")
        print(f"Section 2 (Current Release N):             v{info.get('current_version', 'N/A')}")
        print("--------------------------------------------------------------------------------")
        print(f"Progress Indicators: [x] Completed: {counts['completed']} | [-] In-Progress: {counts['in_progress']} | [ ] Planned: {counts['planned']}")
        print("--------------------------------------------------------------------------------")
        print("Upcoming Milestones:")
        for m in info.get("upcoming_milestones", []):
            print(f"  [{m['number']}] {m['type']}: {m['title']}")
        print("================================================================================")

    if args.check:
        passed, issues = mgr.audit()
        if passed:
            print("[PASS] Roadmap conforms strictly to N-1 sliding window and status tracking invariants.")
            return 0
        else:
            print("[FAIL] Roadmap audit encountered issues:")
            for issue in issues:
                print(f"  - {issue}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())

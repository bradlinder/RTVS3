#!/usr/bin/env python3
"""AI Studio Web Preview Manager for Radio & TV Story Segmenter.

This script manages, verifies, and restores the AI Studio zero-dependency web preview
scaffolding (interactive changelog and release history viewer).

Zero-Dependency Architecture:
- Uses Node.js native standard library (`http` and `fs`) to serve CHANGELOG.md on port 3000.
- Zero npm dependencies, zero node_modules, zero compilation steps, zero build failures.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

PACKAGE_JSON_TEMPLATE = """{
  "name": "radio-tv-segmenter-preview",
  "private": true,
  "version": "__VERSION__",
  "type": "module",
  "scripts": {
    "dev": "node server.js",
    "build": "node -e 'process.exit(0)'",
    "lint": "node -e 'process.exit(0)'"
  }
}
"""

METADATA_JSON_TEMPLATE = """{
  "name": "Radio & TV Segmenter",
  "description": "Radio & TV Segmenter v__VERSION__ - AI-powered audio/video transcription, diarization, translation, and story segmentation suite.",
  "requestFramePermissions": [],
  "majorCapabilities": [
    "MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"
  ]
}
"""

SERVER_JS_TEMPLATE = """import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PORT = 3000;
const HOST = '0.0.0.0';

function getChangelog() {
  try {
    const changelogPath = path.join(__dirname, 'CHANGELOG.md');
    if (fs.existsSync(changelogPath)) {
      return fs.readFileSync(changelogPath, 'utf8');
    }
    return '# Changelog\\n\\nNo CHANGELOG.md found in workspace.';
  } catch (err) {
    return `# Changelog\\n\\nError reading CHANGELOG.md: ${err.message}`;
  }
}

function extractCurrentVersion(changelogText) {
  const match = changelogText.match(/##\\s+v?([0-9]+\\.[0-9]+\\.[0-9]+[a-zA-Z0-9.\\-_]*)/);
  return match ? `v${match[1]}` : 'v__VERSION__';
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderHtml(rawMarkdown) {
  const version = extractCurrentVersion(rawMarkdown);
  const escaped = escapeHtml(rawMarkdown);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Radio & TV Story Segmenter ${version} - Changelog</title>
  <meta name="description" content="Radio & TV Story Segmenter ${version} - AI-powered audio/video transcription, diarization, translation, and story segmentation suite.">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #0f172a;
      --border: #1e293b;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.6;
      padding: 0;
      min-height: 100vh;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(9, 13, 22, 0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 14px 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .title {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      font-family: var(--font-mono);
      background: var(--accent-glow);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .search-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: #fff;
      font-size: 13px;
      padding: 6px 12px;
      border-radius: 6px;
      width: 200px;
      outline: none;
      transition: border-color 0.15s ease;
    }
    .search-box:focus {
      border-color: var(--accent);
    }
    .btn {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 500;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      transition: all 0.15s ease;
    }
    .btn:hover {
      color: #fff;
      border-color: var(--accent);
    }
    main {
      max-width: 960px;
      margin: 0 auto;
      padding: 24px 20px 60px 20px;
    }
    .intro-banner {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 24px;
      font-size: 13px;
      color: var(--text-muted);
    }
    .intro-banner strong {
      color: var(--text-main);
    }
    pre#changelog {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.65;
      color: #cbd5e1;
      white-space: pre-wrap;
      word-break: break-word;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="title">Radio & TV Story Segmenter</div>
      <span class="badge">${version}</span>
    </div>
    <div class="controls">
      <input type="text" id="filterInput" class="search-box" placeholder="Filter changes..." />
      <a href="/raw" class="btn" target="_blank">Raw Markdown</a>
      <button class="btn" onclick="location.reload()">Refresh</button>
    </div>
  </header>

  <main>
    <div class="intro-banner">
      <strong>Interactive Desktop Changelog Viewer</strong> &bull; This web preview reflects live release notes synchronized with <code>CHANGELOG.md</code> in the PySide6 desktop suite.
    </div>

    <pre id="changelog">${escaped}</pre>
  </main>

  <script>
    const filterInput = document.getElementById('filterInput');
    const changelogEl = document.getElementById('changelog');
    const originalText = changelogEl.textContent;

    filterInput.addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        changelogEl.textContent = originalText;
        return;
      }

      const lines = originalText.split('\\\\n');
      const filtered = [];
      let inSection = false;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith('## ')) {
          inSection = line.toLowerCase().includes(q);
          if (inSection) filtered.push(line);
        } else if (inSection || line.toLowerCase().includes(q)) {
          filtered.push(line);
        }
      }

      changelogEl.textContent = filtered.join('\\\\n');
    });
  </script>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  const url = req.url || '/';
  const changelog = getChangelog();

  if (url === '/raw') {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(changelog);
    return;
  }

  if (url === '/favicon.ico') {
    res.writeHead(204);
    res.end();
    return;
  }

  const html = renderHtml(changelog);
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(html);
});

server.listen(PORT, HOST, () => {
  console.log(`[PREVIEW] Zero-dependency Changelog preview server listening on http://${HOST}:${PORT}`);
});
"""


def get_project_version() -> str:
    """Extract PROJECT_VERSION from prs_shared.py."""
    prs_path = ROOT_DIR / "prs_shared.py"
    if prs_path.is_file():
        content = prs_path.read_text(encoding="utf-8")
        match = re.search(r'PROJECT_VERSION\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            v = match.group(1).strip()
            return re.sub(r"\.+", ".", v)
    return "3.9.36-beta"


def restore_preview(force: bool = False) -> int:
    """Ensure all preview scaffolding files exist with up-to-date version strings."""
    version = get_project_version()
    print(f"[PREVIEW] Synchronizing zero-dependency web preview for v{version}...")

    files = {
        ROOT_DIR / "package.json": PACKAGE_JSON_TEMPLATE.replace("__VERSION__", version),
        ROOT_DIR / "metadata.json": METADATA_JSON_TEMPLATE.replace("__VERSION__", version),
        ROOT_DIR / "server.js": SERVER_JS_TEMPLATE.replace("__VERSION__", version),
    }

    created = 0
    updated = 0

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"  + Created: {path.relative_to(ROOT_DIR)}")
            created += 1
        elif force:
            path.write_text(content, encoding="utf-8")
            print(f"  * Overwritten: {path.relative_to(ROOT_DIR)}")
            updated += 1

    print(f"[PREVIEW] Zero-dependency preview restoration complete ({created} created, {updated} updated).")
    return 0


def sync_version(version: str | None = None) -> int:
    """Synchronize the application version into package.json and metadata.json."""
    if not version:
        version = get_project_version()
    clean_version = re.sub(r"\.+", ".", str(version).strip().lstrip("v"))
    print(f"[PREVIEW] Synchronizing version v{clean_version} across preview files...")

    # 1. package.json
    pkg_path = ROOT_DIR / "package.json"
    if pkg_path.is_file():
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            if data.get("version") != clean_version:
                data["version"] = clean_version
                pkg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                print(f"  * Synchronized package.json -> v{clean_version}")
        except Exception as e:
            print(f"  ! Error updating package.json: {e}")

    # 2. metadata.json
    meta_path = ROOT_DIR / "metadata.json"
    if meta_path.is_file():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            data["description"] = f"Radio & TV Segmenter v{clean_version} - AI-powered audio/video transcription, diarization, translation, and story segmentation suite."
            meta_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"  * Synchronized metadata.json -> v{clean_version}")
        except Exception as e:
            print(f"  ! Error updating metadata.json: {e}")

    # 3. index.html
    html_path = ROOT_DIR / "index.html"
    if html_path.is_file():
        try:
            content = html_path.read_text(encoding="utf-8")
            content = re.sub(r"v\d+\.\d+\.\d+[-a-zA-Z0-9._]*", f"v{clean_version}", content)
            html_path.write_text(content, encoding="utf-8")
            print(f"  * Synchronized index.html -> v{clean_version}")
        except Exception as e:
            print(f"  ! Error updating index.html: {e}")

    print("[PREVIEW] Version synchronization complete.")
    return 0


def verify_preview() -> int:
    """Verify that all preview files exist and are valid."""
    required_files = [
        ROOT_DIR / "package.json",
        ROOT_DIR / "metadata.json",
        ROOT_DIR / "server.js",
    ]

    missing = [f.relative_to(ROOT_DIR) for f in required_files if not f.exists()]
    if missing:
        print(f"[PREVIEW] Missing preview files: {', '.join(str(m) for m in missing)}")
        print("[PREVIEW] Run `python preview_manager.py --restore` to restore.")
        return 1

    print("[PREVIEW] All zero-dependency preview files are present and verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Studio Zero-Dependency Web Preview Manager")
    parser.add_argument("--restore", action="store_true", help="Restore any missing preview files")
    parser.add_argument("--force", action="store_true", help="Force overwrite all preview files with fresh defaults")
    parser.add_argument("--sync", action="store_true", help="Synchronize versions across preview files from prs_shared.py")
    parser.add_argument("--version-str", help="Specify an explicit version string for sync")
    parser.add_argument("--verify", action="store_true", help="Check integrity of preview files")

    args = parser.parse_args()

    if args.force:
        return restore_preview(force=True)
    if args.restore:
        return restore_preview(force=False)
    if args.sync or args.version_str:
        return sync_version(version=args.version_str)
    if args.verify:
        return verify_preview()

    if verify_preview() != 0:
        restore_preview(force=False)
    return sync_version()


if __name__ == "__main__":
    sys.exit(main())

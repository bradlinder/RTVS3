#!/usr/bin/env python3
"""AI Studio Web Preview Manager for Radio & TV Story Segmenter.

Manages, verifies, and restores the ultra-lightweight zero-dependency web preview status card.
"""

from __future__ import annotations

import argparse
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

function getVersion() {
  try {
    const prs = fs.readFileSync(path.join(__dirname, 'prs_shared.py'), 'utf8');
    const m = prs.match(/PROJECT_VERSION\\s*=\\s*["']([^"']+)["']/);
    if (m) return m[1];
  } catch (e) {}
  return '__VERSION__';
}

const server = http.createServer((req, res) => {
  if (req.url === '/favicon.ico') {
    res.writeHead(204);
    res.end();
    return;
  }

  const version = getVersion();
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Radio & TV Story Segmenter v\${version}</title>
  <style>
    body {
      background: #090d16;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 36px 48px;
      border-radius: 12px;
      text-align: center;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    h1 { margin: 0 0 8px 0; font-size: 22px; color: #f8fafc; }
    .badge {
      display: inline-block;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    p { margin: 0; color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Radio & TV Story Segmenter</h1>
    <div class="badge">v\${version}</div>
    <p>Native PySide6 Desktop Application Suite</p>
  </div>
</body>
</html>`;

  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  });
  res.end(html);
});

server.listen(PORT, HOST, () => {
  console.log(`[PREVIEW] Server running on http://${HOST}:${PORT}`);
});
"""

INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Radio & TV Story Segmenter</title>
  <style>
    body {
      background: #090d16;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 36px 48px;
      border-radius: 12px;
      text-align: center;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    h1 { margin: 0 0 8px 0; font-size: 22px; color: #f8fafc; }
    .badge {
      display: inline-block;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    p { margin: 0; color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Radio & TV Story Segmenter</h1>
    <div class="badge">v__VERSION__</div>
    <p>Native PySide6 Desktop Application Suite</p>
  </div>
</body>
</html>
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
    return "3.9.40-beta"


def restore_preview(force: bool = False) -> int:
    """Ensure all preview scaffolding files exist with up-to-date version strings."""
    version = get_project_version()
    print(f"[PREVIEW] Synchronizing zero-dependency web preview for v{version}...")

    files = {
        ROOT_DIR / "package.json": PACKAGE_JSON_TEMPLATE.replace("__VERSION__", version),
        ROOT_DIR / "metadata.json": METADATA_JSON_TEMPLATE.replace("__VERSION__", version),
        ROOT_DIR / "server.js": SERVER_JS_TEMPLATE.replace("__VERSION__", version),
        ROOT_DIR / "index.html": INDEX_HTML_TEMPLATE.replace("__VERSION__", version),
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
    """Synchronize the application version into package.json, metadata.json, and index.html."""
    if not version:
        version = get_project_version()
    clean_version = re.sub(r"\.+", ".", str(version).strip().lstrip("v"))
    print(f"[PREVIEW] Synchronizing version v{clean_version} across preview files...")

    # 1. package.json
    pkg_path = ROOT_DIR / "package.json"
    if pkg_path.is_file():
        text = pkg_path.read_text(encoding="utf-8")
        updated_text = re.sub(r'"version":\s*"[^"]+"', f'"version": "{clean_version}"', text)
        pkg_path.write_text(updated_text, encoding="utf-8")
        print(f"  * Synchronized package.json -> v{clean_version}")

    # 2. metadata.json
    meta_path = ROOT_DIR / "metadata.json"
    if meta_path.is_file():
        text = meta_path.read_text(encoding="utf-8")
        updated_text = re.sub(r'v[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9.\-_]*', f'v{clean_version}', text)
        meta_path.write_text(updated_text, encoding="utf-8")
        print(f"  * Synchronized metadata.json -> v{clean_version}")

    # 3. index.html
    idx_path = ROOT_DIR / "index.html"
    if idx_path.is_file():
        text = idx_path.read_text(encoding="utf-8")
        updated_text = re.sub(r'v[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9.\-_]*', f'v{clean_version}', text)
        idx_path.write_text(updated_text, encoding="utf-8")
        print(f"  * Synchronized index.html -> v{clean_version}")

    print("[PREVIEW] Version synchronization complete.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage AI Studio zero-dependency web preview.")
    parser.add_argument("--restore", action="store_true", help="Restore all preview files if missing")
    parser.add_argument("--sync", action="store_true", help="Synchronize current version across preview files")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing preview files")

    args = parser.parse_args()

    if args.sync:
        sys.exit(sync_version())
    else:
        sys.exit(restore_preview(force=args.force))


if __name__ == "__main__":
    main()

import http from 'node:http';
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
    return '# Changelog\n\nNo CHANGELOG.md found in workspace.';
  } catch (err) {
    return `# Changelog\n\nError reading CHANGELOG.md: ${err.message}`;
  }
}

function extractCurrentVersion(changelogText) {
  const match = changelogText.match(/##\s+v?([0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9.\-_]*)/);
  return match ? `v${match[1]}` : 'v3.9.36-beta';
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
    .version-tag {
      color: var(--accent);
      font-weight: 700;
    }
    .highlight {
      background: rgba(234, 179, 8, 0.25);
      color: #fef08a;
      border-radius: 2px;
      padding: 1px 3px;
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

      const lines = originalText.split('\\n');
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

      changelogEl.textContent = filtered.join('\\n');
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

  if (url === '/favicon.ico' || url === '/noun_electronicmedia_5929933.svg') {
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

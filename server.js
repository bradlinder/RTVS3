import http from 'node:http';
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
    const m = prs.match(/PROJECT_VERSION\s*=\s*["']([^"']+)["']/);
    if (m) return m[1];
  } catch (e) {}
  return '3.9.40-beta';
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
  <title>Radio & TV Story Segmenter v${version}</title>
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
    <div class="badge">v${version}</div>
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

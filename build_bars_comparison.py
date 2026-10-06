#!/usr/bin/env python3
"""Generates a high-resolution close-up inspection board comparing the exact title bars from the user's screenshot."""

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = ROOT_DIR / "resources"
PUBLIC_DIR = ROOT_DIR / "public"


def build_bars_comparison():
    canvas_w = 1200
    canvas_h = 920

    options = [
        {
            "num": "CURRENT BASELINE (Light Mode Option C)",
            "desc": "Title bars currently render in matching silver/fog #dcdfe3 (default light mode)",
            "main_bg": "#dcdfe3",
            "main_fg": "#22262c",
            "main_border": "#b6bcc4",
            "dialog_bg": "#dcdfe3",
            "dialog_fg": "#22262c",
            "dialog_border": "#b6bcc4",
        },
        {
            "num": "OPTION 1: DEEP SLATE / CHARCOAL (#22262c)",
            "desc": "Title bars in deep charcoal slate matching body ink, crisp white text #f8fafc",
            "main_bg": "#22262c",
            "main_fg": "#f8fafc",
            "main_border": "#333b46",
            "dialog_bg": "#22262c",
            "dialog_fg": "#f8fafc",
            "dialog_border": "#333b46",
        },
        {
            "num": "OPTION 2: DARK SLATE CHROME (#20252d)",
            "desc": "Deep workstation slate #20252d with crisp white title text #f8fafc",
            "main_bg": "#20252d",
            "main_fg": "#f8fafc",
            "main_border": "#2c333e",
            "dialog_bg": "#20252d",
            "dialog_fg": "#f8fafc",
            "dialog_border": "#2c333e",
        },
        {
            "num": "OPTION 3: MIDNIGHT BROADCAST NAVY (#16243b)",
            "desc": "Deep midnight blue title bars harmonizing with broadcast blue accents #2e74b5",
            "main_bg": "#16243b",
            "main_fg": "#f0f6fc",
            "main_border": "#233757",
            "dialog_bg": "#16243b",
            "dialog_fg": "#f0f6fc",
            "dialog_border": "#233757",
        },
        {
            "num": "OPTION 4: MEDIUM STEEL SLATE (#3c4450)",
            "desc": "Muted dark steel slate for softer contrast against the light fog window body",
            "main_bg": "#3c4450",
            "main_fg": "#f8fafc",
            "main_border": "#4e5765",
            "dialog_bg": "#3c4450",
            "dialog_fg": "#f8fafc",
            "dialog_border": "#4e5765",
        },
    ]

    svg_blocks = []
    y_pos = 85

    for opt in options:
        block = f"""
        <!-- Block for {opt['num']} -->
        <g transform="translate(40, {y_pos})">
          <text x="0" y="-8" font-size="12" font-weight="700" fill="#38bdf8">{opt['num']}</text>
          <text x="440" y="-8" font-size="11" fill="#94a3b8">{opt['desc']}</text>

          <!-- Main Window Bar -->
          <g transform="translate(0, 0)">
            <rect width="1120" height="34" rx="4" fill="{opt['main_bg']}" stroke="{opt['main_border']}" stroke-width="1" />
            <rect x="10" y="9" width="16" height="16" rx="3" fill="#205493" />
            <circle cx="18" cy="17" r="4" fill="#ffffff" />
            <text x="34" y="22" font-size="12" font-weight="600" fill="{opt['main_fg']}">Radio &amp; TV Segmenter v3.8.4-stable — Project: gun.violence.final.version.rtvs * - Radio &amp; TV Segmenter</text>
            
            <g transform="translate(1010, 0)">
              <line x1="15" y1="18" x2="25" y2="18" stroke="{opt['main_fg']}" stroke-width="1.3" />
              <rect x="45" y="12" width="11" height="10" fill="none" stroke="{opt['main_fg']}" stroke-width="1.2" />
              <line x1="77" y1="12" x2="89" y2="22" stroke="{opt['main_fg']}" stroke-width="1.3" />
              <line x1="89" y1="12" x2="77" y2="22" stroke="{opt['main_fg']}" stroke-width="1.3" />
            </g>
          </g>

          <!-- Preferences Dialog Bar -->
          <g transform="translate(160, 42)">
            <rect width="800" height="34" rx="4" fill="{opt['dialog_bg']}" stroke="{opt['dialog_border']}" stroke-width="1" />
            <rect x="12" y="9" width="16" height="16" rx="3" fill="#205493" />
            <circle cx="20" cy="17" r="4" fill="#ffffff" />
            <text x="36" y="22" font-size="12" font-weight="600" fill="{opt['dialog_fg']}">Preferences — Radio &amp; TV Segmenter</text>
            
            <g transform="translate(690, 0)">
              <line x1="15" y1="18" x2="25" y2="18" stroke="{opt['dialog_fg']}" stroke-width="1.3" />
              <rect x="45" y="12" width="11" height="10" fill="none" stroke="{opt['dialog_fg']}" stroke-width="1.2" />
              <line x1="77" y1="12" x2="89" y2="22" stroke="{opt['dialog_fg']}" stroke-width="1.3" />
              <line x1="89" y1="12" x2="77" y2="22" stroke="{opt['dialog_fg']}" stroke-width="1.3" />
            </g>
          </g>
        </g>
        """
        svg_blocks.append(block)
        y_pos += 160

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <rect width="{canvas_w}" height="{canvas_h}" fill="#11141a" />

  <!-- Title -->
  <g transform="translate(40, 36)">
    <text x="0" y="0" font-size="22" font-weight="800" fill="#f8fafc">Main Window &amp; Preferences Title Bars — Exact Color Options</text>
    <text x="0" y="22" font-size="12" fill="#94a3b8">Inspection of Main Window Title Bar (top) and Preferences Dialog Title Bar (modal) across all 4 suggested dark palettes</text>
  </g>

  {''.join(svg_blocks)}
</svg>"""

    svg_file = RESOURCES_DIR / "titlebar_user_bars_inspection.svg"
    png_file = RESOURCES_DIR / "titlebar_user_bars_inspection.png"
    pub_file = PUBLIC_DIR / "titlebar_user_bars_inspection.png"

    svg_file.write_text(svg_content, encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-i", str(svg_file), str(png_file)], check=True)
    pub_file.write_bytes(png_file.read_bytes())
    print(f"[OK] Generated {png_file.name}")


if __name__ == "__main__":
    build_bars_comparison()

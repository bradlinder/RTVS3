#!/usr/bin/env python3
"""Generates pixel-perfect SVG and PNG mockups for Light Mode Dark Title Bar options."""

import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = ROOT_DIR / "resources"
PUBLIC_DIR = ROOT_DIR / "public"

RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)


def generate_single_window_svg(
    titlebar_bg: str,
    titlebar_text: str,
    titlebar_subtext: str,
    titlebar_border: str,
    menubar_bg: str,
    menubar_text: str,
    menubar_border: str,
    opt_title: str,
    opt_badge: str,
    w: int = 760,
    h: int = 560,
) -> str:
    """Generate SVG content for a single window mockup."""
    # Scale coordinates to fit w x h
    return f"""
    <!-- Window Outer Shell with Shadow -->
    <g filter="url(#dropShadow)">
      <rect width="{w}" height="{h}" rx="8" fill="#dcdfe3" stroke="#b6bcc4" stroke-width="1.5" />

      <!-- Window Title Bar -->
      <path d="M 0 8 Q 0 0 8 0 L {w-8} 0 Q {w} 0 {w} 8 L {w} 36 L 0 36 Z" fill="{titlebar_bg}" />
      <line x1="0" y1="36" x2="{w}" y2="36" stroke="{titlebar_border}" stroke-width="1" />

      <!-- Window Title & Subtitle -->
      <text x="16" y="23" font-size="12" font-weight="700" fill="{titlebar_text}">Radio &amp; TV Story Segmenter v3.8.4</text>
      <text x="245" y="23" font-size="11" fill="{titlebar_subtext}">Morning_News_Block.wav — {opt_title}</text>

      <!-- Window Controls (Min, Max, Close) -->
      <g transform="translate({w - 80}, 11)">
        <rect x="0" y="0" width="18" height="14" rx="2" fill="transparent" />
        <line x1="4" y1="11" x2="14" y2="11" stroke="{titlebar_text}" stroke-width="1.5" />
        <rect x="24" y="0" width="18" height="14" rx="2" fill="transparent" />
        <rect x="27" y="2" width="12" height="10" fill="none" stroke="{titlebar_text}" stroke-width="1.2" />
        <rect x="48" y="0" width="18" height="14" rx="2" fill="transparent" />
        <line x1="51" y1="2" x2="63" y2="12" stroke="{titlebar_text}" stroke-width="1.5" />
        <line x1="63" y1="2" x2="51" y2="12" stroke="{titlebar_text}" stroke-width="1.5" />
      </g>

      <!-- Menu Bar -->
      <rect x="0" y="37" width="{w}" height="28" fill="{menubar_bg}" />
      <line x1="0" y1="65" x2="{w}" y2="65" stroke="{menubar_border}" stroke-width="1" />
      <g transform="translate(16, 55)">
        <text x="0" y="0" font-size="11" font-weight="500" fill="{menubar_text}">File</text>
        <text x="36" y="0" font-size="11" font-weight="500" fill="{menubar_text}">Edit</text>
        <text x="72" y="0" font-size="11" font-weight="500" fill="{menubar_text}">View</text>
        <text x="114" y="0" font-size="11" font-weight="500" fill="{menubar_text}">Settings</text>
        <text x="172" y="0" font-size="11" font-weight="500" fill="{menubar_text}">Plugins</text>
        <text x="228" y="0" font-size="11" font-weight="500" fill="{menubar_text}">Help</text>
      </g>

      <!-- Transport / Action Bar -->
      <g transform="translate(12, 74)">
        <rect x="0" y="0" width="{w-24}" height="40" rx="5" fill="#e3e6ea" stroke="#b6bcc4" stroke-width="1" />
        <rect x="8" y="6" width="60" height="28" rx="14" fill="#2e74b5" />
        <polygon points="34,14 34,26 44,20" fill="#ffffff" />
        
        <rect x="76" y="7" width="76" height="26" rx="4" fill="#d0d4d9" stroke="#b2b8c0" stroke-width="1" />
        <text x="86" y="24" font-size="10" font-weight="600" fill="#22262c">+ New Story</text>
        
        <rect x="158" y="7" width="72" height="26" rx="4" fill="#d0d4d9" stroke="#b2b8c0" stroke-width="1" />
        <text x="168" y="24" font-size="10" font-weight="600" fill="#22262c">Auto-Split</text>
        
        <rect x="236" y="7" width="68" height="26" rx="4" fill="#d0d4d9" stroke="#b2b8c0" stroke-width="1" />
        <text x="248" y="24" font-size="10" font-weight="600" fill="#22262c">Diarize</text>

        <!-- Timecode -->
        <rect x="312" y="7" width="116" height="26" rx="4" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
        <text x="322" y="24" font-family="monospace" font-size="11" font-weight="700" fill="#205493">00:01:24.350</text>
        <text x="436" y="24" font-size="10" fill="#545b66">/ 00:28:45</text>

        <!-- Badge -->
        <rect x="{w-148}" y="8" width="116" height="24" rx="4" fill="#2e74b5" />
        <text x="{w-136}" y="24" font-size="10" font-weight="700" fill="#ffffff">{opt_badge}</text>
      </g>

      <!-- Waveform & Timeline Panel -->
      <g transform="translate(12, 122)">
        <rect x="0" y="0" width="{w-24}" height="106" rx="5" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
        <rect x="0" y="0" width="{w-24}" height="18" rx="4" fill="#d6dae0" />
        <line x1="0" y1="18" x2="{w-24}" y2="18" stroke="#b6bcc4" stroke-width="1" />
        
        <!-- Ticks -->
        <g font-size="8" fill="#545b66" font-family="monospace">
          <text x="30" y="12">00:00</text><line x1="40" y1="14" x2="40" y2="18" stroke="#545b66" stroke-width="1" />
          <text x="140" y="12">00:30</text><line x1="150" y1="14" x2="150" y2="18" stroke="#545b66" stroke-width="1" />
          <text x="250" y="12">01:00</text><line x1="260" y1="14" x2="260" y2="18" stroke="#545b66" stroke-width="1" />
          <text x="360" y="12">01:30</text><line x1="370" y1="14" x2="370" y2="18" stroke="#545b66" stroke-width="1" />
          <text x="470" y="12">02:00</text><line x1="480" y1="14" x2="480" y2="18" stroke="#545b66" stroke-width="1" />
          <text x="580" y="12">02:30</text><line x1="590" y1="14" x2="590" y2="18" stroke="#545b66" stroke-width="1" />
        </g>

        <!-- Waveform Paths -->
        <path d="M 30 60 Q 40 32, 50 60 T 70 60 T 90 25 T 110 60 T 130 38 T 150 60 T 170 22 T 190 60 T 210 42 T 230 60 T 250 30 T 270 60 T 290 48 T 310 60 T 330 22 T 350 60 T 370 34 T 390 60 T 410 26 T 430 60 T 450 38 T 470 60 T 490 20 T 510 60 T 530 40 T 550 60 T 570 30 T 590 60 T 610 50 T 630 60 T 650 34 T 670 60 L 670 60 L 30 60 Z" fill="#4178a8" fill-opacity="0.85" />
        <path d="M 30 60 Q 40 88, 50 60 T 70 60 T 90 95 T 110 60 T 130 82 T 150 60 T 170 98 T 190 60 T 210 78 T 230 60 T 250 90 T 270 60 T 290 72 T 310 60 T 330 98 T 350 60 T 370 86 T 390 60 T 410 94 T 430 60 T 450 82 T 470 60 T 490 100 T 510 60 T 530 80 T 550 60 T 570 90 T 590 60 T 610 70 T 630 60 T 650 86 T 670 60 L 670 60 L 30 60 Z" fill="#4178a8" fill-opacity="0.85" />
        
        <!-- Story Region -->
        <rect x="30" y="19" width="220" height="86" fill="#205493" fill-opacity="0.10" stroke="#205493" stroke-width="1" stroke-dasharray="3 3" />
        <rect x="32" y="21" width="105" height="14" rx="2" fill="#205493" fill-opacity="0.85" />
        <text x="36" y="31" font-size="8" font-weight="700" fill="#ffffff">Story 1: Transit Opening</text>

        <!-- Playhead -->
        <line x1="225" y1="18" x2="225" y2="105" stroke="#b91c1c" stroke-width="2" />
        <polygon points="220,18 230,18 225,23" fill="#b91c1c" />
      </g>

      <!-- Bottom Split Area -->
      <g transform="translate(12, 236)">
        <!-- Transcript Box -->
        <rect x="0" y="0" width="{int((w-24)*0.64)}" height="310" rx="5" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
        <rect x="0" y="0" width="{int((w-24)*0.64)}" height="24" rx="4" fill="#d6dae0" />
        <line x1="0" y1="24" x2="{int((w-24)*0.64)}" y2="24" stroke="#b6bcc4" stroke-width="1" />
        <text x="12" y="16" font-size="10" font-weight="700" fill="#22262c">TRANSCRIPT EDITOR (Option C Matte #eaedf0)</text>

        <!-- Paragraphs -->
        <g transform="translate(12, 44)">
          <text x="0" y="0" font-family="monospace" font-size="10" font-weight="600" fill="#545b66">00:00:04</text>
          <text x="56" y="0" font-size="11" font-weight="700" fill="#205493">Jane Doe (Host):</text>
          <text x="160" y="0" font-size="11" fill="#22262c">Good morning. Today the city council opens</text>
          <text x="0" y="18" font-size="11" fill="#22262c">hearings on the proposed</text>
          <rect x="130" y="7" width="124" height="13" rx="2" fill="#b8d1ea" />
          <text x="132" y="18" font-size="11" font-weight="500" fill="#132c44">municipal transit budget</text>
          <text x="258" y="18" font-size="11" fill="#22262c">for the year.</text>
        </g>

        <g transform="translate(12, 94)">
          <text x="0" y="0" font-family="monospace" font-size="10" font-weight="600" fill="#545b66">00:00:18</text>
          <text x="56" y="0" font-size="11" font-weight="700" fill="#205493">Council President:</text>
          <text x="168" y="0" font-size="11" fill="#22262c">Thank you Jane. Line items in rail</text>
          <rect x="0" y="7" width="144" height="13" rx="2" fill="#fef08a" />
          <text x="2" y="18" font-size="11" font-weight="500" fill="#0f172a">will take top priority over</text>
          <text x="148" y="18" font-size="11" fill="#22262c">road expansions countywide.</text>
        </g>

        <g transform="translate(12, 144)">
          <text x="0" y="0" font-family="monospace" font-size="10" font-weight="600" fill="#545b66">00:00:42</text>
          <text x="56" y="0" font-size="11" font-weight="700" fill="#205493">Reporter Mark:</text>
          <text x="150" y="0" font-size="11" fill="#22262c">Several members of the public have</text>
          <text x="0" y="18" font-size="11" fill="#22262c">signed up to testify during public comment period.</text>
        </g>
        
        <!-- Story Panel -->
        <g transform="translate({int((w-24)*0.64) + 12}, 0)">
          <rect x="0" y="0" width="{w - 24 - int((w-24)*0.64) - 12}" height="310" rx="5" fill="#e3e6ea" stroke="#b6bcc4" stroke-width="1" />
          <rect x="0" y="0" width="{w - 24 - int((w-24)*0.64) - 12}" height="24" rx="4" fill="#d0d4d9" />
          <line x1="0" y1="24" x2="{w - 24 - int((w-24)*0.64) - 12}" y2="24" stroke="#b6bcc4" stroke-width="1" />
          <text x="10" y="16" font-size="10" font-weight="700" fill="#22262c">STORIES (2)</text>

          <!-- Story Card 1 -->
          <g transform="translate(8, 34)">
            <rect x="0" y="0" width="{w - 24 - int((w-24)*0.64) - 28}" height="56" rx="4" fill="#eaedf0" stroke="#2e74b5" stroke-width="1.8" />
            <rect x="6" y="6" width="6" height="44" rx="2" fill="#205493" />
            <text x="18" y="20" font-size="10" font-weight="700" fill="#22262c">Story 1: Transit Opening</text>
            <text x="18" y="36" font-size="9" fill="#545b66">00:00:04 - 00:01:18 (01:14)</text>
          </g>

          <!-- Story Card 2 -->
          <g transform="translate(8, 100)">
            <rect x="0" y="0" width="{w - 24 - int((w-24)*0.64) - 28}" height="56" rx="4" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
            <rect x="6" y="6" width="6" height="44" rx="2" fill="#c05621" />
            <text x="18" y="20" font-size="10" font-weight="700" fill="#22262c">Story 2: Budget Debate</text>
            <text x="18" y="36" font-size="9" fill="#545b66">00:01:18 - 00:03:45 (02:27)</text>
          </g>

          <!-- Color Spec Box -->
          <g transform="translate(8, 168)">
            <rect x="0" y="0" width="{w - 24 - int((w-24)*0.64) - 28}" height="130" rx="4" fill="#d0d4d9" stroke="#b2b8c0" stroke-width="1" />
            <text x="10" y="18" font-size="10" font-weight="700" fill="#22262c">Title Bar Spec:</text>
            <text x="10" y="34" font-size="9" font-weight="600" fill="{titlebar_bg == '#22262c' or titlebar_bg == '#20252d' or titlebar_bg == '#16243b' or titlebar_bg == '#3c4450' and '#22262c'}">Title Bar BG: {titlebar_bg}</text>
            <text x="10" y="50" font-size="9" fill="#545b66">Title Text: {titlebar_text}</text>
            <text x="10" y="66" font-size="9" fill="#545b66">Menu Bar BG: {menubar_bg}</text>
            <text x="10" y="82" font-size="9" fill="#545b66">Menu Text: {menubar_text}</text>
            <text x="10" y="100" font-size="9" font-weight="700" fill="#205493">{opt_badge}</text>
          </g>
        </g>
      </g>
    </g>
    """


def create_comparison_board():
    """Create a 2x2 comparison board showing all 4 title bar options."""
    w = 760
    h = 570
    canvas_w = 1640
    canvas_h = 1340

    # Option 1: Deep Slate / Charcoal Title Bar (#22262c) + Silver Menu Bar (#e3e6ea)
    opt1 = generate_single_window_svg(
        titlebar_bg="#22262c",
        titlebar_text="#f8fafc",
        titlebar_subtext="#94a3b8",
        titlebar_border="#333b46",
        menubar_bg="#e3e6ea",
        menubar_text="#22262c",
        menubar_border="#b6bcc4",
        opt_title="Option 1: Dark Slate Title Bar",
        opt_badge="OPT 1: DARK SLATE (#22262c)",
        w=w,
        h=h,
    )

    # Option 2: Unified Dark Slate Chrome (Both Title Bar & Menu Bar in Dark Slate #20252d)
    opt2 = generate_single_window_svg(
        titlebar_bg="#20252d",
        titlebar_text="#f8fafc",
        titlebar_subtext="#94a3b8",
        titlebar_border="#2a313b",
        menubar_bg="#252b34",
        menubar_text="#e2e8f0",
        menubar_border="#333b46",
        opt_title="Option 2: Unified Dark Chrome",
        opt_badge="OPT 2: UNIFIED DARK (#20252d)",
        w=w,
        h=h,
    )

    # Option 3: Midnight Broadcast Navy Title Bar (#16243b) + Silver Menu Bar (#e3e6ea)
    opt3 = generate_single_window_svg(
        titlebar_bg="#16243b",
        titlebar_text="#f0f6fc",
        titlebar_subtext="#7dd3fc",
        titlebar_border="#233757",
        menubar_bg="#e3e6ea",
        menubar_text="#22262c",
        menubar_border="#b6bcc4",
        opt_title="Option 3: Midnight Broadcast Navy",
        opt_badge="OPT 3: MIDNIGHT NAVY (#16243b)",
        w=w,
        h=h,
    )

    # Option 4: Medium Steel / Muted Slate Title Bar (#3c4450) + Silver Menu Bar (#e3e6ea)
    opt4 = generate_single_window_svg(
        titlebar_bg="#3c4450",
        titlebar_text="#f8fafc",
        titlebar_subtext="#cbd5e1",
        titlebar_border="#4e5765",
        menubar_bg="#e3e6ea",
        menubar_text="#22262c",
        menubar_border="#b6bcc4",
        opt_title="Option 4: Medium Steel Slate",
        opt_badge="OPT 4: MEDIUM STEEL (#3c4450)",
        w=w,
        h=h,
    )

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <defs>
    <filter id="dropShadow" x="-2%" y="-2%" width="104%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.25" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="{canvas_w}" height="{canvas_h}" fill="#13161c" />

  <!-- Top Title Banner -->
  <g transform="translate(40, 42)">
    <text x="0" y="0" font-size="24" font-weight="800" fill="#f8fafc">Radio &amp; TV Story Segmenter — Light Mode (Option C) Title Bar Variations</text>
    <text x="0" y="24" font-size="13" fill="#94a3b8">Comparative preview of 4 dark title bar options on top of the Option C low-glare Silver/Fog canvas (#dcdfe3) and matte editor (#eaedf0)</text>
  </g>

  <!-- Top Left: Option 1 -->
  <g transform="translate(40, 100)">
    <!-- Section Header Tag -->
    <rect x="0" y="-24" width="340" height="20" rx="3" fill="#22262c" />
    <text x="10" y="-10" font-size="11" font-weight="700" fill="#38bdf8">OPTION 1: DARK SLATE TITLE BAR (#22262c)</text>
    <text x="350" y="-10" font-size="11" fill="#94a3b8">Dark window caption + Light silver menu bar below</text>
    {opt1}
  </g>

  <!-- Top Right: Option 2 -->
  <g transform="translate({40 + w + 40}, 100)">
    <!-- Section Header Tag -->
    <rect x="0" y="-24" width="340" height="20" rx="3" fill="#20252d" stroke="#333b46" stroke-width="1" />
    <text x="10" y="-10" font-size="11" font-weight="700" fill="#38bdf8">OPTION 2: UNIFIED DARK CHROME (#20252d)</text>
    <text x="350" y="-10" font-size="11" fill="#94a3b8">Both Title Bar and Menu Bar in cohesive dark slate</text>
    {opt2}
  </g>

  <!-- Bottom Left: Option 3 -->
  <g transform="translate(40, {100 + h + 50})">
    <!-- Section Header Tag -->
    <rect x="0" y="-24" width="370" height="20" rx="3" fill="#16243b" />
    <text x="10" y="-10" font-size="11" font-weight="700" fill="#38bdf8">OPTION 3: MIDNIGHT BROADCAST NAVY (#16243b)</text>
    <text x="380" y="-10" font-size="11" fill="#94a3b8">Deep navy title bar matching broadcast blue theme accents</text>
    {opt3}
  </g>

  <!-- Bottom Right: Option 4 -->
  <g transform="translate({40 + w + 40}, {100 + h + 50})">
    <!-- Section Header Tag -->
    <rect x="0" y="-24" width="370" height="20" rx="3" fill="#3c4450" />
    <text x="10" y="-10" font-size="11" font-weight="700" fill="#38bdf8">OPTION 4: MEDIUM STEEL SLATE (#3c4450)</text>
    <text x="380" y="-10" font-size="11" fill="#94a3b8">Muted medium dark slate for reduced contrast jump against silver</text>
    {opt4}
  </g>
</svg>"""

    svg_file = RESOURCES_DIR / "titlebar_options_comparison.svg"
    png_file = RESOURCES_DIR / "titlebar_options_comparison.png"
    public_png = PUBLIC_DIR / "titlebar_options_comparison.png"

    svg_file.write_text(svg_content, encoding="utf-8")
    print(f"[OK] Wrote {svg_file}")

    cmd = ["ffmpeg", "-y", "-i", str(svg_file), str(png_file)]
    subprocess.run(cmd, check=True)
    print(f"[OK] Rendered {png_file}")

    public_png.write_bytes(png_file.read_bytes())
    print(f"[OK] Copied to {public_png}")


def create_header_strips_mockup():
    """Create a high-detail zoomed strip comparison focusing on the title bar and menu bar."""
    canvas_w = 1200
    canvas_h = 780
    strip_w = 1120
    strip_h = 100

    strips = [
        {
            "name": "BASELINE: Original Light Mode (Matching Fog/Silver #dcdfe3)",
            "desc": "Title bar matches the window canvas color #dcdfe3 with dark ink text #22262c",
            "title_bg": "#dcdfe3",
            "title_fg": "#22262c",
            "title_sub": "#545b66",
            "title_border": "#b6bcc4",
            "menu_bg": "#e3e6ea",
            "menu_fg": "#22262c",
            "menu_border": "#b6bcc4",
        },
        {
            "name": "OPTION 1: Dark Slate / Charcoal Title Bar (#22262c)",
            "desc": "Charcoal slate title bar with crisp white text #f8fafc, silver menu bar #e3e6ea below",
            "title_bg": "#22262c",
            "title_fg": "#f8fafc",
            "title_sub": "#94a3b8",
            "title_border": "#333b46",
            "menu_bg": "#e3e6ea",
            "menu_fg": "#22262c",
            "menu_border": "#b6bcc4",
        },
        {
            "name": "OPTION 2: Unified Dark Slate Header (#20252d)",
            "desc": "Both Title Bar and Menu Bar in sleek dark slate with light menu text #e2e8f0 (Pro DAW style)",
            "title_bg": "#20252d",
            "title_fg": "#f8fafc",
            "title_sub": "#94a3b8",
            "title_border": "#2a313b",
            "menu_bg": "#252b34",
            "menu_fg": "#e2e8f0",
            "menu_border": "#333b46",
        },
        {
            "name": "OPTION 3: Midnight Broadcast Navy Title Bar (#16243b)",
            "desc": "Deep midnight blue title bar harmonizing with broadcast blue accents #2e74b5, silver menu bar below",
            "title_bg": "#16243b",
            "title_fg": "#f0f6fc",
            "title_sub": "#7dd3fc",
            "title_border": "#233757",
            "menu_bg": "#e3e6ea",
            "menu_fg": "#22262c",
            "menu_border": "#b6bcc4",
        },
        {
            "name": "OPTION 4: Medium Steel / Muted Slate Title Bar (#3c4450)",
            "desc": "Softer dark steel slate reducing harsh contrast jumps against the light fog window body",
            "title_bg": "#3c4450",
            "title_fg": "#f8fafc",
            "title_sub": "#cbd5e1",
            "title_border": "#4e5765",
            "menu_bg": "#e3e6ea",
            "menu_fg": "#22262c",
            "menu_border": "#b6bcc4",
        },
    ]

    svg_strips = []
    y_offset = 90
    for idx, s in enumerate(strips):
        svg_strip = f"""
        <!-- Strip {idx+1} Container -->
        <g transform="translate(40, {y_offset})">
          <text x="0" y="-8" font-size="12" font-weight="700" fill="#38bdf8">{s['name']}</text>
          <text x="480" y="-8" font-size="11" fill="#94a3b8">{s['desc']}</text>
          
          <!-- Outer border -->
          <g filter="url(#dropShadowSmall)">
            <rect width="{strip_w}" height="{strip_h}" rx="6" fill="#dcdfe3" stroke="#b6bcc4" stroke-width="1.2" />
            
            <!-- Title Bar -->
            <path d="M 0 6 Q 0 0 6 0 L {strip_w-6} 0 Q {strip_w} 0 {strip_w} 6 L {strip_w} 38 L 0 38 Z" fill="{s['title_bg']}" />
            <line x1="0" y1="38" x2="{strip_w}" y2="38" stroke="{s['title_border']}" stroke-width="1" />
            <text x="16" y="24" font-size="13" font-weight="700" fill="{s['title_fg']}">Radio &amp; TV Story Segmenter v3.8.4</text>
            <text x="260" y="24" font-size="12" fill="{s['title_sub']}">Morning_News_Block_2026-10-05.wav — [Light Mode Option C Preview]</text>

            <!-- Window buttons -->
            <g transform="translate({strip_w - 90}, 12)">
              <line x1="6" y1="12" x2="18" y2="12" stroke="{s['title_fg']}" stroke-width="1.5" />
              <rect x="30" y="3" width="13" height="11" fill="none" stroke="{s['title_fg']}" stroke-width="1.2" />
              <line x1="58" y1="3" x2="70" y2="14" stroke="{s['title_fg']}" stroke-width="1.5" />
              <line x1="70" y1="3" x2="58" y2="14" stroke="{s['title_fg']}" stroke-width="1.5" />
            </g>

            <!-- Menu Bar -->
            <rect x="0" y="39" width="{strip_w}" height="32" fill="{s['menu_bg']}" />
            <line x1="0" y1="71" x2="{strip_w}" y2="71" stroke="{s['menu_border']}" stroke-width="1" />
            <g transform="translate(16, 60)">
              <text x="0" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">File</text>
              <text x="44" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">Edit</text>
              <text x="88" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">View</text>
              <text x="138" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">Settings</text>
              <text x="204" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">Plugins</text>
              <text x="268" y="0" font-size="12" font-weight="500" fill="{s['menu_fg']}">Help</text>
            </g>

            <!-- Bottom content slice indication -->
            <rect x="0" y="72" width="{strip_w}" height="28" fill="#dcdfe3" />
            <text x="16" y="90" font-size="11" font-weight="600" fill="#545b66">▼ Application Window Body &amp; Toolbars below in Silver/Fog (#dcdfe3 / #eaedf0)</text>
          </g>
        </g>
        """
        svg_strips.append(svg_strip)
        y_offset += 134

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <defs>
    <filter id="dropShadowSmall" x="-2%" y="-3%" width="104%" height="108%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.18" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="{canvas_w}" height="{canvas_h}" fill="#13161c" />

  <!-- Top Title Banner -->
  <g transform="translate(40, 38)">
    <text x="0" y="0" font-size="22" font-weight="800" fill="#f8fafc">Title Bar &amp; Header Strip Close-Up Comparison (Light Mode Option C)</text>
    <text x="0" y="22" font-size="12" fill="#94a3b8">Side-by-side inspection of title bar backgrounds, window controls, and menu bar relationships</text>
  </g>

  {''.join(svg_strips)}
</svg>"""

    svg_file = RESOURCES_DIR / "titlebar_options_header_strips.svg"
    png_file = RESOURCES_DIR / "titlebar_options_header_strips.png"
    public_png = PUBLIC_DIR / "titlebar_options_header_strips.png"

    svg_file.write_text(svg_content, encoding="utf-8")
    print(f"[OK] Wrote {svg_file}")

    cmd = ["ffmpeg", "-y", "-i", str(svg_file), str(png_file)]
    subprocess.run(cmd, check=True)
    print(f"[OK] Rendered {png_file}")

    public_png.write_bytes(png_file.read_bytes())
    print(f"[OK] Copied to {public_png}")


if __name__ == "__main__":
    create_comparison_board()
    create_header_strips_mockup()
    print("[ALL DONE] Generated title bar mockup images.")

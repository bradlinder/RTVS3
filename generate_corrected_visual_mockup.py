#!/usr/bin/env python3
"""Generates side-by-side comparison PNGs showing:
1. The Before state (discrepancy with white/unstyled dialog title bar + dark navy Export menu)
2. The Corrected After state (Option 4 #3c4450 on BOTH title bars + light mode visual consistency for Export menu)
"""

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = ROOT_DIR / "resources"
PUBLIC_DIR = ROOT_DIR / "public"

RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)


def build_app_screen_svg(
    is_after: bool = True,
    w: int = 1280,
    h: int = 740,
) -> str:
    """Build SVG representing the main app window with the Export modal dialog."""
    # Colors
    main_title_bg = "#3c4450"
    main_title_fg = "#f8fafc"
    main_title_border = "#4e5765"

    if is_after:
        dialog_title_bg = "#3c4450"
        dialog_title_fg = "#f8fafc"
        dialog_title_border = "#4e5765"
        
        # Export menu interior
        exp_header_fg = "#22262c"
        exp_sec_btn_bg = "#e3e6ea"
        exp_sec_btn_fg = "#22262c"
        exp_sec_btn_border = "#b6bcc4"
        exp_sec_body_bg = "#eaedf0"
        exp_sec_body_border = "#b6bcc4"
        exp_btn_bg = "#e3e6ea"
        exp_btn_fg = "#22262c"
        exp_btn_border = "#b6bcc4"
        exp_text_muted = "#545b66"
    else:
        # Before state from user's screenshot
        dialog_title_bg = "#ffffff"  # unstyled / default white title bar
        dialog_title_fg = "#22262c"
        dialog_title_border = "#d0d4d9"

        # Export menu interior (dark mode hardcoded colors)
        exp_header_fg = "#f1f5f9"
        exp_sec_btn_bg = "#1e293b"
        exp_sec_btn_fg = "#f1f5f9"
        exp_sec_btn_border = "#334155"
        exp_sec_body_bg = "#334155"
        exp_sec_body_border = "#475569"
        exp_btn_bg = "#1e293b"
        exp_btn_fg = "#94a3b8"
        exp_btn_border = "#334155"
        exp_text_muted = "#94a3b8"

    return f"""
    <!-- Outer Main Window Shell -->
    <g>
      <!-- Canvas Background -->
      <rect width="{w}" height="{h}" fill="#dcdfe3" />

      <!-- Top Title Bar (Main Window) -->
      <rect x="0" y="0" width="{w}" height="32" fill="{main_title_bg}" />
      <line x1="0" y1="32" x2="{w}" y2="32" stroke="{main_title_border}" stroke-width="1" />
      <rect x="10" y="8" width="16" height="16" rx="3" fill="#205493" />
      <circle cx="18" cy="16" r="4" fill="#ffffff" />
      <text x="34" y="21" font-size="12" font-weight="600" fill="{main_title_fg}">Radio &amp; TV Segmenter v3.8.6-stable — Project: gun.violence.final.version.rtvs * - Radio &amp; TV Segmenter</text>

      <!-- Main Window Controls -->
      <g transform="translate({w - 110}, 0)">
        <line x1="13" y1="17" x2="23" y2="17" stroke="{main_title_fg}" stroke-width="1.2" />
        <rect x="48" y="11" width="11" height="10" fill="none" stroke="{main_title_fg}" stroke-width="1.2" />
        <line x1="84" y1="11" x2="96" y2="21" stroke="{main_title_fg}" stroke-width="1.2" />
        <line x1="96" y1="11" x2="84" y2="21" stroke="{main_title_fg}" stroke-width="1.2" />
      </g>

      <!-- Menu Bar -->
      <rect x="0" y="32" width="{w}" height="28" fill="#e3e6ea" />
      <line x1="0" y1="60" x2="{w}" y2="60" stroke="#b6bcc4" stroke-width="1" />
      <g transform="translate(16, 50)" font-size="11" font-weight="500" fill="#22262c">
        <text x="0" y="0">File</text>
        <text x="36" y="0">Edit</text>
        <text x="72" y="0">View</text>
        <text x="114" y="0">Tools</text>
        <text x="160" y="0">Settings</text>
        <text x="218" y="0">Help</text>
      </g>

      <!-- Waveform area (background simulation) -->
      <rect x="10" y="68" width="{w - 20}" height="140" rx="4" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
      <text x="18" y="86" font-size="11" fill="#78808d">Audio: gun.violence.final.version.wav</text>
      <!-- Simulated waveform bars -->
      <g fill="#5c768d" opacity="0.6">
        <rect x="20" y="115" width="2" height="40" /><rect x="26" y="105" width="2" height="60" />
        <rect x="32" y="95" width="2" height="80" /><rect x="38" y="110" width="2" height="50" />
        <rect x="44" y="120" width="2" height="30" /><rect x="50" y="100" width="2" height="70" />
        <rect x="56" y="90" width="2" height="90" /><rect x="62" y="105" width="2" height="60" />
        <rect x="68" y="115" width="2" height="40" /><rect x="74" y="125" width="2" height="20" />
      </g>
      <!-- Red playhead line -->
      <line x1="120" y1="72" x2="120" y2="204" stroke="#dc2626" stroke-width="2" />

      <!-- Bottom panels in background -->
      <rect x="10" y="216" width="760" height="510" rx="4" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
      <g transform="translate(24, 250)" font-size="11">
        <text x="0" y="0" font-family="monospace" font-weight="700" fill="#22262c">00:00</text>
        <text x="40" y="0" font-weight="700" fill="#205493">Kevin Walker:</text>
        <text x="130" y="0" fill="#22262c">Eight years ago, Stanley Crawford lost his son to gun violence...</text>

        <text x="0" y="32" font-family="monospace" font-weight="700" fill="#22262c">00:20</text>
        <text x="40" y="32" font-weight="700" fill="#205493">Stanley Crawford:</text>
        <text x="156" y="32" fill="#22262c">I love my grandson. I don't want him to end up dead...</text>
      </g>

      <rect x="780" y="216" width="{w - 790}" height="510" rx="4" fill="#e3e6ea" stroke="#b6bcc4" stroke-width="1" />

      <!-- ======================================================== -->
      <!-- EXPORT MODAL DIALOG (Foreground)                         -->
      <!-- ======================================================== -->
      <g transform="translate(240, 75)" filter="url(#modalShadow)">
        <!-- Dialog Outer Frame -->
        <rect width="800" height="610" rx="8" fill="#dcdfe3" stroke="#9ea6b0" stroke-width="1.5" />

        <!-- Dialog Title Bar -->
        <path d="M 0 8 Q 0 0 8 0 L 792 0 Q 800 0 800 8 L 800 34 L 0 34 Z" fill="{dialog_title_bg}" />
        <line x1="0" y1="34" x2="800" y2="34" stroke="{dialog_title_border}" stroke-width="1" />
        <rect x="12" y="9" width="16" height="16" rx="3" fill="#205493" />
        <circle cx="20" cy="17" r="4" fill="#ffffff" />
        <text x="36" y="22" font-size="12" font-weight="600" fill="{dialog_title_fg}">Export - Radio &amp; TV Segmenter</text>

        <!-- Dialog Controls (Min, Max, Close) -->
        <g transform="translate(705, 0)">
          <line x1="11" y1="18" x2="21" y2="18" stroke="{dialog_title_fg}" stroke-width="1.2" />
          <rect x="42" y="12" width="11" height="10" fill="none" stroke="{dialog_title_fg}" stroke-width="1.2" />
          <line x1="76" y1="12" x2="88" y2="22" stroke="{dialog_title_fg}" stroke-width="1.2" />
          <line x1="88" y1="12" x2="76" y2="22" stroke="{dialog_title_fg}" stroke-width="1.2" />
        </g>

        <!-- Dialog Header Row -->
        <g transform="translate(14, 46)">
          <text x="0" y="16" font-size="13" font-weight="700" fill="{exp_header_fg}">Unified Export Center</text>
          <g transform="translate(685, 0)">
            <rect width="85" height="24" rx="4" fill="{exp_btn_bg}" stroke="{exp_btn_border}" stroke-width="1" />
            <text x="10" y="16" font-size="11" font-weight="600" fill="{exp_btn_fg}">▾ Collapse All</text>
          </g>
        </g>

        <!-- Section 1: Export Destination -->
        <g transform="translate(14, 76)">
          <rect width="772" height="32" rx="4" fill="{exp_sec_btn_bg}" stroke="{exp_sec_btn_border}" stroke-width="1" />
          <text x="320" y="21" font-size="12" font-weight="700" fill="{exp_sec_btn_fg}">▾ Export Destination</text>
          <!-- Section 1 Content Card -->
          <g transform="translate(0, 31)">
            <rect width="772" height="40" fill="{exp_sec_body_bg}" stroke="{exp_sec_body_border}" stroke-width="1" />
            <!-- Radio pill buttons -->
            <rect x="12" y="8" width="180" height="24" rx="4" fill="#2e74b5" />
            <text x="22" y="24" font-size="11" font-weight="600" fill="#ffffff">● Local Files (Media &amp; Transcripts)</text>
            
            <text x="210" y="24" font-size="11" fill="{exp_sec_btn_fg}">○ WordPress Draft Post</text>
            <text x="375" y="24" font-size="11" fill="{exp_sec_btn_fg}">○ Google Docs</text>
            <text x="475" y="24" font-size="11" fill="{exp_sec_btn_fg}">○ YouTube Video Publisher</text>
            
            <rect x="690" y="8" width="70" height="24" rx="3" fill="{exp_btn_bg}" stroke="{exp_btn_border}" stroke-width="1" />
            <text x="702" y="24" font-size="11" fill="#2e74b5">⇅ Reorder...</text>
          </g>
        </g>

        <!-- Section 2: Export Scope -->
        <g transform="translate(14, 155)">
          <rect width="772" height="32" rx="4" fill="{exp_sec_btn_bg}" stroke="{exp_sec_btn_border}" stroke-width="1" />
          <text x="340" y="21" font-size="12" font-weight="700" fill="{exp_sec_btn_fg}">▾ Export Scope</text>
          <!-- Section 2 Content Card -->
          <g transform="translate(0, 31)">
            <rect width="772" height="42" fill="{exp_sec_body_bg}" stroke="{exp_sec_body_border}" stroke-width="1" />
            <rect x="10" y="8" width="752" height="26" rx="4" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
            <text x="20" y="25" font-size="11" fill="#22262c">Full Episode</text>
            <text x="745" y="25" font-size="11" fill="#78808d">▼</text>
          </g>
        </g>

        <!-- Section 3: Export Formats -->
        <g transform="translate(14, 236)">
          <rect width="772" height="32" rx="4" fill="{exp_sec_btn_bg}" stroke="{exp_sec_btn_border}" stroke-width="1" />
          <text x="250" y="21" font-size="12" font-weight="700" fill="{exp_sec_btn_fg}">▾ Export Formats (TXT, DOCX, PDF, Media...)</text>
          <!-- Section 3 Content Card -->
          <g transform="translate(0, 31)">
            <rect width="772" height="270" rx="0 0 6 6" fill="{exp_sec_body_bg}" stroke="{exp_sec_body_border}" stroke-width="1" />
            
            <!-- Checkbox items -->
            <g transform="translate(16, 20)" font-size="11" fill="{exp_sec_btn_fg}">
              <rect x="0" y="-12" width="14" height="14" rx="2" fill="#2e74b5" />
              <text x="3" y="-1" fill="#ffffff" font-weight="bold">✓</text>
              <text x="24" y="0">Text transcript (.txt)</text>

              <rect x="0" y="12" width="14" height="14" rx="2" fill="#2e74b5" />
              <text x="3" y="23" fill="#ffffff" font-weight="bold">✓</text>
              <text x="24" y="24">Word document (.docx)</text>

              <rect x="0" y="36" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="48">PDF document (.pdf)</text>

              <rect x="0" y="60" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="72">SubRip subtitles (.srt)</text>

              <rect x="0" y="84" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="96">WebVTT subtitles (.vtt)</text>

              <rect x="0" y="108" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="120">CUE sheet (.cue)</text>

              <rect x="0" y="132" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="144">Tracklist / YouTube Chapters (.txt)</text>
              <rect x="230" y="130" width="85" height="20" rx="3" fill="#2e74b5" />
              <text x="238" y="144" fill="#ffffff" font-size="10" font-weight="600">Copy Chapters</text>

              <rect x="0" y="156" width="14" height="14" rx="2" fill="none" stroke="#b6bcc4" stroke-width="1.5" />
              <text x="24" y="168">Cockos REAPER project (.rpp)</text>
            </g>

            <!-- Bottom row inside section 3 -->
            <g transform="translate(16, 225)">
              <text x="0" y="16" font-size="11" fill="{exp_text_muted}">Unselected Audio Mode:</text>
              <rect x="145" y="0" width="180" height="24" rx="3" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
              <text x="155" y="16" font-size="11" fill="#22262c">Exclude unselected audio</text>
              <text x="310" y="16" font-size="10" fill="#78808d">▼</text>

              <rect x="350" y="0" width="110" height="24" rx="3" fill="#eaedf0" stroke="#b6bcc4" stroke-width="1" />
              <text x="360" y="16" font-size="11" fill="#2e74b5">Edit ID3 Tags</text>
            </g>
          </g>
        </g>

        <!-- Bottom Action Bar (Export Files..., Cancel) -->
        <g transform="translate(14, 555)">
          <rect x="0" y="8" width="160" height="28" rx="4" fill="{exp_btn_bg}" stroke="{exp_btn_border}" stroke-width="1" />
          <text x="14" y="26" font-size="11" fill="{exp_sec_btn_fg}">Save Options as Default</text>

          <g transform="translate(560, 8)">
            <rect width="110" height="28" rx="4" fill="#2e74b5" />
            <text x="20" y="18" font-size="11" font-weight="bold" fill="#ffffff">Export Files...</text>

            <rect x="120" y="0" width="70" height="28" rx="4" fill="{exp_btn_bg}" stroke="{exp_btn_border}" stroke-width="1" />
            <text x="136" y="18" font-size="11" fill="{exp_sec_btn_fg}">Cancel</text>
          </g>
        </g>
      </g>
    </g>
    """


def generate_side_by_side_comparison():
    canvas_w = 1920
    canvas_h = 1080
    sub_w = 880
    sub_h = 510

    before_panel = build_app_screen_svg(is_after=False, w=sub_w, h=sub_h)
    after_panel = build_app_screen_svg(is_after=True, w=sub_w, h=sub_h)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <defs>
    <filter id="modalShadow" x="-5%" y="-5%" width="110%" height="112%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.30" />
    </filter>
  </defs>

  <rect width="{canvas_w}" height="{canvas_h}" fill="#0f172a" />

  <!-- Main Title Banner -->
  <g transform="translate(60, 50)">
    <text x="0" y="0" font-size="26" font-weight="800" fill="#f8fafc">Light Mode Theme Consistency &amp; Title Bar Synchronization</text>
    <text x="0" y="26" font-size="14" fill="#94a3b8">Resolving title bar mismatch (Option 4 Medium Steel Slate #3c4450 across all windows) and unifying Export menu backgrounds with Preferences &amp; Batch processing</text>
  </g>

  <!-- Left: Before Panel -->
  <g transform="translate(60, 120)">
    <!-- Label -->
    <rect x="0" y="-30" width="380" height="24" rx="4" fill="#dc2626" />
    <text x="12" y="-14" font-size="12" font-weight="800" fill="#ffffff">BEFORE: Title Bar Mismatch &amp; Dark Navy Export Menu</text>
    <text x="400" y="-14" font-size="12" fill="#fca5a5">Pop-up title bar was white/unstyled, and Export menu had hardcoded dark navy #0f172a / #1e293b styling</text>
    {before_panel}
  </g>

  <!-- Right: After Panel -->
  <g transform="translate({60 + sub_w + 40}, 120)">
    <!-- Label -->
    <rect x="0" y="-30" width="380" height="24" rx="4" fill="#16a34a" />
    <text x="12" y="-14" font-size="12" font-weight="800" fill="#ffffff">AFTER: Option 4 #3c4450 on All Windows + Unified Light Menu</text>
    <text x="400" y="-14" font-size="12" fill="#86efac">Both top bars match #3c4450, and Export menu adopts clean light surfaces #eaedf0 / #e3e6ea matching Preferences</text>
    {after_panel}
  </g>

  <!-- Bottom Summary Info Card -->
  <g transform="translate(60, {120 + sub_h + 30})">
    <rect width="{canvas_w - 120}" height="320" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1.5" />
    
    <text x="30" y="36" font-size="16" font-weight="800" fill="#38bdf8">Detailed Changes Applied for Complete Light Mode Harmony:</text>

    <g transform="translate(30, 65)" font-size="13" fill="#e2e8f0">
      <text x="0" y="0" font-weight="700" fill="#f8fafc">1. Universal Window &amp; Pop-up Title Bar Synchronization (Option 4 Medium Steel Slate):</text>
      <text x="20" y="24" fill="#cbd5e1">• Main Application Window and all Modal Dialogs (Export, Preferences, Story Metadata, Voice Match, Shortcuts, ID3 Editor, Batch Processing)</text>
      <text x="20" y="44" fill="#cbd5e1">  now receive the exact same <tspan font-weight="bold" fill="#38bdf8">#3c4450</tspan> caption color, crisp white <tspan font-weight="bold" fill="#ffffff">#f8fafc</tspan> text, and subtle <tspan font-weight="bold" fill="#94a3b8">#4e5765</tspan> border via Windows DWM attribute propagation.</text>
      <text x="20" y="64" fill="#cbd5e1">• Implemented global eventFilter interception on QEvent.Show / WindowActivate to ensure dynamically spawned dialogs never revert to white.</text>

      <text x="0" y="105" font-weight="700" fill="#f8fafc">2. Export Menu Theme Normalization (Visual Consistency with Preferences &amp; Batch Processing):</text>
      <text x="20" y="129" fill="#cbd5e1">• Refactored <tspan font-family="monospace" fill="#38bdf8">CollapsibleSection</tspan> in prs_shared.py: In Light Mode, section header strips now use clean silver fog <tspan font-weight="bold" fill="#38bdf8">#e3e6ea</tspan> with dark ink <tspan font-weight="bold" fill="#38bdf8">#22262c</tspan> text</text>
      <text x="20" y="149" fill="#cbd5e1">  and light container backgrounds <tspan font-weight="bold" fill="#38bdf8">#eaedf0</tspan> instead of hardcoded dark navy #1e293b / rgba(15, 23, 42, 0.35).</text>
      <text x="20" y="169" fill="#cbd5e1">• Refactored <tspan font-family="monospace" fill="#38bdf8">UnifiedExportDialog</tspan>, WordPress exporter, and YouTube exporter: Buttons, checkboxes, combo boxes, list widgets, and badges</text>
      <text x="20" y="189" fill="#cbd5e1">  now use light mode token palettes matching Preferences, Batch Processing, and Multi-Stage Processing.</text>
      <text x="20" y="209" fill="#cbd5e1">• Refactored Story Metadata Editor, Voice Profile Matcher, and Shortcuts Manager to fully respect active theme mode.</text>
    </g>
  </g>
</svg>"""

    svg_file = RESOURCES_DIR / "light_mode_consistency_comparison.svg"
    png_file = RESOURCES_DIR / "light_mode_consistency_comparison.png"
    public_png = PUBLIC_DIR / "light_mode_consistency_comparison.png"

    svg_file.write_text(svg_content, encoding="utf-8")
    print(f"[OK] Wrote {svg_file}")

    subprocess.run(["ffmpeg", "-y", "-i", str(svg_file), str(png_file)], check=True)
    print(f"[OK] Rendered {png_file}")

    public_png.write_bytes(png_file.read_bytes())
    print(f"[OK] Copied to {public_png}")


if __name__ == "__main__":
    generate_side_by_side_comparison()

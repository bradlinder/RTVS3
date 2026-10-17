"""transcript_styles.py - Transcript view stylesheets and dark-mode clipboard styling normalizers.

Provides:
- transcript_text_view_stylesheet: Dynamic theme and font-scale CSS generator for transcript views
- clean_dark_mode_clipboard_html: Normalizes plain white text to #000000 while preserving rich styles
"""

import re

_CLIPBOARD_WHITE_COLORS = {
    "#ffffff", "#f0f3f6", "#f0f0f0", "#e0e0e0", "#ffffff", "#fff", "white",
    "rgb(255,255,255)", "rgb(255, 255, 255)",
    "rgb(240,243,246)", "rgb(240, 243, 246)",
    "rgb(240,240,240)", "rgb(240, 240, 240)",
    "rgb(224,224,224)", "rgb(224, 224, 224)",
}


def transcript_text_view_stylesheet(mode: str, font_size: float = 16.0) -> str:
    """Shared visual treatment for transcript-style views.

    ``font_size`` is deliberately supplied at runtime so the user's transcript
    zoom preference changes only transcript text, not the surrounding UI.
    """
    font_size = max(11, min(25, float(font_size)))
    if mode == "light":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #eaedf0;
                color: #22262c;
                border: 1px solid #b6bcc4;
                border-radius: 8px;
                padding: 12px;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
                selection-background-color: #b8d1ea;
                selection-color: #132c44;
            }}
        """
    elif mode == "high_contrast":
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffff00;
                font-size: {font_size:.1f}px;
                line-height: 1.7;
            }}
        """
    return f"""
            QTextEdit, QTextBrowser {{
                background-color: #121417;
                color: #f0f3f6;
                border: 1px solid #282c35;
                border-radius: 8px;
                padding: 12px;
                font-size: {font_size:.1f}px;
                line-height: 1.6;
                selection-background-color: #38bdf8;
                selection-color: #ffffff;
            }}
        """


def clean_dark_mode_clipboard_html(raw_html: str) -> str:
    """Normalize plain text font colors to black (#000000) for external pasting.

    Preserves rich styling such as blue speaker labels, highlight backgrounds and text,
    bold, italic, underline, strikethrough, and timestamps so pasting into Microsoft Word,
    Google Docs, Apple Notes, or email renders clean, readable black text without
    invisible white-on-white text or broken highlight/label styling.
    """
    if not raw_html:
        return raw_html

    def _replace_white_color(match):
        prefix = match.group(1)
        color = match.group(2).lower().strip()
        suffix = match.group(3)
        if color in _CLIPBOARD_WHITE_COLORS:
            return f"{prefix}#000000{suffix}"
        return match.group(0)

    # Use negative lookbehind (?<![-a-zA-Z]) so that 'background-color:' is strictly untouched
    cleaned = re.sub(
        r'((?<![-a-zA-Z])color\s*:\s*)(#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|white)(\s*[;\"\'])',
        _replace_white_color,
        raw_html,
        flags=re.IGNORECASE,
    )

    # If body style does not explicitly define a text color, inject color:#000000 so any
    # unadorned text defaults to black when pasted into external document editors
    if '<body' in cleaned.lower():
        if not re.search(r'body[^{>]*style=[\"\'][^\"\']*(?<![-a-zA-Z])color\s*:', cleaned, re.IGNORECASE):
            cleaned = re.sub(
                r'(<body[^\>]*style=[\"\'])([^\"]*)([\"\'])',
                r'\g<1>color:#000000; \g<2>\g<3>',
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            )

    return cleaned

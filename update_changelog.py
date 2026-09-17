import sys

with open("CHANGELOG.md", "r") as f:
    text = f.read()

text = text.replace("## v3.3.26\n- **Fixed QProcess Stdout Pipe Truncation on Subprocess Exit**", """## v3.3.26
- **Fixed Silent Subprocess Payload Drop via Unicode Encode Failure (The True 100% Hang Fix)**:
  - Discovered that on Windows, \`sys.stdout.write\` defaults to the active OEM code page (typically \`cp1252\`) instead of UTF-8.
  - When the final JSON payload containing the translated text or speaker boundaries included unencodable characters (e.g. Spanish accents, emojis, or Unicode formatting), \`sys.stdout.write\` threw a hidden \`UnicodeEncodeError\`.
  - The internal signal emitter silently caught and swallowed the error, allowing the subprocess to cleanly exit with code 0 without ever delivering the final result to the UI.
  - Completely rewrote all subprocess IPC emit pipelines to aggressively write raw UTF-8 bytes to \`sys.stdout.buffer\`, definitively unblocking the "100% Complete" stall on Windows without data loss.

## v3.3.25
- **Fixed QProcess Stdout Pipe Truncation on Subprocess Exit**""")

with open("CHANGELOG.md", "w") as f:
    f.write(text)

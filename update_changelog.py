import sys

with open("CHANGELOG.md", "r") as f:
    text = f.read()

text = text.replace("## v3.3.27\n- **Fixed Silent Subprocess Payload Drop via Unicode Encode Failure (The True 100% Hang Fix)**:", """## v3.3.27
- **Resolved Bilingual Transcript Display Crash (`NameError: seg_indices`)**:
  - Fixed a UI rendering crash where the translation payload would successfully complete, but the text renderer would fail to display the Spanish or bilingual text due to a missing mapping reference (`seg_indices`).
  - The UI now successfully maps the translated segments back into the transcript viewer paragraph blocks, restoring bilingual mode functionality.

## v3.3.26
- **Fixed Silent Subprocess Payload Drop via Unicode Encode Failure (The True 100% Hang Fix)**:""")

with open("CHANGELOG.md", "w") as f:
    f.write(text)

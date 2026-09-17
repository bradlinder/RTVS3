import sys

with open("roadmap.txt", "r") as f:
    text = f.read()

text = text.replace("3. CURRENT RELEASE: SILENT SUBPROCESS PAYLOAD DROP & UNICODE FIX (Completed in v3.3.27)", """3. PREVIOUS RELEASE: SILENT SUBPROCESS PAYLOAD DROP & UNICODE FIX (Completed in v3.3.26)
================================================================================

[x] 3.1 FIXED UNICODE ENCODE ERRORS IN SUBPROCESS STDOUT
--------------------------------------------------------
- Found the actual root cause of the "Translation complete (100%)" application hang. 
- `sys.stdout.write` on Windows was defaulting to `cp1252`, causing unencodable characters (e.g. Spanish accents) to throw a `UnicodeEncodeError`. 
- The background thread caught and discarded this exception silently, causing the process to exit with code 0 but drop the final translated payload entirely.
- Transitioned all `emit()` IPC functions in `plugins/translation/runtime_entry.py` and `radio_tv_story_segmenter_worker.py` to write raw UTF-8 bytes to `sys.stdout.buffer` directly.

================================================================================
4. CURRENT RELEASE: UI TRANSLATION RENDERER HOTFIX (Completed in v3.3.27)
================================================================================

[x] 4.1 FIXED TRANSLATION BILINGUAL VIEW CRASH
----------------------------------------------
- Fixed a NameError (`seg_indices`) in the UI HTML rendering loop that was preventing Spanish translations from displaying in the transcript text area despite a successful subprocess payload drop.
""")

text = text.replace("4. FUTURE MILESTONE: EXPANDED NLE & DAW TIMELINE INTERCHANGE", "5. FUTURE MILESTONE: EXPANDED NLE & DAW TIMELINE INTERCHANGE")
text = text.replace("5. FUTURE MILESTONE: TEXT-DRIVEN AUDIO EDITING", "6. FUTURE MILESTONE: TEXT-DRIVEN AUDIO EDITING")

with open("roadmap.txt", "w") as f:
    f.write(text)

import sys

with open("roadmap.txt", "r") as f:
    text = f.read()

text = text.replace("2. CURRENT RELEASE: QPROCESS BUFFER FLUSH & TRUNCATION HOTFIX (Completed in v3.3.25)", """2. PREVIOUS RELEASE: QPROCESS BUFFER FLUSH & TRUNCATION HOTFIX (Completed in v3.3.25)
================================================================================

[x] 2.1 ENFORCED BUFFER FLUSH ON MISSING TRAILING NEWLINES
----------------------------------------------------------
- Fixed a bug where a final JSON payload missing a trailing newline would be left orphaned in the output buffer when `QProcess` closed its pipes.
- Updated `processing.py` and `translation.py` to aggressively parse remaining chunks via `force_flush=True`.

================================================================================
3. CURRENT RELEASE: SILENT SUBPROCESS PAYLOAD DROP & UNICODE FIX (Completed in v3.3.26)
================================================================================

[x] 3.1 FIXED UNICODE ENCODE ERRORS IN SUBPROCESS STDOUT
--------------------------------------------------------
- Found the actual root cause of the "Translation complete (100%)" application hang. 
- `sys.stdout.write` on Windows was defaulting to `cp1252`, causing unencodable characters (e.g. Spanish accents) to throw a `UnicodeEncodeError`. 
- The background thread caught and discarded this exception silently, causing the process to exit with code 0 but drop the final translated payload entirely.
- Transitioned all `emit()` IPC functions in `plugins/translation/runtime_entry.py` and `radio_tv_story_segmenter_worker.py` to write raw UTF-8 bytes to `sys.stdout.buffer` directly.""")

text = text.replace("3. FUTURE MILESTONE: EXPANDED NLE & DAW TIMELINE INTERCHANGE", "4. FUTURE MILESTONE: EXPANDED NLE & DAW TIMELINE INTERCHANGE")
text = text.replace("4. FUTURE MILESTONE: TEXT-DRIVEN AUDIO EDITING", "5. FUTURE MILESTONE: TEXT-DRIVEN AUDIO EDITING")

with open("roadmap.txt", "w") as f:
    f.write(text)

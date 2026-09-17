import sys
import json
import time

def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()

emit({"type": "progress", "percent": 100, "message": "Translation complete."})
time.sleep(0.1)
emit({"type": "finished", "result": [], "key": "en-es"})

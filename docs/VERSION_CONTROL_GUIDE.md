# Version Control & AI Safety Guide
## Managing Stable, Beta, and Dev Branches in Radio & TV Story Segmenter

This guide outlines a simple, reliable workflow for developing with both **local AI models** (Ollama, Qwen, DeepSeek via Continue, Cline, or Cursor) and **cloud models** (Gemini, Claude) while guaranteeing that stable builds remain protected from regressions.

---

## 1. The 3-Tier Branching Model

To balance rapid AI experimentation with rock-solid stability, maintain three primary branches alongside short-lived task branches:

```text
  [ ai/fix-audio ] ──┐ (Tested & verified)
                     ▼
                 [ dev ] (Daily integration & active work)
                     │
                     ▼ (Feature freeze & candidate testing)
                 [ beta ] (Release candidate installer testing)
                     │
                     ▼ (Tagged production release)
                [ stable ] (Always deployable & rock-solid)
```

### The Roles of Each Branch

| Branch | Purpose | Who Works Here? | Stability Level |
| :--- | :--- | :--- | :--- |
| **`stable`** | Official releases (e.g. `v3.2.20`). Tied to release installer builds. | Humans / release scripts only. Never edit directly. | 100% Rock-Solid |
| **`beta`** | Release candidates & pre-release testing. Used to test Inno Setup installers. | Pre-release verification. | High |
| **`dev`** | Active integration line. All verified AI task branches merge here. | Developers & AI assistants. | Working / Functional |
| **`ai/*`** | Short-lived, disposable task branches for specific features or bug fixes. | Local models (Qwen, DeepSeek) & Cloud AI. | Experimental |

---

## 2. The 5-Step AI Safety Routine

Follow this simple routine whenever you prompt an AI to write, modify, or refactor code.

### Step 1: Create a Snapshot (Your Zero-Risk Safety Net)
Before letting an AI touch files, create a project snapshot. This captures every file—including untracked files and local settings—into a standalone compressed archive:
```bash
python snapshot_manager.py --create pre-ai-experiment
```
*(If anything ever goes catastrophic, `python snapshot_manager.py --restore pre-ai-experiment` restores your workspace in 0.2s).*

### Step 2: Branch Off `dev`
Always create an isolated, disposable branch for the AI task:
```bash
# Make sure you are on dev and up to date
git checkout dev

# Create a dedicated task branch
git checkout -b ai/audio-scrubbing-fix
```

### Step 3: Run the AI with Visual Diff Preview
- **If using local tools (Cline, Continue, Cursor, Aider)**: Set edits to **Review Diff** mode. Never allow local 14B or 32B models to auto-accept changes without showing you the diff.
- Watch out for common local AI hallucination patterns:
  - Comments like `# ... rest of file unchanged ...` that wipe out unshown methods.
  - Replaced method signatures that break external callers.
  - Deletion of imports or utility helpers.

### Step 4: Run Fast Verification (`scripts/dev_check.py`)
Before accepting and committing the change, run the pre-flight verification gate:
```bash
python scripts/dev_check.py
```
This runs in ~1.5 seconds and verifies:
1. Python syntax compilation across all modified files.
2. Typing stubs (`.pyi`) synchronization.
3. Zero-dependency web preview synchronization.
4. Modular file size budget guard (<1,000 lines).
5. Targeted Tier 2 regression tests (`test_runner.py`).

### Step 5: Merge or Burn

- **Scenario A: The fix works and tests pass!**
  Commit and merge cleanly into `dev`:
  ```bash
  git add .
  git commit -m "fix(timeline): resolve audio scrubbing offset"
  git checkout dev
  git merge --no-ff ai/audio-scrubbing-fix
  git branch -d ai/audio-scrubbing-fix
  ```

- **Scenario B: The AI hallucinated or made a mess.**
  Do not waste time trying to undo manual edits. Simply burn the branch:
  ```bash
  git checkout dev
  git branch -D ai/audio-scrubbing-fix
  ```
  The broken code is 100% wiped from existence. Your `dev` branch remains pristine.

---

## 3. Promoting Changes: From `dev` to `beta` to `stable`

Once a collection of features and fixes is stabilized on `dev`:

### Promoting to `beta`:
```bash
git checkout beta
git merge dev
# Run the full diagnostic suite and build test installers
python test_runner.py --quiet --all
python build_installer.py
```
Test the resulting Windows `.exe` installer or Linux package.

### Promoting to `stable`:
Once verified on real media files and audio samples:
```bash
# 1. Update version across all locations synchronously
python bump_version.py --patch  # or: python bump_version.py 3.2.21

# 2. Merge into stable and tag
git checkout stable
git merge beta
git tag -a v3.2.21 -m "Release v3.2.21"

# 3. Create verified-stable snapshot
python snapshot_manager.py --create v3.2.21-release --stable
```

---

## 4. Emergency Recovery Cheat Sheet

### "The AI just mangled my working directory, but I haven't committed yet!"
Discard all uncommitted modifications and extra untracked files immediately:
```bash
# Discard all changes to tracked files
git restore .

# Remove any random scratch files or temp folders created by the AI
git clean -fd
```
Your working folder is now back to your last clean commit.

---

### "I accidentally committed a bad AI change to my branch. How do I undo it?"
Undo the last commit while keeping or wiping the files:
```bash
# Option A: Wipe the commit and the files completely
git reset --hard HEAD~1

# Option B: Undo the commit, but keep the files in your editor to inspect
git reset --soft HEAD~1
```

---

### "I don't know what state Git is in, and things seem broken."
Use the project snapshot fallback to bypass Git entirely:
```bash
# List all saved snapshots
python snapshot_manager.py --list

# Restore your last verified stable point
python snapshot_manager.py --restore stable
```

---

## 5. Summary Rules of Thumb

1. **`stable` is sacred**: No AI ever writes to `stable`. Only merges from `beta` land here.
2. **`dev` is the launchpad**: Branch off `dev` for every AI prompt.
3. **Branches are free**: Delete broken AI branches with `git branch -D` without hesitation. Starting a fresh 1-minute prompt is always faster than fixing a degraded 20-minute hallucination.
4. **Always verify before merging**: Run `python scripts/dev_check.py` before merging any AI branch back into `dev`.

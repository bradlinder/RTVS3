# Universal "Segment / Segments" Terminology & Display Title Unification

Standardize all curated timeline regions and episode cuts across the application as **Segment / Segments** (`Segmento / Segmentos` in Spanish), remove the cosmetic vocabulary selector and context-dependent Stories/Songs label switching, and unify all remaining menus, tooltips, dialogs, and display titles under **Radio & TV Segmenter**.

## User Review & Critical Decisions

> [!IMPORTANT]
> The following architectural and UX choices were confirmed during clarification and govern this implementation:

- **Confirmed Decision 1 — Universal "Segment / Segments" Vocabulary**: All timeline cuts, sidebar headers, buttons, context menus, floating bubbles, hover readouts, and export scopes will universally use **Segment / Segments** (`Segmento / Segmentos` in Spanish). The `Stories`, `Clips`, and `Songs` UI label modes and the Preferences vocabulary selector will be removed.
- **Confirmed Decision 2 — Distinct Transcript Speech "Blocks" vs. Timeline "Segments"**: Individual speaker dialogue turns in the transcript editor remain labeled as **Blocks / Speaker Blocks** (e.g., *Split Speaker Block*, *Split Block at Playhead*, *Merge with Next Block*), ensuring zero ambiguity with timeline **Segments**.
- **Confirmed Decision 3 — Retain Voice vs. Music Audio Detection Algorithm**: The audio analysis mode in Preferences (*Voice / Speech* vs. *Music* silence/boundary detection) remains available for acoustic boundary detection, but switching detection modes will no longer relabel the UI from *Segments* to *Songs*.
- **Confirmed Decision 4 — Unify Application Display Title**: User-facing window titles, About menu items, and dialogs will consistently display **Radio & TV Segmenter**, while internal storage identifiers (`INTERNAL_APP_ID = "RadioTVStorySegmenter"`) and `.rtvs` project file format headers remain untouched for 100% backward compatibility.

---

## Effort Estimate & Risk Assessment

- **Estimated Time**: **~3 to 5 minutes** (a single automated pass across ~14 UI and test modules, removing roughly 60 lines of conditional branching and replacing ~25 display strings).
- **Risk Level**: **Low** — strictly limited to user-facing display strings, with zero changes to audio DSP, project file formats, or internal variable names.
- **Specific Risks & Mitigations**:
  1. **Risk: Existing `.rtvs` Project Files or `QSettings` Failing to Load**
     - *Why it could happen*: If internal format strings (`"format": "Radio & TV Story Segmenter Project"`), JSON keys (`"stories"`), or `INTERNAL_APP_ID` (`"RadioTVStorySegmenter"`) were renamed to match the display title.
     - *Mitigation*: Strictly separate `APP_DISPLAY_NAME` (`"Radio & TV Segmenter"`) from `INTERNAL_APP_ID` and project schema keys, which remain 100% untouched.
  2. **Risk: Diagnostic Test Suite Failures on Hardcoded String Assertions**
     - *Why it could happen*: Several automated tests in `diagnostic_editor_tests.py` and `diagnostic_batch_tests.py` assert exact UI text (e.g., `assert host.stories_header.text() == "Stories (2) — [03:45.5]"` or `"Story #1:"` in timeline hover tooltips).
     - *Mitigation*: Update the corresponding test expectations in the same pass and run the diagnostic test suite before completion.
  3. **Risk: Saved Keyboard Shortcut Customizations Resetting**
     - *Why it could happen*: If shortcut `action_id` keys (like `"play_current_story"`, `"mark_story_start"`) were renamed along with their display names.
     - *Mitigation*: Keep all internal `action_id` and `attr_name` identifiers identical; only change the human-readable `name` and `description` fields.
  4. **Risk: REAPER Companion Bridge Desynchronization**
     - *Why it could happen*: The REAPER Lua scripts read `latest_transcript_index.json` and `latest_clip_cue.json`, which expect `"stories"` and `"segments"` keys in the JSON payload.
     - *Mitigation*: Keep the IPC JSON schema keys unchanged; only user-facing UI labels in RTVS change.

---

## 1. Overview & Core Concept

- **What It Does**: Eliminates mixed terminology across the desktop suite by establishing a clean two-tier nomenclature: **Blocks** for speaker dialogue turns in the transcript, and **Segments** for curated time ranges on the timeline and sidebar.
- **Target Audience / Persona**: Broadcast journalists, podcast producers, audio engineers (REAPER / DAW workflows), and music archivists who want a predictable, self-explanatory interface that matches the application's name (**Radio & TV Segmenter**).
- **Key Value**:
  - Removes cognitive friction and Preferences clutter by eliminating cosmetic mode switching.
  - Fixes all 8 remaining hardcoded `"Story"` / `"Stories"` UI surfaces so every context menu, tooltip, floating selection bubble, and dialog speaks the same language.
  - Reduces code complexity and line count across core modules while keeping saved `.rtvs` projects 100% compatible.

---

## 2. User Experience & Visual Design

- **Key User Flows**:
  1. **Creating a Segment from Transcript Selection**: Highlighting text in the transcript displays the floating selection bubble with **`+ Segment`** (*"Create a new segment cut from highlighted text (Enter)"*). Right-clicking the selection offers **`Add Selected Text to New Segment`** (or **`Add Selected Sections to New Segments (N)`** for multi-selection).
  2. **Managing Segments in the Right Sidebar**: The sidebar header displays **`Segments`** (and **`Segments (2) — [03:45.5]`** when items are selected), accompanied by **`Segment Settings`**, **`Add Segment`**, **`Set Segment Start`**, **`Set Segment End`**, **`Segment Metadata...`**, and form placeholders **`Segment title / headline`** and **`Segment author / reporter / contributor`**.
  3. **Auditioning & Inspecting on the Timeline**: Hovering over a region on the waveform canvas displays **`Segment #1: [Title] — Duration: 02:30.5`**. Right-clicking a region on the timeline or in the sidebar list offers **`Audition Segment Playback`**, **`Copy Segment Transcript`**, **`Copy Segment as Audio Clip`**, **`Segment & Post Metadata...`**, and **`Delete Selected Segment`**.
  4. **Exporting & Auto-Detection**: Opening the Export dialog presents **`Selected Segments`**, **`All Segments`**, **`Full Episode`**, and **`Full Episode & All Segments`**. The Tools menu consistently shows **`Detect Segments...`** / **`Detect Segments (Complete)`** regardless of whether the acoustic detector is set to Voice or Music mode.
- **Visual Identity & Theme**:
  - *Aesthetic Direction*: Clean, native desktop broadcast workstation utility with zero decorative emoji clutter.
  - *Color Palette & Mood*: Preserves the application's high-contrast dark, light, and accessibility themes without visual regressions.
  - *Typography & Hierarchy*: Crisp, consistent title-case action labels and tabular-numeral duration readouts (`[MM:SS.d]`).
- **Interactive Feedback & Motion**:
  - Instant live language switching between English (`Segment` / `Segments`) and Spanish (`Segmento` / `Segmentos`) without requiring an application restart.

---

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: Universal "Segments" Over Configurable Cosmetic Modes**
  - *Chosen Approach*: Hard-standardize the vocabulary resolver to return `Segment` / `Segments` (and `Segmento` / `Segmentos` in Spanish) and remove the Preferences vocabulary dropdown.
  - *Why*: A single universal term that matches the application name (**Radio & TV Segmenter**) works naturally for news broadcast segments, podcast chapters, DAW audio clips, and music segments alike—without forcing users to configure cosmetic preferences or encounter inconsistent labels.
  - *Alternatives Considered*: Maintaining a 5-way Preferences dropdown (`Auto`, `Stories`, `Clips`, `Segments`, `Songs`), which added unnecessary settings surface area and conditional branches across dozens of menus.
- **Decision 2: Decouple Acoustic Detection Mode from UI Terminology**
  - *Chosen Approach*: Keep the *Voice / Speech* vs. *Music* detection algorithm selector in Preferences (under Segment Detection Settings) so users can still tune how silence and musical boundaries are detected, but remove all `is_music` UI relabeling.
  - *Why*: Preserves full audio DSP capability for music shows while keeping the user interface terminology 100% consistent.
- **Decision 3: Zero-Mutation Persistence & Backward Compatibility**
  - *Chosen Approach*: Keep internal Python data structures (`Story` class, `stories` JSON array key, `"format": "Radio & TV Story Segmenter Project"`, and `INTERNAL_APP_ID = "RadioTVStorySegmenter"`) intact under the hood.
  - *Why*: Guarantees that existing `.rtvs` project archives, `QSettings` user profiles, REAPER Lua companion scripts, and undo/redo stacks continue to load and operate with zero breakage.

---

## 4. Technical Architecture & Data Strategy *(Technical Reference)*

- **Architecture & Component Diagram**:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                   Centralized Terminology Resolver                        │
│     get_story_vocabulary(win_or_settings, language) -> StoryVocabulary    │
│        Always resolves to: "Segment" / "Segments" (EN)                    │
│                            "Segmento" / "Segmentos" (ES)                  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│   Sidebar & Menus     │   │  Transcript & Canvas  │   │  Dialogs & Shortcuts  │
│ ───────────────────── │   │ ───────────────────── │   │ ───────────────────── │
│ • Header & Counter    │   │ • Right-Click Menus   │   │ • Export Scope Combo  │
│ • Add / Set Start/End │   │ • Selection Bubble    │   │ • Segment Metadata    │
│ • Segment Settings    │   │   (+ Segment)         │   │   Window Title        │
│ • Title & Author      │   │ • Waveform Hover &    │   │ • Shortcuts Schema    │
│   Placeholders        │   │   Edge Drag Readouts  │   │   (Play/Mark/Delete)  │
│ • Tools > Detect      │   │ • Sidebar Item Menu   │   │ • App Display Title   │
│   Segments            │   │   (Audition/Copy/Del) │   │   (Radio & TV         │
│ • View > Segments     │   │                       │   │    Segmenter)         │
└───────────────────────┘   └───────────────────────┘   └───────────────────────┘
```

- **Data Model & State**:
  - `StoryVocabulary` (`NamedTuple`) remains the single source of truth for localized UI strings (`singular="Segment"`, `plural="Segments"`, `add_label="Add Segment"`, `set_start="Set Segment Start"`, `set_end="Set Segment End"`, `metadata_btn="Segment Metadata..."`, `settings_btn="Segment Settings"`, `detect_action="Detect Segments"`, `panel_title="Segments Panel"`), simplifying callers while supporting English and Spanish.
  - Removes `ui_vocabulary_mode` from Preferences UI builders, save handlers, and reset dialogs.
- **Interactive Component & State Mapping (Completed Checklist)**:
  1. [x] **Central Resolver & Preferences Cleanup**:
     - Simplified `get_story_vocabulary()` to universally return `Segment` / `Segments` (`Segmento` / `Segmentos` in Spanish) and removed `vocab_combo` and `ui_vocabulary_mode` from Preferences General tab, save routine, and factory reset handlers.
     - Kept Voice vs. Music detection algorithm in Preferences Media tab while updating labels to "Music / Track Breaks (Music Programs)" and tooltips to consistently reference segment boundaries.
  2. [x] **Transcript Right-Click Context Menu**:
     - Updated to `Add Selected Text to New Segment` / `Add Selected Sections to New Segments ({count})`.
     - Updated active span actions: `Audition Segment Playback`, `Copy Segment Transcript`, `Copy Segment as Audio Clip`, and `Segment & Post Metadata...`.
  3. [x] **Floating Text Selection Bubble**:
     - Updated button label from `+ Story` to `+ Segment` and tooltip to *"Create a new segment cut from highlighted text (Enter)"*.
  4. [x] **Sidebar List Right-Click Context Menu & Edit Form**:
     - Updated list item context menu actions to `Audition Segment Playback`, `Copy Segment Transcript (Ctrl+C)`, `Export Selected Segments...`, `Segment & Post Metadata...`, and `Delete Selected Segment`.
     - Updated Title placeholder to `Segment title / headline` and Author input placeholder to `Segment author / reporter / contributor` (and Spanish equivalents in `media_batch.py`).
     - Updated card badge prefix to `Segment 1`, `Segment 2` (or `Segmento 1`, `Segmento 2`).
  5. [x] **Timeline Waveform Hover & Drag Readouts**:
     - Updated waveform body hover tooltips and status bar messages from `Story #N:` to `Segment #N:`.
  6. [x] **Tools Menu & Processing Status**:
     - Updated `update_processing_menu_status()` to always display `Detect Segments (Complete)` / `&Detect Segments...` (or `&Detectar segmentos`), removing dynamic song switching.
  7. [x] **Metadata & Fades Dialog Titles**:
     - Updated metadata dialog window title to `Segment Settings & Metadata` and info header.
  8. [x] **Keyboard Shortcuts Registry & Action Bindings**:
     - Updated category and action names in the shortcuts reference: `Play Current Segment Only`, `Mark Segment In-Point ([)`, `Mark Segment Out-Point (])`, and `Delete Selected Segment` while keeping `action_id` keys identical.
  9. [x] **Application Display Title Unification**:
     - Updated `&About Radio & TV Segmenter` in Help menu to match `APP_DISPLAY_NAME = "Radio & TV Segmenter"`, while keeping `INTERNAL_APP_ID = "RadioTVStorySegmenter"` and `.rtvs` file format headers intact for 100% backward compatibility.
  10. [x] **Diagnostic Test Suite Synchronization**:
      - Updated diagnostic assertions in `diagnostic_editor_tests.py` to assert universal `Segment` / `Segments` (`Segmento` / `Segmentos`) headers, tooltips, and timeline hover strings. All tests and syntax compilation checks pass.

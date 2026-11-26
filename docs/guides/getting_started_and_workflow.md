# Getting Started & Essential Workflow

This guide covers the core workflow of Radio & TV Segmenter: loading media, generating transcripts, detecting segments, editing speaker labels, and navigating the interactive timeline.

---

## 1. Opening Audio & Video Media

You can load media into RTVS3 in several ways:
- **Drag-and-Drop**: Drag any supported audio or video file directly onto the timeline canvas or into the transcript area.
- **File Menu**: Go to **File > Open Media...** (or press **Ctrl+O**).
- **Import Existing Document**: Go to **File > Open Document...** (**Ctrl+Alt+O**) to bring `.txt`, `.docx`, `.pdf`, `.html`, or `.md` transcripts into the workspace for editing or segmenting.
- **Open Remote Episode (YouTube or WordPress)**: Go to **File > Open Remote Episode** to import already-published back-catalog episodes:
  - **From YouTube Video...** (**Ctrl+Alt+Y**): Paste any YouTube URL to auto-install/use `yt-dlp`, download at selectable quality (defaulting to 1080p MP4 for crisp screenshots), optionally pre-seed YouTube chapters as stories, and auto-bind the YouTube URL for WordPress full-episode and per-story embeds.
  - **From Existing WordPress Post...**: Paste an older WordPress episode URL to fetch its original publication date, title, and show-notes excerpt and download its MP3 into the Managed Remote Media Cache (or pair with a local audio file).
  - **Re-download Archived Source Media...**: If a previously cached remote download was cleared to free disk space, reopening its `.rtvs` project keeps all transcripts, stories, and metadata editable and offers 1-click re-download.
- **Recent Projects**: Go to **File > Recent Projects** to quickly reopen past `.rtvs` project files.

### Supported File Formats:
- **Audio**: MP3, WAV, FLAC, M4A, AAC, OGG, OPUS, AIFF, WMA.
- **Video**: MP4, MOV, MKV, WEBM, AVI, WMV, MPEG, TS, M4V.

When media is loaded:
- RTVS3 automatically generates a multi-resolution waveform pyramid on the timeline.
- For video files, a thumbnail filmstrip is generated above the timeline tracks.
- Press **Ctrl+Shift+V** (**View > Timeline > Video Preview Window**) to open a floating video player that synchronizes with timeline scrubbing.
- **Broadcast Loudness Normalization**: Press **Ctrl+Alt+N** (**Tools > Normalize Audio Loudness...**) to inspect EBU R128 / ITU BS.1770 metrics (Integrated LUFS, LRA, True Peak) with non-destructive boost preview, or configure automatic normalization in **Settings > Preferences... > Audio Settings**.

---

## 2. Playback & Timeline Navigation

- **Play / Pause**: Press **Spacebar**.
- **Scrubbing**: Click and drag anywhere along the timeline ruler or waveform.
- **Zooming**: Use **Ctrl + Mouse Wheel** over the timeline, or press the **+** and **-** zoom buttons. You can zoom from full-episode overview down to a fraction of a second (300x zoom) for precise edits.
- **Playback Speed**: Adjust the speed dropdown between **0.5x** and **3.0x** to listen at your preferred pace.
- **Volume & Fades**: Use the master volume slider. Configure **Audio Fades** (**Ctrl+Shift+F**) to preview real-time volume fade-ins and fade-outs on segments.

---

## 3. Transcription & Speaker Diarization

RTVS3 uses state-of-the-art AI speech models running locally on your computer to convert spoken audio into aligned text.

1. Click **Transcribe Audio...** (**Ctrl+T**) or **Detect Speakers...** (**Ctrl+D**), or launch the full pipeline via **Tools > Multi-Stage Processing...** (**Ctrl+R**).
2. Choose your ASR engine and language (English, Spanish, or Auto-Detect): **faster-whisper** models (Tiny, Base, Small, Medium, Large) or **Parakeet TDT** (`sherpa-onnx`) for ultra-fast local English transcription.
3. Tune **Minimum Segment Length** and diarization defaults under **Settings > Preferences... > Detection**.
4. The processing panel shows live progress through each stage:
   - **VAD (Voice Activity Detection)**: Isolates spoken speech from background silence or noise.
   - **Transcription**: Generates word-level aligned text with accurate timestamps, optionally seeded with your **Glossary & Custom Vocabulary...** (**Ctrl+Alt+V**).
   - **Diarization**: Distinguishes between speakers (*Speaker 1*, *Speaker 2*, etc.) and can auto-tag recurring hosts using saved **Station Voice Profiles**.

---

## 4. Editing Transcripts, Speakers & Editorial Comments

The center panel features an interactive transcript editor:
- **Karaoke Word Tracking**: Words light up in yellow as audio plays so you can follow along.
- **Click to Seek**: Click any timestamp `[00:00]` or word to instantly jump playback to that second.
- **Assign & Clean Up Speaker Names**: Double-click any speaker header to rename it across the project (check **Save to Station Voices** when assigning recurring hosts), or open **Tools > Voice Profile Tools**:
  - **Manage Speakers & Detection Clusters...**: Audit speaker durations, rename/merge duplicate clusters, toggle per-speaker **Station Voice** profiles, and run **Fix Speaker Names...** (with *Preserve Case*, whitespace **Trim**, **Add to Glossary**, and grouped Undo).
  - **Manage Voice Profiles...**, **Teach / Match Voice Across Project...**, and **Refine Rapid Dialog Turns (A/B Classifier)...**: Save, rename, or match persistent host voices across broadcasts.
- **Find & Replace**: Press **Ctrl+F** to search and replace words. Check **Include Speakers** (or launch **Fix Speaker Names...**) to clean up speaker labels too.
- **Edit Mode & Rich Formatting**: Press **F2** (**View > Transcript > Edit Transcript Mode**) to edit spoken text directly; press **Ctrl+M** to attach **Editorial Comments** (**View > Comments Sidebar Panel** / `Ctrl+Alt+C`, highlights in **View > Transcript > Show Comment Highlights** / `Ctrl+Alt+H`).
- **Offline Spellcheck & Glossary**: Segment titles and WordPress metadata fields highlight unrecognized words automatically. Right-click any underlined word for spelling suggestions, **Add '<word>' to Glossary**, or **Ignore (This Session)** (Glossary terms and confirmed speaker names are allowlisted automatically).

---

## 5. Segment Creation & Editing

RTVS3 organizes broadcasts into distinct, individual segments that can be exported separately or together.

### Automatic Segment Detection:
Press **Ctrl+Shift+A** (**Tools > Detect Segments...**). The engine analyzes topic boundaries, speech pauses, and speaker turns to segment your episode automatically.

### Manual Segment Creation:
1. Press `[` to mark a segment start and `]` to mark a segment end at the current playhead position.
2. Or **right-click and drag** across any region on the timeline waveform to draw a selection, then right-click and choose **Add Segment from Selection**.
3. A new segment appears in the right-hand **Segments** panel.

### Adjusting Segment Boundaries & Fades:
- **Move Boundaries**: Click and drag the left or right edge handle of any segment box on the timeline.
- **Audio Fades**: Drag the fade handle at the top corners of a segment to set fade-in and fade-out durations (e.g., 1.5 seconds) with linear, exponential, or S-curve shapes.
- **Segment Metadata & ID3 Tags**: Select a segment to edit its title, summary, author, and categories, or press **Ctrl+Shift+I** (**Tools > ID3 Tag Editor (MP3)...**) to embed broadcast MP3 metadata and artwork.

---

## 6. Unified Export, Batch Processing & Maintenance

- **Unified Export Center**: Press **Ctrl+E** (**File > Export...**) to export split audio cuts, Word/PDF cue sheets, WordPress draft posts, or DAW timelines.
- **Copy YouTube Chapters**: Press **Ctrl+Shift+Y** (**File > Copy YouTube Chapters to Clipboard**) to copy formatted chapter markers instantly.
- **Batch Processing Center**: Go to **Tools > Batch Processing...** (**Ctrl+Shift+B**) to queue and process multiple episodes or media files sequentially in the background.
- **Settings, Shortcuts & Maintenance**: Customize hotkeys under **Settings > Customize Keyboard Shortcuts...** (**F8**), back up/restore settings via **Settings > Backup & Restore Settings...**, free cached waveforms/sidecars via **Tools > Clear Temporary Cache...**, inspect/cap/clear downloaded YouTube & WordPress episodes via **Tools > Manage Cached Remote Media...** (or **Settings > Preferences... > Cleanup Data**), or selectively reset open project data under **Edit > Clear / Purge Project Data...**.

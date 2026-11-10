# Getting Started & Essential Workflow

This guide covers the core workflow of Radio & TV Segmenter: loading media, generating transcripts, detecting segments, editing speaker labels, and navigating the interactive timeline.

---

## 1. Opening Audio & Video Media

You can load media into RTVS3 in several ways:
- **Drag-and-Drop**: Drag any supported audio or video file directly onto the timeline canvas or into the transcript area.
- **File Menu**: Go to **File > Open Media...** (or press **Ctrl+O**).
- **Recent Projects**: Go to **File > Recent Projects** to quickly reopen past files.

### Supported File Formats:
- **Audio**: MP3, WAV, FLAC, M4A, AAC, OGG, OPUS, AIFF, WMA.
- **Video**: MP4, MOV, MKV, WEBM, AVI, WMV, MPEG, TS, M4V.

When media is loaded:
- RTVS3 automatically generates a multi-resolution waveform pyramid on the timeline.
- For video files, a thumbnail filmstrip is generated above the timeline tracks.
- Press **Ctrl+Shift+V** (**View > Video Preview Window**) to open a floating video player that synchronizes with timeline scrubbing.

---

## 2. Playback & Timeline Navigation

- **Play / Pause**: Press **Spacebar**.
- **Scrubbing**: Click and drag anywhere along the timeline ruler or waveform.
- **Zooming**: Use **Ctrl + Mouse Wheel** over the timeline, or press the **+** and **-** zoom buttons. You can zoom from full-episode overview down to a fraction of a second (300x zoom) for precise edits.
- **Playback Speed**: Adjust the speed dropdown between **0.5x** and **3.0x** to listen at your preferred pace.
- **Volume & Fades**: Use the master volume slider. Enable **Audio Fades** to preview real-time volume fade-ins and fade-outs on segments.

---

## 3. Transcription & Speaker Diarization

RTVS3 uses state-of-the-art AI speech models running locally on your computer to convert spoken audio into aligned text.

1. Click **Transcribe Audio...** (**Ctrl+T**) or **Detect Speakers...** (**Ctrl+D**), or launch the full pipeline via **Tools > Multi-Stage Processing...** (**Ctrl+R**).
2. Choose your language (e.g., English, Spanish, or Auto-Detect) and Whisper model size (Tiny, Base, Small, Medium, Large).
3. The processing panel shows live progress through each stage:
   - **VAD (Voice Activity Detection)**: Isolates spoken speech from background silence or noise.
   - **Transcription**: Generates word-level aligned text with accurate timestamps.
   - **Diarization**: Distinguishes between different speakers (*Speaker 1*, *Speaker 2*, etc.).

---

## 4. Editing Transcripts & Assigning Speakers

The center panel features an interactive transcript editor:
- **Karaoke Word Tracking**: Words light up in yellow as audio plays so you can follow along.
- **Click to Seek**: Click any timestamp `[00:00]` or word to instantly jump playback to that second.
- **Assign Speaker Names**: Double-click any speaker header to rename it across the entire project (e.g. changing *Speaker 1* to *Jane Doe*), or open the Speaker Manager (**Ctrl+Alt+S**).
- **Find & Replace**: Press **Ctrl+F** to search and replace words. Check **Include Speakers** to update spoken dialogue and speaker headers simultaneously.
- **Edit Mode**: Press **Ctrl+E** while focused on the transcript (or click **Edit Transcript**) to edit spoken text directly.

---

## 5. Segment Creation & Editing

RTVS3 organizes broadcasts into distinct, individual segments that can be exported separately or together.

### Automatic Segment Detection:
Click **Detect Segments...** (or press **Ctrl+Shift+A**). The engine analyzes topic boundaries, speech pauses, and speaker turns to segment your episode automatically.

### Manual Segment Creation:
1. Press `[` to mark a segment start and `]` to mark a segment end at the current playhead position.
2. Or **right-click and drag** across any region on the timeline waveform to draw a selection, then right-click and choose **Add Segment from Selection**.
3. A new segment appears in the right-hand **Segments** panel.

### Adjusting Segment Boundaries & Fades:
- **Move Boundaries**: Click and drag the left or right edge handle of any segment box on the timeline.
- **Audio Fades**: Drag the fade handle at the top corners of a segment to set fade-in and fade-out durations (e.g., 1.5 seconds) with linear, exponential, or S-curve shapes.
- **Segment Metadata**: Select a segment in the Segments list and click **Segment Metadata...** to edit its title, summary, author, and categories.

---

## 6. Unified Export & Batch Processing

- **Unified Export Center**: Press **Ctrl+E** (**File > Export...**) to export split audio cuts, Word/PDF cue sheets, WordPress draft posts, or DAW timelines.
- **Copy YouTube Chapters**: Press **Ctrl+Shift+Y** (**File > Copy YouTube Chapters to Clipboard**) to copy formatted chapter markers instantly.
- **Batch Processing Center**: Go to **File > Batch Processing...** (**Ctrl+Shift+B**) to queue and process multiple episodes or media files sequentially in the background.

# Getting Started & Essential Workflow

This guide covers the core workflow of Radio & TV Story Segmenter: loading media, generating transcripts, detecting stories, editing speaker labels, and navigating the interactive timeline.

---

## 1. Opening Audio & Video Media

You can load media into RTVS3 in several ways:
- **Drag-and-Drop**: Drag any supported audio or video file directly onto the timeline canvas or into the transcript area.
- **File Menu**: Go to **File > Open Media...** (or press **Ctrl+O**).
- **Recent Projects**: Go to **File > Open Recent...** to quickly reopen past files.

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
- **Volume & Fades**: Use the master volume slider. Enable **Audio Fades** to preview real-time volume fade-ins and fade-outs on segmented stories.

---

## 3. Transcription & Speaker Diarization

RTVS3 uses state-of-the-art AI speech models running locally on your computer to convert spoken audio into aligned text.

1. Click **Transcribe & Diarize** (or press **Ctrl+T**).
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
- **Assign Speaker Names**: Double-click any speaker header to rename it across the entire project (e.g. changing *Speaker 1* to *Jane Doe*).
- **Find & Replace**: Press **Ctrl+F** to search and replace words. Check **Include Speakers** to update spoken dialogue and speaker headers simultaneously.
- **Edit Mode**: Press **Ctrl+E** while focused on the transcript (or click the pencil icon) to edit spoken text directly.

---

## 5. Story Segmentation

RTVS3 organizes broadcasts into distinct, individual stories that can be exported separately or together.

### Automatic Story Detection:
Click **Auto-Detect Stories** (or press **Ctrl+D**). The engine analyzes topic boundaries, speech pauses, and speaker turns to segment your episode automatically.

### Manual Story Creation:
1. **Right-click and drag** across any region on the timeline waveform to draw a selection.
2. Right-click the highlighted region and choose **Add Story from Selection**.
3. A new story appears in the right-hand **Stories** panel.

### Adjusting Story Boundaries & Fades:
- **Move Boundaries**: Click and drag the left or right edge handle of any story box on the timeline.
- **Audio Fades**: Drag the fade handle at the top corners of a story to set fade-in and fade-out durations (e.g., 1.5 seconds) with linear, exponential, or S-curve shapes.
- **Story Metadata**: Right-click a story in the Stories list and select **Story & Post Metadata...** to edit its title, summary, author, and categories.

---

## 6. Batch Processing Center

If you have multiple episodes or audio files to process:
1. Go to **Tools > Batch Processing Center...** (or press **Ctrl+Shift+B**).
2. Drag and drop a folder or list of media files into the queue.
3. Configure your desired pipeline (e.g., Transcribe + Diarize + Story Detect + Export).
4. Click **Start Batch**. RTVS3 processes each file sequentially in the background.

# Radio & TV Story Segmenter v3

Radio & TV Story Segmenter is a cross-platform desktop application built with Python and PySide6. Designed for broadcast journalists, audio producers, podcasters, and researchers, it transcribes long-form audio and video recordings, labels distinct speakers, translates text across languages, and segments programs into independent, publishable stories.

---

## Features

* Automated Speech Transcription: Powered by faster-whisper (CTranslate2) with local Whisper models from tiny up to large-v3.
* Speaker Diarization: Uses diarize (Silero VAD + WeSpeaker ONNX embeddings) to detect and attribute speakers across multi-person interviews and panel segments without requiring heavy PyTorch dependencies in the core application.
* Bilingual Translation: Direct in-app Spanish/English translation using local Helsinki-NLP MarianMT transformer models with sentence-level alignment via an isolated plugin runtime.
* Interactive Transcript Editor: Click-to-seek playback navigation, inline text correction, customizable font scaling, and speaker reattribution tools.
* Visual Waveform Timeline: Synchronized timeline with zoom, scrub markers, region selection, and optional video thumbnail strips.
* Hardware Acceleration: Optional NVIDIA CUDA acceleration (Windows) for faster-whisper and diarization via an on-demand download, keeping the default application CPU-first and lightweight across platforms.
* Multi-Format Publishing & Exports:
  * Standard Subtitles (SRT, VTT)
  * Plain and annotated transcripts (TXT, Markdown, CSV)
  * Cockos Reaper Digital Audio Workstation project markers (EDL)
  * WordPress REST API direct draft/post creation
  * Audio segment extractions sliced directly through FFmpeg



---

## Installation & Setup

### 1. Prerequisites

* Python: 3.10 to 3.12 (64-bit recommended)
* FFmpeg: Must be installed and accessible in your system PATH (or placed in the project root directory).
* Node.js 18+ & npm: (Optional) Only required if building the integrated React/Vite transcript preview components.

### 2. Environment Configuration

Clone the repository and set up a virtual environment:

Windows:
python -m venv venv
venv\Scripts\activate

Linux / macOS:
python3 -m venv venv
source venv/bin/activate

Install standard application requirements:
pip install -r requirements.txt

### 3. GPU Hardware Acceleration (Optional - Windows NVIDIA)

The base application is CPU-first by design to keep download and install footprints minimal and universally compatible across platforms. Diarization (WeSpeaker ONNX) and Translation (CTranslate2 INT8) run exclusively on optimized CPU backends with zero CUDA bloat. On Windows systems equipped with a supported NVIDIA GPU, you can optionally download and enable a dedicated CUDA-accelerated Whisper transcription environment:
1. Open the application.
2. Go to **Settings > GPU Acceleration (NVIDIA CUDA)...**
3. Click **Download and Install** to provision the isolated CUDA runtime.
4. Check **Use GPU acceleration when available**.

---

## Running the Application

Launch the desktop client via:
python RadioTVSegmenter.py

Or on Windows:
Run_RadioTVSegmenter.bat

---

## Workflows & Export Integrations

### Segmenting Stories

1. Load Media: Drag and drop an audio or video file onto the timeline canvas or select File -> Open Media...
2. Process Pipeline: Use Tools -> Multi-Stage Processing... (Ctrl+R / Cmd+R) to run transcription, speaker detection, and automated story segmentation in sequence.
3. Refine Segments: Highlight text in the transcript or drag region handles on the timeline, then click Add Story to create segment boundaries.

### Cockos Reaper DAW (EDL Marker Export)

* Exports selected stories and timeline cuts into a standard EDL (.edl) edit decision list compatible with Reaper and Samplitude.
* Import into Reaper:
1. Open Cockos Reaper.
2. Choose File -> Open Project or Item -> Open Items in Editor.
3. Select the generated .edl file. Segments will map onto the timeline with speaker markers preserved.



### WordPress Direct Publishing

* Pushes selected segmented stories and transcribed body copy directly to WordPress sites via the REST API.
* Setup & Authentication:
1. In WordPress Admin, navigate to Users -> Profile.
2. Scroll down to Application Passwords, enter a descriptive name (e.g., StorySegmenter), and click Add New Application Password.
3. Copy the 24-character generated password (with spaces) into the application's WordPress Export dialog along with your site URL and username. Note: Your regular login password is not accepted by the REST API.



---

## Keyboard Shortcuts

All keyboard shortcuts can be viewed at any time by pressing <kbd>F1</kbd> (or <kbd>Cmd+?</kbd> on macOS) to open the interactive, searchable **Keyboard Shortcuts Reference** dialog, and can be fully customized in **Preferences -> Keyboard Shortcuts** (<kbd>Ctrl+,</kbd> / <kbd>Cmd+,</kbd>).

| Category | Action | Windows / Linux | macOS | Description |
| --- | --- | --- | --- | --- |
| **File & Project** | Open Media... | `Ctrl+O` | `Cmd+O` | Select an audio or video file to open and process |
| **File & Project** | Open Document... | `Ctrl+Alt+O` | `Cmd+Alt+O` | Open an existing .rtvs project document file |
| **File & Project** | Save Document | `Ctrl+S` | `Cmd+S` | Save current project, audio offsets, stories, and edits to .rtvs file |
| **File & Project** | Save Document As... | `Ctrl+Shift+S` | `Cmd+Shift+S` | Save current project to a new .rtvs file location |
| **File & Project** | Export Center... | `Ctrl+E` | `Cmd+E` | Open the Unified Export Center for audio, text, transcripts, and plugins |
| **File & Project** | Batch Processing... | `Ctrl+Shift+B` | `Cmd+Shift+B` | Open Batch Audio / Video Transcription and Diarization Manager |
| **File & Project** | Backup & Restore... | *Unassigned* | *Unassigned* | Open project snapshot backup and restore manager |
| **File & Project** | Multi-Stage Pipeline... | `Ctrl+Shift+M` | `Cmd+Shift+M` | Open automated multi-model pipeline configuration |
| **File & Project** | Manage AI Models... | `Ctrl+M` | `Cmd+M` | Download, delete, verify, and monitor Whisper and ASR neural weights |
| **File & Project** | Preferences... | `Ctrl+,` | `Cmd+,` | Open application settings, audio playback, theming, and shortcuts |
| **File & Project** | Export Diagnostic Bundle... | `Ctrl+Alt+D` | `Cmd+Alt+D` | Export system diagnostic zip bundle for bug reports and support |
| **File & Project** | Exit Application | `Ctrl+Q` | `Cmd+Q` | Close the application |
| **Playback & Transport** | Play / Pause Audio | `Space` | `Space` | Toggle audio playback on/off from current playhead position |
| **Playback & Transport** | Jump Back (Short / 5s) | `Left` | `Left` | Rewind audio playhead by configured short jump distance (default 5s) |
| **Playback & Transport** | Skip Backward | `Left` | `Left` | Rewind audio playhead by configured jump distance |
| **Playback & Transport** | Jump Forward (Short / 5s) | `Right` | `Right` | Advance audio playhead by configured short jump distance (default 5s) |
| **Playback & Transport** | Skip Forward | `Right` | `Right` | Advance audio playhead by configured jump distance |
| **Playback & Transport** | Jump Back (Medium / 15s) | `Shift+Left` | `Shift+Left` | Rewind audio playhead by medium jump distance (default 15s) |
| **Playback & Transport** | Jump Forward (Medium / 15s) | `Shift+Right` | `Shift+Right` | Advance audio playhead by medium jump distance (default 15s) |
| **Playback & Transport** | Jump Back (Long / 30s) | `Ctrl+Left` | `Cmd+Left` | Rewind audio playhead by long jump distance (default 30s) |
| **Playback & Transport** | Jump Forward (Long / 30s) | `Ctrl+Right` | `Cmd+Right` | Advance audio playhead by long jump distance (default 30s) |
| **Playback & Transport** | Jump to Start of Recording | `Home` | `Home` | Seek playhead to 00:00:00 |
| **Playback & Transport** | Seek to Start | `Home` | `Home` | Seek playhead to 00:00:00 |
| **Playback & Transport** | Jump to End of Recording | `End` | `End` | Seek playhead to the end of the loaded media |
| **Playback & Transport** | Seek to End | `End` | `End` | Seek playhead to the end of the loaded media |
| **Playback & Transport** | Play Current Story Only | `Ctrl+Alt+Space` | `Cmd+Alt+Space` | Play selected story block from in-point to out-point then stop |
| **Playback & Transport** | Toggle Auto-Follow Playhead | `Ctrl+F12` | `Cmd+F12` | Enable or disable automatic timeline scrolling following the playhead |
| **Story & Segment Editing** | Mark Story In-Point ([) | `[` | `[` | Set the beginning timestamp of a new story segment at current playhead |
| **Story & Segment Editing** | Mark Story Out-Point (]) | `]` | `]` | Set the ending timestamp of the current story segment at playhead and save story |
| **Story & Segment Editing** | Edit Story Metadata... | `Ctrl+Shift+E` | `Cmd+Shift+E` | Open story metadata editor for headline, author, excerpt, tags, and category |
| **Story & Segment Editing** | Audio Fades & Crossfades... | `Ctrl+Shift+F` | `Cmd+Shift+F` | Configure audio fade-in, fade-out, crossfade curves, and ducking parameters |
| **Story & Segment Editing** | Edit ID3 / Broadcast Tags... | `Ctrl+I` | `Cmd+I` | Open ID3v2 metadata tag editor for broadcast episode and podcast tagging |
| **Story & Segment Editing** | Delete Selected Story | `Delete` | `Backspace` | Remove currently highlighted story cut from project |
| **Story & Segment Editing** | Rename Speaker... | `Ctrl+R` | `Cmd+R` | Open speaker rename and identity manager for current segment |
| **Story & Segment Editing** | Toggle Proofreading / Edit Mode | `F2` | `F2` | Toggle between viewing and proofreading edit mode; in edit mode, pauses audio and places cursor on spoken word; in viewing mode, resumes playback with pre-roll |
| **Story & Segment Editing** | Split Speaker Segment | `Shift+Return` | `Shift+Return` | Split current segment at cursor position and insert a new speaker turn |
| **Story & Segment Editing** | Split Segment at Playhead | `Ctrl+K` | `Cmd+K` | Split the highlighted transcript segment into two pieces at playhead timestamp |
| **Story & Segment Editing** | Merge with Next Segment | `Ctrl+J` | `Cmd+J` | Combine selected transcript segment with following segment |
| **Search & Transcript Tools** | Find in Transcript... | `Ctrl+F` | `Cmd+F` | Focus search bar to highlight words and phrases across transcript |
| **Search & Transcript Tools** | Find Next Occurrence | `F3` | `Cmd+G` | Jump to next occurrence of search term in transcript |
| **Search & Transcript Tools** | Find Previous Occurrence | `Shift+F3` | `Cmd+Shift+G` | Jump to previous occurrence of search term in transcript |
| **Search & Transcript Tools** | Add Comment / Marker | `Ctrl+Alt+C` | `Cmd+Alt+C` | Attach an editorial comment or production marker to current playhead / text selection |
| **Search & Transcript Tools** | Glossary / Terminology... | `Ctrl+T` | `Cmd+T` | Open custom vocabulary, acronyms, station glossary, and ASR phonetic hints |
| **Timeline & Navigation** | Zoom In Timeline | `Ctrl+=` | `Cmd+=` | Increase timeline horizontal zoom resolution |
| **Timeline & Navigation** | Zoom Out Timeline | `Ctrl+-` | `Cmd+-` | Decrease timeline horizontal zoom resolution |
| **Timeline & Navigation** | Fit Entire Timeline in View | `Ctrl+0` | `Cmd+0` | Scale timeline zoom to show full audio duration within window width |
| **Help & Diagnostics** | Run Performance Benchmark... | `Ctrl+Alt+B` | `Cmd+Alt+B` | Execute CPU, GPU, memory, and ASR model transcription speed benchmark |
| **Help & Diagnostics** | Run Diagnostic Test Bench... | `Ctrl+Shift+D` | `Cmd+Shift+D` | Execute automated self-tests across all application engines and plugins |
| **Help & Diagnostics** | Check for Updates... | `Ctrl+Alt+U` | `Cmd+Alt+U` | Check GitHub releases for new versions and patches |
| **Help & Diagnostics** | Keyboard Shortcuts Reference | `F1` | `Cmd+?` | Open interactive keyboard shortcuts reference table |
| **Help & Diagnostics** | About Application | `Shift+F1` | `Shift+F1` | Display version, build, and system diagnostic overview |

---

## AI Studio Web Preview

The web preview in Google AI Studio is configured to serve as the live, interactive **Changelog & Release Notes Viewer** for the project (sourced from `CHANGELOG.md`). It provides search, version filtering, collapsible release cards, and markdown copying capabilities for desktop application updates.

---

## Third-Party Notices & License

Radio & TV Story Segmenter is released under the MIT License.

This application incorporates or interfaces with several open source libraries and pre-trained models:

* faster-whisper & CTranslate2: MIT License
* diarize: Apache 2.0 License (FoxNoseTech)
* Silero VAD: MIT License
* WeSpeaker & sherpa-onnx: Apache 2.0 License
* onnxruntime: MIT License
* Hugging Face Transformers & MarianMT (Translation Plugin): Apache 2.0 License
* uv (Isolated Python & Dependency Packaging): MIT / Apache 2.0 License (Astral Software)
* PySide6 / Qt 6: LGPL v3 / Commercial
* scipy & scikit-learn: BSD 3-Clause License
* cryptography & keyring: Apache 2.0 / PSF License
* FFmpeg: LGPL v2.1+ / GPL v2+ (executed externally)

For full license texts and copyright acknowledgments, see NOTICES.txt or open Help -> Third-Party Licenses within the application.

## Acknowledgments

This project was developed with the aid of AI collaboration tools, including Gemini, Claude, and ChatGPT.

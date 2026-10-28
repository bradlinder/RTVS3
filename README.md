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
pip install -r installer/requirements.txt

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

All keyboard shortcuts can be viewed at any time by pressing <kbd>F1</kbd> (or <kbd>Cmd+?</kbd> on macOS) to open the interactive, searchable **Keyboard Shortcuts Reference** dialog, and can be fully customized in **Preferences -> Keyboard Shortcuts** (<kbd>Ctrl+P</kbd> / <kbd>Cmd+P</kbd>).

| Category | Action | Windows / Linux | macOS | Description |
| --- | --- | --- | --- | --- |
| **File & Project** | Open Media... | `Ctrl+O` | `Cmd+O` | Select an audio or video file to open and process |
| **File & Project** | Open Document... | `Ctrl+Alt+O` | `Cmd+Alt+O` | Import an external text document into transcript workspace |
| **File & Project** | New Project | `Ctrl+N` | `Cmd+N` | Create a new project session |
| **File & Project** | Open Project... | `Ctrl+Shift+O` | `Cmd+Shift+O` | Open an existing .rtvs project session |
| **File & Project** | Close Project | `Ctrl+W` | `Cmd+W` | Close current project session |
| **File & Project** | Save Project | `Ctrl+S` | `Cmd+S` | Save current project, audio offsets, stories, and edits |
| **File & Project** | Save Project As... | `Ctrl+Shift+S` | `Cmd+Shift+S` | Save current project to a new file location |
| **File & Project** | Export Project Archive (.zip)... | `Ctrl+Shift+E` | `Cmd+Shift+E` | Export complete project archive with audio and transcript to a .zip file |
| **File & Project** | Unified Export Center... | `Ctrl+E` | `Cmd+E` | Open the Unified Export Center for audio, text, transcripts, and plugins |
| **File & Project** | Copy YouTube Chapters to Clipboard | `Ctrl+Shift+Y` | `Cmd+Shift+Y` | Copy zero-based timestamps and story headlines formatted for YouTube descriptions |
| **File & Project** | Batch Processing... | `Ctrl+Shift+B` | `Cmd+Shift+B` | Open Batch Audio / Video Transcription and Diarization Manager |
| **File & Project** | Backup & Restore... | *Unassigned* | *Unassigned* | Open project snapshot backup and restore manager |
| **File & Project** | Manage AI Models... | `Ctrl+Alt+M` | `Cmd+Alt+M` | Download, delete, verify, and monitor Whisper and ASR neural weights |
| **File & Project** | Preferences... | `Ctrl+P` | `Cmd+P` | Open application settings, audio playback, theming, and shortcuts |
| **File & Project** | Manage Plugins & Add-ons... | `Ctrl+Shift+X` | `Cmd+Shift+X` | Enable, disable, or inspect external plugins and integrations |
| **File & Project** | GPU Acceleration Settings... | `Ctrl+Alt+G` | `Cmd+Alt+G` | Configure CUDA, ROCm, or DirectML GPU hardware acceleration |
| **File & Project** | Exit Application | `Ctrl+Q` | `Cmd+Q` | Close the application |
| **AI Pipeline & Tools** | Transcribe Audio... | `Ctrl+T` | `Cmd+T` | Run automated speech-to-text transcription on loaded media |
| **AI Pipeline & Tools** | Detect Speakers (Diarization)... | `Ctrl+D` | `Cmd+D` | Perform speaker diarization and voice cluster detection |
| **AI Pipeline & Tools** | Detect Stories... | `Ctrl+Shift+A` | `Cmd+Shift+A` | Automatically segment recording into stories or songs based on pauses |
| **AI Pipeline & Tools** | Translate Transcript... | `Ctrl+Shift+L` | `Cmd+Shift+L` | Translate transcript text into Spanish or target language |
| **AI Pipeline & Tools** | Multi-Stage Processing Pipeline... | `Ctrl+R` | `Cmd+R` | Execute automated multi-model transcription, diarization, and story segmentation |
| **AI Pipeline & Tools** | Regenerate Waveform | `Ctrl+Shift+W` | `Cmd+Shift+W` | Rebuild audio peak envelope cache for the timeline |
| **AI Pipeline & Tools** | Regenerate Video Thumbnails | `Ctrl+Shift+T` | `Cmd+Shift+T` | Extract new frame thumbnails across video duration |
| **AI Pipeline & Tools** | Normalize Audio Loudness... | `Ctrl+Alt+N` | `Cmd+Alt+N` | Analyze and normalize broadcast loudness according to EBU R128 / ITU BS.1770 |
| **Panels & Views** | Toggle Timeline Panel | `Alt+1` | `Ctrl+Alt+1` | Show or hide the audio/video timeline and waveform panel |
| **Panels & Views** | Toggle Transcript Panel | `Alt+2` | `Ctrl+Alt+2` | Show or hide the interactive text transcript panel |
| **Panels & Views** | Toggle Stories Panel | `Alt+3` | `Ctrl+Alt+3` | Show or hide the story cuts and segment list panel |
| **Panels & Views** | Toggle Activity History Panel | `Alt+4` | `Ctrl+Alt+4` | Show or hide the background job and activity log panel |
| **Panels & Views** | Toggle Comments Sidebar | `Ctrl+Alt+C` | `Cmd+Alt+C` | Show or hide the editorial comments and annotations sidebar |
| **Panels & Views** | Show Comment Highlights | `Ctrl+Alt+H` | `Cmd+Alt+H` | Toggle yellow editorial comment highlight overlays in transcript |
| **Panels & Views** | Show Waveform | `Ctrl+Alt+W` | `Cmd+Alt+W` | Toggle visual audio waveform display in the timeline |
| **Panels & Views** | Show Video Thumbnails | `Ctrl+Alt+T` | `Cmd+Alt+T` | Toggle thumbnail preview strip along the video timeline |
| **Panels & Views** | Video Preview Window | `Ctrl+Shift+V` | `Cmd+Shift+V` | Open or toggle the floating video preview monitor window |
| **Panels & Views** | Show Speaker Labels | `Ctrl+Alt+S` | `Cmd+Alt+S` | Show or hide speaker names before each transcript turn |
| **Panels & Views** | Show Timestamps | `Ctrl+Alt+I` | `Cmd+Alt+I` | Show or hide timecode markers in the transcript |
| **Playback & Transport** | Play / Pause Audio | `Space` | `Space` | Toggle audio playback on/off from current playhead position |
| **Playback & Transport** | Skip Backward (5s) | `Left` | `Left` | Rewind audio playhead by configured short jump distance (default 5s) |
| **Playback & Transport** | Skip Forward (5s) | `Right` | `Right` | Advance audio playhead by configured short jump distance (default 5s) |
| **Playback & Transport** | Jump Back (15s) | `Shift+Left` | `Shift+Left` | Rewind audio playhead by medium jump distance (default 15s) |
| **Playback & Transport** | Jump Forward (15s) | `Shift+Right` | `Shift+Right` | Advance audio playhead by medium jump distance (default 15s) |
| **Playback & Transport** | Jump Back (30s) | `Ctrl+Left` | `Cmd+Left` | Rewind audio playhead by long jump distance (default 30s) |
| **Playback & Transport** | Jump Forward (30s) | `Ctrl+Right` | `Cmd+Right` | Advance audio playhead by long jump distance (default 30s) |
| **Playback & Transport** | Seek to Start | `Home` | `Home` | Seek playhead to 00:00:00 |
| **Playback & Transport** | Seek to End | `End` | `End` | Seek playhead to the end of the loaded media |
| **Playback & Transport** | Play Current Story Only | `Ctrl+Alt+Space` | `Cmd+Alt+Space` | Play selected story block from in-point to out-point then stop |
| **Playback & Transport** | Toggle Auto-Follow Playhead | `Ctrl+F12` | `Cmd+F12` | Enable or disable automatic timeline scrolling following the playhead |
| **Story & Segment Editing** | Mark Story In-Point ([) | `[` | `[` | Set the beginning timestamp of a new story segment at current playhead |
| **Story & Segment Editing** | Mark Story Out-Point (]) | `]` | `]` | Set the ending timestamp of the current story segment at playhead and save story |
| **Story & Segment Editing** | Audio Fades & Crossfades... | `Ctrl+Shift+F` | `Cmd+Shift+F` | Configure audio fade-in, fade-out, crossfade curves, and ducking parameters |
| **Story & Segment Editing** | ID3 Tag Editor (MP3)... | `Ctrl+Shift+I` | `Cmd+Shift+I` | Open ID3v2 metadata tag editor for broadcast episode and podcast tagging |
| **Story & Segment Editing** | Delete Selected Story | `Delete` | `Backspace` | Remove currently highlighted story cut from project |
| **Story & Segment Editing** | Toggle Proofreading / Edit Mode | `F2` | `F2` | Toggle between viewing and proofreading edit mode |
| **Story & Segment Editing** | Split Speaker Segment | `Shift+Return` | `Shift+Return` | Split current segment at cursor position and insert a new speaker turn |
| **Story & Segment Editing** | Split Segment at Playhead | `Ctrl+K` | `Cmd+K` | Split the highlighted transcript segment into two pieces at playhead timestamp |
| **Story & Segment Editing** | Merge with Next Segment | `Ctrl+J` | `Cmd+J` | Combine selected transcript segment with following segment |
| **Story & Segment Editing** | Undo | `Ctrl+Z` | `Cmd+Z` | Undo previous transcript or story edit |
| **Story & Segment Editing** | Redo | `Ctrl+Shift+Z` | `Cmd+Shift+Z` | Redo previously undone edit |
| **Search & Transcript Tools** | Find in Transcript... | `Ctrl+F` | `Cmd+F` | Focus search bar to highlight words and phrases across transcript |
| **Search & Transcript Tools** | Find Next Occurrence | `F3` | `Cmd+G` | Jump to next occurrence of search term in transcript |
| **Search & Transcript Tools** | Find Previous Occurrence | `Shift+F3` | `Cmd+Shift+G` | Jump to previous occurrence of search term in transcript |
| **Search & Transcript Tools** | Add / Edit Comment... | `Ctrl+M` | `Cmd+M` | Attach an editorial comment or production marker to current playhead / text selection |
| **Search & Transcript Tools** | Glossary & Custom Vocabulary... | `Ctrl+Shift+G` | `Cmd+Shift+G` | Open custom vocabulary, acronyms, station glossary, and ASR phonetic hints |
| **Search & Transcript Tools** | Bold Text | `Ctrl+B` | `Cmd+B` | Toggle bold formatting on selected transcript text |
| **Search & Transcript Tools** | Italic Text | `Ctrl+I` | `Cmd+I` | Toggle italic formatting on selected transcript text |
| **Search & Transcript Tools** | Underline Text | `Ctrl+U` | `Cmd+U` | Toggle underline formatting on selected transcript text |
| **Search & Transcript Tools** | Clear Text Formatting | `Ctrl+\` | `Cmd+\` | Remove rich formatting and color styles from selected transcript text |
| **Search & Transcript Tools** | Increase Transcript Text Size | `Ctrl++` | `Cmd++` | Increase transcript display font size by 1 point |
| **Search & Transcript Tools** | Decrease Transcript Text Size | `Ctrl+-` | `Cmd+-` | Decrease transcript display font size by 1 point |
| **Search & Transcript Tools** | Reset Transcript Text Size | `Ctrl+0` | `Cmd+0` | Reset transcript display font size to default |
| **Timeline & Navigation** | Zoom In Timeline | `+` | `+` | Increase timeline horizontal zoom resolution (or Mouse Wheel) |
| **Timeline & Navigation** | Zoom Out Timeline | `-` | `-` | Decrease timeline horizontal zoom resolution (or Mouse Wheel) |
| **Help & Diagnostics** | Run Performance Benchmark... | `Ctrl+Alt+B` | `Cmd+Alt+B` | Execute CPU, GPU, memory, and ASR model transcription speed benchmark |
| **Help & Diagnostics** | Run Diagnostic Test Bench... | `Ctrl+Shift+D` | `Cmd+Shift+D` | Execute automated self-tests across all application engines and plugins |
| **Help & Diagnostics** | Check for Updates... | `Ctrl+Alt+U` | `Cmd+Alt+U` | Check GitHub releases for new versions and patches |
| **Help & Diagnostics** | Keyboard Shortcuts Reference | `F1` | `Cmd+?` | Open interactive keyboard shortcuts reference table |
| **Help & Diagnostics** | About Application | `Shift+F1` | `Shift+F1` | Display version, build, and system diagnostic overview |
| **Help & Diagnostics** | Open Diagnostic Log Folder | `Ctrl+Shift+K` | `Cmd+Shift+K` | Open the application diagnostic logs directory in file explorer |
| **Help & Diagnostics** | Third-Party Licenses | `Ctrl+Shift+F1` | `Cmd+Shift+F1` | View open-source licenses and attribution disclosures |

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

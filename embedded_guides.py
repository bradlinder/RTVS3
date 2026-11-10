"""Radio & TV Story Segmenter — Built-In Embedded User Guides & Documentation.

Provides compile-time hardcoded fallbacks of all user guides and workflows.
Ensures documentation is immediately accessible even when running inside frozen
standalone executables, partial installations, or isolated environments without disk files.
"""
from __future__ import annotations

from typing import Dict, List, Optional

EMBEDDED_GUIDES: Dict[str, str] = {
    "workflow": """# Getting Started & Essential Workflow

This guide covers the core workflow of Radio & TV Story Segmenter: loading media, generating transcripts, detecting stories, editing speaker labels, and navigating the interactive timeline.

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
- **Volume & Fades**: Use the master volume slider. Enable **Audio Fades** to preview real-time volume fade-ins and fade-outs on segmented stories.

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

## 5. Story Segmentation

RTVS3 organizes broadcasts into distinct, individual stories that can be exported separately or together.

### Automatic Story Detection:
Click **Detect Stories...** (or press **Ctrl+Shift+A**). The engine analyzes topic boundaries, speech pauses, and speaker turns to segment your episode automatically.

### Manual Story Creation:
1. Press `[` to mark a story start and `]` to mark a story end at the current playhead position.
2. Or **right-click and drag** across any region on the timeline waveform to draw a selection, then right-click and choose **Add Story from Selection**.
3. A new story appears in the right-hand **Stories** panel.

### Adjusting Story Boundaries & Fades:
- **Move Boundaries**: Click and drag the left or right edge handle of any story box on the timeline.
- **Audio Fades**: Drag the fade handle at the top corners of a story to set fade-in and fade-out durations (e.g., 1.5 seconds) with linear, exponential, or S-curve shapes.
- **Story Metadata**: Select a story in the Stories list and click **Story Metadata...** to edit its title, summary, author, and categories.

---

## 6. Unified Export & Batch Processing

- **Unified Export Center**: Press **Ctrl+E** (**File > Export...**) to export split audio cuts, Word/PDF cue sheets, WordPress draft posts, or DAW timelines.
- **Copy YouTube Chapters**: Press **Ctrl+Shift+Y** (**File > Copy YouTube Chapters to Clipboard**) to copy formatted chapter markers instantly.
- **Batch Processing Center**: Go to **File > Batch Processing...** (**Ctrl+Shift+B**) to queue and process multiple episodes or media files sequentially in the background.
""",
    "wordpress": """# WordPress Exporting & Setup Guide

This guide details how to configure RTVS3 to publish story drafts, podcast enclosures, and YouTube embeds directly to your WordPress website.

---

## 1. Creating a WordPress Application Password

To communicate securely with your WordPress site without sharing your master account password, RTVS3 uses standard **WordPress Application Passwords**.

### Step-by-Step in WordPress:
1. Log in to your WordPress admin dashboard (e.g., `https://yoursite.com/wp-admin`).
2. Navigate to **Users > Profile** (or click your name in the top right corner).
3. Scroll down to the **Application Passwords** section.
4. In the **New Application Password Name** field, type a label such as `RTVS3 Desktop` or `Story Segmenter`.
5. Click **Add New Application Password**.
6. WordPress will display a 24-character generated password formatted with spaces (e.g., `abcd efgh ijkl mnop qrst uvwx`).
7. **Copy this password immediately** (WordPress only displays it once).

> **Tip:** Application Passwords can be revoked at any time from your WordPress profile without changing your primary WordPress login password.

---

## 2. Entering Credentials in RTVS3

You can save your WordPress credentials in preferences so you only need to enter them once:

1. In RTVS3, go to **Settings > Preferences...** (or press **Ctrl+,**).
2. Click the **WordPress** tab on the left.

![WordPress Preferences Credentials](../images/wordpress_preferences_credentials.png)

3. Fill in your details:
   - **Site URL**: The full web address of your WordPress homepage (e.g., `https://example-news-station.com`). Both `https://` and trailing slash variations are handled automatically.
   - **Username**: Your WordPress administrative or author username (e.g., `newsroom_editor`).
   - **App Password**: Paste the 24-character password generated in Step 1.
4. Click **Test Connection**. RTVS3 contacts your site's REST API. When successful, your site title and authenticated user permissions are confirmed.
5. Click **Save Preferences**.

---

## 3. Opening WordPress Export in the Unified Export Center

When your broadcast media has been segmented into stories, open the export panel:
1. Press **Ctrl+E** (or go to **File > Export...**).
2. In the **Export Destination** bar at the top, select the **WordPress Draft Post** radio button.

![WordPress Content Tab](../images/wordpress_export_content_tab.png)

### Choosing Export Scope:
In the **Export Scope** dropdown, choose which posts you want to generate:
- **All Stories**: Generates separate draft posts for every detected story.
- **Selected Stories**: Generates drafts only for the stories currently highlighted in the Stories panel.
- **Full Broadcast**: Generates one post containing the complete episode transcript.
- **Full Broadcast and All Stories**: Generates one master episode post plus individual story posts.

---

## 4. Customizing Individual Post Details Across the 4 Tabs

Under **WordPress Post Configuration**, select any post in the left-hand **Posts to Export:** list. The divider between the post list and the editor pane is an expandable splitter that you can drag to widen the sidebar.

Configure each post across the 4 editor tabs:

### Tab 1: Post Content
- **Post Title**: The headline of the WordPress draft post.
- **Post Excerpt / Teaser**: A concise summary of the story used for article previews, RSS feeds, and social cards. Click **Generate from Story** to automatically extract a snippet (≤55 words) from the transcript.
- **Custom Notice / Disclaimer**: An optional notice (e.g., *"This story aired on Radio One on Nov 4"*) prepended or appended to the article.

### Tab 2: Authors & Taxonomy

![WordPress Authors & Taxonomy Tab](../images/wordpress_export_taxonomy_tab.png)

- **Authors**: Search, filter, and select registered WordPress authors to assign bylines.
- **Categories**: Search, filter, and assign one or more WordPress categories (e.g., *News*, *Interviews*, *Local*).
- **Tags**: Enter comma-separated tag keywords.

### Tab 3: Media

![WordPress Media Tab](../images/wordpress_export_media_tab.png)

- **Featured Image**: Choose a captured video thumbnail frame, custom image file, or disabled.
- **YouTube Video Link**: Paste a YouTube watch link, short link, or studio URL.
  - **Context-Aware Auto-Dimming**: Controls automatically dim when the URL field is empty and illuminate as soon as a valid video link is detected.
  - **Stop Video at Story End**: When checked, the embedded player automatically pauses playback when the segment concludes.
  - **Embed Placement**: Choose whether the responsive 16:9 player appears at the **Top** (above transcript) or **Bottom** (below transcript).
- **Include Audio Files**:
  - For radio and audio projects, checking this extracts a 128 kbps MP3 cut and uploads it to the WordPress Media Library.
  - For video shows, this defaults to unchecked because the YouTube embed already provides full audio.
  - **Apply Audio Fades**: Automatically rendered on the MP3 cut if audio inclusion is enabled.
- **Podcast Enclosure**: Check this to format the audio upload with Castos or standard RSS podcast enclosures so aggregator plugins detect the episode.

### Tab 4: Publishing & Formatting

![WordPress Publishing & Formatting Tab](../images/wordpress_export_publishing_tab.png)

- **Transcript Languages**: Select your primary spoken language and choose any translated languages to append to the post draft.
- **Episode Cross-Linking**: Automatically insert hyperlinks back to the full broadcast master post or related story segments.

---

## 5. Left-Hand Post List Prefix Indicators & Tooltips

In the **Posts to Export:** list, compact prefix tags appear immediately after the story number so you can verify each post's configuration at a glance, even when the sidebar is narrow:

![WordPress Post List Badges](../images/wordpress_posts_list_badges.png)

- **`[YT]`**: A responsive YouTube embed with story timestamps is attached.
- **`[Pod]`**: Podcast RSS enclosure tags are configured.
- **`[A]`**: An MP3 audio cut will be uploaded.
- **`[Img]`**: A featured image or video thumbnail will be uploaded.
- **Example**: `Story 1 [YT, A]: Demonstrators push for more funding...`
- **Hover Tooltips**: Hover your mouse over any post in the list to view a multi-line tooltip detailing exact start/end timecodes, author names, and category tags.
- **Resizable Sidebar**: Drag the vertical splitter bar between the post list and the editor tabs to expand or shrink the sidebar.

---

## 6. Uploading Drafts to WordPress

Click **Export to WordPress Drafts...** at the bottom of the dialog:
- RTVS3 authenticates via the WordPress REST API and creates **Draft** posts on your WordPress site.
- Posts are created in draft status so you or your editorial team can review and preview them before publishing them live to the public.
- When upload completes, a clickable link takes you directly to the WordPress post editor.
""",
    "youtube": """# YouTube Features & Chapter Generation Guide

This guide explains how to use RTVS3's YouTube features: generating video chapters for YouTube video descriptions, configuring the YouTube upload plugin, and embedding timestamped video clips into WordPress articles.

---

## 1. Generating YouTube Chapter Lists

YouTube automatically divides videos into chapters along the video player scrub bar when timestamps are included in the video description. RTVS3 converts your segmented stories directly into YouTube-formatted chapters with one click.

### Requirements for YouTube Video Chapters:
- The first chapter must begin at `00:00` (or `0:00`).
- You must have at least 3 timestamps listed in ascending order.
- Each chapter must be at least 10 seconds long.

RTVS3 guarantees all three rules are satisfied automatically.

### Two Ways to Generate & Copy Chapters:

#### Method A: Instant Clipboard Copy (Recommended)
1. Open your episode in RTVS3 and ensure stories have been detected or created.
2. Press **Ctrl+Shift+Y** (or go to **File > Copy YouTube Chapters to Clipboard**).
3. The chapter list is copied to your clipboard immediately:
   ```text
   00:00 - Introduction & Cold Open
   02:25 - Deep Dive: Renewable Energy Grid Tech
   07:40 - Battery Chemistry Breakdown
   10:15 - Audience Q&A and Credits
   ```
4. Open your video in **YouTube Studio** (`studio.youtube.com`), navigate to the **Details** tab, and paste the chapters directly into the **Description** box.
5. Click **Save**. YouTube will automatically draw chapter markers on your video scrub bar.

#### Method B: Unified Export Center (.txt File)
1. Press **Ctrl+E** (or go to **File > Export...**).
2. Select **Local Files (Media & Transcript)** at the top.
3. Check **Tracklist / YouTube Chapters (.txt)** under document exports.
4. Click **Export Selected Formats** to save the formatted chapter file to disk.

---

## 2. Embedding YouTube Video Segments in WordPress

When publishing articles about individual segments of a show, you can embed the main YouTube video so that it starts and stops at the exact moment of each story:

1. In RTVS3, open **File > Export...** (**Ctrl+E**) and select **WordPress Draft Post**.
2. Select a story in the **Posts to Export:** list, then click the **Media** tab (Tab 3).
3. In the **YouTube Video Link** field, paste your YouTube video URL:
   - Supports standard watch URLs (`https://www.youtube.com/watch?v=...`)
   - Short links (`https://youtu.be/...`)
   - YouTube Studio edit URLs (`https://studio.youtube.com/video/.../edit`)
   - Live stream and Shorts links
4. Check **Stop Video at Story End**:
   - When checked, the embedded player automatically pauses playback when the segment concludes.
5. Choose **Embed Placement**:
   - **Top**: Places the video player above the transcript.
   - **Bottom**: Places the video player below the transcript.
6. When exported to WordPress, RTVS3 generates a responsive 16:9 Gutenberg player that works smoothly on mobile devices and bypasses server-side oEmbed issues on scheduled or unlisted videos.

---

## 3. Direct YouTube Video Upload Plugin

If you have the **YouTube Publisher** plugin enabled:
1. Configure your Google OAuth credentials in **Settings > Preferences... > YouTube Publisher**.
2. Go to **File > Export...** (**Ctrl+E**) and select the **YouTube Video Publisher** radio button at top.
3. Set your video title, description, category, privacy status (*Public*, *Unlisted*, or *Private*), and thumbnail.
4. RTVS3 uploads your video directly to your YouTube channel with chapters pre-populated in the description.
""",
    "video_shows": """# Video Shows & YouTube Publishing Guide

This guide walks through the end-to-end workflow for transcribing, segmenting, and publishing video shows to WordPress with responsive, timestamp-synchronized YouTube video embeds.

---

## 1. Architectural Overview & The Hybrid Workflow

Publishing video shows to WordPress often involves a friction point: uploading full multi-gigabyte `.mp4` video files directly to WordPress web hosts can quickly exhaust server storage, exceed PHP upload limits, and result in sluggish mobile streaming.

Radio & TV Story Segmenter provides a streamlined **hybrid video workflow**:
1. **Local Media Processing**: You work directly with your original high-resolution video file (`.mp4`, `.mov`, `.mkv`, `.webm`) on your local machine for rapid transcription, speaker diarization, story boundary detection, and timeline scrubbing.
2. **Video Hosting on YouTube**: You upload your full episode to YouTube (as unlisted, scheduled, or public).
3. **Automated Timestamped Embeds in WordPress**: By simply pasting your base YouTube link into the WordPress export dialog, the application automatically computes the start and end offsets for every segment and injects mobile-responsive, 16:9 Gutenberg iframe blocks (`<!-- wp:html -->`) directly into each story's post draft.

```mermaid
flowchart LR
    A["Local Video File<br>(.mp4 / .mov)"] --> B["RTVS3 Local Processing<br>Transcription & Stories"]
    C["YouTube Video<br>(Public / Unlisted)"] --> D["WordPress Export Panel<br>Media Tab"]
    B --> D
    D --> E["WordPress Post Drafts<br>Responsive 16:9 Embeds<br>Exact Story Timestamps"]
```

---

## 2. Step-by-Step Workflow

### Step 1: Open Your Video Media
Drag and drop your video file directly onto the timeline canvas or press **Ctrl+O** (**File > Open Media...**).
- RTVS3 automatically generates multi-resolution waveform pyramids and a video thumbnail filmstrip along the timeline ruler.
- Press **Ctrl+Shift+V** (**View > Video Preview Window**) to open the resizable floating video preview window.

### Step 2: Transcribe, Diarize & Detect Stories
1. Click **Transcribe Audio...** (**Ctrl+T**) or use the Multi-Stage Pipeline (**Ctrl+R**) to generate word-level aligned transcripts and speaker turns.
2. Click **Detect Stories...** (**Ctrl+Shift+A**) to detect story boundaries based on topic changes, natural speech pauses, or speaker transitions.
3. Review stories on the timeline: you can zoom in up to 300x, drag boundaries, and adjust audio fades.

### Step 3: Open Unified Export to WordPress
Press **Ctrl+E** (**File > Export...**) and select the **WordPress Draft Post** radio button from the **Export Destination** bar at the top.

### Step 4: Configure the "Media" Tab
Select a story (or your full episode) from the left-hand **Posts to Export:** list, then switch to the **Media** tab (Tab 3):

![WordPress Export Media Tab](../images/wordpress_export_media_tab.png)

1. **Enter YouTube Video Link**:
   Paste the base URL of your video show. RTVS3 supports all standard link formats (see [URL Compatibility](#3-youtube-url-compatibility-reference)). Controls automatically illuminate when a valid URL is provided.
2. **Stop Video at Story End**:
   - **Checked (Recommended)**: The YouTube player will pause playback when the story concludes (`?end=XXX`), encouraging readers to continue through your article or explore other stories.
   - **Unchecked**: The video will start at the story's beginning (`?start=XXX`) and continue playing the remainder of the episode.
3. **Embed Placement**:
   - **Top (Default)**: Inserts the video player above your transcript text, placing the video prominently beneath the post title.
   - **Bottom**: Places the video player below the story transcript and excerpt.

### Step 5: Review Audio & Podcast Options
For video projects, **Include audio files in WordPress export** defaults to unchecked:
- Because the YouTube video already provides full synchronized audio, extracting and uploading redundant MP3 files is disabled by default to save server bandwidth.
- If you uncheck audio inclusion, **Apply audio fades** is automatically unchecked and bypassed.
- If you explicitly check audio inclusion on a video file, RTVS3 displays a brief confirmation dialog to ensure you intended to produce a hybrid video + audio podcast post.

### Step 6: Inspect Post Prefix Indicators & Tooltips
In the left-hand **Posts to Export:** list, each item displays compact prefix badges right after the story number:

![WordPress Post List Badges](../images/wordpress_posts_list_badges.png)

- **`[YT]`**: Indicates an active YouTube embed link is configured with timestamp offsets.
- **`[Pod]`**: Indicates the post is configured as an audio podcast episode with enclosure tags.
- **`[A]`**: Indicates an MP3 audio cut will be uploaded to the WordPress media library.
- **`[Img]`**: Indicates an extracted video thumbnail frame or featured image will be attached.
- **Example**: `Story 1 [YT]: Demonstrators push for more funding...`
- Drag the splitter between the post list and editor tabs to expand the sidebar as desired.
- Hover over any post in the list to view a multi-line tooltip detailing exact start/end timestamps, author IDs, category tags, and embed settings.

### Step 7: Export to WordPress
Click **Export to WordPress Drafts...**. RTVS3 authenticates via the WordPress REST API and creates draft posts for all selected stories.

---

## 3. YouTube URL Compatibility Reference

The YouTube URL parser in RTVS3 automatically normalizes video IDs and time offsets across all common YouTube URL formats:

| Link Format | Example Input | Recognized Video ID |
| :--- | :--- | :--- |
| **Standard Watch** | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| **Short Link** | `https://youtu.be/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| **Embed Link** | `https://www.youtube.com/embed/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| **Live Stream** | `https://www.youtube.com/live/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| **YouTube Short** | `https://www.youtube.com/shorts/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| **Studio Edit** | `https://studio.youtube.com/video/dQw4w9WgXcQ/edit` | `dQw4w9WgXcQ` |
| **Link with Existing Time** | `https://youtu.be/dQw4w9WgXcQ?t=2m5s` | `dQw4w9WgXcQ` *(start offset computed)* |
| **Raw 11-Char ID** | `dQw4w9WgXcQ` | `dQw4w9WgXcQ` |

---

## 4. Responsive 16:9 Gutenberg Embed Structure

RTVS3 generates standards-compliant Gutenberg Custom HTML blocks (`<!-- wp:html -->`) using a fluid 16:9 container:

```html
<!-- wp:html -->
<div class="rtvs-youtube-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;margin:1.5rem 0;">
  <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0&amp;start=145&amp;end=450" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen="" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>
</div>
<!-- /wp:html -->
```

### Why This Matters:
1. **Works with Unlisted & Scheduled Videos**: Standard WordPress `<!-- wp:core-embed/youtube -->` blocks trigger server-side HTTP oEmbed validation. When a video is unlisted or scheduled for future release, WordPress's server often fails the oEmbed lookup, reverting the player to a plain text link. The Custom HTML block bypasses oEmbed verification while rendering reliably on all browsers.
2. **Mobile Responsive Without Theme CSS**: The `padding-bottom: 56.25%` rule maintains a true 16:9 aspect ratio across smartphones, tablets, and desktop displays without requiring theme-specific CSS plugins.
3. **`rel=0` Safe Related Videos**: Setting `rel=0` ensures that when playback pauses or completes, YouTube only displays related videos from your own channel rather than competing content.

---

## 5. Troubleshooting & FAQs

### Q: Why did the video preview window show a black box on macOS?
In earlier versions, the video preview dialog was lazily created after the media file was already loaded. On macOS Qt 6 with AVFoundation, `AVPlayer` configured an audio-only pipeline if no video sink was attached before `setSource()`. In **v3.9.74-beta** and later, RTVS3 pre-initializes the floating video dialog and attaches `setVideoOutput()` at startup, ensuring macOS Cocoa properly maps the `AVPlayerLayer`.

### Q: Can I set default YouTube embed options so I don't have to configure them every time?
Yes. Go to **Settings > Preferences...** (or press **Ctrl+,**), navigate to the **WordPress** tab, and configure your defaults under **YouTube Video Embed Defaults**:
- **Default Stop Video at Story End**
- **Default Embed Placement (Top vs. Bottom)**

These settings are also mirrored in the **YouTube Publisher** plugin preferences.
""",
    "reaper_bridge": r"""# REAPER & Digital Audio Workstation (DAW) Live Bridge

This guide explains how to configure and use the real-time copy/paste integration between **Radio & TV Story Segmenter (RTVS3)** and **Cockos REAPER DAW** (as well as other DAWs and video editors such as Adobe Audition, Premiere Pro, and DaVinci Resolve).

---

## 1. Architectural Overview

Radio & TV Story Segmenter and digital audio workstations serve complementary roles in modern broadcast and podcast production:
- **RTVS3**: Speech intelligence, automated transcription, speaker diarization, story boundary detection, and rapid quote logging.
- **REAPER / DAWs**: Multi-track assembly, fine audio leveling, noise reduction, music ducking, equalization, and final broadcast mastering.

Rather than forcing users to export files and manually re-import them, RTVS3 provides a **unified multi-channel clipboard and real-time IPC bridge**:

```mermaid
flowchart TD
    A["RTVS3 Transcript or Timeline<br>(Ctrl+C Copy)"] --> B["Unified QMimeData & Sidecar Emitter"]
    B --> C["REAPER DAW Bridge<br>(ReaScript Lua Companion)"]
    B --> D["Universal WAV Clipboard<br>(CF_HDROP / text/uri-list)"]
    C --> E["REAPER Timeline Clip<br>• Zero-Generation Sample Alignment<br>• Verbatim Transcript in Item Notes<br>• Speaker Colors & Take Markers<br>• Dynamic Trim/Split Live Auto-Sync"]
    D --> F["Audition / Premiere / Resolve<br>(Direct Ctrl+V File Drop)"]
```

### Key Advantages of the Live Bridge:
1. **Zero Generation Loss & Non-Destructive Referencing**: Pasting a clip into REAPER references the original master audio file using native REAPER timeline offsets (`D_STARTOFFS` and `D_LENGTH`), without re-encoding or introducing lossy artifacts.
2. **Verbatim Transcript in Item Notes**: Full speaker-attributed dialogue is automatically injected into REAPER's native **Item Notes (`P_NOTES`)**, keeping the spoken transcript permanently attached to the audio block wherever it is moved on the timeline.
3. **Take Markers**: Visual markers placed directly on the media take indicate speaker turns or concise sentence cues.
4. **Dynamic Trim, Extend & Split Auto-Sync**: If you drag the edges of an inserted clip in REAPER to expand or trim context, or split a clip into multiple pieces with `S`, the transcript in Item Notes, the Take Name timecode range, and Take Markers automatically update to match the new boundaries.
5. **Universal Audio Clipboard Fallback**: For other audio and video editors (Audition, DaVinci Resolve, Premiere), RTVS3 can automatically render temporary lossless WAV slices to the OS clipboard on `Ctrl+C`.

---

## 2. Setting Up the REAPER Companion Scripts

RTVS3 bundles four native ReaScript Lua scripts:
- **`rtvs_reaper_companion.lua`**: Fast one-key action to paste the latest copied RTVS3 selection at the REAPER edit cursor.
- **`rtvs_reaper_auto_sync.lua`**: Continuous background watcher that monitors the timeline and automatically updates Item Notes, Take Names, and Take Markers whenever you drag clip edges or split items (`S`).
- **`rtvs_reaper_sync.lua`**: Manual one-shot action to immediately scan and refresh all trimmed/split clips on the timeline.
- **`rtvs_reaper_dock.lua`**: Optional dockable ReaImGui browser panel inside REAPER to search, browse, and insert stories or segments with live polling.

### Step 1: Install Scripts from RTVS3 Preferences
1. In RTVS3, go to **Settings > Preferences...** (or press **Ctrl+,**).
2. Click the **External Audio & Video Editors** tab on the left sidebar.
3. Review the **REAPER DAW Companion Bridge** settings.
4. Click **Install REAPER Companion Scripts...**.
5. RTVS3 automatically detects your REAPER resource directory:
   - **Windows**: `%APPDATA%\REAPER\Scripts\RTVS3`
   - **macOS**: `~/Library/Application Support/REAPER/Scripts/RTVS3`
   - **Linux**: `~/.config/REAPER/Scripts/RTVS3`
   *(If using a portable REAPER installation, you can browse to select its directory).*
6. Click **Install Scripts**. The installer copies `rtvs_reaper_companion.lua` and `rtvs_reaper_dock.lua` into your REAPER scripts folder.

### Step 2: Register the Script in REAPER's Action List
1. Open **Cockos REAPER**.
2. Press `?` (or go to **Actions > Show action list...**).
3. In the bottom-right corner, click **New action... > Load ReaScript...**.
4. Browse to your `Scripts/RTVS3` directory and select all scripts:
   - `rtvs_reaper_companion.lua`
   - `rtvs_reaper_auto_sync.lua`
   - `rtvs_reaper_sync.lua`
   - `rtvs_reaper_dock.lua`
5. Click **Open**. Both scripts are now registered in REAPER's action list.

### Step 3: Assign a Keyboard Shortcut in REAPER (Recommended)
1. In REAPER's Action List, search for `RTVS3` in the filter box.
2. Select **`Script: rtvs_reaper_companion.lua`**.
3. In the bottom-left **Shortcuts for selected action** section, click **Add...**.
4. Press your desired shortcut key (for example: **Ctrl+V**, **Alt+V**, or **Ctrl+Shift+V**).
5. Click **OK** and close the Action List.

---

## 3. How to Copy from RTVS3 & Paste into REAPER

### Copying in RTVS3:
You can copy audio selections using either the **Transcript** or **Timeline** view:
- **From the Transcript**:
  - Drag to highlight any passage of spoken dialogue.
  - Or click any story header tag in the transcript.
  - Press standard **Ctrl+C** (or right-click and choose **Copy (Ctrl+C)**).
- **From the Timeline**:
  - Right-click and drag across the waveform to create a drag selection range.
  - Or click any existing story block on the timeline.
  - Press standard **Ctrl+C** (or right-click and choose **Copy Selection (Ctrl+C)**).

> **Unified Multi-Channel Copy:** A single `Ctrl+C` copy action bundles plain text, formatted HTML, REAPER IPC JSON metadata, and optional WAV clip files simultaneously.

### Pasting into REAPER:
1. Switch to REAPER.
2. Click on the timeline track where you want the clip placed and position your edit cursor.
   *(If no track is selected, the companion script automatically creates or routes to a track named `"RTVS3 Assemble"`).*
3. Press your assigned shortcut for `rtvs_reaper_companion.lua` (e.g. `Alt+V`).
4. The media item immediately appears on the timeline:
   - Aligned precisely to the sample range copied from RTVS3.
   - Color-coded with the speaker's assigned color.
   - Non-destructive volume fade handles applied if configured in RTVS3.
   - The edit cursor advances automatically to the end of the newly placed clip, ready for immediate sequential assembly.

---

## 4. Where is the Transcript? (Item Notes & Take Names)

### Item Notes (`P_NOTES`):
The full verbatim transcript is stored inside REAPER's native **Media Item Notes** formatted with line and paragraph breaks identical to the RTVS3 transcript view:

```text
[00:10.0] Mayor Bradley:
Mayor announced the new budget transit proposal today.

[00:40.0] Council Member:
The funding expands light rail operations across the county.
```

- **How to view in REAPER**:
  - Right-click the media item on the timeline and choose **Item notes** (or press the Item Notes shortcut in REAPER).
  - Or click the small note icon in the upper-left of the media item header bar.
- The notes window opens, displaying the cleanly formatted, paragraph-separated transcript for that clip.

### Take Name (`P_NAME`):
The Take Name is formatted with the story title or the first 45 characters of spoken dialogue, followed by the exact timecode range:
```text
Mayor Bradley: Transit funding announcement [00:10.0 - 01:10.0]
```

---

## 5. Speaker Color Coding & Take Marker Styles

### Automatic Speaker Color Coding:
By default, pasted clips and take markers are automatically color-coded with the primary speaker's assigned color from RTVS3. If you prefer to manage track, item, and marker colors manually in REAPER:
- Go to **Settings > Preferences... > External Audio & Video Editors**.
- Uncheck **Apply speaker color coding to pasted DAW clips**.
- When disabled, ALL color coding rules are bypassed: the media item, take, and all take markers retain default REAPER track and theme coloring.

### Customizing Take Marker Styles:

Take markers appear directly on media items in REAPER as visual landmarks. You can customize their density in RTVS3 under **Settings > Preferences... > External Audio & Video Editors > REAPER Take Marker Style**:

1. **Speaker Changes Only (Default & Recommended)**:
   - Places a single color-coded take marker at the beginning of each speaker turn (e.g., `[Mayor Bradley]`).
   - Keeps your timeline clean and uncluttered while clearly marking speaker hand-offs.
2. **Speaker Changes + True Sentence Cues**:
   - Places concise, 6-word phrase preview markers at true grammatical sentence breaks (terminated by periods, question marks, exclamation points, or speech pauses >= 1.5 seconds) and speaker turns.
   - Compatible with both Whisper and Parakeet ASR models, preventing mid-sentence segment fragments or minor breath pauses from cluttering the timeline with duplicate markers.
3. **None (No Take Markers)**:
   - Completely omits take markers from the media item.
   - Ideal for minimalist workflows; the full transcript remains accessible at any time inside the **Item Notes**.

---

## 6. Live Non-Destructive Trim, Extend & Split Auto-Sync

One of the most powerful capabilities of the RTVS3 REAPER bridge is **automatic transcript re-slicing**:

### What Happens When You Trim or Extend in REAPER:
Because the media item references your master episode file rather than an isolated rendered file:
1. Drag the **left edge** of the item earlier in time to pull in earlier context or intro dialogue.
2. Drag the **right edge** of the item later in time to extend the sentence or capture the reaction.
3. Split the item into two separate clips by positioning the edit cursor and pressing `S`.

### How Auto-Sync Works:
- Each item inserted by RTVS3 is tagged with extended metadata (`P_EXT:RTVS3_MANAGED`).
- Whenever the start offset (`D_STARTOFFS`) or item length (`D_LENGTH`) changes:
  - The script slices the master transcript index (`latest_transcript_index.json`) for the new timecode range.
  - The **Item Notes (`P_NOTES`)** are automatically updated with the newly expanded or trimmed dialogue.
  - The timecode range in the **Take Name** is updated.
  - The Take Markers are automatically cleared and repositioned for the new boundaries.
### How to Run Auto-Sync:
Because REAPER only executes ReaScripts when triggered or while a background loop is running, RTVS3 provides seamless auto-sync options:
1. **Automatic Background Activation via Paste (`rtvs_reaper_companion.lua`)**:
   - When you run `rtvs_reaper_companion.lua` to paste a clip, it **automatically launches a background watcher loop** in REAPER.
   - Any time you drag the edges of an RTVS3 clip to shrink or expand it, or split a clip with `S`, the Item Notes and Take Markers update automatically in real time (~0.35s)! You do not need to launch any separate script.
2. **Dedicated Background Toggle Action (`rtvs_reaper_auto_sync.lua`)**:
   - In REAPER, run **`Script: rtvs_reaper_auto_sync.lua`** (or add it to a toolbar button).
   - Its toolbar button lights up indicating it is active in the background. Click again to stop.
3. **One-Shot Manual Sync (`rtvs_reaper_sync.lua`)**:
   - Assign a shortcut (such as `F5` or `Alt+S`) to **`Script: rtvs_reaper_sync.lua`**.
   - Press it anytime after trimming or splitting to refresh all timeline clips immediately.
4. **ReaImGui Dock (`rtvs_reaper_dock.lua`)**:
   - Automatically checks and syncs clips every 0.5 seconds whenever the dock window is open, or click the **Sync Trimmed Clips** button in the dock header bar.

---

## 7. Using the Dockable ReaImGui Transcript Browser (`rtvs_reaper_dock.lua`)

If you have the free **ReaImGui** extension installed in REAPER (available via ReaPack):

1. In REAPER, run **`Script: rtvs_reaper_dock.lua`**.
2. A floating panel appears that can be docked anywhere in your REAPER workspace (e.g., beside the Mixer or below the Track Control Panel).
3. **Features of the Dock**:
   - **Real-Time Story Browser**: Lists all stories defined in your active RTVS3 project with exact durations. Click **Insert** next to any story to place it directly at the REAPER edit cursor.
   - **Transcript Block Search**: Type any word or phrase into the search box to filter speech blocks across the entire episode. Click **Insert** next to any speech line to place that exact quote.
   - **Paste Copied Clip**: One-click button to paste the active clipboard cue.
   - **Sync Trimmed Clips**: Forces an immediate re-sync of all trimmed or split clips on the timeline with the current transcript index.

---

## 8. Universal Audio Clipboard for Other DAWs (Audition, Premiere, Resolve)

If you work in digital audio workstations or non-linear video editors other than REAPER:

1. **Standard `Ctrl+C` (Clean Text & REAPER IPC)**:
   - Standard `Ctrl+C` copies plain text, formatted HTML, and the lightweight REAPER JSON cue payload.
   - It **never** attaches file URLs to the OS clipboard, ensuring pasting into chat windows, browsers, Google Docs, and emails always pastes clean text without triggering unexpected file uploads.
2. **Dedicated `Ctrl+Shift+C` (Copy Selection as Audio Clip)**:
   - When you specifically want to copy an audio file to paste into an external NLE or DAW, press **Ctrl+Shift+C** (or right-click and choose **Copy as Audio Clip** / **Copy Story as Audio Clip**).
   - RTVS3 rapidly renders a lossless, 16-bit uncompressed WAV slice of the exact selection (with any configured story audio volume fades applied) to a temporary cache file.
   - It attaches this file to the operating system's native file clipboard (`CF_HDROP` / `text/uri-list`).
3. Switch to **Adobe Audition**, **Adobe Premiere Pro**, **DaVinci Resolve**, or **Pro Tools**, and press **Ctrl+V** on any audio track. The trimmed audio file is immediately pasted onto your timeline.

---

## 9. Troubleshooting & Common Questions

### Q: REAPER shows "No RTVS3 clip cue sidecar file found" when running the companion script.
- **Cause**: No text or story has been copied yet in RTVS3, or automatic sidecar emission is disabled.
- **Fix**: Open RTVS3, highlight dialogue or select a story, and press **Ctrl+C**. In RTVS3 **Preferences > External Audio & Video Editors**, ensure **Automatically emit REAPER DAW clip cues when copying transcript text or stories** is checked.

### Q: How do I view Item Notes in REAPER?
- Right-click any media item in REAPER and select **Item notes**. Alternatively, enable **Media item buttons: Notes** under REAPER's **Options > Preferences > Appearance > Media**.

### Q: Why does the dock say "ReaImGui extension is not installed"?
- `rtvs_reaper_dock.lua` requires the free ReaImGui extension. Open REAPER, go to **Extensions > ReaPack > Browse packages**, search for `ReaImGui`, right-click and install it, then restart REAPER.
- Note: The primary paste companion script (`rtvs_reaper_companion.lua`) requires **zero** external extensions and works on any standard REAPER installation out of the box.

### Q: Can I use both REAPER integration and the universal WAV clipboard simultaneously?
- Yes. Use **Ctrl+C** for REAPER (and standard text pasting), which uses the zero-generation sample-accurate IPC sidecar referencing your master episode file. When you specifically need a standalone WAV file clip for Audition, Premiere, or File Explorer, use **Ctrl+Shift+C**.
""",
    "export_formats": """# Export Formats & DAW Integration Guide

Radio & TV Story Segmenter provides a versatile Unified Export Center (`Ctrl+E` or `File > Export...`) supporting broadcast audio cuts, document reports, digital audio workstation (DAW) timelines, and video editing interchange formats.

![Unified Export Dialog](../images/unified_export_dialog.png)

---

## 1. Export Destinations Overview

At the top of the Unified Export Center, choose between 4 primary export destinations:
1. **Local Files (Media & Transcript)**: Split audio cuts, Word/PDF cue sheets, subtitles, and chapter tracklists saved directly to disk.
2. **WordPress Draft Post**: Multi-story draft posts with Gutenberg audio players, taxonomy, and responsive YouTube video embeds.
3. **Timeline & DAW Interchange**: Non-destructive multi-track project sequences for digital audio workstations and NLEs.
4. **YouTube Video Publisher**: Video upload to YouTube with metadata and automated description chapters.

---

## 2. Split Audio Cuts with Real-Time Fades

Under **Local Files (Media & Transcript)**, export each detected story as an independent audio file for broadcast syndication, podcasting, or archiving:
- **Formats**: MP3 (configurable bitrate), WAV (lossless 16/24-bit), FLAC, M4A, OGG.
- **Audio Fades**: Automatically renders user-defined fade-in and fade-out volume curves into each cut.
- **ID3 Metadata**: Automatically embeds episode title, artist, year, track numbers, and cover art into exported MP3 and FLAC files.
- **Naming Patterns**: Automatically names files based on story titles, episode numbers, and dates (e.g. `2026-11-04_Story01_EnergyGrid.mp3`).

---

## 3. Document & Report Exports

Share transcripts and show rundowns with editorial staff and producers:
- **Microsoft Word (.docx)**: Styled documents with headings, timestamps, speaker headers, and story excerpt blocks.
- **Adobe PDF (.pdf)**: High-resolution broadcast cue sheets with exact timecode alignment and speaker tags.
- **Plain Text (.txt) & Markdown (.md)**: Clean text files ideal for note-taking apps, summaries, and web publishing.
- **Tracklist / YouTube Chapters (.txt)**: Formatted timestamped chapter lists ready for YouTube video descriptions (also accessible instantly via **Ctrl+Shift+Y**).
- **Red Book Cue Sheet (.cue)**: Playout automation index files.
- **Google Docs & Sheets**: Directly creates formatted Google Docs articles and Google Sheets rundown schedules via Google Drive integration.

---

## 4. Broadcast DAW & Video Editor Timelines

Select **Timeline & DAW Interchange** or use RTVS3's live clipboard bridges to assemble and edit in professional audio workstations and NLEs:

### Real-Time REAPER & DAW Live Bridge (Recommended)
Rather than manually exporting files, you can copy selections directly from RTVS3 into your DAW:
- **Cockos REAPER Live Companion Bridge**:
  - Press standard **Ctrl+C** on any transcript or timeline selection in RTVS3.
  - In REAPER, trigger `Script: rtvs_reaper_companion.lua` (assignable to a shortcut) to paste the clip immediately at the edit cursor.
  - Features zero-generation sample-accurate referencing of the master media, verbatim transcripts in **Item Notes (`P_NOTES`)**, speaker color coding, non-destructive fades, customizable take markers, and dynamic transcript auto-sync when clips are trimmed or split on the REAPER timeline.
  - Includes an optional dockable ReaImGui browser (`rtvs_reaper_dock.lua`) for searching and inserting quotes live from within REAPER.
  - See the dedicated **[REAPER & DAW Live Bridge Guide](reaper_and_daw_integration.md)** for full step-by-step setup instructions.
- **Universal Audio Clipboard for Other DAWs (Audition, Premiere, DaVinci Resolve)**:
  - Enable **Render temporary WAV audio clip to OS file clipboard** in **Settings > Preferences... > Playback & Timeline**.
  - When copying in RTVS3, a lossless uncompressed WAV slice is attached to the OS file clipboard (`CF_HDROP`), allowing direct **Ctrl+V** pasting onto timeline tracks in Adobe Audition, Premiere Pro, DaVinci Resolve, and Pro Tools.

### Timeline File Exports:
- **Cockos REAPER Project (.rpp)**:
  - Generates full REAPER project files with each story arranged on separate tracks or color-coded regions with take markers.
  - Automatically translates audio volume fades into native REAPER fade handles.
- **Final Cut Pro XML & Adobe Premiere Pro**:
  - Exports timeline sequences with markers, split clips, and synchronized audio channels.
- **CMX 3600 EDL (Edit Decision List)**:
  - Industry-standard interchange format compatible with Avid Media Composer, DaVinci Resolve, and broadcast playout automation.
- **Magix Samplitude EDL (v1.5)**:
  - Multi-track timeline cues compatible with Samplitude and Sequoia broadcast workstations.
- **Subtitles & Captions (.srt, .vtt)**:
  - Generates synchronized SubRip (`.srt`) and WebVTT (`.vtt`) caption files with speaker labels for YouTube, Vimeo, and video players.
""",
}


def get_embedded_guide(guide_id: str) -> Optional[str]:
    """Retrieve embedded markdown text for a guide topic ID, if available."""
    return EMBEDDED_GUIDES.get(guide_id)


def get_all_embedded_guide_ids() -> List[str]:
    """Return all guide IDs provided as embedded fallback content."""
    return list(EMBEDDED_GUIDES.keys())

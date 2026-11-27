# YouTube Features & Chapter Generation Guide

This guide explains how to use RTVS3's YouTube features: generating video chapters for YouTube video descriptions, preparing Zero-Auth Assisted Studio uploads, and embedding timestamped video clips into WordPress articles.

---

## 1. Generating YouTube Chapter Lists

YouTube automatically divides videos into chapters along the video player scrub bar when timestamps are included in the video description. RTVS3 converts your detected segments directly into YouTube-formatted chapters with one click.

### Requirements for YouTube Video Chapters:
- The first chapter must begin at `00:00` (or `0:00`).
- You must have at least 3 timestamps listed in ascending order.
- Each chapter must be at least 10 seconds long.

RTVS3 guarantees all three rules are satisfied automatically.

### Two Ways to Generate & Copy Chapters:

#### Method A: Instant Clipboard Copy (Recommended)
1. Open your episode in RTVS3 and ensure segments have been detected or created.
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
2. Select **Local Files (Media & Transcripts)** at the top.
3. Check **Tracklist / YouTube Chapters (.txt)** under document exports.
4. Click **Export Selected Formats** to save the formatted chapter file to disk.

---

## 2. Embedding YouTube Video Segments in WordPress

When publishing articles about individual segments of a show, you can embed the main YouTube video so that it starts and stops at the exact moment of each segment:

1. In RTVS3, open **File > Export...** (**Ctrl+E**) and select **WordPress Draft Post**.
2. Choose your scope (use **Custom Selection** to toggle **Full Episode** and/or individual segments in the **Items to Export:** sidebar), select a post, and click the **Media** tab (Tab 3).
3. In the **YouTube Video Link** field, paste your YouTube video URL (projects imported from YouTube pre-fill this automatically and inherit the timestamped embed onto every segment—including newly detected segments—whenever **Apply this YouTube URL to the full episode and all stories** is checked):
   - Supports standard watch URLs (`https://www.youtube.com/watch?v=...`)
   - Short links (`https://youtu.be/...`)
   - YouTube Studio edit URLs (`https://studio.youtube.com/video/.../edit`)
   - Live stream and Shorts links
4. Review **Featured Image**: YouTube-imported projects automatically default **Full Episode** to **YouTube default thumbnail** and each individual **segment** to **Grab frame from video** inside that segment's bounds (you can scrub to another frame, select a custom image file, or choose **None** at any time).
5. Check **Stop Video at Story End**:
   - When checked, the embedded player automatically pauses playback when the segment concludes.
6. Choose **Embed Placement**:
   - **Top**: Places the video player above the transcript.
   - **Bottom**: Places the video player below the transcript.
7. When exported to WordPress, RTVS3 generates a responsive 16:9 Gutenberg player that works smoothly on mobile devices and bypasses server-side oEmbed issues on scheduled or unlisted videos.

---

## 3. Zero-Auth YouTube Assisted Upload Plugin

The **YouTube Video Publisher** plugin uses a **Zero-Auth Assisted Upload** workflow that requires no Google OAuth client secrets or cloud API tokens:
1. Optional: Configure default privacy, category, and embed preferences under **Settings > Preferences... > YouTube** (**Ctrl+P**).
2. Go to **File > Export...** (**Ctrl+E**) and select **YouTube Video Publisher** in the **Export Destination** bar (or launch from **File > Publishing & Plugins**). Use **Export Scope > Custom Selection** to pick **Full Episode** and/or specific segments directly from the checkable **Items to Export:** sidebar.
3. Set your video title, description (auto-populated with YouTube chapter markers), tags, privacy status (*Public*, *Unlisted*, or *Private*), and thumbnail.
4. Click export to package your local MP4/thumbnail/`.srt` deliverables, copy the formatted video metadata and chapter markers to the clipboard, and open YouTube Studio in your browser for quick drag-and-drop upload.

---

## 4. Importing Existing YouTube Videos (Back-Catalog Workflow)

To transcribe, segment, translate, and publish WordPress posts from videos that are already uploaded to YouTube:
1. Ensure the **YouTube Video Publisher** plugin is enabled under **Tools > Manage Plugins & Add-ons...** (**Ctrl+Shift+X**).
2. Go to **File > Open Remote Episode > From YouTube Video...** (**Ctrl+Alt+Y**).
3. Paste any YouTube URL (or 11-character video ID) and click **Fetch Info** to preview title, duration, upload date, estimated size, and any existing YouTube chapters.
4. Select your preferred download quality (default **1080p Full HD MP4** for crisp frame screenshots, or 720p / 480p / Best Available / Audio Only). If the same video and quality are already in your local cache, RTVS3 opens it immediately without re-downloading.
5. Optional: Link an existing WordPress post URL right in the import dialog to start in **Update Existing Post** mode, or check **Import YouTube chapters as initial story markers** when chapters are present.
6. Click **Download & Open**. RTVS3 automatically installs `yt-dlp` on first use (with SHA-256 verification), merges streams via bundled FFmpeg, stores the video in the **Managed Remote Media Cache**, pre-fills the WordPress **YouTube Video Embed** across the full episode and all segments (including segments detected later), and defaults Featured Images to **YouTube default thumbnail** (Full Episode) and an in-bounds video frame (individual segments).
7. Manage cache size limits, update `yt-dlp`, or manually free exported videos anytime under **Tools > Manage Cached Remote Media...**. Clearing cached media keeps your `.rtvs` transcript, stories, and embed links intact and allows 1-click re-download if you reopen the project later.

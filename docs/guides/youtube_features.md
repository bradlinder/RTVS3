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
2. Select a segment in the **Posts to Export:** list, then click the **Media** tab (Tab 3).
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

## 3. Zero-Auth YouTube Assisted Upload Plugin

The **YouTube Video Publisher** plugin uses a **Zero-Auth Assisted Upload** workflow that requires no Google OAuth client secrets or cloud API tokens:
1. Optional: Configure default privacy, category, and embed preferences under **Settings > Preferences... > YouTube** (**Ctrl+P**).
2. Go to **File > Export...** (**Ctrl+E**) and select **YouTube Video Publisher** in the **Export Destination** bar (or launch from **File > Publishing & Plugins**).
3. Set your video title, description (auto-populated with YouTube chapter markers), tags, privacy status (*Public*, *Unlisted*, or *Private*), and thumbnail.
4. Click export to package your local MP4/thumbnail/`.srt` deliverables, copy the formatted video metadata and chapter markers to the clipboard, and open YouTube Studio in your browser for quick drag-and-drop upload.
